# mapping.md — matplotlib__matplotlib-20488

Binds `Solution.lean` symbols to the repo at
`base_commit = b7ce415c15eb39b026a097a2865da73fbcf15c9c`.

Repo file under change:
`lib/matplotlib/image.py` (method `_ImageBase._make_image`).

Band: **float-precision** (plan §10 open question 1).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `logNormVmin (sVmin eps : Rat)` | the `s_vmin` sanitisation branch at `lib/matplotlib/image.py:535-537` inside `_make_image` | the modeled lower-bound clamp |
| `sVmin` | `s_vmin` (the lower scale bound, unpacked from `vrange` at `image.py:534`) | the lower bound being sanitised |
| `eps` | `np.finfo(scaled_dtype).eps` (`image.py:537`) | a fixed strictly-positive floor |
| `out` (result) | the (possibly reassigned) `s_vmin` passed as `vmin=...` to `cbook._setattr_cm` (`image.py:539`) | the sanitised lower bound |

The branch is reached only when `isinstance(self.norm, mcolors.LogNorm)` is true
(`image.py:535`). The model is exactly the body of that LogNorm branch; the
LogNorm guard itself is the precondition for the modeled operation (it is the
"when a logarithmic mapping is applied" framing in the spec docstring) and is
not a separate computed input.

## 2. Float modeling choice (plan §10 Q1) — Rat, not Float, not Real

The modeled carrier for `sVmin`, `eps`, `out` is Mathlib **`Rat`** (exact
rationals), NOT Lean `Float`. Rationale, decided on this bundle (recorded for
plan §10 Q1):

- **Float defeats the verifier here.** A direct `Float` model
  (`method logNormVmin (sVmin eps : Float) ...`) is the closest model to the
  repo and was attempted first. `loom_solve` leaves the goal
  `sVmin ≤ 0 → (sVmin > 0 → eps = sVmin)` unsolved: Lean's `Float.le`/`Float.lt`
  are defined over an **opaque** `floatSpec` (`#print Float.le` ⇒
  `fun a b => floatSpec.le a.val b.val`), so the solver has NO usable trichotomy
  or `a ≤ b → ¬ b < a` lemma to discharge that the `≤ 0` and `> 0` branches are
  exclusive. `loom_smt` fails earlier still — the Float comparison term does not
  survive the Auto/Lean→SMT translation (`Unexpected head term ... LamTerm.lam`),
  i.e. `loom_smt` has no IEEE-754 Float theory wired in at the pinned Velvet
  commit. No interactive `decide`/`exact?` route exists because the order facts
  are not theorems over the opaque spec.
- **Real is noncomputable.** A `Real` model fails to elaborate as a Velvet method
  body: `Real.decidableLE` is `noncomputable`, so the `if sVmin ≤ 0` condition
  cannot compile (`dependsOnNoncomputable`).
- **`Rat` is exact, computable, and has a clean dense total order.** It verifies
  with bare `loom_solve` (no hints). It is faithful because the **discriminating
  behaviour is order-only**: the patch turns on the boundary `s_vmin ≤ 0` vs the
  old `s_vmin < 0`, a sign/zero comparison that is *precision-independent*. No
  rounding, ULP, or representable-value reasoning is part of the changed logic —
  the clamp does not compute with `eps`, it only *selects* between `eps` and
  `s_vmin`. A dense exact ordered field (Rat) represents "a tiny positive floor"
  and "a small negative / zero lower bound" with full fidelity for the only
  property the fix observes (the sign of `s_vmin`). Int would also verify but is
  less faithful (it cannot represent a tiny sub-unit positive `eps` or a
  fractional lower bound); Rat is preferred precisely because it keeps those
  representable while staying in `loom_solve`'s clean order theory.

### `eps > 0` provenance
`eps = np.finfo(scaled_dtype).eps`. `numpy.finfo(dtype).eps` is the machine
epsilon for the floating dtype — the difference between 1.0 and the next larger
representable value — and is **always strictly positive** for every floating
dtype (`np.finfo(np.float32).eps ≈ 1.19e-7`, `np.finfo(np.float64).eps ≈
2.22e-16`). `scaled_dtype` is `np.float32` or `np.float64` (`image.py:414-424`),
both floating, so `eps > 0` holds unconditionally. Modeled as the precondition
`require eps > 0`. (The exact magnitude of `eps` is irrelevant to the
discriminating behaviour — only its strict positivity matters, since after the
clamp the post-image is `eps` whenever `s_vmin ≤ 0`.)

### The LogNorm-branch condition
The modeled operation is the BODY of the `isinstance(self.norm, mcolors.LogNorm)`
guard. The fix folds `and s_vmin <= 0` into that guard. Under the spec, the
"a logarithmic intensity mapping is applied" framing IS the LogNorm guard; the
`s_vmin <= 0` test is the modeled branch condition `sVmin ≤ 0`.

## 3. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `s_vmin` : `float` (np float32/64 scalar) | `Rat` | order-preserving abstraction; sign/zero exact; magnitude exact for any representable value. The only observed property is the sign relative to 0. |
| `np.finfo(scaled_dtype).eps` : strictly-positive `float` | `Rat` with `require eps > 0` | exact; the strict positivity IS the `require`. |
| sanitised `s_vmin` (post-assignment) | `Rat` (result `out`) | order-preserving abstraction |
| `x <= 0` (Python float compare) | `sVmin ≤ 0` (`Rat` order) | identical on non-NaN; see §4 for NaN |
| `a = b if c else a` (in-place conditional clamp) | `if c then b else a` | identical control |

### Float round-tripping / exact predicate
Lean↔Python float round-tripping is NOT exercised: the model is `Rat`, and the
discriminating predicate is the **exact order comparison** `sVmin ≤ 0` (resp.
`> 0`), which is lossless for both the Rat model and the Python float for every
non-NaN value. The observable-equality predicate G-CONF uses is therefore
**exact** on the *selection outcome* ("did the clamp replace `s_vmin`?"), not on
float bit-patterns. There is no ULP tolerance needed because the changed logic
selects, it does not arithmetically combine.

### NaN behaviour (documented, plan §10 Q1)
The patch condition is `s_vmin <= 0`, which evaluates to **`False` for NaN** in
both Python (`float('nan') <= 0` is `False`) and numpy. So a NaN lower bound is
left UNTOUCHED by both the buggy and the fixed code — neither clamps it. The
`Rat` model has no NaN value, so this branch is outside the model's domain; it
is faithful because the model never claims to clamp NaN (the spec's `sVmin ≤ 0`
clause does not fire for an input that is "not ≤ 0", matching `<=` returning
`False` on NaN). `conformance_check.py` includes explicit NaN cases and asserts
SHADOW and ORACLE agree (both pass NaN through), documenting the boundary.

## 4. Callee provenance
There are **no axiomatized callees**. `np.finfo(...).eps` is a constant
strictly-positive value abstracted as the plain positive input `eps`
(R-abstracted input, tagged **R** in refinement.md); its strict positivity is
captured by `require eps > 0`. The `isinstance(self.norm, mcolors.LogNorm)`
guard is the modeled-operation precondition, not a computed callee. Therefore
there is **no `axiom_check.py`** for this bundle.

## 5. G-CONF fuzz seed
`conformance_check.py` seeds with **20488**. The R/I shadow is the clamp formula
from `Solution.lean`'s `logNormVmin` post-image
(`eps if sVmin <= 0 else sVmin`); the ORACLE is the patched source line
transliterated VERBATIM (`s_vmin = eps if s_vmin <= 0 else s_vmin`, under the
LogNorm branch). SHADOW vs ORACLE are differential-tested over fuzzed floats
(including `0.0`, `-0.0`, tiny positives/negatives, large magnitudes, and `NaN`)
with `eps > 0`; exit 0 iff zero disagreements.
