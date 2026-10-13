# refinement.md — django__django-10554

Operation-by-operation correspondence between `model.py`'s implementation
(`relabel_order_term` + the `first_pos` deep model) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee
— none here), or **I** (identical concrete operation). Claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The two gold hunks

Hunk 1 — `django/db/models/sql/compiler.py`, inside
`SQLCompiler.get_order_by`'s `if self.query.combinator:` block, the
`for … in enumerate(self.select): … else:` clause:

```
                 else:
-                    raise DatabaseError('ORDER BY term does not match any column in the result set.')
+                    if col_alias:
+                        raise DatabaseError('ORDER BY term does not match any column in the result set.')
+                    # Add column used in ORDER BY clause without an alias to
+                    # the selected columns.
+                    self.query.add_select_col(src)
+                    resolved.set_source_expressions([RawSQL('%d' % len(self.query.select), ())])
```

Hunk 2 — `django/db/models/sql/query.py`, the new helper the rewrite calls:

```
+    def add_select_col(self, col):
+        self.select += col,
+        self.values_select += col.output_field.name,
```

## B. Operation map (`relabel_order_term` ↔ the two hunks)

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `cols: List[int]` parameter | `self.select` (tuple of selected-column triples) | R | the result set's selected columns ↔ a list of column identities (mapping.md §2). |
| B2 | `src: int`, `aliased: bool` parameters | `src = resolved.get_source_expressions()[0]`; `col_alias` truthiness on the unmatched entry | R | the ordering term's column identity and the alias discriminator (mapping.md §1, §2). |
| B3 | the back-to-front scan computing `pos` = first matching position via `first_pos` | `for idx,(sel_expr,_,col_alias) in enumerate(self.select): … if src == sel_expr: … break` (the FIRST `idx+1` taken) | R + I | same search for the leftmost column equal to the term; loop direction is a proof convenience, the modelled result (`first_pos`, leftmost) equals the real for/break that takes the first match (mapping.md §1). The `==` is identical. |
| B4 | `if pos != 0: return pos` (MATCH) | `if src == sel_expr: resolved.set_source_expressions([RawSQL('%d' % (idx+1), ())]); break` | R | a match references the FIRST matching 1-based position and leaves `self.select` unchanged; `RawSQL('%d' % (idx+1))` rendering is abstracted to the integer position. |
| B5 | `if aliased: raise OrderTermUnmatched()` (REJECT) | `else: if col_alias: raise DatabaseError(...)` | R | an unmatched aliased term is rejected; the user exception abstracts `DatabaseError` (mapping.md §2). `self.select` is untouched. |
| B6 | `cols.append(src); return len(cols)` (APPEND) | `else: … self.query.add_select_col(src); resolved.set_source_expressions([RawSQL('%d' % len(self.query.select), ())])` | I (+ R on the carrier) | an unmatched plain column is appended to the selected columns and referenced by its NEW position (the new length). `add_select_col` (hunk 2) is `self.select += col,` — a single append at the end — modelled by `cols.append(src)`; the new position `len(self.query.select)` ↔ `len(cols)`. The parallel `values_select += col.output_field.name,` is a bookkeeping append that does not change the ordinal positions and is not observed by the pinned behaviour. |

No step is a *changed operation Nagini cannot express*: every one is R or I.

## C. Why `add_select_col` is modelled (I), not axiomatized (A)

`Query.add_select_col` is **added by this same patch** (hunk 2) and its entire
observable effect is "append the column at the end of `self.select`, so the new
1-based position is the new length." That is exactly `cols.append(src)` /
`len(cols)` under the `self.select` ↔ `cols` refinement, so it is modelled as an
**identical** concrete operation — not an unchanged external callee. There is no
`@ContractOnly` axiom and nothing for G-AX to execute (the `axioms` region is
empty by design; mapping.md §3). The match-search and the reject/append decision
are likewise modelled deeply, so refinement.md has **no A-consumed and no
A-reference rows** — all R/I.

## D. verify(model) ⇒ resolved (the discriminator the spec pins)

The pre-patch code's `else:` branch raised on EVERY unmatched term. The single
behavioural change is: *an unmatched **plain** (un-aliased) column is appended to
the result set and the term is rewritten to its new position, instead of the
whole query being rejected.* The spec pins this with three grounded clauses over
the actual input carrier (directive 8 — structural predicates, no oracle):

- **MATCH** (`Old(first_pos(src,cols)) != 0`): `cols` unchanged and
  `Result() == Old(first_pos(src,cols))` (the leftmost matching position);
- **APPEND** (`Old(first_pos(src,cols)) == 0 and not aliased`):
  `ToSeq(cols) == Old(ToSeq(cols)) + PSeq(src)` (the column is appended) and
  `Result() == Old(len(cols)) + 1` (the new last position);
- **REJECT** (`Old(first_pos(src,cols)) == 0 and aliased`): raises and leaves
  `cols` unchanged.

`model_prepatch.py` is the pre-patch skeleton: its no-match branch raises
UNCONDITIONALLY (no append path). It therefore **fails** verification — on an
unmatched plain column (`Old(first_pos)==0 and not aliased`) it raises instead
of returning the appended position, so the **APPEND** postcondition is
unprovable, and the raise is not sanctioned by the **REJECT** `Exsures` (whose
condition requires `aliased`). That is exactly the spec sensing the bug
(G-DIFF). Conversely, any impl that verifies must append-and-renumber the
unmatched plain column (it cannot raise there, cannot leave `cols` unchanged,
and cannot return a forged position — `Result()` is pinned to `Old(len(cols))+1`
with `cols` provably grown by `src`). It also cannot append-and-return an
unmatched ALIASED term: the `Ensures(not (Old(first_pos(src,cols)) == 0 and
aliased))` forbids any normal return in the reject case, so a verifying impl
MUST raise there (this closes the batch08 re-audit W5 hole, where the REJECT was
pinned only by the `Exsures`, which constrains the state IF the function raises
but never forces the raise — letting a wrong impl append the aliased term and
return a position, which would fail the PASS_TO_PASS test
`test_order_raises_on_non_selected_column`). By the R/I map above that impl
equals the gold patch on the tested inputs, and the gold patch resolves
(G-RESOLVE). There are TWO FAIL_TO_PASS tests, both covered by this single
modeled `get_order_by` rewrite: `test_union_with_values_list_and_order` orders a
union by `pk`/`-pk`/`-name` (plain columns not in the values_list select) and
asserts the rows come back ordered instead of raising `ORDER BY position N is
not in select list` (the APPEND behaviour), and
`test_union_with_values_list_on_annotated_and_unannotated` exercises the same
changed hunk — precisely the match/append/reject discrimination the spec pins.

## E. No kind-3 (unexpressible-changed-op) steps

Every step in §B is R or I. The one operation that genuinely *changed* — taking
the append branch for an unmatched plain column instead of always raising — is a
control-flow choice modelled directly by the `if aliased: raise … else:
append` branch, with the append's effect pinned structurally
(`cols` grows by `src`; new position = new length). No oracle, no axiom.
