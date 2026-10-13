#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14376.

This bundle consumes NO @ContractOnly axioms: the modelled operation (the
database-name selection used when assembling the client command line) is
modelled DEEPLY in model.py. What G-AX validates here is the **A-reference** —
that the deep model faithfully captures the real Python semantics of the
changed client-argument assembly.

The deep model `select_name` (model.py pure region) encodes the three-level
precedence:

    select_name(opt_database, opt_db, settings_name) =
        opt_database        if the non-deprecated option is present
        else opt_db         if the legacy option is present
        else settings_name

and `resolve_db_arg` appends the selected name as a trailing positional
argument exactly when it is non-empty.

This check executes the REAL (gold-patched) Django
``DatabaseClient.settings_to_cmd_args_env`` for the MySQL backend on a battery
of option configurations and asserts that the trailing positional database
argument it produces is EXACTLY the selected name under the modelled
precedence. The discriminating case (both the non-deprecated and the legacy
option present, with different values) pins that the non-deprecated option
wins — the behaviour the pre-patch code got wrong.

Run inside the official SWE-bench container for the instance, where Django is
importable. Exit 0 iff every obligation holds. Outside the container (Django
absent) it prints ``G-AX SKIP`` and returns 0; the orchestrator runs it
in-container.

PATCH STATE (reproducibility): the A-reference models a *changed* function, so
it MUST be validated against the GOLD-PATCHED callee. The eval image is checked
out at ``base_commit`` (PRE-patch), where ``settings_to_cmd_args_env`` selects
``OPTIONS.get('db', NAME)`` and NEVER examines the non-deprecated ``database``
option — the bug. This script therefore applies the bundle's gold ``patch.diff``
to the in-container ``/testbed`` checkout BEFORE importing Django, so the deep
model is checked against the post-patch callee it abstracts. The apply is
idempotent: if the source already carries the post-patch ``database`` selection
(e.g. the harness was invoked with ``apply_gold=True``), the script detects it
and skips re-applying. ``git apply`` failures are surfaced explicitly (rc 3),
never swallowed.
"""
import os
import random
import subprocess
import sys

# The changed source file and a fragment present ONLY in the post-patch db-name
# selection (the outer non-deprecated 'database' option). At base_commit the db
# chain is `db = settings_dict['OPTIONS'].get('db', settings_dict['NAME'])` and
# the token 'database' is absent from client.py; the gold patch introduces it.
_CHANGED_FILE = "django/db/backends/mysql/client.py"
_POSTPATCH_MARKER = "'database'"


def _ensure_postpatch_source():
    """Make the in-container Django carry the post-patch db-name selection.

    The eval image is base_commit (pre-patch). The A-reference abstracts the
    POST-patch ``settings_to_cmd_args_env`` selection, so we apply the bundle's
    gold ``patch.diff`` to the writable ``/testbed`` checkout before importing
    Django. Idempotent: if the post-patch ``'database'`` selection is already
    present (the harness applied the patch via apply_gold, or a prior run), we
    do nothing. Returns None on success or a string error (caller exits rc 3)."""
    testbed = os.environ.get("TESTBED", "/testbed")
    changed = os.path.join(testbed, _CHANGED_FILE)
    if not os.path.isfile(changed):
        # Not running in the instance container (no /testbed checkout). Fall
        # through to the import-based SKIP; the orchestrator runs in-container.
        return None
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER in fh.read():
                return None  # already post-patch (apply_gold or prior apply)
    except OSError as exc:
        return "could not read %s: %r" % (changed, exc)

    # Locate the bundle patch. Under the standard recipe the whole bundle dir is
    # mounted read-only at /work; apply_gold also mounts it at /gold.patch.
    candidates = ["/work/patch.diff", "/gold.patch",
                  os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "patch.diff")]
    patch_path = next((p for p in candidates if os.path.exists(p)), None)
    if patch_path is None:
        return ("post-patch source required but no patch.diff found in %r"
                % (candidates,))

    proc = subprocess.run(["git", "apply", "-v", patch_path],
                          cwd=testbed, capture_output=True, text=True)
    if proc.returncode != 0:
        return ("git apply %s failed (rc %d): %s"
                % (patch_path, proc.returncode,
                   (proc.stderr or proc.stdout).strip()))
    # Confirm the apply actually produced the post-patch selection.
    try:
        with open(changed, "r") as fh:
            if _POSTPATCH_MARKER not in fh.read():
                return ("patch applied but post-patch selection %r still absent "
                        "in %s" % (_POSTPATCH_MARKER, changed))
    except OSError as exc:
        return "could not re-read %s: %r" % (changed, exc)
    return None


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


# --- model.py reference: the deep model select_name + the append decision -----

_ABSENT = object()


def model_select_name(opt_database, opt_db, settings_name):
    """Reference implementation of model.py's select_name (three-level
    precedence). A present option short-circuits the fallback even when its
    stored value is the empty string."""
    if opt_database is not _ABSENT:
        return opt_database
    if opt_db is not _ABSENT:
        return opt_db
    return settings_name


def model_trailing_db_arg(opt_database, opt_db, settings_name):
    """The trailing positional database argument the model predicts: the
    selected name when non-empty, otherwise no trailing argument (None)."""
    selected = model_select_name(opt_database, opt_db, settings_name)
    return selected if len(selected) > 0 else None


def real_trailing_db_arg(settings_to_cmd_args_env, opt_database, opt_db,
                         settings_name):
    """Run the REAL gold-patched callee and extract the database it appends as
    the trailing positional argument. The settings dict carries no user / host
    / port / charset / ssl, so the only trailing positional argument (if any)
    is the database name."""
    options = {}
    if opt_database is not _ABSENT:
        options['database'] = opt_database
    if opt_db is not _ABSENT:
        options['db'] = opt_db
    settings_dict = {
        'NAME': settings_name,
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
        'OPTIONS': options,
    }
    args, env = settings_to_cmd_args_env(settings_dict, [])
    # args[0] is the executable name ('mysql'); with no user/host/port/charset/
    # ssl, any further entry is the trailing database positional argument.
    assert args[0] == 'mysql', "unexpected executable token: %r" % (args[0],)
    rest = args[1:]
    if not rest:
        return None
    assert len(rest) == 1, (
        "expected at most one trailing positional (the database) but got %r "
        "for options=%r name=%r" % (rest, options, settings_name))
    return rest[0]


def main():
    # Ensure the in-container source carries the POST-patch db-name selection the
    # A-reference abstracts (the eval image ships base_commit / pre-patch). Must
    # happen BEFORE importing the MySQL client so the patched module is loaded.
    err = _ensure_postpatch_source()
    if err is not None:
        print("G-AX FAIL: could not establish post-patch source: %s" % err)
        return 3

    try:
        _configure_django()
        from django.db.backends.mysql.client import DatabaseClient
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django MySQL backend not importable here: %r" % (exc,))
        return 0

    callee = DatabaseClient.settings_to_cmd_args_env

    observations = 0
    saw_discriminator = False

    # Boundary configurations over the two option keys x the settings name.
    names = ['settingdbname', 'optiondbname', 'deprecateddbname', '']
    values_or_absent = [_ABSENT, 'optiondbname', 'deprecateddbname', 'altname', '']

    for settings_name in names:
        for opt_database in values_or_absent:
            for opt_db in values_or_absent:
                expected = model_trailing_db_arg(opt_database, opt_db, settings_name)
                observed = real_trailing_db_arg(callee, opt_database, opt_db,
                                                settings_name)
                assert observed == expected, (
                    "database selection mismatch: opt_database=%r opt_db=%r "
                    "NAME=%r -> real %r, model %r"
                    % (opt_database, opt_db, settings_name, observed, expected))
                # Discriminator: both options present with different non-empty
                # values => the non-deprecated 'database' option must win.
                if (opt_database is not _ABSENT and opt_db is not _ABSENT
                        and opt_database != opt_db and len(opt_database) > 0):
                    assert observed == opt_database, (
                        "non-deprecated option must take precedence: got %r, "
                        "expected %r" % (observed, opt_database))
                    saw_discriminator = True
                observations += 1

    # Randomized fuzz over the same shape.
    rng = random.Random(14376)
    pool = [_ABSENT, '', 'a', 'db1', 'db2', 'name', 'X', 'optiondbname']
    for _ in range(3000):
        settings_name = rng.choice(['', 'n', 'settingdbname', 'zzz'])
        opt_database = rng.choice(pool)
        opt_db = rng.choice(pool)
        expected = model_trailing_db_arg(opt_database, opt_db, settings_name)
        observed = real_trailing_db_arg(callee, opt_database, opt_db, settings_name)
        assert observed == expected, (
            "fuzz mismatch: opt_database=%r opt_db=%r NAME=%r -> real %r model %r"
            % (opt_database, opt_db, settings_name, observed, expected))
        observations += 1

    assert saw_discriminator, (
        "test battery did not exercise the non-deprecated-vs-legacy "
        "precedence discriminator")

    print("G-AX OK: deep model select_name / resolve_db_arg validated against "
          "the real gold-patched DatabaseClient.settings_to_cmd_args_env over "
          "%d observations; the non-deprecated database option takes precedence "
          "over the legacy option over the settings name, appended iff non-empty."
          % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
