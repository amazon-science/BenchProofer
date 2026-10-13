# mapping.md — matplotlib__matplotlib-25122

## Instance
- repo: matplotlib/matplotlib
- base_commit: 5ec2bd279729ff534719b8bf238dbbca907b93c5
- changed function: `_spectral_helper`
- file: `lib/matplotlib/mlab.py`

## Symbol binding (file:line @ base_commit)

| Python symbol | location | role |
|---|---|---|
| `result = np.abs(result) / np.abs(window).sum()` | `lib/matplotlib/mlab.py:396` | `magnitude` mode: normalize by the window-sum factor (PRE-PATCH: sum of magnitudes) |
| `result /= np.abs(window).sum()` | `lib/matplotlib/mlab.py:402` | `complex` mode: normalize by the window-sum factor (PRE-PATCH: sum of magnitudes) |
| `result /= (np.abs(window)**2).sum()` | `lib/matplotlib/mlab.py:427` | `psd` mode, `scale_by_freq=True`: normalize by sum of squared window samples |
| `result /= np.abs(window).sum()**2` | `lib/matplotlib/mlab.py:430` | `psd` mode, `scale_by_freq=False`: normalize by the squared window-sum factor (PRE-PATCH: squared sum of magnitudes) |
| `window` | parameter / `window(np.ones(NFFT, x.dtype))` (l.375) | the 1-D analysis window applied per segment; a real-valued array that may contain NEGATIVE samples (e.g. `flattop`) |
| `mode`, `scale_by_freq` | parameters | select which normalization branch (and divisor) is applied |

## Behaviour modeled

`_spectral_helper` divides the (already FFT'd / detrended) `result` by a
*window-correction factor* built from the analysis `window`, to compensate for
the energy/amplitude lost to windowing (Bendat & Piersol §11.5.2). The factor
depends on `mode` (and, for `psd`, on `scale_by_freq`):

| mode | scale_by_freq | divisor (CORRECT / fix) |
|---|---|---|
| `magnitude` | – | `Σ wᵢ` |
| `complex`   | – | `Σ wᵢ` |
| `psd`       | True  | `Σ wᵢ²` |
| `psd`       | False | `(Σ wᵢ)²` |
| `angle` / `phase` | – | `1` (no window correction applied) |

The reported bug: the **linear** factor was computed as `Σ|wᵢ|`
(`np.abs(window).sum()`) rather than `Σ wᵢ` (`window.sum()`). For a window with
negative samples these differ, giving a wrong result for the `magnitude`,
`complex`, and `psd`+`scale_by_freq=False` branches. The fix drops the absolute
value, computing the plain signed sum.

The `psd`+`scale_by_freq=True` branch divides by `Σ wᵢ²`. The pre-patch code
wrote this as `(Σ|wᵢ|²)`, which is numerically identical to `Σ wᵢ²` for real
windows (|w|² = w²), so that branch's BEHAVIOUR is unchanged by the patch; it is
modeled deeply as `Σ wᵢ²` and is not a discriminator.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| real window samples `window` (`np.ndarray`, may be negative) | `window : List Rat` | element-wise; exact rationals stand in for the real samples — the fix is purely about SIGN handling (negatives), so kernel-opaque `Float` is avoided and `Rat` is exact (DECISIONS.md: order/sign-only float fix ⇒ exact Rat) |
| `mode` string in `{magnitude, complex, psd, angle, phase}` | `Mode` inductive (`magnitude`/`complex`/`psd`/`angle`/`phase`) | one constructor per spectrum mode |
| `scale_by_freq` bool | `scaleByFreq : Bool` | identity |
| `window.sum()` | `window.sum` (`List.sum`) | front fold over the same elements |
| `(window**2).sum()` | `(window.map (fun w => w * w)).sum` | element-wise square then fold |
| `window.sum()**2` | `window.sum * window.sum` | square of the fold |
| the window-correction divisor | `result : Rat` (output of `windowCorrectionFactor`) | the value `result` is divided by |

## Callee provenance + flag deps
None. The modeled operation is the pure computation of the divisor from the
window samples (a sum / sum-of-squares reduction, modeled deeply as a `for`-loop
fold). No unchanged repo callee is consumed by the proof, so there are no
`opaque` declarations and no `axiom _prop` contracts. `np.fft.fft`, `_stride_windows`,
`detrend`, `np.conj`, `np.abs(result)`, `np.angle` are all DOWNSTREAM of / orthogonal
to the modeled boundary (they act on `result`, not on the window factor) and are
not part of the changed computation, so they are not modeled.

Flag dependency: the divisor branch is selected by `mode` and `scale_by_freq`;
G-CONF fuzzes all `(mode, scale_by_freq)` combinations.

## G-CONF fuzz seed
`seed = 25122` (pinned; used by conformance_check.py).
