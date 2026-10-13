# refinement.md — scikit-learn__scikit-learn-13779

Operation-by-operation correspondence between `implementation_checkWeightSupport`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `sample_weight`
support-validation loop in `_BaseVoting.fit`). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `for slot in estimators do` | `for name, step in self.estimators:` | R |
| 2 | `let (name, step) := slot` | tuple unpack `name, step` | I |
| 3 | `match step with \| none => pure ()` | `if step is None: continue` (the inserted guard — pass over an empty slot) | R |
| 4 | `\| some accepts => if accepts then pure ()` | `if not has_fit_parameter(step, 'sample_weight'): …` — the present component accepts weights, so the body is skipped and the walk continues | R |
| 5 | `else return Except.error (errMsg name)` | `raise ValueError('Underlying estimator \'%s\' does not support sample weights.' % name)` | R |
| 6 | `return Except.ok ()` | fall through the loop (validation passes; `fit` proceeds) | I |

Notes:

- **Every step is R or I — no A.** The behavior the patch changes (op 3: passing
  over a `None`/empty slot) is modeled DEEPLY — it is the `none` branch of the
  loop's `match`, not an axiomatized callee — so per SPEC_GUIDE §3 the `axioms`
  region is empty and **G-AX skips**.
- **R on op 1**: `self.estimators` (a list of `(name, estimator)` pairs) is
  refined to `List (String × Option Bool)`. The estimator object's ONLY property
  the modeled region observes is `has_fit_parameter(step, 'sample_weight')` — a
  boolean — so a present slot is refined to `(name, some accepts)` and a removed
  slot (`step is None`) to `(name, none)`. The bijection is in mapping.md.
- **R on op 3 (the fix)**: pre-patch, the loop has no `none` branch — the first
  `None` slot hits `has_fit_parameter(None, …)` → `AttributeError`, a failure of
  `fit`. Post-patch, `None` slots are passed over. The Lean model captures this
  exactly: `Solution.lean`'s impl returns `Except.ok ()` (or continues) on a
  `none` slot, whereas `Solution_prepatch.lean`'s impl returns
  `Except.error (errMsg name)` on a `none` slot. The spec's `validateRoster`
  passes over `none`, so the prepatch (which rejects `none`) is unprovable on a
  roster containing a present-accepting roster behind a `none` slot — exactly the
  discriminating F2P scenario (`set_params(lr=None)` then `fit(…, sample_weight=…)`).
- **R on ops 4-5**: `has_fit_parameter(step, 'sample_weight')` is an UNCHANGED
  callee invoked identically on every present estimator; its boolean result is
  carried as the grounded input flag `accepts` (`some true` = accepts weights,
  `some false` = does not). It is NOT axiomatized and NOT validated against the
  real callee (it constrains no output component the spec leaves free). The
  `AttributeError` (pre-patch, on `None`) and the `ValueError` (a present
  unsupported estimator) are both failures of validation; the observable the F2P
  test checks is whether `fit` raises, so both map to a non-`.ok` outcome
  (`.error`). The spec pins the FULL outcome: `.ok ()` iff every present component
  accepts weights, else `.error` naming the first that does not — no output
  component left free (directive 5 frame).
- **Discriminating clause**: `result = validateRoster estimators`. On a roster
  with a `none` slot followed only by accepting components, `validateRoster`
  yields `.ok ()`; the prepatch impl yields `.error` — so the prepatch cannot
  satisfy the spec. This is exactly the bug the issue reports and what the F2P
  tests observe (`fit` must not raise after `set_params(lr=None)`).
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the POST-PATCH loop over
  ≥1e5 fuzzed rosters (`conf_skip=false`).
