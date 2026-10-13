# mapping.md — django__django-12708

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 447980e72ac01da1594dd3373a03ba40b7ee6f80`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every modeled operation.

Repo file under change: `django/db/backends/base/schema.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectIndexConstraints (cs : List Constraint)` | the composite-index deletion selection performed by `alter_index_together` → `_delete_composed_index` → `_constraint_names(model, columns, **constraint_kwargs)` — `django/db/backends/base/schema.py:396` (call site), `:402` (`_delete_composed_index`), `:1142` (`_constraint_names`) | the modeled changed selection: which constraints on the target columns are selected for deletion |
| `Constraint.isIndex` | `infodict['index']` in `_constraint_names`'s loop (`schema.py:1155`) | whether the constraint provides an index over the columns |
| `Constraint.isUnique` | `infodict['unique']` in `_constraint_names`'s loop (`schema.py:1153`) | whether the constraint enforces uniqueness |
| `Constraint.name` | the constraint `name` key in `_constraint_names`'s loop (`schema.py:1151`) | the constraint's identity |
| `keep (c : Constraint)` | the post-patch filter the kwargs `{'index': True, 'unique': False}` impose inside `_constraint_names`: `infodict['index'] == True and infodict['unique'] == False` (`schema.py:1153-1157`) | per-constraint "selectable" predicate (I — identical concrete op) |
| `selected (cs : List Constraint)` | the list `_constraint_names` returns when called with the post-patch kwargs (`schema.py:1148-1168`) | deep, structural model of the unchanged filtering callee under the patched kwargs (R + I) |

The CHANGED line is the `constraint_kwargs` dict literal passed at `schema.py:396`
(`{'index': True}` → `{'index': True, 'unique': False}`). The filtering callee
`_constraint_names` is **unchanged**; the patch only changes which filter kwargs
it receives. G-CONF runs the real `_constraint_names` with the post-patch kwargs
as the oracle.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the constraints defined on the target columns — the `{name: infodict}` map `get_constraints` returns, restricted to the columns being deleted | `List Constraint` | each `infodict` ↔ one `Constraint`; the map's name-keyed entries ↔ the list elements; iteration order (dict insertion order) ↔ list order |
| `infodict['index']` (bool) | `Constraint.isIndex : Bool` | `True` ↔ `isIndex = true`; `False` ↔ `isIndex = false` |
| `infodict['unique']` (bool) | `Constraint.isUnique : Bool` | `True` ↔ `isUnique = true`; `False` ↔ `isUnique = false` |
| constraint `name` (str) | `Constraint.name : String` | identity on the name string |
| the list of selected constraint names `_constraint_names` returns | `selected cs` (the kept `Constraint`s, in order) | name-for-name correspondence; G-CONF compares the selected `name`s |

A uniqueness constraint over the same columns is typically **index-backed**, so
its `infodict` reports `index = True` AND `unique = True` — this is precisely the
collision the issue describes ("it will find two constraints, the _uniq and the
_idx one"). The `Constraint` carrier models this with `isIndex = true,
isUnique = true`; `keep` drops it (because `isUnique`), the pre-patch predicate
(`isIndex` alone) keeps it.

`_constraint_names` also filters by `column_names`, `exclude`, `primary_key`,
`check`, `foreign_key`, `type_`. For the modeled selection those are held fixed:
all candidate constraints are on the target columns (so the column match is
constant), `exclude` excludes only meta-defined constraints/indexes (orthogonal
to the index/unique flags), and the other kwargs are `None` (not applied). The
only flags the patch's kwargs vary over are `index` and `unique`; the carrier
therefore exposes exactly those two booleans. G-CONF holds the other dimensions
fixed (column-matched, empty exclude, other kwargs `None`) and fuzzes the two
modeled flags, so it tests exactly the dimension the patch changes.

## 3. Callee provenance

**No axioms; no deep-model references (A-reference); no consumed axioms
(A-consumed).** The single thing the patch changes — the `constraint_kwargs`
filter — is modeled **identically** (`keep`), and the surrounding selection
performed by the unchanged `_constraint_names` callee is a structural refinement
(`selected` over the flattened constraint list). Every step is therefore R or I
(see refinement.md), all mechanically checked by G-CONF against the real
`_constraint_names` run with the post-patch kwargs. There is no unchanged opaque
callee whose contract the proof must *assume* (G-CONF runs the real callee, it is
not axiomatized), so `axiom_check.py` (G-AX) has no axiom `ensures` to validate
and exits 0 after confirming the bundle declares none and that the
`index`/`unique` filter semantics of the real `_constraint_names` match the §2
bijection.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12708`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `keep`/`selected` (R/I-tagged ops) to Python and compares the
resulting selected-name list against the real `_constraint_names` invoked with
the post-patch kwargs `index=True, unique=False` over fuzzed constraint maps.
There are no A-tagged callees to leave as real-callee calls beyond
`_constraint_names` itself, which is exercised for real as the oracle.
