#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13810.

The behaviour under spec is a pure control/data-flow; there is NO consumed
axiom.  What G-AX validates here are the two **A-reference** deep models of
`Solution.lean` against the REAL UNCHANGED callees `load_middleware` invokes:

  (A-reference 1) `adaptedMode (hmode flag target) = if flag = target then hmode
      else target`  ==  the actual execution mode of the callable returned by the
      real `BaseHandler.adapt_method_mode(target, handler, method_is_async=flag)`,
      in the consistent regime the assembler maintains (flag == actual mode of
      the handler passed in).  The real adapter:
        * wraps a sync callable into async (sync_to_async) when target is async,
        * wraps an async callable into sync (async_to_sync) when target is sync,
        * returns the callable unchanged when its recorded mode already matches.
      So the returned callable's actual mode is `target` when flag != target, and
      the handler's current actual mode (== flag, in regime) when flag == target.

  (A-reference 2) `stageMode (flag) (s) = if (flag = False and s.canSync) then
      False else s.canAsync`  ==  the `middleware_is_async` chosen by the real
      `if/elif/else` ladder in `load_middleware`, over every stage that advertises
      at least one capability.

  (boundary) a stage advertising NEITHER capability makes the real
      `load_middleware` raise `RuntimeError` before any wiring (mapping.md §2),
      so such stages are correctly excluded from the modeled `stages` list.

Runs in-container (the prebuilt SWE-Bench instance image); django is importable.
Exit 0 iff every obligation holds.
"""
import asyncio
import os
import sys
import types
import warnings


def _bootstrap_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "axcheck_settings")
    mod = types.ModuleType("axcheck_settings")
    mod.DEBUG = False
    mod.SECRET_KEY = "x"
    mod.DATABASES = {}
    mod.INSTALLED_APPS = []
    mod.MIDDLEWARE = []
    sys.modules["axcheck_settings"] = mod
    import django
    django.setup()


# --- Solution.lean reference encodings (kept in lock-step with the models) ----

def adapted_mode(hmode, flag, target):
    """Solution.lean `adaptedMode`."""
    return hmode if flag == target else target


def stage_mode(flag, can_sync, can_async):
    """Solution.lean `stageMode`."""
    return False if ((flag is False) and can_sync) else can_async


# --- A-reference 1: adaptedMode == adapt_method_mode (consistent regime) ------

def check_adapted_mode(h):
    def sync_fn(request):
        return request

    async def async_fn(request):
        return request

    checked = 0
    # Consistent regime: the mode recorded for the running chain (flag) equals
    # the actual mode of the handler passed in.  This is the invariant the
    # assembler preserves, and the only regime in which the real adapter is
    # total (outside it, asgiref raises -- the very poisoning the spec forbids).
    for actual in (True, False):
        flag = actual                      # consistent
        method = async_fn if actual else sync_fn
        for target in (True, False):
            res = h.adapt_method_mode(target, method, method_is_async=flag)
            real_actual = asyncio.iscoroutinefunction(res)
            model = adapted_mode(actual, flag, target)
            assert real_actual == model, (
                "adaptedMode deep model unsound: actual=%s flag=%s target=%s "
                "-> real %s, model %s" % (actual, flag, target, real_actual, model))
            checked += 1
    return checked


# --- A-reference 2 + boundary: stageMode == the middleware_is_async ladder -----

def _ladder(handler_is_async, middleware_can_sync, middleware_can_async):
    """The REAL selection ladder transcribed verbatim from
    django/core/handlers/base.py:43-51 (unchanged by the patch)."""
    if not middleware_can_sync and not middleware_can_async:
        raise RuntimeError("middleware must have at least one capability")
    elif not handler_is_async and middleware_can_sync:
        return False
    else:
        return middleware_can_async


def check_stage_mode():
    checked = 0
    boundary_hits = 0
    for flag in (True, False):
        for can_sync in (True, False):
            for can_async in (True, False):
                if not can_sync and not can_async:
                    # boundary: the real ladder aborts assembly with RuntimeError;
                    # such a stage never reaches the modeled fold.
                    try:
                        _ladder(flag, can_sync, can_async)
                    except RuntimeError:
                        boundary_hits += 1
                        continue
                    raise AssertionError(
                        "expected RuntimeError for neither-capable stage "
                        "(flag=%s)" % flag)
                real = _ladder(flag, can_sync, can_async)
                model = stage_mode(flag, can_sync, can_async)
                assert real == model, (
                    "stageMode deep model unsound: flag=%s canSync=%s canAsync=%s "
                    "-> real %s, model %s" % (flag, can_sync, can_async, real, model))
                checked += 1
    assert boundary_hits == 2, "expected 2 neither-capable boundary cases"
    return checked, boundary_hits


def main():
    warnings.simplefilter("ignore")
    _bootstrap_django()
    from django.core.handlers.base import BaseHandler

    h = BaseHandler()
    n_adapt = check_adapted_mode(h)
    n_stage, n_boundary = check_stage_mode()

    print("G-AX OK: adaptedMode deep model (== adapt_method_mode, consistent "
          "regime) sound on %d combinations; stageMode deep model (== the "
          "middleware_is_async ladder) sound on %d combinations + %d "
          "neither-capable RuntimeError boundary cases. No consumed axiom."
          % (n_adapt, n_stage, n_boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
