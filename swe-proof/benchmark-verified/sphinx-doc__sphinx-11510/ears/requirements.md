# Requirements: `source-read` event must reach the text of included files

## Introduction

Sphinx exposes a `source-read` event that lets extensions rewrite the text of a
source document before it is parsed. Extensions register a handler with
`app.connect("source-read", handler)`; the handler is invoked with the
application, the document name, and a single-element list holding the source
text, and it may replace that text in place (`source[0] = ...`).

When one document pulls in the contents of another through the `include`
directive (Sphinx's `Include` directive in `sphinx/directives/other.py`, which
extends the docutils `Include` directive), the included text historically
bypassed the `source-read` event: the top-level document's text was offered to
registered handlers, but the text drawn in by an `include` was parsed verbatim,
so any rewrite an extension performed never reached the final output for
included content.

The goal is to make the `Include` directive offer the text of each included
(RST-parsed) file to the `source-read` event before that text is parsed, so
that a registered handler's rewrite of included content is reflected in the
resulting document tree — including content brought in through nested includes —
while leaving the behavior unchanged when no such handler is registered and for
includes that are not parsed as RST.

## Requirement 1: Offer included RST text to the `source-read` event

**User story:** As a Sphinx extension author, I want the `source-read` event to
fire for the contents of files brought in via the `include` directive, so that
my search-and-replace (or other) rewrites apply to included content just as they
do to top-level source files.

**Acceptance criteria**

1. WHEN the `Include` directive processes a file that is parsed as
   reStructuredText and at least one `source-read` handler is registered, THEN
   the directive SHALL emit the `source-read` event with the included file's
   text before that text is parsed.
2. WHEN the `source-read` event is emitted for an included file, THEN the
   directive SHALL pass the document name derived from the included file's path
   (via the environment's path-to-docname derivation) as the event's document
   name argument.
3. WHEN the `source-read` event is emitted for an included file, THEN the
   directive SHALL pass the included file's text as a single-element mutable
   list, matching the calling convention already used for the `source-read`
   event on top-level documents, so that a handler may replace the text in
   place.
4. WHEN a `source-read` handler replaces the included file's text, THEN the
   directive SHALL parse the handler-provided (rewritten) text rather than the
   original included text.
5. WHEN no `source-read` handler rewrites the text, THEN the directive SHALL
   parse text equivalent to the originally included content (the event's
   presence SHALL NOT by itself alter the included content).

## Requirement 2: Offer the included content itself and preserve its structure

**User story:** As a Sphinx extension author, I want the text offered to my
`source-read` handler for an included file to be that file's own textual content
— not the include machinery's internal bookkeeping — and I want my rewrite to be
parsed with the same line and block structure as the original, so that parsing,
error reporting, and source provenance continue to work correctly.

**Acceptance criteria**

1. WHEN the directive emits the `source-read` event for an included file, THEN
   the text offered to handlers SHALL be that file's source content as it would
   be inserted at that point (reflecting any inclusion options such as a
   selected line range), and SHALL NOT contain any internal line-tracking or
   provenance bookkeeping that the include machinery attaches around the
   content.
2. WHEN a `source-read` handler examines the text offered for an included file,
   THEN that text SHALL consist of exactly the content that would otherwise be
   parsed for that inclusion, with no additional leading or trailing lines
   beyond that content.
3. WHEN a `source-read` handler rewrites included content, THEN the directive
   SHALL parse the rewritten content with the same physical-line and
   paragraph/block boundaries that the original content would have produced, so
   that multi-line and list structure is preserved (no lines merged, dropped, or
   shifted).
4. WHEN the directive parses the included content after the `source-read` event,
   THEN the source-location and provenance information for that content SHALL be
   preserved, so that source-location reporting for the included content is the
   same as when no handler is registered.

## Requirement 3: Do not emit `source-read` for content not parsed as RST

**User story:** As a documentation author, I want literal (verbatim) includes to
remain untouched, so that inserting plain-text or code content does not trigger
source rewriting that only makes sense for reStructuredText.

**Acceptance criteria**

1. WHEN a file is included as literal or verbatim content (i.e. inserted without
   reStructuredText parsing), THEN the directive SHALL NOT emit a `source-read`
   event for that file's content.
2. The system SHALL emit the `source-read` event only for included content that
   is parsed as reStructuredText.

## Requirement 4: Apply the event to nested includes

**User story:** As an extension author, I want my `source-read` rewrite to reach
content that is itself included by an included file, so that deeply composed
documentation is transformed consistently at every level.

**Acceptance criteria**

1. WHEN an included file itself includes a further reStructuredText file, THEN
   the directive SHALL emit the `source-read` event for that nested file's text
   before it is parsed.
2. WHEN a `source-read` handler rewrites nested included content, THEN the
   resulting document tree SHALL reflect the rewritten text for that nested
   content.

## Requirement 5: Preserve existing behavior when no handler is registered

**User story:** As a Sphinx user without any `source-read` extension, I want the
`include` directive to behave exactly as before, so that this change introduces
no regression in ordinary builds.

**Acceptance criteria**

1. IF no `source-read` handler is registered, THEN the directive SHALL parse the
   included content exactly as received, without emitting a `source-read` event
   for included files.
2. The system SHALL preserve the `Include` directive's existing path handling
   for included files, including resolving paths relative to the source
   directory and recording included files for rebuild tracking.
3. The change SHALL be confined to how the `Include` directive routes included
   RST text through the `source-read` event; WHEN any other directive (such as
   directives unrelated to `include`) is processed, THEN its behavior SHALL
   remain exactly as it was before this change.
