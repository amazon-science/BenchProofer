# Requirements: Docstring inheritance for properties in the `InheritDocstrings` metaclass

## Introduction

The `InheritDocstrings` metaclass in `astropy/utils/misc.py` fills in missing
docstrings on the members of a class from the members they override in a base
class. As reported, the mechanism works for ordinary methods but silently skips
**properties**: because the eligibility test only recognizes plain functions, a
property that lacks its own docstring never receives the docstring of the
overridden base-class property.

The goal is to make docstring inheritance apply to properties (and, more
generally, data descriptors) in the same way it already applies to methods,
while preserving the existing behavior for methods and leaving members that
already carry a docstring untouched.

Affected module/function: `astropy/utils/misc.py`, the `InheritDocstrings`
metaclass (its class-creation initialization that walks the class body and
assigns inherited docstrings).

## Requirement 1: Inherit docstrings for properties

**User story:** As a developer subclassing a class that uses the
`InheritDocstrings` metaclass, I want an overriding property that has no
docstring of its own to automatically pick up the docstring of the property it
overrides, so that documentation is not lost when I override a property.

**Acceptance criteria**

1. WHEN a class whose metaclass is `InheritDocstrings` is created and its class
   body defines a public member that is a property (a data descriptor) whose own
   docstring is absent, THEN the metaclass SHALL set that member's docstring to
   the docstring of the correspondingly named member found in a base class.
2. WHEN resolving the inherited docstring for such a property, THEN the metaclass
   SHALL search the base classes in method-resolution order and use the docstring
   of the first base class that defines a correspondingly named member.
3. IF a property in the class body already has its own (non-absent) docstring,
   THEN the metaclass SHALL leave that property's docstring unchanged.
4. IF no base class defines a correspondingly named member, THEN the metaclass
   SHALL leave the property's docstring unchanged (absent).
5. WHEN a property's docstring is inherited, THEN accessing the documentation of
   that property on the subclass SHALL yield the exact docstring text defined on
   the overridden base-class property.

## Requirement 2: Preserve existing method docstring inheritance

**User story:** As a maintainer, I want the existing docstring inheritance for
ordinary methods to keep working exactly as before, so that widening the
mechanism to properties does not regress methods.

**Acceptance criteria**

1. WHEN a class whose metaclass is `InheritDocstrings` is created and its class
   body defines a public method whose own docstring is absent, THEN the metaclass
   SHALL set that method's docstring to the docstring of the correspondingly
   named method resolved through the base classes.
2. The system SHALL continue to inherit docstrings for callable members such as
   overridden special methods (for example `__call__`) exactly as it did before.
3. IF a method already has its own docstring, THEN the metaclass SHALL leave that
   method's docstring unchanged.

## Requirement 3: Restrict inheritance to eligible public members

**User story:** As a developer, I want docstring inheritance to be limited to the
appropriate public members, so that private members and members with existing
documentation are not altered.

**Acceptance criteria**

1. The metaclass SHALL only consider members that are public, treating a member
   as public when its name does not begin with a single underscore, and treating
   dunder names (names that both begin and end with double underscores and are
   longer than four characters) as public.
2. IF a member's name is non-public, THEN the metaclass SHALL NOT modify that
   member's docstring.
3. The metaclass SHALL only assign an inherited docstring to a member whose own
   docstring is absent; a member that is neither a function/method nor a
   property/data descriptor SHALL NOT have its docstring modified.
