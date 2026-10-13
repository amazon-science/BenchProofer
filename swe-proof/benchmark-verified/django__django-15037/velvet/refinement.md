# refinement.md — django__django-15037

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`qualifyReference` `do` block and the pure `targetQualifier` decision) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized/free callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a free input is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The reference-qualifier decision — `inspectdb.py:118-128`

Gold hunk (the relation branch):
```
  if is_relation:
+     ref_db_column, ref_db_table = relations[column_name]
      if extra_params.pop('unique', False) or extra_params.get('primary_key'):
          rel_type = 'OneToOneField'
      else:
          rel_type = 'ForeignKey'
+         ref_pk_column = connection.introspection.get_primary_key_column(cursor, ref_db_table)
+         if ref_pk_column and ref_pk_column != ref_db_column:
+             extra_params['to_field'] = ref_db_column
      rel_to = (
-         "self" if relations[column_name][1] == table_name
-         else table2model(relations[column_name][1])
+         'self' if ref_db_table == table_name
+         else table2model(ref_db_table)
      )
```

| # | Solution.lean impl op (`qualifyReference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `isUniqueRef : Bool` | `rel_type` decision `pop('unique') or get('primary_key')` (`:119`) | R | `True`→`OneToOneField`, `False`→`ForeignKey` ↔ `isUniqueRef` (mapping.md §1/§2). The qualifier is attached only on the `ForeignKey` branch, modeled by the `if isUniqueRef then none` guard. |
| A2 | param `refColumn : List Char` | `ref_db_column = relations[column_name][0]` (`:119` post-patch unpack) | R | the referenced column name; `str` ↔ `List Char` (mapping.md §2). |
| A3 | param `idKey : Option (List Char)` | `ref_pk_column = connection.introspection.get_primary_key_column(cursor, ref_db_table)` (`:123` post-patch) | A-reference | the referenced table's PK column, or `None`. UNCHANGED callee, newly consulted; taken as a free input, validated == real callee by G-AX (mapping.md §3.1). NOT a consumed axiom — the proof needs no contract about how the callee computes, only the value it yields. |
| A4 | `if isUniqueRef then return none` | qualifier never assigned on the `OneToOneField` branch (`:120`) | I | a one-to-one reference carries no `to_field`. Concrete branch, transliterated by G-CONF. |
| A5 | `match idKey with \| none => return none` | `if ref_pk_column and …` — `None`/falsy `ref_pk_column` ⇒ the `to_field` assignment is skipped (`:124`) | R + I | absence (`None`/`""`) ↔ `none`/empty guard; the truthiness test ↔ `none`-match + `k ≠ []`. |
| A6 | `if k ≠ [] ∧ k ≠ refColumn then return (some refColumn) else return none` | `if ref_pk_column and ref_pk_column != ref_db_column: extra_params['to_field'] = ref_db_column` (`:124-125`) | I | the discriminating decision: attach the qualifier (value = the referenced column) exactly when the PK column is present and differs from the referenced column. Concrete equality + conjunction, transliterated by G-CONF. |
| A7 | result `out : Option (List Char)` | `extra_params` gains / lacks the `'to_field'` key (`:125`) | R | qualifier present `some c` ↔ `to_field` set to `c`; `none` ↔ key absent (mapping.md §2). |

Discriminating content of the change — a plain FK to a **non-PK** column must
emit `to_field = <that column>` — lives in
`k ≠ [] ∧ k ≠ refColumn ⇒ some refColumn` (A6). The pre-patch code never
consults the PK column and never sets `to_field`; `Solution_prepatch.lean`
reproduces that (always `none`) and **fails** `out = targetQualifier …` exactly
on the `isUniqueRef = false`, present-distinct-`idKey` branch (G-DIFF). This is
the behaviour the F2P `test_foreign_key_to_field` observes (it asserts the
generated `ForeignKey(..., to_field='people_unique_id')`).

## B. The `rel_to` variable extraction — not modeled (tag I, no observable)

The gold hunk also rewrites `relations[column_name][1]` to the locally-unpacked
`ref_db_table` in the `rel_to` computation. This is a pure
**behaviour-preserving local-variable rename** (`ref_db_table` *is*
`relations[column_name][1]`): same value, same `'self' if … else table2model(…)`
result. It produces no observable difference, adds no spec obligation, and is
tagged **I** with no modeled op. No separate prepatch is warranted — there is no
independently-observable fixed behaviour here.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the decision to attach an explicit target-column qualifier — is modeled
**deeply** as `targetQualifier` (a spelled-out structural function of the three
inputs), not hidden behind an axiom about the function under change. The only
A-tagged element, `idKey`, is the value of an **unchanged** introspection callee
(`get_primary_key_column`), taken as a free input and validated by G-AX — an
A-reference, not a consumed contract. No consumed axiom exists in this bundle.

## D. verify(Solution) ⇒ resolved

`qualifyReference` verifies only if its output equals `targetQualifier` (A4–A7):
the qualifier is `some refColumn` precisely on a plain link whose target PK
column is present and distinct from the referenced column, and `none` otherwise.
By R (`str ↔ List Char`, `None ↔ none`, `rel_type ↔ Bool`, `to_field`-set ↔
`some`) the verified decision equals the gold patch's `to_field` assignment on
the modeled inputs; by G-AX the free input `idKey` equals the real
`get_primary_key_column` and the re-derived gold decision equals
`targetQualifier`; by G-CONF the R/I transliteration of the decision agrees with
the gold patch's literal decision expression on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and an audited callee — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: callee-reference soundness (G-AX)
and refinement fidelity (this doc, G-EQ + G-CONF).
