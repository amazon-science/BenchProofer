# P2 adversarial audit — django__django-16100

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -41,7 +41,7 @@
   for f in steps do
     match f s with
     | .ok s'   => s := s'
-    | .error e => return (s0, some e)
+    | .error e => return (s, some e)
   return (s, none)
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -36,13 +36,8 @@
 
 -- impl-start
 def implementation_changelistView {σ E : Type}
-    (s0 : σ) (steps : List (σ → Except E σ)) : σ × Option E := Id.run do
-  let mut s := s0
-  for f in steps do
-    match f s with
-    | .ok s'   => s := s'
-    | .error e => return (s0, some e)
-  return (s, none)
+    (s0 : σ) (steps : List (σ → Except E σ)) : σ × Option E :=
+  (s0, none)
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   for f in steps do
     match f s with
     | .ok s'   => s := s'
-    | .error e => return (s0, some e)
+    | .error _ => pure ()
   return (s, none)
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
   for f in steps do
     match f s with
     | .ok s'   => s := s'
-    | .error e => return (s0, some e)
+    | .error _ => return (s0, none)
   return (s, none)
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -42,7 +42,7 @@
     match f s with
     | .ok s'   => s := s'
     | .error e => return (s0, some e)
-  return (s, none)
+  return (s0, none)
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -38,11 +38,14 @@
 def implementation_changelistView {σ E : Type}
     (s0 : σ) (steps : List (σ → Except E σ)) : σ × Option E := Id.run do
   let mut s := s0
+  let mut err : Option E := none
   for f in steps do
     match f s with
     | .ok s'   => s := s'
-    | .error e => return (s0, some e)
-  return (s, none)
+    | .error e => err := some e
+  match err with
+  | none   => return (s, none)
+  | some e => return (s0, some e)
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
A bulk-edit view processes a sequence of pending record updates. Each pending
update applies a sequence of writes to the shared data store and may fail
(raise). The desired behaviour is all-or-nothing: if every pending update
applies cleanly the store reflects all of them; if any update fails, the store
is observed in exactly its original state and the failure is reported.

The model abstracts each pending update as a single state-transition
`σ → Except E σ`: it either yields the next store state (the update committed)
or reports a failure value. `result = (storeState, maybeFailure)` records the
observable store state together with whether a failure propagated.
-/

-- axioms-start
-- No unchanged callee is axiomatized: each pending update is modeled deeply as
-- an input state-transition, so there is no consumed axiom and no opaque decl.
-- axioms-end

-- pure-start
/-- Apply a sequence of state-transitions front-to-back, short-circuiting on the
first failure. Returns the final state if all succeed, else the first failure. -/
def applyAll {σ E : Type} (s0 : σ) (steps : List (σ → Except E σ)) : Except E σ :=
  steps.foldl (fun acc f => acc.bind f) (Except.ok s0)
-- pure-end

-- post-conditions-start
def problem_spec_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) (result : σ × Option E) : Prop :=
  match applyAll s0 steps with
  | .ok sf    => result = (sf, none)
  | .error e  => result = (s0, some e)
-- post-conditions-end

-- impl-start
def implementation_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) : σ × Option E := Id.run do
  let mut s := s0
  for f in steps do
    match f s with
    | .ok s'   => s := s'
    | .error e => return (s0, some e)
  return (s, none)
-- impl-end


-- proof-start
/-- Explicit recursion mirroring the imperative loop body: `s0` is the fixed
rollback state, `acc` is the mutable loop state. On the first `.error` the loop
returns `(s0, some e)`; if all succeed it returns `(finalAcc, none)`. -/
def loopRec {σ E : Type} (s0 acc : σ) : List (σ → Except E σ) → σ × Option E
  | [] => (acc, none)
  | f :: rest =>
    match f acc with
    | .ok acc' => loopRec s0 acc' rest
    | .error e => (s0, some e)

theorem impl_eq_loopRec {σ E : Type} (s0 : σ) (steps : List (σ → Except E σ)) :
    implementation_changelistView s0 steps = loopRec s0 s0 steps := by
  have key : ∀ (acc : σ),
      (Id.run do
        let mut s := acc
        for f in steps do
          match f s with
          | .ok s'   => s := s'
          | .error e => return (s0, some e)
        return (s, none)) = loopRec s0 acc steps := by
    intro acc
    induction steps generalizing acc with
    | nil => rfl
    | cons f rest ih =>
      simp only [List.forIn_cons, Id.run, bind, pure, loopRec]
      cases hf : f acc with
      | ok s' => exact ih s'
      | error e => rfl
  unfold implementation_changelistView
  exact key s0

theorem applyAll_cons_step {σ E : Type} (acc : σ) (f : σ → Except E σ)
    (rest : List (σ → Except E σ)) :
    applyAll acc (f :: rest) =
      (match f acc with
       | .ok acc' => applyAll acc' rest
       | .error e => .error e) := by
  cases h : f acc with
  | ok acc' => simp [applyAll, List.foldl_cons, Except.bind, h]
  | error e =>
    simp only [applyAll, List.foldl_cons, Except.bind, h]
    induction rest with
    | nil => rfl
    | cons g gs ih => simpa using ih

theorem foldl_bind_error {σ E : Type} (e : E) (rest : List (σ → Except E σ)) :
    List.foldl (fun acc g => acc.bind g) (Except.error e) rest = Except.error e := by
  induction rest with
  | nil => rfl
  | cons g gs ih => simpa using ih

theorem loopRec_eq_closed {σ E : Type} (s0 acc : σ) (steps : List (σ → Except E σ)) :
    loopRec s0 acc steps =
      (match applyAll acc steps with
       | .ok sf   => (sf, none)
       | .error e => (s0, some e)) := by
  induction steps generalizing acc with
  | nil => simp [loopRec, applyAll]
  | cons f rest ih =>
    rw [applyAll_cons_step]
    show (match f acc with
          | .ok acc' => loopRec s0 acc' rest
          | .error e => (s0, some e)) = _
    cases h : f acc with
    | ok acc' => exact ih acc'
    | error e => rfl

theorem correct_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) :
    problem_spec_changelistView s0 steps
      (implementation_changelistView s0 steps) := by
  unfold problem_spec_changelistView
  rw [impl_eq_loopRec, loopRec_eq_closed]
  cases h : applyAll s0 steps with
  | ok sf => rfl
  | error e => rfl

-- proof-end

#print axioms correct_changelistView
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec is functional (total match on applyAll uniquely pins result per input), so no same-spec wrong impl can close correct_ ; no verifying wrong impl => no faithful patch to resolve-run.

### Evidence

same_spec True for all 6 attacks + pos_control (swebench_unified.markers.same_spec, lean backend).

Positive control (gold) pos_control.lean: exit 0; `#print axioms correct_changelistView` => [propext, Quot.sound] (clean, no sorryAx).

6 DISTINCT same-spec wrong impls, each carrying the verbatim gold proof machinery, ALL FAIL to close (exit 1, genuine 'Type mismatch' at the correct_ theorem, no accidental close):
- atk_1 exit=1: prepatch bug — partial state (s, some e) on error.
- atk_2 exit=1: ungrounded-oracle echo — (s0, none), ignores steps.
- atk_3 exit=1: control-flow-effect — skip failing steps, never report error.
- atk_4 exit=1: boundary — correct rollback state s0 but drops error tag => (s0, none).
- atk_5 exit=1: partial-domain — success path returns s0 (ignores accumulated state).
- atk_6 exit=1: last-error semantics — continue past errors, report LAST error.

DECISIVE FUNCTIONALITY PROOF (uniq2.lean, exit 0): `theorem spec_unique` closes with '`spec_unique` does not depend on any axioms'. Plus machine-checked concrete counterexamples on s0=0, steps=[fun s=>.ok(s+1), fun _=>.error 7]: applyAll = .error 7 (app_eval), gold-mandated result (0, some 7) satisfies spec; prepatch (1, some 7) and every (_,none) [(0,none),(1,none)] provably ¬satisfy spec. Since (σ,Option E) is uniquely determined, any verifying impl computes exactly the canonical all-or-nothing gold result => its faithful patch resolves. No verifying wrong impl exists, so patches={} (nothing to materialize/resolve-run) — not a skipped step.

refinement.md audit: 5 legs, all R (type refinement over universally-quantified input step-functions). No A-consumed, no A-reference, no I, NO kind-3 (changed-inexpressible). The transaction.atomic rollback is modeled DEEPLY as the spec's .error branch pinning result to (s0, some e) — a legitimate R modeling, not an axiomatized callee. axioms-start/end region declares no axiom/opaque (matches Solution.lean). No A-leg correspondence to break; the A-leg concern is vacuous here. prepatch_reproduced=true (atk_1 is the prepatch impl and provably violates the spec via the (1,some 7) counterexample; Solution_prepatch.lean carries this exact impl with a sorry).

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
A bulk-edit view processes a sequence of pending record updates. Each pending
update applies a sequence of writes to the shared data store and may fail
(raise). The desired behaviour is all-or-nothing: if every pending update
applies cleanly the store reflects all of them; if any update fails, the store
is observed in exactly its original state and the failure is reported.

The model abstracts each pending update as a single state-transition
`σ → Except E σ`: it either yields the next store state (the update committed)
or reports a failure value. `result = (storeState, maybeFailure)` records the
observable store state together with whether a failure propagated.
-/

-- axioms-start
-- No unchanged callee is axiomatized: each pending update is modeled deeply as
-- an input state-transition, so there is no consumed axiom and no opaque decl.
-- axioms-end

-- pure-start
/-- Apply a sequence of state-transitions front-to-back, short-circuiting on the
first failure. Returns the final state if all succeed, else the first failure. -/
def applyAll {σ E : Type} (s0 : σ) (steps : List (σ → Except E σ)) : Except E σ :=
  steps.foldl (fun acc f => acc.bind f) (Except.ok s0)
-- pure-end

-- post-conditions-start
def problem_spec_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) (result : σ × Option E) : Prop :=
  match applyAll s0 steps with
  | .ok sf    => result = (sf, none)
  | .error e  => result = (s0, some e)
-- post-conditions-end

-- impl-start
def implementation_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) : σ × Option E := Id.run do
  let mut s := s0
  for f in steps do
    match f s with
    | .ok s'   => s := s'
    | .error e => return (s0, some e)
  return (s, none)
-- impl-end


-- proof-start
/-- Explicit recursion mirroring the imperative loop body: `s0` is the fixed
rollback state, `acc` is the mutable loop state. On the first `.error` the loop
returns `(s0, some e)`; if all succeed it returns `(finalAcc, none)`. -/
def loopRec {σ E : Type} (s0 acc : σ) : List (σ → Except E σ) → σ × Option E
  | [] => (acc, none)
  | f :: rest =>
    match f acc with
    | .ok acc' => loopRec s0 acc' rest
    | .error e => (s0, some e)

theorem impl_eq_loopRec {σ E : Type} (s0 : σ) (steps : List (σ → Except E σ)) :
    implementation_changelistView s0 steps = loopRec s0 s0 steps := by
  have key : ∀ (acc : σ),
      (Id.run do
        let mut s := acc
        for f in steps do
          match f s with
          | .ok s'   => s := s'
          | .error e => return (s0, some e)
        return (s, none)) = loopRec s0 acc steps := by
    intro acc
    induction steps generalizing acc with
    | nil => rfl
    | cons f rest ih =>
      simp only [List.forIn_cons, Id.run, bind, pure, loopRec]
      cases hf : f acc with
      | ok s' => exact ih s'
      | error e => rfl
  unfold implementation_changelistView
  exact key s0

theorem applyAll_cons_step {σ E : Type} (acc : σ) (f : σ → Except E σ)
    (rest : List (σ → Except E σ)) :
    applyAll acc (f :: rest) =
      (match f acc with
       | .ok acc' => applyAll acc' rest
       | .error e => .error e) := by
  cases h : f acc with
  | ok acc' => simp [applyAll, List.foldl_cons, Except.bind, h]
  | error e =>
    simp only [applyAll, List.foldl_cons, Except.bind, h]
    induction rest with
    | nil => rfl
    | cons g gs ih => simpa using ih

theorem foldl_bind_error {σ E : Type} (e : E) (rest : List (σ → Except E σ)) :
    List.foldl (fun acc g => acc.bind g) (Except.error e) rest = Except.error e := by
  induction rest with
  | nil => rfl
  | cons g gs ih => simpa using ih

theorem loopRec_eq_closed {σ E : Type} (s0 acc : σ) (steps : List (σ → Except E σ)) :
    loopRec s0 acc steps =
      (match applyAll acc steps with
       | .ok sf   => (sf, none)
       | .error e => (s0, some e)) := by
  induction steps generalizing acc with
  | nil => simp [loopRec, applyAll]
  | cons f rest ih =>
    rw [applyAll_cons_step]
    show (match f acc with
          | .ok acc' => loopRec s0 acc' rest
          | .error e => (s0, some e)) = _
    cases h : f acc with
    | ok acc' => exact ih acc'
    | error e => rfl

theorem correct_changelistView {σ E : Type}
    (s0 : σ) (steps : List (σ → Except E σ)) :
    problem_spec_changelistView s0 steps
      (implementation_changelistView s0 steps) := by
  unfold problem_spec_changelistView
  rw [impl_eq_loopRec, loopRec_eq_closed]
  cases h : applyAll s0 steps with
  | ok sf => rfl
  | error e => rfl

-- proof-end

#print axioms correct_changelistView
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** Spec is functional (total match on applyAll uniquely pins result per input), so no same-spec wrong impl can close correct_ ; no verifying wrong impl => no faithful patch to resolve-run.

### Evidence

same_spec True for all 6 attacks + pos_control (swebench_unified.markers.same_spec, lean backend).

Positive control (gold) pos_control.lean: exit 0; `#print axioms correct_changelistView` => [propext, Quot.sound] (clean, no sorryAx).

6 DISTINCT same-spec wrong impls, each carrying the verbatim gold proof machinery, ALL FAIL to close (exit 1, genuine 'Type mismatch' at the correct_ theorem, no accidental close):
- atk_1 exit=1: prepatch bug — partial state (s, some e) on error.
- atk_2 exit=1: ungrounded-oracle echo — (s0, none), ignores steps.
- atk_3 exit=1: control-flow-effect — skip failing steps, never report error.
- atk_4 exit=1: boundary — correct rollback state s0 but drops error tag => (s0, none).
- atk_5 exit=1: partial-domain — success path returns s0 (ignores accumulated state).
- atk_6 exit=1: last-error semantics — continue past errors, report LAST error.

DECISIVE FUNCTIONALITY PROOF (uniq2.lean, exit 0): `theorem spec_unique` closes with '`spec_unique` does not depend on any axioms'. Plus machine-checked concrete counterexamples on s0=0, steps=[fun s=>.ok(s+1), fun _=>.error 7]: applyAll = .error 7 (app_eval), gold-mandated result (0, some 7) satisfies spec; prepatch (1, some 7) and every (_,none) [(0,none),(1,none)] provably ¬satisfy spec. Since (σ,Option E) is uniquely determined, any verifying impl computes exactly the canonical all-or-nothing gold result => its faithful patch resolves. No verifying wrong impl exists, so patches={} (nothing to materialize/resolve-run) — not a skipped step.

refinement.md audit: 5 legs, all R (type refinement over universally-quantified input step-functions). No A-consumed, no A-reference, no I, NO kind-3 (changed-inexpressible). The transaction.atomic rollback is modeled DEEPLY as the spec's .error branch pinning result to (s0, some e) — a legitimate R modeling, not an axiomatized callee. axioms-start/end region declares no axiom/opaque (matches Solution.lean). No A-leg correspondence to break; the A-leg concern is vacuous here. prepatch_reproduced=true (atk_1 is the prepatch impl and provably violates the spec via the (1,some 7) counterexample; Solution_prepatch.lean carries this exact impl with a sorry).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Setup independently re-verified: (1) lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). (2) #print axioms correct_changelistView -> [propext, Quot.sound] — clean, NO sorryAx; proof genuinely closes. (3) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) -> True; the frozen spec (axioms comment + applyAll in pure + post-conditions problem_spec_changelistView) is byte-identical between patched and prepatch.

Real repo check (base c6350d594c, django/contrib/admin/options.py:2011-2021): gold patch wraps the per-form save loop `for form in formset.forms: if form.has_changed(): save_form/save_model/save_related/construct_change_message/log_change; changecount+=1` in `with transaction.atomic(using=router.db_for_write(self.model)):`. Semantics = all-or-nothing: all forms save -> all writes commit; any raise -> whole block rolls back to pre-loop state and the exception propagates (loop short-circuits on the raise).

Model faithfulness, vector by vector: applyAll = left-fold of Except.bind (short-circuits on first .error, runs no later steps) matches the exception halting the loop; error branch pins result state to s0 (not partial s) matches atomic rollback — this is exactly the discriminating clause vs. prepatch which returns (s, some e); collapsing each form's multi-call save sequence into one step f is sound because a mid-form raise inside atomic also rolls the whole block back so only post-view observable state (=s0) matters; success path folds all steps -> all committed in order -> (sf, none); empty steps -> (s0, none) matches changecount=0.

Gold FAIL_TO_PASS test test_list_editable_atomicity confirms both discriminating cases: log_change side_effect=DatabaseError (form0 raises) -> both objects preserved = spec first-step .error -> (s0, some e); side_effect=[None, DatabaseError] (form0 commits, form1 raises) -> both STILL preserved = spec .ok,.error -> (s0, some e), form0's committed write rolled back. Both agree with the model.

The modeled function is universally quantified over sigma, E, and the step functions, so it is strictly MORE GENERAL than the concrete real callees; it cannot be stronger than the real function on the real inputs. Searched for a diverging input across all branches (empty, all-success, first-step error, mid-sequence error, within-form partial write) — none found; the spec matches the real patched behavior on every input. Spec is not too strong and does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (impl + proof elided) contains: de-narrated docstring, empty axioms comment, pure helper `applyAll` (foldl bind, short-circuit on first failure), and post-condition `problem_spec_changelistView` (.ok sf => (sf,none); .error e => (s0,some e)). same_spec(Solution, Solution_prepatch)=True under LeanBackend tables (spec region byte-identical; only impl `.error e => (s,some e)` vs `(s0,some e)` and the elided proof differ — correctly outside the spec region).

Leakage check vs PUBLIC problem_statement only (NOT hints): the problem_statement already states the fix and its rationale — 'Add transaction handling to Changelist list_editable processing ... it should be wrapped in a transaction to prevent unexpected states in case of errors.' The spec view's 'all-or-nothing: if any update fails, the store is observed in exactly its original state and the failure is reported', and the post-condition's rollback-to-s0 on error, are exactly the definitional semantics of a database transaction — an elaboration of the openly-disclosed fix, not new solution content. The gold edit is the discriminating boundary (rollback to s0 vs partial s), and that discriminating clause lives in the IMPL region, which is elided from the spec view. The view is fully de-narrated: it names no patched file/symbol (transaction.atomic, router.db_for_write, changelist_view, formset, Django admin) and is strictly more abstract/less identifying than the public problem_statement. No line in the spec view reconstructs the gold edit beyond the problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
