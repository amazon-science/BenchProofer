# refinement.md — scikit-learn__scikit-learn-12585

Maps every operation in `implementation_duplicate` (Solution.lean) to its
`patch.diff` / base `clone` counterpart. Tags: **R** (type refinement),
**A-consumed** (proof consumes this axiom's property), **A-reference** (deep model
validated == real callee by G-AX), **I** (identical concrete op).

The modeled function is `clone` (`sklearn/base.py`). The impl is a recursive
functional `def` mirroring `clone`'s recursion (clone is fundamentally recursive;
a class-valued parameter is cloned *inside* the recursion — that is where the bug
fires — so the imperative `Id.run do` form cannot host the self-call under the
termination checker; the faithful skeleton is the recursive `def`, SPEC_GUIDE §2
"recursive `def` with `termination_by`").

| # | `implementation_duplicate` op | `clone` / patch.diff counterpart | tag |
|---|---|---|---|
| 1 | match head `.group kind es` vs `.node …` | `estimator_type = type(estimator)`; collection-vs-other dispatch | R |
| 2 | `.group kind es` branch | `if estimator_type in (list,tuple,set,frozenset)` | R |
| 3 | `es.attach.mapM (reproduce safe)` then `.ok (.group kind es')` | `estimator_type([clone(e, safe=safe) for e in estimator])` | R |
| 4 | `if (!exposesConfig) \|\| isBlueprint` | `elif not hasattr(estimator,'get_params') or isinstance(estimator, type)` — **the fixed guard** | R |
| 5 | `if safe then .error ()` | `else: raise TypeError(...)` | R |
| 6 | `else .ok (.node isBlueprint exposesConfig tag cfg)` | `if not safe: return copy.deepcopy(estimator)` — deepcopy of a leaf/class is observationally the input | R (I-grade: identity) |
| 7 | inner `if isBlueprint then .error ()` | dead under the post-fix guard (a blueprint already took op-4's no-config branch); a defensive no-op kept so spec and impl share shape. Realized-only nodes reach the rebuild | R |
| 8 | `cfg.attach.mapM (fun ⟨kv,_⟩ => (reproduce false kv.2).map (kv.1, ·))` | `new_object_params = estimator.get_params(deep=False)` then `new_object_params[name] = clone(param, safe=False)` for each param | R |
| 9 | `.ok (.node isBlueprint exposesConfig tag cfg')` | `klass = estimator.__class__; new_object = klass(**new_object_params)` | R |

No row is A-consumed or A-reference: there is **no `opaque` callee and no `axiom`
in Solution.lean**. The only non-trivial callee, `copy.deepcopy`, is modeled as
the identity no-op of the no-config branch (op 6) — for the value shapes that
reach it under `safe=False` (leaves and class objects) deepcopy is observationally
identity, so this is an R/I op validated by G-CONF, not an axiom (SPEC_GUIDE §3:
a deeply-modeled changed decision is never axiomatized; here the *whole* routing
decision the patch changes is modeled deeply by `configUnusable`).

No changed op is inexpressible: the entire fix is the boolean guard at op 4,
modeled exactly as `configUnusable isBlueprint exposesConfig`.

## Prepatch (the real bug)

`Solution_prepatch.lean` weakens op 4 to `if !exposesConfig then …` (drops the
`|| isBlueprint` disjunct), reproducing the pre-fix guard
`not hasattr(estimator,'get_params')`. A blueprint node
(`isBlueprint=true, exposesConfig=true`) — an estimator **class** — then skips the
no-config branch and reaches the rebuild path. The realized-only invariant of that
path is violated: op 7's `if isBlueprint then .error ()` now fires, modeling the
`TypeError` raised by calling the unbound `get_params` on a class. So the prepatch
returns `.error ()` where the fixed spec returns `.ok` (the class unchanged) —
exactly the F2P case `clone(MyEstimator(empty=MyEstimator))`. The carried gold
proof cannot close against this impl (G-DIFF).

## Conformance (G-CONF) — R/I differential

All ops are R/I, so `conf_skip=false`. `conformance_check.py` transliterates
`implementation_duplicate` into a Python shadow and differential-tests it against
an oracle that reproduces the **post-patch** `clone` routing
(`not hasattr or isinstance(...,type)`) over ≥10⁵ fuzzed `PyVal` trees + edge
cases, including class-valued parameters at every recursion depth.
