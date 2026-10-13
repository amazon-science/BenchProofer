#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14500 (nagini).

SHADOW: the impl region of `keys_leaving_applied_set` from model.py, copied
verbatim below with the contract calls (Requires/Ensures/Invariant/Assert)
stripped and PSeq realized as an immutable tuple shim. There are no @Pure
helpers and no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.db.migrations.executor.MigrationExecutor.unapply_migration`, observed
through the ordered sequence of `record_unapplied(app_label, name)` calls it
issues on its recorder. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched module importable. The
method is invoked with `fake=True` (a real parameter of the function): that
skips only the schema-editor work, which lies outside the modeled observable
(the recording behaviour is identical for fake and non-fake runs), so no
database is needed. The recorder is replaced by a spy that appends each
recorded key, and the migration argument is a REAL
`django.db.migrations.Migration` instance carrying the generated identity and
replaced-key list.

Type bridge (mapping.md section 2): each migration bookkeeping key
`(app_label, name)` maps to an int code. The bridge realizes each int code k
as the distinct pair ("app_%d" % k, "mig_%d" % k) -- injective, so key
equality on either side coincides. `replaced_keys: PSeq[int]` maps to the
migration's replaced-key list of the corresponding pairs (order preserved);
the shadow's `List[int]` result maps to the ordered list of pairs the real
method records.

Input domain: Requires(True) -- every (own_key, replaced_keys) pair is
admissible. Generation covers the boundary cases (empty replaced list,
singleton, duplicates, own key among the replaced keys, negative codes) plus
an exhaustive small enumeration and heavy fuzz.

>= 1e5 Requires-satisfying inputs: boundary + exhaustive small enumeration
(3905) + 100000 fuzz pairs. Pinned fuzz seed: 14500.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import itertools
import json
import random
import sys

SEED = 14500
N_FUZZ = 100_000


# --- PSeq shim: immutable sequence, the operations the impl region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def keys_leaving_applied_set(own_key, replaced_keys):
    result = []  # type: list
    # For replacement migrations, record each replaced key as no-longer-applied,
    # in listed order.
    i = 0
    while i < len(replaced_keys):
        result = result + [replaced_keys[i]]
        i = i + 1
    # Then record the migration's own key as no-longer-applied -- always.
    result = result + [own_key]
    return result


# --- bridge: int key code <-> (app_label, name) pair ---------------------------

def code_to_pair(k):
    """Injective realization of an int key code as a bookkeeping key pair."""
    return ("app_%d" % k, "mig_%d" % k)


class SpyRecorder:
    """Stands in for the executor's recorder; captures the ordered sequence of
    keys recorded as no-longer-applied (the modeled observable)."""

    def __init__(self):
        self.unapplied = []

    def record_unapplied(self, app, name):
        self.unapplied.append((app, name))


def real_recorded(executor_cls, migration_cls, own_key, replaced_keys):
    """Run the REAL patched unapply_migration on a real Migration instance and
    return the ordered list of key pairs it records as no-longer-applied."""
    own_app, own_name = code_to_pair(own_key)
    migration = migration_cls(own_name, own_app)
    migration.replaces = [code_to_pair(k) for k in replaced_keys]
    executor = executor_cls.__new__(executor_cls)  # no loader/DB needed
    executor.connection = None
    executor.recorder = SpyRecorder()
    executor.progress_callback = None
    state = object()
    out_state = executor.unapply_migration(state, migration, fake=True)
    assert out_state is state, "state must pass through unchanged"
    return executor.recorder.unapplied


def check_pair(executor_cls, migration_cls, own_key, replaced_keys):
    """Diff shadow vs oracle on one input; return an error string on
    disagreement, else None."""
    shadow = keys_leaving_applied_set(own_key, PSeq._wrap(replaced_keys))
    shadow_pairs = [code_to_pair(k) for k in shadow]
    real_pairs = real_recorded(executor_cls, migration_cls,
                               own_key, replaced_keys)
    if shadow_pairs != real_pairs:
        return ("DISAGREEMENT\n  own_key=%r replaced_keys=%r\n"
                "  shadow recorded: %r\n  real recorded:   %r"
                % (own_key, replaced_keys, shadow_pairs, real_pairs))
    return None


def boundary_inputs():
    return [
        (0, []),                    # non-replacement: own key only
        (7, []),
        (-1, []),
        (100, [1, 2]),              # replacement rolled back: replaced + own
        (5, [5]),                   # own key also among its replaced keys
        (3, [1, 2, 3, 4]),
        (10, [10, 10]),             # duplicate replaced keys, order preserved
        (-1, [-2, -3]),             # negative codes
        (42, [1]),
        (0, [0]),
    ]


def main():
    # REAL patched callee (PYTHONPATH=/testbed, gold patch applied by the gate)
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
        django.setup()
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations.migration import Migration

    checked = 0

    n_boundary = 0
    for own_key, replaced in boundary_inputs():
        err = check_pair(MigrationExecutor, Migration, own_key, replaced)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    # exhaustive small enumeration: own key x replaced lists of length 0..4
    # over a 5-code universe
    universe = [0, 1, 2, 3, 4]
    n_exhaustive = 0
    for own_key in universe:
        for length in range(0, 5):
            for replaced in itertools.product(universe, repeat=length):
                err = check_pair(MigrationExecutor, Migration,
                                 own_key, list(replaced))
                if err:
                    print(err)
                    return 1
                checked += 1
                n_exhaustive += 1

    # randomized fuzz, pinned seed
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        own_key = rng.randint(-50, 50)
        n = rng.randint(0, 10)
        replaced = [rng.randint(-50, 50) for _ in range(n)]
        err = check_pair(MigrationExecutor, Migration, own_key, replaced)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real unapply_migration recording on "
          "%d inputs (%d boundary + %d exhaustive + %d fuzz, seed %d)."
          % (checked, n_boundary, n_exhaustive, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
