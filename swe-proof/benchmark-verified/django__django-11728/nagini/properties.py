"""PBT falsification battery for django__django-11728.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes. Spec cases are full model.py variants that
share the FROZEN spec (markers.same_spec) and differ ONLY inside the
# impl-start/# impl-end regions (the invariants region nests inside impl and is
elided by the spec view, so editing it is still same_spec). Each is checked by
the Nagini verifier on the host.

Defended surface (per function `*_pattern_end`):
  * `region: List[int]` is READ-ONLY: `Requires/Ensures(Acc(list_pred(region), 1/2))`.
  * Precondition: `close_off(ToSeq(region), 1, prev0) < len(region)` (a matching
    close exists in the region).
  * LOAD-BEARING postcondition: `Result() == close_off(ToSeq(region), 1, prev0) + 1`
    pins the output EXACTLY to a GROUNDED @Pure oracle (a front-recursive fold of
    the input, fully unfolded -- not an opaque answer key), plus the range bound
    `1 <= Result() <= len(region)`.

The instance fix (gold patch) is *where* the depth-zero condition is detected:
the pre-patch top-of-loop placement records the span ONE iteration late and
drops a group whose matching `)` is the final character (the F2P trailing-group
bug). The exact-value postcondition is what makes that bug fail to verify.

There are NO @ContractOnly axioms (the axioms region is empty); close_off/step_bal
are A-reference DEEP models validated by axiom_check.py / G-AX, not consumed
axioms. Hence AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "django__django-11728"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The verbatim impl bodies (one per function). Both functions are textually
# identical inside their impl regions, so each named-impl literal occurs TWICE
# in _BASE; _swap requires uniqueness. We therefore anchor edits on the WHOLE
# impl body of ONE function (the named site for most attacks; a couple target
# the unnamed site for differential coverage). The two impl bodies differ only
# in their surrounding markers, but the bodies themselves are byte-identical, so
# to keep _swap unique we splice using a per-function unique surrounding context.
# ---------------------------------------------------------------------------

# Unique left/right context for the NAMED function's impl region.
_NAMED_CTX_HEAD = (
    "def named_group_pattern_end(region: List[int], prev0: int) -> int:")
# Unique left/right context for the UNNAMED function's impl region.
_UNNAMED_CTX_HEAD = (
    "def unnamed_group_pattern_end(region: List[int], prev0: int) -> int:")

# The shared gold impl body (between # impl-start and # impl-end), verbatim.
_GOLD_IMPL = """    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res"""


_GOLD_DRIFT_ANCHORS = (
    "    bal = 1\n    prev = prev0\n    i = 0\n    res = -1\n",
    "    while i < len(region) and bal != 0:\n",
    "        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))\n",
    "        if bal == 0:\n            res = i\n    return res\n",
)


def _check_drift(old):
    for anchor in _GOLD_DRIFT_ANCHORS:
        if anchor not in old:
            raise AssertionError(f"impl body drift: missing {anchor!r}")


def _replace_named_impl(new_body):
    """Replace ONLY the named function's impl body, keeping the unnamed one
    (the gold) intact. Anchors on the function head to disambiguate the two
    byte-identical bodies."""
    head_idx = _BASE.index(_NAMED_CTX_HEAD)
    impl_start = _BASE.index("    # impl-start\n", head_idx)
    impl_end = _BASE.index("    # impl-end", impl_start)
    body_start = impl_start + len("    # impl-start\n")
    old = _BASE[body_start:impl_end]
    _check_drift(old)
    return _BASE[:body_start] + new_body + "\n" + _BASE[impl_end:]


def _replace_unnamed_impl(new_body):
    """Replace ONLY the unnamed function's impl body, keeping the named one
    (the gold) intact."""
    head_idx = _BASE.index(_UNNAMED_CTX_HEAD)
    impl_start = _BASE.index("    # impl-start\n", head_idx)
    impl_end = _BASE.index("    # impl-end", impl_start)
    body_start = impl_start + len("    # impl-start\n")
    old = _BASE[body_start:impl_end]
    _check_drift(old)
    return _BASE[:body_start] + new_body + "\n" + _BASE[impl_end:]


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG)
# ===========================================================================

# pos-1: structurally-different correct impl. Loop reshaped to use an explicit
# `break` on depth-zero instead of the `bal != 0` loop guard, and the result is
# recorded directly as i (== idx+1). Keeps EVERY gold invariant and framing
# Assert verbatim (directive: do not drop proof obligations). The loop guard is
# relaxed to `i < len(region)` and a `break` exits when bal hits 0; the
# invariants are unchanged so the proof still goes through.
_POS1_BODY = """    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region):
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard `i < len(region)` bounds the scan -- `i` rises
        # by exactly 1 on every pass that reaches the loop head again (the
        # `break` only exits sooner) and `len(region)` is fixed, so
        # `len(region) - i + 1` strictly decreases and is >= 2 at every head.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        if bal == 0:
            break
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res"""

# pos-2: honest cheapest-impl positive control. The oracle is GROUNDED (a @Pure
# fold of the args, fully unfolded -- not an opaque answer key), so the directly
# materialized value IS a correct implementation, not a cheat. This is the
# directive-2 "honest cheapest-impl positive control": there is no WRONG echo
# because the oracle is a function of the input, so returning it must verify.
# No loop, hence no invariants/framing asserts needed (maximally different shape).
_POS2_BODY = """    answer = close_off(ToSeq(region), 1, prev0) + 1
    return answer"""


# ===========================================================================
# UNIQUENESS / REJECT rivals — must NOT verify (else SPEC-TOO-WEAK)
# ===========================================================================

# rej-1 (FRAME-MUTATION, MANDATORY): the rival writes to the read-only `region`
# input before scanning. With only Acc(list_pred(region), 1/2) the write to
# region[0] is illegal: Nagini rejects for INSUFFICIENT PERMISSION. Every gold
# invariant/assert is kept verbatim so the rejection is attributable ONLY to the
# write, not to a proof gap. Refinement: a faithful real patch that mutated the
# scanned pattern string (e.g. region[0] = ord('x')) would corrupt the very text
# replace_named_groups must later slice and substitute, so the simplify_regex
# F2P output would be wrong -- it would NOT resolve.
_REJ_FRAME_BODY = """    region[0] = region[0]
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res"""

# rej-2 (PARTIAL-DOMAIN = the pre-patch bug itself): record the depth-zero span
# at the TOP of the loop instead of the bottom -- i.e. the original buggy
# placement that defers recording to the NEXT iteration. This is correct on
# every input where a character FOLLOWS the matching close (close_off <
# len(region)-1), but drops the group when the matching `)` is the FINAL
# character (close_off == len(region)-1): res stays -1, violating
# Result() == close_off+1 (which is >= 1). Refinement: this is the literal
# pre-patch code (model_prepatch.py); the F2P trailing-group patterns
# (r'^(?P<a>\\w+)/b/(?P<c>\\w+)') are exactly what it fails -- it would NOT
# resolve. Invariants are weakened to the pre-patch shape so the failure is a
# postcondition (value) failure, not a translation/proof artifact.
_REJ_PREPATCH_BODY = """    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and res == -1:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        # Termination: `i` rises by exactly 1 on every pass that reaches the
        # loop head again (the early `break` only exits sooner) and
        # `len(region)` is fixed, so `len(region) - i + 1` strictly decreases
        # and is >= 2 at every loop head, where `i < len(region)` holds.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        if bal == 0:
            res = i
            break
        val = region[i]
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
    return res"""

# rej-3 (OFF-BY-ONE / value double-mask): record res = i-1 (the matching-close
# offset itself) rather than i (one past it). This returns close_off instead of
# close_off+1 -- the exact pre-patch span the gold corrected (end+idx vs
# end+idx+1). The postcondition Result() == close_off+1 must reject it on EVERY
# input. Refinement: this is the off-by-one the gold patch fixes (pattern[start:
# end+idx] vs end+idx+1); it slices one character short, dropping the closing
# `)` from the captured group -> simplify_regex output wrong -> does NOT resolve.
_REJ_OFFBYONE_BODY = """    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0)))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i - 1
    return res"""

# rej-4 (UNNAMED-site differential off-by-one): the same off-by-one applied to
# the UNNAMED function (rej-3 hits the named one), giving an independent
# differential witness that the second modeled function's postcondition is also
# tight. Refinement: same as rej-3 but for replace_unnamed_groups
# (start+1+idx vs start+2+idx); drops the trailing `)` of the unnamed group ->
# does NOT resolve.
_REJ_OFFBYONE_UNNAMED_BODY = _REJ_OFFBYONE_BODY


# ===========================================================================
# ADMISSIBILITY — must VERIFY (else PRECOND-TOO-STRONG)
# ===========================================================================

# adm-1: the precondition close_off(...) < len(region) is NON-VACUOUS and admits
# the F2P shape (a non-empty region). It implies len(region) >= 1: if region were
# empty, close_off returns 0 and 0 < 0 is false. Asserting len(region) >= 1
# inside the impl proves the precondition actually constrains a real input rather
# than being unsatisfiable/contradictory (which would make the function verify
# vacuously). Keeps the gold impl otherwise so the postcondition is still proven.
_ADM_BODY = """    Assert(len(region) >= 1)
    bal = 1
    prev = prev0
    i = 0
    res = -1
    while i < len(region) and bal != 0:
        # invariants-start
        Invariant(Acc(list_pred(region), 1 / 2))
        Invariant(0 <= i and i <= len(region))
        Invariant(bal >= 0)
        Invariant(close_off(ToSeq(region), 1, prev0) < len(region))
        Invariant(Implies(bal >= 1, res == -1))
        Invariant(Implies(bal >= 1, i <= close_off(ToSeq(region), 1, prev0)))
        Invariant(Implies(bal >= 1,
                          close_off(ToSeq(region), 1, prev0)
                          == i + close_off(ToSeq(region).drop(i), bal, prev)))
        Invariant(Implies(bal == 0, res == close_off(ToSeq(region), 1, prev0) + 1))
        # Termination: the guard's FIRST conjunct `i < len(region)` alone bounds
        # the scan -- `i` rises by exactly 1 per pass and `len(region)` is fixed
        # (region is only read), so `len(region) - i + 1` strictly decreases and
        # is >= 2 at every loop head. The second conjunct `bal != 0` can only
        # make the loop exit sooner, so it cannot invalidate the bound.
        Invariant(MustTerminate(len(region) - i + 1))
        # invariants-end
        val = region[i]
        Assert(ToSeq(region).drop(i)[0] == val)
        Assert(ToSeq(region).drop(i).drop(1) == ToSeq(region).drop(i + 1))
        nb = step_bal(val, prev, bal)
        prev = val
        bal = nb
        i = i + 1
        if bal == 0:
            res = i
    return res"""


SPEC_TESTS = [
    {
        "id": "pos-break-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _replace_named_impl(_POS1_BODY),
        "rationale": "structurally-different CORRECT impl (loop guard relaxed to "
                     "i<len(region) with an explicit break on bal==0) that keeps "
                     "every gold invariant + framing Assert; must verify else "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-grounded-oracle",
        "kind": "soundness",
        "expect": "verify",
        "module": _replace_named_impl(_POS2_BODY),
        "rationale": "honest cheapest-impl: the oracle close_off is GROUNDED in "
                     "the args (a fully-unfolded @Pure fold, not an opaque answer "
                     "key), so returning close_off+1 directly IS correct and must "
                     "verify. Doubles as the no-wrong-echo positive control "
                     "(directive 2).",
    },
    {
        "id": "adm-nonvacuous-precond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _replace_named_impl(_ADM_BODY),
        "rationale": "Assert(len(region) >= 1) inside impl proves the precondition "
                     "close_off(...)<len(region) is non-vacuous and admits an "
                     "F2P-shaped non-empty region (else PRECOND-TOO-STRONG / "
                     "the spec would verify vacuously).",
    },
    {
        "id": "rej-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_named_impl(_REJ_FRAME_BODY),
        "refinement": "a faithful real patch that wrote to the scanned pattern "
                      "(region[0]=...) would corrupt the text replace_named_groups "
                      "later slices/substitutes, producing the wrong simplify_regex "
                      "output -> would NOT resolve the F2P.",
        "rationale": "MANDATORY frame-mutation probe. region is read-only "
                     "(Acc(list_pred(region),1/2)); the write region[0]=... must be "
                     "rejected for INSUFFICIENT PERMISSION (permission system), not "
                     "a proof gap -- all gold invariants kept verbatim.",
    },
    {
        "id": "rej-prepatch-top-check",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_named_impl(_REJ_PREPATCH_BODY),
        "refinement": "this is the literal PRE-PATCH placement (model_prepatch.py): "
                      "depth-zero recorded at the loop TOP, deferred a step. It "
                      "drops a group whose matching ) is the final char, exactly "
                      "the F2P trailing-group patterns r'^(?P<a>\\w+)/b/(?P<c>\\w+)' "
                      "-> would NOT resolve.",
        "rationale": "PARTIAL-DOMAIN: correct when a char follows the close, but on "
                     "close_off==len(region)-1 res stays -1, violating "
                     "Result()==close_off+1 (>=1). Rejection from the postcondition "
                     "value clause.",
    },
    {
        "id": "rej-offbyone-named",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_named_impl(_REJ_OFFBYONE_BODY),
        "refinement": "records res=i-1 (close_off, the close offset) instead of i "
                      "(close_off+1). This is the gold's off-by-one (pattern[start:"
                      "end+idx] vs end+idx+1): it slices one char short, dropping "
                      "the closing ) from the captured group -> wrong output -> "
                      "would NOT resolve.",
        "rationale": "value double-mask / off-by-one. Postcondition "
                     "Result()==close_off+1 rejects close_off on EVERY input "
                     "(invariant lower-bound adjusted to the wrong value so the "
                     "failure is the final postcondition, a value defect).",
    },
    {
        "id": "rej-offbyone-unnamed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _replace_unnamed_impl(_REJ_OFFBYONE_UNNAMED_BODY),
        "refinement": "same off-by-one as rej-offbyone-named but on the UNNAMED "
                      "function (start+1+idx vs start+2+idx); drops the trailing ) "
                      "of the unnamed group -> would NOT resolve. Independent "
                      "differential witness that the SECOND function's postcondition "
                      "is also tight.",
        "rationale": "uniqueness on the second modeled function (the bundle models "
                     "both sites independently); same postcondition value clause "
                     "drives the rejection.",
    },
]

# No @ContractOnly axioms consumed (axioms region empty); close_off/step_bal are
# A-reference DEEP models validated out-of-band by axiom_check.py (G-AX), not
# axioms the proof consumes. Hence no axiom soundness/containment lane here.
AXIOM_TESTS = []
