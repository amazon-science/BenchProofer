#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12308.

The bundle has NO consumed axiom. The display choice for a JSON-typed value
(`jsonDisplay` in Solution.lean) is modeled DEEPLY over three observable facts
of the rendered value, each produced by a callee the patch does NOT change:

  (A-reference) `present`  == the real Python truthiness `bool(value)`.
  (A-reference) `prep`     == the real `JSONField().get_prep_value(value)`
                             outcome: `json(text)` on success, `unserializable`
                             iff it raises `TypeError`.
  (A-reference) `generic`  == the real `display_for_value(value, empty)`.

This script runs the REAL Django callees (in the prebuilt SWE-Bench instance
image, at base_commit) on boundary + fuzz values and asserts the deep model's
field encodings match every observation. Exit 0 iff every obligation holds.

The deep model under check (lock-step with Solution.lean `jsonDisplay`):

    present := bool(value)
    prep    := json(json.dumps(value))   on success
             | unserializable            on TypeError
    generic := display_for_value(value, empty)
    display := text       if present and prep == json(text)
             | generic    if present and prep == unserializable
             | generic    if not present
"""
import json
import random
import sys


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


# --- the deep model (kept in lock-step with Solution.lean jsonDisplay) -------

_UNSERIALIZABLE = object()  # marker == PrepResult.unserializable


def model_present(value):
    return bool(value)


def model_prep(value):
    """PrepResult: the JSON text, or the unserializable marker."""
    try:
        return json.dumps(value)            # default encoder, == get_prep_value
    except TypeError:
        return _UNSERIALIZABLE


def model_json_display(present, prep, generic):
    """jsonDisplay: choose among the three observed facts."""
    if present:
        if prep is _UNSERIALIZABLE:
            return generic
        return prep
    return generic


# --- the checks: model field == real callee ---------------------------------

def check_value(value, empty, JSONField, display_for_value):
    field = JSONField()
    present = bool(value)
    m_prep = model_prep(value)

    # (A-reference) prep == real get_prep_value outcome.
    # The JSON arm consults `prep` ONLY when `present` (the `and value` guard,
    # mapping.md §2), so the model only ever reads `prep` for a truthy value;
    # that is the only case in which `prep` must match the real callee. (Real
    # `get_prep_value` short-circuits `None` to `None` before `json.dumps`, but
    # `None` is falsy and never reaches the arm — so the divergence is
    # unobservable. We still assert it for every truthy value.)
    if present:
        try:
            real_prep = field.get_prep_value(value)
            real_prep_raised = False
        except TypeError:
            real_prep = None
            real_prep_raised = True
        if real_prep_raised:
            assert m_prep is _UNSERIALIZABLE, (
                "prep unsound on %r: real get_prep_value raised TypeError, "
                "model gives %r" % (value, m_prep))
        else:
            assert m_prep is not _UNSERIALIZABLE and m_prep == real_prep, (
                "prep unsound on %r: real get_prep_value=%r, model=%r"
                % (value, real_prep, m_prep))

    # (A-reference) generic == real display_for_value
    real_generic = display_for_value(value, empty)
    m_generic = real_generic  # generic field IS the callee's value (identity)

    # (A-reference) present == real bool(value)
    assert model_present(value) == bool(value), (
        "present unsound on %r" % (value,))

    return model_json_display(model_present(value), m_prep, m_generic)


def main():
    _configure_django()
    from django.db import models
    from django.contrib.admin.utils import display_for_value

    empty = "-"

    boundary = [
        {"a": {"b": "c"}},
        ["a", "b"],
        "a",
        {("a", "b"): "c"},     # invalid JSON -> TypeError -> unserializable
        None,
        {},                    # falsy -> present False
        [],
        "",
        0,
        0.0,
        False,
        True,
        {"foo": "bar"},
        [1, 2, 3],
        {"n": 1, "x": None, "b": True},
        "Joe's",
        '{"already": "json"}',
        {("k",): {("j",): 1}},  # nested non-serializable
        [("t", "u")],           # list with tuple element (serializable -> list)
        {"unicode": "café •"},
    ]
    for v in boundary:
        check_value(v, empty, models.JSONField, display_for_value)

    # randomized fuzz: mix of serializable JSON values and non-serializable ones
    rng = random.Random(12308)

    def rand_value(depth=0):
        kinds = ["str", "int", "float", "bool", "none", "list", "dict"]
        if depth >= 3:
            kinds = ["str", "int", "float", "bool", "none"]
        k = rng.choice(kinds + ["tuplekey", "tupleval"])  # bias toward errors
        if k == "str":
            n = rng.randint(0, 6)
            return "".join(rng.choice("ab cd'\"{}[]:,é•") for _ in range(n))
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
            return {("t", "u"): rand_value(depth + 1)}   # non-serializable key
        if k == "tupleval":
            return rng.choice([("x", "y"), {1, 2}])       # tuple/set value
        return None

    n_fuzz = 20000
    seen_ser = seen_unser = 0
    for _ in range(n_fuzz):
        v = rand_value()
        check_value(v, empty, models.JSONField, display_for_value)
        if model_prep(v) is _UNSERIALIZABLE:
            seen_unser += 1
        else:
            seen_ser += 1

    print("G-AX OK: deep-model fields present/prep/generic sound against real "
          "bool / JSONField.get_prep_value / display_for_value on %d boundary + "
          "%d fuzz values (%d serializable, %d unserializable); no consumed "
          "axioms." % (len(boundary), n_fuzz, seen_ser, seen_unser))
    return 0


if __name__ == "__main__":
    sys.exit(main())
