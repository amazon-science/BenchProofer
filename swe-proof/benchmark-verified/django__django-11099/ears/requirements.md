# Username validator requirements

## Introduction

The authentication layer of the framework provides two username validators in
`django.contrib.auth.validators`: `ASCIIUsernameValidator` and
`UnicodeUsernameValidator`. Each subclasses the core `RegexValidator` and is
meant to accept a username only when the value consists **entirely** of allowed
characters — English letters (ASCII validator) or letters from any script
(Unicode validator), plus digits, the underscore, and the four punctuation
characters `.`, `@`, `+`, and `-`.

A defect in how the validators anchor their pattern lets a value that ends with
a line-break (newline) character slip through: the trailing newline is treated
as an acceptable terminator, so a username whose final character is a newline is
wrongly accepted even though the newline is not an allowed character. The goal
is to make both validators judge the *whole* value — from its first character
through its very last — so that any value containing a non-allowed character
anywhere, including a terminating newline, is rejected, while every previously
accepted legitimate username stays accepted.

This document specifies the observable admissibility behavior of both
validators. All requirements are about which username values the validators
accept versus reject.

## Requirement 1: Reject usernames ending in a line-break character

**User story:** As an operator relying on username validation, I want a value
that ends with a newline character to be rejected, so that a trailing line
break cannot be smuggled into an otherwise valid-looking username.

**Acceptance criteria**
1. WHEN `ASCIIUsernameValidator` is applied to a value that consists of
   otherwise-allowed English-letter-family characters immediately followed by a
   trailing newline (line-feed) character, THEN the validator SHALL reject the
   value (raise the validation error).
2. WHEN `UnicodeUsernameValidator` is applied to a value that consists of
   otherwise-allowed characters immediately followed by a trailing newline
   (line-feed) character, THEN the validator SHALL reject the value.
3. The validators SHALL treat a newline character as a non-allowed character:
   its presence anywhere in the value, including as the final character, SHALL
   cause rejection.
4. IF a value would be accepted after removing a single trailing newline, THEN
   the validator SHALL nonetheless reject the value while the trailing newline
   is present.

## Requirement 2: Accept only values allowed end-to-end

**User story:** As an operator, I want a username accepted only when every one
of its characters is allowed, so that no non-allowed character in any position
is tolerated.

**Acceptance criteria**
1. The validators SHALL accept a value only when it is non-empty AND every
   character in it, from the first through the last, belongs to the relevant
   allowed set.
2. IF any character of the value is not in the allowed set, THEN the validator
   SHALL reject the value regardless of that character's position.
3. `ASCIIUsernameValidator` SHALL restrict its allowed set to English letters,
   digits, the underscore, and the characters `.`, `@`, `+`, and `-`.
4. `UnicodeUsernameValidator` SHALL allow letters from any script in addition to
   digits, the underscore, and the characters `.`, `@`, `+`, and `-`.

## Requirement 3: Preserve acceptance of legitimate usernames

**User story:** As a user with a valid username, I want my existing username to
keep validating, so that tightening the trailing-newline behavior does not break
legitimate accounts.

**Acceptance criteria**
1. WHEN `ASCIIUsernameValidator` is applied to a value composed only of English
   letters (e.g. all lower-case, mixed case) with no non-allowed character,
   THEN the validator SHALL accept the value.
2. WHEN `ASCIIUsernameValidator` is applied to a value that combines English
   letters with one of the allowed punctuation characters (`.`, `@`, `+`, `-`),
   THEN the validator SHALL accept the value.
3. WHEN `UnicodeUsernameValidator` is applied to a value composed of letters
   from a non-English script, THEN the validator SHALL accept the value.
4. The system SHALL leave the human-readable error message and the ASCII-only
   matching mode of `ASCIIUsernameValidator` unchanged, so that unchanged
   validator metadata continues to report as before.

## Requirement 4: Preserve rejection of other invalid usernames

**User story:** As an operator, I want values that were already invalid to
remain rejected, so that the fix narrows rather than widens what is accepted.

**Acceptance criteria**
1. WHEN either validator is applied to a value containing an ASCII space or
   other whitespace between characters, THEN the validator SHALL reject the
   value.
2. WHEN either validator is applied to a value containing an apostrophe or other
   punctuation outside the allowed set, THEN the validator SHALL reject the
   value.
3. WHEN `ASCIIUsernameValidator` is applied to a value containing a non-ASCII
   letter, THEN the validator SHALL reject the value.
4. WHEN `UnicodeUsernameValidator` is applied to a value containing any Unicode
   character that is not a letter (in any script), a digit, the underscore, or
   one of the allowed punctuation characters (`.`, `@`, `+`, `-`), THEN the
   validator SHALL reject the value. This holds regardless of how visually
   similar the non-allowed character may be to an allowed one, so that a
   character outside the allowed set cannot be smuggled in on the basis of
   appearance.
