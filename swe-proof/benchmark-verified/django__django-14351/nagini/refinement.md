# refinement.md — django__django-14351

The operation-by-operation correspondence between `model.py`'s implementation
(the `membership_group_by_cols` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change — `In.get_group_by_cols` (`django/db/models/lookups.py`)

Gold hunk (a NEW override added to the `In` lookup, which previously inherited
the un-normalising base `Lookup.get_group_by_cols`):
```python
+    def get_group_by_cols(self, alias=None):
+        cols = self.lhs.get_group_by_cols()
+        if hasattr(self.rhs, 'get_group_by_cols'):
+            if not getattr(self.rhs, 'has_select_fields', True):
+                self.rhs.clear_select_clause()
+                self.rhs.add_fields(['pk'])
+            cols.extend(self.rhs.get_group_by_cols())
+        return cols
```

| # | model.py impl op (`membership_group_by_cols`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `cols = list(lhs_cols)` | `cols = self.lhs.get_group_by_cols()` | R | the lhs grouping columns; `List[int]` of opaque column ids ↔ list of `Col` (mapping.md §2). `list(lhs_cols)` is the mutable copy the patch then `.extend`s; faithful since `self.lhs.get_group_by_cols()` returns a fresh list. |
| 2 | `if rhs_is_query:` | `if hasattr(self.rhs, 'get_group_by_cols'):` | R | the rhs-is-column-bearing branch guard; the boolean `rhs_is_query` ↔ the `hasattr` test (mapping.md §1). |
| 3 | `if not rhs.has_fields:` | `if not getattr(self.rhs, 'has_select_fields', True):` | R | `rhs.has_fields` ↔ `self.rhs.has_select_fields` (`query.py:244`); the rhs is a `Query`, which always has the property, so the `getattr` default is dead (mapping.md §2). |
| 4 | `clear_output_columns(rhs)` | `self.rhs.clear_select_clause()` | A-consumed | unchanged primitive; axiom ensures `¬has_fields` and preserves pk/default facets (mapping.md §3.2). |
| 5 | `add_identity_column(rhs)` | `self.rhs.add_fields(['pk'])` | A-consumed | unchanged primitive; axiom ensures `has_fields` AND `explicit_cols == PSeq(pk_col)` afterwards (mapping.md §3.3). After steps 4+5 the query carries explicit output columns = exactly its identity column. |
| 6 | `rhs_cols = nested_group_by_cols(rhs)` | `self.rhs.get_group_by_cols()` (inside `.extend`) | A-consumed | the unchanged grouping-column reader; axiom ties the result to the query's columns: `has_fields ⇒ Result() == explicit_cols` (mapping.md §3.1). Post-normalisation `has_fields` holds AND `explicit_cols == PSeq(pk_col)` ⇒ reader yields `PSeq(pk_col)` (one column). An already-explicit rhs (steps 4+5 skipped) yields its own `explicit_cols` unchanged. |
| 7 | the `while` loop appending each `rhs_cols[i]` to `cols` | `cols.extend(self.rhs.get_group_by_cols())` | R + I | element-wise append is the faithful skeleton of `.extend`; the loop invariant proves `cols == lhs_cols ++ rhs_cols`. |
| 8 | `return cols` | `return cols` | I | identical. |

## The discriminating behaviour (what the spec senses)

The fix is the insertion of steps 4+5 (the field-less normalisation) **before**
step 6. Pin: when the rhs is a column-bearing query with **no** explicit output
columns, its grouping-column reader returns the full `default_cols` (possibly
several columns). The fix first normalises it (clear + add `pk`) so the reader
returns exactly the one identity column. The discriminating postcondition
```
rhs_is_query ∧ ¬Old(rhs.has_fields) ⇒ ToSeq(Result()) == ToSeq(lhs_cols) + PSeq(rhs.pk_col)
```
holds for the patched skeleton (exactly one rhs column appended) and **fails**
for `model_prepatch.py` (which omits steps 4+5 and appends the full
`default_cols`) — that is the spec sensing the bug (G-DIFF).

**Produced-by grounding on the field-less branch (SPEC_GUIDE directive 8 — anti
echo/fabrication).** The constant clause above (`== lhs_cols + PSeq(pk_col)`) is
necessary but not sufficient: an impl could *fabricate* `PSeq(pk_col)` and append
it without ever calling steps 4+5+6 (an "echo" of the constant), leaving the rhs
un-normalised. Such an impl is NOT the gold mechanism (gold mutates `self.rhs` so
the subquery expression renders one column; a fabricated bare pk col does not
refine to that). Two additional postconditions on this branch close the hole:
```
rhs_is_query ∧ ¬Old(rhs.has_fields) ⇒ rhs.has_fields ∧ rhs.explicit_cols == PSeq(rhs.pk_col)   (post-state)
rhs_is_query ∧ ¬Old(rhs.has_fields) ⇒ ToSeq(Result()) == ToSeq(lhs_cols) + nested_group_by_cols(rhs)   (produced-by)
```
The post-state clause forces the rhs to be left in the normalised state (steps
4+5 must have run — step 5 = `add_identity_column` is the only producer of
`rhs.explicit_cols == PSeq(pk_col)`); the produced-by clause forces `Result()` to
be the **reader's output on that post-state** (step 6), not a constant. The echo
impl FAILS the post-state clause (it never mutates `rhs`). Crucially the
post-state clause is the load-bearing anti-prepatch part: a produced-by clause
using only `nested_group_by_cols(rhs)` WITHOUT the post-state would re-admit the
prepatch (which reads the same reader on an un-normalised rhs); pairing it with
`rhs.has_fields ∧ explicit_cols==PSeq(pk_col)` is what keeps G-DIFF.

**Frame clause on the untouched branches (anti gratuitous-mutation).** The three
value clauses above pin the RETURNED list, and the produced-by pair pins the rhs
post-state on the field-less branch — but they said nothing about the rhs
post-state OFF that branch. That admitted a same-spec rival that computes the
correct result and then gratuitously normalises an already-explicit rhs (or a
literal-branch rhs) before returning: every value clause still holds (P2 uses
`Old(rhs.explicit_cols)`), yet the impl is NOT the gold mechanism — gold mutates
`self.rhs` only inside the `if not has_select_fields:` guard, and rewriting a
`values('name')` subquery's SELECT to `pk` changes the emitted SQL for every
explicit-fields IN lookup (regresses P2P semantics; a G-PANEL-1 audit built
exactly this rival and it verified). The frame pair closes the hole:
```
¬(rhs_is_query ∧ ¬Old(rhs.has_fields)) ⇒ rhs.has_fields == Old(rhs.has_fields)
¬(rhs_is_query ∧ ¬Old(rhs.has_fields)) ⇒ rhs.explicit_cols == Old(rhs.explicit_cols)
```
i.e. the field-less normalisation is the ONLY branch on which the nested query's
select facets change — exactly the gold write-footprint (`pk_col`/`default_cols`
are already frozen by the earlier preservation clauses and by Acc(...,1/2)).
Gold trivially satisfies it (its only rhs writes are steps 4+5 under the guard);
the gratuitous-mutation rivals now fail this clause (properties.py cases
`gratuitous-normalise-explicit-after-result`, `gratuitous-normalise-literal-rhs`).

The two non-bug
postconditions are preserved by both prepatch and patch, so the witness isolates
exactly the fixed behaviour:
  - `¬rhs_is_query ⇒ result == lhs_cols`;
  - the **explicit-fields** postcondition is GROUNDED in the query's own column
    carrier (SPEC_GUIDE directive 8), not pinned to a pk sentinel:
    ```
    rhs_is_query ∧ Old(rhs.has_fields) ⇒ ToSeq(Result()) == ToSeq(lhs_cols) + Old(rhs.explicit_cols)
    ```
    An already-explicit rhs is left untouched and contributes exactly its own
    chosen columns (`values('name')` → `[name]`, `values('id','name')` → two
    columns) — NOT forced to the pk. This grounding makes the spec REJECT an
    impl that normalises unconditionally (which would force every explicit rhs
    to the pk): such an impl produces `lhs_cols + PSeq(pk_col)`, violating this
    postcondition when `Old(rhs.explicit_cols) ≠ PSeq(pk_col)` — verified by
    construction (the unconditional-normalise attacker fails to verify on this
    postcondition). The earlier revision pinned this branch to `PSeq(rhs.pk_col)`,
    which was an ungrounded over-claim (false of the gold callee for non-pk
    explicit shapes); the fix replaces it with the grounded `Old(rhs.explicit_cols)`.

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A-consumed, or I. The operation that *changed* — adding the
field-less normalisation before reading the rhs's grouping columns — is modeled
**directly in the impl** (the `if not rhs.has_fields: clear_output_columns;
add_identity_column` block, steps 4+5), using **A-consumed** axioms for the
three unchanged callees (`get_group_by_cols`, `clear_select_clause`,
`add_fields`). No callee under change is axiomatized: the changed function
itself (`In.get_group_by_cols`) is the contracted `membership_group_by_cols`,
spelled out. There are no A-reference deep models (no changed string/float
operation to validate out-of-band); the three axioms are all A-consumed and
audited against the real callees by G-AX.

## verify(model) ⇒ resolved

`membership_group_by_cols` verifies only if, for a field-less rhs query, the
appended grouping columns are exactly the single identity column (the
discriminating postcondition), which forces steps 4+5 (the normalisation) to be
present and to run before the reader. By R (column list ↔ `List[int]`, `hasattr`
↔ `rhs_is_query`, `has_select_fields` ↔ `has_fields`) and A-consumed (the three
unchanged callees, audited == real by G-AX), the verified skeleton equals the
gold `In.get_group_by_cols` on the tested path; the gold patch resolves
(G-RESOLVE). The trust points are the two of PLAN §1.1: axiom soundness (G-AX,
§3) and refinement fidelity (this document, G-EQ).
