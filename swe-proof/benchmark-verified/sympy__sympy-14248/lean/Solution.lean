import Mathlib
-- imports-end

/-!
Rendering an additive expression — a sequence of already-formatted summand
strings — into a single displayed sum.

Each summand has already been rendered to text. When that text carries a leading
minus sign, the summand is a negative quantity and must be joined into the sum as
a *subtraction* rather than as the addition of an explicitly-negated term. The
desired behaviour is:

* the summands appear left to right in their input order;
* a summand whose rendered text begins with `-` contributes its remaining text
  preceded by a subtraction connective; any other summand contributes its text
  preceded by an addition connective;
* the very first summand has no leading addition connective — if it is positive
  it stands alone, and if it is negative it keeps its leading minus and stands
  alone;
* connectives between summands are surrounded by single spaces.

So a leading-minus summand turns into a genuine subtraction in the joined output
instead of being shown as the addition of a negated term.
-/

-- axioms-start
-- The modeled routine is a self-contained transform over a list of already
-- rendered summand strings: it consumes no unchanged repo callee, so there is no
-- `opaque` declaration and no consumed `axiom … _prop`. (The per-summand renderer
-- that PRODUCES these strings is upstream of this routine and out of scope.)
-- axioms-end

-- pure-start
/-- The signed, split pieces of the summand list, in order: for each summand,
two entries — a connective (`"-"` for a leading-minus summand, `"+"` otherwise)
followed by the summand's body (its text with a leading minus removed when
present). Front-of-list accumulation by an append fold, matching the imperative
build of the working list. -/
def signParts (terms : List String) : List String :=
  terms.foldl
    (fun acc t =>
      if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
    []

/-- The displayed sum: drop the very first connective (a leading `"+"` becomes
nothing, a leading `"-"` is kept and glued directly to the first body), then join
the remaining connectives and bodies with single spaces. -/
def renderSum (terms : List String) : String :=
  let l := signParts terms
  let firstSign := l.headD "+"
  (if firstSign = "+" then "" else firstSign) ++ String.intercalate " " l.tail
-- pure-end

-- post-conditions-start
/-- The rendered output is exactly the displayed sum of the summand texts: each
leading-minus summand contributes as a subtraction, every other summand as an
addition, in input order, with the first connective elided. -/
def problem_spec_renderSum (terms : List String) (result : String) : Prop :=
  result = renderSum terms
-- post-conditions-end

-- impl-start
def implementation_renderSum (terms : List String) : String := Id.run do
  let mut l : List String := []
  for t in terms do
    if t.startsWith "-" then
      l := l ++ ["-", t.drop 1]
    else
      l := l ++ ["+", t]
  let firstSign := l.headD "+"
  let rest := l.tail
  let firstSign := if firstSign = "+" then "" else firstSign
  return firstSign ++ String.intercalate " " rest
-- impl-end

-- proof-start
/-- The cleaned `forIn` loop (generalized over the accumulator) collapses to the
`signParts` append fold. Route B helper. -/
theorem loop_helper_renderSum (terms : List String) (init : List String) :
    (Id.run (forIn terms init (fun t r =>
        if t.startsWith "-" = true then
          (pure (ForInStep.yield (r ++ ["-", t.drop 1])) : Id _)
        else
          pure (ForInStep.yield (r ++ ["+", t])))))
    = terms.foldl
        (fun acc t => if t.startsWith "-" then acc ++ ["-", t.drop 1] else acc ++ ["+", t])
        init := by
  induction terms generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a.startsWith "-" = true <;>
      simp only [h, List.foldl_cons, if_true, if_false, ih, reduceCtorEq]

theorem correct_renderSum :
    ∀ (terms : List String),
      problem_spec_renderSum terms (implementation_renderSum terms) := by
  intro terms
  unfold problem_spec_renderSum implementation_renderSum renderSum
  have key : (forIn terms ([] : List String) (fun t r =>
      if t.startsWith "-" = true then do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["-", t.drop 1]))
      else do
        pure PUnit.unit
        pure (ForInStep.yield (r ++ ["+", t]))) : Id (List String))
      = signParts terms := loop_helper_renderSum terms []
  simp only [Id.run]
  rw [key]
  rfl
-- proof-end
