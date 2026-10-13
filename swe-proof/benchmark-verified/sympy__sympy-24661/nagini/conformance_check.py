#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24661 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model's carrier classes
(Expr/Compare/Node) become plain Python classes with the same constructor
shapes; the @Pure helpers `is_relational` / `rel_class_of` copy over as plain
functions. There are no @ContractOnly callees and no PSeq in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
`sympy.parsing.sympy_parser.EvaluateFalseTransformer.visit_Compare`, run on a
freshly built comparison syntax node. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable.

Type bridge (mapping.md section 2):
  * the comparison-operator class on the syntax node <-> the model's int
    operator code (Lt<->0, LtE<->1, Gt<->2, GtE<->3, NotEq<->4, Eq<->5; any
    comparison-operator class outside that set <-> a code >= 6). The model
    collapses ALL codes >= 6 into one non-relational bucket, so a fuzzed code
    >= 6 is realized as one of the four concrete non-relational operator
    classes (In/NotIn/Is/IsNot), chosen deterministically from the code.
  * the rewritten node <-> the model's Node record: "result is a Call node"
    <-> is_call; the called constructor name <-> rel_class (int code
    'Lt'<->100, 'Le'<->101, 'Gt'<->102, 'Ge'<->103, 'Ne'<->104, 'Eq'<->105,
    no-constructor <-> -1); the evaluate keyword value on a produced call
    <-> evaluate (an unchanged node carries no such keyword; the model's
    False on that branch bridges to "no evaluation is introduced", vacuous
    there and checked only on the call branch);
  * operand identity/order: the model's `Result().left is node.left` pin
    <-> "the rewritten node carries the two original operand objects in
    source order" (call branch: args[0]/args[1]; unchanged branch: the node
    itself, operands included). Operands are opaque in the model (Expr), so
    they are realized as leaf sub-expressions (number/name literals), on
    which the transformer's operand recursion is the identity — exactly the
    modeled domain per refinement.md row C.
  * `Node.op` on the call branch is model-side bookkeeping (the produced
    call carries the operator only via the constructor name); its oracle
    reading is rel-code-consistency on the call branch and the node's own
    operator on the unchanged branch.

Input domain: the Requires only demand a well-formed comparison node (one
operator, two operands), so every generated input is Requires-satisfying.

>= 1e5 Requires-satisfying inputs: 10 boundary cases + 100000 fuzz draws.
Pinned fuzz seed: 24661.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import ast
import json
import random
import sys

SEED = 24661
N_FUZZ = 100_000

# --- model.py constants (module header, verbatim) -----------------------------

OP_LT = 0
OP_LE = 1
OP_GT = 2
OP_GE = 3
OP_NE = 4
OP_EQ = 5

REL_LT = 100
REL_LE = 101
REL_GT = 102
REL_GE = 103
REL_NE = 104
REL_EQ = 105
REL_NONE = -1


# --- model.py carrier classes, contracts stripped ------------------------------

class Expr:
    def __init__(self):
        self.tag = 0


class Compare:
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right


class Node:
    def __init__(self, is_call, rel_class, evaluate, left, right, op):
        self.is_call = is_call
        self.rel_class = rel_class
        self.evaluate = evaluate
        self.left = left
        self.right = right
        self.op = op


# --- pure helpers from model.py, contracts stripped ----------------------------

def is_relational(op):
    return op == OP_LT or op == OP_LE or op == OP_GT or \
        op == OP_GE or op == OP_NE or op == OP_EQ


def rel_class_of(op):
    if op == OP_LT:
        return REL_LT
    if op == OP_LE:
        return REL_LE
    if op == OP_GT:
        return REL_GT
    if op == OP_GE:
        return REL_GE
    if op == OP_NE:
        return REL_NE
    if op == OP_EQ:
        return REL_EQ
    return REL_NONE


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def rewrite_comparison(node):
    if is_relational(node.op):
        sympy_class = rel_class_of(node.op)
        right = node.right
        left = node.left
        new_node = Node(True, sympy_class, False, left, right, node.op)
        return new_node
    return Node(False, REL_NONE, False, node.left, node.right, node.op)


# --- bridge: model op codes <-> syntax-node operator classes -------------------

RELATIONAL_AST = {
    OP_LT: ast.Lt,
    OP_LE: ast.LtE,
    OP_GT: ast.Gt,
    OP_GE: ast.GtE,
    OP_NE: ast.NotEq,
    OP_EQ: ast.Eq,
}

# the four concrete non-relational comparison-operator classes; a fuzzed model
# code >= 6 picks one deterministically (the model collapses them all)
NON_RELATIONAL_AST = [ast.In, ast.NotIn, ast.Is, ast.IsNot]

# constructor name <-> model constructor code
REL_NAME_TO_CODE = {
    "Lt": REL_LT,
    "Le": REL_LE,
    "Gt": REL_GT,
    "Ge": REL_GE,
    "Ne": REL_NE,
    "Eq": REL_EQ,
}


def ast_op_class(op_code):
    if op_code in RELATIONAL_AST:
        return RELATIONAL_AST[op_code]
    return NON_RELATIONAL_AST[op_code % len(NON_RELATIONAL_AST)]


def make_leaf(rng):
    """A leaf operand sub-expression (the model's opaque Expr carrier: the
    operand recursion is the identity on leaves, refinement.md row C)."""
    if rng.random() < 0.5:
        return ast.Constant(value=rng.randint(-10, 10))
    return ast.Name(id=rng.choice("xyzabc"), ctx=ast.Load())


def keyword_false(call_node):
    """Read the evaluation keyword off a produced call node; returns the
    keyword's value (expected False) or a sentinel if absent/odd."""
    for kw in call_node.keywords:
        if kw.arg == "evaluate":
            val = kw.value
            return getattr(val, "value", getattr(val, "n", "<?>"))
    return "<missing>"


def observe_real(transformer_cls, op_code, left_leaf, right_leaf):
    """Run the REAL rewrite on a comparison node built from the bridged
    operator class and the two leaf operands; read the result back through
    the bridge as a (is_call, rel_class, evaluate, left_ok, right_ok, op)
    tuple in model terms."""
    cmp_node = ast.Compare(left=left_leaf, ops=[ast_op_class(op_code)()],
                           comparators=[right_leaf])
    out = transformer_cls().visit_Compare(cmp_node)
    if isinstance(out, ast.Call):
        func = out.func
        name = func.id if isinstance(func, ast.Name) else "<?>"
        rel = REL_NAME_TO_CODE.get(name, "<?>")
        evaluate = keyword_false(out)
        left_ok = len(out.args) == 2 and out.args[0] is left_leaf
        right_ok = len(out.args) == 2 and out.args[1] is right_leaf
        # op is carried implicitly by the constructor name (bookkeeping field:
        # consistent iff the constructor matches the input operator's image)
        op_obs = op_code if rel == rel_class_of(op_code) else "<?>"
        return (True, rel, evaluate, left_ok, right_ok, op_obs)
    # unchanged branch: the node itself is returned, operands + operator intact
    is_same = out is cmp_node
    left_ok = is_same and out.left is left_leaf
    right_ok = is_same and out.comparators[0] is right_leaf
    op_obs = op_code if (is_same and
                         out.ops[0].__class__ is ast_op_class(op_code)) else "<?>"
    # no evaluation keyword exists on an unchanged node; the model's False on
    # this branch means "no evaluation introduced" — bridge it to False
    return (False, REL_NONE, False, left_ok, right_ok, op_obs)


def observe_shadow(op_code):
    l, r = Expr(), Expr()
    n = rewrite_comparison(Compare(op_code, l, r))
    return (n.is_call, n.rel_class, n.evaluate,
            n.left is l, n.right is r, n.op)


def check_one(transformer_cls, rng, op_code):
    left_leaf = make_leaf(rng)
    right_leaf = make_leaf(rng)
    shadow = observe_shadow(op_code)
    real = observe_real(transformer_cls, op_code, left_leaf, right_leaf)
    if shadow != real:
        print("DISAGREEMENT")
        print("  op_code=%r (operator class %s)"
              % (op_code, ast_op_class(op_code).__name__))
        print("  shadow (is_call, rel_class, evaluate, left_ok, right_ok, op) = %r"
              % (shadow,))
        print("  real   (is_call, rel_class, evaluate, left_ok, right_ok, op) = %r"
              % (real,))
        return False
    return True


def main():
    from sympy.parsing.sympy_parser import EvaluateFalseTransformer  # REAL patched callee

    rng = random.Random(SEED)

    # boundary: each of the six relational codes, and each of the four
    # non-relational operator classes (codes 6..9 cycle through them)
    boundary = [OP_LT, OP_LE, OP_GT, OP_GE, OP_NE, OP_EQ, 6, 7, 8, 9]
    checked = 0
    for code in boundary:
        if not check_one(EvaluateFalseTransformer, rng, code):
            return 1
        checked += 1

    for _ in range(N_FUZZ):
        # mostly the six relational codes; a healthy slice of non-relational
        # codes >= 6 (including large ones — the model collapses them all)
        if rng.random() < 0.6:
            code = rng.randint(0, 5)
        else:
            code = rng.randint(6, 10_000)
        if not check_one(EvaluateFalseTransformer, rng, code):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real comparison rewrite on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
