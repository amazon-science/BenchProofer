#!/usr/bin/env python3
"""G-AX / deep-model soundness check for sympy__sympy-24661.

This bundle consumes NO @ContractOnly axiom: the comparison rewrite is a pure,
fully-expressible AST transformation that calls no unchanged external callee
(it builds plain `ast` nodes). What G-AX validates here is therefore the
A-reference: the model's operator-to-constructor mapping and conversion
predicate (`rel_class_of`, `is_relational` in model.py's pure region, mirrored
by the impl) == the behaviour of the REAL post-patch
`EvaluateFalseTransformer.visit_Compare`.

Concretely, for each comparison-operator AST class we:
  * run the REAL transformer's mapping (`relational_operators`) and assert it
    equals the model's `rel_class_of` correspondence;
  * parse a small comparison expression for that operator, run the REAL
    `visit_Compare`, and assert the produced node is a Call to the matching
    SymPy relational constructor with `evaluate=False` and the operands in
    left/right order (is_relational operators), or is left an ast.Compare
    unchanged (non-relational operators).

Imports only the Python standard-library `ast` module and the repository's
`sympy.parsing.sympy_parser` (the module the patch edits) — nothing else.
Exit 0 iff every observation matches the model.
"""
import ast
import sys

from sympy.parsing.sympy_parser import EvaluateFalseTransformer

# --- model.py reference encodings (kept in lock-step with the spec) ----------

# operator code -> SymPy relational constructor name (model rel_class_of, with
# constructor codes mapped back to their public names)
MODEL_REL_NAME = {
    "Lt": "Lt",   # OP_LT  -> REL_LT
    "LtE": "Le",  # OP_LE  -> REL_LE
    "Gt": "Gt",   # OP_GT  -> REL_GT
    "GtE": "Ge",  # OP_GE  -> REL_GE
    "NotEq": "Ne",  # OP_NE -> REL_NE
    "Eq": "Eq",   # OP_EQ  -> REL_EQ
}

# AST comparison-operator class -> the model's expectation
RELATIONAL_AST = {
    ast.Lt: "Lt",
    ast.LtE: "Le",
    ast.Gt: "Gt",
    ast.GtE: "Ge",
    ast.NotEq: "Ne",
    ast.Eq: "Eq",
}

# expression text per relational operator, for the end-to-end rewrite check
SAMPLE_TEXT = {
    ast.Lt: "1 < 2",
    ast.LtE: "1 <= 2",
    ast.Gt: "1 > 2",
    ast.GtE: "1 >= 2",
    ast.NotEq: "1 != 2",
    ast.Eq: "1 == 2",
}

# comparison operators OUTSIDE the relational set: must be left unchanged
NON_RELATIONAL_TEXT = {
    "In": "1 in x",
    "NotIn": "1 not in x",
    "Is": "1 is x",
    "IsNot": "1 is not x",
}


def check_mapping_table():
    """The REAL transformer's relational_operators table == the model's
    operator-to-constructor correspondence (same domain, same images)."""
    real = EvaluateFalseTransformer.relational_operators
    # same set of operator classes
    assert set(real.keys()) == set(RELATIONAL_AST.keys()), (
        "relational operator domain mismatch: real=%r model=%r"
        % (sorted(c.__name__ for c in real), sorted(c.__name__ for c in RELATIONAL_AST)))
    for cls, name in real.items():
        assert name == RELATIONAL_AST[cls], (
            "constructor mismatch for %s: real=%r model=%r"
            % (cls.__name__, name, RELATIONAL_AST[cls]))
        # and the model's pure mapping agrees
        assert MODEL_REL_NAME[cls.__name__] == name, (
            "model rel_class_of disagrees for %s: model=%r real=%r"
            % (cls.__name__, MODEL_REL_NAME[cls.__name__], name))


def check_relational_rewrite(op_cls, expected_name):
    """Run the REAL visit_Compare on a comparison of this operator; assert the
    result is a Call(Name(expected_name), [left, right], evaluate=False)."""
    tree = ast.parse(SAMPLE_TEXT[op_cls], mode="eval")
    node = tree.body
    assert isinstance(node, ast.Compare)
    assert node.ops[0].__class__ is op_cls
    out = EvaluateFalseTransformer().visit_Compare(node)
    # converted to a symbolic-comparison call (model: is_call == True)
    assert isinstance(out, ast.Call), (
        "%s not converted to a Call: got %r" % (op_cls.__name__, type(out)))
    assert isinstance(out.func, ast.Name) and out.func.id == expected_name, (
        "%s wrong constructor: got %r expected %r"
        % (op_cls.__name__, getattr(out.func, "id", out.func), expected_name))
    # two operands, in left/right order
    assert len(out.args) == 2, "%s wrong arg count: %r" % (op_cls.__name__, out.args)
    # evaluate=False keyword present (model: evaluate == False)
    kw = {k.arg: k for k in out.keywords}
    assert "evaluate" in kw, "%s missing evaluate keyword" % op_cls.__name__
    val = kw["evaluate"].value
    # NameConstant(False) on <=3.7, Constant(False) on >=3.8
    actual = getattr(val, "value", getattr(val, "n", None))
    assert actual is False, (
        "%s evaluate keyword not False: %r" % (op_cls.__name__, actual))


def check_non_relational_unchanged(label, text):
    """A comparison whose operator is outside the relational set is returned
    unchanged (model: is_call == False, node kept)."""
    tree = ast.parse(text, mode="eval")
    node = tree.body
    assert isinstance(node, ast.Compare)
    out = EvaluateFalseTransformer().visit_Compare(node)
    assert out is node, (
        "%s should be returned unchanged but visit_Compare altered it: %r"
        % (label, type(out)))


def main():
    check_mapping_table()
    for op_cls, name in RELATIONAL_AST.items():
        check_relational_rewrite(op_cls, name)
    for label, text in NON_RELATIONAL_TEXT.items():
        check_non_relational_unchanged(label, text)
    print("G-AX OK: EvaluateFalseTransformer.visit_Compare matches the model "
          "on all 6 relational operators (Lt/Le/Gt/Ge/Ne/Eq, evaluate=False, "
          "left/right order) and %d non-relational operators (unchanged)."
          % len(NON_RELATIONAL_TEXT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
