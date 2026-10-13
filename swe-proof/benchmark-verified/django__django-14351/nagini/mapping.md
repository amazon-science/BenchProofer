# mapping.md — django__django-14351

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 06fd4df41afb5aa1d681b853c3c08d8c688ca3a5`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/models/lookups.py` (the `In` lookup, which
inherits `get_group_by_cols` from the base `Lookup`). The new override is added
right after `In.process_rhs` (lines 406–408 already perform the *same*
clear-then-add-`pk` normalisation in the rhs-rendering path; the fix mirrors it
in the grouping-columns path).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `membership_group_by_cols(lhs_cols, rhs_is_query, rhs)` | `In.get_group_by_cols(self, alias=None)` — added to `In` (`django/db/models/lookups.py:376` class; method inserted after line 408) | the modeled changed function: the grouping-columns reader for the `IN` lookup |
| `lhs_cols` (param) | `self.lhs.get_group_by_cols()` — `django/db/models/lookups.py` (base `Lookup.get_group_by_cols`, line 117) returns the lhs grouping columns | the left operand's grouping columns (read-only) |
| `rhs_is_query` (param) | `hasattr(self.rhs, 'get_group_by_cols')` — True iff the rhs is a column-bearing expression/query rather than a literal collection | branch guard |
| `rhs: NestedQuery` | `self.rhs` when it is a `Query`/expression (e.g. the subquery from `Q(field__in=queryset)`) | the nested query whose grouping columns are appended |
| `rhs.has_fields` | `self.rhs.has_select_fields` — `django/db/models/sql/query.py:244` (`bool(self.select or self.annotation_select_mask or self.extra_select_mask)`) | whether the nested query carries explicit output columns |
| `rhs.explicit_cols` | the columns the query's grouping-column reader returns WHEN it carries explicit output columns (`self.rhs.select`-derived; for `values('name')` this is `[name]`, for `values('id','name')` two columns) | the query's own chosen output columns — whatever they are, NOT forced to the pk |
| `nested_group_by_cols(q)` *(axiom — A-consumed)* | `self.rhs.get_group_by_cols()` — for a `Query` rhs this is `BaseExpression.get_group_by_cols` (`django/db/models/expressions.py:348`) / the compiler's column resolution; UNCHANGED by the patch | the nested query's grouping-column reader |
| `clear_output_columns(q)` *(axiom — A-consumed)* | `self.rhs.clear_select_clause()` — `django/db/models/sql/query.py:1861` | unchanged primitive: removes all SELECT-clause fields |
| `add_identity_column(q)` *(axiom — A-consumed)* | `self.rhs.add_fields(['pk'])` — `django/db/models/sql/query.py:1893` | unchanged primitive: sets the SELECT list to exactly `['pk']` |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): `In` had **no** `get_group_by_cols`
override and inherited `Lookup.get_group_by_cols` (`lookups.py:117`):
```python
def get_group_by_cols(self, alias=None):
    cols = self.lhs.get_group_by_cols()
    if hasattr(self.rhs, 'get_group_by_cols'):
        cols.extend(self.rhs.get_group_by_cols())   # NO normalisation
    return cols
```
A field-less subquery rhs therefore contributed its full default column set to
the GROUP BY, producing `... GROUP BY ..., (SELECT U0."id", U0."created", ...)`
— Postgres' "subquery must return only one column".

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a list of grouping-`Col` objects | `List[int]` of opaque column identifiers | each `Col` ↔ one `int`; list order, length, `.extend(...)` and `list(...)` copy mirror exactly; only identity/equality of columns is observed by the test (column count + which column) |
| `self.lhs.get_group_by_cols()` (a freshly-built list) | the read-only `List[int]` parameter `lhs_cols` | the lhs columns are computed independently of the rhs branch; modeling them as a read-only input is faithful (the fix never mutates them) |
| `self.rhs` (a `Query`) | `NestedQuery(has_fields, default_cols, explicit_cols, pk_col)` | only the touched facets are kept: `has_select_fields`→`has_fields`; the columns its reader returns when field-less→`default_cols` (a `PSeq[int]`); the columns its reader returns when it carries explicit output columns→`explicit_cols` (a `PSeq[int]`); its identity (`pk`) column→`pk_col` |
| `getattr(self.rhs, 'has_select_fields', True)` | `rhs.has_fields` | the rhs here is always a `Query`, which always has the property; the `getattr` default is irrelevant to the tested path |
| `alias=None` keyword arg | omitted | the F2P path calls `get_group_by_cols()` with no alias; modeled as the single contracted behaviour |
| `list.extend(seq)` | the `while` loop appending each element of `rhs_cols` to `cols` | element-wise append is the faithful skeleton of `.extend`; the loop invariant pins `cols == lhs_cols ++ rhs_cols.take(i)` |

`str`/`Col` indexing is irrelevant here; columns are modeled as opaque `int`
identifiers carried by `List[int]` / `PSeq[int]`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `nested_group_by_cols` ↔ `Query.get_group_by_cols` (A-consumed)
**Callee:** the rhs query's `get_group_by_cols()` (`BaseExpression.get_group_by_cols`,
`django/db/models/expressions.py:348`, plus the compiler's column expansion).
UNCHANGED by the patch. The property the proof consumes is parameterised by
whether explicit output columns are present:

  - if the query has explicit output columns, its grouping-column reader yields
    exactly THOSE chosen columns — whatever they are (`values('name')` → the one
    `name` column, NOT the pk; `values('id','name')` → two columns). After the
    fix's normalisation (`clear_select_clause()` + `add_fields(['pk'])`) the
    explicit output columns are exactly `['pk']`, so the reader yields exactly
    one column (the identity column) — but that one-column result is a
    consequence of the normalisation having SET the explicit columns to the pk,
    not a property of `has_fields` alone;
  - if the query has NO explicit output columns, the reader yields its full
    default column set (which, for a model with several fields, is several
    columns — the source of the bug).

The axiom encodes precisely this, FAITHFULLY (no exact-pk-sentinel over-claim):
`has_fields ⇒ Result() == explicit_cols` and `¬has_fields ⇒ Result() ==
default_cols`. This is the weakest contract the proof needs: the proof never
inspects column *values*; what it consumes is that after the normalisation
`add_identity_column` sets `explicit_cols == PSeq(pk_col)` (§3.3), so a
*field-less* rhs collapses to the single pk column, whereas an
*already-explicit* rhs keeps its own columns. (Earlier revision over-claimed
`has_fields ⇒ Result() == PSeq(pk_col)`, which is FALSE of the real callee for
non-pk explicit shapes; the `explicit_cols` facet grounds the result in the
query's own carrier per SPEC_GUIDE directive 8.)

### 3.2 `clear_output_columns` ↔ `Query.clear_select_clause` (A-consumed)
**Callee:** `Query.clear_select_clause` — `django/db/models/sql/query.py:1861`:
```python
def clear_select_clause(self):
    self.select = ()
    self.default_cols = False
    self.select_related = False
    self.set_extra_mask(())
    self.set_annotation_mask(())
```
After it runs, `has_select_fields` (= `bool(self.select or
annotation_select_mask or extra_select_mask)`) is **False** (select emptied,
masks cleared). The axiom ensures `¬has_fields` and that it does not touch the
identity column or the default-column set — faithful: `clear_select_clause`
only manipulates the SELECT/masks, not the model's pk field.

### 3.3 `add_identity_column` ↔ `Query.add_fields(['pk'])` (A-consumed)
**Callee:** `Query.add_fields` — `django/db/models/sql/query.py:1893`. Called as
`self.rhs.add_fields(['pk'])`: it resolves the `pk` field name and calls
`self.set_select(cols)` (`query.py:1884`) with the single resolved column, which
sets `self.select` to a one-element tuple. Afterwards `has_select_fields` is
**True** and the query's explicit output columns are exactly the one identity
column, so its grouping-column reader yields exactly that one column. The axiom
ensures `has_fields` AND `explicit_cols == PSeq(pk_col)` (and preserves
pk/default facets). This `explicit_cols == PSeq(pk_col)` post-state is what the
proof actually consumes: it is the reason a *field-less* rhs collapses to the
single pk column. This mirrors `process_rhs` (`lookups.py:406-408`), which
performs the identical `clear_select_clause()` + `add_fields(['pk'])` pair in
the rhs-rendering path — the fix is the same normalisation in the
grouping-columns path.

**Soundness check (G-AX):** `axiom_check.py` builds an in-process `django.db`
query against a multi-field model, exercises the three callees on
Requires-satisfying states (a field-less subquery; the explicit-fields shapes
`values('pk')`, `values('name')`, `values('id','name')`; boundary single/many
default columns), and asserts:
  - a field-less subquery's `get_group_by_cols()` returns >1 column when the
    model has >1 default column (the pre-patch hazard);
  - after `clear_select_clause()` + `add_fields(['pk'])`, `has_select_fields`
    is True and the reader returns exactly one column (the pk); and
  - an already-explicit query's reader returns exactly its chosen columns —
    `values('name')` → one column that is NOT the pk, `values('id','name')` →
    two columns — which FALSIFIES a too-strong `has_fields ⇒ PSeq(pk_col)`
    reading and confirms the faithful `has_fields ⇒ explicit_cols` axiom,
matching `nested_group_by_cols` / `clear_output_columns` / `add_identity_column`.
Run IN the pinned eval container (RC=0, 55 observations). Exit 0 iff every
observation meets the axioms' Ensures.

## 4. G-CONF (conformance_check.py)

Differential gate: the contract-stripped impl region (shadow, with the three
@ContractOnly callees delegated to the real `Query` primitives per §1) vs the
real patched `In.get_group_by_cols` (oracle), run in-container over >= 1e5
Requires-satisfying inputs (boundary crossings + fuzz). Pinned fuzz seed:
**14351** (the instance number).
