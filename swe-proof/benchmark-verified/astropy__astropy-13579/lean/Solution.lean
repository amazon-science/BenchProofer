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
