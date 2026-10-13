# mapping.md — sympy__sympy-19954

## Symbol binding (file:line @ base_commit)

- Modeled routine: the per-candidate update block inside
  `PermutationGroup.minimal_blocks(self, randomized=True)`,
  `sympy/combinatorics/perm_groups.py`.
  - method def: line 2133 @ base_commit
  - accumulator init: `blocks=[]`/`num_blocks=[]`/`rep_blocks=[]` lines 2175–2177
  - the modeled inner block (per-orbit candidate): lines 2187–2218
  - the comparison loop over `rep_blocks`: lines 2198–2206
  - the mutated-during-iteration deletions (the bug): line 2201
    `del num_blocks[i], blocks[i]` + 2202 `to_remove.append(rep_blocks[i])`
  - value-pruned `rep_blocks`: line 2208
  - conditional append: lines 2210–2213
- Gold patch replaces lines 2197–2208: introduces
  `blocks_remove_mask = [False]*len(blocks)`, sets `blocks_remove_mask[i]=True`
  on supersession (no in-loop deletion), and after the loop rebuilds `blocks`,
  `num_blocks`, `rep_blocks` by the same mask via list comprehensions.

## What is modeled

The Lean triple models exactly the candidate-update step: given the current
retained collections and a fresh candidate `(block, num_block, rep)`, produce
the next collections. The surrounding `minimal_blocks` scaffolding
(transitivity guard, stabilizer/orbit enumeration, `minimal_block`,
`_number_blocks`, the `rep` set construction) is OUTSIDE the modeled step — it
produces the inputs to the step and is not affected by the fix.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python (repo) | Lean (Solution.lean) | notes |
|---|---|---|
| `blocks : list[list[int]]` | `blocks : List (List Int)` | each entry carried opaquely; only position matters |
| `num_blocks : list[tuple[int,…]]` | `numBlocks : List (List Nat)` | tuple ↔ `List Nat`; entries non-negative; equality used for dedup |
| `rep_blocks : list[set[int]]` | `repBlocks : List (Finset Nat)` | set of points ↔ `Finset Nat` |
| candidate `block : list[int]` | `block : List Int` | |
| candidate `num_block : tuple[int,…]` | `numBlock : List Nat` | |
| representative cell `rep : set[int]` | `rep : Finset Nat` | |
| `len(r)` | `r.card` | `Finset.card` |
| `rep.issubset(r)` | `rep ⊆ r` | `Finset` subset |
| `del`/comprehension prune by mask | `dropFlagged xs mask` | drop where flag true |
| `num_block not in num_blocks` | `!(numBlocks'.contains numBlock)` | list membership |
| `blocks.append(block)` etc. | `blocks' ++ [block]` etc. | append |
| result triple | `List (List Int) × List (List Nat) × List (Finset Nat)` | |

The only behavior that distinguishes implementations is cardinality and the
subset relation among `rep` cells, and the index-alignment of the three
collections — all preserved exactly by the bijection.

## Callee provenance + flag deps

- No unchanged callee is consumed as an axiom or A-reference. The values
  `block`, `num_block`, `rep` are inputs to the modeled step (produced upstream
  by `minimal_block` / `_number_blocks`), not callees invoked inside it.
- The `randomized` flag of `minimal_blocks` only affects how `stab` (and hence
  the orbits feeding the candidates) is built; it does NOT affect the modeled
  candidate-update step, so it is irrelevant to the model.

## G-CONF fuzz seed

Pinned seed: **19954** (see `conformance_check.py` `SEED = 19954`, 150k inputs).
