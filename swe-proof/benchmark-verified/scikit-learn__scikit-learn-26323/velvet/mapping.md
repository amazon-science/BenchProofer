# mapping.md — scikit-learn__scikit-learn-26323

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 586f4318ffcdfbd9a1093f35ad43e81983740b66`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms** and **no A-reference deep models**
in this bundle (§3 below): the only callee involved is applied identically to
every selected component and factors out as an R refinement.

Repo file under change: `sklearn/compose/_column_transformer.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collectBroadcastTargets (listed : List Component) (extra : Component)` | `ColumnTransformer.set_output(self, *, transform=None)` — `sklearn/compose/_column_transformer.py:275` (body 320-322 post-patch) | the modeled changed function (the output-config broadcast) |
| `listed : List Component` | the `transformers` generator of `set_output`: `trans for _, trans, _ in chain(self.transformers, getattr(self, "transformers_", [])) if trans not in {"passthrough", "drop"}` — `_column_transformer.py:304-310` | the listed sub-transformers, sentinel markers already filtered |
| `extra : Component` | `self.remainder` — `_column_transformer.py:312` (post-patch `if self.remainder not in {"passthrough", "drop"}: _safe_set_output(self.remainder, ...)`) | the designated extra component (the remainder estimator-or-sentinel) |
| `isReal c` | the membership test `c not in {"passthrough", "drop"}` — `_column_transformer.py:308, 312` | True iff the component is a real estimator (not a placeholder sentinel string) |
| `selectReal`, `broadcastTargets` *(deep model — pure, NOT an axiom/A-reference)* | the ordered set of components reached by `_safe_set_output(trans, transform=...)` — `_column_transformer.py:311, 313` | pure spec: which components receive the broadcast |

The pre-patch repo state the change corrects (refinement audit only, not in the
consumer spec view): `set_output` broadcasts to the listed transformers but
never to `self.remainder`, so a remainder estimator's output container is left
unconfigured (`_column_transformer.py` pre-patch, lines 300-306).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a sub-transformer `trans` (an estimator object, or one of the sentinel strings `"passthrough"`/`"drop"`) | `Component` | a sentinel string ↔ `Component.marker`; a real estimator with object identity `n` ↔ `Component.real n`. Only the sentinel-vs-estimator distinction is observed. |
| the `transformers` generator (post-filter list of `trans`) | `List Component` | the `chain(self.transformers, transformers_)`-derived `trans` values, in order, with the sentinel filter applied; G-CONF mirrors that the `set_output` generator already drops sentinels — `selectReal` makes the same exclusion explicit so SHADOW and ORACLE agree. |
| `self.remainder` | `Component` (the `extra` argument) | a sentinel string remainder ↔ `Component.marker`; a remainder estimator ↔ `Component.real n`. Default `remainder="drop"` ↔ `.marker`. |
| `_safe_set_output(c, transform=transform)` applied to a component | identity on `Component` (omitted from the carrier) | the per-component configuration action is **unchanged** by this patch and is applied identically to every selected component; it alters internal output-config state, not the membership of the broadcast target list that the change governs. It therefore factors out as R — the observable the F2P test depends on is exactly *which* components get configured (the remainder included), which is the ordered `out` list. |
| `transform` keyword (`"default"`/`"pandas"`/`None`) | (omitted) | passed through unchanged to every selected component; identical on both sides of the change, so it does not affect the selection and is not modeled. |

`set_output` mutates no input list and returns `self`; the modeled query reads
the membership of each component and mutates nothing (directive 5 — neither
`listed` nor `extra` is `mut`).

## 3. Callee provenance — no axioms, no A-references

There is **no `axiom`** and **no A-reference deep model of an outside callee**
in this bundle, so there is no `axiom_check.py` (G-AX is vacuous — like the
`astropy__astropy-13236` exemplar). The one callee in the changed region,
`_safe_set_output`, is **unchanged** by the patch and is applied identically to
every selected component; per §2 it factors out as an R refinement (identity on
`Component`), not a consumed axiom. Modeling it deeply would add a dead model
the proof never uses. The behavioural content of the change lives entirely in
**which** components are selected — `broadcastTargets` (deep model, pure region),
whose R/I transliteration G-CONF differential-tests against the patched code.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`26323`** so the
consumer-side verdict (§11.3) is reproducible. The SHADOW transliterates
`selectReal`/`broadcastTargets` (R/I-tagged ops); the ORACLE transliterates the
**patched** `set_output` selection block verbatim (the post-image: listed
sub-transformers minus sentinels, then `self.remainder` when it is not a
sentinel). There are no A-tagged callees to leave as the real repo callee.
