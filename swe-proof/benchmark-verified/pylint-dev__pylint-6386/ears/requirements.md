# Requirements: Short verbose option must not expect an argument

## Introduction

Pylint accepts a `--verbose` option that enables extra, non-checker-related
diagnostic output. This option has a short spelling, `-v`. When a user runs
pylint with the short spelling (e.g. `pylint mytest.py -v`), pylint fails with
an error saying the argument expected one value, and its generated help text
displays a placeholder value (e.g. `VERBOSE`) for the option — even though the
option is a pure on/off flag that takes no value. The long spelling
(`--verbose`) already behaves correctly and consumes no value.

The root cause lives in pylint's command-line configuration layer:

- `pylint/config/utils.py` — the early pre-pass over the raw argument vector
  (the routine that walks `args` before the main parser runs, using the table
  of options that must be handled early) only recognizes tokens that begin with
  the long-option marker (`--`), so short-spelled options are never matched
  against that table and fall through to the main parser, which for `-v`
  incorrectly demands a value.
- `pylint/lint/base_options.py` — the definition of the verbose option (and the
  enable-all-extensions option) does not suppress the value placeholder in
  generated help.
- `pylint/config/argument.py` and `pylint/config/arguments_manager.py` — the
  argument abstraction and the code that registers callable-style options with
  the underlying parser must be able to carry and forward a help-placeholder
  setting.

The goal is to make the short verbose spelling behave exactly like the long
spelling: it enables verbose mode, consumes no following value, and does not
advertise a value placeholder in help — without regressing the handling of any
other command-line option.

## Requirement 1: Short verbose spelling enables verbose mode without consuming a value

**User story:** As a pylint user, I want `-v` to behave the same as
`--verbose`, so that I can enable verbose diagnostic output with the short flag
without pylint demanding a value.

**Acceptance criteria**

1. WHEN pylint is invoked with the short verbose spelling (`-v`) and no value
   attached to it, THEN pylint SHALL enable verbose mode and proceed with the
   run instead of aborting with an "expected one argument" style error.
2. WHEN pylint runs in verbose mode as a result of the short spelling, THEN
   pylint SHALL emit the same extra non-checker-related diagnostic information
   to standard error that it emits when verbose mode is enabled via the long
   spelling.
3. The short verbose spelling SHALL be treated as a flag that takes no value:
   pylint SHALL NOT consume the token that follows `-v` as the option's value.
4. IF a token immediately following `-v` is itself an ordinary argument (for
   example a file or module path), THEN that token SHALL remain available to
   the rest of pylint (it SHALL NOT be swallowed as a value of the verbose
   flag).
5. WHEN pylint is invoked with the long verbose spelling (`--verbose`), THEN it
   SHALL continue to enable verbose mode and consume no value, exactly as
   before.

## Requirement 2: Early argument pre-pass recognizes short-spelled options

**User story:** As a maintainer, I want the early command-line pre-pass to
consider short-spelled option tokens, so that short options handled before the
main parser (such as the short verbose flag) are matched and acted upon.

**Acceptance criteria**

1. WHEN the early pre-pass walks the raw argument vector and encounters a token
   that begins with the option marker character (`-`), THEN it SHALL treat that
   token as an option candidate and attempt to match it against the table of
   options handled during the pre-pass, regardless of whether the token uses
   the single-dash short form or the double-dash long form.
2. WHEN a token does not begin with the option marker character, THEN the
   pre-pass SHALL leave it untouched and pass it through to the remaining
   arguments unchanged.
3. WHEN a token begins with the option marker character but its name is not
   present in the pre-pass table, THEN the pre-pass SHALL pass the token
   through unchanged for the main parser to handle (it SHALL NOT raise a
   pre-pass error for an unrecognized option-like token).
4. WHEN the pre-pass matches an option that takes no value yet an inline value
   was attached to it (via `=`), THEN it SHALL raise an error indicating the
   option does not accept a value.
5. WHEN the pre-pass matches an option that requires a value and no inline value
   was given and either no further token exists or the next token is itself
   option-like, THEN it SHALL raise an error indicating the option expects a
   value.

## Requirement 3: Verbose option help does not advertise a value placeholder

**User story:** As a pylint user, I want the help text for the verbose option to
show it as a valueless flag, so that I am not misled into thinking it requires a
value.

**Acceptance criteria**

1. The generated help/usage text for the verbose option SHALL NOT display a
   value placeholder for the option (no upper-cased or bracketed value token
   suggesting an argument is required).
2. The system SHALL allow an option definition to specify that no value
   placeholder be shown for that option, and this setting SHALL be forwarded
   through the argument-registration layer to the underlying parser.
3. WHEN the enable-all-extensions option is defined as a valueless flag, THEN
   its generated help text SHALL likewise show no value placeholder.

## Requirement 4: Existing command-line handling is preserved

**User story:** As a maintainer, I want all other command-line parsing behavior
to remain unchanged, so that broadening the pre-pass to recognize short options
and suppressing the verbose placeholder does not regress option validation.

**Acceptance criteria**

1. WHEN pylint is invoked with an option-like token (short- or long-spelled)
   whose name is not a recognized option, THEN pylint SHALL still report it as
   an unrecognized option, exactly as before this change; broadening the
   pre-pass to consider short tokens SHALL NOT cause an unknown short option to
   be silently accepted or to fail with a different error.
2. WHEN pylint is invoked with an option that takes a value and the supplied
   value is invalid for that option, THEN pylint SHALL still reject the value
   with the same validation error it produced before this change; the value-
   validation paths for value-taking options SHALL remain unaffected by the
   pre-pass and placeholder changes.
3. Adding the short verbose spelling to the set of options handled during the
   pre-pass and suppressing its help placeholder SHALL NOT alter how any other
   value-taking option consumes and validates its value.
4. The system SHALL continue to read configuration correctly from a properly
   formatted configuration file.
