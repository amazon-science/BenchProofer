# refinement.md — sympy__sympy-19954

The operation-by-operation correspondence between `model.py`'s implementation
(the `prune_parallel` impl region plus the deep `filtered` / `kept` folds) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real operation by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The prune site — `minimal_blocks` inner loop (`sympy/combinatorics/perm_groups.py:2194-2213`)

Gold hunk (the load-bearing change):
```
-                to_remove = []
+                blocks_remove_mask = [False] * len(blocks)
                 for i, r in enumerate(rep_blocks):
                     if len(r) > len(rep) and rep.issubset(r):
-                        del num_blocks[i], blocks[i]
-                        to_remove.append(rep_blocks[i])
+                        blocks_remove_mask[i] = True
                     elif len(r) < len(rep) and r.issubset(rep):
                         minimal = False
                         break
-                rep_blocks = [r for r in rep_blocks if r not in to_remove]
+                blocks = [b for i, b in enumerate(blocks) if not blocks_remove_mask[i]]
+                num_blocks = [n for i, n in enumerate(num_blocks) if not blocks_remove_mask[i]]
+                rep_blocks = [r for i, r in enumerate(rep_blocks) if not blocks_remove_mask[i]]
```

| # | model.py impl op (`prune_parallel`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `blocks, nums, reps : List[int]` | the locals `blocks`, `num_blocks`, `rep_blocks` (`perm_groups.py:2175-2177`) | R | each candidate's partition/numbering/representative is an opaque identity; the prune observes only identity & position. `list[partition]`/`list[tuple]`/`list[set]` ↔ `List[int]` (mapping.md §2). |
| A2 | param `flag : List[bool]` | the per-index removal decision; post-patch the literal `blocks_remove_mask = [False]*len(blocks)` set to `True` at the flagged positions (`perm_groups.py:2197,2201`) | R | the decision `len(r) > len(rep) and rep.issubset(r)` is UNCHANGED by the patch and abstracted into the opaque boolean input; the spec admits every assignment, so it covers the prune for any decision the unchanged scan produces. |
| A3 | `out_reps == filtered(ToSeq(reps), ToSeq(flag))` (the survivors of `reps` where `flag` is False, computed by the backward loop) | `rep_blocks = [r for i, r in enumerate(rep_blocks) if not blocks_remove_mask[i]]` | A-reference | the mask filter on `rep_blocks` is modelled DEEPLY by `filtered`; validated == the real comprehension by G-AX (axiom_check.py). |
| A4 | `out_blocks == filtered(ToSeq(blocks), ToSeq(flag))` | `blocks = [b for i, b in enumerate(blocks) if not blocks_remove_mask[i]]` | A-reference | same deep model `filtered`, same shared `flag`; validated by G-AX. |
| A5 | `out_nums == filtered(ToSeq(nums), ToSeq(flag))` | `num_blocks = [n for i, n in enumerate(num_blocks) if not blocks_remove_mask[i]]` | A-reference | same deep model `filtered`, same shared `flag`; validated by G-AX. |
| A6 | `len(out_blocks) == len(out_nums) == len(out_reps) == kept(ToSeq(flag))` | implied by the three comprehensions sharing one mask | A-reference + I | parallel alignment is the spec's discriminating consequence; `kept` is the deep model of the common survivor count, validated == the real comprehension lengths by G-AX. |

The discriminating content of the change — **all three parallel lists pruned by
ONE shared per-position mask taken from a single snapshot, so they stay aligned**
— lives in the conjunction of A3/A4/A5 sharing the single `flag` plus the
length-alignment A6. The pre-patch pruned `blocks`/`num_blocks` by in-place
`del` *while the scan was still running* (`del num_blocks[i], blocks[i]`), so a
second removal landed on a shifted index and either ran off the end of the
now-shorter list (the `IndexError` the issue reports) or discarded the wrong
position; meanwhile `rep_blocks` was pruned separately afterwards. That is
exactly a desynchronisation of the three lists. `model_prepatch.py` reproduces
it (prunes `reps` correctly but lets only the FIRST flagged `blocks`/`num_blocks`
removal take effect) and **fails** the postcondition
`ToSeq(Result()[0]) == filtered(ToSeq(blocks), ToSeq(flag))` (and, transitively,
the alignment clauses A6) on every input with two or more flagged positions —
which is exactly the spec sensing the change (G-DIFF). The F2P case
`DihedralGroup(18).sylow_subgroup(p=2)` / `DihedralGroup(50)...` is one such
≥2-removal input that the pre-patch crashed on with `IndexError`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the application of one shared removal mask to three parallel lists
— is modelled **deeply** (the spelled-out front-recursive folds `filtered` /
`kept`, consumed by the verified backward loop in `prune_parallel`), not hidden
behind an axiom. There is **no consumed axiom** (`A-consumed`: none) and **no
external library callee**: the only library operations in the hunk are
`enumerate` + list comprehension (modelled directly by the `PSeq` fold) and the
UNCHANGED `issubset`/`len` decision (abstracted into the opaque `flag`). The
deep model is validated == the real Python list-comprehension semantics by G-AX
(A-reference), not consumed as an axiom — so there is no dead `@ContractOnly`.

## C. verify(model) ⇒ resolved

`prune_parallel` verifies only if each of its three outputs equals the SAME
mask-filter of its input under one shared `flag` (A3/A4/A5) and the three
results are length-aligned to `kept(flag)` (A6). By R (opaque-identity carriers,
the unchanged decision abstracted as `flag`) the verified prune equals the gold
patch's three shared-mask comprehensions on the candidate lists; by G-AX the
deep model `filtered`/`kept` equals the real comprehension semantics
(A-reference) over 50 000+ fuzz inputs including repeated identities. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust
point is refinement fidelity (this document, G-EQ); there is no axiom-soundness
trust point because no axiom is consumed (the deep-model A-reference is checked
executably by G-AX rather than trusted).
