# Requirements: Deferred URL keyword arguments in TemplateView context

## Introduction

Django's class-based `TemplateView` (in `django/views/generic/base.py`) captures
the keyword arguments taken from a resolved URL route and makes them available in
the template rendering context. Because reaching these arguments through the
context is being phased out, each captured argument is not placed into the
context eagerly; instead it is wrapped in a deferred value produced by the module
helper `_wrap_url_kwargs_with_deprecation_warning(url_kwargs)`, which is called
from `TemplateView.get()`. The deferred value resolves to the original argument
the first time it is consumed and, on that first resolution, emits a one-time
deprecation notice keyed to the argument's name.

The problem: the deferred wrapper advertised only a generic, opaque deferred type
to consumers. When a captured argument was passed into a type-directed operation
— for example, using a URL slug (a string) as the value in a database query
filter — the consumer received something whose apparent type was the opaque
wrapper rather than the underlying value's type. This caused downstream failures
(e.g. a database backend rejecting the parameter as an unsupported type) unless
the caller manually coerced the argument to its real type.

The goal: the deferred wrapper must delegate the *behavioral interface* of the
underlying value — its methods, operators, and conversions — while still
deferring resolution and preserving the deprecation notice, so that URL keyword
arguments can be used directly in operations that invoke the underlying value's
own methods/operators (such as a database query filter) without manual coercion,
and all existing deferral/warning behavior is retained. (This is method
delegation, not type-identity replacement: operations that inspect or dispatch on
the object's own type — for example `isinstance`/`type()` — are not required to
report the underlying value's type.)

## Requirement 1: Deferred wrappers delegate the underlying value's behavior

**User story:** As a developer using `TemplateView` with URL-captured keyword
arguments, I want each argument available in the context to behave like its real
value, so that I can pass it directly into operations that invoke the value's own
methods and operators (such as a database query filter) without explicitly
coercing it.

**Acceptance criteria**
1. WHEN `_wrap_url_kwargs_with_deprecation_warning` wraps a captured URL keyword
   argument, THEN the resulting deferred value SHALL delegate the behavioral
   interface of the argument's underlying value — the methods, operators, and
   conversions defined by that value's type — rather than exposing only a
   generic or opaque deferred-object interface. (The wrapper's own object type as
   reported by type-inspection/dispatch operations need not, and does not, become
   the underlying value's type.)
2. WHEN a wrapped URL keyword argument is consumed by an operation that invokes
   a method, operator, or conversion of the underlying value's type (for example
   a string method, an arithmetic operator, or coercion to text), THEN the
   operation SHALL behave as it would on the underlying value itself.
3. WHEN a wrapped URL keyword argument is passed where its underlying type is
   expected (for example, a captured string slug used as a database query filter
   value), THEN the system SHALL accept it as that type without requiring the
   caller to coerce it, and the operation SHALL behave as if the original value
   had been supplied directly.
4. WHEN the underlying value is resolved through the wrapper, THEN the produced
   value SHALL be exactly the original captured value — nothing added, nothing
   dropped, and equal to what the route captured.

## Requirement 2: Deferred resolution and one-time deprecation notice are retained

**User story:** As a Django maintainer, I want the existing lazy-resolution and
deprecation-warning behavior for URL kwargs in the template context to be
unchanged by the type fix, so that the deprecation path continues to function.

**Acceptance criteria**
1. The system SHALL continue to place each captured URL keyword argument into the
   template context as a deferred value rather than resolving it eagerly.
2. WHEN a deferred wrapper is first consumed, THEN it SHALL emit a
   `RemovedInDjango40Warning` deprecation notice whose message identifies that
   argument by name and directs the reader to reference `view.kwargs` instead.
3. IF a deferred wrapper is never consumed, THEN the system SHALL NOT emit its
   deprecation notice.
4. WHEN deprecation warnings are suppressed by the caller, THEN consuming a
   wrapped argument SHALL still resolve to the correct underlying value.

## Requirement 3: Names and ordering of captured arguments are preserved

**User story:** As a developer, I want the context to contain exactly the URL
keyword arguments that were captured, under their original names, so that
templates and `get_context_data` see the expected keys.

**Acceptance criteria**
1. The system SHALL produce one deferred wrapper for each captured URL keyword
   argument, with the same set of keys as the input arguments.
2. The system SHALL preserve the names (keys) of the captured arguments exactly,
   mapping each name to the wrapper that stands for that argument's value.
3. The system SHALL preserve the order of the captured arguments in the resulting
   collection of wrappers.
4. The deprecation notice carried by each wrapper SHALL be keyed to the name of
   the argument that wrapper stands for.

## Requirement 4: Preserve existing TemplateView context behavior

**User story:** As a Django user, I want `TemplateView`'s established context
behavior to remain intact, so that this fix introduces no regressions.

**Acceptance criteria**
1. WHEN a `TemplateView` is rendered, THEN each captured URL keyword argument
   SHALL be reachable in the rendering context under its name.
2. WHEN `get_context_data` is invoked for a `TemplateView`, THEN the standard
   context entries (including the view instance itself) SHALL continue to be
   present alongside the captured URL keyword arguments.
3. WHEN a wrapped URL keyword argument is rendered as text (for example, coerced
   to a string), THEN it SHALL yield the string form of its underlying value.
4. The system SHALL keep the type of each captured argument's underlying value
   available to callers that access the argument by its name in the context.
