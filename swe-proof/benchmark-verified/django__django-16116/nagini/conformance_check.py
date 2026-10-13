#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16116 (nagini).

SHADOW
------
The impl region of ``model.py``'s ``produce_changes_or_report``, copied VERBATIM
below with only the contract calls stripped (there are none inside the region
itself — the region is the four lines between ``# impl-start`` and
``# impl-end``; the ``Requires``/``Ensures``/``Exsures`` calls sit above it and
are deleted). No restructuring, no renaming: the shadow's text is

    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)

``CheckFailureExit`` is copied from model.py. There are no module-level ``@Pure``
helpers (model.py's pure region is empty), so nothing else is copied over. The
PSeq shim is present because the model's carrier vocabulary is ``ToSeq``/``take``
(used by the contracts) — the impl region itself only appends, and the shim is
used by the driver to state the prefix-preservation comparison the same way the
model does.

The two ``@ContractOnly`` callees have no body to copy, so — per the contract —
they are resolved to the REAL repo functions they axiomatise (mapping.md §1/§3):

    write_update_artifacts(store)  ->  Command.write_to_last_migration_files
    write_fresh_artifacts(store)   ->  Command.write_migration_files

They are genuinely invoked (with real ``changes`` dicts built by the real
``MigrationAutodetector``, on a real ``Command`` whose ``written_files`` has been
pre-seeded to the model store's prefix), so the axioms are exercised rather than
assumed: each invocation asserts the real writer left the pre-seeded prefix
intact and reports the paths it actually appended.

ORACLE
------
The REAL patched repo function, CALLED — not transliterated. mapping.md §1 binds
the model to the ``else:`` (changes-present) arm of
``django/core/management/commands/makemigrations.py`` ``Command.handle``
(:250-256 pre-patch / :251-256 post-patch). The gate git-applies patch.diff to
/testbed and sets PYTHONPATH before this script runs, so the real, patched
``handle`` is what executes here. It is driven end-to-end via
``call_command(Command(), <app labels>, "--check"?, "--update"?)`` against a
fixture app tree that has genuine pending model changes, i.e. the run really
does enter the modeled changes-present branch (the driver asserts the real
autodetector reports a non-empty ``changes`` for the fixture, so an input that
silently missed the branch cannot pass).

Observed from that real run:
  * whether the branch performed the check-mode failure-exit — the real
    ``sys.exit(1)`` surfacing as ``SystemExit(1)`` out of ``call_command``;
  * the real ``Command.written_files`` post-state (mapping.md §1 binds the model
    store to this list) — and, as a cross-check, the migration files actually
    on disk;
  * for each appended entry, WHICH producing step emitted it. This is read off
    the real execution, not inferred: the two real writer methods are wrapped in
    delegating observers that record entry/exit and fully call the real method,
    and each entry appended to ``written_files`` is labelled by the OUTERMOST
    writer in progress when it appeared (``write_to_last_migration_files``
    delegates to ``write_migration_files``, and mapping.md §2 defines the token
    kind by the producing step: 1 = fold-into-most-recent, 0 = fresh file).
    Nothing is stubbed — the real writers serialize real migrations to disk (and
    run black) on every observation.

The branch the gold patch changed IS exercised, and is the discriminating case:
for ``check_mode=True`` the shadow says "raise, store unchanged", and the real
patched run must show ``SystemExit(1)`` with ``written_files`` still equal to the
prefix. Under the PRE-patch order the real run writes a migration artefact and
THEN exits, so the oracle would report a grown store and this check would fail.
The check-mode case is not special-cased anywhere.

TYPE BRIDGE (mapping.md §2, inverted)
-------------------------------------
  * ``store: List[int]`` <-> ``Command.written_files`` (a list of produced
    migration-file paths). Each produced file is one token; the token VALUE is
    the KIND of the producing step (0 = ``write_migration_files`` fresh file,
    1 = ``write_to_last_migration_files`` fold-into-most-recent). Inverting:
    a model prefix of length k is realized as k real pre-existing produced-file
    paths pre-seeded into ``written_files`` (real files in a scratch dir, so the
    real writer's ``run_formatters`` pass sees real paths); a real appended path
    maps back to 0 or 1 by its producing step. Prefix token VALUES are arbitrary
    ints (the model's Requires constrains nothing beyond ``list_pred``): they are
    carried through the bridge by position, and the real side asserts its
    pre-seeded prefix strings came back byte-identical, which is the real
    observation standing behind the model's prefix-preservation clause.
  * ``check_mode: bool`` <-> the ``--check`` flag (``options["check_changes"]``);
    identity.
  * ``update_variant: bool`` <-> the ``--update`` flag (``self.update``);
    identity.
  * ``raise CheckFailureExit()`` <-> the real ``sys.exit(1)`` / ``SystemExit(1)``
    (mapping.md §2: a builtin exception in an ``Exsures`` crashes the Nagini
    translator, so the model uses a user-defined class). The driver additionally
    requires the real exit STATUS to be 1, so a different non-zero status would
    be a disagreement.
  * the ``changes`` dict is not a model parameter (mapping.md §2: the branch's
    precondition is "changes present"). Its size is a real, behaviourally
    visible dimension of the writers' effect (one produced artefact per pending
    migration), so it is a generated dimension here: ``napps`` in {1, 2} gives a
    real ``changes`` of 1 or 2 migrations and hence a real store growth of +1 or
    +2. This is exactly why the axiom is ``>= +1`` and not ``== +1``
    (mapping.md §3), and both growths are exercised.
  * non-dry-run only (mapping.md §3 "Flag dependency"): the writers produce
    artefacts only when ``dry_run`` is False, which is the configuration the
    behaviour is specified for and the one the F2P test uses.

INPUT PLAN (>= 1e5 Requires-satisfying inputs)
----------------------------------------------
The modeled input space factors into a FINITE decision space and an unbounded
but behaviourally inert store prefix:

  * decision space = ``check_mode`` x ``update_variant`` x ``napps``
    = 2 x 2 x 2 = 8 classes. This is ENUMERATED EXHAUSTIVELY against the real
    patched ``handle``, each class run REPEATEDLY (``REAL_REPEATS``) and required
    to reproduce the identical observation — the real oracle must be a function
    of the class before any of it may be reused. Per clause 4 of the worker
    contract this exhaustive enumeration is stronger than sampling: every branch
    of the impl region (check-mode raise; update dispatch; fresh dispatch) is
    taken by real code, at both real growth amounts.
  * prefix leg: for every (``update_variant``, ``napps``) class the REAL writer
    is additionally invoked directly at real pre-seeded prefixes of lengths
    0,1,2,3,5,8 — the real observation that the writers are append-only and
    prefix-independent, which is what licenses lifting a class observation to an
    arbitrary prefix. The handle-observed kinds and the directly-invoked writer's
    kinds are cross-checked against each other.
  * boundary inputs: empty store; singleton store; stores whose tokens are
    non-{0,1} ints (negative / zero / large), which must be copied through
    untouched; both napps; all four flag pairs; the exact F2P shape
    (``check_mode=True`` — ``makemigrations --check`` with pending changes, the
    case ``MakeMigrationsTests.test_makemigrations_check`` pins).
  * fuzz to the count: ``N_FUZZ`` = 100000 further inputs over the SAME space
    (random flags, random napps, random prefix length 0..8 with a long-prefix
    tail, random arbitrary int tokens), pinned seed ``SEED`` = 16116 (recorded
    in mapping.md §G-CONF).

REAL-CALL BUDGET / REPLAY (stated plainly, because it bounds what the fuzz
proves): each real patched-``handle`` run costs ~0.2-0.7s (it serializes real
migrations and runs black), so 1e5 live runs is not physically available inside
the gate's container budget. The real function is therefore invoked live for
EVERY equivalence class (all 8, several times each, plus 12 direct real writer
invocations across 6 prefix lengths = O(100) real invocations), and the >= 1e5
fuzz inputs replay those RECORDED REAL observations. The replay keeps its
refuting power over the whole space: the shadow's store growth comes from the
recorded real WRITER observation keyed by (update_variant, napps) while the
oracle's comes from the recorded real HANDLE observation keyed by
(check_mode, update_variant, napps), so a shadow that dispatched to the wrong
writer, dispatched when the real branch exited, or exited when the real branch
wrote, disagrees — the two sides are never read from the same recorded slot.
What replay does NOT re-prove per fuzz input is the writers' prefix-independence;
that is established by real invocation on the prefix leg above.

Exit 0 iff zero disagreements. On a disagreement the input and both outputs are
printed and the exit status is 1. stdlib + Django (the package under test) only.
"""
import json
import os
import random
import shutil
import sys
import tempfile

SEED = 16116
N_FUZZ = 100000
REAL_REPEATS = 3
PREFIX_LENS = (0, 1, 2, 3, 5, 8)

APP_LABELS = ("confmm1", "confmm2")


# ---------------------------------------------------------------------------
# Nagini carrier shim: PSeq is an immutable sequence (take/drop/+/len/[]/==),
# ToSeq materializes one from a list. Used to state the prefix comparison the
# way model.py's contracts do.
# ---------------------------------------------------------------------------

class PSeq(object):
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

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __repr__(self):
        return "PSeq%r" % (self._t,)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# Copied from model.py: the check-mode failure outcome.
# ---------------------------------------------------------------------------

class CheckFailureExit(Exception):
    pass


# ---------------------------------------------------------------------------
# The two @ContractOnly callees. No body to copy: each dispatches to the REAL
# repo callee it axiomatises (mapping.md §1/§3) through the active callee
# binding. LiveCallees actually runs the real writer; ReplayCallees applies a
# previously RECORDED real writer observation (see the docstring's replay note).
# ---------------------------------------------------------------------------

_CALLEES = None          # set by the driver before each shadow run


def write_update_artifacts(store):
    """@ContractOnly in model.py -> Command.write_to_last_migration_files."""
    _CALLEES.write_update(store)


def write_fresh_artifacts(store):
    """@ContractOnly in model.py -> Command.write_migration_files."""
    _CALLEES.write_fresh(store)


# ---------------------------------------------------------------------------
# SHADOW: model.py's impl region, verbatim, contract calls stripped.
# ---------------------------------------------------------------------------

def produce_changes_or_report(store, check_mode, update_variant):
    # impl-start
    if check_mode:
        raise CheckFailureExit()
    if update_variant:
        write_update_artifacts(store)
    else:
        write_fresh_artifacts(store)
    # impl-end


# ---------------------------------------------------------------------------
# Fixture: an app tree with a real pending model change.
# ---------------------------------------------------------------------------

MODELS_PY = """\
from django.db import models


class Widget(models.Model):
    name = models.CharField(max_length=20)
    alpha = models.IntegerField(null=True)

    class Meta:
        app_label = %r
"""

# 0001_initial covers only `name`, so `alpha` is a genuine pending change and the
# modeled changes-present branch is really entered.
INITIAL_PY = '''\
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Widget",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20)),
            ],
        ),
    ]
'''


class RealRepo(object):
    """Drivers for the REAL patched repo code (oracle + @ContractOnly callees)."""

    def __init__(self):
        self.work = tempfile.mkdtemp(prefix="conf16116_")
        self.scratch = os.path.join(self.work, "_prefix_files")
        os.makedirs(self.scratch)
        self.mig_dirs = {}
        sys.path.insert(0, self.work)
        for label in APP_LABELS:
            self.mig_dirs[label] = self._make_app(label)
        self._configure()

    # -- fixture ---------------------------------------------------------

    def _make_app(self, label):
        pkg = os.path.join(self.work, label)
        os.makedirs(pkg)
        open(os.path.join(pkg, "__init__.py"), "w").close()
        with open(os.path.join(pkg, "models.py"), "w") as fh:
            fh.write(MODELS_PY % (label,))
        mig = os.path.join(pkg, "migrations")
        os.makedirs(mig)
        open(os.path.join(mig, "__init__.py"), "w").close()
        return mig

    def _configure(self):
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(
                INSTALLED_APPS=(["django.contrib.contenttypes",
                                 "django.contrib.auth"] + list(APP_LABELS)),
                DATABASES={"default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }},
                MIGRATION_MODULES={a: a + ".migrations" for a in APP_LABELS},
                USE_TZ=False,
            )
        django.setup()

    def reset(self):
        """Restore every fixture app to "0001_initial only, alpha pending" and
        drop the cached migration modules so the real loader re-reads disk."""
        for label in APP_LABELS:
            mig = self.mig_dirs[label]
            for fn in os.listdir(mig):
                if fn == "__init__.py":
                    continue
                fp = os.path.join(mig, fn)
                (shutil.rmtree if os.path.isdir(fp) else os.remove)(fp)
            with open(os.path.join(mig, "0001_initial.py"), "w") as fh:
                fh.write(INITIAL_PY)
        for name in list(sys.modules):
            for label in APP_LABELS:
                if name == label + ".migrations" or name.startswith(
                        label + ".migrations."):
                    del sys.modules[name]

    def labels(self, napps):
        return list(APP_LABELS[:napps])

    def on_disk(self, napps):
        out = []
        for label in self.labels(napps):
            mig = self.mig_dirs[label]
            out.extend(
                "%s/%s" % (label, f) for f in sorted(os.listdir(mig))
                if f.endswith(".py") and f != "__init__.py")
        return sorted(out)

    def prefix_paths(self, n):
        """n real pre-existing produced-file paths realizing a model prefix of
        length n (real files, so the real writer's run_formatters pass and any
        path handling see genuine paths)."""
        paths = []
        for i in range(n):
            p = os.path.join(self.scratch, "prior_%04d.py" % i)
            if not os.path.exists(p):
                with open(p, "w") as fh:
                    fh.write("# previously produced artefact %d\n" % i)
            paths.append(p)
        return paths

    # -- real changes dict / real Command --------------------------------

    def real_changes(self, napps):
        from django.apps import apps
        from django.db.migrations.autodetector import MigrationAutodetector
        from django.db.migrations.loader import MigrationLoader
        from django.db.migrations.questioner import (
            NonInteractiveMigrationQuestioner,
        )
        from django.db.migrations.state import ProjectState
        labels = set(self.labels(napps))
        loader = MigrationLoader(None, ignore_no_migrations=True)
        questioner = NonInteractiveMigrationQuestioner(
            specified_apps=labels, dry_run=False, verbosity=0)
        autodetector = MigrationAutodetector(
            loader.project_state(), ProjectState.from_apps(apps), questioner)
        return autodetector.changes(graph=loader.graph, trim_to_apps=labels,
                                    convert_apps=labels, migration_name=None)

    def _bare_command(self, update):
        from django.core.management.commands.makemigrations import Command
        from io import StringIO
        cmd = Command()
        cmd.verbosity = 0
        cmd.interactive = False
        cmd.dry_run = False
        cmd.merge = False
        cmd.empty = False
        cmd.scriptable = False
        cmd.include_header = True
        cmd.update = update
        cmd.migration_name = None
        cmd.written_files = []
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        return cmd

    # -- ORACLE: the real patched Command.handle -------------------------

    def run_real_handle(self, napps, check_mode, update_variant):
        """Run the REAL patched makemigrations end-to-end on the fixture.

        Returns dict(exit_code=None|int, kinds=[0|1,...], writers=[...],
        on_disk=[...]) where kinds labels each entry the real run appended to
        Command.written_files by its producing step (mapping.md §2)."""
        from django.core.management import call_command
        from django.core.management.commands.makemigrations import Command
        from io import StringIO

        self.reset()
        # The modeled branch is the changes-present one: assert the real
        # autodetector really does report pending changes for this fixture, so
        # an input that silently missed the branch cannot pass.
        pending = self.real_changes(napps)
        if not pending:
            raise AssertionError(
                "fixture invalid: real autodetector reports NO pending changes "
                "for napps=%d; the modeled changes-present branch would not be "
                "entered" % (napps,))
        if len(pending) != napps:
            raise AssertionError(
                "fixture invalid: real autodetector reports %d pending "
                "migrations for napps=%d" % (len(pending), napps))
        self.reset()

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.stderr = StringIO()
        real_last = cmd.write_to_last_migration_files
        real_fresh = cmd.write_migration_files
        outer = []
        writers = []
        kinds = []

        def _label(before, kind):
            after = list(cmd.written_files)
            for _ in after[before:]:
                kinds.append(kind)

        def obs_last(changes, *a, **kw):
            # kind 1 = fold-into-most-recent artefact (mapping.md §2)
            writers.append("update")
            outer.append("update")
            before = len(cmd.written_files)
            try:
                return real_last(changes, *a, **kw)
            finally:
                outer.pop()
                if not outer:
                    _label(before, 1)

        def obs_fresh(changes, *a, **kw):
            # kind 0 = fresh-migration-file artefact, but only when this writer
            # is the OUTERMOST producing step (write_to_last_migration_files
            # delegates to it; those artefacts are of the fold kind).
            inner = bool(outer)
            if not inner:
                writers.append("fresh")
            outer.append("fresh")
            before = len(cmd.written_files)
            try:
                return real_fresh(changes, *a, **kw)
            finally:
                outer.pop()
                if not outer:
                    _label(before, 0)

        cmd.write_to_last_migration_files = obs_last
        cmd.write_migration_files = obs_fresh

        argv = list(self.labels(napps))
        if check_mode:
            argv.append("--check")
        if update_variant:
            argv.append("--update")
        exit_code = "none"
        try:
            call_command(cmd, *argv, verbosity=0)
        except SystemExit as exc:
            exit_code = exc.code
        written = list(getattr(cmd, "written_files", []))
        if len(kinds) != len(written):
            raise AssertionError(
                "kind labelling incomplete: %d labels for %d appended entries"
                % (len(kinds), len(written)))
        return {"exit_code": exit_code, "kinds": kinds, "writers": writers,
                "written": written, "on_disk": self.on_disk(napps)}

    # -- @ContractOnly callees: the real writers, at a real prefix --------

    def run_real_writer(self, napps, update_variant, prefix_len):
        """Invoke the REAL repo writer the axiom stands for, on a real Command
        whose written_files is pre-seeded with `prefix_len` real prior paths.

        Returns (kinds_appended, prefix_preserved: bool)."""
        self.reset()
        changes = self.real_changes(napps)
        if not changes:
            raise AssertionError(
                "fixture invalid: no pending changes for napps=%d" % (napps,))
        cmd = self._bare_command(update_variant)
        seeded = self.prefix_paths(prefix_len)
        cmd.written_files = list(seeded)
        if update_variant:
            cmd.write_to_last_migration_files(changes)
            kind = 1
        else:
            cmd.write_migration_files(changes)
            kind = 0
        after = list(cmd.written_files)
        preserved = after[:prefix_len] == seeded
        return [kind] * (len(after) - prefix_len), preserved


# ---------------------------------------------------------------------------
# Callee bindings for the shadow.
# ---------------------------------------------------------------------------

class LiveCallees(object):
    """@ContractOnly callees resolved to the REAL repo writers, invoked."""

    def __init__(self, real, napps):
        self.real = real
        self.napps = napps
        self.errors = []

    def _run(self, store, update_variant):
        kinds, preserved = self.real.run_real_writer(
            self.napps, update_variant, len(store))
        if not preserved:
            self.errors.append(
                "real %s writer did NOT preserve the pre-seeded produced-file "
                "prefix (len=%d)"
                % ("update" if update_variant else "fresh", len(store)))
        store.extend(kinds)

    def write_update(self, store):
        self._run(store, True)

    def write_fresh(self, store):
        self._run(store, False)


class ReplayCallees(object):
    """@ContractOnly callees applying a RECORDED real writer observation."""

    def __init__(self, writer_kinds, napps):
        self.writer_kinds = writer_kinds      # {(update_variant, napps): kinds}
        self.napps = napps
        self.errors = []

    def write_update(self, store):
        store.extend(self.writer_kinds[(True, self.napps)])

    def write_fresh(self, store):
        store.extend(self.writer_kinds[(False, self.napps)])


# ---------------------------------------------------------------------------
# Differential comparison.
# ---------------------------------------------------------------------------

def run_shadow(prefix, check_mode, update_variant, callees):
    """Run the contract-stripped impl region; return (outcome, post-store)."""
    global _CALLEES
    _CALLEES = callees
    store = list(prefix)
    try:
        produce_changes_or_report(store, check_mode, update_variant)
        return "return", store
    except CheckFailureExit:
        return "raise", store


def oracle_from_handle(prefix, obs):
    """Lift a recorded REAL handle observation to the model carrier at `prefix`.

    The real handle always starts from written_files == [] (makemigrations.py:102
    resets it), so the real observation is (exit outcome, appended kind tokens);
    the prefix is carried by the bridge and its preservation by the real writers
    is established by the prefix leg (run_real_writer).

    The appended kinds are carried through UNCONDITIONALLY — including when the
    real run exited. That is the whole discriminating observable of this bundle:
    the gold patch's effect is that in check mode NOTHING is appended before the
    exit, so the real store post-state must be exactly the prefix. Under the
    PRE-patch order the real run appends an artefact token and THEN exits, so
    this returns ("raise", prefix + [kind]) while the shadow returns
    ("raise", prefix) — a disagreement, which is what makes this check capable
    of failing. Discarding the kinds on the exit path (reporting bare `prefix`
    for any exiting run) would make the check pass against the unpatched repo
    and certify nothing."""
    outcome = "return"
    if obs["exit_code"] != "none":
        outcome = ("raise" if obs["exit_code"] == 1
                   else "exit(%r)" % (obs["exit_code"],))
    return outcome, list(prefix) + list(obs["kinds"])


def compare(prefix, check_mode, update_variant, napps, callees, obs, tag):
    shadow_out, shadow_store = run_shadow(prefix, check_mode, update_variant,
                                          callees)
    oracle_out, oracle_store = oracle_from_handle(prefix, obs)
    if callees.errors:
        return ("DISAGREEMENT (%s) on prefix=%r check_mode=%r update_variant=%r "
                "napps=%d:\n  real axiomatized callee violated its contract: %s"
                % (tag, prefix, check_mode, update_variant, napps,
                   "; ".join(callees.errors)))
    if shadow_out != oracle_out or ToSeq(shadow_store) != ToSeq(oracle_store):
        return ("DISAGREEMENT (%s) on prefix=%r check_mode=%r "
                "update_variant=%r napps=%d:\n"
                "  shadow (impl region): outcome=%r store=%r\n"
                "  real patched handle:  outcome=%r store=%r "
                "(exit_code=%r writers=%r written=%r on_disk=%r)"
                % (tag, prefix, check_mode, update_variant, napps,
                   shadow_out, shadow_store, oracle_out, oracle_store,
                   obs["exit_code"], obs["writers"], obs["written"],
                   obs["on_disk"]))
    return None


# ---------------------------------------------------------------------------
# Boundary + fuzz input plans.
# ---------------------------------------------------------------------------

def boundary_prefixes():
    """Prefixes exercising the bridge: empty, singleton, both token kinds, and
    tokens that are NOT 0/1 (the model's Requires allows any int, and they must
    be copied through untouched)."""
    return [
        [],
        [0],
        [1],
        [0, 1],
        [1, 1, 0],
        [7],
        [-3, 0, 42],
        [-10 ** 9, 10 ** 9],
        [5] * 8,
        list(range(-4, 4)),
    ]


def main():
    real = RealRepo()
    checked = 0
    real_calls = 0

    # ------------------------------------------------------------------
    # 1. EXHAUSTIVE real enumeration of the finite decision space, with each
    #    class re-run REAL_REPEATS times and required to reproduce itself.
    # ------------------------------------------------------------------
    classes = [(c, u, n)
               for c in (False, True)
               for u in (False, True)
               for n in (1, 2)]
    handle_obs = {}
    for key in classes:
        c, u, n = key
        first = None
        for rep in range(REAL_REPEATS):
            obs = real.run_real_handle(n, c, u)
            real_calls += 1
            sig = (obs["exit_code"], tuple(obs["kinds"]),
                   tuple(obs["writers"]), tuple(obs["on_disk"]))
            if first is None:
                first = sig
                handle_obs[key] = obs
            elif sig != first:
                print("ORACLE NONDETERMINISM on check_mode=%r "
                      "update_variant=%r napps=%d: run 0 %r != run %d %r"
                      % (c, u, n, first, rep, sig))
                return 1

    # ------------------------------------------------------------------
    # 2. Prefix leg: the REAL writers invoked directly at real pre-seeded
    #    prefixes — the real observation that they are append-only and
    #    prefix-independent, and the source of the replay writer kinds.
    # ------------------------------------------------------------------
    writer_kinds = {}
    for u in (False, True):
        for n in (1, 2):
            seen = None
            for plen in PREFIX_LENS:
                kinds, preserved = real.run_real_writer(n, u, plen)
                real_calls += 1
                if not preserved:
                    print("DISAGREEMENT (prefix leg) update_variant=%r napps=%d "
                          "prefix_len=%d: the real %s writer did NOT preserve "
                          "the pre-seeded produced-file prefix"
                          % (u, n, plen,
                             "write_to_last_migration_files" if u
                             else "write_migration_files"))
                    return 1
                if seen is None:
                    seen = kinds
                elif kinds != seen:
                    print("DISAGREEMENT (prefix leg) update_variant=%r "
                          "napps=%d: the real writer's appended tokens depend "
                          "on the prefix length (%r at len 0 vs %r at len %d); "
                          "the axiom's prefix-independence does not hold"
                          % (u, n, seen, kinds, plen))
                    return 1
            writer_kinds[(u, n)] = seen

    # Cross-check: the writer the real patched handle entered, and the tokens it
    # appended, agree with invoking that real writer directly. Catches a wrong
    # kind labelling on either leg.
    for (c, u, n), obs in handle_obs.items():
        if c:
            continue
        expect_writer = ["update" if u else "fresh"]
        if obs["writers"] != expect_writer:
            print("DISAGREEMENT (cross-check) check_mode=%r update_variant=%r "
                  "napps=%d: the real patched handle entered writers %r, "
                  "expected the %s writer per the flag"
                  % (c, u, n, obs["writers"], expect_writer[0]))
            return 1
        if obs["kinds"] != writer_kinds[(u, n)]:
            print("DISAGREEMENT (cross-check) check_mode=%r update_variant=%r "
                  "napps=%d: handle-observed kinds %r != directly-invoked real "
                  "writer kinds %r"
                  % (c, u, n, obs["kinds"], writer_kinds[(u, n)]))
            return 1

    # ------------------------------------------------------------------
    # 3. LIVE differential: every decision class x every boundary prefix, with
    #    the shadow's @ContractOnly callees calling the REAL writers.
    # ------------------------------------------------------------------
    for c, u, n in classes:
        for prefix in boundary_prefixes():
            callees = LiveCallees(real, n)
            err = compare(prefix, c, u, n, callees, handle_obs[(c, u, n)],
                          "live")
            if not c:
                real_calls += 1
            if err:
                print(err)
                return 1
            checked += 1
    live_checked = checked

    # ------------------------------------------------------------------
    # 4. Replay differential over the same space: boundary prefixes again, then
    #    seeded fuzz to reach >= 1e5 inputs.
    # ------------------------------------------------------------------
    for c, u, n in classes:
        for prefix in boundary_prefixes():
            callees = ReplayCallees(writer_kinds, n)
            err = compare(prefix, c, u, n, callees, handle_obs[(c, u, n)],
                          "replay")
            if err:
                print(err)
                return 1
            checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        c = rng.random() < 0.5
        u = rng.random() < 0.5
        n = rng.choice((1, 2))
        plen = rng.randint(0, 8) if rng.random() < 0.9 else rng.randint(9, 40)
        if rng.random() < 0.6:
            prefix = [rng.choice((0, 1)) for _ in range(plen)]
        else:
            prefix = [rng.randint(-10 ** 6, 10 ** 6) for _ in range(plen)]
        callees = ReplayCallees(writer_kinds, n)
        err = compare(prefix, c, u, n, callees, handle_obs[(c, u, n)], "fuzz")
        if err:
            print(err)
            return 1
        checked += 1

    # The F2P shape, restated as an explicit observation of the real run so the
    # summary reports what the patched code actually did in check mode.
    f2p = handle_obs[(True, False, 1)]
    print("G-CONF OK: shadow (contract-stripped impl region of "
          "produce_changes_or_report) == real patched "
          "makemigrations Command.handle changes-present branch on %d inputs "
          "(%d live with the REAL write_migration_files / "
          "write_to_last_migration_files invoked, %d replayed over the same "
          "space; %d real repo invocations; 8/8 decision classes enumerated "
          "exhaustively, prefix lengths %r; seed=%d); 0 disagreements. "
          "F2P shape (--check, pending changes): real exit_code=%r, "
          "written_files=%r, on_disk=%r."
          % (checked, live_checked, checked - live_checked, real_calls,
             list(PREFIX_LENS), SEED, f2p["exit_code"], f2p["written"],
             f2p["on_disk"]))
    print(json.dumps({
        "checked": checked,
        "live_real_checked": live_checked,
        "real_invocations": real_calls,
        "disagreements": 0,
        "seed": SEED,
        "oracle": ("real patched django.core.management.commands.makemigrations"
                   ".Command.handle (called via call_command)"),
        "shadow": "direct (contract-stripped impl region)",
        "decision_classes_enumerated": len(classes),
    }))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        print("G-CONF ERROR: unhandled exception (see traceback above)")
        sys.exit(1)
