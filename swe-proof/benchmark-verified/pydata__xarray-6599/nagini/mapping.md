# mapping.md — pydata__xarray-6599

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6bb2b855498b5c68d7cca8cceb710365d58e6048`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `xarray/core/computation.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `to_floatable(kind, values, reference)` | `to_floatable(x)` — the nested helper inside `_ensure_numeric`, `xarray/core/computation.py:1935` (body lines 1936-1944) | the modeled changed function: per-kind coercion of a variable's values to float |
| `elapsed_since(kind, values, reference)` *(axiom — A-consumed)* | `datetime_to_numeric` — `xarray/core/duck_array_ops.py:398`, called at `computation.py:1938` with `offset=np.datetime64("1970-01-01")`, `datetime_unit="ns"` | unchanged callee the timestamp branch invokes; the instant-relative measurement (domain: `kind == TIME_POINT` and NaT-free magnitudes — §3.1) |
| `well_defined_magnitudes(values)` *(pure predicate)* | the implicit domain of `datetime_to_numeric`'s measurement on `datetime64[ns]` (no `NaT`, i.e. no int64 magnitude `-2**63`) | pure spec: the per-element subtraction is the callee's value only on well-defined (non-`NaT`) magnitudes; referenced as an atom by both `elapsed_since`'s `Requires` and the caller precondition (§3.1) |
| `magnitude_read(values)` *(deep model — A-reference)* | `x.astype(float)` — the NEW duration branch added by the patch (`computation.py` post-patch `elif x.dtype.kind == "m": return x.astype(float)`) | pure spec: the direct float-magnitude read; the deep model of the changed/new operation, validated `magnitude_read == astype(float)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `kind` (`OTHER`/`TIME_POINT`/`TIME_SPAN`) | `x.dtype.kind` ∈ {numeric kinds, `"M"`, `"m"`} | pure spec: the value category that selects the conversion branch |
| `reference` | the ns-since-epoch magnitude of `offset=np.datetime64("1970-01-01")` (= 0) | pure spec: the reference instant subtracted by the measurement |

The pre-patch repo expression the change splits (for the refinement audit, not
referenced from the consumer spec view): the single guard `if x.dtype.kind in
"mM":` (`computation.py:1936`) that routed BOTH `"M"` (datetime) and `"m"`
(timedelta) into `datetime_to_numeric(...)`. The patch narrows that guard to
`== "M"` and adds the separate `elif x.dtype.kind == "m": return x.astype(float)`
branch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a variable's underlying values: a numpy array of `datetime64[ns]` / `timedelta64[ns]` / numeric dtype | `List[int]` of magnitudes in the base resolution (ns since epoch for timestamps; ns for durations; the value itself otherwise) | `array[k]` ↔ `values[k]`; `len(array)` ↔ `len(values)`; the spec is carried by `PSeq[int]` via `ToSeq` |
| `x.dtype.kind` (a one-character dtype-category code) | the `int` tag `kind` ∈ {`OTHER=0`, `TIME_POINT=1`, `TIME_SPAN=2`} | `"M"` ↔ `TIME_POINT`; `"m"` ↔ `TIME_SPAN`; every other kind ↔ `OTHER` |
| `float64` output of the conversion | `List[int]` (the tested magnitudes are exact integers, so the float values are integer-valued; the conversion under test is precision-independent — see refinement.md) | a float `f` that equals an integer `n` ↔ `n` |
| `x.copy(data=...)` wrapper (`computation.py:1937`) | identity on the value content (omitted) | `copy` only rebuilds the DataArray container around the new data; it does not change the numeric content the F2P test observes (`assert_allclose` compares values) |
| `offset=np.datetime64("1970-01-01")`, `datetime_unit="ns"` (`computation.py:1940-1941`) | `reference` = the offset's ns-since-epoch magnitude (= 0); base resolution ns | the call site fixes these constants; the axiom is stated for a general `reference` and `axiom_check.py` instantiates the real `1970-01-01`/`ns` call |

`float` is modeled as `int` here under §2 of the SPEC_GUIDE: the F2P timedelta
magnitudes (`1000, 2000, 3000` ns) and the P2P datetime magnitudes
(`0, 1e9, 2e9` ns) are exact integers, and the behaviour under test — *which
conversion is applied to each dtype kind, and whether the timestamp measurement
is even applicable to a duration* — is precision-independent. No rounding
distinguishes the buggy from the fixed behaviour; the bug is a type-applicability
error, not a precision loss.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `elapsed_since` axiom ↔ `datetime_to_numeric` (A-consumed)
**Callee:** `xarray.core.duck_array_ops.datetime_to_numeric(array, offset,
datetime_unit)` (`xarray/core/duck_array_ops.py:398-450`), invoked by the
timestamp branch as
`datetime_to_numeric(x.data, offset=np.datetime64("1970-01-01"), datetime_unit="ns")`.
Its relevant body:

```python
array = array - offset                       # line 434
...
elif array.dtype.kind in "mM":
    if datetime_unit:
        array = array / np.timedelta64(1, datetime_unit)   # -> ns count
    return np.where(isnull(array), np.nan, array.astype(dtype))   # float
```

For a `datetime64[ns]` input and the `1970-01-01` (epoch) offset, `array -
offset` is the timedelta `array - epoch`, and dividing by `np.timedelta64(1,
"ns")` yields the ns-since-epoch magnitude as float. Because the epoch offset's
ns magnitude is **0**, the result equals the raw ns magnitudes — i.e. per
element `result[k] == values[k] - reference` with `reference == 0`. The axiom
encodes exactly this per-element subtraction (the weakest contract the
timestamp branch needs), generalised to an arbitrary `reference`.

**Domain — NaT-free, exact-integer magnitudes (the second precondition).** The
per-element subtraction is the callee's value *only on well-defined magnitudes*.
`datetime_to_numeric`'s body terminates in
`np.where(isnull(array), np.nan, array.astype(dtype))` (line 450), and a
`datetime64[ns]` whose underlying int64 magnitude is the not-a-value sentinel
`-9223372036854775808` (= `-2**63`) *is* `NaT`: for it the callee returns
`np.nan`, **not** `values[k] - reference == -2**63`. So an unrestricted
`Ensures(result[k] == values[k] - reference)` would be **stronger than the real
callee** on the `-2**63` magnitude — a Requires-satisfying input the tag
constraint `kind == TIME_POINT` alone does not exclude (the G-AX panel defect).
The axiom therefore also carries `Requires(well_defined_magnitudes(values))`
(no element equals `-2**63`), restricting the domain to magnitudes on which the
subtraction is genuinely the callee's value. Within this domain the conversion
is also exact in the int model (`|magnitude| < 2**53`; the tested magnitudes are
small, see §2 / refinement.md §D). `axiom_check.py` (a) checks the subtraction on
the NaT-free domain incl. int64 extremes, and (b) `check_sentinel_excluded`
asserts the real callee really returns `nan` (deviates from the subtraction) at
`-2**63`, so the exclusion is **necessary, not gratuitous**. (NB: the *duration*
branch's `astype(float)` does NOT special-case NaT — it reinterprets the
magnitude — so `magnitude_read` stays the identity even at `-2**63`; the
NaT-exclusion is needed only for the timestamp measurement, hence the caller
guards it by `Implies(kind == TIME_POINT, ...)`.)

**Precondition (the load-bearing soundness fact):** `datetime_to_numeric` is
called with `offset` a `datetime64` *instant*; its first step `array - offset`
subtracts an instant. For a `timedelta64` (duration) input,
`timedelta64 - datetime64` is `numpy`'s `UFuncTypeError` ("ufunc 'subtract'
cannot use operands with types `<m8[ns]` and `<M8[D]`"; reproduced in the issue
thread). Hence the measurement is **defined only for timestamps**, which the
axiom records as `Requires(kind == TIME_POINT)`. `axiom_check.py` asserts the
real callee RAISES on a timedelta input called this way — making the
precondition honest, not artificially strong. Source:
https://github.com/pydata/xarray/blob/main/xarray/core/duck_array_ops.py
(`datetime_to_numeric`).

### 3.2 `magnitude_read` deep model ↔ `x.astype(float)` (A-reference)
**Callee:** the NEW duration branch the patch introduces, `x.astype(float)` on a
`timedelta64[ns]` array. `numpy`'s `timedelta64[ns].astype(float)` reinterprets
each duration as its integer count of nanoseconds, as a float — i.e. the
identity on the ns magnitudes. The changed/new operation is modeled **deeply**
by the `@Pure` `magnitude_read` (the identity on magnitudes) in the `pure`
region; there is **no consumed axiom** for it. The deep model is validated equal
to the real operation out-of-band by `axiom_check.py` (G-AX), which runs
`np.array(ns, dtype="timedelta64[ns]").astype(float)` and asserts it equals the
raw ns magnitudes. This is the single behavioural change the F2P test observes:
the duration `[1000, 2000, 3000]` ns becomes the floats `[1000.0, 2000.0,
3000.0]`, which `polyval` (coeffs `0 + 1·x`) returns verbatim.

**Soundness check (G-AX):** `axiom_check.py` runs the real `datetime_to_numeric`
(A-consumed) and the real `timedelta64.astype(float)` (A-reference) on boundary
inputs (empty, single, the F2P/P2P magnitudes, negatives, large, **int64
extremes** `+max`/`-2**63+1`) plus 20 000 randomized fuzz arrays (now **mixing
int64 extremes and the NaT sentinel** — the old band `[-10**15, 10**15]` could
never reach `-2**63`, which is why the original over-claim escaped), asserting:
(a) the datetime path equals the per-element subtraction with `reference == 0`
**on the NaT-free domain**; (b) the callee RAISES on a timedelta input
(precondition honesty); (c) the timedelta `astype(float)` equals the raw ns
magnitudes (the `magnitude_read` identity) **on the full int64 range incl. the
NaT sentinel** (sound there — the duration branch does not special-case NaT); and
(d) **`check_sentinel_excluded`** asserts the real callee returns `nan` (deviates
from the per-element subtraction) on the NaT sentinel `-2**63`, proving the
axiom's `Requires(well_defined_magnitudes(values))` domain exclusion is
**necessary** (the un-refined axiom over-claimed exactly there). It imports the
real callee from `xarray.core.duck_array_ops` plus `numpy`; nothing else. Exit 0
iff sound.

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (shadow; the
`elapsed_since` callee delegated to the real `datetime_to_numeric` with the
epoch offset) against the real patched per-variable coercion inside
`_ensure_numeric`, over the §2 bridge, on boundary arrays per kind plus
100000 fuzz arrays. **Pinned fuzz seed: 6599** (the instance number).
