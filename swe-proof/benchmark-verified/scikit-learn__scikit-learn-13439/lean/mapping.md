# mapping.md — scikit-learn__scikit-learn-13439

## Symbol binding (file:line @ base_commit a62775e99f)
Modeled function: the size query of a `Pipeline`, added by the gold patch as
`Pipeline.__len__(self)` in `sklearn/pipeline.py` (inserted between `_iter`,
ending at `pipeline.py:204`, and `__getitem__`, beginning at `pipeline.py:206`).
The method returns `len(self.steps)`. At `base_commit` no `__len__` exists on
`Pipeline` nor anywhere in its base chain (`_BaseComposition` →
`BaseEstimator`; `sklearn/utils/metaestimators.py:17`, `sklearn/base.py`), so
`len(pipe)` raises `TypeError: object of type 'Pipeline' has no len()`.

`self.steps` is the list of `(name, transform)` tuples set in
`Pipeline.__init__` (`pipeline.py:128`, `self.steps = steps`); it is the
list-of-step-tuples carrier the whole class is built around.

Lean modeled function name: `len` (names the *behavior* — "report the size of a
sequential composition" — at the abstract level; the public `problem_statement`
already names `Pipeline`, `len`, and `steps`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `self : CompSeq` | the `Pipeline` instance `self` |
| `self.steps : List CompStep` | `self.steps : list[(name, transform)]` (`pipeline.py:128`) |
| `CompStep` | one `(name, transform)` tuple in `self.steps` |
| `CompStep.name : String` | the tuple's `name` (a `str`) — never read by the size query |
| `CompStep.component : String` | the tuple's `transform`/estimator object — never read by the size query (opaque stand-in) |
| `self.steps.length` | `len(self.steps)` (`pipeline.py`, the new `__len__` body) |
| result `: Option Nat` | the value `len(pipe)` produces: `some n` = a defined size `n`; `none` = no size defined (the pre-patch `TypeError`) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.steps : list[(str, estimator)]` | `self.steps : List CompStep` |
| one `(name, transform)` tuple | `CompStep` (with `name`, `component`) |
| `len(self.steps) : int (≥ 0)` | `self.steps.length : Nat` |
| `len(pipe)` returns an int `n` | `some n : Option Nat` |
| `len(pipe)` raises `TypeError` (pre-patch, no `__len__`) | `none : Option Nat` |

### Result-type modeling note
Python's `len()` either returns a non-negative `int` or, when no `__len__` is
defined, raises `TypeError`. We model the result as `Option Nat`: `some n` is a
defined size, `none` is "no size defined" (the exception case — the
exception→`Option` mapping from the SPEC_GUIDE §2 type table). The post-patch
method always returns an int, so the modeled result is always
`some (len self.steps)`; the pre-patch absence of `__len__` is the `none` case
that `Solution_prepatch.lean` exhibits, which the spec rejects.

## Callee provenance + flag deps
- **No unchanged callee is consumed as an axiom.** The size query performs only
  one operation: take the length of the step list (`len(self.steps)`), modeled
  directly as `List.length`. There is no `opaque`/`axiom` callee contract ⇒
  `axioms = []`, `deep_model_references = []`, `axiom_check.py` is a skip stub
  (G-AX skips).
- No flag dependency: `__len__` has no parameters and branches on nothing.

## G-LEAK
The solver-visible `problem_statement` publicly names `Pipeline`, `len`,
`pipe[:len(pipe)]`, and `pipe`. The gold diff adds the dunder method `__len__`
(stripped/len-filtered to `len`, which is public via the problem statement) on
`Pipeline`; the section header names `_iter` (a neighbouring method) — that token
appears NOWHERE in the spec view (no identifier embeds it; no comment names it).
No gold-diff line is reproduced, no diff marker, no patched file path, no
bug→fix mechanism is narrated; the docstring states the abstract size behavior
only ("the size of a sequential composition equals the number of steps").

## Pinned G-CONF fuzz seed
`13439`.
