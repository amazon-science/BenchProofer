#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-11400 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour: the real
`Field.get_choices` (forward) and `ForeignObjectRel.get_choices` (reverse)
ordering-fallback, exercised end-to-end by actually materializing choices against
an in-memory SQLite database — exactly the issue's reproduction.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled rule, transliterated to Python over the
              real repo types via the mapping.md §2 bijection:
                  effective_ordering(default_ordering, requested) =
                      requested if requested else default_ordering
              followed by the UNCHANGED shared materialization (order the related
              rows by that ordering specification, then read off the choices) —
              the same continuation both the buggy and fixed code reach. There
              are NO A-tagged ops (no consumed axioms, no deep-model reference),
              so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `get_choices`. We call
              the patched forward `Field.get_choices(include_blank=False,
              ordering=requested)` and the patched reverse
              `field.remote_field.get_choices(include_blank=False,
              ordering=requested)` and read back the real ordered choice list.
              The bug is precisely that an EMPTY `requested` used to clear the
              related model's intrinsic `Meta.ordering` (forward) / order nothing
              at all (reverse); the patched code falls back to the default.

`restrictedChoices` (the RelatedOnlyFieldListFilter plumbing) adds no new R/I op
beyond `orderedChoices`: it is the method-call composition
`orderedChoices defaultOrdering adminOrdering` (an I-tagged callee-under-spec
call), i.e. it routes its configured ordering as the `requested` argument to the
SAME kernel. So driving `get_choices` over many `requested` orderings — empty and
non-empty, with and without a `Meta.ordering` default — mechanically covers the
R/I content of BOTH modeled methods.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. stdlib + django only; in-memory
SQLite. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 11400
N_FUZZ = 100_000


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            USE_TZ=True,
        )
    django.setup()


_bootstrap_django()

from django.db import connection, models  # noqa: E402  (after django.setup())


# A related model whose choices are materialized, and a holder with a FK into
# it. `name`/`pos` are plain, distinct-valued columns so an ordering by either is
# total and Python's sort matches SQLite's BINARY/numeric collation. Defined at
# module top level so they are real, ordinary models.
class Related(models.Model):
    name = models.CharField(max_length=20)
    pos = models.IntegerField()

    class Meta:
        app_label = "auth"

    def __str__(self):
        return self.name


class Holder(models.Model):
    label = models.CharField(max_length=20)
    sortkey = models.IntegerField()
    rel = models.ForeignKey(Related, models.CASCADE, related_name="holders")

    class Meta:
        app_label = "auth"

    def __str__(self):
        return self.label


def _sort_key_spec(spec):
    """A single ordering key like 'name' or '-pos' -> (attr, reverse)."""
    if spec.startswith("-"):
        return spec[1:], True
    return spec, False


def shadow_order(objs, ordering):
    """The R/I shadow: order `objs` by the ordering specification `ordering`
    (a sequence of field names, possibly '-'-prefixed). This is the UNCHANGED
    materialization continuation, applied to whatever ordering specification the
    modeled kernel selects. Multi-key stable sort: apply keys right-to-left."""
    out = list(objs)
    for spec in reversed(list(ordering)):
        attr, rev = _sort_key_spec(spec)
        out.sort(key=lambda o, a=attr: getattr(o, a), reverse=rev)
    return out


def effective_ordering(default_ordering, requested):
    """effectiveOrdering transliterated: an explicit non-empty request governs;
    an empty request falls back to the intrinsic default ordering."""
    return tuple(requested) if requested else tuple(default_ordering)


def shadow_forward(field, requested, default_ordering):
    """SHADOW of the forward Field.get_choices ordering: select the effective
    ordering, materialize Related rows under it, read off (pk, str)."""
    eff = effective_ordering(default_ordering, requested)
    rows = shadow_order(list(Related.objects.all()), eff)
    return [(obj.pk, str(obj)) for obj in rows]


def shadow_reverse(rel, requested, default_ordering):
    """SHADOW of the reverse ForeignObjectRel.get_choices ordering: same kernel,
    materializing Holder rows (the reverse related_model) under the effective
    ordering, read off (pk, str)."""
    eff = effective_ordering(default_ordering, requested)
    rows = shadow_order(list(Holder.objects.all()), eff)
    return [(obj.pk, str(obj)) for obj in rows]


def main():
    with connection.schema_editor() as se:
        se.create_model(Related)
        se.create_model(Holder)

    # Distinct names/positions so every single-key ordering is total.
    related = [
        Related.objects.create(name=n, pos=p)
        for n, p in [("delta", 3), ("alpha", 1), ("charlie", 4), ("bravo", 2)]
    ]
    holders = [
        Holder.objects.create(label=l, sortkey=s, rel=related[i % len(related)])
        for i, (l, s) in enumerate(
            [("h_w", 30), ("h_x", 10), ("h_y", 40), ("h_z", 20), ("h_v", 50)]
        )
    ]

    field = Holder._meta.get_field("rel")        # forward FK Field
    rel = field.remote_field                      # reverse ForeignObjectRel

    # Real patched callees (the ORACLE).
    def oracle_forward(requested):
        return field.get_choices(include_blank=False, ordering=requested)

    def oracle_reverse(requested):
        return rel.get_choices(include_blank=False, ordering=requested)

    # The ordering specifications we drive through the kernel: empty (the fix's
    # fallback trigger), and assorted single/double keys, ascending/descending.
    REQ_SPECS = [
        (),
        ("name",), ("-name",), ("pos",), ("-pos",),
        ("name", "pos"), ("-pos", "name"),
    ]
    REQ_SPECS_REV = [
        (),
        ("label",), ("-label",), ("sortkey",), ("-sortkey",),
        ("label", "sortkey"), ("-sortkey", "label"),
    ]
    # The intrinsic default orderings (Meta.ordering) we sweep, including the
    # no-default case (empty). The fallback must use these when requested empty.
    DEFAULTS_FWD = [(), ("name",), ("-name",), ("pos",), ("-pos",)]
    DEFAULTS_REV = [(), ("label",), ("-label",), ("sortkey",), ("-sortkey",)]

    disagreements = []
    count = 0

    def check_forward(requested, default_ordering):
        nonlocal count
        count += 1
        # Install the related model's intrinsic default ordering, then observe.
        Related._meta.ordering = tuple(default_ordering)
        try:
            shadow = shadow_forward(field, requested, default_ordering)
            oracle = oracle_forward(requested)
        finally:
            Related._meta.ordering = ()
        # When the EFFECTIVE ordering is empty (no request, no default), SQLite
        # returns rows in unspecified order; skip that ambiguous case (the fix
        # changes nothing there — both legs hit the same unordered manager).
        if not effective_ordering(default_ordering, requested):
            return
        if list(shadow) != list(oracle):
            disagreements.append(("forward", requested, default_ordering,
                                  shadow, oracle))

    def check_reverse(requested, default_ordering):
        nonlocal count
        count += 1
        Holder._meta.ordering = tuple(default_ordering)
        try:
            shadow = shadow_reverse(rel, requested, default_ordering)
            oracle = oracle_reverse(requested)
        finally:
            Holder._meta.ordering = ()
        if not effective_ordering(default_ordering, requested):
            return
        if list(shadow) != list(oracle):
            disagreements.append(("reverse", requested, default_ordering,
                                  shadow, oracle))

    # Boundary sweep: every (requested, default) combination on both sites.
    for req in REQ_SPECS:
        for dft in DEFAULTS_FWD:
            check_forward(req, dft)
    for req in REQ_SPECS_REV:
        for dft in DEFAULTS_REV:
            check_reverse(req, dft)

    # Randomized fuzz to >= N_FUZZ: keep drawing (requested, default) pairs and
    # checking both sites on the SAME database.
    rng = random.Random(SEED)
    while count < N_FUZZ:
        req = rng.choice(REQ_SPECS)
        dft = rng.choice(DEFAULTS_FWD)
        check_forward(req, dft)
        req = rng.choice(REQ_SPECS_REV)
        dft = rng.choice(DEFAULTS_REV)
        check_reverse(req, dft)
        if len(disagreements) >= 10:
            break

    if disagreements:
        print(f"G-CONF FAIL: {len(disagreements)} R/I disagreement(s) over "
              f"{count} observations (seed={SEED}):")
        for site, req, dft, sh, orc in disagreements[:10]:
            print(f"  site={site} requested={req} default={dft} "
                  f"shadow={sh} oracle={orc}")
        return 1

    print(f"G-CONF OK: R/I shadow of orderedChoices/restrictedChoices agrees "
          f"with patch.diff behaviour (real patched forward + reverse "
          f"get_choices) on {count} observations (seed={SEED}), 0 "
          f"disagreements.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
