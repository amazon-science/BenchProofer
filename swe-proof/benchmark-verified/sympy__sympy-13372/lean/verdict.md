# P2 adversarial audit — sympy__sympy-13372

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -114,8 +114,6 @@
   else if rePart.kind = .number then
     reOut := .num rePart.floatVal
     reprec := some prec
-  else
-    return .error ()
   let mut imOut : EvalfPartOut := .sym
   let mut imprec : Option Nat := none
   if imPart.kind = .zero then
@@ -124,8 +122,6 @@
   else if imPart.kind = .number then
     imOut := .num imPart.floatVal
     imprec := some prec
-  else
-    return .error ()
   return .ok (reOut, imOut, reprec, imprec)
 -- impl-end
 
@@ -135,13 +131,9 @@
       problem_spec_reduceComponentsToFloat rePart imPart prec
         (implementation_reduceComponentsToFloat rePart imPart prec) := by
   intro rePart imPart prec
-  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
-    reduceComponentsToFloat
-  simp only [Id.run, bind, pure]
-  by_cases huneval : rePart.hasUneval || imPart.hasUneval
-  · simp only [huneval, if_true]
-  · simp only [huneval]
-    rcases hre : rePart.kind with _ | _ | _ <;>
-      rcases him : imPart.kind with _ | _ | _ <;>
-      simp [evalfPartOut, evalfPartPrec, hre, him]
+  rcases rePart with ⟨rk, rm, ru⟩
+  rcases imPart with ⟨ik, im, iu⟩
+  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat reduceComponentsToFloat
+  cases rk <;> cases ik <;> cases ru <;> cases iu <;>
+    simp [evalfPartOut, evalfPartPrec, Id.run] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -124,8 +124,6 @@
   else if imPart.kind = .number then
     imOut := .num imPart.floatVal
     imprec := some prec
-  else
-    return .error ()
   return .ok (reOut, imOut, reprec, imprec)
 -- impl-end
 
@@ -135,13 +133,9 @@
       problem_spec_reduceComponentsToFloat rePart imPart prec
         (implementation_reduceComponentsToFloat rePart imPart prec) := by
   intro rePart imPart prec
-  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
-    reduceComponentsToFloat
-  simp only [Id.run, bind, pure]
-  by_cases huneval : rePart.hasUneval || imPart.hasUneval
-  · simp only [huneval, if_true]
-  · simp only [huneval]
-    rcases hre : rePart.kind with _ | _ | _ <;>
-      rcases him : imPart.kind with _ | _ | _ <;>
-      simp [evalfPartOut, evalfPartPrec, hre, him]
+  rcases rePart with ⟨rk, rm, ru⟩
+  rcases imPart with ⟨ik, im, iu⟩
+  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat reduceComponentsToFloat
+  cases rk <;> cases ik <;> cases ru <;> cases iu <;>
+    simp [evalfPartOut, evalfPartPrec, Id.run] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,7 +112,7 @@
     reOut := .null
     reprec := none
   else if rePart.kind = .number then
-    reOut := .num rePart.floatVal
+    reOut := .num (rePart.floatVal + 1)
     reprec := some prec
   else
     return .error ()
@@ -135,13 +135,9 @@
       problem_spec_reduceComponentsToFloat rePart imPart prec
         (implementation_reduceComponentsToFloat rePart imPart prec) := by
   intro rePart imPart prec
-  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
-    reduceComponentsToFloat
-  simp only [Id.run, bind, pure]
-  by_cases huneval : rePart.hasUneval || imPart.hasUneval
-  · simp only [huneval, if_true]
-  · simp only [huneval]
-    rcases hre : rePart.kind with _ | _ | _ <;>
-      rcases him : imPart.kind with _ | _ | _ <;>
-      simp [evalfPartOut, evalfPartPrec, hre, him]
+  rcases rePart with ⟨rk, rm, ru⟩
+  rcases imPart with ⟨ik, im, iu⟩
+  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat reduceComponentsToFloat
+  cases rk <;> cases ik <;> cases ru <;> cases iu <;>
+    simp [evalfPartOut, evalfPartPrec, Id.run] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,8 +104,6 @@
 -- impl-start
 def implementation_reduceComponentsToFloat
     (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do
-  if rePart.hasUneval || imPart.hasUneval then
-    return .error ()
   let mut reOut : EvalfPartOut := .sym
   let mut reprec : Option Nat := none
   if rePart.kind = .zero then
@@ -135,13 +133,9 @@
       problem_spec_reduceComponentsToFloat rePart imPart prec
         (implementation_reduceComponentsToFloat rePart imPart prec) := by
   intro rePart imPart prec
-  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
-    reduceComponentsToFloat
-  simp only [Id.run, bind, pure]
-  by_cases huneval : rePart.hasUneval || imPart.hasUneval
-  · simp only [huneval, if_true]
-  · simp only [huneval]
-    rcases hre : rePart.kind with _ | _ | _ <;>
-      rcases him : imPart.kind with _ | _ | _ <;>
-      simp [evalfPartOut, evalfPartPrec, hre, him]
+  rcases rePart with ⟨rk, rm, ru⟩
+  rcases imPart with ⟨ik, im, iu⟩
+  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat reduceComponentsToFloat
+  cases rk <;> cases ik <;> cases ru <;> cases iu <;>
+    simp [evalfPartOut, evalfPartPrec, Id.run] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,7 +110,7 @@
   let mut reprec : Option Nat := none
   if rePart.kind = .zero then
     reOut := .null
-    reprec := none
+    reprec := some prec
   else if rePart.kind = .number then
     reOut := .num rePart.floatVal
     reprec := some prec
@@ -135,13 +135,9 @@
       problem_spec_reduceComponentsToFloat rePart imPart prec
         (implementation_reduceComponentsToFloat rePart imPart prec) := by
   intro rePart imPart prec
-  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
-    reduceComponentsToFloat
-  simp only [Id.run, bind, pure]
-  by_cases huneval : rePart.hasUneval || imPart.hasUneval
-  · simp only [huneval, if_true]
-  · simp only [huneval]
-    rcases hre : rePart.kind with _ | _ | _ <;>
-      rcases him : imPart.kind with _ | _ | _ <;>
-      simp [evalfPartOut, evalfPartPrec, hre, him]
+  rcases rePart with ⟨rk, rm, ru⟩
+  rcases imPart with ⟨ik, im, iu⟩
+  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat reduceComponentsToFloat
+  cases rk <;> cases ik <;> cases ru <;> cases iu <;>
+    simp [evalfPartOut, evalfPartPrec, Id.run] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,30 +103,8 @@
 
 -- impl-start
 def implementation_reduceComponentsToFloat
-    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do
-  if rePart.hasUneval || imPart.hasUneval then
-    return .error ()
-  let mut reOut : EvalfPartOut := .sym
-  let mut reprec : Option Nat := none
-  if rePart.kind = .zero then
-    reOut := .null
-    reprec := none
-  else if rePart.kind = .number then
-    reOut := .num rePart.floatVal
-    reprec := some prec
-  else
-    return .error ()
-  let mut imOut : EvalfPartOut := .sym
-  let mut imprec : Option Nat := none
-  if imPart.kind = .zero then
-    imOut := .null
-    imprec := none
-  else if imPart.kind = .number then
-    imOut := .num imPart.floatVal
-    imprec := some prec
-  else
-    return .error ()
-  return .ok (reOut, imOut, reprec, imprec)
+    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple :=
+  .error ()
 -- impl-end
 
 -- proof-start
@@ -135,13 +113,9 @@
       problem_spec_reduceComponentsToFloat rePart imPart prec
         (implementation_reduceComponentsToFloat rePart imPart prec) := by
   intro rePart imPart prec
-  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
-    reduceComponentsToFloat
-  simp only [Id.run, bind, pure]
-  by_cases huneval : rePart.hasUneval || imPart.hasUneval
-  · simp only [huneval, if_true]
-  · simp only [huneval]
-    rcases hre : rePart.kind with _ | _ | _ <;>
-      rcases him : imPart.kind with _ | _ | _ <;>
-      simp [evalfPartOut, evalfPartPrec, hre, him]
+  rcases rePart with ⟨rk, rm, ru⟩
+  rcases imPart with ⟨ik, im, iu⟩
+  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat reduceComponentsToFloat
+  cases rk <;> cases ik <;> cases ru <;> cases iu <;>
+    simp [evalfPartOut, evalfPartPrec, Id.run] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing the real and imaginary components of a numeric evaluation to a tuple of
machine-float values paired with their precisions.

A numeric evaluation step takes the real part and the imaginary part of an
expression and tries to turn each into a concrete machine-float value:

* a component that is exactly zero contributes no value and carries no
  precision;
* a component that is a concrete number contributes its machine-float value at
  the working precision;
* a component that is neither exactly zero nor a concrete number cannot be
  reduced numerically — when either component is in this state, the whole
  reduction is reported as unsupported, so that a caller may fall back to a
  different strategy.

In addition, if either component still contains an unevaluated symbolic
real/imaginary marker, the reduction is likewise reported as unsupported.

The result, when supported, is the four-tuple of (real value, imaginary value,
real precision, imaginary precision): every one of these four outputs is pinned
to the classification of the corresponding input component, so a supported
result is well-formed in all four positions exactly when both components are
reducible.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The numeric
-- machine-float value a concrete component reduces to is supplied as part of the
-- classified input (the `floatVal` field) and carried through unchanged, so there is
-- no `opaque`/`axiom` callee contract to declare: the control-flow behavior is
-- modeled DEEPLY over the observable classification of each component.
-- axioms-end

-- pure-start
/-- Classification of one component (real part or imaginary part) of the
expression being evaluated. -/
inductive EvalfPartKind
  | zero      -- the component is exactly zero
  | number    -- the component is a concrete number reducible to a float
  | symbolic  -- the component is neither zero nor a concrete number
  deriving DecidableEq, Repr

/-- One classified component: its kind, the machine-float value it reduces to
when it is a concrete number, and whether it still contains an unevaluated
symbolic real/imaginary marker. -/
structure EvalfPart where
  kind : EvalfPartKind
  floatVal : Int          -- the machine-float value (meaningful only for `number`)
  hasUneval : Bool   -- carries an unevaluated symbolic real/imaginary marker
  deriving DecidableEq, Repr

/-- A reduced component value in the output tuple. -/
inductive EvalfPartOut
  | null        -- no value (the component was exactly zero)
  | num (m : Int)  -- a concrete machine-float value
  | sym         -- a still-symbolic, non-reduced value (a malformed output)
  deriving DecidableEq, Repr

/-- The supported reduction result: (real value, imaginary value, real
precision, imaginary precision). -/
abbrev EvalfTuple := EvalfPartOut × EvalfPartOut × Option Nat × Option Nat

/-- The reduced value contributed by a component (used only when the component
is reducible). -/
def evalfPartOut (p : EvalfPart) : EvalfPartOut :=
  match p.kind with
  | .zero => .null
  | .number => .num p.floatVal
  | .symbolic => .sym

/-- The precision contributed by a component: the working precision for a
concrete number, none otherwise. -/
def evalfPartPrec (p : EvalfPart) (prec : Nat) : Option Nat :=
  match p.kind with
  | .number => some prec
  | _ => none

/-- The desired reduction: unsupported (`.error ()`) when either component
carries an unevaluated marker, or when either component is symbolic; otherwise
the well-formed four-tuple. -/
def reduceComponentsToFloat (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple :=
  if rePart.hasUneval || imPart.hasUneval then
    .error ()
  else if rePart.kind = .symbolic then
    .error ()
  else if imPart.kind = .symbolic then
    .error ()
  else
    .ok (evalfPartOut rePart, evalfPartOut imPart, evalfPartPrec rePart prec, evalfPartPrec imPart prec)
-- pure-end

-- post-conditions-start
/-- The reduction produces exactly the supported/unsupported decision and the
fully-pinned four-tuple dictated by the rule above. -/
def problem_spec_reduceComponentsToFloat
    (rePart imPart : EvalfPart) (prec : Nat) (result : Except Unit EvalfTuple) : Prop :=
  result = reduceComponentsToFloat rePart imPart prec
-- post-conditions-end

-- impl-start
def implementation_reduceComponentsToFloat
    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do
  if rePart.hasUneval || imPart.hasUneval then
    return .error ()
  let mut reOut : EvalfPartOut := .sym
  let mut reprec : Option Nat := none
  if rePart.kind = .zero then
    reOut := .null
    reprec := none
  else if rePart.kind = .number then
    reOut := .num rePart.floatVal
    reprec := some prec
  else
    return .error ()
  let mut imOut : EvalfPartOut := .sym
  let mut imprec : Option Nat := none
  if imPart.kind = .zero then
    imOut := .null
    imprec := none
  else if imPart.kind = .number then
    imOut := .num imPart.floatVal
    imprec := some prec
  else
    return .error ()
  return .ok (reOut, imOut, reprec, imprec)
-- impl-end

-- proof-start
theorem correct_reduceComponentsToFloat :
    ∀ (rePart imPart : EvalfPart) (prec : Nat),
      problem_spec_reduceComponentsToFloat rePart imPart prec
        (implementation_reduceComponentsToFloat rePart imPart prec) := by
  intro rePart imPart prec
  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
    reduceComponentsToFloat
  simp only [Id.run, bind, pure]
  by_cases huneval : rePart.hasUneval || imPart.hasUneval
  · simp only [huneval, if_true]
  · simp only [huneval]
    rcases hre : rePart.kind with _ | _ | _ <;>
      rcases him : imPart.kind with _ | _ | _ <;>
      simp [evalfPartOut, evalfPartPrec, hre, him]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is `result = reduceComponentsToFloat rePart imPart prec` — EXACT pointwise equality to a total, fully-deep reference model (no opaque/axiom; the model encodes the post-patch control flow directly). Tightest possible spec: any verifying impl must be extensionally equal to the model, so any behavioral deviation yields an unprovable goal.

same_spec: verified True for all 6 attacks + echo control (impl+proof regions elide to placeholders in _lean_spec_view; axioms/pure/pre/post byte-identical). Command: swebench_unified.markers.same_spec with get_backend('lean').language.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`; 0=verifies, 1=error):
- atk_1 PREPATCH BUG (drop both `else return .error ()`): exit 1, goal reduces to `⊢ False` on symbolic component. prepatch reproduced.
- atk_2 PARTIAL-DOMAIN (drop imag `else error` only): exit 1, `⊢ False` on (number, symbolic).
- atk_3 BOUNDARY (number carries floatVal+1): exit 1, goal `.num (rm+1) = .num rm`.
- atk_4 CONTROL-FLOW-EFFECT (drop uneval guard entirely): exit 1, `⊢ False` on uneval=true.
- atk_5 PREC-SWAP (zero leg emits some prec instead of none): exit 1, goal `some prec = none` mismatch.
- atk_6 UNGROUNDED-ORACLE / ALWAYS-ERROR (return .error () unconditionally): exit 1, `⊢ False`.
All six produce genuinely false goals (`⊢ False` / constructor-injectivity mismatch), i.e. provably unprovable, not tactic-fragility.

CONTROLS (exit 0): atk_7 (echo `reduceComponentsToFloat rePart imPart prec` = the model) verifies; pos_control (gold Solution.lean) verifies. `#print axioms correct_reduceComponentsToFloat` on both = `[propext]` only — clean (no sorryAx, no custom axioms).

PROTOCOL STEP 2: NO wrong impl closed a clean-axiom proof, so there is no verifying-wrong-impl requiring a materialized faithful patch + resolve run. patches={} accordingly. verify⇏correct is NOT exhibited; the spec's exact-equality shape closes the gap by construction.

REFINEMENT AUDIT: 8 legs, all R or I, ZERO A-legs — sound. The gold patch adds only two `else: raise NotImplementedError` clauses (pure control-flow guard, no new callee). The only callee on changed context (`._to_mpmath(prec, allow_ints=False)._mpf_`) sits on UNCHANGED lines and its result is threaded through as the opaque `floatVal` payload the fix never inspects/re-derives => no A-consumed (no unchanged-callee contract the proof consumes) and no A-reference (no deeply-modeled changed callee). No kind-3/ungrounded legs (there are no axioms at all; axioms region intentionally empty, G-AX skips). mapping.md binds evalf.py fallback branch lines 1289-1312 @ base_commit 30379ea6e2, consistent with patch.diff (else:raise at 1300+/1306+). Model faithfully mirrors post-patch branch: uneval-OR->error; re/im symbolic->error; else->pinned four-tuple (evalfPartOut/evalfPartPrec).

VERDICT: SOUND — 6 distinct same-spec wrong impls all fail to verify (false goals), correct echo + positive control verify with clean [propext] axioms, prepatch bug reproduced, no verifying wrong-impl exists to break the spec, and refinement.md A-leg/correspondence audit passes.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reducing the real and imaginary components of a numeric evaluation to a tuple of
machine-float values paired with their precisions.

A numeric evaluation step takes the real part and the imaginary part of an
expression and tries to turn each into a concrete machine-float value:

* a component that is exactly zero contributes no value and carries no
  precision;
* a component that is a concrete number contributes its machine-float value at
  the working precision;
* a component that is neither exactly zero nor a concrete number cannot be
  reduced numerically — when either component is in this state, the whole
  reduction is reported as unsupported, so that a caller may fall back to a
  different strategy.

In addition, if either component still contains an unevaluated symbolic
real/imaginary marker, the reduction is likewise reported as unsupported.

The result, when supported, is the four-tuple of (real value, imaginary value,
real precision, imaginary precision): every one of these four outputs is pinned
to the classification of the corresponding input component, so a supported
result is well-formed in all four positions exactly when both components are
reducible.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The numeric
-- machine-float value a concrete component reduces to is supplied as part of the
-- classified input (the `floatVal` field) and carried through unchanged, so there is
-- no `opaque`/`axiom` callee contract to declare: the control-flow behavior is
-- modeled DEEPLY over the observable classification of each component.
-- axioms-end

-- pure-start
/-- Classification of one component (real part or imaginary part) of the
expression being evaluated. -/
inductive EvalfPartKind
  | zero      -- the component is exactly zero
  | number    -- the component is a concrete number reducible to a float
  | symbolic  -- the component is neither zero nor a concrete number
  deriving DecidableEq, Repr

/-- One classified component: its kind, the machine-float value it reduces to
when it is a concrete number, and whether it still contains an unevaluated
symbolic real/imaginary marker. -/
structure EvalfPart where
  kind : EvalfPartKind
  floatVal : Int          -- the machine-float value (meaningful only for `number`)
  hasUneval : Bool   -- carries an unevaluated symbolic real/imaginary marker
  deriving DecidableEq, Repr

/-- A reduced component value in the output tuple. -/
inductive EvalfPartOut
  | null        -- no value (the component was exactly zero)
  | num (m : Int)  -- a concrete machine-float value
  | sym         -- a still-symbolic, non-reduced value (a malformed output)
  deriving DecidableEq, Repr

/-- The supported reduction result: (real value, imaginary value, real
precision, imaginary precision). -/
abbrev EvalfTuple := EvalfPartOut × EvalfPartOut × Option Nat × Option Nat

/-- The reduced value contributed by a component (used only when the component
is reducible). -/
def evalfPartOut (p : EvalfPart) : EvalfPartOut :=
  match p.kind with
  | .zero => .null
  | .number => .num p.floatVal
  | .symbolic => .sym

/-- The precision contributed by a component: the working precision for a
concrete number, none otherwise. -/
def evalfPartPrec (p : EvalfPart) (prec : Nat) : Option Nat :=
  match p.kind with
  | .number => some prec
  | _ => none

/-- The desired reduction: unsupported (`.error ()`) when either component
carries an unevaluated marker, or when either component is symbolic; otherwise
the well-formed four-tuple. -/
def reduceComponentsToFloat (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple :=
  if rePart.hasUneval || imPart.hasUneval then
    .error ()
  else if rePart.kind = .symbolic then
    .error ()
  else if imPart.kind = .symbolic then
    .error ()
  else
    .ok (evalfPartOut rePart, evalfPartOut imPart, evalfPartPrec rePart prec, evalfPartPrec imPart prec)
-- pure-end

-- post-conditions-start
/-- The reduction produces exactly the supported/unsupported decision and the
fully-pinned four-tuple dictated by the rule above. -/
def problem_spec_reduceComponentsToFloat
    (rePart imPart : EvalfPart) (prec : Nat) (result : Except Unit EvalfTuple) : Prop :=
  result = reduceComponentsToFloat rePart imPart prec
-- post-conditions-end

-- impl-start
def implementation_reduceComponentsToFloat
    (rePart imPart : EvalfPart) (prec : Nat) : Except Unit EvalfTuple := Id.run do
  if rePart.hasUneval || imPart.hasUneval then
    return .error ()
  let mut reOut : EvalfPartOut := .sym
  let mut reprec : Option Nat := none
  if rePart.kind = .zero then
    reOut := .null
    reprec := none
  else if rePart.kind = .number then
    reOut := .num rePart.floatVal
    reprec := some prec
  else
    return .error ()
  let mut imOut : EvalfPartOut := .sym
  let mut imprec : Option Nat := none
  if imPart.kind = .zero then
    imOut := .null
    imprec := none
  else if imPart.kind = .number then
    imOut := .num imPart.floatVal
    imprec := some prec
  else
    return .error ()
  return .ok (reOut, imOut, reprec, imprec)
-- impl-end

-- proof-start
theorem correct_reduceComponentsToFloat :
    ∀ (rePart imPart : EvalfPart) (prec : Nat),
      problem_spec_reduceComponentsToFloat rePart imPart prec
        (implementation_reduceComponentsToFloat rePart imPart prec) := by
  intro rePart imPart prec
  unfold problem_spec_reduceComponentsToFloat implementation_reduceComponentsToFloat
    reduceComponentsToFloat
  simp only [Id.run, bind, pure]
  by_cases huneval : rePart.hasUneval || imPart.hasUneval
  · simp only [huneval, if_true]
  · simp only [huneval]
    rcases hre : rePart.kind with _ | _ | _ <;>
      rcases him : imPart.kind with _ | _ | _ <;>
      simp [evalfPartOut, evalfPartPrec, hre, him]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is `result = reduceComponentsToFloat rePart imPart prec` — EXACT pointwise equality to a total, fully-deep reference model (no opaque/axiom; the model encodes the post-patch control flow directly). Tightest possible spec: any verifying impl must be extensionally equal to the model, so any behavioral deviation yields an unprovable goal.

same_spec: verified True for all 6 attacks + echo control (impl+proof regions elide to placeholders in _lean_spec_view; axioms/pure/pre/post byte-identical). Command: swebench_unified.markers.same_spec with get_backend('lean').language.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`; 0=verifies, 1=error):
- atk_1 PREPATCH BUG (drop both `else return .error ()`): exit 1, goal reduces to `⊢ False` on symbolic component. prepatch reproduced.
- atk_2 PARTIAL-DOMAIN (drop imag `else error` only): exit 1, `⊢ False` on (number, symbolic).
- atk_3 BOUNDARY (number carries floatVal+1): exit 1, goal `.num (rm+1) = .num rm`.
- atk_4 CONTROL-FLOW-EFFECT (drop uneval guard entirely): exit 1, `⊢ False` on uneval=true.
- atk_5 PREC-SWAP (zero leg emits some prec instead of none): exit 1, goal `some prec = none` mismatch.
- atk_6 UNGROUNDED-ORACLE / ALWAYS-ERROR (return .error () unconditionally): exit 1, `⊢ False`.
All six produce genuinely false goals (`⊢ False` / constructor-injectivity mismatch), i.e. provably unprovable, not tactic-fragility.

CONTROLS (exit 0): atk_7 (echo `reduceComponentsToFloat rePart imPart prec` = the model) verifies; pos_control (gold Solution.lean) verifies. `#print axioms correct_reduceComponentsToFloat` on both = `[propext]` only — clean (no sorryAx, no custom axioms).

PROTOCOL STEP 2: NO wrong impl closed a clean-axiom proof, so there is no verifying-wrong-impl requiring a materialized faithful patch + resolve run. patches={} accordingly. verify⇏correct is NOT exhibited; the spec's exact-equality shape closes the gap by construction.

REFINEMENT AUDIT: 8 legs, all R or I, ZERO A-legs — sound. The gold patch adds only two `else: raise NotImplementedError` clauses (pure control-flow guard, no new callee). The only callee on changed context (`._to_mpmath(prec, allow_ints=False)._mpf_`) sits on UNCHANGED lines and its result is threaded through as the opaque `floatVal` payload the fix never inspects/re-derives => no A-consumed (no unchanged-callee contract the proof consumes) and no A-reference (no deeply-modeled changed callee). No kind-3/ungrounded legs (there are no axioms at all; axioms region intentionally empty, G-AX skips). mapping.md binds evalf.py fallback branch lines 1289-1312 @ base_commit 30379ea6e2, consistent with patch.diff (else:raise at 1300+/1306+). Model faithfully mirrors post-patch branch: uneval-OR->error; re/im symbolic->error; else->pinned four-tuple (evalfPartOut/evalfPartPrec).

VERDICT: SOUND — 6 distinct same-spec wrong impls all fail to verify (false goals), correct echo + positive control verify with clean [propext] axioms, prepatch bug reproduced, no verifying wrong-impl exists to break the spec, and refinement.md A-leg/correspondence audit passes.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-13372 (lean). Modeled routine: the fallback (except KeyError) branch of evalf(x,prec,options) in sympy/core/evalf.py @ base 30379ea6e2, reducing re/im components of xe.as_real_imag() to r=re,im,reprec,imprec. Gold patch (confirmed from dataset test.jsonl) adds `else: raise NotImplementedError` after the `elif re.is_number` chain (~1301) and after the `elif im.is_number` chain (~1307).

### Validation done
- Spec region byte-identical: same_spec(Solution, Solution_prepatch, lean-backend) = True (impl/proof differ as required; spec view diff = identical).
- lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- #print axioms correct_reduceComponentsToFloat -> [propext] only; NO sorryAx -> proof is real, not faked.
- conformance_check.py -> pass, 0 disagreements over full boundary sweep (kind x kind x uneval x uneval x prec) + 150k fuzzed inputs, seed 13372.

### FAITHFULNESS REASONING (model vs real post-patch callee, checked for over-constraint / drift):
1. Abstract kind domain {zero, number, symbolic} is COMPLETE and mutually exclusive, mirroring the Python `if re==0 / elif re.is_number / else` cascade exactly (is_number examined only when !=0). No component classification is left unmodeled.
2. error condition modeled as (hasUneval_re OR hasUneval_im OR re.symbolic OR im.symbolic) == raise NotImplementedError. This matches: `if re.has(re_) or im.has(im_): raise` (short-circuit OR over both parts) plus the two added `else: raise` clauses. Not stronger than reality.
3. Raise ordering is UNOBSERVABLE: the real code may raise on the re-part before evaluating im, but NotImplementedError carries no inspected payload, so collapsing all symbolic/uneval cases to a single `.error ()` (Except Unit) neither over- nor under-constrains behavior. Faithful.
4. ._to_mpmath(prec, allow_ints=False)._mpf_ result is a pure passthrough the fix never inspects or re-derives; modeling it as an opaque carried Int (floatVal) threaded through unchanged does not constrain the real callee. reprec/imprec pinning (some prec for number, none for zero) matches `reprec=prec` / `reprec=None`.
5. supported result assembles the four-tuple in exactly the pinned positions dictated by each component's classification — matches `r = re, im, reprec, imprec` on the non-raising path.

No input was found on which the modeled function disagrees with the real post-patch branch's observable behavior (return-vs-raise decision + tuple contents up to the opaque mpf token). The spec is not too strong and does not drift. Note: patch.diff file in the bundle is empty, but gold patch was recovered from the dataset and the base source @30379ea6e2 was inspected directly to confirm the pre/post-patch structure; this did not affect the faithfulness conclusion.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified rigorously. (1) Spec-region integrity: swebench_unified.markers.same_spec self-check = True, and the regenerated spec_view sha256 (ecb49bc4...da63) matches meta.json region_hashes.spec_view exactly — the spec view is the frozen one. (2) Mechanical leakage screen (swebench_unified.leakage.screen over Solution.lean, gold patch, problem_statement) returns passed=True, no hard failures. (3) Substantive judgment: The spec view is fully abstract — it models the routine as EvalfPart/EvalfPartKind classification (zero/number/symbolic trichotomy) reducing to an Except Unit EvalfTuple. It NEVER names any gold-patch specific: no 'evalf.py', 'reprec'/'imprec', '_to_mpmath', 'NotImplementedError', 'Max'/'Mul', file paths, or line numbers. The impl and proof regions are elided to placeholders in the spec view. (4) Beyond-problem_statement test: the PUBLIC problem_statement already discloses the fix verbatim in the reporter's words ('the elif clauses that define reprec and imprec should have an `else: raise NotImplementedError`. That appears to fix it') plus the full traceback pinning the UnboundLocalError at 'r = re, im, reprec, imprec'. The spec view's semantic content — a symbolic/uneval component yields the unsupported result (.error ()) — is exactly the post-fix behavior any faithful spec must encode, and it reveals nothing an auditor couldn't already read from the public problem_statement. The genuinely leaky material (hint that the else-branch should raise, the culprit file/line) lives in problem_statement (and hints_text, which is excluded from this screen), not in the spec view. No spec-view line leaks the gold edit beyond problem_statement. Note: leaking documents such as refinement.md and mapping.md name Python identifiers and the fix, but they are NOT part of the spec view an auditor sees; G-PANEL-3 screens the spec view, which is clean.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
