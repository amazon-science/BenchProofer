# P2 adversarial audit — pydata__xarray-4687

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None survived. The postcondition problem_spec_condSelect fully pins BOTH output fields as exact functions of inputs: result.values = selVals cond x.values y.values AND result.attrs = (if keptAttrs keepAttrs then x.attrs else []). Every same-spec wrong impl makes the universally-quantified correct_condSelect literally false (a concrete counterexample input exists, e.g. atk_5 fails at keepAttrs=some true, x.attrs=[(a,b)], y.attrs=[] where spec demands x.attrs but impl gives y.attrs=[]), hence is unprovable in sound Lean. No wrong impl closed, so no faithful patch was eligible for run_resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,7 @@
 -- impl-start
 def implementation_condSelect (cond : List Bool) (x y : DataArr)
     (keepAttrs : Option Bool) : DataArr := Id.run do
-  let mut ka : Option Bool := keepAttrs
-  if ka == none then
-    ka := some getKeepAttrsDefault
-  let kept : Bool := match ka with
-    | some true => true
-    | _         => false
-  let attrs := if kept then x.attrs else []
-  return { values := selVals cond x.values y.values, attrs := attrs }
+  return { values := selVals cond x.values y.values, attrs := [] }
 -- impl-end
 
 -- proof-start
@@ -79,10 +72,10 @@
         (implementation_condSelect cond x y keepAttrs) := by
   intro cond x y keepAttrs
   unfold problem_spec_condSelect implementation_condSelect keptAttrs
-  cases keepAttrs with
-  | none =>
-    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
-    cases h : getKeepAttrsDefault <;> simp
-  | some b =>
-    cases b <;> simp [Id.run, bind, pure]
+  refine ⟨?_, ?_⟩ <;>
+    (first
+      | rfl
+      | (cases keepAttrs with
+         | none => simp_all [Id.run, bind, pure]; try (cases h : getKeepAttrsDefault <;> simp_all)
+         | some b => cases b <;> simp_all [Id.run, bind, pure]))
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,12 +62,9 @@
 -- impl-start
 def implementation_condSelect (cond : List Bool) (x y : DataArr)
     (keepAttrs : Option Bool) : DataArr := Id.run do
-  let mut ka : Option Bool := keepAttrs
-  if ka == none then
-    ka := some getKeepAttrsDefault
-  let kept : Bool := match ka with
-    | some true => true
-    | _         => false
+  let kept : Bool := match keepAttrs with
+    | some false => false
+    | _          => true
   let attrs := if kept then x.attrs else []
   return { values := selVals cond x.values y.values, attrs := attrs }
 -- impl-end
@@ -79,10 +76,10 @@
         (implementation_condSelect cond x y keepAttrs) := by
   intro cond x y keepAttrs
   unfold problem_spec_condSelect implementation_condSelect keptAttrs
-  cases keepAttrs with
-  | none =>
-    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
-    cases h : getKeepAttrsDefault <;> simp
-  | some b =>
-    cases b <;> simp [Id.run, bind, pure]
+  refine ⟨?_, ?_⟩ <;>
+    (first
+      | rfl
+      | (cases keepAttrs with
+         | none => simp_all [Id.run, bind, pure]; try (cases h : getKeepAttrsDefault <;> simp_all)
+         | some b => cases b <;> simp_all [Id.run, bind, pure]))
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,11 @@
 -- impl-start
 def implementation_condSelect (cond : List Bool) (x y : DataArr)
     (keepAttrs : Option Bool) : DataArr := Id.run do
-  let mut ka : Option Bool := keepAttrs
-  if ka == none then
-    ka := some getKeepAttrsDefault
-  let kept : Bool := match ka with
+  let kept : Bool := match keepAttrs with
     | some true => true
     | _         => false
   let attrs := if kept then x.attrs else []
-  return { values := selVals cond x.values y.values, attrs := attrs }
+  return { values := selVals cond y.values x.values, attrs := attrs }
 -- impl-end
 
 -- proof-start
@@ -79,10 +76,10 @@
         (implementation_condSelect cond x y keepAttrs) := by
   intro cond x y keepAttrs
   unfold problem_spec_condSelect implementation_condSelect keptAttrs
-  cases keepAttrs with
-  | none =>
-    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
-    cases h : getKeepAttrsDefault <;> simp
-  | some b =>
-    cases b <;> simp [Id.run, bind, pure]
+  refine ⟨?_, ?_⟩ <;>
+    (first
+      | rfl
+      | (cases keepAttrs with
+         | none => simp_all [Id.run, bind, pure]; try (cases h : getKeepAttrsDefault <;> simp_all)
+         | some b => cases b <;> simp_all [Id.run, bind, pure]))
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,11 @@
 -- impl-start
 def implementation_condSelect (cond : List Bool) (x y : DataArr)
     (keepAttrs : Option Bool) : DataArr := Id.run do
-  let mut ka : Option Bool := keepAttrs
-  if ka == none then
-    ka := some getKeepAttrsDefault
-  let kept : Bool := match ka with
+  let kept : Bool := match keepAttrs with
     | some true => true
     | _         => false
   let attrs := if kept then x.attrs else []
-  return { values := selVals cond x.values y.values, attrs := attrs }
+  return { values := selVals cond.tail x.values y.values, attrs := attrs }
 -- impl-end
 
 -- proof-start
@@ -79,10 +76,10 @@
         (implementation_condSelect cond x y keepAttrs) := by
   intro cond x y keepAttrs
   unfold problem_spec_condSelect implementation_condSelect keptAttrs
-  cases keepAttrs with
-  | none =>
-    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
-    cases h : getKeepAttrsDefault <;> simp
-  | some b =>
-    cases b <;> simp [Id.run, bind, pure]
+  refine ⟨?_, ?_⟩ <;>
+    (first
+      | rfl
+      | (cases keepAttrs with
+         | none => simp_all [Id.run, bind, pure]; try (cases h : getKeepAttrsDefault <;> simp_all)
+         | some b => cases b <;> simp_all [Id.run, bind, pure]))
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,13 +62,10 @@
 -- impl-start
 def implementation_condSelect (cond : List Bool) (x y : DataArr)
     (keepAttrs : Option Bool) : DataArr := Id.run do
-  let mut ka : Option Bool := keepAttrs
-  if ka == none then
-    ka := some getKeepAttrsDefault
-  let kept : Bool := match ka with
+  let kept : Bool := match keepAttrs with
     | some true => true
     | _         => false
-  let attrs := if kept then x.attrs else []
+  let attrs := if kept then y.attrs else []
   return { values := selVals cond x.values y.values, attrs := attrs }
 -- impl-end
 
@@ -79,10 +76,10 @@
         (implementation_condSelect cond x y keepAttrs) := by
   intro cond x y keepAttrs
   unfold problem_spec_condSelect implementation_condSelect keptAttrs
-  cases keepAttrs with
-  | none =>
-    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
-    cases h : getKeepAttrsDefault <;> simp
-  | some b =>
-    cases b <;> simp [Id.run, bind, pure]
+  refine ⟨?_, ?_⟩ <;>
+    (first
+      | rfl
+      | (cases keepAttrs with
+         | none => simp_all [Id.run, bind, pure]; try (cases h : getKeepAttrsDefault <;> simp_all)
+         | some b => cases b <;> simp_all [Id.run, bind, pure]))
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,7 @@
 -- impl-start
 def implementation_condSelect (cond : List Bool) (x y : DataArr)
     (keepAttrs : Option Bool) : DataArr := Id.run do
-  let mut ka : Option Bool := keepAttrs
-  if ka == none then
-    ka := some getKeepAttrsDefault
-  let kept : Bool := match ka with
-    | some true => true
-    | _         => false
-  let attrs := if kept then x.attrs else []
-  return { values := selVals cond x.values y.values, attrs := attrs }
+  return { values := selVals cond x.values y.values, attrs := x.attrs }
 -- impl-end
 
 -- proof-start
@@ -79,10 +72,10 @@
         (implementation_condSelect cond x y keepAttrs) := by
   intro cond x y keepAttrs
   unfold problem_spec_condSelect implementation_condSelect keptAttrs
-  cases keepAttrs with
-  | none =>
-    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
-    cases h : getKeepAttrsDefault <;> simp
-  | some b =>
-    cases b <;> simp [Id.run, bind, pure]
+  refine ⟨?_, ?_⟩ <;>
+    (first
+      | rfl
+      | (cases keepAttrs with
+         | none => simp_all [Id.run, bind, pure]; try (cases h : getKeepAttrsDefault <;> simp_all)
+         | some b => cases b <;> simp_all [Id.run, bind, pure]))
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,14 +62,11 @@
 -- impl-start
 def implementation_condSelect (cond : List Bool) (x y : DataArr)
     (keepAttrs : Option Bool) : DataArr := Id.run do
-  let mut ka : Option Bool := keepAttrs
-  if ka == none then
-    ka := some getKeepAttrsDefault
-  let kept : Bool := match ka with
+  let kept : Bool := match keepAttrs with
     | some true => true
     | _         => false
   let attrs := if kept then x.attrs else []
-  return { values := selVals cond x.values y.values, attrs := attrs }
+  return { values := selVals (cond.map not) x.values y.values, attrs := attrs }
 -- impl-end
 
 -- proof-start
@@ -79,10 +76,10 @@
         (implementation_condSelect cond x y keepAttrs) := by
   intro cond x y keepAttrs
   unfold problem_spec_condSelect implementation_condSelect keptAttrs
-  cases keepAttrs with
-  | none =>
-    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
-    cases h : getKeepAttrsDefault <;> simp
-  | some b =>
-    cases b <;> simp [Id.run, bind, pure]
+  refine ⟨?_, ?_⟩ <;>
+    (first
+      | rfl
+      | (cases keepAttrs with
+         | none => simp_all [Id.run, bind, pure]; try (cases h : getKeepAttrsDefault <;> simp_all)
+         | some b => cases b <;> simp_all [Id.run, bind, pure]))
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Elementwise conditional selection between two attributed arrays.

Each operand is an array of integer values carrying a set of metadata
attributes (modeled as an association list of name/value pairs). Given a boolean
condition array and two operands `x` and `y`, the result takes, position by
position, the value from `x` where the condition holds and from `y` otherwise.

Alongside the selected data, the operation accepts a three-valued flag
governing whether the result retains metadata attributes:

* when the flag is left unset, an ambient default policy decides;
* when it requests retention, the result carries the attributes of the operand
  chosen where the condition is true (here, `x`);
* otherwise the result carries no attributes.

The desired behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- The ambient default attribute-retention policy, consulted only when the
caller leaves the retention flag unset. Its concrete value comes from the
surrounding configuration; the behavior is specified for whatever value it
yields. -/
opaque getKeepAttrsDefault : Bool
-- axioms-end

-- pure-start
/-- An array of integer values together with its metadata attributes (an
association list of name/value pairs). -/
structure DataArr where
  values : List Int
  attrs  : List (String × String)

/-- Elementwise conditional selection: at each position keep the value from
`xs` when the condition is true, otherwise the value from `ys`. -/
def selVals (cond : List Bool) (xs ys : List Int) : List Int :=
  (cond.zip (xs.zip ys)).map (fun p => if p.1 then p.2.1 else p.2.2)

/-- Whether the result should retain attributes: the caller's flag when given,
otherwise the ambient default policy. -/
def keptAttrs (keepAttrs : Option Bool) : Bool :=
  match keepAttrs with
  | none   => getKeepAttrsDefault
  | some b => b
-- pure-end

-- post-conditions-start
/-- The result's values are the elementwise conditional selection of `x` and
`y` under `cond`; its attributes are those of `x` exactly when attribute
retention is in effect, and empty otherwise. -/
def problem_spec_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) (result : DataArr) : Prop :=
  result.values = selVals cond x.values y.values ∧
  result.attrs = (if keptAttrs keepAttrs then x.attrs else [])
-- post-conditions-end

-- impl-start
def implementation_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) : DataArr := Id.run do
  let mut ka : Option Bool := keepAttrs
  if ka == none then
    ka := some getKeepAttrsDefault
  let kept : Bool := match ka with
    | some true => true
    | _         => false
  let attrs := if kept then x.attrs else []
  return { values := selVals cond x.values y.values, attrs := attrs }
-- impl-end

-- proof-start
theorem correct_condSelect :
    ∀ (cond : List Bool) (x y : DataArr) (keepAttrs : Option Bool),
      problem_spec_condSelect cond x y keepAttrs
        (implementation_condSelect cond x y keepAttrs) := by
  intro cond x y keepAttrs
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  cases keepAttrs with
  | none =>
    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
    cases h : getKeepAttrsDefault <;> simp
  | some b =>
    cases b <;> simp [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True for all 8 files (pos_control + atk_1..7), verified via swebench_unified.markers.same_spec with lean backend. Verify command: `bash scripts/lean_verify.sh <file>`. Results: pos_control EXIT=0 (verifies); atk_1..atk_7 ALL EXIT=1 (proof does not close; NOT timeout/sorry). Attack categories covered: prepatch-bug (atk_1), partial-domain flag (atk_2), control-flow-effect value swap (atk_3), boundary/off-by-one cond.tail (atk_4), control-flow-effect wrong-attrs y.attrs (atk_5), ungrounded-oracle echo always-retain (atk_6), partial-domain value negation (atk_7). Tactic-competence sanity: tactic_sanity.lean = GOLD impl + my aggressive attack proof tactic -> EXIT=0, confirming the tactic can close a true goal, so the 7 failures are genuine unprovability not tactic weakness.

Clean-axioms: pos_axioms.lean with `#print axioms correct_condSelect` -> EXIT=0, 'correct_condSelect' depends on axioms: [propext, Classical.choice, Quot.sound] (no sorryAx, opaque getKeepAttrsDefault contributes no axiom). prepatch_reproduced=true: atk_1 encodes the prepatch bug (attrs unconditionally []) and its proof fails to close (bug is genuinely detected by the spec at keepAttrs=some true with x.attrs != []); Solution_prepatch.lean carries the gold proof with sorry, consistent. patches={} because NO wrong impl closed with clean axioms, so run_resolve had no eligible candidate to execute (protocol step 2 vacuously satisfied). refinement.md audit: 6 legs tagged R / A-reference / I / A-reference / A-reference / R; NO kind-3 (_prop) consumed axiom; A-references (getKeepAttrsDefault <-> _get_keep_attrs(default=False) unchanged callee; selVals <-> duck_array_ops.where; attr propagation in apply_ufunc) correspond to real unchanged callees, value-relation exercised by G-CONF/conformance_check.py (SEED=20240626, N=120000). G-AX is a legitimate skip stub (no consumed callee axioms). Correspondence holds. Verdict SOUND: >=5 distinct same-spec wrong impls (7 run) verified, none closed, so verify=>correct is preserved for this tight functional spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None survived. The postcondition problem_spec_condSelect fully pins BOTH output fields as exact functions of inputs: result.values = selVals cond x.values y.values AND result.attrs = (if keptAttrs keepAttrs then x.attrs else []). Every same-spec wrong impl makes the universally-quantified correct_condSelect literally false (a concrete counterexample input exists, e.g. atk_5 fails at keepAttrs=some true, x.attrs=[(a,b)], y.attrs=[] where spec demands x.attrs but impl gives y.attrs=[]), hence is unprovable in sound Lean. No wrong impl closed, so no faithful patch was eligible for run_resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Elementwise conditional selection between two attributed arrays.

Each operand is an array of integer values carrying a set of metadata
attributes (modeled as an association list of name/value pairs). Given a boolean
condition array and two operands `x` and `y`, the result takes, position by
position, the value from `x` where the condition holds and from `y` otherwise.

Alongside the selected data, the operation accepts a three-valued flag
governing whether the result retains metadata attributes:

* when the flag is left unset, an ambient default policy decides;
* when it requests retention, the result carries the attributes of the operand
  chosen where the condition is true (here, `x`);
* otherwise the result carries no attributes.

The desired behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- The ambient default attribute-retention policy, consulted only when the
caller leaves the retention flag unset. Its concrete value comes from the
surrounding configuration; the behavior is specified for whatever value it
yields. -/
opaque getKeepAttrsDefault : Bool
-- axioms-end

-- pure-start
/-- An array of integer values together with its metadata attributes (an
association list of name/value pairs). -/
structure DataArr where
  values : List Int
  attrs  : List (String × String)

/-- Elementwise conditional selection: at each position keep the value from
`xs` when the condition is true, otherwise the value from `ys`. -/
def selVals (cond : List Bool) (xs ys : List Int) : List Int :=
  (cond.zip (xs.zip ys)).map (fun p => if p.1 then p.2.1 else p.2.2)

/-- Whether the result should retain attributes: the caller's flag when given,
otherwise the ambient default policy. -/
def keptAttrs (keepAttrs : Option Bool) : Bool :=
  match keepAttrs with
  | none   => getKeepAttrsDefault
  | some b => b
-- pure-end

-- post-conditions-start
/-- The result's values are the elementwise conditional selection of `x` and
`y` under `cond`; its attributes are those of `x` exactly when attribute
retention is in effect, and empty otherwise. -/
def problem_spec_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) (result : DataArr) : Prop :=
  result.values = selVals cond x.values y.values ∧
  result.attrs = (if keptAttrs keepAttrs then x.attrs else [])
-- post-conditions-end

-- impl-start
def implementation_condSelect (cond : List Bool) (x y : DataArr)
    (keepAttrs : Option Bool) : DataArr := Id.run do
  let mut ka : Option Bool := keepAttrs
  if ka == none then
    ka := some getKeepAttrsDefault
  let kept : Bool := match ka with
    | some true => true
    | _         => false
  let attrs := if kept then x.attrs else []
  return { values := selVals cond x.values y.values, attrs := attrs }
-- impl-end

-- proof-start
theorem correct_condSelect :
    ∀ (cond : List Bool) (x y : DataArr) (keepAttrs : Option Bool),
      problem_spec_condSelect cond x y keepAttrs
        (implementation_condSelect cond x y keepAttrs) := by
  intro cond x y keepAttrs
  unfold problem_spec_condSelect implementation_condSelect keptAttrs
  cases keepAttrs with
  | none =>
    simp only [Id.run, bind, pure, beq_self_eq_true, if_true]
    cases h : getKeepAttrsDefault <;> simp
  | some b =>
    cases b <;> simp [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec=True for all 8 files (pos_control + atk_1..7), verified via swebench_unified.markers.same_spec with lean backend. Verify command: `bash scripts/lean_verify.sh <file>`. Results: pos_control EXIT=0 (verifies); atk_1..atk_7 ALL EXIT=1 (proof does not close; NOT timeout/sorry). Attack categories covered: prepatch-bug (atk_1), partial-domain flag (atk_2), control-flow-effect value swap (atk_3), boundary/off-by-one cond.tail (atk_4), control-flow-effect wrong-attrs y.attrs (atk_5), ungrounded-oracle echo always-retain (atk_6), partial-domain value negation (atk_7). Tactic-competence sanity: tactic_sanity.lean = GOLD impl + my aggressive attack proof tactic -> EXIT=0, confirming the tactic can close a true goal, so the 7 failures are genuine unprovability not tactic weakness.

Clean-axioms: pos_axioms.lean with `#print axioms correct_condSelect` -> EXIT=0, 'correct_condSelect' depends on axioms: [propext, Classical.choice, Quot.sound] (no sorryAx, opaque getKeepAttrsDefault contributes no axiom). prepatch_reproduced=true: atk_1 encodes the prepatch bug (attrs unconditionally []) and its proof fails to close (bug is genuinely detected by the spec at keepAttrs=some true with x.attrs != []); Solution_prepatch.lean carries the gold proof with sorry, consistent. patches={} because NO wrong impl closed with clean axioms, so run_resolve had no eligible candidate to execute (protocol step 2 vacuously satisfied). refinement.md audit: 6 legs tagged R / A-reference / I / A-reference / A-reference / R; NO kind-3 (_prop) consumed axiom; A-references (getKeepAttrsDefault <-> _get_keep_attrs(default=False) unchanged callee; selVals <-> duck_array_ops.where; attr propagation in apply_ufunc) correspond to real unchanged callees, value-relation exercised by G-CONF/conformance_check.py (SEED=20240626, N=120000). G-AX is a legitimate skip stub (no consumed callee axioms). Correspondence holds. Verdict SOUND: >=5 distinct same-spec wrong impls (7 run) verified, none closed, so verify=>correct is preserved for this tight functional spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec: problem_spec_condSelect requires result.values = selVals cond x.values y.values AND result.attrs = (if keptAttrs keepAttrs then x.attrs else []), where keptAttrs resolves None to the ambient getKeepAttrsDefault (= _get_keep_attrs(default=False)) and treats `some b` as b. Modeled function is xarray.core.computation.where(cond,x,y,keep_attrs=None) at base_commit d3b6aa6d.

HYGIENE: Solution.lean compiles (lean_verify exit 0); `#print axioms correct_condSelect` = [propext, Classical.choice, Quot.sound] — NO sorryAx, proof is real. same_spec(Solution, Solution_prepatch, lean)=True (spec region byte-identical; only impl+proof differ). prepatch impl always yields attrs:=[] and its gold proof fails to close (G-DIFF pass).

FAITHFULNESS analysis vs real callee:
- values branch: real `where` dispatches duck_array_ops.where(cond,x,y) via apply_ufunc = elementwise np.where; selVals is the exact zip/map transliteration. Matches.
- attrs branch: gold patch resolves keep_attrs None->_get_keep_attrs(default=False), and only `keep_attrs is True` installs the combiner `lambda attrs,context: attrs[1]` which, since ufunc operands are (cond,x,y), selects x.attrs; any non-True value drops attrs. I traced all 6 combinations of {None,True,False} x {ambient True,False}: real vs spec agree on every one (True->x.attrs regardless of ambient; None->ambient; False->[]). No divergence found.
- F2P test test_where_attrs asserts keep_attrs=True keeps x.attrs ({'attr':'x'}) — exactly the spec at keepAttrs=some true.

Empirical: recorded G-CONF ran INSIDE the correct instance image (base_commit + gold patch) with 120005 randomized+catalogue cases, 0 mismatches, default_keep=False, grounding the shadow only in inputs. 

Caveat noted: my own local re-run against produced apparent MISMATCHes (keep_attrs=True copied cond's attrs), but this is a WORKTREE VERSION-SKEW ARTIFACT, not a spec defect: that worktree is at commit 1757dff (mid-2019, #3112) which PREDATES base_commit d3b6aa6d; its apply_dataarray_vfunc treats keep_attrs as a plain boolean (`if keep_attrs and hasattr(args[0],'name')`) and has no support for the callable combiner protocol, so a callable is merely truthy and it wrongly copies args[0]=cond attrs. At the true base_commit apply_ufunc honors the callable combiner and attrs[1]->x. The G-CONF run in the correct image is authoritative and confirms agreement.

Spec scope is appropriately restricted (keepAttrs : Option Bool; str/callable values out of scope, matching F2P/issue API), so the spec is neither too strong nor drifting. No input where the modeled function disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view verified byte-identical: markers.spec_view(Solution.lean, lean tables) reproduces the recorded spec_view hash 754b16014a65e9452bdcbb2d641e198a062c46be7563374b2dd4f5409e76d255 (matches G-HYGIENE region_hashes.spec_view); same_spec holds. impl-region and proof-region are correctly collapsed to standard placeholders, so neither implementation_condSelect nor the proof of correct_condSelect is exposed.

Exposed spec regions (docstring, axioms, pure, post-conditions) are fully abstract. Grep of the spec view for gold-patch specifics (apply_ufunc, _get_keep_attrs, OPTIONS, attrs[1], lambda, duck_array_ops, computation.py) returns nothing. The observable of the gold edit — add an attribute-retention flag whose True value keeps x's attributes — is ALREADY disclosed in the PUBLIC problem_statement (ignoring hints_text): 'Attributes should be preserved or at least there should be a choice (e.g. pass kwargs to apply_ufunc so keep_attrs=True can be passed)', with expected outputs showing attributes preserved.

The only detail arguably beyond the bare problem_statement — 'when the flag is left unset, an ambient default policy decides' (the None->default design) — is stated purely abstractly (opaque getKeepAttrsDefault : Bool), names no real callee or mechanism, and is a legitimate behavioral contract rather than a reconstruction of the gold implementation. G-LEAK lexical screen passed independently (failures: []). No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
