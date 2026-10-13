# P2 adversarial audit — django__django-14238

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing clean-axiom proof, so no falsifying (verify-but-not-resolve) impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,50 +58,33 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_subclassCheck {Cls : Type}
+def implementation_subclassCheck {Cls : Type} [DecidableEq Cls]
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
+  -- PRE-PATCH (buggy): accepts the candidate only when it is IDENTICAL to a
+  -- designated member class (membership by identity), instead of when it is a
+  -- subclass of a designated member. A class derived from a designated member is
+  -- therefore not recognized by this leg; only the inherited check could save it.
   let mut matched := false
   for d in subclasses do
-    if isSub subclass d then
+    if subclass = d then
       matched := true
   return matched || superCheck subclass
 -- impl-end
 
 -- proof-start
 theorem correct_subclassCheck :
-    ∀ {Cls : Type}
+    ∀ {Cls : Type} [DecidableEq Cls]
       (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
       (subclass : Cls) (subclasses : List Cls),
       problem_spec_subclassCheck isSub superCheck subclass subclasses
         (implementation_subclassCheck isSub superCheck subclass subclasses) := by
-  intro Cls isSub superCheck subclass subclasses
+  intro Cls _ isSub superCheck subclass subclasses
   unfold problem_spec_subclassCheck implementation_subclassCheck
-  have helper : ∀ (xs : List Cls) (init : Bool),
-      Id.run (forIn xs init (fun d r =>
-        (if isSub subclass d = true then pure (ForInStep.yield true)
-         else pure (ForInStep.yield r)) : Id _))
-      = (init || xs.any (fun d => isSub subclass d)) := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [Id.run, pure]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : isSub subclass a = true <;>
-        simp [h, ih, List.any_cons]
-  show Id.run _ = _
-  rw [show (Id.run (do
-      let r ← forIn subclasses false (fun d r =>
-        (if isSub subclass d = true then do pure PUnit.unit; pure (ForInStep.yield true)
-         else do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)
-      pure (r || superCheck subclass)) : Bool)
-    = (Id.run (forIn subclasses false (fun d r =>
-        (if isSub subclass d = true then pure (ForInStep.yield true)
-         else pure (ForInStep.yield r)) : Id _)) || superCheck subclass) from rfl]
-  rw [helper]
-  simp
+  simp only [Id.run]
+  induction subclasses with
+  | nil => rfl
+  | cons a as ih =>
+    rw [List.forIn_cons, List.any_cons]
+    simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,13 +61,7 @@
 def implementation_subclassCheck {Cls : Type}
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
-  let mut matched := false
-  for d in subclasses do
-    if isSub subclass d then
-      matched := true
-  return matched || superCheck subclass
+  return superCheck subclass
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,13 +61,11 @@
 def implementation_subclassCheck {Cls : Type}
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
   let mut matched := false
   for d in subclasses do
     if isSub subclass d then
       matched := true
-  return matched || superCheck subclass
+  return matched
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,13 +61,11 @@
 def implementation_subclassCheck {Cls : Type}
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
   let mut matched := false
   for d in subclasses do
     if isSub subclass d then
       matched := true
-  return matched || superCheck subclass
+  return matched && superCheck subclass
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,12 +61,9 @@
 def implementation_subclassCheck {Cls : Type}
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
-  let mut matched := false
-  for d in subclasses do
-    if isSub subclass d then
-      matched := true
+  let matched := match subclasses with
+    | [] => false
+    | d :: _ => isSub subclass d
   return matched || superCheck subclass
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,13 +61,11 @@
 def implementation_subclassCheck {Cls : Type}
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
   let mut matched := false
   for d in subclasses do
     if isSub subclass d then
       matched := true
-  return matched || superCheck subclass
+  return !(matched || superCheck subclass)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,13 +61,7 @@
 def implementation_subclassCheck {Cls : Type}
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
-  let mut matched := false
-  for d in subclasses do
-    if isSub subclass d then
-      matched := true
-  return matched || superCheck subclass
+  return true
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,11 +61,9 @@
 def implementation_subclassCheck {Cls : Type}
     (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
     (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
-  -- Accept the candidate if it is a subclass of any designated member class
-  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
   let mut matched := false
   for d in subclasses do
-    if isSub subclass d then
+    if isSub d subclass then
       matched := true
   return matched || superCheck subclass
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a candidate class should be treated as a subclass of a special
base class, where the base class designates a specific list of "member" classes that
are to be accepted in addition to whatever the ordinary type machinery already
accepts.

The decision combines two independent checks:

  * a check of the candidate against the designated member classes, and
  * the ordinary inherited subclass check.

The candidate is accepted when EITHER check accepts it.

The check against the designated members must accept not only each member class
itself but also any class derived from a member class: membership is judged by the
reflexive-transitive subclass relation, not by identity with a member. The
subclass relation and the ordinary inherited check are taken here as arbitrary
functions, so the behavior pinned below is exactly "the candidate is accepted iff
it is a subclass (in the reflexive-transitive sense) of one of the designated
members, or the inherited check accepts it."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The reflexive-transitive
-- subclass relation between two classes (`isSub`) and the ordinary inherited
-- subclass check (`superCheck`) are both modeled as arbitrary function
-- parameters: the modeled change is solely WHICH relation tests the candidate
-- against the designated member classes, so the result is pinned for every
-- possible subclass relation and inherited check. Hence the spec needs no
-- `opaque`/`axiom` callee contract. `Cls` is an abstract type of class objects;
-- classes are compared only through these relations.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the result is the disjunction of
-- "some designated member subsumes the candidate" and "the inherited check
-- accepts the candidate".
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the inputs:

  * `subclasses` is the designated list of member classes;
  * `isSub c d` is true when `c` is a subclass of `d` (reflexive-transitive);
  * `superCheck c` is the ordinary inherited check applied to `c`.

The candidate is accepted iff it is a subclass of SOME designated member, or the
inherited check accepts it. No output component is left free: the single boolean
result is pinned to the disjunction over the actual member list and the inherited
check applied to the actual candidate. -/
def problem_spec_subclassCheck {Cls : Type}
    (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
    (subclass : Cls) (subclasses : List Cls) (result : Bool) : Prop :=
  result = ((subclasses.any (fun d => isSub subclass d)) || superCheck subclass)
-- post-conditions-end

-- impl-start
def implementation_subclassCheck {Cls : Type}
    (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
    (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
  -- Accept the candidate if it is a subclass of any designated member class
  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
  let mut matched := false
  for d in subclasses do
    if isSub subclass d then
      matched := true
  return matched || superCheck subclass
-- impl-end

-- proof-start
theorem correct_subclassCheck :
    ∀ {Cls : Type}
      (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
      (subclass : Cls) (subclasses : List Cls),
      problem_spec_subclassCheck isSub superCheck subclass subclasses
        (implementation_subclassCheck isSub superCheck subclass subclasses) := by
  intro Cls isSub superCheck subclass subclasses
  unfold problem_spec_subclassCheck implementation_subclassCheck
  have helper : ∀ (xs : List Cls) (init : Bool),
      Id.run (forIn xs init (fun d r =>
        (if isSub subclass d = true then pure (ForInStep.yield true)
         else pure (ForInStep.yield r)) : Id _))
      = (init || xs.any (fun d => isSub subclass d)) := by
    intro xs
    induction xs with
    | nil => intro init; simp [Id.run, pure]
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : isSub subclass a = true <;>
        simp [h, ih, List.any_cons]
  show Id.run _ = _
  rw [show (Id.run (do
      let r ← forIn subclasses false (fun d r =>
        (if isSub subclass d = true then do pure PUnit.unit; pure (ForInStep.yield true)
         else do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)
      pure (r || superCheck subclass)) : Bool)
    = (Id.run (forIn subclasses false (fun d r =>
        (if isSub subclass d = true then pure (ForInStep.yield true)
         else pure (ForInStep.yield r)) : Id _)) || superCheck subclass) from rfl]
  rw [helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_subclassCheck is a FULLY-PINNED functional equality: result = (subclasses.any (fun d => isSub subclass d)) || superCheck subclass, with isSub and superCheck UNIVERSALLY QUANTIFIED arbitrary Bool-valued functions (no axioms consumed; A-legs are references only). Universal quantification is a strong constraint: the impl must equal the exact disjunction for EVERY relation/check, so any semantically distinct impl is unprovable.

Protocol executed (all in scratch dir, one backend):
Used python for same_spec.
- same_spec=True for all 8 attacks (axioms/pure/pre/post byte-identical; only impl region edited).
- Positive control (gold impl) pos_control.lean: lean_verify.sh exit 0. #print axioms correct_subclassCheck => [propext, Quot.sound] (clean, no sorryAx).
- 8 DISTINCT same-spec wrong impls, all lean_verify.sh exit 1 (proof fails to close):
atk_1 = prepatch bug (identity 'subclass = d' instead of reflexive-transitive isSub) — PREPATCH REPRODUCED, exit 1.
atk_2 = partial-domain: drop member check, return superCheck only — exit 1.
atk_3 = partial-domain: drop superCheck, return matched only — exit 1.
atk_4 = control-flow-effect: '&&' instead of '||' — exit 1.
atk_5 = boundary: only test head member, ignore tail — exit 1.
atk_6 = control-flow-effect: negate whole result (!(matched||superCheck)) — exit 1.
atk_7 = ungrounded-oracle echo: return true — exit 1.
atk_8 = swapped isSub args (isSub d subclass) — exit 1.

NO attack closed with clean axioms => step 2 (materialize faithful patch + run_resolve) has no candidates; the verify=>correct falsification condition is unreachable. patches={} accordingly.

refinement.md audit: all 5 legs are R (op2 iterate member tuple), I (op1 accumulator init, op5 return), or A-reference (op3 issubclass, op4 super().__subclasscheck__). No A-consumed (meta axioms=[], axiom_check is skip stub), no kind-3 ungrounded oracle. A-reference<->real-callee correspondence verified against conformance_check.py: isSub<->real builtin issubclass, superCheck<->real type.__subclasscheck__ bound to AutoField, oracle=issubclass(candidate, AutoField) dispatching through AutoFieldMeta.__subclasscheck__. Correspondence holds.

Verdict SOUND: >=5 (8) distinct same-spec attacks run, none closes a clean-axiom proof, so none can have a non-resolving patch. Spec faithfully pins the gold behavior.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl produced a closing clean-axiom proof, so no falsifying (verify-but-not-resolve) impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a candidate class should be treated as a subclass of a special
base class, where the base class designates a specific list of "member" classes that
are to be accepted in addition to whatever the ordinary type machinery already
accepts.

The decision combines two independent checks:

  * a check of the candidate against the designated member classes, and
  * the ordinary inherited subclass check.

The candidate is accepted when EITHER check accepts it.

The check against the designated members must accept not only each member class
itself but also any class derived from a member class: membership is judged by the
reflexive-transitive subclass relation, not by identity with a member. The
subclass relation and the ordinary inherited check are taken here as arbitrary
functions, so the behavior pinned below is exactly "the candidate is accepted iff
it is a subclass (in the reflexive-transitive sense) of one of the designated
members, or the inherited check accepts it."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The reflexive-transitive
-- subclass relation between two classes (`isSub`) and the ordinary inherited
-- subclass check (`superCheck`) are both modeled as arbitrary function
-- parameters: the modeled change is solely WHICH relation tests the candidate
-- against the designated member classes, so the result is pinned for every
-- possible subclass relation and inherited check. Hence the spec needs no
-- `opaque`/`axiom` callee contract. `Cls` is an abstract type of class objects;
-- classes are compared only through these relations.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the result is the disjunction of
-- "some designated member subsumes the candidate" and "the inherited check
-- accepts the candidate".
-- pure-end

-- post-conditions-start
/-- The result is fully pinned to the inputs:

  * `subclasses` is the designated list of member classes;
  * `isSub c d` is true when `c` is a subclass of `d` (reflexive-transitive);
  * `superCheck c` is the ordinary inherited check applied to `c`.

The candidate is accepted iff it is a subclass of SOME designated member, or the
inherited check accepts it. No output component is left free: the single boolean
result is pinned to the disjunction over the actual member list and the inherited
check applied to the actual candidate. -/
def problem_spec_subclassCheck {Cls : Type}
    (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
    (subclass : Cls) (subclasses : List Cls) (result : Bool) : Prop :=
  result = ((subclasses.any (fun d => isSub subclass d)) || superCheck subclass)
-- post-conditions-end

-- impl-start
def implementation_subclassCheck {Cls : Type}
    (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
    (subclass : Cls) (subclasses : List Cls) : Bool := Id.run do
  -- Accept the candidate if it is a subclass of any designated member class
  -- (reflexive-transitive subclass relation), or if the inherited check accepts.
  let mut matched := false
  for d in subclasses do
    if isSub subclass d then
      matched := true
  return matched || superCheck subclass
-- impl-end

-- proof-start
theorem correct_subclassCheck :
    ∀ {Cls : Type}
      (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
      (subclass : Cls) (subclasses : List Cls),
      problem_spec_subclassCheck isSub superCheck subclass subclasses
        (implementation_subclassCheck isSub superCheck subclass subclasses) := by
  intro Cls isSub superCheck subclass subclasses
  unfold problem_spec_subclassCheck implementation_subclassCheck
  have helper : ∀ (xs : List Cls) (init : Bool),
      Id.run (forIn xs init (fun d r =>
        (if isSub subclass d = true then pure (ForInStep.yield true)
         else pure (ForInStep.yield r)) : Id _))
      = (init || xs.any (fun d => isSub subclass d)) := by
    intro xs
    induction xs with
    | nil => intro init; simp [Id.run, pure]
    | cons a as ih =>
      intro init
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : isSub subclass a = true <;>
        simp [h, ih, List.any_cons]
  show Id.run _ = _
  rw [show (Id.run (do
      let r ← forIn subclasses false (fun d r =>
        (if isSub subclass d = true then do pure PUnit.unit; pure (ForInStep.yield true)
         else do pure PUnit.unit; pure (ForInStep.yield r)) : Id _)
      pure (r || superCheck subclass)) : Bool)
    = (Id.run (forIn subclasses false (fun d r =>
        (if isSub subclass d = true then pure (ForInStep.yield true)
         else pure (ForInStep.yield r)) : Id _)) || superCheck subclass) from rfl]
  rw [helper]
  simp
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_subclassCheck is a FULLY-PINNED functional equality: result = (subclasses.any (fun d => isSub subclass d)) || superCheck subclass, with isSub and superCheck UNIVERSALLY QUANTIFIED arbitrary Bool-valued functions (no axioms consumed; A-legs are references only). Universal quantification is a strong constraint: the impl must equal the exact disjunction for EVERY relation/check, so any semantically distinct impl is unprovable.

Protocol executed (all in scratch dir, one backend):
Used python for same_spec.
- same_spec=True for all 8 attacks (axioms/pure/pre/post byte-identical; only impl region edited).
- Positive control (gold impl) pos_control.lean: lean_verify.sh exit 0. #print axioms correct_subclassCheck => [propext, Quot.sound] (clean, no sorryAx).
- 8 DISTINCT same-spec wrong impls, all lean_verify.sh exit 1 (proof fails to close):
atk_1 = prepatch bug (identity 'subclass = d' instead of reflexive-transitive isSub) — PREPATCH REPRODUCED, exit 1.
atk_2 = partial-domain: drop member check, return superCheck only — exit 1.
atk_3 = partial-domain: drop superCheck, return matched only — exit 1.
atk_4 = control-flow-effect: '&&' instead of '||' — exit 1.
atk_5 = boundary: only test head member, ignore tail — exit 1.
atk_6 = control-flow-effect: negate whole result (!(matched||superCheck)) — exit 1.
atk_7 = ungrounded-oracle echo: return true — exit 1.
atk_8 = swapped isSub args (isSub d subclass) — exit 1.

NO attack closed with clean axioms => step 2 (materialize faithful patch + run_resolve) has no candidates; the verify=>correct falsification condition is unreachable. patches={} accordingly.

refinement.md audit: all 5 legs are R (op2 iterate member tuple), I (op1 accumulator init, op5 return), or A-reference (op3 issubclass, op4 super().__subclasscheck__). No A-consumed (meta axioms=[], axiom_check is skip stub), no kind-3 ungrounded oracle. A-reference<->real-callee correspondence verified against conformance_check.py: isSub<->real builtin issubclass, superCheck<->real type.__subclasscheck__ bound to AutoField, oracle=issubclass(candidate, AutoField) dispatching through AutoFieldMeta.__subclasscheck__. Correspondence holds.

Verdict SOUND: >=5 (8) distinct same-spec attacks run, none closes a clean-axiom proof, so none can have a non-resolving patch. Spec faithfully pins the gold behavior.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): no divergence found; verdict FAITHFUL.

Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, LeanBackend.language) == True. spec_view confirms the pinned post-condition is `result = ((subclasses.any (fun d => isSub subclass d)) || superCheck subclass)`.

Lean verification: scripts/lean_verify.sh Solution.lean exits 0 (compiles, no sorry). `#print axioms correct_subclassCheck` = [propext, Quot.sound] only — no sorryAx, proof is genuine.

Real callee @ base-commit worktree (django/db/models/fields/__init__.py:2718) post-patch:
    def __subclasscheck__(self, subclass):
        return issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)
with self._subclasses == (BigAutoField, SmallAutoField).

Semantic equivalence: Python `issubclass(c, (m0, m1))` is True iff issubclass(c,m0) or issubclass(c,m1), which is exactly `subclasses.any (fun d => isSub subclass d)` with isSub bound to real issubclass and subclasses = [BigAutoField, SmallAutoField]. The `or super().__subclasscheck__` disjunct maps to `|| superCheck subclass` with superCheck bound to the inherited type.__subclasscheck__. So the modeled function equals the real callee on every class-object input.

Empirical differential check against the REAL patched repo over the full candidate pool (AutoField, Big/SmallAutoField, user subclasses MyBig/MySmall, deeper Deep(MyBig), MyAuto, IntegerField, Field, unrelated Field subclass, object, int, str, CharField): oracle issubclass(c, AutoField) vs spec-shadow => 0 mismatches. The regression case (user subclass of a designated member) is accepted by both, confirming the fix behavior is faithfully captured.

No overconstraint: universally quantifying isSub/superCheck strengthens the THEOREM (holds for all relations) but the spec itself only pins the disjunction-over-actual-members || inherited-check, which is precisely the observable boolean. No output component left free, none over-pinned. axioms=[] is correct (proof consumes no property of the abstract parameters). No spec-too-strong drift detected.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified spec view directly via swebench_unified.markers.spec_view with LeanBackend.language, and same_spec(Solution, Solution_prepatch)=True. The spec region is byte-identical between the gold and prepatch twins, so the spec view CANNOT distinguish the gold impl from the buggy one — the discriminator lives entirely in the ELIDED impl region (`isSub subclass d` reflexive-transitive loop vs prepatch identity `subclass = d`). The spec view (docstring + post-condition) pins only: result = subclasses.any(fun d => isSub subclass d) || superCheck subclass, i.e. the candidate is accepted iff it is a reflexive-transitive subclass of some designated member OR the inherited check accepts. isSub and superCheck are universally-quantified abstract parameters; no Python callee (issubclass, self._subclasses, super().__subclasscheck__) or the token-level edit is named in the spec view — those appear only in mapping.md/refinement.md, which are NOT part of the spec view. The gold edit is `subclass in self._subclasses` -> `issubclass(subclass, self._subclasses)` (identity membership -> subclass relation). This is EXACTLY disclosed by the PUBLIC problem_statement, which ends: 'This can be fixed in AutoFieldMeta.__subclasscheck__ by allowing subclasses of those classes in the _subclasses property.' The spec view's 'reflexive-transitive subclass relation, not identity with a member' phrasing adds nothing beyond that public sentence. hints_text is empty, so nothing hinges on it. No spec-view line reveals the gold edit beyond the already-public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
