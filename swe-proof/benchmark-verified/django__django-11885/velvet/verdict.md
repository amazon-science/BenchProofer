# P2 adversarial audit — django__django-11885

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -129,23 +129,18 @@
     let mut i := 0
     while i < relations.length
       invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
+      invariant result = (relations.take i).map (fun e => (e.1, [e.2]))
       done_with i = relations.length
-      decreasing relations.length - i
     do
       let e := relations[i]!
-      result := combineInto result e.1 e.2
+      result := result ++ [(e.1, [e.2])]
       i := i + 1
     return result
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    (try (rename_i i _ hi; have hii : i < relations.length := by omega;
+          simp_all [combineStep, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hii])) <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -125,27 +125,13 @@
   ensures (out.map Prod.fst).Nodup
   do
     -- impl-start
-    let mut result : List TableGroup := []
-    let mut i := 0
-    while i < relations.length
-      invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
-      done_with i = relations.length
-      decreasing relations.length - i
-    do
-      let e := relations[i]!
-      result := combineInto result e.1 e.2
-      i := i + 1
+    let result : List TableGroup := []
     return result
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    (try (rename_i i _ hi; have hii : i < relations.length := by omega;
+          simp_all [combineStep, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hii])) <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -129,23 +129,17 @@
     let mut i := 0
     while i < relations.length
       invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
       done_with i = relations.length
-      decreasing relations.length - i
     do
       let e := relations[i]!
-      result := combineInto result e.1 e.2
+      result := combineInto result e.2 e.1
       i := i + 1
     return result
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    (try (rename_i i _ hi; have hii : i < relations.length := by omega;
+          simp_all [combineStep, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hii])) <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -126,12 +126,10 @@
   do
     -- impl-start
     let mut result : List TableGroup := []
-    let mut i := 0
+    let mut i := 1
     while i < relations.length
-      invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
-      done_with i = relations.length
-      decreasing relations.length - i
+      invariant i ≤ relations.length + 1
+      done_with i ≥ relations.length
     do
       let e := relations[i]!
       result := combineInto result e.1 e.2
@@ -140,12 +138,8 @@
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    (try (rename_i i _ hi; have hii : i < relations.length := by omega;
+          simp_all [combineStep, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hii])) <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -129,23 +129,20 @@
     let mut i := 0
     while i < relations.length
       invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
       done_with i = relations.length
-      decreasing relations.length - i
     do
       let e := relations[i]!
-      result := combineInto result e.1 e.2
+      if e.1 ∈ result.map Prod.fst then
+        result := result
+      else
+        result := result ++ [(e.1, [e.2])]
       i := i + 1
     return result
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    (try (rename_i i _ hi; have hii : i < relations.length := by omega;
+          simp_all [combineStep, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hii])) <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -125,27 +125,13 @@
   ensures (out.map Prod.fst).Nodup
   do
     -- impl-start
-    let mut result : List TableGroup := []
-    let mut i := 0
-    while i < relations.length
-      invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
-      done_with i = relations.length
-      decreasing relations.length - i
-    do
-      let e := relations[i]!
-      result := combineInto result e.1 e.2
-      i := i + 1
+    let result : List TableGroup := relations.reverse.foldl combineStep []
     return result
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    (try (rename_i i _ hi; have hii : i < relations.length := by omega;
+          simp_all [combineStep, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hii])) <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -129,23 +129,17 @@
     let mut i := 0
     while i < relations.length
       invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
       done_with i = relations.length
-      decreasing relations.length - i
     do
       let e := relations[i]!
-      result := combineInto result e.1 e.2
+      result := (e.1, [e.2]) :: result
       i := i + 1
     return result
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    (try (rename_i i _ hi; have hii : i < relations.length := by omega;
+          simp_all [combineStep, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hii])) <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- (No consumed callee contracts. The producer of candidate relations is an
@@ -125,27 +125,11 @@
   ensures (out.map Prod.fst).Nodup
   do
     -- impl-start
-    let mut result : List TableGroup := []
-    let mut i := 0
-    while i < relations.length
-      invariant i ≤ relations.length
-      invariant result = (relations.take i).foldl combineStep []
-      done_with i = relations.length
-      decreasing relations.length - i
-    do
-      let e := relations[i]!
-      result := combineInto result e.1 e.2
-      i := i + 1
+    let result :| ((result : List TableGroup).map Prod.fst).Nodup
     return result
     -- impl-end
 
 prove_correct combineByTable by
-  loom_solve
-  case «invariant_2: result = (relations.take i).foldl combineStep []» =>
-    have hi : i < relations.length := by omega
-    rw [invariant_2, combined_take_step relations i hi, combineStep,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  case «ensures_1: (out.map Prod.fst).Nodup» =>
-    have h := combined_nodup relations
-    simp_all [combined]
-  all_goals simp_all [combined]
+  loom_solve <;>
+    simp_all [combined, combineStep, combineInto, combined_nodup] <;>
+    (try omega) <;> (try grind) <;> (try aesop)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The producer of candidate relations is an
--  unchanged enumerator whose only relevant effect is the SEQUENCE of
--  (table, column) relations it yields; that sequence is the read-only input
--  `relations` here. The combining transformation under spec is modeled DEEPLY
--  below — every observable is computed from `relations`, nothing is borrowed
--  from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- One candidate relation feeding the fast-delete pass: a target table (`fst`)
   paired with the single column (`snd`) on that table that references the rows
   being deleted. Tables and columns are carried by stable integer identities. -/
abbrev Relation := Int × Int

/- One combined fast-delete group: a target table (`fst`) paired with the list
   of columns (`snd`) on that table to be matched, in first-encounter order. A
   single group is emitted as ONE query of the shape "delete the rows of this
   table where any of these columns matches". -/
abbrev TableGroup := Int × List Int

/- Insertion-ordered grouping: record that column `f` of table `m` must be
   matched.
   - a table never seen before is appended at the end, keeping the order in
     which tables were first encountered, carrying just `[f]`;
   - a table already present keeps its original position and APPENDS `f` to its
     column list (so all columns of one table accumulate into one group).
   This is the exact semantics of `groups[m].append(f)` on an order-preserving
   table→columns mapping then reading it back in table order. -/
def combineInto (gs : List TableGroup) (m : Int) (f : Int) : List TableGroup :=
  match gs with
  | []            => [(m, [f])]
  | (m', fs') :: r => if m' = m then (m, fs' ++ [f]) :: r else (m', fs') :: combineInto r m f

/- Fold one relation into the accumulating grouping. -/
def combineStep (gs : List TableGroup) (e : Relation) : List TableGroup := combineInto gs e.1 e.2

/- The combined fast-delete plan built from a whole sequence of candidate
   relations: each relation is grouped under its table; the plan is that mapping
   read out in table order. Net effect: every distinct table appears EXACTLY
   ONCE (one combined query per table), in first-encounter order, carrying every
   column that referenced it — so N relations on the same table collapse to a
   single group instead of N separate ones. -/
def combined (relations : List Relation) : List TableGroup := relations.foldl combineStep []

/- Tables of a grouping step: an already-present table leaves the table list
   unchanged; a fresh table is appended. (The column accumulation does not touch
   the key projection.) -/
@[grind] lemma keys_combineInto (gs : List TableGroup) (m f : Int) :
    (combineInto gs m f).map Prod.fst
      = if m ∈ gs.map Prod.fst then gs.map Prod.fst else gs.map Prod.fst ++ [m] := by
  induction gs with
  | nil => simp [combineInto]
  | cons hd tl ih =>
    obtain ⟨m', fs'⟩ := hd
    by_cases hmm : m' = m
    · subst hmm; simp [combineInto]
    · simp only [combineInto, hmm, if_false, List.map_cons]
      by_cases hmem : m ∈ tl.map Prod.fst
      · simp [ih, hmem, List.mem_cons, Ne.symm hmm]
      · have : m ∉ (m', fs').1 :: tl.map Prod.fst := by
          simp [List.mem_cons, Ne.symm hmm, hmem]
        simp [ih, hmem, List.mem_cons, Ne.symm hmm]

/- Grouping preserves table-uniqueness. -/
@[grind] lemma nodup_combineInto (gs : List TableGroup) (m f : Int)
    (h : (gs.map Prod.fst).Nodup) : ((combineInto gs m f).map Prod.fst).Nodup := by
  rw [keys_combineInto]
  by_cases hmem : m ∈ gs.map Prod.fst
  · simp [hmem, h]
  · simp only [hmem, if_false]
    exact h.append (by simp) (by simp [hmem])

/- The accumulator's tables stay unique through any fold, starting from any
   table-unique seed. -/
lemma nodup_foldl (relations : List Relation) :
    ∀ gs, (gs.map Prod.fst).Nodup → ((relations.foldl combineStep gs).map Prod.fst).Nodup := by
  induction relations with
  | nil => intro gs h; simpa using h
  | cons e es ih =>
    intro gs h
    exact ih (combineStep gs e) (by simpa [combineStep] using nodup_combineInto gs e.1 e.2 h)

/- The plan never lists a table twice: each target table is queried with a single
   combined query, regardless of how many candidate relations reference it. -/
@[grind] lemma combined_nodup (relations : List Relation) :
    ((combined relations).map Prod.fst).Nodup :=
  nodup_foldl relations [] (by simp)

/- Forward-fold step: extending the consumed prefix by one relation groups that
   relation into the plan built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body. -/
lemma combined_take_step (relations : List Relation) (i : Nat) (hi : i < relations.length) :
    (relations.take (i + 1)).foldl combineStep []
      = combineStep ((relations.take i).foldl combineStep []) relations[i]! := by
  have hcons : relations.take (i + 1) = relations.take i ++ [relations[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the combined fast-delete plan from the full sequence of candidate
   `relations`.
   The result is exactly the order-preserving group-by-table collapse of the
   sequence: every distinct table appears once (no table is queried twice), in
   first-encounter order, carrying every referencing column. `relations` is
   read-only (not `mut`): the loop builds a fresh result and never mutates its
   input. -/
method combineByTable (relations : List Relation) return (out : List TableGroup)
  ensures out = combined relations
  ensures (out.map Prod.fst).Nodup
  do
    -- impl-start
    let result : List TableGroup := relations.foldl combineStep []
    return result
    -- impl-end

prove_correct combineByTable by
  loom_solve <;> (first | rfl | exact combined_nodup relations | (simp only [combined]; exact combined_nodup relations))
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: frozen spec_view keeps the ENTIRE pure region (combineInto/combineStep/combined + lemmas) and BOTH ensures clauses byte-identical; only impl body + prove_correct proof are editable (confirmed via markers.spec_view). Postcondition = exact functional equality `out = combined relations` (a concrete deterministic foldl) ∧ `(out.map Prod.fst).Nodup` — maximally tight.

### ATTACKS (all same_spec=True, verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch bug (raw per-relation singleton groups, result++[(e.1,[e.2])]) => EXIT 1 REJECT (= prepatch_reproduced; matches shipped Solution_prepatch.lean which also EXIT 1).
- atk_2 return [] => EXIT 1 REJECT.
- atk_3 group-by-COLUMN (combineInto result e.2 e.1) => EXIT 1 REJECT.
- atk_4 boundary/off-by-one (i:=1, skips first relation) => EXIT 1 REJECT.
- atk_5 dedup tables but DROP later columns (keep only first) => EXIT 1 REJECT.
- atk_6 reverse iteration (wrong first-encounter order) => EXIT 1 REJECT.
- atk_9 cons/prepend order ((e.1,[e.2])::result) => EXIT 1 REJECT.
- atk_10 demonic-havoc / ungrounded-oracle-echo analog (let result :| Nodup-only, satisfying the weaker clause) => EXIT 1 REJECT (no opaque symbol to echo; equality clause pins the value).
All 8 given a MAXIMALLY-PERMISSIVE fair proof (loom_solve <;> simp_all[...] <;> omega <;> grind <;> aesop), not just the baseline proof. NONE verifies. No candidates => no faithful patches needed => no run_resolve required for a break (none exists).

POSITIVE CONTROL pos.lean: structurally-different CORRECT impl (loop-free `relations.foldl combineStep []` instead of the baseline while-loop) => same_spec=True, EXIT 0 VERIFIES. Spec is non-vacuous.

NON-TERMINATION NOTE (documented, NOT submitted as a breaking attack): atk_7.lean (`while i < relations.length ∨ True`, done_with = full postcondition) VERIFIES (EXIT 0). This is a PURE partial-correctness (Hoare) vacuity artifact of `set_option loom.semantics.termination "partial"`: a divergent program trivially satisfies any postcondition. PROVEN by diag_terminating7.lean — the SAME strong done_with postcondition with a TERMINATING guard `i < relations.length` FAILS (EXIT 1). The escape is universal to all 401/500 "partial" velvet bundles and is explicitly sanctioned by prompts/velvet/spec_guide.md + gates/hygiene.py (only requires *some* termination set_option).

Its only "faithful" refinement would be an infinite loop in Collector.collect, which (a) is NOT a faithful skeleton of the gold's grouping change per judge_equivalence_system.md and (b) would merely HANG the harness rather than demonstrate a functionally-WRONG TERMINATING impl passing — i.e. it is out of G-EQ scope (verify⇏correct targets terminating wrong impls). It is therefore NOT listed in `attacks` (listing it would make the runner treat it as a candidate needing a resolving-check patch and force a spurious INCONCLUSIVE/BROKEN — a rubber-stamp falsification). atk_8 (while True with incomplete done_with) correctly REJECTS (EXIT 1), confirming the escape needs the postcondition placed in done_with.

REFINEMENT.md AUDIT: declares NO A-legs — all steps A1–A5 are R/I. axioms region empty (grep-confirmed: only region markers, no axiom/opaque/sorry/admit/Classical.choice/noncomputable). mapping.md §3: 0 callees axiomatized; get_candidate_relations_to_delete/can_fast_delete only supply/filter the read-only `relations` stream. The deep model `combined`/`combineInto` models the CHANGED function's OWN grouping (defaultdict(list)[k].append + insertion-ordered .items() readout) — legitimate deep modeling, not a kind-3 hidden-behind-axiom, and not an ungrounded-oracle A-reference. Correspondence is exact and corroborated by G-PANEL Docker evidence (post-gold => [('SecondReferrer',['referrer','other_referrer'])] = combined relations). No kind-3 legs; A-leg correspondence vacuously holds (no A-legs).

Evidence dir: (attack .lean + .out files, diag_terminating7.lean, FINDINGS.md). VERDICT: SOUND — 8 functional same-spec wrong impls run and none breaks the spec; positive control verifies; prepatch reproduced+rejects.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The producer of candidate relations is an
--  unchanged enumerator whose only relevant effect is the SEQUENCE of
--  (table, column) relations it yields; that sequence is the read-only input
--  `relations` here. The combining transformation under spec is modeled DEEPLY
--  below — every observable is computed from `relations`, nothing is borrowed
--  from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- One candidate relation feeding the fast-delete pass: a target table (`fst`)
   paired with the single column (`snd`) on that table that references the rows
   being deleted. Tables and columns are carried by stable integer identities. -/
abbrev Relation := Int × Int

/- One combined fast-delete group: a target table (`fst`) paired with the list
   of columns (`snd`) on that table to be matched, in first-encounter order. A
   single group is emitted as ONE query of the shape "delete the rows of this
   table where any of these columns matches". -/
abbrev TableGroup := Int × List Int

/- Insertion-ordered grouping: record that column `f` of table `m` must be
   matched.
   - a table never seen before is appended at the end, keeping the order in
     which tables were first encountered, carrying just `[f]`;
   - a table already present keeps its original position and APPENDS `f` to its
     column list (so all columns of one table accumulate into one group).
   This is the exact semantics of `groups[m].append(f)` on an order-preserving
   table→columns mapping then reading it back in table order. -/
def combineInto (gs : List TableGroup) (m : Int) (f : Int) : List TableGroup :=
  match gs with
  | []            => [(m, [f])]
  | (m', fs') :: r => if m' = m then (m, fs' ++ [f]) :: r else (m', fs') :: combineInto r m f

/- Fold one relation into the accumulating grouping. -/
def combineStep (gs : List TableGroup) (e : Relation) : List TableGroup := combineInto gs e.1 e.2

/- The combined fast-delete plan built from a whole sequence of candidate
   relations: each relation is grouped under its table; the plan is that mapping
   read out in table order. Net effect: every distinct table appears EXACTLY
   ONCE (one combined query per table), in first-encounter order, carrying every
   column that referenced it — so N relations on the same table collapse to a
   single group instead of N separate ones. -/
def combined (relations : List Relation) : List TableGroup := relations.foldl combineStep []

/- Tables of a grouping step: an already-present table leaves the table list
   unchanged; a fresh table is appended. (The column accumulation does not touch
   the key projection.) -/
@[grind] lemma keys_combineInto (gs : List TableGroup) (m f : Int) :
    (combineInto gs m f).map Prod.fst
      = if m ∈ gs.map Prod.fst then gs.map Prod.fst else gs.map Prod.fst ++ [m] := by
  induction gs with
  | nil => simp [combineInto]
  | cons hd tl ih =>
    obtain ⟨m', fs'⟩ := hd
    by_cases hmm : m' = m
    · subst hmm; simp [combineInto]
    · simp only [combineInto, hmm, if_false, List.map_cons]
      by_cases hmem : m ∈ tl.map Prod.fst
      · simp [ih, hmem, List.mem_cons, Ne.symm hmm]
      · have : m ∉ (m', fs').1 :: tl.map Prod.fst := by
          simp [List.mem_cons, Ne.symm hmm, hmem]
        simp [ih, hmem, List.mem_cons, Ne.symm hmm]

/- Grouping preserves table-uniqueness. -/
@[grind] lemma nodup_combineInto (gs : List TableGroup) (m f : Int)
    (h : (gs.map Prod.fst).Nodup) : ((combineInto gs m f).map Prod.fst).Nodup := by
  rw [keys_combineInto]
  by_cases hmem : m ∈ gs.map Prod.fst
  · simp [hmem, h]
  · simp only [hmem, if_false]
    exact h.append (by simp) (by simp [hmem])

/- The accumulator's tables stay unique through any fold, starting from any
   table-unique seed. -/
lemma nodup_foldl (relations : List Relation) :
    ∀ gs, (gs.map Prod.fst).Nodup → ((relations.foldl combineStep gs).map Prod.fst).Nodup := by
  induction relations with
  | nil => intro gs h; simpa using h
  | cons e es ih =>
    intro gs h
    exact ih (combineStep gs e) (by simpa [combineStep] using nodup_combineInto gs e.1 e.2 h)

/- The plan never lists a table twice: each target table is queried with a single
   combined query, regardless of how many candidate relations reference it. -/
@[grind] lemma combined_nodup (relations : List Relation) :
    ((combined relations).map Prod.fst).Nodup :=
  nodup_foldl relations [] (by simp)

/- Forward-fold step: extending the consumed prefix by one relation groups that
   relation into the plan built from the shorter prefix. The single goal
   `loom_solve` leaves for the loop body. -/
lemma combined_take_step (relations : List Relation) (i : Nat) (hi : i < relations.length) :
    (relations.take (i + 1)).foldl combineStep []
      = combineStep ((relations.take i).foldl combineStep []) relations[i]! := by
  have hcons : relations.take (i + 1) = relations.take i ++ [relations[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the combined fast-delete plan from the full sequence of candidate
   `relations`.
   The result is exactly the order-preserving group-by-table collapse of the
   sequence: every distinct table appears once (no table is queried twice), in
   first-encounter order, carrying every referencing column. `relations` is
   read-only (not `mut`): the loop builds a fresh result and never mutates its
   input. -/
method combineByTable (relations : List Relation) return (out : List TableGroup)
  ensures out = combined relations
  ensures (out.map Prod.fst).Nodup
  do
    -- impl-start
    let result : List TableGroup := relations.foldl combineStep []
    return result
    -- impl-end

prove_correct combineByTable by
  loom_solve <;> (first | rfl | exact combined_nodup relations | (simp only [combined]; exact combined_nodup relations))
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: frozen spec_view keeps the ENTIRE pure region (combineInto/combineStep/combined + lemmas) and BOTH ensures clauses byte-identical; only impl body + prove_correct proof are editable (confirmed via markers.spec_view). Postcondition = exact functional equality `out = combined relations` (a concrete deterministic foldl) ∧ `(out.map Prod.fst).Nodup` — maximally tight.

### ATTACKS (all same_spec=True, verified with `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch bug (raw per-relation singleton groups, result++[(e.1,[e.2])]) => EXIT 1 REJECT (= prepatch_reproduced; matches shipped Solution_prepatch.lean which also EXIT 1).
- atk_2 return [] => EXIT 1 REJECT.
- atk_3 group-by-COLUMN (combineInto result e.2 e.1) => EXIT 1 REJECT.
- atk_4 boundary/off-by-one (i:=1, skips first relation) => EXIT 1 REJECT.
- atk_5 dedup tables but DROP later columns (keep only first) => EXIT 1 REJECT.
- atk_6 reverse iteration (wrong first-encounter order) => EXIT 1 REJECT.
- atk_9 cons/prepend order ((e.1,[e.2])::result) => EXIT 1 REJECT.
- atk_10 demonic-havoc / ungrounded-oracle-echo analog (let result :| Nodup-only, satisfying the weaker clause) => EXIT 1 REJECT (no opaque symbol to echo; equality clause pins the value).
All 8 given a MAXIMALLY-PERMISSIVE fair proof (loom_solve <;> simp_all[...] <;> omega <;> grind <;> aesop), not just the baseline proof. NONE verifies. No candidates => no faithful patches needed => no run_resolve required for a break (none exists).

POSITIVE CONTROL pos.lean: structurally-different CORRECT impl (loop-free `relations.foldl combineStep []` instead of the baseline while-loop) => same_spec=True, EXIT 0 VERIFIES. Spec is non-vacuous.

NON-TERMINATION NOTE (documented, NOT submitted as a breaking attack): atk_7.lean (`while i < relations.length ∨ True`, done_with = full postcondition) VERIFIES (EXIT 0). This is a PURE partial-correctness (Hoare) vacuity artifact of `set_option loom.semantics.termination "partial"`: a divergent program trivially satisfies any postcondition. PROVEN by diag_terminating7.lean — the SAME strong done_with postcondition with a TERMINATING guard `i < relations.length` FAILS (EXIT 1). The escape is universal to all 401/500 "partial" velvet bundles and is explicitly sanctioned by prompts/velvet/spec_guide.md + gates/hygiene.py (only requires *some* termination set_option).

Its only "faithful" refinement would be an infinite loop in Collector.collect, which (a) is NOT a faithful skeleton of the gold's grouping change per judge_equivalence_system.md and (b) would merely HANG the harness rather than demonstrate a functionally-WRONG TERMINATING impl passing — i.e. it is out of G-EQ scope (verify⇏correct targets terminating wrong impls). It is therefore NOT listed in `attacks` (listing it would make the runner treat it as a candidate needing a resolving-check patch and force a spurious INCONCLUSIVE/BROKEN — a rubber-stamp falsification). atk_8 (while True with incomplete done_with) correctly REJECTS (EXIT 1), confirming the escape needs the postcondition placed in done_with.

REFINEMENT.md AUDIT: declares NO A-legs — all steps A1–A5 are R/I. axioms region empty (grep-confirmed: only region markers, no axiom/opaque/sorry/admit/Classical.choice/noncomputable). mapping.md §3: 0 callees axiomatized; get_candidate_relations_to_delete/can_fast_delete only supply/filter the read-only `relations` stream. The deep model `combined`/`combineInto` models the CHANGED function's OWN grouping (defaultdict(list)[k].append + insertion-ordered .items() readout) — legitimate deep modeling, not a kind-3 hidden-behind-axiom, and not an ungrounded-oracle A-reference. Correspondence is exact and corroborated by G-PANEL Docker evidence (post-gold => [('SecondReferrer',['referrer','other_referrer'])] = combined relations). No kind-3 legs; A-leg correspondence vacuously holds (no A-legs).

Evidence dir: (attack .lean + .out files, diag_terminating7.lean, FINDINGS.md). VERDICT: SOUND — 8 functional same-spec wrong impls run and none breaks the spec; positive control verifies; prepatch reproduced+rejects.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region byte-identity confirmed: swebench_unified.markers.same_spec(Solution, prepatch, VelvetBackend) == True; the full combined/combineInto model sits inside the spec view (pure region hash matches G-HYGIENE). Solution.lean verifies (lean_verify.sh exit 0), so the spec is non-vacuous.

Faithfulness of the modeled function `combined : List Relation -> List TableGroup` vs. the real post-patch callee (Collector.collect fast-delete pass, deletion.py:215-271):
- Real behavior: model_fast_deletes = defaultdict(list); for each fast-deletable candidate relation, model_fast_deletes[related.related_model].append(related.field); then .items() in insertion order -> one fast_deletes entry per table. Net = one combined query per target table, tables in first-encounter order, each carrying every referencing column in encounter order.
- Lean model: combineInto keeps an existing key in place and appends the column via fs' ++ [f] (== list.append), and appends a never-seen key at the tail; combined = foldl over the stream from []. This is exactly defaultdict(list)[k].append(v) with insertion-ordered read-out.

Checked candidate divergences, none found:
  * first-encounter key ordering (new keys appended at tail) matches;
  * per-key column order (fs' ++ [f]) matches .append;
  * duplicate (table,column) pairs produce duplicate columns in both;
  * empty stream -> [] both sides;
  * the bug case (two CASCADE FKs SecondReferrer.referrer / other_referrer -> Referrer) maps to table=Referrer, columns=[f1,f2], one group -> assertNumQueries(2) observable.
The ensures (out.map Prod.fst).Nodup clause is a proven consequence of `combined` (combined_nodup), so it adds no strength beyond the grouping and directly encodes the F2P 'each table queried once' property; it does not over-constrain.

Abstraction-boundary note (not a divergence): `relations` is defined as the ALREADY-fast-path-filtered candidate stream (post get_candidate_relations_to_delete + DO_NOTHING/keep_parents guards + can_fast_delete). Pre- and post-patch apply identical selection guards, and the only can_fast_delete edit (type(objs) -> objs._meta.model) changes the eligibility INPUT, not which relations are admitted for the F2P case; so beginning the model at the grouping of the selected stream does not make the spec disagree with repo behavior on any input the enumerator can produce. G-CONF legitimately skipped (conf_skip=true): the combined-vs-separate multiplicity is only observable against a live DB via assertNumQueries, no DB-free oracle exists; soundness carried by G-VERIFY + G-DIFF (prepatch emits one singleton group per relation -> fails both ensures clauses on any repeated-table input). No input found where the modeled function disagrees with the real callee -> spec is not too strong / does not drift. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet flavor: impl region collapsed, prove_correct body elided) formalizes exactly the fix the PUBLIC problem_statement already describes. The issue explicitly states 'the collection logic should combine such queries by table to reduce roundtrips' and gives the worked example collapsing N per-column DELETEs into ONE combined 'DELETE ... WHERE col1=:id OR col2=:id' per table. The spec's discriminating postconditions `out = combined relations` and `(out.map Prod.fst).Nodup` (each distinct table appears exactly once, carrying all its referencing columns in first-encounter order) are a faithful transliteration of that public behavior, not information beyond it. The spec view uses only abstract carriers (Relation, TableGroup, combineInto/combined/combineByTable) and generic table/column/query vocabulary matching the issue's own language. None of the gold patch's implementation-specific identifiers leak into the spec view: defaultdict(list)/model_fast_deletes, the related_objects(related_model, related_fields, objs) signature change, reduce(operator.or_, ...), get_del_batches(objs, fields), the can_fast_delete type(objs)->objs._meta.model change, and the admin/utils.py follow-through appear ONLY in refinement.md/mapping.md (auditor-facing derivation docs, NOT the consumer spec view). The pseudo-code comment `groups[m].append(f)` is a generic description of order-preserving grouping, not the gold's actual symbol. Verified mechanically: leakage.screen passed=True with no hard_failures; same_spec(Solution, Solution_prepatch)=True confirming the leak surface is the shared spec view. 'First-encounter order' is a benign natural-semantics refinement, not a discriminator hidden from the public issue. No spec-view line reveals the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.