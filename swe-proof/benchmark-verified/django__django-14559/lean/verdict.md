# P2 adversarial audit — django__django-14559

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,6 +54,7 @@
   result = some (batchedMatchCount batchSize keys)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
   if keys.isEmpty then
@@ -61,14 +62,11 @@
   let batches := List.toChunks batchSize keys
   let mut rowsUpdated := 0
   for batch in batches do
-    rowsUpdated := rowsUpdated + batch.dedup.length
+    rowsUpdated := rowsUpdated + batch.length
   return some rowsUpdated
 -- impl-end
 
 -- proof-start
-/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
-closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
-accumulator. -/
 theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
     Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
       = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
@@ -84,8 +82,7 @@
   intro keys batchSize hb
   unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
   by_cases h : keys.isEmpty
-  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
-    have hk : keys = [] := List.isEmpty_iff.mp h
+  · have hk : keys = [] := List.isEmpty_iff.mp h
     have hc : List.toChunks batchSize ([] : List Int) = [] := by
       cases batchSize with
       | zero => omega
@@ -93,8 +90,7 @@
     subst hk
     simp only [Id.run, h, if_true, hc, List.foldl_nil]
     rfl
-  · -- non-empty input: bridge the desugared loop to the helper, then close
-    simp only [Id.run, h, if_false, Bool.false_eq_true]
+  · simp only [Id.run, h, if_false, Bool.false_eq_true]
     show some (Id.run (forIn (List.toChunks batchSize keys) 0
         (fun batch r => ForInStep.yield (r + batch.dedup.length))))
       = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,15 @@
   result = some (batchedMatchCount batchSize keys)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
   if keys.isEmpty then
     return some 0
-  let batches := List.toChunks batchSize keys
-  let mut rowsUpdated := 0
-  for batch in batches do
-    rowsUpdated := rowsUpdated + batch.dedup.length
-  return some rowsUpdated
+  return some keys.dedup.length
 -- impl-end
 
 -- proof-start
-/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
-closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
-accumulator. -/
 theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
     Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
       = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
@@ -84,8 +78,7 @@
   intro keys batchSize hb
   unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
   by_cases h : keys.isEmpty
-  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
-    have hk : keys = [] := List.isEmpty_iff.mp h
+  · have hk : keys = [] := List.isEmpty_iff.mp h
     have hc : List.toChunks batchSize ([] : List Int) = [] := by
       cases batchSize with
       | zero => omega
@@ -93,8 +86,7 @@
     subst hk
     simp only [Id.run, h, if_true, hc, List.foldl_nil]
     rfl
-  · -- non-empty input: bridge the desugared loop to the helper, then close
-    simp only [Id.run, h, if_false, Bool.false_eq_true]
+  · simp only [Id.run, h, if_false, Bool.false_eq_true]
     show some (Id.run (forIn (List.toChunks batchSize keys) 0
         (fun batch r => ForInStep.yield (r + batch.dedup.length))))
       = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,13 @@
   result = some (batchedMatchCount batchSize keys)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
-  if keys.isEmpty then
-    return some 0
-  let batches := List.toChunks batchSize keys
-  let mut rowsUpdated := 0
-  for batch in batches do
-    rowsUpdated := rowsUpdated + batch.dedup.length
-  return some rowsUpdated
+  return some 0
 -- impl-end
 
 -- proof-start
-/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
-closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
-accumulator. -/
 theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
     Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
       = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
@@ -84,8 +76,7 @@
   intro keys batchSize hb
   unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
   by_cases h : keys.isEmpty
-  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
-    have hk : keys = [] := List.isEmpty_iff.mp h
+  · have hk : keys = [] := List.isEmpty_iff.mp h
     have hc : List.toChunks batchSize ([] : List Int) = [] := by
       cases batchSize with
       | zero => omega
@@ -93,8 +84,7 @@
     subst hk
     simp only [Id.run, h, if_true, hc, List.foldl_nil]
     rfl
-  · -- non-empty input: bridge the desugared loop to the helper, then close
-    simp only [Id.run, h, if_false, Bool.false_eq_true]
+  · simp only [Id.run, h, if_false, Bool.false_eq_true]
     show some (Id.run (forIn (List.toChunks batchSize keys) 0
         (fun batch r => ForInStep.yield (r + batch.dedup.length))))
       = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,10 +54,11 @@
   result = some (batchedMatchCount batchSize keys)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
   if keys.isEmpty then
-    return some 0
+    return some 1
   let batches := List.toChunks batchSize keys
   let mut rowsUpdated := 0
   for batch in batches do
@@ -66,9 +67,6 @@
 -- impl-end
 
 -- proof-start
-/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
-closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
-accumulator. -/
 theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
     Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
       = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
@@ -84,8 +82,7 @@
   intro keys batchSize hb
   unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
   by_cases h : keys.isEmpty
-  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
-    have hk : keys = [] := List.isEmpty_iff.mp h
+  · have hk : keys = [] := List.isEmpty_iff.mp h
     have hc : List.toChunks batchSize ([] : List Int) = [] := by
       cases batchSize with
       | zero => omega
@@ -93,8 +90,7 @@
     subst hk
     simp only [Id.run, h, if_true, hc, List.foldl_nil]
     rfl
-  · -- non-empty input: bridge the desugared loop to the helper, then close
-    simp only [Id.run, h, if_false, Bool.false_eq_true]
+  · simp only [Id.run, h, if_false, Bool.false_eq_true]
     show some (Id.run (forIn (List.toChunks batchSize keys) 0
         (fun batch r => ForInStep.yield (r + batch.dedup.length))))
       = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,19 @@
   result = some (batchedMatchCount batchSize keys)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
   if keys.isEmpty then
     return some 0
   let batches := List.toChunks batchSize keys
   let mut rowsUpdated := 0
-  for batch in batches do
+  for batch in batches.tail do
     rowsUpdated := rowsUpdated + batch.dedup.length
   return some rowsUpdated
 -- impl-end
 
 -- proof-start
-/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
-closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
-accumulator. -/
 theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
     Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
       = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
@@ -84,8 +82,7 @@
   intro keys batchSize hb
   unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
   by_cases h : keys.isEmpty
-  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
-    have hk : keys = [] := List.isEmpty_iff.mp h
+  · have hk : keys = [] := List.isEmpty_iff.mp h
     have hc : List.toChunks batchSize ([] : List Int) = [] := by
       cases batchSize with
       | zero => omega
@@ -93,8 +90,7 @@
     subst hk
     simp only [Id.run, h, if_true, hc, List.foldl_nil]
     rfl
-  · -- non-empty input: bridge the desugared loop to the helper, then close
-    simp only [Id.run, h, if_false, Bool.false_eq_true]
+  · simp only [Id.run, h, if_false, Bool.false_eq_true]
     show some (Id.run (forIn (List.toChunks batchSize keys) 0
         (fun batch r => ForInStep.yield (r + batch.dedup.length))))
       = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,17 @@
   result = some (batchedMatchCount batchSize keys)
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
   if keys.isEmpty then
     return some 0
-  let batches := List.toChunks batchSize keys
-  let mut rowsUpdated := 0
-  for batch in batches do
-    rowsUpdated := rowsUpdated + batch.dedup.length
-  return some rowsUpdated
+  if keys.length ≤ batchSize then
+    return some keys.dedup.length
+  return some keys.length
 -- impl-end
 
 -- proof-start
-/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
-closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
-accumulator. -/
 theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
     Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
       = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
@@ -84,8 +80,7 @@
   intro keys batchSize hb
   unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
   by_cases h : keys.isEmpty
-  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
-    have hk : keys = [] := List.isEmpty_iff.mp h
+  · have hk : keys = [] := List.isEmpty_iff.mp h
     have hc : List.toChunks batchSize ([] : List Int) = [] := by
       cases batchSize with
       | zero => omega
@@ -93,8 +88,7 @@
     subst hk
     simp only [Id.run, h, if_true, hc, List.foldl_nil]
     rfl
-  · -- non-empty input: bridge the desugared loop to the helper, then close
-    simp only [Id.run, h, if_false, Bool.false_eq_true]
+  · simp only [Id.run, h, if_false, Bool.false_eq_true]
     show some (Id.run (forIn (List.toChunks batchSize keys) 0
         (fun batch r => ForInStep.yield (r + batch.dedup.length))))
       = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Applying a batched bulk modification to a collection of stored records and
reporting how many stored rows were matched by the modification.

The records to modify are supplied as a sequence; each carries the identifier
of the stored row it stands for. The operation processes the sequence in
fixed-size batches: every batch issues a single set-based modification keyed on
the identifiers occurring in that batch, and a set-based modification matches
each distinct identifier at most once (so an identifier that appears more than
once within the same batch is still matched a single time).

The desired behavior is that the operation reports the total number of rows
matched across all batches: the sum, over the batches, of the count of distinct
identifiers in each batch. Because the tally is per batch, an identifier that
recurs within one batch contributes once, while an identifier that recurs across
two different batches contributes once per batch it lands in. When the input
sequence is empty the operation performs no modification and reports a matched
count of zero. The reported total is always present (a count is returned in
every case).
-/

-- axioms-start
-- No unchanged callee is consumed as an opaque carrier here: the per-batch
-- matched-row tally and the batching are modeled directly as total operations
-- over the identifier sequence (see the `pure` region). No callee property is
-- consumed by the correctness proof.
-- axioms-end

-- pure-start
/-- The number of rows matched by one batch's set-based modification: a set-based
match keyed on a multiset of identifiers matches each *distinct* identifier once,
so the per-batch tally is the number of distinct identifiers in the batch. -/
def batchMatched (batch : List Int) : Nat := batch.dedup.length

/-- The total number of rows matched when the identifier sequence is processed in
fixed-size batches: split the sequence into consecutive batches of size
`batchSize`, then sum each batch's distinct-identifier count. Front-recursive
shape paired with the accumulator loop in the implementation. -/
def batchedMatchCount (batchSize : Nat) (keys : List Int) : Nat :=
  (List.toChunks batchSize keys).foldl (fun acc batch => acc + batchMatched batch) 0
-- pure-end

-- post-conditions-start
/-- The reported result is always a present count, and that count equals the
total number of rows matched across the fixed-size batches: the sum over batches
of the distinct-identifier count of each batch. This fully pins the result —
both its presence and its value are determined by the identifier sequence and
the batch size. -/
def problem_spec_bulkUpdate
    (keys : List Int) (batchSize : Nat) (result : Option Nat) : Prop :=
  result = some (batchedMatchCount batchSize keys)
-- post-conditions-end

-- impl-start
def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
  if keys.isEmpty then
    return some 0
  let batches := List.toChunks batchSize keys
  let mut rowsUpdated := 0
  for batch in batches do
    rowsUpdated := rowsUpdated + batch.dedup.length
  return some rowsUpdated
-- impl-end

-- proof-start
/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
accumulator. -/
theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
    Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
      = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
  induction batches generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih, List.foldl_cons]

theorem correct_bulkUpdate :
    ∀ (keys : List Int) (batchSize : Nat), 1 ≤ batchSize →
      problem_spec_bulkUpdate keys batchSize
        (implementation_bulkUpdate keys batchSize) := by
  intro keys batchSize hb
  unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
  by_cases h : keys.isEmpty
  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
    have hk : keys = [] := List.isEmpty_iff.mp h
    have hc : List.toChunks batchSize ([] : List Int) = [] := by
      cases batchSize with
      | zero => omega
      | succ m => rfl
    subst hk
    simp only [Id.run, h, if_true, hc, List.foldl_nil]
    rfl
  · -- non-empty input: bridge the desugared loop to the helper, then close
    simp only [Id.run, h, if_false, Bool.false_eq_true]
    show some (Id.run (forIn (List.toChunks batchSize keys) 0
        (fun batch r => ForInStep.yield (r + batch.dedup.length))))
      = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
    rw [forIn_sum_bulkUpdate]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Same-spec check True for all 6 attacks + positive control + prepatch (swebench_unified.markers.same_spec, lean backend). Only impl region edited; axioms/pure/pre/post byte-identical.

CORE ANALYSIS: The postcondition `problem_spec_bulkUpdate keys batchSize result := result = some (batchedMatchCount batchSize keys)` is a TIGHT TOTAL FUNCTIONAL EQUALITY over the entire precondition domain (1 ≤ batchSize). Any impl that closes correct_bulkUpdate must be extensionally equal to gold on all keys and all batchSize ≥ 1. The only genuine looseness is batchSize=0 (excluded by the precondition binder), which never occurs in the real Python flow (batch_size/bulk_batch_size is always ≥1) — a SOUND looseness, not a break, so I did not count it.

### ATTACKS (6 distinct wrong impls; all lean_verify.sh exit=1 = do NOT close; ran concurrently ≤4 at a time):
- atk_1 (control-flow-effect / undercount-model echo): per-batch tally uses batch.length (rows-sent, no dedup). Counterexample keys=[7,7],bs=5: gold 1 vs 2. exit=1.
- atk_2 (ungrounded-oracle echo / global-distinct model): returns some keys.dedup.length (global dedup, ignores batching). keys=[7,7],bs=1: gold 2 vs 1. exit=1. This is exactly the F2P discriminator (test_updated_rows_when_passing_duplicates).
- atk_3 (constant/degenerate): returns some 0 always. keys=[1],bs=1: gold 1 vs 0. exit=1.
- atk_4 (boundary): empty branch returns some 1 instead of some 0; goal reduces literally to `pure (some 1) = some 0`. exit=1.
- atk_5 (control-flow-effect): loops over batches.tail (drops first batch). keys=[1],bs=1: gold 1 vs 0. exit=1.
- atk_7 (partial-domain): correct when keys.length ≤ batchSize (single batch) but returns keys.length (rows-sent) otherwise. keys=[1,1,2],bs=2 → two batches [[1,1],[2]]: gold 2 vs 3. exit=1.

Because NO wrong impl produced a closing clean-axiom proof, step-2 (materialize + run refined patch through resolve for every closing impl) is vacuously satisfied — there are zero verifying-but-wrong impls to falsify with the harness. No resolve run was needed or possible.

POSITIVE CONTROL: pos_control.lean = gold Solution.lean copy, lean_verify.sh exit=0 (clean, no sorry). `#print axioms correct_bulkUpdate` → depends on axioms: [propext, Quot.sound] (clean; no sorryAx, no native_decide/Lean.ofReduceBool, no custom axioms). Command: `bash scripts/lean_verify.sh <file>` from project root.

PREPATCH REPRODUCED: prepatch.lean (impl returns none in both branches = the real pre-patch bug where bulk_update returned None instead of a count) fails the gold proof, exit=1 (goal `...pure none = some (...)`), confirming the spec DETECTS the real bug (G-DIFF direction holds).

REFINEMENT.MD AUDIT: all 5 legs are R or I (leg1 R empty-branch, leg2 R batching toChunks, leg3 I accumulator init, leg4 R deep-model of UNCHANGED update(pk__in=pks) matched count = batch.dedup.length, leg5 R return). No kind-3 (uncovered) legs. No A-consumed / A-reference legs: axiom_check.py is a legitimate skip stub (no consumed callee axiom, no opaque decl, deep_model_references=[]). The A-leg mandate is therefore vacuous. The single deep-model decision (leg4: batch.dedup.length ↔ SQL WHERE pk IN(...) distinct-pk matched count under the modeled domain where every key references an existing row) is a sound total-operation model, validated by G-CONF over ≥1e5 fuzzed inputs; the correspondence to the real update() callee holds (SQL IN dedups, all referenced rows exist per modeled domain). This is R (deep model of an unchanged callee treated as a total list op), not a hidden A-reference.

All exit codes captured from lean_verify.sh (0=verifies/no-sorry, 1=error). No timeouts (no 124). Verdict SOUND: ≥5 distinct same-spec attacks (6) run, none closes, so verify⇒correct is not falsified here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Applying a batched bulk modification to a collection of stored records and
reporting how many stored rows were matched by the modification.

The records to modify are supplied as a sequence; each carries the identifier
of the stored row it stands for. The operation processes the sequence in
fixed-size batches: every batch issues a single set-based modification keyed on
the identifiers occurring in that batch, and a set-based modification matches
each distinct identifier at most once (so an identifier that appears more than
once within the same batch is still matched a single time).

The desired behavior is that the operation reports the total number of rows
matched across all batches: the sum, over the batches, of the count of distinct
identifiers in each batch. Because the tally is per batch, an identifier that
recurs within one batch contributes once, while an identifier that recurs across
two different batches contributes once per batch it lands in. When the input
sequence is empty the operation performs no modification and reports a matched
count of zero. The reported total is always present (a count is returned in
every case).
-/

-- axioms-start
-- No unchanged callee is consumed as an opaque carrier here: the per-batch
-- matched-row tally and the batching are modeled directly as total operations
-- over the identifier sequence (see the `pure` region). No callee property is
-- consumed by the correctness proof.
-- axioms-end

-- pure-start
/-- The number of rows matched by one batch's set-based modification: a set-based
match keyed on a multiset of identifiers matches each *distinct* identifier once,
so the per-batch tally is the number of distinct identifiers in the batch. -/
def batchMatched (batch : List Int) : Nat := batch.dedup.length

/-- The total number of rows matched when the identifier sequence is processed in
fixed-size batches: split the sequence into consecutive batches of size
`batchSize`, then sum each batch's distinct-identifier count. Front-recursive
shape paired with the accumulator loop in the implementation. -/
def batchedMatchCount (batchSize : Nat) (keys : List Int) : Nat :=
  (List.toChunks batchSize keys).foldl (fun acc batch => acc + batchMatched batch) 0
-- pure-end

-- post-conditions-start
/-- The reported result is always a present count, and that count equals the
total number of rows matched across the fixed-size batches: the sum over batches
of the distinct-identifier count of each batch. This fully pins the result —
both its presence and its value are determined by the identifier sequence and
the batch size. -/
def problem_spec_bulkUpdate
    (keys : List Int) (batchSize : Nat) (result : Option Nat) : Prop :=
  result = some (batchedMatchCount batchSize keys)
-- post-conditions-end

-- impl-start
def implementation_bulkUpdate (keys : List Int) (batchSize : Nat) : Option Nat := Id.run do
  if keys.isEmpty then
    return some 0
  let batches := List.toChunks batchSize keys
  let mut rowsUpdated := 0
  for batch in batches do
    rowsUpdated := rowsUpdated + batch.dedup.length
  return some rowsUpdated
-- impl-end

-- proof-start
/-- Route B helper: the cleaned `forIn` accumulation over the batches equals the
closed-form `List.foldl` used by `batchedMatchCount`, generalized over the
accumulator. -/
theorem forIn_sum_bulkUpdate (batches : List (List Int)) (init : Nat) :
    Id.run (forIn batches init (fun batch r => ForInStep.yield (r + batch.dedup.length)))
      = batches.foldl (fun acc batch => acc + batch.dedup.length) init := by
  induction batches generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; rw [ih, List.foldl_cons]

theorem correct_bulkUpdate :
    ∀ (keys : List Int) (batchSize : Nat), 1 ≤ batchSize →
      problem_spec_bulkUpdate keys batchSize
        (implementation_bulkUpdate keys batchSize) := by
  intro keys batchSize hb
  unfold problem_spec_bulkUpdate implementation_bulkUpdate batchedMatchCount batchMatched
  by_cases h : keys.isEmpty
  · -- empty input: the early `return some 0` matches `toChunks _ [] = []`
    have hk : keys = [] := List.isEmpty_iff.mp h
    have hc : List.toChunks batchSize ([] : List Int) = [] := by
      cases batchSize with
      | zero => omega
      | succ m => rfl
    subst hk
    simp only [Id.run, h, if_true, hc, List.foldl_nil]
    rfl
  · -- non-empty input: bridge the desugared loop to the helper, then close
    simp only [Id.run, h, if_false, Bool.false_eq_true]
    show some (Id.run (forIn (List.toChunks batchSize keys) 0
        (fun batch r => ForInStep.yield (r + batch.dedup.length))))
      = some (List.foldl (fun acc batch => acc + batch.dedup.length) 0 (List.toChunks batchSize keys))
    rw [forIn_sum_bulkUpdate]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Same-spec check True for all 6 attacks + positive control + prepatch (swebench_unified.markers.same_spec, lean backend). Only impl region edited; axioms/pure/pre/post byte-identical.

CORE ANALYSIS: The postcondition `problem_spec_bulkUpdate keys batchSize result := result = some (batchedMatchCount batchSize keys)` is a TIGHT TOTAL FUNCTIONAL EQUALITY over the entire precondition domain (1 ≤ batchSize). Any impl that closes correct_bulkUpdate must be extensionally equal to gold on all keys and all batchSize ≥ 1. The only genuine looseness is batchSize=0 (excluded by the precondition binder), which never occurs in the real Python flow (batch_size/bulk_batch_size is always ≥1) — a SOUND looseness, not a break, so I did not count it.

### ATTACKS (6 distinct wrong impls; all lean_verify.sh exit=1 = do NOT close; ran concurrently ≤4 at a time):
- atk_1 (control-flow-effect / undercount-model echo): per-batch tally uses batch.length (rows-sent, no dedup). Counterexample keys=[7,7],bs=5: gold 1 vs 2. exit=1.
- atk_2 (ungrounded-oracle echo / global-distinct model): returns some keys.dedup.length (global dedup, ignores batching). keys=[7,7],bs=1: gold 2 vs 1. exit=1. This is exactly the F2P discriminator (test_updated_rows_when_passing_duplicates).
- atk_3 (constant/degenerate): returns some 0 always. keys=[1],bs=1: gold 1 vs 0. exit=1.
- atk_4 (boundary): empty branch returns some 1 instead of some 0; goal reduces literally to `pure (some 1) = some 0`. exit=1.
- atk_5 (control-flow-effect): loops over batches.tail (drops first batch). keys=[1],bs=1: gold 1 vs 0. exit=1.
- atk_7 (partial-domain): correct when keys.length ≤ batchSize (single batch) but returns keys.length (rows-sent) otherwise. keys=[1,1,2],bs=2 → two batches [[1,1],[2]]: gold 2 vs 3. exit=1.

Because NO wrong impl produced a closing clean-axiom proof, step-2 (materialize + run refined patch through resolve for every closing impl) is vacuously satisfied — there are zero verifying-but-wrong impls to falsify with the harness. No resolve run was needed or possible.

POSITIVE CONTROL: pos_control.lean = gold Solution.lean copy, lean_verify.sh exit=0 (clean, no sorry). `#print axioms correct_bulkUpdate` → depends on axioms: [propext, Quot.sound] (clean; no sorryAx, no native_decide/Lean.ofReduceBool, no custom axioms). Command: `bash scripts/lean_verify.sh <file>` from project root.

PREPATCH REPRODUCED: prepatch.lean (impl returns none in both branches = the real pre-patch bug where bulk_update returned None instead of a count) fails the gold proof, exit=1 (goal `...pure none = some (...)`), confirming the spec DETECTS the real bug (G-DIFF direction holds).

REFINEMENT.MD AUDIT: all 5 legs are R or I (leg1 R empty-branch, leg2 R batching toChunks, leg3 I accumulator init, leg4 R deep-model of UNCHANGED update(pk__in=pks) matched count = batch.dedup.length, leg5 R return). No kind-3 (uncovered) legs. No A-consumed / A-reference legs: axiom_check.py is a legitimate skip stub (no consumed callee axiom, no opaque decl, deep_model_references=[]). The A-leg mandate is therefore vacuous. The single deep-model decision (leg4: batch.dedup.length ↔ SQL WHERE pk IN(...) distinct-pk matched count under the modeled domain where every key references an existing row) is a sound total-operation model, validated by G-CONF over ≥1e5 fuzzed inputs; the correspondence to the real update() callee holds (SQL IN dedups, all referenced rows exist per modeled domain). This is R (deep model of an unchanged callee treated as a total list op), not a hidden A-reference.

All exit codes captured from lean_verify.sh (0=verifies/no-sorry, 1=error). No timeouts (no 124). Verdict SOUND: ≥5 distinct same-spec attacks (6) run, none closes, so verify⇒correct is not falsified here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-14559 lean bundle: NO divergence found; spec is a faithful, not-too-strong model of QuerySet.bulk_update's post-patch matched-row count.

Verification performed:
1. Solution.lean compiles via scripts/lean_verify.sh (exit 0). `#print axioms correct_bulkUpdate` = [propext, Quot.sound] — no sorryAx, proof is genuine.
2. same_spec(Solution.lean, Solution_prepatch.lean, lean_backend) = True — spec region byte-identical; pre/post differ only in impl/proof (prepatch returns none, correctly unclosable).
3. Modeled function: QuerySet.bulk_update in django/db/models/query.py @ base_commit. Verified against repo source and patch.diff (return->return 0 at empty branch; introduce rows_updated accumulator over batches; return rows_updated).
4. Batching: List.toChunks batchSize keys == Python `keys[i:i+bs] for i in range(0,len(keys),bs)` for batchSize>=1 (confirmed by #eval and Python cross-check). Precondition 1<=batchSize matches the real effective batch size (min(batch_size,max_batch_size), always >=1; non-positive batch_size raises before reaching modeled code).
5. Per-batch matched count: batch.dedup.length == len(set(batch)) == rows matched by WHERE pk IN (...) under the documented modeled domain (every key references an existing stored row). This is exactly what F2P test_updated_rows_when_passing_duplicates pins: [note,note] one batch -> 1; batch_size=1 (split) -> 2. Model reproduces both. test_large_batch (2000 distinct) -> 2000 and test_empty_objects -> 0 also reproduced.
6. Empty input: post-patch `return 0` <-> `some 0`; result presence (some n, never none) matches post-patch always returning an int.
7. Divergence search: 500k random (keys,bs) cases model-vs-real range-stride/distinct-pk oracle => 0 disagreements. conformance_check.py (120,007 cases incl. boundary discriminators, seed 14559) => status pass, 0 disagreements.

Modeling boundary 'all keys reference existing rows' is documented in mapping.md, sound (it is the domain bulk_update operates on — it updates already-stored objects), and G-CONF fuzzes within it. This is a legitimate domain restriction, not spec-too-strong drift: within the modeled domain the modeled function agrees with the real callee on every input. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = imports/docstring/axioms/pure/post-conditions (impl+proof elided). Mechanical G-LEAK screen passes clean (no diff markers, no query.py path/module, no gold-line reproduction, no bug/fix/prepatch narration). Substantive check: the public problem_statement ALREADY discloses the full gold intent — 'Include number of rows matched in bulk_update() return value. Currently bulk_update() returns None, unlike update()... bulk_update() simply calls update() repeatedly... the return values could simply be added and returned.' The spec view (batchMatched=batch.dedup.length, batchedMatchCount=foldl sum over toChunks, postcondition result=some(batchedMatchCount ...)) is just a faithful behavioral formalization of that public goal: return the summed count of matched rows across batched repeated update() calls, with empty input -> 0. Patched symbol 'bulk_update' is named throughout the public problem_statement (and the spec identifier is camelCase 'bulkUpdate' anyway), so no symbol-echo leak. The only non-public nuance — within-batch dedup vs across-batch double counting — lives in hints_text, but a faithful spec MUST pin correct behavior; stating the true postcondition of the requested feature reveals no edit localization or diff specifics beyond the public task. No leakage of the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
