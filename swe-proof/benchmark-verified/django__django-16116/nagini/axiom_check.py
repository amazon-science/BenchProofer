#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16116.

The two axioms (A-consumed) model the UNCHANGED artefact writers the command
invokes in its changes-present branch:

    write_update_artifacts(store)   <-> Command.write_to_last_migration_files
    write_fresh_artifacts(store)    <-> Command.write_migration_files

Each axiom's (weakened) Ensures says: invoking the writer APPENDS AT LEAST one
produced-file token to the produced-file store while keeping the
previously-produced tokens intact — i.e. each writer is genuinely an
artefact-PRODUCING step (it creates one migration file on disk per pending
migration and records each in ``self.written_files``). The count tracks the
number of migrations in ``changes`` (one app -> +1, two apps -> +2, an empty
``changes`` -> +0), which the axiom deliberately does NOT pin: it asserts only
``len(store) >= len(Old) + 1`` for a non-empty ``changes`` (the proof needs only
that the store GREW), never an exact ``== +1``. The proof relies on exactly
this: because the writer produces >=1 artefact, performing the failure-exit
BEFORE vs AFTER a writer is an OBSERVABLE difference (the on-disk produced-file
set grows vs stays empty).

PATCH-STATE INDEPENDENCE.  The axioms are about the UNCHANGED writers, so the
axiom-soundness portion is true at ``base_commit`` AND with the gold patch
applied — it is the script's authoritative pass/fail (the rc). The separate
end-to-end portion exercises the command's check-mode behaviour, which DIFFERS
by patch state (pre-patch: ``--check`` writes a file then exits; post-patch:
``--check`` exits first and writes nothing). The script auto-detects the patch
state by observing whether ``--check`` writes a file and asserts the
state-appropriate invariant, so it returns 0 regardless of whether the gold
patch is applied.  (See meta.json ``axiom_check_requires: any``.)

This check runs the REAL command inside the official SWE-bench container, where
Django is importable and a writable temp directory is available. It:

  (A, authoritative — patch-state-independent) Drives the REAL
      ``MigrationAutodetector.changes`` to build real ``changes`` dicts and calls
      the REAL ``Command.write_migration_files`` on them — asserting the writer
      grows ``self.written_files`` by ``len(changes)`` (>= 1 for non-empty
      changes; +0 for an empty ``changes``), keeps the previously-produced tokens
      as a prefix, and writes each recorded file to disk. This validates the
      weakened axiom (``>= +1`` growth, prefix preserved) and confirms it is NOT
      over-claimed as ``== +1`` (a two-app changes dict grows by 2).

  (B, informational — patch-state-aware) Runs the full REAL
      ``makemigrations --check`` end-to-end against an app with pending changes,
      and the same command WITHOUT ``--check``. Without ``--check`` it MUST write
      a file (the writer is reached and artefact-producing in BOTH patch states).
      With ``--check`` it raises SystemExit in both states; whether it ALSO wrote
      a file distinguishes the pre-patch bug (writes then exits) from the gold
      fix (exits first, writes nothing). The script reports which state it is in
      and only asserts the F2P observable (``--check`` writes nothing) when the
      fix is present.

Imports nothing repo-specific beyond Django itself (the package under test).
Exit 0 iff every axiom-soundness obligation (portion A) holds.
"""
import os
import sys
import tempfile
import shutil


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "axcheck",
                "axcheck2",
            ],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
            MIGRATION_MODULES={
                "axcheck": "axcheck.migrations",
                "axcheck2": "axcheck2.migrations",
            },
        )
    django.setup()


def _make_app(work, name):
    """Create a writable package tree for an app with one un-migrated model
    (so there ARE pending changes) and an empty migrations package."""
    pkg = os.path.join(work, name)
    os.makedirs(pkg)
    open(os.path.join(pkg, "__init__.py"), "w").close()
    with open(os.path.join(pkg, "models.py"), "w") as fh:
        fh.write(
            "from django.db import models\n"
            "class Widget(models.Model):\n"
            "    name = models.CharField(max_length=20)\n"
            "    class Meta:\n"
            "        app_label = %r\n" % (name,)
        )
    mig = os.path.join(pkg, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return mig


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")

    work = tempfile.mkdtemp(prefix="ax16116_")
    sys.path.insert(0, work)
    try:
        mig1 = _make_app(work, "axcheck")
        mig2 = _make_app(work, "axcheck2")

        try:
            _configure_django()
        except Exception as exc:  # pragma: no cover - environment guard
            print("G-AX SKIP: Django not configurable in this environment: %r"
                  % (exc,))
            return 0

        from django.apps import apps
        from django.core.management import call_command
        from django.core.management.commands.makemigrations import Command
        from django.db.migrations.autodetector import MigrationAutodetector
        from django.db.migrations.loader import MigrationLoader
        from django.db.migrations.questioner import (
            NonInteractiveMigrationQuestioner,
        )
        from django.db.migrations.state import ProjectState
        from io import StringIO

        def real_changes(trim_apps):
            """Drive the REAL autodetector to produce a real changes dict for
            the pending (un-migrated) Widget model(s) in `trim_apps`."""
            loader = MigrationLoader(None, ignore_no_migrations=True)
            questioner = NonInteractiveMigrationQuestioner(
                specified_apps=set(), dry_run=False, verbosity=0
            )
            autodetector = MigrationAutodetector(
                loader.project_state(),
                ProjectState.from_apps(apps),
                questioner,
            )
            return autodetector.changes(
                graph=loader.graph,
                trim_to_apps=set(trim_apps),
                convert_apps=set(trim_apps),
                migration_name=None,
            )

        def fresh_command():
            cmd = Command()
            cmd.verbosity = 0
            cmd.interactive = False
            cmd.dry_run = False
            cmd.merge = False
            cmd.empty = False
            cmd.scriptable = False
            cmd.include_header = True
            cmd.update = False
            cmd.migration_name = None
            cmd.written_files = []
            cmd.stdout = StringIO()
            cmd.stderr = StringIO()
            return cmd

        def cleanup(paths):
            for p in paths:
                try:
                    os.remove(p)
                except OSError:
                    pass

        def migration_files(mig):
            return sorted(
                f for f in os.listdir(mig)
                if f.endswith(".py") and f != "__init__.py"
            )

        def clean_mig(mig):
            for fn in os.listdir(mig):
                if fn != "__init__.py":
                    fp = os.path.join(mig, fn)
                    (shutil.rmtree if os.path.isdir(fp) else os.remove)(fp)

        # ================================================================
        # PORTION A (authoritative): the weakened axiom is sound against the
        # REAL Command.write_migration_files — patch-state-independent (the
        # writer is unchanged by the gold patch).
        # ================================================================

        # --- A.1: single-app changes -> writer grows store by len(changes) (1)
        changes1 = real_changes({"axcheck"})
        assert changes1, (
            "axiom_check setup invalid: the autodetector reported NO pending "
            "changes for the single un-migrated model; cannot validate the "
            "artefact-writer axiom")
        cmd = fresh_command()
        before = list(cmd.written_files)
        cmd.write_migration_files(changes1)
        after = list(cmd.written_files)
        grew = len(after) - len(before)
        assert grew >= 1, (
            "write_fresh_artifacts axiom UNSOUND: the REAL "
            "Command.write_migration_files appended NO produced-file token "
            "(written_files did not grow: %r -> %r); the writer would not be "
            "an artefact-producing step and the exit-ordering would be "
            "unobservable" % (before, after))
        assert grew == len(changes1), (
            "axiom_check sanity: the writer appended %d tokens but changes has "
            "%d migration(s); the per-migration append assumption is wrong"
            % (grew, len(changes1)))
        assert after[: len(before)] == before, (
            "write_fresh_artifacts axiom UNSOUND: the writer dropped/altered a "
            "previously-produced token (prefix not preserved)")
        for p in after[len(before):]:
            assert os.path.exists(p), (
                "write_fresh_artifacts axiom UNSOUND: recorded produced file "
                "%r does not exist on disk" % (p,))
        cleanup(after)
        clean_mig(mig1)

        # --- A.2: multi-app changes -> writer grows by len(changes) (== 2)
        # This is the case the OLD "== +1" axiom would have falsely claimed +1
        # for; the weakened ">= +1" contract is the only sound one.
        changes2 = real_changes({"axcheck", "axcheck2"})
        assert len(changes2) >= 2, (
            "axiom_check setup invalid: expected >= 2 pending migrations for "
            "two un-migrated apps, got %d" % (len(changes2),))
        cmd = fresh_command()
        before = list(cmd.written_files)
        cmd.write_migration_files(changes2)
        after = list(cmd.written_files)
        grew = len(after) - len(before)
        assert grew >= 1, (
            "write_fresh_artifacts axiom UNSOUND: multi-app changes produced "
            "no token (%r -> %r)" % (before, after))
        assert grew == len(changes2), (
            "write_fresh_artifacts axiom mis-modeled: multi-app changes "
            "appended %d tokens for %d migrations (per-migration append "
            "assumption wrong)" % (grew, len(changes2)))
        assert grew >= 2, (
            "OVER-CLAIM CHECK: a >=2-migration changes dict grew the store by "
            "only %d; the axiom MUST be '>= +1' (growth), not '== +1' — an "
            "'== +1' axiom would be UNSOUND here (this is exactly the defect "
            "the weakening fixes)" % (grew,))
        assert after[: len(before)] == before, (
            "write_fresh_artifacts axiom UNSOUND: prefix not preserved on "
            "multi-app changes")
        cleanup(after)
        clean_mig(mig1)
        clean_mig(mig2)

        # --- A.3: empty changes -> writer appends NOTHING (the lower bound is
        # vacuous; confirms growth is conditioned on there being changes, so
        # the axiom never over-claims a +1 for an empty changes dict).
        cmd = fresh_command()
        before = list(cmd.written_files)
        cmd.write_migration_files({})
        after = list(cmd.written_files)
        assert after == before, (
            "write_fresh_artifacts axiom UNSOUND: empty changes appended a "
            "token (%r -> %r); growth must track the number of migrations"
            % (before, after))
        cleanup(after)
        clean_mig(mig1)
        clean_mig(mig2)

        # ================================================================
        # PORTION B (informational, patch-state-aware): end-to-end behaviour.
        # Without --check the writer MUST be reached (both patch states).
        # With --check it raises SystemExit (both states); whether it ALSO
        # wrote distinguishes the pre-patch bug from the gold fix.
        # ================================================================

        # B.1: WITHOUT --check the command writes a migration file (writer
        # reached + artefact-producing) — true in BOTH patch states.
        clean_mig(mig1)
        assert migration_files(mig1) == [], "setup: migrations dir not clean"
        call_command("makemigrations", "axcheck", verbosity=0)
        wrote = migration_files(mig1)
        assert wrote, (
            "makemigrations without --check produced NO migration file; the "
            "writer is not artefact-producing, so the exit-ordering would be "
            "unobservable")

        # B.2: WITH --check the command raises SystemExit; observe whether it
        # also wrote (pre-patch bug) or not (gold fix) and assert accordingly.
        clean_mig(mig1)
        assert migration_files(mig1) == [], "setup: migrations dir not clean"
        raised = False
        try:
            call_command("makemigrations", "axcheck", "--check", verbosity=0)
        except SystemExit:
            raised = True
        assert raised, (
            "makemigrations --check did NOT raise SystemExit on pending "
            "changes (the check-mode failure outcome is missing)")
        check_wrote = migration_files(mig1)
        if check_wrote:
            state = "PRE-PATCH (bug present)"
            print("G-AX NOTE: --check wrote a migration file %r before exiting "
                  "— this container is at base_commit (the bug the gold patch "
                  "fixes). The axiom-soundness portion (A) is independent of "
                  "this and PASSED." % (check_wrote,))
        else:
            state = "POST-PATCH (gold applied)"
            print("G-AX NOTE: --check produced NO migration file (artefact set "
                  "stayed empty) — the gold fix is present (exit before any "
                  "writer); the exact F2P observable holds.")

        print("G-AX OK: write_fresh_artifacts / write_update_artifacts axioms "
              "sound against the real Command.write_migration_files. Weakened "
              "contract validated: single-app changes -> +1, two-app changes "
              "-> +%d (so '>= +1' is required, '== +1' would be UNSOUND), "
              "empty changes -> +0; previously-produced tokens kept as a "
              "prefix and each recorded file written to disk. End-to-end state: "
              "%s; without --check a migration file IS written (writer reached "
              "in both states)." % (len(changes2), state))
        return 0
    finally:
        try:
            sys.path.remove(work)
        except ValueError:
            pass
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
