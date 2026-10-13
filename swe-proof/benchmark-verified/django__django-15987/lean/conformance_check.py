#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-15987.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the Lean skeleton
`implementation_fixtureDirs` (string-form membership + first match) and diffs it
against the REAL patched callee `Command.fixture_dirs`.

For each fuzzed configuration of
  * `settings.FIXTURE_DIRS`            — a list mixing plain `str` and
                                         `pathlib.Path` entries, and
  * the installed app components       — each with a `.label` and a `.path`
                                         (so its default dir is
                                         `os.path.join(path, "fixtures")`),
we drive the REAL `Command.fixture_dirs` property and observe whether it raises
`ImproperlyConfigured` for the "default fixture directory ... cannot be listed"
reason and, if so, for which `app_label`. That observable is compared against the
shadow's first-colliding-component prediction.

Observable, classified as:
  ("raise", app_label)   -> the property raised the default-fixture-dir error
  ("ok",)                -> the property completed (or did not raise THAT error)

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import os
import random
import sys
import tempfile
from pathlib import Path

SEED = 20240823
N_RANDOM = 120_000  # >= 1e5

DEFAULT_DIR_MSG = "is a default fixture directory for the"


def setup_django():
    d = tempfile.mkdtemp()
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
        FIXTURE_DIRS=[],
        USE_TZ=True,
    )
    django.setup()


class FakeAppConfig:
    """Stand-in for an AppConfig: only `.label` and `.path` are read by the
    modeled collision loop."""
    def __init__(self, label, path):
        self.label = label
        self.path = path


# ---- shadow of implementation_fixtureDirs --------------------------------
# comps: list of (label, default_dir)   default_dir = os.path.join(path,"fixtures")
# entries: the FIXTURE_DIRS list (str or Path objects)
# Returns ("raise", label) for the first colliding component, else ("ok",).
def shadow(comps, entries):
    string_forms = [str(d) for d in entries]
    for label, default_dir in comps:
        if default_dir in string_forms:        # string-form membership (the fix)
            return ("raise", label)
    return ("ok",)


def classify_real(cmd_cls, app_configs, entries, settings, apps):
    """Drive the REAL `Command.fixture_dirs` and classify the observable."""
    from django.core.exceptions import ImproperlyConfigured
    settings.FIXTURE_DIRS = entries
    apps.get_app_configs = lambda: list(app_configs)
    cmd = cmd_cls()
    cmd.app_label = None  # read by the property; None => no app filtering
    try:
        cmd.fixture_dirs            # cached_property: triggers the loop
        return ("ok",)
    except ImproperlyConfigured as e:
        msg = str(e)
        if DEFAULT_DIR_MSG in msg:
            # recover the offending app_label from the formatted message
            # "'<dir>' is a default fixture directory for the '<label>' app ..."
            label = msg.split("for the '", 1)[1].split("'", 1)[0]
            return ("raise", label)
        # a DIFFERENT ImproperlyConfigured (e.g. "contains duplicates") — the
        # generator avoids this, but treat as non-collision for safety.
        return ("ok",)


def build_components(rng, n_locs):
    """n distinct app components; default dirs live under /srv/appK/fixtures."""
    comps_meta = []          # (label, path, default_dir)
    for i in range(n_locs):
        path = "/srv/app%d" % i
        label = "app%d" % i
        comps_meta.append((label, path, os.path.join(path, "fixtures")))
    return comps_meta


def main():
    setup_django()
    from django.conf import settings
    from django.apps import apps
    from django.core.management.commands.loaddata import Command

    rng = random.Random(SEED)

    # A fixed pool of components; their default dirs are the collision targets.
    N_COMPS = 5
    comps_meta = build_components(rng, N_COMPS)
    app_configs = [FakeAppConfig(label, path) for (label, path, _dd) in comps_meta]
    comps = [(label, dd) for (label, _p, dd) in comps_meta]   # (label, default_dir)

    # Candidate locations for FIXTURE_DIRS entries: every component default dir
    # (collision-inducing) plus some unrelated dirs (never collide).
    collide_locs = [dd for (_l, _p, dd) in comps_meta]
    other_locs = ["/etc/elsewhere%d" % i for i in range(4)]
    all_locs = collide_locs + other_locs

    def make_entries(spec):
        """spec: list of (location, is_path). Deduped by (is_path, location) so
        the unchanged whole-list duplicate guard never fires."""
        seen, entries = set(), []
        for loc, is_path in spec:
            key = (is_path, loc)
            if key in seen:
                continue
            seen.add(key)
            entries.append(Path(loc) if is_path else loc)
        return entries

    disagreements = 0
    checked = 0

    def run_case(spec):
        nonlocal disagreements, checked
        entries = make_entries(spec)
        got = classify_real(Command, app_configs, entries, settings, apps)
        exp = shadow(comps, entries)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH entries={[ (str(e), type(e).__name__) for e in entries]} "
                      f"real={got} shadow={exp}")

    # ---- full discrete matrix: each single location as str / as Path / absent
    run_case([])                                            # empty FIXTURE_DIRS
    for loc in all_locs:
        run_case([(loc, False)])                            # plain str entry
        run_case([(loc, True)])                             # Path entry (the bug)
    # pairs: a Path collision hidden behind a non-colliding str, and vice versa
    for cdd in collide_locs:
        run_case([(other_locs[0], False), (cdd, True)])     # Path collision
        run_case([(other_locs[0], True), (cdd, False)])     # str collision
        run_case([(cdd, True), (cdd, False)])               # both forms present

    # ---- randomized draws
    for _ in range(N_RANDOM):
        k = rng.randint(0, 4)
        spec = [(rng.choice(all_locs), rng.random() < 0.5) for _ in range(k)]
        run_case(spec)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
