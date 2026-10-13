# mapping.md — pydata__xarray-6599

## Symbol binding (file:line @ base_commit 6bb2b855498b5c68d7cca8cceb710365d58e6048)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_coerceToFloat` / `problem_spec_coerceToFloat` / `coerceResult` | `to_floatable`, the inner helper of `_ensure_numeric` (the value-coercion it performs per array) | `xarray/core/computation.py:1935-1945` |
| `datetimeToFloat` (opaque callee) | `datetime_to_numeric(x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns")` | `xarray/core/duck_array_ops.py:398` (called from `computation.py:1938`) |
| `ValKind` (pure helper) | `x.dtype.kind` (the numpy dtype-kind character) | `computation.py:1936` |
| `ArrayView` (pure helper) | the observations of `x` the helper reads: its dtype kind, its underlying integer buffer, and its float values | `computation.py:1935-1945` |

The modeled function is `to_floatable`, the per-array coercion inside
`_ensure_numeric`. It is the only behavior the patch changes and the behavior the
FAIL_TO_PASS test (`test_polyval[timedelta-False]`) observes: `polyval` calls
`_ensure_numeric(coord)`; for a duration (timedelta64) coordinate the coerced
float values must equal the integer nanosecond counts cast to float, so that
Horner evaluation produces the v2022.3.0 results.

### What the function does

`_ensure_numeric` maps `to_floatable` over every variable (`Dataset.map`) or
applies it to a lone `DataArray`. That `Dataset`/`DataArray` dispatch is unchanged
plumbing; the only changed logic is `to_floatable` itself.

base_commit (buggy):

```python
def to_floatable(x):
    if x.dtype.kind in "mM":          # both datetime ("M") AND timedelta ("m")
        return x.copy(data=datetime_to_numeric(
            x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns"))
    return x
```

post-patch (gold):

```python
def to_floatable(x):
    if x.dtype.kind == "M":           # datetimes only
        return x.copy(data=datetime_to_numeric(
            x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns"))
    elif x.dtype.kind == "m":         # timedeltas
        return x.astype(float)
    return x
```

numpy dtype `.kind` is `"M"` for `datetime64`, `"m"` for `timedelta64`. The bug:
a `timedelta64` array satisfied `kind in "mM"` and so was routed through
`datetime_to_numeric` with a `datetime64` offset — `array - offset` raises
`UFuncTypeError` (timedelta minus datetime), and even when it does not raise the
epoch reduction is wrong for a duration. The fix gives durations their own branch
`x.astype(float)`, which reinterprets the underlying `int64` nanosecond counts
directly as floats (e.g. `timedelta64[ns]` counts `[1000,2000,3000]` → floats
`[1000.0,2000.0,3000.0]`).

### Lean modeling

- `ValKind` models the three coercion-relevant `dtype.kind` cases: `datetime`
  (`"M"`), `duration` (`"m"`), `numeric` (everything else — the identity branch).
- `ArrayView` records the observations the branches read: `kind`, `raw` (the
  underlying `int64` nanosecond buffer that both time branches read; for the
  duration branch it is what `astype(float)` reinterprets), and `data` (the
  array's values as floats, returned unchanged by the numeric branch).
- The **datetime** branch is an UNCHANGED callee: `datetime_to_numeric` with a
  fixed epoch and unit. It is declared `opaque datetimeToFloat : List Int → List
  Float` (signature only) and used identically in spec and impl; no property of
  it is consumed by the proof (it cancels syntactically). → A-reference / no
  consumed axiom (G-AX skip; see below).
- The **duration** branch is modeled DEEPLY as `raw.map Float.ofInt`: a
  `timedelta64[ns]` array's `astype(float)` casts each underlying `int64`
  nanosecond count to its float value, exactly `Float.ofInt` per element. This is
  the changed op, so it is spelled out, never axiomatized (SPEC_GUIDE §3).
- The **numeric** branch returns `data` unchanged (`return x`).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `x.dtype.kind == "M"` | `ValKind.datetime` | identity |
| `x.dtype.kind == "m"` | `ValKind.duration` | identity |
| any other `x.dtype.kind` | `ValKind.numeric` | the identity (`return x`) branch |
| `x.data` viewed as `int64` (ns counts) | `raw : List Int` | element-wise `int64 ↔ Int` |
| `x` values as floats | `data : List Float` | element-wise `float ↔ Float` |
| `datetime_to_numeric(x.data, offset=epoch, unit="ns")` | `datetimeToFloat raw` | the unchanged datetime reduction, applied to the int buffer |
| `x.astype(float)` for `timedelta64[ns]` | `raw.map Float.ofInt` | per-element `int64 → float` cast |
| `to_floatable(x)` result values | `result : List Float` | element-wise `float ↔ Float` |

`Float.ofInt` is exact for the `int64` magnitudes a `timedelta64[ns]` buffer
holds (the only lossy case is `|n| > 2^53`, far outside fuzzed/realistic spans;
the not-a-time sentinel `int64.min` casts to its float value identically under
both numpy and `Float.ofInt`).

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The datetime reduction `datetime_to_numeric`
  appears identically in the spec helper (`coerceResult`) and the impl
  (`implementation_coerceToFloat`); the proof discharges the datetime branch by
  reflexivity (both sides are literally `datetimeToFloat x.raw`), consuming NO
  property of the opaque. It is therefore an **A-reference** (signature carried),
  not an A-consumed axiom, and there is no `_prop` for G-AX to check → **G-AX
  skips**.
- The changed branch (duration) is modeled deeply (`raw.map Float.ofInt`), so it
  is not a callee axiom either.
- `_ensure_numeric`'s `Dataset.map` / `isinstance(data, Dataset)` dispatch is
  unchanged plumbing applying `to_floatable` per variable; not separately
  modeled (orthogonal to the fix; each variable's coercion is exactly the modeled
  function).
- No flag dependencies: the branch is selected purely by `x.dtype.kind`.

## G-CONF fuzz seed

Pinned LCG seed: **6599** (see `conformance_check.py` `SEED`). Corpus: randomized
`ArrayView`s crossing all three kinds, with emphasis on the discriminating
category — duration arrays (`kind = duration`, random `int64` ns buffers incl.
negative and large magnitudes) — plus datetime and numeric controls, over ≥1e5
fuzzed inputs. The R/I shadow of `implementation_coerceToFloat` is diffed against
an in-process replica of the POST-PATCH `to_floatable` branch selection (the
datetime reduction modeled as the SAME opaque stand-in on both sides, since it is
unchanged and identical in spec and impl). Hand-picked edge cases pin the
discriminating clause: the F2P duration buffer `[1000,2000,3000]` → its float
cast, and a duration buffer must NOT be routed through the datetime reduction.
