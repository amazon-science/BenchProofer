#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15278 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (`ColumnSpec.__init__` loses its Ensures; `add_column` loses
its Requires/Ensures block). The single @ContractOnly callee,
`has_effective_default(col)`, delegates to the REAL repo function it stands
for per mapping.md section 3.1: the boolean observation
`editor.effective_default(field) is not None` evaluated on the real backend
schema editor against the real field the ColumnSpec was bridged from. The
@Pure helper `needs_full_rebuild` is copied over as a plain function (the
impl region itself does not call it, but it is part of the model's pure
region). No PSeq usage in this bundle; carriers are plain bools/ints.

ORACLE: the REAL patched routing decision the model models per mapping.md —
`django.db.backends.sqlite3.schema.DatabaseSchemaEditor.add_field(model,
field)`. The gate applies patch.diff to /testbed before this script runs and
sets PYTHONPATH=/testbed, so the import picks up the patched code. The two
route targets are stubbed to route recorders (the model abstracts each
unchanged branch body to its label: 1 for the table-rebuild route via
`_remake_table`, 0 for the in-place append route via the base class
`add_field`), so calling the real `add_field` records exactly which route
its predicate — the behaviour under test — selects, without executing DDL.

Type bridge (mapping.md section 2): a real model `Field` object maps to a
`ColumnSpec` via `field.primary_key -> col.primary_key`,
`field.unique -> col.unique`, `field.null -> col.nullable`; the effective-
default observation is bridged through the @ContractOnly delegation above
(the ColumnSpec carries a reference to its source field for that purpose
only — the shadow impl never reads it directly). Route ints compare with
`==`.

Input domain: the model's preconditions demand only read access to the three
boolean flags, so every well-formed field is Requires-satisfying. Boundary
cases enumerate all 16 combinations of (primary_key, unique, nullable,
default-present) over an integer field, plus the axiom_check.py witness set
(nullable relational one-to-one/foreign-key fields, blank char fields whose
effective default is the empty string, auto-now datetime fields, binary
fields). Fuzz draws random field classes x flag combinations x
type-appropriate defaults (absent / literal / callable).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz draws.
Pinned fuzz seed: 15278.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import itertools
import json
import random
import sys
import uuid

SEED = 15278
N_FUZZ = 100_000


# --- shadow: model.py regions with contracts stripped ---------------------------

class ColumnSpec:
    def __init__(self, primary_key, unique, nullable):
        self.primary_key = primary_key
        self.unique = unique
        self.nullable = nullable
        self._real_field = None  # bridge handle for the @ContractOnly callee


# @ContractOnly callee: delegates to the REAL unchanged backend observation
# (a pure boolean read of the field's effective database default). Set up in
# main() once the schema editor exists.
_EDITOR = None


def has_effective_default(col):
    return _EDITOR.effective_default(col._real_field) is not None


# @Pure helper, decorator + Requires stripped (copied for completeness; the
# impl region below is the shadow actually diffed).
def needs_full_rebuild(col):
    return (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col))


def add_column(col):
    # impl region of model.py, verbatim
    if (col.primary_key or col.unique or
            (not col.nullable) or has_effective_default(col)):
        return 1
    else:
        return 0


# --- oracle plumbing --------------------------------------------------------------

def _setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            USE_TZ=False,
        )
    django.setup()


def _describe(field):
    return ("%s(primary_key=%r, unique=%r, null=%r, has_default=%r, "
            "blank=%r)" % (type(field).__name__, field.primary_key,
                           field.unique, field.null, field.has_default(),
                           field.blank))


def main():
    global _EDITOR
    _setup_django()
    from django.db import connection
    from django.db.models import (
        BigIntegerField, BinaryField, BooleanField, CharField, DateField,
        DateTimeField, DecimalField, EmailField, FloatField, ForeignKey,
        IntegerField, OneToOneField, PositiveIntegerField, SlugField,
        SmallIntegerField, TextField, TimeField, UUIDField,
    )
    from django.db.models.deletion import CASCADE, SET_NULL
    from django.db.backends.sqlite3.schema import DatabaseSchemaEditor
    from django.db.backends.base.schema import BaseDatabaseSchemaEditor
    from django.contrib.auth.models import User

    # Route recorder: stub the two (unchanged, abstracted-to-labels) branch
    # targets so the REAL patched add_field records which route it selects.
    routes = []

    def _rec_remake(self, model, create_field=None, delete_field=None,
                    alter_field=None):
        routes.append(1)

    def _rec_base_add(self, model, field):
        routes.append(0)

    DatabaseSchemaEditor._remake_table = _rec_remake
    BaseDatabaseSchemaEditor.add_field = _rec_base_add

    def real_route(editor, field):
        del routes[:]
        editor.add_field(User, field)  # REAL patched function under test
        assert len(routes) == 1, (
            "real add_field selected %d routes for %s"
            % (len(routes), _describe(field)))
        return routes[0]

    def shadow_route(field):
        col = ColumnSpec(bool(field.primary_key), bool(field.unique),
                         bool(field.null))
        col._real_field = field
        return add_column(col)

    def mk(field):
        field.set_attributes_from_name("probe")
        return field

    # --- boundary cases -----------------------------------------------------
    def boundary_fields():
        out = []
        # all 16 combinations of the four routing signals over IntegerField
        for pk, uq, nl, dflt in itertools.product(
                (False, True), repeat=4):
            kwargs = {"primary_key": pk, "unique": uq, "null": nl}
            if dflt:
                kwargs["default"] = 7
            out.append(mk(IntegerField(**kwargs)))
        # the axiom_check.py witness set
        out += [
            mk(OneToOneField(User, CASCADE, null=True)),
            mk(OneToOneField(User, SET_NULL, null=True, blank=True)),
            mk(ForeignKey(User, CASCADE, null=True)),
            mk(IntegerField(null=True)),
            mk(CharField(max_length=10, null=True)),
            mk(DateTimeField(null=True)),
            mk(IntegerField(null=False)),
            mk(IntegerField(null=True, unique=True)),
            mk(CharField(max_length=10, null=True, unique=True)),
            mk(IntegerField(primary_key=True)),
            mk(IntegerField(null=True, default=7)),
            mk(BooleanField(null=True, default=False)),
            mk(CharField(max_length=10, null=False, blank=True)),
            mk(BinaryField(null=True)),
            # auto-now datetimes carry an effective default
            mk(DateTimeField(null=True, auto_now=True)),
            mk(DateTimeField(null=True, auto_now_add=True)),
            # callable default
            mk(UUIDField(null=True, default=uuid.uuid4)),
            # blank text/binary (empty-string effective default when non-null)
            mk(TextField(null=False, blank=True)),
            mk(BinaryField(null=False, blank=True)),
        ]
        return out

    # --- fuzz ---------------------------------------------------------------
    rng = random.Random(SEED)

    def rand_field():
        pk = rng.random() < 0.25
        uq = rng.random() < 0.25
        nl = rng.random() < 0.5
        blank = rng.random() < 0.25
        want_default = rng.random() < 0.35
        roll = rng.random()
        if roll < 0.10:
            cls = OneToOneField if rng.random() < 0.5 else ForeignKey
            kwargs = {"null": nl, "blank": blank, "unique": uq,
                      "primary_key": pk}
            if want_default:
                kwargs["default"] = rng.randint(1, 1000)
            return mk(cls(User, CASCADE, **kwargs))
        makers = [
            (IntegerField, lambda: rng.randint(-10**9, 10**9), {}),
            (BigIntegerField, lambda: rng.randint(-10**12, 10**12), {}),
            (SmallIntegerField, lambda: rng.randint(-32768, 32767), {}),
            (PositiveIntegerField, lambda: rng.randint(0, 10**6), {}),
            (FloatField, lambda: rng.uniform(-1e6, 1e6), {}),
            (DecimalField, lambda: rng.randint(0, 999),
             {"max_digits": 6, "decimal_places": 2}),
            (BooleanField, lambda: rng.random() < 0.5, {}),
            (CharField, lambda: "v%d" % rng.randint(0, 999),
             {"max_length": 32}),
            (TextField, lambda: "t%d" % rng.randint(0, 999), {}),
            (SlugField, lambda: "s%d" % rng.randint(0, 999), {}),
            (EmailField, lambda: "a%d@example.com" % rng.randint(0, 99), {}),
            (BinaryField, lambda: b"\x00\x01", {}),
            (UUIDField, uuid.uuid4, {}),
            (DateField, None, {}),
            (TimeField, None, {}),
            (DateTimeField, None, {}),
        ]
        cls, mkdefault, extra = makers[rng.randrange(len(makers))]
        kwargs = dict(extra)
        kwargs.update(primary_key=pk, unique=uq, null=nl, blank=blank)
        if cls is DateTimeField and rng.random() < 0.3:
            kwargs["auto_now" if rng.random() < 0.5 else "auto_now_add"] = True
        elif want_default and mkdefault is not None:
            # half literal, half callable default
            if rng.random() < 0.5:
                kwargs["default"] = mkdefault()
            else:
                kwargs["default"] = mkdefault
        return mk(cls(**kwargs))

    checked = 0
    with connection.schema_editor(atomic=False) as editor:
        _EDITOR = editor

        def check(field):
            s = shadow_route(field)
            r = real_route(editor, field)
            if s != r:
                print("DISAGREEMENT\n  field=%s\n  shadow=%r\n  real=%r"
                      % (_describe(field), s, r))
                return False
            return True

        boundaries = boundary_fields()
        for field in boundaries:
            if not check(field):
                return 1
            checked += 1

        for _ in range(N_FUZZ):
            if not check(rand_field()):
                return 1
            checked += 1

    print("G-CONF OK: shadow impl route == real patched add_field route on "
          "%d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundaries), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "@ContractOnly callee delegates to the real "
                                "backend effective-default observation)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
