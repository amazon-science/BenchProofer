"""Twin-artifact model for sphinx-doc__sphinx-9673.

Behaviour under specification (stated as desired behaviour, not as an edit):

When type-hint information is folded into an already-rendered description, the
routine decides whether to emit a return-type entry. Whether the return value
carries a textual description is read off the description fields already
present, via the classification of clause (1): a return value that the
description documents is one whose type must end up shown.

  (1) Given the collection of existing description fields, the return value is
      considered to HAVE a textual description exactly when at least one field
      is classified as describing the return value. It is considered to ALREADY
      HAVE a declared type exactly when at least one field is classified as
      declaring the return type.

  (2) A fresh return-type entry is emitted exactly when all three hold: the
      object carries a return annotation, the return value has a textual
      description (clause 1), and it does not already have a declared type.

Independently, when iterating the annotated names to back-fill parameter types,
a name that stands for the return value is skipped: it is not a parameter, and
the return value is handled by clause (2).

Type abstraction: each existing field is reduced to an integer "kind" code
determined by its leading token, and the description fields are carried by a
read-only `List[int]` of these codes. Codes 2 and 3 are the kinds classified as
describing the return value; code 4 is the kind classified as declaring the
return type; any other code is a field that does not bear on the return
decision. `return_annotated` carries whether a return annotation exists. The
name carriers `return_key_a` / `return_key_b` are the identifiers that stand for
the return value. The two classification predicates are front-recursive pure
sequence folds.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. The field classification and the return decision are pure
# structural logic, modelled deeply (`has_return_description` /
# `has_return_type`). The leading-token split of each field name is upstream of
# the modelled decision and is not consumed here.
# axioms-end


# pure-start
@Pure
def has_return_description(kinds: PSeq[int]) -> bool:
    """True iff the field collection contains a field classified as describing
    the return value -- code 2 or code 3. Front-recursive so a single unfold is
    available per loop step; uniformly false on the empty collection."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 2 or kinds[0] == 3 or has_return_description(kinds.drop(1))


@Pure
def has_return_type(kinds: PSeq[int]) -> bool:
    """True iff the field collection contains a field classified as declaring
    the return type (code 4). Front-recursive; uniformly false on the empty
    collection."""
    if len(kinds) == 0:
        return False
    return kinds[0] == 4 or has_return_type(kinds.drop(1))
# pure-end


def augment_return_typefield(field_kinds: List[int], return_annotated: bool) -> bool:
    # pre-conditions-start
    # The existing description fields are read-only: fractional permission,
    # required AND ensured.
    Requires(Acc(list_pred(field_kinds), 1 / 2))
    # The emission decision below is claimed of EVERY run, not only of the runs
    # that reach a return: for any collection of existing description fields the
    # routine must reach the decision in finitely many steps. Level 2 leaves
    # room strictly below it for the obligations of whatever a body calls.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(field_kinds), 1 / 2))
    # A fresh return-type entry is emitted exactly when: a return annotation
    # exists, the return value has a textual description, and it does not
    # already carry a declared type. Every field code classified as describing
    # the return value contributes to the description alike.
    Ensures(Result() == (return_annotated and
                         has_return_description(ToSeq(field_kinds)) and
                         not has_return_type(ToSeq(field_kinds))))
    # post-conditions-end
    # impl-start
    described = False
    typed = False
    i = len(field_kinds)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(field_kinds), 1 / 2))
        Invariant(0 <= i and i <= len(field_kinds))
        Invariant(described == has_return_description(ToSeq(field_kinds).drop(i)))
        Invariant(typed == has_return_type(ToSeq(field_kinds).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = field_kinds[i - 1]
        Assert(ToSeq(field_kinds).drop(i - 1)[0] == c)
        Assert(ToSeq(field_kinds).drop(i - 1).drop(1) == ToSeq(field_kinds).drop(i))
        if c == 2 or c == 3:
            # a field classified as describing the return value
            described = True
        elif c == 4:
            # a field classified as declaring the return type
            typed = True
        i = i - 1
    if return_annotated:
        if described and not typed:
            return True
    return False
    # impl-end


def name_is_return_key(name: int, return_key_a: int, return_key_b: int) -> bool:
    # pre-conditions-start
    # `return_key_a`/`return_key_b` are the identifiers that stand for the
    # return value; all three carriers are scalars (no permission).
    # The answer below is likewise claimed of EVERY run: the routine must decide
    # in finitely many steps whether the name it was handed stands for the
    # return value. A level above the emission decision, so a body here may
    # consult that decision and still sit strictly above its obligation.
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    # A name that stands for the return value is the one name skipped when
    # back-filling parameter types.
    Ensures(Result() == (name == return_key_a or name == return_key_b))
    # post-conditions-end
    # impl-start
    if name == return_key_a or name == return_key_b:
        return True
    return False
    # impl-end
