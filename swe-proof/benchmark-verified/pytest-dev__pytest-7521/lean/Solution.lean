import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The operation under
-- specification — turning the raw character stream that was written into the
-- capture buffer back into the text handed to the caller — is modeled DEEPLY as
-- the single read pass below, rather than abstracted behind any callee. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The text read back out of a capture buffer must reproduce, character for
character, exactly the text that was written into it: nothing is dropped,
rewritten, merged, or inserted. The result is pinned entirely to the input
stream — the readback equals the written stream verbatim. -/
def problem_spec_readCaptured (written : List Char) (result : List Char) : Prop :=
  result = written
-- post-conditions-end

-- impl-start
/-- Read the buffered character stream back out. Each character that was written
is handed back unchanged, in order, with no transformation applied. -/
def implementation_readCaptured (written : List Char) : List Char := Id.run do
  let mut out : Array Char := #[]
  for c in written do
    out := out.push c
  return out.toList
-- impl-end

-- proof-start
/-- The cleaned `forIn` accumulation over the array, generalized over the
accumulator: writing each character in order appends `written` to the running
array. Proven by induction with `List.forIn_cons`. -/
theorem readCaptured_forIn_eq (written : List Char) (init : Array Char) :
    (forIn written init (fun c r =>
        (pure (ForInStep.yield (r.push c)) : Id (ForInStep (Array Char)))) : Id (Array Char))
    = pure (init ++ ⟨written⟩) := by
  induction written generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind, ih]
    apply congrArg
    apply Array.ext'
    simp

theorem correct_readCaptured :
    ∀ (written : List Char),
    problem_spec_readCaptured written (implementation_readCaptured written) := by
  intro written
  unfold problem_spec_readCaptured implementation_readCaptured
  simp only [Id.run, bind, readCaptured_forIn_eq written #[]]
  show ((#[] ++ ⟨written⟩ : Array Char)).toList = written
  simp
-- proof-end
