# P2 adversarial audit — django__django-16116

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
"""Positive control + Req1 core: `makemigrations --check` with pending changes
exits NON-ZERO *and* writes NO migration file.

HOLDS iff: call_command raises SystemExit(!=0) AND the app's migrations dir has
no numbered migration file afterward.

On the PATCHED tree this must hold. On BASE it must FAIL (base writes the file
before exiting non-zero) -> discriminating power.
"""
import os, sys, tempfile, shutil, textwrap

def build_project():
    root = tempfile.mkdtemp(prefix="mmproj_")
    app = os.path.join(root, "testapp")
    os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.db import models
            class Widget(models.Model):
                name = models.CharField(max_length=10)
        """))
    with open(os.path.join(app, "apps.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.apps import AppConfig
            class TestappConfig(AppConfig):
                name = 'testapp'
                default_auto_field = 'django.db.models.AutoField'
        """))
    # empty migrations package so makemigrations writes 0001_initial into it
    mig = os.path.join(app, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return root, mig

def main():
    root, mig = build_project()
    sys.path.insert(0, root)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["testapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management import call_command

    exit_code = None
    try:
        call_command("makemigrations", check_changes=True, verbosity=0)
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    except Exception as e:
        print("UNEXPECTED EXCEPTION:", repr(e))
        return 1

    written = [f for f in os.listdir(mig)
               if f.endswith(".py") and f != "__init__.py"]
    print("exit_code=", exit_code, " migration_files_written=", written)

    ok = (exit_code not in (None, 0)) and (len(written) == 0)
    shutil.rmtree(root, ignore_errors=True)
    if ok:
        print("HOLD: --check exited nonzero and wrote no migration file")
        return 0
    print("FAIL: expected nonzero exit and no files written")
    return 1

sys.exit(main())
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
"""Req 2.1 / 2.3 regression: normal `makemigrations` (NO --check, no update)
with pending changes SHALL write a new migration file and SHALL NOT raise a
non-zero early exit.

HOLDS iff: call_command returns without SystemExit AND 0001_initial.py exists.
"""
import os, sys, tempfile, shutil, textwrap

def build_project():
    root = tempfile.mkdtemp(prefix="mmproj_")
    app = os.path.join(root, "testapp")
    os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.db import models
            class Widget(models.Model):
                name = models.CharField(max_length=10)
        """))
    with open(os.path.join(app, "apps.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.apps import AppConfig
            class TestappConfig(AppConfig):
                name = 'testapp'
                default_auto_field = 'django.db.models.AutoField'
        """))
    mig = os.path.join(app, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return root, mig

def main():
    root, mig = build_project()
    sys.path.insert(0, root)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["testapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management import call_command

    raised = None
    try:
        call_command("makemigrations", verbosity=0)  # no check_changes
    except SystemExit as e:
        raised = e.code
    except Exception as e:
        print("UNEXPECTED EXCEPTION:", repr(e))
        return 1

    written = [f for f in os.listdir(mig)
               if f.endswith(".py") and f != "__init__.py"]
    print("systemexit=", raised, " migration_files_written=", written)
    ok = (raised is None) and any(f.startswith("0001") for f in written)
    shutil.rmtree(root, ignore_errors=True)
    if ok:
        print("HOLD: normal makemigrations wrote migration and did not early-exit")
        return 0
    print("FAIL: expected a written migration and no SystemExit")
    return 1

sys.exit(main())
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
"""Req 3: with NO model changes, `makemigrations --check` completes with exit 0
(SHALL NOT request non-zero early exit) and writes no file.

Set up an app whose models EXACTLY match an already-present migration, so
change detection reports nothing.
HOLDS iff: no SystemExit (or exit code 0) AND no new numbered migration written
beyond the pre-existing 0001_initial.
"""
import os, sys, tempfile, shutil, textwrap

def build_project():
    root = tempfile.mkdtemp(prefix="mmproj_")
    app = os.path.join(root, "testapp")
    os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.db import models
            class Widget(models.Model):
                name = models.CharField(max_length=10)
        """))
    with open(os.path.join(app, "apps.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.apps import AppConfig
            class TestappConfig(AppConfig):
                name = 'testapp'
                default_auto_field = 'django.db.models.AutoField'
        """))
    mig = os.path.join(app, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return root, mig

def main():
    root, mig = build_project()
    sys.path.insert(0, root)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["testapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management import call_command

    # First, create the initial migration so models are fully migrated.
    call_command("makemigrations", verbosity=0)
    before = sorted(f for f in os.listdir(mig)
                    if f.endswith(".py") and f != "__init__.py")

    # Now run --check with NO pending changes; must not error, must not write.
    raised = "none"
    try:
        call_command("makemigrations", check_changes=True, verbosity=0)
    except SystemExit as e:
        raised = e.code if e.code is not None else 0
    except Exception as e:
        print("UNEXPECTED EXCEPTION:", repr(e))
        return 1

    after = sorted(f for f in os.listdir(mig)
                   if f.endswith(".py") and f != "__init__.py")
    print("before=", before, " after=", after, " raised=", raised)
    ok = (raised in ("none", 0)) and (before == after)
    shutil.rmtree(root, ignore_errors=True)
    if ok:
        print("HOLD: --check with no changes exited 0 and wrote nothing")
        return 0
    print("FAIL: --check with no changes should exit 0 and write nothing")
    return 1

sys.exit(main())
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
"""Req 1.3 / 1.4 (update-mode branch): `makemigrations --check --update` with
pending changes SHALL exit non-zero WITHOUT rewriting the latest existing
migration file.

Scenario: create 0001_initial, then add a field to the model so a change is
pending, then run --check --update. The pre-existing latest migration file's
CONTENT must be byte-identical afterward (no merge/rewrite), and exit nonzero.
"""
import os, sys, tempfile, shutil, textwrap

def write_models(app, extra=""):
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(textwrap.dedent(f"""
            from django.db import models
            class Widget(models.Model):
                name = models.CharField(max_length=10)
            {extra}
        """))

def build_project():
    root = tempfile.mkdtemp(prefix="mmproj_")
    app = os.path.join(root, "testapp")
    os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    write_models(app)
    with open(os.path.join(app, "apps.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.apps import AppConfig
            class TestappConfig(AppConfig):
                name = 'testapp'
                default_auto_field = 'django.db.models.AutoField'
        """))
    mig = os.path.join(app, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return root, app, mig

def main():
    root, app, mig = build_project()
    sys.path.insert(0, root)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["testapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management import call_command
    from django.apps import apps as global_apps

    # 0001_initial
    call_command("makemigrations", verbosity=0)
    latest = os.path.join(mig, "0001_initial.py")
    orig = open(latest).read()

    # Introduce a change: add a field. Rewrite models on disk AND update the
    # in-memory model state so autodetector sees a diff without a full reload.
    from django.db import models
    Widget = global_apps.get_model("testapp", "Widget")
    Widget.add_to_class("qty", models.IntegerField(default=0))

    raised = "none"
    try:
        call_command("makemigrations", check_changes=True, update=True, verbosity=0)
    except SystemExit as e:
        raised = e.code if e.code is not None else 0
    except Exception as e:
        print("UNEXPECTED EXCEPTION:", repr(e))
        return 1

    after = open(latest).read() if os.path.exists(latest) else "<MISSING/RENAMED>"
    files = sorted(f for f in os.listdir(mig)
                   if f.endswith(".py") and f != "__init__.py")
    unchanged = (after == orig)
    print("raised=", raised, " latest_unchanged=", unchanged, " files=", files)
    ok = (raised not in ("none", 0)) and unchanged and files == ["0001_initial.py"]
    shutil.rmtree(root, ignore_errors=True)
    if ok:
        print("HOLD: --check --update exited nonzero and did not rewrite latest migration")
        return 0
    print("FAIL: expected nonzero exit and untouched latest migration")
    return 1

sys.exit(main())
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
"""Req 2.2 regression: normal `makemigrations --update` (NO --check) with a
pending change SHALL write the change INTO the latest existing migration file
(rewrite it), not early-exit.

Scenario: create 0001_initial, add a field, run --update (no check). The latest
migration file content must CHANGE (the new field folded in) and no SystemExit.
"""
import os, sys, tempfile, shutil, textwrap

def build_project():
    root = tempfile.mkdtemp(prefix="mmproj_")
    app = os.path.join(root, "testapp")
    os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.db import models
            class Widget(models.Model):
                name = models.CharField(max_length=10)
        """))
    with open(os.path.join(app, "apps.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.apps import AppConfig
            class TestappConfig(AppConfig):
                name = 'testapp'
                default_auto_field = 'django.db.models.AutoField'
        """))
    mig = os.path.join(app, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return root, app, mig

def main():
    root, app, mig = build_project()
    sys.path.insert(0, root)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["testapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management import call_command
    from django.apps import apps as global_apps
    from django.db import models

    call_command("makemigrations", verbosity=0)
    latest = os.path.join(mig, "0001_initial.py")
    orig = open(latest).read()

    Widget = global_apps.get_model("testapp", "Widget")
    Widget.add_to_class("qty", models.IntegerField(default=0))

    raised = "none"
    try:
        call_command("makemigrations", update=True, verbosity=0)
    except SystemExit as e:
        raised = e.code if e.code is not None else 0
    except Exception as e:
        print("UNEXPECTED EXCEPTION:", repr(e))
        return 1

    after = open(os.path.join(mig,
             sorted(f for f in os.listdir(mig)
                    if f.endswith('.py') and f != '__init__.py')[0])).read() \
            if os.path.exists(latest) else ""
    # After --update the latest file is renamed/rewritten to include qty.
    files = sorted(f for f in os.listdir(mig)
                   if f.endswith(".py") and f != "__init__.py")
    combined = "".join(open(os.path.join(mig, f)).read() for f in files)
    folded = ("qty" in combined)
    print("raised=", raised, " files=", files, " qty_in_migrations=", folded)
    ok = (raised == "none") and folded
    shutil.rmtree(root, ignore_errors=True)
    if ok:
        print("HOLD: --update (no check) folded change into latest migration, no early exit")
        return 0
    print("FAIL: --update should rewrite latest migration and not early-exit")
    return 1

sys.exit(main())
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
"""Req 4.1: the `--check` option help text SHALL describe exiting non-zero when
migrations are missing AND that it does NOT write those migrations.

HOLDS iff the makemigrations command's --check help string mentions the
non-write behavior (e.g. "don't ... write" / "without writing").
"""
import sys

def main():
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management.commands.makemigrations import Command
    import argparse
    parser = argparse.ArgumentParser()
    Command().add_arguments(parser)
    help_text = None
    for act in parser._actions:
        if "--check" in getattr(act, "option_strings", []):
            help_text = act.help
    print("check_help=", repr(help_text))
    if not help_text:
        print("FAIL: no --check option found")
        return 1
    low = help_text.lower()
    mentions_exit = "non-zero" in low or "nonzero" in low or "exit" in low
    mentions_nowrite = ("write" in low and
                        ("don't" in low or "dont" in low or "not" in low
                         or "without" in low or "no" in low))
    print("mentions_exit=", mentions_exit, " mentions_nowrite=", mentions_nowrite)
    if mentions_exit and mentions_nowrite:
        print("HOLD: help text documents nonzero-exit and no-write behavior")
        return 0
    print("FAIL: help text does not document no-write behavior")
    return 1

sys.exit(main())
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1 core: `makemigrations --check` with pending changes
exits NON-ZERO *and* writes NO migration file.

HOLDS iff: call_command raises SystemExit(!=0) AND the app's migrations dir has
no numbered migration file afterward.

On the PATCHED tree this must hold. On BASE it must FAIL (base writes the file
before exiting non-zero) -> discriminating power.
"""
import os, sys, tempfile, shutil, textwrap

def build_project():
    root = tempfile.mkdtemp(prefix="mmproj_")
    app = os.path.join(root, "testapp")
    os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.db import models
            class Widget(models.Model):
                name = models.CharField(max_length=10)
        """))
    with open(os.path.join(app, "apps.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.apps import AppConfig
            class TestappConfig(AppConfig):
                name = 'testapp'
                default_auto_field = 'django.db.models.AutoField'
        """))
    # empty migrations package so makemigrations writes 0001_initial into it
    mig = os.path.join(app, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return root, mig

def main():
    root, mig = build_project()
    sys.path.insert(0, root)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["testapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management import call_command

    exit_code = None
    try:
        call_command("makemigrations", check_changes=True, verbosity=0)
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    except Exception as e:
        print("UNEXPECTED EXCEPTION:", repr(e))
        return 1

    written = [f for f in os.listdir(mig)
               if f.endswith(".py") and f != "__init__.py"]
    print("exit_code=", exit_code, " migration_files_written=", written)

    ok = (exit_code not in (None, 0)) and (len(written) == 0)
    shutil.rmtree(root, ignore_errors=True)
    if ok:
        print("HOLD: --check exited nonzero and wrote no migration file")
        return 0
    print("FAIL: expected nonzero exit and no files written")
    return 1

sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

instance django__django-16116: makemigrations --check must exit nonzero WITHOUT writing migrations. 6 probes, all HOLD on gold-patched tree.

POSITIVE CONTROL probe_1 (Req 1.1/1.2): --check with pending changes -> SystemExit(1) and NO migration file written. HOLDS patched; VIOLATED at base (base writes 0001_initial.py then exits 1). Discriminating power confirmed.

Regression probes: probe_2 (Req 2.1/2.3 normal makemigrations still writes, no early exit) HOLDS; probe_3 (Req 3.1/3.2 --check with no changes exits 0, writes nothing) HOLDS; probe_4 (Req 1.3/1.4 --check --update exits nonzero without rewriting latest migration) HOLDS; probe_5 (Req 2.2 --update folds change into latest migration, no early exit) HOLDS; probe_6 (Req 4.1 help text documents nonzero-exit + no-write) HOLDS.

CANDIDATE PATCHES both REJECTED by the suite (>=1 exercised, >=1 rejected satisfied; none passed all probes):
- weak_writes.diff: help-text-only change, no early-exit logic. REJECTED by probe_1 (writes 0001_initial.py, still exits nonzero -> base behavior). Would not resolve F2P.
- weak_partial.diff: adds sys.exit(1) only inside the non-update else-branch (before write_migration_files), leaving the update-mode branch writing before exit. Satisfies Req1 core (probe_1/2/3/5 HOLD) but REJECTED by probe_4: with --check --update the write_to_last_migration_files writer runs and renames 0001_initial.py -> 0001_initial_updated.py, violating Req 1.3/1.4.

No requirements-conforming candidate escaped the suite. Verdict SOUND. Runner: SBU_AUDIT_TIMEOUT/probe timeouts fine; all runs completed (no INCONCLUSIVE).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
"""Positive control + Req1 core: `makemigrations --check` with pending changes
exits NON-ZERO *and* writes NO migration file.

HOLDS iff: call_command raises SystemExit(!=0) AND the app's migrations dir has
no numbered migration file afterward.

On the PATCHED tree this must hold. On BASE it must FAIL (base writes the file
before exiting non-zero) -> discriminating power.
"""
import os, sys, tempfile, shutil, textwrap

def build_project():
    root = tempfile.mkdtemp(prefix="mmproj_")
    app = os.path.join(root, "testapp")
    os.makedirs(app)
    open(os.path.join(app, "__init__.py"), "w").close()
    with open(os.path.join(app, "models.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.db import models
            class Widget(models.Model):
                name = models.CharField(max_length=10)
        """))
    with open(os.path.join(app, "apps.py"), "w") as f:
        f.write(textwrap.dedent("""
            from django.apps import AppConfig
            class TestappConfig(AppConfig):
                name = 'testapp'
                default_auto_field = 'django.db.models.AutoField'
        """))
    # empty migrations package so makemigrations writes 0001_initial into it
    mig = os.path.join(app, "migrations")
    os.makedirs(mig)
    open(os.path.join(mig, "__init__.py"), "w").close()
    return root, mig

def main():
    root, mig = build_project()
    sys.path.insert(0, root)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        INSTALLED_APPS=["testapp"],
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        USE_TZ=True,
    )
    django.setup()
    from django.core.management import call_command

    exit_code = None
    try:
        call_command("makemigrations", check_changes=True, verbosity=0)
    except SystemExit as e:
        exit_code = e.code if e.code is not None else 0
    except Exception as e:
        print("UNEXPECTED EXCEPTION:", repr(e))
        return 1

    written = [f for f in os.listdir(mig)
               if f.endswith(".py") and f != "__init__.py"]
    print("exit_code=", exit_code, " migration_files_written=", written)

    ok = (exit_code not in (None, 0)) and (len(written) == 0)
    shutil.rmtree(root, ignore_errors=True)
    if ok:
        print("HOLD: --check exited nonzero and wrote no migration file")
        return 0
    print("FAIL: expected nonzero exit and no files written")
    return 1

sys.exit(main())
```

Prepatch bug re-encoded as an attack: `True`.

instance django__django-16116: makemigrations --check must exit nonzero WITHOUT writing migrations. 6 probes, all HOLD on gold-patched tree.

POSITIVE CONTROL probe_1 (Req 1.1/1.2): --check with pending changes -> SystemExit(1) and NO migration file written. HOLDS patched; VIOLATED at base (base writes 0001_initial.py then exits 1). Discriminating power confirmed.

Regression probes: probe_2 (Req 2.1/2.3 normal makemigrations still writes, no early exit) HOLDS; probe_3 (Req 3.1/3.2 --check with no changes exits 0, writes nothing) HOLDS; probe_4 (Req 1.3/1.4 --check --update exits nonzero without rewriting latest migration) HOLDS; probe_5 (Req 2.2 --update folds change into latest migration, no early exit) HOLDS; probe_6 (Req 4.1 help text documents nonzero-exit + no-write) HOLDS.

CANDIDATE PATCHES both REJECTED by the suite (>=1 exercised, >=1 rejected satisfied; none passed all probes):
- weak_writes.diff: help-text-only change, no early-exit logic. REJECTED by probe_1 (writes 0001_initial.py, still exits nonzero -> base behavior). Would not resolve F2P.
- weak_partial.diff: adds sys.exit(1) only inside the non-update else-branch (before write_migration_files), leaving the update-mode branch writing before exit. Satisfies Req1 core (probe_1/2/3/5 HOLD) but REJECTED by probe_4: with --check --update the write_to_last_migration_files writer runs and renames 0001_initial.py -> 0001_initial_updated.py, violating Req 1.3/1.4.

No requirements-conforming candidate escaped the suite. Verdict SOUND. Runner: SBU_AUDIT_TIMEOUT/probe timeouts fine; all runs completed (no INCONCLUSIVE).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probed via nl_attack on the gold-patched tree. Confirmed exact source of Command.handle else-branch: `else:\n  if check_changes: sys.exit(1)\n  if self.update: self.write_to_last_migration_files(changes)\n  else: self.write_migration_files(changes)`. Confirmed live help text via parser _actions. The requirements pin the changed observable behavior (early exit-before-write) at the correct boundary — the full changes-detected branch, not a narrow slice — and Requirement 2 correctly preserves both write paths keyed on update mode. No mandated-but-absent, forbidden-but-present, or invented behavior.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The document localizes the change to makemigrations.py Command.handle and names the migration-writing helpers (write_migration_files / write_to_last_migration_files, referenced as 'fresh-file writer'/'update-last-migration writer') and the pre-existing check_changes/update options — all legitimate localization, not fix-invented identifiers. The hidden test (test_makemigrations_check) merely asserts SystemExit plus os.path.exists(tmpdir) is False; the requirements translate this into behavioral obligations (exit non-zero without writing/merging any migration file) without transmitting test names, paths, ids, or parametrization. Requirement 4 paraphrases the gold help-text change ('as not writing those migrations') rather than quoting the verbatim gold string ('and don't actually write them.'). The migrate/optimizemigration --check consistency framing is public via problem_statement. No case enumeration mirrors the test structure.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
