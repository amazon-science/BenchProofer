# mapping.md — django__django-11551

Cold spec (`spec_provenance: "cold"`): derived only from `problem_statement`, the
gold `patch`, and the real repo source at
`base_commit = 7991111af12056ec9a856f35935d273526338c1f`. Binds every
`Solution.lean` symbol to its repository counterpart, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the (non-)axioms.

Repo file under change: `django/contrib/admin/checks.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `listDisplayItemCheck (isCallable) (hasAttrObj) (getFieldRaises) (modelAttrRaises) (fieldIsM2M)` | `ModelAdminChecks._check_list_display_item(self, obj, item, label)` — `django/contrib/admin/checks.py:718` | the modeled changed function: how one display-configuration entry is reported (acceptable / E108 / E109) |
| `listDisplayItemOutcome` *(deep model — R/I)* | the body of `_check_list_display_item` (`checks.py:719-749`) | pure spec: the acceptable/E108/E109 decision as a closed function of the five abstracted observations |
| `CheckResult.ok` | `return []` (no `checks.Error`) | the entry is acceptable |
| `CheckResult.e108` | `return [checks.Error("…not a callable, an attribute of '%s', or an attribute or method on '%s.%s'…", id='admin.E108')]` (`checks.py:738-748` post-patch) | the entry resolves to nothing usable |
| `CheckResult.e109` | `return [checks.Error("…must not be a ManyToManyField.", id='admin.E109')]` (`checks.py:751-758` post-patch) | the entry resolves to a many-to-many relation |

The pre-patch repo state the change addresses (refinement audit only, not in the
consumer spec view): the function gated field resolution on
`elif hasattr(obj.model, item)` (`checks.py:722` pre-patch). When
`hasattr(obj.model, item)` was false it returned `E108` immediately WITHOUT ever
trying `obj.model._meta.get_field(item)`. A field whose descriptor raises on
class-level access (the `PositionField` of the issue) makes `hasattr` false even
though the field registry knows the name, so a valid field was wrongly reported
`E108`. The gold patch removes that gate: it consults the field registry first
(`get_field`), and only on `FieldDoesNotExist` falls back to `getattr`, reporting
`E108` only when BOTH raise.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The five method inputs abstract the runtime observations the decision depends
on. This is the table G-CONF (§4.1) uses to translate values between the Lean
value domain and the Python repo behaviour. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `callable(item)` — the entry is itself an invokable object | `isCallable : Bool` | `True ↔ true`; `False ↔ false` |
| `hasattr(obj, item)` — the entry names an attribute of the administrator instance | `hasAttrObj : Bool` | `True ↔ true`; `False ↔ false` |
| `obj.model._meta.get_field(item)` raises `FieldDoesNotExist` — the model's field registry does not know the name | `getFieldRaises : Bool` | raises `↔ true`; returns a field `↔ false` |
| `getattr(obj.model, item)` raises `AttributeError` — plain attribute access on the model class fails (equivalently `not hasattr(obj.model, item)`) | `modelAttrRaises : Bool` | raises `↔ true`; returns a value `↔ false` |
| `isinstance(field, models.ManyToManyField)` — the resolved descriptor is a many-to-many relation | `fieldIsM2M : Bool` | `True ↔ true`; `False ↔ false` |
| the report produced for the entry | `CheckResult` | `[] ↔ ok`; `[Error(id='admin.E108')] ↔ e108`; `[Error(id='admin.E109')] ↔ e109` (the only observable is the error id — the F2P/P2P tests compare `Error` objects, whose discriminating content here is the `id`) |

Notes on the abstraction faithfulness (the join G-CONF validates):

* `fieldIsM2M` is meaningful only on the paths where a field is actually
  resolved (registry hit, or `getattr` success after a registry miss). On the
  `e108` path (both routes fail) no field exists; `listDisplayItemOutcome` never
  inspects `fieldIsM2M` there, matching the real control flow.
* The post-patch real code obtains the field from `get_field` when
  `getFieldRaises = false`, else from `getattr`; in both cases it then tests
  `isinstance(field, ManyToManyField)`. `fieldIsM2M` is that single test applied
  to whichever field was resolved — the model collapses the two field sources
  into one boolean because the subsequent M2M test is identical for both
  (`checks.py:750` post-patch is a single shared `if isinstance(...)`).

## 3. Callee provenance (kind-A)

**None.** There are no axiomatized callees and no deep-model references to an
unchanged callee. The entire changed behaviour is a closed function of five
abstracted boolean observations and is modeled deeply in the `pure` region
(`listDisplayItemOutcome`). G-AX is therefore skipped (no `axiom_check.py`); the
abstraction of the five inputs from the real `callable` / `hasattr` /
`get_field` / `getattr` / `isinstance` observations is an R-refinement validated
by G-CONF, not an axiom.

`checks.Error(...)` construction (the unchanged way a message is packaged) is NOT
modeled beyond its observable `id`: the issue and the tests observe which error
id is produced (or none), which is exactly what `CheckResult` captures. The
message string, `obj=`, and `id=` are produced verbatim by the unchanged
`checks.Error` call on each branch; the patch does not change the message text on
the E108/E109 branches (only which branch is reached), so the error id is the
complete observable of the changed decision.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11551`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`listDisplayItemOutcome` (the R/I-tagged decision) to Python and compares it,
over the full boundary cross-product of the five observations plus fuzz, against
the real patched `_check_list_display_item` behaviour: it constructs, for each
input combination, real `ModelAdmin` / model classes that realize those
observations (a callable display item; a method on the admin; a field whose
registry lookup hits or misses; a class-level descriptor whose `getattr`
succeeds or raises — including the issue's `PositionField`; a `ManyToManyField`
vs an ordinary field), runs the patched check, and reads back the resulting
error id (or `[]`). There are no A-tagged callees to leave as the real repo
callee.
