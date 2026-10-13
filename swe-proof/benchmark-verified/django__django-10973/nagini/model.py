"""Twin-artifact model for django__django-10973.

Behaviour under specification (stated as the desired behaviour, not as an edit):

  The database shell launcher makes the connection password available to the
  child process through a dedicated mechanism. The value exposed to the child
  for the password is the password sequence itself — element i of the exposed
  value is code point i of the input password, for every position — so the
  exposed value equals the input password and has the same length.

  The mechanism is populated (the exposed value is non-empty) exactly when the
  input password is non-empty.

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing); the specification is carried over `PSeq[int]` via `ToSeq`. The
returned `List[int]` is the value exposed to the child for the password; it is
populated (the mechanism is active) exactly when its length is positive, which
holds exactly when the input password is non-empty.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed axioms: the changed behaviour is modelled deeply — the exposed
# value is pinned to the input password element-wise. The proof consumes no
# @ContractOnly contract.)
# axioms-end


# pure-start
# pure-end


# impl-start
# (Proof/impl-only region, elided from the consumer-visible spec view. The
# post-patch model below needs no reference helpers: the exposed value is the
# input password element for element, spelled out directly in the loop.)
# impl-end


def password_env_value(passwd: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(passwd), 1 / 2))
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(passwd), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The exposed value equals the password element for element.
    Ensures(ToSeq(Result()) == ToSeq(passwd))
    # The mechanism is populated exactly when the password is non-empty.
    Ensures((len(Result()) > 0) == (len(passwd) > 0))
    # post-conditions-end
    # impl-start
    result = []  # type: List[int]
    i = 0
    while i < len(passwd):
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == ToSeq(passwd).take(i))
        Invariant(MustTerminate(len(passwd) - i + 1))
        # invariants-end
        c = passwd[i]
        Assert(ToSeq(passwd).take(i + 1) == ToSeq(passwd).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(passwd).take(len(passwd)) == ToSeq(passwd))
    return result
    # impl-end
