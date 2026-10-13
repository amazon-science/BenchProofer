# mapping.md — django__django-15161

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 96e7ff5e9ff6362d9a886545869ce4496ca4b0fb`, states the type
abstraction, and gives the provenance of every axiomatized callee.

Repo files under change:
- `django/db/models/expressions.py` — the expression node classes the patch
  augments with a configured canonical import path.
- `django/utils/deconstruct.py` — the (UNCHANGED) decorator whose
  `deconstruct(obj)` method computes the import path that is observed; this is
  the behaviour the patch steers, modeled deeply.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deconstruct_path(configured, exact, module, name)` | the path-selecting body of `deconstruct(obj)` inside `deconstructible.decorator` — `django/utils/deconstruct.py:20-48` (the `if path and type(obj) is klass: … else …` choice and the returned first tuple element, lines 26-29 and 42-48) | the modeled function: which import path a deconstructible node reports |
| `serialized_module_rooted(path)` | the `module == "django.db.models"` branch of `DeconstructableSerializer._serialize_path` — `django/db/migrations/serializer.py:94-102` | pure spec: whether the reported path is rooted directly at the public `django.db.models` package (⇒ the migration writer emits the short `models.X` form + `from django.db import models`) |
| `qualified(module, name)` | the fallback expression `f'{obj.__class__.__module__}.{name}'` — `django/utils/deconstruct.py:45` | pure spec: the dotted `module "." name` fallback |

The patch itself (`expressions.py`) adds, to each of `Func`, `Value`,
`ExpressionWrapper`, `When`, `Case`, `OrderBy`, the class decorator
`@deconstructible(path='django.db.models.<ClassName>')`. The decorator already
in place for `F` (`expressions.py:581`, `@deconstructible(path='django.db.models.F')`)
is the public reference template the patch generalizes. Supplying `path=` is
exactly what makes `deconstruct`'s `if path and type(obj) is klass` branch fire,
so the reported path becomes the configured public-package-rooted string instead
of the `obj.__module__`-derived fallback.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` import paths / module / name (`path`, `obj.__module__`, `name`) | `List[int]` of Unicode code points; specification over `PSeq[int]` | `s[k]` ↔ `cp[k] == ord(s[k])`; `len(s)` ↔ `len(cp)`; `str` `+`/`.`-join ↔ list `+` with `46` (`'.'`) separator; empty `str` ↔ `[]` |
| `if path` truthiness (a non-empty configured path) | `len(configured) > 0` | a configured path is a non-empty code-point list; "no path configured" is `[]` |
| `type(obj) is klass` (the node is exactly the decorated class, not a subclass) | a `bool` flag `exact` | the patch decorates concrete leaf classes; the F2P nodes (`Value('name')`, `Func(...)`, …) instantiate exactly the decorated class ⇒ `exact == True` |
| `f'{module}.{name}'` fallback | `qualified(module, name) == module + PSeq(46) + name` | dotted-join refinement |

`str` indexing/iteration is banned in Nagini, so paths are carried as
`List[int]`; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Axioms / deep-model references

There are **no `@ContractOnly` consumed axioms**: the patched behaviour
(`deconstruct`'s path choice) and the observable serializer rooting check are
both expressible directly over `List[int]`/`PSeq[int]`, so they are modeled
**deeply** and verified, not axiomatized.

### 3.1 `serialized_module_rooted` deep model ↔ `_serialize_path` rooting test (A-reference)
**Callee:** `DeconstructableSerializer._serialize_path(path)`
(`django/db/migrations/serializer.py:94-102`). It splits `path` on the LAST `.`
into `(module, name)` and takes the public-short branch iff
`module == "django.db.models"`. The deep model
`serialized_module_rooted(path)` returns `True` iff `path` equals
`PSeq(...django.db.models...) + PSeq(46) + name` with `name` containing no `.`
— i.e. the part before the last dot is exactly `django.db.models`. G-AX
(`axiom_check.py`) runs the REAL `_serialize_path` on every F2P path and the
boundary/fuzz paths and asserts the deep model agrees (rooted ⇔ short
`models.X` form emitted).

### 3.2 Provenance of the F2P discriminators (no callee axiom needed)
- `test_deconstruct (ValueTests)` / `test_deconstruct_output_field`:
  `Value('name').deconstruct()[0]` must equal `'django.db.models.Value'`
  (post-patch) — pre-patch it was `'django.db.models.expressions.Value'`
  because no `path` was configured and the fallback used
  `obj.__class__.__module__ == 'django.db.models.expressions'`.
- `test_serialize_complex_func_index (WriterTests)`: serializing an `Index`
  over `Func/Case/When/Value/ExpressionWrapper/OrderBy` yields the short
  `models.Func(...)`, `models.Case(...)`, … form with the single import
  `from django.db import models`; this holds iff every node's reported path is
  rooted at `django.db.models` (§3.1), which the configured `path=` produces.

**Soundness check (G-AX):** `axiom_check.py` imports only the standard library
plus the repo's `django.utils.deconstruct` / `django.db.migrations.serializer`
(the unchanged callees the deep model stands in for) and replays the path
choice + rooting check on the F2P inputs and randomized fuzz. Exit 0 iff sound.
