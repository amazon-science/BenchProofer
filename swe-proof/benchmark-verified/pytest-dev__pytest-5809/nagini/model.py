"""Twin-artifact model for pytest-dev__pytest-5809.

Behaviour under specification (stated as desired behaviour, not as an edit):

  When the session output is submitted to the paste service, the request body
  carries three named fields. Two of them are forwarded unchanged from the
  inputs:

    * the paste BODY field holds exactly the supplied contents (identity), and
    * the EXPIRY field holds the constant one-week token "1week".

  The third field selects the syntax-highlighting MODE under which the paste
  service should render the body. Because the body being submitted is the
  console output of a test run — arbitrary text rather than source code in any
  particular language — the mode field is the constant plain-text token "text".
  Crucially this choice is INVARIANT under the running interpreter's major
  version: whatever the interpreter major version, the mode field is "text"
  (it is NOT derived from, and does not vary with, the interpreter version).

Strings are modelled as `List[int]` of Unicode code points (Nagini bans `str`
indexing). The pure sequence theory `PSeq[int]` carries the specification.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axiomatized callee: the modelled behaviour — which constant token the
# request's mode field carries — is concrete and modelled deeply.)
# axioms-end


# pure-start
@Pure
def text_token() -> PSeq[int]:
    """The plain-text highlighting-mode token "text" as code points."""
    return PSeq(116, 101, 120, 116)


@Pure
def expiry_token() -> PSeq[int]:
    """The constant one-week expiry token "1week" as code points."""
    return PSeq(49, 119, 101, 101, 107)
# pure-end


def paste_mode_field(py_major: int) -> List[int]:
    # pre-conditions-start
    # py_major is the running interpreter's major version (an arbitrary int);
    # no carrier object is required.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The mode field is the constant plain-text token, INVARIANT under py_major:
    # the very same value is returned whatever the interpreter major version.
    Ensures(ToSeq(Result()) == text_token())
    # post-conditions-end
    # impl-start
    mode = [116, 101, 120, 116]  # type: List[int]
    return mode
    # impl-end


def paste_body_field(contents: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(contents), 1 / 2))
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(contents), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The body field forwards the supplied contents unchanged (identity).
    Ensures(ToSeq(Result()) == ToSeq(contents))
    # post-conditions-end
    # impl-start
    body = list(contents)  # type: List[int]
    return body
    # impl-end


def paste_expiry_field() -> List[int]:
    # pre-conditions-start
    Requires(MustTerminate(10))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(Result())))
    # The expiry field is the constant one-week token, unchanged.
    Ensures(ToSeq(Result()) == expiry_token())
    # post-conditions-end
    # impl-start
    exp = [49, 119, 101, 101, 107]  # type: List[int]
    return exp
    # impl-end
