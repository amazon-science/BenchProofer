# mapping.md — django__django-15161

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 96e7ff5e9ff6362d9a886545869ce4496ca4b0fb`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance.

Repo file under change: `django/db/models/expressions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `deconstructPath (definingModule className : List Char) (publicPath : Option …) (exactType : Bool)` | `deconstruct()` of a `@deconstructible`-decorated expression node — the closure installed by `deconstructible(...)` in `django/utils/deconstruct.py:20` (the `deconstruct` inner fn, lines 20–47) | the modeled changed behavior: which import path `deconstruct()` reports for an expression node |
| `definingModule` | `obj.__class__.__module__` (`deconstruct.py:29`) | the fully-qualified module the node's class is actually defined in (always `django.db.models.expressions` for these nodes) |
| `className` | `name` = `obj.__class__.__name__` (`deconstruct.py:30`) | the node's class name |
| `publicPath` | the decorator's `path` kwarg captured in the `deconstruct` closure (`deconstruct.py:6, 26, 43`) — `some p` iff the node's type (or an ancestor type) was decorated `@deconstructible(path=p)`, else `none` | the assigned *simplified* public import path |
| `exactType` | `type(obj) is klass` (`deconstruct.py:26, 42`) — true iff the node's runtime type is exactly the class the `path` was assigned to | whether the simplified public path applies to this exact type |

The gold patch adds `@deconstructible(path='django.db.models.X')` to six classes
in `django/db/models/expressions.py` — `Func` (line 654), `Value` (734),
`ExpressionWrapper` (956), `When` (988), `Case` (1056), `OrderBy` (1230). Each
of these types is also re-exported from `django.db.models`
(`django/db/models/__init__.py:14-15, 43-45`), so the simplified public path is a
valid import path for the type. `F` was already decorated this way by the prior
PR #14047 (line 581, `path='django.db.models.F'`) and is the precedent the issue
cites; the patch extends the same technique to the other five.

The behavior `deconstruct()` selects (`deconstruct.py:42-46`):
```python
path if path and type(obj) is klass else f'{obj.__class__.__module__}.{name}'
```
i.e. the assigned simplified public path when present **and** the runtime type is
exactly the decorated class; otherwise the defining-module-qualified class name.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a dotted import path `str` (`deconstruct()[0]`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; the `.` separator ↔ `['.']` |
| `obj.__class__.__module__` (a `str`) | `definingModule : List Char` | str ↔ `List Char` |
| `obj.__class__.__name__` (a `str`) | `className : List Char` | str ↔ `List Char` |
| the decorator `path` kwarg: a `str` or absent | `publicPath : Option (List Char)` | `path is not None` ↔ `some p`; `path is None` (undecorated) ↔ `none` |
| `type(obj) is klass` (a `bool`) | `exactType : Bool` | Python `bool` ↔ Lean `Bool` |
| the f-string `f'{module}.{name}'` (`deconstruct.py:45`) | `definingModule ++ ['.'] ++ className` | string interpolation with a literal `.` ↔ list concat with `['.']` |

`deconstruct()` also returns positional args (`obj._constructor_args[0]`) and
kwargs (`obj._constructor_args[1]`); the patch does NOT touch those — only the
path (element 0) changes — so they are out of the modeled frame (the F2P
`test_deconstruct` asserts `args`/`kwargs` are unchanged, which the patch
preserves by construction since it edits only the decorator).

## 3. Callee provenance

No axiomatized callees and no A-reference deep models of a separate callee. The
import-path selection IS the function under specification; it is modeled
directly and deeply as the two-way choice in `deconstructPath`. There is no
unchanged outside callee whose contract the proof must assume — hence no `axiom`
declaration, no `axiom_check.py`, and G-AX is `skip` (precedent:
`tasks/astropy__astropy-14995`, also a no-axiom config/branch change).

### 3.1 The public-path registry (G-CONF data, not a callee)
The data the patch introduces — which class gets which simplified public path —
is the discrete input data of this change, analogous to the per-character
substitution table of `tasks/django__django-11276`'s conformance shadow. G-CONF
declares it explicitly:

| class | `publicPath` | also re-exported from |
|---|---|---|
| `F` (pre-existing precedent) | `django.db.models.F` | `django.db.models` |
| `Func` | `django.db.models.Func` | `django.db.models` |
| `Value` | `django.db.models.Value` | `django.db.models` |
| `ExpressionWrapper` | `django.db.models.ExpressionWrapper` | `django.db.models` |
| `When` | `django.db.models.When` | `django.db.models` |
| `Case` | `django.db.models.Case` | `django.db.models` |
| `OrderBy` | `django.db.models.OrderBy` | `django.db.models` |

A *subclass* of a decorated class (e.g. `ExpressionList`, `OrderByList` — both
subclass `Func`; `OuterRef`, `ResolvedOuterRef` — both subclass `F`) inherits
the closure `path` but has `type(obj) is klass = False`, so its `publicPath` is
`some <ancestor path>` but `exactType = false` → the long defining-module path
is reported. An undecorated expression class (e.g. `RawSQL`, `Col`, `Star`,
`Ref`) has `publicPath = none`. G-CONF's shadow derives `(publicPath, exactType)`
from this registry; the oracle runs the real `deconstruct()`; the two are
independent derivations that must agree.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15161`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`deconstructPath`'s two-way choice (R/I-tagged ops) to Python over the real
`str` carriers; there are no A-tagged callees, so the shadow is pure R/I.
