#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16801.

The bundle models ONE function: the decision, taken when a model class is set
up, of whether to install the post-initialization handler that keeps an image
field's associated width/height attributes in sync
(`ImageField.contribute_to_class`, `django/db/models/fields/files.py`).

Its Lean implementation (`implementation_connectPostInit`) returns a `Bool`:

    if (not is_abstract) and (truthy(width_field) or truthy(height_field)):
        return True
    return False

where `truthy(name)` is "name present and non-empty".

This script transliterates that R/I impl into Python (`shadow_connect`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH guard in `contribute_to_class` —

    not cls._meta.abstract and (self.width_field or self.height_field)

We do NOT stand up Django's model/signal machinery (heavy; the modeled value is
a pure boolean decision over three already-available facts). Both legs are total
functions over the modeled abstraction, so the edge set EXHAUSTIVELY enumerates
the modeled input space (abstract flag × width-field {absent, empty, set} ×
height-field {absent, empty, set}); the fuzz loop additionally samples random
points over a wider name alphabet. The discriminating case — a concrete model
with neither dimension attribute set — is covered exhaustively: oracle
(post-patch) returns False, while the pre-patch code installs the handler (True).

stdlib-only. Pinned seed: 16801 (also recorded in mapping.md).
"""
import itertools
import sys

SEED = 16801
N = 120_000

# Modeled values for an optional attribute name: absent (None), present-empty
# (falsy in Python, mirrors `self.width_field` being ""), present-nonempty.
NAMES = (None, "", "w", "Width")


def truthy(name):
    # Python truthiness of an optional identifier string: None and "" are falsy.
    return bool(name)


# --- ORACLE: the post-patch contribute_to_class guard, faithful replica -------
def oracle_connect(is_abstract, width_field, height_field):
    return (not is_abstract) and (truthy(width_field) or truthy(height_field))


# --- shadow of implementation_connectPostInit (the R/I leg) -------------------
# Mirrors Solution.lean op-for-op.
def shadow_connect(is_abstract, width_field, height_field):
    if (not is_abstract) and (truthy(width_field) or truthy(height_field)):
        return True
    return False


def disagree(is_abstract, width_field, height_field):
    got = oracle_connect(is_abstract, width_field, height_field)
    want = shadow_connect(is_abstract, width_field, height_field)
    if bool(got) != bool(want):
        return (is_abstract, width_field, height_field, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # Edge set = EXHAUSTIVE over the modeled abstraction.
    for is_abstract, wf, hf in itertools.product((False, True), NAMES, NAMES):
        d = disagree(is_abstract, wf, hf)
        if d:
            print(f"DISAGREE exhaustive abstract={d[0]!r} width={d[1]!r} "
                  f"height={d[2]!r}: oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    # Redundant random fuzz over a wider name alphabet.
    rnd = _lcg(SEED)
    alpha = (None, "", "w", "h", "Width", "HEIGHT", "x")
    bools = (False, True)
    for _ in range(N):
        def pick(seq):
            return seq[next(rnd) % len(seq)]
        d = disagree(pick(bools), pick(alpha), pick(alpha))
        if d:
            print(f"DISAGREE fuzz abstract={d[0]!r} width={d[1]!r} "
                  f"height={d[2]!r}: oracle={d[3]} shadow={d[4]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
