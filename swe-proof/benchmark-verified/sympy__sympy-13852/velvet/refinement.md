# refinement.md — sympy__sympy-13852

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `recognizeClosedForm` and `seriesExpansionAtOne` `do` blocks, plus the
concrete `closedFormFor` / `expansionCode` pure maps) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-reference** (a
deep/concrete model is validated == the real callee by `axiom_check.py` / G-AX,
NOT a consumed axiom), or **I** (identical concrete control flow). There is no
**A-consumed** axiom and no kind-3 step.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A-reference legs and this narrative are audited by **G-AX** / **G-EQ**.
Claim: any implementation verifying against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`; the real
correctness oracle, G-RESOLVE).

The gold patch fixes TWO behaviours; the GATED resolution (the single F2P
`test_polylog_values`) rests on behaviour A alone (see §B for behaviour B's
non-gating status). Each behaviour is modeled as its own method with its own
failing prepatch (G-DIFF). The `Solution.lean` spec view uses neutral
identifiers (the closed forms are referenced structurally, not named) to avoid
leakage; the neutral↔concrete key is in `mapping.md` §1.

## A. The value-dispatch site — `recognizeClosedForm (s, zTag)`  (GATING)

Gold hunk (body of the modeled `eval` dispatch, `polylog.eval`):
```
  elif z == 0:
-     return 0
+     return S.Zero
+ elif s == 2:
+     if z == 1/2:        ...        # six special-z closed forms
+     ...
+ elif s == 0:               return z/(1 - z)
+ elif s == -1:              return z/(1 - z)**2
```

Model: `recognizeClosedForm(s : Int, zTag : Int) -> Int`, returning a
closed-form CODE.

| # | `Solution.lean` impl op (`recognizeClosedForm`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `s : Int` | `s` (a SymPy expression) | R | the dispatch branches only on the discrete predicates `s = sSpecial`, `s = sKeyA`, `s = sKeyB` (and otherwise); the integer `s` carries exactly those distinctions (mapping.md §2). |
| A2 | parameter `zTag : Int` ∈ {0..9} | `z` (a SymPy expression) | R | `z` enters the dispatch only through the discrete equality tests `z == 1, -1, 0, 1/2, 2,` and the four golden-ratio points; `zTag` is the finite quotient of `z` by exactly those equalities, `zOther` for any unrecognised `z` (mapping.md §2). |
| A3 | `if zTag = zA then cfZa` | the first z-keyed clause (`z == 1`) | I + R | identical priority-1 (z-keyed) branch; the returned form is the s-only value (`cfZa`). Unchanged across the fix. |
| A4 | `else if zTag = zB then cfZb` | the second z-keyed clause (`z == -1`) | I + R | identical priority-1 (z-keyed) branch (`cfZb`). Unchanged across the fix. |
| A5 | `else if zTag = zC then cfZc` | `elif z == 0: return S.Zero` | I + R | identical priority-1 (z-keyed) branch; `cfZc` names the exact zero. (The pre-patch returned a plain integer literal here; the closed form is observationally identical for the F2P, so the discriminating fix at this site is the s=2 / s∈{0,-1} cascade below.) |
| A6 | the six `if s = sSpecial then if zTag = z_k then cfP_k` branches | the six `elif s == 2: if z == …` branches | I + A-reference | identical nested dispatch; each CODE (`cfP1`..`cfP6`) names the exact gold closed form at the distinguished s. That the named closed form EQUALS the real function at that argument is validated by `axiom_check.py` (G-AX) against the real callee — an **A-reference**, not a consumed axiom. |
| A7 | `else if s = sKeyA then cfSa` / `else if s = sKeyB then cfSb` | `elif s == 0: return z/(1-z)` / `elif s == -1: return z/(1-z)**2` | I + A-reference | identical priority-3 (s-keyed) branches; `cfSa` names `z/(1-z)`, `cfSb` names `z/(1-z)**2`. Their equality to the real function is G-AX-validated (A-reference). |
| A8 | final `else cfUneval` | (implicit fall-through: the call stays unevaluated) | I + R | an unrecognised pattern produces no closed form. `cfUneval` ↔ the gold dispatch returning nothing (the call stays an unevaluated instance). `axiom_check.py` asserts the real callee STAYS unevaluated on unrecognised patterns (no over-fire). |

The dispatch **priority** (z-keyed clauses before the s-keyed clauses) is pinned
by the `closedFormFor` cascade in the postcondition `out = closedFormFor s zTag`:
e.g. `closedFormFor sKeyA zA = cfZa`, never `cfSa` (the explicit `ensures (zTag =
zA ∧ s = sKeyA) → out = cfZa` makes this concrete). G-AX confirms this on the
real callee (`polylog(0,1) == zeta(0)`, not a division by zero).

The discriminating content of this site — the s=2 specials and s∈{0,-1} now
produce closed forms where the pre-patch left them **unevaluated** — lives in the
cascade past the three z-keyed clauses. `Solution_prepatch.lean` reproduces the
pre-patch (only the three z-keyed clauses recognised, everything else
`cfUneval`) and **fails** the postcondition `out = closedFormFor s zTag` (plus
the explicit `cfP1`/`cfP2`/`cfSa`/`cfSb` clauses) — exactly the spec sensing the
change (G-DIFF). This is the gating behaviour: the F2P `test_polylog_values`
enumerates the six s=2 specials and the s∈{0,-1} numeric loop, all of which
exercise this dispatch.

## B. The series-expansion site — `seriesExpansionAtOne (s)`  (NON-GATING CO-FIX)

Gold hunk (the `s == 1` branch of `_eval_expand_func`):
```
  if s == 1:
-     return -log(1 + exp_polar(-I*pi)*z)
+     return -log(1 - z)
```

Model: `seriesExpansionAtOne(s : Int) -> Int` (precondition `s = sExpand`),
returning an expansion CODE.

| # | `Solution.lean` impl op (`seriesExpansionAtOne`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | precondition `s = sExpand` | the `if s == 1:` guard | I + R | the modeled branch is exactly the distinguished-s case. |
| B2 | `return expPlain` | `return -log(1 - z)` | I + A-reference | `expPlain` names the elementary single real logarithm `-log(1 - z)` (no polar factor); `expPolar` names the pre-patch polar-factored form. That `expand_func` of the function at the distinguished s equals `-log(1-z)` and is polar-free is validated by `axiom_check.py` (G-AX) — an **A-reference**. |

`Solution_prepatch_2.lean` reproduces the pre-patch (`return expPolar`) and
**fails** the postconditions `out = expansionCode` / `out = expPlain` / `out ≠
expPolar` (G-DIFF), so the spec senses this change too.

**Non-gating status.** This series-expansion change is part of the gold diff and
is exercised by a test that the gold `test_patch` modifies, but that test is in
NEITHER `FAIL_TO_PASS` nor `PASS_TO_PASS`. The single F2P,
`test_polylog_values`, exercises the distinguished-s case only via numeric
`.evalf()` agreement, which goes through auto-evaluation / numeric evaluation —
NOT through the series-expansion branch. So the GATED resolution rests SOLELY on
behaviour A. Behaviour B is modeled and its prepatch fails for faithfulness (it
IS part of the gold fix and keeps a per-hunk skeleton + differential witness),
but it is documented here as a **non-gating co-fix**: the `verify ⟹ resolved`
guarantee depends only on behaviour A; behaviour B's contract is a faithful but
non-scored addition. Because the spec is a conjunction the gold patch satisfies
in full (and G-RESOLVE runs the gold patch verbatim), `verify ⟹ resolved` is
preserved — the spec is (intentionally) at least as strong as the gold fix, never
weaker.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. There is **no consumed axiom**: the
changed operation (which closed form each pattern produces, and the polar-free
distinguished-s expansion) is modelled CONCRETELY as a discrete dispatch
(`closedFormFor` / `expansionCode` are plain functions in the `pure` region),
and the MATHEMATICAL correctness of each code-named closed form is validated
against the real callee out-of-band by G-AX (the A-references in A6/A7/B2),
never assumed by an axiom the proof consumes. There is no oracle echo (directive
8): the postconditions pin `out` to the concrete cascade `closedFormFor s zTag`,
a per-pattern structural map of the discrete inputs `s`/`zTag` whose body IS the
computation (a pure cascade, not an opaque answer-key) — echoing it is a positive
control, not a cheat.

## D. verify(Solution) ⇒ resolved

`recognizeClosedForm` verifies only if its result equals the full priority
cascade `closedFormFor s zTag` — so it must produce
`cfP1`/…/`cfP6`/`cfSa`/`cfSb` for the newly-recognised patterns (not `cfUneval`)
and respect the z-keyed priority. By R (`s`/`z` ↔ their discrete dispatch
quotient; CODE ↔ the named closed form) the verified dispatch is the gold `eval`
control flow; by G-AX the code-named closed forms equal the real function
(A-references A6/A7) and the dispatch does not over-fire. Therefore a model
satisfying behaviour A, refined by the map above, is the gold dispatch up to type
refinement and the audited A-references — and the gold patch resolves the F2P
`test_polylog_values` (G-RESOLVE). `seriesExpansionAtOne` adds the faithful
non-gating co-fix B (also gold-faithful and G-AX-validated). The trust points are
exactly the two of plan §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ + G-CONF).
