import Mathlib
-- imports-end

/-!
Making the free symbols of an expression generically positive.

A symbol can carry a set of declared algebraic *properties* (for example that it
is finite, that it is an integer, that it is commutative, and so on). Each such
property is recorded as a name together with a known truth value; properties
whose value is not determined are simply absent.

This routine rewrites an expression so that every symbol whose sign is not
already determined is replaced by a brand-new symbol that is asserted to be
positive. A symbol counts as "sign undetermined" exactly when it carries no
known value for the `positive` property.

The intended behaviour for each replaced symbol: the new symbol is asserted to be
positive *in addition to* every property the original symbol already declared —
the replacement should not discard any of the original symbol's known properties.
The full property record the new symbol then carries is whatever a freshly built
symbol with that declared property set entails (the declared properties together
with everything they imply).

Declaring a symbol from a property set is a PARTIAL operation. Not every property
set is one a symbol can be declared with: a set that states the same property
twice is not a declaration at all, and a set whose stated values cannot hold
together simultaneously has no symbol satisfying it. Where the declaration has no
record, this routine has no value either — the whole call has none, rather than a
shortened list of records. So the routine's DEFINEDNESS is inherited, and
inherited from exactly the declarations it forms: those of the sign-undetermined
symbols. A declaration formed for no symbol it replaces cannot make the routine
valueless, and cannot make it valued either.

That partiality is carried below as what a partial operation IS — an operation on
its domain — rather than as a total operation that reports a placeholder
somewhere: the inferred record of a declaration comes only together with the fact
that the declaration is one that has a record. Whether a property set is such a
declaration is a separate and TOTAL question: it always has an answer, and "no"
is one of its answers rather than a failure. Two consequences belong to the
behaviour itself and not to any one way of realizing it. There is no such thing
as the inferred record of a property set that is not a declaration, so no part of
this behaviour can depend on one or be spent obtaining one. And a behaviour that
would put a property set to the inference without having settled that it is a
declaration must settle that first — a step that always completes, whichever way
it comes out.

The behaviour is stated abstractly as an input→output relation over the list of
symbol property records; the implementation and correctness proof are supplied
separately.
-/

-- axioms-start
/-- A symbol's known property record: a list of `(property name, truth value)`
pairs. A property whose value is undetermined is absent from the list (mirroring
the convention that only known properties are recorded). -/
abbrev Assumptions := List (String × Bool)

/-- Where declaring a symbol from a property set HAS a result: `declAccepted decl`
is `true` exactly on the property sets a fresh symbol can be declared with, and
`false` on a set that is not a declaration — the same property stated more than
once, or stated values that cannot hold together simultaneously. Whether a set is
one of those is itself a total question: it always has an answer, and the answer
`false` is an answer rather than a failure.

`resolveAssumptions decl h` is the inference itself: the full property record a
freshly built symbol carries once it is declared with `decl` — the declared
properties together with every property they entail (sign/positivity reasoning,
reality, finiteness interactions, …). The inference is PARTIAL, and is carried
here as what a partial operation is — an operation on its domain. It is
applicable only together with `h`, the fact that `decl` is a set that has a
record, so no term names the inferred record of a property set that has none, and
nothing below can be made to depend on one.

These are unchanged ambient dependency operations — declaring a symbol from a
property set and reading back its complete inferred record — declared opaque so
they appear in the executable implementation. They are validated against the real
dependency by the differential conformance check (an A-reference). The proof
consumes no property of them (they occur identically in the specification and the
implementation), so no contract axiom is asserted. This routine's own behaviour is
held constant — only which property sets are handed to it is at issue. -/
opaque declAccepted : Assumptions → Bool
opaque resolveAssumptions : (decl : Assumptions) → declAccepted decl = true → Assumptions
-- axioms-end

-- pure-start
/-- A symbol's sign is undetermined exactly when it carries no known value for the
`positive` property (the value is neither known-true nor known-false, hence the
key is absent from the record). -/
def signUndetermined (a : Assumptions) : Bool := (a.lookup "positive").isNone

/-- The property set used to declare the replacement symbol: the original
symbol's own properties, with the assertion that it is positive stated in front
of them. -/
def assertPositive (a : Assumptions) : Assumptions := ("positive", true) :: a
-- pure-end

-- post-conditions-start
/-- `posify` over the property records of an expression's free symbols.

Read the two halves together; both are load-bearing.

DEFINEDNESS. The replacement declarations this behaviour forms are exactly
`assertPositive a` for the ORIGINAL symbols `a` whose sign is undetermined.
`result` carries a list of records precisely when every one of those is a
declaration that has a record, and carries no value at all precisely when at
least one of them has none. Consequently the acceptance of a property set formed
from a symbol that is not replaced cannot influence the outcome in either
direction: whether the routine has a value is settled by the kept symbols alone.
And because the inference is an operation on its domain, a property set is not
something this behaviour can put to it at all without first settling that it is a
declaration — a question that, wherever it is asked, has an answer.

VALUE. Where `result` carries a list, it is the list of full inferred property
records of the replacement symbols, one per original sign-undetermined symbol,
taken in order: element `i` is the record of the symbol declared with the `i`-th
kept symbol's own properties together with positivity. Symbols whose sign is
already determined are not replaced and contribute nothing. -/
def problem_spec_posify (syms : List Assumptions) (result : Option (List Assumptions)) : Prop :=
  if h : ∀ a ∈ syms.filter signUndetermined, declAccepted (assertPositive a) = true then
    result = some ((syms.filter signUndetermined).pmap
      (fun a ha => resolveAssumptions (assertPositive a) ha) h)
  else
    result = none
-- post-conditions-end

-- impl-start
def implementation_posify : List Assumptions → Option (List Assumptions)
  | [] => some []
  | a :: as =>
    if signUndetermined a then
      if h : declAccepted (assertPositive a) = true then
        (implementation_posify as).map (fun rs => resolveAssumptions (assertPositive a) h :: rs)
      else
        none
    else
      implementation_posify as
-- impl-end

-- proof-start
theorem correct_posify :
    ∀ (syms : List Assumptions),
      problem_spec_posify syms (implementation_posify syms) := by
  intro syms
  induction syms with
  | nil => simp [problem_spec_posify, implementation_posify]
  | cons a as ih =>
    unfold problem_spec_posify at ih ⊢
    rw [List.filter_cons]
    by_cases hs : signUndetermined a = true
    · rw [if_pos hs]
      by_cases hd : declAccepted (assertPositive a) = true
      · by_cases ht : ∀ x ∈ List.filter signUndetermined as,
            declAccepted (assertPositive x) = true
        · rw [dif_pos ht] at ih
          rw [dif_pos (fun x hx => by
            rcases List.mem_cons.mp hx with h' | h'
            · subst h'; exact hd
            · exact ht x h')]
          simp [implementation_posify, hs, hd, ih, List.pmap]
        · rw [dif_neg ht] at ih
          rw [dif_neg (fun H => ht (fun x hx => H x (List.mem_cons_of_mem _ hx)))]
          simp [implementation_posify, hs, hd, ih]
      · rw [dif_neg (fun H => hd (H a List.mem_cons_self))]
        simp [implementation_posify, hs, hd]
    · rw [if_neg hs]
      simp only [implementation_posify, hs, Bool.false_eq_true, if_false]
      exact ih
-- proof-end
