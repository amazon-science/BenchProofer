# P2 adversarial audit — sympy__sympy-13031

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,8 +96,8 @@
 
 -- impl-start
 def implementation_hJoin (self other : Mat) : Mat := Id.run do
-  if self.cols = 0 ∧ self.rows ≠ other.rows then
-    return concatCols (zeroColsMat other.rows self.kind) other
+  if self.rows = 0 ∨ self.cols = 0 then
+    return { other with kind := self.kind }
   return concatCols self other
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -96,7 +96,7 @@
 
 -- impl-start
 def implementation_hJoin (self other : Mat) : Mat := Id.run do
-  if self.cols = 0 ∧ self.rows ≠ other.rows then
+  if self.rows ≠ other.rows ∧ self.cols = 0 then
     return concatCols (zeroColsMat other.rows self.kind) other
   return concatCols self other
 -- impl-end
@@ -107,24 +107,24 @@
       problem_spec_hJoin self other (implementation_hJoin self other) := by
   intro self other _hpre
   have himpl : implementation_hJoin self other =
-      if self.cols = 0 ∧ self.rows ≠ other.rows then
+      if self.rows ≠ other.rows ∧ self.cols = 0 then
         concatCols (zeroColsMat other.rows self.kind) other
       else concatCols self other := by
     unfold implementation_hJoin; simp only [Id.run]; rfl
   rw [himpl]
-  by_cases h : self.cols = 0 ∧ self.rows ≠ other.rows
+  by_cases h : self.rows ≠ other.rows ∧ self.cols = 0
   · rw [if_pos h]
     refine ⟨rfl, ?_, ?_⟩
     · intro _
       refine ⟨rfl, ?_, ?_⟩
       · simp [concatCols, zeroColsMat]
       · intro i j; simp [concatCols, zeroColsMat]
-    · intro hc0; exact absurd h.1 hc0
+    · intro hc0; exact absurd h.2 hc0
   · rw [if_neg h]
     refine ⟨rfl, ?_, ?_⟩
     · intro hc0
       have hr : self.rows = other.rows := by
-        by_contra hne; exact h ⟨hc0, hne⟩
+        by_contra hne; exact h ⟨hne, hc0⟩
       refine ⟨hr, ?_, ?_⟩
       · simp [concatCols, hc0]
       · intro i j; simp [concatCols, hc0]
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -98,18 +98,21 @@
 def implementation_hJoin (self other : Mat) : Mat := Id.run do
   if self.cols = 0 ∧ self.rows ≠ other.rows then
     return concatCols (zeroColsMat other.rows self.kind) other
-  return concatCols self other
+  if self.rows = other.rows then
+    return concatCols self other
+  return zeroColsMat 0 self.kind
 -- impl-end
 
 -- proof-start
 theorem correct_hJoin :
     ∀ (self other : Mat), (self.cols = 0 ∨ self.rows = other.rows) →
       problem_spec_hJoin self other (implementation_hJoin self other) := by
-  intro self other _hpre
+  intro self other hpre
   have himpl : implementation_hJoin self other =
       if self.cols = 0 ∧ self.rows ≠ other.rows then
         concatCols (zeroColsMat other.rows self.kind) other
-      else concatCols self other := by
+      else if self.rows = other.rows then concatCols self other
+      else zeroColsMat 0 self.kind := by
     unfold implementation_hJoin; simp only [Id.run]; rfl
   rw [himpl]
   by_cases h : self.cols = 0 ∧ self.rows ≠ other.rows
@@ -121,10 +124,13 @@
       · intro i j; simp [concatCols, zeroColsMat]
     · intro hc0; exact absurd h.1 hc0
   · rw [if_neg h]
+    have hr : self.rows = other.rows := by
+      rcases hpre with hc0 | hrr
+      · by_contra hne; exact h ⟨hc0, hne⟩
+      · exact hrr
+    rw [if_pos hr]
     refine ⟨rfl, ?_, ?_⟩
     · intro hc0
-      have hr : self.rows = other.rows := by
-        by_contra hne; exact h ⟨hc0, hne⟩
       refine ⟨hr, ?_, ?_⟩
       · simp [concatCols, hc0]
       · intro i j; simp [concatCols, hc0]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -97,7 +97,7 @@
 -- impl-start
 def implementation_hJoin (self other : Mat) : Mat := Id.run do
   if self.cols = 0 ∧ self.rows ≠ other.rows then
-    return concatCols (zeroColsMat other.rows self.kind) other
+    return other
   return concatCols self other
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -157,18 +157,21 @@
 def implementation_vJoin (self other : Mat) : Mat := Id.run do
   if self.rows = 0 ∧ self.cols ≠ other.cols then
     return concatRows (zeroRowsMat other.cols self.kind) other
-  return concatRows self other
+  if self.cols = other.cols then
+    return concatRows self other
+  return zeroRowsMat 0 self.kind
 -- impl-end
 
 -- proof-start
 theorem correct_vJoin :
     ∀ (self other : Mat), (self.rows = 0 ∨ self.cols = other.cols) →
       problem_spec_vJoin self other (implementation_vJoin self other) := by
-  intro self other _hpre
+  intro self other hpre
   have himpl : implementation_vJoin self other =
       if self.rows = 0 ∧ self.cols ≠ other.cols then
         concatRows (zeroRowsMat other.cols self.kind) other
-      else concatRows self other := by
+      else if self.cols = other.cols then concatRows self other
+      else zeroRowsMat 0 self.kind := by
     unfold implementation_vJoin; simp only [Id.run]; rfl
   rw [himpl]
   by_cases h : self.rows = 0 ∧ self.cols ≠ other.cols
@@ -181,10 +184,13 @@
       · intro i j; simp [concatRows, zeroRowsMat]
     · intro hr0; exact absurd h.1 hr0
   · rw [if_neg h]
+    have hc : self.cols = other.cols := by
+      rcases hpre with hr0 | hcc
+      · by_contra hne; exact h ⟨hr0, hne⟩
+      · exact hcc
+    rw [if_pos hc]
     refine ⟨rfl, ?_, ?_⟩
     · intro hr0
-      have hc : self.cols = other.cols := by
-        by_contra hne; exact h ⟨hr0, hne⟩
       refine ⟨?_, ?_, ?_⟩
       · simp [concatRows, hr0]
       · simp [concatRows, hc]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -157,7 +157,7 @@
 def implementation_vJoin (self other : Mat) : Mat := Id.run do
   if self.rows = 0 ∧ self.cols ≠ other.cols then
     return concatRows (zeroRowsMat other.cols self.kind) other
-  return concatRows self other
+  return concatRows other self
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,8 +96,6 @@
 
 -- impl-start
 def implementation_hJoin (self other : Mat) : Mat := Id.run do
-  if self.cols = 0 ∧ self.rows ≠ other.rows then
-    return concatCols (zeroColsMat other.rows self.kind) other
   return concatCols self other
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -155,7 +155,7 @@
 
 -- impl-start
 def implementation_vJoin (self other : Mat) : Mat := Id.run do
-  if self.rows = 0 ∧ self.cols ≠ other.cols then
+  if self.cols ≠ other.cols ∧ self.rows = 0 then
     return concatRows (zeroRowsMat other.cols self.kind) other
   return concatRows self other
 -- impl-end
@@ -166,12 +166,12 @@
       problem_spec_vJoin self other (implementation_vJoin self other) := by
   intro self other _hpre
   have himpl : implementation_vJoin self other =
-      if self.rows = 0 ∧ self.cols ≠ other.cols then
+      if self.cols ≠ other.cols ∧ self.rows = 0 then
         concatRows (zeroRowsMat other.cols self.kind) other
       else concatRows self other := by
     unfold implementation_vJoin; simp only [Id.run]; rfl
   rw [himpl]
-  by_cases h : self.rows = 0 ∧ self.cols ≠ other.cols
+  by_cases h : self.cols ≠ other.cols ∧ self.rows = 0
   · rw [if_pos h]
     refine ⟨rfl, ?_, ?_⟩
     · intro _
@@ -179,12 +179,12 @@
       · simp [concatRows, zeroRowsMat]
       · simp [concatRows, zeroRowsMat]
       · intro i j; simp [concatRows, zeroRowsMat]
-    · intro hr0; exact absurd h.1 hr0
+    · intro hr0; exact absurd h.2 hr0
   · rw [if_neg h]
     refine ⟨rfl, ?_, ?_⟩
     · intro hr0
       have hc : self.cols = other.cols := by
-        by_contra hne; exact h ⟨hr0, hne⟩
+        by_contra hne; exact h ⟨hne, hr0⟩
       refine ⟨?_, ?_, ?_⟩
       · simp [concatRows, hr0]
       · simp [concatRows, hc]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Joining two matrices edge-to-edge.

A matrix is modelled by its row/column dimensions, a value accessor
`get i j` (row `i`, column `j`), and a `kind` tag identifying the concrete
class of matrix it is (different in-memory representations of a matrix are
different kinds; two matrices can hold the same values yet be of different
kinds).

Two joins are described:

* a **horizontal join** places `other` to the right of `self`, producing a matrix
  `[self other]`. When `self` has no columns it contributes no entries, so the
  join has `other`'s shape and entries; otherwise the result has
  `self.cols + other.cols` columns and every entry is read from `self` in the
  left block and from `other` in the right block.

* a **vertical join** places `other` beneath `self`, producing a matrix
  `[self; other]`. When `self` has no rows it contributes no entries, so the
  join has `other`'s shape and entries; otherwise the result has
  `self.rows + other.rows` rows and every entry is read from `self` in the top
  block and from `other` in the bottom block.

In every case the result is a matrix of the same kind as `self` (joining is an
operation OF the left/top operand: even when `self` contributes no entries the
result is a `self`-kind matrix holding `other`'s values, never `other` itself),
and the result's dimensions and every entry are pinned to the two operands, so
no component of the output is left free. A null-dimensioned operand never
silently discards the other operand's contribution.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Both joins are modelled deeply: each
-- output entry is read directly off one of the two input accessors at an index
-- computed from the inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A matrix: its row/column dimensions, a value accessor `get i j` giving the
value at row `i`, column `j`, and a `kind` tag identifying the concrete class
of matrix it is. -/
structure Mat where
  rows : Nat
  cols : Nat
  get  : Nat → Nat → Int
  kind : Nat

/-- A matrix of the given height and kind with no columns; its accessor is
identically 0. -/
def zeroColsMat (rows kind : Nat) : Mat := ⟨rows, 0, fun _ _ => 0, kind⟩

/-- A matrix of the given width and kind with no rows; its accessor is
identically 0. -/
def zeroRowsMat (cols kind : Nat) : Mat := ⟨0, cols, fun _ _ => 0, kind⟩

/-- `A` with `B` placed to its right: width `A.cols + B.cols`; the left block
reads from `A`, the right block from `B` at the offset past `A.cols`. The
result is of `A`'s kind. -/
def concatCols (A B : Mat) : Mat :=
  ⟨A.rows, A.cols + B.cols,
    fun i j => if j < A.cols then A.get i j else B.get i (j - A.cols),
    A.kind⟩

/-- `A` with `B` placed beneath it: height `A.rows + B.rows`; the top block reads
from `A`, the bottom block from `B` at the offset past `A.rows`. The result is
of `A`'s kind. -/
def concatRows (A B : Mat) : Mat :=
  ⟨A.rows + B.rows, A.cols,
    fun i j => if i < A.rows then A.get i j else B.get (i - A.rows) j,
    A.kind⟩
-- pure-end

-- post-conditions-start
/-- Horizontal join `[self other]`, fully pinned to the operands. The result is
always of `self`'s kind, and:

  * if `self` has no columns the result has `other`'s shape and entries;
  * otherwise the result has `self.rows` rows and `self.cols + other.cols`
    columns, with the left `self.cols` columns read from `self` and the rest read
    from `other` shifted left by `self.cols`. -/
def problem_spec_hJoin (self other : Mat) (result : Mat) : Prop :=
  result.kind = self.kind
  ∧ (self.cols = 0 →
        result.rows = other.rows
      ∧ result.cols = other.cols
      ∧ ∀ i j, result.get i j = other.get i j)
  ∧ (self.cols ≠ 0 →
        result.rows = self.rows
      ∧ result.cols = self.cols + other.cols
      ∧ ∀ i j, result.get i j =
          (if j < self.cols then self.get i j else other.get i (j - self.cols)))
-- post-conditions-end

-- impl-start
def implementation_hJoin (self other : Mat) : Mat := Id.run do
  if self.cols = 0 ∧ self.rows ≠ other.rows then
    return concatCols (zeroColsMat other.rows self.kind) other
  return concatCols self other
-- impl-end

-- proof-start
theorem correct_hJoin :
    ∀ (self other : Mat), (self.cols = 0 ∨ self.rows = other.rows) →
      problem_spec_hJoin self other (implementation_hJoin self other) := by
  intro self other _hpre
  have himpl : implementation_hJoin self other =
      if self.cols = 0 ∧ self.rows ≠ other.rows then
        concatCols (zeroColsMat other.rows self.kind) other
      else concatCols self other := by
    unfold implementation_hJoin; simp only [Id.run]; rfl
  rw [himpl]
  by_cases h : self.cols = 0 ∧ self.rows ≠ other.rows
  · rw [if_pos h]
    refine ⟨rfl, ?_, ?_⟩
    · intro _
      refine ⟨rfl, ?_, ?_⟩
      · simp [concatCols, zeroColsMat]
      · intro i j; simp [concatCols, zeroColsMat]
    · intro hc0; exact absurd h.1 hc0
  · rw [if_neg h]
    refine ⟨rfl, ?_, ?_⟩
    · intro hc0
      have hr : self.rows = other.rows := by
        by_contra hne; exact h ⟨hc0, hne⟩
      refine ⟨hr, ?_, ?_⟩
      · simp [concatCols, hc0]
      · intro i j; simp [concatCols, hc0]
    · intro _
      exact ⟨rfl, rfl, fun i j => rfl⟩
-- proof-end

-- post-conditions-start
/-- Vertical join `[self; other]`, fully pinned to the operands. The result is
always of `self`'s kind, and:

  * if `self` has no rows the result has `other`'s shape and entries;
  * otherwise the result has `self.rows + other.rows` rows and `self.cols`
    columns, with the top `self.rows` rows read from `self` and the rest read
    from `other` shifted up by `self.rows`. -/
def problem_spec_vJoin (self other : Mat) (result : Mat) : Prop :=
  result.kind = self.kind
  ∧ (self.rows = 0 →
        result.rows = other.rows
      ∧ result.cols = other.cols
      ∧ ∀ i j, result.get i j = other.get i j)
  ∧ (self.rows ≠ 0 →
        result.rows = self.rows + other.rows
      ∧ result.cols = self.cols
      ∧ ∀ i j, result.get i j =
          (if i < self.rows then self.get i j else other.get (i - self.rows) j))
-- post-conditions-end

-- impl-start
def implementation_vJoin (self other : Mat) : Mat := Id.run do
  if self.rows = 0 ∧ self.cols ≠ other.cols then
    return concatRows (zeroRowsMat other.cols self.kind) other
  return concatRows self other
-- impl-end

-- proof-start
theorem correct_vJoin :
    ∀ (self other : Mat), (self.rows = 0 ∨ self.cols = other.cols) →
      problem_spec_vJoin self other (implementation_vJoin self other) := by
  intro self other _hpre
  have himpl : implementation_vJoin self other =
      if self.rows = 0 ∧ self.cols ≠ other.cols then
        concatRows (zeroRowsMat other.cols self.kind) other
      else concatRows self other := by
    unfold implementation_vJoin; simp only [Id.run]; rfl
  rw [himpl]
  by_cases h : self.rows = 0 ∧ self.cols ≠ other.cols
  · rw [if_pos h]
    refine ⟨rfl, ?_, ?_⟩
    · intro _
      refine ⟨?_, ?_, ?_⟩
      · simp [concatRows, zeroRowsMat]
      · simp [concatRows, zeroRowsMat]
      · intro i j; simp [concatRows, zeroRowsMat]
    · intro hr0; exact absurd h.1 hr0
  · rw [if_neg h]
    refine ⟨rfl, ?_, ?_⟩
    · intro hr0
      have hc : self.cols = other.cols := by
        by_contra hne; exact h ⟨hr0, hne⟩
      refine ⟨?_, ?_, ?_⟩
      · simp [concatRows, hr0]
      · simp [concatRows, hc]
      · intro i j; simp [concatRows, hr0]
    · intro _
      exact ⟨rfl, rfl, fun i j => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE NOTE: patch.diff is absent from the bundle dir; gold patch reconstructed from the frozen dataset row (base_commit 2dfa7457f2). Scripts live. All commands run there; lean_verify.sh used, never lake/lean directly.

SPEC SHAPE: problem_spec_hJoin/vJoin are TOTAL and fully pin result kind+shape+entries on their domain. The theorem preconditions (hJoin: self.cols=0 ∨ self.rows=other.rows; vJoin: self.rows=0 ∨ self.cols=other.cols) are EXACTLY Python's no-ShapeError domains. The hidden+P2P test suite (test_sparse.py) never probes row_join/col_join on shape-mismatch (test_errors only checks ShapeError for '+'). So the only degree of freedom for a verifying wrong impl is OFF the precondition domain (the ShapeError inputs), which no test exercises — and off-domain divergence still resolves. This is why the spec is not falsifiable via a verifying impl here.

### ATTACKS (8, all same_spec=True via markers.same_spec on lean backend; pos_control same_spec=True too):
- atk_1: prepatch bug hJoin (`if rows=0 ∨ cols=0 then return {other with kind:=self.kind}`). VERIFY exit 1 (cannot close) — confirms G-DIFF/prepatch reproduction.
- atk_4: hJoin null branch returns bare `other` (kind wrong). VERIFY exit 1 (kind conjunct fails).
- atk_6: vJoin normal path uses `concatRows other self` (operands swapped). VERIFY exit 1.
- atk_7: hJoin bare normal path, no null special-case. VERIFY exit 1 (fails cols=0 null-stack leg on-domain).
- atk_2: hJoin echo (guard conjuncts And-swapped, logically identical). VERIFY exit 0, axioms=[propext,Classical.choice,Quot.sound]. Faithful patch RESOLVES=true (F2P test_sparse_matrix pass, all 9 P2P pass).
- atk_8: vJoin echo (And-swapped guard). VERIFY exit 0, clean axioms. Faithful patch RESOLVES=true.
- atk_3: hJoin off-domain — adds `if self.rows != other.rows: return self._new(0,0,[])` in place of raising ShapeError; on-domain behavior byte-identical to gold. VERIFY exit 0, clean axioms. Faithful patch RESOLVES=true (rc0).
- atk_5: vJoin off-domain — symmetric (`if self.cols != other.cols: return _new(0,0,[])`). VERIFY exit 0, clean axioms. Faithful patch RESOLVES=true.

COMMANDS: verify = `bash scripts/lean_verify.sh <atk>.lean`. axioms = same file + `#print axioms correct_hJoin/correct_vJoin` appended; all print only [propext, Classical.choice, Quot.sound], no sorry. Resolve = official harness via swebench_unified.run_evaluation under `docker`, dataset princeton-nlp/SWE-bench_Verified, image swebench/sweb.eval.x86_64.sympy_1776_sympy-13031, timeout 1800. Gold-patch positive control RESOLVES=true (F2P+P2P all pass). NOTE: the wrapped run_resolve() returned completed=false ('no report — harness error') for ALL 4 under 4-way contention (63 pre-existing containers); re-running each via the identical direct harness invocation (proven by the gold control) yielded report.json with resolved=true for every one. Reported results are the executed direct-harness runs.

EVERY verifying clean-axiom attack has a materialized faithful patch that RESOLVES. No verify⇏correct witness found.

A-LEG AUDIT (refinement.md): meta.json axioms=[], deep_model_references=[], opaque_callees=[], conf_skip=false. refinement.md declares NO A-legs — both joins modeled deeply (all legs R/I, G-CONF carries full differential burden), matching the clean `#print axioms` (no custom axiom/opaque callee could smuggle a spuriously strong spec). Correspondence to real callees SparseMatrix.row_join/col_join is faithful: the Lean recursive-call unroll (self._new(...).row_join/col_join(other) → concatCols/concatRows on a null-shaped receiver) is statically justified (constructed receiver's guard is false → normal path), and the on-domain shape/entries/kind pinning matches the tested Python behavior (gold resolves). No kind-3 legs. A-leg audit: PASS.

VERDICT: SOUND. 8 attacks fully verified; 4 with closing clean-axiom proofs; all 4 faithful patches executed through the official harness and RESOLVE. Spec is not shown to be too weak.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Joining two matrices edge-to-edge.

A matrix is modelled by its row/column dimensions, a value accessor
`get i j` (row `i`, column `j`), and a `kind` tag identifying the concrete
class of matrix it is (different in-memory representations of a matrix are
different kinds; two matrices can hold the same values yet be of different
kinds).

Two joins are described:

* a **horizontal join** places `other` to the right of `self`, producing a matrix
  `[self other]`. When `self` has no columns it contributes no entries, so the
  join has `other`'s shape and entries; otherwise the result has
  `self.cols + other.cols` columns and every entry is read from `self` in the
  left block and from `other` in the right block.

* a **vertical join** places `other` beneath `self`, producing a matrix
  `[self; other]`. When `self` has no rows it contributes no entries, so the
  join has `other`'s shape and entries; otherwise the result has
  `self.rows + other.rows` rows and every entry is read from `self` in the top
  block and from `other` in the bottom block.

In every case the result is a matrix of the same kind as `self` (joining is an
operation OF the left/top operand: even when `self` contributes no entries the
result is a `self`-kind matrix holding `other`'s values, never `other` itself),
and the result's dimensions and every entry are pinned to the two operands, so
no component of the output is left free. A null-dimensioned operand never
silently discards the other operand's contribution.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Both joins are modelled deeply: each
-- output entry is read directly off one of the two input accessors at an index
-- computed from the inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A matrix: its row/column dimensions, a value accessor `get i j` giving the
value at row `i`, column `j`, and a `kind` tag identifying the concrete class
of matrix it is. -/
structure Mat where
  rows : Nat
  cols : Nat
  get  : Nat → Nat → Int
  kind : Nat

/-- A matrix of the given height and kind with no columns; its accessor is
identically 0. -/
def zeroColsMat (rows kind : Nat) : Mat := ⟨rows, 0, fun _ _ => 0, kind⟩

/-- A matrix of the given width and kind with no rows; its accessor is
identically 0. -/
def zeroRowsMat (cols kind : Nat) : Mat := ⟨0, cols, fun _ _ => 0, kind⟩

/-- `A` with `B` placed to its right: width `A.cols + B.cols`; the left block
reads from `A`, the right block from `B` at the offset past `A.cols`. The
result is of `A`'s kind. -/
def concatCols (A B : Mat) : Mat :=
  ⟨A.rows, A.cols + B.cols,
    fun i j => if j < A.cols then A.get i j else B.get i (j - A.cols),
    A.kind⟩

/-- `A` with `B` placed beneath it: height `A.rows + B.rows`; the top block reads
from `A`, the bottom block from `B` at the offset past `A.rows`. The result is
of `A`'s kind. -/
def concatRows (A B : Mat) : Mat :=
  ⟨A.rows + B.rows, A.cols,
    fun i j => if i < A.rows then A.get i j else B.get (i - A.rows) j,
    A.kind⟩
-- pure-end

-- post-conditions-start
/-- Horizontal join `[self other]`, fully pinned to the operands. The result is
always of `self`'s kind, and:

  * if `self` has no columns the result has `other`'s shape and entries;
  * otherwise the result has `self.rows` rows and `self.cols + other.cols`
    columns, with the left `self.cols` columns read from `self` and the rest read
    from `other` shifted left by `self.cols`. -/
def problem_spec_hJoin (self other : Mat) (result : Mat) : Prop :=
  result.kind = self.kind
  ∧ (self.cols = 0 →
        result.rows = other.rows
      ∧ result.cols = other.cols
      ∧ ∀ i j, result.get i j = other.get i j)
  ∧ (self.cols ≠ 0 →
        result.rows = self.rows
      ∧ result.cols = self.cols + other.cols
      ∧ ∀ i j, result.get i j =
          (if j < self.cols then self.get i j else other.get i (j - self.cols)))
-- post-conditions-end

-- impl-start
def implementation_hJoin (self other : Mat) : Mat := Id.run do
  if self.cols = 0 ∧ self.rows ≠ other.rows then
    return concatCols (zeroColsMat other.rows self.kind) other
  return concatCols self other
-- impl-end

-- proof-start
theorem correct_hJoin :
    ∀ (self other : Mat), (self.cols = 0 ∨ self.rows = other.rows) →
      problem_spec_hJoin self other (implementation_hJoin self other) := by
  intro self other _hpre
  have himpl : implementation_hJoin self other =
      if self.cols = 0 ∧ self.rows ≠ other.rows then
        concatCols (zeroColsMat other.rows self.kind) other
      else concatCols self other := by
    unfold implementation_hJoin; simp only [Id.run]; rfl
  rw [himpl]
  by_cases h : self.cols = 0 ∧ self.rows ≠ other.rows
  · rw [if_pos h]
    refine ⟨rfl, ?_, ?_⟩
    · intro _
      refine ⟨rfl, ?_, ?_⟩
      · simp [concatCols, zeroColsMat]
      · intro i j; simp [concatCols, zeroColsMat]
    · intro hc0; exact absurd h.1 hc0
  · rw [if_neg h]
    refine ⟨rfl, ?_, ?_⟩
    · intro hc0
      have hr : self.rows = other.rows := by
        by_contra hne; exact h ⟨hc0, hne⟩
      refine ⟨hr, ?_, ?_⟩
      · simp [concatCols, hc0]
      · intro i j; simp [concatCols, hc0]
    · intro _
      exact ⟨rfl, rfl, fun i j => rfl⟩
-- proof-end

-- post-conditions-start
/-- Vertical join `[self; other]`, fully pinned to the operands. The result is
always of `self`'s kind, and:

  * if `self` has no rows the result has `other`'s shape and entries;
  * otherwise the result has `self.rows + other.rows` rows and `self.cols`
    columns, with the top `self.rows` rows read from `self` and the rest read
    from `other` shifted up by `self.rows`. -/
def problem_spec_vJoin (self other : Mat) (result : Mat) : Prop :=
  result.kind = self.kind
  ∧ (self.rows = 0 →
        result.rows = other.rows
      ∧ result.cols = other.cols
      ∧ ∀ i j, result.get i j = other.get i j)
  ∧ (self.rows ≠ 0 →
        result.rows = self.rows + other.rows
      ∧ result.cols = self.cols
      ∧ ∀ i j, result.get i j =
          (if i < self.rows then self.get i j else other.get (i - self.rows) j))
-- post-conditions-end

-- impl-start
def implementation_vJoin (self other : Mat) : Mat := Id.run do
  if self.rows = 0 ∧ self.cols ≠ other.cols then
    return concatRows (zeroRowsMat other.cols self.kind) other
  return concatRows self other
-- impl-end

-- proof-start
theorem correct_vJoin :
    ∀ (self other : Mat), (self.rows = 0 ∨ self.cols = other.cols) →
      problem_spec_vJoin self other (implementation_vJoin self other) := by
  intro self other _hpre
  have himpl : implementation_vJoin self other =
      if self.rows = 0 ∧ self.cols ≠ other.cols then
        concatRows (zeroRowsMat other.cols self.kind) other
      else concatRows self other := by
    unfold implementation_vJoin; simp only [Id.run]; rfl
  rw [himpl]
  by_cases h : self.rows = 0 ∧ self.cols ≠ other.cols
  · rw [if_pos h]
    refine ⟨rfl, ?_, ?_⟩
    · intro _
      refine ⟨?_, ?_, ?_⟩
      · simp [concatRows, zeroRowsMat]
      · simp [concatRows, zeroRowsMat]
      · intro i j; simp [concatRows, zeroRowsMat]
    · intro hr0; exact absurd h.1 hr0
  · rw [if_neg h]
    refine ⟨rfl, ?_, ?_⟩
    · intro hr0
      have hc : self.cols = other.cols := by
        by_contra hne; exact h ⟨hr0, hne⟩
      refine ⟨?_, ?_, ?_⟩
      · simp [concatRows, hr0]
      · simp [concatRows, hc]
      · intro i j; simp [concatRows, hr0]
    · intro _
      exact ⟨rfl, rfl, fun i j => rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE NOTE: patch.diff is absent from the bundle dir; gold patch reconstructed from the frozen dataset row (base_commit 2dfa7457f2). Scripts live. All commands run there; lean_verify.sh used, never lake/lean directly.

SPEC SHAPE: problem_spec_hJoin/vJoin are TOTAL and fully pin result kind+shape+entries on their domain. The theorem preconditions (hJoin: self.cols=0 ∨ self.rows=other.rows; vJoin: self.rows=0 ∨ self.cols=other.cols) are EXACTLY Python's no-ShapeError domains. The hidden+P2P test suite (test_sparse.py) never probes row_join/col_join on shape-mismatch (test_errors only checks ShapeError for '+'). So the only degree of freedom for a verifying wrong impl is OFF the precondition domain (the ShapeError inputs), which no test exercises — and off-domain divergence still resolves. This is why the spec is not falsifiable via a verifying impl here.

### ATTACKS (8, all same_spec=True via markers.same_spec on lean backend; pos_control same_spec=True too):
- atk_1: prepatch bug hJoin (`if rows=0 ∨ cols=0 then return {other with kind:=self.kind}`). VERIFY exit 1 (cannot close) — confirms G-DIFF/prepatch reproduction.
- atk_4: hJoin null branch returns bare `other` (kind wrong). VERIFY exit 1 (kind conjunct fails).
- atk_6: vJoin normal path uses `concatRows other self` (operands swapped). VERIFY exit 1.
- atk_7: hJoin bare normal path, no null special-case. VERIFY exit 1 (fails cols=0 null-stack leg on-domain).
- atk_2: hJoin echo (guard conjuncts And-swapped, logically identical). VERIFY exit 0, axioms=[propext,Classical.choice,Quot.sound]. Faithful patch RESOLVES=true (F2P test_sparse_matrix pass, all 9 P2P pass).
- atk_8: vJoin echo (And-swapped guard). VERIFY exit 0, clean axioms. Faithful patch RESOLVES=true.
- atk_3: hJoin off-domain — adds `if self.rows != other.rows: return self._new(0,0,[])` in place of raising ShapeError; on-domain behavior byte-identical to gold. VERIFY exit 0, clean axioms. Faithful patch RESOLVES=true (rc0).
- atk_5: vJoin off-domain — symmetric (`if self.cols != other.cols: return _new(0,0,[])`). VERIFY exit 0, clean axioms. Faithful patch RESOLVES=true.

COMMANDS: verify = `bash scripts/lean_verify.sh <atk>.lean`. axioms = same file + `#print axioms correct_hJoin/correct_vJoin` appended; all print only [propext, Classical.choice, Quot.sound], no sorry. Resolve = official harness via swebench_unified.run_evaluation under `docker`, dataset princeton-nlp/SWE-bench_Verified, image swebench/sweb.eval.x86_64.sympy_1776_sympy-13031, timeout 1800. Gold-patch positive control RESOLVES=true (F2P+P2P all pass). NOTE: the wrapped run_resolve() returned completed=false ('no report — harness error') for ALL 4 under 4-way contention (63 pre-existing containers); re-running each via the identical direct harness invocation (proven by the gold control) yielded report.json with resolved=true for every one. Reported results are the executed direct-harness runs.

EVERY verifying clean-axiom attack has a materialized faithful patch that RESOLVES. No verify⇏correct witness found.

A-LEG AUDIT (refinement.md): meta.json axioms=[], deep_model_references=[], opaque_callees=[], conf_skip=false. refinement.md declares NO A-legs — both joins modeled deeply (all legs R/I, G-CONF carries full differential burden), matching the clean `#print axioms` (no custom axiom/opaque callee could smuggle a spuriously strong spec). Correspondence to real callees SparseMatrix.row_join/col_join is faithful: the Lean recursive-call unroll (self._new(...).row_join/col_join(other) → concatCols/concatRows on a null-shaped receiver) is statically justified (constructed receiver's guard is false → normal path), and the on-domain shape/entries/kind pinning matches the tested Python behavior (gold resolves). No kind-3 legs. A-leg audit: PASS.

VERDICT: SOUND. 8 attacks fully verified; 4 with closing clean-axiom proofs; all 4 faithful patches executed through the official harness and RESOLVE. Spec is not shown to be too weak.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift-from-real-callee) audit of sympy__sympy-13031 lean bundle. Models patched SparseMatrix.row_join (hJoin) and col_join (vJoin), sparse.py after gold patch (base 2dfa7457f2). 

Checks: (1) Solution.lean is the canonical bundle file; patch_equals_gold=True, conf_skip=False. (2) lean_verify.sh exit 0; #print axioms correct_hJoin / correct_vJoin = [propext, Classical.choice, Quot.sound] only — no sorryAx, proofs genuine. Read the actual gold patch from test.jsonl and the base-commit source; the special branch (cols==0 and rows!=other.rows -> self._new(other.rows,0,[]).row_join(other)) is faithfully modeled as concatCols(zeroColsMat …) other, a single statically-justified one-step unroll landing in the normal concat path (symmetric for vJoin).

Differential test: applied gold patch to a repo copy, ran 4393 randomized cases (shapes 0..4, other both dense Matrix and SparseMatrix), restricted to each function's precondition domain (self.cols=0 OR self.rows=other.rows for hJoin; self.rows=0 OR self.cols=other.cols for vJoin). For every case compared real result vs the Lean postcondition predicate on kind (type(result)==type(self)), dimensions, and every entry. Result: tested 4393, fails 0, and no ShapeError ever raised inside the precondition domain. All four regimes exercised incl. the null-operand special branch (the hidden-test scenario type(a.row_join(b))==type(a)) and the shifted-block entry reads.

Conclusion: the spec exactly matches the real patched callee on the modeled domain — not too strong, not too weak, no drift. The correct_* preconditions correctly exclude precisely the ShapeError inputs. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) passes: no hard failures, no warnings. same_spec confirms the spec view is byte-identical across Solution.lean and both prepatch variants. Detailed judgment against the SOLVER-VISIBLE problem_statement (NOT hints_text):

- No gold-diff line reproduced. The distinctive gold guard conjunctions (`self.rows == 0 and self.cols != other.cols` for col_join; `self.cols == 0 and self.rows != other.rows` for row_join) and the reshape recursion (`self._new(other.rows,0,[]).row_join(other)`) live ONLY in the impl region, which the spec view elides. The visible post-conditions split on a plain `self.cols = 0` / `self.rows = 0` case — this describes the CORRECT dimension-summing behavior that the public issue already demands (hstack(zeros(0,n)...) must give (0,6) not (0,3)), not the gold's specific two-condition guard.
- No patched repo symbol echoed. Patched symbols are {row_join, col_join}; spec-view identifiers are hJoin/vJoin/concatCols/concatRows/zeroColsMat/zeroRowsMat/Mat — none embed either symbol (screen check (a) clean). No `self._new`, no `#10770`, no `ShapeError`, no `sparse.py` module/path.
- No diff markers, no patched file path, no module path.
- No bug/fix narration: comments describe join semantics abstractly ('places other to the right of self', 'null-dimensioned operand never silently discards...'); no bug/fix/regression/previously/incorrectly terms.

The spec faithfully pins the intended correct behavior of the binary join primitives (shape, entries, result kind) — which is what a spec must do and is already implied by the public problem_statement. It does not reveal the gold edit's mechanism (dimension-specific guard + reshape-and-recurse) beyond the public statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
