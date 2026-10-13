# refinement.md — sympy__sympy-23824

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `restoreLeading` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete operation). The claim: *any implementation
that verifies against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The restore-leading site — `kahane_simplify()` (`sympy/physics/hep/gamma_matrices.py:697-698`)

Gold hunk:
```
- for i in range(0, first_dum_pos):
-     [ri.insert(0, free_pos[i]) for ri in resulting_indices]
+ resulting_indices = list( free_pos[0:first_dum_pos] + ri for ri in resulting_indices )
```

Setting at this point in `kahane_simplify`:
- `free_pos` is a `list` of index labels, `free_pos[i]` (for `i < first_dum_pos`)
  being the integer label of the *i*-th leading uncontracted gamma factor, in
  the input's original left-to-right order (built at `gamma_matrices.py:472-474`;
  `first_dum_pos` is the position of the first contracted factor,
  `gamma_matrices.py:460`).
- `resulting_indices` is a `list` of terms; each term `ri` is a `list` of index
  labels — the factors of one additive term produced by the core rewrite.
- The whole site rebuilds **every** term `ri` identically: it prepends the
  leading run `free_pos[0:first_dum_pos]` to `ri`. The model captures the
  per-term transformation (one representative term `tail` = `ri`), which is the
  entire observable content of the change; the surrounding
  `for ri in resulting_indices` comprehension applies that same transformation
  uniformly to each term (an unchanged map, an R/I structural wrapper).

| # | Solution.lean impl op (`restoreLeading`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `leading : List Int` | the slice `free_pos[0:first_dum_pos]` (a `list` of index labels) | R | `list` of gamma-factor index labels ↔ `List Int` of those labels; `leading[i]` ↔ `free_pos[i]`, `leading.length` ↔ `first_dum_pos`. The labels are integers in both (mapping.md §2). |
| A2 | parameter `tail : List Int` | the term `ri` (a `list` of index labels) | R | same carrier bijection: `tail[j]` ↔ `ri[j]`, `tail.length` ↔ `len(ri)`. Read-only (the gold builds a fresh list per `ri`; the term content is not otherwise mutated). |
| A3 | initialise `result := tail`, then backward loop `i = leading.length .. 1` prepending `leading[i-1]` (`result := c :: result`) | the left summand `free_pos[0:first_dum_pos]` placed **in front of** `ri` in `free_pos[0:first_dum_pos] + ri`, **in its original order** | I (under R on the elements) | both place the leading run in front of the term preserving its left-to-right order. Prepending `leading[i-1]` for *descending* `i` (last element first, front element last) reproduces the slice `free_pos[0:first_dum_pos]` exactly, in order. Certified by the invariant `result = restoreSeq (leading.drop i) tail`. |
| A4 | the deep model `restoreSeq leading tail` and the lemma `restoreSeq leading tail = leading ++ tail` | the concatenation operator `+` joining the leading slice and `ri` | I (under R) | the front-recursive `restoreSeq` is ordinary list concatenation (proven `restoreSeq_eq_append`); Python `list` `+` is the same order-preserving concatenation. The loop builds `restoreSeq (leading.drop i) tail`, terminating at `restoreSeq leading tail = leading ++ tail`. |
| A5 | return `out` with `out = leading ++ tail` | the rebuilt `resulting_indices` entry `free_pos[0:first_dum_pos] + ri` | I (under R) | identical concrete result: the leading run in order, then the term. Bound by the postcondition `out = leading ++ tail`. |

The discriminating content of the change — the leading run is prepended in its
**original order** (`leading ++ tail`) rather than **reversed**
(`reverse(leading) ++ tail`) — lives in the order in which `result` is built.
The pre-patch code front-inserts each leading factor in turn
(`ri.insert(0, free_pos[i])` for `i = 0,1,…,k-1`), which reverses the leading
run; `Solution_prepatch.lean` reproduces that front-insertion order (a forward
loop prepending `leading[i]` for ascending `i`, building
`restoreSeq (leading.take i).reverse tail`) and **fails** the postcondition
`out = leading ++ tail` whenever the leading run has two or more distinct
factors — exactly the spec sensing the change (G-DIFF). This is precisely the
issue's witness `G(rho)*G(sigma)*G(mu)*G(-mu)`: leading run `[rho, sigma]`,
which the bug restores as `[sigma, rho]`.

## B. No kind-3 (unexpressible-changed-op) steps and no axioms

Every step above is R or I. The changed operation is pure list concatenation
with an order constraint — fully expressible in Velvet's `List Int` fragment —
so it is modelled **deeply** in the impl (the front-recursive `restoreSeq`
fold + the `restoreSeq_eq_append` identity), not behind any axiom. There is **no
`axiom` and no `:|`-stub** in this bundle: the surrounding `kahane_simplify`
machinery (links graph, sign correction, the core rewrite that produces each
`ri`) is untouched by the patch and produces the `tail`/`leading` inputs the
modelled site consumes; it is therefore an R-refinement of the unchanged context
(the inputs), not a consumed callee contract. Consequently there are no
A-consumed and no A-reference rows, and no `axiom_check.py` is required (G-AX is
vacuously satisfied: nothing to check).

## C. verify(Solution) ⇒ resolved

`restoreLeading` verifies only if its output equals `leading ++ tail` with the
leading run in original order (A3–A5, the postcondition). By R (the gamma-factor
index labels are integers; `free_pos[0:first_dum_pos]` ↔ `leading`, `ri` ↔
`tail`; list `+` ↔ list `++`) the verified term equals
`free_pos[0:first_dum_pos] + ri` for every term `ri`, which is exactly what the
gold patch assigns to each entry of `resulting_indices`. The surrounding
comprehension applies this transformation uniformly to every term, unchanged.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this document, G-EQ + the mechanical G-CONF
differential test); there is no axiom trust point.
