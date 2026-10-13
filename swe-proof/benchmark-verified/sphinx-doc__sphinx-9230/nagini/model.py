"""Twin-artifact model for sphinx-doc__sphinx-9230.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A typed field argument is a run of tokens (a token is one maximal
  whitespace-free chunk). The whole run carries two pieces of information: a
  parameter name and a parameter type description. The type description may
  itself span several tokens (e.g. a comma-separated generic such as
  ``dict(str, str)``). The desired parse assigns these two pieces structurally
  over the run t0 t1 ... t(n-1) of n >= 2 tokens:

    (1) the parsed name is exactly the FINAL element of the run, t(n-1); and
    (2) the parsed type is the ordered PREFIX of the run — every element before
        the last, t0 t1 ... t(n-2), in their original order, separated by a
        single space — so that none of the leading tokens of a multi-token type
        is dropped.

  When the prefix is a single token the result is just (t0, t1); when the
  prefix spans several tokens every one of them is retained, in order, ahead of
  the name.

Modelling choices (Nagini fragment):
  * `str` indexing/iteration crashes Nagini, so the argument is modelled as the
    sequence of its tokens. Each token is one distinct symbol (an `int >= 0`);
    the run is a `List[int]` (carrier) / `PSeq[int]` (specification). The
    rendered type re-emits each prefix element separated by a single space;
    mapping.md records that the run abstracts the maximal whitespace-free chunks
    of the real string and that the modelled domain is single-space-separated
    input (so the single-space rendering reproduces the original type text).
  * A token is emitted into a rendered type via `encode_name`, kept disjoint
    from the separator code point so a token is never confused with the
    separating space.
  * The structural parse is modelled DEEPLY (a front-recursive prefix fold +
    verified construction loops), not behind a consumed axiom; on the modelled
    single-space-separated domain axiom_check.py (G-AX) validates it against the
    real `str` behaviour as an A-reference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate

SPACE = 32   # " " — the single separator between elements of a rendered type


# axioms-start
# No consumed axioms. The structural assignment of name (final element) and type
# (ordered prefix) is the behaviour under specification and is modelled deeply
# (the pure fold below + the impl loops spell it out). The only library behaviour
# relied on is that re-emitting a token prefix separated by single spaces
# reproduces the original type text WHEN the input is single-space-separated;
# this is validated out-of-band by axiom_check.py (G-AX) as an A-reference on
# that modelled domain, not consumed as an axiom.
# axioms-end


# pure-start
@Pure
def empty_seq() -> PSeq[int]:
    """The empty token sequence."""
    Ensures(len(Result()) == 0)
    return PSeq(0).take(0)


@Pure
def encode_name(t: int) -> int:
    """Encode a token disjointly from the separator code point, so a token can
    never be confused with the separating space in a rendered type. Tokens are
    emitted as (token + 256)."""
    return t + 256


@Pure
def last_token(run: PSeq[int]) -> int:
    """The final token of a non-empty run."""
    Requires(len(run) >= 1)
    return run[len(run) - 1]


@Pure
def joined(run: PSeq[int]) -> PSeq[int]:
    """The single-space-separated rendering of a run of tokens, in order.
    Front-recursive so a single unfold is available per construction step.
    Empty for an empty run; the lone token for a single-token run; otherwise
    every token in order separated by one space."""
    if len(run) == 0:
        return empty_seq()
    if len(run) == 1:
        return PSeq(encode_name(run[0]))
    return PSeq(encode_name(run[0])) + PSeq(SPACE) + joined(run.drop(1))
# pure-end


def parsed_argument_name(tokens: List[int]) -> List[int]:
    """The parsed parameter name of a typed argument: the FINAL element of the
    run (rendered as a one-element sequence). Per (1)."""
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(tokens) >= 2)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The name is exactly the last token, rendered as a one-token sequence.
    Ensures(len(ToSeq(tokens)) == len(tokens) and len(ToSeq(tokens)) >= 2
            and ToSeq(Result())
            == PSeq(encode_name(last_token(ToSeq(tokens)))))
    # post-conditions-end
    # impl-start
    last = tokens[len(tokens) - 1]  # type: int
    Assert(last_token(ToSeq(tokens)) == last)
    result = [encode_name(last)]  # type: List[int]
    Assert(ToSeq(result) == PSeq(encode_name(last)))
    return result
    # impl-end


def parsed_argument_type(tokens: List[int]) -> List[int]:
    """The parsed type of a typed argument: the ordered PREFIX of the run —
    every element before the last, separated by single spaces. Per (2)."""
    # pre-conditions-start
    Requires(Acc(list_pred(tokens), 1 / 2))
    Requires(len(tokens) >= 2)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(tokens), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The type is the join of every token up to (but excluding) the last.
    Ensures(ToSeq(Result()) == joined(ToSeq(tokens).take(len(tokens) - 1)))
    # post-conditions-end
    # impl-start
    tokens_s = ToSeq(tokens)  # type: PSeq[int]
    prefix_len = len(tokens) - 1  # type: int
    result = []  # type: List[int]
    i = prefix_len
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(tokens), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(tokens_s == ToSeq(tokens))
        Invariant(prefix_len == len(tokens) - 1)
        Invariant(0 <= i and i <= prefix_len)
        Invariant(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        elt = tokens[i - 1]  # type: int
        Assert(tokens_s.take(prefix_len).drop(i - 1)[0] == elt)
        Assert(tokens_s.take(prefix_len).drop(i - 1).drop(1)
               == tokens_s.take(prefix_len).drop(i))
        if i == prefix_len:
            # last token of the prefix: no trailing separator
            result = [encode_name(elt)]
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        else:
            result = [encode_name(elt), SPACE] + result
            Assert(ToSeq(result) == PSeq(encode_name(elt)) + PSeq(SPACE)
                   + joined(tokens_s.take(prefix_len).drop(i)))
            Assert(ToSeq(result) == joined(tokens_s.take(prefix_len).drop(i - 1)))
        i = i - 1
    Assert(ToSeq(result) == joined(tokens_s.take(prefix_len)))
    return result
    # impl-end
