#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-11880.

The bundle models ONE function: `Field.__deepcopy__` (`django/forms/fields.py`).
Its Lean implementation (`implementation_duplicateField`) builds a duplicate of
a form field starting from a shallow copy, then replaces each mutable container
(widget, error-message mapping, validator list) with a freshly allocated object
that carries the same contents:

    result = shallow_copy(self)
    result.widget        = fresh(fw)                         # deepcopy(widget)
    result.error_messages = (fresh(fe), self.error_messages) # dict.copy()  <-- fix
    result.validators     = (fresh(fv), self.validators)     # list[:]
    return result

This script transliterates that R/I impl into Python (`shadow_deepcopy`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH `__deepcopy__`, run on REAL Python objects so that object identity
(`is` / `id()`) is exercised exactly as the F2P test exercises it
(`assertIsNot(field_copy.error_messages, field.error_messages)`).

We do NOT stand up Django (heavy, and the modeled value is a pure
identity/contents decision over the field's mutable containers). Instead we use
a light stand-in `Field` object whose touched attributes are a widget object, an
`error_messages` dict, a `validators` list, and an immutable scalar `required`.
The oracle runs the patched `__deepcopy__` body verbatim; the shadow reproduces
the Lean modeling (fresh identities `fw`/`fe`/`fv` + preserved contents). Both
legs are compared on the full observable tuple:

  * identity of result.widget / error_messages / validators is FRESH
    (`is not` the original's, and `is not` self when distinct), and
  * contents of error_messages / validators EQUAL the original's, and
  * the immutable scalar is preserved.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 11880 (also in
mapping.md).
"""
import copy
import sys

SEED = 11880
N = 120_000


# --- light stand-in for django.forms.Field, touched attributes only ----------
class StubField:
    def __init__(self, widget, error_messages, validators, required):
        self.widget = widget                 # an object (deep-copied)
        self.error_messages = error_messages  # a dict (the fix: .copy())
        self.validators = validators          # a list ([:])
        self.required = required              # an immutable scalar (carried)

    # ORACLE: the POST-PATCH __deepcopy__ body, verbatim.
    def __deepcopy__(self, memo):
        result = copy.copy(self)                              # shallow copy
        memo[id(self)] = result
        result.widget = copy.deepcopy(self.widget, memo)      # deepcopy widget
        result.error_messages = self.error_messages.copy()    # <-- the fix line
        result.validators = self.validators[:]                # list slice
        return result


class Widget:
    """A trivial deep-copyable widget object (only its identity matters)."""
    def __init__(self, tag):
        self.tag = tag

    def __deepcopy__(self, memo):
        new = Widget(self.tag)
        memo[id(self)] = new
        return new


def oracle_observe(field):
    """Run the post-patch __deepcopy__ and return the observable tuple."""
    cp = copy.deepcopy(field)
    return (
        cp.widget is not field.widget,
        cp.error_messages is not field.error_messages,
        cp.validators is not field.validators,
        dict(cp.error_messages) == dict(field.error_messages),
        list(cp.validators) == list(field.validators),
        cp.required == field.required,
    )


# --- shadow of implementation_duplicateField (the R/I leg) -------------------
# Mirrors Solution.lean: start from a shallow copy (shared identities), then
# rebind widget/error_messages/validators each to a FRESH object carrying the
# same contents. We materialise fresh objects so `is`/`==` observe the same
# facts the Lean ObjId/contents model asserts.
def shadow_observe(field):
    result = copy.copy(field)                  # let mut result := self
    result.widget = Widget(field.widget.tag)   # fresh widget identity fw
    result.error_messages = dict(field.error_messages)  # fresh dict, same contents
    result.validators = list(field.validators)          # fresh list, same contents
    # result.required left as carried by the shallow copy
    return (
        result.widget is not field.widget,
        result.error_messages is not field.error_messages,
        result.validators is not field.validators,
        dict(result.error_messages) == dict(field.error_messages),
        list(result.validators) == list(field.validators),
        result.required == field.required,
    )


def disagree(field):
    got = oracle_observe(field)
    want = shadow_observe(field)
    if got != want:
        return (got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases pinning the identity/contents observations."""
    return [
        # the F2P case: a single custom 'invalid' error message
        StubField(Widget("text"), {"invalid": "Form custom error message."}, [], True),
        # empty error_messages dict
        StubField(Widget("text"), {}, [], True),
        # several error codes
        StubField(Widget("sel"), {"required": "r", "invalid": "i", "max": "m"}, [1, 2], False),
        # non-empty validators
        StubField(Widget("num"), {"required": "r"}, [10, 20, 30], True),
        # required False
        StubField(Widget("hid"), {"invalid": "x"}, [7], False),
    ]


def _rand_field(rnd):
    n_msg = next(rnd) % 4
    msgs = {}
    for _ in range(n_msg):
        code = next(rnd) % 6
        msg = next(rnd) % 100
        msgs[f"code{code}"] = f"msg{msg}"
    n_val = next(rnd) % 4
    vals = [next(rnd) % 50 for _ in range(n_val)]
    required = bool(next(rnd) % 2)
    tag = f"w{next(rnd) % 5}"
    return StubField(Widget(tag), msgs, vals, required)


def main() -> int:
    checked = 0

    for field in _enumerate_edge():
        d = disagree(field)
        if d:
            print(f"DISAGREE edge: oracle={d[0]} shadow={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        field = _rand_field(rnd)
        d = disagree(field)
        if d:
            print(f"DISAGREE fuzz: oracle={d[0]} shadow={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
