# mapping.md — scikit-learn__scikit-learn-13779

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b34751b7ed02b2cfcc36037fb729d4360480a299`, states the type
abstraction (the bijection G-CONF and the bridge check use to translate
Lean↔Python), and gives the provenance of each callee fact.

Repo file under change: `sklearn/ensemble/voting.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateWeightSupport (members : List Member)` | the per-member weight-support validation loop inside `_BaseVoting.fit(self, X, y, sample_weight)` — `sklearn/ensemble/voting.py:76-81` (the `if sample_weight is not None:` block iterating `for name, step in self.estimators`) | the modeled changed function (the validation scan run when a per-sample weighting is supplied) |
| `Member` (`name`,`present`,`supports`) | one `(name, step)` entry of `self.estimators` | the abstracted member carrier (mapping.md §2) |
| `validate (ms : List Member)` | the loop's net effect: raise `ValueError("Underlying estimator '%s' does not support sample weights." % name)` at the first offending member, else fall through | pure spec of the scan's outcome |
| `has_fit_parameter(step, 'sample_weight')` | `sklearn/utils/validation.py:784` | the predicate refined into `Member.supports` for a present member (`step is not None`); **not** axiomatized — see §3 |

The modeled function corresponds to the gold hunk:

```
 if sample_weight is not None:
     for name, step in self.estimators:
+        if step is None:
+            continue
         if not has_fit_parameter(step, 'sample_weight'):
             raise ValueError('Underlying estimator \'%s\' does not'
                              ' support sample weights.' % name)
```

The fix is the `if step is None: continue` guard: an absent member
(`step is None`) is skipped before `has_fit_parameter` is consulted (which is
what crashes on `None` pre-patch, and — once that crash is removed — would
otherwise spuriously raise, since `None` exposes no `sample_weight` parameter).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and `axiom_check.py` use to translate values
between the Lean value domain and the Python repo types. A wrong entry surfaces
as a spurious G-CONF disagreement (the falsifiability the plan §4 trust
statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.estimators` — a list of `(name, step)` pairs | `List Member` | the i-th `(name, step)` pair ↔ the i-th `Member`; `len(self.estimators)` ↔ `members.length`; order preserved |
| the member label `name : str` | `Member.name : Int` | distinct labels ↔ distinct integer ids; only label *equality / identity* is observed (the raised message embeds the label), so an injective `str → Int` coding is faithful. The identity reported on the failure leg is the label of the first offending member. |
| `step is None` (the member is absent) | `Member.present = false` | `step is None` ↔ `present = false`; `step is not None` ↔ `present = true` |
| `has_fit_parameter(step, 'sample_weight')` for a present `step` | `Member.supports : Bool` | `True` ↔ `supports = true`; `False` ↔ `supports = false`. For an absent member (`step is None`) `supports` is immaterial (the `present` conjunct already exempts it); the conformance shadow sets it `false` for absent members, matching that `None` has no `sample_weight` parameter. |
| `raise ValueError(... % name)` at the first offending member | `Except.error name` | the *only* observable of the failure path the F2P / P2P tests check is "raises with this member's label" (`assert_raise_message`); modeled as the error leg carrying `Member.name` |
| fall-through (no raise) | `Except.ok ()` | the validation block completes; `fit` proceeds |

`sample_weight is not None` is the gate that runs this whole block; the modeled
`validateWeightSupport` *is* that already-gated scan, so the gate itself is not
re-modeled (it is the precondition under which the method is the fit's behavior).

## 3. Callee provenance — no consumed axioms, no deep-model reference callee

There is **no `axiom`** in this bundle and **no A-reference callee model**. The
only repo callee the scan invokes, `has_fit_parameter(step, 'sample_weight')`,
is a *pure boolean predicate* on a present member; its result is carried as the
input bit `Member.supports`. That is a **type refinement** of the member
carrier (R), not an axiomatized contract — the spec does not assert anything
about *how* `has_fit_parameter` decides, only consumes its boolean verdict as a
given input field. Hence:

- `axioms` region is empty; `meta.json axioms = []`, `deep_model_references = []`.
- The soundness obligation that remains is purely the R/I refinement fidelity of
  the scan (skip-absent + raise-at-first-unsupported), which **G-CONF** refutes
  against the real patched `fit`.

### 3.1 `has_fit_parameter` bridge (checked by `axiom_check.py`, G-AX-style)
Even though no axiom is consumed, `axiom_check.py` executes the **real**
`sklearn.utils.validation.has_fit_parameter` on representative present
estimators to confirm the `Member.supports` refinement is faithful (a supported
estimator → `True`, an unsupported one → `False`) and that `step is None` is the
genuine absent case the fix skips. This pins the R-refinement of §2 to observed
reality. stdlib + sklearn only; exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13779`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `validate` (the skip-absent + raise-at-first-unsupported scan) to
Python and diffs it against the real patched `_BaseVoting.fit` behaviour:
whether `fit` raises (and with which member label) versus completes, over the
fuzzed ensembles. There is no A-tagged callee left symbolic in the impl region,
so `conf_skip = false`.
