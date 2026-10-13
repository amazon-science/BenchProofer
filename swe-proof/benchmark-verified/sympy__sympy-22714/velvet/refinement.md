# refinement.md — sympy__sympy-22714

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `imaginaryCoordCheck` `do` block plus the deep `anyImaginary`/`coordImaginary`
model in the `pure` region) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — none here), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are no A-tagged steps, so
G-AX skips (no `axiom_check.py`).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The imaginary-coordinate guard — `Point.__new__` (`sympy/geometry/point.py:153`)

Gold hunk:
```
- if any(a.is_number and im(a) for a in coords):
+ if any(a.is_number and im(a).is_zero is False for a in coords):
      raise ValueError('Imaginary coordinates are not permitted.')
```

| # | Solution.lean impl op (`imaginaryCoordCheck`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `coords : List Coord` | `coords` tuple iterated by the `any(... for a in coords)` generator | R | the coordinate sequence ↔ `List Coord` (mapping.md §2). G-CONF bridges each element via the abstraction `(a.is_number, im(a).is_zero is False, bool(im(a)))`. |
| A2 | per-element `coordImaginary c = c.numeric && c.imagNonzero` | the generator body `a.is_number and im(a).is_zero is False` | R + I | `c.numeric ↔ bool(a.is_number)`, `c.imagNonzero ↔ (im(a).is_zero is False)` (mapping.md §2). The boolean `and` ↔ `&&` is **I**. This is the EXACT post-patch predicate. |
| A3 | result `anyImaginary coords`: the disjunction over the list, computed by the backward `while` fold | the `any(...)` aggregation | I | `any` over the generator ↔ the front-recursive `||` fold; the backward loop computes exactly the left-to-right disjunction `anyImaginary`. Order-insensitive, so the backward walk is observationally identical. |
| A4 | returned `out : Bool` | the `if`-test value that gates `raise ValueError('Imaginary coordinates are not permitted.')` | R | `out = true` ↔ the constructor raises the imaginary-coordinate `ValueError`; `out = false` ↔ that guard is skipped (mapping.md §1). The `raise`/control-flow wrapper is identity on the boolean decision the F2P test observes (it observes raise vs. no-raise). |

Discriminating content of the change — a concrete coordinate whose imaginary
part is *coarsely present but not provably nonzero* (the case that arises under
suppressed expression evaluation, e.g. `im(Integer(1))` carried unsimplified)
must NOT trigger the guard. This lives in `coordImaginary c = c.numeric &&
c.imagNonzero` (model) ⇔ `a.is_number and im(a).is_zero is False` (real). The
pre-patch generator `a.is_number and im(a)` used the coarse truthiness
`bool(im(a))`; `Solution_prepatch.lean` reproduces that as
`c.numeric && c.imagPresent` and **fails** `out = anyImaginary coords` (G-DIFF)
precisely on the `imagPresent` vs `imagNonzero` clause.

## B. No additional change sites

The gold patch is a single one-line change to one predicate. There are no other
changed functions and no callee swaps.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
per-coordinate imaginary test — is modeled **deeply** (the spelled-out predicate
`coordImaginary`, step A2), not hidden behind an axiom about the function under
change. There is no consumed axiom and no A-reference: the two SymPy queries the
predicate consults (`a.is_number`, the three-valued `im(a).is_zero`) are
UNCHANGED by the patch; their *results* are the abstracted observations
`Coord.numeric` / `Coord.imagNonzero`, which G-CONF recomputes from the real
SymPy expressions at base_commit (mapping.md §3). No dead axioms.

## D. verify(Solution) ⇒ resolved

`imaginaryCoordCheck` verifies only if its output equals the exact per-coordinate
disjunction using the *rigorous* nonzero test (A2: `numeric && imagNonzero`),
NOT the coarse truthiness. By R (`coords ↔ List Coord`, the raise/no-raise
identity A4) the verified decision equals the patched guard
`any(a.is_number and im(a).is_zero is False for a in coords)` on every
coordinate list. By G-CONF the R/I transliteration of the fold agrees with
`patch.diff`'s behaviour — including the regression case `Point(1, 2)` under
suppressed evaluation, which the pre-patch coarse rule wrongly rejected — over
≥10⁵ inputs. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). There is exactly one trust point and it is mechanical: refinement
fidelity (this doc, G-EQ + G-CONF). No axiom soundness obligation arises.
