"""Twin-artifact model for astropy__astropy-13579.

Behaviour under specification (the desired input/output contract):

  Two boolean/scalar vectors indexed by a common index space `0 <= i < n`
  describe a per-index selection. `kept[i]` selects between two candidate
  scalars at index `i`:

    * if `kept[i]` is true, index `i` takes `supplied[i]`;
    * if `kept[i]` is false, index `i` takes `world_at_slice[i]`.

  The two modeled functions:

  (1) `assemble_inverse_world` returns the length-`n` vector whose element `i`
      is exactly this per-index selection: `value_at(kept, supplied,
      world_at_slice, i)`. Equivalently its output equals the pure reference
      vector `ref_world_vector`.
  (2) `recovered_pixel` applies a single scalar-valued function of the WHOLE
      assembled vector (component `dim`) to that vector, and states the result
      equals that function applied to the reference vector. That function is an
      opaque, deterministic callee (axiomatized: equal vectors give equal
      results; vectors that differ are NOT provably equal), so the result is a
      function of the EXACT assembled vector — any vector that differs in some
      slot is a different argument and not provably the same result.

Scalar values are modeled as `int`: the contract is about *which* scalar is
selected at each index and the output being a function of the whole vector,
which is precision-independent (see refinement.md R0). The selection flag at
each index is the boolean vector `kept`; the two candidate scalars are
`supplied` and `world_at_slice` (all sharing one index space; refinement.md R1
explains the order-preserving re-indexing). Sequences are `List[int]`; the
specification uses `PSeq[int]` via `ToSeq`. Markers (machine-parsed) delimit
spec / proof / impl regions; provenance binding to the repository is in
mapping.md.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def full_world_to_pixel(world_vec: PSeq[int], dim: int) -> int:
    """A single scalar-valued function of the whole vector, component `dim`
    (an opaque, UNCHANGED callee). A `@Pure @ContractOnly` declaration encodes
    exactly the property the proof consumes: it is a deterministic function of
    the whole vector (equal vectors give equal results, different vectors are
    NOT provably equal). Provenance (which repository callee this binds to) and
    the executable soundness check are in mapping.md §3 / axiom_check.py (G-AX).
    """
    Requires(dim >= 0)
# axioms-end


# pure-start
@Pure
def value_at(kept: PSeq[bool], supplied: PSeq[int],
             world_at_slice: PSeq[int], iworld: int) -> int:
    """The scalar the assembled vector carries at index `iworld`: `supplied`
    at that index if `kept` is true there, else `world_at_slice` at that
    index."""
    Requires(0 <= iworld and iworld < len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    if kept[iworld]:
        return supplied[iworld]
    return world_at_slice[iworld]


@Pure
def ref_world_vector(kept: PSeq[bool], supplied: PSeq[int],
                     world_at_slice: PSeq[int], n: int) -> PSeq[int]:
    """The reference assembled world vector of length `n`: element `i` is
    `value_at(.., i)`. Prefix-recursive (extends by one element per step) so the
    assembly loop's invariant tracks `ToSeq(result) == ref_world_vector(.., i)`.
    """
    Requires(0 <= n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Ensures(len(Result()) == n)
    if n == 0:
        return world_at_slice.take(0)
    return ref_world_vector(kept, supplied, world_at_slice, n - 1) \
        + PSeq(value_at(kept, supplied, world_at_slice, n - 1))


@Pure
def lemma_ref_unfold(kept: PSeq[bool], supplied: PSeq[int],
                     world_at_slice: PSeq[int], n: int) -> bool:
    """The prefix-recursion equation of `ref_world_vector`, exposed for callers
    (this is its body unfolded once)."""
    Requires(0 < n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Ensures(Result())
    Ensures(ref_world_vector(kept, supplied, world_at_slice, n)
            == ref_world_vector(kept, supplied, world_at_slice, n - 1)
            + PSeq(value_at(kept, supplied, world_at_slice, n - 1)))
    return True


@Pure
def lemma_ref_index(kept: PSeq[bool], supplied: PSeq[int],
                    world_at_slice: PSeq[int], n: int, i: int) -> bool:
    """Unfolding lemma: for the prefix-recursive `ref_world_vector`, the element
    at index `i < n` equals `value_at(.., i)`. Proven by recursion on `n`."""
    Requires(0 <= n and n <= len(kept))
    Requires(len(supplied) == len(kept) and len(world_at_slice) == len(kept))
    Requires(0 <= i and i < n)
    Ensures(Result())
    Ensures(ref_world_vector(kept, supplied, world_at_slice, n)[i]
            == value_at(kept, supplied, world_at_slice, i))
    if i == n - 1:
        return True
    return lemma_ref_index(kept, supplied, world_at_slice, n - 1, i)
# pure-end


def assemble_inverse_world(kept: List[bool], supplied: List[int],
                           world_at_slice: List[int], world_n_dim: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(kept), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Acc(list_pred(world_at_slice), 1 / 2))
    Requires(world_n_dim >= 0)
    # kept[i] is the per-index selection flag; supplied and world_at_slice are
    # the two candidate-scalar vectors (all of length world_n_dim).
    Requires(len(kept) == world_n_dim)
    Requires(len(supplied) == world_n_dim)
    Requires(len(world_at_slice) == world_n_dim)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kept), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    Ensures(Acc(list_pred(world_at_slice), 1 / 2))
    Ensures(len(kept) == world_n_dim and len(supplied) == world_n_dim
            and len(world_at_slice) == world_n_dim)
    Ensures(Acc(list_pred(Result())))
    Ensures(len(Result()) == world_n_dim)
    # The assembled vector is exactly the reference vector.
    Ensures(ToSeq(Result()) == ref_world_vector(ToSeq(kept), ToSeq(supplied),
                                                ToSeq(world_at_slice), world_n_dim))
    # At each index where `kept` is true, the result carries `supplied[iw]`.
    Ensures(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim and kept[iw],
                                           ToSeq(Result())[iw] == supplied[iw]),
                                   [[ToSeq(Result())[iw]]])))
    # At each index where `kept` is false, the result carries
    # `world_at_slice[iw]` (the second candidate scalar at that index).
    Ensures(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim and not kept[iw],
                                           ToSeq(Result())[iw] == world_at_slice[iw]),
                                   [[ToSeq(Result())[iw]]])))
    # post-conditions-end
    # impl-start
    world_arrays_new = []  # type: List[int]
    iworld = 0
    while iworld < world_n_dim:
        # invariants-start
        Invariant(Acc(list_pred(kept), 1 / 2))
        Invariant(Acc(list_pred(supplied), 1 / 2))
        Invariant(Acc(list_pred(world_at_slice), 1 / 2))
        Invariant(Acc(list_pred(world_arrays_new)))
        Invariant(len(kept) == world_n_dim and len(supplied) == world_n_dim
                  and len(world_at_slice) == world_n_dim)
        Invariant(0 <= iworld and iworld <= world_n_dim)
        Invariant(len(world_arrays_new) == iworld)
        Invariant(ToSeq(world_arrays_new) == ref_world_vector(ToSeq(kept), ToSeq(supplied),
                                                            ToSeq(world_at_slice), iworld))
        # each appended slot already carries supplied / at-view per kept-ness
        Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and kept[iw],
                                                 ToSeq(world_arrays_new)[iw] == supplied[iw]),
                                         [[ToSeq(world_arrays_new)[iw]]])))
        Invariant(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld and not kept[iw],
                                                 ToSeq(world_arrays_new)[iw] == world_at_slice[iw]),
                                         [[ToSeq(world_arrays_new)[iw]]])))
        Invariant(MustTerminate(world_n_dim - iworld + 1))
        # invariants-end
        old_seq = ToSeq(world_arrays_new)
        if kept[iworld]:
            v = supplied[iworld]
        else:
            v = world_at_slice[iworld]
        Assert(v == value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld))
        world_arrays_new.append(v)
        Assert(ToSeq(world_arrays_new) == old_seq + PSeq(v))
        # old elements are unchanged; the new element at iworld is v.
        Assert(Forall(int, lambda iw: (Implies(0 <= iw and iw < iworld,
                                              ToSeq(world_arrays_new)[iw] == old_seq[iw]),
                                      [[ToSeq(world_arrays_new)[iw]]])))
        Assert(ToSeq(world_arrays_new)[iworld] == v)
        # ref_world_vector is prefix-recursive: one unfold at iworld+1.
        Assert(lemma_ref_unfold(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iworld + 1))
        iworld += 1
    # certify each final element equals value_at via the unfolding lemma, so the
    # kept/dropped postconditions read off the same per-slot characterization.
    Assert(Forall(int, lambda iw: (Implies(0 <= iw and iw < world_n_dim,
                                          lemma_ref_index(ToSeq(kept), ToSeq(supplied),
                                                          ToSeq(world_at_slice), world_n_dim, iw)),
                                  [[value_at(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), iw)]])))
    return world_arrays_new
    # impl-end


def recovered_pixel(kept: List[bool], supplied: List[int],
                    world_at_slice: List[int], world_n_dim: int, dim: int) -> int:
    # pre-conditions-start
    Requires(Acc(list_pred(kept), 1 / 2))
    Requires(Acc(list_pred(supplied), 1 / 2))
    Requires(Acc(list_pred(world_at_slice), 1 / 2))
    Requires(world_n_dim >= 0)
    Requires(dim >= 0)
    Requires(len(kept) == world_n_dim)
    Requires(len(supplied) == world_n_dim)
    Requires(len(world_at_slice) == world_n_dim)
    Requires(MustTerminate(6))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(kept), 1 / 2))
    Ensures(Acc(list_pred(supplied), 1 / 2))
    Ensures(Acc(list_pred(world_at_slice), 1 / 2))
    Ensures(len(kept) == world_n_dim and len(supplied) == world_n_dim
            and len(world_at_slice) == world_n_dim)
    # The result is the opaque function (component `dim`) evaluated at the
    # reference vector. Because that function is opaque and deterministic, the
    # result is tied to the EXACT vector: a vector differing in any slot is a
    # different argument and not provably this result.
    Ensures(Result() == full_world_to_pixel(
        ref_world_vector(ToSeq(kept), ToSeq(supplied), ToSeq(world_at_slice), world_n_dim), dim))
    # post-conditions-end
    # impl-start
    assembled = assemble_inverse_world(kept, supplied, world_at_slice, world_n_dim)
    res = full_world_to_pixel(ToSeq(assembled), dim)
    return res
    # impl-end
