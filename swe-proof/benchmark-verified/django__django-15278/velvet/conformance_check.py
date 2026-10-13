#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-15278 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of `requiresTableRebuild`'s
impl: the modeled decision

    isUnique || !acceptsNull || hasServerDefault

where `isUnique` is the column's EFFECTIVE uniqueness observation — the repo's
`field.unique` PROPERTY, which is defined as

    @property
    def unique(self):
        return self._unique or self.primary_key
    (django/db/models/fields/__init__.py:753 @ base_commit)

REFINEMENT STRUCTURE:
  - `effective_default(field) is not None` is an UNCHANGED callee, observed only
    as the boolean `hasServerDefault` ("a usable server-side default is
    present"). The spec asserts nothing about its value, so it is a FREE INPUT
    here — we fuzz it over {True, False}. (A-consumed / opaque; nothing for
    G-AX to validate — no axiom_check.py.)
  - The gold `if` condition reads FOUR operands (`field.primary_key`,
    `field.unique`, `field.null`, the `is not None` test), but `field.unique`
    is the property above, so `field.primary_key or field.unique` collapses to
    `field.unique` — the `primary_key` disjunct is redundant in the real repo.
    The model therefore observes the single effective boolean `isUnique`
    (= the `field.unique` property value). This R-leg (the property collapse)
    is exactly what this check refutes: we drive the RAW underlying state
    (primary_key flag, stored _unique flag, null flag, default-present) over
    the full 2^4 cube and compare the gold condition verbatim against the
    model's decision computed from the derived effective observations.

ORACLE: the patched `if` condition transliterated verbatim from
  django/db/backends/sqlite3/schema.py (SQLiteSchemaEditor.add_field, gold):
      field.primary_key or field.unique or
      not field.null or self.effective_default(field) is not None
  with `field.unique` expanded to its property definition
  `_unique or primary_key` and the opaque callee test represented by the free
  boolean `has_server_default`.

SHADOW: Solution.lean's `requiresTableRebuild` post-image transliterated:
      is_unique or (not accepts_null) or has_server_default
  applied to the derived effective observations
      is_unique = _unique or primary_key   (the `field.unique` property)
      accepts_null = null flag
      has_server_default = free boolean.

We differential-test SHADOW vs ORACLE over all 2^4 = 16 raw combinations
plus seeded fuzz. Exit 0 iff zero disagreements. stdlib only.
"""
import itertools
import random
import sys

SEED = 15278
N_FUZZ = 100_000


def unique_property(underlying_unique, primary_key):
    """Field.unique transliterated verbatim
    (django/db/models/fields/__init__.py:753):
        return self._unique or self.primary_key"""
    return underlying_unique or primary_key


def shadow(primary_key, underlying_unique, accepts_null, has_server_default):
    """requiresTableRebuild transliterated:
        isUnique || !acceptsNull || hasServerDefault
    fed the derived effective observation isUnique = field.unique (property)."""
    is_unique = unique_property(underlying_unique, primary_key)
    return is_unique or (not accepts_null) or has_server_default


def oracle(primary_key, underlying_unique, accepts_null, has_server_default):
    """The patched `if` condition, transliterated verbatim:
        field.primary_key or field.unique or
        not field.null or self.effective_default(field) is not None
    `field.unique` is the property `_unique or primary_key`; `accepts_null`
    stands for `field.null` (so `not field.null` ↔ `not accepts_null`);
    `has_server_default` stands for the boolean
    `self.effective_default(field) is not None`."""
    field_unique = unique_property(underlying_unique, primary_key)
    return (primary_key or field_unique
            or not accepts_null or has_server_default)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    # Exhaustive: all 2^4 = 16 raw boolean combinations
    # (primary_key, _unique, null, default-present).
    combos = list(itertools.product([False, True], repeat=4))
    # Plus seeded fuzz over the same raw boolean cube.
    combos += [tuple(rng.random() < 0.5 for _ in range(4)) for _ in range(N_FUZZ)]

    for pk, uniq, null, dflt in combos:
        count += 1
        s = bool(shadow(pk, uniq, null, dflt))
        o = bool(oracle(pk, uniq, null, dflt))
        if s != o:
            disagreements.append((pk, uniq, null, dflt, s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d disagreement(s) "
              "(primary_key, underlying_unique, accepts_null, "
              "has_server_default, shadow, oracle): %r"
              % (len(disagreements), disagreements))
        return 1
    print("G-CONF OK: R/I shadow of requiresTableRebuild agrees with the "
          "patched decision condition on %d raw inputs (16 exhaustive + fuzz, "
          "seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
