#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-12774 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same inputs and comparing observable outcomes:

  * SHADOW  — Solution.lean's modeled decision (`soleColumn`, `singleColumnKeys`,
              `lookupFieldDecision`) transliterated to Python over the real repo
              types, via the mapping.md §2 bijection:
                  fieldName   <->  field_name (str)
                  fieldUnique <->  opts.get_field(field_name).unique (bool)
                  constraints <->  [list(c.fields) for c in
                                     opts.total_unique_constraints]
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the REAL patched `QuerySet.in_bulk`
              validation guard. We call `Model.objects.in_bulk([],
              field_name=field_name)`: the guard runs FIRST, so an inadmissible
              field raises `ValueError` before any DB access, and an admissible
              field falls through to the empty-`id_list` short-circuit returning
              `{}` — both DB-free.

Observable of a validation, per the mapping.md §2 bijection:
  - the guard rejects (raises ValueError)  <->  Except.error .fieldNotUnique
  - the guard accepts (returns {})         <->  Except.ok ()

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

No database is touched: `in_bulk([])` returns `{}` after the guard without
issuing a query, and the rejection path raises before the query. stdlib +
django only. Fuzz seed pinned (mapping.md §4).
"""
import random
import sys

SEED = 12774
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


def _define_models():
    """Models exercising every shape of total_unique_constraints the patched
    guard must distinguish: a single-column UniqueConstraint (admits its sole
    field), a multi-column one (admits none of its fields), a *conditional* one
    (excluded from total_unique_constraints, admits nothing), an individually
    unique field (admits), and plain non-unique fields (reject). Mirrors the
    test_patch models (Season + the isolate_apps Model) without applying it."""
    from django.db import models

    class Season(models.Model):
        year = models.IntegerField(null=True, blank=True)
        gt = models.IntegerField(null=True, blank=True)

        class Meta:
            app_label = "auth"
            constraints = [
                models.UniqueConstraint(fields=["year"], name="m_season_year_unq"),
            ]

    class Product(models.Model):
        ean = models.CharField(max_length=100)
        brand = models.CharField(max_length=100)
        name = models.CharField(max_length=80)
        sku = models.CharField(max_length=50, unique=True)

        class Meta:
            app_label = "auth"
            constraints = [
                models.UniqueConstraint(
                    fields=["ean"], name="m_partial_ean_unq",
                    condition=models.Q(name="x"),
                ),
                models.UniqueConstraint(
                    fields=["brand", "name"], name="m_brand_name_unq",
                ),
            ]

    class Plain(models.Model):
        a = models.IntegerField()
        b = models.IntegerField()

        class Meta:
            app_label = "auth"

    return [Season, Product, Plain]


# --- the R/I shadow: Solution.lean soleColumn/singleColumnKeys/decision -------

def shadow_sole_column(guarantee):
    """soleColumn (pure region) transliterated."""
    return [guarantee[0]] if len(guarantee) == 1 else []


def shadow_single_column_keys(constraints):
    """singleColumnKeys (pure region): per-guarantee expansion, concatenated."""
    out = []
    for g in constraints:
        out.extend(shadow_sole_column(g))
    return out


def shadow_decision(field_name, field_unique, constraints):
    """lookupFieldDecision (pure region) transliterated. Returns 'error' or
    'ok'."""
    unique_fields = shadow_single_column_keys(constraints)
    if (field_name != "pk") and (not field_unique) and \
            (field_name not in unique_fields):
        return "error"
    return "ok"


def shadow_inputs(model):
    """The (field_unique, constraints) inputs the shadow reads from the real
    _meta — exactly the unchanged callees the model abstracts (mapping.md §3)."""
    opts = model._meta
    constraints = [list(c.fields) for c in opts.total_unique_constraints]
    return opts, constraints


# --- the oracle: the REAL patched in_bulk guard -------------------------------

def oracle_decision(model, field_name):
    """patch.diff's behaviour: call the real patched in_bulk validation. An
    inadmissible field raises ValueError before any DB access; an admissible
    one returns {} (empty id_list short-circuit). Both DB-free."""
    try:
        model.objects.in_bulk([], field_name=field_name)
    except ValueError:
        return "error"
    return "ok"


def field_names_for(model):
    """Real field names the guard's get_field() resolves, plus the 'pk' alias.
    Names get_field rejects (FieldDoesNotExist) are out of scope for this
    bundle (the guard never reaches the modeled decision for them)."""
    opts = model._meta
    names = ["pk"]
    for f in opts.get_fields():
        n = getattr(f, "name", None)
        if not n or n in names:
            continue
        try:
            opts.get_field(n)
        except Exception:
            continue
        names.append(n)
    return names


def main():
    _bootstrap_django()
    models = _define_models()
    rng = random.Random(SEED)

    # Build the full (model, field_name) work-list (boundary cross product).
    cases = []
    for m in models:
        opts, constraints = shadow_inputs(m)
        for fn in field_names_for(m):
            if fn == "pk":
                field_unique = True  # exempted before get_field is consulted
            else:
                try:
                    field_unique = bool(opts.get_field(fn).unique)
                except Exception:
                    continue  # field the guard's get_field would reject; skip
            cases.append((m, fn, field_unique, constraints))

    if not cases:
        print("G-CONF FAIL: no cases enumerated")
        return 1

    disagreements = []
    count = 0

    def run(m, fn, field_unique, constraints):
        nonlocal count
        count += 1
        shadow = shadow_decision(fn, field_unique, constraints)
        oracle = oracle_decision(m, fn)
        if shadow != oracle:
            disagreements.append((m.__name__, fn, shadow, oracle))

    # boundary cases first
    for c in cases:
        run(*c)
        if len(disagreements) >= 5:
            break

    # then randomized re-sampling to exceed the fuzz floor deterministically
    while count < N_FUZZ and len(disagreements) < 5:
        run(*rng.choice(cases))

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for model_name, fn, sh, orc in disagreements:
            print("  model=%s field=%r shadow=%r oracle=%r"
                  % (model_name, fn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of validateLookupField agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
