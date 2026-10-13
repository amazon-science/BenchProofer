# mapping.md — sympy__sympy-20154

## Symbol binding (base_commit bdb49c4abfb35554a3c8ce761696ffff3bb837fe)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_partitions` / `problem_spec_partitions` | the consumer-visible materialization of the `partitions(n, m, k, size=False)` generator (`list(partitions(...))`) | `sympy/utilities/iterables.py:1696-1842` (generator); the materialization is what the issue + F2P tests exercise |
| `states` (input carrier) | the sequence of partition dicts the generator *produces* at each `yield` (the generation algorithm, which the patch leaves UNCHANGED) | `iterables.py` generator body, every `yield` site |
| `result` | `[p for p in partitions(...)]` — the list the consumer collects | F2P test `test_partitions` / `test_uniq` |
| (impl op) `out := out ++ [s]` (the snapshot) | `yield ms.copy()` (the two patched `yield` sites) | `iterables.py:1789, 1831` (post-patch) |

The patch touches ONLY what each `yield` hands out: `yield ms` → `yield ms.copy()`
(and the symmetric `size=True` site `yield sum(...), ms` → `..., ms.copy()`). The
partition-generation algorithm (the `while keys != [1]` loop that advances the
working dict `ms`) is byte-for-byte unchanged. So the model takes the produced
sequence of partition *values* as the input carrier `states` and models the fix
as the position-wise materialization relating `result` to `states`.

## Type bijection (G-CONF uses this)

| Python | Lean | notes |
|---|---|---|
| one partition `dict[int,int]` (part-value ↦ multiplicity), e.g. `{2: 3}` | `PartMap = List (Nat × Nat)`, e.g. `[(2, 3)]` | association list; key order from the generator's `keys` (largest→smallest) is preserved |
| the produced sequence of partition values | `states : List PartMap` | one entry per `yield` |
| `list(partitions(...))` (size=False) | `result : List PartMap` | the materialized list |
| `len(list(...))` | `result.length` | number of yields |
| the i-th materialized element | `result.getD i []` | |

Only the `size=False` form is modeled (the `else: yield ms[.copy()]` sites); the
`size=True` form is the same defect on the same object (`ms` vs `ms.copy()`), so
modeling one branch captures the fixed behavior — see refinement.md.

## Callee provenance / flag deps

None consumed. The generation algorithm is NOT axiomatized — its *output* (the
produced value sequence) is taken as the abstract input, and the fix
(snapshot-on-yield) is modeled deeply (position-wise identity). No
`opaque`/`axiom` decls; `axiom_check.py` is a skip stub.

## G-CONF fuzz seed

Pinned seed: **20154**. Inputs: random `(n, m, k, size=False)` argument tuples
within `1 ≤ n ≤ 40`, `m ∈ {None} ∪ [1..n]`, `k ∈ {None} ∪ [1..n]`; the shadow
materializes the produced-value sequence (identity) and is diffed against
`[p for p in partitions(n, m, k)]` from the gold-patched repo.
