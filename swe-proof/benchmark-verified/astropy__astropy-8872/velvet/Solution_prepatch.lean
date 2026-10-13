import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a pure decision over the
--  element-type carried by an input array: given only that element-type, decide
--  the element-type the resulting array is materialized under. The element-type is
--  the read-only input; the result element-type is computed solely from it. The
--  surrounding array-construction machinery that reads back an element-type and
--  rebuilds the array is an UNCHANGED shared continuation reached identically on
--  every branch, so nothing about it is assumed: it is neither consumed as a
--  contract nor deep-modeled. There is no `axiom` declaration and no A-reference.
--  See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The element-type carried by a numeric array, reduced to the only distinctions
   the materialization decision reacts to. Real floating element-types are split
   by storage width because width is exactly what the decision must preserve:
     * `boolean`       — a truth-valued element-type;
     * `integral`      — a signed or unsigned whole-number element-type;
     * `floatHalf`     — a real floating element-type of the narrowest width;
     * `floatSingle`   — a real floating element-type of single width;
     * `floatDouble`   — a real floating element-type of double width; this is
                         ALSO the default real floating element-type an input is
                         converted to when conversion applies;
     * `floatExtended` — a real floating element-type wider than double;
     * `complexFloat`  — a complex floating element-type;
     * `object`        — a generic boxed-Python-object element-type (numbers
                         stored individually as objects rather than packed);
     * `structured`    — a composite record element-type carrying named fields. -/
inductive ElemType where
  | boolean
  | integral
  | floatHalf
  | floatSingle
  | floatDouble
  | floatExtended
  | complexFloat
  | object
  | structured
  deriving Inhabited, DecidableEq

/- The default real floating element-type an input is re-materialized under when
   conversion applies: double width. -/
def defaultFloat : ElemType := .floatDouble

/- Whether the element-type is a real floating element-type of SOME width. The
   decision must treat every member of this family identically — preserve it. -/
def isFloating : ElemType → Bool
  | .floatHalf     => true
  | .floatSingle   => true
  | .floatDouble   => true
  | .floatExtended => true
  | _              => false

/- The GENERAL-path conversion rule (used for a fresh array built from an
   arbitrary input): an integral or boxed-object element-type is converted to the
   default real floating element-type; every other element-type — including EVERY
   floating width, boolean, complex, and structured records — is preserved as
   given. The single behaviour this turns on: a real floating element-type must be
   preserved at its own width, never re-materialized under the default merely
   because it is narrower than some reference width. -/
def castsToFloatGeneral : ElemType → Bool
  | .integral => true
  | .object   => true
  | _         => false

/- The FAST-path conversion rule (used when the input is already an array of the
   target kind, so a boxed-object element-type cannot arise there): only an
   integral element-type is converted to the default real floating element-type;
   every floating width is preserved, and a boolean element-type is preserved on
   this path. -/
def castsToFloatFast : ElemType → Bool
  | .integral => true
  | _         => false

/- The element-type an array ends up materialized under on the GENERAL path: the
   default real floating element-type when conversion applies, otherwise the input
   element-type unchanged. -/
def resultElemGeneral (input : ElemType) : ElemType :=
  if castsToFloatGeneral input then defaultFloat else input

/- The element-type an array ends up materialized under on the FAST path. -/
def resultElemFast (input : ElemType) : ElemType :=
  if castsToFloatFast input then defaultFloat else input
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the element-type a freshly materialized array carries when no element
   type is explicitly requested, for an arbitrary input (the GENERAL path).
   `input` is read-only (not `mut`): the decision computes a single result element
   type and mutates nothing (directive 5).

   Desired behaviour: integral and boxed-object inputs default to the double-width
   real floating element-type; every real floating input is preserved exactly at
   its OWN width, of any width; boolean, complex, and structured-record inputs are
   preserved. In particular a real floating input of a narrow width must keep that
   width — it is never re-materialized under the default for being narrow. -/
method resolveElemGeneral (input : ElemType) return (out : ElemType)
  ensures out = resultElemGeneral input
  -- integral and boxed-object inputs default to the double-width floating type:
  ensures input = .integral → out = .floatDouble
  ensures input = .object → out = .floatDouble
  -- EVERY real floating width is preserved exactly, never widened to the default:
  ensures input = .floatHalf → out = .floatHalf
  ensures input = .floatSingle → out = .floatSingle
  ensures input = .floatDouble → out = .floatDouble
  ensures input = .floatExtended → out = .floatExtended
  -- boolean, complex, and structured-record inputs are preserved unchanged:
  ensures input = .boolean → out = .boolean
  ensures input = .complexFloat → out = .complexFloat
  ensures input = .structured → out = .structured
  -- a real floating input stays floating at its own width (no widening), so the
  -- result is floating iff the input was floating, integral, or object:
  ensures isFloating out = true ↔
    (isFloating input = true ∨ input = .integral ∨ input = .object)
  do
    -- impl-start
    -- Pre-image skeleton (general path): an input is converted to the default
    -- floating type unless its element-type is no narrower than the single-width
    -- reference type (or carries record fields); a boxed-object element-type is
    -- additionally converted. A narrow-width floating input fails the "no narrower
    -- than single width" test and is re-materialized under the default — and a
    -- boolean is converted too. The frozen spec requires every floating width
    -- (and boolean) preserved, so prove_correct MUST fail.
    let result : ElemType :=
      match input with
      | .integral     => .floatDouble
      | .object       => .floatDouble
      | .floatHalf     => .floatDouble   -- narrower than single width ⇒ converted
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .floatDouble    -- cannot represent float ⇒ converted
      | .complexFloat => .complexFloat
      | .structured   => .structured
    return result
    -- impl-end

/- Decide the element-type a materialized array carries on the FAST path, where
   the input is already an array of the target kind (so a boxed-object element
   type cannot arise). `input` is read-only (not `mut`).

   Desired behaviour: only integral inputs default to the double-width real
   floating element-type; every real floating input is preserved exactly at its
   own width, and a boolean input is preserved on this path — a narrow floating
   input is never re-materialized under the default for being narrow. -/
method resolveElemFast (input : ElemType) return (out : ElemType)
  ensures out = resultElemFast input
  -- only integral inputs default to the double-width floating element-type:
  ensures input = .integral → out = .floatDouble
  -- EVERY real floating width is preserved exactly, never widened to the default:
  ensures input = .floatHalf → out = .floatHalf
  ensures input = .floatSingle → out = .floatSingle
  ensures input = .floatDouble → out = .floatDouble
  ensures input = .floatExtended → out = .floatExtended
  -- boolean, complex, object, and structured-record inputs are preserved here:
  ensures input = .boolean → out = .boolean
  ensures input = .complexFloat → out = .complexFloat
  ensures input = .object → out = .object
  ensures input = .structured → out = .structured
  -- a real floating input stays floating at its own width (no widening), so the
  -- result is floating iff the input was floating or integral:
  ensures isFloating out = true ↔ (isFloating input = true ∨ input = .integral)
  do
    -- impl-start
    -- Dispatch on the input element-type. Only whole numbers default to the
    -- double-width floating element-type; every floating width is kept exactly,
    -- and boolean, complex, boxed-object, and structured records are kept as given.
    let result : ElemType :=
      match input with
      | .integral     => .floatDouble
      | .floatHalf     => .floatHalf
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .boolean
      | .complexFloat => .complexFloat
      | .object       => .object
      | .structured   => .structured
    return result
    -- impl-end

prove_correct resolveElemGeneral by
  loom_solve <;>
    cases input <;>
      simp_all [resultElemGeneral, castsToFloatGeneral, defaultFloat, isFloating]

prove_correct resolveElemFast by
  loom_solve <;>
    cases input <;>
      simp_all [resultElemFast, castsToFloatFast, defaultFloat, isFloating]
