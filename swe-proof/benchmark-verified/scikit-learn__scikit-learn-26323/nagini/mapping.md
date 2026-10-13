# mapping.md — scikit-learn__scikit-learn-26323

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 586f4318ffcdfbd9a1093f35ad43e81983740b66`, states the type
abstraction, and gives the provenance of each unchanged callee the deep model
is validated against (G-AX).

Repo file under change: `sklearn/compose/_column_transformer.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `set_output(subs, remainder, transform)` | `ColumnTransformer.set_output(self, *, transform=None)` — `sklearn/compose/_column_transformer.py:275` (body 300-306) | the modeled changed method (output-container configuration propagation) |
| `subs: List[Trans]` | the children iterated at `_column_transformer.py:301-303` — `trans for _, trans, _ in chain(self.transformers, getattr(self, "transformers_", []))` filtered by `if trans not in {"passthrough", "drop"}` | the explicitly-listed sub-transformers |
| `remainder: Trans` | `self.remainder` — `_column_transformer.py:245` (set in `__init__`), the leftover-columns handler | the estimator (or sentinel) handling the otherwise-unspecified columns |
| `Trans.kind` | whether a child is an actual estimator vs one of the routing strings `"passthrough"`/`"drop"` | observable class flag (1 = estimator, 0 = sentinel) |
| `Trans.cfg` | the child's recorded output container, i.e. `_get_output_config("transform", child)["dense"]` backed by `child._sklearn_output_config["transform"]` (`sklearn/utils/_set_output.py:83-87,240`) | observable output-container code (0 = unconfigured/default) |
| `is_estimator(t)` *(deep model — A-reference)* | the guard `trans not in {"passthrough", "drop"}` (`_column_transformer.py:303` for the children; `:307` post-patch for the remainder) | pure spec: a child is configurable iff it is not a routing sentinel |
| `t.cfg = transform` *(deep model — A-reference)* | `_safe_set_output(trans, transform=transform)` (`sklearn/utils/_set_output.py:244`) | the per-child configuration primitive — records the requested output container |

The pre-patch behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): `set_output` configured only the
children gathered from `self.transformers` / `self.transformers_`, and **never
configured `self.remainder`** when it was an estimator. The added hunk
(`_column_transformer.py:307-309` post-patch):

```python
if self.remainder not in {"passthrough", "drop"}:
    _safe_set_output(self.remainder, transform=transform)
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a child transformer object (estimator instance) OR a routing string `"passthrough"`/`"drop"` | `Trans` with `kind ∈ {0,1}` | `kind == 1` ↔ an estimator object; `kind == 0` ↔ the string sentinel `"passthrough"` or `"drop"` (the two values the guard excludes). The model needs only the configurable-or-not bit, so both sentinels collapse to `kind == 0`. |
| the recorded output container `_sklearn_output_config["transform"]` ∈ {absent, `"default"`, `"pandas"`} | `cfg: int` | `cfg == 0` ↔ no per-estimator container recorded (the default / unconfigured state at the start of this configuration step); `cfg == transform != 0` ↔ the requested container `"pandas"`/`"default"` recorded. The integer is an opaque code; only equality to the requested code is observed. |
| the generator over `chain(self.transformers, transformers_)` filtered by the sentinel guard | `subs: List[Trans]` | the model's explicit list is the materialized sequence of children the real generator yields; the real generator already excludes sentinels, but the model keeps sentinels in `subs` with `kind==0` and re-applies the same guard inside the loop — observationally identical (a sentinel is never configured either way). |
| keyword arg `transform=None` collapsed to a concrete container request | `transform: int`, `transform != 0` | the configuration call is exercised with a real container (`"pandas"`/`"default"`), never the `None` no-op; `transform != 0` records that a genuine container is requested. |

`str` indexing/iteration is banned in Nagini and is irrelevant here: the
discriminating observable is *which children get configured*, modelled with
integer flags, not character content.

## 3. Callee provenance (kind-A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**: the propagation is modelled
deeply (a per-child field write inside a verified loop, plus one extra write
for the leftover-columns child). Two unchanged repo callees the deep model
abstracts are validated against the real code out-of-band.

### 3.1 `t.cfg = transform` ↔ `_safe_set_output(trans, transform=transform)` (A-reference)
**Callee:** `sklearn/utils/_set_output.py:244` `_safe_set_output(estimator, *, transform=None)`.
It calls `estimator.set_output(transform=transform)`, which sets
`estimator._sklearn_output_config["transform"] = transform`
(`_set_output.py:240`). Thereafter
`_get_output_config("transform", estimator)["dense"] == transform`
(`_set_output.py:83-87`). The model's `cfg = transform` records exactly that
container code. **G-AX** (`axiom_check.py::check_safe_set_output_primitive`)
runs the real `_safe_set_output` on a real estimator for both `"pandas"` and
`"default"` and asserts the recorded container equals the requested one.

### 3.2 `is_estimator(t)` ↔ `trans not in {"passthrough", "drop"}` (A-reference)
**Callee/guard:** `_column_transformer.py:303` (children) and `:307` post-patch
(the leftover-columns child). The two routing strings are the only
non-estimator children; everything else is an estimator that owns an output
container. The model's `kind == 1` ⇔ "configurable estimator". **G-AX**
(`axiom_check.py::check_sentinel_classification`) asserts
`"passthrough"`/`"drop"` are excluded and real estimators (`StandardScaler`,
`VarianceThreshold`) are included.

**End-to-end soundness check (G-AX):**
`axiom_check.py::check_composite_behaviour_estimator_remainder` reconstructs the
issue's reproducer with the real composite: a leftover-columns *estimator*
(`VarianceThreshold`) under `set_output(transform="pandas")` preserves the input
DataFrame on `fit_transform` (the expected result), and reverting to
`"default"` yields a numpy array — the discriminating witness that the
leftover-columns estimator is genuinely configured. It imports only sklearn /
pandas / numpy (the very packages the patch runs against, all present in the
evaluation image). Exit 0 iff every obligation holds.
