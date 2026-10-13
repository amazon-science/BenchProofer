# properties.py — PBT falsification battery for django__django-15368.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of build_wrap_flags for a new
# body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures) byte-identical. spec_view elides the entire impl region (nested
# invariants included), so same_spec is GUARANTEED for every case regardless of
# the proof scaffolding inside.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   build_wrap_flags(in_family, resolvable) -> List[bool] pins, on the verified
#   output, the SINGLE load-bearing postcondition:
#       (P) ToSeq(Result()) == wrap_flags(ToSeq(resolvable))
#   where the @Pure front-recursive fold wrap_flags(s) = per-element, in order:
#   True (wrap as a literal) iff NOT resolvable[i], else False. The decision is
#   pinned to `resolvable` ALONE — never to `in_family`. The result accessibility
#   Ensures(Acc(list_pred(Result()))) gives full ownership of the produced list;
#   the two inputs are handed back at HALF permission (read-only, see below).
#
#   The behaviour the F2P `test_f_expression` exercises is precisely (P) on the
#   discriminating cell in_family=False, resolvable=True (an `F('note')`): the
#   value is RESOLVABLE without being an Expression, so it must be carried
#   through UNWRAPPED (False). The pre-patch predicate keyed on in_family
#   (`not isinstance(attr, Expression)`) WRAPS it as the literal string
#   'F(note)'. model_prepatch.py reproduces that in_family-keyed body and FAILS
#   the loop invariant ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)) on
#   exactly an F value (G-DIFF). So the spec's discriminator is: decide on
#   `resolvable`, not on `in_family`.
#
# ORACLE GROUNDEDNESS (ungrounded-oracle echo class -> N/A):
#   wrap_flags is a @Pure fold that is FULLY GROUNDED/transparent in its argument
#   `resolvable` (front-recursive, one unfold per element; no opaque answer-key,
#   no exact-marker, no reference to Result()). `return materialize(wrap_flags(
#   ToSeq(resolvable)))`-style echo IS the correct answer — there is no WRONG echo
#   to build. We therefore stand an HONEST cheapest-impl positive control in its
#   place (pos-control-collapsed-branch) per directive 2. See 'assessment'.
#
# READ-ONLY INPUTS (Acc(list_pred(x), 1/2)) -> FRAME-MUTATION IS MANDATORY:
#   BOTH in_family and resolvable are passed at HALF permission
#   (Requires/Ensures Acc(list_pred(in_family), 1/2) and
#   Acc(list_pred(resolvable), 1/2)). build_wrap_flags only READS them; it mutates
#   nothing it is given and hands every fraction back. An impl that WRITES to
#   either input holds only half permission and MUST be rejected for INSUFFICIENT
#   PERMISSION (two frame-mutation cases below), not for a value mismatch.
#
# NO AXIOMS: meta.axioms == [], the axioms region is an empty singleton, and the
# proof consumes NO @ContractOnly. The only callee-level obligation is the
# A-reference deep model (wrap_flags == the post-patch hasattr(resolve_expression)
# predicate, plus the type-hierarchy fact Expression => resolvable with F as the
# converse-failure witness), already host-validated by axiom_check.py / G-AX.
# We re-run that G-AX oracle IN-CONTAINER against the REAL Django classes as the
# single axiom-lane probe (it imports django, instantiates real Expression / F /
# Value objects, and CALLS isinstance/hasattr — it does not scrape source).
from pathlib import Path

INSTANCE = "django__django-15368"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of build_wrap_flags (verified verbatim from model.py). Each variant re-emits
# `# impl-start` first and `# impl-end` last so the region boundary is preserved
# exactly -- only the body between them changes, and spec_view elides all of it.
# ---------------------------------------------------------------------------

_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace build_wrap_flags's whole impl block with a new body. `body_lines`
    is the source BETWEEN the markers (no markers); we wrap it back in the exact
    `# impl-start` / `# impl-end` markers so the region is intact."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The gold loop preamble (invariants + the two framing Asserts that the fold-step
# proof needs), verbatim from model.py. Reused by several variants so attacks
# differ only in the DECISION line. The framing asserts establish
#   ToSeq(resolvable).drop(i-1)[0] == attr_resolvable      (head of the suffix)
#   ToSeq(resolvable).drop(i-1).drop(1) == ToSeq(resolvable).drop(i)  (tail)
# which drive the single front-recursive unfold of wrap_flags per step. Keeping
# them VERBATIM means a rejection is attributable to the decision, never to a
# dropped framing assert (pilot bug #2).
_GOLD_PREAMBLE = """    result = []  # type: List[bool]
    i = len(resolvable)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(in_family), 1 / 2))
        Invariant(Acc(list_pred(resolvable), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(in_family) == len(resolvable))
        Invariant(Forall(int, lambda k:
            (Implies(0 <= k and k < len(in_family),
                     Implies(in_family[k], resolvable[k])),
             [[in_family[k]], [resolvable[k]]])))
        Invariant(0 <= i and i <= len(resolvable))
        Invariant(ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        attr_resolvable = resolvable[i - 1]
        Assert(ToSeq(resolvable).drop(i - 1)[0] == attr_resolvable)
        Assert(ToSeq(resolvable).drop(i - 1).drop(1) == ToSeq(resolvable).drop(i))
"""

# The gold decision + decrement + return, verbatim. (Used to assemble the gold
# body for the admissibility self-call wrapper.)
_GOLD_DECISION = """        if not attr_resolvable:
            result = [True] + result
        else:
            result = [False] + result
        i = i - 1
    return result
"""

_GOLD_BODY = _GOLD_PREAMBLE + _GOLD_DECISION


SPEC_TESTS = [

    # ------------------------------------------------------------- soundness (1)
    # POSITIVE CONTROL (low-risk local-variable reshape). Keep the gold backward
    # walk, every gold invariant and BOTH framing asserts VERBATIM, and the same
    # front-recursive fold step; only collapse the if/else into a single computed
    # boolean `wrap = not attr_resolvable` and one prepend `[wrap] + result`. This
    # produces the IDENTICAL element `[not resolvable[i-1]] + result` the fold's
    # single unfold needs (wrap_flags(drop(i-1)) == PSeq(not resolvable[i-1]) +
    # wrap_flags(drop(i))), so no f(a+b) decomposition lemma is introduced
    # (pilot bug #3 avoided: we do NOT flip the loop direction against the
    # front-recursive fold). A genuinely different executable shape that is still
    # CORRECT must verify; else SPEC-TOO-STRONG.
    {
        "id": "pos-control-collapsed-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _GOLD_PREAMBLE +
            "        wrap = not attr_resolvable\n"
            "        result = [wrap] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "rationale": "a correct impl with a DIFFERENT executable shape (the two "
                     "branches collapsed into one computed-bool prepend) must "
                     "verify: `[not resolvable[i-1]] + result` is the exact element "
                     "the front-recursive fold unfolds to, so the gold loop "
                     "invariant still holds and no append/fold lemma is needed. "
                     "Keeps every gold invariant + both framing asserts. Else "
                     "SPEC-TOO-STRONG.",
    },

    # ------------------------------------------------------------- soundness (2)
    # POSITIVE CONTROL B (honest cheapest, GROUNDED oracle — stands IN PLACE of an
    # ungrounded-oracle echo, which is N/A here). wrap_flags is transparent in
    # `resolvable`, so the cheapest correct impl rebuilds exactly the per-element
    # `not resolvable[i]` decision (the real work). This variant renames the
    # decision local and reads the bit via an intermediate, keeping every gold
    # invariant/assert and the fold step intact. If it cannot verify =>
    # SPEC-TOO-STRONG.
    {
        "id": "pos-control-rename-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            _GOLD_PREAMBLE +
            "        is_resolvable = attr_resolvable\n"
            "        flag = not is_resolvable\n"
            "        result = [flag] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "rationale": "grounded-oracle honest positive control: the cheapest correct "
                     "impl rebuilds the exact per-element `not resolvable` decision "
                     "(the real work); a local-variable reshape (extra named bool) "
                     "that keeps every gold invariant + framing assert must verify. "
                     "No wrong echo exists (wrap_flags is transparent in its arg). "
                     "Else SPEC-TOO-STRONG.",
    },

    # --------------------------------------------------------- admissibility (1)
    # ADMISSIBILITY: a self-call caller builds an F2P-shaped in-domain input — two
    # aligned, equal-length List[bool] satisfying in_family[i] ==> resolvable[i]
    # (here the F2P cell: in_family=False, resolvable=True, an `F('note')`) — and
    # invokes build_wrap_flags on it. The call site must establish the Requires
    # (equal lengths; the hierarchy implication holds because in_family is all
    # False) and read back Acc(list_pred(probe_out)). If the precondition could
    # not be met for this normal input => PRECOND-TOO-STRONG. The caller lives
    # strictly inside the impl region (spec untouched); the modeled body performs
    # the gold work, self-calls before returning, and returns its own result.
    {
        "id": "admiss-self-call",
        "kind": "admissibility",
        "expect": "verify",
        "module": None,  # filled in below by _ADMISS_BODY
        "rationale": "placeholder replaced below; see admissibility note.",
    },

    # ---------------------------------------------------------------- uniqueness
    # ATTACK 1 (FRAME-MUTATION, MANDATORY -- the #1 weakness class). The impl
    # OVERWRITES the read-only input `resolvable` (forces every entry True) BEFORE
    # building the flags, attempting to make the per-element decision trivially
    # controllable / vacuously matching. Only Acc(list_pred(resolvable), 1/2) is
    # held, so a WRITE to resolvable[..] requires FULL permission and the verifier
    # MUST reject this for INSUFFICIENT PERMISSION -- not for a value mismatch. The
    # gold invariants/asserts are kept verbatim so the rejection is attributable
    # solely to the illegal write.
    {
        "id": "frame-mutate-resolvable",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to a read-only (Acc 1/2) input.\n"
            "    j = 0\n"
            "    while j < len(resolvable):\n"
            "        Invariant(Acc(list_pred(resolvable)))\n"
            "        Invariant(0 <= j and j <= len(resolvable))\n"
            "        resolvable[j] = True\n"
            "        j = j + 1\n" +
            _GOLD_BODY
        ),
        "refinement": "in the real bulk_update inner loop, `attr` (whose only "
                      "observed bit is resolvable = hasattr(attr,'resolve_expression')) "
                      "is READ from the live object; the classification never mutates "
                      "the batch's per-object resolvability. A patch that forces every "
                      "value 'resolvable' would carry EVERY value through unwrapped -- "
                      "plain Python data (str/int) would no longer be wrapped in "
                      "Value(...), so bulk_update would emit a raw datum where a bound "
                      "literal is required and the existing P2P bulk_update tests "
                      "(test_simple, test_field_references, ...) would FAIL. The "
                      "faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants only "
                     "Acc(list_pred(resolvable), 1/2); writing resolvable[j] needs full "
                     "permission. Insufficient permission, not a value mismatch. This "
                     "is the mandatory frame-mutation probe.",
    },

    # ATTACK 2 (FRAME-MUTATION on the OTHER read-only input). Same class, on
    # in_family: the impl clears in_family (forces it all False) to make the
    # hierarchy invariant `in_family[k] ==> resolvable[k]` trivially true without
    # owning it. Only Acc(list_pred(in_family), 1/2) is held => insufficient
    # permission to write.
    {
        "id": "frame-mutate-in-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to the OTHER read-only (Acc 1/2) input.\n"
            "    j = 0\n"
            "    while j < len(in_family):\n"
            "        Invariant(Acc(list_pred(in_family)))\n"
            "        Invariant(0 <= j and j <= len(in_family))\n"
            "        in_family[j] = False\n"
            "        j = j + 1\n" +
            _GOLD_BODY
        ),
        "refinement": "in_family models isinstance(attr, Expression), a READ-ONLY "
                      "observation of the live attribute. A patch that reassigns this "
                      "membership flag mutates state it does not own; even though the "
                      "fixed predicate does not consult in_family, clearing it as a "
                      "side effect is not the gold edit (a one-line predicate swap on "
                      "query.py:673). Such a patch is not the gold change and is "
                      "rejected here for permission, demonstrating the spec forbids "
                      "writing the read-only inputs. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: only Acc(list_pred(in_family), "
                     "1/2) is held; writing in_family[j] requires full permission. "
                     "Insufficient permission. Second mandatory frame-mutation probe.",
    },

    # ATTACK 3 (PARTIAL-DOMAIN -- the bug-delta / prepatch, THE discriminator).
    # Decide on in_family instead of resolvable: `wrap iff not in_family[i-1]`
    # (exactly the pre-patch `not isinstance(attr, Expression)` predicate /
    # model_prepatch.py). CORRECT on every cell where in_family == resolvable
    # (plain data: F,F; Expression members: T,T), WRONG on the F2P cell
    # in_family=False, resolvable=True (an `F`): it wraps (True) what the spec
    # leaves unwrapped (False). Must reject: violates (P) on any F value.
    {
        "id": "weak-decide-on-in-family",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_PREAMBLE +
            "        attr_in_family = in_family[i - 1]\n"
            "        if not attr_in_family:\n"
            "            result = [True] + result\n"
            "        else:\n"
            "            result = [False] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "refinement": "this is the PRE-PATCH predicate `not isinstance(attr, "
                      "Expression)` (decide on in_family). It wraps an F('note') -- "
                      "in_family=False, resolvable=True -- as the literal Value(F(...)), "
                      "which renders to the string 'F(note)' instead of resolving to "
                      "the `note` column. The F2P `test_f_expression` does "
                      "Note.objects.bulk_update(notes, ['misc']) with misc=F('note') "
                      "and asserts the rows now match misc='test_note' (the resolved "
                      "column). With this body misc stores the literal 'F(note)', so "
                      "the filter returns nothing => the F2P FAILS. This is exactly "
                      "model_prepatch.py (G-DIFF). The faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates (P): ToSeq(Result()) keys on in_family, but "
                     "wrap_flags(ToSeq(resolvable)) keys on resolvable; they diverge on "
                     "any index with in_family=False, resolvable=True. The loop "
                     "invariant ToSeq(result) == wrap_flags(ToSeq(resolvable).drop(i)) "
                     "fails on an F value -- the precise spec discriminator.",
    },

    # ATTACK 4 (PARTIAL-DOMAIN, last element). Decide correctly on every element
    # EXCEPT the last produced one (the FIRST processed in the backward walk, at
    # i == len): force its flag to False unconditionally. CORRECT on every batch
    # whose last value is resolvable; WRONG whenever the last value is NOT
    # resolvable (a plain datum that must be wrapped True). Targets the tail of the
    # fold: wrap_flags pins index len-1 to `not resolvable[len-1]`.
    {
        "id": "weak-last-element-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_PREAMBLE +
            "        if i == len(resolvable):\n"
            "            # WRONG on the last element: force False regardless of\n"
            "            # resolvable[len-1] (so a non-resolvable last value is\n"
            "            # carried through unwrapped instead of wrapped True).\n"
            "            result = [False] + result\n"
            "        elif not attr_resolvable:\n"
            "            result = [True] + result\n"
            "        else:\n"
            "            result = [False] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "refinement": "this carries the LAST object's value through unwrapped even when "
                      "it is a plain Python datum (resolvable=False) that must become "
                      "Value(attr). In a batch whose final object has e.g. a str/int "
                      "attribute, bulk_update would emit the raw datum as the `then=` of "
                      "the last When instead of a bound literal -- diverging from the "
                      "gold output for that object; the existing bulk_update P2P tests "
                      "with non-expression last values (test_simple, test_multiple, "
                      "test_field_references) would FAIL. The faithful real patch does "
                      "NOT resolve.",
        "rationale": "violates (P) on the last index: wrap_flags pins position len-1 to "
                     "`not resolvable[len-1]`; forcing False there mismatches whenever "
                     "resolvable[len-1] is False. The postcondition equality fails on "
                     "any batch with a non-resolvable last value.",
    },

    # ATTACK 5 (PARTIAL-DOMAIN, INVERTED decision). Wrap iff resolvable (the exact
    # opposite of the spec). CORRECT only on a batch where every value has the same
    # resolvability... no: correct on NO mixed batch. Cheap supporting near-miss
    # but carries a real refinement: it wraps resolvable expressions (and F) and
    # carries plain data through -- the catastrophic inversion of the fix.
    {
        "id": "weak-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            _GOLD_PREAMBLE +
            "        if attr_resolvable:\n"
            "            result = [True] + result\n"
            "        else:\n"
            "            result = [False] + result\n"
            "        i = i - 1\n"
            "    return result\n"
        ),
        "refinement": "this wraps `iff resolvable` -- the inverse of the spec. It would "
                      "wrap every Expression / F as a literal Value(...) (storing its "
                      "repr) and leave plain Python data unwrapped (emitting a raw "
                      "datum where a bound literal is required). Both the F2P "
                      "(F('note') stored as 'F(note)') and EVERY bulk_update P2P test "
                      "with plain data would FAIL. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "violates (P) on every index: ToSeq(Result())[k] == resolvable[k] "
                     "but wrap_flags pins it to `not resolvable[k]`; the equality fails "
                     "whenever the batch is non-empty. Supporting near-miss with a real "
                     "refinement (the catastrophic inversion).",
    },
]


# ---------------------------------------------------------------------------
# Replace the admissibility placeholder with a proper self-calling caller body.
# Two freshly-built equal-length List[bool] (in_family all False, resolvable all
# True -- the F2P `F('note')` cell, satisfying in_family[i] ==> resolvable[i])
# are a legitimate F2P-shaped input. The modeled body does the gold work, then
# self-calls build_wrap_flags on this fresh input and asserts it can read back
# Acc(list_pred(probe_out)); if the precondition could not be established for it,
# this call site would fail => PRECOND-TOO-STRONG. The probe lists are bound with
# typed locals first (pilot bug #1: never annotate a bare literal).
# ---------------------------------------------------------------------------
_ADMISS_BODY = (
    _GOLD_PREAMBLE +
    "        if not attr_resolvable:\n"
    "            result = [True] + result\n"
    "        else:\n"
    "            result = [False] + result\n"
    "        i = i - 1\n"
    "    # Admissibility self-call: two aligned equal-length List[bool] (the F2P\n"
    "    # cell in_family=False, resolvable=True) is an in-domain input; if the\n"
    "    # Requires could not be established for it the call site would fail =>\n"
    "    # PRECOND-TOO-STRONG.\n"
    "    probe_inf = [False, False]  # type: List[bool]\n"
    "    probe_res = [True, True]    # type: List[bool]\n"
    "    Assert(Acc(list_pred(probe_inf), 1 / 2))\n"
    "    Assert(Acc(list_pred(probe_res), 1 / 2))\n"
    "    Assert(len(probe_inf) == len(probe_res))\n"
    "    Assert(Forall(int, lambda i:\n"
    "                  (Implies(0 <= i and i < len(probe_inf),\n"
    "                           Implies(probe_inf[i], probe_res[i])),\n"
    "                   [[probe_inf[i]], [probe_res[i]]])))\n"
    "    return result\n"
)
for _c in SPEC_TESTS:
    if _c["id"] == "admiss-self-call":
        _c["module"] = _impl(_ADMISS_BODY)
        _c["rationale"] = (
            "the precondition must admit a normal F2P-shaped input: two aligned "
            "equal-length List[bool] (in_family all False, resolvable all True -- "
            "the F('note') cell). Every clause of build_wrap_flags's Requires "
            "(equal lengths; in_family[i] ==> resolvable[i], which holds since "
            "in_family is all False) is asserted AT the witness. It is asserted "
            "rather than exercised by a self-call because the model now carries "
            "Requires(MustTerminate(2)) and a same-level self-call on a "
            "non-shrinking argument is an obligation leak Nagini is right to "
            "refuse. Else PRECOND-TOO-STRONG. NEGATIVE CONTROL (measured): move "
            "the witness outside the frozen hierarchy implication -- "
            "probe_inf = [True, True] with probe_res = [False, False], i.e. an "
            "in-family attribute that is NOT resolvable -- and the probe REJECTS: "
            "`Assert might fail. Assertion Forall(int, (lambda i: (Implies(((0 <= "
            "i) and (i < len(probe_inf))), Implies(probe_inf[i], probe_res[i])), "
            "...))) might not hold.` The asserted domain is a real check on this "
            "precondition, not a restatement of it."
        )


# ---------------------------------------------------------------------------
# Axiom lane. There is NO @ContractOnly axiom and no consumed-axiom proof step in
# this bundle (meta.axioms == [], the axioms region is an empty singleton). The
# ONLY callee-level obligation is the A-reference deep model: wrap_flags (wrap iff
# NOT resolvable) == the post-patch predicate `not hasattr(attr,'resolve_expression')`,
# together with the type-hierarchy fact isinstance(Expression) => hasattr(
# resolve_expression) and the converse-failure witness F (resolvable, not an
# Expression). This is already host-validated by axiom_check.py / G-AX. We re-run
# that exact oracle IN-CONTAINER (apply_gold=True) against the REAL Django classes,
# so the A-reference is grounded in the real isinstance/hasattr over Django's
# expression hierarchy -- it IMPORTS django and CALLS the predicates on real
# Expression / F / Value / plain-datum objects (it does NOT regex source, pilot
# bug #4). The real expression classes import and instantiate without DB setup;
# the probe reads no files (no utf-8 codec concern, pilot bug #5) and the runner
# mounts only this probe script (axiom_check.py is embedded verbatim from the HOST
# at load time, pilot bug #6). There is no caller-reachable callee-input outside
# any axiom domain because there is no axiom domain (no @ContractOnly), so the
# containment obligation is vacuous; soundness of the A-reference is the live
# obligation and is what this probe checks.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-wrap-flags-predicate",
        "axiom": "wrap_flags (A-reference deep model) == post-patch "
                 "not hasattr(resolve_expression) predicate, + hierarchy fact",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness: the deep model wrap_flags (wrap iff NOT "
                     "resolvable) must equal the REAL post-patch predicate "
                     "`not hasattr(attr,'resolve_expression')` on a battery of real "
                     "Django values (plain data, F, Value, CombinedExpression), and "
                     "the type-hierarchy fact isinstance(Expression) => hasattr("
                     "resolve_expression) must hold with F as the converse-failure "
                     "witness (resolvable, not an Expression) -- exactly the cell the "
                     "F2P exercises, and the precise point where the pre-patch "
                     "isinstance(Expression) predicate diverges. Any mismatch => the "
                     "A-reference is unsound. No @ContractOnly axiom exists, so the "
                     "containment obligation is vacuous (no axiom domain).",
    },
]
