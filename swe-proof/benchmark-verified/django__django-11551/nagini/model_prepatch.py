"""Twin-artifact model for django__django-11551.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A startup validator inspects one entry that a presentation list declares it
  wants to display for a model. The entry is valid (produces no complaint) when
  it can be resolved to something displayable, and otherwise produces exactly
  one diagnostic. There are two distinct diagnostics:

    * a "not-resolvable" complaint (call it the E108 code), meaning the entry
      names nothing the model knows about; and
    * a "wrong-kind" complaint (call it the E109 code), meaning the entry
      resolves to a relation that cannot be displayed in a single column.

  The entry resolves successfully in any of these independent ways, checked in
  order, and as soon as one succeeds the entry is accepted with no further work:

    (1) the entry is itself directly invokable;
    (2) the entry names an attribute the presenter object itself carries;
    (3) the entry names a structural field declared on the model (a metadata
        field lookup that either yields a field or reports the field absent); or
    (4) the entry names an attribute reachable on the model class (a plain
        attribute lookup that either yields a value or reports it absent).

  The required behaviour:

    * If (1) or (2) holds, the entry is accepted (no diagnostic), and none of
      the later resolution steps are even attempted.
    * Otherwise the structural-field lookup (3) is attempted FIRST. Only if it
      reports the field absent is the attribute lookup (4) attempted. The
      not-resolvable complaint (E108) is produced if AND ONLY IF the structural
      lookup reports absent AND the attribute lookup also reports absent — i.e.
      a single failed structural lookup must NOT by itself produce a complaint
      while an attribute is still reachable, and the unreachability of the
      attribute must NOT by itself produce a complaint while a structural field
      exists.
    * If EITHER lookup yields something (a field from (3) or a value from (4)),
      that resolved object is examined: if it is a non-displayable relation the
      wrong-kind complaint (E109) is produced; otherwise the entry is accepted.
      The wrong-kind examination applies equally to the object obtained from (3)
      and to the object obtained from (4).

The two early predicates and the two lookups are unchanged opaque primitives.
The directly-invokable test and the presenter-attribute test are pure boolean
decisions. Each lookup is modelled by a pair: a boolean "reports absent" flag
and, when it does not report absent, a boolean "is a non-displayable relation"
flag for the object it yields. The diagnostic produced is reported as an
integer code: 0 = accepted (no diagnostic), 108 = not-resolvable, 109 =
wrong-kind.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no @ContractOnly axioms are consumed: the unchanged primitives this routine
#  consults — the invokable test, the presenter-attribute test, the structural
#  field lookup, and the attribute lookup — are each reduced to the boolean
#  observation they produce, supplied as parameters. The decision logic over
#  those observations is the changed behaviour and is modelled deeply below.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def check_display_item(
        is_invokable: bool,
        is_presenter_attr: bool,
        structural_absent: bool,
        structural_is_relation: bool,
        attribute_absent: bool,
        attribute_is_relation: bool) -> int:
    # pre-conditions-start
    # No heap state is touched; the routine is a pure decision over the
    # observations of the unchanged primitives.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly one of the three diagnostic codes.
    Ensures(Result() == 0 or Result() == 108 or Result() == 109)

    # (A) Directly-invokable or a presenter attribute => accepted, with NO later
    #     resolution attempted (so the later observations are irrelevant).
    Ensures(Implies(is_invokable or is_presenter_attr, Result() == 0))

    # (B) The not-resolvable complaint is produced IFF neither early acceptance
    #     holds AND BOTH lookups report absent. A single absent lookup must not
    #     on its own yield this complaint while the other lookup still resolves.
    Ensures((Result() == 108) ==
            (not (is_invokable or is_presenter_attr)
             and structural_absent and attribute_absent))

    # (C) When neither early acceptance holds and the STRUCTURAL lookup yields a
    #     field, that field decides the verdict: wrong-kind iff it is a
    #     non-displayable relation, else accepted. (The attribute lookup is not
    #     consulted in this case.)
    Ensures(Implies(not (is_invokable or is_presenter_attr) and not structural_absent,
                    Result() == (109 if structural_is_relation else 0)))

    # (D) When neither early acceptance holds, the structural lookup reports
    #     absent, but the ATTRIBUTE lookup yields a value, THAT value decides the
    #     verdict equally: wrong-kind iff it is a non-displayable relation, else
    #     accepted. (This is the path that must NOT collapse to the
    #     not-resolvable complaint.)
    Ensures(Implies(not (is_invokable or is_presenter_attr)
                    and structural_absent and not attribute_absent,
                    Result() == (109 if attribute_is_relation else 0)))
    # post-conditions-end
    # impl-start
    # Pre-patch (buggy) skeleton: the structural-field lookup is only attempted
    # when the attribute is reachable; if the attribute lookup reports absent
    # the routine emits the not-resolvable complaint WITHOUT first trying the
    # structural lookup. So a field reachable only via the structural lookup
    # (attribute unreachable) is wrongly rejected.
    if is_invokable:
        return 0
    if is_presenter_attr:
        return 0
    if not attribute_absent:
        if structural_absent:
            return 0
        if structural_is_relation:
            return 109
        return 0
    return 108
    # impl-end
