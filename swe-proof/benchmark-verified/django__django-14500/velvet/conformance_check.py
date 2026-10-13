#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14500 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (`recordUnappliedKeys`)
              transliterated to Python over the real repo carrier, via the
              mapping.md bijection (`Migration` struct ↔ the touched fields of a
              real Migration; `List (String × String)` ↔ the ordered sequence of
              keys passed to `recorder.record_unapplied`). Every op in the impl
              region is R/I (a list of `(app_label, name)` pairs and a `++`);
              there are no A-tagged callees in the impl, so the shadow is pure
              R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `MigrationExecutor.unapply_migration` applied at base_commit (the
              real correctness oracle, G-RESOLVE), invoked with `fake=True` and a
              capturing stub recorder so the observable is exactly the ordered
              sequence of `record_unapplied(app_label, name)` calls — the keys
              the migration is recorded as unapplied under.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image after the gold patch is
applied), stdlib only. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

SEED = 14500
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean recordUnappliedKeys, transliterated -------
def shadow_record(replaces, app_label, name):
    """recordUnappliedKeys (m) transliterated to Python: the replaced keys in
    order, followed by the migration's own key. This is the R/I shadow of the
    impl region (`out = m.replaces ++ [(m.appLabel, m.name)]`)."""
    return list(replaces) + [(app_label, name)]


# --- the oracle: patch.diff's behaviour (real patched unapply_migration) -----
class _CaptureRecorder:
    """Stub MigrationRecorder: captures the ordered record_unapplied keys."""
    def __init__(self):
        self.calls = []

    def record_unapplied(self, app_label, name):
        self.calls.append((app_label, name))


class _StubMigration:
    def __init__(self, replaces, app_label, name):
        self.replaces = list(replaces)
        self.app_label = app_label
        self.name = name
        self.atomic = True

    def unapply(self, state, schema_editor):  # pragma: no cover - fake=True skips
        return state


def oracle_record(replaces, app_label, name):
    """patch.diff's behaviour. We call the *real* patched unapply_migration on a
    MigrationExecutor whose recorder is the capturing stub, with fake=True (so
    the schema_editor / DB path is skipped) and no progress_callback. The
    observable is the captured record_unapplied key sequence."""
    from django.db.migrations.executor import MigrationExecutor
    # Build an executor without running __init__ (which needs a live DB
    # connection); install only the fields unapply_migration touches.
    ex = MigrationExecutor.__new__(MigrationExecutor)
    ex.recorder = _CaptureRecorder()
    ex.progress_callback = None
    ex.connection = None  # unused when fake=True
    migration = _StubMigration(replaces, app_label, name)
    ex.unapply_migration(None, migration, fake=True)
    return ex.recorder.calls


# --- fuzzing -----------------------------------------------------------------
def _rand_label(rng):
    n = rng.randint(1, 6)
    return "".join(rng.choice("abcdefghijklmnopqrstuvwxyz_0123456789") for _ in range(n))


def _rand_key(rng):
    return (_rand_label(rng), _rand_label(rng))


def fuzz_inputs(n, rng):
    # boundary cases first (plan §4.1 step 4)
    # ordinary migration: no replaced set
    yield ([], "migrations", "0001_initial")
    # squashed / replacement migration: the F2P scenario
    yield ([("migrations", "0001_initial"), ("migrations", "0002_second")],
           "migrations", "0001_squashed_0002")
    # single replaced key
    yield ([("app", "0001")], "app", "0001_squashed")
    # own key duplicated inside replaces (still appended unconditionally)
    yield ([("app", "0001_squashed")], "app", "0001_squashed")
    # empty-string fields
    yield ([], "", "")
    yield ([("", "")], "x", "y")
    for _ in range(n):
        k = rng.randint(0, 6)
        replaces = [_rand_key(rng) for _ in range(k)]
        app_label, name = _rand_key(rng)
        yield (replaces, app_label, name)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for replaces, app_label, name in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_record(replaces, app_label, name)
        oracle = oracle_record(replaces, app_label, name)
        if shadow != oracle:
            disagreements.append((replaces, app_label, name, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for replaces, app_label, name, sh, orc in disagreements:
            print("  replaces=%r own=(%r,%r) shadow=%r oracle=%r"
                  % (replaces, app_label, name, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of recordUnappliedKeys agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
