# properties.py — PBT falsification battery for scikit-learn__scikit-learn-14496.
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Each SPEC_TESTS case is
# a full model.py variant that shares the FROZEN spec exactly (markers.same_spec)
# and edits ONLY inside the # impl-start/# impl-end region (the nested
# # invariants-start/# invariants-end live INSIDE that span, so loop invariants
# are part of the impl and may be reshaped too); the runner re-runs the Nagini
# verifier on each variant and compares the outcome to `expect`.
#
# --- The defended surface (read adversarially) ---------------------------------
# neighborhood_size(scaled: float) -> float turns the repository's ALREADY
# COMPUTED scaled neighbourhood value (the float64 product value*n_samples,
# carried losslessly as an interpreted real) into a whole-number sample COUNT.
# The input is a pass-by-value scalar (float): there is NO heap reference and NO
# Acc(x, 1/2) read-only input, so the frame-mutation class is N/A (there is
# nothing to overwrite to satisfy the postcondition vacuously). This is recorded
# in the assessment, not faked with an inapplicable case.
#
# The postcondition has four clauses that JOINTLY pin Result() to exactly
# floor(clamp_low(scaled)):
#   (P1) is_whole(Result())                 -- Result is an integer value
#   (P2) Result() >= 2.0                    -- floor of two
#   (P3) Result() <= clamp_low(scaled)      -- not above the clamped value
#   (P4) clamp_low(scaled) < Result() + 1.0 -- clamped value below next int
# clamp_low(scaled) = max(2.0, scaled) is a @Pure helper that is FULLY a
# function of the argument (it unfolds to a real max). It is therefore a
# GROUNDED oracle, not an opaque answer-key: there is no "wrong value an impl
# could echo and still verify", because echoing clamp_low itself (the un-floored
# real) violates P1. So the ungrounded-oracle-echo class has no wrong-echo here;
# in its place we add an honest cheapest-impl positive control (pos-cheapest) and
# the prepatch-echo uniqueness case (uniq-unfloored-echo) which the spec MUST
# reject on P1.
#
# Applicable classes: soundness (positive controls), admissibility, and
# uniqueness via PARTIAL-DOMAIN rivals (over-count / under-count / floor-of-two
# only / strict-undercount / un-floored echo). control-flow-effect is N/A (pure
# value computation, no raise/return/side-effect distinction the abstraction
# could miss). No @ContractOnly axioms in the bundle => AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14496"
FLOAT_ENCODING = "real"   # meta.json float_encoding; the spec is verified with --float-encoding=real

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region of model.py, verbatim. Every variant below is produced
# by _swap on _BASE editing ONLY the text BETWEEN # impl-start / # impl-end
# (inclusive), which guarantees same_spec (the spec view elides this whole span).
_IMPL_OLD = """    # impl-start
    clamped = clamp_low(scaled)     # type: float
    # Reduce the value to the largest whole number not exceeding it.
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 <= clamped:
        # invariants-start
        Invariant(count >= 0)
        Invariant(acc <= clamped)
        Invariant(acc == count)
        # invariants-end
        count = count + 1
        acc = acc + 1.0
    return acc
    # impl-end"""


# ---------------------------------------------------------------------------
# POSITIVE CONTROL #1 (soundness): structurally-different but CORRECT.
# Swap the order of the two body updates (acc first, then count) and rename the
# accumulator/counter locals. The loop invariant acc == count is asserted at the
# loop HEAD, so the within-body assignment order is irrelevant to soundness; the
# computed floor is identical. Keeps every gold invariant verbatim (only the
# executable shape changes) => must verify, else SPEC-TOO-STRONG.
_POS_REORDER = """    # impl-start
    bound = clamp_low(scaled)       # type: float
    steps = 0       # type: int
    total = 0.0     # type: float
    while total + 1.0 <= bound:
        # invariants-start
        Invariant(steps >= 0)
        Invariant(total <= bound)
        Invariant(total == steps)
        # invariants-end
        total = total + 1.0
        steps = steps + 1
    return total
    # impl-end"""


# POSITIVE CONTROL #2 (soundness): keeps the proven integer-counter discharge
# (acc == count establishes is_whole via the integer witness) but restructures
# the executable form: the clamped value is bound to a fresh local `bound`, the
# two body updates are reordered (acc first, then count), and an extra
# redundant-but-valid framing invariant (count <= acc) is added on top of the
# three gold invariants (none are dropped). The added invariant strengthens the
# proof state without weakening it. A faithful author could write this shape, so
# it MUST verify (else SPEC-TOO-STRONG).
_POS_SINGLE_CARRIER = """    # impl-start
    bound = clamp_low(scaled)       # type: float
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 <= bound:
        # invariants-start
        Invariant(count >= 0)
        Invariant(count <= acc)
        Invariant(acc <= bound)
        Invariant(acc == count)
        # invariants-end
        acc = acc + 1.0
        count = count + 1
    return acc
    # impl-end"""


# ---------------------------------------------------------------------------
# ADMISSIBILITY (must verify; else PRECOND-TOO-STRONG). We cannot add a
# top-level caller (it would alter the spec view and break same_spec), so the
# witness is injected INSIDE the impl region: before the real impl, assert that
# a concrete F2P-shaped input satisfies the precondition predicate. The F2P
# test (test_extract_xi) reaches the conversion with min_samples=0.1 on 31
# samples, i.e. the repo-computed scaled value float64(0.1*31) = 3.1 (exactly
# representable rounding of the product). The asserts use literals so they
# cannot be vacuous; if the Requires were unsatisfiable for a legitimate
# F2P-shaped input these asserts would be unprovable. The real floor impl then
# follows unchanged.
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    # test_extract_xi feeds min_samples=0.1 on 31 samples: the repo computes the
    # scaled value 3.1 > 0, so the precondition admits this normal input.
    Assert(3.1 > 0.0)
    # the clamped value for that input is 3.1, whose floor (3) is in range:
    Assert(clamp_low(3.1) >= 2.0)
    # --- end admissibility witness; the real impl follows unchanged ---
    clamped = clamp_low(scaled)     # type: float
    # Reduce the value to the largest whole number not exceeding it.
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 <= clamped:
        # invariants-start
        Invariant(count >= 0)
        Invariant(acc <= clamped)
        Invariant(acc == count)
        # invariants-end
        count = count + 1
        acc = acc + 1.0
    return acc
    # impl-end"""


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN rivals (each MUST be rejected; if any verifies the
# spec is SPEC-TOO-WEAK). Each is a wrong neighbourhood size whose faithful real
# patch would NOT resolve test_extract_xi (which asserts the fractional run
# equals the integer-parameter run, i.e. the exact whole-number size).

# RIVAL 1 — UN-FLOORED ECHO (the prepatch bug, ungrounded-oracle stand-in).
# Return the clamped REAL value without reducing it to a whole number. This is
# exactly model_prepatch.py / the pre-patch code `max(2, value*n_samples)`.
# Refinement: a real patch that omits int(...) leaves 2.48 / 3.1 as floats; the
# integer-only NearestNeighbors size raises the very TypeError the issue reports,
# so test_extract_xi does NOT pass. Rejection source: P1 is_whole(Result())
# (2.48 is not whole).
_UNIQ_UNFLOORED_ECHO = """    # impl-start
    clamped = clamp_low(scaled)     # type: float
    return clamped
    # impl-end"""


# RIVAL 2 — OVER-COUNT BY ONE (ceiling-like). Run the floor loop, then return
# one more than the floor. On a non-integer clamped value (e.g. 3.1) this is a
# ceiling (4), and even on an integer clamped value it over-shoots.
# Refinement: a real patch using math.ceil(value*n_samples) yields 4 for 3.1 and
# 3 for 2.48 -> too many neighbours, so the fractional run no longer equals the
# integer-parameter run and test_extract_xi fails. Rejection source: P3
# Result() <= clamp_low(scaled) (floor+1 > clamped).
_UNIQ_OVERCOUNT = """    # impl-start
    clamped = clamp_low(scaled)     # type: float
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 <= clamped:
        # invariants-start
        Invariant(count >= 0)
        Invariant(acc <= clamped)
        Invariant(acc == count)
        # invariants-end
        count = count + 1
        acc = acc + 1.0
    return acc + 1.0
    # impl-end"""


# RIVAL 3 — STRICT-UNDERCOUNT (off-by-one on whole-number inputs). Use a
# strict bound `acc + 1.0 < clamped` instead of `<=`, undercounting by one when
# the clamped value is exactly a whole number (e.g. scaled=3.0 returns 2
# instead of 3; the repo produces such values, e.g. value=1.0 on any n, or
# 0.11165523996082272*1021 which rounds in float64 to exactly 114.0). Correct
# on the F2P inputs (3.1 -> 3, 2.48 -> 2) but wrong on a sub-domain.
# Refinement: a real patch using an off-by-one truncation undercounts the
# neighbour size for any whole-number scaled value, diverging from int(...) on
# those inputs => would not resolve the P2P/other fractional callers.
# Rejection source: P4 clamp_low(scaled) < Result()+1 (3.0 < 2+1 = 3.0 is
# false).
_UNIQ_STRICT_UNDERCOUNT = """    # impl-start
    clamped = clamp_low(scaled)     # type: float
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 < clamped:
        # invariants-start
        Invariant(count >= 0)
        Invariant(acc <= clamped)
        Invariant(acc == count)
        # invariants-end
        count = count + 1
        acc = acc + 1.0
    return acc
    # impl-end"""


# RIVAL 4 — FLOOR-OF-TWO ONLY (partial-domain: correct only where the floor is
# 2). Always return 2.0, ignoring the scaled value. Correct on inputs whose
# floor is 2 (e.g. min_cluster_size=0.08, n=31 -> 2.48 -> 2) but wrong wherever
# the real size exceeds two (e.g. min_samples=0.1, n=31 -> 3.1 -> should be 3).
# Refinement: a real patch hard-coding max(2, ...) -> 2 collapses every
# fractional neighbourhood to two neighbours, so test_extract_xi's min_samples
# branch (expects 3) diverges from the integer-parameter run => does not resolve.
# Rejection source: P4 clamp_low(scaled) < Result()+1 (3.1 < 2+1 = 3.0 is
# false for the min_samples input).
_UNIQ_FLOOR_TWO_ONLY = """    # impl-start
    two = 2.0       # type: float
    return two
    # impl-end"""


# RIVAL 5 — ROUND-TO-NEAREST (rounds up at the .5 boundary). Implemented as
# floor of (clamped + 0.5): on 3.1 -> floor(3.6)=3 (coincidentally correct) and
# on 2.48 -> floor(2.98)=2 (also correct on F2P), but on a half-integer clamped
# value such as 2.5 it yields 3 where floor yields 2. Refinement: a real patch
# using round(value*n_samples) diverges from int(...) on any product with a
# fractional part >= 0.5 (e.g. min_samples=0.5, n=5 -> round(2.5)=3 vs int=2),
# so other fractional callers / P2P fixtures with such products would not match
# the integer-parameter behaviour => would not resolve. Rejection source: P3
# Result() <= clamp_low(scaled) (3 > 2.5 on the 2.5 sub-domain).
_UNIQ_ROUND_NEAREST = """    # impl-start
    clamped = clamp_low(scaled)     # type: float
    shifted = clamped + 0.5         # type: float
    count = 0       # type: int
    acc = 0.0       # type: float
    while acc + 1.0 <= shifted:
        # invariants-start
        Invariant(count >= 0)
        Invariant(acc <= shifted)
        Invariant(acc == count)
        # invariants-end
        count = count + 1
        acc = acc + 1.0
    return acc
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-reorder-rename",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_REORDER),
        "rationale": "structurally-different correct impl: body update order "
                     "swapped (acc then count) and locals renamed, gold loop "
                     "invariants kept verbatim. Same floor value; the acc==count "
                     "invariant holds at the loop head regardless of body order. "
                     "Must verify (else the spec rejects a faithful correct impl "
                     "= SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-single-carrier",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_SINGLE_CARRIER),
        "rationale": "a genuinely different proof shape: fresh local for the "
                     "clamped bound, reordered body updates, and a redundant "
                     "strengthening invariant (count <= acc) on top of the gold "
                     "three. A faithful author could write this; it must verify, "
                     "else SPEC-TOO-STRONG.",
    },
    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region "
                     "asserts that the F2P-shaped input scaled=3.1 (the repo's "
                     "float64 product 0.1*31 from test_extract_xi) satisfies the "
                     "precondition predicate and yields an in-range clamped "
                     "value. If the Requires could not admit a normal F2P input "
                     "these asserts would be unprovable => PRECOND-TOO-STRONG. "
                     "The real floor impl follows unchanged.",
    },
    # ---- uniqueness / partial-domain rivals (must be rejected; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-unfloored-echo",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_UNFLOORED_ECHO),
        "refinement": "this is the pre-patch code itself "
                      "(max(2, value*n_samples) with no int wrap); it leaves "
                      "2.48 / 3.1 as floats, and the integer-only neighbour "
                      "search raises the TypeError the issue reports, so "
                      "test_extract_xi does NOT pass. A faithful real patch with "
                      "this body would not resolve.",
        "rationale": "rejected by P1 is_whole(Result()): clamp_low(scaled) is "
                     "a real value that need not be a whole number (e.g. 2.48), "
                     "so the integrality postcondition is unprovable.",
    },
    {
        "id": "uniq-overcount-ceiling",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OVERCOUNT),
        "refinement": "returning floor+1 is a ceiling on non-integer products "
                      "(3.1 -> 4, 2.48 -> 3); a real patch using "
                      "math.ceil(value*n_samples) over-counts neighbours, so the "
                      "fractional run no longer equals the integer-parameter run "
                      "asserted by test_extract_xi => would not resolve.",
        "rationale": "rejected by P3 Result() <= clamp_low(scaled): floor+1 "
                     "exceeds the clamped value, so the upper-bound clause is "
                     "unprovable.",
    },
    {
        "id": "uniq-strict-undercount",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_STRICT_UNDERCOUNT),
        "refinement": "the strict loop bound undercounts by one whenever the "
                      "clamped value is exactly a whole number (scaled=3.0 "
                      "returns 2 not 3); the repo produces such values (value=1.0 "
                      "on any n; float64 products that round to a whole double, "
                      "e.g. 0.11165523996082272*1021 = 114.0). A real patch with "
                      "this off-by-one truncation diverges from int(...) on every "
                      "whole-product caller => would not resolve.",
        "rationale": "rejected by P4 clamp_low(scaled) < Result()+1: on a whole "
                     "clamped value v, the strict bound returns v-1 and "
                     "v < (v-1)+1 = v is false, so the lower-bound clause is "
                     "unprovable (it is the existential floor-tightness pin).",
    },
    {
        "id": "uniq-floor-of-two-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_FLOOR_TWO_ONLY),
        "refinement": "always returning 2 is correct only where the real floor is "
                      "two; on test_extract_xi's min_samples=0.1, n=31 the size "
                      "must be 3, so collapsing it to 2 changes the neighbour "
                      "count and the fractional run diverges from the "
                      "integer-parameter run => does not resolve.",
        "rationale": "rejected by P4 clamp_low(scaled) < Result()+1: for any "
                     "input whose clamped value is >= 3 (e.g. 3.1), 3.1 < 2+1 = "
                     "3.0 is false, so the floor-tightness clause is unprovable.",
    },
    {
        "id": "uniq-round-to-nearest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_ROUND_NEAREST),
        "refinement": "round-to-nearest (floor of clamped+0.5) agrees with floor "
                      "on the two F2P inputs but diverges on any product with a "
                      "fractional part >= 0.5 (0.5*5 -> 2.5 rounds to 3 vs "
                      "int=2); a real patch using round(value*n_samples) would "
                      "over-count on such P2P/fractional inputs and not match the "
                      "integer-parameter behaviour => would not resolve.",
        "rationale": "rejected by P3 Result() <= clamp_low(scaled): on a "
                     "half-integer clamped value v.5 the rounded result v+1 "
                     "exceeds v.5, so the upper-bound clause is unprovable.",
    },
]


# No @ContractOnly axioms and no consumed-axiom deep models in this bundle: the
# only changed operation (the int(...) wrap) is modelled DEEPLY by the verified
# floor loop, and the supporting max is spelled out as a @Pure helper
# (clamp_low). The A-reference soundness of the floor loop == the real
# int(max(2, <scaled>)) is already covered by axiom_check.py / G-AX; there is no
# @ContractOnly obligation for the PBT axiom lane to probe.
AXIOM_TESTS = []
