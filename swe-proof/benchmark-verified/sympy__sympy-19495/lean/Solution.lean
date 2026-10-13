import Mathlib
-- imports-end

/-!
Substituting a *free* symbol (one that is **not** the bound/dummy variable) into
a set that is described by three components:

* a bound variable,
* a predicate condition phrased in terms of that bound variable, and
* a base set the bound variable ranges over.

The routine reads those three components off its input, applies the substitution
to the condition and to the base set, and hands the three resulting values to the
set-building routine that assembles a set from them.

When the substituted symbol is the free symbol (i.e. it differs from the bound
variable), the substitution acts only on the condition and on the base set; the
identity of the bound variable is part of the set's *binding structure* and is
therefore carried through unchanged. In particular the bound variable must be
preserved even in the corner case where applying the substitution makes the
condition collapse to a trivially-true predicate: the substituted value names a
quantity from the surrounding context, not a new bound variable, so it must not
take the bound variable's place.

Three modeling decisions below are what make every term of this model denote a
routine call that is actually defined, and each is forced by the real routines
rather than chosen for convenience:

* The components live on DISTINCT carriers — a bound variable, a general
  symbolic expression, a condition, and a set — because the routines are each
  defined on some of them and not on the others: a condition is what the collapse
  test inspects, a set is what a membership question is asked about, only a
  general expression may stand as a substituted value, and the *first* position
  of the set-building routine takes a bound variable specifically. A bound
  variable is also an expression, so an explicit inclusion makes it usable where
  an expression is called for (comparing it with the symbol being substituted);
  there is no route in the other direction, because an arbitrary expression is
  not something the set-building routine can bind a set over.
* An ASSEMBLED set is a carrier of its own, reachable only as a result. The
  routine modeled here assembles a set exactly once, at the end, and returns it;
  nothing it does consumes an assembled value. So the set-building routine's
  result carrier has no projections — it normalises what it is given, and the
  value it produces need not carry the three components it was built from — and
  it is also not the carrier the substitution routine, the membership assembly or
  the set-building routine itself take a set FROM. Reading components back out of
  an assembled set, substituting into one, or restricting one further are not
  calls this routine makes, and they are not calls the real routines are defined
  on. The components are available on the INPUT, which is a set already known to
  be of the three-part shape, and nowhere else.
* Every carrier carries STRUCTURAL identity, and the condition and set carriers
  are the shapes this routine ranges over: a condition and a base set given
  outright, neither of them itself a further condition-restricted set. On those
  shapes the substitution routine and the set-building routine are genuine
  functions of their arguments — equal arguments give equal results, with no
  freshly chosen name anywhere in the value — which is what lets the
  specification below state its requirement as an equation between assembled
  values. Which expression is which is exactly what a substitution looks at, so
  structural identity is also the equality the substitution respects.

The desired behavior is stated abstractly as an input→output relation; the
implementation and the correctness proof are supplied separately.
-/

-- axioms-start
/-- A symbolic expression (a symbol, a number, an applied function, …) modeled as
an abstract carrier with structural identity — the identity a substitution
matches on. Concrete construction is irrelevant here; only the routines below are
used. The `tag` field is an inert inhabitant — it is what makes the carrier
`DecidableEq` and lets a particular element be named — and no routine below reads
it. -/
structure Expr where
  tag : Nat
deriving DecidableEq, Inhabited

/-- A BOUND VARIABLE: the kind of value a set may be bound over, and the first
component of the three-part shape below. Its own carrier, because the
set-building routine's first position is defined on a bound variable and not on
an arbitrary expression: handed something else there, together with a condition
that does not mention it, the routine has no variable to bind and fails. Every
bound variable is also an expression (`symExpr` below), but nothing maps back.
The `tag` field is inert, as for `Expr`. -/
structure SymE where
  tag : Nat
deriving DecidableEq, Inhabited

/-- A predicate condition GIVEN OUTRIGHT: a boolean-valued symbolic object, the
second component of the three-part shape below, and not one that carries a
condition-restricted set inside it. Its own carrier, because the routines that
consume a condition and the routines that consume a general expression are
different routines defined on different things: a condition is not something a
substitution may put in place of a symbol. Structural identity, as for `Expr`;
the `tag` field is inert. -/
structure Cond where
  tag : Nat
deriving DecidableEq, Inhabited

/-- A base set GIVEN OUTRIGHT — described by its own range rather than by a
further condition-restriction — which is the kind of set the modeled routine
RECEIVES as its third component. Its own carrier for the same reason as `Cond`: a
membership question is asked about a set and about nothing else, and a set is not
something a substitution may put in place of a symbol. Restricting it to the
shapes described outright is what makes the routines below total and
deterministic on it: substituting into one, and assembling over one, neither fail
nor have to choose a fresh name for a variable. Structural identity, as for
`Expr`; the `tag` field is inert. -/
structure SetE where
  tag : Nat
deriving DecidableEq, Inhabited

/-- An ASSEMBLED set: what the set-building routine below RETURNS. Its own
carrier, and a terminal one — it has no projections, and no routine below takes
one. That mirrors the routine being modeled, which assembles a set once, at the
end, and returns it: an assembled value is never read apart, never substituted
into, and never restricted further, and the real routines are in fact undefined
on such uses. The `tag` field is inert, as for `Expr`. -/
structure AsmSet where
  tag : Nat
deriving DecidableEq, Inhabited

/-- A bound variable, viewed as an expression: the inclusion of the
bound-variable carrier into the expression carrier. It is what lets the bound
variable be compared with the symbol being substituted. It is injective and
structure-preserving (a bound variable IS an expression), and there is
deliberately no map the other way. -/
opaque symExpr : SymE → Expr

/-- Apply a substitution to a CONDITION: `subsCond c old new` is the result of
replacing every free occurrence of `old` by `new` inside `c`, which is again a
condition of the same kind. This is the ordinary substitution routine on symbolic
expressions, taken at the condition component; it is reused unchanged here. -/
opaque subsCond : Cond → Expr → Expr → Cond

/-- Apply a substitution to a BASE SET: `subsSet s old new` is the result of
replacing every free occurrence of `old` by `new` inside `s`, which is again a
base set of the same kind. The same ordinary substitution routine, taken at the
base-set component; it is reused unchanged here. -/
opaque subsSet : SetE → Expr → Expr → SetE

/-- Assemble a set from the three components: a bound variable, a condition on it,
and a base set it ranges over. Reused unchanged, and OPAQUE in both directions:
its value is unknown here, and — the load-bearing part — what it returns lands on
the assembled-set carrier. It normalises what it is handed, so the value it
produces need not retain the three components it was built from; the model
provides no way to take one apart and no way to hand one back to any routine.
Its first argument is a bound variable, which is the domain on which it is
defined for an arbitrary condition. -/
opaque mkSet : SymE → Cond → SetE → AsmSet

/-- `isTrue c` is `true` exactly when `c` is the trivially-true condition. Lets
the surrounding code detect a condition that has collapsed to "always holds". -/
opaque isTrue : Cond → Bool

/-- `mkMemberSet v s` is the set assembled by binding a set over the VALUE `v`,
restricted by the condition "`v` lies in `s`", over the base set `s`. It is ONE
routine rather than a membership question composed with the assembly above,
because the pair is what is defined: the assembly accepts a value where a bound
variable belongs only when the condition it is handed is one that mentions that
value, which is exactly the case here and is not the case in general. Like the
assembly, it produces an assembled set. No implementation of the behavior
specified below has any use for it; it is the shape that the corner case must NOT
produce. -/
opaque mkMemberSet : Expr → SetE → AsmSet
-- axioms-end

-- pure-start
/-- The INPUT: a set already known to be of the three-part shape, so its bound
variable `sym`, its `cond`ition and its `base` set are each readable. This is the
only place components are readable; an assembled set carries no projections. -/
structure CondSet where
  sym : SymE
  cond : Cond
  base : SetE
-- pure-end

-- post-conditions-start
/-- Substituting the free symbol `old` (≠ the bound variable) by `new` yields the
set assembled from

* the bound variable of the INPUT (the binding structure is preserved — the
  substituted value must not take the bound variable's place),
* the input condition with the substitution applied, and
* the input base set with the substitution applied. -/
def problem_spec_freeSubs (cs : CondSet) (old new : Expr) (result : AsmSet) : Prop :=
  result = mkSet cs.sym (subsCond cs.cond old new) (subsSet cs.base old new)
-- post-conditions-end

-- impl-start
def implementation_freeSubs (cs : CondSet) (old new : Expr) : AsmSet := Id.run do
  let cond' := subsCond cs.cond old new
  let base' := subsSet cs.base old new
  return mkSet cs.sym cond' base'
-- impl-end

-- proof-start
theorem correct_freeSubs :
    ∀ (cs : CondSet) (old new : Expr),
      old ≠ symExpr cs.sym →
      problem_spec_freeSubs cs old new (implementation_freeSubs cs old new) := by
  intro cs old new _
  rfl
-- proof-end
