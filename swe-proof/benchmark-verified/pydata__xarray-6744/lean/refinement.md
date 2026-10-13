# refinement.md — `implementation_rollingWindows` ↔ `patch.diff`

Modeled function: `DataArrayRolling.__iter__` (xarray/core/rolling.py), restricted
to the behavior the fix touches: computing, for each position of a 1-D rolling
object, the contiguous slice `[start, stop)` of the underlying sequence that the
position's window covers.

The gold patch replaces the start/stop arithmetic:

```python
-        stops = np.arange(1, len(self.window_labels) + 1)
-        starts = stops - int(self.window[0])
-        starts[: int(self.window[0])] = 0
+        dim0 = self.dim[0]
+        window0 = int(self.window[0])
+        offset = (window0 + 1) // 2 if self.center[0] else 1
+        stops = np.arange(offset, self.obj.sizes[dim0] + offset)
+        starts = stops - window0
+        starts[: window0 - offset] = 0
```

The bug: pre-patch the forward shift is hard-wired to `1` (right-anchored
windows) and the `center` flag is never consulted, so manually iterating a
`center=True` rolling object yields right-anchored windows instead of the
centered windows produced by the vectorized reduction. The behaviors diverge
once `window >= 3` (since `(window+1)//2 >= 2`); for `window in {1,2}` the
centered offset is itself `1`, so the discriminating cases are `window >= 3`
under `center=True` — exactly the F2P parametrization (sizes 3 and 7,
`center=True`).

## Operation correspondence

| # | `implementation_rollingWindows` op | `patch.diff` / repo counterpart | tag |
|---|---|---|---|
| 1 | `offset := if center then (window + 1) / 2 else 1` | `offset = (window0 + 1) // 2 if self.center[0] else 1` | **R** |
| 2 | `for i in [0:n]` with `n := xs.length` | `zip(self.window_labels, starts, stops)`; `stops = np.arange(offset, sizes[dim0] + offset)` (length `n`) | **R** (index range) |
| 3 | `stop := offset + i` | `stops[i] = offset + i` | **R** |
| 4 | `start := if i + offset < window then 0 else stop - window` | `starts = stops - window0; starts[: window0 - offset] = 0` | **R** |
| 5 | `(xs.drop start).take (stop - start)` | `self.obj.isel({dim0: slice(start, stop)})` | **R** (slice extraction modeled directly) |
| 6 | result is `List (List Int)`, one inner list per position, position order preserved | the per-position `window` values yielded in iteration order | **I** (structural) |

- **R legs (1–5):** the start/stop index arithmetic + slice — mechanically
  differential-tested by G-CONF against the patched repo's per-window `isel`
  slice values.
- **I leg (6):** the result is the column of slices in position order, matching
  the iteration order of `__iter__`.

### Clamp equivalence (op 4)

Gold sets `starts[: window0 - offset] = 0`, i.e. the first `window0 - offset`
positions get `start = 0`. For position `i`, `i < window0 - offset` iff
`i + offset < window0`. For positions not clamped, `start = stops[i] - window0 =
(offset + i) - window`. This is exactly `winStart`:
`if i + offset < window then 0 else (offset + i) - window`. (Where the clamp
applies, `(offset+i) - window` would be negative in ℤ; in the gold ℕ-free numpy
it is the same indices that get overwritten to 0, so no behavioral gap.)

No changed op is axiomatized; the index arithmetic and slice are all modeled
deeply (R). `conf_skip=false`.
