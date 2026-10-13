# refinement.md — sympy__sympy-19954

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`pruneParallelSystems` `do` block and the deep `keepByMask` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The prune site — `PermutationGroup.minimal_blocks` (`sympy/combinatorics/perm_groups.py:2197-2209`)

Gold hunk (the changed region):
```
-                to_remove = []
+                blocks_remove_mask = [False] * len(blocks)
                 for i, r in enumerate(rep_blocks):
                     if len(r) > len(rep) and rep.issubset(r):
                         # i-th block system is not minimal
-                        del num_blocks[i], blocks[i]
-                        to_remove.append(rep_blocks[i])
+                        blocks_remove_mask[i] = True
                     elif len(r) < len(rep) and r.issubset(rep):
                         minimal = False
                         break
                 # remove non-minimal representative blocks
-                rep_blocks = [r for r in rep_blocks if r not in to_remove]
+                blocks = [b for i, b in enumerate(blocks) if not blocks_remove_mask[i]]
+                num_blocks = [n for i, n in enumerate(num_blocks) if not blocks_remove_mask[i]]
+                rep_blocks = [r for i, r in enumerate(rep_blocks) if not blocks_remove_mask[i]]
```

| # | Solution.lean impl op (`pruneParallelSystems`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `blocks numBlocks repBlocks : List Int` | the three locals `blocks`, `num_blocks`, `rep_blocks` | R | each Python list of (descriptor / numbering-tuple / representative-set) ↔ `List Int` of opaque positional identifiers (mapping.md §2). G-CONF bridges by feeding identical integer lists to both sides. |
| A2 | param `removeFlags : List Bool` | `blocks_remove_mask = [False]*len(blocks)` then set `True` at flagged `i` by the comparison loop (`:2198-2206`) | R | the per-position removal decision ↔ `List Bool`. The comparison loop that *computes* the mask is UNCHANGED by the patch; its result is this read-only input (mapping.md §1, §3). |
| A3 | `keepByMask blocks removeFlags` | `blocks = [b for i, b in enumerate(blocks) if not blocks_remove_mask[i]]` | I | positional filter: keep entries whose flag is `False`. `keepByMask` IS this comprehension, transliterated (G-CONF). |
| A4 | `keepByMask numBlocks removeFlags` | `num_blocks = [n for i, n in enumerate(num_blocks) if not blocks_remove_mask[i]]` | I | same positional filter, SAME mask. |
| A5 | `keepByMask repBlocks removeFlags` | `rep_blocks = [r for i, r in enumerate(rep_blocks) if not blocks_remove_mask[i]]` | I | same positional filter, SAME mask. |
| A6 | `return (kept…, kept…, kept…)` | the three rebound locals after the hunk | R | tuple ordering ↔ the `(blocks, num_blocks, rep_blocks)` rebind (mapping.md §2). |

Discriminating content of the change — **all three parallel lists are filtered
by the SAME positional mask, so survivors stay index-aligned (equal length)** —
lives in the spec's three `keepByMask … removeFlags` equalities PLUS the two
length-equality postconditions (`out.1.length = out.2.1.length`,
`out.2.1.length = out.2.2.length`). The pre-patch instead (a) deleted from
`blocks`/`num_blocks` BY INDEX *during* iteration over `rep_blocks` — corrupting
the indices and raising `IndexError` once an earlier deletion shortens the lists
— and (b) filtered `rep_blocks` separately BY VALUE (`r not in to_remove`). The
two operations are not driven by one consistent positional mask, so the three
lists desynchronize. `Solution_prepatch.lean` reproduces the divergence (only
`repBlocks` mask-filtered; the other two left unfiltered) and **fails**
`out.1 = keepByMask blocks removeFlags` and the length-alignment clauses
(G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — replacing
mutate-during-iteration + value-filter with three consistent positional
mask-filters — is modeled **deeply** (`keepByMask`, steps A3–A5, all **I**),
not hidden behind an axiom. There are no consumed axioms and no A-reference deep
models: the slice calls no unchanged library function (the minimality comparison
is unchanged and outside the slice; its result is the input `removeFlags`).

## C. verify(Solution) ⇒ resolved

`pruneParallelSystems` verifies only if its three outputs equal the three
SAME-mask positional filters (A3–A5) and the survivor lengths stay equal
(alignment) — exactly the property the IndexError bug violated. By R
(`list ↔ List Int`, mask ↔ `List Bool`, tuple ordering) the verified operation
equals the gold patch's three list-comprehensions on the tested inputs; by
G-CONF the R/I transliteration of `keepByMask` agrees with `patch.diff`'s
behaviour over ≥10⁵ fuzzed `(lists, mask)` inputs (including the boundary that
crashed the pre-patch: a flagged position before the list end). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axiom trust
points (G-AX = skip); the sole trust point is refinement fidelity (this doc,
G-EQ + G-CONF).
