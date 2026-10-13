#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15252 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `recordStoreGate` impl
              region, transliterated to Python over the real repo facts via the
              mapping.md bijection (`plan == [] ↔ !hasWork`,
              `has_table() ↔ storePresent`, effect-observations are identity on
              Bool). There are NO A-tagged callees (mapping.md §3), so the
              shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched
              `MigrationExecutor.migrate` applied at base_commit (the harness
              applies patch.diff before this runs). We drive it with the
              surrounding methods replaced by call spies and read back the two
              observable effects:
                ensured   = was `self.recorder.ensure_schema()` invoked?
                earlyExit = did the step short-circuit before
                            `self.check_replacements()`?

They must agree on every Requires-satisfying input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import os
import random
import sys
from unittest import mock

SEED = 15252
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean recordStoreGate, transliterated -----------
def shadow_gate(has_work, store_present):
    """recordStoreGate (hasWork storePresent) transliterated to Python.
    Returns (ensured, earlyExit). This is the impl region's nested-if branch."""
    ensured = False
    early_exit = False
    if not has_work:
        if not store_present:
            early_exit = True
    else:
        ensured = True
    return ensured, early_exit


# --- the oracle: drive the REAL patched migrate, observe the two effects -----
def _build_executor():
    """A MigrationExecutor whose surrounding machinery is stubbed, so the only
    live code is the patched gate at the top of `migrate`."""
    from django.db.migrations.executor import MigrationExecutor
    ex = MigrationExecutor.__new__(MigrationExecutor)
    ex.progress_callback = None
    ex.recorder = mock.Mock()                 # has_table / ensure_schema spies
    ex.loader = mock.Mock()
    ex.loader.graph.leaf_nodes.return_value = []
    # migration_plan / state builders / forward runner / replacement check: all
    # unchanged-by-this-fix machinery, replaced by spies so we observe only the
    # gate's two effects.
    ex.migration_plan = mock.Mock(return_value=[])
    ex._create_project_state = mock.Mock(return_value="STATE")
    ex._migrate_all_forwards = mock.Mock(return_value="STATE")
    ex._migrate_all_backwards = mock.Mock(return_value="STATE")
    ex.check_replacements = mock.Mock()
    return ex


def oracle_gate(has_work, store_present):
    """patch.diff's behaviour: observed (ensured, earlyExit) of the real
    patched migrate on a Requires-satisfying input."""
    ex = _build_executor()
    ex.recorder.has_table.return_value = store_present
    if has_work:
        # a non-empty, all-forwards plan: one (migration, backwards=False) tuple
        plan = [(object(), False)]
    else:
        plan = []
    ex.migrate(targets=[("app", "0001")], plan=plan)
    ensured = ex.recorder.ensure_schema.called
    # The patched early-return fires *before* check_replacements; in every other
    # path check_replacements runs. So "did NOT reach check_replacements" is
    # exactly the short-circuit.
    early_exit = not ex.check_replacements.called
    return ensured, early_exit


def fuzz_inputs(n, rng):
    # The Requires-satisfying input domain is the 2x2 boolean table; enumerate
    # the corners first (boundary), then fuzz the full table to N_FUZZ.
    for hw in (False, True):
        for sp in (False, True):
            yield hw, sp
    for _ in range(n):
        yield rng.random() < 0.5, rng.random() < 0.5


def main():
    # Allow the harness to point us at the repo; otherwise assume it's importable.
    repo = os.environ.get("REPO_ROOT")
    if repo and repo not in sys.path:
        sys.path.insert(0, repo)
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for hw, sp in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_gate(hw, sp)
        oracle = oracle_gate(hw, sp)
        if shadow != oracle:
            disagreements.append((hw, sp, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for hw, sp, sh, orc in disagreements:
            print("  hasWork=%r storePresent=%r shadow=%r oracle=%r"
                  % (hw, sp, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of recordStoreGate agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
