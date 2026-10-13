# refinement.md — scikit-learn__scikit-learn-13124

Operation-by-operation correspondence between `implementation_classOrders`
(Solution.lean impl region) and `patch.diff` (the post-patch RNG threading in
`StratifiedKFold._make_test_folds` and the per-class shuffle it drives). Tags:
**R** type refinement, **A-consumed** proof uses an axiom, **A-reference** deep
model validated == real callee by G-AX, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if !shuffle then return counts.map (fun c => List.range (max c nFolds))` | `shuffle=False` branch of `KFold._iter_test_indices`: `indices = np.arange(max(count, n_splits))` left unshuffled for every class | R |
| 2 | `let mut st : RngState := seedState seed` | `rng = check_random_state(self.random_state)` (build ONE generator from the seed) | A-reference |
| 3 | `let mut orders : List (List Nat) := []` | the `per_cls_cvs` list being accumulated | I |
| 4 | `for c in counts do` | `for count in y_counts` (per-class comprehension, consumed in class order by `zip(*per_cls_cvs)`) | R |
| 5 | `let res := shuffleN st (max c nFolds)` | `KFold(n_splits, shuffle=True, random_state=rng).split(np.zeros(max(count, n_splits)))` → `check_random_state(rng).shuffle(np.arange(max(count, n_splits)))` | A-reference |
| 6 | `orders := orders ++ [res.1]` | this class's shuffled `indices` order is recorded as its fold assignment | R |
| 7 | `st := res.2` | the SHARED `rng` instance is advanced in place by `.shuffle`, carried to the next class | A-reference |
| 8 | `return orders` | the per-class orders feed `zip(*per_cls_cvs)` → `test_folds` | R |

Notes:

- **The fix itself is the THREADING (steps 2 + 5 + 7).** The patch changes one
  line: `rng = self.random_state` → `rng = check_random_state(self.random_state)`.
  - PRE-patch, `rng` is the raw int seed; each per-class `KFold` re-runs
    `check_random_state(int)` and builds a **fresh** `RandomState(seed)`, so the
    generator NEVER advances across classes — every class is shuffled from the
    identical state. The prepatch impl mirrors this exactly: `shuffleN (seedState
    seed) (max c nFolds)` re-seeds from `seed` every iteration (no `st` carried).
  - POST-patch, `rng` is a single `RandomState` instance; `check_random_state`
    returns it unchanged and `.shuffle` ADVANCES it, so it is threaded across the
    classes in class order. The post-patch impl carries `st := res.2` forward.
- **A-reference, not consumed axiom.** The generator (`seedState` = real
  `check_random_state` on an int; `shuffleN` = real `np.arange` +
  `RandomState.shuffle` returning the order and the advanced generator) is taken
  OPAQUELY and the spec/proof assert NO property of it. The proof obligation is
  purely that the impl's threading equals the front-recursive `perClassShuffleOrders`
  fold — true for any `seedState`/`shuffleN` by structure. Because the spec
  consumes no `_prop` axiom, **G-AX has nothing to validate and skips**; the real
  generator's behavior (that it advances, so threading ≠ re-seeding) is exercised
  by **G-CONF** as an A-reference. There is no dead axiom.
- **R vs I.** Step 3 is **I** (literal empty-accumulator init). Steps 1,4,6,8 are
  **R**: the numpy arrays / `y_counts` / per-class generator objects are refined
  to `List Nat` / `List (List Nat)` carriers and the `Nat` index model per the
  mapping.md bijection. `np.arange(m)` ↔ `List.range m`; `max(count, n_splits)` ↔
  `max c nFolds`.
- **What the spec pins (frame discipline, directive 5).** Every per-class order is
  pinned: OFF → the natural ascending order; ON → exactly the order the single
  threaded generator produces for that class (`perClassShuffleOrders`, which fixes
  both the order list AND the generator state handed to the next class). Nothing
  is left unconstrained — the result list length equals `counts.length` and each
  entry is the determined order.
- **G-DIFF discriminator.** The prepatch (re-seed per class) and the fix (thread)
  agree only when the generator happens not to advance between classes, which the
  real generator does not satisfy: with ≥2 equal-length classes the prepatch gives
  them the IDENTICAL order while the fix generally gives distinct orders, and two
  seeds collapse to the same collection under the bug. The spec equates the result
  to `perClassShuffleOrders … (seedState seed)` (threaded); the prepatch impl
  produces the re-seeded orders, which differ from the threaded ones whenever
  `shuffleN (seedState seed) m ≠ shuffleN st' m` for the advanced `st'` — so its
  `correct_classOrders` is unclosable (G-DIFF).
- **Out of scope of this triple** (unchanged, not modeled): `np.unique` /
  `np.bincount` computing `y_counts`, the `type_of_target` validation, the
  `n_splits > y_counts` error/warning, and the final scatter of fold indices back
  to sample positions (`test_folds[y == cls] = …`). The patch touches none of
  them; the only behavioral change is which generator each class shuffles with,
  which this triple isolates.
- **G-CONF** mechanically refutes the R/I + A-reference legs: it drives the REAL
  repo `check_random_state` + `KFold(...).split` to recover each class's shuffled
  order with the generator threaded in class order (the genuine post-patch path),
  and diffs it element-wise against the impl shadow over an edge matrix plus ≥1e5
  fuzzed draws. The prepatch (re-seed) shadow is a negative control that MUST
  disagree on at least one configuration.

## Spec determinism (P1 repair, 2026-08-03)

`problem_spec_classOrders` pins `result` by an EXACT equality to a total
function of the inputs (`if shuffle then perClassShuffleOrders … (seedState
seed) else counts.map …`), so the spec is DETERMINISTIC:
`spec_classOrders_deterministic` (proved in `Solution.lean`, axioms
`[propext, Quot.sound]`) shows any `result` satisfying the spec equals
`implementation_classOrders`. Consequently NO observably wrong same-spec
implementation can verify — any verifying same-spec variant is extensionally
the gold (threaded-generator) behavior. In particular a gold-equivalent
RESTATEMENT of the implementation (e.g. one returning the spec's right-hand
side `perClassShuffleOrders nFolds counts (seedState seed)` directly, closing
by `rfl`) is a **positive control, not a counterexample**: its faithful
refined patch IS the gold patch and resolves (executed in a prior audit round:
RESOLVED=True). A prior audit round listed exactly such a gold-equivalent
oracle-echo in its attack set and the mechanized re-check scored it as a
spec-too-weak candidate; the determinism lemma documents why that reading is
unsound here — spec-admittance implies gold-equal output, so a same-spec
verifying file can only be a correct restatement. Auditors: submit such
restatements as the positive control (or with their gold patch under
`patches`), never as a wrong-impl attack.
