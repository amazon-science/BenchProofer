# mapping.md — scikit-learn__scikit-learn-12585

## Symbol binding (file:line @ base_commit bfc4a566423e036fbdc9fb02765fd893e4860c85)

Modeled function: `clone(estimator, safe=True)` — `sklearn/base.py:30`.

| Python (base.py) | line | Lean (Solution.lean) |
|---|---|---|
| `clone(estimator, safe=True)` | 30 | `reproduce (safe : Bool) : PyVal → Except Unit PyVal` (spec) / `implementation_duplicate` (impl) |
| `estimator_type = type(estimator)` | 47 | the `PyVal` constructor head (`.group` vs `.node`) |
| `estimator_type in (list, tuple, set, frozenset)` | 49 | `.group kind es` case (an ordered collection) |
| `[clone(e, safe=safe) for e in estimator]` | 50 | `es.attach.mapM (fun ⟨e,_⟩ => reproduce safe e)` |
| `not hasattr(estimator, 'get_params')` | 51 | `!exposesConfig` (does NOT advertise the config-query interface) |
| `isinstance(estimator, type)`  *(the fix)* | 51 | `isBlueprint` (value is a class/template, not a realized instance) |
| `not hasattr(...) or isinstance(...,type)` | 51 | `configUnusable isBlueprint exposesConfig = (!exposesConfig) || isBlueprint` |
| `if not safe: return copy.deepcopy(estimator)` | 52–53 | `if safe then .error () else .ok (.node …)` — unchanged identity copy |
| `else: raise TypeError(...)` | 54–58 | `.error ()` (safe branch on a non-configurable value) |
| `klass = estimator.__class__` | 59 | `tag` (carried through the rebuild) |
| `new_object_params = estimator.get_params(deep=False)` | 60 | reading `cfg` (the keyed configuration) |
| `new_object_params[name] = clone(param, safe=False)` | 61–62 | `cfg.attach.mapM (fun ⟨kv,_⟩ => (reproduce false kv.2).map (fun v => (kv.1,v)))` |
| `new_object = klass(**new_object_params)` | 63 | `.ok (.node isBlueprint exposesConfig tag cfg')` |
| sanity re-check loop (params is/identity) | 64–73 | not modeled — see "Out of scope" |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

`PyVal` models a clone-able Python value, restricted to the shape `clone` observes:

* `PyVal.group kind elems`
  ↔ a `list` / `tuple` / `set` / `frozenset` of clone-able values.
  `kind : Nat` is an injective encoding of which collection type it is (only
  equality is observed). `elems` is the ordered element list.
* `PyVal.node isBlueprint exposesConfig tag config`
  ↔ a non-collection Python value.
  - `exposesConfig : Bool` ↔ `hasattr(estimator, 'get_params')` — whether the
    value advertises the `get_params` interface. A plain leaf (int, str, the
    `None`, a numpy scalar, …) has `exposesConfig = false`; an estimator
    *instance* AND an estimator *class* both have `exposesConfig = true`
    (a class exposes the attribute as an unbound method).
  - `isBlueprint : Bool` ↔ `isinstance(estimator, type)` — whether the value is
    a *class object* (a type) rather than an instance. A class is a blueprint;
    every instance has `isBlueprint = false`.
  - `tag : Nat` ↔ `estimator.__class__` identity (carried through the rebuild).
  - `config : List (Nat × PyVal)` ↔ `estimator.get_params(deep=False)`, the
    keyed parameter dict (keys are `Nat`-encoded parameter names; insertion
    order preserved as list order). Empty for a leaf.
* `Except Unit PyVal`
  ↔ the result of `clone`: `.ok v` ↔ a returned value; `.error ()` ↔ the
    `TypeError` raised on a non-cloneable value under `safe=True`.

Realizability of the flag pair (which `(isBlueprint, exposesConfig)` combos a
real Python value can take):

| `isBlueprint` | `exposesConfig` | real Python value |
|---|---|---|
| false | false | a leaf (int/str/None/array/…) — no `get_params` |
| false | true  | an estimator **instance** — `get_params` bound, callable |
| true  | true  | an estimator **class** (a `type`) — `get_params` present but UNBOUND ⇒ calling it raises `TypeError: missing 'self'` |
| true  | false | a non-estimator class/`type` (e.g. `int`, a plain class) — is a `type` but exposes no `get_params` |

All four are realizable; the conformance fuzzer covers all four.

## The discriminating behavior (what the patch fixes)

Pre-fix, the no-config branch guard is `not hasattr(estimator,'get_params')`
alone. An estimator **class** (`isBlueprint=true, exposesConfig=true`) therefore
falls through to the estimator branch and `estimator.get_params(deep=False)` is
called on the class — `get_params` is an unbound method, so this raises
`TypeError: get_params() missing 1 required positional argument: 'self'`. This is
hit in practice while *recursively* cloning a parameter that is itself a class
(`clone(param, safe=False)` at line 62), which is the F2P scenario:
`clone(MyEstimator(empty=MyEstimator))`.

Post-fix the guard is `not hasattr(...) or isinstance(estimator, type)`, i.e.
`configUnusable = (!exposesConfig) || isBlueprint`. A class now takes the
no-config branch: with `safe=False` (the recursion's flag) it returns
`copy.deepcopy(estimator)`, and `deepcopy` of a class object returns the class
itself (classes are atomic to deepcopy) — so the cloned param is the same class,
matching the test's `assert clf.empty is clf2.empty`.

## Callee provenance / flag deps

* `copy.deepcopy(estimator)` (line 53): for the values reaching this branch under
  `safe=False` — leaves, and (post-fix) class objects — `deepcopy` returns a value
  observationally identical to the input (a class deepcopies to itself; an
  immutable leaf to an equal value). Modeled as identity (`.ok (.node …)` /
  `.ok (.group …)` unchanged), NOT axiomatized — it is the structural no-op of the
  no-config branch. No consumed axiom.
* `hasattr` / `isinstance` / `type` (lines 47,51): pure reflection captured
  directly by the `PyVal` flags; no callee contract consumed.

## Out of scope (faithfully unmodeled)

* The post-construction sanity loop (lines 64–73) raising `RuntimeError` when a
  constructor drops/mutates a parameter. This is orthogonal to the issue and to
  the F2P test (well-behaved estimators round-trip params unchanged); it concerns
  no branch the patch touches. Modeling it would require an estimator-constructor
  semantics the fix does not exercise. The spec assumes well-behaved
  reconstruction (the §3 "touched fields only" discipline).
* `numpy`/`scipy` array internals — not reached by the cloned shapes here.

## G-CONF fuzz seed

Pinned seed: **12585** (also hard-coded in `conformance_check.py`). ≥10⁵ fuzzed
inputs over randomly generated `PyVal` trees with all four flag combinations,
plus hand-picked edge cases pinning the class-valued-parameter discriminator.
