# properties.py — PBT falsification battery for pydata__xarray-4075. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` is edited; the spec view — docstring,
# imports, axioms/pure/pre-/post-conditions regions, the signature — is never
# touched). Each spec case is checked by Nagini verify + markers.same_spec. Axiom
# cases probe the consumed @ContractOnly axiom `dot_reduce` and the two A-reference
# deep models `int_dot` / `bool_dot` against the REAL `xarray.core.computation.dot`
# in the instance Docker image (see AXIOM_TESTS at the bottom).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   sum_of_weights_value(mask: List[int], weights: List[int], weights_are_bool: bool)
#     -> int
#   Models the gold change to Weighted._sum_of_weights: it computes the weighted
#   reduction sum_i mask[i]*weights[i] (the array dot product of the boolean presence
#   mask `da.notnull()` and the `weights`) and the genuine numeric COUNT must come out
#   even when the weights are a boolean array — the GH4074 bug was that
#   xr.dot([True,True],[True,True]) -> True (==1), not 2. The gold inserts
#   `if self.weights.dtype == bool: ...astype(int)...` so the dot always runs numeric.
#
#   PRECONDITION (read-only inputs + element-domain):
#     (P1) Requires(Acc(list_pred(mask), 1/2))      # HALF permission => READ-ONLY
#     (P2) Requires(Acc(list_pred(weights), 1/2))   # HALF permission => READ-ONLY
#     (P3) Requires(len(mask) == len(weights)) and len(ToSeq(mask))==len(ToSeq(weights))
#     (P4) mask[i] in {0,1};  weights[i] >= 0;  weights_are_bool => weights[i] in {0,1}
#   POSTCONDITION (three framing clauses + one LOAD-BEARING):
#     (Q1) Ensures(Acc(list_pred(mask), 1/2))       # returns the read permission
#     (Q2) Ensures(Acc(list_pred(weights), 1/2))    # returns the read permission
#     (Q3) Ensures(len(ToSeq(mask)) == len(ToSeq(weights)))
#     (Q4) Ensures(Result() == int_dot(ToSeq(mask), ToSeq(weights)))  <-- LOAD-BEARING
#   Q4 pins the result to the GENUINE arithmetic count int_dot == sum_i mask[i]*w[i],
#   a @Pure front-recursive fold GROUNDED element-wise in the actual inputs — not an
#   opaque oracle and not a constant. There is no slack: any impl whose value differs
#   from int_dot on ANY in-domain input fails Q4. The only verifying way to obtain
#   int_dot through the consumed axiom is `dot_reduce(...., boolean_dot=False)`
#   (the numeric contraction), which refines to the gold `astype(int)` cast.
#
# FRAME-MUTATION lane is MANDATORY: BOTH `mask` and `weights` are read-only
#   (Acc(...,1/2)). A rival that WRITES either to satisfy Q4 vacuously must be
#   REJECTED for INSUFFICIENT PERMISSION. The real `_sum_of_weights` only READS the
#   mask (`da.notnull()`, a fresh array) and `self.weights` — it never mutates them
#   in place; the gold even ADDS a non-mutating `.astype(int)` (a copy). Two probes:
#   one writing `mask[0]`, one writing `weights[0]`. Byte-fuzzers never mutate the
#   input; this is the project's #1 weakness class.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q4 is pinned to
#   int_dot(ToSeq(mask), ToSeq(weights)) — a @Pure fold fully unfolded element-wise
#   over the two argument carriers, NOT a @ContractOnly answer-key and NOT an exact
#   marker. (The @ContractOnly axiom `dot_reduce` is about the UNCHANGED community
#   dot callee, keyed on the input `boolean_dot`; its numeric branch RETURNS int_dot,
#   it is not an oracle the impl could echo to fake the count.) The unique value that
#   satisfies Q4 IS the grounded count, so there is no wrong echo. Therefore the
#   honest control is the cheapest faithful impl that produces that count — and the
#   `pos-int-dot-direct` positive control (return int_dot directly) is exactly that
#   cheapest-impl control. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. `sum_of_weights_value` is a single straight-line
#   value computation — no raise path, no return fork, no side effect. The only
#   behavioural content is the returned int, which Q4 fully governs; there is no
#   raise/return/effect difference invisible to the value abstraction, so no
#   capability-token rival is needed. (Justified in 'assessment'.)
#
# PARTIAL-DOMAIN lane: the central attack here, because the bug IS a sub-domain
#   divergence. A rival can be correct on the NUMERIC-weights sub-domain yet wrong on
#   the BOOLEAN-weights sub-domain when the true count >= 2:
#     - weak-prepatch     : boolean_dot = weights_are_bool (model_prepatch.py). Correct
#                           on numeric weights (boolean_dot=False -> int_dot) but on a
#                           boolean weight array lets the dot saturate (bool_dot), so on
#                           the F2P mask=[1,1] weights=[1,1] it returns 1 != 2.
#     - weak-bool-dot     : boolean_dot = True always (forces the saturating branch);
#                           returns bool_dot on EVERY input -> wrong whenever count>=2.
#     - weak-zero         : returns the constant 0 — correct only on the all-absent /
#                           all-zero-weight sub-domain (cheap supporting partial-domain).
#
# AXIOM lane: meta.axioms has ONE consumed @ContractOnly axiom `dot_reduce` (the
#   UNCHANGED community array-dot callee xarray.core.computation.dot), keyed on
#   `boolean_dot`; meta.deep_model_references has TWO A-references int_dot / bool_dot.
#   The real callee is `xr.dot`, which lives ONLY in the instance image, so the axiom
#   probes run in Docker (apply_gold True — the contract describes the post-gold
#   numeric path; the gold patch only adds the dtype branch, the dot is unchanged).
#   axiom-soundness: run the real xr.dot and assert numeric contraction (bool mask .
#   int weights, incl. the astype(int) cast = the gold) == int_dot, and boolean
#   contraction (bool mask . bool weights) == bool_dot (saturating to 0/1) — both
#   branches of dot_reduce's Ensures, over the GH4074 boundary + heavy fuzz.
#   axiom-containment: the model only ever passes boolean_dot=False (the gold impl);
#   the reachable operands are a 0/1 mask and non-negative-int weights of equal
#   length — assert every such reachable input lies in dot_reduce's Requires domain
#   (len(mask)==len(weights)) and that the numeric real dot equals int_dot on it
#   (covering the boolean branch too is sound, not a defect).
from pathlib import Path

INSTANCE = "pydata__xarray-4075"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`). Every spec variant _swap()s ONLY this
# block, so the edit never touches the spec (docstring/imports/axioms/pure/pre-/
# post-conditions + the signature). same_spec is computed over the spec_view, which
# elides every impl region, so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    # Hand the dot a numeric operand (a boolean weight array is cast to int
    # first), so the reduction always runs in numeric arithmetic and counts.
    boolean_dot = False
    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
    return result"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ---------------------------------------------------------------------------

# pos-int-dot-direct: a structurally DIFFERENT but behaviourally CORRECT impl. Instead
# of routing through the `dot_reduce` axiom at boolean_dot=False, it computes the
# count DIRECTLY via the @Pure deep fold int_dot over the input carriers. Since Q4 is
# literally `Result() == int_dot(ToSeq(mask), ToSeq(weights))`, returning exactly that
# value satisfies the postcondition with no proof gap — int_dot is a total @Pure fold
# over the (length-matched) sequences, so no extra lemma is needed (directive 3: this
# is NOT a forward-append against a front-recursive fold; it is a direct evaluation of
# the same front-recursive fold the spec names). Reads only (no write), so the
# half-permissions suffice. If it FAILS => SPEC-TOO-STRONG (a faithful, structurally
# different correct impl that produces the pinned count is rejected).
_POS_INT_DOT = """\
    # Compute the genuine count directly via the grounded numeric fold.
    result = int_dot(ToSeq(mask), ToSeq(weights))
    return result"""

# pos-local-reshape: the gold impl with a pure LOCAL-VARIABLE reshape — the boolean
# `False` is bound to a differently-named local and the dot call is split across two
# statements, but it is still `dot_reduce(..., boolean_dot=False)`. Semantically
# identical to the gold; keeps the same single consumed-axiom obligation. Must verify
# (else SPEC-TOO-STRONG on a trivial source reshape).
_POS_RESHAPE = """\
    use_boolean_arithmetic = False
    ms = ToSeq(mask)
    ws = ToSeq(weights)
    result = dot_reduce(ms, ws, use_boolean_arithmetic)
    return result"""


# admiss-reads: an admissibility positive control. The precondition is the two
# half-permissions plus the element-domain Forall clauses. This control keeps the gold
# impl VERBATIM but FIRST asserts, under the half-permissions, that the reads a normal
# F2P-shaped input needs are admitted — the lengths are readable/equal and (when
# non-empty, e.g. the F2P mask=[1,1] weights=[1,1]) the first elements are readable. No
# write, so no extra permission demand. If the precondition could not admit a normal
# (mask, weights) pair, this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal length-matched (mask, weights) pair is in-domain;\n"
    "    # the half-permissions admit reading the lengths and the elements.\n"
    "    Assert(len(mask) == len(weights))\n"
    "    Assert(len(ToSeq(mask)) == len(ToSeq(weights)))\n"
    "    if len(mask) > 0:\n"
    "        Assert(mask[0] == 0 or mask[0] == 1)   # P4: 0/1 mask, read admitted\n"
    "        Assert(weights[0] >= 0)                # P4: non-negative weight\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVALS (MANDATORY — both `mask` and `weights` are Acc(...,1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-mask: keeps the gold body VERBATIM (so the rejection is attributable SOLELY
# to the added write, not to a value mismatch), then WRITES BACK into the read-only
# `mask`: mask[0] = mask[0]. A no-op store, but a STORE — it demands FULL write
# permission on `mask`, which the caller granted only at 1/2. The verifier must reject
# for insufficient permission. Guarded by len>0 so it is reachable on the F2P input.
_FRAME_MUT_MASK = (
    "    if len(mask) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) mask.\n"
    "        mask[0] = mask[0]\n"
    + _IMPL
)

# frame-mut-weights: the dual — writes back into the read-only `weights`. The gold
# `.astype(int)` is a non-mutating COPY; any in-place write to the weight carrier
# would diverge from the gold and is forbidden by the half-permission.
_FRAME_MUT_WEIGHTS = (
    "    if len(weights) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) weights.\n"
    "        weights[0] = weights[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-prepatch: the EXACT pre-patch behaviour (model_prepatch.py). It hands the dot
# the operand dtype unchanged, i.e. `boolean_dot = weights_are_bool`. On numeric
# weights (weights_are_bool=False) this is boolean_dot=False -> int_dot (correct on
# that sub-domain) but on a BOOLEAN weight array it lets the dot run boolean ->
# bool_dot, which SATURATES to 0/1. On the F2P mask=[1,1] weights=[1,1]
# (weights_are_bool=True) bool_dot==1 != int_dot==2. Rejected by Q4.
_WEAK_PREPATCH = """\
    boolean_dot = weights_are_bool
    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
    return result"""

# weak-bool-dot: forces the SATURATING branch on every input (boolean_dot=True).
# Returns bool_dot(mask, weights) (0/1) regardless of the true count -> wrong whenever
# the count is >= 2. Rejected by Q4 (bool_dot != int_dot on the F2P).
_WEAK_BOOL_DOT = """\
    boolean_dot = True
    result = dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot)
    return result"""

# weak-zero: returns the constant 0 (a cheap supporting PARTIAL-DOMAIN near-miss).
# Correct ONLY on the all-absent / all-zero-weight sub-domain (where int_dot==0);
# wrong on any input with a present positive weight (the F2P count is 2). Rejected by
# Q4. Bound to a typed local first (directive 1: no `# type:` on a bare return).
_WEAK_ZERO = """\
    result = 0  # type: int
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-int-dot-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_INT_DOT),
        "rationale": (
            "structurally-different but CORRECT impl: it computes the genuine count "
            "DIRECTLY via the @Pure grounded fold int_dot(ToSeq(mask),ToSeq(weights)), "
            "bypassing the dot_reduce axiom entirely. Q4 is literally "
            "`Result()==int_dot(ToSeq(mask),ToSeq(weights))`, so returning that value "
            "satisfies the postcondition with no proof gap (int_dot is a total @Pure "
            "front-recursive fold over length-matched sequences — directly evaluated, "
            "not a forward-append, so no lemma is needed). If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl producing the pinned count is "
            "rejected)."
        ),
    },
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_RESHAPE),
        "rationale": (
            "the gold impl with a pure LOCAL-VARIABLE reshape: the boolean False is "
            "bound to a differently-named local and ToSeq(mask)/ToSeq(weights) are "
            "hoisted to locals before the same `dot_reduce(.., boolean_dot=False)` "
            "call. Semantically identical to the gold, same single consumed-axiom "
            "obligation, no dropped lemma/assert (directive 2/3). If it FAILS => "
            "SPEC-TOO-STRONG on a trivial source reshape."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (two Acc(...,1/2) half-permissions + the 0/1-mask / "
            "non-negative-weight element domains) must admit a normal length-matched "
            "(mask, weights) pair — e.g. the F2P mask=[1,1] weights=[1,1]. The control "
            "keeps the gold impl verbatim and only ADDS reads/asserts (lengths equal; "
            "when non-empty, mask[0] in {0,1} and weights[0] >= 0), all admitted under "
            "the half-permissions; no write. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-mask",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_MASK),
        "refinement": (
            "the gold `_sum_of_weights` only READS the presence mask (`mask = "
            "da.notnull()` produces a fresh boolean array that is consumed by the dot) "
            "— it NEVER writes into it. A faithful real patch that mutated the mask in "
            "place would diverge from the gold (which is read-only over the mask) and "
            "would not be the gold patch; it would not faithfully resolve. The store "
            "here is a no-op only by coincidence; the point is the spec must forbid ANY "
            "write to the read-only mask."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `mask` is granted at "
            "Acc(list_pred(mask),1/2) (P1); the store mask[0]=mask[0] demands FULL "
            "write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold value body is kept verbatim so the "
            "rejection is attributable solely to the write. If it VERIFIES => the "
            "read-only frame on `mask` is hollow (frame-mutation, the #1 weakness "
            "class)."
        ),
    },
    {
        "id": "frame-mut-weights",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_WEIGHTS),
        "refinement": (
            "the gold patch's `self.weights.astype(int)` is a non-mutating COPY of the "
            "weight array; the gold never writes into `self.weights` in place. A "
            "faithful real patch that mutated the weight carrier would corrupt the "
            "Weighted object's shared weights for every subsequent reduction and would "
            "diverge from the gold — it would not faithfully resolve. The store here is "
            "a no-op only by coincidence; the spec must forbid ANY write to the "
            "read-only weights."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `weights` is granted at "
            "Acc(list_pred(weights),1/2) (P2); the store weights[0]=weights[0] demands "
            "FULL write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold value body is kept verbatim so the "
            "rejection is attributable solely to the write. If it VERIFIES => the "
            "read-only frame on `weights` is hollow (frame-mutation, the #1 weakness "
            "class)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): the original "
            "`_sum_of_weights` hands `self.weights` straight to the dot with NO "
            "astype(int) cast, so a boolean weight array makes the dot run boolean. Its "
            "faithful real patch is the UNCHANGED repo, which on a boolean weight array "
            "computes xr.dot(bool_mask, bool_weights) -> True (==1), not the count 2 — "
            "exactly the GH4074 bug. It fails the F2P "
            "test_weighted_sum_of_weights_bool (da=[1,2], weights=[True,True], expects "
            "sum_of_weights == 2) and test_weighted_mean_bool. Does NOT resolve — the "
            "precise change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q4 (Ensures(Result()==int_dot(ToSeq(mask),ToSeq(weights)))): "
            "with weights_are_bool=True the rival passes boolean_dot=True, so by "
            "dot_reduce's Ensures the result is bool_dot(mask,weights), which saturates "
            "to 0/1; on the F2P mask=[1,1] weights=[1,1] bool_dot==1 but int_dot==2, so "
            "Q4 is violated. PARTIAL-DOMAIN: correct on numeric weights, wrong on the "
            "boolean-weights sub-domain when the true count >= 2. If it VERIFIES => "
            "SPEC-TOO-WEAK (the dtype-collapse is not forbidden)."
        ),
    },
    {
        "id": "weak-bool-dot",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_BOOL_DOT),
        "refinement": (
            "forcing boolean_dot=True always is what a real patch that cast the operand "
            "the WRONG way (e.g. `mask.astype(bool)` AND left the weights boolean, or "
            "explicitly took a logical-OR reduction) would do — it returns a 0/1 "
            "presence indicator, never the count. It fails the F2P "
            "test_weighted_sum_of_weights_bool (expects 2, not 1) for any input with "
            ">= 2 present unit weights. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q4: with boolean_dot=True the result is bool_dot (<= 1) on "
            "EVERY input, but Q4 demands int_dot; on the F2P bool_dot==1 != int_dot==2. "
            "PARTIAL-DOMAIN (the dual of weak-prepatch, now unconditional). If it "
            "VERIFIES => SPEC-TOO-WEAK (the count is not enforced)."
        ),
    },
    {
        "id": "weak-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ZERO),
        "refinement": (
            "returning the constant 0 is what a real patch that short-circuited or "
            "dropped the reduction would do. It is correct ONLY on the all-absent / "
            "all-zero-weight sub-domain (int_dot==0). On the F2P mask=[1,1] "
            "weights=[1,1] the true count is 2 != 0, so sum_of_weights() would be 0, "
            "failing test_weighted_sum_of_weights_bool (and dividing-by-zero / wrong in "
            "the mean). Does NOT resolve. (Cheap supporting partial-domain near-miss "
            "carrying a real refinement.)"
        ),
        "rationale": (
            "REJECTED by Q4 (Ensures(Result()==int_dot(ToSeq(mask),ToSeq(weights)))): "
            "0 != int_dot whenever any present sample carries a positive weight (the "
            "F2P count is 2). PARTIAL-DOMAIN: pins only the zero-count slice. If it "
            "VERIFIES => SPEC-TOO-WEAK (the result is not pinned to the count)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the consumed @ContractOnly axiom `dot_reduce` (the UNCHANGED community
# array-dot callee xarray.core.computation.dot) + the two A-reference deep models
# int_dot / bool_dot. The real callee `xr.dot` lives ONLY in the instance image, so
# the probes run in Docker. They mirror axiom_check.py (G-AX), which is embedded here
# verbatim (read on the HOST at load time — directive 6: axiom_check.py is NOT mounted
# in-container) so the soundness probe reuses the exact, audited callee logic. Each
# probe imports only stdlib + the in-image numpy/xarray, prints a diagnostic, and
# exits 0 iff the obligation holds (else 1).
# ---------------------------------------------------------------------------

# axiom-soundness: re-run the audited G-AX check (axiom_check.py) verbatim in-container.
# It executes the REAL xr.dot and asserts BOTH branches of dot_reduce's Ensures:
#   * boolean_dot=False (numeric contraction, incl. the gold astype(int) cast) ==
#     int_dot (the genuine count);
#   * boolean_dot=True (both operands boolean) == bool_dot (saturating to 0/1).
# over the GH4074 boundary + 2000 fuzz pairs. axiom_check.main() returns/exits 0 iff
# every obligation holds. We embed its source and call main().
_AX_SOUND_PROBE = (
    _AXIOM_CHECK_SRC
    + '''

# --- PBT axiom-soundness driver (runs the embedded G-AX check above) -----------
import sys as _sys
_rc = main()
if _rc != 0:
    print("AXIOM-SOUNDNESS FAIL: real xr.dot disagrees with dot_reduce/int_dot/bool_dot")
    _sys.exit(1)
print("AXIOM-SOUNDNESS OK (via embedded axiom_check.py G-AX driver): real xr.dot's "
      "numeric contraction == int_dot (incl. bool->int cast = gold) and boolean "
      "contraction == bool_dot (saturating); both branches of dot_reduce sound.")
_sys.exit(0)
'''
)

# axiom-containment: which callee-inputs can the MODEL actually reach? The gold impl
# passes EXACTLY `dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot=False)` — so the
# reachable callee input is a 0/1 mask sequence and a non-negative-int weight sequence
# of EQUAL length, evaluated in the NUMERIC branch. dot_reduce's Requires is just
# `len(mask)==len(weights)` — every reachable operand satisfies it (the precondition P3
# guarantees equal lengths). We CONFIRM containment + the A-reference soundness on the
# reachable slice by running the real numeric xr.dot on a heavy sample of reachable
# (0/1-mask, non-neg-int-weight) pairs and asserting (a) it raises nothing, (b) the
# lengths match (in-domain), and (c) it equals int_dot. (The model never passes
# boolean_dot=True; covering that branch too — as the axiom does — is sound, not a
# defect: float-vs-int rule.)
_AX_COVER_PROBE = '''
import random
import sys


def int_dot(mask, weights):
    """Reference for model.py's deep model int_dot (numeric contraction)."""
    return sum(m * w for m, w in zip(mask, weights))


def _real_numeric_dot(mask_bits, weight_ints):
    """Run the REAL xarray numeric dot: a boolean presence mask (da.notnull() is
    ALWAYS boolean) dotted with a NUMERIC (int) weight array == the gold path
    (self.weights cast to int). This is exactly the operand pair the model passes
    to dot_reduce at boolean_dot=False."""
    import numpy as np
    import xarray as xr
    m = xr.DataArray(np.asarray([bool(b) for b in mask_bits], dtype=bool), dims=["x"])
    w = xr.DataArray(np.asarray(weight_ints, dtype=int), dims=["x"])
    return int(np.asarray(xr.dot(m, w, dims="x").values).item())


def main():
    try:
        import numpy  # noqa: F401
        import xarray  # noqa: F401
    except Exception as exc:
        print("AXIOM-CONTAINMENT SKIP: xarray/numpy unavailable (%r) -- run in the "
              "evaluation image" % (exc,))
        return 0

    fails = 0
    rng = random.Random(40752)

    # Enumerate the reachable callee operands the MODEL can pass to dot_reduce:
    #   mask:    a 0/1 sequence (P4: mask[i] in {0,1});
    #   weights: a non-negative-int sequence (P4: weights[i] >= 0), of EQUAL length;
    #   boolean_dot = False (the only value the gold impl ever passes).
    # dot_reduce's Requires is len(mask)==len(weights) -- containment = every such
    # reachable pair has equal length (true by construction) AND the numeric real dot
    # equals int_dot (the A-reference deep model) on it.
    def reachable_pairs():
        # boundary: empty, length 1, the F2P shape, all-absent, mixed.
        yield [], []
        yield [1], [1]
        yield [1, 1], [1, 1]            # the F2P (count 2)
        yield [1, 0, 1], [1, 1, 1]
        yield [0, 0], [1, 1]
        yield [1, 1, 1, 1], [0, 1, 0, 1]
        yield [1, 1], [5, 7]           # non-0/1 numeric weights
        yield [1, 0, 1], [3, 5, 7]
        # fuzz: equal-length 0/1 masks and non-negative-int weights.
        for _ in range(4000):
            n = rng.randint(0, 8)
            mask = [rng.randint(0, 1) for _ in range(n)]
            weights = [rng.randint(0, 9) for _ in range(n)]
            yield mask, weights

    checked = 0
    for mask, weights in reachable_pairs():
        # (a) in-domain: dot_reduce.Requires is len(mask)==len(weights).
        if len(mask) != len(weights):
            fails += 1
            print("CONTAINMENT FAIL: reachable operand has unequal lengths %d != %d"
                  % (len(mask), len(weights)))
            continue
        # P4 sanity: mask is 0/1, weights non-negative (the model's element domain).
        assert all(b in (0, 1) for b in mask), "mask not 0/1"
        assert all(w >= 0 for w in weights), "weight negative"
        # (b)+(c) the real NUMERIC dot raises nothing and equals int_dot (A-reference).
        try:
            observed = _real_numeric_dot(mask, weights)
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print("CONTAINMENT FAIL: real xr.dot raised on reachable %r . %r: %r"
                  % (mask, weights, exc))
            continue
        expected = int_dot(mask, weights)
        if observed != expected:
            fails += 1
            print("CONTAINMENT/SOUNDNESS FAIL on reachable %r . %r: real=%r int_dot=%r"
                  % (mask, weights, observed, expected))
        checked += 1

    if fails:
        print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside dot_reduce's "
              "domain or mismatched against int_dot" % fails)
        return 1
    print("AXIOM-CONTAINMENT OK: every callee-input the model reaches "
          "(dot_reduce(0/1-mask, non-neg-int-weights, boolean_dot=False), equal "
          "length) lies in dot_reduce's Requires domain (len==len) and the real "
          "numeric xr.dot equals int_dot on all %d sampled reachable pairs." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-dot_reduce",
        "axiom": "dot_reduce",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "dot_reduce is the ONE consumed @ContractOnly axiom (the UNCHANGED "
            "community array-dot callee xarray.core.computation.dot), keyed on "
            "boolean_dot; int_dot/bool_dot are A-reference deep models. AXIOM-SOUNDNESS: "
            "the real xr.dot must match BOTH branches of dot_reduce's Ensures — numeric "
            "contraction (bool mask . int weights, incl. the astype(int) cast = the "
            "gold) == int_dot, and boolean contraction (bool mask . bool weights) == "
            "bool_dot (saturating to 0/1). The probe embeds and runs the audited G-AX "
            "check (axiom_check.py) verbatim in-container: the GH4074 boundary "
            "(xr.dot([True,True],[True,True]) -> 1 vs the cast -> 2) + 2000 fuzz pairs. "
            "If the real callee disagrees anywhere => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-dot_reduce",
        "axiom": "dot_reduce",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: the gold impl passes EXACTLY "
            "dot_reduce(ToSeq(mask), ToSeq(weights), boolean_dot=False) — a 0/1 mask and "
            "a non-negative-int weight sequence of EQUAL length, in the NUMERIC branch. "
            "dot_reduce's Requires is len(mask)==len(weights), which P3 guarantees, so "
            "every reachable operand is in-domain. The probe samples the reachable "
            "operand space (the F2P shape + boundary + 4000 equal-length 0/1-mask / "
            "non-neg-int-weight fuzz pairs), asserts the real numeric xr.dot raises "
            "nothing, the lengths match, and the result equals int_dot (the A-reference "
            "deep model). The model never passes boolean_dot=True; the axiom also "
            "covering the boolean branch is SOUND, not a defect (covering more than the "
            "caller reaches). A reachable input outside the domain or mismatched against "
            "int_dot => AXIOM-TOO-WEAK-FOR-CALLER / AXIOM-UNSOUND (none expected)."
        ),
    },
]
