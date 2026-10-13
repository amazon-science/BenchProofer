# mapping.md — django__django-15957

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f387d024fc75569d2a4a338bfda76cc2f328f627`, states the type
abstraction (the bijection a differential gate would use to bridge Lean↔Python),
and records the (none) axiom provenance and the conf-skip rationale.

Repo file under change: `django/db/models/fields/related_descriptors.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `perGroupSlice (groups) (low) (high)` | the new helper `_filter_prefetch_queryset(queryset, field_name, instances)` introduced by the patch (added after `related_descriptors.py:83`), in its sliced branch | the modeled changed function: the net row-set the prefetch queryset returns when it is sliced |
| `pySlice (low) (high) (g : List Int)` | the window-bounded keep predicate `low_mark < RowNumber() <= high_mark` evaluated **within one partition** (`partition_by=field_name`) over the partition's ordered rows | pure spec: the slice `g[low:high]` of one ordered group |
| `slicedGroups (low) (high) (gs)` | the union, over all partitions, of each partition's window-bounded rows (the rows the patched queryset yields), grouped downstream per instance | pure spec: concatenation of every group's own slice |

The two **call sites** that delegate to the new helper (both unchanged in
essence — they merely replace the old global `queryset.filter(**query)` with the
helper call):

* `RelatedManager.get_prefetch_queryset` — FK reverse side,
  `related_descriptors.py:721-722` @ base_commit
  (`query = {"%s__in" % self.field.name: instances}; queryset = queryset.filter(**query)`).
* `ManyRelatedManager.get_prefetch_queryset` — M2M side,
  `related_descriptors.py:1054-1055` @ base_commit
  (`query = {"%s__in" % self.query_field_name: instances};
  queryset = queryset._next_is_sticky().filter(**query)`).

Both F2P behaviours (FK-reverse, M2M forward/reverse, reverse-ordering) are the
SAME modeled net effect — per-group slicing — so a single modeled function and a
single failing prepatch cover all four F2P tests.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| the related-object rows the prefetch queryset would return, **grouped by the relation field** (`partition_by=field_name`) and **ordered within each group** by the queryset's resolved `get_order_by()` | `groups : List (List Int)` | each inner `List Int` is one instance's ordered related rows (modeled by their integer order-key / id); group order and intra-group order are taken as already-resolved inputs (the ordering machinery — `get_compiler(...).get_order_by()` — is UNCHANGED and shared by both branches, so it is an abstracted input, tagged R, not an axiom). `len(group)` ↔ `g.length`. |
| `queryset.query.low_mark` (slice start; default `0`) | `low : Nat` | identity on non-negative ints; Django slice marks are always ≥ 0. |
| `queryset.query.high_mark` (slice stop; `None` ⇒ open-ended) | `high : Option Nat` | `None` ↔ `none`; an integer stop `h` ↔ `some h`. Django guarantees `low_mark ≤ high_mark` when both are set. |
| one related row (its position-determining order key) | `Int` | the row's identity under the resolved ordering; equality/order on `Int` mirrors row identity. Only membership, per-group position, and group boundaries are observable to the F2P assertions (`book.authors_sliced == list(book.authors.all())[1:]`), all preserved by this carrier. |
| `RowNumber() OVER (PARTITION BY field ORDER BY order_by)` filtered to `low_mark < rn ≤ high_mark`, then `clear_limits()` | `pySlice low high g` = `g[low:high]` | 1-based `rn`: keep positions with `rn > low ∧ (high = none ∨ rn ≤ high)` ⇔ 0-based positions `j ∈ [low, high)` ⇔ Python `g[low:high]` ⇔ `(g.drop low).take (high − low)` (or `g.drop low` when `high = none`). |
| `queryset.filter(predicate)` returning the union over partitions | `slicedGroups low high groups` | flat concatenation, in group order, of each `pySlice low high g`. The downstream regrouping per instance (`rel_obj_attr`) is unchanged and observes the same multiset of rows. |

Lean `List` indexing/`take`/`drop` are total and sound; the carrier is
`List (List Int)` because the operation is "per independent ordered group, take
that group's own slice."

## 3. Callee provenance

**No consumed axioms and no deep-model A-reference of an outside callee.** The
operation the patch changes — converting a single global slice of all related
rows into an independent slice *per group* — is modeled **directly** by
`pySlice`/`slicedGroups` (pure `take`/`drop`/`++`), the I-tagged concrete ops of
refinement.md. The SQL primitives the patch composes (`Window`, `RowNumber`,
`GreaterThan`, `LessThanOrEqual`, `clear_limits`) are the *mechanism* that
realises this net effect on the backend; their semantic effect is captured by
the deep model, and the ground-truth oracle for that equivalence is the official
harness (G-RESOLVE) plus the adversarial narrative audit (G-EQ). The ordering
machinery (`get_compiler(...).get_order_by()`) is UNCHANGED and shared by both
the buggy and fixed branches, so the resolved ordering enters the model as an
abstracted input (the already-ordered `groups`), tagged **R**, requiring no
axiom (LESSONS: abstracted-input-not-axiom).

Hence `axiom_check.py` is a `status=skip` stub (no axioms / no A-reference to
execute), mirroring the no-axiom bundles (django-12273 family).

## 4. G-CONF: conf_skip = true (DB-effect oracle)

`meta.json conf_skip = true`; `conformance_check.py` is a `status=skip` stub.

The impl region's R/I content (`pySlice`/`slicedGroups`) is a pure, input-
dependent computation, but the **oracle** it must be diffed against —
`patch.diff`'s behaviour — is only observable by running the patched
`_filter_prefetch_queryset` through the real ORM: it builds a `Window(RowNumber(),
partition_by=…, order_by=…)` annotation and emits a SQL window query whose result
is materialised only against a live, window-function-capable backend, inside the
full `prefetch_related` machinery. There is no DB-free way to compute "what rows
the patched queryset returns" without standing up Django models + a DB + the
prefetch pipeline — i.e. re-running the F2P integration tests
(`PrefetchLimitTests.test_{foreignkey_reverse,m2m_forward,m2m_reverse,
reverse_ordering}`). Per SPEC_GUIDE §0 / LESSONS (conf_skip for DB-effect
bundles; cf. django-11179, django-13089), the soundness of the modeled net
effect is carried by **G-VERIFY** (the spec provably forces
`out = slicedGroups low high groups`), **G-DIFF** (the global-slice prepatch
fails exactly that clause), **G-RESOLVE** (the real patch resolves), and
**G-EQ / G-PANEL** (the SQL-window ↔ per-group-slice correspondence narrative).
Pinned fuzz seed (for the prepatch/G-MUT determinism record): **`15957`**.
