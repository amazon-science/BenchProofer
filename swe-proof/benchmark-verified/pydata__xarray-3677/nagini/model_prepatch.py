"""Twin-artifact model for pydata__xarray-3677.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Combining a collection of two labelled operands into a single sequence of
  operands fit for the core combination routine. The core routine iterates the
  named entries of each operand, so every operand it receives MUST expose the
  named-entry interface (be "mapping-shaped"). The receiving operand already is
  mapping-shaped. The second operand may instead be "array-shaped": a single
  named value with no named-entry interface. The desired behaviour is that the
  produced operand sequence contains exactly the receiver followed by the second
  operand in mapping-shaped form, so that:

    * the sequence has the two operands, in order;
    * the receiver passes through unchanged as the first operand;
    * EVERY operand in the sequence is mapping-shaped (exposes named entries);
    * the second operand still carries the second input's single named value
      (its name and value are preserved), whatever shape that input arrived in;
    * neither operand is altered -- the entry each one carried on the way in is
      the entry it still carries once the sequence has been produced.

An array-shaped operand is normalised into the one-entry mapping-shaped operand
that carries the same name and value; a mapping-shaped operand passes through.
The two operands need not be different objects: the same mapping-shaped operand
may be supplied as both, and the produced sequence then holds it twice.

What the sequence is fit FOR is the core routine's own business: this operation
ends at the sequence, so whether the core can afterwards combine the operands it
receives -- and what it reports when it cannot -- is downstream of the behaviour
specified here and is not constrained by it.

Normalising an array-shaped operand is only DEFINED for some array-shaped
operands, and the sequence can be produced exactly when it is defined. An
array-shaped operand carries, besides its single entry, its own named label
entries -- the labels it holds for its axes; normalisation is undefined when the
entry's own name is also the name of one of those label entries, because the
one-entry mapping-shaped form would then have to hold two different things under
one name. On such an operand the
normalisation signals that it is undefined instead of producing an operand, and
the whole combination signals likewise -- no operand sequence is produced at all.
Neither operand is altered on that outcome either: reporting that no sequence
exists never involves rewriting an operand into the shape that makes such a
report apt.
Normalisation is likewise undefined for an unnamed array-shaped operand; that
case is excluded from this specification's domain by the precondition.

Operands are modelled as a minimal tagged object carrying only the touched
fields: a mapping-shaped flag, the single entry's name, its value, and whether
that name is also the name of one of the operand's own label entries (names and values
abstracted to ints; mapping.md gives the bijection). The normalisation of an
array-shaped operand to a mapping-shaped one is modelled deeply (`as_mapping`)
and validated == the real conversion callee out-of-band by axiom_check.py (G-AX),
not consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class NormalisationUndefined(Exception):
    # Signalled when an array-shaped operand has no one-entry mapping-shaped
    # form: its single entry's name is also the name of one of its own label
    # entries.
    pass


class Operand:
    # An operand to the combination routine.
    #   is_mapping        : exposes the named-entry interface the core needs
    #   name              : the single entry's name (-1 == unnamed)
    #   value             : the single entry's value
    #   name_is_own_label : `name` is also the name of one of this operand's own
    #                       label entries, so it has no one-entry mapping-shaped
    #                       form
    def __init__(self, is_mapping: bool, name: int, value: int,
                 name_is_own_label: bool) -> None:
        # level 1: the leaf obligation. `as_mapping` (level 6) and
        # `merge_method` (level 10) both construct Operands, so the
        # constructor's level must sit strictly below theirs, leaving them room
        # to discharge it. Without this, Nagini reports "Obligation leak check
        # failed. Callee __init__ might not take all unsatisfied obligations
        # from the caller." The body is straight-line: it terminates trivially.
        Requires(MustTerminate(1))
        self.is_mapping = is_mapping  # type: bool
        self.name = name              # type: int
        self.value = value            # type: int
        self.name_is_own_label = name_is_own_label  # type: bool
        Ensures(Acc(self.is_mapping) and Acc(self.name) and Acc(self.value)
                and Acc(self.name_is_own_label))
        Ensures(self.is_mapping == is_mapping)
        Ensures(self.name == name and self.value == value)
        Ensures(self.name_is_own_label == name_is_own_label)


# axioms-start
# (no consumed @ContractOnly axiom: the only callee the change introduces is the
#  array->mapping conversion, which is modelled DEEPLY as `as_mapping` below and
#  validated == the real conversion by axiom_check.py / G-AX as an A-reference.)
# axioms-end


# pure-start
@Pure
def is_array_shaped(o: Operand) -> bool:
    # An operand lacks the named-entry interface exactly when it is not
    # mapping-shaped.
    Requires(Acc(o.is_mapping, 1 / 8))
    return not o.is_mapping
# pure-end


def as_mapping(o: Operand) -> Operand:
    """Normalise an array-shaped operand into the one-entry mapping-shaped
    operand carrying the same name and value (deep model of the conversion
    callee; A-reference, G-AX-checked). Signals NormalisationUndefined on an
    array-shaped operand whose entry name is also the name of one of its own
    label entries, for which no such one-entry form exists."""
    # pre-conditions-start
    Requires(Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
             and Acc(o.name_is_own_label, 1 / 4))
    # the conversion is defined for a named array-shaped operand
    Requires(is_array_shaped(o))
    Requires(o.name >= 0)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
            and Acc(o.name_is_own_label, 1 / 4))
    Ensures(Acc(Result().is_mapping) and Acc(Result().name) and Acc(Result().value)
            and Acc(Result().name_is_own_label))
    # an operand is produced ONLY when the entry name is not also the name of one
    # of the operand's own label entries -- the returning path is exactly that case
    Ensures(not o.is_mapping and o.name >= 0)
    Ensures(not o.name_is_own_label)
    # the produced operand is mapping-shaped and carries the same single entry
    Ensures(Result().is_mapping)
    Ensures(Result().name == o.name and Result().value == o.value)
    # and its own name does not collide with a label entry name of itself
    Ensures(not Result().name_is_own_label)
    # the ONLY other outcome: the collision case signals that no one-entry
    # mapping-shaped form exists, and it is signalled exactly on that case
    Exsures(NormalisationUndefined,
            Acc(o.is_mapping, 1 / 4) and Acc(o.name, 1 / 4) and Acc(o.value, 1 / 4)
            and Acc(o.name_is_own_label, 1 / 4)
            and not o.is_mapping and o.name_is_own_label)
    # post-conditions-end
    # impl-start
    if o.name_is_own_label:
        raise NormalisationUndefined()
    res = Operand(True, o.name, o.value, False)
    return res
    # impl-end


def merge_method(receiver: Operand, other: Operand) -> List[Operand]:
    # pre-conditions-start
    Requires(Acc(receiver.is_mapping, 1 / 2) and Acc(receiver.name, 1 / 2)
             and Acc(receiver.value, 1 / 2) and Acc(receiver.name_is_own_label, 1 / 2))
    Requires(Acc(other.is_mapping, 1 / 2) and Acc(other.name, 1 / 2)
             and Acc(other.value, 1 / 2) and Acc(other.name_is_own_label, 1 / 2))
    # the receiver is already mapping-shaped (it is the dataset the method is on)
    Requires(receiver.is_mapping)
    # (the two operands need NOT be distinct objects: the same mapping-shaped
    #  operand may be supplied as both the receiver and the second operand)
    # a second operand lacking the named-entry interface is a named single value
    Requires(Implies(is_array_shaped(other), other.name >= 0))
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(receiver.is_mapping, 1 / 4) and Acc(receiver.name, 1 / 4)
            and Acc(receiver.value, 1 / 4) and Acc(receiver.name_is_own_label, 1 / 4))
    Ensures(Acc(other.is_mapping, 1 / 4) and Acc(other.name, 1 / 4)
            and Acc(other.value, 1 / 4) and Acc(other.name_is_own_label, 1 / 4))
    Ensures(Acc(list_pred(Result())))
    # the produced operand sequence has exactly the two operands, in order
    Ensures(len(Result()) == 2)
    # the receiver passes through unchanged as the first operand
    Ensures(Result()[0] is receiver)
    # EVERY operand reaching the core exposes the named-entry interface
    Ensures(Acc(Result()[0].is_mapping, 1 / 4) and Result()[0].is_mapping)
    Ensures(Acc(Result()[1].is_mapping, 1 / 4) and Result()[1].is_mapping)
    # the second operand still carries the second input's single named value
    Ensures(Acc(Result()[1].name, 1 / 4) and Acc(Result()[1].value, 1 / 4))
    Ensures(Result()[1].name == other.name and Result()[1].value == other.value)
    # NEITHER operand is altered: the second operand still carries, once the
    # sequence has been produced, exactly the entry it arrived with -- so the
    # preservation above cannot be met by rewriting the operand's own entry to
    # match whatever was produced, and (when the same operand was supplied as
    # both) the receiver's entry is equally untouched
    Ensures(other.is_mapping == Old(other.is_mapping))
    Ensures(other.name == Old(other.name) and other.value == Old(other.value))
    Ensures(other.name_is_own_label == Old(other.name_is_own_label))
    # an already-mapping-shaped second operand passes through UNCHANGED (the same
    # object), so no named entry it carries can be silently dropped: the result
    # must be produced from the actual second operand, not rebuilt from a subset
    # of it (see refinement.md B)
    Ensures(Implies(not Old(is_array_shaped(other)), Result()[1] is other))
    # a sequence is produced ONLY when an array-shaped second operand actually
    # has a one-entry mapping-shaped form -- the normalisation is not bypassed,
    # so its undefinedness is not concealed by rebuilding the operand instead
    Ensures(Implies(is_array_shaped(other), not other.name_is_own_label))
    # the ONLY other outcome: an array-shaped second operand whose entry name is
    # also the name of one of its own label entries yields NO operand sequence at
    # all, and that is signalled exactly on that case
    Exsures(NormalisationUndefined,
            Acc(receiver.is_mapping, 1 / 4) and Acc(receiver.name, 1 / 4)
            and Acc(receiver.value, 1 / 4) and Acc(receiver.name_is_own_label, 1 / 4)
            and Acc(other.is_mapping, 1 / 4) and Acc(other.name, 1 / 4)
            and Acc(other.value, 1 / 4) and Acc(other.name_is_own_label, 1 / 4)
            and not other.is_mapping and other.name_is_own_label
            # ... and the operands are as untouched on this outcome as on the other:
            # signalling that no sequence exists is not licence to edit an operand
            # into the shape that makes the signal look justified
            and other.is_mapping == Old(other.is_mapping)
            and other.name == Old(other.name) and other.value == Old(other.value)
            and other.name_is_own_label == Old(other.name_is_own_label))
    # post-conditions-end
    # impl-start
    second = other
    result = [receiver, second]  # type: List[Operand]
    return result
    # impl-end
