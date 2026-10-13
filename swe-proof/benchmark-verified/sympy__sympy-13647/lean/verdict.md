# P2 adversarial audit — sympy__sympy-13647

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     return self.get i j
   if pos ≤ j ∧ j < pos + other.cols then
     return other.get i (j - pos)
-  return self.get i (j - other.cols)
+  return self.get i (j - pos - other.cols)
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     return self.get i j
   if pos ≤ j ∧ j < pos + other.cols then
     return other.get i (j - pos)
-  return self.get i (j - other.cols)
+  return 0
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,7 +58,7 @@
 -- impl-start
 def implementation_colInsert
     (self other : Mat) (pos i j : Nat) : Int := Id.run do
-  if j < pos then
+  if j ≤ pos then
     return self.get i j
   if pos ≤ j ∧ j < pos + other.cols then
     return other.get i (j - pos)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     return self.get i j
   if pos ≤ j ∧ j < pos + other.cols then
     return other.get i (j - pos)
-  return self.get i (j - other.cols)
+  return other.get i (j - other.cols)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -58,11 +58,7 @@
 -- impl-start
 def implementation_colInsert
     (self other : Mat) (pos i j : Nat) : Int := Id.run do
-  if j < pos then
-    return self.get i j
-  if pos ≤ j ∧ j < pos + other.cols then
-    return other.get i (j - pos)
-  return self.get i (j - other.cols)
+  return self.get i j
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     return self.get i j
   if pos ≤ j ∧ j < pos + other.cols then
     return other.get i (j - pos)
-  return self.get i (j - other.cols)
+  return self.get i (j - other.cols + 1)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
   if j < pos then
     return self.get i j
   if pos ≤ j ∧ j < pos + other.cols then
-    return other.get i (j - pos)
+    return other.get i j
   return self.get i (j - other.cols)
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Inserting a block of columns into a matrix.

A matrix is modelled by its dimensions together with its value accessor
`get i j` (row `i`, column `j`). Inserting the columns of a second matrix
`other` into a host matrix `self` at column position `pos` produces a new matrix
with `self.cols + other.cols` columns whose value at `(i, j)` is determined,
column-region by column-region, entirely from the two operands:

  * for a column strictly left of the insertion point the value is the host's
    own value at that very column;
  * for a column inside the inserted block the value is taken from `other`, at
    the column offset measured from the insertion point;
  * for a column to the right of the inserted block the value is again the
    host's, taken from the column it occupied before the block was inserted —
    i.e. the same column index shifted left by the width of the inserted block.

Every output column region is pinned to a specific input value, so no part of
the result is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Each region of the produced matrix
-- is read directly off one of the two input accessors at an index computed from
-- the inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A matrix: its row/column dimensions together with a value accessor
`get i j` giving the value at row `i`, column `j`. -/
structure Mat where
  rows : Nat
  cols : Nat
  get  : Nat → Nat → Int
-- pure-end

-- post-conditions-start
/-- The value of the column-inserted matrix at row `i`, column `j` is fully
pinned to the inputs, region by region:

  * a column left of the insertion point reads the host at the same column;
  * a column within the inserted block reads `other` at the offset from `pos`;
  * a column to the right of the block reads the host at that column shifted
    left by the inserted width.

All three regions partition every column index, so the result is determined for
every `(i, j)`. -/
def problem_spec_colInsert
    (self other : Mat) (pos i j : Nat) (result : Int) : Prop :=
  (j < pos → result = self.get i j) ∧
  (pos ≤ j ∧ j < pos + other.cols → result = other.get i (j - pos)) ∧
  (pos + other.cols ≤ j → result = self.get i (j - other.cols))
-- post-conditions-end

-- impl-start
def implementation_colInsert
    (self other : Mat) (pos i j : Nat) : Int := Id.run do
  if j < pos then
    return self.get i j
  if pos ≤ j ∧ j < pos + other.cols then
    return other.get i (j - pos)
  return self.get i (j - other.cols)
-- impl-end

-- proof-start
theorem correct_colInsert :
    ∀ (self other : Mat) (pos i j : Nat),
      problem_spec_colInsert self other pos i j
        (implementation_colInsert self other pos i j) := by
  intro self other pos i j
  unfold problem_spec_colInsert implementation_colInsert
  simp only [Id.run, bind, pure]
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp [h]
  · rintro ⟨h1, h2⟩
    have hlt : ¬ j < pos := by omega
    simp [hlt, h1, h2]
  · intro h
    have hlt : ¬ j < pos := by omega
    have hmid : ¬ (pos ≤ j ∧ j < pos + other.cols) := by omega
    simp [hlt, hmid]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_colInsert is a complete, mutually-exclusive, exhaustive 3-way partition of column index j (j<pos ; pos<=j<pos+other.cols ; pos+other.cols<=j), each region pinning result to an exact input read -- maximally tight/fully determined.

Same-spec: all 8 files (7 attacks + pos_control) return same_spec=True via swebench_unified.markers.same_spec (byte-identical axioms/pure/pre/post; only impl region edited). Head-region diffs CLEAN for every attack.

Positive control (gold impl): scripts/lean_verify.sh exit 0; `#print axioms correct_colInsert` => [propext, Quot.sound] (clean; no sorryAx/Classical.choice).

7 DISTINCT wrong impls, each carrying the faithful gold proof, ALL FAIL to verify under lean_verify.sh (300s cap), with genuine proof errors -- so NONE produces a closing clean-axiom proof, hence nothing to materialize/resolve:
  atk_1 prepatch bug (right region self.get i (j-pos-other.cols)): exit 1, 'unsolved goals' at proof case 3 -> PREPATCH REPRODUCED.
  atk_2 partial-domain (right region -> 0): exit 1.
  atk_3 boundary off-by-one (left guard j <= pos): exit 1.
  atk_4 control-flow-effect (right region reads other.get instead of self.get): exit 1.
  atk_5 ungrounded-oracle echo (always self.get i j): exit 1, 'simp made no progress'.
  atk_6 right-region off-by-one (j-other.cols+1): exit 1.
  atk_7 middle-region wrong offset (other.get i j, not j-pos): exit 1.

Commands used:
  bash scripts/lean_verify.sh <path>.lean
  same_spec via python swebench_unified.markers.same_spec on lean backend.

refinement.md audit: bundle declares NO axiom/opaque callees (grep confirmed NONE). The three legs are I, I, R -- no A-consumed / A-reference / kind-3 legs. G-AX skip stub is legitimate: the per-entry accessor reads input matrix accessors directly at input-computed indices, no external callee contract consumed; R/I legs are covered by G-CONF/G-CONF-differential. A-legs vacuously hold. Since no wrong impl closes, verify=>correct holds; no resolve run required (no verifying attack to falsify).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Inserting a block of columns into a matrix.

A matrix is modelled by its dimensions together with its value accessor
`get i j` (row `i`, column `j`). Inserting the columns of a second matrix
`other` into a host matrix `self` at column position `pos` produces a new matrix
with `self.cols + other.cols` columns whose value at `(i, j)` is determined,
column-region by column-region, entirely from the two operands:

  * for a column strictly left of the insertion point the value is the host's
    own value at that very column;
  * for a column inside the inserted block the value is taken from `other`, at
    the column offset measured from the insertion point;
  * for a column to the right of the inserted block the value is again the
    host's, taken from the column it occupied before the block was inserted —
    i.e. the same column index shifted left by the width of the inserted block.

Every output column region is pinned to a specific input value, so no part of
the result is left free.
-/

-- axioms-start
-- No unchanged outside callee is consumed. Each region of the produced matrix
-- is read directly off one of the two input accessors at an index computed from
-- the inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A matrix: its row/column dimensions together with a value accessor
`get i j` giving the value at row `i`, column `j`. -/
structure Mat where
  rows : Nat
  cols : Nat
  get  : Nat → Nat → Int
-- pure-end

-- post-conditions-start
/-- The value of the column-inserted matrix at row `i`, column `j` is fully
pinned to the inputs, region by region:

  * a column left of the insertion point reads the host at the same column;
  * a column within the inserted block reads `other` at the offset from `pos`;
  * a column to the right of the block reads the host at that column shifted
    left by the inserted width.

All three regions partition every column index, so the result is determined for
every `(i, j)`. -/
def problem_spec_colInsert
    (self other : Mat) (pos i j : Nat) (result : Int) : Prop :=
  (j < pos → result = self.get i j) ∧
  (pos ≤ j ∧ j < pos + other.cols → result = other.get i (j - pos)) ∧
  (pos + other.cols ≤ j → result = self.get i (j - other.cols))
-- post-conditions-end

-- impl-start
def implementation_colInsert
    (self other : Mat) (pos i j : Nat) : Int := Id.run do
  if j < pos then
    return self.get i j
  if pos ≤ j ∧ j < pos + other.cols then
    return other.get i (j - pos)
  return self.get i (j - other.cols)
-- impl-end

-- proof-start
theorem correct_colInsert :
    ∀ (self other : Mat) (pos i j : Nat),
      problem_spec_colInsert self other pos i j
        (implementation_colInsert self other pos i j) := by
  intro self other pos i j
  unfold problem_spec_colInsert implementation_colInsert
  simp only [Id.run, bind, pure]
  refine ⟨?_, ?_, ?_⟩
  · intro h
    simp [h]
  · rintro ⟨h1, h2⟩
    have hlt : ¬ j < pos := by omega
    simp [hlt, h1, h2]
  · intro h
    have hlt : ¬ j < pos := by omega
    have hmid : ¬ (pos ≤ j ∧ j < pos + other.cols) := by omega
    simp [hlt, hmid]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_colInsert is a complete, mutually-exclusive, exhaustive 3-way partition of column index j (j<pos ; pos<=j<pos+other.cols ; pos+other.cols<=j), each region pinning result to an exact input read -- maximally tight/fully determined.

Same-spec: all 8 files (7 attacks + pos_control) return same_spec=True via swebench_unified.markers.same_spec (byte-identical axioms/pure/pre/post; only impl region edited). Head-region diffs CLEAN for every attack.

Positive control (gold impl): scripts/lean_verify.sh exit 0; `#print axioms correct_colInsert` => [propext, Quot.sound] (clean; no sorryAx/Classical.choice).

7 DISTINCT wrong impls, each carrying the faithful gold proof, ALL FAIL to verify under lean_verify.sh (300s cap), with genuine proof errors -- so NONE produces a closing clean-axiom proof, hence nothing to materialize/resolve:
  atk_1 prepatch bug (right region self.get i (j-pos-other.cols)): exit 1, 'unsolved goals' at proof case 3 -> PREPATCH REPRODUCED.
  atk_2 partial-domain (right region -> 0): exit 1.
  atk_3 boundary off-by-one (left guard j <= pos): exit 1.
  atk_4 control-flow-effect (right region reads other.get instead of self.get): exit 1.
  atk_5 ungrounded-oracle echo (always self.get i j): exit 1, 'simp made no progress'.
  atk_6 right-region off-by-one (j-other.cols+1): exit 1.
  atk_7 middle-region wrong offset (other.get i j, not j-pos): exit 1.

Commands used:
  bash scripts/lean_verify.sh <path>.lean
  same_spec via python swebench_unified.markers.same_spec on lean backend.

refinement.md audit: bundle declares NO axiom/opaque callees (grep confirmed NONE). The three legs are I, I, R -- no A-consumed / A-reference / kind-3 legs. G-AX skip stub is legitimate: the per-entry accessor reads input matrix accessors directly at input-computed indices, no external callee contract consumed; R/I legs are covered by G-CONF/G-CONF-differential. A-legs vacuously hold. Since no wrong impl closes, verify=>correct holds; no resolve run required (no verifying attack to falsify).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-13647, modeled function = entry accessor of MatrixShaping._eval_col_insert (sympy/matrices/common.py:85-96, post-patch return self[i, j - other.cols]).

Spec = problem_spec_colInsert: (j<pos -> self.get i j) & (pos<=j<pos+other.cols -> other.get i (j-pos)) & (pos+other.cols<=j -> self.get i (j-other.cols)). The three region guards partition every column index, so the spec is total, not over-constrained.

Checks performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True -> spec region byte-identical across the impl perturbation (spec is fixed, not moved to match impl).
2. lean_verify.sh -> exit 0; #print axioms correct_colInsert = [propext, Quot.sound] only (no sorryAx; proof is genuine, so impl provably satisfies spec).
3. Nat-subtraction soundness: branch-2 guard pos<=j makes j-pos exact; branch-3 guard pos+other.cols<=j makes j-other.cols exact -> truncating Nat sub equals integer sub on-domain; no underflow inflates the spec.
4. Differential vs REAL repo (base worktree @ patched _eval_col_insert):
   - public col_insert in-range pos in 0..scols: 181,473 entry checks, 0 mismatches.
   - direct _eval_col_insert over full valid domain incl boundary pos=scols, ocols=0: 493,093 checks, 0 drift.
   - G-CONF (recorded) 3,067,739 checks, 0 disagreements.

Only apparent disagreement: out-of-range pos (> self.cols or negative). The PUBLIC col_insert wrapper clamps pos into [0, self.cols] and rejects row-count mismatch BEFORE calling _eval_col_insert, so the modeled callee never receives such pos. That input is unreachable for the modeled function and therefore not a faithfulness defect. The spec is faithful to the real callee on its entire actual input domain and is not stronger than repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view (Solution.lean with impl+proof regions elided) was regenerated via markers.spec_view and run through leakage.screen against the public problem_statement (NOT hints_text): PASSED with zero hard failures. No diff markers, no reproduced gold-patch line, no patched file path/module (sympy/matrices/common.py), no patched repo symbol (`entry`, `_eval_col_insert`) echoed in spec-view identifiers or comments, and no bug/fix narration in any spec-view comment/docstring.

The gold edit is the diff `self[i, j - pos - other.cols]` -> `self[i, j - other.cols]` on common.py:89. The spec view does NOT reveal this edit beyond the public problem statement: (a) the buggy pre-patch index formula `j - pos - other.cols` never appears in the spec view (it lives only in Solution_prepatch.lean's elided impl and in the non-consumer audit docs refinement.md/mapping.md); (b) the post-condition `problem_spec_colInsert` states the CORRECT observable for all three column regions symmetrically and abstractly ("shifted left by the width of the inserted block") — stating correct behavior is the spec's purpose, not edit localization, and it does not single out the third region or narrate a fix; (c) the docstrings are behavioral, not edit-narrating.

same_spec(Solution.lean, Solution_prepatch.lean) = True — the spec region (docstrings, Mat, post-conditions) is byte-identical across the pre/post variants, so the specification itself does not differentially encode the gold edit; the only difference is confined to the elided impl region. The audit docs (refinement.md/mapping.md) which DO contain 'PRE-PATCH (buggy)'/'patched line' narration are not part of the consumer spec view and are not screened. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
