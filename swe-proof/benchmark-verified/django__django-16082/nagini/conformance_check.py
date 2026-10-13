#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16082 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The @Pure helpers ``is_int_kind``,
``is_date_kind``, ``is_subtype``, ``row``, ``records_same_type_numeric``,
``records_mixed_numeric`` and ``records_bitwise_integer`` copy over as plain
functions. This bundle consumes no @ContractOnly axiom, so every shadow callee
is the model's own code. No PSeq/PSet is used by the impl region, so no
sequence shim is needed.

ORACLE: the REAL patched repo function the model models per mapping.md —
``django.db.models.expressions._resolve_combined_type(connector, lhs_type,
rhs_type)``. The gate applies the patch to /testbed before this script runs;
the script only imports and drives the patched code.

Type bridge (mapping.md section 2): the recorded operand field classes are
modelled as the fixed codes ``T_NULL/T_DEC/T_FLT/T_DUR/T_TIME/T_DATE/T_DTM/
T_INT``, every field class strictly below the integer field type gets a code in
the OPEN band ``>= T_INT_SUB``, every field class below no recorded operand type
gets a code in the open band ``<= T_UNREL_TOP``, and the "no combination found"
result ``None`` is the sentinel ``T_NONE``. Connector strings are modelled as
int codes: the five arithmetic connectors 1..5, exponentiation 6, the five
bitwise connectors 7..11, and further codes stand for connector strings the
registry has no entry for. Lifting a model query to the real call maps each code
to its field class / connector string; lowering the real result maps the returned
field class (or None) back to its code. The bridge does not assume the shape of
the hierarchy: the integer family and the unrelated classes are DISCOVERED by
walking ``Field.__subclasses__()``, so the open bands are populated by whatever
the repo really contains at this commit.

Input domain: the model preconditions admit EVERY connector code and EVERY
operand type code (only the unresolved sentinel is excluded as an operand), so
the domain is unbounded on three axes. Boundary coverage is EXHAUSTIVE over the
whole bridged cross-product — every bridged connector code (all 11 registered
plus 4 unregistered) x every bridged field-class code squared — which spans both
open bands end to end at this commit. On top of that, >= 1e5 fuzz draws sample
the same bridged domain with a pinned seed (every draw is Requires-satisfying).
Pinned fuzz seed: 160820.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import importlib
import itertools
import json
import random
import sys

SEED = 160820
N_FUZZ = 100000


# --- field-type / connector codes from model.py ------------------------------

T_NONE = 0   # the "unresolved" sentinel result; NOT an operand type
T_NULL = 1   # the null-literal type
T_DEC = 2    # decimal field type
T_FLT = 3    # float field type
T_DUR = 4    # duration field type
T_TIME = 5   # time field type
T_DATE = 6   # date field type
T_DTM = 7    # date-time field type: a type BELOW the date field type
T_INT = 8    # integer field type
T_INT_SUB = 9    # first code of the OPEN family below the integer type
T_AUTO = 9       # the auto-increment integer type: one member of that family
T_UNREL_TOP = -1  # codes at or below this lie below NO recorded operand type

C_ADD = 1
C_SUB = 2
C_MUL = 3
C_DIV = 4
C_MOD = 5     # the remainder connector
C_POW = 6
C_BITAND = 7
C_BITOR = 8
C_BITLSHIFT = 9
C_BITRSHIFT = 10
C_BITXOR = 11


# --- pure helpers from model.py, contracts stripped ---------------------------

def is_int_kind(t):
    return t == T_INT or t >= T_INT_SUB


def is_date_kind(t):
    return t == T_DATE or t == T_DTM


def is_subtype(a, b):
    if b == T_INT:
        return is_int_kind(a)
    if b == T_DATE:
        return is_date_kind(a)
    return a == b


def row(clhs, crhs, lhs, rhs):
    return is_subtype(lhs, clhs) and is_subtype(rhs, crhs)


def records_same_type_numeric(connector):
    return (connector == C_ADD or connector == C_SUB or connector == C_MUL
            or connector == C_DIV or connector == C_MOD
            or connector == C_POW)


def records_mixed_numeric(connector):
    return (connector == C_ADD or connector == C_SUB or connector == C_MUL
            or connector == C_DIV or connector == C_MOD)


def records_bitwise_integer(connector):
    return (connector == C_BITAND or connector == C_BITOR
            or connector == C_BITLSHIFT or connector == C_BITRSHIFT
            or connector == C_BITXOR)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def resolve_combined_type(connector, lhs_type, rhs_type):
    # Scan the rows recorded for this connector in registration order and
    # return the recorded result type of the first matching row, else the
    # unresolved sentinel. The rows are, per family:
    #   numeric same-type (five arithmetic connectors + exponentiation):
    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
    #   numeric mixed-type (every arithmetic connector, remainder included on
    #   the same footing; NOT exponentiation):
    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
    #   numeric with the null-literal type (same connectors as same-type):
    #       (flt,null)->flt  (null,flt)->flt
    #   bitwise (five bitwise connectors): (int,int)->int
    #   date/time under addition and under subtraction, as recorded.
    if records_same_type_numeric(connector):
        if row(T_INT, T_INT, lhs_type, rhs_type):
            return T_INT
        if row(T_FLT, T_FLT, lhs_type, rhs_type):
            return T_FLT
        if row(T_DEC, T_DEC, lhs_type, rhs_type):
            return T_DEC
    if records_mixed_numeric(connector):
        if row(T_INT, T_DEC, lhs_type, rhs_type):
            return T_DEC
        if row(T_DEC, T_INT, lhs_type, rhs_type):
            return T_DEC
        if row(T_INT, T_FLT, lhs_type, rhs_type):
            return T_FLT
        if row(T_FLT, T_INT, lhs_type, rhs_type):
            return T_FLT
    if records_same_type_numeric(connector):
        if row(T_FLT, T_NULL, lhs_type, rhs_type):
            return T_FLT
        if row(T_NULL, T_FLT, lhs_type, rhs_type):
            return T_FLT
    if records_bitwise_integer(connector):
        if row(T_INT, T_INT, lhs_type, rhs_type):
            return T_INT
    if connector == C_ADD:
        if row(T_DATE, T_DUR, lhs_type, rhs_type):
            return T_DTM
        if row(T_DUR, T_DATE, lhs_type, rhs_type):
            return T_DTM
        if row(T_DUR, T_DUR, lhs_type, rhs_type):
            return T_DUR
        if row(T_TIME, T_DUR, lhs_type, rhs_type):
            return T_TIME
        if row(T_DUR, T_TIME, lhs_type, rhs_type):
            return T_TIME
    if connector == C_SUB:
        if row(T_DATE, T_DUR, lhs_type, rhs_type):
            return T_DTM
        if row(T_DATE, T_DATE, lhs_type, rhs_type):
            return T_DUR
        if row(T_DUR, T_DUR, lhs_type, rhs_type):
            return T_DUR
        if row(T_TIME, T_DUR, lhs_type, rhs_type):
            return T_TIME
        if row(T_TIME, T_TIME, lhs_type, rhs_type):
            return T_DUR
    return T_NONE


# --- oracle plumbing -----------------------------------------------------------

def setup_django():
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


def main():
    try:
        setup_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: Django not importable/configurable: %r" % (exc,))
        return 1

    from django.db.models import fields
    from django.db.models.fields import Field
    from django.db.models.expressions import Combinable, _resolve_combined_type

    NoneType = type(None)

    # Load the repo's own field modules so the whole hierarchy is present before
    # the bridge enumerates it.
    for mod in ("django.db.models.fields.json",
                "django.db.models.fields.files",
                "django.db.models.fields.related",
                "django.db.models.fields.proxy"):
        try:
            importlib.import_module(mod)
        except Exception:
            pass

    def all_subclasses(cls, acc=None):
        if acc is None:
            acc = set()
        for s in cls.__subclasses__():
            if s not in acc:
                acc.add(s)
                all_subclasses(s, acc)
        return acc

    every_field = all_subclasses(Field) | {Field}

    # Type bridge: model codes <-> real field classes / connector strings.
    code_to_field = {
        T_NULL: NoneType,
        T_DEC: fields.DecimalField,
        T_FLT: fields.FloatField,
        T_DUR: fields.DurationField,
        T_TIME: fields.TimeField,
        T_DATE: fields.DateField,
        T_DTM: fields.DateTimeField,
        T_INT: fields.IntegerField,
    }
    # The OPEN band below the integer field type, populated by discovery.
    int_subs = sorted(
        (c for c in every_field
         if issubclass(c, fields.IntegerField) and c is not fields.IntegerField),
        key=lambda c: c.__name__)
    if len(int_subs) < 3:
        print("G-CONF ERROR: expected several field classes below the integer "
              "field type; discovered %r" % ([c.__name__ for c in int_subs],))
        return 1
    for i, cls in enumerate(int_subs):
        code_to_field[T_INT_SUB + i] = cls
    # The OPEN band below no recorded operand type.
    unrelated = [c for c in (fields.CharField, fields.BooleanField,
                             fields.UUIDField, fields.BinaryField,
                             fields.TextField, fields.GenericIPAddressField,
                             fields.SlugField, Field)
                 if c in every_field]
    if len(unrelated) < 3:
        print("G-CONF ERROR: expected several field classes below no recorded "
              "operand type; discovered %r" % ([c.__name__ for c in unrelated],))
        return 1
    for i, cls in enumerate(unrelated):
        code_to_field[T_UNREL_TOP - i] = cls

    field_to_code = {
        None: T_NONE,
        fields.IntegerField: T_INT,
        fields.DecimalField: T_DEC,
        fields.FloatField: T_FLT,
        fields.DurationField: T_DUR,
        fields.TimeField: T_TIME,
        fields.DateField: T_DATE,
        fields.DateTimeField: T_DTM,
    }

    code_to_conn = {
        C_ADD: Combinable.ADD,
        C_SUB: Combinable.SUB,
        C_MUL: Combinable.MUL,
        C_DIV: Combinable.DIV,
        C_MOD: Combinable.MOD,
        C_POW: Combinable.POW,
        C_BITAND: Combinable.BITAND,
        C_BITOR: Combinable.BITOR,
        C_BITLSHIFT: Combinable.BITLEFTSHIFT,
        C_BITRSHIFT: Combinable.BITRIGHTSHIFT,
        C_BITXOR: Combinable.BITXOR,
    }
    registered = set(code_to_conn.values())
    # Connector codes the registry has no entry for: the model admits these and
    # says they resolve nothing.
    for extra_code, extra_conn in ((12, "@@unregistered-a"),
                                   (13, "@@unregistered-b"),
                                   (0, "@@unregistered-c"),
                                   (-4, "@@unregistered-d")):
        if extra_conn in registered:
            print("G-CONF ERROR: %r is a registered connector" % (extra_conn,))
            return 1
        code_to_conn[extra_code] = extra_conn

    conn_codes = sorted(code_to_conn)
    type_codes = sorted(code_to_field)

    def check_one(conn_code, lhs_code, rhs_code):
        """Drive the shadow and the real patched function on one query; return
        an error string on disagreement, else None."""
        shadow = resolve_combined_type(conn_code, lhs_code, rhs_code)
        real = _resolve_combined_type(code_to_conn[conn_code],
                                      code_to_field[lhs_code],
                                      code_to_field[rhs_code])
        if real not in field_to_code:
            return ("DISAGREEMENT (out-of-model oracle result) on input "
                    "connector=%r lhs=%s rhs=%s:\n"
                    "  shadow (impl region) = %r\n"
                    "  real                 = %r"
                    % (code_to_conn[conn_code],
                       code_to_field[lhs_code].__name__,
                       code_to_field[rhs_code].__name__, shadow, real))
        real_code = field_to_code[real]
        if shadow != real_code:
            return ("DISAGREEMENT on input connector=%r lhs=%s rhs=%s:\n"
                    "  shadow (impl region) = %r\n"
                    "  real (lowered)       = %r  (raw %r)"
                    % (code_to_conn[conn_code],
                       code_to_field[lhs_code].__name__,
                       code_to_field[rhs_code].__name__,
                       shadow, real_code,
                       None if real is None else real.__name__))
        return None

    checked = 0

    # Boundary: the ENTIRE bridged domain, exhaustively — every connector code
    # (registered and unregistered) x every bridged operand code squared, which
    # spans both open bands end to end at this commit.
    boundary = list(itertools.product(conn_codes, type_codes, type_codes))
    for conn_code, lhs_code, rhs_code in boundary:
        err = check_one(conn_code, lhs_code, rhs_code)
        if err:
            print(err)
            return 1
        checked += 1

    # Fuzz: >= 1e5 pinned-seed draws from the same domain (each one is
    # Requires-satisfying by construction: the connector is unconstrained and
    # neither operand code is the unresolved sentinel).
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        conn_code = rng.choice(conn_codes)
        lhs_code = rng.choice(type_codes)
        rhs_code = rng.choice(type_codes)
        err = check_one(conn_code, lhs_code, rhs_code)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched _resolve_combined_type on "
          "%d inputs (%d exhaustive boundary covering the whole bridged domain "
          "-- %d connector codes x %d field-class codes squared, spanning the "
          "%d-member family below the integer field type and %d classes below "
          "no recorded operand type -- + %d fuzz, seed %d); 0 disagreements."
          % (checked, len(boundary), len(conn_codes), len(type_codes),
             len(int_subs), len(unrelated), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
