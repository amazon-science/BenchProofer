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

def implementation_resolveIdent
    (name : List Char) (matcher : List Char → Bool) : Option Bool := Id.run do
  -- build the name node's identifier from the match-expression identifier
  let key := identPrefix ++ name
  -- compiling the name node aborts if its identifier is a reserved constant
  if isReservedConst key then
    return none
  -- consult the matcher with the identifier recovered from the name node
  return some (matcher (key.drop identPrefix.length))
-- impl-end

-- proof-start
theorem correct_resolveIdent : ∀ (name : List Char) (matcher : List Char → Bool),
    problem_spec_resolveIdent name matcher (implementation_resolveIdent name matcher) := by
  intro name matcher
  show implementation_resolveIdent name matcher = some (matcher name)
  unfold implementation_resolveIdent
  simp only [identPrefix, isReservedConst, List.cons_append, List.nil_append,
    List.length_cons, List.length_nil, List.drop_succ_cons, List.drop_zero, Id.run]
  rw [if_neg]
  · rfl
  · simp only [List.cons.injEq, Char.reduceEq, false_and, Bool.or_self, decide_false,
      Bool.false_eq_true, not_false_eq_true]
-- proof-end
