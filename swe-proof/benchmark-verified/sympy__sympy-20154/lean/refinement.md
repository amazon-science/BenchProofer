# refinement.md — sympy__sympy-20154

Maps every op in `implementation_partitions` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses callee axiom ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

## The fix, abstractly

The generator builds each partition by mutating a single working dict `ms` in
place and `yield`-ing that *same object* every step. A consumer that materializes
the generator (`list(partitions(...))` / a list comprehension) therefore collects
N references to one object, which — read after the generator is exhausted — all
show the final partition. The patch copies the dict at each yield
(`yield ms` → `yield ms.copy()`), so each materialized element is an independent
snapshot of the partition current at that step.

Because Lean has value semantics (no aliasing), the unchanged generation
algorithm is abstracted to the *sequence of produced partition values* `states`
(the ground truth, identical pre/post patch), and the fix is modeled as the
materialization that relates the collected list to that sequence.

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let mut out : List PartMap := []` | start of `list(partitions(...))` accumulation | I | empty accumulator |
| 2 | `for s in states do` | the generator loop driving each `yield` | R | the produced-value sequence ↔ `states`; the (unchanged) `while keys != [1]` advance step is abstracted into `states` |
| 3 | `out := out ++ [s]` | `yield ms.copy()` then collected by the consumer | R | **the fixed op**: each step appends an independent snapshot of the current partition value; `dict.copy()` of a `dict[int,int]` ↔ taking the produced value `s : List (Nat × Nat)` (a pure value, no shared identity) |
| 4 | `return out` | the fully materialized list | I | |

Every op is R or I. **No A-tagged rows** — the fix is modeled deeply
(snapshot-on-yield = identity materialization of the produced-value sequence); no
unchanged callee is axiomatized. The generation algorithm is not modeled (its
output is the input carrier), per §3 "changed op modeled deeply, callee output
taken as input".

Because the impl region is entirely R/I (no A-tagged content), `conf_skip =
false`: G-CONF mechanically differential-tests this identity-materialization
shadow against the patched `partitions()` materialization.

## Prepatch (the real bug)

`Solution_prepatch.lean` replaces op #3's `out := out ++ [s]` with
`out := out ++ [states.getLastD []]` — every emitted entry is the *final*
produced value, exactly the aliasing defect: a consumer reading the post-exhaustion
shared object sees the last partition in every slot
(`[{1:6}, {1:6}, {1:6}, {1:6}]`). The discriminating clause is `problem_spec`'s
second conjunct (`∀ i < states.length, result.getD i [] = states.getD i []`):
the prepatch produces `states.getLastD []` at position 0, which differs from
`states.getD 0 []` whenever `states` has ≥2 distinct entries — so
`correct_partitions` is unprovable for the prepatch impl (G-DIFF). Validated on
the F2P input `partitions(6, k=2)` whose produced sequence
`[{2:3}, {1:2,2:2}, {1:4,2:1}, {1:6}]` is non-constant.
