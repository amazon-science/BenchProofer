# P2 adversarial audit — scikit-learn__scikit-learn-14894

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. This is an answer-key spec: `ensures out = sparseFitSpec nSV nClass dataLen` fully pins the output over the whole domain (nClass>=1), with zero consumed axioms (meta.json axioms=[]). Any verifying impl is extensionally equal to sparseFitSpec, so no verifying-but-wrong impl can exist. The one remaining break vector (sparseFitSpec != gold on a tested input, i.e. an A-leg / model-patch divergence) does NOT occur: the faithful refined patch of the verifying impls (= gold hunk verbatim by the refinement map) RESOLVES under the official harness.
```

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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,20 +110,13 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
     let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
-      if nSV = 0 then
-        Except.ok emptyResult
-      else
-        match arangeIndptr nSV nClass with
-        | Except.ok indptr =>
-            Except.ok { dataLen := dataLen, indices := indices,
-                        indptr := indptr, rows := nClass, cols := nSV }
-        | Except.error e => Except.error e
+      match arangeIndptr nSV nClass with
+      | Except.ok indptr =>
+          Except.ok { dataLen := dataLen, indices := indices,
+                      indptr := indptr, rows := nClass, cols := nSV }
+      | Except.error e => Except.error e
     return result
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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,20 +110,14 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
     let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
       if nSV = 0 then
-        Except.ok emptyResult
+        Except.ok { dataLen := 0, indices := [], indptr := [0, 0], rows := 0, cols := 0 }
       else
-        match arangeIndptr nSV nClass with
-        | Except.ok indptr =>
-            Except.ok { dataLen := dataLen, indices := indices,
-                        indptr := indptr, rows := nClass, cols := nSV }
-        | Except.error e => Except.error e
+        Except.ok { dataLen := dataLen, indices := indices,
+                    indptr := (List.range (nClass + 1)).map (· * nSV),
+                    rows := nClass, cols := nSV }
     return result
     -- impl-end
 
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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,20 +110,12 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
     let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
       if nSV = 0 then
+        Except.ok (builtResult nSV nClass dataLen)
+      else
         Except.ok emptyResult
-      else
-        match arangeIndptr nSV nClass with
-        | Except.ok indptr =>
-            Except.ok { dataLen := dataLen, indices := indices,
-                        indptr := indptr, rows := nClass, cols := nSV }
-        | Except.error e => Except.error e
     return result
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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,20 +110,14 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
     let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
       if nSV = 0 then
         Except.ok emptyResult
       else
-        match arangeIndptr nSV nClass with
-        | Except.ok indptr =>
-            Except.ok { dataLen := dataLen, indices := indices,
-                        indptr := indptr, rows := nClass, cols := nSV }
-        | Except.error e => Except.error e
+        Except.ok { dataLen := dataLen, indices := indices,
+                    indptr := (List.range nClass).map (· * nSV),
+                    rows := nClass, cols := nSV }
     return result
     -- impl-end
 
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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,20 +110,14 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
     let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
       if nSV = 0 then
         Except.ok emptyResult
       else
-        match arangeIndptr nSV nClass with
-        | Except.ok indptr =>
-            Except.ok { dataLen := dataLen, indices := indices,
-                        indptr := indptr, rows := nClass, cols := nSV }
-        | Except.error e => Except.error e
+        Except.ok { dataLen := dataLen, indices := indices,
+                    indptr := (List.range (nClass + 1)).map (· * nSV),
+                    rows := nSV, cols := nClass }
     return result
     -- impl-end
 
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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,13 +110,9 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
     let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
-      if nSV = 0 then
+      if nClass = 0 then
         Except.ok emptyResult
       else
         match arangeIndptr nSV nClass with
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,20 +110,14 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
     let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
       if nSV = 0 then
         Except.ok emptyResult
       else
-        match arangeIndptr nSV nClass with
-        | Except.ok indptr =>
-            Except.ok { dataLen := dataLen, indices := indices,
-                        indptr := indptr, rows := nClass, cols := nSV }
-        | Except.error e => Except.error e
+        Except.ok { dataLen := dataLen + 1, indices := indices,
+                    indptr := (List.range (nClass + 1)).map (· * nSV),
+                    rows := nClass, cols := nSV }
     return result
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- The two shapes the assembly of a per-class sparse coefficient layout can take:
@@ -110,20 +110,13 @@
   ensures out = sparseFitSpec nSV nClass dataLen
   do
     -- impl-start
-    -- Lay out the column indices first (unconditionally, as the assembly does),
-    -- then branch on whether there are any rows: with no rows, yield the empty
-    -- container; otherwise consult the index-pointer layout and build the
-    -- strided compressed-row matrix.
-    let indices := tileRange nSV nClass
     let result : Except FitErr SparseCoef :=
       if nSV = 0 then
         Except.ok emptyResult
       else
-        match arangeIndptr nSV nClass with
-        | Except.ok indptr =>
-            Except.ok { dataLen := dataLen, indices := indices,
-                        indptr := indptr, rows := nClass, cols := nSV }
-        | Except.error e => Except.error e
+        Except.ok { dataLen := dataLen, indices := List.range nSV,
+                    indptr := (List.range (nClass + 1)).map (· * nSV),
+                    rows := nClass, cols := nSV }
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two shapes the assembly of a per-class sparse coefficient layout can take:

     * `ok m` — a sparse matrix `m` was produced;
     * `error zeroDivision` — the layout could not be produced because the
       per-row stride that lays out the index pointers was zero, which makes the
       arithmetic that derives the pointer sequence ill-defined (a division by
       zero). The desired behavior must never end in this shape.

   This is exactly the success/failure distinction the public problem statement
   draws (a `ZeroDivisionError` versus an empty result). -/
inductive FitErr where
  | zeroDivision
  deriving DecidableEq

/- The observable content of a built sparse coefficient matrix (compressed-row
   form): how many stored entries it has, its per-element column-index sequence,
   its per-row index-pointer sequence, and its row/column dimensions. These are
   the only fields the surrounding computation and the consuming code read. -/
structure SparseCoef where
  dataLen : Nat
  indices : List Nat
  indptr  : List Nat
  rows    : Nat
  cols    : Nat
  deriving DecidableEq

/- Deep model of the unchanged standard array-range helper used to lay out the
   row index-pointers: from a count of rows `nClass` and a count of columns
   `nSV` it produces the evenly-strided pointer sequence `0, nSV, 2·nSV, …,
   nClass·nSV`. The stride is `(nSV·nClass) / nClass`, which is `0` exactly when
   `nSV = 0`; a zero stride leaves the range arithmetic ill-defined, modeled as
   `error zeroDivision`. This is a model of a library callee, NOT a consumed
   axiom — validated == the real range helper by axiom_check.py (G-AX);
   provenance in mapping.md §3. -/
def arangeIndptr (nSV nClass : Nat) : Except FitErr (List Nat) :=
  if nSV = 0 then Except.error FitErr.zeroDivision
  else Except.ok ((List.range (nClass + 1)).map (· * nSV))
-- axioms-end

-- pure-start
/- The per-element column-index sequence: the column indices `0 … nSV-1`
   repeated once per row (`nClass` copies, concatenated). Deep model of the
   unchanged tile-of-range construction; validated == the real construction by
   axiom_check.py (G-AX). -/
def tileRange (nSV nClass : Nat) : List Nat :=
  (List.replicate nClass (List.range nSV)).flatten

/- The degenerate result produced when there are no rows to lay out: an empty
   sparse container — no stored entries, no column indices, a single trivial
   row, zero columns. (The exact internals of an empty compressed-row container;
   confirmed == the real empty container by axiom_check.py, G-AX.) -/
def emptyResult : SparseCoef :=
  { dataLen := 0, indices := [], indptr := [0, 0], rows := 1, cols := 0 }

/- The result produced when there is at least one row: a compressed-row matrix
   carrying the `dataLen` stored values, the tiled column indices, the strided
   index-pointers, and the `nClass × nSV` shape. -/
def builtResult (nSV nClass dataLen : Nat) : SparseCoef :=
  { dataLen := dataLen,
    indices := tileRange nSV nClass,
    indptr  := (List.range (nClass + 1)).map (· * nSV),
    rows    := nClass,
    cols    := nSV }

/- The intended outcome of assembling the per-class sparse coefficient matrix:

     * when there are no rows (`nSV = 0`), the empty container is produced — the
       assembly succeeds and yields a matrix with no stored entries;
     * otherwise the strided compressed-row matrix is built.

   In neither case does the assembly end in the `zeroDivision` failure shape:
   the degenerate count of rows is handled before the strided arithmetic is
   reached. -/
def sparseFitSpec (nSV nClass dataLen : Nat) : Except FitErr SparseCoef :=
  if nSV = 0 then Except.ok emptyResult
  else Except.ok (builtResult nSV nClass dataLen)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the per-class sparse coefficient matrix from the count of support
   rows `nSV`, the count of classes `nClass` (at least one), and the number of
   stored coefficient values `dataLen`.

   Desired behavior: when there are no support rows the result must be the empty
   sparse container (`dataLen = 0`, no stored entries) rather than a failure;
   when there is at least one support row the strided compressed-row layout is
   built exactly as the per-class index-pointer arithmetic prescribes. The
   degenerate no-rows case is the missing behavior the public problem statement
   reports.

   `nSV`, `nClass`, `dataLen` are read-only counts: the assembly computes a
   result and mutates no input (directive 5). -/
method buildSparseCoef (nSV : Nat) (nClass : Nat) (dataLen : Nat)
    return (out : Except FitErr SparseCoef)
  require 1 ≤ nClass
  ensures out = sparseFitSpec nSV nClass dataLen
  do
    -- impl-start
    let result : Except FitErr SparseCoef :=
      if nSV = 0 then
        Except.ok emptyResult
      else
        Except.ok { dataLen := dataLen, indices := tileRange nSV nClass,
                    indptr := (List.range (nClass + 1)).map (· * nSV),
                    rows := nClass, cols := nSV }
    return result
    -- impl-end

prove_correct buildSparseCoef by
  loom_solve
  simp_all [sparseFitSpec, arangeIndptr, builtResult]
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol execution

1. SAME-SPEC: all 11 candidates + shipped prepatch confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). Verified byte-identical axioms/pure/pre/post; only impl region edited.

2. WRONG IMPLS (8 distinct, all same_spec=True) verified concurrently (<=4 batches) with `bash scripts/lean_verify.sh <f>` -- ALL REJECTED (exit 1):
   - atk_1 prepatch bug (no nSV=0 guard) EXIT=1
   - atk_2 wrong empty fields rows:=0 EXIT=1
   - atk_3 swapped guard branches EXIT=1
   - atk_4 off-by-one indptr (List.range nClass) EXIT=1
   - atk_5 swapped rows/cols EXIT=1
   - atk_6 guard on nClass=0 instead of nSV=0 EXIT=1
   - atk_7 partial-domain wrong dataLen (dataLen+1 in built branch) EXIT=1
   - atk_8 wrong indices (List.range nSV, not tiled) EXIT=1
   Shipped Solution_prepatch.lean also fails (EXIT=1) -> prepatch_reproduced=True (F2P regression at nSV=0: error zeroDivision vs ok emptyResult).

3. VERIFYING IMPLS: atk_pc2 (inlined build, no arangeIndptr match) EXIT=0 and atk_pc3 (via builtResult def) EXIT=0 -- structurally different from Solution.lean, both same_spec=True -> non-vacuous positive controls. (atk_echo/atk_pc/atk_ncguard failed only on the FROZEN prove_correct tactic shape, which lives outside the editable impl region -- not a semantic rejection; atk_ncguard's residual goal shows it is also extensionally equal on nClass>=1.)

4. MANDATORY RESOLVE (verify=>correct check): materialized the faithful refined patch for the verifying impls. By the refinement.md map (A2 tileRange<->np.tile.arange unconditional; A3 nSV=0 guard -> sp.csr_matrix([]); A4-A5 else strided csr_matrix; A-reference callees unchanged) the faithful transliteration is the gold hunk VERBATIM. Ran via swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-14894', patch, timeout=1800, retries=1) -> RESOLVED: True, COMPLETED: True, note='resolved', flaky=False (F2P test_sparse_fit_support_vectors_empty). No verifying wrong impl's faithful patch fails to resolve.

5. REFINEMENT AUDIT (refinement.md): legs A1(R), A2(A-reference+I), A3(A-reference+I), A4(A-reference+I), A5(R+I), A6(I). No kind-3. Deep models arangeIndptr/tileRange/emptyResult/builtResult are A-reference (validated == real numpy/scipy by axiom_check.py G-AX; verdict.md records G-AX rc 0 over boundaries incl nSV=0 + fuzz), meta.json axioms=[] -> no consumed axioms. A-leg correspondence to real callees (np.arange/np.tile/csr_matrix, all unchanged by gold; the fix is pure control-flow guard) holds. Local numpy/scipy unavailable (G-AX runs in-container), but the decisive resolve run confirms the model<->patch correspondence end-to-end.

VERDICT: SOUND. Answer-key spec fully pins output; 8 wrong impls rejected; 2 structurally-distinct correct impls verify; their faithful patch (= gold) RESOLVES. verify=>correct holds; no break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. This is an answer-key spec: `ensures out = sparseFitSpec nSV nClass dataLen` fully pins the output over the whole domain (nClass>=1), with zero consumed axioms (meta.json axioms=[]). Any verifying impl is extensionally equal to sparseFitSpec, so no verifying-but-wrong impl can exist. The one remaining break vector (sparseFitSpec != gold on a tested input, i.e. an A-leg / model-patch divergence) does NOT occur: the faithful refined patch of the verifying impls (= gold hunk verbatim by the refinement map) RESOLVES under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The two shapes the assembly of a per-class sparse coefficient layout can take:

     * `ok m` — a sparse matrix `m` was produced;
     * `error zeroDivision` — the layout could not be produced because the
       per-row stride that lays out the index pointers was zero, which makes the
       arithmetic that derives the pointer sequence ill-defined (a division by
       zero). The desired behavior must never end in this shape.

   This is exactly the success/failure distinction the public problem statement
   draws (a `ZeroDivisionError` versus an empty result). -/
inductive FitErr where
  | zeroDivision
  deriving DecidableEq

/- The observable content of a built sparse coefficient matrix (compressed-row
   form): how many stored entries it has, its per-element column-index sequence,
   its per-row index-pointer sequence, and its row/column dimensions. These are
   the only fields the surrounding computation and the consuming code read. -/
structure SparseCoef where
  dataLen : Nat
  indices : List Nat
  indptr  : List Nat
  rows    : Nat
  cols    : Nat
  deriving DecidableEq

/- Deep model of the unchanged standard array-range helper used to lay out the
   row index-pointers: from a count of rows `nClass` and a count of columns
   `nSV` it produces the evenly-strided pointer sequence `0, nSV, 2·nSV, …,
   nClass·nSV`. The stride is `(nSV·nClass) / nClass`, which is `0` exactly when
   `nSV = 0`; a zero stride leaves the range arithmetic ill-defined, modeled as
   `error zeroDivision`. This is a model of a library callee, NOT a consumed
   axiom — validated == the real range helper by axiom_check.py (G-AX);
   provenance in mapping.md §3. -/
def arangeIndptr (nSV nClass : Nat) : Except FitErr (List Nat) :=
  if nSV = 0 then Except.error FitErr.zeroDivision
  else Except.ok ((List.range (nClass + 1)).map (· * nSV))
-- axioms-end

-- pure-start
/- The per-element column-index sequence: the column indices `0 … nSV-1`
   repeated once per row (`nClass` copies, concatenated). Deep model of the
   unchanged tile-of-range construction; validated == the real construction by
   axiom_check.py (G-AX). -/
def tileRange (nSV nClass : Nat) : List Nat :=
  (List.replicate nClass (List.range nSV)).flatten

/- The degenerate result produced when there are no rows to lay out: an empty
   sparse container — no stored entries, no column indices, a single trivial
   row, zero columns. (The exact internals of an empty compressed-row container;
   confirmed == the real empty container by axiom_check.py, G-AX.) -/
def emptyResult : SparseCoef :=
  { dataLen := 0, indices := [], indptr := [0, 0], rows := 1, cols := 0 }

/- The result produced when there is at least one row: a compressed-row matrix
   carrying the `dataLen` stored values, the tiled column indices, the strided
   index-pointers, and the `nClass × nSV` shape. -/
def builtResult (nSV nClass dataLen : Nat) : SparseCoef :=
  { dataLen := dataLen,
    indices := tileRange nSV nClass,
    indptr  := (List.range (nClass + 1)).map (· * nSV),
    rows    := nClass,
    cols    := nSV }

/- The intended outcome of assembling the per-class sparse coefficient matrix:

     * when there are no rows (`nSV = 0`), the empty container is produced — the
       assembly succeeds and yields a matrix with no stored entries;
     * otherwise the strided compressed-row matrix is built.

   In neither case does the assembly end in the `zeroDivision` failure shape:
   the degenerate count of rows is handled before the strided arithmetic is
   reached. -/
def sparseFitSpec (nSV nClass dataLen : Nat) : Except FitErr SparseCoef :=
  if nSV = 0 then Except.ok emptyResult
  else Except.ok (builtResult nSV nClass dataLen)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the per-class sparse coefficient matrix from the count of support
   rows `nSV`, the count of classes `nClass` (at least one), and the number of
   stored coefficient values `dataLen`.

   Desired behavior: when there are no support rows the result must be the empty
   sparse container (`dataLen = 0`, no stored entries) rather than a failure;
   when there is at least one support row the strided compressed-row layout is
   built exactly as the per-class index-pointer arithmetic prescribes. The
   degenerate no-rows case is the missing behavior the public problem statement
   reports.

   `nSV`, `nClass`, `dataLen` are read-only counts: the assembly computes a
   result and mutates no input (directive 5). -/
method buildSparseCoef (nSV : Nat) (nClass : Nat) (dataLen : Nat)
    return (out : Except FitErr SparseCoef)
  require 1 ≤ nClass
  ensures out = sparseFitSpec nSV nClass dataLen
  do
    -- impl-start
    let result : Except FitErr SparseCoef :=
      if nSV = 0 then
        Except.ok emptyResult
      else
        Except.ok { dataLen := dataLen, indices := tileRange nSV nClass,
                    indptr := (List.range (nClass + 1)).map (· * nSV),
                    rows := nClass, cols := nSV }
    return result
    -- impl-end

prove_correct buildSparseCoef by
  loom_solve
  simp_all [sparseFitSpec, arangeIndptr, builtResult]
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol execution

1. SAME-SPEC: all 11 candidates + shipped prepatch confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). Verified byte-identical axioms/pure/pre/post; only impl region edited.

2. WRONG IMPLS (8 distinct, all same_spec=True) verified concurrently (<=4 batches) with `bash scripts/lean_verify.sh <f>` -- ALL REJECTED (exit 1):
   - atk_1 prepatch bug (no nSV=0 guard) EXIT=1
   - atk_2 wrong empty fields rows:=0 EXIT=1
   - atk_3 swapped guard branches EXIT=1
   - atk_4 off-by-one indptr (List.range nClass) EXIT=1
   - atk_5 swapped rows/cols EXIT=1
   - atk_6 guard on nClass=0 instead of nSV=0 EXIT=1
   - atk_7 partial-domain wrong dataLen (dataLen+1 in built branch) EXIT=1
   - atk_8 wrong indices (List.range nSV, not tiled) EXIT=1
   Shipped Solution_prepatch.lean also fails (EXIT=1) -> prepatch_reproduced=True (F2P regression at nSV=0: error zeroDivision vs ok emptyResult).

3. VERIFYING IMPLS: atk_pc2 (inlined build, no arangeIndptr match) EXIT=0 and atk_pc3 (via builtResult def) EXIT=0 -- structurally different from Solution.lean, both same_spec=True -> non-vacuous positive controls. (atk_echo/atk_pc/atk_ncguard failed only on the FROZEN prove_correct tactic shape, which lives outside the editable impl region -- not a semantic rejection; atk_ncguard's residual goal shows it is also extensionally equal on nClass>=1.)

4. MANDATORY RESOLVE (verify=>correct check): materialized the faithful refined patch for the verifying impls. By the refinement.md map (A2 tileRange<->np.tile.arange unconditional; A3 nSV=0 guard -> sp.csr_matrix([]); A4-A5 else strided csr_matrix; A-reference callees unchanged) the faithful transliteration is the gold hunk VERBATIM. Ran via swebench_unified.harness.run_resolve('scikit-learn__scikit-learn-14894', patch, timeout=1800, retries=1) -> RESOLVED: True, COMPLETED: True, note='resolved', flaky=False (F2P test_sparse_fit_support_vectors_empty). No verifying wrong impl's faithful patch fails to resolve.

5. REFINEMENT AUDIT (refinement.md): legs A1(R), A2(A-reference+I), A3(A-reference+I), A4(A-reference+I), A5(R+I), A6(I). No kind-3. Deep models arangeIndptr/tileRange/emptyResult/builtResult are A-reference (validated == real numpy/scipy by axiom_check.py G-AX; verdict.md records G-AX rc 0 over boundaries incl nSV=0 + fuzz), meta.json axioms=[] -> no consumed axioms. A-leg correspondence to real callees (np.arange/np.tile/csr_matrix, all unchanged by gold; the fix is pure control-flow guard) holds. Local numpy/scipy unavailable (G-AX runs in-container), but the decisive resolve run confirms the model<->patch correspondence end-to-end.

VERDICT: SOUND. Answer-key spec fully pins output; 8 wrong impls rejected; 2 structurally-distinct correct impls verify; their faithful patch (= gold) RESOLVES. verify=>correct holds; no break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on modeled function sklearn.svm.base.BaseLibSVM._sparse_fit (sparse-coef assembly, base.py:287-294) modeled as buildSparseCoef/sparseFitSpec. No diverging input found; the spec does NOT drift from / over-strengthen the real repo behavior.

SPEC FREEZE: spec_view recomputes to dc7b0c70... byte-identical with meta.region_hashes.spec_view; axioms/pure/impl hashes all match; same_spec(Solution, Solution_prepatch)=True (spec frozen, prepatch differs only in impl). Solution.lean verifies (lean_verify.sh exit 0).

EMPIRICAL FAITHFULNESS CHECK against real numpy/scipy at base_commit fdbaa58:
1. arangeIndptr float-arange hazard (stride = dual_coef_indices.size/n_class = (nSV*nClass)/nClass = nSV): the model's integer list [0,nSV,...,nClass*nSV] compared to real np.arange(0,size+1,size/nClass) over a dense grid AND randomized fuzz up to nSV=1e9, nClass=1e6 -> 0 mismatches. Stride is an exact-integer-valued float because size is divisible by nClass, so no float drift and length is always nClass+1.
2. Full observable-field comparison (m.data.size, list(m.indices), list(m.indptr), m.shape) of the gold-patched assembly vs sparseFitSpec on REACHABLE inputs (dataLen = nSV*nClass): dense 60x60 grid + 2000 random up to 500, INCLUDING nSV=0 -> 0 mismatches. nSV=0 yields empty container (data=0, indices=[], indptr=[0,0], shape=(1,0)) matching emptyResult; sp.csr_matrix([]) confirmed to have exactly those fields.
3. Over-generalization of opaque dataLen is benign/unreachable: every dataLen != nSV*nClass raises ValueError in real scipy csr construction (data/indices length mismatch), so at the call site dataLen is always exactly nSV*nClass -> the free dataLen carrier never diverges on reachable inputs.
4. require 1 <= nClass matches the real site (classification n_class=len(classes_)-1>=1; regression n_class=1); the only division-by-zero the fix addresses is nSV=0, correctly modeled as the guarded empty branch.

The spec is neither too strong nor drifted: on every reachable input the modeled function agrees with the real callee, and the fixed nSV=0 behavior (empty matrix, not ZeroDivisionError) matches the gold patch.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = spec_view(Solution.lean, velvet): imports/axioms/pure/pre/post regions + method signature (require 1 ≤ nClass; ensures out = sparseFitSpec nSV nClass dataLen), with impl and prove_correct bodies elided. same_spec(Solution, Solution_prepatch)=True. The mapping.md/refinement.md docs DO quote gold specifics (`if not n_SV:`, `sp.csr_matrix([])`, `np.arange`, base.py:287-294) but those are G-EQ/G-AX audit artifacts, NOT part of the consumer spec view.

What the PUBLIC problem_statement (not hints) already discloses: title 'ZeroDivisionError in _sparse_fit for SVM with empty support_vectors_'; the traceback pinpoints the culpable expression `dual_coef_indices.size / n_class` raising 'float division by zero'; and Expected Results explicitly states the fix: 'No error is thrown and self.dual_coef_ = sp.csr_matrix([])'. So empty support-vectors -> empty csr_matrix (not an error) is already public.

What the spec view adds is only the abstract obligation sparseFitSpec = (if nSV = 0 then Except.ok emptyResult else Except.ok (builtResult ...)) and emptyResult's fields, which are just the observable fields of sp.csr_matrix([]) already named as the expected result. No repo symbols (base.py, n_SV, np.arange, np.tile, sp.csr_matrix), no line numbers, no diff/patch syntax, no commit hash appear in the spec view (lexical scan confirmed; the only `+ ` match is a Unicode prose bullet). The spec encodes the desired behavior within exactly the envelope the problem_statement draws and reveals no mechanism/location of the gold edit beyond it. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
