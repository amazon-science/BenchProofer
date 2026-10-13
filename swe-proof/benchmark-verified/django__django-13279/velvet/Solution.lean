import Velvet.Std
-- imports-end

/- Total correctness: the real encoder always terminates (it is a straight-line
   dispatch over pure serialization/signing calls), so a diverging implementation
   must NOT satisfy this spec. Partial correctness would let a non-terminating
   branch discharge its postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- Carriers, identified abstractly (mapping.md §2): a piece of session data, its
   serialized byte form, a content hash of that form, and the final textual
   encoding. Only the textual encoding is observed by callers; the intermediate
   carriers exist so the legacy encoding can be modeled as the exact composition
   of the unchanged building blocks it is built from (see `legacyEncoding`). -/
abbrev SessionData := Nat
abbrev Serialized  := Nat
abbrev Hash        := Nat
abbrev Encoded     := Nat

/- The UNCHANGED building blocks the encoder delegates to. None is the operation
   under spec (the dispatch + the legacy composition are spelled out below); each
   is a pre-existing community callee with published behavior. Provenance +
   executable soundness are in mapping.md §3 / axiom_check.py (G-AX).

   * `serialize` — turn a piece of session data into its serialized byte form.
   * `hashOf`    — a salted keyed content hash of a serialized form.
   * `wrap`      — combine a hash and a serialized form into one textual blob
                   (a reversible packaging of the two).
   * `standardEncoding` — the standard signed-and-compressed textual encoding,
                   together with the standard loader that inverts it.

   These are modeled as opaque functions: the spec pins the encoder's output to
   compositions of them, never to a free-floating oracle (directive 8). G-AX
   binds each to its real callee and checks the legacy composition is read back
   by the long-standing legacy reader, and the standard encoding by its loader. -/
opaque serialize        : SessionData → Serialized
opaque hashOf           : Serialized → Hash
opaque wrap             : Hash → Serialized → Encoded
opaque standardEncoding : SessionData → Encoded
-- axioms-end

-- pure-start
/- The legacy-compatibility textual encoding of a piece of session data, modeled
   as the exact composition of the unchanged building blocks: serialize it, hash
   the serialized form, then package the hash together with the serialized form
   into one reversible textual blob. This is the form the long-standing legacy
   reader can read back unchanged — the behavior the public report asks for when
   the legacy hashing-algorithm mode is in effect. -/
def legacyEncoding (d : SessionData) : Encoded :=
  wrap (hashOf (serialize d)) (serialize d)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Serialize and encode a piece of session data into its textual form.

   Desired behavior: the encoder is consulted together with a flag selecting the
   legacy hashing-algorithm mode (the sha1 setting the public report names). When
   that legacy mode is in effect, the encoder must emit the legacy-compatibility
   form — serialized, hashed, and packaged so the long-standing legacy reader can
   read it back unchanged; the public report's exact failure is that, in this
   mode, written data could not be decoded back by another running instance. When
   the legacy mode is NOT in effect, the encoder emits the standard form.

   `sessionData` and `legacyHashMode` are read-only (neither is `mut`): the
   encoder produces a textual form and mutates no input (directive 5). -/
method encodeSession (sessionData : SessionData) (legacyHashMode : Bool)
    return (out : Encoded)
  ensures legacyHashMode = true  → out = legacyEncoding sessionData
  ensures legacyHashMode = false → out = standardEncoding sessionData
  do
    -- impl-start
    -- Dispatch on the legacy hashing-algorithm mode. In legacy mode emit the
    -- legacy-compatibility composition (serialize, hash, package); otherwise emit
    -- the standard form. The legacy branch is the behavior the change introduces.
    let result : Encoded :=
      if legacyHashMode then legacyEncoding sessionData
      else standardEncoding sessionData
    return result
    -- impl-end

prove_correct encodeSession by
  loom_solve
