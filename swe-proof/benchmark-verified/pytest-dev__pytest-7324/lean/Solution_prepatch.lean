import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature. The compilation guard that
-- rejects an identifier colliding with a reserved boolean/none constant is a
-- small, fully-known finite set, so it is modeled DEEPLY (an A-reference,
-- validated by G-AX against the real compiler) rather than axiomatized. The
-- proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
-- No spec-visible helper is required: the contract is stated directly as an
-- input→output relation over the identifier and the matcher.
-- pure-end

-- post-conditions-start
/-- Resolving a single match-expression identifier against a matcher always
succeeds and yields exactly the matcher's verdict on that identifier. The
identifier is consulted verbatim (the matcher sees the original identifier, not
some transformed form), and resolution never aborts — the result is always a
genuine boolean verdict (`some _`), for every identifier and every matcher. -/
def problem_spec_resolveIdent
    (name : List Char) (matcher : List Char → Bool) (result : Option Bool) : Prop :=
  result = some (matcher name)
-- post-conditions-end

-- impl-start
-- identPrefix: the prefix attached to an identifier when it is turned into a
-- name node, so the name node can never collide with a reserved constant.
def identPrefix : List Char := ['$']

-- isReservedConst: the compiler rejects a name node whose identifier is one of
-- the reserved boolean/none constants; modeled deeply as the exact finite set.
def isReservedConst (id : List Char) : Bool :=
  id = ['T', 'r', 'u', 'e'] || id = ['F', 'a', 'l', 's', 'e'] || id = ['N', 'o', 'n', 'e']

-- Pre-patch skeleton: the identifier is used verbatim as the name node's
-- identifier (no prefix attached, none stripped on lookup). When the identifier
-- is a reserved constant the name node fails to compile and resolution aborts.
def implementation_resolveIdent
    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
  let key := name
  if isReservedConst key then
    return none
  return some (matcher key)
-- impl-end

-- proof-start
theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
    problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
