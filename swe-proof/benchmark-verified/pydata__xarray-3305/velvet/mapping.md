# mapping.md — pydata__xarray-3305

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 69c7e01e5167a3137c285cb50d1978252bb8bcbf`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one deep-model reference.

Repo files under change: `xarray/core/variable.py`, `xarray/core/dataset.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduceElementAttrs (srcAttrs, choice, glob)` | `Variable.quantile(self, q, dim, interpolation, keep_attrs)` — `xarray/core/variable.py:1595` | the element-level changed function (per-array reduction), viewed through the metadata it attaches |
| `reduceContainerAttrs (srcAttrs, choice, glob)` | `Dataset.quantile(self, q, dim, interpolation, numeric_only, keep_attrs)` — `xarray/core/dataset.py:4694` (member call site line 4769) | the container-level changed function; threads its `keep_attrs` to each member's `Variable.quantile` |
| `reduceLabeledAttrs (srcAttrs, choice, glob)` | `DataArray.quantile(self, q, dim, interpolation, keep_attrs)` — `xarray/core/dataarray.py:2827` | the user-facing wrapper; forwards `keep_attrs` to the container reduction (`_to_temp_dataset().quantile(...)`). Unchanged by the patch but the F2P-observable entry point — modeled as the composition that exercises both fixed sites |
| `resolveGlobal (g, fallback)` *(deep model — A-reference)* | `_get_keep_attrs(default)` — `xarray/core/options.py:61`, reading `OPTIONS["keep_attrs"]` | unchanged shared callee resolving the ambient library option against a per-op fallback; validated `resolveGlobal == _get_keep_attrs` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `effectiveKeep`, `keptAttrs` | pure spec composing the above | the keep-metadata semantics every reduction shares |

The pre-patch behaviour the change removes (refinement audit only, not in the
consumer spec view): `Variable.quantile` constructed its result as
`Variable(new_dims, qs)` — no `attrs` argument, so the result always carried the
empty mapping (`variable.py:1657` pre-patch); and `Dataset.quantile` called
`var.quantile(q, dim=reduce_dims, interpolation=interpolation)` without passing
`keep_attrs` (`dataset.py:4769` pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the result's attribute mapping (`Variable._attrs`, an `OrderedDict`/`None`) | `List (String × String)` | a present mapping `{k1:v1, …}` ↔ the association list `[(k1,v1), …]`; the **absent** mapping (`attrs=None`, observed as the empty `OrderedDict`) ↔ `[]`. The F2P observable (`actual.attrs == self.attrs`) is dict equality; key/value content is preserved by the bijection. Values are stringified for the differential (mapping is content-faithful, not type-faithful — only presence/identity of the carried mapping is at issue). |
| `keep_attrs` argument (`bool` or `None`) | `Option Bool` | `True ↔ some true`, `False ↔ some false`, `None ↔ none` |
| `OPTIONS["keep_attrs"]` global (`"default"` \| `True` \| `False`) | `GlobalPref` | `"default" ↔ gDefault`, `True ↔ gKeep`, `False ↔ gDrop` |
| the data/shape computation (`np.nanpercentile`, `new_dims`, `q`) | (elided) | **unchanged by the patch** (identical pre/post); orthogonal to the metadata view. Not modeled — an R-refinement that drops an unobserved-by-this-change coordinate. The F2P test asserts both `np.testing.assert_allclose(actual.values, expected)` (unchanged path) AND `actual.attrs == self.attrs` (the changed path); only the latter is the behaviour this bundle pins. |

The `numeric_only` / per-variable / coordinate-skipping logic of `Dataset.quantile`
is unchanged data-flow around the member call; the modeled view is the single
member whose metadata propagation the patch alters (mapping.md §3.2).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `resolveGlobal` deep model ↔ `_get_keep_attrs` (A-reference)
**Callee:** `xarray.core.options._get_keep_attrs(default)` (unchanged by the patch).
Source at base_commit:

```python
def _get_keep_attrs(default):
    global_choice = OPTIONS["keep_attrs"]
    if global_choice == "default":
        return default
    elif global_choice in [True, False]:
        return global_choice
    else:
        raise ValueError(...)
```

`resolveGlobal g fallback` models this exactly: `gDefault → fallback`,
`gKeep → true`, `gDrop → false` (the `ValueError` branch is unreachable — the
option setter restricts `keep_attrs` to `True/False/"default"`,
`options.py:37`). It is the deep model of an **unchanged** callee, so it is an
**A-reference** validated by G-AX, not a consumed axiom.

### 3.2 Why both sites are modeled (directive 2/3)
The F2P test (`test_quantile`) calls `DataArray(self.va).quantile(q, dim=dim,
keep_attrs=True)` and asserts `actual.attrs == self.attrs`. The call path is
`DataArray.quantile → _to_temp_dataset().quantile → Variable.quantile`. The
metadata survives **iff** (a) `Dataset.quantile` forwards `keep_attrs` to
`Variable.quantile` (the `dataset.py` hunk) AND (b) `Variable.quantile` honors it
by setting `attrs = self._attrs if keep_attrs else None` (the `variable.py`
hunk). Each is independently necessary — hence two `Solution_prepatch` variants,
one per site, and three composed methods.

The element fallback is **drop** (`_get_keep_attrs(default=False)`), matching the
`variable.py` hunk `keep_attrs = _get_keep_attrs(default=False)`.

## 4. G-CONF / G-AX fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` and `axiom_check.py` seed `random.Random` with **`3305`**
so the consumer-side verdict (§11.3) is reproducible. The R/I shadow
transliterates `effectiveKeep`/`keptAttrs` (R/I ops) to Python and leaves
`resolveGlobal`'s callee as the real `_get_keep_attrs` (A-reference → run real
callee under the corresponding `set_options(keep_attrs=…)`, not the model).
