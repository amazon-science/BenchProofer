#!/usr/bin/env python3
"""G-CONF differential conformance for astropy__astropy-14096 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`lookupMissingAttribute`) is the miss-path fallback the
gold patch rewrites in `SkyCoord.__getattr__`:

    def __getattr__(self, attr):
        if "_sky_coord_frame" in self.__dict__:
            ...                      # the UNCHANGED prefix (frameOutcome)
        # Fail
-       raise AttributeError(f"'{self.__class__.__name__}' object has no "
-                            f"attribute '{attr}'")
+       return self.__getattribute__(attr)   # <-- the fix

The CHANGED op is "on a genuine miss, return the GENUINE attribute-resolution
routine's outcome (`self.__getattribute__(attr)`) verbatim, instead of
fabricating a fresh AttributeError renamed to the requested attribute". The
outcome it hands back is the FREE INPUT `genuineOutcome` (an UNCHANGED callee,
mapping.md section 3); its R/I shadow is a constant pass-through with no
input-dependent computation to refute.

There is no interpreter-free, input-dependent R/I shadow to differential-test:

  * The discriminating observable is the IDENTITY of the propagated
    AttributeError (must name the genuine inner attribute, e.g. `random_attr`,
    not the requested property, e.g. `prop`). That materializes only against a
    live Python object model: a real SkyCoord subclass with a property whose
    getter accesses a missing attribute, resolved through CPython's descriptor +
    __getattr__ + __getattribute__ machinery — i.e. the F2P test itself
    (`test_subclass_property_exception_error`), not a pure transliteration this
    gate can fuzz over >=1e5 inputs.
  * The miss-path result is exactly the free input `genuineOutcome` (the
    unchanged genuine resolver); the prefix value-path returns the free input
    `frameOutcome`. Neither has an input-dependent computation whose shadow could
    disagree with patch.diff — the changed op's content is "propagate the
    unchanged callee verbatim", carrying no information the spec (G-VERIFY) does
    not already pin.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the modeled op's only
discriminating observable is the outcome of an unchanged callee carried as a free
input (here, the genuine resolver's exception identity) with no interpreter-free
R/I shadow, set meta.json conf_skip=true and ship this status=skip stub
(precedent: django__django-11451). Soundness of the modeled behaviour is carried
instead by G-VERIFY (the spec provably forces the miss path to equal
`genuineOutcome`, never a failure renamed to the requested attribute) and G-DIFF
(the prepatch, which fabricates `Except.error { subject := requested }`, fails
exactly the miss-path clause). See mapping.md section 4 and refinement.md
sections B/C.
"""
import sys


def main():
    print("G-CONF status=skip: astropy__astropy-14096 — the modeled do-block is "
          "the __getattr__ miss-path fallback whose only discriminating "
          "observable is the IDENTITY of the propagated AttributeError (the "
          "genuine inner attribute vs the requested one) on a live Python object "
          "model with CPython descriptor/__getattribute__ machinery; the "
          "miss-path result is the free input `genuineOutcome` (the unchanged "
          "genuine resolver) and the prefix value-path is the free input "
          "`frameOutcome`. No interpreter-free, input-dependent R/I shadow "
          "exists. conf_skip=true. Soundness covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
