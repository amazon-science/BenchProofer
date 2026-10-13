#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15561 (nagini).

SHADOW: the impl regions of model.py, copied verbatim below with the contract
calls stripped (the Invariant lines inside the loop; the pure attr_* helpers
copied over as plain functions). PSet becomes a plain frozenset shim; the
PSeq parameters are exercised with plain Python lists (indexing / len /
membership behave identically). There are no @ContractOnly callees.

ORACLE: the REAL patched repo functions the model models per mapping.md --
  * site 1: `django.db.models.fields.Field.non_db_attrs` (the class attribute
    listing which field attributes have no bearing on the physical column);
  * site 2: `BaseDatabaseSchemaEditor._field_should_be_altered(old, new)`
    (the rebuild decision), reached through a concrete sqlite schema editor
    built with collect_sql=True so no database work happens (the decision
    only reads deconstruct() output and quote_name()).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched code importable.

TYPE BRIDGE (mapping.md section 2):
  * attribute NAME (str) <-> int attribute code: the 12 names carried by the
    model constants get their fixed codes 0..11; any other kwarg key seen at
    runtime gets a fresh code >= 12 (a fixed injection -- distinct names,
    distinct codes).
  * kwargs dicts <-> aligned sequences: attrs[i] lists the codes of the keys
    present in either deconstructed kwargs bag; old_vals[i]/new_vals[i] carry
    a value token per side, with a distinct ABSENCE token (-1) when the key
    is missing on that side. Value tokens respect Python `==` (equal values,
    equal tokens; the token table is scanned with `==`, matching dict
    equality semantics exactly, including bool==int coercions).
  * the non-kwarg structural part (quoted column names plus the path and
    leading args of the two deconstructions) <-> the read-only bool
    `other_differs`, computed from the same real fields.
The bridge projects each REAL field pair onto the model carrier, so every
generated input is Requires-satisfying by construction (the three sequences
are aligned).

INPUT DOMAIN: pairs of real Field instances (CharField / TextField /
IntegerField / SlugField) over a per-key value pool covering the
schema-irrelevant attributes constructible on plain fields (choices, blank,
db_column, editable, error_messages, help_text, verbose_name) plus several
schema-relevant ones (max_length, null, unique, db_index, default), with
same-name and different-name / different-class pairs. Boundary cases include
the identical pair, the enumeration-only difference in both directions, single
and multiple irrelevant-attribute differences, relevant-attribute differences,
column / class differences, and mixed cases.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz pairs.
Pinned fuzz seed: 15561.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 15561
N_FUZZ = 100_000


# --- shims for the model carrier types ----------------------------------------

def PSet(*args):
    return frozenset(args)


# --- pure helpers from model.py, decorators stripped ---------------------------

def attr_choices():
    # Attribute code for the enumeration of permitted values.
    return 0


def attr_blank():
    return 1


def attr_db_column():
    return 2


def attr_editable():
    return 3


def attr_error_messages():
    return 4


def attr_help_text():
    return 5


def attr_limit_choices_to():
    return 6


def attr_on_delete():
    return 7


def attr_related_name():
    return 8


def attr_related_query_name():
    return 9


def attr_validators():
    return 10


def attr_verbose_name():
    return 11


# --- impl region of schema_irrelevant_attrs, verbatim --------------------------

def schema_irrelevant_attrs():
    s = PSet(attr_choices(), attr_blank(), attr_db_column(), attr_editable(),
             attr_error_messages(), attr_help_text(), attr_limit_choices_to(),
             attr_on_delete(), attr_related_name(), attr_related_query_name(),
             attr_validators(), attr_verbose_name())
    return s


# --- impl region of field_alteration_needed, verbatim (Invariants stripped) ----

def field_alteration_needed(attrs, old_vals, new_vals, non_db, other_differs):
    if other_differs:
        return True
    i = 0
    while i < len(attrs):
        if not (attrs[i] in non_db):
            if old_vals[i] != new_vals[i]:
                return True
        i = i + 1
    return False


# --- bridge: attribute-name -> code injection, value -> token ------------------

# The 12 names the model's constants carry, at their model codes.
ATTR_CODE = {
    "choices": 0,
    "blank": 1,
    "db_column": 2,
    "editable": 3,
    "error_messages": 4,
    "help_text": 5,
    "limit_choices_to": 6,
    "on_delete": 7,
    "related_name": 8,
    "related_query_name": 9,
    "validators": 10,
    "verbose_name": 11,
}
_NEXT_CODE = [12]


def attr_code(name):
    """Fixed injection attribute name -> int code (fresh codes for names
    outside the 12 modelled constants)."""
    if name not in ATTR_CODE:
        ATTR_CODE[name] = _NEXT_CODE[0]
        _NEXT_CODE[0] += 1
    return ATTR_CODE[name]


ABSENT = -1
_TOKEN_VALS = {}  # key -> list of previously seen values (compared with ==)


def value_token(key, value):
    """A stable int token per (key, value): tokens are equal iff the values
    compare equal under Python `==` (the same relation dict equality uses),
    and every token is >= 1 so it never collides with the ABSENCE token."""
    vals = _TOKEN_VALS.setdefault(key, [])
    for i, v in enumerate(vals):
        eq = False
        try:
            eq = (v == value)
        except Exception:
            eq = False
        if eq:
            return i + 1
    vals.append(value)
    return len(vals)


def project(editor, old_field, new_field):
    """Project a REAL field pair onto the model carrier (mapping.md section 2):
    aligned code / value-token sequences over the union of deconstructed kwarg
    keys, plus the non-kwarg structural bool."""
    _, old_path, old_args, old_kwargs = old_field.deconstruct()
    _, new_path, new_args, new_kwargs = new_field.deconstruct()
    other_differs = (
        editor.quote_name(old_field.column) != editor.quote_name(new_field.column)
        or (old_path, old_args) != (new_path, new_args)
    )
    attrs, old_vals, new_vals = [], [], []
    for k in sorted(set(old_kwargs) | set(new_kwargs)):
        attrs.append(attr_code(k))
        old_vals.append(value_token(k, old_kwargs[k]) if k in old_kwargs
                        else ABSENT)
        new_vals.append(value_token(k, new_kwargs[k]) if k in new_kwargs
                        else ABSENT)
    return attrs, old_vals, new_vals, other_differs


# --- input generation -----------------------------------------------------------

# Per-key value pools. Bool-valued and int-valued keys never share a pool, and
# tokens use `==` anyway, so bool/int coercion cannot desynchronise the bridge.
KWARG_POOL = {
    "blank": [True, False],
    "editable": [True, False],
    "null": [True, False],
    "unique": [True, False],
    "db_index": [True, False],
    "max_length": [10, 100, 255],
    "help_text": ["", "h1", "h2"],
    "verbose_name": ["v1", "v2"],
    "db_column": ["col_a", "col_b"],
    "choices": [(("a", "a"),), (("a", "a"), ("b", "b")), (("x", "X"),)],
    "error_messages": [{"null": "m1"}, {"null": "m2"}],
    "default": ["d1", "d2"],
}
KWARG_KEYS = sorted(KWARG_POOL)


def make_field(cls, name, kwargs):
    f = cls(**kwargs)
    f.set_attributes_from_name(name)
    return f


def check_pair(editor, old_field, new_field, label):
    attrs, old_vals, new_vals, other_differs = project(editor, old_field,
                                                       new_field)
    non_db = schema_irrelevant_attrs()
    shadow_out = field_alteration_needed(attrs, old_vals, new_vals, non_db,
                                         other_differs)
    real_out = editor._field_should_be_altered(old_field, new_field)
    if bool(shadow_out) != bool(real_out):
        print("DISAGREEMENT on %s\n  old=%r %r\n  new=%r %r\n"
              "  projected attrs=%r old_vals=%r new_vals=%r other_differs=%r\n"
              "  shadow=%r real=%r"
              % (label,
                 type(old_field).__name__, old_field.deconstruct(),
                 type(new_field).__name__, new_field.deconstruct(),
                 attrs, old_vals, new_vals, other_differs,
                 shadow_out, real_out))
        return False
    return True


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=[],
            USE_TZ=False,
        )
        django.setup()
    from django.db import connection, models
    from django.db.models.fields import Field

    # collect_sql=True: the editor only inspects deconstruct() output and
    # quotes names; nothing touches the database.
    editor = connection.schema_editor(collect_sql=True)

    # --- site 1: shadow set == real class attribute, through the injection ---
    real_codes = frozenset(attr_code(a) for a in Field.non_db_attrs)
    shadow_codes = schema_irrelevant_attrs()
    if shadow_codes != real_codes:
        print("DISAGREEMENT on the schema-irrelevant attribute set:\n"
              "  shadow codes=%r\n  real attribute names=%r -> codes=%r"
              % (sorted(shadow_codes), tuple(Field.non_db_attrs),
                 sorted(real_codes)))
        return 1

    field_classes = [models.CharField, models.TextField,
                     models.IntegerField, models.SlugField]
    C = models.CharField
    checked = 0

    # --- boundary field pairs -------------------------------------------------
    base = {"max_length": 255}
    with_choices = {"max_length": 255,
                    "choices": (("Jane", "Jane"), ("Joe", "Joe"))}
    boundary = [
        (make_field(C, "name", base), make_field(C, "name", dict(base)),
         "identical"),
        (make_field(C, "name", base), make_field(C, "name", with_choices),
         "enumeration-only forward"),
        (make_field(C, "name", with_choices), make_field(C, "name", base),
         "enumeration-only reverse"),
        (make_field(C, "name", {"max_length": 255, "choices": (("a", "a"),)}),
         make_field(C, "name", {"max_length": 255, "choices": (("a", "a"),)}),
         "enumeration-equal"),
        (make_field(C, "name", {"max_length": 255, "help_text": "h1"}),
         make_field(C, "name", {"max_length": 255, "help_text": "h2"}),
         "help_text-diff"),
        (make_field(C, "name", {"max_length": 255, "verbose_name": "v1"}),
         make_field(C, "name", {"max_length": 255, "verbose_name": "v2"}),
         "verbose_name-diff"),
        (make_field(C, "name", {"max_length": 255, "blank": True,
                                "editable": False, "help_text": "h1"}),
         make_field(C, "name", {"max_length": 255, "blank": False,
                                "editable": True, "help_text": "h2"}),
         "many-irrelevant-diff"),
        (make_field(C, "name", {"max_length": 255}),
         make_field(C, "name", {"max_length": 100}),
         "max_length-diff"),
        (make_field(C, "name", base), make_field(C, "title", dict(base)),
         "column-diff"),
        (make_field(C, "name", {"max_length": 255, "db_column": "col_a"}),
         make_field(C, "name", {"max_length": 255, "db_column": "col_b"}),
         "db_column-diff (column changes though the key is irrelevant)"),
        (make_field(C, "name", {"max_length": 255, "db_column": "col_a"}),
         make_field(C, "name", {"max_length": 255, "db_column": "col_a"}),
         "db_column-equal"),
        (make_field(C, "name", base),
         make_field(models.TextField, "name", {}),
         "class-diff"),
        (make_field(C, "name", {"max_length": 255, "help_text": "h1"}),
         make_field(C, "name", {"max_length": 100, "help_text": "h2"}),
         "relevant+irrelevant"),
        (make_field(C, "name", {"max_length": 255, "unique": True}),
         make_field(C, "name", {"max_length": 255}),
         "unique-dropped"),
        (make_field(C, "name", {"max_length": 255, "default": "d1"}),
         make_field(C, "name", {"max_length": 255, "default": "d2"}),
         "default-diff"),
    ]
    for old_f, new_f, label in boundary:
        if not check_pair(editor, old_f, new_f, label):
            return 1
        checked += 1

    # --- randomized fuzz --------------------------------------------------------
    rng = random.Random(SEED)

    def rand_kwargs():
        kw = {}
        for k in KWARG_KEYS:
            if rng.random() < 0.4:
                kw[k] = rng.choice(KWARG_POOL[k])
        return kw

    for it in range(N_FUZZ):
        old_cls = rng.choice(field_classes)
        new_cls = old_cls if rng.random() < 0.85 else rng.choice(field_classes)
        old_name = "name"
        new_name = "name" if rng.random() < 0.9 else "title"
        old_kw = rand_kwargs()
        if rng.random() < 0.7:
            # perturb a copy of the old kwargs: change / drop / add a few keys
            new_kw = dict(old_kw)
            for _ in range(rng.randint(1, 3)):
                k = rng.choice(KWARG_KEYS)
                r = rng.random()
                if r < 0.5:
                    new_kw[k] = rng.choice(KWARG_POOL[k])
                elif k in new_kw:
                    del new_kw[k]
        else:
            new_kw = rand_kwargs()
        old_f = make_field(old_cls, old_name, old_kw)
        new_f = make_field(new_cls, new_name, new_kw)
        if not check_pair(editor, old_f, new_f, "fuzz #%d" % it):
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real rebuild decision on %d field pairs "
          "(%d boundary + %d fuzz, seed %d); shadow schema-irrelevant set == "
          "real class attribute (12 codes)."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
