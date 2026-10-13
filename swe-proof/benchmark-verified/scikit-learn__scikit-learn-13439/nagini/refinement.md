# refinement.md — scikit-learn__scikit-learn-13439

The operation-by-operation correspondence between `model.py`'s implementation
(the `composite_size` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed** / **A-reference**), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs,
so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The size site — `Pipeline.__len__` (added in `sklearn/pipeline.py`)

Gold hunk (inserted between `_iter` and `__getitem__`):
```
+    def __len__(self):
+        """
+        Returns the length of the Pipeline
+        """
+        return len(self.steps)
```

| # | model.py impl op (`composite_size`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `steps: List[int]` | the receiver's `self.steps` attribute | R | `self.steps` is the `Pipeline`'s ordered list of `(name, estimator)` stages; `List[int]` (one opaque element per stage) is that carrier with the irrelevant pair values abstracted away (mapping.md §2). One model element per real stage, so the lengths agree. |
| A2 | `len(steps)` | `len(self.steps)` | I + R | the Python builtin `len` on the stage list. Identical `len` operation; the only difference is the carrier type (`List[int]` ↔ `list` of tuples), an R refinement that preserves cardinality (mapping.md §2). |
| A3 | `return len(steps)` (an `int`) | `return len(self.steps)` | I + R | returning the stage count. Identical return of the `len` value; `int` ↔ `int`. |

The discriminating content of the change — the reported size is the FULL
cardinality of the stage collection, every stage counted once including the
final stage and any inert placeholder stages — lives in the postcondition
`Result() == len(steps)`. At `base_commit` the method is absent, so `len(pipe)`
raises and `pipe[:len(pipe)]` raises; the F2P test `test_make_pipeline_memory`
adds `assert len(pipeline) == 2` for a 2-step pipeline, i.e. it demands exactly
`len(self.steps)`.

`model_prepatch.py` reproduces the only *truncated* stage-traversal present in
the surrounding code — `_iter(with_final=False)` does `stop -= 1`, walking one
fewer than `len(self.steps)` — as the candidate size (`len(steps) - 1`), and
**fails** verification on the obligation `Result() == len(steps)` (G-DIFF).
That is exactly the spec sensing that the reported size must be the whole
collection's cardinality, not a count that drops the terminal stage.

## B. No consumed axiom; no A-reference

The `axioms` region is empty. The changed behaviour is modelled **deeply** as
the length of the input collection (`len(steps)`); no `@ContractOnly` contract
is consumed by the proof, and there is no deep model standing in for a real
callee that G-AX must validate. `len` is the Python builtin applied to the
`Pipeline`'s own `steps` list — modelled directly by Nagini's `len` over the
`List[int]` carrier — not an opaque callee. `axiom_check.py` exercises, for
completeness, the single fact the refinement relies on (real `len(pipeline)`
post-patch equals the number of constructed stages), but the proof consumes no
axiom.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is I, R, or I-of-R. The one operation that genuinely changed —
introducing a size query that returns the stage-collection cardinality — is
modelled directly with `len(steps)` over `List[int]`, not hidden behind an
axiom. There is no kind-3 step.

## D. verify(model) ⇒ resolved

`composite_size` verifies only if it produces `Result() == len(steps)` — the
exact cardinality of the stage collection — while leaving the collection
unmutated (the read-only fractional permission `Acc(list_pred(steps), 1/2)` is
required AND ensured, directive 5, so a wrong impl cannot satisfy the spec by
overwriting `steps`). By the R-refinement (mapping.md §2:
`self.steps`↔`List[int]`, one element per stage, `len`↔`len`) a verified
implementation is exactly `return len(self.steps)` of the gold patch. The F2P
test `test_make_pipeline_memory` constructs a 2-step pipeline and asserts
`len(pipeline) == 2 == len(self.steps)`; the P2P indexing tests
(`test_pipeline_slice`, `test_pipeline_index`) continue to pass because the
added method does not touch indexing. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The only trust point is refinement fidelity
(this document, G-EQ); there is no axiom, so G-AX is vacuous.
