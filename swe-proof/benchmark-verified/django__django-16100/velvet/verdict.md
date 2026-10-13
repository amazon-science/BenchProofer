# P2 adversarial audit — django__django-16100

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = committedAtomic updates` is a TOTAL functional equality that pins the output for every input, so no behaviourally-wrong same-spec impl verifies. The only same-spec impl that verifies (atk_6, the ungrounded-oracle echo `return committedAtomic updates`) is behaviourally CORRECT: its faithful refined patch is the gold `transaction.atomic` wrap, which RESOLVES under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,8 +104,6 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
     let mut staged : List Int := []
     let mut failed : Bool := false
     let mut i : Nat := updates.length
@@ -117,14 +115,11 @@
       decreasing i
     do
       let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
       staged := (if u.changed then [u.value] else []) ++ staged
       failed := (u.changed && u.raises) || failed
       i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
-    let committed : List Int := if failed then [] else staged
+    -- BUG: commit staged regardless of failure (no atomic rollback)
+    let committed : List Int := staged
     return committed
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,28 +104,8 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
-    let mut staged : List Int := []
-    let mut failed : Bool := false
-    let mut i : Nat := updates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ updates.length
-      invariant staged = changedVals (updates.drop i)
-      invariant failed = anyFail (updates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
-      staged := (if u.changed then [u.value] else []) ++ staged
-      failed := (u.changed && u.raises) || failed
-      i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
-    let committed : List Int := if failed then [] else staged
-    return committed
+    -- BUG: commit every edited row's write, never roll back on error
+    return changedVals updates
     -- impl-end
 
 prove_correct processBatch by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,8 +104,6 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
     let mut staged : List Int := []
     let mut failed : Bool := false
     let mut i : Nat := updates.length
@@ -117,14 +115,11 @@
       decreasing i
     do
       let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
       staged := (if u.changed then [u.value] else []) ++ staged
       failed := (u.changed && u.raises) || failed
       i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
-    let committed : List Int := if failed then [] else staged
+    -- BUG: commit ONLY when failed (inverted)
+    let committed : List Int := if failed then staged else []
     return committed
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,11 +104,10 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
     let mut staged : List Int := []
     let mut failed : Bool := false
-    let mut i : Nat := updates.length
+    -- BUG: start one short, skipping the final row
+    let mut i : Nat := updates.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ updates.length
       invariant staged = changedVals (updates.drop i)
@@ -117,13 +116,9 @@
       decreasing i
     do
       let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
       staged := (if u.changed then [u.value] else []) ++ staged
       failed := (u.changed && u.raises) || failed
       i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
     let committed : List Int := if failed then [] else staged
     return committed
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,28 +104,8 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
-    let mut staged : List Int := []
-    let mut failed : Bool := false
-    let mut i : Nat := updates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ updates.length
-      invariant staged = changedVals (updates.drop i)
-      invariant failed = anyFail (updates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
-      staged := (if u.changed then [u.value] else []) ++ staged
-      failed := (u.changed && u.raises) || failed
-      i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
-    let committed : List Int := if failed then [] else staged
-    return committed
+    -- BUG: never commit anything
+    return []
     -- impl-end
 
 prove_correct processBatch by
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -104,38 +104,9 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
-    let mut staged : List Int := []
-    let mut failed : Bool := false
-    let mut i : Nat := updates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ updates.length
-      invariant staged = changedVals (updates.drop i)
-      invariant failed = anyFail (updates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
-      staged := (if u.changed then [u.value] else []) ++ staged
-      failed := (u.changed && u.raises) || failed
-      i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
-    let committed : List Int := if failed then [] else staged
-    return committed
+    -- Echo: return the spec model directly.
+    return committedAtomic updates
     -- impl-end
 
 prove_correct processBatch by
-  loom_solve <;>
-    first
-    | -- loop-entry: drop updates.length = [], both folds are nil.
-      (rw [List.drop_length]; simp)
-    | -- loop-body step: peel row `i-1` from the staged-values fold.
-      (rw [changedVals_drop_step updates i (by omega) (by omega)]; simp_all)
-    | -- loop-body step: peel row `i-1` from the error scan.
-      (rw [anyFail_drop_step updates i (by omega) (by omega)]; simp_all)
-    | -- exit (i = 0): `drop 0 = updates`, so the commit equals `committedAtomic`.
-      (simp only [committedAtomic] at *; simp_all)
+  loom_solve <;> rfl
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,28 +104,11 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
-    let mut staged : List Int := []
-    let mut failed : Bool := false
-    let mut i : Nat := updates.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ updates.length
-      invariant staged = changedVals (updates.drop i)
-      invariant failed = anyFail (updates.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
-      staged := (if u.changed then [u.value] else []) ++ staged
-      failed := (u.changed && u.raises) || failed
-      i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
-    let committed : List Int := if failed then [] else staged
-    return committed
+    -- BUG (partial-domain): correct except returns a bogus write on empty batch
+    if updates.isEmpty then
+      return [1]
+    else
+      return committedAtomic updates
     -- impl-end
 
 prove_correct processBatch by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,8 +104,6 @@
   ensures out = committedAtomic updates
   do
     -- impl-start
-    -- All staged writes accumulate in one unit of work (`staged`); `failed`
-    -- records whether processing any row signalled an error escaping that unit.
     let mut staged : List Int := []
     let mut failed : Bool := false
     let mut i : Nat := updates.length
@@ -117,13 +115,10 @@
       decreasing i
     do
       let u := updates[i - 1]!
-      -- an edited row stages its write into the unit of work; a downstream step
-      -- may signal a failure of the unit while processing that row.
       staged := (if u.changed then [u.value] else []) ++ staged
-      failed := (u.changed && u.raises) || failed
+      -- BUG: overwrite rather than accumulate — only row 0's failure survives
+      failed := (u.changed && u.raises)
       i := i - 1
-    -- Commit point: a clean unit commits its staged writes; a failed unit
-    -- commits nothing (the whole batch is rolled back as one unit of work).
     let committed : List Int := if failed then [] else staged
     return committed
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled save loop is a bounded pass over a finite
-- batch of queued updates that always terminates and reports its commit set,
-- so a diverging implementation must NOT satisfy the spec (partial
-- correctness would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The all-or-nothing commit behaviour the desired
--  semantics requires is modeled DEEPLY in the `pure` region (`committedAtomic`): a batch of
--  record updates is committed only if the whole batch is processed without an
--  error, otherwise no update is committed. The unchanged commit/rollback
--  machinery this rides on is an A-reference, validated against the real
--  transaction manager by axiom_check.py (G-AX); there is no module-level
--  `axiom`. mapping.md §3.)
-- axioms-end

-- pure-start
/- One queued record update in a save batch. The only facts the desired
   behaviour distinguishes are: whether this row was actually edited (`changed`
   — an unedited row stages no write), the new value its write would persist
   (`value` — an opaque identity token; presence in the result means the write
   was committed), and whether processing this row encounters an error
   (`raises` — e.g. a downstream step signalling a failure). Everything else
   about the record is orthogonal (mapping.md §2). -/
structure Upd where
  changed : Bool
  value   : Int
  raises  : Bool
deriving Inhabited, DecidableEq

/- Does processing the batch encounter an error? An error can only arise while
   processing an edited row (an unedited row stages no work). Front-recursive so
   a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def anyFail : List Upd → Bool
  | []      => false
  | u :: us => (u.changed && u.raises) || anyFail us

/- The values the edited rows would stage, in batch order — what a clean run of
   the batch commits. Front-recursive (the fold pattern). -/
def changedVals : List Upd → List Int
  | []      => []
  | u :: us => (if u.changed then [u.value] else []) ++ changedVals us

/- The set of writes actually committed after the WHOLE batch is processed under
   all-or-nothing semantics: if any error is encountered anywhere in the batch,
   nothing is committed (the batch is rolled back as a unit); otherwise every
   edited row's write is committed. This is the desired behaviour — partial
   progress is never left behind when the batch fails midway. -/
def committedAtomic (us : List Upd) : List Int :=
  if anyFail us then [] else changedVals us

@[simp] lemma anyFail_nil : anyFail [] = false := rfl
@[simp] lemma changedVals_nil : changedVals [] = [] := rfl
lemma anyFail_cons (u : Upd) (us : List Upd) :
    anyFail (u :: us) = ((u.changed && u.raises) || anyFail us) := rfl
lemma changedVals_cons (u : Upd) (us : List Upd) :
    changedVals (u :: us) = (if u.changed then [u.value] else []) ++ changedVals us := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (us : List Upd) (i : Nat) (hi : i < us.length) :
    us.drop i = us[i]! :: us.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-row fold step for the error scan: dropping one fewer element exposes
   row `i-1` on the front, so the scan peels its error contribution. -/
lemma anyFail_drop_step (us : List Upd) (i : Nat) (hi : 0 < i) (hle : i ≤ us.length) :
    anyFail (us.drop (i - 1)) =
      ((us[i - 1]!.changed && us[i - 1]!.raises) || anyFail (us.drop i)) := by
  have hlt : i - 1 < us.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq us (i - 1) hlt, hsucc, anyFail_cons]

/- The per-row fold step for the staged values. -/
lemma changedVals_drop_step (us : List Upd) (i : Nat) (hi : 0 < i) (hle : i ≤ us.length) :
    changedVals (us.drop (i - 1)) =
      (if us[i - 1]!.changed then [us[i - 1]!.value] else []) ++ changedVals (us.drop i) := by
  have hlt : i - 1 < us.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq us (i - 1) hlt, hsucc, changedVals_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Process a batch of queued record updates and report which writes end up
   committed. Desired behaviour (all-or-nothing): the batch is a single unit of
   work — if processing any row raises an error, the result must commit NOTHING
   (every staged write is rolled back, so a failure midway leaves no partial
   progress); only a batch processed end-to-end without error commits its edited
   rows' writes. `updates` is read-only (not `mut`): the batch description is not
   mutated, only consulted (directive 5). -/
method processBatch (updates : List Upd) return (out : List Int)
  ensures out = committedAtomic updates
  do
    -- impl-start
    -- All staged writes accumulate in one unit of work (`staged`); `failed`
    -- records whether processing any row signalled an error escaping that unit.
    let mut staged : List Int := []
    let mut failed : Bool := false
    let mut i : Nat := updates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ updates.length
      invariant staged = changedVals (updates.drop i)
      invariant failed = anyFail (updates.drop i)
      done_with i = 0
      decreasing i
    do
      let u := updates[i - 1]!
      -- an edited row stages its write into the unit of work; a downstream step
      -- may signal a failure of the unit while processing that row.
      staged := (if u.changed then [u.value] else []) ++ staged
      failed := (u.changed && u.raises) || failed
      i := i - 1
    -- Commit point: a clean unit commits its staged writes; a failed unit
    -- commits nothing (the whole batch is rolled back as one unit of work).
    let committed : List Int := if failed then [] else staged
    return committed
    -- impl-end

prove_correct processBatch by
  loom_solve <;>
    first
    | -- loop-entry: drop updates.length = [], both folds are nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel row `i-1` from the staged-values fold.
      (rw [changedVals_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- loop-body step: peel row `i-1` from the error scan.
      (rw [anyFail_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- exit (i = 0): `drop 0 = updates`, so the commit equals `committedAtomic`.
      (simp only [committedAtomic] at *; simp_all)
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed fully in /tmp scratch dir.

POSITIVE CONTROL: pc.lean (byte-identical to frozen Solution.lean) -> lean_verify.sh exit 0 (verifies).
PREPATCH: prepatch.lean (commit `staged` without rollback) -> exit 1, unsolved goal exactly `i_1 = true -> staged_1 = []` as refinement.md B/G-DIFF documents. Prepatch bug reproduced.

### ATTACKS (each `bash scripts/lean_verify.sh <path>`, run concurrently <=4 at a time):
- atk_1.lean (no-rollback / partial-commit, = prepatch bug re-encoded): exit 1 REJECTED (goal i_1=true -> staged_1=[]).
- atk_2.lean (ungrounded: always `changedVals updates`, never roll back): exit 1 REJECTED (goal anyFail=true -> changedVals=[]).
- atk_3.lean (inverted commit condition `if failed then staged else []`): exit 1 REJECTED.
- atk_4.lean (boundary/off-by-one: i starts at length-1, skips last row): exit 1 REJECTED.
- atk_5.lean (always []): exit 1 REJECTED (goal anyFail=false -> changedVals=[]).
- atk_6.lean (ungrounded-oracle echo `return committedAtomic updates`, trivial proof `loom_solve <;> rfl`): exit 0 VERIFIES. This is the sole verifying same-spec impl and it is behaviourally correct.
- atk_7.lean (partial-domain: returns [1] on empty batch, else committedAtomic): exit 1 REJECTED (goal False under updates=[]).
- atk_8.lean (control-flow-effect: `failed := (u.changed && u.raises)` overwrite instead of accumulate): exit 1 REJECTED.

MANDATORY RESOLVE RUN: atk_6 is the only verifying attack, so per protocol its faithful refined patch was materialized (= gold patch, since the echo refines exactly to the transaction.atomic wrap A4) and RUN through the official harness: run_resolve('django__django-16100', patch, timeout=1800, retries=1) on active benchmark swe_bench_verified (supports_docker=True) => RESOLVED=True, COMPLETED=True, note='resolved'. verify does NOT imply incorrect here: the sole verifying impl resolves. Spec NOT broken.

REFINEMENT.MD AUDIT: legs A1(R), A2(R+I), A3(R+I), A4(A-reference+I), A5(A-reference). No kind-3 (inexpressible changed-op) legs; the genuinely-changed op (atomic wrap) is modeled deeply, not hidden behind a consumed axiom. meta.json axioms==[] confirms no A-consumed legs. The load-bearing A-reference committedAtomic<->transaction.atomic is validated by axiom_check.py which runs the patch's real save loop INSIDE a real transaction.atomic(using=router.db_for_write(Row)) and asserts durable DB state == committedAtomic(batch) over 9 boundary + 2000 fuzz batches (mid-batch raise -> [], clean -> changedVals); A5 router.db_for_write checked to resolve to real alias 'default' and orthogonal to rollback. Correspondence holds. G-CONF is a genuine conf_skip (only observable is a live DB commit/rollback side effect; no DB-free R/I shadow to fuzz).

VERDICT: SOUND. >=5 distinct wrong-impl attacks (partial-domain atk_7, boundary atk_4, control-flow-effect atk_8, ungrounded-oracle atk_2/atk_5, plus prepatch bug atk_1 and inverted atk_3) run and none breaks the spec; the only verifying same-spec impl (echo) resolves under the harness. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition `out = committedAtomic updates` is a TOTAL functional equality that pins the output for every input, so no behaviourally-wrong same-spec impl verifies. The only same-spec impl that verifies (atk_6, the ungrounded-oracle echo `return committedAtomic updates`) is behaviourally CORRECT: its faithful refined patch is the gold `transaction.atomic` wrap, which RESOLVES under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled save loop is a bounded pass over a finite
-- batch of queued updates that always terminates and reports its commit set,
-- so a diverging implementation must NOT satisfy the spec (partial
-- correctness would admit it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The all-or-nothing commit behaviour the desired
--  semantics requires is modeled DEEPLY in the `pure` region (`committedAtomic`): a batch of
--  record updates is committed only if the whole batch is processed without an
--  error, otherwise no update is committed. The unchanged commit/rollback
--  machinery this rides on is an A-reference, validated against the real
--  transaction manager by axiom_check.py (G-AX); there is no module-level
--  `axiom`. mapping.md §3.)
-- axioms-end

-- pure-start
/- One queued record update in a save batch. The only facts the desired
   behaviour distinguishes are: whether this row was actually edited (`changed`
   — an unedited row stages no write), the new value its write would persist
   (`value` — an opaque identity token; presence in the result means the write
   was committed), and whether processing this row encounters an error
   (`raises` — e.g. a downstream step signalling a failure). Everything else
   about the record is orthogonal (mapping.md §2). -/
structure Upd where
  changed : Bool
  value   : Int
  raises  : Bool
deriving Inhabited, DecidableEq

/- Does processing the batch encounter an error? An error can only arise while
   processing an edited row (an unedited row stages no work). Front-recursive so
   a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def anyFail : List Upd → Bool
  | []      => false
  | u :: us => (u.changed && u.raises) || anyFail us

/- The values the edited rows would stage, in batch order — what a clean run of
   the batch commits. Front-recursive (the fold pattern). -/
def changedVals : List Upd → List Int
  | []      => []
  | u :: us => (if u.changed then [u.value] else []) ++ changedVals us

/- The set of writes actually committed after the WHOLE batch is processed under
   all-or-nothing semantics: if any error is encountered anywhere in the batch,
   nothing is committed (the batch is rolled back as a unit); otherwise every
   edited row's write is committed. This is the desired behaviour — partial
   progress is never left behind when the batch fails midway. -/
def committedAtomic (us : List Upd) : List Int :=
  if anyFail us then [] else changedVals us

@[simp] lemma anyFail_nil : anyFail [] = false := rfl
@[simp] lemma changedVals_nil : changedVals [] = [] := rfl
lemma anyFail_cons (u : Upd) (us : List Upd) :
    anyFail (u :: us) = ((u.changed && u.raises) || anyFail us) := rfl
lemma changedVals_cons (u : Upd) (us : List Upd) :
    changedVals (u :: us) = (if u.changed then [u.value] else []) ++ changedVals us := rfl

/- Exposing the element at index `i` on the front of `drop i`. -/
lemma drop_cons_eq (us : List Upd) (i : Nat) (hi : i < us.length) :
    us.drop i = us[i]! :: us.drop (i + 1) := by
  have h := List.drop_eq_getElem_cons hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi, Option.getD_some]
  exact h

/- The per-row fold step for the error scan: dropping one fewer element exposes
   row `i-1` on the front, so the scan peels its error contribution. -/
lemma anyFail_drop_step (us : List Upd) (i : Nat) (hi : 0 < i) (hle : i ≤ us.length) :
    anyFail (us.drop (i - 1)) =
      ((us[i - 1]!.changed && us[i - 1]!.raises) || anyFail (us.drop i)) := by
  have hlt : i - 1 < us.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq us (i - 1) hlt, hsucc, anyFail_cons]

/- The per-row fold step for the staged values. -/
lemma changedVals_drop_step (us : List Upd) (i : Nat) (hi : 0 < i) (hle : i ≤ us.length) :
    changedVals (us.drop (i - 1)) =
      (if us[i - 1]!.changed then [us[i - 1]!.value] else []) ++ changedVals (us.drop i) := by
  have hlt : i - 1 < us.length := by omega
  have hsucc : i - 1 + 1 = i := by omega
  rw [drop_cons_eq us (i - 1) hlt, hsucc, changedVals_cons]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Process a batch of queued record updates and report which writes end up
   committed. Desired behaviour (all-or-nothing): the batch is a single unit of
   work — if processing any row raises an error, the result must commit NOTHING
   (every staged write is rolled back, so a failure midway leaves no partial
   progress); only a batch processed end-to-end without error commits its edited
   rows' writes. `updates` is read-only (not `mut`): the batch description is not
   mutated, only consulted (directive 5). -/
method processBatch (updates : List Upd) return (out : List Int)
  ensures out = committedAtomic updates
  do
    -- impl-start
    -- All staged writes accumulate in one unit of work (`staged`); `failed`
    -- records whether processing any row signalled an error escaping that unit.
    let mut staged : List Int := []
    let mut failed : Bool := false
    let mut i : Nat := updates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ updates.length
      invariant staged = changedVals (updates.drop i)
      invariant failed = anyFail (updates.drop i)
      done_with i = 0
      decreasing i
    do
      let u := updates[i - 1]!
      -- an edited row stages its write into the unit of work; a downstream step
      -- may signal a failure of the unit while processing that row.
      staged := (if u.changed then [u.value] else []) ++ staged
      failed := (u.changed && u.raises) || failed
      i := i - 1
    -- Commit point: a clean unit commits its staged writes; a failed unit
    -- commits nothing (the whole batch is rolled back as one unit of work).
    let committed : List Int := if failed then [] else staged
    return committed
    -- impl-end

prove_correct processBatch by
  loom_solve <;>
    first
    | -- loop-entry: drop updates.length = [], both folds are nil.
      (rw [List.drop_length]; simp)
    | -- loop-body step: peel row `i-1` from the staged-values fold.
      (rw [changedVals_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- loop-body step: peel row `i-1` from the error scan.
      (rw [anyFail_drop_step updates i (by omega) (by omega)]; simp_all)
    | -- exit (i = 0): `drop 0 = updates`, so the commit equals `committedAtomic`.
      (simp only [committedAtomic] at *; simp_all)
```

Prepatch bug re-encoded as an attack: `True`.

Protocol executed fully in /tmp scratch dir.

POSITIVE CONTROL: pc.lean (byte-identical to frozen Solution.lean) -> lean_verify.sh exit 0 (verifies).
PREPATCH: prepatch.lean (commit `staged` without rollback) -> exit 1, unsolved goal exactly `i_1 = true -> staged_1 = []` as refinement.md B/G-DIFF documents. Prepatch bug reproduced.

### ATTACKS (each `bash scripts/lean_verify.sh <path>`, run concurrently <=4 at a time):
- atk_1.lean (no-rollback / partial-commit, = prepatch bug re-encoded): exit 1 REJECTED (goal i_1=true -> staged_1=[]).
- atk_2.lean (ungrounded: always `changedVals updates`, never roll back): exit 1 REJECTED (goal anyFail=true -> changedVals=[]).
- atk_3.lean (inverted commit condition `if failed then staged else []`): exit 1 REJECTED.
- atk_4.lean (boundary/off-by-one: i starts at length-1, skips last row): exit 1 REJECTED.
- atk_5.lean (always []): exit 1 REJECTED (goal anyFail=false -> changedVals=[]).
- atk_6.lean (ungrounded-oracle echo `return committedAtomic updates`, trivial proof `loom_solve <;> rfl`): exit 0 VERIFIES. This is the sole verifying same-spec impl and it is behaviourally correct.
- atk_7.lean (partial-domain: returns [1] on empty batch, else committedAtomic): exit 1 REJECTED (goal False under updates=[]).
- atk_8.lean (control-flow-effect: `failed := (u.changed && u.raises)` overwrite instead of accumulate): exit 1 REJECTED.

MANDATORY RESOLVE RUN: atk_6 is the only verifying attack, so per protocol its faithful refined patch was materialized (= gold patch, since the echo refines exactly to the transaction.atomic wrap A4) and RUN through the official harness: run_resolve('django__django-16100', patch, timeout=1800, retries=1) on active benchmark swe_bench_verified (supports_docker=True) => RESOLVED=True, COMPLETED=True, note='resolved'. verify does NOT imply incorrect here: the sole verifying impl resolves. Spec NOT broken.

REFINEMENT.MD AUDIT: legs A1(R), A2(R+I), A3(R+I), A4(A-reference+I), A5(A-reference). No kind-3 (inexpressible changed-op) legs; the genuinely-changed op (atomic wrap) is modeled deeply, not hidden behind a consumed axiom. meta.json axioms==[] confirms no A-consumed legs. The load-bearing A-reference committedAtomic<->transaction.atomic is validated by axiom_check.py which runs the patch's real save loop INSIDE a real transaction.atomic(using=router.db_for_write(Row)) and asserts durable DB state == committedAtomic(batch) over 9 boundary + 2000 fuzz batches (mid-batch raise -> [], clean -> changedVals); A5 router.db_for_write checked to resolve to real alias 'default' and orthogonal to rollback. Correspondence holds. G-CONF is a genuine conf_skip (only observable is a live DB commit/rollback side effect; no DB-free R/I shadow to fuzz).

VERDICT: SOUND. >=5 distinct wrong-impl attacks (partial-domain atk_7, boundary atk_4, control-flow-effect atk_8, ungrounded-oracle atk_2/atk_5, plus prepatch bug atk_1 and inverted atk_3) run and none breaks the spec; the only verifying same-spec impl (echo) resolves under the harness. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16100/velvet. No diverging input found; the modeled function agrees with the real callee on every tested input.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean) = True via swebench_unified.markers with the Lean LanguageTables — the spec region (imports, semantics options, pure defs Upd/anyFail/changedVals/committedAtomic + fold lemmas, the processBatch signature `ensures out = committedAtomic updates`, and the prove_correct block) is byte-identical between patch and prepatch. Only the elided impl region differs. Spec view rendered and inspected.

LEAN VERIFY: scripts/lean_verify.sh Solution.lean → exit 0. processBatch proves against `ensures out = committedAtomic updates` under total-correctness (loom.semantics.termination "total", decreasing i), so a non-terminating/diverging impl cannot satisfy it.

FAITHFULNESS vs REAL REPO (the key check for spec-too-strong / drift): the spec's discriminating claim is committedAtomic us = if anyFail us then [] else changedVals us — a batch commits ALL edited-row writes iff no edited row raises, else NOTHING. The modeled callee is Django's transaction.atomic wrapping the list-editable save loop (options.py:2011-2025, base_commit c6350d59). I executed axiom_check.py against the REAL Django source (Django 4.2.dev) — it stands up a real sqlite backend with transaction support, defines a real Row model+table, and runs the actual save loop inside a real transaction.atomic(using=router.db_for_write(Row)) block over 9 boundary batches + 2000 seeded fuzz batches (seed 16100), asserting the durably-committed DB state == committedAtomic(batch) for EVERY batch. Result: 'G-AX OK ... on 2009 batches'. A mid-batch exception rolls back ALL staged writes (commit set []); a clean batch commits every edited row's write (== changedVals); router.db_for_write → 'default'.

Searched the model's full input space (Upd = changed × value × raises) for divergence and found none: (1) order preservation — changedVals batch order matches order_by('id') insertion order; (2) duplicate values (fuzz produces dupes) — multiset preserved on both sides; (3) raises on an UNEDITED row — the real loop guards all work with `if form.has_changed()`, so an unedited row never executes and cannot raise, matching anyFail counting only (changed && raises) (boundary case U(False,·,True) tested → both commit []); (4) multiple sub-writes per row (save_form/save_model/save_related) all inside the atomic block, so a later raise rolls back earlier writes — consistent with whole-batch rollback; (5) empty / no-edited-row batches → [] in both. conf_skip is justified (§C): the only observable is a live DB commit/rollback side effect with no DB-free R/I shadow to fuzz; soundness is carried by G-VERIFY + G-DIFF + G-AX, and G-AX passed against the real transaction manager.

The spec is neither too strong nor drifted: it is total-correctness (rejects diverging impls, appropriate for a finite bounded loop) and its extensional content exactly matches the real transaction.atomic behaviour on all tested inputs. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorously verified for django__django-16100/velvet. Public problem_statement already states the gold edit at full fidelity: 'Add transaction handling to Changelist list_editable processing... it should be wrapped in a transaction to prevent unexpected states in case of errors.' The gold patch is exactly wrapping the save loop in transaction.atomic(using=router.db_for_write(self.model)).

Spec-view checks:
- markers.spec_view + leakage.screen (velvet/lean flavor) run mechanically: PASSED=True, hard_failures=[]. Recorded G-LEAK status 'pass', no relaxed_leakage flag, no RELAXED_LEAKAGE.md.
- same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical between patched and prepatch; the discriminator lives only in the elided impl/proof).
- No gold-patch line reproduced (L1 clean); no patched file path 'django/contrib/admin/options.py' nor dotted module 'django.contrib.admin.options' in the spec view (L2 clean).
- No repo callee/identifier leaks: save_model, save_form, save_related, log_change, formset, has_changed, transaction.atomic, router, db_for_write, changelist_view are all ABSENT from the spec view. Only 'atomic' appears (inside the generic def committedAtomic) — subsumed by the public word 'transaction'.
- Changed symbol set = {changelist_view}; its distinctive fragment 'changelist' is already in the public problem_statement, so it is not a leak.
- No narration terms (bug/fix/patch/etc.) in spec-view comments.

The spec view describes only the desired all-or-nothing commit behavior (which a faithful spec must) using an abstract List Upd model; every fact it reveals is already public via problem_statement and none of it localizes the gold edit beyond what the task already discloses. Reference to hints_text is correctly avoided in the screen. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
