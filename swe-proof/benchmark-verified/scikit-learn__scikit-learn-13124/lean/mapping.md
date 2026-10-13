# mapping.md — scikit-learn__scikit-learn-13124

## Symbol binding (@ base_commit 9f0b959a8c9195d1b6e203f08b698e052b426ca9)

- Changed function: `StratifiedKFold._make_test_folds`
  — `sklearn/model_selection/_split.py:622-672` @ base_commit.
- The single changed line: `sklearn/model_selection/_split.py:623`
  `rng = self.random_state` → `rng = check_random_state(self.random_state)`.
- The site that CONSUMES `rng`: the per-class fold-splitter list comprehension,
  `sklearn/model_selection/_split.py:653-656`:
  ```python
  per_cls_cvs = [
      KFold(self.n_splits, shuffle=self.shuffle,
            random_state=rng).split(np.zeros(max(count, self.n_splits)))
      for count in y_counts]
  ```
  consumed interleaved by `zip(*per_cls_cvs)` at L658; on the first round each
  class's generator runs to its first `yield`, which is where its own per-class
  shuffle happens.
- The per-class shuffle itself: `KFold._iter_test_indices`,
  `sklearn/model_selection/_split.py:423-427`:
  ```python
  indices = np.arange(n_samples)
  if self.shuffle:
      check_random_state(self.random_state).shuffle(indices)
  ```
  with `n_samples = max(count, n_splits)` (the `np.zeros(max(count, n_splits))`
  passed in at L656).
- Unchanged callees used: `check_random_state`
  (`sklearn/utils/validation.py`, `check_random_state(seed)`: int → fresh
  `np.random.RandomState(seed)`; RandomState instance → returned unchanged) and
  `numpy.random.RandomState.shuffle` (in-place Fisher–Yates permutation that
  ADVANCES the generator's internal state).

## The behavioral change being modeled

`rng` is built ONCE in `_make_test_folds`. With the bug it is the raw
`self.random_state` (an int seed, in the tested configuration); with the fix it
is `check_random_state(self.random_state)`, a `RandomState` *instance*.

That single difference changes how the generator is THREADED across classes:

- BUG (`rng` = int seed): each per-class `KFold` stores `random_state=<int>`, so
  `check_random_state(<int>)` inside `_iter_test_indices` builds a **fresh**
  `RandomState(seed)` for every class. The generator never carries forward; every
  class is shuffled from the identical starting state. Classes whose index range
  has the same length receive the IDENTICAL order, and the int seed has no power
  to differentiate the overall collection of orders.
- FIX (`rng` = `RandomState` instance): each per-class `KFold` stores that SAME
  instance; `check_random_state(instance)` returns it unchanged, and `.shuffle`
  ADVANCES it. The single generator is consumed once per class in class order, so
  successive classes draw from successive generator states and generally receive
  DISTINCT orders; distinct seeds yield distinct overall collections.

## Lean ↔ Python type bijection (G-CONF / G-AX use this)

| Python | Lean |
|---|---|
| int seed `self.random_state` | `seed : Nat` |
| `self.shuffle : bool` | `shuffle : Bool` |
| `self.n_splits : int` | `nFolds : Nat` |
| `y_counts : np.ndarray[int]` (per-class sample counts, in class order) | `counts : List Nat` |
| `max(count, n_splits)` (per-class range length) | `max c nFolds` |
| `np.arange(m)` natural order | `List.range m` (= `[0,1,…,m-1]`) |
| shuffled `indices` array for one class | one `List Nat` (a permutation of `List.range m`) |
| the list of per-class shuffled orders (in class order) | `result : List (List Nat)` |
| `RandomState` generator value (opaque, threaded) | `RngState` (`abbrev … := Nat`), value of `seedState`/`shuffleN.2` |
| `check_random_state(int_seed)` | `seedState : Nat → RngState` |
| one consume `arange(m); rng.shuffle(arange(m))` returning (order, advanced rng) | `shuffleN : RngState → Nat → (List Nat × RngState)` |

## Callee provenance + flag dependency

- `seedState`/`shuffleN` are declared `opaque` and taken **structurally** (like an
  opaque input): the spec/proof assert NO property of them (no `_prop` axiom is
  consumed). What is pinned is purely the THREADING discipline — one `seedState`
  seeding, then `shuffleN` consumed once per class with the advanced state carried
  forward. This holds for ANY generator, so it needs no callee contract.
- The real generators behind `shuffleN`/`seedState` (`numpy.random.RandomState`
  seeding + `.shuffle`) are exercised as an **A-reference** by `conformance_check.py`
  (G-CONF), NOT by an axiom. There is no consumed axiom → G-AX skips.
- **Flag dependency:** the per-class shuffle only happens under `shuffle=True`
  (`KFold._iter_test_indices` L426 guard, inherited from `self.shuffle`). G-CONF
  fuzzes both `shuffle` values; the threaded-generator behavior is the
  `shuffle=True` configuration.

## G-CONF fuzz seed

Pinned `conf_seed = 13124` (used for the stdlib `random` draws over seeds /
n_splits / per-class counts in `conformance_check.py`). NumPy generators inside
the oracle/shadow are seeded by the per-draw `seed` value itself, matching the
real code path.
