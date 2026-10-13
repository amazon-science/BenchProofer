import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two inputs are the
-- runtime version data (a numeric component tuple and the version display
-- string); the order comparison on the tuple and the message formatting are
-- modeled DEEPLY (below), not axiomatized. The proof agent may add `_prop`
-- axioms only if stuck.
-- axioms-end

-- pure-start
/-- Lexicographic strict order on component tuples, matching Python tuple `<`:
compare element-wise; a strict prefix is smaller than its extension; equal-length
equal tuples are not less than one another. -/
def versionLt : List Nat → List Nat → Bool
  | [],      [] => false
  | [],      _ :: _ => true
  | _ :: _,  [] => false
  | a :: as, b :: bs =>
      if a < b then true
      else if b < a then false
      else versionLt as bs

/-- The minimum supported version: components `3, 9, 0`. -/
def requiredMin : List Nat := [3, 9, 0]

/-- The configuration-error message reported for an unsupported runtime: a
constant prefix naming the minimum supported version, the actual version display
string substituted in, and a closing parenthesis and period. -/
def errorMessage (versionStr : List Char) : List Char :=
  "SQLite 3.9.0 or later is required (found ".toList ++ versionStr ++ ").".toList
-- pure-end

-- post-conditions-start
/-- A runtime whose version components are strictly below the minimum supported
version is rejected with the configuration-error message carrying its version
string; any other runtime is accepted. Both branches are pinned. -/
def problem_spec_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char)
    (result : Except (List Char) Unit) : Prop :=
  if versionLt versionInfo requiredMin then
    result = Except.error (errorMessage versionStr)
  else
    result = Except.ok ()
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy) skeleton: the accepted-version threshold sits one minor
release too low (components `3, 8, 3`) and the reported message names that lower
minimum, so a runtime at components `3, 8, 11, 1` is wrongly accepted. -/
def requiredMinBug : List Nat := [3, 8, 3]

def errorMessageBug (versionStr : List Char) : List Char :=
  "SQLite 3.8.3 or later is required (found ".toList ++ versionStr ++ ").".toList

def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :
    Except (List Char) Unit := Id.run do
  if versionLt versionInfo requiredMinBug then
    return Except.error (errorMessageBug versionStr)
  return Except.ok ()
-- impl-end

-- proof-start
theorem correct_ensureSupportedVersion : ∀ (versionInfo : List Nat) (versionStr : List Char),
    problem_spec_ensureSupportedVersion versionInfo versionStr
      (implementation_ensureSupportedVersion versionInfo versionStr) := by
  intro versionInfo versionStr
  unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion
  -- carries the gold proof shape; UNCLOSABLE against the buggy impl (G-DIFF):
  -- the threshold/message disagree on the (3, 8, 11, 1) runtime.
  simp [requiredMin, requiredMinBug, errorMessage, errorMessageBug]
-- proof-end
