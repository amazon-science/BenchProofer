import Mathlib
-- imports-end

/-!
Normalizing the indentation of a multi-line block of text.

The routine takes a block of text already split into lines (tab stops having
been expanded beforehand) and returns the block with its indentation uniformly
normalized, following the conventional rule for laying out indented text blocks:

* the first line is stripped of all of its leading whitespace;
* a single common indentation amount is determined as the smallest number of
  leading whitespace characters occurring on any non-blank line *among the lines
  that follow the first*; every line after the first then has exactly that many
  leading characters removed (lines after the first keep whatever indentation
  they have in excess of the common amount);
* if there is no non-blank line after the first, the lines after the first are
  left untouched;
* finally, completely empty lines are removed from the end of the block and then
  from the beginning of the block.

A blank line (a line whose characters are all whitespace) does not contribute to
the common indentation amount, but only a *completely empty* line (no characters
at all) is eligible for removal at the ends.

"Whitespace" here follows the ambient string library's notion of a whitespace
character (space, the various separators, no-break and other Unicode spaces),
not merely the ASCII space.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract. Splitting the text into
-- lines and rejoining them, and expanding tab stops, happen outside this routine
-- and are supplied/consumed at the boundary; the indentation-normalization logic
-- itself is spelled out concretely below.
-- axioms-end

-- pure-start
/-- The whitespace code points recognized by the ambient string library's
whitespace predicate (the same set its left-strip operation removes). Kept as an
explicit table so the model matches that predicate exactly rather than only the
ASCII space. -/
def whitespaceCodes : List Nat :=
  [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20,
   0x85, 0xa0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007,
   0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]

/-- Whether a character is whitespace under the ambient predicate. -/
def isSpaceChar (c : Char) : Bool := whitespaceCodes.contains c.toNat

/-- Number of leading whitespace characters on a line. -/
def leadingWs (l : List Char) : Nat := (l.takeWhile isSpaceChar).length

/-- A line with its leading whitespace removed. -/
def lstripWs (l : List Char) : List Char := l.dropWhile isSpaceChar

/-- A line is blank when it has no non-whitespace content. -/
def isBlank (l : List Char) : Bool := (lstripWs l).isEmpty

/-- The common indentation amount: the least leading-whitespace count over the
non-blank lines of `rest`, or `none` when `rest` has no non-blank line. -/
def marginSpec (rest : List (List Char)) : Option Nat :=
  rest.foldl (fun m line =>
    if isBlank line then m
    else some (match m with
               | none   => leadingWs line
               | some k => Nat.min k (leadingWs line))) none

/-- Strip the first line's leading whitespace and dedent every following line by
the common margin (or leave them untouched when there is no common margin). -/
def dedentSpec (margin : Option Nat) (lines : List (List Char)) : List (List Char) :=
  match lines with
  | []            => []
  | first :: rest =>
    lstripWs first :: (match margin with
                       | none   => rest
                       | some m => rest.map (·.drop m))

/-- Drop completely empty lines from the end of the block. -/
def dropTrailingEmpty (ls : List (List Char)) : List (List Char) :=
  (ls.reverse.dropWhile (· == ([] : List Char))).reverse

/-- Drop completely empty lines from the beginning of the block. -/
def dropLeadingEmpty (ls : List (List Char)) : List (List Char) :=
  ls.dropWhile (· == ([] : List Char))

/-- Functional reference for indentation normalization. -/
def normalizeIndentSpec (lines : List (List Char)) : List (List Char) :=
  dropLeadingEmpty (dropTrailingEmpty
    (dedentSpec (marginSpec (lines.drop 1)) lines))
-- pure-end

-- post-conditions-start
/-- Input→output relation for indentation normalization. `lines` is the block of
text already split into lines; `result` is the normalized block. The result is
exactly the normalized block produced by the rule above. -/
def problem_spec_normalizeIndent (lines : List (List Char))
    (result : List (List Char)) : Prop :=
  result = normalizeIndentSpec lines
-- post-conditions-end

-- impl-start
def implementation_normalizeIndent (lines : List (List Char)) :
    List (List Char) := Id.run do
  -- common indentation, measured over the lines after the first
  let mut margin : Option Nat := none
  for line in lines.drop 1 do
    if !isBlank line then
      let ind := leadingWs line
      margin := some (match margin with
                      | none   => ind
                      | some m => Nat.min m ind)
  -- strip the first line's leading whitespace; dedent each following line by the
  -- common margin
  let mut out : List (List Char) :=
    match lines with
    | []          => []
    | first :: _  => [lstripWs first]
  for line in lines.drop 1 do
    match margin with
    | none   => out := out ++ [line]
    | some m => out := out ++ [line.drop m]
  -- drop completely empty lines from the end, then from the beginning
  out := dropTrailingEmpty out
  out := dropLeadingEmpty out
  return out
-- impl-end

-- proof-start
-- @ns:fold_append_map-start
-- @decl:fold_append_map-start
theorem fold_append_map {α β : Type _} (g : α → β) (init : List β) (l : List α) :
    List.foldl (fun acc x => acc ++ [g x]) init l = init ++ l.map g := by
  induction l generalizing init with
  | nil => simp
  | cons a t ih => simp [List.foldl_cons, List.map_cons, ih, List.append_assoc]
-- @decl:fold_append_map-end
-- @ns:fold_append_map-end

-- @ns:margin_loop_eq-start
-- @decl:margin_loop_eq-start
theorem margin_loop_eq (rest : List (List Char)) :
    List.foldl
      (fun margin line =>
        if !isBlank line then
          some (match margin with
                | none   => leadingWs line
                | some m => Nat.min m (leadingWs line))
        else margin)
      none rest = marginSpec rest := by
  unfold marginSpec
  congr 1
  funext m line
  cases isBlank line <;> simp
-- @decl:margin_loop_eq-end
-- @ns:margin_loop_eq-end

-- @ns:dedent_loop_eq-start
-- @decl:dedent_loop_eq-start
theorem dedent_loop_eq (lines : List (List Char)) (margin : Option Nat) :
    (match lines with
     | []           => []
     | first :: _   => [lstripWs first]) ++
      List.foldl
        (fun out line =>
          match margin with
          | none   => out ++ [line]
          | some m => out ++ [line.drop m])
        [] (lines.drop 1) = dedentSpec margin lines := by
  cases lines with
  | nil => simp [dedentSpec]
  | cons first rest =>
    simp only [List.drop_succ_cons, List.drop_zero, dedentSpec]
    cases margin with
    | none =>
      show [lstripWs first] ++ List.foldl (fun out line => out ++ [id line]) [] rest = _
      rw [fold_append_map (g := id)]; simp
    | some m =>
      show [lstripWs first] ++ List.foldl (fun out line => out ++ [(fun l => List.drop m l) line]) [] rest = _
      rw [fold_append_map (g := fun l => List.drop m l)]; simp
-- @decl:dedent_loop_eq-end
-- @ns:dedent_loop_eq-end

-- @ns:impl_as_folds-start
-- @decl:impl_as_folds-start
theorem impl_as_folds (lines : List (List Char)) :
    implementation_normalizeIndent lines =
      dropLeadingEmpty (dropTrailingEmpty
        ((match lines with
          | []          => []
          | first :: _  => [lstripWs first]) ++
          List.foldl
            (fun out line =>
              match
                (List.foldl
                  (fun margin line =>
                    if !isBlank line then
                      some (match margin with
                            | none   => leadingWs line
                            | some m => Nat.min m (leadingWs line))
                    else margin)
                  none (lines.drop 1)) with
              | none   => out ++ [line]
              | some m => out ++ [line.drop m])
            [] (lines.drop 1))) := by
  unfold implementation_normalizeIndent
  simp only [Id.run, bind, pure]
  simp only [← apply_ite ForInStep.yield]
  rw [List.forIn_yield_eq_foldl]
  generalize List.foldl (fun b a =>
      if (!isBlank a) = true then
        some (match b with | none => leadingWs a | some m => m.min (leadingWs a))
      else b) none (lines.drop 1) = M
  cases M with
  | none =>
    simp only []
    rw [List.forIn_yield_eq_foldl]
    rw [fold_append_map (fun a => a), fold_append_map (fun a => a)]
    simp
  | some m =>
    simp only []
    rw [List.forIn_yield_eq_foldl]
    rw [fold_append_map (fun a : List Char => a.drop m),
        fold_append_map (fun a : List Char => a.drop m)]
    simp
-- @decl:impl_as_folds-end
-- @ns:impl_as_folds-end


theorem correct_normalizeIndent :
    ∀ (lines : List (List Char)),
      problem_spec_normalizeIndent lines
        (implementation_normalizeIndent lines) := by
  intro lines
  unfold problem_spec_normalizeIndent
  rw [impl_as_folds]
  simp only [margin_loop_eq]
  unfold normalizeIndentSpec
  congr 1
  congr 1
  rcases h : marginSpec (lines.drop 1) with _ | m
  · exact dedent_loop_eq lines none
  · exact dedent_loop_eq lines (some m)
-- proof-end
