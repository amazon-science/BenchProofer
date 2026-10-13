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
# PRE-PATCH reference helpers (PROOF/IMPL ONLY — elided from the spec view, so
# they do not appear in the consumer-visible projection). These spell out the
# legacy file-fragment quoting the pre-patch code applied to the password
# fragment: backslash (92) doubles, colon (58) is backslash-escaped, every
# other code point maps to itself. This is the deep A-reference the prepatch
# differential is stated against (validated == the removed `_escape_pgpass`
# helper by axiom_check.py / G-AX). The post-patch model.py never references it.
@Pure
def pgpass_quote(c: int) -> PSeq[int]:
    if c == 92:        # backslash -> doubled
        return PSeq(92, 92)
    if c == 58:        # colon -> backslash + colon
        return PSeq(92, 58)
    return PSeq(c)


@Pure
def pgpass_quote_seq(s: PSeq[int]) -> PSeq[int]:
    # Front-recursive whole-sequence quoting, so a single unfold is available to
    # callers (the loop invariant below).
    if len(s) == 0:
        return PSeq(0).take(0)
    return pgpass_quote(s[0]) + pgpass_quote_seq(s.drop(1))
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
    # PRE-PATCH skeleton: the exposed value is the legacy file-fragment quoting
    # of the password (the per-code-point map above), which differs from the
    # raw password whenever it contains code point 58 or 92.
    result = []  # type: List[int]
    i = len(passwd)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(passwd), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(passwd))
        Invariant(ToSeq(result) == pgpass_quote_seq(ToSeq(passwd).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        c = passwd[i - 1]
        Assert(ToSeq(passwd).drop(i - 1)[0] == c)
        Assert(ToSeq(passwd).drop(i - 1).drop(1) == ToSeq(passwd).drop(i))
        if c == 92:
            result = [92, 92] + result
        elif c == 58:
            result = [92, 58] + result
        else:
            result = [c] + result
        i = i - 1
    return result
    # impl-end
