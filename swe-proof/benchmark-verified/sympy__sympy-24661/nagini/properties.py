# properties.py — PBT manifest for sympy__sympy-24661. NOT a Nagini module; a
# record of adversarial falsification cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md):
#   rewrite_comparison(node: Compare) -> Node
#     READ-ONLY inputs (all fractional):
#       Acc(node.op, 1/2), Acc(node.left, 1/2), Acc(node.right, 1/2),
#       Acc(node.left.tag, 1/2), Acc(node.right.tag, 1/2)
#       -> the rewrite only READS the comparison node; it never mutates op /
#          operand handles. (The real visit_Compare reads node.ops[0].__class__,
#          node.left, node.comparators[0] and builds a NEW ast.Call; it never
#          writes the source node.)  =>  FRAME-MUTATION is MANDATORY.
#     LOAD-BEARING postconditions (all GROUNDED in the input op via @Pure
#     helpers, fully unfolded — there is no opaque answer-key to echo):
#       (P1) Result().is_call   == is_relational(node.op)
#       (P2) Result().rel_class == rel_class_of(node.op)            # bijection
#       (P3) Result().evaluate  == False
#       (P4) Result().left is node.left and Result().right is node.right
#            (UNCONDITIONAL: a produced call carries the operands in source
#             order; an unchanged non-relational node keeps its own operands)
#       (P5) Result().op == node.op
#            (UNCONDITIONAL: the operator code is preserved on both branches,
#             so no result field is a free/unconstrained channel)
#     is_relational(op) = op in {OP_LT..OP_EQ} = {0..5}; rel_class_of maps
#       OP_LT->REL_LT(100) .. OP_EQ->REL_EQ(105), else REL_NONE(-1).
#
# Ungrounded-oracle note: the postcondition oracle (is_relational / rel_class_of)
# is a function of the INPUT node.op, fully unfolded by Nagini — NOT an opaque
# answer key the impl could echo without doing the work. The honest cheapest impl
# IS to call these helpers (which is what the gold does). So there is no "wrong
# echo" rival to build (directive 2); instead the positive controls below are the
# soundness controls, and the uniqueness attacks target the bijection/flag/order
# pins directly.
#
# Control-flow-effect note: rewrite_comparison is pure — no raise path, no
# side-effect, and EVERY observable of the produced node (is_call, rel_class,
# evaluate, left, right, op) is in the value abstraction. There is no
# raise/return/side-effect difference invisible to the abstraction, so the
# control-flow-effect class is N/A here (see assessment).
#
# Region-surgery (_swap on _BASE) edits ONLY inside the single
# # impl-start / # impl-end region, so every spec case is same_spec by
# construction (the frozen axioms/pure/pre/post-conditions are never touched).
from pathlib import Path

INSTANCE = "sympy__sympy-24661"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl body (unique, strictly inside the # impl-start/# impl-end region).
# Every variant below is produced by replacing this exact block.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)"""


# ===========================================================================
# (1) FRAME-MUTATION — MANDATORY: node.op (and node.left.tag) are READ-ONLY
# (Acc(...,1/2)). A rival that WRITES node.op to a relational code before
# branching could vacuously force the relational path, and a value-blind "real
# patch" that mutated the source AST node in place would look correct on the
# F2P (the produced Call value is unchanged). The spec must reject it for
# INSUFFICIENT PERMISSION: the precondition grants only Acc(node.op,1/2), enough
# to READ node.op but not to assign it. Gold logic kept verbatim around the write
# so the rejection is attributable solely to the mutation.
# ===========================================================================
_frame_mut_op = _swap(
    _BASE,
    _GOLD_IMPL,
    """    node.op = node.op  # WRITE to read-only input -> insufficient permission
    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)""",
)

# Frame-mutation on the operand tag (Acc(node.left.tag,1/2) is read-only too).
_frame_mut_tag = _swap(
    _BASE,
    _GOLD_IMPL,
    """    node.left.tag = node.left.tag  # WRITE to read-only operand -> insufficient permission
    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)""",
)


# ===========================================================================
# (2) WRONG CONSTRUCTOR (bijection violation) — convert relational operators but
# emit a HARD-CODED constructor (REL_LT) for every operator instead of
# rel_class_of(node.op). Correct for op==OP_LT, wrong for the other five.
# Refinement: the real patch looks up self.relational_operators[op.__class__],
# producing Le/Gt/Ge/Ne/Eq for the matching operators. Hard-coding 'Lt' would
# rewrite "1 <= 2" to Lt(1,2,evaluate=False) != Le(1,2,evaluate=False), so the
# F2P test_issue_24288 assertion for "1 <= 2" (and 4 others) FAILS — does NOT
# resolve.
# ===========================================================================
_wrong_ctor = _swap(
    _BASE,
    _GOLD_IMPL,
    """    if is_relational(node.op):
        right = node.right
        left = node.left
        new_node = Node(True, REL_LT, False, left, right, node.op)  # always Lt
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)""",
)


# ===========================================================================
# (3) OPERAND ORDER SWAP — convert with the correct constructor but build the
# call with operands SWAPPED (left<->right). Violates P4
# (Result().left is node.left).
# Refinement: the real patch builds args=[left, right] in source order, so
# "1 < 2" yields Lt(1, 2, evaluate=False). Swapping yields Lt(2, 1, evaluate=
# False), which is NOT equal to Lt(1, 2, evaluate=False) — F2P test_issue_24288
# for "1 < 2" (and all five asymmetric ops) FAILS — does NOT resolve.
# ===========================================================================
_swap_operands = _swap(
    _BASE,
    _GOLD_IMPL,
    """    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, right, left, node.op)  # swapped
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)""",
)


# ===========================================================================
# (4) EVALUATE=TRUE — convert with the correct constructor + order but set the
# evaluating flag. Violates P3 (Result().evaluate == False). This is the EXACT
# reported bug: a relational built with evaluate=True collapses to a concrete
# truth value.
# Refinement: the real patch sets keywords=[evaluate=False]; emitting
# evaluate=True (or omitting it) makes parse_expr('1 < 2', evaluate=False)
# return True instead of Lt(1, 2, evaluate=False) — precisely what
# test_issue_24288 was written to catch — does NOT resolve.
# ===========================================================================
_evaluate_true = _swap(
    _BASE,
    _GOLD_IMPL,
    """    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, True, left, right, node.op)  # evaluate=True!
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)""",
)


# ===========================================================================
# (5) PARTIAL-DOMAIN — handle 5 of the 6 operators but DROP equality (treat
# OP_EQ as non-relational, returning it unchanged). Correct on Lt/Le/Gt/Ge/Ne,
# wrong on Eq. Violates P1 (is_call==is_relational(node.op)) for op==OP_EQ:
# is_relational(OP_EQ) is True but this returns is_call==False.
# Refinement: the faithful real patch would omit ast.Eq:'Eq' from
# relational_operators. Then "1 == 2" has no relational rewrite and stays a bare
# ast.Compare that collapses to a bool, so parse_expr('1 == 2', evaluate=False)
# returns True instead of Eq(1, 2, evaluate=False) — the F2P entry
# inputs["1 == 2"] of test_issue_24288 FAILS — does NOT resolve.
# ===========================================================================
_drop_eq = _swap(
    _BASE,
    _GOLD_IMPL,
    """    if node.op == OP_LT or node.op == OP_LE or node.op == OP_GT or \\
            node.op == OP_GE or node.op == OP_NE:   # OP_EQ deliberately dropped
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)""",
)


# ===========================================================================
# (6) OVER-CONVERT — convert EVERY comparison to a call, including
# non-relational (membership/identity) operators. Violates P1 for op>=6:
# is_relational returns False there but this forces is_call==True. (rel_class_of
# returns REL_NONE for op>=6, so Node(True, rel_class_of(node.op), ...) yields a
# call with REL_NONE — the postcondition for is_call still fails first.)
# Refinement: the faithful real patch only rewrites operators IN
# relational_operators; converting `1 in x` / `1 is x` to a symbolic-comparison
# call with a REL_NONE / nonexistent constructor would change parser output for
# membership/identity comparisons (the gold returns them unchanged so they
# behave as before). PASS_TO_PASS parser tests covering non-relational
# comparison parsing would break — does NOT resolve.
# ===========================================================================
_over_convert = _swap(
    _BASE,
    _GOLD_IMPL,
    """    sympy_class = rel_class_of(node.op)
    right = node.right
    left = node.left
    new_node = Node(True, sympy_class, False, left, right, node.op)  # convert ALL ops
    return new_node""",
)


# ===========================================================================
# (7) POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
# Shape change: branch on the NEGATION (handle the non-relational case first via
# an early return), and reshape the relational branch with the constructor
# hoisted into a named local computed before the operands. No loop here (so no
# induction-lemma hazard, pilot warning #3 N/A); the gold proof obligations are
# all discharged by the same per-branch reasoning. Must verify; if it cannot,
# the postcondition is SPEC-TOO-STRONG.
# ===========================================================================
_pos_ctrl = _swap(
    _BASE,
    _GOLD_IMPL,
    """    if not is_relational(node.op):
        return Node(False, REL_NONE, False, node.left, node.right, node.op)
    cls = rel_class_of(node.op)
    lft = node.left
    rgt = node.right
    return Node(True, cls, False, lft, rgt, node.op)""",
)


# ===========================================================================
# (8) ADMISSIBILITY — the precondition must admit a normal F2P-shaped input.
# Inside the impl region, BEFORE the gold logic, assert the Requires holds for
# the actual argument (op readable, operands readable) — a representative
# F2P-shaped relational node (a "1 < 2"-style Compare) is in-domain. Uses only
# the permissions the gold proof already holds (fractional reads). If this
# cannot verify, the precondition is PRECOND-TOO-STRONG.
# ===========================================================================
_admiss = _swap(
    _BASE,
    _GOLD_IMPL,
    """    # admissibility: the precondition admits a normal F2P-shaped comparison
    # node — op and both operand tags are readable at 1/2 permission.
    Assert(Acc(node.op, 1 / 2))
    Assert(Acc(node.left.tag, 1 / 2) and Acc(node.right.tag, 1 / 2))
    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)""",
)


SPEC_TESTS = [
    {
        "id": "frame-mut-op",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_op,
        "refinement": (
            "node.op = node.op is a value no-op, so a real patch that wrote back "
            "the source AST node's operator (or any in-place mutation of the "
            "ast.Compare) would still build the same ast.Call and could look "
            "correct on the F2P test. The spec must reject it on PERMISSION "
            "grounds: the real visit_Compare only READS node.ops[0].__class__ and "
            "constructs a NEW node, so the contract grants only Acc(node.op,1/2). "
            "A patch that mutated the shared source AST would be unfaithful (and "
            "could corrupt the tree for sibling visitors)."
        ),
        "rationale": (
            "Rejection comes from the permission system: assigning node.op needs "
            "FULL write permission to node.op but the precondition grants only "
            "1/2. INSUFFICIENT PERMISSION, not a postcondition failure."
        ),
    },
    {
        "id": "frame-mut-tag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _frame_mut_tag,
        "refinement": (
            "node.left.tag = node.left.tag is a value no-op; a real patch that "
            "mutated an operand sub-expression in place would still emit the same "
            "Call and pass the F2P value checks — the value abstraction is blind "
            "to the write. But the operands are read-only (Acc(node.left.tag,1/2)) "
            "because the real rewrite only visits/reads them; mutating an operand "
            "node is unfaithful to the gold patch."
        ),
        "rationale": (
            "Rejection from the permission system: assigning node.left.tag needs "
            "FULL permission to node.left.tag; the precondition grants only 1/2."
        ),
    },
    {
        "id": "wrong-constructor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _wrong_ctor,
        "refinement": (
            "Hard-coding REL_LT (Lt) for every relational operator is correct only "
            "for strict-less. The faithful real patch looks up "
            "relational_operators[op], producing Le/Gt/Ge/Ne/Eq for the matching "
            "operators; emitting Lt for '1 <= 2' yields Lt(1,2,evaluate=False) != "
            "Le(1,2,evaluate=False). F2P test_issue_24288's assertion for '1 <= 2' "
            "(and four other operators) FAILS — does NOT resolve."
        ),
        "rationale": (
            "Rejection from postcondition P2: Result().rel_class == "
            "rel_class_of(node.op). For op==OP_LE the produced rel_class is REL_LT "
            "(100) but rel_class_of(OP_LE)==REL_LE (101) — the equality fails."
        ),
    },
    {
        "id": "operand-order-swap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap_operands,
        "refinement": (
            "Building the call with operands swapped produces Lt(2,1,evaluate="
            "False) for '1 < 2'. The faithful real patch sets args=[left, right] "
            "in source order; Lt(2,1,evaluate=False) != Lt(1,2,evaluate=False), so "
            "F2P test_issue_24288 for '1 < 2' (and every asymmetric operator) "
            "FAILS — does NOT resolve."
        ),
        "rationale": (
            "Rejection from postcondition P4 (unconditional): Result().left is "
            "node.left and Result().right is node.right. With operands swapped "
            "Result().left is node.right, so the identity pin fails."
        ),
    },
    {
        "id": "evaluate-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _evaluate_true,
        "refinement": (
            "Setting evaluate=True reproduces the EXACT reported bug: a relational "
            "built with evaluate=True collapses to a concrete truth value. The "
            "faithful real patch sets keywords=[evaluate=False]; with evaluate "
            "True, parse_expr('1 < 2', evaluate=False) returns True instead of "
            "Lt(1,2,evaluate=False) — precisely what test_issue_24288 catches — "
            "does NOT resolve."
        ),
        "rationale": (
            "Rejection from postcondition P3: Result().evaluate == False. The "
            "produced node has evaluate==True, contradicting the unconditional "
            "False pin."
        ),
    },
    {
        "id": "partial-domain-drop-eq",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _drop_eq,
        "refinement": (
            "Treating OP_EQ as non-relational is correct on five operators but "
            "drops equality. The faithful real patch would omit ast.Eq:'Eq' from "
            "relational_operators, leaving '1 == 2' a bare ast.Compare that "
            "collapses to a bool; parse_expr('1 == 2', evaluate=False) returns "
            "True instead of Eq(1,2,evaluate=False) — the inputs['1 == 2'] entry "
            "of F2P test_issue_24288 FAILS — does NOT resolve."
        ),
        "rationale": (
            "Rejection from postcondition P1: Result().is_call == "
            "is_relational(node.op). For op==OP_EQ, is_relational(OP_EQ) is True "
            "but this returns is_call==False — the equality fails."
        ),
    },
    {
        "id": "over-convert-nonrelational",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _over_convert,
        "refinement": (
            "Converting every comparison to a call also rewrites membership/"
            "identity comparisons (op>=6). The faithful real patch only rewrites "
            "operators IN relational_operators and returns the rest unchanged; "
            "wrapping '1 in x' / '1 is x' into a symbolic-comparison call with a "
            "REL_NONE / nonexistent constructor changes parser output for those "
            "comparisons (the PASS_TO_PASS parser suite exercises non-relational "
            "comparison parsing) — does NOT resolve."
        ),
        "rationale": (
            "Rejection from postcondition P1: Result().is_call == "
            "is_relational(node.op). For op>=6, is_relational is False but this "
            "forces is_call==True — the equality fails."
        ),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_ctrl,
        "rationale": (
            "A structurally-different but CORRECT impl: the non-relational case is "
            "handled first via an early return, and the relational branch hoists "
            "the constructor and operands into named locals before constructing "
            "the node. No loop (so no induction-lemma hazard); each branch "
            "discharges the same per-branch obligations as the gold. It MUST "
            "verify; if it cannot, the postcondition is SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-readonly-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss,
        "rationale": (
            "The precondition Acc(node.op,1/2) + Acc(node.left.tag,1/2) + "
            "Acc(node.right.tag,1/2) must admit a normal F2P-shaped comparison "
            "node. The impl asserts those reads hold for the actual argument "
            "before running the gold logic, using only permissions the gold proof "
            "already holds. If this cannot verify, the precondition is "
            "PRECOND-TOO-STRONG."
        ),
    },
]


# ===========================================================================
# AXIOM LANE.
# The bundle has NO @ContractOnly axiom (axioms region empty; meta axioms: []).
# It DOES carry one A-reference deep model: the model's operator->constructor
# correspondence (rel_class_of / is_relational + produced Node shape) IS the deep
# model of the real post-patch EvaluateFalseTransformer.visit_Compare. G-AX
# already validates this via axiom_check.py; per PBT_PLAN §2.4 / §4a the
# A-reference is checked the same way as an axiom (deep model == real callee on
# every caller-reachable input). We persist that check as an axiom-soundness
# probe so a future regression in the real callee (e.g. a constructor remap or an
# evaluate-default change) is caught by G-PBT too.
#
# The runner mounts ONLY this probe at /work; it imports only stdlib `ast` + the
# repository's sympy.parsing.sympy_parser (the edited module). apply_gold=True so
# the post-patch visit_Compare (with relational_operators + the rewrite) exists.
# ===========================================================================
_AREF_PROBE = r'''
import ast
import sys

from sympy.parsing.sympy_parser import EvaluateFalseTransformer

FAIL = []
def fail(m):
    FAIL.append(m); print("VIOLATION:", m)

# model.py's operator->constructor correspondence (rel_class_of / is_relational),
# expressed by the AST comparison-operator class -> SymPy constructor name.
MODEL = {
    ast.Lt: "Lt",    # OP_LT  -> REL_LT
    ast.LtE: "Le",   # OP_LE  -> REL_LE
    ast.Gt: "Gt",    # OP_GT  -> REL_GT
    ast.GtE: "Ge",   # OP_GE  -> REL_GE
    ast.NotEq: "Ne", # OP_NE  -> REL_NE
    ast.Eq: "Eq",    # OP_EQ  -> REL_EQ
}
SAMPLE = {
    ast.Lt: "1 < 2", ast.LtE: "1 <= 2", ast.Gt: "1 > 2",
    ast.GtE: "1 >= 2", ast.NotEq: "1 != 2", ast.Eq: "1 == 2",
}
# comparison operators OUTSIDE the relational set -> must be returned unchanged.
NON_REL = {"In": "1 in x", "NotIn": "1 not in x", "Is": "1 is x", "IsNot": "1 is not x"}

# (A) the real relational_operators table == the model bijection (same domain,
#     same images). This is the containment+image check: the model covers
#     EXACTLY the six operators the real callee maps, and no caller-reachable
#     operator lies outside it.
real = EvaluateFalseTransformer.relational_operators
if set(real.keys()) != set(MODEL.keys()):
    fail("relational_operators domain mismatch: real=%r model=%r"
         % (sorted(c.__name__ for c in real), sorted(c.__name__ for c in MODEL)))
for cls, name in real.items():
    if MODEL.get(cls) != name:
        fail("constructor mismatch for %s: real=%r model=%r"
             % (cls.__name__, name, MODEL.get(cls)))

# (B) run the REAL visit_Compare on each relational operator; assert it builds a
#     Call to the matching SymPy constructor with evaluate=False and operands in
#     left/right order (model: is_call==True, rel_class==rel_class_of(op),
#     evaluate==False, left/right identity).
for op_cls, name in MODEL.items():
    tree = ast.parse(SAMPLE[op_cls], mode="eval")
    node = tree.body
    if not isinstance(node, ast.Compare) or node.ops[0].__class__ is not op_cls:
        fail("parse setup wrong for %s" % op_cls.__name__); continue
    out = EvaluateFalseTransformer().visit_Compare(node)
    if not isinstance(out, ast.Call):
        fail("%s not converted to a Call: %r" % (op_cls.__name__, type(out))); continue
    if not (isinstance(out.func, ast.Name) and out.func.id == name):
        fail("%s wrong constructor: %r expected %r"
             % (op_cls.__name__, getattr(out.func, "id", out.func), name))
    if len(out.args) != 2:
        fail("%s wrong arg count: %r" % (op_cls.__name__, out.args))
    kw = {k.arg: k for k in out.keywords}
    if "evaluate" not in kw:
        fail("%s missing evaluate keyword" % op_cls.__name__)
    else:
        val = kw["evaluate"].value
        actual = getattr(val, "value", getattr(val, "n", None))
        if actual is not False:
            fail("%s evaluate keyword not False: %r" % (op_cls.__name__, actual))

# (C) non-relational comparisons are returned UNCHANGED (model: is_call==False).
for label, text in NON_REL.items():
    tree = ast.parse(text, mode="eval")
    node = tree.body
    if not isinstance(node, ast.Compare):
        fail("parse setup wrong for %s" % label); continue
    out = EvaluateFalseTransformer().visit_Compare(node)
    if out is not node:
        fail("%s should be unchanged but visit_Compare altered it: %r" % (label, type(out)))

if FAIL:
    print("A-REF FAILED: %d violation(s)" % len(FAIL)); sys.exit(1)
print("A-REF OK: EvaluateFalseTransformer.visit_Compare == model on all 6 "
      "relational rewrites (Lt/Le/Gt/Ge/Ne/Eq, evaluate=False, left/right order), "
      "the relational_operators bijection, and %d non-relational unchanged cases."
      % len(NON_REL))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "aref-visit-compare",
        "axiom": "rel_class_of / is_relational + produced Node shape (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AREF_PROBE,
        "rationale": (
            "A-reference: the model's operator->constructor bijection "
            "(rel_class_of / is_relational) and produced-node shape must equal the "
            "REAL post-patch EvaluateFalseTransformer.visit_Compare on every "
            "caller-reachable operator. The probe runs the real callee on all six "
            "relational operators (asserting a Call to the matching constructor, "
            "evaluate=False, left/right order), checks the relational_operators "
            "table has EXACTLY the six keys the model covers (containment: no "
            "caller-reachable operator falls outside the model), and checks four "
            "non-relational operators are returned unchanged. Divergence is an "
            "A-reference unsoundness (verify would not imply resolve)."
        ),
    },
]
