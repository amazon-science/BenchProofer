# refinement.md — sympy__sympy-19954

Every operation in `implementation_pruneSystems` (Solution.lean impl region)
mapped to its `patch.diff` (post-patch `minimal_blocks` inner block) counterpart.
Tags: **R** type refinement, **A-consumed** proof uses axiom property,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

| # | Lean impl op | patch.diff (post-patch) op | tag | note |
|---|---|---|---|---|
| 1 | `let mut minimal := true` | `minimal = True` | I | viability flag |
| 2 | `let mut mask : List Bool := []` | `blocks_remove_mask = [False]*len(blocks)` | R | the gold mask; Lean builds it incrementally during the scan, padding to full length after — same final mask (all later indices `False`) |
| 3 | `for r in repBlocks do` | `for i, r in enumerate(rep_blocks):` | R | enumerate index `i` is only used by the gold to index the mask; Lean appends in order so position is implicit |
| 4 | `if r.card > rep.card && rep ⊆ r` | `if len(r) > len(rep) and rep.issubset(r):` | R | `Finset.card`/`⊆` ↔ `len`/`issubset` |
| 5 | `mask := mask ++ [true]` | `blocks_remove_mask[i] = True` | R | mark index for removal (no in-loop mutation of the collections) |
| 6 | `else if r.card < rep.card && r ⊆ rep` | `elif len(r) < len(rep) and r.issubset(rep):` | R | candidate dominated |
| 7 | `minimal := false; break` | `minimal = False; break` | I | reject candidate, stop scan |
| 8 | `else mask := mask ++ [false]` | (implicit: index left `False`) | R | untouched system |
| 9 | `mask := mask ++ List.replicate (… - mask.length) false` | (gold mask already full length) | R | on `break`, Lean pads the un-scanned tail with `False`; matches the gold mask whose tail entries were initialized `False` and never set |
| 10 | `dropFlagged blocks mask` | `blocks = [b for i,b in enumerate(blocks) if not blocks_remove_mask[i]]` | R | aligned prune by the single mask |
| 11 | `dropFlagged numBlocks mask` | `num_blocks = [n for i,n in … if not blocks_remove_mask[i]]` | R | same mask |
| 12 | `dropFlagged repBlocks mask` | `rep_blocks = [r for i,r in … if not blocks_remove_mask[i]]` | R | same mask |
| 13 | `if minimal && !(numBlocks'.contains numBlock)` | `if minimal and num_block not in num_blocks:` | R | membership over the PRUNED `num_blocks` |
| 14 | `(blocks' ++ [block], numBlocks' ++ [numBlock], repBlocks' ++ [rep])` | `blocks.append(block); num_blocks.append(num_block); rep_blocks.append(rep)` | R | conditional append to all three |
| 15 | `else (blocks', numBlocks', repBlocks')` | (no append) | I | rejected / duplicate case |

No op is changed-inexpressible: the entire candidate-update step is modeled
deeply over lists/`Finset`. No A-consumed or A-reference rows — the impl region
is all R/I, so G-CONF (150k-fuzz, 0 disagreements) is the differential check and
G-AX is a skip stub. `meta.json conf_skip=false`.

## Prepatch divergence (G-DIFF)

`Solution_prepatch.lean` transliterates the PRE-PATCH bug: superseded systems
are deleted from `blocks`/`num_blocks` by a running index `i` (`eraseIdx i`)
*while the scan over `rep_blocks` is still running*, and `rep_blocks` is pruned
afterward by value. Once two systems are superseded the running index no longer
addresses the intended rows — the second `eraseIdx i` removes the wrong entry
(or, in the real Python, raises `IndexError` because the parallel list already
shrank). The buggy impl therefore disagrees with `problem_spec_pruneSystems`
exactly on inputs with ≥2 superseded systems (witnessed by a `decide` example
during construction), so its carried proof cannot close — G-DIFF fails the
prepatch as required.
