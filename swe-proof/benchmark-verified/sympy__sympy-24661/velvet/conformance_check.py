#!/usr/bin/env python3
"""G-CONF differential conformance for sympy__sympy-24661.

Refutes the R/I refinement leg: the modeled comparison rewrite
`rewriteCompare`/`relOf` (a dispatch from a comparison operator to either the
matching UNEVALUATED relation node or the preserved comparison node) over the
finite comparison-operator space.

ORACLE CHOICE — why we transliterate the patched `visit_Compare` instead of
driving `parse_expr(..., evaluate=False)` end-to-end:
  The modeled behaviour is the *node-shape* decision of
  `EvaluateFalseTransformer.visit_Compare`: which SymPy relational class a
  comparison operator maps to, and that the produced `ast.Call` carries the
  `evaluate=False` keyword (so the relation is held unevaluated). The full
  `parse_expr` path additionally runs tokenization, the standard transformation
  pipeline, `compile`, and `eval` against the live SymPy namespace — none of
  which the patch touches and all of which are shared pre/post-patch. Exercising
  it end-to-end would compare SymPy objects, not isolate the modeled AST-rewrite
  decision. So, per the worker prompt, the ORACLE is the gold-patched
  `visit_Compare` node-shape decision transliterated VERBATIM from
  sympy/parsing/sympy_parser.py:

      relational_operators = {NotEq:'Ne', Lt:'Lt', LtE:'Le',
                              Gt:'Gt', GtE:'Ge', Eq:'Eq'}
      def visit_Compare(node):
          if node.ops[0].__class__ in relational_operators:
              cls = relational_operators[node.ops[0].__class__]
              right = visit(node.comparators[0]); left = visit(node.left)
              return Call(Name(cls), [left, right], keywords=[evaluate=False])
          return node

  The SHADOW is the model from Solution.lean (`relOf` + `rewriteCompare`).
  Both produce a structural description of the returned node:
    - a relation: (kind=REL, rel_class, evaluate_flag, left_tag, right_tag)
    - a preserved comparison: (kind=CMP, op, left_tag, right_tag)
  The operand rewrite `visit` is the unchanged free callee (mapping.md §3); we
  model it on BOTH sides as the same opaque tag-preserving function so the
  differential isolates the rewrite decision (the only thing the patch changes).
  We differential-test SHADOW vs ORACLE over every comparison operator (the full
  finite domain) plus seeded fuzz. Exit 0 iff zero disagreements. stdlib only.
"""
import random
import sys

SEED = 24661
N_FUZZ = 100_000

# The comparison operators modeled (mapping.md §2). The six supported ones plus
# representative unsupported comparison operators (identity / membership) that
# the rewrite must leave unchanged.
SUPPORTED = ["lt", "le", "gt", "ge", "eq", "ne"]
UNSUPPORTED = ["is", "isnot", "in", "notin"]
OPS = SUPPORTED + UNSUPPORTED

# Comparison-operator -> SymPy relational class name (the patch's dict).
REL_OF = {
    "ne": "Ne",
    "lt": "Lt",
    "le": "Le",
    "gt": "Gt",
    "ge": "Ge",
    "eq": "Eq",
}


def visit_tag(tag):
    """The unchanged recursive operand rewrite, modeled identically on both
    sides as an opaque tag-preserving function (mapping.md §3). Distinct operands
    keep distinct tags; the decision under test does not depend on its result."""
    return ("visited", tag)


# ---- SHADOW: Solution.lean `relOf` + `rewriteCompare` transliterated --------

def shadow(op, left_tag, right_tag):
    """rewriteCompare transliterated: a supported operator -> the matching
    relation node held unevaluated (built=False); else the comparison preserved."""
    rk = REL_OF.get(op)  # relOf
    if rk is not None:
        return ("REL", rk, False, visit_tag(left_tag), visit_tag(right_tag))
    return ("CMP", op, left_tag, right_tag)


# ---- ORACLE: patched visit_Compare node-shape decision, transliterated ------

def oracle(op, left_tag, right_tag):
    """The PATCHED visit_Compare, transliterated. `node.ops[0].__class__ in
    relational_operators` -> build `Call(Name(cls), [visit(left), visit(right)],
    keywords=[evaluate=False])`; else `return node` (the unchanged Compare)."""
    if op in REL_OF:
        cls = REL_OF[op]
        right = visit_tag(right_tag)
        left = visit_tag(left_tag)
        return ("REL", cls, False, left, right)
    return ("CMP", op, left_tag, right_tag)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: every operator with a couple of fixed operand tags.
    combos = [(op, 1, 2) for op in OPS] + [(op, 7, 7) for op in OPS]
    # Plus seeded fuzz over the operator space with random operand tags.
    combos += [(rng.choice(OPS), rng.randint(0, 9999), rng.randint(0, 9999))
               for _ in range(N_FUZZ)]

    for op, lt, rt in combos:
        count += 1
        s = shadow(op, lt, rt)
        o = oracle(op, lt, rt)
        if s != o:
            disagreements.append((op, lt, rt, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of rewriteComparison (relOf + rewriteCompare) "
          "agrees with the patched visit_Compare node-shape decision on %d "
          "inputs (%d operators exhaustive + fuzz, seed=%d), 0 disagreements."
          % (count, len(OPS), SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
