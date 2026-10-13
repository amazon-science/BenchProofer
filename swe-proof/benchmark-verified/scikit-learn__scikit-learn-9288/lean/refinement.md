# refinement.md — scikit-learn__scikit-learn-9288

Operation correspondence between `implementation_bestTrial` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are consumed. The per-attempt routine (`kmeans_single`) is left
`opaque runTrial : Int → Outcome` with NO `_prop` (the selection is correct for
any attempt routine). The changed behavior — the serial best-of-`n_init` loop now
running over the precomputed seed list so each attempt is driven by its
corresponding supplied value — is modeled DEEPLY (A-reference) and
differential-tested by G-CONF. Every row is **R**, **A-reference**, or **I**.
G-AX is a skip stub.

## The gold patch

```python
seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)   # hoisted above the branch
if effective_n_jobs(n_jobs) == 1:
    for seed in seeds:                                               # was: for it in range(n_init)
        labels, inertia, centers, n_iter_ = kmeans_single(
            X, …, random_state=seed)                                 # was: random_state=random_state
        if best_inertia is None or inertia < best_inertia:
            best_labels, best_centers, best_inertia, best_n_iter = labels, centers, inertia, n_iter_
else:
    # seeds line removed from here (hoisted up); parallel branch already used `seeds`
    results = Parallel(...)(delayed(kmeans_single)(..., random_state=seed) for seed in seeds)
    best = np.argmin(inertia); best_* = *[best]
```

The fix makes the serial branch consume exactly the `seeds` array the parallel
branch consumes, so `k_means`'s output no longer depends on `n_jobs`.

## `implementation_bestTrial` ↔ the single-thread selection loop

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| parameter `trials : List Int` | `seeds = random_state.randint(np.iinfo(np.int32).max, size=n_init)` | R | the per-attempt seed array ↦ `List Int`; the patch HOISTS this line so the serial branch receives it. `randint` value-identical (unchanged RNG), so it is an INPUT, not modeled |
| `for t in trials do let o := runTrial t` | `for seed in seeds: … = kmeans_single(X, …, random_state=seed)` | A-reference | THE EDITED op: each attempt is driven by the corresponding supplied value (`for seed in seeds` / `random_state=seed`), not by the loop index / shared RNG. `kmeans_single` is the unchanged callee `runTrial`; deterministic in its seed |
| `match best with none => some o \| some b => if o.cost < b.cost then some o` | `if best_inertia is None or inertia < best_inertia: best = …` | I | running best, STRICT `<` ⇒ first minimum kept (matches `np.argmin`'s first-occurrence tie-break in the parallel branch) |
| `return best.getD default` | `return best_labels, best_inertia, …` | R | the whole chosen attempt's outcome (cost + produced data) returned verbatim; frame: all components come from one `runTrial` |

`Outcome.cost : Int` is an ORDER-ONLY refinement of `inertia : float` (only `<` /
argmin observed; DECISIONS.md keeps float order out of the kernel). G-CONF fuzzes
the order relation and confirms the Lean selection == both real idioms (serial
running-best and parallel `np.argmin`).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the serial loop is driven by the attempt POSITION
  (`for p in [0:trials.length] do runTrial (Int.ofNat p)`) instead of the
  supplied value `trials.get p` — the pre-patch shape, where the serial branch's
  randomness was NOT the `seeds` array the parallel branch uses. The carried gold
  proof of `correct_bestTrial` cannot close: the discriminating clause
  `result = runTrial (trials.get i)` is unprovable because the result comes from
  `runTrial (index)`. This is the single fixed behavior.
  (FAIL_TO_PASS: `test_result_of_kmeans_equal_in_diff_n_jobs`.)
