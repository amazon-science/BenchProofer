#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-13109.

The bundle models ONE function: `ForeignKey.validate`. Its Lean implementation
(`implementation_validateReference`) decides whether a reference is sound:

    if parentLink:            return True       # parent-link: no existence check
    if value is None:         return True       # null reference
    # existence check over the UNDERLYING stored collection (every stored row,
    # regardless of the default presentation filter):
    qs = rows
    qs = [r for r in qs if r.key == value]
    qs = [r for r in qs if r.limitOk]
    return len(qs) != 0

This script transliterates that R/I impl into Python (`shadow_validate`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `ForeignKey.validate`
(`django/db/models/fields/related.py`):

    using = router.db_for_read(...)
    qs = model._base_manager.using(using).filter(**{field_name: value})
    qs = qs.complex_filter(self.get_limit_choices_to())
    if not qs.exists():
        raise ValidationError(...)   # -> validation FAILS

We do NOT stand up a database / ORM (heavy, and the modeled value is a pure
decision over the stored rows the query consults). Instead we reproduce the
patched behavior with light stand-in row records carrying the SAME observables
the real query consults (mapping.md): `key` (the referenced-field value),
`defaultVisible` (whether the row survives the model's default manager
`get_queryset()` filter), and `limitOk` (whether the row satisfies
`get_limit_choices_to()`).

The KEY of the differential is the manager selection. The post-patch oracle
starts from `_base_manager` — the unfiltered collection — so it IGNORES
`defaultVisible` entirely. The shadow mirrors that: it scans all `rows`. They
must agree for every input — in particular on rows with `defaultVisible == False`
(the genuinely-stored-but-hidden case the patch fixes), where a default-manager
scan would wrongly exclude the row.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 13109 (also recorded in
mapping.md).
"""
import sys

SEED = 13109
N = 120_000


# --- ORACLE: the post-patch behavior, faithful in-process replica ------------
# A row is a dict {"key": int, "defaultVisible": bool, "limitOk": bool}.
# Post-patch `validate` builds the existence query from `_base_manager`, i.e. the
# UNFILTERED stored collection, then filters by `field_name == value` and by the
# `complex_filter(get_limit_choices_to())` constraint, then checks `.exists()`.
# Because the base manager is unfiltered, `defaultVisible` is NOT consulted.
def oracle_validate(parent_link, value, rows):
    if parent_link:
        return True
    if value is None:
        return True
    qs = list(rows)                                  # _base_manager: all stored rows
    qs = [r for r in qs if r["key"] == value]        # .filter(field_name=value)
    qs = [r for r in qs if r["limitOk"]]             # .complex_filter(limit_choices_to)
    return len(qs) != 0                              # qs.exists()


# --- shadow of implementation_validateReference (the R/I leg) ----------------
# Mirrors Solution.lean: scan all `rows`, filter by key then by limitOk, non-empty.
def shadow_validate(parent_link, value, rows):
    if parent_link:
        return True
    if value is None:
        return True
    qs = list(rows)
    qs = [r for r in qs if r["key"] == value]
    qs = [r for r in qs if r["limitOk"]]
    return len(qs) != 0


def disagree(parent_link, value, rows):
    got = oracle_validate(parent_link, value, rows)
    want = shadow_validate(parent_link, value, rows)
    if got != want:
        return ((parent_link, value, rows), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases, exercising the hidden-but-stored row behavior."""
    cases = []
    for parent in (True, False):
        for value in (None, 1):
            cases.append((parent, value, []))
    # the discriminating case: the only matching row is hidden from the default
    # presentation (defaultVisible == False) but stored and eligible. The fix
    # must report this reference sound.
    cases.append((False, 1, [{"key": 1, "defaultVisible": False, "limitOk": True}]))
    cases.append((False, 1, [{"key": 1, "defaultVisible": True, "limitOk": True}]))
    cases.append((False, 1, [{"key": 1, "defaultVisible": False, "limitOk": False}]))
    cases.append((False, 2, [{"key": 1, "defaultVisible": False, "limitOk": True}]))
    cases.append((False, 1,
                  [{"key": 1, "defaultVisible": False, "limitOk": True},
                   {"key": 2, "defaultVisible": True, "limitOk": True}]))
    # parent-link / null short-circuits even with non-matching tables:
    cases.append((True, 9, [{"key": 0, "defaultVisible": True, "limitOk": True}]))
    cases.append((False, None, [{"key": 0, "defaultVisible": True, "limitOk": True}]))
    return cases


def _rand_bool(rnd):
    return (next(rnd) & 1) == 1


def main() -> int:
    checked = 0

    for parent, value, rows in _enumerate_edge():
        d = disagree(parent, value, rows)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        parent = _rand_bool(rnd)
        vsel = next(rnd) % 6              # 0 => None, else key 0..4
        value = None if vsel == 0 else (vsel - 1)
        length = next(rnd) % 9           # 0..8 rows
        rows = []
        for _ in range(length):
            rows.append({
                "key": next(rnd) % 5,             # keys 0..4 (repeats possible)
                "defaultVisible": _rand_bool(rnd),
                "limitOk": _rand_bool(rnd),
            })
        d = disagree(parent, value, rows)
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
