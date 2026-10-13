# Requirements: Include the rejected value in validator ValidationErrors

## Introduction

Django's built-in validators live in `django/core/validators.py`. When a
validator rejects its input it raises a `django.core.exceptions.ValidationError`
carrying a message, an error `code`, and an optional `params` mapping. The
`params` mapping supplies named substitutions (e.g. `%(limit_value)s`,
`%(max)s`, `%(extension)s`) that a caller-customized error message can
interpolate.

Callers cannot currently reference the rejected input itself in a custom
message, because most validators do not put that input into `params`. The goal
is to make every built-in validator that raises a `ValidationError` include the
rejected input under the substitution name `value`, so an application that
overrides a validator's error message may use a `%(value)s` placeholder and have
it resolve to the exact value that was rejected.

A related cleanup lives in `django/forms/fields.py`: `DecimalField` performed a
redundant non-finite check in its own `validate` method, duplicating what
`DecimalValidator` already detects. That duplicate check raised a
`ValidationError` without the `value` in `params`, so it must no longer shadow
the validator's error path; the non-finite rejection must be produced by
`DecimalValidator` (which carries `value`) instead.

Behaviorally, the observable effect throughout is: when a field is configured
with a custom error message consisting solely of the `%(value)s` placeholder,
the reported form error for a rejected input equals the string form of that
input.

## Requirement 1: RegexValidator supplies the rejected value

**User story:** As a developer customizing a regex validator's error message, I
want the rejected value available to the message, so that I can echo the bad
input back to the user.

**Acceptance criteria**
1. WHEN `RegexValidator.__call__` determines the input is invalid (it fails to
   match, or matches under `inverse_match`), THEN the raised `ValidationError`
   SHALL carry a `params` mapping whose `value` entry equals the value passed to
   the validator.
2. The system SHALL keep the existing message and `code` of that
   `ValidationError` unchanged.
3. WHEN validators built on `RegexValidator` reject input — including
   `validate_slug`, `validate_unicode_slug`, `validate_integer` /
   `integer_validator`, and the validators produced by `int_list_validator`
   (such as `validate_comma_separated_integer_list`) — THEN the resulting
   `ValidationError` SHALL likewise expose the rejected value under `value`.

## Requirement 2: URLValidator supplies the rejected value on every rejection path

**User story:** As a developer validating URLs, I want the rejected URL echoed
in a custom error message, so that error output is specific.

**Acceptance criteria**
1. WHEN `URLValidator.__call__` rejects input because it is not a string, THEN
   the raised `ValidationError` SHALL carry `value` equal to the input.
2. WHEN `URLValidator.__call__` rejects input because the scheme is not among the
   allowed schemes, THEN the raised `ValidationError` SHALL carry `value` equal
   to the input.
3. WHEN `URLValidator.__call__` rejects input because the URL cannot be split
   (for example an invalid IPv6 URL), THEN the raised `ValidationError` SHALL
   carry `value` equal to the input.
4. WHEN `URLValidator.__call__` rejects input because the bracketed IPv6 literal
   in the host is not a valid IPv6 address, THEN the raised `ValidationError`
   SHALL carry `value` equal to the input.
5. WHEN `URLValidator.__call__` rejects input because the network location
   exceeds the maximum host length, THEN the raised `ValidationError` SHALL carry
   `value` equal to the input.
6. IF the input to `URLValidator.__call__` is not of a type its checks expect
   (for example an integer rather than a string), THEN the validator SHALL still
   reject it and the raised `ValidationError` SHALL carry `value` equal to that
   input.
7. The system SHALL keep the message and `code` of each such `ValidationError`
   unchanged.

## Requirement 3: EmailValidator supplies the rejected value

**User story:** As a developer validating email addresses, I want the rejected
address echoed in a custom message.

**Acceptance criteria**
1. WHEN `EmailValidator.__call__` rejects input because it is empty or lacks an
   `@`, THEN the raised `ValidationError` SHALL carry `value` equal to the input.
2. WHEN `EmailValidator.__call__` rejects input because the user part fails to
   match, THEN the raised `ValidationError` SHALL carry `value` equal to the
   input.
3. WHEN `EmailValidator.__call__` rejects input because the domain part is
   invalid (including after the IDN punycode attempt), THEN the raised
   `ValidationError` SHALL carry `value` equal to the input.
4. The system SHALL keep the message and `code` of each such `ValidationError`
   unchanged, and SHALL continue to accept inputs it previously accepted.

## Requirement 4: IP-address validators supply the rejected value

**User story:** As a developer validating IP addresses, I want the rejected
address echoed in a custom message.

**Acceptance criteria**
1. WHEN `validate_ipv4_address` rejects input, THEN the raised `ValidationError`
   SHALL carry `value` equal to the input, retaining code `invalid`.
2. WHEN `validate_ipv6_address` rejects input, THEN the raised `ValidationError`
   SHALL carry `value` equal to the input, retaining code `invalid`.
3. WHEN `validate_ipv46_address` rejects input (neither a valid IPv4 nor IPv6
   address), THEN the raised `ValidationError` SHALL carry `value` equal to the
   input, retaining code `invalid`.

## Requirement 5: DecimalValidator supplies the rejected value on every rejection

**User story:** As a developer validating decimal numbers, I want the rejected
number echoed in a custom message across all decimal failure kinds.

**Acceptance criteria**
1. WHEN `DecimalValidator.__call__` rejects a non-finite value (exponent
   indicating infinity or NaN), THEN the raised `ValidationError` SHALL carry
   `value` equal to the input AND SHALL carry code `invalid`.
2. WHEN `DecimalValidator.__call__` rejects input for exceeding the maximum total
   number of digits, THEN the raised `ValidationError` SHALL carry both its
   existing `max` entry and a `value` entry equal to the input, retaining code
   `max_digits`.
3. WHEN `DecimalValidator.__call__` rejects input for exceeding the maximum
   number of decimal places, THEN the raised `ValidationError` SHALL carry both
   its existing `max` entry and a `value` entry equal to the input, retaining
   code `max_decimal_places`.
4. WHEN `DecimalValidator.__call__` rejects input for exceeding the maximum
   number of whole digits, THEN the raised `ValidationError` SHALL carry both its
   existing `max` entry and a `value` entry equal to the input, retaining code
   `max_whole_digits`.

## Requirement 6: DecimalField must not shadow the validator's non-finite rejection

**User story:** As a developer using a form `DecimalField` with a custom
`invalid` message, I want a non-finite input's error to expose the rejected
value.

**Acceptance criteria**
1. WHEN a form `DecimalField` (in `django/forms/fields.py`) cleans a non-finite
   value such as `NaN`, THEN the `invalid`-coded `ValidationError` surfaced for
   that field SHALL be the one produced by `DecimalValidator`, so that its
   `params` include `value` equal to the input.
2. The system SHALL NOT perform a separate, duplicate non-finite check in
   `DecimalField` that raises an `invalid` `ValidationError` without the `value`
   parameter.
3. The system SHALL keep rejecting non-finite decimal inputs (the value is still
   invalid) — the change concerns only which code path reports it, not whether it
   is rejected.

## Requirement 7: FileExtensionValidator supplies the rejected value

**User story:** As a developer validating uploaded file extensions, I want the
rejected file identified in a custom message.

**Acceptance criteria**
1. WHEN `FileExtensionValidator.__call__` rejects a file whose extension is not
   allowed, THEN the raised `ValidationError` SHALL carry, in addition to its
   existing `extension` and `allowed_extensions` entries, a `value` entry equal
   to the input value passed to the validator (the file object, whose string form
   is its name).
2. The system SHALL keep the message and code (`invalid_extension`) unchanged.
3. WHEN `validate_image_file_extension` rejects a file, THEN the resulting
   `ValidationError` SHALL likewise expose the rejected value, since it delegates
   to `FileExtensionValidator`.

## Requirement 8: ProhibitNullCharactersValidator supplies the rejected value

**User story:** As a developer prohibiting null characters, I want the rejected
input echoed in a custom message.

**Acceptance criteria**
1. WHEN `ProhibitNullCharactersValidator.__call__` rejects input containing a
   null character, THEN the raised `ValidationError` SHALL carry `value` equal to
   the input.
2. The system SHALL keep the message and code
   (`null_characters_not_allowed`) unchanged.

## Requirement 9: Limit validators (Base/Max/Min value and length) supply the rejected value

**User story:** As a developer using min/max value and length validators, I want
the rejected input echoed in a custom message.

**Acceptance criteria**
1. WHEN a validator deriving from `BaseValidator` — including
   `MaxValueValidator`, `MinValueValidator`, `MaxLengthValidator`, and
   `MinLengthValidator` — rejects input, THEN the raised `ValidationError` SHALL
   carry a `value` entry equal to the original input passed to the validator.
2. The system SHALL preserve the existing `limit_value` and `show_value`
   entries and the existing message and code of that `ValidationError`.
3. WHILE validating a length-based limit, the `value` entry SHALL be the original
   input (not its computed length), even though `show_value` remains the length.

## Requirement 10: The value parameter equals the string form of the rejected input

**User story:** As a developer using a message that is exactly `%(value)s`, I
want the reported error to be precisely the rejected value.

**Acceptance criteria**
1. WHEN a field configured with a custom error message of `%(value)s` for the
   relevant code rejects an input, THEN the field's reported error SHALL equal
   the string rendering of that input.
2. The system SHALL bind `value` to the exact rejected input object, so that its
   default string interpolation yields the original textual value for string
   inputs and the standard string form for non-string inputs (e.g. an integer).
3. The system SHALL NOT introduce any duplicate or conflicting `value` entry into
   any existing `params` mapping; where a `params` mapping already exists, the
   `value` binding SHALL be added alongside the existing entries.
