#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-11400.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python R/I shadow of the two Lean
`implementation_*` skeletons and diffs it against the REAL patched callees over
the full discrete input matrix plus >=1e5 randomized draws.

  behavior 1  shadow of `implementation_orderedChoices`
              vs the REAL patched `Field.get_choices` (forward FK) AND
                 the REAL patched `ForeignObjectRel.get_choices` (reverse rel).
              observable: the produced [(pk, str(obj)), ...] choice list.
              The fix is the CONDITIONAL: an empty ordering directive must
              PRESERVE the related model's default (Meta.ordering) order; a
              non-empty directive re-sequences by it.

  behavior 2  shadow of `implementation_restrictedChoices`
              vs the REAL patched `RelatedOnlyFieldListFilter.field_admin_ordering`
                 forwarding into `Field.get_choices` with limit_choices_to.
              observable: the configured ordering is FORWARDED (not discarded),
              so the restricted choice list is ordered by it.

The opaque Lean `applyOrdering` is the I-tagged real re-sequencing primitive
(`QuerySet.order_by`), so the shadow consults the REAL queryset to materialize
both the default-order and the re-sequenced lists. What G-CONF pins is the Lean
skeleton's *control flow* (apply iff the directive is non-empty) against the real
patched control flow.

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import os
import random
import sys
import tempfile

SEED = 20240629
N_RANDOM = 120_000  # >= 1e5


def setup_django():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "ordapp"))
    open(os.path.join(d, "ordapp", "__init__.py"), "w").close()
    open(os.path.join(d, "ordapp", "models.py"), "w").close()
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth",
                        "ordapp"],
        USE_TZ=True,
    )
    django.setup()


# ---- Lean shadows ----------------------------------------------------------

def to_choice(obj):
    # toChoice : Obj -> (pk, label)
    return (obj.pk, str(obj))


def shadow_ordered_choices(include_blank, blank, ordering, default_objs,
                           ordered_objs):
    """Transliteration of implementation_orderedChoices.

    `default_objs`  = the collection in default presentation order (ordering=[]).
    `ordered_objs`  = the collection re-sequenced under a NON-EMPTY directive
                      (the result of the real applyOrdering = order_by).
    """
    qs = default_objs
    if ordering != []:
        qs = ordered_objs
    head = blank if include_blank else []
    return head + [to_choice(o) for o in qs]


def shadow_restricted_choices(admin_ordering, default_objs, ordered_objs):
    """Transliteration of implementation_restrictedChoices: no blank choice,
    honoring the configured ordering directive (configuredOrdering)."""
    ordering = admin_ordering if admin_ordering is not None else []
    return shadow_ordered_choices(False, [], ordering, default_objs, ordered_objs)


# ---- shared model fixtures -------------------------------------------------

def build_models():
    from django.db import models, connection

    class Author(models.Model):
        name = models.CharField(max_length=50)

        class Meta:
            app_label = "ordapp"
            # default presentation order (Meta.ordering) — the order that an
            # EMPTY directive must PRESERVE (the heart of the fix).
            ordering = ("name",)

        def __str__(self):
            return self.name

    class Book(models.Model):
        title = models.CharField(max_length=50)
        author = models.ForeignKey(Author, models.CASCADE, related_name="books")

        class Meta:
            app_label = "ordapp"
            ordering = ("title",)

        def __str__(self):
            return self.title

    with connection.schema_editor() as se:
        se.create_model(Author)
        se.create_model(Book)
    return Author, Book


def check_behaviors():
    from django.db import models

    Author, Book = build_models()

    # populate: insertion order deliberately != name order != title order, so a
    # dropped/garbled ordering is observable.
    a_carol = Author.objects.create(name="Carol")
    a_alice = Author.objects.create(name="Alice")
    a_bob = Author.objects.create(name="Bob")
    authors = [a_carol, a_alice, a_bob]

    Book.objects.create(title="Zeta", author=a_carol)
    Book.objects.create(title="Mu", author=a_alice)
    Book.objects.create(title="Alpha", author=a_bob)

    fk_field = Book._meta.get_field("author")          # forward FK Field
    rev_field = Author._meta.get_field("books")        # reverse rel descriptor

    disagreements = 0
    checked = 0

    # ordering directives to test against each carrier
    fwd_orderings = [(), ("name",), ("-name",), ("pk",), ("-pk",)]
    rev_orderings = [(), ("title",), ("-title",), ("pk",), ("-pk",)]

    def real_order_by(manager_qs, ordering):
        """The real re-sequencing primitive (I-tagged applyOrdering)."""
        if ordering:
            return list(manager_qs.order_by(*ordering))
        return list(manager_qs.all())

    # ----- behavior 1: forward Field.get_choices -----
    def b1_forward(ordering, include_blank):
        from django.db.models.fields import BLANK_CHOICE_DASH
        real = fk_field.get_choices(include_blank=include_blank, ordering=ordering)
        default_objs = real_order_by(Author._default_manager, ())
        ordered_objs = real_order_by(Author._default_manager, ordering)
        blank = list(BLANK_CHOICE_DASH)
        exp = shadow_ordered_choices(include_blank, blank, list(ordering),
                                     default_objs, ordered_objs)
        return list(real), exp

    # ----- behavior 1': reverse get_choices -----
    def b1_reverse(ordering, include_blank):
        from django.db.models.fields import BLANK_CHOICE_DASH
        real = rev_field.get_choices(include_blank=include_blank, ordering=ordering)
        default_objs = real_order_by(Book._default_manager, ())
        ordered_objs = real_order_by(Book._default_manager, ordering)
        blank = list(BLANK_CHOICE_DASH)
        exp = shadow_ordered_choices(include_blank, blank, list(ordering),
                                     default_objs, ordered_objs)
        return list(real), exp

    # full discrete matrix
    plan_b1 = []
    for ordering in fwd_orderings:
        for ib in (True, False):
            plan_b1.append(("fwd", ordering, ib))
    for ordering in rev_orderings:
        for ib in (True, False):
            plan_b1.append(("rev", ordering, ib))

    rng = random.Random(SEED)
    for _ in range(N_RANDOM):
        kind = rng.choice(["fwd", "rev"])
        ordering = rng.choice(fwd_orderings if kind == "fwd" else rev_orderings)
        ib = rng.choice([True, False])
        plan_b1.append((kind, ordering, ib))

    for kind, ordering, ib in plan_b1:
        got, exp = (b1_forward if kind == "fwd" else b1_reverse)(ordering, ib)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"behavior1 MISMATCH {kind} ordering={ordering} "
                      f"include_blank={ib}: real={got!r} shadow={exp!r}")

    # ----- behavior 2: RelatedOnlyFieldListFilter forwards configured ordering -
    # The patched field_admin_ordering returns the admin/Meta ordering; the
    # restricted field_choices forwards it into Field.get_choices(limit...).
    # We observe: with limit_choices_to restricting to a pk subset, the choices
    # are ordered by the configured directive (and the restriction is preserved).
    def b2(admin_ordering, pk_subset):
        limit = {"pk__in": pk_subset}
        ordering = admin_ordering if admin_ordering is not None else ()
        real = fk_field.get_choices(include_blank=False,
                                    limit_choices_to=limit, ordering=ordering)
        restricted_default = real_order_by(
            Author._default_manager.complex_filter(limit), ())
        restricted_ordered = real_order_by(
            Author._default_manager.complex_filter(limit), ordering)
        exp = shadow_restricted_choices(
            list(admin_ordering) if admin_ordering is not None else None,
            restricted_default, restricted_ordered)
        return list(real), exp

    all_pks = [a.pk for a in authors]
    subsets = [tuple(all_pks), (a_alice.pk, a_bob.pk), (a_carol.pk,),
               (a_carol.pk, a_alice.pk)]
    admin_orderings = [None, (), ("name",), ("-name",), ("pk",)]

    plan_b2 = []
    for ao in admin_orderings:
        for ss in subsets:
            plan_b2.append((ao, ss))
    for _ in range(N_RANDOM // 2):
        plan_b2.append((rng.choice(admin_orderings), rng.choice(subsets)))

    for ao, ss in plan_b2:
        got, exp = b2(ao, ss)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"behavior2 MISMATCH admin_ordering={ao} subset={ss}: "
                      f"real={got!r} shadow={exp!r}")

    return checked, disagreements


def main():
    setup_django()
    checked, disagreements = check_behaviors()
    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
