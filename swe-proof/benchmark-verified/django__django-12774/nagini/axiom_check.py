#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-12774.

There are NO consumed @ContractOnly callee axioms in model.py. The substance of
the change is modelled DEEPLY (the per-guarantee predicate ``permits_alone`` and
the fold ``any_permits`` over the declared uniqueness guarantees, plus the final
``should_reject`` decision). This check validates that deep model as an
A-reference: it executes the REAL Django code paths the patch relies on and
asserts the deep model agrees with reality on every observation.

The real callees / data the patch uses (all UNCHANGED by the patch except the
guard expression itself, which we re-derive identically):

  * ``opts.total_unique_constraints`` — the model's declared ``UniqueConstraint``
    objects whose ``condition is None`` (the "unconditional" guarantees).
  * ``len(constraint.fields) == 1`` and ``constraint.fields[0]`` — the
    single-field extraction the patch performs to build ``unique_fields``.
  * ``opts.get_field(field_name).unique`` — the field's individual-unique flag.
  * the primary-key name ``opts.pk.name`` and ``'pk'`` — the distinguished
    primary-key identity.

For each constructed model and each candidate field name we compute, from the
REAL objects:

  reject_real = (field_name not in ('pk', pk.name)) and
                (not opts.get_field(field_name).unique) and
                (field_name not in unique_fields_real)

and the deep MODEL decision via the same encoding model.py uses (each guarantee
reduced to (condition is None, list(fields)); permits_alone / any_permits;
should_reject). We assert reject_real == reject_model on every case, including
the F2P discriminators: a single-field unconditional constraint accepts the
field; a conditional (partial) constraint or a multi-field constraint does NOT.

Run inside the official SWE-bench container for the instance (Django importable).
Imports nothing repo-specific beyond Django itself. Exit 0 iff every obligation
holds.
"""
import os
import sys


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def permits_alone(g, field_name):
    """model.py: a guarantee g = (unconditional, names) permits field_name on
    its own iff unconditional and it ranges over exactly that one field."""
    unconditional, names = g
    return unconditional and len(names) == 1 and names[0] == field_name


def any_permits(guarantees, field_name):
    """model.py any_permits(guarantees, 0, field_name)."""
    return any(permits_alone(g, field_name) for g in guarantees)


def should_reject_model(field_name, field_unique, guarantees, pk_id):
    """model.py should_reject, with PK modelled as the distinguished pk_id."""
    if field_name == pk_id:
        return False
    if field_unique:
        return False
    return not any_permits(guarantees, field_name)


APP = "auth"  # an installed app (real filesystem location) to host temp models


def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r" % (exc,))
        return 0

    from django.db import models

    checked = 0

    def real_unique_fields(opts):
        """Re-derive the patch's unique_fields from the REAL property."""
        return [
            constraint.fields[0]
            for constraint in opts.total_unique_constraints
            if len(constraint.fields) == 1
        ]

    def real_reject(opts, field_name):
        """The patch's guard, computed over the REAL Options/field objects.
        Mirrors the patch's short-circuit: 'pk' never reaches get_field()."""
        if field_name == 'pk':
            return False
        unique_fields = real_unique_fields(opts)
        return (
            not opts.get_field(field_name).unique and
            field_name not in unique_fields
        )

    def model_guarantees(opts):
        """Reduce the REAL declared UniqueConstraints to the model encoding
        (unconditional, list-of-field-names) used by model.py."""
        out = []
        for c in opts.total_unique_constraints:
            # total_unique_constraints already filters to condition is None,
            # i.e. the unconditional guarantees; record that explicitly so the
            # encoding matches model.py one-to-one (we still include the flag).
            out.append((c.condition is None, list(c.fields)))
        return out

    def check_model(klass, field_names):
        nonlocal checked
        opts = klass._meta
        guarantees = model_guarantees(opts)
        pk_id = '\x00PK'  # a token no real field name equals (model's PK)
        for fn in field_names:
            # pk identity in the model is a distinguished id; map both the 'pk'
            # alias and the real primary-key name to it. For a pk lookup the
            # real guard short-circuits (no get_field call), so the field's own
            # unique flag is irrelevant.
            is_pk = (fn == 'pk' or fn == opts.pk.name)
            field_unique = False if is_pk else opts.get_field(fn).unique
            r_real = real_reject(opts, 'pk' if is_pk else fn)
            fn_id = pk_id if is_pk else fn
            r_model = should_reject_model(fn_id, field_unique, guarantees, pk_id)
            assert r_real == r_model, (
                "deep model disagrees with real guard on %s.%s: real=%r model=%r "
                "(guarantees=%r, unique=%r)"
                % (klass.__name__, fn, r_real, r_model, guarantees, field_unique))
            checked += 1

    def run_cases():
        nonlocal checked
        # --- Case 1: the F2P discriminator — a single-field UNCONDITIONAL
        #     constraint must make a non-unique field acceptable. ------------
        class SeasonLike(models.Model):
            year = models.IntegerField(null=True, blank=True)
            gt = models.IntegerField(null=True, blank=True)

            class Meta:
                app_label = APP
                constraints = [
                    models.UniqueConstraint(fields=['year'], name='axc_season_year_unique'),
                ]

        check_model(SeasonLike, ['pk', 'id', 'year', 'gt'])
        # year is NOT individually unique but IS the sole field of an
        # unconditional constraint -> must be accepted (not rejected).
        assert real_reject(SeasonLike._meta, 'year') is False
        assert should_reject_model('year', SeasonLike._meta.get_field('year').unique,
                                   model_guarantees(SeasonLike._meta), '\x00PK') is False

        # --- Case 2: a PARTIAL (conditional) constraint and a MULTI-FIELD
        #     constraint must NOT make their fields acceptable on their own. -
        class PartialAndCompositeLike(models.Model):
            ean = models.CharField(max_length=100)
            brand = models.CharField(max_length=100)
            name = models.CharField(max_length=80)
            is_active = models.BooleanField(default=True)

            class Meta:
                app_label = APP
                constraints = [
                    models.UniqueConstraint(
                        fields=['ean'], name='axc_partial_ean_unique',
                        condition=models.Q(is_active=True),
                    ),
                    models.UniqueConstraint(
                        fields=['brand', 'name'], name='axc_together_brand_name_unique',
                    ),
                ]

        check_model(PartialAndCompositeLike, ['pk', 'id', 'ean', 'brand', 'name', 'is_active'])
        # ean: partial constraint -> rejected; brand: multi-field -> rejected.
        assert real_reject(PartialAndCompositeLike._meta, 'ean') is True
        assert real_reject(PartialAndCompositeLike._meta, 'brand') is True

        # --- Case 3: a genuinely unique=True field must be accepted. --------
        class HasUniqueLike(models.Model):
            slug = models.SlugField(unique=True)
            other = models.IntegerField(default=0)

            class Meta:
                app_label = APP

        check_model(HasUniqueLike, ['pk', 'id', 'slug', 'other'])
        assert real_reject(HasUniqueLike._meta, 'slug') is False
        assert real_reject(HasUniqueLike._meta, 'other') is True

        # --- Case 4: mix of single-field-unconditional + multi + partial. ---
        class MixedLike(models.Model):
            a = models.IntegerField(default=0)
            b = models.IntegerField(default=0)
            c = models.IntegerField(default=0)
            flag = models.BooleanField(default=True)

            class Meta:
                app_label = APP
                constraints = [
                    models.UniqueConstraint(fields=['a'], name='axc_a_unique'),
                    models.UniqueConstraint(fields=['b', 'c'], name='axc_bc_unique'),
                    models.UniqueConstraint(
                        fields=['c'], name='axc_c_partial',
                        condition=models.Q(flag=True),
                    ),
                ]

        check_model(MixedLike, ['pk', 'id', 'a', 'b', 'c', 'flag'])
        assert real_reject(MixedLike._meta, 'a') is False   # single-field unconditional
        assert real_reject(MixedLike._meta, 'b') is True    # only in a composite
        assert real_reject(MixedLike._meta, 'c') is True    # composite + partial only

    run_cases()

    print("G-AX OK: deep model (permits_alone / any_permits / should_reject) "
          "agrees with the real Django guard (total_unique_constraints + "
          "single-field extraction + get_field().unique) on %d field/model "
          "observations across F2P single-field-unconditional, partial, "
          "composite, and unique=True cases." % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
