# refinement.md — sympy__sympy-24213

The operation-by-operation correspondence between `model.py`'s implementation
(the `collect_sum_dimension` impl region, the deep `equivalent` model, and the
`reduction_of` function-axiom) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized/deep callee — split into
**A-consumed**, where the proof uses the axiom's contract, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed guard — the `Add` branch of `_collect_factor_and_dimension`

Gold hunk (`sympy/physics/units/unitsystem.py:178`):
```
-                if dim != addend_dim:
+                if not self.get_dimension_system().equivalent_dims(dim, addend_dim):
                     raise ValueError(
                         'Dimension of "{}" is {}, '
                         'but it should be {}'.format(
                             addend, addend_dim, dim))
```
Surrounding (unchanged) control flow: `dim` is collected from `expr.args[0]`;
the loop runs over `addend in expr.args[1:]`, recursively collecting each
`addend_dim`; on incompatibility it raises `ValueError`, else it sums the
magnitude (`factor += addend_factor`) and finally returns `(factor, dim)`.

| # | model.py impl op (`collect_sum_dimension`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `surf: List[int]`, `red: List[int]` (per-addend facets) | the dimensions `dim`, `addend_dim` (one `Dimension` per addend of `expr.args`) | R | each `Dimension` ↔ its `(surf[i], red[i])` facet pair: surface-description identity ↔ `surf[i]`, canonical-reduction identity ↔ `red[i]` (mapping.md §2). |
| A2 | `red[0]` is the reference reduction; the loop index runs `i = 1 … len-1` | `dim = collect(expr.args[0])`; `for addend in expr.args[1:]` | I/R | index 0 = the first addend (reference), `1..` = the rest — identical loop shape under R. |
| A3 | guard `if not equivalent(surf[0], red[0], surf[i], red[i]): raise DimensionMismatch()` where `equivalent(...) == (red[0] == red[i])` | `if not self.get_dimension_system().equivalent_dims(dim, addend_dim): raise ValueError(...)` | A-reference | the changed comparison is modelled **deeply**: `equivalent` (the spelled-out `red_a == red_b` in the `pure` region) IS the equivalence test. There is no consumed `equivalent_dims` axiom. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) asserts `equivalent_dims(d_a, d_b) == (reduction(d_a) == reduction(d_b))` on 729 pairs + 4000 fuzz, 0 mismatch (mapping.md §3.1). The real `equivalent_dims` compares the two dimensions' `get_dimensional_dependencies` (the reductions), never their surface descriptions. |
| A4 | `raise DimensionMismatch()` | `raise ValueError('Dimension of "{}" is {} …')` | R | user-defined exception ↔ the `ValueError` (builtin-exception `Exsures` crashes Nagini). The F2P test observes only *whether* a raise occurs, not its message/type (mapping.md §1). |
| A5 | (the function-axiom) `red[i] == reduction_of(surf[i])`, `reduction_of` `@Pure` | `addend_dim`/`dim` are reduced by `get_dimensional_dependencies` inside `equivalent_dims` | A-consumed | the proof consumes only that the reduction is a genuine FUNCTION of the dimension: `reduction_of` is `@Pure`, so equal surface identities give equal reduction identities (`surf[i]==surf[j] ⇒ red[i]==red[j]`). G-AX confirms the real `get_dimensional_dependencies` is deterministic / a function of the dimension (mapping.md §3.2). |
| A6 | `return red[0]` (the common reduction identity) | `return factor, dim` (the magnitude sum + the reference dimension) | R | the patch does not change factor accumulation; the only modeled, changed observable is the dimension-compatibility decision. Returning the reference reduction identity ↔ returning `dim`; magnitude accumulation is identical in both versions and not modeled. |
| A7 | `Requires(MustTerminate(2))` + loop `Invariant(MustTerminate(len(surf) - i + 1))` (total-correctness obligation) | `for addend in expr.args[1:]` — a bounded pass over the sum's finitely many addends that always returns `(factor, dim)` or raises `ValueError` | I | the real loop is structurally terminating (a `for` over a finite tuple); the model carries the same totality as an explicit Nagini obligation. Without it a diverging impl (e.g. `while True: pass` in place of the raise) satisfies every value postcondition vacuously while its faithful real patch hangs the hidden tests (the G-PANEL-1/G-EQ atk_1/atk_8 exploit). The obligation pins "delivers a verdict", exactly what the real patched code does. |

The discriminating content of the change — accept a later addend that is
**physically equivalent** to the first even though its **surface description**
differs — lives in `equivalent(...) == (red_a == red_b)` (model) ⇔
`equivalent_dims(dim, addend_dim)` (real). The pre-patch guard compared surface
descriptions (`dim != addend_dim`, structural `Dimension.__eq__`);
`model_prepatch.py` reproduces that (`if surf[i] != surf[0]: raise`) and **fails**
the exceptional postcondition `Exsures(DimensionMismatch, … Exists i: red[i] !=
red[0])`: it raises on `surf[i] != surf[0]` even when all reductions are equal,
which the spec forbids (it permits a raise only when some reduction differs).
That is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, A-consumed, or I. The one operation that
genuinely *changed* — the dimension-compatibility comparison — is modelled
**deeply** (the spelled-out `equivalent`/`red_a == red_b`, an **A-reference**
validated == the real `equivalent_dims` by G-AX), not hidden behind an axiom
about the function under change. The only consumed axiom, `reduction_of`
(**A-consumed**), covers the **unchanged** engine `get_dimensional_dependencies`
the comparison consults, and encodes only its weakest used property (it is a
function). There is no dead axiom.

## C. verify(model) ⇒ resolved

`collect_sum_dimension` verifies only if it terminates — returning normally or
raising; `Requires(MustTerminate(2))` makes every path to an exit carry a
discharged termination obligation, so a diverging implementation (whose real
patch would hang the hidden tests) is rejected by Nagini's obligation system
("obligation leak") rather than passing vacuously — and if it returns normally
exactly when every addend's reduction equals the first's (success
postcondition) and raises exactly when some addend's reduction differs
(`Exsures`). By R (Dimension ↔ (surf, red),
ValueError ↔ DimensionMismatch, factor accumulation unchanged) the verified
guard equals `not equivalent_dims(dim, addend_dim)` on the collected dimensions;
by G-AX the deep model `equivalent` equals the real `equivalent_dims`
(A-reference) and the real `get_dimensional_dependencies` meets the
`reduction_of` function-axiom (A-consumed). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE: F2P `test_issue_24211`
no longer raises, all P2P preserved). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
