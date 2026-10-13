# P2 adversarial audit — scikit-learn__scikit-learn-14894

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk1_always_empty.lean`, `atk2_wrong_boundary.lean`, `atk3_drop_data.lean`, `atk4_swap_shape.lean`, `atk5_wrong_indptr.lean`, `atk6_abort_nonempty.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_rows0_divergent.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is fully-pinned: problem_spec_dualCoef requires Except.ok for ALL inputs and pins every output field (data, indices, indptr, nrows, ncols) to the inputs in BOTH the width=0 and width!=0 branches. Under the precondition 1<=rows the output is uniquely determined for every reachable input, so any closing impl is extensionally equal to gold on the whole modeled domain. The only divergent-but-closing impl found (atk7) diverges solely at rows=0 (n_class=0), which is excluded by 1<=rows AND unreachable in real sklearn (n_class=len(classes_)-1>=1 for clf, =1 for regression); its faithful patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,9 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
   let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
   if width = 0 then
-    return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
+    return Except.error "row-offset construction aborted: zero spacing step"
   let indptr := rowOffsets rows width
   return Except.ok
     { data := data, indices := indices, indptr := indptr,
@@ -89,13 +85,13 @@
       (implementation_dualCoef width rows data) := by
   unfold problem_spec_dualCoef implementation_dualCoef
   by_cases h : width = 0
-  · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-    · intro hne; exact absurd h hne
-  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
-        CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
+  · subst h
+    refine ⟨emptyCSR α, by simp [Id.run, pure], ?_, ?_⟩
+    · intro _; simp [emptyCSR]
+    · intro hne; exact absurd rfl hne
+  · refine ⟨{ data := data, indices := tileRange width rows,
+              indptr := rowOffsets rows width, nrows := rows, ncols := width },
+            by simp only [Id.run, h, if_false]; rfl, ?_, ?_⟩
     · intro h0; exact absurd h0 h
     · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 2 — `atk1_always_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,7 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
-  let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
-  if width = 0 then
-    return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
-  let indptr := rowOffsets rows width
-  return Except.ok
-    { data := data, indices := indices, indptr := indptr,
-      nrows := rows, ncols := width }
+  return Except.ok (emptyCSR α)
 -- impl-end
 
 -- proof-start
@@ -88,14 +78,8 @@
     problem_spec_dualCoef width rows data
       (implementation_dualCoef width rows data) := by
   unfold problem_spec_dualCoef implementation_dualCoef
-  by_cases h : width = 0
-  · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-    · intro hne; exact absurd h hne
-  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
-        CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
-    · intro h0; exact absurd h0 h
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  refine ⟨emptyCSR α, ?_, ?_, ?_⟩
+  · simp [Id.run]
+  · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  · intro hne; simp [emptyCSR]
 -- proof-end
```

Attack 3 — `atk2_wrong_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,13 +69,9 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
   let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
-  if width = 0 then
+  if rows = 0 then
     return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
   let indptr := rowOffsets rows width
   return Except.ok
     { data := data, indices := indices, indptr := indptr,
@@ -88,14 +84,13 @@
     problem_spec_dualCoef width rows data
       (implementation_dualCoef width rows data) := by
   unfold problem_spec_dualCoef implementation_dualCoef
-  by_cases h : width = 0
-  · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-    · intro hne; exact absurd h hne
-  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
-        CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
-    · intro h0; exact absurd h0 h
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  have hr : rows ≠ 0 := by omega
+  refine ⟨{ data := data, indices := tileRange width rows,
+            indptr := rowOffsets rows width, nrows := rows, ncols := width },
+          by simp only [Id.run, hr, if_false]; rfl, ?_, ?_⟩
+  · intro h0
+    -- width = 0 branch: spec requires empty fields but impl gives full record
+    simp only [tileRange, tileCopies, h0, List.range_zero]
+    sorry
+  · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

Attack 4 — `atk3_drop_data.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,16 +69,12 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
   let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
   if width = 0 then
     return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
   let indptr := rowOffsets rows width
   return Except.ok
-    { data := data, indices := indices, indptr := indptr,
+    { data := [], indices := indices, indptr := indptr,
       nrows := rows, ncols := width }
 -- impl-end
 
@@ -90,12 +86,15 @@
   unfold problem_spec_dualCoef implementation_dualCoef
   by_cases h : width = 0
   · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
+    · simp only [Id.run, h]; rfl
     · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
     · intro hne; exact absurd h hne
-  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
+  · refine ⟨(⟨[], tileRange width rows, rowOffsets rows width, rows, width⟩ :
         CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
+    · simp only [Id.run, h]; rfl
     · intro h0; exact absurd h0 h
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+    · intro _
+      -- spec requires m.data = data but impl gives []
+      refine ⟨?_, rfl, rfl, rfl, rfl⟩
+      sorry
 -- proof-end
```

Attack 5 — `atk4_swap_shape.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,13 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
   let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
   if width = 0 then
     return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
   let indptr := rowOffsets rows width
   return Except.ok
     { data := data, indices := indices, indptr := indptr,
-      nrows := rows, ncols := width }
+      nrows := width, ncols := rows }
 -- impl-end
 
 -- proof-start
@@ -90,12 +86,15 @@
   unfold problem_spec_dualCoef implementation_dualCoef
   by_cases h : width = 0
   · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
+    · simp only [Id.run, h]; rfl
     · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
     · intro hne; exact absurd h hne
-  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
+  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, width, rows⟩ :
         CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
+    · simp only [Id.run, h]; rfl
     · intro h0; exact absurd h0 h
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+    · intro _
+      refine ⟨rfl, rfl, rfl, ?_, ?_⟩
+      · sorry
+      · sorry
 -- proof-end
```

Attack 6 — `atk5_wrong_indptr.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,14 +69,10 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
   let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
   if width = 0 then
     return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
-  let indptr := rowOffsets rows width
+  let indptr := rowOffsets width rows
   return Except.ok
     { data := data, indices := indices, indptr := indptr,
       nrows := rows, ncols := width }
@@ -90,12 +86,14 @@
   unfold problem_spec_dualCoef implementation_dualCoef
   by_cases h : width = 0
   · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
+    · simp only [Id.run, h]; rfl
     · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
     · intro hne; exact absurd h hne
-  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
+  · refine ⟨(⟨data, tileRange width rows, rowOffsets width rows, rows, width⟩ :
         CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
+    · simp only [Id.run, h]; rfl
     · intro h0; exact absurd h0 h
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+    · intro _
+      refine ⟨rfl, rfl, ?_, rfl, rfl⟩
+      sorry
 -- proof-end
```

Attack 7 — `atk6_abort_nonempty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,17 +69,9 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
-  let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
   if width = 0 then
     return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
-  let indptr := rowOffsets rows width
-  return Except.ok
-    { data := data, indices := indices, indptr := indptr,
-      nrows := rows, ncols := width }
+  return Except.error "not implemented"
 -- impl-end
 
 -- proof-start
@@ -90,12 +82,10 @@
   unfold problem_spec_dualCoef implementation_dualCoef
   by_cases h : width = 0
   · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
+    · simp only [Id.run, h]; rfl
     · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
     · intro hne; exact absurd h hne
-  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
-        CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
-    · intro h0; exact absurd h0 h
-    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
+  · -- non-empty branch returns Except.error, spec needs Except.ok
+    exfalso
+    sorry
 -- proof-end
```

Attack 8 — `atk7_rows0_divergent.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,14 +69,14 @@
 -- impl-start
 def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
     Except String (CSRMatrix α) := Id.run do
-  -- the column indices: the support ramp repeated once per class
-  let indices := tileRange width rows
-  -- empty support set ⇒ return the canonical empty matrix instead of building
-  -- evenly spaced row offsets (which would require stepping by the support size)
   if width = 0 then
     return Except.ok (emptyCSR α)
-  -- non-empty: evenly spaced row offsets and the full block matrix
+  if rows = 0 then
+    -- diverges from gold here, but this input is excluded by the precondition
+    -- 1 ≤ rows and never occurs in the real code (n_class ≥ 1)
+    return Except.error "unreachable: zero classes"
   let indptr := rowOffsets rows width
+  let indices := tileRange width rows
   return Except.ok
     { data := data, indices := indices, indptr := indptr,
       nrows := rows, ncols := width }
@@ -88,14 +88,15 @@
     problem_spec_dualCoef width rows data
       (implementation_dualCoef width rows data) := by
   unfold problem_spec_dualCoef implementation_dualCoef
+  have hr : rows ≠ 0 := by omega
   by_cases h : width = 0
   · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_true]; rfl
+    · simp only [Id.run, h]; rfl
     · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
     · intro hne; exact absurd h hne
   · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
         CSRMatrix α), ?_, ?_, ?_⟩
-    · simp only [Id.run, h, if_false]; rfl
+    · simp only [Id.run, h, hr, if_false]; rfl
     · intro h0; exact absurd h0 h
     · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The operations the change
-- guards — building the repeated column-index block, the row-offset vector, and
-- assembling the compressed-sparse-row record — are modeled DIRECTLY (deep
-- model) as the `tileRange` / `List.range`-map helpers and record fields below,
-- not axiomatized. The proof agent may add `_prop` axioms only if genuinely
-- stuck.
-- axioms-end

-- pure-start
/-- A compressed-sparse-row matrix: the three parallel storage arrays plus the
logical shape. `data` holds the stored values, `indices` the column index of
each stored value, `indptr` the per-row start offsets (length `nrows + 1`). -/
structure CSRMatrix (α : Type) where
  data : List α
  indices : List Nat
  indptr : List Nat
  nrows : Nat
  ncols : Nat
deriving Repr

/-- `nClass` copies of `block`, concatenated front-first (front-recursive). -/
def tileCopies (block : List Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => block ++ tileCopies block n

/-- The column-index vector: the contiguous block `[0, 1, …, width-1]` repeated
`copies` times. Models repeating a ramp `copies` times. -/
def tileRange (width copies : Nat) : List Nat :=
  tileCopies (List.range width) copies

/-- The row-offset vector `[0, width, 2·width, …, rows·width]` (length
`rows + 1`): the evenly spaced offsets stepping by `width`. -/
def rowOffsets (rows width : Nat) : List Nat :=
  (List.range (rows + 1)).map (· * width)

/-- The canonical empty sparse matrix: no stored values, a single (degenerate)
row offset pair, shape one-by-zero. -/
def emptyCSR (α : Type) : CSRMatrix α :=
  { data := [], indices := [], indptr := [0, 0], nrows := 1, ncols := 0 }
-- pure-end

-- post-conditions-start
/-- The coefficient matrix assembled from a stored coefficient buffer `data`, a
support-set size `width`, and a per-class repeat count `rows`.

The assembly must always succeed (return a matrix, never abort). When the
support set is empty (`width = 0`) the result is the canonical empty matrix.
Otherwise the result is the block matrix whose stored values are exactly the
supplied buffer, whose column indices are the support ramp repeated once per
class, whose row offsets are evenly spaced by the support-set size, and whose
shape is `rows × width`. Every output component is pinned to the inputs. -/
def problem_spec_dualCoef {α : Type} (width rows : Nat) (data : List α)
    (result : Except String (CSRMatrix α)) : Prop :=
  ∃ m : CSRMatrix α, result = Except.ok m ∧
    (width = 0 →
      m.data = [] ∧ m.indices = [] ∧ m.indptr = [0, 0] ∧
      m.nrows = 1 ∧ m.ncols = 0) ∧
    (width ≠ 0 →
      m.data = data ∧
      m.indices = tileRange width rows ∧
      m.indptr = rowOffsets rows width ∧
      m.nrows = rows ∧ m.ncols = width)
-- post-conditions-end

-- impl-start
def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
    Except String (CSRMatrix α) := Id.run do
  if h : width = 0 then
    return Except.ok (emptyCSR α)
  else
    -- build offsets and indices then assemble (reordered from gold, same result)
    let indptr := rowOffsets rows width
    let indices := tileRange width rows
    return Except.ok
      { data := data, indices := indices, indptr := indptr,
        nrows := rows, ncols := width }
-- impl-end

-- proof-start
theorem correct_dualCoef {α : Type} (width rows : Nat) (data : List α)
    (hrows : 1 ≤ rows) :
    problem_spec_dualCoef width rows data
      (implementation_dualCoef width rows data) := by
  unfold problem_spec_dualCoef implementation_dualCoef
  by_cases h : width = 0
  · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
    · simp only [Id.run, h]; rfl
    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
    · intro hne; exact absurd h hne
  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
        CSRMatrix α), ?_, ?_, ?_⟩
    · simp only [Id.run, h]; rfl
    · intro h0; exact absurd h0 h
    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all; verifier=lean_verify.sh, exit 0=verifies/no-sorry, 1=error, 3=sorry). same_spec=True confirmed for all 8 attack files + positive control via swebench_unified.markers.same_spec (spec regions byte-identical).

### VERIFY RESULTS (ran concurrently, <=4 background jobs):
- pos_control.lean (echo/reordered gold, semantically identical): EXIT 0. #print axioms correct_dualCoef => [propext] (clean, no sorryAx/_prop). POSITIVE CONTROL verifies.
- atk_prepatch.lean (prepatch ZeroDivisionError bug reproduced: Except.error on width=0): EXIT 1, unsolved goal `⊢ False` in width=0 branch. Bug is DISCRIMINATED by the spec (prepatch_reproduced=true).
- atk1_always_empty.lean (partial-domain, always emptyCSR): EXIT 1, unsolved `data=[] ∧ tileRange width rows=[] ∧ ... ∧ 0=width` in width!=0 leg. Does NOT close.
- atk2_wrong_boundary.lean (branch on rows=0 not width=0): EXIT 3 (sorry) — full record supplied in width=0 case violates pinned empty fields.
- atk3_drop_data.lean (control-flow-effect: data:=[] in non-empty branch): EXIT 3 (sorry) — spec pins m.data=data.
- atk4_swap_shape.lean (nrows/ncols swapped): EXIT 3 (sorry) — spec pins nrows=rows, ncols=width.
- atk5_wrong_indptr.lean (rowOffsets args swapped width<->rows): EXIT 3 (sorry) — spec pins indptr=rowOffsets rows width.
- atk6_abort_nonempty.lean (ungrounded-oracle echo: Except.error when width!=0): EXIT 3 (sorry) — spec requires Except.ok everywhere.
- atk7_rows0_divergent.lean (gold on reachable domain, Except.error only at rows=0): EXIT 0. #print axioms => [propext, Quot.sound] (both standard, clean). This is the ONLY wrong-shaped impl whose proof CLOSES with clean axioms.

MANDATORY RESOLVE STEP: atk7 is the only closing-clean-axiom impl, so per protocol its faithful refined patch (atk7_faithful.patch: adds a dead `elif not n_class: raise ValueError` guard mirroring the Lean rows=0 branch, gold's fix otherwise verbatim) was materialized and run through the official harness:
  run_resolve('scikit-learn__scikit-learn-14894', atk7_faithful.patch, timeout=1800)
  => COMPLETED=True, RESOLVED=True, ATTEMPTS=1, NOTE='resolved' (atk7_resolve.log).
The divergence is on an input the hidden tests never exercise (n_class>=1 always), so verify AND correct agree. No verify⇏correct gap.

REFINEMENT.MD AUDIT: 5 legs, all tagged R (legs 1,2,3,4: type-refinement deep models of np.tile∘arange, sp.csr_matrix([]) sentinel, np.arange offsets, CSR triple->record) or I (leg 5: no-abort). NO A-consumed and NO A-reference legs exist (axioms region empty; axiom_check.py is a skip stub; meta.json axioms=[], deep_model_references=[]). No kind-3 leg. Since there are zero A-legs there is no callee-correspondence that could fail; the deep models are instead validated by G-CONF (recorded pass: 120005 inputs, 0 disagreements, seed 14894) and I confirmed the model↔patch correspondence matches the gold patch.diff (if not n_SV: sp.csr_matrix([]) else the arange/csr build) and mapping.md (width=n_SV, rows=n_class>=1, data=dual_coef_data).

VERDICT: SOUND. >=5 distinct wrong impls (8 attacks: partial-domain, wrong-boundary, control-flow-effect x2, ungrounded-oracle-echo, wrong-indptr, prepatch-bug, and the divergent-unreachable atk7) attempted; none produces a verify⇏correct gap. The one closing-clean-axiom impl (atk7) had its faithful patch executed through run_resolve and it RESOLVED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_prepatch.lean`, `atk1_always_empty.lean`, `atk2_wrong_boundary.lean`, `atk3_drop_data.lean`, `atk4_swap_shape.lean`, `atk5_wrong_indptr.lean`, `atk6_abort_nonempty.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7_rows0_divergent.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is fully-pinned: problem_spec_dualCoef requires Except.ok for ALL inputs and pins every output field (data, indices, indptr, nrows, ncols) to the inputs in BOTH the width=0 and width!=0 branches. Under the precondition 1<=rows the output is uniquely determined for every reachable input, so any closing impl is extensionally equal to gold on the whole modeled domain. The only divergent-but-closing impl found (atk7) diverges solely at rows=0 (n_class=0), which is excluded by 1<=rows AND unreachable in real sklearn (n_class=len(classes_)-1>=1 for clf, =1 for regression); its faithful patch RESOLVES.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk1_always_empty.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2_wrong_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk3_drop_data.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk4_swap_shape.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk5_wrong_indptr.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk6_abort_nonempty.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk7_rows0_divergent.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The operations the change
-- guards — building the repeated column-index block, the row-offset vector, and
-- assembling the compressed-sparse-row record — are modeled DIRECTLY (deep
-- model) as the `tileRange` / `List.range`-map helpers and record fields below,
-- not axiomatized. The proof agent may add `_prop` axioms only if genuinely
-- stuck.
-- axioms-end

-- pure-start
/-- A compressed-sparse-row matrix: the three parallel storage arrays plus the
logical shape. `data` holds the stored values, `indices` the column index of
each stored value, `indptr` the per-row start offsets (length `nrows + 1`). -/
structure CSRMatrix (α : Type) where
  data : List α
  indices : List Nat
  indptr : List Nat
  nrows : Nat
  ncols : Nat
deriving Repr

/-- `nClass` copies of `block`, concatenated front-first (front-recursive). -/
def tileCopies (block : List Nat) : Nat → List Nat
  | 0 => []
  | n + 1 => block ++ tileCopies block n

/-- The column-index vector: the contiguous block `[0, 1, …, width-1]` repeated
`copies` times. Models repeating a ramp `copies` times. -/
def tileRange (width copies : Nat) : List Nat :=
  tileCopies (List.range width) copies

/-- The row-offset vector `[0, width, 2·width, …, rows·width]` (length
`rows + 1`): the evenly spaced offsets stepping by `width`. -/
def rowOffsets (rows width : Nat) : List Nat :=
  (List.range (rows + 1)).map (· * width)

/-- The canonical empty sparse matrix: no stored values, a single (degenerate)
row offset pair, shape one-by-zero. -/
def emptyCSR (α : Type) : CSRMatrix α :=
  { data := [], indices := [], indptr := [0, 0], nrows := 1, ncols := 0 }
-- pure-end

-- post-conditions-start
/-- The coefficient matrix assembled from a stored coefficient buffer `data`, a
support-set size `width`, and a per-class repeat count `rows`.

The assembly must always succeed (return a matrix, never abort). When the
support set is empty (`width = 0`) the result is the canonical empty matrix.
Otherwise the result is the block matrix whose stored values are exactly the
supplied buffer, whose column indices are the support ramp repeated once per
class, whose row offsets are evenly spaced by the support-set size, and whose
shape is `rows × width`. Every output component is pinned to the inputs. -/
def problem_spec_dualCoef {α : Type} (width rows : Nat) (data : List α)
    (result : Except String (CSRMatrix α)) : Prop :=
  ∃ m : CSRMatrix α, result = Except.ok m ∧
    (width = 0 →
      m.data = [] ∧ m.indices = [] ∧ m.indptr = [0, 0] ∧
      m.nrows = 1 ∧ m.ncols = 0) ∧
    (width ≠ 0 →
      m.data = data ∧
      m.indices = tileRange width rows ∧
      m.indptr = rowOffsets rows width ∧
      m.nrows = rows ∧ m.ncols = width)
-- post-conditions-end

-- impl-start
def implementation_dualCoef {α : Type} (width rows : Nat) (data : List α) :
    Except String (CSRMatrix α) := Id.run do
  if h : width = 0 then
    return Except.ok (emptyCSR α)
  else
    -- build offsets and indices then assemble (reordered from gold, same result)
    let indptr := rowOffsets rows width
    let indices := tileRange width rows
    return Except.ok
      { data := data, indices := indices, indptr := indptr,
        nrows := rows, ncols := width }
-- impl-end

-- proof-start
theorem correct_dualCoef {α : Type} (width rows : Nat) (data : List α)
    (hrows : 1 ≤ rows) :
    problem_spec_dualCoef width rows data
      (implementation_dualCoef width rows data) := by
  unfold problem_spec_dualCoef implementation_dualCoef
  by_cases h : width = 0
  · refine ⟨emptyCSR α, ?_, ?_, ?_⟩
    · simp only [Id.run, h]; rfl
    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
    · intro hne; exact absurd h hne
  · refine ⟨(⟨data, tileRange width rows, rowOffsets rows width, rows, width⟩ :
        CSRMatrix α), ?_, ?_, ?_⟩
    · simp only [Id.run, h]; rfl
    · intro h0; exact absurd h0 h
    · intro _; exact ⟨rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE (all; verifier=lean_verify.sh, exit 0=verifies/no-sorry, 1=error, 3=sorry). same_spec=True confirmed for all 8 attack files + positive control via swebench_unified.markers.same_spec (spec regions byte-identical).

### VERIFY RESULTS (ran concurrently, <=4 background jobs):
- pos_control.lean (echo/reordered gold, semantically identical): EXIT 0. #print axioms correct_dualCoef => [propext] (clean, no sorryAx/_prop). POSITIVE CONTROL verifies.
- atk_prepatch.lean (prepatch ZeroDivisionError bug reproduced: Except.error on width=0): EXIT 1, unsolved goal `⊢ False` in width=0 branch. Bug is DISCRIMINATED by the spec (prepatch_reproduced=true).
- atk1_always_empty.lean (partial-domain, always emptyCSR): EXIT 1, unsolved `data=[] ∧ tileRange width rows=[] ∧ ... ∧ 0=width` in width!=0 leg. Does NOT close.
- atk2_wrong_boundary.lean (branch on rows=0 not width=0): EXIT 3 (sorry) — full record supplied in width=0 case violates pinned empty fields.
- atk3_drop_data.lean (control-flow-effect: data:=[] in non-empty branch): EXIT 3 (sorry) — spec pins m.data=data.
- atk4_swap_shape.lean (nrows/ncols swapped): EXIT 3 (sorry) — spec pins nrows=rows, ncols=width.
- atk5_wrong_indptr.lean (rowOffsets args swapped width<->rows): EXIT 3 (sorry) — spec pins indptr=rowOffsets rows width.
- atk6_abort_nonempty.lean (ungrounded-oracle echo: Except.error when width!=0): EXIT 3 (sorry) — spec requires Except.ok everywhere.
- atk7_rows0_divergent.lean (gold on reachable domain, Except.error only at rows=0): EXIT 0. #print axioms => [propext, Quot.sound] (both standard, clean). This is the ONLY wrong-shaped impl whose proof CLOSES with clean axioms.

MANDATORY RESOLVE STEP: atk7 is the only closing-clean-axiom impl, so per protocol its faithful refined patch (atk7_faithful.patch: adds a dead `elif not n_class: raise ValueError` guard mirroring the Lean rows=0 branch, gold's fix otherwise verbatim) was materialized and run through the official harness:
  run_resolve('scikit-learn__scikit-learn-14894', atk7_faithful.patch, timeout=1800)
  => COMPLETED=True, RESOLVED=True, ATTEMPTS=1, NOTE='resolved' (atk7_resolve.log).
The divergence is on an input the hidden tests never exercise (n_class>=1 always), so verify AND correct agree. No verify⇏correct gap.

REFINEMENT.MD AUDIT: 5 legs, all tagged R (legs 1,2,3,4: type-refinement deep models of np.tile∘arange, sp.csr_matrix([]) sentinel, np.arange offsets, CSR triple->record) or I (leg 5: no-abort). NO A-consumed and NO A-reference legs exist (axioms region empty; axiom_check.py is a skip stub; meta.json axioms=[], deep_model_references=[]). No kind-3 leg. Since there are zero A-legs there is no callee-correspondence that could fail; the deep models are instead validated by G-CONF (recorded pass: 120005 inputs, 0 disagreements, seed 14894) and I confirmed the model↔patch correspondence matches the gold patch.diff (if not n_SV: sp.csr_matrix([]) else the arange/csr build) and mapping.md (width=n_SV, rows=n_class>=1, data=dual_coef_data).

VERDICT: SOUND. >=5 distinct wrong impls (8 attacks: partial-domain, wrong-boundary, control-flow-effect x2, ungrounded-oracle-echo, wrong-indptr, prepatch-bug, and the divergent-unreachable atk7) attempted; none produces a verify⇏correct gap. The one closing-clean-axiom impl (atk7) had its faithful patch executed through run_resolve and it RESOLVED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. Checks performed: (1) same_spec regions (axioms/pure/post-conditions) are byte-identical between Solution.lean and Solution_prepatch.lean. (2) Solution.lean compiles via lean_verify.sh (exit 0, no sorry). (3) #print axioms correct_dualCoef => [propext, Quot.sound] only — no sorryAx, proof is genuine. (4) Live scipy ground truth: sp.csr_matrix([]) yields data=[], indices=[], indptr=[0,0], shape=(1,0), exactly matching emptyCSR (nrows=1, ncols=0). (5) Differential test of the modeled tileRange/rowOffsets/shape against real np.tile/np.arange/sp.csr_matrix over n_SV in 0..24, n_class in 1..6 (including the n_SV=0 boundary): 0 diverging cases. The np.arange step size/n_class equals exactly n_SV (integer since size=n_class*n_SV), so indptr=[0,n_SV,...,n_class*n_SV] length n_class+1 equals rowOffsets. The spec is neither too strong nor drifted: every reachable input agrees with the real post-patch callee, and the post-condition pins outputs to inputs correctly in both the empty (width=0) and non-empty branches. Precondition 1<=rows (n_class>=1) matches the real invariant (len(classes_)-1 for clf, 1 for regression). No spec-too-strong defect found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Role: leakage / gold-reconstruction on the CONSUMER SPEC VIEW (impl+proof elided).

Mechanical G-LEAK screen: PASS (leakage.screen → passed=True, hard_failures=[]). No diff markers, no gold-patch line reproduced (the gold's `if not n_SV:` / `sp.csr_matrix([])` do not appear in the Lean view), patched path `sklearn/svm/base.py` absent, changed-symbol set {sparse_fit} not embedded in any spec-view identifier or comment, no narration terms. same_spec(Solution, Solution_prepatch)=True and spec region hashes are stable — spec not tailored to gold.

Semantic judgement — nothing in the spec view exceeds the public problem_statement:
1. The impl branch that mirrors the gold guard (`if width = 0 then return emptyCSR`) lives in the ELIDED impl region; the consumer never sees it. The proof region is likewise elided.
2. The post-condition's `width = 0 → empty CSR` case (data [], indices [], indptr [0,0], shape 1×0) is exactly the behavior the public problem_statement already mandates: "Expected Results: No error is thrown and `self.dual_coef_ = sp.csr_matrix([])`". The specific attributes of the empty matrix (indptr [0,0], shape (1,0)) are inherent, documented properties of the named scipy object, not new gold information.
3. The branch discriminator (empty vs non-empty support set) is the public bug condition ("support_vectors_ attribute is empty"); the crash locus (row-offset build, `dual_coef_indices.size / n_class`) is spelled out in the public traceback.
4. Comments describe the abstract model (tileRange/rowOffsets/CSR record) and reference only what the public traceback already pins — no edit-localization beyond problem_statement.

The spec view reveals only the required post-condition behavior that is already public; it does not disclose the gold edit's structure/location beyond problem_statement. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
