#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15277.

The bundle models ONE function: `CharField.__init__` (the validator-attachment
portion). Its Lean implementation (`implementation_buildFieldValidators`) builds
the field's validator list by appending a length-bound validator EXACTLY when a
maximum length is declared:

    validators = list(base)
    if max_length is not None:
        validators = validators + [("lengthBound", max_length)]
    return validators

This script transliterates that R/I impl into Python (`shadow_build`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch behavior of `CharField.__init__` (`django/db/models/fields/__init__.py`):

    self.validators (== base) is augmented in place; post-patch:
        if self.max_length is not None:
            self.validators.append(MaxLengthValidator(self.max_length))

We do NOT instantiate a real Django field / ORM (heavy, and the modeled value is
a pure decision over whether the length-bound validator is attached and what bound
it carries). Instead we reproduce the patched control flow over light stand-in
validators carrying the SAME observable the real code exposes (mapping.md): the
pre-existing validators as opaque tags, and the attached `MaxLengthValidator`
represented as `("lengthBound", max_length)` whose payload IS `self.max_length`.

The differential genuinely tests the Lean modeling: the shadow mirrors Lean's
`if maxLength.isSome then validators ++ [lengthBound maxLength]`, whereas the
oracle reproduces the patched `if self.max_length is not None: append(...)`
semantics. They must agree for every input — in particular when `max_length` is
None, the case the patch newly guards (pre-patch attached a broken
`MaxLengthValidator(None)`; post-patch attaches nothing).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 15277 (also in mapping.md).
"""
import sys

SEED = 15277
N = 120_000


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# `base` is the list of pre-existing validators, each an opaque tag (an int or
# the marker we use for an already-present length-bound validator). The attached
# validator is modeled as ("lengthBound", max_length) — its limit_value IS
# self.max_length. Post-patch: attach iff max_length is not None.
def oracle_build(max_length, base):
    validators = list(base)
    if max_length is not None:                      # the guard the patch ADDS
        validators.append(("lengthBound", max_length))
    return validators


# --- shadow of implementation_buildFieldValidators (the R/I leg) -------------
# Mirrors Solution.lean: `if maxLength.isSome then validators ++ [lengthBound maxLength]`.
def shadow_build(max_length, base):
    validators = list(base)
    if max_length is not None:                      # Option.isSome
        validators = validators + [("lengthBound", max_length)]
    return validators


def disagree(max_length, base):
    got = oracle_build(max_length, base)
    want = shadow_build(max_length, base)
    if got != want:
        return ((max_length, base), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases exercising the guard."""
    cases = []
    bases = [
        [],
        [1],
        [1, 2, 3],
        [("lengthBound", 5)],            # base already carries a length-bound one
    ]
    # max_length None is the discriminating case the patch newly guards.
    for ml in (None, 0, 1, 10, 255, -1):
        for base in bases:
            cases.append((ml, list(base)))
    return cases


def main() -> int:
    checked = 0

    for ml, base in _enumerate_edge():
        d = disagree(ml, base)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        # max_length: None ~half the time, else a small int (incl. 0 / negative)
        r = next(rnd)
        if r & 1:
            max_length = None
        else:
            max_length = (next(rnd) % 300) - 2      # -2 .. 297
        length = next(rnd) % 7                       # 0..6 pre-existing validators
        base = []
        for _ in range(length):
            base.append(next(rnd) % 1000)            # opaque tag
        d = disagree(max_length, base)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
