"""Twin-artifact model for sympy__sympy-18189.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A solver computes the complete set of integer solution tuples of an equation.
  Its enumeration is governed by a boolean option `expand` (when True the solver
  enumerates the full family of solutions — sign and order variants included —
  rather than a single representative family). The public entry point also
  accepts a caller-chosen ordering of the unknowns. When that ordering differs
  from the solver's canonical ordering, the entry point re-derives the answer in
  the canonical ordering and then re-arranges every solution tuple's components
  into the caller's ordering (a single, injective relabelling applied to each
  solution).

  The behaviour that matters: re-arranging the components must NOT change which
  family of solutions is enumerated. The re-derivation that feeds the
  re-arrangement must be performed under the SAME `expand` option the caller
  requested, so the re-arranged answer is the relabelling of the very same
  complete solution family the canonical ordering would have produced.
  Re-ordering the unknowns is a relabelling of coordinates only; it must never
  silently collapse the enumerated family down to the un-expanded one.

Modelling choices (Nagini fragment):
  * The canonical solution family is a `PSeq[int]` of solution-tuple identity
    tokens — one entry per enumerated solution. Re-arranging a solution's
    components is an injective relabelling `relabel` on these tokens (a constant
    index permutation applied component-wise is, on the level the test observes,
    exactly an injective relabelling of solutions), so the re-arranged family is
    the element-wise `relabel` image of the canonical family. The tested
    behaviour observes the family as a set and the re-arrangement is the image
    of the canonical family under one constant bijection, so this carrier is
    faithful (mapping.md §2). Pure sequences carry no heap permission.
  * The option is a `bool`. The canonical solver is an unchanged callee
    `solve_family(expand)` — axiomatized: it is keyed on `expand`; its
    `expand=True` and `expand=False` families are deliberately NOT asserted
    equal (they differ in general — that is the whole point of the option).

No string indexing is used (Nagini bans it). Markers (machine-parsed) delimit
the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def solve_family(expand: bool) -> PSeq[int]:
    """The canonical-ordering solver (the unchanged callee the entry point
    re-invokes), as a sequence of solution-tuple identity tokens. Keyed on
    `expand` — the `True` and `False` families are NOT asserted equal (the
    option genuinely changes which family is enumerated). Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def relabel(token: int) -> int:
    """The single, injective re-arrangement applied to one solution when the
    caller's ordering of the unknowns differs from the canonical one. It is a
    bijection on solution identities (a coordinate relabelling), so it never
    merges two distinct solutions. Unchanged callee; provenance: mapping.md."""
# axioms-end


# pure-start
@Pure
def relabel_family(s: PSeq[int]) -> PSeq[int]:
    """The re-arranged family: each canonical solution is relabelled into the
    caller's ordering, in order. Front-recursive over `s` (peel the head,
    recurse on the tail), so a single unfold is available per element."""
    Ensures(len(Result()) == len(s))
    if len(s) == 0:
        return PSeq(0).take(0)
    return PSeq(relabel(s[0])) + relabel_family(s.drop(1))
# pure-end


def reorder_solution_family(expand: bool) -> PSeq[int]:
    # pre-conditions-start
    # pre-conditions-end
    # post-conditions-start
    # The re-arranged answer is the relabelling of the canonical family that the
    # SAME `expand` option produces. Re-ordering the unknowns never changes
    # which family is enumerated — it is enumerated under the caller's `expand`,
    # then relabelled component-wise. A derivation that ignores `expand` and uses
    # a default option cannot satisfy this when `expand` requests the full family.
    Ensures(Result() == relabel_family(solve_family(expand)))
    Ensures(len(Result()) == len(solve_family(expand)))
    # post-conditions-end
    # impl-start
    # Re-derive the canonical family under the caller's option, then re-arrange
    # every solution into the caller's ordering.
    canonical = solve_family(expand)  # type: PSeq[int]
    result = relabel_family(canonical)  # type: PSeq[int]
    return result
    # impl-end
