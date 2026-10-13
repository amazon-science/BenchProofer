# mapping.md — pydata__xarray-6744

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7cc6cc991e586a6158bb656b8001234ccda25407`, states the type
abstraction, and records the provenance of the deep model.

Repo file under change: `xarray/core/rolling.py`.
Changed function: `DataArrayRolling.__iter__` (`xarray/core/rolling.py:270-282`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `block_ends(n, w, center)` | the `stops` index array built in `DataArrayRolling.__iter__` (`xarray/core/rolling.py:273` pre / the `stops` line post-patch) | the per-position window END indices (one site of the changed function) |
| `block_begins(n, w, center)` | the `starts` index array built in `DataArrayRolling.__iter__` (`xarray/core/rolling.py:274-275` pre / the `starts` lines post-patch) | the per-position window START indices (the other site of the changed function) |
| `end_shift(w, center)` | the `offset` local of the patched `__iter__` (post-patch: `(window0 + 1)//2 if self.center[0] else 1`) | pure spec: forward shift of every block end |
| `end_at(i, w, center)` | `stops[i]` of the patched `__iter__` (post-patch `stops = np.arange(offset, n + offset)`, so `stops[i] = offset + i`) | pure spec: end index of position i |
| `begin_at(i, w, center)` | `starts[i]` of the patched `__iter__` (post-patch `starts = stops - window0` then `starts[: window0 - offset] = 0`, i.e. `max(0, offset + i - window0)`) | pure spec: start index of position i |
| `ends_from / begins_from` | (proof scaffolding) the in-order sequence of the above over positions `j..n-1` | pure fold materializing the index arrays for the loop invariant |
| `ends_unfold / begins_unfold / ends_index_lemma / begins_index_lemma` | (proof scaffolding only) | front-recursion unfold + index-projection lemmas for the folds |

Inputs of the modeled functions ↔ repo quantities inside `__iter__`:
- `n` ↔ `self.obj.sizes[dim0]` (post-patch) = `len(self.window_labels)` (the
  size of the rolling dimension; equal pre- and post-patch).
- `w` ↔ `int(self.window[0])` (the 1-d window size; `__init__` enforces `w > 0`,
  `xarray/core/rolling.py:106-108`).
- `center` ↔ `self.center[0]` (the per-dimension centred flag for this 1-d
  rolling; a plain `bool`).

The values `start_i, stop_i` produced by the model are precisely the bounds of
the half-open slice `slice(start, stop)` passed to `self.obj.isel({dim0: ...})`
at `__iter__` (post-patch). The slicing (`isel`), the per-window NaN masking
(`count`/`where`) and the `yield` are the UNCHANGED tail of the function: the
patch alters only how `starts`/`stops` are computed, so the model specifies
exactly those two arrays and treats the rest as the unchanged caller.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `np.arange(...)` integer index array (`stops`, `starts`) | `List[int]` of the same integer values in the same order | `arr[i]` ↔ `Result()[i]`; `len(arr)` ↔ `len(Result())`; numpy int subtraction / slice-assign-zero ↔ the same integer arithmetic on `int` |
| `offset` (a Python/np `int`) | `int` | identity |
| `int(self.window[0])` | `int` `w` with `w > 0` | identity (window positivity is a constructor invariant) |
| `self.center[0]` | `bool` `center` | identity |
| `self.obj.sizes[dim0]` | `int` `n >= 0` | identity (a dimension size) |

No string or float modeling is involved: the changed operation is integer
index arithmetic, modeled exactly. `np.arange(a, b)` over an integer range is
the ascending integer list `[a, a+1, ..., b-1]`; the gold patch's
`stops = np.arange(offset, n + offset)` therefore has `stops[i] = offset + i`
for `0 <= i < n`, which is `end_at(i, w, center)`. `starts = stops - window0`
then the leading clamp `starts[: window0 - offset] = 0` yields
`starts[i] = max(0, offset + i - window0)`, which is `begin_at(i, w, center)`
(see §3 for the clamp algebra).

## 3. Provenance of the deep model (A-reference — checked by G-AX / axiom_check.py)

There are **no axiomatized library callees**: the operation the patch changes
is the index computation itself, modeled deeply. The deep model is validated
**== the real changed operation** (the gold patch's `starts`/`stops`) by
`axiom_check.py` (G-AX), as an A-reference.

### 3.1 `end_shift` ↔ the patch's `offset`
Post-patch source (`xarray/core/rolling.py`, the `__iter__` body):
```python
dim0 = self.dim[0]
window0 = int(self.window[0])
offset = (window0 + 1) // 2 if self.center[0] else 1
stops = np.arange(offset, self.obj.sizes[dim0] + offset)
starts = stops - window0
starts[: window0 - offset] = 0
```
`end_shift(w, center)` returns `(w + 1)//2` when centred and `1` otherwise —
byte-for-byte the patch's `offset`. `(w + 1)//2 == ceil(w/2)` for `w > 0`
(floor of `(w+1)/2`); for `w = 1` it is `1`, collapsing centred to non-centred,
matching the patch.

### 3.2 the clamp algebra `begin_at(i) == max(0, end_at(i) - w)`
The patch sets `starts = stops - window0` then `starts[: window0 - offset] = 0`.
For `i >= window0 - offset`: `starts[i] = offset + i - window0 >= 0` (since
`i >= window0 - offset`), so the clamp leaves it unchanged. For
`i < window0 - offset`: `offset + i - window0 < 0`, and the slice assigns `0`.
Hence `starts[i] = max(0, offset + i - window0) = max(0, end_at(i) - w)`,
which is exactly `begin_at(i, w, center)` (the model clamps `raw` to `0` when
`raw <= 0`). The pre-patch code clamps the first `window0` entries (not
`window0 - offset`) but with `offset == 1` always, so its leading clamp and its
shift both differ from the centred case.

### 3.3 the soundness witness (the F2P discriminator)
For the issue's example `n = 9, w = 3, center = True`: `offset = 2`,
`end_at(1) = 3`, `begin_at(1) = 0`, so position 1's block is `[0, 3)`
(values 1,2,3, mean 2.0) — the centre-justified result `[nan, 2, 3, ...]`. The
pre-patch rule (`offset = 1` always) gives position 1's block `[0, 2)`
(values 1,2, masked to NaN by `min_periods`), the buggy `[nan, nan, 2, ...]`.
`axiom_check.py` reproduces the gold patch's `np.arange`/subtract/slice-assign
arithmetic with plain ints and asserts `end_at`/`begin_at` equal it on the
boundary sweep (sizes 0..21, windows 1..21, both centred flags) plus 200 000
randomized `(n, w, center)` fuzz cases, plus the worked example. Exit 0 iff
sound. stdlib-only.

## 4. Flag dependencies
None. The computation depends only on `w > 0`, `n >= 0`, and the `center`
boolean; there is no library call whose default flags matter (cf. the
`html.escape quote=True` dependency in other bundles).
