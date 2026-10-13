# refinement.md — scikit-learn__scikit-learn-13439

Maps every operation in `implementation_len` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op). Every step is R, A, or I.

## Modeled function: `len` (`Pipeline.__len__`)

Post-patch repo code (`patch.diff`):
```python
def __len__(self):
    """
    Returns the length of the Pipeline
    """
    return len(self.steps)
```

Lean impl (`implementation_len`): an `Id.run do` that returns the size of the
composition's step list, in `Option Nat`.

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `self : CompSeq` (`steps : List CompStep`) | the receiver `Pipeline` `self`, observed through `self.steps` (mapping.md bijection) | **R** | `self.steps : list[(name, transform)]` ↔ `self.steps : List CompStep`; each `(name, transform)` tuple ↔ a `CompStep`. Neither `name` nor `component` is read by `__len__`. |
| 2 | `self.steps.length` | `len(self.steps)` | **I** (the changed op, deeply modeled) | **the fixed operation.** The patch ADDS `__len__` returning `len(self.steps)`; the Lean impl computes `self.steps.length` — Python `len(list)` ↔ Lean `List.length`, identical. At base_commit no `__len__` exists, so `len(pipe)` raises (modeled `none`); the prepatch impl returns `none` accordingly. |
| 3 | `return some self.steps.length` | `return len(self.steps)` | **R** | the post-patch method always produces a defined non-negative int; modeled as `some n : Option Nat` (`int` → `Nat`, the always-defined case). The exception→`Option` carrier maps "no size defined" to `none` (mapping.md result-type note). |
| 4 | `Id.run do … return …` (`Option Nat`) | `__len__` returns an `int` (or raises when absent) | **R** | result modeled as `Option Nat`: a defined size is `some n`, an undefined size (the pre-patch `TypeError`) is `none`. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch `Pipeline.__len__` (`len(self.steps)`).

## Soundness check (verify ⟹ correct)

- `problem_spec_len` pins the result to exactly `some self.steps.length`
  (directive 5 — frame: the single output component is fully constrained, equal
  to the step-list length; directive 8 — the output is grounded in the input
  `self.steps`, no ungrounded oracle). A verifying impl MUST return
  `some (len steps)` — it cannot return `none`, a wrong count, or echo an
  answer-key.
- The discriminating clause is the whole equation: the prepatch (the actual
  base_commit behavior — no `__len__`, `len(pipe)` raises) is modeled as `none`,
  which is `≠ some self.steps.length` for every composition. Hence the carried
  gold proof (`rfl`, reducing `implementation_len self` to
  `some self.steps.length`) fails to typecheck against the prepatch impl, whose
  `Id.run do return none` reduces to `none` (G-DIFF/G-PANEL).
- This is exactly what `test_make_pipeline_memory` exercises:
  `assert len(pipeline) == 2` on a two-step pipeline — post-patch `len` returns
  `2 = len(self.steps)`; pre-patch it raises (no `__len__`).
- G-CONF confirms the R/I shadow == an in-process replica of the post-patch
  `Pipeline.__len__` (`len(self.steps)`), exhaustively over the boundary
  (lengths 0..256) plus ≥1e5 fuzzed step lists with varied names/components
  (0 disagreements — the count never depends on a step's contents).
