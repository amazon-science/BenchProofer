# P2 adversarial audit — django__django-16527

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Discriminating input isPopup=false, hasAddPermission=false, hasChangePermission=true, change=true, saveAs=true: gold flag=false, but the prepatch/atk_1 (change-permission gate) returns true. This is exactly the F2P discriminator test_submit_row_save_as_new_add_permission_required. Under the exact-equality Bool spec every non-extensionally-equal impl leaves 'unsolved goals'.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    return (!isPopup && hasChangePermission && change && saveAs)
     -- impl-end
 
 prove_correct showSaveAsNew by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    return true
     -- impl-end
 
 prove_correct showSaveAsNew by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    return (!isPopup || (hasAddPermission && change && saveAs))
     -- impl-end
 
 prove_correct showSaveAsNew by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    return (!isPopup && hasAddPermission && change)
     -- impl-end
 
 prove_correct showSaveAsNew by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    if isPopup then return true else return (!isPopup && hasAddPermission && change && saveAs)
     -- impl-end
 
 prove_correct showSaveAsNew by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    return (!isPopup && hasAddPermission && hasChangePermission && change && saveAs)
     -- impl-end
 
 prove_correct showSaveAsNew by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    return (isPopup && hasAddPermission && change && saveAs)
     -- impl-end
 
 prove_correct showSaveAsNew by
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,7 +46,7 @@
   ensures result = (!isPopup && hasAddPermission && change && saveAs)
   do
     -- impl-start
-    return (!isPopup && hasAddPermission && change && saveAs)
+    if (!isPopup && hasAddPermission && change && saveAs) then return true else return false
     -- impl-end
 
 prove_correct showSaveAsNew by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real flag computation is a straight-line pure boolean
   conjunction that always terminates, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating body
   discharge the exact-equality postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the flag is a pure boolean combination of the four
--  inputs, modeled deeply.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The administrative form offers a "duplicate this object as a new one"
   shortcut. Because that shortcut CREATES a brand-new object, it must be
   gated on the viewer's permission to ADD objects of this kind — holding the
   permission to merely edit an existing object is NOT sufficient to expose it.

   The shortcut is offered exactly when ALL of these hold simultaneously:
   the request is a normal (non-popup) request, the viewer may ADD objects,
   the page is the edit view of an existing object, and this admin opts into
   the duplicate-as-new affordance. If any one is absent, the shortcut is
   hidden.

   Two distinct permission inputs are observed — the right to ADD and the
   right to edit (CHANGE) — because the decision must DISCRIMINATE between
   them: the gate is the ADD permission alone. The four boolean inputs and
   the change/edit permission are read-only (not `mut`); the query computes a
   single boolean and mutates nothing (directive 5). All inputs and the
   result are modeled as `Bool`. -/
method showSaveAsNew (isPopup : Bool) (hasAddPermission : Bool) (hasChangePermission : Bool) (change : Bool) (saveAs : Bool) return (result : Bool)
  ensures result = (!isPopup && hasAddPermission && change && saveAs)
  do
    -- impl-start
    return (!isPopup && hasAddPermission && change && saveAs)
    -- impl-end

prove_correct showSaveAsNew by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec = exact-equality Bool postcondition result = (!isPopup && hasAddPermission && change && saveAs) under total correctness + demonic choice, no preconditions. meta.json: axioms=[], deep_model_references=[] => the A-leg attack surface (axioms/deep-model refs) is VACUOUS by construction; refinement.md legs are all R/I (A1=R Bool bijection, A2-A5=I identical ops), no kind-3, no A-consumed/A-reference legs, correspondence to submit_row['show_save_as_new'] holds. same_spec=True for all 8 attacks and pos (verified with swebench_unified.markers.same_spec, velvet backend).

Verifications run concurrently (<=4) via scripts/lean_verify.sh (300s): pos.lean EXIT 0 (verifies); atk_1 (prepatch change-perm bug), atk_2 (return true constant echo), atk_3 (OR boundary), atk_4 (dropped saveAs conjunct = partial domain), atk_5 (control-flow-effect: if isPopup then true), atk_6 (extra hasChangePermission conjunct), atk_7 (dropped negation) => ALL EXIT 1 with genuine 'unsolved goals' (not syntax errors). atk_8 (semantically-correct echo: if (gold) then return true else return false) EXIT 0 (verifies).

Per protocol, atk_8's faithful refined patch materialized (= gold swap has_change_permission->has_add_permission, the exact refinement of if c then true else false ~ c) and RUN through official harness: run_resolve('django__django-16527', patch) => RESOLVED=True, COMPLETED=True, note='resolved'. So the only verifying wrong-shaped impl is an extensionally-correct echo whose patch RESOLVES => verify does NOT diverge from correct. Prepatch (Solution_prepatch.lean) reproduced: EXIT 1 unsolved goals. No verifying impl yielded a non-resolving faithful patch; >=5 distinct attacks run and reported. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Discriminating input isPopup=false, hasAddPermission=false, hasChangePermission=true, change=true, saveAs=true: gold flag=false, but the prepatch/atk_1 (change-permission gate) returns true. This is exactly the F2P discriminator test_submit_row_save_as_new_add_permission_required. Under the exact-equality Bool spec every non-extensionally-equal impl leaves 'unsolved goals'.
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

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real flag computation is a straight-line pure boolean
   conjunction that always terminates, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating body
   discharge the exact-equality postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the flag is a pure boolean combination of the four
--  inputs, modeled deeply.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The administrative form offers a "duplicate this object as a new one"
   shortcut. Because that shortcut CREATES a brand-new object, it must be
   gated on the viewer's permission to ADD objects of this kind — holding the
   permission to merely edit an existing object is NOT sufficient to expose it.

   The shortcut is offered exactly when ALL of these hold simultaneously:
   the request is a normal (non-popup) request, the viewer may ADD objects,
   the page is the edit view of an existing object, and this admin opts into
   the duplicate-as-new affordance. If any one is absent, the shortcut is
   hidden.

   Two distinct permission inputs are observed — the right to ADD and the
   right to edit (CHANGE) — because the decision must DISCRIMINATE between
   them: the gate is the ADD permission alone. The four boolean inputs and
   the change/edit permission are read-only (not `mut`); the query computes a
   single boolean and mutates nothing (directive 5). All inputs and the
   result are modeled as `Bool`. -/
method showSaveAsNew (isPopup : Bool) (hasAddPermission : Bool) (hasChangePermission : Bool) (change : Bool) (saveAs : Bool) return (result : Bool)
  ensures result = (!isPopup && hasAddPermission && change && saveAs)
  do
    -- impl-start
    return (!isPopup && hasAddPermission && change && saveAs)
    -- impl-end

prove_correct showSaveAsNew by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Spec = exact-equality Bool postcondition result = (!isPopup && hasAddPermission && change && saveAs) under total correctness + demonic choice, no preconditions. meta.json: axioms=[], deep_model_references=[] => the A-leg attack surface (axioms/deep-model refs) is VACUOUS by construction; refinement.md legs are all R/I (A1=R Bool bijection, A2-A5=I identical ops), no kind-3, no A-consumed/A-reference legs, correspondence to submit_row['show_save_as_new'] holds. same_spec=True for all 8 attacks and pos (verified with swebench_unified.markers.same_spec, velvet backend).

Verifications run concurrently (<=4) via scripts/lean_verify.sh (300s): pos.lean EXIT 0 (verifies); atk_1 (prepatch change-perm bug), atk_2 (return true constant echo), atk_3 (OR boundary), atk_4 (dropped saveAs conjunct = partial domain), atk_5 (control-flow-effect: if isPopup then true), atk_6 (extra hasChangePermission conjunct), atk_7 (dropped negation) => ALL EXIT 1 with genuine 'unsolved goals' (not syntax errors). atk_8 (semantically-correct echo: if (gold) then return true else return false) EXIT 0 (verifies).

Per protocol, atk_8's faithful refined patch materialized (= gold swap has_change_permission->has_add_permission, the exact refinement of if c then true else false ~ c) and RUN through official harness: run_resolve('django__django-16527', patch) => RESOLVED=True, COMPLETED=True, note='resolved'. So the only verifying wrong-shaped impl is an extensionally-correct echo whose patch RESOLVES => verify does NOT diverge from correct. Prepatch (Solution_prepatch.lean) reproduced: EXIT 1 unsolved goals. No verifying impl yielded a non-resolving faithful patch; >=5 distinct attacks run and reported. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function showSaveAsNew postcondition `result = (!isPopup && hasAddPermission && change && saveAs)` is byte-for-byte the gold-patched callee `submit_row`'s "show_save_as_new" entry (`not is_popup and has_add_permission and change and save_as`) at django/contrib/admin/templatetags/admin_modify.py. All five inputs are genuine Python booleans read from the template context (context["is_popup"], ["has_add_permission"], ["change"], ["save_as"]), so the Bool<->bool bijection (mapping.md §2) is exact. Verified independently: (1) same_spec(Solution, Solution_prepatch, VelvetBackend)=True — spec region byte-identical; (2) Solution.lean verifies (lean_verify exit 0); (3) base_commit source has `has_change_permission` and patched has `has_add_permission`, so the spec correctly models the PATCHED (fixed) behavior; (4) conformance_check shadow≡oracle over 32 exhaustive + 100k fuzz inputs, 0 disagreements. hasChangePermission is intentionally unused in the postcondition — this is correct, since the fix removes the change-permission conjunct; it exists only to make the prepatch expressible against the identical spec (fails when hasAddPermission != hasChangePermission, per G-DIFF pass). No input exists on which the modeled function disagrees with the real repo callee. Spec is neither too strong nor too weak.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical to prepatch (swebench_unified.markers.same_spec = True via VelvetBackend). The gold edit is the swap has_change_permission -> has_add_permission in the show_save_as_new conjunction of admin_modify.py. That discriminating fact is ALREADY fully public in problem_statement (not hints_text): it names the file/line, states 'you must put one more verification ... and has_add_permission', and shows the full rewritten conjunction flagging 'and has_add_permission # This line that I put!!!'. The spec view's postcondition (result = !isPopup && hasAddPermission && change && saveAs) is the legitimate specification of correct behavior — every verified spec encodes correct behavior; using has_add_permission alone as the gate is directly implied by, and no more revealing than, the public problem_statement. Rationale comments are abstract ('gated on the viewer's permission to ADD', 'the gate is the ADD permission alone') and quote neither the gold diff verbatim nor problem-statement phrasing; hasChangePermission is carried as an unused param solely to make the prepatch expressible against the identical spec (a legitimate modeling device, not an edit-mechanics leak). No F2P test name, no gold-patch strings, no line-number-to-edit callout appear in the solver-visible view. G-LEAK is a lexical screen and nothing here leaks beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).