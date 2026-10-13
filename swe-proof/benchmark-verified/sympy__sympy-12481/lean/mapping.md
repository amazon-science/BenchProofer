# mapping.md — sympy__sympy-12481

## Symbol binding (file:line @ base_commit c807dfe756)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_permFromCycles` / `problem_spec_permFromCycles` / `correct_permFromCycles` | the cyclic-form (`is_cycle`) branch of `Permutation.__new__` that turns a list of cycles into an array form | `sympy/combinatorics/permutations.py:846-929` @ base_commit (edited hunk: lines `897-903`) |
| the dup-rejection guard (pre-patch) | `if has_dups(temp): if is_cycle: raise ValueError(...)` | `permutations.py:898-901` (pre-patch). Post-patch: `if has_dups(temp) and not is_cycle: raise ...` |
| `applyAll` / `applyCycle` fold | `c = Cycle(); for ci in args: c = c(*ci); aform = c.list()` | `permutations.py:911-917` (the left-to-right composition that survives the patch unchanged) |
| `permSize cycles` | `Cycle.list()` extending `0..max-named` | `Cycle.list` / `Cycle.size`, `permutations.py:344-377,455-459` |
| `sizeUndetermined cycles` | `Cycle.list`'s refusal when the accumulated `Cycle` is empty and no `size` was passed | `permutations.py:369-370` (`if not self and size is None: raise ValueError('must give size for empty Cycle')`) |

## What the function does (cyclic-form path)

For `Permutation([c₀, c₁, …])` where the entries are themselves sequences
(`is_cycle = True`), the constructor:

1. flattens all cycles into `temp = flatten(args)`;
2. **(the edited check)** raises `ValueError('there were repeated elements.')`
   only in the NON-cycle (array-form) case; for cyclic input it no longer
   rejects repeats;
3. composes the cycles left-to-right: `c = Cycle(); for ci in args: c = c(*ci)`
   (`Cycle.__call__` returns the product of cycles processed so the *leftmost*
   listed cycle is applied first to a point), then `aform = c.list()`.

`Cycle.list()` returns `[self[i] for i in range(size)]` with
`size = max(named points)+1`, i.e. the array form whose `i`-th entry is the
image of `i`.

`Cycle.list` has one further step, and it is NOT part of the patch delta:
`permutations.py:369-370` refuses outright when the accumulated `Cycle` is still
empty and no explicit `size` was supplied. The accumulated `Cycle` is empty
exactly when no supplied cycle named any point, so the constructor RAISES
`ValueError('must give size for empty Cycle')` on `Permutation([[]])`,
`Permutation([[], []])` and the rest of that family. This is the
`sizeUndetermined` leg of the model, and it is unchanged by the patch: at
base_commit and post-patch alike the observed behavior on `[[]]` is that same
`ValueError` (verified by running both trees). It must be modeled anyway, because
the modeled domain admits those inputs — each cycle in `[[]]` vacuously lists
distinct points — so a model that predicted success there would predict something
the real routine never does.

Note the neighbouring case is genuinely DIFFERENT: `Permutation([])` supplies no
cycle at all, so `is_cycle = args and is_sequence(args[0])` is falsy, the
array-form branch is taken, and the result is the empty array form `[]` rather
than a refusal. `sizeUndetermined` is therefore conditioned on the cycle list
being non-empty, not on `permSize` alone.

### The bug and the fix

Pre-patch, `has_dups(temp)` was true whenever two cycles shared a point (e.g.
`[[0,1],[0,2]]` flattens to `[0,1,0,2]`), so the cyclic branch raised
`ValueError` — even though non-disjoint cycles compose into a perfectly valid
permutation. The patch drops the `is_cycle` arm of that guard (`and not
is_cycle`), so cyclic input with shared points is now COMPOSED instead of
rejected. `Permutation([[0,1],[0,2]])` now yields the array form `[1,2,0]` (=
`Permutation(0,1,2)`), matching the new F2P assertion
`Permutation([[0,1],[0,2]]) == Permutation(0,1,2)` and removing the old
`raises(ValueError, lambda: Permutation([[1],[1,2]]))`.

The duplicate-rejection for the **array-form** (non-cycle) path is unchanged and
out of scope — it is a different input shape (`is_cycle = False`) and is the
`Permutation([1,1,0])` case the test suite still rejects.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `args` — list of cycles, each a list of distinct nonneg ints | `cycles : List (List Nat)` | element-wise; cycle `cᵢ` ↦ `cycles[i]`; entries are `0`-based points |
| `Cycle.__call__` left-to-right composition + `Cycle.list()` | `applyAll cycles` applied at each index `0..permSize-1` | `aform[i] = applyAll cycles i` |
| single cycle `(a₀ … a_{k-1})` action | `applyCycle c` | `aₜ ↦ a_{(t+1) mod k}`, others fixed |
| `len(Cycle.list())` = `max named + 1` | `permSize cycles` | one past the largest point in `cycles.flatten` (`0` if none) |
| the resulting `Permutation`'s `array_form` | `result = some aform : Option (List Nat)` | success carrier; `none` models the constructor declining to build (any of its `ValueError` refusals), which is both the pre-patch rejection and the width-undetermined refusal in `Cycle.list` |

`Nat` is sound here: cycles in cyclic notation contain only nonnegative
integers (`Cycle.__init__` raises on negatives, `permutations.py:448-449`), and the F2P/issue inputs are
small nonnegative points.

The `Nodup` precondition is likewise the faithful reading of a real guard rather
than a convenience: `Cycle.__init__` raises `ValueError('All elements must be
unique in a cycle.')` when a SINGLE cycle repeats a point
(`permutations.py:450-451`), so an input violating it never reaches the composition
at all. That is a per-cycle condition and says nothing about points shared BETWEEN
cycles, which is exactly why the shared-point sub-domain the patch opens up stays
admissible.

## Callee provenance + flag dependencies

- No callee axiom is consumed. The composition of cycles (`Cycle.__call__` /
  `Cycle.list`) is the behavior the function relies on and is modeled DEEPLY as
  `applyCycle` / `applyAll` (an A-reference validated by G-CONF against the real
  `Permutation(...).array_form`), never axiomatized (§0.7). The operation the
  patch actually changes — removing the dup-guard for cyclic input — is captured
  by the difference between the pre-patch `none` return and the post-patch
  `some` return.
- Flag dependency: the modeled path is exactly the `is_cycle = True` branch
  (input is a list of lists). G-CONF constructs only list-of-lists (cyclic)
  inputs, the configuration the bug manifests in, and its generators now draw the
  degenerate (no-point-named) family and the no-cycle case too, so no part of the
  modeled domain is excluded from the differential.

## G-CONF fuzz seed

`SEED = 20240630` (pinned in `conformance_check.py`).
