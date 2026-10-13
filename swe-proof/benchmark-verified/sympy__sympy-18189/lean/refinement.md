# refinement.md — sympy__sympy-18189

Maps every op in `implementation_diophantine` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses axiom property),
**A-reference** (deep model validated == real callee by G-AX), **I** (identical
concrete op).

The gold patch is a one-token change: the recursive self-call
`diophantine(eq, param)` becomes `diophantine(eq, param, permute=permute)` — i.e.
the solution-generation mode `permute` is propagated into the recursive solve
that feeds the reordering branch.

| # | `implementation_diophantine` op | `patch.diff` / source counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if syms ≠ var then …` | `if syms != var:` (line 181) | R | `syms`/`var` are `List Symbol` ↔ `List Nat`; `≠` ↔ `!=` (list inequality). Identity tokens, order-preserving bijection (mapping.md). |
| 2 | `solveCanonical eq permute` (inside the branch) | `diophantine(eq, param, permute=permute)` (line 184, **post-patch**) | I | The op is the recursive canonical solve under the propagated mode. `solveCanonical` is the abstract stand-in for that call; the `param` argument is irrelevant to the modeled output shape and is elided. The propagation of `permute` IS the fix and is the discriminating clause vs the prepatch. |
| 3 | `for t in … do acc := acc ++ [reindexTuple var syms t]` | `{tuple([t[dict_sym_index[i]] for i in var]) for t in …}` (lines 182-184) | R | set comprehension ↔ ordered accumulator loop; G-CONF compares as sets (mapping.md). The per-tuple map is op #4. |
| 4 | `reindexTuple var syms t = var.map (fun i => t.getD (syms.idxOf i) 0)` | `tuple([t[dict_sym_index[i]] for i in var])`, `dict_sym_index = dict(zip(syms, range(len(syms))))` | R | `dict_sym_index[i]` (position of `i` in `syms`) ↔ `syms.idxOf i`; tuple-index ↔ `List.getD` (default `0` unreachable, since every `i ∈ var` survives the `syms = [i for i in syms if i in var]` filter and `syms ≠ var` ⇒ same membership). |
| 5 | `return solveCanonical eq permute` (fall-through, `syms = var`) | the function continues to the canonical solve without reindexing (`syms == var`, comprehension skipped) | I | when the requested order equals the canonical order the reordering branch is not entered; the result is the canonical solution set under the same mode. |

**No A-consumed and no A-reference rows.** `solveCanonical` is an UNCHANGED
callee left abstract (`opaque` signature, no `_prop` axiom consumed by the
proof), so it is neither a consumed axiom nor a G-AX-validated deep-model
reference. `axiom_check.py` is therefore a skip stub. The impl region has R/I
content (not all-A-tagged), so `conf_skip=false` and G-CONF runs a real fuzz.

**No changed-inexpressible op.** The entire fix — threading `permute` into the
recursive solve — is captured by op #2 (post-patch passes `permute`; the
prepatch passes `false`). The spec pins the canonical solve's mode argument to
the caller's `permute` in BOTH branches, so any impl that drops the mode on the
reordering branch (the real bug) fails to satisfy the spec.
