# refinement.md — matplotlib__matplotlib-25122

Operation-by-operation correspondence between `model.py`'s implementation (the
`amplitude_loss_divisor` / `power_loss_divisor` impl regions and the deep folds
`signed_sum` / `square_sum`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (proof uses an axiom's Ensures),
**A-reference** (a deep model validated == the real callee by `axiom_check.py`
/ G-AX, NOT consumed), or **I** (identical concrete operation). Claim: any impl
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## Type refinements (whole-bundle)

| # | model.py | patch.diff / repo | tag | justification |
|---|---|---|---|---|
| R1 | `window: List[int]` | the 1-D real window array `window` | R | the array of `NFFT` real weights ↔ a `List` of weights; the per-element value type `float`→`int` is precision-free because the tested behaviour is a SIGN property of a reduction, not a magnitude/precision property (mapping.md §2). |
| R0 | `Requires(MustTerminate(2))` on both divisors | the real reductions `window.sum()` / `(window**2).sum()` always complete and deliver a value to `_spectral_helper` | R | total-correctness obligation. Nagini is a partial-correctness verifier by default, so without it a diverging impl (unbounded loop before the return) satisfies every `Ensures` vacuously while its faithful real patch would hang `psd()`/`specgram()` and resolve nothing. The obligation pins "the divisor is actually computed", which is trivially true of the real bounded ndarray reductions. The gold loops discharge it with `Invariant(MustTerminate(i + 1))` (measure `i` strictly decreases). |
| R2 | `signed_sum(ToSeq(window))` | `window.sum()` | R + A-reference | `ndarray.sum()` of a 1-D real array is the algebraic sum `Σ w_i`; modelled deeply as the front-recursive fold `signed_sum` and validated == real `numpy.array(w).sum()` by G-AX. |
| R3 | `square_sum(ToSeq(window))` | `(window**2).sum()` | R + A-reference | element-wise square then `ndarray.sum()` = `Σ w_i²`; modelled deeply as `square_sum`, validated == `(numpy.array(w)**2).sum()` by G-AX. |

## A. The amplitude normaliser — sites 1, 2, 4 (`magnitude`, `complex`, `psd` spectrum)

Gold hunks (`lib/matplotlib/mlab.py`):
```
398 - result = np.abs(result) / np.abs(window).sum()
398 + result = np.abs(result) / window.sum()
403 - result /= np.abs(window).sum()
403 + result /= window.sum()
430 - result /= np.abs(window).sum()**2
430 + result /= window.sum()**2
```
All three replace the divisor `Σ|w_i|` (the pre-patch `np.abs(window).sum()`)
with `Σ w_i` (`window.sum()`); site 4 squares it. Modelled by
`amplitude_loss_divisor`, whose postcondition pins the shared primitive.

| # | model.py impl op (`amplitude_loss_divisor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `window: List[int]` (read at `Acc(list_pred, 1/2)`) | the read-only `window` array | R | R1; the divisor reads the window, never mutates it (fractional permission, both Required and Ensured). |
| A2 | the running total `total`, accumulated over every weight with its own sign (`total = weight + total`), equal to `signed_sum(ToSeq(window))` | `window.sum()` | R + A-reference | the changed reduction is modelled DEEPLY: `signed_sum` (pure region) and the loop ARE the algebraic sum. No consumed `window_sum` axiom; G-AX validates `signed_sum == real ndarray.sum()` (R2). |
| A3 | postcondition `Result() == signed_sum(ToSeq(window))` | the divisor value entering `/ window.sum()` (sites 1,2) and `/ window.sum()**2` (site 4, squared by the caller) | R + I | the spec pins the divisor to the signed fold; site 4's squaring is `divisor*divisor` in `_spectral_helper`, an identical concrete op applied to the verified divisor. A wrong `Σ|w|` divisor differs ⇒ its square differs (for sign-mixed windows). |

The discriminating content — the divisor is `Σ w_i` (sign-respecting), NOT
`Σ |w_i|` — lives in `signed_sum` (model) ⇔ `window.sum()` vs `np.abs(window).sum()`
(real). The pre-patch reading is `magnitude_sum` (`Σ|w_i|`);
`model_prepatch.py` reproduces it (`total = magnitude(weight) + total`) and
**fails** the loop invariant `total == signed_sum(ToSeq(window).drop(i))` — the
spec sensing the bug (G-DIFF).

## B. The power normaliser — site 3 (`psd` density)

Gold hunk:
```
427 - result /= (np.abs(window)**2).sum()
427 + result /= (window**2).sum()
```

| # | model.py construct (`power_loss_divisor`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | running total of squares `total = weight*weight + total`, equal to `square_sum(ToSeq(window))` | `(window**2).sum()` | R + A-reference | R3; the squared-weight reduction modelled deeply as `square_sum`, validated == `(numpy.array(w)**2).sum()` by G-AX. |
| B2 | postcondition `Result() == square_sum(ToSeq(window))` | the divisor value entering `/ (window**2).sum()` | R + I | pins the divisor to the squared fold. |
| B3 | postcondition `square_sum == magnitude_square_sum` (lemma `squares_are_sign_blind`) | the OBSERVATION that the `427` edit `(np.abs(window)**2).sum()` → `(window**2).sum()` is a no-op | I | squaring is sign-blind, so `Σ|w_i|² ≡ Σw_i²`; the gold edit at site 3 cannot change any output. This is why site 3 has NO failing prepatch (its prepatch impl, using `magnitude(weight)*magnitude(weight)`, would still verify against the byte-identical spec — the spec correctly does NOT see a non-existent behaviour change). The lemma documents this and keeps the spec faithful to the full hunk. |

Why no separate failing `model_prepatch` for site B/site 3: the change there is
provably behaviour-preserving (B3). A `model_prepatch` is required only per
*independently-observable fixed behaviour* (G-DIFF); site 3 fixes nothing
observable, so reverting it yields a verifying skeleton — which is the *correct*
G-DIFF outcome and is documented rather than forced to fail. The single
`model_prepatch.py` exercises the amplitude site (A), which is the behaviour the
F2P flattop test observes.

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The genuinely-changed operation — the
window reduction `Σ|w| → Σw` — is modelled **deeply** (the spelled-out folds
`signed_sum` / `square_sum` consumed in the contracted functions), NOT hidden
behind an axiom about the function under change. There is NO consumed
`@ContractOnly` axiom; `numpy`'s `ndarray.sum` / `np.abs` appear only as the
**A-reference** callees G-AX validates the deep folds against.

## D. verify(model) ⇒ resolved

`amplitude_loss_divisor` verifies only if its result equals the signed fold
`signed_sum(window)` (A3), which by R/A-reference equals the real
`window.sum()`; the spectrum branch squares it, giving `window.sum()**2` (gold
site 4), and the magnitude/complex branches divide by it (gold sites 1,2). A
prepatch returning `Σ|w|` fails the invariant (G-DIFF). `power_loss_divisor`
verifies only with `square_sum(window) == (window**2).sum()` (B1) and pins the
site-3 no-op (B3). Therefore a model satisfying this spec, refined by the map,
is the gold patch up to type refinement and G-AX-validated reductions — and the
gold patch resolves (G-RESOLVE). The two trust points (PLAN §1.1): reduction
soundness (G-AX) and refinement fidelity (this document, G-EQ).
