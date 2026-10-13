#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12050 (nagini).

SHADOW: the impl region of model.py's `resolve_iterable_value`, copied
verbatim below with the contract calls (Requires/Ensures/Invariant) stripped.
The `Iterable` carrier class is copied with its constructor contracts
stripped; there is no PSeq usage (the carrier is a plain List) and no @Pure
helper in this bundle. The single @ContractOnly callee, `normalise_item`,
calls the REAL repo function per the contract: mapping.md binds it to
`Query.resolve_lookup_value` applied to ONE sub-value, so the shadow's
`normalise_item` delegates to exactly that call on the real patched Query.

ORACLE: the REAL patched `django.db.models.sql.query.Query.resolve_lookup_value`
applied to the whole iterable value. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched code
importable. A minimal in-memory settings module is configured (no database
access is performed for plain/expression values).

Type bridge (mapping.md section 2):
  - `kind: int` in {0, 1}  <->  the concrete container type of the value
    (0 <-> list, 1 <-> tuple);
  - `items: List[int]` of opaque item identities  <->  the ordered items of
    the value; identity k of the input is the k-th item, and its normalised
    identity is the per-item resolution of that item.
To diff, each generated real value (a list or tuple of items) is abstracted
into (kind, items); the shadow output is concretised back into a container of
the shadow's `kind` holding the shadow's `items`, and compared against the
oracle output on: exact concrete type, length, and per-index item equality.

Input domain: the model's preconditions require only kind in {0, 1} and an
arbitrary item list, i.e. any plain list or tuple of items. Items mix plain
scalars (ints, strings, None, bools, floats), objects carrying a
deterministic `resolve_expression` (so both per-item branches of the real
callee are exercised), and nested lists/tuples (the per-item call recurses).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz containers.
Pinned fuzz seed: 12050.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + Django (the package under test) only.
"""
import json
import random
import sys

SEED = 12050
N_FUZZ = 100_000

QUERY = None  # the real patched Query instance; set in main()


# --- @ContractOnly callee bridged to the REAL repo function --------------------
# mapping.md: normalise_item(item) <-> Query.resolve_lookup_value applied to a
# single sub-value.

def normalise_item(item):
    return QUERY.resolve_lookup_value(item, can_reuse=set(),
                                      allow_joins=True, simple_col=False)


# --- carrier class from model.py, constructor contracts stripped ---------------

class Iterable:
    def __init__(self, kind):
        self.kind = kind  # type: int
        self.items = []  # type: List[int]


# --- the impl region of model.py, verbatim (contract calls stripped) -----------

def resolve_iterable_value(value):
    out = Iterable(value.kind)
    i = 0
    while i < len(value.items):
        out.items.append(normalise_item(value.items[i]))
        i = i + 1
    return out
    # (impl region end)


# --- bridge helpers -------------------------------------------------------------

def abstract(real_value):
    """Real list/tuple -> model Iterable (kind tag + ordered items)."""
    it = Iterable(0 if isinstance(real_value, list) else 1)
    it.items = list(real_value)
    return it


def concretise(model_out):
    """Model Iterable -> the concrete container its kind tag denotes."""
    if model_out.kind == 0:
        return list(model_out.items)
    return tuple(model_out.items)


class Expr:
    """An item carrying a deterministic `resolve_expression` (value-comparable
    result), so the per-item rule's expression branch is exercised."""

    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "Expr(%r)" % (self.tag,)

    def resolve_expression(self, query, **kwargs):
        return ("resolved", self.tag)


def items_equal(a, b):
    """Per-index equality with an exact-type check for containers, so a list
    and a tuple of equal items never compare equal by accident."""
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        if type(a) is not type(b) or len(a) != len(b):
            return False
        return all(items_equal(x, y) for x, y in zip(a, b))
    same_none = (a is None) == (b is None)
    return same_none and a == b


def check_case(value):
    """Diff shadow vs oracle on one list/tuple value; return an error string
    on disagreement, else None."""
    shadow_out = concretise(resolve_iterable_value(abstract(value)))
    real_out = QUERY.resolve_lookup_value(value, can_reuse=set(),
                                          allow_joins=True, simple_col=False)
    if type(shadow_out) is not type(real_out):
        return ("DISAGREEMENT (container type)\n  input=%r\n  shadow=%r (%s)\n"
                "  real=%r (%s)" % (value, shadow_out, type(shadow_out).__name__,
                                    real_out, type(real_out).__name__))
    if len(shadow_out) != len(real_out):
        return ("DISAGREEMENT (length)\n  input=%r\n  shadow=%r\n  real=%r"
                % (value, shadow_out, real_out))
    for k in range(len(shadow_out)):
        if not items_equal(shadow_out[k], real_out[k]):
            return ("DISAGREEMENT (item %d)\n  input=%r\n  shadow=%r\n  real=%r"
                    % (k, value, shadow_out, real_out))
    return None


# --- input generation -----------------------------------------------------------

def boundary_cases():
    return [
        [],
        (),
        [0],
        (0,),
        ["a"],
        ("a",),
        ["a", "b"],                 # the F2P-shaped input
        ("a", "b", "c"),
        [Expr("x")],
        (Expr("x"),),
        ["a", Expr("y"), 3],
        (None, True, "", 0),
        [None, False, 0.0, -1],
        ["a", ["b", "c"], "d"],     # nested list item (per-item call recurses)
        ("a", ("b", "c"), "d"),
        [["x"], ("y",)],
        [0, 0, 0],
        list(range(50)),
        tuple(range(50)),
    ]


_POOL = [0, 1, -3, 42, 2 ** 40, "a", "b", "alpha", "", 3.5, -2.25,
         True, False, None]


def rand_item(rng, depth):
    r = rng.random()
    if r < 0.70 or depth >= 2:
        return rng.choice(_POOL)
    if r < 0.85:
        return Expr(rng.randint(0, 999))
    inner = [rand_item(rng, depth + 1) for _ in range(rng.randint(0, 3))]
    return inner if rng.random() < 0.5 else tuple(inner)


def rand_value(rng):
    n = rng.randint(0, 8)
    items = [rand_item(rng, 0) for _ in range(n)]
    return items if rng.random() < 0.5 else tuple(items)


# --- main -----------------------------------------------------------------------

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

    checked = 0
    for value in boundary_cases():
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
          "list/tuple inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "ContractOnly callee bridged to the real "
                                "per-item resolution)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
