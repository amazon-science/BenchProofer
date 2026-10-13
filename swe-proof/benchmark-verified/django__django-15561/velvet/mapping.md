# mapping.md — django__django-15561

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6991880109e35c879b71b7d9d9c154baeec12b89`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo files under change:
- `django/db/backends/base/schema.py` (`_field_should_be_altered`)
- `django/db/models/fields/__init__.py` (`Field.non_db_attrs`)

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `decideSchemaAlteration (a b : FieldDef)` | `BaseDatabaseSchemaEditor._field_should_be_altered(self, old_field, new_field)` — `django/db/backends/base/schema.py:1372` (body lines 1373-1398) | the modeled changed function (decide whether replacing one field definition with another requires rewriting the stored column) |
| `FieldDef` | the observable projection of a `django.db.models.Field` used by `_field_should_be_altered`: its quoted column name, its schema-relevant reconstructed identity, and its enumerated choices | type carrier for one field definition |
| `FieldDef.quotedColumn` | `self.quote_name(field.column)` — `schema.py:1396-1397` | quoted column name |
| `FieldDef.schemaIdentity` | `(path, args, kwargs)` from `field.deconstruct()` with the schema-irrelevant attributes removed — `schema.py:1373-1374,1393-1398` | schema-relevant identity |
| `FieldDef.choices` | the `choices` kwarg of `field.deconstruct()` — pulled out separately | presentation-only attribute |
| `schemaAlterationNeeded (a b : FieldDef)` | the boolean returned by `_field_should_be_altered` post-patch — `schema.py:1396-1398` | pure spec: the decision |

The projection callees `field.deconstruct()` and `schema_editor.quote_name()`
are **unchanged** by the patch; they are the R-refinement bridge (§2), exercised
against the real callees by G-CONF (conformance_check.py). There is no axiom in
this bundle: the changed decision logic is modeled directly in the `pure` region
and the projection callees are concrete repo functions run live by G-CONF.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `django.db.models.Field` instance `f` | `FieldDef` | `f` ↔ `⟨quote_name(f.column), schemaIdentity(f), repr(choices(f))⟩`; projection via the unchanged `f.deconstruct()` + `schema_editor.quote_name()` |
| `self.quote_name(field.column)` (a `str`) | `FieldDef.quotedColumn : String` | identity on the quoted-name string |
| `(path, args, kwargs∖non_db_attrs∖{choices})` from `deconstruct()` | `FieldDef.schemaIdentity : String` | the schema-relevant reconstruction, serialized canonically (`repr` of `(path, args, sorted(kwargs.items()))`); equal iff the two reconstructions are equal as Python tuples |
| the `choices` kwarg (a list of pairs, or absent) | `FieldDef.choices : String` | `repr(choices)`; carried but **not consulted** by the decision |
| the returned `bool` | `Bool` | `True` ↔ `true`, `False` ↔ `false` |

### 2.1 What `schemaIdentity` strips (the unchanged `non_database_attrs` set)

The schema-irrelevant attributes removed from both reconstructed kwargs before
forming `schemaIdentity` are the **pre-patch** `non_database_attrs` list — the
attributes already known not to affect a column's schema:

```
blank, db_column, editable, error_messages, help_text, limit_choices_to,
on_delete, related_name, related_query_name, validators, verbose_name
```

`choices` is **not** in this list. Instead `choices` is split out into
`FieldDef.choices`, and the decision `schemaAlterationNeeded` (§ pure region)
simply never consults it. This is the modeled behaviour: the gold patch makes
`_field_should_be_altered` ignore a `choices`-only difference by adding
`"choices"` to the attribute list it pops; the Lean model encodes the same
end-state — a `choices`-only difference never requires a rewrite — by giving
`choices` its own observable field that the decision does not read. The
prepatch (`Solution_prepatch.lean`) instead treats `choices` as part of the
rewrite decision and so fails `out = schemaAlterationNeeded a b` exactly when
`a` and `b` differ only in `choices` (G-DIFF).

Note `db_column` is in the stripped set: a `db_column`-only change that leaves
the *resulting* column name unchanged is already a noop pre-patch (the issue
concerns `choices`). The quoted column name is compared separately via
`quotedColumn`, so a `db_column` change that *renames* the column is still
correctly detected as needing a rewrite.

## 3. Callee provenance

No axioms (A-consumed) and no deep-model references (A-reference) in this bundle.
The two callees the modeled function uses — `field.deconstruct()` and
`schema_editor.quote_name(field.column)` — are **unchanged** by the patch and are
run **live** (the real repo functions) inside G-CONF's shadow projection, not
axiomatized. They are part of the R-refinement bridge, validated by the
conformance differential, so `axiom_check.py` is absent (G-AX skips: no axioms).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15561`** so the
consumer-side verdict is reproducible. The R/I shadow it builds projects real
`Field` objects to `FieldDef` via the unchanged `deconstruct()`/`quote_name()`
callees and applies `schemaAlterationNeeded` (the impl's I-logic), comparing
against the patched `_field_should_be_altered` (the patch.diff oracle) over the
12 deterministic boundary pairs plus 100 000 fuzzed field pairs (biased toward
single-attribute differences, with `choices`-only diffs over-weighted). Zero
disagreements ⇒ exit 0. No `hypothesis` dependency (stdlib + django only).
