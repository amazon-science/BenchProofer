# Requirements: `quantity_input` return-annotation handling for `None`

## Introduction

`astropy.units.quantity_input` (in `astropy/units/decorators.py`) is a decorator
that validates the physical units of a callable's arguments against annotations
(or decorator keyword arguments), and — when the callable declares a return
annotation naming a unit — converts the returned value to that unit before
handing it back to the caller.

Return type hints are commonly written for callables that return nothing, most
notably constructors (`__init__`), whose idiomatic annotation is `-> None`.
Currently, when a decorated callable declares a return annotation of `None`, the
wrapper treats `None` like a unit target and calls `.to(...)` on the returned
value. Because the returned value is `None` (or otherwise carries no convertible
unit), this raises `AttributeError: 'NoneType' object has no attribute 'to'`,
making the decorator unusable on constructors and other functions that return
`None`.

The goal is to make the decorator treat a `None` return annotation the same way
it treats an absent return annotation: the wrapped callable's result is returned
unchanged, with no unit conversion attempted. All existing argument-validation
and return-conversion behavior must be preserved unchanged.

## Requirement 1: `None` return annotation returns the value unchanged

**User story:** As a developer decorating a constructor or a function that
returns nothing, I want to annotate its return type as `None` so that a static
type checker understands it returns nothing, without the decorator raising an
error at call time.

**Acceptance criteria**

1. WHEN a callable decorated with `quantity_input` declares a return annotation
   of `None` and is invoked with valid arguments, THEN the wrapper SHALL return
   the wrapped callable's result unchanged, without attempting any unit
   conversion on it.
2. WHEN the wrapped callable annotated with a `None` return type returns `None`,
   THEN the wrapper SHALL return `None` and SHALL NOT raise an exception (in
   particular SHALL NOT raise `AttributeError` from attempting attribute access
   such as `.to` on the returned value).
3. IF the return annotation is `None`, THEN the wrapper SHALL NOT call any
   unit-conversion operation on the returned value.

## Requirement 2: Concrete-unit return annotation still converts the result

**User story:** As a developer, I want a return annotation that names a real
unit to keep converting my function's result to that unit, so that the existing
return-conversion feature continues to work.

**Acceptance criteria**

1. WHEN a decorated callable declares a return annotation that names a concrete
   unit and returns a quantity, THEN the wrapper SHALL convert the returned
   value to the annotated unit and return the converted value.
2. The system SHALL, for a return annotation naming a unit, produce a returned
   value whose unit equals the annotated unit.
3. IF a callable declares no return annotation (the annotation is absent/empty),
   THEN the wrapper SHALL return the wrapped callable's result unchanged, with no
   conversion attempted.

## Requirement 3: Argument unit validation and conversion is preserved

**User story:** As a developer, I want argument unit checking to keep behaving
exactly as before, so that fixing the `None` return case does not regress the
core feature.

**Acceptance criteria**

1. WHEN an argument is annotated (or targeted via a decorator keyword) with a
   unit or a physical-type string and a compatible quantity is passed, THEN the
   wrapper SHALL accept the call and SHALL pass the argument through preserving
   its original unit (it SHALL NOT force-convert the argument's unit).
2. WHEN a target unit is supplied for a parameter via a decorator keyword
   argument, THEN that decorator keyword SHALL take precedence over any
   annotation on the same parameter for the purpose of unit validation.
3. WHEN equivalencies are supplied to the decorator, THEN argument validation
   SHALL succeed for values that are convertible only under those equivalencies,
   and those equivalencies SHALL be in force while the wrapped callable executes.
4. WHEN a parameter is not annotated and has no decorator target, THEN the
   wrapper SHALL leave that argument unchanged and SHALL NOT require it to be a
   quantity.
5. The system SHALL apply the same validation to keyword arguments and to
   parameters that fall back to their default values as it applies to positional
   arguments, including parameters that carry a default value.
6. WHILE validating arguments the system SHALL accept both `astropy` unit
   objects and physical-type strings as valid annotation/target forms.

## Requirement 4: Error behavior for invalid arguments is preserved

**User story:** As a developer, I want incorrect argument units to keep raising
the same clear errors, so that misuse is still reported precisely.

**Acceptance criteria**

1. WHEN an argument is passed in a unit that is not convertible to the target
   unit/physical type, THEN the wrapper SHALL raise `astropy.units.UnitsError`.
2. WHEN the wrapper raises for a non-convertible argument, THEN the error message
   SHALL state that the offending argument to the named function must be in units
   convertible to the target unit's string form, naming the argument and function.
3. WHEN an argument that is expected to carry a unit is passed a value with no
   `unit` attribute (e.g. a plain number), THEN the wrapper SHALL raise
   `TypeError` whose message states that the named argument to the named function
   has no `unit` attribute and suggests passing an astropy `Quantity` instead.
4. WHEN a parameter's target set explicitly permits `None` and the passed value
   is `None`, THEN the wrapper SHALL accept the call and pass the `None` through
   without unit validation.
5. WHEN a parameter's argument value is `None` and that parameter's default value
   is also `None`, THEN the wrapper SHALL pass the `None` through even if a target
   unit is specified.
