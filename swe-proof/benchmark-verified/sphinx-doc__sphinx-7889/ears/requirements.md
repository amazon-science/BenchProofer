# Requirements: Mock objects must support subscription with non-string keys

## Introduction

Sphinx's autodoc extension can build documentation for modules whose imports are
unavailable by substituting placeholder ("mock") objects for the missing symbols.
This behavior is implemented in `sphinx.ext.autodoc.mock`, principally by the
`_MockObject` class and the `_make_subclass` helper.

When documentation refers to a generically-typed class (for example, a class
declared as a subclass of a mocked, parametrized base such as `Base[T]`), the
mock machinery is subscripted with a key that is not a string — it is a type
parameter object. The current subscription path (`_MockObject.__getitem__`)
forwards the key directly into display-name construction, which concatenates it
onto a string. When the key is not a string this concatenation raises
`TypeError`, and the documentation build fails.

The goal is to make placeholder subscription tolerant of any key object so that
building documentation for generic/parametrized classes succeeds, while
preserving every other behavior of the mock objects and mock modules.

## Requirement 1: Subscription accepts non-string keys

**User story:** As a developer documenting a project that uses mocked, generically
parametrized base classes, I want the placeholder object to be indexable with a
type parameter (or any non-string key), so that my documentation build does not
crash.

**Acceptance criteria**

1. WHEN a mock placeholder object is subscripted with a key that is not a string
   (for example a type parameter object), THEN `_MockObject.__getitem__` SHALL
   return a mock placeholder object rather than raising an exception.
2. WHEN `_MockObject.__getitem__` is invoked with a key of any type, THEN the
   subject SHALL derive the returned object's identity from the textual
   representation of that key, so that display-name construction always receives a
   string component.
3. IF the supplied key is already a string, THEN `_MockObject.__getitem__` SHALL
   behave exactly as before, returning a mock placeholder object identified by that
   string key.
4. The returned object SHALL be an instance of the mock placeholder type (a
   `_MockObject`), so that it can be indexed, attribute-accessed, or called
   further without error.

## Requirement 2: A class may subclass a parametrized mocked base

**User story:** As a developer, I want to declare a class whose base is a
subscripted mocked class (e.g. `class Sub(Base[T])`), so that autodoc can process
generic class definitions.

**Acceptance criteria**

1. WHEN a class is declared with a base obtained by subscripting a mock
   placeholder object (a parametrized mock base), THEN the class definition SHALL
   complete without raising `TypeError`.
2. WHEN such a class carries a docstring, THEN its `__doc__` attribute SHALL be
   exactly the docstring given in the class definition, unchanged by the mock
   machinery.
3. WHEN an instance of such a class is created, THEN the object SHALL be a
   genuine instance of that declared class.

## Requirement 3: Preserve existing mock object behavior

**User story:** As a maintainer, I want all previously supported mock behaviors to
keep working, so that this change fixes the generic-typing crash without
regressing anything.

**Acceptance criteria**

1. WHEN a mock placeholder object's attribute is accessed, THEN the subject SHALL
   return a mock placeholder object (attribute chains SHALL remain mock objects).
2. WHEN a mock placeholder object is called, THEN the subject SHALL return a mock
   placeholder object, EXCEPT that IF it is called as a decorator with a single
   argument that is itself a class or a callable of function/bound-function
   type, THEN it SHALL return that argument unchanged.
3. WHEN a class is declared subclassing a mock placeholder object directly
   (without subscription), THEN the class definition SHALL succeed, any function
   the subclass defines itself SHALL execute and return its own real result
   (rather than a mock value), and the subclass docstring SHALL be preserved on
   `__doc__`.
4. The system SHALL continue to support mocking of modules: accessing an attribute
   on a mocked module SHALL yield a mock placeholder object, and importing a
   configured module name (or any descendant module name) SHALL succeed under the
   mock context.
5. WHEN a mocked module or placeholder is registered as an abstract base class
   subject, THEN `isinstance`/`issubclass`-style abstract-base-class checks against
   it SHALL continue to behave as they did before this change.
6. The mock machinery SHALL be active only within its context manager and SHALL
   remove its import hooks and invalidate the modules it created when the context
   exits, so that mocking does not leak beyond the documentation build.
