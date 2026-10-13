import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The only thing this bundle pins is the eligibility test
   that decides whether two query operands may be logically combined; it is
   modeled DEEPLY in the `pure` region, not behind an axiom. The actual
   combination of two eligible operands is UNCHANGED by the desired behaviour and
   is modeled as an arbitrary value supplied to the operation (a free input), so
   the postcondition holds for EVERY such combination result — strictly weaker
   than any concrete combiner, hence no contract is owed (directive 7). There is
   no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The only outcome the desired behaviour distinguishes for the combination of
   two query operands: a rejection raised when the right operand is not something
   that may participate in a logical combination of conditions. -/
inductive CombineErr where
  | notCombinable
  deriving DecidableEq

/- The observable result of a successful logical combination of two operands.
   Its internal shape is produced by machinery the desired behaviour does NOT
   change, so only an opaque carrier of that result is modeled here (mapping.md
   §2); the combination itself is supplied as a free input to the operation. -/
structure CombinedNode where
  payload : List Int
  deriving DecidableEq

/- The right-hand operand of a logical combination, reduced to the only two
   observables the admissibility test consults: whether the operand is itself a
   filter-condition container, and whether it advertises that it denotes a
   boolean condition usable as a filter. -/
structure Operand where
  isFilterNode : Bool
  isCondition : Bool
  deriving DecidableEq

/- The desired outcome of logically combining a filter condition with a
   right-hand `other` operand, given the (unchanged) combination result
   `combined` the operation would produce when the operands ARE eligible.

   Eligibility — the behaviour this bundle pins — is: the right operand may be
   combined exactly when it is itself a filter-condition container OR it
   advertises that it denotes a boolean condition usable as a filter. When
   eligible the operation yields the (unchanged) combination `combined`; when
   not, it is rejected as not combinable. -/
def combineResult (other : Operand) (combined : CombinedNode) :
    Except CombineErr CombinedNode :=
  if other.isFilterNode || other.isCondition then Except.ok combined
  else Except.error .notCombinable
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Logically combine a filter condition with a right-hand `other` operand under
   a connector. Desired behaviour: the combination must be accepted not only when
   `other` is itself a filter-condition container but ALSO when `other` merely
   advertises that it denotes a boolean condition usable as a filter; only an
   operand that is neither is rejected as not combinable. On an accepted
   combination the operation produces the result `combined` it would otherwise
   build from the two operands (unchanged here — modeled as a free input,
   mapping.md §1/§2). -/
method combineConditions (other : Operand) (combined : CombinedNode)
    return (out : Except CombineErr CombinedNode)
  ensures out = combineResult other combined
  do
    -- impl-start
    -- Pre-image skeleton: accept the combination ONLY when `other` is itself a
    -- filter-condition container, rejecting every other operand — including one
    -- that merely advertises a boolean condition usable as a filter. The frozen
    -- spec requires accepting that case too, so prove_correct MUST not succeed.
    let result : Except CombineErr CombinedNode :=
      if other.isFilterNode then Except.ok combined
      else Except.error .notCombinable
    return result
    -- impl-end

prove_correct combineConditions by
  loom_solve
  simp [combineResult]
