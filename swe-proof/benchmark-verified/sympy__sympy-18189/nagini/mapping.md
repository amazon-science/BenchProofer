# mapping.md — sympy__sympy-18189

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1923822ddf8265199dbd9ef9ce09641d3fd042b9`, states the type
abstraction, and gives the provenance of each axiom.

Repo file under change: `sympy/solvers/diophantine.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reorder_solution_family(expand)` | the `if syms != var:` re-ordering branch of `diophantine(eq, param, syms, permute)` — `sympy/solvers/diophantine.py:182-185` (body of `diophantine`, defined at `:101-102`) | the modeled changed code path: when the caller's symbol ordering differs from the canonical ordering, re-derive and re-arrange |
| `solve_family(expand)` *(axiom — A-consumed)* | the recursive call `diophantine(eq, param, permute=permute)` — `sympy/solvers/diophantine.py:185` (post-patch); `diophantine(eq, param)` pre-patch | the unchanged callee the branch re-invokes to obtain the canonical-ordering solution set; keyed on the `permute` option |
| `relabel(token)` *(axiom — A-consumed)* | the per-tuple component re-arrangement `tuple([t[dict_sym_index[i]] for i in var])` — `sympy/solvers/diophantine.py:183-184` | the fixed, injective coordinate relabelling applied to each canonical solution tuple (built from `dict_sym_index = dict(zip(syms, range(len(syms))))`) |
| `relabel_family(s)` | the set comprehension `{ tuple([...]) for t in diophantine(...) }` — `sympy/solvers/diophantine.py:184-185` | pure spec: the image of the canonical family under the per-tuple relabelling, element-wise |
| `expand` (bool) | the `permute` keyword argument of `diophantine` — `sympy/solvers/diophantine.py:102` | the option that governs whether the full solution family (sign / order variants) or only the base family is enumerated |

The branch is reached only when `syms` is supplied and, after filtering to the
free symbols, `syms != var` (the `default_sort_key`-sorted free-symbol list,
`:174-175`). The return value of `diophantine` in this branch is exactly the
re-arranged image of the inner recursive call's result — which is what the model
computes.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the solution *set* returned by `diophantine` (a Python `set` of solution tuples) | `PSeq[int]` of solution-tuple identity tokens | each solution tuple ↦ a distinct integer identity token; the set ↦ a pure sequence enumerating those tokens. The branch's output is the **image of the inner set under one fixed map** (`relabel`), and the F2P observable is **set equality** of that image; an order-respecting sequence carrier therefore preserves exactly the observed content (the relabelling is injective ⇒ no two distinct solutions merge ⇒ image cardinality = source cardinality, and a bijection on tokens models the column permutation faithfully) |
| `tuple([t[dict_sym_index[i]] for i in var])` — one tuple's components re-indexed by the syms→canonical index map | `relabel(token)` (an injective `int -> int`) | the component permutation is a deterministic, injective function of the canonical solution; modelled as one opaque injective relabelling on the tuple's identity token |
| `permute` (bool keyword) | `expand` (bool) | identity |
| `diophantine(eq, param, permute=permute)` recursive call (returns the canonical-ordering set under the given option) | `solve_family(expand)` (axiom) | the canonical solver, keyed on the option; `permute=permute` ↔ `solve_family(expand)`, `permute=False` (the bug) ↔ `solve_family(False)` |

`str`/symbol/expression objects never enter the model: the only behaviour the
F2P tests observe is *which* set of integer-tuple solutions is returned, and the
modeled change is purely the propagation of the boolean option through the
re-derivation. Integer identity tokens are therefore the faithful carrier.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `solve_family` ↔ the recursive `diophantine(eq, param, permute=…)` call (A-consumed)
**Callee:** `sympy.solvers.diophantine.diophantine`, invoked recursively at
`sympy/solvers/diophantine.py:185`. The model relies on exactly one property of
this callee: **its result depends on the option** — the family enumerated under
`permute=True` is in general a strict superset of the one under
`permute=False`, and the two are NOT equal. The axiom therefore states *no*
equality between `solve_family(True)` and `solve_family(False)`; it leaves them
unconstrained relative to each other. This is the **weakest** contract the proof
needs: the post-patch impl invokes `solve_family(expand)` and trivially matches
the postcondition (same option), while any impl that re-derives under a fixed
`False` cannot prove `relabel_family(solve_family(False)) ==
relabel_family(solve_family(expand))` for arbitrary `expand`.

**Soundness for G-AX:** the only obligation on the real callee is that the
option genuinely matters — i.e. there exists an input on which
`diophantine(eq, param, permute=True) != diophantine(eq, param, permute=False)`.
This is the very phenomenon the issue reports and the F2P test exercises
(`y**4 + x**4 - 2**4 - 3**4`): with `permute=True` the canonical-ordering call
returns the full 8-element sign-and-order family
`{(-3,-2),(-3,2),(-2,-3),(-2,3),(2,-3),(2,3),(3,-2),(3,2)}`, whereas with
`permute=False` it returns the single base solution `{(2,3)}`. `axiom_check.py`
executes the real `diophantine` in-container on this and further equations to
confirm the option-dependence the axiom assumes (and the absence of a spurious
`True == False` equality), over the canonical ordering.

### 3.2 `relabel` ↔ the per-tuple component re-arrangement (A-consumed)
**Callee:** the comprehension body `tuple([t[dict_sym_index[i]] for i in var])`
(`sympy/solvers/diophantine.py:183-184`), where
`dict_sym_index = dict(zip(syms, range(len(syms))))`. For a fixed `(syms, var)`
this is a fixed permutation of the tuple's components, hence a **bijection** on
solution tuples — applying it to two distinct canonical solutions yields two
distinct re-arranged solutions (a coordinate relabelling never identifies
distinct points). The model relies only on this injectivity (so the relabelled
family has the same cardinality and the set image is faithful); it is left
otherwise opaque (`@ContractOnly`, no body constraint beyond being a function).

**Soundness for G-AX:** `axiom_check.py` confirms the re-arrangement is a
bijection on tuples — for the F2P equation it checks that re-indexing each
canonical solution by the `(y, x)` vs `(x, y)` index map produces a set of the
same cardinality (no collisions) and that the round between the two orderings is
consistent — i.e. `relabel` is a genuine coordinate permutation, not a merging
map. The component permutation is itself unchanged by the patch (the patch
touches only the option propagation), so axiomatizing it is sound.

## 4. Why these are A-consumed, not A-reference, and there is no kind-3 step
The two changed-vs-unchanged distinctions: the **only** thing the patch changes
is the option propagated into the recursive `diophantine` call (`permute=permute`
replacing the dropped default). That changed operation is modelled **deeply** —
it is the explicit `solve_family(expand)` call in the impl, keyed on the caller's
`expand`, pinned by the postcondition `Result() == relabel_family(solve_family(
expand))`. Both `solve_family` (the recursive solver) and `relabel` (the
component permutation) are callees that the branch *invokes but does not change*;
their `Ensures` (option-dependence-without-equality for `solve_family`,
injectivity for `relabel` — the latter implicit in the weakest contract) are
**consumed** by the proof. There is no operation that is a *changed* op Nagini
cannot express (no kind-3 step): the change is exactly the argument forwarded to
`solve_family`, which the model expresses directly.
