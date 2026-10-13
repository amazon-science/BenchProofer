# mapping.md — django__django-15561

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6991880109e35c879b71b7d9d9c154baeec12b89`, states the type
abstraction, and gives the provenance of each modelled operation.

Repo files under change:
* `django/db/models/fields/__init__.py` — the `Field` class (adds the
  `non_db_attrs` class attribute).
* `django/db/backends/base/schema.py` — `BaseDatabaseSchemaEditor.
  _field_should_be_altered` (reads `field.non_db_attrs` instead of a local list).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `schema_irrelevant_attrs()` | `Field.non_db_attrs` class attribute — `django/db/models/fields/__init__.py:140` (added by the patch, just after `system_check_removed_details`) | the first modelled changed site: the set of attribute names that do NOT affect a column definition |
| `field_alteration_needed(...)` | `BaseDatabaseSchemaEditor._field_should_be_altered(old_field, new_field)` — `django/db/backends/base/schema.py:1372` (body 1373-1398) | the second modelled changed site: the rebuild decision |
| `disagrees_relevant(...)` | the residual-tuple inequality `(old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)` after `kwargs.pop(attr, None)` over `non_db_attrs` (`schema.py:1397-1398`) | pure spec: the two attribute bags disagree on some schema-RELEVANT attribute |
| `attr_choices()` | the string `"choices"` (the attribute the patch ADDS to the set) | pure spec: the enumeration-of-permitted-values attribute code |
| `attr_blank()` … `attr_verbose_name()` (11 codes) | the strings `"blank" "db_column" "editable" "error_messages" "help_text" "limit_choices_to" "on_delete" "related_name" "related_query_name" "validators" "verbose_name"` (the legacy `non_database_attrs` list) | pure spec: the eleven legacy schema-irrelevant attribute codes |
| `non_db` parameter of `field_alteration_needed` | the value of `field.non_db_attrs` consumed inside `_field_should_be_altered` (the result of `schema_irrelevant_attrs()`) | the schema-irrelevant set, passed in (the gold reads `old_field.non_db_attrs` / `new_field.non_db_attrs`) |
| `other_differs` parameter | `quote_name(old.column) != quote_name(new.column)` OR `(old_path,old_args) != (new_path,new_args)` (the NON-kwarg structural comparison, `schema.py:1396-1398`) | a read-only bool summarising the non-attribute part of the comparison |

The pre-patch repo symbol the change supersedes (for the refinement audit, not
referenced from the consumer spec view): the local list `non_database_attrs`
inside `_field_should_be_altered` (`schema.py:1379-1392` @ base_commit), which
listed the eleven legacy attributes but **omitted `choices`**.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an attribute NAME (`str`, e.g. `"choices"`, `"blank"`) | an `int` attribute code (`attr_choices()` … `attr_verbose_name()`) | a fixed injection: distinct attribute names ↔ distinct codes (`str` indexing is banned in Nagini; only equality/membership of attribute names is observed, faithfully an int-equality carrier) |
| `field.non_db_attrs` (a `tuple` of attribute names) | `PSet[int]` of attribute codes | `attr in tuple` ↔ `code in set`; the gold only ever tests membership while popping kwargs, so a set is the faithful carrier |
| `old_kwargs` / `new_kwargs` (a `dict` from attribute name to a deconstructed value) | aligned `PSeq[int]`: `attrs[i]` = the i-th attribute code present in either bag, `old_vals[i]`/`new_vals[i]` = a value token (a distinct ABSENCE token if the key is absent on that side) | `k in old_kwargs and old_kwargs[k]==new_kwargs[k]` ↔ `old_vals[i]==new_vals[i]` at the position with `attrs[i]==code(k)`; "key present on one side only" ↔ "ABSENCE token ≠ present token" (so membership-disagreement and value-disagreement are one elementwise test). Object/value identity carried by int equality. |
| the residual-tuple inequality after stripping `non_db_attrs` | `disagrees_relevant`: ∃ a listed attribute OUTSIDE `non_db` whose value tokens differ | popping a key `k ∈ non_db` from both kwargs makes it irrelevant to the residual comparison ↔ excluding `attrs[i] ∈ non_db` from the existential |
| `quote_name(old.column) != quote_name(new.column)` and `(old_path,old_args)!=(new_path,new_args)` | the read-only bool `other_differs` | `quote_name` is injective (it only quotes), so column inequality is preserved; the path/args part is a tuple inequality. All of it is the non-kwarg structural comparison, summarised by one bool (its internal structure is not what the fix changes). |
| the disjunction `column_differs OR residual_kwargs_differ` (the gold's `return`) | `other_differs or disagrees_relevant(...)` | Python `or` ↔ logical `or`; the bool result is the rebuild decision (`True` = alter/rebuild needed) |

`str` indexing/iteration is banned in Nagini, so attribute names are carried by
`int` codes and the kwargs bags by `PSeq[int]`; membership by `PSet[int]`.

## 3. Operation provenance (kind A-reference — checked by G-AX / axiom_check.py)

There is **no `@ContractOnly` axiom** in this bundle: every operation the gold
composes is a real Python language primitive (`dict.pop`, tuple `!=`, tuple
membership), so the changed behaviour is modelled DEEPLY and validated against
those primitives out-of-band rather than consumed as an axiom.

### 3.1 `schema_irrelevant_attrs` deep model ↔ `Field.non_db_attrs` (A-reference)
**Real value (gold, `django/db/models/fields/__init__.py:140`):**
```python
non_db_attrs = (
    "blank", "choices", "db_column", "editable", "error_messages",
    "help_text", "limit_choices_to",
    "on_delete", "related_name", "related_query_name",
    "validators", "verbose_name",
)
```
This is the eleven legacy `non_database_attrs` PLUS `choices` — twelve entries.
The model's `schema_irrelevant_attrs()` builds the `PSet` of the 12
corresponding codes and its postcondition pins the result EXACTLY (set
equality with the 12-code literal `PSet`, plus a redundant membership clause
for the enumeration attribute). Equality is load-bearing in both directions: a
set missing `choices` reproduces the bug, and a set with any EXTRA member
would mark a schema-RELEVANT attribute (e.g. `max_length`) as irrelevant and
silently suppress required rebuilds — such an implementation must not verify.
`axiom_check.py` asserts the model code set == the code set of the gold tuple
(and that the enumeration attribute `choices` is a member). The pre-patch had
no class attribute; the local `non_database_attrs` list omitted `choices` —
the single behavioural delta.

### 3.2 `field_alteration_needed` deep model ↔ `_field_should_be_altered` (A-reference)
**Real body (gold, `django/db/backends/base/schema.py:1373-1398`):**
```python
_, old_path, old_args, old_kwargs = old_field.deconstruct()
_, new_path, new_args, new_kwargs = new_field.deconstruct()
for attr in old_field.non_db_attrs:
    old_kwargs.pop(attr, None)
for attr in new_field.non_db_attrs:
    new_kwargs.pop(attr, None)
return self.quote_name(old_field.column) != self.quote_name(new_field.column) or (
    old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)
```
After popping every `non_db_attrs` key from both kwargs dicts, the residual
tuples are compared. The residual comparison differs iff some key NOT in
`non_db_attrs` is present-on-one-side-only or present-on-both-with-differing-
values — exactly `disagrees_relevant`. Combined with `other_differs` (column +
path/args), this is `field_alteration_needed`. `axiom_check.py` reconstructs the
gold body over real Python `dict`s (the exact `.pop`/tuple-`!=` primitives) and
asserts `model_decision == gold_should_be_altered` on 9 boundary + 20 000 fuzz
field pairs, including the F2P choices-only no-op in both directions and a
schema-relevant rebuild.

**Soundness check (G-AX):** `axiom_check.py` imports only the Python standard
library (`dict`/`tuple` are the primitives the gold composes). Exit 0 iff the
deep models equal the real gold operations on every observation.
`deconstruct`'s `choices` handling (it unrolls any iterable into a concrete list
and uses `!=` comparison — `django/db/models/fields/__init__.py:534,546`) means a
choices difference IS a kwargs difference pre-strip, so stripping `choices` is
necessary and sufficient to make the choices-only change a no-op.
