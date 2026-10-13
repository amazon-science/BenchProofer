# refinement.md — sympy__sympy-13757

The operation-by-operation correspondence between `model.py`'s implementation
(the `polynomial_priority` / `product_is_evaluated` / `generic_times_polynomial`
impl regions and the deep `resolved_by_right` dispatch model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (modeled
callee — split into **A-consumed**, where the proof uses an axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The change site — the `Poly` operation priority

Gold hunk (`sympy/polys/polytools.py`, `Poly(Expr)` class body):
```
     is_commutative = True
     is_Poly = True
+    _op_priority = 10.001
```

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `polynomial_priority()` returns `10.001` | `_op_priority = 10.001` added to the `Poly` class body | R | the Python `float` class attribute `Poly._op_priority` ↔ the interpreted real returned by `polynomial_priority()` (mapping.md §2/§3.2). The value is identical (`10.001`); the only carrier difference is class-attribute-vs-function, which is observationally the same scalar at the dispatch comparison site. |
| A2 | `default_priority()` returns `10.0` | the inherited `Expr._op_priority = 10.0` (`expr.py:105`, unchanged) | A-reference | the generic default priority is an UNCHANGED repo datum; `default_priority` models it and axiom_check.py asserts `default_priority() == Expr._op_priority` against the real class. |
| A3 | `resolved_by_right(self_p, other_p, has)` = `has and other_p > self_p` | the dispatch in `binary_op_wrapper` (`decorators.py:124-131`): `if hasattr(other,'_op_priority'): if other._op_priority > self._op_priority: return getattr(other,method_name)(self)` | A-reference | the dispatch rule is UNCHANGED; modeled deeply (not behind a consumed axiom). axiom_check.py validates `resolved_by_right` == the real `binary_op_wrapper` delegation decision over a grid+fuzz of priorities (mapping.md §3.1). The strict `>` is faithful to the source. |
| A4 | `product_is_evaluated(...)` returns `other_evaluates` when `resolved_by_right(...)` else `self_evaluates` | `Expr.__mul__` = `@call_highest_priority('__rmul__')` over `return Mul(self, other)` (`expr.py:137-140`): delegates to `other.__rmul__(self)` (here `Poly.__rmul__`, which evaluates) when the right operand wins, else builds the inert `Mul` | R + A-reference | which operand's handler runs is the A-reference dispatch (A3); the observable (`evaluated` bool) ↔ "an evaluated `Poly`" vs. "an inert `Mul` node" (mapping.md §2). For the tested product the left handler is `Mul(...)` (inert for a Poly ⇒ `self_evaluates=False`) and the right handler is `Poly.__rmul__` → `g.mul(f)` (evaluated ⇒ `other_evaluates=True`). |
| A5 | `generic_times_polynomial()` builds `(default, evaluates=False)` × `(polynomial, evaluates=True, has=True)` and returns `product_is_evaluated(...)`, ensured `== True` | the expression `x * Poly(x)` (generic `Symbol` on the left, `Poly` on the right), required by F2P to be the evaluated `Poly(x**2, x, domain='ZZ')` | R + I | the operands' modeled characteristics are the R-refinement of the real `Symbol`/`Poly` (mapping.md §2); the product is computed by the (A-reference) dispatch, not asserted. The postcondition `Result() == True` ⇔ "the product is evaluated", which is exactly what `test_issue_13079`'s `x*Poly(x) == Poly(x**2, x, domain='ZZ')` observes. |

The discriminating content of the change is **A1**: a polynomial's advertised
operation priority becomes strictly greater than the default (`10.001 > 10.0`).
By the unchanged dispatch (A3), this is precisely what routes a
generic-left-times-polynomial-right product to the polynomial's evaluating
reverse handler (A4), making `generic_times_polynomial` verify (A5). The
pre-patch state — `Poly` inherits the default priority — makes
`polynomial_priority() == 10.0`, so `polynomial_priority`'s postcondition
`Result() >= default_priority() + 1e-15` fails, and with it
`generic_times_polynomial`. `model_prepatch.py` reproduces exactly this
(`return 10.0`) and **fails** on the clause
`Result() >= default_priority() + 1e-15` (G-DIFF) — the spec sensing the change.

The postcondition carries an explicit **margin** (`+ 1e-15`) rather than a bare
strict order over the interpreted reals. The model verifies under
`--float-encoding=real` (exact reals), but the repo datum is carried by a
finite-precision runtime scalar and the dispatch comparison runs there. A
margin-free strict order would admit values whose distance above the baseline
lies beneath the carrier's resolution at that magnitude (one ULP of the runtime
scalar at 10.0 is ≈1.78e-15; anything closer than half of that collapses onto
the baseline when materialized), turning the dispatch comparison into a tie and
routing the product away from the polynomial. The `1e-15` margin exceeds that
half-resolution (≈8.9e-16), so every admitted real materializes to a runtime
scalar strictly above the baseline and the strict order in A3 survives
refinement. This closes the A1 R-refinement gap (interpreted real ↔ runtime
scalar): verify ⇒ the materialized attribute strictly exceeds the default ⇒
the dispatch picks the polynomial ⇒ resolved.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the polynomial's operation priority crossing strictly above the
default — is modeled **directly** as the value `polynomial_priority()` returns
(A1), an interpreted real whose order against the default is the whole content.
The dispatch machinery it feeds (`binary_op_wrapper`, the default priority) is
UNCHANGED and modeled **deeply** as the A-references `resolved_by_right` /
`default_priority`, validated == the real callees by axiom_check.py (G-AX) — not
hidden behind a consumed axiom about the thing under change. There is **no
A-consumed axiom**: the proof consumes only the deep models and the changed
value, all on the model side.

## C. verify(model) ⇒ resolved

`generic_times_polynomial` verifies only if `product_is_evaluated` returns
`True` for a default-priority non-evaluating left operand and a
polynomial-priority evaluating right operand — which, by the dispatch
`resolved_by_right` (strict `>`), holds iff `polynomial_priority() >
default_priority()` (A5←A4←A3←A1). By R (the class attribute `Poly._op_priority`
== the modeled real, the `Symbol`/`Poly` operands == their modeled
characteristics) the verified behaviour equals the gold patch's effect on the
tested product; by G-AX the deep dispatch model == the real `binary_op_wrapper`
(A-reference) and the modeled priorities == the real `_op_priority` values
(A-reference), and the real `x*Poly(x)` evaluates iff the strict order holds.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited (unchanged) callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: callee
soundness (G-AX — here the unchanged dispatch + priority data) and refinement
fidelity (this document, G-EQ).
