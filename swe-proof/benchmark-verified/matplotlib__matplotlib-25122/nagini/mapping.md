# mapping.md — matplotlib__matplotlib-25122

Binds every model.py symbol to the real repo symbol it abstracts, states the
type abstraction, and cites callee provenance (file:line at `base_commit`
`5ec2bd279729ff534719b8bf238dbbca907b93c5`). The changed function is
`matplotlib.mlab._spectral_helper` (`lib/matplotlib/mlab.py:291`); the patched
hunks are the window-normalisation divisions inside it.

## 1. The patched sites (all in `_spectral_helper`, `lib/matplotlib/mlab.py`)

| site | mode / branch | base line | pre-patch | post-patch | behaviour change? |
|---|---|---|---|---|---|
| 1 | `magnitude` | 398 | `np.abs(result) / np.abs(window).sum()` | `np.abs(result) / window.sum()` | YES (divisor = Σ\|w\| → Σw) |
| 2 | `complex` | 403 | `result /= np.abs(window).sum()` | `result /= window.sum()` | YES (divisor = Σ\|w\| → Σw) |
| 3 | `psd` density (`scale_by_freq`) | 427 | `result /= (np.abs(window)**2).sum()` | `result /= (window**2).sum()` | NO — `Σ\|w\|² ≡ Σw²` pointwise (cosmetic) |
| 4 | `psd` spectrum (not `scale_by_freq`) | 430 | `result /= np.abs(window).sum()**2` | `result /= window.sum()**2` | YES (divisor = (Σ\|w\|)² → (Σw)²) |

Sites 1, 2, 4 share ONE changed primitive: the amplitude normaliser is the
**signed window sum** `Σ w_i` (the fix), not the **absolute-value sum**
`Σ |w_i|` (the bug). Site 4 squares it. Site 3 is the power normaliser
`Σ w_i²`, which is sign-blind (`|w_i|² = w_i²`), so the gold edit there is a
pure no-op refactor — it cannot change any output and is not the locus of the
failing test.

The F2P test `TestSpectral.test_psd_window_flattop`
(`lib/matplotlib/tests/test_mlab.py`, added by `test_patch`) feeds a `flattop`
window (which has negative weights) and asserts
`spec*win.sum()**2 ≈ spec_a*Fs*(win**2).sum()` where `spec` comes from the
spectrum branch (site 4) and `spec_a` from the density branch (site 3). With the
fix both sides reduce to the same raw value; pre-patch, `spec` carries the wrong
`(Σ|w|)²` divisor and the identity breaks — exactly the negative-weight case.

## 2. Type abstraction (model.py ↔ repo)

| model.py | repo reality | abstraction |
|---|---|---|
| `amplitude_loss_divisor(window: List[int]) -> int` | the amplitude normaliser `window.sum()` over the 1-D real window array `window` (sites 1, 2; squared at site 4) | the window array of `NFFT` real weights ↔ `List[int]` of weights; `window.sum()` ↔ `signed_sum(ToSeq(window))` |
| `power_loss_divisor(window: List[int]) -> int` | the power normaliser `(window**2).sum()` (site 3) | same window ↔ `List[int]`; `(window**2).sum()` ↔ `square_sum(ToSeq(window))` |
| `signed_sum` / `square_sum` (pure folds) | `ndarray.sum()` of `window` resp. `window**2` | spelled-out front-recursive folds; deep models, validated == the real reductions by `axiom_check.py` (A-reference) |
| `magnitude` / `magnitude_sum` / `magnitude_square_sum` | `np.abs(window)` then `.sum()` resp. `(np.abs(window)**2).sum()` (the pre-patch readings) | the bug's quantities; `magnitude_sum` is what the prepatch impl computes; `magnitude_square_sum` documents site 3's no-op via `squares_are_sign_blind` |

**Termination obligation (total correctness).** Both contracted divisors carry
`Requires(MustTerminate(2))`: the real reductions `window.sum()` /
`(window**2).sum()` are bounded single passes over the window that always
complete and deliver their value to `_spectral_helper`. Nagini verifies
partial correctness by default, so without the obligation a non-terminating
implementation (an unbounded loop before the return) would satisfy the value
postconditions vacuously while its faithful real patch would hang
`psd()`/`specgram()` — verifying but not resolving. The gold loops discharge
the obligation with `Invariant(MustTerminate(i + 1))` (measure `i` strictly
decreases each iteration).

**`float` → `int` refinement (precision-free).** Window weights are real
(`float`) in the repo. The tested distinction is purely about **sign handling
in a reduction**: whether each weight enters the running total with its sign
(`Σ w_i`, correct) or by its magnitude (`Σ |w_i|`, buggy). This disagreement is
caused solely by the *presence of negative weights*, never by the weights'
magnitudes or floating-point precision — for any window with a negative weight,
`Σ |w_i| > |Σ w_i|`, regardless of the exact reals. Signed integers already
carry both signs, so they are a faithful, precision-free carrier; the bug is
reproduced identically. (See `refinement.md` rows R1–R3 and SPEC_GUIDE §2
"float where the bug is NOT about precision → int, only if the tested behaviour
is precision-independent".) `float_encoding` is therefore `null`; this is NOT a
precision bug.

## 3. Callee provenance (deep-model references — A-reference, validated by G-AX)

There are NO consumed `@ContractOnly` axioms. The reductions the fix uses are
the changed operations themselves and are modelled DEEPLY as folds; each is
validated **== its real numpy reduction** by `axiom_check.py` (G-AX), not
consumed as an axiom.

### 3.1 `signed_sum(w)` ↔ `numpy.ndarray.sum()` of the window
- Real callee: `numpy.ndarray.sum(axis=None)` — the algebraic sum of all
  elements (NumPy reference, `numpy.sum`: "Sum of array elements over a given
  axis."). For a 1-D real array this is `Σ_i w_i` with each element's sign.
- Provenance in source: `lib/matplotlib/mlab.py:398,403,430` call `window.sum()`
  (post-patch); the pre-patch called `np.abs(window).sum()`.
- Encoded property (weakest needed): `signed_sum(w) = Σ_i w_i`, front-recursive.
- G-AX: `axiom_check.py` runs the real `numpy.array(w).sum()` on boundary +
  fuzz integer windows (incl. negative + sign-mixed) and asserts it equals
  `signed_sum`.

### 3.2 `square_sum(w)` ↔ `(numpy_window ** 2).sum()`
- Real callee: element-wise square then `ndarray.sum()`.
- Provenance: `lib/matplotlib/mlab.py:427` `(window**2).sum()` (post-patch).
- Encoded property: `square_sum(w) = Σ_i w_i²`.
- G-AX: validated == `(numpy.array(w)**2).sum()`.

### 3.3 `magnitude` / `magnitude_sum` / `magnitude_square_sum` ↔ `np.abs(window)…`
- Real callee: `numpy.absolute` (`np.abs`), the element-wise magnitude, then
  `.sum()` resp. squared-then-`.sum()` (NumPy reference, `numpy.absolute`:
  "Calculate the absolute value element-wise.").
- Provenance (pre-patch readings): `lib/matplotlib/mlab.py:398,403,430`
  (`np.abs(window).sum()`), `:427` (`(np.abs(window)**2).sum()`).
- Encoded property: `magnitude(x)=|x|`; `magnitude_sum(w)=Σ|w_i|`;
  `magnitude_square_sum(w)=Σ|w_i|²`.
- G-AX: validated == `numpy.abs(...)…`; AND the no-op identity
  `square_sum == magnitude_square_sum` (site 3) is checked to hold on all fuzz
  inputs (it is the lemma `squares_are_sign_blind`).

No flag dependencies (no `quote=`-style configuration): `ndarray.sum()` and
`np.abs` are called with their defaults. `axiom_check.py` uses NumPy as shipped
in the evaluation image.

## 4. Conformance (G-CONF)

`conformance_check.py` runs the contract-stripped impl regions (shadow)
differentially against the real patched `_spectral_helper` (oracle) via an
impulse-response readout of all four normalisation sites, on >= 1e5
Requires-satisfying windows (boundary + exhaustive sign/value sweeps +
100000 fuzz). **Pinned fuzz seed: 25122** (the instance number).
