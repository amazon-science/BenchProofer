#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-16792 (nagini).

SHADOW: the impl region of model.py `pointer_flags`, copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped, plus
the @Pure helpers `shape_is_intrinsic` / `array_resolved` / `arg_is_pointer`
/ `want_pointer` copied over as plain functions. The carriers are plain
`List[int]` / `List[bool]` — no PSeq shim needed. There is no @ContractOnly
callee (the bundle consumes no axiom).

ORACLE: the REAL patched repo functions the model models per mapping.md —
`CodeGen.routine` (the caller-supplied argument-sequence handling) composed
with `CCodeGen.get_prototype` (the C prototype renderer), both in
`sympy/utilities/codegen.py`. The gate applies patch.diff to /testbed before
this script runs; PYTHONPATH=/testbed makes the patched code importable.

Type bridge (mapping.md §2): each requested argument is abstracted by a kind
tag (0 = plain scalar `Symbol`, 1 = fixed-shape `MatrixSymbol`,
2 = indexed-array `IndexedBase`) and a presence flag (does the symbol occur
in the wrapped expression). Each check materialises one real symbol per
(position, kind) from disjoint name pools, builds an expression containing
exactly the present symbols, runs the real `routine(...,
argument_sequence=...)` + `get_prototype`, and reads back the ordered
per-parameter pointer decision two independent ways that must agree: the
rendered parameter text (`*name` vs `name`) and the truthiness of the
argument's `dimensions` attribute. That ordered `List[bool]` is compared
`==` against the shadow's output.

Input domain (the model's Requires): len(kinds) == len(present) and every
kinds[i] in {0, 1, 2}. Boundary cases cover the empty sequence, every
(kind, presence) singleton, the exact failing-test shape (a matrix argument
absent from the expression), and mixed multi-argument sequences; fuzz draws
sequences of length 0..8 with independent per-position kind and presence.

>= 1e5 Requires-satisfying inputs: 21 boundary + 100000 fuzz cases.
Pinned fuzz seed: 167920.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

from sympy import MatrixSymbol, Symbol
from sympy.tensor.indexed import IndexedBase, Idx
from sympy.utilities.codegen import CCodeGen

SEED = 167920
N_FUZZ = 100_000

# kind tags (lock-step with model.py)
SCALAR = 0    # Symbol
MATRIX = 1    # MatrixSymbol
INDEXED = 2   # IndexedBase

MAX_ARGS = 8


# --- pure helpers from model.py, decorators + contracts stripped --------------

def shape_is_intrinsic(k):
    return k == 1


def array_resolved(k, present):
    if shape_is_intrinsic(k):
        return True
    if k == 2:
        return present
    return False


def arg_is_pointer(has_dims):
    return has_dims


def want_pointer(k, present):
    return arg_is_pointer(array_resolved(k, present))


# --- the impl region of model.py, verbatim (contract calls stripped) ----------

def pointer_flags(kinds, present):
    result = []  # type: list
    j = 0
    while j < len(kinds):
        k = kinds[j]
        is_present = present[j]
        # Resolve the argument's array-ness, then render the dimension flag.
        # A matrix is intrinsically an array and is given dimensions whether or
        # not it occurs in the expression. An indexed array is given dimensions
        # only when it occurs (its shape is recovered from the entries there).
        # A scalar never carries dimensions.
        if shape_is_intrinsic(k):
            has_dims = True
        elif k == 2:
            if is_present:
                has_dims = True
            else:
                has_dims = False
        else:
            has_dims = False
        flag = arg_is_pointer(has_dims)
        old_result = result
        result = result + [flag]
        j = j + 1
    return result


# --- oracle: the real patched routine + prototype renderer --------------------

IDX = Idx('cidx', 5)


def build_symbol(pos, kind, rng):
    """One real sympy symbol for position `pos` of kind `kind`. Name pools are
    disjoint across kinds and positions, so 'occurs in the expression' is
    controlled exactly by whether we add the symbol's term below."""
    if kind == SCALAR:
        return Symbol('cs_%d' % pos)
    if kind == MATRIX:
        return MatrixSymbol('cm_%d' % pos, rng.randint(1, 4), rng.randint(1, 4))
    return IndexedBase('cb_%d' % pos)


def present_term(sym, kind):
    """A term that makes `sym` occur in the wrapped expression."""
    if kind == SCALAR:
        return sym
    if kind == MATRIX:
        return sym[0, 0]
    return sym[IDX]


def printed_name(cg, sym):
    """The C-printed name a symbol appears under in the generated parameter
    list (an indexed-array symbol appears under its scalar label)."""
    if isinstance(sym, IndexedBase):
        return cg.printer.doprint(sym.label)
    return cg.printer.doprint(sym)


def real_pointer_flags(kinds, present, rng):
    """The REAL ordered per-argument pointer decision: build the routine for
    the requested argument sequence, render the C prototype, and read each
    parameter's pointer-ness two independent ways that must agree."""
    syms = [build_symbol(n, k, rng) for n, k in enumerate(kinds)]
    expr = 1.0
    for sym, k, p in zip(syms, kinds, present):
        if p:
            expr = expr + present_term(sym, k)
    cg = CCodeGen()
    routine = cg.routine('f', expr, argument_sequence=tuple(syms))
    proto = cg.get_prototype(routine)

    # (1) parse the rendered parameter list, in order
    inner = proto[proto.index('(') + 1:proto.rindex(')')]
    params = [p.strip() for p in inner.split(',')] if inner.strip() else []
    if len(params) != len(syms):
        raise AssertionError(
            "parameter count %d != requested %d in %r"
            % (len(params), len(syms), proto))
    by_render = []
    for n, (param, sym) in enumerate(zip(params, syms)):
        name = param.split()[-1].lstrip('*')
        expect_name = printed_name(cg, sym)
        if name != expect_name:
            raise AssertionError(
                "parameter %d is %r, expected name %r in %r"
                % (n, param, expect_name, proto))
        by_render.append('*' in param)

    # (2) the dimensions attribute the renderer consults, per argument
    by_dims = [bool(arg.dimensions) for arg in routine.arguments]
    if by_render != by_dims:
        raise AssertionError(
            "renderer inconsistent: proto=%r render=%r dims=%r"
            % (proto, by_render, by_dims))
    return by_render


def check_case(kinds, present, rng, label):
    shadow_out = pointer_flags(kinds, present)
    real_out = real_pointer_flags(kinds, present, rng)
    if shadow_out != real_out:
        return ("DISAGREEMENT [%s]\n"
                "  kinds=%r\n  present=%r\n"
                "  shadow=%r\n  real=%r"
                % (label, kinds, present, shadow_out, real_out))
    return None


def boundary_cases():
    """(kinds, present, label) triples over the model's input domain."""
    return [
        ([], [], "empty sequence"),
        ([MATRIX], [False], "matrix absent (the failing-test shape)"),
        ([MATRIX], [True], "matrix present"),
        ([SCALAR], [False], "scalar absent"),
        ([SCALAR], [True], "scalar present"),
        ([INDEXED], [False], "indexed absent"),
        ([INDEXED], [True], "indexed present"),
        ([MATRIX, SCALAR], [False, True], "matrix absent + scalar present"),
        ([MATRIX, SCALAR], [True, True], "matrix + scalar both present"),
        ([INDEXED, SCALAR], [False, True], "indexed absent + scalar present"),
        ([MATRIX, MATRIX], [False, False], "two matrices both absent"),
        ([SCALAR, SCALAR], [True, True], "two scalars present"),
        ([INDEXED, INDEXED], [False, True], "indexed absent + indexed present"),
        ([MATRIX, SCALAR, MATRIX, INDEXED], [False, True, False, True],
         "mixed: matrices absent, scalar + indexed present"),
        ([SCALAR, MATRIX, INDEXED], [False, False, False], "all kinds absent"),
        ([SCALAR, MATRIX, INDEXED], [True, True, True], "all kinds present"),
        ([INDEXED, MATRIX, SCALAR], [True, False, False],
         "indexed present + matrix absent + scalar absent"),
        ([MATRIX] * 5, [False] * 5, "five matrices all absent"),
        ([INDEXED] * 4, [False, True, False, True], "alternating indexed"),
        ([SCALAR] * 8, [True] * 8, "max-width scalars"),
        ([MATRIX, INDEXED] * 4, [False, False] * 4, "max-width arrays absent"),
    ]


def rand_case(rng):
    size = rng.randint(0, MAX_ARGS)
    kinds = [rng.choice([SCALAR, MATRIX, INDEXED]) for _ in range(size)]
    present = [rng.random() < 0.5 for _ in range(size)]
    return kinds, present


def main():
    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0
    for kinds, present, label in boundary_cases():
        err = check_case(kinds, present, rng, label)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    for trial in range(N_FUZZ):
        kinds, present = rand_case(rng)
        err = check_case(kinds, present, rng, "fuzz#%d" % trial)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow pointer_flags == real routine+get_prototype "
          "pointer decisions on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "no @ContractOnly callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
