# mapping.md — scikit-learn__scikit-learn-14087

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a5743ed36fbd3fbc8e351bdab16561fbfca7dfa1`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each value the spec treats as a free input.

Repo file under change: `sklearn/linear_model/logistic.py`.

## 1. Symbol ↔ repo binding

The modeled code is the per-class body of the no-refit aggregation branch inside
`LogisticRegressionCV.fit` (`sklearn/linear_model/logistic.py:1936`, class at
`:1670`). The branch is the `else:` arm of `if self.refit:` (`else` at `:2169`),
executed once per class in the `for index, (cls, encoded_label) ...:` loop
(`:2138`). Two independent outputs are committed there per class: the
coefficient vector `w` and the appended auxiliary mixing value.

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recordClassResult (...)` | the per-class output commitment of the no-refit branch — the `w = ...` selection (`logistic.py:2173-2178`) together with the auxiliary append (`logistic.py:2183-2184`) | the modeled changed code: commit, for one class, the coefficient vector and the auxiliary mixing value |
| `perClassEffective : Bool` | `multi_class == 'ovr'` — the **resolved** strategy local `multi_class` (set by `_check_multi_class(self.multi_class, solver, len(classes))` at `logistic.py:2004`) tested at `:2173` post-fix | true ⇔ the per-class (one-vs-rest) layout is the strategy in effect |
| `perClassRequested : Bool` | `self.multi_class == 'ovr'` — the **raw requested** estimator attribute tested at `:2173` pre-fix | true ⇔ the per-class layout was the strategy as originally requested |
| `coefByPerClass : Coef` | `np.mean([coefs_paths[i, best_indices[i], :] for i in range(len(folds))], axis=0)` (`:2174-2175`) — the coefficient read-out under the per-class array layout | candidate coefficient vector for the per-class layout |
| `coefByJoint : Coef` | `np.mean([coefs_paths[:, i, best_indices[i], :] for i in range(len(folds))], axis=0)` (`:2177-2178`) — the read-out under the joint (multinomial) layout | candidate coefficient vector for the joint layout |
| `auxActive : Bool` | `self.penalty == 'elasticnet'` (`:2183` post-fix) | true ⇔ the auxiliary regularization (elastic-net) mode is in effect |
| `auxValue : Rat` | `np.mean(l1_ratios_[best_indices_l1])` (`:2184`) — the averaged auxiliary mixing value | the auxiliary value to record when the mode applies |
| `out : Coef × Option Rat` | the pair `(w, self.l1_ratio_[-1])` committed for this class | the two recorded outputs |
| `chooseCoef` / `chooseAux` | the (post-fix) decision logic of the two commitments | pure spec: select the coefficient vector / the recorded auxiliary value |

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `multi_class == 'ovr'` (resolved local, `:2173` post-fix) | `perClassEffective : Bool` | the Python equality test ↔ the Lean `Bool`. The resolver `_check_multi_class` maps `'auto'`→`'ovr'`/`'multinomial'` and passes `'ovr'`/`'multinomial'` through; only `'ovr'` yields the per-class layout, so `multi_class == 'ovr'` ↔ `perClassEffective = true`. |
| `self.multi_class == 'ovr'` (raw attribute, `:2173` pre-fix) | `perClassRequested : Bool` | the raw requested attribute equality ↔ the Lean `Bool`. With a `'multinomial'`/`'ovr'` request the two agree; with `'auto'` the raw test is always `False` while the resolved one may be `True` — the disagreement the issue triggers. |
| `np.mean([...], axis=0)` coefficient vector (either layout) | `Coef` (`= List Rat`) | a fitted coefficient vector ↔ a `List Rat`. Only WHICH candidate vector is selected is observed by the modeled decision (the numeric contents are produced by unchanged code, `np.mean`/array indexing); G-CONF carries each candidate by an opaque tag, not by its numbers (mapping §3). |
| `self.penalty == 'elasticnet'` (`:2183` post-fix) | `auxActive : Bool` | the penalty-mode equality ↔ the Lean `Bool`. Pre-fix there is no such guard (the append is unconditional). |
| `np.mean(l1_ratios_[best_indices_l1])` (`:2184`) | `auxValue : Rat` | the averaged auxiliary scalar ↔ a `Rat` (exact; DECISIONS float note — a quantity observed only for whether/which it is recorded is modeled with `Rat`, not `Float`). |
| `self.l1_ratio_.append(v)` vs `self.l1_ratio_.append(None)` | `Option Rat` (`some v` / `none`) | recording the averaged value ↔ `some auxValue`; recording `None` ↔ `none`. The result list `self.l1_ratio_` is a list of `float`-or-`None`; each appended entry ↔ one `Option Rat`. |

### 2.1 The two bugs being fixed (refinement audit; not in the consumer spec view)

**Behavior 1 — coefficient selection (`logistic.py:2173`).** Pre-fix the branch
chose `w` with `if self.multi_class == 'ovr':`, reading the *raw requested*
attribute. When the user requests `'auto'` (or any non-`'ovr'` value that the
resolver turns into the per-class layout for the data at hand), `self.multi_class
== 'ovr'` is `False`, so the code takes the `else` (joint/multinomial) read-out
`coefs_paths[:, i, best_indices[i], :]` — a 4-index access — against a
`coefs_paths` array that, for the per-class layout actually in effect, is only
3-dimensional. NumPy raises `IndexError: too many indices for array` (the issue's
traceback at `:2193`). The fix tests the *resolved* local `multi_class`, which
names the layout the stored coefficients really have. Modeled as: select by
`perClassEffective`, not `perClassRequested`.

**Behavior 2 — auxiliary append (`logistic.py:2183-2184`).** Pre-fix the branch
ran `best_indices_l1 = best_indices // len(self.Cs_)` and
`self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))` unconditionally.
When the penalty is not `'elasticnet'`, `l1_ratios_` is the singleton `[None]`
(`logistic.py:1978`); indexing it by `best_indices_l1` and averaging produces a
length-1 array whose shape no longer matches the per-class expectation the
no-refit attribute-shape contract requires (`l1_ratio_.shape == (n_classes,)`),
which the F2P `test_LogisticRegressionCV_no_refit[*-l2]` cases assert. The fix
guards the averaging with `if self.penalty == 'elasticnet':` and appends `None`
otherwise. Modeled as: record `some auxValue` only when `auxActive`, else `none`.

The two fixes are independent: behavior 1 changes which coefficient vector is
returned (observed by the no-refit `coef_` shape and the absence of the
`IndexError`); behavior 2 changes the recorded auxiliary value (observed by the
no-refit `l1_ratio_` value/shape). `Solution_prepatch.lean` reproduces bug 1 and
fails `out.1 = chooseCoef perClassEffective ...`; `Solution_prepatch_2.lean`
reproduces bug 2 and fails `out.2 = chooseAux auxActive auxValue` (G-DIFF).

## 3. Callee provenance (kind-A) — none

This bundle declares **no axioms and no deep-model references**. The modeled
change is the two control-flow decisions that commit a class's outputs; every
operand they consume has ALREADY been computed by surrounding, *unchanged* code
and is taken as a free input:

- the two candidate coefficient vectors (`coefByPerClass`, `coefByJoint`) are the
  two `np.mean(..., axis=0)` read-outs — produced identically pre- and post-fix;
  the fix only chooses *between* them;
- `auxValue` is `np.mean(l1_ratios_[best_indices_l1])` — computed by unchanged
  arithmetic; the fix only decides *whether* to record it;
- `perClassEffective` / `perClassRequested` / `auxActive` are three boolean flags
  read from the resolved strategy, the raw attribute, and the penalty mode.

None of these is a repo function the modeled code *calls* whose contract the
proof must assume; they are values handed in. (`np.mean`, NumPy indexing, and
`_check_multi_class` are unchanged by the patch and only *produce* the operands —
they are folded into the free inputs.) Hence **G-AX has nothing to falsify** —
see `axiom_check.py`, which (a) asserts the empty obligation set
(`axioms == []`, `deep_model_references == []`), (b) re-confirms the deep model
(`chooseCoef`/`chooseAux`) against the real patched decision logic on boundary +
fuzz inputs, and (c) exercises the **unchanged** real resolver
`_check_multi_class` to validate the `perClassEffective` (resolved) vs
`perClassRequested` (raw) bijection, including the binary-`'auto'` disagreement
the issue triggers. NOTE G-AX runs against the **unpatched** image (the gold
patch is applied only for G-CONF/G-RESOLVE), so the witness exercises only
patch-unchanged code; it does NOT drive the buggy `fit` path and assert it is
already fixed. All refinement.md rows are R or I; `conf_skip = false` (the impl
region carries no A-tagged op, so G-CONF carries full weight).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14087`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `chooseCoef`/`chooseAux` (R/I-tagged ops) to Python and compares
against the patched decision logic's behaviour (the real correctness oracle),
including the binary-`auto` boundary the issue reports and the non-elastic-net
penalty cases the F2P tests exercise.
