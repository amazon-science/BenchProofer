# Requirements: Session encoding compatibility during the Django 3.1 transition

## Introduction

Django's session framework serializes a session dictionary into a transport
string and later reads it back. In an earlier change the serialized session
format was updated, which broke deployments that run several instances of the
same project side by side while migrating between release lines: an instance
using the new format writes session data that an instance still on the old code
cannot read.

The project already exposes a configuration setting,
`settings.DEFAULT_HASHING_ALGORITHM`, intended to keep such transitions
compatible. The affected code lives in the session base class
`django.contrib.sessions.backends.base.SessionBase`, specifically its
`encode()` method (used by every session backend when persisting session data)
and the pre-3.1 read path `_legacy_decode()`. Before this change, `encode()`
unconditionally produced the new format, so selecting the legacy hashing
algorithm did not restore the old, interchangeable serialized format.

The goal is to make `encode()` produce the older pre-3.1 interchange format
whenever the deployment has opted into the legacy hashing algorithm, so that a
value written by a new-code instance in that mode can be read by the matching
legacy read path, while leaving normal (non-legacy) behavior unchanged.

## Requirement 1: Legacy-format session encoding under the compatibility setting

**User story:** As an operator running multiple instances of one project during
a Django upgrade, I want session data to be serialized in the older
interchange format when I opt into the legacy hashing algorithm, so that
instances on both release lines can read each other's session data.

**Acceptance criteria**

1. WHEN `SessionBase.encode()` is called AND `settings.DEFAULT_HASHING_ALGORITHM`
   equals `'sha1'`, THEN `encode()` SHALL return the session data serialized in
   the pre-3.1 interchange format (the format the pre-3.1 read path accepts),
   rather than the current signing-based format.
2. WHEN encoding in the legacy-format case, THEN the produced value SHALL be the
   base64 encoding of the message-authentication hash of the serialized session
   payload, a `:` separator, and the serialized session payload, using the same
   serializer and the same hashing scheme that the pre-3.1 read path
   (`_legacy_decode()`) expects, so that the two are mutually consistent.
3. WHEN a session dictionary is encoded while `DEFAULT_HASHING_ALGORITHM` equals
   `'sha1'` and the resulting string is then decoded via `SessionBase.decode()`,
   THEN decoding SHALL return a dictionary equal to the original session
   dictionary.
4. The system SHALL produce, in the legacy-format case, output that
   `SessionBase.decode()` accepts through its pre-3.1 fallback path without
   raising, and that yields the original session data.

## Requirement 2: Standard encoding preserved outside the compatibility setting

**User story:** As a developer on a normally configured project, I want session
encoding to keep using the current format when I have not opted into the legacy
algorithm, so that default behavior and security are unchanged.

**Acceptance criteria**

1. WHEN `SessionBase.encode()` is called AND `settings.DEFAULT_HASHING_ALGORITHM`
   does not equal `'sha1'`, THEN `encode()` SHALL return the session data in the
   current signing-based serialized format (unchanged from prior behavior).
2. The chosen serialized format SHALL be determined solely by whether
   `settings.DEFAULT_HASHING_ALGORITHM` equals `'sha1'`; no other input SHALL
   change which of the two formats is produced.
3. WHEN a session dictionary is encoded with `DEFAULT_HASHING_ALGORITHM` set to a
   non-legacy value and the result is decoded via `SessionBase.decode()`, THEN
   decoding SHALL return a dictionary equal to the original session dictionary.

## Requirement 3: Regression protection for existing session behavior

**User story:** As a Django user, I want all pre-existing session behavior to
keep working, so that adding the compatibility path introduces no regressions.

**Acceptance criteria**

1. The system SHALL keep `SessionBase.decode()` able to read values produced in
   the current signing-based format, returning the original session dictionary.
2. The system SHALL keep `SessionBase.decode()` able to read values produced in
   the pre-3.1 interchange format, returning the original session dictionary.
3. IF `SessionBase.decode()` is given data it cannot authenticate or parse in
   either format, THEN it SHALL return an empty session dictionary rather than
   propagating an exception, and SHALL log tampering-style failures to the
   security logger as before.
4. The system SHALL keep all session container operations (storing, retrieving,
   updating, popping, clearing, key membership, iteration over keys/values/items,
   default handling, expiry configuration, cycling, flushing, and saving) behaving
   as before across every session backend (cookie, cache, cache+db, file, and
   database backends, including custom database and time-zone variants).
5. The behavior described in Requirement 1 and Requirement 2 SHALL hold
   identically regardless of which session backend performs the encoding.
