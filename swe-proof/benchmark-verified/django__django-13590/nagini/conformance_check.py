#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-13590 (nagini).

SHADOW: the impl region of model.py's `resolve_sequence`, copied VERBATIM
below with only the contract calls (Requires/Ensures/Invariant/Assert)
stripped. The @Pure helper `resolved_seq` copies over on a small immutable
PSeq shim and serves as an internal cross-check of the shadow's loop. The two
@ContractOnly callees are bridged to the REAL repo counterparts mapping.md
section 1 binds them to:

  * `resolve_one(sub_value)`  -> the real recursive per-element resolution,
    `Query.resolve_lookup_value` applied to ONE sub-value on the patched
    Query;
  * `build_container(elems, field_named, spread)` -> the real, unchanged
    container constructor of the input's kind, invoked under the convention
    the `spread` flag denotes (one element per positional argument when
    spread, a single iterable argument otherwise).

ORACLE: the REAL patched
`django.db.models.sql.query.Query.resolve_lookup_value` applied to the whole
sequence value. The gate applies patch.diff to /testbed before this script
runs and sets PYTHONPATH so the import resolves to the patched module. A
minimal in-memory settings module is configured (no database access happens
for plain / expression sub-values).

TYPE BRIDGE (mapping.md section 2):
  * `value: List[int]` of opaque sub-value identities  <->  the ordered
    sub-values of a real list / tuple / field-named (namedtuple) sequence;
    the k-th identity is the k-th sub-value, order-preserving;
  * `field_named: bool`  <->  `hasattr(type(value), '_make')`;
  * the model's `List[int]` result  <->  the rebuilt real container; the
    shadow's `build_container` IS the real constructor, so the shadow output
    is already concrete and is compared against the oracle output on exact
    container type, length, and per-index sub-value equality (exact-type
    container comparison, so a field-named container never compares equal to
    a plain tuple of the same values by accident);
  * the `well_formed_container` capability token abstracts the construction
    succeeding at all; executably it is covered by the shadow actually
    routing its result through the real constructor call (a convention
    mismatch would raise and fail the check).

INPUT DOMAIN: the precondition demands only a readable sequence, so every
list / tuple / namedtuple of sub-values is Requires-satisfying. Sub-values
mix plain scalars (ints, strings, None, bools, floats), objects carrying a
deterministic `resolve_expression` (exercising the per-element expression
branch of the real recursion), and nested lists / tuples / namedtuples (the
per-element call recurses through the same branch). Field-named kinds of
field counts 1..6 are exercised, including the discriminating 2-field shape.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz sequences.
Pinned fuzz seed: 13590. Exit 0 iff zero disagreements; on disagreement
prints the input and both outputs and exits 1. stdlib + Django (the package
under test) only.
"""
import collections
import json
import random
import sys

SEED = 13590
N_FUZZ = 100_000

QUERY = None            # the real patched Query instance; set in main()
CONTAINER_TYPE = None   # the concrete container kind of the current input;
                        # set per check (the bridge supplies the kind the
                        # bool `field_named` abstracts)


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- @ContractOnly callees bridged to the REAL repo counterparts -------------
# mapping.md section 1: resolve_one <-> the recursive per-element resolution;
# build_container <-> the unchanged container constructor of the kind, called
# under the convention `spread` denotes.

def resolve_one(sub_value):
    return QUERY.resolve_lookup_value(sub_value, None, True)


def build_container(elems, field_named, spread):
    if spread:
        return CONTAINER_TYPE(*elems)
    return CONTAINER_TYPE(elems)


# --- @Pure helper of model.py, copied on the PSeq shim ------------------------

def resolved_seq(s):
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(resolve_one(s[0])) + resolved_seq(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def resolve_sequence(value, field_named):
    resolved = []  # type: List[int]
    i = len(value)
    while i > 0:
        e = value[i - 1]
        resolved = [resolve_one(e)] + resolved
        i = i - 1
    if field_named:
        result = build_container(resolved, field_named, True)
    else:
        result = build_container(resolved, field_named, False)
    return result


# --- helpers ------------------------------------------------------------------

class Expr:
    """A sub-value carrying a deterministic `resolve_expression` (value-
    comparable result), so the per-element expression branch of the real
    recursion is exercised on both sides."""

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "Expr(%r)" % (self.tag,)

    def resolve_expression(self, *args, **kwargs):
        return ("resolved", self.tag)


def items_equal(a, b):
    """Per-index equality with an exact-type check for containers, so
    containers of different kinds (e.g. a field-named kind vs a plain tuple)
    holding equal sub-values never compare equal by accident."""
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        if type(a) is not type(b) or len(a) != len(b):
            return False
        return all(items_equal(x, y) for x, y in zip(a, b))
    same_none = (a is None) == (b is None)
    return same_none and a == b


def check_case(value):
    """Diff shadow vs oracle on one sequence value; return an error string on
    disagreement, else None."""
    global CONTAINER_TYPE
    type_ = type(value)
    CONTAINER_TYPE = type_
    # the bridge for the bool the model abstracts the kind into
    field_named = hasattr(type_, '_make')
    items = list(value)
    shadow_out = resolve_sequence(items, field_named)
    real_out = QUERY.resolve_lookup_value(value, None, True)
    if type(shadow_out) is not type(real_out):
        return ("DISAGREEMENT (container kind)\n  input=%r (%s)\n"
                "  shadow=%r (%s)\n  real=%r (%s)"
                % (value, type_.__name__,
                   shadow_out, type(shadow_out).__name__,
                   real_out, type(real_out).__name__))
    if len(shadow_out) != len(real_out):
        return ("DISAGREEMENT (length)\n  input=%r\n  shadow=%r\n  real=%r"
                % (value, shadow_out, real_out))
    for k in range(len(shadow_out)):
        if not items_equal(shadow_out[k], real_out[k]):
            return ("DISAGREEMENT (element %d)\n  input=%r\n  shadow=%r\n"
                    "  real=%r" % (k, value, shadow_out, real_out))
    # internal cross-check: the executable impl loop agrees with the pure
    # element-wise map of the spec region
    if ToSeq(list(shadow_out)) != resolved_seq(ToSeq(items)):
        return ("INTERNAL: impl region and pure fold disagree on %r"
                % (value,))
    return None


# --- input generation -----------------------------------------------------------

# field-named kinds of field counts 1..6 (generic field names)
NTS = [collections.namedtuple("NT%d" % n, ["f%d" % i for i in range(n)])
       for n in range(1, 7)]


def boundary_cases():
    NT1, NT2, NT3, NT4, NT5, NT6 = NTS
    return [
        [],
        (),
        [0],
        (0,),
        ["a"],
        ("a", "b"),
        NT1(5),                       # 1-field field-named kind
        NT2(51, 100),                 # the discriminating 2-field shape
        NT2("a", "b"),
        NT2(Expr("x"), Expr("y")),    # expression sub-values in a field-named kind
        NT2(None, 0),
        NT3(1, Expr("m"), "z"),
        NT4(0, 1, 2, 3),
        NT5("a", "b", "c", "d", "e"),
        NT6(1, 2, 3, 4, 5, 6),
        [Expr("x")],
        (Expr("x"),),
        ["a", Expr("y"), 3],
        (None, True, "", 0),
        [None, False, 0.0, -1],
        ["a", ["b", "c"], "d"],       # nested plain container (recursion)
        ("a", ("b", "c"), "d"),
        [NT2(1, 2), "x"],             # nested field-named container as element
        NT2([1, 2], (3, 4)),          # plain containers inside a field-named kind
        NT2(NT2(1, 2), NT1(3)),       # field-named nested in field-named
        (NT3("p", "q", "r"),),
        [0, 0, 0],
        list(range(50)),
        tuple(range(50)),
    ]


_POOL = [0, 1, -3, 42, 2 ** 40, "a", "b", "alpha", "", 3.5, -2.25,
         True, False, None]


def rand_item(rng, depth):
    r = rng.random()
    if r < 0.65 or depth >= 2:
        return rng.choice(_POOL)
    if r < 0.80:
        return Expr(rng.randint(0, 999))
    if r < 0.90:
        nt = rng.choice(NTS)
        return nt(*[rand_item(rng, depth + 1) for _ in nt._fields])
    inner = [rand_item(rng, depth + 1) for _ in range(rng.randint(0, 3))]
    return inner if rng.random() < 0.5 else tuple(inner)


def rand_value(rng):
    r = rng.random()
    if r < 0.35:
        nt = rng.choice(NTS)
        return nt(*[rand_item(rng, 0) for _ in nt._fields])
    n = rng.randint(0, 8)
    items = [rand_item(rng, 0) for _ in range(n)]
    return items if r < 0.70 else tuple(items)


# --- differential driver ----------------------------------------------------------

def run_checks():
    checked = 0
    boundary = boundary_cases()
    for value in boundary:
        err = check_case(value)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        err = check_case(rand_value(rng))
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched resolve_lookup_value on %d "
          "sequence inputs (%d boundary + %d fuzz over list/tuple/field-named "
          "kinds, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "ContractOnly callees bridged to the real "
                                "per-element resolution and the real "
                                "container constructor)"}))
    return 0


def main():
    global QUERY
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],
            DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3',
                                   'NAME': ':memory:'}},
        )
        django.setup()
    from django.contrib.auth.models import User
    from django.db.models.sql.query import Query
    QUERY = Query(User)
    return run_checks()


if __name__ == "__main__":
    sys.exit(main())
