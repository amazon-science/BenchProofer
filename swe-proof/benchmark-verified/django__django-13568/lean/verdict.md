# P2 adversarial audit — django__django-13568

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_checkUserModel is a TOTAL functional equation pinning `result` to exactly one list per input assignment, so any impl whose correct_ closes is extensionally equal to gold. No closing-but-non-resolving alternative exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
       errors := errors ++ ["auth.E001"]
     if usernameInRequired then
       errors := errors ++ ["auth.E002"]
-    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
+    if !fieldUnique then
       if usesDefaultBackend then
         errors := errors ++ ["auth.E003"]
       else
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
       errors := errors ++ ["auth.E001"]
     if usernameInRequired then
       errors := errors ++ ["auth.E002"]
-    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
+    if !fieldUnique && !(constraints.any (fun c => c.isUnique && c.fields == [usernameField])) then
       if usesDefaultBackend then
         errors := errors ++ ["auth.E003"]
       else
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,15 +72,15 @@
       errors := errors ++ ["auth.E001"]
     if usernameInRequired then
       errors := errors ++ ["auth.E002"]
+    if isAnonymousMethod then
+      errors := errors ++ ["auth.C009"]
+    if isAuthenticatedMethod then
+      errors := errors ++ ["auth.C010"]
     if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
       if usesDefaultBackend then
         errors := errors ++ ["auth.E003"]
       else
         errors := errors ++ ["auth.W004"]
-    if isAnonymousMethod then
-      errors := errors ++ ["auth.C009"]
-    if isAuthenticatedMethod then
-      errors := errors ++ ["auth.C010"]
     return errors
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,10 +73,7 @@
     if usernameInRequired then
       errors := errors ++ ["auth.E002"]
     if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
-      if usesDefaultBackend then
-        errors := errors ++ ["auth.E003"]
-      else
-        errors := errors ++ ["auth.W004"]
+      errors := errors ++ ["auth.W004"]
     if isAnonymousMethod then
       errors := errors ++ ["auth.C009"]
     if isAuthenticatedMethod then
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
       errors := errors ++ ["auth.E001"]
     if usernameInRequired then
       errors := errors ++ ["auth.E002"]
-    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
+    if !fieldUnique && !(constraints.any (fun c => c.isUnique && !c.isConditional && c.fields.contains usernameField)) then
       if usesDefaultBackend then
         errors := errors ++ ["auth.E003"]
       else
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -72,7 +72,7 @@
       errors := errors ++ ["auth.E001"]
     if usernameInRequired then
       errors := errors ++ ["auth.E002"]
-    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
+    if !(fieldUnique || coveredByUnconditionalUniqueConstraint constraints usernameField) then
       if usesDefaultBackend then
         errors := errors ++ ["auth.E003"]
       else
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No callee needs an opaque signature here. The system check that validates a
-- user model accumulates a list of diagnostics from several independent
-- sub-checks; the outcomes of the structural sub-checks (the
-- required-fields-shape check, the required-fields-membership check, the chosen
-- authentication backend, and the two anonymous/authenticated attribute checks)
-- are taken as boolean inputs (a type-only refinement, refinement.md). The
-- decision of whether the login field is guaranteed unique is modeled DEEPLY
-- below over the declared model constraints, so no callee property is consumed.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The information about one declared model constraint that the login-field
uniqueness decision inspects: whether it is a uniqueness constraint, whether it
is conditional (applies only to a subset of rows), and the ordered tuple of
field names it ranges over. -/
structure ConstraintInfo where
  isUnique : Bool
  isConditional : Bool
  fields : List String
deriving DecidableEq

/-- The login field counts as guaranteed unique by a declared constraint when
some unconditional uniqueness constraint ranges over exactly that one field. A
conditional (partial) constraint, a non-uniqueness constraint, or a constraint
spanning a different set of fields does not count. -/
def coveredByUnconditionalUniqueConstraint
    (constraints : List ConstraintInfo) (field : String) : Bool :=
  constraints.any (fun c => c.isUnique && !c.isConditional && c.fields == [field])
-- pure-end

-- post-conditions-start
/-- The diagnostics produced when validating a user model, each represented by
its stable identifier code. The list is the in-order accumulation of the
independent sub-checks: a required-fields-shape diagnostic, a
required-fields-membership diagnostic, then — only when the login field is
neither directly unique nor guaranteed unique by a declared unconditional
uniqueness constraint over exactly that field — a uniqueness diagnostic whose
severity depends on whether the default authentication backend is in use (an
error there, otherwise a warning), and finally the two
anonymous/authenticated-attribute diagnostics. Each unchanged sub-check pins its
contribution to its input, and the login-field branch is grounded in the
declared constraints. -/
def problem_spec_checkUserModel
    (usernameField : String)
    (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
      isAnonymousMethod isAuthenticatedMethod : Bool)
    (constraints : List ConstraintInfo)
    (result : List String) : Prop :=
  result =
    (if reqFieldsBadShape then ["auth.E001"] else []) ++
    (if usernameInRequired then ["auth.E002"] else []) ++
    (if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
      (if usesDefaultBackend then ["auth.E003"] else ["auth.W004"]) else []) ++
    (if isAnonymousMethod then ["auth.C009"] else []) ++
    (if isAuthenticatedMethod then ["auth.C010"] else [])
-- post-conditions-end

-- impl-start
def implementation_checkUserModel
    (usernameField : String)
    (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
      isAnonymousMethod isAuthenticatedMethod : Bool)
    (constraints : List ConstraintInfo) : List String :=
  Id.run do
    let mut errors : List String := []
    if reqFieldsBadShape then
      errors := errors ++ ["auth.E001"]
    if usernameInRequired then
      errors := errors ++ ["auth.E002"]
    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
      if usesDefaultBackend then
        errors := errors ++ ["auth.E003"]
      else
        errors := errors ++ ["auth.W004"]
    if isAnonymousMethod then
      errors := errors ++ ["auth.C009"]
    if isAuthenticatedMethod then
      errors := errors ++ ["auth.C010"]
    return errors
-- impl-end

-- proof-start
theorem correct_checkUserModel :
    ∀ (usernameField : String)
      (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
        isAnonymousMethod isAuthenticatedMethod : Bool)
      (constraints : List ConstraintInfo),
    problem_spec_checkUserModel usernameField reqFieldsBadShape usernameInRequired
      fieldUnique usesDefaultBackend isAnonymousMethod isAuthenticatedMethod constraints
      (implementation_checkUserModel usernameField reqFieldsBadShape usernameInRequired
        fieldUnique usesDefaultBackend isAnonymousMethod isAuthenticatedMethod constraints) := by
  intro usernameField reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
    isAnonymousMethod isAuthenticatedMethod constraints
  unfold problem_spec_checkUserModel implementation_checkUserModel
  cases reqFieldsBadShape <;> cases usernameInRequired <;> cases fieldUnique <;>
    cases usesDefaultBackend <;> cases isAnonymousMethod <;> cases isAuthenticatedMethod <;>
    cases coveredByUnconditionalUniqueConstraint constraints usernameField <;>
    simp [Id.run] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 6 same-spec wrong-labeled impls (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec) built by editing ONLY the impl region; axioms/pure/pre/post byte-identical.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently in 2 batches of <=4):
- atk_1 (prepatch bug: drop coveredBy guard, fire on !fieldUnique alone) -> exit 1 FAIL. Goal mismatch on case true.true.false.true.true.true.true: impl emits auth.E003 where spec demands none. Reproduces the recorded prepatch bug + F2P test_username_unique_with_model_constraint discriminator.
- atk_2 (over-cover: drop !isConditional, conditional constraints also suppress) -> exit 1 FAIL.
- atk_3 (control-flow reorder: emit C009/C010 before E003/W004) -> exit 1 FAIL (list order differs).
- atk_4 (boundary: always W004, never E003, ignore usesDefaultBackend) -> exit 1 FAIL.
- atk_5 (partial-domain: fields.contains usernameField instead of == [usernameField]; composite unique constraints wrongly suppress) -> exit 1 FAIL.
- atk_6 (De Morgan echo: !(fieldUnique || coveredBy...) which is LOGICALLY IDENTICAL to gold !fieldUnique && !coveredBy...) -> exit 0 VERIFIES, #print axioms = [propext, Quot.sound] (clean, no sorryAx/Classical.choice).

MANDATORY RESOLVE of the ONE verifying impl (atk_6): materialized faithful patch (De Morgan rewrite of the gold guard, atk_6_patch.diff) and ran through official harness run_resolve. Result: RESOLVED=True, COMPLETED=True, NOTE=resolved (run_id sbu-13568-atk6-dm-c3p, retries=2). GOLD control patch also run same session: RESOLVED=True COMPLETED=True (confirms harness live for this instance; first atk6 attempt had COMPLETED=False from concurrent runs-contention harness error, re-run cleanly resolved). atk_6 is a gold-equivalent ECHO, NOT a weakness (G-EQ/G-PANEL-1 echo-exemption policy: a same-spec verifying attack fails only if its refined patch does NOT resolve; this one resolves).

**A-LEG AUDIT:** meta.json axioms=[], deep_model_references=[], opaque_callees=[] -> NO A-consumed, NO A-reference legs exist. axiom_check.py is a genuine skip stub. refinement.md legs: rows 1,2,4,5,6 = R (boolean refinements of UNCHANGED sub-checks the patch does not touch), row 3 = R+I (the CHANGED op; fieldUnique conjunct is R, added constraint-guard conjunct modeled DEEPLY as coveredByUnconditionalUniqueConstraint, I-tagged, spelled out concretely delegating to no opaque callee). No kind-3 (changed-inexpressible) leg. The I-tagged deep model's correspondence to the real callee (total_unique_constraints filter isUnique && condition is None, then fields == (USERNAME_FIELD,)) is validated by G-CONF (conformance_check.py: 130k+ fuzzed inputs, seed 13568, independent reconstruction of patched check_user_model, exact F2P/PASS_TO_PASS scenarios in the deterministic boundary set). No axiom slack to exploit.

**CONCLUSION:** The spec being a total functional equation with an empty axioms region means verify => correct: every closing impl is extensionally == gold and resolves iff gold does. The single verifying wrong-labeled impl was a De Morgan echo that correctly resolves. No verify-but-not-correct alternative found. Positive control (gold Solution.lean) verifies exit 0 with clean axioms [propext, Quot.sound]. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_checkUserModel is a TOTAL functional equation pinning `result` to exactly one list per input assignment, so any impl whose correct_ closes is extensionally equal to gold. No closing-but-non-resolving alternative exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No callee needs an opaque signature here. The system check that validates a
-- user model accumulates a list of diagnostics from several independent
-- sub-checks; the outcomes of the structural sub-checks (the
-- required-fields-shape check, the required-fields-membership check, the chosen
-- authentication backend, and the two anonymous/authenticated attribute checks)
-- are taken as boolean inputs (a type-only refinement, refinement.md). The
-- decision of whether the login field is guaranteed unique is modeled DEEPLY
-- below over the declared model constraints, so no callee property is consumed.
-- The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The information about one declared model constraint that the login-field
uniqueness decision inspects: whether it is a uniqueness constraint, whether it
is conditional (applies only to a subset of rows), and the ordered tuple of
field names it ranges over. -/
structure ConstraintInfo where
  isUnique : Bool
  isConditional : Bool
  fields : List String
deriving DecidableEq

/-- The login field counts as guaranteed unique by a declared constraint when
some unconditional uniqueness constraint ranges over exactly that one field. A
conditional (partial) constraint, a non-uniqueness constraint, or a constraint
spanning a different set of fields does not count. -/
def coveredByUnconditionalUniqueConstraint
    (constraints : List ConstraintInfo) (field : String) : Bool :=
  constraints.any (fun c => c.isUnique && !c.isConditional && c.fields == [field])
-- pure-end

-- post-conditions-start
/-- The diagnostics produced when validating a user model, each represented by
its stable identifier code. The list is the in-order accumulation of the
independent sub-checks: a required-fields-shape diagnostic, a
required-fields-membership diagnostic, then — only when the login field is
neither directly unique nor guaranteed unique by a declared unconditional
uniqueness constraint over exactly that field — a uniqueness diagnostic whose
severity depends on whether the default authentication backend is in use (an
error there, otherwise a warning), and finally the two
anonymous/authenticated-attribute diagnostics. Each unchanged sub-check pins its
contribution to its input, and the login-field branch is grounded in the
declared constraints. -/
def problem_spec_checkUserModel
    (usernameField : String)
    (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
      isAnonymousMethod isAuthenticatedMethod : Bool)
    (constraints : List ConstraintInfo)
    (result : List String) : Prop :=
  result =
    (if reqFieldsBadShape then ["auth.E001"] else []) ++
    (if usernameInRequired then ["auth.E002"] else []) ++
    (if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
      (if usesDefaultBackend then ["auth.E003"] else ["auth.W004"]) else []) ++
    (if isAnonymousMethod then ["auth.C009"] else []) ++
    (if isAuthenticatedMethod then ["auth.C010"] else [])
-- post-conditions-end

-- impl-start
def implementation_checkUserModel
    (usernameField : String)
    (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
      isAnonymousMethod isAuthenticatedMethod : Bool)
    (constraints : List ConstraintInfo) : List String :=
  Id.run do
    let mut errors : List String := []
    if reqFieldsBadShape then
      errors := errors ++ ["auth.E001"]
    if usernameInRequired then
      errors := errors ++ ["auth.E002"]
    if !fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField then
      if usesDefaultBackend then
        errors := errors ++ ["auth.E003"]
      else
        errors := errors ++ ["auth.W004"]
    if isAnonymousMethod then
      errors := errors ++ ["auth.C009"]
    if isAuthenticatedMethod then
      errors := errors ++ ["auth.C010"]
    return errors
-- impl-end

-- proof-start
theorem correct_checkUserModel :
    ∀ (usernameField : String)
      (reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
        isAnonymousMethod isAuthenticatedMethod : Bool)
      (constraints : List ConstraintInfo),
    problem_spec_checkUserModel usernameField reqFieldsBadShape usernameInRequired
      fieldUnique usesDefaultBackend isAnonymousMethod isAuthenticatedMethod constraints
      (implementation_checkUserModel usernameField reqFieldsBadShape usernameInRequired
        fieldUnique usesDefaultBackend isAnonymousMethod isAuthenticatedMethod constraints) := by
  intro usernameField reqFieldsBadShape usernameInRequired fieldUnique usesDefaultBackend
    isAnonymousMethod isAuthenticatedMethod constraints
  unfold problem_spec_checkUserModel implementation_checkUserModel
  cases reqFieldsBadShape <;> cases usernameInRequired <;> cases fieldUnique <;>
    cases usesDefaultBackend <;> cases isAnonymousMethod <;> cases isAuthenticatedMethod <;>
    cases coveredByUnconditionalUniqueConstraint constraints usernameField <;>
    simp [Id.run] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL:** 6 same-spec wrong-labeled impls (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec) built by editing ONLY the impl region; axioms/pure/pre/post byte-identical.

### VERIFICATION (scripts/lean_verify.sh <file>, run concurrently in 2 batches of <=4):
- atk_1 (prepatch bug: drop coveredBy guard, fire on !fieldUnique alone) -> exit 1 FAIL. Goal mismatch on case true.true.false.true.true.true.true: impl emits auth.E003 where spec demands none. Reproduces the recorded prepatch bug + F2P test_username_unique_with_model_constraint discriminator.
- atk_2 (over-cover: drop !isConditional, conditional constraints also suppress) -> exit 1 FAIL.
- atk_3 (control-flow reorder: emit C009/C010 before E003/W004) -> exit 1 FAIL (list order differs).
- atk_4 (boundary: always W004, never E003, ignore usesDefaultBackend) -> exit 1 FAIL.
- atk_5 (partial-domain: fields.contains usernameField instead of == [usernameField]; composite unique constraints wrongly suppress) -> exit 1 FAIL.
- atk_6 (De Morgan echo: !(fieldUnique || coveredBy...) which is LOGICALLY IDENTICAL to gold !fieldUnique && !coveredBy...) -> exit 0 VERIFIES, #print axioms = [propext, Quot.sound] (clean, no sorryAx/Classical.choice).

MANDATORY RESOLVE of the ONE verifying impl (atk_6): materialized faithful patch (De Morgan rewrite of the gold guard, atk_6_patch.diff) and ran through official harness run_resolve. Result: RESOLVED=True, COMPLETED=True, NOTE=resolved (run_id sbu-13568-atk6-dm-c3p, retries=2). GOLD control patch also run same session: RESOLVED=True COMPLETED=True (confirms harness live for this instance; first atk6 attempt had COMPLETED=False from concurrent runs-contention harness error, re-run cleanly resolved). atk_6 is a gold-equivalent ECHO, NOT a weakness (G-EQ/G-PANEL-1 echo-exemption policy: a same-spec verifying attack fails only if its refined patch does NOT resolve; this one resolves).

**A-LEG AUDIT:** meta.json axioms=[], deep_model_references=[], opaque_callees=[] -> NO A-consumed, NO A-reference legs exist. axiom_check.py is a genuine skip stub. refinement.md legs: rows 1,2,4,5,6 = R (boolean refinements of UNCHANGED sub-checks the patch does not touch), row 3 = R+I (the CHANGED op; fieldUnique conjunct is R, added constraint-guard conjunct modeled DEEPLY as coveredByUnconditionalUniqueConstraint, I-tagged, spelled out concretely delegating to no opaque callee). No kind-3 (changed-inexpressible) leg. The I-tagged deep model's correspondence to the real callee (total_unique_constraints filter isUnique && condition is None, then fields == (USERNAME_FIELD,)) is validated by G-CONF (conformance_check.py: 130k+ fuzzed inputs, seed 13568, independent reconstruction of patched check_user_model, exact F2P/PASS_TO_PASS scenarios in the deterministic boundary set). No axiom slack to exploit.

**CONCLUSION:** The spec being a total functional equation with an empty axioms region means verify => correct: every closing impl is extensionally == gold and resolves iff gold does. The single verifying wrong-labeled impl was a De Morgan echo that correctly resolves. No verify-but-not-correct alternative found. Positive control (gold Solution.lean) verifies exit 0 with clean axioms [propext, Quot.sound]. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness audit of problem_spec_checkUserModel vs the real callee check_user_model (django/contrib/auth/checks.py) at base_commit ede9fac75807fe5810df66280a60e7068cc97e4a, verified against git objects and the gold fix f7963615eb.

Mechanical pre-checks: same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend)=True -> spec regions byte-identical. lean_verify.sh EXIT 0 (compiles, no sorry). #print axioms correct_checkUserModel = [propext, Quot.sound] -> clean, no sorryAx/Classical.choice; proof is genuine.

Correspondence verified exact:
- Diagnostic accumulation order in real code (E001 -> E002 -> E003|W004 -> C009 -> C010) matches the spec's list concatenation order exactly.
- Post-patch guard `not get_field(USERNAME_FIELD).unique and not any(constraint.fields == (cls.USERNAME_FIELD,) for constraint in total_unique_constraints)` == `!fieldUnique && !coveredByUnconditionalUniqueConstraint constraints usernameField`.
- total_unique_constraints (options.py:831-841) = [c for c in constraints if isinstance(c, UniqueConstraint) and c.condition is None] == filter `c.isUnique && !c.isConditional`.
- constraint.fields == (USERNAME_FIELD,) is a single-element tuple comparison (UniqueConstraint sets self.fields=tuple(fields)) == `c.fields == [usernameField]` (exact one-field match; multi-field or different-field constraints correctly excluded).
- Backend severity selector, E003 vs W004, matches usesDefaultBackend branch.
- The five unchanged sub-checks are independent in the real code and are modeled as free Bool inputs (type-only R refinement) with no artificial coupling; abstracting each diagnostic to its id code drops only obj=/hint=/message framing that is patch-invariant and identical across both branches, so no patched observable behavior is lost.

The spec is a total functional equation pinning result to one exact list for every assignment; it neither over-strengthens (does not constrain unchanged sub-checks beyond their own outcome) nor drifts from the real callee. No diverging input exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean projection: imports, axioms, pure ConstraintInfo/coveredByUnconditionalUniqueConstraint, post-conditions problem_spec_checkUserModel; impl+proof elided) was regenerated via markers.spec_view and screened with leakage.screen(row['patch'], row['problem_statement']): PASSED, zero hard failures. same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical). Semantic check: the gold edit adds a guard skipping auth.E003/W004 when a total (unconditional) UniqueConstraint ranges over exactly USERNAME_FIELD. The PUBLIC problem_statement already fully discloses this — title 'Skip auth.E003 system check for USERNAME_FIELD with total UniqueConstraints', the UniqueConstraint(fields=['username']) example, the named auth.E003 code, and the explicit instruction 'The system check should be extended to check for the presence of USERNAME_FIELD in Model.`_meta`.constraints'. The spec view models exactly that behavior (E003/W004 fires only when !fieldUnique && !coveredByUnconditionalUniqueConstraint), so nothing is revealed beyond the public task. No diff markers, no patched file path (django/contrib/auth/checks.py) or module path, no bug/fix/patch narration, and no patched repo symbol echoed in the consumer view (patch touches only check_user_model; modeled name is checkUserModel; total_unique_constraints/UniqueConstraint appear only in auditor docs refinement.md/mapping.md, which are NOT part of the spec view). E003/W004 are public Django check IDs and E003 is named in the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
