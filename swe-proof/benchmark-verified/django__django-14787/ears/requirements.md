# Requirements: `method_decorator()` must preserve wrapper assignments on the callable it hands to the wrapped decorator

## Introduction

`django.utils.decorators.method_decorator(decorator, name='')` adapts an
ordinary function decorator so it can be applied to a method (either directly on
a method, or on a class together with a `name` argument). Internally, the helper
`_multi_decorate(decorators, method)` builds a per-call closure `_wrapper` that,
at call time, constructs a *bound callable* representing the target method with
`self` already bound, and then feeds that bound callable through each supplied
decorator.

Today the bound callable is created with
`functools.partial(method.__get__(self, type(self)))`. A `functools.partial`
object carries none of the identity metadata that a normal function exposes —
it has no `__name__`, `__module__`, `__qualname__`, `__doc__`, `__dict__`, and
so on. Consequently, any user decorator that inspects those attributes of the
callable passed to it — for example a decorator applying `functools.wraps` to
its inner function, or one that logs `func.__name__` — raises
`AttributeError: 'functools.partial' object has no attribute '__name__'` or
otherwise misbehaves.

The goal is to ensure that the callable `method_decorator` hands to a wrapped
decorator carries the same identity metadata as the original method, so that
decorators relying on standard function attributes (and on `functools.wraps`)
work correctly — while every existing behavior of `method_decorator` /
`_multi_decorate` continues to hold.

## Requirement 1: The callable passed into a wrapped decorator exposes the original method's identity metadata

**User story:** As a developer writing a function decorator that inspects or
copies the wrapped function's identity (e.g. via `functools.wraps` or by reading
`func.__name__`), I want `method_decorator` to give my decorator a callable that
looks like the original method, so that my decorator does not crash and produces
correctly-named wrappers.

**Acceptance criteria**

1. WHEN a decorator adapted by `method_decorator` is invoked and, inside the
   per-call `_wrapper` built by `_multi_decorate`, the bound callable for the
   target method is constructed, THEN that bound callable SHALL carry the
   identity metadata of the original method rather than the bare metadata of a
   `functools.partial` object.
2. WHEN the wrapped decorator reads the standard wrapper-assignment attributes of
   the callable it receives — specifically `__name__`, `__module__`,
   `__qualname__`, `__doc__`, and `__annotations__` — THEN each such attribute
   SHALL be present and SHALL equal the corresponding attribute of the original
   target method.
3. WHEN the wrapped decorator reads `__name__` of the callable it receives, THEN
   the value SHALL be the original method's name (i.e. accessing `__name__` SHALL
   NOT raise `AttributeError`).
4. WHEN the wrapped decorator reads `__module__` of the callable it receives,
   THEN the value SHALL be present (non-`None`) and equal to the original
   method's defining module.
5. The system SHALL copy the wrapper-*update* attributes of the original method
   onto the bound callable as well, so that the mapping in the method's
   `__dict__` (any attributes previously attached to the method) is reflected on
   the callable handed to the decorator.
6. WHEN a decorator adapted by `method_decorator` finishes, THEN the identity
   metadata transfer described above SHALL be performed using the standard
   function-metadata copying semantics (equivalent to `functools.wraps` /
   `functools.update_wrapper`), so that the set of copied attributes matches what
   those utilities copy.

## Requirement 2: Existing `method_decorator` / `_multi_decorate` behavior is preserved

**User story:** As a maintainer, I want the metadata fix to be surgical, so that
all previously-working behaviors of `method_decorator` keep holding.

**Acceptance criteria**

1. The final wrapper returned by `_multi_decorate` SHALL continue to expose the
   original method's identity attributes (name, module, qualname, doc), i.e.
   `method_decorator` SHALL preserve the decorated method's signature-visible
   metadata as before.
2. WHEN a decorator adds a new attribute to the function it decorates, THEN that
   attribute SHALL still appear on the wrapper produced by `method_decorator`.
3. WHEN `method_decorator` is given a tuple/iterable of decorators, THEN the
   decorators SHALL be applied so that the call order matches the order in which
   they appear in the iterable, and all decorators' added attributes SHALL be
   preserved on the resulting wrapper.
4. WHEN `method_decorator` is applied with a single decorator, a decorator that
   takes arguments, or is used to decorate a class (with `name`) and its methods,
   THEN it SHALL continue to behave as before, wrapping the correct method and
   returning a working, correctly-bound callable.
5. WHEN `method_decorator(decorator, name=...)` is given a `name` that is not a
   method of the decorated class (empty or nonexistent attribute), THEN it SHALL
   raise `ValueError` describing that `name` must be the name of a method of the
   decorated class.
6. WHEN `method_decorator(decorator, name=...)` names an attribute that exists
   but is not callable, THEN it SHALL raise `TypeError` indicating the attribute
   is not a callable attribute of the class.
7. WHEN the adapted method is invoked on an instance, THEN it SHALL call the
   original underlying method bound to that instance and return its result
   unchanged, and the descriptor/`__get__` binding behavior SHALL be preserved.
8. The system SHALL preserve these behaviors without altering the observable
   result of calling the decorated method (the return value and the effect of
   each decorator SHALL be identical to before, aside from the now-available
   metadata on the callable passed into the decorator).
