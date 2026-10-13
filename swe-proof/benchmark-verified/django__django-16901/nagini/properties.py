# properties.py — PBT falsification battery for django__django-16901. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` — which INCLUDES the nested invariants
# region — is edited; the spec view is never touched), checked by Nagini verify +
# markers.same_spec.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   xor_fallback_matches(operands: List[int]) -> bool
#   Models the gold XOR-fallback branch of WhereNode.as_sql for backends without
#   native XOR. The gold patch re-expresses `a XOR b XOR c XOR ...` as
#     (a OR b OR c OR ...) AND MOD(a + b + c + ..., 2) == 1        # >2 operands
#     (a OR b OR c OR ...) AND     (a + b + c + ...) == 1          # <=2 operands
#   i.e. the n-ary XOR is true iff an ODD number of operands are true. The pre-patch
#   fallback used `(... ) == 1` ("exactly one") for ALL operand counts; the gold
#   inserts `if len(self.children) > 2: rhs_sum = Mod(rhs_sum, 2)`. The carrier is a
#   List[int] of per-operand 1/0 truth values; the spec is over PSeq[int] via ToSeq.
#
#   PRECONDITION:
#     (P1) Requires(Acc(list_pred(operands), 1/2))   # HALF permission => READ-ONLY
#     (P2) Requires(MustTerminate(2))                # TOTAL correctness: must answer
#   POSTCONDITION (three clauses; one framing/permission + two LOAD-BEARING):
#     (Q1) Ensures(Acc(list_pred(operands), 1/2))        # returns the read permission
#     (Q2) Ensures(Result() == xor_holds(ToSeq(operands)))
#            -- result == (OR of operands) AND (derived_count == 1), where
#               derived_count = count_true % 2 for >2 operands else count_true.
#     (Q3) Ensures(Result() == (count_true(ToSeq(operands)) % 2 == 1))
#            -- result == "an ODD number of operands are true" (the issue's demand,
#               and the F2P oracle in spec form).
#   Q2 and Q3 are mutually equivalent and TOGETHER pin the result to the exact parity
#   semantics on EVERY operand count. There is no slack: a rival that diverges on ANY
#   assignment (esp. >2 operands, where parity != exactly-one) fails Q2 and Q3.
#
# FRAME-MUTATION lane is MANDATORY: `operands` is Acc(list_pred(operands),1/2)
#   (read-only). A rival that WRITES it must be REJECTED for INSUFFICIENT PERMISSION.
#   Byte-fuzzers never think to mutate the input; this is the #1 weakness class. The
#   real gold branch only READS self.children (it builds NEW SQL nodes — Case/When,
#   Mod, Exact, OR/AND — over them); it never mutates the children list. Any write to
#   the operand carrier would diverge from the read-only gold and corrupt a shared
#   WhereNode child list.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q2/Q3 are pinned to xor_holds /
#   count_true, which are @Pure FRONT-RECURSIVE FOLDS fully unfolded over the input
#   carrier `operands` (no @ContractOnly axiom, no opaque answer-key, no exact marker):
#   the pure region COMPUTES the truth value from the operand list, it does not assert
#   an answer. count_true is `sum of per-operand 1/0`, any_true is its `>= 1`,
#   derived_count is the len-guarded parity, xor_holds their conjunction — every value
#   is a function of the args, fully unfolded. There is no value an echo could carry
#   that satisfies Q2/Q3 yet is wrong: the unique satisfier IS the grounded parity
#   decision. So the honest control is the cheapest faithful impl that computes that
#   decision (the positive control below), not a wrong echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: xor_fallback_matches returns a bool and has NO raise
#   path and NO side effect other than reading the (read-only) input — the value
#   abstraction (the returned bool) captures the entire observable behaviour EXCEPT
#   for termination: Nagini is a partial-correctness verifier by default, so a rival
#   whose loop never exits satisfies every Ensures vacuously (this was the audit's P1
#   witness — a same-spec never-terminating loop VERIFIED under the pre-fix contract).
#   The contract now carries Requires(MustTerminate(2)) (P2) and the gold loop
#   discharges it with the strictly-decreasing measure Invariant(MustTerminate(i)).
#   The weak-nonterm rival below pins the rejection.
#
# PARTIAL-DOMAIN lane: heavily exercised — this is the heart of the instance. The
#   discriminating content of the gold change is the parity reduction, which only
#   diverges from the pre-patch "exactly one" on >2 operands (where the true count can
#   exceed 2). Rivals correct on the <=2-operand sub-domain (and on most >2-operand
#   assignments) but wrong on the discriminating sub-domain:
#     - weak-no-mod   : drops the Mod entirely (rhs = total always) — the LITERAL
#                       pre-patch fallback (model_prepatch.py). Correct for <=2 operands
#                       but on 3 true operands (the F2P uses 5) returns False while
#                       xor_holds/parity demand True. Fails Q2/Q3.
#     - weak-mod3     : reduces modulo 3 instead of 2 — agrees on small counts but on 3
#                       true operands gives 3%3==0 (False) vs parity True. Fails Q2/Q3.
#     - weak-guard-ge3-only: applies the parity but with a guard that mis-handles a
#                       boundary count is NOT a divergence (count<=2 coincidence), so
#                       instead weak-eq-count pins exactly-one universally (== weak-no-mod
#                       restated via `total == 1`). [folded into weak-no-mod]
#
# POSITIVE CONTROL (soundness): a structurally-different but CORRECT impl that keeps
#   the gold BACKWARD loop and EVERY framing assert/invariant verbatim (directive 2/3:
#   the folds count_true/any_true are FRONT-recursive, so a forward-append loop would
#   need an f(a+b)==f(a)+f(b) lemma the verifier can't auto-discharge — we therefore
#   reorder the final parity branch and commute the final `and`, a pure local reshape
#   that keeps the gold proof valid).
#
# ADMISSIBILITY: a positive control that, under the half-permission, FIRST asserts the
#   reads a normal F2P-shaped assignment needs are admitted, then runs the gold body.
#
# AXIOM lane: meta.axioms == [] AND deep_model_references is "deep model (NOT an axiom,
#   NOT an A-reference callee)" — the changed op (Mod parity) is integer arithmetic
#   modelled DEEPLY with native Nagini %/+/==/and/or, never axiomatized (directive 7).
#   There is no @ContractOnly axiom and no A-reference deep model to validate against a
#   real library callee, so AXIOM_TESTS = [] (the single external soundness link is
#   already checked by axiom_check.py / G-AX over 208191 assignments).
from pathlib import Path

INSTANCE = "django__django-16901"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`, INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms/pure/pre-/post-conditions regions + the function signature). same_spec is
# computed over the spec_view, which elides every impl region (and nested invariants),
# so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    total = 0
    any_t = False
    i = len(operands)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(operands), 1 / 2))
        Invariant(0 <= i and i <= len(operands))
        Invariant(total == count_true(ToSeq(operands).drop(i)))
        Invariant(any_t == any_true(ToSeq(operands).drop(i)))
        # The loop consumes the termination obligation: i is the strictly
        # decreasing, bounded-below measure.
        Invariant(MustTerminate(i))
        # invariants-end
        c = operands[i - 1]
        Assert(ToSeq(operands).drop(i - 1)[0] == c)
        Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))
        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.
        contribution = 1 if c == 1 else 0
        total = contribution + total
        any_t = (c == 1) or any_t
        i = i - 1
    Assert(ToSeq(operands).drop(0) == ToSeq(operands))
    # rhs_sum derivation: the parity is taken once the operand count exceeds two.
    if len(operands) > 2:
        rhs = total % 2
    else:
        rhs = total
    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.
    return any_t and rhs == 1"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-reorder-commute: structurally DIFFERENT but behaviourally identical. The gold
# BACKWARD loop, its four invariants, and BOTH per-step `.drop` framing asserts are
# kept VERBATIM (directive 2: keep every proof obligation; directive 3: NO
# forward-append against the front-recursive count_true/any_true folds). Only the tail
# is reshaped: the parity branch guard is COMPLEMENTED (`if len(operands) <= 2: rhs =
# total else: rhs = total % 2` — semantically identical to the gold `> 2` form), and
# the final conjunction is COMMUTED (`rhs == 1 and any_t` instead of `any_t and rhs ==
# 1`). Both are pure source reshapes with identical semantics. If it FAILS =>
# SPEC-TOO-STRONG (a faithful, structurally-different correct impl is rejected).
_POS = _IMPL.replace(
    "    # rhs_sum derivation: the parity is taken once the operand count exceeds two.\n"
    "    if len(operands) > 2:\n"
    "        rhs = total % 2\n"
    "    else:\n"
    "        rhs = total\n"
    "    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.\n"
    "    return any_t and rhs == 1",
    "    # Branch reorder (<=2 complement of >2) + commuted final conjunction.\n"
    "    if len(operands) <= 2:\n"
    "        rhs = total\n"
    "    else:\n"
    "        rhs = total % 2\n"
    "    return rhs == 1 and any_t",
)
assert _POS != _IMPL, "pos-reorder-commute did not rewrite"


# admiss-reads: an admissibility positive control. The precondition is the single
# half-permission Acc(list_pred(operands),1/2). This control keeps the gold impl
# VERBATIM but FIRST asserts, under that half-permission, that the reads a normal
# F2P-shaped operand assignment needs are admitted — the length is readable and (when
# the assignment is non-empty, e.g. the F2P's 5-operand row) the first element is
# readable. No write, so no extra permission demand. If the precondition could not
# admit a legitimate operand list, this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal (possibly empty) operand assignment is in-domain;\n"
    "    # the half-permission admits reading the length and elements (no write).\n"
    "    Assert(len(operands) >= 0)\n"
    "    if len(operands) > 0:\n"
    "        Assert(operands[0] == operands[0])   # read admitted under Acc(...,1/2)\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — `operands` is Acc(list_pred(operands),1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only input: operands[0] = operands[0]. A no-op store, but a STORE — it demands
# FULL write permission on `operands`, which the caller granted only at 1/2. The
# verifier must reject for insufficient permission. The store is guarded by len>0 so it
# is reachable on the F2P's 5-operand row.
_FRAME_MUT = (
    "    if len(operands) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        operands[0] = operands[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-no-mod: PARTIAL-DOMAIN + the LITERAL pre-patch behaviour (model_prepatch.py).
# Keeps the gold backward loop / invariants / asserts verbatim, but DROPS the parity
# reduction: `rhs = total` unconditionally (the pre-patch `Exact(1, rhs_sum)` straight
# from the raw sum, no Mod). Correct for <=2 operands (count<=2 coincidence) but WRONG
# the moment the true count exceeds 2: on 3 true operands rhs=3, `rhs == 1` is False,
# yet xor_holds / parity demand True.
_WEAK_NO_MOD = _IMPL.replace(
    "    # rhs_sum derivation: the parity is taken once the operand count exceeds two.\n"
    "    if len(operands) > 2:\n"
    "        rhs = total % 2\n"
    "    else:\n"
    "        rhs = total\n"
    "    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.\n"
    "    return any_t and rhs == 1",
    "    # PRE-PATCH fallback: no Mod, raw sum compared to one ('exactly one').\n"
    "    rhs = total\n"
    "    return any_t and rhs == 1",
)
assert _WEAK_NO_MOD != _IMPL, "weak-no-mod did not rewrite"

# weak-mod3: PARTIAL-DOMAIN. Reduces modulo 3 instead of 2 for >2 operands. Agrees with
# parity on counts 0,1,2 (and trivially the OR), but DIVERGES the moment the true count
# is a positive multiple of 3 or otherwise differs in parity: on 3 true operands
# rhs = 3 % 3 == 0, `rhs == 1` is False, yet xor_holds / parity demand True. (Also
# wrong on 5 true operands: 5%3==2 != 1 False vs parity 5%2==1 True.)
_WEAK_MOD3 = _IMPL.replace(
    "    if len(operands) > 2:\n"
    "        rhs = total % 2\n",
    "    if len(operands) > 2:\n"
    "        rhs = total % 3\n",
)
assert _WEAK_MOD3 != _IMPL, "weak-mod3 did not rewrite"

# weak-eq-true: PARTIAL-DOMAIN / value-mask. Returns `any_t and total == 1` directly —
# i.e. it tests "exactly one true operand" against the RAW count for ALL operand counts
# (equivalent semantics to weak-no-mod, but spelled as the bare exactly-one predicate
# with the parity branch deleted entirely). Correct for <=2 operands, wrong on 3 true
# (total==3, `total == 1` False, parity True). A second, independent expression of the
# exactly-one bug to ensure the spec rejects it however it is phrased.
# weak-nonterm: CONTROL-FLOW-EFFECT / VACUITY — the audit's P1 witness. The loop
# body is emptied of ALL progress (i is never decremented, total/any_t never change),
# so `while i > 0` never exits on any non-empty operand list; every Ensures then
# holds vacuously on that path (no normal exit). The four value/frame invariants are
# trivially preserved by the no-op body. Under the PRE-FIX contract (no MustTerminate)
# this rival VERIFIED — the hole the audit exhibited. It must now be REJECTED by the
# termination obligation: the function carries Requires(MustTerminate(2)) and the
# no-progress loop can take no strictly-decreasing measure, so Nagini reports an
# obligation leak.
_WEAK_NONTERM = _IMPL.replace(
    "        # The loop consumes the termination obligation: i is the strictly\n"
    "        # decreasing, bounded-below measure.\n"
    "        Invariant(MustTerminate(i))\n"
    "        # invariants-end\n"
    "        c = operands[i - 1]\n"
    "        Assert(ToSeq(operands).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(operands).drop(i - 1).drop(1) == ToSeq(operands).drop(i))\n"
    "        # Case(When(c, then=1), default=0): 1 if the operand is true else 0.\n"
    "        contribution = 1 if c == 1 else 0\n"
    "        total = contribution + total\n"
    "        any_t = (c == 1) or any_t\n"
    "        i = i - 1\n",
    "        # invariants-end\n"
    "        # NO PROGRESS: i never decreases — the loop spins forever on any\n"
    "        # non-empty operand list; the postconditions hold only vacuously.\n"
    "        total = total\n",
)
assert _WEAK_NONTERM != _IMPL, "weak-nonterm did not rewrite"

_WEAK_EQ_TRUE = _IMPL.replace(
    "    Assert(ToSeq(operands).drop(0) == ToSeq(operands))\n"
    "    # rhs_sum derivation: the parity is taken once the operand count exceeds two.\n"
    "    if len(operands) > 2:\n"
    "        rhs = total % 2\n"
    "    else:\n"
    "        rhs = total\n"
    "    # Exact(1, rhs_sum): the derived count equals one; conjoined with the OR.\n"
    "    return any_t and rhs == 1",
    "    Assert(ToSeq(operands).drop(0) == ToSeq(operands))\n"
    "    # 'exactly one true operand' against the raw count, for every operand count.\n"
    "    return any_t and total == 1",
)
assert _WEAK_EQ_TRUE != _IMPL, "weak-eq-true did not rewrite"


SPEC_TESTS = [
    {
        "id": "pos-reorder-commute",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS),
        "rationale": (
            "structurally-different but CORRECT impl: the gold BACKWARD loop, its four "
            "invariants and BOTH per-step `.drop` framing asserts are kept VERBATIM "
            "(directive 2/3 — the count_true/any_true folds are FRONT-recursive, so a "
            "forward-append loop would need an f(a+b)==f(a)+f(b) lemma the verifier "
            "can't auto-discharge; we therefore reshape only the tail). The parity "
            "branch guard is COMPLEMENTED (`<= 2` else-first, semantically identical to "
            "`> 2`) and the final conjunction is COMMUTED (`rhs == 1 and any_t`). Both "
            "are pure source reshapes with identical semantics. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (single Acc(list_pred(operands),1/2) half-permission) "
            "must admit a normal F2P-shaped operand assignment: the length is readable "
            "and, when non-empty (the F2P's 5-operand row), the first element is "
            "readable under the half-permission. The gold impl is otherwise verbatim "
            "(only reads/asserts added inside the impl region, no write). If it FAILS "
            "=> PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold branch only READS self.children — it builds NEW SQL nodes "
            "(Case/When, the reduce(add) sum, the added Mod, Exact, OR/AND) OVER the "
            "children; it NEVER mutates the children list. A faithful real patch that "
            "wrote back into the operand list would diverge from the read-only gold "
            "(and would corrupt a WhereNode child list shared across query compilation) "
            "— it would not be the gold patch and would not faithfully resolve. The "
            "store here is a no-op only by coincidence; the point is the spec must "
            "forbid ANY write to the input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `operands` is granted at "
            "Acc(list_pred(operands),1/2) (P1); the store operands[0]=operands[0] "
            "demands FULL write permission, which is not available, so the verifier "
            "rejects for INSUFFICIENT PERMISSION. The gold decision/return body is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "VERIFIES => the read-only frame is hollow (frame-mutation, the #1 weakness "
            "class; a byte-fuzzer never thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-no-mod",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_MOD),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): the original fallback "
            "built `rhs = Exact(1, rhs_sum)` straight from the raw sum, with NO Mod, so "
            "the predicate was `(OR ...) AND (sum == 1)` — 'exactly one operand true' "
            "for every operand count. Its faithful real patch is the UNCHANGED repo, "
            "which on the F2P test_filter_multiple's 5-clause XOR "
            "(Q(num__gte=1)^...^Q(num__gte=9)) selects the wrong rows (e.g. a row with "
            "3 true operands is XOR-true but the exactly-one fallback rejects it). It "
            "fails the F2P. Does NOT resolve — the precise change the spec senses "
            "(G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q2 (Result() == xor_holds(ToSeq(operands))) and Q3 (Result() "
            "== count_true % 2 == 1): for >2 operands xor_holds uses derived_count = "
            "count_true % 2, but this rival returns `any_t and total == 1` with total = "
            "raw count; on 3 true operands xor_holds is True (3 is odd) while the rival "
            "is False (3 != 1). PARTIAL-DOMAIN: correct on <=2 operands (count<=2 "
            "coincidence) but wrong as soon as the count exceeds 2. If it VERIFIES => "
            "SPEC-TOO-WEAK (the parity reduction is not enforced)."
        ),
    },
    {
        "id": "weak-mod3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MOD3),
        "refinement": (
            "reducing modulo 3 (`Mod(rhs_sum, 3)`) instead of 2 is NOT the n-ary XOR "
            "semantics — XOR is true iff an ODD number of operands are true, which is "
            "remainder-mod-2, not mod-3. A real patch with Mod(rhs_sum, 3) would, on the "
            "F2P's 5-clause XOR, mis-select rows: a row with 3 true operands is XOR-true "
            "(odd) but 3 %% 3 == 0 != 1, so it is rejected; a row with 5 true operands "
            "gives 5 %% 3 == 2 != 1, also rejected though XOR-true. It fails the F2P. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2/Q3: for >2 operands the rival's derived count is "
            "total % 3, but xor_holds/parity require total % 2. On 3 true operands the "
            "rival gives 3 %% 3 == 0 (rhs != 1, result False) while xor_holds/parity "
            "demand True (3 is odd). PARTIAL-DOMAIN: agrees on counts 0/1/2 but diverges "
            "for counts whose mod-3 value differs from their parity. If it VERIFIES => "
            "SPEC-TOO-WEAK (the spec would not pin the modulus to 2)."
        ),
    },
    {
        "id": "weak-nonterm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONTERM),
        "refinement": (
            "a real patch whose fallback evaluation never completes (e.g. an "
            "accidental infinite loop while combining the per-operand CASE terms) "
            "never returns the constructed predicate to the compiler; the F2P "
            "test_filter_multiple (and every P2P xor test) hangs and the harness "
            "times out — it does NOT resolve. This is the audit's P1 witness "
            "(atk_8 / atk_3 class): same-spec, and it VERIFIED under the pre-fix "
            "contract because Nagini checks partial correctness by default."
        ),
        "rationale": (
            "REJECTED by the termination obligation: the function precondition "
            "carries Requires(MustTerminate(2)) (P2) and this rival's loop makes "
            "no progress (i never decreases), so it can take no strictly "
            "decreasing measure — Nagini reports an obligation leak ('Loop might "
            "not take all unsatisfied obligations from the context'). Under the "
            "pre-fix contract (no MustTerminate) this rival VERIFIED: every "
            "Ensures held vacuously on the non-exiting path. Vacuity / "
            "control-flow-effect case."
        ),
    },
    {
        "id": "weak-eq-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EQ_TRUE),
        "refinement": (
            "a second, independent phrasing of the exactly-one bug: return `any_t and "
            "total == 1` with the parity branch DELETED entirely, i.e. compare the raw "
            "true count to one for ALL operand counts. This is the same wrong predicate "
            "as the pre-patch (`Exact(1, raw_sum)` for every count) spelled directly. Its "
            "faithful real patch never inserts the Mod and fails the F2P "
            "test_filter_multiple (a 3-true-operand row is XOR-true but rejected). Does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2/Q3: on >2 operands xor_holds/parity demand "
            "count_true % 2 == 1, but the rival pins exactly-one against the raw count; "
            "on 3 true operands the rival is False (3 != 1) while xor_holds/parity is "
            "True. PARTIAL-DOMAIN/value-mask: correct on the <=2 sub-domain, wrong once "
            "the count exceeds 2 — included to confirm the spec rejects the exactly-one "
            "predicate HOWEVER it is phrased. If it VERIFIES => SPEC-TOO-WEAK."
        ),
    },
]


# meta.axioms == [] and deep_model_references is explicitly "deep model (NOT an axiom,
# NOT an A-reference callee)": the changed op (Mod parity) is integer arithmetic
# modelled DEEPLY with native Nagini %/+/==/and/or (directive 7 forbids axiomatizing
# the changed op). There is no @ContractOnly axiom and no A-reference deep model to
# validate against a real library callee, so the axiom lane is vacuous here. The single
# external soundness link (model xor_holds == gold SQL predicate == odd-count) is
# already exhaustively checked by axiom_check.py / G-AX (208191 assignments).
AXIOM_TESTS = []
