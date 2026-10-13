# mapping.md — django__django-15104

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a7e7043c8746933dafce652507d3b821801cdc7d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each modeled sub-step. **This bundle has no consumed axioms and no
deep-model reference to a library callee** (G-AX skips — meta.json); the only
unchanged callees are modeled as free inputs (§3).

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fieldDefsIgnoringRelationTargets (fields : List FieldDef)` | `MigrationAutodetector.only_relation_agnostic_fields(self, fields)` — `django/db/migrations/autodetector.py:89` (changed body line 99) | the modeled changed function |
| `FieldDef` | one `(name, field)` entry of the `fields` mapping the method iterates (`autodetector.py:96`) | the touched facets of one field (§2) |
| `FieldDef.relational` | `field.remote_field and field.remote_field.model` (`autodetector.py:98`) | whether the field references another model |
| `FieldDef.kwargs` | the keyword-bindings dict `deconstruction[2]` produced by `self.deep_deconstruct(field)` (`autodetector.py:97`, dict component) | the field's canonicalized keyword bindings |
| `dropTarget` / `targetKey = "to"` | the relation-target elision the changed line performs on `deconstruction[2]` (`autodetector.py:99`) | drop the `'to'` binding |
| `fieldView` | per-field result appended to `fields_def` (`autodetector.py:100`) | the comparison view of one field |
| `viewAll` | the assembled `fields_def` list returned (`autodetector.py:101`) | deep model of the whole routine's output |

### 1.1 The change (gold hunk)
```
 if field.remote_field and field.remote_field.model:
-    del deconstruction[2]['to']
+    deconstruction[2].pop('to', None)
```
`del d['to']` raises `KeyError` when the relational field's deconstructed kwargs
carry **no** `'to'` binding (the issue: a custom `ForeignKey` that hardcodes its
`to` and removes it from its own `deconstruct()` kwargs). `pop('to', None)`
removes the binding when present and is a no-op otherwise — **never raises**.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `fields` mapping, iterated as `sorted(fields.items())` | `List FieldDef`, in ascending field-name order | the `sorted` ordering is reproduced by presenting the list already name-sorted; `sorted` is an unchanged callee, modeled as the chosen input order (free — §3) |
| `field.remote_field and field.remote_field.model` (truthiness) | `FieldDef.relational : Bool` | a relational field ↔ `relational = true`; a non-relational field ↔ `false`. The exact relation object is orthogonal — only the truthiness is consulted (free input — §3) |
| `deconstruction[2]` — the kwargs dict from `deep_deconstruct(field)` | `FieldDef.kwargs : List (String × Int)` | each `(key, value)` ↔ `(key, identity-token)`; the value is never inspected, only carried and keyed, so an opaque `Int` token is faithful. Dict ↔ ordered assoc-list; key membership ↔ `p.1 == "to"` |
| `del`/`pop('to', None)` result kwargs dict | `dropTarget kw` (= `kw.filter (·.1 ≠ "to")`) | the resulting bindings keyed by everything except `"to"` |
| raising / not raising | `Except Unit α` (`Except.error ()` = raised; `Except.ok` = completed) | the gold routine never raises ⇒ always `Except.ok (viewAll fields)`. The pre-patch raises on a relational field lacking `"to"` (modeled in `Solution_prepatch.lean`) |

`deep_deconstruct(field)` is itself an **unchanged** callee: its kwargs output is
taken as the given input `FieldDef.kwargs` (free — §3), not modeled or
axiomatized. The patch touches only what is done *to* that dict.

## 3. Callee provenance (free inputs — directive 7, no axioms)

Three callees the routine consults are **unchanged** by the patch and are modeled
as FREE inputs whose every value the postcondition tolerates — strictly weaker
than any concrete contract, so none is owed an axiom (SPEC_GUIDE §0.7, §3):

- **`deep_deconstruct(field)`** — canonicalizes a field to `(path, args, kwargs)`.
  Its `kwargs` component is the free input `FieldDef.kwargs`. The patch does not
  change it; the spec holds for every value of it.
- **`field.remote_field and field.remote_field.model`** — the relational test, the
  free Boolean `FieldDef.relational`. The spec holds for both values.
- **`sorted(fields.items())`** — orders the iteration by field name. Unchanged;
  modeled as the (caller-chosen) order of the input list. The per-field views are
  independent, so order only permutes the output list identically on both sides.

There is **no** modeled library callee whose behavior the proof relies on, hence
**no consumed axiom and no A-reference**. `axiom_check.py` is therefore omitted
(G-AX skips — gates.py `gate_ax`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15104`** so the
consumer-side verdict (§11.3) is reproducible. The shadow transliterates
`fieldView`/`viewAll`/`dropTarget` (R/I-tagged ops) to Python over the real
`deep_deconstruct` kwargs of fuzzed fields, and the oracle is the REAL
gold-patched `only_relation_agnostic_fields` driven over the same fields —
including the hardcoded-`to` custom-FK shape that triggers the issue.
