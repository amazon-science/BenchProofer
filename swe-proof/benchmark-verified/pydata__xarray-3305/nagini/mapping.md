# mapping.md — pydata__xarray-3305

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 69c7e01e5167a3137c285cb50d1978252bb8bcbf`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo files under change: `xarray/core/variable.py`, `xarray/core/dataset.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduce_result_metadata(self_meta, keep_metadata)` | `Variable.quantile` — `xarray/core/variable.py:1595` (attrs/return at lines 1640, 1658-1661) | the modeled changed function (site 1): the single-array reduction that now honours `keep_attrs` for the result metadata |
| `entrypoint_reduce_metadata(self_meta, keep_metadata)` | `Dataset.quantile` — `xarray/core/dataset.py:4694` (per-variable delegation at lines 4756-4772) | the modeled changed function (site 2): the container-level reduction that now forwards `keep_attrs` to the per-variable delegation |
| `ambient_keep_default()` *(axiom — A-consumed)* | `xarray.core.options._get_keep_attrs(default=False)` — `xarray/core/options.py:61` | unchanged community callee consulted when the caller leaves `keep_attrs` unspecified (`None`); resolves the ambient default policy |
| `resolve_keep(keep)` | the inline three-valued resolution `if keep_attrs is None: keep_attrs = _get_keep_attrs(default=False)` (`variable.py` patched lines; `dataset.py:4780-4781`) | pure spec: None → ambient default, else the explicit flag |
| `selected_meta(src, keep)` | `attrs = self._attrs if keep_attrs else None` → `Variable(new_dims, qs, attrs)` (`variable.py` patched lines 1671-1673) | pure spec: result metadata = copy of source when keeping, else empty |

The pre-patch repo facts the change targets (for the refinement audit, not
referenced from the consumer spec view):
- `Variable.quantile` had signature `quantile(self, q, dim=None,
  interpolation="linear")` (no `keep_attrs`) and unconditionally returned
  `Variable(new_dims, qs)` — i.e. metadata `None` always (`variable.py:1595,1661`).
- `Dataset.quantile` delegated with `var.quantile(q, dim=reduce_dims,
  interpolation=interpolation)` — the keep flag was NOT forwarded
  (`dataset.py:4770-4772`), so the per-variable reduction received the default
  `None` and resolved it to "drop".

End-to-end caller (unchanged, context only): `DataArray.quantile`
(`xarray/core/dataarray.py:2827`) already accepted and forwarded `keep_attrs`
to `Dataset.quantile` via the temp dataset, so once both sites above honour
the flag the DataArray-level metadata survives — the F2P observable.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the attribute mapping `self._attrs` / `self.attrs` (`OrderedDict`/`dict`) and the result Variable's `attrs` | `List[int]` of code points (an opaque metadata payload) | the metadata payload is carried verbatim or dropped; the patch never inspects individual entries, so the touched behaviour is "copy the whole payload" vs "empty payload". `ToSeq(list)` materializes it as `PSeq[int]`; equal payload ⇔ equal `PSeq`. The F2P test asserts `out.attrs == self.attrs` (full-payload equality), which the carrier models exactly. |
| `attrs = self._attrs if keep_attrs else None` then `Variable(new_dims, qs, attrs)` — metadata `None` ⇔ empty `.attrs` | `selected_meta(src, keep)`: `src` when keep, `PSeq().take(0)` (empty) otherwise | `Variable(..., attrs=None)` yields an empty `.attrs` mapping, observationally equal to the empty payload `[]`. |
| `keep_attrs: bool = None` three-valued flag | `Optional[bool]` (`None` = unspecified) | identical three-valued domain. |
| the numeric reduction `np.nanpercentile(self.data, …)` and the dims bookkeeping (`new_dims`, `axis`, `q`) | omitted | the change is metadata-only; the numeric result `qs` and `new_dims` are computed identically before and after the patch and are observationally unchanged. axiom_check.py confirms the numeric values are untouched while the attrs vary with `keep_attrs`. |

`dict`/`OrderedDict` attribute access is not exercised element-wise by the
patch; the carrier therefore models the payload as a single `List[int]` whose
identity (copy vs empty) is the only observed property — exactly what the F2P
equality `out.attrs == self.attrs` tests.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `ambient_keep_default` ↔ `_get_keep_attrs(default=False)` (A-consumed)
**Callee:** `xarray.core.options._get_keep_attrs(default)`
(`xarray/core/options.py:61`):

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

The patched code calls it as `_get_keep_attrs(default=False)` only when
`keep_attrs is None`. The axiom encodes the **weakest** fact the proof needs:
under the **default ambient configuration** `OPTIONS["keep_attrs"] ==
"default"` (`options.py:21`), `_get_keep_attrs(default=False)` returns the
supplied default, `False`. Hence `ambient_keep_default() == False`.

**Flag dependency (recorded, like html.escape's quote=True):** the axiom is
sound only for `OPTIONS["keep_attrs"] == "default"`. Every F2P/P2P test runs
under this baseline — none of them mutates the global option around the
quantile call (the F2P `test_quantile` passes `keep_attrs=True` explicitly, so
the `None`→default branch is not even taken; the axiom matters for the
`keep_attrs=None` P2P-style paths). axiom_check.py fuzzes the resolver under
the default config (asserts `== False`) AND under the `True`/`False` global
settings (documents the boundary, so a future config change fails loud).
Docs/source: `xarray/core/options.py`.

This is the only consumed axiom. The metadata-selection itself
(`resolve_keep` + `selected_meta`) is modeled **deeply** (spelled out in the
`pure` region and the two impls); G-AX additionally validates that deep model
end-to-end against the real `Variable.quantile` / `DataArray.quantile`
(375 fuzz cases over attr payloads × keep flags × q shapes × interpolations).
