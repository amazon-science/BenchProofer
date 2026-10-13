#!/usr/bin/env python3
"""G-AX for django__django-14915 — validate the A-reference op against the REAL
repo callee in-container.

refinement.md op #1 routes the choice-value wrapper's digest through the standard
builtin digest of the wrapped value: post-patch,

    ModelChoiceIteratorValue.__hash__(self) == hash(self.value)

The Lean model encodes exactly this — the wrapper's digest is `valueHash m.val`
(the value's own digest), with NO dependence on the accompanying model object
`m.inst`. `valueHash` is the unchanged callee (builtin `hash` on the value).

This script runs the REAL post-patch `ModelChoiceIteratorValue` against boundary
+ fuzz inputs and asserts, for every input:

  (A) the wrapper IS hashable — `hash(obj)` succeeds (does not raise TypeError);
  (B) ROUTING: `hash(obj) == hash(value)` — the wrapper's digest is exactly the
      wrapped value's own digest (the `valueHash m.val` model);
  (C) FRAME: the digest is independent of the accompanying model object —
      `hash(ModelChoiceIteratorValue(value, inst_a)) ==
       hash(ModelChoiceIteratorValue(value, inst_b))` for any two model objects
      (including `None`), since both equal `hash(value)`.

stdlib + django only; exit 0 iff every observation meets the modeled property.
The exact numeric value of `hash(int)` is a CPython detail and is NOT pinned —
only the routing/frame equalities are.
"""
import json
import os
import random
import subprocess
import sys

SEED = 14915
N = 50_000


def _ensure_patched():
    """Git-apply the bundle's gold patch to /testbed if it is not already
    applied, so the imported `django.forms.models` is the FIXED code this check
    validates (post-patch `ModelChoiceIteratorValue.__hash__`).

    G-AX does NOT git-apply the gold patch to /testbed (unlike G-CONF), so this
    check applies the mounted gold patch (`/work/patch.diff`) itself. The harness
    runs the frozen instance image, so /testbed is either exactly the unpatched
    base_commit or exactly the gold-patched tree; both directions are checked so
    a drifted tree errors loudly instead of validating against the wrong source.
    Without this, the pre-patch class defines `__eq__` without `__hash__`, so
    Python sets `__hash__ = None` and `hash(obj)` raises TypeError — the exact
    bug under specification — which would spuriously fail this check."""
    patch = "/work/patch.diff"
    testbed = "/testbed"
    if not (os.path.isfile(patch) and os.path.isdir(testbed)):
        return  # not in the harness layout; assume caller arranged the fix

    def _check(*extra):
        return subprocess.run(["git", "apply", "--check", *extra, patch],
                              cwd=testbed, capture_output=True).returncode == 0

    forward = _check()               # patch applies cleanly => tree is unpatched
    reverse = _check("--reverse")    # reverse applies cleanly => tree is patched
    if forward and not reverse:
        subprocess.run(["git", "apply", patch], cwd=testbed, check=True,
                       capture_output=True)
    elif reverse and not forward:
        return                       # already gold-patched: no-op
    else:
        raise SystemExit(
            f"G-AX ERROR: unexpected /testbed state (forward={forward}, "
            f"reverse={reverse}); cannot establish gold-patched reference")


_ensure_patched()


def main() -> int:
    # `django.forms.models` pulls in the settings machinery at import time.
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
    except Exception as e:  # pragma: no cover - settings best effort
        # Settings may already be configured by the harness; only fail if the
        # callee itself cannot be imported (handled below).
        pass

    try:
        from django.forms.models import ModelChoiceIteratorValue
    except Exception as e:
        print(json.dumps({"status": "error",
                          "reason": f"cannot import django callee: {e!r}"}))
        return 1

    rng = random.Random(SEED)

    # Distinct sentinel "model objects" — any object works; the digest must not
    # read them. `None` is the case the F2P test exercises.
    class FakeInstance:
        def __init__(self, tag):
            self.tag = tag

    def instances():
        yield None
        yield FakeInstance("a")
        yield FakeInstance("b")
        yield object()

    # Boundary + fuzzed wrapped values (model pks are ints in practice; include
    # 0, negatives, and large magnitudes).
    boundary = [0, 1, -1, 2, 7, 10, 255, 256,
                2 ** 31 - 1, 2 ** 31, 2 ** 63 - 1, -(2 ** 63),
                10 ** 18, -(10 ** 18)]
    values = list(boundary) + [rng.randint(-(10 ** 12), 10 ** 12) for _ in range(N)]

    for value in values:
        digests = []
        for inst in instances():
            obj = ModelChoiceIteratorValue(value, inst)
            # (A) hashable
            try:
                h = hash(obj)
            except TypeError as e:
                print(json.dumps({"status": "fail", "kind": "unhashable",
                                  "value": value, "reason": repr(e)}))
                return 1
            # (B) routing: digest equals the wrapped value's own digest
            if h != hash(value):
                print(json.dumps({"status": "fail", "kind": "routing",
                                  "value": value, "got": h,
                                  "expected": hash(value)}))
                return 1
            digests.append(h)
        # (C) frame: digest independent of the accompanying model object
        if len(set(digests)) != 1:
            print(json.dumps({"status": "fail", "kind": "frame",
                              "value": value, "digests": digests}))
            return 1

    print(json.dumps({"status": "ok", "checked_values": len(values),
                      "property": "hash(wrapper)==hash(value), independent of instance"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
