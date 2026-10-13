# refinement.md — pydata__xarray-7233

The operation-by-operation correspondence between `model.py`'s implementation
(the `rebuild_label_status` loop and the deep `promoted` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == a real callee by G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed site — `Coarsen.construct` coordinate restoration

Gold hunk (`xarray/core/rolling.py`):
```
-        should_be_coords = set(window_dim) & set(self.obj.coords)
+        # should handle window_dim being unindexed
+        should_be_coords = (set(window_dim) & set(self.obj.coords)) | set(
+            self.obj.coords
+        )
         result = reshaped.set_coords(should_be_coords)
```

The fresh `reshaped` Dataset is built by re-inserting every variable of the
original object (`rolling.py:964-974`). That insertion is not status-neutral:
it routes through `merge_core`, which at `merge.py:767-768` adds to
`coord_names` any inserted variable whose name equals one of the container's own
dimension names. `set_coords` then ADDS the names in `should_be_coords`
(`dataset.py:1710`, `_coord_names.update`, which never resets). So the result's
coordinate-name set is the UNION of those two steps, and the change widens the
`should_be_coords` half from `window_dim ∩ coords` to `(window_dim ∩ coords) ∪
coords`. The insertion half is untouched by the patch and behaves identically
before and after it.

| # | model.py impl op (`rebuild_label_status`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameters `was_label`, `is_window`, `is_axis_name : List[int]` of 0/1 flags over members `0..n-1` | the name iterables `set(self.obj.coords)` and `set(window_dim)`, plus the coincidence between a member's insertion name and `reshaped`'s own dimension names | R | a name's membership in each set ↔ the 0/1 bit at that member's index (mapping.md §2). The name universe is fixed across the transform, so the bit lists have a stable common length `n`. |
| 2 | `wl == 1 and iw == 1` ⟶ the AND clause of `promoted` | `set(window_dim) & set(self.obj.coords)` (membership of member's name in the intersection) | R | set intersection ↔ pointwise bit-AND (mapping.md §2). |
| 3 | the second `if wl == 1: sel = 1` clause of `promoted` (OR with the prior labelling bit) | `... | set(self.obj.coords)` (union with the full coordinate set) | R | set union ↔ pointwise bit-OR; the bug fix is exactly this added disjunct (mapping.md §2). The model `promoted` returns the union of the two, matching `(A & B) | B`. |
| 3b | the third `if ax == 1: sel = 1` clause of `promoted` | the insertion step's own effect: `merge_core` adds to `coord_names` any inserted name equal to one of `reshaped`'s dimension names (`merge.py:767-768`, reached from `rolling.py:964-974` via `dataset.py:1483,4923`) | R | membership in `reshaped`'s dimension-name set ↔ the `is_axis_name` bit; the OR with the other legs is the union `set_coords` produces because `_coord_names.update` ADDS (`dataset.py:1710`). Unchanged callee, identical pre- and post-patch. |
| 4 | the loop builds `result[k] == promoted(was_label[k], is_window[k], is_axis_name[k])` for every member and returns it | `result = reshaped.set_coords(should_be_coords)` — the result's coordinate-name set becomes `reshaped._coord_names` ∪ `should_be_coords` | R | `set_coords` (unchanged callee, `dataset.py:1683`) UNIONS `should_be_coords` into the coordinate names the insertion step already established; refined to "`Result()[k] == 1` iff member `k` is in that union" (mapping.md §2, §3). Pure type refinement of unchanged callees — no axiom consumed. |
| 5 | DataArray vs Dataset: the same per-member computation, over the name each member is INSERTED under | `if isinstance(self.obj, DataArray): return self.obj._from_temp_dataset(result) else: return result` (`rolling.py:978-981`), with `_to_temp_dataset` at `rolling.py:957-958` | R | the two arms reach different naming code: on the DataArray arm the array member is inserted under the container's internal placeholder (`dataarray.py:222,530-531`), not under its own name, so its `is_axis_name` bit is 0 even when its name equals a rebuilt axis name. `is_axis_name[k]` is defined on the insertion name (mapping.md §2), which makes one expression cover both arms; `conformance_check.py` exercises each arm separately. |
| 6 | `Requires(MustTerminate(2))` on `rebuild_label_status`; loop `Invariant(MustTerminate(len(was_label) - i + 1))` | the real rebuild (the insertion loop plus `set_coords` over the fixed finite name universe) is a bounded computation that always returns its result to the caller | R | total-correctness obligation: the real operation always ANSWERS. Nagini verifies partial correctness by default, so without this obligation a diverging same-spec impl (`while True:` before ever building `result`) satisfies both value postconditions vacuously — the audited G-PANEL-1 counterexample class. The loop consumes the obligation with the strictly decreasing, bounded-below measure `len(was_label) - i`. |

## The discriminating property

The model `promoted(was_label, is_window, is_axis_name)` returns
`(was_label ∧ is_window) ∨ was_label ∨ is_axis_name`, which equals
`was_label ∨ is_axis_name` for any 0/1 input (the union disjunct subsumes the
intersection). The spec postconditions therefore pin:
1. `Result()[k] == promoted(was_label[k], is_window[k], is_axis_name[k])` — the
   result coords are the per-member union selection; and
2. `was_label[k] == 1 → Result()[k] == 1` — prior labelling/coordinate status is
   PRESERVED across the transform (every prior coordinate stays a coordinate),
   which is exactly the behaviour the issue demands ("all variables that were
   coordinates before stay coordinates afterwards") and what the F2P test
   `test_coarsen_construct_keeps_all_coords` checks (`list(da.coords) ==
   list(result.coords)`); and
3. `is_axis_name[k] == 1 → Result()[k] == 1` — the container's standing
   axis-name property (step 3b), which holds identically pre- and post-patch; and
4. `was_label[k] == 0 ∧ is_axis_name[k] == 0 → Result()[k] == 0` — nothing else
   is promoted, so a data variable stays a data variable. Clauses 2-4 partition
   the domain and pin every output bit, so the spec is an equality, not a
   one-sided bound: an impl cannot satisfy them and differ from the gold.

Clause 2 alone is the direction the patch changes; clauses 3 and 4 state what the
unchanged callees guarantee, and without clause 3 the spec would demand the
opposite of what the real rebuilt container does on the axis-name sub-domain.

`model_prepatch.py` keeps the spec **byte-identical** and reverts the impl to
the pre-patch selection `should_be_coords = set(window_dim) & set(self.obj.coords)`
(per member: `sel = (was_label ∧ is_window) ∨ is_axis_name`, omitting the union
with all prior labels while keeping the insertion step, which the patch does not
change). It FAILS verification on postcondition (1)/(2): for a member that was a
coordinate, whose name is NOT one of the windowed axes, and whose insertion name
is not one of the rebuilt container's axis names (`was_label=1, is_window=0,
is_axis_name=0`), the pre-patch impl yields `0 ≠ promoted(1,0,0)=1`. That is
precisely the demoted-non-dimensional-coordinate bug the spec senses (G-DIFF).

## No kind-3, no axiom

Every step is R or I. The one operation that genuinely *changed* — the
membership computation deciding which members stay coordinates — is modeled
**deeply** (`promoted` + the verified loop spell out the per-member union
selection), not hidden behind an axiom. There is **no `@ContractOnly` axiom**
(consumed or reference): the callees involved — `Dataset.__setitem__`/`update`/
`merge_core`, `Dataset.set_coords`, and the DataArray temp-dataset round trip —
are all unchanged by the patch and handled by the set⟶bit type refinement
(steps 3b, 4, 5), so there is no G-AX obligation. `set` `&`/`|` are total pure
built-ins refined pointwise.

## verify(model) ⇒ resolved

`rebuild_label_status` verifies only if every member's result bit equals the
union selection `(was_label ∧ is_window) ∨ was_label ∨ is_axis_name` (steps
2-3b), and clauses 2-4 of the discriminating property partition the domain, so
no position is left free. By R (set ↔ bit, insertion-step promotion ↔ the
`is_axis_name` leg, `set_coords` ↔ coordinate-set union, steps 3b-5) the verified
per-member status equals the coordinate-name set produced by
`reshaped.set_coords((set(window_dim) & set(self.obj.coords)) |
set(self.obj.coords))` on the tested inputs — i.e. the gold patch up to type
refinement. G-CONF checks this on 100023 inputs including 11595 that exercise the
axis-name sub-domain. The gold patch resolves
(G-RESOLVE). The sole trust point is refinement fidelity (this document, G-EQ);
there is no axiom-soundness trust point because nothing is axiomatized.
