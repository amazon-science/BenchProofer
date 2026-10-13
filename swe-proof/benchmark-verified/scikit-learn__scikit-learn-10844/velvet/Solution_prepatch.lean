import Velvet.Std
import Mathlib.Data.Rat.Defs
import Mathlib.Algebra.Order.Field.Rat
import Mathlib.Tactic.FieldSimp
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The single positive square root applied to the
--  similarity coefficient is the unchanged numeric primitive of the
--  computation; it is order-preserving and value-determining on a nonnegative
--  argument, so the entire observable distinction this routine pins — which
--  nonnegative number the coefficient is, and by which combination of the
--  aggregates it is assembled — is carried by the SQUARED coefficient and by
--  the combination plan below. Relating the returned value to that primitive is
--  a squaring identity, not a borrowed contract, so no `axiom` is consumed. See
--  refinement.md (the root is peeled by squaring) and mapping.md §3.)
-- axioms-end

-- pure-start
/- Which of the three aggregates a combination step reads. -/
inductive Aggregate where
  | agree
  | spreadA
  | spreadB

/- An INTEGER-valued step of a combination: read one aggregate, or multiply two
   integer-valued steps. This is the whole integer vocabulary available to the
   routine: the aggregates arrive as machine integers of some width, and the
   only integer arithmetic the combination performs on them is multiplication. -/
inductive IntPlan where
  | read : Aggregate → IntPlan
  | mul : IntPlan → IntPlan → IntPlan

/- A RATIO-valued combination plan: the exact ratio of two integer steps, or the
   product of two ratio-valued plans. A plan is a first-class description of HOW
   the coefficient is assembled from the aggregates — which integer quantities
   are materialised on the way, and in which order the ratios and the products
   are taken. -/
inductive RatPlan where
  | ratio : IntPlan → IntPlan → RatPlan
  | mul : RatPlan → RatPlan → RatPlan
  /- Answer zero outright when an integer step is zero, WITHOUT evaluating the
     rest of the combination. A degenerate partition has aggregates that make
     some quotient's divisor zero, and a routine that goes ahead and divides
     there obtains no number at all; short-circuiting is how a routine still
     produces one. Recording the short-circuit in the plan is what makes "does
     this routine answer at all on a degenerate input" observable. -/
  | zeroThen : IntPlan → RatPlan → RatPlan

/- The integers a two's-complement machine word of `width` bits can hold. An
   integer quantity outside this range cannot be materialised at that width. -/
def inWord (width : Nat) (x : Int) : Prop :=
  -(2 ^ (width - 1)) ≤ x ∧ x ≤ 2 ^ (width - 1) - 1

instance (width : Nat) (x : Int) : Decidable (inWord width x) :=
  inferInstanceAs (Decidable (-(2 ^ (width - 1)) ≤ x ∧ x ≤ 2 ^ (width - 1) - 1))

/- What an integer step of a plan yields, at machine word `width`, on the three
   aggregates. Reading an aggregate yields it. A multiplication yields the
   product ONLY when that product is itself a `width`-bit machine integer:
   otherwise the step has no value at all, and neither does any plan containing
   it. This is the one partiality in the model, and it is what makes a plan's
   choice of intermediates observable rather than a matter of taste. -/
def IntPlan.value (width : Nat) (agree spreadA spreadB : Int) :
    IntPlan → Option Int
  | .read .agree => some agree
  | .read .spreadA => some spreadA
  | .read .spreadB => some spreadB
  | .mul p q =>
      match IntPlan.value width agree spreadA spreadB p,
            IntPlan.value width agree spreadA spreadB q with
      | some x, some y => if inWord width (x * y) then some (x * y) else none
      | _, _ => none

/- What a ratio-valued plan yields, at machine word `width`, on the three
   aggregates. A ratio yields the EXACT rational quotient of its two integer
   steps (a quotient of two machine integers is always a representable
   magnitude, so this step is total once both integer steps have a value, and it
   is undefined only on a zero divisor). A product of two ratios yields their
   exact product. So a plan fails to yield a value exactly when one of the
   integer products it materialises leaves the machine word. -/
def RatPlan.value (width : Nat) (agree spreadA spreadB : Int) :
    RatPlan → Option Rat
  | .ratio n d =>
      match IntPlan.value width agree spreadA spreadB n,
            IntPlan.value width agree spreadA spreadB d with
      | some x, some y => if y = 0 then none else some ((x : Rat) / (y : Rat))
      | _, _ => none
  | .mul p q =>
      match RatPlan.value width agree spreadA spreadB p,
            RatPlan.value width agree spreadA spreadB q with
      | some x, some y => some (x * y)
      | _, _ => none
  | .zeroThen g p =>
      match IntPlan.value width agree spreadA spreadB g with
      | some 0 => some 0
      | some _ => RatPlan.value width agree spreadA spreadB p
      | none => none

/- Truncation of an exact integer back into a `width`-bit two's-complement
   register: the silent wraparound a fixed-width register performs when the
   quantity written to it does not fit. -/
def truncW (width : Nat) (x : Int) : Int :=
  (x + 2 ^ (width - 1)) % (2 ^ width) - 2 ^ (width - 1)

/- The three aggregates do NOT reach this routine as unbounded integers: each
   arrives held in a fixed-width machine REGISTER, and `Word width` is the
   contents of one such register.

   `toExact` reads that content out of the register and into exact unbounded
   arithmetic. It is a PROMOTION — a widening — and not a register operation: a
   routine that promotes has left the fixed-width carrier behind, and every
   arithmetic step it performs afterwards is exact. Arithmetic performed on the
   registers THEMSELVES is a different thing, with a different result, and the
   distinction between the two is exactly what this routine has to get right. -/
structure Word (width : Nat) where
  toExact : Int

/- Register multiplication — the ONLY arithmetic the fixed-width carrier itself
   offers, and the multiplication an unpromoted aggregate is subject to. It is
   total and SILENT, and it WRAPS: the exact product is truncated back into the
   `width`-bit register, so whenever the mathematical product does not fit, what
   the register then holds is a different number (and, for two positive
   aggregates, possibly a negative one).

   A routine that materialises the product of two aggregates IN THEIR REGISTERS
   therefore does not obtain their product, and any coefficient it goes on to
   derive from that content is not the coefficient of the aggregates. This is the
   machine fact the routine must respect, and giving it a home here is what makes
   the distinction observable instead of a matter of prose. -/
instance instMulWord {width : Nat} : Mul (Word width) where
  mul x y := ⟨truncW width (x.toExact * y.toExact)⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A similarity coefficient for two partitions, derived from three nonnegative
   integer aggregates of the agreement structure, each held in a machine register
   of some common width:

     * `agree`   — a count of co-grouped element pairs (zero exactly when the two
                   partitions share no co-grouped pair);
     * `spreadA` — an aggregate of one partition's group sizes;
     * `spreadB` — an aggregate of the other partition's group sizes.

   None of the three is required to be positive. Each spread is at least `agree`,
   and a DEGENERATE input — one where a partition spreads its elements so thinly
   that its aggregate vanishes — is admissible: there the co-grouped count
   vanishes too, and a spread of zero is exactly the case in which forming a
   quotient against it yields no number at all. Such inputs are ordinary, not
   pathological, and the coefficient on them is zero.

   The coefficient is `agree / sqrt(spreadA * spreadB)`; this routine returns its
   SQUARE, `agree^2 / (spreadA * spreadB)`, which determines the coefficient (the
   coefficient is the nonnegative square root of the returned value). When there
   is no co-grouped pair the coefficient is zero — and that case has to be
   ANSWERED rather than computed: it is the case in which a spread may also
   vanish, so a routine that goes ahead and forms the quotients obtains no number
   there at all. Deciding it first, on the co-grouped count alone, is what lets
   the routine produce a number on every admissible input.

   TWO things about this routine are observable, and both are returned.

   1. THE VALUE. `agree^2 / (spreadA * spreadB)` names an exact rational NUMBER,
      built from the integers the three registers HOLD. It does not name an
      evaluation order — the same number is reached by many different
      combinations of the three aggregates — but neither is it free of the
      machine. The registers' own multiplication wraps silently, so a routine
      that assembles its answer through a register product of two aggregates is
      working from a different quantity as soon as that product outgrows the
      register, and the number it then returns is not this one. Reaching this
      value at every width therefore takes a routine that either divides before
      it multiplies, or first promotes the aggregates out of their registers into
      exact arithmetic.

   2. THE COMBINATION PLAN (`RatPlan`). The plan records how the coefficient is
      assembled: which integer products are materialised, where the ratios are
      taken, and whether the degenerate case is decided before the quotients are
      formed. Two plans that denote the same rational number on the generic
      inputs are still different routines, because a plan that materialises an
      integer product can leave the machine word while a plan that only ever
      divides one aggregate by another cannot, and because a plan that forms its
      quotients unconditionally yields nothing on a degenerate input while a plan
      that short-circuits first still yields zero.

   WHICH OBSERVABLE SAYS WHAT THE ROUTINE DOES. The value slot names only WHICH
   number comes out. It cannot name the steps taken to reach it, and in one place
   it actively cannot: the model's exact-rational quotient is TOTAL, and it
   reports 0 for a quotient whose divisor vanishes. The modelled quantity has no
   value there — a division by a vanishing spread yields no number at all — so
   that 0 is an artifact of the rational carrier, with nothing answering to it in
   the computation being described. Two routines whose value slots agree on every
   admissible input can therefore still be different routines: one that decides
   the degenerate case ahead of its quotients yields zero there, one that divides
   first yields nothing there, and the total quotient reports 0 for both.

   The PLAN is the observable that settles which steps were taken, and it is
   pinned at every width and on every admissible triple. The two observables are
   moreover tied by an OBLIGATION and not by a reading of one: the clause

       p.value width agree spreadA spreadB = some v

   below requires the number in the value slot to BE the number the returned plan
   yields, at this call's own width and on this call's own aggregates. So the
   plan's steps are this routine's steps, and a returned plan is not a comment on
   a routine's arithmetic — it is that arithmetic, stated as an object the
   specification can quantify over.

   HOW TO REFINE THIS ROUTINE. Three consequences bind any refinement, and each
   is the difference between a refinement that computes the coefficient and one
   that only appears to.

   * THE SHORT-CIRCUIT IS AN OBLIGATION, NOT A CONVENIENCE. A value slot written
     as an unconditional combination of quotients is NOT a licence to divide
     unconditionally: it denotes the required number only because the rational
     quotient is total, and that totality is a property of the carrier, not of
     the computation. The plan is what a refinement implements, and a plan that
     decides the degenerate case before forming a quotient must be refined by a
     routine that decides it before forming a quotient. A refinement that divides
     by a vanishing spread has obtained no number where zero was required, and it
     refines no implementation that satisfies this specification.

   * A PRODUCT OF TWO AGGREGATES MUST NOT BE FORMED IN THEIR REGISTERS. An
     implementation may reach the value by promoting the aggregates out of their
     registers into exact arithmetic — that is a legitimate way to obtain this
     number — but then a refinement of it must perform the promotion as well, and
     arithmetic left in the fixed-width carrier is not a promotion. What no
     implementation may do is materialise a product of two aggregates at a width
     the product outgrows: the plan clause below has no value there, at any width.

   * SAMENESS OF RESULT IS SAMENESS OF ROUTINE. The plan and the value are the
     whole result. An implementation whose returned plan and returned value agree
     with another's across the admissible domain is not a different routine
     dressed differently; it is the same routine, and a refinement of it is the
     same arithmetic. Implementations that differ only in intermediate
     expressions the model's exact arithmetic cannot observe are, for the purpose
     of refinement, the routine their common plan describes.

   The obligation is therefore: return a plan together with the value THAT PLAN
   YIELDS at this call's own width, where the plan yields the exact coefficient AT
   EVERY MACHINE WORD WIDTH that can hold the three aggregates and ON EVERY
   ADMISSIBLE AGGREGATE TRIPLE — not merely at some convenient width, and not
   merely on the inputs of this call — and where that value is the exact
   coefficient of the integers the registers hold. Three routines fail this. One that
   materialises any product of aggregates: for every width there are aggregates
   the word holds whose product it does not, and there the plan has no value. One
   that combines through a register product of aggregates: it returns a different
   number at exactly the magnitudes where that product outgrows the register. And
   one that forms its quotients without deciding the degenerate case first: on an
   admissible triple whose spread vanishes it yields no number where zero is
   required.

   The result is wrapped in `Option`: `some (p, v)` means the routine does
   produce a coefficient, assembled by plan `p`, with square `v`; `none` would
   mean it produced no number at all. The guarantee is that, for every
   admissible input, it does produce one, and its value is pinned exactly:

     * zero when there is no co-grouped pair (`agree = 0`);
     * otherwise the exact rational `agree^2 / (spreadA * spreadB)`.

   The three aggregates are read-only (directive-5 frame: none is `mut`); the
   plan and the value are produced freshly from them. -/
method fowlkesCoeffSquared (width : Nat) (agree : Word width)
    (spreadA : Word width) (spreadB : Word width)
    return (out : Option (RatPlan × Rat))
  require 2 ≤ width
  require inWord width agree.toExact
  require inWord width spreadA.toExact
  require inWord width spreadB.toExact
  require agree.toExact ≤ spreadA.toExact
  require agree.toExact ≤ spreadB.toExact
  require 0 ≤ agree.toExact
  require 0 ≤ spreadA.toExact
  require 0 ≤ spreadB.toExact
  ensures ∃ (p : RatPlan) (v : Rat), out = some (p, v)
            ∧ 0 ≤ v
            ∧ p.value width agree.toExact spreadA.toExact spreadB.toExact
                = some v
            ∧ (agree.toExact = 0 → v = 0)
            ∧ (agree.toExact ≠ 0 →
                 v = (agree.toExact : Rat) * agree.toExact
                       / ((spreadA.toExact : Rat) * spreadB.toExact))
            ∧ (∀ (w : Nat) (a b c : Int), 2 ≤ w → 0 ≤ a → a ≤ b → a ≤ c →
                 inWord w a → inWord w b → inWord w c →
                 p.value w a b c
                   = some (if a = 0 then 0
                           else (a : Rat) * a / ((b : Rat) * c)))
  do
    -- impl-start
    -- Pre-fix skeleton: combine the two spreads by forming their PRODUCT first
    -- -- in the register, which is where the machine forms it -- and dividing the
    -- squared agreement count into it, with no decision taken on the degenerate
    -- case ahead of the quotient. The plan records exactly that.
    let p : RatPlan :=
      .ratio (.mul (.read .agree) (.read .agree))
             (.mul (.read .spreadA) (.read .spreadB))
    let prod : Word width := spreadA * spreadB
    let v : Rat :=
      if agree.toExact = 0 then (0 : Rat)
      else (agree.toExact : Rat) * agree.toExact / (prod.toExact : Rat)
    return some (p, v)
    -- impl-end

prove_correct fowlkesCoeffSquared by
  loom_solve
