# mapping.md — django__django-15278

## Symbol binding (file:line @ base_commit 0ab58c120939093fea90822f376e1866fc714d1f)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_requiresTableRebuild` / `problem_spec_requiresTableRebuild` | the boolean routing decision inside `DatabaseSchemaEditor.add_field` that selects `self._remake_table(...)` (reconstruct) vs. `super().add_field(...)` (plain in-place add) | `django/db/backends/sqlite3/schema.py:325-333` |
| `ColumnProps` (pure helper) | the four field/column attributes the decision consults | see field note below |

The modeled function is the decision predicate at the head of
`DatabaseSchemaEditor.add_field` (sqlite3 backend). Only the truth value of this
predicate changes behavior: `True` → the table is reconstructed via
`_remake_table`; `False` → the plain in-place column addition
(`super().add_field`) is used. Everything downstream of the branch is unchanged
by the patch.

### What the decision does (base_commit, pre-patch)

```python
def add_field(self, model, field):
    """Create a field on a model."""
    # Fields with default values cannot by handled by ALTER TABLE ADD
    # COLUMN statement because DROP DEFAULT is not supported in
    # ALTER TABLE.
    if not field.null or self.effective_default(field) is not None:
        self._remake_table(model, create_field=field)
    else:
        super().add_field(model, field)
```

Pre-patch the decision is `not field.null or effective_default(field) is not
None`. It reconstructs the table for a non-nullable column or a column with a
stored default, and otherwise does the plain in-place column addition.

**The observable bug.** The plain in-place column-addition statement on this
backend cannot append a primary-key column or a uniqueness-bearing column. A
nullable, default-free column that is nonetheless `unique` (e.g. a one-to-one
relation column, which sets `unique = True`) takes the `else` branch pre-patch
and the in-place addition fails. The F2P test `test_add_field_o2o_nullable` adds
a nullable one-to-one column and asserts the column is materialized.

### Post-fix behavior (`patch.diff`)

```python
if (
    # Primary keys and unique fields are not supported in ALTER TABLE
    # ADD COLUMN.
    field.primary_key or field.unique or
    # Fields with default values cannot by handled by ALTER TABLE ADD
    # COLUMN statement because DROP DEFAULT is not supported in
    # ALTER TABLE.
    not field.null or self.effective_default(field) is not None
):
    self._remake_table(model, create_field=field)
else:
    super().add_field(model, field)
```

The decision gains two leading disjuncts: `field.primary_key or field.unique`.
The table is now reconstructed whenever the column is a primary-key column, a
uniqueness-bearing column, a non-nullable column, OR a column with a stored
default. Only a plain column (none of these) takes the in-place path.

### `ColumnProps` field ↔ Python bijection

| `ColumnProps` field | Python expression | notes |
|---|---|---|
| `isPrimaryKey : Bool` | `field.primary_key` | whether the field is the model's primary key. Default `False`. |
| `isUnique : Bool` | `field.unique` | whether the field carries a uniqueness requirement. `OneToOneField` sets `kwargs['unique'] = True` (`django/db/models/fields/related.py:1088`); default `False` otherwise. |
| `allowsNull : Bool` | `field.null` | whether the column permits null values. Default `False`. |
| `hasStoredDefault : Bool` | `self.effective_default(field) is not None` | whether the field has a stored database default. `effective_default` (`django/db/backends/base/schema.py:332`) returns the prepared default or `None`; this boolean is exactly the `is not None` test. The default's *computation* is unchanged by the patch (identical pre/post), so it is abstracted into a single boolean observation rather than re-modeled. |

### Output bijection (used by G-CONF)

| Lean output | Python meaning |
|---|---|
| `result : Bool` | the truth value of the `if (...)` condition: `True` ⇔ `_remake_table` (reconstruct) branch taken; `False` ⇔ `super().add_field` (plain in-place add) branch taken. |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `(field.primary_key, field.unique, field.null, effective_default(field) is not None)` | `ColumnProps` (4 `Bool` fields) | component-wise boolean identity per the table above. |
| condition truth value | `Bool` | `True ↔ true` (reconstruct), `False ↔ false` (in-place add). |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The decision the patch changes is modeled DEEPLY
  as the explicit boolean disjunction over the four column properties
  (SPEC_GUIDE §3: a deeply-modeled changed decision is never axiomatized). There
  is no opaque callee whose contract the proof consumes (`axiom_check.py` is a
  skip stub; G-AX skips).
- **`effective_default`** is an unchanged callee; its result enters the decision
  only via the boolean `effective_default(field) is not None`, which is the
  `hasStoredDefault` input. Its computation is byte-identical pre- and post-patch
  and is NOT the modeled decision, so it is abstracted into the input rather than
  carried as an opaque callee or axiom.
- **Flag dependency (`OneToOneField`).** The F2P discriminator is a *nullable*
  one-to-one column. `OneToOneField.__init__` forces `unique = True` while the
  test passes `null=True`; thus `isUnique = true`, `allowsNull = true`,
  `isPrimaryKey = false`, `hasStoredDefault = false`. Pre-patch this column is
  `false` (in-place add, which fails); post-patch it is `true` (reconstruct).
  This is the discriminating clause for G-DIFF.

## G-CONF fuzz seed

Pinned LCG seed: **15278** (see `conformance_check.py` `SEED`). Corpus: the 16
exhaustive 4-bit assignments of `(isPrimaryKey, isUnique, allowsNull,
hasStoredDefault)` plus ≥1e5 fuzzed boolean 4-tuples, diffed against an
in-process replica of the post-patch decision
(`primary_key or unique or (not null) or has_default`).
