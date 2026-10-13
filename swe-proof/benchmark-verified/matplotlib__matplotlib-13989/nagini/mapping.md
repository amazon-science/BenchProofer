# mapping.md — matplotlib__matplotlib-13989

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a3e2897bfaf9eaac1d6649da535c4e721c89fa69`, states the type
abstraction, and gives the provenance of the operation the deep model mirrors.

Repo file under change: `lib/matplotlib/axes/_axes.py` (method `Axes.hist`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_binning_options(multi_precomputed, density, stacked, range_value)` | the assembly of the local `hist_kwargs` dict inside `Axes.hist` — `lib/matplotlib/axes/_axes.py` from `hist_kwargs = dict()` (line 6654) through the `density and not stacked` branch (lines 6688-6689), as forwarded to `np.histogram(..., **hist_kwargs)` (line 6698) | the modeled changed behaviour: which keyword options the histogram routine forwards |
| `KEY_RANGE()` | the string key `'range'` placed by `hist_kwargs['range'] = bin_range` (line 6685) | option-name token for the explicit value range |
| `KEY_DENSITY()` | the string key `'density'` placed for the normalisation flag (line 6689, `dict(density=density)` pre-patch / `hist_kwargs['density'] = density` post-patch) | option-name token for the normalisation flag |
| `range_value` (param) | the local `bin_range` (a `(xmin, xmax)` tuple) assigned to `hist_kwargs['range']` (lines 6627-6628, 6659-6671, 6685) | the range value that must survive into the forwarded options |
| `multi_precomputed` (param) | the truth of `not input_empty and len(x) > 1` — the branch that pre-computes shared bins via `histogram_bin_edges(...)` instead of recording a range (lines 6676-6683) | selects whether the range key is recorded at all |
| `density` (param) | the resolved `density = bool(density) or bool(normed)` (line 6687) | whether normalisation is requested |
| `stacked` (param) | the local `stacked` (lines 6604-6605, the `stacked` argument) | whether datasets are stacked |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `hist_kwargs` (a Python `dict` of keyword options) | `Dict[int, int]` from an option-name token to its recorded value | a string key ↔ an int token (`'range'` ↔ `KEY_RANGE()==0`, `'density'` ↔ `KEY_DENSITY()==1`); `k in hist_kwargs` ↔ `tok in result`; only membership and per-key value are observed |
| `bin_range` (a `(xmin, xmax)` float tuple) | `range_value : int` (opaque token) | only the *preservation* of the range entry is observed (does the forwarded dict still carry the range supplied), not its numeric content; an int token is a faithful identity-only carrier |
| the normalisation flag `density` (a Python `bool`, truthy in this branch) | the value `1` stored under `KEY_DENSITY()` | the branch fires only when `density` is truthy, so the recorded flag is the constant truthy `1` |
| the runtime branch conditions (`not input_empty and len(x) > 1`, `density and not stacked`) | explicit `bool` parameters | each condition is computed upstream from inputs the model does not need to re-derive; abstracted to the boolean it evaluates to |

`dict` rebinding/mutation is the operation under change; the carrier is a Nagini
`Dict[int, int]` under `dict_pred`. The routine *builds and returns* the freshly
created options mapping, mirroring the real `hist_kwargs` local that is assembled
before being forwarded to `np.histogram`.

## 3. Provenance of the modeled operation (checked by G-AX / axiom_check.py)

### 3.1 `assemble_binning_options` deep model ↔ the real `Axes.hist` kwargs assembly (A-reference)

There is **no consumed `@ContractOnly` axiom**: the changed operation — building
the `hist_kwargs` mapping forwarded to `np.histogram` — is modelled **deeply**
(the two guarded writes spelled out in the impl region). The deep model is
validated **== the real operation** out-of-band by `axiom_check.py` (G-AX).

Real source at `base_commit` (`lib/matplotlib/axes/_axes.py`, `Axes.hist`):

```python
hist_kwargs = dict()                                   # 6654
...
if not input_empty and len(x) > 1:                     # 6676  multi-dataset: precompute bins
    bins = histogram_bin_edges(np.concatenate(x), bins, bin_range, _w)
else:                                                  # 6684  single-pass: record the range
    hist_kwargs['range'] = bin_range                   # 6685
density = bool(density) or bool(normed)                # 6687
if density and not stacked:                            # 6688
    hist_kwargs = dict(density=density)                # 6689  PRE-PATCH (bug): rebinds, drops 'range'
    #   gold fix:  hist_kwargs['density'] = density            #         mutates, keeps 'range'
...
m, bins = np.histogram(x[i], bins, weights=w[i], **hist_kwargs)   # 6698
```

The behaviour the deep model encodes: the forwarded options mapping carries the
range entry exactly in the single-pass case (`not multi_precomputed`) and carries
the density entry exactly in the `density and not stacked` case, and these two
are **independent** — recording density does not discard a previously recorded
range. In the pre-patch tree the `density and not stacked` branch *rebinds*
`hist_kwargs` to a brand-new one-key dict, so the `'range'` recorded at line 6685
never reaches `np.histogram`; the histogram then computes its own bin edges from
the data instead of the requested interval. The gold patch changes the rebind to
an in-place write, preserving `'range'`.

**Why the observable matters (F2P `test_hist_range_and_density`):**
`plt.hist(np.random.rand(10), "auto", range=(0, 1), density=True)` takes the
single-dataset path (`len(x) == 1`, so `not multi_precomputed`), records
`hist_kwargs['range'] = (0, 1)`, then enters the `density and not stacked`
branch. With the range preserved, `np.histogram(data, "auto", range=(0, 1),
density=True)` returns bin edges spanning `[0, 1]`, so `bins[0] == 0` and
`bins[-1] == 1`. With the range dropped (pre-patch), the edges follow the data
and neither holds. This is exactly the discriminating clause
`Implies(not multi_precomputed, KEY_RANGE() in Result() and
Result()[KEY_RANGE()] == range_value)` on which `model_prepatch.py` fails.

**Soundness check (G-AX):** `axiom_check.py` reconstructs the real `Axes.hist`
kwargs-assembly logic (both the gold and the base_commit rebind) over boundary +
fuzz boolean combinations and asserts the resulting key set matches the deep
model; and it drives the **real** `numpy.histogram` with the assembled kwargs to
confirm the observable the deep model relies on (range preserved ⟹ bins span the
interval; range dropped ⟹ they do not). Imports: the standard library plus
`numpy` (the library `Axes.hist` forwards the kwargs to). Exit 0 iff sound.
