"""Twin-artifact model for pytest-dev__pytest-10356.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A class participates in a linearised ancestor chain: itself first, then each
  of its ancestors in a determinate resolution order. Each class in that chain
  carries its OWN directly-attached list of decorating tokens (the tokens
  applied to that class alone, not inherited).

  When the full ancestor chain is to be considered, the tokens attached to the
  whole class are EXACTLY the concatenation of every chain member's own token
  list, in chain order: the class's own tokens first, then those of each
  ancestor in order. No member's tokens are dropped, even when several ancestors
  each contribute tokens (e.g. a class with two independent ancestors, each
  decorated, yields BOTH ancestors' tokens, not just one).

  When only the directly-attached tokens are wanted, the result is exactly the
  class's own token list -- the contributions of the ancestors are excluded.

The ancestor chain is modelled as `PSeq[PSeq[int]]`: an ordered sequence of
per-class own-token lists, each a `PSeq[int]` of token identifiers (Nagini bans
`str` indexing / rich objects). The concatenation is modelled DEEPLY as a
front-recursive fold (`concat_chain`); the per-class own-token lookup along the
real linearisation is the unchanged callee, validated out-of-band by
axiom_check.py (G-AX), NOT consumed as an axiom.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no consumed @ContractOnly axiom: the chain-concatenation is modelled deeply
#  below as `concat_chain` and validated == the real per-class own-list lookup
#  over the linearisation out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
@Pure
def concat_chain(chain: PSeq[PSeq[int]]) -> PSeq[int]:
    """The concatenation of a chain of per-member token lists, in chain order:
    chain[0] then, appended, the concatenation of the remaining members.
    Front-recursive (one unfold per member) so a backward impl loop can
    discharge the value equality. The empty chain concatenates to the empty
    sequence."""
    if len(chain) == 0:
        return PSeq(0).take(0)
    return chain[0] + concat_chain(chain.drop(1))
# pure-end


def unpacked_tokens(chain: PSeq[PSeq[int]], consider_chain: bool) -> PSeq[int]:
    # pre-conditions-start
    # The chain always has at least its first member (the class itself).
    Requires(len(chain) >= 1)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # With the full chain considered, the result is EXACTLY the concatenation
    # of every member's own token list, in chain order -- nothing dropped.
    Ensures(Implies(consider_chain, Result() == concat_chain(chain)))
    # Without the chain, the result is exactly the first member's own tokens.
    Ensures(Implies(not consider_chain, Result() == chain[0]))
    # post-conditions-end
    # impl-start
    if not consider_chain:
        return chain[0]
    # Empty accumulator, derived from the input carrier (the suffix chain[len:]
    # is empty, and concat_chain of the empty chain is the empty sequence).
    result = chain[len(chain) - 1].take(0)  # type: PSeq[int]
    i = len(chain)
    while i > 0:
        # invariants-start
        Invariant(0 <= i and i <= len(chain))
        # `result` is the concatenation of the suffix chain[i:].
        Invariant(result == concat_chain(chain.drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        Assert(chain.drop(i - 1)[0] == chain[i - 1])
        Assert(chain.drop(i - 1).drop(1) == chain.drop(i))
        result = chain[i - 1] + result
        i = i - 1
    return result
    # impl-end
