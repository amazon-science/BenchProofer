#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-12096.

Runs the REAL recursive numeric evaluation (`Expr.evalf` driving the patched
`Function._eval_evalf`) on nested implemented-function compositions and asserts
that every observation matches the model in model.py.

There are NO consumed (@ContractOnly) axioms in this bundle. The two kind-A
references the deep model is validated against:

  (A-reference) `imp` (model.py pure region) == the user implementation
      `self._imp_` on the worked example: imp(x) = x * x  (lambda x: x ** 2).

  (A-reference) `eval_seq` (model.py pure region) == the real inside-out
      recursive reduction the patched line performs
      (`self._imp_(*[i.evalf(prec) for i in self.args])` recursing through the
      nested applications): a chain of `n` layers of `imp` over a numeric leaf
      `v` reduces to `imp` applied `n` times to `v`, ALWAYS yielding a present
      number (never left unevaluated), for every n >= 0.

This includes the F2P discriminator `f(f(2)).evalf() == Float(16)` (two layers,
leaf 2: imp(imp(2)) = (2*2)**2 = 16) and deeper compositions that the pre-patch
code left unevaluated. Imports only the standard library and the repo under
test (`sympy`). Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import Float, Integer
from sympy.utilities.lambdify import implemented_function


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def imp(x):
    """Reference for model.py's `imp`: the squaring map of the worked example."""
    return x * x


def eval_seq(leaf, n_layers):
    """Reference for model.py's deep fold `eval_seq`: apply `imp` `n_layers`
    times to the numeric `leaf` (inside-out). n_layers == 0 is the bare leaf."""
    acc = leaf
    for _ in range(n_layers):
        acc = imp(acc)
    return acc


# --- build a real nested implemented-function composition ---------------------

def build_nested(symfunc, leaf, n_layers):
    """`symfunc` applied `n_layers` times to the Integer leaf."""
    expr = Integer(leaf)
    for _ in range(n_layers):
        expr = symfunc(expr)
    return expr


def check_reference(symfunc, leaf, n_layers):
    """Assert the REAL recursive evalf reproduces the deep model:
    a present number equal to eval_seq(leaf, n_layers)."""
    expr = build_nested(symfunc, leaf, n_layers)
    observed = expr.evalf()                       # real recursive reduction
    # The reduction must yield a number (never leave the object unevaluated).
    assert observed.is_Number, (
        "evalf left a %d-layer composition over leaf %r unevaluated: got %r"
        % (n_layers, leaf, observed))
    expected = eval_seq(leaf, n_layers)           # deep model
    assert observed == Float(expected), (
        "eval_seq deep model unsound on (leaf=%r, layers=%d): real evalf gave "
        "%r, deep model gives %r" % (leaf, n_layers, observed, Float(expected)))


def main():
    f = implemented_function('f', lambda x: x ** 2)   # imp(x) = x * x

    # --- the F2P discriminator (two layers, leaf 2): f(f(2)).evalf() == 16 ---
    assert f(f(2)).evalf() == Float(16), (
        "F2P discriminator failed: f(f(2)).evalf() = %r != Float(16)"
        % f(f(2)).evalf())

    # also confirm the single-layer and zero-layer base behaviour
    assert f(2).evalf() == Float(4)
    assert Integer(2).evalf() == Float(2)

    # MIRROR the model.py contract domain EXACTLY (no broader, no narrower):
    # the precondition in model.py is `leaf >= 0 and eval_seq(leaf, layers) <
    # 1e14`, i.e. the leaf is non-negative and the inside-out reduction stays
    # inside the exact representable float window (~15 sig digits) so the
    # exact-integer reference and the real evalf agree bit-for-bit. This filter
    # is identical to that precondition (filter == Requires), so the check never
    # validates outside the contract's declared domain nor leaves any in-domain
    # input unchecked.
    def within_precision(leaf, n):
        return leaf >= 0 and eval_seq(leaf, n) < 10 ** 14

    # --- boundary cases over leaves and nesting depth -----------------------
    boundary_leaves = [0, 1, 2, 3, 5, 10]
    boundary_depths = [0, 1, 2, 3, 4, 5]
    boundary_checks = 0
    for leaf in boundary_leaves:
        for n in boundary_depths:
            if within_precision(leaf, n):
                check_reference(f, leaf, n)
                boundary_checks += 1

    # --- randomized fuzz over leaves and depths -----------------------------
    rng = random.Random(12096)
    checks = 0
    for _ in range(400):
        leaf = rng.randint(0, 10)
        n = rng.randint(0, 5)
        if not within_precision(leaf, n):
            continue
        check_reference(f, leaf, n)
        checks += 1

    print("G-AX OK: imp + eval_seq deep model (== real recursive evalf) sound "
          "on the F2P discriminator, %d boundary, and %d fuzz compositions"
          % (boundary_checks, checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
