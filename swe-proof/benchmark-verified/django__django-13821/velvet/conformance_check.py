#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13821 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`verifyVersion`)
              transliterated to Python over the *real* repo types, via the
              mapping.md bijection: the version-info tuple ↔ `List Nat`, the
              version string ↔ `List Char`, the `Except (List Char) Unit`
              outcome ↔ (raise `ImproperlyConfigured` with that message | no
              raise). The impl region has NO A-tagged content (no axioms / no
              deep-model references), so the whole shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `check_sqlite_version`
              applied at base_commit (the real correctness oracle, G-RESOLVE),
              driven by monkeypatching the SQLite version globals it reads.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + hypothesis
only. The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 13821
N_FUZZ = 100_000

REQUIRED = (3, 9, 0)


# --- the R/I shadow: Solution.lean lexLt / checkSpec, transliterated ----------

def shadow_outcome(info, version_str):
    """checkSpec(info, version_str) transliterated to Python.

    Returns None when the spec succeeds (`Except.ok ()`), or the diagnostic
    string when it fails (`Except.error (errorMessage ...)`). Python tuple `<`
    IS the lexicographic order `lexLt` models, so the comparison transliterates
    directly."""
    if tuple(info) < REQUIRED:
        return "SQLite 3.9.0 or later is required (found %s)." % version_str
    return None


# --- the oracle: patch.diff's behaviour (the patched check_sqlite_version) ----

def oracle_outcome(info, version_str):
    """patch.diff's behaviour: drive the real patched `check_sqlite_version` by
    monkeypatching the SQLite version globals it reads, and observe whether it
    raises `ImproperlyConfigured` (and with what message) or returns."""
    from django.core.exceptions import ImproperlyConfigured
    from django.db.backends.sqlite3 import base as sqlite3_base

    Database = sqlite3_base.Database
    saved_info = Database.sqlite_version_info
    saved_str = Database.sqlite_version
    try:
        Database.sqlite_version_info = tuple(info)
        Database.sqlite_version = version_str
        try:
            sqlite3_base.check_sqlite_version()
        except ImproperlyConfigured as exc:
            return str(exc)
        return None
    finally:
        Database.sqlite_version_info = saved_info
        Database.sqlite_version = saved_str


def info_to_str(info):
    return ".".join(str(p) for p in info)


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4): straddle both the old (3,8,3) and
    # new (3,9,0) thresholds and the F2P version.
    boundary = [
        (3, 9, 0),          # exactly the new minimum -> ok
        (3, 8, 11, 1),      # the F2P version: below new min, above old -> error
        (3, 8, 3),          # exactly the old minimum -> error under the new spec
        (3, 8, 2),          # the old-test version -> error
        (3, 8, 0),
        (3, 9, 1),
        (3, 10, 0),
        (3, 11, 0),         # Ubuntu Xenial ships this -> ok
        (3, 8, 7),          # Debian Jessie ships this -> error
        (4, 0, 0),
        (2, 9, 9),
        (3,),
        (3, 9),             # prefix of the minimum -> below it -> error
        (3, 10),
        (3, 8),
        (0, 0, 0),
    ]
    for info in boundary:
        yield list(info), info_to_str(info)
    for _ in range(n):
        k = rng.randint(1, 4)
        info = [rng.randint(0, 12) for _ in range(k)]
        # bias toward the interesting 3.x neighbourhood
        if rng.random() < 0.5 and k >= 1:
            info[0] = 3
        if rng.random() < 0.5 and k >= 2:
            info[1] = rng.randint(7, 11)
        yield info, info_to_str(info)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for info, vstr in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_outcome(info, vstr)
        oracle = oracle_outcome(info, vstr)
        if shadow != oracle:
            disagreements.append((info, vstr, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for info, vstr, sh, orc in disagreements:
            print("  info=%r vstr=%r shadow=%r oracle=%r" % (info, vstr, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of verifyVersion agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
