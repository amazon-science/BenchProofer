# refinement.md — sphinx-doc__sphinx-10466

The operation-by-operation correspondence between `model.py`'s implementation
(the `canonical_positions` impl region, the helper loop `insert_sorted`, and the
deep pure model `dedup_sort`/`ins`) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The position-list site — `Catalog.__iter__` (`sphinx/builders/gettext.py:58-62`)

Gold hunk:
```
-            positions = [(source, line) for source, line, uuid in self.metadata[message]]
+            positions = sorted(set((source, line) for source, line, uuid
+                                   in self.metadata[message]))
             uuids = [uuid for source, line, uuid in self.metadata[message]]
             yield Message(message, positions, uuids)
```

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `recorded: List[int]` | the projected positions `((source, line) for source, line, uuid in self.metadata[message])`, a list of `(source, line)` tuples | R | `(source, line)` tuple ↔ integer key under the order/equality-preserving bijection (mapping.md §2); list ↔ `List[int]` element-wise; scan order and duplicate multiplicity preserved. |
| A2 | the result is `dedup_sort(ToSeq(recorded))`, the strictly-ascending list of the distinct keys, computed by the verified `insert_sorted` loop folded over `recorded` (the `canonical_positions` loop with invariant `result == dedup_sort(take(i))`) | `sorted(set(...))` applied to the projected positions | A-reference | the changed operation (deduplicate + sort) is modelled **deeply**: `ins`/`dedup_sort` (the spelled-out ordered-set construction in the `pure` region) and the verified loops ARE that operation. There is **no consumed `sorted`/`set` axiom** — the proof never depends on one. The deep model is instead validated **== the real operation** out-of-band: G-AX (axiom_check.py) runs `sorted(set(...))` on boundary+fuzz and asserts `dedup_sort == sorted(set(...))`, and that the integer-key abstraction reproduces `sorted(set(positions))` over real `(source, line)` tuples (mapping.md §3.1). |
| A3 | `Result()` returned (a `List[int]`) | bound to `positions`, passed to `Message(message, positions, uuids)` | R/I | the list content is the observable; `Message.__init__` stores `self.locations = positions` (identity on content), and the F2P test reads `.locations`. The `uuids` sibling and `yield Message(...)` are unchanged by the patch and not part of the modeled behaviour (mapping.md §1). |

The discriminating content of the change — duplicates removed AND order made
strictly ascending — lives in `dedup_sort`/`ins` (model) ⇔ `sorted(set(...))`
(real). The pre-patch took the projection verbatim; `model_prepatch.py`
reproduces that (`result = result + [key]` over the scan order, no dedup/sort)
and **fails** the postcondition `ToSeq(Result()) == dedup_sort(ToSeq(recorded))`,
which is exactly the spec sensing the change (G-DIFF). The F2P test
`test_Catalog_duplicated_message` records `('/path/to/filename', 1)` twice and
expects it once, in sorted order — precisely the duplicate-and-order behaviour
the postcondition pins.

## B. Internal refinement: `insert_sorted` / `canonical_positions` ↔ `dedup_sort`

These two functions are the verified imperative skeleton of the deep pure model;
they introduce no new repo correspondence. `insert_sorted` computes `ins`
(postcondition `ToSeq(Result()) == ins(key, ToSeq(xs))`), and
`canonical_positions` folds it so `ToSeq(result) == dedup_sort(ToSeq(recorded))`.
Both are **I** with respect to the deep model: the loops compute exactly the
pure functions, by their loop invariants. The pure functions in turn are the
A-reference of step A2.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — composing the projection with deduplication and sorting — is modelled
**deeply** (the spelled-out ordered-set construction `dedup_sort`/`ins`,
consumed by `insert_sorted`/`canonical_positions`, step A2, an **A-reference**),
not hidden behind an axiom about the operation under change. There is **no
consumed axiom** in this bundle (the `axioms` region is empty); the only callee
correspondence is the **A-reference** that G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`canonical_positions` verifies only if its output equals `dedup_sort` of the
recorded positions (A2) — i.e. exactly the distinct positions, strictly
ascending. By R (tuple ↔ integer key, list ↔ `List[int]`, `Message`/`yield`
identities) the verified result equals `sorted(set((source, line) for ...))` on
the tested positions; by G-AX the deep model `dedup_sort` equals the real
`sorted(set(...))` (A-reference) and the integer-key abstraction is faithful for
`(source, line)` tuples. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited deep-model
reference — and the gold patch resolves (G-RESOLVE). The trust points reduce to
the single one of PLAN §1.1 that applies here: refinement fidelity (this
document, G-EQ) plus the A-reference soundness (axiom_check.py, G-AX); there is
no consumed-axiom trust point.
