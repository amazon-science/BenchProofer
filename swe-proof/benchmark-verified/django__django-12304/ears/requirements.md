# Requirements: Enumeration choices classes usable in templates

## Introduction

Django's model enumeration helpers — `Choices`, `IntegerChoices`, and
`TextChoices` (in `django/db/models/enums.py`), built via the `ChoicesMeta`
metaclass (a subclass of `enum.EnumMeta`) — bundle a set of enumeration members,
each carrying a stored value and a human-readable label.

These enumeration classes cannot currently be used from within the Django
template language. The Django template engine, when it resolves a name to a
value and finds that value is callable, invokes it with no arguments and
substitutes the result. An enumeration class is itself callable: invoking it
performs a value lookup and therefore requires a `value` argument. When a
template references the class (for example to reach one of its members and then
that member's `label` or `value`), the no-argument call fails, so the member and
attribute the template wanted can never be reached.

The goal is to make these enumeration classes resolve in templates as the class
object itself (so member and attribute access proceeds), by marking the class
with the standard Django convention that tells the template engine not to call
it, while leaving every existing enumeration behavior unchanged.

## Requirement 1: Enumeration classes are not invoked by the template engine

**User story:** As a developer, I want to reference an enumeration choices class
and its members directly in a Django template, so that expressions like a
member's label or value render correctly instead of failing.

**Acceptance criteria**

1. WHEN a class is created through the `ChoicesMeta` metaclass (i.e. any
   `Choices`, `IntegerChoices`, or `TextChoices` subclass), THEN that class
   SHALL carry the standard Django marker that instructs the template engine not
   to call it during variable resolution.
2. WHEN the Django template engine resolves a variable to an enumeration choices
   class, THEN the engine SHALL leave the class object intact (SHALL NOT invoke
   it with no arguments) and SHALL use the class itself as the resolved value.
3. WHEN a template resolves an enumeration member reached through such a class
   and then accesses that member's `label` attribute, THEN the rendered output
   SHALL be the member's human-readable label.
4. WHEN a template resolves an enumeration member reached through such a class
   and then accesses that member's `value` attribute, THEN the rendered output
   SHALL be the member's stored value.
5. IF an enumeration choices class is passed into the template rendering context
   and referenced by name, THEN rendering the template SHALL succeed without
   raising the missing-argument error that a no-argument call of the class would
   otherwise raise.

## Requirement 2: Existing enumeration value/label behavior is preserved

**User story:** As a developer relying on model enumerations, I want all
existing enumeration behavior to remain exactly the same, so that adding
template support does not regress any current usage.

**Acceptance criteria**

1. The system SHALL keep the value→label association built from a class's
   members unchanged; a member's `label` SHALL continue to return the label
   supplied for that member (or the auto-generated title-cased label derived
   from the member name when none is supplied).
2. WHEN the class-level `choices`, `labels`, `values`, or `names` properties are
   read, THEN each SHALL return the same sequence it returned before, including
   the leading empty entry when an `__empty__` label is defined.
3. WHEN a value or member is tested for membership in an enumeration class via
   the `in` operator, THEN the result SHALL be unchanged: a non-enum operand
   SHALL match when it equals one of the members' values, and an enum operand
   SHALL match by standard enum containment.
4. WHEN an enumeration member is cast to `str`, THEN the result SHALL be the
   string form of the member's stored value.
5. The system SHALL continue to support the functional API for constructing
   integer and text enumerations, and SHALL continue to generate a text member's
   value from its name when only a label is provided.
6. IF two members are defined with the same value, THEN class creation SHALL
   still raise the duplicate-value error (uniqueness enforcement is retained).
7. The system SHALL continue to reject unsupported member value types (for
   example boolean, UUID, or timezone-bearing datetime values) exactly as
   before, and SHALL continue to accept the previously valid label
   configurations.
