#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12308.

The bundle models ONE decision `display_for_field` makes for a JSON-valued
field (mapping.md): which textual rendering is selected for the field's stored
`value`, given the placeholder text `empty_value_display`.

Standing up Django's admin + a real `JSONField` + locale machinery to drive
`display_for_field` is heavy and unnecessary: for a JSON field the decision is
the pure dispatch

    if value is None:                       # earlier cascade test
        return empty
    elif value:                             # the new `and value` guard
        try:
            return json.dumps(value)        # field.get_prep_value
        except TypeError:
            return display_for_value(value, empty)
    else:                                   # present but empty -> final else
        return display_for_value(value, empty)

The two LEAF operations are UNCHANGED callees (A-reference): the JSON serializer
(`field.get_prep_value`, i.e. `json.dumps(value, cls=encoder)`) and the generic
renderer (`display_for_value`). They are left as the REAL operations and shared
by BOTH legs of the differential, so this genuinely tests the DISPATCH — that
`implementation_displayForField`'s control flow matches the patched cascade —
which is the modeled (R / A-reference / I) content.

  * ORACLE  = the patched `display_for_field` JSON branch (above).
  * SHADOW  = op-for-op transliteration of `implementation_displayForField`
              (per refinement.md), using the SAME leaf operations.

Both are exercised over discrete edge cases + >=1e5 fuzzed values, including
values `json.dumps` rejects (dicts keyed by a tuple) to drive the TypeError /
`.error` fall-back arm. Strings compared directly.

stdlib-only. Pinned seed: 20240627 (also in mapping.md).
"""
import json
import random
import sys

SEED = 20240627
N = 120_000


# --- shared LEAF operations (UNCHANGED callees; A-reference) ------------------
def json_serialize(value):
    """field.get_prep_value(value) == json.dumps(value, cls=encoder).
    Returns ('ok', s) on success, ('error', None) on a TypeError (value not
    representable as JSON) -- the Except Unit String bijection."""
    try:
        return ("ok", json.dumps(value))
    except TypeError:
        return ("error", None)


def display_for_value(value, empty):
    """Faithful replica of django.contrib.admin.utils.display_for_value for the
    value classes a JSON field can hold (locale/number formatting elided -- it
    is the SAME function on both legs, so the dispatch test is unaffected)."""
    if value is None:
        return empty
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (list, tuple)):
        return ', '.join(str(v) for v in value)
    if isinstance(value, int):
        return str(value)
    return str(value)


# --- ORACLE: the patched display_for_field decision for a JSON field ----------
def oracle(value, empty):
    if value is None:
        return empty
    if value:                                  # the `and value` truthiness guard
        try:
            return json.dumps(value)           # field.get_prep_value
        except TypeError:
            return display_for_value(value, empty)
    return display_for_value(value, empty)


# --- SHADOW of implementation_displayForField (R / I / A-reference legs) -------
# Mirrors Solution.lean:
#   if isNull value: return empty
#   if truthy value:
#       match jsonSerialize value with .ok s => s | .error _ => genericDisplay …
#   return genericDisplay value empty
def is_null(value):
    return value is None


def truthy(value):
    return bool(value)


def shadow(value, empty):
    if is_null(value):
        return empty
    if truthy(value):
        kind, s = json_serialize(value)
        if kind == "ok":
            return s
        return display_for_value(value, empty)
    return display_for_value(value, empty)


# --- value generation ---------------------------------------------------------
def gen_scalar(rng, depth):
    pick = rng.randint(0, 6)
    if pick == 0:
        return None
    if pick == 1:
        return rng.choice([True, False])
    if pick == 2:
        return rng.choice([rng.randint(-1000, 1000),
                           rng.choice([0.0, -1.5, 2.5, 3.14])])
    if pick == 3:
        return rng.choice(["", "a", "foo", "bar", "hello world", "0", "false"])
    if pick == 4 and depth < 3:
        return [gen_value(rng, depth + 1) for _ in range(rng.randint(0, 3))]
    if pick == 5 and depth < 3:
        return tuple(gen_value(rng, depth + 1) for _ in range(rng.randint(0, 3)))
    return gen_value(rng, depth + 1) if depth < 3 else 0


def gen_value(rng, depth=0):
    r = rng.random()
    if r < 0.30:
        return gen_scalar(rng, depth)
    if r < 0.55:
        return [gen_scalar(rng, depth + 1) for _ in range(rng.randint(0, 4))]
    if r < 0.70:
        return tuple(gen_scalar(rng, depth + 1) for _ in range(rng.randint(0, 4)))
    if r < 0.90:
        # JSON-serializable dict (string keys)
        return {rng.choice(["a", "b", "c", "x", "k"]): gen_scalar(rng, depth + 1)
                for _ in range(rng.randint(0, 4))}
    # JSON-UNrepresentable dict (tuple key) -> drives the TypeError / .error arm
    return {(rng.choice(["a", "b"]), rng.choice(["c", "d"])):
            rng.choice(["c", "v", 1, None]) for _ in range(rng.randint(1, 2))}


EMPTIES = ["-", "(none)", "", "—"]

DISCRETE = [
    ({"foo": "bar"}, "-"),
    ({"a": {"b": "c"}}, "-"),
    (["a", "b"], "-"),
    ("a", "-"),
    ({}, "-"),
    ([], "-"),
    ("", "-"),
    (0, "-"),
    (0.0, "-"),
    (2.5, "-"),
    (False, "-"),
    (True, "-"),
    (42, "-"),
    ({("a", "b"): "c"}, "-"),     # invalid JSON -> generic str(...)
    (None, "-"),
]


def main():
    rng = random.Random(SEED)
    mism = 0
    examples = []
    for value, empty in DISCRETE:
        o, s = oracle(value, empty), shadow(value, empty)
        if o != s:
            mism += 1
            if len(examples) < 10:
                examples.append((value, empty, o, s))
    for _ in range(N):
        value = gen_value(rng)
        empty = rng.choice(EMPTIES)
        o, s = oracle(value, empty), shadow(value, empty)
        if o != s:
            mism += 1
            if len(examples) < 10:
                examples.append((value, empty, o, s))
    total = len(DISCRETE) + N
    if mism:
        print(f"status=fail {mism}/{total} disagreements; examples:")
        for v, e, o, s in examples:
            print(f"  value={v!r} empty={e!r} oracle={o!r} shadow={s!r}")
        sys.exit(1)
    print(f"status=ok 0/{total} disagreements over discrete edge cases + "
          f"{N} fuzzed values (seed={SEED})")
    sys.exit(0)


if __name__ == "__main__":
    main()
