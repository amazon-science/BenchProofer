#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12858 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped; the @Pure helper
`flag_path` copies over as a plain function. List[int] carriers stay plain
Python lists. There are no @ContractOnly callees in this bundle (the two
registry queries enter the model as boolean inputs).

ORACLE: the REAL patched repo function per mapping.md section 1 —
`Model._check_ordering` (django/db/models/base.py), whose related-field loop
contains the reporting decision under specification. The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed resolves
the patched module.

Type bridge (mapping.md section 2): each activation of the loop's
unresolved-segment handler contributes one observation triple
(reached_field, is_value_op, is_compare_op). The bridge derives the triples
by walking each ordering path with the SAME repo state the real loop reads
(`_meta.get_field` / `pk` alias / `get_path_info` for relation hops;
`get_transform` / `get_lookup` for the two operator-registry queries), one
triple per part whose resolution fails — the model's inputs are exactly these
observations, so the extraction walk mirrors the resolution structure while
the reporting DECISION stays solely in the shadow. The shadow's 0/1 output
flags map back to the per-activation presence of a reported invalid-ordering
error; the real function's observable is its returned error list (each entry
naming the offending path), compared in order against the activations the
shadow flags 1.

Input domain: Requires demands three equal-length 0/1 lists, i.e. any
sequence of per-activation observations; these are generated from orderings
of 1..4 multi-part paths (parts drawn from real field names on a small model
family with relation hops, the pk alias, registered comparison operators,
registered value-producing operators, and unresolvable names). Every ordering
entry contains a path separator so the function's unrelated tail validation
(outside the modeled region) contributes no errors. Boundary inputs cover the
comparison-operator acceptance, value-producing acceptance, no-field-reached
reporting, repeated failures within one path (multiple activations), and
direction prefixes.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz orderings.
Pinned fuzz seed: 12858.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (Django is the system under test).
"""
import json
import random
import re
import sys

SEED = 12858
N_FUZZ = 100_000


# --- pure helper from model.py, contracts stripped -----------------------------

def flag_path(reached_field, is_value_op, is_compare_op):
    if reached_field == 0 or (is_value_op == 0 and is_compare_op == 0):
        return 1
    return 0


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def select_reported_paths(reached_field, is_value_op, is_compare_op):
    errors = []
    i = 0
    while i < len(reached_field):
        if reached_field[i] == 0 or (is_value_op[i] == 0 and is_compare_op[i] == 0):
            errors.append(1)
        else:
            errors.append(0)
        i = i + 1
    return errors


_LOOKUP_MSG = re.compile(r"lookup '([^']*)'")


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()

    from django.db import models
    from django.core.exceptions import FieldDoesNotExist

    class Other(models.Model):
        name = models.CharField(max_length=20)
        created = models.DateTimeField()

        class Meta:
            app_label = "confcheck"

    class Main(models.Model):
        title = models.CharField(max_length=20)
        rank = models.IntegerField()
        fk = models.ForeignKey(Other, models.CASCADE)
        parent = models.ForeignKey("self", models.CASCADE, null=True)

        class Meta:
            app_label = "confcheck"
            ordering = ("fk__name",)

    def observations(cls, path):
        """Per-activation observation triples for one ordering path, read from
        the same repo state the real loop consults (bridge; mapping.md
        section 2). Returns a list of (reached_field, is_value_op,
        is_compare_op) 0/1 triples, one per part whose resolution fails, in
        activation order."""
        _cls = cls
        fld = None
        triples = []
        for part in path.split("__"):
            try:
                if part == "pk":
                    fld = _cls._meta.pk
                else:
                    fld = _cls._meta.get_field(part)
                if fld.is_relation:
                    _cls = fld.get_path_info()[-1].to_opts.model
                else:
                    _cls = None
            except (FieldDoesNotExist, AttributeError):
                reached = 1 if fld is not None else 0
                value_op = 1 if (fld is not None
                                 and fld.get_transform(part) is not None) else 0
                compare_op = 1 if (fld is not None
                                   and fld.get_lookup(part) is not None) else 0
                triples.append((reached, value_op, compare_op))
        return triples

    checked = [0]

    def check_one(ordering):
        # --- bridge: observation triples per activation, in loop order -------
        stripped = [f[1:] if f.startswith("-") else f for f in ordering]
        acts = []  # (path, triple) per activation
        for path in stripped:
            for triple in observations(Main, path):
                acts.append((path, triple))

        # --- shadow -----------------------------------------------------------
        flags = select_reported_paths([t[0] for _, t in acts],
                                      [t[1] for _, t in acts],
                                      [t[2] for _, t in acts])
        shadow_reports = [p for (p, _), f in zip(acts, flags) if f == 1]

        # --- oracle: the REAL patched validator -------------------------------
        Main._meta.ordering = tuple(ordering)
        errors = Main._check_ordering()
        real_reports = []
        for e in errors:
            if e.id != "models.E015":
                return ("DISAGREEMENT ordering=%r\n  real produced a non-E015 "
                        "error outside the modeled decision: %r"
                        % (ordering, e))
            m = _LOOKUP_MSG.search(e.msg)
            real_reports.append(m.group(1) if m else None)

        if shadow_reports != real_reports:
            return ("DISAGREEMENT ordering=%r\n  activations=%r\n"
                    "  shadow reports: %r\n  real reports:   %r"
                    % (ordering, acts, shadow_reports, real_reports))
        checked[0] += 1
        return None

    def run(ordering):
        err = check_one(ordering)
        if err:
            print(err)
            sys.exit(1)

    # --- boundary inputs -------------------------------------------------------
    boundary = [
        ("fk__name__isnull",),          # comparison operator: accepted
        ("fk__name__iexact",),          # comparison operator: accepted
        ("fk__created__year",),         # value-producing operator: accepted
        ("fk__created__year__gt",),     # transform then comparison: accepted
        ("fk__nonexistent",),           # neither kind: reported
        ("bogus__x",),                  # no field reached: two activations
        ("fk__nope__alsonope",),        # repeated failures on one path
        ("-fk__name__isnull",),         # direction prefix
        ("parent__fk__name",),          # relation hop chain, resolves fully
        ("parent__pk",),                # pk alias mid-path
        ("pk__isnull",),                # pk alias then comparison operator
        ("fk__name", "fk__nope", "parent__fk__name"),   # mixed multi-entry
        ("fk__name__isnull", "fk__created__nope", "rank__gt"),
        ("title__isnull", "title__nope__deeper"),
    ]
    for ordering in boundary:
        run(ordering)

    # --- fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    fields = ["title", "rank", "fk", "parent", "name", "created", "pk"]
    compare_ops = ["isnull", "iexact", "gt", "lt", "in", "exact",
                   "contains", "startswith", "range", "icontains"]
    value_ops = ["year", "month", "day", "date", "time", "hour"]
    bogus = ["nope", "xyz", "random123", "_private", "missing", "q"]
    vocab = fields + compare_ops + value_ops + bogus

    def rand_path(rng):
        n = rng.randint(2, 4)
        return "__".join(rng.choice(vocab) for _ in range(n))

    for _ in range(N_FUZZ):
        k = rng.randint(1, 4)
        ordering = tuple((("-" if rng.random() < 0.2 else "") + rand_path(rng))
                         for _ in range(k))
        run(ordering)

    print("G-CONF OK: shadow impl == real ordering-validation decision on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked[0], len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
