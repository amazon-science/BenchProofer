"""Twin-artifact model for sympy__sympy-21930.

Behaviour under specification (an abstract behavioural contract, not an edit):

  A renderer whose body already carries an interior ``^`` superscript must emit
  that body as a SINGLE self-delimited group: the rendered token begins with
  ``{`` and ends with the matching ``}``, with the original body verbatim in
  between (result element 0 is ``{``, the last element is ``}``, and the
  interior is the body unchanged). The contract is compositional — when a
  further superscript ``^{...}`` is appended directly after the token, that
  appended ``^`` must bind to the WHOLE token rather than colliding with the
  body's own interior ``^``. A token that is a single delimited group has this
  property: the appended ``^`` sits just outside the closing ``}``. A bare body
  that exposes a trailing interior ``^`` does not.

Three renderers with this contract are modelled. Each receives a body that
already contains an interior ``^`` and must wrap it as one group.

Rendering is a bounded, straight-line computation: the operation MUST
terminate and return its token (a total-correctness obligation, carried as
MustTerminate in the precondition). An implementation that diverges before
returning would satisfy the value postconditions only vacuously and would
never deliver the rendered token to the printer.

Strings are modelled as ``List[int]`` of code points (Nagini bans ``str``
indexing); the specification is carried over ``PSeq[int]`` via ``ToSeq``. The
special tokens are the ASCII code points ``{`` = 123, ``}`` = 125, ``^`` = 94.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No consumed @ContractOnly axioms: the rendered-token construction is
# modelled DEEPLY below. A body that carries an interior ``^`` and its
# interaction with an appended outer superscript — which must bind to the
# wrapped group rather than to the interior ``^`` — are spelled out as the pure
# models `grouped_token` / `appended_super_is_outer`, validated against the real
# renderer out-of-band by axiom_check.py (G-AX).)
# axioms-end


# pure-start
@Pure
def LBRACE() -> int:
    return 123        # '{'


@Pure
def RBRACE() -> int:
    return 125        # '}'


@Pure
def CARET() -> int:
    return 94         # '^'


@Pure
def grouped_token(body: PSeq[int]) -> PSeq[int]:
    """The rendered token: the body wrapped as one group `{ body }`."""
    return PSeq(LBRACE()) + body + PSeq(RBRACE())


@Pure
def appended_super_is_outer(token: PSeq[int], exp: PSeq[int]) -> bool:
    """A superscript `^{...}` appended after `token` is the OUTERMOST
    superscript of the composite: the `^` introducing it sits immediately after
    a closing `}` (so it binds to the preceding delimited group), not
    immediately after another superscript's content. This holds exactly when
    `token` ends in `}` — i.e. `token` is a self-delimited group."""
    Requires(0 <= len(token))
    if len(token) == 0:
        return False
    return token[len(token) - 1] == RBRACE()
# pure-end


def render_token_a(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # the token is exactly the body wrapped as one group
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    # self-delimited group: opens with `{`, closes with `}`, body verbatim
    # between (length is body + the two delimiters)
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    # an appended superscript binds to the whole token (it follows the closing
    # `}`), so it does not collide with the body's interior `^`
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end


def render_token_b(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end


def render_token_c(body: List[int]) -> List[int]:
    """Renderer whose body carries an interior `^` superscript; must emit the
    body as one self-delimited group `{ body }`."""
    # pre-conditions-start
    Requires(Acc(list_pred(body), 1 / 2))
    # Rendering is a bounded, straight-line computation: the renderer MUST
    # terminate and return its token (total correctness). A diverging
    # implementation would satisfy the value postconditions only vacuously
    # and would never deliver the rendered token to the printer.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(body), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == grouped_token(ToSeq(body)))
    Ensures(len(Result()) == len(body) + 2)
    Ensures(ToSeq(Result())[0] == LBRACE())
    Ensures(ToSeq(Result())[len(Result()) - 1] == RBRACE())
    Ensures(Forall(PSeq[int], lambda e:
                   appended_super_is_outer(ToSeq(Result()), e)))
    # post-conditions-end
    # impl-start
    result = [LBRACE()]  # type: List[int]
    i = 0
    while i < len(body):
        # invariants-start
        Invariant(Acc(list_pred(body), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(body))
        Invariant(ToSeq(result) == PSeq(LBRACE()) + ToSeq(body).take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure (len(body) - i), discharging
        # MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(body) - i + 1))
        # invariants-end
        result.append(body[i])
        i = i + 1
    result.append(RBRACE())
    return result
    # impl-end
