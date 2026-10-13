"""Twin-artifact model for pydata__xarray-4629.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A routine combines the per-source attribute mappings carried by several
  objects into a single attribute mapping for a combined object, according to a
  selected combination mode. Two of the modes are pinned here:

    * "drop" discards every attribute: the combined mapping is empty.

    * "override" adopts the leading source's attributes wholesale. The
      behaviour that matters: the combined mapping must be an INDEPENDENT
      object that merely has the same content as the leading source. A caller
      that subsequently mutates an entry of the combined mapping must NOT
      thereby change the leading source's mapping. In other words, the combined
      mapping is a copy of the leading source, not a shared reference to it.

  The consequence the specification pins down: after combining, mutating the
  result leaves every source's attribute mapping exactly as it was.

Modelling choices (Nagini fragment):
  * An attribute mapping is carried by its content sequence as a `List[int]`
    (the per-entry tokens of the mapping; the operation under specification
    cares about content equality and, decisively, OBJECT IDENTITY, both of
    which the list carrier models faithfully -- mapping.md §2). The collection
    of per-source mappings is the `List[List[int]]` argument `variable_attrs`.
  * The combination mode is an `int` token (`DROP`, `OVERRIDE`).
  * "independent copy" is expressed in separation-logic permissions: the
    read-only source keeps its fractional permission, while the result carries
    FULL permission on a DISTINCT object. A result that aliased the source
    could not hold full permission while the source retains half (they would
    sum past one) -- so the permission discipline forces a genuine copy.
  * The empty-source short-circuit and the conflict-resolving modes are
    unchanged and outside the modeled domain (precondition: at least one source
    mapping); they are not re-modelled here.

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

DROP = 0
OVERRIDE = 1


# axioms-start
# No consumed axioms. The combination is the behaviour under specification and
# is modelled deeply (the impl region spells out the per-entry copy and the
# empty mapping). The list operations it composes have ordinary Python
# semantics, validated out-of-band by axiom_check.py (G-AX) as an A-reference.
# axioms-end


# pure-start
# No pure helpers: the selection and the copy are spelled out in the impl
# region; their content/identity guarantees are the postconditions.
# pure-end


def combine_attrs(variable_attrs: List[List[int]], mode: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(variable_attrs), 1 / 2))
    # At least one source mapping is present (the modeled, non-trivial domain).
    Requires(len(variable_attrs) > 0)
    Requires(mode == DROP or mode == OVERRIDE)
    # The leading source mapping is read-only: fractional permission.
    Requires(Acc(list_pred(variable_attrs[0]), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(variable_attrs), 1 / 2))
    Ensures(len(variable_attrs) > 0)
    # The leading source's read-only permission is returned to the caller
    # unchanged -- it is never mutated, nor handed out as the result.
    Ensures(Acc(list_pred(variable_attrs[0]), 1 / 2))
    # The result is a freshly produced mapping: FULL permission on a new object.
    Ensures(Acc(list_pred(Result())))
    # Drop mode discards every attribute: the result mapping is empty.
    Ensures(Implies(mode == DROP, len(Result()) == 0))
    # Override mode: the result is a DISTINCT object from the leading source
    # (so the source's retained half-permission and the result's full
    # permission coexist -- impossible were they the same object) ...
    Ensures(Implies(mode == OVERRIDE, Result() is not variable_attrs[0]))
    # ... with the SAME content as the leading source (a faithful copy).
    Ensures(Implies(mode == OVERRIDE,
                    ToSeq(Result()) == ToSeq(variable_attrs[0])))
    # post-conditions-end
    # impl-start
    if mode == DROP:
        empty = []  # type: List[int]
        return empty
    # Pre-image skeleton: the leading source mapping is handed back directly,
    # as a shared reference rather than an independent copy.
    return variable_attrs[0]
    # impl-end
