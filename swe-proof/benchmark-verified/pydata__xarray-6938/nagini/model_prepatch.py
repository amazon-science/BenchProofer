"""Twin-artifact model for pydata__xarray-6938.

Behaviour under specification (stated as desired behaviour, not as an edit):

  Re-presenting a one-dimensional coordinate variable as a coordinate variable
  must yield an INDEPENDENT object, never an alias of the receiver. Concretely:

    (1) the returned object is a distinct object from the receiver (a fresh
        allocation, not the receiver itself);
    (2) the returned object initially carries the same dimension-name tuple as
        the receiver;
    (3) the returned object owns its own dimension-name storage, so that later
        reassigning the result's dimension names leaves the receiver's
        dimension names unchanged.

The coordinate variable is modelled as a small object whose only touched field
is its dimension-name tuple `dims`, carried as a `List[int]` of name codes
(Nagini bans `str` indexing, and the tested observation is purely the tuple of
dimension names). Object independence is captured by Nagini's permission
discipline: the receiver is read-only (fractional permission, required AND
ensured), while the result is handed FULL write permission to its own `dims`
field -- a guarantee an aliasing result (one that returns the receiver itself)
cannot satisfy, since the receiver's retained read permission plus the result's
full write permission would exceed the total available permission.

A second exercised behaviour: re-presenting the variable in its plain
(non-coordinate) form likewise yields a distinct object that observes exactly
the receiver's stored dimension names.

All re-presentation operations are TOTAL: each carries a MustTerminate
obligation in its precondition. The real callees are bounded, straight-line
copies (tuple copy + fresh allocation) that always return; an implementation
that diverges would satisfy the value/identity postconditions only vacuously
and would never deliver the re-presented variable to the caller (swap_dims
would hang instead of returning the swapped dataset).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axiomatized callees: the changed behaviour -- independent allocation vs.
# aliasing -- is modelled deeply via the permission discipline, not behind an
# axiom.)
# axioms-end


# pure-start
# (no pure helpers needed.)
# pure-end


class CoordVar:
    """A one-dimensional coordinate variable. The only field the studied
    behaviour touches is `dims`, the tuple of dimension names (modelled as a
    `List[int]` of name codes)."""

    def __init__(self, dims: List[int]) -> None:
        # pre-conditions-start
        Requires(Acc(list_pred(dims)))
        # Construction is a single field write: it MUST terminate. The strictly
        # smallest measure (1) lets every re-presentation holding a larger
        # obligation invoke the constructor without leaking its own obligation.
        Requires(MustTerminate(1))
        # pre-conditions-end
        # post-conditions-start
        Ensures(Acc(self.dims))
        Ensures(Acc(list_pred(self.dims)))
        Ensures(self.dims is dims)
        Ensures(ToSeq(self.dims) == Old(ToSeq(dims)))
        # post-conditions-end
        # impl-start
        self.dims = dims  # type: List[int]
        # impl-end


def independent_clone(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The copy is a bounded element-wise walk over the receiver's dims: it
    # MUST terminate. Measure 2 > the constructor's 1, so the fresh-allocation
    # call discharges without leaking the obligation. A diverging clone would
    # never hand the caller the promised independent object.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    # The receiver's dimension names are unchanged.
    Ensures(ToSeq(self.dims) == Old(ToSeq(self.dims)))
    # The copy is a distinct object owning its own dimension-name storage.
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # ... carrying the same dimension names as the receiver.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    s_old = ToSeq(self.dims)  # type: PSeq[int]
    new_dims = []  # type: List[int]
    i = 0
    while i < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(new_dims)))
        Invariant(ToSeq(self.dims) == s_old)
        Invariant(0 <= i and i <= len(s_old))
        Invariant(ToSeq(new_dims) == s_old.take(i))
        # the copy loop consumes the caller's termination obligation with a
        # strictly decreasing measure, discharging MustTerminate(2).
        Invariant(MustTerminate(len(self.dims) - i + 1))
        # invariants-end
        new_dims.append(self.dims[i])
        i = i + 1
    Assert(i == len(s_old))
    Assert(s_old.take(len(s_old)) == s_old)
    Assert(ToSeq(new_dims) == s_old)
    res = CoordVar(new_dims)
    Assert(ToSeq(res.dims) == s_old)
    Assert(ToSeq(self.dims) == s_old)
    Assert(ToSeq(res.dims) == ToSeq(self.dims))
    return res
    # impl-end


def as_coordinate(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The re-presentation is a bounded operation that always returns; callers
    # depend on it RETURNING the independent object before reassigning that
    # object's dims. It MUST terminate: an implementation that loops forever
    # would satisfy the value clauses only vacuously and is rejected here.
    # Measure 3 > independent_clone's 2.
    Requires(MustTerminate(3))
    # pre-conditions-end
    # post-conditions-start
    # The receiver is read-only and survives unchanged.
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(ToSeq(self.dims) == Old(ToSeq(self.dims)))
    # The result is an INDEPENDENT object: a distinct allocation owning its own
    # dimension-name storage with FULL write permission, so a caller may
    # reassign the result's dims without touching the receiver's dims.
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # ... and it initially carries the receiver's dimension names.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    return self
    # impl-end


def as_plain(self: CoordVar) -> CoordVar:
    # pre-conditions-start
    Requires(Acc(self.dims, 1 / 2))
    Requires(Acc(list_pred(self.dims), 1 / 2))
    # The plain re-presentation is likewise a bounded copy that always
    # returns: it MUST terminate. Measure 4 strictly dominates the sibling
    # re-presentations (constructor 1, clone 2, coordinate 3), so a caller
    # holding this obligation can still invoke any of them.
    Requires(MustTerminate(4))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.dims, 1 / 2))
    Ensures(Acc(list_pred(self.dims), 1 / 2))
    Ensures(Acc(Result().dims))
    Ensures(Acc(list_pred(Result().dims)))
    Ensures(Result() is not self)
    Ensures(Result().dims is not self.dims)
    # The plain re-presentation carries exactly the receiver's dimension names.
    Ensures(ToSeq(Result().dims) == ToSeq(self.dims))
    # post-conditions-end
    # impl-start
    base_dims = []  # type: List[int]
    j = 0
    while j < len(self.dims):
        # invariants-start
        Invariant(Acc(self.dims, 1 / 4))
        Invariant(Acc(list_pred(self.dims), 1 / 4))
        Invariant(Acc(list_pred(base_dims)))
        Invariant(0 <= j and j <= len(self.dims))
        Invariant(ToSeq(base_dims) == ToSeq(self.dims).take(j))
        # strictly decreasing measure discharges MustTerminate(4).
        Invariant(MustTerminate(len(self.dims) - j + 1))
        # invariants-end
        base_dims.append(self.dims[j])
        j = j + 1
    Assert(ToSeq(self.dims).take(len(self.dims)) == ToSeq(self.dims))
    return CoordVar(base_dims)
    # impl-end
