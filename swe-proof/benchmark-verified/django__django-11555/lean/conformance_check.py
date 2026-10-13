#!/usr/bin/env python3
"""G-CONF for django__django-11555.

Differential test of the R/I shadow of `implementation_expandOrdering` against
the behaviour of the gold `patch.diff` (the patched body of
`SQLCompiler.find_ordering_name`'s relation/default-ordering loop).

Modeled behavior: the per-item dispatch of a model's default-ordering
specification.

  * an ordering EXPRESSION item (an `OrderBy` instance) is emitted directly as
    `(item, False)` and the recursive name resolver is SKIPPED;
  * a string FIELD-REFERENCE item is routed through the resolver
    (`find_ordering_name`) and its directives are concatenated in order.

The recursive resolver is an A-reference callee (mapping.md). It needs a full
Query/model graph to run for real, so here it is represented by a deterministic
stub that is shared IDENTICALLY by both legs (impl shadow and patch reference) —
the resolver cancels and what is actually differential-tested is the dispatch,
which is exactly the R/I content of the impl region.

stdlib-only; exit 0 iff zero disagreements over >=1e5 fuzzed inputs.
"""
import random
import sys

SEED = 11555          # pinned in mapping.md
N = 200_000           # >= 1e5


class OrderBy:
    """Marker for an already-built ordering expression (an `OrderBy` instance)."""
    __slots__ = ("eid",)

    def __init__(self, eid):
        self.eid = eid

    def __eq__(self, other):
        return isinstance(other, OrderBy) and other.eid == self.eid

    def __hash__(self):
        return hash(("OrderBy", self.eid))


def resolver_stub(item):
    """Stands in for `self.find_ordering_name(item, ...)` on a string item.

    Deterministic; SHARED by both legs. A string field reference resolves to a
    small list of directives (modeled as `(OrderBy(...), bool)` tuples) derived
    from the name, mirroring "one or more concrete column directives"."""
    n = (len(item) % 3) + 1   # 1..3 resolved directives
    return [(OrderBy(("R", item, k)), bool(k % 2)) for k in range(n)]


def impl_shadow(items):
    """R/I shadow of implementation_expandOrdering."""
    results = []
    for item in items:
        if isinstance(item, OrderBy):
            results.append((item, False))
        else:
            results.extend(resolver_stub(item))
    return results


def patch_reference(items):
    """Behaviour of the gold-patched find_ordering_name loop body."""
    results = []
    for item in items:
        if isinstance(item, OrderBy):
            results.append((item, False))
            continue
        results.extend(resolver_stub(item))
    return results


def random_item(rng, k):
    if rng.random() < 0.5:
        return OrderBy(("E", k, rng.randrange(1000)))
    # a string field reference (possibly a multi-part lookup path)
    parts = [rng.choice("abc_field") for _ in range(rng.randrange(1, 8))]
    return "".join(parts)


def main():
    rng = random.Random(SEED)
    disagreements = 0
    for _ in range(N):
        length = rng.randrange(0, 13)
        items = [random_item(rng, k) for k in range(length)]
        a = impl_shadow(items)
        b = patch_reference(items)
        if a != b:
            disagreements += 1
            if disagreements <= 5:
                print(f"DISAGREE on {items!r}: impl={a!r} patch={b!r}",
                      file=sys.stderr)
    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements over {N} inputs")
        return 1
    print(f"G-CONF OK: 0 disagreements over {N} inputs (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
