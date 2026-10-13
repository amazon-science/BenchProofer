# Requirements: ResolverMatch repr handles partial views and quotes field values

## Introduction

`ResolverMatch` (in `django/urls/resolvers.py`) is the object returned by URL
resolution; its `__repr__` produces a human-readable summary of the matched
view callable (`func`) and the resolution metadata (`args`, `kwargs`,
`url_name`, `app_names`, `namespaces`, `route`).

Two problems exist in the current representation:

1. When the resolved view is a `functools.partial` object, the representation
   renders the callable unhelpfully (it does not reveal the underlying function
   or the arguments the partial was pre-bound with), because `ResolverMatch`
   derives its callable description from attributes that a `functools.partial`
   does not carry meaningfully.
2. The scalar/metadata fields are interpolated with their plain string form,
   so strings appear unquoted and are visually ambiguous (e.g. a `url_name`
   or `route` is indistinguishable from surrounding text).

The goal is to make `ResolverMatch.__repr__` render the `func` portion
informatively when the view is a `functools.partial`, and to render every
metadata field using its unambiguous (quoted/`repr`) form, while leaving all
other `ResolverMatch` behavior (attribute values, indexing, view-name
computation, resolution) unchanged.

The behavior is localized to `ResolverMatch.__repr__` in
`django/urls/resolvers.py`.

## Requirement 1: Represent partial view callables informatively

**User story:** As a developer inspecting a resolved URL match, I want the
`repr` of a `ResolverMatch` whose view is a `functools.partial` to reveal the
underlying function and the pre-bound arguments, so that I can understand what
callable will actually handle the request.

**Acceptance criteria**
1. WHEN `repr()` is called on a `ResolverMatch` whose `func` is a
   `functools.partial` instance, THEN the returned string's `func=` portion
   SHALL be the standard Python representation of that partial object (its own
   `repr`), revealing the wrapped underlying function together with the
   arguments and keyword arguments the partial was constructed with, rather than
   a bare dotted name.
2. WHEN the resolved view is a `functools.partial`, THEN the `func=` portion of
   the `repr` SHALL be derived solely from that partial object's own
   representation, irrespective of any attributes (such as `__name__` or
   `__module__`) the object may otherwise carry.

## Requirement 2: Represent metadata fields unambiguously

**User story:** As a developer reading a `ResolverMatch` repr, I want string
and collection fields shown in their unambiguous quoted form, so that values
such as names and routes are clearly delimited.

**Acceptance criteria**
1. WHEN `repr()` is called on a `ResolverMatch`, THEN the `args`, `kwargs`,
   `url_name`, `app_names`, `namespaces`, and `route` values SHALL each be
   rendered using their Python `repr` form (i.e. strings appear quoted,
   collections appear in their literal form).
2. WHEN a `ResolverMatch` has a string `url_name`, THEN that `url_name` SHALL
   appear quoted in the `url_name=` portion of the `repr` output.
3. WHEN a `ResolverMatch` has a string `route`, THEN that `route` SHALL appear
   quoted in the `route=` portion of the `repr` output.
4. The `repr` string SHALL present these fields in the order `func`, `args`,
   `kwargs`, `url_name`, `app_names`, `namespaces`, `route`, wrapped in a
   `ResolverMatch(...)` prefix and suffix.

## Requirement 3: Preserve representation of ordinary view callables

**User story:** As a maintainer, I want the representation of a normal
(non-partial) view to be unchanged, so that the fix does not regress the common
case.

**Acceptance criteria**
1. WHEN `repr()` is called on a `ResolverMatch` whose `func` is an ordinary
   function-based or class-based view (not a `functools.partial`), THEN the
   `func=` portion SHALL be the dotted module-and-name path of that view, as it
   was before this change.
2. IF the resolved view is not a `functools.partial`, THEN the `func=` portion
   SHALL NOT be rendered as a partial-object representation.

## Requirement 4: Preserve all other ResolverMatch behavior

**User story:** As a maintainer, I want every non-`repr` aspect of
`ResolverMatch` to keep working exactly as before, so that adding this
representation change introduces no regressions.

**Acceptance criteria**
1. The `ResolverMatch` attributes `func`, `args`, and `kwargs` SHALL retain the
   exact values supplied at construction, and indexing a match at positions 0,
   1, and 2 SHALL continue to return `func`, `args`, and `kwargs` respectively.
2. The system SHALL continue to compute `url_name`, `app_name`, `app_names`,
   `namespace`, `namespaces`, `route`, and `view_name` for a resolved match as
   it did before this change.
3. WHEN a request is resolved through the normal request-handling path, THEN the
   resolved `ResolverMatch` SHALL remain available on the request (and on the
   response) with the same attribute values it had before this change.
4. The system SHALL leave URL resolution and reverse resolution behavior
   (including namespaced, nested, and include-based lookups) unchanged.
