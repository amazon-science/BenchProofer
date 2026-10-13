#!/usr/bin/env python3
"""G-CONF for django__django-11211.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_normalizeKey` (the Lean impl, transliterated
op-for-op per refinement.md — INCLUDING the deep model `decodeHex` of the
text->identifier decode, NOT the real callee) against the REAL patched
`UUIDField.get_prep_value` over >=1e5 fuzzed values. Zero disagreements => exit 0.

Model (refinement.md): preparing a key value composes two steps —
  op 1 (I + A-reference): the base pass-through `Field.get_prep_value` (identity
        for an ordinary value);
  op 2 (R + A-reference): the canonicalising conversion `UUIDField.to_python`,
        modeled deeply as `canonicalValue` / `decodeHex` (accumulate the hex
        digits of a text spelling, ignoring separators) = `uuid.UUID(hex=s).int`.

  * Oracle = the REAL patched `UUIDField().get_prep_value(value)` (a uuid.UUID,
             or None), compared by `.int` / None.
  * Shadow = the Lean model: `canonicalValue(basePrep(value))`, where
             `decodeHex` is reimplemented from the Lean source (it does NOT call
             the real `to_python`). This makes G-CONF genuinely validate the
             deep model against Python, not compare Python to itself.

Modeled domain (mapping.md): the prefetch use case stores `object_pk =
str(related.pk)`, i.e. the canonical hyphenated spelling. The deep model is faithful
to `uuid.UUID(hex=s).int` for the spellings that contain ONLY hex digits and the
standard separators `- { }` (hyphenated, bare 32-hex, upper-cased, brace-wrapped).
The `urn:uuid:` spellings are OUT of the modeled domain (their literal letters
include hex digits, which a digits-only decode cannot model) and are not fuzzed.
stdlib-only; no hypothesis required.
"""
import os
import random
import sys
import uuid

# --- configure Django settings before importing field machinery --------------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
        USE_I18N=False,
    )
    django.setup()

from django.db.models.fields import UUIDField

FIELD = UUIDField()


# ---- the Lean deep model, transliterated from Solution.lean ------------------

def hex_val(c):
    """`hexVal?`: hex value of a single character, or None."""
    n = ord(c)
    if 48 <= n <= 57:
        return n - 48
    if 97 <= n <= 102:
        return n - 97 + 10
    if 65 <= n <= 70:
        return n - 65 + 10
    return None


def decode_hex(s):
    """`decodeHex`: accumulate hex digits left-to-right, ignoring separators."""
    acc = 0
    for c in s:
        d = hex_val(c)
        if d is not None:
            acc = acc * 16 + d
    return acc


def base_prep(v):
    """`basePrep`: identity."""
    return v


def canonical_value(v):
    """`canonicalValue` over the (None | uuid.UUID | str) carrier.

    Returns the canonical identifier as an int (the uuid.int), or None."""
    if v is None:
        return None
    if isinstance(v, uuid.UUID):
        return v.int
    return decode_hex(v)            # a text spelling


def shadow(value):
    """R/I transliteration of implementation_normalizeKey (the Lean model)."""
    return canonical_value(base_prep(value))


def oracle_int(value):
    """REAL patched UUIDField.get_prep_value, normalized to an int / None."""
    r = FIELD.get_prep_value(value)
    if r is None:
        return None
    return r.int if isinstance(r, uuid.UUID) else r


# ---- fuzzing over the modeled domain -----------------------------------------

def spellings(u):
    """str spellings of `u` that the deep model is faithful to (no urn forms)."""
    return [
        str(u),            # canonical hyphenated (what prefetch stores)
        u.hex,             # bare 32-hex
        str(u).upper(),    # upper-cased hyphenated
        u.hex.upper(),     # upper-cased bare
        "{%s}" % str(u),   # brace-wrapped
    ]


def gen_value(rng):
    boundary = [uuid.UUID(int=0), uuid.UUID(int=(1 << 128) - 1)]
    r = rng.random()
    if r < 0.05:
        return None
    u = rng.choice(boundary) if rng.random() < 0.1 else uuid.UUID(int=rng.getrandbits(128))
    if rng.random() < 0.35:
        return u                          # already a uuid.UUID object
    return rng.choice(spellings(u))       # a faithful text spelling


def main():
    rng = random.Random(11211)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        value = gen_value(rng)
        o = oracle_int(value)
        s = shadow(value)
        if o != s:
            disagreements += 1
            if first is None:
                first = (repr(value), repr(o), repr(s))
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements (deep model vs real get_prep_value)" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
