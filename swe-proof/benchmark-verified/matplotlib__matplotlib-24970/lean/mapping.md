# mapping.md — matplotlib__matplotlib-24970

## Symbol binding (file:line @ base_commit a3011dfd1a)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_index` / `problem_spec_index` / `correct_index` | the integer-data-value → lookup-table-row-index conversion inside `Colormap.__call__` | `lib/matplotlib/colors.py:683-732` @ base_commit (edited hunk lines `715-732`) |
| `desiredIndex N x` | the net index a data value gets: palette row `x` if in range, else reserved `under` (`N`) / `over` (`N+1`) slot | `colors.py:730-731` (`xa[xa > self.N - 1] = self._i_over`; `xa[xa < 0] = self._i_under`) |
| `N` | `self.N` (palette size) | `colors.py:669` (`self.N = int(N)`) |
| reserved index `N` (under) | `self._i_under = self.N` | `colors.py:673` |
| reserved index `N + 1` (over) | `self._i_over = self.N + 1` | `colors.py:674` |
| reserved index `N + 2` (bad) | `self._i_bad = self.N + 2` | `colors.py:675` (modeled but not exercised: masked-value path, out of scope) |
| `M` (capacity) | the width of the integer index array `xa` — for a `uint8` input, `M = 256` | implicit in `xa.dtype` |
| `Except.error ()` | the rejected out-of-bound store (NumPy ≥1.24 deprecation→error) | `colors.py:730-732` pre-patch (narrow `xa`) |

## The modeled function

`Colormap.__call__(X, …)` maps data values `X` to RGBA colors via a lookup
table `self._lut` of shape `(N + 3, 4)`: rows `0 … N-1` are palette colors, row
`N` is the under-range color, row `N+1` the over-range color, row `N+2` the
bad/masked color. For **integer** input the value array `xa` is reduced to LUT
row indices and then `rgba = lut.take(xa, …)`.

The reserved-slot assignments at `colors.py:730-732` are

```python
xa[xa > self.N - 1] = self._i_over     # N + 1
xa[xa < 0]          = self._i_under    # N
xa[mask_bad]        = self._i_bad      # N + 2
```

Pre-patch, the widening cast `xa = xa.astype(int)` only ran inside the
`if xa.dtype.kind == "f":` branch (`colors.py:717-727`), so an **integer**-dtype
input kept its narrow dtype. Storing a reserved index that overflows that dtype
(e.g. `N + 1 = 257` into a `uint8`, capacity 256) is rejected by NumPy ≥ 1.24
(a `DeprecationWarning`; under the test suite's `filterwarnings = error` this is
a hard error). The gold patch hoists the cast out of the float branch so the
index array is widened for *all* dtypes before the reserved-slot stores, making
the conversion always succeed.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean |
|---|---|
| integer data value `int(v)` | `Int` |
| list of data values | `List Int` |
| palette size `self.N` | `N : Nat` |
| index-array element type capacity (`uint8 → 256`) | `M : Nat` (values `0 … M-1`) |
| resulting LUT row index | `Nat` |
| the index array (success) | `Except.ok (List Nat)` |
| out-of-bound store rejected | `Except.error ()` |

The conversion's net per-value behavior is exactly `desiredIndex N v`:
`v < 0 ↦ N`, `v ≥ N ↦ N+1`, `0 ≤ v < N ↦ v`. (In the source the over-test is
applied before the under-test — "Set the over-range indices before the
under-range" — and `implementation_index` mirrors that order; the two branches
are disjoint so the net map equals `desiredIndex`.)

## Callee provenance / flag deps

- No unchanged callee is consumed as an axiom. `self.N`, `self._i_under`,
  `self._i_over` are plain integer attributes set in `Colormap.__init__`
  (`colors.py:669-675`); they are inlined as `N`, `N`, `N + 1`. There is no
  external function whose contract the proof must assume.
- The modeled branch is the **integer-dtype** path (`xa.dtype.kind != "f"`).
  The float path (`* self.N`, clip, `astype(int)`) is behaviorally unchanged by
  the patch and is out of scope; only the placement of the widening cast (which
  affects the integer path) changed. G-CONF fuzzes integer inputs accordingly.
- `mask_bad` / `_i_bad` (masked-array path) is not exercised: the F2P test
  (`test_index_dtype[uint8]`) uses plain integer scalars, and the deprecation it
  trips on is the over/under store, not the bad store.

## G-CONF fuzz seed

`SEED = 20240630`, `N_RANDOM = 120_000` (≥ 1e5), palette sizes
`{1,2,3,4,8,16,64,128,255,256,300}` (resampled `viridis`), values fuzzed over
`[-2N-5, 2N+5]` plus the boundary catalogue `{-3,-1,0,1,N/2,N-1,N,N+1,N+5,2N,-N}`.
