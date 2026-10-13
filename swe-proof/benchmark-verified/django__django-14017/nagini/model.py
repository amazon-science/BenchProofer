"""Twin-artifact model for django__django-14017.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A logical-filter container combines itself with another operand under a
  boolean connector (conjunction or disjunction). The combination must accept
  an operand that is EITHER another container of the same kind OR any object
  that is itself usable directly as a boolean filter condition (a
  boolean-valued operand) — the two are interchangeable as boolean operands and
  the combination is therefore symmetric on such a pair. Only an operand that is
  neither — one that is not a same-kind container AND is not usable as a boolean
  filter condition — is rejected, with a single uniform type-rejection failure
  to the caller.

  When the operand is acceptable, the combination returns normally. The empty
  container is the identity element of both connectors: combining an empty
  operand yields a copy of the container, and combining into an empty container
  yields a copy of the operand. When both sides are non-empty the result is a
  fresh container carrying the requested connector with both operands joined
  under it. The connector of the merged result is exactly the requested one.

  The behaviour pinned here is the ACCEPTANCE decision: an operand that is
  usable directly as a boolean filter condition must be accepted (no rejection)
  exactly as a same-kind container is, and only an operand that is neither a
  same-kind container nor a boolean filter condition is rejected. Whether the
  connector is conjunction or disjunction does not change which operands are
  accepted.

The operand is modelled abstractly by its observable predicates — whether it is
a same-kind container, whether it is usable directly as a boolean filter
condition, and whether it is empty — together with the calling container's own
emptiness; the discriminating observable is purely WHICH outcome the
combination produces (reject vs. which acceptance branch), not the operands'
internal data. The uniform type-rejection failure is a user-defined exception
class (a builtin exception in an `Exsures` crashes the Nagini translator). The
combination outcome is modelled as a small result object tagging the branch
taken and the connector it carries.

The combination must actually DELIVER its outcome — return or raise — on every
input: a total-correctness obligation, carried as ``MustTerminate`` in the
precondition. Nagini checks partial correctness by default, so without this
obligation a diverging body would satisfy every postcondition vacuously; the
real combination is bounded, loop-free work that always answers.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class OperandTypeRejected(Exception):
    """The single uniform type-rejection failure the combination surfaces to its
    caller whenever the operand is neither a same-kind container nor an operand
    usable directly as a boolean filter condition. User-defined stand-in for the
    type-rejection the desired behaviour requires (a builtin exception in an
    `Exsures` crashes the Nagini translator; mapping.md §2)."""
    pass


class Combined:
    """Observable outcome of an accepted combination (mapping.md §2):

      * ``branch`` tags which acceptance branch produced the result —
        0: the operand was empty, so the result is a copy of the container;
        1: the container was empty (operand non-empty), so the result is a copy
           of the operand;
        2: both sides non-empty, so the result is a fresh container joining both
           operands under the requested connector.
      * ``connector`` is the boolean connector carried by the result. For a
        branch-2 merge it is EXACTLY the requested connector; the identity
        branches carry the copied side's own connector (left abstract here)."""

    def __init__(self, branch: int, connector: int) -> None:
        # Terminates: field initialisation is straight-line work; measure 1
        # lets any caller holding MustTerminate(2) construct a result without
        # leaking its own obligation.
        Requires(MustTerminate(1))
        Requires(0 <= branch and branch <= 2)
        Ensures(Acc(self.branch) and Acc(self.connector))
        Ensures(self.branch == branch and self.connector == connector)
        self.branch = branch          # type: int
        self.connector = connector    # type: int


# axioms-start
# (no axiomatized callee: the changed function reads only its operands'
#  observable predicates — same-kind-container test, the boolean-operand test,
#  and emptiness — all modelled abstractly. The downstream identity/merge
#  branches are modelled directly, not via an unchanged library callee.)
# axioms-end


# pure-start
# (no module-level pure helpers required: the combination's decision is stated
#  inline over the operands' boolean observables.)
# pure-end


def combine(other_is_container: bool, other_is_boolean_operand: bool,
            other_empty: bool, self_empty: bool, conn: int) -> Combined:
    # pre-conditions-start
    # The operand and the calling container are characterised by their
    # observable predicates (plain booleans, no heap permission needed):
    #   other_is_container       — the operand is another same-kind container;
    #   other_is_boolean_operand — the operand is usable directly as a boolean
    #                              filter condition (a boolean-valued operand);
    #   other_empty              — the operand is empty (its falsy/identity form);
    #   self_empty               — the calling container is empty.
    # `conn` is the requested boolean connector (an opaque tag).
    # TOTALITY: the combination must actually deliver its outcome (return or
    # raise) on every input. Nagini is a partial-correctness verifier by
    # default, so without this obligation a diverging body (e.g. an endless
    # loop on an accepted branch) would satisfy every postcondition vacuously;
    # the real combination is bounded, loop-free work that always answers.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # ACCEPTANCE: a normal return is reachable for EXACTLY the acceptable
    # operands — a same-kind container OR an operand usable directly as a
    # boolean filter condition. An operand that is neither must NOT return
    # normally.
    Ensures(other_is_container or other_is_boolean_operand)
    # The branch taken is determined by the emptiness observables, identically
    # for either connector: an empty operand -> container copy (branch 0); else
    # an empty container -> operand copy (branch 1); else a merge (branch 2).
    Ensures(Acc(Result().branch) and Acc(Result().connector))
    Ensures(0 <= Result().branch and Result().branch <= 2)
    Ensures(Implies(other_empty, Result().branch == 0))
    Ensures(Implies(not other_empty and self_empty, Result().branch == 1))
    Ensures(Implies(not other_empty and not self_empty, Result().branch == 2))
    # The merge carries EXACTLY the requested connector (pins the result to the
    # caller-supplied connector, not an arbitrary tag).
    Ensures(Implies(Result().branch == 2, Result().connector == conn))
    # REJECTION: an operand that is neither a same-kind container nor usable as a
    # boolean filter condition is surfaced as the uniform type-rejection, and
    # ONLY then.
    Exsures(OperandTypeRejected, not other_is_container and not other_is_boolean_operand)
    # post-conditions-end
    # impl-start
    if not (other_is_container or other_is_boolean_operand):
        raise OperandTypeRejected()

    # If the operand is empty, ignore it and just use the container (a copy).
    if other_empty:
        return Combined(0, conn)
    # Or if the container is empty, ignore it and just use the operand (a copy).
    elif self_empty:
        return Combined(1, conn)

    # Both sides non-empty: a fresh container under the requested connector,
    # joining the container and the operand.
    obj = Combined(2, conn)
    return obj
    # impl-end
