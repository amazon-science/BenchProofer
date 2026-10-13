# refinement.md — django__django-15037

The operation-by-operation correspondence between `model.py`'s implementation
(`relation_field` + the pure helpers `names_equal` / `qualifier_required`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a value/deep
model validated == the real callee by axiom_check.py / G-AX, NOT consumed), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## The changed block — `inspectdb.py:118-130` (the `if is_relation:` body)

Gold hunk (the relevant changed lines):
```
+ ref_db_column, ref_db_table = relations[column_name]
  if extra_params.pop('unique', False) or extra_params.get('primary_key'):
      rel_type = 'OneToOneField'
  else:
      rel_type = 'ForeignKey'
+     ref_pk_column = connection.introspection.get_primary_key_column(cursor, ref_db_table)
+     if ref_pk_column and ref_pk_column != ref_db_column:
+         extra_params['to_field'] = ref_db_column
  rel_to = (
-     "self" if relations[column_name][1] == table_name
-     else table2model(relations[column_name][1])
+     'self' if ref_db_table == table_name
+     else table2model(ref_db_table)
  )
```

| # | model.py impl op (`relation_field`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | params `ref_db_column`, `ref_db_table: List[int]` | `ref_db_column, ref_db_table = relations[column_name]` | R | `relations[column_name]` is the documented 2-tuple `(field_name_other_table, other_table)` (`base/introspection.py:147-152`; sqlite producer line 168 `(other_name, table)`). Element 0 ↔ `ref_db_column`, element 1 ↔ `ref_db_table`; each `str` name ↔ `List[int]` code points (mapping.md §2). |
| 2 | param `unique_or_pk: bool` | `extra_params.pop('unique', False) or extra_params.get('primary_key')` | R | the patch computes one boolean from `extra_params`; the model takes it directly. The dict bookkeeping is upstream of the change and unmodified. |
| 3 | `out.is_one_to_one = unique_or_pk` | `rel_type = 'OneToOneField'` when the boolean holds, else `'ForeignKey'` | R | `is_one_to_one: bool` ↔ the two-valued `rel_type` string (`True`↔`'OneToOneField'`, `False`↔`'ForeignKey'`); mapping.md §2. |
| 4 | param `other_pk_column: Optional[List[int]]` | `ref_pk_column = connection.introspection.get_primary_key_column(cursor, ref_db_table)` | A-reference | `get_primary_key_column` is an **unchanged** callee the patch newly *calls*; its return (the referenced table's PK column name, or `None`) is taken as the introspected input. The proof relies on NO contract about its internals — it is validated == the real base-class algorithm (returns the first PK constraint's first column, else None) by axiom_check.py / G-AX (mapping.md §3.1). Not a consumed axiom. |
| 5 | `qualifier_required(unique_or_pk, referenced_column, other_pk_column)` = `(not unique_or_pk) and other_pk_column is not None and len(other_pk_column) > 0 and ToSeq(other_pk_column) != ToSeq(referenced_column)` | the guard `rel_type == 'ForeignKey'` (the `else`) **and** `if ref_pk_column and ref_pk_column != ref_db_column:` | I + R | `not unique_or_pk` ↔ being in the `else` (`ForeignKey`) branch (I, via step 3's bijection). `other_pk_column is not None and len(other_pk_column) > 0` ↔ the Python truthiness `if ref_pk_column` for a string (None or `''` is falsy) — modelled explicitly because the carrier is `Optional[List[int]]` (R; this is exactly the gap G-AX caught and the model now matches). `ToSeq(other_pk_column) != ToSeq(referenced_column)` ↔ `ref_pk_column != ref_db_column` (R, string `!=` ↔ `PSeq` inequality). |
| 6 | `out.needs_qualifier = True; out.qualifier_column = col_copy` (where `ToSeq(col_copy) == ToSeq(referenced_column)`) | `extra_params['to_field'] = ref_db_column` | R | setting the `to_field` key with value `ref_db_column` ↔ `needs_qualifier == True` with `qualifier_column` equal (code-point-wise) to `ref_db_column`. The up-front element copy (`col_copy`) is a Nagini framing device only — see Note B; it carries `ToSeq(col_copy) == ToSeq(referenced_column)`, i.e. the same value as the shared reference in the patch. |
| 6b | (no assignment: `qualifier_column` keeps the constructor's empty list on the not-required branch) | the `to_field` key is simply **absent** from `extra_params` when the guard does not fire | R | in the repo the absent case has NO qualifier value at all (the key is never set); the model's total-record carrier pins that absence to the canonical empty list via the postcondition `Implies(not needs_qualifier, len(qualifier_column) == 0)`. This closes the representation gap: an impl cannot smuggle an arbitrary value into the absent case (the previously unconstrained don't-care admitted a same-spec impl that wrote `qualifier_column` on the else branch — G-PANEL-1's atk_6). |
| 7 | `out.rel_to_self = names_equal(referenced_table, table_name)` | `'self' if ref_db_table == table_name else table2model(ref_db_table)` | I + R | the self-vs-other decision is the equality `ref_db_table == table_name` (I, via `names_equal` = `ToSeq` equality, R). `table2model(ref_db_table)` is a downstream name transform of the non-self branch, **unchanged** by the patch (the patch only renames `relations[column_name][1]` to the now-unpacked `ref_db_table` — same value), so it is not part of the modeled decision; `rel_to_self` captures the only branch the change can flip. |

## Notes

**Note A — what the change actually is.** Pre-patch, the referenced *column*
(`relations[column_name][0]`) was discarded; the FK always targeted the other
table's implicit primary key. The fix emits `to_field=<referenced column>`
exactly when the relation is a plain ForeignKey whose referenced column is a
non-PK column of the other table. `model_prepatch.py` is the faithful pre-image:
it decides the relation kind and the self/other target but **never** emits the
qualifier (`needs_qualifier` stays `False`). It therefore fails the postcondition
`Result().needs_qualifier == qualifier_required(...)` precisely when
`qualifier_required` is `True` — the FK-to-non-PK-column case the F2P test
`test_foreign_key_to_field` exercises (`to_field='people_unique_id'`). That is
the spec sensing the bug (G-DIFF).

**Note B — the up-front copy is a framing device, not an algorithmic change.**
`relation_field` builds `col_copy` (a verified element-wise copy of
`ref_db_column`, `ToSeq(col_copy) == ToSeq(referenced_column)`) before evaluating
the pure decisions, so that all heap allocation precedes the `@Pure`
`qualifier_required` calls and Nagini can frame them. This is the canonical
"allocate first, decide after" pattern; it does not change behaviour — the value
stored is `ref_db_column`, exactly as the patch's `extra_params['to_field'] =
ref_db_column`.

## No kind-3 (unexpressible-changed-op) steps

Every step is R, I, or A-reference. The one operation that genuinely *changed*
— the FK-to-field decision and the `to_field` emission — is modeled **deeply**
(spelled out in `qualifier_required` + `relation_field`, steps 5-6), not hidden
behind an axiom about the function under change. The only callee involved,
`get_primary_key_column` (step 4), is **unchanged** and appears solely as the
**A-reference** that G-AX validates the introspected input against. There is **no
consumed `@ContractOnly` axiom**.

## verify(model) ⇒ resolved

`relation_field` verifies only if `needs_qualifier` equals `qualifier_required`
(step 5) and, when set, `qualifier_column` equals `ref_db_column` (step 6), and the
relation kind / self-target track `unique_or_pk` / the table-name equality
(steps 3, 7). By R (str ↔ List[int]; the `rel_type`/`rel_to` bijections;
`extra_params` bookkeeping unchanged) the verified decision equals the gold
block's effect on the tested inputs; by G-AX the introspected `ref_pk_column`
matches the real `get_primary_key_column` (A-reference) and the whole decision
matches the real `inspectdb` block over 50 000 fuzz cases. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE). The
trust points are exactly those of PLAN §1.1: callee/A-reference soundness (G-AX)
and refinement fidelity (this document, G-EQ).
