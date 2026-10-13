# Requirements: correct `:kbd:` role rendering for separator keystrokes

## Introduction

Sphinx's HTML builder renders the `:kbd:` inline role into nested `<kbd>`
elements: a compound keystroke such as `Control+X` becomes an outer `<kbd>`
wrapper containing one inner `<kbd>` element per keystroke, with the literal
separator characters left as plain text between the inner elements. This
splitting is performed by the `KeyboardTransform` post-transform in
`sphinx/builders/html/transforms.py`, which operates on the `literal` nodes
carrying the `kbd` class.

The transform currently treats every `-`, `+`, `^`, or run of whitespace as a
keystroke separator, regardless of position. This is wrong when one of those
characters is itself a keystroke rather than a joiner. A standalone `:kbd:`-``
is rendered as a separator sitting between two empty keystrokes, and a compound
keystroke that ends in (or otherwise uses) one of these characters as a real key
(for example `Shift-+`, whose final keystroke is the `+` character) is
mis-split, producing spurious empty `<kbd>` elements.

The goal is to make the transform distinguish separators from keystroke
characters by position: a `-`, `+`, `^`, or whitespace run only acts as a
separator when it has keystroke content on **both** sides. This must fix the
broken cases while preserving the existing correct rendering of ordinary
compound and single keystrokes.

## Requirement 1: Standalone keystroke consisting of a separator character

**User story:** As a documentation author, I want `:kbd:` with a single
keystroke that happens to be `-`, `+`, or `^` to render as one key, so that a
lone separator-like key is displayed correctly instead of as blanks around a
divider.

**Acceptance criteria**

1. WHEN a `kbd`-classed literal node contains text that has no separator with a
   character on both sides of it, THEN the transform SHALL leave the node with a
   single keystroke whose text is exactly the original text, adding no nested
   `<kbd>` child elements.
2. WHEN the keystroke text is exactly `-`, `+`, or `^`, THEN the rendered output
   SHALL be a single `<kbd>` element whose text content is that one character.
3. The system SHALL NOT emit any empty keystroke element (a `<kbd>` element with
   no text) for a standalone separator-character keystroke.

## Requirement 2: Separators only split when surrounded by keystroke content

**User story:** As a documentation author, I want compound keystrokes to be
split only at genuine joiners, so that a `-`, `+`, or `^` that is itself a key
(including at the start or end of the specification) is kept with its keystroke.

**Acceptance criteria**

1. WHEN the keystroke text contains a `-`, `+`, or `^` character that has at
   least one character both immediately before it and immediately after it,
   THEN the transform SHALL treat that character as a separator: it SHALL split
   the text there, emitting the preceding text as a keystroke element and the
   separator character as plain text between keystroke elements.
2. IF a `-`, `+`, or `^` character appears at the very beginning of the
   keystroke text (no character before it), THEN the transform SHALL NOT treat
   it as a separator and SHALL keep it as part of the following keystroke text.
3. IF a `-`, `+`, or `^` character appears at the very end of the keystroke text
   (no character after it), THEN the transform SHALL NOT treat it as a separator
   and SHALL keep it as part of the preceding keystroke text.
4. WHEN the text is a compound keystroke whose final keystroke is itself a
   single separator character (a `-`, `+`, or `^` appearing as the last
   character, immediately preceded by an interior joiner), THEN the transform
   SHALL produce a keystroke element for the leading key(s), each interior
   joiner as plain text, and a final keystroke element whose text is that
   trailing separator character — and SHALL NOT produce an empty trailing
   keystroke element.

## Requirement 3: Whitespace as a separator, by position

**User story:** As a documentation author, I want whitespace-joined keystrokes
(such as `M-x  M-y`) to keep splitting on whitespace runs, so that existing
Emacs-style key sequences continue to render as before.

**Acceptance criteria**

1. WHEN a run of whitespace appears with keystroke content on both sides, THEN
   the transform SHALL treat that whitespace run as a separator, splitting the
   surrounding text into separate keystroke elements with the whitespace kept as
   the plain-text separator between them.
2. IF a whitespace run occurs at the very start or the very end of the keystroke
   text (with no keystroke content on the far side), THEN the transform SHALL
   NOT treat it as a boundary that creates an empty keystroke element.

## Requirement 4: Preserve existing compound-keystroke rendering (regression)

**User story:** As a documentation author, I want ordinary compound keystrokes
to render exactly as they did before, so that fixing the edge cases does not
regress common usage.

**Acceptance criteria**

1. WHEN the keystroke text is an ordinary compound keystroke whose separators
   each have keystroke content on both sides (for example `Control+X`), THEN the
   transform SHALL wrap the whole thing in an outer `<kbd>` element containing
   one inner `<kbd>` element per keystroke, with each separator character emitted
   as plain text between the inner elements, in original left-to-right order.
2. WHEN the keystroke text is a single ordinary keystroke with no separator (for
   example `space`), THEN the transform SHALL keep it as a single keystroke with
   its text unchanged and add no nested keystroke elements.
3. The system SHALL keep splitting whitespace-joined key sequences (for example
   `M-x  M-y`) into their constituent keystrokes as it did previously.
4. The transform SHALL continue to apply only to `literal` nodes carrying the
   `kbd` class and only for the HTML builder, leaving other roles and other
   builders unaffected.
5. The system SHALL preserve the CSS classes on the emitted keystroke elements
   so that the rendered `<kbd>` markup keeps its existing styling classes.
