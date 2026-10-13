# mapping.md — pydata__xarray-7233

## Symbol binding (file:line @ base_commit 51d37d1be95547059251076b3fadaa317750aab3)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_retainedCoordNames` / `problem_spec_retainedCoordNames` / `correct_retainedCoordNames` | the `should_be_coords` computation inside `Coarsen.construct` (the set of names re-promoted to coordinates of the reshaped result) | `xarray/core/rolling.py:976` (base_commit); rewritten to `xarray/core/rolling.py:976-979` post-patch |

## What the function does (base_commit)

`Coarsen.construct` reshapes a container by splitting each coarsened dimension
into two new dimensions, builds an intermediate dataset `reshaped`, and then
decides which names become coordinates of the result:

```python
        should_be_coords = set(window_dim) & set(self.obj.coords)
        result = reshaped.set_coords(should_be_coords)
```

Here `window_dim` is a mapping whose KEYS are the names of the dimensions being
reshaped, and `self.obj.coords` is the set of names that were coordinates of the
input. The line above keeps as coordinates only the names that are BOTH a
reshaped dimension AND a prior coordinate (`set(window_dim) & set(self.obj.coords)`).

The **bug**: a name that was a coordinate before the operation but is NOT itself a
reshaped dimension (a non-dimensional coordinate, e.g. `day` defined along the
coarsened `time` axis) is absent from `set(window_dim)`, so the intersection drops
it. `set_coords` therefore demotes it to a plain data variable. (Issue MVCE:
`day` becomes a data variable after `coarsen(time=12).construct(time=("year","month"))`.)

The **fix** unions the prior coordinate set back in:

```python
        should_be_coords = (set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)
```

Since `(W ∩ C) ∪ C = C`, the result is exactly `set(self.obj.coords)` — every
name that was a coordinate before stays a coordinate, independently of which
dimensions are reshaped.

## Lean modeling

- The modeled value is the set of names re-promoted to coordinates
  (`should_be_coords`), the sole observable the patch changes. It is a PURE
  function of two name collections the code reads: the reshaped-dimension names
  (`set(window_dim)`, i.e. the dict keys) and the prior coordinate names
  (`set(self.obj.coords)`).
- Inputs:
  `reshapedDims : List String` = `list(window_dim)` (the keys of the
  reshape mapping — the names of dimensions being split);
  `priorCoordNames : List String` = `list(self.obj.coords)` (the names that were
  coordinates of the input).
- Output: `result : List String` = the names of `should_be_coords` (the argument
  passed to `set_coords`). Order/multiplicity are irrelevant downstream
  (`set_coords` consumes a set), so the spec characterizes the result purely by
  MEMBERSHIP.
- The impl mirrors the post-patch set expression op-for-op:
  `set(window_dim) & set(self.obj.coords)` ↔
  `reshapedDims.filter (fun d => priorCoordNames.contains d)` (the common names),
  and `… | set(self.obj.coords)` ↔ `… ++ priorCoordNames` (union with the prior
  coordinate names). The `problem_spec` pins membership to `priorCoordNames`
  exactly — the set identity `(W ∩ C) ∪ C = C`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `list(window_dim)` (dict keys = reshaped dim names) | `reshapedDims : List String` | ordered list of names |
| `list(self.obj.coords)` (prior coordinate names) | `priorCoordNames : List String` | ordered list of names |
| `set(a) & set(b)` | `a.filter (fun x => b.contains x)` | as SETS: `{x ∈ a : x ∈ b}` (membership-equal; impl dedups via the set on the Python side, the Lean spec compares membership) |
| `s1 \| s2` (set union) | `xs1 ++ xs2` | as SETS: membership is the disjunction; the spec compares membership, not multiplicity |
| `should_be_coords` (a `set[str]`) | `result : List String` | a name is in the set iff it is in the list (membership bijection) |

`set_coords` and the whole `reshaped` construction are downstream of
`should_be_coords` and unchanged by the patch; only the set of names handed to
`set_coords` differs between pre- and post-patch, so that name set is the sole
modeled observable.

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The changed op is a pure set
  expression over two name collections; it is modeled DEEPLY (a filter followed
  by a union) over the observable inputs. SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op, so the `axioms` region is empty and **G-AX skips**.
- No flag dependencies: the `should_be_coords` line is unconditional (it does not
  depend on `keep_attrs`, dask, or `DataArray`-vs-`Dataset`; those affect other,
  unchanged, parts of `construct`).

## G-CONF fuzz seed

Pinned LCG seed: **7233** (see `conformance_check.py` `SEED`). Corpus: randomized
pairs of name lists — reshaped-dimension names and prior-coordinate names drawn
from a shared pool, with sizes crossing empty, singleton, and multi-name cases,
and overlaps ranging from disjoint to fully contained — over ≥1e5 fuzzed inputs.
The R/I shadow of `implementation_retainedCoordNames` is diffed (as SETS) against
an in-process replica of the POST-PATCH `should_be_coords` expression
(`(set(window_dim) & set(coords)) | set(coords)`). Hand-picked edge case pins the
F2P scenario: `reshapedDims=["time"]`, `priorCoordNames=["day"]` (a
non-dimensional coordinate) → the result set must still contain `day`.
