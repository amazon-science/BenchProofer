# mapping.md — django__django-12754

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 18759b2209ff556aed7f20d83cbf23e3d234e41c`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee/flag provenance.

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `movedBaseFields (oldBaseFields newBaseFields : Option (List Int)) (derivedFields : List Int)` | the added block inside `MigrationAutodetector.generate_created_models` (`django/db/migrations/autodetector.py:563-578`, the `for base in model_state.bases:` body) | the modeled changed computation: which of a newly created derived model's fields were just removed from its (string) base, hence must be sequenced after that removal |
| `oldBaseFields : Option (List Int)` | `set(old_base_model_state.fields)` where `old_base_model_state = self.from_state.models.get((base_app_label, base_name))` (`autodetector.py:567`) | the base model's field-name set BEFORE the change; `none` ⇔ `self.from_state.models.get(...)` is falsy (base absent before) |
| `newBaseFields : Option (List Int)` | `set(new_base_model_state.fields)` where `new_base_model_state = self.to_state.models.get((base_app_label, base_name))` (`autodetector.py:568`) | the base model's field-name set AFTER the change; `none` ⇔ `self.to_state.models.get(...)` is falsy (base absent after) |
| `derivedFields : List Int` | `model_state.fields` — the created (derived) model's own field names (`autodetector.py:574`, the `.intersection(model_state.fields)`) | the created model's own field-name set |
| `isMoved oldBase newBase n` | the per-field membership test of `set(old).difference(new).intersection(model_state.fields)` (`autodetector.py:571-574`) | one field name qualifies iff base present both sides ∧ removed from base ∧ in derived model |
| `movedFold oldBase newBase derived` | `removed_base_fields = set(old_base_model_state.fields).difference(new_base_model_state.fields).intersection(model_state.fields)` (`autodetector.py:571-574`) | the set of derived-model field names made into removal dependencies |
| `out` (the returned list) | `for removed_base_field in removed_base_fields: dependencies.append((base_app_label, base_name, removed_base_field, False))` (`autodetector.py:575-577`) — the SET of `removed_base_field` values appended | the field names the created model's operation is made to depend on |

The guard `if old_base_model_state and new_base_model_state:` (`autodetector.py:569`)
is modeled by the `Option`/`Option` `match` in `isMoved`: when either side is
`none`, no field qualifies (`movedFold_none_left` / `movedFold_none_right`),
exactly mirroring the short-circuit when either `.get(...)` returns a falsy
state.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a field NAME (`str` key of `ModelState.fields`, an ordered dict) | `Int` | each distinct field name ↔ a distinct integer identifier; membership/equality only — the spec never inspects name characters. `f in fields` ↔ `f ∈ (xs : List Int)`; set difference/intersection ↔ the `isMoved` membership predicate. |
| `set(model_state.fields)` (a Python `set` of field names) | `List Int` | the field-name collection; order is irrelevant to the observable (the patch wraps the result in a `set` and iterates it to append deps), so G-CONF compares the result as a SET. The Lean `movedFold` preserves derived-field order; `movedFold_mem` proves no name is invented. |
| `self.{from,to}_state.models.get((app,name))` — a `ModelState` or `None` | `Option (List Int)` | a present base state ↔ `some (its field-name set)`; an absent base (`.get` → `None`, falsy) ↔ `none`. Only the base's `.fields` key set is observed (the bijection above); no other `ModelState` attribute enters the computation. |
| `dependencies.append((base_app, base_name, field, False))` | membership of `field` in `out` | the observable is WHICH field names become removal dependencies; `base_app`/`base_name`/the `False` create/delete flag are constants for the fixed base and are not modeled (R-identity). |

`base_app_label`, `base_name`, and the `False` flag (`autodetector.py:577`) are
constants determined by the fixed base string and the dependency kind; they are
R-identities not carried into the spec. The single behavioural content is the
field-name SET, which is exactly `movedFold`.

## 3. Callee provenance

**No axioms / no deep-model references.** The modeled computation is a closed set
operation over three field-name collections read directly from the migration
project states (`set.difference(...).intersection(...)`). It consults no
unchanged library callee whose contract the proof must assume; `set.difference`
and `set.intersection` are Python built-ins transliterated directly as the
`isMoved` membership predicate (an **I** op, not an axiomatized callee). Hence
`axioms = []` and `deep_model_references = []`; there is no `axiom_check.py` and
G-AX is `skip` (mirrors django__django-11163, an axiom-free filter-fold bundle).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12754`**. The R/I shadow
it builds transliterates `isMoved`/`movedFold` (R/I-tagged ops) to Python and
diffs the field-name set the shadow predicts against the field-removal
dependencies the REAL gold-patched `generate_created_models` appends for the
created derived model, over boundary cases (incl. the exact issue shape:
`Readable.title` removed, moved onto `Book`) plus randomized fuzz, driving the
real autodetector over in-memory `ProjectState`s (the DB-free `get_changes`
flow). Exit 0 iff zero disagreements.

**Valid-domain constraint.** A concrete multi-table-inheritance subclass may NOT
redeclare a field that still exists on its base: Django model validation rejects
that as a field clash (`Local field 'x' in class 'Sub' clashes with field of the
same name from base class 'Base'`) and the autodetector never reaches the modeled
block for such a model. The conformance fuzzer therefore restricts derived-model
fields to the union of *removed* base fields (those moved down — the issue's
shape) and *fresh* names never on the base, guaranteeing
`derivedFields ∩ newBaseFields = ∅`. Configurations violating this are outside
the function's real input space and are not generated. This is a domain
restriction on the differential test, not a weakening of the frozen spec
(`Solution.lean` is unchanged): the spec's `movedFold` is still total over all
`List Int`, but only valid Django states can actually drive the real callee.
