# mapping.md — pydata__xarray-6599

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6bb2b855498b5c68d7cca8cceb710365d58e6048`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep-model reference.

Repo file under change: `xarray/core/computation.py` (the nested helper
`to_floatable` inside `_ensure_numeric`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `toNumeric (t : TypedArr)` | `to_floatable(x)` — `xarray/core/computation.py:1935` (nested in `_ensure_numeric`, `computation.py:1920`) | the modeled changed function: maps one array to its floatable numeric form |
| `Kind` (`.datetime`/`.duration`/`.numeric`) | `x.dtype.kind` — the numpy dtype-kind char: `"M"` (datetime64), `"m"` (timedelta64), anything else | the discriminant the fix dispatches on |
| `missingCount` (= −2⁶³) | `np.datetime64("NaT")` / `np.timedelta64("NaT")` — numpy's reserved int64-min carrier value for a missing time value | the one reserved count in the int64 carrier |
| `NumVal` (`.num n` / `.nan`) | a `np.float64` result value: an exact integer-valued float, or `nan` (what a NaT datetime converts to) | the converted-value domain |
| `epochCount (t)` *(deep model — A-reference)* | `datetime_to_numeric(x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns")` — `xarray/core/duck_array_ops.py:388` (called at `computation.py:1938` post-patch) | unchanged callee: re-expresses a datetime array as an ns count relative to a reference epoch; maps NaT → nan |
| `durationCast (t)` *(deep model — A-reference)* | `x.astype(float)` — numpy ndarray method (called at `computation.py:1947` post-patch) | unchanged callee: direct float cast of a timedelta array to its ns count (NO NaT special-case: the reserved count comes through as its numeric value) |

The pre-patch code routes BOTH time kinds through the single test
`x.dtype.kind in "mM"` → `datetime_to_numeric(...)`; the post-patch code splits
them (`== "M"` → datetime path, `elif == "m"` → `astype(float)`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `DataArray` `x` whose `.dtype.kind` is observed | `TypedArr` (`kind`, `raw`) | `x.dtype.kind == "M"` ↔ `.datetime`; `== "m"` ↔ `.duration`; else ↔ `.numeric` |
| the array's underlying integer carrier `x.data` | `raw : Array Int` | for `M`/`m` kinds, the int64 view of the ns counts: `x.data.astype("int64")` ↔ `t.raw` (NaT is the reserved count `missingCount` = int64 min = −2⁶³); for numeric, the int-valued payload |
| the floatable result `to_floatable(x)` returns | `Except ConvErr (Array NumVal)` | `.ok r` ↔ a returned DataArray whose float values equal `r` elementwise (`NumVal.num n` ↔ the exact float image of `n`; `NumVal.nan` ↔ `np.nan`, compared position-wise with `equal_nan`); `.error .illTypedForDuration` ↔ the `_UFuncBinaryResolutionError` raised when a timedelta array is fed to the epoch path |
| `np.float64` result values | `NumVal` (`.num` over `Int`, order-/value-exact, plus `.nan`) | the F2P test inputs are exact integers (ns counts) whose float images are exact; modeling the int carrier captures the observed values without IEEE rounding (SPEC_GUIDE §2: model order/value-only floats with the exact carrier, not `Float`). The one non-integer float the conversion can produce — the `nan` a NaT datetime maps to — is modeled explicitly as `NumVal.nan` |

Modeling the carrier as `Array Int` is sound here because the only observation
the F2P `test_polyval[timedelta-False]` makes is that the timedelta coordinate's
ns counts arrive as their exact float values (`[1000.0, 2000.0, 3000.0]` from
`timedelta64[ns]` counts `[1000, 2000, 3000]`), with no rounding.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

Both unchanged callees are modeled **deeply** (spelled out in the `pure`
region), so each is an **A-reference** validated `== real callee` by
`axiom_check.py`; there is **no consumed module-level `axiom`** (SPEC_GUIDE §3,
directive 7 — no dead axioms).

### 3.1 `epochCount` deep model ↔ `datetime_to_numeric(..., offset="1970-01-01", datetime_unit="ns")` (A-reference)
**Callee:** `xarray.core.duck_array_ops.datetime_to_numeric`. With
`offset=np.datetime64("1970-01-01")` and `datetime_unit="ns"`, on a
`datetime64[ns]` array it computes `(array - offset) / np.timedelta64(1, "ns")`
as float — i.e. exactly the int64 ns-since-epoch count cast to float
(`duck_array_ops.py:434,448-450`) — **except a NaT element (the reserved
int64-min count): `NaT - offset = NaT`, and the division yields `nan`.** Hence
`epochCount t = .ok (t.raw.map (missing → .nan, else .num))` on the datetime
kind. **It is undefined on a duration array:**
`array - offset` subtracts a `datetime64[D]` offset from a `timedelta64[ns]`
array, which numpy rejects with `_UFuncBinaryResolutionError` (witnessed in the
issue's `hints_text` traceback). This is exactly the pre-patch bug — modeled as
`epochCount` returning `.error .illTypedForDuration` on the duration kind.

### 3.2 `durationCast` deep model ↔ `x.astype(float)` (A-reference)
**Callee:** the numpy ndarray `.astype(float)` method on a `timedelta64[ns]`
array. `timedelta64[ns].astype(float)` yields the int64 ns count as float
exactly (e.g. `array([1000,2000,3000], "timedelta64[ns]").astype(float)
== [1000., 2000., 3000.]`). **It does NOT special-case NaT: the reserved
int64-min count comes through as `float(-2**63)` = −9.223372036854776e18
(verified in-container on this instance's numpy 1.23.0).** Hence
`durationCast t = t.raw.map NumVal.num` (the plain ns counts, no `.nan` leaf).

**Soundness check (G-AX):** `axiom_check.py` runs the REAL callees in-container
on boundary + fuzzed `datetime64[ns]` / `timedelta64[ns]` / numeric arrays —
including NaT-bearing ones (the reserved count in ~10% of fuzz positions plus
dedicated boundary rows) — asserting (a) `datetime_to_numeric(v,
offset=1970-01-01, datetime_unit="ns") == epochCount` on datetimes (nan
positions coincide, `equal_nan` compare); (b) `x.astype(float) == durationCast`
on timedeltas (incl. the un-special-cased NaT count); (c) feeding a timedelta
array to the epoch path raises (validating `epochCount`'s `.error` leaf).
Imports only `numpy` + the repo's `datetime_to_numeric` — the same callees the
gold patch uses. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`6599`** so the
consumer-side verdict (§11.3) is reproducible. The shadow it builds
transliterates the impl's **kind-routing** (the R/I content — the changed
dispatch) and leaves the two A-reference callees as the REAL repo callees
(`datetime_to_numeric` for the datetime branch, `.astype(float)` for the
duration branch). It compares against `patch.diff`'s behaviour (the patched
`to_floatable`) over ≥10⁵ fuzzed arrays across the three kinds, including
NaT-bearing arrays (the reserved int64-min count), with an `equal_nan`
elementwise compare (nan positions must coincide, everything else exactly
equal). Exit 0 iff zero disagreements.
