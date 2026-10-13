import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the mode-string
-- transformation is modeled DEEPLY (a per-character filter, below) rather than
-- axiomatized, so its standard-library reference is validated as an A-reference
-- by G-AX. The proof agent may add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Front-recursive specification fold over the underlying stream's mode string:
keep every character except the binary-indicator character `'b'`, in order. -/
def stripBinary : List Char → List Char
  | [] => []
  | c :: cs => if c = 'b' then stripBinary cs else c :: stripBinary cs
-- pure-end

-- post-conditions-start
/-- The reported text-stream mode is exactly the underlying stream's mode string
with every binary-indicator character `'b'` removed and every other character
preserved in its original order. -/
def problem_spec_mode (bufferMode : List Char) (result : List Char) : Prop :=
  result = stripBinary bufferMode
-- post-conditions-end

-- impl-start
def implementation_mode (bufferMode : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in bufferMode do
    if c ≠ 'b' then
      acc := acc ++ [c]
  return acc
-- impl-end

-- proof-start
/-- Helper: the cleaned `forIn` accumulation, generalized over the accumulator,
equals the initial accumulator appended with the front-recursive `stripBinary`. -/
theorem mode_forIn_helper (xs : List Char) (init : List Char) :
    Id.run (forIn xs init (fun c r =>
      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
      else do pure PUnit.unit; pure (ForInStep.yield r))) = init ++ stripBinary xs := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, Id.run, stripBinary, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    by_cases h : a = 'b'
    · simp only [h, ne_eq, not_true_eq_false, if_false]
      rw [ih]
      simp [stripBinary]
    · simp only [h, ne_eq, not_false_eq_true, if_true]
      rw [ih, List.append_assoc]
      simp [stripBinary, h]

theorem correct_mode : ∀ bufferMode : List Char,
    problem_spec_mode bufferMode (implementation_mode bufferMode) := by
  intro bufferMode
  unfold problem_spec_mode implementation_mode
  have h2 : (Id.run do
      let mut acc : List Char := []
      for c in bufferMode do
        if c ≠ 'b' then
          acc := acc ++ [c]
      return acc) = Id.run (forIn bufferMode ([] : List Char) (fun c r =>
      if c ≠ 'b' then do pure PUnit.unit; pure (ForInStep.yield (r ++ [c]))
      else do pure PUnit.unit; pure (ForInStep.yield r))) := rfl
  rw [h2, mode_forIn_helper]
  simp
-- proof-end
