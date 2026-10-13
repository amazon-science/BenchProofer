# properties.py — PBT manifest for sympy__sympy-21847. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md / meta.json):
#   * keep_comm(powers: List[int], min_degree: int) -> bool   (site 1, hunk 1)
#   * keep_noncomm(powers: List[int], min_degree: int) -> bool (site 2, hunk 2)
#     Both carry the BYTE-IDENTICAL frozen spec and impl skeleton:
#       READ-ONLY input  powers          (Acc(list_pred(powers), 1/2))
#       Requires min_degree >= 0 ; every powers[i] >= 0
#       LOAD-BEARING post  Result() == (deg_sum(ToSeq(powers)) >= min_degree)
#     The single behavioural change the gold patch makes is the REDUCTION over
#     the exponent vector: pre-patch max(powers.values()), post-patch
#     sum(powers.values()). deg_sum is the SUM spelled out as a front-recursive
#     @Pure fold (deg_sum(p) = p[0] + deg_sum(p.drop(1))); the impl computes it
#     with a BACKWARD loop (i from len(powers) down to 0) whose invariant is
#     total == deg_sum(ToSeq(powers).drop(i)) and whose two framing Asserts
#     trigger the front-recursive unfold.
#
#   * deg_sum is a GROUNDED oracle: it fully unfolds to an arithmetic sum over
#     the ACTUAL input handle ToSeq(powers); it is a function of the args, not an
#     opaque answer key, so there is no "wrong echo" to build (UNGROUNDED-ORACLE
#     is N/A here — see assessment). The honest cheapest impl IS the loop that
#     computes the sum; any cheaper impl that skips elements / uses a different
#     reduction is caught by the postcondition.
#   * No @ContractOnly axiom and no A-reference deep model in this bundle
#     (the changed reduction is modeled deeply, not axiomatized) => AXIOM_TESTS=[].
#
# Region-surgery: each variant is built by _swap on the FULL function block of
# ONE function (def ... -> # impl-end). The two functions are byte-identical
# except for their names, so the impl text alone is NOT unique; anchoring on the
# whole named block makes the swap unique while still editing ONLY text inside
# that function's # impl-start/# impl-end region. The frozen spec
# (axioms/pure/pre/post-conditions/invariants) is never touched -> same_spec by
# construction.
from pathlib import Path

INSTANCE = "sympy__sympy-21847"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors: the FULL gold function block for each site (unique by the def name).
# Only text strictly inside the # impl-start/# impl-end region is rewritten in
# each variant; the pre/post-conditions and the # invariants-* block are kept
# verbatim so same_spec holds and any rejection is attributable to the impl.
# ---------------------------------------------------------------------------

_COMM_GOLD = '''def keep_comm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree
    # impl-end'''

_NONCOMM_GOLD = '''def keep_noncomm(powers: List[int], min_degree: int) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(powers), 1 / 2))
    Requires(min_degree >= 0)
    Requires(Forall(int, lambda i: (Implies(0 <= i and i < len(powers),
                                            powers[i] >= 0),
                                    [[powers[i]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(powers), 1 / 2))
    # The candidate is retained exactly when its TOTAL degree (the sum of the
    # per-variable exponents) meets the lower bound.
    Ensures(Result() == (deg_sum(ToSeq(powers)) >= min_degree))
    # post-conditions-end
    # impl-start
    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree
    # impl-end'''

# Sanity: both anchors are present exactly once in _BASE.
assert _BASE.count(_COMM_GOLD) == 1, "comm anchor drift"
assert _BASE.count(_NONCOMM_GOLD) == 1, "noncomm anchor drift"


# ===========================================================================
# (1) FRAME-MUTATION — MANDATORY: powers is read-only (Acc(list_pred(powers),
# 1/2)). A rival that WRITES to powers while still computing the correct sum
# must be rejected for INSUFFICIENT PERMISSION. The write powers[i-1]=powers[i-1]
# is a VALUE no-op, so the postcondition would still hold; the spec must reject
# on permission grounds alone. All gold invariants/framing Asserts are kept
# VERBATIM so the rejection is attributable solely to the write.
# ===========================================================================
_frame_mut_comm = _swap(
    _BASE,
    _COMM_GOLD,
    _COMM_GOLD.replace(
        "        total = powers[i - 1] + total\n        i = i - 1",
        "        total = powers[i - 1] + total\n"
        "        powers[i - 1] = powers[i - 1]  # WRITE to read-only input -> insufficient permission\n"
        "        i = i - 1",
    ),
)

_frame_mut_noncomm = _swap(
    _BASE,
    _NONCOMM_GOLD,
    _NONCOMM_GOLD.replace(
        "        total = powers[i - 1] + total\n        i = i - 1",
        "        total = powers[i - 1] + total\n"
        "        powers[i - 1] = powers[i - 1]  # WRITE to read-only input -> insufficient permission\n"
        "        i = i - 1",
    ),
)


# ===========================================================================
# (2) WRONG-REDUCTION (the actual pre-patch bug) — reduce by the per-variable
# MAXIMUM instead of the total degree (this is the exact model_prepatch.py
# running-max loop). On any exponent vector whose largest single exponent is
# below min_degree but whose SUM reaches it (e.g. [2,1] at min_degree=3) the
# decision flips. The frozen postcondition Result()==(deg_sum>=min_degree)
# rejects it. This is the partial-domain attack grounded in the real bug.
# ===========================================================================
_MAX_IMPL = """    # PRE-PATCH (buggy): test the lower bound against the LARGEST single
    # per-variable exponent (max) rather than the total degree (sum).
    running = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        if powers[i - 1] >= running:
            running = powers[i - 1]
        i = i - 1
    return running >= min_degree"""

# We keep the gold loop body intact (so the invariant total==deg_sum(...) still
# holds and there is no spurious proof gap), and ONLY change the returned
# reduction to the running maximum. The impl region between '# impl-start' and
# '# impl-end' becomes the gold accumulator PLUS a running-max, returning max.
_wrong_max_comm = _swap(
    _BASE,
    _COMM_GOLD,
    _COMM_GOLD.replace(
        """    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree""",
        """    total = 0
""" + _MAX_IMPL,
    ),
)

_wrong_max_noncomm = _swap(
    _BASE,
    _NONCOMM_GOLD,
    _NONCOMM_GOLD.replace(
        """    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree""",
        """    total = 0
""" + _MAX_IMPL,
    ),
)


# ===========================================================================
# (3) PARTIAL-DOMAIN (drop-first) — stop the fold at i > 1, so powers[0] is
# never summed: Result() ends up driven by deg_sum(ToSeq(powers).drop(1)) >=
# min_degree, i.e. the total degree MINUS the first exponent. Diverges whenever
# the first exponent matters (e.g. powers=[3], min_degree=3: drop(1) sum is 0 <
# 3, but the true total degree is 3 >= 3). Rejected by the postcondition.
# ===========================================================================
_DROP_FIRST_IMPL = """    total = 0
    i = len(powers)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(1 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree  # never sums powers[0]: equals deg_sum(drop(1))"""

_partial_first_comm = _swap(
    _BASE,
    _COMM_GOLD,
    _COMM_GOLD.replace(
        """    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree""",
        _DROP_FIRST_IMPL,
    ),
)


# ===========================================================================
# (4) OFF-BY-ONE BOUNDARY (strict vs non-strict) — return total > min_degree
# instead of total >= min_degree. Correct on every input EXCEPT the boundary
# where the total degree exactly equals min_degree (the F2P case
# itermonomials([x,y],3,3) keeps x**2*y whose total degree is exactly 3). The
# frozen postcondition demands == (deg_sum >= min_degree), so the boundary makes
# it reject.
# ===========================================================================
_strict_comm = _swap(
    _BASE,
    _COMM_GOLD,
    _COMM_GOLD.replace(
        "    return total >= min_degree\n    # impl-end",
        "    return total > min_degree  # strict: drops the exact-equality boundary\n    # impl-end",
    ),
)


# ===========================================================================
# (5) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT, while
# KEEPING the BACKWARD loop and ALL gold invariants/framing Asserts (per pilot
# warnings #2/#3: a forward-append against the front-recursive deg_sum fold would
# need an unprovable deg_sum(a+b) lemma, so we do NOT flip the loop direction).
# The shape change is local-variable / statement-reorder only: the two framing
# Asserts are reordered, the read powers[i-1] is hoisted into a named local `e`,
# and the accumulator is written as `total = e + total`. The gold invariants are
# kept verbatim. Must verify; if it cannot => SPEC-TOO-STRONG.
# ===========================================================================
_RESHAPE_IMPL = """    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        e = powers[i - 1]
        total = e + total
        i = i - 1
    return total >= min_degree"""

_pos_ctrl_comm = _swap(
    _BASE,
    _COMM_GOLD,
    _COMM_GOLD.replace(
        """    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree""",
        _RESHAPE_IMPL,
    ),
)


# ===========================================================================
# (6) ADMISSIBILITY — the precondition must admit a normal F2P-shaped input.
# We BUILD a fresh exponent vector [2, 1] (the F2P discriminator: total degree
# 3) as a full-permission local, establish the callee's Requires on it
# (min_degree >= 0 and every element >= 0), and self-call keep_comm on that
# fresh input -- a representative legal call witnessing the precondition is
# satisfiable for a normal input, and checking the returned value matches the
# grounded oracle deg_sum on the probe. The gold body then runs UNCHANGED on
# `powers`, discharging this function's own postcondition. If this cannot verify
# => PRECOND-TOO-STRONG.
#
# NOTE (proof engineering): the self-call is made on a FRESH local probe, NOT on
# the function's own read-only parameter `powers`. A self-call keep_comm(powers,
# ...) on the parameter is rejected NOT by the precondition but by a Nagini
# framing limitation: ToSeq(powers) is not framed across a method call even when
# Acc(list_pred(powers),1/2) is retained continuously, so after such a call the
# post-loop fact `total == deg_sum(ToSeq(powers))` -- and hence the function's
# OWN postcondition Result()==(deg_sum(ToSeq(powers))>=min_degree) -- can no
# longer be re-discharged. The fresh-probe idiom (cf. django__django-10097
# admiss-selfcall) exercises precondition admissibility without dragging the
# parameter's un-framable ToSeq across the call.
# ===========================================================================
_ADMISS_IMPL = """    # admissibility: a fresh F2P-shaped input [2,1] (total degree 3) satisfies
    # the precondition and the self-call on it is legal -- the Requires admits a
    # normal input; the returned value matches the grounded oracle deg_sum.
    probe = [2, 1]  # type: List[int]
    Assert(probe[0] == 2 and probe[1] == 1)
    Assert(Forall(int, lambda j: (Implies(0 <= j and j < len(probe),
                                          probe[j] >= 0), [[probe[j]]])))
    _ok = keep_comm(probe, 0)
    Assert(_ok == (deg_sum(ToSeq(probe)) >= 0))
    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree"""

_admiss_comm = _swap(
    _BASE,
    _COMM_GOLD,
    _COMM_GOLD.replace(
        """    total = 0
    i = len(powers)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(0 <= i and i <= len(powers))
        Invariant(total == deg_sum(ToSeq(powers).drop(i)))
        # invariants-end
        Assert(ToSeq(powers).drop(i - 1)[0] == ToSeq(powers)[i - 1])
        Assert(ToSeq(powers).drop(i - 1).drop(1) == ToSeq(powers).drop(i))
        total = powers[i - 1] + total
        i = i - 1
    return total >= min_degree""",
        _ADMISS_IMPL,
    ),
)


SPEC_TESTS = [
    {
        "id": "frame-mut-comm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_comm,
        "refinement": (
            "powers[i-1]=powers[i-1] is a VALUE no-op, so a 'faithful' real patch "
            "that wrote back into the powers dict while computing sum(powers.values()) "
            "would still compute the identical total degree and could look correct on "
            "the F2P test_monomials assertions -- the value abstraction is blind to "
            "the write. The gold patch only READS powers.values() at the retention "
            "test (`sum(powers.values()) >= min_degree`); it never mutates the dict. "
            "A patch that mutated `powers` would corrupt the freshly-built per-"
            "candidate exponent dict and is not what the gold patch does, so it is "
            "unfaithful and must be rejected on permission grounds rather than admitted."
        ),
        "rationale": (
            "Rejection comes from the PERMISSION system: powers[i-1]=... needs full "
            "write permission to list_pred(powers), but the precondition/invariant "
            "grant only Acc(...,1/2). INSUFFICIENT PERMISSION, not a postcondition "
            "failure. (The #1 weakness class; a byte-fuzzer never constructs it.)"
        ),
    },
    {
        "id": "frame-mut-noncomm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_noncomm,
        "refinement": (
            "Identical to frame-mut-comm but on the second hunk (the non-commutative "
            "branch). The write powers[i-1]=powers[i-1] is a value no-op; a real patch "
            "mutating the exponent dict in the non-commutative branch would still pass "
            "the F2P value checks but is not what the gold patch does (it only reads "
            "powers.values()). Must be rejected on permission grounds."
        ),
        "rationale": (
            "Rejection from the permission system: assigning powers[i-1] needs full "
            "list_pred(powers) permission; the function holds only 1/2."
        ),
    },
    {
        "id": "wrong-max-comm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrong_max_comm,
        "refinement": (
            "This is the EXACT pre-patch bug: reduce by the largest single exponent "
            "(max(powers.values())) instead of the total degree (sum). The faithful "
            "real correspondent is the unpatched line `if max(powers.values()) >= "
            "min_degree`. On the F2P discriminator itermonomials([x,y],3,3) the term "
            "x**2*y has exponent vector [2,1] (total degree 3, max 2): the correct sum "
            "rule keeps it but the max rule drops it (2<3), so the produced set is "
            "{x**3, y**3} instead of {x**3, x**2*y, x*y**2, y**3}. test_monomials FAILS "
            "-- this is precisely the issue the gold patch fixes, so it does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Result()==(deg_sum(ToSeq(powers))>="
            "min_degree): returning running(=max)>=min_degree differs from sum>="
            "min_degree on any vector with max<min_degree<=sum (e.g. [2,1] at 3)."
        ),
    },
    {
        "id": "wrong-max-noncomm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrong_max_noncomm,
        "refinement": (
            "The same pre-patch max reduction in the non-commutative branch (hunk 2). "
            "The F2P discriminator itermonomials([i,j,k],2,2) over non-commuting "
            "generators contains terms like i*j (exponent vector with two 1s: total "
            "degree 2, max 1) that the max rule drops (1<2) but the sum rule keeps; "
            "test_monomials FAILS. This is the reported bug, so it does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Result()==(deg_sum(ToSeq(powers))>="
            "min_degree): max-reduction != sum-reduction on vectors where the sum "
            "reaches the threshold but no single exponent does."
        ),
    },
    {
        "id": "partial-first-comm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _partial_first_comm,
        "refinement": (
            "Stopping the fold at i>1 leaves total == deg_sum(ToSeq(powers).drop(1)): "
            "the FIRST exponent powers[0] is never added. The faithful real patch would "
            "be `sum(list(powers.values())[1:]) >= min_degree` -- it omits the first "
            "variable's exponent from the total degree. On a single-variable candidate "
            "(e.g. x**3 over [x], min_degree 3) the true total degree is 3 but the "
            "dropped-first sum is 0, so x**3 is wrongly dropped; more generally any "
            "candidate whose first counted variable carries the decisive degree is "
            "misclassified. test_monomials would FAIL, so the patch does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition: the returned value equals deg_sum over "
            "the tail drop(1), not the full sequence, so the equality "
            "Result()==(deg_sum(ToSeq(powers))>=min_degree) fails whenever the first "
            "exponent changes the comparison's outcome."
        ),
    },
    {
        "id": "strict-boundary-comm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _strict_comm,
        "refinement": (
            "Returning total > min_degree (strict) instead of total >= min_degree "
            "corresponds to the off-by-one patch `sum(powers.values()) > min_degree`. "
            "It is correct on every input EXCEPT the exact-equality boundary, which is "
            "the heart of the F2P case: itermonomials([x,y],3,3) must retain x**2*y "
            "(total degree exactly 3 == min_degree 3) and x**3, y**3, x*y**2. With the "
            "strict test every term whose total degree equals min_degree is dropped, so "
            "the produced set is empty and test_monomials FAILS -- it does NOT resolve."
        ),
        "rationale": (
            "Rejection from the postcondition Result()==(deg_sum(ToSeq(powers))>="
            "min_degree): a strict comparison disagrees with >= exactly when "
            "deg_sum == min_degree (the F2P boundary), so the equality fails."
        ),
    },
    {
        "id": "pos-control-reshape-comm",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl_comm,
        "rationale": (
            "A structurally-different but CORRECT impl: the two framing Asserts are "
            "reordered and the read powers[i-1] is hoisted into a named local `e`, "
            "with the accumulator written as `total = e + total`. The BACKWARD loop "
            "and ALL gold invariants/framing pins are kept verbatim (no loop-direction "
            "flip -- per pilot warning #3 a forward-append against the front-recursive "
            "deg_sum fold would need an unprovable deg_sum(a+b) lemma). It MUST verify; "
            "if it cannot, the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-comm-selfcall",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_comm,
        "rationale": (
            "The precondition Acc(list_pred(powers),1/2) + min_degree>=0 + every "
            "powers[i]>=0 must admit a normal F2P-shaped input. A fresh exponent "
            "vector [2,1] (the F2P discriminator: total degree 3) is built as a "
            "full-permission local, satisfies the callee's Requires (min_degree>=0, "
            "every element>=0), and the self-call keep_comm([2,1],0) is legal -- a "
            "representative legal call witnessing the precondition is satisfiable; the "
            "returned value matches the grounded oracle deg_sum(ToSeq(probe))>=0. The "
            "gold body then runs unchanged on `powers`, discharging the function's own "
            "postcondition. If this cannot verify, the precondition is PRECOND-TOO-"
            "STRONG. The probe is a FRESH local, not the read-only parameter: a "
            "self-call on `powers` is blocked by a Nagini framing limitation (ToSeq "
            "is not framed across a call even with retained 1/2 perm), not by the "
            "precondition, so it would be a false PRECOND-TOO-STRONG signal."
        ),
    },
]


# No @ContractOnly axiom and no A-reference deep model in this bundle: the only
# changed operation (the reduction over the exponent vector) is modeled DEEPLY by
# the front-recursive @Pure fold deg_sum, consumed directly by the postcondition
# and computed by the impl loop (refinement.md "No kind-3"; mapping.md §3 "None").
# deg_sum's fidelity to sum(...) and the real gold-patched itermonomials are
# already exercised by axiom_check.py (parts 1 and 2). There is therefore no
# axiom soundness / containment obligation here.
AXIOM_TESTS = []
