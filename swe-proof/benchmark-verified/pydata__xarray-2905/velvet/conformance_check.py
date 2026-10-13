#!/usr/bin/env python3
"""G-CONF differential conformance for pydata__xarray-2905 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`prepareData`) is the "we don't want nested
self-described arrays" dispatch the gold patch rewrites in
`as_compatible_data` (xarray/core/variable.py:221):

-   data = getattr(data, "values", data)
+   if isinstance(data, (pd.Series, pd.Index, pd.DataFrame)):
+       data = data.values

The CHANGED op is "unwrap to the stored values payload ONLY for the recognized
self-describing container types; forward every other object UNCHANGED — even one
that merely exposes a `.values` attribute". The two observables the dispatch
consults are:

  * `isRecognized`  — whether the object IS one of the recognized container types
                      (`isinstance(data, (pd.Series, pd.Index, pd.DataFrame))`);
  * `valuesPayload` — the object's stored `.values`, when it exposes any.

Both are pure type/attribute reflection on a live Python object; neither side of
the dispatch performs any input-dependent *content* computation. The result is a
SELECTION among free inputs (the object itself, or the values it exposes), not a
transformation. There is therefore no interpreter-free, input-dependent R/I
shadow to differential-test over >=1e5 fuzzed inputs:

  * The discriminating observable is the IDENTITY of the forwarded object — an
    arbitrary user object with a `.values` attribute must come back AS ITSELF
    (so that storing it in an object-dtype array yields `array([<obj>])`), not
    replaced by `obj.values`. That distinction (object identity vs. its `.values`
    payload) materializes only against the live CPython type system and numpy's
    object-array machinery — i.e. the F2P test itself
    (`TestAsCompatibleData::test_unsupported_type`, which asserts
    `orig._data.item()` is the original `CustomWithValuesAttr` instance) — not a
    pure transliteration this gate can fuzz.
  * `isinstance(..., (pd.Series, pd.Index, pd.DataFrame))` is the unchanged
    Python/pandas type predicate; `data.values` is the unchanged attribute
    access. Neither carries information the spec (G-VERIFY) does not already pin
    via the `forwarded` postcondition.

Per SPEC_GUIDE §0 / WORKER_PROMPT: when the modeled op's only discriminating
observable is object identity decided by the live type system with no
interpreter-free R/I shadow, set meta.json conf_skip=true and ship this
status=skip stub (precedent: astropy__astropy-14096, django__django-11066's
identity legs, django__django-11451). Soundness of the modeled behaviour is
carried instead by G-VERIFY (the spec provably forces an UNrecognized object to
be forwarded unchanged, never replaced by its payload) and G-DIFF (the prepatch,
which unwraps any object exposing a values payload, fails exactly the
unrecognized-with-payload clause). See mapping.md §4 and refinement.md §B/§C.
"""
import sys


def main():
    print("G-CONF status=skip: pydata__xarray-2905 — the modeled do-block is the "
          "as_compatible_data self-described-array dispatch whose only "
          "discriminating observable is the IDENTITY of the forwarded object (an "
          "arbitrary user object with a .values attribute must be returned as "
          "itself, not replaced by its .values payload) on the live CPython type "
          "system + numpy object-array machinery; the two arms select among free "
          "inputs (the object, or its stored values) with no input-dependent "
          "content computation. No interpreter-free, input-dependent R/I shadow "
          "exists. conf_skip=true. Soundness covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
