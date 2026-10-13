import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The behavior under spec is
-- a pass-through of a textual-or-binary payload; the modeled branch performs no
-- call. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A request payload that is either a text value (a sequence of characters) or a
binary value (a sequence of bytes). Only these two shapes of the payload domain
are modeled; the constructor records which of the two a value is. -/
inductive Datum where
  | text  (s : List Char)
  | binary (b : List UInt8)
  deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- Encoding a payload that is already a text or binary value returns that value
unchanged: both its kind (text vs binary) and its contents are preserved. The
result is pinned to be exactly the input, so an implementation that converts a
binary value into a text value — or alters its contents — cannot satisfy this
predicate. -/
def problem_spec_encodeParams (data : Datum) (result : Datum) : Prop :=
  result = data
-- post-conditions-end

-- impl-start
/-- The native-string coercion: a text value is already native and passes
through; a binary value is decoded into the corresponding text value (so its
kind flips from binary to text). This is the pre-patch behavior of the modeled
branch. -/
def toNativeString : Datum → Datum
  | .text s   => .text s
  | .binary b => .text (b.map (fun byte => Char.ofNat byte.toNat))

def implementation_encodeParams (data : Datum) : Datum := Id.run do
  -- pre-patch: the payload is forced through the native-string coercion.
  return toNativeString data
-- impl-end

-- proof-start
theorem correct_encodeParams :
    ∀ (data : Datum),
      problem_spec_encodeParams data (implementation_encodeParams data) := by
  intro data
  -- carries the gold proof shape: the result should equal the input unchanged,
  -- but the buggy impl flips a binary value into a text value, so this is
  -- UNCLOSABLE — exactly the G-DIFF signal.
  rfl
-- proof-end
