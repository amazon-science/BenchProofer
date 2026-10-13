# mapping.md — scikit-learn__scikit-learn-13124

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9f0b959a8c9195d1b6e203f08b698e052b426ca9`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one axiom.

Repo file under change: `sklearn/model_selection/_split.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `perClassShuffles (counts) (nSplits) (s)` | the per-class permutation production inside `StratifiedKFold._make_test_folds` — `sklearn/model_selection/_split.py:622` (the `per_cls_cvs = [KFold(..., random_state=rng).split(np.zeros(max(count, n_splits))) for count in y_counts]` comprehension, body line ~654) | the modeled changed computation (per-class shuffle from the shared source) |
| `shuffleAfter` *(axiom — A-reference)* | the pseudo-random source `KFold._iter_test_indices` consumes — `check_random_state(self.random_state).shuffle(indices)` (`sklearn/model_selection/_split.py:427`), i.e. `numpy.random.RandomState` | unchanged community callee: the random generator threaded through the per-class KFold |
| `threadStep`, `threadAll` *(deep model — A-reference)* | the threading of one shared `rng` across the per-class `KFold(...).split(...)` calls (post-patch `rng = check_random_state(self.random_state)`) | pure spec: per-class permutations from the single source consumed in sequence; deep model validated by axiom_check.py (G-AX), NOT a consumed answer-key |
| `blockSize nSplits count` | `max(count, self.n_splits)` — the `np.zeros(max(count, n_splits))` block length (`_split.py:656`) | pure spec: the block size permuted for one class |

The pre-patch repo symbol the change replaces (refinement audit only, not in the
consumer spec view): the raw `rng = self.random_state` (`_split.py:623`) — an
integer seed re-consumed by `check_random_state` *inside each* per-class
`KFold._iter_test_indices`, so each class gets a freshly-seeded `RandomState`
(the source restarted per class). A comment-only docstring rewording at
`_split.py:579` carries no behaviour.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `y_counts` (`np.bincount(y_inversed)`, per-class member counts in `unique_y` order) | `counts : List Nat` | the `i`-th class count ↔ `counts[i]`; `len(y_counts)` ↔ `counts.length`. G-CONF derives `y_counts` from `y` exactly as the repo does (`np.unique(..., return_inverse=True)` then `np.bincount`). |
| `self.n_splits` (`int`) | `nSplits : Nat` | identity on non-negative ints. |
| `self.random_state` (`int` seed) | `s : Int` | identity; the integer seed selecting the source. The F2P test passes integer `random_state` (0 and 1). |
| one per-class permutation (`np.ndarray[int]`, a permutation of `range(max(count, n_splits))`) | one `List Nat` | the permutation as a list of 0-based positions, in order; `np.ndarray` element ↔ `Nat`. |
| the sequence of per-class permutations | `List (List Nat)` | in `unique_y`/`y_counts` order, by position. |

The modeled `perClassShuffles` captures the per-class permutations; the unchanged
surrounding structure of `_make_test_folds` (the `KFold` contiguous fold
assignment of each permutation, and the `for test_fold_indices ...: for cls ...:`
scatter into `test_folds`) is **I** and is reconstructed verbatim by G-CONF
(`conformance_check.py`) around the modeled permutations.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `shuffleAfter` / `threadAll` ↔ a shared `numpy.random.RandomState` consumed in sequence (A-reference)
**Callee:** `numpy.random.RandomState` (obtained post-patch by
`check_random_state(self.random_state)`), the generator the per-class
`KFold._iter_test_indices` calls `.shuffle(indices)` on. The changed data-flow —
one source threaded through the classes — is modeled **deeply** by
`threadAll`/`threadStep`; the opaque `shuffleAfter s prev sz` denotes "the
permutation the source selected by `s` yields for a block of size `sz`, after it
has already permuted blocks of sizes `prev` in order". There is **no consumed
answer-key axiom**: `shuffleAfter` pins no specific permutation value; its only
load-bearing content is functional determinism + that the residue `prev` matters.

**The crux of the bug (provenance for the discriminator).** `check_random_state`
(`sklearn/utils/validation.py:760`) returns:
  * for an **int** seed: a **fresh** `np.random.RandomState(seed)` — a new source;
  * for a **RandomState instance**: **that same instance** (identity).

Pre-patch, `_make_test_folds` sets `rng = self.random_state` (the raw int), so
each per-class `KFold(..., random_state=int)` re-enters `check_random_state(int)`
and builds a *fresh* `RandomState(int)` — every class is shuffled identically
from the source's initial state (residue ignored). Post-patch,
`rng = check_random_state(self.random_state)` builds **one** `RandomState`
instance once; each per-class `KFold(..., random_state=<that instance>)` re-enters
`check_random_state(instance)` which returns the *same* instance, so the source
**advances** across classes (the residue `prev` is real). This is the threading
`threadAll` models.

Flag dependency: the per-class shuffle only happens under `shuffle=True`
(`KFold._iter_test_indices`: `if self.shuffle: check_random_state(...).shuffle`).
The F2P test and the modeled behaviour are the `shuffle=True` configuration;
G-CONF and G-AX fuzz that configuration.

**Soundness check (G-AX):** `axiom_check.py` runs the real `numpy.random.RandomState`
as the sequential source and asserts (1) `shuffleAfter` is deterministic in
`(s, prev, sz)` and always a permutation of `range(sz)`; (2) the residue `prev` is
load-bearing — the threaded result differs from the reset result (`prev = []`) on
a large fraction of configs, so the model is not vacuously the buggy one; (3)
distinct seeds give distinct permutations (grounding the F2P assertion). Imports
only numpy + stdlib. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13124`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `threadAll`/`threadStep`/`blockSize` (R/I-tagged ops) to Python —
one shared `np.random.RandomState(s)` consumed in sequence across the classes —
and wraps them in the unchanged `KFold` fold-assignment + scatter I-structure.
The A-tagged callee `shuffleAfter` is left as the **real** numpy shuffle (run the
real callee, not an axiom model), per §4.1. The oracle is the patched
`StratifiedKFold._make_test_folds` at base_commit (the harness applies patch.diff
first). Requires-satisfying inputs: valid binary/multiclass `y`, `n_splits >= 2`
and `<=` the smallest class count.
