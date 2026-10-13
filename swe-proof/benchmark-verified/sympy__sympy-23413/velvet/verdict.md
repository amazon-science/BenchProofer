# P2 adversarial audit — sympy__sympy-23413

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_3_no_kguard.lean`, `atk_4_offbyone.lean`, `atk_5_noop.lean`, `atk_6_diverge.lean`, `atk_7_kgt1.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,29 +128,29 @@
   ensures out = hnfResult numCols numRows A
   do
     -- impl-start
+    -- Pre-image skeleton: the number of rows considered is capped at
+    -- `min numRows numCols`, and there is no early stop once every column has a
+    -- pivot. When numRows > numCols this skips the top rows, so the frozen spec
+    -- (which reduces over ALL numRows rows) is not met and prove_correct MUST
+    -- fail.
     let mut mat : Mat := A
     let mut k := numCols
     let mut rowsLeft := numRows
-    while rowsLeft > 0 ∧ k > 0
+    let mut toProcess := min numRows numCols
+    while toProcess > 0
       invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
-      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
-      done_with rowsLeft = 0 ∨ k = 0
-      decreasing rowsLeft
+      invariant toProcess ≤ rowsLeft
+      done_with toProcess = 0
+      decreasing toProcess
     do
       let p := stepRow numCols mat k (rowsLeft - 1)
       mat := p.1
       k := p.2
       rowsLeft := rowsLeft - 1
+      toProcess := toProcess - 1
     return slice mat k
     -- impl-end
 end
 
 prove_correct hermiteNormalForm by
   loom_solve
-  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]
-    assumption
-  · simp only [hnfResult]
-    have hinv : reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k := by
-      assumption
-    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]
-    simp_all
```

Attack 2 — `atk_2_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -128,29 +128,9 @@
   ensures out = hnfResult numCols numRows A
   do
     -- impl-start
-    let mut mat : Mat := A
-    let mut k := numCols
-    let mut rowsLeft := numRows
-    while rowsLeft > 0 ∧ k > 0
-      invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
-      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
-      done_with rowsLeft = 0 ∨ k = 0
-      decreasing rowsLeft
-    do
-      let p := stepRow numCols mat k (rowsLeft - 1)
-      mat := p.1
-      k := p.2
-      rowsLeft := rowsLeft - 1
-    return slice mat k
+    return hnfResult numCols numRows A
     -- impl-end
 end
 
 prove_correct hermiteNormalForm by
   loom_solve
-  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]
-    assumption
-  · simp only [hnfResult]
-    have hinv : reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k := by
-      assumption
-    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]
-    simp_all
```

Attack 3 — `atk_3_no_kguard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,10 +131,10 @@
     let mut mat : Mat := A
     let mut k := numCols
     let mut rowsLeft := numRows
-    while rowsLeft > 0 ∧ k > 0
+    while rowsLeft > 0
       invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
       invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
-      done_with rowsLeft = 0 ∨ k = 0
+      done_with rowsLeft = 0
       decreasing rowsLeft
     do
       let p := stepRow numCols mat k (rowsLeft - 1)
```

Attack 4 — `atk_4_offbyone.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,10 +131,10 @@
     let mut mat : Mat := A
     let mut k := numCols
     let mut rowsLeft := numRows
-    while rowsLeft > 0 ∧ k > 0
+    while rowsLeft > 1 ∧ k > 0
       invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
       invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
-      done_with rowsLeft = 0 ∨ k = 0
+      done_with rowsLeft ≤ 1 ∨ k = 0
       decreasing rowsLeft
     do
       let p := stepRow numCols mat k (rowsLeft - 1)
```

Attack 5 — `atk_5_noop.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,29 +128,9 @@
   ensures out = hnfResult numCols numRows A
   do
     -- impl-start
-    let mut mat : Mat := A
-    let mut k := numCols
-    let mut rowsLeft := numRows
-    while rowsLeft > 0 ∧ k > 0
-      invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
-      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
-      done_with rowsLeft = 0 ∨ k = 0
-      decreasing rowsLeft
-    do
-      let p := stepRow numCols mat k (rowsLeft - 1)
-      mat := p.1
-      k := p.2
-      rowsLeft := rowsLeft - 1
-    return slice mat k
+    return slice A numCols
     -- impl-end
 end
 
 prove_correct hermiteNormalForm by
   loom_solve
-  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]
-    assumption
-  · simp only [hnfResult]
-    have hinv : reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k := by
-      assumption
-    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]
-    simp_all
```

Attack 6 — `atk_6_diverge.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,27 +130,13 @@
     -- impl-start
     let mut mat : Mat := A
     let mut k := numCols
-    let mut rowsLeft := numRows
-    while rowsLeft > 0 ∧ k > 0
-      invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
-      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
-      done_with rowsLeft = 0 ∨ k = 0
-      decreasing rowsLeft
+    while True
+      invariant True
     do
-      let p := stepRow numCols mat k (rowsLeft - 1)
-      mat := p.1
-      k := p.2
-      rowsLeft := rowsLeft - 1
+      mat := mat
     return slice mat k
     -- impl-end
 end
 
 prove_correct hermiteNormalForm by
   loom_solve
-  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]
-    assumption
-  · simp only [hnfResult]
-    have hinv : reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k := by
-      assumption
-    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]
-    simp_all
```

Attack 7 — `atk_7_kgt1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -131,10 +131,10 @@
     let mut mat : Mat := A
     let mut k := numCols
     let mut rowsLeft := numRows
-    while rowsLeft > 0 ∧ k > 0
+    while rowsLeft > 0 ∧ k > 1
       invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
       invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
-      done_with rowsLeft = 0 ∨ k = 0
+      done_with rowsLeft = 0 ∨ k ≤ 1
       decreasing rowsLeft
     do
       let p := stepRow numCols mat k (rowsLeft - 1)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real reduction is a bounded loop over the matrix rows
   (at most one pass per row, stopping early once every column has a pivot) and
   always terminates, so a diverging implementation must NOT satisfy this spec.
   Partial correctness would let a non-terminating loop discharge the
   postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An integer matrix in the working dense representation that the reduction
   mutates column-by-column. Its internal layout is irrelevant to the loop
   structure under specification — only that one and the same per-row reduction is
   applied to it, in order — so it is left fully opaque (directive 7: the
   weakest sufficient contract is none). The bijection to the repository value
   space is in mapping.md (G-AX / G-CONF use it). -/
axiom Mat : Type

/- A canonical matrix value, so an out-of-range probe has a harmless default.
   An UNCHANGED constructed value; left fully opaque. Provenance + soundness:
   mapping.md / axiom_check.py (G-AX). -/
axiom matDefault : Mat
noncomputable instance : Inhabited Mat := ⟨matDefault⟩

/- The single per-row reduction step, applied once to a single row of the matrix
   while assigning a pivot to a rightmost column. Given the column count, the
   current matrix, the current count of still-unassigned pivot columns, and the
   row index being processed, it returns the reduced matrix together with the
   updated count of unassigned pivot columns (the count drops by one when a
   pivot is successfully placed, and is unchanged when the row contributes no
   pivot). An UNCHANGED reduction callee the operation delegates to for every
   row; left fully opaque — the operation assumes nothing about the entries it
   produces, only that the SAME reduction is applied to each processed row.
   Provenance + executable soundness check: mapping.md §3 / axiom_check.py
   (G-AX). Tagged A-reference. -/
axiom stepRow : Nat → Mat → Nat → Nat → Mat × Nat

/- The final selection of the assigned pivot columns: keep the rightmost columns
   of the reduced matrix, starting from the first column that received a pivot.
   An UNCHANGED column-selection callee; left fully opaque. Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). Tagged
   A-reference. -/
axiom slice : Mat → Nat → Mat
-- axioms-end

-- pure-start
/- Reduce the matrix one row at a time, working from the bottom row upward.

   `numCols` is the number of columns; `rowsLeft` counts how many rows are still
   eligible to be processed (so the next row to process has index
   `rowsLeft - 1`); `mat` is the matrix being reduced; `k` is the count of
   columns that have not yet received a pivot.

   A row is processed only while there remains at least one column without a
   pivot: once every column has been assigned a pivot (`k = 0`), no further row
   can contribute, so processing stops immediately. Otherwise the same per-row
   reduction is applied to the current top-eligible row and the recursion
   continues on the remaining rows. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
noncomputable def reduceRows (numCols : Nat) : Nat → Mat → Nat → Mat × Nat
  | 0,     mat, k => (mat, k)
  | r + 1, mat, k =>
      if k = 0 then (mat, k)
      else
        let p := stepRow numCols mat k r
        reduceRows numCols r p.1 p.2

@[grind] lemma reduceRows_zero (numCols : Nat) (mat : Mat) (k : Nat) :
    reduceRows numCols 0 mat k = (mat, k) := rfl

@[grind] lemma reduceRows_succ (numCols r : Nat) (mat : Mat) (k : Nat) :
    reduceRows numCols (r + 1) mat k =
      (if k = 0 then (mat, k)
       else reduceRows numCols r (stepRow numCols mat k r).1 (stepRow numCols mat k r).2) := rfl

/- The final HNF selection: the matrix reduced over all eligible rows, then its
   pivot columns kept. -/
noncomputable def hnfResult (numCols numRows : Nat) (mat : Mat) : Mat :=
  let p := reduceRows numCols numRows mat numCols
  slice p.1 p.2

/- Processing stops with the matrix and pivot count unchanged exactly when there
   are no eligible rows left or every column already has a pivot. -/
lemma reduceRows_exit (numCols rowsLeft : Nat) (mat : Mat) (k : Nat)
    (h : rowsLeft = 0 ∨ k = 0) : reduceRows numCols rowsLeft mat k = (mat, k) := by
  cases rowsLeft with
  | zero => rfl
  | succ r =>
    rcases h with h | h
    · exact absurd h (Nat.succ_ne_zero r)
    · simp [reduceRows_succ, h]

/- The backward-fold step: with eligible rows remaining and a column still
   awaiting a pivot, the top-eligible row (index `rowsLeft - 1`) is reduced and
   the recursion continues on one fewer row. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma reduceRows_step (numCols rowsLeft : Nat) (mat : Mat) (k : Nat)
    (hr : 0 < rowsLeft) (hk : 0 < k) :
    reduceRows numCols rowsLeft mat k =
      reduceRows numCols (rowsLeft - 1)
        (stepRow numCols mat k (rowsLeft - 1)).1
        (stepRow numCols mat k (rowsLeft - 1)).2 := by
  obtain ⟨r, rfl⟩ : ∃ r, rowsLeft = r + 1 := ⟨rowsLeft - 1, by omega⟩
  have hk' : k ≠ 0 := by omega
  simp [reduceRows_succ, hk']
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the Hermite normal form of an integer matrix by the column-reduction
   algorithm.

   `A` is the read-only input matrix; `numRows` and `numCols` are its row and
   column counts. Desired behaviour: rows are reduced one at a time from the
   bottom upward, each placing a pivot in a rightmost column, continuing until
   either all rows have been processed or every column has received a pivot. The
   result keeps exactly the pivot columns of the fully reduced matrix. -/
noncomputable section
method hermiteNormalForm (A : Mat) (numRows : Nat) (numCols : Nat) return (out : Mat)
  ensures out = hnfResult numCols numRows A
  do
    -- impl-start
    let mut mat : Mat := A
    let mut k := numCols
    let mut rowsLeft := numRows
    while rowsLeft > 0 ∧ k > 0
      invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
      done_with rowsLeft = 0 ∨ k = 0
      decreasing rowsLeft
    do
      let p := stepRow numCols mat k (rowsLeft - 1)
      mat := p.1
      k := p.2
      rowsLeft := rowsLeft - 1
    return slice mat k
    -- impl-end
end

prove_correct hermiteNormalForm by
  loom_solve
  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]
    assumption
  · simp only [hnfResult]
    have hinv : reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k := by
      assumption
    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The frozen postcondition `out = hnfResult numCols numRows A` is a TOTAL-correctness functional equation with NO precondition; `hnfResult`/`reduceRows` concretely model the post-patch loop (process rows bottom-up from numRows with the k=0 early stop, then slice) over opaque A-references stepRow/slice. Therefore ANY verifying impl must produce exactly the post-patch output on all inputs -> its faithful refined patch is behaviourally the gold patch and resolves. verify => correct holds here.

Protocol executed from project root,. same_spec=True verified for ALL 7 attacks + pos_control against the frozen Solution.lean (swebench_unified.markers.same_spec, velvet). Verifications launched concurrently in 2 background batches of 4 (`bash scripts/lean_verify.sh <f>`).

### Results
- pos_control.lean: EXIT 0 (verifies, no sorry). Positive control OK.
- atk_1_prepatch.lean (min(m,n) row cap, no break — the ACTUAL pre-patch bug): EXIT 1 (fails to verify). Prepatch bug reproduced -> G-DIFF satisfied.
- atk_2_echo.lean (ungrounded-oracle echo: `return hnfResult numCols numRows A`): EXIT 0 (VERIFIES). The ONLY verifying wrong impl. Its faithful refined patch = gold patch (hnfResult refines exactly to post-patch _hermite_normal_form per mapping.md). Ran official harness: `run_resolve('sympy__sympy-23413', <patch>, retries=1, timeout=1800)` -> COMPLETED=True, RESOLVED=True, note='resolved', attempts=1. Per 2026-08-06 echo-attack policy a resolving echo is NOT a weakness. Does NOT break the spec.
- atk_3_no_kguard.lean (drop k>0 guard from while, call stepRow at k=0): EXIT 1 (fails; omega cannot discharge — invariant/exit no longer match reduceRows).
- atk_4_offbyone.lean (stop at rowsLeft>1, skip top row 0): EXIT 1 (fails; exit state != hnfResult).
- atk_5_noop.lean (`return slice A numCols`, no reduction): EXIT 1 (fails).
- atk_6_diverge.lean (`while True` non-terminating): EXIT 1 (fails) — 'Decreasing annotations are required in total correctness semantics'. Confirms TOTAL correctness is enforced: a diverging impl CANNOT vacuously discharge the post. This closes the classic partial-correctness spec-too-weak hole (refinement.md termination section is accurate).
- atk_7_kgt1.lean (stop one column early, k>1 guard): EXIT 1 (fails).

refinement.md leg audit: A1=R, A2=R+I, A3=I (changed control-flow modeled concretely by the while loop + reduceRows deep model), A4=A-reference (stepRow == unchanged per-row body add_columns/_gcdex), A5=I, A6=A-reference (slice == unchanged DomainMatrix.from_rep(A)[:, k:]). NO kind-3 leg. The two A-references cover UNCHANGED callees and correspond to the real repo body; axiom_check.py (G-AX) reconstructs the real pre-patch _hermite_normal_form EXACTLY over 13 boundary + 6000 fuzz matrices, and checks the k-1<=k'<=k pivot-count contract + determinism. Correspondence holds.

6/7 distinct wrong impls (prepatch cap, no-kguard, off-by-one, noop, diverge, k>1) correctly FAIL to verify; the single verifying impl (echo) resolves. No verifying wrong impl yields a non-resolving faithful patch. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1_prepatch.lean`, `atk_3_no_kguard.lean`, `atk_4_offbyone.lean`, `atk_5_noop.lean`, `atk_6_diverge.lean`, `atk_7_kgt1.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_2_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3_no_kguard.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_noop.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_diverge.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_kgt1.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real reduction is a bounded loop over the matrix rows
   (at most one pass per row, stopping early once every column has a pivot) and
   always terminates, so a diverging implementation must NOT satisfy this spec.
   Partial correctness would let a non-terminating loop discharge the
   postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An integer matrix in the working dense representation that the reduction
   mutates column-by-column. Its internal layout is irrelevant to the loop
   structure under specification — only that one and the same per-row reduction is
   applied to it, in order — so it is left fully opaque (directive 7: the
   weakest sufficient contract is none). The bijection to the repository value
   space is in mapping.md (G-AX / G-CONF use it). -/
axiom Mat : Type

/- A canonical matrix value, so an out-of-range probe has a harmless default.
   An UNCHANGED constructed value; left fully opaque. Provenance + soundness:
   mapping.md / axiom_check.py (G-AX). -/
axiom matDefault : Mat
noncomputable instance : Inhabited Mat := ⟨matDefault⟩

/- The single per-row reduction step, applied once to a single row of the matrix
   while assigning a pivot to a rightmost column. Given the column count, the
   current matrix, the current count of still-unassigned pivot columns, and the
   row index being processed, it returns the reduced matrix together with the
   updated count of unassigned pivot columns (the count drops by one when a
   pivot is successfully placed, and is unchanged when the row contributes no
   pivot). An UNCHANGED reduction callee the operation delegates to for every
   row; left fully opaque — the operation assumes nothing about the entries it
   produces, only that the SAME reduction is applied to each processed row.
   Provenance + executable soundness check: mapping.md §3 / axiom_check.py
   (G-AX). Tagged A-reference. -/
axiom stepRow : Nat → Mat → Nat → Nat → Mat × Nat

/- The final selection of the assigned pivot columns: keep the rightmost columns
   of the reduced matrix, starting from the first column that received a pivot.
   An UNCHANGED column-selection callee; left fully opaque. Provenance +
   executable soundness check: mapping.md §3 / axiom_check.py (G-AX). Tagged
   A-reference. -/
axiom slice : Mat → Nat → Mat
-- axioms-end

-- pure-start
/- Reduce the matrix one row at a time, working from the bottom row upward.

   `numCols` is the number of columns; `rowsLeft` counts how many rows are still
   eligible to be processed (so the next row to process has index
   `rowsLeft - 1`); `mat` is the matrix being reduced; `k` is the count of
   columns that have not yet received a pivot.

   A row is processed only while there remains at least one column without a
   pivot: once every column has been assigned a pivot (`k = 0`), no further row
   can contribute, so processing stops immediately. Otherwise the same per-row
   reduction is applied to the current top-eligible row and the recursion
   continues on the remaining rows. Front-recursive so a single unfold is
   available per loop step (the fold pattern, plan §5.4). -/
noncomputable def reduceRows (numCols : Nat) : Nat → Mat → Nat → Mat × Nat
  | 0,     mat, k => (mat, k)
  | r + 1, mat, k =>
      if k = 0 then (mat, k)
      else
        let p := stepRow numCols mat k r
        reduceRows numCols r p.1 p.2

@[grind] lemma reduceRows_zero (numCols : Nat) (mat : Mat) (k : Nat) :
    reduceRows numCols 0 mat k = (mat, k) := rfl

@[grind] lemma reduceRows_succ (numCols r : Nat) (mat : Mat) (k : Nat) :
    reduceRows numCols (r + 1) mat k =
      (if k = 0 then (mat, k)
       else reduceRows numCols r (stepRow numCols mat k r).1 (stepRow numCols mat k r).2) := rfl

/- The final HNF selection: the matrix reduced over all eligible rows, then its
   pivot columns kept. -/
noncomputable def hnfResult (numCols numRows : Nat) (mat : Mat) : Mat :=
  let p := reduceRows numCols numRows mat numCols
  slice p.1 p.2

/- Processing stops with the matrix and pivot count unchanged exactly when there
   are no eligible rows left or every column already has a pivot. -/
lemma reduceRows_exit (numCols rowsLeft : Nat) (mat : Mat) (k : Nat)
    (h : rowsLeft = 0 ∨ k = 0) : reduceRows numCols rowsLeft mat k = (mat, k) := by
  cases rowsLeft with
  | zero => rfl
  | succ r =>
    rcases h with h | h
    · exact absurd h (Nat.succ_ne_zero r)
    · simp [reduceRows_succ, h]

/- The backward-fold step: with eligible rows remaining and a column still
   awaiting a pivot, the top-eligible row (index `rowsLeft - 1`) is reduced and
   the recursion continues on one fewer row. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma reduceRows_step (numCols rowsLeft : Nat) (mat : Mat) (k : Nat)
    (hr : 0 < rowsLeft) (hk : 0 < k) :
    reduceRows numCols rowsLeft mat k =
      reduceRows numCols (rowsLeft - 1)
        (stepRow numCols mat k (rowsLeft - 1)).1
        (stepRow numCols mat k (rowsLeft - 1)).2 := by
  obtain ⟨r, rfl⟩ : ∃ r, rowsLeft = r + 1 := ⟨rowsLeft - 1, by omega⟩
  have hk' : k ≠ 0 := by omega
  simp [reduceRows_succ, hk']
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the Hermite normal form of an integer matrix by the column-reduction
   algorithm.

   `A` is the read-only input matrix; `numRows` and `numCols` are its row and
   column counts. Desired behaviour: rows are reduced one at a time from the
   bottom upward, each placing a pivot in a rightmost column, continuing until
   either all rows have been processed or every column has received a pivot. The
   result keeps exactly the pivot columns of the fully reduced matrix. -/
noncomputable section
method hermiteNormalForm (A : Mat) (numRows : Nat) (numCols : Nat) return (out : Mat)
  ensures out = hnfResult numCols numRows A
  do
    -- impl-start
    let mut mat : Mat := A
    let mut k := numCols
    let mut rowsLeft := numRows
    while rowsLeft > 0 ∧ k > 0
      invariant 0 ≤ rowsLeft ∧ rowsLeft ≤ numRows
      invariant reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k
      done_with rowsLeft = 0 ∨ k = 0
      decreasing rowsLeft
    do
      let p := stepRow numCols mat k (rowsLeft - 1)
      mat := p.1
      k := p.2
      rowsLeft := rowsLeft - 1
    return slice mat k
    -- impl-end
end

prove_correct hermiteNormalForm by
  loom_solve
  · rw [← reduceRows_step numCols rowsLeft mat k (by omega) (by omega)]
    assumption
  · simp only [hnfResult]
    have hinv : reduceRows numCols numRows A numCols = reduceRows numCols rowsLeft mat k := by
      assumption
    rw [hinv, reduceRows_exit numCols rowsLeft mat k (by omega)]
    simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The frozen postcondition `out = hnfResult numCols numRows A` is a TOTAL-correctness functional equation with NO precondition; `hnfResult`/`reduceRows` concretely model the post-patch loop (process rows bottom-up from numRows with the k=0 early stop, then slice) over opaque A-references stepRow/slice. Therefore ANY verifying impl must produce exactly the post-patch output on all inputs -> its faithful refined patch is behaviourally the gold patch and resolves. verify => correct holds here.

Protocol executed from project root,. same_spec=True verified for ALL 7 attacks + pos_control against the frozen Solution.lean (swebench_unified.markers.same_spec, velvet). Verifications launched concurrently in 2 background batches of 4 (`bash scripts/lean_verify.sh <f>`).

### Results
- pos_control.lean: EXIT 0 (verifies, no sorry). Positive control OK.
- atk_1_prepatch.lean (min(m,n) row cap, no break — the ACTUAL pre-patch bug): EXIT 1 (fails to verify). Prepatch bug reproduced -> G-DIFF satisfied.
- atk_2_echo.lean (ungrounded-oracle echo: `return hnfResult numCols numRows A`): EXIT 0 (VERIFIES). The ONLY verifying wrong impl. Its faithful refined patch = gold patch (hnfResult refines exactly to post-patch _hermite_normal_form per mapping.md). Ran official harness: `run_resolve('sympy__sympy-23413', <patch>, retries=1, timeout=1800)` -> COMPLETED=True, RESOLVED=True, note='resolved', attempts=1. Per 2026-08-06 echo-attack policy a resolving echo is NOT a weakness. Does NOT break the spec.
- atk_3_no_kguard.lean (drop k>0 guard from while, call stepRow at k=0): EXIT 1 (fails; omega cannot discharge — invariant/exit no longer match reduceRows).
- atk_4_offbyone.lean (stop at rowsLeft>1, skip top row 0): EXIT 1 (fails; exit state != hnfResult).
- atk_5_noop.lean (`return slice A numCols`, no reduction): EXIT 1 (fails).
- atk_6_diverge.lean (`while True` non-terminating): EXIT 1 (fails) — 'Decreasing annotations are required in total correctness semantics'. Confirms TOTAL correctness is enforced: a diverging impl CANNOT vacuously discharge the post. This closes the classic partial-correctness spec-too-weak hole (refinement.md termination section is accurate).
- atk_7_kgt1.lean (stop one column early, k>1 guard): EXIT 1 (fails).

refinement.md leg audit: A1=R, A2=R+I, A3=I (changed control-flow modeled concretely by the while loop + reduceRows deep model), A4=A-reference (stepRow == unchanged per-row body add_columns/_gcdex), A5=I, A6=A-reference (slice == unchanged DomainMatrix.from_rep(A)[:, k:]). NO kind-3 leg. The two A-references cover UNCHANGED callees and correspond to the real repo body; axiom_check.py (G-AX) reconstructs the real pre-patch _hermite_normal_form EXACTLY over 13 boundary + 6000 fuzz matrices, and checks the k-1<=k'<=k pivot-count contract + determinism. Correspondence holds.

6/7 distinct wrong impls (prepatch cap, no-kguard, off-by-one, noop, diverge, k>1) correctly FAIL to verify; the single verifying impl (echo) resolves. No verifying wrong impl yields a non-resolving faithful patch. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: could not break faithfulness. Findings:

1. SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean)=True — the spec view (imports, axioms Mat/matDefault/stepRow/slice, pure region reduceRows/hnfResult + lemmas, empty pre/post, method signature with `ensures out = hnfResult numCols numRows A`) is frozen. Prepatch differs ONLY in the impl region (capped `min numRows numCols` loop, no k=0 break) and correctly FAILS the postcondition (G-DIFF holds).

2. LEAN: Solution.lean elaborates cleanly, exit 0 (no sorry/error), 300s wall.

3. G-CONF (bundle, model loop structure + REAL callees vs PATCHED _hermite_normal_form, seed 23413): ran against — 0/100000 disagreements.

4. G-AX (bundle, stepRow/slice recompose real PRE-patch callee): ran against — passes on 13 boundary + 6000 fuzz; pivot-count contract k-1<=k'<=k holds.

5. INDEPENDENT DIFFERENTIAL (my own, not the pinned seed): modeled hnfResult (reduce over ALL numRows rows bottom-up with the k=0 early stop, then slice) vs patched _hermite_normal_form. 160000 inputs across 4 fresh seeds, shapes up to 9x9, magnitudes up to 1e12, incl. the m>n bug regime. 0 divergences.

The modeled function agrees with the real patched callee on every tested input. The changed operation (all rows eligible instead of min(m,n), with early stop) is modeled deeply/concretely (reduceRows + while loop), not axiomatized. The two opaque A-references (stepRow, slice) are genuinely unchanged by the gold patch and match the real body. TOTAL correctness + decreasing rowsLeft rules out vacuous discharge by a non-terminating impl. No input where the spec disagrees with the real repo behavior was found. Spec is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction judgment for velvet bundle sympy__sympy-23413. Spec-view integrity: same_spec(Solution, Solution_prepatch) = True (frozen spec region byte-identical). Mechanical G-LEAK screen (leakage.screen) PASSES with zero hard failures.

Gold edit: in _hermite_normal_form, remove the `rows = min(m, n)` cap and the bounded `for i in range(m-1, m-1-rows, -1)`, replacing with `for i in range(m-1, -1, -1)` plus an early `if k == 0: break`. The discriminating delta is the pre-patch min(m,n) row cap.

What the consumer spec view actually exposes: the pure model reduceRows/hnfResult and the postcondition `ensures out = hnfResult numCols numRows A`. The gold-equivalent `while` impl and the proof are ELIDED ("implementation elided"/"proof elided"). No reconstruction of the gold edit beyond problem_statement, for these reasons:
1. L1 clean: no diff markers, no gold-patch line reproduced.
2. L2 clean: patched file path sympy/polys/matrices/normalforms.py and dotted module path do NOT appear in the spec view.
3. Pre-patch state is NOT disclosed: the spec view never names the removed `rows = min(m,n)` cap or the bounded range. The buggy-vs-fixed delta lives only in mapping.md/refinement.md (auditor docs, not the consumer spec view). Without the pre-patch behavior the reader cannot reconstruct WHAT the edit changed from the spec view alone.
4. L3 clean: no bug/fix/previously/incorrectly narration in comments; comments describe correct target behavior abstractly.
5. Symbol check: the only distinctive changed symbol is `hermite_normal_form`, and it appears VERBATIM in the public problem_statement (`hermite_normal_form(Matrix(...))`), so it is already public — not a leak.

The spec necessarily encodes correct behavior (bottom-up row reduction, pivot in rightmost columns, k=0 early stop, keep pivot columns). Encoding the correct functional contract is the legitimate, accepted setup and is not gold-edit leakage: it localizes no edit beyond the publicly-named function, quotes no patch line, and does not reveal the removed min(m,n) cap that constitutes the actual fix. No RELAXED_LEAKAGE.md present and none needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
