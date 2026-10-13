"""Twin-artifact model for pylint-dev__pylint-6386.

Behaviour under specification (an abstract input -> output contract):

  The operation transforms an ordered list of argument tokens into an output
  list of tokens together with a verbose-mode flag. There is a designated
  verbose option that has two interchangeable spellings: a long spelling and a
  short single-letter spelling. The two spellings denote the same option and
  are treated identically.

  The contract is:
    * A token that is the verbose option, in EITHER spelling, is removed from
      the output and turns verbose mode on.
    * Every other token is preserved, unchanged and in its original relative
      order, in the output.
    * Verbose mode in the output state is on iff it was already on on input or
      at least one verbose-option token (either spelling) appeared in the input.

    * The pass is carried out to completion for an argument list of ANY length:
      every token is examined once and the caller is then handed back the
      forwarded token list; it is not left waiting on one.

  The short spelling and the long spelling of the verbose option must produce
  the same observable result.

Argument tokens are modelled as `List[int]` (Nagini bans `str` indexing): each
token is abstracted to a small integer KIND code naming the four token classes
the contract distinguishes — verbose-long, verbose-short, and two classes of
non-verbose token. The output token list is pinned exactly over `PSeq[int]`,
and the verbose flag is the mutated state of the run object.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
# Completion obligations: a measure that must strictly decrease at every call and
# every iteration, so the clauses below are claimed of EVERY execution rather than
# only of the ones that reach a return -- a pass that never delivers a forwarded
# list cannot satisfy them by never arriving at an answer.
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (No axioms: the whole contract — classifying each token, removing the verbose
# option in either spelling, preserving every other token in order, and the
# verbose-flag side effect — is expressed directly over the token-kind
# sequence. There is no external opaque callee whose contract the proof
# consumes.)
# axioms-end


# pure-start
# Token KIND codes (four opaque token classes the contract distinguishes):
#   0  OTHER_A        - a non-verbose token; preserved in the output.
#   1  VERBOSE_LONG   - the verbose option in its long spelling.
#   2  VERBOSE_SHORT  - the verbose option in its short single-letter spelling.
#   3  OTHER_B        - a non-verbose token; preserved in the output.
# (Classes 0 and 3 are distinct opaque non-verbose token classes; both are
#  preserved. Only classes 1 and 2 — the two spellings of the verbose option —
#  are removed and turn on verbose mode.)

@Pure
def keep(kind: int) -> bool:
    """A token is preserved in the output iff it is a non-verbose token (class
    0 or 3). The two spellings of the verbose option (1, 2) are removed."""
    return kind == 0 or kind == 3


@Pure
def sets_verbose(kind: int) -> bool:
    """A token turns on verbose mode iff it is the verbose option in EITHER its
    long or its short single-letter spelling."""
    return kind == 1 or kind == 2


@Pure
def processed(s: PSeq[int]) -> PSeq[int]:
    """The output token list: concatenate, in original order, each preserved
    token (a removed token contributes nothing). Front-recursive so a single
    unfold is available to callers per step."""
    if len(s) == 0:
        return PSeq(0).take(0)
    if keep(s[0]):
        return PSeq(s[0]) + processed(s.drop(1))
    return processed(s.drop(1))


@Pure
def any_verbose(s: PSeq[int]) -> bool:
    """Whether any token in the sequence is the verbose option in either
    spelling. Front-recursive (a left fold of OR)."""
    if len(s) == 0:
        return False
    return sets_verbose(s[0]) or any_verbose(s.drop(1))
# pure-end


class Run:
    def __init__(self) -> None:
        # A fresh run is built to completion. Level 2 is the leaf level, strictly
        # below the level the pass itself carries, so the pass may construct one.
        Requires(MustTerminate(2))
        Ensures(Acc(self.verbose) and self.verbose == False)  # type: ignore[name-defined]
        self.verbose = False  # type: bool


def forward_startup_tokens(run: Run, args: List[int]) -> List[int]:
    # pre-conditions-start
    # The token kinds are the read-only input; only the run object's verbose
    # flag is mutated. Each token is one of the four valid kind codes.
    Requires(Acc(run.verbose))
    Requires(Acc(list_pred(args), 1 / 2))
    Requires(Forall(int, lambda k: (Implies(0 <= k and k < len(args),
                                            0 <= args[k] and args[k] <= 3))))
    # The pass runs to completion and hands the forwarded list back, for an
    # argument list of ANY length: each token is examined once and the pass then
    # returns. Demanded of every admissible input, so this obliges the pass; it
    # restricts no input. Level 6 leaves room strictly below it for the run
    # object's own construction (level 2).
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(run.verbose))
    Ensures(Acc(list_pred(args), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # The output list is exactly the preserved tokens, in their original order:
    # every non-verbose token survives; both spellings of the verbose option
    # are removed.
    Ensures(ToSeq(Result()) == processed(ToSeq(args)))
    # Verbose mode is on iff it was already on, or some verbose-option token
    # (long OR short spelling) appeared in the input.
    Ensures(run.verbose == (Old(run.verbose) or any_verbose(ToSeq(args))))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
