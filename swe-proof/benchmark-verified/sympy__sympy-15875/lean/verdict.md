# P2 adversarial audit — sympy__sympy-15875

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is an EXACT-EQUALITY spec: problem_spec_zeroStatus terms realSumZero result := (result = zeroVerdict terms realSumZero), and correct_zeroStatus proves it for ALL (terms, realSumZero). Any impl that differs from zeroVerdict on even one input cannot close the proof in a consistent logic. Concretely, terms=[imaginary, imaginary], realSumZero=some true discriminates the prepatch bug (zeroVerdict=none vs prepatch=some false), and none of atk_1..atk_6 could close.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -125,7 +125,7 @@
     | .indeterminate => return none
   if z == terms.length then
     return some true
-  if nz == 0 || nz == terms.length then
+  if nz == terms.length then
     return none
   match realSumZero with
   | some true =>
@@ -139,276 +139,15 @@
 -- impl-end
 
 
+
 -- proof-start
-/-- The mutable state tracked by the imperative loop: the running counts of
-real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
-imaginary-or-zero (`imOrZ`) presence flags. -/
-structure LoopState where
-  z : Nat
-  nz : Nat
-  im : Bool
-  imOrZ : Bool
-
-/-- Pure model of the loop body: updates the accumulator for a classified term,
-or signals early exit (`none`) on an unclassifiable term. -/
-def stepState (s : LoopState) (a : Summand) : Option LoopState :=
-  match a with
-  | .realZero => some { s with z := s.z + 1 }
-  | .realNonzero => some { s with nz := s.nz + 1 }
-  | .realUnknown => none
-  | .imaginary => some { s with im := true }
-  | .imagOrZero => some { s with imOrZ := true }
-  | .indeterminate => none
-
-/-- Pure model of the implementation's post-loop decision cascade. Structurally
-identical to the `else`-branch of `zeroVerdict`. -/
-def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
-  if s.z == n then some true
-  else if s.nz == 0 || s.nz == n then none
-  else
-    match realSumZero with
-    | some true =>
-        if !s.imOrZ && !s.im then some true
-        else if s.im && !s.imOrZ then some false
-        else none
-    | some false => some false
-    | none => none
-
-/-- Pure recursive model of the whole imperative computation: fold the loop body
-over the list (short-circuiting to `none` on an unclassifiable term), then apply
-the post-loop decision at the empty tail. -/
-def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
-  | [], s => postDecide s n realSumZero
-  | a :: l, s =>
-      match stepState s a with
-      | none => none
-      | some s' => loopRec n realSumZero l s'
-/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
-the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
-flags and the `nz`, `z` counts, in the exact order Lean packs them
-(`⟨slot, im, imOrZ, nz, z⟩`). -/
-abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))
-
-/-- Refinement map from the packed loop state to the model `LoopState`,
-dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
-`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
-def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩
-
-/-- Pure model of the elaborated loop body: the accumulating constructors
-`yield` a slot-`none` state with one field bumped; the two unclassifiable
-constructors `done` with the slot set to `some none` (early return). -/
-def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
-  match a with
-  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
-  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
-  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
-  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-
-/-- Pure model of the elaborated post-loop projection + decision cascade:
-if the early-return slot is set (`some a`) return `a`; otherwise run the same
-`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
-def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
-  match p.1 with
-  | some a => a
-  | none =>
-      if p.2.2.2.2 == n then some true
-      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
-      else match realSumZero with
-        | some true =>
-            if !p.2.2.1 && !p.2.1 then some true
-            else if p.2.1 && !p.2.2.1 then some false
-            else none
-        | some false => some false
-        | none => none
-
-/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
-packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
-is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
-def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
-  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))
-
-/-- Base unfold of the full computation: an empty suffix runs only the
-post-loop cascade. -/
-theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
-    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl
-
-/-- One-step unfold of the full computation: run the body on the head; on
-`yield` recurse on the tail, on `done` short-circuit into the post-loop
-cascade. -/
-theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
-    (l : List Summand) (p : PS) :
-    runFrom n realSumZero (a :: l) p
-      = (match forInBodyPS a p with
-          | ForInStep.yield p' => runFrom n realSumZero l p'
-          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
-  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl
-
-/-- With the early-return slot empty, the post-loop cascade coincides with
-`postDecide` on the projected model state. -/
-theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (h : p.1 = none) :
-    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
-  unfold postLoopPS postDecide toLS
-  rw [h]
-
-/-- With the early-return slot set to `some r`, the post-loop cascade returns
-`r` directly (the early return short-circuits the decision). -/
-theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (r : Option Bool) (h : p.1 = some r) :
-    postLoopPS n realSumZero p = r := by
-  unfold postLoopPS
-  rw [h]
-
-/-- Per-constructor lockstep between the elaborated body and `stepState`: an
-accumulating constructor (`stepState = some s'`) yields a slot-`none` state
-whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
-emits `done` with the slot set to `some none`. -/
-theorem toLS_step_agree (a : Summand) (p : PS) :
-    (∀ s', stepState (toLS p) a = some s' →
-        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
-    (stepState (toLS p) a = none →
-        forInBodyPS a p
-          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
-  constructor
-  · intro s' h
-    cases a <;>
-      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
-      subst h <;>
-      rfl
-  · intro h
-    cases a <;>
-      simp_all [stepState, toLS, forInBodyPS]
-
-/-- The semantic core: for every suffix `l` and every packed state `p` whose
-early-return slot is empty, the full computation equals the pure model
-`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
-casing on the head constructor so the elaborated body reduces in lockstep with
-`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
-the accumulating `yield`s. -/
-theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
-    (l : List Summand) (p : PS) (h : p.1 = none) :
-    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
-  induction l generalizing p with
-  | nil =>
-    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
-    rfl
-  | cons a l' ih =>
-    rw [runFrom_cons]
-    have hstep := toLS_step_agree a p
-    cases hs : stepState (toLS p) a with
-    | none =>
-      have hbody := hstep.2 hs
-      rw [hbody]
-      simp only []
-      rw [postLoop_slot_some n realSumZero _ none rfl]
-      simp only [loopRec, hs]
-    | some s' =>
-      have hbody := hstep.1 s' hs
-      rw [hbody]
-      simp only []
-      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
-      rw [ih _ hp1]
-      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
-        cases s'; rfl
-      rw [htols]
-      simp only [loopRec, hs]
-
-/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
-packed state (slot empty, all counters/flags zero). -/
-theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
-  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
-  congr 1
-  congr 1
-  funext r
-  rcases hr : r.fst with _ | _ <;> rfl
-
-/-- Reify the imperative `for` loop (with early `return none`) as the pure
-recursion `loopRec`, started from the zero state. -/
-theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
-  rw [impl_eq_runFrom_init,
-      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
-  rfl
-
-/-- The loop returns `none` whenever some term is unclassifiable, matching the
-outer guard of `zeroVerdict`. -/
-theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = true) :
-    implementation_zeroStatus terms realSumZero = none := by
-  rw [forIn_unfold]
-  suffices H : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = true →
-      loopRec terms.length realSumZero l s = none by
-    exact H terms _ h
-  intro l
-  induction l with
-  | nil => intro s hl; simp [List.any_nil] at hl
-  | cons a l ih =>
-    intro s hl
-    rw [List.any_cons] at hl
-    cases a <;>
-      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
-      first
-        | rfl
-        | exact ih _ hl
-
-/-- When no term is unclassifiable, running the loop from the zero state drives
-the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
-the post-loop decision with those values. -/
-theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
-      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
-  suffices key : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = false →
-      loopRec terms.length realSumZero l s
-        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
-            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
-    have := key terms ⟨0, 0, false, false⟩ h
-    simpa using this
-  intro l
-  induction l with
-  | nil => intro s _; simp [loopRec]
-  | cons a t ih =>
-    intro s hany
-    cases a <;>
-      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
-        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
-        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
-    case realUnknown => exact absurd hany.1 (by decide)
-    case indeterminate => exact absurd hany.1 (by decide)
-    all_goals
-      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
-        Nat.add_assoc, Nat.add_right_comm])
-
-/-- In the classified case, the post-loop decision applied to the aggregates
-equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
-theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
-      = zeroVerdict terms realSumZero := by
-  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]
-
 theorem correct_zeroStatus :
     ∀ (terms : List Summand) (realSumZero : Option Bool),
       problem_spec_zeroStatus terms realSumZero
         (implementation_zeroStatus terms realSumZero) := by
   intro terms realSumZero
-  unfold problem_spec_zeroStatus
-  by_cases h : terms.any isUnclassified = true
-  · rw [shortcircuit_iff terms realSumZero h]
-    simp only [zeroVerdict, h, if_true]
-  · have h' : terms.any isUnclassified = false := by
-      simpa using h
-    rw [forIn_unfold terms realSumZero,
-        final_state_aggregates terms realSumZero h',
-        decision_cascade_agree terms realSumZero h']
-
+  unfold problem_spec_zeroStatus implementation_zeroStatus zeroVerdict
+  simp
+  try decide
+  try rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,285 +130,24 @@
   match realSumZero with
   | some true =>
       if !imOrZ && !im then
+        return some false
+      if im && !imOrZ then
         return some true
-      if im && !imOrZ then
-        return some false
   | some false => return some false
   | none => pure ()
   return none
 -- impl-end
 
 
+
 -- proof-start
-/-- The mutable state tracked by the imperative loop: the running counts of
-real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
-imaginary-or-zero (`imOrZ`) presence flags. -/
-structure LoopState where
-  z : Nat
-  nz : Nat
-  im : Bool
-  imOrZ : Bool
-
-/-- Pure model of the loop body: updates the accumulator for a classified term,
-or signals early exit (`none`) on an unclassifiable term. -/
-def stepState (s : LoopState) (a : Summand) : Option LoopState :=
-  match a with
-  | .realZero => some { s with z := s.z + 1 }
-  | .realNonzero => some { s with nz := s.nz + 1 }
-  | .realUnknown => none
-  | .imaginary => some { s with im := true }
-  | .imagOrZero => some { s with imOrZ := true }
-  | .indeterminate => none
-
-/-- Pure model of the implementation's post-loop decision cascade. Structurally
-identical to the `else`-branch of `zeroVerdict`. -/
-def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
-  if s.z == n then some true
-  else if s.nz == 0 || s.nz == n then none
-  else
-    match realSumZero with
-    | some true =>
-        if !s.imOrZ && !s.im then some true
-        else if s.im && !s.imOrZ then some false
-        else none
-    | some false => some false
-    | none => none
-
-/-- Pure recursive model of the whole imperative computation: fold the loop body
-over the list (short-circuiting to `none` on an unclassifiable term), then apply
-the post-loop decision at the empty tail. -/
-def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
-  | [], s => postDecide s n realSumZero
-  | a :: l, s =>
-      match stepState s a with
-      | none => none
-      | some s' => loopRec n realSumZero l s'
-/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
-the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
-flags and the `nz`, `z` counts, in the exact order Lean packs them
-(`⟨slot, im, imOrZ, nz, z⟩`). -/
-abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))
-
-/-- Refinement map from the packed loop state to the model `LoopState`,
-dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
-`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
-def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩
-
-/-- Pure model of the elaborated loop body: the accumulating constructors
-`yield` a slot-`none` state with one field bumped; the two unclassifiable
-constructors `done` with the slot set to `some none` (early return). -/
-def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
-  match a with
-  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
-  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
-  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
-  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-
-/-- Pure model of the elaborated post-loop projection + decision cascade:
-if the early-return slot is set (`some a`) return `a`; otherwise run the same
-`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
-def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
-  match p.1 with
-  | some a => a
-  | none =>
-      if p.2.2.2.2 == n then some true
-      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
-      else match realSumZero with
-        | some true =>
-            if !p.2.2.1 && !p.2.1 then some true
-            else if p.2.1 && !p.2.2.1 then some false
-            else none
-        | some false => some false
-        | none => none
-
-/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
-packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
-is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
-def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
-  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))
-
-/-- Base unfold of the full computation: an empty suffix runs only the
-post-loop cascade. -/
-theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
-    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl
-
-/-- One-step unfold of the full computation: run the body on the head; on
-`yield` recurse on the tail, on `done` short-circuit into the post-loop
-cascade. -/
-theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
-    (l : List Summand) (p : PS) :
-    runFrom n realSumZero (a :: l) p
-      = (match forInBodyPS a p with
-          | ForInStep.yield p' => runFrom n realSumZero l p'
-          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
-  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl
-
-/-- With the early-return slot empty, the post-loop cascade coincides with
-`postDecide` on the projected model state. -/
-theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (h : p.1 = none) :
-    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
-  unfold postLoopPS postDecide toLS
-  rw [h]
-
-/-- With the early-return slot set to `some r`, the post-loop cascade returns
-`r` directly (the early return short-circuits the decision). -/
-theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (r : Option Bool) (h : p.1 = some r) :
-    postLoopPS n realSumZero p = r := by
-  unfold postLoopPS
-  rw [h]
-
-/-- Per-constructor lockstep between the elaborated body and `stepState`: an
-accumulating constructor (`stepState = some s'`) yields a slot-`none` state
-whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
-emits `done` with the slot set to `some none`. -/
-theorem toLS_step_agree (a : Summand) (p : PS) :
-    (∀ s', stepState (toLS p) a = some s' →
-        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
-    (stepState (toLS p) a = none →
-        forInBodyPS a p
-          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
-  constructor
-  · intro s' h
-    cases a <;>
-      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
-      subst h <;>
-      rfl
-  · intro h
-    cases a <;>
-      simp_all [stepState, toLS, forInBodyPS]
-
-/-- The semantic core: for every suffix `l` and every packed state `p` whose
-early-return slot is empty, the full computation equals the pure model
-`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
-casing on the head constructor so the elaborated body reduces in lockstep with
-`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
-the accumulating `yield`s. -/
-theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
-    (l : List Summand) (p : PS) (h : p.1 = none) :
-    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
-  induction l generalizing p with
-  | nil =>
-    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
-    rfl
-  | cons a l' ih =>
-    rw [runFrom_cons]
-    have hstep := toLS_step_agree a p
-    cases hs : stepState (toLS p) a with
-    | none =>
-      have hbody := hstep.2 hs
-      rw [hbody]
-      simp only []
-      rw [postLoop_slot_some n realSumZero _ none rfl]
-      simp only [loopRec, hs]
-    | some s' =>
-      have hbody := hstep.1 s' hs
-      rw [hbody]
-      simp only []
-      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
-      rw [ih _ hp1]
-      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
-        cases s'; rfl
-      rw [htols]
-      simp only [loopRec, hs]
-
-/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
-packed state (slot empty, all counters/flags zero). -/
-theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
-  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
-  congr 1
-  congr 1
-  funext r
-  rcases hr : r.fst with _ | _ <;> rfl
-
-/-- Reify the imperative `for` loop (with early `return none`) as the pure
-recursion `loopRec`, started from the zero state. -/
-theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
-  rw [impl_eq_runFrom_init,
-      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
-  rfl
-
-/-- The loop returns `none` whenever some term is unclassifiable, matching the
-outer guard of `zeroVerdict`. -/
-theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = true) :
-    implementation_zeroStatus terms realSumZero = none := by
-  rw [forIn_unfold]
-  suffices H : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = true →
-      loopRec terms.length realSumZero l s = none by
-    exact H terms _ h
-  intro l
-  induction l with
-  | nil => intro s hl; simp [List.any_nil] at hl
-  | cons a l ih =>
-    intro s hl
-    rw [List.any_cons] at hl
-    cases a <;>
-      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
-      first
-        | rfl
-        | exact ih _ hl
-
-/-- When no term is unclassifiable, running the loop from the zero state drives
-the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
-the post-loop decision with those values. -/
-theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
-      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
-  suffices key : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = false →
-      loopRec terms.length realSumZero l s
-        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
-            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
-    have := key terms ⟨0, 0, false, false⟩ h
-    simpa using this
-  intro l
-  induction l with
-  | nil => intro s _; simp [loopRec]
-  | cons a t ih =>
-    intro s hany
-    cases a <;>
-      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
-        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
-        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
-    case realUnknown => exact absurd hany.1 (by decide)
-    case indeterminate => exact absurd hany.1 (by decide)
-    all_goals
-      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
-        Nat.add_assoc, Nat.add_right_comm])
-
-/-- In the classified case, the post-loop decision applied to the aggregates
-equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
-theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
-      = zeroVerdict terms realSumZero := by
-  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]
-
 theorem correct_zeroStatus :
     ∀ (terms : List Summand) (realSumZero : Option Bool),
       problem_spec_zeroStatus terms realSumZero
         (implementation_zeroStatus terms realSumZero) := by
   intro terms realSumZero
-  unfold problem_spec_zeroStatus
-  by_cases h : terms.any isUnclassified = true
-  · rw [shortcircuit_iff terms realSumZero h]
-    simp only [zeroVerdict, h, if_true]
-  · have h' : terms.any isUnclassified = false := by
-      simpa using h
-    rw [forIn_unfold terms realSumZero,
-        final_state_aggregates terms realSumZero h',
-        decision_cascade_agree terms realSumZero h']
-
+  unfold problem_spec_zeroStatus implementation_zeroStatus zeroVerdict
+  simp
+  try decide
+  try rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -133,282 +133,21 @@
         return some true
       if im && !imOrZ then
         return some false
-  | some false => return some false
+  | some false => return none
   | none => pure ()
   return none
 -- impl-end
 
 
+
 -- proof-start
-/-- The mutable state tracked by the imperative loop: the running counts of
-real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
-imaginary-or-zero (`imOrZ`) presence flags. -/
-structure LoopState where
-  z : Nat
-  nz : Nat
-  im : Bool
-  imOrZ : Bool
-
-/-- Pure model of the loop body: updates the accumulator for a classified term,
-or signals early exit (`none`) on an unclassifiable term. -/
-def stepState (s : LoopState) (a : Summand) : Option LoopState :=
-  match a with
-  | .realZero => some { s with z := s.z + 1 }
-  | .realNonzero => some { s with nz := s.nz + 1 }
-  | .realUnknown => none
-  | .imaginary => some { s with im := true }
-  | .imagOrZero => some { s with imOrZ := true }
-  | .indeterminate => none
-
-/-- Pure model of the implementation's post-loop decision cascade. Structurally
-identical to the `else`-branch of `zeroVerdict`. -/
-def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
-  if s.z == n then some true
-  else if s.nz == 0 || s.nz == n then none
-  else
-    match realSumZero with
-    | some true =>
-        if !s.imOrZ && !s.im then some true
-        else if s.im && !s.imOrZ then some false
-        else none
-    | some false => some false
-    | none => none
-
-/-- Pure recursive model of the whole imperative computation: fold the loop body
-over the list (short-circuiting to `none` on an unclassifiable term), then apply
-the post-loop decision at the empty tail. -/
-def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
-  | [], s => postDecide s n realSumZero
-  | a :: l, s =>
-      match stepState s a with
-      | none => none
-      | some s' => loopRec n realSumZero l s'
-/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
-the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
-flags and the `nz`, `z` counts, in the exact order Lean packs them
-(`⟨slot, im, imOrZ, nz, z⟩`). -/
-abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))
-
-/-- Refinement map from the packed loop state to the model `LoopState`,
-dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
-`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
-def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩
-
-/-- Pure model of the elaborated loop body: the accumulating constructors
-`yield` a slot-`none` state with one field bumped; the two unclassifiable
-constructors `done` with the slot set to `some none` (early return). -/
-def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
-  match a with
-  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
-  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
-  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
-  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-
-/-- Pure model of the elaborated post-loop projection + decision cascade:
-if the early-return slot is set (`some a`) return `a`; otherwise run the same
-`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
-def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
-  match p.1 with
-  | some a => a
-  | none =>
-      if p.2.2.2.2 == n then some true
-      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
-      else match realSumZero with
-        | some true =>
-            if !p.2.2.1 && !p.2.1 then some true
-            else if p.2.1 && !p.2.2.1 then some false
-            else none
-        | some false => some false
-        | none => none
-
-/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
-packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
-is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
-def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
-  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))
-
-/-- Base unfold of the full computation: an empty suffix runs only the
-post-loop cascade. -/
-theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
-    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl
-
-/-- One-step unfold of the full computation: run the body on the head; on
-`yield` recurse on the tail, on `done` short-circuit into the post-loop
-cascade. -/
-theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
-    (l : List Summand) (p : PS) :
-    runFrom n realSumZero (a :: l) p
-      = (match forInBodyPS a p with
-          | ForInStep.yield p' => runFrom n realSumZero l p'
-          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
-  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl
-
-/-- With the early-return slot empty, the post-loop cascade coincides with
-`postDecide` on the projected model state. -/
-theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (h : p.1 = none) :
-    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
-  unfold postLoopPS postDecide toLS
-  rw [h]
-
-/-- With the early-return slot set to `some r`, the post-loop cascade returns
-`r` directly (the early return short-circuits the decision). -/
-theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (r : Option Bool) (h : p.1 = some r) :
-    postLoopPS n realSumZero p = r := by
-  unfold postLoopPS
-  rw [h]
-
-/-- Per-constructor lockstep between the elaborated body and `stepState`: an
-accumulating constructor (`stepState = some s'`) yields a slot-`none` state
-whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
-emits `done` with the slot set to `some none`. -/
-theorem toLS_step_agree (a : Summand) (p : PS) :
-    (∀ s', stepState (toLS p) a = some s' →
-        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
-    (stepState (toLS p) a = none →
-        forInBodyPS a p
-          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
-  constructor
-  · intro s' h
-    cases a <;>
-      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
-      subst h <;>
-      rfl
-  · intro h
-    cases a <;>
-      simp_all [stepState, toLS, forInBodyPS]
-
-/-- The semantic core: for every suffix `l` and every packed state `p` whose
-early-return slot is empty, the full computation equals the pure model
-`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
-casing on the head constructor so the elaborated body reduces in lockstep with
-`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
-the accumulating `yield`s. -/
-theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
-    (l : List Summand) (p : PS) (h : p.1 = none) :
-    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
-  induction l generalizing p with
-  | nil =>
-    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
-    rfl
-  | cons a l' ih =>
-    rw [runFrom_cons]
-    have hstep := toLS_step_agree a p
-    cases hs : stepState (toLS p) a with
-    | none =>
-      have hbody := hstep.2 hs
-      rw [hbody]
-      simp only []
-      rw [postLoop_slot_some n realSumZero _ none rfl]
-      simp only [loopRec, hs]
-    | some s' =>
-      have hbody := hstep.1 s' hs
-      rw [hbody]
-      simp only []
-      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
-      rw [ih _ hp1]
-      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
-        cases s'; rfl
-      rw [htols]
-      simp only [loopRec, hs]
-
-/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
-packed state (slot empty, all counters/flags zero). -/
-theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
-  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
-  congr 1
-  congr 1
-  funext r
-  rcases hr : r.fst with _ | _ <;> rfl
-
-/-- Reify the imperative `for` loop (with early `return none`) as the pure
-recursion `loopRec`, started from the zero state. -/
-theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
-  rw [impl_eq_runFrom_init,
-      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
-  rfl
-
-/-- The loop returns `none` whenever some term is unclassifiable, matching the
-outer guard of `zeroVerdict`. -/
-theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = true) :
-    implementation_zeroStatus terms realSumZero = none := by
-  rw [forIn_unfold]
-  suffices H : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = true →
-      loopRec terms.length realSumZero l s = none by
-    exact H terms _ h
-  intro l
-  induction l with
-  | nil => intro s hl; simp [List.any_nil] at hl
-  | cons a l ih =>
-    intro s hl
-    rw [List.any_cons] at hl
-    cases a <;>
-      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
-      first
-        | rfl
-        | exact ih _ hl
-
-/-- When no term is unclassifiable, running the loop from the zero state drives
-the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
-the post-loop decision with those values. -/
-theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
-      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
-  suffices key : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = false →
-      loopRec terms.length realSumZero l s
-        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
-            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
-    have := key terms ⟨0, 0, false, false⟩ h
-    simpa using this
-  intro l
-  induction l with
-  | nil => intro s _; simp [loopRec]
-  | cons a t ih =>
-    intro s hany
-    cases a <;>
-      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
-        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
-        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
-    case realUnknown => exact absurd hany.1 (by decide)
-    case indeterminate => exact absurd hany.1 (by decide)
-    all_goals
-      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
-        Nat.add_assoc, Nat.add_right_comm])
-
-/-- In the classified case, the post-loop decision applied to the aggregates
-equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
-theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
-      = zeroVerdict terms realSumZero := by
-  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]
-
 theorem correct_zeroStatus :
     ∀ (terms : List Summand) (realSumZero : Option Bool),
       problem_spec_zeroStatus terms realSumZero
         (implementation_zeroStatus terms realSumZero) := by
   intro terms realSumZero
-  unfold problem_spec_zeroStatus
-  by_cases h : terms.any isUnclassified = true
-  · rw [shortcircuit_iff terms realSumZero h]
-    simp only [zeroVerdict, h, if_true]
-  · have h' : terms.any isUnclassified = false := by
-      simpa using h
-    rw [forIn_unfold terms realSumZero,
-        final_state_aggregates terms realSumZero h',
-        decision_cascade_agree terms realSumZero h']
-
+  unfold problem_spec_zeroStatus implementation_zeroStatus zeroVerdict
+  simp
+  try decide
+  try rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -123,7 +123,7 @@
     | .imaginary => im := true
     | .imagOrZero => imOrZ := true
     | .indeterminate => return none
-  if z == terms.length then
+  if z + 1 == terms.length then
     return some true
   if nz == 0 || nz == terms.length then
     return none
@@ -139,276 +139,15 @@
 -- impl-end
 
 
+
 -- proof-start
-/-- The mutable state tracked by the imperative loop: the running counts of
-real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
-imaginary-or-zero (`imOrZ`) presence flags. -/
-structure LoopState where
-  z : Nat
-  nz : Nat
-  im : Bool
-  imOrZ : Bool
-
-/-- Pure model of the loop body: updates the accumulator for a classified term,
-or signals early exit (`none`) on an unclassifiable term. -/
-def stepState (s : LoopState) (a : Summand) : Option LoopState :=
-  match a with
-  | .realZero => some { s with z := s.z + 1 }
-  | .realNonzero => some { s with nz := s.nz + 1 }
-  | .realUnknown => none
-  | .imaginary => some { s with im := true }
-  | .imagOrZero => some { s with imOrZ := true }
-  | .indeterminate => none
-
-/-- Pure model of the implementation's post-loop decision cascade. Structurally
-identical to the `else`-branch of `zeroVerdict`. -/
-def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
-  if s.z == n then some true
-  else if s.nz == 0 || s.nz == n then none
-  else
-    match realSumZero with
-    | some true =>
-        if !s.imOrZ && !s.im then some true
-        else if s.im && !s.imOrZ then some false
-        else none
-    | some false => some false
-    | none => none
-
-/-- Pure recursive model of the whole imperative computation: fold the loop body
-over the list (short-circuiting to `none` on an unclassifiable term), then apply
-the post-loop decision at the empty tail. -/
-def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
-  | [], s => postDecide s n realSumZero
-  | a :: l, s =>
-      match stepState s a with
-      | none => none
-      | some s' => loopRec n realSumZero l s'
-/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
-the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
-flags and the `nz`, `z` counts, in the exact order Lean packs them
-(`⟨slot, im, imOrZ, nz, z⟩`). -/
-abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))
-
-/-- Refinement map from the packed loop state to the model `LoopState`,
-dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
-`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
-def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩
-
-/-- Pure model of the elaborated loop body: the accumulating constructors
-`yield` a slot-`none` state with one field bumped; the two unclassifiable
-constructors `done` with the slot set to `some none` (early return). -/
-def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
-  match a with
-  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
-  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
-  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
-  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-
-/-- Pure model of the elaborated post-loop projection + decision cascade:
-if the early-return slot is set (`some a`) return `a`; otherwise run the same
-`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
-def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
-  match p.1 with
-  | some a => a
-  | none =>
-      if p.2.2.2.2 == n then some true
-      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
-      else match realSumZero with
-        | some true =>
-            if !p.2.2.1 && !p.2.1 then some true
-            else if p.2.1 && !p.2.2.1 then some false
-            else none
-        | some false => some false
-        | none => none
-
-/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
-packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
-is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
-def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
-  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))
-
-/-- Base unfold of the full computation: an empty suffix runs only the
-post-loop cascade. -/
-theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
-    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl
-
-/-- One-step unfold of the full computation: run the body on the head; on
-`yield` recurse on the tail, on `done` short-circuit into the post-loop
-cascade. -/
-theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
-    (l : List Summand) (p : PS) :
-    runFrom n realSumZero (a :: l) p
-      = (match forInBodyPS a p with
-          | ForInStep.yield p' => runFrom n realSumZero l p'
-          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
-  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl
-
-/-- With the early-return slot empty, the post-loop cascade coincides with
-`postDecide` on the projected model state. -/
-theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (h : p.1 = none) :
-    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
-  unfold postLoopPS postDecide toLS
-  rw [h]
-
-/-- With the early-return slot set to `some r`, the post-loop cascade returns
-`r` directly (the early return short-circuits the decision). -/
-theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (r : Option Bool) (h : p.1 = some r) :
-    postLoopPS n realSumZero p = r := by
-  unfold postLoopPS
-  rw [h]
-
-/-- Per-constructor lockstep between the elaborated body and `stepState`: an
-accumulating constructor (`stepState = some s'`) yields a slot-`none` state
-whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
-emits `done` with the slot set to `some none`. -/
-theorem toLS_step_agree (a : Summand) (p : PS) :
-    (∀ s', stepState (toLS p) a = some s' →
-        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
-    (stepState (toLS p) a = none →
-        forInBodyPS a p
-          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
-  constructor
-  · intro s' h
-    cases a <;>
-      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
-      subst h <;>
-      rfl
-  · intro h
-    cases a <;>
-      simp_all [stepState, toLS, forInBodyPS]
-
-/-- The semantic core: for every suffix `l` and every packed state `p` whose
-early-return slot is empty, the full computation equals the pure model
-`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
-casing on the head constructor so the elaborated body reduces in lockstep with
-`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
-the accumulating `yield`s. -/
-theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
-    (l : List Summand) (p : PS) (h : p.1 = none) :
-    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
-  induction l generalizing p with
-  | nil =>
-    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
-    rfl
-  | cons a l' ih =>
-    rw [runFrom_cons]
-    have hstep := toLS_step_agree a p
-    cases hs : stepState (toLS p) a with
-    | none =>
-      have hbody := hstep.2 hs
-      rw [hbody]
-      simp only []
-      rw [postLoop_slot_some n realSumZero _ none rfl]
-      simp only [loopRec, hs]
-    | some s' =>
-      have hbody := hstep.1 s' hs
-      rw [hbody]
-      simp only []
-      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
-      rw [ih _ hp1]
-      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
-        cases s'; rfl
-      rw [htols]
-      simp only [loopRec, hs]
-
-/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
-packed state (slot empty, all counters/flags zero). -/
-theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
-  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
-  congr 1
-  congr 1
-  funext r
-  rcases hr : r.fst with _ | _ <;> rfl
-
-/-- Reify the imperative `for` loop (with early `return none`) as the pure
-recursion `loopRec`, started from the zero state. -/
-theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
-  rw [impl_eq_runFrom_init,
-      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
-  rfl
-
-/-- The loop returns `none` whenever some term is unclassifiable, matching the
-outer guard of `zeroVerdict`. -/
-theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = true) :
-    implementation_zeroStatus terms realSumZero = none := by
-  rw [forIn_unfold]
-  suffices H : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = true →
-      loopRec terms.length realSumZero l s = none by
-    exact H terms _ h
-  intro l
-  induction l with
-  | nil => intro s hl; simp [List.any_nil] at hl
-  | cons a l ih =>
-    intro s hl
-    rw [List.any_cons] at hl
-    cases a <;>
-      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
-      first
-        | rfl
-        | exact ih _ hl
-
-/-- When no term is unclassifiable, running the loop from the zero state drives
-the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
-the post-loop decision with those values. -/
-theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
-      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
-  suffices key : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = false →
-      loopRec terms.length realSumZero l s
-        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
-            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
-    have := key terms ⟨0, 0, false, false⟩ h
-    simpa using this
-  intro l
-  induction l with
-  | nil => intro s _; simp [loopRec]
-  | cons a t ih =>
-    intro s hany
-    cases a <;>
-      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
-        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
-        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
-    case realUnknown => exact absurd hany.1 (by decide)
-    case indeterminate => exact absurd hany.1 (by decide)
-    all_goals
-      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
-        Nat.add_assoc, Nat.add_right_comm])
-
-/-- In the classified case, the post-loop decision applied to the aggregates
-equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
-theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
-      = zeroVerdict terms realSumZero := by
-  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]
-
 theorem correct_zeroStatus :
     ∀ (terms : List Summand) (realSumZero : Option Bool),
       problem_spec_zeroStatus terms realSumZero
         (implementation_zeroStatus terms realSumZero) := by
   intro terms realSumZero
-  unfold problem_spec_zeroStatus
-  by_cases h : terms.any isUnclassified = true
-  · rw [shortcircuit_iff terms realSumZero h]
-    simp only [zeroVerdict, h, if_true]
-  · have h' : terms.any isUnclassified = false := by
-      simpa using h
-    rw [forIn_unfold terms realSumZero,
-        final_state_aggregates terms realSumZero h',
-        decision_cascade_agree terms realSumZero h']
-
+  unfold problem_spec_zeroStatus implementation_zeroStatus zeroVerdict
+  simp
+  try decide
+  try rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,7 +121,7 @@
     | .realNonzero => nz := nz + 1
     | .realUnknown => return none
     | .imaginary => im := true
-    | .imagOrZero => imOrZ := true
+    | .imagOrZero => im := true
     | .indeterminate => return none
   if z == terms.length then
     return some true
@@ -139,276 +139,15 @@
 -- impl-end
 
 
+
 -- proof-start
-/-- The mutable state tracked by the imperative loop: the running counts of
-real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
-imaginary-or-zero (`imOrZ`) presence flags. -/
-structure LoopState where
-  z : Nat
-  nz : Nat
-  im : Bool
-  imOrZ : Bool
-
-/-- Pure model of the loop body: updates the accumulator for a classified term,
-or signals early exit (`none`) on an unclassifiable term. -/
-def stepState (s : LoopState) (a : Summand) : Option LoopState :=
-  match a with
-  | .realZero => some { s with z := s.z + 1 }
-  | .realNonzero => some { s with nz := s.nz + 1 }
-  | .realUnknown => none
-  | .imaginary => some { s with im := true }
-  | .imagOrZero => some { s with imOrZ := true }
-  | .indeterminate => none
-
-/-- Pure model of the implementation's post-loop decision cascade. Structurally
-identical to the `else`-branch of `zeroVerdict`. -/
-def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
-  if s.z == n then some true
-  else if s.nz == 0 || s.nz == n then none
-  else
-    match realSumZero with
-    | some true =>
-        if !s.imOrZ && !s.im then some true
-        else if s.im && !s.imOrZ then some false
-        else none
-    | some false => some false
-    | none => none
-
-/-- Pure recursive model of the whole imperative computation: fold the loop body
-over the list (short-circuiting to `none` on an unclassifiable term), then apply
-the post-loop decision at the empty tail. -/
-def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
-  | [], s => postDecide s n realSumZero
-  | a :: l, s =>
-      match stepState s a with
-      | none => none
-      | some s' => loopRec n realSumZero l s'
-/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
-the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
-flags and the `nz`, `z` counts, in the exact order Lean packs them
-(`⟨slot, im, imOrZ, nz, z⟩`). -/
-abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))
-
-/-- Refinement map from the packed loop state to the model `LoopState`,
-dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
-`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
-def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩
-
-/-- Pure model of the elaborated loop body: the accumulating constructors
-`yield` a slot-`none` state with one field bumped; the two unclassifiable
-constructors `done` with the slot set to `some none` (early return). -/
-def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
-  match a with
-  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
-  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
-  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
-  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-
-/-- Pure model of the elaborated post-loop projection + decision cascade:
-if the early-return slot is set (`some a`) return `a`; otherwise run the same
-`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
-def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
-  match p.1 with
-  | some a => a
-  | none =>
-      if p.2.2.2.2 == n then some true
-      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
-      else match realSumZero with
-        | some true =>
-            if !p.2.2.1 && !p.2.1 then some true
-            else if p.2.1 && !p.2.2.1 then some false
-            else none
-        | some false => some false
-        | none => none
-
-/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
-packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
-is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
-def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
-  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))
-
-/-- Base unfold of the full computation: an empty suffix runs only the
-post-loop cascade. -/
-theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
-    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl
-
-/-- One-step unfold of the full computation: run the body on the head; on
-`yield` recurse on the tail, on `done` short-circuit into the post-loop
-cascade. -/
-theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
-    (l : List Summand) (p : PS) :
-    runFrom n realSumZero (a :: l) p
-      = (match forInBodyPS a p with
-          | ForInStep.yield p' => runFrom n realSumZero l p'
-          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
-  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl
-
-/-- With the early-return slot empty, the post-loop cascade coincides with
-`postDecide` on the projected model state. -/
-theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (h : p.1 = none) :
-    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
-  unfold postLoopPS postDecide toLS
-  rw [h]
-
-/-- With the early-return slot set to `some r`, the post-loop cascade returns
-`r` directly (the early return short-circuits the decision). -/
-theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (r : Option Bool) (h : p.1 = some r) :
-    postLoopPS n realSumZero p = r := by
-  unfold postLoopPS
-  rw [h]
-
-/-- Per-constructor lockstep between the elaborated body and `stepState`: an
-accumulating constructor (`stepState = some s'`) yields a slot-`none` state
-whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
-emits `done` with the slot set to `some none`. -/
-theorem toLS_step_agree (a : Summand) (p : PS) :
-    (∀ s', stepState (toLS p) a = some s' →
-        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
-    (stepState (toLS p) a = none →
-        forInBodyPS a p
-          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
-  constructor
-  · intro s' h
-    cases a <;>
-      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
-      subst h <;>
-      rfl
-  · intro h
-    cases a <;>
-      simp_all [stepState, toLS, forInBodyPS]
-
-/-- The semantic core: for every suffix `l` and every packed state `p` whose
-early-return slot is empty, the full computation equals the pure model
-`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
-casing on the head constructor so the elaborated body reduces in lockstep with
-`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
-the accumulating `yield`s. -/
-theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
-    (l : List Summand) (p : PS) (h : p.1 = none) :
-    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
-  induction l generalizing p with
-  | nil =>
-    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
-    rfl
-  | cons a l' ih =>
-    rw [runFrom_cons]
-    have hstep := toLS_step_agree a p
-    cases hs : stepState (toLS p) a with
-    | none =>
-      have hbody := hstep.2 hs
-      rw [hbody]
-      simp only []
-      rw [postLoop_slot_some n realSumZero _ none rfl]
-      simp only [loopRec, hs]
-    | some s' =>
-      have hbody := hstep.1 s' hs
-      rw [hbody]
-      simp only []
-      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
-      rw [ih _ hp1]
-      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
-        cases s'; rfl
-      rw [htols]
-      simp only [loopRec, hs]
-
-/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
-packed state (slot empty, all counters/flags zero). -/
-theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
-  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
-  congr 1
-  congr 1
-  funext r
-  rcases hr : r.fst with _ | _ <;> rfl
-
-/-- Reify the imperative `for` loop (with early `return none`) as the pure
-recursion `loopRec`, started from the zero state. -/
-theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
-  rw [impl_eq_runFrom_init,
-      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
-  rfl
-
-/-- The loop returns `none` whenever some term is unclassifiable, matching the
-outer guard of `zeroVerdict`. -/
-theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = true) :
-    implementation_zeroStatus terms realSumZero = none := by
-  rw [forIn_unfold]
-  suffices H : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = true →
-      loopRec terms.length realSumZero l s = none by
-    exact H terms _ h
-  intro l
-  induction l with
-  | nil => intro s hl; simp [List.any_nil] at hl
-  | cons a l ih =>
-    intro s hl
-    rw [List.any_cons] at hl
-    cases a <;>
-      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
-      first
-        | rfl
-        | exact ih _ hl
-
-/-- When no term is unclassifiable, running the loop from the zero state drives
-the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
-the post-loop decision with those values. -/
-theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
-      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
-  suffices key : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = false →
-      loopRec terms.length realSumZero l s
-        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
-            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
-    have := key terms ⟨0, 0, false, false⟩ h
-    simpa using this
-  intro l
-  induction l with
-  | nil => intro s _; simp [loopRec]
-  | cons a t ih =>
-    intro s hany
-    cases a <;>
-      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
-        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
-        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
-    case realUnknown => exact absurd hany.1 (by decide)
-    case indeterminate => exact absurd hany.1 (by decide)
-    all_goals
-      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
-        Nat.add_assoc, Nat.add_right_comm])
-
-/-- In the classified case, the post-loop decision applied to the aggregates
-equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
-theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
-      = zeroVerdict terms realSumZero := by
-  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]
-
 theorem correct_zeroStatus :
     ∀ (terms : List Summand) (realSumZero : Option Bool),
       problem_spec_zeroStatus terms realSumZero
         (implementation_zeroStatus terms realSumZero) := by
   intro terms realSumZero
-  unfold problem_spec_zeroStatus
-  by_cases h : terms.any isUnclassified = true
-  · rw [shortcircuit_iff terms realSumZero h]
-    simp only [zeroVerdict, h, if_true]
-  · have h' : terms.any isUnclassified = false := by
-      simpa using h
-    rw [forIn_unfold terms realSumZero,
-        final_state_aggregates terms realSumZero h',
-        decision_cascade_agree terms realSumZero h']
-
+  unfold problem_spec_zeroStatus implementation_zeroStatus zeroVerdict
+  simp
+  try decide
+  try rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -127,288 +127,19 @@
     return some true
   if nz == 0 || nz == terms.length then
     return none
-  match realSumZero with
-  | some true =>
-      if !imOrZ && !im then
-        return some true
-      if im && !imOrZ then
-        return some false
-  | some false => return some false
-  | none => pure ()
   return none
 -- impl-end
 
 
+
 -- proof-start
-/-- The mutable state tracked by the imperative loop: the running counts of
-real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
-imaginary-or-zero (`imOrZ`) presence flags. -/
-structure LoopState where
-  z : Nat
-  nz : Nat
-  im : Bool
-  imOrZ : Bool
-
-/-- Pure model of the loop body: updates the accumulator for a classified term,
-or signals early exit (`none`) on an unclassifiable term. -/
-def stepState (s : LoopState) (a : Summand) : Option LoopState :=
-  match a with
-  | .realZero => some { s with z := s.z + 1 }
-  | .realNonzero => some { s with nz := s.nz + 1 }
-  | .realUnknown => none
-  | .imaginary => some { s with im := true }
-  | .imagOrZero => some { s with imOrZ := true }
-  | .indeterminate => none
-
-/-- Pure model of the implementation's post-loop decision cascade. Structurally
-identical to the `else`-branch of `zeroVerdict`. -/
-def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
-  if s.z == n then some true
-  else if s.nz == 0 || s.nz == n then none
-  else
-    match realSumZero with
-    | some true =>
-        if !s.imOrZ && !s.im then some true
-        else if s.im && !s.imOrZ then some false
-        else none
-    | some false => some false
-    | none => none
-
-/-- Pure recursive model of the whole imperative computation: fold the loop body
-over the list (short-circuiting to `none` on an unclassifiable term), then apply
-the post-loop decision at the empty tail. -/
-def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
-  | [], s => postDecide s n realSumZero
-  | a :: l, s =>
-      match stepState s a with
-      | none => none
-      | some s' => loopRec n realSumZero l s'
-/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
-the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
-flags and the `nz`, `z` counts, in the exact order Lean packs them
-(`⟨slot, im, imOrZ, nz, z⟩`). -/
-abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))
-
-/-- Refinement map from the packed loop state to the model `LoopState`,
-dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
-`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
-def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩
-
-/-- Pure model of the elaborated loop body: the accumulating constructors
-`yield` a slot-`none` state with one field bumped; the two unclassifiable
-constructors `done` with the slot set to `some none` (early return). -/
-def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
-  match a with
-  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
-  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
-  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
-  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-
-/-- Pure model of the elaborated post-loop projection + decision cascade:
-if the early-return slot is set (`some a`) return `a`; otherwise run the same
-`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
-def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
-  match p.1 with
-  | some a => a
-  | none =>
-      if p.2.2.2.2 == n then some true
-      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
-      else match realSumZero with
-        | some true =>
-            if !p.2.2.1 && !p.2.1 then some true
-            else if p.2.1 && !p.2.2.1 then some false
-            else none
-        | some false => some false
-        | none => none
-
-/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
-packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
-is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
-def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
-  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))
-
-/-- Base unfold of the full computation: an empty suffix runs only the
-post-loop cascade. -/
-theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
-    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl
-
-/-- One-step unfold of the full computation: run the body on the head; on
-`yield` recurse on the tail, on `done` short-circuit into the post-loop
-cascade. -/
-theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
-    (l : List Summand) (p : PS) :
-    runFrom n realSumZero (a :: l) p
-      = (match forInBodyPS a p with
-          | ForInStep.yield p' => runFrom n realSumZero l p'
-          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
-  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl
-
-/-- With the early-return slot empty, the post-loop cascade coincides with
-`postDecide` on the projected model state. -/
-theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (h : p.1 = none) :
-    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
-  unfold postLoopPS postDecide toLS
-  rw [h]
-
-/-- With the early-return slot set to `some r`, the post-loop cascade returns
-`r` directly (the early return short-circuits the decision). -/
-theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (r : Option Bool) (h : p.1 = some r) :
-    postLoopPS n realSumZero p = r := by
-  unfold postLoopPS
-  rw [h]
-
-/-- Per-constructor lockstep between the elaborated body and `stepState`: an
-accumulating constructor (`stepState = some s'`) yields a slot-`none` state
-whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
-emits `done` with the slot set to `some none`. -/
-theorem toLS_step_agree (a : Summand) (p : PS) :
-    (∀ s', stepState (toLS p) a = some s' →
-        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
-    (stepState (toLS p) a = none →
-        forInBodyPS a p
-          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
-  constructor
-  · intro s' h
-    cases a <;>
-      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
-      subst h <;>
-      rfl
-  · intro h
-    cases a <;>
-      simp_all [stepState, toLS, forInBodyPS]
-
-/-- The semantic core: for every suffix `l` and every packed state `p` whose
-early-return slot is empty, the full computation equals the pure model
-`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
-casing on the head constructor so the elaborated body reduces in lockstep with
-`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
-the accumulating `yield`s. -/
-theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
-    (l : List Summand) (p : PS) (h : p.1 = none) :
-    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
-  induction l generalizing p with
-  | nil =>
-    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
-    rfl
-  | cons a l' ih =>
-    rw [runFrom_cons]
-    have hstep := toLS_step_agree a p
-    cases hs : stepState (toLS p) a with
-    | none =>
-      have hbody := hstep.2 hs
-      rw [hbody]
-      simp only []
-      rw [postLoop_slot_some n realSumZero _ none rfl]
-      simp only [loopRec, hs]
-    | some s' =>
-      have hbody := hstep.1 s' hs
-      rw [hbody]
-      simp only []
-      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
-      rw [ih _ hp1]
-      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
-        cases s'; rfl
-      rw [htols]
-      simp only [loopRec, hs]
-
-/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
-packed state (slot empty, all counters/flags zero). -/
-theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
-  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
-  congr 1
-  congr 1
-  funext r
-  rcases hr : r.fst with _ | _ <;> rfl
-
-/-- Reify the imperative `for` loop (with early `return none`) as the pure
-recursion `loopRec`, started from the zero state. -/
-theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
-  rw [impl_eq_runFrom_init,
-      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
-  rfl
-
-/-- The loop returns `none` whenever some term is unclassifiable, matching the
-outer guard of `zeroVerdict`. -/
-theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = true) :
-    implementation_zeroStatus terms realSumZero = none := by
-  rw [forIn_unfold]
-  suffices H : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = true →
-      loopRec terms.length realSumZero l s = none by
-    exact H terms _ h
-  intro l
-  induction l with
-  | nil => intro s hl; simp [List.any_nil] at hl
-  | cons a l ih =>
-    intro s hl
-    rw [List.any_cons] at hl
-    cases a <;>
-      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
-      first
-        | rfl
-        | exact ih _ hl
-
-/-- When no term is unclassifiable, running the loop from the zero state drives
-the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
-the post-loop decision with those values. -/
-theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
-      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
-  suffices key : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = false →
-      loopRec terms.length realSumZero l s
-        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
-            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
-    have := key terms ⟨0, 0, false, false⟩ h
-    simpa using this
-  intro l
-  induction l with
-  | nil => intro s _; simp [loopRec]
-  | cons a t ih =>
-    intro s hany
-    cases a <;>
-      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
-        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
-        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
-    case realUnknown => exact absurd hany.1 (by decide)
-    case indeterminate => exact absurd hany.1 (by decide)
-    all_goals
-      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
-        Nat.add_assoc, Nat.add_right_comm])
-
-/-- In the classified case, the post-loop decision applied to the aggregates
-equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
-theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
-      = zeroVerdict terms realSumZero := by
-  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]
-
 theorem correct_zeroStatus :
     ∀ (terms : List Summand) (realSumZero : Option Bool),
       problem_spec_zeroStatus terms realSumZero
         (implementation_zeroStatus terms realSumZero) := by
   intro terms realSumZero
-  unfold problem_spec_zeroStatus
-  by_cases h : terms.any isUnclassified = true
-  · rw [shortcircuit_iff terms realSumZero h]
-    simp only [zeroVerdict, h, if_true]
-  · have h' : terms.any isUnclassified = false := by
-      simpa using h
-    rw [forIn_unfold terms realSumZero,
-        final_state_aggregates terms realSumZero h',
-        decision_cascade_agree terms realSumZero h']
-
+  unfold problem_spec_zeroStatus implementation_zeroStatus zeroVerdict
+  simp
+  try decide
+  try rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -110,305 +110,17 @@
 
 -- impl-start
 def implementation_zeroStatus
-    (terms : List Summand) (realSumZero : Option Bool) : Option Bool := Id.run do
-  let mut z := 0
-  let mut nz := 0
-  let mut im := false
-  let mut imOrZ := false
-  for a in terms do
-    match a with
-    | .realZero => z := z + 1
-    | .realNonzero => nz := nz + 1
-    | .realUnknown => return none
-    | .imaginary => im := true
-    | .imagOrZero => imOrZ := true
-    | .indeterminate => return none
-  if z == terms.length then
-    return some true
-  if nz == 0 || nz == terms.length then
-    return none
-  match realSumZero with
-  | some true =>
-      if !imOrZ && !im then
-        return some true
-      if im && !imOrZ then
-        return some false
-  | some false => return some false
-  | none => pure ()
-  return none
+    (terms : List Summand) (realSumZero : Option Bool) : Option Bool :=
+  zeroVerdict terms realSumZero
 -- impl-end
 
 
+
 -- proof-start
-/-- The mutable state tracked by the imperative loop: the running counts of
-real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
-imaginary-or-zero (`imOrZ`) presence flags. -/
-structure LoopState where
-  z : Nat
-  nz : Nat
-  im : Bool
-  imOrZ : Bool
-
-/-- Pure model of the loop body: updates the accumulator for a classified term,
-or signals early exit (`none`) on an unclassifiable term. -/
-def stepState (s : LoopState) (a : Summand) : Option LoopState :=
-  match a with
-  | .realZero => some { s with z := s.z + 1 }
-  | .realNonzero => some { s with nz := s.nz + 1 }
-  | .realUnknown => none
-  | .imaginary => some { s with im := true }
-  | .imagOrZero => some { s with imOrZ := true }
-  | .indeterminate => none
-
-/-- Pure model of the implementation's post-loop decision cascade. Structurally
-identical to the `else`-branch of `zeroVerdict`. -/
-def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
-  if s.z == n then some true
-  else if s.nz == 0 || s.nz == n then none
-  else
-    match realSumZero with
-    | some true =>
-        if !s.imOrZ && !s.im then some true
-        else if s.im && !s.imOrZ then some false
-        else none
-    | some false => some false
-    | none => none
-
-/-- Pure recursive model of the whole imperative computation: fold the loop body
-over the list (short-circuiting to `none` on an unclassifiable term), then apply
-the post-loop decision at the empty tail. -/
-def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
-  | [], s => postDecide s n realSumZero
-  | a :: l, s =>
-      match stepState s a with
-      | none => none
-      | some s' => loopRec n realSumZero l s'
-/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
-the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
-flags and the `nz`, `z` counts, in the exact order Lean packs them
-(`⟨slot, im, imOrZ, nz, z⟩`). -/
-abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))
-
-/-- Refinement map from the packed loop state to the model `LoopState`,
-dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
-`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
-def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩
-
-/-- Pure model of the elaborated loop body: the accumulating constructors
-`yield` a slot-`none` state with one field bumped; the two unclassifiable
-constructors `done` with the slot set to `some none` (early return). -/
-def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
-  match a with
-  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
-  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
-  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
-  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
-
-/-- Pure model of the elaborated post-loop projection + decision cascade:
-if the early-return slot is set (`some a`) return `a`; otherwise run the same
-`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
-def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
-  match p.1 with
-  | some a => a
-  | none =>
-      if p.2.2.2.2 == n then some true
-      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
-      else match realSumZero with
-        | some true =>
-            if !p.2.2.1 && !p.2.1 then some true
-            else if p.2.1 && !p.2.2.1 then some false
-            else none
-        | some false => some false
-        | none => none
-
-/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
-packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
-is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
-def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
-  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))
-
-/-- Base unfold of the full computation: an empty suffix runs only the
-post-loop cascade. -/
-theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
-    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl
-
-/-- One-step unfold of the full computation: run the body on the head; on
-`yield` recurse on the tail, on `done` short-circuit into the post-loop
-cascade. -/
-theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
-    (l : List Summand) (p : PS) :
-    runFrom n realSumZero (a :: l) p
-      = (match forInBodyPS a p with
-          | ForInStep.yield p' => runFrom n realSumZero l p'
-          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
-  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl
-
-/-- With the early-return slot empty, the post-loop cascade coincides with
-`postDecide` on the projected model state. -/
-theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (h : p.1 = none) :
-    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
-  unfold postLoopPS postDecide toLS
-  rw [h]
-
-/-- With the early-return slot set to `some r`, the post-loop cascade returns
-`r` directly (the early return short-circuits the decision). -/
-theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
-    (r : Option Bool) (h : p.1 = some r) :
-    postLoopPS n realSumZero p = r := by
-  unfold postLoopPS
-  rw [h]
-
-/-- Per-constructor lockstep between the elaborated body and `stepState`: an
-accumulating constructor (`stepState = some s'`) yields a slot-`none` state
-whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
-emits `done` with the slot set to `some none`. -/
-theorem toLS_step_agree (a : Summand) (p : PS) :
-    (∀ s', stepState (toLS p) a = some s' →
-        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
-    (stepState (toLS p) a = none →
-        forInBodyPS a p
-          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
-  constructor
-  · intro s' h
-    cases a <;>
-      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
-      subst h <;>
-      rfl
-  · intro h
-    cases a <;>
-      simp_all [stepState, toLS, forInBodyPS]
-
-/-- The semantic core: for every suffix `l` and every packed state `p` whose
-early-return slot is empty, the full computation equals the pure model
-`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
-casing on the head constructor so the elaborated body reduces in lockstep with
-`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
-the accumulating `yield`s. -/
-theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
-    (l : List Summand) (p : PS) (h : p.1 = none) :
-    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
-  induction l generalizing p with
-  | nil =>
-    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
-    rfl
-  | cons a l' ih =>
-    rw [runFrom_cons]
-    have hstep := toLS_step_agree a p
-    cases hs : stepState (toLS p) a with
-    | none =>
-      have hbody := hstep.2 hs
-      rw [hbody]
-      simp only []
-      rw [postLoop_slot_some n realSumZero _ none rfl]
-      simp only [loopRec, hs]
-    | some s' =>
-      have hbody := hstep.1 s' hs
-      rw [hbody]
-      simp only []
-      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
-      rw [ih _ hp1]
-      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
-        cases s'; rfl
-      rw [htols]
-      simp only [loopRec, hs]
-
-/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
-packed state (slot empty, all counters/flags zero). -/
-theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
-  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
-  congr 1
-  congr 1
-  funext r
-  rcases hr : r.fst with _ | _ <;> rfl
-
-/-- Reify the imperative `for` loop (with early `return none`) as the pure
-recursion `loopRec`, started from the zero state. -/
-theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
-    implementation_zeroStatus terms realSumZero
-      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
-  rw [impl_eq_runFrom_init,
-      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
-  rfl
-
-/-- The loop returns `none` whenever some term is unclassifiable, matching the
-outer guard of `zeroVerdict`. -/
-theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = true) :
-    implementation_zeroStatus terms realSumZero = none := by
-  rw [forIn_unfold]
-  suffices H : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = true →
-      loopRec terms.length realSumZero l s = none by
-    exact H terms _ h
-  intro l
-  induction l with
-  | nil => intro s hl; simp [List.any_nil] at hl
-  | cons a l ih =>
-    intro s hl
-    rw [List.any_cons] at hl
-    cases a <;>
-      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
-      first
-        | rfl
-        | exact ih _ hl
-
-/-- When no term is unclassifiable, running the loop from the zero state drives
-the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
-the post-loop decision with those values. -/
-theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
-      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
-  suffices key : ∀ (l : List Summand) (s : LoopState),
-      l.any isUnclassified = false →
-      loopRec terms.length realSumZero l s
-        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
-            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
-    have := key terms ⟨0, 0, false, false⟩ h
-    simpa using this
-  intro l
-  induction l with
-  | nil => intro s _; simp [loopRec]
-  | cons a t ih =>
-    intro s hany
-    cases a <;>
-      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
-        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
-        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
-    case realUnknown => exact absurd hany.1 (by decide)
-    case indeterminate => exact absurd hany.1 (by decide)
-    all_goals
-      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
-        Nat.add_assoc, Nat.add_right_comm])
-
-/-- In the classified case, the post-loop decision applied to the aggregates
-equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
-theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
-    (h : terms.any isUnclassified = false) :
-    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
-        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
-      = zeroVerdict terms realSumZero := by
-  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]
-
 theorem correct_zeroStatus :
     ∀ (terms : List Summand) (realSumZero : Option Bool),
       problem_spec_zeroStatus terms realSumZero
         (implementation_zeroStatus terms realSumZero) := by
   intro terms realSumZero
-  unfold problem_spec_zeroStatus
-  by_cases h : terms.any isUnclassified = true
-  · rw [shortcircuit_iff terms realSumZero h]
-    simp only [zeroVerdict, h, if_true]
-  · have h' : terms.any isUnclassified = false := by
-      simpa using h
-    rw [forIn_unfold terms realSumZero,
-        final_state_aggregates terms realSumZero h',
-        decision_cascade_agree terms realSumZero h']
-
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a finite sum of terms is definitely zero, definitely nonzero,
or undetermined — a three-valued verdict (`some true` / `some false` / `none`).

Each term is pre-classified by where it lives:

* `realZero`     — a real term already known to be zero;
* `realNonzero`  — a real term known to be nonzero;
* `realUnknown`  — a real term whose zero-ness cannot be settled;
* `imaginary`    — a purely imaginary (nonzero) term;
* `imagOrZero`   — a term that is either purely imaginary or zero (its product
                   with the imaginary unit is real), but which is not pinned to
                   be purely imaginary;
* `indeterminate`— a term that fits none of the above categories.

The verdict must be *sound*: it may answer `none` (undetermined) whenever it
cannot be sure, but every definite zero/nonzero answer it gives must hold. The
decision also consumes one auxiliary three-valued fact —
`realSumZero`, whether the combined sum of just the definitely-nonzero real
terms is itself zero — since cancellation among those terms can still occur.

The governing principle this captures: when every term is real and zero the sum
is zero; when there is no definitely-nonzero real term to anchor the real part
(or every term is such a term), no definite verdict about the whole sum is
warranted and the answer must stay undetermined; otherwise the real anchor plus
the imaginary content jointly decide the outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Each term's category is supplied as
-- an input classification (`Summand`), and the three-valued zero-test of the
-- real anchor sub-sum is supplied as the input `realSumZero`, so the verdict is
-- grounded directly in the inputs and the proof needs no callee contract.
-- (G-AX is a skip stub.)
-- axioms-end

-- pure-start
/-- Category of a single summand (see module docstring). -/
inductive Summand
  | realZero
  | realNonzero
  | realUnknown
  | imaginary
  | imagOrZero
  | indeterminate
deriving DecidableEq, Repr

/-- A real term whose zero-ness cannot be decided, or a wholly unclassifiable
term: either forces the overall verdict to be undetermined. -/
def isUnclassified : Summand → Bool
  | .realUnknown => true
  | .indeterminate => true
  | _ => false

def isRealZero : Summand → Bool
  | .realZero => true
  | _ => false

def isRealNonzero : Summand → Bool
  | .realNonzero => true
  | _ => false

def isImag : Summand → Bool
  | .imaginary => true
  | _ => false

def isImagOrZero : Summand → Bool
  | .imagOrZero => true
  | _ => false

/-- The sound three-valued zero-verdict for the whole sum, as a total function
of the term categories and the real-anchor fact `realSumZero`. -/
def zeroVerdict (terms : List Summand) (realSumZero : Option Bool) : Option Bool :=
  if terms.any isUnclassified then
    none
  else
    let z := terms.countP isRealZero
    let nz := terms.countP isRealNonzero
    let n := terms.length
    let im := terms.any isImag
    let imOrZ := terms.any isImagOrZero
    if z == n then
      some true
    else if nz == 0 || nz == n then
      none
    else
      match realSumZero with
      | some true =>
          if !imOrZ && !im then some true
          else if im && !imOrZ then some false
          else none
      | some false => some false
      | none => none
-- pure-end

-- post-conditions-start
/-- The result is exactly the sound three-valued zero-verdict determined by the
term categories and the real-anchor fact. This pins every case: a sum of only
real-zero terms is zero; a sum with no definitely-nonzero real anchor (or made
up entirely of such terms) is undetermined; otherwise the anchor combined with
the imaginary content decides, and any presence of an undecidable real term or
an unclassifiable term forces `none`. -/
def problem_spec_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) (result : Option Bool) : Prop :=
  result = zeroVerdict terms realSumZero
-- post-conditions-end

-- impl-start
def implementation_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) : Option Bool := Id.run do
  let mut z := 0
  let mut nz := 0
  let mut im := false
  let mut imOrZ := false
  for a in terms do
    match a with
    | .realZero => z := z + 1
    | .realNonzero => nz := nz + 1
    | .realUnknown => return none
    | .imaginary => im := true
    | .imagOrZero => imOrZ := true
    | .indeterminate => return none
  if z == terms.length then
    return some true
  if nz == 0 || nz == terms.length then
    return none
  match realSumZero with
  | some true =>
      if !imOrZ && !im then
        return some true
      if im && !imOrZ then
        return some false
  | some false => return some false
  | none => pure ()
  return none
-- impl-end


-- proof-start
/-- The mutable state tracked by the imperative loop: the running counts of
real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
imaginary-or-zero (`imOrZ`) presence flags. -/
structure LoopState where
  z : Nat
  nz : Nat
  im : Bool
  imOrZ : Bool

/-- Pure model of the loop body: updates the accumulator for a classified term,
or signals early exit (`none`) on an unclassifiable term. -/
def stepState (s : LoopState) (a : Summand) : Option LoopState :=
  match a with
  | .realZero => some { s with z := s.z + 1 }
  | .realNonzero => some { s with nz := s.nz + 1 }
  | .realUnknown => none
  | .imaginary => some { s with im := true }
  | .imagOrZero => some { s with imOrZ := true }
  | .indeterminate => none

/-- Pure model of the implementation's post-loop decision cascade. Structurally
identical to the `else`-branch of `zeroVerdict`. -/
def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
  if s.z == n then some true
  else if s.nz == 0 || s.nz == n then none
  else
    match realSumZero with
    | some true =>
        if !s.imOrZ && !s.im then some true
        else if s.im && !s.imOrZ then some false
        else none
    | some false => some false
    | none => none

/-- Pure recursive model of the whole imperative computation: fold the loop body
over the list (short-circuiting to `none` on an unclassifiable term), then apply
the post-loop decision at the empty tail. -/
def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
  | [], s => postDecide s n realSumZero
  | a :: l, s =>
      match stepState s a with
      | none => none
      | some s' => loopRec n realSumZero l s'
/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
flags and the `nz`, `z` counts, in the exact order Lean packs them
(`⟨slot, im, imOrZ, nz, z⟩`). -/
abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))

/-- Refinement map from the packed loop state to the model `LoopState`,
dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩

/-- Pure model of the elaborated loop body: the accumulating constructors
`yield` a slot-`none` state with one field bumped; the two unclassifiable
constructors `done` with the slot set to `some none` (early return). -/
def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
  match a with
  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩

/-- Pure model of the elaborated post-loop projection + decision cascade:
if the early-return slot is set (`some a`) return `a`; otherwise run the same
`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
  match p.1 with
  | some a => a
  | none =>
      if p.2.2.2.2 == n then some true
      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
      else match realSumZero with
        | some true =>
            if !p.2.2.1 && !p.2.1 then some true
            else if p.2.1 && !p.2.2.1 then some false
            else none
        | some false => some false
        | none => none

/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))

/-- Base unfold of the full computation: an empty suffix runs only the
post-loop cascade. -/
theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl

/-- One-step unfold of the full computation: run the body on the head; on
`yield` recurse on the tail, on `done` short-circuit into the post-loop
cascade. -/
theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
    (l : List Summand) (p : PS) :
    runFrom n realSumZero (a :: l) p
      = (match forInBodyPS a p with
          | ForInStep.yield p' => runFrom n realSumZero l p'
          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl

/-- With the early-return slot empty, the post-loop cascade coincides with
`postDecide` on the projected model state. -/
theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
    (h : p.1 = none) :
    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
  unfold postLoopPS postDecide toLS
  rw [h]

/-- With the early-return slot set to `some r`, the post-loop cascade returns
`r` directly (the early return short-circuits the decision). -/
theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
    (r : Option Bool) (h : p.1 = some r) :
    postLoopPS n realSumZero p = r := by
  unfold postLoopPS
  rw [h]

/-- Per-constructor lockstep between the elaborated body and `stepState`: an
accumulating constructor (`stepState = some s'`) yields a slot-`none` state
whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
emits `done` with the slot set to `some none`. -/
theorem toLS_step_agree (a : Summand) (p : PS) :
    (∀ s', stepState (toLS p) a = some s' →
        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
    (stepState (toLS p) a = none →
        forInBodyPS a p
          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
  constructor
  · intro s' h
    cases a <;>
      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
      subst h <;>
      rfl
  · intro h
    cases a <;>
      simp_all [stepState, toLS, forInBodyPS]

/-- The semantic core: for every suffix `l` and every packed state `p` whose
early-return slot is empty, the full computation equals the pure model
`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
casing on the head constructor so the elaborated body reduces in lockstep with
`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
the accumulating `yield`s. -/
theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
    (l : List Summand) (p : PS) (h : p.1 = none) :
    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
  induction l generalizing p with
  | nil =>
    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
    rfl
  | cons a l' ih =>
    rw [runFrom_cons]
    have hstep := toLS_step_agree a p
    cases hs : stepState (toLS p) a with
    | none =>
      have hbody := hstep.2 hs
      rw [hbody]
      simp only []
      rw [postLoop_slot_some n realSumZero _ none rfl]
      simp only [loopRec, hs]
    | some s' =>
      have hbody := hstep.1 s' hs
      rw [hbody]
      simp only []
      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
      rw [ih _ hp1]
      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
        cases s'; rfl
      rw [htols]
      simp only [loopRec, hs]

/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
packed state (slot empty, all counters/flags zero). -/
theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
    implementation_zeroStatus terms realSumZero
      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
  congr 1
  congr 1
  funext r
  rcases hr : r.fst with _ | _ <;> rfl

/-- Reify the imperative `for` loop (with early `return none`) as the pure
recursion `loopRec`, started from the zero state. -/
theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
    implementation_zeroStatus terms realSumZero
      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
  rw [impl_eq_runFrom_init,
      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
  rfl

/-- The loop returns `none` whenever some term is unclassifiable, matching the
outer guard of `zeroVerdict`. -/
theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = true) :
    implementation_zeroStatus terms realSumZero = none := by
  rw [forIn_unfold]
  suffices H : ∀ (l : List Summand) (s : LoopState),
      l.any isUnclassified = true →
      loopRec terms.length realSumZero l s = none by
    exact H terms _ h
  intro l
  induction l with
  | nil => intro s hl; simp [List.any_nil] at hl
  | cons a l ih =>
    intro s hl
    rw [List.any_cons] at hl
    cases a <;>
      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
      first
        | rfl
        | exact ih _ hl

/-- When no term is unclassifiable, running the loop from the zero state drives
the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
the post-loop decision with those values. -/
theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = false) :
    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
  suffices key : ∀ (l : List Summand) (s : LoopState),
      l.any isUnclassified = false →
      loopRec terms.length realSumZero l s
        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
    have := key terms ⟨0, 0, false, false⟩ h
    simpa using this
  intro l
  induction l with
  | nil => intro s _; simp [loopRec]
  | cons a t ih =>
    intro s hany
    cases a <;>
      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
    case realUnknown => exact absurd hany.1 (by decide)
    case indeterminate => exact absurd hany.1 (by decide)
    all_goals
      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
        Nat.add_assoc, Nat.add_right_comm])

/-- In the classified case, the post-loop decision applied to the aggregates
equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = false) :
    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
      = zeroVerdict terms realSumZero := by
  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]

theorem correct_zeroStatus :
    ∀ (terms : List Summand) (realSumZero : Option Bool),
      problem_spec_zeroStatus terms realSumZero
        (implementation_zeroStatus terms realSumZero) := by
  intro terms realSumZero
  unfold problem_spec_zeroStatus
  by_cases h : terms.any isUnclassified = true
  · rw [shortcircuit_iff terms realSumZero h]
    simp only [zeroVerdict, h, if_true]
  · have h' : terms.any isUnclassified = false := by
      simpa using h
    rw [forIn_unfold terms realSumZero,
        final_state_aggregates terms realSumZero h',
        decision_cascade_agree terms realSumZero h']

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: pure exact-equality (result = zeroVerdict terms realSumZero), proved by ∀. There are NO A-legs: meta.json has axioms=[], opaque_callees=[], deep_model_references=[]; axiom_check.py is a genuine skip stub (nothing to validate); #print axioms on atk_7 = 'does not depend on any axioms', on pos_control = [propext, Quot.sound] (standard sound Lean axioms only — clean). refinement.md audit: all 14 legs tagged R or I, no kind-3; the sole nontrivial modeling (realSumZero:Option Bool standing in for self.func(*nz).is_zero) is a legitimate R grounded in inputs and exercised end-to-end by G-CONF (112636 checks, 0 disagreements). The correspondence to the real callee Add._eval_is_zero holds.

### ATTACK BATTERY (all same_spec=True, confirmed via swebench_unified.markers.same_spec):
- atk_1: prepatch bug — drop the `nz == 0 ||` disjunct (the exact pre-fix line). VERIFY: `bash scripts/lean_verify.sh atk_1.lean` -> exit=1 (does NOT verify). Prepatch bug reproduced.
- atk_2: swap some true/some false in the realSumZero=some true imaginary branch. exit=1.
- atk_3: partial-domain — (some false) branch returns none instead of some false. exit=1.
- atk_4: boundary off-by-one — `z + 1 == terms.length` instead of `z == terms.length`. exit=1.
- atk_5: control-flow-effect — .imagOrZero sets im instead of imOrZ. exit=1.
- atk_6: null-effect — drop the entire realSumZero decision cascade (always fall to return none). exit=1.
- atk_7: ungrounded-oracle echo — implementation_zeroStatus := zeroVerdict terms realSumZero; proof `rfl`. exit=0 (VERIFIES). #print axioms: does not depend on any axioms (clean).
- pos_control (Solution.lean unchanged): `bash scripts/lean_verify.sh pos_control.lean` -> exit=0 (verifies); #print axioms clean [propext, Quot.sound].

All lean_verify runs launched concurrently as background jobs (≤4 at a time).

MANDATORY RESOLVE STEP: atk_7 is the ONLY verifying attack. It is a behaviorally-exact echo of zeroVerdict (= gold behavior), so its faithful refined patch IS the gold patch (the `len(nz) == 0 or` fix, add.py:554-556). Materialized to atk_7_patch.diff and RUN through the official harness. run_resolve wrapper twice returned COMPLETED=False (harness error / image-pull failure) purely from infrastructure contention (instance image not built locally + ~20 long-running containers, some 25-31h). Ran the harness DIRECTLY via `... swebench_unified.run_evaluation --run_id sbu-manual-15875-atk7 --instance_ids sympy__sympy-15875 ...`: EXECUTED RESULT = 'Instances resolved: 1' / resolved_ids: [sympy__sympy-15875] (report sbu_patch.sbu-manual-15875-atk7.json). So the one verifying same-spec impl's faithful patch RESOLVES — per the echo-attack policy (G-PANEL-1/EQ resolve check) a resolving echo of gold is NOT a weakness.

CONCLUSION: No behaviorally-wrong same-spec impl closes a clean-axiom proof (the exact-equality spec forecloses it). The only closing same-spec impl (atk_7) resolves. ≥5 distinct wrong impls (partial-domain, boundary, control-flow-effect, oracle-echo, prepatch, sign-swap) attempted, none breaks the spec. Positive control verifies. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is an EXACT-EQUALITY spec: problem_spec_zeroStatus terms realSumZero result := (result = zeroVerdict terms realSumZero), and correct_zeroStatus proves it for ALL (terms, realSumZero). Any impl that differs from zeroVerdict on even one input cannot close the proof in a consistent logic. Concretely, terms=[imaginary, imaginary], realSumZero=some true discriminates the prepatch bug (zeroVerdict=none vs prepatch=some false), and none of atk_1..atk_6 could close.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a finite sum of terms is definitely zero, definitely nonzero,
or undetermined — a three-valued verdict (`some true` / `some false` / `none`).

Each term is pre-classified by where it lives:

* `realZero`     — a real term already known to be zero;
* `realNonzero`  — a real term known to be nonzero;
* `realUnknown`  — a real term whose zero-ness cannot be settled;
* `imaginary`    — a purely imaginary (nonzero) term;
* `imagOrZero`   — a term that is either purely imaginary or zero (its product
                   with the imaginary unit is real), but which is not pinned to
                   be purely imaginary;
* `indeterminate`— a term that fits none of the above categories.

The verdict must be *sound*: it may answer `none` (undetermined) whenever it
cannot be sure, but every definite zero/nonzero answer it gives must hold. The
decision also consumes one auxiliary three-valued fact —
`realSumZero`, whether the combined sum of just the definitely-nonzero real
terms is itself zero — since cancellation among those terms can still occur.

The governing principle this captures: when every term is real and zero the sum
is zero; when there is no definitely-nonzero real term to anchor the real part
(or every term is such a term), no definite verdict about the whole sum is
warranted and the answer must stay undetermined; otherwise the real anchor plus
the imaginary content jointly decide the outcome.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Each term's category is supplied as
-- an input classification (`Summand`), and the three-valued zero-test of the
-- real anchor sub-sum is supplied as the input `realSumZero`, so the verdict is
-- grounded directly in the inputs and the proof needs no callee contract.
-- (G-AX is a skip stub.)
-- axioms-end

-- pure-start
/-- Category of a single summand (see module docstring). -/
inductive Summand
  | realZero
  | realNonzero
  | realUnknown
  | imaginary
  | imagOrZero
  | indeterminate
deriving DecidableEq, Repr

/-- A real term whose zero-ness cannot be decided, or a wholly unclassifiable
term: either forces the overall verdict to be undetermined. -/
def isUnclassified : Summand → Bool
  | .realUnknown => true
  | .indeterminate => true
  | _ => false

def isRealZero : Summand → Bool
  | .realZero => true
  | _ => false

def isRealNonzero : Summand → Bool
  | .realNonzero => true
  | _ => false

def isImag : Summand → Bool
  | .imaginary => true
  | _ => false

def isImagOrZero : Summand → Bool
  | .imagOrZero => true
  | _ => false

/-- The sound three-valued zero-verdict for the whole sum, as a total function
of the term categories and the real-anchor fact `realSumZero`. -/
def zeroVerdict (terms : List Summand) (realSumZero : Option Bool) : Option Bool :=
  if terms.any isUnclassified then
    none
  else
    let z := terms.countP isRealZero
    let nz := terms.countP isRealNonzero
    let n := terms.length
    let im := terms.any isImag
    let imOrZ := terms.any isImagOrZero
    if z == n then
      some true
    else if nz == 0 || nz == n then
      none
    else
      match realSumZero with
      | some true =>
          if !imOrZ && !im then some true
          else if im && !imOrZ then some false
          else none
      | some false => some false
      | none => none
-- pure-end

-- post-conditions-start
/-- The result is exactly the sound three-valued zero-verdict determined by the
term categories and the real-anchor fact. This pins every case: a sum of only
real-zero terms is zero; a sum with no definitely-nonzero real anchor (or made
up entirely of such terms) is undetermined; otherwise the anchor combined with
the imaginary content decides, and any presence of an undecidable real term or
an unclassifiable term forces `none`. -/
def problem_spec_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) (result : Option Bool) : Prop :=
  result = zeroVerdict terms realSumZero
-- post-conditions-end

-- impl-start
def implementation_zeroStatus
    (terms : List Summand) (realSumZero : Option Bool) : Option Bool := Id.run do
  let mut z := 0
  let mut nz := 0
  let mut im := false
  let mut imOrZ := false
  for a in terms do
    match a with
    | .realZero => z := z + 1
    | .realNonzero => nz := nz + 1
    | .realUnknown => return none
    | .imaginary => im := true
    | .imagOrZero => imOrZ := true
    | .indeterminate => return none
  if z == terms.length then
    return some true
  if nz == 0 || nz == terms.length then
    return none
  match realSumZero with
  | some true =>
      if !imOrZ && !im then
        return some true
      if im && !imOrZ then
        return some false
  | some false => return some false
  | none => pure ()
  return none
-- impl-end


-- proof-start
/-- The mutable state tracked by the imperative loop: the running counts of
real-zero (`z`) and real-nonzero (`nz`) terms, and the imaginary (`im`) /
imaginary-or-zero (`imOrZ`) presence flags. -/
structure LoopState where
  z : Nat
  nz : Nat
  im : Bool
  imOrZ : Bool

/-- Pure model of the loop body: updates the accumulator for a classified term,
or signals early exit (`none`) on an unclassifiable term. -/
def stepState (s : LoopState) (a : Summand) : Option LoopState :=
  match a with
  | .realZero => some { s with z := s.z + 1 }
  | .realNonzero => some { s with nz := s.nz + 1 }
  | .realUnknown => none
  | .imaginary => some { s with im := true }
  | .imagOrZero => some { s with imOrZ := true }
  | .indeterminate => none

/-- Pure model of the implementation's post-loop decision cascade. Structurally
identical to the `else`-branch of `zeroVerdict`. -/
def postDecide (s : LoopState) (n : Nat) (realSumZero : Option Bool) : Option Bool :=
  if s.z == n then some true
  else if s.nz == 0 || s.nz == n then none
  else
    match realSumZero with
    | some true =>
        if !s.imOrZ && !s.im then some true
        else if s.im && !s.imOrZ then some false
        else none
    | some false => some false
    | none => none

/-- Pure recursive model of the whole imperative computation: fold the loop body
over the list (short-circuiting to `none` on an unclassifiable term), then apply
the post-loop decision at the empty tail. -/
def loopRec (n : Nat) (realSumZero : Option Bool) : List Summand → LoopState → Option Bool
  | [], s => postDecide s n realSumZero
  | a :: l, s =>
      match stepState s a with
      | none => none
      | some s' => loopRec n realSumZero l s'
/-- The REAL elaborated loop-state type threaded by the desugared `for` loop:
the early-return slot (`Option (Option Bool)`) bundled with the `im`, `imOrZ`
flags and the `nz`, `z` counts, in the exact order Lean packs them
(`⟨slot, im, imOrZ, nz, z⟩`). -/
abbrev PS := MProd (Option (Option Bool)) (MProd Bool (MProd Bool (MProd Nat Nat)))

/-- Refinement map from the packed loop state to the model `LoopState`,
dropping the early-return slot. `PS` is `⟨slot, im, imOrZ, nz, z⟩`;
`LoopState` is `⟨z, nz, im, imOrZ⟩`. -/
def toLS (p : PS) : LoopState := ⟨p.2.2.2.2, p.2.2.2.1, p.2.1, p.2.2.1⟩

/-- Pure model of the elaborated loop body: the accumulating constructors
`yield` a slot-`none` state with one field bumped; the two unclassifiable
constructors `done` with the slot set to `some none` (early return). -/
def forInBodyPS (a : Summand) (p : PS) : ForInStep PS :=
  match a with
  | .realZero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2 + 1⟩
  | .realNonzero => ForInStep.yield ⟨none, p.2.1, p.2.2.1, p.2.2.2.1 + 1, p.2.2.2.2⟩
  | .realUnknown => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
  | .imaginary => ForInStep.yield ⟨none, true, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩
  | .imagOrZero => ForInStep.yield ⟨none, p.2.1, true, p.2.2.2.1, p.2.2.2.2⟩
  | .indeterminate => ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩

/-- Pure model of the elaborated post-loop projection + decision cascade:
if the early-return slot is set (`some a`) return `a`; otherwise run the same
`z==n / nz==0∨nz==n / realSumZero` cascade as `postDecide`. -/
def postLoopPS (n : Nat) (realSumZero : Option Bool) (p : PS) : Option Bool :=
  match p.1 with
  | some a => a
  | none =>
      if p.2.2.2.2 == n then some true
      else if p.2.2.2.1 == 0 || p.2.2.2.1 == n then none
      else match realSumZero with
        | some true =>
            if !p.2.2.1 && !p.2.1 then some true
            else if p.2.1 && !p.2.2.1 then some false
            else none
        | some false => some false
        | none => none

/-- The WHOLE `Option Bool`-valued computation continuing from suffix `l` and
packed state `p`: finish the `forIn` loop, then run the post-loop cascade. This
is what the generalized lemma equates to `loopRec` (NOT the bare `forIn`). -/
def runFrom (n : Nat) (realSumZero : Option Bool) (l : List Summand) (p : PS) : Option Bool :=
  Id.run (forIn l p (fun a r => pure (forInBodyPS a r)) >>= fun r => pure (postLoopPS n realSumZero r))

/-- Base unfold of the full computation: an empty suffix runs only the
post-loop cascade. -/
theorem runFrom_nil (n : Nat) (realSumZero : Option Bool) (p : PS) :
    runFrom n realSumZero [] p = postLoopPS n realSumZero p := rfl

/-- One-step unfold of the full computation: run the body on the head; on
`yield` recurse on the tail, on `done` short-circuit into the post-loop
cascade. -/
theorem runFrom_cons (n : Nat) (realSumZero : Option Bool) (a : Summand)
    (l : List Summand) (p : PS) :
    runFrom n realSumZero (a :: l) p
      = (match forInBodyPS a p with
          | ForInStep.yield p' => runFrom n realSumZero l p'
          | ForInStep.done p'' => postLoopPS n realSumZero p'') := by
  cases a <;> simp only [runFrom, forInBodyPS, List.forIn_cons] <;> rfl

/-- With the early-return slot empty, the post-loop cascade coincides with
`postDecide` on the projected model state. -/
theorem postLoop_slot_none (n : Nat) (realSumZero : Option Bool) (p : PS)
    (h : p.1 = none) :
    postLoopPS n realSumZero p = postDecide (toLS p) n realSumZero := by
  unfold postLoopPS postDecide toLS
  rw [h]

/-- With the early-return slot set to `some r`, the post-loop cascade returns
`r` directly (the early return short-circuits the decision). -/
theorem postLoop_slot_some (n : Nat) (realSumZero : Option Bool) (p : PS)
    (r : Option Bool) (h : p.1 = some r) :
    postLoopPS n realSumZero p = r := by
  unfold postLoopPS
  rw [h]

/-- Per-constructor lockstep between the elaborated body and `stepState`: an
accumulating constructor (`stepState = some s'`) yields a slot-`none` state
whose projection is `s'`; an unclassifiable constructor (`stepState = none`)
emits `done` with the slot set to `some none`. -/
theorem toLS_step_agree (a : Summand) (p : PS) :
    (∀ s', stepState (toLS p) a = some s' →
        forInBodyPS a p = ForInStep.yield ⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩) ∧
    (stepState (toLS p) a = none →
        forInBodyPS a p
          = ForInStep.done ⟨some none, p.2.1, p.2.2.1, p.2.2.2.1, p.2.2.2.2⟩) := by
  constructor
  · intro s' h
    cases a <;>
      simp only [stepState, toLS, forInBodyPS, Option.some.injEq, reduceCtorEq] at h ⊢ <;>
      subst h <;>
      rfl
  · intro h
    cases a <;>
      simp_all [stepState, toLS, forInBodyPS]

/-- The semantic core: for every suffix `l` and every packed state `p` whose
early-return slot is empty, the full computation equals the pure model
`loopRec` on the projected state. Proved by induction on `l` generalizing `p`,
casing on the head constructor so the elaborated body reduces in lockstep with
`stepState` (via `toLS_step_agree`); the slot-none invariant is preserved by
the accumulating `yield`s. -/
theorem loop_eq_loopRec_general (n : Nat) (realSumZero : Option Bool)
    (l : List Summand) (p : PS) (h : p.1 = none) :
    runFrom n realSumZero l p = loopRec n realSumZero l (toLS p) := by
  induction l generalizing p with
  | nil =>
    rw [runFrom_nil, postLoop_slot_none n realSumZero p h]
    rfl
  | cons a l' ih =>
    rw [runFrom_cons]
    have hstep := toLS_step_agree a p
    cases hs : stepState (toLS p) a with
    | none =>
      have hbody := hstep.2 hs
      rw [hbody]
      simp only []
      rw [postLoop_slot_some n realSumZero _ none rfl]
      simp only [loopRec, hs]
    | some s' =>
      have hbody := hstep.1 s' hs
      rw [hbody]
      simp only []
      have hp1 : (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS).1 = none := rfl
      rw [ih _ hp1]
      have htols : toLS (⟨none, s'.im, s'.imOrZ, s'.nz, s'.z⟩ : PS) = s' := by
        cases s'; rfl
      rw [htols]
      simp only [loopRec, hs]

/-- Expose the impl's outer `Id.run` as `runFrom` started from the real initial
packed state (slot empty, all counters/flags zero). -/
theorem impl_eq_runFrom_init (terms : List Summand) (realSumZero : Option Bool) :
    implementation_zeroStatus terms realSumZero
      = runFrom terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ := by
  simp only [implementation_zeroStatus, runFrom, postLoopPS, forInBodyPS, pure_bind]
  congr 1
  congr 1
  funext r
  rcases hr : r.fst with _ | _ <;> rfl

/-- Reify the imperative `for` loop (with early `return none`) as the pure
recursion `loopRec`, started from the zero state. -/
theorem forIn_unfold (terms : List Summand) (realSumZero : Option Bool) :
    implementation_zeroStatus terms realSumZero
      = loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩ := by
  rw [impl_eq_runFrom_init,
      loop_eq_loopRec_general terms.length realSumZero terms ⟨none, false, false, 0, 0⟩ rfl]
  rfl

/-- The loop returns `none` whenever some term is unclassifiable, matching the
outer guard of `zeroVerdict`. -/
theorem shortcircuit_iff (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = true) :
    implementation_zeroStatus terms realSumZero = none := by
  rw [forIn_unfold]
  suffices H : ∀ (l : List Summand) (s : LoopState),
      l.any isUnclassified = true →
      loopRec terms.length realSumZero l s = none by
    exact H terms _ h
  intro l
  induction l with
  | nil => intro s hl; simp [List.any_nil] at hl
  | cons a l ih =>
    intro s hl
    rw [List.any_cons] at hl
    cases a <;>
      simp only [isUnclassified, Bool.false_or, Bool.true_or, loopRec, stepState] at hl ⊢ <;>
      first
        | rfl
        | exact ih _ hl

/-- When no term is unclassifiable, running the loop from the zero state drives
the four counters/flags to exactly the four `zeroVerdict` aggregates, and reaches
the post-loop decision with those values. -/
theorem final_state_aggregates (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = false) :
    loopRec terms.length realSumZero terms ⟨0, 0, false, false⟩
      = postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
          terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero := by
  suffices key : ∀ (l : List Summand) (s : LoopState),
      l.any isUnclassified = false →
      loopRec terms.length realSumZero l s
        = postDecide ⟨s.z + l.countP isRealZero, s.nz + l.countP isRealNonzero,
            s.im || l.any isImag, s.imOrZ || l.any isImagOrZero⟩ terms.length realSumZero by
    have := key terms ⟨0, 0, false, false⟩ h
    simpa using this
  intro l
  induction l with
  | nil => intro s _; simp [loopRec]
  | cons a t ih =>
    intro s hany
    cases a <;>
      simp only [loopRec, stepState, isUnclassified, isRealZero, isRealNonzero,
        isImag, isImagOrZero, List.countP_cons, List.any_cons, Bool.or_eq_false_iff,
        Bool.false_eq_true, false_and, true_and, cond_true, cond_false] at hany ⊢
    case realUnknown => exact absurd hany.1 (by decide)
    case indeterminate => exact absurd hany.1 (by decide)
    all_goals
      (rw [ih _ hany]; congr 1 <;> simp [Bool.or_assoc, Nat.add_comm, Nat.add_left_comm,
        Nat.add_assoc, Nat.add_right_comm])

/-- In the classified case, the post-loop decision applied to the aggregates
equals the `else`-branch of `zeroVerdict` (the two cascades are identical). -/
theorem decision_cascade_agree (terms : List Summand) (realSumZero : Option Bool)
    (h : terms.any isUnclassified = false) :
    postDecide ⟨terms.countP isRealZero, terms.countP isRealNonzero,
        terms.any isImag, terms.any isImagOrZero⟩ terms.length realSumZero
      = zeroVerdict terms realSumZero := by
  simp only [zeroVerdict, h, Bool.false_eq_true, if_false, postDecide]

theorem correct_zeroStatus :
    ∀ (terms : List Summand) (realSumZero : Option Bool),
      problem_spec_zeroStatus terms realSumZero
        (implementation_zeroStatus terms realSumZero) := by
  intro terms realSumZero
  unfold problem_spec_zeroStatus
  by_cases h : terms.any isUnclassified = true
  · rw [shortcircuit_iff terms realSumZero h]
    simp only [zeroVerdict, h, if_true]
  · have h' : terms.any isUnclassified = false := by
      simpa using h
    rw [forIn_unfold terms realSumZero,
        final_state_aggregates terms realSumZero h',
        decision_cascade_agree terms realSumZero h']

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: pure exact-equality (result = zeroVerdict terms realSumZero), proved by ∀. There are NO A-legs: meta.json has axioms=[], opaque_callees=[], deep_model_references=[]; axiom_check.py is a genuine skip stub (nothing to validate); #print axioms on atk_7 = 'does not depend on any axioms', on pos_control = [propext, Quot.sound] (standard sound Lean axioms only — clean). refinement.md audit: all 14 legs tagged R or I, no kind-3; the sole nontrivial modeling (realSumZero:Option Bool standing in for self.func(*nz).is_zero) is a legitimate R grounded in inputs and exercised end-to-end by G-CONF (112636 checks, 0 disagreements). The correspondence to the real callee Add._eval_is_zero holds.

### ATTACK BATTERY (all same_spec=True, confirmed via swebench_unified.markers.same_spec):
- atk_1: prepatch bug — drop the `nz == 0 ||` disjunct (the exact pre-fix line). VERIFY: `bash scripts/lean_verify.sh atk_1.lean` -> exit=1 (does NOT verify). Prepatch bug reproduced.
- atk_2: swap some true/some false in the realSumZero=some true imaginary branch. exit=1.
- atk_3: partial-domain — (some false) branch returns none instead of some false. exit=1.
- atk_4: boundary off-by-one — `z + 1 == terms.length` instead of `z == terms.length`. exit=1.
- atk_5: control-flow-effect — .imagOrZero sets im instead of imOrZ. exit=1.
- atk_6: null-effect — drop the entire realSumZero decision cascade (always fall to return none). exit=1.
- atk_7: ungrounded-oracle echo — implementation_zeroStatus := zeroVerdict terms realSumZero; proof `rfl`. exit=0 (VERIFIES). #print axioms: does not depend on any axioms (clean).
- pos_control (Solution.lean unchanged): `bash scripts/lean_verify.sh pos_control.lean` -> exit=0 (verifies); #print axioms clean [propext, Quot.sound].

All lean_verify runs launched concurrently as background jobs (≤4 at a time).

MANDATORY RESOLVE STEP: atk_7 is the ONLY verifying attack. It is a behaviorally-exact echo of zeroVerdict (= gold behavior), so its faithful refined patch IS the gold patch (the `len(nz) == 0 or` fix, add.py:554-556). Materialized to atk_7_patch.diff and RUN through the official harness. run_resolve wrapper twice returned COMPLETED=False (harness error / image-pull failure) purely from infrastructure contention (instance image not built locally + ~20 long-running containers, some 25-31h). Ran the harness DIRECTLY via `... swebench_unified.run_evaluation --run_id sbu-manual-15875-atk7 --instance_ids sympy__sympy-15875 ...`: EXECUTED RESULT = 'Instances resolved: 1' / resolved_ids: [sympy__sympy-15875] (report sbu_patch.sbu-manual-15875-atk7.json). So the one verifying same-spec impl's faithful patch RESOLVES — per the echo-attack policy (G-PANEL-1/EQ resolve check) a resolving echo of gold is NOT a weakness.

CONCLUSION: No behaviorally-wrong same-spec impl closes a clean-axiom proof (the exact-equality spec forecloses it). The only closing same-spec impl (atk_7) resolves. ≥5 distinct wrong impls (partial-domain, boundary, control-flow-effect, oracle-echo, prepatch, sign-swap) attempted, none breaks the spec. Positive control verifies. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness break attack: no divergence found. Setup checks: Solution.lean compiles (lean_verify exit 0, only lint warnings); `#print axioms correct_zeroStatus` = [propext, Quot.sound] (no sorryAx, proof genuine); spec region byte-identical to Solution_prepatch.lean via swebench_unified.markers.same_spec (True). Modeled function = Add._eval_is_zero (sympy/core/add.py), commutative path, three-valued zero verdict. Worktree confirmed gold-patched (line 563: `if len(nz) == 0 or len(nz) == len(self.args): return None`). Ran the bundle conformance_check.py against the REAL patched callee: checked=112636, disagreements=0. Additionally hand-constructed the hard `b.is_zero is True` mixed branch (0<nz<n) via evaluate=False sums (a-a+I, 3-3+3*I+imag, 5-5+I*r) — all match. Ran a 300k evaluate=False fuzz stressing that branch: checked=291957, mismatches=0, with 10367 genuine hits on the `real_sum_zero is True` mixed case. Guard order (z==n before nz==0||nz==n) matches Python. Input abstractions legitimate: Summand = exact is_real/is_zero/is_imaginary/(I*a).is_real ladder; realSumZero = real self.func(*nz).is_zero. The spec is neither too strong nor drifted — it agrees with the real callee on every input tested including the issue witness [imaginary,imaginary]/some true -> none. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: single line in Add._eval_is_zero, `if len(nz) == len(self.args):` -> `if len(nz) == 0 or len(nz) == len(self.args):` in sympy/core/add.py. Public problem_statement discloses: is_zero wrongly returns False on -2*I+(1+I)**2 (should be None), 'never give the wrong answer', release note 'Fix is_zero becoming False on some expressions with Add'. The add.py file location is in hints_text only (off-limits) and is NOT echoed.

Spec-view checks (verified via swebench_unified.leakage.screen and manual review):
- Mechanical G-LEAK screen PASSES: no hard failures, no warnings. meta G-LEAK status=pass, relaxed_leakage=None (not a relaxed bundle, so no G-PANEL-3 deferral needed).
- No diff markers, no patched file path (sympy/core/add.py), no module path in spec view.
- Patched symbol _eval_is_zero (stripped: eval_is_zero) is not embedded in any spec identifier (zeroStatus, zeroVerdict, Summand, isRealZero, etc.) nor named in any comment/docstring.
- No narration words (bug/fix/wrong/regression/previously/incorrectly/broken/...) anywhere in the spec-view docstrings or comments. Docstrings describe behavior/soundness abstractly.
- The impl and proof regions are ELIDED in the spec view ('implementation elided'/'proof elided'); the actual gold (impl fix) is not shown.
- same_spec(Solution.lean, Solution_prepatch.lean)=True: spec region is byte-identical, bug lives only in elided impl.

The spec's zeroVerdict encodes the correct post-fix behavior (`else if nz == 0 || nz == n then none`), but this is the intended behavioral specification the framework necessarily provides, stated over an abstract Summand/Option Bool model with no reference to the repo, the diff, the pre-fix line, the existence of a bug, or the specific one-line edit. It does not reconstruct the gold edit beyond the already-public 'return None when it cannot decide' behavior. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
