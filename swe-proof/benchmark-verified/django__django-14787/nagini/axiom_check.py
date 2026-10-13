#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14787.

Executes the REAL unchanged standard-library wrapper-update primitive —
``functools.update_wrapper`` (invoked via ``functools.wraps(method)(...)``,
exactly the call the gold patch introduces in
``_multi_decorate(...)._wrapper``) — on a bare ``functools.partial`` (the
object the bound callable is built from) and asserts that every observation
matches the DEEP MODEL spelled out in model.py.

There is no consumed ``@ContractOnly`` axiom in this bundle; the wrapper-
identity copy is modelled DEEPLY (model.py impl region: the two guarded
per-attribute assignments). This script validates that deep model **== the real
callee** (an A-reference):

  for a function/method ``m`` that has ``__name__`` and ``__module__``,
      bound = wraps(m)(partial(m))          # == update_wrapper(partial(m), m)
  satisfies
      getattr(bound, '__name__')   == m.__name__       (model: Result().name   == method.name,   has_name)
      getattr(bound, '__module__') == m.__module__      (model: Result().module == method.module, has_module)
  and ``m`` itself is left unmodified (the method is read-only).

It also records the pre-patch fact that motivates the change: a bare
``partial`` has NO ``__name__`` of its own (``getattr(partial(m), '__name__',
None) is None``) — the AttributeError in the problem statement — which is why
the prepatch model fails its ``Result().has_name`` postcondition.

Imports only the standard library (``functools`` — the very module the patch
calls); nothing repo-specific. Exit 0 iff every obligation holds.
"""
import functools
import random
import sys
from functools import partial, wraps, update_wrapper


def _make_bound_callable_like_patch(method):
    """Mirror the gold line: wraps(method)(partial(method.__get__(...))).

    We use ``partial(method)`` as the structural twin of
    ``partial(method.__get__(self, type(self)))`` — both are bare partials with
    no ``__name__`` of their own; the wrapper-update behaviour the patch relies
    on is identical for either (it copies from ``method``, the second arg)."""
    bare = partial(method)
    return wraps(method)(bare), bare


def check_reference(method):
    """Assert the deep model == the real wraps/update_wrapper on ``method``."""
    # The two behaviour-bearing attributes the model copies and the F2P test reads.
    assert hasattr(method, "__name__"), "test fixture method lacks __name__"
    assert hasattr(method, "__module__"), "test fixture method lacks __module__"
    m_name = method.__name__
    m_module = method.__module__

    # Pre-patch fact: the bare partial has no __name__ of its own.
    bare = partial(method)
    assert getattr(bare, "__name__", None) is None, (
        "expected a bare partial to expose no __name__ (the bug); got %r"
        % (getattr(bare, "__name__", None),))

    # The patched assembly (real callee).
    bound, _ = _make_bound_callable_like_patch(method)

    # A-reference: the wrapped partial now carries the method's identity.
    assert getattr(bound, "__name__", None) == m_name, (
        "wraps(method)(partial) did not copy __name__: method=%r bound=%r"
        % (m_name, getattr(bound, "__name__", None)))
    assert getattr(bound, "__module__", None) == m_module, (
        "wraps(method)(partial) did not copy __module__: method=%r bound=%r"
        % (m_module, getattr(bound, "__module__", None)))
    # Presence (model: has_name / has_module true on the result).
    assert hasattr(bound, "__name__") and hasattr(bound, "__module__")

    # The method is read-only: update_wrapper must not mutate the wrapped fn.
    assert method.__name__ == m_name, "update_wrapper mutated method.__name__"
    assert method.__module__ == m_module, "update_wrapper mutated method.__module__"

    # update_wrapper returns the same (updated) object that flows onward.
    again = update_wrapper(partial(method), method)
    assert getattr(again, "__name__", None) == m_name
    assert getattr(again, "__module__", None) == m_module


def main():
    # --- boundary fixtures: realistic shapes of the "method" the patch wraps --
    def method(self):
        return "tests"

    class Host:
        def bound_method(self):
            return "tests"

    fixtures = []
    fixtures.append(method)                       # a plain function
    fixtures.append(Host.bound_method)            # an unbound function attribute
    fixtures.append(Host().bound_method.__func__) # the underlying function
    fixtures.append(lambda self: None)            # lambda (__name__ == '<lambda>')

    # functions with deliberately unusual names/modules
    def helper(self):
        return None
    helper.__name__ = "weird name with spaces"
    helper.__module__ = "some.dotted.module"
    fixtures.append(helper)

    def helper2(self):
        return None
    helper2.__name__ = ""                        # empty name (still present)
    fixtures.append(helper2)

    for m in fixtures:
        check_reference(m)

    # --- randomized fuzz over name/module tokens -----------------------------
    rng = random.Random(14787)
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ "
    for _ in range(20000):
        def fz(self):
            return None
        n = rng.randint(0, 30)
        fz.__name__ = "".join(rng.choice(alphabet) for _ in range(n))
        fz.__module__ = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 20)))
        check_reference(fz)

    # WRAPPER_ASSIGNMENTS must in fact include the two attributes we model.
    assert "__name__" in functools.WRAPPER_ASSIGNMENTS, (
        "__name__ not in WRAPPER_ASSIGNMENTS: %r" % (functools.WRAPPER_ASSIGNMENTS,))
    assert "__module__" in functools.WRAPPER_ASSIGNMENTS, (
        "__module__ not in WRAPPER_ASSIGNMENTS: %r" % (functools.WRAPPER_ASSIGNMENTS,))

    print("G-AX OK: deep model (== functools.wraps/update_wrapper) sound over "
          "%d boundary + 20000 fuzz methods; the wrapped partial carries the "
          "method's __name__/__module__, the method is unmodified, and a bare "
          "partial exposes no __name__ (the pre-patch bug)." % (len(fixtures),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
