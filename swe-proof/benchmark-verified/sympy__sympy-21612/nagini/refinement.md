# refinement.md — sympy__sympy-21612

The operation-by-operation correspondence between `model.py`'s implementation
(the `bracket_flags` loop, with the deep `needs_brackets` / `is_composite_form`
predicates) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == a real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim:

*any implementation that verifies against this frozen spec, refined per the map
below, computes the same per-denominator-factor bracketing decision as the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The bracketing decision — `_print_Mul` (`sympy/printing/str.py:335-336`)

Gold hunk:
```
  if (len(item.args[0].args) != 1 and
-         isinstance(item.base, Mul)):
+         isinstance(item.base, (Mul, Pow))):
      # To avoid situations like #14160
      pow_paren.append(item)
  b.append(item.base)
```
`pow_paren` membership later causes the factor's rendered base to be wrapped in
brackets (`str.py:353-356`).

| # | model.py impl op (`bracket_flags`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `factors: List[Factor]` | the loop `for item in args:` over denominator items (`Pow`, `exp is S.NegativeOne`) | R | each `item` ↔ a `Factor`; the model receives the denominator factors in the same order (mapping.md §2). |
| A2 | `f.parts` (int field of `Factor`) | `len(item.args[0].args)` | R | `len(item.args[0].args)` is the integer part count of the reciprocated base; abstracted to the int field `parts`. The only operation performed on it is the comparison in A4 (mapping.md §2). |
| A3 | `f.form` read + the disjunction `f.form == 1 or f.form == 2` (via `is_composite_form`) | `isinstance(item.base, (Mul, Pow))` | R | the `isinstance` against the 2-tuple `(Mul, Pow)` ↔ membership of the structural-form tag in `{1, 2}` (`form==1` ⇔ `Mul`, `form==2` ⇔ `Pow`, `form==0` ⇔ any other class ⇔ `isinstance` False). This is the *changed* operation, modeled **deeply** as a boolean over the form tag — not behind a consumed axiom, since `isinstance` is a concrete language operation, not an opaque library callee. Its faithfulness (the tag bijection actually matches `isinstance(item.base, (Mul, Pow))` on real sympy expressions) is validated out-of-band by axiom_check.py (G-AX); see §C. |
| A4 | `flag = f.parts != 1 and (f.form == 1 or f.form == 2)` (`== needs_brackets(f.parts, f.form)`) | `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))` | I + R | the `!= 1` integer comparison and the `and` are identical concrete operations (I); the two operands are A2 (R) and A3 (R). The guard is reproduced exactly. |
| A5 | `result.append(flag)`; flag True ⇒ this factor is bracketed | `pow_paren.append(item)` ⇒ `b_str[...] = "(%s)" % b_str[...]` (`str.py:338,354-356`) | R | a True flag ↔ the factor's base rendered with surrounding brackets; a False flag ↔ bare. The downstream rendering (`parenthesize`, `'/'.join`) is unchanged by the patch and lies entirely after the decision, so it is not modeled — the decision (this flag list) is the complete delta. |

The discriminating content of the change — a *power*-form reciprocal
(`item.base` an `isinstance` of `Pow`, e.g. `1/y == Pow(y, -1)`) with more than
one part must now be bracketed — lives in the `f.form == 2` disjunct of
`needs_brackets` (model) ⇔ the added `Pow` in `isinstance(item.base, (Mul,
Pow))` (real). The pre-patch guard tested only `Mul` (form tag 1);
`model_prepatch.py` reproduces that (`flag = f.parts != 1 and (f.form == 1)`)
and **fails** the loop invariant / postcondition
`Result()[k] == needs_brackets(factors[k].parts, factors[k].form)` on any
factor with `form == 2` and `parts != 1` — exactly the issue's `1/(1/y)`
factor. That is the spec sensing the change (G-DIFF).

## B. No consumed axioms

There is **no `@ContractOnly` axiom** and no A-consumed row. The changed
operation (the two-part guard) is fully expressible as integer/boolean
reasoning over the abstracted facets, so it is modeled deeply; no opaque library
callee is invoked whose contract the proof would consume.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — adding
the `Pow` structural form to the bracketing guard — is modeled **deeply** (the
`form == 2` disjunct of the spelled-out predicate `needs_brackets`, an
**A-reference**), not hidden behind an axiom about the function under change.
The deep model is validated against reality by G-AX: axiom_check.py constructs
the real sympy expressions (`Mul(x, Pow(1/y, -1, evaluate=False), ...)` and the
`#14160` witness), extracts each denominator item's true
`(len(item.args[0].args), structural-form-of(item.base))` facets, and asserts
the model predicate `needs_brackets` over those facets equals the **post-patch**
real guard `len(...) != 1 and isinstance(item.base, (Mul, Pow))` and differs
from the **pre-patch** guard `... isinstance(item.base, Mul)` exactly on the
`1/y` factor (the A-reference soundness of the form-tag bijection).

## D. verify(model) ⇒ resolved

`bracket_flags` verifies only if every output flag equals the post-patch guard
`parts != 1 and (form ∈ {Mul, Pow})` (A4) for every factor. By R (the `Factor`
field bijection: `parts` ↔ `len(item.args[0].args)`, `form ∈ {1,2}` ↔
`isinstance(item.base, (Mul, Pow))`, flag ↔ bracketed-or-bare rendering) the
verified decision equals the gold patch's `pow_paren` collection on the tested
inputs; the unchanged downstream rendering then prints the issue's denominator
factor `1/y` bracketed (`x/(1/y)`) and the `#14160` factor `y*y` bracketed
(`-2*x/(y*y)`), which is exactly what the F2P `test_Mul` requires. By G-AX the
form-tag bijection equals the real `isinstance(_, (Mul, Pow))` on those
expressions. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE: with the test_patch applied, `test_Mul` fails pre-patch and passes
post-patch, confirmed in-container). The trust points reduce to the single
A-reference of §C, audited by G-AX.
