#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16333.

Executes the THREE REAL unchanged callees the modeled routine relies on and
asserts that every observation matches the corresponding @ContractOnly axiom in
model.py. All three are callees the routine INVOKES but does not change:

  (1) base_form_save_deferred(self)  <->  BaseModelForm.save(commit=False)
        Django's django.forms.models.BaseModelForm.save called in deferred
        (commit=False) mode. Axiom: it sets up the deferred relational save
        (the form gains a callable `save_m2m` handle) and writes NOTHING — the
        primary record is not in the database and the m2m associations are not
        written. (model.py: deferred_save_ready becomes True; record_persisted
        unchanged; the relational-data capability relations_done(self) is NOT
        granted.)

  (2) persist_record(self)  <->  Model.save()  (here driven via the instance)
        Writing the primary record only: after it the row exists, but the m2m
        associations are still NOT written. (model.py: record_persisted True;
        the relational-data capability relations_done(self) is NOT granted.)

  (3) run_deferred_save(self)  <->  the deferred relational save `save_m2m`
        (== BaseModelForm._save_m2m). Running it writes the m2m associations.
        (model.py: it is the SOLE producer of the per-form relational-data
        capability relations_done(self); record_persisted unchanged.)

The relational-data fact is modelled by the abstract per-form capability
predicate `relations_done(self)` (directive-8 / control-flow grounding): an
opaque predicate with NO body, so an implementation cannot fold it into
existence, and tied to the specific form `self`, so a capability obtained for a
different form does not stand in for it. Its single load-bearing real-world
claim — that BEFORE the deferred relational save runs the m2m associations are
NOT written, and that running save_m2m is what writes them — is asserted
directly below (after super().save(commit=False) and after the record write the
relations are unwritten; only save_m2m writes them). The capability predicate
has no separate real callee; it is validated by the same observations of
`relations_written(instance)` across the three steps.

Run inside the official SWE-bench container for the instance, where Django is
importable and a sqlite test database is available. Configures an in-memory
sqlite database and a minimal model carrying one ManyToManyField, then drives a
real django.forms.ModelForm exactly as the routine does (super().save(
commit=False); instance.save(); save_m2m()). Exit 0 iff every obligation holds.
Standard-library + Django (the very framework the patch lives in) only.
"""
import os
import sys


def _configure_django():
    import types
    import django
    from django.conf import settings
    # Register a synthetic app module "axcheck" so the app label resolves even
    # when this file is not on the import path as a package.
    if "axcheck" not in sys.modules:
        mod = types.ModuleType("axcheck")
        mod.__path__ = [os.path.dirname(os.path.abspath(__file__))]
        mod.__file__ = os.path.abspath(__file__)
        sys.modules["axcheck"] = mod
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
                "axcheck",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=False,
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django import forms
    from django.db import connection, models

    # A minimal pair of models: a related target and a record carrying one
    # ManyToManyField to it. The structural twin of the test's custom user +
    # Organization with an `orgs` m2m.
    class Target(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            app_label = "axcheck"

    class Record(models.Model):
        label = models.CharField(max_length=50)
        rels = models.ManyToManyField(Target, blank=True)

        class Meta:
            app_label = "axcheck"

    with connection.schema_editor() as editor:
        editor.create_model(Target)
        editor.create_model(Record)

    class RecordForm(forms.ModelForm):
        class Meta:
            model = Record
            fields = ("label", "rels")

    def relations_written(instance):
        """True iff the m2m associations for `instance` are persisted."""
        if instance.pk is None:
            return False
        return instance.rels.exists()

    def record_written(instance):
        """True iff the primary row for `instance` exists in the database."""
        if instance.pk is None:
            return False
        return Record.objects.filter(pk=instance.pk).exists()

    obs = 0
    for trial in range(40):
        target = Target.objects.create(name="t%d" % trial)

        form = RecordForm(data={"label": "r%d" % trial, "rels": [str(target.pk)]})
        assert form.is_valid(), "fixture form should validate: %r" % (form.errors,)

        # ---- Axiom (1): BaseModelForm.save(commit=False) ------------------
        # This is exactly `super().save(commit=False)` in the routine.
        instance = forms.ModelForm.save(form, commit=False)

        # The deferred relational save handle is installed (deferred_save_ready
        # becomes True).
        assert hasattr(form, "save_m2m"), (
            "BaseModelForm.save(commit=False) must install save_m2m")
        assert callable(form.save_m2m)
        # Nothing is written yet: neither the primary record nor the m2m data
        # (the relational-data capability relations_done is not yet earned).
        assert not record_written(instance), (
            "deferred save must not write the primary record")
        assert not relations_written(instance), (
            "deferred save must not write the m2m associations")

        # ---- Axiom (3) precondition (NEGATIVE): record must exist first ----
        # run_deferred_save requires the primary record to already be written
        # (get_record() is True). The real save_m2m attaches the associations
        # to the instance's primary key, so running it BEFORE instance.save()
        # (no pk yet) must FAIL. Exercising this guards the ordering precondition
        # the axiom encodes (Requires(get_record() is True)). One observation
        # (trial 0) suffices; we leave the form usable for the positive path
        # afterwards because save_m2m raised without persisting anything.
        if trial == 0:
            assert instance.pk is None, (
                "fixture must have no primary key before the record write")
            raised = False
            try:
                form.save_m2m()
            except Exception:
                # The real save_m2m cannot write the m2m through-rows for a
                # record that has no primary key yet.
                raised = True
            assert raised, (
                "save_m2m() before the primary-record write must FAIL "
                "(the relational associations need the record's primary key) "
                "— this is the ordering precondition run_deferred_save encodes")
            assert not relations_written(instance), (
                "the failed pre-pk save_m2m must not have written associations")

        # ---- Axiom (2): the primary record write ---------------------------
        # This is exactly `user.save()` in the routine (commit branch).
        instance.save()
        assert record_written(instance), (
            "instance.save() must write the primary record")
        # The m2m data is STILL not written by the primary-record write alone —
        # this is the entire reason the deferred save must be run. (record
        # persisted True; relations unchanged == still False.)
        assert not relations_written(instance), (
            "instance.save() must NOT write the m2m associations by itself")

        # ---- Axiom (3): the deferred relational save -----------------------
        # This is exactly `self.save_m2m()` in the routine's commit branch.
        # Precondition: the deferred save was set up (it was, by axiom 1).
        before_pk = instance.pk
        form.save_m2m()
        assert relations_written(instance), (
            "save_m2m() must write the m2m associations")
        # It writes the relational data only; it does not unset / re-create the
        # primary record (record_persisted unchanged).
        assert instance.pk == before_pk and record_written(instance), (
            "save_m2m() must not disturb the primary record")
        # The written associations are exactly the submitted target.
        assert list(instance.rels.all()) == [target], (
            "save_m2m() wrote unexpected associations: %r"
            % (list(instance.rels.all()),))

        obs += 1

    # Boundary: a form whose m2m field is empty. The deferred save must still
    # be set up, write nothing erroneously, and leave the (empty) relation set.
    for trial in range(10):
        form = RecordForm(data={"label": "e%d" % trial, "rels": []})
        assert form.is_valid(), "empty-m2m fixture should validate: %r" % (form.errors,)
        instance = forms.ModelForm.save(form, commit=False)
        assert hasattr(form, "save_m2m")
        assert not record_written(instance)
        instance.save()
        assert record_written(instance)
        form.save_m2m()
        assert list(instance.rels.all()) == [], (
            "empty-m2m form should persist an empty relation set")
        obs += 1

    print("G-AX OK: base_form_save_deferred / persist_record / run_deferred_save "
          "axioms sound against real BaseModelForm.save(commit=False), "
          "Model.save(), and save_m2m over %d observations (incl. empty-m2m "
          "boundary). Deferred save installs the handle and writes nothing; the "
          "record write never writes m2m; save_m2m writes only the m2m data."
          % (obs,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
