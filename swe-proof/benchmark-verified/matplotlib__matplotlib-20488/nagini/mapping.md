# mapping.md — matplotlib__matplotlib-20488

Model ↔ repo symbol binding, type abstraction, and callee provenance. All
file:line references are at `base_commit`
`b7ce415c15eb39b026a097a2865da73fbcf15c9c`.

## Modeled function

| model symbol | repo symbol | repo location (base_commit) | role |
|---|---|---|---|
| `sanitized_lower_bound(is_log, s_vmin, eps)` | the LogNorm lower-bound guard inside `matplotlib.image._ImageBase._make_image` | `lib/matplotlib/image.py:534-537` (the `s_vmin, s_vmax = vrange` line and the `if isinstance(self.norm, mcolors.LogNorm): if s_vmin < 0: s_vmin = max(...)` block) | the single changed hunk: sanitise the lower bound `s_vmin` before it is fed to the active normalization |

The gold patch (the only hunk) replaces lines 535-537 with:

```python
if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0:
    # Don't give 0 or negative values to LogNorm
    s_vmin = np.finfo(scaled_dtype).eps
```

`_make_image` is large (`lib/matplotlib/image.py:307`); only the post-resample
vmin/vmax sanitisation hunk is touched, so only that hunk is modeled. The
surrounding resampling/scaling pipeline is irrelevant to the tested behavior and
is not modeled.

## Type abstraction (refinement carriers)

| repo reality | model carrier | justification |
|---|---|---|
| `isinstance(self.norm, mcolors.LogNorm)` — a runtime type test producing a bool | `is_log: bool` | the only property of `self.norm` the hunk consults is "is it a logarithmic normalization?"; that boolean is the faithful abstraction. The `isinstance` call itself is unchanged by the patch (it appears identically on both sides), so it is an `I` (identical) refinement of a boolean-valued condition. |
| `s_vmin` — a `numpy` float scalar unpacked from `vrange` (an `np.ndarray` of `scaled_dtype`) | `s_vmin: float` (interpreted real, `--float-encoding=real`) | the candidate lower bound is a finite real number; the tested behavior is a sign/zero comparison against it. Modeled directly as an interpreted real. The precondition `s_vmin <= 0.0 or s_vmin > 0.0` excludes NaN — faithful, since `vrange` arises from finite arithmetic on the autoscaled data range (`vmin/vmax`, `a_min/a_max` clipping), never NaN at this point. |
| `np.finfo(scaled_dtype).eps` — the smallest representable positive magnitude (machine epsilon) of the working float dtype (`np.float32` or `np.float64`) | `eps: float` with `Requires(eps > 0.0)` | `numpy.finfo(...).eps` is documented and observably a strictly positive constant for any floating dtype (`float32`: ~1.19e-7, `float64`: ~2.22e-16). Only its strict positivity is consumed; that is the weakest sufficient property. No `@ContractOnly` axiom is needed because the value enters the modeled function as a parameter constrained by `eps > 0.0` (its sole relevant property). Provenance below. |
| `max(s_vmin, np.finfo(...).eps)` (pre-patch only) | a real-number conditional `eps if s_vmin <= eps else s_vmin` | modeled directly over interpreted reals; appears only in `model_prepatch.py` to faithfully reproduce the buggy skeleton. |

## Callee / constant provenance

- `numpy.finfo(dtype).eps`: "The difference between 1.0 and the next smallest
  representable float larger than 1.0." Strictly positive for every floating
  dtype. Source/doc: numpy `numpy/core/getlimits.py` (`finfo` class, `eps`
  attribute); https://numpy.org/doc/stable/reference/generated/numpy.finfo.html .
  Only positivity is relied on; G-AX (`axiom_check.py`) executes the real
  `np.finfo(...).eps` for `float16/float32/float64/float128` and asserts each is
  strictly positive (boundary + the dtypes matplotlib actually selects in
  `_make_image`: `float32` and `float64`).
- `matplotlib.colors.LogNorm`: `lib/matplotlib/colors.py:1543` (`class LogNorm`).
  Its only relevance to the hunk is the `isinstance` test; modeled as the bool
  `is_log`. The patch does not change `LogNorm`; no axiom about it is needed.

## Flag dependencies

None. The behavior depends only on the bool `is_log`, the sign of `s_vmin`, and
the positivity of `eps`. No keyword-argument-dependent callee is axiomatized.
