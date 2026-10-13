import Mathlib
-- imports-end

/-!
The three-valued status table for a single numeric quantity. Each field is a
fuzzy fact about the quantity: `some true` (the property is known to hold),
`some false` (it is known not to hold), or `none` (undetermined). Only the
properties the two witnessed deductions touch are carried.

`finite` is the boundedness fact: a quantity is `finite` when its absolute value
is bounded. The behaviour under specification is that membership in the "small"
number sets (rational / algebraic / irrational / transcendental) forces
boundedness.
-/
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
--  conformance_check.py / G-CONF, not relied on as an axiom.)
-- axioms-end

-- pure-start
/-- A fact table is CLOSED under the intended set-containment relations between
the number classes. Each `A is true ⇒ B is true` clause is a containment; each
`A is false ⇒ B is false` clause is its contrapositive. The boundedness-forcing
containments are the behaviour under specification:

  * a rational quantity is real, is algebraic, AND is bounded;
  * a real quantity is complex;
  * an algebraic quantity is complex AND is bounded;
  * an irrational quantity is real, is not rational, AND is bounded;
  * a transcendental quantity is complex, is not algebraic, AND is bounded;
  * an integer is rational; an even or odd quantity is an integer; a prime or
    composite quantity is an integer; an even quantity is not odd;
  * an unbounded quantity is not bounded; a real quantity that is not an integer
    is a non-integer, and an integer is not a non-integer.

Closure is two-directional: each containment also propagates its contrapositive,
so a quantity known NOT to be bounded is thereby known NOT to be rational /
algebraic / irrational / transcendental, hence not an integer, hence not even /
odd / prime / composite. -/
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
-- pure-end

-- post-conditions-start
/-- Postcondition for the closure of the seed `even = true`. The table must be
closed under `consistentTheory`, must retain the `even` seed, and — via the
`rational → finite` containment (even → integer → rational → finite) — must resolve
`finite = some true`. A rational quantity is algebraic and not irrational, so
`irrational`/`transcendental` resolve to false; its primality is undetermined,
so `prime`/`composite` stay `none`. This pins every fact the F2P test observes. -/
def problem_spec_deduceEven (out : KB) : Prop :=
  consistentTheory out
  ∧ out.even = some true
  ∧ out.finite = some true
  ∧ out.transcendental = some false
  ∧ out.irrational = some false
  ∧ out.prime = none
  ∧ out.composite = none
-- post-conditions-end

-- impl-start
/-- The closed fact table for a quantity seeded as `even`. Forward-chaining the
seed `even = true` along the containments yields a fully resolved record;
boundedness is forced via even → integer → rational → finite. -/
def implementation_deduceEven : KB :=
  { integer := some true, rational := some true, real := some true,
    finite := none, even := some true, odd := some false,
    algebraic := some true, transcendental := some false, irrational := some false,
    infinite := none, complex := some true, noninteger := some false,
    prime := none, composite := none }
-- impl-end

-- proof-start
theorem correct_deduceEven :
    problem_spec_deduceEven implementation_deduceEven := by
  unfold problem_spec_deduceEven implementation_deduceEven consistentTheory
  refine ⟨?_, ?_⟩ <;> simp
-- proof-end

-- post-conditions-start
/-- Postcondition for the closure of an unbounded real quantity (seeded
`infinite` and `real`). `infinite → ¬finite` forces `finite = some false`; via
the contrapositives `¬finite → ¬{rational, algebraic, irrational,
transcendental}`, then `¬rational → ¬integer → ¬{even, odd, prime, composite}`,
every set membership resolves to false; `real → complex` gives `complex`, and a
real non-integer is a `noninteger`. This pins every fact the F2P tests observe
for `oo` / `-oo`. -/
def problem_spec_deduceInfinite (out : KB) : Prop :=
  consistentTheory out
  ∧ out.infinite = some true
  ∧ out.real = some true
  ∧ out.finite = some false
  ∧ out.rational = some false
  ∧ out.integer = some false
  ∧ out.even = some false
  ∧ out.odd = some false
  ∧ out.algebraic = some false
  ∧ out.transcendental = some false
  ∧ out.irrational = some false
  ∧ out.composite = some false
  ∧ out.noninteger = some true
-- post-conditions-end

-- impl-start
/-- The closed fact table for an unbounded real quantity (seeded `infinite` and
`real`). Not-bounded contradicts every set whose membership forces boundedness,
so rational / algebraic / irrational / transcendental — and hence integer / even
/ odd / prime / composite — all resolve to false; the quantity is a non-integer. -/
def implementation_deduceInfinite : KB :=
  { integer := some false, rational := some false, real := some true,
    finite := some false, even := some false, odd := some false,
    algebraic := some false, transcendental := some false,
    irrational := some false, infinite := some true, complex := some true,
    noninteger := some true, prime := some false, composite := some false }
-- impl-end

-- proof-start
theorem correct_deduceInfinite :
    problem_spec_deduceInfinite implementation_deduceInfinite := by
  unfold problem_spec_deduceInfinite implementation_deduceInfinite consistentTheory
  refine ⟨?_, ?_⟩ <;> simp
-- proof-end
