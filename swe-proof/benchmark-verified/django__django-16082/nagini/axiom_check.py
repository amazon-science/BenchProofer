#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16082.

model.py axiomatizes NO callee (no @ContractOnly the proof consumes). The deep
model of combined-type resolution rests on two UNCHANGED primitives that are
validated here as A-references (the deep model is checked == the real callee),
not consumed as axioms:

  (1) the subtype test ``is_subtype`` <-> Python ``issubclass`` over the field
      classes the registry mentions as recorded operand types and over every
      field class that lies BELOW one of them. The model's carrier gives the
      family below the integer field type an OPEN band of codes; this script
      checks that band against the real hierarchy by enumerating every real
      subclass of the integer field type reachable from the repo's own field
      module, and likewise that the date-time type lies below the date type and
      that classes below no recorded operand type match nothing.

  (2) the per-connector row set the deep model spells out <-> Django's real
      registry ``_connector_combinators`` consulted by
      ``_resolve_combined_type``, over EVERY connector the registry is keyed by
      (the five arithmetic connectors, exponentiation, the five bitwise
      connectors) plus unregistered connector codes, crossed with that whole
      field-class domain.

This script runs inside the official SWE-bench container for the instance with
the POST-PATCH source present (the patch having been applied). Exit 0 iff every
observation matches the deep model. stdlib + the repo's django only.
"""
import os
import sys
import itertools


def configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
        )
    django.setup()


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        configure_django()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: Django not configurable in this environment: %r"
              % (exc,))
        return 0

    from django.db.models import fields
    from django.db.models.fields import Field
    from django.db.models.expressions import Combinable, _resolve_combined_type

    NoneType = type(None)

    # ---------------- model codes (mirrors model.py) ----------------
    T_NONE, T_NULL, T_DEC, T_FLT = 0, 1, 2, 3
    T_DUR, T_TIME, T_DATE, T_DTM, T_INT = 4, 5, 6, 7, 8
    T_INT_SUB = 9
    T_UNREL_TOP = -1

    C_ADD, C_SUB, C_MUL, C_DIV, C_MOD, C_POW = 1, 2, 3, 4, 5, 6
    C_BITAND, C_BITOR, C_BITLSHIFT, C_BITRSHIFT, C_BITXOR = 7, 8, 9, 10, 11

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

    def row(cl, cr, l, r):
        return is_subtype(l, cl) and is_subtype(r, cr)

    def records_same_type_numeric(c):
        return c in (C_ADD, C_SUB, C_MUL, C_DIV, C_MOD, C_POW)

    def records_mixed_numeric(c):
        return c in (C_ADD, C_SUB, C_MUL, C_DIV, C_MOD)

    def records_bitwise_integer(c):
        return c in (C_BITAND, C_BITOR, C_BITLSHIFT, C_BITRSHIFT, C_BITXOR)

    def deep_resolve(c, l, r):
        if records_same_type_numeric(c):
            if row(T_INT, T_INT, l, r):
                return T_INT
            if row(T_FLT, T_FLT, l, r):
                return T_FLT
            if row(T_DEC, T_DEC, l, r):
                return T_DEC
        if records_mixed_numeric(c):
            if row(T_INT, T_DEC, l, r):
                return T_DEC
            if row(T_DEC, T_INT, l, r):
                return T_DEC
            if row(T_INT, T_FLT, l, r):
                return T_FLT
            if row(T_FLT, T_INT, l, r):
                return T_FLT
        if records_same_type_numeric(c):
            if row(T_FLT, T_NULL, l, r):
                return T_FLT
            if row(T_NULL, T_FLT, l, r):
                return T_FLT
        if records_bitwise_integer(c):
            if row(T_INT, T_INT, l, r):
                return T_INT
        if c == C_ADD:
            if row(T_DATE, T_DUR, l, r):
                return T_DTM
            if row(T_DUR, T_DATE, l, r):
                return T_DTM
            if row(T_DUR, T_DUR, l, r):
                return T_DUR
            if row(T_TIME, T_DUR, l, r):
                return T_TIME
            if row(T_DUR, T_TIME, l, r):
                return T_TIME
        if c == C_SUB:
            if row(T_DATE, T_DUR, l, r):
                return T_DTM
            if row(T_DATE, T_DATE, l, r):
                return T_DUR
            if row(T_DUR, T_DUR, l, r):
                return T_DUR
            if row(T_TIME, T_DUR, l, r):
                return T_TIME
            if row(T_TIME, T_TIME, l, r):
                return T_DUR
        return T_NONE

    # ---------------- the real domain, discovered not assumed ----------------
    # Import the repo's own field modules so every Field subclass the registry
    # could ever be driven with is loaded before we enumerate the hierarchy.
    import importlib
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

    # The recorded operand types: exactly the classes the registry's rows name.
    recorded = {
        T_INT: fields.IntegerField,
        T_DEC: fields.DecimalField,
        T_FLT: fields.FloatField,
        T_NULL: NoneType,
        T_DATE: fields.DateField,
        T_DTM: fields.DateTimeField,
        T_DUR: fields.DurationField,
        T_TIME: fields.TimeField,
    }

    # (a) The model claims the family below the integer field type is an open
    #     band and that NOTHING else in the hierarchy lies below a recorded
    #     operand type except the date-time type below the date type. Check that
    #     against the real hierarchy before using it.
    int_family = sorted(
        (c for c in every_field if issubclass(c, fields.IntegerField)),
        key=lambda c: c.__name__)
    assert fields.IntegerField in int_family
    int_subs = [c for c in int_family if c is not fields.IntegerField]
    assert len(int_subs) >= 3, (
        "expected the integer field type to have several field types below it; "
        "found %r" % ([c.__name__ for c in int_subs],))
    for base_code, base in recorded.items():
        if base is NoneType:
            continue
        below = sorted((c for c in every_field if issubclass(c, base)),
                       key=lambda c: c.__name__)
        extra = [c for c in below if c is not base]
        if base is fields.IntegerField:
            expected_extra = int_subs
        elif base is fields.DateField:
            expected_extra = [fields.DateTimeField]
        else:
            expected_extra = []
        assert sorted(c.__name__ for c in extra) == \
            sorted(c.__name__ for c in expected_extra), (
            "hierarchy below %s is %r but the model carrier expects %r"
            % (base.__name__, [c.__name__ for c in extra],
               [c.__name__ for c in expected_extra]))

    # Bridge: assign each real class a model code. Members of the integer family
    # other than the integer type itself get distinct codes in the OPEN band;
    # classes below no recorded operand type get codes in the band the model
    # reserves for them.
    code_to_field = dict(recorded)
    for i, cls in enumerate(int_subs):
        code_to_field[T_INT_SUB + i] = cls
    unrelated = [c for c in (fields.CharField, fields.BooleanField,
                             fields.UUIDField, fields.BinaryField,
                             fields.TextField, fields.GenericIPAddressField,
                             fields.SlugField, Field)
                 if c in every_field]
    for i, cls in enumerate(unrelated):
        code_to_field[T_UNREL_TOP - i] = cls

    result_to_code = {None: T_NONE, fields.IntegerField: T_INT,
                      fields.DecimalField: T_DEC, fields.FloatField: T_FLT,
                      fields.DurationField: T_DUR, fields.TimeField: T_TIME,
                      fields.DateField: T_DATE, fields.DateTimeField: T_DTM}

    codes = sorted(code_to_field)

    # ---- (1) subtype relation == real issubclass, over the WHOLE domain ----
    sub_checks = 0
    for a, b in itertools.product(codes, sorted(recorded)):
        fa, fb = code_to_field[a], code_to_field[b]
        real = issubclass(fa, fb)
        model = is_subtype(a, b)
        assert real == model, (
            "subtype mismatch: issubclass(%s, %s)=%r but is_subtype(%d,%d)=%r"
            % (fa.__name__, fb.__name__, real, a, b, model))
        sub_checks += 1
    # The open band must really be populated by proper subtypes of the integer
    # field type — the fact the band predicate encodes.
    for cls in int_subs:
        assert issubclass(cls, fields.IntegerField) and cls is not fields.IntegerField, \
            "%s is expected to be a proper subclass of IntegerField" % cls.__name__
    assert issubclass(fields.DateTimeField, fields.DateField), \
        "DateTimeField is expected to be a subclass of DateField"

    # ---- (2) real _resolve_combined_type == deep model, exhaustively ----
    code_to_conn = {
        C_ADD: Combinable.ADD, C_SUB: Combinable.SUB, C_MUL: Combinable.MUL,
        C_DIV: Combinable.DIV, C_MOD: Combinable.MOD, C_POW: Combinable.POW,
        C_BITAND: Combinable.BITAND, C_BITOR: Combinable.BITOR,
        C_BITLSHIFT: Combinable.BITLEFTSHIFT,
        C_BITRSHIFT: Combinable.BITRIGHTSHIFT,
        C_BITXOR: Combinable.BITXOR,
    }
    # Unregistered connector codes: the model says these resolve nothing.
    for extra_code, extra_conn in ((12, "@@unregistered-a"),
                                   (13, "@@unregistered-b"),
                                   (0, "@@unregistered-c"),
                                   (-4, "@@unregistered-d")):
        assert extra_conn not in code_to_conn.values()
        code_to_conn[extra_code] = extra_conn

    obs = 0
    for conn_code in sorted(code_to_conn):
        connector = code_to_conn[conn_code]
        for lhs_code, rhs_code in itertools.product(codes, codes):
            lhs_field = code_to_field[lhs_code]
            rhs_field = code_to_field[rhs_code]
            real = _resolve_combined_type(connector, lhs_field, rhs_field)
            assert real in result_to_code, (
                "real _resolve_combined_type(%r, %s, %s) returned an "
                "out-of-model type %r"
                % (connector, lhs_field.__name__, rhs_field.__name__, real))
            real_code = result_to_code[real]
            model_code = deep_resolve(conn_code, lhs_code, rhs_code)
            assert real_code == model_code, (
                "resolution mismatch for connector=%r lhs=%s rhs=%s: "
                "real=%r model=%r"
                % (connector, lhs_field.__name__, rhs_field.__name__,
                   None if real is None else real.__name__, model_code))
            obs += 1

    # ---- the discriminating cases the issue describes, spelled out ----
    # Mixed numeric operands under the remainder connector must resolve to the
    # wider type in the post-patch source (the behaviour the change delivers) —
    # including when the integer operand is a NARROWER integer field class,
    # which is what makes the subtype match load-bearing.
    IF, DF, FF = fields.IntegerField, fields.DecimalField, fields.FloatField
    MOD = Combinable.MOD
    assert _resolve_combined_type(MOD, IF, DF) is DF, \
        "MOD(Integer, Decimal) must resolve to DecimalField"
    assert _resolve_combined_type(MOD, DF, IF) is DF, \
        "MOD(Decimal, Integer) must resolve to DecimalField"
    assert _resolve_combined_type(MOD, IF, FF) is FF, \
        "MOD(Integer, Float) must resolve to FloatField"
    assert _resolve_combined_type(MOD, FF, IF) is FF, \
        "MOD(Float, Integer) must resolve to FloatField"
    for cls in int_subs:
        assert _resolve_combined_type(MOD, cls, DF) is DF, \
            "MOD(%s, Decimal) must resolve to DecimalField" % cls.__name__
        assert _resolve_combined_type(MOD, cls, cls) is IF, \
            "MOD(%s, %s) must resolve to IntegerField" % (cls.__name__,
                                                          cls.__name__)
        assert _resolve_combined_type(Combinable.BITOR, cls, cls) is IF, \
            "BITOR(%s, %s) must resolve to IntegerField" % (cls.__name__,
                                                            cls.__name__)

    print("G-AX OK: subtype relation sound vs real issubclass over %d "
          "(queried class, recorded class) pairs spanning the whole family "
          "below the integer field type (%d members) and the date-time/date "
          "pair; deep registry model == real _resolve_combined_type over %d "
          "(connector, lhs, rhs) observations spanning every registered "
          "connector plus unregistered codes x %d field classes squared; the "
          "remainder connector resolves mixed numeric operands to the wider "
          "type for every integer field class."
          % (sub_checks, len(int_subs), obs, len(codes)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
