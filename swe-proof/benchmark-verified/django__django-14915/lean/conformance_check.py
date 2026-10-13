#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-14915.

The bundle models ONE behavior: obtaining the hash digest of a select-widget
choice-value wrapper (`ModelChoiceIteratorValue`). The Lean implementation
(`implementation_choiceValueHash`) is:

    return some (valueHash m.val)

i.e. the wrapper IS hashable (the `some` carrier — R leg) and its digest is the
wrapped value's own digest `valueHash m.val` (A-reference; the real builtin
`hash` on the value is left in place).

This script builds the R/I shadow of that impl in Python (`shadow_hash`), leaving
the A-tagged callee as the REAL repo callee (`hash(value)`), and differential-
tests it against the ORACLE: the REAL post-patch `ModelChoiceIteratorValue.__hash__`
run in-container. The shadow returns `("some", hash(value))`; the oracle returns
`("some", hash(obj))` when hashable, `("none", None)` when `hash(obj)` raises.

The edge set EXHAUSTIVELY enumerates the modeled wrapped-value forms (zero,
±small, large ±magnitudes, 64-bit boundaries) crossed with DISTINCT accompanying
model objects (including `None`) — so a leg that wrongly read the model object,
or that failed to produce a digest, would disagree. The fuzz loop additionally
samples random integer values. The discriminating case — the wrapper must be
hashable AND its digest equals the value's digest regardless of the model object
— is therefore covered: the oracle (post-patch) is hashable with
`hash(obj) == hash(value)`, while the PRE-patch behavior (`__hash__ = None`,
unhashable) would disagree on the `some`/`none` carrier.

stdlib + django only. Pinned seed: 14915 (also recorded in mapping.md).
"""
import json
import random
import sys

SEED = 14915
N = 120_000


def shadow_hash(value, _inst):
    """R/I shadow of implementation_choiceValueHash.

    R: the wrapper is hashable -> the "some" carrier.
    A-reference: the digest is the wrapped value's own digest (real callee).
    The accompanying model object `_inst` is never read (frame)."""
    return ("some", hash(value))


def main() -> int:
    try:
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                DEBUG=True,
                DATABASES={},
                INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
                USE_TZ=True,
            )
        import django
        django.setup()
    except Exception:
        pass

    try:
        from django.forms.models import ModelChoiceIteratorValue
    except Exception as e:
        print(json.dumps({"status": "error",
                          "reason": f"cannot import django callee: {e!r}"}))
        return 1

    def oracle(value, inst):
        """Post-patch real behavior, normalized to the modeled Option carrier."""
        obj = ModelChoiceIteratorValue(value, inst)
        try:
            return ("some", hash(obj))
        except TypeError:
            return ("none", None)

    rng = random.Random(SEED)

    class FakeInstance:
        def __init__(self, tag):
            self.tag = tag

    insts = [None, FakeInstance("a"), FakeInstance("b"), object()]

    boundary = [0, 1, -1, 2, 7, 10, 255, 256,
                2 ** 31 - 1, 2 ** 31, 2 ** 63 - 1, -(2 ** 63),
                10 ** 18, -(10 ** 18)]

    def check(value, inst):
        s = shadow_hash(value, inst)
        o = oracle(value, inst)
        if s != o:
            print(json.dumps({"status": "fail", "value": value,
                              "shadow": list(s) if s[1] is not None else s,
                              "oracle": list(o) if o[1] is not None else o}))
            return False
        return True

    checked = 0
    for value in boundary:
        for inst in insts:
            if not check(value, inst):
                return 1
            checked += 1

    for _ in range(N):
        value = rng.randint(-(10 ** 15), 10 ** 15)
        inst = rng.choice(insts)
        if not check(value, inst):
            return 1
        checked += 1

    print(json.dumps({"status": "ok", "checked": checked, "disagreements": 0}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
