# mapping.md — scikit-learn__scikit-learn-13124

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 9f0b959a8c9195d1b6e203f08b698e052b426ca9`, states the type
abstraction, and gives the provenance of each abstracted callee (source + the
exact behaviour the abstraction relies on, checked by axiom_check.py / G-AX).

Repo file under change: `sklearn/model_selection/_split.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `per_class_draw_states(seed, n_classes)` | `StratifiedKFold._make_test_folds(self, X, y)` — `sklearn/model_selection/_split.py:622` (changed line `623`) | the modeled changed function: the per-class randomized source handling. Returns the list of per-class draw states. |
| `seed_state(seed)` *(abstract callee — A-reference)* | `sklearn.utils.check_random_state(seed)` (`sklearn/utils/validation.py:760`), the int→`numpy.random.RandomState(seed)` branch; the conversion the fix introduces at line `623` | the unchanged seed→source conversion; its real internal state is `RandomState(seed)`'s state |
| `advance(state)` *(abstract callee — A-reference)* | the per-class state transition of the one shared `RandomState` when `KFold(..., random_state=rng).split(...)` draws from it once per class via `check_random_state(rng).shuffle(indices)` (`KFold._iter_test_indices`, `_split.py:423-427`) | the unchanged per-draw state move; abstract, but validated as a genuine MOVE by G-AX |
| `state_stream(s, n)` *(deep model)* | the sequence of per-class draws produced by the per-class loop `per_cls_cvs = [KFold(..., random_state=rng).split(...) for count in y_counts]` (`_split.py:653-656`) over the SHARED, advancing `rng` | pure spec: the advancing stream of per-class draw states |

The pre-patch repo line the change replaces (for the refinement audit, not
referenced from the consumer spec view): `rng = self.random_state`
(`_split.py:623`) — a raw seed re-converted to a *fresh* source inside every
class's `KFold` (each class re-seeds identically). The post-patch line:
`rng = check_random_state(self.random_state)` — one source, shared and advanced
across classes.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the configured `self.random_state` (an `int` seed in the tested configuration) | `seed: int` | identity on the integer seed |
| the number of classes `len(y_counts)` (the per-class loop length) | `n_classes: int` | identity (a non-negative count) |
| a `numpy.random.RandomState` source | its integer internal state | a source is modelled by its state; `seed_state` is the state of `RandomState(seed)`; `advance` is the state after one per-class draw |
| the per-class draws (`per_cls_cvs`, one `KFold` split per class, consumed in lockstep) | `List[int]` of per-class draw states; specification carried by `PSeq[int]` via `ToSeq` | element k ↔ the draw state used for class k; `state_stream` is the front-recursive advancing fold |

The X/y arrays, the fold-index bookkeeping (`test_folds`, the trim of an
over-large split), `np.unique`, `np.bincount`, `type_of_target`,
`column_or_1d`, and the `ValueError`/warning guards are all UNCHANGED by the
patch and observationally orthogonal to the single changed line: the only edit
is whether the per-class sources advance through one stream (fix) or all
re-seed to the identical initial state (bug). The model abstracts exactly the
changed data-flow — the per-class draw states — and elides the unchanged
machinery, none of which the F2P test's discriminator depends on (the F2P test
only observes that two seeds give different sorted per-fold test sets, which is
a function purely of whether the per-class draws advance).

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `seed_state` / `advance` ↔ the real pseudo-random source

**`seed_state(seed)`** abstracts `sklearn.utils.check_random_state(seed)` on the
integer branch:

```python
def check_random_state(seed):
    if seed is None or seed is np.random:
        return np.random.mtrand._rand
    if isinstance(seed, (numbers.Integral, np.integer)):
        return np.random.RandomState(seed)   # <- the int branch the fix uses
    if isinstance(seed, np.random.RandomState):
        return seed                           # <- the passthrough the fix uses
    raise ValueError(...)
```

The fix `rng = check_random_state(self.random_state)` converts the seed to a
`RandomState` **once**; thereafter every class's `KFold(..., random_state=rng)`
calls `check_random_state(rng)` which hits the third branch (`return seed`) and
returns **the same** source — so the per-class `.shuffle` draws advance one
shared stream. `seed_state(seed)` is that one source's initial internal state.

**`advance(state)`** abstracts the state transition that one shared
`RandomState` undergoes when drawn from once per class (numpy
`RandomState.shuffle` of the per-class index vector in
`KFold._iter_test_indices`, `_split.py:423-427`).

Both are modelled **abstractly** (no claimed `Ensures`): the proof needs only
that they are deterministic functions of their argument. The one fact the
model's discriminator relies on — that `advance` is a genuine state **move**, so
the per-class draws are NOT all identical — is NOT asserted as a contract; it is
validated against the REAL callees by axiom_check.py (G-AX). This keeps the
abstraction the *weakest* possible (it claims nothing the real callee might
violate) while the discriminating behaviour is checked empirically.

**Soundness check (G-AX).** `axiom_check.py` runs the real numpy
`RandomState` (the source `check_random_state` wraps) and the real, patched
`sklearn.model_selection.StratifiedKFold`:

  - (A-reference 1) one shared `RandomState` drawn once per class yields
    per-class permutations that ADVANCE (successive classes differ) over 25
    seeds — confirming `advance` is a real state move;
  - (A-reference 2) re-seeding a fresh `RandomState` from the same integer seed
    for every class yields IDENTICAL per-class permutations over 25 seeds — the
    pre-patch behaviour the model forbids;
  - (end-to-end) the real patched `StratifiedKFold._make_test_folds` makes the
    sorted per-fold test sets seed-dependent (seeds 0 and 1 differ; a 12-seed
    sweep does not collapse to one assignment) — exactly the F2P observation.

It imports only numpy and the repository's own sklearn (the module the gold
patch edits); nothing else. Exit 0 iff every obligation holds.
