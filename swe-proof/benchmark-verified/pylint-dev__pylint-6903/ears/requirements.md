# Requirements: robust CPU-count detection so `--jobs=0` never crashes on fractional-core containers

## Introduction

When pylint is asked to auto-detect the number of parallel jobs (for example via
`--jobs=0`), it derives a processor count from Linux control-group (cgroup)
accounting files. The helper `pylint.lint.run._query_cpu()` reads the cgroup CPU
quota/period and CPU-shares files and computes an integer count. The consumer
`pylint.lint.run._cpu_count()` combines that result with the OS-reported CPU set,
and the resulting count is ultimately used to size a `multiprocessing.Pool`.

In containerized environments (e.g. a Kubernetes pod granted only a fraction of a
single core), the accounting values can make the integer division truncate to
`0` — for example a CPU-shares value of `2` divided by the base unit `1024`
truncates to `0`. A computed count of `0` then propagates to the worker pool,
which rejects a size below `1`, so pylint aborts with an error instead of running.

The goal is that CPU-count detection never yields an unusable count of zero: when
the accounting math would truncate to zero, the reported count is raised to the
smallest usable value, one. As a result, invoking pylint with automatic job
detection completes normally rather than crashing, while all pre-existing
detection behavior for ordinary values is preserved.

The affected code is `pylint/lint/run.py`, specifically the `_query_cpu()` helper
and, by extension, `_cpu_count()` and the `pylint.lint.Run` entry point.

## Requirement 1: A determined CPU count is never zero

**User story:** As a user running pylint with automatic job detection inside a
container that exposes only a fraction of a CPU core, I want the detected
processor count to be at least one, so that pylint does not crash while sizing its
worker pool.

**Acceptance criteria**

1. WHEN `_query_cpu()` derives a processor count from the cgroup accounting files
   and that computed count equals exactly `0`, THEN `_query_cpu()` SHALL return
   `1` instead of `0`.
2. WHEN `_query_cpu()` derives a computed processor count that is greater than or
   equal to `1`, THEN `_query_cpu()` SHALL return that computed count unchanged.
3. The system SHALL never return `0` from `_query_cpu()`.
4. IF the CPU-shares accounting file is present with a strictly positive value
   whose division by the base unit `1024` truncates toward zero (for example a
   shares value of `2`), THEN `_query_cpu()` SHALL return `1` rather than `0`.

## Requirement 2: Existing accounting-branch and no-data behavior is preserved

**User story:** As a maintainer, I want the CPU detection to keep its current
results for all ordinary inputs, so that the fix changes only the degenerate
zero case and introduces no regression.

**Acceptance criteria**

1. WHEN the CPU quota file is present with a value that is neither `0` nor the
   "no quota" sentinel `-1`, and the CPU period file is present, THEN
   `_query_cpu()` SHALL compute the count as the quota divided by the period,
   truncated toward zero, before applying the minimum-of-one adjustment of
   Requirement 1.
2. WHEN the quota/period pair is not usable (quota absent, `0`, or `-1`, or the
   period file absent) and the CPU-shares file is present, THEN `_query_cpu()`
   SHALL compute the count as the shares value divided by `1024`, truncated
   toward zero, before applying the minimum-of-one adjustment of Requirement 1.
3. IF neither a usable quota/period pair nor a CPU-shares file is available, THEN
   `_query_cpu()` SHALL return an undetermined result (`None`), and SHALL NOT
   substitute `1` in that case.
4. The system SHALL keep `_cpu_count()` returning the smaller of the detected
   share count and the OS-reported CPU count when a share count is determined,
   and the OS-reported CPU count when the share count is undetermined.

## Requirement 3: Automatic job detection completes without crashing

**User story:** As a user launching pylint with `--jobs=0` in a fractional-core
container, I want the run to finish normally, so that my pipeline is not aborted
by a worker-pool sizing error.

**Acceptance criteria**

1. WHEN pylint is invoked through `pylint.lint.Run` requesting automatic job
   detection (a jobs value of `0`) in an environment whose cgroup accounting
   would otherwise yield a computed CPU count of zero, THEN the run SHALL complete
   and terminate with a success exit status rather than raising an error about
   the number of processes being below one.
2. The system SHALL supply the worker-pool sizing path with a processor count of
   at least `1` in every case where a count is determined.

## Requirement 4: Ordinary runner entry points keep working

**User story:** As a user of pylint's standard command entry points, I want them
to continue behaving exactly as before, so that this change is transparent for
normal usage.

**Acceptance criteria**

1. WHEN a standard pylint command entry point is invoked on a valid target, THEN
   it SHALL keep completing and exiting with its established success status.
2. WHEN a standard pylint command entry point is invoked with additional
   command-line arguments on a valid target, THEN it SHALL keep completing and
   exiting with its established success status.
