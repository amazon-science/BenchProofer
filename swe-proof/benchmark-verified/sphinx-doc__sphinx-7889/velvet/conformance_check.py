#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-7889 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the *real* repo type, via the mapping.md bijection. The
              one I op is `textForm` (= the builtin `str(key)`); the A-tagged
              callee `buildSubclass` is left as the REAL `_make_subclass`
              (A legs stay with G-AX). The observable is the constructed class's
              `__display_name__`.
  * ORACLE  — `patch.diff`'s behaviour: the patched `_MockObject.__getitem__`
              applied at base_commit (the real correctness oracle, G-RESOLVE):
              `_make_subclass(str(key), self.__display_name__, self.__class__)()`.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, with patch.diff
applied), stdlib + repo import only. The fuzz seed is pinned (mapping.md §4) for
a deterministic verdict.
"""
import random
import sys
from typing import TypeVar

from sphinx.ext.autodoc.mock import _MockObject, _make_subclass

SEED = 7889
N_FUZZ = 100_000


def shadow_display(display_name, key):
    """Solution.lean impl: out = buildSubclass display_name (textForm key).
    textForm = str() (I op); buildSubclass left as the real _make_subclass (A).
    Observable: the constructed class's __display_name__."""
    name = str(key)                                   # textForm (I op)
    cls = _make_subclass(name, display_name)          # A-tagged: real callee
    return cls.__display_name__


def oracle_display(mock, key):
    """patch.diff behaviour: the patched __getitem__ produces an instance; we
    observe type(instance).__display_name__."""
    inst = mock[key]                                  # patched __getitem__
    return type(inst).__display_name__


def fuzz_keys(n, rng):
    # boundary cases first (plan §4.1 step 4)
    yield ""
    yield "x"
    yield "T"
    yield "SomeClass"
    yield "a.b.c"
    yield "name with spaces"
    yield TypeVar("T")                                # the reported bug class
    yield TypeVar("Name", covariant=True)
    yield int
    yield str
    yield object
    yield 0
    yield -1
    yield 3.14
    yield None
    yield True
    yield ["a", "b"]
    yield ("a",)
    yield {"k": "v"}
    yield type
    # type()-illegal textual names (NUL byte) and control-byte names: the
    # previously-uncovered subset where construction raises ValueError.
    yield "\x00null"
    yield "pre\x00post"
    yield "\x00"
    yield "a\x00"
    yield "\t"
    yield "\x01"
    str_alphabet = list("abcDEF0123_.- TZ") + ["é", "•", "\x00", "\x01", "\x1f"]
    for _ in range(n):
        choice = rng.randint(0, 3)
        if choice == 0:
            k = rng.randint(0, 18)
            yield "".join(rng.choice(str_alphabet) for _ in range(k))
        elif choice == 1:
            yield TypeVar("V%d" % rng.randint(0, 9999))
        elif choice == 2:
            yield rng.randint(-10000, 10000)
        else:
            yield rng.random()


def main():
    rng = random.Random(SEED)
    mock = _MockObject()
    disagreements = []
    count = 0
    for key in fuzz_keys(N_FUZZ, rng):
        count += 1
        try:
            shadow = ("ok", shadow_display(mock.__display_name__, key))
        except Exception as e:                        # noqa: BLE001 - mirror oracle
            shadow = ("err", type(e).__name__)
        try:
            oracle = ("ok", oracle_display(mock, key))
        except Exception as e:                        # noqa: BLE001
            oracle = ("err", type(e).__name__)
        if shadow != oracle:
            disagreements.append((key, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for key, sh, orc in disagreements:
            print("  key=%r shadow=%r oracle=%r" % (key, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of subscriptMock agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
