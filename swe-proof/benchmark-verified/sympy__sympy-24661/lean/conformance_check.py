#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-24661.

The bundle models ONE routine: the comparison-rewrite the patch adds to
`EvaluateFalseTransformer` (the new `visit_Compare`, mapping.md). For a single
comparison `cmp(left, op, right)`,

    - if `op` is one of the six recognised relational operators
      (Lt/Le/Gt/Ge/Eq/Ne), produce a call to that operator's constructor on the
      recursively-rewritten operands, with the "do not evaluate" flag set;
    - otherwise return the comparison node unchanged.

ORACLE PROVENANCE. The ORACLE is the REAL callee: this script imports
`EvaluateFalseTransformer` from the patched repo and invokes its bound
`visit_Compare` on a genuine `ast.Compare` node built from the fuzzed model
input. It does NOT re-implement the method. That matters, and it is the reason
this script was re-authored: an earlier revision had `oracle()` and `shadow()`
both call the same local `transform()` helper, which was itself the
transliteration of the Lean `transform`. A shadow cannot refute the helper it
shares, so that revision reported disagreements=0 while the model's `transform`
was the IDENTITY on call nodes and the real `self.visit` dispatch was not.
Driving the imported class closes the hole: the recursive dispatch (the call
handler, which rewrites the arguments and attaches the flag for a
non-evaluating callee) is exercised for real on every fuzzed input.

The SHADOW remains the op-for-op transliteration of
`implementation_transformRelational` (Solution.lean impl region) together with
the modeled `transform`/`transformArgs`, per refinement.md.

The model<->ast correspondence used to cross the boundary is mapping.md §2's
bijection, implemented by `to_ast` / `from_ast` below and applied in BOTH
directions so the comparison is between values of the same type.

This genuinely tests the soundness-critical clause: a recognised relational
comparison (e.g. `1 < 2`) must be rebuilt as the unevaluated relational call
`Lt(1, 2, evaluate=False)` — matching the F2P expectations (`test_issue_24288`)
— rather than left as a bare comparison node (the pre-patch bug, which evaluates
to a boolean).

stdlib-only (plus the repo under test). Pinned seed: 24661 (also in mapping.md).
"""
import ast
import random
import sys

SEED = 24661
N = 120_000

# RelOp <-> constructor-name table (mapping.md bijection). `other` -> None.
REL_OPS = ["lt", "le", "gt", "ge", "eq", "ne", "other"]
REL_CLASS = {
    "lt": "Lt", "le": "Le", "gt": "Gt", "ge": "Ge", "eq": "Eq", "ne": "Ne",
    "other": None,
}
# mapping.md §2: the comparison-operator class each RelOp denotes. `other` is
# witnessed by `ast.Is` — any operator outside the recognised table behaves the
# same way, since the only thing the method asks is whether it IS in the table.
OP_CLASS = {
    "lt": ast.Lt, "le": ast.LtE, "gt": ast.Gt, "ge": ast.GtE,
    "eq": ast.Eq, "ne": ast.NotEq, "other": ast.Is,
}
OP_CLASS_INV = {v: k for k, v in OP_CLASS.items()}

# AstNode is encoded as a tuple tagged by its head:
#   ("const", n)
#   ("name", s)
#   ("app", func, args_list, eval_false_bool)
#   ("cmp", left, op, right)


def rel_class_name(op):
    return REL_CLASS[op]


# --- the model's recursive rewrite (`transform` / `transformArgs`) -------------
# Mirrors Solution.lean's pure region exactly, INCLUDING the call arm: the
# arguments are each rewritten, and the flag is set when the callee is one of the
# non-evaluating names (else it keeps the flag it already carried).
NON_EVALUATING_FUNCS = (
    'Abs', 'im', 're', 'sign', 'arg', 'conjugate',
    'acos', 'acot', 'acsc', 'asec', 'asin', 'atan',
    'acosh', 'acoth', 'acsch', 'asech', 'asinh', 'atanh',
    'cos', 'cot', 'csc', 'sec', 'sin', 'tan',
    'cosh', 'coth', 'csch', 'sech', 'sinh', 'tanh',
    'exp', 'ln', 'log', 'sqrt', 'cbrt',
)


def is_non_evaluating_func(f):
    return f in NON_EVALUATING_FUNCS


def transform(node):
    tag = node[0]
    if tag == "const":
        return node
    if tag == "name":
        return node
    if tag == "app":
        _, func, args, eval_false = node
        return ("app", func, transform_args(args),
                eval_false or is_non_evaluating_func(func))
    if tag == "cmp":
        _, left, op, right = node
        cls = rel_class_name(op)
        if cls is not None:
            return ("app", cls, [transform(left), transform(right)], True)
        return ("cmp", left, op, right)
    raise ValueError(f"bad node {node!r}")


def transform_args(args):
    return [transform(a) for a in args]


# --- mapping.md §2 bridge: model node <-> real ast node ------------------------
def to_ast(n):
    tag = n[0]
    if tag == "const":
        return ast.Constant(value=n[1])
    if tag == "name":
        return ast.Name(id=n[1], ctx=ast.Load())
    if tag == "app":
        _, func, args, eval_false = n
        kw = ([ast.keyword(arg='evaluate', value=ast.Constant(value=False))]
              if eval_false else [])
        return ast.Call(func=ast.Name(id=func, ctx=ast.Load()),
                        args=[to_ast(a) for a in args], keywords=kw)
    if tag == "cmp":
        _, left, op, right = n
        return ast.Compare(left=to_ast(left), ops=[OP_CLASS[op]()],
                           comparators=[to_ast(right)])
    raise ValueError(f"bad node {n!r}")


def from_ast(a):
    if isinstance(a, ast.Constant) and isinstance(a.value, int) \
            and not isinstance(a.value, bool):
        return ("const", a.value)
    if isinstance(a, ast.Name):
        return ("name", a.id)
    if isinstance(a, ast.Call):
        if not isinstance(a.func, ast.Name):
            raise ValueError("unsupported callee shape")
        eval_false = any(
            k.arg == 'evaluate' and isinstance(k.value, ast.Constant)
            and k.value.value is False for k in a.keywords)
        return ("app", a.func.id, [from_ast(x) for x in a.args], eval_false)
    if isinstance(a, ast.Compare):
        return ("cmp", from_ast(a.left), OP_CLASS_INV[a.ops[0].__class__],
                from_ast(a.comparators[0]))
    raise ValueError(f"unsupported node {ast.dump(a)}")


# --- ORACLE: the REAL patched callee, driven on the modeled arguments ----------
def oracle(left, op, right):
    from sympy.parsing.sympy_parser import EvaluateFalseTransformer
    node = ast.Compare(left=to_ast(left), ops=[OP_CLASS[op]()],
                       comparators=[to_ast(right)])
    return from_ast(EvaluateFalseTransformer().visit_Compare(node))


# --- SHADOW of implementation_transformRelational (the R/I leg) -----------------
# Mirrors Solution.lean impl region exactly: match the table, bind right' then
# left', build app cls [left', right'] true; else return the cmp node.
def shadow(left, op, right):
    cls = rel_class_name(op)
    if cls is not None:
        right_p = transform(right)
        left_p = transform(left)
        return ("app", cls, [left_p, right_p], True)
    else:
        return ("cmp", left, op, right)


def disagree(left, op, right):
    got = oracle(left, op, right)
    want = shadow(left, op, right)
    if got != want:
        return ((left, op, right), got, want)
    return None


def rand_atom(rng):
    if rng.random() < 0.5:
        return ("const", rng.randint(-5, 5))
    return ("name", rng.choice(["x", "y", "z", "a", "b"]))


# Callee names are drawn from BOTH sides of the non-evaluating table, plus the
# relational constructor names themselves (a rewrite-output shape reappearing as
# an operand), so the flag arm is exercised in both directions.
FUNC_POOL = (list(NON_EVALUATING_FUNCS)
             + ["f", "g", "h", "Add", "Mul", "Rel", "Lt", "Eq"])


def rand_operand(rng, depth):
    r = rng.random()
    if depth <= 0 or r < 0.45:
        return rand_atom(rng)
    if r < 0.75:
        # a call node: arity 0..2, callee possibly non-evaluating, flag possibly
        # already set — the arm an identity-on-call model gets wrong.
        return ("app", rng.choice(FUNC_POOL),
                [rand_operand(rng, depth - 1)
                 for _ in range(rng.randint(0, 2))],
                rng.random() < 0.3)
    # a nested comparison
    return ("cmp", rand_operand(rng, depth - 1), rng.choice(REL_OPS),
            rand_operand(rng, depth - 1))


# Hand-picked cases that pin the call arm — the branch a shadow sharing the
# model's helper cannot see. Each is an ordinary in-scope operand shape.
HAND = [
    # non-evaluating callee as an operand: the flag is attached
    (("app", "sin", [("name", "x")], False), "lt", ("const", 3)),
    # ordinary callee: the flag is NOT attached, but arguments are rewritten
    (("app", "f", [("cmp", ("const", 1), "lt", ("const", 2))], False),
     "lt", ("const", 3)),
    # ordinary callee wrapping a non-evaluating one
    (("app", "g", [("app", "sin", [("name", "y")], False)], False),
     "lt", ("const", 1)),
    # ordinary callee, atomic argument: nothing changes
    (("app", "f", [("name", "x")], False), "lt", ("const", 3)),
    # flag already present on a non-evaluating callee
    (("app", "sin", [("name", "x")], True), "lt", ("const", 3)),
    # zero-arity non-evaluating callee
    (("app", "sin", [], False), "lt", ("const", 3)),
    # both operands are calls, both non-evaluating, one with a nested cmp
    (("app", "cbrt", [("name", "x")], False), "le",
     ("app", "exp", [("cmp", ("const", 1), "lt", ("const", 2))], False)),
    # deep mixed nesting
    (("app", "f", [("app", "g", [("cmp", ("const", 1), "lt", ("const", 2))],
                    False), ("app", "sin", [("name", "x")], False)], False),
     "gt", ("const", 3)),
    # unrecognised operator: operands must be left ENTIRELY alone
    (("app", "sin", [("cmp", ("const", 1), "lt", ("const", 2))], False),
     "other", ("name", "y")),
    # nested comparison operand under a recognised operator
    (("cmp", ("const", 1), "lt", ("const", 2)), "ne", ("const", 3)),
    # chain of non-evaluating callees
    (("app", "log", [("app", "sqrt", [("name", "x")], False)], False),
     "ne", ("const", 0)),
    # negative literal against an identifier (atoms only)
    (("const", -5), "lt", ("name", "x")),
]


def main() -> int:
    checked = 0

    # F2P edge cases: the six literals `1 ⊙ 2`.
    one, two = ("const", 1), ("const", 2)
    for op, cls in [("lt", "Lt"), ("le", "Le"), ("gt", "Gt"),
                    ("ge", "Ge"), ("ne", "Ne"), ("eq", "Eq")]:
        d = disagree(one, op, two)
        if d:
            print(f"DISAGREE f2p {op}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        # also assert the oracle yields exactly the expected unevaluated call
        assert oracle(one, op, two) == ("app", cls, [one, two], True)
        checked += 1
    # an unrecognised comparison operator returns the node unchanged.
    d = disagree(one, "other", two)
    if d:
        print(f"DISAGREE other: oracle={d[1]} shadow={d[2]}")
        print("status=fail")
        return 1
    checked += 1

    for left, op, right in HAND:
        d = disagree(left, op, right)
        if d:
            print(f"DISAGREE hand: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        op = rng.choice(REL_OPS)
        left = rand_operand(rng, depth=3)
        right = rand_operand(rng, depth=3)
        d = disagree(left, op, right)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
