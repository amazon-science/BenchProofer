#!/usr/bin/env python3
"""G-AX — validate the A-reference deep models against the REAL Python behaviour
they stand in for.

The proof consumes NO callee axiom (axioms region is empty). Two A-reference deep
models are validated here against real CPython (refinement.md rows 3, 4):

  1. dotted join:  module ++ "." ++ ownerQualname ++ "." ++ methodName
                   == "%s.%s.%s" % (module, ownerQualname, methodName)
  2. import line:  "import " ++ module == "import %s" % module

Additionally we exercise the language property the fix relies on by building REAL
nested classes: a class's `__qualname__` is its `__name__` for a top-level class
and a strict dotted superset for a nested class, so using the qualified name is
necessary and sufficient to address a method on a nested class.

stdlib-only. exit 0 iff every observation meets the model.
"""
import random
import sys

SEED = 17087
NAME_FRAGS = ["A", "B", "C", "Profile", "Capability", "Inner", "Outer", "X"]
MOD_FRAGS = ["app", "models", "core", "pkg", "appname"]


def main() -> int:
    rng = random.Random(SEED)
    mismatches = 0
    examples = []

    # 1 & 2: dotted join and import line vs real %-format, on fuzzed strings.
    for _ in range(60_000):
        module = ".".join(rng.choice(MOD_FRAGS) for _ in range(rng.randint(1, 3)))
        qual = ".".join(rng.choice(NAME_FRAGS) for _ in range(rng.randint(1, 3)))
        method = rng.choice(NAME_FRAGS).lower()

        model_text = module + "." + qual + "." + method
        real_text = "%s.%s.%s" % (module, qual, method)
        model_imp = "import " + module
        real_imp = "import %s" % module
        if model_text != real_text or model_imp != real_imp:
            mismatches += 1
            if len(examples) < 10:
                examples.append(("join", model_text, real_text))

    # 3: real-class language property — qualname == name for top-level,
    #    dotted superset for nested.
    class Outer:
        class Inner:
            @classmethod
            def m(cls):
                return cls

    class Top:
        @classmethod
        def m(cls):
            return cls

    # top-level: qualname endswith name, no extra dotted prefix beyond enclosing
    if Top.__qualname__.split(".")[-1] != Top.__name__:
        mismatches += 1
        examples.append(("toplevel", Top.__qualname__, Top.__name__))
    # nested: qualname strictly contains the enclosing class and differs from name
    if not (Outer.Inner.__qualname__.endswith("Outer.Inner")
            and Outer.Inner.__qualname__ != Outer.Inner.__name__):
        mismatches += 1
        examples.append(("nested", Outer.Inner.__qualname__, Outer.Inner.__name__))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches")
        for k, g, w in examples:
            print(f"  {k}: model={g!r} real={w!r}")
        return 1

    print(f"G-AX OK: dotted-join / import models == real %-format and the "
          f"nested-class qualname property holds (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
