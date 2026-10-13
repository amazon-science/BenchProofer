# P2 adversarial audit — django__django-15563

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The two facts an ancestor's update is routed on —
@@ -88,10 +88,11 @@
       invariant i ≤ parents.length
       invariant st = (parents.take i).foldl stepCol ([], 1)
       done_with i = parents.length
-      decreasing parents.length - i
     do
-      let p := parents[i]!
-      st := stepCol st p
+      let _p := parents[i]!
+      let cols := st.1
+      let next := st.2
+      st := (cols ++ [0], next)
       i := i + 1
     return st.1.map (idColumn rows)
     -- impl-end
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
 -- (No axiomatized callees. The two facts an ancestor's update is routed on —
@@ -82,13 +82,12 @@
   ensures out = (assignedColumns parents).map (idColumn rows)
   do
     -- impl-start
-    let mut st : List Nat × Nat := ([], 1)
+    let mut st : List Nat × Nat := ([], 0)
     let mut i := 0
     while i < parents.length
       invariant i ≤ parents.length
-      invariant st = (parents.take i).foldl stepCol ([], 1)
+      invariant st = (parents.take i).foldl stepCol ([], 0)
       done_with i = parents.length
-      decreasing parents.length - i
     do
       let p := parents[i]!
       st := stepCol st p
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
 -- (No axiomatized callees. The two facts an ancestor's update is routed on —
@@ -88,10 +88,11 @@
       invariant i ≤ parents.length
       invariant st = (parents.take i).foldl stepCol ([], 1)
       done_with i = parents.length
-      decreasing parents.length - i
     do
       let p := parents[i]!
-      st := stepCol st p
+      let cols := st.1
+      let next := st.2
+      st := if p.sharesChildPk then (cols ++ [next], next + 1) else (cols ++ [0], next)
       i := i + 1
     return st.1.map (idColumn rows)
     -- impl-end
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
 -- (No axiomatized callees. The two facts an ancestor's update is routed on —
@@ -84,11 +84,10 @@
     -- impl-start
     let mut st : List Nat × Nat := ([], 1)
     let mut i := 0
-    while i < parents.length
+    while i + 1 < parents.length
       invariant i ≤ parents.length
       invariant st = (parents.take i).foldl stepCol ([], 1)
-      done_with i = parents.length
-      decreasing parents.length - i
+      done_with i + 1 = parents.length
     do
       let p := parents[i]!
       st := stepCol st p
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
 -- (No axiomatized callees. The two facts an ancestor's update is routed on —
@@ -88,12 +88,11 @@
       invariant i ≤ parents.length
       invariant st = (parents.take i).foldl stepCol ([], 1)
       done_with i = parents.length
-      decreasing parents.length - i
     do
       let p := parents[i]!
       st := stepCol st p
       i := i + 1
-    return st.1.map (idColumn rows)
+    return st.1.map (fun _ => idColumn rows 0)
     -- impl-end
 
 prove_correct parentFilterIds by
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
 -- (No axiomatized callees. The two facts an ancestor's update is routed on —
@@ -83,15 +83,11 @@
   do
     -- impl-start
     let mut st : List Nat × Nat := ([], 1)
-    let mut i := 0
+    let mut i := parents.length
     while i < parents.length
       invariant i ≤ parents.length
-      invariant st = (parents.take i).foldl stepCol ([], 1)
       done_with i = parents.length
-      decreasing parents.length - i
     do
-      let p := parents[i]!
-      st := stepCol st p
       i := i + 1
     return st.1.map (idColumn rows)
     -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The two facts an ancestor's update is routed on —
@@ -82,24 +82,9 @@
   ensures out = (assignedColumns parents).map (idColumn rows)
   do
     -- impl-start
-    let mut st : List Nat × Nat := ([], 1)
-    let mut i := 0
-    while i < parents.length
-      invariant i ≤ parents.length
-      invariant st = (parents.take i).foldl stepCol ([], 1)
-      done_with i = parents.length
-      decreasing parents.length - i
-    do
-      let p := parents[i]!
-      st := stepCol st p
-      i := i + 1
-    return st.1.map (idColumn rows)
+    return (assignedColumns parents).map (idColumn rows)
     -- impl-end
 
 prove_correct parentFilterIds by
   loom_solve
-  case «invariant_2: st = (parents.take i).foldl stepCol ([], 1)» =>
-    have hi : i < parents.length := by omega
-    rw [invariant_2, cols_take_step parents i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  all_goals simp_all [assignedColumns]
+  all_goals simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two facts an ancestor's update is routed on —
--  "does this ancestor share the child's identity value" (`sharesChildPk`) and
--  "the fetched identity rows" (`rows`) — are taken as FREE INPUTS. The spec
--  makes no behavioural claim about how those facts are produced and holds for
--  EVERY schema/row set, so there is nothing to check against a real callee,
--  hence no G-AX. The routing decision under spec — which fetched column each
--  ancestor's filter values are drawn from — is modeled deeply below; every
--  observable is computed from the inputs, nothing is borrowed from an oracle.
--  See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- An ancestor table that the same statement must also update, abstracted to the
   single fact that decides where its filter values come from: whether it shares
   the child's identity value (`sharesChildPk`). When it does, the child's own
   identity is also the ancestor's, so no extra value need be fetched for it;
   when it does not, a distinct identity value must be fetched alongside the
   child's. -/
structure Parent where
  sharesChildPk : Bool
deriving Inhabited, DecidableEq

/- Advance the column assignment by one ancestor, threading the next free column.
   Column 0 always carries the child's identity. An ancestor that shares that
   identity is assigned column 0 (reuse it); one that does not is assigned the
   next free column, which is then consumed. -/
def stepCol (st : List Nat × Nat) (p : Parent) : List Nat × Nat :=
  let cols := st.1
  let next := st.2
  if p.sharesChildPk then (cols ++ [0], next)
  else (cols ++ [next], next + 1)

/- The column each ancestor's filter values are drawn from, one per ancestor in
   order. Column 0 is the child's identity; distinct-identity ancestors take the
   appended columns in the order they appear. -/
def assignedColumns (ps : List Parent) : List Nat :=
  (ps.foldl stepCol ([], 1)).1

/- The identity values for a single column: the value at that column of every
   fetched row. A row is the tuple of fetched values for one matched child; the
   column index selects which fetched identity is read. -/
def idColumn (rows : List (List Int)) (idx : Nat) : List Int :=
  rows.map (fun row => row[idx]!)

/- Forward-fold step: extending the consumed prefix by one ancestor advances the
   assignment built from the shorter prefix by exactly that ancestor. The single
   goal `loom_solve` leaves for the loop body. -/
lemma cols_take_step (ps : List Parent) (i : Nat) (hi : i < ps.length) :
    (ps.take (i + 1)).foldl stepCol ([], 1)
      = stepCol ((ps.take i).foldl stepCol ([], 1)) ps[i]! := by
  have hcons : ps.take (i + 1) = ps.take i ++ [ps[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- For a statement that updates a child together with the ancestors in
   `parents`, decide, per ancestor (in order), the list of identity values its
   own update must be filtered on. Each value is read from one column of the
   fetched `rows`: an ancestor that shares the child's identity reads the child
   identity column; one that does not reads the distinct identity fetched for it.

   `parents` and `rows` are read-only (not `mut`): the routing threads a fresh
   accumulator and never mutates anything it is handed (directive 5). -/
method parentFilterIds (parents : List Parent) (rows : List (List Int))
    return (out : List (List Int))
  ensures out = (assignedColumns parents).map (idColumn rows)
  do
    -- impl-start
    let mut st : List Nat × Nat := ([], 1)
    let mut i := 0
    while i < parents.length
      invariant i ≤ parents.length
      invariant st = (parents.take i).foldl stepCol ([], 1)
      done_with i = parents.length
    do
      let p := parents[i]!
      st := stepCol st p
      i := i + 1
    return st.1.map (idColumn rows)
    -- impl-end

prove_correct parentFilterIds by
  loom_solve
  case «invariant_2: st = (parents.take i).foldl stepCol ([], 1)» =>
    have hi : i < parents.length := by omega
    rw [invariant_2, cols_take_step parents i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  all_goals simp_all [assignedColumns]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen postcondition `ensures out = (assignedColumns parents).map (idColumn rows)` is a TOTAL, DETERMINISTIC, closed-form functional equation pinning `out` as an exact function of the inputs (parents, rows). Verification is therefore only achievable by an impl that computes the gold routing function extensionally; no wrong impl can satisfy prove_correct. This is the strongest possible G-EQ shape.

Protocol executed (all; same_spec=True verified for all 7 attacks + positive control against velvet backend; verified with scripts/lean_verify.sh, wall 300s; verifications run concurrently in batches of 4).

Positive control (gold impl) pos_control.lean: `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (VERIFIES).

Six DISTINCT wrong impls (impl-region-only edits, spec/axioms/pure/pre/post byte-identical) -- all FAIL verification on the postcondition goal `ensures_1: out = (assignedColumns parents).map (idColumn rows)`, i.e. genuine spec discrimination, NOT syntax errors:
  - atk_1.lean (prepatch bug / ungrounded routing: EVERY ancestor -> child identity column 0, `st := (cols++[0], next)`): exit 1, unsolved goals under invariant_2 (matches Solution_prepatch behavior).
  - atk_2.lean (boundary/off-by-one: next counter starts at 0 instead of 1 = len([pk])): exit 1, invariant/ensures mismatch.
  - atk_3.lean (control-flow-effect: swapped branches -- shared-pk ancestor routed to a fresh column, non-shared to col 0): exit 1, unsolved goals.
  - atk_4.lean (partial-domain: loop guard `i+1 < length` skips the last ancestor): exit 1, unsolved ensures_1.
  - atk_5.lean (wrong projection: every ancestor reads column 0, `map (fun _ => idColumn rows 0)`): exit 1, unsolved ensures_1.
  - atk_6.lean (control-flow: loop never entered, returns []): exit 1, ensures_1 not discharged.

atk_7.lean (ungrounded-oracle ECHO: impl returns the spec RHS `(assignedColumns parents).map (idColumn rows)` verbatim): `bash scripts/lean_verify.sh atk_7.lean` -> exit 0 (VERIFIES). Because it returns exactly the postcondition RHS, it is behaviorally IDENTICAL to the gold impl on every input; its faithful refined patch is therefore the gold patch. Per the 2026-08-06 echo-attack policy, a same-spec verifying echo whose refined patch resolves is NOT a weakness. MANDATORY resolve run executed via swebench_unified.harness.run_resolve('django__django-15563', <faithful patch>, timeout=900): COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, NOTE='resolved'. So the only verifying non-gold impl's materialized faithful patch RESOLVES -> verify does NOT imply incorrect here.

prepatch_reproduced=True: Solution_prepatch.lean (always-column-0 routing) `bash scripts/lean_verify.sh prepatch.lean` -> exit 1, unsolved goals on `ensures_1` (fails exactly on a non-shared-pk ancestor), reproducing the bug the two F2P tests (test_mti_update_parent_through_child, test_mti_update_grand_parent_through_child) observe. atk_1 is an independent re-encoding of the same bug and also fails.

G-CONF independently re-run (`python conformance_check.py`) -> exit 0: R/I shadow of parentFilterIds agrees with the gold-patched pre_sql_setup column routing on 100006 checks (F2P boundary scenarios + fuzz, seed 15563), 0 disagreements. Confirms the deep model (stepCol/assignedColumns/idColumn) faithfully transliterates the gold routing.

refinement.md audit: all 7 legs are R (A1 related_updates order, A2 rows, A3 sharesChildPk -- type refinements) / I (A4 the fold loop, A5 related_ids_index, A6 idColumn projection -- concrete transliterations) / R+I (A7 per-ancestor pk__in consumption in get_related_updates). NO kind-3 (inexpressible-changed-op) leg: the operation that actually changed -- per-ancestor identity-column routing -- is modeled DEEPLY (spelled-out stepCol/assignedColumns fold + idColumn read), not hidden behind an axiom about the function under change. There are NO axiomatized callees and NO deep-model reference to a real callee, so G-AX is legitimately skip; sharesChildPk and rows are genuine free inputs (the pk-chain predicate and the pre-select are UNCHANGED by the patch; only which fetched column each ancestor reads changes, which is the modeled routing) and the spec holds universally over them, so no oracle borrowing. mapping.md bijection (Bool identity, row/list order preservation, column index identity) is sound. The A-legs' correspondence to the real callees (compiler.py:1839-1875 pre_sql_setup, subqueries.py:137 get_related_updates) holds.

Conclusion: >=5 distinct wrong impls attacked; all wrong impls fail verification via genuine postcondition discrimination; the one verifying non-gold impl (echo) resolves under the official harness. No verify-but-not-resolve counterexample exists. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The two facts an ancestor's update is routed on —
--  "does this ancestor share the child's identity value" (`sharesChildPk`) and
--  "the fetched identity rows" (`rows`) — are taken as FREE INPUTS. The spec
--  makes no behavioural claim about how those facts are produced and holds for
--  EVERY schema/row set, so there is nothing to check against a real callee,
--  hence no G-AX. The routing decision under spec — which fetched column each
--  ancestor's filter values are drawn from — is modeled deeply below; every
--  observable is computed from the inputs, nothing is borrowed from an oracle.
--  See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- An ancestor table that the same statement must also update, abstracted to the
   single fact that decides where its filter values come from: whether it shares
   the child's identity value (`sharesChildPk`). When it does, the child's own
   identity is also the ancestor's, so no extra value need be fetched for it;
   when it does not, a distinct identity value must be fetched alongside the
   child's. -/
structure Parent where
  sharesChildPk : Bool
deriving Inhabited, DecidableEq

/- Advance the column assignment by one ancestor, threading the next free column.
   Column 0 always carries the child's identity. An ancestor that shares that
   identity is assigned column 0 (reuse it); one that does not is assigned the
   next free column, which is then consumed. -/
def stepCol (st : List Nat × Nat) (p : Parent) : List Nat × Nat :=
  let cols := st.1
  let next := st.2
  if p.sharesChildPk then (cols ++ [0], next)
  else (cols ++ [next], next + 1)

/- The column each ancestor's filter values are drawn from, one per ancestor in
   order. Column 0 is the child's identity; distinct-identity ancestors take the
   appended columns in the order they appear. -/
def assignedColumns (ps : List Parent) : List Nat :=
  (ps.foldl stepCol ([], 1)).1

/- The identity values for a single column: the value at that column of every
   fetched row. A row is the tuple of fetched values for one matched child; the
   column index selects which fetched identity is read. -/
def idColumn (rows : List (List Int)) (idx : Nat) : List Int :=
  rows.map (fun row => row[idx]!)

/- Forward-fold step: extending the consumed prefix by one ancestor advances the
   assignment built from the shorter prefix by exactly that ancestor. The single
   goal `loom_solve` leaves for the loop body. -/
lemma cols_take_step (ps : List Parent) (i : Nat) (hi : i < ps.length) :
    (ps.take (i + 1)).foldl stepCol ([], 1)
      = stepCol ((ps.take i).foldl stepCol ([], 1)) ps[i]! := by
  have hcons : ps.take (i + 1) = ps.take i ++ [ps[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- For a statement that updates a child together with the ancestors in
   `parents`, decide, per ancestor (in order), the list of identity values its
   own update must be filtered on. Each value is read from one column of the
   fetched `rows`: an ancestor that shares the child's identity reads the child
   identity column; one that does not reads the distinct identity fetched for it.

   `parents` and `rows` are read-only (not `mut`): the routing threads a fresh
   accumulator and never mutates anything it is handed (directive 5). -/
method parentFilterIds (parents : List Parent) (rows : List (List Int))
    return (out : List (List Int))
  ensures out = (assignedColumns parents).map (idColumn rows)
  do
    -- impl-start
    let mut st : List Nat × Nat := ([], 1)
    let mut i := 0
    while i < parents.length
      invariant i ≤ parents.length
      invariant st = (parents.take i).foldl stepCol ([], 1)
      done_with i = parents.length
    do
      let p := parents[i]!
      st := stepCol st p
      i := i + 1
    return st.1.map (idColumn rows)
    -- impl-end

prove_correct parentFilterIds by
  loom_solve
  case «invariant_2: st = (parents.take i).foldl stepCol ([], 1)» =>
    have hi : i < parents.length := by omega
    rw [invariant_2, cols_take_step parents i hi,
        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
  all_goals simp_all [assignedColumns]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The frozen postcondition `ensures out = (assignedColumns parents).map (idColumn rows)` is a TOTAL, DETERMINISTIC, closed-form functional equation pinning `out` as an exact function of the inputs (parents, rows). Verification is therefore only achievable by an impl that computes the gold routing function extensionally; no wrong impl can satisfy prove_correct. This is the strongest possible G-EQ shape.

Protocol executed (all; same_spec=True verified for all 7 attacks + positive control against velvet backend; verified with scripts/lean_verify.sh, wall 300s; verifications run concurrently in batches of 4).

Positive control (gold impl) pos_control.lean: `bash scripts/lean_verify.sh pos_control.lean` -> exit 0 (VERIFIES).

Six DISTINCT wrong impls (impl-region-only edits, spec/axioms/pure/pre/post byte-identical) -- all FAIL verification on the postcondition goal `ensures_1: out = (assignedColumns parents).map (idColumn rows)`, i.e. genuine spec discrimination, NOT syntax errors:
  - atk_1.lean (prepatch bug / ungrounded routing: EVERY ancestor -> child identity column 0, `st := (cols++[0], next)`): exit 1, unsolved goals under invariant_2 (matches Solution_prepatch behavior).
  - atk_2.lean (boundary/off-by-one: next counter starts at 0 instead of 1 = len([pk])): exit 1, invariant/ensures mismatch.
  - atk_3.lean (control-flow-effect: swapped branches -- shared-pk ancestor routed to a fresh column, non-shared to col 0): exit 1, unsolved goals.
  - atk_4.lean (partial-domain: loop guard `i+1 < length` skips the last ancestor): exit 1, unsolved ensures_1.
  - atk_5.lean (wrong projection: every ancestor reads column 0, `map (fun _ => idColumn rows 0)`): exit 1, unsolved ensures_1.
  - atk_6.lean (control-flow: loop never entered, returns []): exit 1, ensures_1 not discharged.

atk_7.lean (ungrounded-oracle ECHO: impl returns the spec RHS `(assignedColumns parents).map (idColumn rows)` verbatim): `bash scripts/lean_verify.sh atk_7.lean` -> exit 0 (VERIFIES). Because it returns exactly the postcondition RHS, it is behaviorally IDENTICAL to the gold impl on every input; its faithful refined patch is therefore the gold patch. Per the 2026-08-06 echo-attack policy, a same-spec verifying echo whose refined patch resolves is NOT a weakness. MANDATORY resolve run executed via swebench_unified.harness.run_resolve('django__django-15563', <faithful patch>, timeout=900): COMPLETED=True, RESOLVED=True, ATTEMPTS=1, FLAKY=False, NOTE='resolved'. So the only verifying non-gold impl's materialized faithful patch RESOLVES -> verify does NOT imply incorrect here.

prepatch_reproduced=True: Solution_prepatch.lean (always-column-0 routing) `bash scripts/lean_verify.sh prepatch.lean` -> exit 1, unsolved goals on `ensures_1` (fails exactly on a non-shared-pk ancestor), reproducing the bug the two F2P tests (test_mti_update_parent_through_child, test_mti_update_grand_parent_through_child) observe. atk_1 is an independent re-encoding of the same bug and also fails.

G-CONF independently re-run (`python conformance_check.py`) -> exit 0: R/I shadow of parentFilterIds agrees with the gold-patched pre_sql_setup column routing on 100006 checks (F2P boundary scenarios + fuzz, seed 15563), 0 disagreements. Confirms the deep model (stepCol/assignedColumns/idColumn) faithfully transliterates the gold routing.

refinement.md audit: all 7 legs are R (A1 related_updates order, A2 rows, A3 sharesChildPk -- type refinements) / I (A4 the fold loop, A5 related_ids_index, A6 idColumn projection -- concrete transliterations) / R+I (A7 per-ancestor pk__in consumption in get_related_updates). NO kind-3 (inexpressible-changed-op) leg: the operation that actually changed -- per-ancestor identity-column routing -- is modeled DEEPLY (spelled-out stepCol/assignedColumns fold + idColumn read), not hidden behind an axiom about the function under change. There are NO axiomatized callees and NO deep-model reference to a real callee, so G-AX is legitimately skip; sharesChildPk and rows are genuine free inputs (the pk-chain predicate and the pre-select are UNCHANGED by the patch; only which fetched column each ancestor reads changes, which is the modeled routing) and the spec holds universally over them, so no oracle borrowing. mapping.md bijection (Bool identity, row/list order preservation, column index identity) is sound. The A-legs' correspondence to the real callees (compiler.py:1839-1875 pre_sql_setup, subqueries.py:137 get_related_updates) holds.

Conclusion: >=5 distinct wrong impls attacked; all wrong impls fail verification via genuine postcondition discrimination; the one verifying non-gold impl (echo) resolves under the official harness. No verify-but-not-resolve counterexample exists. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-15563 velvet bundle. FINDINGS: (1) same_spec(Solution, Solution_prepatch, velvet)=True — the spec region (parentFilterIds signature + `ensures out = (assignedColumns parents).map (idColumn rows)` + pure helpers stepCol/assignedColumns/idColumn/cols_take_step) is byte-identical between patched and prepatch; spec view confirmed frozen. (2) Solution.lean elaborates clean (lean_verify exit 0, no sorry/error). (3) Solution_prepatch.lean FAILS (exit 1, unsolved goals at cols_take_step) — the always-column-0 prepatch cannot discharge the invariant for a non-shared-pk ancestor; G-DIFF holds, exactly the bug the two F2P MTI tests observe. (4) FAITHFULNESS: the deep model captures the gold-patched routing precisely. I re-derived the real gold-patched behaviour faithfully — pre_sql_setup building fields/related_ids_index (shared-pk ancestor→col 0; else→len(fields) then append), accumulation across multiple execute_sql(MULTI) cursor blocks into related_ids[parent], and get_related_updates consuming related_ids[model] one query per ancestor in related_updates order — and ran 300k independent differential inputs (n_parents 0..6, multiple cursor blocks, varied row widths) against the model's stepCol/assignedColumns/idColumn semantics: ZERO divergences. The bundle's own conformance_check.py (seed 15563, 100006 checks incl. both F2P scenarios) also passes with 0 disagreements. (5) The two abstracted facts (sharesChildPk, rows) are genuine free inputs over UNCHANGED repo code (the get_path_to_parent/join_field.primary_key pk-chain predicate and the SQL pre-select); the spec universally quantifies over them, so nothing is borrowed from an oracle and the spec is not too strong. The only partial op (row[idx]! default-on-OOB) is unreachable: the mapping bijection ties row width to len(fields)=number of assigned columns, which the real SELECT produces exactly. No reachable input makes the modeled function disagree with the real repo behaviour. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK passes (verified via leakage.screen: passed=True, no hard failures; recorded meta status 'pass', no relaxed_leakage flag). Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean)=True. Spec view contains NO patched repo symbols (no related_ids_index / related_updates / pre_sql_setup / add_filter / pk__in / execute_sql), NO patched file paths (compiler.py, subqueries.py), NO diff markers, NO reproduced gold-diff lines, and NO bug/fix narration. All spec identifiers are abstract (Parent, sharesChildPk, stepCol, assignedColumns, idColumn). Semantically, the modeled correct behavior — routing each ancestor's update filter to its own identity column (column 0 if it shares the child pk, a distinct fetched column otherwise) — does not exceed the public problem_statement, which already discloses that the multi-inheritance update wrongly filters the second parent (OtherBase) using the child/Base primary keys, with distinct pks (base_id vs otherbase_id) shown in the example. Modeling the intended correct behavior is the spec's legitimate role and reveals no localization/implementation of the gold edit beyond what the public task states.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
