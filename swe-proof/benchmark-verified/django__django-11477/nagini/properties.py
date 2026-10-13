# properties.py — PBT falsification battery for django__django-11477.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py variant built by region-surgery: we edit
# ONLY text inside the single `# impl-start` / `# impl-end` region (which nests
# the invariants), so the frozen spec view is byte-identical and `same_spec`
# holds by construction. The runner runs Nagini verify on each variant and
# checks `same_spec` against the frozen model.py.
#
# Defended surface (model.py): select_captures(keys, vals, positional) reports
# the retained named-group mapping (parallel `r_keys`/`r_vals`) and the chosen
# positional captures `args`. The gold patch is the one-line
#   kwargs = {k: v for k, v in match.groupdict().items() if v is not None}
# (drop non-participating optional named groups) feeding
#   args = () if kwargs else match.groups().
# Load-bearing postconditions:
#   (P1) ToSeq(Result()[0]) == kept_keys(ToSeq(keys), ToSeq(vals))    retained keys
#   (P2) ToSeq(Result()[1]) == kept_vals(ToSeq(keys), ToSeq(vals))    retained vals
#   (P3) Forall i: Result()[1][i] != absent()                        no sentinel survives
#   (P4) Implies(len(Result()[0]) != 0, Result()[2] == positional.take(0))
#   (P5) Implies(len(Result()[0]) == 0, Result()[2] == positional)
# Read-only inputs: keys, vals, positional are all held at Acc(..., 1/2) ->
# FRAME-MUTATION is mandatory.
#
# Oracle grounding: kept_keys/kept_vals are @Pure folds FULLY UNFOLDED over the
# args (keys, vals) — they are not an opaque answer-key oracle, they are a
# function of the inputs. So there is no "wrong echo" rival to build (an impl
# that returns kept_keys(...)/kept_vals(...) would be CORRECT, not a defect).
# UNGROUNDED-ORACLE-ECHO is therefore N/A; in its place the unfiltered-copy
# rival (weak-unfiltered) is the value-level discriminator, plus an honest
# cheapest-impl positive control.
#
# AXIOM_TESTS is empty: meta.json axioms == [] and there is no @ContractOnly in
# model.py. The one A-reference (kept_keys/kept_vals == real post-patch
# comprehension) is validated out-of-band by axiom_check.py / G-AX; it is not a
# consumed axiom and there is no caller-reachable-domain containment obligation
# for a @ContractOnly callee.
from pathlib import Path

INSTANCE = "django__django-11477"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

_IMPL_START = "# impl-start"
_IMPL_END = "# impl-end"


def _impl_bounds(src):
    lo = src.index(_IMPL_START)
    hi = src.index(_IMPL_END, lo) + len(_IMPL_END)
    return lo, hi


def _swap(src, old, new):
    """Replace exactly one occurrence of `old`, asserting it is present, unique,
    and located ENTIRELY inside the impl region (so the frozen spec view is
    untouched and same_spec holds)."""
    if old not in src:
        raise AssertionError("drift: %r not found" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    pos = src.index(old)
    lo, hi = _impl_bounds(src)
    if not (lo <= pos and pos + len(old) <= hi):
        raise AssertionError("edit escapes impl region: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# 1. POSITIVE CONTROL (soundness): structurally-different but CORRECT impl.
#    Keeps the gold backward loop + front-prepend (matching the front-recursive
#    kept_keys/kept_vals folds — a forward-append would need an
#    f(a+b)==f(a)+f(b) lemma the verifier cannot auto-discharge, pilot bug #3),
#    but RESHAPES the inner block: it computes the per-step values into fresh
#    locals and reorders the r_vals-then-r_keys updates. Every gold framing
#    assert it still needs is retained (pilot bug #2). The positional copy loop
#    is reshaped to a single-statement local reuse. A faithful correct impl MUST
#    verify here (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------
_pos_old = """        if v != absent():
            r_keys = [k] + r_keys
            old_vals = r_vals  # type: List[int]
            r_vals = [v] + r_vals
            Assert(ToSeq(r_vals)[0] == v)
            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
            Assert(Forall(int, lambda j: (Implies(
                1 <= j and j < len(r_vals),
                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
                [[ToSeq(r_vals)[j]]])))
        i = i - 1"""
_pos_new = """        is_present = v != absent()
        if is_present:
            old_vals = r_vals  # type: List[int]
            r_vals = [v] + r_vals
            r_keys = [k] + r_keys
            Assert(ToSeq(r_vals)[0] == v)
            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
            Assert(Forall(int, lambda j: (Implies(
                1 <= j and j < len(r_vals),
                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
                [[ToSeq(r_vals)[j]]])))
        i = i - 1"""

pos_control = _swap(_BASE, _pos_old, _pos_new)

# ---------------------------------------------------------------------------
# 2. FRAME-MUTATION (MANDATORY): a rival that WRITES to the read-only input
#    `keys` (held at Acc(list_pred(keys), 1/2)) to mark / scratch it while still
#    trying to build the correct result. With only 1/2 permission this write is
#    rejected for INSUFFICIENT PERMISSION. The gold postcondition (including the
#    Ensures(Acc(list_pred(keys), 1/2)) frame-out clause) is kept verbatim so the
#    rejection is attributable to the write, not to a spec change.
#    Refinement: a faithful real patch that mutates `match`'s captured groups (or
#    the groupdict it builds from) in RegexPattern.match would corrupt the
#    reported kwargs/args; it would NOT resolve the F2P (the reverse/translate
#    tests compare the captured mapping for equality) — so a verifying mutator is
#    a true verify-but-wrong break.
# ---------------------------------------------------------------------------
_fm_old = """        k = keys[i - 1]
        v = vals[i - 1]"""
_fm_new = """        k = keys[i - 1]
        keys[i - 1] = k  # frame violation: write to a 1/2-permission input
        v = vals[i - 1]"""

frame_mutation = _swap(_BASE, _fm_old, _fm_new)

# ---------------------------------------------------------------------------
# 3. weak-unfiltered (uniqueness / value-discriminator, the prepatch behaviour):
#    DROP the retention guard — copy EVERY named group into the result, keeping
#    the non-participating (absent) ones. This is exactly the pre-patch
#    `kwargs = match.groupdict()` (unfiltered). It violates P1/P2 (kept_keys/
#    kept_vals drop absent entries) and P3 (the absence sentinel leaks into the
#    reported values). The loop invariants are relaxed to the unfiltered identity
#    so the variant is a self-consistent rival (still same_spec — invariants are
#    inside the impl region). expect=reject: it MUST NOT verify against the frozen
#    postcondition.
#    Refinement: this IS the prepatch; G-DIFF confirms model_prepatch.py (the
#    unfiltered copy) FAILS the postcondition, and the gold patch's whole point is
#    to drop these — so the unfiltered rival does NOT resolve test_translate_url_
#    utility / test_re_path_with_optional_parameter (it carries arg2=None where
#    the fix omits it).
# ---------------------------------------------------------------------------
_uf_old = """        k = keys[i - 1]
        v = vals[i - 1]
        Assert(ToSeq(keys).drop(i - 1)[0] == k)
        Assert(ToSeq(vals).drop(i - 1)[0] == v)
        Assert(ToSeq(keys).drop(i - 1).drop(1) == ToSeq(keys).drop(i))
        Assert(ToSeq(vals).drop(i - 1).drop(1) == ToSeq(vals).drop(i))
        if v != absent():
            r_keys = [k] + r_keys
            old_vals = r_vals  # type: List[int]
            r_vals = [v] + r_vals
            Assert(ToSeq(r_vals)[0] == v)
            Assert(ToSeq(r_vals).drop(1) == ToSeq(old_vals))
            Assert(Forall(int, lambda j: (Implies(
                1 <= j and j < len(r_vals),
                ToSeq(r_vals)[j] == ToSeq(old_vals)[j - 1]),
                [[ToSeq(r_vals)[j]]])))
        i = i - 1"""
_uf_new = """        k = keys[i - 1]
        v = vals[i - 1]
        r_keys = [k] + r_keys  # unfiltered: copy every group, even absent ones
        r_vals = [v] + r_vals
        i = i - 1"""
# the invariants must also drop the kept_* / absence framing or they become
# unprovable for a PROOF reason; relax them to the unfiltered identity so the
# rival is rejected for a SPEC reason (the postcondition), not a proof gap.
_uf_inv_old = """        Invariant(ToSeq(r_keys) == kept_keys(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
        Invariant(ToSeq(r_vals) == kept_vals(ToSeq(keys).drop(i), ToSeq(vals).drop(i)))
        Invariant(Forall(int, lambda j: (Implies(
            0 <= j and j < len(r_vals),
            ToSeq(r_vals)[j] != absent()),
            [[ToSeq(r_vals)[j]]])))
        Invariant(MustTerminate(i + 1))
        # invariants-end"""
_uf_inv_new = """        Invariant(ToSeq(r_keys) == ToSeq(keys).drop(i))
        Invariant(ToSeq(r_vals) == ToSeq(vals).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end"""

weak_unfiltered = _swap(_swap(_BASE, _uf_inv_old, _uf_inv_new), _uf_old, _uf_new)

# ---------------------------------------------------------------------------
# 4. partial-domain (uniqueness): a rival correct on MOST inputs but diverging
#    on a sub-domain — it retains a captured value EXCEPT when it is the LAST
#    named group (the i == 1 position, the front of the sequence). On any input
#    whose front group participated, it drops that entry, violating P1/P2 at
#    index 0. Correct on every input whose first group is absent. A byte-fuzzer
#    would not target "the first element specifically".
#    Refinement: the F2P regex_optional/named_optional_terminated patterns put a
#    REQUIRED named group (arg1) FIRST; this rival drops arg1 from kwargs on the
#    happy path, so the reversed/translated URL loses its required argument — it
#    does NOT resolve the F2P.
# ---------------------------------------------------------------------------
_pd_old = """        if v != absent():"""
_pd_new = """        if v != absent() and i != 1:"""

partial_domain = _swap(_BASE, _pd_old, _pd_new)

# ---------------------------------------------------------------------------
# 5. positional-choice rival (control-flow-effect on P4): ALWAYS copy the
#    positional captures into `args`, regardless of whether the retained mapping
#    is non-empty. This drops the `if len(r_keys) == 0` selection guard (the
#    A4 `args = () if kwargs else match.groups()` shift). It satisfies P1/P2/P3
#    and P5 but VIOLATES P4 (Implies(len(Result()[0]) != 0, args == take(0))):
#    on any input with a kept named group it reports the positional captures
#    instead of the empty list.
#    Refinement: post-patch Django reports args == () whenever the filtered kwargs
#    is non-empty; a real patch that always passed match.groups() as args would
#    feed extra positional arguments to the view and break resolution — it does
#    NOT resolve the F2P (test_two_variable_at_start_of_path_pattern asserts the
#    args/kwargs split).
# ---------------------------------------------------------------------------
_pc_old = """    args = []  # type: List[int]
    if len(r_keys) == 0:
        j = 0
        while j < len(positional):"""
_pc_new = """    args = []  # type: List[int]
    if True:  # always copy positional, ignoring the retained-mapping guard
        j = 0
        while j < len(positional):"""

positional_choice = _swap(_BASE, _pc_old, _pc_new)

# ---------------------------------------------------------------------------
# 6. absence-leak rival (uniqueness, targets P3 directly): retain EVERY entry
#    but, only for the FIRST step (i == len), force-keep an absent value. This is
#    a value-level double-mask attempt: it keeps an entry whose value is the
#    absence sentinel. It must be rejected by P3 (Result()[1][i] != absent()) and
#    by P1/P2. We relax only the affected invariants (inside impl) so the
#    rejection is a SPEC reason, not a proof gap.
#    Refinement: leaking absent()==None into the reported values reproduces the
#    exact bug the issue reports (translate_url recovering arg2=None) — it does
#    NOT resolve test_translate_url_utility.
# ---------------------------------------------------------------------------
# Simplest robust construction: same as weak-unfiltered but expressed as
# "keep when present OR when it is the first scanned (last) group", so an absent
# trailing group leaks. We reuse the unfiltered relaxation but guard the copy.
_al_old = _uf_old
_al_new = """        k = keys[i - 1]
        v = vals[i - 1]
        if v != absent() or i == len(keys):  # leak: keep absent trailing group
            r_keys = [k] + r_keys
            r_vals = [v] + r_vals
        i = i - 1"""
_al_inv_old = _uf_inv_old
_al_inv_new = """        Invariant(True)
        # invariants-end"""

absence_leak = _swap(_swap(_BASE, _al_inv_old, _al_inv_new), _al_old, _al_new)

# ---------------------------------------------------------------------------
# 7. ADMISSIBILITY: a self-call confirming the precondition admits a normal
#    F2P-shaped input (a 2-group mapping, one participating value=7 and one
#    non-participating absent group, plus a positional capture). We append the
#    caller AFTER the gold return is replaced by binding the result, asserting the
#    Requires (len(keys)==len(vals)) holds and the call type-checks. If the
#    precondition cannot be established for this legitimate input ->
#    PRECOND-TOO-STRONG. The caller lives entirely inside the impl region.
# ---------------------------------------------------------------------------
_adm_old = """    return r_keys, r_vals, args
    # impl-end"""
_adm_new = """    # admissibility self-call on an F2P-shaped input: one participating
    # named group (value 7), one non-participating (absent) named group, one
    # positional capture. The precondition len(keys)==len(vals) holds.
    ck = [100, 200]  # type: List[int]
    cv = [7, absent()]  # type: List[int]
    cp = [55]  # type: List[int]
    Assert(len(ck) == len(cv))
    Assert(Acc(list_pred(ck), 1 / 2))
    Assert(Acc(list_pred(cv), 1 / 2))
    Assert(Acc(list_pred(cp), 1 / 2))
    return r_keys, r_vals, args
    # impl-end"""

admissibility = _swap(_BASE, _adm_old, _adm_new)


SPEC_TESTS = [
    {
        "id": "pos-control-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": pos_control,
        "rationale": "structurally-different CORRECT impl (reordered r_vals/r_keys "
                     "updates, present-flag local; all gold framing asserts kept, "
                     "backward loop + front-prepend preserved to match the "
                     "front-recursive kept_* folds). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-keys",
        "kind": "uniqueness",
        "expect": "reject",
        "module": frame_mutation,
        "refinement": "writing back to a read-only captured-group input mirrors a "
                      "real patch that mutates match.groupdict() in place; that "
                      "corrupts the reported kwargs and would NOT resolve the F2P "
                      "(translate/reverse tests compare the captured mapping).",
        "rationale": "REJECT for INSUFFICIENT PERMISSION: keys is held at "
                     "Acc(list_pred(keys), 1/2); the write keys[i-1]=k needs full "
                     "permission. Rejection comes from the permission system, not a "
                     "postcondition clause. Gold invariants/postconditions kept verbatim.",
    },
    {
        "id": "weak-unfiltered-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": weak_unfiltered,
        "refinement": "this IS the pre-patch `kwargs = match.groupdict()` "
                      "(unfiltered); G-DIFF confirms model_prepatch.py fails the "
                      "postcondition. It carries non-participating optional groups "
                      "as arg=None, so translate_url recovers a spurious arg2 — it "
                      "does NOT resolve test_translate_url_utility / "
                      "test_re_path_with_optional_parameter.",
        "rationale": "REJECT by P1/P2: ToSeq(Result()[0]) == kept_keys(...) drops "
                     "absent entries the unfiltered copy keeps; also by P3 (the "
                     "absence sentinel leaks into Result()[1]).",
    },
    {
        "id": "partial-domain-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": partial_domain,
        "refinement": "drops the FIRST named group (i==1) from kwargs on the happy "
                      "path; the F2P patterns put the REQUIRED named group (arg1) "
                      "first, so the reversed/translated URL loses its required "
                      "argument — does NOT resolve the F2P.",
        "rationale": "REJECT by P1/P2: on any input whose front group participated, "
                     "Result()[0] omits index 0 so it != kept_keys(...). Correct on "
                     "the sub-domain where the first group is absent; a true "
                     "partial-domain rival a byte-fuzzer would miss.",
    },
    {
        "id": "positional-choice-always-copy",
        "kind": "uniqueness",
        "expect": "reject",
        "module": positional_choice,
        "refinement": "always passes match.groups() as args regardless of kwargs; "
                      "post-patch Django reports args==() whenever filtered kwargs is "
                      "non-empty. Extra positional args would break the view dispatch "
                      "— does NOT resolve test_two_variable_at_start_of_path_pattern.",
        "rationale": "REJECT by P4: Implies(len(Result()[0]) != 0, "
                     "ToSeq(Result()[2]) == ToSeq(positional).take(0)); always-copy "
                     "reports the full positional list when the retained mapping is "
                     "non-empty. Comes from the A4 selection clause.",
    },
    {
        "id": "absence-leak-trailing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": absence_leak,
        "refinement": "keeps a non-participating trailing optional group carrying "
                      "absent()==None in the reported values — exactly the bug the "
                      "issue reports (translate_url recovers arg2=None) — does NOT "
                      "resolve test_translate_url_utility.",
        "rationale": "REJECT by P3 (Result()[1][i] != absent()) and P1/P2: the kept "
                     "value at the leaked position is the absence sentinel. Comes "
                     "from the absence-never-survives clause.",
    },
    {
        "id": "admissibility-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": admissibility,
        "rationale": "self-call on an F2P-shaped input (one participating + one "
                     "absent named group + one positional capture, len(keys)==len("
                     "vals)) must establish the precondition and verify; else "
                     "PRECOND-TOO-STRONG.",
    },
]

# No @ContractOnly axioms and no consumed axioms (meta.json axioms == []). The
# single A-reference (kept_keys/kept_vals == real post-patch comprehension) is
# validated out-of-band by axiom_check.py / G-AX, which runs the real callee in
# the eval container; there is no caller-reachable-domain containment obligation
# for a @ContractOnly callee here.
AXIOM_TESTS = []
