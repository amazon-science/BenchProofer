# mapping.md — pydata__xarray-2905

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7c4e2ac83f7b4306296ff9b7b51aaf016e5ad614`, states the type
abstraction, and gives the provenance of the deeply-modelled decision.

Repo file under change: `xarray/core/variable.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalize_self_describing(data)` | the "we don't want nested self-described arrays" normalization step inside `as_compatible_data(data, fastpath=False)` — `xarray/core/variable.py:220-221` (body line `data = getattr(data, "values", data)`) | the modeled changed behaviour: decide whether to replace the incoming value by its `.values` contents |
| `Incoming` class | the incoming `data` argument of `as_compatible_data` at this step (an arbitrary Python value) | minimal carrier exposing only the facts the step inspects |
| `Incoming.is_recognized_container` | the predicate `isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` (post-patch) — `xarray/core/variable.py:221` after the fix | whether `data` is a recognized self-describing container |
| `Incoming.exposes_values` | `hasattr(data, "values")` — the condition `getattr(data, "values", data)` keys off (pre-patch) | whether `data` carries a `.values` attribute |
| `Incoming.values_identity` | the object referenced by `data.values` | identity tag of the `.values` contents |
| `Incoming.identity` | `data` itself | identity tag of the value itself |
| `normalize_self_describing` return | the rebinding of the local `data` after this step | identity tag of the value that survives normalization |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): `data = getattr(data, "values",
data)` (`xarray/core/variable.py:221`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the arbitrary Python value `data` and its possible `.values` rebinding | identity tags (`int`): `identity` for `data`, `values_identity` for `data.values` | object identity (`is`) ↔ integer-tag equality (`==`). The step's only effect is *which* object the local `data` ends up bound to; the model returns the surviving tag. Object content is irrelevant to this decision and is abstracted away. |
| `isinstance(data, (pd.Series, pd.Index, pd.DataFrame))` | the bool field `is_recognized_container` | `True` ⟺ `data` is one of the three recognized pandas container kinds |
| `hasattr(data, "values")` | the bool field `exposes_values` | `True` ⟺ `getattr(data, "values", data)` would return `data.values` rather than the default |

The real-world fact that every recognized pandas container exposes a `.values`
attribute is encoded as the model invariant
`Implies(is_recognized_container, exposes_values)` — Required on the function
and on the constructor, and validated on real `pd.Series`/`pd.Index`/
`pd.DataFrame` instances by `axiom_check.py`. It makes "recognized container"
strictly more specific than "exposes `.values`", which is the whole point of
the fix.

## 3. Provenance of the deeply-modelled decision (G-AX / axiom_check.py)

There is **no `@ContractOnly` axiom** in this bundle: the operation that
changed *is* the decision predicate, so it is modelled **deeply** (the two bool
fields + the verified branch in `normalize_self_describing`), never hidden
behind an axiom about an unchanged callee.

**The changed step** (`xarray/core/variable.py`, `as_compatible_data`):

```python
# we don't want nested self-described arrays
-    data = getattr(data, "values", data)
+    if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)):
+        data = data.values
```

Pre-patch the step unwrapped `.values` for **any** object exposing that
attribute (`getattr(data, "values", data)`). Post-patch it unwraps only the
three recognized pandas containers; every other value — crucially, a plain user
object that merely exposes a `.values` attribute — survives unchanged. The
later code path (`np.asarray(data)` → object dtype → `_possibly_convert_objects`
round-trip) then wraps such an unrecognized object as a 0-d object array whose
single item *is* the original object. This is exactly what the F2P test
`TestAsCompatibleData::test_unsupported_type` asserts:
`Variable(dims=(), data=CustomWithValuesAttr(np.arange(3)))._data.item()` is the
custom object.

**Soundness / faithfulness check (G-AX):** `axiom_check.py` runs the real
`as_compatible_data` and the public `Variable` constructor on (a) three
non-recognized objects — the issue's scalar-`.values` object, an
array-`.values` object, and a bare object — asserting each survives unchanged
(`item() is` the original); and (b) `pd.Series`/`pd.Index`/`pd.DataFrame`,
asserting each is unwrapped to its `.values` content. It also asserts the model
invariant (`recognized ⟹ exposes .values`) on real pandas instances. It imports
only numpy/pandas/xarray (the libraries the patched code itself uses). Exit 0
iff faithful.
