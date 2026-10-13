#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12308 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean `displayJson`/`jsonDisplay`'s branch ladder
              transliterated to Python (the if-ladder + match over the three
              observable facts of the value). The facts are bridged via the
              mapping.md §2/§3 bijection; the deeply-modeled callees
              (`get_prep_value`, `display_for_value`, `bool`) are NOT replaced by
              a model here — the shadow calls the REAL repo callees for them, so
              G-CONF isolates the R/I branch-selection legs (A-reference callee
              soundness stays with G-AX).
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `django.contrib.admin.utils.display_for_field(value,
              models.JSONField(), empty)` at base_commit (the real correctness
              oracle, G-RESOLVE).

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), Django + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import json
import random
import sys

SEED = 12308
N_FUZZ = 100_000


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={},
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            USE_TZ=False,
        )
    django.setup()


def shadow_display(value, empty, JSONField, display_for_value):
    """jsonDisplay transliterated to Python. The three observable facts come
    from the REAL callees (mapping.md §2/§3); the branch SELECTION is the R/I
    content this gate checks."""
    field = JSONField()
    present = bool(value)                              # ValueView.present
    # ValueView.prep: json(text) on success, unserializable on TypeError
    try:
        prep_text = field.get_prep_value(value)        # == json.dumps(value)
        prep_ok = True
    except TypeError:
        prep_text = None
        prep_ok = False
    generic = display_for_value(value, empty)          # ValueView.generic
    # jsonDisplay's branch ladder:
    if present:
        if prep_ok:
            return prep_text
        return generic
    return generic


def oracle_display(value, empty, display_for_field, JSONField):
    """patch.diff's behaviour: the patched display_for_field on a JSONField."""
    return display_for_field(value, JSONField(), empty)


def fuzz_inputs(n, rng):
    # boundary cases first (incl. the F2P test matrix and null case)
    yield from [
        {"a": {"b": "c"}},
        ["a", "b"],
        "a",
        {("a", "b"): "c"},
        None,
        {},
        [],
        "",
        0,
        0.0,
        False,
        True,
        {"foo": "bar"},
        [1, 2, 3],
        "Joe's",
        '{"already": "json"}',
        {("k",): 1},
        [("t", "u")],
        {"unicode": "café •"},
        {"nested": {"deep": [1, {"x": None}]}},
    ]

    def rand_value(depth=0):
        kinds = ["str", "int", "float", "bool", "none", "list", "dict"]
        if depth >= 3:
            kinds = ["str", "int", "float", "bool", "none"]
        k = rng.choice(kinds + ["tuplekey", "tupleval"])
        if k == "str":
            m = rng.randint(0, 6)
            return "".join(rng.choice("ab cd'\"{}[]:,é•") for _ in range(m))
        if k == "int":
            return rng.randint(-5, 5)
        if k == "float":
            return rng.choice([0.0, 1.5, -2.25, 3.0])
        if k == "bool":
            return rng.choice([True, False])
        if k == "none":
            return None
        if k == "list":
            return [rand_value(depth + 1) for _ in range(rng.randint(0, 3))]
        if k == "dict":
            return {("s%d" % i): rand_value(depth + 1)
                    for i in range(rng.randint(0, 3))}
        if k == "tuplekey":
            return {("t", "u"): rand_value(depth + 1)}
        if k == "tupleval":
            return rng.choice([("x", "y"), {1, 2}])
        return None

    for _ in range(n):
        yield rand_value()


def main():
    _configure_django()
    from django.db import models
    from django.contrib.admin.utils import display_for_field, display_for_value

    empty = "-"
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for v in fuzz_inputs(N_FUZZ, rng):
        count += 1
        try:
            shadow = shadow_display(v, empty, models.JSONField, display_for_value)
        except Exception as e:
            shadow = "SHADOW-EXC:%r" % (e,)
        try:
            oracle = oracle_display(v, empty, display_for_field, models.JSONField)
        except Exception as e:
            oracle = "ORACLE-EXC:%r" % (e,)
        if shadow != oracle:
            disagreements.append((v, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, sh, orc in disagreements:
            print("  value=%r shadow=%r oracle=%r" % (v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of displayJson agrees with patch.diff behaviour "
          "on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
