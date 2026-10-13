#!/usr/bin/env python
"""G-CONF: differential conformance for django__django-12858.

Runs INSIDE the instance image with the gold patch applied (PYTHONPATH=/testbed).
Compares the Python R/I shadow of `implementation_orderingFieldCheck` (the Lean
impl, transliterated op-for-op per refinement.md) against the REAL patched
`Model._check_ordering` E015-report decision, over a synthetic model graph and
>=1e5 fuzzed relation-spanning ordering entries. Zero disagreements => exit 0.

Model (refinement.md): for one relation-spanning ordering entry, walk its
segments from the originating model, threading the last resolved field `fld` and
the current model context `ctx`. A resolved relation field descends into its
related model; a resolved non-relation field exhausts the context. An unresolved
segment is reported (models.E015) unless it is a transform OR a registered lookup
of the preceding resolved field (the `$`->lookup post-patch widening).

  * Oracle  = REAL patched `Model._check_ordering`: set the model's
              `Meta.ordering` to the single entry, run the check, observe whether
              a models.E015 error is produced for that entry.
  * Shadow  = the Lean walk transliterated, using the REAL model machinery
              (`_meta.get_field` / `is_relation` / `get_path_info` /
              `get_transform` / `get_lookup`) as the A-reference parameters.

Type bijection (mapping.md): parts:List String <-> entry.split('__');
start:Model <-> the originating model; result:Bool <-> E015 reported for entry.
stdlib-only fuzzing (pinned seed).
"""
import os
import random
import sys
import tempfile

SEED = 12858
N_RANDOM = 120_000  # >= 1e5


def setup_django():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "t"))
    open(os.path.join(d, "t", "__init__.py"), "w").close()
    open(os.path.join(d, "t", "models.py"), "w").close()
    sys.path.insert(0, d)
    import django
    from django.conf import settings
    settings.configure(
        DEBUG=True,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                               "NAME": ":memory:"}},
        INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth", "t"],
        USE_TZ=True,
    )
    django.setup()


def build_graph():
    from django.db import models
    from django.db.models.functions import Lower

    # Register a transform (Lower) on CharField so a segment can be a transform
    # that is NOT a lookup; isnull/exact/contains/gt are builtin lookups.
    try:
        models.CharField.register_lookup(Lower)
    except Exception:
        pass

    class Product(models.Model):
        parent = models.ForeignKey("self", null=True, on_delete=models.CASCADE)
        name = models.CharField(max_length=100)

        class Meta:
            app_label = "t"

    class Supply(models.Model):
        product = models.ForeignKey(Product, on_delete=models.CASCADE)

        class Meta:
            app_label = "t"

    class Stock(models.Model):
        supply = models.ForeignKey(Supply, on_delete=models.CASCADE)
        title = models.CharField(max_length=100)

        class Meta:
            app_label = "t"

    return Stock


# ---- shadow: transliteration of implementation_orderingFieldCheck ----------

def shadow(start_model, parts):
    from django.core.exceptions import FieldDoesNotExist

    def report(fld, part):
        # reportSegment (post-patch): report unless `part` is a transform OR a
        # registered lookup of the preceding resolved field `fld`.
        if fld is None:
            return True
        return fld.get_transform(part) is None and fld.get_lookup(part) is None

    fld = None
    cur = start_model           # ctx = some start
    exhausted = False           # ctx = none
    err = False
    for part in parts:
        if not exhausted:
            try:
                if part == "pk":
                    f = cur._meta.pk
                else:
                    f = cur._meta.get_field(part)
                fld = f
                if f.is_relation:
                    cur = f.get_path_info()[-1].to_opts.model
                else:
                    exhausted = True
            except (FieldDoesNotExist, AttributeError):
                if report(fld, part):
                    err = True
        else:
            if report(fld, part):
                err = True
    return err


# ---- outcome capture (differential over bool OR raised-exception) -----------
#
# The real patched `_check_ordering` walk can leave `fld` bound to a REVERSE
# relation object (e.g. `ManyToOneRel`), which — unlike a forward field — has no
# `get_transform`/`get_lookup` method. On an entry whose later segment is
# unresolved after such a step (e.g. `...__<reverse-accessor>__<missing>...`),
# the patched report condition `fld.get_transform(part)` raises an UNCAUGHT
# `AttributeError` inside `_check_ordering` itself. This is a pre-existing latent
# crash, present identically pre- and post-patch, orthogonal to the E015 fix.
#
# The R/I shadow is a faithful transliteration that calls the SAME real
# machinery (`fld.get_transform`/`fld.get_lookup`), so on exactly those entries
# it raises the SAME `AttributeError`. Both legs crashing identically is
# AGREEMENT, not divergence. So we capture each leg's outcome as a comparable
# token — ("ok", bool) on a clean return, or ("raised", <ExceptionTypeName>) on
# an exception — and diff the tokens. A divergence is a genuine disagreement:
# one leg reports E015 while the other does not, or the two raise different
# exception types, or one raises while the other returns.

def _outcome(fn):
    try:
        return ("ok", bool(fn()))
    except Exception as exc:  # noqa: BLE001 — outcome is the exception's identity
        # Compare the FULL exception identity (module + qualified name), not just
        # the bare class name, so two distinct exceptions that happen to share a
        # name cannot collapse into a spurious agreement.
        t = type(exc)
        return ("raised", t.__module__, t.__qualname__)


# ---- oracle: REAL patched Model._check_ordering ----------------------------

def oracle(model, entry):
    # _check_ordering reads cls._meta.ordering fresh each call; mutate it to the
    # single relation-spanning entry under test and observe E015 for it.
    model._meta.ordering = (entry,)
    model._meta.order_with_respect_to = None
    model._meta._ordering_clash = False
    errors = model._check_ordering()
    return any(getattr(e, "id", None) == "models.E015" for e in errors)


# ---- fuzzing ----------------------------------------------------------------

SEGMENTS = [
    "supply", "product", "parent", "name", "title",   # field / relation names
    "pk", "id",                                        # pk alias / id
    "isnull", "exact", "contains", "gt", "lte",        # builtin lookups
    "lower",                                           # registered transform
    "nonexistent", "zzz", "foo",                       # neither
]

FIXED = [
    "supply__product__parent__isnull",   # the issue's path (lookup) -> no E015
    "title__isnull",                     # FAIL_TO_PASS shape: lookup, no E015
    "title__lower",                      # transform, no E015
    "title__nonexistent",                # neither -> E015
    "supply__bogus",                     # missing on FK, no tf/lookup -> E015
    "supply__product__name__upper",      # 'upper' not registered -> E015
    "supply__product__parent",           # resolves to a field -> no E015
    "supply__product__parent__name",     # descend then field -> no E015
    "name__isnull",                      # (single-relation? no '__'? has '__') lookup
    "pk__isnull",                        # pk alias then lookup
    "supply__id__isnull",                # id is non-relation -> exhaust -> lookup
    "supply__product__zzz__isnull",      # missing then lookup-of-None -> E015
]


def rand_entry(rng):
    n = rng.randint(2, 5)
    parts = [rng.choice(SEGMENTS) for _ in range(n)]
    return "__".join(parts)


def main():
    setup_django()
    Stock = build_graph()

    rng = random.Random(SEED)
    entries = list(FIXED)
    while len(entries) < N_RANDOM:
        e = rand_entry(rng)
        if "__" in e:  # only relation-spanning entries hit the changed loop
            entries.append(e)

    disagreements = 0
    first = None
    checked = 0
    for entry in entries:
        parts = entry.split("__")
        # Compare full outcomes: ("ok", bool) on clean return, ("raised", type)
        # on an exception. An entry on which BOTH the real patched walk and the
        # R/I shadow raise the same exception type is agreement (a pre-existing
        # crash reproduced faithfully), not a divergence.
        o = _outcome(lambda: oracle(Stock, entry))
        s = _outcome(lambda: shadow(Stock, parts))
        checked += 1
        if o != s:
            disagreements += 1
            if first is None:
                first = (entry, o, s)
            if disagreements <= 5:
                print("MISMATCH %r: real=%r shadow=%r" % (entry, o, s))

    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, checked, first))
        return 1
    print("G-CONF OK: %d entries, 0 disagreements" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
