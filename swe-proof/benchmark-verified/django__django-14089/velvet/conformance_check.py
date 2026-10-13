#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14089 (plan §4.1).

Refutes (does not prove) the R/I refinement leg of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo type (the OrderedSet, via the
              mapping.md bijection `List Int` ↔ the keys of `self.dict`). The
              `reverseEnum` impl region is a backward append loop that builds the
              reversal of the forward enumeration, followed by the eight
              observations of the traversal handles: one handle's own answer to a
              single-element request (`result.head?`), `demand` further single
              draws (`List.take j remaining`), what is left (`List.drop j
              remaining`), what a second drain yields (`[]`), what a FRESH handle
              answers to a positional read (`none`), what a FRESH handle
              yields to a consumer that only drains it (`result`), what a
              consumer collects from a FRESH handle by taking the element at
              position 0, then 1, then 2, until refused (`[]`), and how many
              DISTINCT things a consumer is left holding after asking a FRESH
              handle twice over to supply the thing that is to be stepped, the
              handle itself included (`1`). There is no
              consumed axiom in the impl region, so the shadow is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `OrderedSet.__reversed__`
              applied at base_commit (the real correctness oracle, G-RESOLVE),
              interrogated in exactly that order on FIVE handles taken from the
              same unchanged collection: `h = reversed(OrderedSet(items))` gets
              `next(h, None)`, then `demand` further `next(h)` calls, then
              `list(h)`, then `list(h)` again; a fresh `h2` gets `h2[0]`, with a
              `TypeError` (or `IndexError`/`KeyError`) read as the refusal
              `None`; a fresh `h3` gets `list(h3)` with no prior advance; a
              fresh `h4` is collected position by position through the object's
              OWN element-at-position access (`operator.getitem(h4, j)` for
              j = 0, 1, 2, ... until it refuses), which is the access path an
              index-driven traversal itself uses (mapping.md §1); and a fresh
              `h5` is asked TWICE for the thing that is to be stepped —
              `iter(h5)` twice, the request every consumer and every for-each
              walk issues before drawing — after which the DISTINCT objects the
              consumer holds are counted, `h5` included.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample. Because the oracle side puts the
single-element request to the handed-back object itself, drains that same object
twice, asks a fresh one for an element by index, drains a fresh one without
advancing it, tries to collect a fresh one position by position through the
object's own element-at-position access, and counts what a fresh one nominates
as the thing to be stepped, this refutation covers the
self-advancing, one-shot, index-free, already-populated and self-nominating
observations (refinement.md A3/A5/A7/A8/A9), not just the enumerated sequence.
The position-by-position leg matters because a SINGLE refused positional read is
a fact about that one question, whereas refusing the 0, 1, 2, ... sequence is a
fact about the object: it is the access path an index-driven traversal uses, so
an object that served it would be reachable by position however it answers a
bare read. The self-nomination leg matters for a different reason: every one of
the other seven observations reports which ELEMENTS emerged from which channel,
and an object that merely SUPPLIES a traversal produces the same element reports
as the traversal itself, so only counting the objects a consumer ends up holding
distinguishes them.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib only. The
fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import operator
import random
import sys

SEED = 14089
N_FUZZ = 100_000


def shadow_observe(items, demand):
    """reverseEnum's impl region transliterated to Python over the carrier:
    the backward append loop produces the reversal of the forward enumeration
    (the distinct keys in insertion order), and the eight handle observations
    are read off it. `dict.fromkeys` realizes OrderedSet's insertion-ordered
    distinct keys (mapping.md §2)."""
    keys = list(dict.fromkeys(items))    # forward enumeration (List Int carrier)
    result = []
    i = len(keys)
    while i > 0:                         # backward loop, append from the end
        result = result + [keys[i - 1]]
        i = i - 1
    given = result[0] if result else None            # result.head?
    remaining = result[1:]                           # result.tail
    j = 0
    while j < demand and j < len(remaining):         # the `demand` further draws
        j = j + 1
    drawn = remaining[:j]                            # List.take j remaining
    first_drain = remaining[j:]                      # List.drop j remaining
    k = j
    while k < len(remaining):                        # the drain carries j forward
        k = k + 1
    second_drain = remaining[k:]                     # List.drop k remaining
    positional = None                                # (none : Option Int)
    fresh_drain = result                             # the whole enumeration
    by_position = []                                 # ([] : List Int)
    held_distinct = 1                                # (1 : Nat)
    return (given, drawn, first_drain, second_drain, positional, fresh_drain,
            by_position, held_distinct)


def oracle_observe(items, demand):
    """patch.diff's behaviour: FIVE handles from the patched
    OrderedSet.__reversed__ over the same unchanged collection, interrogated the
    eight ways mapping.md §1 binds.
    The harness applies patch.diff at base_commit before this runs."""
    from django.utils.datastructures import OrderedSet
    collection = OrderedSet(items)
    h = reversed(collection)
    given = next(h, None)                # the handle's own answer, or a refusal
    drawn = []
    for _ in range(demand):              # further single draws on the SAME handle
        nxt = next(h, None)
        if nxt is None:
            break
        drawn.append(nxt)
    first_drain = list(h)                # what that same handle has left
    second_drain = list(h)               # asking the spent handle again
    h2 = reversed(collection)            # a FRESH handle, holding everything
    try:                                 # a request for the element AT A POSITION
        positional = h2[0]
    except (TypeError, IndexError, KeyError):
        positional = None                # refused: the handle has no positions
    h3 = reversed(collection)            # a FRESH handle, never advanced
    fresh_drain = list(h3)               # asked only to yield everything
    h4 = reversed(collection)            # a FRESH handle, collected BY POSITION
    by_position = []                     # position 0, then 1, then 2, ...
    for idx in range(len(collection) + 1):
        try:                             # the object's OWN element-at-position
            by_position.append(operator.getitem(h4, idx))
        except Exception:                # refused: stop collecting there
            break
    h5 = reversed(collection)            # a FRESH handle, asked what to step
    try:                                 # the request a for-each walk issues
        nominated_a = iter(h5)           # ... and the same request again
        nominated_b = iter(h5)           # (both kept alive, so no id reuse)
    except TypeError:                    # declined: nothing was nominated
        held_distinct = 0
    else:                                # the handle plus what it nominated
        held_distinct = len({id(h5), id(nominated_a), id(nominated_b)})
    return (given, drawn, first_drain, second_drain, positional, fresh_drain,
            by_position, held_distinct)


def fuzz_inputs(n, rng):
    # boundary cases first: (items, demand)
    yield [], 0                   # empty collection
    yield [], 3
    yield [1], 0                  # singleton, no further draws
    yield [1], 1
    yield [1, 2, 3], 0            # the F2P witness -> 3, then [2, 1]
    yield [1, 2, 3], 1
    yield [1, 2, 3], 2            # demand exactly drains the remainder
    yield [1, 2, 3], 7            # demand past the end
    yield [3, 2, 1], 2
    yield [0, -1, -2, 5, 100], 3
    yield [1, 1, 2, 2, 3], 2      # duplicates collapse to distinct keys
    yield [5, 5, 5], 1
    yield list(range(40)), 0
    yield list(range(40)), 39
    yield list(range(40))[::-1], 40
    for _ in range(n):
        k = rng.randint(0, 40)
        yield [rng.randint(-20, 20) for _ in range(k)], rng.randint(0, 45)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for items, demand in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_observe(items, demand)
        oracle = oracle_observe(items, demand)
        if shadow != oracle:
            disagreements.append((items, demand, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for it, dm, sh, orc in disagreements:
            print("  items=%r demand=%r shadow=%r oracle=%r" % (it, dm, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of reverseEnum (all eight handle observations) "
          "agrees with patch.diff behaviour on %d inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
