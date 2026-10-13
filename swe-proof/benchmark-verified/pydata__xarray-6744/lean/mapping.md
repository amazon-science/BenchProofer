# mapping.md — symbol binding & type bijection

Instance: `pydata__xarray-6744`
base_commit: `7cc6cc991e586a6158bb656b8001234ccda25407`

## Symbols (file:line @ base_commit)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_rollingWindows` | `DataArrayRolling.__iter__` (the start/stop index computation + per-position slice) | xarray/core/rolling.py:270 |
| `winOffset window center` | `offset = (window0 + 1) // 2 if self.center[0] else 1` | xarray/core/rolling.py (added in fix) |
| `winStart window offset i` | `starts = stops - window0; starts[: window0 - offset] = 0` | xarray/core/rolling.py (added in fix) |
| `windowAt xs window center i` | `self.obj.isel({dim0: slice(start, stop)})` | xarray/core/rolling.py |
| `xs : List Int` | the 1-D data values of `self.obj` along `dim0` | DataArray cell values |
| `window : Nat` | `int(self.window[0])` | xarray/core/rolling.py |
| `center : Bool` | `self.center[0]` | xarray/core/rolling.py |
| result `List (List Int)` | the sequence of `window` DataArrays yielded by `__iter__`, taken as their underlying values | iteration order |

## Type bijection (used by G-CONF)

| Lean | Python | bridge |
|---|---|---|
| `xs : List Int` | DataArray 1-D values (`da.values`), integer-valued | per-index order preserved |
| `window : Nat` | window size `w` passed to `da.rolling(dim=w)` | identity, `w >= 1` |
| `center : Bool` | `center=` kwarg of `da.rolling` | `True ↔ true`, `False ↔ false` |
| `windowAt … i : List Int` | `window_i.values` for the `i`-th yielded `(label, window)` | the slice the window covers, in order |
| result `List (List Int)` | `[w.values for _, w in da.rolling(...)]` (pre-`where`/`count` slice) | one entry per position |

Notes:
- The modeled behavior is the **slice membership** (which contiguous range of
  the input each position's window covers) — i.e. the start/stop arithmetic that
  the fix changes. The downstream `count` / `where`-`min_periods` masking is a
  fixed post-step driven by the same slice and is out of scope of the changed
  arithmetic; G-CONF compares the slice contents (the `isel` result) directly.
- `len(self.window_labels)` equals `self.obj.sizes[dim0]` for 1-D rolling, so the
  result has exactly one window per input position; the bijection uses
  `xs.length`.
- `slice(start, stop)` with `start` clamped to 0 maps to `(xs.drop start).take
  (stop - start)`. For all modeled positions `0 <= start <= stop <= len(xs)`.

## Callee provenance & flag deps

- No unchanged callee is axiomatized. The slice extraction (`isel` + `slice`) is
  modeled directly as a list `drop`/`take`. No `_prop` axiom; `axiom_check.py`
  is a skip stub.
- Flag dependency: the forward `offset` depends on `center` — `(w+1)//2` when
  centered, else `1`. G-CONF fuzzes both `center=True` and `center=False`.

## G-CONF fuzz seed

Pinned seed: `6744`. Inputs fuzzed: sequence length (0..40), window size
(1..12), and the `center` flag (both values), with integer values.
