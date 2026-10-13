# refinement.md — scikit-learn__scikit-learn-13142

Maps every op in `implementation_fit_predict` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses callee axiom · **A-reference**
deep-modeled changed op validated == real callee by G-AX · **I** identical op.

The gold patch is purely a REORDERING: it moves the final
`_, log_resp = self._e_step(X)` block from BEFORE the `if not self.converged_`
warning (i.e. before `self._set_parameters(best_params)`) to AFTER
`self._set_parameters(best_params)`. So the post-patch (correct) code computes
the returned labels from the SELECTED best parameters; the pre-patch code
computes them from whatever parameters were left set after the LAST trial.

| # | impl op (`implementation_fit_predict`) | patch.diff / source counterpart | tag |
|---|---|---|---|
| 1 | `let mut best : Option (Int×Int) := none` | `max_lower_bound = -np.infty` (no best yet) | R: `-np.infty` seed ↔ `none`; first trial always strictly greater. |
| 2 | `for t in trials do …` | `for init in range(n_init): … _initialize/_e_step/_m_step … lower_bound` | R: each trial's fitted `(best_params, lower_bound)` ↔ `(config, score)`. The inner EM loop is collapsed to its result `(config, score)`. |
| 3 | `match best with none => best := some t \| some (_,bs) => if t.2 > bs then best := some t` | `if lower_bound > max_lower_bound: max_lower_bound = lower_bound; best_params = self._get_parameters(); best_n_iter = n_iter` | I (under R): strict `>`, earliest-tie keeps prior best — identical control flow. |
| 4 | `match best with none => return [] \| some (bp,_) => return labelsOf bp` | `self._set_parameters(best_params)`; **then** `_, log_resp = self._e_step(X)`; `return log_resp.argmax(axis=1)` | A-reference: `labelsOf bp` is the final e-step + argmax run under the SELECTED best config `bp`. This is the moved-after-selection ordering = the FIX. The pre-patch impl applies `labelsOf` to the last trial's config (`lastConfig`) instead — the bug. |

- No A-consumed axioms: the proof needs no property of `labelsOf`; correctness is
  entirely about WHICH config it is applied to (a structural fact about the
  selection fold), so `labelsOf` is opaque-signature-only (A-reference, G-AX).
- No changed-inexpressible op. The reordering is modeled exactly by the choice
  of argument to `labelsOf` (selected best vs last).
- `meta.json conf_skip = false`: the impl region's R/I content (the selection
  fold + the choice of config fed to `labelsOf`) is differential-tested by
  G-CONF, with `labelsOf` left as a fixed deterministic stub on both legs.
