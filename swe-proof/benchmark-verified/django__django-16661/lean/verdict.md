# P2 adversarial audit — django__django-16661

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
No same-spec wrong impl admits a closing proof. The postcondition problem_spec_lookupAllowed is EXACT equality (result = lookupDecision steps validLookups fkeyAllowed) with NO axioms (refinement.md A-legs = None; grep confirms no axiom/opaque/sorry callee). Any impl that differs from lookupDecision on even one input makes correct_lookupAllowed a FALSE proposition, hence unprovable. Demonstrated concretely: for each of the 7 attacks I materialized disp_N.lean that keeps the wrong impl byte-for-byte but proves `implementation_lookupAllowed W ≠ lookupDecision W` at a concrete witness W via `decide` (NOT native_decide) — all 7 CLOSE (exit 0, clean), which machine-proves correct_lookupAllowed is false for each wrong impl. Witnesses: atk_1(prepatch bug: pr && !inTargetFields)/atk_2(dropped !inParents conjunct): steps=[⟨1,T,T,T,F,F,F,F,F⟩,⟨2,T,F,F,F,inParents=T,...⟩], VL=[], fkey=false — gold appends part 2 (inParents collapse only fires under prev.is_relation guard combos), the buggy guards diverge → relationParts differ. atk_3(len<1 vs ≤1): single appended step, len1 → gold True, atk False. atk_4(ignores hasPathInfos break): a step with hasPathInfos=F must stop the walk; atk keeps folding → extra relation part. atk_5(ungrounded oracle: always true): chain→[1,2] len2 with VL=[] → spec False. atk_6(&& instead of ||): [1,2] with VL=[[1,2]] → spec True(||) but atk requires both join-keys present → False. atk_7(prepend instead of append): order of relationParts flipped, membership in VL=[[1,2]] fails.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -167,9 +167,7 @@
           let appendIt : Bool :=
             match prev with
             | none => true
-            | some pr =>
-                pr && !step.inParents && !step.isAutoField &&
-                  (!step.modelHasAutoField || !step.partInPrevToFields)
+            | some pr => pr && !step.inTargetFields
           if appendIt then
             relationParts := relationParts ++ [step.part]
           if !step.hasPathInfos then
@@ -183,206 +181,14 @@
 -- impl-end
 
 -- proof-start
--- @decl:phi_stateProj-start
-/-- Projection from the spec's record state to the impl's anonymous 4-tuple
-accumulator. Component order matches the do-elaborator's packing of the four
-`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
-def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
-  (s.relationParts, s.prev, s.lastPart, s.stopped)
--- @decl:phi_stateProj-end
-
--- @decl:loopBody_tuple-start
-/-- The tuple-threading form of one loop iteration, read directly off
-`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
-destructured into its four components. This is what the impl's `forIn` reduces
-to under `Id`. -/
-def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
-    List Nat × Option Bool × Nat × Bool :=
-  let relationParts := acc.1
-  let prev := acc.2.1
-  let stopped := acc.2.2.2
-  if stopped then acc
-  else
-    let lastPart := step.part
-    if !step.exists_ then (relationParts, prev, lastPart, true)
-    else
-      let appendIt : Bool :=
-        match prev with
-        | none => true
-        | some pr =>
-            pr && !step.inParents && !step.isAutoField &&
-              (!step.modelHasAutoField || !step.partInPrevToFields)
-      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
-      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
-      else (relationParts, some step.isRelation, lastPart, false)
--- @decl:loopBody_tuple-end
-
--- @ns:forIn_to_foldl-start
--- @decl:forIn_to_foldl-start
-/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
-over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
-tuple init. -/
-theorem forIn_to_foldl (steps : List PathStep) :
-    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
-        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
-      = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  simp only [Id.run, List.forIn_yield_eq_foldl]
--- @decl:forIn_to_foldl-end
--- @ns:forIn_to_foldl-end
-
--- @ns:step_correspondence-start
--- @decl:step_correspondence-start
-/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
-result equals applying the tuple loop body to the projected state. -/
-theorem step_correspondence (s : LoopState) (step : PathStep) :
-    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
-  cases s with
-  | mk relationParts prev lastPart stopped =>
-    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
-    repeat' (first | rfl | simp_all | split)
--- @decl:step_correspondence-end
--- @ns:step_correspondence-end
-
--- @ns:runLoop_proj_eq-start
--- @decl:runLoop_proj_eq-start
-/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
-tuple foldl from the tuple init. -/
-theorem runLoop_proj_eq (steps : List PathStep) :
-    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  unfold runLoop
-  have key : ∀ (l : List PathStep) (s : LoopState),
-      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
-    intro l
-    induction l with
-    | nil => intro s; rfl
-    | cons a t ih =>
-      intro s
-      simp only [List.foldl_cons]
-      rw [ih (stepFold s a), step_correspondence]
-  exact key steps _
--- @decl:runLoop_proj_eq-end
--- @ns:runLoop_proj_eq-end
-
--- @ns:impl_loopBridge-start
--- @decl:impl_loopBridge-start
-/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
-— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
-tuple accumulator, and its post-loop tail decision — equals the closed
-`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
-decision read off the tuple components. This isolates the monad/do-elaboration
-reduction (prove by exposing the always-`yield` `forIn` and applying the
-`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
-theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
-    (fkeyAllowed : Bool) :
-    implementation_lookupAllowed steps validLookups fkeyAllowed
-      = (if fkeyAllowed then true
-         else
-           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
-           if acc.1.length ≤ 1 then true
-           else validLookups.contains acc.1 ||
-                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
-  unfold implementation_lookupAllowed
-  split
-  · rfl
-  · simp only [Id.run, bind, pure]
-    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
-    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
-    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
-    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
-        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
-          (fun step r =>
-            if (!r.snd.snd.snd) = true then
-              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-              else
-                if
-                    (match r.snd.fst with
-                      | none => true
-                      | some pr =>
-                        pr && !step.inParents && !step.isAutoField &&
-                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
-                      true then
-                  if (!step.hasPathInfos) = true then
-                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
-                else
-                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
-            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
-          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
-             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
-      intro l
-      induction l with
-      | nil => intro lp pv rp st; rfl
-      | cons a t ih =>
-        intro lp pv rp st
-        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
-        by_cases hst : st = true
-        · subst hst
-          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
-          exact ih lp pv rp true
-        · simp only [Bool.not_eq_true] at hst
-          subst hst
-          simp only [Bool.not_false, if_true]
-          by_cases hex : a.exists_ = true
-          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
-            by_cases happ :
-                (match pv with
-                  | none => true
-                  | some pr =>
-                    pr && !a.inParents && !a.isAutoField &&
-                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
-            · simp only [happ, if_true]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv (rp ++ [a.part]) true
-            · simp only [happ, Bool.false_eq_true, if_false]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) rp false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv rp true
-          · simp only [Bool.not_eq_true] at hex
-            simp only [hex, Bool.not_false, if_true]
-            exact ih a.part pv rp true
-    generalize hR : (forIn steps _ _ : Id _) = R
-    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
-                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
-      hR.symm.trans (key steps 0 none [] false)
-    rw [hkey]
--- @decl:impl_loopBridge-end
--- @ns:impl_loopBridge-end
-
--- @ns:tail_match-start
--- @decl:tail_match-start
-/-- DecisionTail: the post-loop decision computed from the projected tuple
-components equals the decision computed from the record's fields. -/
-theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
-    (if (phi_stateProj st).1.length ≤ 1 then true
-     else validLookups.contains (phi_stateProj st).1 ||
-          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
-      = (if st.relationParts.length ≤ 1 then true
-         else validLookups.contains st.relationParts ||
-              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
--- @decl:tail_match-end
--- @ns:tail_match-end
-
-
 theorem correct_lookupAllowed :
     ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
       problem_spec_lookupAllowed steps validLookups fkeyAllowed
         (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
   intro steps validLookups fkeyAllowed
-  unfold problem_spec_lookupAllowed
-  rw [impl_loopBridge]
-  by_cases h : fkeyAllowed
-  · simp [h, lookupDecision]
-  · simp only [h, if_false]
-    rw [← runLoop_proj_eq]
-    unfold lookupDecision
-    simp only [h, if_false]
-    exact tail_match validLookups (runLoop steps)
+  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision runLoop stepFold continuesLocal
+  simp only [Id.run, List.forIn_yield_eq_foldl]
+  induction steps with
+  | nil => simp_all
+  | cons h t ih => simp_all <;> (try rfl) <;> (repeat' (first | rfl | simp_all | split))
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -168,7 +168,7 @@
             match prev with
             | none => true
             | some pr =>
-                pr && !step.inParents && !step.isAutoField &&
+                pr && !step.isAutoField &&
                   (!step.modelHasAutoField || !step.partInPrevToFields)
           if appendIt then
             relationParts := relationParts ++ [step.part]
@@ -183,206 +183,14 @@
 -- impl-end
 
 -- proof-start
--- @decl:phi_stateProj-start
-/-- Projection from the spec's record state to the impl's anonymous 4-tuple
-accumulator. Component order matches the do-elaborator's packing of the four
-`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
-def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
-  (s.relationParts, s.prev, s.lastPart, s.stopped)
--- @decl:phi_stateProj-end
-
--- @decl:loopBody_tuple-start
-/-- The tuple-threading form of one loop iteration, read directly off
-`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
-destructured into its four components. This is what the impl's `forIn` reduces
-to under `Id`. -/
-def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
-    List Nat × Option Bool × Nat × Bool :=
-  let relationParts := acc.1
-  let prev := acc.2.1
-  let stopped := acc.2.2.2
-  if stopped then acc
-  else
-    let lastPart := step.part
-    if !step.exists_ then (relationParts, prev, lastPart, true)
-    else
-      let appendIt : Bool :=
-        match prev with
-        | none => true
-        | some pr =>
-            pr && !step.inParents && !step.isAutoField &&
-              (!step.modelHasAutoField || !step.partInPrevToFields)
-      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
-      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
-      else (relationParts, some step.isRelation, lastPart, false)
--- @decl:loopBody_tuple-end
-
--- @ns:forIn_to_foldl-start
--- @decl:forIn_to_foldl-start
-/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
-over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
-tuple init. -/
-theorem forIn_to_foldl (steps : List PathStep) :
-    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
-        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
-      = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  simp only [Id.run, List.forIn_yield_eq_foldl]
--- @decl:forIn_to_foldl-end
--- @ns:forIn_to_foldl-end
-
--- @ns:step_correspondence-start
--- @decl:step_correspondence-start
-/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
-result equals applying the tuple loop body to the projected state. -/
-theorem step_correspondence (s : LoopState) (step : PathStep) :
-    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
-  cases s with
-  | mk relationParts prev lastPart stopped =>
-    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
-    repeat' (first | rfl | simp_all | split)
--- @decl:step_correspondence-end
--- @ns:step_correspondence-end
-
--- @ns:runLoop_proj_eq-start
--- @decl:runLoop_proj_eq-start
-/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
-tuple foldl from the tuple init. -/
-theorem runLoop_proj_eq (steps : List PathStep) :
-    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  unfold runLoop
-  have key : ∀ (l : List PathStep) (s : LoopState),
-      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
-    intro l
-    induction l with
-    | nil => intro s; rfl
-    | cons a t ih =>
-      intro s
-      simp only [List.foldl_cons]
-      rw [ih (stepFold s a), step_correspondence]
-  exact key steps _
--- @decl:runLoop_proj_eq-end
--- @ns:runLoop_proj_eq-end
-
--- @ns:impl_loopBridge-start
--- @decl:impl_loopBridge-start
-/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
-— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
-tuple accumulator, and its post-loop tail decision — equals the closed
-`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
-decision read off the tuple components. This isolates the monad/do-elaboration
-reduction (prove by exposing the always-`yield` `forIn` and applying the
-`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
-theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
-    (fkeyAllowed : Bool) :
-    implementation_lookupAllowed steps validLookups fkeyAllowed
-      = (if fkeyAllowed then true
-         else
-           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
-           if acc.1.length ≤ 1 then true
-           else validLookups.contains acc.1 ||
-                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
-  unfold implementation_lookupAllowed
-  split
-  · rfl
-  · simp only [Id.run, bind, pure]
-    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
-    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
-    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
-    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
-        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
-          (fun step r =>
-            if (!r.snd.snd.snd) = true then
-              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-              else
-                if
-                    (match r.snd.fst with
-                      | none => true
-                      | some pr =>
-                        pr && !step.inParents && !step.isAutoField &&
-                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
-                      true then
-                  if (!step.hasPathInfos) = true then
-                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
-                else
-                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
-            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
-          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
-             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
-      intro l
-      induction l with
-      | nil => intro lp pv rp st; rfl
-      | cons a t ih =>
-        intro lp pv rp st
-        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
-        by_cases hst : st = true
-        · subst hst
-          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
-          exact ih lp pv rp true
-        · simp only [Bool.not_eq_true] at hst
-          subst hst
-          simp only [Bool.not_false, if_true]
-          by_cases hex : a.exists_ = true
-          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
-            by_cases happ :
-                (match pv with
-                  | none => true
-                  | some pr =>
-                    pr && !a.inParents && !a.isAutoField &&
-                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
-            · simp only [happ, if_true]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv (rp ++ [a.part]) true
-            · simp only [happ, Bool.false_eq_true, if_false]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) rp false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv rp true
-          · simp only [Bool.not_eq_true] at hex
-            simp only [hex, Bool.not_false, if_true]
-            exact ih a.part pv rp true
-    generalize hR : (forIn steps _ _ : Id _) = R
-    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
-                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
-      hR.symm.trans (key steps 0 none [] false)
-    rw [hkey]
--- @decl:impl_loopBridge-end
--- @ns:impl_loopBridge-end
-
--- @ns:tail_match-start
--- @decl:tail_match-start
-/-- DecisionTail: the post-loop decision computed from the projected tuple
-components equals the decision computed from the record's fields. -/
-theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
-    (if (phi_stateProj st).1.length ≤ 1 then true
-     else validLookups.contains (phi_stateProj st).1 ||
-          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
-      = (if st.relationParts.length ≤ 1 then true
-         else validLookups.contains st.relationParts ||
-              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
--- @decl:tail_match-end
--- @ns:tail_match-end
-
-
 theorem correct_lookupAllowed :
     ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
       problem_spec_lookupAllowed steps validLookups fkeyAllowed
         (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
   intro steps validLookups fkeyAllowed
-  unfold problem_spec_lookupAllowed
-  rw [impl_loopBridge]
-  by_cases h : fkeyAllowed
-  · simp [h, lookupDecision]
-  · simp only [h, if_false]
-    rw [← runLoop_proj_eq]
-    unfold lookupDecision
-    simp only [h, if_false]
-    exact tail_match validLookups (runLoop steps)
+  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision runLoop stepFold continuesLocal
+  simp only [Id.run, List.forIn_yield_eq_foldl]
+  induction steps with
+  | nil => simp_all
+  | cons h t ih => simp_all <;> (try rfl) <;> (repeat' (first | rfl | simp_all | split))
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,213 +176,21 @@
             stopped := true
           else
             prev := some step.isRelation
-    if relationParts.length ≤ 1 then
+    if relationParts.length < 1 then
       return true
     return (validLookups.contains relationParts) ||
            (validLookups.contains (relationParts ++ [lastPart]))
 -- impl-end
 
 -- proof-start
--- @decl:phi_stateProj-start
-/-- Projection from the spec's record state to the impl's anonymous 4-tuple
-accumulator. Component order matches the do-elaborator's packing of the four
-`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
-def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
-  (s.relationParts, s.prev, s.lastPart, s.stopped)
--- @decl:phi_stateProj-end
-
--- @decl:loopBody_tuple-start
-/-- The tuple-threading form of one loop iteration, read directly off
-`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
-destructured into its four components. This is what the impl's `forIn` reduces
-to under `Id`. -/
-def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
-    List Nat × Option Bool × Nat × Bool :=
-  let relationParts := acc.1
-  let prev := acc.2.1
-  let stopped := acc.2.2.2
-  if stopped then acc
-  else
-    let lastPart := step.part
-    if !step.exists_ then (relationParts, prev, lastPart, true)
-    else
-      let appendIt : Bool :=
-        match prev with
-        | none => true
-        | some pr =>
-            pr && !step.inParents && !step.isAutoField &&
-              (!step.modelHasAutoField || !step.partInPrevToFields)
-      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
-      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
-      else (relationParts, some step.isRelation, lastPart, false)
--- @decl:loopBody_tuple-end
-
--- @ns:forIn_to_foldl-start
--- @decl:forIn_to_foldl-start
-/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
-over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
-tuple init. -/
-theorem forIn_to_foldl (steps : List PathStep) :
-    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
-        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
-      = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  simp only [Id.run, List.forIn_yield_eq_foldl]
--- @decl:forIn_to_foldl-end
--- @ns:forIn_to_foldl-end
-
--- @ns:step_correspondence-start
--- @decl:step_correspondence-start
-/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
-result equals applying the tuple loop body to the projected state. -/
-theorem step_correspondence (s : LoopState) (step : PathStep) :
-    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
-  cases s with
-  | mk relationParts prev lastPart stopped =>
-    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
-    repeat' (first | rfl | simp_all | split)
--- @decl:step_correspondence-end
--- @ns:step_correspondence-end
-
--- @ns:runLoop_proj_eq-start
--- @decl:runLoop_proj_eq-start
-/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
-tuple foldl from the tuple init. -/
-theorem runLoop_proj_eq (steps : List PathStep) :
-    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  unfold runLoop
-  have key : ∀ (l : List PathStep) (s : LoopState),
-      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
-    intro l
-    induction l with
-    | nil => intro s; rfl
-    | cons a t ih =>
-      intro s
-      simp only [List.foldl_cons]
-      rw [ih (stepFold s a), step_correspondence]
-  exact key steps _
--- @decl:runLoop_proj_eq-end
--- @ns:runLoop_proj_eq-end
-
--- @ns:impl_loopBridge-start
--- @decl:impl_loopBridge-start
-/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
-— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
-tuple accumulator, and its post-loop tail decision — equals the closed
-`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
-decision read off the tuple components. This isolates the monad/do-elaboration
-reduction (prove by exposing the always-`yield` `forIn` and applying the
-`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
-theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
-    (fkeyAllowed : Bool) :
-    implementation_lookupAllowed steps validLookups fkeyAllowed
-      = (if fkeyAllowed then true
-         else
-           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
-           if acc.1.length ≤ 1 then true
-           else validLookups.contains acc.1 ||
-                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
-  unfold implementation_lookupAllowed
-  split
-  · rfl
-  · simp only [Id.run, bind, pure]
-    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
-    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
-    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
-    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
-        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
-          (fun step r =>
-            if (!r.snd.snd.snd) = true then
-              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-              else
-                if
-                    (match r.snd.fst with
-                      | none => true
-                      | some pr =>
-                        pr && !step.inParents && !step.isAutoField &&
-                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
-                      true then
-                  if (!step.hasPathInfos) = true then
-                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
-                else
-                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
-            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
-          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
-             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
-      intro l
-      induction l with
-      | nil => intro lp pv rp st; rfl
-      | cons a t ih =>
-        intro lp pv rp st
-        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
-        by_cases hst : st = true
-        · subst hst
-          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
-          exact ih lp pv rp true
-        · simp only [Bool.not_eq_true] at hst
-          subst hst
-          simp only [Bool.not_false, if_true]
-          by_cases hex : a.exists_ = true
-          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
-            by_cases happ :
-                (match pv with
-                  | none => true
-                  | some pr =>
-                    pr && !a.inParents && !a.isAutoField &&
-                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
-            · simp only [happ, if_true]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv (rp ++ [a.part]) true
-            · simp only [happ, Bool.false_eq_true, if_false]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) rp false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv rp true
-          · simp only [Bool.not_eq_true] at hex
-            simp only [hex, Bool.not_false, if_true]
-            exact ih a.part pv rp true
-    generalize hR : (forIn steps _ _ : Id _) = R
-    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
-                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
-      hR.symm.trans (key steps 0 none [] false)
-    rw [hkey]
--- @decl:impl_loopBridge-end
--- @ns:impl_loopBridge-end
-
--- @ns:tail_match-start
--- @decl:tail_match-start
-/-- DecisionTail: the post-loop decision computed from the projected tuple
-components equals the decision computed from the record's fields. -/
-theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
-    (if (phi_stateProj st).1.length ≤ 1 then true
-     else validLookups.contains (phi_stateProj st).1 ||
-          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
-      = (if st.relationParts.length ≤ 1 then true
-         else validLookups.contains st.relationParts ||
-              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
--- @decl:tail_match-end
--- @ns:tail_match-end
-
-
 theorem correct_lookupAllowed :
     ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
       problem_spec_lookupAllowed steps validLookups fkeyAllowed
         (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
   intro steps validLookups fkeyAllowed
-  unfold problem_spec_lookupAllowed
-  rw [impl_loopBridge]
-  by_cases h : fkeyAllowed
-  · simp [h, lookupDecision]
-  · simp only [h, if_false]
-    rw [← runLoop_proj_eq]
-    unfold lookupDecision
-    simp only [h, if_false]
-    exact tail_match validLookups (runLoop steps)
+  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision runLoop stepFold continuesLocal
+  simp only [Id.run, List.forIn_yield_eq_foldl]
+  induction steps with
+  | nil => simp_all
+  | cons h t ih => simp_all <;> (try rfl) <;> (repeat' (first | rfl | simp_all | split))
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -172,10 +172,7 @@
                   (!step.modelHasAutoField || !step.partInPrevToFields)
           if appendIt then
             relationParts := relationParts ++ [step.part]
-          if !step.hasPathInfos then
-            stopped := true
-          else
-            prev := some step.isRelation
+          prev := some step.isRelation
     if relationParts.length ≤ 1 then
       return true
     return (validLookups.contains relationParts) ||
@@ -183,206 +180,14 @@
 -- impl-end
 
 -- proof-start
--- @decl:phi_stateProj-start
-/-- Projection from the spec's record state to the impl's anonymous 4-tuple
-accumulator. Component order matches the do-elaborator's packing of the four
-`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
-def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
-  (s.relationParts, s.prev, s.lastPart, s.stopped)
--- @decl:phi_stateProj-end
-
--- @decl:loopBody_tuple-start
-/-- The tuple-threading form of one loop iteration, read directly off
-`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
-destructured into its four components. This is what the impl's `forIn` reduces
-to under `Id`. -/
-def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
-    List Nat × Option Bool × Nat × Bool :=
-  let relationParts := acc.1
-  let prev := acc.2.1
-  let stopped := acc.2.2.2
-  if stopped then acc
-  else
-    let lastPart := step.part
-    if !step.exists_ then (relationParts, prev, lastPart, true)
-    else
-      let appendIt : Bool :=
-        match prev with
-        | none => true
-        | some pr =>
-            pr && !step.inParents && !step.isAutoField &&
-              (!step.modelHasAutoField || !step.partInPrevToFields)
-      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
-      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
-      else (relationParts, some step.isRelation, lastPart, false)
--- @decl:loopBody_tuple-end
-
--- @ns:forIn_to_foldl-start
--- @decl:forIn_to_foldl-start
-/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
-over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
-tuple init. -/
-theorem forIn_to_foldl (steps : List PathStep) :
-    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
-        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
-      = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  simp only [Id.run, List.forIn_yield_eq_foldl]
--- @decl:forIn_to_foldl-end
--- @ns:forIn_to_foldl-end
-
--- @ns:step_correspondence-start
--- @decl:step_correspondence-start
-/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
-result equals applying the tuple loop body to the projected state. -/
-theorem step_correspondence (s : LoopState) (step : PathStep) :
-    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
-  cases s with
-  | mk relationParts prev lastPart stopped =>
-    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
-    repeat' (first | rfl | simp_all | split)
--- @decl:step_correspondence-end
--- @ns:step_correspondence-end
-
--- @ns:runLoop_proj_eq-start
--- @decl:runLoop_proj_eq-start
-/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
-tuple foldl from the tuple init. -/
-theorem runLoop_proj_eq (steps : List PathStep) :
-    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  unfold runLoop
-  have key : ∀ (l : List PathStep) (s : LoopState),
-      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
-    intro l
-    induction l with
-    | nil => intro s; rfl
-    | cons a t ih =>
-      intro s
-      simp only [List.foldl_cons]
-      rw [ih (stepFold s a), step_correspondence]
-  exact key steps _
--- @decl:runLoop_proj_eq-end
--- @ns:runLoop_proj_eq-end
-
--- @ns:impl_loopBridge-start
--- @decl:impl_loopBridge-start
-/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
-— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
-tuple accumulator, and its post-loop tail decision — equals the closed
-`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
-decision read off the tuple components. This isolates the monad/do-elaboration
-reduction (prove by exposing the always-`yield` `forIn` and applying the
-`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
-theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
-    (fkeyAllowed : Bool) :
-    implementation_lookupAllowed steps validLookups fkeyAllowed
-      = (if fkeyAllowed then true
-         else
-           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
-           if acc.1.length ≤ 1 then true
-           else validLookups.contains acc.1 ||
-                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
-  unfold implementation_lookupAllowed
-  split
-  · rfl
-  · simp only [Id.run, bind, pure]
-    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
-    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
-    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
-    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
-        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
-          (fun step r =>
-            if (!r.snd.snd.snd) = true then
-              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-              else
-                if
-                    (match r.snd.fst with
-                      | none => true
-                      | some pr =>
-                        pr && !step.inParents && !step.isAutoField &&
-                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
-                      true then
-                  if (!step.hasPathInfos) = true then
-                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
-                else
-                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
-            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
-          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
-             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
-      intro l
-      induction l with
-      | nil => intro lp pv rp st; rfl
-      | cons a t ih =>
-        intro lp pv rp st
-        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
-        by_cases hst : st = true
-        · subst hst
-          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
-          exact ih lp pv rp true
-        · simp only [Bool.not_eq_true] at hst
-          subst hst
-          simp only [Bool.not_false, if_true]
-          by_cases hex : a.exists_ = true
-          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
-            by_cases happ :
-                (match pv with
-                  | none => true
-                  | some pr =>
-                    pr && !a.inParents && !a.isAutoField &&
-                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
-            · simp only [happ, if_true]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv (rp ++ [a.part]) true
-            · simp only [happ, Bool.false_eq_true, if_false]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) rp false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv rp true
-          · simp only [Bool.not_eq_true] at hex
-            simp only [hex, Bool.not_false, if_true]
-            exact ih a.part pv rp true
-    generalize hR : (forIn steps _ _ : Id _) = R
-    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
-                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
-      hR.symm.trans (key steps 0 none [] false)
-    rw [hkey]
--- @decl:impl_loopBridge-end
--- @ns:impl_loopBridge-end
-
--- @ns:tail_match-start
--- @decl:tail_match-start
-/-- DecisionTail: the post-loop decision computed from the projected tuple
-components equals the decision computed from the record's fields. -/
-theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
-    (if (phi_stateProj st).1.length ≤ 1 then true
-     else validLookups.contains (phi_stateProj st).1 ||
-          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
-      = (if st.relationParts.length ≤ 1 then true
-         else validLookups.contains st.relationParts ||
-              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
--- @decl:tail_match-end
--- @ns:tail_match-end
-
-
 theorem correct_lookupAllowed :
     ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
       problem_spec_lookupAllowed steps validLookups fkeyAllowed
         (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
   intro steps validLookups fkeyAllowed
-  unfold problem_spec_lookupAllowed
-  rw [impl_loopBridge]
-  by_cases h : fkeyAllowed
-  · simp [h, lookupDecision]
-  · simp only [h, if_false]
-    rw [← runLoop_proj_eq]
-    unfold lookupDecision
-    simp only [h, if_false]
-    exact tail_match validLookups (runLoop steps)
+  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision runLoop stepFold continuesLocal
+  simp only [Id.run, List.forIn_yield_eq_foldl]
+  induction steps with
+  | nil => simp_all
+  | cons h t ih => simp_all <;> (try rfl) <;> (repeat' (first | rfl | simp_all | split))
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -151,238 +151,18 @@
 -- impl-start
 def implementation_lookupAllowed
     (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool) : Bool :=
-  Id.run do
-    if fkeyAllowed then
-      return true
-    let mut relationParts : List Nat := []
-    let mut prev : Option Bool := none
-    let mut lastPart : Nat := 0
-    let mut stopped : Bool := false
-    for step in steps do
-      if !stopped then
-        lastPart := step.part
-        if !step.exists_ then
-          stopped := true
-        else
-          let appendIt : Bool :=
-            match prev with
-            | none => true
-            | some pr =>
-                pr && !step.inParents && !step.isAutoField &&
-                  (!step.modelHasAutoField || !step.partInPrevToFields)
-          if appendIt then
-            relationParts := relationParts ++ [step.part]
-          if !step.hasPathInfos then
-            stopped := true
-          else
-            prev := some step.isRelation
-    if relationParts.length ≤ 1 then
-      return true
-    return (validLookups.contains relationParts) ||
-           (validLookups.contains (relationParts ++ [lastPart]))
+  true
 -- impl-end
 
 -- proof-start
--- @decl:phi_stateProj-start
-/-- Projection from the spec's record state to the impl's anonymous 4-tuple
-accumulator. Component order matches the do-elaborator's packing of the four
-`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
-def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
-  (s.relationParts, s.prev, s.lastPart, s.stopped)
--- @decl:phi_stateProj-end
-
--- @decl:loopBody_tuple-start
-/-- The tuple-threading form of one loop iteration, read directly off
-`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
-destructured into its four components. This is what the impl's `forIn` reduces
-to under `Id`. -/
-def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
-    List Nat × Option Bool × Nat × Bool :=
-  let relationParts := acc.1
-  let prev := acc.2.1
-  let stopped := acc.2.2.2
-  if stopped then acc
-  else
-    let lastPart := step.part
-    if !step.exists_ then (relationParts, prev, lastPart, true)
-    else
-      let appendIt : Bool :=
-        match prev with
-        | none => true
-        | some pr =>
-            pr && !step.inParents && !step.isAutoField &&
-              (!step.modelHasAutoField || !step.partInPrevToFields)
-      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
-      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
-      else (relationParts, some step.isRelation, lastPart, false)
--- @decl:loopBody_tuple-end
-
--- @ns:forIn_to_foldl-start
--- @decl:forIn_to_foldl-start
-/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
-over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
-tuple init. -/
-theorem forIn_to_foldl (steps : List PathStep) :
-    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
-        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
-      = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  simp only [Id.run, List.forIn_yield_eq_foldl]
--- @decl:forIn_to_foldl-end
--- @ns:forIn_to_foldl-end
-
--- @ns:step_correspondence-start
--- @decl:step_correspondence-start
-/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
-result equals applying the tuple loop body to the projected state. -/
-theorem step_correspondence (s : LoopState) (step : PathStep) :
-    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
-  cases s with
-  | mk relationParts prev lastPart stopped =>
-    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
-    repeat' (first | rfl | simp_all | split)
--- @decl:step_correspondence-end
--- @ns:step_correspondence-end
-
--- @ns:runLoop_proj_eq-start
--- @decl:runLoop_proj_eq-start
-/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
-tuple foldl from the tuple init. -/
-theorem runLoop_proj_eq (steps : List PathStep) :
-    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  unfold runLoop
-  have key : ∀ (l : List PathStep) (s : LoopState),
-      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
-    intro l
-    induction l with
-    | nil => intro s; rfl
-    | cons a t ih =>
-      intro s
-      simp only [List.foldl_cons]
-      rw [ih (stepFold s a), step_correspondence]
-  exact key steps _
--- @decl:runLoop_proj_eq-end
--- @ns:runLoop_proj_eq-end
-
--- @ns:impl_loopBridge-start
--- @decl:impl_loopBridge-start
-/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
-— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
-tuple accumulator, and its post-loop tail decision — equals the closed
-`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
-decision read off the tuple components. This isolates the monad/do-elaboration
-reduction (prove by exposing the always-`yield` `forIn` and applying the
-`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
-theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
-    (fkeyAllowed : Bool) :
-    implementation_lookupAllowed steps validLookups fkeyAllowed
-      = (if fkeyAllowed then true
-         else
-           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
-           if acc.1.length ≤ 1 then true
-           else validLookups.contains acc.1 ||
-                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
-  unfold implementation_lookupAllowed
-  split
-  · rfl
-  · simp only [Id.run, bind, pure]
-    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
-    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
-    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
-    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
-        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
-          (fun step r =>
-            if (!r.snd.snd.snd) = true then
-              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-              else
-                if
-                    (match r.snd.fst with
-                      | none => true
-                      | some pr =>
-                        pr && !step.inParents && !step.isAutoField &&
-                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
-                      true then
-                  if (!step.hasPathInfos) = true then
-                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
-                else
-                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
-            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
-          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
-             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
-      intro l
-      induction l with
-      | nil => intro lp pv rp st; rfl
-      | cons a t ih =>
-        intro lp pv rp st
-        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
-        by_cases hst : st = true
-        · subst hst
-          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
-          exact ih lp pv rp true
-        · simp only [Bool.not_eq_true] at hst
-          subst hst
-          simp only [Bool.not_false, if_true]
-          by_cases hex : a.exists_ = true
-          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
-            by_cases happ :
-                (match pv with
-                  | none => true
-                  | some pr =>
-                    pr && !a.inParents && !a.isAutoField &&
-                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
-            · simp only [happ, if_true]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv (rp ++ [a.part]) true
-            · simp only [happ, Bool.false_eq_true, if_false]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) rp false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv rp true
-          · simp only [Bool.not_eq_true] at hex
-            simp only [hex, Bool.not_false, if_true]
-            exact ih a.part pv rp true
-    generalize hR : (forIn steps _ _ : Id _) = R
-    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
-                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
-      hR.symm.trans (key steps 0 none [] false)
-    rw [hkey]
--- @decl:impl_loopBridge-end
--- @ns:impl_loopBridge-end
-
--- @ns:tail_match-start
--- @decl:tail_match-start
-/-- DecisionTail: the post-loop decision computed from the projected tuple
-components equals the decision computed from the record's fields. -/
-theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
-    (if (phi_stateProj st).1.length ≤ 1 then true
-     else validLookups.contains (phi_stateProj st).1 ||
-          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
-      = (if st.relationParts.length ≤ 1 then true
-         else validLookups.contains st.relationParts ||
-              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
--- @decl:tail_match-end
--- @ns:tail_match-end
-
-
 theorem correct_lookupAllowed :
     ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
       problem_spec_lookupAllowed steps validLookups fkeyAllowed
         (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
   intro steps validLookups fkeyAllowed
-  unfold problem_spec_lookupAllowed
-  rw [impl_loopBridge]
-  by_cases h : fkeyAllowed
-  · simp [h, lookupDecision]
-  · simp only [h, if_false]
-    rw [← runLoop_proj_eq]
-    unfold lookupDecision
-    simp only [h, if_false]
-    exact tail_match validLookups (runLoop steps)
+  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision runLoop stepFold continuesLocal
+  simp only [Id.run, List.forIn_yield_eq_foldl]
+  induction steps with
+  | nil => simp_all
+  | cons h t ih => simp_all <;> (try rfl) <;> (repeat' (first | rfl | simp_all | split))
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -178,211 +178,19 @@
             prev := some step.isRelation
     if relationParts.length ≤ 1 then
       return true
-    return (validLookups.contains relationParts) ||
+    return (validLookups.contains relationParts) &&
            (validLookups.contains (relationParts ++ [lastPart]))
 -- impl-end
 
 -- proof-start
--- @decl:phi_stateProj-start
-/-- Projection from the spec's record state to the impl's anonymous 4-tuple
-accumulator. Component order matches the do-elaborator's packing of the four
-`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
-def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
-  (s.relationParts, s.prev, s.lastPart, s.stopped)
--- @decl:phi_stateProj-end
-
--- @decl:loopBody_tuple-start
-/-- The tuple-threading form of one loop iteration, read directly off
-`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
-destructured into its four components. This is what the impl's `forIn` reduces
-to under `Id`. -/
-def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
-    List Nat × Option Bool × Nat × Bool :=
-  let relationParts := acc.1
-  let prev := acc.2.1
-  let stopped := acc.2.2.2
-  if stopped then acc
-  else
-    let lastPart := step.part
-    if !step.exists_ then (relationParts, prev, lastPart, true)
-    else
-      let appendIt : Bool :=
-        match prev with
-        | none => true
-        | some pr =>
-            pr && !step.inParents && !step.isAutoField &&
-              (!step.modelHasAutoField || !step.partInPrevToFields)
-      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
-      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
-      else (relationParts, some step.isRelation, lastPart, false)
--- @decl:loopBody_tuple-end
-
--- @ns:forIn_to_foldl-start
--- @decl:forIn_to_foldl-start
-/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
-over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
-tuple init. -/
-theorem forIn_to_foldl (steps : List PathStep) :
-    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
-        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
-      = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  simp only [Id.run, List.forIn_yield_eq_foldl]
--- @decl:forIn_to_foldl-end
--- @ns:forIn_to_foldl-end
-
--- @ns:step_correspondence-start
--- @decl:step_correspondence-start
-/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
-result equals applying the tuple loop body to the projected state. -/
-theorem step_correspondence (s : LoopState) (step : PathStep) :
-    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
-  cases s with
-  | mk relationParts prev lastPart stopped =>
-    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
-    repeat' (first | rfl | simp_all | split)
--- @decl:step_correspondence-end
--- @ns:step_correspondence-end
-
--- @ns:runLoop_proj_eq-start
--- @decl:runLoop_proj_eq-start
-/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
-tuple foldl from the tuple init. -/
-theorem runLoop_proj_eq (steps : List PathStep) :
-    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  unfold runLoop
-  have key : ∀ (l : List PathStep) (s : LoopState),
-      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
-    intro l
-    induction l with
-    | nil => intro s; rfl
-    | cons a t ih =>
-      intro s
-      simp only [List.foldl_cons]
-      rw [ih (stepFold s a), step_correspondence]
-  exact key steps _
--- @decl:runLoop_proj_eq-end
--- @ns:runLoop_proj_eq-end
-
--- @ns:impl_loopBridge-start
--- @decl:impl_loopBridge-start
-/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
-— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
-tuple accumulator, and its post-loop tail decision — equals the closed
-`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
-decision read off the tuple components. This isolates the monad/do-elaboration
-reduction (prove by exposing the always-`yield` `forIn` and applying the
-`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
-theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
-    (fkeyAllowed : Bool) :
-    implementation_lookupAllowed steps validLookups fkeyAllowed
-      = (if fkeyAllowed then true
-         else
-           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
-           if acc.1.length ≤ 1 then true
-           else validLookups.contains acc.1 ||
-                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
-  unfold implementation_lookupAllowed
-  split
-  · rfl
-  · simp only [Id.run, bind, pure]
-    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
-    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
-    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
-    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
-        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
-          (fun step r =>
-            if (!r.snd.snd.snd) = true then
-              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-              else
-                if
-                    (match r.snd.fst with
-                      | none => true
-                      | some pr =>
-                        pr && !step.inParents && !step.isAutoField &&
-                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
-                      true then
-                  if (!step.hasPathInfos) = true then
-                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
-                else
-                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
-            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
-          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
-             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
-      intro l
-      induction l with
-      | nil => intro lp pv rp st; rfl
-      | cons a t ih =>
-        intro lp pv rp st
-        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
-        by_cases hst : st = true
-        · subst hst
-          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
-          exact ih lp pv rp true
-        · simp only [Bool.not_eq_true] at hst
-          subst hst
-          simp only [Bool.not_false, if_true]
-          by_cases hex : a.exists_ = true
-          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
-            by_cases happ :
-                (match pv with
-                  | none => true
-                  | some pr =>
-                    pr && !a.inParents && !a.isAutoField &&
-                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
-            · simp only [happ, if_true]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv (rp ++ [a.part]) true
-            · simp only [happ, Bool.false_eq_true, if_false]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) rp false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv rp true
-          · simp only [Bool.not_eq_true] at hex
-            simp only [hex, Bool.not_false, if_true]
-            exact ih a.part pv rp true
-    generalize hR : (forIn steps _ _ : Id _) = R
-    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
-                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
-      hR.symm.trans (key steps 0 none [] false)
-    rw [hkey]
--- @decl:impl_loopBridge-end
--- @ns:impl_loopBridge-end
-
--- @ns:tail_match-start
--- @decl:tail_match-start
-/-- DecisionTail: the post-loop decision computed from the projected tuple
-components equals the decision computed from the record's fields. -/
-theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
-    (if (phi_stateProj st).1.length ≤ 1 then true
-     else validLookups.contains (phi_stateProj st).1 ||
-          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
-      = (if st.relationParts.length ≤ 1 then true
-         else validLookups.contains st.relationParts ||
-              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
--- @decl:tail_match-end
--- @ns:tail_match-end
-
-
 theorem correct_lookupAllowed :
     ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
       problem_spec_lookupAllowed steps validLookups fkeyAllowed
         (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
   intro steps validLookups fkeyAllowed
-  unfold problem_spec_lookupAllowed
-  rw [impl_loopBridge]
-  by_cases h : fkeyAllowed
-  · simp [h, lookupDecision]
-  · simp only [h, if_false]
-    rw [← runLoop_proj_eq]
-    unfold lookupDecision
-    simp only [h, if_false]
-    exact tail_match validLookups (runLoop steps)
+  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision runLoop stepFold continuesLocal
+  simp only [Id.run, List.forIn_yield_eq_foldl]
+  induction steps with
+  | nil => simp_all
+  | cons h t ih => simp_all <;> (try rfl) <;> (repeat' (first | rfl | simp_all | split))
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -171,7 +171,7 @@
                 pr && !step.inParents && !step.isAutoField &&
                   (!step.modelHasAutoField || !step.partInPrevToFields)
           if appendIt then
-            relationParts := relationParts ++ [step.part]
+            relationParts := [step.part] ++ relationParts
           if !step.hasPathInfos then
             stopped := true
           else
@@ -183,206 +183,14 @@
 -- impl-end
 
 -- proof-start
--- @decl:phi_stateProj-start
-/-- Projection from the spec's record state to the impl's anonymous 4-tuple
-accumulator. Component order matches the do-elaborator's packing of the four
-`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
-def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
-  (s.relationParts, s.prev, s.lastPart, s.stopped)
--- @decl:phi_stateProj-end
-
--- @decl:loopBody_tuple-start
-/-- The tuple-threading form of one loop iteration, read directly off
-`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
-destructured into its four components. This is what the impl's `forIn` reduces
-to under `Id`. -/
-def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
-    List Nat × Option Bool × Nat × Bool :=
-  let relationParts := acc.1
-  let prev := acc.2.1
-  let stopped := acc.2.2.2
-  if stopped then acc
-  else
-    let lastPart := step.part
-    if !step.exists_ then (relationParts, prev, lastPart, true)
-    else
-      let appendIt : Bool :=
-        match prev with
-        | none => true
-        | some pr =>
-            pr && !step.inParents && !step.isAutoField &&
-              (!step.modelHasAutoField || !step.partInPrevToFields)
-      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
-      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
-      else (relationParts, some step.isRelation, lastPart, false)
--- @decl:loopBody_tuple-end
-
--- @ns:forIn_to_foldl-start
--- @decl:forIn_to_foldl-start
-/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
-over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
-tuple init. -/
-theorem forIn_to_foldl (steps : List PathStep) :
-    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
-        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
-      = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  simp only [Id.run, List.forIn_yield_eq_foldl]
--- @decl:forIn_to_foldl-end
--- @ns:forIn_to_foldl-end
-
--- @ns:step_correspondence-start
--- @decl:step_correspondence-start
-/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
-result equals applying the tuple loop body to the projected state. -/
-theorem step_correspondence (s : LoopState) (step : PathStep) :
-    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
-  cases s with
-  | mk relationParts prev lastPart stopped =>
-    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
-    repeat' (first | rfl | simp_all | split)
--- @decl:step_correspondence-end
--- @ns:step_correspondence-end
-
--- @ns:runLoop_proj_eq-start
--- @decl:runLoop_proj_eq-start
-/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
-tuple foldl from the tuple init. -/
-theorem runLoop_proj_eq (steps : List PathStep) :
-    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
-  unfold runLoop
-  have key : ∀ (l : List PathStep) (s : LoopState),
-      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
-    intro l
-    induction l with
-    | nil => intro s; rfl
-    | cons a t ih =>
-      intro s
-      simp only [List.foldl_cons]
-      rw [ih (stepFold s a), step_correspondence]
-  exact key steps _
--- @decl:runLoop_proj_eq-end
--- @ns:runLoop_proj_eq-end
-
--- @ns:impl_loopBridge-start
--- @decl:impl_loopBridge-start
-/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
-— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
-tuple accumulator, and its post-loop tail decision — equals the closed
-`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
-decision read off the tuple components. This isolates the monad/do-elaboration
-reduction (prove by exposing the always-`yield` `forIn` and applying the
-`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
-theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
-    (fkeyAllowed : Bool) :
-    implementation_lookupAllowed steps validLookups fkeyAllowed
-      = (if fkeyAllowed then true
-         else
-           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
-           if acc.1.length ≤ 1 then true
-           else validLookups.contains acc.1 ||
-                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
-  unfold implementation_lookupAllowed
-  split
-  · rfl
-  · simp only [Id.run, bind, pure]
-    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
-    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
-    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
-    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
-        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
-          (fun step r =>
-            if (!r.snd.snd.snd) = true then
-              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-              else
-                if
-                    (match r.snd.fst with
-                      | none => true
-                      | some pr =>
-                        pr && !step.inParents && !step.isAutoField &&
-                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
-                      true then
-                  if (!step.hasPathInfos) = true then
-                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
-                else
-                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
-                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
-            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
-          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
-             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
-      intro l
-      induction l with
-      | nil => intro lp pv rp st; rfl
-      | cons a t ih =>
-        intro lp pv rp st
-        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
-        by_cases hst : st = true
-        · subst hst
-          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
-          exact ih lp pv rp true
-        · simp only [Bool.not_eq_true] at hst
-          subst hst
-          simp only [Bool.not_false, if_true]
-          by_cases hex : a.exists_ = true
-          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
-            by_cases happ :
-                (match pv with
-                  | none => true
-                  | some pr =>
-                    pr && !a.inParents && !a.isAutoField &&
-                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
-            · simp only [happ, if_true]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv (rp ++ [a.part]) true
-            · simp only [happ, Bool.false_eq_true, if_false]
-              by_cases hpath : a.hasPathInfos = true
-              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
-                exact ih a.part (some a.isRelation) rp false
-              · simp only [Bool.not_eq_true] at hpath
-                simp only [hpath, Bool.not_false, if_true]
-                exact ih a.part pv rp true
-          · simp only [Bool.not_eq_true] at hex
-            simp only [hex, Bool.not_false, if_true]
-            exact ih a.part pv rp true
-    generalize hR : (forIn steps _ _ : Id _) = R
-    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
-                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
-      hR.symm.trans (key steps 0 none [] false)
-    rw [hkey]
--- @decl:impl_loopBridge-end
--- @ns:impl_loopBridge-end
-
--- @ns:tail_match-start
--- @decl:tail_match-start
-/-- DecisionTail: the post-loop decision computed from the projected tuple
-components equals the decision computed from the record's fields. -/
-theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
-    (if (phi_stateProj st).1.length ≤ 1 then true
-     else validLookups.contains (phi_stateProj st).1 ||
-          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
-      = (if st.relationParts.length ≤ 1 then true
-         else validLookups.contains st.relationParts ||
-              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
--- @decl:tail_match-end
--- @ns:tail_match-end
-
-
 theorem correct_lookupAllowed :
     ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
       problem_spec_lookupAllowed steps validLookups fkeyAllowed
         (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
   intro steps validLookups fkeyAllowed
-  unfold problem_spec_lookupAllowed
-  rw [impl_loopBridge]
-  by_cases h : fkeyAllowed
-  · simp [h, lookupDecision]
-  · simp only [h, if_false]
-    rw [← runLoop_proj_eq]
-    unfold lookupDecision
-    simp only [h, if_false]
-    exact tail_match validLookups (runLoop steps)
+  unfold problem_spec_lookupAllowed implementation_lookupAllowed lookupDecision runLoop stepFold continuesLocal
+  simp only [Id.run, List.forIn_yield_eq_foldl]
+  induction steps with
+  | nil => simp_all
+  | cons h t ih => simp_all <;> (try rfl) <;> (repeat' (first | rfl | simp_all | split))
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether an admin change-list may filter on a chained relational lookup.

A lookup is a chain of components (e.g. `a__b__c`) walked left-to-right over a
model graph. Walking accumulates the subset of components that name a genuine
relational HOP — the "relation parts". A component is dropped from the relation
parts when the value it names would already be reachable from the previous
model's own local column, so that two syntactically different chains that reach
the SAME stored value are treated as one.

Three situations make the previous relation's continuation collapse into the
local model (and so the component is NOT counted as a fresh hop):

  * the field is the link that realises concrete model inheritance (a parent
    link), so the child row already carries the parent's identity locally;
  * the field IS the model's own synthesised primary key, so its value is the
    local row's identity;
  * the model has a synthesised primary key AND the component names one of the
    previous relation's target columns, so the value is already reachable from
    the previous model's local column.

Crucially, when a relation's own primary key is itself a relation to another
model (a foreign key used as the primary key), that relation is a genuine hop:
none of the three collapsing situations applies, so the component MUST stay in
the relation parts. Otherwise the chain would be shortened to a form that is not
declarable as an allowed filter.

After the walk, a chain is permitted when it resolves to at most one relation
part (a purely local filter), or when the accumulated relation parts — with or
without the final trailing component — match one of the declared allowed
filters. A separate early allowance covers foreign-key raw-id popups.

MODELING. The model graph metadata resolved at each component is abstracted to a
`PathStep` record carrying only the booleans the walk branches on (mapping.md
gives the bijection to the real field metadata). Component names are identities
(`Nat`); a chain is a `List Nat`; the declared allowed filters are a
`List (List Nat)`. Only equality of chains is observed.
-/

-- axioms-start
-- No unchanged outside callee contributes a property this specification
-- consumes. The model-graph metadata that the walk reads at each component
-- (whether the component resolves to a field, whether the previous field is a
-- relation, whether the field is a parent link / the synthesised primary key,
-- whether the model has a synthesised primary key, whether the component is one
-- of the previous relation's target columns, and whether the walk continues) is
-- abstracted as the input `PathStep` record — a structure restricted to the
-- touched fields — not axiomatised. Hence there is no `opaque`/`axiom` callee.
-- axioms-end

-- pure-start
/-- The model-graph metadata resolved at one lookup component, restricted to the
booleans the walk branches on (mapping.md gives the bijection to the real field
metadata):
* `part` — the component's name identity;
* `exists_` — the component resolves to a field on the current model;
* `isRelation` — the resolved field is itself a relation (i.e. it would be the
  "previous relation" for the next component);
* `hasPathInfos` — the resolved field continues the walk to a further model;
* `inTargetFields` — the resolved field is one of the previous relation's target
  columns;
* `inParents` — the resolved field is the link realising concrete inheritance;
* `isAutoField` — the resolved field is the current model's synthesised primary
  key;
* `modelHasAutoField` — the current model has a synthesised primary key;
* `partInPrevToFields` — this component names one of the previous relation's
  declared target columns. -/
structure PathStep where
  part : Nat
  exists_ : Bool
  isRelation : Bool
  hasPathInfos : Bool
  inTargetFields : Bool
  inParents : Bool
  isAutoField : Bool
  modelHasAutoField : Bool
  partInPrevToFields : Bool
deriving DecidableEq, Inhabited

/-- The walk's running state:
* `relationParts` — the component names counted as genuine relational hops;
* `prev` — the previous field's `isRelation`, or `none` before the first hop;
* `lastPart` — the component name reached on the final processed step;
* `stopped` — the walk has halted (component did not resolve, or a non-relational
  field ended the chain). -/
structure LoopState where
  relationParts : List Nat
  prev : Option Bool
  lastPart : Nat
  stopped : Bool
deriving DecidableEq, Inhabited

/-- Whether a resolved relational field continues the previous relation's local
column — in which case the component is folded into the local model rather than
counted as a fresh hop. None of the three collapsing situations may apply. -/
def continuesLocal (step : PathStep) : Bool :=
  !step.inParents && !step.isAutoField &&
    (!step.modelHasAutoField || !step.partInPrevToFields)

/-- Process one lookup component, updating the walk state. Once halted the state
is unchanged. Otherwise the reached component becomes `lastPart`; if it does not
resolve the walk halts; if the previous field is `none` OR the previous field is
a relation whose continuation does not fold into the local model, the component
joins the relation parts; if the field does not continue the walk it halts,
otherwise the field's relational status is carried forward. -/
def stepFold (s : LoopState) (step : PathStep) : LoopState :=
  if s.stopped then s
  else
    let s := { s with lastPart := step.part }
    if !step.exists_ then { s with stopped := true }
    else
      let appendIt : Bool :=
        match s.prev with
        | none => true
        | some pr => pr && continuesLocal step
      let s := if appendIt then { s with relationParts := s.relationParts ++ [step.part] } else s
      if !step.hasPathInfos then { s with stopped := true }
      else { s with prev := some step.isRelation }

/-- Walk the whole chain from the initial state. -/
def runLoop (steps : List PathStep) : LoopState :=
  steps.foldl stepFold { relationParts := [], prev := none, lastPart := 0, stopped := false }

/-- The full decision. `fkeyAllowed` is the early foreign-key raw-id-popup
allowance; `validLookups` is the set of declared allowed filter chains. A chain
is permitted when the early allowance fires, when it resolves to at most one
relation part, or when the accumulated relation parts — with or without the
final trailing component — match a declared allowed filter. -/
def lookupDecision (steps : List PathStep) (validLookups : List (List Nat))
    (fkeyAllowed : Bool) : Bool :=
  if fkeyAllowed then true
  else
    let st := runLoop steps
    if st.relationParts.length ≤ 1 then true
    else (validLookups.contains st.relationParts) ||
         (validLookups.contains (st.relationParts ++ [st.lastPart]))
-- pure-end

-- post-conditions-start
/-- The decision is exactly the value produced by walking the chain and matching
the accumulated relation parts against the declared allowed filters. -/
def problem_spec_lookupAllowed
    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool)
    (result : Bool) : Prop :=
  result = lookupDecision steps validLookups fkeyAllowed
-- post-conditions-end

-- impl-start
def implementation_lookupAllowed
    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool) : Bool :=
  Id.run do
    if fkeyAllowed then
      return true
    let mut relationParts : List Nat := []
    let mut prev : Option Bool := none
    let mut lastPart : Nat := 0
    let mut stopped : Bool := false
    for step in steps do
      if !stopped then
        lastPart := step.part
        if !step.exists_ then
          stopped := true
        else
          let appendIt : Bool :=
            match prev with
            | none => true
            | some pr =>
                pr && !step.inParents && !step.isAutoField &&
                  (!step.modelHasAutoField || !step.partInPrevToFields)
          if appendIt then
            relationParts := relationParts ++ [step.part]
          if !step.hasPathInfos then
            stopped := true
          else
            prev := some step.isRelation
    if relationParts.length ≤ 1 then
      return true
    return (validLookups.contains relationParts) ||
           (validLookups.contains (relationParts ++ [lastPart]))
-- impl-end

-- proof-start
-- @decl:phi_stateProj-start
/-- Projection from the spec's record state to the impl's anonymous 4-tuple
accumulator. Component order matches the do-elaborator's packing of the four
`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
  (s.relationParts, s.prev, s.lastPart, s.stopped)
-- @decl:phi_stateProj-end

-- @decl:loopBody_tuple-start
/-- The tuple-threading form of one loop iteration, read directly off
`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
destructured into its four components. This is what the impl's `forIn` reduces
to under `Id`. -/
def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
    List Nat × Option Bool × Nat × Bool :=
  let relationParts := acc.1
  let prev := acc.2.1
  let stopped := acc.2.2.2
  if stopped then acc
  else
    let lastPart := step.part
    if !step.exists_ then (relationParts, prev, lastPart, true)
    else
      let appendIt : Bool :=
        match prev with
        | none => true
        | some pr =>
            pr && !step.inParents && !step.isAutoField &&
              (!step.modelHasAutoField || !step.partInPrevToFields)
      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
      else (relationParts, some step.isRelation, lastPart, false)
-- @decl:loopBody_tuple-end

-- @ns:forIn_to_foldl-start
-- @decl:forIn_to_foldl-start
/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
tuple init. -/
theorem forIn_to_foldl (steps : List PathStep) :
    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
      = steps.foldl loopBody_tuple ([], none, 0, false) := by
  simp only [Id.run, List.forIn_yield_eq_foldl]
-- @decl:forIn_to_foldl-end
-- @ns:forIn_to_foldl-end

-- @ns:step_correspondence-start
-- @decl:step_correspondence-start
/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
result equals applying the tuple loop body to the projected state. -/
theorem step_correspondence (s : LoopState) (step : PathStep) :
    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
  cases s with
  | mk relationParts prev lastPart stopped =>
    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
    repeat' (first | rfl | simp_all | split)
-- @decl:step_correspondence-end
-- @ns:step_correspondence-end

-- @ns:runLoop_proj_eq-start
-- @decl:runLoop_proj_eq-start
/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
tuple foldl from the tuple init. -/
theorem runLoop_proj_eq (steps : List PathStep) :
    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
  unfold runLoop
  have key : ∀ (l : List PathStep) (s : LoopState),
      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
    intro l
    induction l with
    | nil => intro s; rfl
    | cons a t ih =>
      intro s
      simp only [List.foldl_cons]
      rw [ih (stepFold s a), step_correspondence]
  exact key steps _
-- @decl:runLoop_proj_eq-end
-- @ns:runLoop_proj_eq-end

-- @ns:impl_loopBridge-start
-- @decl:impl_loopBridge-start
/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
tuple accumulator, and its post-loop tail decision — equals the closed
`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
decision read off the tuple components. This isolates the monad/do-elaboration
reduction (prove by exposing the always-`yield` `forIn` and applying the
`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
    (fkeyAllowed : Bool) :
    implementation_lookupAllowed steps validLookups fkeyAllowed
      = (if fkeyAllowed then true
         else
           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
           if acc.1.length ≤ 1 then true
           else validLookups.contains acc.1 ||
                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
  unfold implementation_lookupAllowed
  split
  · rfl
  · simp only [Id.run, bind, pure]
    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
          (fun step r =>
            if (!r.snd.snd.snd) = true then
              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
              else
                if
                    (match r.snd.fst with
                      | none => true
                      | some pr =>
                        pr && !step.inParents && !step.isAutoField &&
                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
                      true then
                  if (!step.hasPathInfos) = true then
                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
                else
                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
      intro l
      induction l with
      | nil => intro lp pv rp st; rfl
      | cons a t ih =>
        intro lp pv rp st
        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
        by_cases hst : st = true
        · subst hst
          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
          exact ih lp pv rp true
        · simp only [Bool.not_eq_true] at hst
          subst hst
          simp only [Bool.not_false, if_true]
          by_cases hex : a.exists_ = true
          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
            by_cases happ :
                (match pv with
                  | none => true
                  | some pr =>
                    pr && !a.inParents && !a.isAutoField &&
                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
            · simp only [happ, if_true]
              by_cases hpath : a.hasPathInfos = true
              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
              · simp only [Bool.not_eq_true] at hpath
                simp only [hpath, Bool.not_false, if_true]
                exact ih a.part pv (rp ++ [a.part]) true
            · simp only [happ, Bool.false_eq_true, if_false]
              by_cases hpath : a.hasPathInfos = true
              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
                exact ih a.part (some a.isRelation) rp false
              · simp only [Bool.not_eq_true] at hpath
                simp only [hpath, Bool.not_false, if_true]
                exact ih a.part pv rp true
          · simp only [Bool.not_eq_true] at hex
            simp only [hex, Bool.not_false, if_true]
            exact ih a.part pv rp true
    generalize hR : (forIn steps _ _ : Id _) = R
    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
      hR.symm.trans (key steps 0 none [] false)
    rw [hkey]
-- @decl:impl_loopBridge-end
-- @ns:impl_loopBridge-end

-- @ns:tail_match-start
-- @decl:tail_match-start
/-- DecisionTail: the post-loop decision computed from the projected tuple
components equals the decision computed from the record's fields. -/
theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
    (if (phi_stateProj st).1.length ≤ 1 then true
     else validLookups.contains (phi_stateProj st).1 ||
          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
      = (if st.relationParts.length ≤ 1 then true
         else validLookups.contains st.relationParts ||
              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
-- @decl:tail_match-end
-- @ns:tail_match-end


theorem correct_lookupAllowed :
    ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
      problem_spec_lookupAllowed steps validLookups fkeyAllowed
        (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
  intro steps validLookups fkeyAllowed
  unfold problem_spec_lookupAllowed
  rw [impl_loopBridge]
  by_cases h : fkeyAllowed
  · simp [h, lookupDecision]
  · simp only [h, if_false]
    rw [← runLoop_proj_eq]
    unfold lookupDecision
    simp only [h, if_false]
    exact tail_match validLookups (runLoop steps)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Spec shape = exact-equality postcondition, NO axioms/opaque callees (A-legs audit: refinement.md declares None; grep of Solution.lean finds no axiom/opaque/sorry — only a comment). This is the tightest possible spec: verify ⇒ correct trivially, because a verifying impl must equal lookupDecision pointwise.

SAME_SPEC: all 7 attacks + pos_control return True (spec_signature identical; impl+proof regions elided by _lean_spec_view).

### COMMANDS (lean_verify.sh, 300s):
- Positive control (gold, unmodified): bash scripts/lean_verify.sh $D/pos_control.lean → exit 0 (VERIFIES).
- #print axioms correct_lookupAllowed → 'depends on axioms: [propext, Quot.sound]' — CLEAN (no sorryAx, no Classical.choice). File pos_axioms.lean, log_posax.txt.
- Disproofs disp_1..disp_7 (wrong impl kept verbatim, theorem replaced by `implementation ≠ lookupDecision W := by decide`): ALL exit 0. (decide, not native_decide — grep -c native_decide = 0 in all disp files.)
- Honest correctness attempts atk_1/5/6/7 (generic induction+simp proof against the wrong impl): ALL exit 1, 'error: unsolved goals' — genuine failure, not timeout.

STEP-2 RESOLVE: vacuously satisfied. patches={} because ZERO wrong impls have a closing clean-axiom proof; there is nothing to materialize/resolve. The equality spec leaves no gap for a verifying-but-incorrect impl.

6 DISTINCT wrong-impl classes attacked: prepatch bug (atk_1), partial-domain/dropped-conjunct (atk_2), boundary off-by-one (atk_3), control-flow-effect / dropped break (atk_4), ungrounded-oracle echo / always-true (atk_5), final-decision operator swap (atk_6), plus ordering (atk_7). All fail to verify AND are provably ≠ spec.

A-LEG AUDIT: refinement.md rows are all R or I; A-legs section = 'None' (no opaque/axiom callee). mapping.md gives a complete Python↔Lean bijection for every PathStep boolean; the changed guard (relation_parts.append guard, lines 461-469) is modeled DEEPLY via continuesLocal/stepFold, not axiomatized. No kind-3 legs. Correspondence holds; nothing to falsify on the A side because there is no A side.

prepatch_reproduced=true: atk_1 IS the Solution_prepatch.lean impl (pr && !step.inTargetFields); its honest proof fails (exit 1) and disp_1 proves it differs from lookupDecision.

VERDICT: SOUND. The exact-equality, axiom-free spec cannot be satisfied by any incorrect implementation; 7 same-spec wrong impls all machine-proven ≠ spec and all fail to verify.

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
No same-spec wrong impl admits a closing proof. The postcondition problem_spec_lookupAllowed is EXACT equality (result = lookupDecision steps validLookups fkeyAllowed) with NO axioms (refinement.md A-legs = None; grep confirms no axiom/opaque/sorry callee). Any impl that differs from lookupDecision on even one input makes correct_lookupAllowed a FALSE proposition, hence unprovable. Demonstrated concretely: for each of the 7 attacks I materialized disp_N.lean that keeps the wrong impl byte-for-byte but proves `implementation_lookupAllowed W ≠ lookupDecision W` at a concrete witness W via `decide` (NOT native_decide) — all 7 CLOSE (exit 0, clean), which machine-proves correct_lookupAllowed is false for each wrong impl. Witnesses: atk_1(prepatch bug: pr && !inTargetFields)/atk_2(dropped !inParents conjunct): steps=[⟨1,T,T,T,F,F,F,F,F⟩,⟨2,T,F,F,F,inParents=T,...⟩], VL=[], fkey=false — gold appends part 2 (inParents collapse only fires under prev.is_relation guard combos), the buggy guards diverge → relationParts differ. atk_3(len<1 vs ≤1): single appended step, len1 → gold True, atk False. atk_4(ignores hasPathInfos break): a step with hasPathInfos=F must stop the walk; atk keeps folding → extra relation part. atk_5(ungrounded oracle: always true): chain→[1,2] len2 with VL=[] → spec False. atk_6(&& instead of ||): [1,2] with VL=[[1,2]] → spec True(||) but atk requires both join-keys present → False. atk_7(prepend instead of append): order of relationParts flipped, membership in VL=[[1,2]] fails.
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
Deciding whether an admin change-list may filter on a chained relational lookup.

A lookup is a chain of components (e.g. `a__b__c`) walked left-to-right over a
model graph. Walking accumulates the subset of components that name a genuine
relational HOP — the "relation parts". A component is dropped from the relation
parts when the value it names would already be reachable from the previous
model's own local column, so that two syntactically different chains that reach
the SAME stored value are treated as one.

Three situations make the previous relation's continuation collapse into the
local model (and so the component is NOT counted as a fresh hop):

  * the field is the link that realises concrete model inheritance (a parent
    link), so the child row already carries the parent's identity locally;
  * the field IS the model's own synthesised primary key, so its value is the
    local row's identity;
  * the model has a synthesised primary key AND the component names one of the
    previous relation's target columns, so the value is already reachable from
    the previous model's local column.

Crucially, when a relation's own primary key is itself a relation to another
model (a foreign key used as the primary key), that relation is a genuine hop:
none of the three collapsing situations applies, so the component MUST stay in
the relation parts. Otherwise the chain would be shortened to a form that is not
declarable as an allowed filter.

After the walk, a chain is permitted when it resolves to at most one relation
part (a purely local filter), or when the accumulated relation parts — with or
without the final trailing component — match one of the declared allowed
filters. A separate early allowance covers foreign-key raw-id popups.

MODELING. The model graph metadata resolved at each component is abstracted to a
`PathStep` record carrying only the booleans the walk branches on (mapping.md
gives the bijection to the real field metadata). Component names are identities
(`Nat`); a chain is a `List Nat`; the declared allowed filters are a
`List (List Nat)`. Only equality of chains is observed.
-/

-- axioms-start
-- No unchanged outside callee contributes a property this specification
-- consumes. The model-graph metadata that the walk reads at each component
-- (whether the component resolves to a field, whether the previous field is a
-- relation, whether the field is a parent link / the synthesised primary key,
-- whether the model has a synthesised primary key, whether the component is one
-- of the previous relation's target columns, and whether the walk continues) is
-- abstracted as the input `PathStep` record — a structure restricted to the
-- touched fields — not axiomatised. Hence there is no `opaque`/`axiom` callee.
-- axioms-end

-- pure-start
/-- The model-graph metadata resolved at one lookup component, restricted to the
booleans the walk branches on (mapping.md gives the bijection to the real field
metadata):
* `part` — the component's name identity;
* `exists_` — the component resolves to a field on the current model;
* `isRelation` — the resolved field is itself a relation (i.e. it would be the
  "previous relation" for the next component);
* `hasPathInfos` — the resolved field continues the walk to a further model;
* `inTargetFields` — the resolved field is one of the previous relation's target
  columns;
* `inParents` — the resolved field is the link realising concrete inheritance;
* `isAutoField` — the resolved field is the current model's synthesised primary
  key;
* `modelHasAutoField` — the current model has a synthesised primary key;
* `partInPrevToFields` — this component names one of the previous relation's
  declared target columns. -/
structure PathStep where
  part : Nat
  exists_ : Bool
  isRelation : Bool
  hasPathInfos : Bool
  inTargetFields : Bool
  inParents : Bool
  isAutoField : Bool
  modelHasAutoField : Bool
  partInPrevToFields : Bool
deriving DecidableEq, Inhabited

/-- The walk's running state:
* `relationParts` — the component names counted as genuine relational hops;
* `prev` — the previous field's `isRelation`, or `none` before the first hop;
* `lastPart` — the component name reached on the final processed step;
* `stopped` — the walk has halted (component did not resolve, or a non-relational
  field ended the chain). -/
structure LoopState where
  relationParts : List Nat
  prev : Option Bool
  lastPart : Nat
  stopped : Bool
deriving DecidableEq, Inhabited

/-- Whether a resolved relational field continues the previous relation's local
column — in which case the component is folded into the local model rather than
counted as a fresh hop. None of the three collapsing situations may apply. -/
def continuesLocal (step : PathStep) : Bool :=
  !step.inParents && !step.isAutoField &&
    (!step.modelHasAutoField || !step.partInPrevToFields)

/-- Process one lookup component, updating the walk state. Once halted the state
is unchanged. Otherwise the reached component becomes `lastPart`; if it does not
resolve the walk halts; if the previous field is `none` OR the previous field is
a relation whose continuation does not fold into the local model, the component
joins the relation parts; if the field does not continue the walk it halts,
otherwise the field's relational status is carried forward. -/
def stepFold (s : LoopState) (step : PathStep) : LoopState :=
  if s.stopped then s
  else
    let s := { s with lastPart := step.part }
    if !step.exists_ then { s with stopped := true }
    else
      let appendIt : Bool :=
        match s.prev with
        | none => true
        | some pr => pr && continuesLocal step
      let s := if appendIt then { s with relationParts := s.relationParts ++ [step.part] } else s
      if !step.hasPathInfos then { s with stopped := true }
      else { s with prev := some step.isRelation }

/-- Walk the whole chain from the initial state. -/
def runLoop (steps : List PathStep) : LoopState :=
  steps.foldl stepFold { relationParts := [], prev := none, lastPart := 0, stopped := false }

/-- The full decision. `fkeyAllowed` is the early foreign-key raw-id-popup
allowance; `validLookups` is the set of declared allowed filter chains. A chain
is permitted when the early allowance fires, when it resolves to at most one
relation part, or when the accumulated relation parts — with or without the
final trailing component — match a declared allowed filter. -/
def lookupDecision (steps : List PathStep) (validLookups : List (List Nat))
    (fkeyAllowed : Bool) : Bool :=
  if fkeyAllowed then true
  else
    let st := runLoop steps
    if st.relationParts.length ≤ 1 then true
    else (validLookups.contains st.relationParts) ||
         (validLookups.contains (st.relationParts ++ [st.lastPart]))
-- pure-end

-- post-conditions-start
/-- The decision is exactly the value produced by walking the chain and matching
the accumulated relation parts against the declared allowed filters. -/
def problem_spec_lookupAllowed
    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool)
    (result : Bool) : Prop :=
  result = lookupDecision steps validLookups fkeyAllowed
-- post-conditions-end

-- impl-start
def implementation_lookupAllowed
    (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool) : Bool :=
  Id.run do
    if fkeyAllowed then
      return true
    let mut relationParts : List Nat := []
    let mut prev : Option Bool := none
    let mut lastPart : Nat := 0
    let mut stopped : Bool := false
    for step in steps do
      if !stopped then
        lastPart := step.part
        if !step.exists_ then
          stopped := true
        else
          let appendIt : Bool :=
            match prev with
            | none => true
            | some pr =>
                pr && !step.inParents && !step.isAutoField &&
                  (!step.modelHasAutoField || !step.partInPrevToFields)
          if appendIt then
            relationParts := relationParts ++ [step.part]
          if !step.hasPathInfos then
            stopped := true
          else
            prev := some step.isRelation
    if relationParts.length ≤ 1 then
      return true
    return (validLookups.contains relationParts) ||
           (validLookups.contains (relationParts ++ [lastPart]))
-- impl-end

-- proof-start
-- @decl:phi_stateProj-start
/-- Projection from the spec's record state to the impl's anonymous 4-tuple
accumulator. Component order matches the do-elaborator's packing of the four
`mut` variables in declaration order: relationParts, prev, lastPart, stopped. -/
def phi_stateProj (s : LoopState) : List Nat × Option Bool × Nat × Bool :=
  (s.relationParts, s.prev, s.lastPart, s.stopped)
-- @decl:phi_stateProj-end

-- @decl:loopBody_tuple-start
/-- The tuple-threading form of one loop iteration, read directly off
`implementation_lookupAllowed`'s loop body (lines 162-178) with the accumulator
destructured into its four components. This is what the impl's `forIn` reduces
to under `Id`. -/
def loopBody_tuple (acc : List Nat × Option Bool × Nat × Bool) (step : PathStep) :
    List Nat × Option Bool × Nat × Bool :=
  let relationParts := acc.1
  let prev := acc.2.1
  let stopped := acc.2.2.2
  if stopped then acc
  else
    let lastPart := step.part
    if !step.exists_ then (relationParts, prev, lastPart, true)
    else
      let appendIt : Bool :=
        match prev with
        | none => true
        | some pr =>
            pr && !step.inParents && !step.isAutoField &&
              (!step.modelHasAutoField || !step.partInPrevToFields)
      let relationParts := if appendIt then relationParts ++ [step.part] else relationParts
      if !step.hasPathInfos then (relationParts, prev, lastPart, true)
      else (relationParts, some step.isRelation, lastPart, false)
-- @decl:loopBody_tuple-end

-- @ns:forIn_to_foldl-start
-- @decl:forIn_to_foldl-start
/-- MonadBridge: the impl's `Id`-monad `for`-loop (an always-`yield` `forIn`
over the 4-tuple accumulator) equals `List.foldl loopBody_tuple` over the same
tuple init. -/
theorem forIn_to_foldl (steps : List PathStep) :
    (Id.run (forIn steps (([] : List Nat), (none : Option Bool), (0 : Nat), false)
        (fun step acc => ForInStep.yield (loopBody_tuple acc step))))
      = steps.foldl loopBody_tuple ([], none, 0, false) := by
  simp only [Id.run, List.forIn_yield_eq_foldl]
-- @decl:forIn_to_foldl-end
-- @ns:forIn_to_foldl-end

-- @ns:step_correspondence-start
-- @decl:step_correspondence-start
/-- FoldHom: per-iteration correspondence — projecting the spec's `stepFold`
result equals applying the tuple loop body to the projected state. -/
theorem step_correspondence (s : LoopState) (step : PathStep) :
    phi_stateProj (stepFold s step) = loopBody_tuple (phi_stateProj s) step := by
  cases s with
  | mk relationParts prev lastPart stopped =>
    simp only [stepFold, loopBody_tuple, phi_stateProj, continuesLocal, Bool.and_assoc]
    repeat' (first | rfl | simp_all | split)
-- @decl:step_correspondence-end
-- @ns:step_correspondence-end

-- @ns:runLoop_proj_eq-start
-- @decl:runLoop_proj_eq-start
/-- FoldHom: the fold homomorphism — the projected `runLoop` state equals the
tuple foldl from the tuple init. -/
theorem runLoop_proj_eq (steps : List PathStep) :
    phi_stateProj (runLoop steps) = steps.foldl loopBody_tuple ([], none, 0, false) := by
  unfold runLoop
  have key : ∀ (l : List PathStep) (s : LoopState),
      phi_stateProj (l.foldl stepFold s) = l.foldl loopBody_tuple (phi_stateProj s) := by
    intro l
    induction l with
    | nil => intro s; rfl
    | cons a t ih =>
      intro s
      simp only [List.foldl_cons]
      rw [ih (stepFold s a), step_correspondence]
  exact key steps _
-- @decl:runLoop_proj_eq-end
-- @ns:runLoop_proj_eq-end

-- @ns:impl_loopBridge-start
-- @decl:impl_loopBridge-start
/-- MonadBridge (do → foldl): the actual `implementation_lookupAllowed` do-block
— its `fkeyAllowed` early `return`, its four `mut` variables packed into the
tuple accumulator, and its post-loop tail decision — equals the closed
`List.foldl loopBody_tuple` form over the tuple init followed by the same tail
decision read off the tuple components. This isolates the monad/do-elaboration
reduction (prove by exposing the always-`yield` `forIn` and applying the
`forIn → foldl` bridge, then reducing the surrounding `Id.run` scaffolding). -/
theorem impl_loopBridge (steps : List PathStep) (validLookups : List (List Nat))
    (fkeyAllowed : Bool) :
    implementation_lookupAllowed steps validLookups fkeyAllowed
      = (if fkeyAllowed then true
         else
           let acc := steps.foldl loopBody_tuple ([], none, 0, false)
           if acc.1.length ≤ 1 then true
           else validLookups.contains acc.1 ||
                validLookups.contains (acc.1 ++ [acc.2.2.1])) := by
  unfold implementation_lookupAllowed
  split
  · rfl
  · simp only [Id.run, bind, pure]
    -- The impl `forIn` accumulator is packed as (lastPart, prev, relationParts, stopped);
    -- `loopBody_tuple` uses (relationParts, prev, lastPart, stopped): coords 1 and 3 are swapped.
    -- Prove the permutation bridge by induction on the list, generalizing the accumulator.
    have key : ∀ (l : List PathStep) (lp : ℕ) (pv : Option Bool) (rp : List ℕ) (st : Bool),
        (forIn l (⟨lp, pv, rp, st⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))
          (fun step r =>
            if (!r.snd.snd.snd) = true then
              if (!step.exists_) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
              else
                if
                    (match r.snd.fst with
                      | none => true
                      | some pr =>
                        pr && !step.inParents && !step.isAutoField &&
                          (!step.modelHasAutoField || !step.partInPrevToFields)) =
                      true then
                  if (!step.hasPathInfos) = true then
                    ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst ++ [step.part], true⟩
                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst ++ [step.part], r.snd.snd.snd⟩
                else
                  if (!step.hasPathInfos) = true then ForInStep.yield ⟨step.part, r.snd.fst, r.snd.snd.fst, true⟩
                  else ForInStep.yield ⟨step.part, some step.isRelation, r.snd.snd.fst, r.snd.snd.snd⟩
            else ForInStep.yield ⟨r.fst, r.snd.fst, r.snd.snd.fst, r.snd.snd.snd⟩) : Id _)
          = (let s := List.foldl loopBody_tuple (rp, pv, lp, st) l
             ⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩) := by
      intro l
      induction l with
      | nil => intro lp pv rp st; rfl
      | cons a t ih =>
        intro lp pv rp st
        simp only [List.forIn_cons, List.foldl_cons, loopBody_tuple, bind, pure]
        by_cases hst : st = true
        · subst hst
          simp only [Bool.not_true, Bool.false_eq_true, if_false, if_true]
          exact ih lp pv rp true
        · simp only [Bool.not_eq_true] at hst
          subst hst
          simp only [Bool.not_false, if_true]
          by_cases hex : a.exists_ = true
          · simp only [hex, Bool.not_true, Bool.false_eq_true, if_false]
            by_cases happ :
                (match pv with
                  | none => true
                  | some pr =>
                    pr && !a.inParents && !a.isAutoField &&
                      (!a.modelHasAutoField || !a.partInPrevToFields)) = true
            · simp only [happ, if_true]
              by_cases hpath : a.hasPathInfos = true
              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
                exact ih a.part (some a.isRelation) (rp ++ [a.part]) false
              · simp only [Bool.not_eq_true] at hpath
                simp only [hpath, Bool.not_false, if_true]
                exact ih a.part pv (rp ++ [a.part]) true
            · simp only [happ, Bool.false_eq_true, if_false]
              by_cases hpath : a.hasPathInfos = true
              · simp only [hpath, Bool.not_true, Bool.false_eq_true, if_false]
                exact ih a.part (some a.isRelation) rp false
              · simp only [Bool.not_eq_true] at hpath
                simp only [hpath, Bool.not_false, if_true]
                exact ih a.part pv rp true
          · simp only [Bool.not_eq_true] at hex
            simp only [hex, Bool.not_false, if_true]
            exact ih a.part pv rp true
    generalize hR : (forIn steps _ _ : Id _) = R
    have hkey : R = (let s := List.foldl loopBody_tuple (([] : List ℕ), (none : Option Bool), (0 : ℕ), false) steps
                     (⟨s.2.2.1, s.2.1, s.1, s.2.2.2⟩ : MProd ℕ (MProd (Option Bool) (MProd (List ℕ) Bool)))) :=
      hR.symm.trans (key steps 0 none [] false)
    rw [hkey]
-- @decl:impl_loopBridge-end
-- @ns:impl_loopBridge-end

-- @ns:tail_match-start
-- @decl:tail_match-start
/-- DecisionTail: the post-loop decision computed from the projected tuple
components equals the decision computed from the record's fields. -/
theorem tail_match (validLookups : List (List Nat)) (st : LoopState) :
    (if (phi_stateProj st).1.length ≤ 1 then true
     else validLookups.contains (phi_stateProj st).1 ||
          validLookups.contains ((phi_stateProj st).1 ++ [(phi_stateProj st).2.2.1]))
      = (if st.relationParts.length ≤ 1 then true
         else validLookups.contains st.relationParts ||
              validLookups.contains (st.relationParts ++ [st.lastPart])) := rfl
-- @decl:tail_match-end
-- @ns:tail_match-end


theorem correct_lookupAllowed :
    ∀ (steps : List PathStep) (validLookups : List (List Nat)) (fkeyAllowed : Bool),
      problem_spec_lookupAllowed steps validLookups fkeyAllowed
        (implementation_lookupAllowed steps validLookups fkeyAllowed) := by
  intro steps validLookups fkeyAllowed
  unfold problem_spec_lookupAllowed
  rw [impl_loopBridge]
  by_cases h : fkeyAllowed
  · simp [h, lookupDecision]
  · simp only [h, if_false]
    rw [← runLoop_proj_eq]
    unfold lookupDecision
    simp only [h, if_false]
    exact tail_match validLookups (runLoop steps)
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Spec shape = exact-equality postcondition, NO axioms/opaque callees (A-legs audit: refinement.md declares None; grep of Solution.lean finds no axiom/opaque/sorry — only a comment). This is the tightest possible spec: verify ⇒ correct trivially, because a verifying impl must equal lookupDecision pointwise.

SAME_SPEC: all 7 attacks + pos_control return True (spec_signature identical; impl+proof regions elided by _lean_spec_view).

### COMMANDS (lean_verify.sh, 300s):
- Positive control (gold, unmodified): bash scripts/lean_verify.sh $D/pos_control.lean → exit 0 (VERIFIES).
- #print axioms correct_lookupAllowed → 'depends on axioms: [propext, Quot.sound]' — CLEAN (no sorryAx, no Classical.choice). File pos_axioms.lean, log_posax.txt.
- Disproofs disp_1..disp_7 (wrong impl kept verbatim, theorem replaced by `implementation ≠ lookupDecision W := by decide`): ALL exit 0. (decide, not native_decide — grep -c native_decide = 0 in all disp files.)
- Honest correctness attempts atk_1/5/6/7 (generic induction+simp proof against the wrong impl): ALL exit 1, 'error: unsolved goals' — genuine failure, not timeout.

STEP-2 RESOLVE: vacuously satisfied. patches={} because ZERO wrong impls have a closing clean-axiom proof; there is nothing to materialize/resolve. The equality spec leaves no gap for a verifying-but-incorrect impl.

6 DISTINCT wrong-impl classes attacked: prepatch bug (atk_1), partial-domain/dropped-conjunct (atk_2), boundary off-by-one (atk_3), control-flow-effect / dropped break (atk_4), ungrounded-oracle echo / always-true (atk_5), final-decision operator swap (atk_6), plus ordering (atk_7). All fail to verify AND are provably ≠ spec.

A-LEG AUDIT: refinement.md rows are all R or I; A-legs section = 'None' (no opaque/axiom callee). mapping.md gives a complete Python↔Lean bijection for every PathStep boolean; the changed guard (relation_parts.append guard, lines 461-469) is modeled DEEPLY via continuesLocal/stepFold, not axiomatized. No kind-3 legs. Correspondence holds; nothing to falsify on the A side because there is no A side.

prepatch_reproduced=true: atk_1 IS the Solution_prepatch.lean impl (pr && !step.inTargetFields); its honest proof fails (exit 1) and disp_1 proves it differs from lookupDecision.

VERDICT: SOUND. The exact-equality, axiom-free spec cannot be satisfied by any incorrect implementation; 7 same-spec wrong impls all machine-proven ≠ spec and all fail to verify.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong/drift) check for django__django-16661 ModelAdmin.lookup_allowed (lean).

SETUP verified: (1) Lean compiles via scripts/lean_verify.sh exit 0; `#print axioms correct_lookupAllowed` = [propext, Quot.sound] — genuine proof, no sorryAx/native_decide/unsafe. (2) markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True: problem_spec_lookupAllowed / lookupDecision / continuesLocal / PathStep are byte-identical between prepatch and postpatch; only the impl append-guard differs (prepatch `pr && !inTargetFields` vs postpatch `pr && continuesLocal`), as required. Checked out base_commit d687febce5868545f99974d2499a91f81a32fef5 worktree and applied patch.diff — post-patch guard is `not prev_field or (prev_field.is_relation and field not in model._meta.parents.values() and field is not model._meta.auto_field and (model._meta.auto_field is None or part not in getattr(prev_field,'to_fields',[])))`.

FAITHFULNESS argument: Every conjunct of the real post-patch guard maps verbatim to the Lean model — prev=none => true (not prev_field); pr (is_relation); !inParents (field not in parents.values()); !isAutoField (field is not auto_field); (!modelHasAutoField || !partInPrevToFields) (auto_field is None or part not in to_fields). continuesLocal transcribes the added conjunction exactly. Control flow faithful: FieldDoesNotExist break -> stopped; path_infos falsy break -> !hasPathInfos -> stopped; prev carried as some isRelation; lastPart set before exists_ check, matching Python's loop-variable retention on break; final `not {SEP.join(rp), SEP.join(rp+[part])}.isdisjoint(valid_lookups)` == contains rp || contains (rp++[lastPart]) — SEP-join<->list-eq is sound because components never contain LOOKUP_SEP (they are the split pieces) so the encoding is injective; only chain equality is observed.

The field-metadata reads (get_field/is_relation/path_infos/parents/auto_field/to_fields) are abstracted into the per-component PathStep booleans — a documented modeling boundary (structure restricted to touched fields), fed as inputs, NOT axiomatized; so no unmodeled callee property is assumed and there is no spec that is too strong. On every input the abstracted booleans take their real values and the model returns exactly what the patched lookup_allowed returns.

DIFFERENTIAL EVIDENCE: bundle conformance_check.py passes (checked=120011, disagreements=0). Independent re-derivation: a from-scratch Python oracle transcribing the post-patch loop with LOOKUP_SEP string-join semantics agreed with the Lean model on 2,000,000 randomized cases (0 divergence), covering chains len 0..6, all metadata boolean combos, valid_lookups variants, and both fkey values.

No diverging input exists. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous verification of the spec view (markers.spec_view over Solution.lean, lean backend) against public problem_statement (hints_text excluded):

1. DECISIVE STRUCTURAL FACT: markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True — verified live. The spec region (docstring, PathStep, LoopState, continuesLocal, stepFold, runLoop, lookupDecision, problem_spec_lookupAllowed) is BYTE-IDENTICAL between the buggy prepatch bundle and the postpatch bundle. The entire prepatch<->postpatch discriminator (impl `pr && !step.inTargetFields` vs the added three-conjunct guard) lives in the ELIDED impl region. A spec view invariant to the patch cannot differentially disclose the gold edit, and the carried gold proof still fails against the buggy prepatch impl (G-DIFF holds: prepatch proof is `sorry`).

2. LEXICAL SCREEN: leakage.screen(solution_src, lean, patch, problem_statement) PASSES clean — passed=True, hard_failures=[], warnings=[]. No diff markers, no reproduced gold-patch line, no patched file path (django/contrib/admin/options.py), no repo symbols (auto_field / to_fields / parents.values / path_infos). The only changed public symbol `lookup_allowed` already appears in problem_statement ('ModelAdmin.lookup_allowed()').

3. DOCSTRING STAYS WITHIN problem_statement: the 'three collapsing situations' and the 'FK-as-PK is a genuine hop ... otherwise the chain would be shortened to a form not declarable as an allowed filter' paragraph restate the reporter's PUBLIC diagnosis ('admin thinking a FK as PK is the same as concrete inheritance ... shortcuts restaurant__place__country to restaurant__country which isn't in list_filter'). Metadata is described abstractly ('synthesised primary key', 'declared target columns', 'parent link'), not via repo field-metadata symbols. No 'old check -> new check' / bug-fix narration. inTargetFields is defined with neutral prose and is unused in the spec view.

4. The prose that DOES quote the gold guard verbatim (each conjunct) and name the prepatch discriminator (inTargetFields) lives in refinement.md and mapping.md, which are NOT part of the leakage-screened spec view (leakage.screen reads solution_src() only); they are auditor-facing derivation docs, not the agent-facing spec.

5. Encoding correct post-patch behavior is by-design for every spec in this benchmark (spec is the correctness oracle); leakage concerns revealing the EDIT/diff, not correct behavior. No spec-view line goes beyond problem_statement.

Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
