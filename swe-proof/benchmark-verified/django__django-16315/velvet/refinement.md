# refinement.md — django__django-16315

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `conflictColumns` `do` block and the pure `dbColumns` fold over the `Field`
structure) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** / **A-reference**), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The conflict-target / updated-column site

The bug: the `ON CONFLICT(...) DO UPDATE SET ...` clause referenced each field
by its **model attribute name** instead of its **database column**, so a field
declared with an explicit (e.g. mixed-case) database column produced an invalid
SQL identifier. The fix makes the conflict-resolution clause use each field's
database column.

Gold hunks (`django/db/models/sql/compiler.py:1725-1729`, `SQLInsertCompiler.as_sql`):
```
  on_conflict_suffix_sql = self.connection.ops.on_conflict_suffix_sql(
      fields,
      self.query.on_conflict,
-     self.query.update_fields,
-     self.query.unique_fields,
+     (f.column for f in self.query.update_fields),
+     (f.column for f in self.query.unique_fields),
  )
```
Enabling hunks (`django/db/models/query.py`): the caller-supplied field-name
strings are resolved to `Field` objects (`self.model._meta.get_field(name)`)
in `bulk_create` so the `Field` objects — not strings — reach
`self.query.update_fields` / `self.query.unique_fields`; the now-redundant
resolution inside `_check_bulk_create_options` is removed.

| # | Solution.lean impl op (`conflictColumns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fields : List Field` | `self.query.update_fields` / `self.query.unique_fields` (now lists of resolved `Field` objects) | R | the resolved `Field` list ↔ `List Field` (mapping.md §2). How each `Field` was obtained from the caller's name strings (`get_field`) is UNCHANGED and upstream of this boundary, hence a free input (mapping.md §1, §3) — not modeled, no axiom. |
| A2 | `dbColumns fields`: the per-field column expansion `[f₀.column, f₁.column, …]`, computed by the backward `while` fold | `(f.column for f in self.query.update_fields)` / `(... for f in self.query.unique_fields)` | R + I | the changed operation is modeled **deeply and concretely**: `dbColumns`/the `Field.column` projection and the verified loop ARE the comprehension. `f.column` is an UNCHANGED pure projection carried by the structure's `column` field (mapping.md §2), so it is plain **R**, NOT an A-reference (no algorithm to validate against a real callee). The fold ops (`[f.column]`, `++`, the loop) are **I** (concrete, transliterated by G-CONF). |
| A3 | the SAME `conflictColumns` covers both argument positions | the two comprehensions are identical-shaped (one for `update_fields`, one for `unique_fields`) | I | one model, applied twice; the operation is the same per-field column extraction. |

Discriminating content of the change — emit `f.column`, not `f.attr` — lives in
`dbColumns (f :: fs) = [f.column] ++ …` (model) ⇔ `(f.column for f in …)` (real).
The pre-patch code passed the field *names* (`self.query.update_fields` etc.
were still name strings, and the suffix builder quoted them directly);
`Solution_prepatch.lean` reproduces that by prepending `f.attr` and **fails**
`out = dbColumns fields` exactly when a field's attribute name differs from its
column (G-DIFF; the unsolved goal is literally `f.attr = f.column`).

## B. No consumed axiom, no deep-model reference

`get_field` (name → `Field`) is **unchanged** and upstream of the modeled
boundary — the patch only relocates the call so `Field` objects (not strings)
propagate; it resolves the same fields pre- and post-patch and cannot cause a
resolve/not-resolve divergence. The conflict-suffix builder
(`on_conflict_suffix_sql`) is **unchanged** and downstream (it quotes/joins
whatever tokens it gets). `Field.column` is an **unchanged** pure projection
carried directly by the structure. Therefore:

* **No A-consumed axiom** — nothing about a changed callee's contract is assumed.
* **No A-reference deep model** — `Field.column` has no algorithm to spell out;
  it is plain R (a carried attribute), validated by G-CONF building the oracle
  from real `Field` objects, not by G-AX. `meta.json`: `axioms: []`,
  `deep_model_references: []`, G-AX `skip` (no `axiom_check.py`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — referring to
each field by its column rather than its name — is modeled **deeply** (the
spelled-out fold `dbColumns`, step A2, R + I), not hidden behind an axiom about
the function under change. There are no consumed axioms at all.

## D. verify(Solution) ⇒ resolved

`conflictColumns` verifies only if its output equals the exact per-field column
expansion `dbColumns fields` (A2) — i.e. each field contributes its `column`, in
order. By R (`Field` ↔ resolved field object, `List Char` ↔ `str`, `List` order
↔ generator order) the verified operation equals `(f.column for f in fields)` on
the tested inputs; the surrounding suffix builder and `get_field` resolution are
unchanged. By G-CONF the R/I transliteration of the fold agrees with real
Django `Field.column` behaviour on ≥10⁵ inputs. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The only trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust point
because there are no axioms.
