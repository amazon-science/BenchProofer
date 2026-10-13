import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- The three-valued status table for a single numeric quantity. Each field is a
   fuzzy fact about the quantity: `some true` (the property is known to hold),
   `some false` (it is known not to hold), or `none` (undetermined). Only the
   properties the two witnessed deductions touch are carried.

   `finite` is the boundedness fact: a quantity is `finite` when its absolute
   value is bounded. The behaviour under specification is that membership in the
   "small" number sets (rational / algebraic / irrational / transcendental)
   forces boundedness. -/
structure KB where
  integer : Option Bool
  rational : Option Bool
  real : Option Bool
  finite : Option Bool
  even : Option Bool
  odd : Option Bool
  algebraic : Option Bool
  transcendental : Option Bool
  irrational : Option Bool
  infinite : Option Bool
  complex : Option Bool
  noninteger : Option Bool
  prime : Option Bool
  composite : Option Bool
  deriving Inhabited, Repr, DecidableEq

-- axioms-start
-- (No opaque callee is consumed. The containment theory below is the behaviour
--  under specification itself; it is spelled out deeply as `consistentTheory`
--  and validated against the real property-deduction engine out of band by
--  conformance_check.py, not relied on as an axiom.)
-- axioms-end

-- pure-start
/- A fact table is CLOSED under the intended set-containment relations between
   the number classes. Each `A is true ⇒ B is true` clause is a containment;
   each `A is false ⇒ B is false` clause is its contrapositive. The
   boundedness-forcing containments are the behaviour under specification:

     * a rational quantity is real, is algebraic, AND is bounded;
     * a real quantity is complex;
     * an algebraic quantity is complex AND is bounded;
     * an irrational quantity is real, is not rational, AND is bounded;
     * a transcendental quantity is complex, is not algebraic, AND is bounded;
     * an integer is rational; an even or odd quantity is an integer; a prime or
       composite quantity is an integer; an even quantity is not odd;
     * an unbounded quantity is not bounded; a real quantity that is not an
       integer is a non-integer, and an integer is not a non-integer.

   Closure is two-directional: each containment also propagates its
   contrapositive, so a quantity known NOT to be bounded is thereby known NOT to
   be rational / algebraic / irrational / transcendental, hence not an integer,
   hence not even / odd / prime / composite. -/
def consistentTheory (k : KB) : Prop :=
  -- integer → rational ; ¬rational → ¬integer
  (k.integer = some true → k.rational = some true)
  ∧ (k.rational = some false → k.integer = some false)
  -- rational → real ; rational → algebraic ; rational → finite
  ∧ (k.rational = some true → k.real = some true)
  ∧ (k.rational = some true → k.algebraic = some true)
  ∧ (k.rational = some true → k.finite = some true)
  -- real → complex
  ∧ (k.real = some true → k.complex = some true)
  -- algebraic → complex ; algebraic → finite
  ∧ (k.algebraic = some true → k.complex = some true)
  ∧ (k.algebraic = some true → k.finite = some true)
  -- even → integer ; odd → integer ; ¬integer → ¬even ; ¬integer → ¬odd
  ∧ (k.even = some true → k.integer = some true)
  ∧ (k.odd = some true → k.integer = some true)
  ∧ (k.integer = some false → k.even = some false)
  ∧ (k.integer = some false → k.odd = some false)
  -- even ⇒ not odd (the ¬odd direction of even ≡ integer ∧ ¬odd)
  ∧ (k.even = some true → k.odd = some false)
  -- prime → integer ; composite → integer ; ¬integer → ¬prime, ¬composite
  ∧ (k.prime = some true → k.integer = some true)
  ∧ (k.composite = some true → k.integer = some true)
  ∧ (k.integer = some false → k.prime = some false)
  ∧ (k.integer = some false → k.composite = some false)
  -- irrational → real ; irrational → ¬rational ; irrational → finite
  ∧ (k.irrational = some true → k.real = some true)
  ∧ (k.irrational = some true → k.rational = some false)
  ∧ (k.irrational = some true → k.finite = some true)
  -- transcendental → complex ; → ¬algebraic ; → finite
  ∧ (k.transcendental = some true → k.complex = some true)
  ∧ (k.transcendental = some true → k.algebraic = some false)
  ∧ (k.transcendental = some true → k.finite = some true)
  -- infinite → ¬finite
  ∧ (k.infinite = some true → k.finite = some false)
  -- contrapositives of the four boundedness-forcing containments
  ∧ (k.finite = some false → k.rational = some false)
  ∧ (k.finite = some false → k.algebraic = some false)
  ∧ (k.finite = some false → k.irrational = some false)
  ∧ (k.finite = some false → k.transcendental = some false)
  -- a real non-integer is a non-integer ; an integer is not a non-integer
  ∧ (k.real = some true ∧ k.integer = some false → k.noninteger = some true)
  ∧ (k.integer = some true → k.noninteger = some false)

/- The closed fact table for a quantity seeded as `even`. Forward-chaining the
   seed `even = true` along the containments yields a fully resolved record;
   boundedness is forced via even → integer → rational → finite. -/
def evenTable : KB :=
  { integer := some true, rational := some true, real := some true,
    finite := some true, even := some true, odd := some false,
    algebraic := some true, transcendental := some false, irrational := some false,
    infinite := none, complex := some true, noninteger := some false,
    prime := none, composite := none }

/- The closed fact table for an unbounded real quantity (seeded `infinite` and
   `real`). Not-bounded contradicts every set whose membership forces
   boundedness, so rational / algebraic / irrational / transcendental, and
   hence integer / even / odd / prime / composite, all resolve to false; the
   quantity is a non-integer. -/
def infiniteTable : KB :=
  { integer := some false, rational := some false, real := some true,
    finite := some false, even := some false, odd := some false,
    algebraic := some false, transcendental := some false,
    irrational := some false, infinite := some true, complex := some true,
    noninteger := some true, prime := some false, composite := some false }

@[grind] lemma evenTable_consistent : consistentTheory evenTable := by
  unfold consistentTheory evenTable; simp

@[grind] lemma infiniteTable_consistent : consistentTheory infiniteTable := by
  unfold consistentTheory infiniteTable; simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method deduceEven return (out : KB)
  ensures consistentTheory out
  ensures out.even = some true
  ensures out.finite = some true
  -- an even quantity is rational, hence algebraic and not irrational, hence not
  -- transcendental: both `irrational` and `transcendental` resolve to false.
  ensures out.transcendental = some false
  ensures out.irrational = some false
  -- a quantity seeded only as `even` is an integer but its primality is
  -- undetermined (it could be 2, or 4, …), so neither `prime` nor `composite`
  -- resolves: both stay `none`.
  ensures out.prime = none
  ensures out.composite = none
  do
    -- impl-start
    let k : KB :=
      { integer := some true, rational := some true, real := some true,
        finite := some true, even := some true, odd := some false,
        algebraic := some true, transcendental := some false, irrational := some false,
        infinite := none, complex := some true, noninteger := some false,
        prime := none, composite := none }
    return k
    -- impl-end

method deduceInfinite return (out : KB)
  ensures consistentTheory out
  ensures out.infinite = some true
  ensures out.real = some true
  ensures out.finite = some false
  ensures out.rational = some false
  ensures out.integer = some false
  ensures out.even = some false
  ensures out.odd = some false
  ensures out.algebraic = some false
  ensures out.transcendental = some false
  ensures out.irrational = some false
  ensures out.composite = some false
  ensures out.noninteger = some true
  do
    -- impl-start
    let k : KB :=
      { integer := none, rational := none, real := some true,
        finite := some false, even := none, odd := none,
        algebraic := none, transcendental := none,
        irrational := none, infinite := some true, complex := some true,
        noninteger := none, prime := none, composite := none }
    return k
    -- impl-end

prove_correct deduceEven by
  loom_solve
  unfold consistentTheory; simp

prove_correct deduceInfinite by
  loom_solve
  unfold consistentTheory; simp
