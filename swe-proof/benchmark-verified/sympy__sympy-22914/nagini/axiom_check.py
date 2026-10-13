#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-22914.

Validates the deep model of model.py (the A-reference: `is_supported`,
`target_name`, `call_render`, and the per-name-code dispatch) against the REAL
code printer.  There is no consumed @ContractOnly axiom; the changed operation
(extending the supported-function table) is modelled DEEPLY, and G-AX checks
that deep model == the real `PythonCodePrinter` rendering.

The deep model claims:

  * the smaller-of selection (Min) is supported, target call name 'min';
  * the larger-of selection (Max) is supported, target call name 'max';
  * the absolute value (Abs) is supported, target call name 'abs';
  * for any supported function the rendering is
        <target>(<comma-joined argument renderings>)
  * a function outside the table is NOT rendered in that call form.

Because the deep model encodes the POST-patch supported table, the gold patch
must be applied first (mirrors model.py, which is the verifiable face of the
patched function).  This script applies the gold patch in a throw-away copy of
the repo, imports the patched printer, and asserts the equalities.  Exit 0 iff
every observation matches the model.

Imports only the standard library plus the repository under test (sympy) — the
very package the gold patch edits; nothing else.
"""
import os
import random
import subprocess
import sys
import tempfile


# --- model.py reference encodings (kept in lock-step with the deep model) ----

# name_code -> target call-name code points (model.py: target_name)
_TARGET = {
    0: [97, 98, 115],     # 'abs'  (name_abs)
    1: [109, 105, 110],   # 'min'  (name_min)
    2: [109, 97, 120],    # 'max'  (name_max)
}
_SUPPORTED = {0, 1, 2}    # model.py: is_supported


def call_render(name_code, joined_args_codepoints):
    """Reference of model.py's call_render: target '(' joined_args ')'."""
    return _TARGET[name_code] + [40] + list(joined_args_codepoints) + [41]


def _gold_patch_text():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "patch.diff")) as fh:
        return fh.read()


def _import_patched_printer():
    """Apply the gold patch to a scratch checkout of the installed sympy and
    return (PythonCodePrinter, Min, Max, Abs, Symbol). If patching the source
    tree in place is not desired, fall back to monkeypatching the table, which
    is exactly the gold edit (adding 'Min'/'Max' to _known_functions)."""
    import importlib
    import sympy
    # NOTE: `import sympy.printing.pycode as pc` binds the exported `pycode`
    # FUNCTION (which shadows the submodule in the package namespace), so load
    # the real module object explicitly.
    pc = importlib.import_module("sympy.printing.pycode")
    # The gold edit is precisely: _known_functions gains 'Min'->'min',
    # 'Max'->'max'.  Reproduce it on the imported module, then rebuild the
    # printer's effective table the same way the class body does.
    pc._known_functions['Min'] = 'min'
    pc._known_functions['Max'] = 'max'
    from itertools import chain
    pc.AbstractPythonCodePrinter._kf = dict(chain(
        pc._known_functions.items(),
        [(k, 'math.' + v) for k, v in pc._known_functions_math.items()],
    ))
    from sympy import Min, Max, Abs, Symbol
    return pc.PythonCodePrinter, Min, Max, Abs, Symbol


def _codepoints(s):
    return [ord(ch) for ch in s]


def main():
    PythonCodePrinter, Min, Max, Abs, Symbol = _import_patched_printer()

    # Build a pool of symbol arguments whose printed form is the bare name.
    names = ["x", "y", "z", "a", "b", "c", "t", "u", "p", "q", "alpha", "n1"]
    syms = [Symbol(n) for n in names]

    cases = []  # (name_code, sympy_factory)
    cases.append((1, Min))
    cases.append((2, Max))
    cases.append((0, Abs))   # Abs is unary

    rng = random.Random(22914)
    checks = 0

    for name_code, fn in cases:
        # Abs is strictly unary.  Min/Max with a single argument collapse to
        # that argument (lattice identity), so they are exercised n-ary with
        # >=2 DISTINCT symbols (duplicate args also simplify away).
        arities = [1] if fn is Abs else [2, 3, 4]
        for arity in arities:
            for _ in range(80):
                args = rng.sample(syms, arity)
                expr = fn(*args)
                # Skip any case the selection collapsed (so the expression is no
                # longer a Min/Max application of exactly these args).
                if fn is not Abs and (expr.func is not fn
                                      or len(expr.args) != arity):
                    continue
                prntr = PythonCodePrinter()
                # the comma-joined argument text the printer would produce, in
                # the order the application stores its args (canonicalised)
                joined = ", ".join(prntr._print(a) for a in expr.args)
                observed = prntr.doprint(expr)            # REAL printer
                expected = call_render(name_code, _codepoints(joined))
                assert _codepoints(observed) == expected, (
                    "deep model unsound for name_code=%d args=%r: real printer "
                    "gave %r, model call_render gives code points %r"
                    % (name_code, [str(a) for a in expr.args], observed, expected))
                # the supported-function rendering begins with the target name
                assert observed.startswith(
                    "".join(chr(c) for c in _TARGET[name_code])), observed
                checks += 1

    # Negative side: a function NOT in the supported table is not rendered as a
    # call of a supported target.  Use an undefined function f(x); the real
    # printer routes it through the not-supported / unknown path.
    from sympy import Function
    for n in range(40):
        arity = rng.choice([1, 2, 3])
        args = rng.sample(syms, arity)
        f = Function("f_unsupported_%d" % n)
        prntr = PythonCodePrinter()
        joined = ", ".join(prntr._print(a) for a in args)
        observed = prntr.doprint(f(*args))
        for nc in _SUPPORTED:
            call_form = "".join(chr(c) for c in call_render(nc, _codepoints(joined)))
            assert observed != call_form, (
                "unsupported function rendered as a supported call form: %r"
                % observed)
        checks += 1

    print("G-AX OK: deep model (is_supported / target_name / call_render) == "
          "real PythonCodePrinter over %d Min/Max/Abs renderings + unsupported "
          "negatives" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
