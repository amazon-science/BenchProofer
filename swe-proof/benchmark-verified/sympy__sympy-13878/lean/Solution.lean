import Mathlib
-- imports-end

/-!
Cumulative distribution of a continuous random variable whose density is
supported on a bounded interval, given by its lower endpoint `a`, its upper
endpoint `b`, and an evaluation point `x`.

The cumulative distribution of such a variable is a CASE SPLIT on where `x`
falls relative to the support, and the required answer is that this case split
be produced explicitly, assembled from the three operands:

- below the support nothing has accumulated yet, so the value is `0`, and the
  case that says so is guarded by a STRICT cutoff at the lower endpoint (the
  lower endpoint itself already belongs to the support);
- on the support the probability grows from `0` to `1` with an inverse-sine
  profile, `2 · arcsin(√((x − a)/(b − a))) / π`, and the case that says so is
  guarded by a NON-STRICT cutoff at the upper endpoint (the upper endpoint
  itself still belongs to the support);
- beyond the support the outcome is certain, so the value is `1`, under a
  catch-all guard.

WHAT THE CARRIER BELOW DENOTES, and why it records terms rather than numbers.

The answer is a symbolic object and is compared as one, so its shape is part of
it: the number of cases, their ORDER, the STRICTNESS of each cutoff, and the
term structure of each value all distinguish one answer from another. Two case
splits that agree as functions of a real `x` — and on this family several do,
because the inverse-sine profile happens to flatten to `0` below the support and
saturate at `1` above it — are still DIFFERENT answers, and only one of them is
the required one. So the carrier records terms, not real numbers, and the
operands themselves may be free rather than numeric.

WHY THE CARRIER IS A SIGNATURE AND NOT A DATATYPE OF SYNTAX TREES.

`Term T` below is the SIGNATURE of the term-builders the answer is assembled
from: one builder per node, over a carrier `T` left ARBITRARY. Everything under
it — the answer type, the value on the support, the required postcondition, and
the answer this file hands back — is stated for every carrier carrying that
signature. So the operands are elements of some such carrier and nothing more:
they may be assembled WITH, and nothing about them may be OBSERVED. That is part
of what is being specified, not an economy.

The reason is that the surrounding symbolic-algebra layer, which owns the terms
this behavior assembles, IDENTIFIES terms this behavior has no business telling
apart. It evaluates as it builds: a quotient of two equal operands is already the
unit there, a product is already stored in that layer's own argument order, a
sum with a zero operand is already the other operand. A behavior stated over a
datatype of syntax trees could ask a question those identifications settle
differently — the trees say two nodes differ, the layer says the two terms are
the same term — and a behavior whose answer turns on such a question is not a
behavior OF that layer, however the answer it finally hands back is judged. Over
an arbitrary carrier the question cannot be asked at all: the answer can only be
ASSEMBLED from the operands, so what this behavior does is what it does in every
algebra the layer could be, which is exactly the claim to make about it. The
signature therefore carries no laws either: a law would be a question about the
operands that IS settled, and the layer's identifications are its own business.

`CdfObject.caseSplit cs` denotes the case-split object ASSEMBLED FROM the
ordered case list `cs`, and `cs` is what this file pins. It is an abstract
denotation, one level above the value the surrounding layer finally hands back.
That layer owns the case-split constructor, and it is entitled to simplify an
analysis it is handed whenever the operands it is given already settle the
guards: it drops a case whose guard is settled negatively, stops at the first
case whose guard is settled positively, and offers a single unguarded value when
only one case is left standing. So with the operands free the whole ordered
analysis survives, while with all three operands numeric every guard settles and
a single value comes back. Those are the same modeled answer seen through that
layer, and which one is observed is the layer's business rather than this
behavior's. The operand-to-answer correspondence records that composition
(mapping.md §2) and the conformance oracle checks it against the real layer on
operands of both kinds.

Two shapes that are NOT the answer are representable too, so that offering them
is expressible and rejected: a single unguarded value, offered with no case
analysis at all, and the generic accumulation of the density from the far left
up to `x`, left unevaluated — what comes back for this family when no closed
form is on hand.
-/

-- axioms-start
-- No unchanged callee is CONSUMED as an axiom. Every term-builder the answer is
-- composed from -- the integer literals and the circle constant, the field
-- operations, the inverse sine and the square root, the strict and non-strict
-- order relations, the catch-all guard, and the ordered case list itself -- is
-- modeled DEEPLY, as an operation of the signature below rather than as an
-- opaque callee, so there is no `_prop` axiom to declare. The one operation left
-- OUTSIDE the model is the surrounding algebra layer's case-split constructor,
-- and it is outside deliberately: it is not part of this behavior, it is
-- unchanged, and what it does to an analysis whose guards already settle is its
-- own business. It is therefore carried by the operand-to-answer correspondence
-- rather than asserted here, and it is the conformance oracle that holds it to
-- account. The signature itself asserts nothing: it has operations and no laws.
-- axioms-end

-- pure-start
/-- The signature of term-builders this cumulative distribution is assembled
from. Every node is one operation applied to its sub-operands: there is no
opaque "answer" operation, so the required object can only be obtained by
applying these operations to the actual operands `a`, `b`, `x`. The carrier `T`
is arbitrary and the signature offers no way to take a carrier element apart, so
an answer can depend on the operands only by being assembled from them. -/
class Term (T : Type) where
  /-- an integer literal -/
  lit : Nat → T
  /-- a free operand, standing for itself and settling no order comparison -/
  sym : String → T
  /-- the circle constant -/
  pi : T
  div : T → T → T
  mul : T → T → T
  sub : T → T → T
  /-- the inverse sine -/
  arcsin : T → T
  sqrt : T → T
  /-- the STRICT order relation `p < q` -/
  lt : T → T → T
  /-- the NON-STRICT order relation `p ≤ q` -/
  le : T → T → T
  /-- the always-true guard of a catch-all case -/
  always : T

/-- One case of a case split: the value it contributes, and the guard under
which that value is the answer. -/
structure Case (T : Type) where
  value : T
  guard : T

/-- What can come back as the cumulative distribution.

`caseSplit cs` is the case-split object assembled from the ORDERED list `cs`, so
the number of cases and their order are both part of the answer. `bare` is a
single unguarded term, i.e. an answer offered with no case analysis at all.
`accumulateUpTo` is the generic, unevaluated accumulation of the density from
the far left up to the evaluation point -- what is handed back for this family
when no closed form is on hand. -/
inductive CdfObject (T : Type) where
  | caseSplit (cs : List (Case T))
  | bare (e : T)
  | accumulateUpTo (x : T)

/-- The value on the support: the position of `x` normalized by the width of the
support, under a square root, under an inverse sine, scaled by `2/π`. Every node
is built from `a`, `b`, `x` and the constants, so this is a per-operand
expansion and not an answer key. -/
def arcsinProfile {T : Type} [Term T] (a b x : T) : T :=
  Term.div
    (Term.mul (Term.lit 2)
      (Term.arcsin (Term.sqrt (Term.div (Term.sub x a) (Term.sub b a)))))
    Term.pi
-- pure-end

-- post-conditions-start
/-- The cumulative distribution, pinned as the case analysis it is assembled as.

The answer must be an explicit case split -- not a single unguarded value, and
not the unevaluated accumulation of the density -- carrying exactly three cases
in this order:

  0. value `0` under a STRICT cutoff at the lower endpoint;
  1. the inverse-sine profile under a NON-STRICT cutoff at the upper endpoint;
  2. value `1` under the catch-all guard.

Each conjunct is independent: the first pins what KIND of answer comes back, the
second how many cases it carries, and the last three pin, position by position,
which value is offered under which guard -- including each cutoff's strictness
and which operand it is drawn at. The claim is made for EVERY carrier of the
signature, at every triple of operands drawn from it. -/
def problem_spec_arcsinCdf {T : Type} [Term T] (a b x : T)
    (result : CdfObject T) : Prop :=
  ∃ cs : List (Case T),
    result = CdfObject.caseSplit cs ∧
    cs.length = 3 ∧
    cs[0]? = some ⟨Term.lit 0, Term.lt x a⟩ ∧
    cs[1]? = some ⟨arcsinProfile a b x, Term.le x b⟩ ∧
    cs[2]? = some ⟨Term.lit 1, Term.always⟩
-- post-conditions-end

-- impl-start
def implementation_arcsinCdf {T : Type} [Term T] (a b x : T) :
    CdfObject T := Id.run do
  let mut cs : List (Case T) := []
  cs := cs ++ [{ value := Term.lit 0, guard := Term.lt x a }]
  cs := cs ++ [{ value := arcsinProfile a b x, guard := Term.le x b }]
  cs := cs ++ [{ value := Term.lit 1, guard := Term.always }]
  return CdfObject.caseSplit cs
-- impl-end

-- proof-start
theorem correct_arcsinCdf {T : Type} [Term T] : ∀ a b x : T,
    problem_spec_arcsinCdf a b x (implementation_arcsinCdf a b x) := by
  intro a b x
  unfold problem_spec_arcsinCdf implementation_arcsinCdf
  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl

/-- Non-vacuity witness. The signature is inhabited, and at three free operands
of one carrier that inhabits it -- the operand kind on which the whole assembled
analysis is observable -- the required case analysis is what comes back, by
evaluation.

This carrier is declared HERE, after the answer above, and that placement is
deliberate: nothing that assembles an answer can consult it. A carrier fixed
before the answer would let the answer ask a question about carrier elements
that this particular carrier settles -- the questions the surrounding algebra
layer settles differently, being the whole reason the answer is stated over an
arbitrary carrier instead. A carrier fixed after it can only witness that the
claim above is about something. -/
inductive TermTree where
  | lit (n : Nat)
  | sym (name : String)
  | pi
  | div (p q : TermTree)
  | mul (p q : TermTree)
  | sub (p q : TermTree)
  | arcsin (e : TermTree)
  | sqrt (e : TermTree)
  | lt (p q : TermTree)
  | le (p q : TermTree)
  | always
  deriving DecidableEq

instance : Term TermTree where
  lit := TermTree.lit
  sym := TermTree.sym
  pi := TermTree.pi
  div := TermTree.div
  mul := TermTree.mul
  sub := TermTree.sub
  arcsin := TermTree.arcsin
  sqrt := TermTree.sqrt
  lt := TermTree.lt
  le := TermTree.le
  always := TermTree.always

example : problem_spec_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
    (Term.sym "x")
    (implementation_arcsinCdf (Term.sym "a" : TermTree) (Term.sym "b")
      (Term.sym "x")) := by
  unfold problem_spec_arcsinCdf implementation_arcsinCdf
  refine ⟨_, rfl, ?_, ?_, ?_, ?_⟩ <;> rfl
-- proof-end
