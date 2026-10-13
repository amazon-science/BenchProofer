# refinement.md — sympy__sympy-13852

The operation-by-operation correspondence between `model.py`'s implementation
(the `recognize_closed_form` and `series_expansion_at_one` impl regions, plus the
concrete `closed_form_for` / `expansion_code` pure maps) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (the
proof uses a `@ContractOnly` axiom's `Ensures`), **A-reference** (a deep/concrete
model is validated == the real callee by axiom_check.py / G-AX, NOT consumed), or
**I** (identical concrete control flow). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (applies at `base_commit`; the real
correctness oracle, G-RESOLVE).

The gold patch fixes TWO behaviours; the GATED resolution (F2P
`test_polylog_values`) rests on behaviour A alone (see §B for behaviour B's
non-gating status). Each behaviour is modeled as its own function with its own
failing prepatch (G-DIFF). The model.py spec view uses neutral identifiers
(the closed forms are referenced structurally, not named) to avoid leakage; the
neutral↔concrete key is in mapping.md §1.

## A. The value-dispatch site — `polylog.eval(cls, s, z)`  (GATING)

Gold hunk (`sympy/functions/special/zeta_functions.py`, body of `eval`, lines
274-279 → expanded):
```
  elif z == 0:
-     return 0
+     return S.Zero
+ elif s == 2:
+     if z == S.Half:        return pi**2/12 - log(2)**2/2
+     elif z == 2:           return pi**2/4 - I*pi*log(2)
+     elif z == -(sqrt(5)-1)/2: return -pi**2/15 + log((sqrt(5)-1)/2)**2/2
+     elif z == -(sqrt(5)+1)/2: return -pi**2/10 - log((sqrt(5)+1)/2)**2
+     elif z == (3-sqrt(5))/2:  return pi**2/15 - log((sqrt(5)-1)/2)**2
+     elif z == (sqrt(5)-1)/2:  return pi**2/10 - log((sqrt(5)-1)/2)**2
+ elif s == 0:               return z/(1 - z)
+ elif s == -1:              return z/(1 - z)**2
```

Model: `recognize_closed_form(s: int, z_tag: int) -> int`, returning a
closed-form CODE.

| # | model.py impl op (`recognize_closed_form`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `s: int` | `s` (a SymPy expression) | R | the dispatch branches only on the discrete predicates `s == 2` (`S_SPECIAL`), `s == 0` (`S_KEY_A`), `s == -1` (`S_KEY_B`) (and otherwise); the integer `s` carries exactly those distinctions (mapping.md §2). |
| A2 | parameter `z_tag: int` ∈ {0..9} | `z` (a SymPy expression) | R | `z` enters the dispatch only through the discrete equality tests `z == 1, -1, 0, 1/2, 2,` and the four golden-ratio points; `z_tag` is the finite quotient of `z` by exactly those equalities, `Z_OTHER` for any unrecognised `z` (mapping.md §2). |
| A3 | `if z_tag == Z_A: return CF_ZA` | `if z == 1: return zeta(s)` | I + R | identical priority-1 (z-keyed) branch; the returned form is the s-only zeta value (CF_ZA names `zeta(s)`). |
| A4 | `if z_tag == Z_B: return CF_ZB` | `elif z == -1: return -dirichlet_eta(s)` | I + R | identical priority-1 (z-keyed) branch (CF_ZB names `-dirichlet_eta(s)`). |
| A5 | `if z_tag == Z_C: return CF_ZC` | `elif z == 0: return S.Zero` | I + R | identical priority-1 (z-keyed) branch; CF_ZC names the exact zero `S.Zero`. The pre-patch returned the python int `0` here; `S.Zero` is the SymPy exact zero — observationally identical for the F2P (`polylog(s,0)==0`) but the patch upgrades the literal. The discriminating fix at this site is the s=2 / s∈{0,-1} cascade below. |
| A6 | the six `if s == S_SPECIAL and z_tag == Z_*: return CF_P*` branches | the six `elif s == 2: if z == …` branches | I + A-reference | identical nested dispatch; each CODE (CF_P1 … CF_P6) names the exact gold dilog closed form. That the named closed form EQUALS the real `polylog(2, z)` at that argument is validated by axiom_check.py (G-AX) against the real callee — an **A-reference**, not a consumed axiom. |
| A7 | `if s == S_KEY_A: return CF_SA` / `if s == S_KEY_B: return CF_SB` | `elif s == 0: return z/(1-z)` / `elif s == -1: return z/(1-z)**2` | I + A-reference | identical priority-3 (s-keyed) branches; CF_SA names `z/(1-z)`, CF_SB names `z/(1-z)**2`. Their equality to the real `polylog(0,z)` / `polylog(-1,z)` is G-AX-validated (A-reference). |
| A8 | final `return CF_UNEVAL` | (implicit `return None` — falls through to the unevaluated `polylog`) | I + R | an unrecognised pattern produces no closed form. CF_UNEVAL ↔ the gold `eval` returning `None` (the call stays a `polylog` instance). axiom_check.py asserts the real callee STAYS unevaluated on unrecognised patterns (no over-fire). |
| A9 | `Requires(MustTerminate(2))` | the real `eval` is a loop-free `if/elif` equality cascade; it always completes (returning a closed form or `None`) | R | total-correctness obligation: the real dispatch always ANSWERS. Nagini is a partial-correctness verifier by default, so without the obligation a non-terminating impl (an infinite loop before an unreachable return) satisfies every value `Ensures` vacuously — the spec-too-weak hole the G-PANEL-1 audit exploited (its `atk_8_oracle_echo` witness verified with an unreachable `return closed_form_for(s, z_tag)` behind a diverging loop). A diverging `eval` would hang every `polylog(...)` construction and the F2P test, so it does not resolve. |

The dispatch **priority** (z-keyed clauses before the s-keyed clauses) is pinned
by the `closed_form_for` cascade in the postcondition `Result() ==
closed_form_for(s, z_tag)`: e.g. `closed_form_for(0, Z_A) == CF_ZA`, never CF_SA.
G-AX confirms this on the real callee (`polylog(0,1) == zeta(0)`, not a division
by zero).

The discriminating content of this site — the s=2 specials, z=0→S.Zero, and
s∈{0,-1} now produce closed forms where the pre-patch left them **unevaluated** —
lives in the cascade past the three z-keyed clauses. `model_prepatch.py`
reproduces the pre-patch (only the three z-keyed clauses recognised, everything
else `CF_UNEVAL`) and **fails** the postcondition `Result() ==
closed_form_for(s, z_tag)` (G-DIFF), which is exactly the spec sensing the
change. This is the gating behaviour: the F2P `test_polylog_values` enumerates
the six s=2 specials and the s∈{0,-1} numeric loop, all of which exercise this
dispatch.

## B. The series-expansion site — `polylog._eval_expand_func` at s = 1  (NON-GATING CO-FIX)

Gold hunk (`sympy/functions/special/zeta_functions.py`, line 293-294):
```
  if s == 1:
-     return -log(1 + exp_polar(-I*pi)*z)
+     return -log(1 - z)
```

Model: `series_expansion_at_one(s: int) -> int` (precondition `s == 1`),
returning an expansion CODE.

| # | model.py impl op (`series_expansion_at_one`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | precondition `s == 1` (`S_EXPAND`) | `if s == 1:` guard | I + R | the modeled branch is exactly the s=1 case of `_eval_expand_func`. |
| B2 | `return EXP_PLAIN` | `return -log(1 - z)` | I + A-reference | EXP_PLAIN names the elementary single real logarithm `-log(1 - z)` (no polar factor); EXP_POLAR names the pre-patch `-log(1 + exp_polar(-I*pi)*z)`. That `expand_func(polylog(1,z))` equals `-log(1-z)` and is `exp_polar`-free is validated by axiom_check.py (G-AX) — an **A-reference**. |
| B3 | `Requires(MustTerminate(2))` | the `s == 1` branch is a single `return`; it always completes | R | same total-correctness obligation as A9: without it a diverging impl satisfies the value `Ensures` vacuously. |

`model_prepatch_2.py` reproduces the pre-patch (`return EXP_POLAR`) and **fails**
the postcondition `Result() == expansion_code(s)` (G-DIFF), so the spec senses
this change too.

**Non-gating status (Defect 3, panel verdict).** This `_eval_expand_func` s=1
change is part of the gold diff and is exercised by `test_polylog_expansion`
(modified by the gold `test_patch`: `myexpand(polylog(1, z), -log(1 - z))`), but
that test is in NEITHER `FAIL_TO_PASS` nor `PASS_TO_PASS`. The single F2P,
`test_polylog_values`, exercises the s=1 case only via numeric `.evalf()`
agreement (the `for s in [-1, 0, 1]` loop), which goes through auto-evaluation /
numeric evaluation — NOT through `expand_func` / `_eval_expand_func`. So the
GATED resolution rests SOLELY on behaviour A (the eval dispatch). Behaviour B is
modeled and its prepatch fails for faithfulness (it IS part of the gold fix and
keeps a per-hunk skeleton + differential witness), but it is documented here as a
**non-gating co-fix**: the `verify ⟹ resolved` guarantee depends only on
behaviour A; behaviour B's contract is a faithful but non-scored addition.
Because the spec is a conjunction the gold patch satisfies in full (and
G-RESOLVE runs the gold patch verbatim), `verify ⟹ resolved` is preserved — the
spec is (intentionally) at least as strong as the gold fix, never weaker.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. There is **no consumed `@ContractOnly`
axiom**: the changed operation (which closed form each pattern produces, and the
polar-free s=1 expansion) is modelled CONCRETELY as a discrete dispatch
(`closed_form_for` / `expansion_code` are plain `@Pure` maps in the `pure`
region), and the MATHEMATICAL correctness of each code-named closed form is
validated against the real callee out-of-band by G-AX (the A-references in
A6/A7/B2), never assumed by an axiom the proof consumes. There is no oracle echo
(directive 8): the postconditions pin `Result()` to the concrete cascade
`closed_form_for(s, z_tag)`, a per-pattern structural map of the discrete inputs
`s`/`z_tag` whose body IS the computation (a `@Pure` cascade, not an opaque
`@ContractOnly` answer-key) — echoing it is a positive control, not a cheat.
Vacuous satisfaction of the value postconditions by a NON-TERMINATING impl (the
one same-spec hole the G-PANEL-1 audit found) is closed by the
`Requires(MustTerminate(2))` obligations (steps A9/B3): Nagini's obligation
leak check rejects any loop that does not carry a decreasing termination
measure, so an infinite loop before an unreachable return no longer verifies.

## D. verify(model) ⇒ resolved

`recognize_closed_form` verifies only if its result equals the full priority
cascade `closed_form_for(s, z_tag)` — so it must produce
CF_P1/…/CF_P6/CF_SA/CF_SB for the newly-recognised patterns (not CF_UNEVAL) and
respect the z-keyed priority. By R (`s`/`z` ↔ their discrete dispatch quotient;
CODE ↔ the named closed form) the verified dispatch is the gold `eval` control
flow; by G-AX the code-named closed forms equal the real `polylog`
(A-references A6/A7) and the dispatch does not over-fire. Therefore a model
satisfying behaviour A, refined by the map above, is the gold `eval` up to type
refinement and the audited A-references — and the gold patch resolves the F2P
`test_polylog_values` (G-RESOLVE). `series_expansion_at_one` adds the faithful
non-gating co-fix B (also gold-faithful and G-AX-validated). The trust points
are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ).
