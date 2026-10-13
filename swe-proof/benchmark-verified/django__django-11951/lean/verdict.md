# P2 adversarial audit — django__django-11951

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl both verifies with clean axioms AND has a faithful patch that fails to resolve. The only impl that verifies (atk_6) is a behaviorally-exact echo of the spec; its faithful patch is the gold patch, which RESOLVES (resolved=True, completed=True). All 6 behaviorally-distinct wrong impls fail to verify.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,13 +79,9 @@
 -- impl-start
 def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
     List (List α) := Id.run do
-  -- The compatible maximum, normalized to at least one usable slot.
   let maxBatchSize := max rawMax 1
-  -- A requested size never enlarges a batch beyond the compatible maximum; an
-  -- unset request (`0`) falls back to the compatible maximum.
-  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
-  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
-  -- emitting one consecutive batch per offset.
+  -- BUG (prepatch): a truthy requested size overrides the compatible maximum.
+  let eff := if batchSize = 0 then maxBatchSize else batchSize
   let mut batches : List (List α) := []
   for k in [0:batchCount eff objs.length] do
     batches := batches ++ [(objs.drop (k * eff)).take eff]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,13 +79,8 @@
 -- impl-start
 def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
     List (List α) := Id.run do
-  -- The compatible maximum, normalized to at least one usable slot.
-  let maxBatchSize := max rawMax 1
-  -- A requested size never enlarges a batch beyond the compatible maximum; an
-  -- unset request (`0`) falls back to the compatible maximum.
-  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
-  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
-  -- emitting one consecutive batch per offset.
+  -- BUG (boundary): skip the max(·,1) normalization; use rawMax directly.
+  let eff := if batchSize = 0 then rawMax else min batchSize rawMax
   let mut batches : List (List α) := []
   for k in [0:batchCount eff objs.length] do
     batches := batches ++ [(objs.drop (k * eff)).take eff]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,13 +79,9 @@
 -- impl-start
 def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
     List (List α) := Id.run do
-  -- The compatible maximum, normalized to at least one usable slot.
   let maxBatchSize := max rawMax 1
-  -- A requested size never enlarges a batch beyond the compatible maximum; an
-  -- unset request (`0`) falls back to the compatible maximum.
-  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
-  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
-  -- emitting one consecutive batch per offset.
+  -- BUG (partial-domain): use max instead of min on the truthy branch.
+  let eff := if batchSize = 0 then maxBatchSize else max batchSize maxBatchSize
   let mut batches : List (List α) := []
   for k in [0:batchCount eff objs.length] do
     batches := batches ++ [(objs.drop (k * eff)).take eff]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,16 +79,12 @@
 -- impl-start
 def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
     List (List α) := Id.run do
-  -- The compatible maximum, normalized to at least one usable slot.
   let maxBatchSize := max rawMax 1
-  -- A requested size never enlarges a batch beyond the compatible maximum; an
-  -- unset request (`0`) falls back to the compatible maximum.
   let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
-  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
-  -- emitting one consecutive batch per offset.
   let mut batches : List (List α) := []
+  -- BUG (control-flow-effect): prepend each batch, reversing the order.
   for k in [0:batchCount eff objs.length] do
-    batches := batches ++ [(objs.drop (k * eff)).take eff]
+    batches := [(objs.drop (k * eff)).take eff] ++ batches
   return batches
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,15 +79,11 @@
 -- impl-start
 def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
     List (List α) := Id.run do
-  -- The compatible maximum, normalized to at least one usable slot.
   let maxBatchSize := max rawMax 1
-  -- A requested size never enlarges a batch beyond the compatible maximum; an
-  -- unset request (`0`) falls back to the compatible maximum.
   let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
-  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
-  -- emitting one consecutive batch per offset.
   let mut batches : List (List α) := []
-  for k in [0:batchCount eff objs.length] do
+  -- BUG (off-by-one): iterate one index too many, appending a trailing slice.
+  for k in [0:batchCount eff objs.length + 1] do
     batches := batches ++ [(objs.drop (k * eff)).take eff]
   return batches
 -- impl-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -78,18 +78,9 @@
 
 -- impl-start
 def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
-    List (List α) := Id.run do
-  -- The compatible maximum, normalized to at least one usable slot.
-  let maxBatchSize := max rawMax 1
-  -- A requested size never enlarges a batch beyond the compatible maximum; an
-  -- unset request (`0`) falls back to the compatible maximum.
-  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
-  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
-  -- emitting one consecutive batch per offset.
-  let mut batches : List (List α) := []
-  for k in [0:batchCount eff objs.length] do
-    batches := batches ++ [(objs.drop (k * eff)).take eff]
-  return batches
+    List (List α) :=
+  -- ECHO: directly return the spec's own definition.
+  chunkBatches (effectiveBatchSize batchSize rawMax) objs
 -- impl-end
 
 -- proof-start
@@ -117,11 +108,6 @@
       problem_spec_splitBatches batchSize rawMax objs
         (implementation_splitBatches batchSize rawMax objs) := by
   intro α batchSize rawMax objs
-  unfold problem_spec_splitBatches implementation_splitBatches chunkBatches
-        effectiveBatchSize
-  simp only [Id.run]
-  rw [Std.Range.forIn_eq_forIn_range']
-  simp only [Std.Range.size, Nat.sub_zero, Nat.add_one_sub_one, Nat.div_one]
-  rw [List.range_eq_range']
-  exact forIn_append_map _ _ _
+  unfold problem_spec_splitBatches implementation_splitBatches
+  rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,13 +79,10 @@
 -- impl-start
 def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
     List (List α) := Id.run do
-  -- The compatible maximum, normalized to at least one usable slot.
   let maxBatchSize := max rawMax 1
-  -- A requested size never enlarges a batch beyond the compatible maximum; an
-  -- unset request (`0`) falls back to the compatible maximum.
-  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
-  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
-  -- emitting one consecutive batch per offset.
+  -- BUG (cap off-by-one): cap to maxBatchSize+1 instead of maxBatchSize.
+  let eff := if batchSize = 0 then maxBatchSize
+             else if batchSize < maxBatchSize then batchSize else maxBatchSize + 1
   let mut batches : List (List α) := []
   for k in [0:batchCount eff objs.length] do
     batches := batches ++ [(objs.drop (k * eff)).take eff]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Splitting a collection of objects into the consecutive batches that a bulk
operation will process one at a time.

Two sizes constrain the batching:

* a caller-supplied requested size, which may be left unset (modeled as the value
  `0`, the "no request" marker);
* a compatible maximum size that the storage backend can handle for the objects
  in question. This compatible maximum is taken as given here (it is computed
  elsewhere from the objects and their fields) and is normalized to be at least
  `1`, so a usable batch size always exists.

The effective per-batch size is then:

* the compatible maximum, when the caller requested no particular size;
* otherwise the smaller of the requested size and the compatible maximum — a
  request never enlarges a batch beyond what the backend can compatibly handle,
  but a request smaller than the maximum is honored.

Given that effective size, the objects are partitioned into consecutive,
non-overlapping batches in order: each batch holds up to the effective size many
objects, the next begins exactly where the previous ended, and the final batch
holds whatever remains. The number and contents of these batches are fully
determined by the inputs.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The only outside operation
-- used here — obtaining the backend's compatible maximum batch size — has its
-- result supplied as an input (`rawMax`); the size selection and the partitioning
-- of the objects are spelled out concretely below.
-- axioms-end

-- pure-start
/-- The effective per-batch size. `batchSize = 0` models "no size requested": the
compatible maximum (normalized to at least `1`) is used. Otherwise the smaller of
the requested size and the compatible maximum is used, so a request can shrink a
batch but never enlarge it past the compatible maximum. The result is always
`≥ 1`. -/
def effectiveBatchSize (batchSize rawMax : Nat) : Nat :=
  let maxBatchSize := max rawMax 1
  if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize

/-- The number of consecutive batches of size `eff` needed to cover `n` objects,
i.e. `⌈n / eff⌉` for `eff ≥ 1` (the count of start offsets `0, eff, 2·eff, …`
that are `< n`). -/
def batchCount (eff n : Nat) : Nat := (n + eff - 1) / eff

/-- The consecutive batches `objs` is split into, each holding up to `eff`
elements: batch `k` is the slice of `objs` starting at offset `k · eff` and
spanning `eff` elements. There are `batchCount eff objs.length` batches. -/
def chunkBatches (eff : Nat) (objs : List α) : List (List α) :=
  (List.range (batchCount eff objs.length)).map (fun k => (objs.drop (k * eff)).take eff)
-- pure-end

-- post-conditions-start
/-- Input→output relation for splitting `objs` into bulk batches.

Inputs:
* `batchSize` — the caller-requested batch size (`0` = unset);
* `rawMax`    — the backend's compatible maximum batch size (taken as given);
* `objs`      — the objects to partition.

The result is the consecutive partition of `objs` into batches whose size is the
effective batch size derived from `batchSize` and `rawMax`. The whole output is
pinned to the inputs. -/
def problem_spec_splitBatches (batchSize rawMax : Nat) (objs : List α)
    (result : List (List α)) : Prop :=
  result = chunkBatches (effectiveBatchSize batchSize rawMax) objs
-- post-conditions-end

-- impl-start
def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
    List (List α) := Id.run do
  -- The compatible maximum, normalized to at least one usable slot.
  let maxBatchSize := max rawMax 1
  -- A requested size never enlarges a batch beyond the compatible maximum; an
  -- unset request (`0`) falls back to the compatible maximum.
  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
  -- emitting one consecutive batch per offset.
  let mut batches : List (List α) := []
  for k in [0:batchCount eff objs.length] do
    batches := batches ++ [(objs.drop (k * eff)).take eff]
  return batches
-- impl-end

-- proof-start
/-- The `forIn` loop (in its desugared `do pure PUnit.unit; pure (yield …)`
form) that appends one mapped element per index over a list of indices `xs`
produces `acc ++ xs.map f`. Proved by induction on `xs`, generalizing the
accumulator. -/
theorem forIn_append_map {β : Type} (xs : List Nat) (acc : List β)
    (f : Nat → β) :
    (Id.run (do
        let r ← forIn (m := Id) xs acc
          (fun k r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [f k])))
        pure r))
      = acc ++ xs.map f := by
  induction xs generalizing acc with
  | nil => simp [Id.run]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]

theorem correct_splitBatches :
    ∀ {α : Type} (batchSize rawMax : Nat) (objs : List α),
      problem_spec_splitBatches batchSize rawMax objs
        (implementation_splitBatches batchSize rawMax objs) := by
  intro α batchSize rawMax objs
  unfold problem_spec_splitBatches implementation_splitBatches chunkBatches
        effectiveBatchSize
  simp only [Id.run]
  rw [Std.Range.forIn_eq_forIn_range']
  simp only [Std.Range.size, Nat.sub_zero, Nat.add_one_sub_one, Nat.div_one]
  rw [List.range_eq_range']
  exact forIn_append_map _ _ _
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 7 attacks confirmed same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Only the impl region was edited; axioms/pure/pre/post byte-identical.

VERIFY COMMANDS: `bash scripts/lean_verify.sh <file>`.
### Results
- pos_control.lean (gold impl): exit 0 (verifies). Positive control OK.
- atk_1.lean (prepatch bug: eff:=batchSize on truthy branch): exit 1 (does NOT verify).
- atk_2.lean (boundary: drop max(rawMax,1) normalization): exit 1.
- atk_3.lean (partial-domain: min->max on truthy branch): exit 1.
- atk_4.lean (control-flow-effect: prepend batches, reversed order): exit 1.
- atk_5.lean (off-by-one: batchCount+1, trailing extra batch): exit 1.
- atk_7.lean (cap off-by-one: cap to maxBatchSize+1): exit 1.
- atk_6.lean (ungrounded-oracle echo: returns chunkBatches (effectiveBatchSize ..) objs directly): exit 0 (VERIFIES). #print axioms correct_splitBatches => 'correct_splitBatches does not depend on any axioms' (clean, atk_6_ax.lean exit 0).

RESOLVE (mandatory for every verifying impl): atk_6 is behaviorally identical to gold, so its faithful refined patch is the gold patch (atk_6_patch.diff, taken from data/swe_bench_verified/test.jsonl). run_resolve('django__django-11951', gold_patch, timeout=1800) => resolved=True completed=True note='resolved'. Per the eq/panel-1 resolving-echo policy, a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness.

WHY SOUND: postcondition problem_spec_splitBatches pins output exactly (result = chunkBatches (effectiveBatchSize batchSize rawMax) objs). Any behaviorally-different impl provably cannot close correct_splitBatches (confirmed: atk_1-5,7 all exit 1). No falsification exists.

REFINEMENT.MD AUDIT: axioms block EMPTY (grep confirms no `axiom`/`opaque`/`sorry`/`admit`/`native_decide` in Solution.lean). No A-consumed legs => no over-strong-axiom leak channel. Legs are R (input/output type refinements, positional identity), I (max(rawMax,1) normalization present pre&post-patch; the unchanged slicing comprehension), and one A-reference leg: effectiveBatchSize ↔ `batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size` — matches the gold post-patch expression exactly and is differential-tested by G-CONF (conformance_check.py oracle uses the exact patched Python, shadow transliterates the Lean; SEED=20240627, 120k fuzz + edge cases, G-CONF status=pass in meta.json). No kind-3 legs. A-reference correspondence to the real callee (ops.bulk_batch_size supplied as input rawMax, UNCHANGED across patch) holds.

SCHEDULE: attack verifications run as concurrent background Bash jobs, <=4 at a time (batch1: pos+atk_1/2/3; batch2: atk_4/5/6/7); resolve run separately. This changed only schedule, not pass criteria.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl both verifies with clean axioms AND has a faithful patch that fails to resolve. The only impl that verifies (atk_6) is a behaviorally-exact echo of the spec; its faithful patch is the gold patch, which RESOLVES (resolved=True, completed=True). All 6 behaviorally-distinct wrong impls fail to verify.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Splitting a collection of objects into the consecutive batches that a bulk
operation will process one at a time.

Two sizes constrain the batching:

* a caller-supplied requested size, which may be left unset (modeled as the value
  `0`, the "no request" marker);
* a compatible maximum size that the storage backend can handle for the objects
  in question. This compatible maximum is taken as given here (it is computed
  elsewhere from the objects and their fields) and is normalized to be at least
  `1`, so a usable batch size always exists.

The effective per-batch size is then:

* the compatible maximum, when the caller requested no particular size;
* otherwise the smaller of the requested size and the compatible maximum — a
  request never enlarges a batch beyond what the backend can compatibly handle,
  but a request smaller than the maximum is honored.

Given that effective size, the objects are partitioned into consecutive,
non-overlapping batches in order: each batch holds up to the effective size many
objects, the next begins exactly where the previous ended, and the final batch
holds whatever remains. The number and contents of these batches are fully
determined by the inputs.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. The only outside operation
-- used here — obtaining the backend's compatible maximum batch size — has its
-- result supplied as an input (`rawMax`); the size selection and the partitioning
-- of the objects are spelled out concretely below.
-- axioms-end

-- pure-start
/-- The effective per-batch size. `batchSize = 0` models "no size requested": the
compatible maximum (normalized to at least `1`) is used. Otherwise the smaller of
the requested size and the compatible maximum is used, so a request can shrink a
batch but never enlarge it past the compatible maximum. The result is always
`≥ 1`. -/
def effectiveBatchSize (batchSize rawMax : Nat) : Nat :=
  let maxBatchSize := max rawMax 1
  if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize

/-- The number of consecutive batches of size `eff` needed to cover `n` objects,
i.e. `⌈n / eff⌉` for `eff ≥ 1` (the count of start offsets `0, eff, 2·eff, …`
that are `< n`). -/
def batchCount (eff n : Nat) : Nat := (n + eff - 1) / eff

/-- The consecutive batches `objs` is split into, each holding up to `eff`
elements: batch `k` is the slice of `objs` starting at offset `k · eff` and
spanning `eff` elements. There are `batchCount eff objs.length` batches. -/
def chunkBatches (eff : Nat) (objs : List α) : List (List α) :=
  (List.range (batchCount eff objs.length)).map (fun k => (objs.drop (k * eff)).take eff)
-- pure-end

-- post-conditions-start
/-- Input→output relation for splitting `objs` into bulk batches.

Inputs:
* `batchSize` — the caller-requested batch size (`0` = unset);
* `rawMax`    — the backend's compatible maximum batch size (taken as given);
* `objs`      — the objects to partition.

The result is the consecutive partition of `objs` into batches whose size is the
effective batch size derived from `batchSize` and `rawMax`. The whole output is
pinned to the inputs. -/
def problem_spec_splitBatches (batchSize rawMax : Nat) (objs : List α)
    (result : List (List α)) : Prop :=
  result = chunkBatches (effectiveBatchSize batchSize rawMax) objs
-- post-conditions-end

-- impl-start
def implementation_splitBatches (batchSize rawMax : Nat) (objs : List α) :
    List (List α) := Id.run do
  -- The compatible maximum, normalized to at least one usable slot.
  let maxBatchSize := max rawMax 1
  -- A requested size never enlarges a batch beyond the compatible maximum; an
  -- unset request (`0`) falls back to the compatible maximum.
  let eff := if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize
  -- Walk the start offsets `0, eff, 2·eff, …` that fall within the collection,
  -- emitting one consecutive batch per offset.
  let mut batches : List (List α) := []
  for k in [0:batchCount eff objs.length] do
    batches := batches ++ [(objs.drop (k * eff)).take eff]
  return batches
-- impl-end

-- proof-start
/-- The `forIn` loop (in its desugared `do pure PUnit.unit; pure (yield …)`
form) that appends one mapped element per index over a list of indices `xs`
produces `acc ++ xs.map f`. Proved by induction on `xs`, generalizing the
accumulator. -/
theorem forIn_append_map {β : Type} (xs : List Nat) (acc : List β)
    (f : Nat → β) :
    (Id.run (do
        let r ← forIn (m := Id) xs acc
          (fun k r => do pure PUnit.unit; pure (ForInStep.yield (r ++ [f k])))
        pure r))
      = acc ++ xs.map f := by
  induction xs generalizing acc with
  | nil => simp [Id.run]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.map_cons, List.append_assoc]

theorem correct_splitBatches :
    ∀ {α : Type} (batchSize rawMax : Nat) (objs : List α),
      problem_spec_splitBatches batchSize rawMax objs
        (implementation_splitBatches batchSize rawMax objs) := by
  intro α batchSize rawMax objs
  unfold problem_spec_splitBatches implementation_splitBatches chunkBatches
        effectiveBatchSize
  simp only [Id.run]
  rw [Std.Range.forIn_eq_forIn_range']
  simp only [Std.Range.size, Nat.sub_zero, Nat.add_one_sub_one, Nat.div_one]
  rw [List.range_eq_range']
  exact forIn_append_map _ _ _
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 All 7 attacks confirmed same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Only the impl region was edited; axioms/pure/pre/post byte-identical.

VERIFY COMMANDS: `bash scripts/lean_verify.sh <file>`.
### Results
- pos_control.lean (gold impl): exit 0 (verifies). Positive control OK.
- atk_1.lean (prepatch bug: eff:=batchSize on truthy branch): exit 1 (does NOT verify).
- atk_2.lean (boundary: drop max(rawMax,1) normalization): exit 1.
- atk_3.lean (partial-domain: min->max on truthy branch): exit 1.
- atk_4.lean (control-flow-effect: prepend batches, reversed order): exit 1.
- atk_5.lean (off-by-one: batchCount+1, trailing extra batch): exit 1.
- atk_7.lean (cap off-by-one: cap to maxBatchSize+1): exit 1.
- atk_6.lean (ungrounded-oracle echo: returns chunkBatches (effectiveBatchSize ..) objs directly): exit 0 (VERIFIES). #print axioms correct_splitBatches => 'correct_splitBatches does not depend on any axioms' (clean, atk_6_ax.lean exit 0).

RESOLVE (mandatory for every verifying impl): atk_6 is behaviorally identical to gold, so its faithful refined patch is the gold patch (atk_6_patch.diff, taken from data/swe_bench_verified/test.jsonl). run_resolve('django__django-11951', gold_patch, timeout=1800) => resolved=True completed=True note='resolved'. Per the eq/panel-1 resolving-echo policy, a same-spec verifying impl whose refined patch RESOLVES is NOT a weakness.

WHY SOUND: postcondition problem_spec_splitBatches pins output exactly (result = chunkBatches (effectiveBatchSize batchSize rawMax) objs). Any behaviorally-different impl provably cannot close correct_splitBatches (confirmed: atk_1-5,7 all exit 1). No falsification exists.

REFINEMENT.MD AUDIT: axioms block EMPTY (grep confirms no `axiom`/`opaque`/`sorry`/`admit`/`native_decide` in Solution.lean). No A-consumed legs => no over-strong-axiom leak channel. Legs are R (input/output type refinements, positional identity), I (max(rawMax,1) normalization present pre&post-patch; the unchanged slicing comprehension), and one A-reference leg: effectiveBatchSize ↔ `batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size` — matches the gold post-patch expression exactly and is differential-tested by G-CONF (conformance_check.py oracle uses the exact patched Python, shadow transliterates the Lean; SEED=20240627, 120k fuzz + edge cases, G-CONF status=pass in meta.json). No kind-3 legs. A-reference correspondence to the real callee (ops.bulk_batch_size supplied as input rawMax, UNCHANGED across patch) holds.

SCHEDULE: attack verifications run as concurrent background Bash jobs, <=4 at a time (batch1: pos+atk_1/2/3; batch2: atk_4/5/6/7); resolve run separately. This changed only schedule, not pass criteria.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-11951 lean bundle.

### Setup verified
- Spec region byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(...) = True.
- Solution.lean compiles via scripts/lean_verify.sh (exit 0, no sorry).
- #print axioms correct_splitBatches => [propext, Classical.choice, Quot.sound] only; no sorryAx, proof is genuine.

### MODELED FUNCTION vs REAL REPO (django/db/models/query.py _batched_insert @ base 312049091288; gold patch at patch.diff lines 1318-1322):
  Real (post-patch): max_batch_size = max(ops.bulk_batch_size(fields,objs),1); batch_size = min(batch_size,max_batch_size) if batch_size else max_batch_size; then [objs[i:i+batch_size] for i in range(0,len(objs),batch_size)].
  Spec: effectiveBatchSize batchSize rawMax = let m=max rawMax 1; if batchSize=0 then m else min batchSize m  — identical selection. chunkBatches eff objs = map (k => (objs.drop (k*eff)).take eff) over range(batchCount eff n) where batchCount eff n = (n+eff-1)/eff. For eff>=1 this equals len(range(0,n,eff)) and offsets k*eff coincide with range(0,n,eff); slice (drop i).take eff == objs[i:i+eff]. eff>=1 always (max rawMax 1 >=1; min batchSize m >=1 when batchSize>=1).

DOMAIN / DEAD-INPUT CHECK: bulk_create rejects batch_size<=0 (query.py:489) before reaching _batched_insert, so only None(falsy) or positive ints arrive. Model maps None->0 (unset marker) faithfully; negative/zero requested sizes are unreachable, so the Nat model omits no live path. rawMax models bulk_batch_size (int>=0); max(.,1) applied identically.

SEARCHED FOR DIVERGENCE: empty objs (both []), rawMax=0 (both normalize to 1), batchSize > rawMax (both cap to max -> the F2P fix), batchSize < rawMax (both honor request), batchSize=rawMax, exact multiples, remainders. conformance_check.py oracle (exact patched expressions) vs shadow agree over edge set + 120k fuzz (seed 20240627). No diverging input exists; the spec is a deep exact transliteration, neither too strong nor drifted.

VERDICT: FAITHFUL (no defect found).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `batch_size = (batch_size or max(...,1))` -> `max_batch_size = max(ops.bulk_batch_size(fields,objs),1); batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size`. The public problem_statement ALREADY discloses this exact fix verbatim: the reporter writes 'I suggest using similar `batch_size = min(batch_size, max_batch_size) if batch_size else max_batch_size` logic in bulk_create as well.' So the clamp-to-max selection is public.

Spec view (Solution.lean prose + effectiveBatchSize/problem_spec_splitBatches, lines 1-77, verified byte-identical to Solution_prepatch.lean via diff): effectiveBatchSize = `if batchSize = 0 then maxBatchSize else min batchSize maxBatchSize` and the prose ('the smaller of the requested size and the compatible maximum — a request never enlarges a batch beyond what the backend can compatibly handle, but a request smaller than the maximum is honored') restate exactly the min/clamp behavior the problem_statement already spells out. Nothing in the shared spec view reveals the gold edit beyond the public problem_statement.

refinement.md and mapping.md do quote the full pre/post patch lines, but (a) those are auditor-derivation artifacts, not the solver-facing spec view, and (b) the content they expose is identical to what the public problem_statement already states, so no leakage beyond problem_statement.

Spec region byte-identical between Solution.lean and Solution_prepatch.lean confirmed (lines 1-77 diff clean).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
