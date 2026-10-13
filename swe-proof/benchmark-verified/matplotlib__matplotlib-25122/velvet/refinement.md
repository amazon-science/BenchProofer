# refinement.md — matplotlib__matplotlib-25122

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `windowSum` `do` block and the deep `listSum` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses the axiom's `ensures`,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so the `while` fold
carries a `decreasing i` measure and a verifying impl must TERMINATE and
produce a value satisfying `WithinRoundoff ulp coeffs`. (An earlier revision used partial correctness, which
a same-spec diverging impl — a `while true` loop with a trivial invariant —
vacuously satisfied; the G-PANEL-1 audit found that counterexample class, and
total semantics excludes it. The real reduction trivially terminates: `numpy`'s
`window.sum()` is a bounded fold over a finite array.)

## A. The window-normalization site — `_spectral_helper` (`lib/matplotlib/mlab.py`)

Gold hunks (four sites, one observable behaviour):
```
- result = np.abs(result) / np.abs(window).sum()      # mode == 'magnitude'
+ result = np.abs(result) / window.sum()
- result /= np.abs(window).sum()                       # mode == 'complex'
+ result /= window.sum()
- result /= (np.abs(window)**2).sum()                  # psd, scale_by_freq
+ result /= (window**2).sum()
- result /= np.abs(window).sum()**2                    # psd, not scale_by_freq
+ result /= window.sum()**2
```

| # | Solution.lean impl op (`windowSum`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | `require RealArith ulp maxMag`, `require Accumulable maxMag ulp coeffs` | the arithmetic `numpy` carries the reduction in, and the sequences it can carry | R | `numpy` reduces in the ARRAY's own dtype and `_spectral_helper` propagates the caller's dtype unnormalized (`mlab.py:377`), so `(ulp, maxMag)` is an argument, not a constant. `RealArith` admits the four `(2⁻ᵖ, 2ᵉ − 2ᵉ⁻ᵖ)` pairs `np.finfo` reports for `float16/float32/float64/longdouble`, pairing each rounding with the range of the format that has it; `Accumulable` (`Σ\|wᵢ\| + n·2·ulp·Σ\|wᵢ\| ≤ maxMag`) drops the sequences whose accumulation saturates to `±inf`, a **patch-invariant** class (mapping.md §3.1). Neither is a disjunction the impl may choose between: both are hypotheses on the arguments, so a verifying impl owes the postcondition at ALL four arithmetics. |
| A1 | parameter `coeffs : List Rat` | `window` (1-D real `ndarray`) | R | `ndarray` ↔ `List Rat`, order- and length-preserving (mapping.md §2). G-CONF bridges via `w[k] ↔ coeffs[k]`. Read-only — not `mut` (directive 5). |
| A2 | result satisfies `WithinRoundoff ulp coeffs out`: it agrees with the order-preserving **signed** total `listSum coeffs` to within `roundoffBound ulp coeffs`; the frozen impl discharges this by computing the exact total with the backward `while` fold | `window.sum()` (the patched normalization total) | A-reference + I | the changed primitive is modeled **deeply**: `listSum`/`magSum`/`roundoffBound` (pure region) and the verified loop. No consumed `npSum` axiom. The fold ops (`+`, the loop) are **I** (concrete, transliterated by G-CONF); that the real `numpy` `window.sum()` SATISFIES this postcondition is the **A-reference** G-AX validates. It is a tolerance and not an equality because the reduction accumulates with rounding — asserting exactness would describe a function the repo does not contain. The tolerance is parameterized by `ulp` rather than frozen at `2⁻⁵³` because the reduction accumulates in the ARRAY'S OWN dtype, which `_spectral_helper` inherits from the caller unnormalized (`window = window(np.ones(NFFT, x.dtype))`, `mlab.py:377`); a frozen binary64 tolerance is false of the real callee on a `float32` input (mapping.md §3.1). And `ulp` ranges over `RealArith`'s four format pairs rather than over every positive rational, because an unconstrained `ulp` could be driven toward `0` and the postcondition would collapse back to the exactness this same section measures to be FALSE of the callee (A0, mapping.md §3.1). |
| A3 | (no node) — `np.abs(window)` is absent from the impl | the **removed** `np.abs(...)` wrapper | I (deletion) | the fix is the deletion of the elementwise magnitude before the reduction. Modeled as its absence: `listSum` sums the signed coefficients. There is NO axiom about `np.abs` (directive 7: never pin an op the patch removes). |

Discriminating content of the change — for a window with negative coefficients,
`Σ wᵢ ≠ Σ |wᵢ|` — lives in `windowSum`'s postcondition `WithinRoundoff ulp coeffs
out` (model) ⇔ the patched `window.sum()` (real). The pre-patch normalized by
`np.abs(window).sum() = Σ|wᵢ|`; `Solution_prepatch.lean` reproduces that
(magnitude fold) and **fails** the invariant `acc = listSum (coeffs.drop i)`
(G-DIFF), because on any negative coefficient `|x| + … ≠ x + …`.

The tolerance cannot absorb that difference, which is what keeps the refutation
sound: the accuracy bound is `n · 2·ulp · Σ|wᵢ|`, while the signed/magnitude gap
is `2 · Σ_{wᵢ<0} |wᵢ|` — at `ulp = 2⁻⁵³`, the binary64 instantiation, the gap
exceeds the bound by 10 to 13 orders of magnitude on the discriminating windows
(measured on scipy `flattop`: gap/bound ≈ 5.1e13 at n=8, 1.3e12 at n=512, 3.9e10
at n=16384). The margin shrinks as `ulp` loosens; at `ulp = 2⁻¹¹` (`float16`) and
`n ≥ 512` it closes (mapping.md §3.1 records the measurements), which is a true
property of a `float16` accumulator and not a hole: `RealArith` is a hypothesis on
the arguments, so an impl owes the postcondition on the SAME coefficients at the
binary64 arithmetic too, where the gap is 12 orders clear. The refutation of the
prepatch does not rest on that margin either: `Solution_prepatch.lean` fails its
exact invariant `acc = listSum (coeffs.drop i)` for every `ulp`. `axiom_check.py`
and `conformance_check.py` both assert this separation directly, i.e. that the
magnitude total VIOLATES the postcondition wherever the negative lobes are
material.

### Why only the linear sum is the observable discriminator
The two squared sites (`(np.abs(window)**2).sum()` and `np.abs(window).sum()**2`)
are touched by the gold patch, but `(|wᵢ|)² = wᵢ²` makes
`(window**2).sum()` numerically identical to `(np.abs(window)**2).sum()`. The
*only* value that changes is the **linear** window sum `Σwᵢ` vs `Σ|wᵢ|` — which
the F2P `test_psd_window_flattop` asserts via `spec*win.sum()**2 == spec_a*Fs*(win**2).sum()`.
`windowSum`/`listSum` models exactly that linear signed total (to within the
reduction's own accuracy); the prepatch models the magnitude total and so cannot
verify.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the
normalization total — is modeled **deeply** (the spelled-out fold `listSum` with
its accuracy `roundoffBound ulp`, step A2, an A-reference + I), not hidden behind an
axiom about the function under change: there is no consumed `npSum` axiom, and
`np.abs` (the removed op) is not axiomatized at all. There are no consumed axioms
in this bundle. Note that abstracting the reduction to a tolerance is not a
weakening of the modeled op: it is what the op guarantees, and the postcondition
still pins the SIGNED total to a precision 10¹⁰× finer than the defect.

## C. verify(Solution) ⇒ resolved

`windowSum` verifies only if its output agrees with the **signed** total
`listSum coeffs` to within the accumulation bound (A2), at every arithmetic
`RealArith` admits (A0) — never with the magnitude total, which lies far outside
that interval at the binary64 arithmetic. By R (`ndarray ↔ List Rat`,
order/length preserving) the verified output is an admissible value of the
patched `window.sum()` on the tested windows; by G-AX the real `numpy` reduction
SATISFIES the deep model's postcondition (A-reference) and the magnitude total
VIOLATES it on every window with material negative lobes (the discrimination the
fix needs); by G-CONF the real `window.sum()` lands inside the interval the R/I
transliteration of the fold admits on ≥10⁵ inputs — and, per format, on 83 929
`(window, arithmetic)` observations — while the pre-patch `np.abs(window).sum()`
lands outside it.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
