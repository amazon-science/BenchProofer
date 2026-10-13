#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13346 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Requires/Ensures/Invariant lines removed; the loop body is
byte-for-byte the model's). The @Pure helpers (sep / wrapped_slot / bare_slot /
slots_sql) copy over as plain functions on a tuple-backed PSeq shim; the impl
itself uses only int lists, so the shim is exercised only by the internal
consistency probe on boundary counts.

ORACLE: the REAL patched repo function the model models per mapping.md --
django.db.models.fields.json.KeyTransformIn.process_rhs, called on the default
SQLite connection (a non-native-JSON backend, so the value-slot rewriting
branch is taken). The gate applies patch.diff to /testbed before this script
runs; PYTHONPATH=/testbed makes the patched code importable. One membership
lookup is resolved through the ORM (data__key__in=...) to obtain the exact
lookup class + resolved key-transform lhs the query machinery uses; each input
then constructs a fresh real lookup over that lhs and calls its process_rhs.

Type bridge (mapping.md section 2):
  - the produced comparison string <-> List[int] of code points (ord per char);
  - the outer parentheses of the placeholder are produced identically by the
    unchanged base class and are outside the modeled content, so the real
    string is stripped of its leading '(' and trailing ')' (asserted present)
    before comparison -- exactly the documented refinement boundary;
  - the model input num_values <-> len(rhs_params), the count of bind
    parameters the real call returns (>= 1 on every generated input: values
    are distinct and non-None, so none is deduplicated or dropped);
  - the bind parameters themselves are unchanged by the modeled branch and are
    outside the modeled output (not compared).

Input domain: Requires(num_values >= 1). Real inputs are non-empty lists of
distinct hashable scalar values (ints, floats, ascii strings, bools) so the
value count survives the base class's de-duplication; the shadow is fed
len(rhs_params) from the real call. Boundary covers counts 1..5, 8, 10, 16,
32, 64, 100, 200 across several value-type mixes; fuzz draws 100000 random
(count, value-mix) pairs.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz draws.
Pinned fuzz seed: 13346.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json as _json
import random
import string
import sys

SEED = 13346
N_FUZZ = 100_000


# --- PSeq shim (tuple-backed) ---------------------------------------------------

class PSeq(tuple):
    def __new__(cls, *xs):
        return super(PSeq, cls).__new__(cls, xs)

    def take(self, n):
        t = tuple(self)[:n]
        return PSeq(*t)

    def drop(self, n):
        t = tuple(self)[n:]
        return PSeq(*t)

    def __add__(self, other):
        return PSeq(*(tuple(self) + tuple(other)))


# --- pure helpers from model.py, decorators/contracts stripped -------------------

def sep():
    # ', '  -- the separator between comparison slots
    return PSeq(44, 32)


def wrapped_slot():
    # The per-value comparison form: an opaque backend constant (constant code
    # points) that every slot must take.
    return PSeq(74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                40, 37, 115, 44, 32, 39, 36, 39, 41)


def bare_slot():
    # The bare bind placeholder -- a slot in the un-formed shape.
    return PSeq(37, 115)


def slots_sql(n):
    """The comparison string for `n` value slots: wrapped_slot repeated n
    times, joined by sep."""
    if n == 0:
        return PSeq(0).take(0)
    if n == 1:
        return wrapped_slot()
    return wrapped_slot() + sep() + slots_sql(n - 1)


# --- the impl region of model.py, verbatim (contracts stripped) ------------------

def process_membership_rhs(num_values):
    result = []  # type: List[int]
    i = num_values
    while i > 0:
        if i == num_values:
            # Last slot: no trailing separator.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41]
        else:
            # Earlier slot: wrapped slot, then separator, then the rest.
            result = [74, 83, 79, 78, 95, 69, 88, 84, 82, 65, 67, 84,
                      40, 37, 115, 44, 32, 39, 36, 39, 41, 44, 32] + result
        i = i - 1
    return result


# --- input generation -------------------------------------------------------------

_ASCII = string.ascii_letters + string.digits + "_-. "


def _distinct_values(rng, n):
    """n distinct, non-None, hashable scalar values (mixed types), so the base
    class's de-duplication keeps all n and the bind-parameter count equals n."""
    vals = []
    seen = set()
    while len(vals) < n:
        kind = rng.random()
        if kind < 0.4:
            v = rng.randint(-10**6, 10**6)
        elif kind < 0.6:
            v = "".join(rng.choice(_ASCII) for _ in range(rng.randint(0, 12)))
        elif kind < 0.8:
            v = round(rng.uniform(-1e6, 1e6), 6)
        else:
            v = rng.choice([True, False])
        # de-dupe on the prepared (JSON) form so bools/ints/floats that
        # serialize identically never collapse a slot downstream.
        key = _json.dumps(v)
        if key in seen:
            continue
        seen.add(key)
        vals.append(v)
    return vals


def boundary_counts():
    return [1, 2, 3, 4, 5, 8, 10, 16, 32, 64, 100, 200]


# --- oracle + differential ---------------------------------------------------------

def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DEBUG=False,
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            USE_TZ=True,
        )
        django.setup()

    from django.db import connections, models

    connection = connections["default"]
    # Sanity: the modeled branch is the non-native-JSON sqlite path.
    assert connection.vendor == "sqlite", connection.vendor
    assert not connection.features.has_native_json_field

    class ConfModel(models.Model):
        data = models.JSONField()

        class Meta:
            app_label = "conf_check_13346"

    # Resolve ONE membership lookup through the ORM to obtain the exact lookup
    # class and resolved key-transform lhs the query machinery uses.
    qs = ConfModel.objects.filter(data__key__in=[1])
    lookup0 = qs.query.where.children[0]
    lookup_cls = type(lookup0)
    lhs = lookup0.lhs
    compiler = qs.query.get_compiler("default")
    # The patched repo registers a dedicated membership lookup on the key
    # transform; if the resolved class were the plain base lookup the oracle
    # would be the unpatched behaviour, so pin the class name.
    assert lookup_cls.__name__ == "KeyTransformIn", lookup_cls.__name__

    def real_call(values):
        """Real patched process_rhs on a fresh lookup; returns
        (inner code points with outer parens stripped, len(rhs_params))."""
        lk = lookup_cls(lhs, values)
        rhs, rhs_params = lk.process_rhs(compiler, connection)
        assert rhs[0] == "(" and rhs[-1] == ")", rhs
        return [ord(c) for c in rhs[1:-1]], len(rhs_params)

    def check_case(values):
        real_inner, n = real_call(values)
        if n < 1:
            return ("PRECONDITION VIOLATION\n  values=%r\n  bind-param count=%d"
                    % (values, n))
        shadow_out = process_membership_rhs(n)
        if shadow_out != real_inner:
            return ("DISAGREEMENT\n  values=%r\n  num_values=%d\n"
                    "  shadow=%r\n  real=%r"
                    % (values, n, shadow_out, real_inner))
        return None

    checked = 0
    rng = random.Random(SEED)

    # Boundary: each count across several value-type mixes, plus an internal
    # consistency probe (impl loop == pure fold) on the same counts.
    n_boundary = 0
    for n in boundary_counts():
        assert process_membership_rhs(n) == list(slots_sql(n)), n
        for vals in (list(range(n)),
                     ["v%d" % k for k in range(n)],
                     _distinct_values(rng, n)):
            err = check_case(vals)
            if err:
                print(err)
                return 1
            checked += 1
            n_boundary += 1

    # Fuzz: random (count, value-mix) pairs; counts skew small with a long tail.
    for _ in range(N_FUZZ):
        r = rng.random()
        if r < 0.30:
            n = 1
        elif r < 0.85:
            n = rng.randint(2, 16)
        elif r < 0.99:
            n = rng.randint(17, 64)
        else:
            n = rng.randint(65, 256)
        err = check_case(_distinct_values(rng, n))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real membership-lookup slot expansion "
          "on %d inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(_json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                       "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
