# Requirements: linkcheck should verify local (internal) references

## Introduction

Sphinx ships a `linkcheck` builder (`sphinx/builders/linkcheck.py`) that
inspects every hyperlink reference in a documentation set and reports a status
for it. Before contacting the network, the builder performs a purely local,
network-free classification of each reference string in the worker's `check()`
routine (inside `CheckExternalLinksBuilder`).

Historically that classification only distinguished web references (those with
an `http:`/`https:` prefix, which are resolved over the network) from
everything else, which was lumped together and reported as `local` without any
verification. As a result a reference that points at a file inside the
documentation source tree was never actually checked: a dangling internal
reference was silently treated the same as a valid one.

The goal is to make the network-free classifier actually resolve references
that look like paths into the source tree — reporting them as working, ignored,
or broken as appropriate — while continuing to skip references it genuinely
cannot check (empty references, in-page anchors, mail addresses, and references
carrying an unsupported explicit URI scheme). The web-resolution path and the
report/statistics-emission machinery must keep behaving as before.

## Requirement 1: Skip references that cannot be checked locally

**User story:** As a documentation author running `linkcheck`, I want the
builder to quietly skip references that are inherently uncheckable, so that
anchors, mail links, and unsupported schemes do not produce spurious results.

**Acceptance criteria**

1. WHEN the reference string is empty, THEN the network-free classifier SHALL
   report the reference with the `unchecked` status.
2. WHEN the reference string begins with the in-page anchor prefix (`#`), THEN
   the classifier SHALL report the reference with the `unchecked` status.
3. WHEN the reference string begins with the mail-address prefix (`mailto:`),
   THEN the classifier SHALL report the reference with the `unchecked` status.
4. WHEN a reference that does not begin with `http:` or `https:` begins with an
   explicit URI scheme — one or more lowercase ASCII letters immediately
   followed by `://` (for example a transfer scheme such as an FTP URL) — THEN
   the classifier SHALL report the reference with the `unchecked` status rather
   than attempting to resolve it as a path.
5. The system SHALL classify references entirely from the reference string and
   local observations, without contacting the network, for every case covered
   by this requirement.

## Requirement 2: Resolve references that denote source-tree paths

**User story:** As a documentation author, I want references that look like
paths into the documentation source tree to actually be resolved, so that a
dangling internal reference is reported as broken instead of being ignored.

**Acceptance criteria**

1. WHEN a reference does not begin with `http:` or `https:` and does not begin
   with an explicit `<lowercase-letters>://` URI scheme, THEN the classifier
   SHALL treat the reference as a path relative to the documentation source
   directory and resolve it against that directory.
2. IF such a reference resolves to an existing file or directory within the
   source directory, THEN the classifier SHALL report the reference with the
   `working` status.
3. IF such a reference does not resolve to an existing entry in the source
   directory AND the reference matches one of the configured link-ignore
   patterns, THEN the classifier SHALL report the reference with the `ignored`
   status.
4. IF such a reference does not resolve to an existing entry in the source
   directory AND the reference matches none of the configured link-ignore
   patterns, THEN the classifier SHALL report the reference with the `broken`
   status.
5. WHEN a reference is reported as `broken`, THEN the builder SHALL record it in
   the human-readable output such that the failing reference string appears on
   its own line prefixed with the broken-status marker, so that a build that
   contains an unresolved internal reference finishes with problems.

## Requirement 3: Preserve the network web-resolution path

**User story:** As a maintainer, I want the existing web-link checking behavior
to remain unchanged, so that adding local-reference checking does not regress
external link results.

**Acceptance criteria**

1. WHEN a reference begins with `http:` or `https:`, THEN the classifier SHALL
   defer to the existing network web-resolution stage and SHALL report exactly
   the status that stage produces (`working`, `broken`, `redirected`, etc.).
2. The system SHALL keep the existing cache short-circuits for web references:
   IF a web reference is already recorded as known-good, known-broken, or
   known-redirected, THEN the classifier SHALL reuse the recorded outcome
   without re-contacting the network.
3. The system SHALL keep reporting a web reference whose URL cannot be
   retrieved (for example a not-found image URL) with the `broken` status.

## Requirement 4: Preserve unrelated linkcheck behavior and output shape

**User story:** As a maintainer, I want unrelated linkcheck features and the
result-record schema to keep working, so that existing consumers of the report
are unaffected.

**Acceptance criteria**

1. The system SHALL keep emitting one structured result record per checked
   reference, each record carrying its filename, source line number, status,
   HTTP code, reference URI, and info fields.
2. The system SHALL keep reporting the correct source line number for each
   reference as it appears in the document, including references that follow a
   newly checked internal reference.
3. The system SHALL keep honoring request authentication configuration when
   resolving web references, so that credentials are applied to matching URLs.
4. The system SHALL keep sending the configured request headers when resolving
   web references.
5. WHEN the reference set includes both checkable internal references and web
   references, THEN the builder SHALL produce exactly one result record for
   every reference in the set, so that the total number of emitted records
   equals the number of references checked.
