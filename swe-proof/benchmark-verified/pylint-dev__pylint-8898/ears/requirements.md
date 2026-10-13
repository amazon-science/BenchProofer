# Requirements: comma-separated regular-expression options must preserve commas inside quantifiers

## Introduction

Several pylint configuration options accept a **comma-separated list of regular
expressions** (for example `bad-names-rgxs`). These values are parsed by the
comma-separated-regexp transformer in `pylint/config/argument.py`
(`_regexp_csv_transfomer`), which delegates the string-splitting step to a
helper in `pylint/utils/utils.py`.

The current splitting step treats **every** comma as a list separator. That is
wrong for regular expressions, because a comma is also meaningful *inside* a
regex brace quantifier such as `{1,3}`. When such a quantifier
appears in the value, the comma inside the braces is used as a separator, the
brace group is torn in half, and the resulting fragments are no longer valid
regular expressions. Compiling a fragment then raises `re.error`, which
surfaces as an uncaught crash during configuration parsing.

The goal is to make the splitting rule brace-aware: a comma that lies inside an
open brace group is part of the pattern and must not split the list, while a
comma outside any brace group continues to separate list items. Individual
regexes that are genuinely invalid must still be reported with a clear error.

## Requirement 1: Split a regexp list only on top-level commas

**User story:** As a pylint user, I want to put a regular expression containing
a brace quantifier (e.g. one written `foo{1,3}`) into a comma-separated regexp
option, so that the comma inside the quantifier is kept as part of my pattern
instead of splitting it into pieces.

**Acceptance criteria**

1. WHEN the comma-separated-regexp transformer in `pylint/config/argument.py`
   receives a string value, THEN it SHALL split that string into pattern items
   using only commas that occur while no brace group is open.
2. WHILE scanning the string left to right, the splitter SHALL treat a `{`
   character as opening a brace group and a `}` character as closing the
   currently open brace group.
3. IF a `}` character is encountered while no brace group is open, THEN the
   splitter SHALL treat it as an ordinary character (it SHALL NOT change the
   open/closed state).
4. WHEN a comma is encountered while a brace group is open, THEN the splitter
   SHALL treat that comma as an ordinary character belonging to the current
   pattern item, not as a list separator.
5. WHEN a comma is encountered while no brace group is open, THEN the splitter
   SHALL end the current pattern item and begin a new one.
6. WHEN the value is a single regex containing a brace quantifier and no
   top-level comma (for example a value written `foo{1,3}`), THEN the splitter
   SHALL produce exactly one pattern item whose text is the entire value,
   preserving the comma inside the quantifier.

## Requirement 2: Trim whitespace and drop empty items

**User story:** As a pylint user, I want to write my regexp list with spaces
after the commas for readability, so that the surrounding whitespace does not
become part of my patterns.

**Acceptance criteria**

1. WHEN the splitter produces a pattern item, THEN it SHALL remove leading and
   trailing whitespace from that item before the item is compiled.
2. WHEN a separator is found but no characters were collected for the item at
   that position, THEN the splitter SHALL contribute no pattern item for that
   position.
3. WHEN two patterns are separated by a top-level comma followed by one or more
   spaces, THEN the splitter SHALL produce exactly those two items with the
   inter-item whitespace removed from each.
4. WHEN two patterns are separated by a top-level comma with no surrounding
   spaces, THEN the splitter SHALL produce exactly those two items unchanged.
5. WHEN the value contains no top-level comma, THEN the splitter SHALL produce
   exactly one item consisting of the whole (whitespace-trimmed) value.
6. WHEN a top-level comma separates a plain pattern from a pattern that itself
   contains an in-brace comma, THEN the splitter SHALL produce exactly two
   items: the plain pattern and the brace-containing pattern with its in-brace
   comma preserved.

## Requirement 3: Compile each item and preserve the parsed result

**User story:** As a pylint user, I want each comma-separated regexp option to
end up as the list of compiled patterns I intended, so that options such as
`bad-names-rgxs` behave the way the individual regexes describe.

**Acceptance criteria**

1. WHEN the splitter has produced the list of pattern items, THEN the
   transformer SHALL compile each item into a regular-expression pattern and
   SHALL return the compiled patterns in the same order as the items appeared
   in the input.
2. WHEN a value for a comma-separated regexp option (such as `bad-names-rgxs`)
   is provided on the command line or in a configuration file and every item is
   a valid regular expression, THEN configuration initialization SHALL complete
   successfully and the option's stored value SHALL equal the list of patterns
   obtained by compiling each split item.
3. WHEN the transformer receives a value that is already a list or tuple of
   strings (rather than a single string), THEN it SHALL treat each element as a
   pattern item without performing any comma splitting.

## Requirement 4: Report genuinely invalid regexes clearly

**User story:** As a pylint user, I want a clear error when one of my regexes is
actually malformed, so that I can fix the offending pattern.

**Acceptance criteria**

1. IF a split pattern item is not a valid regular expression, THEN the
   transformer SHALL raise an argument-type error rather than allowing an
   uncaught exception to propagate from the regex engine.
2. WHEN such an error is raised, THEN its message SHALL identify the offending
   pattern text, the index within that pattern at which the problem begins, and
   the reason reported by the regular-expression engine.
3. IF an invalid regexp is supplied for such an option during a normal run,
   THEN pylint SHALL terminate the process (exit) rather than continue.
4. WHEN brace-aware splitting yields a pattern item that contains an in-brace
   comma and is itself an invalid regular expression, THEN the error message
   SHALL report that whole item's text as split — that is, the item text SHALL
   NOT be truncated at the comma inside its brace group.

## Requirement 5: Keep existing comma-separated and single-regex behavior

**User story:** As a maintainer, I want the fix to preserve the previously
correct behavior of regexp options, so that lists without brace commas and
single-regex validation keep working.

**Acceptance criteria**

1. The system SHALL keep splitting a plain comma-separated list of regexes that
   contains no brace quantifiers into the same items as before (a comma between
   two top-level patterns still separates them).
2. The system SHALL keep raising an error (and exiting on a normal run) when a
   single regexp option is given a value that is not a valid regular
   expression.
3. The system SHALL keep reporting an unknown option, unknown message id,
   unknown confidence value, invalid yes/no value, and invalid target Python
   version with their existing error messages, so that this change affects only
   the parsing of comma-separated regexp values.
