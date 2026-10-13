# refinement.md — sympy__sympy-21847

The operation-by-operation correspondence between `model.py`'s implementation
(the `keep_comm` / `keep_noncomm` impl regions and the deep fold `deg_sum`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == a real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The two changed sites (identical hunks)

Gold hunk 1 — commutative branch (`sympy/polys/monomials.py:130`):
```
-                if max(powers.values()) >= min_degree:
+                if sum(powers.values()) >= min_degree:
```
Gold hunk 2 — non-commutative branch (`sympy/polys/monomials.py:142`): textually
identical (`max` → `sum`). The two hunks fix the SAME behaviour in the two
branches that handle commuting vs. non-commuting variables.

`keep_comm` ↔ hunk 1, `keep_noncomm` ↔ hunk 2. Both model functions carry the
byte-identical frozen spec and the same skeleton; they are kept distinct to
mirror the two hunks faithfully and to give an independent differential witness
per branch (each `model_prepatch` site fails on its own postcondition).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `powers: List[int]` (the exponent values) | the `powers` dict's `.values()` at the retention test | R | dict-of-exponents ↔ `List[int]` of exponent values; `sum`/`max` are order-independent so the value enumeration order is immaterial (mapping.md §2). |
| 2 | parameter `min_degree: int`, `Requires(min_degree >= 0)` | the `min_degree` local (validated `>= 0`, `<= max_degree` upstream) | R / I | same integer threshold; the upstream guards (`monomials.py:104-115`) establish the `Requires`. |
| 3 | `total` accumulated by the loop and the postcondition `Result() == (deg_sum(ToSeq(powers)) >= min_degree)` | `sum(powers.values()) >= min_degree` | I (over R-carrier) | the patched reduction is the arithmetic SUM of the exponent vector; `deg_sum` is that sum spelled out as a `@Pure` front-recursive fold, and the impl loop computes it. `sum` over a finite int multiset = the fold; identical concrete operation under the carrier refinement (no callee — the changed reduction is modeled deeply, NOT axiomatized). |
| 4 | `return total >= min_degree` (the retained/dropped decision) | `if ... >= min_degree:` controls whether the candidate is appended to the yielded list | I | the boolean retention decision is the observable effect of the changed line; the surrounding enumeration/`Mul`/`set` is unchanged and abstracted away (mapping.md §2). A candidate is in the result set iff this predicate is true, so pinning the predicate pins the F2P-observable change. |

## The discriminator (what the prepatch fails on)

The single behavioural change is **SUM** vs **MAX** over the exponent vector.
For any exponent vector whose maximum single exponent is below `min_degree` but
whose total degree reaches it — e.g. `[2, 1]` with `min_degree = 3`
(`max = 2 < 3 <= 3 = sum`) — the correct predicate retains the term and the
buggy one drops it. This is exactly the F2P case
`itermonomials([x, y], 3, 3) == {x**3, x**2*y, x*y**2, y**3}`: `x**2*y` has
exponent vector `[2, 1]` (total degree 3), retained by `sum >= 3`, dropped by
`max >= 3`. `model_prepatch.py` reverts the reduction to the maximum (modeled
inline as a running-max loop with invariant `forall j in [i,len): powers[j] <=
running`, no named pure helper) and **fails** the frozen postcondition
`Result() == (deg_sum(ToSeq(powers)) >= min_degree)` at both `keep_comm` and
`keep_noncomm` — the spec sensing the change (G-DIFF).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The one operation that genuinely *changed* — the
reduction over the exponent vector from the per-variable maximum to the total
degree — is modeled **deeply** (the spelled-out `@Pure` fold `deg_sum`, consumed
directly by the postcondition and computed by the impl loop; the pre-patch
maximum is modeled inline in model_prepatch.py), **never axiomatized**: there is
no `@ContractOnly` callee in this bundle. Hence there is no A-consumed and no
A-reference row, and no G-AX axiom obligation.

## verify(model) ⇒ resolved

`keep_comm` / `keep_noncomm` verify only if their boolean result equals
`deg_sum(powers) >= min_degree` — the genuine total-degree lower-bound test. By
R (dict-values ↔ `List[int]`; `sum` ↔ the fold) the verified predicate equals
`sum(powers.values()) >= min_degree`, which is exactly the gold patch's changed
line in each branch. The unchanged enumeration determines the candidate set; the
gold patch (this predicate in both branches) makes the F2P `test_monomials`
assertions hold and resolves (G-RESOLVE). The sole trust point reduces to
refinement fidelity (this document, G-EQ); there is no axiom trust point.
