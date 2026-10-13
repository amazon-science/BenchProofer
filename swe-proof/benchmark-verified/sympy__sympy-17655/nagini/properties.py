# properties.py — PBT manifest for sympy__sympy-17655. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# parses SPEC_TESTS / AXIOM_TESTS, builds each `module` by region-surgery on the
# frozen model.py (editing ONLY inside an impl region, so same_spec is preserved
# by construction), runs Nagini verify + same_spec on the spec lane, and stamps
# RESULT.
#
# Defended surface (read from model.py):
#   mul_right(point, factor) and mul_left(factor, point) BOTH take `point` as a
#   READ-ONLY input carrying only fractional permission `Acc(list_pred(point),
#   1/2)`.  Each Ensures:
#     (P1) Acc(list_pred(point), 1/2)            -- point stays read-only & intact
#     (P2) Acc(list_pred(Result()))              -- a fresh fully-owned result
#     (P3) len(Result()) == len(point)           -- dimension preserved
#     (P4) ToSeq(Result()) == scaled(ToSeq(point), factor)  -- LOAD-BEARING:
#          every result coordinate is point[i] * factor, in order.
#   `scaled` is a @Pure front-recursive fold FULLY GROUNDED in the args
#   (ToSeq(point), factor) -- it is not an opaque answer-key, so there is no
#   wrong "echo" a cheap impl could materialize without doing the per-coordinate
#   work (a PSeq[int] cannot be returned as the List[int] result without the
#   per-coordinate multiply).  Hence no ungrounded-oracle-echo case; instead an
#   honest structurally-different positive control (see `assessment`).
#
# Attacks: (a) frame-mutation -- write the read-only `point` to build the answer
# in place, must be REJECTED for insufficient permission; (b) partial-domain --
# correct on most coordinates but wrong on the first coordinate / by an off-by
# factor, must be rejected by P4; (c) dimension drop -- violates P3.  Each reject
# rival carries the refinement argument that its faithful real patch would NOT
# resolve the F2P (`5 * Point(1,1) == Point(5,5)` / `5 * Point(1,1,1) ==
# Point3D(5,5,5)` in test_point / test_point3D).

from pathlib import Path

INSTANCE = "sympy__sympy-17655"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors (ALL inside an impl region, so spec regions are untouched).
# ---------------------------------------------------------------------------

# mul_right impl body (lines between # impl-start / # impl-end of mul_right).
_RIGHT_IMPL = """    result = []  # type: List[int]
    i = len(point)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(point), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(point))
        Invariant(len(result) == len(point) - i)
        Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = point[i - 1]
        Assert(ToSeq(point).drop(i - 1)[0] == c)
        Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
        result = [c * factor] + result
        i = i - 1
    Assert(ToSeq(point).drop(0) == ToSeq(point))
    return result"""

# mul_left impl body.
_LEFT_IMPL = "    return mul_right(point, factor)"


# ===========================================================================
# 1. POSITIVE CONTROL (soundness) — structurally-different but CORRECT impl.
#    A local-variable reshape of the gold backward loop: the per-coordinate
#    product is bound to its own local `prod` before the prepend, the guard is
#    written `not (i <= 0)` instead of `i > 0`, and `i = i - 1` becomes
#    `i -= 1`.  All gold framing asserts + invariants are KEPT verbatim (per
#    pilot bug #2 / #3 -- changing the loop DIRECTION to a forward append would
#    need an f(a+b)==f(a)+f(b) lemma against the front-recursive `scaled`, so we
#    keep the backward shape and only reshape locals/guard).  Must verify; if a
#    faithful correct impl cannot verify => SPEC-TOO-STRONG.
# ===========================================================================
_POS_RIGHT = """    result = []  # type: List[int]
    i = len(point)
    while not (i <= 0):
        # invariants-start
        Invariant(Acc(list_pred(point), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(point))
        Invariant(len(result) == len(point) - i)
        Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = point[i - 1]
        prod = c * factor
        Assert(ToSeq(point).drop(i - 1)[0] == c)
        Assert(ToSeq(point).drop(i - 1).drop(1) == ToSeq(point).drop(i))
        result = [prod] + result
        i -= 1
    Assert(ToSeq(point).drop(0) == ToSeq(point))
    return result"""

POS_CONTROL = _swap(_BASE, _RIGHT_IMPL, _POS_RIGHT)


# ===========================================================================
# 2. ADMISSIBILITY — the precondition must accept a normal F2P-shaped input.
#    Keep the gold impl but add a benign in-domain assertion (`len(point) >= 0`,
#    always true under Acc(list_pred(point),1/2)) at the top of mul_right's impl
#    region: it can only verify if the Requires is establishable for the input
#    shape the F2P uses.  Must verify; if it cannot => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS_RIGHT = _RIGHT_IMPL.replace(
    "    result = []  # type: List[int]",
    "    Assert(len(point) >= 0)\n    result = []  # type: List[int]",
    1,
)
ADMISS = _swap(_BASE, _RIGHT_IMPL, _ADMISS_RIGHT)


# ===========================================================================
# 3. FRAME-MUTATION (mul_right) — MANDATORY (read-only Acc(point,1/2) input).
#    Build the answer by WRITING the read-only `point` in place, then returning
#    it.  The contract grants only Acc(list_pred(point), 1/2); a write needs
#    full permission, so this must be REJECTED for insufficient permission.
#    The gold P4/invariants are kept verbatim so the rejection is attributable
#    to the write, not a proof gap.
#    Refinement: a faithful real patch that mutated `self.args` (a SymPy Tuple,
#    immutable) to scale in place would raise / not produce a fresh scaled Point,
#    so `5 * Point(1,1) == Point(5,5)` would NOT hold => F2P would NOT resolve.
# ===========================================================================
_FRAME_RIGHT = """    i = len(point)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(point)))
        Invariant(0 <= i and i <= len(point))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        point[i - 1] = point[i - 1] * factor
        i = i - 1
    return point"""

FRAME_MUT_RIGHT = _swap(_BASE, _RIGHT_IMPL, _FRAME_RIGHT)


# ===========================================================================
# 4. FRAME-MUTATION (mul_left) — the read-only input on the DELEGATING site.
#    mul_left writes `point` before delegating; only Acc(point,1/2) is held,
#    so the write must be REJECTED for insufficient permission.
#    Refinement: mutating the operand of `factor * point` instead of returning a
#    fresh scaled point breaks `5 * p4 == Point(5,5)` (the original p4 would be
#    clobbered / a Tuple write would raise) => F2P would NOT resolve.
# ===========================================================================
_FRAME_LEFT = """    point[0] = point[0] * factor
    return mul_right(point, factor)"""

FRAME_MUT_LEFT = _swap(_BASE, _LEFT_IMPL, _FRAME_LEFT)


# ===========================================================================
# 5. PARTIAL-DOMAIN (first coordinate unscaled) — correct on every coordinate
#    EXCEPT index 0, which is copied unscaled.  Violates P4
#    (ToSeq(Result()) == scaled(ToSeq(point), factor)) on the first coordinate.
#    Refinement: `5 * Point(1,1)` would give `Point(1, 5)` not `Point(5, 5)`
#    (first coord 1*1 unscaled) => test_point's `5 * p4 == Point(5,5)` FAILS,
#    F2P would NOT resolve.  Built with the gold invariants kept so the only
#    discrepancy is the first-element value.
# ===========================================================================
_PARTIAL_FIRST = """    result = []  # type: List[int]
    i = len(point)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(point), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(point))
        Invariant(len(result) == len(point) - i)
        Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = point[i - 1]
        if i - 1 == 0:
            result = [c] + result
        else:
            result = [c * factor] + result
        i = i - 1
    return result"""

PARTIAL_FIRST = _swap(_BASE, _RIGHT_IMPL, _PARTIAL_FIRST)


# ===========================================================================
# 6. PARTIAL-DOMAIN (off-by-factor on one coordinate) — scales by `factor + 1`
#    for the LAST coordinate (i == len(point)), correct elsewhere.  Violates P4
#    on the last coordinate.
#    Refinement: `5 * Point(1,1)` would give `Point(5, 6)` (last coord scaled by
#    6) not `Point(5, 5)` => F2P would NOT resolve.
# ===========================================================================
_PARTIAL_LAST = """    result = []  # type: List[int]
    i = len(point)
    n = len(point)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(point), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(n == len(point))
        Invariant(0 <= i and i <= len(point))
        Invariant(len(result) == len(point) - i)
        Invariant(ToSeq(result) == scaled(ToSeq(point).drop(i), factor))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = point[i - 1]
        if i == n:
            result = [c * (factor + 1)] + result
        else:
            result = [c * factor] + result
        i = i - 1
    return result"""

PARTIAL_LAST = _swap(_BASE, _RIGHT_IMPL, _PARTIAL_LAST)


# ===========================================================================
# 7. DIMENSION-DROP (partial-domain on length) — drops the first coordinate of
#    the result, so len(Result()) == len(point) - 1.  Violates P3
#    (len(Result()) == len(point)).
#    Refinement: `5 * Point(1,1)` would give a 1-D point `Point(5)` (a different
#    dimension) which is != Point(5,5) => F2P would NOT resolve.
# ===========================================================================
_DIM_DROP = """    result = []  # type: List[int]
    i = len(point)
    while i > 1:
        c = point[i - 1]
        result = [c * factor] + result
        i = i - 1
    return result"""

DIM_DROP = _swap(_BASE, _RIGHT_IMPL, _DIM_DROP)


# ---------------------------------------------------------------------------
SPEC_TESTS = [
    {
        "id": "pos-control-localreshape",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CONTROL,
        "rationale": "structurally-different CORRECT mul_right (local `prod`, "
        "guard `not (i<=0)`, `i -= 1`); keeps the backward shape and all gold "
        "invariants/asserts so the front-recursive `scaled` proof still goes "
        "through. Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fzp-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "gold impl + a benign in-domain Assert(len(point) >= 0); "
        "verifies only if Requires Acc(list_pred(point),1/2) is establishable "
        "for the normal F2P input shape. Else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mut-right",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MUT_RIGHT,
        "refinement": "writes the read-only `point` in place (point[i-1] = "
        "point[i-1]*factor) and returns it. The real Point.__mul__ cannot mutate "
        "self.args (an immutable SymPy Tuple) to scale in place; a faithful "
        "in-place patch would raise / not yield a fresh scaled Point, so "
        "`5 * Point(1,1) == Point(5,5)` would FAIL => F2P (test_point) would NOT "
        "resolve.",
        "rationale": "MUST fail for INSUFFICIENT PERMISSION: only "
        "Acc(list_pred(point),1/2) is held but the body writes point. Rejection "
        "comes from the permission system (the read-only fractional input), not "
        "the postcondition.",
    },
    {
        "id": "frame-mut-left",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MUT_LEFT,
        "refinement": "mul_left writes point[0] before delegating. The real "
        "__rmul__ delegates to __mul__ which builds a FRESH Point; mutating the "
        "operand of `factor * point` would clobber the original / raise on the "
        "immutable Tuple, so `5 * p4 == Point(5,5)` would FAIL => F2P would NOT "
        "resolve.",
        "rationale": "MUST fail for INSUFFICIENT PERMISSION on the delegating "
        "site: only Acc(list_pred(point),1/2) is held. Rejection from the "
        "permission system.",
    },
    {
        "id": "partial-first-coord-unscaled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_FIRST,
        "refinement": "leaves point[0] UNSCALED (result[0] == point[0], not "
        "point[0]*factor); correct on every other coordinate. `5 * Point(1,1)` "
        "would be `Point(1, 5)` != `Point(5, 5)` => test_point's `5 * p4 == "
        "Point(5,5)` FAILS, F2P would NOT resolve.",
        "rationale": "MUST be rejected by postcondition P4 "
        "ToSeq(Result()) == scaled(ToSeq(point), factor) on the first "
        "coordinate. A spec that admitted this would be SPEC-TOO-WEAK "
        "(partial-domain: first element).",
    },
    {
        "id": "partial-last-coord-offbyfactor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_LAST,
        "refinement": "scales the LAST coordinate by factor+1 instead of factor; "
        "correct elsewhere. `5 * Point(1,1)` would be `Point(5, 6)` != "
        "`Point(5, 5)` => F2P would NOT resolve.",
        "rationale": "MUST be rejected by postcondition P4 on the last "
        "coordinate. Else SPEC-TOO-WEAK (partial-domain: off-by-factor on a "
        "boundary element).",
    },
    {
        "id": "dimension-drop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DIM_DROP,
        "refinement": "drops the first coordinate: len(result) == len(point)-1. "
        "`5 * Point(1,1)` would be a 1-D `Point(5)` != `Point(5, 5)` => F2P "
        "would NOT resolve (and a real impl that lost a coordinate breaks the "
        "dimension-preservation the test asserts).",
        "rationale": "MUST be rejected by postcondition P3 "
        "len(Result()) == len(point). Else SPEC-TOO-WEAK (partial-domain: "
        "length class).",
    },
]


# ===========================================================================
# AXIOM LANE — empty.  meta.json axioms == [] and the axioms region of model.py
# is empty: the scaling is modeled DEEPLY as integer multiplication (the @Pure
# `scaled` / the verified `mul_right` loop), there is no @ContractOnly axiom the
# proof consumes.  The single A-reference deep model `scaled` is validated
# == the real Point.__mul__/__rmul__ by axiom_check.py (G-AX), which the
# orchestrator runs separately; there is no caller-reachable callee-input to
# containment-check (the model performs the multiplication itself, it does not
# call out to an axiomatized callee).
# ===========================================================================
AXIOM_TESTS = []
