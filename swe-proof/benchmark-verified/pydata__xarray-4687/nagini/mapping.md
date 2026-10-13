# mapping.md — pydata__xarray-4687

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d3b6aa6d8b997df115a53c001d00222a0f92f63a`, states the type
abstraction, and gives the provenance of the axiom and the deep-model reference.

Repo file under change: `xarray/core/computation.py` (the function `where`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_payload(attrs, mode)` | `where(cond, x, y, keep_attrs)` — `xarray/core/computation.py:1730` (body 1811-1820) | the modeled changed function: it threads the attribute-handling mode into the underlying combine step (the patched `keep_attrs=keep_attrs` argument to `apply_ufunc`) |
| `default_mode_drops()` *(axiom — A-consumed)* | `_get_keep_attrs(default)` / `_get_boolean_with_default` — `xarray/core/options.py:107` / `:94` | unchanged global-option reader the patch calls when the mode is unspecified (`keep_attrs is None` ⇒ `keep_attrs = _get_keep_attrs(default=False)`) |
| `select_payload`'s PRESERVE branch (`ToSeq(Result()) == ToSeq(attrs[1])`) *(deep model — A-reference)* | `merge_attrs(variable_attrs, combine_attrs=<callable>)` — `xarray/core/merge.py:516` (callable branch line 522-523), driven by the installed combiner `lambda attrs, context: attrs[1]` (`computation.py` patched hunk) | the changed combine behaviour is modeled **deeply** as the positional-index-1 selection; validated `== merge_attrs(callable)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `empty_payload()` | the empty `dict()` returned by the `"drop"` branch of `merge_attrs` (`merge.py:525`) / `keep_attrs=False → "drop"` (`computation.py:1119-1120`) | pure spec: the empty attribute payload |
| `mode` (`int`: 0=DEFAULT, 1=PRESERVE) | the `keep_attrs` argument value: `None` (unspecified → DEFAULT) and `True` (PRESERVE) | the two F2P-relevant configurations |
| `attrs` (`List[List[int]]`, length 3) | `variable_attrs = [cond.attrs, x.attrs, y.attrs]`, the positional attrs list `apply_ufunc` hands to `merge_attrs` (`computation.py:302/458`) | positional operand payloads, index 0=cond, 1=x, 2=y |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an attribute mapping `dict` carried by an operand | `List[int]` opaque payload | payloads are compared by content equality; the only behaviour the F2P test observes is *which operand's payload is kept*, so the payload's internal structure is abstracted to a code-point/identity list. `{}` ↔ `[]` (empty). |
| the positional operand list `[cond.attrs, x.attrs, y.attrs]` | `List[List[int]]` of length 3 | index 0 ↔ cond, index 1 ↔ x, index 2 ↔ y (the order `where` passes to `apply_ufunc`: `cond, x, y`). |
| `keep_attrs` argument (`None` / `True` / `bool` / `str` / callable) | `mode: int` ∈ {0, 1} | `None` ↔ 0 (DEFAULT, the unspecified mode that resolves through `_get_keep_attrs`); `True` ↔ 1 (PRESERVE). The general `bool`/`str`/callable forms are not exercised by the F2P test and are out of the modeled domain (`Requires(mode == 0 or mode == 1)`). |
| `merge_attrs(...)` result `dict` | `Result()` payload (`List[int]`) | content equality; `{}` ↔ empty. |

xarray rich objects (`DataArray`/`Dataset`/`Variable`) and the elementwise
selection of *values* are irrelevant to the bug (values were already correct);
only the attribute payload's provenance is modeled. The `cond`/`x`/`y` value
arrays are abstracted away — only their attribute payloads enter the spec.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `default_mode_drops` ↔ `_get_keep_attrs(default=False)` (A-consumed)
**Callee:** `xarray.core.options._get_keep_attrs(default)` →
`_get_boolean_with_default("keep_attrs", default)` (`options.py:107`, `:94`).
Source at base_commit:

```python
def _get_boolean_with_default(option, default):
    global_choice = OPTIONS[option]
    if global_choice == "default":
        return default
    elif global_choice in [True, False]:
        return global_choice
    else:
        raise ValueError(...)

def _get_keep_attrs(default):
    return _get_boolean_with_default("keep_attrs", default)
```

The ambient global option is `OPTIONS["keep_attrs"] == "default"`
(`options.py:44`). Hence `_get_keep_attrs(default=False)` returns `False`, which
`apply_ufunc` maps to `"drop"` (`computation.py:1119-1120`: `keep_attrs =
"override" if keep_attrs else "drop"`), and `merge_attrs`'s `"drop"` branch
returns `{}` (`merge.py:524-525`). So when the mode is unspecified the result
carries the empty payload — exactly what the axiom `Ensures(Result() == True)`
(drops == True) encodes. The axiom is the **weakest** fact the proof needs (it
says nothing about non-default global options, which the F2P test does not set).

**Soundness check (G-AX):** `axiom_check.py::check_default_resolves_to_drop`
asserts `OPTIONS["keep_attrs"] == "default"` and `_get_keep_attrs(default=False)
is False` against the real installed xarray.

### 3.2 PRESERVE deep model ↔ `merge_attrs(callable)` (A-reference)
**Callee:** `xarray.core.merge.merge_attrs(variable_attrs, combine_attrs,
context)` (`merge.py:516`). Source at base_commit, callable branch:

```python
def merge_attrs(variable_attrs, combine_attrs, context=None):
    if not variable_attrs:
        return None
    if callable(combine_attrs):
        return combine_attrs(variable_attrs, context=context)
    ...
```

The patch installs the combiner `lambda attrs, context: attrs[1]` when the mode
is PRESERVE (`keep_attrs is True`), and `apply_ufunc` passes the positional
attrs list `[cond.attrs, x.attrs, y.attrs]` as `variable_attrs`
(`computation.py:302` / `:458`: `merge_attrs([x.attrs for x in objs], ...)`).
Because the combiner is `callable`, `merge_attrs` returns
`combiner([cond.attrs, x.attrs, y.attrs], context) = attrs[1] = x.attrs` — the
first-choice operand's payload at positional index 1. This is exactly the deep
model `ToSeq(Result()) == ToSeq(attrs[1])`. There is **no consumed axiom about
`merge_attrs`**; the index-1 selection is spelled out in `select_payload` and
validated equal to the real callee out-of-band.

The comment in the gold hunk states the intent: "keep the attributes of x, the
second parameter, by default to be consistent with the `where` method of
`DataArray` and `Dataset`" — i.e. `attrs[1]` is x.

**Soundness check (G-AX):** `axiom_check.py::check_preserve_selects_index_1_via_
merge_attrs` runs the real `merge_attrs` with the combiner on 6 boundary + 5000
fuzz payload lists and asserts the result equals positional index 1; and
`check_where_end_to_end` confirms on the real public `xr.where` that
`keep_attrs=True` keeps x's attrs (not cond's, not y's) and the unspecified
mode drops them — the exact F2P assertion.
