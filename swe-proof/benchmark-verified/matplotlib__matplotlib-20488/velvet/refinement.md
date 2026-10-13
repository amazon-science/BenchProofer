# refinement.md — matplotlib__matplotlib-20488

Correspondence between `Solution.lean`'s `logNormVmin` impl and `patch.diff`
(the gold patch clamps the LogNorm lower scale bound to a strictly-positive
floor whenever it is zero or negative). `patch.diff` is the gold verbatim
(applies at base_commit, resolves — G-RESOLVE).

Band: **float-precision** (plan §10 Q1). Float modeling choice and the
`Rat`-vs-`Float`-vs-`Real` decision are justified in mapping.md §2.

## A. The corrected clamp — `_make_image`'s `s_vmin` sanitisation

Gold hunk:
```
                 s_vmin, s_vmax = vrange
-                if isinstance(self.norm, mcolors.LogNorm):
-                    if s_vmin < 0:
-                        s_vmin = max(s_vmin, np.finfo(scaled_dtype).eps)
+                if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0:
+                    # Don't give 0 or negative values to LogNorm
+                    s_vmin = np.finfo(scaled_dtype).eps
```

| # | Solution.lean impl op (`logNormVmin`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `sVmin : Rat` | `s_vmin` (lower scale bound from `vrange`) | R | `float` ↔ `Rat`, order-preserving; only the sign relative to 0 is observed (mapping.md §3). The discriminating boundary `<0` vs `<=0` is order-only, so an exact ordered carrier is faithful. |
| A2 | param `eps : Rat` with `require eps > 0` | `np.finfo(scaled_dtype).eps` | R | UNCHANGED constant callee result abstracted as a plain positive input (mapping.md §4); `np.finfo(...).eps > 0` for every floating dtype IS the `require`. Identical on both sides of the fix ⇒ abstracted, NOT axiomatized. |
| A3 | `if sVmin ≤ 0 then return eps` | `s_vmin = np.finfo(...).eps` under `... and s_vmin <= 0` | I | identical: a non-positive lower bound is replaced outright by the floor. This is the CHANGED logic: the guard moves from `s_vmin < 0` to `s_vmin <= 0`, and the action from `max(s_vmin, eps)` to an outright `= eps`. The `<= 0` boundary is the discriminator (`Rat` `≤` ↔ Python `<=`; NaN out of model domain, mapping.md §3). |
| A4 | `else return sVmin` | (fall-through: `s_vmin` left unchanged when `s_vmin > 0`) | I | identical: a strictly-positive lower bound is left untouched. `Rat` `>` ↔ Python `>`. |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. `np.finfo(...).eps`
is an **R-abstracted input** (a fixed strictly-positive constant, identical
pre/post-fix), NOT a consumed axiom — hence no `axiom_check.py`. The clamp itself
(the `<= 0` selection between `eps` and `s_vmin`) is the changed logic, modeled
deeply and tagged **I**.

### R / I tag summary
- **R**: A1 (`sVmin` float↔Rat order abstraction), A2 (`eps` finfo-eps abstracted positive input).
- **I**: A3 (the non-positive ⇒ floor replacement), A4 (the positive ⇒ pass-through).
- **The clamp (A3/A4) is the I-tagged changed op.** **`eps` is the R-abstracted input.** The boundary move `<0` → `<=0` is the discriminating change (boundary at exactly `s_vmin = 0`).

## B. verify(Solution) ⇒ resolved

`logNormVmin` verifies only if
`(sVmin ≤ 0 → out = eps) ∧ (sVmin > 0 → out = sVmin)` (A3–A4). By R (mapping.md
§3) the verified result equals the patched
`s_vmin = eps if s_vmin <= 0 else s_vmin` (under LogNorm) on the real argument.
The F2P test `test_huge_range_log[png--1]` builds a LogNorm image whose data
floor drives `s_vmin` to a non-positive value; pre-fix this reached `LogNorm`
with a `0`/negative `vmin`, raising `ValueError("Invalid vmin or vmax")` (the
log transform of a non-positive bound is non-finite). The spec pins the
post-image to the strictly-positive `eps` exactly when `sVmin ≤ 0`, which is
what keeps the bound in LogNorm's valid (positive) domain.

The prepatch impl tests `< 0` (not `≤ 0`) and uses `max sVmin eps` instead of an
outright `eps`, against the byte-identical spec. It leaves two unsolved goals;
the discriminating one is
`(¬ sVmin < 0) → (sVmin ≤ 0 → sVmin = eps)` — i.e. at **`sVmin = 0`**:
`¬(0 < 0)` holds (the buggy `else` branch returns `sVmin = 0`), `0 ≤ 0` holds,
so the spec demands `0 = eps`, which is false since `require eps > 0`. This is
exactly the bug: a zero lower bound was NOT clamped (the old guard tested `< 0`),
so LogNorm still received `0`. G-DIFF fails on this `sVmin = 0` clause (the
`<0` vs `<=0` boundary), precisely as required.

G-CONF differential-tests the R/I shadow (`eps if sVmin <= 0 else sVmin`)
against the patched source line over fuzzed floats — including `0.0`, `-0.0`,
tiny positives/negatives, large magnitudes, and `NaN` — with `eps > 0`
(seed 20488). No trust points beyond the type bijection (mapping.md §3): there
are no axioms. NaN is documented (both sides pass it through, since `<=` is
`False` on NaN — mapping.md §3).
