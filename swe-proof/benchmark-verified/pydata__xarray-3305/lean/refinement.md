# refinement.md — operation correspondence (pydata__xarray-3305)

Each op of the two impls ↔ its `patch.diff` counterpart.
Tags: **R** type refinement, **A-consumed** axiom property consumed by proof,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

## `implementation_arrayQuantile` ↔ `Variable.quantile` (callee, `variable.py`)

| # | Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut keep := keepAttrs; if keep.isNone then keep := some globalDefault` | `if keep_attrs is None:\n    keep_attrs = _get_keep_attrs(default=False)` (added) | R | The optional keep request is defaulted to the resolved global option. `None ↔ none`; `_get_keep_attrs(default=False) ↔ globalDefault`. |
| 2 | `let attrs := if keep.getD globalDefault then some selfAttrs else none` | `attrs = self._attrs if keep_attrs else None` (added) | R | The source attributes are kept iff the resolved request is truthy. `self._attrs ↔ some selfAttrs`; `None ↔ none`. After op 1 `keep` is never `none`, so `keep.getD globalDefault = resolveKeepAttrs keepAttrs globalDefault`. |
| 3 | `return { dims := newDims, data := qs, attrs := attrs }` | `return Variable(new_dims, qs, attrs)` (changed from `Variable(new_dims, qs)`) | R | The result carries the reduction `(new_dims, qs)` plus the (optional) attrs. `new_dims ↔ newDims`, `qs ↔ qs`. dims/data frame-pinned to inputs (§0.5). |

`newDims` and `qs` are the UNCHANGED reduction outputs (`np.nanpercentile` + dim
removal), taken as modeled inputs and pinned to the result by the spec
(frame). The patch does not touch them.

## `implementation_collectionQuantile` ↔ `Dataset.quantile` (caller loop, `dataset.py`)

| # | Lean op | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 4 | `for a in arrays do … out := out.push r` | `for name, var in self.variables.items(): … variables[name] = var.quantile(...)` | R | The per-variable reduction loop. Only the reduced/aggregated members are modeled (`arrays`); the carrier dict ↔ ordered list. |
| 5 | `implementation_arrayQuantile a.dims a.qs a.attrs keepAttrs globalDefault` | `var.quantile(q, dim=reduce_dims, interpolation=interpolation, keep_attrs=keep_attrs)` (the added `keep_attrs=keep_attrs`) | R | The fix: the SAME caller keep request is forwarded to each member's reduction (`keep_attrs=keep_attrs`), rather than omitted. Calls `implementation_arrayQuantile` directly (callee-under-spec). |
| 6 | `return out.toList` | `variables` dict handed on to dataset construction | R | The collection of per-member results. Dataset-level attr handling (`dataset.py:4780-4782`) concerns the dataset's OWN attrs, not the per-member attrs the F2P test observes — out of scope. |

Every op is **R** (type refinement). There are **no A-consumed axioms** (no
external callee contract is consumed — `_get_keep_attrs`, `np.nanpercentile`, and
dim reduction are taken as modeled inputs `globalDefault`/`qs`/`newDims`; see
mapping.md callee provenance) and **no A-reference** deep-model callees beyond
those inputs. There is no changed-inexpressible op: the entire fix is the
keep-attrs defaulting + attribute selection (ops 1–3) plus the caller's flag
forwarding (op 5), all modeled deeply over `Attrs`/`QResult`.

`conf_skip = false` — both impl regions are all-R (no A-tagged ops), so G-CONF
mechanically differential-tests them against the real patched `Variable.quantile`
/ `Dataset.quantile`.
