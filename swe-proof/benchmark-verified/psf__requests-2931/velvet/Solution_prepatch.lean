import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The only modeled repo callee — the native-string
--  coercion `toNativeString` — is modeled DEEPLY in the pure region below and
--  validated `== ` its real counterpart by axiom_check.py (G-AX, A-reference),
--  not consumed as an opaque axiom. The modeled operation itself is
--  specified directly, never axiomatized.)
-- axioms-end

-- pure-start
/- A payload value carried by an HTTP request: either a text payload (a sequence
   of code points) or a binary payload (a sequence of octets). The two are
   DISTINCT carriers — a binary payload is not a text payload — which is exactly
   the property the consumer observes (`isinstance(body, bytes)`). -/
inductive Payload where
  | text (s : List Char)
  | binary (b : List UInt8)
  deriving DecidableEq, Inhabited

/- `toNativeString`: the native-string coercion named in the problem statement.
   On a text payload it is the identity; on a binary payload it yields the text
   payload obtained by decoding each octet to its corresponding code point.
   Deep model (A-reference) of the standard coercion; validated against the real
   callee on its in-domain inputs by axiom_check.py (G-AX). Always yields a TEXT
   payload. -/
def toNativeString : Payload → Payload
  | .text s   => .text s
  | .binary b => .text (b.map (fun u => Char.ofNat u.toNat))

@[grind] lemma toNativeString_text (s : List Char) :
    toNativeString (.text s) = .text s := rfl
@[grind] lemma toNativeString_binary (b : List UInt8) :
    toNativeString (.binary b) = .text (b.map (fun u => Char.ofNat u.toNat)) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Encoding a str/bytes payload for transmission returns the payload UNCHANGED:
   both its kind (text vs binary) and its content are preserved. In particular a
   binary payload stays binary — it is never coerced to a text payload. `data`
   is read-only (not `mut`); the operation mutates nothing it is handed
   (directive 5). -/
method encodePayload (data : Payload) return (out : Payload)
  ensures out = data
  do
    -- impl-start
    -- Pre-image skeleton: the encoder coerces a str/bytes payload to the native
    -- string form (`toNativeString data`), so a binary payload is silently
    -- turned into a text payload. The frozen spec requires `out = data`, so for
    -- a binary input `out = .text (...)` ≠ `.binary (...)`; prove_correct MUST
    -- fail (this is the bug the issue reports).
    let r ← pure (toNativeString data)
    return r
    -- impl-end

prove_correct encodePayload by
  loom_solve
