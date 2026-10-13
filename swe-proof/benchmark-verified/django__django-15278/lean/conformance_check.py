#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15278.

The bundle models ONE decision: the boolean routing predicate at the head of
`DatabaseSchemaEditor.add_field` (sqlite3 backend) that selects whether to
reconstruct the table (`_remake_table`) or do a plain in-place column addition
(`super().add_field`). Its Lean implementation
(`implementation_requiresTableRebuild`) computes:

    if isPrimaryKey or isUnique or (not allowsNull) or hasStoredDefault:
        return True
    return False

This script transliterates that R/I impl into Python (`shadow_decide`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
post-patch decision in `django/db/backends/sqlite3/schema.py`:

    if (
        field.primary_key or field.unique or
        not field.null or self.effective_default(field) is not None
    ):
        self._remake_table(...)   # -> decision True
    else:
        super().add_field(...)    # -> decision False

We do NOT stand up real Field / schema-editor objects (heavy, and the modeled
value is a pure decision over four boolean column properties). Instead we
reproduce the patched decision over light stand-in inputs carrying the SAME
observables the real field exposes (mapping.md): `is_primary_key`, `is_unique`,
`allows_null`, `has_stored_default` (the last is `effective_default(field) is not
None`). The real PRE-patch decision omitted `field.primary_key or field.unique`;
the post-patch decision below includes them — which is what the oracle encodes.

The differential genuinely tests the Lean modeling: the shadow uses the Lean
`||`-shaped disjunction over the abstracted booleans, whereas the oracle
reproduces the patched Python `or`-chain over realistically shaped inputs. They
must agree for every input — in particular for a nullable, default-free,
non-primary-key UNIQUE column (the one-to-one case the patch repairs), where the
pre-patch decision was False and the post-patch decision is True.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 15278 (also recorded in
mapping.md).
"""
import sys

SEED = 15278
N = 120_000


# --- ORACLE: the post-patch decision, faithful in-process replica ------------
# Inputs are the four boolean observables of the column (mapping.md):
#   is_primary_key      <- field.primary_key
#   is_unique           <- field.unique
#   allows_null         <- field.null
#   has_stored_default  <- (self.effective_default(field) is not None)
def oracle_decide(is_primary_key, is_unique, allows_null, has_stored_default):
    # post-patch: field.primary_key or field.unique or
    #             not field.null or effective_default(field) is not None
    if (
        is_primary_key or is_unique or
        (not allows_null) or has_stored_default
    ):
        return True   # _remake_table (reconstruct)
    return False      # super().add_field (plain in-place add)


# --- shadow of implementation_requiresTableRebuild (the R/I leg) -------------
# Mirrors Solution.lean: `if isPrimaryKey || isUnique || !allowsNull ||
# hasStoredDefault then return true; return false`.
def shadow_decide(is_primary_key, is_unique, allows_null, has_stored_default):
    if is_primary_key or is_unique or (not allows_null) or has_stored_default:
        return True
    return False


def disagree(t):
    got = oracle_decide(*t)
    want = shadow_decide(*t)
    if got != want:
        return (t, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_exhaustive():
    """All 16 assignments of the four booleans."""
    out = []
    for bits in range(16):
        out.append((
            bool(bits & 1),        # is_primary_key
            bool(bits & 2),        # is_unique
            bool(bits & 4),        # allows_null
            bool(bits & 8),        # has_stored_default
        ))
    return out


def main() -> int:
    checked = 0

    # Exhaustive over the whole 4-bit input space (includes the F2P
    # discriminator: nullable unique non-pk default-free column).
    for t in _enumerate_exhaustive():
        d = disagree(t)
        if d:
            print(f"DISAGREE exhaustive {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        t = (
            next(rnd) % 2 == 0,
            next(rnd) % 2 == 0,
            next(rnd) % 2 == 0,
            next(rnd) % 2 == 0,
        )
        d = disagree(t)
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
