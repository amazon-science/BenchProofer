# refinement.md — sympy__sympy-12419

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `identityEntry` `do` block and the deep models `entryFor`/`coincideValue`)
and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX/G-CONF), or **I** (identical
concrete op). EVERY step is R, A, or I. There is no kind-3
(changed-op-Velvet-cannot-express) step.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1) which runs the REAL patched repo function as the oracle; the A-reference
component callees are audited by **G-AX** (`axiom_check.py`).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). The modeled site is the
sole FAIL_TO_PASS-relevant change: the rewritten `Identity._entry`. (The gold
patch also moves the `KroneckerDelta` import to module scope and removes a
local `from sympy import KroneckerDelta` inside `_eval_derivative` — both are
import-placement no-ops with no behavioural effect and no test in FAIL_TO_PASS /
PASS_TO_PASS; they ride along in `patch.diff` for G-RESOLVE but are outside the
modeled behaviour.)

## A. The element-selection site — `Identity._entry(self, i, j)`

Gold hunk (`sympy/matrices/expressions/matexpr.py:478-482`):
```python
def _entry(self, i, j):
    eq = Eq(i, j)
    if eq is S.true:
        return S.One
    elif eq is S.false:
        return S.Zero
    return KroneckerDelta(i, j)
```

| # | Solution.lean impl op (`identityEntry`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `i j : Idx` | `i, j` — the two `sympify`'d position arguments | R | symbolic index ↔ opaque `Idx` atom (mapping.md §2); only their identity matters, surfacing inside the coincidence indicator. G-CONF binds them to real indices. |
| A2 | param `eq : Option Bool` | `eq = Eq(i, j)`, observed by `eq is S.true` / `eq is S.false` | R + A-reference (input) | the three-valued verdict ↔ `Option Bool` (mapping.md §2). `Eq` is the **unchanged** comparison primitive; the input IS its real three-valued outcome. G-CONF computes the real `Eq(i,j)` verdict to build the input; G-AX checks the `threeval` bridge is total/exact (§3.2). |
| A3 | `if eq = some true then return MatEntry.unit` | `if eq is S.true: return S.One` | I (R on leaf) | definite-equal branch; `unit` ↔ `S.One` (mapping.md §2). Control flow transliterated. |
| A4 | `else … if eq = some false then MatEntry.null` | `elif eq is S.false: return S.Zero` | I (R on leaf) | definite-distinct branch; `null` ↔ `S.Zero`. (The `else`/nested-`if` ladder is the Velvet transliteration of `elif`, which is banned syntactically; behaviour identical.) |
| A5 | param `kd : Option Bool` | the three-valued value the `KroneckerDelta(i, j)` call itself denotes (`KroneckerDelta.eval`, `tensor_functions.py:136-175`) | R + A-reference (input) | the indicator's OWN verdict ↔ `Option Bool` (mapping.md §2). It is an INDEPENDENT input, not derivable from `eq`: the indicator's rules (`diff.is_zero`/`fuzzy_not`, lines 158-162; below_fermi/above_fermi, lines 164-169) are strictly broader than `Eq`'s. G-CONF computes the real value to build the input; G-AX checks the `kdval` bridge is total/exact. |
| A6 | `else coincideValue i j kd` — i.e. `if kd = some true then unit else if kd = some false then null else coincide i j` | `return KroneckerDelta(i, j)`, and the value that call DENOTES | A-reference + I (R on leaves) | the fall-through (comparison UNSETTLED) branch. The patch's single `return KroneckerDelta(i, j)` is not a single value: the call self-evaluates to `S.One`, `S.Zero`, or an unevaluated `KroneckerDelta` by its own rules, so the model performs the same three-way collapse via `coincideValue` — `unit`/`null`/`coincide i j` ↔ `S.One`/`S.Zero`/unevaluated `KroneckerDelta` (mapping.md §2). Modeling this branch as an ALWAYS-unevaluated indicator would be unfaithful on the populated below_fermi/above_fermi class, where the real `_entry` returns `S.Zero` (mapping.md §3.1). The constructor applications are **I**; the equality to the real unchanged `KroneckerDelta` callee is the **A-reference** validated by G-AX/G-CONF. No consumed `KroneckerDelta` axiom. |

The whole modeled output is a deep model (`entryFor` composed with
`coincideValue`) of the value the unchanged library value-builders (`S.One`,
`S.Zero`, `KroneckerDelta`) produce under the TWO three-valued verdicts: an
**A-reference** validated == the real `Identity(n)[i, j]` by G-CONF. There is **no consumed axiom** — the builders are
unchanged callees exercised end-to-end (G-CONF) and component-checked (G-AX),
not abstracted behind an `ensures` the proof consumes.

## B. The pre-change skeleton (G-DIFF)

Pre-patch `_entry` tested `if i == j` (Python two-valued structural equality):
equal → `S.One`, **else** → `S.Zero`. An UNSETTLED comparison (distinct symbolic
indices whose coincidence `Eq` cannot decide) fell into that `else` and collapsed
to `S.Zero`, with no deferral to the indicator at all. `Solution_prepatch.lean` models this by returning `MatEntry.null` on
the non-`some true` branch (i.e. on both `some false` AND `none`), which is
**not** the coincidence indicator the spec demands on `none`, so verification
fails on exactly the discriminating clauses:

```
case «ensures_1: eq = none → kd = none → out ≠ MatEntry.null»          -- unsolved
case «ensures_2: eq = none → kd = none → out = MatEntry.coincide i j»  -- unsolved
case «ensures_4: eq = none → kd = some true  → out = MatEntry.unit»    -- unsolved
case «ensures_5: eq = none → out = coincideValue i j kd»               -- unsolved
case «ensures_8: out = entryFor i j eq kd»                             -- unsolved
```
(Measured: `lean_verify.sh Solution_prepatch.lean` exits 1 with these five goals.)

This is the F2P discriminator: at base the symbolic entry `In[i, j]` is `0` (the
undetermined case collapsed to the zero), so `In[i, j] != 0` is False and the
double summation vanishes; post-patch the undetermined case is the coincidence
indicator (nonzero, summation-reducible), so the sum recovers `n`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, I, or A-reference. The operation that genuinely changed — the
value returned when the comparison does not settle the pair — is modeled
**deeply** (`coincideValue i j kd`, collapsing to `MatEntry.coincide i j` over the
operands where the indicator declines, steps A5–A6), not hidden behind an axiom
about the function under change. There is **no consumed `_entry` axiom** and no
answer-key oracle: `entryFor` is a transparent constructor expression over the
verdict and the operands `i, j`, so its postcondition is dischargeable only by
emitting the exact value (unit / zero / coincidence-indicator-over-`i,j`) the
modeled branch produces at BOTH verdicts (mapping.md §2 grounding).

A math-adjacent but structurally-different fall-through value — e.g. a two-clause
case split `Piecewise((1, Eq(i,j)), (0, True))` (the issue's first hint
candidate) — does **not** satisfy `out = entryFor i j eq kd` (it is not
`coincide i j`) and, correspondingly, does **not** pass the F2P assert: in the
real library the *nested* double sum of the `Piecewise` form does NOT reduce to
`n` (it leaves `Piecewise((3, Eq(i,0)), …) + …`), whereas the coincidence
indicator does. So the structural pin is exactly the F2P criterion — the spec is
neither too weak (the `Piecewise` counter-impl and the base zero-collapse are
both rejected) nor an echo (the value is built from the operands).

## D. verify(Solution) ⇒ resolved

`identityEntry` verifies only if its output equals `entryFor i j eq kd` — the unit
on a definite-equal comparison, the zero on a definite-distinct comparison, and,
when the comparison is unsettled, exactly the value the coincidence indicator
itself denotes at those operands (A3–A6): the unit or the zero where the
indicator's own rules settle the pair, and the unevaluated indicator over the
operands — in particular **not** the zero — where they do not. By R (`MatEntry`
constructor ↔ library value-builder, each `Option Bool` ↔ its three-valued
verdict; mapping.md §2) the verified output transliterates to the real value the
gold `_entry` returns; by the A-reference (G-CONF) that deep model equals the real
`Identity(n)[i, j]` (post-patch) under structural equality on 100 000 index-pair
configurations — including below_fermi/above_fermi pairs, so the class where the
two verdicts DISAGREE is covered rather than assumed empty; by G-AX both
component bridges (`Eq` verdict via `threeval`, the indicator's own verdict via
`kdval`) meet the modeled semantics in isolation, and G-AX additionally witnesses
the populated cross-class. That structural object is exactly what the
sole FAIL_TO_PASS `test_Identity` asserts on (nonzero entry; double sum `= n`).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited unchanged callees — and the gold
patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1:
deep-model / component soundness (G-AX, G-CONF) and refinement fidelity (this
doc, G-EQ + G-CONF); there are no consumed axioms.
