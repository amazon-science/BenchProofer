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
/-- PRE-PATCH (buggy) skeleton: the first-round inner imputer is built without the
user's chosen constant, so the per-feature fill statistic and the sentinel
replacement always use the numerical default of zero, ignoring `fillValue`. -/
def implementation_initial_fill
    (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
    InitialFillResult := Id.run do
  let fill : Rat := 0
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
