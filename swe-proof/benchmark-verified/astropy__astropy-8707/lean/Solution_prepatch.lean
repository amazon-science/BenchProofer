import Mathlib
-- imports-end

/-!
Construction of a constant-width "card image" from a raw input.

The raw input may be supplied in one of two forms:

* as a sequence of text characters, or
* as a sequence of raw 8-bit bytes.

When the input is a sequence of raw bytes, each byte is interpreted directly as
the code point whose numeric value equals that byte (the one-to-one Latin-1
correspondence between byte values 0..255 and the first 256 code points). Once
the input is in textual form it is padded out with trailing spaces to the next
multiple of the constant card width (80 columns): inputs already a positive
multiple of the width are returned unchanged; shorter or non-aligned inputs are
extended with spaces up to the next multiple.

Stated as an input → output relation `image ↦ card-image-text`. Accepting either
form always succeeds. The implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- No UNCHANGED dependency callee needs a contract: the textual reinterpretation
-- of raw bytes and the width-padding are both modeled DEEPLY below (the only
-- observable touched by this behavior is the resulting card-image text), so
-- there is no `axiom <callee>_prop` for the proof to consume.

/-- The constant card width, in columns. -/
def cardWidth : Nat := 80

/-- A raw input to card-image construction: either textual characters or a
sequence of raw 8-bit bytes. -/
inductive CardImage where
  | text  : List Char → CardImage
  | bytes : List UInt8 → CardImage
deriving DecidableEq, Repr

/-- Error outcomes of card-image construction. A textual input always succeeds;
this carrier exists to express that an input which cannot be treated as text has
no card image. -/
inductive CardErr where
  | illTyped
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Reinterpret raw bytes as text: each byte becomes the code point whose value
equals the byte (the Latin-1 correspondence; every byte 0..255 maps to a valid
code point). -/
def bytesAsText (bs : List UInt8) : List Char :=
  bs.map (fun b => Char.ofNat b.toNat)

/-- The textual content of a raw input: text passes through; raw bytes are
reinterpreted one byte ↦ one code point. -/
def decodeImage : CardImage → List Char
  | CardImage.text cs  => cs
  | CardImage.bytes bs => bytesAsText bs

/-- Pad text out with trailing spaces to a multiple of the constant card width.
Text already exactly the card width, or a positive multiple of it, is returned
unchanged; otherwise it is extended with spaces up to the next multiple. -/
def padCard (cs : List Char) : List Char :=
  let n := cs.length
  if n = cardWidth then cs
  else if n > cardWidth then
    let r := n % cardWidth
    if r = 0 then cs else cs ++ List.replicate (cardWidth - r) ' '
  else
    let r := n % cardWidth
    cs ++ List.replicate (cardWidth - r) ' '
-- pure-end

-- post-conditions-start
/-- The card image produced from a raw input: the input's textual content
(text as-is; raw bytes reinterpreted one byte ↦ one code point) padded out to a
multiple of the constant card width. Construction always succeeds. -/
def problem_spec_cardFromString (image : CardImage)
    (result : Except CardErr (List Char)) : Prop :=
  result = Except.ok (padCard (decodeImage image))
-- post-conditions-end

-- impl-start
-- PRE-PATCH (buggy) skeleton: there is no reinterpretation of a raw-byte input
-- into text. A textual input is padded and returned; a raw-byte input is fed
-- directly to the width-padding step, which is ill-typed on raw bytes and
-- therefore has no result (the observed crash).
def implementation_cardFromString (image : CardImage) :
    Except CardErr (List Char) := Id.run do
  match image with
  | CardImage.text cs => return Except.ok (padCard cs)
  | CardImage.bytes _ => return Except.error CardErr.illTyped
-- impl-end

-- proof-start
-- Gold proof body carried over; it does NOT close against the buggy impl
-- (the raw-bytes case diverges: the spec requires `Except.ok (padCard …)` but
-- the buggy impl yields `Except.error illTyped`).
theorem correct_cardFromString : ∀ (image : CardImage),
    problem_spec_cardFromString image (implementation_cardFromString image) := by
  intro image
  unfold problem_spec_cardFromString implementation_cardFromString
  cases image with
  | text cs => simp [decodeImage, Id.run, pure]
  | bytes bs => simp [decodeImage, Id.run, pure]
-- proof-end
