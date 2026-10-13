#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15561 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo objects, via the mapping.md
              bijection (`Field` ↔ `FieldDef`). A concrete `Field` is projected
              onto the three observable components `FieldDef` carries:
                - quotedColumn   = schema_editor.quote_name(field.column)
                - schemaIdentity = (path, args, kwargs) from field.deconstruct()
                                   with the schema-irrelevant attributes removed
                                   and `choices` pulled out separately
                - choices        = the field's enumerated choices kwarg
              Then `schemaAlterationNeeded` (the impl's I-logic) is applied:
              a rewrite is needed iff quotedColumn differs OR schemaIdentity
              differs — `choices` is deliberately NOT consulted. The projection
              ops (`deconstruct`, `quote_name`) are the UNCHANGED repo callees
              (the R-refinement bridge); the decision disjunction is the I op.
  * ORACLE  — `patch.diff`'s behaviour: the patched
              `BaseDatabaseSchemaEditor._field_should_be_altered(old, new)`
              applied at base_commit (the real correctness oracle, G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + django only (no hypothesis needed). The fuzz seed is pinned
(mapping.md §4) for a deterministic verdict.
"""
import itertools
import random
import sys

SEED = 15561
N_FUZZ = 100_000

# The schema-irrelevant attributes the projection strips from a field's
# reconstructed kwargs BEFORE forming schemaIdentity. This is the pre-patch
# `non_database_attrs` list (the unchanged set) — i.e. every attribute that was
# already known not to affect a column's schema. `choices` is intentionally
# NOT in this list: it is pulled out into FieldDef.choices separately, and the
# I-logic `schemaAlterationNeeded` decides (by ignoring it) that a choices-only
# difference needs no rewrite. That decision is exactly the modeled behaviour.
_STRIP_ATTRS = (
    "blank",
    "db_column",
    "editable",
    "error_messages",
    "help_text",
    "limit_choices_to",
    "on_delete",
    "related_name",
    "related_query_name",
    "validators",
    "verbose_name",
)


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            USE_TZ=False,
        )
    django.setup()


def _project(field, schema_editor):
    """Field -> FieldDef components (the R-refinement projection).

    Uses only the UNCHANGED repo callees `field.deconstruct()` and
    `schema_editor.quote_name()`; strips the schema-irrelevant attributes and
    splits `choices` out, mirroring the FieldDef structure in Solution.lean."""
    _, path, args, kwargs = field.deconstruct()
    kwargs = dict(kwargs)
    choices = repr(kwargs.pop("choices", None))
    for attr in _STRIP_ATTRS:
        kwargs.pop(attr, None)
    quoted_column = schema_editor.quote_name(field.column)
    schema_identity = repr((path, args, sorted(kwargs.items(), key=lambda kv: kv[0])))
    return quoted_column, schema_identity, choices


def shadow_alteration_needed(old_field, new_field, schema_editor):
    """schemaAlterationNeeded (Solution.lean, pure region) over projected
    FieldDefs: rewrite needed iff quotedColumn differs OR schemaIdentity
    differs. `choices` is observable but NOT consulted (presentation-only)."""
    a_col, a_id, _a_ch = _project(old_field, schema_editor)
    b_col, b_id, _b_ch = _project(new_field, schema_editor)
    return (a_col != b_col) or (a_id != b_id)


def oracle_alteration_needed(old_field, new_field, schema_editor):
    """patch.diff's behaviour: the patched _field_should_be_altered."""
    return bool(schema_editor._field_should_be_altered(old_field, new_field))


def _make_field(models, spec):
    """Build a concrete Field from a fuzz spec and bind its column name."""
    kind = spec["kind"]
    kwargs = {}
    if kind == "CharField":
        kwargs["max_length"] = spec["max_length"]
        f = models.CharField(**_common(kwargs, spec))
    elif kind == "IntegerField":
        f = models.IntegerField(**_common(kwargs, spec))
    elif kind == "TextField":
        f = models.TextField(**_common(kwargs, spec))
    elif kind == "BooleanField":
        f = models.BooleanField(**_common(kwargs, spec))
    else:
        f = models.SlugField(**_common(kwargs, spec))
    f.set_attributes_from_name(spec["name"])
    return f


def _common(kwargs, spec):
    # schema-relevant attributes (affect column definition)
    if spec["null"]:
        kwargs["null"] = True
    if spec["unique"]:
        kwargs["unique"] = True
    if spec["db_index"]:
        kwargs["db_index"] = True
    if spec["db_column"] is not None:
        kwargs["db_column"] = spec["db_column"]
    # schema-irrelevant / presentation attributes
    if spec["choices"] is not None:
        kwargs["choices"] = spec["choices"]
    if spec["help_text"]:
        kwargs["help_text"] = spec["help_text"]
    if spec["verbose_name"]:
        kwargs["verbose_name"] = spec["verbose_name"]
    if spec["blank"]:
        kwargs["blank"] = True
    if not spec["editable"]:
        kwargs["editable"] = False
    return kwargs


_KINDS = ["CharField", "IntegerField", "TextField", "BooleanField", "SlugField"]
_NAMES = ["col", "title", "name", "field_x"]
_CHOICE_SETS = [
    None,
    [("a", "A"), ("b", "B")],
    [("x", "X")],
    [(1, "one"), (2, "two")],
    [("a", "A"), ("b", "B"), ("c", "C")],
]
_HELP = ["", "help", "Some help text.", "another"]
_VERBOSE = ["", "Verbose", "a name"]


def _rand_spec(rng):
    kind = rng.choice(_KINDS)
    return {
        "kind": kind,
        "name": rng.choice(_NAMES),
        "max_length": rng.choice([5, 10, 255]),
        "null": rng.random() < 0.5,
        "unique": rng.random() < 0.3,
        "db_index": rng.random() < 0.3,
        "db_column": rng.choice([None, None, "explicit_col", "other_col"]),
        "choices": rng.choice(_CHOICE_SETS),
        "help_text": rng.choice(_HELP),
        "verbose_name": rng.choice(_VERBOSE),
        "blank": rng.random() < 0.5,
        "editable": rng.random() < 0.8,
    }


def _mutate(spec, rng):
    """Produce a second spec, biased toward differing in exactly one attribute
    (especially `choices` — the discriminating change) to stress the decision."""
    s = dict(spec)
    attr = rng.choice([
        "choices", "choices", "choices",        # over-weight the discriminator
        "help_text", "verbose_name", "blank", "editable", "db_column",
        "null", "unique", "db_index", "max_length", "name", "kind", "none",
    ])
    if attr == "none":
        return s
    if attr == "choices":
        s["choices"] = rng.choice(_CHOICE_SETS)
    elif attr == "help_text":
        s["help_text"] = rng.choice(_HELP)
    elif attr == "verbose_name":
        s["verbose_name"] = rng.choice(_VERBOSE)
    elif attr == "blank":
        s["blank"] = not s["blank"]
    elif attr == "editable":
        s["editable"] = not s["editable"]
    elif attr == "db_column":
        s["db_column"] = rng.choice([None, "explicit_col", "other_col"])
    elif attr == "null":
        s["null"] = not s["null"]
    elif attr == "unique":
        s["unique"] = not s["unique"]
    elif attr == "db_index":
        s["db_index"] = not s["db_index"]
    elif attr == "max_length":
        s["max_length"] = rng.choice([5, 10, 255])
    elif attr == "name":
        s["name"] = rng.choice(_NAMES)
    elif attr == "kind":
        s["kind"] = rng.choice(_KINDS)
    return s


def _boundary_pairs(models):
    """Deterministic boundary pairs (plan §4.1 step 4): the choices-only diff
    that drives the modeled behaviour, plus genuine schema diffs."""
    base = {"kind": "CharField", "name": "col", "max_length": 10, "null": False,
            "unique": False, "db_index": False, "db_column": None,
            "choices": None, "help_text": "", "verbose_name": "", "blank": False,
            "editable": True}
    pairs = []

    def with_(**over):
        s = dict(base)
        s.update(over)
        return s

    # identical -> no alteration
    pairs.append((base, dict(base)))
    # choices added only -> NO alteration (the issue's core case)
    pairs.append((base, with_(choices=[("a", "A"), ("b", "B")])))
    # choices changed only -> NO alteration
    pairs.append((with_(choices=[("a", "A")]), with_(choices=[("a", "A"), ("b", "B")])))
    # help_text only -> NO alteration
    pairs.append((base, with_(help_text="help")))
    # verbose_name only -> NO alteration
    pairs.append((base, with_(verbose_name="Verbose")))
    # db_column only, same resulting column -> NO alteration
    pairs.append((base, with_(db_column="col")))
    # max_length changed -> alteration required
    pairs.append((base, with_(max_length=255)))
    # null toggled -> alteration required
    pairs.append((base, with_(null=True)))
    # unique toggled -> alteration required
    pairs.append((base, with_(unique=True)))
    # column renamed via db_column -> alteration required
    pairs.append((base, with_(db_column="renamed")))
    # field type changed -> alteration required
    pairs.append((base, with_(kind="TextField", max_length=10)))
    # choices added AND schema change -> alteration required
    pairs.append((base, with_(choices=[("a", "A")], null=True)))
    return [(_make_field(models, a), _make_field(models, b)) for a, b in pairs]


def main():
    _bootstrap_django()
    from django.db import connection, models

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    with connection.schema_editor() as se:
        # boundary cases first
        for old_f, new_f in _boundary_pairs(models):
            count += 1
            sh = shadow_alteration_needed(old_f, new_f, se)
            orc = oracle_alteration_needed(old_f, new_f, se)
            if sh != orc:
                disagreements.append((_desc(old_f, new_f), sh, orc))
        # randomized fuzz
        for _ in range(N_FUZZ):
            count += 1
            a = _rand_spec(rng)
            b = _mutate(a, rng) if rng.random() < 0.7 else _rand_spec(rng)
            old_f = _make_field(models, a)
            new_f = _make_field(models, b)
            sh = shadow_alteration_needed(old_f, new_f, se)
            orc = oracle_alteration_needed(old_f, new_f, se)
            if sh != orc:
                disagreements.append((_desc(old_f, new_f), sh, orc))
                if len(disagreements) >= 5:
                    break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for d, sh, orc in disagreements:
            print("  %s shadow=%r oracle=%r" % (d, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of decideSchemaAlteration agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


def _desc(old_f, new_f):
    return "old=%s new=%s" % (old_f.deconstruct()[1:], new_f.deconstruct()[1:])


if __name__ == "__main__":
    sys.exit(main())
