# mapping.md — matplotlib__matplotlib-25122

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5ec2bd279729ff534719b8bf238dbbca907b93c5`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep-model reference.

Repo file under change: `lib/matplotlib/mlab.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `windowSum (ulp) (maxMag) (coeffs : List Rat)` | the window-normalization factor inside `_spectral_helper` — `lib/matplotlib/mlab.py:291` (changed expression at body line 403, and the linear term of 398) | the modeled changed computation: the order-preserving total of the window coefficients used to normalize the spectrum. Two `require`s: `RealArith ulp maxMag` names the arithmetic the reduction is carried in, `Accumulable maxMag ulp coeffs` restricts to sequences that arithmetic can carry |
| `listSum (xs : List Rat)` *(deep model)* | the exact signed total the patched `window.sum()` approximates | pure spec: the order-preserving **signed** reference total, exact over `Rat`. Not itself claimed equal to the callee — see `WithinRoundoff` |
| `magSum (xs : List Rat)` *(deep model)* | `np.abs(window).sum()` as a *scale*, i.e. `Σ\|wᵢ\|` | pure spec: the magnitude scale the accuracy bound is proportional to. It is the yardstick for `roundoffBound`, NOT a total the method may report |
| `roundoffBound ulp` *(deep model)* | the accumulation error of the reduction in the ACCUMULATOR'S OWN format, `n · 2·ulp · Σ\|wᵢ\|` | pure spec: the accuracy `window.sum()` guarantees. `ulp` is a method PARAMETER, not the constant `2⁻⁵³`: `numpy` accumulates a reduction in the ARRAY's dtype (`np.array([1.0],dtype=np.float32).sum().dtype == float32`), and `_spectral_helper` performs NO dtype normalization — `window = window(np.ones(NFFT, x.dtype))` (`mlab.py:377`) propagates the caller's dtype — so the guaranteed accuracy scales with that dtype's unit roundoff. Not a free parameter either: `require RealArith` confines it to the four roundings real formats have |
| `RealArith ulp maxMag` *(deep model)* | the binary formats a `numpy` reduction is actually carried in, read off `np.finfo(dt)` for `dt ∈ {float16, float32, float64, longdouble}` | pure spec: the admissible **(relative rounding, finite range) PAIRS**, `ulp = 2⁻ᵖ` and `maxMag = 2ᵉ − 2ᵉ⁻ᵖ` for `p = finfo.nmant + 1`, `e = finfo.maxexp` — i.e. `(11, 16)`, `(24, 128)`, `(53, 1024)`, `(64, 16384)`. A format fixes both quantities at once, so they are paired rather than free |
| `Accumulable maxMag ulp coeffs` *(deep model)* | the coefficient sequences whose reduction stays finite in that format | pure spec: `Σ\|wᵢ\| + n·2·ulp·Σ\|wᵢ\| ≤ maxMag`. Every rounded partial total is bounded by the left side, so the reduction cannot saturate; outside it `window.sum()` is `±inf`, about which no finite accuracy claim is honest |
| `WithinRoundoff ulp coeffs out` *(deep model — A-reference)* | `ndarray.sum()` applied to `window` — i.e. the patched expression `window.sum()` (`mlab.py:403/430` post-patch, the `numpy` array reduction) | the postcondition: the reported total agrees with the exact signed total to within `roundoffBound`. Validated against the real `np.sum(window)` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): the `np.abs(...)` wrapper around `window` before the
`.sum()` reduction (`mlab.py:398,403,427,430`, e.g. `np.abs(window).sum()`).
`np.abs` is the callee the patch *deletes*; it is therefore NOT axiomatized in
the post-patch `Solution.lean` (directive 7: never pin a contract about an op
the patch removes).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `window` — a real-valued 1-D `numpy.ndarray` of window coefficients | `List Rat` | the array `w` (length `NFFT`) ↔ a `List Rat` of the same length and order; `w[k]` ↔ `coeffs[k]`; `len(w)` ↔ `coeffs.length`. Each coefficient carried as **exact `Rat`** because the sign of each coefficient participates in the total (directive 8), and a finite binary float of any width is itself an exact rational, so the coefficient-level bridge is a bijection. It is a bijection onto the FINITE values only: `nan`/`±inf` array entries have no `Rat` image and are outside the bridge, which loses nothing the fix is about — on such a window the pre-patch `np.abs(w).sum()` and the patched `w.sum()` are BOTH non-finite, so it is a class on which the gold patch changes no value. The direction matters: the model's `coeffs` are the values read BACK OFF the built array, so each is exactly representable in the arithmetic being modeled. |
| the `(ulp, maxMag)` pair — the arithmetic the reduction is carried in | `RealArith ulp maxMag` | `numpy` reduces an array in the array's OWN dtype (`np.array(w, np.float32).sum().dtype == float32`), and each dtype fixes a relative rounding and a finite range TOGETHER: `ulp = 2⁻ᵖ`, `maxMag = 2ᵉ − 2ᵉ⁻ᵖ` with `p = np.finfo(dt).nmant + 1`, `e = np.finfo(dt).maxexp`. The four disjuncts are exactly `float16/(11,16)`, `float32/(24,128)`, `float64/(53,1024)`, `longdouble/(64,16384)` as `finfo` reports them; `conformance_check.py`/`axiom_check.py` build the pairs from `finfo` at run time so the model cannot drift from the formats. |
| `window.sum()` — the `numpy` reduction over the coefficients (`mlab.py:403` post-patch) | constrained by `WithinRoundoff ulp coeffs out`, i.e. `\|out − listSum coeffs\| ≤ roundoffBound ulp coeffs` | the reduction is a **rounding accumulation in the array's own dtype**, so it does not return the exact rational total; what it guarantees is the classical accumulation error bound `n · 2·ulp · Σ\|wᵢ\|`, where `ulp` is the unit roundoff of THAT dtype. `ulp` is a `windowSum` parameter, bound alongside the coefficients: `numpy` reduces in the array's dtype rather than promoting to binary64, and `_spectral_helper` never normalizes it (`window = window(np.ones(NFFT, x.dtype))`, `mlab.py:377`), so the caller's `x.dtype` fixes both. `listSum` is the exact reference total and `roundoffBound ulp` the accuracy; the pair is the A-reference G-AX validates against the real `np.sum`. |
| `np.abs(window)` — elementwise magnitude (pre-patch only) | (not modeled) | the removed op; its absence IS the fix. Modeled implicitly: `listSum` sums the *signed* coefficients, never their magnitudes. |

One primitive carries all the observable change. Of the four sites the patch
touches, `(np.abs(window)**2).sum()` → `(window**2).sum()` changes NO value at
all, because `(|wᵢ|)² = wᵢ²` elementwise (and exactly so in floating point). The
other three all reduce to the same one difference: `np.abs(window).sum() = Σ|wᵢ|`
becomes `window.sum() = Σwᵢ`, either directly (`mlab.py:398`, `403`) or squared
(`mlab.py:430`, where `(Σ|wᵢ|)²` becomes `(Σwᵢ)²` — a different value for the
same reason, and one that is a function of the linear total). So the single
discriminating primitive is the **signed linear total** `Σ wᵢ` against `Σ |wᵢ|`;
`windowSum`/`listSum` models the signed total, and the prepatch twin models the
magnitude total.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `WithinRoundoff` deep model ↔ `numpy.ndarray.sum` (A-reference)
**Callee:** `numpy`'s array reduction `window.sum()` (equivalently `np.sum`).
The changed normalization is modeled **deeply** in the `pure` region — the exact
reference total `listSum`, the magnitude scale `magSum`, the accuracy
`roundoffBound`, and the postcondition `WithinRoundoff` — with **no consumed
`npSum` axiom**. The reduction is the signed total of the coefficients in index
order, accumulated with rounding in the array's own dtype. The fix removes the
elementwise `np.abs` that preceded this reduction, so the patched value is the
**signed** total.

**What the callee guarantees, and what it does not (G-PANEL-2 correction).** An
earlier revision of this file claimed the reduction was *bit-exact* against the
exact rational total on the fuzz domain, and the spec asserted `out = listSum
coeffs`. That claim is **false**: element-wise exact representability does not
make the *reduction* exact, because the accumulator rounds at every step.
Measured with numpy 1.26.4:

* `coeffs = [1.0, 2⁵³, 1.0, −2⁵³]` → `window.sum()` returns **0.0**, while the
  exact signed total is **2.0**;
* on the windows `_spectral_helper` is actually fed, `np.hanning(2048).sum()` is
  `1023.5000000000001` vs an exact `1023.5`, and `np.blackman(8192).sum()` is
  `3440.2200000000003` vs an exact `3440.22`;
* the reduction is **pairwise**, so it does not even equal a sequential float
  fold of the same values (`np.hanning(2048)`: `1023.5000000000001` pairwise vs
  `1023.5000000000007` sequential) — a model that fixed a summation order would
  be unfaithful for that reason alone.

So exactness is not a property of this callee, and the postcondition states what
the callee does guarantee: the classical accumulation error bound
`|out − Σwᵢ| ≤ n · 2·u · Σ|wᵢ|`, where `u` is the unit roundoff of the format
the accumulation is carried in. The bound is the textbook sequential-accumulation
bound, which dominates the pairwise error numpy actually incurs (pairwise
summation over `n` values has error `O(log n · u · Σ|wᵢ|)`), so it is not a fit
to numpy's current blocking scheme and survives a change of it.

**`u` is a parameter, not the constant `2⁻⁵³`.** A prior revision hardcoded
`ulpScale = 2⁻⁵³`, i.e. it asserted the accuracy of a binary64 accumulator for
every input. That is not what the callee does. `numpy` reduces an array in the
array's OWN dtype — `np.array(w, np.float32).sum()` has dtype `float32` and
accumulates at `u = 2⁻²⁴` — and `_spectral_helper` performs no normalization:
`window = window(np.ones(NFFT, x.dtype))` (`mlab.py:377`) propagates the caller's
`x.dtype` straight into the array that is reduced. `window` is documented as
`callable or ndarray` (`mlab.py:482`), so a `float32` input is an ordinary
admissible call, not a corner case. Measured witness (numpy 2.2.6, scipy 1.15.3,
`scipy.signal.windows.flattop(512).astype(np.float32)`, and identically for the
cosine-sum flattop `axiom_check.py` builds without scipy): the real
`window.sum()` returns `110.16043`, whose distance from the exact signed total
`110.16042266401928` is `8.24e-6` — about `5.6e5` times the hardcoded `2⁻⁵³`
bound of `1.46e-11`, so the old postcondition was FALSE of the real callee on
that input. At the `float32` arithmetic the same witness satisfies the
postcondition with room to spare (bound `7.84e-3`).

**Which `ulp` values, and why not "any positive `ulp`" (the G-PANEL-2 repair).**
Parameterizing `ulp` is necessary but not sufficient: a *freely* quantified
`ulp` constrained only by `0 < ulp` makes the contract STRONGER than any
arithmetic, because the tolerance can be driven toward `0` and the postcondition
then collapses to `out = listSum coeffs` — exactly the exactness this section
measures to be FALSE of the callee. `require RealArith ulp maxMag` is the fix:
the admissible values are the four `(2⁻ᵖ, 2ᵉ − 2ᵉ⁻ᵖ)` pairs `np.finfo` reports
for `float16/float32/float64/longdouble` (§2), so `ulp` ranges over the roundings
that exist and each is paired with the range of the format that has it. The old
divergences land as follows, machine-checked over the shipped `pure` region:

| input | arithmetic | real `window.sum()` | spec's admitted interval | inside? |
|---|---|---|---|---|
| `[1, 2⁵³, 1, −2⁵³]` | float16 | — | `Accumulable` REJECTS (`Σ\|wᵢ\| = 2⁵⁴+2 > 65504`), and `2⁵³` is not even representable | n/a |
| `[1, 2⁵³, 1, −2⁵³]` | float32 | `0.0` | `2 ± 8.59e9` | yes |
| `[1, 2⁵³, 1, −2⁵³]` | float64 | `0.0` | `2 ± 16` | yes |
| `[1, 2⁵³, 1, −2⁵³]` | longdouble | `2.0` (exact: `1 + 2⁵³` fits a 64-bit significand) | `2 ± 0.0078125` | yes |
| `np.hanning(2048)` | float64 | `1023.5000000000001` (error `1.14e-13`) | `1023.5 ± 4.65e-10` | yes |
| `np.blackman(8192)` | float64 | `3440.2200000000003` (error `4.55e-13`) | `3440.22 ± 6.26e-9` | yes |

The old spec's counterexample needed `ulp = 2⁻⁶⁰`, which is not the rounding of
any binary format; `∀ maxMag, ¬ RealArith (1/2⁶⁰) maxMag` is machine-checked.
And exactness is no longer forced: `1 + 2⁻⁶⁴ ≠ listSum [1]` yet it satisfies
`WithinRoundoff` at all four admitted arithmetics, so the tolerance is a real
tolerance rather than a disguised equality. Empirically the bound holds per
format with a wide margin: over 60 559 `(window, arithmetic)` observations drawn
with generic (non-dyadic) mantissas across exponents `2^±40`, the worst
`err/bound` ratio was `0.233` (float16), `0.289` (float32), `0.252` (float64),
`0.255` (longdouble) — each computed in exact rational arithmetic via
`float.as_integer_ratio` (plain `float()` truncates `longdouble` and manufactures
spurious violations).

**Why the range precondition, and why it does not excuse the bug.** `require
Accumulable maxMag ulp coeffs` (`Σ|wᵢ| + n·2·ulp·Σ|wᵢ| ≤ maxMag`) bounds the
magnitude scale TOGETHER WITH the accumulated error the same arithmetic incurs on
it, which is what a rounded partial total is bounded by; it therefore excludes
exactly the inputs whose accumulation saturates to `±inf`, about which no finite
error bound can be honest. Both parts are load-bearing.

*The magnitude term.* With `maxMag` pinned by `RealArith` the constraint bites:
`[2¹⁰²³, 2¹⁰²³]`, whose real float64 `.sum()` is `+inf`, is REJECTED at the
float64 arithmetic (`Σ|wᵢ| = 2¹⁰²⁴ > 2¹⁰²⁴ − 2⁹⁷¹`, machine-checked), and at the
longdouble arithmetic — the one that does admit it — the real reduction is the
finite `1.7976931348623159e308`, inside the bound.

*The error term.* `Σ|wᵢ| ≤ maxMag` alone would NOT be enough, because the value
carried between steps is a ROUNDED partial, which can exceed every exact partial.
Measured witness at the float16 arithmetic: `w = [32768] + [17]*1024`, whose
`Σ|wᵢ| = 50176 ≤ 65504` — admitted by the magnitude term alone — accumulates in
order to `+inf`, because a running total in `[2¹⁵, 65504]` has spacing 32 and each
`+17` rounds UP by 32, so the accumulator climbs at nearly twice the true rate.
`Accumulable` rejects it (`Σ|wᵢ| + n·2u·Σ|wᵢ| = 100401 > 65504`). The bound the
postcondition states is the order-independent sequential one (it is not fitted to
numpy's current pairwise blocking, which on this same input returns a finite
`50180`), so the precondition has to exclude everything that saturates under an
accumulation that bound covers — which is exactly what the error term adds. The
term costs nothing on the real domain: an `NFFT`-point float64 window has
`Σ|wᵢ| ≈ NFFT` and `n·2u·Σ|wᵢ| ≈ 1e-11`, some 300 orders of magnitude inside
`2¹⁰²⁴ − 2⁹⁷¹`.

The earlier 2-argument `Accumulable maxMag coeffs` could not do this work: with
`maxMag` unconstrained, `maxMag := Σ|wᵢ|` satisfied it for EVERY sequence, so it
excluded nothing. The exclusion is **patch-invariant**: on every overflowing
window the patched `w.sum()` and the pre-patch `np.abs(w).sum()` are BOTH
non-finite, so the class the precondition drops is one on which the gold patch
changes no value. It is not a narrowing that hides the discriminating behaviour —
G-CONF and G-AX both assert the converse direction mechanically, that
`Accumulable` never admitted an input whose real reduction saturated (0 such
inputs over 100 018 + 40 022 windows).

**The tolerance does not blunt the fix.** At `ulp = 2⁻⁵³` (binary64, the dtype
`_spectral_helper` sees for the default `float64` input, and the one every window
in `axiom_check.py` / `conformance_check.py` is built at) the signed/magnitude gap
on the discriminating windows exceeds the bound by 10 to 13 orders of magnitude
(scipy `flattop`: gap/bound ≈ 5.1e13 at n=8, 1.3e12 at n=512, 3.9e10 at
n=16384), so `np.abs(window).sum()` lies far OUTSIDE the interval
`WithinRoundoff` admits. That is the precise sense in which the prepatch violates
the spec.

*Recorded limitation, at the loosest real precision.* The separation is a
function of `ulp`. At `ulp = 2⁻¹¹` (`float16`) and long windows the bound grows
past the gap — `flattop(512)`: gap/bound = 0.285, `flattop(2048)`: 0.0713 — so at
that ONE arithmetic the interval would admit the magnitude total, and the
postcondition would not discriminate on those inputs. This is a true statement
about what a `float16` accumulator guarantees, not a modelling shortcut: at
`n = 512`, `n·2u·Σ|wᵢ|` genuinely exceeds the signed/magnitude gap, and a
`float16` reduction of such a window really can land anywhere in that interval.
(The very worst cases are not even in the domain: `Accumulable` at `float16`
rejects `flattop(16384)`, where `Σ|wᵢ| + n·2u·Σ|wᵢ| = 7.0e4 > 65504`.) It leaves
no room for a wrong implementation, because `RealArith` is a precondition on
`windowSum`'s ARGUMENTS, not a disjunction the implementation may choose between:
a verifying impl must satisfy the postcondition on the same `coeffs` at ALL four
arithmetics, including the `float64` one where the gap exceeds the bound by
`1.3e12`. Nor is it what refutes the prepatch twin: that fails structurally,
since its loop invariant `acc = listSum (coeffs.drop i)` is an exact equation a
magnitude fold violates for EVERY `ulp`. It is stated here rather than left for a
reader to discover.

**Soundness check (G-AX):** `axiom_check.py` runs the real `numpy.sum` on
boundary windows (empty, single, all-positive, all-negative, mixed-sign, the
flattop coefficient pattern from the F2P test, sentinels ±0, and the
catastrophic-cancellation witness above), the seven real window functions, three
cosine-sum flattops built as the F2P test builds them, plus 40 000 randomized
fuzz windows — half of them wide-dynamic-range (exponents over ±60, lengths to
400), the domain the old fuzz never reached — asserting that the real
`window.sum()` satisfies `WithinRoundoff` at the `ulp = 2⁻⁵³` instantiation, which
is the faithful one for the `float64` arrays it builds. It re-runs the same
assertion at EVERY pair `RealArith` admits (each window rebuilt in that format
and its coefficients read back off the array), 21 939 `(window, arithmetic)`
observations in exact rational arithmetic, and checks the precondition's own
soundness in the converse direction: `Accumulable` never admitted an input whose
real reduction saturated. It also asserts the *discrimination
property* that motivates the fix, on every window whose negative lobes are
material: the signed/magnitude gap EXCEEDS the bound, and the magnitude total
therefore VIOLATES the postcondition. A window whose only negative samples are
float dust (e.g. `np.blackman(8192)`'s ~−1e-19 tails, total negative content
8.1e-21 of the magnitude scale) genuinely does not discriminate, and the guard
`has_material_negative_content` says so rather than asserting something false of
the callee. Imports only `numpy`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25122`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates the impl's fold (`listSum` / the backward `while` loop) to an
exact `Fraction` signed total — exact because the Lean carrier is exact `Rat`,
which is what the impl region computes — and checks the **patched** repo
expression `window.sum()` (the behaviour `patch.diff` introduces at
`mlab.py:403/430`) against the spec's postcondition `WithinRoundoff`. The
`numpy` reduction is the A-reference left as the real callee on the oracle side;
the shadow is the pure R/I transliteration of the fold plus the accuracy bound.
The oracle must land inside the interval the postcondition admits on every
fuzzed window.

Bit equality is deliberately NOT the comparison: the reduction rounds, and it is
pairwise, so it equals neither the exact total nor a sequential float fold. The
check additionally confirms the tolerance still SEPARATES the behaviours — the
pre-patch `np.abs(window).sum()` must fall OUTSIDE the same interval on every
window with material negative lobes (measured: it does, on all 95 270 such
windows of the 100 018-input run).

The R/I leg is checked at every arithmetic the precondition admits, not only at
binary64: `conform_all_ariths` rebuilds each short window in `float16`,
`float32`, `float64` and `longdouble`, reads the coefficients BACK OFF the built
array (so the model's `coeffs` are exactly the values that format holds — deriving
them from the pre-conversion rationals would compare the reduction of one input
against the exact total of a different one), skips the `(window, arithmetic)`
pairs `Accumulable` does not admit, and FAILS if a real reduction saturates on a
pair it does admit. Last run: 100 018 inputs, 83 929 `(window, arithmetic)`
observations, 0 disagreements, 0 saturations.
