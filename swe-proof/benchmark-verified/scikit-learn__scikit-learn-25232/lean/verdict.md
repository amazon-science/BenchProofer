# P2 adversarial audit — scikit-learn__scikit-learn-25232

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
@@ -46,14 +46,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton of the first-round constant initialization. The fill
-statistic for every feature is the chosen constant (a user value when given, else
-the numerical default), and the matrix is rewritten by replacing each sentinel
-entry with the corresponding per-feature statistic. -/
+/-- PRE-PATCH (buggy) skeleton: the first-round inner imputer is built without the
+user's chosen constant, so the per-feature fill statistic and the sentinel
+replacement always use the numerical default of zero, ignoring `fillValue`. -/
 def implementation_initial_fill
     (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
     InitialFillResult := Id.run do
-  let fill := effFill fillValue
+  let fill : Rat := 0
   let statistics := Array.replicate (nFeatures X) fill
   let mut xFilled : Array (Array Rat) := #[]
   for row in X do
@@ -67,7 +66,6 @@
     xFilled := xFilled.push newRow
   return { statistics := statistics, xFilled := xFilled }
 -- impl-end
-
 
 -- proof-start
 -- Module `defs`: closed form computed by the inner per-row loop.
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 def implementation_initial_fill
     (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
     InitialFillResult := Id.run do
-  let fill := effFill fillValue
+  let fill := fillValue.getD 1
   let statistics := Array.replicate (nFeatures X) fill
   let mut xFilled : Array (Array Rat) := #[]
   for row in X do
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
     for j in [0:row.size] do
       let v := row[j]!
       if v = missingValues then
-        newRow := newRow.push fill
+        newRow := newRow.push 0
       else
         newRow := newRow.push v
     xFilled := xFilled.push newRow
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,15 +56,18 @@
   let fill := effFill fillValue
   let statistics := Array.replicate (nFeatures X) fill
   let mut xFilled : Array (Array Rat) := #[]
+  let mut rowIdx : Nat := 0
   for row in X do
     let mut newRow : Array Rat := #[]
     for j in [0:row.size] do
       let v := row[j]!
-      if v = missingValues then
+      -- partial-domain bug: only rows with even index get the sentinel replaced
+      if v = missingValues ∧ rowIdx % 2 = 0 then
         newRow := newRow.push fill
       else
         newRow := newRow.push v
     xFilled := xFilled.push newRow
+    rowIdx := rowIdx + 1
   return { statistics := statistics, xFilled := xFilled }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,8 @@
     (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
     InitialFillResult := Id.run do
   let fill := effFill fillValue
-  let statistics := Array.replicate (nFeatures X) fill
+  -- boundary bug: statistics vector sized by number of rows, not features
+  let statistics := Array.replicate X.size fill
   let mut xFilled : Array (Array Rat) := #[]
   for row in X do
     let mut newRow : Array Rat := #[]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,11 @@
     let mut newRow : Array Rat := #[]
     for j in [0:row.size] do
       let v := row[j]!
+      -- swapped-branch bug: keep the sentinel, overwrite the good values with fill
       if v = missingValues then
+        newRow := newRow.push v
+      else
         newRow := newRow.push fill
-      else
-        newRow := newRow.push v
     xFilled := xFilled.push newRow
   return { statistics := statistics, xFilled := xFilled }
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -52,20 +52,18 @@
 entry with the corresponding per-feature statistic. -/
 def implementation_initial_fill
     (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
-    InitialFillResult := Id.run do
-  let fill := effFill fillValue
-  let statistics := Array.replicate (nFeatures X) fill
-  let mut xFilled : Array (Array Rat) := #[]
-  for row in X do
-    let mut newRow : Array Rat := #[]
-    for j in [0:row.size] do
-      let v := row[j]!
-      if v = missingValues then
-        newRow := newRow.push fill
-      else
-        newRow := newRow.push v
-    xFilled := xFilled.push newRow
-  return { statistics := statistics, xFilled := xFilled }
+    InitialFillResult :=
+  -- Behaviorally identical to gold, written as a direct (non-monadic) fold:
+  { statistics := Array.replicate (nFeatures X) (effFill fillValue),
+    xFilled :=
+      X.foldl
+        (fun acc row =>
+          acc.push
+            ((List.range row.size).foldl
+              (fun nr j =>
+                nr.push (if row[j]! = missingValues then effFill fillValue else row[j]!))
+              #[]))
+        #[] }
 -- impl-end
 
 
@@ -88,23 +86,7 @@
           X.foldl
             (fun acc row => acc.push (mapRow missingValues (effFill fillValue) row))
             #[] } := by
-  simp only [implementation_initial_fill, Id.run, bind, pure]
-  congr 1
-  rw [Array.forIn_yield_eq_foldl]
-  congr 1
-  funext acc row
-  congr 1
-  -- inner per-row loop equals `mapRow`
-  rw [mapRow]
-  rw [Std.Range.forIn_eq_forIn_range']
-  simp only [← apply_ite ForInStep.yield]
-  rw [List.forIn_yield_eq_foldl]
-  rw [List.range_eq_range']
-  have hs : [:row.size].size = row.size := by simp [Std.Range.size]
-  rw [hs]
-  congr 1
-  funext nr j
-  split <;> rfl
+  simp only [implementation_initial_fill, mapRow]
 
 -- Module `M_stats`: the two statistics conjuncts.
 theorem stats_size (X : Array (Array Rat)) (fillValue : Option Rat) :
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No opaque callees are consumed as axioms: the round-zero constant fill and the
-- subsequent replacement of the sentinel are modeled deeply (spelled out below),
-- so there is no UNCHANGED callee whose contract we must assume. (The behavior is
-- validated end-to-end against the real library routine by the conformance gate.)
-- axioms-end

-- pure-start
/-- Result of the first-round constant initialization: the per-feature fill
statistic vector, and the input matrix with every sentinel entry replaced. -/
structure InitialFillResult where
  statistics : Array Rat
  xFilled : Array (Array Rat)

/-- The effective numerical constant: a user-supplied value when present,
otherwise the numerical default of zero. -/
def effFill (fillValue : Option Rat) : Rat := fillValue.getD 0

/-- Number of feature columns of a matrix (columns of its first row; `0` when
empty). -/
def nFeatures (X : Array (Array Rat)) : Nat := if X.size = 0 then 0 else X[0]!.size
-- pure-end

-- post-conditions-start
/-- Specification of the first-round constant initialization.

`statistics` must be exactly the chosen constant in every feature column (this is
the value a user controls); `xFilled` must equal the input matrix with each
sentinel-valued entry replaced by that same constant and every other entry left
untouched (frame: shape and non-sentinel entries are pinned to the input). -/
def problem_spec_initial_fill
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat)
    (result : InitialFillResult) : Prop :=
  let fill := effFill fillValue
  (result.statistics.size = nFeatures X ∧
    ∀ j, j < nFeatures X → result.statistics[j]! = fill) ∧
  (result.xFilled.size = X.size ∧
    ∀ i, i < X.size →
      (result.xFilled[i]!).size = (X[i]!).size ∧
      ∀ j, j < (X[i]!).size →
        (result.xFilled[i]!)[j]! =
          (if (X[i]!)[j]! = missingValues then fill else (X[i]!)[j]!))
-- post-conditions-end

-- impl-start
/-- Imperative skeleton of the first-round constant initialization. The fill
statistic for every feature is the chosen constant (a user value when given, else
the numerical default), and the matrix is rewritten by replacing each sentinel
entry with the corresponding per-feature statistic. -/
def implementation_initial_fill
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
    InitialFillResult := Id.run do
  let fill := effFill fillValue
  let statistics := Array.replicate (nFeatures X) fill
  let mut xFilled : Array (Array Rat) := #[]
  for row in X do
    let mut newRow : Array Rat := #[]
    for j in [0:row.size] do
      let v := row[j]!
      if v = missingValues then
        newRow := newRow.push fill
      else
        newRow := newRow.push v
    xFilled := xFilled.push newRow
  return { statistics := statistics, xFilled := xFilled }
-- impl-end


-- proof-start
-- Module `defs`: closed form computed by the inner per-row loop.
/-- The inner loop's accumulation on a row `r`: replace each entry equal to the
sentinel `missingValues` by `fill`, leaving every other entry untouched. Defined
directly as the inner `foldl` over `List.range r.size` so the loop lemmas are
literal facts about this closed form. -/
def mapRow (missingValues fill : Rat) (r : Array Rat) : Array Rat :=
  (List.range r.size).foldl
    (fun nr j => nr.push (if r[j]! = missingValues then fill else r[j]!)) #[]

-- Module `M_unfold`: expose the two concrete fields of the result record.
theorem unfold_fields
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
    implementation_initial_fill X missingValues fillValue =
      { statistics := Array.replicate (nFeatures X) (effFill fillValue),
        xFilled :=
          X.foldl
            (fun acc row => acc.push (mapRow missingValues (effFill fillValue) row))
            #[] } := by
  simp only [implementation_initial_fill, Id.run, bind, pure]
  congr 1
  rw [Array.forIn_yield_eq_foldl]
  congr 1
  funext acc row
  congr 1
  -- inner per-row loop equals `mapRow`
  rw [mapRow]
  rw [Std.Range.forIn_eq_forIn_range']
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl]
  rw [List.range_eq_range']
  have hs : [:row.size].size = row.size := by simp [Std.Range.size]
  rw [hs]
  congr 1
  funext nr j
  split <;> rfl

-- Module `M_stats`: the two statistics conjuncts.
theorem stats_size (X : Array (Array Rat)) (fillValue : Option Rat) :
    (Array.replicate (nFeatures X) (effFill fillValue)).size = nFeatures X := by
  simp

theorem stats_val (X : Array (Array Rat)) (fillValue : Option Rat)
    (j : Nat) (hj : j < nFeatures X) :
    (Array.replicate (nFeatures X) (effFill fillValue))[j]! = effFill fillValue := by
  have hsize : (Array.replicate (nFeatures X) (effFill fillValue)).size = nFeatures X :=
    Array.size_replicate
  have hj' : j < (Array.replicate (nFeatures X) (effFill fillValue)).size := by omega
  rw [getElem!_pos (Array.replicate (nFeatures X) (effFill fillValue)) j hj']
  simp [Array.getElem_replicate]

-- Module `M_inner`: per-row inner-loop characterization (size + pointwise value).
theorem inner_size (missingValues fill : Rat) (r : Array Rat) :
    (mapRow missingValues fill r).size = r.size := by
  unfold mapRow
  have h : ∀ (l : List Nat) (acc : Array Rat),
      (l.foldl (fun nr j => nr.push (if r[j]! = missingValues then fill else r[j]!)) acc).size
        = acc.size + l.length := by
    intro l
    induction l with
    | nil => intro acc; simp
    | cons a t ih => intro acc; simp [ih]
  simp [h]

theorem inner_val (missingValues fill : Rat) (r : Array Rat)
    (j : Nat) (hj : j < r.size) :
    (mapRow missingValues fill r)[j]! =
      if r[j]! = missingValues then fill else r[j]! := by
  have key : ∀ (n : Nat) (g : Nat → Rat) (init : Array Rat),
      ((List.range n).foldl (fun nr j => nr.push (g j)) init).toList = init.toList ++ (List.range n).map g := by
    intro n
    induction n with
    | zero => intro g init; simp
    | succ m ih => intro g init; rw [List.range_succ, List.foldl_append, List.map_append]; simp [ih]
  have hlist : (mapRow missingValues fill r).toList
      = (List.range r.size).map (fun j => if r[j]! = missingValues then fill else r[j]!) := by
    unfold mapRow; rw [key]; simp
  have hidx : (mapRow missingValues fill r)[j]! = (mapRow missingValues fill r).toList[j]! := by
    simp [Array.getElem!_eq_getD, List.getElem!_eq_getElem?_getD]
  rw [hidx, hlist]
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_map]
  simp [List.getElem?_range, hj]

-- Module `M_outer`: outer-loop characterization and the composed xFilled facts.
theorem outer_size (X : Array (Array Rat)) (missingValues fill : Rat) :
    (X.foldl (fun acc row => acc.push (mapRow missingValues fill row)) #[]).size =
      X.size := by
  simp

theorem outer_elem (X : Array (Array Rat)) (missingValues fill : Rat)
    (i : Nat) (hi : i < X.size) :
    (X.foldl (fun acc row => acc.push (mapRow missingValues fill row)) #[])[i]! =
      mapRow missingValues fill (X[i]!) := by
  rw [← Array.map_eq_foldl]
  simp only [getElem!_pos, Array.size_map, hi, Array.getElem_map]

theorem xfilled_rowsize
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat)
    (i : Nat) (hi : i < X.size) :
    ((implementation_initial_fill X missingValues fillValue).xFilled[i]!).size =
      (X[i]!).size := by
  rw [unfold_fields]
  rw [outer_elem X missingValues (effFill fillValue) i hi]
  exact inner_size missingValues (effFill fillValue) (X[i]!)

theorem xfilled_entry
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat)
    (i : Nat) (hi : i < X.size) (j : Nat) (hj : j < (X[i]!).size) :
    ((implementation_initial_fill X missingValues fillValue).xFilled[i]!)[j]! =
      (if (X[i]!)[j]! = missingValues then effFill fillValue else (X[i]!)[j]!) := by
  rw [unfold_fields]
  dsimp only
  rw [outer_elem X missingValues (effFill fillValue) i hi]
  rw [inner_val missingValues (effFill fillValue) (X[i]!) j hj]

theorem correct_initial_fill :
    ∀ (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat),
      (∀ i, i < X.size → (X[i]!).size = nFeatures X) →
      problem_spec_initial_fill X missingValues fillValue
        (implementation_initial_fill X missingValues fillValue) := by
  intro X missingValues fillValue _huniform
  refine ⟨⟨?_, ?_⟩, ?_, ?_⟩
  · -- statistics.size = nFeatures X
    rw [unfold_fields]; exact stats_size X fillValue
  · -- ∀ j < nFeatures X, statistics[j]! = fill
    intro j hj; rw [unfold_fields]; exact stats_val X fillValue j hj
  · -- xFilled.size = X.size
    rw [unfold_fields]; exact outer_size X missingValues (effFill fillValue)
  · -- per-row size and value facts
    intro i hi
    exact ⟨xfilled_rowsize X missingValues fillValue i hi,
           fun j hj => xfilled_entry X missingValues fillValue i hi j hj⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The spec problem_spec_initial_fill is a COMPLETE pointwise functional specification: statistics fully pinned (size = nFeatures X AND every valid entry = fill), and xFilled fully pinned (size = X.size, each row size = input row size, each entry = if X[i][j]=missingValues then fill else X[i][j]), where fill = effFill fillValue = fillValue.getD 0. There are NO A-consumed axioms (axiom_check.py is a skip stub, G-AX pass=skip); legs #2 and #3 are A-reference deep models of the unchanged SimpleImputer constant-strategy fit (np.full → statistics_) and transform (replace ==missing_values entries by per-column statistic), spelled out directly in the impl and pinned pointwise by the spec — validated == real callee by G-CONF (exit 0, 120007 configs match, prepatch distinguished on 80042). refinement.md audit: all 5 legs are R (#1 changed op, #4, #5) / A-reference (#2, #3) / I — NO kind-3 inexpressible legs; A-legs correspond to the real callees.

same_spec: True for all 7 attacks (axioms/pure/pre/post byte-identical).

Attacks (project root; cmd: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean (gold impl): EXIT 0, verifies. #print axioms correct_initial_fill = [propext, Classical.choice, Quot.sound] (clean).
- atk_1.lean (prepatch bug: fill := 0 hard-coded, drops fillValue): EXIT 1 — proof does NOT close. Prepatch reproduced.
- atk_2.lean (wrong numerical default: fillValue.getD 1): EXIT 1 — rejected.
- atk_3.lean (control-flow-effect: xFilled replaces missing with literal 0 not fill): EXIT 1 — rejected.
- atk_4.lean (partial-domain: only rows with even index get sentinel replaced): EXIT 1 — rejected.
- atk_5.lean (boundary: statistics sized by X.size (rows) instead of nFeatures (cols)): EXIT 1 — rejected.
- atk_6.lean (swapped-branch: keep sentinel, overwrite good values with fill): EXIT 1 — rejected.
- atk_7.lean (ungrounded-oracle / gold-equivalent ECHO: same behavior, written as a direct non-monadic nested foldl instead of Id.run do; unfold_fields proof simplified to `simp only [implementation_initial_fill, mapRow]`): EXIT 0, verifies. #print axioms = [propext, Quot.sound] (clean, no sorryAx).

Only atk_7 closes with clean axioms. Per protocol its faithful refined patch (= the gold fix, forwarding fill_value into the inner SimpleImputer) was materialized and RUN through the official harness (run_resolve, one backend): RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note='resolved'; FAIL_TO_PASS test_iterative_imputer_constant_fill_value PASSED and all PASS_TO_PASS passed. (A first-run pre-warm invocation returned resolved=False before the image/report was fully materialized; the clean re-run resolved True — recorded honestly.)

No same-spec impl with a closing clean-axiom proof has a faithful patch that fails to resolve. verify⇒correct holds on all attacks tried. Verdict SOUND.

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
import Mathlib
-- imports-end

-- axioms-start
-- No opaque callees are consumed as axioms: the round-zero constant fill and the
-- subsequent replacement of the sentinel are modeled deeply (spelled out below),
-- so there is no UNCHANGED callee whose contract we must assume. (The behavior is
-- validated end-to-end against the real library routine by the conformance gate.)
-- axioms-end

-- pure-start
/-- Result of the first-round constant initialization: the per-feature fill
statistic vector, and the input matrix with every sentinel entry replaced. -/
structure InitialFillResult where
  statistics : Array Rat
  xFilled : Array (Array Rat)

/-- The effective numerical constant: a user-supplied value when present,
otherwise the numerical default of zero. -/
def effFill (fillValue : Option Rat) : Rat := fillValue.getD 0

/-- Number of feature columns of a matrix (columns of its first row; `0` when
empty). -/
def nFeatures (X : Array (Array Rat)) : Nat := if X.size = 0 then 0 else X[0]!.size
-- pure-end

-- post-conditions-start
/-- Specification of the first-round constant initialization.

`statistics` must be exactly the chosen constant in every feature column (this is
the value a user controls); `xFilled` must equal the input matrix with each
sentinel-valued entry replaced by that same constant and every other entry left
untouched (frame: shape and non-sentinel entries are pinned to the input). -/
def problem_spec_initial_fill
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat)
    (result : InitialFillResult) : Prop :=
  let fill := effFill fillValue
  (result.statistics.size = nFeatures X ∧
    ∀ j, j < nFeatures X → result.statistics[j]! = fill) ∧
  (result.xFilled.size = X.size ∧
    ∀ i, i < X.size →
      (result.xFilled[i]!).size = (X[i]!).size ∧
      ∀ j, j < (X[i]!).size →
        (result.xFilled[i]!)[j]! =
          (if (X[i]!)[j]! = missingValues then fill else (X[i]!)[j]!))
-- post-conditions-end

-- impl-start
/-- Imperative skeleton of the first-round constant initialization. The fill
statistic for every feature is the chosen constant (a user value when given, else
the numerical default), and the matrix is rewritten by replacing each sentinel
entry with the corresponding per-feature statistic. -/
def implementation_initial_fill
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
    InitialFillResult := Id.run do
  let fill := effFill fillValue
  let statistics := Array.replicate (nFeatures X) fill
  let mut xFilled : Array (Array Rat) := #[]
  for row in X do
    let mut newRow : Array Rat := #[]
    for j in [0:row.size] do
      let v := row[j]!
      if v = missingValues then
        newRow := newRow.push fill
      else
        newRow := newRow.push v
    xFilled := xFilled.push newRow
  return { statistics := statistics, xFilled := xFilled }
-- impl-end


-- proof-start
-- Module `defs`: closed form computed by the inner per-row loop.
/-- The inner loop's accumulation on a row `r`: replace each entry equal to the
sentinel `missingValues` by `fill`, leaving every other entry untouched. Defined
directly as the inner `foldl` over `List.range r.size` so the loop lemmas are
literal facts about this closed form. -/
def mapRow (missingValues fill : Rat) (r : Array Rat) : Array Rat :=
  (List.range r.size).foldl
    (fun nr j => nr.push (if r[j]! = missingValues then fill else r[j]!)) #[]

-- Module `M_unfold`: expose the two concrete fields of the result record.
theorem unfold_fields
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
    implementation_initial_fill X missingValues fillValue =
      { statistics := Array.replicate (nFeatures X) (effFill fillValue),
        xFilled :=
          X.foldl
            (fun acc row => acc.push (mapRow missingValues (effFill fillValue) row))
            #[] } := by
  simp only [implementation_initial_fill, Id.run, bind, pure]
  congr 1
  rw [Array.forIn_yield_eq_foldl]
  congr 1
  funext acc row
  congr 1
  -- inner per-row loop equals `mapRow`
  rw [mapRow]
  rw [Std.Range.forIn_eq_forIn_range']
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl]
  rw [List.range_eq_range']
  have hs : [:row.size].size = row.size := by simp [Std.Range.size]
  rw [hs]
  congr 1
  funext nr j
  split <;> rfl

-- Module `M_stats`: the two statistics conjuncts.
theorem stats_size (X : Array (Array Rat)) (fillValue : Option Rat) :
    (Array.replicate (nFeatures X) (effFill fillValue)).size = nFeatures X := by
  simp

theorem stats_val (X : Array (Array Rat)) (fillValue : Option Rat)
    (j : Nat) (hj : j < nFeatures X) :
    (Array.replicate (nFeatures X) (effFill fillValue))[j]! = effFill fillValue := by
  have hsize : (Array.replicate (nFeatures X) (effFill fillValue)).size = nFeatures X :=
    Array.size_replicate
  have hj' : j < (Array.replicate (nFeatures X) (effFill fillValue)).size := by omega
  rw [getElem!_pos (Array.replicate (nFeatures X) (effFill fillValue)) j hj']
  simp [Array.getElem_replicate]

-- Module `M_inner`: per-row inner-loop characterization (size + pointwise value).
theorem inner_size (missingValues fill : Rat) (r : Array Rat) :
    (mapRow missingValues fill r).size = r.size := by
  unfold mapRow
  have h : ∀ (l : List Nat) (acc : Array Rat),
      (l.foldl (fun nr j => nr.push (if r[j]! = missingValues then fill else r[j]!)) acc).size
        = acc.size + l.length := by
    intro l
    induction l with
    | nil => intro acc; simp
    | cons a t ih => intro acc; simp [ih]
  simp [h]

theorem inner_val (missingValues fill : Rat) (r : Array Rat)
    (j : Nat) (hj : j < r.size) :
    (mapRow missingValues fill r)[j]! =
      if r[j]! = missingValues then fill else r[j]! := by
  have key : ∀ (n : Nat) (g : Nat → Rat) (init : Array Rat),
      ((List.range n).foldl (fun nr j => nr.push (g j)) init).toList = init.toList ++ (List.range n).map g := by
    intro n
    induction n with
    | zero => intro g init; simp
    | succ m ih => intro g init; rw [List.range_succ, List.foldl_append, List.map_append]; simp [ih]
  have hlist : (mapRow missingValues fill r).toList
      = (List.range r.size).map (fun j => if r[j]! = missingValues then fill else r[j]!) := by
    unfold mapRow; rw [key]; simp
  have hidx : (mapRow missingValues fill r)[j]! = (mapRow missingValues fill r).toList[j]! := by
    simp [Array.getElem!_eq_getD, List.getElem!_eq_getElem?_getD]
  rw [hidx, hlist]
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_map]
  simp [List.getElem?_range, hj]

-- Module `M_outer`: outer-loop characterization and the composed xFilled facts.
theorem outer_size (X : Array (Array Rat)) (missingValues fill : Rat) :
    (X.foldl (fun acc row => acc.push (mapRow missingValues fill row)) #[]).size =
      X.size := by
  simp

theorem outer_elem (X : Array (Array Rat)) (missingValues fill : Rat)
    (i : Nat) (hi : i < X.size) :
    (X.foldl (fun acc row => acc.push (mapRow missingValues fill row)) #[])[i]! =
      mapRow missingValues fill (X[i]!) := by
  rw [← Array.map_eq_foldl]
  simp only [getElem!_pos, Array.size_map, hi, Array.getElem_map]

theorem xfilled_rowsize
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat)
    (i : Nat) (hi : i < X.size) :
    ((implementation_initial_fill X missingValues fillValue).xFilled[i]!).size =
      (X[i]!).size := by
  rw [unfold_fields]
  rw [outer_elem X missingValues (effFill fillValue) i hi]
  exact inner_size missingValues (effFill fillValue) (X[i]!)

theorem xfilled_entry
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat)
    (i : Nat) (hi : i < X.size) (j : Nat) (hj : j < (X[i]!).size) :
    ((implementation_initial_fill X missingValues fillValue).xFilled[i]!)[j]! =
      (if (X[i]!)[j]! = missingValues then effFill fillValue else (X[i]!)[j]!) := by
  rw [unfold_fields]
  dsimp only
  rw [outer_elem X missingValues (effFill fillValue) i hi]
  rw [inner_val missingValues (effFill fillValue) (X[i]!) j hj]

theorem correct_initial_fill :
    ∀ (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat),
      (∀ i, i < X.size → (X[i]!).size = nFeatures X) →
      problem_spec_initial_fill X missingValues fillValue
        (implementation_initial_fill X missingValues fillValue) := by
  intro X missingValues fillValue _huniform
  refine ⟨⟨?_, ?_⟩, ?_, ?_⟩
  · -- statistics.size = nFeatures X
    rw [unfold_fields]; exact stats_size X fillValue
  · -- ∀ j < nFeatures X, statistics[j]! = fill
    intro j hj; rw [unfold_fields]; exact stats_val X fillValue j hj
  · -- xFilled.size = X.size
    rw [unfold_fields]; exact outer_size X missingValues (effFill fillValue)
  · -- per-row size and value facts
    intro i hi
    exact ⟨xfilled_rowsize X missingValues fillValue i hi,
           fun j hj => xfilled_entry X missingValues fillValue i hi j hj⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The spec problem_spec_initial_fill is a COMPLETE pointwise functional specification: statistics fully pinned (size = nFeatures X AND every valid entry = fill), and xFilled fully pinned (size = X.size, each row size = input row size, each entry = if X[i][j]=missingValues then fill else X[i][j]), where fill = effFill fillValue = fillValue.getD 0. There are NO A-consumed axioms (axiom_check.py is a skip stub, G-AX pass=skip); legs #2 and #3 are A-reference deep models of the unchanged SimpleImputer constant-strategy fit (np.full → statistics_) and transform (replace ==missing_values entries by per-column statistic), spelled out directly in the impl and pinned pointwise by the spec — validated == real callee by G-CONF (exit 0, 120007 configs match, prepatch distinguished on 80042). refinement.md audit: all 5 legs are R (#1 changed op, #4, #5) / A-reference (#2, #3) / I — NO kind-3 inexpressible legs; A-legs correspond to the real callees.

same_spec: True for all 7 attacks (axioms/pure/pre/post byte-identical).

Attacks (project root; cmd: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean (gold impl): EXIT 0, verifies. #print axioms correct_initial_fill = [propext, Classical.choice, Quot.sound] (clean).
- atk_1.lean (prepatch bug: fill := 0 hard-coded, drops fillValue): EXIT 1 — proof does NOT close. Prepatch reproduced.
- atk_2.lean (wrong numerical default: fillValue.getD 1): EXIT 1 — rejected.
- atk_3.lean (control-flow-effect: xFilled replaces missing with literal 0 not fill): EXIT 1 — rejected.
- atk_4.lean (partial-domain: only rows with even index get sentinel replaced): EXIT 1 — rejected.
- atk_5.lean (boundary: statistics sized by X.size (rows) instead of nFeatures (cols)): EXIT 1 — rejected.
- atk_6.lean (swapped-branch: keep sentinel, overwrite good values with fill): EXIT 1 — rejected.
- atk_7.lean (ungrounded-oracle / gold-equivalent ECHO: same behavior, written as a direct non-monadic nested foldl instead of Id.run do; unfold_fields proof simplified to `simp only [implementation_initial_fill, mapRow]`): EXIT 0, verifies. #print axioms = [propext, Quot.sound] (clean, no sorryAx).

Only atk_7 closes with clean axioms. Per protocol its faithful refined patch (= the gold fix, forwarding fill_value into the inner SimpleImputer) was materialized and RUN through the official harness (run_resolve, one backend): RESOLVED=True, COMPLETED=True, ATTEMPTS=1, note='resolved'; FAIL_TO_PASS test_iterative_imputer_constant_fill_value PASSED and all PASS_TO_PASS passed. (A first-run pre-warm invocation returned resolved=False before the image/report was fully materialized; the clean re-run resolved True — recorded honestly.)

No same-spec impl with a closing clean-axiom proof has a faithful patch that fails to resolve. verify⇒correct holds on all attacks tried. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee) check for scikit-learn__scikit-learn-25232 (lean). No divergence found within the modeled domain.

WHAT THE SPEC MODELS: problem_spec_initial_fill models IterativeImputer._initial_imputation on the initial_strategy="constant" path (the only path the issue/F2P test exercise). It asserts: statistics.size = nFeatures X and statistics[j] = fill for every column, and xFilled equals X with each entry == missingValues replaced by fill, all other entries and the shape preserved, where fill = effFill fillValue = fillValue.getD 0 (None -> 0, the numerical default).

REAL CALLEE @ base_commit f7eea978097085a6781a0e92fc14ba7712a52d75 (verified by reading source of a fresh checkout): _initial_imputation builds SimpleImputer(strategy="constant", fill_value=self.fill_value) and calls fit_transform. In _base.py the constant branch of _dense_fit is `np.full(X.shape[1], fill_value)` (never NaN), fit maps None->0 for numerical dtype, and transform under strategy=="constant" sets valid_statistics=statistics with NO column drop. This is exactly the spec: per-column constant + sentinel replacement.

EMPIRICAL DIFFERENTIAL: transliterated the spec/impl into Python and diffed statistics_ and X_filled against the REAL SimpleImputer constant path. Against base-commit-era sklearn 1.3.0: 15,000 fuzzed rectangular numerical matrices (n_features 1-6, n_samples 1-10, missing_values in {-1,0,7,3}, fill in {None,ints,floats}, sentinel frequent enough to yield all-missing columns) + directed edges including the EXACT F2P reproducer ([[-1,2,3,-1],...], mv=-1, fill=100 with an all-missing 4th column) => 0 disagreements.

RULED-OUT FALSE ALARM: an initial run against sklearn 1.9.0 showed ~1620 'disagreements', ALL on all-missing columns, because 1.9.0 later added NaN-in-statistics_ + column dropping even for strategy="constant" (statistics.fill(fill_value) then set NaN for empty features). That behavior does NOT exist at base commit f7eea978 (constant branch is unconditional np.full; transform never drops on constant). So it is a library-version artifact, not a spec defect. The bundle's target base commit matches the spec.

SCOPE: honestly documented in mapping.md — numerical (Rat) fills only (NaN/string fills out of model), rectangular matrices (ndarrays are always rectangular; correct_initial_fill takes uniform-rows as precondition, which is not a strengthening since inputs are true matrices), constant strategy only. Within this domain the spec is neither too strong nor too weak: it agrees with the real base-commit callee on every tested input.

CORROBORATING: Solution.lean compiles (lean_verify exit 0); #print axioms correct_initial_fill = [propext, Classical.choice, Quot.sound] (no sorryAx, proof is genuine); same_spec(Solution, Solution_prepatch) = True under lean tables (spec region byte-identical); recorded G-CONF passed 120007 configs (fix==oracle 0, prepatch distinguished 80042).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = axioms + pure + post-conditions (impl and proof both elided). The gold edit is: add a `fill_value` parameter to IterativeImputer and forward it into the inner SimpleImputer so the round-zero constant fill uses the user constant instead of the hard-coded numerical default 0. The PUBLIC problem_statement already discloses this in full: title 'IterativeImputer has no parameter "fill_value"', it quotes SimpleImputer's semantics ('fill_value will be 0 when imputing numerical data') and proposes 'The parameter fill_value needs to be added to IterativeImputer for when initial_strategy is set to "constant"'. Thus the spec's core content — effFill fillValue = fillValue.getD 0 and statistics[j]! = fill (user value, else 0) — is exactly the publicly-stated requirement, not a leak beyond problem_statement. The spec-view comments are abstract ('round-zero constant initialization', 'the real library routine', 'conformance gate'); no gold-patch specifics leak: no `_iterative.py`/`_base.py` paths, no SimpleImputer symbol, no `fill_value=self.fill_value` patch line, no file:line refs appear in the exposed regions (those live only in refinement.md/mapping.md, which are not part of the spec view). same_spec(patched, prepatch) = True confirms the spec region is byte-identical across the bug/fix boundary, so it encodes the correct requirement rather than the diff. Leakage screened against problem_statement only (hints_text excluded per instructions), though hints add nothing beyond the same fill_value ask. No line in the spec view reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
