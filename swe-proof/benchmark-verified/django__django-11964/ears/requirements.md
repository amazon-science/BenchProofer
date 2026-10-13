# Requirements: String conversion of enumerated choice members

## Introduction

Django provides enumeration helper classes in `django.db.models.enums` —
`Choices` (the shared base, built on `enum.Enum` via the `ChoicesMeta`
metaclass) and its concrete subclasses `IntegerChoices` (an `int`-backed enum)
and `TextChoices` (a `str`-backed enum). These are used to declare the
`choices=` of model fields such as `CharField` and `IntegerField`.

Each enumeration member carries an underlying value (a string for text
choices, an integer for integer choices) and a human-readable label. When a
member is used where a plain string is expected — for example as a freshly
assigned model-instance attribute rendered in a template, or serialized when
talking to an external API — Python's textual conversion of the member is
produced.

The defect: textual conversion of a member yields the default `enum.Enum`
representation of the form `"<ClassName>.<MEMBER_NAME>"` instead of the
underlying value. This makes a just-created object (whose attribute still
holds the enum member) render differently from a reloaded object (whose
attribute holds the plain value), an inconsistency that leaks into templates
and outbound payloads.

The goal is to make textual conversion of any enumerated choice member return
the textual form of its underlying value, while leaving every other documented
behavior of these enumeration classes unchanged.

## Requirement 1: Textual conversion returns the member's value

**User story:** As a developer using `TextChoices`/`IntegerChoices` for a model
field, I want converting a choice member to a string to yield its underlying
value, so that a freshly created instance renders and serializes the same way
as one reloaded from the database.

**Acceptance criteria**

1. WHEN a member of a `Choices` subclass is converted to a string (its Python
   textual conversion), THEN the enumeration SHALL return the textual
   conversion of that member's underlying value.
2. WHEN a member of a text-backed choices class is converted to a string, THEN
   the enumeration SHALL return that member's underlying string value exactly
   (including the empty string when the value is empty).
3. WHEN a member of an integer-backed choices class is converted to a string,
   THEN the enumeration SHALL return the decimal textual form of that member's
   underlying integer value.
4. The textual conversion of a member SHALL NOT include the enumeration class
   name or the member name (i.e. it SHALL NOT be of the form
   `"<ClassName>.<MEMBER_NAME>"`).
5. The system SHALL produce the same textual conversion result regardless of
   the member's label and regardless of whether the enumeration declares an
   empty (`__empty__`) member.
6. WHEN a model-field attribute has been assigned a choice member and the
   attribute is rendered in a string context (such as a template), THEN the
   rendered text SHALL equal the textual form of the member's underlying value.
7. This textual-conversion behavior SHALL be defined on the shared choices base
   so that it applies uniformly to text-backed members, integer-backed members,
   and any other member of a choices subclass.

## Requirement 2: Preserve existing member attributes and representation

**User story:** As a developer, I want the value, label, and debug
representation of a choice member to stay exactly as before, so that changing
string conversion does not disturb existing behavior.

**Acceptance criteria**

1. The system SHALL keep each member's `value` attribute equal to its declared
   underlying value, with its original type preserved (integer for
   integer-backed members, string for text-backed members).
2. The system SHALL keep each member's `label` property equal to the declared
   label, or to a title-cased label auto-derived from the member name when no
   label is declared.
3. The system SHALL keep the debug representation (`repr`) of a member in its
   original form showing the class name, member name, and underlying value
   (for example `<ClassName.MEMBER: value>`).
4. IF a member is declared with no explicit label, THEN the system SHALL derive
   its label by replacing underscores with spaces and title-casing the member
   name.

## Requirement 3: Preserve class-level choices metadata

**User story:** As a developer, I want the aggregate metadata exposed by a
choices class to be unaffected, so that field definitions and admin/forms
continue to work.

**Acceptance criteria**

1. The system SHALL keep the `choices` sequence as ordered
   `(value, label)` pairs for every member.
2. The system SHALL keep the `values`, `labels`, and `names` sequences aligned
   in declaration order with the `choices` sequence.
3. IF the enumeration declares an empty member (`__empty__`), THEN the system
   SHALL keep a leading `(None, <empty label>)` entry in `choices`, with the
   corresponding `None` value, empty label, and `'__empty__'` name appearing
   first in `values`, `labels`, and `names` respectively.
4. The system SHALL keep membership testing working both for enumeration
   members and for raw underlying values (a raw value that equals some member's
   value SHALL be reported as contained, and a value matching no member SHALL
   be reported as not contained).
5. The system SHALL keep member lookup by name and by value returning the
   corresponding member.

## Requirement 4: Preserve construction rules and constraints

**User story:** As a developer, I want the functional construction API and the
error conditions of choices classes to remain unchanged, so that misuse is
still rejected and valid definitions still succeed.

**Acceptance criteria**

1. The system SHALL keep supporting the functional construction form
   (creating a choices class from a name and a space-separated list of member
   names), producing sequential integer values for integer choices and the
   member names as values for text choices, with title-cased auto labels.
2. IF an integer choice member is declared with a non-integer second positional
   argument, THEN the system SHALL raise a `TypeError` reporting that the object
   cannot be interpreted as an integer.
3. IF two members of a choices class are declared with the same underlying
   value, THEN the system SHALL raise a `ValueError` reporting the duplicate.
4. IF a choices class is declared with a base type that the enumeration
   machinery does not accept, THEN the system SHALL raise a `TypeError`
   describing that the base type is not acceptable.
5. The system SHALL keep supporting choices classes backed by value types other
   than integer and string, with every member still receiving a valid
   (non-`None`) label under the usual declared-or-auto-derived label rules.
