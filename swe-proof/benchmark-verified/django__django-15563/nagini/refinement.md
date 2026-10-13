# refinement.md — django__django-15563

The operation-by-operation correspondence between `model.py`'s implementation
(the `assign_columns` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The column-assignment site — `SQLUpdateCompiler.pre_sql_setup`

Gold hunk (`django/db/models/sql/compiler.py`), the construction of `fields`
and `related_ids_index`:

```
- query.add_fields([query.get_meta().pk.name])
+ meta = query.get_meta()
+ fields = [meta.pk.name]
+ related_ids_index = []
+ for related in self.query.related_updates:
+     if all(path.join_field.primary_key for path in meta.get_path_to_parent(related)):
+         related_ids_index.append((related, 0))
+     else:
+         related_ids_index.append((related, len(fields)))
+         fields.append(related._meta.pk.name)
+ query.add_fields(fields)
```

| # | model.py impl op (`assign_columns`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `chain: List[int]`, indexed `0..len-1` | `for related in self.query.related_updates:` (the ordered ancestor targets) | R | the ordered `related_updates` keys ↔ the index domain `0..len(chain)-1` (mapping.md §2). |
| A2 | `chain[i] == 1` test | `all(path.join_field.primary_key for path in meta.get_path_to_parent(related))` | A-reference | the unchanged Django path-classification predicate; its boolean value is the input flag `chain[i]` (`True↔1`). The model treats it as input and validates it == the real callee by G-AX (mapping.md §3.1). NOT a consumed axiom. |
| A3 | true branch: `result = result + [0]` | `related_ids_index.append((related, 0))` | I | reuse column 0 (the source model's own pk) for a primary-key-chain ancestor. |
| A4 | false branch: `result = result + [width]; width = width + 1` | `related_ids_index.append((related, len(fields))); fields.append(related._meta.pk.name)` | R | a fresh column is appended; its index is the running width of the pre-selection. `width` (1-based, starting at 1 = `len([pk])`) ↔ `len(fields)` (mapping.md §2). Appending `related._meta.pk.name` to `fields` ↔ incrementing `width`; the model does not carry the column *name* (irrelevant to which-column behaviour), only its index. |
| A5 | `result` returned (a `List[int]` of column indices, one per target) | `related_ids_index` (a list of `(related, index)` pairs) + `query.add_fields(fields)` | R | the per-target column index list ↔ the `index` projection of `related_ids_index`; `add_fields(fields)` materialises the columns the indices point into (mapping.md §2). |

The pre-patch repo line `query.add_fields([query.get_meta().pk.name])` selects
ONLY column 0 and never builds `related_ids_index`, so every ancestor is
implicitly assigned column 0. `model_prepatch.py` reproduces this
(`result = result + [0]` for every target) and **fails** the postcondition
`(Result()[k] == 0) == (ToSeq(chain)[k] == 1)` whenever some target is not a
primary-key chain (`chain[k] == 0`) — exactly the spec sensing the bug
(G-DIFF).

**Dense-index pin (A4, load-bearing).** The fresh column appended by the gold
is `related_ids_index.append((related, len(fields)))` immediately before
`fields.append(...)`, so its index is the *running length* of `fields` —
`fields` starts as `[meta.pk.name]` (length 1) and grows by exactly one per
fresh ancestor. Therefore the k-th fresh ancestor's column is exactly
`1 + (number of fresh ancestors strictly before k)` (a contiguous block
`1, 2, …, F`). This is the column the consumer reads as a PHYSICAL OFFSET into
each pre-selection row (`r[index]`), whose width is exactly `1 + F`. A "positive
and strictly increasing" but *sparse* assignment (e.g. columns 2, 4, 6, …)
over-runs the row width and `IndexError`s. The model's postcondition pins this
exact dense index —
`Result()[k] == 1 + (count_fresh(chain) − count_fresh(chain[k:]))` — using the
front-recursive `@Pure count_fresh`. The model impl's `width` (starting at 1,
incremented per fresh target) is the `len(fields)` counterpart under R, and the
loop invariant `count_fresh(chain) == (width−1) + count_fresh(chain[i:])` ties
`width` to that dense running count. (Batch08 verdict D1: the earlier
"positive + strictly increasing" clause admitted a sparse `i+2` impl that
verified yet `IndexError`ed both F2P tests; the dense pin closes that hole and
kills the `width+2` G-MUT survivor.)

## B. The projection + filter sites (delivered by the column assignment)

Gold hunks: in `pre_sql_setup`, `related_ids = collections.defaultdict(list)`
and `related_ids[parent].extend(r[index] for r in rows)` per `(parent, index)`
in `related_ids_index`, then `self.query.related_ids = related_ids`; and in
`UpdateQuery.get_related_updates` (`subqueries.py`), `query.add_filter("pk__in",
self.related_ids[model])` (was `self.related_ids`).

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| P | the column index `Result()[k]` produced by `assign_columns` | `r[index]` projection (`related_ids[parent].extend(r[index] for r in rows)`) and the keyed filter `self.related_ids[model]` | R / I | the only behavioural content of the projection + keyed filter is *which column* each ancestor reads — that column is exactly `Result()[k]`. Reading `r[index]` from each row and keying `related_ids` by ancestor is a type-trivial list-index + dict-key carrier (mapping.md §2); given the correct column index per target (site A), the projected values and the per-ancestor filter are determined. The pre-patch flat `idents`/`self.related_ids` is the degenerate "everyone reads column 0" of the buggy assignment. |

There is no separate failing `model_prepatch` for site B: its content is
entirely "read column `index`", whose only free parameter is the index produced
by site A. The pre-patch's single flat list is observationally "index = 0 for
all", which is exactly the buggy assignment site A's prepatch already exhibits
and the spec already fails on. The dict-keyed `related_ids` and the `r[index]`
projection are carrier mechanics with no behaviour beyond the column choice.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — choosing, per ancestor, which pre-selection column identifies its
rows (and never defaulting non-primary-key-chain ancestors to column 0) — is
modeled **deeply** (the spelled-out loop in `assign_columns`, pinned by the
biconditional postcondition), not hidden behind an axiom about the function
under change. The only callee abstracted, the path-primary-key predicate
(`get_path_to_parent`/`join_field.primary_key`), is **A-reference** (its value
is the input flag, validated == the real callee by G-AX); there is **no
consumed `@ContractOnly` axiom**.

## D. verify(model) ⇒ resolved

`assign_columns` verifies only if, for every target, it assigns column 0 iff
that target's path is a primary-key chain (the biconditional A2/A3/A4) and
otherwise a positive column (site A). By R (ordered `related_updates` ↔ index
domain, `len(fields)` ↔ `width`, column-name carrier dropped) the verified
assignment equals the gold `related_ids_index` construction; by G-AX the real
predicate driving it is faithfully the input flag (A-reference), and the gold
construction is reproduced from it with 0 mismatch on both F2P scenarios. The
projection + keyed filter (site B) then constrain each ancestor by its own
column's values. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited predicate — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: A-reference soundness (G-AX) and refinement fidelity (this document,
G-EQ).
