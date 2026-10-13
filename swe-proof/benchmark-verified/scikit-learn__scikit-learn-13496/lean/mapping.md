# mapping.md — symbol binding & type bijection (scikit-learn__scikit-learn-13496)

## Modeled function
- **Lean** `implementation_isolationForestInit : … → IForestConfig …`
- **Python** `sklearn.ensemble.iforest.IsolationForest.__init__(self, …)` —
  `sklearn/ensemble/iforest.py:167-195 @ 3aefc834` (post-patch: the constructor
  accepts a `warm_start` keyword, default `False`, and forwards it to the parent
  bagging constructor `super().__init__(…, warm_start=warm_start, …)`).

The function under spec is the constructor. It assembles the estimator's stored
configuration by forwarding the bagging parameters to the parent constructor
(`sklearn.ensemble.bagging.BaseBagging.__init__`, which sets `self.<attr> =
<attr>` for each), then sets the two subclass-only attributes. The behavior the
issue + F2P test demand is that the `warm_start` configuration flag is **stored
as supplied** by the caller; pre-patch this flag was not accepted by the
constructor and so always took the parent default value (the closed/`False`
state), and the iterative-tree-addition behavior it enables was unreachable.

## Stored configuration (the constructed object's settable attributes)
After construction the object carries (per `BaseBagging.__init__` + the two
subclass assignments): `n_estimators`, `max_samples`, `max_features`,
`bootstrap`, `bootstrap_features` (hardcoded `False` in the super call),
`oob_score` (parent default `False`, never overridden), `warm_start`, `n_jobs`,
`random_state`, `verbose`, `behaviour`, `contamination`.

## Type bijection (used by G-CONF)
| Python | Lean | notes |
|---|---|---|
| `warm_start : bool` | `Bool` | the exposed flag (the fix) |
| `bootstrap : bool` | `Bool` | forwarded |
| `bootstrap_features` (always `False`) | `Bool` | hardcoded constant in super call |
| `oob_score` (parent default `False`) | `Bool` | never set by subclass |
| `n_estimators : int` | `Nat` | tree count, non-negative |
| `verbose : int` | `Nat` | verbosity level, non-negative |
| `behaviour : str` | `String` | subclass attribute |
| `max_samples` (`"auto"` \| float \| int) | `Sample` (opaque type var) | pass-through value, never computed on by `__init__`; modeled polymorphically to avoid committing a union encoding |
| `contamination` (`"legacy"` \| float) | `Contam` (opaque type var) | subclass attribute, pass-through |
| `max_features` (float \| int) | `Feat` (opaque type var) | pass-through |
| `n_jobs` (`None` \| int) | `Jobs` (opaque type var) | pass-through |
| `random_state` (`None` \| int \| RandomState) | `Rand` (opaque type var) | pass-through |

The five pass-through value parameters are modeled as universally-quantified
type variables because `__init__` never inspects or transforms them — it only
stores them. Polymorphic identity-storage is the faithful, minimal model and
sidesteps a Python-union encoding the fix does not exercise.

## Callee provenance
- No UNCHANGED callee is consumed as an axiom. The only operation the patch
  changes is the **threading of one constructor argument into the stored
  configuration**, which is modeled DIRECTLY as a field assignment (an I/R
  operation), not axiomatized. The parent constructor's per-attribute
  `self.<attr> = <attr>` assignments are themselves identity stores, modeled as
  the record fields. The axioms region is therefore empty and `axiom_check.py`
  is a skip stub.

## Flag dependency
None. The constructor takes no mode flag that alters which attributes are
stored.

## G-CONF fuzz seed
Pinned seed: **13496**. ≥10^5 fuzzed configurations over `warm_start ∈
{True, False}`, `bootstrap ∈ {True, False}`, integer `n_estimators`/`verbose`,
`max_samples ∈ {"auto", floats, ints}`, `contamination ∈ {"legacy", floats}`,
`max_features`, `n_jobs ∈ {None, ints}`, `behaviour` strings, `random_state ∈
{None, ints}`. The shadow is compared against the real post-patch
`IsolationForest(**kwargs)` stored attributes.
