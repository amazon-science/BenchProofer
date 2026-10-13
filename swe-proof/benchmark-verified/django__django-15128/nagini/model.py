"""Twin-artifact model for django__django-15128.

Behaviour under specification (an abstract behavioural contract):

  Given an ordered list of current aliases, a target namespace, and one
  designated alias to leave unmapped, the operation produces a relabel map
  (a partial function from current aliases to new aliases) with these
  properties:

    * the designated alias is NOT a key of the map (it is left unmapped);
    * every other current alias IS a key of the map -- equivalently, a current
      alias is a key if and only if it is not the designated one;
    * the value assigned to the alias at ordinal position ``pos`` is the fresh
      alias generated for that position, so distinct positions get distinct
      values (the map is injective);
    * the map's KEY set and VALUE set are DISJOINT (no current alias equals any
      assigned value).

  Disjointness of keys and values is the well-formedness condition the map must
  meet: it lets the map be applied so that each alias is rewritten exactly once.

Aliases are modelled as non-negative integers; a namespace n occupies the
integer region at and above ``n * BASE``, and the current aliases are required
to live strictly below the target namespace's floor (mapping.md §2). The fresh
value for ordinal position ``pos`` is ``new_ns * BASE + pos``. The construction
returns, per ordinal position, the fresh value for that position and a flag
marking whether that position is a key (1) or the unmapped alias (0). The two
returned lists are positionally aligned with the input alias list.

The whole behaviour is modelled deeply (the construction is spelled out in the
impl region); there is no axiomatised callee. Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No axioms: the relabel construction is the behaviour under specification and
# is spelled out deeply in the impl region. There is no unchanged opaque callee
# to axiomatise.
# axioms-end


# pure-start
@Pure
def BASE() -> int:
    """Per-namespace alias capacity: a namespace n occupies the integer region
    [n*BASE, (n+1)*BASE), so distinct namespaces never collide."""
    return 1000


@Pure
def floor_of(ns: int) -> int:
    """The lowest integer alias belonging to namespace ``ns``."""
    Requires(ns >= 0)
    Ensures(Result() == ns * BASE())
    Ensures(Result() >= 0)
    return ns * BASE()


@Pure
def fresh_alias(new_ns: int, pos: int) -> int:
    """The fresh alias generated for the source at ordinal position ``pos`` in
    the new namespace ``new_ns``."""
    Requires(new_ns >= 0)
    Requires(0 <= pos and pos < BASE())
    # A fresh alias lives in new_ns: it sits at or above that namespace's floor.
    Ensures(Result() == new_ns * BASE() + pos)
    Ensures(Result() >= floor_of(new_ns))
    return new_ns * BASE() + pos
# pure-end


def disjoint_by_floor(below: List[int], above: List[int], f: int) -> None:
    """Lemma: if every element of `below` is < f and every element of `above`
    is >= f, then no element of `below` equals any element of `above`. Pure
    arithmetic; carries the disjointness of the source and target alias sets."""
    Requires(Acc(list_pred(below), 1 / 4))
    Requires(Acc(list_pred(above), 1 / 4))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(below),
                                             below[k] < f), [[below[k]]])))
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                             above[j] >= f), [[above[j]]])))
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(below), 1 / 4))
    Ensures(Acc(list_pred(above), 1 / 4))
    Ensures(Forall(int, lambda k: Forall(int, lambda j: (
            Implies(0 <= k and k < len(below) and 0 <= j and j < len(above),
                    below[k] != above[j])))))
    k = 0
    while k < len(below):
        # invariants-start
        Invariant(Acc(list_pred(below), 1 / 4))
        Invariant(Acc(list_pred(above), 1 / 4))
        Invariant(0 <= k and k <= len(below))
        Invariant(Forall(int, lambda kk: (Implies(0 <= kk and kk < len(below),
                                                   below[kk] < f), [[below[kk]]])))
        Invariant(Forall(int, lambda j: (Implies(0 <= j and j < len(above),
                                                  above[j] >= f), [[above[j]]])))
        # For every source already processed, it is below f, hence below every
        # target (each >= f), so it differs from each.
        Invariant(Forall(int, lambda kk: Forall(int, lambda j: (
                Implies(0 <= kk and kk < k and 0 <= j and j < len(above),
                        below[kk] != above[j])))))
        Invariant(MustTerminate(len(below) - k + 1))
        # invariants-end
        k = k + 1


def build_relabel_map(aliases: List[int], new_ns: int,
                      excluded: int) -> Tuple[List[int], List[int]]:
    # pre-conditions-start
    # `aliases` is the ordered list of current aliases (the map's potential
    # keys), each a well-formed encoding; read-only.
    Requires(Acc(list_pred(aliases), 1 / 2))
    Requires(new_ns >= 0)
    # The current aliases each fit one ordinal slot, and are well-formed.
    Requires(len(aliases) <= BASE())
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                             aliases[k] >= 0), [[aliases[k]]])))
    # Every current alias lives strictly below the target namespace's floor.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                            aliases[k] < floor_of(new_ns)),
                                     [[aliases[k]]])))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(aliases), 1 / 2))
    # Two positionally-aligned outputs: `targets[pos]` is the value assigned to
    # the alias at `pos`, and `is_source[pos]` is 1 iff that position is a key
    # of the map (0 iff it is the designated unmapped alias).
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[1])))
    Ensures(len(Result()[0]) == len(aliases))
    Ensures(len(Result()[1]) == len(aliases))
    # A current alias is a key IFF it is not the designated alias: the
    # designated alias is left unmapped, every other current alias is a key.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
            (Result()[1][k] == 1) == (aliases[k] != excluded)),
            [[Result()[1][k]]])))
    # The value at ordinal position `j` is the fresh value generated for that
    # position. Distinct positions therefore receive distinct values, so the
    # map is injective (no two current aliases collapse onto one value).
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(aliases) and j < BASE(),
            Result()[0][j] == fresh_alias(new_ns, j)),
            [[Result()[0][j]]])))
    # Every produced value lives in the target namespace (at or above its
    # floor), while every current alias lives strictly below it.
    Ensures(Forall(int, lambda j: (Implies(0 <= j and j < len(aliases),
            Result()[0][j] >= floor_of(new_ns)),
            [[Result()[0][j]]])))
    # Hence the map's KEY set and VALUE set are DISJOINT: no current alias
    # equals any produced value, so applying the map rewrites each alias exactly
    # once (the map's well-formedness condition).
    Ensures(Forall(int, lambda k: Forall(int, lambda j: (
            Implies(0 <= k and k < len(aliases) and 0 <= j and j < len(Result()[0]),
                    aliases[k] != Result()[0][j])))))
    # post-conditions-end
    # impl-start
    targets = []  # type: List[int]
    is_source = []  # type: List[int]
    pos = 0
    while pos < len(aliases):
        # invariants-start
        Invariant(Acc(list_pred(aliases), 1 / 2))
        Invariant(Acc(list_pred(targets)))
        Invariant(Acc(list_pred(is_source)))
        Invariant(0 <= pos and pos <= len(aliases))
        Invariant(len(aliases) <= BASE())
        Invariant(len(targets) == pos)
        Invariant(len(is_source) == pos)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                  aliases[k] >= 0), [[aliases[k]]])))
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < len(aliases),
                                                 aliases[k] < floor_of(new_ns)),
                                          [[aliases[k]]])))
        # Each produced target so far is the fresh alias for its position...
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                targets[j] == fresh_alias(new_ns, j))))
        # ...hence lives in the fresh namespace...
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < pos,
                targets[j] >= floor_of(new_ns))))
        # ...and the source flag records exactly "not the kept alias".
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < pos,
                (is_source[k] == 1) == (aliases[k] != excluded))))
        Invariant(MustTerminate(len(aliases) - pos + 1))
        # invariants-end
        t = fresh_alias(new_ns, pos)
        targets.append(t)
        Assert(targets[pos] == t)
        Assert(targets[pos] >= floor_of(new_ns))
        if aliases[pos] != excluded:
            is_source.append(1)
        else:
            is_source.append(0)
        Assert((is_source[pos] == 1) == (aliases[pos] != excluded))
        pos = pos + 1
    # Every source lives below the fresh floor and every target at or above it,
    # so no source equals any target: the relabel map's keys and values are
    # disjoint. The disjoint_by_floor lemma carries this from the two facts.
    Assert(pos == len(aliases) and len(targets) == len(aliases))
    disjoint_by_floor(aliases, targets, floor_of(new_ns))
    return targets, is_source
    # impl-end
