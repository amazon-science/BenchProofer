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
-- Pre-patch skeleton: no transformation of the underlying stream's mode string —
-- the reported mode is the buffer's mode string verbatim (binary indicator kept).
def implementation_mode (bufferMode : List Char) : List Char := Id.run do
  let mut acc : List Char := []
  for c in bufferMode do
    acc := acc ++ [c]
  return acc
-- impl-end

-- proof-start
theorem correct_mode : ∀ bufferMode : List Char,
    problem_spec_mode bufferMode (implementation_mode bufferMode) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
