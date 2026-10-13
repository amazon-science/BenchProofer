# properties.py — PBT falsification battery for django__django-15277.
#
# NOT a Nagini module: a manifest of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that share the FROZEN spec exactly (markers.same_spec) and
# differ ONLY inside the # impl-start/# impl-end regions; each is checked by
# Nagini verify. There are NO @ContractOnly axioms in this bundle (meta.axioms
# == []), so AXIOM_TESTS is empty — the three A-references are validated out of
# band by axiom_check.py / G-AX, not consumed by the proof.
#
# Defended surface (model.py):
#   compare_length(value_length:int, limit:Optional[int]) -> bool
#     Ensures(limit is not None)                       # normal return needs a concrete limit
#     Ensures(Result() == (value_length > limit))      # grounded in inputs (no oracle)
#     Exsures(LimitComparisonError, limit is None)     # absent limit => raise
#   build_char_validators(max_length:Optional[int]) -> List[Optional[int]]
#     Ensures(Acc(list_pred(Result())))
#     Ensures(Forall k. 0<=k<len ==> Result()[k] is not None)
#     Ensures(max_length is None  ==> len(Result()) == 0)
#     Ensures(max_length is not None ==> len(Result())==1 and Result()[0]==max_length)
#   clean_charfield(max_length:Optional[int], value_length:int) -> bool
#     (NO Exsures => running the assembled validators must be PROVABLY non-raising)
#     Ensures(max_length is None ==> Result() is False)
#     Ensures(max_length is not None ==> Result() == (value_length > max_length))
#
# Read-only inputs: NONE. Every input is an immutable scalar / Optional[int]
# (no Acc(x,1/2) heap parameter), so the frame-mutation probe is N/A here —
# there is no read-only heap input an impl could overwrite. The only heap object
# is the list build_char_validators *produces* (full perm, caller-owned). This
# is stated honestly in the structured-output assessment.

from pathlib import Path

INSTANCE = "django__django-15277"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact gold impl bodies (text inside the three # impl-start/# impl-end blocks).
# Every variant below is produced by _swap-ing exactly ONE of these on _BASE, so
# the spec regions are byte-for-byte untouched and same_spec is guaranteed.
# ---------------------------------------------------------------------------

_COMPARE_GOLD = """    # impl-start
    if limit is None:
        raise LimitComparisonError()
    return value_length > limit
    # impl-end"""

_BUILD_GOLD = """    # impl-start
    validators = []  # type: List[Optional[int]]
    if max_length is not None:
        validators.append(max_length)
    return validators
    # impl-end"""

_CLEAN_GOLD = """    # impl-start
    validators = build_char_validators(max_length)
    flagged = False
    if len(validators) > 0:
        limit = validators[0]
        flagged = compare_length(value_length, limit)
    return flagged
    # impl-end"""


def _compare(body):
    return _swap(_BASE, _COMPARE_GOLD, "    # impl-start\n" + body + "\n    # impl-end")


def _build(body):
    return _swap(_BASE, _BUILD_GOLD, "    # impl-start\n" + body + "\n    # impl-end")


def _clean(body):
    return _swap(_BASE, _CLEAN_GOLD, "    # impl-start\n" + body + "\n    # impl-end")


SPEC_TESTS = [

    # ===================== SOUNDNESS (positive controls) =====================
    # A structurally-DIFFERENT but CORRECT impl must verify; if a faithful
    # correct impl cannot satisfy the Ensures => SPEC-TOO-STRONG.

    {
        "id": "pos-build-conditional-return",
        "kind": "soundness",
        "expect": "verify",
        # Same behaviour as gold, reshaped: no mutate-then-return; build the two
        # result shapes by direct construction in each branch and early-return.
        "module": _build(
            "    if max_length is None:\n"
            "        empty = []  # type: List[Optional[int]]\n"
            "        return empty\n"
            "    out = [max_length]  # type: List[Optional[int]]\n"
            "    return out"),
        "rationale": "correct but structurally different (branch-and-return "
                     "instead of conditional-append); satisfies all four "
                     "build_char_validators posts. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-compare-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Same behaviour, reordered: handle the concrete-limit return first under
        # an explicit `is not None` guard, raise on the else. Keeps the gold
        # proof valid (no induction needed).
        "module": _compare(
            "    if limit is not None:\n"
            "        return value_length > limit\n"
            "    raise LimitComparisonError()"),
        "rationale": "correct, reordered (return-then-raise). Establishes "
                     "Ensures(limit is not None) on the normal path and the "
                     "Exsures on the raise path. Must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-clean-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Same behaviour, restructured: early-return False when no validator was
        # assembled; otherwise run the single assembled comparison.
        "module": _clean(
            "    validators = build_char_validators(max_length)\n"
            "    if len(validators) == 0:\n"
            "        return False\n"
            "    limit = validators[0]\n"
            "    return compare_length(value_length, limit)"),
        "rationale": "correct, restructured (early-return on empty validator "
                     "list). build_char_validators' posts give len==0 iff "
                     "max_length is None and Result()[0]==max_length otherwise, "
                     "so both clean posts hold. Must verify (else SPEC-TOO-STRONG).",
    },

    # ========================= ADMISSIBILITY =================================
    # The precondition must accept a normal, F2P-shaped input (else
    # PRECOND-TOO-STRONG). A positive-control caller exercises build_char_
    # validators on a concrete in-domain max_length and asserts the resulting
    # fact, then proceeds with the gold clean logic. If the Requires could not
    # be established for a legitimate input, the call site would fail to verify.

    {
        "id": "admiss-clean-selfexercise",
        "kind": "admissibility",
        "expect": "verify",
        "module": _clean(
            "    probe = build_char_validators(7)\n"
            "    Assert(len(probe) == 1)\n"
            "    Assert(probe[0] == 7)\n"
            "    validators = build_char_validators(max_length)\n"
            "    flagged = False\n"
            "    if len(validators) > 0:\n"
            "        limit = validators[0]\n"
            "        flagged = compare_length(value_length, limit)\n"
            "    return flagged"),
        "rationale": "admissibility witness: build_char_validators is callable "
                     "on a representative concrete max_length (7) and its post "
                     "yields len==1, Result()[0]==7 — the precondition admits a "
                     "normal F2P-shaped input. Must verify (else PRECOND-TOO-STRONG).",
    },

    # ===================== UNIQUENESS / completeness =========================
    # same-spec WRONG impls that MUST be rejected; if any verifies => SPEC-TOO-WEAK.
    # No @Pure answer-key oracle exists (posts are grounded in the args), so
    # there is no ungrounded-oracle echo to build; the attacks are partial-domain
    # and control-flow-effect instead.

    # ---- marquee control-flow-effect: the pre-patch bug shape (the F2P) ----
    {
        "id": "weak-clean-drop-none-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the guard: runs the length comparison against max_length
        # unconditionally — exactly the pre-patch CharField.__init__ that the
        # gold patch fixes. When max_length is None, compare_length's
        # Exsures(LimitComparisonError, limit is None) fires, but clean_charfield
        # has NO Exsures, so the call site cannot prove non-raising => rejected.
        "module": _clean(
            "    return compare_length(value_length, max_length)"),
        "refinement": "the faithful real patch is the PRE-PATCH code: drop the "
                      "`if self.max_length is not None` guard so a "
                      "MaxLengthValidator(None) runs in run_validators(); on the "
                      "F2P (Value(...)._resolve_output_field().clean(value, "
                      "model_instance=None) with max_length None) "
                      "len(value) > None raises TypeError, which run_validators "
                      "does NOT swallow (it catches only ValidationError) — the "
                      "F2P test fails. So this would NOT resolve.",
        "rationale": "rejected by clean_charfield having NO Exsures while "
                     "compare_length raises on limit is None (the dropped guard "
                     "lets None reach the comparison). This is the exact change "
                     "under test.",
    },

    # ---- partial-domain on clean: correct on most inputs, wrong above limit ----
    {
        "id": "weak-clean-always-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Always reports 'not flagged'. Correct when max_length is None and when
        # the value fits, but WRONG on the sub-domain value_length > max_length.
        "module": _clean(
            "    return False"),
        "refinement": "a real patch that makes clean always report 'fits' would "
                      "stop CharField from flagging over-long values (the "
                      "MaxLengthValidator would never raise ValidationError on "
                      "value_length > max_length), breaking max-length "
                      "enforcement P2P tests — it would NOT resolve.",
        "rationale": "rejected by Ensures(max_length is not None ==> "
                     "Result() == (value_length > max_length)) on the sub-domain "
                     "value_length > max_length (partial-domain).",
    },

    # ---- partial-domain on build: wrong assembled limit when present ----
    {
        "id": "weak-build-limit-plus-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct emptiness for None, but assembles a validator with the WRONG
        # limit (max_length + 1) when a maximum is supplied.
        "module": _build(
            "    validators = []  # type: List[Optional[int]]\n"
            "    if max_length is not None:\n"
            "        validators.append(max_length + 1)\n"
            "    return validators"),
        "refinement": "a real patch that builds MaxLengthValidator(max_length+1) "
                      "would let strings of exactly max_length+0..1 through, "
                      "off-by-one breaking length enforcement — P2P max-length "
                      "tests fail; it would NOT resolve.",
        "rationale": "rejected by Ensures(max_length is not None ==> "
                     "Result()[0] == max_length): the assembled limit must equal "
                     "the supplied maximum (partial-domain on the limit value).",
    },

    # ---- partial-domain on build: never assembles the validator ----
    {
        "id": "weak-build-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Always returns the empty slot — correct for max_length is None, but
        # drops the length validator entirely when a maximum IS supplied.
        "module": _build(
            "    validators = []  # type: List[Optional[int]]\n"
            "    return validators"),
        "refinement": "a real patch that never appends the MaxLengthValidator "
                      "would silently disable length checking for fields that "
                      "declare max_length — the field would accept arbitrarily "
                      "long values, breaking max-length validation P2P tests; "
                      "it would NOT resolve.",
        "rationale": "rejected by Ensures(max_length is not None ==> "
                     "len(Result()) == 1 and Result()[0] == max_length): a "
                     "declared maximum MUST assemble exactly one validator "
                     "(partial-domain: only the None sub-domain is correct).",
    },

    # ---- partial-domain on compare: off-by-one (>= instead of >) ----
    {
        "id": "weak-compare-ge",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one: flags at equality too. Diverges from gold only on the
        # value_length == limit boundary.
        "module": _compare(
            "    if limit is None:\n"
            "        raise LimitComparisonError()\n"
            "    return value_length >= limit"),
        "refinement": "MaxLengthValidator.compare is `a > b` (validators.py:390): "
                      "a real `>=` patch would reject strings of length exactly "
                      "max_length, which the field must ACCEPT — boundary P2P "
                      "max-length tests fail; it would NOT resolve.",
        "rationale": "rejected by Ensures(Result() == (value_length > limit)) on "
                     "the boundary value_length == limit (partial-domain off-by-one).",
    },

    # ---- uniqueness on compare: constant True ignores the comparison ----
    {
        "id": "weak-compare-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Echoes a constant 'exceeds' verdict without doing the numeric work.
        "module": _compare(
            "    if limit is None:\n"
            "        raise LimitComparisonError()\n"
            "    return True"),
        "refinement": "a real patch where the comparison always reports 'exceeds' "
                      "would make MaxLengthValidator reject every value (even "
                      "in-bounds), breaking normal cleaning — F2P/P2P fail; it "
                      "would NOT resolve.",
        "rationale": "rejected by Ensures(Result() == (value_length > limit)) "
                     "whenever value_length <= limit (the constant disagrees with "
                     "the grounded comparison).",
    },
]


# No @ContractOnly axioms (meta.axioms == []); the three A-references are
# validated out of band by axiom_check.py / G-AX, not consumed by the proof.
AXIOM_TESTS = []
