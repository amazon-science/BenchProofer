# mapping.md — sympy__sympy-23824

## Symbol binding (file:line @ base_commit 39de9a2698)

- Modeled behavior: the **final prepend step** of `kahane_simplify` in
  `sympy/physics/hep/gamma_matrices.py`, lines **695–698** @ base_commit.
  Gold patch replaces lines 697–698:
  ```python
  for i in range(0, first_dum_pos):
      [ri.insert(0, free_pos[i]) for ri in resulting_indices]
  ```
  with
  ```python
  resulting_indices = list( free_pos[0:first_dum_pos] + ri for ri in resulting_indices )
  ```

## What the changed slice computes

By the time control reaches line 695, the Kahane graph-walk (lines 472–688) has
already produced:
- `first_dum_pos : int` — number of **leading** gamma matrices that carry a free
  (uncontracted) index, sitting before the first contracted index
  (`first_dum_pos = min(map(min, dum))`, line 460).
- `free_pos : list` — length `total_number`; positions `0 .. first_dum_pos-1`
  hold the **index labels** of those leading free matrices (`free_pos[i[1]] = i[0]`
  for each free `i`, line 473–474). These leading positions are never `None`
  (they are exactly the leading free indices).
- `resulting_indices : list[list]` — the additive terms produced by the walk,
  each a list of index labels (`rows`).

The slice prepends the leading block `free_pos[0:first_dum_pos]` to **every** row.
The bug: `ri.insert(0, free_pos[i])` applied for `i = 0,1,…` prepends the labels
one at a time at the FRONT, which lays them down in **reverse** order
(`free_pos[first_dum_pos-1], …, free_pos[1], free_pos[0]`). The fix prepends the
slice `free_pos[0:first_dum_pos]` in its natural order.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python (@ base_commit) | Lean model | bijection |
|---|---|---|
| `first_dum_pos : int ≥ 0` | `firstDumPos : Nat` | identity |
| `free_pos : list` (leading slice) | `freePos : List Int` | each gamma index **label** ↦ a distinct `Int` id; only `free_pos[0:first_dum_pos]` is consumed and those entries are non-`None`, so they map to `Int` total |
| `resulting_indices : list[list]` | `rows : List (List Int)` | list of terms, each a list of index labels, same order |
| `free_pos[0:first_dum_pos]` | `freePos.take firstDumPos` | identity (Python slice ↦ `List.take`) |
| `[a] + ri` (list concat) | `lead ++ ri` (`List.append`) | identity |
| result `resulting_indices` | `List (List Int)` | identity |

The index **labels** are opaque identifiers for the reordering logic — the fix
only permutes their order, never their value — so modeling them as `Int` ids
loses nothing (`mapping`: gamma index `j` ↦ its integer slot, injective).

## Callee provenance / flag deps

None. The changed slice calls only Python builtins (`list`, slice `+`,
`list.insert`) whose Lean counterparts (`List.append`, `List.take`, `::`,
`List.map`) are concrete library ops. **No `opaque` callee, no consumed axiom**
(`axioms` region is empty; `axiom_check.py` is a skip stub).

## G-CONF fuzz seed

Pinned seed: **23824**. Fuzzer draws `firstDumPos ∈ [0,8]`, `freePos` of length
`firstDumPos + extra` (extra `∈ [0,4]`) with labels in `[-9,9]`, and `rows` a
list of `[0,6]` rows each of `[0,6]` labels in `[-9,9]`, over ≥10⁵ samples.
