#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-14500.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean skeleton

    implementation_unapplyMigration

and diffs it against the REAL patched callee
`MigrationExecutor.unapply_migration`.

Observable: the ORDERED sequence of identifiers handed to
`recorder.record_unapplied(app, name)` when the method runs. We drive the real
method with `fake=True` (so the schema-editor / state-mutation path is skipped —
it is orthogonal to the recording decision, mapping.md) and a captured recorder
that records each `(app, name)` call in order. The migration is a light stub
exposing `app_label`, `name`, `replaces`, and `atomic`.

Exit 0 iff zero disagreements over the discrete matrix plus >=1e5 randomized
draws. stdlib-only fuzzing (pinned seed).
"""
import os
import random
import string
import sys


SEED = 14500
N_RANDOM = 120_000  # >= 1e5


# ---- shadow of implementation_unapplyMigration -----------------------------
# mig is (app_label, name, replaces) where replaces is a list of (app, name).
# Returns the ordered list of recorded identifiers.
def shadow(app_label, name, replaces):
    recorded = []
    if replaces:                      # if mig.replaces != []
        for r in replaces:
            recorded.append(r)
    recorded.append((app_label, name))   # unconditional own-identifier record
    return recorded


# ---- real callee -----------------------------------------------------------
class _CaptureRecorder:
    def __init__(self):
        self.calls = []

    def record_unapplied(self, app, name):
        self.calls.append((app, name))

    # record_applied / ensure_schema unused on the unapply path under fake=True.


class _StubMigration:
    atomic = False

    def __init__(self, app_label, name, replaces):
        self.app_label = app_label
        self.name = name
        self.replaces = replaces

    def unapply(self, state, schema_editor):   # never called with fake=True
        return state


def real(executor_cls, app_label, name, replaces):
    """Drive the REAL unapply_migration recording path, capture the call order."""
    ex = executor_cls.__new__(executor_cls)   # bypass __init__ (no DB needed)
    rec = _CaptureRecorder()
    ex.recorder = rec
    ex.connection = None          # unused with fake=True
    ex.progress_callback = None
    mig = _StubMigration(app_label, name, replaces)
    ex.unapply_migration(state=None, migration=mig, fake=True)
    return rec.calls


def rand_id(rng):
    a = "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(1, 8)))
    n = "".join(rng.choice(string.digits) for _ in range(rng.randint(1, 4)))
    return (a, n)


def cases(rng):
    # Discrete boundary matrix.
    yield ("migrations", "0001_initial", [])
    yield ("migrations", "0001_initial", None)      # falsy replaces
    yield ("app", "0001_squashed_0002",
           [("app", "0001_initial"), ("app", "0002_more")])
    yield ("app", "0001_squashed", [("app", "0001_initial")])
    # Randomized draws.
    for _ in range(N_RANDOM):
        app_label, name = rand_id(rng)
        k = rng.randint(0, 5)
        if k == 0 and rng.random() < 0.5:
            replaces = None
        else:
            replaces = [rand_id(rng) for _ in range(k)]
        yield (app_label, name, replaces)


def main():
    sys.path.insert(0, os.environ.get("TESTBED", "/testbed"))
    from django.db.migrations.executor import MigrationExecutor

    rng = random.Random(SEED)
    mismatches = 0
    examples = []
    total = 0
    for app_label, name, replaces in cases(rng):
        total += 1
        norm_replaces = [tuple(r) for r in (replaces or [])]
        want = shadow(app_label, name, norm_replaces)
        got = real(MigrationExecutor, app_label, name, replaces)
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append((app_label, name, replaces, got, want))

    if mismatches:
        print(f"G-CONF FAIL: {mismatches}/{total} disagreements")
        for a, n, r, g, w in examples:
            print(f"  app={a!r} name={n!r} replaces={r!r} real={g} shadow={w}")
        return 1

    print(f"G-CONF OK: {total} inputs, 0 disagreements vs real "
          f"unapply_migration (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
