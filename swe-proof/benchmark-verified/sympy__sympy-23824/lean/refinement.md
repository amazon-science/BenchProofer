# refinement.md — sympy__sympy-23824

Maps every op in `implementation_prependLeading` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model == real callee, G-AX), **I**
(identical concrete op).

The modeled slice is the final prepend step of `kahane_simplify` (gold lines
695–698 → the single replacement line). Gold (post-patch):

```python
resulting_indices = list( free_pos[0:first_dum_pos] + ri for ri in resulting_indices )
```

| # | `implementation_prependLeading` op | `patch.diff` counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let lead := labels.take leadCount` | `free_pos[0:first_dum_pos]` (Python slice of the leading block) | R | `list[:n]` ↦ `List.take n`; `free_pos`↦`labels`, `first_dum_pos`↦`leadCount`. Bijection in mapping.md. |
| 2 | `for t in terms do …` | `for ri in resulting_indices` (generator) | R | iterate the additive terms; `resulting_indices`↦`terms`. Order preserved. |
| 3 | `out := out ++ [lead ++ t]` | `free_pos[0:first_dum_pos] + ri` (list concat, accumulated by `list(... )`) | I | list concatenation `++`; the comprehension rebuilds the term list in the same order. |
| 4 | `return out` | bind back to `resulting_indices` | I | the rebuilt list of terms is the function's working value going into `resulting_expr`. |

Every op is R or I. No A rows: the slice calls no unchanged repo callee — only
Python list builtins whose Lean counterparts are concrete library ops.
`axioms` region is empty; `axiom_check.py` is a skip stub.

## Prepatch correspondence (the bug)

Pre-patch source (gold lines 697–698):
```python
for i in range(0, first_dum_pos):
    [ri.insert(0, free_pos[i]) for ri in resulting_indices]
```
`ri.insert(0, free_pos[i])` for `i = 0,1,…,first_dum_pos-1` lays the leading
labels down at the FRONT one at a time, so they end up REVERSED:
`free_pos[first_dum_pos-1], …, free_pos[0]` ahead of each term. The prepatch impl
mirrors this exactly:
```lean
for i in [0:leadCount] do
  out := out.map (fun t => labels[i]! :: t)
```
which yields `(labels.take leadCount).reverse ++ t`. For `leadCount ≥ 2` with
distinct labels this disagrees with `problem_spec_prependLeading` (which demands
`labels.take leadCount ++ t`, in order), so `correct_prependLeading` is
unclosable → G-DIFF fails as required. This is the actual issue bug: the F2P
case `G(rho)*G(sigma)*G(mu)*G(-mu)` has a 2-item leading block `[rho, sigma]`
that the bug emits as `[sigma, rho]`.

## R/I conformance (G-CONF)

`conformance_check.py` builds the R/I shadow (`take` + concat) in Python and
differential-tests it against the gold patch line over ≥10⁵ fuzzed
`(leadCount, labels, terms)`; zero disagreements expected.
