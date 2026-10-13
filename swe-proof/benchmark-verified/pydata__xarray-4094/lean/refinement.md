# refinement.md — pydata__xarray-4094

Maps every operation in `implementation_toUnstackedDataset` to its `patch.diff`
counterpart in `DataArray.to_unstacked_dataset` (`xarray/core/dataarray.py:1900`,
changed loop at `:1961-1963`). Tags: **R** type-refinement, **A-consumed** proof
uses a callee axiom, **A-reference** op left as the real repo callee in G-CONF
(not axiomatized), **I** identical concrete op.

## Patch (post-patch loop)
```python
data_dict = {}
for k in variables:
    data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)
return Dataset(data_dict)
```
The behavioral content of the fix is the single token `drop=True` added to the
`sel(...)` call: each per-label slice is now extracted in the label-removing mode,
so the recombined dataset has no conflicting `variable_dim` scalar coordinate.

## Modeling decision
The observable behavior of the loop is: (i) the result lists exactly the variable
labels, in iteration order; (ii) each label is paired with the slice extracted in
the LABEL-REMOVING mode (`drop=True`), not the label-retaining default. The slice
extraction itself — `self.sel({variable_dim: k}, drop=mode).squeeze(drop=True)` —
is the unchanged work (the patch only flips `mode`), so it is modeled as an
arbitrary `extractSlice : Bool → κ → ν`, universally quantified, with the first
argument carrying the extraction mode. The spec pins only that `mode = true`
reaches the extraction for every label and that the result is the in-order
`(label, slice)` list. `Dataset(data_dict)` (the recombination) is faithfully
modeled by the association list `List (κ × ν)`; the `MergeError` the bug triggers
is *downstream* of the loop and is exactly what pinning `mode = true` prevents, so
it need not be modeled as a separate failure mode.

## Operation correspondence
| # | Lean op (`implementation_toUnstackedDataset`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut dataDict : List (κ × ν) := []` | `data_dict = {}` | R | the `{label: slice}` mapping ↔ an association `List (κ × ν)` (insertion-ordered, keys = labels). |
| 2 | `for k in vars do dataDict := dataDict ++ [(k, extractSlice true k)]` | `for k in variables: data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)` | R + A-reference | R: `for k in variables` ↔ `for k in vars`; dict assignment ↔ append of `(k, slice)`. The fixed token is `drop=True ↔ extractSlice true k` (label-removing mode). The extraction `sel(...).squeeze(...)` is the A-reference: left abstract (universally quantified) in spec/proof, bound to the REAL callee in G-CONF; no property consumed ⇒ NOT A-consumed and NOT deep-modeled. |
| 3 | `return dataDict` | `return Dataset(data_dict)` | R | recombine the per-label slices; `Dataset(·)` over a conflict-free mapping ↔ the association list itself (the patch's whole point is that, with `drop=True`, the mapping is conflict-free so the recombination succeeds). |

## R/I legs ⇒ G-CONF
Ops 1, 2 (mode resolution + list build, R), and 3 (return, R) are the R content.
The extraction in op 2 is the A-reference: G-CONF leaves it as the REAL
`self.sel({variable_dim: k}, drop=True).squeeze(drop=True)` callee (it does NOT
substitute an axiom model). `conf_skip = false`: the impl region has genuine R
content (building the in-order label→slice list under the resolved `drop=True`
mode is the fixed behavior), so `conformance_check.py` differential-tests the
shadow (loop over labels, extraction in `drop=True` mode, recombine) against the
real patched `DataArray.to_unstacked_dataset` over ≥1e5 fuzzed datasets,
comparing the resulting datasets with `.identical`.

## No A-consumed row
The proof consumes no property of `extractSlice` (it is universally quantified),
so `meta.json axioms = []`. The extraction is recorded as an A-reference solely to
document the G-CONF binding to the real callee; there is no `opaque`/`axiom`
declaration in `Solution.lean` and `axiom_check.py` is a skip stub.

## F2P alignment
`test_to_stacked_array_to_unstacked_dataset` adds the GH4049 regression: a dataset
of two single-dim variables `{"a", "b"}` is stacked then unstacked; the round-trip
must be `assert_identical(unstacked, data)`. With the buggy default extraction the
unstack raises `MergeError` (each slice keeps its `variable_dim` scalar). The
discriminating clause `problem_spec_toUnstackedDataset` pins each entry to
`extractSlice true k` (label-removing). The prepatch impl (the real bug:
`extractSlice false k`, i.e. `sel(...)` without `drop=True`) pairs every label
with the label-retaining slice, so its carried gold proof — which rewrites the
loop to `vars.map (fun k => (k, extractSlice false k))` — is not defeq to the
spec's `extractSlice true k` map and fails to typecheck (G-DIFF, confirmed: the
final `rw [forIn_collect_eq]` finds no matching pattern). `patch.diff` (gold
verbatim) makes the harness resolve.
