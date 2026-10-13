# refinement.md — scikit-learn__scikit-learn-13439

Correspondence between `Solution.lean`'s `compositeSize` impl and `patch.diff`
(the gold patch adds `Pipeline.__len__`). `patch.diff` is the gold verbatim
(applies at base_commit, resolves — G-RESOLVE).

## A. The added length method — `Pipeline.__len__`

Gold hunk:
```
+    def __len__(self):
+        """Returns the length of the Pipeline"""
+        return len(self.steps)
```

| # | Solution.lean impl op (`compositeSize`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `steps : List Int` | `self.steps` (list of stage tuples) | R | `list[(str,est)]` ↔ `List Int`, one element per stage; only cardinality observed (mapping.md §2). |
| A2 | `return steps.length` | `return len(self.steps)` | I | identical concrete operation: collection cardinality. `List.length` ↔ `len`. |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. The single op is
the length of the input collection, modeled deeply and tagged **I**.

## B. verify(Solution) ⇒ resolved

`compositeSize` verifies only if `n = steps.length` (A2). By R (the stage-list
bijection) the verified result equals `len(self.steps)` on the real pipeline.
The F2P test (`test_make_pipeline_memory`, which exercises `len(pipe)` /
`pipe[:len(pipe)]`) passes iff `__len__` returns the stage count — exactly what
the spec pins. G-CONF differential-tests A2 (the I leg) against the patched
`Pipeline.__len__`. The prepatch (`return 0`) fails `n = steps.length`
whenever the pipeline is non-empty (G-DIFF). No trust points beyond the type
bijection (mapping.md §2): there are no axioms.
