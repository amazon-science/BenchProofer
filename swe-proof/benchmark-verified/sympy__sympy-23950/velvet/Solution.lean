import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The conversion reads the assertion's own stored
--  components and returns one of them directly; there is no separate callee to
--  contract, so there are no module-level axioms.)
-- axioms-end

-- pure-start
/- A membership assertion: a boolean-valued expression stating that some element
   belongs to some collection. It carries exactly two components — the element
   being tested (`elem`) and the collection it is tested against (`container`).
   Both are modeled as opaque identifiers (`Nat`), since the conversion only
   needs to tell them apart and to hand one of them back unchanged. -/
structure MembershipAssertion where
  elem : Nat
  container : Nat
  deriving DecidableEq

/- The two outcomes the set-conversion of a membership assertion distinguishes:
   a successful conversion yielding a collection, or a refusal (the conversion is
   undefined / unavailable). The refusal arm exists so that a routine which
   declines to produce a collection is expressible against this same spec. -/
inductive ConversionErr where
  | unavailable
  deriving DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The set form of a membership assertion. A statement "this element belongs to
   this collection" describes, as a set, precisely that collection: the set the
   membership ranges over. So converting the assertion to its set form must
   SUCCEED and yield the assertion's collection component — its second component
   — handed back unchanged. The element component is NOT the answer: the result
   is the collection, never the element being tested. The assertion is read-only
   (not `mut`); the conversion reads its components and mutates nothing
   (directive 5). The element, the collection, and the result are modeled as
   `Nat` identifiers; the result is wrapped in `Except` to allow a refusal arm. -/
method asSet (a : MembershipAssertion) return (out : Except ConversionErr Nat)
  ensures out = Except.ok a.container
  do
    -- impl-start
    return Except.ok a.container
    -- impl-end

prove_correct asSet by
  loom_solve
