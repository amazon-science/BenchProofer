# refinement.md — django__django-15161

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `deconstructPath` `do` block) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement; state the bijection), **A-consumed** (proof
uses an axiom's `ensures`), **A-reference** (deep model validated == a real
callee by G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the (here, zero) A legs and this narrative are audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The deconstruct-path site

The gold patch adds six decorator lines to `django/db/models/expressions.py`:
```
+@deconstructible(path='django.db.models.Func')          # before class Func
+@deconstructible(path='django.db.models.Value')         # before class Value
+@deconstructible(path='django.db.models.ExpressionWrapper')
+@deconstructible(path='django.db.models.When')
+@deconstructible(path='django.db.models.Case')
+@deconstructible(path='django.db.models.OrderBy')
```
Each `@deconstructible(path=p)` rebinds the class's `deconstruct()` to the
closure in `django/utils/deconstruct.py` whose path-selection line is
(`deconstruct.py:42-46`):
```python
return (
    path if path and type(obj) is klass
    else f'{obj.__class__.__module__}.{name}',
    obj._constructor_args[0],
    obj._constructor_args[1],
)
```
The patch is purely additive (six decorator applications). Its only observable
effect is on element 0 of the `deconstruct()` 3-tuple — the import path — for
nodes of exactly these six types: it flips from
`django.db.models.expressions.X` to the simplified public `django.db.models.X`.

| # | Solution.lean impl op (`deconstructPath`) | patch.diff effect (`deconstruct()[0]` via `deconstruct.py:42-46`) | tag | justification |
|---|---|---|---|---|
| A1 | params `definingModule className : List Char` | `obj.__class__.__module__`, `obj.__class__.__name__` (both `str`) | R | `str ↔ List Char` (mapping.md §2). For these nodes `definingModule = "django.db.models.expressions"`. |
| A2 | param `publicPath : Option (List Char)` | the closure's captured `path` kwarg: `some p` iff the (ancestor) type was decorated `@deconstructible(path=p)`, else `none` | R | `path is None / not None ↔ none / some p` (mapping.md §2, §3.1). The patch is exactly what makes `publicPath = some 'django.db.models.X'` for the six types. |
| A3 | param `exactType : Bool` | `type(obj) is klass` (`deconstruct.py:42`) | R | Python `bool ↔ Bool` (mapping.md §2). |
| A4 | `if publicPath ≠ none ∧ exactType = true then publicPath.getD []` | `path if path and type(obj) is klass` — return the simplified public path | I + R | identical guard and value under R: a non-`None` `path` (`path` truthy) AND exact-type ⇒ report the assigned simplified public path. The `and` ↔ `∧`. |
| A5 | `else definingModule ++ ['.'] ++ className` | `else f'{obj.__class__.__module__}.{name}'` | I + R | identical: otherwise the defining-module-qualified class name; `f'{m}.{n}'` ↔ `m ++ ['.'] ++ n` (mapping.md §2). |

Discriminating content of the change — for a node whose runtime type is exactly
one of the six decorated classes (`publicPath ≠ none ∧ exactType = true`), the
reported path is the simplified public `django.db.models.X` (A4), NOT the longer
`django.db.models.expressions.X`. The pre-patch left these classes undecorated,
so `publicPath` was effectively never honored for them and `deconstruct()`
always returned the long defining-module path. `Solution_prepatch.lean`
reproduces that (always `definingModule ++ ['.'] ++ className`) and **fails** the
first `ensures` clause `(publicPath ≠ none ∧ exactType = true) → out =
publicPath.getD []` (G-DIFF) — the exact behavior the F2P `test_deconstruct`
(`Value` → `django.db.models.Value`) and `test_serialize_complex_func_index`
(`Func`/`Case`/`When`/`Value`/`ExpressionWrapper`/`OrderBy` serialize as
`models.X(...)`) observe.

The subtype/undecorated frame (`¬(publicPath ≠ none ∧ exactType = true)`, A5) is
pinned too: a `Func` subclass such as `ExpressionList`/`OrderByList`
(`exactType = false`) and an undecorated class such as `RawSQL`
(`publicPath = none`) must still report the long defining-module path — the
patch must NOT over-simplify these. This is the directive-5 / spec-strength
frame: both arms are exactly stated.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that changed — which import path
`deconstruct()` selects — is modeled **deeply** and directly as the function
under specification (`deconstructPath`'s two-way choice), not hidden behind an
axiom. There are no consumed axioms and no A-reference deep models of a separate
callee: the change is a configuration of *which* of two paths the existing
selection logic reports, and that selection logic is exactly what `deconstructPath`
encodes. G-AX is therefore `skip` (no axiom_check.py).

## C. verify(Solution) ⇒ resolved

`deconstructPath` verifies only if it returns the simplified public path on
exactly the `(publicPath ≠ none ∧ exactType = true)` frame (A4) and the long
defining-module path otherwise (A5). By R (`str ↔ List Char`, `f'{m}.{n}' ↔ m ++
['.'] ++ n`, `path is None ↔ none`, `type(obj) is klass ↔ exactType`) the
verified selection equals the real `deconstruct.py:42-46` path-selection on every
node; by G-CONF the R/I transliteration agrees with `patch.diff`'s real
`deconstruct()` over ≥10⁵ fuzzed `(class, publicPath, exactType)` configurations
including the six patched types, their subtypes, and undecorated classes.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The sole
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms to trust (G-AX skip).
