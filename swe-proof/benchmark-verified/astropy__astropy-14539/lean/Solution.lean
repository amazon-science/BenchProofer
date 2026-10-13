import Mathlib
-- imports-end

/-!
Comparing two table columns and reporting the rows at which they differ.

A table column carries a declared format, and the format determines the shape of
the data stored in it. An ordinary fixed-shape column holds the same number of
values in every row. A variable-length column instead holds, for each row, a
short sequence of values, and different rows may hold sequences of different
lengths.

The two shapes are compared in two different ways, and the column's declared
format is what selects between them. The selection is a property of the format
alone: it never depends on the values that happen to be stored, so two columns
with the same format are always compared the same way.

For a variable-length column the comparison is purely row-wise: the two columns
are walked row by row, and row `i` counts as a difference exactly when the
numeric closeness test — an unchanged library routine, applied to the whole
sequence stored for row `i` in the first column and the whole sequence stored for
row `i` in the second — does not report the two sequences as agreeing. The report
is the list of row indices, in increasing order, at which the two columns differ.
Nothing else about that test is assumed here: how close two values must be to
agree, and how it treats the pairs of sequences it can compare at all, are its
business, not this routine's.

For a fixed-shape column, where every row holds the same number of values, the
report is instead exactly the one produced by the flat element-by-element
comparison of the
two columns — that routine's own result, with nothing added to it and nothing
removed from it.

Each shape must get its own comparison and only its own: the row-wise comparison
for every variable-length column, the flat one for every column that is not.
-/

-- axioms-start
/-- Whether the per-row closeness test can be applied to a row at all: it relates
two stored sequences of the same length position by position, and it also accepts
a pair in which one side stores a single value, which it then relates to every
value on the other side. Presented with any other pair of lengths it reports no
answer, so a row like that is outside what a differing-row report can describe. -/
def rowsComparable (xs ys : List Int) : Bool :=
  xs.length == ys.length || xs.length == 1 || ys.length == 1

/-- Whether two columns are of the ordinary fixed-shape kind AND are relatable as
such: each of the two stores the same number of values in every one of its rows,
the two report the same number of rows, and the two row widths are widths the flat
comparison can relate — the same width, or one of them a single value it relates
to every value facing it, which is the same rule the per-row test above follows.

Storing SEVERAL values in a row is no obstacle: a fixed-shape column may hold a
small block of values in each of its rows, and the flat comparison relates two
such columns value against facing value just the same. What it has no answer for
is a RAGGED column, whose rows store sequences of differing lengths and which is
therefore not a block of one shape at all; a pair like that is outside what its
report can describe. -/
def rowsAreFixedShape (arra arrb : List (List Int)) : Bool :=
  arra.length == arrb.length &&
    arra.all (fun r => r.length == (arra.headD []).length) &&
    arrb.all (fun r => r.length == (arrb.headD []).length) &&
    rowsComparable (arra.headD []) (arrb.headD [])

-- The flat element-by-element comparison of two columns. This is the comparison
-- appropriate to an ordinary fixed-shape column, whose rows all store the same
-- number of values, and it is an UNCHANGED library routine that this code does
-- not modify.
-- It is declared opaque (signature only): what a fixed-shape column's report is
-- REQUIRED to be is exactly this routine's own result, whatever that result
-- happens to be, so no property of it is stated or assumed anywhere. The shape
-- of column it can be applied to at all is an ARGUMENT of the comparison: it has
-- no answer for a pair of columns of any other shape, so asking it about one is
-- not something this routine — or any other reporter meeting the contract below
-- — is able to express.
opaque elementwiseDiff (arra arrb : List (List Int))
    (h : rowsAreFixedShape arra arrb = true) : List Nat

-- The per-row numeric closeness test: whether the two value sequences stored for
-- one row count as agreeing. This too is an UNCHANGED library routine that this
-- code only calls, once per row, on the two whole stored sequences. It is
-- declared opaque for the same reason: the row-wise report is REQUIRED to be the
-- set of rows this test does not accept, whatever this test accepts, so nothing
-- about its treatment of tolerances or of value magnitudes is stated or assumed
-- anywhere. The pair of lengths it can be applied to at all is an ARGUMENT of
-- the test and not a matter of trust: the test has no answer for any other pair,
-- so asking it about one is not something this routine — or any other reporter
-- meeting the contract below — is able to express.
opaque rowsAgree (xs ys : List Int) (h : rowsComparable xs ys = true) : Bool
-- axioms-end

-- pure-start
/-- Whether a column's declared format makes it a variable-length column rather
than an ordinary fixed-shape one: the declared format carries a variable-length
descriptor marker. -/
def isVariableLengthFormat (fmt : List Char) : Bool :=
  fmt.contains 'P' || fmt.contains 'Q'

/-- The row indices at which two columns of value sequences differ: the
increasing list of positions `idx < arra.length` at which the per-row closeness
test does not report the sequence stored by the first column and the sequence
stored by the second as agreeing. The positions are walked as positions OF the
first column, and the fact that every one of its rows is a pair the test can
relate is an argument here too, so the only rows this report can be built from
are the stored ones. -/
def rowDiffIndices (arra arrb : List (List Int))
    (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true) :
    List Nat :=
  ((List.finRange arra.length).filter
      (fun i => !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt))).map Fin.val
-- pure-end

-- post-conditions-start
/-- The differing-row report for one pair of columns of the given format.

BOTH shapes of column are pinned, to two different reports, and the format is
what decides which. For a variable-length format the report is exactly the
row-wise difference set: the indices, in increasing order, of the rows the
per-row closeness test does not accept. For a format that is not variable-length
the report is exactly the flat element-by-element comparison's result, unaltered.

So neither comparison may be used for a column of the other shape, and neither
report may be replaced by any other value — including by a report that happens to
be correct for the other shape. -/
def problem_spec_columnDiffRows
    (fmt : List Char) (arra arrb : List (List Int))
    (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
    (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true)
    (result : List Nat) : Prop :=
  if h : isVariableLengthFormat fmt = true then
    result = rowDiffIndices arra arrb hcmp
  else
    result = elementwiseDiff arra arrb (hfix (by simpa using h))

/-- The full contract demanded of a differing-row reporter: for EVERY declared
format — variable-length or not — and every pair of columns that report the same
number of rows, the value it produces is the report required above.

The quantification over formats is part of the demand, not a convenience: a
reporter that gets the report right only for some of the formats it accepts does
not meet this contract.

Row comparability is the other side of that coin, and it enters as the reporter's
OWN argument rather than as a side condition on it: the per-row test has an answer
only for a pair of sequences it can relate, so a reporter is handed the fact that
every row of the two columns it is given is such a pair, and that fact is the only
thing entitling it — or anything it calls — to ask the test about a row at all.
Where the fact is unavailable there is no report to demand and no question to ask.
The flat comparison's own shape requirement is handed over the same way, and only
for the formats that reach it: a format that is not variable-length belongs to a
column that stores the same number of values in every row, and that is what
entitles a reporter to consult the flat comparison at all. -/
def columnDiffRowsContract
    (report : (fmt : List Char) → (arra arrb : List (List Int)) →
      (∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true) →
      (isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) →
      List Nat) : Prop :=
  ∀ (fmt : List Char) (arra arrb : List (List Int)),
    arra.length = arrb.length →
    ∀ (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
      (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true),
      problem_spec_columnDiffRows fmt arra arrb hcmp hfix (report fmt arra arrb hcmp hfix)
-- post-conditions-end

-- impl-start
def implementation_columnDiffRows
    (fmt : List Char) (arra arrb : List (List Int))
    (hcmp : ∀ idx, idx < arra.length → rowsComparable arra[idx]! arrb[idx]! = true)
    (hfix : isVariableLengthFormat fmt = false → rowsAreFixedShape arra arrb = true) :
    List Nat := Id.run do
  if hb : (fmt.contains 'P' || fmt.contains 'Q') = true then
    let mut acc : List Nat := []
    for i in List.finRange arra.length do
      if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
        acc := acc ++ [i.val]
    return acc
  else
    return elementwiseDiff arra arrb (hfix (by simpa [isVariableLengthFormat] using hb))
-- impl-end

-- proof-start
/-- The conditional-append loop over `l`, generalized over the accumulator and
over the row predicate, computes `init` followed by the filtered positions
(Route B helper). -/
theorem columnDiffRows_loop {n : Nat} (p : Fin n → Bool) (l : List (Fin n))
    (init : List Nat) :
      Id.run (forIn l init (fun i r =>
        (if p i then ForInStep.yield (r ++ [i.val])
         else ForInStep.yield r : Id (ForInStep (List Nat)))))
      = init ++ (l.filter p).map Fin.val := by
  induction l generalizing init with
  | nil => simp only [List.forIn_nil, List.filter_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.filter_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : p a = true
    · rw [if_pos h]; simp only [ih, h, if_true, List.map_cons]; simp [List.append_assoc]
    · rw [if_neg h]; simp only [Bool.not_eq_true] at h; simp only [ih, h]; simp

theorem correct_columnDiffRows :
    columnDiffRowsContract implementation_columnDiffRows := by
  intro fmt arra arrb _ hcmp hfix
  unfold problem_spec_columnDiffRows implementation_columnDiffRows
    isVariableLengthFormat rowDiffIndices
  by_cases hc : (fmt.contains 'P' || fmt.contains 'Q') = true
  · simp only [hc, dif_pos]
    have h2 : (Id.run (do
        let r ← forIn (List.finRange arra.length) ([] : List Nat) fun i r =>
              if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then do
                pure PUnit.unit
                pure (ForInStep.yield (r ++ [i.val]))
              else do
                pure PUnit.unit
                pure (ForInStep.yield r)
        pure r))
        = Id.run (forIn (List.finRange arra.length) ([] : List Nat) (fun i r =>
          (if !rowsAgree arra[i.val]! arrb[i.val]! (hcmp i.val i.isLt) then
             ForInStep.yield (r ++ [i.val])
           else ForInStep.yield r : Id (ForInStep (List Nat))))) := rfl
    rw [h2, columnDiffRows_loop]
    simp
  · simp only [hc]
    rfl
-- proof-end
