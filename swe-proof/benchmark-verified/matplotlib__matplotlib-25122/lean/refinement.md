# refinement.md — operation correspondence (matplotlib__matplotlib-25122)

Each op of `implementation_windowCorrectionFactor` ↔ its `patch.diff` counterpart.
Tags: **R** type refinement, **A-consumed** axiom property consumed by proof,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

The modeled function is the window-correction *divisor* computed inside
`_spectral_helper`; the patch changes only how that divisor is built from the
window samples. `result` (the spectrum) is divided by this factor in each branch;
the bijection records the factor, not the spectrum it scales (the spectrum is
upstream / downstream of the changed expression and unchanged by the fix).

| # | Lean op (`implementation_windowCorrectionFactor`) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `match mode with \| Mode.magnitude \| Mode.complex => let mut s := 0; for w in window do s := s + w; return s` | `result = np.abs(result) / window.sum()` (l.396, magnitude) and `result /= window.sum()` (l.402, complex) — the divisor `window.sum()` | R | `window.sum()` (the FIXED, signed total) ⟷ the `List.sum` fold `Σ wᵢ`. The amplitude branches share one divisor; the differing numerator (`np.abs(result)` vs `result`) is upstream of the modeled factor and not part of the changed expression. Exact `Rat` ⟷ real samples (sign-only fix). |
| 2 | `\| Mode.psd => if scaleByFreq then let mut sq := 0; for w in window do sq := sq + w*w; return sq` | `result /= (window**2).sum()` (l.427) | R | `(window**2).sum()` ⟷ `(window.map (·*·)).sum = Σ wᵢ²`. NOTE: this line's BEHAVIOUR is unchanged by the patch (`Σ|wᵢ|² = Σ wᵢ²`); modeled deeply as the signed-square sum for completeness, not a discriminator. |
| 3 | `else let mut s := 0; for w in window do s := s + w; return s * s` | `result /= window.sum()**2` (l.430) | R | `window.sum()**2` (FIXED) ⟷ `(Σ wᵢ)²`. This is the squared-signed-total branch and IS a discriminator (`(Σ|wᵢ|)² ≠ (Σ wᵢ)²` for windows with negatives). |
| 4 | `\| Mode.angle \| Mode.phase => return 1` | (no window-correction division in the `angle`/`phase` branches; l.399-401 set `result = np.angle(result)` and apply no window factor) | R | The absence of a window-correction division ⟷ a factor of `1` (dividing by `1` is the identity). |

Every op is **R** (type refinement). There are no **A-consumed** axioms (the proof
consumes no callee contract — the factor is a pure reduction over the window
samples) and no **A-reference** deep-model callees (no unchanged repo callee is
invoked; the `sum`/`map`+`sum` reductions are spelled out, not delegated to an
`opaque`). No changed op is inexpressible: the entire fix is the replacement of
`np.abs(window).sum()`/`np.abs(window).sum()**2` (sum / squared-sum of magnitudes)
with `window.sum()`/`window.sum()**2` (signed sum / squared signed sum), modeled
deeply by the signed `List.sum` folds.

`conf_skip = false` — the impl region is all-R (no A-tagged ops), so G-CONF
mechanically differential-tests the R legs against the real patched factor.
