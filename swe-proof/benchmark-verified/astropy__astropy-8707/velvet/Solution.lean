import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The changed operation — normalizing a construction source
   to its character image, accepting a raw octet source as readily as a
   character source — is modeled DEEPLY in the `pure` region (`imageSpec`,
   `codepointsOf`). The fixed-width normalizer that runs AFTERWARD on the
   resulting image is an unchanged downstream helper, applied identically in
   both source cases; it is orthogonal to the behavior under spec and is not
   part of the model (refinement.md step C, mapping.md §3.1). -/
-- axioms-end

-- pure-start
/- A construction source is EITHER a character image already in hand, OR a raw
   octet sequence (each element an octet value, 0–255). The desired behavior is
   that BOTH are acceptable inputs. -/
inductive Source where
  | text (s : List Char)
  | raw  (b : List Nat)
  deriving DecidableEq

/- The single way construction can be refused: a raw octet sequence is rejected
   instead of being accepted as a valid source. This is the only outcome the
   desired behavior distinguishes from success. -/
inductive ImageErr where
  | rawNotAccepted
  deriving DecidableEq

/- The character image obtained from a raw octet sequence: each octet is mapped
   to the character whose code point equals that octet's value (so every octet
   in 0–255 yields exactly one character, byte-for-byte, with no re-encoding).
   Front-recursive so a single unfold is available per element (the Velvet fold
   pattern); the deep model G-AX validates against the real octet→character
   interpretation (mapping.md §3.1, A-reference). -/
def codepointsOf : List Nat → List Char
  | []      => []
  | b :: bs => Char.ofNat b :: codepointsOf bs

@[grind] lemma codepointsOf_nil : codepointsOf [] = [] := rfl
@[grind] lemma codepointsOf_cons (b : Nat) (bs : List Nat) :
    codepointsOf (b :: bs) = Char.ofNat b :: codepointsOf bs := rfl

/- The intended character image obtained from a construction source, before the
   unchanged downstream fixed-width normalizer runs, as
   `Except ImageErr (List Char)` (`error` = the source was refused, `ok img` =
   the character image to normalize and store):

     * a character source is accepted and its image is the source itself;
     * a raw octet source is ALSO accepted — its image is the per-octet
       code-point interpretation above.

   No source is ever refused; a raw octet source is treated exactly like a
   character source whose characters are the per-octet code points. -/
def imageSpec (src : Source) : Except ImageErr (List Char) :=
  match src with
  | Source.text s => Except.ok s
  | Source.raw  b => Except.ok (codepointsOf b)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the character image from a construction source (the image the unchanged
   downstream fixed-width normalizer is then applied to, identically in either
   case). Desired behavior: a raw octet source must NOT be refused — it is
   accepted exactly as a character source is, by interpreting each octet (0–255)
   as the character with that code point. -/
method buildImage (src : Source) return (out : Except ImageErr (List Char))
  require (match src with
            | Source.raw b => ∀ x ∈ b, x < 256
            | Source.text _ => True)
  ensures out = imageSpec src
  do
    -- impl-start
    -- A raw octet source is decoded to a character image (each octet → the
    -- character with that code-point value); a character source is used as-is.
    let image : Except ImageErr (List Char) :=
      match src with
      | Source.text s => Except.ok s
      | Source.raw  b => Except.ok (codepointsOf b)
    return image
    -- impl-end

prove_correct buildImage by
  loom_solve
  simp [imageSpec]
