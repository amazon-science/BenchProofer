# P2 adversarial audit — django__django-16819

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_w1_prepatch.lean`, `atk_w2_drop_nameeq.lean`, `atk_w3_boundary_neq.lean`, `atk_w4_else_cannot.lean`, `atk_w5_echo_payload.lean`, `atk_w6_swapped.lean`, `atk_w7_always_empty.lean`, `atk_w8_prefix_match.lean`, `atk_w9_case_insensitive.lean`, `atk_w10_aleg_wrong_selfname.lean`, `atk_w11_aleg_const_applabel.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_v1_reordered_guard.lean`, `atk_v2_eager_conjuncts.lean`, `atk_v3_nested_if.lean`, `atk_v4_fallback_called_first.lean`, `atk_v5_elidable_probe.lean`, `atk_v6_negated_guard.lean`, `atk_v7_eta_reconstructed_op.lean`, `atk_v8_partial_swapped_eq.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a pointwise EQUALITY pinning result to a unique value at every input (`result = if op.isRemoveIndex && selfName == op.name then .replace [] else baseReduce selfName op appLabel`), with the else-branch FRAMED to the A-reference rather than left free. Consequently every impl whose correct_* closes is extensionally identical to gold, and all 8 such impls have materialized faithful patches that RESOLVE under the official harness (resolved=true, completed=true, F2P test_add_remove_index success, P2P failure=[]). The A-leg attacks that could in principle break the model<->callee correspondence (v4 unconditional pre-call of the fallback, v7 reconstructed stand-in argument, v5 extra elidable observation, v8 maximally-partial guard reading operation.name before any type test) all resolve, because (a) Operation.reduce is pure and total over the modeled observation space, (b) AddIndex.elidable is the never-overridden constant False so the base's first branch is dead, and (c) every operation the optimizer feeds AddIndex.reduce in the graded suite carries a .name attribute, so the Lean-vs-Python evaluation-order/partiality gap is never exercised.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_v1_reordered_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,7 +88,7 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
+  if selfName == op.name && op.isRemoveIndex then
     return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
@@ -100,6 +100,5 @@
         (implementation_reduceAddIndex selfName op appLabel) := by
   intro selfName op appLabel
   unfold problem_spec_reduceAddIndex implementation_reduceAddIndex
-  by_cases h : op.isRemoveIndex && selfName == op.name <;>
-    simp only [h, Id.run, bind, if_true, pure]
+  simp only [Id.run, bind, pure, Bool.and_comm]
 -- proof-end
```

Attack 2 — `atk_v2_eager_conjuncts.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,7 +88,9 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
+  let sameName := selfName == op.name
+  let isRem := op.isRemoveIndex
+  if sameName && isRem then
     return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
@@ -100,6 +102,5 @@
         (implementation_reduceAddIndex selfName op appLabel) := by
   intro selfName op appLabel
   unfold problem_spec_reduceAddIndex implementation_reduceAddIndex
-  by_cases h : op.isRemoveIndex && selfName == op.name <;>
-    simp only [h, Id.run, bind, if_true, pure]
+  simp only [Id.run, bind, pure, Bool.and_comm]
 -- proof-end
```

Attack 3 — `atk_v3_nested_if.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,8 +88,9 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
-    return ReduceResult.replace []
+  if op.isRemoveIndex then
+    if selfName == op.name then
+      return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
 
@@ -100,6 +101,6 @@
         (implementation_reduceAddIndex selfName op appLabel) := by
   intro selfName op appLabel
   unfold problem_spec_reduceAddIndex implementation_reduceAddIndex
-  by_cases h : op.isRemoveIndex && selfName == op.name <;>
-    simp only [h, Id.run, bind, if_true, pure]
+  simp only [Id.run, bind, pure]
+  cases op.isRemoveIndex <;> simp
 -- proof-end
```

Attack 4 — `atk_v4_fallback_called_first.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,9 +88,10 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
+  let base := baseReduce selfName op appLabel
   if op.isRemoveIndex && selfName == op.name then
     return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+  return base
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_v5_elidable_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,8 +88,11 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
+  let elid := op.elidable
   if op.isRemoveIndex && selfName == op.name then
     return ReduceResult.replace []
+  if elid then
+    return baseReduce selfName op appLabel
   return baseReduce selfName op appLabel
 -- impl-end
 
@@ -100,6 +103,5 @@
         (implementation_reduceAddIndex selfName op appLabel) := by
   intro selfName op appLabel
   unfold problem_spec_reduceAddIndex implementation_reduceAddIndex
-  by_cases h : op.isRemoveIndex && selfName == op.name <;>
-    simp only [h, Id.run, bind, if_true, pure]
+  simp only [Id.run, bind, pure, ite_self]
 -- proof-end
```

Attack 6 — `atk_v6_negated_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,9 +88,9 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
-    return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+  if !(op.isRemoveIndex && selfName == op.name) then
+    return baseReduce selfName op appLabel
+  return ReduceResult.replace []
 -- impl-end
 
 -- proof-start
@@ -101,5 +101,6 @@
   intro selfName op appLabel
   unfold problem_spec_reduceAddIndex implementation_reduceAddIndex
   by_cases h : op.isRemoveIndex && selfName == op.name <;>
-    simp only [h, Id.run, bind, if_true, pure]
+    simp only [h, Id.run, bind, pure, Bool.not_true, Bool.not_false,
+      Bool.false_eq_true, if_false, if_true, reduceIte]
 -- proof-end
```

Attack 7 — `atk_v7_eta_reconstructed_op.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -90,7 +90,9 @@
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
   if op.isRemoveIndex && selfName == op.name then
     return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+  return baseReduce selfName
+    { isRemoveIndex := op.isRemoveIndex, name := op.name, elidable := op.elidable }
+    appLabel
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_v8_partial_swapped_eq.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,7 +88,7 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
+  if op.name == selfName && op.isRemoveIndex then
     return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
@@ -100,6 +100,8 @@
         (implementation_reduceAddIndex selfName op appLabel) := by
   intro selfName op appLabel
   unfold problem_spec_reduceAddIndex implementation_reduceAddIndex
-  by_cases h : op.isRemoveIndex && selfName == op.name <;>
-    simp only [h, Id.run, bind, if_true, pure]
+  have hc : (op.name == selfName) = (selfName == op.name) := by
+    by_cases hx : selfName = op.name <;> simp [hx, Ne.symm, beq_iff_eq]
+  simp only [Id.run, bind, pure, hc,
+    Bool.and_comm (selfName == op.name) op.isRemoveIndex]
 -- proof-end
```

Attack 9 — `atk_w1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,8 +88,6 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
-    return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
 
```

Attack 10 — `atk_w2_drop_nameeq.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,7 +88,7 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
+  if op.isRemoveIndex then
     return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
```

Attack 11 — `atk_w3_boundary_neq.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,7 +88,7 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
+  if op.isRemoveIndex && selfName != op.name then
     return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
```

Attack 12 — `atk_w4_else_cannot.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -90,7 +90,7 @@
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
   if op.isRemoveIndex && selfName == op.name then
     return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+  return ReduceResult.cannot
 -- impl-end
 
 -- proof-start
```

Attack 13 — `atk_w5_echo_payload.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -89,7 +89,7 @@
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
   if op.isRemoveIndex && selfName == op.name then
-    return ReduceResult.replace []
+    return ReduceResult.replace [op]
   return baseReduce selfName op appLabel
 -- impl-end
 
```

Attack 14 — `atk_w6_swapped.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -89,8 +89,8 @@
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
   if op.isRemoveIndex && selfName == op.name then
-    return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+    return baseReduce selfName op appLabel
+  return ReduceResult.replace []
 -- impl-end
 
 -- proof-start
```

Attack 15 — `atk_w7_always_empty.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,9 +88,7 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
-    return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+  return ReduceResult.replace []
 -- impl-end
 
 -- proof-start
```

Attack 16 — `atk_w8_prefix_match.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,7 +88,7 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
+  if op.isRemoveIndex && op.name.startsWith selfName then
     return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
```

Attack 17 — `atk_w9_case_insensitive.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -88,7 +88,7 @@
 -- impl-start
 def implementation_reduceAddIndex
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
-  if op.isRemoveIndex && selfName == op.name then
+  if op.isRemoveIndex && selfName.toLower == op.name.toLower then
     return ReduceResult.replace []
   return baseReduce selfName op appLabel
 -- impl-end
```

Attack 18 — `atk_w10_aleg_wrong_selfname.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -90,7 +90,7 @@
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
   if op.isRemoveIndex && selfName == op.name then
     return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+  return baseReduce op.name op appLabel
 -- impl-end
 
 -- proof-start
```

Attack 19 — `atk_w11_aleg_const_applabel.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -90,7 +90,7 @@
     (selfName : String) (op : OpArg) (appLabel : String) : ReduceResult := Id.run do
   if op.isRemoveIndex && selfName == op.name then
     return ReduceResult.replace []
-  return baseReduce selfName op appLabel
+  return baseReduce selfName op ""
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-16819/lean. Repo root =swe-proof; venv python python. base_commit worktree (git clone --shared of the upstream repository @ 0b0998dc151feb77068e2387c34cc50ef6b356ae).

**SAME-SPEC:** all 19 attack files + pos_control built by gen.py, which copies Solution.lean and replaces ONLY the impl+proof regions. `swebench_unified.markers.same_spec(Solution.lean, atk, LeanBackend.language)` = True for every file (imports/axioms/pure/post-conditions byte-identical).

VERIFY CMD (run 4-wide as background jobs): `bash scripts/lean_verify.sh <f>.lean`.
AXIOMS CMD: copied each verifying file to ax_<f>.lean with `#print axioms correct_reduceAddIndex` appended, re-ran lean_verify.sh.
RESOLVE CMD: `python resolve_one.py <name>` -> `swebench_unified.harness.run_resolve('django__django-16819', <diff>, timeout=1800)`; JSON <name>.json, logs rs_<name>.log.
DIFF APPLICABILITY: `git apply --check -v <name>.diff` -> exit 0 for all 8 (mkpatches.py prints each).
LOCAL PRE-CHECK: pc.sh copies wt (test_patch pre-applied) + attack diff, runs migrations.test_optimizer via runner.py (which strips the venv's editable django-3.2 meta-path finder that otherwise shadows the checkout with a stray  tree). All 8: 39/39 OK.

=== A) VERIFYING ATTACKS (proof closes, clean axioms) -> faithful patch MATERIALIZED AND RESOLVED (8/8) ===
Each: lean_verify exit 0; `#print axioms correct_reduceAddIndex` shows NO sorryAx; run_resolve resolved=True completed=True, F2P test_add_remove_index in success[], P2P failure=[].
1. atk_v1_reordered_guard.lean (guard conjuncts COMMUTED) -> exit 0, axioms=[propext]; diff atk_v1_reordered_guard.diff (`if self.index.name == operation.name and isinstance(operation, RemoveIndex)`) -> RESOLVED. Lean && is commutative, Python `and` short-circuits, so this reads operation.name before the type test - the transliteration gap, unexercised by the suite.
2. atk_v2_eager_conjuncts.lean (both conjuncts into locals first) -> exit 0, [propext]; diff -> RESOLVED.
3. atk_v3_nested_if.lean (nested-if, isinstance outer) -> exit 0, [propext]; diff -> RESOLVED.
4. atk_v4_fallback_called_first.lean (A-LEG: `let base := baseReduce ...` invoked UNCONDITIONALLY before the guard, discarded on the annihilation path where gold never calls it) -> exit 0, [propext]; diff (`base = super().reduce(operation, app_label)` first) -> RESOLVED. Harmless because Operation.reduce is pure/total.
5. atk_v5_elidable_probe.lean (extra eager read of op.elidable + a both-arms-equal branch on it) -> exit 0, [propext]; diff -> RESOLVED.
6. atk_v6_negated_guard.lean (INVERTED control flow: `if !(guard) then fallback; return replace []`) -> exit 0, [propext]; diff -> RESOLVED.
7. atk_v7_eta_reconstructed_op.lean (A-LEG argument IDENTITY: fallback invoked on a RECONSTRUCTED OpArg carrying exactly the three modeled observables - defeq to `op` by structure eta) -> exit 0, [propext]; diff builds a `_ObservedOp` stand-in with .elidable/.name and passes THAT to super().reduce -> RESOLVED. This is the sharpest A-reference probe: the spec pins only the callee's observable projection, not the object identity, and the real Operation.reduce genuinely touches only `.elidable`, so the model is faithful rather than merely lucky.
8. atk_v8_partial_swapped_eq.lean (maximally PARTIAL guard: `op.name == selfName && op.isRemoveIndex`, equality operands swapped too) -> exit 0, axioms=[propext, Classical.choice, Quot.sound] (Mathlib String lemmas; NO sorryAx, so still a genuine clean-axiom proof); diff (`if operation.name == self.index.name and isinstance(operation, RemoveIndex)`) -> RESOLVED.

#### B) GENUINELY WRONG IMPLS -> proof does NOT close (11/11 rejected)
9. atk_w1_prepatch.lean = THE PREPATCH BUG re-encoded (no override; always `baseReduce`) -> exit 1. Residual pos goal `baseReduce selfName op appLabel = ReduceResult.replace []` (opaque, unprovable) - exactly the G-DIFF signal on the annihilation branch the F2P test exercises. PREPATCH REPRODUCED.
10. atk_w2_drop_nameeq.lean PARTIAL-DOMAIN (annihilate any remove-index) -> exit 1.
11. atk_w3_boundary_neq.lean BOUNDARY (selfName != op.name) -> exit 1.
12. atk_w4_else_cannot.lean CONTROL-FLOW-EFFECT (else abandons the A-reference for .cannot) -> exit 1: the else-branch is pinned to baseReduce, so the frame is not free.
13. atk_w5_echo_payload.lean UNGROUNDED-ORACLE ECHO (`replace [op]` not `replace []`) -> exit 1.
14. atk_w6_swapped.lean branches swapped -> exit 1.
15. atk_w7_always_empty.lean over-annihilation -> exit 1.
16. atk_w8_prefix_match.lean PARTIAL-DOMAIN widening (op.name.startsWith selfName) -> exit 1.
17. atk_w9_case_insensitive.lean DRIFT (toLower comparison) -> exit 1.
18. atk_w10_aleg_wrong_selfname.lean A-LEG argument SUBSTITUTION (`baseReduce op.name op appLabel`) -> exit 1.
19. atk_w11_aleg_const_applabel.lean A-LEG argument DROPPING (`baseReduce selfName op ""`) -> exit 1.
w10/w11 confirm the A-reference's argument threading is live in the spec, not decorative: substituting or constant-folding either argument to the opaque callee is rejected.
POSITIVE CONTROL pos_control.lean (gold impl region) -> exit 0, axioms=[propext]. Non-vacuity holds.

#### C) refinement.md AUDIT: every leg R / A-consumed / A-reference / I; NO kind-3
Leg 1 (`if op.isRemoveIndex && selfName == op.name`) = R. Leg 2 (`return ReduceResult.replace []`) = R. Type-bijection row (`.cannot`/`.replace _` <-> `False`/`list[Operation]`) = R. Leg 3 (`return baseReduce selfName op appLabel`) = A-REFERENCE, NOT A-consumed and NOT kind-3: the spec FRAMES the else-branch to baseReduce's value (so nothing is left unconstrained - w4 proves the frame bites), while the proof consumes no property of it (closes by case split + simp; #print axioms shows only [propext], no baseReduce_prop). Consistent with meta.json axioms=[] / deep_model_references=[baseReduce] / opaque_callees=[baseReduce]. There is no free/ungrounded leg anywhere in the impl region.
A-LEG CORRESPONDENCE VERIFIED MECHANICALLY against the real callees (introspection in the clean base_commit tree):
  - PREPATCH `'reduce' in AddIndex.__dict__` = False; `'reduce' in IndexOperation.__dict__` = False; `AddIndex.reduce is Operation.reduce` = **True**. So super() in the patched method provably resolves through IndexOperation to Operation.reduce (base.py:128-138), exactly as mapping.md and refinement.md claim. Post-patch the same introspection shows AddIndex.reduce is no longer Operation.reduce (the override landed) with MRO AddIndex->IndexOperation->Operation->object.
  - `Operation.elidable` = False and NEITHER AddIndex nor IndexOperation overrides `elidable`; an AddIndex instance reports elidable=False. Hence the base's `if self.elidable: return [operation]` arm is DEAD for AddIndex, so the base result depends only on `operation.elidable` - which OpArg carries. baseReduce not receiving self's elidable is therefore sound, and OpArg's three fields are exactly the touched observables (isinstance(_, RemoveIndex), .name, .elidable). No 4th observable exists.
  - Enumerated the full modeled observation space (isRemoveIndex x name in {idx,other} x elidable = 8 points) through the REAL `Operation.reduce`: outcome is `list` iff operation.elidable else `False` - total, pure, in the list/False codomain the mapping.md bijection assumes. Matches the recorded G-AX (50048 checks).
  - RemoveIndex has no subclass in django/db/migrations (only contrib.postgres RemoveIndexConcurrently, which IS a RemoveIndex, so isinstance stays correct); RemoveIndex.`__init__` stores self.name, so op.name <-> operation.name binds.
mapping.md file:line bindings (models.py:811-819 AddIndex.`__init__`, :860-862 migration_name_fragment insertion point, base.py:128-138 Operation.reduce) all check out against the worktree.

#### Verdict: SOUND
19 same-spec attacks run (>=5 required), spanning partial-domain (w2, w8), boundary (w3, w9), control-flow-effect (w4, w6, v4, v6), ungrounded-oracle echo (w5, w7), A-leg argument threading (w10, w11), A-leg callee-argument identity (v7), extra-observation (v5), and transliteration/evaluation-order gap (v1, v2, v3, v8), plus the prepatch bug (w1). Every impl whose correct_* closed with clean axioms (8 of them) had its faithful patch MATERIALIZED, checked with `git apply --check` at base_commit, and EXECUTED through the official harness run_resolve - all 8 RESOLVED. No impl exists with a closing clean-axiom proof and a non-resolving faithful patch, so no verify=/=>correct break. Not INCONCLUSIVE: every attack and every needed resolve run completed with recorded exit codes/axioms/resolve JSON.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 19 admissible attacks re-run of 19 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 19 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_w1_prepatch.lean`, `atk_w2_drop_nameeq.lean`, `atk_w3_boundary_neq.lean`, `atk_w4_else_cannot.lean`, `atk_w5_echo_payload.lean`, `atk_w6_swapped.lean`, `atk_w7_always_empty.lean`, `atk_w8_prefix_match.lean`, `atk_w9_case_insensitive.lean`, `atk_w10_aleg_wrong_selfname.lean`, `atk_w11_aleg_const_applabel.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_v1_reordered_guard.lean`, `atk_v2_eager_conjuncts.lean`, `atk_v3_nested_if.lean`, `atk_v4_fallback_called_first.lean`, `atk_v5_elidable_probe.lean`, `atk_v6_negated_guard.lean`, `atk_v7_eta_reconstructed_op.lean`, `atk_v8_partial_swapped_eq.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is a pointwise EQUALITY pinning result to a unique value at every input (`result = if op.isRemoveIndex && selfName == op.name then .replace [] else baseReduce selfName op appLabel`), with the else-branch FRAMED to the A-reference rather than left free. Consequently every impl whose correct_* closes is extensionally identical to gold, and all 8 such impls have materialized faithful patches that RESOLVE under the official harness (resolved=true, completed=true, F2P test_add_remove_index success, P2P failure=[]). The A-leg attacks that could in principle break the model<->callee correspondence (v4 unconditional pre-call of the fallback, v7 reconstructed stand-in argument, v5 extra elidable observation, v8 maximally-partial guard reading operation.name before any type test) all resolve, because (a) Operation.reduce is pure and total over the modeled observation space, (b) AddIndex.elidable is the never-overridden constant False so the base's first branch is dead, and (c) every operation the optimizer feeds AddIndex.reduce in the graded suite carries a .name attribute, so the Lean-vs-Python evaluation-order/partiality gap is never exercised.
```

**Attacks re-run (19):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 19 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_v1_reordered_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_v2_eager_conjuncts.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_v3_nested_if.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_v4_fallback_called_first.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_v5_elidable_probe.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_v6_negated_guard.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 7 — `atk_v7_eta_reconstructed_op.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 8 — `atk_v8_partial_swapped_eq.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_w1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_w2_drop_nameeq.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_w3_boundary_neq.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_w4_else_cannot.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_w5_echo_payload.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_w6_swapped.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_w7_always_empty.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_w8_prefix_match.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_w9_case_insensitive.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_w10_aleg_wrong_selfname.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_w11_aleg_const_applabel.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit, django__django-16819/lean. Repo root =swe-proof; venv python python. base_commit worktree (git clone --shared of the upstream repository @ 0b0998dc151feb77068e2387c34cc50ef6b356ae).

**SAME-SPEC:** all 19 attack files + pos_control built by gen.py, which copies Solution.lean and replaces ONLY the impl+proof regions. `swebench_unified.markers.same_spec(Solution.lean, atk, LeanBackend.language)` = True for every file (imports/axioms/pure/post-conditions byte-identical).

VERIFY CMD (run 4-wide as background jobs): `bash scripts/lean_verify.sh <f>.lean`.
AXIOMS CMD: copied each verifying file to ax_<f>.lean with `#print axioms correct_reduceAddIndex` appended, re-ran lean_verify.sh.
RESOLVE CMD: `python resolve_one.py <name>` -> `swebench_unified.harness.run_resolve('django__django-16819', <diff>, timeout=1800)`; JSON <name>.json, logs rs_<name>.log.
DIFF APPLICABILITY: `git apply --check -v <name>.diff` -> exit 0 for all 8 (mkpatches.py prints each).
LOCAL PRE-CHECK: pc.sh copies wt (test_patch pre-applied) + attack diff, runs migrations.test_optimizer via runner.py (which strips the venv's editable django-3.2 meta-path finder that otherwise shadows the checkout with a stray  tree). All 8: 39/39 OK.

=== A) VERIFYING ATTACKS (proof closes, clean axioms) -> faithful patch MATERIALIZED AND RESOLVED (8/8) ===
Each: lean_verify exit 0; `#print axioms correct_reduceAddIndex` shows NO sorryAx; run_resolve resolved=True completed=True, F2P test_add_remove_index in success[], P2P failure=[].
1. atk_v1_reordered_guard.lean (guard conjuncts COMMUTED) -> exit 0, axioms=[propext]; diff atk_v1_reordered_guard.diff (`if self.index.name == operation.name and isinstance(operation, RemoveIndex)`) -> RESOLVED. Lean && is commutative, Python `and` short-circuits, so this reads operation.name before the type test - the transliteration gap, unexercised by the suite.
2. atk_v2_eager_conjuncts.lean (both conjuncts into locals first) -> exit 0, [propext]; diff -> RESOLVED.
3. atk_v3_nested_if.lean (nested-if, isinstance outer) -> exit 0, [propext]; diff -> RESOLVED.
4. atk_v4_fallback_called_first.lean (A-LEG: `let base := baseReduce ...` invoked UNCONDITIONALLY before the guard, discarded on the annihilation path where gold never calls it) -> exit 0, [propext]; diff (`base = super().reduce(operation, app_label)` first) -> RESOLVED. Harmless because Operation.reduce is pure/total.
5. atk_v5_elidable_probe.lean (extra eager read of op.elidable + a both-arms-equal branch on it) -> exit 0, [propext]; diff -> RESOLVED.
6. atk_v6_negated_guard.lean (INVERTED control flow: `if !(guard) then fallback; return replace []`) -> exit 0, [propext]; diff -> RESOLVED.
7. atk_v7_eta_reconstructed_op.lean (A-LEG argument IDENTITY: fallback invoked on a RECONSTRUCTED OpArg carrying exactly the three modeled observables - defeq to `op` by structure eta) -> exit 0, [propext]; diff builds a `_ObservedOp` stand-in with .elidable/.name and passes THAT to super().reduce -> RESOLVED. This is the sharpest A-reference probe: the spec pins only the callee's observable projection, not the object identity, and the real Operation.reduce genuinely touches only `.elidable`, so the model is faithful rather than merely lucky.
8. atk_v8_partial_swapped_eq.lean (maximally PARTIAL guard: `op.name == selfName && op.isRemoveIndex`, equality operands swapped too) -> exit 0, axioms=[propext, Classical.choice, Quot.sound] (Mathlib String lemmas; NO sorryAx, so still a genuine clean-axiom proof); diff (`if operation.name == self.index.name and isinstance(operation, RemoveIndex)`) -> RESOLVED.

#### B) GENUINELY WRONG IMPLS -> proof does NOT close (11/11 rejected)
9. atk_w1_prepatch.lean = THE PREPATCH BUG re-encoded (no override; always `baseReduce`) -> exit 1. Residual pos goal `baseReduce selfName op appLabel = ReduceResult.replace []` (opaque, unprovable) - exactly the G-DIFF signal on the annihilation branch the F2P test exercises. PREPATCH REPRODUCED.
10. atk_w2_drop_nameeq.lean PARTIAL-DOMAIN (annihilate any remove-index) -> exit 1.
11. atk_w3_boundary_neq.lean BOUNDARY (selfName != op.name) -> exit 1.
12. atk_w4_else_cannot.lean CONTROL-FLOW-EFFECT (else abandons the A-reference for .cannot) -> exit 1: the else-branch is pinned to baseReduce, so the frame is not free.
13. atk_w5_echo_payload.lean UNGROUNDED-ORACLE ECHO (`replace [op]` not `replace []`) -> exit 1.
14. atk_w6_swapped.lean branches swapped -> exit 1.
15. atk_w7_always_empty.lean over-annihilation -> exit 1.
16. atk_w8_prefix_match.lean PARTIAL-DOMAIN widening (op.name.startsWith selfName) -> exit 1.
17. atk_w9_case_insensitive.lean DRIFT (toLower comparison) -> exit 1.
18. atk_w10_aleg_wrong_selfname.lean A-LEG argument SUBSTITUTION (`baseReduce op.name op appLabel`) -> exit 1.
19. atk_w11_aleg_const_applabel.lean A-LEG argument DROPPING (`baseReduce selfName op ""`) -> exit 1.
w10/w11 confirm the A-reference's argument threading is live in the spec, not decorative: substituting or constant-folding either argument to the opaque callee is rejected.
POSITIVE CONTROL pos_control.lean (gold impl region) -> exit 0, axioms=[propext]. Non-vacuity holds.

#### C) refinement.md AUDIT: every leg R / A-consumed / A-reference / I; NO kind-3
Leg 1 (`if op.isRemoveIndex && selfName == op.name`) = R. Leg 2 (`return ReduceResult.replace []`) = R. Type-bijection row (`.cannot`/`.replace _` <-> `False`/`list[Operation]`) = R. Leg 3 (`return baseReduce selfName op appLabel`) = A-REFERENCE, NOT A-consumed and NOT kind-3: the spec FRAMES the else-branch to baseReduce's value (so nothing is left unconstrained - w4 proves the frame bites), while the proof consumes no property of it (closes by case split + simp; #print axioms shows only [propext], no baseReduce_prop). Consistent with meta.json axioms=[] / deep_model_references=[baseReduce] / opaque_callees=[baseReduce]. There is no free/ungrounded leg anywhere in the impl region.
A-LEG CORRESPONDENCE VERIFIED MECHANICALLY against the real callees (introspection in the clean base_commit tree):
  - PREPATCH `'reduce' in AddIndex.__dict__` = False; `'reduce' in IndexOperation.__dict__` = False; `AddIndex.reduce is Operation.reduce` = **True**. So super() in the patched method provably resolves through IndexOperation to Operation.reduce (base.py:128-138), exactly as mapping.md and refinement.md claim. Post-patch the same introspection shows AddIndex.reduce is no longer Operation.reduce (the override landed) with MRO AddIndex->IndexOperation->Operation->object.
  - `Operation.elidable` = False and NEITHER AddIndex nor IndexOperation overrides `elidable`; an AddIndex instance reports elidable=False. Hence the base's `if self.elidable: return [operation]` arm is DEAD for AddIndex, so the base result depends only on `operation.elidable` - which OpArg carries. baseReduce not receiving self's elidable is therefore sound, and OpArg's three fields are exactly the touched observables (isinstance(_, RemoveIndex), .name, .elidable). No 4th observable exists.
  - Enumerated the full modeled observation space (isRemoveIndex x name in {idx,other} x elidable = 8 points) through the REAL `Operation.reduce`: outcome is `list` iff operation.elidable else `False` - total, pure, in the list/False codomain the mapping.md bijection assumes. Matches the recorded G-AX (50048 checks).
  - RemoveIndex has no subclass in django/db/migrations (only contrib.postgres RemoveIndexConcurrently, which IS a RemoveIndex, so isinstance stays correct); RemoveIndex.`__init__` stores self.name, so op.name <-> operation.name binds.
mapping.md file:line bindings (models.py:811-819 AddIndex.`__init__`, :860-862 migration_name_fragment insertion point, base.py:128-138 Operation.reduce) all check out against the worktree.

#### Verdict: SOUND
19 same-spec attacks run (>=5 required), spanning partial-domain (w2, w8), boundary (w3, w9), control-flow-effect (w4, w6, v4, v6), ungrounded-oracle echo (w5, w7), A-leg argument threading (w10, w11), A-leg callee-argument identity (v7), extra-observation (v5), and transliteration/evaluation-order gap (v1, v2, v3, v8), plus the prepatch bug (w1). Every impl whose correct_* closed with clean axioms (8 of them) had its faithful patch MATERIALIZED, checked with `git apply --check` at base_commit, and EXECUTED through the official harness run_resolve - all 8 RESOLVED. No impl exists with a closing clean-axiom proof and a non-resolving faithful patch, so no verify=/=>correct break. Not INCONCLUSIVE: every attack and every needed resolve run completed with recorded exit codes/axioms/resolve JSON.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**Modeled function:** AddIndex.reduce added by patch.diff at django/db/migrations/operations/models.py:864-867. Reference = worktree at base_commit 0b0998dc151feb77068e2387c34cc50ef6b356ae with patch.diff APPLIED (confirmed `git diff` == patch.diff exactly, plus the test_patch hunk). No divergence found; no defect to report.

### Artifact integrity
- scripts/lean_verify.sh on Solution.lean: exit 0 (elaborates, no sorry/error).
- `#print axioms correct_reduceAddIndex` => [propext] only. No sorryAx, no ad-hoc axiom. meta.json axioms=[] is consistent: the proof closes by case split, consuming NO property of `baseReduce` (a true A-reference, not a consumed axiom).
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True => spec region byte-identical; the prepatch carries the same spec text, so the discrimination signal is real and not a prose edit.
- Prepatch discriminates (not vacuous): Solution_prepatch.lean FAILS to elaborate with exactly the expected error at the annihilation branch: `(pure (baseReduce selfName op appLabel)).run is not definitionally equal to ReduceResult.replace []` (case isTrue, h : (op.isRemoveIndex && selfName == op.name) = true). That is the real bug leg — prepatch AddIndex has no reduce override and always defers to the inherited Operation.reduce.
- FAIL_TO_PASS test_add_remove_index passes on the patched worktree (runtests.py: OK).

### Faithfulness method
Built an executable shadow of `problem_spec_reduceAddIndex` in Python and differential-tested it against the REAL patched AddIndex.reduce. Per the A-reference rule, the opaque `baseReduce` was instantiated with the REAL callee value (Operation.reduce, base.py:129-138, UNCHANGED by the patch — verified), so only the R guard leg is under test and the else-branch is pinned to real behavior rather than assumed. Results normalized through the mapping.md bijection: False -> .cannot, list[Operation] -> .replace (each element projected to the OpArg observation triple).

COVERAGE / RESULTS
1. Structured sweep, 357 cases: selfName in {idx_a, idx_b, IDX_A, 30-char, i_1, non-ASCII 'idx_ä'} x others in {matching RemoveIndex (same and different model_name), non-matching RemoveIndex over all name pairs, RenameIndex with new_name==selfName, AddIndex with same name, DeleteModel, CreateModel, RemoveConstraint (has a .name attribute but is NOT a RemoveIndex — the key discriminator for the isinstance leg), RunPython/RunSQL elidable True and False} x app_label in {'app','','other_app'}. 0 mismatches.
2. Randomized fuzz, 200,000 cases, seed 16819 (the pinned conformance seed), names drawn from an alphabet including uppercase, underscore, digits and non-ASCII to stress the string-equality leg. 0 mismatches.
3. Targeted abstraction-boundary probes, all matching:
   - selfName == '' (constructed via `__new__` to bypass AddIndex.`__init__`'s name validation) against RemoveIndex(''): real [] == model .replace [].
   - RemoveIndex with name=None: real False == model's base-branch value (String vs None is a non-match on both sides).
   - Case sensitivity ('idx' vs 'IDX'), trailing whitespace ('x ' vs 'x'), and identical non-ASCII names: real and model agree; the guard is exact str equality, matching Lean's String ==, with no .lower() normalization on either side.
   - Guard precedence: with self.elidable forced True and a MATCHING RemoveIndex, the real code still returns [] (the added guard runs BEFORE super()), exactly as the model's if/else orders it. This is the one place a mis-modeled precedence would show and it agrees.
   - Elidable other operation: real returns [self]; equals the model's else-branch (= real Operation.reduce) under the projection.
   - `&&` vs `and` short-circuit: benign. When isRemoveIndex is False the Python `and` never reads .name (avoiding AttributeError on operations lacking it) while Lean's total `selfName == op.name` is simply discarded by the False conjunct — same Bool either way.
   - RemoveIndexConcurrently (postgres subclass of RemoveIndex): isinstance is True so both real and model annihilate on a name match; consistent by construction (psycopg2 absent, so asserted from the isinstance-based control flow rather than executed).

### SPEC-STRENGTH ANALYSIS (is it TOO STRONG?)
No. The spec is a total equality that pins the result on BOTH legs, yet nothing it pins exceeds real behavior:
- The guard leg is pinned to .replace [] — matches the patch's `return []`.
- The else leg is pinned to `baseReduce selfName op appLabel`, an opaque constant, so it asserts only 'the fallback IS whatever the generic reducer yields for the same two operations'. It does not pin a VALUE, so it cannot be too strong there; correct frame discipline (the fallback is framed, not left free, so the spec is also not too weak).
- OpArg carries exactly the three observables the reduction touches (isinstance-RemoveIndex, .name, .elidable). Notably it deliberately omits model_name — and that is the faithful choice, not an omission: the real patched code also ignores model_name, so AddIndex('Pony','idx') vs RemoveIndex('Zebra','idx') annihilates in the REAL repo (verified: returns []) and the model annihilates too. A model that added a model_name equality would have been UNFAITHFUL (too strong); this one tracks the repo, including that arguably-questionable upstream behavior.
- appLabel is threaded but unused by the guard, mirroring the patch, which only forwards it to super().

**CONCLUSION:** no input on which the modeled function disagrees with the real patched callee was found across ~200k differential cases plus hand-built boundary probes. Spec is faithful and appropriately scoped.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**NO RELAXATION IN THIS BUNDLE:** there is no RELAXED_LEAKAGE.md and meta.json has no `relaxed_leakage` key (checked: `{k:v for k,v in meta.items() if 'relax' in k.lower()}` == {}). So this is a straight leakage judgement, not a relaxation review; the facet-unavoidability branch of my instructions does not apply. Nothing in the bundle addressed me or told me what to record: leakage.reviewer_directed() over every .md/.lean in the bundle returned no hits, and a manual grep for auditor/reviewer/panel/'honest recording'/'you must submit' hit only verdict.md's own role-ledger headings (prior G-PANEL rows), which are gate-owned records, not instructions.

### WHAT I RAN (my own measurements, not the recorded gate rows):
1. Spec-region identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True; spec_view of the two is byte-identical; spec_signature sha256 prefix 3d050a98748a2647. So the spec view I judged is the frozen one and the prepatch differs only in the elided impl/proof regions.
2. Mechanical screen (lean flavor) on BOTH Solution.lean and Solution_prepatch.lean against the frozen instance.json patch + problem_statement: leakage.screen() hard_failures=[] , warnings=[] in both cases. No diff markers, no gold line reproduced at the len>=8 normalized threshold, no patched file/module path.
3. Proof soundness (so the verdict does not rest on a fake proof): scripts/lean_verify.sh Solution.lean exit 0; appended `#print axioms correct_reduceAddIndex` -> 'depends on axioms: [propext]'. No sorryAx. meta axioms=[] , deep_model_references=['baseReduce'] (opaque A-reference, not a consumed axiom).
4. Load-bearing check (the strip-the-clause test, run as G-DIFF): scripts/lean_verify.sh Solution_prepatch.lean FAILS, and fails at exactly the annihilation branch -- line 110, case isTrue with h : (op.isRemoveIndex && selfName == op.name) = true, goal `(pure (baseReduce selfName op appLabel)).run = ReduceResult.replace []`, rfl cannot close it. So the same-name -> empty-list clause is genuinely load-bearing against the PRE-patch impl; the spec is not vacuous and the clause is not decoration.
5. Consumer surface: src/swebench_unified/eval/dataset.py as_dict/build shows only spec_view (plus problem_statement, and localization in modes that grant it) reaches the solver. refinement.md and mapping.md DO quote the gold patch verbatim (`if isinstance(operation, RemoveIndex) and self.index.name == operation.name: return []`), but they are audit-side artifacts and are never serialized into the agent view, so they are not a leak channel. I judged the projected spec_view only.

SYMBOL-LEVEL RE-SCAN AGAINST problem_statement (public text is only: 'Reduce Add/RemoveIndex migration operations. Description. We should reduce AddIndex/RemoveIndex operations when optimizing migration operations.'; hints_text is '' so no risk of screening against it):
- Patch-changed distinctive symbols are {reduce, describe}. `reduce` and the class names AddIndex/RemoveIndex appear literally in the problem_statement, so describing the behavior in those words is public by construction -- the screen's skip here is a correct skip, not a loophole. `describe` (picked up from the hunk section header) does NOT appear in the spec view.
- Absent from the spec view entirely: isinstance, super, self.index.name, app_label as a Python name, models.py, base.py, migration_name_fragment, optimizer, and any test name. The F2P test is test_add_remove_index (migrations.test_optimizer) and neither the test name nor its module is echoed. Lean identifiers are OpArg/ReduceResult/baseReduce/reduceAddIndex -- no patched repo symbol echoed beyond the public words.
- `elidable` appears twice in the view and is NOT in the problem_statement. I judged it non-leaking on the merits, not by the screen's silence: it is not a patch-changed symbol, it is an attribute of the UNCHANGED generic Operation.reduce (base.py:136) that already existed at base_commit 0b0998dc151feb77068e2387c34cc50ef6b356ae. Naming it localizes pre-existing Django code, not the edit, and it is required by frame discipline to pin the else-branch rather than leave it free.
- No narration: leakage.`_NARRATION` vocabulary (bug/fix/patched/previously/incorrectly/...) has zero occurrences in the view. The view states desired behavior ('the desired behavior is'), never 'a method was added' and never a file/line.
- Closest call I weighed: the docstring line 'the fallback is the unchanged shared behavior'. 'unchanged' implies the delta lives in the other branch, i.e. that the AddIndex/RemoveIndex cancellation is the new thing. But the problem_statement already says exactly that ('we should reduce AddIndex/RemoveIndex operations when optimizing'), so it adds nothing beyond public, and pinning the else-branch to the shared reducer is a faithfulness requirement (else the spec would be underdetermined). Not a leak.

**DERIVABILITY:** every behavioral commitment in the view -- (a) an add-index and a following remove-index reduce against each other, (b) matched on index name, (c) the pair annihilates to no operations, (d) otherwise the pre-existing shared reducer decides -- follows from the public 'reduce AddIndex/RemoveIndex operations when optimizing migration operations' plus the base_commit source a solver can read. (b) and (c) are the only content a skeptic could call added, and both are the ordinary meaning of 'reduce' for an add/remove pair of the same index; neither names the edit's location or shape.

CAVEAT recorded for honesty: benchmark-verified/.../axiom_check.py could not execute in my shell (ModuleNotFoundError: django -- no repo venv on PATH from this cwd), so I did not independently re-run G-AX; the recorded G-AX row is pass (checked=50048). My verdict does not depend on it -- G-AX concerns whether baseReduce models the real Operation.reduce (a faithfulness question owned by G-PANEL-2), not whether the spec view discloses the edit. The four measurements the leakage verdict does rest on (same_spec, screen, verify+axioms, prepatch-fails) I ran myself and all passed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
