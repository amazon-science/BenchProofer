# P2 adversarial audit — django__django-15563

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,22 +50,8 @@
 
 -- impl-start
 def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
-    (rows : List (List Int)) : List (Nat × List Int) := Id.run do
-  -- Build, in one pass, the column each ancestor reads from: a shared ancestor
-  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.
-  let mut nextCol := 1
-  let mut assignment : List (Nat × Nat) := []
-  for ancestor in ancestors do
-    if sharesPrimaryKey ancestor then
-      assignment := assignment ++ [(ancestor, 0)]
-    else
-      assignment := assignment ++ [(ancestor, nextCol)]
-      nextCol := nextCol + 1
-  -- Pair each ancestor with the identifiers gathered from its dedicated column.
-  let mut result : List (Nat × List Int) := []
-  for ac in assignment do
-    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
-  return result
+    (rows : List (List Int)) : List (Nat × List Int) :=
+  ancestors.map (fun a => (a, rows.map (fun r => r.getD 0 0)))
 -- impl-end
 
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,6 @@
 -- impl-start
 def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
     (rows : List (List Int)) : List (Nat × List Int) := Id.run do
-  -- Build, in one pass, the column each ancestor reads from: a shared ancestor
-  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.
   let mut nextCol := 1
   let mut assignment : List (Nat × Nat) := []
   for ancestor in ancestors do
@@ -61,10 +59,9 @@
     else
       assignment := assignment ++ [(ancestor, nextCol)]
       nextCol := nextCol + 1
-  -- Pair each ancestor with the identifiers gathered from its dedicated column.
   let mut result : List (Nat × List Int) := []
   for ac in assignment do
-    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
+    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 999))]
   return result
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,22 +50,10 @@
 
 -- impl-start
 def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
-    (rows : List (List Int)) : List (Nat × List Int) := Id.run do
-  -- Build, in one pass, the column each ancestor reads from: a shared ancestor
-  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.
-  let mut nextCol := 1
-  let mut assignment : List (Nat × Nat) := []
-  for ancestor in ancestors do
-    if sharesPrimaryKey ancestor then
-      assignment := assignment ++ [(ancestor, 0)]
-    else
-      assignment := assignment ++ [(ancestor, nextCol)]
-      nextCol := nextCol + 1
-  -- Pair each ancestor with the identifiers gathered from its dedicated column.
-  let mut result : List (Nat × List Int) := []
-  for ac in assignment do
-    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
-  return result
+    (rows : List (List Int)) : List (Nat × List Int) :=
+  match ancestors with
+  | [] => []
+  | _  => ancestors.map (fun a => (a, rows.map (fun r => r.getD 0 0)))
 -- impl-end
 
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,6 @@
 -- impl-start
 def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
     (rows : List (List Int)) : List (Nat × List Int) := Id.run do
-  -- Build, in one pass, the column each ancestor reads from: a shared ancestor
-  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.
   let mut nextCol := 1
   let mut assignment : List (Nat × Nat) := []
   for ancestor in ancestors do
@@ -61,11 +59,10 @@
     else
       assignment := assignment ++ [(ancestor, nextCol)]
       nextCol := nextCol + 1
-  -- Pair each ancestor with the identifiers gathered from its dedicated column.
   let mut result : List (Nat × List Int) := []
   for ac in assignment do
     result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
-  return result
+  return result.reverse
 -- impl-end
 
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,20 +51,11 @@
 -- impl-start
 def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
     (rows : List (List Int)) : List (Nat × List Int) := Id.run do
-  -- Build, in one pass, the column each ancestor reads from: a shared ancestor
-  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.
   let mut nextCol := 1
-  let mut assignment : List (Nat × Nat) := []
+  let mut result : List (Nat × List Int) := []
   for ancestor in ancestors do
-    if sharesPrimaryKey ancestor then
-      assignment := assignment ++ [(ancestor, 0)]
-    else
-      assignment := assignment ++ [(ancestor, nextCol)]
-      nextCol := nextCol + 1
-  -- Pair each ancestor with the identifiers gathered from its dedicated column.
-  let mut result : List (Nat × List Int) := []
-  for ac in assignment do
-    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
+    result := result ++ [(ancestor, rows.map (fun r => r.getD nextCol 0))]
+    nextCol := nextCol + 1
   return result
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,9 +51,7 @@
 -- impl-start
 def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
     (rows : List (List Int)) : List (Nat × List Int) := Id.run do
-  -- Build, in one pass, the column each ancestor reads from: a shared ancestor
-  -- reuses column 0; each non-sharing ancestor claims the next dedicated column.
-  let mut nextCol := 1
+  let mut nextCol := 0
   let mut assignment : List (Nat × Nat) := []
   for ancestor in ancestors do
     if sharesPrimaryKey ancestor then
@@ -61,7 +59,6 @@
     else
       assignment := assignment ++ [(ancestor, nextCol)]
       nextCol := nextCol + 1
-  -- Pair each ancestor with the identifiers gathered from its dedicated column.
   let mut result : List (Nat × List Int) := []
   for ac in assignment do
     result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Targeting the right rows when an update must cascade to a model's inheritance
ancestors.

When a model inherits from several base models, a single update may have to be
propagated to one update per ancestor. The set of identifiers used to target an
ancestor's rows must be that ancestor's *own* identifiers, read from a
materialized table of identifier rows. An ancestor that shares the
model's primary key reuses the model's identifier column (column `0`); an
ancestor that does not has its own dedicated identifier column, gathered
independently. Each ancestor is then paired, in order, with the identifiers read
from the column dedicated to it.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the surrounding query machinery
-- (identifier materialization, inheritance-path inspection) is abstracted into
-- this function's inputs — the table of identifier rows and the per-ancestor
-- flag recording whether the ancestor shares the model's primary key.
-- axioms-end

-- pure-start
/-- Assign each ancestor the column of the identifier-row table that carries its
identifiers. An ancestor that shares the model's primary key (`sharesPrimaryKey`)
reuses column `0`; otherwise it is given the next dedicated column, numbered from
`next`. Front-recursive companion of the accumulating loop in the impl. -/
def columnAssignment (sharesPrimaryKey : Nat → Bool) : List Nat → Nat → List (Nat × Nat)
  | [], _ => []
  | a :: rest, next =>
      if sharesPrimaryKey a then
        (a, 0) :: columnAssignment sharesPrimaryKey rest next
      else
        (a, next) :: columnAssignment sharesPrimaryKey rest (next + 1)
-- pure-end

-- post-conditions-start
/-- Correct targeting: each ancestor is paired, in its original order, with the
identifiers read from the table column dedicated to it — column `0` when the
ancestor shares the model's primary key, otherwise its own dedicated column,
numbered consecutively from `1` across the non-sharing ancestors. -/
def problem_spec_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) (result : List (Nat × List Int)) : Prop :=
  result =
    (columnAssignment sharesPrimaryKey ancestors 1).map
      (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0)))
-- post-conditions-end

-- impl-start
def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) : List (Nat × List Int) := Id.run do
  let mut nextCol := 1
  let mut assignment : List (Nat × Nat) := []
  for ancestor in ancestors do
    if sharesPrimaryKey ancestor then
      assignment := assignment ++ [(ancestor, 0)]
    else
      assignment := assignment ++ [(ancestor, nextCol)]
      nextCol := nextCol + 1
  let mut result : List (Nat × List Int) := []
  for ac in assignment do
    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
  return result
-- impl-end

-- proof-start
/-- Closed form of loop 1's `assignment` accumulator: the first projection of the
tail-accumulating fold over `ancestors` with paired state `(assignment, nextCol)`. -/
def assignFold (sharesPrimaryKey : Nat → Bool) (ancestors : List Nat) : List (Nat × Nat) :=
  Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
    if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
    else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)

/-- Closed form of loop 2's `result` accumulator on an assignment list `L`. -/
def resultFold (rows : List (List Int)) (L : List (Nat × Nat)) : List (Nat × List Int) :=
  List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) [] L

/-- Do-notation state bridge for loop 1: the impl's `for` loop desugars to a fold over
the `MProd`-valued loop state.  Its first projection equals the first projection of the
`Prod`-valued `assignFold`-style closed form, generalized over the initial state. -/
theorem loop1_mprod (sharesPrimaryKey : Nat → Bool) :
    ∀ (L : List Nat) (init : MProd (List (Nat × Nat)) Nat),
      (forIn (m := Id) L init fun ancestor r =>
        if sharesPrimaryKey ancestor = true then
          ForInStep.yield (⟨r.fst ++ [(ancestor, 0)], r.snd⟩ : MProd (List (Nat × Nat)) Nat)
        else ForInStep.yield ⟨r.fst ++ [(ancestor, r.snd)], r.snd + 1⟩).fst
      = (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
          if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
          else (st.1 ++ [(a, st.2)], st.2 + 1)) (init.fst, init.snd) L).1 := by
  intro L
  induction L with
  | nil => intro init; rfl
  | cons a rest ih =>
      intro init
      simp only [List.forIn_cons, List.foldl_cons]
      split
      · exact ih ⟨init.fst ++ [(a, 0)], init.snd⟩
      · exact ih ⟨init.fst ++ [(a, init.snd)], init.snd + 1⟩

theorem loops_to_folds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) :
    implementation_relatedTargetIds ancestors sharesPrimaryKey rows =
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) []
        (Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
          if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
          else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)) := by
  simp only [implementation_relatedTargetIds, Id.run, bind, pure]
  simp only [List.forIn_yield_eq_foldl]
  rw [← loop1_mprod sharesPrimaryKey ancestors ⟨[], 1⟩]
  rfl

theorem foldl_assign_eq_columnAssignment_gen (sharesPrimaryKey : Nat → Bool) :
    ∀ (as : List Nat) (acc : List (Nat × Nat)) (next : Nat),
      Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
        if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
        else (st.1 ++ [(a, st.2)], st.2 + 1)) (acc, next) as)
        = acc ++ columnAssignment sharesPrimaryKey as next := by
  intro as
  induction as with
  | nil => intro acc next; simp [columnAssignment]
  | cons a rest ih =>
      intro acc next
      simp only [List.foldl_cons, columnAssignment]
      cases h : sharesPrimaryKey a with
      | true => simp only [h, if_true]; rw [ih]; simp [List.append_assoc]
      | false => simp only [h, if_false, Bool.false_eq_true]; rw [ih]; simp [List.append_assoc]

theorem foldl_assign_eq_columnAssignment (sharesPrimaryKey : Nat → Bool)
    (ancestors : List Nat) :
    Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
      if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
      else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)
      = columnAssignment sharesPrimaryKey ancestors 1 := by
  simpa using foldl_assign_eq_columnAssignment_gen sharesPrimaryKey ancestors [] 1

theorem foldl_append_singleton_eq_map (rows : List (List Int)) :
    ∀ (L : List (Nat × Nat)) (acc : List (Nat × List Int)),
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) acc L
        = acc ++ L.map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0))) := by
  intro L
  induction L with
  | nil => intro acc; simp
  | cons a rest ih =>
      intro acc
      simp only [List.foldl_cons, List.map_cons, ih, List.append_assoc, List.cons_append,
        List.nil_append]

theorem resultFold_eq_map (rows : List (List Int)) :
    ∀ (L : List (Nat × Nat)),
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) [] L
        = L.map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0))) := by
  intro L
  have h := foldl_append_singleton_eq_map rows L []
  simpa using h

theorem correct_relatedTargetIds : ∀ (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)),
    -- ancestors are distinct keys (they model an insertion-ordered key set), and
    -- every row carries exactly one column per gathered identifier (no defaulted
    -- reads): the abstracted inputs the surrounding machinery is guaranteed to
    -- supply.
    ancestors.Nodup →
    (∀ r ∈ rows, r.length = 1 + (ancestors.filter (fun a => !sharesPrimaryKey a)).length) →
    problem_spec_relatedTargetIds ancestors sharesPrimaryKey rows
      (implementation_relatedTargetIds ancestors sharesPrimaryKey rows) := by
  intro ancestors sharesPrimaryKey rows _ _
  unfold problem_spec_relatedTargetIds
  rw [loops_to_folds, resultFold_eq_map, foldl_assign_eq_columnAssignment]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-15563 (lean). SPEC SHAPE: exact-equality post-condition (problem_spec_relatedTargetIds pins result = (columnAssignment sharesPrimaryKey ancestors 1).map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0)))). meta.json: axioms=[], opaque_callees=[], deep_model_references=[] -> NO A-legs to audit; every refinement.md leg is R or I, all with faithful callee correspondence (pre_sql_setup related_ids_index/len(fields) <-> columnAssignment; get_related_updates per-ancestor pk__in <-> loop-2 pairing). G-CONF already passed 120007 differential cases; I re-read conformance_check.py and its gold_oracle transliterates the two patched functions faithfully. refinement.md audited: 9 legs, all R/I, no kind-3, no A rows -> nothing to falsify on the A axis.

SANCTIONED ATTACK SURFACE (impl-region-only, same_spec byte-identical spec regions): 6 DISTINCT wrong impls, all same_spec=True (verified via swebench_unified.markers.same_spec). Command per file: `bash scripts/lean_verify.sh <path>`.
- atk_1 (prepatch bug / control-flow-effect: reuse child-pk col 0 for every ancestor): exit 1, error 'simp made no progress' at correct_ -> does NOT close. Rejected.
- atk_2 (ungrounded-oracle echo: gold structure but r.getD ac.2 999): exit 1, 'rfl failed'. Rejected.
- atk_3 (boundary: empty-ancestors special-case then col-0-for-all): exit 1, 'simp made no progress'. Rejected.
- atk_4 (partial-domain: correct assignment then result.reverse): exit 1, 'rfl failed'. Rejected.
- atk_5 (control-flow: ignore sharesPrimaryKey, give every ancestor a dedicated column): exit 1, 'rfl failed'. Rejected.
- atk_6 (off-by-one: dedicated columns start at nextCol:=0): exit 1, 'rfl failed'. Rejected.
NONE of the 6 impl-only wrong impls closes correct_. No candidate -> no resolve needed for these (check_attack would return verifies=False). Reason: the exact-equality post-condition + the two proof-region preconditions (ancestors.Nodup; forall r in rows, r.length = 1 + #non-sharing ancestors) faithfully cover Django's realizable domain (dict-keyed related_updates => distinct keys; add_fields([pk]+extra pks) => exact row width), and on that domain the spec pins the output exactly, so any impl-region divergence is provably refuted.

POSITIVE CONTROL (pos_control.lean = exact gold impl): lean_verify exit 0; `#print axioms correct_relatedTargetIds` = [propext, Quot.sound] (clean; no sorryAx/Classical.choice). Confirmed via pos_ax.lean.

PREPATCH REPRODUCED (executed resolve): materialized the faithful prepatch/no-op patch (patch_prepatch_noop.diff -- non-empty comment-only edit that RETAINS base pre_sql_setup behavior; note: an EMPTY model_patch is SKIPPED by run_evaluation ('Instances with empty patches: 1 -> No instances to run'), so a non-empty no-op is required). `run_resolve('django__django-15563', <prepatch-noop>)` -> RESOLVED=False, COMPLETED=True, 'patch did not resolve in 3 attempts (consistent -- not flaky)'. Gold-patch positive control `run_resolve(..., <gold.diff>)` -> RESOLVED=True, COMPLETED=True ('resolved') -- confirms the Docker oracle works for this instance and the prepatch non-resolution is a real signal, not infra.

OUT-OF-SCOPE MARKER-SCOPE OBSERVATION (atk_7, reported as a note, NOT the verdict driver, NOT listed as a G-EQ attack): the correct_ theorem's preconditions live in the PROOF region, which markers._lean_spec_view fully elides (this bundle has no separate pre-conditions region). Therefore same_spec does NOT pin the preconditions. atk_7 = prepatch-bug impl (col-0-for-all) + an INJECTED unfaithful 3rd precondition in the proof region (forall a in ancestors, sharesPrimaryKey a = true), under which gold==col-0-for-all so the buggy impl closes: lean_verify exit 0, `#print axioms` = [propext] (clean), same_spec=True, and adversary.check_attack returned {same_spec:True, verifies:True, verify_completed:True} (CANDIDATE).

Its faithful patch is the same prepatch-noop.diff, which does NOT resolve (executed above). By the LITERAL mechanized _derive_audit_verdict criterion (candidate -> run_resolve not-resolved -> BROKEN) this would trip BROKEN. HOWEVER atk_7 edits the proof region, explicitly outside the audit's stated attack surface ('editing ONLY the impl region'; 'leave axioms/pure/pre/post byte-identical'). It substitutes a WEAKER OBLIGATION, not an alternative implementation, so it is NOT a valid refinement-fidelity break of THIS spec.

It is a SYSTEMIC same_spec-scope gap that would apply to EVERY lean bundle whose preconditions sit in the proof region (recommend: extend spec_view/spec_signature to pin the correct_<name> binder/precondition signature, or move preconditions into a pinned pre-conditions region). Files: atk_7.lean, atk_7_ax.lean, patch_prepatch_noop.diff, gold.diff.

VERDICT: SOUND against the G-EQ (impl-only) refinement-fidelity surface -- 6 distinct wrong impls all fail to close correct_, positive control verifies with clean axioms and its gold patch resolves, prepatch reproduced and confirmed non-resolving via executed harness. The empty A-legs leave nothing to falsify on the axiom/deep-model axis. (Filed the proof-region precondition marker gap as a systemic note for the harness owners.)

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Targeting the right rows when an update must cascade to a model's inheritance
ancestors.

When a model inherits from several base models, a single update may have to be
propagated to one update per ancestor. The set of identifiers used to target an
ancestor's rows must be that ancestor's *own* identifiers, read from a
materialized table of identifier rows. An ancestor that shares the
model's primary key reuses the model's identifier column (column `0`); an
ancestor that does not has its own dedicated identifier column, gathered
independently. Each ancestor is then paired, in order, with the identifiers read
from the column dedicated to it.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom: the surrounding query machinery
-- (identifier materialization, inheritance-path inspection) is abstracted into
-- this function's inputs — the table of identifier rows and the per-ancestor
-- flag recording whether the ancestor shares the model's primary key.
-- axioms-end

-- pure-start
/-- Assign each ancestor the column of the identifier-row table that carries its
identifiers. An ancestor that shares the model's primary key (`sharesPrimaryKey`)
reuses column `0`; otherwise it is given the next dedicated column, numbered from
`next`. Front-recursive companion of the accumulating loop in the impl. -/
def columnAssignment (sharesPrimaryKey : Nat → Bool) : List Nat → Nat → List (Nat × Nat)
  | [], _ => []
  | a :: rest, next =>
      if sharesPrimaryKey a then
        (a, 0) :: columnAssignment sharesPrimaryKey rest next
      else
        (a, next) :: columnAssignment sharesPrimaryKey rest (next + 1)
-- pure-end

-- post-conditions-start
/-- Correct targeting: each ancestor is paired, in its original order, with the
identifiers read from the table column dedicated to it — column `0` when the
ancestor shares the model's primary key, otherwise its own dedicated column,
numbered consecutively from `1` across the non-sharing ancestors. -/
def problem_spec_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) (result : List (Nat × List Int)) : Prop :=
  result =
    (columnAssignment sharesPrimaryKey ancestors 1).map
      (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0)))
-- post-conditions-end

-- impl-start
def implementation_relatedTargetIds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) : List (Nat × List Int) := Id.run do
  let mut nextCol := 1
  let mut assignment : List (Nat × Nat) := []
  for ancestor in ancestors do
    if sharesPrimaryKey ancestor then
      assignment := assignment ++ [(ancestor, 0)]
    else
      assignment := assignment ++ [(ancestor, nextCol)]
      nextCol := nextCol + 1
  let mut result : List (Nat × List Int) := []
  for ac in assignment do
    result := result ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]
  return result
-- impl-end

-- proof-start
/-- Closed form of loop 1's `assignment` accumulator: the first projection of the
tail-accumulating fold over `ancestors` with paired state `(assignment, nextCol)`. -/
def assignFold (sharesPrimaryKey : Nat → Bool) (ancestors : List Nat) : List (Nat × Nat) :=
  Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
    if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
    else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)

/-- Closed form of loop 2's `result` accumulator on an assignment list `L`. -/
def resultFold (rows : List (List Int)) (L : List (Nat × Nat)) : List (Nat × List Int) :=
  List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) [] L

/-- Do-notation state bridge for loop 1: the impl's `for` loop desugars to a fold over
the `MProd`-valued loop state.  Its first projection equals the first projection of the
`Prod`-valued `assignFold`-style closed form, generalized over the initial state. -/
theorem loop1_mprod (sharesPrimaryKey : Nat → Bool) :
    ∀ (L : List Nat) (init : MProd (List (Nat × Nat)) Nat),
      (forIn (m := Id) L init fun ancestor r =>
        if sharesPrimaryKey ancestor = true then
          ForInStep.yield (⟨r.fst ++ [(ancestor, 0)], r.snd⟩ : MProd (List (Nat × Nat)) Nat)
        else ForInStep.yield ⟨r.fst ++ [(ancestor, r.snd)], r.snd + 1⟩).fst
      = (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
          if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
          else (st.1 ++ [(a, st.2)], st.2 + 1)) (init.fst, init.snd) L).1 := by
  intro L
  induction L with
  | nil => intro init; rfl
  | cons a rest ih =>
      intro init
      simp only [List.forIn_cons, List.foldl_cons]
      split
      · exact ih ⟨init.fst ++ [(a, 0)], init.snd⟩
      · exact ih ⟨init.fst ++ [(a, init.snd)], init.snd + 1⟩

theorem loops_to_folds (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)) :
    implementation_relatedTargetIds ancestors sharesPrimaryKey rows =
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) []
        (Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
          if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
          else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)) := by
  simp only [implementation_relatedTargetIds, Id.run, bind, pure]
  simp only [List.forIn_yield_eq_foldl]
  rw [← loop1_mprod sharesPrimaryKey ancestors ⟨[], 1⟩]
  rfl

theorem foldl_assign_eq_columnAssignment_gen (sharesPrimaryKey : Nat → Bool) :
    ∀ (as : List Nat) (acc : List (Nat × Nat)) (next : Nat),
      Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
        if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
        else (st.1 ++ [(a, st.2)], st.2 + 1)) (acc, next) as)
        = acc ++ columnAssignment sharesPrimaryKey as next := by
  intro as
  induction as with
  | nil => intro acc next; simp [columnAssignment]
  | cons a rest ih =>
      intro acc next
      simp only [List.foldl_cons, columnAssignment]
      cases h : sharesPrimaryKey a with
      | true => simp only [h, if_true]; rw [ih]; simp [List.append_assoc]
      | false => simp only [h, if_false, Bool.false_eq_true]; rw [ih]; simp [List.append_assoc]

theorem foldl_assign_eq_columnAssignment (sharesPrimaryKey : Nat → Bool)
    (ancestors : List Nat) :
    Prod.fst (List.foldl (fun (st : List (Nat × Nat) × Nat) a =>
      if sharesPrimaryKey a then (st.1 ++ [(a, 0)], st.2)
      else (st.1 ++ [(a, st.2)], st.2 + 1)) ([], 1) ancestors)
      = columnAssignment sharesPrimaryKey ancestors 1 := by
  simpa using foldl_assign_eq_columnAssignment_gen sharesPrimaryKey ancestors [] 1

theorem foldl_append_singleton_eq_map (rows : List (List Int)) :
    ∀ (L : List (Nat × Nat)) (acc : List (Nat × List Int)),
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) acc L
        = acc ++ L.map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0))) := by
  intro L
  induction L with
  | nil => intro acc; simp
  | cons a rest ih =>
      intro acc
      simp only [List.foldl_cons, List.map_cons, ih, List.append_assoc, List.cons_append,
        List.nil_append]

theorem resultFold_eq_map (rows : List (List Int)) :
    ∀ (L : List (Nat × Nat)),
      List.foldl (fun acc ac => acc ++ [(ac.1, rows.map (fun r => r.getD ac.2 0))]) [] L
        = L.map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0))) := by
  intro L
  have h := foldl_append_singleton_eq_map rows L []
  simpa using h

theorem correct_relatedTargetIds : ∀ (ancestors : List Nat) (sharesPrimaryKey : Nat → Bool)
    (rows : List (List Int)),
    -- ancestors are distinct keys (they model an insertion-ordered key set), and
    -- every row carries exactly one column per gathered identifier (no defaulted
    -- reads): the abstracted inputs the surrounding machinery is guaranteed to
    -- supply.
    ancestors.Nodup →
    (∀ r ∈ rows, r.length = 1 + (ancestors.filter (fun a => !sharesPrimaryKey a)).length) →
    problem_spec_relatedTargetIds ancestors sharesPrimaryKey rows
      (implementation_relatedTargetIds ancestors sharesPrimaryKey rows) := by
  intro ancestors sharesPrimaryKey rows _ _
  unfold problem_spec_relatedTargetIds
  rw [loops_to_folds, resultFold_eq_map, foldl_assign_eq_columnAssignment]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit of django__django-15563 (lean). SPEC SHAPE: exact-equality post-condition (problem_spec_relatedTargetIds pins result = (columnAssignment sharesPrimaryKey ancestors 1).map (fun ac => (ac.1, rows.map (fun r => r.getD ac.2 0)))). meta.json: axioms=[], opaque_callees=[], deep_model_references=[] -> NO A-legs to audit; every refinement.md leg is R or I, all with faithful callee correspondence (pre_sql_setup related_ids_index/len(fields) <-> columnAssignment; get_related_updates per-ancestor pk__in <-> loop-2 pairing). G-CONF already passed 120007 differential cases; I re-read conformance_check.py and its gold_oracle transliterates the two patched functions faithfully. refinement.md audited: 9 legs, all R/I, no kind-3, no A rows -> nothing to falsify on the A axis.

SANCTIONED ATTACK SURFACE (impl-region-only, same_spec byte-identical spec regions): 6 DISTINCT wrong impls, all same_spec=True (verified via swebench_unified.markers.same_spec). Command per file: `bash scripts/lean_verify.sh <path>`.
- atk_1 (prepatch bug / control-flow-effect: reuse child-pk col 0 for every ancestor): exit 1, error 'simp made no progress' at correct_ -> does NOT close. Rejected.
- atk_2 (ungrounded-oracle echo: gold structure but r.getD ac.2 999): exit 1, 'rfl failed'. Rejected.
- atk_3 (boundary: empty-ancestors special-case then col-0-for-all): exit 1, 'simp made no progress'. Rejected.
- atk_4 (partial-domain: correct assignment then result.reverse): exit 1, 'rfl failed'. Rejected.
- atk_5 (control-flow: ignore sharesPrimaryKey, give every ancestor a dedicated column): exit 1, 'rfl failed'. Rejected.
- atk_6 (off-by-one: dedicated columns start at nextCol:=0): exit 1, 'rfl failed'. Rejected.
NONE of the 6 impl-only wrong impls closes correct_. No candidate -> no resolve needed for these (check_attack would return verifies=False). Reason: the exact-equality post-condition + the two proof-region preconditions (ancestors.Nodup; forall r in rows, r.length = 1 + #non-sharing ancestors) faithfully cover Django's realizable domain (dict-keyed related_updates => distinct keys; add_fields([pk]+extra pks) => exact row width), and on that domain the spec pins the output exactly, so any impl-region divergence is provably refuted.

POSITIVE CONTROL (pos_control.lean = exact gold impl): lean_verify exit 0; `#print axioms correct_relatedTargetIds` = [propext, Quot.sound] (clean; no sorryAx/Classical.choice). Confirmed via pos_ax.lean.

PREPATCH REPRODUCED (executed resolve): materialized the faithful prepatch/no-op patch (patch_prepatch_noop.diff -- non-empty comment-only edit that RETAINS base pre_sql_setup behavior; note: an EMPTY model_patch is SKIPPED by run_evaluation ('Instances with empty patches: 1 -> No instances to run'), so a non-empty no-op is required). `run_resolve('django__django-15563', <prepatch-noop>)` -> RESOLVED=False, COMPLETED=True, 'patch did not resolve in 3 attempts (consistent -- not flaky)'. Gold-patch positive control `run_resolve(..., <gold.diff>)` -> RESOLVED=True, COMPLETED=True ('resolved') -- confirms the Docker oracle works for this instance and the prepatch non-resolution is a real signal, not infra.

OUT-OF-SCOPE MARKER-SCOPE OBSERVATION (atk_7, reported as a note, NOT the verdict driver, NOT listed as a G-EQ attack): the correct_ theorem's preconditions live in the PROOF region, which markers._lean_spec_view fully elides (this bundle has no separate pre-conditions region). Therefore same_spec does NOT pin the preconditions. atk_7 = prepatch-bug impl (col-0-for-all) + an INJECTED unfaithful 3rd precondition in the proof region (forall a in ancestors, sharesPrimaryKey a = true), under which gold==col-0-for-all so the buggy impl closes: lean_verify exit 0, `#print axioms` = [propext] (clean), same_spec=True, and adversary.check_attack returned {same_spec:True, verifies:True, verify_completed:True} (CANDIDATE).

Its faithful patch is the same prepatch-noop.diff, which does NOT resolve (executed above). By the LITERAL mechanized _derive_audit_verdict criterion (candidate -> run_resolve not-resolved -> BROKEN) this would trip BROKEN. HOWEVER atk_7 edits the proof region, explicitly outside the audit's stated attack surface ('editing ONLY the impl region'; 'leave axioms/pure/pre/post byte-identical'). It substitutes a WEAKER OBLIGATION, not an alternative implementation, so it is NOT a valid refinement-fidelity break of THIS spec.

It is a SYSTEMIC same_spec-scope gap that would apply to EVERY lean bundle whose preconditions sit in the proof region (recommend: extend spec_view/spec_signature to pin the correct_<name> binder/precondition signature, or move preconditions into a pinned pre-conditions region). Files: atk_7.lean, atk_7_ax.lean, patch_prepatch_noop.diff, gold.diff.

VERDICT: SOUND against the G-EQ (impl-only) refinement-fidelity surface -- 6 distinct wrong impls all fail to close correct_, positive control verifies with clean axioms and its gold patch resolves, prepatch reproduced and confirmed non-resolving via executed harness. The empty A-legs leave nothing to falsify on the axiom/deep-model axis. (Filed the proof-region precondition marker gap as a systemic note for the harness owners.)

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-15563 (lean) failed; the spec faithfully models the real callees at base_commit 9ffd4eae2c.

Mechanical checks:
- scripts/lean_verify.sh Solution.lean: exit 0 (only deprecation/unusedSimpArgs warnings; no error/sorry).
- #print axioms correct_relatedTargetIds = [propext, Quot.sound] — no sorryAx, no Classical.choice; proof is genuine.
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, LeanBackend.language) = True (spec region byte-identical).
- conformance_check.py: pass, 120007 cases, seed 15563.

Faithfulness analysis vs the gold patch (compiler.py pre_sql_setup + subqueries.py get_related_updates):
- The model abstracts the query machinery (add_fields, execute_sql(MULTI), get_path_to_parent, add_filter) into inputs ancestors:List Nat, sharesPrimaryKey:Nat->Bool, rows:List(List Int). Provenance in mapping.md is accurate: related_updates is an insertion-ordered dict keyed by distinct ancestor models; get_related_updates iterates it in the same order the gathering loop uses.
- columnAssignment sharesPrimaryKey ancestors 1 exactly reproduces gold's related_ids_index: fields=[pk] (col 0), sharing ancestor -> (related,0), non-sharing -> (related,len(fields)) then fields.append -> dedicated columns 1,2,... in encounter order. r.getD ac.2 0 corresponds to r[index].
- The two correct_ preconditions are facts the real callees guarantee, not spec-weakening cheats: Nodup follows from dict keys being distinct models; row width = 1 + #non-sharing follows from the add_fields([pk] + one pk per non-sharing ancestor) select layout. Because valid rows are exactly this width, the getD default (0) is never reached for any assigned column index, so getD never fabricates behavior on realizable inputs.

Independent adversarial cross-check: I transliterated the ACTUAL gold patch lines (fields/related_ids_index/defaultdict/get_related_updates), not the bundled shadow, and diffed against the Lean model over 300000 random precondition-satisfying inputs (n_anc 0..6, distinct keys, both sharesPrimaryKey values, matching row widths) — zero divergences. No input found where the modeled function disagrees with the real callee.

The spec is an exact equality that pins output on the full Django precondition domain; it is neither too strong (preconditions only exclude malformed inputs the machinery never produces) nor drifting from repo behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean, lean flavor) reviewed against the public problem_statement (NOT hints_text). Mechanical leakage.screen() passes clean (no hard failures). Manual review confirms:

- No gold-patch lines reproduced, no diff markers, no patched file/module paths (compiler.py, subqueries.py, dotted paths all absent).
- No patched repo symbols leaked: pre_sql_setup, get_related_updates, related_ids, related_ids_index, add_fields, add_filter, get_path_to_parent, parent_link, defaultdict do NOT appear in spec-view identifiers or comments. Lean symbols (columnAssignment, sharesPrimaryKey, ancestors, rows, result) are abstract modeling names.
- No bug/fix narration in prose; the docstrings describe CORRECT behavior (each ancestor targeted by its own identifiers, shared-PK ancestor reuses column 0), never the defect or the edit.
- Hints_text (which discloses the concrete mechanism: related_ids dict[Model,list[int]], parent_link, add_filter('pk__in', self.related_ids[model])) does NOT bleed into the spec view.
- 'primary key' is already public in problem_statement ('query is using primiary keys from Base class'). The postcondition encodes the correct-behavior contract, which any faithful spec must; it does not reveal the repo-level edit location or the dict-keyed-by-model mechanism.

Specifying correct behavior != leaking the gold edit. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.