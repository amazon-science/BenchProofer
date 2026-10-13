import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- An object's runtime class, abstracted to an identity tag. The behaviour under
   spec turns on WHICH class a freshly constructed result object carries, so the
   class is a first-class observable with decidable equality. Distinct classes
   carry distinct tags; the only relation the spec relies on is equality. -/
abbrev ClassTag := Nat

/- The value-level contents the construction operations produce. None of these
   value computations is affected by the behaviour under change (only the class
   of the wrapper that holds the contents is), so each is modeled opaquely: its
   concrete result is never pinned, only that the SAME map is applied on both
   sides. Each is a settled map of the relevant operand contents / parameters. -/
opaque composeContents : List Nat → List Nat → List Nat
opaque powerContents : List Nat → Int → List Nat
opaque reverseContents : List Nat → List Nat
opaque conjugateContents : List Nat → List Nat → List Nat
opaque stepContents : List Nat → List Nat
opaque divideContents : List Nat → List Nat → List Nat
opaque bracketContents : List Nat → List Nat → List Nat
opaque stepAltContents : List Nat → List Nat
opaque foldContents : List (List Nat) → List Nat
opaque fromUnitContents : List Nat → List Nat → List Nat
opaque extentContents : Nat → List Nat
opaque generatedContents : Nat → Nat → List Nat
opaque rankedContents : Nat → Nat → List Nat
opaque rankedAltContents : Nat → Nat → List Nat
opaque rankedThirdContents : Nat → Nat → List Nat
opaque fromVectorContents : List Nat → List Nat
opaque scheduleContents : Nat → Nat → Nat → List Nat

/- The two successor orders above are DIFFERENT orderings of the same operands,
   so `stepContents` and `stepAltContents` are different maps: nothing relates
   the two, and an operand's successor under one order is not its successor under
   the other.

   Each successor order also RUNS OUT. An operand that is last in that order has
   no successor at all, and the corresponding operation then produces no object
   whatsoever - not an object carrying some other contents. Which operands are
   last differs between the two orders and is never pinned here; each decision is
   a settled predicate of the operand contents, modeled opaquely and asked
   separately per order. -/
opaque stepDefined : List Nat → Bool
opaque stepAltDefined : List Nat → Bool

/- Three of the operations below REFUSE some of their inputs outright: they
   produce no object at all for them, rather than producing one carrying some
   substitute contents.

   Two of them refuse a PAIR whose extents differ - they are defined only between
   operands of the same extent. That decision is not one of the opaque maps: it is
   a concrete, decidable function of the two operands' contents. -/
def sameExtent (a b : List Nat) : Bool := a.length == b.length

/- The third refuses an ill-formed offset vector: only a vector whose successive
   entries stay within the shrinking pool of remaining positions describes an
   object at all. Which vectors those are is a settled predicate of the vector,
   modeled opaquely and never pinned here. -/
opaque vectorValid : List Nat → Bool

/- Three FURTHER operations refuse part of their input, for a different reason
   than the extent test above: each computes its value by indexing one operand
   through another, and that indexing is defined only where the operands fit
   together. Where they do not, no object is produced at all - not one carrying
   substitute contents.

   The left-divide indexes the left operand's inverse at the RIGHT operand's
   entries, so it is defined exactly when the right operand fits within the left.
   That decision is a concrete, decidable comparison of the two extents, and -
   unlike the pair test above - it is ASYMMETRIC: the right operand may be
   shorter than the left, never longer. -/
def fitsWithin (inner : List Nat) (outer : List Nat) : Bool :=
  inner.length ≤ outer.length

/- The remaining two refuse sub-domains that are NOT a comparison of extents.

   The fold composes its whole sequence pairwise, so it is undefined on the EMPTY
   sequence (there is nothing to compose) and on any sequence whose successive
   operands do not compose; the shape of that condition follows the fold's own
   pairwise structure and is not a plain length ordering.

   The third index variant walks its construction off the end for an index outside
   its range - and that range is NOT the plain count of arrangements of the extent,
   because this variant, alone among the three, does not reduce its index first.

   Each decision is a settled predicate of that site's own parameters, modeled
   opaquely and never pinned here: the spec pins WHERE nothing is constructed
   without pinning WHICH parameters those are. -/
opaque foldDefined : List (List Nat) → Bool
opaque rankedThirdDefined : Nat → Nat → Bool

/- An object carrying ordered contents together with its runtime class tag.
   Only the two fields the behaviour observes are modeled. -/
structure Obj where
  contents : List Nat
  classId : ClassTag
  deriving Inhabited, DecidableEq
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- THE SHARED CONSTRUCTION PRIMITIVE.

   Every construction operation below builds its fresh result by invoking THIS
   one primitive, passing the class it is dispatched on. The primitive's sole
   behaviour-under-change is its first observation: the produced object is an
   instance of the class it was dispatched on (`builtOn`) — never silently
   coerced to a single predetermined base class. Its contents are exactly the
   value handed to it. Both arguments are read-only.

   Because every construction site flows through this primitive AND each site
   below must pass ITS OWN dispatch class, the whole family of operations is
   pinned together: an operation that fails to thread its dispatch class into
   the primitive cannot satisfy its own postcondition. -/
method buildVia (builtOn : ClassTag) (value : List Nat) return (out : Obj)
  ensures out.classId = builtOn
  ensures out.contents = value
  do
    -- impl-start
    return { contents := value, classId := builtOn }
    -- impl-end

/- Binary product of a left operand with a right operand. The result is built
   via the shared primitive dispatched on the LEFT operand's class, so it is an
   instance of the left operand's (possibly derived) class. Contents are the
   unchanged composition of both operands' contents, in operand order. -/
method composeProduct (self : Obj) (other : Obj) return (out : Obj)
  ensures out.classId = self.classId
  ensures out.contents = composeContents self.contents other.contents
  do
    -- impl-start
    let r ← buildVia self.classId (composeContents self.contents other.contents)
    return r
    -- impl-end

/- Raising an operand to an integer exponent. Built via the shared primitive
   dispatched on the operand's class. Contents are the unchanged power map. -/
method powerSelf (self : Obj) (n : Int) return (out : Obj)
  ensures out.classId = self.classId
  ensures out.contents = powerContents self.contents n
  do
    -- impl-start
    let r ← buildVia self.classId (powerContents self.contents n)
    return r
    -- impl-end

/- Inverting an operand. Built via the shared primitive dispatched on the
   operand's class. Contents are the unchanged inverse map. -/
method reverseSelf (self : Obj) return (out : Obj)
  ensures out.classId = self.classId
  ensures out.contents = reverseContents self.contents
  do
    -- impl-start
    let r ← buildVia self.classId (reverseContents self.contents)
    return r
    -- impl-end

/- Conjugation of an operand by another operand - a REFUSING operation. The two
   operands must be of the same extent; a pair of differing extents is refused
   and NO object is produced for it. On an accepted pair the result is built via
   the shared primitive dispatched on the (left) operand's class, so it is an
   instance of that operand's (possibly derived) class. -/
method conjugateSelf (self : Obj) (other : Obj) return (out : Option Obj)
  ensures sameExtent self.contents other.contents = true →
    out.map (·.classId) = some self.classId
  ensures sameExtent self.contents other.contents = true →
    out.map (·.contents) = some (conjugateContents self.contents other.contents)
  ensures sameExtent self.contents other.contents = false → out = none
  do
    -- impl-start
    if sameExtent self.contents other.contents then
      let r ← buildVia self.classId (conjugateContents self.contents other.contents)
      return some r
    else
      return none
    -- impl-end

/- The lexical-successor of an operand - a PARTIAL operation. When the operand
   has a successor in that order, the result is built via the shared primitive
   dispatched on the operand's class, so it is an instance of the operand's
   (possibly derived) class, and carries the successor contents. When the operand
   is last in that order there is no successor and no object is produced. -/
method stepSelf (self : Obj) return (out : Option Obj)
  ensures stepDefined self.contents = true → out.map (·.classId) = some self.classId
  ensures stepDefined self.contents = true →
    out.map (·.contents) = some (stepContents self.contents)
  ensures stepDefined self.contents = false → out = none
  do
    -- impl-start
    if stepDefined self.contents then
      let r ← buildVia self.classId (stepContents self.contents)
      return some r
    else
      return none
    -- impl-end

/- A left-divide of an operand by another - a REFUSING operation on an
   ASYMMETRIC test: its value indexes the left operand's inverse at the right
   operand's entries, so a right operand that does not fit within the left is
   refused and NO object is produced for it. On an accepted pair the result is
   built via the shared primitive dispatched on the (left) operand's class. -/
method divideSelf (self : Obj) (other : Obj) return (out : Option Obj)
  ensures fitsWithin other.contents self.contents = true →
    out.map (·.classId) = some self.classId
  ensures fitsWithin other.contents self.contents = true →
    out.map (·.contents) = some (divideContents self.contents other.contents)
  ensures fitsWithin other.contents self.contents = false → out = none
  do
    -- impl-start
    if fitsWithin other.contents self.contents then
      let r ← buildVia self.classId (divideContents self.contents other.contents)
      return some r
    else
      return none
    -- impl-end

/- A second binary combination of an operand with another - also REFUSING, on
   the same extent test: a pair of differing extents produces no object at all.
   On an accepted pair the result is built via the shared primitive dispatched on
   the (left) operand's class. -/
method bracketSelf (self : Obj) (other : Obj) return (out : Option Obj)
  ensures sameExtent self.contents other.contents = true →
    out.map (·.classId) = some self.classId
  ensures sameExtent self.contents other.contents = true →
    out.map (·.contents) = some (bracketContents self.contents other.contents)
  ensures sameExtent self.contents other.contents = false → out = none
  do
    -- impl-start
    if sameExtent self.contents other.contents then
      let r ← buildVia self.classId (bracketContents self.contents other.contents)
      return some r
    else
      return none
    -- impl-end

/- The successor of an operand under the ALTERNATIVE order - a second, PARTIAL
   operation, over its OWN successor map: the alternative order enumerates the
   operands differently, so this operand's successor here is unrelated to its
   lexical one. When it exists, the result is built via the shared primitive
   dispatched on the operand's class, so it is an instance of the operand's
   (possibly derived) class. When the operand is last in the alternative order
   there is no successor and no object is produced. -/
method stepAltSelf (self : Obj) return (out : Option Obj)
  ensures stepAltDefined self.contents = true → out.map (·.classId) = some self.classId
  ensures stepAltDefined self.contents = true →
    out.map (·.contents) = some (stepAltContents self.contents)
  ensures stepAltDefined self.contents = false → out = none
  do
    -- impl-start
    if stepAltDefined self.contents then
      let r ← buildVia self.classId (stepAltContents self.contents)
      return some r
    else
      return none
    -- impl-end

/- A fold over a sequence of operands - a REFUSING operation: it composes the
   sequence pairwise, so a sequence it cannot compose (the empty one among them)
   is refused and NO object is produced for it. On an accepted sequence the result
   is built via the shared primitive dispatched on the target class `cls`. -/
method foldOver (cls : ClassTag) (items : List (List Nat)) return (out : Option Obj)
  ensures foldDefined items = true → out.map (·.classId) = some cls
  ensures foldDefined items = true → out.map (·.contents) = some (foldContents items)
  ensures foldDefined items = false → out = none
  do
    -- impl-start
    if foldDefined items then
      let r ← buildVia cls (foldContents items)
      return some r
    else
      return none
    -- impl-end

/- Coerce-and-rebuild a raw operand into an object of the target class `cls`, by
   delegating to the extent-parameterized construction below. The result is an
   instance of `cls`. -/
method fromUnit (cls : ClassTag) (a : List Nat) (b : List Nat) return (out : Obj)
  ensures out.classId = cls
  ensures out.contents = fromUnitContents a b
  do
    -- impl-start
    let r ← buildVia cls (fromUnitContents a b)
    return r
    -- impl-end

/- An extent-parameterized construction on the target class `cls`. The result is an
   instance of `cls` — invoked on a derived class it returns a derived instance,
   never a single predetermined base class. -/
method extentFor (cls : ClassTag) (extent : Nat) return (out : Obj)
  ensures out.classId = cls
  ensures out.contents = extentContents extent
  do
    -- impl-start
    let r ← buildVia cls (extentContents extent)
    return r
    -- impl-end

/- A generating construction on the target class `cls` of a given extent. The
   value it generates is drawn from the ambient generator state, so it is a value
   of BOTH the extent and that state: two constructions of the same extent taken
   at different generator states need not carry the same contents, and an
   operation that ignored the state would not be this one. The generated value
   itself is opaque; the discriminating observable is the result's class, which is
   exactly `cls`. -/
method generateFor (cls : ClassTag) (n : Nat) (entropy : Nat) return (out : Obj)
  ensures out.classId = cls
  ensures out.contents = generatedContents n entropy
  do
    -- impl-start
    let r ← buildVia 0 (generatedContents n entropy)
    return r
    -- impl-end

/- A construction-by-index on the target class `cls`. The result is an instance
   of `cls`. -/
method rankedFor (cls : ClassTag) (extent : Nat) (rank : Nat) return (out : Obj)
  ensures out.classId = cls
  ensures out.contents = rankedContents extent rank
  do
    -- impl-start
    let r ← buildVia cls (rankedContents extent rank)
    return r
    -- impl-end

/- A second construction-by-index variant on the target class `cls`. -/
method rankedAltFor (cls : ClassTag) (n : Nat) (r : Nat) return (out : Obj)
  ensures out.classId = cls
  ensures out.contents = rankedAltContents n r
  do
    -- impl-start
    let r2 ← buildVia cls (rankedAltContents n r)
    return r2
    -- impl-end

/- A third construction-by-index variant on the target class `cls` - a REFUSING
   operation, and the one index variant that is: it does not reduce its index into
   range first, so an out-of-range index describes no object and none is produced
   for it. On an accepted index the result is built via the shared primitive
   dispatched on `cls`. -/
method rankedThirdFor (cls : ClassTag) (extent : Nat) (rank : Nat) return (out : Option Obj)
  ensures rankedThirdDefined extent rank = true → out.map (·.classId) = some cls
  ensures rankedThirdDefined extent rank = true →
    out.map (·.contents) = some (rankedThirdContents extent rank)
  ensures rankedThirdDefined extent rank = false → out = none
  do
    -- impl-start
    if rankedThirdDefined extent rank then
      let r ← buildVia cls (rankedThirdContents extent rank)
      return some r
    else
      return none
    -- impl-end

/- A construction from a per-position offset vector on the target class `cls` -
   the third REFUSING operation: an ill-formed vector describes no object, and
   none is produced for it. On a well-formed vector the result is built via the
   shared primitive dispatched on `cls`. -/
method fromVectorFor (cls : ClassTag) (vec : List Nat) return (out : Option Obj)
  ensures vectorValid vec = true → out.map (·.classId) = some cls
  ensures vectorValid vec = true → out.map (·.contents) = some (fromVectorContents vec)
  ensures vectorValid vec = false → out = none
  do
    -- impl-start
    if vectorValid vec then
      let r ← buildVia cls (fromVectorContents vec)
      return some r
    else
      return none
    -- impl-end

/- A scheduling construction on the target class `cls` from three numeric
   parameters. The result is an instance of `cls`. -/
method scheduleFor (cls : ClassTag) (m : Nat) (n : Nat) (s : Nat) return (out : Obj)
  ensures out.classId = cls
  ensures out.contents = scheduleContents m n s
  do
    -- impl-start
    let r ← buildVia cls (scheduleContents m n s)
    return r
    -- impl-end

prove_correct buildVia by loom_solve
prove_correct composeProduct by loom_solve
prove_correct powerSelf by loom_solve
prove_correct reverseSelf by loom_solve
prove_correct conjugateSelf by loom_solve
prove_correct stepSelf by loom_solve
prove_correct divideSelf by loom_solve
prove_correct bracketSelf by loom_solve
prove_correct stepAltSelf by loom_solve
prove_correct foldOver by loom_solve
prove_correct fromUnit by loom_solve
prove_correct extentFor by loom_solve
prove_correct generateFor by loom_solve
prove_correct rankedFor by loom_solve
prove_correct rankedAltFor by loom_solve
prove_correct rankedThirdFor by loom_solve
prove_correct fromVectorFor by loom_solve
prove_correct scheduleFor by loom_solve
