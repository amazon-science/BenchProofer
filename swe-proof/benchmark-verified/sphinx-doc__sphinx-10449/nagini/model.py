"""Twin-artifact model for sphinx-doc__sphinx-10449.

Behaviour under specification (stated as desired behaviour, not as an edit):

When type-hint information is rendered into a description-style field list and
the rendering target covers every annotation, a synthetic "return type" field
is appended for the documented object's return annotation under these rules:

  (1) A return-type field is appended exactly when the annotation set carries a
      return annotation AND the field list does not already declare a return
      type.

  (2) Documentation of a CONTAINER object (the kind whose body is itself a
      documented entity, e.g. the constructed thing rather than a plain
      callable) must NOT advertise a return type of "no value" (the textual
      annotation ``None``): for such an object, when the return annotation is
      exactly ``None``, no return-type field is appended. Every other return
      annotation, and every non-container object, still appends the field.

  (3) When a return-type field IS appended, its rendered content is the OBJECT'S
      OWN return annotation -- not the annotation of some other documented name.

The dispatch that selects rule (2) requests return-type suppression precisely
for the container object kind.

Strings (object kind, annotation text) are modelled as `List[int]` of Unicode
code points (Nagini bans `str` indexing); the existing field list is modelled
as a `List[int]` of per-field kind codes (a field that already declares a
return type is code 1, any other field is code 0). The pure sequence theory
`PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callees: the changed behaviour is the append decision and its
# rendered content, modelled deeply below. No @ContractOnly is consumed.)
# axioms-end


# pure-start
@Pure
def seq_class() -> PSeq[int]:
    # 'class' as Unicode code points
    return PSeq(99, 108, 97, 115, 115)


@Pure
def seq_none() -> PSeq[int]:
    # 'None' as Unicode code points
    return PSeq(78, 111, 110, 101)


@Pure
def is_return_field(code: int) -> bool:
    """A field already declares a return type iff its kind code is 1."""
    return code == 1


@Pure
def opt_seq(x: Optional[List[int]]) -> PSeq[int]:
    """The element sequence of an optional rendered field: its code points when
    a field is produced, the empty sequence when none is. Guards the None case
    so the spec can compare a produced field's content without indexing through
    None."""
    Requires(Implies(x is not None, Acc(list_pred(x), 1 / 4)))
    if x is None:
        return PSeq(0).take(0)
    return ToSeq(x)


@Pure
def has_return_field(fields: PSeq[int]) -> bool:
    """Whether the existing field list already declares a return type, i.e.
    some field is a return-type-declaring field. Front-recursive so a single
    unfold is available to callers."""
    if len(fields) == 0:
        return False
    return is_return_field(fields[0]) or has_return_field(fields.drop(1))


# pure-end


def suppress_for_kind(object_kind: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(object_kind), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(object_kind), 1 / 2))
    # Return-type suppression is requested exactly for the container object
    # kind (the one whose textual kind equals 'class').
    Ensures(Result() == (ToSeq(object_kind) == seq_class()))
    # post-conditions-end
    # impl-start
    return ToSeq(object_kind) == seq_class()
    # impl-end


def has_return_field_in(fields: List[int]) -> bool:
    # pre-conditions-start
    Requires(Acc(list_pred(fields), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    Ensures(Result() == has_return_field(ToSeq(fields)))
    # post-conditions-end
    # impl-start
    found = False
    i = len(fields)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(fields), 1 / 2))
        Invariant(0 <= i and i <= len(fields))
        Invariant(found == has_return_field(ToSeq(fields).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(ToSeq(fields).drop(i - 1)[0] == fields[i - 1])
        Assert(ToSeq(fields).drop(i - 1).drop(1) == ToSeq(fields).drop(i))
        if is_return_field(fields[i - 1]):
            found = True
        i = i - 1
    return found
    # impl-end


def append_return_type(fields: List[int], has_return: bool,
                       return_annotation: List[int],
                       suppress_void_return: bool) -> Optional[List[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(fields), 1 / 2))
    Requires(Acc(list_pred(return_annotation), 1 / 2))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(fields), 1 / 2))
    Ensures(Acc(list_pred(return_annotation), 1 / 2))
    # A return-type field is appended (Result is not None) exactly when there is
    # a return annotation, the list declares no return type yet, and we are not
    # suppressing a 'None' return type for a container object.
    Ensures(
        (Result() is not None)
        == (has_return
            and not has_return_field(ToSeq(fields))
            and not (suppress_void_return and ToSeq(return_annotation) == seq_none()))
    )
    # When a field IS appended, its content is exactly this object's own return
    # annotation (grounded in the input carrier, never some other name's text).
    Ensures(Implies(Result() is not None, Acc(list_pred(Result()))))
    Ensures(Implies(Result() is not None,
                    opt_seq(Result()) == ToSeq(return_annotation)))
    # post-conditions-end
    # impl-start
    no_return_field = not has_return_field_in(fields)
    Assert(no_return_field == (not has_return_field(ToSeq(fields))))
    if has_return and no_return_field:
        suppressed_none = ToSeq(return_annotation) == seq_none() and suppress_void_return
        if suppressed_none:
            return None
        # Render the field with the object's own return annotation as content.
        field = []  # type: List[int]
        j = 0
        while j < len(return_annotation):
            # invariants-start
            Invariant(Acc(list_pred(return_annotation), 1 / 2))
            Invariant(Acc(list_pred(field)))
            Invariant(0 <= j and j <= len(return_annotation))
            Invariant(ToSeq(field) == ToSeq(return_annotation).take(j))
            Invariant(not suppressed_none)
            Invariant(suppressed_none
                      == (ToSeq(return_annotation) == seq_none() and suppress_void_return))
            Invariant(MustTerminate(len(return_annotation) - j + 1))
            # invariants-end
            Assert(ToSeq(return_annotation).take(j + 1).drop(j)[0]
                   == return_annotation[j])
            Assert(ToSeq(return_annotation).take(j + 1)
                   == ToSeq(return_annotation).take(j) + PSeq(return_annotation[j]))
            field.append(return_annotation[j])
            j = j + 1
        Assert(ToSeq(return_annotation).take(len(return_annotation))
               == ToSeq(return_annotation))
        Assert(ToSeq(field) == ToSeq(return_annotation))
        Assert(has_return and no_return_field and not suppressed_none)
        return field
    return None
    # impl-end
