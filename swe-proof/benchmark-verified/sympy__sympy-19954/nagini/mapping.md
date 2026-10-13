# mapping.md — sympy__sympy-19954

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6f54459aa0248bf1467ad12ee6333d8bc924a642`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/combinatorics/perm_groups.py`.
Changed function: `PermutationGroup.minimal_blocks` (the inner pruning hunk at
`sympy/combinatorics/perm_groups.py:2194-2213`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `prune_parallel(blocks, nums, reps, flag)` | the non-minimal-system pruning hunk inside `minimal_blocks` — `perm_groups.py:2196-2208` (the `for i, r in enumerate(rep_blocks)` scan and the three list rebuilds that follow it) | the modeled changed behaviour: prune the three parallel candidate lists by one shared per-position removal decision |
| `blocks` (param) | the local `blocks` list (`perm_groups.py:2175`, mutated at 2201/2211) | parallel list: block partitions |
| `nums` (param) | the local `num_blocks` list (`perm_groups.py:2176`, mutated at 2201/2212) | parallel list: block numberings |
| `reps` (param) | the local `rep_blocks` list (`perm_groups.py:2177`, mutated at 2208/2213) | parallel list: representative sets |
| `flag` (param) | the per-index removal decision — pre-patch the implicit `del`/`to_remove` decision computed by the `if len(r) > len(rep) and rep.issubset(r)` test; post-patch the explicit `blocks_remove_mask` (`perm_groups.py:2197` post-patch) | the single boolean removal mask shared by all three lists |
| `filtered(xs, flag)` *(deep model — A-reference)* | the gold patch's list comprehension `[x for i, x in enumerate(L) if not blocks_remove_mask[i]]` applied to each of `blocks` / `num_blocks` / `rep_blocks` (`perm_groups.py:2207-2209` post-patch) | pure spec: keep position i iff `not flag[i]`, survivors in order |
| `kept(flag)` *(deep model — A-reference)* | the common length of the three filtered comprehensions = number of `False` mask entries | pure spec: survivor count |

The `flag` argument abstracts the removal DECISION the inner scan makes per
position; the scan that computes it (`len(r) > len(rep) and rep.issubset(r)`)
is UNCHANGED by the patch — only the *application* of the decision to the three
parallel lists changed. The set predicate `rep.issubset(r)` and the `len`
comparisons are not part of the changed behaviour and are abstracted into the
opaque `flag` input (any boolean assignment is admitted), so the spec covers the
prune for every decision the unchanged scan could produce.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `blocks[i]` : a block-partition list (`list[int]`) | `int` identity in `List[int]` | the prune observes only element *identity / position*, never the partition's content; each candidate is a distinct opaque token `blocks[i]` ↔ model `blocks[i]` |
| `num_blocks[i]` : a numbering `tuple` | `int` identity in `List[int]` | same: prune is content-agnostic |
| `rep_blocks[i]` : a representative `set` | `int` identity in `List[int]` | same: prune is content-agnostic |
| the per-index removal decision | `bool` in `List[bool]` | post-patch this IS a `[bool]` mask (`blocks_remove_mask`); pre-patch it is the same decision realised by `del`/`to_remove` |
| `[x for i,x in enumerate(L) if not mask[i]]` (Python list comp) | `filtered(ToSeq(L), ToSeq(mask))` (front-recursive `PSeq` fold) | element-for-element identical; `len` ↔ `kept(mask)` |
| Python `list` value inside a specification | `PSeq[int]` / `PSeq[bool]` via `ToSeq` | `ToSeq(list)` materialises a list; `PSeq` `+`/`drop`/`len`/`[i]` mirror list `+`/slice/`len`/index |

`str` indexing is irrelevant here; the carrier is `List[int]` / `List[bool]`,
and the specification is phrased over `PSeq` via `ToSeq`. The three parallel
lists carry distinct identities so the spec can observe whether a wrong
implementation desynchronises them (the very defect under repair).

## 3. Callee provenance

**There is no axiomatized external callee** — `@ContractOnly` axioms: none.
The changed operation is pure in-process list pruning; the only library calls in
the hunk (`enumerate`, list comprehension, `set.issubset`) are either Python
built-ins modelled directly by the `PSeq` fold or, in the case of `issubset`/
`len`, part of the UNCHANGED decision abstracted into the opaque `flag` input.
Accordingly the proof consumes **no axiom**.

### 3.1 `filtered` / `kept` deep model ↔ the gold list comprehensions (A-reference)
The changed prune is modelled DEEPLY by the `@Pure` folds `filtered` and `kept`
(pure region). These are the spelled-out semantics of the gold patch's three
comprehensions

```python
blocks      = [b for i, b in enumerate(blocks)      if not blocks_remove_mask[i]]
num_blocks  = [n for i, n in enumerate(num_blocks)  if not blocks_remove_mask[i]]
rep_blocks  = [r for i, r in enumerate(rep_blocks)  if not blocks_remove_mask[i]]
```

— keep position `i` iff `not mask[i]`, survivors in original order, ALL THREE
governed by the SAME `mask`. Because one mask drives all three, the outputs are
parallel-aligned: equal length (`kept(mask)`) and the k-th survivor of each list
comes from the same original index. There is no consumed axiom; the deep model
is validated **equal to the real Python list-comprehension semantics**
out-of-band by `axiom_check.py` (G-AX): it runs `gold_prune` (the three real
comprehensions) and asserts `filtered`/`kept` agree, over 11 boundary + 50 000
fuzz inputs (small integer domain so element identities repeat — exercising that
the prune is positional, not value-based), and additionally reproduces the
pre-patch in-place-deletion to confirm it diverges (IndexError / wrong
survivors) on every ≥2-flag input. Stdlib-only; exit 0 iff sound.
