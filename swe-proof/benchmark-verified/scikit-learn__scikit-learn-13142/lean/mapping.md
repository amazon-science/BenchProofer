# mapping.md — scikit-learn__scikit-learn-13142

## Symbol binding (@ base_commit 1c8668b0a021832386470ddf740d834e02c66f69)

- Modeled function: `BaseMixture.fit_predict(self, X, y=None)`
  `sklearn/mixture/base.py:194-276` (the `for init in range(n_init)` selection
  loop + the final e-step + `_set_parameters(best_params)` + `return
  log_resp.argmax(axis=1)`).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | notes |
|---|---|---|
| one fitting trial → `(best_params candidate, lower_bound)` | `Int × Int` `(config, score)` | `config` is an opaque identifier of the fitted parameter set; `score` is `lower_bound`. |
| `lower_bound` (float) | `Int` (`score`) | order-only: selection uses `>` only (`if lower_bound > max_lower_bound`). Exact `Int` keeps order decidable (DECISIONS.md). |
| sequence of `n_init` trials | `List (Int × Int)` `trials` | one element per `init` iteration; non-empty since `n_init ≥ 1`. |
| `max_lower_bound` running max + `best_params` | `bestParam : List (Int×Int) → Option Int` via `foldl stepBest` | `max_lower_bound` init `-np.infty`; first trial always strictly greater ⇒ `none` seed. Strict `>` ⇒ earliest-tie wins (matches Python: ties do NOT replace `best_params`). |
| `log_resp.argmax(axis=1)` for a config `c` | `labelsOf c : List Nat` | per-sample component labels; deterministic function of the parameter config the e-step was run under. |
| returned labels | `result : List Nat` | must equal `labelsOf (selected best config)`. |

## Callee provenance

- `labelsOf` (Lean `opaque`) ↔ the composite "run final `_e_step(X)` under the
  current model parameters, then `log_resp.argmax(axis=1)`". It is a
  deterministic function of the parameter configuration currently set on the
  estimator. UNCHANGED by the patch. No `_prop` axiom is consumed by the proof
  (the bug is purely about WHICH config `labelsOf` is applied to — ordering of
  the final e-step relative to `_set_parameters(best_params)` — not about
  `labelsOf`'s own behavior), so it is A-reference (signature only).

## Flag deps

- `do_init = not(self.warm_start and hasattr(self,'converged_'))`; with the
  default `warm_start=False`, `n_init = self.n_init`. The bug is only OBSERVABLE
  when `n_init > 1` (F2P sets `n_init=5`/`10`): with `n_init=1` the last trial IS
  the best trial, so the buggy and fixed code agree. The model therefore covers
  `len(trials) ≥ 1` and the discriminating clause fires whenever the
  highest-scoring trial is not the last one.

## G-CONF fuzz seed

- pinned seed: `13142`
