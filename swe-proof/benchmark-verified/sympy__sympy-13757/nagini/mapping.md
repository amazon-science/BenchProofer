# mapping.md — sympy__sympy-13757

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a5e6a101869e027e7930e694f8b1cfb082603453`, states the type
abstraction, and gives the provenance of each modeled callee (the unchanged
priority-dispatch decorator).

Repo file under change: `sympy/polys/polytools.py` (the `Poly` class header).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `polynomial_priority()` | `Poly._op_priority` class attribute — `sympy/polys/polytools.py:106-108` (the `Poly(Expr)` class body, just after `is_Poly = True`); pre-patch INHERITED from `Expr._op_priority` | the modeled changed datum: the operation priority a polynomial advertises. Pre-patch it equals the default (inherited); post-patch it is `10.001`, strictly above the default. |
| `default_priority()` *(pure constant)* | `Expr._op_priority = 10.0` — `sympy/core/expr.py:105` | the baseline operation priority a generic symbolic expression carries; the value every operand's priority is compared against in dispatch. UNCHANGED. |
| `resolved_by_right(self_p, other_p, has)` *(deep model — A-reference)* | the `binary_op_wrapper` body inside `call_highest_priority(method_name)` — `sympy/core/decorators.py:121-133` | pure spec of the FIXED dispatch rule: a binary special method delegates to the other operand's reverse handler iff that operand has the handler AND `other._op_priority > self._op_priority`. UNCHANGED by the patch; modeled deeply, validated == the real decorator by axiom_check.py (G-AX). |
| `product_is_evaluated(...)` | `Expr.__mul__` wrapped by `@call_highest_priority('__rmul__')` — `sympy/core/expr.py:137-140`, with `Poly.__rmul__` — `sympy/polys/polytools.py:4050-4058` as the right operand's reverse handler | the dispatch applied to a product: the result is produced by the winning operand's handler; "evaluated" iff that handler evaluates a polynomial product. |
| `generic_times_polynomial()` | the expression `<generic expr> * Poly(...)` (e.g. `x*Poly(x)`), evaluated through `Expr.__mul__`'s priority dispatch — F2P `test_issue_13079`, `sympy/polys/tests/test_polytools.py:680-685` | the required behaviour: a generic expression times a polynomial evaluates to the polynomial product. |

The pre-patch repo state the change fixes (for the refinement audit, not
referenced from the consumer spec view): `Poly` defines no `_op_priority` of its
own, so it inherits `Expr._op_priority = 10.0` (`expr.py:105`). The gold patch
adds the line `_op_priority = 10.001` to the `Poly` class body
(`polytools.py:108`, inserted after `is_Poly = True`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `_op_priority` class attributes (Python `float`) | interpreted `float` (`--float-encoding=real`) | the priorities are genuine real numbers; the dispatch turns on their strict order `>`. `Expr._op_priority` ↔ `default_priority() == 10.0`; `Poly._op_priority` ↔ `polynomial_priority() == 10.001`. Precision matters: `10.001 > 10.0` is the entire behavioural content, so the float is interpreted (real), never faked with an int. |
| a SymPy operand object (`Symbol`, `Poly`, …) in a binary product | its two touched characteristics, passed as parameters: an operation priority (`float`) and whether its winning handler evaluates a polynomial product (`bool`) | only the two fields the dispatch and the observable behaviour read are modeled; the rich `Expr`/`Poly` object is otherwise opaque. A generic expression ↔ `(default_priority(), evaluates=False)`; a polynomial as right operand ↔ `(polynomial_priority(), evaluates=True, has_handler=True)`. |
| `hasattr(other, '_op_priority')` then the reverse-method `getattr` (`decorators.py:124-131`) | the boolean `other_has_handler` | a polynomial exposes both `_op_priority` and `__rmul__`, so for the modeled product `other_has_handler` is `True`. |
| the evaluated polynomial product vs. an inert `Mul(...)` node | the boolean result `evaluated` | `True` ↔ `Poly.__rmul__` ran and returned `g.mul(f)` (an evaluated `Poly`); `False` ↔ `Expr.__mul__` built an unevaluated `Mul(self, other)`. The F2P test observes exactly this distinction (`x*Poly(x) == Poly(x**2, x, domain='ZZ')` vs. the inert `x*Poly(x, x, domain='ZZ')`). |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolved_by_right` deep model ↔ `call_highest_priority` dispatch (A-reference)
**Callee:** the `binary_op_wrapper` closure produced by
`call_highest_priority(method_name)` in `sympy/core/decorators.py:121-133`:

```python
def binary_op_wrapper(self, other):
    if hasattr(other, '_op_priority'):
        if other._op_priority > self._op_priority:
            try:
                f = getattr(other, method_name)
            except AttributeError:
                pass
            else:
                return f(self)
    return func(self, other)
```

The dispatch rule is UNCHANGED by the patch — it is modeled **deeply** by the
`@Pure` helper `resolved_by_right` (no consumed `@ContractOnly` axiom stands in
for it). The deep model is validated equal to the real decorator out-of-band by
axiom_check.py (G-AX): for operands with priorities `p_self`, `p_other` where
`other` exposes the named reverse handler, the wrapper delegates to `other`
(returns `f(self)`) iff `p_other > p_self`; otherwise it calls the original
`func(self, other)` (the left operand's own handler). `resolved_by_right`
encodes exactly the predicate `other_has_handler and other_priority >
self_priority`. The strict `>` (not `>=`) is faithful to the source line
`if other._op_priority > self._op_priority`.

### 3.2 `default_priority` / `polynomial_priority` ↔ the two `_op_priority` values
**`Expr._op_priority = 10.0`** (`sympy/core/expr.py:105`) is the documented
default operation priority every `Expr` subclass inherits unless it overrides it
(the class comment at `expr.py:95-104` explains the mechanism: "an object that
defines binary operators … should set an `_op_priority` value that is higher
than the default"). `default_priority()` returns `10.0`, the real callee value.

**`Poly._op_priority`** is, pre-patch, this inherited `10.0`; the gold patch sets
it to `10.001` (`polytools.py:108`). `polynomial_priority()` returns `10.001`.
The property the proof relies on is `polynomial_priority() >=
default_priority() + 1e-15` (`10.001 >= 10.0 + 1e-15`), i.e. a polynomial
advertises a priority above the default by at least the resolution of the
runtime scalar carrier at that magnitude (half a ULP of a 64-bit scalar at 10.0
is ≈8.9e-16 < 1e-15), so the strict order the dispatch tests survives the
model-real-to-runtime-scalar materialization (see refinement.md A1). axiom_check.py confirms, against the real classes,
that `Poly._op_priority > Expr._op_priority` post-patch (and that they are equal
pre-patch, i.e. the bug), and that the real `binary_op_wrapper` routes
`x * Poly(x)` to `Poly.__rmul__` (evaluated) iff this strict order holds.

**Soundness check (G-AX):** `axiom_check.py` (a) reproduces `binary_op_wrapper`
on a grid + fuzz of `(p_self, p_other, has_handler)` and asserts the delegation
decision equals `resolved_by_right` (the A-reference deep model); (b) reads the
real `Expr._op_priority` and `Poly._op_priority` and asserts
`default_priority() == Expr._op_priority`, `Poly._op_priority > Expr._op_priority`
post-patch; (c) end-to-end: builds the real `Symbol('x')` and `Poly(x)` and
asserts `x*Poly(x)` is an evaluated `Poly` equal to `Poly(x)*x`. It imports only
`sympy` (the very package the patch lives in). Exit 0 iff sound.

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl regions (shadow)
differentially against the real patched repo in-container: the dispatch
observable against the real `call_highest_priority` wrapper on probe operand
classes, the two priority constants against the real `Expr._op_priority` /
`Poly._op_priority` class data, and `generic_times_polynomial` against the
real end-to-end product `<generic expr> * Poly(x)`. The float carrier bridges
identically (interpreted real ↔ Python float). >= 1e5 inputs: boundary
priority grid (ties, ULP/1e-15 offsets, specials) × all boolean combinations
+ 100000 fuzz tuples. **Pinned fuzz seed: 13757.**
