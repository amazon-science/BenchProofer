"""Twin-artifact model for sympy__sympy-24443.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A relator word is a finite ordered sequence of blocks; each block is a
  (generator, exponent) pair, and the exponent may be negative (an inverted
  generator). A given assignment maps each generator to a group element of the
  codomain; resolving every block through that assignment yields, for each
  block, the codomain element assigned to its generator together with the
  block's exponent. The IMAGE of the relator word under the assignment is the
  ordered product, taken left to right over the blocks, of the assigned element
  raised to the block's exponent:

        image  =  (g0 ^ e0) * (g1 ^ e1) * ... * (g_{n-1} ^ e_{n-1})

  EVERY block contributes its factor, regardless of the sign of its exponent:
  a block with a negative exponent contributes `g ^ e` (the inverse power) in
  exactly its position, just like a positive one. No block may be silently
  skipped or have its factor replaced by the group identity. The empty word
  maps to the identity. The product is taken in word order; the group operation
  is associative with identity but is NOT assumed commutative, so the order and
  multiplicity of factors is observable.

Group elements of the codomain are modelled as opaque handles (`int` tags) and
the two unchanged group operations the image computation CALLS -- the group
product `gmul` and the integer power `gpow` -- are axiomatized as opaque,
non-commutative monoid operations (A-consumed; provenance + soundness in
mapping.md / axiom_check.py). The relator's blocks are modelled as two parallel
`List[int]`: `block_elems[k]` is the codomain element assigned to block k's
generator (the resolved per-block image) and `block_pows[k]` its exponent. The
image is the front-recursive accumulator fold `image_fold`.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


# axioms-start
@Pure
@ContractOnly
def gid() -> int:
    """The codomain group identity element (opaque handle). Unchanged callee."""
    Ensures(True)


@Pure
@ContractOnly
def gmul(a: int, b: int) -> int:
    """The codomain group product a*b (opaque, NOT assumed commutative). The
    unchanged group multiplication the image computation calls. Provenance +
    executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)


@Pure
@ContractOnly
def gpow(g: int, e: int) -> int:
    """The codomain integer power g**e of a group element (opaque). Defined for
    every integer exponent e, positive, zero, or NEGATIVE (the inverse power).
    The unchanged power callee the image computation invokes per block.
    Provenance + executable soundness check: mapping.md / axiom_check.py."""
    Ensures(True)
# axioms-end


# pure-start
@Pure
def image_fold(acc: int, elems: PSeq[int], pows: PSeq[int]) -> int:
    """Left-to-right product of the per-block factors onto the running product
    `acc`: block 0's factor is `gpow(elems[0], pows[0])`, multiplied on the
    right of `acc`, then recurse over the tail. Front-recursive over the head so
    a single unfold is available per loop step. The empty word leaves `acc`."""
    Requires(len(elems) == len(pows))
    if len(elems) == 0:
        return acc
    return image_fold(gmul(acc, gpow(elems[0], pows[0])),
                      elems.drop(1), pows.drop(1))
# pure-end


def relator_image(block_elems: List[int], block_pows: List[int]) -> int:
    # pre-conditions-start
    # The relator's blocks (resolved element + exponent) are read-only.
    Requires(Acc(list_pred(block_elems), 1 / 2))
    Requires(Acc(list_pred(block_pows), 1 / 2))
    # The two parallel block arrays have equal length (one exponent per block).
    Requires(len(block_elems) == len(block_pows))
    Requires(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(block_elems), 1 / 2))
    Ensures(Acc(list_pred(block_pows), 1 / 2))
    Ensures(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
    # The image is the ordered left-to-right product of every block's factor
    # onto the identity -- every block, including negative-exponent ones,
    # contributes `gpow(elem, exponent)` in its position.
    Ensures(Result() == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
    # post-conditions-end
    # impl-start
    w = gid()
    i = 0
    while i < len(block_elems):
        # invariants-start
        Invariant(Acc(list_pred(block_elems), 1 / 2))
        Invariant(Acc(list_pred(block_pows), 1 / 2))
        Invariant(len(block_elems) == len(block_pows))
        Invariant(0 <= i and i <= len(block_elems))
        Invariant(len(ToSeq(block_elems)) == len(ToSeq(block_pows)))
        Invariant(len(ToSeq(block_elems).drop(i)) == len(ToSeq(block_pows).drop(i)))
        # `w` is the product of the first `i` blocks; the remaining suffix folds
        # onto it to give the whole-word image.
        Invariant(image_fold(w, ToSeq(block_elems).drop(i), ToSeq(block_pows).drop(i))
                  == image_fold(gid(), ToSeq(block_elems), ToSeq(block_pows)))
        # invariants-end
        # The fold unfolds at the head of drop(i) (non-empty since i < len):
        # supply the head/tail split so a single unfold relates step i to i+1.
        Assert(ToSeq(block_elems).drop(i).drop(1) == ToSeq(block_elems).drop(i + 1))
        Assert(ToSeq(block_pows).drop(i).drop(1) == ToSeq(block_pows).drop(i + 1))
        Assert(ToSeq(block_elems).drop(i)[0] == block_elems[i])
        Assert(ToSeq(block_pows).drop(i)[0] == block_pows[i])
        if block_pows[i] >= 0:
            w = gmul(w, gpow(block_elems[i], block_pows[i]))
        i = i + 1
    return w
    # impl-end
