# mapping.md — pydata__xarray-3305

## Symbol binding (file:line @ base_commit 69c7e01e5167a3137c285cb50d1978252bb8bcbf)

Two changed functions in a caller→callee chain. The callee is the heart of the
fix; the caller threads the new flag into the callee. Both are modeled.

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_arrayQuantile` / `problem_spec_arrayQuantile` / `correct_arrayQuantile` | `Variable.quantile` (the callee) | `xarray/core/variable.py:1595-1661` |
| `implementation_collectionQuantile` / `problem_spec_collectionQuantile` / `correct_collectionQuantile` | `Dataset.quantile` (the caller, per-variable loop) | `xarray/core/dataset.py:4755-4772` |
| `newDims : List String` | `new_dims` — the dims that remain after reduction (+ a leading `"quantile"` when `q` is array-like) | `variable.py:1642-1656` |
| `qs : List Int` | `qs = np.nanpercentile(self.data, q*100, axis=axis, interpolation=...)` — the computed quantile value array | `variable.py:1658-1660` |
| `selfAttrs : Attrs` | `self._attrs` — the source variable's attribute mapping | `variable.py` (Variable `_attrs`) |
| `keepAttrs : Option Bool` | the `keep_attrs=None` parameter added to `Variable.quantile` | `variable.py:1595` (post-patch) |
| `globalDefault : Bool` | the value of `_get_keep_attrs(default=False)` — the resolved global option | `variable.py` (post-patch) ← `xarray/core/options.py:61-71` |
| `QResult` (`dims`, `data`, `attrs`) | the returned `Variable(new_dims, qs, attrs)` | `variable.py:1661` (post-patch `Variable(new_dims, qs, attrs)`) |
| `arrays : List SrcArray` | the variables looped over in `Dataset.quantile` that are reduced via `var.quantile(...)` | `dataset.py:4756-4772` |
| `SrcArray` (`dims`, `qs`, `attrs`) | one such variable, paired with its reduced `new_dims` and computed `qs` | per loop iteration |

The FAIL_TO_PASS test `test_dataarray.py::TestDataArray::test_quantile` calls
`DataArray(self.va).quantile(q, dim=dim, keep_attrs=True)` and asserts
`actual.attrs == self.attrs`. `DataArray.quantile` delegates to
`Dataset.quantile` (`dataarray.py:2875`), which loops calling `var.quantile`
(now with `keep_attrs=keep_attrs`); the underlying `Variable.quantile` now copies
`self._attrs` when `keep_attrs` is truthy. The DataArray's `attrs` come from that
variable. Both edits are on the path the test exercises.

### What the functions do

**`Variable.quantile` (base_commit, buggy):**
```python
def quantile(self, q, dim=None, interpolation="linear"):
    ...
    qs = np.nanpercentile(self.data, q * 100.0, axis=axis, interpolation=interpolation)
    return Variable(new_dims, qs)          # <-- attrs always dropped
```
The returned variable never carries the source's attributes; there is no
`keep_attrs` parameter at all.

**`Variable.quantile` (patched):**
```python
def quantile(self, q, dim=None, interpolation="linear", keep_attrs=None):
    ...
    qs = np.nanpercentile(self.data, q * 100.0, axis=axis, interpolation=interpolation)
    if keep_attrs is None:
        keep_attrs = _get_keep_attrs(default=False)
    attrs = self._attrs if keep_attrs else None
    return Variable(new_dims, qs, attrs)
```
The flag defaults from the global option when not given; the source attributes
are copied iff the (resolved) flag is truthy.

**`Dataset.quantile` (base_commit, buggy):** the per-variable call is
```python
variables[name] = var.quantile(q, dim=reduce_dims, interpolation=interpolation)
```
— `keep_attrs` is NOT forwarded, so every reduced variable defaults to the
global option (False), dropping its attributes even when the caller asked to
keep them.

**`Dataset.quantile` (patched):**
```python
variables[name] = var.quantile(
    q, dim=reduce_dims, interpolation=interpolation, keep_attrs=keep_attrs,
)
```
— forwards `keep_attrs` to the callee.

The reduction logic that produces `new_dims` and `qs` (`np.nanpercentile`, dim
removal, the leading `"quantile"` dim) is UNCHANGED by the patch and is taken as
the modeled inputs `newDims` / `qs`. The dataset-level attribute handling
(`dataset.py:4780-4782`) is unchanged and concerns the DATASET's own attrs (not
the per-variable attrs the test observes), so it is outside the modeled
behavior.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| an attribute mapping (`{'units':'K'}`, …) | `Attrs := List (String × String)` | a dict ↔ its (key,value) string pairs; only equality is observed (the test compares `actual.attrs == self.attrs`). |
| `self._attrs` | `selfAttrs : Attrs` | the source variable's attribute mapping. |
| `keep_attrs` parameter (`None`/`True`/`False`) | `keepAttrs : Option Bool` | `None ↔ none`; `True ↔ some true`; `False ↔ some false`. |
| `_get_keep_attrs(default=False)` result | `globalDefault : Bool` | the resolved global option (a bool); modeled input (unchanged callee). |
| `attrs = self._attrs if keep_attrs else None` | `result.attrs : Option Attrs` | `self._attrs ↔ some selfAttrs`; `None ↔ none`. |
| `new_dims` | `newDims : List String` | the remaining dimension names; modeled input (reduction unchanged). |
| `qs` (nanpercentile output) | `qs : List Int` | the computed quantile value array; modeled input, observed only by identity (frame-pinned, A-reference — the patch does not touch it). |
| `Variable(new_dims, qs, attrs)` | `QResult { dims, data, attrs }` | dims ↔ `new_dims`, data ↔ `qs`, attrs ↔ the (optional) copied attrs. |
| one looped variable in `Dataset.quantile` | `SrcArray { dims, qs, attrs }` | the reduced variable's remaining dims, computed quantile array, and source attrs. |

The observable the F2P test pins is `result.attrs`. The fix's point: for a
truthy resolved `keep_attrs`, `result.attrs = some selfAttrs` (the source attrs),
whereas pre-patch it is always `none`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The changed behavior (the `keep_attrs`
  defaulting + the `self._attrs if keep_attrs else None` selection + the caller's
  flag threading) is modeled DEEPLY over the inputs (SPEC_GUIDE §3 — a
  deeply-modeled changed op is never axiomatized). No external callee property is
  consumed by either proof, so the `axioms` region declares no `axiom
  <callee>_prop` and **G-AX skips**.
- `_get_keep_attrs(default=False)` (`options.py:61-71`) is **unchanged**; its
  resolved value is taken as the modeled input `globalDefault`. (When the caller
  passes an explicit `keep_attrs`, it is irrelevant; the F2P test passes
  `keep_attrs=True`.)
- `np.nanpercentile(...)` and the dim-reduction logic are **unchanged**; their
  outputs are taken as the modeled inputs `qs` / `newDims`. Exercised end-to-end
  by G-CONF (which drives the real patched functions).
- **Flag dependency:** the discriminating behavior is gated on the resolved
  `keep_attrs`. G-CONF fuzzes `keep_attrs ∈ {None, True, False}` crossed with
  the global option (so `globalDefault ∈ {True, False}`), and non-empty source
  attrs.

## G-CONF fuzz seed

Pinned LCG seed: **3305** (see `conformance_check.py` `SEED`). Corpus: randomized
draws over (a) `keep_attrs ∈ {None, True, False}`; (b) the global option ∈
{"default", True, False} (so `globalDefault ∈ {False, True}`); (c) non-empty vs
empty source attrs; (d) scalar vs array-like `q`; (e) reductions over a chosen
dimension, over ≥1e5 fuzzed inputs. The R/I shadow of the impls is diffed
against the REAL patched `Variable.quantile` / `Dataset.quantile` (via
`DataArray`/`Dataset` objects built on real numpy), observing `(dims, attrs)`.
Hand-picked edge case pins the discriminating clause: a source array with
non-empty attrs, `keep_attrs=True`, global option "default" (→ globalDefault
False) — pre-patch drops the attrs, post-patch keeps them.
