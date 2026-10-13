import Mathlib
-- imports-end

/-!
Determining the program name presented by a command-line utility.

A command-line utility is invoked with an argument vector whose first entry is
the path under which the program was launched. The utility presents a program
name to the user (for example, in the usage banner of its option parser). That
program name is defined to be:

* the final path component of the utility's own first argument, and
* a constant textual name (`python -m django`) in the special case where that
  final component is the module-execution entry point `__main__.py`.

The key property is that the presented program name is a function of the
utility's own argument vector alone. It does not depend on any ambient,
process-global argument vector: two invocations with the same utility argument
vector present the same program name regardless of the surrounding process
state.

Argument vectors are modeled as `List String` (one element per argument);
individual arguments are modeled as `String`. Path components are separated by
`'/'`, matching POSIX path semantics.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The two operations the behavior
-- relies on — extracting the final path component of a string and the constant
-- module-execution special case — are modeled deeply below (`basename` /
-- `computeProgName`), so there is no opaque callee signature and no consumed
-- `_prop` axiom. The deep model is validated against the real implementation by
-- the conformance check.
-- axioms-end

-- pure-start
/-- The final path component of a string: everything after the last `'/'`
separator (the whole string when there is no separator; the empty string when
the string ends in a separator). Models POSIX basename. -/
def basename (s : String) : String :=
  (s.split (· = '/')).reverse.headI

/-- The program name derived from a single argument (the utility's first
argument): the final path component, except that the module-execution entry
point maps to a constant textual name. -/
def computeProgName (arg0 : String) : String :=
  let b := basename arg0
  if b = "__main__.py" then "python -m django" else b
-- pure-end

-- post-conditions-start
/-- The presented program name is exactly the name derived from the utility's
own argument vector. The specification mentions only the utility's own argument
vector, and never the ambient one: this pins the result to be independent of any
ambient argument vector. -/
def problem_spec_progName (argv : List String) (result : String) : Prop :=
  result = computeProgName argv.headI
-- post-conditions-end

-- impl-start
def implementation_progName (argv : List String) (_ambient : List String) : String :=
  Id.run do
    -- Derive the program name from the utility's OWN argument vector, applying
    -- the module-execution special case. The ambient argument vector is not
    -- consulted.
    let mut progName := basename argv.headI
    if progName = "__main__.py" then
      progName := "python -m django"
    return progName
-- impl-end

-- proof-start
theorem correct_progName :
    ∀ (argv ambient : List String), argv ≠ [] →
      problem_spec_progName argv (implementation_progName argv ambient) := by
  intro argv ambient _
  unfold problem_spec_progName implementation_progName computeProgName
  by_cases h : basename argv.headI = "__main__.py" <;>
    simp only [Id.run, bind, pure, h, if_true, if_false]
-- proof-end
