# mapping.md — scikit-learn__scikit-learn-13439

Binds `Solution.lean` symbols to the repo at
`base_commit = a62775e99f2a5ea3d51db7160fad783f6cd8a4c5`.

Repo file under change: `sklearn/pipeline.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `compositeSize (steps : List Int)` | `Pipeline.__len__(self)` — `sklearn/pipeline.py` (added at ~line 202, after `_iter`) | the modeled added function (length of the pipeline) |
| `steps` | `self.steps` — the ordered list of `(name, estimator)` stage tuples | the stage collection |

No callee is axiomatized: the behavior is the cardinality of the input
collection, modeled deeply (`steps.length`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.steps` : `list[(str, estimator)]` | `List Int` | one element per stage; element VALUES are irrelevant (only cardinality observed); `len(self.steps)` ↔ `steps.length` |
| `len(self.steps)` : `int` (≥0) | `Nat` | non-negative; exact |

## 3. Callee provenance

None (no axioms). The whole behavior is `len`, modeled deeply as `List.length`.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **13439**. The R/I shadow is `len(steps)`;
the oracle is the patched `Pipeline.__len__` (= `len(self.steps)`), exercised by
constructing pipelines of varying length.
