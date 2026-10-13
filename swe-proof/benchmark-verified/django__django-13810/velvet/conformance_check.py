#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-13810 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's impl region (`stageMode` / `wireStage` / `assemble`)
              transliterated to Python over the real repo types, via the
              mapping.md §2 bijection:
                  stages       <->  reversed(settings.MIDDLEWARE), each a
                                    synthetic middleware class with controllable
                                    sync_capable / async_capable / "raises
                                    MiddlewareNotUsed" (== Stage.usable = False)
                  Chain.flag   <->  handler_is_async
                  stageMode    <->  the middleware_is_async ladder
                  wireStage/assemble <-> the assembly loop's flag threading
                  adaptedMode  <->  A-reference (left as the real adapt_method_mode
                                    in the oracle leg; its soundness is G-AX's)
              The OBSERVABLE is the per-stage wiring trajectory
              `(middleware_is_async, handler_is_async)` recorded at each in-loop
              `adapt_method_mode` call, PLUS the health property that assembly
              completes WITHOUT raising (the consistency the fix restores; the
              pre-patch poisoning surfaces as a TypeError from the asgiref
              adapter when a later stage is wired onto a chain whose recorded
              mode lies about its actual mode).  Both are pure R/I functions of
              the threaded flags -- no A-tagged value enters the observable.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `BaseHandler.load_middleware` run at the gold commit, with
              `adapt_method_mode` instrumented to record (target, handler_is_async)
              at each in-loop call.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

No database is touched: only chain assembly via `load_middleware`. stdlib +
django only. Fuzz seed pinned (mapping.md §4).
"""
import itertools
import os
import random
import sys
import types
import warnings

SEED = 13810
N_FUZZ = 100_000
MAX_STAGES = 4


def _bootstrap_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf_settings")
    mod = types.ModuleType("conf_settings")
    mod.DEBUG = False
    mod.SECRET_KEY = "x"
    mod.DATABASES = {}
    mod.INSTALLED_APPS = []
    mod.MIDDLEWARE = []
    sys.modules["conf_settings"] = mod
    import django
    django.setup()


_SYNTH = types.ModuleType("conf_synthmw")
sys.modules["conf_synthmw"] = _SYNTH


def _make_mw(can_sync, can_async, usable, idx):
    """A synthetic middleware factory.  Its instances are sync callables (as real
    Django middleware instances are); capabilities are class attrs; an unusable
    stage raises MiddlewareNotUsed from __init__ (Stage.usable = False)."""
    from django.core.exceptions import MiddlewareNotUsed

    class MW:
        sync_capable = can_sync
        async_capable = can_async

        def __init__(self, get_response):
            if not usable:
                raise MiddlewareNotUsed
            self.get_response = get_response

        def __call__(self, request):
            return self.get_response(request)

    name = "MW%d" % idx
    setattr(_SYNTH, name, MW)
    return "conf_synthmw." + name


# --- the R/I shadow: Solution.lean stageMode / wireStage / assemble -----------

def shadow_stage_mode(flag, can_sync, can_async):
    return False if ((flag is False) and can_sync) else can_async


def shadow_trajectory(is_async, specs):
    """specs: list of (can_sync, can_async, usable) in PROCESSING order.
    Returns the list of in-loop (middleware_is_async, handler_is_async) pairs the
    assembler observes -- `wireStage`/`assemble` threading the recorded mode."""
    flag = is_async
    traj = []
    for can_sync, can_async, usable in specs:
        target = shadow_stage_mode(flag, can_sync, can_async)
        traj.append((target, flag))            # (middleware_is_async, handler_is_async)
        if usable:
            flag = target                      # the running chain advances (the fix)
        # skipped stage: recorded mode untouched
    return traj


# --- the ORACLE: the REAL patched load_middleware, instrumented ----------------

def oracle_trajectory(BaseHandler, settings, specs, is_async):
    paths = [_make_mw(cs, ca, us, i) for i, (cs, ca, us) in enumerate(specs)]
    settings.MIDDLEWARE = list(reversed(paths))

    records = []
    orig = BaseHandler.adapt_method_mode

    def traced(self, is_a, method, method_is_async=None, debug=False, name=None):
        if name and name.startswith("middleware "):
            records.append((is_a, method_is_async))  # (target, handler_is_async)
        return orig(self, is_a, method, method_is_async, debug, name)

    BaseHandler.adapt_method_mode = traced
    crashed = None
    try:
        BaseHandler().load_middleware(is_async=is_async)
    except Exception as exc:           # pre-patch poisoning -> asgiref TypeError
        crashed = type(exc).__name__
    finally:
        BaseHandler.adapt_method_mode = orig
    return records, crashed


def main():
    warnings.simplefilter("ignore")
    _bootstrap_django()
    from django.conf import settings
    from django.core.handlers.base import BaseHandler

    rng = random.Random(SEED)
    caps = [(True, True), (True, False), (False, True)]

    def fuzz_specs(n):
        # boundary: every stage list up to length 3 over the capability/usable
        # alphabet (excluding neither-capable stages -- the real callee aborts on
        # them with RuntimeError, mapping.md §2; that boundary is G-AX's).
        for length in range(0, 4):
            for combo in itertools.product(caps, repeat=length):
                for ub in itertools.product((True, False), repeat=length):
                    yield [(cs, ca, u) for (cs, ca), u in zip(combo, ub)]
        for _ in range(n):
            k = rng.randint(0, MAX_STAGES)
            yield [(*rng.choice(caps), rng.random() < 0.5) for _ in range(k)]

    disagreements = []
    count = 0
    for spec in fuzz_specs(N_FUZZ):
        for is_async in (True, False):
            count += 1
            shadow = shadow_trajectory(is_async, spec)
            records, crashed = oracle_trajectory(BaseHandler, settings, spec, is_async)
            if crashed is not None:
                disagreements.append((is_async, spec,
                                      "oracle raised %s; the shadow's consistent "
                                      "chain never poisons assembly" % crashed,
                                      shadow, records))
            elif records != shadow:
                disagreements.append((is_async, spec,
                                      "in-loop wiring trajectory differs",
                                      shadow, records))
            if len(disagreements) >= 5:
                break
        if len(disagreements) >= 5:
            break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for ia, spec, why, sh, rec in disagreements:
            print("  is_async=%s spec=%r: %s\n    shadow=%r oracle=%r"
                  % (ia, spec, why, sh, rec))
        return 1
    print("G-CONF OK: R/I shadow of loadPipeline (stageMode/wireStage/assemble) "
          "agrees with patch.diff behaviour (real load_middleware in-loop wiring "
          "trajectory; assembly never poisoned) on %d configurations (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
