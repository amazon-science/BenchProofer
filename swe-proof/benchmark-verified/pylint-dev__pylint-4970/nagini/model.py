"""Twin-artifact model for pylint-dev__pylint-4970.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A duplicate-code search is parameterised by a non-negative threshold giving
  the minimum number of successive lines that two chunks must share to count as
  a duplication. The standalone entry point produces a report and writes it to
  its output buffer.

  The threshold acts as an ENABLE switch: a threshold of zero means the search
  is disabled, so the entry point produces no report at all (its output stays
  empty). For any positive threshold the search runs and the entry point writes
  the whole report it produces to the output buffer.

The report and the emitted output are modelled as sequences of integers (each
integer standing for one emitted record; for a positive threshold the report is
always non-empty because it always carries a summary record). The report is a
read-only input describing what the display step would write; the output buffer
is the only mutated object, and for a positive threshold it ends up equal to the
report (the display step writes the report out verbatim, in order).

The entry point is a bounded dispatch-and-copy: it MUST terminate, by either
returning immediately (zero threshold) or writing the finite report out (a
total-correctness obligation, carried as MustTerminate in the precondition).
An implementation that diverges — e.g. hangs before displaying at a positive
threshold — would satisfy the value postconditions only vacuously and would
hang every positive-threshold run (all the P2P duplicate-detection tests)
forever.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


# axioms-start
# (no axioms: the changed function calls only its own unchanged sibling helpers,
#  which are modelled directly as the precomputed-findings input and the deep
#  emit operation; there is no external opaque callee whose contract the proof
#  consumes.)
# axioms-end


# pure-start
# (no pure helpers needed: the emitted content is the findings sequence itself.)
# pure-end


class Search:
    def __init__(self) -> None:
        Ensures(Acc(self.min_lines) and self.min_lines == 0)  # type: ignore[name-defined]
        Ensures(Acc(self.output) and Acc(list_pred(self.output)))  # type: ignore[name-defined]
        Ensures(len(self.output) == 0)  # type: ignore[name-defined]
        self.min_lines = 0  # type: int
        self.output = []  # type: List[int]


def emit(self: Search, report: List[int]) -> None:
    # pre-conditions-start
    # The threshold and the read-only report the display step would write are
    # the inputs; only the output buffer is mutated. For a positive threshold
    # the report is always non-empty (it always carries a summary record), which
    # is the regime in which the display step actually runs.
    Requires(Acc(self.min_lines))
    Requires(self.min_lines >= 0)
    Requires(Acc(self.output) and Acc(list_pred(self.output)))
    Requires(len(self.output) == 0)
    Requires(Acc(list_pred(report), 1 / 2))
    Requires(Implies(self.min_lines > 0, len(report) > 0))
    # The entry point is a bounded dispatch-and-copy: it MUST terminate
    # (return at once or finish writing the finite report) — total
    # correctness. A diverging impl (e.g. hanging before the display at a
    # positive threshold) would satisfy the value postconditions only
    # vacuously and hang every positive-threshold run (the P2P tests).
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.min_lines))
    Ensures(self.min_lines == Old(self.min_lines))
    Ensures(Acc(self.output) and Acc(list_pred(self.output)))
    # Report stays read-only (fractional permission preserved).
    Ensures(Acc(list_pred(report), 1 / 2))
    # Threshold zero disables the search: nothing is emitted, output stays empty.
    Ensures(Implies(self.min_lines == 0, len(self.output) == 0))
    # A positive threshold runs the search and writes the whole report out,
    # verbatim and in order; that report is non-empty.
    Ensures(Implies(self.min_lines > 0, ToSeq(self.output) == ToSeq(report)))
    Ensures(Implies(self.min_lines > 0, len(self.output) > 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
