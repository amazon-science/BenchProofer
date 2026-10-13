#!/usr/bin/env python3
"""G-CONF for django__django-13590.

The gold patch is already applied to /testbed when this runs. We compare the
R/I Python shadow of `implementation_resolveValue` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`Query.resolve_lookup_value`, over >=1e5 fuzzed values. Zero disagreements => 0.

Model (refinement.md / mapping.md): a value is a scalar, a single resolvable
expression, or a finite sequence carrying a container kind drawn from
{plain (list), tupleLike (plain tuple), special (namedtuple, i.e.
`hasattr(type_, '_make')`)}. Resolution is structural: scalar -> itself,
expression -> `resolveExpr` of it, sequence -> a sequence of the SAME length and
SAME container kind whose elements are the resolved originals.

  * Oracle = the REAL patched `Query.resolve_lookup_value` bound to a dummy
             `self` (the method only recurses through `self.resolve_lookup_value`
             and passes `self` to `resolve_expression`; no DB needed).
  * Shadow = `resolveRef` (the Lean pure helper), with `resolveExpr` bound to the
             SAME fixed deterministic resolver used on the oracle side.

Type bijection (mapping.md): Value.scalar n <-> int n; Value.expr id <-> an
object carrying `resolve_expression` that resolves to int (SENTINEL_BASE+id);
Value.seq plain <-> list; Value.seq tupleLike <-> plain tuple; Value.seq special
<-> namedtuple. result Option Value: post-patch resolution always succeeds, so we
compare the unwrapped value. The container kind is part of the comparison: the
oracle's output type (list / plain tuple / namedtuple) must match the modeled
kind. stdlib-only; no hypothesis required.
"""
import collections
import os
import random
import sys
import types

# --- configure Django settings before importing the query machinery ----------
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        USE_L10N=False,
        DATABASES={},
        INSTALLED_APPS=[],
        USE_I18N=False,
    )
    django.setup()

from django.db.models.sql.query import Query

SENTINEL_BASE = 700000  # resolveExpr(id) := scalar(SENTINEL_BASE + id)


# --- dummy `self` carrying the REAL patched resolve_lookup_value --------------
class _Dummy:
    pass


_dummy = _Dummy()
_dummy.resolve_lookup_value = types.MethodType(Query.resolve_lookup_value, _dummy)


# --- an "expression" object: resolve_expression(self, reuse, allow_joins) -----
class _Expr:
    def __init__(self, ident):
        self.ident = ident

    def resolve_expression(self, query, reuse=None, allow_joins=True):
        # the fixed deterministic resolver bound on BOTH sides
        return SENTINEL_BASE + self.ident


# --- canonical encoding so oracle output and shadow output are comparable -----
def canon(obj):
    if isinstance(obj, _Expr):  # should never survive resolution, defensive
        return ("expr", obj.ident)
    if isinstance(obj, int):
        return ("s", obj)
    type_ = type(obj)
    if hasattr(type_, "_make"):  # namedtuple -> special
        return ("seq", "special", [canon(x) for x in obj])
    if isinstance(obj, list):  # list -> plain
        return ("seq", "plain", [canon(x) for x in obj])
    if isinstance(obj, tuple):  # plain tuple -> tupleLike
        return ("seq", "tupleLike", [canon(x) for x in obj])
    raise AssertionError("unexpected object in oracle output: %r" % (obj,))


# --- shadow: resolveRef (the Lean pure helper) over the abstract Value tree ---
def resolve_ref(v):
    """v is the abstract Value: ('s',n) | ('e',id) | ('seq',kind,[...])."""
    tag = v[0]
    if tag == "s":
        return ("s", v[1])
    if tag == "e":
        return ("s", SENTINEL_BASE + v[1])  # resolveExpr(id)
    if tag == "seq":
        _, kind, elems = v
        return ("seq", kind, [resolve_ref(e) for e in elems])
    raise AssertionError("bad Value: %r" % (v,))


# --- build the concrete Python object an abstract Value denotes ----------------
_NT_CACHE = {}


def _namedtuple_type(n):
    if n not in _NT_CACHE:
        _NT_CACHE[n] = collections.namedtuple(
            "NT%d" % n, ["f%d" % i for i in range(n)]
        )
    return _NT_CACHE[n]


def to_py(v):
    tag = v[0]
    if tag == "s":
        return v[1]
    if tag == "e":
        return _Expr(v[1])
    if tag == "seq":
        _, kind, elems = v
        parts = [to_py(e) for e in elems]
        if kind == "special":
            return _namedtuple_type(len(parts))(*parts)
        if kind == "plain":
            return list(parts)
        if kind == "tupleLike":
            return tuple(parts)
        raise AssertionError("bad kind: %r" % (kind,))
    raise AssertionError("bad Value: %r" % (v,))


# --- random Value generator ----------------------------------------------------
_KINDS = ["plain", "tupleLike", "special"]


def gen_value(rng, depth):
    if depth <= 0:
        # leaf: scalar or expression
        if rng.random() < 0.5:
            return ("s", rng.randint(-50, 50))
        return ("e", rng.randint(0, 20))
    r = rng.random()
    if r < 0.30:
        return ("s", rng.randint(-50, 50))
    if r < 0.50:
        return ("e", rng.randint(0, 20))
    # a sequence; bias toward the special (namedtuple) discriminating case
    kr = rng.random()
    kind = "special" if kr < 0.5 else ("plain" if kr < 0.75 else "tupleLike")
    n = rng.randint(0, 4)
    elems = [gen_value(rng, depth - 1) for _ in range(n)]
    return ("seq", kind, elems)


# fixed cases covering the issue and boundaries
FIXED = [
    ("s", 42),
    ("e", 3),
    ("seq", "plain", [("s", 1), ("s", 2)]),                       # list
    ("seq", "tupleLike", [("s", 1), ("s", 2)]),                   # plain tuple
    ("seq", "special", [("s", 51), ("s", 100)]),                  # the namedtuple range case
    ("seq", "special", [("e", 1), ("e", 2)]),                     # namedtuple of expressions
    ("seq", "special", []),                                       # empty namedtuple
    ("seq", "plain", []),                                         # empty list
    ("seq", "tupleLike", []),                                     # empty tuple
    ("seq", "special", [("seq", "special", [("s", 7)]), ("s", 8)]), # nested namedtuple
    ("seq", "plain", [("seq", "special", [("e", 0)]), ("s", 9)]), # list containing namedtuple
    ("seq", "tupleLike", [("seq", "plain", [("s", 2)])]),         # tuple containing list
    ("seq", "special", [("s", 1)]),                               # 1-field namedtuple
]


def main():
    rng = random.Random(13590)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        v = FIXED[i] if i < len(FIXED) else gen_value(rng, rng.randint(0, 3))
        py = to_py(v)
        try:
            out = _dummy.resolve_lookup_value(py, can_reuse=None, allow_joins=True)
            o = canon(out)
        except Exception as exc:  # the pre-patch TypeError would land here
            o = ("RAISED", type(exc).__name__)
        s = resolve_ref(v)
        if o != s:
            disagreements += 1
            if first is None:
                first = (v, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
