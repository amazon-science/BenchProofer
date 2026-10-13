#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-17029 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`clearAllCaches`) is the body of `Apps.clear_cache`:

    self.get_swappable_settings_name.cache_clear()   # <-- the fix (added)
    self.get_models.cache_clear()
    if self.ready:
        for app_config in self.app_configs.values():
            for model in app_config.get_models(include_auto_created=True):
                model._meta._expire_cache()

The CHANGED op the spec pins is `self.get_swappable_settings_name.cache_clear()`
— emptying the live `functools._lru_cache_wrapper` cache of a method on the
global application registry. Its only observable is a side effect on that
wrapper (`cache_info().currsize` becomes `0`), and it is not reproducible as a
pure, state-free R/I shadow:

  * The state change materializes only on a primed registry: standing up the
    global `Apps` registry with installed apps, priming both `@functools.cache`
    methods, calling `clear_cache()`, then reading `cache_info().currsize` —
    i.e. the F2P integration test itself (`test_clear_cache`), not a
    transliteration this gate can fuzz over >=1e5 inputs.
  * The changed op's content is the constant state assignment
    `swappableOccupancy := 0`; its only R/I shadow is the constant `0`. Diffing
    `0 == 0` carries no information — there is no input-dependent computation to
    refute.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the impl region is the deep state
mutation of a live registry object with no state-free R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub. Soundness of the
modeled mutation is carried instead by G-VERIFY (the spec provably forces both
occupancies to 0 on return), G-DIFF (the prepatch, which never assigns
swappableOccupancy, fails exactly the swappableOccupancy = 0 clause), and the
single functools.cache A-reference fact (G-AX, axiom_check.py). See mapping.md
section 4 and refinement.md section B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-17029 — the modeled do-block "
          "empties the live functools._lru_cache_wrapper caches of two registry "
          "methods (get_swappable_settings_name.cache_clear(); "
          "get_models.cache_clear()); the changed op is a constant state "
          "mutation (swappableOccupancy:=0) with no state-free, input-dependent "
          "R/I shadow. conf_skip=true. Soundness covered by G-VERIFY + G-DIFF + "
          "G-AX (functools.cache A-reference).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
