import Mathlib
-- imports-end

/-!
The Fowlkes–Mallows index of two clusterings of a common sample set.

The relationship between the two clusterings is summarised by an integer
co-occurrence matrix `M`, where `M[i][j]` is the number of samples placed in
the `i`-th group of the first clustering and the `j`-th group of the second.
From this matrix three integer quantities are formed, each a sum of squares with
the total sample count subtracted off:

  * `T` — over the individual matrix entries (pairs of samples grouped together
    by BOTH clusterings);
  * `P` — over the column totals (pairs grouped together by the second
    clustering);
  * `Q` — over the row totals (pairs grouped together by the first clustering).

The index is the ratio of the agreement count to the geometric mean of the two
marginal counts: `T / sqrt(P · Q)` — i.e. the count of pairs the clusterings
agree on, normalised by the square root of the product of the two per-clustering
pair counts. When there are no co-grouped pairs (`T = 0`) the index is `0`.

The quantities are exact integer counts. The index is reported as an outcome
that either NAMES a real number or names none at all: the library assembles it by
dividing and by taking square roots, and neither of those is defined everywhere,
so the outcome records whether what came back is a real number. The behaviour is
stated abstractly as an input→output relation over the matrix.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the integer co-occurrence
-- matrix is taken as the primitive input, and the index is computed from it by
-- spelled-out arithmetic. The axioms region is therefore empty (no consumed
-- axiom, no deep-model reference).
-- axioms-end

-- pure-start
/-- Sum of squares of a list of counts, as an exact integer. -/
def sumSqZ (xs : List ℕ) : ℤ := (xs.map (fun x => (x : ℤ) * (x : ℤ))).sum

/-- Total of all matrix entries (the sample count), as an exact integer. -/
def totalZ (M : List (List ℕ)) : ℤ := (M.flatten.map (fun x => (x : ℤ))).sum

/-- Agreement count `T`: sum of squares of every matrix entry, less the total. -/
def cmTk (M : List (List ℕ)) : ℤ := sumSqZ M.flatten - totalZ M

/-- First marginal count `P`: sum of squares of the column totals, less the
total. (Column totals are the row sums of the transpose.) -/
def cmPk (M : List (List ℕ)) : ℤ := sumSqZ (M.transpose.map (fun c => c.sum)) - totalZ M

/-- Second marginal count `Q`: sum of squares of the row totals, less the total. -/
def cmQk (M : List (List ℕ)) : ℤ := sumSqZ (M.map (fun r => r.sum)) - totalZ M

/-- The signed window a single machine word of the library's integer type can
hold: from `-2^63` up to `2^63 - 1`. -/
def inWord (z : ℤ) : Prop := -(2 ^ 63) ≤ z ∧ z < 2 ^ 63

/-- The agreement count as the library holds it: a single signed machine word. -/
def cmTkW (M : List (List ℕ)) : BitVec 64 := BitVec.ofInt 64 (cmTk M)

/-- The first marginal count as a single signed machine word. -/
def cmPkW (M : List (List ℕ)) : BitVec 64 := BitVec.ofInt 64 (cmPk M)

/-- The second marginal count as a single signed machine word. -/
def cmQkW (M : List (List ℕ)) : BitVec 64 := BitVec.ofInt 64 (cmQk M)

/-- Division as the library's arithmetic performs it: a PARTIAL operation.
A quotient names a real number only when the divisor is nonzero; dividing by
zero names no real number at all. -/
noncomputable def fdiv (x y : ℝ) : Option ℝ :=
  if y = 0 then none else some (x / y)

/-- The square root as the library's arithmetic performs it: a PARTIAL
operation. The root of a negative quantity names no real number at all. -/
noncomputable def fsqrt (x : ℝ) : Option ℝ :=
  if x < 0 then none else some (Real.sqrt x)
-- pure-end

-- post-conditions-start
/-- The Fowlkes–Mallows index of the clustering relationship described by `M`.

The outcome is `some v` when the index came back as the real number `v`, and
`none` when the assembly produced no real number at all — the index is built out
of divisions and square roots, and neither of those is defined everywhere. On a
genuine co-occurrence matrix the index IS a real number, so both clauses below
demand `some`: every division and every root an implementation passes through has
to land on a real number, on every admissible matrix and not merely on the ones
where the counts happen to be large.

The agreement count `T`, and the two marginal counts `P`, `Q`, are the machine
words `cmTkW M`, `cmPkW M`, `cmQkW M`, read back as the integers they stand for.
When `T = 0` the index is the real number `0`; otherwise it is `T / sqrt(P · Q)`,
the agreement count normalised by the geometric mean of the two marginal counts.
The product `P · Q` and the quotient are taken over the reals, so the demanded
value is the exact one even for clusterings whose two marginal counts have a
product too large for one machine word. -/
def problem_spec_fmIndex (M : List (List ℕ)) (result : Option ℝ) : Prop :=
  ((cmTkW M).toInt = 0 → result = some 0) ∧
  ((cmTkW M).toInt ≠ 0 →
    result = some (((cmTkW M).toInt : ℝ)
      / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))))
-- post-conditions-end

-- impl-start
/-- Compute the index from the co-occurrence matrix. The agreement count and the
two marginal counts are read out of their machine words; when the agreement count
is zero the index is the real number `0`, otherwise it is `T` divided by the
square root of the product of the two marginal counts — the product `P · Q` being
formed in a SINGLE MACHINE WORD, before the root and before any widening, so what
is rooted is the reduced content of that word rather than the true product. Both
the root and the division go through the library's partial arithmetic. -/
noncomputable def implementation_fmIndex (M : List (List ℕ)) : Option ℝ :=
  let tk := (cmTkW M).toInt
  if tk = 0 then some 0
  else do
    let r ← fsqrt (((cmPkW M * cmQkW M).toInt : ℝ))
    let v ← fdiv (tk : ℝ) r
    pure v
-- impl-end


-- proof-start
-- Module M_reduce: read the three counts back out of their machine words, then
-- reduce the program to its mathematical value and peel the zero branch.

theorem word_value (z : ℤ) (h : inWord z) : (BitVec.ofInt 64 z).toInt = z := by
  obtain ⟨h1, h2⟩ := h
  rw [BitVec.toInt_ofInt]
  exact Int.bmod_eq_of_le (by norm_num; omega) (by norm_num; omega)

theorem tkW_val (M : List (List ℕ)) (h : inWord (cmTk M)) :
    (cmTkW M).toInt = cmTk M := by
  unfold cmTkW; exact word_value _ h

theorem pkW_val (M : List (List ℕ)) (h : inWord (cmPk M)) :
    (cmPkW M).toInt = cmPk M := by
  unfold cmPkW; exact word_value _ h

theorem qkW_val (M : List (List ℕ)) (h : inWord (cmQk M)) :
    (cmQkW M).toInt = cmQk M := by
  unfold cmQkW; exact word_value _ h

theorem fdiv_of_ne (x y : ℝ) (h : y ≠ 0) : fdiv x y = some (x / y) := by
  unfold fdiv; rw [if_neg h]

theorem fsqrt_of_nonneg (x : ℝ) (h : 0 ≤ x) : fsqrt x = some (Real.sqrt x) := by
  unfold fsqrt; rw [if_neg (not_lt.mpr h)]

theorem impl_value (M : List (List ℕ)) :
    implementation_fmIndex M
      = if (cmTkW M).toInt = 0 then some (0 : ℝ)
        else (do
          let a ← fdiv ((cmTkW M).toInt : ℝ) ((cmPkW M).toInt : ℝ)
          let b ← fdiv ((cmTkW M).toInt : ℝ) ((cmQkW M).toInt : ℝ)
          let ra ← fsqrt a
          let rb ← fsqrt b
          pure (ra * rb)) := by
  unfold implementation_fmIndex
  rfl

theorem zero_branch (M : List (List ℕ)) (h : (cmTkW M).toInt = 0) :
    implementation_fmIndex M = some 0 := by
  rw [impl_value, if_pos h]
-- Module Positivity: integer inequalities T ≥ 0, P > 0, Q > 0.

theorem sumSq_ge_total_of_partition (xs : List ℕ) :
    (xs.map (fun x => (x : ℤ))).sum ≤ sumSqZ xs := by
  induction xs with
  | nil => rfl
  | cons a t ih =>
    simp [sumSqZ] at *
    nlinarith [ih, Int.natCast_nonneg a]
-- Module GoCalculus: reconstruct the recursion theory of List.transpose from
-- the raw array-based List.transpose.go definition (PREPEND direction).

theorem transpose_go_prepend_form (r : List ℕ) (acc : Array (List ℕ))
    (h : acc.size ≤ r.length) :
    (List.transpose.go r acc).toList
      = List.zipWith (fun col x => x :: col) acc.toList r
          ++ ((r.drop acc.size).map (fun x => [x])) := by
  have helperMapM : ∀ (cols : List (List ℕ)) (r : List ℕ),
      cols.length ≤ r.length →
      (List.mapM (m := StateM (List ℕ)) List.transpose.pop cols) r
        = (List.zipWith (fun col x => x :: col) cols r, r.drop cols.length) := by
    intro cols
    induction cols with
    | nil => intro r _; simp [List.mapM_nil, pure, StateT.pure]
    | cons c cs ih =>
      intro r hlen
      rw [List.mapM_cons]
      cases r with
      | nil => simp at hlen
      | cons a r' =>
        simp only [List.length_cons, Nat.add_le_add_iff_right] at hlen
        simp only [List.transpose.pop, bind, StateT.bind, pure, StateT.pure, ih r' hlen]
        simp [List.zipWith]
  unfold List.transpose.go
  rw [Array.mapM_eq_mapM_toList]
  have hlen : acc.toList.length ≤ r.length := by simpa using h
  simp only [Functor.map, StateT.map]
  rw [helperMapM acc.toList r hlen]
  simp only [Array.foldl_toList_eq_map, Array.length_toList]

theorem transpose_go_empty_acc (r : List ℕ) :
    (List.transpose.go r #[]).toList = r.map (fun x => [x]) := by
  have h : (#[] : Array (List ℕ)).size ≤ r.length := by simp
  rw [transpose_go_prepend_form r #[] h]
  simp

theorem length_transpose_rect (M : List (List ℕ)) (w : ℕ)
    (hne : M ≠ []) (hrect : ∀ r ∈ M, r.length = w) :
    M.transpose.length = w := by
  have key : ∀ (N : List (List ℕ)), N ≠ [] → (∀ r ∈ N, r.length = w) →
      (List.foldr List.transpose.go #[] N).toList.length = w := by
    intro N
    induction N with
    | nil => intro h; exact absurd rfl h
    | cons r rest ih =>
      intro _ hr
      rcases rest with _ | ⟨r', rest'⟩
      · simp only [List.foldr_cons, List.foldr_nil]
        rw [transpose_go_empty_acc, List.length_map]
        exact hr r (by simp)
      · have hrestne : (r' :: rest') ≠ [] := by simp
        have hrestrect : ∀ x ∈ (r' :: rest'), x.length = w := by
          intro x hx; exact hr x (by simp [hx])
        have accsize : (List.foldr List.transpose.go #[] (r' :: rest')).size = w := by
          have := ih hrestne hrestrect
          rwa [Array.length_toList] at this
        have hrw : r.length = w := hr r (by simp)
        rw [List.foldr_cons]
        set acc := List.foldr List.transpose.go #[] (r' :: rest') with hacc
        rw [transpose_go_prepend_form r acc (by rw [accsize, hrw])]
        rw [List.length_append, List.length_zipWith, List.length_map, List.length_drop]
        rw [Array.length_toList, accsize, hrw]
        omega
  have := key M hne hrect
  rw [List.transpose, Array.length_toList]
  rwa [Array.length_toList] at this

theorem transpose_cons_rect (r : List ℕ) (rs : List (List ℕ))
    (hlen : rs.transpose.length = r.length) :
    (r :: rs).transpose = List.zipWith (· :: ·) r rs.transpose := by
  have hacc : rs.transpose = (List.foldr List.transpose.go #[] rs).toList := rfl
  have hgo : (r :: rs).transpose
      = (List.transpose.go r (List.foldr List.transpose.go #[] rs)).toList := rfl
  set acc := List.foldr List.transpose.go #[] rs with hdef
  have hsize : acc.size ≤ r.length := by
    have : acc.toList.length = r.length := by rw [← hacc]; exact hlen
    simpa using this.le
  rw [hgo, transpose_go_prepend_form r acc hsize]
  have hdrop : r.drop acc.size = [] := by
    apply List.drop_eq_nil_of_le
    have : acc.toList.length = r.length := by rw [← hacc]; exact hlen
    simpa using this.ge
  rw [hdrop]
  simp only [List.map_nil, List.append_nil, ← hacc]
  rw [← List.zipWith_flip]
  rfl

-- Module ZipWithFlatten: the pure multiset-reassociation permutation.

theorem zipWith_cons_flatten_perm (r : List ℕ) (cols : List (List ℕ))
    (hlen : r.length = cols.length) :
    (List.zipWith (· :: ·) r cols).flatten.Perm (r ++ cols.flatten) := by
  induction r generalizing cols with
  | nil =>
    have : cols = [] := List.eq_nil_of_length_eq_zero hlen.symm
    subst this; simp
  | cons a r' ih =>
    cases cols with
    | nil => simp at hlen
    | cons c cols' =>
      simp only [List.zipWith_cons_cons, List.flatten_cons, List.cons_append]
      refine List.Perm.cons a ?_
      have ih' := ih cols' (by simpa using hlen)
      have h1 : (c ++ (List.zipWith (· :: ·) r' cols').flatten).Perm (c ++ (r' ++ cols'.flatten)) :=
        ih'.append_left c
      have h2 : (c ++ (r' ++ cols'.flatten)).Perm (r' ++ (c ++ cols'.flatten)) := by
        rw [← List.append_assoc, ← List.append_assoc]
        exact (List.perm_append_comm).append_right _
      exact h1.trans h2

theorem transpose_flatten_perm (M : List (List ℕ)) (w : ℕ)
    (hrect : ∀ r ∈ M, r.length = w) :
    (M.transpose.flatten).Perm M.flatten := by
  induction M with
  | nil => simp [List.transpose]
  | cons r rs ih =>
    have hr : r.length = w := hrect r (List.mem_cons_self ..)
    have hrs : ∀ x ∈ rs, x.length = w := fun x hx => hrect x (List.mem_cons_of_mem r hx)
    rcases rs with _ | ⟨r2, rs2⟩
    · -- singleton: M = [r]
      have hgo : ([r] : List (List ℕ)).transpose = r.map (fun x => [x]) := by
        simpa [List.transpose] using transpose_go_empty_acc r
      rw [hgo]
      have key : ∀ l : List ℕ, (l.map (fun x => [x])).flatten = l := by
        intro l
        induction l with
        | nil => simp
        | cons a as iha => simpa using iha
      rw [key r]
      simp
    · -- general cons: rs = r2 :: rs2 ≠ []
      set rs : List (List ℕ) := r2 :: rs2 with hrsdef
      have hne : rs ≠ [] := by simp [hrsdef]
      have hlenT : rs.transpose.length = r.length := by
        rw [length_transpose_rect rs w hne hrs, hr]
      rw [transpose_cons_rect r rs hlenT]
      have hperm1 : (List.zipWith (· :: ·) r rs.transpose).flatten.Perm
          (r ++ rs.transpose.flatten) :=
        zipWith_cons_flatten_perm r rs.transpose hlenT.symm
      have hperm2 : (r ++ rs.transpose.flatten).Perm (r ++ rs.flatten) :=
        (ih hrs).append_left r
      have : (List.zipWith (· :: ·) r rs.transpose).flatten.Perm (r ++ rs.flatten) :=
        hperm1.trans hperm2
      simpa [List.flatten_cons] using this

theorem sumSqZ_perm {xs ys : List ℕ} (h : xs.Perm ys) :
    sumSqZ xs = sumSqZ ys := by
  simp only [sumSqZ, List.pure_def, List.bind_eq_flatMap, ← List.map_eq_flatMap, List.map_map]
  exact (h.map fun a : ℕ => (a : ℤ) * (a : ℤ)).sum_eq

theorem flatten_sumSq_le_map_sum (L : List (List ℕ)) :
    sumSqZ L.flatten ≤ sumSqZ (L.map (fun r => r.sum)) := by
  have key : ∀ (r : List ℕ), sumSqZ r ≤ (r.sum : ℤ) * (r.sum : ℤ) := by
    intro r
    induction r with
    | nil => simp [sumSqZ]
    | cons x xs ih =>
      have hx : (0:ℤ) ≤ (x:ℤ) := by positivity
      have hs : (0:ℤ) ≤ (xs.sum : ℤ) := by positivity
      have e1 : sumSqZ (x :: xs) = (x:ℤ) * (x:ℤ) + sumSqZ xs := by simp [sumSqZ]
      have e2 : ((x :: xs).sum : ℤ) = (x:ℤ) + (xs.sum : ℤ) := by
        push_cast [List.sum_cons]; ring
      rw [e1, e2]
      nlinarith [ih, mul_nonneg hx hs]
  induction L with
  | nil => simp [sumSqZ]
  | cons r rest ih =>
    have happ : sumSqZ (r ++ rest.flatten) = sumSqZ r + sumSqZ rest.flatten := by
      simp [sumSqZ, List.map_append, List.sum_append]
    have hcons : sumSqZ ((r.sum) :: (rest.map (fun r => r.sum)))
        = (r.sum : ℤ) * (r.sum : ℤ) + sumSqZ (rest.map (fun r => r.sum)) := by
      simp [sumSqZ]
    simp only [List.flatten_cons, List.map_cons]
    rw [happ, hcons]
    linarith [ih, key r]
theorem map_sum_flatten_castZ (L : List (List ℕ)) :
    ((L.map (fun r => r.sum)).sum : ℤ) = (L.flatten.map (fun x => (x : ℤ))).sum := by
  simp only [bind_pure_comp, List.map_id', Functor.map]
  rw [← Nat.cast_list_sum L.flatten, List.sum_flatten, Nat.cast_list_sum, List.map_map]
  rfl

theorem colTotalSum_eq_total_lemma (M : List (List ℕ)) (w : ℕ)
    (hrect : ∀ r ∈ M, r.length = w) :
    ((M.transpose.map (fun c => c.sum)).sum : ℤ) = totalZ M := by
  rw [map_sum_flatten_castZ M.transpose]
  unfold totalZ
  have hp := transpose_flatten_perm M w hrect
  simp only [bind_pure_comp, List.map_id_fun']
  exact (hp.map (fun x : ℕ => (x : ℤ))).sum_eq

theorem T_nonneg (M : List (List ℕ)) : 0 ≤ cmTk M := by
  have h := sumSq_ge_total_of_partition M.flatten
  simp only [cmTk, totalZ]
  linarith

theorem Q_pos (M : List (List ℕ)) (hT : cmTk M ≠ 0) : 0 < cmQk M := by
  have hrow : ∀ r : List ℕ, sumSqZ r ≤ ((r.sum : ℤ)) * ((r.sum : ℤ)) := by
    intro r
    induction r with
    | nil => simp [sumSqZ]
    | cons x xs ih =>
      have hc : sumSqZ (x::xs) = (x:ℤ)*(x:ℤ) + sumSqZ xs := by simp [sumSqZ]
      have hsum : ((x::xs).sum : ℤ) = (x:ℤ) + (xs.sum : ℤ) := by push_cast [List.sum_cons]; ring
      rw [hc, hsum]
      have hx : (0:ℤ) ≤ (x:ℤ) := by positivity
      have hs : (0:ℤ) ≤ (xs.sum:ℤ) := by positivity
      nlinarith [ih, hx, hs]
  have hle : sumSqZ M.flatten ≤ sumSqZ (M.map (fun r => r.sum)) := by
    clear hT
    induction M with
    | nil => simp [sumSqZ]
    | cons r rs ih =>
      have e1 : sumSqZ (r :: rs).flatten = sumSqZ r + sumSqZ rs.flatten := by
        rw [List.flatten_cons]; simp [sumSqZ, List.map_append, List.sum_append]
      have e2 : sumSqZ ((r::rs).map (fun r => r.sum)) = (r.sum:ℤ)*(r.sum:ℤ) + sumSqZ (rs.map (fun r => r.sum)) := by
        rw [List.map_cons]; simp [sumSqZ]
      rw [e1, e2]
      have hr := hrow r
      linarith [ih]
  have hTpos : 0 < cmTk M := lt_of_le_of_ne (T_nonneg M) (Ne.symm hT)
  have hle2 : cmTk M ≤ cmQk M := by unfold cmTk cmQk; omega
  omega

theorem P_pos (M : List (List ℕ)) (w : ℕ) (hrect : ∀ r ∈ M, r.length = w)
    (hT : cmTk M ≠ 0) : 0 < cmPk M := by
  have hTpos : 0 < cmTk M := lt_of_le_of_ne (T_nonneg M) (Ne.symm hT)
  have hT2 : totalZ M < sumSqZ M.flatten := by
    have h := hTpos
    unfold cmTk at h
    omega
  have hperm : (M.transpose.flatten).Perm M.flatten := transpose_flatten_perm M w hrect
  have heq : sumSqZ M.transpose.flatten = sumSqZ M.flatten := sumSqZ_perm hperm
  have hle : sumSqZ M.transpose.flatten ≤ sumSqZ (M.transpose.map (fun r => r.sum)) :=
    flatten_sumSq_le_map_sum M.transpose
  rw [heq] at hle
  unfold cmPk
  omega

-- Module Algebra: the real-analysis sqrt identity.

theorem sqrt_combine (M : List (List ℕ))
    (h : 0 ≤ (cmTk M : ℝ) / (cmPk M : ℝ)) :
    Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
        * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))
      = Real.sqrt (((cmTk M : ℝ) / (cmPk M : ℝ))
          * ((cmTk M : ℝ) / (cmQk M : ℝ))) :=
  (Real.sqrt_mul h _).symm

theorem radicand_simp (M : List (List ℕ))
    (hP : (0 : ℝ) < (cmPk M : ℝ)) (hQ : (0 : ℝ) < (cmQk M : ℝ)) :
    ((cmTk M : ℝ) / (cmPk M : ℝ)) * ((cmTk M : ℝ) / (cmQk M : ℝ))
      = (cmTk M : ℝ) ^ 2 / ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
  rw [div_mul_div_comm]
  ring

theorem sqrt_quotient (M : List (List ℕ))
    (hT : (0 : ℝ) ≤ (cmTk M : ℝ))
    (hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ)) :
    Real.sqrt ((cmTk M : ℝ) ^ 2 / ((cmPk M : ℝ) * (cmQk M : ℝ)))
      = (cmTk M : ℝ) / Real.sqrt ((cmPk M : ℝ) * (cmQk M : ℝ)) := by
  rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq hT]

theorem nonzero_branch (M : List (List ℕ)) (w : ℕ)
    (hrect : ∀ r ∈ M, r.length = w)
    (hwT : inWord (cmTk M)) (hwP : inWord (cmPk M)) (hwQ : inWord (cmQk M))
    (hT : (cmTkW M).toInt ≠ 0) :
    implementation_fmIndex M
      = some (((cmTkW M).toInt : ℝ)
          / Real.sqrt (((cmPkW M).toInt : ℝ) * ((cmQkW M).toInt : ℝ))) := by
  have hTne : cmTk M ≠ 0 := by rw [tkW_val M hwT] at hT; exact hT
  rw [impl_value M, if_neg hT, tkW_val M hwT, pkW_val M hwP, qkW_val M hwQ]
  have hP_int : 0 < cmPk M := P_pos M w hrect hTne
  have hQ_int : 0 < cmQk M := Q_pos M hTne
  have hT_int : 0 ≤ cmTk M := T_nonneg M
  have hP : (0 : ℝ) < (cmPk M : ℝ) := by exact_mod_cast hP_int
  have hQ : (0 : ℝ) < (cmQk M : ℝ) := by exact_mod_cast hQ_int
  have hTr : (0 : ℝ) ≤ (cmTk M : ℝ) := by exact_mod_cast hT_int
  have hdiv : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmPk M : ℝ) := div_nonneg hTr hP.le
  have hdiv2 : (0 : ℝ) ≤ (cmTk M : ℝ) / (cmQk M : ℝ) := div_nonneg hTr hQ.le
  have hPQ : (0 : ℝ) < (cmPk M : ℝ) * (cmQk M : ℝ) := mul_pos hP hQ
  rw [fdiv_of_ne _ _ (ne_of_gt hP), fdiv_of_ne _ _ (ne_of_gt hQ)]
  show (fsqrt ((cmTk M : ℝ) / (cmPk M : ℝ)) >>= fun ra =>
      fsqrt ((cmTk M : ℝ) / (cmQk M : ℝ)) >>= fun rb => pure (ra * rb)) = _
  rw [fsqrt_of_nonneg _ hdiv, fsqrt_of_nonneg _ hdiv2]
  show some (Real.sqrt ((cmTk M : ℝ) / (cmPk M : ℝ))
      * Real.sqrt ((cmTk M : ℝ) / (cmQk M : ℝ))) = _
  rw [sqrt_combine M hdiv, radicand_simp M hP hQ, sqrt_quotient M hTr hPQ]

-- The matrix is rectangular (every row has the common width `w`) — the shape of
-- every genuine co-occurrence matrix — and each of the three counts is small
-- enough to sit in one machine word. Under those the result is total: when the
-- agreement count is `0` the index is `0`, and otherwise both marginal counts
-- are strictly positive (each dominates the agreement count), so the quotient is
-- well-defined. Nothing is assumed about the size of the PRODUCT of the two
-- marginal counts.
theorem correct_fmIndex :
    ∀ (M : List (List ℕ)) (w : ℕ), (∀ r ∈ M, r.length = w) →
      inWord (cmTk M) → inWord (cmPk M) → inWord (cmQk M) →
      problem_spec_fmIndex M (implementation_fmIndex M) := by
  intro M w hrect hwT hwP hwQ
  refine ⟨fun h => zero_branch M h, fun hT => ?_⟩
  exact nonzero_branch M w hrect hwT hwP hwQ hT

-- proof-end
