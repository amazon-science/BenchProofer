"""Twin-artifact model for pydata__xarray-6599.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A helper coerces the values held by one variable to floating-point numbers
  before a polynomial is evaluated over them. The coercion it performs is
  dispatched on the variable's value category ("kind"):

    * absolute-time values (a calendar timestamp, kind = TIME_POINT) are made
      numeric by measuring each timestamp as the elapsed amount since a chosen
      reference instant. This measurement is only meaningful for timestamps: it
      subtracts a reference *instant* from each value, an operation defined only
      when the values are themselves instants.

    * elapsed-duration values (a span of time, kind = TIME_SPAN) are made
      numeric by reading each duration directly as its magnitude in the base
      resolution; no reference instant is involved, because a duration is
      already a relative quantity. The resulting numbers equal the input
      magnitudes.

    * every other value category already carries numeric values and is returned
      unchanged.

The decisive property: a duration must be converted by reading its magnitude,
NOT by the instant-relative measurement reserved for timestamps -- applying the
instant-relative measurement to a duration is undefined (a span has no
reference instant to subtract). A correct helper therefore routes each kind to
the conversion defined for it.

Modelling: the underlying values are modelled as `List[int]` magnitudes in the
base resolution (the tested magnitudes are exact integers, so the
float-conversion is precision-independent; see refinement.md / mapping.md). The
value category is an `int` tag. The instant-relative measurement is the
UNCHANGED callee `elapsed_since` (axiomatized; defined only for TIME_POINT
inputs). The duration's direct magnitude read is the NEW branch, modelled
deeply as the identity on magnitudes.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *

# value-category tags
OTHER = 0       # already-numeric values: returned unchanged
TIME_POINT = 1  # absolute timestamps  (numpy datetime64; dtype.kind 'M')
TIME_SPAN = 2   # elapsed durations    (numpy timedelta64; dtype.kind 'm')


# axioms-start
@Pure
@ContractOnly
def elapsed_since(kind: int, values: PSeq[int], reference: int) -> PSeq[int]:
    """The instant-relative measurement (unchanged callee): measure each
    absolute timestamp as its elapsed magnitude since a chosen reference instant,
    i.e. the per-element subtraction of the reference. It is defined ONLY for
    timestamp inputs (kind == TIME_POINT); subtracting a reference instant from
    a value that is not itself an instant is undefined and rejected by the
    precondition. The per-element subtraction is the measurement's value only on
    well-defined magnitudes: a not-a-value sentinel magnitude (the int64 extremum
    -9223372036854775808, i.e. -2**63) is itself undefined, so the domain
    excludes it; likewise the magnitudes are within the exact-integer band of the
    base resolution (|magnitude| < 2**53) so the conversion is exact. Provenance +
    executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(kind == TIME_POINT)
    # domain: well-defined, exact-integer magnitudes only -- exclude the
    # not-a-value sentinel (the int64 extremum -2**63), for which the
    # measurement is undefined (its value is not the per-element subtraction).
    Requires(well_defined_magnitudes(values))
    Ensures(len(Result()) == len(values))
    Ensures(Forall(int, lambda k:
        (Implies(0 <= k and k < len(values),
                 Result()[k] == values[k] - reference),
         [[Result()[k]]])))
# axioms-end


# pure-start
@Pure
def well_defined_magnitudes(values: PSeq[int]) -> bool:
    """Every element is a well-defined magnitude: none is the not-a-value
    sentinel (the int64 extremum -2**63). The instant-relative measurement's
    per-element subtraction is its value only on such magnitudes; a not-a-value
    element is itself undefined, so it lies outside the measurement's domain."""
    return Forall(int, lambda k:
        (Implies(0 <= k and k < len(values),
                 values[k] != -9223372036854775808),
         [[values[k]]]))


@Pure
def magnitude_read(values: PSeq[int]) -> PSeq[int]:
    """The duration's direct magnitude read (the NEW branch), modelled deeply:
    a span is already relative, so its float magnitude equals the input
    magnitude in the base resolution. The identity on magnitudes."""
    return values
# pure-end


def coerce_values_to_float(kind: int, values: List[int], reference: int) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(values), 1 / 2))
    # the input carries exactly one value category (its dtype kind)
    Requires(kind == OTHER or kind == TIME_POINT or kind == TIME_SPAN)
    # for a timestamp input the magnitudes are well-defined instants: no
    # not-a-value sentinel (the int64 extremum -2**63), the domain on which the
    # instant-relative measurement is defined (mapping.md / axiom_check.py)
    Requires(Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values))))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(values), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    # timestamps: numeric via the instant-relative measurement -- the input
    # magnitudes are well-defined (no not-a-value sentinel), preserved into the
    # post-state since the input is read-only, so the measurement is applicable
    Ensures(Implies(kind == TIME_POINT, well_defined_magnitudes(ToSeq(values))))
    Ensures(Implies(kind == TIME_POINT,
                    ToSeq(Result()) == elapsed_since(kind, ToSeq(values), reference)))
    # durations: numeric via the direct magnitude read (NOT the instant-relative
    # measurement) -- the result equals the input magnitudes
    Ensures(Implies(kind == TIME_SPAN,
                    ToSeq(Result()) == magnitude_read(ToSeq(values))))
    Ensures(Implies(kind == TIME_SPAN, ToSeq(Result()) == ToSeq(values)))
    # already-numeric values: unchanged
    Ensures(Implies(kind == OTHER, ToSeq(Result()) == ToSeq(values)))
    # post-conditions-end
    # impl-start
    if kind == TIME_POINT:
        # numeric via the instant-relative measurement (the unchanged callee):
        # hold its result, the elapsed magnitudes since the reference instant
        measured = elapsed_since(kind, ToSeq(values), reference)
        result = []  # type: List[int]
        i = 0
        while i < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(values))
            Invariant(well_defined_magnitudes(ToSeq(values)))
            Invariant(measured == elapsed_since(kind, ToSeq(values), reference))
            Invariant(len(measured) == len(values))
            Invariant(ToSeq(result) == measured.take(i))
            # invariants-end
            result.append(measured[i])
            i = i + 1
        Assert(ToSeq(result) == measured.take(len(values)))
        Assert(measured.take(len(values)) == measured)
        return result
    elif kind == TIME_SPAN:
        # read each duration's magnitude directly (the new branch): the float
        # magnitude equals the input magnitude in the base resolution
        out = []  # type: List[int]
        j = 0
        while j < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(out)))
            Invariant(0 <= j and j <= len(values))
            Invariant(ToSeq(out) == ToSeq(values).take(j))
            # invariants-end
            out.append(values[j])
            j = j + 1
        Assert(ToSeq(out) == ToSeq(values).take(len(values)))
        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
        return out
    else:
        # already numeric: passthrough
        passthrough = []  # type: List[int]
        m = 0
        while m < len(values):
            # invariants-start
            Invariant(Acc(list_pred(values), 1 / 2))
            Invariant(Acc(list_pred(passthrough)))
            Invariant(0 <= m and m <= len(values))
            Invariant(ToSeq(passthrough) == ToSeq(values).take(m))
            # invariants-end
            passthrough.append(values[m])
            m = m + 1
        Assert(ToSeq(passthrough) == ToSeq(values).take(len(values)))
        Assert(ToSeq(values).take(len(values)) == ToSeq(values))
        return passthrough
    # impl-end
