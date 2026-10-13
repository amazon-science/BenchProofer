#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12663 (nagini).

SHADOW: the impl region of model.py ``output_field_identity``, copied verbatim
below with the contract calls (Requires/Ensures) stripped. The impl region is
plain executable Python over a minimal ``Selection`` object exposing two int
attributes, so it runs directly — no transliteration. There are no @Pure
helpers and no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo property the model models per mapping.md —
``django.db.models.sql.query.Query.output_field``, exercised on its
single-selection branch (``len(self.select) == 1``). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes the
patched module importable. Each probe installs one selected item as the sole
element of a real ``Query``'s ``select`` and reads the property.

Type bridge (mapping.md section 2): field objects are carried in the model as
integer identities. The bridge interns each distinct runtime object to a
distinct positive integer; the model's ``source`` is that identity when the
selected item exposes a usable (present and truthy) source-field attribute and
the sentinel ``0`` when the attribute is absent or falsy; the model's ``field``
is the identity of the item's resolved output field (a real object, so always
nonzero — the Requires ``sel.field != 0`` holds by construction). The oracle's
returned object is lifted through the same interning and compared to the
shadow's returned identity, so agreement means the property returned exactly
the object the model's choice designates.

Input domain: the Requires are the fractional access permissions plus
``sel.field != 0``; every generated item satisfies them. Boundary cases cover
real ``Col`` objects (with and without an explicit, differing resolved field)
plus items whose source attribute is absent or takes each falsy shape; fuzz
draws random combinations of presence/truthiness and object identities.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz probes.
Pinned fuzz seed: 12663.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 12663
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped ----------
# (comment lines quoting repository code are omitted from the copy)

def output_field_identity(sel):
    source = sel.source
    if source != 0:
        return source
    return sel.field


# --- minimal Selection carrier matching the model's object modeling ----------

class Selection:
    def __init__(self, source, field):
        self.source = source  # 0 == "no usable source identity"
        self.field = field    # always nonzero (usable)


# --- bridge: intern runtime objects to the model's integer identities --------

class Intern:
    """Distinct positive identity per distinct runtime object (by id)."""

    def __init__(self):
        self._ids = {}
        self._keep = []   # pin objects so ids stay unique
        self._next = 1

    def ident(self, obj):
        key = id(obj)
        if key not in self._ids:
            self._ids[key] = self._next
            self._keep.append(obj)
            self._next += 1
        return self._ids[key]


# --- selected-item stand-ins driven through the REAL property ----------------

class Item:
    """A selected item exposing the two attribute notions the property reads;
    the source-field attribute may be absent entirely."""

    def __init__(self, target, field, has_target=True):
        if has_target:
            self.target = target
        self.field = field


def _configure_django():
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
            USE_I18N=False,
        )
    django.setup()


def check_item(query, item, intern):
    """Run oracle and shadow on one selected item; return an error string on
    disagreement, else None."""
    # Bridge the item into the model's carrier.
    t = getattr(item, "target", None)
    source_id = intern.ident(t) if t else 0
    field_id = intern.ident(item.field)
    assert field_id != 0  # Requires(sel.field != 0) holds by construction

    shadow_id = output_field_identity(Selection(source_id, field_id))

    query.select = (item,)
    real_obj = query.output_field
    real_id = intern.ident(real_obj)

    if shadow_id != real_id:
        return ("DISAGREEMENT\n  item: target=%r (present=%r), field=%r\n"
                "  bridged: source=%d field=%d\n"
                "  shadow identity=%d\n  real object=%r (identity=%d)"
                % (t, hasattr(item, "target"), item.field,
                   source_id, field_id, shadow_id, real_obj, real_id))
    return None


def boundary_items():
    """Real Col objects plus absent/falsy-source stand-ins."""
    from django.db.models import (
        IntegerField, CharField, BigIntegerField, FloatField, DateField,
    )
    from django.db.models.expressions import Col
    from django.contrib.auth.models import User

    items = []
    pk_field = User._meta.pk

    # A plain Col: resolved field defaults to the source field (they coincide).
    items.append(Col("alias", pk_field))

    # Cols whose explicit resolved field DIFFERS from the source field — the
    # discriminating shape: the shadow must designate the source field.
    for factory in (IntegerField, CharField, BigIntegerField,
                    FloatField, DateField):
        items.append(Col("alias", pk_field, output_field=factory()))

    # Items with the source attribute present but falsy (each falsy shape),
    # and with the attribute absent: the fallback to the resolved field.
    resolved = IntegerField()
    for falsy in (None, 0, 0.0, "", [], {}, (), set(), False):
        items.append(Item(falsy, resolved))
    items.append(Item(None, resolved, has_target=False))
    items.append(Item(None, pk_field, has_target=False))

    # Source present, truthy, and identical to the resolved field.
    items.append(Item(resolved, resolved))
    return items


def main():
    _configure_django()
    from django.db.models import IntegerField
    from django.db.models.sql.query import Query
    from django.contrib.auth.models import User

    intern = Intern()
    query = Query(User)

    checked = 0
    boundary = boundary_items()
    for item in boundary:
        err = check_item(query, item, intern)
        if err:
            print(err)
            return 1
        checked += 1

    # Fuzz: random presence/truthiness of the source attribute over a pool of
    # distinct objects, resolved fields drawn from a pool of real field
    # objects (plus plain distinct objects, which the property only needs to
    # hand back).
    from django.db.models import CharField, FloatField
    rng = random.Random(SEED)
    truthy_pool = ([IntegerField(), CharField(), FloatField(),
                    User._meta.pk] + [object() for _ in range(24)]
                   + [("F", i) for i in range(1, 9)] + [1, 2, 7, -3, "fk"])
    falsy_pool = [None, 0, 0.0, "", [], {}, (), set(), False]
    field_pool = [IntegerField(), CharField(), FloatField(), User._meta.pk,
                  object(), object(), ("G", 1)]

    for _ in range(N_FUZZ):
        field_obj = rng.choice(field_pool)
        mode = rng.randrange(4)
        if mode == 0:
            item = Item(None, field_obj, has_target=False)   # absent
        elif mode == 1:
            item = Item(rng.choice(falsy_pool), field_obj)   # present, falsy
        elif mode == 2:
            item = Item(rng.choice(truthy_pool), field_obj)  # present, truthy
        else:
            item = Item(field_obj, field_obj)                # source == field
        err = check_item(query, item, intern)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched single-selection "
          "output_field on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
