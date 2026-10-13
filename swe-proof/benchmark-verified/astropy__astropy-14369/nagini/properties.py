# properties.py — PBT falsification battery for astropy__astropy-14369.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a FULL model.py source that shares the frozen spec
# (markers.same_spec) and edits ONLY the impl region (# impl-start..# impl-end);
# the runner verifies it with Nagini on the host and checks the expect outcome.
#
# DEFENDED SURFACE (what this spec pins, reasoned from model.py):
#   reduce_division_chain(powers: List[int], leading: bool) -> List[int]
#     Requires Acc(list_pred(powers), 1/2)       <-- READ-ONLY input (half perm)
#     Requires len(powers) >= 1
#     Ensures  Acc(list_pred(powers), 1/2)        <-- caller keeps its half (frame)
#     Ensures  Acc(list_pred(Result()))
#     Ensures  len(Result()) == len(powers)       <-- one exponent per operand
#     Ensures  Forall k. 0<=k<len(Result()) ==>
#                  Result()[k] == chain_power(k, powers[k], leading)
#   chain_power(i, power, leading) = power if (i==0 and not leading) else -power
#   (@Pure, GROUNDED in the args; the left-grouped division rule, A-reference
#   validated by G-AX/axiom_check.py against the real callee.)
#
# The load-bearing clause is the element-wise Forall pinning EVERY position to
# chain_power(k, powers[k], leading). Because chain_power is a pure function of
# (position, that operand's own exponent, the leading flag) — fully unfolded, not
# an opaque answer-key over the Result — there is no "wrong echo that verifies":
# ungrounded-oracle echo is N/A here (see assessment).
# The attacks that DO bite this surface: frame-mutation of the read-only
# `powers`, the pre-patch alternating rival (the actual differential), rivals
# that collapse an operand's own exponent to a bare unit sign, rivals that
# ignore the leading flag, and partial-domain rivals that pin all but one
# sub-domain.

from pathlib import Path

INSTANCE = "astropy__astropy-14369"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The GOLD impl region body, verbatim (between # impl-start and # impl-end).
# Every variant is produced by _swap-ing a unique fragment of THIS text, so the
# edit is guaranteed to land inside the impl region (same_spec preserved).
_GOLD_IMPL = '''    result = []  # type: List[int]
    n = len(powers)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == n - i)
        # result currently holds the exponents of chain positions i .. n-1.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < n - i,
                                                  result[k] == chain_power(i + k, powers[i + k], leading)),
                                          [[result[k]]])))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        old = result
        q = powers[i - 1]
        if i - 1 == 0 and not leading:
            # combined_units seed: the leading unit_expression keeps its own
            # exponent.
            result = [q] + result
        else:
            # combined_units DIVISION unit_expression: the accumulated left
            # group divided by the next single operand -> that operand's own
            # exponent is negated exactly once.
            result = [-q] + result
        # The new head is the exponent of chain position i-1.
        Assert(result[0] == chain_power(i - 1, powers[i - 1], leading))
        Assert(ToSeq(result).drop(1) == ToSeq(old))
        Assert(Forall(int, lambda k: (Implies(1 <= k and k < len(result),
                                              result[k] == old[k - 1]),
                                       [[result[k]]])))
        i = i - 1
    Assert(i == 0)
    Assert(len(result) == n)
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < n,
                                          result[k] == chain_power(k, powers[k], leading)),
                                  [[result[k]]])))
    return result'''

# Sanity: the gold impl text must appear verbatim in model.py.
assert _GOLD_IMPL in _BASE, "gold impl region drifted from model.py"


# ---------------------------------------------------------------------------
# (1) POSITIVE CONTROL (soundness) — a structurally-DIFFERENT correct impl.
#     The gold folds BACKWARD (i: n -> 0, prepend one operand per step). This
#     control folds FORWARD (i: 0 -> n, append), with the per-element loop
#     invariant Forall k<i. result[k]==chain_power(k,powers[k],leading).
#     chain_power is NOT a fold (it is the closed form keep-head/negate-rest),
#     so each element is pinned independently and the append needs NO
#     f(a+b)==f(a)+f(b) lemma (directive 3 is satisfied: this is not
#     forward-append against a front-recursive fold). All gold proof
#     obligations the loop still needs are KEPT (length, per-element pin, the
#     head branch). The only proof the append needs is the prefix-preservation
#     bridge (ToSeq(old + [x]) == ToSeq(old) ++ <x>: old[k] unchanged for k<i),
#     supplied in-region exactly like the gold's prepend bridge.
#     MUST verify; else SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_IMPL_POS = '''    result = []  # type: List[int]
    n = len(powers)
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == i)
        # result currently holds the exponents of chain positions 0 .. i-1.
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                                  result[k] == chain_power(k, powers[k], leading)),
                                          [[result[k]]])))
        # TERMINATION MEASURE, derived from THIS loop's own shape. The gold folds
        # BACKWARD (`while i > 0`, i falling to 0), so its measure is the
        # down-counter `i + 1`. This control folds FORWARD (`while i < n`, i
        # rising from 0), where `i + 1` INCREASES; the bound on the remaining
        # iterations is `n - i + 1` instead. It decreases by exactly 1 per step
        # because i rises by 1 and `n` is bound once before the loop and never
        # reassigned (`len(powers) == n` above pins it, and powers is read-only
        # at Acc(...,1/2), so len(powers) cannot move either). It stays >= 1
        # while the loop runs because the `i <= n` invariant holds; the `+ 1` is
        # what makes the LAST iteration (i == n - 1, zero iterations left)
        # satisfiable, since MustTerminate(0) is unsatisfiable.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        old = result
        if i == 0 and not leading:
            result = result + [powers[i]]
        else:
            result = result + [-powers[i]]
        # APPEND-PRESERVATION bridge: ToSeq(old + [x]) == ToSeq(old) ++ <x>, so
        # the old prefix elements are unchanged (re-establishing the per-element
        # pin for k < i) and the freshly appended tail is at position i. This
        # mirrors the gold's prepend bridge (result[k]==old[k-1]); it is NOT an
        # f(a+b)==f(a)+f(b) fold-associativity lemma — chain_power is the closed
        # form, so each position is pinned independently. Same_spec preserved.
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < i,
                                              result[k] == old[k]),
                                       [[result[k]]])))
        # The freshly appended tail element is position i.
        Assert(result[i] == chain_power(i, powers[i], leading))
        i = i + 1
    Assert(i == n)
    Assert(len(result) == n)
    Assert(Forall(int, lambda k: (Implies(0 <= k and k < n,
                                          result[k] == chain_power(k, powers[k], leading)),
                                  [[result[k]]])))
    return result'''


# ---------------------------------------------------------------------------
# (2) ADMISSIBILITY — the precondition must accept a normal F2P-shaped input.
#     Keeps the gold impl verbatim but asserts, at entry, the facts the Requires
#     promises (len>=1, the read permission Acc(...,1/2)) and that the loop bound
#     is well-formed for a multi-operand chain (n-1 >= 0 once n>=1). If a
#     legitimate F2P-shaped input could not establish Requires this would fail =>
#     PRECOND-TOO-STRONG. Must VERIFY.
# ---------------------------------------------------------------------------
_IMPL_ADMISS = _swap(
    _GOLD_IMPL,
    "    result = []  # type: List[int]\n    n = len(powers)\n",
    "    result = []  # type: List[int]\n"
    "    # ADMISSIBILITY: a normal F2P-shaped chain (4 operands, the last one\n"
    "    # carrying its own exponent 2) is in-domain; Requires must hold for it.\n"
    "    Assert(len(powers) >= 1)\n"
    "    Assert(Acc(list_pred(powers), 1 / 2))\n"
    "    n = len(powers)\n"
    "    Assert(n - 1 >= 0)\n",
)


# ---------------------------------------------------------------------------
# (3) FRAME-MUTATION (uniqueness) — write to the read-only half-perm `powers`.
#     powers is Requires(Acc(list_pred(powers), 1/2)): only HALF permission, so
#     any WRITE must fail for INSUFFICIENT PERMISSION. The gold
#     invariants/postcond are kept VERBATIM so the rejection is attributable
#     solely to the write. The write stores the SAME value back
#     (powers[i-1] = powers[i-1]); even a no-op store needs full permission.
#     MUST REJECT.
# ---------------------------------------------------------------------------
_IMPL_FRAME = _swap(
    _GOLD_IMPL,
    "        old = result\n",
    "        old = result\n"
    "        # FRAME MUTATION: write back to the read-only half-permission input.\n"
    "        powers[i - 1] = powers[i - 1]\n",
)


# ---------------------------------------------------------------------------
# (4) PRE-PATCH ALTERNATING rival (uniqueness — the ACTUAL differential).
#     The pre-patch right-grouped reduction gives the operand at position i its
#     own exponent times (-1)**i (negated once more when the chain opens with
#     the division operator). This is the behaviour the issue reports as
#     jumbled. It agrees with gold at i=0,1 and DIVERGES at every even i>=2.
#     The element-wise postcondition demands -powers[k] for every k>=1, so this
#     must fail the Forall at the first even position >=2. MUST REJECT.
# ---------------------------------------------------------------------------
_IMPL_ALT = '''    result = []  # type: List[int]
    n = len(powers)
    i = n
    # sign chain position i-1 receives under right grouping: (-1)**(i-1),
    # negated once more when the chain opens with the division operator.
    s = 1 if (n % 2 == 1) else -1
    if leading:
        s = -s
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == n - i)
        Invariant(s == 1 or s == -1)
        # Same backward shape as the gold (`while i > 0`, i falling by 1), so the
        # same down-counter measure. It is present so this rival is rejected for
        # the FUNCTIONAL reason the rationale below names (the element-wise
        # postcondition) rather than for a missing obligation.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        result = [s * powers[i - 1]] + result
        s = -s
        i = i - 1
    Assert(i == 0)
    Assert(len(result) == n)
    return result'''


# ---------------------------------------------------------------------------
# (5) PARTIAL-DOMAIN — correct on every position EXCEPT the LAST operand, which
#     it leaves with its exponent un-negated. Agrees with gold on the head and
#     all interior operands, so it passes the easy sub-domain but mis-signs the
#     trailing operand of every chain of length >= 2. The element-wise
#     postcondition pins position n-1 to -powers[n-1] (for n>=2), so this must
#     fail. MUST REJECT.
# ---------------------------------------------------------------------------
_IMPL_PARTIAL = '''    result = []  # type: List[int]
    n = len(powers)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == n - i)
        # Same backward shape as the gold; measure present so the rejection is on
        # the element-wise postcondition at position n-1, not on the obligation.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if i - 1 == 0 and not leading:
            result = [powers[i - 1]] + result
        elif i == n:
            # PARTIAL-DOMAIN BUG: the last operand (chain position n-1, first
            # prepended) keeps its exponent instead of having it negated.
            result = [powers[i - 1]] + result
        else:
            result = [-powers[i - 1]] + result
        i = i - 1
    Assert(i == 0)
    Assert(len(result) == n)
    return result'''


# ---------------------------------------------------------------------------
# (6) ALL-NEGATED rival (uniqueness — drops the head special case).
#     Negates EVERY operand's exponent, including the head's. Agrees with gold
#     on all non-head positions but mis-signs position 0 of a chain that does
#     not open with the division operator (there chain_power(0,q,False)=+q).
#     MUST REJECT.
# ---------------------------------------------------------------------------
_IMPL_ALLNEG = '''    result = []  # type: List[int]
    n = len(powers)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == n - i)
        # Same backward shape as the gold; measure present so the rejection is on
        # the element-wise postcondition at position 0, not on the obligation.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # ALL-NEGATED BUG: every operand (even the head) has its exponent negated.
        result = [-powers[i - 1]] + result
        i = i - 1
    Assert(i == 0)
    Assert(len(result) == n)
    return result'''


# ---------------------------------------------------------------------------
# (7) UNIT-MAGNITUDE rival (uniqueness — collapses each operand's OWN exponent
#     to a bare +1/-1 sign). Emits +1 for the head and -1 for every following
#     operand, DISCARDING powers[k]'s magnitude. It coincides with gold exactly
#     on chains whose every operand has intrinsic exponent 1, so it passes that
#     whole sub-domain, and mis-scales every operand written with an exponent of
#     its own (e.g. a trailing squared operand gets -1 where -2 is required).
#     The element-wise postcondition pins position k to chain_power(k,powers[k],
#     leading), which is +/- powers[k], not +/- 1. MUST REJECT.
# ---------------------------------------------------------------------------
_IMPL_UNITMAG = '''    result = []  # type: List[int]
    n = len(powers)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == n - i)
        # Same backward shape as the gold; measure present so the rejection is on
        # the element-wise postcondition (magnitude), not on the obligation.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # UNIT-MAGNITUDE BUG: the operand's OWN exponent is discarded and only a
        # bare +1 / -1 sign is emitted.
        if i - 1 == 0 and not leading:
            result = [1] + result
        else:
            result = [-1] + result
        i = i - 1
    Assert(i == 0)
    Assert(len(result) == n)
    return result'''


# ---------------------------------------------------------------------------
# (8) IGNORE-LEADING rival (uniqueness — drops the leading-operator case).
#     Always keeps the head operand's exponent positive, ignoring `leading`. It
#     coincides with gold exactly on chains that do not open with the division
#     operator, so it passes that whole sub-domain, and mis-signs position 0 of
#     every chain that DOES open with it (there the head is divided in too, so
#     chain_power(0,q,True) = -q). MUST REJECT.
# ---------------------------------------------------------------------------
_IMPL_NOLEAD = '''    result = []  # type: List[int]
    n = len(powers)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(powers), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(len(powers) == n)
        Invariant(len(result) == n - i)
        # Same backward shape as the gold; measure present so the rejection is on
        # the element-wise postcondition at position 0, not on the obligation.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # IGNORE-LEADING BUG: the head keeps its exponent even when the chain
        # opens with the division operator (where the head is divided in too).
        if i - 1 == 0:
            result = [powers[i - 1]] + result
        else:
            result = [-powers[i - 1]] + result
        i = i - 1
    Assert(i == 0)
    Assert(len(result) == n)
    return result'''


def _module(impl_body):
    return _swap(_BASE, _GOLD_IMPL, impl_body)


SPEC_TESTS = [
    {
        "id": "pos-control-forward-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _module(_IMPL_POS),
        "rationale": "Structurally-different CORRECT impl: forward append fold "
                     "(i:0->n) vs the gold backward prepend fold. chain_power is "
                     "the closed form keep-head/negate-rest (not a recursive "
                     "fold), so the per-element invariant Forall k<i. "
                     "result[k]==chain_power(k,powers[k],leading) auto-discharges "
                     "the append with no associativity lemma (directive 3 "
                     "satisfied). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _module(_IMPL_ADMISS),
        "rationale": "Gold impl + entry asserts that the Requires facts (len>=1, "
                     "Acc(powers,1/2)) hold and n-1>=0 for a normal multi-operand "
                     "chain whose trailing operand carries its own exponent 2. "
                     "The precondition must admit such an input. Must verify, "
                     "else PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-write-powers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_IMPL_FRAME),
        "refinement": "A faithful real patch that WRITES to the operand chain it "
                      "is handed (the parser's p[1]/p[3] tokens / the caller's "
                      "operand objects) would mutate caller-shared parse state; "
                      "the real reduction combines operands without overwriting "
                      "them and the F2P tests reuse the parsed result, so an "
                      "in-place-mutating patch does not faithfully resolve. Even a "
                      "same-value store needs full permission, which the function "
                      "does not hold.",
        "rationale": "Rejection comes from the PERMISSION SYSTEM: powers is held "
                     "at Acc(list_pred(powers),1/2); the write "
                     "powers[i-1]=powers[i-1] requires full permission => "
                     "insufficient-permission failure. Gold invariants/postcond "
                     "kept verbatim so the reject is attributable to the write. If "
                     "it verified => SPEC-TOO-WEAK (frame leak). MANDATORY "
                     "read-only-input class.",
    },
    {
        "id": "prepatch-alternating-parity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_IMPL_ALT),
        "refinement": "This IS the pre-patch (right-grouped) behaviour: the "
                      "operand at position i gets its own exponent times "
                      "(-1)**i. It is exactly the un-fixed reduction the issue "
                      "reports as 'jumbled' — on a 3-operand chain the third "
                      "operand flips back to positive, which is the divergence "
                      "the F2P data exhibits, so a real patch with this behaviour "
                      "does NOT resolve.",
        "rationale": "Rejection comes from the element-wise postcondition "
                     "Forall k. Result()[k]==chain_power(k,powers[k],leading): it "
                     "demands -powers[k] for every k>=1, but parity gives "
                     "+powers[k] at the first even position >=2. This is the "
                     "G-DIFF discriminating clause. If it verified => "
                     "SPEC-TOO-WEAK.",
    },
    {
        "id": "partial-domain-last-operand",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_IMPL_PARTIAL),
        "refinement": "Correct on the head and all interior operands, but the LAST "
                      "operand of every length>=2 chain keeps its exponent instead "
                      "of having it negated. A real patch with this behaviour "
                      "leaves the trailing operand of the F2P chains on the wrong "
                      "side of the division, so they do NOT resolve.",
        "rationale": "Rejection comes from the element-wise postcondition at "
                     "position n-1: chain_power(n-1,powers[n-1],leading) = "
                     "-powers[n-1] for n>=2, but this impl puts +powers[n-1] "
                     "there. A near-miss that pins all-but-one position; if it "
                     "verified => SPEC-TOO-WEAK (partial-domain leak).",
    },
    {
        "id": "all-negated-head-flip",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_IMPL_ALLNEG),
        "refinement": "Drops the leading-operand special case: every operand's "
                      "exponent is negated. A real patch that negates the head "
                      "operand puts the leading quantity of every chain in the "
                      "denominator, so the F2P chains do NOT resolve.",
        "rationale": "Rejection comes from the element-wise postcondition at "
                     "position 0: chain_power(0,powers[0],False)=+powers[0], but "
                     "this impl puts -powers[0] there. Supporting near-miss to the "
                     "partial-domain attack on the OTHER boundary (the head). If "
                     "it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "unit-magnitude-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_IMPL_UNITMAG),
        "refinement": "Emits a bare +1/-1 per position, discarding each operand's "
                      "OWN exponent. It is indistinguishable from gold on chains "
                      "whose operands all have intrinsic exponent 1, but a real "
                      "reduction with this behaviour would turn an operand written "
                      "with a squared exponent into a first-power one — exactly "
                      "the F2P chain whose trailing operand carries its own "
                      "exponent 2 (expected magnitude 2, this yields 1), so it "
                      "does NOT resolve.",
        "rationale": "Rejection comes from the element-wise postcondition: it pins "
                     "position k to chain_power(k,powers[k],leading), i.e. "
                     "+/-powers[k], not +/-1. This is the sub-domain rival the "
                     "OLD sign-only spec could not sense at all; it must fail "
                     "now. If it verified => SPEC-TOO-WEAK (magnitude leak).",
    },
    {
        "id": "ignore-leading-operator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_IMPL_NOLEAD),
        "refinement": "Ignores the `leading` flag and always keeps the head "
                      "operand's exponent positive. Indistinguishable from gold on "
                      "chains that do not open with the division operator, but a "
                      "real reduction with this behaviour reads a chain that opens "
                      "with the division operator as if its first operand were a "
                      "numerator — the single-operand F2P case of that form "
                      "expects the reciprocal, so it does NOT resolve.",
        "rationale": "Rejection comes from the element-wise postcondition at "
                     "position 0 when leading holds: chain_power(0,powers[0],True) "
                     "= -powers[0], but this impl puts +powers[0] there. The "
                     "second sub-domain rival the OLD spec could not sense. If it "
                     "verified => SPEC-TOO-WEAK (leading-operator leak).",
    },
]


# No @ContractOnly axioms in this bundle (meta.axioms == []); the only deep-model
# entry is the A-reference chain_power, validated by G-AX/axiom_check.py against
# the real patched callee. That executable soundness/containment check already
# lives in axiom_check.py and is exercised by G-AX in Docker; there is nothing
# for the AXIOM lane to add here.
AXIOM_TESTS = []
