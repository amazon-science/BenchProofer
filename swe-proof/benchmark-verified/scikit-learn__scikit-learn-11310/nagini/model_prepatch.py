"""Twin-artifact model for scikit-learn__scikit-learn-11310.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A search procedure, after selecting the best configuration, may fit the chosen
  model once more on the whole data. When (and only when) this final fit is
  performed, the procedure must report the wall-clock duration of that final fit
  as a single real-valued measurement, obtained by reading the clock immediately
  before the fit begins and immediately after it ends and reporting the elapsed
  interval between the two readings (later reading minus earlier reading).

  The two readings are modelled as the inputs `start` (the reading taken before
  the fit) and `end` (the reading taken after it). Because wall-clock time does
  not run backwards, the later reading is never earlier than the earlier one;
  this is the precondition `end >= start`.

  The guarantees the issue demands:

    (1) the reported duration is present exactly when the final fit is performed
        (and is the absent marker, None, when it is not performed); and

    (2) whenever it is present it is precisely the elapsed real-valued interval
        between the two readings (the later reading minus the earlier reading) —
        a genuine real-valued measurement, not an arbitrary stand-in. As a
        consequence it is a non-negative real number, since the reading taken
        after the fit is never earlier than the reading taken before it,
        including the boundary where no measurable time passed.

Clock readings and the reported duration are interpreted real numbers (verified
with `--float-encoding=real`); whether the final fit happens is a bool, and the
absent marker is None (`Optional[float]`).

Two unchanged operations are axiomatized as `@Pure @ContractOnly` callees:

  * the wall-clock reading — the property modelled is its monotonicity across two
    sequential calls: a reading taken after a reference instant is never earlier
    than that instant (this is what justifies the precondition `end >= start`);
    and
  * the elapsed-interval (the difference of two readings) — the property
    consumed by the proof is that the difference of an ordered pair (the later
    minus the earlier reading) is a non-negative real value; the reported
    duration is pinned to exactly this real-valued difference.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List, Optional
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
@Pure
@ContractOnly
def clock_after(reference: float) -> float:
    """Wall-clock reading (the unchanged stdlib timer) taken at or after a
    reference instant. The property modelled is monotonicity: wall-clock time
    does not run backwards, so a reading taken after `reference` is never earlier
    than it. This is what justifies the `end >= start` ordering of the two
    bracketed readings (the inputs of `recorded_refit_duration`).
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Ensures(Result() >= reference)


@Pure
@ContractOnly
def elapsed_between(earlier: float, later: float) -> float:
    """The elapsed real-valued interval between two ordered clock readings (the
    later one minus the earlier one). The property the proof relies on is that,
    for an ordered pair, this difference is a non-negative real value. Weakest
    sound contract on real subtraction of two ordered readings.
    Provenance + executable soundness check: mapping.md / axiom_check.py.
    """
    Requires(later >= earlier)
    Ensures(Result() >= 0.0)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour.)
# pure-end


def recorded_refit_duration(do_final_fit: bool, start: float, end: float) -> Optional[float]:
    # pre-conditions-start
    # `start` is the reading taken before the final fit may begin and `end` the
    # reading taken after it ends. Wall-clock time does not run backwards, so the
    # later reading is never earlier than the earlier one (timer monotonicity,
    # modelled by `clock_after`): `end >= start`.
    Requires(end >= start)
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    # (1) the duration is reported exactly when the final fit is performed, and
    # is the absent marker otherwise.
    Ensures(do_final_fit == (Result() is not None))
    # (2) whenever a duration is reported it is precisely the elapsed real-valued
    # interval between the two readings (the later reading minus the earlier
    # one). This pins the result to the genuine real-valued measurement, so it
    # cannot be discharged by an arbitrary non-real or constant stand-in; as a
    # consequence it is a non-negative real number (including a zero-length
    # interval).
    Ensures(Implies(Result() is not None, Result() == elapsed_between(start, end)))
    # post-conditions-end
    # impl-start
    # PRE-PATCH SKELETON: the final fit on the whole data is performed, but its
    # wall-clock duration is never read or reported — the reported value stays
    # absent even when the final fit happens.
    result = None  # type: Optional[float]
    if do_final_fit:
        # ... the final fit on the whole data happens here (opaque work) ...
        pass
    return result
    # impl-end
