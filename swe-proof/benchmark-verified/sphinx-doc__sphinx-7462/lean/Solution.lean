import Mathlib
-- imports-end

/-!
Assembling the inline display of a parenthesised sequence (a tuple) from the
already-rendered displays of its individual elements.

Each element has already been rendered to a small list of display tokens. The
sequence display is formed by laying the element displays out in order,
separated by a comma-and-space token. A non-empty sequence therefore renders as
`e₀ , e₁ , … , eₙ` (the elements interleaved with the separator, with no
trailing separator). The empty sequence is a special case: it has no elements to
interleave, and must render as the literal opening and closing parentheses
`(` `)` so that an empty sequence still produces a visible, well-formed display.

A second view renders the same sequence as flat source text instead of display
tokens: the element texts joined by a comma-and-space, except that the empty
sequence renders as the two-character text `()`.
-/

-- axioms-start
-- The per-element renderer (which turns one element into its already-rendered
-- form) is an UNCHANGED collaborator. It is represented here by leaving the
-- elements themselves as arbitrary inputs (`elems`), universally quantified in
-- the correctness statements, so the contract holds for every possible
-- per-element rendering. No `opaque`/`axiom` callee contract is consumed; the
-- sequence-assembly rule that the specification pins is modeled DEEPLY below.
-- axioms-end

-- pure-start
/-- A single display token: either a punctuation token carrying its literal
text, or a textual/cross-reference token carrying its text. This is the abstract
carrier for the rendered display pieces. -/
inductive SigToken where
  | punct : String → SigToken
  | text  : String → SigToken
  deriving DecidableEq, Repr

/-- Assemble the display-token rendering of a sequence from the per-element
renderings `elems`. The empty sequence renders as the parenthesis pair; a
non-empty sequence lays the element renderings out in order, each followed by a
separator token, then drops the single trailing separator. -/
def assembleTupleSig (elems : List (List SigToken)) : List SigToken :=
  if elems.isEmpty then
    [SigToken.punct "(", SigToken.punct ")"]
  else
    ((elems.map (fun e => e ++ [SigToken.punct ", "])).flatten).dropLast

/-- Assemble the flat source-text rendering of a sequence from the per-element
texts `elems`. The empty sequence renders as `()`; a non-empty sequence joins
the element texts with a comma-and-space. -/
def assembleTupleText (elems : List String) : String :=
  if elems.isEmpty then "()" else String.intercalate ", " elems
-- pure-end

-- post-conditions-start
/-- The display-token rendering equals the interleaved, trailing-separator-free
layout of the element renderings, with the empty sequence rendered as `()`. -/
def problem_spec_renderTupleSig
    (elems : List (List SigToken)) (result : List SigToken) : Prop :=
  result = assembleTupleSig elems
-- post-conditions-end

-- impl-start
def implementation_renderTupleSig
    (elems : List (List SigToken)) : List SigToken := Id.run do
  if elems.isEmpty then
    return [SigToken.punct "(", SigToken.punct ")"]
  let mut result : List SigToken := []
  for elem in elems do
    result := result ++ elem
    result := result ++ [SigToken.punct ", "]
  return result.dropLast
-- impl-end

-- proof-start
/-- Loop body of `implementation_renderTupleSig`, generalized over the
accumulator: folding `r ↦ r ++ elem ++ [sep]` over the elements appends, in
order, each element followed by the separator. -/
theorem helper_renderTupleSig (sep : SigToken) :
    ∀ (elems : List (List SigToken)) (init : List SigToken),
      Id.run (forIn elems init (fun elem r =>
        (pure (ForInStep.yield (r ++ elem ++ [sep])) : Id _)))
      = init ++ (elems.map (fun e => e ++ [sep])).flatten := by
  intro elems
  induction elems with
  | nil => intro init; simp [Id.run, pure]
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_renderTupleSig :
    ∀ (elems : List (List SigToken)),
      problem_spec_renderTupleSig elems (implementation_renderTupleSig elems) := by
  intro elems
  unfold problem_spec_renderTupleSig implementation_renderTupleSig assembleTupleSig
  by_cases h : elems.isEmpty
  · simp [h, Id.run, pure]
  · simp only [h, Id.run]
    have hbridge :
        (do
          pure PUnit.unit
          let r ← forIn elems ([] : List SigToken) fun elem r => do
              pure PUnit.unit
              pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "]))
          pure r.dropLast : Id (List SigToken))
        = pure (Id.run (forIn elems ([] : List SigToken) fun elem r =>
            (pure (ForInStep.yield (r ++ elem ++ [SigToken.punct ", "])) : Id _))).dropLast := rfl
    rw [hbridge, helper_renderTupleSig]
    simp [pure]
-- proof-end

-- post-conditions-start
/-- The flat source-text rendering equals the comma-and-space join of the
element texts, with the empty sequence rendered as `()`. -/
def problem_spec_renderTupleText
    (elems : List String) (result : String) : Prop :=
  result = assembleTupleText elems
-- post-conditions-end

-- impl-start
def implementation_renderTupleText
    (elems : List String) : String := Id.run do
  if elems.isEmpty then
    return "()"
  return String.intercalate ", " elems
-- impl-end

-- proof-start
theorem correct_renderTupleText :
    ∀ (elems : List String),
      problem_spec_renderTupleText elems (implementation_renderTupleText elems) := by
  intro elems
  unfold problem_spec_renderTupleText implementation_renderTupleText assembleTupleText
  by_cases h : elems.isEmpty <;> simp [h, Id.run, pure, bind]
-- proof-end
