# refinement.md — scikit-learn__scikit-learn-13124

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`perClassShuffles` `do` block, the `threadAll`/`threadStep`/`blockSize` deep
model, and the opaque `shuffleAfter` axiom) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee —
**A-consumed** where the proof uses the axiom's `ensures`, **A-reference** where
a deep model is validated == the real callee by G-AX), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A leg and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The shuffle-source site — `StratifiedKFold._make_test_folds` (`sklearn/model_selection/_split.py:622`)

Gold hunk (the load-bearing line; the docstring line is a comment-only edit):
```
 def _make_test_folds(self, X, y=None):
-    rng = self.random_state
+    rng = check_random_state(self.random_state)
     ...
     per_cls_cvs = [
         KFold(self.n_splits, shuffle=self.shuffle,
               random_state=rng).split(np.zeros(max(count, self.n_splits)))
         for count in y_counts]
```

`Solution.lean` models the part of `_make_test_folds` the change *affects*: the
production, for each class in order, of the permutation its block of positions
receives from the random source. The unchanged surrounding structure (the KFold
contiguous fold assignment and the scatter into `test_folds`) is **I** and is
reconstructed verbatim by G-CONF around the modeled per-class permutations.

| # | Solution.lean impl op (`perClassShuffles`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `counts : List Nat` | `y_counts = np.bincount(y_inversed)` (per-class member counts), in class order `unique_y` | R | `np.ndarray[int]` of counts ↔ `List Nat`, by position (mapping.md §2). G-CONF derives `y_counts` from `y` the same way. |
| A2 | parameter `nSplits : Nat` | `self.n_splits` | R | `int` ↔ `Nat`; identity. |
| A3 | parameter `s : Int` | `self.random_state` (the integer seed) | R | the `int` configuration value selecting the source ↔ `Int` (mapping.md §2). The Requires-satisfying inputs are the integer `random_state` the F2P test uses. |
| A4 | `blockSize nSplits count = max count nSplits` | `max(count, self.n_splits)` (the `np.zeros(max(count, n_splits))` block length) | I | identical arithmetic; `max` ↔ `max`. |
| A5 | `result := result ++ [shuffleAfter s prev sz]` — class `i` contributes the permutation its block receives from the source **after** the earlier classes' residue `prev` | `KFold(..., random_state=rng).split(np.zeros(max(count, n_splits)))` permutes the block with the SHARED `rng` (= `check_random_state(self.random_state)`), which has already shuffled every earlier class | A-reference + I | the changed data-flow is modeled **deeply**: `threadAll`/`threadStep` thread one source through the classes (`prev` = consumed block sizes = the source residue). The fold ops (`++`, the loop, recording `prev`) are **I** (transliterated by G-CONF). The equality of the opaque `shuffleAfter` to the real source consumed in sequence is the **A-reference** G-AX validates. mapping.md §3.1. |
| A6 | `prev := prev ++ [sz]` — record this class's block size so the next class is permuted from the advanced source | the SAME `rng` object is reused for the next class's `KFold` (it carries forward its advanced internal state) | I + A-reference | recording the block size in `prev` is the model's stand-in for the real source advancing by one block; the residue model's fidelity is the A-reference (G-AX (2): the residue is load-bearing). |
| A7 | `return result` (`List (List Nat)`, per-class permutations in class order) | the per-class permutations consumed by the unchanged fold-assignment/scatter loop | R/I | the list of per-class permutations ↔ the sequence of `KFold(...).split(...)` permutations, in `unique_y`/`y_counts` order; the surrounding `for test_fold_indices ...: for cls ...:` scatter is **I**, reconstructed by G-CONF. |

Discriminating content of the change — the per-class permutations come from a
SINGLE source consumed in sequence (threaded), not from a source restarted for
each class — lives in `ensures out = (threadAll nSplits s counts).1`: the fold
threads the residue `prev` into every `shuffleAfter s prev sz`. The pre-patch
code (`rng = self.random_state`, a raw int) makes each per-class `KFold` call
`check_random_state(int)`, which builds a **fresh** `RandomState(seed)` — so the
source is restarted per class (residue ignored, every class permuted from the
fresh source). `Solution_prepatch.lean` reproduces that (`shuffleAfter s [] sz`
for every class, residue dropped) and **fails** `out = (threadAll …).1` (G-DIFF),
because the threaded fold's later classes use a non-empty residue.

Why this resolves the F2P test (`test_shuffle_stratifiedkfold`): the test asserts
`sorted(test_sets(seed=0)) != sorted(test_sets(seed=1))`. Under the bug, all
classes share the identical fresh permutation, so the sorted multiset of test
sets is **seed-invariant** (the same pairings regardless of seed) — the test
fails. Under the fix, the shared source advances across classes, so distinct
seeds yield distinct per-class shuffles and distinct sorted test sets — the test
passes. (Empirically confirmed against the real generator; mapping.md §3.1.)

## B. No second site
The patch's only behavioural change is the single `rng = ...` line (plus a
comment-only docstring rewording, which carries no behaviour and is excluded from
the spec view). `_iter_test_masks`, `split`, and the surrounding scatter loop are
unchanged and reached identically pre/post-patch; they are not modeled (the
scatter is reconstructed verbatim as I-structure by G-CONF).

## C. No kind-3 (inexpressible-changed-op) steps
Every step is R, A, or I. The operation that genuinely *changed* — threading one
random source through the classes instead of restarting it per class — is modeled
**deeply** (the spelled-out fold `threadAll`/`threadStep` over the residue `prev`,
steps A5/A6, an A-reference + I), not hidden behind an axiom about the function
under change. The only axiom, `shuffleAfter`, is about the **unchanged** community
callee (the pseudo-random source); it is consumed by the verifying proof
(definitionally, via the fold) and underlies the A-reference. No dead axiom.

## D. verify(Solution) ⇒ resolved
`perClassShuffles` verifies only if its output equals `(threadAll nSplits s
counts).1` (A5/A6): the per-class permutations from a single source threaded
across the classes. By R (`int ↔ Nat`, count-array ↔ `List Nat`, seed `int ↔
Int`) the verified function equals the patched per-class permutation production on
the tested inputs; by G-AX the opaque `shuffleAfter` is the real source consumed
in sequence (A-reference: deterministic, residue load-bearing, seed sensitive); by
G-CONF the R/I transliteration (the threaded source wrapped in the unchanged
KFold fold/scatter structure) agrees with `patch.diff`'s `_make_test_folds`
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited callee — and
the gold patch resolves (G-RESOLVE). Trust points are exactly the two of plan
§1.1: axiom soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
