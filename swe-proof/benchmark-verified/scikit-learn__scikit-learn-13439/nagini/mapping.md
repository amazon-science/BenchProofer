# mapping.md — scikit-learn__scikit-learn-13439

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a62775e99f2a5ea3d51db7160fad783f6cd8a4c5`, states the type
abstraction, and gives the provenance of each axiom (there are none).

Repo file under change: `sklearn/pipeline.py` (the `Pipeline` class).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `composite_size(steps)` | `Pipeline.__len__(self)` — `sklearn/pipeline.py` (ADDED by the gold patch between `_iter` ending at line 200 and `__getitem__` at line 202) | the modeled changed function (the size query the patch introduces): `return len(self.steps)` |
| `steps` (parameter) | `self.steps` — the `Pipeline`'s ordered list of `(name, estimator)` stages, set in `Pipeline.__init__` (`sklearn/pipeline.py:127`) | the stage collection whose cardinality is reported |
| `Result()` | the value returned by `len(self.steps)` | the reported size |

At `base_commit` the class has **no** `__len__`, so `len(pipe)` raises
`TypeError: object of type 'Pipeline' has no len()` (and `pipe[:len(pipe)]`
therefore raises). The gold patch adds the method so the size is well defined.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.steps` — a Python `list` of `(name, estimator)` 2-tuples | `List[int]` — one element per stage | `self.steps[k]` ↔ `steps[k]`; `len(self.steps)` ↔ `len(steps)`. The element *values* (the name/estimator pairs) are irrelevant to the size query — only the count of stages is observed — so each stage is modelled by an opaque `int` placeholder. The list lengths are equal by construction (one model element per real stage). |
| `len(self.steps)` (Python builtin `len` on a `list`) | `len(steps)` (Nagini `len` on a `List[int]`) | identical: both return the cardinality of the collection. |

`self.steps` is a plain list (no string keys are indexed in this operation), so
no `str→List[int]` modelling is needed; the carrier is `List[int]` and the
specification is phrased directly over `len(steps)`.

## 3. Callee provenance (kind-A)

None. The `axioms` region is empty. `len(self.steps)` is the Python builtin
`len` applied to the `Pipeline`'s own `steps` list; it is modelled deeply as
`len(steps)` over the `List[int]` carrier, not axiomatized. There is no
unchanged opaque callee the proof depends on, and no deep model standing in for
a real callee (so no A-reference for G-AX to validate). `axiom_check.py`
records, for completeness, the single trivial fact the refinement relies on —
`len(self.steps)` equals the number of constructed stages — by exercising it on
real `Pipeline` objects, but the proof consumes no axiom.
