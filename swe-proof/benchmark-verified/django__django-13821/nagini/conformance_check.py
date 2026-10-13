#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13821 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Requires/Ensures/Exsures/Invariant/Assert removed; the
while/else control flow and every executable statement are untouched). The
carrier is a plain List[int], so no PSeq shim is needed at runtime; the @Pure
helpers (min_version, lt_lex) are specification-only and are not called by the
impl, so they do not appear in the shadow. There are no @ContractOnly callees.

ORACLE: the REAL patched repo function the model models per mapping.md —
`django.db.backends.sqlite3.base.check_sqlite_version`. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable. The real function reads the runtime version from
the DB-API module attribute (`Database.sqlite_version_info`, with
`Database.sqlite_version` its dotted-string form used only for the error
message), so the oracle injects each fuzzed version by patching those two
attributes on the imported module and restoring them afterwards — the same
injection the repo's own test uses, and exactly the modeling boundary: the
model takes the version as its input parameter.

Type bridge (mapping.md §2):
  * `version: List[int]` <-> the version-info tuple of ints (component k <->
    component k); the oracle passes `tuple(version)`.
  * shadow raise of UnsupportedConfiguration <-> real raise of
    django.core.exceptions.ImproperlyConfigured; the compared observable is
    the accept/reject DECISION (normal return vs raise), which is what the
    contract pins. The message string is a presentation of the same decision
    (mapping.md §4) and is not part of the carrier, so it is not compared.
  * normal return: both return None; compared as "accepted".

Input domain (the model's Requires): any list of ints (the read-only
list_pred permission is the only value constraint). Boundary cases cover the
empty version, prefixes/extensions of the minimum, components straddling each
minimum component, and large finer-level components; fuzz draws lengths 0..6
with components biased around 0, 3, 8, 9, 10 plus occasional large and
negative values (tuple comparison is total on ints, so negatives are
Requires-satisfying even though real runtimes never produce them).

>= 1e5 Requires-satisfying inputs: 33 boundary + 100000 fuzz.
Pinned fuzz seed: 1382100.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only.
"""
import random
import sys

SEED = 1382100
N_FUZZ = 100_000


class UnsupportedConfiguration(Exception):
    """Shadow stand-in for the configuration error (model.py)."""
    pass


# --- the impl region of model.py, verbatim (contracts stripped) --------------

def check_supported_version(version):
    mn = [3, 9, 0]  # type: List[int]
    below = False
    i = 0
    n = len(version)
    m = len(mn)
    while i < n and i < m:
        a = version[i]
        b = mn[i]
        if a < b:
            below = True
            break
        if a > b:
            below = False
            break
        i = i + 1
    else:
        # The loop ran to exhaustion (no break): one sequence ran out. The
        # runtime is below the minimum iff it is the strict prefix, i.e. it ran
        # out of components first.
        if i < n:
            # minimum exhausted first => runtime is longer => not below.
            below = False
        elif i < m:
            # runtime exhausted first => runtime is a strict prefix => below.
            below = True
        else:
            # both exhausted simultaneously => equal => not below.
            below = False
    if below:
        raise UnsupportedConfiguration()
    return


# --- outcome observers --------------------------------------------------------

def shadow_outcome(version):
    """Run the shadow on a List[int]; return 'accept' or 'reject'."""
    try:
        check_supported_version(list(version))
    except UnsupportedConfiguration:
        return "reject"
    return "accept"


def real_outcome(base_mod, config_error, version):
    """Run the REAL patched check_sqlite_version with the runtime version
    injected as `tuple(version)` on the DB-API module attribute (the value the
    real function reads); return 'accept' or 'reject'."""
    db = base_mod.Database
    saved_info = db.sqlite_version_info
    saved_str = db.sqlite_version
    try:
        db.sqlite_version_info = tuple(version)
        db.sqlite_version = ".".join(str(c) for c in version)
        try:
            base_mod.check_sqlite_version()
        except config_error:
            return "reject"
        return "accept"
    finally:
        db.sqlite_version_info = saved_info
        db.sqlite_version = saved_str


def boundary_cases():
    return [
        [],                                # empty version (strict prefix)
        [3], [3, 9], [3, 8], [3, 10],      # prefixes / near-minimum prefixes
        [3, 9, 0],                         # the minimum exactly (accepted)
        [3, 9, 0, 0], [3, 9, 0, 1],        # extensions of the minimum
        [3, 8, 9], [3, 8, 99], [3, 8, 11, 1],  # 3.8-series (all rejected)
        [3, 8, 3], [3, 8, 3, 0],
        [3, 9, 1], [3, 10, 0], [3, 11, 4],
        [2, 9, 9], [2, 99, 99], [4, 0, 0], [4], [0], [0, 0, 0],
        [3, 9], [3, 9, 0, 0, 0, 0],
        [3, 8, 2 ** 31],                   # huge finer-level component
        [3, 9, 2 ** 31],
        [2 ** 31, 0, 0],
        [3, 8, 3, 9, 9, 9],
        [-1], [-1, 0, 0], [3, -9, 0],      # negatives: Requires-satisfying
        [3, 9, -1],
        [1, 2, 3, 4, 5, 6],
    ]


def rand_version(rng):
    length = rng.randint(0, 6)
    out = []
    for _ in range(length):
        choice = rng.randint(0, 6)
        if choice <= 3:
            out.append(rng.choice([0, 1, 2, 3, 8, 9, 10, 11]))
        elif choice == 4:
            out.append(rng.randint(0, 40))
        elif choice == 5:
            out.append(rng.randint(0, 10 ** 9))
        else:
            out.append(rng.randint(-20, -1))
    return out


def main():
    import django.db.backends.sqlite3.base as base_mod
    from django.core.exceptions import ImproperlyConfigured

    checked = 0
    disagreements = 0

    def check(version):
        nonlocal checked, disagreements
        s = shadow_outcome(version)
        r = real_outcome(base_mod, ImproperlyConfigured, version)
        checked += 1
        if s != r:
            disagreements += 1
            print("DISAGREEMENT\n  version=%r\n  shadow=%s\n  real=%s"
                  % (version, s, r))
            return False
        return True

    for v in boundary_cases():
        if not check(v):
            return 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        if not check(rand_version(rng)):
            return 1

    print("G-CONF OK: shadow impl == real patched check on %d inputs "
          "(%d boundary + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
