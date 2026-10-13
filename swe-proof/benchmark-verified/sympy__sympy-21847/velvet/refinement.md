# refinement.md — sympy__sympy-21847

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectMonomials` `do` block and the deep `selectByDegree`/`totalDegree` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (§C). Claim: any impl verifying against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The degree-threshold site — total-degree branch of the changed function

The patch edits **two identical hunks** (`sympy/polys/monomials.py`): the
commutative branch (`:127`) and the non-commutative branch (`:139`). Both change
the per-candidate keep test the same way:

```
-                if max(powers.values()) >= min_degree:
+                if sum(powers.values()) >= min_degree:
                     monomials_list_*.append(Mul(*item))
```

| # | Solution.lean impl op (`selectMonomials`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `candidates : List (List Nat)` | the stream of enumerated `item`s, summarised by their `powers` dict (`combinations_with_replacement(variables, max_degree)` / `product(variables, repeat=max_degree)` + the counting loop) | R + I | the UNCHANGED enumerator+counter is abstracted into the free input; one candidate ↔ its multiplicity vector (mapping.md §2). The `S.One` padding slot is dropped (it never increments a count, contributes 0 degree). |
| A2 | parameter `minDeg : Nat` | `min_degree` (the integer arg, `0` when omitted) | R | `int ≥ 0` ↔ `Nat` (mapping.md §2); the negative case raises before this branch. |
| A3 | keep decision `if minDeg ≤ totalDegree p` with `totalDegree p = p.sum` | `if sum(powers.values()) >= min_degree:` | I | the CHANGED op, modeled **deeply** and concretely: `totalDegree`/`selectByDegree` ARE the post-patch threshold. `p.sum` ↔ `sum(powers.values())` (the `S.One` slot adds 0). The relation is `min_degree <= total_degree(monom)`, exactly the documented contract. |
| A4 | `result` accumulates the kept multiplicity vectors in enumeration order | `monomials_list_*.append(Mul(*item))` then `yield from set(...)` | R | `Mul(*item)` reconstructs the term from the kept candidate and `set(...)` dedups — a content-preserving R-postprocess applied **equally** pre- and post-patch, so it never masks the threshold change (mapping.md §2). G-CONF transliterates it and compares the yielded monomial **set**. |

Discriminating content of the change — a candidate whose **largest single
multiplicity** is below the bound while its **total degree** meets it (e.g. the
multiplicity vector `[1,1]`, total degree 2, max component 1, at `minDeg = 2`)
— is kept by `selectByDegree` (`minDeg ≤ p.sum`) but dropped by the pre-patch
`max(powers.values()) >= min_degree`. `Solution_prepatch.lean` reproduces the
pre-patch `max` test (`p.foldr Nat.max 0`) and **fails** `out = selectByDegree
minDeg candidates` on exactly that goal (G-DIFF). This is the `x*y`/`x*y**2`-type
monomial the issue reports as wrongly missing.

## B. Both hunks share one model

The commutative and non-commutative hunks are byte-identical edits to the same
keep test; they differ only in the UNCHANGED enumerator feeding `candidates`
(`combinations_with_replacement` vs `product`). The single `selectMonomials`
method models the shared keep decision; both hunks are the same R/I-refinement
of it. The observable fixed behaviour is identical for both branches (a
total-degree candidate that the old `max` test dropped is now kept), so one
prepatch + one G-CONF (which fuzzes BOTH the commutative and non-commutative
enumerations, see §4) suffice; there is no independently-fixed behaviour
requiring a second `Solution_prepatch_<k>.lean`.

## C. No axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
per-candidate aggregation of the multiplicity vector against the bound — is
modeled **deeply** (the spelled-out `selectByDegree` with `totalDegree = p.sum`,
step A3, an **I** op), not hidden behind an axiom about the function under
change: there is **no consumed axiom and no A-reference**. The surrounding
enumerator/counter/`Mul`/`set` are unchanged callees folded into the free
`candidates` input (A1/A4); the spec holds for every candidate list, so there is
nothing to check against a real callee — `axiom_check.py` is a skip stub (G-AX
skip).

## D. verify(Solution) ⇒ resolved

`selectMonomials` verifies only if its output equals the order-preserving filter
that keeps exactly the candidates with `minDeg ≤ totalDegree` (A3 = the sum
threshold). By R (`item ↔ multiplicity vector`, `int ↔ Nat`, `Mul`/`set` a
shared content-preserving postprocess) the verified filter equals the patched
`itermonomials`' keep test on every enumerated candidate; by G-CONF the R/I
transliteration of `selectByDegree` agrees with `patch.diff`'s yielded-monomial
set on ≥10⁵ fuzzed `(variables, max_degree, min_degree)` configurations across
both the commutative and non-commutative enumerations. There are no axioms
(G-AX skip). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-CONF).
