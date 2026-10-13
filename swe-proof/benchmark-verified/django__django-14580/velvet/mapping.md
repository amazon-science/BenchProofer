# mapping.md — django__django-14580

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 36fa071d6ebd18a61c4d7f1b5c9d17106134bd44`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance (there are none consumed — see §3).

Repo file under change: `django/db/migrations/serializer.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderTypeRef (t : TypeInfo)` | `TypeSerializer.serialize(self)` — `django/db/migrations/serializer.py:274` (class at :273) | the modeled changed function: render a runtime type to its source reference + the imports that reference needs |
| `typeRef (t : TypeInfo)` | the body of `TypeSerializer.serialize` (`special_cases` table + the `__module__`/`builtins`/`__qualname__` tail, `serializer.py:275-289`) | pure spec: the `(string, imports)` a type is serialized to |
| `TypeInfo` | the runtime `type` object held in `self.value` (the touched fields only — see §2) | pure spec: the observable slice of a Python type |
| `TypeInfo.isBaseModelType` | `self.value is models.Model` — first row of `special_cases` (`serializer.py:276`) | flag: the type is the framework base-model class `django.db.models.Model` |
| `TypeInfo.isNoneType` | `self.value is type(None)` — second row of `special_cases` (`serializer.py:277`) | flag: the type is `type(None)` (the `NoneType`) |
| `TypeInfo.moduleName` | `self.value.__module__` (`serializer.py:285-286`) | the type's defining module name |
| `TypeInfo.qualName` | `self.value.__qualname__` (`serializer.py:289`) | the type's qualified (dotted) name |
| `TypeInfo.simpleName` | `self.value.__name__` (`serializer.py:288`) | the type's bare name (used in the `builtins` branch) |

The pre-patch text the change edits (refinement audit only, not in the consumer
spec view): the first `special_cases` row's empty import list
`(models.Model, "models.Model", [])` at `serializer.py:276`, which the gold
patch replaces with `(models.Model, "models.Model", ['from django.db import models'])`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement (the falsifiability the plan §4 trust statement relies on).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the runtime `type` object `self.value` | `TypeInfo` structure | a Python `type` ↔ the record of its observable fields: `isBaseModelType = (v is models.Model)`, `isNoneType = (v is type(None))`, `moduleName = getattr(v,'__module__','')`, `qualName = v.__qualname__`, `simpleName = v.__name__`. Only these fields are observed by `serialize`. |
| the returned source string | Lean `String` | identity; Python `str` ↔ Lean `String`; `"%s.%s" % (m, q)` ↔ `m ++ "." ++ q`; `"import %s" % m` ↔ `"import " ++ m` |
| the returned `imports` **set** | Lean `List String` | `set(imports)` ↔ the list literal; for the four branches the list has 0 or 1 element, so set vs. list is observationally identical (no duplicates, order irrelevant — G-CONF compares as sets). mapping.md §2a. |
| `models.Model` identity | `isBaseModelType : Bool` | `v is models.Model` ↔ `isBaseModelType = true`. `models.Model` is the unique base-model class; at most one special case fires (the two `is` checks test distinct singletons). |
| `type(None)` identity | `isNoneType : Bool` | `v is type(None)` ↔ `isNoneType = true`. Distinct from `models.Model`, so `isBaseModelType ∧ isNoneType` never both hold for a real type. |

### 2a. The two-element `special_cases` loop is unrolled, faithfully
The source iterates a literal two-row list `special_cases` with `if case is
self.value: return ...`. Because the table is a fixed two-element literal whose
guards are mutually-exclusive identity tests (`is models.Model`, `is
type(None)`), the loop is observationally a two-arm ordered `if/elif` ladder:
row 0 fires iff `isBaseModelType`, else row 1 fires iff `isNoneType`, else fall
through to the `__module__` tail. `renderTypeRef` models exactly that unrolled
ladder (the Velvet `for`-loop ban, plan §3, is irrelevant here because the loop
carries no iteration-dependent state — it is a static dispatch). The unrolling
is exact, not an approximation: a third special case would change the source,
and there is none.

## 3. Callees — none consumed

`TypeSerializer.serialize` performs no call whose contract the proof consumes.
The only sub-expressions are attribute reads (`__module__`, `__qualname__`,
`__name__`), identity comparisons (`is`), string `%`-formatting and `set()`
construction — all R/I-modeled directly (§2). There is therefore **no
module-level `axiom`** and **no `:|` imperative-callee stub**; `meta.json`
`axioms` and `deep_model_references` are empty, and **G-AX is `skip`** (no
`axiom_check.py`). The entire impl region is R/I-tagged, so G-CONF carries the
full mechanical refinement check (and `conf_skip = false`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14580`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`typeRef`/`renderTypeRef` (all R/I ops) to Python and runs the REAL patched
`TypeSerializer.serialize` (via `MigrationWriter.serialize`) as the oracle over
fuzzed types, comparing `(string, set_of_imports)` for equality.
