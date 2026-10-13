import Mathlib
-- imports-end

-- axioms-start
/-- Encoding of a character sequence into a byte sequence under a named output
charset. This is the standard string-to-bytes encoding operation; it is an
UNCHANGED callee here, so only its signature is declared. The proof agent may
add a `_prop` axiom only if a proof step requires one. -/
opaque encode : List Char → List Char → List UInt8
-- axioms-end

-- pure-start
/-- The kinds of input value the coercion must turn into a byte sequence.
* `bytesV b`            — a value that already is a byte sequence `b`.
* `memoryviewV b r`     — a view over an underlying byte sequence `b`; `r` is the
                          value's textual representation (`r` is irrelevant to the
                          intended result and is present only to model the textual
                          rendering some inputs carry).
* `strV s`              — a character string `s`.
* `otherV text`         — any other value, whose textual rendering is `text`. -/
inductive PyValue where
  | bytesV      (b : List UInt8)
  | memoryviewV (b : List UInt8) (reprText : List Char)
  | strV        (s : List Char)
  | otherV      (text : List Char)
-- pure-end

-- post-conditions-start
/-- The result is the byte sequence that represents `value` in the output
`charset`:
* a byte-sequence value and a view over a byte sequence both yield exactly those
  underlying bytes, unchanged;
* a character string is encoded into bytes under `charset`;
* any other value is rendered to text and that text is encoded under `charset`. -/
def problem_spec_toBytestring (charset : List Char) (value : PyValue)
    (result : List UInt8) : Prop :=
  match value with
  | .bytesV b        => result = b
  | .memoryviewV b _ => result = b
  | .strV s          => result = encode charset s
  | .otherV text     => result = encode charset text
-- post-conditions-end

-- impl-start
def implementation_toBytestring (charset : List Char) (value : PyValue) :
    List UInt8 := Id.run do
  -- Byte-sequence-like values are returned as their underlying bytes directly.
  match value with
  | .bytesV b        => return b
  | .memoryviewV b _ => return b
  | .strV s          => return encode charset s
  | .otherV text     => return encode charset text
-- impl-end

-- proof-start
theorem correct_toBytestring : ∀ (charset : List Char) (value : PyValue),
    problem_spec_toBytestring charset value
      (implementation_toBytestring charset value) := by
  intro charset value
  cases value <;>
    simp only [problem_spec_toBytestring, implementation_toBytestring, Id.run, pure]
-- proof-end
