#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13964.

The bundle models ONE behavior: the foreign-key key-value adoption decision
inside `Model._prepare_related_fields_for_save` (`django/db/models/base.py`).
Its Lean implementation (`implementation_foreignKeyValueOnSave`) computes the
stored key value after the branch from the prior stored value `fkValue` and the
related object's primary key `objPk`:

    result = fkValue
    if fkValueIsEmpty(result):     # fkValue is None or fkValue == ""
        result = objPk             # adopt the related object's pk
    return result

This script transliterates that R/I impl into Python (`shadow_fk`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior. Post-patch, the guard is
`getattr(self, field.attname) in field.empty_values`, where
`field.empty_values == [None, '', [], (), {}]` (`validators.EMPTY_VALUES`). For a
scalar foreign-key key value the reachable members are `None` and the empty
string, so the membership test is exactly `value is None or value == ''`. The
oracle uses that real membership semantics over the modeled scalar domain — this
validates the Lean `fkValueIsEmpty` model.

We do NOT stand up Django's ORM (heavy; the modeled value is a pure scalar
decision). Both legs are total functions over the modeled abstraction. The edge
set EXHAUSTIVELY enumerates the modeled stored-value forms (`None` / empty string
/ non-empty strings) crossed with several primary-key values; the fuzz loop
additionally samples random points. The discriminating case — `fkValue == ""`
(empty string, the non-numeric/CharField-PK scenario) — is covered: the oracle
(post-patch) adopts `objPk`, while only treating `None` as empty (the PRE-patch
behavior) would disagree.

stdlib-only. Pinned seed: 13964 (also recorded in mapping.md).
"""
import sys

SEED = 13964
N = 120_000

# The real EMPTY_VALUES (django.core.validators.EMPTY_VALUES); a field's
# empty_values is list(EMPTY_VALUES). For a scalar FK key value only None and ""
# are reachable members.
EMPTY_VALUES = (None, "", [], (), {})

# Modeled stored-key-value forms (None or string scalars).
FK_VALUE_FORMS = (
    None,
    "",
    "jeff",
    "foo",
    "5",
    "0",
    " ",
    "abc def",
)
# Related object's primary key forms (always present / non-None in the modeled
# branch; the obj.pk is None case is a separate, unchanged behavior).
OBJ_PK_FORMS = (
    "jeff",
    "foo",
    "5",
    "x",
    " ",
)


def value_in_empty_values(v):
    # Real semantics of `v in field.empty_values` for a scalar key value.
    # `in` uses ==; None compares only equal to None; "" equals "".
    return any(v is e or v == e for e in EMPTY_VALUES if not isinstance(e, (list, tuple, dict)) or v == e)


# --- ORACLE: post-patch adoption decision -------------------------------------
def oracle_fk(fk_value, obj_pk):
    # result starts as the stored key value; adopt obj.pk when the stored value
    # is in field.empty_values.
    result = fk_value
    if value_in_empty_values(result):
        result = obj_pk
    return result


# --- shadow of implementation_foreignKeyValueOnSave (the R/I leg) -------------
# Mirrors Solution.lean op-for-op. fkValueIsEmpty: None -> True, str -> s == "".
def fk_value_is_empty(v):
    if v is None:
        return True
    return v == ""


def shadow_fk(fk_value, obj_pk):
    result = fk_value
    if fk_value_is_empty(result):
        result = obj_pk
    return result


def disagree(fk_value, obj_pk):
    got = oracle_fk(fk_value, obj_pk)
    want = shadow_fk(fk_value, obj_pk)
    # Normalize: oracle/shadow both return either a string or None.
    if got != want or (got is None) != (want is None):
        return (fk_value, obj_pk, got, want)
    return None


def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def main() -> int:
    checked = 0

    # Edge set = EXHAUSTIVE over modeled stored-value forms x pk forms.
    for fk in FK_VALUE_FORMS:
        for pk in OBJ_PK_FORMS:
            d = disagree(fk, pk)
            if d:
                print(f"DISAGREE exhaustive fkValue={d[0]!r} objPk={d[1]!r}: "
                      f"oracle={d[2]!r} shadow={d[3]!r}")
                print("status=fail")
                return 1
            checked += 1

    # Redundant random fuzz over richer string scalars.
    rnd = _lcg(SEED)
    pool = (None, "", "0", "jeff", "foo", "5", "  ", "x.y", "a", "")
    pkpool = ("jeff", "foo", "5", "x", "0", "a", " ")
    for _ in range(N):
        fk = pool[next(rnd) % len(pool)]
        pk = pkpool[next(rnd) % len(pkpool)]
        d = disagree(fk, pk)
        if d:
            print(f"DISAGREE fuzz fkValue={d[0]!r} objPk={d[1]!r}: "
                  f"oracle={d[2]!r} shadow={d[3]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
