# P2 adversarial audit — pydata__xarray-4356

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,6 +72,9 @@
 -- impl-start
 def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
     (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
+  -- PREPATCH BUG: reject any multi-axis reduction with an error.
+  if axisSizes.length > 1 then
+    return .error "min_count is not available for reduction with more than one dimensions."
   let total : Int := (axisSizes.prod : Int)
   let mut out : List Float := []
   for cell in cells do
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,9 @@
 -- impl-start
 def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
     (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
-  let total : Int := (axisSizes.prod : Int)
+  -- BUG: use only the first reduced-axis size (mask.shape[axis]) rather than
+  -- the product of all reduced axes.
+  let total : Int := ((axisSizes.headD 1 : Nat) : Int)
   let mut out : List Float := []
   for cell in cells do
     out := out ++ [reducedCellValue total minCount fillValue cell]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,10 @@
   let total : Int := (axisSizes.prod : Int)
   let mut out : List Float := []
   for cell in cells do
-    out := out ++ [reducedCellValue total minCount fillValue cell]
+    -- BUG: off-by-one threshold — use `<= minCount` instead of `< minCount`,
+    -- invalidating an extra boundary cell.
+    let v : Float := if total - (cell.2 : Int) ≤ (minCount : Int) then fillValue else cell.1
+    out := out ++ [v]
   return .ok out
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,7 +75,8 @@
   let total : Int := (axisSizes.prod : Int)
   let mut out : List Float := []
   for cell in cells do
-    out := out ++ [reducedCellValue total minCount fillValue cell]
+    -- BUG: prepend instead of append, reversing the cell order.
+    out := [reducedCellValue total minCount fillValue cell] ++ out
   return .ok out
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,9 +73,12 @@
 def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
     (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
   let total : Int := (axisSizes.prod : Int)
+  let _ := total
   let mut out : List Float := []
   for cell in cells do
-    out := out ++ [reducedCellValue total minCount fillValue cell]
+    -- BUG: ignore the threshold entirely; always keep the cell's own value,
+    -- never substituting the fill sentinel.
+    out := out ++ [cell.1]
   return .ok out
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -72,44 +72,32 @@
 -- impl-start
 def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
     (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
+  -- Behaviorally identical alternative: map with the equivalent signed test
+  -- `total - missing - minCount < 0` (⟺ `total - missing < minCount`).
   let total : Int := (axisSizes.prod : Int)
-  let mut out : List Float := []
-  for cell in cells do
-    out := out ++ [reducedCellValue total minCount fillValue cell]
-  return .ok out
+  return .ok (cells.map (fun cell =>
+    if total - (cell.2 : Int) - (minCount : Int) < 0 then fillValue else cell.1))
 -- impl-end
 
 -- proof-start
-/-- The imperative `for`-accumulation desugars to appending the per-cell map.
-Stated on the cleaned `forIn` body and generalized over the accumulator so the
-induction goes through. -/
-private theorem enforceMinCount_forIn (f : Float × Nat → Float)
-    (cells : List (Float × Nat)) (init : List Float) :
-    (forIn cells init (fun cell r => (pure (ForInStep.yield (r ++ [f cell])))) : Id (List Float)) =
-      init ++ cells.map f := by
-  induction cells generalizing init with
-  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-  | cons a as ih =>
-    rw [List.forIn_cons]
-    simp only [bind] at ih ⊢
-    rw [ih]
-    simp [List.append_assoc]
-
 theorem correct_enforceMinCount :
     ∀ (axisSizes : List Nat) (cells : List (Float × Nat))
       (minCount : Nat) (fillValue : Float),
       problem_spec_enforceMinCount axisSizes cells minCount fillValue
         (implementation_enforceMinCount axisSizes cells minCount fillValue) := by
   intro axisSizes cells minCount fillValue
-  refine ⟨cells.map (reducedCellValue (axisSizes.prod : Int) minCount fillValue), ?_, ?_⟩
-  · -- the loop builds exactly the per-cell map; bridge the desugared body to the helper
-    unfold implementation_enforceMinCount
-    simp only [Id.run, bind]
-    rw [enforceMinCount_forIn (reducedCellValue (axisSizes.prod : Int) minCount fillValue) cells []]
+  refine ⟨cells.map (fun cell =>
+      if (axisSizes.prod : Int) - (cell.2 : Int) - (minCount : Int) < 0
+        then fillValue else cell.1), ?_, ?_⟩
+  · unfold implementation_enforceMinCount
     rfl
-  · -- each index matches: `getElem?` commutes with `map`, and the mapped function
-    -- is definitionally `reducedCellValue`'s `if`
-    intro i
+  · intro i
     rw [List.getElem?_map]
-    rfl
+    cases h : cells[i]? with
+    | none => rfl
+    | some cell =>
+      simp only [Option.map_some]
+      by_cases hc : (axisSizes.prod : Int) - (cell.2 : Int) < (minCount : Int)
+      · rw [if_pos (by omega), if_pos hc]
+      · rw [if_neg (by omega), if_neg hc]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Applying a minimum-valid-count threshold to the cells of a reduced array.

After a missing-value-aware reduction (a sum or product that skips missing
entries) over one or more axes, each output cell aggregates a block of the
original entries — the block of all entries that collapse onto that cell. A
cell is only trustworthy if enough of the entries reduced into it were actually
present; otherwise the reduction had too little data and the cell must be
discarded (overwritten with the fill sentinel).

For each output cell we therefore compare the number of *valid* (present)
entries reduced into it against the required minimum:

* the total number of entries reduced into one cell is the product of the sizes
  of all reduced axes;
* of those, some number were missing (this missing count is supplied per cell);
* the cell is kept with its computed value when
  `total − missing ≥ minimum`, and replaced by the fill sentinel otherwise.

This rule applies uniformly however many axes are reduced — reducing over a
single axis, or over several axes at once, is the same per-cell threshold; the
only difference is that the per-cell total is a product over all the reduced
axes rather than a single axis size. Reducing over several axes at once is a
perfectly valid request and produces a thresholded result rather than being
rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-cell
-- valid-entry count (the product of the reduced-axis sizes minus the supplied
-- missing count) and its comparison to the required minimum are modeled DEEPLY
-- over the observable inputs (the reduced-axis sizes, the per-cell value and
-- missing count, the minimum, the fill sentinel), so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- The value an output cell keeps after the minimum-count threshold.

`total` is the number of entries reduced into the cell (the product of the
reduced-axis sizes). `cell = (value, missing)` is the cell's computed value
together with how many of those entries were missing. The cell keeps its value
when the number of valid entries `total − missing` is at least `minCount`,
otherwise it is replaced by `fillValue`. The subtraction is carried out over the
integers so that the comparison matches the original signed test
`(total − missing − minCount) < 0`. -/
def reducedCellValue (total : Int) (minCount : Nat) (fillValue : Float)
    (cell : Float × Nat) : Float :=
  if total - (cell.2 : Int) < (minCount : Int) then fillValue else cell.1
-- pure-end

-- post-conditions-start
/-- The thresholding completes without error and, position by position, the
output cell is grounded in the corresponding input cell: at every index `i` the
output value present there is exactly the fill sentinel when fewer than
`minCount` of the `axisSizes.prod` entries reduced into that cell were present
(`axisSizes.prod − missingᵢ < minCount`), and the cell's own computed value
otherwise. Quantifying over every index pins the length and every element to the
input carrier, so only the genuine cell-wise computation can satisfy it. -/
def problem_spec_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
    (minCount : Nat) (fillValue : Float) (result : Except String (List Float)) : Prop :=
  ∃ out : List Float, result = Except.ok out ∧
    ∀ i : Nat, out[i]? =
      (cells[i]?).map (fun cell =>
        if (axisSizes.prod : Int) - (cell.2 : Int) < (minCount : Int)
          then fillValue else cell.1)
-- post-conditions-end

-- impl-start
def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
  let total : Int := (axisSizes.prod : Int)
  let mut out : List Float := []
  for cell in cells do
    out := out ++ [reducedCellValue total minCount fillValue cell]
  return .ok out
-- impl-end

-- proof-start
/-- The imperative `for`-accumulation desugars to appending the per-cell map.
Stated on the cleaned `forIn` body and generalized over the accumulator so the
induction goes through. -/
private theorem enforceMinCount_forIn (f : Float × Nat → Float)
    (cells : List (Float × Nat)) (init : List Float) :
    (forIn cells init (fun cell r => (pure (ForInStep.yield (r ++ [f cell])))) : Id (List Float)) =
      init ++ cells.map f := by
  induction cells generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_enforceMinCount :
    ∀ (axisSizes : List Nat) (cells : List (Float × Nat))
      (minCount : Nat) (fillValue : Float),
      problem_spec_enforceMinCount axisSizes cells minCount fillValue
        (implementation_enforceMinCount axisSizes cells minCount fillValue) := by
  intro axisSizes cells minCount fillValue
  refine ⟨cells.map (reducedCellValue (axisSizes.prod : Int) minCount fillValue), ?_, ?_⟩
  · -- the loop builds exactly the per-cell map; bridge the desugared body to the helper
    unfold implementation_enforceMinCount
    simp only [Id.run, bind]
    rw [enforceMinCount_forIn (reducedCellValue (axisSizes.prod : Int) minCount fillValue) cells []]
    rfl
  · -- each index matches: `getElem?` commutes with `map`, and the mapped function
    -- is definitionally `reducedCellValue`'s `if`
    intro i
    rw [List.getElem?_map]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for pydata__xarray-4356 (lean). Spec pins the output EXACTLY: problem_spec_enforceMinCount requires exists out, result = .ok out AND forall i, out[i]? = (cells[i]?).map (fun cell => if axisSizes.prod - cell.2 < minCount then fillValue else cell.1). This fully determines length AND every element as a function of the modeled inputs, so any verifying impl must be behaviorally identical to gold on the modeled domain.

same_spec confirmed True for pos_control + all 6 attacks (swebench_unified.markers.same_spec, lean language; edited impl+proof regions only, which collapse in the spec view; axioms/pure/pre/post byte-identical).

### RESULTS (cmd: bash scripts/lean_verify.sh <f>; exit 0=verifies/no-sorry, 1=error):
- pos_control.lean (gold): exit 0 VERIFIES. #print axioms correct_enforceMinCount => [propext, Quot.sound] (clean).
- atk_1.lean PREPATCH BUG (reject multi-axis reduction with .error via `if axisSizes.length > 1`): exit 1, does NOT verify. Spec demands .ok for every input; the guard breaks the F2P multi-axis scenario. Prepatch reproduced.
- atk_2.lean SINGLE-AXIS COUNT (total = axisSizes.headD 1 instead of prod): exit 1, does NOT verify. Wrong per-cell total for multi-axis; spec's axisSizes.prod not matched.
- atk_3.lean OFF-BY-ONE BOUNDARY (`<= minCount` instead of `< minCount`): exit 1, does NOT verify. Invalidates an extra boundary cell; fails index-wise equality.
- atk_4.lean CONTROL-FLOW/EFFECT (prepend instead of append -> reversed output order): exit 1, does NOT verify. Positional pinning of forall i out[i]? rejects the reversal.
- atk_5.lean PARTIAL-DOMAIN/UNGROUNDED (ignore threshold, always keep cell.1, never fill): exit 1, does NOT verify. Fails whenever a cell should be invalidated.
- atk_6.lean UNGROUNDED-ORACLE ECHO / correct alternative (cells.map with equivalent signed test total - missing - minCount < 0): exit 0 VERIFIES. #print axioms => [propext, Quot.sound] (clean). This is behaviorally IDENTICAL to gold (a - b - c < 0 <-> a - b < c), i.e. a legitimate same-spec correct impl, NOT a wrong impl.

MANDATORY RESOLVE (protocol step 2): atk_6 is the ONLY attack whose proof closes with clean axioms. Its faithful refined patch is exactly the official post-patch code (algebraically identical decision). Executed via swebench_unified.harness.run_resolve('pydata__xarray-4356', <patch>): RESOLVED=True, completed=True; all 8 FAIL_TO_PASS test_min_count_nd[{sum,prod}-False-{float,int,float32,bool_}] pass, PASS_TO_PASS all pass. A resolving echo of the gold is NOT a spec weakness (unified G-PANEL-1/eq policy: same-spec verifying attack fails ONLY if its refined patch does NOT resolve). It resolves, so no break.

REFINEMENT.MD AUDIT: axioms region is EMPTY (no axiom/opaque callee contract). All 5 legs tagged R; no A-consumed, no A-reference, no I, no kind-3. The soundness-critical changed op (per-cell total np.take(mask.shape, axis).prod() - mask.sum(axis), compared to min_count) is modeled DEEPLY as List.prod + Int arithmetic + if, consistent with SPEC_GUIDE section 3 (a deeply-modeled changed op must not be axiomatized). There are therefore NO A-legs whose real-callee correspondence could be falsified; G-AX skips correctly. mask.sum(axis) and maybe_promote are unchanged and enter only as input observables (cell.2, fillValue), not recomputed, so no contract is needed. Branch-unification claim (nd branch == scalar elif) holds: for an all-dims reduction mask.size = prod(reduced axis sizes).

CONCLUSION: 5 distinct wrong impls (partial-domain, boundary, control-flow-effect, single-axis, prepatch) all rejected by verification; the one clean-axiom closing impl (atk_6) is a genuine correct echo whose materialized faithful patch RESOLVES under the official harness. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve. verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Applying a minimum-valid-count threshold to the cells of a reduced array.

After a missing-value-aware reduction (a sum or product that skips missing
entries) over one or more axes, each output cell aggregates a block of the
original entries — the block of all entries that collapse onto that cell. A
cell is only trustworthy if enough of the entries reduced into it were actually
present; otherwise the reduction had too little data and the cell must be
discarded (overwritten with the fill sentinel).

For each output cell we therefore compare the number of *valid* (present)
entries reduced into it against the required minimum:

* the total number of entries reduced into one cell is the product of the sizes
  of all reduced axes;
* of those, some number were missing (this missing count is supplied per cell);
* the cell is kept with its computed value when
  `total − missing ≥ minimum`, and replaced by the fill sentinel otherwise.

This rule applies uniformly however many axes are reduced — reducing over a
single axis, or over several axes at once, is the same per-cell threshold; the
only difference is that the per-cell total is a product over all the reduced
axes rather than a single axis size. Reducing over several axes at once is a
perfectly valid request and produces a thresholded result rather than being
rejected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The per-cell
-- valid-entry count (the product of the reduced-axis sizes minus the supplied
-- missing count) and its comparison to the required minimum are modeled DEEPLY
-- over the observable inputs (the reduced-axis sizes, the per-cell value and
-- missing count, the minimum, the fill sentinel), so no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- The value an output cell keeps after the minimum-count threshold.

`total` is the number of entries reduced into the cell (the product of the
reduced-axis sizes). `cell = (value, missing)` is the cell's computed value
together with how many of those entries were missing. The cell keeps its value
when the number of valid entries `total − missing` is at least `minCount`,
otherwise it is replaced by `fillValue`. The subtraction is carried out over the
integers so that the comparison matches the original signed test
`(total − missing − minCount) < 0`. -/
def reducedCellValue (total : Int) (minCount : Nat) (fillValue : Float)
    (cell : Float × Nat) : Float :=
  if total - (cell.2 : Int) < (minCount : Int) then fillValue else cell.1
-- pure-end

-- post-conditions-start
/-- The thresholding completes without error and, position by position, the
output cell is grounded in the corresponding input cell: at every index `i` the
output value present there is exactly the fill sentinel when fewer than
`minCount` of the `axisSizes.prod` entries reduced into that cell were present
(`axisSizes.prod − missingᵢ < minCount`), and the cell's own computed value
otherwise. Quantifying over every index pins the length and every element to the
input carrier, so only the genuine cell-wise computation can satisfy it. -/
def problem_spec_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
    (minCount : Nat) (fillValue : Float) (result : Except String (List Float)) : Prop :=
  ∃ out : List Float, result = Except.ok out ∧
    ∀ i : Nat, out[i]? =
      (cells[i]?).map (fun cell =>
        if (axisSizes.prod : Int) - (cell.2 : Int) < (minCount : Int)
          then fillValue else cell.1)
-- post-conditions-end

-- impl-start
def implementation_enforceMinCount (axisSizes : List Nat) (cells : List (Float × Nat))
    (minCount : Nat) (fillValue : Float) : Except String (List Float) := Id.run do
  let total : Int := (axisSizes.prod : Int)
  let mut out : List Float := []
  for cell in cells do
    out := out ++ [reducedCellValue total minCount fillValue cell]
  return .ok out
-- impl-end

-- proof-start
/-- The imperative `for`-accumulation desugars to appending the per-cell map.
Stated on the cleaned `forIn` body and generalized over the accumulator so the
induction goes through. -/
private theorem enforceMinCount_forIn (f : Float × Nat → Float)
    (cells : List (Float × Nat)) (init : List Float) :
    (forIn cells init (fun cell r => (pure (ForInStep.yield (r ++ [f cell])))) : Id (List Float)) =
      init ++ cells.map f := by
  induction cells generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_enforceMinCount :
    ∀ (axisSizes : List Nat) (cells : List (Float × Nat))
      (minCount : Nat) (fillValue : Float),
      problem_spec_enforceMinCount axisSizes cells minCount fillValue
        (implementation_enforceMinCount axisSizes cells minCount fillValue) := by
  intro axisSizes cells minCount fillValue
  refine ⟨cells.map (reducedCellValue (axisSizes.prod : Int) minCount fillValue), ?_, ?_⟩
  · -- the loop builds exactly the per-cell map; bridge the desugared body to the helper
    unfold implementation_enforceMinCount
    simp only [Id.run, bind]
    rw [enforceMinCount_forIn (reducedCellValue (axisSizes.prod : Int) minCount fillValue) cells []]
    rfl
  · -- each index matches: `getElem?` commutes with `map`, and the mapped function
    -- is definitionally `reducedCellValue`'s `if`
    intro i
    rw [List.getElem?_map]
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for pydata__xarray-4356 (lean). Spec pins the output EXACTLY: problem_spec_enforceMinCount requires exists out, result = .ok out AND forall i, out[i]? = (cells[i]?).map (fun cell => if axisSizes.prod - cell.2 < minCount then fillValue else cell.1). This fully determines length AND every element as a function of the modeled inputs, so any verifying impl must be behaviorally identical to gold on the modeled domain.

same_spec confirmed True for pos_control + all 6 attacks (swebench_unified.markers.same_spec, lean language; edited impl+proof regions only, which collapse in the spec view; axioms/pure/pre/post byte-identical).

### RESULTS (cmd: bash scripts/lean_verify.sh <f>; exit 0=verifies/no-sorry, 1=error):
- pos_control.lean (gold): exit 0 VERIFIES. #print axioms correct_enforceMinCount => [propext, Quot.sound] (clean).
- atk_1.lean PREPATCH BUG (reject multi-axis reduction with .error via `if axisSizes.length > 1`): exit 1, does NOT verify. Spec demands .ok for every input; the guard breaks the F2P multi-axis scenario. Prepatch reproduced.
- atk_2.lean SINGLE-AXIS COUNT (total = axisSizes.headD 1 instead of prod): exit 1, does NOT verify. Wrong per-cell total for multi-axis; spec's axisSizes.prod not matched.
- atk_3.lean OFF-BY-ONE BOUNDARY (`<= minCount` instead of `< minCount`): exit 1, does NOT verify. Invalidates an extra boundary cell; fails index-wise equality.
- atk_4.lean CONTROL-FLOW/EFFECT (prepend instead of append -> reversed output order): exit 1, does NOT verify. Positional pinning of forall i out[i]? rejects the reversal.
- atk_5.lean PARTIAL-DOMAIN/UNGROUNDED (ignore threshold, always keep cell.1, never fill): exit 1, does NOT verify. Fails whenever a cell should be invalidated.
- atk_6.lean UNGROUNDED-ORACLE ECHO / correct alternative (cells.map with equivalent signed test total - missing - minCount < 0): exit 0 VERIFIES. #print axioms => [propext, Quot.sound] (clean). This is behaviorally IDENTICAL to gold (a - b - c < 0 <-> a - b < c), i.e. a legitimate same-spec correct impl, NOT a wrong impl.

MANDATORY RESOLVE (protocol step 2): atk_6 is the ONLY attack whose proof closes with clean axioms. Its faithful refined patch is exactly the official post-patch code (algebraically identical decision). Executed via swebench_unified.harness.run_resolve('pydata__xarray-4356', <patch>): RESOLVED=True, completed=True; all 8 FAIL_TO_PASS test_min_count_nd[{sum,prod}-False-{float,int,float32,bool_}] pass, PASS_TO_PASS all pass. A resolving echo of the gold is NOT a spec weakness (unified G-PANEL-1/eq policy: same-spec verifying attack fails ONLY if its refined patch does NOT resolve). It resolves, so no break.

REFINEMENT.MD AUDIT: axioms region is EMPTY (no axiom/opaque callee contract). All 5 legs tagged R; no A-consumed, no A-reference, no I, no kind-3. The soundness-critical changed op (per-cell total np.take(mask.shape, axis).prod() - mask.sum(axis), compared to min_count) is modeled DEEPLY as List.prod + Int arithmetic + if, consistent with SPEC_GUIDE section 3 (a deeply-modeled changed op must not be axiomatized). There are therefore NO A-legs whose real-callee correspondence could be falsified; G-AX skips correctly. mask.sum(axis) and maybe_promote are unchanged and enter only as input observables (cell.2, fillValue), not recomputed, so no contract is needed. Branch-unification claim (nd branch == scalar elif) holds: for an all-dims reduction mask.size = prod(reduced axis sizes).

CONCLUSION: 5 distinct wrong impls (partial-domain, boundary, control-flow-effect, single-axis, prepatch) all rejected by verification; the one clean-axiom closing impl (atk_6) is a genuine correct echo whose materialized faithful patch RESOLVES under the official harness. No impl with a closing clean-axiom proof has a faithful patch that fails to resolve. verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attempted faithfulness-break on problem_spec_enforceMinCount vs post-patch xarray/core/nanops._maybe_null_out. No diverging input found; spec is faithful (not too strong).

Modeled decision: fill cell iff `axisSizes.prod - missing < minCount`. Verified against BOTH real post-patch branches (worktree):
- nd branch: `null_mask = (np.take(mask.shape,axis).prod() - mask.sum(axis) - min_count) < 0` == `total - missing < min_count` where total=axisSizes.prod, missing=mask.sum(axis). Exact match; `a-b-c<0 ⟺ a-b<c` over Int is exact.
- scalar/elif branch (0-d, all dims reduced): `mask.size - mask.sum() < min_count`; here mask.size = ∏(all dims) = ∏(reduced axis sizes) = total, so it is the one-cell instance of the same rule. Match.

Scope-out is legitimate: `axis is None` early path and NAT_TYPES datetime guard are untouched by patch.diff and outside the min_count reduction scenario — narrowing the domain, not strengthening the postcondition on the modeled domain.

Evidence gathered:
- lean_verify.sh Solution.lean → exit 0 (compiles, no sorry/error).
- #print axioms correct_enforceMinCount → [propext, Quot.sound]; NO sorryAx — proof is genuine.
- same_spec(Solution, Solution_prepatch, lean) = True → spec region byte-identical; only impl/proof differ (prepatch keeps multi-axis guard, correctly fails G-DIFF).
- conformance_check.py → checked=120009 disagreements=0, status=pass (edge cases + 120k fuzz crossing single/multi-axis, missing 0..total, min_count 0..total+2). Oracle is faithful in-process replica of post-patch decision; shadow mirrors impl.

The postcondition is input-grounded (∀ i, out[i]? = (cells[i]?).map(...)), pinning length and every element to the input carrier — not a self-referential echo of the impl, and not over-tight relative to the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the consumer spec view (markers.spec_view of Solution.lean) against the SOLVER-VISIBLE problem_statement only (not hints_text, not the auditor docs mapping.md/refinement.md/verdict.md).

Mechanical screen: leakage.screen passes (hard_failures=[]). No diff markers, gold-patch line not reproduced, patched file path 'xarray/core/nanops.py' absent, the sole patched symbol '_maybe_null_out' (stripped 'maybe_null_out') does not appear in any spec-view identifier or comment (Lean names use the neutral 'enforceMinCount'). No bug/fix narration tokens.

Substantive judgment — the two gold discriminators are BOTH already public in problem_statement, so the spec view discloses nothing beyond it:
  1. The title 'min_count is not available for reduction with more than one dimensions' + 'Describe the solution: sum with min_count [should work] when passing more than one dim' publicly names dropping the multi-dim guard. Spec-view prose 'Reducing over several axes at once is a perfectly valid request... rather than being rejected' merely restates this.
  2. The problem_statement gives the fix VERBATIM: 'replacing mask.shape[axis] with np.take(a.shape, axis).prod()'. Spec-view prose 'the per-cell total is a product over all the reduced axes' is exactly this public proposal — nothing new.

The detailed gold reproductions (full pre-patch Python source, the exact np.take fix line, the guard-removal) live only in mapping.md/refinement.md/verdict.md, which are auditor-facing and NOT part of the spec_view projection.

same_spec(Solution.lean, Solution_prepatch.lean)=True: the spec view is byte-identical between patched and pre-patch variants (they differ only in the elided impl/proof), so the spec view carries no impl-specific edit tell. G-LEAK meta status is not 'relaxed'; no RELAXED_LEAKAGE.md deferral in play.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
