#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13590 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of `refinement.md`: the deep
reconstruction model of Solution.lean (`resolvedSeq` + the `positionalCtor`
branch) transliterated to Python, differential-tested against `patch.diff`'s
reconstruction behaviour over `list`, `tuple`, and `namedtuple` carriers — the
three sequence types the change distinguishes.

ORACLE CHOICE — why we transliterate the patched reconstruction VERBATIM instead
of driving the real `Query.resolve_lookup_value`:
  The real method lives on `django.db.models.sql.query.Query`; exercising its
  list/tuple branch requires a constructed `Query` bound to a model, plus
  `can_reuse`/`allow_joins` join machinery, purely to read back the reconstructed
  container. The per-element call it makes (`self.resolve_lookup_value(sub_value,
  …)`) is UNCHANGED by the patch — pre- and post-patch resolve each member
  identically; only the RECONSTRUCTION of the container from the resolved members
  changed. So, per the worker prompt, the ORACLE is the gold-patched
  reconstruction transliterated verbatim from
  django/db/models/sql/query.py:1077-1086 (the `elif isinstance(value, (list,
  tuple))` body), and the per-member resolution is abstracted by an in-process
  resolver `f` (the free `f : Int -> Int` of the spec). The SHADOW is the deep
  model `resolvedSeq` from Solution.lean. We differential-test over many
  (carrier-type, members, resolver) triples. Exit 0 iff zero disagreements.

stdlib only (`collections.namedtuple`). The fuzz seed is pinned (mapping.md §4).
"""
import random
import sys
from collections import namedtuple

SEED = 13590
N_FUZZ = 100_000


# ---- ORACLE: patch.diff reconstruction, transliterated verbatim -----------
def oracle_reconstruct(value, f):
    """The gold-patched reconstruction of `value` from its per-element-resolved
    members (django/db/models/sql/query.py post-patch). `f` stands for the
    unchanged per-member `self.resolve_lookup_value(sub_value, ...)` call."""
    values = (f(sub_value) for sub_value in value)
    type_ = type(value)
    if hasattr(type_, '_make'):      # namedtuple
        return type_(*values)
    return type_(values)


# ---- HELPER-LEVEL ORACLES: the raw reconstruction primitives --------------
def oracle_rebuild_positional(value, resolved):
    """`type_(*values)` — supply resolved members as separate positional args,
    UNGUARDED (what the gold patch only ever does behind hasattr(_, '_make'))."""
    return type(value)(*resolved)


def oracle_rebuild_iterable(value, resolved):
    """`type_(values)` — hand the type one iterable of the resolved members,
    UNGUARDED (the pre-patch behaviour for every type)."""
    return type(value)(resolved)


# ---- HELPER-LEVEL SHADOWS: Solution.lean rebuildPositional/rebuildIterable -
def shadow_rebuild_positional(value, resolved):
    """rebuildPositional: .ok iff positionalCtor OR items = [], else
    .error positionalNotAccepted (a list/tuple ctor takes one iterable, so a
    ≥1-member splat raises; the empty splat degenerates to the 0-arg call)."""
    positional_ctor = hasattr(type(value), '_make')
    if positional_ctor or len(resolved) == 0:
        return type(value)(*resolved)
    raise TypeError('positionalNotAccepted')


def shadow_rebuild_iterable(value, resolved):
    """rebuildIterable: .ok iff not positionalCtor, else
    .error iterableNotAccepted (a namedtuple's __new__ wants the members
    positionally, not one iterator)."""
    positional_ctor = hasattr(type(value), '_make')
    if positional_ctor:
        raise TypeError('iterableNotAccepted')
    return type(value)(resolved)


# ---- SHADOW: Solution.lean `resolvedSeq` + positionalCtor branch ----------
def shadow_reconstruct(value, f):
    """resolvedSeq (positionalCtor s.items f), transliterated. positionalCtor
    <-> hasattr(type_, '_make'); items <-> list(value); the always-ok result
    is the reconstructed container of the same type carrying `items.map f`."""
    type_ = type(value)
    positional_ctor = hasattr(type_, '_make')
    resolved = [f(sub_value) for sub_value in value]   # items.map f
    if positional_ctor:
        return type_(*resolved)                        # rebuildPositional
    return type_(resolved)                             # rebuildIterable


def observe(container):
    """Map a reconstructed container to its observable content: (type name,
    is-positional-ctor, members-in-order). This is the SeqVal the spec pins."""
    type_ = type(container)
    return (type_.__name__, hasattr(type_, '_make'), list(container))


def carriers(rng):
    """Yield (value, f) test points over the three sequence types."""
    Pair = namedtuple('Pair', ['minimum', 'maximum'])
    Triple = namedtuple('Triple', ['a', 'b', 'c'])
    resolvers = [
        lambda x: x,
        lambda x: x + 1,
        lambda x: -x,
        lambda x: x * x,
        lambda x: 0,
    ]
    # boundary cases first (plan §4.1 step 4)
    yield ([], resolvers[0])
    yield ((), resolvers[1])
    yield ([1], resolvers[2])
    yield ((9,), resolvers[3])
    yield ([1, 2, 3], resolvers[1])
    yield ((4, 5, 6, 7), resolvers[2])
    yield (Pair(51, 100), resolvers[0])      # the F2P namedtuple shape
    yield (Pair(51, 100), resolvers[1])
    yield (Triple(1, 2, 3), resolvers[3])
    for _ in range(N_FUZZ):
        kind = rng.randint(0, 3)
        f = rng.choice(resolvers)
        if kind == 0:                        # list
            k = rng.randint(0, 8)
            yield ([rng.randint(-50, 50) for _ in range(k)], f)
        elif kind == 1:                      # tuple
            k = rng.randint(0, 8)
            yield (tuple(rng.randint(-50, 50) for _ in range(k)), f)
        elif kind == 2:                      # 2-namedtuple
            yield (Pair(rng.randint(-50, 50), rng.randint(-50, 50)), f)
        else:                                # 3-namedtuple
            yield (Triple(rng.randint(-50, 50),
                          rng.randint(-50, 50),
                          rng.randint(-50, 50)), f)


def _probe(fn, *args):
    """Run fn, mapping success to (observable, None) and any raise to
    (None, True). Helper partiality is compared on WHETHER construction
    fails (the Lean model has one error per helper), not the message."""
    try:
        return observe(fn(*args)), None
    except Exception:                                # noqa: BLE001
        return None, True


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for value, f in carriers(rng):
        count += 1
        try:
            o = observe(oracle_reconstruct(value, f))
            o_err = None
        except Exception as e:                       # noqa: BLE001
            o, o_err = None, type(e).__name__
        try:
            s = observe(shadow_reconstruct(value, f))
            s_err = None
        except Exception as e:                       # noqa: BLE001
            s, s_err = None, type(e).__name__
        if (o, o_err) != (s, s_err):
            disagreements.append(('dispatch', value, (s, s_err), (o, o_err)))
        # Helper-level differential: each spec helper vs its UNGUARDED real
        # primitive, on every carrier — including the off-gold pairings
        # (positional splat on list/tuple, iterable ctor on namedtuple), so a
        # totality over-claim in either helper is refuted, not just the
        # gold-path dispatch.
        resolved = [f(sv) for sv in value]
        if _probe(oracle_rebuild_positional, value, resolved) != \
                _probe(shadow_rebuild_positional, value, resolved):
            disagreements.append(
                ('rebuildPositional', value,
                 _probe(shadow_rebuild_positional, value, resolved),
                 _probe(oracle_rebuild_positional, value, resolved)))
        if _probe(oracle_rebuild_iterable, value, resolved) != \
                _probe(shadow_rebuild_iterable, value, resolved):
            disagreements.append(
                ('rebuildIterable', value,
                 _probe(shadow_rebuild_iterable, value, resolved),
                 _probe(oracle_rebuild_iterable, value, resolved)))
        if len(disagreements) >= 5:
            break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for site, v, sh, orc in disagreements:
            print("  site=%s input=%r shadow=%r oracle=%r" % (site, v, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reconstructSequence agrees with patch.diff "
          "reconstruction over %d inputs (seed=%d), 0 disagreements "
          "(dispatch + both helper primitives)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
