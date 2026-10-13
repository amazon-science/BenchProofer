# P2 adversarial audit — astropy__astropy-13579

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
@@ -65,7 +65,7 @@
       result := result ++ [inputs.getD iworldCurr 0]
       iworldCurr := iworldCurr + 1
     else
-      result := result ++ [slicedOut.getD iworld 0]
+      result := result ++ [(1 : Int)]
   return result
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
   let mut iworldCurr : Nat := 0
   for iworld in [0:worldNDim] do
     if iworld ∈ worldKeep then
-      result := result ++ [inputs.getD iworldCurr 0]
+      result := result ++ [inputs.getD (iworldCurr + 1) 0]
       iworldCurr := iworldCurr + 1
     else
       result := result ++ [slicedOut.getD iworld 0]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,10 +62,10 @@
   let mut iworldCurr : Nat := 0
   for iworld in [0:worldNDim] do
     if iworld ∈ worldKeep then
-      result := result ++ [inputs.getD iworldCurr 0]
+      result := result ++ [slicedOut.getD iworld 0]
       iworldCurr := iworldCurr + 1
     else
-      result := result ++ [slicedOut.getD iworld 0]
+      result := result ++ [inputs.getD iworldCurr 0]
   return result
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
       result := result ++ [inputs.getD iworldCurr 0]
       iworldCurr := iworldCurr + 1
     else
-      result := result ++ [slicedOut.getD iworld 0]
+      result := result ++ [slicedOut.getD (iworld + 1) 0]
   return result
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
       iworldCurr := iworldCurr + 1
     else
       result := result ++ [slicedOut.getD iworld 0]
-  return result
+  return result.reverse
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
       iworldCurr := iworldCurr + 1
     else
       result := result ++ [slicedOut.getD iworld 0]
-  return result
+  return (0 : Int) :: result
 -- impl-end
 
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,16 +57,9 @@
 
 -- impl-start
 def implementation_assemble (worldNDim : Nat) (worldKeep : List Nat)
-    (inputs slicedOut : List Int) : List Int := Id.run do
-  let mut result : List Int := []
-  let mut iworldCurr : Nat := 0
-  for iworld in [0:worldNDim] do
-    if iworld ∈ worldKeep then
-      result := result ++ [inputs.getD iworldCurr 0]
-      iworldCurr := iworldCurr + 1
-    else
-      result := result ++ [slicedOut.getD iworld 0]
-  return result
+    (inputs slicedOut : List Int) : List Int :=
+  (List.range worldNDim).map (fun iworld =>
+    if iworld ∈ worldKeep then inputs.getD iworld 0 else slicedOut.getD iworld 0)
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reassembling a full-length coordinate vector from a reduced one.

A reduced view of a coordinate system keeps only some of the axes of a larger
underlying system. Going back from the reduced view to the underlying system
requires rebuilding a full-length coordinate vector: the underlying system has
`worldNDim` axes, of which a sorted subset `worldKeep` is retained by the view.

To rebuild the full vector, walk the underlying axes in order. For each axis:

* if the axis is one of the kept axes, take the next value from the supplied
  reduced vector (`inputs`), consuming those values left-to-right;
* otherwise the axis is omitted from the reduced view, so its value is not
  supplied by the caller — fill it with the reference value for that axis,
  read from a per-axis reference vector `slicedOut` indexed by the underlying
  axis number.

The result is a vector of length `worldNDim`: every kept axis carries the
corresponding supplied value, and every omitted axis carries its reference
value. The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the reassembly is spelled
-- out concretely as positional placement of supplied values into kept axes and
-- reference values into the omitted axes. The reference vector is taken as an
-- input (it is produced upstream and is not part of the reassembly itself).
-- axioms-end

-- pure-start
-- No additional pure helpers are needed; the predicate is stated directly with
-- list length and positional (`getD`) lookups.
-- pure-end

-- post-conditions-start
/-- The reassembled vector `result` has one entry per underlying axis:

* it has length `worldNDim`;
* every omitted axis (`iworld < worldNDim` with `iworld ∉ worldKeep`) carries the
  reference value `slicedOut.getD iworld`;
* the `c`-th kept axis (`worldKeep.getD c`, for `c < worldKeep.length`) carries
  the `c`-th supplied value `inputs.getD c`.

Together these pin every position of `result`. -/
def problem_spec_assemble (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut result : List Int) : Prop :=
  result.length = worldNDim ∧
  (∀ iworld, iworld < worldNDim → iworld ∉ worldKeep →
      result.getD iworld 0 = slicedOut.getD iworld 0) ∧
  (∀ c, c < worldKeep.length →
      result.getD (worldKeep.getD c 0) 0 = inputs.getD c 0)
-- post-conditions-end

-- impl-start
def implementation_assemble (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut : List Int) : List Int := Id.run do
  let mut result : List Int := []
  let mut iworldCurr : Nat := 0
  for iworld in [0:worldNDim] do
    if iworld ∈ worldKeep then
      result := result ++ [inputs.getD iworldCurr 0]
      iworldCurr := iworldCurr + 1
    else
      result := result ++ [slicedOut.getD iworld 0]
  return result
-- impl-end


-- proof-start
/-- Pure model of one loop iteration: append the supplied-or-reference value at
the current axis and bump the kept-count only on kept axes. -/
def stepf (worldKeep : List Nat) (inputs slicedOut : List Int)
    (st : List Int × Nat) (iworld : Nat) : List Int × Nat :=
  (st.1 ++ [if iworld ∈ worldKeep then inputs.getD st.2 0 else slicedOut.getD iworld 0],
    st.2 + (if iworld ∈ worldKeep then 1 else 0))

/-- Number of kept axes with index strictly below `n`. -/
def keptBelow (worldKeep : List Nat) (n : Nat) : Nat :=
  (List.range n).countP (fun i => decide (i ∈ worldKeep))

/-- Loop invariant after processing the first `n` axes: shape (length), counter
(kept-count), and positional characterization of each entry. -/
def AssembleInv (worldKeep : List Nat) (inputs slicedOut : List Int)
    (n : Nat) (st : List Int × Nat) : Prop :=
  st.1.length = n ∧
  st.2 = keptBelow worldKeep n ∧
  (∀ j, j < n → st.1.getD j 0 =
    (if j ∈ worldKeep then inputs.getD (keptBelow worldKeep j) 0 else slicedOut.getD j 0))
/-- The accumulator function produced by desugaring the `for iworld in [0:worldNDim]`
loop of `implementation_assemble`.  The state is `(iworldCurr, result) : Nat × List Int`,
i.e. the SWAP of `stepf`'s `(list, count)` layout: the kept-count is component `.1`
and the accumulated list is component `.2`. -/
def loopBody (worldKeep : List Nat) (inputs slicedOut : List Int)
    (st : Nat × List Int) (iworld : Nat) : Nat × List Int :=
  if iworld ∈ worldKeep then (st.1 + 1, st.2 ++ [inputs.getD st.1 0])
  else (st.1, st.2 ++ [slicedOut.getD iworld 0])

theorem impl_as_swapped_fold (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut : List Int) :
    implementation_assemble worldNDim worldKeep inputs slicedOut =
      (List.foldl (loopBody worldKeep inputs slicedOut) ((0 : Nat), ([] : List Int))
        (List.range' 0 worldNDim)).2 := by
  have key : ∀ (L : List Nat) (n : Nat) (acc : List Int),
      (forIn L (⟨n, acc⟩ : MProd Nat (List Int)) fun iworld r =>
        (if iworld ∈ worldKeep then pure (ForInStep.yield ⟨r.fst + 1, r.snd ++ [inputs.getD r.fst 0]⟩)
         else pure (ForInStep.yield ⟨r.fst, r.snd ++ [slicedOut.getD iworld 0]⟩) : Id _)).run.snd
        = (List.foldl (loopBody worldKeep inputs slicedOut) (n, acc) L).2 := by
    intro L
    induction L with
    | nil => intro n acc; rfl
    | cons a t ih =>
      intro n acc
      simp only [List.forIn_cons, loopBody, List.foldl_cons]
      by_cases h : a ∈ worldKeep
      · simp only [h, if_true]
        exact ih (n + 1) (acc ++ [inputs.getD n 0])
      · simp only [h, if_false]
        exact ih n (acc ++ [slicedOut.getD a 0])
  simp only [implementation_assemble, Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size,
    Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
  exact key (List.range' 0 worldNDim) 0 []

theorem loopBody_step_swaps_stepf (worldKeep : List Nat) (inputs slicedOut : List Int)
    (c : Nat) (r : List Int) (a : Nat) :
    loopBody worldKeep inputs slicedOut (c, r) a =
      ((stepf worldKeep inputs slicedOut (r, c) a).2,
       (stepf worldKeep inputs slicedOut (r, c) a).1) := by
  unfold loopBody stepf
  by_cases h : a ∈ worldKeep <;> simp [h]

theorem foldl_loopBody_swaps_stepf (worldKeep : List Nat) (inputs slicedOut : List Int)
    (l : List Nat) (c : Nat) (r : List Int) :
    List.foldl (loopBody worldKeep inputs slicedOut) (c, r) l =
      ((List.foldl (stepf worldKeep inputs slicedOut) (r, c) l).2,
       (List.foldl (stepf worldKeep inputs slicedOut) (r, c) l).1) := by
  induction l generalizing c r with
  | nil => rfl
  | cons a l' ih =>
    simp only [List.foldl_cons]
    rw [loopBody_step_swaps_stepf]
    exact ih (stepf worldKeep inputs slicedOut (r, c) a).2
             (stepf worldKeep inputs slicedOut (r, c) a).1

theorem impl_eq_foldl (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int) :
    implementation_assemble worldNDim worldKeep inputs slicedOut =
      (List.foldl (stepf worldKeep inputs slicedOut) (([] : List Int), (0 : Nat))
        (List.range worldNDim)).1 := by
  rw [impl_as_swapped_fold, foldl_loopBody_swaps_stepf, List.range_eq_range']

theorem keptBelow_succ (worldKeep : List Nat) (n : Nat) :
    keptBelow worldKeep (n + 1) =
      keptBelow worldKeep n + (if n ∈ worldKeep then 1 else 0) := by
  simp only [keptBelow, List.range_succ, List.countP_append, List.countP_cons,
    List.countP_nil]
  by_cases h : n ∈ worldKeep <;> simp [h]

theorem sorted_getD_lt_of_lt (worldKeep : List Nat)
    (hsorted : worldKeep.Sorted (· < ·)) (a b : Nat) :
    a < b → b < worldKeep.length → worldKeep.getD a 0 < worldKeep.getD b 0 := by
  intro hab hb
  have ha : a < worldKeep.length := lt_trans hab hb
  rw [List.getD_eq_getElem worldKeep 0 ha, List.getD_eq_getElem worldKeep 0 hb]
  exact List.pairwise_iff_get.1 hsorted ⟨a, ha⟩ ⟨b, hb⟩ hab

theorem count_below (worldKeep : List Nat) (hsorted : worldKeep.Sorted (· < ·)) (c : Nat) :
    c < worldKeep.length → keptBelow worldKeep (worldKeep.getD c 0) = c := by
  intro hc
  have hbridge : keptBelow worldKeep (worldKeep.getD c 0)
      = worldKeep.countP (fun x => decide (x < worldKeep.getD c 0)) := by
    unfold keptBelow
    rw [List.countP_eq_length_filter, List.countP_eq_length_filter]
    apply List.Perm.length_eq
    apply (List.perm_ext_iff_of_nodup ?_ ?_).mpr
    · intro a
      simp only [List.mem_filter, List.mem_range, decide_eq_true_eq]
      exact ⟨fun ⟨h1, h2⟩ => ⟨h2, h1⟩, fun ⟨h1, h2⟩ => ⟨h2, h1⟩⟩
    · exact (List.nodup_range).filter _
    · exact (List.Pairwise.nodup hsorted).filter _
  rw [hbridge]
  have hval : worldKeep.getD c 0 = worldKeep[c] := by rw [List.getD_eq_getElem worldKeep 0 hc]
  rw [hval]
  set v := worldKeep[c] with hv
  conv_lhs => rw [show worldKeep = worldKeep.take c ++ worldKeep.drop c from
    (List.take_append_drop c worldKeep).symm]
  rw [List.countP_append]
  have htake : (worldKeep.take c).countP (fun x => decide (x < v)) = (worldKeep.take c).length := by
    rw [List.countP_eq_length]
    intro x hx
    simp only [decide_eq_true_eq]
    rw [List.mem_take_iff_getElem] at hx
    obtain ⟨i, hi, rfl⟩ := hx
    have hi' : i < c := lt_of_lt_of_le hi (min_le_left _ _)
    rw [hv]
    exact List.pairwise_iff_getElem.mp hsorted i c (by omega) hc hi'
  have hdrop : (worldKeep.drop c).countP (fun x => decide (x < v)) = 0 := by
    rw [List.countP_eq_zero]
    intro x hx
    simp only [decide_eq_true_eq, not_lt]
    rw [List.mem_drop_iff_getElem] at hx
    obtain ⟨i, hi, rfl⟩ := hx
    rcases Nat.eq_zero_or_pos i with hi0 | hipos
    · subst hi0; simp [hv]
    · rw [hv]
      have : worldKeep[c] < worldKeep[c + i] :=
        List.pairwise_iff_getElem.mp hsorted c (c + i) hc (by omega) (by omega)
      exact le_of_lt this
  rw [htake, hdrop, List.length_take, Nat.min_eq_left (le_of_lt hc), Nat.add_zero]

theorem Inv_init (worldKeep : List Nat) (inputs slicedOut : List Int) :
    AssembleInv worldKeep inputs slicedOut 0 (([] : List Int), (0 : Nat)) := by
  refine ⟨rfl, ?_, ?_⟩
  · simp [keptBelow]
  · intro j hj
    exact absurd hj (Nat.not_lt_zero j)

theorem Inv_step (worldKeep : List Nat) (inputs slicedOut : List Int)
    (n : Nat) (st : List Int × Nat) :
    AssembleInv worldKeep inputs slicedOut n st →
      AssembleInv worldKeep inputs slicedOut (n + 1)
        (stepf worldKeep inputs slicedOut st n) := by
  intro h
  obtain ⟨hlen, hcnt, hpos⟩ := h
  unfold stepf AssembleInv
  refine ⟨?_, ?_, ?_⟩
  · simp [hlen]
  · rw [keptBelow_succ, hcnt]
  · intro j hj
    rcases Nat.lt_succ_iff_lt_or_eq.mp hj with hjlt | hjeq
    · rw [List.getD_append _ _ _ _ (by rw [hlen]; exact hjlt)]
      have hjn : j < n := hjlt
      simpa using hpos j hjn
    · subst hjeq
      rw [List.getD_append_right _ _ _ _ (by rw [hlen])]
      simp [hlen, hcnt]

theorem Inv_fold (worldKeep : List Nat) (inputs slicedOut : List Int) (m : Nat) :
    AssembleInv worldKeep inputs slicedOut m
      (List.foldl (stepf worldKeep inputs slicedOut) (([] : List Int), (0 : Nat))
        (List.range m)) := by
  induction m with
  | zero => exact Inv_init worldKeep inputs slicedOut
  | succ n ih =>
    rw [List.range_succ, List.foldl_append]
    exact Inv_step worldKeep inputs slicedOut n _ ih

theorem length_atom (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int) :
    (implementation_assemble worldNDim worldKeep inputs slicedOut).length = worldNDim := by
  rw [impl_eq_foldl]
  exact (Inv_fold worldKeep inputs slicedOut worldNDim).1

theorem omitted_atom (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int) :
    ∀ iworld, iworld < worldNDim → iworld ∉ worldKeep →
      (implementation_assemble worldNDim worldKeep inputs slicedOut).getD iworld 0 =
        slicedOut.getD iworld 0 := by
  intro iworld hlt hnin
  rw [impl_eq_foldl]
  obtain ⟨_, _, h3⟩ := Inv_fold worldKeep inputs slicedOut worldNDim
  rw [h3 iworld hlt]
  simp [hnin]

theorem kept_atom (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int)
    (hsorted : worldKeep.Sorted (· < ·)) (hmem : ∀ i ∈ worldKeep, i < worldNDim) :
    ∀ c, c < worldKeep.length →
      (implementation_assemble worldNDim worldKeep inputs slicedOut).getD
        (worldKeep.getD c 0) 0 = inputs.getD c 0 := by
  intro c hc
  rw [impl_eq_foldl]
  obtain ⟨hlen, hcount, hpos⟩ := Inv_fold worldKeep inputs slicedOut worldNDim
  have hmemk : worldKeep.getD c 0 ∈ worldKeep := by
    rw [List.getD_eq_getElem worldKeep 0 hc]
    exact List.getElem_mem hc
  have hj : worldKeep.getD c 0 < worldNDim := hmem _ hmemk
  have hp := hpos (worldKeep.getD c 0) hj
  rw [if_pos hmemk] at hp
  rw [hp, count_below worldKeep hsorted c hc]

theorem correct_assemble :
    ∀ (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int),
      worldKeep.Sorted (· < ·) →
      (∀ i ∈ worldKeep, i < worldNDim) →
      inputs.length = worldKeep.length →
      slicedOut.length = worldNDim →
      problem_spec_assemble worldNDim worldKeep inputs slicedOut
        (implementation_assemble worldNDim worldKeep inputs slicedOut) := by
  intro worldNDim worldKeep inputs slicedOut hsorted hmem hinlen hsllen
  refine ⟨length_atom worldNDim worldKeep inputs slicedOut,
    omitted_atom worldNDim worldKeep inputs slicedOut,
    kept_atom worldNDim worldKeep inputs slicedOut hsorted hmem⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial (verify=>correct falsification) audit of astropy__astropy-13579 lean bundle.

SPEC ANALYSIS: problem_spec_assemble is a COMPLETE positional characterization of result: (1) result.length = worldNDim; (2) every omitted index iworld<worldNDim, iworld not-in worldKeep -> slicedOut.getD iworld 0; (3) every kept position worldKeep.getD c 0 (c<worldKeep.length) -> inputs.getD c 0. Precondition worldKeep.Sorted (<) makes worldKeep strictly increasing hence distinct, so clause (3) binds each kept position to a UNIQUE c, clause (2) binds every omitted position, length fixes the count => result is UNIQUELY determined on the entire preconditioned domain. Real SlicedLowLevelWCS objects satisfy all 4 preconditions, so any proof-closing impl must equal gold on all real inputs => its faithful patch resolves. No verify=>correct gap is structurally possible.

ATTACKS (all same_spec=True via markers.same_spec + LeanBackend; impl region edited only, axioms/pure/pre/post byte-identical): atk_1 prepatch bug omitted-axis constant (1:Int); atk_2 off-by-one kept cursor inputs.getD(iworldCurr+1) [boundary]; atk_3 branch swap kept<-slicedOut omitted<-inputs; atk_4 omitted-axis shift slicedOut.getD(iworld+1) [boundary]; atk_5 return result.reverse [control-flow-effect]; atk_6 prepend (0:Int) breaking length+positions [control-flow/partial-domain]; atk_7 ungrounded-oracle echo via (List.range worldNDim).map indexing inputs by iworld not the kept cursor.

COMMANDS: same_spec via python -c 'from swebench_unified.markers import same_spec; ...' => all 7 True. Verify: bash scripts/lean_verify.sh <atk>.lean (parallel, <=4). RESULTS: atk_1..7 exit=1 (proof does NOT close; genuine 'error: Type mismatch' at carried gold proof line ~118/125, NOT syntax/sorry/timeout). pos_control.lean (gold Solution.lean) exit=0. #print axioms correct_assemble on pos control => [propext, Classical.choice, Quot.sound] — clean, no sorryAx.

MATERIALIZED PATCHES / RESOLVE RUNS: none required — NO wrong impl produced a closing clean-axiom proof, so there is no attack whose faithful patch must be resolve-tested. patches={} accordingly. (The uniqueness argument above explains why no same-spec wrong impl can verify.)

REFINEMENT.MD AUDIT (A-leg focus): legs are R (acc init: result=[]/iworldCurr), I (for iworld in range walk), R (kept-branch supplied value world_arrays[iworld_curr]<->inputs positional), A-reference (else-branch omitted-axis fill slicedOut.getD iworld 0 <-> sliced_out_world_coords[iworld], produced by unchanged _pixel_to_world_values_all, validated == real captured world_arrays_new by conformance_check.py seed 20240629 over 120k+ inputs + boundary + coupled issue header), R (return result). No kind-3 leg; axioms region empty (no consumed callee axiom, G-AX skip stub is appropriate). The single A-reference correspondence to the real callee holds. R/I legs mechanically covered by G-CONF.

VERDICT: SOUND — 7 distinct same-spec wrong impls (prepatch bug + boundary + branch-swap + control-flow-effect + partial-domain + ungrounded-oracle echo) all fail to verify; positive control verifies clean; no closing-clean-axiom wrong impl exists to break the spec.

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
Reassembling a full-length coordinate vector from a reduced one.

A reduced view of a coordinate system keeps only some of the axes of a larger
underlying system. Going back from the reduced view to the underlying system
requires rebuilding a full-length coordinate vector: the underlying system has
`worldNDim` axes, of which a sorted subset `worldKeep` is retained by the view.

To rebuild the full vector, walk the underlying axes in order. For each axis:

* if the axis is one of the kept axes, take the next value from the supplied
  reduced vector (`inputs`), consuming those values left-to-right;
* otherwise the axis is omitted from the reduced view, so its value is not
  supplied by the caller — fill it with the reference value for that axis,
  read from a per-axis reference vector `slicedOut` indexed by the underlying
  axis number.

The result is a vector of length `worldNDim`: every kept axis carries the
corresponding supplied value, and every omitted axis carries its reference
value. The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the reassembly is spelled
-- out concretely as positional placement of supplied values into kept axes and
-- reference values into the omitted axes. The reference vector is taken as an
-- input (it is produced upstream and is not part of the reassembly itself).
-- axioms-end

-- pure-start
-- No additional pure helpers are needed; the predicate is stated directly with
-- list length and positional (`getD`) lookups.
-- pure-end

-- post-conditions-start
/-- The reassembled vector `result` has one entry per underlying axis:

* it has length `worldNDim`;
* every omitted axis (`iworld < worldNDim` with `iworld ∉ worldKeep`) carries the
  reference value `slicedOut.getD iworld`;
* the `c`-th kept axis (`worldKeep.getD c`, for `c < worldKeep.length`) carries
  the `c`-th supplied value `inputs.getD c`.

Together these pin every position of `result`. -/
def problem_spec_assemble (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut result : List Int) : Prop :=
  result.length = worldNDim ∧
  (∀ iworld, iworld < worldNDim → iworld ∉ worldKeep →
      result.getD iworld 0 = slicedOut.getD iworld 0) ∧
  (∀ c, c < worldKeep.length →
      result.getD (worldKeep.getD c 0) 0 = inputs.getD c 0)
-- post-conditions-end

-- impl-start
def implementation_assemble (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut : List Int) : List Int := Id.run do
  let mut result : List Int := []
  let mut iworldCurr : Nat := 0
  for iworld in [0:worldNDim] do
    if iworld ∈ worldKeep then
      result := result ++ [inputs.getD iworldCurr 0]
      iworldCurr := iworldCurr + 1
    else
      result := result ++ [slicedOut.getD iworld 0]
  return result
-- impl-end


-- proof-start
/-- Pure model of one loop iteration: append the supplied-or-reference value at
the current axis and bump the kept-count only on kept axes. -/
def stepf (worldKeep : List Nat) (inputs slicedOut : List Int)
    (st : List Int × Nat) (iworld : Nat) : List Int × Nat :=
  (st.1 ++ [if iworld ∈ worldKeep then inputs.getD st.2 0 else slicedOut.getD iworld 0],
    st.2 + (if iworld ∈ worldKeep then 1 else 0))

/-- Number of kept axes with index strictly below `n`. -/
def keptBelow (worldKeep : List Nat) (n : Nat) : Nat :=
  (List.range n).countP (fun i => decide (i ∈ worldKeep))

/-- Loop invariant after processing the first `n` axes: shape (length), counter
(kept-count), and positional characterization of each entry. -/
def AssembleInv (worldKeep : List Nat) (inputs slicedOut : List Int)
    (n : Nat) (st : List Int × Nat) : Prop :=
  st.1.length = n ∧
  st.2 = keptBelow worldKeep n ∧
  (∀ j, j < n → st.1.getD j 0 =
    (if j ∈ worldKeep then inputs.getD (keptBelow worldKeep j) 0 else slicedOut.getD j 0))
/-- The accumulator function produced by desugaring the `for iworld in [0:worldNDim]`
loop of `implementation_assemble`.  The state is `(iworldCurr, result) : Nat × List Int`,
i.e. the SWAP of `stepf`'s `(list, count)` layout: the kept-count is component `.1`
and the accumulated list is component `.2`. -/
def loopBody (worldKeep : List Nat) (inputs slicedOut : List Int)
    (st : Nat × List Int) (iworld : Nat) : Nat × List Int :=
  if iworld ∈ worldKeep then (st.1 + 1, st.2 ++ [inputs.getD st.1 0])
  else (st.1, st.2 ++ [slicedOut.getD iworld 0])

theorem impl_as_swapped_fold (worldNDim : Nat) (worldKeep : List Nat)
    (inputs slicedOut : List Int) :
    implementation_assemble worldNDim worldKeep inputs slicedOut =
      (List.foldl (loopBody worldKeep inputs slicedOut) ((0 : Nat), ([] : List Int))
        (List.range' 0 worldNDim)).2 := by
  have key : ∀ (L : List Nat) (n : Nat) (acc : List Int),
      (forIn L (⟨n, acc⟩ : MProd Nat (List Int)) fun iworld r =>
        (if iworld ∈ worldKeep then pure (ForInStep.yield ⟨r.fst + 1, r.snd ++ [inputs.getD r.fst 0]⟩)
         else pure (ForInStep.yield ⟨r.fst, r.snd ++ [slicedOut.getD iworld 0]⟩) : Id _)).run.snd
        = (List.foldl (loopBody worldKeep inputs slicedOut) (n, acc) L).2 := by
    intro L
    induction L with
    | nil => intro n acc; rfl
    | cons a t ih =>
      intro n acc
      simp only [List.forIn_cons, loopBody, List.foldl_cons]
      by_cases h : a ∈ worldKeep
      · simp only [h, if_true]
        exact ih (n + 1) (acc ++ [inputs.getD n 0])
      · simp only [h, if_false]
        exact ih n (acc ++ [slicedOut.getD a 0])
  simp only [implementation_assemble, Id.run, Std.Range.forIn_eq_forIn_range', Std.Range.size,
    Nat.sub_zero, Nat.add_sub_cancel, Nat.div_one]
  exact key (List.range' 0 worldNDim) 0 []

theorem loopBody_step_swaps_stepf (worldKeep : List Nat) (inputs slicedOut : List Int)
    (c : Nat) (r : List Int) (a : Nat) :
    loopBody worldKeep inputs slicedOut (c, r) a =
      ((stepf worldKeep inputs slicedOut (r, c) a).2,
       (stepf worldKeep inputs slicedOut (r, c) a).1) := by
  unfold loopBody stepf
  by_cases h : a ∈ worldKeep <;> simp [h]

theorem foldl_loopBody_swaps_stepf (worldKeep : List Nat) (inputs slicedOut : List Int)
    (l : List Nat) (c : Nat) (r : List Int) :
    List.foldl (loopBody worldKeep inputs slicedOut) (c, r) l =
      ((List.foldl (stepf worldKeep inputs slicedOut) (r, c) l).2,
       (List.foldl (stepf worldKeep inputs slicedOut) (r, c) l).1) := by
  induction l generalizing c r with
  | nil => rfl
  | cons a l' ih =>
    simp only [List.foldl_cons]
    rw [loopBody_step_swaps_stepf]
    exact ih (stepf worldKeep inputs slicedOut (r, c) a).2
             (stepf worldKeep inputs slicedOut (r, c) a).1

theorem impl_eq_foldl (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int) :
    implementation_assemble worldNDim worldKeep inputs slicedOut =
      (List.foldl (stepf worldKeep inputs slicedOut) (([] : List Int), (0 : Nat))
        (List.range worldNDim)).1 := by
  rw [impl_as_swapped_fold, foldl_loopBody_swaps_stepf, List.range_eq_range']

theorem keptBelow_succ (worldKeep : List Nat) (n : Nat) :
    keptBelow worldKeep (n + 1) =
      keptBelow worldKeep n + (if n ∈ worldKeep then 1 else 0) := by
  simp only [keptBelow, List.range_succ, List.countP_append, List.countP_cons,
    List.countP_nil]
  by_cases h : n ∈ worldKeep <;> simp [h]

theorem sorted_getD_lt_of_lt (worldKeep : List Nat)
    (hsorted : worldKeep.Sorted (· < ·)) (a b : Nat) :
    a < b → b < worldKeep.length → worldKeep.getD a 0 < worldKeep.getD b 0 := by
  intro hab hb
  have ha : a < worldKeep.length := lt_trans hab hb
  rw [List.getD_eq_getElem worldKeep 0 ha, List.getD_eq_getElem worldKeep 0 hb]
  exact List.pairwise_iff_get.1 hsorted ⟨a, ha⟩ ⟨b, hb⟩ hab

theorem count_below (worldKeep : List Nat) (hsorted : worldKeep.Sorted (· < ·)) (c : Nat) :
    c < worldKeep.length → keptBelow worldKeep (worldKeep.getD c 0) = c := by
  intro hc
  have hbridge : keptBelow worldKeep (worldKeep.getD c 0)
      = worldKeep.countP (fun x => decide (x < worldKeep.getD c 0)) := by
    unfold keptBelow
    rw [List.countP_eq_length_filter, List.countP_eq_length_filter]
    apply List.Perm.length_eq
    apply (List.perm_ext_iff_of_nodup ?_ ?_).mpr
    · intro a
      simp only [List.mem_filter, List.mem_range, decide_eq_true_eq]
      exact ⟨fun ⟨h1, h2⟩ => ⟨h2, h1⟩, fun ⟨h1, h2⟩ => ⟨h2, h1⟩⟩
    · exact (List.nodup_range).filter _
    · exact (List.Pairwise.nodup hsorted).filter _
  rw [hbridge]
  have hval : worldKeep.getD c 0 = worldKeep[c] := by rw [List.getD_eq_getElem worldKeep 0 hc]
  rw [hval]
  set v := worldKeep[c] with hv
  conv_lhs => rw [show worldKeep = worldKeep.take c ++ worldKeep.drop c from
    (List.take_append_drop c worldKeep).symm]
  rw [List.countP_append]
  have htake : (worldKeep.take c).countP (fun x => decide (x < v)) = (worldKeep.take c).length := by
    rw [List.countP_eq_length]
    intro x hx
    simp only [decide_eq_true_eq]
    rw [List.mem_take_iff_getElem] at hx
    obtain ⟨i, hi, rfl⟩ := hx
    have hi' : i < c := lt_of_lt_of_le hi (min_le_left _ _)
    rw [hv]
    exact List.pairwise_iff_getElem.mp hsorted i c (by omega) hc hi'
  have hdrop : (worldKeep.drop c).countP (fun x => decide (x < v)) = 0 := by
    rw [List.countP_eq_zero]
    intro x hx
    simp only [decide_eq_true_eq, not_lt]
    rw [List.mem_drop_iff_getElem] at hx
    obtain ⟨i, hi, rfl⟩ := hx
    rcases Nat.eq_zero_or_pos i with hi0 | hipos
    · subst hi0; simp [hv]
    · rw [hv]
      have : worldKeep[c] < worldKeep[c + i] :=
        List.pairwise_iff_getElem.mp hsorted c (c + i) hc (by omega) (by omega)
      exact le_of_lt this
  rw [htake, hdrop, List.length_take, Nat.min_eq_left (le_of_lt hc), Nat.add_zero]

theorem Inv_init (worldKeep : List Nat) (inputs slicedOut : List Int) :
    AssembleInv worldKeep inputs slicedOut 0 (([] : List Int), (0 : Nat)) := by
  refine ⟨rfl, ?_, ?_⟩
  · simp [keptBelow]
  · intro j hj
    exact absurd hj (Nat.not_lt_zero j)

theorem Inv_step (worldKeep : List Nat) (inputs slicedOut : List Int)
    (n : Nat) (st : List Int × Nat) :
    AssembleInv worldKeep inputs slicedOut n st →
      AssembleInv worldKeep inputs slicedOut (n + 1)
        (stepf worldKeep inputs slicedOut st n) := by
  intro h
  obtain ⟨hlen, hcnt, hpos⟩ := h
  unfold stepf AssembleInv
  refine ⟨?_, ?_, ?_⟩
  · simp [hlen]
  · rw [keptBelow_succ, hcnt]
  · intro j hj
    rcases Nat.lt_succ_iff_lt_or_eq.mp hj with hjlt | hjeq
    · rw [List.getD_append _ _ _ _ (by rw [hlen]; exact hjlt)]
      have hjn : j < n := hjlt
      simpa using hpos j hjn
    · subst hjeq
      rw [List.getD_append_right _ _ _ _ (by rw [hlen])]
      simp [hlen, hcnt]

theorem Inv_fold (worldKeep : List Nat) (inputs slicedOut : List Int) (m : Nat) :
    AssembleInv worldKeep inputs slicedOut m
      (List.foldl (stepf worldKeep inputs slicedOut) (([] : List Int), (0 : Nat))
        (List.range m)) := by
  induction m with
  | zero => exact Inv_init worldKeep inputs slicedOut
  | succ n ih =>
    rw [List.range_succ, List.foldl_append]
    exact Inv_step worldKeep inputs slicedOut n _ ih

theorem length_atom (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int) :
    (implementation_assemble worldNDim worldKeep inputs slicedOut).length = worldNDim := by
  rw [impl_eq_foldl]
  exact (Inv_fold worldKeep inputs slicedOut worldNDim).1

theorem omitted_atom (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int) :
    ∀ iworld, iworld < worldNDim → iworld ∉ worldKeep →
      (implementation_assemble worldNDim worldKeep inputs slicedOut).getD iworld 0 =
        slicedOut.getD iworld 0 := by
  intro iworld hlt hnin
  rw [impl_eq_foldl]
  obtain ⟨_, _, h3⟩ := Inv_fold worldKeep inputs slicedOut worldNDim
  rw [h3 iworld hlt]
  simp [hnin]

theorem kept_atom (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int)
    (hsorted : worldKeep.Sorted (· < ·)) (hmem : ∀ i ∈ worldKeep, i < worldNDim) :
    ∀ c, c < worldKeep.length →
      (implementation_assemble worldNDim worldKeep inputs slicedOut).getD
        (worldKeep.getD c 0) 0 = inputs.getD c 0 := by
  intro c hc
  rw [impl_eq_foldl]
  obtain ⟨hlen, hcount, hpos⟩ := Inv_fold worldKeep inputs slicedOut worldNDim
  have hmemk : worldKeep.getD c 0 ∈ worldKeep := by
    rw [List.getD_eq_getElem worldKeep 0 hc]
    exact List.getElem_mem hc
  have hj : worldKeep.getD c 0 < worldNDim := hmem _ hmemk
  have hp := hpos (worldKeep.getD c 0) hj
  rw [if_pos hmemk] at hp
  rw [hp, count_below worldKeep hsorted c hc]

theorem correct_assemble :
    ∀ (worldNDim : Nat) (worldKeep : List Nat) (inputs slicedOut : List Int),
      worldKeep.Sorted (· < ·) →
      (∀ i ∈ worldKeep, i < worldNDim) →
      inputs.length = worldKeep.length →
      slicedOut.length = worldNDim →
      problem_spec_assemble worldNDim worldKeep inputs slicedOut
        (implementation_assemble worldNDim worldKeep inputs slicedOut) := by
  intro worldNDim worldKeep inputs slicedOut hsorted hmem hinlen hsllen
  refine ⟨length_atom worldNDim worldKeep inputs slicedOut,
    omitted_atom worldNDim worldKeep inputs slicedOut,
    kept_atom worldNDim worldKeep inputs slicedOut hsorted hmem⟩

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial (verify=>correct falsification) audit of astropy__astropy-13579 lean bundle.

SPEC ANALYSIS: problem_spec_assemble is a COMPLETE positional characterization of result: (1) result.length = worldNDim; (2) every omitted index iworld<worldNDim, iworld not-in worldKeep -> slicedOut.getD iworld 0; (3) every kept position worldKeep.getD c 0 (c<worldKeep.length) -> inputs.getD c 0. Precondition worldKeep.Sorted (<) makes worldKeep strictly increasing hence distinct, so clause (3) binds each kept position to a UNIQUE c, clause (2) binds every omitted position, length fixes the count => result is UNIQUELY determined on the entire preconditioned domain. Real SlicedLowLevelWCS objects satisfy all 4 preconditions, so any proof-closing impl must equal gold on all real inputs => its faithful patch resolves. No verify=>correct gap is structurally possible.

ATTACKS (all same_spec=True via markers.same_spec + LeanBackend; impl region edited only, axioms/pure/pre/post byte-identical): atk_1 prepatch bug omitted-axis constant (1:Int); atk_2 off-by-one kept cursor inputs.getD(iworldCurr+1) [boundary]; atk_3 branch swap kept<-slicedOut omitted<-inputs; atk_4 omitted-axis shift slicedOut.getD(iworld+1) [boundary]; atk_5 return result.reverse [control-flow-effect]; atk_6 prepend (0:Int) breaking length+positions [control-flow/partial-domain]; atk_7 ungrounded-oracle echo via (List.range worldNDim).map indexing inputs by iworld not the kept cursor.

COMMANDS: same_spec via python -c 'from swebench_unified.markers import same_spec; ...' => all 7 True. Verify: bash scripts/lean_verify.sh <atk>.lean (parallel, <=4). RESULTS: atk_1..7 exit=1 (proof does NOT close; genuine 'error: Type mismatch' at carried gold proof line ~118/125, NOT syntax/sorry/timeout). pos_control.lean (gold Solution.lean) exit=0. #print axioms correct_assemble on pos control => [propext, Classical.choice, Quot.sound] — clean, no sorryAx.

MATERIALIZED PATCHES / RESOLVE RUNS: none required — NO wrong impl produced a closing clean-axiom proof, so there is no attack whose faithful patch must be resolve-tested. patches={} accordingly. (The uniqueness argument above explains why no same-spec wrong impl can verify.)

REFINEMENT.MD AUDIT (A-leg focus): legs are R (acc init: result=[]/iworldCurr), I (for iworld in range walk), R (kept-branch supplied value world_arrays[iworld_curr]<->inputs positional), A-reference (else-branch omitted-axis fill slicedOut.getD iworld 0 <-> sliced_out_world_coords[iworld], produced by unchanged _pixel_to_world_values_all, validated == real captured world_arrays_new by conformance_check.py seed 20240629 over 120k+ inputs + boundary + coupled issue header), R (return result). No kind-3 leg; axioms region empty (no consumed callee axiom, G-AX skip stub is appropriate). The single A-reference correspondence to the real callee holds. R/I legs mechanically covered by G-CONF.

VERDICT: SOUND — 7 distinct same-spec wrong impls (prepatch bug + boundary + branch-swap + control-flow-effect + partial-domain + ungrounded-oracle echo) all fail to verify; positive control verifies clean; no closing-clean-axiom wrong impl exists to break the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no drift from real callee) for astropy__astropy-13579 lean bundle. The modeled function `problem_spec_assemble`/`implementation_assemble` models the `world_arrays_new` reassembly loop in SlicedLowLevelWCS.world_to_pixel_values (sliced_wcs.py:245-256 @ base 0df94ff709, confirmed byte-identical against worktree HEAD 0df94ff7097961e92fd7812036a24b145bc13ca8).

Verification performed:
1. Solution.lean compiles clean via lean_verify.sh (exit 0). `#print axioms correct_assemble` = [propext, Classical.choice, Quot.sound] only — NO sorryAx, proof is genuine.
2. same_spec(Solution.lean, Solution_prepatch.lean, lean tables) = True — spec region is byte-identical between pre/post; the only difference is impl (constant `1` vs `slicedOut.getD iworld`), which is exactly the gold edit (patch.diff: `world_arrays_new.append(1.)` -> `append(sliced_out_world_coords[iworld])`).
3. Spec is NOT too strong. All four hypotheses of correct_assemble are guaranteed by the real repo, so they never exclude a reachable input:
   - `worldKeep.Sorted (<)`: `_world_keep = np.nonzero(...)[0]` is strictly ascending, distinct.
   - `∀ i∈worldKeep, i<worldNDim`: nonzero indices over `axis_correlation_matrix[:, pixel_keep]` (rows = world_n_dim) are all `< world_n_dim`.
   - `inputs.length = worldKeep.length`: caller supplies one world value per kept axis (slice world dim = len(world_keep)); real loop indexes world_arrays[iworld_curr] up to len(world_keep)-1.
   - `slicedOut.length = worldNDim`: `sliced_out_world_coords = _pixel_to_world_values_all(...)` returns world_n_dim entries; real loop indexes it at every omitted iworld < world_n_dim.
4. Postcondition matches real behavior exactly, no over-constraint: length = world_n_dim; c-th kept axis carries inputs[c] (real: world_arrays[iworld_curr]); omitted axis carries slicedOut[iworld] (real: sliced_out_world_coords[iworld]). Together they pin every position, exactly as the real loop does.
5. G-CONF (conformance_check.py, seed 20240629, N=120000) differentially tests the shadow model against the REAL patched loop by capturing broadcasted world_arrays_new before the inverse transform — recorded status=pass, 0 disagreements. The A-reference modeling of slicedOut (produced by unchanged _pixel_to_world_values_all, taken as input) is sound: the reassembly does no arithmetic on it, only positional placement, and integer sentinels faithfully model positional float placement.

No diverging input found: on every input satisfying the (repo-guaranteed) preconditions, the modeled function agrees with the real callee. Spec is faithful and not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the Lean spec view (docstring + axioms/pure stubs + problem_spec_assemble post-conditions; impl and proof elided) against the PUBLIC problem_statement ONLY (hints_text — which explicitly names the `1` fix and the correct 'world coordinate corresponding to the pixel value' — is correctly excluded).

Mechanical screen: leakage.screen() PASSES with zero hard failures. same_spec(Solution.lean, Solution_prepatch.lean)=True (spec byte-identical; only impl/proof differ — the intended 'same spec, different impl' shape).

Semantic review (the part the lexical screen can miss):
- No gold-diff line reproduced, no diff markers, no patched file path (sliced_wcs.py), no patched module path.
- No patched repo symbol echoed: changed symbols are world_to_pixel_values / pixel_to_world_values; neither appears. The upstream callee _pixel_to_world_values_all and the edited local sliced_out_world_coords do NOT appear — the spec uses abstract renamed symbols only (worldNDim, worldKeep, inputs, slicedOut, result).
- No bug/fix narration and no echo of the pre-patch constant `1.` or the hints phrasing. The spec view never says anything 'was' one value now another; it states the CORRECT input→output relation abstractly (omitted axis carries slicedOut's reference value, kept axis carries the next supplied input). That is a legitimate behavioral specification, inherent to modeling the task, not a disclosure of the gold-edit delta.
- 'slicedOut' is a spec abstraction (a modeled input vector), not a patched def/class name, so it localizes no edit.

The gold discriminator (omitted axes must carry the reference value, not the constant 1) is the correct behavior any faithful spec must encode; the spec view encodes it without quoting the gold patch, without narrating the fix, and without revealing anything beyond the public problem_statement. No RELAXED_LEAKAGE.md present and none needed. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
