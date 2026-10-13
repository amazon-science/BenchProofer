# refinement.md — sympy__sympy-18189

The operation-by-operation correspondence between `model.py`'s implementation
(the `reorder_solution_family` impl region, the deep `relabel_family` fold, and
the `solve_family` / `relabel` axioms) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses the axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The changed site — `diophantine`'s `if syms != var:` branch

Gold hunk (`sympy/solvers/diophantine.py:182-185`):
```
              if syms != var:
                  dict_sym_index = dict(zip(syms, range(len(syms))))
                  return {tuple([t[dict_sym_index[i]] for i in var])
-                             for t in diophantine(eq, param)}
+                             for t in diophantine(eq, param, permute=permute)}
```

The branch re-derives the answer in the canonical symbol ordering and re-arranges
each solution tuple's components into the caller's ordering. The bug: the
recursive re-derivation `diophantine(eq, param)` drops the caller's `permute`
option, so it returns the *base* family and the re-arranged answer is incomplete
whenever `permute=True`. The fix forwards the option: `permute=permute`.

| # | model.py impl op (`reorder_solution_family`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `expand: bool` | the `permute` keyword of `diophantine` | R | `bool` ↔ `bool`, identity carrier (mapping.md §2). |
| 2 | `canonical = solve_family(expand)` | `for t in diophantine(eq, param, permute=permute)` — the recursive call, forwarding the option | A-consumed | `solve_family` axiomatizes the **unchanged** recursive solver, keyed on the option; the proof consumes the fact that its `True`/`False` families are NOT equal. The model passes the caller's `expand`, exactly as the gold passes `permute=permute`. (mapping.md §3.1.) The single changed token — `permute=permute` replacing the dropped default — is the `expand` argument here; the change is modelled **directly**, not hidden in an axiom about the function under change. |
| 3 | `relabel_family(canonical)` — the front-recursive fold applying `relabel` to each canonical solution in order | `{ tuple([t[dict_sym_index[i]] for i in var]) for t in … }` — the set comprehension re-arranging each tuple's components | A-consumed (via `relabel`) + R | each canonical solution `t` is mapped through one fixed component permutation; modelled as the injective `relabel` token map folded over the family (`relabel_family`). The comprehension builds a *set*; the model builds an order-respecting `PSeq` whose element-set is the relabelled image. Because `relabel` is injective (mapping.md §3.2), the sequence's element-set has the same cardinality as the source family — the set the gold returns. R refines `set` ↔ `PSeq` (mapping.md §2); the per-tuple permutation is the A-consumed `relabel`. |
| 4 | `return result` (a `PSeq[int]`) | `return { … }` (a `set` of tuples) | R | the function's value is the relabelled family; `set` ↔ `PSeq` carrier refinement (mapping.md §2). |

The discriminating content of the change — the option must flow into the
re-derivation — lives in step 2: `solve_family(expand)` (model) ⇔
`diophantine(eq, param, permute=permute)` (real). The pre-patch dropped the
option; `model_prepatch.py` reproduces that exactly
(`canonical = solve_family(False)`) and **fails** the postcondition
`Result() == relabel_family(solve_family(expand))` (model_prepatch.py:89), which
is the spec sensing the change (G-DIFF). For `expand == True` the prepatch would
have to prove `relabel_family(solve_family(False)) ==
relabel_family(solve_family(True))`, which the `solve_family` axiom deliberately
does NOT grant.

## No kind-3 (unexpressible-changed-op) steps
Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — the option forwarded into the recursive call — is modelled
**directly** as the `expand` argument of `solve_family` in the impl (step 2),
pinned by the postcondition, NOT hidden behind an axiom about the function under
change. The two consumed axioms cover the **unchanged** callees the branch
invokes:

- `solve_family` (**A-consumed**) — the recursive `diophantine` solver. The
  patch does not change *it*; it changes *which argument* is passed to it. The
  proof consumes the axiom's option-dependence (no `True == False` equality).
- `relabel` (**A-consumed**) — the per-tuple component permutation. Unchanged by
  the patch; the proof consumes its injectivity (faithful set image).

There is no `A-reference` deep model standing in for a changed string/numeric
operation here; the change is a one-token argument propagation, expressed
directly. G-AX validates both consumed axioms against the real `diophantine` /
component-permutation behaviour in-container (axiom_check.py).

## verify(model) ⇒ resolved
`reorder_solution_family` verifies only if it re-derives the canonical family
under the caller's `expand` (step 2) and relabels it (step 3). By R
(`bool` identity, `set` ↔ `PSeq`, injective `relabel`) the verified branch
equals `{ tuple([t[dict_sym_index[i]] for i in var]) for t in diophantine(eq,
param, permute=permute) }` on the tested inputs. By G-AX the real recursive
`diophantine` honours the option (so `solve_family(True) != solve_family(False)`
on the F2P equation) and the component re-indexing is a bijection. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves (G-RESOLVE).
The trust points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and
refinement fidelity (this document, G-EQ).
