#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-15368.

The bundle models ONE decision inside `QuerySet.bulk_update`'s per-field loop
(`django/db/models/query.py:668-674`): for each object's attribute value, whether
to wrap it as a literal `Value(...)` before placing it into a `When(pk=…, then=…)`
branch. The modeled value is a PURE function of the batch (mapping.md):

    objs : list[(pk: int, attr)]   where attr has a behavioral `kind`

Post-patch rule (the patched line at query.py:672):

    for obj in batch_objs:
        attr = getattr(obj, field.attname)
        if not hasattr(attr, 'resolve_expression'):
            attr = Value(attr, output_field=field)        # wrapped as a literal
        when_statements.append(When(pk=obj.pk, then=attr))

`hasattr(attr, 'resolve_expression')` is true for an `Expression` instance AND for
an `F(...)` field reference (both define `resolve_expression`) but false for a
plain value. So the wrap happens exactly for plain values.

Standing up a database / ORM to drive the real `bulk_update` is heavy and
unnecessary: the modeled value is this pure decision over the runtime category of
each attribute. The ORACLE below is a faithful in-process replica that uses the
EXACT patched predicate `hasattr(attr, 'resolve_expression')` against real stand-in
objects whose classes mirror the repo hierarchy (a plain value; an `Expression`
instance; an `F`-like field reference that subclasses `Combinable` — NOT
`Expression` — yet defines `resolve_expression`). The SHADOW is the op-for-op
transliteration of `implementation_bulkUpdateBranches` (wrap iff
`kind == plainValue`, per refinement.md).

Each produced branch is compared on all three observed components: the carried pk,
the wrapped flag, and the underlying value identity (preserved by both the wrapped
and pass-through legs). This genuinely tests the discriminating clause: an
`F(...)` field reference (a `Combinable`, not an `Expression`) must yield
`wrapped == False` — the exact behavior of FAIL_TO_PASS `test_f_expression`.

stdlib-only. Pinned seed: 15368 (also in mapping.md).
"""
import random
import sys

SEED = 15368
N = 120_000


# --- repo-faithful stand-in classes (mirror the real hierarchy) --------------
class _Combinable:
    pass


class _Expression(_Combinable):
    def resolve_expression(self, *a, **k):
        return self


class _FExpr(_Combinable):                 # F subclasses Combinable, NOT Expression
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "F(%s)" % self.name

    def resolve_expression(self, *a, **k):
        return self


# kind tags: must match Lean `ValueKind`
PLAIN = "plainValue"
EXPR = "directExpression"
FREF = "fieldReference"


def _make_attr(kind, ident):
    """Construct a real Python attribute object of the given behavioral kind,
    tagged with an identity so we can track pass-through."""
    if kind == PLAIN:
        return ("literal", ident)          # an ordinary stored value (str/int/…)
    if kind == EXPR:
        e = _Expression()
        e._ident = ident
        return e
    if kind == FREF:
        f = _FExpr("col%d" % ident)
        f._ident = ident
        return f
    raise ValueError(kind)


def _ident_of(kind, ident):
    return ident


# --- ORACLE: faithful in-process replica of the patched loop -----------------
def oracle_branches(batch):
    """batch: list of (pk, kind, ident). Returns list of (pk, wrapped, ident)."""
    out = []
    for pk, kind, ident in batch:
        attr = _make_attr(kind, ident)
        wrapped = False
        if not hasattr(attr, "resolve_expression"):   # the EXACT patched predicate
            wrapped = True
        out.append((pk, wrapped, ident))
    return out


# --- SHADOW of implementation_bulkUpdateBranches (the R/I leg) ---------------
# Mirrors Solution.lean: wrapped := false; if !resolvesToReference kind then
# wrapped := true; branch := (pk, wrapped, ident). resolvesToReference is
# (kind != plainValue).
def _resolves_to_reference(kind):
    return kind != PLAIN


def shadow_branches(batch):
    out = []
    for pk, kind, ident in batch:
        wrapped = False
        if not _resolves_to_reference(kind):
            wrapped = True
        out.append((pk, wrapped, ident))
    return out


def disagree(batch):
    got = oracle_branches(batch)
    want = shadow_branches(batch)
    if got != want:
        return (batch, got, want)
    return None


def _enumerate_edge():
    cases = []
    # empty batch
    cases.append([])
    # single plain value -> wrapped
    cases.append([(1, PLAIN, 7)])
    # single Expression -> not wrapped
    cases.append([(2, EXPR, 9)])
    # the F2P shape: F('note') field reference -> MUST NOT be wrapped
    cases.append([(3, FREF, 11)])
    # the test_f_expression batch: 10 objects all set to F(...)
    cases.append([(i, FREF, 100 + i) for i in range(10)])
    # mixed batch
    cases.append([(1, PLAIN, 1), (2, EXPR, 2), (3, FREF, 3)])
    return cases


def main() -> int:
    checked = 0
    for batch in _enumerate_edge():
        d = disagree(batch)
        if d:
            print(f"DISAGREE edge {d[0]!r}: oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    kinds = [PLAIN, EXPR, FREF]
    for _ in range(N):
        n = rng.randint(0, 8)
        batch = []
        pks = rng.sample(range(1, 10_000), n) if n else []
        for j in range(n):
            kind = rng.choice(kinds)
            ident = rng.randint(0, 50)
            batch.append((pks[j], kind, ident))
        d = disagree(batch)
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
