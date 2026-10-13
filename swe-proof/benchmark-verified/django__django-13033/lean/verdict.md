# P2 adversarial audit — django__django-13033

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean`, `atk_12.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9.lean`, `atk_10.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found - the spec is NOT broken. All 13 semantically-WRONG same-spec impls FAILED to close (exit 1, sorryAx present in #print axioms). The 4 impls whose proofs DID close with clean axioms (atk_9, atk_10, atk_13, atk_14) are all extensionally EQUAL to gold (different syntactic route to the same boolean), and their materialized faithful patches were each RUN through run_resolve: ALL FOUR RESOLVED=True (F2P test_order_by_self_referential_fk passes, 26/26 P2P pass). So no closing clean-axiom proof has a non-resolving faithful patch: verify=>correct is NOT falsified.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1: prepatch bug re-encoded (whole path instead of final segment).
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
   if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+      (fieldAttr != some path) && (path != "pk") then
     return true
   return false
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,9 +69,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 2: partial domain -- carves out fieldAttr = some \"\" and answers false there.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
+  if fieldAttr == some "" then
+    return false
   if fieldIsRelation && relatedHasOrdering &&
       (fieldAttr != some (lastSegment path)) && (path != "pk") then
     return true
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3: boundary -- the primary-key shortcut exclusion is dropped.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
   if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+      (fieldAttr != some (lastSegment path)) then
     return true
   return false
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,13 +69,17 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4: control-flow effect -- an extra mutation after the guard.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
+  let mut r : Bool := false
   if fieldIsRelation && relatedHasOrdering &&
       (fieldAttr != some (lastSegment path)) && (path != "pk") then
-    return true
-  return false
+    r := true
+  if path == "" then
+    r := true
+  return r
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,13 +69,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5: ungrounded-oracle echo -- echoes only the pk exclusion.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
-    return true
-  return false
+  return (path != "pk")
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,11 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 6: the stored-attribute conjunct is dropped entirely.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+  if fieldIsRelation && relatedHasOrdering && (path != "pk") then
     return true
   return false
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,16 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 7: suffix heuristic -- 'path ends with the stored attribute' instead of
+-- 'the final segment IS the stored attribute'.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+  let attrMatches : Bool :=
+    match fieldAttr with
+    | none => false
+    | some a => path.endsWith a
+  if fieldIsRelation && relatedHasOrdering && (!attrMatches) && (path != "pk") then
     return true
   return false
 -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 8: the final segment is taken by splitting on a SINGLE underscore.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
+  let seg : String := (path.splitOn "_").getLastD ""
   if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+      (fieldAttr != some seg) && (path != "pk") then
     return true
   return false
 -- impl-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 9: same truth value, conjuncts REORDERED (stored-attribute test first).
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+  if (fieldAttr != some (lastSegment path)) && (path != "pk") &&
+      fieldIsRelation && relatedHasOrdering then
     return true
   return false
 -- impl-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,13 +69,15 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 10: same truth value, negated early-return (De Morgan) form.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
-    return true
-  return false
+  if !fieldIsRelation then return false
+  if !relatedHasOrdering then return false
+  if path == "pk" then return false
+  if fieldAttr == some (lastSegment path) then return false
+  return true
 -- impl-end
 
 -- proof-start
@@ -88,7 +90,7 @@
           fieldAttr path) := by
   intro fieldIsRelation relatedHasOrdering fieldAttr path
   unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
-  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
+  simp only [Id.run, bind, pure, bne_iff_ne, ne_eq, Bool.and_eq_true]
   by_cases hr : fieldIsRelation = true <;>
   by_cases ho : relatedHasOrdering = true <;>
   by_cases ha : fieldAttr = some (lastSegment path) <;>
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 11: boundary -- pk exclusion tested on the final segment instead of the
+-- whole path.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
   if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+      (fieldAttr != some (lastSegment path)) && (lastSegment path != "pk") then
     return true
   return false
 -- impl-end
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,15 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 12: a field with NO stored attribute is treated as matching the segment.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+  let attrMatches : Bool :=
+    match fieldAttr with
+    | none     => true
+    | some a   => a == lastSegment path
+  if fieldIsRelation && relatedHasOrdering && (!attrMatches) && (path != "pk") then
     return true
   return false
 -- impl-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,13 +69,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 13: ungrounded-oracle echo -- the impl decides the postcondition itself
+-- instead of computing the decision.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
-    return true
-  return false
+  return decide (fieldIsRelation = true ∧ relatedHasOrdering = true ∧
+    fieldAttr ≠ some (lastSegment path) ∧ path ≠ "pk")
 -- impl-end
 
 -- proof-start
@@ -88,10 +88,5 @@
           fieldAttr path) := by
   intro fieldIsRelation relatedHasOrdering fieldAttr path
   unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
-  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
-  by_cases hr : fieldIsRelation = true <;>
-  by_cases ho : relatedHasOrdering = true <;>
-  by_cases ha : fieldAttr = some (lastSegment path) <;>
-  by_cases hp : path = "pk" <;>
-  simp_all [pure]
+  simp only [Id.run, pure, decide_eq_true_eq]
 -- proof-end
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 14: same truth value, final segment taken by INDEXING the split list.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
+  let segs := path.splitOn "__"
+  let seg := segs[segs.length - 1]!
   if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+      (fieldAttr != some seg) && (path != "pk") then
     return true
   return false
 -- impl-end
@@ -87,8 +90,18 @@
         (implementation_orderingExpandsRelation fieldIsRelation relatedHasOrdering
           fieldAttr path) := by
   intro fieldIsRelation relatedHasOrdering fieldAttr path
+  have hseg : ∀ (l : List String), l[l.length - 1]! = l.getLastD "" := by
+    intro l
+    induction l with
+    | nil => simp
+    | cons a t ih =>
+      cases t with
+      | nil => simp
+      | cons b u => simpa using ih
+  have hs : (path.splitOn "__")[(path.splitOn "__").length - 1]! = lastSegment path := by
+    unfold lastSegment; exact hseg _
   unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
-  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
+  simp only [Id.run, hs, bne_iff_ne, ne_eq, Bool.and_eq_true]
   by_cases hr : fieldIsRelation = true <;>
   by_cases ho : relatedHasOrdering = true <;>
   by_cases ha : fieldAttr = some (lastSegment path) <;>
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,9 +69,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 15: partial domain -- single-segment lookups (e.g. ordering directly by an
+-- FK field) never expand, though the real code does expand them.
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
+  if (path.splitOn "__").length == 1 then
+    return false
   if fieldIsRelation && relatedHasOrdering &&
       (fieldAttr != some (lastSegment path)) && (path != "pk") then
     return true
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 16: the getLastD default is replaced by an unreachable sentinel -- provably
+-- extensionally equal because splitOn on a non-empty separator never returns [].
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
+  let seg := (path.splitOn "__").getLastD "\u0000SENTINEL"
   if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+      (fieldAttr != some seg) && (path != "pk") then
     return true
   return false
 -- impl-end
@@ -87,8 +90,21 @@
         (implementation_orderingExpandsRelation fieldIsRelation relatedHasOrdering
           fieldAttr path) := by
   intro fieldIsRelation relatedHasOrdering fieldAttr path
+  have hne : (path.splitOn "__") ≠ [] := by
+    unfold String.splitOn String.splitOnAux
+    split <;> simp
+  have hd : ∀ (l : List String) (d e : String), l ≠ [] →
+      l.getLastD d = l.getLastD e := by
+    intro l d e hl
+    induction l with
+    | nil => exact absurd rfl hl
+    | cons a t ih => cases t with
+      | nil => simp
+      | cons b u => simpa using ih (by simp)
+  have hs : (path.splitOn "__").getLastD "\u0000SENTINEL" = lastSegment path := by
+    unfold lastSegment; exact hd _ _ _ hne
   unfold problem_spec_orderingExpandsRelation implementation_orderingExpandsRelation
-  simp only [Id.run, bne_iff_ne, ne_eq, Bool.and_eq_true]
+  simp only [Id.run, hs, bne_iff_ne, ne_eq, Bool.and_eq_true]
   by_cases hr : fieldIsRelation = true <;>
   by_cases ho : relatedHasOrdering = true <;>
   by_cases ha : fieldAttr = some (lastSegment path) <;>
```

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -69,11 +69,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 17: narrow fix targeting only the `_id` shape -- suppresses expansion when
+-- the final segment equals the stored attribute ONLY IF that segment ends in "_id".
 def implementation_orderingExpandsRelation
     (fieldIsRelation relatedHasOrdering : Bool) (fieldAttr : Option String)
     (path : String) : Bool := Id.run do
-  if fieldIsRelation && relatedHasOrdering &&
-      (fieldAttr != some (lastSegment path)) && (path != "pk") then
+  let seg := lastSegment path
+  let suppress : Bool := (fieldAttr == some seg) && seg.endsWith "_id"
+  if fieldIsRelation && relatedHasOrdering && (!suppress) && (path != "pk") then
     return true
   return false
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SETUP.** Fresh base_commit worktree (git a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e). All 18 files (17 attacks + positive control) built by copying Solution.lean and editing ONLY the impl region; same_spec(Solution.lean, atk_N.lean, LeanBackend) = True for ALL 18 (verified via swebench_unified.markers.same_spec). Verify cmd per file: bash scripts/lean_verify.sh <D>/atk_N.lean ; an `_ax`.lean twin with a trailing '#print axioms correct_orderingExpandsRelation' gave the axiom read.

**POSITIVE CONTROL.** atk_pos.lean is byte-identical to Solution.lean (diff empty). EXIT=0; #print axioms => 'depends on axioms: [propext]' (clean, no sorryAx/native_decide). Non-vacuity established.

PREPATCH REPRODUCED (2 ways). (a) atk_1.lean re-encodes the prepatch bug (fieldAttr != some path, i.e. compared against the WHOLE lookup instead of the final segment): EXIT=1, axioms [propext, sorryAx]. Error is exactly the discriminating obligation 'lastSegment path = path' under hr/ho/ha/hp. Divergence at fieldIsRelation=true, relatedHasOrdering=true, fieldAttr=some "root_id", path="record__root_id": impl=true, spec=false (lastSegment="root_id"=fieldAttr => no expansion). (b) The bundle's own Solution_prepatch.lean copied to <D>/prepatch.lean: EXIT=1 ('simp made no progress' at the hc-case rewrite). Both confirm the guard-fix is load-bearing.

### REJECTED WRONG IMPLS (13, all EXIT=1 with sorryAx => proof did NOT close; no patch/resolve owed).
1 atk_1 prepatch echo (whole path) - [propext,sorryAx]; div fr=T ro=T fa='root_id' p='record__root_id'. 2 atk_2 PARTIAL-DOMAIN: carves out fieldAttr=some "" -> false - [propext,sorryAx,Quot.sound]; div fa='' p='record'. 3 atk_3 BOUNDARY: pk-shortcut conjunct dropped - [propext,sorryAx]; unsolved 'False' in the path="pk" case; div p='pk'. 4 atk_4 CONTROL-FLOW-EFFECT: 'let mut r' then a second write r:=true when path=="" clobbers the decision - [propext,sorryAx,Quot.sound]; div p=''. 5 atk_5 UNGROUNDED-ORACLE ECHO of one observation: return (path != "pk") - [propext,sorryAx]; 304 divergences over my grid. 6 atk_6 fix-bearing attname conjunct dropped entirely - [propext,sorryAx].

7 atk_7 SUFFIX heuristic path.endsWith attr instead of exact final-segment equality - [propext,sorryAx,Quot.sound]; div fa='' p='record' and fa='root_id' p='xroot_id'. 8 atk_8 WRONG SEPARATOR: splitOn `"_"` (single underscore) instead of "`__`" - [propext,sorryAx]; div fa='root_id' p='record__root_id' (single-split yields 'id'). 9 atk_11 BOUNDARY: pk exclusion tested on lastSegment instead of the whole path - [propext,sorryAx]; div p='a__pk'. 10 atk_12 Option/None bijection BREAK: a field with no stored attribute counts as matching - [propext,sorryAx,Classical.choice,Quot.sound]; div fa=None. 11 atk_15 PARTIAL-DOMAIN over a reachable class: single-segment lookups never expand - [propext,sorryAx,Quot.sound]; div p='record'.

12 atk_17 NARROW F2P-TARGETED fix: suppresses expansion only when the matching segment ends in '`_id`', so any non-`_id` attname match still wrongly expands - [propext,sorryAx,Classical.choice,Quot.sound]. This is the most dangerous shape (it passes the F2P test yet is wrong in general) and the spec still rejects it. 13 atk_16 unreachable-default sentinel in getLastD - EXIT=1 [propext,sorryAx]. NOTE: this impl is extensionally EQUAL to gold, so its non-closure is a proof-effort artifact (I could not discharge splitOn-nonempty; String.splitOn_ne_empty does not exist in this Mathlib and unfolding splitOnAux blew the whnf heartbeat budget), NOT evidence of a spec defect. It is reported for completeness and owes no resolve (nothing closed).

CLOSING CLEAN-AXIOM IMPLS => MANDATORY RESOLVE RUNS (4). Each is extensionally equal to gold via a DIFFERENT syntactic route, so each needed a materialized faithful patch through the official harness. Patches built in the base_commit worktree, each checked with 'git apply --check' (all 4 APPLY at a59de6e8) and run via swebench_unified.harness.run_resolve('django__django-13033', diff).
- atk_9.lean (conjuncts REORDERED: attname/pk tests first, then is_relation/ordering): lean_verify EXIT=0, axioms [propext] CLEAN. Patch atk_9.diff reorders the four conjuncts in the real guard. RESOLVE: RESOLVED=True, completed=True, F2P success ['test_order_by_self_referential_fk'], 26/26 P2P success, 0 PASS_TO_FAIL (note='resolved on attempt 3/3 (flaky: earlier attempt failed or did not complete)', attempts=3).
- atk_10.lean (De Morgan / negated early-return form): lean_verify EXIT=0, axioms [propext, Classical.choice, Quot.sound] - CLEAN (no sorryAx/sorry/native_decide; Classical.choice+Quot.sound are ordinary Mathlib-classical deps, same family the gold proof draws on). Patch replaces the guard with an 'expand = True' + four elif guard-clauses form. RESOLVE: RESOLVED=True, F2P pass, 26/26 P2P, note='resolved', attempts=1, flaky=False.
- atk_13.lean (UNGROUNDED-ORACLE ECHO lane: impl is literally 'decide (<the postcondition>)'): lean_verify EXIT=0, axioms [propext] CLEAN. This is the sharpest echo attack - a decide-the-spec impl closes trivially by construction. Its faithful patch expresses the guard as all((is_relation, bool(ordering), attname != pieces[-1], name != 'pk')). RESOLVE: RESOLVED=True, F2P pass, 26/26 P2P, attempts=1. Verdict on the echo: because the postcondition is FULLY GROUNDED in the four free inputs (no oracle parameter, no result-echoing hypothesis) and lastSegment is a concrete computable function, 'decide (spec)' IS a correct implementation - the echo is benign here, and the harness agrees.
- atk_14.lean (final segment by INDEXING the split list, segs[segs.length-1]!): lean_verify EXIT=0, axioms [propext, Classical.choice, Quot.sound] CLEAN (needed an induction lemma l[l.length-1]! = l.getLastD ""). Patch uses pieces[len(pieces)-1]. RESOLVE: RESOLVED=True, F2P pass, 26/26 P2P, attempts=1.
Bottom line on the A-of-verify-implies-correct leg: 4 closing clean-axiom proofs, 4 materialized applying patches, 4 EXECUTED resolve runs, 4/4 RESOLVED=True. No verify-but-not-resolve pair exists among them.

A-LEG AUDIT (my assigned focus). meta.json declares axioms=[] and deep_model_references=[]; grep -E '^(axiom|opaque|@[extern])' over Solution.lean returns NOTHING, so there is genuinely no axiom/opaque callee contract and no deep-model reference to validate. axiom_check.py is an honest skip stub (prints status=skip, exit 0) and G-AX is recorded status=pass/skip consistently - no A-consumed or A-reference leg exists to be unfaithful. I verified the framing is legitimate rather than an evasion: the guard's own computation is the split plus the (in)equality tests, and BOTH are modeled deeply in Lean (String.splitOn/getLastD, Option/String (in)equality) rather than axiomatized.

The only thing framed as free input is the `_setup_joins`/setup_joins resolution, and I confirmed at base_commit that (a) the gold patch touches ONLY the guard line (patch.diff is a single hunk at compiler.py:727) so the resolution is byte-identical pre/post patch, and (b) setup_joins does NOT mutate its 'names' argument (it only slices names[:pivot]/names[pivot:] and appends to a separate joins list), so 'pieces' at line 730 is exactly name.split('`__`') from line 724 - the mapping.md claim 'pieces[-1] is exactly the final `__`-separated segment of name' holds. Framing the resolution as free inputs is therefore sound, not an ungrounded oracle.

**REFINEMENT.MD LEG AUDIT.** Six legs, tags 1=R, 2=I, 3=I, 4=I, 5=R, 6=R. No leg is A-consumed or A-reference (consistent with axioms=[]), and NO leg is kind-3 (unjustified/hand-waved) - each R leg names the concrete counterpart it abstracts and why the abstraction is patch-invariant (leg 1: resolved observations, unchanged by the patch; leg 5: the fall-through trim_joins + direct OrderBy, downstream of the decision; leg 6: the modeled outcome IS the branch-entered boolean). Legs 2-4 I-tags are byte-level accurate against the post-patch source I read in the worktree: leg 2 pieces[-1] <-> (path.splitOn "`__`").getLastD "", leg 3 the != inequality incl. the None/none case, leg 4 the four-way conjunction incl. name != 'pk'. Only nit, non-blocking: leg 2 is tagged 'I' while also being the changed op; leg 5's claim that the direct-column branch is 'not part of the modeled decision' is a legitimate R abstraction, not a kind-3 gap. Correspondence to the real callees holds.

DEEP-MODEL DIFFERENTIAL (my own, independent of G-CONF). I did not take the bundle's split-equivalence claim on trust. Built <D>/split_diff2.lean pairing 276 inputs with their Python name.split('`__`')[-1] value (hand-picked edges: '', `'_'`, '`__`', '`___`', '`____`', '`_____`', 'a__', '`__a`', '`__a__`', 'a___b', 'a____b', 'a_____b', 'pk', '`__pk`', 'pk__', 'record__root_id', 'author__editor_id', 'record__root__id', unicode 'lie__ming'/'snowman__b', an embedded newline, plus 400 random strings over the alphabet {a,b,_,`__`,`___`,pk} seeded 13033, deduped). lean_verify EXIT=0; #eval of the mismatch filter printed 276 (count) then 0 (mismatches) then [] - ZERO disagreements between Lean lastSegment and Python split('`__`')[-1] across every consecutive-separator, leading-separator, trailing-separator, empty and unicode edge. The Lean pure def is a faithful deep model of pieces[-1]. Also confirmed by construction that splitOn on a non-empty separator never yields [], so the getLastD default is unreachable (this is what makes atk_16 extensionally equal).

**WHY THE SPEC HOLDS.** problem_spec_orderingExpandsRelation is a total iff pinning result exactly to the four-conjunct condition over the free inputs, with the fix-bearing conjunct compared against the actual computed lastSegment path. That leaves no slack: any impl that differs from the real post-patch guard on ANY reachable input differs from the spec on that input and the obligation cannot close. My attacks probed every axis a weak spec usually leaks on - partial domain (atk_2 on an attname value, atk_15 on a whole reachable path class), boundary (atk_3 pk dropped, atk_11 pk mis-scoped), control-flow effect (atk_4 post-guard mutation), ungrounded-oracle echo (atk_5 single-observation echo, atk_13 decide-the-spec), deep-model corruption (atk_8 wrong separator, atk_7 suffix instead of exact match, atk_12 None-bijection break), and the narrow F2P-passing-but-wrong fix (atk_17). All 13 wrong ones were rejected; only extensionally-equal rivals survived, and all four survivors RESOLVE.

**VERDICT SOUND.** 17 same-spec attacks encoded and machine-checked (>=5 required; 13 semantically wrong, all rejected with sorryAx); positive control verifies with clean [propext]; prepatch bug reproduced two independent ways; 4 closing clean-axiom impls all had faithful patches materialized, git apply --check'd at base_commit, and EXECUTED through run_resolve with 4/4 RESOLVED=True. No impl exists with a closing clean-axiom proof whose faithful patch fails to resolve, so verify => correct is not falsified. A-legs: none declared and none needed - the behavior is modeled deeply and I independently confirmed the deep model against the real callee semantics.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 13 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_11.lean`, `atk_12.lean`, `atk_15.lean`, `atk_16.lean`, `atk_17.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_9.lean`, `atk_10.lean`, `atk_13.lean`, `atk_14.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found - the spec is NOT broken. All 13 semantically-WRONG same-spec impls FAILED to close (exit 1, sorryAx present in #print axioms). The 4 impls whose proofs DID close with clean axioms (atk_9, atk_10, atk_13, atk_14) are all extensionally EQUAL to gold (different syntactic route to the same boolean), and their materialized faithful patches were each RUN through run_resolve: ALL FOUR RESOLVED=True (F2P test_order_by_self_referential_fk passes, 26/26 P2P pass). So no closing clean-axiom proof has a non-resolving faithful patch: verify=>correct is NOT falsified.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SETUP.** Fresh base_commit worktree (git a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e). All 18 files (17 attacks + positive control) built by copying Solution.lean and editing ONLY the impl region; same_spec(Solution.lean, atk_N.lean, LeanBackend) = True for ALL 18 (verified via swebench_unified.markers.same_spec). Verify cmd per file: bash scripts/lean_verify.sh <D>/atk_N.lean ; an `_ax`.lean twin with a trailing '#print axioms correct_orderingExpandsRelation' gave the axiom read.

**POSITIVE CONTROL.** atk_pos.lean is byte-identical to Solution.lean (diff empty). EXIT=0; #print axioms => 'depends on axioms: [propext]' (clean, no sorryAx/native_decide). Non-vacuity established.

PREPATCH REPRODUCED (2 ways). (a) atk_1.lean re-encodes the prepatch bug (fieldAttr != some path, i.e. compared against the WHOLE lookup instead of the final segment): EXIT=1, axioms [propext, sorryAx]. Error is exactly the discriminating obligation 'lastSegment path = path' under hr/ho/ha/hp. Divergence at fieldIsRelation=true, relatedHasOrdering=true, fieldAttr=some "root_id", path="record__root_id": impl=true, spec=false (lastSegment="root_id"=fieldAttr => no expansion). (b) The bundle's own Solution_prepatch.lean copied to <D>/prepatch.lean: EXIT=1 ('simp made no progress' at the hc-case rewrite). Both confirm the guard-fix is load-bearing.

### REJECTED WRONG IMPLS (13, all EXIT=1 with sorryAx => proof did NOT close; no patch/resolve owed).
1 atk_1 prepatch echo (whole path) - [propext,sorryAx]; div fr=T ro=T fa='root_id' p='record__root_id'. 2 atk_2 PARTIAL-DOMAIN: carves out fieldAttr=some "" -> false - [propext,sorryAx,Quot.sound]; div fa='' p='record'. 3 atk_3 BOUNDARY: pk-shortcut conjunct dropped - [propext,sorryAx]; unsolved 'False' in the path="pk" case; div p='pk'. 4 atk_4 CONTROL-FLOW-EFFECT: 'let mut r' then a second write r:=true when path=="" clobbers the decision - [propext,sorryAx,Quot.sound]; div p=''. 5 atk_5 UNGROUNDED-ORACLE ECHO of one observation: return (path != "pk") - [propext,sorryAx]; 304 divergences over my grid. 6 atk_6 fix-bearing attname conjunct dropped entirely - [propext,sorryAx].

7 atk_7 SUFFIX heuristic path.endsWith attr instead of exact final-segment equality - [propext,sorryAx,Quot.sound]; div fa='' p='record' and fa='root_id' p='xroot_id'. 8 atk_8 WRONG SEPARATOR: splitOn `"_"` (single underscore) instead of "`__`" - [propext,sorryAx]; div fa='root_id' p='record__root_id' (single-split yields 'id'). 9 atk_11 BOUNDARY: pk exclusion tested on lastSegment instead of the whole path - [propext,sorryAx]; div p='a__pk'. 10 atk_12 Option/None bijection BREAK: a field with no stored attribute counts as matching - [propext,sorryAx,Classical.choice,Quot.sound]; div fa=None. 11 atk_15 PARTIAL-DOMAIN over a reachable class: single-segment lookups never expand - [propext,sorryAx,Quot.sound]; div p='record'.

12 atk_17 NARROW F2P-TARGETED fix: suppresses expansion only when the matching segment ends in '`_id`', so any non-`_id` attname match still wrongly expands - [propext,sorryAx,Classical.choice,Quot.sound]. This is the most dangerous shape (it passes the F2P test yet is wrong in general) and the spec still rejects it. 13 atk_16 unreachable-default sentinel in getLastD - EXIT=1 [propext,sorryAx]. NOTE: this impl is extensionally EQUAL to gold, so its non-closure is a proof-effort artifact (I could not discharge splitOn-nonempty; String.splitOn_ne_empty does not exist in this Mathlib and unfolding splitOnAux blew the whnf heartbeat budget), NOT evidence of a spec defect. It is reported for completeness and owes no resolve (nothing closed).

CLOSING CLEAN-AXIOM IMPLS => MANDATORY RESOLVE RUNS (4). Each is extensionally equal to gold via a DIFFERENT syntactic route, so each needed a materialized faithful patch through the official harness. Patches built in the base_commit worktree, each checked with 'git apply --check' (all 4 APPLY at a59de6e8) and run via swebench_unified.harness.run_resolve('django__django-13033', diff).
- atk_9.lean (conjuncts REORDERED: attname/pk tests first, then is_relation/ordering): lean_verify EXIT=0, axioms [propext] CLEAN. Patch atk_9.diff reorders the four conjuncts in the real guard. RESOLVE: RESOLVED=True, completed=True, F2P success ['test_order_by_self_referential_fk'], 26/26 P2P success, 0 PASS_TO_FAIL (note='resolved on attempt 3/3 (flaky: earlier attempt failed or did not complete)', attempts=3).
- atk_10.lean (De Morgan / negated early-return form): lean_verify EXIT=0, axioms [propext, Classical.choice, Quot.sound] - CLEAN (no sorryAx/sorry/native_decide; Classical.choice+Quot.sound are ordinary Mathlib-classical deps, same family the gold proof draws on). Patch replaces the guard with an 'expand = True' + four elif guard-clauses form. RESOLVE: RESOLVED=True, F2P pass, 26/26 P2P, note='resolved', attempts=1, flaky=False.
- atk_13.lean (UNGROUNDED-ORACLE ECHO lane: impl is literally 'decide (<the postcondition>)'): lean_verify EXIT=0, axioms [propext] CLEAN. This is the sharpest echo attack - a decide-the-spec impl closes trivially by construction. Its faithful patch expresses the guard as all((is_relation, bool(ordering), attname != pieces[-1], name != 'pk')). RESOLVE: RESOLVED=True, F2P pass, 26/26 P2P, attempts=1. Verdict on the echo: because the postcondition is FULLY GROUNDED in the four free inputs (no oracle parameter, no result-echoing hypothesis) and lastSegment is a concrete computable function, 'decide (spec)' IS a correct implementation - the echo is benign here, and the harness agrees.
- atk_14.lean (final segment by INDEXING the split list, segs[segs.length-1]!): lean_verify EXIT=0, axioms [propext, Classical.choice, Quot.sound] CLEAN (needed an induction lemma l[l.length-1]! = l.getLastD ""). Patch uses pieces[len(pieces)-1]. RESOLVE: RESOLVED=True, F2P pass, 26/26 P2P, attempts=1.
Bottom line on the A-of-verify-implies-correct leg: 4 closing clean-axiom proofs, 4 materialized applying patches, 4 EXECUTED resolve runs, 4/4 RESOLVED=True. No verify-but-not-resolve pair exists among them.

A-LEG AUDIT (my assigned focus). meta.json declares axioms=[] and deep_model_references=[]; grep -E '^(axiom|opaque|@[extern])' over Solution.lean returns NOTHING, so there is genuinely no axiom/opaque callee contract and no deep-model reference to validate. axiom_check.py is an honest skip stub (prints status=skip, exit 0) and G-AX is recorded status=pass/skip consistently - no A-consumed or A-reference leg exists to be unfaithful. I verified the framing is legitimate rather than an evasion: the guard's own computation is the split plus the (in)equality tests, and BOTH are modeled deeply in Lean (String.splitOn/getLastD, Option/String (in)equality) rather than axiomatized.

The only thing framed as free input is the `_setup_joins`/setup_joins resolution, and I confirmed at base_commit that (a) the gold patch touches ONLY the guard line (patch.diff is a single hunk at compiler.py:727) so the resolution is byte-identical pre/post patch, and (b) setup_joins does NOT mutate its 'names' argument (it only slices names[:pivot]/names[pivot:] and appends to a separate joins list), so 'pieces' at line 730 is exactly name.split('`__`') from line 724 - the mapping.md claim 'pieces[-1] is exactly the final `__`-separated segment of name' holds. Framing the resolution as free inputs is therefore sound, not an ungrounded oracle.

**REFINEMENT.MD LEG AUDIT.** Six legs, tags 1=R, 2=I, 3=I, 4=I, 5=R, 6=R. No leg is A-consumed or A-reference (consistent with axioms=[]), and NO leg is kind-3 (unjustified/hand-waved) - each R leg names the concrete counterpart it abstracts and why the abstraction is patch-invariant (leg 1: resolved observations, unchanged by the patch; leg 5: the fall-through trim_joins + direct OrderBy, downstream of the decision; leg 6: the modeled outcome IS the branch-entered boolean). Legs 2-4 I-tags are byte-level accurate against the post-patch source I read in the worktree: leg 2 pieces[-1] <-> (path.splitOn "`__`").getLastD "", leg 3 the != inequality incl. the None/none case, leg 4 the four-way conjunction incl. name != 'pk'. Only nit, non-blocking: leg 2 is tagged 'I' while also being the changed op; leg 5's claim that the direct-column branch is 'not part of the modeled decision' is a legitimate R abstraction, not a kind-3 gap. Correspondence to the real callees holds.

DEEP-MODEL DIFFERENTIAL (my own, independent of G-CONF). I did not take the bundle's split-equivalence claim on trust. Built <D>/split_diff2.lean pairing 276 inputs with their Python name.split('`__`')[-1] value (hand-picked edges: '', `'_'`, '`__`', '`___`', '`____`', '`_____`', 'a__', '`__a`', '`__a__`', 'a___b', 'a____b', 'a_____b', 'pk', '`__pk`', 'pk__', 'record__root_id', 'author__editor_id', 'record__root__id', unicode 'lie__ming'/'snowman__b', an embedded newline, plus 400 random strings over the alphabet {a,b,_,`__`,`___`,pk} seeded 13033, deduped). lean_verify EXIT=0; #eval of the mismatch filter printed 276 (count) then 0 (mismatches) then [] - ZERO disagreements between Lean lastSegment and Python split('`__`')[-1] across every consecutive-separator, leading-separator, trailing-separator, empty and unicode edge. The Lean pure def is a faithful deep model of pieces[-1]. Also confirmed by construction that splitOn on a non-empty separator never yields [], so the getLastD default is unreachable (this is what makes atk_16 extensionally equal).

**WHY THE SPEC HOLDS.** problem_spec_orderingExpandsRelation is a total iff pinning result exactly to the four-conjunct condition over the free inputs, with the fix-bearing conjunct compared against the actual computed lastSegment path. That leaves no slack: any impl that differs from the real post-patch guard on ANY reachable input differs from the spec on that input and the obligation cannot close. My attacks probed every axis a weak spec usually leaks on - partial domain (atk_2 on an attname value, atk_15 on a whole reachable path class), boundary (atk_3 pk dropped, atk_11 pk mis-scoped), control-flow effect (atk_4 post-guard mutation), ungrounded-oracle echo (atk_5 single-observation echo, atk_13 decide-the-spec), deep-model corruption (atk_8 wrong separator, atk_7 suffix instead of exact match, atk_12 None-bijection break), and the narrow F2P-passing-but-wrong fix (atk_17). All 13 wrong ones were rejected; only extensionally-equal rivals survived, and all four survivors RESOLVE.

**VERDICT SOUND.** 17 same-spec attacks encoded and machine-checked (>=5 required; 13 semantically wrong, all rejected with sorryAx); positive control verifies with clean [propext]; prepatch bug reproduced two independent ways; 4 closing clean-axiom impls all had faithful patches materialized, git apply --check'd at base_commit, and EXECUTED through run_resolve with 4/4 RESOLVED=True. No impl exists with a closing clean-axiom proof whose faithful patch fails to resolve, so verify => correct is not falsified. A-legs: none declared and none needed - the behavior is modeled deeply and I independently confirmed the deep model against the real callee semantics.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFUL — no diverging input found. `problem_spec_orderingExpandsRelation` / `implementation_orderingExpandsRelation` agree with the POST-PATCH `SQLCompiler.find_ordering_name` guard (compiler.py:730-735) on every input I could reach in the real repo.

**SETUP.** Fresh worktree from the upstream repository at base_commit a59de6e89e8dc1f3e71c9a5a5bbceb373ea5247e (the pre-existing * worktree was STALE — it contained astropy, not django, so I did not use it). Applied patch.diff (verified the guard now reads `getattr(field,'attname',None) != pieces[-1]`) plus the test_patch models.py hunk (Author.editor self-FK).

(1) MECHANICAL. scripts/lean_verify.sh Solution.lean -> exit 0, no sorry. `#print axioms` on correct_orderingExpandsRelation, implementation_orderingExpandsRelation, lastSegment = [propext] only — no sorryAx, proof is real. markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True (spec region byte-identical; the elided-impl spec view is identical across both).

(2) END-TO-END DIFFERENTIAL vs REAL POST-PATCH DJANGO. Instrumented the patched guard in compiler.py to log (field.is_relation, bool(opts.ordering), getattr(field,'attname',None), name, pieces[-1], guard-taken) at every evaluation, then drove 256 real guard evaluations (71 distinct input tuples) through `str(Model.objects.order_by(lookup).query)` over purpose-built models. Replayed all 71 distinct tuples through the actual Lean `implementation_orderingExpandsRelation` (not a Python re-implementation): 0 disagreements. Shapes covered:
  - F2P case: Article.order_by('author__editor') -> rel=1 ord=1 attr=editor_id last=editor -> real=1=spec; order_by('author__editor_id') -> last=editor_id=attr -> real=0=spec. Exactly the patch delta, and the spec sides with post-patch.
  - The mapping.md motivating path record__root_id (attr=root_id) -> real=0=spec; record__root -> 1; record__root__id -> 0.
  - Direction prefix: '-record__root_id' and '-pk' — get_order_dir strips '-' upstream, path arrives already stripped; matched (confirms the `path` free-input modeling in mapping.md is right, not a hidden divergence).
  - Reverse relations with NO attname (attname=None -> Lean `none`): Tagged.order_by('revholders'), 'children', Root.order_by('record'), Root.order_by('holder_o2o'). Confirms the `None != s` <-> `none != some s` bijection claim in mapping.md.
  - M2M ('tags', 'tagged__tags', 'tagged__tags_id'), OneToOne ('o2o', 'o2o_id'), related model WITHOUT Meta.ordering ('record__plain', 'record__plain_id' -> ord=0 -> 0).
  - Transforms where pieces[-1] is NOT a field at all: 'when__year', 'when__date', 'payload__key', 'payload__a__b', 'tagged__parent__when__year'. All matched (is_relation=0 short-circuits before the segment compare).
  - SHARPEST CASE — multi-table inheritance, where the pk IS a relation (parent_link), the only shape that can separate the `path != "pk"` conjunct from the `lastSegment` conjunct: Child.order_by('pk') gives rel=1, ord=1, attr=base_ptr_id, lastSegment('pk')='pk' != attr, so ONLY the `path != "pk"` clause suppresses expansion — real=0=spec. Contrast PointsAtChild.order_by('child__pk') -> path='child__pk' != 'pk', lastSegment='pk' != base_ptr_id -> real=1=spec. Both directions of that clause are exercised and both match; the fourth conjunct is load-bearing and correctly placed.
  - Recursion: nested guard evaluations inside the expansion branch (path='pk', path='root', path='btitle') were logged and checked too, not just top-level calls.

(3) lastSegment vs Python `name.split('__')[-1]`. This is the ONLY computation the spec performs, so I attacked it hardest. Evaluated `(path.splitOn "__").getLastD ""` inside Lean against the Python oracle on 5315 inputs — exhaustive over {a,_}^<=7 and {a,b,_}^<=5 (which saturates every overlapping-separator alignment), plus 6000 random strings over 'ab__cd_', plus django-shaped paths. 0 disagreements. Separately 2009 non-ASCII inputs (é/中/𝕏/Ω/ı/İ/ß/ñ, incl. astral-plane) -> 0 disagreements, ruling out a Lean UTF-8-codepoint vs Python-str indexing divergence. Notably the tricky alignments agree: 'a___b'->'`_b`', 'a____b'->'b', '`__`'->'', 'a__'->'', '`__a`'->'a', ''->''. `getLastD ""` never fires its default on a reachable input (splitOn on a non-empty separator always returns a non-empty list), so the '' default is not a silent divergence.

(4) STRUCTURAL ASSUMPTION CHECKED, NOT ASSUMED. The spec derives the final segment from `path` by splitting, whereas the real code uses the separately-bound local `pieces`. If `setup_joins` mutated its `names` argument in place, `pieces[-1]` at line 733 could differ from `name.split('__')[-1]` and the spec would be unfaithful. I logged BOTH values at every one of the 256 guard evaluations: pieces[-1] == name.split('`__`')[-1] in 256/256. No divergence.

SCOPE / RESIDUAL RISK (honest limits). The modeled function is the boolean 'is the default-ordering-expansion branch entered', with the join/field resolution (`_setup_joins`) read as free inputs. That abstraction is legitimate here because the patch does not touch resolution and it runs identically on both sides of the guard, so it cannot be the site of the delta; refinement.md tags it R and declares no axioms (G-AX correctly skips, and I confirmed there is no opaque/axiom content to be vacuous). The contents of the expansion branch (the recursion, the FieldError infinite-loop guard) and the direct-column OrderBy branch are outside the model — that is a narrowing of scope, which is a G-PANEL-1 (too-weak) question, not a faithfulness one; on its declared domain the spec is exact. I did not find any input on which the modeled function disagrees with the real post-patch callee, and per the brief I did NOT treat the base-version guard's behavior on record__root_id / author__editor_id as a divergence — that difference IS the patch delta and the spec correctly describes the fixed side.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

ATTACKER-3 (leakage / gold-reconstruction), django__django-13033/lean. Verdict NO-LEAKAGE.

**NO RELAXATION IN THIS BUNDLE.** I checked for one rather than assuming: no RELAXED_LEAKAGE.md anywhere under the instance dir (`find -iname '*relax*'` empty), and meta.json has no `relaxed_leakage` key (top-level keys are axioms, conf_skip, deep_model_references, gates, instance_id, modeled_functions, notes, pbt_audit, region_hashes, schema_version, spec_provenance, verifier_pins; grep for 'relax' over the full JSON is empty). So this is judged as a plain full-strength leakage cell, and the disposition below is entirely my own measurement.

### WHAT I MEASURED (spec view = the solver-visible surface).
Computed the actual spec view with swebench_unified.markers.spec_view under the real lean Backend (not a string arg -- `_tables` rejects that). impl and proof regions collapse to '-- implementation elided' / '-- proof elided'; docstring, axioms note, `pure` region (lastSegment) and post-condition survive. Confirmed via eval/prompts.py that this rendered spec view (plus repo-side modeled_functions localization) is what reaches the solver -- refinement.md / mapping.md / meta.json / verdict.md are NOT solver-visible, so I judged only the spec view.

same_spec(Solution.lean, Solution_prepatch.lean) = True -- byte-identical spec region, so the spec view cannot tell the solver which side is gold.

CORE GATES RE-CONFIRMED BY ME, not inherited:
- scripts/lean_verify.sh Solution.lean -> exit 0. Appended `#print axioms correct_orderingExpandsRelation` -> exit 0, "depends on axioms: [propext]". Clean; no sorryAx, so the proof is real. (meta.json's construction note predicts propext+Quot.sound; actual is propext only -- strictly cleaner, not a defect.)
- scripts/lean_verify.sh Solution_prepatch.lean -> exit 1, real elaboration failures at :106 and :112 (`simp made no progress`), i.e. the prepatch genuinely does not verify. G-DIFF sound.

MECHANICAL SCREEN (leakage.screen, lean backend, gold patch + problem_statement + test_patch): passed=True, hard_failures=[], warnings=[]. Independently re-derived the components: diff markers in spec view = none; gold-diff lines reproduced verbatim (whitespace-normalized) = only '):' , a content-free multi-line-signature fragment; narration vocabulary hits (`_NARRATION_RE` over the spec view) = ZERO -- notably the spec view avoids 'fix/bug/wrong/incorrectly' entirely, and the prepatch's bug-narrating impl/proof comments sit inside the elided regions so they never reach the solver.

**NO REPO-SIDE LOCALIZATION.** Token sweep over the spec view: find_ordering_name, compiler.py, pieces, attname, is_relation, opts.ordering, get_order_dir, trim_joins, setup_joins, already_seen, LOOKUP_SEP, OrderBy, django -- ALL absent. Only 'sql' and 'queryset' appear, and both are in the public problem_statement. The spec view names no patched file, no patched symbol, and no diff hunk.

THE DISCRIMINATOR, AND WHY IT IS NOT A LEAK. I ran the load-bearing test rather than arguing it: took Solution_prepatch.lean, weakened ONLY the post-condition `fieldAttr ≠ some (lastSegment path)` to `fieldAttr ≠ some path` (and matched the carried proof's hc-case guard so elaboration was fair), wrote it to a mktemp dir, and lean_verify'd it -> EXIT 0. The weakened spec verifies against the PRE-patch impl. So the `lastSegment` clause is exactly load-bearing: strip it and the buggy base_commit behavior satisfies the spec. A faithful spec must contain it.

Crucially, this cell needs no relaxation to justify it, because the clause is derivable from the PUBLIC problem_statement alone (checked, not assumed -- hints_text ignored throughout). The statement itself contrasts order_by('record__root_id') (reported: spurious extra JOIN + unwanted DESC inherited from OneModel.Meta.ordering) against order_by('record__root__id') (reported: correct, single JOIN, orders the column directly), notes 'record__root' yields the same SQL as 'record__root_id', and states the reporter's expectation that 'the order_by() to take precedence'. That is precisely the spec's clause: when the lookup's trailing segment designates the relation's own stored `_id` column, order by that column directly and do NOT expand the related model's default ordering.

Substrings '`_id`', 'record__root_id', 'record__root__id', 'ordering', 'Meta', 'primary_key' are all present in the public text. The spec view states the required BEHAVIOR (which is its job) at an abstraction the public bug report already fixes; it does not reveal the edit (that the third guard conjunct's right operand changes from `name` to `pieces[-1]` inside find_ordering_name). The `lastSegment` helper models the '`__`' separator that the statement's own lookup syntax exhibits, without naming pieces/LOOKUP_SEP.

Cross-check that the spec matches gold rather than over-reaching: F2P test_order_by_self_referential_fk asserts order_by('author__editor') KEEPS the related default ordering while order_by('author__editor_id') does not -- consistent with the spec's final-segment condition (attname 'editor_id' equals the final segment only in the second case) and with the statement's own 'record__root gives the exact same SQL' remark.

**NO BUNDLE FILE ADDRESSES ME.** Ran leakage.reviewer_directed over verdict.md, meta.json, refinement.md, mapping.md, Solution.lean, Solution_prepatch.lean, conformance_check.py, axiom_check.py -> [] for every file, and my own grep for reviewer-steering phrasing found nothing. The single 'G-PANEL' occurrence (refinement.md:60) is a factual citation of which gate the prepatch failure feeds, and verdict.md:1718 is a prior recorded panel row -- neither instructs me how to record or which verdict is honest. Nothing to report as a steering finding.

**Residual:** none that rises to LEAKAGE. The spec view is a behavioral postcondition whose discriminating clause is both unavoidable (measured) and publicly derivable (measured).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
