# refinement.md — scikit-learn__scikit-learn-14629

Maps every operation in `implementation_collectClasses` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom),
**A-reference** (deep model == real callee, G-AX), **I** (identical concrete op).

| # | Lean impl op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `subModels : List SubModel` (input) | `self.estimators_` after `super().fit(X, Y, sample_weight)` | R | `super().fit` is the unchanged callee; its result (ordered fitted sub-model list) enters as the input carrier. Bijection: list of sub-models ↔ `List SubModel`; `estimator.classes_` ↔ `SubModel.classLabels`. |
| 2 | `let mut acc := []` ; `for m in subModels do acc := acc ++ [m.classLabels]` | `[estimator.classes_ for estimator in self.estimators_]` | R | The Python list comprehension over `self.estimators_` collecting `estimator.classes_`, in target order. Imperative skeleton (accumulator `for` loop) of the same in-order build. Type refinement: `estimator.classes_` (label array) ↔ `m.classLabels` (`List Int`). |
| 3 | `return some acc` | assignment `self.classes_ = [...]` makes the attribute defined; `return self` | R | The collected view becomes the defined value of the queryable attribute. `some` ↔ "attribute defined". |

The pre-patch absence of the override (`self.classes_` never assigned →
`AttributeError`) refines to `none` in `Solution_prepatch.lean`.

No changed op is inexpressible; the collection is modeled deeply as
`List.map (·.classLabels)`. There are NO A-tagged rows: `super().fit`'s result is
consumed as input data, not as an axiom contract. ⇒ `axioms = []`,
`deep_model_references = []`, `conf_skip = false` (impl is all-R).
