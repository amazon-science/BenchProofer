#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-16792.

Runs the REAL sympy code-generation callees (`CCodeGen.routine`,
`CCodeGen.get_prototype`, and the end-to-end `codegen(...)`) and asserts that
the model's deep abstraction matches reality, namely:

  (A-reference) the deep model of array-ness (`shape_is_intrinsic`,
      `array_resolved`) and of the C prototype's pointer rendering
      (`arg_is_pointer`) — see model.py — agree with the real shape/dimension
      computation and the real `CCodeGen.get_prototype`. Concretely an argument
      of the generated routine is declared a POINTER (`*name`) in the C
      prototype iff `want_pointer(kind, present)` holds, where:

        * a matrix argument (MatrixSymbol)  -> pointer ALWAYS (present OR
          absent from the wrapped expression);
        * an indexed-array argument (IndexedBase) -> pointer iff it appears in
          the expression (when passed in argument_sequence it is normalised to
          its scalar label, so an ABSENT indexed array is NOT promoted);
        * a scalar argument (Symbol)        -> never a pointer.

There is no consumed @ContractOnly axiom; this validates the deep model.

The exact FAIL_TO_PASS scenario (`test_ccode_unused_array_arg`) is checked
first, then a boundary + randomized fuzz over argument sequences mixing the
three kinds, each present / absent in the expression.

Imports only sympy (the module under change). Exit 0 iff every obligation
holds.
"""
import random
import sys

from sympy import MatrixSymbol, Symbol
from sympy.tensor.indexed import IndexedBase, Idx
from sympy.utilities.codegen import codegen, CCodeGen


# kind tags (lock-step with model.py)
SCALAR = 0    # Symbol
MATRIX = 1    # MatrixSymbol
INDEXED = 2   # IndexedBase


# --- model.py reference encodings (kept in lock-step with the @Pure region) ---

def shape_is_intrinsic(k):
    return k == MATRIX


def array_resolved(k, present):
    if shape_is_intrinsic(k):
        return True
    if k == INDEXED:
        return bool(present)
    return False


def arg_is_pointer(has_dims):
    return bool(has_dims)


def want_pointer(k, present):
    return arg_is_pointer(array_resolved(k, present))


# --- helpers over the REAL callees -------------------------------------------

def printed_name(cg, sym):
    """The C-printed name a symbol appears under in the generated arguments.
    An IndexedBase is normalised to its scalar label inside routine()."""
    if isinstance(sym, IndexedBase):
        return cg.printer.doprint(sym.label)
    return cg.printer.doprint(sym)


def real_arg_is_pointer(cg, routine, arg):
    """The REAL pointer decision for one argument, read two independent ways
    that must agree: (1) the prototype string emitted by get_prototype, and
    (2) the dimensions attribute the prototype consults."""
    name = cg.printer.doprint(arg.name)
    proto = cg.get_prototype(routine)
    pointer_in_proto = ("*" + name) in proto
    pointer_by_dims = bool(arg.dimensions)
    assert pointer_in_proto == pointer_by_dims, (
        "real renderer inconsistent for %r: proto=%r dims=%r"
        % (name, proto, arg.dimensions))
    return pointer_in_proto


def check_scenario(arg_symbols, kinds, present_flags, expr, label):
    """Build the real routine for `argument_sequence=arg_symbols` and assert
    every emitted argument is a pointer iff the model says it should be, and
    that the modelled `present` flag matches the real presence in the expr."""
    cg = CCodeGen()
    routine = cg.routine('f', expr, argument_sequence=tuple(arg_symbols))
    by_name = {}
    for arg in routine.arguments:
        by_name[cg.printer.doprint(arg.name)] = arg
    for sym, k, present in zip(arg_symbols, kinds, present_flags):
        nm = printed_name(cg, sym)
        assert nm in by_name, (
            "[%s] requested symbol %r missing from generated arguments %r"
            % (label, nm, list(by_name)))
        observed = real_arg_is_pointer(cg, routine, by_name[nm])
        expected = want_pointer(k, present)
        assert observed == expected, (
            "[%s] pointer mismatch for %r (kind=%d present=%s): real=%s model=%s"
            % (label, nm, k, present, observed, expected))


def main():
    # --- 1. The exact FAIL_TO_PASS scenario -------------------------------
    x = MatrixSymbol('x', 2, 1)
    gen = CCodeGen()
    result = codegen(("test", 1.0), code_gen=gen, header=False, empty=False,
                     argument_sequence=(x,))
    source = result[0][1]
    expected = (
        '#include "test.h"\n'
        '#include <math.h>\n'
        'double test(double *x) {\n'
        '   double test_result;\n'
        '   test_result = 1.0;\n'
        '   return test_result;\n'
        '}\n'
    )
    assert source == expected, (
        "FAIL_TO_PASS scenario mismatch:\n--- got ---\n%s\n--- want ---\n%s"
        % (source, expected))

    # --- 2. Boundary scenarios: every (kind, present?) combination --------
    a = Symbol('a')
    b = Symbol('b')
    M = MatrixSymbol('M', 2, 1)
    N = MatrixSymbol('N', 3, 2)
    A = IndexedBase('A')
    B = IndexedBase('B')
    i = Idx('i', 3)

    boundary = [
        # (symbols, kinds, present_flags, expr, label)
        ([M], [MATRIX], [False], 1.0, "matrix absent (F2P shape)"),
        ([M], [MATRIX], [True], M[0, 0], "matrix present"),
        ([a], [SCALAR], [False], 1.0, "scalar absent"),
        ([a], [SCALAR], [True], a, "scalar present"),
        ([A], [INDEXED], [False], 1.0, "indexed absent (NOT promoted)"),
        ([A], [INDEXED], [True], A[i], "indexed present"),
        ([M, a], [MATRIX, SCALAR], [False, True], a, "matrix absent + scalar present"),
        ([M, a], [MATRIX, SCALAR], [True, True], M[0, 0] + a, "matrix+scalar present"),
        ([A, a], [INDEXED, SCALAR], [False, True], a, "indexed absent + scalar present"),
        ([N, M], [MATRIX, MATRIX], [False, False], 1.0, "two matrices both absent"),
        ([b, a], [SCALAR, SCALAR], [True, True], a + b, "two scalars present"),
        ([M, a, N, A], [MATRIX, SCALAR, MATRIX, INDEXED], [False, True, False, True],
            a + A[i], "mixed: matrices absent, scalar+indexed present"),
        ([B, A], [INDEXED, INDEXED], [False, True], A[i], "indexed absent + indexed present"),
    ]
    for syms, kinds, present, expr, label in boundary:
        check_scenario(syms, kinds, present, expr, label)

    # --- 3. Randomized fuzz -----------------------------------------------
    rng = random.Random(16792)
    idx = Idx('j', 5)

    for trial in range(400):
        # build a fresh, distinct pool per trial (avoids name collisions)
        syms = []
        kinds = []
        size = rng.randint(1, 6)
        for n in range(size):
            kind = rng.choice([SCALAR, MATRIX, INDEXED])
            if kind == SCALAR:
                syms.append(Symbol('s_%d_%d' % (trial, n)))
            elif kind == MATRIX:
                syms.append(MatrixSymbol('m_%d_%d' % (trial, n),
                                         rng.randint(1, 4), rng.randint(1, 4)))
            else:
                syms.append(IndexedBase('b_%d_%d' % (trial, n)))
            kinds.append(kind)

        # Decide presence per symbol and build a matching expression.
        present = []
        terms = []
        for s, k in zip(syms, kinds):
            is_present = rng.random() < 0.5
            present.append(is_present)
            if is_present:
                if k == SCALAR:
                    terms.append(s)
                elif k == MATRIX:
                    terms.append(s[0, 0])
                else:
                    terms.append(s[idx])
        expr = 1.0
        for t in terms:
            expr = expr + t
        check_scenario(syms, kinds, present, expr, "fuzz#%d" % trial)

    print("G-AX OK: deep model (matrix => pointer always; indexed => pointer "
          "iff present; scalar => never) matches the real sympy CCodeGen on "
          "the F2P scenario + %d boundary + 400 fuzz argument sequences."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
