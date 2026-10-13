"""Twin-artifact model for sympy__sympy-22456.

Behaviour under specification (stated as desired behaviour, not as an edit):

  An atomic string-valued symbolic token carries a single defining payload (its
  text) that is deliberately held OFF its positional-argument list: the token
  has an empty argument tuple. Every symbolic object must nonetheless satisfy
  ARGUMENT INVARIANCE — rebuilding the object by applying its reconstruction
  operation to its own positional arguments yields an object equal to the
  original:

      rebuild(positional-arguments-of(t)) == t

  Because the defining text is not among the positional arguments (the argument
  count is zero), a faithful reconstruction must reproduce the original text
  WITHOUT reading it from the (empty) argument list. The discriminating case the
  contract pins: for a token with arbitrary — including non-empty — text, the
  reconstruction from the empty argument list must still carry exactly the
  original text, so that the rebuilt token equals the original. A reconstruction
  that can only source the text from the positional arguments would, on the
  empty list, lose every non-empty text and break the invariance.

  The invariance is a claim about EVERY reconstruction, not only about the ones
  that happen to hand an answer back: the reconstruction is TOTAL — for every
  token it must run to completion and DELIVER a rebuilt token. A reconstruction
  that never delivers one (it re-enters itself on the same token, or spins
  without making progress) does not satisfy the invariance, however its result
  would have been constrained had it arrived. Delivery is bounded by the size of
  the payload being reproduced, so a reconstruction that descends on a STRICTLY
  SMALLER token before assembling its answer is admissible.

The token's defining text is modelled as `List[int]` of Unicode code points
(Nagini bans `str` indexing); equality of two tokens is equality of that text,
carried by `PSeq[int]` via `ToSeq`. The positional-argument list is modelled by
its length alone (it is empty for this atomic token, and the reconstruction
consumes no positional element).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Atomic:
    """An atomic string-valued token; only its defining `text` payload is
    modelled (the single quantity token equality depends on)."""

    def __init__(self, text: List[int]) -> None:
        Requires(Acc(list_pred(text)))
        # Building a carrier completes: it hands the token back.
        Requires(MustTerminate(1))
        Ensures(Acc(self.text) and self.text is text)  # type: ignore
        Ensures(Acc(list_pred(self.text)))  # type: ignore
        Ensures(ToSeq(self.text) == Old(ToSeq(text)))  # type: ignore
        self.text = text


# axioms-start
# (no @ContractOnly axioms: the operation that changed — how an atomic token
# reconstructs itself from its arguments — is modelled DEEPLY, as a direct
# text-preserving rebuild. No unchanged opaque callee is consumed inside the
# contract. See refinement.md / mapping.md.)
# axioms-end


# pure-start
@Pure
def arg_count(s: Atomic) -> int:
    """The number of positional arguments of the token. The defining text is
    held OFF the argument list, so an atomic string token has zero positional
    arguments."""
    Requires(Acc(s.text, 1 / 4) and Acc(list_pred(s.text), 1 / 4))
    Ensures(Result() == 0)
    return 0
# pure-end


def rebuild_from_args(s: Atomic) -> Atomic:
    # pre-conditions-start
    # `s` is read-only: reconstruction never mutates the original (fractional
    # permission on both the field reference and its list contents).
    Requires(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
    # TOTALITY. Every postcondition below is claimed of EVERY admissible call,
    # not merely of the calls that happen to reach a return: the reconstruction
    # must run to completion and DELIVER a token. The delivery level is bounded
    # by the size of the payload being reproduced, so a reconstruction that
    # descends on a STRICTLY SMALLER token is admissible, while one that
    # re-enters itself on this very token — or loops without advancing — is not,
    # and cannot borrow this contract to stand in for its own answer.
    Requires(MustTerminate(len(s.text) + 2))
    # pre-conditions-end
    # post-conditions-start
    # The original token is preserved (read-only).
    Ensures(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
    # A fresh token is produced (full permission on the reconstruction).
    Ensures(Acc(Result().text) and Acc(list_pred(Result().text)))
    # The token's positional-argument list is empty: the reconstruction draws
    # from zero positional arguments.
    Ensures(arg_count(s) == 0)
    # ARGUMENT INVARIANCE: rebuilding the token from its (empty) positional
    # arguments yields a token EQUAL to the original — i.e. carrying EXACTLY the
    # original text, element for element, even when that text is non-empty.
    # This is the discriminating clause: a reconstruction that could only source
    # the text from the empty argument list would lose any non-empty text.
    Ensures(ToSeq(Result().text) == ToSeq(s.text))
    # post-conditions-end
    # impl-start
    # The reconstruction operation yields the very same token (its result is the
    # original object), so it carries the original text regardless of how many
    # positional arguments there are. Materialise a fresh carrier holding
    # exactly the original text.
    n = len(s.text)
    rebuilt_text = []  # type: List[int]
    i = 0
    while i < n:
        # invariants-start
        Invariant(Acc(s.text, 1 / 2) and Acc(list_pred(s.text), 1 / 2))
        Invariant(Acc(list_pred(rebuilt_text)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(s.text))
        Invariant(ToSeq(rebuilt_text) == ToSeq(s.text).take(i))
        # At most `n - i` passes remain; `i` rises by exactly one each pass and
        # `n` is loop-invariant, so the bound strictly decreases, and the `+ 1`
        # keeps it positive on the final pass. The reproduction completes.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        c = s.text[i]
        Assert(ToSeq(s.text).take(i + 1) == ToSeq(s.text).take(i) + PSeq(c))
        rebuilt_text = rebuilt_text + [c]
        i = i + 1
    Assert(i == n)
    Assert(ToSeq(s.text).take(n) == ToSeq(s.text))
    Assert(ToSeq(rebuilt_text) == ToSeq(s.text))
    result = Atomic(rebuilt_text)  # type: Atomic
    Assert(result.text is rebuilt_text)
    Assert(ToSeq(result.text) == ToSeq(s.text))
    return result
    # impl-end
