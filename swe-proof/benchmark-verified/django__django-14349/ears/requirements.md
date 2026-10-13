# Requirements: URL validation must reject line-break and tab characters

## Introduction

`URLValidator` in `django/core/validators.py` decides whether a supplied value
is an acceptable URL, raising `django.core.exceptions.ValidationError` when it
is not. Historically, `URLValidator` relied on the URL-splitting machinery in
`urllib.parse` (and its own regular expression) to reject malformed input,
including URLs that carried stray line-feed (`\n`), carriage-return (`\r`), or
horizontal-tab (`\t`) characters.

Newer Python releases changed `urllib.parse`'s splitting behavior to silently
strip all line-feed, carriage-return, and tab characters from a URL before
splitting it into components. As a result, a URL such as
`http://www.example.com/\n` is cleaned to a well-formed URL before the
validator ever inspects it, so the validator no longer rejects it. This makes
`URLValidator` accept values it must reject, and the acceptance depends on which
Python version is in use.

The goal is to make `URLValidator` reject any URL string that contains a tab,
carriage-return, or line-feed character, independently of the underlying
`urllib.parse` behavior, while leaving every other aspect of URL validation
unchanged. These characters are unsafe because their presence lets the same
text be split or interpreted in more than one way.

## Requirement 1: Reject URLs containing tab, carriage-return, or line-feed characters

**User story:** As a developer relying on `URLValidator`, I want any URL that
contains a tab, carriage-return, or line-feed character to be rejected, so that
validation is safe and consistent regardless of the Python version's
URL-parsing behavior.

**Acceptance criteria**

1. WHEN `URLValidator.__call__` is invoked with a string that contains at least
   one horizontal-tab (`\t`), carriage-return (`\r`), or line-feed (`\n`)
   character, THEN the validator SHALL raise `ValidationError`.
2. WHEN such a disallowed character appears anywhere in the string — at the
   start, in the middle, or at the end of the value — THEN the validator SHALL
   raise `ValidationError`.
3. WHEN such a disallowed character appears inside the host portion of an
   otherwise well-formed URL (including a bracketed IPv6 host), THEN the
   validator SHALL raise `ValidationError`.
4. WHEN the validator rejects a value solely because it contains a disallowed
   character, THEN the raised `ValidationError` SHALL carry the same message and
   the same error code that `URLValidator` uses for any other invalid URL, and
   its `params` SHALL include the offending value under the `value` key.
5. IF a value would otherwise be treated as a well-formed URL by the underlying
   URL-splitting machinery only because that machinery strips tab,
   carriage-return, or line-feed characters, THEN `URLValidator` SHALL still
   reject the value.
6. The disqualifying check for these characters SHALL be applied to the raw
   input value before it is passed to any URL-splitting or normalization step,
   so that acceptance does not depend on the underlying parser stripping those
   characters.

## Requirement 2: Preserve existing URL-validation behavior

**User story:** As a developer with existing code and tests that depend on
`URLValidator`, I want all previously correct acceptance and rejection outcomes
to remain unchanged, so that adding the new character check introduces no
regressions.

**Acceptance criteria**

1. WHEN `URLValidator.__call__` is invoked with a value that is not a string,
   THEN the validator SHALL raise `ValidationError`.
2. WHEN a URL string contains none of the disallowed characters (tab,
   carriage-return, line-feed), THEN `URLValidator` SHALL accept or reject it
   exactly as it did before this change — that is, purely on the basis of its
   scheme being among the allowed schemes and its overall structure and host
   matching the URL grammar.
3. WHEN a well-formed URL that contains no disallowed characters is validated,
   THEN the validator SHALL NOT raise `ValidationError`.
4. WHEN a URL uses a scheme that is not in the validator's list of allowed
   schemes, THEN the validator SHALL raise `ValidationError`.
5. The system SHALL continue to reject values whose structure fails the URL
   grammar (for example, values with no scheme separator, or with trailing junk
   after an otherwise valid URL), independently of the new character check.

## Requirement 3: Preserve unrelated validator behaviors

**User story:** As a maintainer of Django's validators module, I want the
supporting behaviors of the validators to keep working, so that the change is
narrowly scoped to URL character safety.

**Acceptance criteria**

1. The system SHALL preserve the equality semantics of validators, so that two
   validators compare equal when their defining attributes match and unequal
   otherwise.
2. The system SHALL preserve the existing deprecation behavior associated with
   the deprecated domain-allow-list attribute, including emitting the
   corresponding deprecation warning when that attribute is accessed or set.
3. The system SHALL preserve the existing message-formatting behavior of the
   validators, including single-message, message-list, and message-dictionary
   handling and length-limited messages.
4. The system SHALL preserve the behavior of the general regular-expression
   validator, including honoring configured regular-expression flags.
