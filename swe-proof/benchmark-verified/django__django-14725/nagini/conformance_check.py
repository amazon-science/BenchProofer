#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14725 (nagini).

SHADOW: the impl region of ``persist`` from model.py, copied VERBATIM below
(the impl region contains no contract calls, so the copy is byte-identical).
Its two @ContractOnly callees, ``persist_existing_objects`` and
``persist_new_objects``, delegate to the REAL unchanged repo primitives they
axiomatize per mapping.md section 3 — ``BaseModelFormSet.save_existing_objects``
and ``BaseModelFormSet.save_new_objects`` on a real bound formset — and each
delegation advances the shadow editor's own invocation count by exactly one,
mirroring the effect clause of the callee's contract. The pure region of
model.py is permission accounting only (an abstraction predicate over the two
counts plus fractional accessors); it has no algorithmic content, so the
shadow carries the counts as plain integer fields read directly.
``CollectionEditor`` becomes a plain three-field class plus the bridge handle
to the real formset whose primitives the callees invoke.

ORACLE: the REAL patched repo function the model models per mapping.md
section 1 — ``django.forms.models.BaseModelFormSet.save(commit)``. The gate
applies patch.diff to /testbed before this script runs and puts /testbed on
PYTHONPATH, so the import resolves to the patched module. Each probe builds a
real bound model formset (via ``modelformset_factory`` with the per-collection
mode flag), validates it, instruments the two persistence primitives with
invocation counters (observing the per-primitive effect facts the spec pins),
runs ``save(commit)``, and reads the returned instance list.

TYPE BRIDGE (mapping.md section 2): a saved model instance <-> its integer
record identifier. Every form's character field carries "n<k>" for a chosen
integer k, and an instance lowers to k by parsing that field, so the repo's
returned ``list`` of instances lowers to the model's ``List[int]``
order-preservingly; ``list`` concatenation is ``+`` on both sides. The mode
flag and ``commit`` are booleans on both sides (identity). The DB side effect
of one primitive invocation <-> one increment of that primitive's count:
shadow counts advance inside the delegating callees, real counts are observed
by the oracle-side instrumentation, and the two are compared per probe.

ISOLATION: persisting mutates the database, so within each scenario the
oracle run and the shadow run each execute inside a savepoint that is rolled
back, over identical starting rows; the scenario's own rows are rolled back
afterwards. Both sides therefore see the same pre-state.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): the model's Requires demand
only the flag permission and the counts predicate, so every
(flag, commit, bound-formset content) triple is Requires-satisfying. Boundary
scenarios cover creation-only submissions, mixed edit+create, unchanged
forms, empty submissions, blank extra forms, duplicate identifiers, and a
submission referencing a record outside the bound queryset; fuzz draws 0..3
existing rows (each changed or not) and 0..3 extra forms (each filled or
blank) with mixed-magnitude identifiers. Every scenario is crossed with both
flag values and both commit values, and each (scenario, flag, commit) probe
contributes three shadow-vs-real comparisons (returned identifier sequence,
existing-group run count, new-group run count). Total checks >= 100000,
asserted at the end. Pinned fuzz seed: 14725.

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outcomes and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 14725
N_FUZZ = 8500   # scenarios; x2 flags x2 commits x3 obligations >= 1e5 checks
MIN_CHECKS = 100000


# --- shadow: CollectionEditor + the @ContractOnly callees ---------------------
# The callees delegate to the REAL unchanged repo primitives (mapping.md
# sections 3.1 / 3.2) on the editor's bound formset, and each run advances the
# editor's own count by exactly one — the effect its contract records.

class CollectionEditor(object):
    def __init__(self, restrict_to_existing):
        self.restrict_to_existing = restrict_to_existing
        self.existing_runs = 0
        self.new_runs = 0
        # bridge plumbing (not model state): the real bound formset whose
        # unchanged primitives the @ContractOnly callees invoke.
        self.formset = None


def _ident(obj):
    """instance -> record identifier (mapping.md section 2): the integer k
    carried in the instance's 'n<k>' character field."""
    name = obj.name
    assert name.startswith("n"), "unexpected carrier field %r" % (name,)
    return int(name[1:])


def persist_existing_objects(self, commit):
    out = self.formset.save_existing_objects(commit)   # REAL repo primitive
    self.existing_runs += 1
    return [_ident(o) for o in out]


def persist_new_objects(self, commit):
    out = self.formset.save_new_objects(commit)        # REAL repo primitive
    self.new_runs += 1
    return [_ident(o) for o in out]


# --- the impl region of model.py, verbatim (no contract calls to strip) -------

def persist(self, commit):
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result


# --- Django environment --------------------------------------------------------

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {
                "ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


class Env(object):
    """Holds the model class and the two factory-produced formset classes
    (one per flag value), built once."""

    def __init__(self):
        from django.db import connection, models
        from django.forms.models import modelformset_factory

        class Author(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                app_label = "auth"

        with connection.schema_editor() as editor:
            editor.create_model(Author)

        self.Author = Author
        self.FS_restrict = modelformset_factory(
            Author, fields="__all__", edit_only=True)
        self.FS_default = modelformset_factory(
            Author, fields="__all__", edit_only=False)


# --- one probe -----------------------------------------------------------------

def _build_data(existing_rows, extras):
    """POST payload: existing_rows is [(pk, posted_ident)], extras is a list
    of posted_ident or None (None = the extra form is left blank)."""
    data = {
        "form-TOTAL_FORMS": str(len(existing_rows) + len(extras)),
        "form-INITIAL_FORMS": str(len(existing_rows)),
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "1000",
    }
    for i, (pk, ident) in enumerate(existing_rows):
        data["form-%d-id" % i] = str(pk)
        data["form-%d-name" % i] = "n%d" % ident
    for j, ident in enumerate(extras, start=len(existing_rows)):
        data["form-%d-id" % j] = ""
        data["form-%d-name" % j] = "" if ident is None else "n%d" % ident
    return data


def _valid_formset(FS, data, env, qs_pks):
    fs = FS(data, queryset=env.Author.objects.filter(pk__in=qs_pks))
    ok = fs.is_valid()
    assert ok, "generated scenario failed validation: %r / %r" % (
        fs.errors, fs.non_form_errors())
    return fs


def run_oracle(FS, data, env, qs_pks, commit):
    """The real patched save(commit): returns (identifier list, run counts)."""
    fs = _valid_formset(FS, data, env, qs_pks)
    counts = {"existing": 0, "new": 0}
    real_existing = fs.save_existing_objects
    real_new = fs.save_new_objects

    def counting_existing(c=True):
        counts["existing"] += 1
        return real_existing(c)

    def counting_new(c=True):
        counts["new"] += 1
        return real_new(c)

    fs.save_existing_objects = counting_existing
    fs.save_new_objects = counting_new
    saved = fs.save(commit)
    return [_ident(o) for o in saved], counts["existing"], counts["new"]


def run_shadow(FS, data, env, qs_pks, commit, flag):
    """The contract-stripped impl region, its callees delegating to the real
    primitives on an identical fresh formset."""
    fs = _valid_formset(FS, data, env, qs_pks)
    # Bridge plumbing: the modeled operation's surrounding body prepares this
    # holder before delegating to the primitives when not committing; the
    # primitives append to it, so the fresh formset needs it in place.
    fs.saved_forms = []
    editor = CollectionEditor(flag)
    editor.formset = fs
    result = persist(editor, commit)
    return result, editor.existing_runs, editor.new_runs


def check_scenario(env, scen, state):
    """scen: {'existing': [(init_ident, posted_ident)], 'extras': [...],
    'outside': bool}. Returns an error string on any disagreement."""
    from django.db import transaction

    with transaction.atomic():
        existing_rows = []
        qs_pks = []
        for init_ident, posted_ident in scen["existing"]:
            row = env.Author.objects.create(name="n%d" % init_ident)
            existing_rows.append((row.pk, posted_ident))
            qs_pks.append(row.pk)
        if scen.get("outside"):
            # a record NOT in the bound queryset, referenced by the single
            # initial form (the machinery treats it as an unexpected object;
            # both sides run the same primitives over it).
            inside = env.Author.objects.create(name="n%d" % scen["inside_ident"])
            outside = env.Author.objects.create(name="n%d" % scen["outside_ident"])
            qs_pks = [inside.pk]
            existing_rows = [(outside.pk, scen["outside_posted"])]
        data = _build_data(existing_rows, scen["extras"])

        err = None
        for flag in (True, False):
            FS = env.FS_restrict if flag else env.FS_default
            for commit in (True, False):
                with transaction.atomic():
                    real_seq, real_er, real_nr = run_oracle(
                        FS, data, env, qs_pks, commit)
                    transaction.set_rollback(True)
                with transaction.atomic():
                    shadow_seq, shadow_er, shadow_nr = run_shadow(
                        FS, data, env, qs_pks, commit, flag)
                    transaction.set_rollback(True)
                state["checked"] += 3
                if (shadow_seq != real_seq or shadow_er != real_er
                        or shadow_nr != real_nr):
                    err = ("DISAGREEMENT\n"
                           "  scenario: %r\n"
                           "  flag=%r commit=%r\n"
                           "  shadow: result=%r existing_runs=%r new_runs=%r\n"
                           "  real:   result=%r existing_runs=%r new_runs=%r"
                           % (scen, flag, commit,
                              shadow_seq, shadow_er, shadow_nr,
                              real_seq, real_er, real_nr))
                    break
            if err:
                break
        transaction.set_rollback(True)
    return err


# --- input generation ------------------------------------------------------------

def boundary_scenarios():
    return [
        # creation-only submission (no existing rows, two filled extras)
        {"existing": [], "extras": [10, 11]},
        # one edited existing row + one filled extra
        {"existing": [(1, 2)], "extras": [3]},
        # one unchanged existing row, nothing else
        {"existing": [(4, 4)], "extras": []},
        # empty submission
        {"existing": [], "extras": []},
        # blank extras only (skipped by the new-group primitive)
        {"existing": [], "extras": [None, None]},
        # mixed: edited / unchanged / edited rows + filled/blank/filled extras
        {"existing": [(5, 6), (7, 7), (8, 9)], "extras": [12, None, 13]},
        # single edited row, no extras
        {"existing": [(14, 15)], "extras": []},
        # single filled extra, no existing rows
        {"existing": [], "extras": [16]},
        # duplicate identifiers across groups
        {"existing": [(5, 7)], "extras": [7, 7]},
        # large / negative identifiers (bridge stress)
        {"existing": [(10 ** 12, -3)], "extras": [-10 ** 12, 0]},
        # record referenced by the initial form lies OUTSIDE the bound queryset
        {"existing": [], "extras": [], "outside": True,
         "inside_ident": 20, "outside_ident": 21, "outside_posted": 22},
    ]


def rand_scenario(rng):
    def ident():
        if rng.random() < 0.8:
            return rng.randint(0, 99)
        return rng.choice([-1, 0, 10 ** 6, 10 ** 12, -10 ** 6,
                           rng.randint(-10 ** 9, 10 ** 9)])

    existing = []
    for _ in range(rng.randint(0, 3)):
        init = ident()
        posted = ident() if rng.random() < 0.6 else init
        existing.append((init, posted))
    extras = []
    for _ in range(rng.randint(0, 3)):
        extras.append(None if rng.random() < 0.25 else ident())
    return {"existing": existing, "extras": extras}


def main():
    _configure_django()
    env = Env()
    state = {"checked": 0}

    boundary = boundary_scenarios()
    for scen in boundary:
        err = check_scenario(env, scen, state)
        if err:
            print(err)
            return 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_scenario(env, rand_scenario(rng), state)
        if err:
            print(err)
            return 1

    if state["checked"] < MIN_CHECKS:
        print("FAIL: only %d checks executed (< 1e5)" % state["checked"])
        return 1

    print("G-CONF OK: shadow impl (real-primitive callees) == real patched "
          "formset save on %d checks (%d boundary + %d fuzz scenarios, each "
          "x2 flags x2 commits x3 obligations: returned identifier sequence "
          "+ both per-primitive run counts; seed %d); 0 disagreements."
          % (state["checked"], len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": state["checked"], "disagreements": 0,
                      "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callees delegate to the real "
                                "repo primitives)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
