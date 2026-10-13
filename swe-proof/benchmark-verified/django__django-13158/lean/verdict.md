# P2 adversarial audit — django__django-13158

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `ctl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is provably SINGLE-VALUED, so no divergent same-spec impl can verify. Independent Lean proof: uniq.lean, `timeout 400 bash scripts/lean_verify.sh .../uniq.lean 360` -> exit 0, `#print axioms spec_unique` = [propext, Classical.choice, Quot.sound] (no sorryAx). spec_unique: forall q r1 r2, problem_spec_makeEmpty q r1 -> problem_spec_makeEmpty q r2 -> r1 = r2. Mechanism: YieldsNothing pins every selfEmpty marker to true recursively, and toShape result = toShape q pins the exact nested child structure INCLUDING order; together they determine the output tree uniquely on every input. Hence the falsification battery is exhaustive by construction, and the 8 wrong impls are not merely rejected-by-tactic-failure but PROVABLY outside the spec (8 closing disproofs, below). The one verifying attack (atk_8) is a correct echo: its faithful patch RESOLVED under the official harness.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,19 +84,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- PREPATCH: force only THIS node's row-selection to match nothing and carry
+the combined sub-queries through untouched (the pre-fix `set_empty`). -/
 def implementation_makeEmpty : Query → Query
   | .mk _ combined => Id.run do
     -- Force this node's own row-selection to match nothing.
-    let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
-    for sub in combined do
-      subs := subs ++ [implementation_makeEmpty sub]
-    return Query.mk true subs
-decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
+    return Query.mk true combined
 -- impl-end
 
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,17 +84,18 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- WRONG (partial domain): force this node empty and recurse into only the
+FIRST combined sub-query; the remaining ones are carried through untouched. -/
 def implementation_makeEmpty : Query → Query
   | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
     let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
+    let mut done := false
     for sub in combined do
-      subs := subs ++ [implementation_makeEmpty sub]
+      if done then
+        subs := subs ++ [sub]
+      else
+        subs := subs ++ [implementation_makeEmpty sub]
+        done := true
     return Query.mk true subs
 decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,17 +84,19 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- WRONG (off-by-one boundary): recurse into every combined sub-query except
+the LAST one. -/
 def implementation_makeEmpty : Query → Query
   | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
+    let n := combined.length
+    let mut i := 0
     let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
     for sub in combined do
-      subs := subs ++ [implementation_makeEmpty sub]
+      if i + 1 < n then
+        subs := subs ++ [implementation_makeEmpty sub]
+      else
+        subs := subs ++ [sub]
+      i := i + 1
     return Query.mk true subs
 decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,19 +84,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- WRONG (frame): return a forced-empty plain leaf, dropping the combined
+sub-queries instead of forcing them empty. -/
 def implementation_makeEmpty : Query → Query
-  | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
-    let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
-    for sub in combined do
-      subs := subs ++ [implementation_makeEmpty sub]
-    return Query.mk true subs
-decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
+  | .mk _ _ => Query.mk true []
 -- impl-end
 
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,18 +84,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- WRONG (own effect dropped): recurse into every combined sub-query but
+never force THIS node's own row-selection to match nothing. -/
 def implementation_makeEmpty : Query → Query
-  | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
+  | .mk e combined => Id.run do
     let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
     for sub in combined do
       subs := subs ++ [implementation_makeEmpty sub]
-    return Query.mk true subs
+    return Query.mk e subs
 decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,18 +84,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- WRONG (frame, inflating): force everything empty but also append a fresh
+forced-empty sub-query to the combination. -/
 def implementation_makeEmpty : Query → Query
   | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
     let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
     for sub in combined do
       subs := subs ++ [implementation_makeEmpty sub]
-    return Query.mk true subs
+    return Query.mk true (subs ++ [Query.mk true []])
 decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,19 +84,14 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- WRONG (depth-limited): force this node empty and force each immediate
+combined sub-query's own row-selection empty, but do not recurse deeper. -/
 def implementation_makeEmpty : Query → Query
   | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
     let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
     for sub in combined do
-      subs := subs ++ [implementation_makeEmpty sub]
+      subs := subs ++ [Query.mk true sub.combined]
     return Query.mk true subs
-decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
 -- impl-end
 
 
```

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,17 +84,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- WRONG (ordering): force this node and every combined sub-query empty, but
+emit the combination in REVERSED order. -/
 def implementation_makeEmpty : Query → Query
   | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
     let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
     for sub in combined do
-      subs := subs ++ [implementation_makeEmpty sub]
+      subs := implementation_makeEmpty sub :: subs
     return Query.mk true subs
 decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
 -- impl-end
```

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -84,17 +84,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Force a query to return an empty result set: mark this node's own
-row-selection to match nothing, and recurse into every combined sub-query so the
-guarantee holds of the whole tree. Skeleton of the imperative fix (mark self,
-then loop over the combined sub-queries forcing each empty). -/
+/-- Alternative impl (echo A): same operation, accumulating the forced
+sub-queries with `List.concat`. -/
 def implementation_makeEmpty : Query → Query
   | .mk _ combined => Id.run do
-    -- Force this node's own row-selection to match nothing.
     let mut subs : List Query := []
-    -- Recurse into each combined sub-query so it, too, returns nothing.
     for sub in combined do
-      subs := subs ++ [implementation_makeEmpty sub]
+      subs := subs.concat (implementation_makeEmpty sub)
     return Query.mk true subs
 decreasing_by all_goals (have h := List.sizeOf_lt_of_mem ‹_ ∈ _›; simp_all; omega)
 -- impl-end
@@ -104,7 +100,7 @@
 theorem correct_makeEmpty :
     ∀ q : Query, problem_spec_makeEmpty q (implementation_makeEmpty q) := by
   have forIn_aux : ∀ (combined acc : List Query),
-      (forIn combined acc fun sub r => (do pure PUnit.unit; pure (ForInStep.yield (r ++ [implementation_makeEmpty sub]))) : Id (List Query))
+      (forIn combined acc fun sub r => (do pure PUnit.unit; pure (ForInStep.yield (r.concat (implementation_makeEmpty sub)))) : Id (List Query))
         = acc ++ combined.map implementation_makeEmpty := by
     intro combined
     induction combined with
@@ -112,8 +108,8 @@
     | cons h t ih =>
       intro acc
       simp only [List.forIn_cons, bind_pure_comp, map_pure, pure_bind, List.map_cons] at ih ⊢
-      rw [ih (acc ++ [implementation_makeEmpty h])]
-      simp [List.append_assoc]
+      rw [ih (acc.concat (implementation_makeEmpty h))]
+      simp [List.concat_eq_append, List.append_assoc]
   have impl_eq : ∀ (e : Bool) (combined : List Query),
       implementation_makeEmpty (.mk e combined) = Query.mk true (combined.map implementation_makeEmpty) := by
     intro e combined
@@ -141,4 +137,5 @@
       intro sub hsub
       exact (ih sub hsub).2
 
+#print axioms correct_makeEmpty
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -141,4 +141,6 @@
       intro sub hsub
       exact (ih sub hsub).2
 
+
+#print axioms correct_makeEmpty
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 9 same-spec attacks (all same_spec=True, unsound_evasions=[]), 8 rejected + 1 correct echo; positive control verifies. Spec regions (axioms/pure/post-conditions) confirmed BYTE-IDENTICAL to the frozen Solution.lean for all 10 files; only the impl (and elided proof) region was edited.

A-LEG AUDIT (the assigned focus). Solution.lean contains NO `axiom`/`opaque` (grep: NONE) and no sorry/admit/native_decide; meta.json axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a documented skip stub. So there are no A-consumed and no A-reference legs to falsify, and there is no dead axiom. refinement.md's 2 modeled ops are tagged R and R+I; the 2 remaining rows are the hunk-1 non-op (tagged —). No kind-3 (changed-inexpressible) leg: the CHANGED behavior (recursing force-empty into every combined sub-query) is modeled DEEPLY as a self-call to implementation_makeEmpty, never axiomatized, per spec_guide §3. Leg taxonomy is therefore complete and correctly tagged.

### ATTACKS (cmd for each: `bash scripts/lean_verify.sh <path>`; all):
1. atk_1.lean PREPATCH bug re-encoded (only the top node's marker flipped; combined sub-queries carried through untouched) -> exit 1. prepatch_reproduced=true.
2. atk_2.lean PARTIAL-DOMAIN (recurse into the FIRST combined sub-query only) -> exit 1.
3. atk_3.lean BOUNDARY off-by-one (every combined sub-query except the LAST) -> exit 1.
4. atk_4.lean FRAME-deflating (returns a forced-empty leaf, dropping the combination) -> exit 1.
5. atk_5.lean CONTROL-FLOW-EFFECT dropped (recursion runs but this node's own marker is never forced) -> exit 1.
6. atk_6.lean FRAME-inflating (appends a fresh forced-empty sub-query) -> exit 1.
7. atk_7.lean DEPTH-LIMITED (forces immediate children's own markers but does not recurse deeper — models `q.where.add(NothingNode(), AND)` instead of `q.set_empty()`) -> exit 1.
8. atk_10.lean ORDERING/frame (forces EVERYTHING empty, so YieldsNothing holds, but emits the combination REVERSED) -> exit 1. This probes whether toShape pins child ORDER or merely child COUNT; it pins order.
9. atk_8.lean UNGROUNDED-ORACLE ECHO / alternative correct impl (List.concat accumulator instead of `++ [x]`) -> exit 0, `#print axioms correct_makeEmpty` = [propext, Classical.choice, Quot.sound] (CLEAN, no sorryAx). Per protocol its faithful refined patch WAS materialized and EXECUTED through the official harness: p_atk_8.diff, `git apply --check` OK at base_commit 7af8f41, run_resolve('django__django-13158', ...) -> completed=True resolved=True note='resolved'. A resolving candidate is a correct echo of the gold, NOT a spec weakness. This is the only attack with a closing clean-axiom proof, so the §2 obligation is fully discharged.

**POSITIVE CONTROL:** ctl.lean (gold impl verbatim) -> exit 0, `#print axioms correct_makeEmpty` = [propext, Classical.choice, Quot.sound], clean.

WHY THE 8 REJECTIONS ARE REAL (anti-rubber-stamp step). The carried-over gold tactic script fails on a wrong impl with tactic-level errors ('Type mismatch', unknown `.induct`), which alone does NOT prove the SPEC rejects the impl — it could be my proof script failing to elaborate. So for each of the 8 I additionally PROVED the spec rejects it on a concrete witness: dis_atk_{1..7,10}.lean each state `¬ problem_spec_makeEmpty q0 (implementation_makeEmpty q0)` and ALL 8 close with exit 0 and clean axioms [propext, Classical.choice, Quot.sound] (no sorryAx). Witnesses: .mk false [.mk false []] (atk_1/4/5/6), a two-child union node = the F2P qs1.union(qs2) shape (atk_2/3), depth-2 nesting (atk_7), an ASYMMETRIC two-child tree (atk_10). These are diagnostics, not submitted attacks (they replace the obligation with its negation and so are deliberately not same-spec-admissible).

ADVERSARIAL PROBE OF THE UNMODELED ALIASING LEG (the one substantive concern, adjudicated NOT a G-EQ defect). refinement.md declares gold hunk 1 (clone() deep-copying combined_queries) 'not a modeled op — automatic under Lean's no-aliasing model'. I tested that claim directly: p_hunk2_only.diff = hunk 2 ALONE (the recursion), `git apply --check` OK at base. run_resolve -> completed=True, resolved=FALSE, patch_successfully_applied=TRUE, all 29 PASS_TO_PASS pass, and exactly the F2P test_union_none FAILS (consistent across 3 attempts, then re-confirmed with retries=0 to capture the report).

I reproduced the mechanism locally without the DB (repo_h2): base clone() does a shallow `__dict__`.copy(), so clone.combined_queries[0] IS the original sub-Query; hunk 2's recursion then mutates the SOURCE queryset's sub-queries, so `qs3.none()` is correctly empty (assertion a) but `qs3` itself is corrupted (assertion b breaks). Judgment: this is a real gap between the Lean model and the repo — the model cannot express it, because Lean is referentially transparent and implementation_makeEmpty returns a fresh tree, so hunk 1 is vacuously satisfied and NO same-spec Lean impl can correspond to the hunk2-only patch.

It is therefore NOT a verify⇏!⇒correct counterexample under the G-EQ protocol: a BROKEN verdict requires a wrong impl whose proof CLOSES with clean axioms and whose faithful patch does not resolve. p_hunk2_only.diff is not the faithful refinement of any verifying attack (the only verifying attack, atk_8, refines to the full gold patch and RESOLVES). Every impl that could motivate dropping hunk 1 is itself rejected by the spec. I record it as a documented modeling-scope limitation, already disclosed in refinement.md's 'Aliasing note' and mapping.md — i.e. correctly disclosed rather than concealed. It is a faithfulness/coverage observation (G-PANEL-2 territory) at most, not a spec weakness, and the disclosure is accurate about the mechanism.

**Discarded:** atk_9.lean (reverse-traversal echo) — exit 1 with sorryAx from MY tactic script, not a spec fact; not submitted, since an unproven echo is not evidence in either direction.

Verifications were run concurrently at width <=4 as instructed; the schedule changed, the pass criteria did not.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 admissible attacks re-run of 9 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `ctl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is provably SINGLE-VALUED, so no divergent same-spec impl can verify. Independent Lean proof: uniq.lean, `timeout 400 bash scripts/lean_verify.sh .../uniq.lean 360` -> exit 0, `#print axioms spec_unique` = [propext, Classical.choice, Quot.sound] (no sorryAx). spec_unique: forall q r1 r2, problem_spec_makeEmpty q r1 -> problem_spec_makeEmpty q r2 -> r1 = r2. Mechanism: YieldsNothing pins every selfEmpty marker to true recursively, and toShape result = toShape q pins the exact nested child structure INCLUDING order; together they determine the output tree uniquely on every input. Hence the falsification battery is exhaustive by construction, and the 8 wrong impls are not merely rejected-by-tactic-failure but PROVABLY outside the spec (8 closing disproofs, below). The one verifying attack (atk_8) is a correct echo: its faithful patch RESOLVED under the official harness.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -141,4 +141,6 @@
       intro sub hsub
       exact (ih sub hsub).2
 
+
+#print axioms correct_makeEmpty
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SOUND.** 9 same-spec attacks (all same_spec=True, unsound_evasions=[]), 8 rejected + 1 correct echo; positive control verifies. Spec regions (axioms/pure/post-conditions) confirmed BYTE-IDENTICAL to the frozen Solution.lean for all 10 files; only the impl (and elided proof) region was edited.

A-LEG AUDIT (the assigned focus). Solution.lean contains NO `axiom`/`opaque` (grep: NONE) and no sorry/admit/native_decide; meta.json axioms=[], deep_model_references=[], conf_skip=false; axiom_check.py is a documented skip stub. So there are no A-consumed and no A-reference legs to falsify, and there is no dead axiom. refinement.md's 2 modeled ops are tagged R and R+I; the 2 remaining rows are the hunk-1 non-op (tagged —). No kind-3 (changed-inexpressible) leg: the CHANGED behavior (recursing force-empty into every combined sub-query) is modeled DEEPLY as a self-call to implementation_makeEmpty, never axiomatized, per spec_guide §3. Leg taxonomy is therefore complete and correctly tagged.

### ATTACKS (cmd for each: `bash scripts/lean_verify.sh <path>`; all):
1. atk_1.lean PREPATCH bug re-encoded (only the top node's marker flipped; combined sub-queries carried through untouched) -> exit 1. prepatch_reproduced=true.
2. atk_2.lean PARTIAL-DOMAIN (recurse into the FIRST combined sub-query only) -> exit 1.
3. atk_3.lean BOUNDARY off-by-one (every combined sub-query except the LAST) -> exit 1.
4. atk_4.lean FRAME-deflating (returns a forced-empty leaf, dropping the combination) -> exit 1.
5. atk_5.lean CONTROL-FLOW-EFFECT dropped (recursion runs but this node's own marker is never forced) -> exit 1.
6. atk_6.lean FRAME-inflating (appends a fresh forced-empty sub-query) -> exit 1.
7. atk_7.lean DEPTH-LIMITED (forces immediate children's own markers but does not recurse deeper — models `q.where.add(NothingNode(), AND)` instead of `q.set_empty()`) -> exit 1.
8. atk_10.lean ORDERING/frame (forces EVERYTHING empty, so YieldsNothing holds, but emits the combination REVERSED) -> exit 1. This probes whether toShape pins child ORDER or merely child COUNT; it pins order.
9. atk_8.lean UNGROUNDED-ORACLE ECHO / alternative correct impl (List.concat accumulator instead of `++ [x]`) -> exit 0, `#print axioms correct_makeEmpty` = [propext, Classical.choice, Quot.sound] (CLEAN, no sorryAx). Per protocol its faithful refined patch WAS materialized and EXECUTED through the official harness: p_atk_8.diff, `git apply --check` OK at base_commit 7af8f41, run_resolve('django__django-13158', ...) -> completed=True resolved=True note='resolved'. A resolving candidate is a correct echo of the gold, NOT a spec weakness. This is the only attack with a closing clean-axiom proof, so the §2 obligation is fully discharged.

**POSITIVE CONTROL:** ctl.lean (gold impl verbatim) -> exit 0, `#print axioms correct_makeEmpty` = [propext, Classical.choice, Quot.sound], clean.

WHY THE 8 REJECTIONS ARE REAL (anti-rubber-stamp step). The carried-over gold tactic script fails on a wrong impl with tactic-level errors ('Type mismatch', unknown `.induct`), which alone does NOT prove the SPEC rejects the impl — it could be my proof script failing to elaborate. So for each of the 8 I additionally PROVED the spec rejects it on a concrete witness: dis_atk_{1..7,10}.lean each state `¬ problem_spec_makeEmpty q0 (implementation_makeEmpty q0)` and ALL 8 close with exit 0 and clean axioms [propext, Classical.choice, Quot.sound] (no sorryAx). Witnesses: .mk false [.mk false []] (atk_1/4/5/6), a two-child union node = the F2P qs1.union(qs2) shape (atk_2/3), depth-2 nesting (atk_7), an ASYMMETRIC two-child tree (atk_10). These are diagnostics, not submitted attacks (they replace the obligation with its negation and so are deliberately not same-spec-admissible).

ADVERSARIAL PROBE OF THE UNMODELED ALIASING LEG (the one substantive concern, adjudicated NOT a G-EQ defect). refinement.md declares gold hunk 1 (clone() deep-copying combined_queries) 'not a modeled op — automatic under Lean's no-aliasing model'. I tested that claim directly: p_hunk2_only.diff = hunk 2 ALONE (the recursion), `git apply --check` OK at base. run_resolve -> completed=True, resolved=FALSE, patch_successfully_applied=TRUE, all 29 PASS_TO_PASS pass, and exactly the F2P test_union_none FAILS (consistent across 3 attempts, then re-confirmed with retries=0 to capture the report).

I reproduced the mechanism locally without the DB (repo_h2): base clone() does a shallow `__dict__`.copy(), so clone.combined_queries[0] IS the original sub-Query; hunk 2's recursion then mutates the SOURCE queryset's sub-queries, so `qs3.none()` is correctly empty (assertion a) but `qs3` itself is corrupted (assertion b breaks). Judgment: this is a real gap between the Lean model and the repo — the model cannot express it, because Lean is referentially transparent and implementation_makeEmpty returns a fresh tree, so hunk 1 is vacuously satisfied and NO same-spec Lean impl can correspond to the hunk2-only patch.

It is therefore NOT a verify⇏!⇒correct counterexample under the G-EQ protocol: a BROKEN verdict requires a wrong impl whose proof CLOSES with clean axioms and whose faithful patch does not resolve. p_hunk2_only.diff is not the faithful refinement of any verifying attack (the only verifying attack, atk_8, refines to the full gold patch and RESOLVES). Every impl that could motivate dropping hunk 1 is itself rejected by the spec. I record it as a documented modeling-scope limitation, already disclosed in refinement.md's 'Aliasing note' and mapping.md — i.e. correctly disclosed rather than concealed. It is a faithfulness/coverage observation (G-PANEL-2 territory) at most, not a spec weakness, and the disclosure is accurate about the mechanism.

**Discarded:** atk_9.lean (reverse-traversal echo) — exit 1 with sorryAx from MY tactic script, not a spec fact; not submitted, since an unproven echo is not evidence in either direction.

Verifications were run concurrently at width <=4 as instructed; the schedule changed, the pass criteria did not.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ATTACK ROLE:** faithfulness-break (is the spec too strong / drifted from real repo behavior?). Result: NO divergence found. Verdict FAITHFUL.

**MODELED FUNCTION:** Query.set_empty (django/db/models/sql/query.py:1778). Reference = base_commit 7af8f4127397279d19ef7c7899e93018274e2f9b WITH patch.diff APPLIED (per instructions). Base commit used only as the pre-fix control.

ENVIRONMENT NOTE (worth flagging): the supplied worktree was DIRTY -- `git status --porcelain` showed ' M django/db/models/sql/query.py' and the gold patch was already present in the working tree (so `git apply patch.diff` failed with 'patch does not apply' because it was already applied, NOT because of a bad patch). It also carries a stash from an unrelated instance. I did NOT touch it (per standing note: never git stash / mutate a shared worktree during a wave). Instead I built pristine trees from git objects via `git archive HEAD` into my own mktemp -d scratch ({base,patched,base_test}) and applied patch.diff cleanly there.

### Lean artifact checks
1. Solution.lean compiles: scripts/lean_verify.sh exit 0 (no sorry/error).
2. `#print axioms correct_makeEmpty` => [propext, Classical.choice, Quot.sound]. CLEAN -- no sorryAx, proof is real.
3. No `axiom`/`opaque`/`sorry`/`native_decide` tokens in the file (only prose in the axioms region). meta.json axioms=[] and deep_model_references=[] are consistent -- there is genuinely no axiomatized callee to attack, since the per-node 'force empty' is modeled deeply as `selfEmpty := true` and the recursion is a self-call.
4. DISCRIMINATING POWER (anti-vacuity control): Solution_prepatch.lean FAILS to verify -- exit 1 with a genuine elaboration error (unsolved goals: `pure (Query.mk true combined) = Query.mk true (List.map ... combined)`), i.e. the spec rejects the pre-fix impl that flips only the top node. The spec is not vacuous and its strength is exactly the patch delta. Impl-region diff prepatch->gold is precisely the added `for sub in combined` recursion.

### Spec region identity
- Computed region_hashes(Solution.lean) for the SPEC regions match meta.json /region_hashes exactly: axioms=eb1e561a..., pure=c43e829c..., post-conditions=d8aec20c....
- same_spec(Solution.lean, Solution_prepatch.lean, lean_tables) = True -> the two share a byte-identical spec, so the prepatch rejection above is attributable to the impl, not to a weakened contract.
- Minor bookkeeping discrepancy (NOT a faithfulness defect, flagging for the gate owner): meta.json /region_hashes/proof (a9cbc374...) and /region_hashes/spec_view (6ea43277...) do not match the current file (proof=1cb8c24a..., spec_view=7a8931da...), while /gates/G-HYGIENE/data/region_hashes matches the current file exactly (spec_view=7a8931da...). Every individual SPEC region matches both records; only the composite spec_view and the proof region differ at top level. Reads as a stale top-level rollup after a proof-region edit, not spec drift.

### FAITHFULNESS EVIDENCE (real Django objects, not a re-transliteration)
I drove the ACTUAL patched django.db.models.sql.query.Query.set_empty and compared it against the Lean model through the mapping.md abstraction (selfEmpty <-> q.is_empty(); combined <-> q.combined_queries), checking all three spec facts: YieldsNothing(result), toShape result = toShape q, and full model equality implementation_makeEmpty(abstract(pre)) == abstract(post).

(a) Seeded differential, 4012 real Query trees (12 hand-built edge shapes incl. the test_union_none shape + 4000 random, varying where connector AND/OR, negated, depth<=3, fan-out 0-3): checked=4012 fails=0 on the PATCHED tree.
(b) Large randomized differential, 30000 real Query trees / 452215 nodes, depth<=4, fan-out up to 5, where-node content drawn from {plain, real Q lookup, ExtraWhere, nested WhereNode}, random pre-existing NothingNode (35%), random combinator in {union, intersection, difference}: divergences=0.
(c) BASE (pre-fix) control on the same harness diverges immediately and exactly on the union shape (False,[leaf,leaf]) -- real post-state (True,[(False,[]),(False,[])]) fails YieldsNothing. This is the patch delta itself, which per the instructions is NOT reportable as unfaithfulness. It confirms the harness has teeth.

### TARGETED OVER-STRENGTH PROBES (all AGREE with the model)
A. DAG / shared sub-query object present twice in combined_queries -> YieldsNothing True, shape preserved, model_eq True. The tree model does not over-constrain aliased children.

B. Deep chain depth 12 -> agrees; confirms real set_empty recurses to arbitrary depth (not one level), matching the recursive YieldsNothing.

C. Negated OR where-node at every level -> agrees. This is the sharpest probe of the `selfEmpty := true` refinement, since WhereNode.as_sql inverts emptiness under `negated`; is_empty() is defined structurally (any NothingNode among where.children) so the refinement holds regardless.

D. Real Q lookups already in where + subsequent set_empty -> agrees (children ['Exact','NothingNode']).

E. Idempotence: set_empty twice leaves the abstraction unchanged (a1==a2), so the spec's non-idempotent-looking `selfEmpty := true` does not over-constrain.

F. Leaf / empty combined_queries tuple -> agrees.

G. EXHAUSTIVE refinement check of `where.add(NothingNode(), AND)` => is_empty(): all 36 WhereNode configurations (connector in {AND,OR,None} x negated in {False,True} x content in {empty,lookup,nothing,extra,subnode,two}) yield is_empty()==True after set_empty. violations=0. So `selfEmpty := true` is a SOUND refinement of the real per-node op on every reachable where shape -- this was my strongest candidate for a break and it held.

H. SEMANTIC end-to-end on sqlite with real rows: for union / intersection / difference, .none() returns [] and the abstraction is (True,[(True,[]),(True,[])]) with YieldsNothing True. So YieldsNothing genuinely corresponds to 'returns no rows' for ALL THREE combinators, not just the union in the F2P test -- the spec is not silently union-only, and it is not stronger than real behavior on intersection/difference either.

I. Aliasing half (hunk 1): after qs3.none(), source qs3 still returns ['u0','u1','u8','u9'] and its combined_queries have is_empty()==[False,False]. refinement.md's claim that hunk 1 is automatic under Lean's referential transparency is correct and does not hide an unmodeled behavior.

### F2P harness
test_union_none passes on the patched tree (OK) and fails on base (AssertionError: QuerySet [0,1,8,9] != []). Note both initially resolved a stray Django; re-ran with PYTHONPATH pinned to my scratch trees to get the real result.

### Bundle's own conformance
conformance_check.py: checked=120008 disagreements=0 status=pass. Independently reproduced above against real Django objects rather than the bundle's Python replica, so the pass is not merely self-consistent.

### RESIDUAL MODELING LIMITS (judged acceptable, not defects)
- The Lean `Query` inductive cannot represent a CYCLE in combined_queries. Real Python could construct one, but set_empty would then not terminate in the real repo either, so there is no input on which a terminating real behavior disagrees with the model.
- The model carries only selfEmpty + combined per node. Justified: set_empty touches exactly where (one NothingNode append) and, post-fix, recurses; probe G shows no other where state can defeat is_empty(). Every other Query field is untouched by the modeled function, so eliding it cannot make the spec disagree with the real callee on the modeled observation.
- Abstraction is a function (many real Querys -> one Lean value), and set_empty's result abstraction is (True, [...]) independent of the elided state, so the refinement square commutes.

**CONCLUSION:** the spec (YieldsNothing result AND toShape result = toShape q) is exactly as strong as the patched Query.set_empty, no stronger. I could not construct any input on which the modeled function disagrees with the real post-patch callee. No diverging input exists to cite; submitting FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

LEAKAGE ATTACK (role 3) — django__django-13158/lean. No relaxation in this bundle: meta.json has no `relaxed_leakage` key (keys = axioms, conf_skip, deep_model_references, gates, instance_id, modeled_functions, notes, patch_equals_gold, prepatch_files, region_hashes, schema_version, spec_provenance) and `find` over the instance root shows no RELAXED_LEAKAGE.md, so this is judged as an ordinary strict-leakage review, not an inherited disposition. No file in the bundle addresses the reviewer or instructs how to record a verdict (grepped Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, properties.py, conformance_check.py, axiom_check.py for 'you must / should / submit / honest verdict / auditor / panel_3' — zero hits). meta.json gates.G-PANEL-3 carries a prior NO-LEAKAGE note; I re-derived every claim below myself rather than adopting it.

### What I ran
(1) Spec-region identity: PYTHONPATH=src markers.same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True. Per-region sha256: axioms/pure/post-conditions identical across post- and pre-patch (eb1e561a…, c43e829c…, d8aec20c…); only impl (6e6def3d… vs 6346fd25…) and proof (1cb8c24a… vs b2f87c98…) differ. So the consumer spec view is stable across the patch and cannot encode the edit by differing from the prepatch view. (Note for the record: meta.json region_hashes.proof = a9cbc374… and .spec_view = 6ea43277… do NOT match Solution.lean's computed proof/spec_view — 6ea43277… is in fact the PREPATCH spec_view hash. Harmless for this gate — region_hashes is written by G-HYGIENE as gate data, not consumed as a leak baseline, and the two files' spec views differ only by one blank line before `-- proof-start`, which spec_signature strips, which is why same_spec is still True — but flagging it as a bookkeeping inconsistency for whoever owns the hygiene record.)

(2) Mechanical screen: leakage.screen(Solution.lean, lean tables, gold patch, problem_statement, test_patch) → passed=True, hard_failures=[], warnings=[]. Same for Solution_prepatch.lean. Gold changed lines the screen checks against are the three real ones ('obj.combined_queries = tuple(query.clone() for query in self.combined_queries)', 'for query in self.combined_queries:', 'query.set_empty()'); none is reproduced.

(3) My own token sweep over the computed spec view (68 lines of prose + defs): zero occurrences of set_empty, combined_queries, NothingNode, clone, is_empty, django, query.py, sql, QuerySet, queryset, 'none()', tuple, copy, deep-cop, alias, mutat, the patched line number 1778, the F2P test names/fixtures (test_union_none, qs1/qs2/qs3, Number, num__), and the PS's example classes (Publication, Article, ModelMultipleChoiceField). G-LEAK narration vocabulary (bug/fix/patch/previously/incorrectly/wrong/broken/regression) is absent. The only near-hits are 'union' (line 8, as an illustrative example of combining — and 'combined queries' is literally the public PS title) and the field name `combined` (public PS vocabulary: 'QuerySet.none() on combined queries returns all results').

(4) Verifier evidence (scripts/lean_verify.sh, 600s cap): gold Solution.lean exits 0 and `#print axioms correct_makeEmpty` = [propext, Classical.choice, Quot.sound] — clean, no sorryAx, so the proof is real. Solution_prepatch.lean exits 1 (YieldsNothing undischargeable for the untouched combined children), so the spec genuinely discriminates.

(5) LOAD-BEARING TEST (the unavoidability test applied on my own initiative, since the interesting question is whether the tree-wide clause is spec or edit-disclosure). I built /tmp scratch weak2.lean: the same pure region, the verbatim PREPATCH impl (`| .mk _ combined => Id.run do return Query.mk true combined`), and the postcondition WEAKENED to drop the recursive clause (`result.selfEmpty = true ∧ toShape result = toShape q`). It VERIFIES (exit 0). So the recursive 'whole tree' clause in YieldsNothing is exactly the load-bearing discriminator — strip it and the buggy impl satisfies the spec. It is therefore required content of any faithful spec, not gratuitous mechanism narration.

(6) Prose-removability control: de-narrated gold (module docstring cut down to the bare data-structure description, mechanism-rationale sentences removed) still verifies (exit 0), confirming the narration is prose only and carries no proof weight — i.e. it is judged purely on informational content.

**JUDGEMENT.** The public problem_statement discloses the entire observable defect and hence the entire required postcondition: title 'QuerySet.none() on combined queries returns all results', plus the worked union() example where submitting an empty form adds ALL matching objects while the `|` (OR) version adds none. From that alone a solver derives the spec: forcing a combined query empty must yield NO rows, i.e. the emptiness guarantee must cover the combined parts and not just the top query. That is precisely `YieldsNothing result` (own marker true AND recursively every combined sub-query), plus the frame `toShape result = toShape q` (an ordinary directive-5 no-free-output clause, no edit content). Generalizing to arbitrary nesting depth is a normal spec-strengthening choice, not gold information.

Closest call, examined and rejected as a leak: docstring lines 16-21, 'marking only the top node is not enough: because a node's result is the combination of its sub-queries' results, a node that combines other queries still returns every row those sub-queries return.' This is a restatement of the PUBLIC symptom ('returns all results') in the model's own abstract vocabulary — top node / sub-queries / self-empty marker — and is fully derivable from problem_statement without hints_text. hints_text ('QuerySet.none() doesn't work properly on combined querysets, it returns all results instead of an empty queryset') was NOT used as a baseline and adds nothing the PS lacks. Critically, the prose reveals no gold MECHANISM: it never names the method, the attribute, the file, or the loop, and — decisive evidence against leakage — the spec view is entirely SILENT about gold hunk 1 (the `clone()` deep-copy of combined_queries), which refinement.md documents as automatic under Lean's no-aliasing model. A solver reading the spec view learns nothing about the aliasing half of the edit at all. The spec view under-determines the gold patch rather than reconstructing it.

Core gates the disposition would lean on all pass in meta.json (G-VERIFY, G-DIFF, G-MUT, G-EQ, G-CONF, G-GOLD, G-HYGIENE, G-INTEGRITY, G-LEAK, G-PBT, G-RESOLVE, G-AX), and I independently reproduced the two that matter here (same_spec identity and the G-LEAK screen) plus the discrimination and load-bearing legs by verifier. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
