"""Twin-artifact model for sphinx-doc__sphinx-9698.

Behaviour under specification (stated as desired behaviour, not as an edit):

A class member, identified by its bare member name together with its qualifying
class name, is given a one-line index label. The member is classified by a
single descriptor selecting one of four mutually-exclusive roles. The label is
built by joining, in order:

  (1) the member name;
  (2) an empty-call marker `()` -- present for every role that denotes a
      CALLABLE member, and ABSENT for the one role that denotes a NON-callable
      attribute-like member;
  (3) a constant qualifier group ` (`, the qualifying class name, a single
      space, a role word, and a closing `)`.

The discriminating behaviour: the empty-call marker `()` follows the member name
for every callable role, and is omitted for the single non-callable role (a
value-like member that is read, never invoked). The qualifier group is otherwise
identical in shape across all roles and always names the qualifying class.

Type abstraction (refinement.md / mapping.md): each name is a `List[int]` of
Unicode code points (Nagini bans `str` indexing); the specification is carried
over `PSeq[int]`. The role descriptor is an integer selector. The four role
words and the structural separators are constant code-point sequences.

Label construction is a bounded computation (one step per name code point plus
constant-length literals) and MUST return its label — a total-correctness
obligation, carried as MustTerminate in the precondition. Nagini is a
partial-correctness verifier by default, so without this obligation a
non-terminating implementation (e.g. an endless loop that never returns)
satisfies every value postcondition vacuously yet would hang the index build
(and the F2P test) forever; the real labeller always returns.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# No consumed axioms. Translation lookup of the label template is the identity
# on the untranslated (reference) template, and the per-placeholder substitution
# of the member/class names is modelled deeply by sequence concatenation. There
# is no opaque callee whose Ensures the proof relies on.
# axioms-end


# pure-start
@Pure
def call_marker() -> PSeq[int]:
    # the empty-call marker '()'
    return PSeq(40, 41)


@Pure
def group_open() -> PSeq[int]:
    # the qualifier-group opening ' ('
    return PSeq(32, 40)


@Pure
def role_suffix(option: int) -> PSeq[int]:
    """The role word, with its leading space and trailing ')', for the role
    selected by `option`: 0 -> ' method)', 1 -> ' class method)',
    2 -> ' property)', 3 -> ' static method)'. The selector 2 is the single
    non-callable role."""
    if option == 1:
        # ' class method)'
        return PSeq(32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41)
    if option == 2:
        # ' property)'
        return PSeq(32, 112, 114, 111, 112, 101, 114, 116, 121, 41)
    if option == 3:
        # ' static method)'
        return PSeq(32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41)
    # ' method)'
    return PSeq(32, 109, 101, 116, 104, 111, 100, 41)


@Pure
def is_callable_role(option: int) -> bool:
    """True for every callable role; false for the single non-callable role
    (selector 2). The empty-call marker is emitted exactly for callable roles."""
    return option != 2


@Pure
def index_prefix(methname: PSeq[int], option: int) -> PSeq[int]:
    """The label prefix up to and including the qualifier-group opening: the
    member name, the empty-call marker iff callable, then ' ('. A proof helper
    for the class-name loop invariant."""
    if is_callable_role(option):
        return methname + call_marker() + group_open()
    return methname + group_open()


@Pure
def index_label(methname: PSeq[int], clsname: PSeq[int], option: int) -> PSeq[int]:
    """The full index label as a code-point sequence: the member name, then the
    empty-call marker iff the role is callable, then the qualifier group naming
    the class and the role word. Modelled deeply -- the label is the in-order
    concatenation of its parts, grounded in the actual name carriers."""
    return index_prefix(methname, option) + clsname + role_suffix(option)
# pure-end


def get_member_index_text(methname: List[int], clsname: List[int], option: int) -> List[int]:
    # pre-conditions-start
    # The member and class names are read-only inputs: fractional permission,
    # required AND ensured. `option` is the role selector (0..3).
    Requires(Acc(list_pred(methname), 1 / 2))
    Requires(Acc(list_pred(clsname), 1 / 2))
    Requires(0 <= option and option <= 3)
    # TERMINATION: the labeller must actually ANSWER — assembling the label is
    # a bounded computation (one step per name code point, plus constant
    # literals). Nagini is a partial-correctness verifier by default, so
    # without this obligation a non-terminating implementation (an endless
    # loop that never reaches its return) satisfies every value postcondition
    # vacuously; the real labeller always returns its label.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(methname), 1 / 2))
    Ensures(Acc(list_pred(clsname), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The label is exactly the in-order assembly of its parts.
    Ensures(ToSeq(Result()) == index_label(ToSeq(methname), ToSeq(clsname), option))
    # Structural discriminator, independent of the assembly helper: the label
    # begins with the member name, and the empty-call marker '()' follows the
    # member name EXACTLY for the callable roles -- i.e. it is present iff the
    # role is callable, and absent for the single non-callable role.
    Ensures(ToSeq(Result()).take(len(methname)) == ToSeq(methname))
    Ensures(is_callable_role(option) ==
            (ToSeq(Result()).drop(len(methname)).take(2) == call_marker()))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    j = 0
    while j < len(methname):
        # invariants-start
        Invariant(Acc(list_pred(methname), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= j and j <= len(methname))
        Invariant(ToSeq(result) == ToSeq(methname).take(j))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(methname) - j,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(methname) - j + 1))
        # invariants-end
        result.append(methname[j])
        j = j + 1
    Assert(ToSeq(result) == ToSeq(methname))
    # Pre-patch behaviour: the empty-call marker is emitted for EVERY role,
    # including the non-callable one -- the value-like member is labelled as if
    # it were invoked.
    result.append(40)
    result.append(41)
    result.append(32)
    result.append(40)
    k = 0
    while k < len(clsname):
        # invariants-start
        Invariant(Acc(list_pred(methname), 1 / 2))
        Invariant(Acc(list_pred(clsname), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(clsname))
        Invariant(ToSeq(result) ==
                  (ToSeq(methname) + call_marker() + group_open() + ToSeq(clsname).take(k)))
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(clsname) - k,
        # discharging MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(clsname) - k + 1))
        # invariants-end
        result.append(clsname[k])
        k = k + 1
    if option == 1:
        result = result + [32, 99, 108, 97, 115, 115, 32, 109, 101, 116, 104, 111, 100, 41]
    elif option == 2:
        result = result + [32, 112, 114, 111, 112, 101, 114, 116, 121, 41]
    elif option == 3:
        result = result + [32, 115, 116, 97, 116, 105, 99, 32, 109, 101, 116, 104, 111, 100, 41]
    else:
        result = result + [32, 109, 101, 116, 104, 111, 100, 41]
    return result
    # impl-end
