# P2 adversarial audit — matplotlib__matplotlib-22871

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
     let column := colVals td lvl
     if 1 < column.dedup.length then
       level := lvl
-      if decide (lvl < 2) && column.contains 1 then
+      if decide (lvl ≤ 2) && column.contains 1 then
         showOffset := false
       return (level, showOffset)
     else if lvl = 0 then
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,6 @@
       level := lvl
       if decide (lvl < 2) && column.contains 1 then
         showOffset := false
-      return (level, showOffset)
     else if lvl = 0 then
       level := 5
   return (level, showOffset)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
     let column := colVals td lvl
     if 1 < column.dedup.length then
       level := lvl
-      if decide (lvl < 2) && column.contains 1 then
+      if decide (lvl < 2) then
         showOffset := false
       return (level, showOffset)
     else if lvl = 0 then
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
         showOffset := false
       return (level, showOffset)
     else if lvl = 0 then
-      level := 5
+      level := 0
   return (level, showOffset)
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -76,113 +76,15 @@
 
 -- impl-start
 def implementation_tickOffset
-    (td : List (List Nat)) (s0 : Bool) : Nat × Bool := Id.run do
-  let mut level : Nat := 5
-  let mut showOffset : Bool := s0
-  for lvl in levels do
-    let column := colVals td lvl
-    if 1 < column.dedup.length then
-      level := lvl
-      if decide (lvl < 2) && column.contains 1 then
-        showOffset := false
-      return (level, showOffset)
-    else if lvl = 0 then
-      level := 5
-  return (level, showOffset)
+    (td : List (List Nat)) (s0 : Bool) : Nat × Bool :=
+  (specLevel td, specShowOffset td s0)
 -- impl-end
 
 
 -- proof-start
-/-- The implementation loop, fully unfolded over the literal `levels` into a
-pure nested-`if` term with NO monadic binds. -/
-def runReduce (td : List (List Nat)) (s0 : Bool) : Nat × Bool :=
-  if 1 < (colVals td 5).dedup.length then
-    (5, if decide (5 < 2) && (colVals td 5).contains 1 then false else s0)
-  else if 1 < (colVals td 4).dedup.length then
-    (4, if decide (4 < 2) && (colVals td 4).contains 1 then false else s0)
-  else if 1 < (colVals td 3).dedup.length then
-    (3, if decide (3 < 2) && (colVals td 3).contains 1 then false else s0)
-  else if 1 < (colVals td 2).dedup.length then
-    (2, if decide (2 < 2) && (colVals td 2).contains 1 then false else s0)
-  else if 1 < (colVals td 1).dedup.length then
-    (1, if decide (1 < 2) && (colVals td 1).contains 1 then false else s0)
-  else if 1 < (colVals td 0).dedup.length then
-    (0, if decide (0 < 2) && (colVals td 0).contains 1 then false else s0)
-  else (5, s0)
-
-/-- `levels.find? (fun j => decide (1 < colDistinct td j))` unfolded over the
-literal `levels` into an explicit nested-`if` term. -/
-def findReduce (td : List (List Nat)) : Option Nat :=
-  if 1 < colDistinct td 5 then some 5
-  else if 1 < colDistinct td 4 then some 4
-  else if 1 < colDistinct td 3 then some 3
-  else if 1 < colDistinct td 2 then some 2
-  else if 1 < colDistinct td 1 then some 1
-  else if 1 < colDistinct td 0 then some 0
-  else none
-
-/-- Definitional bridge: the three column helpers unfold to their bodies. -/
-theorem col_defeqs (td : List (List Nat)) (j : Nat) :
-    colDistinct td j = (colVals td j).dedup.length ∧
-    colHasOne td j = (colVals td j).contains 1 ∧
-    colVals td j = td.map (fun r => r.getD j 0) := ⟨rfl, rfl, rfl⟩
-
-/-- Spec normalization: the `find?` scan over the literal `levels` equals the
-explicit nested-`if` term `findReduce`. -/
-theorem find_to_nestedIf (td : List (List Nat)) :
-    levels.find? (fun j => decide (1 < colDistinct td j)) = findReduce td := by
-  simp only [levels, List.find?, findReduce]
-  grind
-
-/-- Implementation normalization (blocker fix): the `Id.run` loop reduces to the
-pure nested-`if` term `runReduce`, eliminating every monadic bind up front. -/
-theorem impl_to_nestedIf (td : List (List Nat)) (s0 : Bool) :
-    implementation_tickOffset td s0 = runReduce td s0 := by
-  simp only [implementation_tickOffset, levels, Id.run, runReduce,
-    List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, bind_assoc]
-  by_cases h5 : 1 < (colVals td 5).dedup.length
-  · simp only [h5, if_true]; split <;> rfl
-  simp only [h5, if_false, ite_self, pure_bind]
-  by_cases h4 : 1 < (colVals td 4).dedup.length
-  · simp only [h4, if_true]; split <;> rfl
-  simp only [h4, if_false, ite_self, pure_bind]
-  by_cases h3 : 1 < (colVals td 3).dedup.length
-  · simp only [h3, if_true]; split <;> rfl
-  simp only [h3, if_false, ite_self, pure_bind]
-  by_cases h2 : 1 < (colVals td 2).dedup.length
-  · simp only [h2, if_true]; split <;> rfl
-  simp only [h2, if_false, ite_self, pure_bind]
-  by_cases h1 : 1 < (colVals td 1).dedup.length
-  · simp only [h1, if_true]; split <;> rfl
-  simp only [h1, if_false, ite_self, pure_bind]
-  by_cases h0 : 1 < (colVals td 0).dedup.length
-  · simp only [h0, if_true]; split <;> rfl
-  simp only [h0, if_false, pure_bind]
-  rfl
-
-/-- Atom 1: the returned level equals `specLevel`. -/
-theorem level_eq (td : List (List Nat)) (s0 : Bool) :
-    (implementation_tickOffset td s0).1 = specLevel td := by
-  rw [impl_to_nestedIf]
-  unfold specLevel
-  rw [find_to_nestedIf]
-  unfold runReduce findReduce
-  rw [(col_defeqs td 5).1, (col_defeqs td 4).1, (col_defeqs td 3).1,
-      (col_defeqs td 2).1, (col_defeqs td 1).1, (col_defeqs td 0).1]
-  split_ifs <;> rfl
-
-/-- Atom 2: the returned display flag equals `specShowOffset`. -/
-theorem show_eq (td : List (List Nat)) (s0 : Bool) :
-    (implementation_tickOffset td s0).2 = specShowOffset td s0 := by
-  rw [impl_to_nestedIf]
-  rw [specShowOffset, find_to_nestedIf]
-  simp only [runReduce, findReduce, colDistinct, colHasOne]
-  split_ifs <;> simp_all
-
 theorem correct_tickOffset :
     ∀ (td : List (List Nat)) (s0 : Bool),
       problem_spec_tickOffset td s0 (implementation_tickOffset td s0) := by
   intro td s0
-  exact ⟨level_eq td s0, show_eq td s0⟩
-
+  exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,7 +83,7 @@
     let column := colVals td lvl
     if 1 < column.dedup.length then
       level := lvl
-      if decide (lvl < 2) && column.contains 1 then
+      if decide (lvl < 2) && column.contains 0 then
         showOffset := false
       return (level, showOffset)
     else if lvl = 0 then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
   let mut showOffset : Bool := s0
   for lvl in levels do
     let column := colVals td lvl
-    if 1 < column.dedup.length then
+    if 0 < column.dedup.length then
       level := lvl
       if decide (lvl < 2) && column.contains 1 then
         showOffset := false
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
     if 1 < column.dedup.length then
       level := lvl
       if decide (lvl < 2) && column.contains 1 then
-        showOffset := false
+        showOffset := true
       return (level, showOffset)
     else if lvl = 0 then
       level := 5
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the calendar resolution of a set of tick dates, and whether a separate
higher-level summary label (such as the year) should be displayed alongside the
ticks.

Each tick has a calendar breakdown into six ordered components, from coarsest to
finest: year, month, day, hour, minute, second. Given the breakdowns of all the
ticks we decide two things:

* the LEVEL — the finest of these components that is not constant across the
  ticks (scanning from finest to coarsest, the first component whose values are
  not all equal). If every component is constant across the ticks, the level is
  taken to be the finest one.
* whether to DISPLAY the separate summary label. It is displayed by default. It
  is hidden only when the varying level is one of the two coarsest components
  (year or month) AND the value `1` occurs among that component across the ticks
  — i.e. a start-of-year tick is already present, so the summary would be
  redundant. In particular, when a coarse component varies but never takes the
  value `1`, the summary label remains displayed.

We model this as an input→output relation
  (the per-tick calendar breakdowns, the default display flag)
      ↦ (the chosen level, the resulting display flag).
The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-tick
-- calendar breakdowns are taken as an opaque INPUT (each tick is a list of its
-- six calendar components); the distinct-value test over a component and the
-- membership test for the value `1` are modeled directly (deeply), so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The values that calendar component `j` takes across all the ticks. -/
def colVals (td : List (List Nat)) (j : Nat) : List Nat :=
  td.map (fun r => r.getD j 0)

/-- How many DISTINCT values component `j` takes across the ticks. -/
def colDistinct (td : List (List Nat)) (j : Nat) : Nat :=
  (colVals td j).dedup.length

/-- Whether the value `1` occurs in component `j` across the ticks. -/
def colHasOne (td : List (List Nat)) (j : Nat) : Bool :=
  (colVals td j).contains 1

/-- Component indices from finest (5 = second) to coarsest (0 = year). -/
def levels : List Nat := [5, 4, 3, 2, 1, 0]

/-- The chosen level: the first component (finest→coarsest) that is not constant
across the ticks; the finest component (5) if all components are constant. -/
def specLevel (td : List (List Nat)) : Nat :=
  (levels.find? (fun j => decide (1 < colDistinct td j))).getD 5

/-- The resulting display flag: the default flag `s0`, turned off only when the
varying level is one of the two coarsest components and the value `1` occurs in
that component. -/
def specShowOffset (td : List (List Nat)) (s0 : Bool) : Bool :=
  match levels.find? (fun j => decide (1 < colDistinct td j)) with
  | some j => if decide (j < 2) && colHasOne td j then false else s0
  | none => s0
-- pure-end

-- post-conditions-start
/-- The chosen level equals `specLevel` and the display flag equals
`specShowOffset`, each determined structurally from the per-tick calendar
breakdowns and the default flag. -/
def problem_spec_tickOffset
    (td : List (List Nat)) (s0 : Bool) (result : Nat × Bool) : Prop :=
  result.1 = specLevel td ∧ result.2 = specShowOffset td s0
-- post-conditions-end

-- impl-start
def implementation_tickOffset
    (td : List (List Nat)) (s0 : Bool) : Nat × Bool := Id.run do
  let mut level : Nat := 5
  let mut showOffset : Bool := s0
  for lvl in levels do
    let column := colVals td lvl
    if 1 < column.dedup.length then
      level := lvl
      if decide (lvl < 2) && column.contains 1 then
        showOffset := false
      return (level, showOffset)
    else if lvl = 0 then
      level := 5
  return (level, showOffset)
-- impl-end


-- proof-start
/-- The implementation loop, fully unfolded over the literal `levels` into a
pure nested-`if` term with NO monadic binds. -/
def runReduce (td : List (List Nat)) (s0 : Bool) : Nat × Bool :=
  if 1 < (colVals td 5).dedup.length then
    (5, if decide (5 < 2) && (colVals td 5).contains 1 then false else s0)
  else if 1 < (colVals td 4).dedup.length then
    (4, if decide (4 < 2) && (colVals td 4).contains 1 then false else s0)
  else if 1 < (colVals td 3).dedup.length then
    (3, if decide (3 < 2) && (colVals td 3).contains 1 then false else s0)
  else if 1 < (colVals td 2).dedup.length then
    (2, if decide (2 < 2) && (colVals td 2).contains 1 then false else s0)
  else if 1 < (colVals td 1).dedup.length then
    (1, if decide (1 < 2) && (colVals td 1).contains 1 then false else s0)
  else if 1 < (colVals td 0).dedup.length then
    (0, if decide (0 < 2) && (colVals td 0).contains 1 then false else s0)
  else (5, s0)

/-- `levels.find? (fun j => decide (1 < colDistinct td j))` unfolded over the
literal `levels` into an explicit nested-`if` term. -/
def findReduce (td : List (List Nat)) : Option Nat :=
  if 1 < colDistinct td 5 then some 5
  else if 1 < colDistinct td 4 then some 4
  else if 1 < colDistinct td 3 then some 3
  else if 1 < colDistinct td 2 then some 2
  else if 1 < colDistinct td 1 then some 1
  else if 1 < colDistinct td 0 then some 0
  else none

/-- Definitional bridge: the three column helpers unfold to their bodies. -/
theorem col_defeqs (td : List (List Nat)) (j : Nat) :
    colDistinct td j = (colVals td j).dedup.length ∧
    colHasOne td j = (colVals td j).contains 1 ∧
    colVals td j = td.map (fun r => r.getD j 0) := ⟨rfl, rfl, rfl⟩

/-- Spec normalization: the `find?` scan over the literal `levels` equals the
explicit nested-`if` term `findReduce`. -/
theorem find_to_nestedIf (td : List (List Nat)) :
    levels.find? (fun j => decide (1 < colDistinct td j)) = findReduce td := by
  simp only [levels, List.find?, findReduce]
  grind

/-- Implementation normalization (blocker fix): the `Id.run` loop reduces to the
pure nested-`if` term `runReduce`, eliminating every monadic bind up front. -/
theorem impl_to_nestedIf (td : List (List Nat)) (s0 : Bool) :
    implementation_tickOffset td s0 = runReduce td s0 := by
  simp only [implementation_tickOffset, levels, Id.run, runReduce,
    List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, bind_assoc]
  by_cases h5 : 1 < (colVals td 5).dedup.length
  · simp only [h5, if_true]; split <;> rfl
  simp only [h5, if_false, ite_self, pure_bind]
  by_cases h4 : 1 < (colVals td 4).dedup.length
  · simp only [h4, if_true]; split <;> rfl
  simp only [h4, if_false, ite_self, pure_bind]
  by_cases h3 : 1 < (colVals td 3).dedup.length
  · simp only [h3, if_true]; split <;> rfl
  simp only [h3, if_false, ite_self, pure_bind]
  by_cases h2 : 1 < (colVals td 2).dedup.length
  · simp only [h2, if_true]; split <;> rfl
  simp only [h2, if_false, ite_self, pure_bind]
  by_cases h1 : 1 < (colVals td 1).dedup.length
  · simp only [h1, if_true]; split <;> rfl
  simp only [h1, if_false, ite_self, pure_bind]
  by_cases h0 : 1 < (colVals td 0).dedup.length
  · simp only [h0, if_true]; split <;> rfl
  simp only [h0, if_false, pure_bind]
  rfl

/-- Atom 1: the returned level equals `specLevel`. -/
theorem level_eq (td : List (List Nat)) (s0 : Bool) :
    (implementation_tickOffset td s0).1 = specLevel td := by
  rw [impl_to_nestedIf]
  unfold specLevel
  rw [find_to_nestedIf]
  unfold runReduce findReduce
  rw [(col_defeqs td 5).1, (col_defeqs td 4).1, (col_defeqs td 3).1,
      (col_defeqs td 2).1, (col_defeqs td 1).1, (col_defeqs td 0).1]
  split_ifs <;> rfl

/-- Atom 2: the returned display flag equals `specShowOffset`. -/
theorem show_eq (td : List (List Nat)) (s0 : Bool) :
    (implementation_tickOffset td s0).2 = specShowOffset td s0 := by
  rw [impl_to_nestedIf]
  rw [specShowOffset, find_to_nestedIf]
  simp only [runReduce, findReduce, colDistinct, colHasOne]
  split_ifs <;> simp_all

theorem correct_tickOffset :
    ∀ (td : List (List Nat)) (s0 : Bool),
      problem_spec_tickOffset td s0 (implementation_tickOffset td s0) := by
  intro td s0
  exact ⟨level_eq td s0, show_eq td s0⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The postcondition problem_spec_tickOffset td s0 result := result.1 = specLevel td AND result.2 = specShowOffset td s0 is a TOTAL POINTWISE functional spec: universally quantified over all td:List(List Nat), s0:Bool with NO precondition. Any impl closing correct_tickOffset is forced extensionally equal to the gold decision function on every input, so verify => correct.

SAME-SPEC: all 8 attacks + pos_control return same_spec(gold, atk, LeanBackend.language)=True (spec view byte-identical; only impl+proof regions edited). Command: markers.same_spec on Solution.lean vs each atk_N.lean.

### ATTACKS (cmd: bash scripts/lean_verify.sh <path>):
- atk_1 partial/boundary (lvl<=2 instead of lvl<2, hides offset on varying DAY): rc=1 (does NOT close).
- atk_2 control-flow-effect (drop early return, keeps scanning to coarsest varying component -> wrong level): rc=1.
- atk_3 = PREPATCH BUG (drop the column.contains 1 conjunct, unconditional hide when lvl<2): rc=1 -> prepatch reproduced, spec rejects the bug (F2P Feb-Aug).
- atk_4 wrong fall-through default level (all-constant returns level 0 not 5): rc=1.
- atk_5 ungrounded-oracle echo: implementation returns (specLevel td, specShowOffset td s0) directly. rc=0, CLOSES; #print axioms correct_tickOffset = 'does not depend on any axioms' (clean, no sorryAx). This is EXTENSIONALLY IDENTICAL to the spec (a legitimate correct impl, not a wrong one). Per mandate its faithful refined patch was MATERIALIZED (atk_5.patch = the gold post-patch decision loop, since the echo computes exactly the post-patch function) and RUN through run_resolve: RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. A resolving echo of the gold is NOT a spec weakness (post-2026-08-06 G-PANEL-1 policy). Does NOT break the spec.
- atk_6 wrong membership value (contains 0 instead of contains 1): rc=1.
- atk_7 distinct-count off-by-one (0<distinct so every nonempty column 'varies' -> always level 5): rc=1.
- atk_8 negated show flag (set showOffset:=true where gold hides): rc=1.

POSITIVE CONTROL: pos_control.lean = Solution.lean verbatim -> rc=0; #print axioms correct_tickOffset = [propext, Classical.choice, Quot.sound] (clean).

DEEP-MODEL / A-LEG AUDIT: refinement.md declares NO A-legs (axioms region empty, G-AX skips legitimately). All 10 legs are R or I (no kind-3). Two numpy reads are modeled DEEPLY over the input column: len(np.unique(col))>1 <-> 1 < col.dedup.length, and np.any(unique==1) <-> 1 in col. Independent 200k differential (numpy 1.26.4 oracle vs deep-model shadow, values incl 0 and 1 boundaries, n=1..7 ticks): 0 divergences. Correspondence to real callee holds. np.unique's sorted ORDER is never consumed (only count + ==1 membership), so dedup (set-faithful) is exact. Only out-of-domain divergence (empty td) is non-behavioral totalization, documented; format_ticks always called with >=1 tick.

CONCLUSION: No same-spec wrong impl closes with clean axioms. The only closing candidate besides the positive control (atk_5) is extensionally equal to the spec and its materialized faithful patch RESOLVES. The prepatch bug is reproduced and rejected. Spec is a faithful, non-weak model. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the calendar resolution of a set of tick dates, and whether a separate
higher-level summary label (such as the year) should be displayed alongside the
ticks.

Each tick has a calendar breakdown into six ordered components, from coarsest to
finest: year, month, day, hour, minute, second. Given the breakdowns of all the
ticks we decide two things:

* the LEVEL — the finest of these components that is not constant across the
  ticks (scanning from finest to coarsest, the first component whose values are
  not all equal). If every component is constant across the ticks, the level is
  taken to be the finest one.
* whether to DISPLAY the separate summary label. It is displayed by default. It
  is hidden only when the varying level is one of the two coarsest components
  (year or month) AND the value `1` occurs among that component across the ticks
  — i.e. a start-of-year tick is already present, so the summary would be
  redundant. In particular, when a coarse component varies but never takes the
  value `1`, the summary label remains displayed.

We model this as an input→output relation
  (the per-tick calendar breakdowns, the default display flag)
      ↦ (the chosen level, the resulting display flag).
The implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-tick
-- calendar breakdowns are taken as an opaque INPUT (each tick is a list of its
-- six calendar components); the distinct-value test over a component and the
-- membership test for the value `1` are modeled directly (deeply), so no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The values that calendar component `j` takes across all the ticks. -/
def colVals (td : List (List Nat)) (j : Nat) : List Nat :=
  td.map (fun r => r.getD j 0)

/-- How many DISTINCT values component `j` takes across the ticks. -/
def colDistinct (td : List (List Nat)) (j : Nat) : Nat :=
  (colVals td j).dedup.length

/-- Whether the value `1` occurs in component `j` across the ticks. -/
def colHasOne (td : List (List Nat)) (j : Nat) : Bool :=
  (colVals td j).contains 1

/-- Component indices from finest (5 = second) to coarsest (0 = year). -/
def levels : List Nat := [5, 4, 3, 2, 1, 0]

/-- The chosen level: the first component (finest→coarsest) that is not constant
across the ticks; the finest component (5) if all components are constant. -/
def specLevel (td : List (List Nat)) : Nat :=
  (levels.find? (fun j => decide (1 < colDistinct td j))).getD 5

/-- The resulting display flag: the default flag `s0`, turned off only when the
varying level is one of the two coarsest components and the value `1` occurs in
that component. -/
def specShowOffset (td : List (List Nat)) (s0 : Bool) : Bool :=
  match levels.find? (fun j => decide (1 < colDistinct td j)) with
  | some j => if decide (j < 2) && colHasOne td j then false else s0
  | none => s0
-- pure-end

-- post-conditions-start
/-- The chosen level equals `specLevel` and the display flag equals
`specShowOffset`, each determined structurally from the per-tick calendar
breakdowns and the default flag. -/
def problem_spec_tickOffset
    (td : List (List Nat)) (s0 : Bool) (result : Nat × Bool) : Prop :=
  result.1 = specLevel td ∧ result.2 = specShowOffset td s0
-- post-conditions-end

-- impl-start
def implementation_tickOffset
    (td : List (List Nat)) (s0 : Bool) : Nat × Bool := Id.run do
  let mut level : Nat := 5
  let mut showOffset : Bool := s0
  for lvl in levels do
    let column := colVals td lvl
    if 1 < column.dedup.length then
      level := lvl
      if decide (lvl < 2) && column.contains 1 then
        showOffset := false
      return (level, showOffset)
    else if lvl = 0 then
      level := 5
  return (level, showOffset)
-- impl-end


-- proof-start
/-- The implementation loop, fully unfolded over the literal `levels` into a
pure nested-`if` term with NO monadic binds. -/
def runReduce (td : List (List Nat)) (s0 : Bool) : Nat × Bool :=
  if 1 < (colVals td 5).dedup.length then
    (5, if decide (5 < 2) && (colVals td 5).contains 1 then false else s0)
  else if 1 < (colVals td 4).dedup.length then
    (4, if decide (4 < 2) && (colVals td 4).contains 1 then false else s0)
  else if 1 < (colVals td 3).dedup.length then
    (3, if decide (3 < 2) && (colVals td 3).contains 1 then false else s0)
  else if 1 < (colVals td 2).dedup.length then
    (2, if decide (2 < 2) && (colVals td 2).contains 1 then false else s0)
  else if 1 < (colVals td 1).dedup.length then
    (1, if decide (1 < 2) && (colVals td 1).contains 1 then false else s0)
  else if 1 < (colVals td 0).dedup.length then
    (0, if decide (0 < 2) && (colVals td 0).contains 1 then false else s0)
  else (5, s0)

/-- `levels.find? (fun j => decide (1 < colDistinct td j))` unfolded over the
literal `levels` into an explicit nested-`if` term. -/
def findReduce (td : List (List Nat)) : Option Nat :=
  if 1 < colDistinct td 5 then some 5
  else if 1 < colDistinct td 4 then some 4
  else if 1 < colDistinct td 3 then some 3
  else if 1 < colDistinct td 2 then some 2
  else if 1 < colDistinct td 1 then some 1
  else if 1 < colDistinct td 0 then some 0
  else none

/-- Definitional bridge: the three column helpers unfold to their bodies. -/
theorem col_defeqs (td : List (List Nat)) (j : Nat) :
    colDistinct td j = (colVals td j).dedup.length ∧
    colHasOne td j = (colVals td j).contains 1 ∧
    colVals td j = td.map (fun r => r.getD j 0) := ⟨rfl, rfl, rfl⟩

/-- Spec normalization: the `find?` scan over the literal `levels` equals the
explicit nested-`if` term `findReduce`. -/
theorem find_to_nestedIf (td : List (List Nat)) :
    levels.find? (fun j => decide (1 < colDistinct td j)) = findReduce td := by
  simp only [levels, List.find?, findReduce]
  grind

/-- Implementation normalization (blocker fix): the `Id.run` loop reduces to the
pure nested-`if` term `runReduce`, eliminating every monadic bind up front. -/
theorem impl_to_nestedIf (td : List (List Nat)) (s0 : Bool) :
    implementation_tickOffset td s0 = runReduce td s0 := by
  simp only [implementation_tickOffset, levels, Id.run, runReduce,
    List.forIn_cons, List.forIn_nil, bind_pure_comp, map_pure, bind_assoc]
  by_cases h5 : 1 < (colVals td 5).dedup.length
  · simp only [h5, if_true]; split <;> rfl
  simp only [h5, if_false, ite_self, pure_bind]
  by_cases h4 : 1 < (colVals td 4).dedup.length
  · simp only [h4, if_true]; split <;> rfl
  simp only [h4, if_false, ite_self, pure_bind]
  by_cases h3 : 1 < (colVals td 3).dedup.length
  · simp only [h3, if_true]; split <;> rfl
  simp only [h3, if_false, ite_self, pure_bind]
  by_cases h2 : 1 < (colVals td 2).dedup.length
  · simp only [h2, if_true]; split <;> rfl
  simp only [h2, if_false, ite_self, pure_bind]
  by_cases h1 : 1 < (colVals td 1).dedup.length
  · simp only [h1, if_true]; split <;> rfl
  simp only [h1, if_false, ite_self, pure_bind]
  by_cases h0 : 1 < (colVals td 0).dedup.length
  · simp only [h0, if_true]; split <;> rfl
  simp only [h0, if_false, pure_bind]
  rfl

/-- Atom 1: the returned level equals `specLevel`. -/
theorem level_eq (td : List (List Nat)) (s0 : Bool) :
    (implementation_tickOffset td s0).1 = specLevel td := by
  rw [impl_to_nestedIf]
  unfold specLevel
  rw [find_to_nestedIf]
  unfold runReduce findReduce
  rw [(col_defeqs td 5).1, (col_defeqs td 4).1, (col_defeqs td 3).1,
      (col_defeqs td 2).1, (col_defeqs td 1).1, (col_defeqs td 0).1]
  split_ifs <;> rfl

/-- Atom 2: the returned display flag equals `specShowOffset`. -/
theorem show_eq (td : List (List Nat)) (s0 : Bool) :
    (implementation_tickOffset td s0).2 = specShowOffset td s0 := by
  rw [impl_to_nestedIf]
  rw [specShowOffset, find_to_nestedIf]
  simp only [runReduce, findReduce, colDistinct, colHasOne]
  split_ifs <;> simp_all

theorem correct_tickOffset :
    ∀ (td : List (List Nat)) (s0 : Bool),
      problem_spec_tickOffset td s0 (implementation_tickOffset td s0) := by
  intro td s0
  exact ⟨level_eq td s0, show_eq td s0⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The postcondition problem_spec_tickOffset td s0 result := result.1 = specLevel td AND result.2 = specShowOffset td s0 is a TOTAL POINTWISE functional spec: universally quantified over all td:List(List Nat), s0:Bool with NO precondition. Any impl closing correct_tickOffset is forced extensionally equal to the gold decision function on every input, so verify => correct.

SAME-SPEC: all 8 attacks + pos_control return same_spec(gold, atk, LeanBackend.language)=True (spec view byte-identical; only impl+proof regions edited). Command: markers.same_spec on Solution.lean vs each atk_N.lean.

### ATTACKS (cmd: bash scripts/lean_verify.sh <path>):
- atk_1 partial/boundary (lvl<=2 instead of lvl<2, hides offset on varying DAY): rc=1 (does NOT close).
- atk_2 control-flow-effect (drop early return, keeps scanning to coarsest varying component -> wrong level): rc=1.
- atk_3 = PREPATCH BUG (drop the column.contains 1 conjunct, unconditional hide when lvl<2): rc=1 -> prepatch reproduced, spec rejects the bug (F2P Feb-Aug).
- atk_4 wrong fall-through default level (all-constant returns level 0 not 5): rc=1.
- atk_5 ungrounded-oracle echo: implementation returns (specLevel td, specShowOffset td s0) directly. rc=0, CLOSES; #print axioms correct_tickOffset = 'does not depend on any axioms' (clean, no sorryAx). This is EXTENSIONALLY IDENTICAL to the spec (a legitimate correct impl, not a wrong one). Per mandate its faithful refined patch was MATERIALIZED (atk_5.patch = the gold post-patch decision loop, since the echo computes exactly the post-patch function) and RUN through run_resolve: RESOLVED=True, COMPLETED=True, note='resolved', attempts=1, flaky=False. A resolving echo of the gold is NOT a spec weakness (post-2026-08-06 G-PANEL-1 policy). Does NOT break the spec.
- atk_6 wrong membership value (contains 0 instead of contains 1): rc=1.
- atk_7 distinct-count off-by-one (0<distinct so every nonempty column 'varies' -> always level 5): rc=1.
- atk_8 negated show flag (set showOffset:=true where gold hides): rc=1.

POSITIVE CONTROL: pos_control.lean = Solution.lean verbatim -> rc=0; #print axioms correct_tickOffset = [propext, Classical.choice, Quot.sound] (clean).

DEEP-MODEL / A-LEG AUDIT: refinement.md declares NO A-legs (axioms region empty, G-AX skips legitimately). All 10 legs are R or I (no kind-3). Two numpy reads are modeled DEEPLY over the input column: len(np.unique(col))>1 <-> 1 < col.dedup.length, and np.any(unique==1) <-> 1 in col. Independent 200k differential (numpy 1.26.4 oracle vs deep-model shadow, values incl 0 and 1 boundaries, n=1..7 ticks): 0 divergences. Correspondence to real callee holds. np.unique's sorted ORDER is never consumed (only count + ==1 membership), so dedup (set-faithful) is exact. Only out-of-domain divergence (empty td) is non-behavioral totalization, documented; format_ticks always called with >=1 tick.

CONCLUSION: No same-spec wrong impl closes with clean axioms. The only closing candidate besides the positive control (atk_5) is extensionally equal to the spec and its materialized faithful patch RESOLVES. The prepatch bug is reproduced and rejected. Spec is a faithful, non-weak model. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on matplotlib__matplotlib-22871 lean bundle. FINDINGS: (1) Spec region byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(...) = True. Only impl+proof regions differ. (2) Solution.lean compiles via scripts/lean_verify.sh (exit 0). (3) #print axioms correct_tickOffset => [propext, Classical.choice, Quot.sound] only (standard Lean/Mathlib axioms); no sorryAx, proof is genuine. (4) Bundle conformance_check.py: status=pass, n_disagreements=0, prepatch_discriminated=true over edge matrix + 120k fuzz draws. (5) Independent adversarial differential I wrote (300k random draws, non-empty td, values including 0/1/negatives/2000s/boundary calendar values, both s0) against the real post-patch numpy loop (np.unique/len/np.any(unique==1) over tickdate[:,level]) found ZERO divergences on the meaningful non-empty domain.

SPEC-vs-REAL analysis: specLevel = first component (finest->coarsest, [5,4,3,2,1,0]) with 1 < colDistinct, else 5, matching `for level in range(5,-1,-1): if len(np.unique(tickdate[:,level]))>1: break; elif level==0: level=5`. specShowOffset turns the default flag off iff varying j<2 AND colHasOne j, matching `if level<2 and np.any(unique==1): show_offset=False`. The two numpy reads are modeled DEEPLY: len(np.unique(c))>1 ~ 1 < (colVals).dedup.length, and np.any(unique==1) ~ colVals.contains 1. np.unique's sorted ORDER is never consumed by the loop (only the distinct COUNT and ==1 membership), so dedup (set-faithful) is exact for both reads. No axiomatized callee; G-AX correctly skips.

The ONLY input where the modeled function differs from the real callee is the empty-ticks case: real numpy raises IndexError on tickdate[:,level] (a 0-length 1-D array) whereas the spec returns (5, s0). This is the spec being defined on a LARGER/more-permissive domain than the real code, NOT the spec being too strong, and empty ticks are outside the meaningful input domain (date locators always emit >=1 tick; format_ticks is only called with real tick values). It does not constitute a faithfulness break (spec drift toward over-strength). No diverging input exists on the meaningful domain where the spec disagrees with (and is stronger than) the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lean spec view = docstring + axioms(empty) + pure helpers + post-conditions; impl and proof regions are fully elided ('implementation elided', 'proof elided'). same_spec(Solution.lean, Solution_prepatch.lean)=True and the lexical leakage.screen passes (no hard failures) — no gold-patch tokens (np.unique, np.any, tickdate[:, level], 'unique') or problem_statement phrasing appear.

Semantic assessment: The postcondition encodes the CORRECT (fixed) behavior — summary hidden iff varying level is one of the two coarsest components (decide (j<2)) AND colHasOne td j (value 1 occurs in that column). Encoding the fixed behavior is inherent to any faithful spec and is NOT leakage; it is stated entirely in the spec's own abstract vocabulary (colVals/colDistinct/colHasOne over List Nat columns, dedup.length, contains 1), not by quoting the gold diff. A solver still must author the implementation and its correctness proof, both withheld. The docstring rationale ('a start-of-year tick is already present, so the summary would be redundant') is an abstract behavioral paraphrase, not a verbatim echo of the patch comment or the problem_statement, and the problem_statement itself only describes the observed symptom (year not shown for <12-month spans without January), not the level<2 / value-1 discriminator. The gold EDIT text cannot be reconstructed from the spec view beyond what a correct behavioral spec must inherently state.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
