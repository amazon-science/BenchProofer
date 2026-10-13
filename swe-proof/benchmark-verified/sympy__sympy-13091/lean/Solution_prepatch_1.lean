import Mathlib
-- imports-end

/-!
Symmetric equality for a structured value compared against an arbitrary operand.

The observations below describe the OPERATIVE pair. A structured value can be a
trivial wrapper — a construction that denotes exactly the value it is built
from, as raising a value to the first power denotes that value. When the two
sides are of different kinds and one of them is such a wrapper, the comparison
is redirected to the wrapped value, and it is the pair the comparison finally
lands on that the observations describe.

A structured value exposes an equality test against that operand. Kinds come in
two families, and the FIRST observation is which family the value belongs to:

* a kind may decide equality by BARE OBJECT IDENTITY — its test asks only
  whether the operand is the very same object, so it always has an opinion and
  never has to make sense of the operand at all;
* every other kind classifies the operand by three further observations, in
  order: whether the operand can be interpreted in the value's universe at all;
  whether, once interpreted, it is of a kind the value knows how to compare;
  whether the interpreted content coincides with the value's content.

So the classification of an operand rests on five observations, in this order:

* whether it is literally the same object as the value;
* whether the value's kind decides equality by bare object identity;
* whether the operand can be interpreted in the value's universe at all;
* whether, once interpreted, it is of a kind the value knows how to compare;
* whether the interpreted content coincides with the value's content.

The result of the equality OPERATOR (`==`) is then resolved as follows. The
value's own equality test yields one of three outcomes: a definite `true`, a
definite `false`, or — when it cannot make sense of the operand — an ABSTENTION
(no opinion). On a definite outcome the operator yields it directly. On an
abstention the operator consults the operand's OWN equality test against the
value (its reflected opinion); if that too abstains, the operator falls back to
object identity, which for two distinct objects is `false`.

The crucial property is symmetry: when one side cannot interpret the other, it
must ABSTAIN rather than assert a definite `false`, so that the operand's own
opinion is honoured. Otherwise one could observe `a == b` and `b == a` disagree.
A kind that decides by bare object identity is outside that property by
construction: having no notion of interpreting the operand, it has nothing to
abstain about, and it answers a definite `false` for anything that is not itself.

The inequality operator (`!=`) is exactly the boolean negation of the equality
OPERATOR's result — i.e. it negates the fully resolved `==` (including the
reflected consultation), not merely the value's own equality test (whose
abstention is not a boolean and must not be negated as if it were `true`).
-/

-- axioms-start
-- No unchanged outside callee is consumed. The operand's reflected equality
-- opinion is an arbitrary caller-supplied verdict (modeled as the `otherVerdict`
-- input, a three-valued opinion), not a known library routine; the value's own
-- five-way classification is likewise an input. There is no callee contract to
-- declare.
-- axioms-end

-- pure-start
/-- The value's own three-valued equality opinion about an operand it has
classified by the five observations. An abstention is represented by `none`; a
definite verdict by `some b`. A kind that decides by bare object identity always
has an opinion. For every other kind, when the operand cannot be interpreted at
all the opinion is an abstention (`none`). -/
def selfEqVerdict (sameObj identityOnly interpretable sameKind contentEq : Bool) :
    Option Bool :=
  if sameObj then some true
  else if identityOnly then some false
  else if !interpretable then none
  else if !sameKind then some false
  else some contentEq

/-- Resolve the equality OPERATOR from the value's own opinion and the operand's
reflected opinion. A definite own opinion is taken directly; an abstention defers
to the operand's reflected opinion; if both abstain, the operator falls back to
object identity, `false` for distinct objects. -/
def resolveEq (selfVerdict otherVerdict : Option Bool) : Bool :=
  match selfVerdict with
  | some b => b
  | none =>
    match otherVerdict with
    | some b => b
    | none => false

/-- The fully resolved equality operator result. -/
def richEqRef (sameObj identityOnly interpretable sameKind contentEq : Bool)
    (otherVerdict : Option Bool) : Bool :=
  resolveEq (selfEqVerdict sameObj identityOnly interpretable sameKind contentEq)
    otherVerdict

/-- The inequality operator result: the boolean negation of the resolved
equality operator. -/
def richNeRef (sameObj identityOnly interpretable sameKind contentEq : Bool)
    (otherVerdict : Option Bool) : Bool :=
  !(richEqRef sameObj identityOnly interpretable sameKind contentEq otherVerdict)
-- pure-end

-- post-conditions-start
/-- The equality operator yields exactly the resolved value dictated by the
rule above: the own opinion when definite, otherwise the reflected opinion,
otherwise identity. -/
def problem_spec_richEq (sameObj identityOnly interpretable sameKind contentEq : Bool)
    (otherVerdict : Option Bool) (result : Bool) : Prop :=
  result = richEqRef sameObj identityOnly interpretable sameKind contentEq otherVerdict

/-- The inequality operator yields exactly the negation of the resolved equality
operator. -/
def problem_spec_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
    (otherVerdict : Option Bool) (result : Bool) : Prop :=
  result = richNeRef sameObj identityOnly interpretable sameKind contentEq otherVerdict
-- post-conditions-end

-- impl-start
def implementation_richEq (sameObj identityOnly interpretable sameKind contentEq : Bool)
    (otherVerdict : Option Bool) : Bool := Id.run do
  -- Pre-patch behavior: when the operand cannot be interpreted, the value's own
  -- equality test commits to a definite negative instead of declining to opine,
  -- so the operand's reflected opinion is never consulted (asymmetric result).
  let selfVerdict : Option Bool :=
    if sameObj then some true
    else if identityOnly then some false
    else if !interpretable then some false
    else if !sameKind then some false
    else some contentEq
  match selfVerdict with
  | some b => return b
  | none =>
    match otherVerdict with
    | some b => return b
    | none => return false

def implementation_richNe (sameObj identityOnly interpretable sameKind contentEq : Bool)
    (otherVerdict : Option Bool) : Bool := Id.run do
  let eqResult := implementation_richEq sameObj identityOnly interpretable sameKind
    contentEq otherVerdict
  return !eqResult
-- impl-end

-- proof-start
theorem correct_richEq :
    ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
      (otherVerdict : Option Bool),
      problem_spec_richEq sameObj identityOnly interpretable sameKind contentEq
          otherVerdict
        (implementation_richEq sameObj identityOnly interpretable sameKind contentEq
          otherVerdict) := by
  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
  unfold problem_spec_richEq implementation_richEq richEqRef resolveEq selfEqVerdict
  simp only [Id.run]
  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
    cases otherVerdict <;> rfl

theorem correct_richNe :
    ∀ (sameObj identityOnly interpretable sameKind contentEq : Bool)
      (otherVerdict : Option Bool),
      problem_spec_richNe sameObj identityOnly interpretable sameKind contentEq
          otherVerdict
        (implementation_richNe sameObj identityOnly interpretable sameKind contentEq
          otherVerdict) := by
  intro sameObj identityOnly interpretable sameKind contentEq otherVerdict
  unfold problem_spec_richNe implementation_richNe richNeRef richEqRef resolveEq
    selfEqVerdict
  simp only [Id.run]
  cases sameObj <;> cases identityOnly <;> cases interpretable <;> cases sameKind <;>
    cases otherVerdict <;> rfl
-- proof-end
