# refinement.md — sympy__sympy-22080

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `printNegatedFactor` `do` block, plus the deep `opWeight`/`needsParen`/
`renderNeg` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized/modeled *unchanged* callee —
**A-consumed** where the proof uses an axiom's `ensures`, **A-reference** where a
deep model of an unchanged callee is validated == the real callee by G-AX), or
**I** (identical concrete op). The CHANGED operation is not tagged A — it is
modeled deeply and refuted by **G-CONF** as an R/I leg (steps 3/5 below).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The two entangled change sites

The gold patch fixes one observable defect (a leading unary minus binding only
the first piece of its factor, e.g. `-x % y` for `-Mod(x, y)`) via two edits
that BOTH feed the single comparison `precedence(factor) <= level` in
`_print_Mul`'s single-negative-factor branch:

* **Site C** (`codeprinter.py`): raise the comparison `level` for that branch
  from the negated-product strength (`prec == 40`) to the unary-minus threshold
  `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]) == 55`. Modeled by `negLevel = 110`.
* **Site P** (`precedence.py`): give `Mod` the multiplicative strength
  (`precedence(Mod) : 70 → 50`) so a bare `Mod` factor compares at 50, not 70.
  Modeled by `opWeight .modOp = 100 (= 2*50)`.

The model folds both into the single `opWeight kind <= negLevel` test that
`needsParen` performs, exactly as the patched renderer folds them into
`parenthesize(a[0], 55)`.

## Step table — `printNegatedFactor` ↔ `_print_Mul` single-negative-factor branch

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | param `k : OperandKind` | the single numerator factor `a[0]` of a negative `Mul` | R | the factor abstracted to its binding-strength class (mapping.md §2). The change reads only `precedence(a[0])`, so the kind is a faithful abstraction. |
| 2 | param `inner : List Char` | `self._print(item)` for that factor | R + A-tagged | the factor's own printed form; `str ↔ List Char` (mapping.md §2). Unchanged callee, consumed as input; G-CONF supplies the real `pycode(factor)`. |
| 3 | `opWeight k` | `precedence(a[0])` (Site P sets `Mod ↦ 50`) | R (changed; G-CONF) | the *post-fix* binding strength, modeled deeply; this is part of the CHANGED operation, so it is refuted by G-CONF (`precedence(e)*2 == opWeight(k)` against the patched renderer, mapping.md §3.1), NOT a G-AX A-reference. The `Mod ↦ Mul` table entry IS `opWeight .modOp = 100`. |
| 4 | `negLevel` (`110`) | the level `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]) == 55` (Site C) | R + I | the unary-minus threshold; `55 ↔ 110` via the ×2 order-only scaling. Concrete constant, transliterated by G-CONF. |
| 5 | `if needsParen k then ('(' :: inner) ++ [')'] else inner` | `self.parenthesize(a[0], 55)` (wraps iff `precedence(a[0]) <= 55`) | R + I (changed; G-CONF) | the wrap decision: `needsParen k == (opWeight k <= negLevel) == (precedence(e) <= 55) ==` the patched `parenthesize` wrap (mapping.md §3.1). The assembly (`'(' :: … ++ [')']`) is **I** (concrete); the wrap decision is part of the CHANGED operation, refuted by G-CONF against the patched renderer (not a G-AX A-reference). |
| 6 | `'-' :: wrapped` (return) | `sign + a_str[0]` with `sign == "-"` | I | prepend the leading minus; `"-" + s ↔ '-' :: s`. |

Discriminating content of the change lives in two clauses, exercised by two
independently-failing prepatches:

* **Behavior 1 — the threshold (Site C):** `needsParen .mulCluster = true`
  (`opWeight .mulCluster = 99 <= 110`). A single product factor must be wrapped:
  `-(x*x*x*x)`. `Solution_prepatch.lean` uses the pre-patch level `80 (= 2*40)`;
  then `mulCluster (99 > 80)` and `modOp (100 > 80)` are both left unwrapped, so
  it **fails** both the `mulCluster` and `modOp` postconditions (G-DIFF). This is
  the ccode F2P (`-x**4 == '-(x*x*x*x)'`).
* **Behavior 2 — the Mod strength (Site P):** `needsParen .modOp = true`
  (`opWeight .modOp = 100 <= 110`). A remainder factor must be wrapped:
  `-(x % y)`. `Solution_prepatch_2.lean` keeps the correct threshold but looks a
  remainder up at the pre-patch generic strength `140 (= 2*70)`; then
  `modOp (140 > 110)` is left unwrapped while every other kind is correct, so it
  **fails only** the `modOp` postcondition (G-DIFF). This is the pycode F2P
  (`-Mod(x, y) == '-(x % y)'`).

Both sites are necessary for `-(x % y)`: a remainder factor is wrapped only when
its strength (≤ 50, Site P) does not exceed the threshold (55, Site C).

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the
parenthesization of a single negated factor — is modeled **deeply** (`opWeight`/
`needsParen`/`renderNeg`, steps 3/5, R + I), not hidden behind an axiom about the
function under change. Because that operation IS the change (Site C + Site P edit
`precedence`/`parenthesize`), it is refuted as an R/I leg by **G-CONF** against
the patched renderer — directive 7 forbids axiomatizing it, and an A-reference is
reserved for *unchanged* callees. There is **no consumed axiom and no
A-reference**; the bundle ships a G-AX skip stub (G-AX runs unpatched, where the
post-fix strengths do not exist). The only A leg is the A-tagged unchanged
inner-factor printing (step 2), consumed as input and supplied by the real
renderer on both sides of G-CONF.

## verify(Solution) ⇒ resolved

`printNegatedFactor` verifies only if its output wraps exactly the kinds whose
strength does not exceed the threshold — `modOp` and `mulCluster` wrapped,
`atomic`/`power`/`funcCall` bare (the six `ensures`). By R (`str ↔ List Char`,
factor ↔ kind, `precedence ↔ opWeight/2`, `55 ↔ 110`) the verified renderer
equals the patched `_print_Mul` branch on the tested factors; by G-CONF the R/I
transliteration of the deep model `opWeight`/`needsParen`/`renderNeg` agrees with
`patch.diff`'s real `pycode(-e)` on ≥10⁵ inputs (the changed op is checked here,
against the patched renderer, not by G-AX). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). Trust point is refinement fidelity (this doc,
G-EQ + G-CONF); there is no consumed axiom or A-reference, so G-AX skips.
