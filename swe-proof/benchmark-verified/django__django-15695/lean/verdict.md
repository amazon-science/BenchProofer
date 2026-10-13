# P2 adversarial audit — django__django-15695

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,8 +59,6 @@
     Option (Index × Index) := Id.run do
   if canMigrate = false then
     return none
-  if oldIndex.name = newName then
-    return none
   return some (oldIndex, newIndex)
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
     return none
   if oldIndex.name = newName then
     return none
-  return some (oldIndex, newIndex)
+  return some (newIndex, oldIndex)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,8 +57,6 @@
 def implementation_applyIndexRenameForward
     (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String) :
     Option (Index × Index) := Id.run do
-  if canMigrate = false then
-    return none
   if oldIndex.name = newName then
     return none
   return some (oldIndex, newIndex)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
     Option (Index × Index) := Id.run do
   if canMigrate = false then
     return none
-  if oldIndex.name = newName then
+  if oldIndex.name ≠ newName then
     return none
   return some (oldIndex, newIndex)
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,11 +57,7 @@
 def implementation_applyIndexRenameForward
     (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String) :
     Option (Index × Index) := Id.run do
-  if canMigrate = false then
-    return none
-  if oldIndex.name = newName then
-    return none
-  return some (oldIndex, newIndex)
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,10 +57,6 @@
 def implementation_applyIndexRenameForward
     (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String) :
     Option (Index × Index) := Id.run do
-  if canMigrate = false then
-    return none
-  if oldIndex.name = newName then
-    return none
   return some (oldIndex, newIndex)
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
     return none
   if oldIndex.name = newName then
     return none
-  return some (oldIndex, newIndex)
+  return some (newIndex, newIndex)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Deciding whether a schema operation that relabels a database index from one name
to another should actually emit the underlying relabel, and with which index
pair.

The operation works on a model whose migration may or may not be permitted on the
current connection. When migration is not permitted the operation does nothing.
Otherwise it has in hand the index it would relabel *from* (identified earlier in
the operation) and the index it would relabel *to*; each index carries a name.

The relabel is only meaningful when it actually changes the name: if the starting
entry already bears the target name, there is nothing to do and no relabel is
emitted. In every other permitted case the operation emits exactly one relabel of
the starting entry to the target entry.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Whether migration is permitted, the
-- starting index, the target index, and the target name all enter as plain data
-- (already resolved upstream); the only operation modeled is the decision of
-- which relabel to emit, if any, spelled out directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The touched view of a database index: only its `name` is consulted by the
decision modeled here. -/
structure Index where
  name : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The emitted relabel action is fully pinned to the inputs:

  * if migration is not permitted, no relabel is emitted (`result = none`);
  * if migration is permitted but the starting index already carries the target
    name, no relabel is emitted (`result = none`);
  * if migration is permitted and the starting index's name differs from the
    target name, exactly the relabel of the starting index to the target index is
    emitted (`result = some (oldIndex, newIndex)`).

Every input configuration determines the result, so no output is left free. -/
def problem_spec_applyIndexRenameForward
    (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String)
    (result : Option (Index × Index)) : Prop :=
  (canMigrate = false → result = none) ∧
  (canMigrate = true → oldIndex.name = newName → result = none) ∧
  (canMigrate = true → oldIndex.name ≠ newName →
      result = some (oldIndex, newIndex))
-- post-conditions-end

-- impl-start
def implementation_applyIndexRenameForward
    (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String) :
    Option (Index × Index) := Id.run do
  if canMigrate = false then
    return none
  if oldIndex.name = newName then
    return none
  return some (oldIndex, newIndex)
-- impl-end

-- proof-start
theorem correct_applyIndexRenameForward :
    ∀ (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String),
      problem_spec_applyIndexRenameForward canMigrate oldIndex newIndex newName
        (implementation_applyIndexRenameForward canMigrate oldIndex newIndex newName) := by
  intro canMigrate oldIndex newIndex newName
  unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp [Id.run, h, pure]
  · intro h1 h2
    simp [Id.run, h1, h2, pure, bind]
  · intro h1 h2
    simp [Id.run, h1, h2, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-15695 lean. Spec is a TOTAL, DETERMINISTIC exact function: result is uniquely pinned across all three input regions (canMigrate=false -> none; canMigrate=true & oldIndex.name=newName -> none; canMigrate=true & oldIndex.name!=newName -> some(oldIndex,newIndex)). A-legs are trivial: axioms region empty (no opaque/axiom), deep_model_references=[], axiom_check.py is a genuine skip stub; refinement.md legs are all R or I (no kind-3), correspondence sound. All same_spec checks True (7 attacks + positive control), verified with swebench_unified.markers.same_spec under lean backend.

ATTACKS (all same_spec=True; verified via `bash scripts/lean_verify.sh <f>` from project root, run concurrently in 2 batches of 4/3):
- atk_1.lean (prepatch bug; impl BYTE-IDENTICAL to Solution_prepatch.lean = drop name-equal guard): exit=1, unsolved goals case refine_2.
- atk_2.lean (swap emitted pair -> some(newIndex,oldIndex)): exit=1, refine_3.
- atk_3.lean (ignore canMigrate; emit when names differ): exit=1, refine_1.
- atk_4.lean (boundary: invert name guard, none when differ): exit=1, refine_2.
- atk_5.lean (partial-domain: always none): exit=1, refine_3.
- atk_6.lean (ungrounded-oracle echo: always emit some(oldIndex,newIndex)): exit=1, refine_1.
- atk_7.lean (newIndex in both slots -> some(newIndex,newIndex)): exit=1, refine_3.
All failures are genuine `error: unsolved goals` at the discriminating clause, NOT syntax errors.

POSITIVE CONTROL: pos_control.lean (exact copy of Solution.lean) verifies exit=0, empty output (no error/sorry). `#print axioms correct_applyIndexRenameForward` => depends on axioms: [propext] only (clean; no sorryAx, no custom axiom).

Step-2 (materialize+resolve faithful patch) is VACUOUS: no same-spec wrong impl produced a closing clean-axiom proof, so there is nothing to run through the harness. prepatch_reproduced=true (atk_1 impl region is byte-identical to the bundle's Solution_prepatch.lean, and it fails to verify at refine_2 — exactly the F2P discriminating clause). patches={} accordingly.

Conclusion: verify => correct holds under 7 distinct attacks (partial-domain, boundary, control-flow-effect, wrong-pair, ungrounded echo, prepatch bug); none breaks the spec. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Deciding whether a schema operation that relabels a database index from one name
to another should actually emit the underlying relabel, and with which index
pair.

The operation works on a model whose migration may or may not be permitted on the
current connection. When migration is not permitted the operation does nothing.
Otherwise it has in hand the index it would relabel *from* (identified earlier in
the operation) and the index it would relabel *to*; each index carries a name.

The relabel is only meaningful when it actually changes the name: if the starting
entry already bears the target name, there is nothing to do and no relabel is
emitted. In every other permitted case the operation emits exactly one relabel of
the starting entry to the target entry.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Whether migration is permitted, the
-- starting index, the target index, and the target name all enter as plain data
-- (already resolved upstream); the only operation modeled is the decision of
-- which relabel to emit, if any, spelled out directly below. Hence no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The touched view of a database index: only its `name` is consulted by the
decision modeled here. -/
structure Index where
  name : String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The emitted relabel action is fully pinned to the inputs:

  * if migration is not permitted, no relabel is emitted (`result = none`);
  * if migration is permitted but the starting index already carries the target
    name, no relabel is emitted (`result = none`);
  * if migration is permitted and the starting index's name differs from the
    target name, exactly the relabel of the starting index to the target index is
    emitted (`result = some (oldIndex, newIndex)`).

Every input configuration determines the result, so no output is left free. -/
def problem_spec_applyIndexRenameForward
    (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String)
    (result : Option (Index × Index)) : Prop :=
  (canMigrate = false → result = none) ∧
  (canMigrate = true → oldIndex.name = newName → result = none) ∧
  (canMigrate = true → oldIndex.name ≠ newName →
      result = some (oldIndex, newIndex))
-- post-conditions-end

-- impl-start
def implementation_applyIndexRenameForward
    (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String) :
    Option (Index × Index) := Id.run do
  if canMigrate = false then
    return none
  if oldIndex.name = newName then
    return none
  return some (oldIndex, newIndex)
-- impl-end

-- proof-start
theorem correct_applyIndexRenameForward :
    ∀ (canMigrate : Bool) (oldIndex newIndex : Index) (newName : String),
      problem_spec_applyIndexRenameForward canMigrate oldIndex newIndex newName
        (implementation_applyIndexRenameForward canMigrate oldIndex newIndex newName) := by
  intro canMigrate oldIndex newIndex newName
  unfold problem_spec_applyIndexRenameForward implementation_applyIndexRenameForward
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp [Id.run, h, pure]
  · intro h1 h2
    simp [Id.run, h1, h2, pure, bind]
  · intro h1 h2
    simp [Id.run, h1, h2, pure, bind]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Bundle: django__django-15695 lean. Spec is a TOTAL, DETERMINISTIC exact function: result is uniquely pinned across all three input regions (canMigrate=false -> none; canMigrate=true & oldIndex.name=newName -> none; canMigrate=true & oldIndex.name!=newName -> some(oldIndex,newIndex)). A-legs are trivial: axioms region empty (no opaque/axiom), deep_model_references=[], axiom_check.py is a genuine skip stub; refinement.md legs are all R or I (no kind-3), correspondence sound. All same_spec checks True (7 attacks + positive control), verified with swebench_unified.markers.same_spec under lean backend.

ATTACKS (all same_spec=True; verified via `bash scripts/lean_verify.sh <f>` from project root, run concurrently in 2 batches of 4/3):
- atk_1.lean (prepatch bug; impl BYTE-IDENTICAL to Solution_prepatch.lean = drop name-equal guard): exit=1, unsolved goals case refine_2.
- atk_2.lean (swap emitted pair -> some(newIndex,oldIndex)): exit=1, refine_3.
- atk_3.lean (ignore canMigrate; emit when names differ): exit=1, refine_1.
- atk_4.lean (boundary: invert name guard, none when differ): exit=1, refine_2.
- atk_5.lean (partial-domain: always none): exit=1, refine_3.
- atk_6.lean (ungrounded-oracle echo: always emit some(oldIndex,newIndex)): exit=1, refine_1.
- atk_7.lean (newIndex in both slots -> some(newIndex,newIndex)): exit=1, refine_3.
All failures are genuine `error: unsolved goals` at the discriminating clause, NOT syntax errors.

POSITIVE CONTROL: pos_control.lean (exact copy of Solution.lean) verifies exit=0, empty output (no error/sorry). `#print axioms correct_applyIndexRenameForward` => depends on axioms: [propext] only (clean; no sorryAx, no custom axiom).

Step-2 (materialize+resolve faithful patch) is VACUOUS: no same-spec wrong impl produced a closing clean-axiom proof, so there is nothing to run through the harness. prepatch_reproduced=true (atk_1 impl region is byte-identical to the bundle's Solution_prepatch.lean, and it fails to verify at refine_2 — exactly the F2P discriminating clause). patches={} accordingly.

Conclusion: verify => correct holds under 7 distinct attacks (partial-domain, boundary, control-flow-effect, wrong-pair, ungrounded echo, prepatch bug); none breaks the spec. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec models post-patch RenameIndex.database_forwards forward-decision. (1) same_spec(Solution.lean, Solution_prepatch.lean, lean.language)=True — post-conditions/pure/axioms regions byte-identical; only impl+proof differ (prepatch omits the equal-name early return). (2) lean_verify.sh exit 0; #print axioms correct_applyIndexRenameForward => [propext] only, no sorryAx. (3) Spec's 3 clauses match the real patched callee exactly: not allow_migrate=>none; old_index.name==new_name=>none; else rename_index(old,new). Index={name} is the faithful touched-field view (only .name is read by the changed guard). (4) Differential-tested against the REAL patched callee (applied gold guard to base-commit worktree copy): bundled conformance_check.py = 100000 inputs, 0 disagreements; plus a custom adversarial harness = ~301694 inputs (empty/whitespace/unicode/tab names, exhaustive equality-class sweep, bias-true canMigrate) with 0 disagreements. Empty old_name/new_name are rejected by the RenameIndex constructor, so not valid decision-point inputs. No input where the modeled function disagrees with the real repo callee — spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True); only impl/proof bodies differ. Mechanical G-LEAK screen passes (0 hard failures). Semantic gold-reconstruction review: gold edit adds `if old_index.name == self.new_name: return` guard to RenameIndex.database_forwards. The spec view does NOT leak this beyond the public problem_statement: (1) no patched file path (models.py), no patched symbols (database_forwards/old_index/new_index/new_name — model uses abstract paraphrases oldIndex/newIndex/newName/'relabel'/'starting entry'), no diff markers, no reproduced gold line, no narration terms (bug/fix/patch). (2) The discriminating clause `canMigrate=true → oldIndex.name=newName → result=none` encodes the CORRECT intended behavior, which the public problem_statement already discloses: it states that re-applying RenameIndex() forward crashes with 'relation "new_pony_test_idx" already exists' and shows the exact re-apply-forward test — i.e. that a second forward apply when the index already bears the target name must be a no-op. Encoding that intended behavior in the spec is the spec's proper job and is derivable from the public task, not from hints_text. Comments stay at behavioral altitude ('if the starting entry already bears the target name, there is nothing to do'), describing behavior not the edit. No spec-view line reconstructs the gold edit beyond what the public problem_statement already reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
