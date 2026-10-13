# Requirements: Napoleon inclusion of documented decorated members

## Introduction

The Napoleon extension (`sphinx.ext.napoleon`) decides, for each member that
autodoc encounters, whether that member should be *included* in the generated
API documentation even though it is private, special, or an `__init__` method.
This decision is made by the `_skip_member` handler in
`sphinx/ext/napoleon/__init__.py`, which is connected to autodoc's
`autodoc-skip-member` event.

For a member of a class or exception, `_skip_member` must first establish that
the member is genuinely *owned* by the class it appears to belong to. It does
this by taking the member object's qualified name (`Owner.member`), extracting
the owning class's short name, and resolving that short name to the actual
class object through the member function's own module/global scope
(`obj.__globals__`). Ownership then holds when the resolved class exists and
directly declares an attribute of that member's name.

The problem: when a member such as `__init__` is decorated (for example with a
decorator applied via `functools.wraps`), the object passed in is the
decorated (outer) object, not the original function. That decorated object's
global scope does not contain the owning class, so ownership resolution fails
and the documented member is wrongly skipped — even though the user enabled its
inclusion (e.g. `napoleon_include_init_with_doc = True`) and the decorated
object still carries the same docstring.

The goal is to resolve the owning class from the *underlying* (undecorated)
object — obtained by following the decorator link chain to the end — so
that a decorated member is still recognized as owned by its class and is
therefore included whenever its category toggle is enabled, while every other
inclusion/skip decision is left exactly as it was.

The affected code is the `_skip_member` function and its ownership-resolution
branch in `sphinx/ext/napoleon/__init__.py`; unwrapping the decorator chain
uses the decorator-unwrapping helper in `sphinx/util/inspect.py`.

## Requirement 1: Include documented decorated class members

**User story:** As a project author who documents decorated `__init__` (or
other decorated) methods, I want those members to appear in the generated docs
just like undecorated ones, so that decorating a method does not silently drop
it from my API documentation.

**Acceptance criteria**

1. WHEN `_skip_member` is invoked for a `class` or `exception` member whose
   member object is a decorated object (its underlying function is reachable
   by following the decorator link chain to the end), THEN the
   handler SHALL resolve the owning class from the *underlying* object's global
   scope rather than the decorated object's own global scope.
2. WHEN the owning class's short name (the portion of the member's qualified
   name before the final dot) is resolved from the underlying object's scope
   and that class directly declares an attribute equal to the member's name,
   THEN the handler SHALL treat the class as the owner of the member.
3. WHEN a decorated member of a `class` or `exception` is owned by its class,
   has a docstring, and falls into a category whose inclusion toggle is enabled
   (init member with the init toggle on, other special member with the special
   toggle on, or private member with the private toggle on), THEN the handler
   SHALL signal that the member is to be included (i.e. it SHALL NOT be
   skipped).
4. IF the member is `__init__`, is a decorated object that preserves the
   docstring, is owned by its class, and the include-init toggle is enabled,
   THEN the handler SHALL signal inclusion of that `__init__` member.
5. The system SHALL resolve the owning class using only a single, dotless
   class short name (`Owner.member`) via the global scope; nested-class
   qualified names (`Outer.Inner.member`) remain handled by module attribute
   traversal and are outside the scope of this change.
6. IF resolving the owning class raises any error, THEN the handler SHALL treat
   the member as not owned by the class rather than propagating the error.

## Requirement 2: Preserve existing inclusion and skip decisions

**User story:** As a Sphinx user relying on Napoleon's current behavior, I want
the ownership fix to change only the decorated-member case, so that all other
private/special/init handling stays exactly as before.

**Acceptance criteria**

1. WHEN a member's object is *not* decorated (its underlying object is itself),
   THEN the handler SHALL resolve the owning class from that object's global
   scope and reach the identical ownership decision as before this change.
2. WHEN `_skip_member` is invoked for a member named `__weakref__`, THEN the
   handler SHALL defer the decision (SHALL NOT force inclusion).
3. WHEN a member has no docstring, THEN the handler SHALL defer the decision
   (SHALL NOT force inclusion), regardless of its category toggles.
4. WHEN a `class` or `exception` member is *not* owned by its resolved class,
   THEN the handler SHALL defer the decision (SHALL NOT force inclusion).
5. WHEN the handler is invoked for a `module` member (rather than a class or
   exception member), THEN it SHALL decide inclusion by the member's category
   and toggles without performing any owning-class resolution.
6. WHILE a category's inclusion toggle is disabled, the handler SHALL defer the
   decision for members of that category (a documented private member with the
   private toggle off, a documented special member with the special toggle off,
   and an `__init__` with the init toggle off SHALL each be deferred).
7. WHEN a documented private, special, or `__init__` member (for a module,
   class, or exception) has its corresponding toggle enabled and — for class
   and exception members — is owned by its class, THEN the handler SHALL signal
   inclusion.
8. The handler SHALL only ever either signal inclusion (do-not-skip) or defer;
   it SHALL never itself force a member to be skipped.
9. WHEN `_skip_member` processes members of a namedtuple-derived class, THEN it
   SHALL apply the same ownership and category rules and SHALL keep the
   previously produced inclusion/skip decisions for those members.
