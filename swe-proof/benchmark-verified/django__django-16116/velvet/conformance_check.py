#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16116 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`runCheckedWrite`) is the non-empty-`changes` branch of
`makemigrations.Command.handle`
(`django/core/management/commands/makemigrations.py:251-257`):

    else:
        if check_changes:          # <-- the fix relocates this guard ABOVE
            sys.exit(1)            #     the write block
        if self.update:
            self.write_to_last_migration_files(changes)
        else:
            self.write_migration_files(changes)

The CHANGED behaviour the spec pins is the *relative order* of the non-zero
abort and the migration writes: post-patch a check-only run aborts BEFORE any
write, so no migration artifact is emitted; pre-patch the artifact is written
first, then the process aborts.

This is not reproducible as a pure, DB-free R/I shadow this gate can fuzz over
>=1e5 inputs:

  * The only observable the fix produces is a SIDE EFFECT — whether a migration
    file is created on disk and whether the process terminates with a non-zero
    status. It materializes only after `handle` runs the real
    `write_migration_files` / `write_to_last_migration_files` writers (which
    serialize migration objects to a temporary migration module on the
    filesystem) and the real `sys.exit(1)`. Reproducing it requires a populated
    app registry, a `MigrationLoader`, a `MigrationAutodetector` that returns a
    non-empty `changes`, the filesystem writers and a temporary migration
    module — i.e. the F2P integration test itself
    (`MakeMigrationsTests.test_makemigrations_check`,
    `tests/migrations/test_commands.py`), which asserts the temp module dir is
    absent after a `--check` run — not a transliteration this gate can fuzz.
  * The branch's R/I content reduces to the constant two-flag truth table
    `stepOutcome(check_only, update)` — there is NO input-content-dependent
    computation on any data carrier to differentially refute. The discriminating
    fact is the statement ORDER (abort vs write), which is exercised only by the
    live `sys.exit` raise/unwind + write machinery, covered by axiom_check.py
    (G-AX).

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the impl region's observable is a
live filesystem/exit side effect with no DB-free, input-dependent R/I shadow,
set meta.json conf_skip=true and ship this status=skip stub. Soundness of the
modeled branch is carried instead by G-VERIFY (the spec provably forces
`check_only => written = noWrite`), G-DIFF (the prepatch, which writes then
aborts, fails exactly the `check_only -> written = noWrite` clause), and G-AX
(the real `sys.exit(1)` raises `SystemExit` and unwinds the stack, so a write
statement sequenced after it does not run). See mapping.md section 3/4 and
refinement.md section A/B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-16116 — the modeled do-block is "
          "the non-empty-changes branch of makemigrations.handle; the fix "
          "re-orders the non-zero abort (sys.exit(1)) ABOVE the migration "
          "writes so a check-only run emits no artifact. The only observable is "
          "a live filesystem/exit side effect with no DB-free, input-dependent "
          "R/I shadow. conf_skip=true. Soundness covered by G-VERIFY + G-DIFF + "
          "G-AX (axiom_check.py).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
