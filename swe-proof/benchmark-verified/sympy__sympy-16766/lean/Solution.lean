import Mathlib
-- imports-end

/-!
Rendering an array element access as a line of Python source code.

An indexed access is written by a code printer as the array's name followed by
its subscripts in square brackets, the subscripts separated by `", "` — e.g. a
base named `p` accessed at subscripts `0, 1` is rendered `p[0, 1]`. The name and
each already-rendered subscript are supplied as inputs (each subscript is the
string a printer produces for that index expression).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the rendered base name
-- and the rendered subscripts are supplied as inputs (the outputs of the
-- ambient recursive printer), and the formatting is spelled out concretely.
-- axioms-end

-- pure-start
-- (No shared pure helpers are required.)
-- pure-end

-- post-conditions-start
/-- The rendered indexed access is the base name, then the subscript strings
joined by `", "` enclosed in a single pair of square brackets. Every component
of the result is pinned to the inputs: the prefix is exactly `base`, the bracket
content is exactly the comma-joined subscripts, and the brackets are literal. -/
def problem_spec_indexedCode (base : String) (subscripts : List String)
    (result : String) : Prop :=
  result = base ++ "[" ++ String.intercalate ", " subscripts ++ "]"
-- post-conditions-end

-- impl-start
def implementation_indexedCode (base : String) (subscripts : List String) :
    String := Id.run do
  let joined := String.intercalate ", " subscripts
  return base ++ "[" ++ joined ++ "]"
-- impl-end

-- proof-start
theorem correct_indexedCode :
    ∀ (base : String) (subscripts : List String),
      problem_spec_indexedCode base subscripts
        (implementation_indexedCode base subscripts) := by
  intro base subscripts
  unfold problem_spec_indexedCode implementation_indexedCode
  rfl
-- proof-end
