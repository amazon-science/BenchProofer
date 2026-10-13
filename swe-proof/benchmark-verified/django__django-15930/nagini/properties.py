"""properties.py — PBT falsification battery for django__django-15930.

NOT a Nagini module; a record of adversarial cases the runner
(swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
model.py variants that share the FROZEN spec (only the # impl-start/# impl-end
region differs — region surgery guarantees same_spec) and are checked by Nagini
verify. There are no @ContractOnly axioms in this bundle, so AXIOM_TESTS = [].

Defended surface (what the spec pins about `render_branch`):
  Inputs pred / pred_params / cons / cons_params are ALL read-only at
  Acc(..., 1/2) (Requires AND Ensures). The postcondition pins:
    P1  ToSeq(Result()[0]) == clause_text(ToSeq(pred), ToSeq(cons))
    P2  ToSeq(Result()[1]) == clause_params(ToSeq(pred), pred_params, cons_params)
    P3  len(Result()[0]) > len(lead()) + len(sep()) + len(cons)   (slot-non-blank)
  clause_text / clause_params are GROUNDED @Pure helpers (fully-unfolded
  functions of the inputs) — there is no opaque answer-key to echo, so the
  ungrounded-oracle-echo class does not apply here (a "wrong echo" cannot exist
  because the oracle is a deterministic function of the args, not a marker an
  impl can parrot). The discriminating content of the gold fix lives in P1's
  empty branch (substitute the NON-EMPTY always-true predicate) backed by P3.
  No raise / side-effect is modelled, so control-flow-effect is N/A.
"""
from pathlib import Path

INSTANCE = "django__django-15930"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()
_PREPATCH = (Path(__file__).parent / "model_prepatch.py").read_text()


def _impl_region(src):
    lo = src.index("    # impl-start")
    hi = src.index("    # impl-end") + len("    # impl-end")
    return src[lo:hi]


_GOLD_IMPL = _impl_region(_BASE)
_PRE_IMPL = _impl_region(_PREPATCH)
assert _GOLD_IMPL in _BASE and _BASE.count(_GOLD_IMPL) == 1


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


def _replace_impl(new_impl):
    """Swap ONLY the impl region; the frozen spec head is untouched."""
    return _swap(_BASE, _GOLD_IMPL, new_impl)


# --------------------------------------------------------------------------
# (1) POSITIVE CONTROL / soundness — structurally-different but CORRECT.
# Branch-reorder: test `len(pred) != 0` first and swap the two bodies. The two
# real branch bodies are extracted VERBATIM from the gold impl (so every loop
# invariant, framing Assert and the disjunctive merge fact are byte-identical),
# and only the executable branch order changes; the gold proof stays valid.
# Must verify; a rejection here would be SPEC-TOO-STRONG.
# --------------------------------------------------------------------------
_IF_HDR = "    if len(pred) == 0:\n"
_ELSE_HDR = "\n    else:\n"
_MERGE_MARK = "    # The disjunctive predicate-slot fact survives the merge."


def _extract_branches(impl):
    ia = impl.index(_IF_HDR)
    ie = impl.index(_ELSE_HDR, ia)
    empty_body = impl[ia + len(_IF_HDR):ie]            # no trailing newline
    after_else = ie + len(_ELSE_HDR)
    im = impl.index(_MERGE_MARK, after_else)
    nonempty_body = impl[after_else:im]                # ends with "\n"
    gold_branch = (_IF_HDR + empty_body + _ELSE_HDR + nonempty_body)
    reorder_branch = ("    if len(pred) != 0:\n" + nonempty_body.rstrip("\n") +
                      _ELSE_HDR + empty_body + "\n")
    return gold_branch, reorder_branch


_GOLD_BRANCH, _REORDER_BRANCH = _extract_branches(_GOLD_IMPL)
_POS_REORDER = _replace_impl(_swap(_GOLD_IMPL, _GOLD_BRANCH, _REORDER_BRANCH))


# --------------------------------------------------------------------------
# (2) ADMISSIBILITY — the unmodified gold impl. Demonstrates the precondition
# (four Acc(...,1/2) read-only inputs) ADMITS the F2P/P2P-shaped input and that
# the postcondition is reachable along a normal path (both the empty and the
# non-empty predicate branches are proved). If this did NOT verify the
# precondition would be unsatisfiable for a legitimate input (PRECOND-TOO-STRONG).
# --------------------------------------------------------------------------
_ADMISS = _BASE


# --------------------------------------------------------------------------
# (3) FRAME-MUTATION (MANDATORY — read-only inputs at Acc(...,1/2)).
# A rival that WRITES to the read-only consequent-parameter list to satisfy the
# work, keeping every gold invariant verbatim. list.append needs FULL permission;
# the impl holds only Acc(cons_params, 1/2) -> rejection for INSUFFICIENT
# PERMISSION, attributable solely to the write. expect=reject.
# Refinement: the real When.as_sql NEVER mutates its compiled `result_params`
# (it `sql_params.extend(...)`s a fresh list); a faithful patch that mutated the
# caller's shared result_params list would corrupt sibling When clauses /
# re-rendered CASE expressions (test_case_reuse, the order_by re-render),
# failing P2P — so it would not resolve.
# --------------------------------------------------------------------------
_FRAME_CONS = _replace_impl(_swap(
    _GOLD_IMPL,
    "    cond_text = []  # type: List[int]\n    cond_params = []  # type: List[int]\n",
    "    cond_text = []  # type: List[int]\n    cond_params = []  # type: List[int]\n"
    "    cons_params.append(0)  # frame-mutation: write to a read-only Acc(.,1/2) input\n"))

# supporting frame-mutation: write to the predicate-fragment input instead.
_FRAME_PRED = _replace_impl(_swap(
    _GOLD_IMPL,
    "    cond_text = []  # type: List[int]\n    cond_params = []  # type: List[int]\n",
    "    cond_text = []  # type: List[int]\n    cond_params = []  # type: List[int]\n"
    "    pred.append(0)  # frame-mutation: write to a read-only Acc(pred,1/2) input\n"))


# --------------------------------------------------------------------------
# (4) PARTIAL-DOMAIN (text + length) — the REAL pre-patch skeleton. Uses the
# supplied predicate verbatim with NO substitution when empty: on the empty
# predicate the slot is blank, violating P1 (clause_text wants true_predicate
# spliced) AND P3 (the slot-non-blank length clause). Correct on every non-empty
# predicate; diverges precisely on the empty-fragment sub-domain. expect=reject.
# Refinement: this IS the pre-patch When.as_sql. ~Q(pk__in=[]) compiles to the
# empty fragment and renders the malformed "WHEN  THEN ..." -> SQL syntax error
# -> test_annotate_with_full_when (F2P) raises -> does NOT resolve (model_prepatch
# fails exactly P1/P3, per G-DIFF).
# --------------------------------------------------------------------------
_PARTIAL_PREPATCH = _replace_impl(_PRE_IMPL)


# --------------------------------------------------------------------------
# (5) PARTIAL-DOMAIN (params order) — wrong bound-parameter concatenation order.
# Renders the correct TEXT (P1, P3 hold) but emits params as
# cons_params ++ slot_params instead of slot_params ++ cons_params, violating
# P2 (clause_params pins predicate-slot params FIRST). The final two params
# loops are reordered; their invariants are rewritten consistently (in-region),
# so the rival is internally provable and the rejection is attributable to P2.
# expect=reject.
# Refinement: a faithful When.as_sql doing sql_params.extend(result_params)
# before sql_params.extend(condition_params) binds the placeholders in the wrong
# positions -> the CASE WHEN compares/returns the wrong values -> the row-value
# assertions in test_annotate_with_full_when and the many P2P update/annotate
# tests fail -> does NOT resolve.
# --------------------------------------------------------------------------
_GOLD_PARAMS_TAIL = """    params = []  # type: List[int]
    i = 0
    while i < len(cond_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(0 <= i and i <= len(cond_params))
        Invariant(ToSeq(params) == ToSeq(cond_params).take(i))
        Invariant(MustTerminate(len(cond_params) - i + 1))
        # invariants-end
        params = params + [cond_params[i]]
        i = i + 1
    i = 0
    while i < len(cons_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(Acc(list_pred(cons_params), 1 / 2))
        Invariant(0 <= i and i <= len(cons_params))
        Invariant(ToSeq(params) ==
                  ToSeq(cond_params) + ToSeq(cons_params).take(i))
        Invariant(MustTerminate(len(cons_params) - i + 1))
        # invariants-end
        params = params + [cons_params[i]]
        i = i + 1
    return text, params"""

_WRONG_PARAMS_TAIL = """    params = []  # type: List[int]
    i = 0
    while i < len(cons_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cons_params), 1 / 2))
        Invariant(0 <= i and i <= len(cons_params))
        Invariant(ToSeq(params) == ToSeq(cons_params).take(i))
        # invariants-end
        params = params + [cons_params[i]]
        i = i + 1
    i = 0
    while i < len(cond_params):
        # invariants-start
        Invariant(Acc(list_pred(params)))
        Invariant(Acc(list_pred(cond_params), 1 / 2))
        Invariant(Acc(list_pred(cons_params), 1 / 2))
        Invariant(0 <= i and i <= len(cond_params))
        Invariant(ToSeq(params) ==
                  ToSeq(cons_params) + ToSeq(cond_params).take(i))
        # invariants-end
        params = params + [cond_params[i]]
        i = i + 1
    return text, params"""

_PARTIAL_PARAMS_ORDER = _replace_impl(
    _swap(_GOLD_IMPL, _GOLD_PARAMS_TAIL, _WRONG_PARAMS_TAIL))


# --------------------------------------------------------------------------
# (6) PARTIAL-DOMAIN (non-empty slot content) — on the NON-EMPTY predicate
# branch, fill the predicate-slot TEXT from the consequent `cons` instead of the
# supplied predicate `pred` (cond_params kept correct). Correct on the empty
# sub-domain; on every non-empty predicate the slot text is wrong, so the
# returned text cannot equal clause_text(pred, cons) = lead + pred + sep + cons,
# i.e. P1 is unprovable. Concretely the verifier fails the gold bridging fact
# `ToSeq(cond_text) == ToSeq(pred)` (the merge assert that derives P1) because it
# is genuinely false here — the reject is attributable to P1, not a proof
# trigger gap (no impl returning lead+cons+sep+cons can satisfy P1). expect=reject.
# Refinement: a real patch that placed result_sql in the condition slot renders
# "WHEN <result> THEN <result>" -> the CASE WHEN predicate is the wrong
# expression -> wrong/erroring SQL on every non-trivial condition -> the bulk of
# the P2P annotate/filter/update tests fail -> does NOT resolve.
# The whole gold non-empty branch body (extracted verbatim) is swapped; only the
# cond_text loop is redirected to range over `cons`. The trailing disjunctive
# merge Assert is kept identical (it is exactly what becomes unprovable).
# --------------------------------------------------------------------------
_GOLD_NONEMPTY_BODY = _GOLD_BRANCH[
    _GOLD_BRANCH.index(_ELSE_HDR) + len(_ELSE_HDR):]

_NONEMPTY_BODY_WRONG = """        k = 0
        while k < len(cons):
            # invariants-start
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(cons), 1 / 2))
            Invariant(0 <= k and k <= len(cons))
            Invariant(ToSeq(cond_text) == ToSeq(cons).take(k))
            # invariants-end
            cond_text = cond_text + [cons[k]]
            k = k + 1
        Assert(ToSeq(cons).take(len(cons)) == ToSeq(cons))
        Assert(ToSeq(cond_text) == ToSeq(cons))
        k = 0
        while k < len(pred_params):
            # invariants-start
            Invariant(Acc(list_pred(cond_params)))
            Invariant(Acc(list_pred(cond_text)))
            Invariant(Acc(list_pred(pred), 1 / 2))
            Invariant(Acc(list_pred(pred_params), 1 / 2))
            Invariant(len(pred) > 0)
            Invariant(ToSeq(cond_text) == ToSeq(cons))
            Invariant(0 <= k and k <= len(pred_params))
            Invariant(ToSeq(cond_params) == ToSeq(pred_params).take(k))
            Invariant(MustTerminate(len(pred_params) - k + 1))
            # invariants-end
            cond_params = cond_params + [pred_params[k]]
            k = k + 1
        Assert(ToSeq(pred_params).take(len(pred_params)) == ToSeq(pred_params))
        Assert(ToSeq(cond_params) == ToSeq(pred_params))
        Assert(ToSeq(cond_text) == ToSeq(cons))
        Assert(len(pred) != 0)
        # Establish a disjunctive value fact about the predicate slot that holds
        # in this branch; it survives the merge (the if branch proves the other
        # disjunct), pinning cond_text / cond_params to their definitions.
        Assert((len(pred) == 0 and ToSeq(cond_text) == true_predicate() and
                ToSeq(cond_params) == true_params()) or
               (len(pred) != 0 and ToSeq(cond_text) == ToSeq(pred) and
                ToSeq(cond_params) == ToSeq(pred_params)))
"""

_PARTIAL_NONEMPTY = _replace_impl(
    _swap(_GOLD_IMPL, _GOLD_NONEMPTY_BODY, _NONEMPTY_BODY_WRONG))


SPEC_TESTS = [
    {"id": "pos-control-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different CORRECT impl (branch order flipped, "
                  "all gold invariants/asserts kept verbatim) must verify; a "
                  "rejection would be SPEC-TOO-STRONG."},

    {"id": "admiss-gold", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "the frozen gold impl verifies, so the four Acc(...,1/2) "
                  "read-only preconditions ADMIT an F2P/P2P-shaped input and the "
                  "postcondition is reachable on both predicate branches; "
                  "failure would be PRECOND-TOO-STRONG."},

    {"id": "frame-mutate-cons-params", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_CONS,
     "refinement": "the real When.as_sql never mutates its compiled result_params "
                   "(it extends a fresh sql_params); a patch mutating the caller's "
                   "shared param list would corrupt re-rendered/reused CASE "
                   "expressions (test_case_reuse, order_by re-render) and fail P2P "
                   "-> would not resolve.",
     "rationale": "rejection from the PERMISSION SYSTEM: list.append needs full "
                  "permission but cons_params is held at Acc(...,1/2). #1 weakness "
                  "class; a verifying mutation would be SPEC-TOO-WEAK (vacuous "
                  "frame)."},

    {"id": "frame-mutate-pred", "kind": "uniqueness", "expect": "reject",
     "module": _FRAME_PRED,
     "refinement": "same as frame-mutate-cons-params but on the predicate "
                   "fragment input; a real patch mutating the shared condition_sql "
                   "carrier would corrupt sibling clauses -> would not resolve.",
     "rationale": "supporting frame-mutation: write to Acc(pred,1/2) -> "
                  "insufficient permission."},

    {"id": "partial-domain-prepatch", "kind": "uniqueness", "expect": "reject",
     "module": _PARTIAL_PREPATCH,
     "refinement": "this is the pre-patch When.as_sql (no empty-fragment "
                   "substitution). ~Q(pk__in=[]) compiles to the empty fragment, "
                   "rendering the malformed 'WHEN  THEN ...' -> SQL syntax error -> "
                   "test_annotate_with_full_when (F2P) raises -> does NOT resolve.",
     "rationale": "rejection from P1 (clause_text wants true_predicate spliced on "
                  "the empty predicate) and P3 (slot-non-blank length); this is the "
                  "G-DIFF model_prepatch behaviour. A verifying pre-patch impl "
                  "would be SPEC-TOO-WEAK (the bug echoes through)."},

    {"id": "partial-domain-params-order", "kind": "uniqueness", "expect": "reject",
     "module": _PARTIAL_PARAMS_ORDER,
     "refinement": "extending sql_params with result_params BEFORE condition_params "
                   "binds the placeholders in the wrong positions; the CASE WHEN "
                   "returns/compares wrong values, failing the row-value assertions "
                   "in test_annotate_with_full_when and many P2P annotate/update "
                   "tests -> does NOT resolve.",
     "rationale": "rejection from P2 (clause_params pins predicate-slot params "
                  "BEFORE consequent params); text P1/P3 still hold, so this isolates "
                  "P2 as load-bearing. A verifying wrong-order impl would be "
                  "SPEC-TOO-WEAK."},

    {"id": "partial-domain-nonempty-slot", "kind": "uniqueness", "expect": "reject",
     "module": _PARTIAL_NONEMPTY,
     "refinement": "placing result_sql in the condition slot renders "
                   "'WHEN <result> THEN <result>' -> the predicate is the wrong "
                   "expression on every non-trivial condition -> the bulk of the "
                   "P2P annotate/filter/update tests fail -> does NOT resolve.",
     "rationale": "rejection from P1 on the NON-EMPTY sub-domain (slot must be the "
                  "supplied predicate verbatim); confirms P1 pins the non-empty path "
                  "too, not just the empty substitution."},
]

# No @ContractOnly axioms / consumed axioms in model.py. The single A-reference
# (true_predicate()/true_params() == compiler.compile(Value(True))) is validated
# by axiom_check.py / G-AX (the real callee in Docker); it is a deep model, not a
# consumed axiom, so there is no axiom obligation to re-probe here.
AXIOM_TESTS = []
