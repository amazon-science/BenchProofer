#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-7530 (nagini).

SHADOW: the impl region of model.py `members_for_group`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helper `gathered` is specification-side only (the impl never calls
it). There are no @ContractOnly callees.

ORACLE: the REAL patched repo behaviour per mapping.md — the inner iteration
of the history-consistency pre-check in ``makemigrations`` that pairs each
app label with exactly that app's models. Two legs, both against the real
patched /testbed (the gate applies patch.diff before this script runs):

  * BULK leg — the changed sub-expression itself,
    ``apps.get_app_config(app_label).get_models()``, evaluated on the REAL
    application registry over thousands of synthesised multi-app rosters
    (real django.db.models.Model classes registered under synthetic app
    packages, installed via ``apps.set_installed_apps``). For every
    (roster, target label) the shadow's gathered member sequence must equal
    the real registry's answer, element for element and in order.

  * IN-SITU leg — the real patched ``makemigrations`` command is run
    end-to-end (dry run) with a recording routing policy whose
    ``allow_migrate`` records every (app_label, model_name) pair the
    pre-check offers and returns False (so the enumeration is exhaustive
    and no history check fires). Per app label, the recorded model sequence
    must equal the shadow's gathered sequence — this exercises the changed
    line inside the real control flow (the comprehension, the ``any``, the
    alias loop).

Type bridge (mapping.md section 2): app labels and model identities are
interned to ints per roster (label -> group id in installed order;
(label, object_name) -> member id); the roster streams owner/member are
built from the ground-truth creation order, which is the registry's
registration order. Every generated roster satisfies the precondition
len(owner) == len(member) by construction; target ranges over the installed
labels (the repo's own domain for the pre-check).

>= 1e5 Requires-satisfying inputs: boundary rosters + randomized rosters
until 100000 (roster, target) triples are checked in the bulk leg, plus the
in-situ command runs. Pinned seed: 7530.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + django (the repo under test) only.
"""
import json
import os
import random
import sys
import tempfile

SEED = 7530
N_TARGET = 100000
N_COMMAND_RUNS = 12
POOL_LABELS = 40
MAX_MODELS_PER_APP = 6


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def members_for_group(owner, member, target):
    result = []  # type: List[int]
    i = len(owner)
    while i > 0:
        o = owner[i - 1]
        m = member[i - 1]
        if o == target:
            result = [m] + result
        i = i - 1
    return result
    # impl-end


# --- real Django environment ---------------------------------------------------

RECORDED = []


class RecordingRouter(object):
    """Routing policy that records every (app_label, model_name) pair the
    pre-check offers and denies migration (so enumeration is exhaustive and
    the history check is skipped)."""

    def allow_migrate(self, db, app_label, **hints):
        RECORDED.append((app_label, hints.get('model_name')))
        return False


def setup_django():
    from django.conf import settings
    settings.configure(
        INSTALLED_APPS=[],
        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                               'NAME': ':memory:'}},
        DATABASE_ROUTERS=[RecordingRouter()],
        USE_TZ=False,
    )
    import django
    django.setup()


def make_pool(rng):
    """Synthesise POOL_LABELS importable app packages under a temp dir, each
    declaring 0..MAX_MODELS_PER_APP real Model classes in its models.py.
    Returns {label: [object_name, ...]} in declaration (= registration)
    order."""
    root = tempfile.mkdtemp(prefix="sbu7530_")
    sys.path.insert(0, root)
    pool = {}
    for k in range(POOL_LABELS):
        label = "rosterapp_%02d" % k
        pkg = os.path.join(root, label)
        os.makedirs(pkg)
        open(os.path.join(pkg, "__init__.py"), "w").close()
        n_models = rng.randint(0, MAX_MODELS_PER_APP)
        names = ["M%d" % j for j in range(n_models)]
        lines = ["from django.db import models", ""]
        for name in names:
            lines.append("class %s(models.Model):" % name)
            lines.append("    f = models.IntegerField(default=0)")
            lines.append("    class Meta:")
            lines.append("        app_label = %r" % label)
            lines.append("")
        with open(os.path.join(pkg, "models.py"), "w") as f:
            f.write("\n".join(lines))
        pool[label] = names
    return pool


def build_streams(installed, pool):
    """Ground-truth roster streams for one installed-label ordering, with the
    int interning of mapping.md section 2."""
    label_id = {}
    for lab in installed:
        label_id[lab] = len(label_id)
    member_id = {}
    owner = []
    member = []
    for lab in installed:
        for name in pool[lab]:
            member_id[(lab, name)] = len(member_id)
            owner.append(label_id[lab])
            member.append(member_id[(lab, name)])
    return label_id, member_id, owner, member


def main():
    setup_django()
    from django.apps import apps

    rng = random.Random(SEED)
    pool = make_pool(rng)
    labels_all = sorted(pool.keys())

    checked = 0

    def check_round(installed, run_command):
        """One roster: install the labels, then check every target label.
        Returns an error string on disagreement, else the number checked."""
        nonlocal checked
        label_id, member_id, owner, member = build_streams(installed, pool)
        apps.set_installed_apps(list(installed))
        try:
            # BULK leg: the changed sub-expression on the real registry
            for lab in installed:
                shadow = members_for_group(owner, member, label_id[lab])
                real_models = list(apps.get_app_config(lab).get_models())
                real_ids = []
                for m in real_models:
                    key = (m._meta.app_label, m._meta.object_name)
                    if key not in member_id:
                        return ("DISAGREEMENT on roster %r target %r:\n"
                                "  real registry offered a member outside "
                                "the roster: %r" % (installed, lab, key))
                    real_ids.append(member_id[key])
                if shadow != real_ids:
                    return ("DISAGREEMENT on roster %r target %r:\n"
                            "  shadow gathered ids = %r\n"
                            "  real registry ids   = %r"
                            % (installed, lab, shadow, real_ids))
                checked += 1
            # IN-SITU leg: the real patched command end-to-end
            if run_command:
                from django.core.management import call_command
                del RECORDED[:]
                call_command('makemigrations', dry_run=True, verbosity=0)
                by_label = {}
                for app_label, model_name in RECORDED:
                    by_label.setdefault(app_label, []).append(model_name)
                for lab in installed:
                    shadow = members_for_group(owner, member, label_id[lab])
                    got = by_label.get(lab, [])
                    got_ids = [member_id.get((lab, n)) for n in got]
                    if shadow != got_ids:
                        return ("DISAGREEMENT (in-situ) on roster %r "
                                "target %r:\n  shadow gathered ids = %r\n"
                                "  pre-check offered    = %r (ids %r)"
                                % (installed, lab, shadow, got, got_ids))
                    checked += 1
                extra = [l for l in by_label if l not in installed]
                if extra:
                    return ("DISAGREEMENT (in-situ) on roster %r: pre-check "
                            "offered pairs for uninstalled labels %r"
                            % (installed, extra))
        finally:
            apps.unset_installed_apps()
        return None

    # boundary rosters: single empty app, single populated app, two disjoint
    # apps, all apps, reversed order
    empties = [l for l in labels_all if not pool[l]]
    populated = [l for l in labels_all if pool[l]]
    boundary = []
    if empties:
        boundary.append([empties[0]])
    boundary.append([populated[0]])
    boundary.append(populated[:2])
    boundary.append(list(labels_all))
    boundary.append(list(reversed(labels_all)))
    if empties and populated:
        boundary.append([populated[0], empties[0], populated[1]])

    for i, installed in enumerate(boundary):
        err = check_round(installed, run_command=True)
        if err:
            print(err)
            return 1

    # fuzz rosters (in-situ command on a sampled few, bulk on all)
    cmd_left = N_COMMAND_RUNS - len(boundary)
    while checked < N_TARGET:
        n = rng.randint(1, 12)
        installed = rng.sample(labels_all, n)
        run_cmd = cmd_left > 0
        if run_cmd:
            cmd_left -= 1
        err = check_round(installed, run_command=run_cmd)
        if err:
            print(err)
            return 1

    print("G-CONF OK: shadow impl == real patched per-app member gathering "
          "on %d (roster, target) inputs (seed %d; bulk registry + in-situ "
          "command legs); 0 disagreements." % (checked, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
