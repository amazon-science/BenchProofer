# refinement.md — matplotlib__matplotlib-20488

Operation-by-operation correspondence between `implementation_boundedRange`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH lower-bound
sanitisation in `_make_image`). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut sLo := bounds.1` | `s_vmin, s_vmax = vrange` (lower) | R |
| 2 | `let sHi := bounds.2` | `s_vmin, s_vmax = vrange` (upper; never modified) | R |
| 3 | `if logScale = true ∧ sLo ≤ 0 then` | `if isinstance(self.norm, mcolors.LogNorm) and s_vmin <= 0:` | R |
| 4 | `sLo := floor` | `s_vmin = np.finfo(scaled_dtype).eps` | R |
| 5 | `return (sLo, sHi)` | the `(s_vmin, s_vmax)` pair installed via `cbook._setattr_cm(self.norm, vmin=s_vmin, vmax=s_vmax)` | R |

Notes:

- **All legs are R (exact-rational refinement of float bounds) — no A legs.**
  The range floats are modeled as `ℚ` because the fix is purely an order-only
  (sign/zero) decision on `s_vmin` vs `0`; exact `ℚ` captures that comparison
  decidably. `floor` (= `np.finfo(scaled_dtype).eps`) refines to a strictly
  positive rational. No unchanged callee property is consumed, so **G-AX skips**
  and there is no `axiom … _prop`.
- **Op 3 is the discriminating clause (the fix).** Pre-patch the guard is
  `s_vmin < 0` (strict), so an exact-zero lower bound under a log scale is left
  untouched and still breaks the log scale. Post-patch the guard is `s_vmin <= 0`,
  catching zero as well. The pre-patch impl (`Solution_prepatch.lean`) reproduces
  the strict-`<` guard (with the redundant `max sLo floor`), so for
  `logScale = true`, `bounds = (0, hi)` it returns lower bound `0` while
  `problem_spec_boundedRange` requires `floor` (since `0 ≤ 0`). Its
  `correct_boundedRange` is therefore unclosable — exactly the signal G-DIFF
  wants.
- **Frame discipline (directive 5).** `problem_spec_boundedRange` pins the
  upper bound (`result.2 = bounds.2`) AND fully constrains the lower bound in
  both the clamp case and the pass-through case, leaving no output component
  free for a wrong impl to fill.
- **Grounding (directive 8).** The result is pinned by structural conditionals
  on the actual inputs (`bounds.1 ≤ 0`, `logScale`, `floor`), not to an
  ungrounded oracle.
- **G-CONF** mechanically refutes the R legs over ≥1e5 fuzzed inputs (no
  A-consumed legs): the Python shadow of the impl is diffed against the
  post-patch guard. There is no impl-only A-tagged op, so `conf_skip = false`.
