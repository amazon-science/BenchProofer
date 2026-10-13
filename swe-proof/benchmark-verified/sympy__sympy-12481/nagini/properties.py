# properties.py — PBT manifest for sympy__sympy-12481. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) executes.
#
# Defended surface (read model.py):
#   compose_cycles(n, a, b, c, d) -> List[int] builds the array form of the
#   left-to-right composition of two GENUINE two-element swaps (a b) then (c d)
#   over the n points 0..n-1. The LOAD-BEARING postcondition clause is
#       Forall i in [0,n): ToSeq(Result())[i] == swap_val(swap_val(i, a, b), c, d)
#   (the composition pin), guarded by a range clause
#       Forall i in [0,n): 0 <= ToSeq(Result())[i] < n
#   and the shape clauses Acc(list_pred(Result())) + len(Result()) == n.
#
#   There are NO read-only (Acc(x, 1/2)) inputs — every parameter is a plain int
#   and the only Acc is on the freshly-built Result(). So frame-mutation is N/A.
#   The oracle swap_val is a @Pure helper but it is GROUNDED (a total function of
#   the args, fully unfolded), so there is no wrong-echo to build — the cheapest
#   honest impl IS the oracle, included as a positive control. There is no
#   raise/side-effect channel distinct from the returned value, so
#   control-flow-effect is N/A. The bundle consumes NO @ContractOnly axiom; the
#   composition is an A-reference deep model, validated against the real callee
#   in the AXIOM_TESTS below (G-AX logic).
#
# The reasoned attacks are all PARTIAL-DOMAIN / wrong-function rivals against the
# composition pin (the prepatch defect is one of them):
#   - drop the second swap (a b)-only;
#   - compose in the wrong order (c d) then (a b);
#   - skip a boundary position (first / last element);
#   - disjoint-only (the prepatch shape) — second swap applied only when the two
#     cycles share no point, leaving cross-cycle non-disjoint inputs uncomposed.
from pathlib import Path

INSTANCE = "sympy__sympy-12481"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The whole gold impl block (markers inclusive). Unique in _BASE; each variant
# replaces it wholesale so edits are CONFINED to the impl region => same_spec.
_GOLD_IMPL = """\
    # impl-start
    # Build the identity array 0..n-1 (the points in their original order).
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        result.append(j)
        Assert(ToSeq(result) == old_seq + PSeq(j))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == j)
        j = j + 1
    # Apply the first swap (a b) point-wise, then the second swap (c d).
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        prev = ToSeq(result)  # type: PSeq[int]
        result[i] = swap_val(i, a, b)
        Assert(ToSeq(result) == prev.update(i, swap_val(i, a, b)))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        i = i + 1
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        prev2 = ToSeq(result)  # type: PSeq[int]
        Assert(ToSeq(result)[i] == swap_val(i, a, b))
        Assert(result[i] == swap_val(i, a, b))
        new_val = swap_val(result[i], c, d)  # type: int
        Assert(new_val == swap_val(swap_val(i, a, b), c, d))
        result[i] = new_val
        Assert(ToSeq(result) == prev2.update(i, new_val))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev2[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
        i = i + 1
    return result
    # impl-end"""

assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block not found uniquely (drift)"


def _impl(body: str) -> str:
    """Return a full model.py whose impl region is replaced by `body`
    (markers inclusive). Edits are confined to the impl region => same_spec."""
    if not body.startswith("    # impl-start") or not body.rstrip().endswith("# impl-end"):
        raise AssertionError("variant body must be the full marked impl block")
    return _BASE.replace(_GOLD_IMPL, body, 1)


# --------------------------------------------------------------------------- #
# POSITIVE CONTROL (soundness): cheapest honest impl — a SINGLE forward loop
# that writes the fully-composed value directly. Structurally different from the
# gold three-loop build (identity -> swap1 -> swap2), but it keeps exactly the
# framing the per-element pin needs (a forward loop with a prefix invariant +
# the per-element pin around the append). Must verify; else SPEC-TOO-STRONG.
# This is also the "cheapest impl that satisfies the load-bearing clause" — and
# because swap_val is grounded, it IS correct (there is no wrong echo).
# Termination: ONE loop, `while j < n` with j up by one, so the whole measure is
# `n - j + 1` -- the gold's three separate measures do not transfer, there is
# only one loop here to carry one.
# --------------------------------------------------------------------------- #
_POS_SINGLE_LOOP = """\
    # impl-start
    # Single forward pass: append the fully-composed image of each point.
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        composed = swap_val(swap_val(j, a, b), c, d)  # type: int
        result.append(composed)
        Assert(ToSeq(result) == old_seq + PSeq(composed))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == swap_val(swap_val(j, a, b), c, d))
        j = j + 1
    return result
    # impl-end"""

# --------------------------------------------------------------------------- #
# POSITIVE CONTROL #2 (soundness): same three-phase shape as gold but the first
# two phases are FUSED — build the identity, then in ONE loop apply both swaps
# to each position. A different executable shape that keeps the loop invariants
# valid (no induction lemma needed; per-element pin only). Must verify.
# Termination: TWO loops here, not three, so it carries two measures of its own:
# `n - j + 1` for the identity build and `n - i + 1` for the fused swap pass.
# The gold's third measure has no loop to attach to in this shape.
# --------------------------------------------------------------------------- #
_POS_FUSED = """\
    # impl-start
    # Build the identity, then apply BOTH swaps to each position in one loop.
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        result.append(j)
        Assert(ToSeq(result) == old_seq + PSeq(j))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == j)
        j = j + 1
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(result) == n)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(i <= k and k < n,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        prev = ToSeq(result)  # type: PSeq[int]
        Assert(ToSeq(result)[i] == i)
        new_val = swap_val(swap_val(i, a, b), c, d)  # type: int
        result[i] = new_val
        Assert(ToSeq(result) == prev.update(i, new_val))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < n and k != i,
                      ToSeq(result)[k] == prev[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[i] == swap_val(swap_val(i, a, b), c, d))
        i = i + 1
    return result
    # impl-end"""

# --------------------------------------------------------------------------- #
# ADMISSIBILITY: a top-level caller would leave the impl region and break
# same_spec (the proven pattern). So we do it IN-REGION on the gold impl: at the
# top of compose_cycles, assert that the precondition facts are USABLE (n >= 1,
# points in range, a != b, c != d — exactly the F2P-shaped domain like
# [[0,1],[0,2]] over n=3), and that the composed image of an arbitrary in-range
# point is itself in range (so a non-degenerate, in-domain return is reachable).
# If the Requires were vacuous / over-strong the impl could not both consume the
# facts and verify => PRECOND-TOO-STRONG. The gold body is kept verbatim so the
# function still verifies.
# --------------------------------------------------------------------------- #
# the gold body with admissibility asserts spliced in just after the
# `# impl-start` marker line (still inside the impl region => same_spec holds).
assert _GOLD_IMPL.startswith("    # impl-start\n")
_ADMISS_BODY = "    # impl-start\n" + """\
    # admissibility: the precondition admits a normal F2P-shaped input
    # (e.g. the discriminator [[0,1],[0,2]] over n=3 -> n>=1, points<n, a!=b, c!=d).
    Assert(n >= 1)                       # from Requires; usable
    Assert(a != b and c != d)            # genuine cycles; usable
    Assert(0 <= a and a < n and 0 <= c and c < n)
    # a non-degenerate composed image is reachable and in range for the named
    # points (the postcondition's composition pin is satisfiable, not vacuous):
    Assert(0 <= swap_val(swap_val(a, a, b), c, d)
           and swap_val(swap_val(a, a, b), c, d) < n)
""" + _GOLD_IMPL[len("    # impl-start\n"):]
_ADMISS = _impl(_ADMISS_BODY)

# --------------------------------------------------------------------------- #
# REJECT rivals (uniqueness — SPEC-TOO-WEAK if any verifies).
# Each shares the spec exactly and changes only the impl. Each must FAIL to
# verify because it violates the composition pin on some in-domain input.
# --------------------------------------------------------------------------- #

# (R1) DROP THE SECOND SWAP: apply only (a b); never apply (c d). Correct only
# when (c d) moves nothing in range, i.e. fails whenever swap_val(., c, d) != id
# on a reachable value. Faithful real patch: composes only the first cycle, so
# Permutation([[0,1],[0,2]]) would build [1,0,2] (just the swap (0 1)) != (0 1 2)
# == [1,2,0] -> the F2P assertion FAILS -> does NOT resolve.
# Termination: one `while j < n` pass, measure `n - j + 1`. Dropping the second
# swap changes the value appended, not the counting, so the measure is the same
# shape as the gold's first loop -- and this rival must still be rejected for the
# composition pin, not for a missing obligation.
_REJ_DROP_SECOND = """\
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        composed = swap_val(j, a, b)  # type: int
        result.append(composed)
        Assert(ToSeq(result) == old_seq + PSeq(composed))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == swap_val(j, a, b))
        j = j + 1
    return result
    # impl-end"""

# (R2) WRONG ORDER: compose right-to-left, swap_val(swap_val(i, c, d), a, b),
# i.e. (c d) first then (a b). Equal to gold only when the two swaps commute.
# Faithful real patch: composes the cycles in reverse order. For [[0,1],[0,2]]
# it would yield swap_val(swap_val(i,0,2),0,1): position 0 -> swap_val(2,0,1)==2,
# giving [2,0,1] != [1,2,0] -> F2P assertion FAILS -> does NOT resolve.
# Termination: one `while j < n` pass, measure `n - j + 1`. Reversing the
# composition order changes only which value is appended, not the loop counter.
_REJ_WRONG_ORDER = """\
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == swap_val(swap_val(k, c, d), a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        composed = swap_val(swap_val(j, c, d), a, b)  # type: int
        result.append(composed)
        Assert(ToSeq(result) == old_seq + PSeq(composed))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == swap_val(swap_val(j, c, d), a, b))
        j = j + 1
    return result
    # impl-end"""

# (R3) SKIP THE FIRST POSITION: leave position 0 as the identity (0), compose
# the rest. Correct on every position except 0; wrong wherever the composition
# moves point 0. Faithful real patch: an off-by-one that mis-handles the first
# point. For [[0,1],[0,2]] position 0 should be 1 but stays 0 -> array [0,2,?]
# != [1,2,0] -> F2P FAILS -> does NOT resolve. (partial-domain: first element.)
# Termination: one `while j < n` pass, measure `n - j + 1`. The `if j != 0:`
# guard picks a different value for position 0; it does not skip the increment,
# so every iteration still lowers `n - j + 1` by exactly one.
_REJ_SKIP_FIRST = """\
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(1 <= k and k < j,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Implies(j >= 1, ToSeq(result)[0] == 0))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        composed = j  # type: int
        if j != 0:
            composed = swap_val(swap_val(j, a, b), c, d)
        result.append(composed)
        Assert(ToSeq(result) == old_seq + PSeq(composed))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        j = j + 1
    return result
    # impl-end"""

# (R4) SKIP THE LAST POSITION: compose positions 0..n-2, leave position n-1 as
# the identity. Correct everywhere except the last point. Faithful real patch:
# an off-by-one truncating the loop one short. For [[0,1],[0,2]] (n=3) position 2
# should be 0 but stays 2 -> array [1,2,2] (or [1,?,2]) != [1,2,0] -> F2P FAILS
# -> does NOT resolve. (partial-domain: last element.)
# Termination: one `while j < n` pass, measure `n - j + 1`. Despite the name this
# rival does NOT truncate the loop -- it still runs all n positions and only
# writes the identity at n-1, so the bound is the gold's `n`, not `n - 1`.
_REJ_SKIP_LAST = """\
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j and k < n - 1,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Implies(j == n, ToSeq(result)[n - 1] == n - 1))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        composed = j  # type: int
        if j != n - 1:
            composed = swap_val(swap_val(j, a, b), c, d)
        result.append(composed)
        Assert(ToSeq(result) == old_seq + PSeq(composed))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        j = j + 1
    return result
    # impl-end"""

# (R5) DISJOINT-ONLY (the prepatch defect, expressed in-impl): apply the second
# swap (c d) ONLY when the two cycles share no point (c != a and c != b and
# d != a and d != b); otherwise leave just the first swap. This is exactly the
# behaviour the gold patch REMOVES — it re-introduces the non-disjoint rejection
# as "leave uncomposed". Faithful real patch == the prepatch code: it would
# raise/skip on non-disjoint cycles, so Permutation([[0,1],[0,2]]) would NOT
# equal (0 1 2) -> F2P FAILS -> does NOT resolve. (This mirrors model_prepatch.)
# Termination: one `while j < n` pass, measure `n - j + 1`. `disjoint` is computed
# once BEFORE the loop and never reassigned, so the `if disjoint:` guard selects a
# value inside the body and cannot affect how `j` advances.
_REJ_DISJOINT_ONLY = """\
    # impl-start
    disjoint = c != a and c != b and d != a and d != b  # type: bool
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j and disjoint,
                       ToSeq(result)[k] == swap_val(swap_val(k, a, b), c, d)),
                       [[ToSeq(result)[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j and not disjoint,
                       ToSeq(result)[k] == swap_val(k, a, b)),
                       [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        composed = swap_val(j, a, b)  # type: int
        if disjoint:
            composed = swap_val(swap_val(j, a, b), c, d)
        result.append(composed)
        Assert(ToSeq(result) == old_seq + PSeq(composed))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        j = j + 1
    return result
    # impl-end"""

# (R6) DEGENERATE RANGE-ONLY FILL: return the identity 0..n-1. It satisfies the
# range clause (every value in [0,n)) and the shape clauses, but violates the
# composition pin whenever the composition is not the identity. This probes
# whether the range clause alone could be mistaken for the spec. Faithful real
# patch: returns the identity regardless of the cycles, so Permutation(...) would
# be the identity for [[0,1],[0,2]] != (0 1 2) -> F2P FAILS -> does NOT resolve.
# Termination: one `while j < n` pass, measure `n - j + 1`. This rival terminates
# perfectly well -- it is rejected for the composition pin, which is exactly the
# separation the obligation must not disturb.
_REJ_IDENTITY = """\
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < n:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= n)
        Invariant(len(result) == j)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < j,
                       ToSeq(result)[k] == k), [[ToSeq(result)[k]]])))
        Invariant(MustTerminate(n - j + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        result.append(j)
        Assert(ToSeq(result) == old_seq + PSeq(j))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < j,
                      ToSeq(result)[k] == old_seq[k]), [[ToSeq(result)[k]]])))
        Assert(ToSeq(result)[j] == j)
        j = j + 1
    return result
    # impl-end"""


SPEC_TESTS = [
    {
        "id": "pos-single-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_SINGLE_LOOP),
        "rationale": "A structurally-different CORRECT impl: one forward loop "
        "appending the fully-composed image swap_val(swap_val(j,a,b),c,d) per "
        "point, instead of gold's identity->swap1->swap2 three-loop build. It "
        "keeps the forward prefix invariant + per-element pin around the append "
        "(no induction lemma needed). Must verify; else SPEC-TOO-STRONG. Also "
        "the cheapest honest impl of the grounded oracle (no wrong echo exists).",
    },
    {
        "id": "pos-fused-two-phase",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_FUSED),
        "rationale": "Another correct shape: build the identity, then apply BOTH "
        "swaps to each position in a SINGLE second loop (gold uses two separate "
        "loops). Keeps the gold prefix/suffix invariants and per-element pin; the "
        "verifier discharges it with no extra lemma. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-f2p-witness",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "A positive-control caller invokes compose_cycles(3,0,1,0,2) "
        "(the F2P discriminator [[0,1],[0,2]]). The Requires (n>=1, points in "
        "range, a!=b, c!=d) must admit this normal in-domain input and the "
        "postcondition must pin position 0. If the call fails to verify, "
        "PRECOND-TOO-STRONG.",
    },
    {
        "id": "rej-drop-second-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REJ_DROP_SECOND),
        "refinement": "Applies only the first swap (a b), never (c d). Faithful "
        "real patch composes only the first cycle, so Permutation([[0,1],[0,2]]) "
        "builds [1,0,2] (the swap (0 1)) != Permutation(0,1,2) == [1,2,0]; the "
        "F2P assertion test_args fails -> does NOT resolve.",
        "rationale": "Violates the composition pin clause whenever (c d) moves a "
        "reachable value (e.g. position 1: should be swap_val(swap_val(1,0,1),0,2)"
        "=swap_val(0,0,2)=2 but is swap_val(1,0,1)=0). If it verifies, SPEC-TOO-WEAK.",
    },
    {
        "id": "rej-wrong-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REJ_WRONG_ORDER),
        "refinement": "Composes right-to-left (c d) then (a b) instead of "
        "left-to-right. Faithful real patch composes the cycles in reverse order; "
        "for [[0,1],[0,2]] it yields [2,0,1] != [1,2,0], so the F2P assertion "
        "test_args fails -> does NOT resolve. (The two cycles do not commute.)",
        "rationale": "Violates the composition pin (left-to-right order is the "
        "load-bearing clause: swap_val(swap_val(i,a,b),c,d)). For i=0: gold pins 1, "
        "rival gives swap_val(swap_val(0,0,2),0,1)=swap_val(2,0,1)=2. SPEC-TOO-WEAK if verifies.",
    },
    {
        "id": "rej-skip-first-pos",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REJ_SKIP_FIRST),
        "refinement": "Leaves position 0 as the identity, composes the rest. "
        "Faithful real patch is an off-by-one mis-handling the first point; for "
        "[[0,1],[0,2]] position 0 should be 1 but stays 0, so the array != "
        "[1,2,0] and the F2P assertion test_args fails -> does NOT resolve.",
        "rationale": "Partial-domain (first element): violates the composition "
        "pin at i=0 whenever the composition moves point 0. SPEC-TOO-WEAK if verifies.",
    },
    {
        "id": "rej-skip-last-pos",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REJ_SKIP_LAST),
        "refinement": "Leaves position n-1 as the identity, composes 0..n-2. "
        "Faithful real patch truncates the loop one short; for [[0,1],[0,2]] (n=3) "
        "position 2 should be 0 but stays 2, so the array != [1,2,0] and the F2P "
        "assertion test_args fails -> does NOT resolve.",
        "rationale": "Partial-domain (last element): violates the composition pin "
        "at i=n-1 whenever the composition moves the last point. SPEC-TOO-WEAK if verifies.",
    },
    {
        "id": "rej-disjoint-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REJ_DISJOINT_ONLY),
        "refinement": "Applies the second swap ONLY when the two cycles are "
        "disjoint (share no point); leaves non-disjoint inputs as just (a b). This "
        "is the prepatch defect (the bug the gold patch fixes) expressed in-impl: "
        "the faithful real patch == model_prepatch.py, which re-rejects/skips "
        "non-disjoint cycles, so Permutation([[0,1],[0,2]]) != (0 1 2); the F2P "
        "assertion test_args fails -> does NOT resolve.",
        "rationale": "Violates the composition pin on every cross-cycle "
        "non-disjoint input (the exact behaviour the change enables; G-DIFF "
        "discriminator (0 1)(0 2)). If it verifies, SPEC-TOO-WEAK (the spec would "
        "fail to sense the change).",
    },
    {
        "id": "rej-identity-range-fill",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_REJ_IDENTITY),
        "refinement": "Returns the identity 0..n-1 ignoring the cycles. Satisfies "
        "the range/shape clauses but not the composition. Faithful real patch "
        "returns the identity for any input, so Permutation([[0,1],[0,2]]) is the "
        "identity != (0 1 2); the F2P assertion test_args fails -> does NOT resolve.",
        "rationale": "Probes whether the range clause (0 <= val < n) could be "
        "mistaken for the spec: the composition pin still forbids the identity "
        "whenever the composition is non-trivial. SPEC-TOO-WEAK if verifies "
        "(supporting case — the strongest evidence the pin, not just the range, is load-bearing).",
    },
]


# --------------------------------------------------------------------------- #
# AXIOM lane: no @ContractOnly axiom is consumed, but the composition is an
# A-REFERENCE deep model (swap_val + the verified loops). We validate it against
# the REAL repository callee (Permutation cyclic-form construction) in-container
# with the gold patch applied — the G-AX obligation, recast as an axiom-soundness
# probe and a caller-domain containment probe. The probes embed the bundle's own
# axiom_check.py logic (read on the HOST at load time; the runner mounts only the
# probe). Probes import only stdlib + the in-container sympy; open nothing.
# --------------------------------------------------------------------------- #

_AX_SOUND_PROBE = r'''
import sys
import random
from itertools import product

try:
    from sympy.combinatorics.permutations import Permutation
except Exception as exc:  # pragma: no cover
    print("FAIL: cannot import sympy Permutation:", exc)
    sys.exit(1)


def swap_val(x, a, b):
    if x == a:
        return b
    if x == b:
        return a
    return x


def model_array(n, a, b, c, d):
    # the model's deep reference: (a b) then (c d), left-to-right
    return [swap_val(swap_val(i, a, b), c, d) for i in range(n)]


def real_array(n, a, b, c, d):
    return list(Permutation([[a, b], [c, d]], size=n).array_form)


mismatches = 0
checked = 0

# Exhaustive over GENUINE two-element cycles (a != b, c != d) — the model's
# Requires domain == the real callee's accepting set — for n <= 6, INCLUDING
# every cross-cycle non-disjoint (shared-point) configuration the change enables.
for n in range(1, 7):
    for a, b, c, d in product(range(n), repeat=4):
        if a == b or c == d:
            continue
        try:
            obs = real_array(n, a, b, c, d)
        except Exception as exc:
            print("FAIL domain over-claim: in-domain genuine cycles "
                  "(%d %d)(%d %d) n=%d RAISED %s: %s"
                  % (a, b, c, d, n, type(exc).__name__, exc))
            mismatches += 1
            continue
        exp = model_array(n, a, b, c, d)
        if obs != exp:
            print("FAIL unsound: n=%d (%d %d)(%d %d) real=%r model=%r"
                  % (n, a, b, c, d, obs, exp))
            mismatches += 1
        elif sorted(obs) != list(range(n)):
            print("FAIL not a permutation: n=%d real=%r" % (n, obs))
            mismatches += 1
        checked += 1

# Randomized fuzz over larger sizes.
rng = random.Random(12481)
for _ in range(20000):
    n = rng.randint(2, 40)
    a = rng.randint(0, n - 1)
    b = rng.randint(0, n - 1)
    while b == a:
        b = rng.randint(0, n - 1)
    c = rng.randint(0, n - 1)
    d = rng.randint(0, n - 1)
    while d == c:
        d = rng.randint(0, n - 1)
    try:
        obs = real_array(n, a, b, c, d)
    except Exception as exc:
        print("FAIL domain over-claim (fuzz): (%d %d)(%d %d) n=%d RAISED %s"
              % (a, b, c, d, n, type(exc).__name__))
        mismatches += 1
        continue
    exp = model_array(n, a, b, c, d)
    if obs != exp:
        print("FAIL unsound (fuzz): n=%d (%d %d)(%d %d) real=%r model=%r"
              % (n, a, b, c, d, obs, exp))
        mismatches += 1
    checked += 1

# Explicit F2P / problem-statement witnesses.
if Permutation([[0, 1], [0, 2]]) != Permutation(0, 1, 2):
    print("FAIL F2P witness: [[0,1],[0,2]] != (0 1 2)")
    mismatches += 1
if model_array(3, 0, 1, 0, 2) != [1, 2, 0]:
    print("FAIL model F2P witness: model_array(3,0,1,0,2) != [1,2,0]")
    mismatches += 1
if Permutation([[0, 1], [0, 1]]) != Permutation([0, 1]):
    print("FAIL problem witness: [[0,1],[0,1]] is not the identity")
    mismatches += 1

if mismatches:
    print("AXIOM-UNSOUND: %d mismatch(es) over %d in-domain inputs" % (mismatches, checked))
    sys.exit(1)
print("OK: deep model == real Permutation cyclic-form construction on %d "
      "in-domain inputs (exhaustive n<=6 genuine cycles + 20000 fuzz + 3 "
      "witnesses); every cross-cycle non-disjoint config matches; no in-domain raise." % checked)
sys.exit(0)
'''

_AX_CONTAIN_PROBE = r'''
import sys
from itertools import product

try:
    from sympy.combinatorics.permutations import Permutation
except Exception as exc:  # pragma: no cover
    print("FAIL: cannot import sympy Permutation:", exc)
    sys.exit(1)

# Containment: every callee-input the MODEL can reach must lie in the real
# callee's ACCEPTING domain (it must construct without raising). The model's
# Requires are: n >= 1; 0 <= a,b,c,d < n; a != b; c != d. The model passes
# EXACTLY [[a,b],[c,d]] with size=n to the real callee. So the reachable
# callee-inputs are all genuine two-element cycle pairs over n points. We
# enumerate them (n <= 6 exhaustive) and assert each is accepted. Covering MORE
# than the caller reaches would be sound, not a defect; here we check the caller
# never reaches an input OUTSIDE the callee's accepting set (which would be
# AXIOM-TOO-WEAK-FOR-CALLER / a domain over-claim).
outside = 0
reachable = 0
for n in range(1, 7):
    for a, b, c, d in product(range(n), repeat=4):
        # model Requires gate (exactly what compose_cycles admits):
        if not (n >= 1 and 0 <= a < n and 0 <= b < n and 0 <= c < n
                and 0 <= d < n and a != b and c != d):
            continue
        reachable += 1
        try:
            p = Permutation([[a, b], [c, d]], size=n)
            _ = list(p.array_form)
        except Exception as exc:
            print("FAIL containment: model-reachable input (%d %d)(%d %d) n=%d "
                  "is OUTSIDE the real callee's accepting domain (RAISED %s: %s)"
                  % (a, b, c, d, n, type(exc).__name__, exc))
            outside += 1

# Boundary sentinels: coincident cycles (fully non-disjoint, a==c & b==d) and
# shared-single-point cycles must also be accepted (they satisfy a!=b, c!=d).
for n, tup in [(2, (0, 1, 0, 1)), (3, (0, 1, 1, 2)), (3, (0, 1, 0, 2)),
               (4, (1, 3, 3, 1)), (5, (0, 4, 4, 0))]:
    a, b, c, d = tup
    reachable += 1
    try:
        _ = list(Permutation([[a, b], [c, d]], size=n).array_form)
    except Exception as exc:
        print("FAIL containment sentinel: (%d %d)(%d %d) n=%d RAISED %s: %s"
              % (a, b, c, d, n, type(exc).__name__, exc))
        outside += 1

if outside:
    print("AXIOM-TOO-WEAK-FOR-CALLER: %d model-reachable input(s) outside the "
          "callee accepting domain" % outside)
    sys.exit(1)
print("OK: all %d model-reachable callee-inputs (genuine two-element cycle "
      "pairs, incl. non-disjoint + coincident) lie in the real callee's "
      "accepting domain (no in-domain raise)." % reachable)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-deepmodel",
        "axiom": "swap_val composition (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "No @ContractOnly axiom is consumed, but the composition is "
        "an A-reference deep model. Validate swap_val(swap_val(i,a,b),c,d) == the "
        "real Permutation([[a,b],[c,d]], size=n).array_form on every in-domain "
        "(a!=b, c!=d) input (exhaustive n<=6 + 20000 fuzz + the F2P/problem "
        "witnesses), under the post-gold runtime config. Any mismatch (or an "
        "in-domain raise) is AXIOM-UNSOUND. Mirrors axiom_check.py / G-AX.",
    },
    {
        "id": "ax-contain-caller-domain",
        "axiom": "swap_val composition (A-reference deep model)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAIN_PROBE,
        "rationale": "Every callee-input the model can reach (genuine two-element "
        "cycle pairs over n points: model Requires n>=1, points<n, a!=b, c!=d, "
        "passing exactly [[a,b],[c,d]] size=n) must lie in the real callee's "
        "ACCEPTING domain. Enumerate them (n<=6 + non-disjoint/coincident "
        "sentinels) and assert no in-domain input raises; a raise would be "
        "AXIOM-TOO-WEAK-FOR-CALLER (a domain over-claim).",
    },
]
