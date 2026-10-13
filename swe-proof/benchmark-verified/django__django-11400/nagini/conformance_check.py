#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11400 (nagini).

SHADOW: the impl regions of model.py's two contracted functions
(`related_choice_rows`, `reverse_choice_rows`) plus the `copy_rows` helper,
copied VERBATIM below with the contract calls (Requires/Ensures/Invariant/
Assert) stripped. No PSeq appears in the impl region (PSeq/ToSeq live only in
contracts), so no sequence shim is needed; the carriers are plain List[int].

The one @ContractOnly callee the impl uses, `apply_order_by`, calls the REAL
repo function per the contract: it is bridged to
`QuerySet.order_by(*ordering)` on the concrete base queryset that the
List[int] carrier abstracts (mapping.md section 3.1). The bridge context
(which queryset, which field-name tuple) is installed per test case; the
callee returns the row-identity list of the really-reordered queryset.

ORACLE: the REAL patched repo functions the model models (mapping.md
section 1):
  * `django.db.models.fields.Field.get_choices` data-row branch
      <-> related_choice_rows   (forward relation site)
  * `django.db.models.fields.reverse_related.ForeignObjectRel.get_choices`
      <-> reverse_choice_rows   (reverse relation site)
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched code importable. The script itself
applies no patch.

TYPE BRIDGE (mapping.md section 2):
  * base: List[int]      <-> the pks of the base queryset in base-manager
                             emission order (Meta.ordering applied). Read
                             fresh per case from the real base queryset.
  * ordering: List[int]  <-> the field-name tuple; only EMPTINESS is observed
                             by the impl, so the carrier is
                             list(range(len(names))); the name contents feed
                             the apply_order_by bridge, which runs the real
                             order_by with the actual names.
  * Result(): List[int]  <-> the row ORDER of the choices' data rows: the pk
                             of each (pk_value, label) pair in sequence. The
                             (pk, str) projection is order-preserving and
                             elided; the optional blank prefix is untouched
                             by the behaviour under spec, so when
                             include_blank is exercised the known blank
                             prefix is checked then stripped before the
                             data-row comparison.

INPUT DOMAIN: the model's preconditions only require the two list arguments
to exist, so every (base queryset, ordering tuple) pair is
Requires-satisfying. The fixture varies: the pk subset backing the forward
site's base queryset (via its filtering argument), the ordering tuple
(empty / single / multi-field / ascending / descending), the related model's
Meta.ordering (empty and non-trivial in both directions -- the empty-ordering
branch is only discriminating when the base manager has its own order), and
include_blank on the oracle side. Boundary matrix (every discrete
combination, both sites) + >= 1e5 fuzz draws. Pinned fuzz seed: 114000.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random for fuzz).
"""
import json
import random
import sys

SEED = 114000
N_FUZZ_FWD = 55_000
N_FUZZ_REV = 50_000


# --- bridge context for the @ContractOnly callee --------------------------------
# Installed per case: the concrete queryset the base carrier abstracts and the
# real field-name tuple the ordering carrier abstracts.

_CTX = {"base_qs": None, "names": ()}


def apply_order_by(base, ordering):
    # REAL repo callee (the axiomatized reorder operation): order_by(*names)
    # on the concrete base queryset, returned as the row-identity list.
    return [x.pk for x in _CTX["base_qs"].order_by(*_CTX["names"])]


# --- impl region of model.py, verbatim (contracts stripped) ---------------------

def copy_rows(base):
    out = []  # type: List[int]
    i = 0
    while i < len(base):
        out.append(base[i])
        i = i + 1
    return out


def related_choice_rows(base, ordering):
    if len(ordering) > 0:
        qs = apply_order_by(base, ordering)  # type: List[int]
        return qs
    res = copy_rows(base)  # type: List[int]
    return res


def reverse_choice_rows(base, ordering):
    if len(ordering) > 0:
        qs = apply_order_by(base, ordering)  # type: List[int]
        return qs
    res = copy_rows(base)  # type: List[int]
    return res


# --- fixture ---------------------------------------------------------------------

def _configure():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": ":memory:",
                }
            },
        )
    django.setup()


def build_models():
    from django.db import models, connection

    class Author(models.Model):
        name = models.CharField(max_length=32)

        class Meta:
            app_label = "confcheck"
            ordering = ("name",)

        def __str__(self):
            return self.name

    class Book(models.Model):
        title = models.CharField(max_length=32)
        author = models.ForeignKey(Author, models.CASCADE,
                                   related_name="books")

        class Meta:
            app_label = "confcheck"
            ordering = ("title",)

        def __str__(self):
            return self.title

    with connection.schema_editor() as se:
        se.create_model(Author)
        se.create_model(Book)
    return Author, Book


def data_rows(choices, include_blank, blank):
    """Strip the (untouched, unmodeled) blank prefix from the oracle output
    and return the data rows' pk sequence. Returns None if the blank prefix
    is malformed (counts as a disagreement)."""
    choices = list(choices)
    if include_blank:
        if choices[:len(blank)] != blank:
            return None
        choices = choices[len(blank):]
    return [pk for pk, _label in choices]


def main():
    _configure()
    from django.db.models.fields import BLANK_CHOICE_DASH
    blank = list(BLANK_CHOICE_DASH)

    Author, Book = build_models()

    # Insertion order deliberately differs from every field order so that a
    # dropped or spuriously-applied reordering is visible in the pk sequence.
    a1 = Author.objects.create(name="delta")
    a2 = Author.objects.create(name="bravo")
    a3 = Author.objects.create(name="echo")
    a4 = Author.objects.create(name="alpha")
    a5 = Author.objects.create(name="charlie")
    authors = [a1, a2, a3, a4, a5]
    for i, a in enumerate(authors):
        Book.objects.create(title="t%d" % ((7 * i) % 5), author=a)

    fk_field = Book._meta.get_field("author")     # forward relation field
    rev_rel = fk_field.remote_field               # the reverse relation object

    all_pks = tuple(a.pk for a in authors)
    subsets = [
        all_pks, (),
        (a1.pk,), (a4.pk,),
        (a2.pk, a4.pk), (a1.pk, a3.pk, a5.pk),
        (a5.pk, a4.pk, a3.pk, a2.pk, a1.pk),
    ]
    fwd_orderings = [(), ("name",), ("-name",), ("id",), ("-id",),
                     ("name", "-id")]
    rev_orderings = [(), ("title",), ("-title",), ("id",), ("-id",),
                     ("title", "-id")]
    meta_pool = [(), ("name",), ("-name",)]
    rev_meta_pool = [(), ("title",), ("-title",)]
    blanks = [False, True]

    state = {"checked": 0}

    def fail(site, meta_ord, extra, names, ib, shadow_out, real_rows):
        print("DISAGREEMENT at site=%s" % site)
        print("  Meta.ordering=%r  %s  ordering=%r  include_blank=%r"
              % (meta_ord, extra, names, ib))
        print("  shadow=%r" % (shadow_out,))
        print("  real  =%r" % (real_rows,))
        return 1

    def check_forward(meta_ord, subset, names, ib):
        Author._meta.ordering = meta_ord
        limit = {"pk__in": list(subset)}
        base_qs = Author._default_manager.complex_filter(limit)
        base = [x.pk for x in base_qs]                 # base carrier
        ordering = list(range(len(names)))             # emptiness carrier
        _CTX["base_qs"] = base_qs
        _CTX["names"] = names
        shadow_out = related_choice_rows(base, ordering)
        real = fk_field.get_choices(include_blank=ib,
                                    limit_choices_to=limit,
                                    ordering=names)
        real_rows = data_rows(real, ib, blank)
        state["checked"] += 1
        if real_rows is None or shadow_out != real_rows:
            return fail("forward", meta_ord, "subset=%r" % (subset,),
                        names, ib, shadow_out, real_rows)
        return 0

    def check_reverse(meta_ord, names, ib):
        Book._meta.ordering = meta_ord
        base_qs = Book._default_manager.all()
        base = [x.pk for x in base_qs]
        ordering = list(range(len(names)))
        _CTX["base_qs"] = base_qs
        _CTX["names"] = names
        shadow_out = reverse_choice_rows(base, ordering)
        real = rev_rel.get_choices(include_blank=ib, ordering=names)
        real_rows = data_rows(real, ib, blank)
        state["checked"] += 1
        if real_rows is None or shadow_out != real_rows:
            return fail("reverse", meta_ord, "", names, ib,
                        shadow_out, real_rows)
        return 0

    # Boundary matrix: every discrete combination at both sites.
    for meta_ord in meta_pool:
        for subset in subsets:
            for names in fwd_orderings:
                for ib in blanks:
                    if check_forward(meta_ord, subset, names, ib):
                        return 1
    for meta_ord in rev_meta_pool:
        for names in rev_orderings:
            for ib in blanks:
                if check_reverse(meta_ord, names, ib):
                    return 1

    # Fuzz: pinned seed, random draws over the same Requires-satisfying space
    # (random pk subsets included, beyond the boundary list).
    rng = random.Random(SEED)
    for _ in range(N_FUZZ_FWD):
        meta_ord = rng.choice(meta_pool)
        k = rng.randint(0, len(all_pks))
        subset = tuple(rng.sample(all_pks, k))
        names = rng.choice(fwd_orderings)
        ib = rng.random() < 0.25
        if check_forward(meta_ord, subset, names, ib):
            return 1
    for _ in range(N_FUZZ_REV):
        meta_ord = rng.choice(rev_meta_pool)
        names = rng.choice(rev_orderings)
        ib = rng.random() < 0.25
        if check_reverse(meta_ord, names, ib):
            return 1

    print("G-CONF OK: contract-stripped impl region == real patched "
          "get_choices row order at both sites on %d inputs "
          "(boundary matrix + %d fuzz, seed %d)."
          % (state["checked"], N_FUZZ_FWD + N_FUZZ_REV, SEED))
    print(json.dumps({
        "checked": state["checked"], "disagreements": 0, "seed": SEED,
        "shadow": "direct (contract-stripped impl region; apply_order_by "
                  "bridged to the real QuerySet.order_by)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
