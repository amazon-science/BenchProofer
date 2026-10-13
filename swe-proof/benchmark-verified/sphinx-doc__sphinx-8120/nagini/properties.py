# properties.py — PBT falsification battery for sphinx-doc__sphinx-8120.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes. Spec cases are full model.py variants that
# share the FROZEN spec byte-identically (region surgery edits ONLY inside the
# # impl-start / # impl-end region — same_spec elides the whole impl region,
# nested invariants included, so any edit confined there preserves the spec) and
# are checked by Nagini verify + markers.same_spec. Axiom cases are real-callee
# probes run in the instance Docker image.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py + refinement.md/mapping.md + the gold
# patch + the F2P test test_customize_system_message).
# ---------------------------------------------------------------------------
# select_translation(system_defines, system_tr,
#                    user_defines: List[bool], user_tr: List[int],
#                    builtin_defines, builtin_tr, message) -> int
#
#   Models Sphinx._init_i18n: assemble the ordered catalog-source list
#   [default] ++ project ++ [bundled] and resolve a message by FIRST-WINS
#   precedence (the first source, in order, that provides a translation wins;
#   else the untranslated message stands in for itself). Each catalog source is
#   abstracted to a (provides?: bool, text-code: int>=1) pair; the project
#   sources are the parallel READ-ONLY lists user_defines / user_tr.
#
#   READ-ONLY inputs (Acc(list_pred(.),1/2)):  user_defines, user_tr.
#   => FRAME-MUTATION is MANDATORY (directive 5).
#
#   Load-bearing postcondition clauses:
#     (P1) resolved_assembled(...) == NO_TEXT()  -> Result() == message
#     (P2) resolved_assembled(...) != NO_TEXT()  -> Result() == resolved_assembled(...)
#     (P3) not system_defines & some_provides(user_defines)
#          -> 0 <= first_provider(user_defines) < len(user_defines)
#     (P4) not system_defines & some_provides(user_defines)
#          -> Result() == user_tr[first_provider(user_defines)]     << DECISIVE
#   (P4) is the catalog-precedence delta: when the env default provides nothing
#   and a project source provides, the result is the FIRST project source's
#   text — NOT the bundled fallback's, even if the bundled source also provides
#   one. This is exactly the F2P (`'Quick search' -> 'QUICK SEARCH'` project
#   override must win over the bundled `da` catalog).
#
# ---------------------------------------------------------------------------
# ORACLE GROUNDING (directive 2). resolved_assembled / resolved / first_provider
# / some_provides are @Pure functions FULLY UNFOLDED over the input facts (the
# pure region spells out the front-recursive fold). They are NOT opaque
# answer-keys, so there is NO wrong echo to exploit: an impl that "echoes"
# resolved_assembled IS the gold behaviour. We therefore include the
# grounded-oracle delegate as a POSITIVE CONTROL (expect="verify"), not as a
# weakness. The genuinely-wrong outputs (prepatch order, bundled-wins,
# last-wins) are caught by P1/P2/P4 — see the uniqueness lane.
#
# ---------------------------------------------------------------------------
# AXIOM LANE. model.py's `axioms` region is EMPTY (meta.json axioms=[]); there is
# no consumed @ContractOnly axiom. But there IS one A-REFERENCE deep model
# (meta.deep_model_references[0]): `resolved` (first-wins precedence) models the
# real stdlib gettext catalog merge (NullTranslations.add_fallback chain +
# GNUTranslations.gettext). We carry both axiom-lane checks for it:
#   - axiom-soundness:  re-run the REAL gettext merge/lookup and assert it equals
#     `resolved` over boundary + fuzz orderings (no flag dependency: gettext's
#     merge/lookup uses no configurable mode here — mapping.md §3.1).
#   - axiom-containment: every (defines, tr) ordering the MODEL can reach lies in
#     gettext's domain (gettext accepts any chain of catalogs / any message), so
#     containment is total — the probe asserts the model-reachable shapes are all
#     valid gettext inputs and the real lookup never errors on them.
# Both probes import ONLY the stdlib `gettext` module — the very module the
# changed code merges/looks up through — and re-use axiom_check.py's logic
# (embedded so the probe is self-contained; the runner mounts only the probe).

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8120"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact inner impl body, read PROGRAMMATICALLY from the frozen model.py so it
# is byte-exact (never hand-transcribed). Everything between the markers
# (exclusive). Every spec rival is built by _swap on this anchor, so the edit is
# confined to the impl region and same_spec is guaranteed.
_IMPL_START = "    # impl-start\n"
_IMPL_END = "\n    # impl-end"
_GOLD_INNER = _BASE[_BASE.index(_IMPL_START) + len(_IMPL_START):_BASE.index(_IMPL_END)]


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: old block not found")
    if src.count(old) != 1:
        raise AssertionError("not unique: old block")
    return src.replace(old, new, 1)


def _impl(new_inner):
    """Full model.py source whose impl region's inner body is `new_inner` (the
    frozen spec/pure/pre/post regions untouched)."""
    return _swap(_BASE, _GOLD_INNER, new_inner)


# ===========================================================================
# SPEC LANE
# ===========================================================================

# ---------------------------------------------------------------------------
# (1) FRAME-MUTATION — MANDATORY (directive 5). expect="reject".
# The rival does the gold work but, before returning, WRITES into the read-only
# project-source carrier `user_tr` (sets user_tr[0] = builtin_tr). To assign
# user_tr[0] Nagini needs FULL Acc(list_pred(user_tr)); the precondition grants
# only Acc(list_pred(user_tr), 1/2). The write is REJECTED for INSUFFICIENT
# PERMISSION, before any postcondition is reached. The whole gold body
# (invariants/asserts) is kept VERBATIM so the rejection is attributable solely
# to the write. We guard the write with `if len(user_tr) > 0` so it is a genuine
# in-range write attempt (still rejected — the permission, not the index, is the
# obstacle), but we keep `out` computed from the gold fold so the only reason to
# fail is the mutation.
_FRAME_MUTATE = _GOLD_INNER.replace(
    "    out = res\n",
    "    # FRAME-MUTATION rival: overwrite the read-only project-source carrier.\n"
    "    if len(user_tr) > 0:\n"
    "        user_tr[0] = builtin_tr\n"
    "    out = res\n",
    1,
)

# ---------------------------------------------------------------------------
# (2) PREPATCH ORDER — partial-domain / THE BUG. expect="reject".
# Bundled fallback placed AHEAD of the project sources: order
# [default] ++ [bundled] ++ project (the exact pre-patch assembly, == the
# canonical model_prepatch.py). seq_defines/seq_tr are fixed to the post-fix
# order, so the framing asserts/invariants tying `defines` to seq_defines no
# longer hold; we drop those (impl-region only — same_spec preserved) and let
# the OUTPUT fail the postcondition: when the bundled source and a project source
# both provide, the fold returns the BUNDLED text where P2/P4 demand the PROJECT
# text. This is precisely what G-DIFF senses and the F2P observes.
_PREPATCH_ORDER = """    # PRE-PATCH (buggy) assembly: bundled fallback AHEAD of the project sources
    # -- order [default] ++ [bundled] ++ project. The bundled source then wins
    # first-wins resolution for any message it provides, ignoring a project
    # override. (== model_prepatch.py.)
    defines = [system_defines]  # type: List[bool]
    defines = defines + [builtin_defines]
    defines = defines + user_defines
    tr = [system_tr]  # type: List[int]
    tr = tr + [builtin_tr]
    tr = tr + user_tr

    Assert(len(defines) == len(tr))

    n = len(defines)
    res = NO_TEXT()
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(defines)))
        Invariant(Acc(list_pred(tr)))
        Invariant(Acc(list_pred(user_defines), 1 / 2))
        Invariant(Acc(list_pred(user_tr), 1 / 2))
        Invariant(len(user_defines) == len(user_tr))
        Invariant(len(defines) == n and len(tr) == n)
        Invariant(0 <= i and i <= n)
        Invariant(res == resolved(ToSeq(defines).drop(i), ToSeq(tr).drop(i)))
        # invariants-end
        Assert(ToSeq(defines).drop(i - 1)[0] == ToSeq(defines)[i - 1])
        Assert(ToSeq(tr).drop(i - 1)[0] == ToSeq(tr)[i - 1])
        Assert(ToSeq(defines).drop(i - 1).drop(1) == ToSeq(defines).drop(i))
        Assert(ToSeq(tr).drop(i - 1).drop(1) == ToSeq(tr).drop(i))
        if defines[i - 1]:
            res = tr[i - 1]
        i = i - 1

    Assert(ToSeq(defines).drop(0) == ToSeq(defines))
    Assert(ToSeq(tr).drop(0) == ToSeq(tr))
    Assert(res == resolved(ToSeq(defines), ToSeq(tr)))
    out = res
    if res == NO_TEXT():
        out = message
    return out"""

# ---------------------------------------------------------------------------
# (3) BUNDLED-WINS-OVER-PROJECT — partial-domain. expect="reject".
# Compute the gold first-wins resolution over the CORRECT order, but on the
# decisive sub-domain (default provides nothing AND some project source provides
# AND the bundled source also provides) OVERRIDE the result with the bundled
# text. Correct on every other input (no project provider, or no bundled
# provider, or the env default provides) yet WRONG on exactly the F2P
# sub-domain: returns builtin_tr where P4 demands user_tr[first_provider].
_BUNDLED_WINS = _GOLD_INNER.replace(
    "    out = res\n    if res == NO_TEXT():\n        out = message\n",
    "    out = res\n    if res == NO_TEXT():\n        out = message\n"
    "    # BUNDLED-WINS rival: on the decisive sub-domain (default provides\n"
    "    # nothing, a project source provides, the bundled source also provides)\n"
    "    # override with the BUNDLED text instead of the project override.\n"
    "    if (not system_defines) and some_provides(ToSeq(user_defines)) and builtin_defines:\n"
    "        out = builtin_tr\n",
    1,
)

# ---------------------------------------------------------------------------
# (4) LAST-WINS — partial-domain (precedence inverted). expect="reject".
# A FORWARD fold that lets a LATER source overwrite an earlier one (last-wins),
# the opposite of gettext's first-in-chain-wins. We replace the whole body with
# an independent forward-resolution loop over the SAME assembled order, returning
# the LAST provider's text. Diverges from `resolved` whenever two sources
# provide. (No reliance on the gold backward-fold invariants — a fully separate,
# self-contained loop with its own simple invariants.) Caught by P2.
_LAST_WINS = """    # LAST-WINS rival: forward fold, a later source overrides an earlier one
    # (the opposite of gettext first-in-chain-wins). Diverges from `resolved`
    # whenever two sources provide for the same message.
    defines = [system_defines]  # type: List[bool]
    defines = defines + user_defines
    defines = defines + [builtin_defines]
    tr = [system_tr]  # type: List[int]
    tr = tr + user_tr
    tr = tr + [builtin_tr]

    Assert(len(defines) == len(tr))

    n = len(defines)
    res = NO_TEXT()
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(defines)))
        Invariant(Acc(list_pred(tr)))
        Invariant(Acc(list_pred(user_defines), 1 / 2))
        Invariant(Acc(list_pred(user_tr), 1 / 2))
        Invariant(len(user_defines) == len(user_tr))
        Invariant(len(defines) == n and len(tr) == n)
        Invariant(0 <= j and j <= n)
        # invariants-end
        if defines[j]:
            res = tr[j]
        j = j + 1

    out = res
    if res == NO_TEXT():
        out = message
    return out"""

# ---------------------------------------------------------------------------
# (5) POSITIVE CONTROL (grounded-oracle delegate). expect="verify".
# `resolved_assembled` is fully unfolded over the inputs, so delegating to it
# directly IS the gold behaviour (directive-2: grounded oracle => no wrong echo).
# We replace the whole impl body with the direct oracle delegate plus the
# decisive-clause proof glue (the P4 obligation still needs the
# _resolution_picks_user / first_provider lemmas discharged, kept verbatim from
# gold). No loop, no induction the verifier can't auto-discharge. MUST verify.
_POS_DELEGATE = """    # POSITIVE CONTROL (grounded oracle): return the first-wins resolution
    # directly; resolved_assembled is fully unfolded over the inputs, so this is
    # the gold behaviour, not a wrong echo.
    res = resolved_assembled(system_defines, system_tr, ToSeq(user_defines),
                             ToSeq(user_tr), builtin_defines, builtin_tr)
    out = res
    if res == NO_TEXT():
        out = message

    # Decisive-clause proof glue (P3/P4), kept verbatim from gold: when some
    # project source provides, the first provider's text is real (>= 1).
    if not system_defines and some_provides(ToSeq(user_defines)):
        Assert(_resolution_picks_user(system_defines, system_tr, ToSeq(user_defines),
                                      ToSeq(user_tr), builtin_defines, builtin_tr))
        Assert(lemma_first_provider_bound(ToSeq(user_defines)))
        fp = first_provider(ToSeq(user_defines))
        Assert(ToSeq(user_defines)[fp])
        Assert(0 <= fp and fp < len(user_defines))
        Assert(user_defines[fp])
        Assert(ToSeq(user_defines)[fp] == user_defines[fp])
        Assert(ToSeq(user_tr)[fp] == user_tr[fp])
        Assert(user_tr[fp] >= 1)
        Assert(res == ToSeq(user_tr)[fp])
        Assert(res >= 1)
        Assert(out == res)
    return out"""

# ---------------------------------------------------------------------------
# (6) POSITIVE CONTROL (branch-reorder of the NO_TEXT fall-back). expect="verify".
# Keep the entire gold backward-fold proof VERBATIM (all framing asserts and
# invariants — directive 5a/5b: do not drop a needed framing assert), and change
# ONLY the executable shape of the final out-selection: instead of
#   out = res; if res == NO_TEXT(): out = message
# test the NO_TEXT case first into a local, equivalent semantics. The decisive
# clause glue is preserved. No new lemma needed. MUST verify (else SPEC-TOO-STRONG
# from over-fitting to the gold out-selection shape).
_POS_REORDER = _GOLD_INNER.replace(
    "    out = res\n    if res == NO_TEXT():\n        out = message\n",
    "    # POSITIVE CONTROL: branch-reorder the NO_TEXT fall-back (test NO_TEXT\n"
    "    # first); semantically identical to gold.\n"
    "    out = message  # type: int\n"
    "    if res != NO_TEXT():\n"
    "        out = res\n",
    1,
)

# ---------------------------------------------------------------------------
# (7) ADMISSIBILITY. expect="verify".
# The impl DELEGATES to a self-call: it invokes select_translation on the SAME
# in-scope inputs and RETURNS the result. The caller already holds exactly the
# callee Requires — Acc(.,1/2) of user_defines/user_tr, len-equality, message>=1,
# and the `user_tr[i]>=1 where user_defines[i]` quantified precondition (all in
# scope as this method's own Requires) — so Nagini must establish the
# precondition at a real call site for a legitimate F2P-shaped input (else
# PRECOND-TOO-STRONG). The callee's Ensures returns the half-permissions AND pins
# the result to the first-wins resolution over the current sequences, so
# returning it directly DISCHARGES this method's own postcondition. Editing only
# the impl region keeps same_spec true.
#
# NOTE (why we delegate-and-return rather than splice the self-call ahead of the
# gold body): select_translation's Ensures returns the list_pred permission but,
# being a read-only-input contract, deliberately does NOT restate the quantified
# element fact `user_tr[k] >= 1 where user_defines[k]` nor pin the input
# SEQUENCES unchanged across the call. A self-call spliced *before* the gold
# backward-fold therefore havocs that fact, and the gold loop invariant (and the
# method postcondition P2, which both refer to ToSeq(user_*)) can no longer be
# re-derived — a COMPOSABILITY/framing limitation of splicing, NOT precond
# strength (the call site itself raises no precondition error). The delegate form
# is the faithful admissibility probe: it establishes the precondition at a real
# call site and verifies, since the callee's Ensures directly implies ours.
_ADMISS = (
    "    # ADMISSIBILITY: delegate to a self-call on the SAME in-scope F2P-shaped\n"
    "    # input. The caller holds exactly the callee Requires (Acc(.,1/2) of the\n"
    "    # two project lists, len-equality, message>=1, the user_tr[k]>=1-where-\n"
    "    # user_defines[k] precondition), so Nagini must establish the precondition\n"
    "    # at a real call site (else PRECOND-TOO-STRONG); the callee's Ensures\n"
    "    # returns the half-permissions and pins the result to the first-wins\n"
    "    # resolution, so returning it directly discharges this method's own\n"
    "    # postcondition.\n"
    "    return select_translation(system_defines, system_tr, user_defines,\n"
    "                              user_tr, builtin_defines, builtin_tr, message)"
)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-user-tr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUTATE),
        "refinement": (
            "The read-only half-permission abstracts the gold patch's contract "
            "that resolution READS each catalog source's entry (`gettext` looks "
            "up, it never writes back into a source's catalog) and leaves the "
            "project sources untouched. A faithful real 'patch' that, to make a "
            "message resolve, MUTATED the project source's catalog in place (e.g. "
            "rewrote repo.locale_dirs' .mo entry to the bundled text) would "
            "corrupt the project author's other messages and the shared catalog "
            "object aliased across builds — test_customize_system_message expects "
            "the project's own 'QUICK SEARCH' returned WITHOUT altering the source "
            "catalogs, so such a patch would NOT resolve. The half-permission is "
            "exactly the spec defending that read-only contract."),
        "rationale": (
            "Rejected by the PERMISSION SYSTEM: `user_tr[0] = builtin_tr` needs "
            "full Acc(list_pred(user_tr)) but only Acc(.,1/2) is held (pre-cond / "
            "loop invariant). Insufficient permission, before any postcondition is "
            "checked. The gold fold/proof is kept verbatim so the failure is "
            "attributable solely to the write."),
    },
    {
        "id": "prepatch-order-bundled-ahead",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_PREPATCH_ORDER),
        "refinement": (
            "This is the pre-patch assembly verbatim (== model_prepatch.py): "
            "locale_dirs = [None, package_dir/'locale'] + list(repo.locale_dirs), "
            "i.e. bundled fallback AHEAD of project sources. Its faithful real "
            "patch IS the UNPATCHED _init_i18n: gettext's first-in-chain-wins then "
            "selects the bundled `da` catalog's value for 'Quick search', so "
            "app.translator.gettext('Quick search') != 'QUICK SEARCH' and "
            "test_customize_system_message FAILS. It does not resolve (this is the "
            "very bug the issue reports)."),
        "rationale": (
            "Rejected by P2 (resolved_assembled != NO_TEXT -> Result == "
            "resolved_assembled) and the decisive P4 (Result == "
            "user_tr[first_provider(user_defines)]): resolved_assembled is defined "
            "over the FIXED [default]++project++[bundled] order; the bundled-ahead "
            "fold returns builtin_tr where the spec demands the project text. "
            "Exactly what G-DIFF detects."),
    },
    {
        "id": "bundled-wins-over-project-subdomain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_BUNDLED_WINS),
        "refinement": (
            "A surgically-minimal rival: correct first-wins resolution EVERYWHERE "
            "except the decisive sub-domain (env default provides nothing, a "
            "project source provides, the bundled source ALSO provides), where it "
            "returns the BUNDLED text. Its faithful real patch keeps the correct "
            "order but special-cases the bundled catalog to take precedence when "
            "both provide (e.g. moving package_dir/'locale' back to the front only "
            "when it has the entry) — on the F2P input "
            "(project 'QUICK SEARCH' over bundled 'da') it returns the bundled "
            "value, so test_customize_system_message FAILS. It does not resolve. "
            "This is the partial-domain attack pinned to the exact failing input."),
        "rationale": (
            "Rejected by the decisive P4 (Result == user_tr[first_provider]) and "
            "P2: on the sub-domain it returns builtin_tr, but first_provider is a "
            "project index whose text user_tr[fp] (>= 1) differs from builtin_tr in "
            "the witnessing model where they are distinct codes. Demonstrates the "
            "spec is tight on the precise project-overrides-bundled point."),
    },
    {
        "id": "last-wins-forward-fold",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_LAST_WINS),
        "refinement": (
            "A forward fold that lets a LATER source overwrite an earlier one "
            "(last-wins). Its faithful real patch misuses gettext as if "
            "add_fallback PREPENDED / the LAST source in locale_dirs won — e.g. "
            "iterating locale_dirs and reassigning the primary translator each "
            "time. Then the bundled fallback (last in [default]++project++[bundled]) "
            "wins over a project override, so 'Quick search' resolves to the "
            "bundled `da` value and test_customize_system_message FAILS. It also "
            "regresses every message two sources provide. It does not resolve."),
        "rationale": (
            "Rejected by P2 (Result == resolved_assembled): `resolved` is "
            "first-wins (returns the FIRST provider in order); the forward fold "
            "returns the LAST provider, which differs whenever >= 2 sources "
            "provide. The self-contained forward loop carries its own simple "
            "invariants, so the rejection is the output mismatch, not a proof gap."),
    },
    {
        "id": "pos-control-grounded-oracle-delegate",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DELEGATE),
        "rationale": (
            "Directive-2 grounded-oracle positive control: resolved_assembled is "
            "fully unfolded over the inputs (not an opaque answer key), so "
            "returning it directly (with the NO_TEXT fall-back) IS the gold "
            "behaviour and MUST verify. The decisive-clause proof glue "
            "(_resolution_picks_user / lemma_first_provider_bound) is kept verbatim "
            "so P3/P4 discharge. If this CORRECT impl failed => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-branch-reorder-no-text",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "Structurally different but correct: the entire gold backward-fold "
            "proof (framing asserts + invariants + decisive-clause glue) is kept "
            "VERBATIM; only the final out-selection is reshaped to test the "
            "NO_TEXT case first (out = message; if res != NO_TEXT(): out = res) — "
            "semantically identical. No new lemma needed (directive 5a/5b: no "
            "framing assert dropped). MUST verify (else the postcondition is "
            "over-fit to the gold out-selection shape => SPEC-TOO-STRONG)."),
    },
    {
        "id": "admissibility-f2p-shaped-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "The impl DELEGATES to a self-call on the SAME in-scope inputs and "
            "returns its result. The caller holds exactly the callee Requires "
            "(Acc(.,1/2) of the two project lists, len-equality, real-text-where- "
            "provided, message>=1), so the precondition is establishable for a "
            "legitimate input and the call site verifies (else PRECOND-TOO-STRONG); "
            "the callee's Ensures returns the half-permissions AND pins the result "
            "to the first-wins resolution, so returning it directly discharges this "
            "method's own postcondition. Editing only the impl region keeps "
            "same_spec true. (Delegate-and-return, NOT a self-call spliced ahead of "
            "the gold body: the read-only-input contract's Ensures returns the "
            "list_pred permission but does not restate the quantified element fact "
            "nor pin the input sequences unchanged, so a spliced call would havoc "
            "the gold loop invariant / postcondition P2 — a framing/composability "
            "limitation of splicing, not precond strength.)"),
    },
]

# ===========================================================================
# AXIOM LANE — A-reference deep model `resolved` vs the real stdlib gettext.
# ===========================================================================
# meta.json axioms=[] (no consumed @ContractOnly axiom). The single kind-A
# obligation is the A-REFERENCE deep model (deep_model_references[0]): `resolved`
# must equal the real gettext merge/lookup the changed code relies on. We embed
# axiom_check.py's exact reference + real-callee logic so each probe is
# self-contained (the runner mounts only the probe script). stdlib-only import.

# axiom_check.py reference logic, embedded verbatim (read on the HOST at load
# time so the probe needs nothing mounted). This is the genuine gettext
# merge/lookup the changed code uses (NullTranslations.add_fallback +
# GNUTranslations.gettext semantics), not a source scrape.
_AX_COMMON = r'''
import gettext, random, sys

NO_TEXT = 0

def model_resolved(defines, tr):
    """Reference of model.py `resolved`: text of the FIRST source (in order)
    that provides, else NO_TEXT. Front-recursive fold == this linear scan."""
    for d, t in zip(defines, tr):
        if d:
            return t
    return NO_TEXT

class _Cat(gettext.NullTranslations):
    """Real gettext translations object, in-memory catalog. Uses the genuine
    NullTranslations.add_fallback chaining; per-catalog lookup matches
    GNUTranslations.gettext (entry present -> return it; else descend the chain;
    else the message itself)."""
    def __init__(self, catalog):
        super().__init__()
        self._catalog = dict(catalog)
    def gettext(self, message):
        if message in self._catalog:
            return self._catalog[message]
        if self._fallback:
            return self._fallback.gettext(message)
        return message

def real_resolve(sources, message):
    """Merge `sources` (each a dict msg->text, in order; None == skipped) with
    the REAL gettext add_fallback chain -- exactly sphinx.locale.init -- and look
    `message` up."""
    translator = None
    for cat in sources:
        if cat is None:
            continue
        trans = _Cat(cat)
        if translator is None:
            translator = trans
        else:
            translator.add_fallback(trans)
    if translator is None:
        translator = gettext.NullTranslations()
    return translator.gettext(message)

def check_case(message_text, source_specs):
    """Assert the REAL merged gettext lookup of `message_text` equals the model's
    first-wins fold over the same ordered sources (under a code bijection)."""
    texts = [message_text]
    for spec in source_specs:
        if spec:
            for v in spec.values():
                if v not in texts:
                    texts.append(v)
    mapping = {t: i + 1 for i, t in enumerate(texts)}
    message_code = mapping[message_text]
    real_text = real_resolve(source_specs, message_text)
    real_code = mapping.get(real_text, None)
    assert real_code is not None, (
        "real gettext produced an unexpected text %r" % (real_text,))
    defines = []
    tr = []
    for spec in source_specs:
        if spec and message_text in spec:
            defines.append(True)
            tr.append(mapping[spec[message_text]])
        else:
            defines.append(False)
            tr.append(NO_TEXT)
    model_res = model_resolved(defines, tr)
    if model_res == NO_TEXT:
        model_res = message_code
    assert real_code == model_res, (
        "first-wins precedence mismatch on message %r over sources %r: real "
        "gettext -> %r (code %d), model -> code %d"
        % (message_text, source_specs, real_text, real_code, model_res))
'''

_AX_SOUNDNESS = _AX_COMMON + r'''
def main():
    # Decisive sphinx scenario (the F2P behaviour): order [default] ++ project
    # ++ bundled; the project override must win over the bundled fallback.
    msg = "Quick search"
    project = {msg: "QUICK SEARCH"}
    bundled = {msg: "Hurtig sogning", "Other": "Andet"}
    fixed = real_resolve([None, project, bundled], msg)
    assert fixed == "QUICK SEARCH", (
        "post-fix order must select the project override, got %r" % (fixed,))
    buggy = real_resolve([None, bundled, project], msg)
    assert buggy == "Hurtig sogning", (
        "pre-fix order selects the bundled value (the bug), got %r" % (buggy,))

    M = "m"; A, B, C = "A", "B", "C"
    boundary = [
        [], [None], [None, None],
        [{M: A}], [{}],
        [{M: A}, {M: B}], [{M: B}, {M: A}],
        [{}, {M: A}], [{M: A}, {}],
        [None, {M: A}, {M: B}],
        [None, {M: A}, {M: B}, {M: C}],
        [{"other": A}, {M: B}], [{"other": A}],
        [None, {"x": A}, {M: B}, {M: C}],
    ]
    for spec in boundary:
        check_case(M, spec)

    rng = random.Random(8120)
    texts = ["A", "B", "C", "D", "E"]
    for _ in range(20000):
        nsrc = rng.randint(0, 6)
        specs = []
        for _ in range(nsrc):
            r = rng.random()
            if r < 0.2:
                specs.append(None)
            elif r < 0.45:
                specs.append({})
            else:
                d = {M: rng.choice(texts)}
                if rng.random() < 0.5:
                    d["noise"] = rng.choice(texts)
                specs.append(d)
        check_case(M, specs)

    print("AXIOM-SOUNDNESS OK: deep model `resolved` == real gettext "
          "merge/lookup over %d boundary + 20000 fuzz orderings; decisive "
          "project-overrides-bundled scenario sound." % len(boundary))
    sys.exit(0)

main()
'''

_AX_CONTAINMENT = _AX_COMMON + r'''
def main():
    # CONTAINMENT: every (defines, tr) ordering the MODEL can reach must be a
    # VALID input to the real gettext merge/lookup (its Requires domain). The
    # model can reach: any chain length n = 2 + len(user) (>= 2), any subset of
    # providing sources, any int text codes (>= 1 where provided), any message
    # (>= 1). The real callee's domain is TOTAL over chains of catalogs / any
    # hashable message -- gettext.translation merge + *.gettext accept any catalog
    # chain and never error on a lookup. We enumerate the model-reachable SHAPES
    # (n from 0..6, every providing-subset, with/without a leading skipped
    # default and trailing bundled) and assert the real lookup completes WITHOUT
    # error and lands inside the catalog-text set -- i.e. every caller-reachable
    # input lies in the callee domain (no AXIOM-TOO-WEAK-FOR-CALLER gap).
    import itertools
    M = "m"
    texts = ["A", "B", "C"]
    checked = 0
    # All assembled orders the model builds: [default] ++ project(0..4) ++ [bundled],
    # default and bundled possibly providing, each project source providing or not.
    for nproj in range(0, 5):
        for provmask in itertools.product([False, True], repeat=nproj + 2):
            # provmask[0] = default provides?, provmask[-1] = bundled provides?,
            # the middle = each project source provides?
            specs = []
            for k, prov in enumerate(provmask):
                if prov:
                    specs.append({M: texts[k % len(texts)]})
                else:
                    # a non-providing source: present but no entry for M, OR a
                    # skipped source (None) for the leading default sometimes.
                    if k == 0:
                        specs.append(None)   # default skipped (system_defines=False)
                    else:
                        specs.append({})     # source present, no entry for M
            # Real callee must complete without error on this model-reachable shape.
            try:
                real_text = real_resolve(specs, M)
            except Exception as e:  # pragma: no cover
                print("CONTAINMENT VIOLATION: real gettext errored on a "
                      "model-reachable order %r: %r" % (specs, e))
                sys.exit(1)
            # And the result is a valid text (a catalog value or the untranslated
            # message) -- inside the callee's value domain.
            valid = {M}
            for s in specs:
                if s:
                    valid.update(s.values())
            assert real_text in valid, (
                "real gettext returned a text outside the catalog/value domain: "
                "%r not in %r (order %r)" % (real_text, valid, specs))
            # And it AGREES with the model fold (containment + soundness on the
            # reachable shape).
            check_case(M, specs)
            checked += 1
    print("AXIOM-CONTAINMENT OK: %d model-reachable assembled orders all lie in "
          "the real gettext domain (lookup completes, lands in the value domain, "
          "and matches the deep model). Containment is total -- no caller-reachable "
          "input escapes the callee domain." % checked)
    sys.exit(0)

main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-soundness-resolved-vs-gettext",
        "axiom": "resolved",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS,
        "rationale": (
            "The A-reference deep model `resolved` (first-wins precedence) must "
            "equal the REAL stdlib gettext merge/lookup the changed code relies "
            "on (NullTranslations.add_fallback chain + GNUTranslations.gettext). "
            "The probe builds REAL gettext translation objects, chains them with "
            "the genuine add_fallback, and asserts merged.gettext(message) == "
            "`resolved` over 14 boundary + 20000 fuzz orderings plus the decisive "
            "project-overrides-bundled scenario. No flag dependency (gettext's "
            "merge/lookup uses no configurable mode here). Any mismatch => "
            "AXIOM-UNSOUND."),
    },
    {
        "id": "ax-containment-resolved-domain",
        "axiom": "resolved",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": (
            "Every assembled order the MODEL can reach "
            "([default] ++ project(0..4) ++ [bundled], any providing-subset) must "
            "lie in the real gettext callee's domain. The probe enumerates those "
            "shapes and asserts the real merge/lookup completes without error, "
            "lands in the catalog/value domain, and matches the deep model. "
            "gettext accepts any chain of catalogs / any message, so containment "
            "is total; a reachable order outside the domain would be "
            "AXIOM-TOO-WEAK-FOR-CALLER."),
    },
]
