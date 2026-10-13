#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-12050.

The bundle models ONE function: `Query.resolve_lookup_value`
(`django/db/models/sql/query.py`). Its Lean implementation
(`implementation_resolveLookupValue`) classifies a lookup `value` and resolves it:

    * an EXPRESSION (carries `resolve_expression`)  -> resolve it via the callee;
    * a SCALAR leaf                                 -> returned unchanged;
    * a LIST / TUPLE                                -> rebuild a collection of the
      SAME KIND whose entries are the RECURSIVE resolution of the entries.

This script transliterates that R/I impl into Python (`shadow`) and
differential-tests it against the ORACLE: a faithful in-process replica of the
POST-PATCH behavior of `resolve_lookup_value`:

    def resolve(value):
        if is_expr(value):
            return ('R', resolve_expression(value))     # the unchanged callee
        elif isinstance(value, (LST, TUP)):
            return type(value)(resolve(sub) for sub in value)   # the fix
        return value

We do NOT stand up a Django Query / ORM (heavy, and the modeled behavior is a
pure structural recursion over the value's shape). Instead we model an `LV` tree
with the SAME observables the dispatch keys on (mapping.md): "is this an
expression", "is this a list", "is this a tuple", else a scalar leaf. The real
`value.resolve_expression(...)` is an UNCHANGED callee (A-reference); the impl and
the oracle call it IDENTICALLY, so we stub it with the SAME deterministic function
on both legs (`resolve_expression(e) = ('E', e)`), which makes it cancel and
isolates the behavior the patch changes: container-type preservation + recursion.

The differential genuinely tests the Lean modeling: the shadow rebuilds the SAME
container kind and recurses through every entry (Lean `LV.lst (xs.map resolveSpec)`
/ `LV.tup (...)`), whereas the oracle reproduces the patched `type(value)(... for
sub in value)`. They must agree for every input — in particular a top-level LIST
(`Q(name=['a','b'])`), the case the patch fixes (pre-fix it became a tuple).

stdlib-only; deterministic built-in fuzzer. Pinned seed: 12050 (also in mapping.md).
"""
import sys

SEED = 12050
N = 120_000

# --- LV tree representation --------------------------------------------------
# A node is a tuple (kind, payload):
#   ("expr", e)   : an expression with opaque identity e (int)
#   ("plain", n)  : a scalar leaf with opaque identity n (int)
#   ("lst", [..]) : a list of LV nodes
#   ("tup", [..]) : a tuple of LV nodes
# The result is itself an LV node.


# --- the unchanged callee (A-reference), stubbed identically on both legs ----
def resolve_expression(e):
    # deterministic function of the expression identity; both legs use THIS.
    return ("plain", 10_000 + e)   # resolved form lands as a scalar carrier


# --- ORACLE: the post-patch resolve_lookup_value, faithful replica -----------
def oracle(value):
    kind = value[0]
    if kind == "expr":
        return resolve_expression(value[1])
    if kind in ("lst", "tup"):
        # type(value)(resolve(sub) for sub in value): SAME kind, recurse each
        return (kind, [oracle(sub) for sub in value[1]])
    # scalar leaf -> unchanged
    return value


# --- shadow of implementation_resolveLookupValue (the R/I leg) ---------------
# Mirrors Solution.lean resolveSpec/implementation: expr -> resolveExpression;
# plain -> itself; lst -> LV.lst of recursive resolutions; tup -> LV.tup ditto.
def shadow(value):
    kind = value[0]
    if kind == "expr":
        return resolve_expression(value[1])
    if kind == "plain":
        return value
    if kind == "lst":
        resolved = []
        for sub in value[1]:
            resolved.append(shadow(sub))
        return ("lst", resolved)
    if kind == "tup":
        resolved = []
        for sub in value[1]:
            resolved.append(shadow(sub))
        return ("tup", resolved)
    raise AssertionError(f"bad kind {kind!r}")


def disagree(value):
    got = oracle(value)
    want = shadow(value)
    if got != want:
        return (value, got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _enumerate_edge():
    """Hand-picked edge cases exercising the container-type + recursion fix."""
    e = lambda i: ("expr", i)
    p = lambda i: ("plain", i)
    return [
        # bare scalar / bare expression (PASS_TO_PASS shapes)
        p(1),
        e(2),
        # THE discriminating fix: a top-level list stays a list (Q(name=['a','b']))
        ("lst", [p(1), p(2)]),
        # a top-level tuple stays a tuple
        ("tup", [p(1), p(2)]),
        # empty list / empty tuple keep their kind
        ("lst", []),
        ("tup", []),
        # list of expressions -> list of resolved
        ("lst", [e(1), e(2), p(3)]),
        # tuple of expressions
        ("tup", [e(1), p(2)]),
        # nested list inside tuple (recursion must keep inner kind)
        ("tup", [("lst", [p(1), e(2)]), p(3)]),
        # nested tuple inside list
        ("lst", [("tup", [e(1)]), p(2)]),
        # deeply nested mix
        ("lst", [("tup", [("lst", [e(1), p(2)])]), p(3)]),
    ]


def _rand_lv(rnd, depth):
    tag = next(rnd) % 4
    if depth <= 0:
        # only leaves at max depth
        tag = next(rnd) % 2
    if tag == 0:
        return ("expr", next(rnd) % 50)
    if tag == 1:
        return ("plain", next(rnd) % 1000)
    children_n = next(rnd) % 5          # 0..4 entries
    children = [_rand_lv(rnd, depth - 1) for _ in range(children_n)]
    return ("lst" if tag == 2 else "tup", children)


def main() -> int:
    checked = 0

    for value in _enumerate_edge():
        d = disagree(value)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        value = _rand_lv(rnd, depth=4)
        d = disagree(value)
        if d:
            print(f"DISAGREE fuzz {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
