# P2 adversarial audit — sympy__sympy-13852

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -122,16 +122,6 @@
   if z = .lit 1 then return some (.zeta s)
   if z = .lit (-1) then return some (.neg (.eta s))
   if z = .lit 0 then return some (.lit 0)
-  if s = .lit 2 then
-    if z = SymExpr.half then return some SymExpr.outHalf
-    if z = .lit 2 then return some SymExpr.outTwo
-    if z = SymExpr.zA then return some SymExpr.outA
-    if z = SymExpr.zB then return some SymExpr.outB
-    if z = SymExpr.zC then return some SymExpr.outC
-    if z = SymExpr.gSub then return some SymExpr.outD
-    return none
-  if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
-  if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
   return none
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,7 +130,6 @@
     if z = SymExpr.zC then return some SymExpr.outC
     if z = SymExpr.gSub then return some SymExpr.outD
     return none
-  if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
   if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
   return none
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,7 +123,7 @@
   if z = .lit (-1) then return some (.neg (.eta s))
   if z = .lit 0 then return some (.lit 0)
   if s = .lit 2 then
-    if z = SymExpr.half then return some SymExpr.outHalf
+    if z = SymExpr.half then return some SymExpr.outTwo
     if z = .lit 2 then return some SymExpr.outTwo
     if z = SymExpr.zA then return some SymExpr.outA
     if z = SymExpr.zB then return some SymExpr.outB
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,6 +121,7 @@
 def implementation_polylogEval (s z : SymExpr) : Option SymExpr := Id.run do
   if z = .lit 1 then return some (.zeta s)
   if z = .lit (-1) then return some (.neg (.eta s))
+  if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
   if z = .lit 0 then return some (.lit 0)
   if s = .lit 2 then
     if z = SymExpr.half then return some SymExpr.outHalf
@@ -130,7 +131,6 @@
     if z = SymExpr.zC then return some SymExpr.outC
     if z = SymExpr.gSub then return some SymExpr.outD
     return none
-  if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
   if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
   return none
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,7 +131,7 @@
     if z = SymExpr.gSub then return some SymExpr.outD
     return none
   if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
-  if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
+  if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 1))
   return none
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -129,6 +129,7 @@
     if z = SymExpr.zB then return some SymExpr.outB
     if z = SymExpr.zC then return some SymExpr.outC
     if z = SymExpr.gSub then return some SymExpr.outD
+    if z = SymExpr.gAdd then return some SymExpr.outD
     return none
   if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
   if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -118,21 +118,21 @@
 -- impl-start
 /-- Dispatch on the argument `z`, then (for the recognized orders) on `z` again or
 on `s`, returning the matching closed form or `none`. -/
-def implementation_polylogEval (s z : SymExpr) : Option SymExpr := Id.run do
-  if z = .lit 1 then return some (.zeta s)
-  if z = .lit (-1) then return some (.neg (.eta s))
-  if z = .lit 0 then return some (.lit 0)
-  if s = .lit 2 then
-    if z = SymExpr.half then return some SymExpr.outHalf
-    if z = .lit 2 then return some SymExpr.outTwo
-    if z = SymExpr.zA then return some SymExpr.outA
-    if z = SymExpr.zB then return some SymExpr.outB
-    if z = SymExpr.zC then return some SymExpr.outC
-    if z = SymExpr.gSub then return some SymExpr.outD
-    return none
-  if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
-  if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
-  return none
+def implementation_polylogEval (s z : SymExpr) : Option SymExpr :=
+  if z = .lit 1 then some (.zeta s)
+  else if z = .lit (-1) then some (.neg (.eta s))
+  else if z = .lit 0 then some (.lit 0)
+  else if s = .lit 2 then
+    (if z = SymExpr.half then some SymExpr.outHalf
+     else if z = .lit 2 then some SymExpr.outTwo
+     else if z = SymExpr.zA then some SymExpr.outA
+     else if z = SymExpr.zB then some SymExpr.outB
+     else if z = SymExpr.zC then some SymExpr.outC
+     else if z = SymExpr.gSub then some SymExpr.outD
+     else none)
+  else if s = .lit 0 then some (.div z (.sub (.lit 1) z))
+  else if s = .lit (-1) then some (.div z (.powInt (.sub (.lit 1) z) 2))
+  else none
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -119,8 +119,8 @@
 /-- Dispatch on the argument `z`, then (for the recognized orders) on `z` again or
 on `s`, returning the matching closed form or `none`. -/
 def implementation_polylogEval (s z : SymExpr) : Option SymExpr := Id.run do
-  if z = .lit 1 then return some (.zeta s)
-  if z = .lit (-1) then return some (.neg (.eta s))
+  if z = .lit 1 then return some (.neg (.eta s))
+  if z = .lit (-1) then return some (.zeta s)
   if z = .lit 0 then return some (.lit 0)
   if s = .lit 2 then
     if z = SymExpr.half then return some SymExpr.outHalf
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Closed-form evaluation of a parametrized special function at a symbolic argument.

The function takes an order parameter `s` and an argument `z`, both symbolic
expressions, and returns either a closed-form value (when the pair falls into a
recognized case) or "no closed form" (the call is left as the unevaluated
function application).

The recognized cases are:

* three distinguished arguments (`z = 1`, `z = -1`, `z = 0`), handled for every
  order `s` and returning, respectively, a companion zeta-type value, the
  negation of an eta-type value, and `0`;
* for the specific order `s = 2`, a finite table of six distinguished arguments,
  each mapping to a transcendental closed form;
* for the orders `s = 0` and `s = -1`, a rational closed form in `z`.

Every other `(s, z)` pair has no closed form and the result is "none".

Modeled as an input→output relation: a pair of symbolic expressions ↦ an optional
symbolic expression. The implementation and the correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract: this behavior is a
-- pure structural dispatch over the symbolic argument, returning closed-form
-- expressions built from the symbolic carrier below. There is therefore no
-- `axiom <callee>_prop` for the proof to consume.

/-- A minimal symbolic-expression carrier: the fragment of the host algebra
needed to state the recognized arguments and their closed-form values. Two
expressions are considered equal iff they are built identically (structural
equality), mirroring the host system's structural comparison of these particular
construction forms. The companions `zeta`/`eta` and the constants `pi`, `imagUnit`
(the imaginary unit), `sqrt5` (the square root of five) are opaque builders. -/
inductive SymExpr where
  | lit : Int → SymExpr
  | pi : SymExpr
  | imagUnit : SymExpr
  | sqrt5 : SymExpr
  | log : SymExpr → SymExpr
  | zeta : SymExpr → SymExpr
  | eta : SymExpr → SymExpr
  | neg : SymExpr → SymExpr
  | add : SymExpr → SymExpr → SymExpr
  | sub : SymExpr → SymExpr → SymExpr
  | mul : SymExpr → SymExpr → SymExpr
  | div : SymExpr → SymExpr → SymExpr
  | powInt : SymExpr → Int → SymExpr
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- One half, `1/2`. -/
def SymExpr.half : SymExpr := .div (.lit 1) (.lit 2)
/-- `(√5 − 1)/2`. -/
def SymExpr.gSub : SymExpr := .div (.sub .sqrt5 (.lit 1)) (.lit 2)
/-- `(√5 + 1)/2`. -/
def SymExpr.gAdd : SymExpr := .div (.add .sqrt5 (.lit 1)) (.lit 2)
/-- `−(√5 − 1)/2`. -/
def SymExpr.zA : SymExpr := .neg SymExpr.gSub
/-- `−(√5 + 1)/2`. -/
def SymExpr.zB : SymExpr := .neg SymExpr.gAdd
/-- `(3 − √5)/2`. -/
def SymExpr.zC : SymExpr := .div (.sub (.lit 3) .sqrt5) (.lit 2)

/-- `π²`. -/
def SymExpr.piSq : SymExpr := .powInt .pi 2

/-- Closed form at the half argument: `π²/12 − log(2)²/2`. -/
def SymExpr.outHalf : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 12)) (.div (.powInt (.log (.lit 2)) 2) (.lit 2))
/-- Closed form at the argument `2`: `π²/4 − I·π·log(2)`. -/
def SymExpr.outTwo : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 4)) (.mul (.mul .imagUnit .pi) (.log (.lit 2)))
/-- Closed form at `−(√5 − 1)/2`: `−π²/15 + log((√5−1)/2)²/2`. -/
def SymExpr.outA : SymExpr :=
  .add (.neg (.div SymExpr.piSq (.lit 15))) (.div (.powInt (.log SymExpr.gSub) 2) (.lit 2))
/-- Closed form at `−(√5 + 1)/2`: `−π²/10 − log((√5+1)/2)²`. -/
def SymExpr.outB : SymExpr :=
  .sub (.neg (.div SymExpr.piSq (.lit 10))) (.powInt (.log SymExpr.gAdd) 2)
/-- Closed form at `(3 − √5)/2`: `π²/15 − log((√5−1)/2)²`. -/
def SymExpr.outC : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 15)) (.powInt (.log SymExpr.gSub) 2)
/-- Closed form at `(√5 − 1)/2`: `π²/10 − log((√5−1)/2)²`. -/
def SymExpr.outD : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 10)) (.powInt (.log SymExpr.gSub) 2)
-- pure-end

-- post-conditions-start
/-- The result is the closed-form value of the order-`s` function at argument `z`,
or `none` when the pair has no closed form. The three distinguished arguments take
priority over the order, matching for every `s`; the order `s = 2` selects from a
finite argument table (no match ⇒ `none`); orders `s = 0` and `s = -1` give a
rational form in `z`; everything else is `none`. Every case pins the result, so no
output is left unconstrained. -/
def problem_spec_polylogEval (s z : SymExpr) (result : Option SymExpr) : Prop :=
  if z = .lit 1 then result = some (.zeta s)
  else if z = .lit (-1) then result = some (.neg (.eta s))
  else if z = .lit 0 then result = some (.lit 0)
  else if s = .lit 2 then
    (if z = SymExpr.half then result = some SymExpr.outHalf
     else if z = .lit 2 then result = some SymExpr.outTwo
     else if z = SymExpr.zA then result = some SymExpr.outA
     else if z = SymExpr.zB then result = some SymExpr.outB
     else if z = SymExpr.zC then result = some SymExpr.outC
     else if z = SymExpr.gSub then result = some SymExpr.outD
     else result = none)
  else if s = .lit 0 then result = some (.div z (.sub (.lit 1) z))
  else if s = .lit (-1) then result = some (.div z (.powInt (.sub (.lit 1) z) 2))
  else result = none
-- post-conditions-end

-- impl-start
/-- Dispatch on the argument `z`, then (for the recognized orders) on `z` again or
on `s`, returning the matching closed form or `none`. -/
def implementation_polylogEval (s z : SymExpr) : Option SymExpr := Id.run do
  if z = .lit 1 then return some (.zeta s)
  if z = .lit (-1) then return some (.neg (.eta s))
  if z = .lit 0 then return some (.lit 0)
  if s = .lit 2 then
    if z = SymExpr.half then return some SymExpr.outHalf
    if z = .lit 2 then return some SymExpr.outTwo
    if z = SymExpr.zA then return some SymExpr.outA
    if z = SymExpr.zB then return some SymExpr.outB
    if z = SymExpr.zC then return some SymExpr.outC
    if z = SymExpr.gSub then return some SymExpr.outD
    return none
  if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
  if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
  return none
-- impl-end

-- proof-start
set_option maxHeartbeats 4000000 in
theorem impl_eq (s z : SymExpr) :
    implementation_polylogEval s z =
    (if z = .lit 1 then some (.zeta s)
     else if z = .lit (-1) then some (.neg (.eta s))
     else if z = .lit 0 then some (.lit 0)
     else if s = .lit 2 then
       (if z = SymExpr.half then some SymExpr.outHalf
        else if z = .lit 2 then some SymExpr.outTwo
        else if z = SymExpr.zA then some SymExpr.outA
        else if z = SymExpr.zB then some SymExpr.outB
        else if z = SymExpr.zC then some SymExpr.outC
        else if z = SymExpr.gSub then some SymExpr.outD
        else none)
     else if s = .lit 0 then some (.div z (.sub (.lit 1) z))
     else if s = .lit (-1) then some (.div z (.powInt (.sub (.lit 1) z) 2))
     else none) := by
  unfold implementation_polylogEval
  rfl

set_option maxHeartbeats 4000000 in
theorem correct_polylogEval :
    ∀ (s z : SymExpr),
    problem_spec_polylogEval s z (implementation_polylogEval s z) := by
  intro s z
  rw [impl_eq]
  unfold problem_spec_polylogEval
  split_ifs <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_polylogEval is a FULLY-PINNED TOTAL function (every if-branch fixes `result` uniquely) and correct_polylogEval is a `∀ s z` statement. By Lean soundness a proof closes only if the impl is extensionally equal to the spec on all SymExpr. A-LEGS: axioms=[] (no consumed axiom; axiom_check.py is a skip stub; both verifying proofs depend only on [propext]). Exactly ONE A-reference leg: the whole SymExpr dispatch ladder + closed-form outputs as a deep model of post-patch polylog.eval, validated_by G-CONF (conformance_check.py). G-CONF recorded pass: 120171 checks, 0 disagreements, seed=13852 — model↔real-callee correspondence holds end-to-end. refinement.md legs #1-#11 are all R or I; it explicitly states 'No changed-inexpressible op.' — NO kind-3 leg. 

### ATTACKS (all same_spec=True, impl-region-only edits; verified concurrently ≤4 at a time via `bash scripts/lean_verify.sh <f>`):
- positive_control (gold): exit 0; #print axioms correct_polylogEval => [propext].
- atk_1 prepatch bug (only z∈{1,-1,0}, else none): exit 1 (fails). Prepatch reproduced.
- atk_2 partial-domain (drop s=0 rational branch): exit 1.
- atk_3 boundary/wrong-output (outTwo returned at z=½ instead of outHalf): exit 1.
- atk_4 control-flow-effect (test s=0 BEFORE z=0, corrupting z=0,s=0): exit 1.
- atk_5 ungrounded-oracle echo (s=-1 uses powInt ...1 instead of 2): exit 1.
- atk_6 over-eager (extra s=2,z=gAdd row returns outD where spec requires none): exit 1.
- atk_8 output-oracle swap (zeta↔eta at z=1 vs z=-1): exit 1.
- atk_7 EXTENSIONALLY-EQUAL ECHO (gold table rewritten as pure nested if/else, no Id.run): exit 0; #print axioms => [propext] (clean). 

MANDATORY RESOLVE (protocol step 2): atk_7 is the only verifying same-spec candidate. Its faithful refined patch = the bundle gold patch (behaviorally identical dispatch table; patch_equals_gold=True; verified byte-identical to gold_13852.patch). RAN under official harness: run_resolve('sympy__sympy-13852', atk_7_faithful.patch) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. 

CONCLUSION: all 7 genuinely-wrong impls FAIL to verify (spec catches partial-domain, boundary, control-flow, over-eager, oracle-swap, and prepatch defects); the single verifying candidate's materialized faithful patch RESOLVES. No verifying candidate has a non-resolving faithful patch ⇒ verify⇒correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Closed-form evaluation of a parametrized special function at a symbolic argument.

The function takes an order parameter `s` and an argument `z`, both symbolic
expressions, and returns either a closed-form value (when the pair falls into a
recognized case) or "no closed form" (the call is left as the unevaluated
function application).

The recognized cases are:

* three distinguished arguments (`z = 1`, `z = -1`, `z = 0`), handled for every
  order `s` and returning, respectively, a companion zeta-type value, the
  negation of an eta-type value, and `0`;
* for the specific order `s = 2`, a finite table of six distinguished arguments,
  each mapping to a transcendental closed form;
* for the orders `s = 0` and `s = -1`, a rational closed form in `z`.

Every other `(s, z)` pair has no closed form and the result is "none".

Modeled as an input→output relation: a pair of symbolic expressions ↦ an optional
symbolic expression. The implementation and the correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract: this behavior is a
-- pure structural dispatch over the symbolic argument, returning closed-form
-- expressions built from the symbolic carrier below. There is therefore no
-- `axiom <callee>_prop` for the proof to consume.

/-- A minimal symbolic-expression carrier: the fragment of the host algebra
needed to state the recognized arguments and their closed-form values. Two
expressions are considered equal iff they are built identically (structural
equality), mirroring the host system's structural comparison of these particular
construction forms. The companions `zeta`/`eta` and the constants `pi`, `imagUnit`
(the imaginary unit), `sqrt5` (the square root of five) are opaque builders. -/
inductive SymExpr where
  | lit : Int → SymExpr
  | pi : SymExpr
  | imagUnit : SymExpr
  | sqrt5 : SymExpr
  | log : SymExpr → SymExpr
  | zeta : SymExpr → SymExpr
  | eta : SymExpr → SymExpr
  | neg : SymExpr → SymExpr
  | add : SymExpr → SymExpr → SymExpr
  | sub : SymExpr → SymExpr → SymExpr
  | mul : SymExpr → SymExpr → SymExpr
  | div : SymExpr → SymExpr → SymExpr
  | powInt : SymExpr → Int → SymExpr
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- One half, `1/2`. -/
def SymExpr.half : SymExpr := .div (.lit 1) (.lit 2)
/-- `(√5 − 1)/2`. -/
def SymExpr.gSub : SymExpr := .div (.sub .sqrt5 (.lit 1)) (.lit 2)
/-- `(√5 + 1)/2`. -/
def SymExpr.gAdd : SymExpr := .div (.add .sqrt5 (.lit 1)) (.lit 2)
/-- `−(√5 − 1)/2`. -/
def SymExpr.zA : SymExpr := .neg SymExpr.gSub
/-- `−(√5 + 1)/2`. -/
def SymExpr.zB : SymExpr := .neg SymExpr.gAdd
/-- `(3 − √5)/2`. -/
def SymExpr.zC : SymExpr := .div (.sub (.lit 3) .sqrt5) (.lit 2)

/-- `π²`. -/
def SymExpr.piSq : SymExpr := .powInt .pi 2

/-- Closed form at the half argument: `π²/12 − log(2)²/2`. -/
def SymExpr.outHalf : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 12)) (.div (.powInt (.log (.lit 2)) 2) (.lit 2))
/-- Closed form at the argument `2`: `π²/4 − I·π·log(2)`. -/
def SymExpr.outTwo : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 4)) (.mul (.mul .imagUnit .pi) (.log (.lit 2)))
/-- Closed form at `−(√5 − 1)/2`: `−π²/15 + log((√5−1)/2)²/2`. -/
def SymExpr.outA : SymExpr :=
  .add (.neg (.div SymExpr.piSq (.lit 15))) (.div (.powInt (.log SymExpr.gSub) 2) (.lit 2))
/-- Closed form at `−(√5 + 1)/2`: `−π²/10 − log((√5+1)/2)²`. -/
def SymExpr.outB : SymExpr :=
  .sub (.neg (.div SymExpr.piSq (.lit 10))) (.powInt (.log SymExpr.gAdd) 2)
/-- Closed form at `(3 − √5)/2`: `π²/15 − log((√5−1)/2)²`. -/
def SymExpr.outC : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 15)) (.powInt (.log SymExpr.gSub) 2)
/-- Closed form at `(√5 − 1)/2`: `π²/10 − log((√5−1)/2)²`. -/
def SymExpr.outD : SymExpr :=
  .sub (.div SymExpr.piSq (.lit 10)) (.powInt (.log SymExpr.gSub) 2)
-- pure-end

-- post-conditions-start
/-- The result is the closed-form value of the order-`s` function at argument `z`,
or `none` when the pair has no closed form. The three distinguished arguments take
priority over the order, matching for every `s`; the order `s = 2` selects from a
finite argument table (no match ⇒ `none`); orders `s = 0` and `s = -1` give a
rational form in `z`; everything else is `none`. Every case pins the result, so no
output is left unconstrained. -/
def problem_spec_polylogEval (s z : SymExpr) (result : Option SymExpr) : Prop :=
  if z = .lit 1 then result = some (.zeta s)
  else if z = .lit (-1) then result = some (.neg (.eta s))
  else if z = .lit 0 then result = some (.lit 0)
  else if s = .lit 2 then
    (if z = SymExpr.half then result = some SymExpr.outHalf
     else if z = .lit 2 then result = some SymExpr.outTwo
     else if z = SymExpr.zA then result = some SymExpr.outA
     else if z = SymExpr.zB then result = some SymExpr.outB
     else if z = SymExpr.zC then result = some SymExpr.outC
     else if z = SymExpr.gSub then result = some SymExpr.outD
     else result = none)
  else if s = .lit 0 then result = some (.div z (.sub (.lit 1) z))
  else if s = .lit (-1) then result = some (.div z (.powInt (.sub (.lit 1) z) 2))
  else result = none
-- post-conditions-end

-- impl-start
/-- Dispatch on the argument `z`, then (for the recognized orders) on `z` again or
on `s`, returning the matching closed form or `none`. -/
def implementation_polylogEval (s z : SymExpr) : Option SymExpr := Id.run do
  if z = .lit 1 then return some (.zeta s)
  if z = .lit (-1) then return some (.neg (.eta s))
  if z = .lit 0 then return some (.lit 0)
  if s = .lit 2 then
    if z = SymExpr.half then return some SymExpr.outHalf
    if z = .lit 2 then return some SymExpr.outTwo
    if z = SymExpr.zA then return some SymExpr.outA
    if z = SymExpr.zB then return some SymExpr.outB
    if z = SymExpr.zC then return some SymExpr.outC
    if z = SymExpr.gSub then return some SymExpr.outD
    return none
  if s = .lit 0 then return some (.div z (.sub (.lit 1) z))
  if s = .lit (-1) then return some (.div z (.powInt (.sub (.lit 1) z) 2))
  return none
-- impl-end

-- proof-start
set_option maxHeartbeats 4000000 in
theorem impl_eq (s z : SymExpr) :
    implementation_polylogEval s z =
    (if z = .lit 1 then some (.zeta s)
     else if z = .lit (-1) then some (.neg (.eta s))
     else if z = .lit 0 then some (.lit 0)
     else if s = .lit 2 then
       (if z = SymExpr.half then some SymExpr.outHalf
        else if z = .lit 2 then some SymExpr.outTwo
        else if z = SymExpr.zA then some SymExpr.outA
        else if z = SymExpr.zB then some SymExpr.outB
        else if z = SymExpr.zC then some SymExpr.outC
        else if z = SymExpr.gSub then some SymExpr.outD
        else none)
     else if s = .lit 0 then some (.div z (.sub (.lit 1) z))
     else if s = .lit (-1) then some (.div z (.powInt (.sub (.lit 1) z) 2))
     else none) := by
  unfold implementation_polylogEval
  rfl

set_option maxHeartbeats 4000000 in
theorem correct_polylogEval :
    ∀ (s z : SymExpr),
    problem_spec_polylogEval s z (implementation_polylogEval s z) := by
  intro s z
  rw [impl_eq]
  unfold problem_spec_polylogEval
  split_ifs <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_polylogEval is a FULLY-PINNED TOTAL function (every if-branch fixes `result` uniquely) and correct_polylogEval is a `∀ s z` statement. By Lean soundness a proof closes only if the impl is extensionally equal to the spec on all SymExpr. A-LEGS: axioms=[] (no consumed axiom; axiom_check.py is a skip stub; both verifying proofs depend only on [propext]). Exactly ONE A-reference leg: the whole SymExpr dispatch ladder + closed-form outputs as a deep model of post-patch polylog.eval, validated_by G-CONF (conformance_check.py). G-CONF recorded pass: 120171 checks, 0 disagreements, seed=13852 — model↔real-callee correspondence holds end-to-end. refinement.md legs #1-#11 are all R or I; it explicitly states 'No changed-inexpressible op.' — NO kind-3 leg. 

### ATTACKS (all same_spec=True, impl-region-only edits; verified concurrently ≤4 at a time via `bash scripts/lean_verify.sh <f>`):
- positive_control (gold): exit 0; #print axioms correct_polylogEval => [propext].
- atk_1 prepatch bug (only z∈{1,-1,0}, else none): exit 1 (fails). Prepatch reproduced.
- atk_2 partial-domain (drop s=0 rational branch): exit 1.
- atk_3 boundary/wrong-output (outTwo returned at z=½ instead of outHalf): exit 1.
- atk_4 control-flow-effect (test s=0 BEFORE z=0, corrupting z=0,s=0): exit 1.
- atk_5 ungrounded-oracle echo (s=-1 uses powInt ...1 instead of 2): exit 1.
- atk_6 over-eager (extra s=2,z=gAdd row returns outD where spec requires none): exit 1.
- atk_8 output-oracle swap (zeta↔eta at z=1 vs z=-1): exit 1.
- atk_7 EXTENSIONALLY-EQUAL ECHO (gold table rewritten as pure nested if/else, no Id.run): exit 0; #print axioms => [propext] (clean). 

MANDATORY RESOLVE (protocol step 2): atk_7 is the only verifying same-spec candidate. Its faithful refined patch = the bundle gold patch (behaviorally identical dispatch table; patch_equals_gold=True; verified byte-identical to gold_13852.patch). RAN under official harness: run_resolve('sympy__sympy-13852', atk_7_faithful.patch) => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. 

CONCLUSION: all 7 genuinely-wrong impls FAIL to verify (spec catches partial-domain, boundary, control-flow, over-eager, oracle-swap, and prepatch defects); the single verifying candidate's materialized faithful patch RESOLVES. No verifying candidate has a non-resolving faithful patch ⇒ verify⇒correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (G-PANEL-2) audit of polylog.eval(cls,s,z) for sympy__sympy-13852 (post-patch, base c935e1d1). Method: built a fresh git worktree at base_commit, applied bundle patch.diff (confirmed byte-identical to gold and to the inspected post-patch eval body), and ran a differential test of the Lean problem_spec_polylogEval ladder (transliterated to SymPy per the type bijection in mapping.md) against the REAL post-patch polylog.eval under py3.8+mpmath. Results: 0 divergences over the full boundary cross-product + ~120k fuzzed pairs, plus a second 60k-pair fuzz and a targeted near-miss golden-ratio probe. Coverage of subtle surfaces: (a) auto-evaluating opaque-builder outputs zeta(s)/-dirichlet_eta(s) match semantically incl. the zoo case at s=1,z=1 (handled soundly by structural-first agree()); (b) Float canonicalization -- Float(0.5)==S.Half, Float(2.0)==2, Float(0.0)==0, Float(1.0)==1 all True in SymPy, so real eval fires the same z/s branches the structural Lean match expects (0 divergences on float inputs); (c) near-miss golden forms ((sqrt5+1)/2, (sqrt5-3)/2, sqrt5/2, 1-sqrt5, etc.) all -> None on both sides (cascade does not over-fire); (d) priority ordering z-keyed > s=2 block > s=0 > s=-1 with s=2 block falling through to None mirrors the Python elif ladder; (e) numeric check: every order-2 table closed form equals the true polylog(2,z).N() value. Supporting checks: markers CLI exit 0 (spec byte-identical pre/post); lean_verify.sh exit 0; #print axioms correct_polylogEval -> [propext] only, no sorryAx (genuine proof). No diverging input constructible. Spec is neither too strong nor drifting from the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `mapping.md`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True, lean backend). Mechanical leakage.screen over the spec view: passed, zero hard failures. Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md), so no deferral needed. Manual review of the spec view (docstring + axioms SymExpr carrier + pure helpers outTwo/outA-D/half/gSub/... + problem_spec_polylogEval post-condition): no diff markers, no patched-file path (zeta_functions.py absent), no gold-diff line quoted, no bug/fix narration, no problem_statement phrasing echoed in comments. Names are abstract/behavior-descriptive (polylogEval, SymExpr, opaque zeta/eta/pi/imagUnit/sqrt5 builders). The token 'polylog' is already public in problem_statement. The spec DOES encode the full post-patch behavior table (six-entry s=2 argument table incl. the golden-ratio √5 arguments, the s=0->z/(1-z) and s=-1->z/(1-z)**2 rational forms, z==0->0) — most of which is NOT in the public problem_statement (which only reveals polylog(2,1/2)==-log(2)**2/2+pi**2/12 and the exp_polar/expand_func issue). However, this is a spec->impl->proof bundle: the consumer is given the spec view and must supply implementation+proof. Pinning correct input->output behavior is the necessary specification content and the task input, not disclosure of the *edit*. Leakage would be edit-specific artifacts (paths/diffs/fix narrative), none present. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
