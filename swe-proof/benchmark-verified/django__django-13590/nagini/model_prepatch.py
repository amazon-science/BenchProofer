"""Twin-artifact model for django__django-13590.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When a lookup argument is a sequence of sub-values, each sub-value is
  resolved independently and a NEW container of the SAME kind is produced from
  the resolved sub-values. Container kinds differ in HOW their builder accepts
  the elements, and crucially in WHETHER the builder even succeeds:

    * a plain positional sequence kind, whose builder consumes a single
      iterable holding all the elements and succeeds; and
    * a field-named sequence kind, whose builder instead takes the elements as
      SEPARATE positional arguments (one per field). Handed the elements as
      separate positional arguments it succeeds and produces a well-formed
      container; handed a single iterable instead it does NOT produce a
      well-formed container at all — the lone iterable would occupy just the
      first field, leaving the remaining required fields unfilled, so the
      construction FAILS rather than yielding a usable container.

  The reconstruction must, for EITHER kind, yield a WELL-FORMED container
  holding exactly the resolved sub-values, in order: its length equals the
  number of sub-values and its i-th element is the independent resolution of the
  i-th input sub-value. Producing a well-formed container is the load-bearing
  requirement: for a field-named kind the elements must be supplied one per
  field (spread across the fields), never bundled into a single iterable
  argument, because only the per-field convention yields a well-formed container
  for such a kind — the single-iterable convention does not construct one.

The sequence of sub-values is modelled as a `List[int]` of opaque sub-value
identities. The unchanged per-element resolution (recursively resolving one
sub-value) is axiomatized as a deterministic pure callee `resolve_one`. The
container builder is an UNCHANGED callee too (the constructor of the container
kind): it is axiomatized as `build_container`. Its contract captures the effect
that distinguishes the two calling conventions — for a field-named kind only the
per-field convention constructs a well-formed container, the single-iterable
convention does not — by granting an unforgeable `well_formed_container` token
ONLY when the convention matches the kind. The reconstruction's own
postcondition REQUIRES that token, so a verifying reconstruction must route its
result through a successful (convention-matching) construction; it cannot return
a container the builder never well-formed. No callee under change is
axiomatized; the constructor contract is validated against the real Python
container semantics out-of-band (axiom_check.py / G-AX).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def resolve_one(sub_value: int) -> int:
    """Independent resolution of a single sub-value (the unchanged recursive
    resolution of one element of the sequence). Deterministic: the resolution
    of a sub-value depends only on the sub-value. The unchanged callee the
    reconstruction maps over; never the operation under change. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """


# Abstract token marking a container that was PRODUCED BY a SUCCESSFUL builder
# call for its kind: a capability the builder grants on its output and that
# nothing else can fabricate. Its arguments record the container contents and
# the kind it was built for. The reconstruction's result must hold this token
# for the kind it claims to rebuild, so the result can only be a container the
# builder actually well-formed for that kind — a builder call under the
# convention that does not match a field-named kind never grants it (the
# construction does not succeed). Provenance + executable soundness check:
# mapping.md / axiom_check.py.
@ContractOnly
@Predicate
def well_formed_container(contents: PSeq[int], field_named: bool) -> bool:
    pass


@ContractOnly
def build_container(elems: List[int], field_named: bool, spread: bool) -> List[int]:
    """Container-builder callee (the UNCHANGED constructor of the container
    kind). It is invoked under one of two conventions:

      * `spread == False`: the elements are handed to the builder as a SINGLE
        iterable (the constructor receives one positional argument holding all
        the elements);
      * `spread == True`: the elements are SPREAD one-per-field (the constructor
        receives the elements as separate positional arguments).

    The construction is only WELL-FORMED — actually yielding a usable container
    holding the elements — when the convention matches the container kind: a
    plain kind well-forms from the single iterable; a field-named kind well-forms
    only from the spread, because the single iterable would leave its required
    fields unfilled. That match is `field_named == spread`, which is the
    builder's precondition for a well-formed construction. On a well-formed
    construction it returns a fresh container holding exactly the elements, in
    order, AND grants the `well_formed_container` token on its output for this
    kind. Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(Acc(list_pred(elems), 1 / 2))
    # A well-formed construction requires the convention to match the kind. A
    # field-named kind handed a single (un-spread) iterable does not well-form a
    # container (the lone iterable cannot fill the separate fields).
    Requires(field_named == spread)
    Requires(MustTerminate(2))
    Ensures(Acc(list_pred(elems), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The well-formed container holds exactly the elements, in order.
    Ensures(len(Result()) == len(elems))
    Ensures(ToSeq(Result()) == Old(ToSeq(elems)))
    # ...and is marked as a builder-produced well-formed container for this kind.
    Ensures(well_formed_container(ToSeq(Result()), field_named))
# axioms-end


# pure-start
@Pure
def resolved_seq(s: PSeq[int]) -> PSeq[int]:
    """The element-wise resolution of a whole sequence: each element replaced by
    its independent resolution. Front-recursive so a single unfold is available
    to callers at each loop step. Length-preserving (one resolved element per
    input element)."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(resolve_one(s[0])) + resolved_seq(s.drop(1))
# pure-end


def resolve_sequence(value: List[int], field_named: bool) -> List[int]:
    # pre-conditions-start
    # The input sequence is read-only; only fractional permission is needed and
    # returned (the spec may not be satisfied by overwriting the input).
    Requires(Acc(list_pred(value), 1 / 2))
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(value), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The reconstruction holds exactly the resolved sub-values, in order, for
    # BOTH container kinds: same length and element-wise independent resolution.
    Ensures(len(Result()) == len(value))
    Ensures(ToSeq(Result()) == resolved_seq(ToSeq(value)))
    # The result must be a WELL-FORMED container the builder actually produced
    # for THIS kind — it holds the token the builder grants only on a successful
    # (convention-matching) construction. For a field-named kind that means the
    # result went through the per-field (spread) construction; a result the
    # builder never well-formed (e.g. one assembled without going through a
    # successful builder call for this kind) lacks the token. This is the
    # load-bearing clause: it cannot be discharged by value-equality alone,
    # because the elements are identical whether or not the field-named builder
    # would have succeeded — the discriminator is the construction effect.
    Ensures(well_formed_container(ToSeq(Result()), field_named))
    # post-conditions-end
    # impl-start
    resolved = []  # type: List[int]
    i = len(value)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(value), 1 / 2))
        Invariant(Acc(list_pred(resolved)))
        Invariant(0 <= i and i <= len(value))
        Invariant(len(resolved) == len(value) - i)
        Invariant(ToSeq(resolved) == resolved_seq(ToSeq(value).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        e = value[i - 1]
        Assert(ToSeq(value).drop(i - 1)[0] == e)
        Assert(ToSeq(value).drop(i - 1).drop(1) == ToSeq(value).drop(i))
        resolved = [resolve_one(e)] + resolved
        i = i - 1
    # Pre-patch reconstruction: ALWAYS hand the builder the single iterable,
    # regardless of the container kind. For a field-named kind this is the
    # convention that does not match, so the construction is not well-formed.
    result = build_container(resolved, field_named, False)
    return result
    # impl-end
