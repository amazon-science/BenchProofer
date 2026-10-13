# P2 adversarial audit — django__django-13513

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
None. The spec is a full functional pin: problem_spec_gatherFrames linkFrames result := result = linkFrames.flatten. Any verifying implementation must satisfy (forall lf, f lf = lf.flatten), i.e. be pointwise identical to flatten, hence observationally identical to gold and guaranteed to resolve. No divergent-but-closing impl exists, so there is no verify-not-implies-correct witness; step 2 (materialize+resolve) is vacuous because zero wrong impls closed.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -43,31 +43,43 @@
   Id.run do
     let mut frames : List Frame := []
     for tb in linkFrames do
+      -- A single combined walk: once a link contributes no frames the walk is
+      -- abandoned, so any later link's frames never reach the report.
+      if tb = [] then
+        return frames
       frames := frames ++ tb
     return frames
 -- impl-end
 
 -- proof-start
-/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
-link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
-theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
-    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
-      = init ++ xs.flatten := by
+-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
+-- impl it cannot close: on any chain with an empty link FOLLOWED by a non-empty
+-- link (e.g. `[[], [f]]`), the impl abandons the walk at the empty link and
+-- returns `[]`, while the spec requires every later link's frames (`[f]`).
+theorem forIn_append_eq (xs : List (List Frame)) (init : List Frame) :
+    (Id.run (forIn xs init (fun tb r =>
+        (ForInStep.yield (r ++ tb) : Id (ForInStep (List Frame))))))
+    = init ++ xs.flatten := by
   induction xs generalizing init with
-  | nil => simp; rfl
+  | nil => simp
   | cons a as ih =>
     rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
+    simp only [Id.run, bind] at ih ⊢
+    rw [ih, List.flatten_cons, List.append_assoc]
 
 theorem correct_gatherFrames :
     ∀ (linkFrames : List (List Frame)),
       problem_spec_gatherFrames linkFrames
         (implementation_gatherFrames linkFrames) := by
-  intro lf
+  intro linkFrames
   unfold problem_spec_gatherFrames implementation_gatherFrames
-  simp only [Id.run, bind, pure]
-  rw [gatherFrames_forIn]
+  have h2 : (Id.run (do
+      let r ← forIn linkFrames [] fun tb r =>
+        ((do pure PUnit.unit; pure (ForInStep.yield (r ++ tb))) : Id (ForInStep (List Frame)))
+      pure r) : List Frame)
+    = Id.run (forIn linkFrames [] fun tb r =>
+        (ForInStep.yield (r ++ tb) : Id (ForInStep (List Frame)))) := rfl
+  show (Id.run _ : List Frame) = linkFrames.flatten
+  rw [h2, forIn_append_eq]
   simp
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,34 +40,15 @@
 
 -- impl-start
 def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
-  Id.run do
-    let mut frames : List Frame := []
-    for tb in linkFrames do
-      frames := frames ++ tb
-    return frames
+  linkFrames.reverse.flatten
 -- impl-end
 
 -- proof-start
-/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
-link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
-theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
-    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
-      = init ++ xs.flatten := by
-  induction xs generalizing init with
-  | nil => simp; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_gatherFrames :
     ∀ (linkFrames : List (List Frame)),
       problem_spec_gatherFrames linkFrames
         (implementation_gatherFrames linkFrames) := by
   intro lf
   unfold problem_spec_gatherFrames implementation_gatherFrames
-  simp only [Id.run, bind, pure]
-  rw [gatherFrames_forIn]
-  simp
+  simp [List.flatten_reverse]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,34 +40,15 @@
 
 -- impl-start
 def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
-  Id.run do
-    let mut frames : List Frame := []
-    for tb in linkFrames do
-      frames := frames ++ tb
-    return frames
+  (linkFrames.takeWhile (· ≠ [])).flatten
 -- impl-end
 
 -- proof-start
-/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
-link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
-theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
-    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
-      = init ++ xs.flatten := by
-  induction xs generalizing init with
-  | nil => simp; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_gatherFrames :
     ∀ (linkFrames : List (List Frame)),
       problem_spec_gatherFrames linkFrames
         (implementation_gatherFrames linkFrames) := by
   intro lf
   unfold problem_spec_gatherFrames implementation_gatherFrames
-  simp only [Id.run, bind, pure]
-  rw [gatherFrames_forIn]
   simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,34 +40,15 @@
 
 -- impl-start
 def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
-  Id.run do
-    let mut frames : List Frame := []
-    for tb in linkFrames do
-      frames := frames ++ tb
-    return frames
+  linkFrames.dropLast.flatten
 -- impl-end
 
 -- proof-start
-/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
-link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
-theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
-    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
-      = init ++ xs.flatten := by
-  induction xs generalizing init with
-  | nil => simp; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_gatherFrames :
     ∀ (linkFrames : List (List Frame)),
       problem_spec_gatherFrames linkFrames
         (implementation_gatherFrames linkFrames) := by
   intro lf
   unfold problem_spec_gatherFrames implementation_gatherFrames
-  simp only [Id.run, bind, pure]
-  rw [gatherFrames_forIn]
   simp
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,35 +39,16 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
-  Id.run do
-    let mut frames : List Frame := []
-    for tb in linkFrames do
-      frames := frames ++ tb
-    return frames
+def implementation_gatherFrames (_linkFrames : List (List Frame)) : List Frame :=
+  []
 -- impl-end
 
 -- proof-start
-/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
-link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
-theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
-    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
-      = init ++ xs.flatten := by
-  induction xs generalizing init with
-  | nil => simp; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_gatherFrames :
     ∀ (linkFrames : List (List Frame)),
       problem_spec_gatherFrames linkFrames
         (implementation_gatherFrames linkFrames) := by
   intro lf
   unfold problem_spec_gatherFrames implementation_gatherFrames
-  simp only [Id.run, bind, pure]
-  rw [gatherFrames_forIn]
   simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,34 +40,15 @@
 
 -- impl-start
 def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
-  Id.run do
-    let mut frames : List Frame := []
-    for tb in linkFrames do
-      frames := frames ++ tb
-    return frames
+  linkFrames.flatten ++ [0]
 -- impl-end
 
 -- proof-start
-/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
-link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
-theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
-    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
-      = init ++ xs.flatten := by
-  induction xs generalizing init with
-  | nil => simp; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_gatherFrames :
     ∀ (linkFrames : List (List Frame)),
       problem_spec_gatherFrames linkFrames
         (implementation_gatherFrames linkFrames) := by
   intro lf
   unfold problem_spec_gatherFrames implementation_gatherFrames
-  simp only [Id.run, bind, pure]
-  rw [gatherFrames_forIn]
   simp
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,34 +40,15 @@
 
 -- impl-start
 def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
-  Id.run do
-    let mut frames : List Frame := []
-    for tb in linkFrames do
-      frames := frames ++ tb
-    return frames
+  linkFrames.tail.flatten
 -- impl-end
 
 -- proof-start
-/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
-link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
-theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
-    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
-      = init ++ xs.flatten := by
-  induction xs generalizing init with
-  | nil => simp; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_gatherFrames :
     ∀ (linkFrames : List (List Frame)),
       problem_spec_gatherFrames linkFrames
         (implementation_gatherFrames linkFrames) := by
   intro lf
   unfold problem_spec_gatherFrames implementation_gatherFrames
-  simp only [Id.run, bind, pure]
-  rw [gatherFrames_forIn]
   simp
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling a diagnostic frame report from a chain of related failures.

When a failure is reported, it is presented together with the chain of earlier
failures it arose from. The chain is walked in a set order (from the deepest
link outward), and each link contributes its own sequence of call frames to
the report.

The complete report is the in-order concatenation of every link's frames: each
link contributes exactly the frames it carries, and the contributions of the
links are laid end to end in chain order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-link
-- frame sequences are taken as the modeled input (their internal assembly is
-- identical across the behavior under study and is abstracted away), and the
-- combination of those sequences into the final report is modeled structurally
-- as a concatenation, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One assembled call frame of the report. Its concrete content is irrelevant
to the behavior modeled here — only which frames appear, and in what order,
matters — so a frame is carried as an opaque identifier. -/
abbrev Frame := Nat
-- pure-end

-- post-conditions-start
/-- `linkFrames` lists, for each link of the chain in walk order, the sequence of
frames that link contributes. The report is the in-order concatenation of all of
them, in chain order. -/
def problem_spec_gatherFrames
    (linkFrames : List (List Frame)) (result : List Frame) : Prop :=
  result = linkFrames.flatten
-- post-conditions-end

-- impl-start
def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
  Id.run do
    let mut frames : List Frame := []
    for tb in linkFrames do
      frames := frames ++ tb
    return frames
-- impl-end

-- proof-start
/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
      = init ++ xs.flatten := by
  induction xs generalizing init with
  | nil => simp; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_gatherFrames :
    ∀ (linkFrames : List (List Frame)),
      problem_spec_gatherFrames linkFrames
        (implementation_gatherFrames linkFrames) := by
  intro lf
  unfold problem_spec_gatherFrames implementation_gatherFrames
  simp only [Id.run, bind, pure]
  rw [gatherFrames_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Project root (used python for markers). same_spec confirmed True for ALL 7 attacks via swebench_unified.markers.same_spec against gold Solution.lean (spec/axioms/pure/pre/post regions byte-identical; only impl+proof regions edited).

COMMANDS: verify = `bash scripts/lean_verify.sh <file>`, run CONCURRENTLY in two background batches (batch1 atk_1..atk_4; batch2 atk_5..atk_7 + pos_control), <=4 at a time. Axioms via appended `#print axioms correct_gatherFrames` in pos_ax.lean.

RESULTS (exit codes): atk_1 rc=1 (prepatch bug: early-return on empty link with carried gold proof -> prepatch reproduced, gold proof fails to close against buggy impl); atk_2 rc=1 (reverse.flatten, order-divergent); atk_3 rc=1 ((takeWhile (.!=[])).flatten, prepatch partial-domain functional form); atk_4 rc=1 (dropLast.flatten, boundary drop-last); atk_5 rc=1 ([] ignores input, ungrounded-oracle echo); atk_6 rc=1 (flatten ++ [0], control-flow-effect extra frame); atk_7 rc=1 (tail.flatten, boundary drop-innermost). ALL 7 fail with 'error: unsolved goals' at the proof's final line -- genuine mathematical unprovability (impl != flatten), NOT a wrong-tactic artifact. Positive control pos_control.lean rc=0. pos_ax.lean rc=0 with axioms exactly [propext, Quot.sound] -- no sorryAx, no declared/custom axioms, clean.

Because NO wrong impl closed with clean axioms, there is NO faithful patch to materialize or run through run_resolve; step 2 is vacuously satisfied and no resolve run was needed. This matches the mechanized proof-obligation: correct_gatherFrames pins the output to a deterministic fully-input-grounded expression, leaving zero slack for a divergent-yet-closing impl.

REFINEMENT.MD AUDIT (A-legs focus): all 5 legs are R/I. Leg 1 = R (List (List Frame) <-> exception chain / per-link tb frames). Legs 2-5 = I. No A-consumed or A-reference legs exist (axiom_check.py is a skip stub; G-AX skips) -- there is NO opaque/axiom callee content, so no kind-3 leg and no A-leg correspondence to validate. The 'I (deep model of changed control flow)' tags on legs 3-4 are legitimate per SPEC_GUIDE 3: the changed decision (an empty link contributes [] but does NOT curtail the walk) is deeply modeled as flatten rather than axiomatized, and verdict.md Role 3 (G-PANEL-2) already confirmed this matches the real post-patch callee get_exception_traceback_frames (per-link tb walk ending with tb=tb.tb_next, no cross-link jump => frames = in-order concat of all links = linkFrames.flatten). Correspondence holds. Relaxed-leakage disposition (documented PS<->gold mismatch) is orthogonal to G-EQ and consistent with mapping.md/RELAXED_LEAKAGE.md.

VERDICT: SOUND after 7 distinct same-spec attacks (>=5 required, covering prepatch bug, order, partial-domain, two boundary, ungrounded-oracle echo, control-flow-effect) all failed to close; positive control verifies with clean axioms.

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
None. The spec is a full functional pin: problem_spec_gatherFrames linkFrames result := result = linkFrames.flatten. Any verifying implementation must satisfy (forall lf, f lf = lf.flatten), i.e. be pointwise identical to flatten, hence observationally identical to gold and guaranteed to resolve. No divergent-but-closing impl exists, so there is no verify-not-implies-correct witness; step 2 (materialize+resolve) is vacuous because zero wrong impls closed.
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
Assembling a diagnostic frame report from a chain of related failures.

When a failure is reported, it is presented together with the chain of earlier
failures it arose from. The chain is walked in a set order (from the deepest
link outward), and each link contributes its own sequence of call frames to
the report.

The complete report is the in-order concatenation of every link's frames: each
link contributes exactly the frames it carries, and the contributions of the
links are laid end to end in chain order.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-link
-- frame sequences are taken as the modeled input (their internal assembly is
-- identical across the behavior under study and is abstracted away), and the
-- combination of those sequences into the final report is modeled structurally
-- as a concatenation, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- One assembled call frame of the report. Its concrete content is irrelevant
to the behavior modeled here — only which frames appear, and in what order,
matters — so a frame is carried as an opaque identifier. -/
abbrev Frame := Nat
-- pure-end

-- post-conditions-start
/-- `linkFrames` lists, for each link of the chain in walk order, the sequence of
frames that link contributes. The report is the in-order concatenation of all of
them, in chain order. -/
def problem_spec_gatherFrames
    (linkFrames : List (List Frame)) (result : List Frame) : Prop :=
  result = linkFrames.flatten
-- post-conditions-end

-- impl-start
def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
  Id.run do
    let mut frames : List Frame := []
    for tb in linkFrames do
      frames := frames ++ tb
    return frames
-- impl-end

-- proof-start
/-- Generalized-over-accumulator helper: the cleaned `forIn` loop appends each
link's frames in chain order, i.e. it computes `init ++ xs.flatten`. -/
theorem gatherFrames_forIn (xs : List (List Frame)) (init : List Frame) :
    (forIn (m := Id) xs init (fun tb r => ForInStep.yield (r ++ tb)))
      = init ++ xs.flatten := by
  induction xs generalizing init with
  | nil => simp; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_gatherFrames :
    ∀ (linkFrames : List (List Frame)),
      problem_spec_gatherFrames linkFrames
        (implementation_gatherFrames linkFrames) := by
  intro lf
  unfold problem_spec_gatherFrames implementation_gatherFrames
  simp only [Id.run, bind, pure]
  rw [gatherFrames_forIn]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Project root (used python for markers). same_spec confirmed True for ALL 7 attacks via swebench_unified.markers.same_spec against gold Solution.lean (spec/axioms/pure/pre/post regions byte-identical; only impl+proof regions edited).

COMMANDS: verify = `bash scripts/lean_verify.sh <file>`, run CONCURRENTLY in two background batches (batch1 atk_1..atk_4; batch2 atk_5..atk_7 + pos_control), <=4 at a time. Axioms via appended `#print axioms correct_gatherFrames` in pos_ax.lean.

RESULTS (exit codes): atk_1 rc=1 (prepatch bug: early-return on empty link with carried gold proof -> prepatch reproduced, gold proof fails to close against buggy impl); atk_2 rc=1 (reverse.flatten, order-divergent); atk_3 rc=1 ((takeWhile (.!=[])).flatten, prepatch partial-domain functional form); atk_4 rc=1 (dropLast.flatten, boundary drop-last); atk_5 rc=1 ([] ignores input, ungrounded-oracle echo); atk_6 rc=1 (flatten ++ [0], control-flow-effect extra frame); atk_7 rc=1 (tail.flatten, boundary drop-innermost). ALL 7 fail with 'error: unsolved goals' at the proof's final line -- genuine mathematical unprovability (impl != flatten), NOT a wrong-tactic artifact. Positive control pos_control.lean rc=0. pos_ax.lean rc=0 with axioms exactly [propext, Quot.sound] -- no sorryAx, no declared/custom axioms, clean.

Because NO wrong impl closed with clean axioms, there is NO faithful patch to materialize or run through run_resolve; step 2 is vacuously satisfied and no resolve run was needed. This matches the mechanized proof-obligation: correct_gatherFrames pins the output to a deterministic fully-input-grounded expression, leaving zero slack for a divergent-yet-closing impl.

REFINEMENT.MD AUDIT (A-legs focus): all 5 legs are R/I. Leg 1 = R (List (List Frame) <-> exception chain / per-link tb frames). Legs 2-5 = I. No A-consumed or A-reference legs exist (axiom_check.py is a skip stub; G-AX skips) -- there is NO opaque/axiom callee content, so no kind-3 leg and no A-leg correspondence to validate. The 'I (deep model of changed control flow)' tags on legs 3-4 are legitimate per SPEC_GUIDE 3: the changed decision (an empty link contributes [] but does NOT curtail the walk) is deeply modeled as flatten rather than axiomatized, and verdict.md Role 3 (G-PANEL-2) already confirmed this matches the real post-patch callee get_exception_traceback_frames (per-link tb walk ending with tb=tb.tb_next, no cross-link jump => frames = in-order concat of all links = linkFrames.flatten). Correspondence holds. Relaxed-leakage disposition (documented PS<->gold mismatch) is orthogonal to G-EQ and consistent with mapping.md/RELAXED_LEAKAGE.md.

VERDICT: SOUND after 7 distinct same-spec attacks (>=5 required, covering prepatch bug, order, partial-domain, two boundary, ungrounded-oracle echo, control-flow-effect) all failed to close; positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Lean compiles (lean_verify.sh exit 0), no sorry; #print axioms correct_gatherFrames => [propext, Quot.sound] only (no sorryAx, proof is genuine). same_spec(Solution.lean, Solution_prepatch.lean) = True with LeanBackend tables (spec region byte-identical). FAITHFULNESS: modeled function problem_spec_gatherFrames linkFrames result := result = linkFrames.flatten, with linkFrames[i] abstracted as the frames link i contributes via get_exception_traceback_frames. The real POST-PATCH get_traceback_frames (verified patched worktree, and base_commit prepatch via git show) rewrites the collection as a flat `while True: frames.extend(get_exception_traceback_frames(exc_value, tb)); pop; ...` — i.e. the in-order concatenation of every link's yielded frames = linkFrames.flatten. 200k-input fuzz of real-concat vs spec-flatten = 0 mismatches. The postcondition agrees with the real callee on every input; it is neither too strong (does not exclude any real behavior) nor drifting. No diverging input exists. CAVEAT (non-blocking, does NOT affect spec faithfulness): refinement.md/mapping.md misdescribe the per-link production — they state an empty/None-traceback link 'yields zero frames' and that the F2P test asserts len==1, but the real get_exception_traceback_frames has `if tb is None: yield {...}` emitting one 'user' frame, and test_innermost_exception_without_traceback actually asserts len(frames)==2. Because the spec pins result = linkFrames.flatten over the ACTUAL per-link yields (whatever they are), this narrative inaccuracy in the abstraction description does not make the postcondition disagree with the real function; the spec stays exactly faithful. Recommend correcting the prose in a doc pass, but no spec/model change is warranted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.json relaxed_leakage=true, G-LEAK status=relaxed, RELAXED_LEAKAGE.md present). Independently re-verified, not rubber-stamped:

CORE SOUNDNESS: same_spec(Solution, Solution_prepatch, lean-backend) = True (spec regions byte-identical). Solution.lean compiles via lean_verify.sh (exit 0); #print axioms correct_gatherFrames = [propext, Quot.sound] — no sorryAx, proof is genuine. Prepatch twin carries the discriminating early-return `if tb = [] then return frames`; gold proof cannot close against it on `[[], [f]]` (spec requires [f], impl returns []), so G-DIFF is sound. patch.diff == gold (G-RESOLVE). All recorded gates pass.

LEAKAGE RE-DERIVATION (vs problem_statement ONLY, hints_text excluded): The public PS is entirely about __suppress_context__/PEP-415 exception-chain SELECTION, which is already correct at base_commit (helper body `return explicit or (None if suppress_context else implicit)`); the gold's touch there is a behavior-preserving hoist to a method. The gold's F2P-graded behavior is instead the empty-traceback NO-CURTAILMENT fix: every link's frames appear = flat concatenation. The spec view's postcondition `result = linkFrames.flatten` plus the docstring 'in-order concatenation of every link's frames ... laid end to end in chain order' semantically discloses exactly that behavior, which is NOT derivable from problem_statement. This is a real semantic leak, but it is precisely the dispositioned all-links-concatenation facet. Unavoidability confirmed: a faithful spec (G-EQ/G-DIFF) must pin flatten (not takeWhile), while PS names only selection — faithful + non-leaking are jointly impossible.

No NEW leak found beyond the dispositioned facet: the spec view names no patched symbol/file/mechanism (no get_exception_traceback_frames, generator, extend, yield, tb_next, no bug→fix curtailment narration — the previously-flagged narrative sentences were de-narrated from both twins identically). No core gate is unsound and the unavoidability argument is not refuted. Per gates/_audit.py + RELAXED_LEAKAGE.md panel convention, a properly-dispositioned relaxed leak is recorded NO-LEAKAGE (pass): dispositioned facet re-confirmed, no leak beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
