# mapping.md — pydata__xarray-7233

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 51d37d1be95547059251076b3fadaa317750aab3`, states the type
abstraction, and explains why no callee is axiomatized.

Repo file under change: `xarray/core/rolling.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rebuild_label_status(was_label, is_window, is_axis_name)` | the whole rebuild tail of `Coarsen.construct` — the per-variable insertion loop `xarray/core/rolling.py:964-974` TOGETHER WITH the `should_be_coords = ...` computation feeding `reshaped.set_coords(should_be_coords)` (`rolling.py:976-977`) | the modeled changed behaviour: which members of the rebuilt container are coordinates |
| `promoted(was_label, is_window, is_axis_name)` | the per-member decision: the name lands in `should_be_coords` (`(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)`, `rolling.py:976` post-patch) OR it was already in `reshaped._coord_names` after insertion, which `merge_core` sets for any inserted name equal to one of `reshaped`'s dimensions (`xarray/core/merge.py:767-768`) | pure spec: the labelling status one member ends with |
| `Result()` (the returned `List[int]` of 0/1 flags) | the coordinate-name set of the value returned by `set_coords(should_be_coords)` (`rolling.py:977`) | the result's per-member coordinate status |

The `construct` method whose tail is modeled is the base
`Coarsen.construct` (`xarray/core/rolling.py:880`), shared by
`DataArrayCoarsen` / `DatasetCoarsen`. The DataArray path round-trips through
`_to_temp_dataset()` / `_from_temp_dataset()` (`rolling.py:957-958,978-979`),
so the coordinate-name set is what is preserved in both cases (this is exactly
what the F2P test checks for both a DataArray and its `to_dataset()`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the ordered collection of variable names in `obj.variables` (the members re-inserted into the fresh `reshaped` Dataset, `rolling.py:964-974`) | the index set `0 .. n-1` of the parallel `List[int]` | member `k` ↔ the `k`-th variable name |
| `name ∈ set(self.obj.coords)` (the variable was a coordinate before the transform) | `was_label[k] == 1` (else `0`) | coordinate-name membership ↔ the 0/1 bit |
| `name ∈ set(window_dim)` (the name is one of the dimensions being coarsened / windowed) | `is_window[k] == 1` (else `0`) | window-dim membership ↔ the 0/1 bit |
| the name member `k` is INSERTED under in `reshaped` is one of `reshaped`'s own dimension names | `is_axis_name[k] == 1` (else `0`) | see the insertion-name note below |
| `reshaped._coord_names` after the insertion loop, unioned with `should_be_coords` ⟶ the result's coordinate-name set | `Result()` (the 0/1 coordinate-status flags) | `name ∈ result.coords` ↔ `Result()[k] == 1` |
| `set` intersection `&` / union `|` over the name sets | per-member boolean AND / OR over the parallel bits | `(A & B)` ↔ pointwise `min`; `(A | B)` ↔ pointwise `max` |

Justification of the set ⟶ pointwise-bit refinement. The rebuild has TWO steps
that decide coordinate status, and the model has a leg for each.

*Step 1 — insertion.* `reshaped[key] = ...` (`rolling.py:964-974`) routes through
`Dataset.__setitem__` → `Dataset.update` → `dataset_update_method` → `merge_core`
(`dataset.py:1483,4923`; `merge.py:1104,755`). `merge_core` computes the merged
`dims` and then, at `merge.py:767-768`, does
`for dim, size in dims.items(): if dim in variables: coord_names.add(dim)` —
i.e. the container itself makes any inserted variable whose name equals one of
the container's own dimension names a coordinate, whatever its prior status.
Because the reshape gives the members the rebuilt container's dimension names,
this is a standing property of the container, not a choice the rebuild makes;
it is code the patch does not touch and it applies identically before and after
the patch. `is_axis_name[k]` is that condition's membership bit.

*Step 2 — restoration.* `set_coords(names)` then adds `names` to the
coordinate-name set (`dataset.py:1683-1711`; the effect is only
`_coord_names.update(names)`, which ADDS and never resets). So the result's
coordinate set is `reshaped._coord_names` (step 1) ∪ `should_be_coords`
(step 2) — a union, and the model's `promoted` is exactly that union pointwise.
`set_coords` requires every name be present, satisfied because every original
variable (coords included) was copied into `reshaped`.

*Insertion names differ by arm.* On the Dataset arm a member is inserted under
its own name. On the DataArray arm `construct` first calls `_to_temp_dataset()`
(`rolling.py:957-958`), which inserts the array member under the container's
internal placeholder name `_THIS_ARRAY` (`dataarray.py:222,530-531,558-585`)
rather than the array's own name, and `_from_temp_dataset` (`dataarray.py:533-539`)
pops that placeholder back out. So on that arm the array member's
`is_axis_name` bit is decided by the placeholder, which is never a dimension
name, and an array whose own name happens to equal a rebuilt axis name is NOT
promoted. `is_axis_name[k]` is therefore the bit for the name member `k` is
*inserted under*, and the two arms genuinely reach different naming code;
`conformance_check.py` follows each arm to the name it uses and re-derives the
rebuilt-axis set from the realized output on every case (`axis_bridge` check),
so the bridge is checked rather than assumed.

The transform reshapes dimensions but never adds, drops, or renames a member's
*name*, so the member name set, the `obj.coords` membership, the `window_dim`
membership, and the insertion-name/axis-name coincidence are all order-stable
and modeled as fixed-length parallel bit lists. Set operations on names become
pointwise boolean operations on the membership bits — an exact bijection on the
finite name universe.

`is_window[k]` is the membership bit for the *windowed* axes (`window_dim`);
the spec leaves it unconstrained beyond its role as a flag, because the fixed
behaviour does not depend on it (every prior coordinate is kept regardless),
which is precisely the property the issue demands. `is_axis_name[k]` is not
derivable from the other two bits — it is a third, independent input, which is
why the modeled function takes it explicitly rather than folding it in.

## 3. Callees and axioms

**No `@ContractOnly` axiom is shipped.** The changed operation is the *selection
of which members become coordinates* — modeled DEEPLY as the per-member
`promoted` function and the verified loop. The real callees the patched line
invokes are:

- Python `set` intersection/union (`&`, `|`) and `set(...)` construction over
  the name iterables — pure, total, deterministic; refined to pointwise bit
  operations (§2), not axiomatized.
- `Dataset.__setitem__` → `Dataset.update` → `merge_core`
  (`dataset.py:1483,4923`; `merge.py:755,767-768`) — UNCHANGED by the patch.
  Its only effect on the observable property is that an inserted variable whose
  name equals one of the container's dimension names is added to `coord_names`;
  modeled as the `is_axis_name` leg of `promoted`. A type refinement of an
  unchanged callee, not an axiom.
- `Dataset.set_coords(names)` (`xarray/core/dataset.py:1683`) — UNCHANGED by the
  patch. Its only effect on the observable property is
  `_coord_names.update(names)` (line 1710), which ADDS to whatever coordinate
  names the insertion step already established and never resets them; modeled as
  the `was_label` leg of `promoted`, unioned with the `is_axis_name` leg. This is
  a type refinement of an unchanged callee, not an axiom the proof consumes.
- `DataArray._to_temp_dataset` / `_from_temp_dataset`
  (`dataarray.py:530-539,558-585`) — UNCHANGED. They decide which name the array
  member is inserted under on the DataArray arm; modeled by the insertion-name
  note in §2.

Because nothing is axiomatized, there is no G-AX obligation for this bundle
(no `@ContractOnly`); `axiom_check.py` is therefore not required. The soundness
of the set⟶bit refinement (§2) is a refinement-fidelity claim audited by G-EQ,
and the shipped gold `patch.diff` is confirmed by G-RESOLVE.
