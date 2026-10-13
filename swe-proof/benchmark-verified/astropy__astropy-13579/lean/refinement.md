# refinement.md — astropy__astropy-13579

Operation correspondence between `implementation_assemble` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed: the changed operation (filling an omitted
world axis with its reference value) is modeled DEEPLY as positional placement
of an input reference vector. Every row is **R**, **A-reference**, or **I**. The
R/I/A-reference legs are differential-tested by G-CONF; G-AX is a skip stub (no
consumed callee axiom).

## `implementation_assemble` ↔ the `world_arrays_new` reassembly loop

The gold patch adds the reference vector and changes the omitted-axis fill:

```python
sliced_out_world_coords = self._pixel_to_world_values_all(*[0]*len(self._pixel_keep))  # NEW
...
for iworld in range(self._wcs.world_n_dim):
    if iworld in self._world_keep:
        iworld_curr += 1
        world_arrays_new.append(world_arrays[iworld_curr])
    else:
        world_arrays_new.append(sliced_out_world_coords[iworld])  # POST-PATCH (was `1.`)
```

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `let mut result := []` ; `let mut iworldCurr := 0` | `world_arrays_new = []` ; `iworld_curr = -1` | R | accumulator + kept-axis cursor. Python starts at `-1` and pre-increments on each kept axis; Lean starts at `0` and post-increments, so both name the same `c`-th supplied value `inputs[c]` for the `c`-th kept axis |
| `for iworld in [0:worldNDim] do` | `for iworld in range(self._wcs.world_n_dim):` | I | walk underlying world axes in order |
| `if iworld ∈ worldKeep then result := result ++ [inputs.getD iworldCurr 0]; iworldCurr := iworldCurr+1` | `if iworld in self._world_keep: iworld_curr += 1; world_arrays_new.append(world_arrays[iworld_curr])` | R | kept axis takes the next supplied value; `world_arrays` (len = slice world dim) ↦ `inputs : List Int`, positional |
| `else result := result ++ [slicedOut.getD iworld 0]` (the post-patch branch) | `else: world_arrays_new.append(sliced_out_world_coords[iworld])` | A-reference | the EDITED op: omitted axis takes its reference value (NOT the constant `1.`). Modeled deeply as positional placement of `slicedOut`; `slicedOut` itself is produced by the unchanged `_pixel_to_world_values_all` and validated == the real loop's behavior by G-CONF |
| `return result` | `world_arrays_new` (passed to `np.broadcast_arrays` then the inverse transform) | R | the reassembled length-`world_n_dim` vector ↦ `result : List Int`, entry `i` ↦ `result.getD i 0` |

The reassembled vector is the precise observable that distinguishes the bug: the
downstream inverse transform `self._wcs.world_to_pixel_values(*world_arrays_new)`
is unchanged, so any error in `world_arrays_new` on an omitted (dropped) axis
propagates into the returned kept pixels exactly when the underlying WCS couples
that dropped axis to a kept one. With the pre-patch constant `1.`, a coupled
dropped axis injects a wrong world value and the kept pixel blows up (the issue's
"essentially infinite" first pixel).

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: omitted axes are filled with the constant `1`
  (`(1 : Int)`) instead of `slicedOut`'s reference entry. The carried gold proof
  of `correct_assemble` fails to close on the omitted-axis clause
  (`result.getD iworld 0 = slicedOut.getD iworld 0` is violated wherever the
  reference value is not `1`). This is the single fixed behavior.
  (FAIL_TO_PASS: `test_coupled_world_slicing`.)
