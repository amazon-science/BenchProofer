# P2 adversarial audit — matplotlib__matplotlib-24870

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_ctrl_rebuilt.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,13 +84,7 @@
     match args with
     | a :: _ => return a
     | [] =>
-      if zIsBool then
-        if filled then
-          return LevelsArg.explicit [0, 1/2, 1]
-        else
-          return LevelsArg.explicit [1/2]
-      else
-        return LevelsArg.count 7
+      return LevelsArg.count 7
 -- impl-end
 
 -- proof-start
@@ -100,16 +94,11 @@
         (implementation_chooseLevels userLevels args zIsBool filled) := by
   intro userLevels args zIsBool filled
   unfold problem_spec_chooseLevels implementation_chooseLevels
-  cases userLevels with
-  | some lv => rfl
-  | none =>
-    cases args with
-    | cons a as => rfl
-    | nil =>
-      cases zIsBool with
-      | false => rfl
-      | true =>
-        cases filled <;>
-          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-            first | rfl | simp_all
+  first
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      simp_all [LevelsArg.count, LevelsArg.explicit] <;> decide)
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      first | rfl | (refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all) | simp_all)
+  | decide
+  | simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,9 +86,9 @@
     | [] =>
       if zIsBool then
         if filled then
+          return LevelsArg.explicit [1/2]
+        else
           return LevelsArg.explicit [0, 1/2, 1]
-        else
-          return LevelsArg.explicit [1/2]
       else
         return LevelsArg.count 7
 -- impl-end
@@ -100,16 +100,11 @@
         (implementation_chooseLevels userLevels args zIsBool filled) := by
   intro userLevels args zIsBool filled
   unfold problem_spec_chooseLevels implementation_chooseLevels
-  cases userLevels with
-  | some lv => rfl
-  | none =>
-    cases args with
-    | cons a as => rfl
-    | nil =>
-      cases zIsBool with
-      | false => rfl
-      | true =>
-        cases filled <;>
-          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-            first | rfl | simp_all
+  first
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      simp_all [LevelsArg.count, LevelsArg.explicit] <;> decide)
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      first | rfl | (refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all) | simp_all)
+  | decide
+  | simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,7 +90,7 @@
         else
           return LevelsArg.explicit [1/2]
       else
-        return LevelsArg.count 7
+        return LevelsArg.count 6
 -- impl-end
 
 -- proof-start
@@ -100,16 +100,11 @@
         (implementation_chooseLevels userLevels args zIsBool filled) := by
   intro userLevels args zIsBool filled
   unfold problem_spec_chooseLevels implementation_chooseLevels
-  cases userLevels with
-  | some lv => rfl
-  | none =>
-    cases args with
-    | cons a as => rfl
-    | nil =>
-      cases zIsBool with
-      | false => rfl
-      | true =>
-        cases filled <;>
-          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-            first | rfl | simp_all
+  first
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      simp_all [LevelsArg.count, LevelsArg.explicit] <;> decide)
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      first | rfl | (refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all) | simp_all)
+  | decide
+  | simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,16 +81,13 @@
   match userLevels with
   | some lv => return lv
   | none =>
-    match args with
-    | a :: _ => return a
-    | [] =>
-      if zIsBool then
-        if filled then
-          return LevelsArg.explicit [0, 1/2, 1]
-        else
-          return LevelsArg.explicit [1/2]
+    if zIsBool then
+      if filled then
+        return LevelsArg.explicit [0, 1/2, 1]
       else
-        return LevelsArg.count 7
+        return LevelsArg.explicit [1/2]
+    else
+      return LevelsArg.count 7
 -- impl-end
 
 -- proof-start
@@ -100,16 +97,11 @@
         (implementation_chooseLevels userLevels args zIsBool filled) := by
   intro userLevels args zIsBool filled
   unfold problem_spec_chooseLevels implementation_chooseLevels
-  cases userLevels with
-  | some lv => rfl
-  | none =>
-    cases args with
-    | cons a as => rfl
-    | nil =>
-      cases zIsBool with
-      | false => rfl
-      | true =>
-        cases filled <;>
-          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-            first | rfl | simp_all
+  first
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      simp_all [LevelsArg.count, LevelsArg.explicit] <;> decide)
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      first | rfl | (refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all) | simp_all)
+  | decide
+  | simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,19 +78,7 @@
 def implementation_chooseLevels
     (userLevels : Option LevelsArg) (args : List LevelsArg)
     (zIsBool filled : Bool) : LevelsArg := Id.run do
-  match userLevels with
-  | some lv => return lv
-  | none =>
-    match args with
-    | a :: _ => return a
-    | [] =>
-      if zIsBool then
-        if filled then
-          return LevelsArg.explicit [0, 1/2, 1]
-        else
-          return LevelsArg.explicit [1/2]
-      else
-        return LevelsArg.count 7
+  return LevelsArg.count 7
 -- impl-end
 
 -- proof-start
@@ -100,16 +88,11 @@
         (implementation_chooseLevels userLevels args zIsBool filled) := by
   intro userLevels args zIsBool filled
   unfold problem_spec_chooseLevels implementation_chooseLevels
-  cases userLevels with
-  | some lv => rfl
-  | none =>
-    cases args with
-    | cons a as => rfl
-    | nil =>
-      cases zIsBool with
-      | false => rfl
-      | true =>
-        cases filled <;>
-          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-            first | rfl | simp_all
+  first
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      simp_all [LevelsArg.count, LevelsArg.explicit] <;> decide)
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      first | rfl | (refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all) | simp_all)
+  | decide
+  | simp_all
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
     | [] =>
       if zIsBool then
         if filled then
-          return LevelsArg.explicit [0, 1/2, 1]
+          return LevelsArg.explicit [1/2, 1]
         else
           return LevelsArg.explicit [1/2]
       else
@@ -100,16 +100,11 @@
         (implementation_chooseLevels userLevels args zIsBool filled) := by
   intro userLevels args zIsBool filled
   unfold problem_spec_chooseLevels implementation_chooseLevels
-  cases userLevels with
-  | some lv => rfl
-  | none =>
-    cases args with
-    | cons a as => rfl
-    | nil =>
-      cases zIsBool with
-      | false => rfl
-      | true =>
-        cases filled <;>
-          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-            first | rfl | simp_all
+  first
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      simp_all [LevelsArg.count, LevelsArg.explicit] <;> decide)
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      first | rfl | (refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all) | simp_all)
+  | decide
+  | simp_all
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,19 +78,16 @@
 def implementation_chooseLevels
     (userLevels : Option LevelsArg) (args : List LevelsArg)
     (zIsBool filled : Bool) : LevelsArg := Id.run do
-  match userLevels with
-  | some lv => return lv
-  | none =>
-    match args with
-    | a :: _ => return a
-    | [] =>
-      if zIsBool then
-        if filled then
-          return LevelsArg.explicit [0, 1/2, 1]
-        else
-          return LevelsArg.explicit [1/2]
+  match args with
+  | a :: _ => return a
+  | [] =>
+    if zIsBool then
+      if filled then
+        return LevelsArg.explicit [0, 1/2, 1]
       else
-        return LevelsArg.count 7
+        return LevelsArg.explicit [1/2]
+    else
+      return LevelsArg.count 7
 -- impl-end
 
 -- proof-start
@@ -100,16 +97,11 @@
         (implementation_chooseLevels userLevels args zIsBool filled) := by
   intro userLevels args zIsBool filled
   unfold problem_spec_chooseLevels implementation_chooseLevels
-  cases userLevels with
-  | some lv => rfl
-  | none =>
-    cases args with
-    | cons a as => rfl
-    | nil =>
-      cases zIsBool with
-      | false => rfl
-      | true =>
-        cases filled <;>
-          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
-            first | rfl | simp_all
+  first
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      simp_all [LevelsArg.count, LevelsArg.explicit] <;> decide)
+  | (cases userLevels <;> cases args <;> cases zIsBool <;> cases filled <;>
+      first | rfl | (refine ⟨fun h => ?_, fun h => ?_⟩ <;> first | rfl | simp_all) | simp_all)
+  | decide
+  | simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl_rebuilt.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the level specification for a contour plot.

A contour routine must decide, from the caller's request and the nature of the
data being contoured, *what set of levels* to draw. The decision has three
ingredients:

* an optional explicit level specification provided by the caller (a preset count
  of automatically chosen levels, or a concrete list of level values);
* an optional positional level argument supplied alongside the data;
* the nature of the data itself — in particular whether the data is
  boolean-valued — together with whether the plot is filled (regions between
  levels are shaded) or unfilled (only the level curves are drawn).

The decision is resolved in priority order. A caller-provided explicit
specification always wins. Failing that, a positional level argument, if present,
is used directly. Failing both, the choice depends on the data: for
boolean-valued data the only meaningful boundary sits midway between the two
values, so an unfilled plot draws the single mid-level and a filled plot uses the
three values that bracket and separate the two regions; for all other data a
preset default count of automatically chosen levels is used.

The behaviour is stated abstractly here as an input→output relation; the
implementation and correctness proof are supplied separately. The value `1/2`
denotes the midpoint between the two boolean values `0` and `1`.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract here: the level-specification
-- decision is modeled value-exactly (a count, or a concrete list of exact
-- rationals). The downstream routine that expands a count into concrete
-- automatic levels is invoked only AFTER this decision and is outside the
-- modeled function (validated against the real routine by the differential
-- conformance check, not assumed as an axiom).
-- axioms-end

-- pure-start
/-- A level specification: either a count `n` of levels to be chosen
automatically downstream, or an explicit list of level values. -/
inductive LevelsArg where
  | count    (n : Nat)
  | explicit (xs : List Rat)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The chosen level specification, resolved in priority order from the caller's
request and the data characteristics.

* If the caller gave an explicit specification (`userLevels = some lv`), the
  result is exactly that specification.
* Otherwise, if a positional level argument is present, the result is its first
  element.
* Otherwise the result depends on the data: for boolean-valued data the result
  is the three bracketing values `[0, 1/2, 1]` for a filled plot and the single
  mid-value `[1/2]` for an unfilled plot; for non-boolean data the result is the
  preset default count `7`. -/
def problem_spec_chooseLevels
    (userLevels : Option LevelsArg) (args : List LevelsArg)
    (zIsBool filled : Bool) (result : LevelsArg) : Prop :=
  match userLevels with
  | some lv => result = lv
  | none =>
    match args with
    | a :: _ => result = a
    | [] =>
      if zIsBool then
        (filled = true  → result = LevelsArg.explicit [0, 1/2, 1]) ∧
        (filled = false → result = LevelsArg.explicit [1/2])
      else
        result = LevelsArg.count 7
-- post-conditions-end

-- impl-start
def implementation_chooseLevels
    (userLevels : Option LevelsArg) (args : List LevelsArg)
    (zIsBool filled : Bool) : LevelsArg := Id.run do
  match userLevels with
  | some lv => return lv
  | none =>
    match args with
    | a :: _ => return a
    | [] =>
      if zIsBool then
        if filled then
          return LevelsArg.explicit [0, 1/2, 1]
        else
          return LevelsArg.explicit [1/2]
      else
        return LevelsArg.count 7
-- impl-end

-- proof-start
theorem correct_chooseLevels :
    ∀ (userLevels : Option LevelsArg) (args : List LevelsArg) (zIsBool filled : Bool),
      problem_spec_chooseLevels userLevels args zIsBool filled
        (implementation_chooseLevels userLevels args zIsBool filled) := by
  intro userLevels args zIsBool filled
  unfold problem_spec_chooseLevels implementation_chooseLevels
  cases userLevels with
  | some lv => rfl
  | none =>
    cases args with
    | cons a as => rfl
    | nil =>
      cases zIsBool with
      | false => rfl
      | true =>
        cases filled <;>
          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
            first | rfl | simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec problem_spec_chooseLevels is functionally total and TIGHT: for every input tuple (userLevels, args, zIsBool, filled) the postcondition pins `result` to a unique value. The boolean branch's conjunction (filled=true -> result=explicit[0,1/2,1]) AND (filled=false -> result=explicit[1/2]) collapses to exactly one equation for any concrete `filled : Bool`, so no input is under-specified. A-LEG AUDIT: the axioms-start/axioms-end region contains ZERO axiom declarations (only prose); the correctness proof relies on NO axiomatized callee contract, so there is nothing to exploit. refinement.md legs are I (op1), R (ops2-5), plus one A-reference (downstream _autolev count-expansion, outside the modeled function, reconciled by G-CONF); no kind-3 (changed-yet-inexpressible) leg.

The A-reference correspondence holds (count 7 <-> real hard-wired 7 fed to _autolev; explicit [0,1/2,1]/[1/2] <-> literal [0,.5,1]/[.5]). ATTACKS: built 7 DISTINCT same-spec (all same_spec=True, verified via swebench_unified.markers.same_spec) wrong impls, each editing ONLY the impl region (axioms/pure/pre/post byte-identical): atk_1=prepatch bug (ignores zIsBool, always count 7 in the [] path); atk_2=filled/unfilled swap; atk_3=wrong default count 6; atk_4=control-flow drop of the positional-args branch; atk_5=ungrounded-oracle echo (always return count 7); atk_6=wrong explicit list [1/2,1] for filled bool; atk_7=userLevels ignored (always take data path). Each was given a maximal brute-force proof attempt (nested simp_all/decide/refine across all case splits).

COMMANDS (run, ROOT of this checkout, concurrently in 2 batches of <=4 background jobs): `bash scripts/lean_verify.sh atk_N.lean`. RESULTS: atk_1..atk_7 ALL exit=1 with genuine 'unsolved goals' errors (verified via grep of .out files, e.g. atk_1.lean:94:72 unsolved goals; atk_5:88; atk_7:97) — NOT tactic-syntax artifacts. Positive control pos_ctrl_rebuilt.lean (byte-identical gold impl+proof) exit=0. `#print axioms correct_chooseLevels` on the positive control => [propext, Classical.choice, Quot.sound] (clean, NO sorryAx). Because NO wrong impl closed with a clean-axiom proof, there is no faithful refined patch to materialize/resolve (patches={}), so verify=>correct is not falsified. The R/I legs (mechanically covered by G-CONF) and the single A-reference are consistent with the real callees. >=5 distinct attacks run, none breaks the spec => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_ctrl_rebuilt.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl_rebuilt.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the level specification for a contour plot.

A contour routine must decide, from the caller's request and the nature of the
data being contoured, *what set of levels* to draw. The decision has three
ingredients:

* an optional explicit level specification provided by the caller (a preset count
  of automatically chosen levels, or a concrete list of level values);
* an optional positional level argument supplied alongside the data;
* the nature of the data itself — in particular whether the data is
  boolean-valued — together with whether the plot is filled (regions between
  levels are shaded) or unfilled (only the level curves are drawn).

The decision is resolved in priority order. A caller-provided explicit
specification always wins. Failing that, a positional level argument, if present,
is used directly. Failing both, the choice depends on the data: for
boolean-valued data the only meaningful boundary sits midway between the two
values, so an unfilled plot draws the single mid-level and a filled plot uses the
three values that bracket and separate the two regions; for all other data a
preset default count of automatically chosen levels is used.

The behaviour is stated abstractly here as an input→output relation; the
implementation and correctness proof are supplied separately. The value `1/2`
denotes the midpoint between the two boolean values `0` and `1`.
-/

-- axioms-start
-- No unchanged dependency callee needs a contract here: the level-specification
-- decision is modeled value-exactly (a count, or a concrete list of exact
-- rationals). The downstream routine that expands a count into concrete
-- automatic levels is invoked only AFTER this decision and is outside the
-- modeled function (validated against the real routine by the differential
-- conformance check, not assumed as an axiom).
-- axioms-end

-- pure-start
/-- A level specification: either a count `n` of levels to be chosen
automatically downstream, or an explicit list of level values. -/
inductive LevelsArg where
  | count    (n : Nat)
  | explicit (xs : List Rat)
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The chosen level specification, resolved in priority order from the caller's
request and the data characteristics.

* If the caller gave an explicit specification (`userLevels = some lv`), the
  result is exactly that specification.
* Otherwise, if a positional level argument is present, the result is its first
  element.
* Otherwise the result depends on the data: for boolean-valued data the result
  is the three bracketing values `[0, 1/2, 1]` for a filled plot and the single
  mid-value `[1/2]` for an unfilled plot; for non-boolean data the result is the
  preset default count `7`. -/
def problem_spec_chooseLevels
    (userLevels : Option LevelsArg) (args : List LevelsArg)
    (zIsBool filled : Bool) (result : LevelsArg) : Prop :=
  match userLevels with
  | some lv => result = lv
  | none =>
    match args with
    | a :: _ => result = a
    | [] =>
      if zIsBool then
        (filled = true  → result = LevelsArg.explicit [0, 1/2, 1]) ∧
        (filled = false → result = LevelsArg.explicit [1/2])
      else
        result = LevelsArg.count 7
-- post-conditions-end

-- impl-start
def implementation_chooseLevels
    (userLevels : Option LevelsArg) (args : List LevelsArg)
    (zIsBool filled : Bool) : LevelsArg := Id.run do
  match userLevels with
  | some lv => return lv
  | none =>
    match args with
    | a :: _ => return a
    | [] =>
      if zIsBool then
        if filled then
          return LevelsArg.explicit [0, 1/2, 1]
        else
          return LevelsArg.explicit [1/2]
      else
        return LevelsArg.count 7
-- impl-end

-- proof-start
theorem correct_chooseLevels :
    ∀ (userLevels : Option LevelsArg) (args : List LevelsArg) (zIsBool filled : Bool),
      problem_spec_chooseLevels userLevels args zIsBool filled
        (implementation_chooseLevels userLevels args zIsBool filled) := by
  intro userLevels args zIsBool filled
  unfold problem_spec_chooseLevels implementation_chooseLevels
  cases userLevels with
  | some lv => rfl
  | none =>
    cases args with
    | cons a as => rfl
    | nil =>
      cases zIsBool with
      | false => rfl
      | true =>
        cases filled <;>
          refine ⟨fun h => ?_, fun h => ?_⟩ <;>
            first | rfl | simp_all
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec problem_spec_chooseLevels is functionally total and TIGHT: for every input tuple (userLevels, args, zIsBool, filled) the postcondition pins `result` to a unique value. The boolean branch's conjunction (filled=true -> result=explicit[0,1/2,1]) AND (filled=false -> result=explicit[1/2]) collapses to exactly one equation for any concrete `filled : Bool`, so no input is under-specified. A-LEG AUDIT: the axioms-start/axioms-end region contains ZERO axiom declarations (only prose); the correctness proof relies on NO axiomatized callee contract, so there is nothing to exploit. refinement.md legs are I (op1), R (ops2-5), plus one A-reference (downstream _autolev count-expansion, outside the modeled function, reconciled by G-CONF); no kind-3 (changed-yet-inexpressible) leg.

The A-reference correspondence holds (count 7 <-> real hard-wired 7 fed to _autolev; explicit [0,1/2,1]/[1/2] <-> literal [0,.5,1]/[.5]). ATTACKS: built 7 DISTINCT same-spec (all same_spec=True, verified via swebench_unified.markers.same_spec) wrong impls, each editing ONLY the impl region (axioms/pure/pre/post byte-identical): atk_1=prepatch bug (ignores zIsBool, always count 7 in the [] path); atk_2=filled/unfilled swap; atk_3=wrong default count 6; atk_4=control-flow drop of the positional-args branch; atk_5=ungrounded-oracle echo (always return count 7); atk_6=wrong explicit list [1/2,1] for filled bool; atk_7=userLevels ignored (always take data path). Each was given a maximal brute-force proof attempt (nested simp_all/decide/refine across all case splits).

COMMANDS (run, ROOT of this checkout, concurrently in 2 batches of <=4 background jobs): `bash scripts/lean_verify.sh atk_N.lean`. RESULTS: atk_1..atk_7 ALL exit=1 with genuine 'unsolved goals' errors (verified via grep of .out files, e.g. atk_1.lean:94:72 unsolved goals; atk_5:88; atk_7:97) — NOT tactic-syntax artifacts. Positive control pos_ctrl_rebuilt.lean (byte-identical gold impl+proof) exit=0. `#print axioms correct_chooseLevels` on the positive control => [propext, Classical.choice, Quot.sound] (clean, NO sorryAx). Because NO wrong impl closed with a clean-axiom proof, there is no faithful refined patch to materialize/resolve (patches={}), so verify=>correct is not falsified. The R/I legs (mechanically covered by G-CONF) and the single A-reference are consistent with the real callees. >=5 distinct attacks run, none breaks the spec => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check on problem_spec_chooseLevels vs the real _process_contour_level_args selection block (contour.py:1120-1134 @ base_commit 6091437, post-patch), also reused by tri/_tricontour.py.

Mechanical checks:
- same_spec(Solution, Solution_prepatch, lean backend) = True → spec region byte-identical, unchanged by patch.
- lean_verify.sh exit 0 → compiles, no sorry.
- #print axioms correct_chooseLevels = [propext, Classical.choice, Quot.sound] → no sorryAx; proof is real.

Branch-by-branch equivalence (real callee applied, diff confirms patched block):
1. userLevels=some lv → result=lv  ⟺  self.levels is not None → levels_arg=self.levels (args never consulted; priority order matches).
2. none, args=a::_ → result=a  ⟺  self.levels is None, `if args:` truthiness → args[0]. Python `if args:` on a list is exactly non-emptiness (a non-empty list is truthy regardless of element values) = `a :: _`. No divergence.
3. none, [], zIsBool, filled → explicit [0,1/2,1]; ¬filled → explicit [1/2]  ⟺  [0,.5,1]/[.5], with 1/2=.5 exact Rat.
4. none, [], ¬zIsBool → count 7  ⟺  levels_arg=7 hard-wired.

Modeling boundary is honest and not over-strong: the downstream conversion (_autolev, np.asarray, in-range filtering) is genuinely UNCHANGED by the patch and correctly excluded from the modeled function; dtype plumbing through _contour_args/_check_xyz is a pure data-flow refactor represented by the zIsBool input. Exhaustive search over the finite branch structure (Option × list-emptiness × Bool × Bool) yields no input where the spec disagrees with the real repo behavior. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (relaxed_leakage=true, gates.G-LEAK.status=relaxed, RELAXED_LEAKAGE.md present). Independently re-verified the disposition rather than rubber-stamping.

Core soundness — clean: Solution.lean compiles (lean_verify exit 0); #print axioms correct_chooseLevels = [propext, Classical.choice, Quot.sound] with NO sorryAx (proof is real). same_spec(Solution, Solution_prepatch) = True — spec region byte-identical. Prepatch skeleton carries a sorry and drops the boolean special-case (falls through to count 7), so it fails G-DIFF against the identical spec.

Leak scan of the spec view against the PUBLIC problem_statement only (NOT hints_text): the spec discloses (a) boolean+filled -> explicit [0,1/2,1], (b) boolean+line -> explicit [1/2], (c) non-boolean -> count 7. The problem_statement shows plt.contour(boolean_2d_array, levels=[.5]) and proposes 'default levels to [0.5]' and mentions 'the default 8 levels' — token check confirms NO occurrence of contourf / filled / [0,.5,1] / 'at least 2 levels'. Hence facets (b) and (c) are PS-derivable ('single level at 0.5'; '8 levels' = 7 inner boundaries via downstream _autolev count path reconciled by G-CONF), but the FILLED [0,1/2,1] facet is derivable only from hints_text ('For contourf(bool_array) the natural levels would be [0,.5,1]') and the gold/test_patch — this is the single dispositioned semantic leak.

Unavoidability re-confirmed: the F2P test_bool_autolevel pins the filled default (contourf(z).levels == [0,.5,1] etc.); a spec omitting it admits a verifying-but-wrong impl (verify => correct violation). No PS-only reformulation can express the filled discriminator, so faithful+non-leaking is provably impossible. The leak is genuine and unavoidable, matching the recorded disposition exactly.

No NEW leaking line beyond the dispositioned filled facet was found; the disposition is not broken (core gates sound, unavoidability holds). Per the panel recording convention for a properly-dispositioned relaxed-leakage bundle (gates/_audit.py: relaxed leakage recorded as pass at panel layer), honest verdict = NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.