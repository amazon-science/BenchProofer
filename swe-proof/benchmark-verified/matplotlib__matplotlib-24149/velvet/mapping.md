# mapping.md — matplotlib__matplotlib-24149

Cold spec. Provenance: `spec_provenance: "cold"` (meta.json). Derived only from
`problem_statement`, the gold `patch`, and the repo source at
`base_commit = af39f1edffcd828f05cfdd04f2e59506bb4a27bc`.

## 1. Symbol binding (file:line @ base_commit)

| Lean symbol | repo symbol | file @ base_commit | role |
|---|---|---|---|
| `selectReference` | the per-sequence element-extraction step inside `Axes._convert_dx` | `lib/matplotlib/axes/_axes.py:2170-2189` | **function under spec** (the changed function; the modeled region is the `try … except` element-extraction block) |
| `firstFinite xs` (deep model `xs.find? isFiniteVal`) | `matplotlib.cbook._safe_first_finite(obj, skip_nonfinite=True)` | `lib/matplotlib/cbook/__init__.py:1709-1749` | **A-reference** callee (unchanged; deep-modeled, G-AX-validated) |
| `xs.headD default` | `matplotlib.cbook.safe_first_element(obj)` ( = `_safe_first_finite(obj, skip_nonfinite=False)`) | `lib/matplotlib/cbook/__init__.py:1699-1706,1728-1741` | **A-reference** callee (unchanged; deep-modeled, G-AX-validated) |
| `isFiniteVal x` ( = `x.isFinite`) | `safe_isfinite` (the nested predicate inside `_safe_first_finite`) applied to a scalar float, i.e. `np.isfinite(val)` | `lib/matplotlib/cbook/__init__.py:1719-1727` | **A-reference** predicate (G-AX-validated == `np.isfinite` on scalar floats) |
| `ExtractErr.noFiniteFound` | the `StopIteration` raised by `next(val for val in obj if safe_isfinite(val))` when no element is finite | `lib/matplotlib/cbook/__init__.py:1749` | exception kind (modeled as an `Except` error leg) |

## 2. The Lean ↔ Python type bijection (used by G-CONF and G-AX)

The bug and the F2P test (`test_bar_all_nan`) exercise the float-array path:
`ax.bar([np.nan], [np.nan])` makes both `x0` and `xconv` be length-1 sequences
of floats. The modeled domain is therefore:

| Lean | Python | bijection |
|---|---|---|
| `xs : List Float` | the sequence argument `obj` to the extraction (`x0`, resp. `xconv`): a finite-length, index/iter-able, **non-iterator**, **non-`np.flatiter`** sequence of scalar real (float) elements | `xs[i]` ↔ `obj[i]`; `xs.length` ↔ `len(obj)`; element ↔ IEEE-754 double |
| `isFiniteVal x : Bool` | `safe_isfinite(val)` for a scalar float `val` = `np.isfinite(val)` | NaN, +inf, −inf ↦ `false`; every other double ↦ `true` |
| `Except.ok v : Except ExtractErr Float` | normal return of the extraction (`x0`/`x` bound to a scalar) | `v` ↔ the returned double |
| `Except.error ExtractErr.noFiniteFound` | the `StopIteration` that escapes `_convert_dx` (caught by neither inner `(TypeError, IndexError, KeyError)` nor outer `(ValueError, TypeError, AttributeError)`) → crash | — |

**Modeled-domain pin (why the simple path is faithful).** The extraction is only
reached when `xconv.size != 0` (the `if xconv.size == 0: return convert(dx)`
guard at line 2168 precedes it) ⇒ the sequence is non-empty ⇒ `require xs ≠ []`.
For a float `ndarray`/`list`, `_safe_first_finite` takes the final `else` branch
(`next(val for val in obj if safe_isfinite(val))`); the iterator / `np.flatiter`
branches (lines 1742-1747) are out of the modeled domain and are recorded here
as excluded (G-AX fuzzes only the in-domain float-sequence case).

## 3. Callee provenance + flag dependencies

- `_safe_first_finite` (A-reference): unchanged by the patch. Called with the
  **default `skip_nonfinite=True`** at both extraction sites. Under that flag, on
  a non-empty float sequence it returns the first element with `np.isfinite`
  true, and raises `StopIteration` if none is finite. Deep model: `xs.find?
  isFiniteVal` returns `some v` (the first finite element) or `none` (⇒ would
  raise). **Flag dependency:** the `skip_nonfinite=True` configuration is what
  makes this "first *finite*"; G-AX must call it with the default flag.
- `safe_first_element` (A-reference): unchanged by the patch. `=
  _safe_first_finite(obj, skip_nonfinite=False)`. On a non-empty sequence it
  returns `next(iter(obj))` = the first element unconditionally (finite or not).
  Deep model: `xs.headD default` (head when non-empty). **Flag dependency:**
  `skip_nonfinite=False`; G-AX must call `safe_first_element` (or the explicit
  `skip_nonfinite=False`), NOT the default.
- `isFiniteVal` (A-reference predicate): `np.isfinite` on a scalar float. Lean
  `Float.isFinite` (not-NaN ∧ not-±inf). G-AX checks agreement on fuzzed doubles
  incl. the sentinels NaN, +inf, −inf, 0.0, ±max.

## 4. G-CONF fuzz seed

Pinned seed: **24149**. Conformance fuzzes `List Float` sequences (lengths
1..8; element pool = {finite randoms, NaN, +inf, −inf, 0.0, ±1.0, ±1e308})
biased to include all-non-finite sequences (the discriminating case) and
mixed-position-of-first-finite sequences. ≥10⁵ inputs; exit 0 iff the R/I shadow
of the `do` block agrees with `patch.diff` behaviour on every input.
