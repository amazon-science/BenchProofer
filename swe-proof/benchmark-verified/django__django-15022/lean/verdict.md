# P2 adversarial audit — django__django-15022

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_2b.lean`, `atk_5b.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
terms=[1,2], one parent {id=0, rows=[{matched=[1]},{matched=[2]}]}. Gold spec = parents.filter(combinedMatch [1,2]) yields [] because no single row matches BOTH words (combinedMatch=false). The prepatch/∀word∃row impl yields [p] (word 1 matched by row0, word 2 by row1). Verified in cex.lean (exit 0): the gold filter = [] and the ∀word∃row filter = [p]. This is the (∀word ∃row) vs (∃row ∀word) quantifier-swap fix (F2P test_related_field_multiple_search_terms 'danielle 19' -> count()==0).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,10 @@
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
     List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
+  let mut qs := parents
   for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    qs := qs.filter (fun p => p.rows.any (fun r => r.matched.contains t))
+  return qs
 -- impl-end
 
 -- proof-start
@@ -84,20 +81,8 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
-  unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  unfold problem_spec_searchFilter implementation_searchFilter combinedMatch
+  cases terms with
+  | nil => simp
+  | cons t ts => rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,8 @@
 
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
-    List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
-  for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    List Parent :=
+  parents.filter (fun p => terms.all (fun t => p.rows.any (fun r => r.matched.contains t)))
 -- impl-end
 
 -- proof-start
@@ -84,20 +78,9 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
   unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  first
+  | rfl
+  | (simp_all [combinedMatch, rowMatchesAll])
+  | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,8 @@
 
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
-    List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
-  for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    List Parent :=
+  parents.filter (fun p => p.rows.any (fun r => terms.any (fun t => r.matched.contains t)))
 -- impl-end
 
 -- proof-start
@@ -84,20 +78,9 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
   unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  first
+  | rfl
+  | (simp_all [combinedMatch, rowMatchesAll])
+  | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,10 @@
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
     List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
   let mut termQueries : List Nat := []
   for t in terms do
     termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+  return parents.filter (fun p => combinedMatch termQueries.dropLast p)
 -- impl-end
 
 -- proof-start
@@ -84,20 +81,9 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
   unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  first
+  | rfl
+  | (simp_all [combinedMatch, rowMatchesAll])
+  | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,8 @@
 
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
-    List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
-  for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    List Parent :=
+  parents.filter (fun p => p.rows.all (fun r => rowMatchesAll terms r))
 -- impl-end
 
 -- proof-start
@@ -84,20 +78,9 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
   unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  first
+  | rfl
+  | (simp_all [combinedMatch, rowMatchesAll])
+  | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,10 @@
 
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
-    List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
-  for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    List Parent :=
+  match terms with
+  | []     => []
+  | _ :: _ => parents.filter (fun p => combinedMatch terms p)
 -- impl-end
 
 -- proof-start
@@ -84,20 +80,9 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
   unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  first
+  | rfl
+  | (simp_all [combinedMatch, rowMatchesAll])
+  | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,8 @@
 
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
-    List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
-  for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    List Parent :=
+  parents.filter (fun p => combinedMatch (0 :: terms) p)
 -- impl-end
 
 -- proof-start
@@ -84,20 +78,9 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
   unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  first
+  | rfl
+  | (simp_all [combinedMatch, rowMatchesAll])
+  | decide
 -- proof-end
```

Attack 8 — `atk_2b.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,8 @@
 
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
-    List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
-  for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    List Parent :=
+  parents.filter (fun p => terms.all (fun t => p.rows.any (fun r => r.matched.contains t)))
 -- impl-end
 
 -- proof-start
@@ -84,20 +78,8 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
-  unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  unfold problem_spec_searchFilter implementation_searchFilter combinedMatch rowMatchesAll
+  ext p
+  simp_all [List.mem_filter]
+  aesop
 -- proof-end
```

Attack 9 — `atk_5b.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,14 +68,8 @@
 
 -- impl-start
 def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
-    List Parent := Id.run do
-  -- Accumulate the per-word queries, then apply ONE combined filter (a single
-  -- join), so the surviving records are those a single related row satisfies
-  -- across the whole query.
-  let mut termQueries : List Nat := []
-  for t in terms do
-    termQueries := termQueries ++ [t]
-  return parents.filter (fun p => combinedMatch termQueries p)
+    List Parent :=
+  parents.filter (fun p => p.rows.all (fun r => rowMatchesAll terms r))
 -- impl-end
 
 -- proof-start
@@ -84,20 +78,7 @@
       problem_spec_searchFilter terms parents
         (implementation_searchFilter terms parents) := by
   intro terms parents
-  have helper : ∀ (xs : List Nat) (init : List Nat),
-      (forIn (m := Id) xs init
-        (fun t r => pure (ForInStep.yield (r ++ [t])))) = init ++ xs := by
-    intro xs
-    induction xs with
-    | nil => intro init; simp [List.forIn_nil, pure, List.append_nil]
-    | cons a as ih =>
-      intro init
-      rw [List.forIn_cons]
-      simp only [bind, pure] at ih ⊢
-      rw [ih]
-      simp
-  unfold problem_spec_searchFilter implementation_searchFilter
-  simp only [Id.run, bind]
-  rw [helper, List.nil_append]
-  rfl
+  unfold problem_spec_searchFilter implementation_searchFilter combinedMatch
+  ext p
+  cases terms <;> simp_all [rowMatchesAll] <;> aesop
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Narrowing a collection of records by a multi-word search query.

Each record reaches a set of related rows (through its multi-valued relations).
For one related row and one processed search word, the row either matches that
word or it does not (matching is the standard per-field test, abstracted here to
a per-row set of matched words). The search query is the list of processed words.

The desired behaviour, stated as an input→output relation: the narrowed
collection keeps a record exactly when a SINGLE one of its related rows matches
EVERY word of the query simultaneously. (When the query carries no words the
collection is returned unchanged.) Equivalently, the existential over related
rows sits inside the universal over words: one related row must account for the
whole query, not a different row per word.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behaviour is modeled
-- deeply with concrete operations over the per-(row, word) match matrix. The
-- word-splitting, per-field text comparison, and OR-over-fields combination are
-- unchanged here and are folded into the inputs (the processed word list and
-- each row's matched-word set), so no callee property is consumed by the proof.
-- axioms-end

-- pure-start
/-- One related row reachable from a record. `matched` is the set of processed
search words this row satisfies (under the OR over the configured search
fields). Words are carried as opaque ids: equal words have equal ids. -/
structure Row where
  matched : List Nat
deriving DecidableEq, Repr

/-- A record under consideration, identified by `id`, together with the related
rows it reaches through its multi-valued relations. -/
structure Parent where
  id : Nat
  rows : List Row
deriving DecidableEq, Repr

/-- A single related row matches the whole accumulated query when it matches
every word in it. -/
def rowMatchesAll (tqs : List Nat) (r : Row) : Bool :=
  tqs.all (fun t => r.matched.contains t)

/-- Whether a record is kept by the combined query `tqs`: with no words the
query is a no-op (every record is kept); otherwise the record is kept exactly
when ONE of its related rows matches every word. -/
def combinedMatch (tqs : List Nat) (p : Parent) : Bool :=
  match tqs with
  | []     => true
  | _ :: _ => p.rows.any (fun r => rowMatchesAll tqs r)
-- pure-end

-- post-conditions-start
/-- The narrowed collection is the input collection restricted to the records
the combined query keeps: order preserved, each record kept at most once, and a
record present exactly when a single related row matches every search word. -/
def problem_spec_searchFilter (terms : List Nat) (parents : List Parent)
    (result : List Parent) : Prop :=
  result = parents.filter (fun p => combinedMatch terms p)
-- post-conditions-end

-- impl-start
def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
    List Parent :=
  parents.filter (fun p => combinedMatch terms p)
-- impl-end

-- proof-start
theorem correct_searchFilter :
    ∀ (terms : List Nat) (parents : List Parent),
      problem_spec_searchFilter terms parents
        (implementation_searchFilter terms parents) := by
  intro terms parents
  unfold problem_spec_searchFilter implementation_searchFilter
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is an EXACT extensional equality: problem_spec_searchFilter terms parents result := result = parents.filter (fun p => combinedMatch terms p). Any impl whose correct_searchFilter closes is thereby forced extensionally IDENTICAL to the gold total function on every input, so no closing impl can correspond to a non-resolving patch.

Protocol executed:

Attack files (impl region varied only; axioms/pure/pre/post byte-identical => same_spec=True confirmed for ALL 9 via swebench_unified.markers.same_spec with get_backend('lean')):
- atk_1: prepatch ∀word∃row per-word filter loop + carried gold prepatch proof (cases terms; rfl). cmd: bash scripts/lean_verify.sh atk_1.lean -> EXIT=1 (does not close).  [prepatch bug re-encoded]
- atk_2: parents.filter (terms.all (rows.any (contains))) — quantifier swapped, direct form. EXIT=1.
- atk_2b: same impl, aggressive proof (ext/simp_all/aesop). EXIT=1.
- atk_3: boundary — rows.any (terms.ANY matched) instead of all. EXIT=1.
- atk_4: control-flow-effect — accumulate termQueries then combinedMatch termQueries.dropLast (drops last word). EXIT=1.
- atk_5: rows.ALL (rowMatchesAll) — every related row must match. EXIT=1.
- atk_5b: same impl, aggressive proof. EXIT=1.
- atk_6: partial-domain — empty terms returns [] (spec keeps all). EXIT=1.
- atk_7: ungrounded-oracle echo — combinedMatch (0 :: terms) (spurious extra word). EXIT=1.
Best-effort tactic ladder used on the non-prepatch attacks: unfold; first | rfl | simp_all[combinedMatch,rowMatchesAll] | decide; plus hardened ext/aesop variants (2b,5b). None closed.

Positive control: atk_pos = parents.filter (fun p => combinedMatch terms p), proof unfold; rfl. cmd: bash scripts/lean_verify.sh atk_pos.lean -> EXIT=0. #print axioms correct_searchFilter (pos_axioms.lean) => "'correct_searchFilter' does not depend on any axioms" (clean, no sorryAx). It is extensionally identical to gold (same post-patch ∃row∀word narrowing), so no break.

Counterexample proof cex.lean -> EXIT=0: proves gold filter = [] and the ∀word∃row filter = [p] on the discriminating input, i.e. the spec ACTIVELY REJECTS the prepatch behaviour.

Because NO wrong impl produced a closing clean-axiom proof, there was no candidate whose faithful refined patch needed to be materialized and run through run_resolve — the BROKEN precondition (a closing clean-axiom impl with a non-resolving patch) was never met. patches={} accordingly.

refinement.md audit: axioms region is EMPTY (verbatim byte-identical in all attacks); the changed quantifier structure is modeled DEEPLY with concrete Lean ops (List.filter of rows.any of terms.all). All three legs in the correspondence table are tagged R (accumulator, per-bit loop, single combined filter); helpers combinedMatch/rowMatchesAll are I (shared pure region). No kind-3 (unjustified) legs; no A-consumed / A-reference legs to exploit (G-AX is a legitimate skip stub since no unchanged callee contract is consumed — smart_split/unescape/construct_search/models.Q per-row match are correctly folded into inputs terms/Row.matched, as the surviving-instance observable depends only on the per-(row,word) match matrix, not their internals). Correspondence to real callees holds: single combined queryset.filter(models.Q(*term_queries)) over one join alias set <-> parents.filter(rows.any(terms.all)).

Parallelism: verifications launched as background Bash jobs in two batches of 4 (atk_1..4, then atk_5..7+pos), collected via wait; hardened attempts (2b,5b) in a third concurrent batch. Every attack fully verified and reported.

Conclusion: >=9 distinct same-spec wrong impls attacked (partial-domain atk_6, boundary atk_3, control-flow-effect atk_4, ungrounded-oracle echo atk_7, quantifier-swap atk_2/2b, rows.all atk_5/5b, prepatch atk_1); none closes. Verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_2b.lean`, `atk_5b.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
terms=[1,2], one parent {id=0, rows=[{matched=[1]},{matched=[2]}]}. Gold spec = parents.filter(combinedMatch [1,2]) yields [] because no single row matches BOTH words (combinedMatch=false). The prepatch/∀word∃row impl yields [p] (word 1 matched by row0, word 2 by row1). Verified in cex.lean (exit 0): the gold filter = [] and the ∀word∃row filter = [p]. This is the (∀word ∃row) vs (∃row ∀word) quantifier-swap fix (F2P test_related_field_multiple_search_terms 'danielle 19' -> count()==0).
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

Attack 8 — `atk_2b.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_5b.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Narrowing a collection of records by a multi-word search query.

Each record reaches a set of related rows (through its multi-valued relations).
For one related row and one processed search word, the row either matches that
word or it does not (matching is the standard per-field test, abstracted here to
a per-row set of matched words). The search query is the list of processed words.

The desired behaviour, stated as an input→output relation: the narrowed
collection keeps a record exactly when a SINGLE one of its related rows matches
EVERY word of the query simultaneously. (When the query carries no words the
collection is returned unchanged.) Equivalently, the existential over related
rows sits inside the universal over words: one related row must account for the
whole query, not a different row per word.

This is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the behaviour is modeled
-- deeply with concrete operations over the per-(row, word) match matrix. The
-- word-splitting, per-field text comparison, and OR-over-fields combination are
-- unchanged here and are folded into the inputs (the processed word list and
-- each row's matched-word set), so no callee property is consumed by the proof.
-- axioms-end

-- pure-start
/-- One related row reachable from a record. `matched` is the set of processed
search words this row satisfies (under the OR over the configured search
fields). Words are carried as opaque ids: equal words have equal ids. -/
structure Row where
  matched : List Nat
deriving DecidableEq, Repr

/-- A record under consideration, identified by `id`, together with the related
rows it reaches through its multi-valued relations. -/
structure Parent where
  id : Nat
  rows : List Row
deriving DecidableEq, Repr

/-- A single related row matches the whole accumulated query when it matches
every word in it. -/
def rowMatchesAll (tqs : List Nat) (r : Row) : Bool :=
  tqs.all (fun t => r.matched.contains t)

/-- Whether a record is kept by the combined query `tqs`: with no words the
query is a no-op (every record is kept); otherwise the record is kept exactly
when ONE of its related rows matches every word. -/
def combinedMatch (tqs : List Nat) (p : Parent) : Bool :=
  match tqs with
  | []     => true
  | _ :: _ => p.rows.any (fun r => rowMatchesAll tqs r)
-- pure-end

-- post-conditions-start
/-- The narrowed collection is the input collection restricted to the records
the combined query keeps: order preserved, each record kept at most once, and a
record present exactly when a single related row matches every search word. -/
def problem_spec_searchFilter (terms : List Nat) (parents : List Parent)
    (result : List Parent) : Prop :=
  result = parents.filter (fun p => combinedMatch terms p)
-- post-conditions-end

-- impl-start
def implementation_searchFilter (terms : List Nat) (parents : List Parent) :
    List Parent :=
  parents.filter (fun p => combinedMatch terms p)
-- impl-end

-- proof-start
theorem correct_searchFilter :
    ∀ (terms : List Nat) (parents : List Parent),
      problem_spec_searchFilter terms parents
        (implementation_searchFilter terms parents) := by
  intro terms parents
  unfold problem_spec_searchFilter implementation_searchFilter
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec is an EXACT extensional equality: problem_spec_searchFilter terms parents result := result = parents.filter (fun p => combinedMatch terms p). Any impl whose correct_searchFilter closes is thereby forced extensionally IDENTICAL to the gold total function on every input, so no closing impl can correspond to a non-resolving patch.

Protocol executed:

Attack files (impl region varied only; axioms/pure/pre/post byte-identical => same_spec=True confirmed for ALL 9 via swebench_unified.markers.same_spec with get_backend('lean')):
- atk_1: prepatch ∀word∃row per-word filter loop + carried gold prepatch proof (cases terms; rfl). cmd: bash scripts/lean_verify.sh atk_1.lean -> EXIT=1 (does not close).  [prepatch bug re-encoded]
- atk_2: parents.filter (terms.all (rows.any (contains))) — quantifier swapped, direct form. EXIT=1.
- atk_2b: same impl, aggressive proof (ext/simp_all/aesop). EXIT=1.
- atk_3: boundary — rows.any (terms.ANY matched) instead of all. EXIT=1.
- atk_4: control-flow-effect — accumulate termQueries then combinedMatch termQueries.dropLast (drops last word). EXIT=1.
- atk_5: rows.ALL (rowMatchesAll) — every related row must match. EXIT=1.
- atk_5b: same impl, aggressive proof. EXIT=1.
- atk_6: partial-domain — empty terms returns [] (spec keeps all). EXIT=1.
- atk_7: ungrounded-oracle echo — combinedMatch (0 :: terms) (spurious extra word). EXIT=1.
Best-effort tactic ladder used on the non-prepatch attacks: unfold; first | rfl | simp_all[combinedMatch,rowMatchesAll] | decide; plus hardened ext/aesop variants (2b,5b). None closed.

Positive control: atk_pos = parents.filter (fun p => combinedMatch terms p), proof unfold; rfl. cmd: bash scripts/lean_verify.sh atk_pos.lean -> EXIT=0. #print axioms correct_searchFilter (pos_axioms.lean) => "'correct_searchFilter' does not depend on any axioms" (clean, no sorryAx). It is extensionally identical to gold (same post-patch ∃row∀word narrowing), so no break.

Counterexample proof cex.lean -> EXIT=0: proves gold filter = [] and the ∀word∃row filter = [p] on the discriminating input, i.e. the spec ACTIVELY REJECTS the prepatch behaviour.

Because NO wrong impl produced a closing clean-axiom proof, there was no candidate whose faithful refined patch needed to be materialized and run through run_resolve — the BROKEN precondition (a closing clean-axiom impl with a non-resolving patch) was never met. patches={} accordingly.

refinement.md audit: axioms region is EMPTY (verbatim byte-identical in all attacks); the changed quantifier structure is modeled DEEPLY with concrete Lean ops (List.filter of rows.any of terms.all). All three legs in the correspondence table are tagged R (accumulator, per-bit loop, single combined filter); helpers combinedMatch/rowMatchesAll are I (shared pure region). No kind-3 (unjustified) legs; no A-consumed / A-reference legs to exploit (G-AX is a legitimate skip stub since no unchanged callee contract is consumed — smart_split/unescape/construct_search/models.Q per-row match are correctly folded into inputs terms/Row.matched, as the surviving-instance observable depends only on the per-(row,word) match matrix, not their internals). Correspondence to real callees holds: single combined queryset.filter(models.Q(*term_queries)) over one join alias set <-> parents.filter(rows.any(terms.all)).

Parallelism: verifications launched as background Bash jobs in two batches of 4 (atk_1..4, then atk_5..7+pos), collected via wait; hardened attempts (2b,5b) in a third concurrent batch. Every attack fully verified and reported.

Conclusion: >=9 distinct same-spec wrong impls attacked (partial-domain atk_6, boundary atk_3, control-flow-effect atk_4, ungrounded-oracle echo atk_7, quantifier-swap atk_2/2b, rows.all atk_5/5b, prepatch atk_1); none closes. Verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. (1) same_spec(Solution, Solution_prepatch, lean_tables)=True; spec region (problem_spec_searchFilter/combinedMatch/rowMatchesAll) byte-identical. (2) Solution.lean compiles exit 0; #print axioms correct_searchFilter = [propext, Quot.sound] — no sorryAx/native_decide, proof is genuine. Ran the bundle's conformance_check.py against the REAL patched Django (worktree @ base_commit e1d673c, patch.diff applied → confirmed single combined queryset.filter(models.Q(*term_queries))): 15,007 randomized+edge checks, 0 disagreements at the declared membership observable. (4) Reproduced both F2P discriminators on real Django: 'danielle 19'→membership 0, 'daniel 19'→membership 1, matching spec's ∃row∀word. (5) Adversarial abstraction-boundary probe: a parent with two children both matching yields real get_search_results raw_count=2 but distinct/membership=1 — the spec models MEMBERSHIP (List.filter keeps each parent once), which is exactly the instance-identity/.count()-with-distinct observable mapping.md declares and the F2P tests assert (may_have_duplicates=True → changelist applies .distinct()). may_have_duplicates is legitimately framed out. The empty-query no-op (combinedMatch []=true ↦ models.Q() match-all) and order-preserving single-keep filter also match. The spec is neither too strong nor drifting; the R/I abstraction (word-splitting/OR-of-lookups/icontains folded into terms & Row.matched, all unchanged by the patch) is sound and documented.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (imports/docstring + axioms + pure + post-conditions) verified rendered via markers.spec_view with the lean backend tables; impl and proof regions are correctly elided to 'implementation elided' / 'proof elided'. same_spec(Solution, Solution_prepatch, lean)=True, so the spec region is frozen/byte-identical.

What the visible spec view discloses: only the abstract input->output relation over abstracted Row/Parent/matched-word-set types — a record is kept iff a SINGLE related row matches EVERY query word (exists-row forall-word), and empty query is a no-op. It states this in domain-neutral vocabulary; there is NO Django/gold-patch token: no `term_queries`, no `models.Q(*...)`, no `queryset.filter`, no JOIN/alias mechanics, no reference to the loop-accumulation refactor.

Comparison to public problem_statement: the public statement ALREADY openly names both the bug and the fix direction — 'each word in the search query leads to additional JOIN in final SQL query because of qs = qs.filter(...) pattern' and 'The attached patch ... fixes it'. Stating the corrected input->output relation (the quantifier the fix restores) is the spec's proper job and does not disclose the gold edit beyond what the public statement already broadcasts.

The one genuinely leaky line — the impl comment 'Accumulate the per-word queries, then apply ONE combined filter (a single join)' plus the `termQueries` accumulator — lives entirely inside the impl-start region, which spec_view elides; it is NOT in the audited spec view. Reconstructing the actual gold diff (term_queries.append + models.Q(*term_queries)) still requires independent Django QuerySet/Q knowledge not present in the spec view. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
