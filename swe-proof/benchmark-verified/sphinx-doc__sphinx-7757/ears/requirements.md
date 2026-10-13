# Requirements: default values for positional-only parameters in parsed signatures

## Introduction

Sphinx can parse a function signature written as a string (for example the text
following a `.. py:function::` directive) into a structured signature object.
This parsing is performed by `signature_from_str` in
`sphinx/util/inspect.py`, which turns the source text into an
`inspect.Signature` built from `inspect.Parameter` objects.

When a signature declares positional-only parameters (using the PEP 570 `/`
separator), any default value written for a positional-only parameter is lost:
the parsed parameter reports no default. As a result, documentation renders a
positional-only parameter such as `b=0` without its default. The goal is to
make the parser attach default-value expressions to positional-only parameters
exactly as it already does for ordinary positional-or-keyword parameters, while
preserving all other parsing behavior (parameter kinds, annotations, keyword-only
defaults, variadic parameters, return annotations, and syntax-error handling).

The affected function is `signature_from_str`; the observable outputs are the
`name`, `kind`, `default`, and `annotation` attributes of each parsed
`Parameter`, plus the signature's return annotation. Default values are
represented as their source-text form (a string), and the absence of a default
is represented by `Parameter.empty`.

## Requirement 1: Default values on positional-only parameters

**User story:** As a documentation author, I want default values written for
positional-only parameters to be preserved when a signature string is parsed,
so that the rendered documentation shows the correct defaults.

**Acceptance criteria**

1. WHEN a signature string containing positional-only parameters (parameters
   before a `/` separator) is parsed, THEN `signature_from_str` SHALL emit one
   `Parameter` per positional-only parameter with `kind` equal to
   `Parameter.POSITIONAL_ONLY`.
2. WHEN a positional-only parameter is written with a default value (for example
   `b=0`), THEN the corresponding `Parameter`'s `default` SHALL be the
   source-text representation of that default expression (for example the string
   `'0'`), not `Parameter.empty`.
3. IF a positional-only parameter is written without a default value, THEN the
   corresponding `Parameter`'s `default` SHALL be `Parameter.empty`.
4. WHEN parsing a signature such as `(a, b=0, /, c=1)`, THEN
   `signature_from_str` SHALL produce parameters named `a`, `b`, `c` in that
   order, where `a` is `POSITIONAL_ONLY` with default `Parameter.empty`, `b` is
   `POSITIONAL_ONLY` with default `'0'`, and `c` is `POSITIONAL_OR_KEYWORD` with
   default `'1'`.

## Requirement 2: Right-to-left default alignment across the whole positional run

**User story:** As a documentation author, I want defaults matched to the
correct parameters regardless of whether they are positional-only or
positional-or-keyword, so that no parameter shows the wrong default.

**Acceptance criteria**

1. The system SHALL treat the positional-only parameters and the
   positional-or-keyword parameters as a single ordered run of positional
   parameters (positional-only first, then positional-or-keyword) for the
   purpose of assigning default values.
2. WHEN the signature supplies a list of positional default expressions, THEN
   the system SHALL assign those defaults, in order, to the rightmost positional
   parameters of that combined run — the last *k* positional parameters receive
   the *k* supplied defaults and every earlier positional parameter receives
   `Parameter.empty`, where *k* is the number of supplied positional defaults.
3. WHEN a supplied default falls on a positional-only parameter because it is
   among the rightmost positional parameters, THEN that positional-only
   parameter SHALL carry the default, exactly as a positional-or-keyword
   parameter in the same position would.
4. The system SHALL keep the existing behavior for positional-or-keyword
   parameters: a positional-or-keyword parameter that is among the rightmost
   positional parameters SHALL carry its supplied default (as source text), and
   one that is not SHALL have `default` equal to `Parameter.empty`.

## Requirement 3: Preserve parsing of other parameter kinds and metadata

**User story:** As a Sphinx maintainer, I want the fix to leave all other
signature-parsing behavior unchanged, so that existing documentation continues
to render correctly.

**Acceptance criteria**

1. The system SHALL continue to parse positional-or-keyword parameters,
   producing `Parameter` objects with `kind` equal to
   `Parameter.POSITIONAL_OR_KEYWORD`, preserving their names, defaults (as
   source text or `Parameter.empty`), and annotations.
2. The system SHALL continue to parse keyword-only parameters (those following a
   `*` or `*args` marker), producing `Parameter` objects with `kind` equal to
   `Parameter.KEYWORD_ONLY` and preserving each one's default value as source
   text when present.
3. The system SHALL continue to parse a variadic positional parameter (`*args`)
   as `Parameter.VAR_POSITIONAL` and a variadic keyword parameter (`**kwargs`)
   as `Parameter.VAR_KEYWORD`, each with `default` equal to `Parameter.empty`.
4. The system SHALL preserve each parameter's annotation as its source-text form
   when an annotation is present, and as `Parameter.empty` when it is absent.
5. The system SHALL preserve the parsed signature's return annotation as its
   source-text form when present and as `Parameter.empty` when absent.
6. WHEN a default value is any Python literal or expression (for example a
   number, string, bytes, ellipsis, boolean, list, dict, set, lambda, `None`,
   call, or dotted name), THEN the system SHALL represent that default as the
   source-text rendering of the expression.
7. WHEN the signature string is not syntactically valid, THEN
   `signature_from_str` SHALL raise a `SyntaxError`.
