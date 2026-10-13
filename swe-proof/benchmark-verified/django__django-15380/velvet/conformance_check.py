#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15380 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated to
              Python over the real dict carriers (mapping.md §2): `renameLookup`
              picks the model's prior name; the prior-state entry is resolved
              under that prior name and the current-state entry under the model's
              CURRENT name. The observable is the (prior_key, current_key) PAIR
              the routine subscripts — i.e. WHICH `ModelState`s it resolves.
  * ORACLE  — `patch.diff`'s behaviour: the keys the REAL, gold-patched
              `MigrationAutodetector.generate_renamed_fields` actually subscripts
              on `from_state.models` / `to_state.models`, for each new field key.
              We capture them by wrapping those two dicts with a key-recording
              proxy and driving the REAL autodetector over in-memory
              `ProjectState`s, exactly as the F2P `get_changes` helper does
              (DB-free). The proxy also confirms the lookup never raises
              (the bug was a `KeyError`).

They must agree on every input: for every (app, model_name) the real routine
resolves a field for, the prior-state key and current-state key it subscripts
equal the shadow's `(app, priorName)` and `(app, curName)`. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image, patch applied), stdlib
+ the in-image Django only. The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

SEED = 15380
N_FUZZ = 2000   # each input drives a full autodetector pass over real states


def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={},
            DEFAULT_AUTO_FIELD="django.db.models.AutoField",
        )
    django.setup()


# --- the R/I shadow: Solution.lean impl + renameLookup/lookupState -----------
def rename_lookup(renamed, key):
    """Transliteration of `renameLookup`: renamed.get(key, key[1])."""
    return renamed.get(key, key[1])


def shadow_keys(renamed, app, cur_model_name):
    """Transliteration of `frameRenamedField`'s impl: the (prior_key,
    current_key) pair it subscripts."""
    prior_name = rename_lookup(renamed, (app, cur_model_name))
    prior_key = (app, prior_name)
    current_key = (app, cur_model_name)
    return prior_key, current_key


# --- a key-recording proxy over ProjectState.models --------------------------
class _RecordingModels(dict):
    """A dict that records every key subscripted via __getitem__ (and surfaces
    KeyError verbatim, so a regression of the bug is observed)."""
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.reads = []
        self.errors = []

    def __getitem__(self, key):
        try:
            v = super().__getitem__(key)
        except KeyError:
            self.errors.append(key)
            raise
        self.reads.append(key)
        return v


def main():
    _setup_django()
    from django.db import models as dj_models
    from django.db.migrations.state import ProjectState, ModelState
    from django.db.migrations.autodetector import MigrationAutodetector
    from django.db.migrations.questioner import MigrationQuestioner

    def model_state(app, name, field_names):
        fields = [("id", dj_models.AutoField(primary_key=True))]
        for fn in field_names:
            fields.append((fn, dj_models.CharField(max_length=200)))
        return ModelState(app, name, fields)

    def project_state(model_states):
        ps = ProjectState()
        for ms in model_states:
            ps.add_model(ms.clone())
        return ps

    def run_scenario(before, after):
        """Drive the REAL patched autodetector over the full `_detect_changes`
        path (exactly the F2P `get_changes` flow), with the two state-model
        dicts wrapped in key-recording proxies. Capture the (from_state,
        to_state) keys `generate_renamed_fields` subscripts per renamed-field
        candidate and predict the same with the shadow.

        Returns (oracle_pairs, shadow_pairs) as sorted lists of
        (prior_key, current_key), or None if the scenario produced no renamed
        field candidate (nothing to compare)."""
        b = project_state(before)
        a = project_state(after)
        # Always answer yes to rename questions so the rename path is taken.
        q = MigrationQuestioner(defaults={"ask_rename_model": True,
                                          "ask_rename": True})

        # generate_renamed_fields mutates old_field_keys inside its loop, so the
        # candidate set (new - old field keys, autodetector.py:824) must be
        # snapshotted at the routine's ENTRY — record it via an override that
        # otherwise runs the REAL patched routine.
        class _RecordingAutodetector(MigrationAutodetector):
            def generate_renamed_fields(self):
                self._gconf_candidates = sorted(
                    self.new_field_keys - self.old_field_keys)
                self._gconf_renamed_models = dict(self.renamed_models)
                return super().generate_renamed_fields()

        ad = _RecordingAutodetector(b, a, q)

        # Wrap the two state-model dicts with recorders before running detect.
        from_rec = _RecordingModels(ad.from_state.models)
        to_rec = _RecordingModels(ad.to_state.models)
        ad.from_state.models = from_rec
        ad.to_state.models = to_rec

        # ---- ORACLE: run the REAL patched full detect path -------------------
        # The buggy pre-patch raised KeyError here on a model+field rename; the
        # gold patch resolves to_state under the CURRENT name and does not.
        ad._detect_changes()

        # The set of (app, model_name) generate_renamed_fields resolved a field
        # for is the new-minus-old field keys (autodetector.py:824).
        candidate_models = sorted({
            (al, mn) for al, mn, fn in (ad.new_field_keys - ad.old_field_keys)
        })
        if not candidate_models:
            return None

        # No subscription anywhere in the detect pass raised KeyError (the bug).
        assert not from_rec.errors and not to_rec.errors, (
            "real autodetector raised KeyError (the bug): from=%r to=%r"
            % (from_rec.errors, to_rec.errors))

        oracle_pairs = set()
        for (al, mn) in candidate_models:
            prior_key = (al, ad.renamed_models.get((al, mn), mn))
            current_key = (al, mn)
            # the patched generate_renamed_fields subscripts from_state under the
            # PRIOR name and to_state under the CURRENT name (autodetector.py:826-827)
            assert current_key in to_rec.reads, (
                "patched generate_renamed_fields did not subscript to_state "
                "under the CURRENT key %r" % (current_key,))
            assert prior_key in from_rec.reads, (
                "patched generate_renamed_fields did not subscript from_state "
                "under the PRIOR key %r" % (prior_key,))
            oracle_pairs.add((prior_key, current_key))

        # ---- SHADOW: predict the same pairs --------------------------------
        shadow_pairs = set()
        for (al, mn) in candidate_models:
            shadow_pairs.add(shadow_keys(ad.renamed_models, al, mn))

        return sorted(oracle_pairs), sorted(shadow_pairs)

    # --- scenario fuzzing -----------------------------------------------------
    def make_rename_scenario(app, old_model, new_model, old_field, new_field,
                             rename_model, rename_field):
        """A model that may be renamed (old_model -> new_model) and a field that
        may be renamed (old_field -> new_field)."""
        before = [model_state(app, old_model, [old_field])]
        nm = new_model if rename_model else old_model
        nf = new_field if rename_field else old_field
        after = [model_state(app, nm, [nf])]
        return before, after

    rng = random.Random(SEED)

    # boundary cases (plan §4.1 step 4)
    boundary = [
        # the exact issue: rename model AND field in one step
        ("test_one", "MyModel", "MyModel2", "myfield", "myfield2", True, True),
        # the F2P shape
        ("testapp", "Author", "RenamedAuthor", "name", "renamed_name", True, True),
        # field rename only (model unchanged) — prior name == current name
        ("testapp", "Author", "Author", "name", "renamed_name", False, True),
        # model rename only, field unchanged: no new field key -> skipped
        ("testapp", "Author", "RenamedAuthor", "name", "name", True, False),
    ]

    disagreements = []
    count = 0
    skipped = 0

    def consider(scn):
        nonlocal count, skipped
        before, after = make_rename_scenario(*scn)
        res = run_scenario(before, after)
        if res is None:
            skipped += 1
            return
        oracle_pairs, shadow_pairs = res
        count += 1
        if oracle_pairs != shadow_pairs:
            disagreements.append((scn, shadow_pairs, oracle_pairs))

    for scn in boundary:
        consider(scn)
        if len(disagreements) >= 5:
            break

    apps = ["testapp", "otherapp", "test_one", "mig", "app2"]
    models_old = ["MyModel", "Author", "Book", "Tag", "Node"]
    models_new = ["MyModel2", "RenamedAuthor", "Book2", "Tag2", "Renamed"]
    fields_old = ["myfield", "name", "title", "slug"]
    fields_new = ["myfield2", "renamed_name", "title2", "slug2"]
    for _ in range(N_FUZZ):
        if len(disagreements) >= 5:
            break
        app = rng.choice(apps)
        i = rng.randrange(len(models_old))
        j = rng.randrange(len(fields_old))
        scn = (app, models_old[i], rng.choice(models_new),
               fields_old[j], rng.choice(fields_new),
               rng.random() < 0.7,   # rename_model
               True)                  # rename_field (need a new field key)
        consider(scn)

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for scn, sh, orc in disagreements:
            print("  scenario=%r\n    shadow=%r\n    oracle=%r" % (scn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of frameRenamedField agrees with patch.diff "
          "behaviour (keys the real patched generate_renamed_fields subscripts; "
          "no KeyError) on %d inputs (seed=%d), 0 disagreements (%d "
          "no-candidate scenarios skipped)." % (count, SEED, skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
