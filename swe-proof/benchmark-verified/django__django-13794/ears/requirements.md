# Requirements: Concatenation support for lazy string/value proxies

## Introduction

Django's `django.utils.functional.lazy()` builds a proxy class (`Promise`
subclass) that stands in for a value produced on demand: the wrapped callable
is not evaluated until an operation is performed on the proxy, at which point
the proxy delegates the operation to the forced underlying result. Common
examples are the lazily-evaluated translation strings returned by
`django.utils.translation.gettext_lazy`.

The proxy delegates most magic methods to the underlying result via a generated
wrapper, but it does **not** provide the addition protocol methods. As a result,
the Python `+` operator fails whenever a lazy proxy participates in a
concatenation: `"string" + gettext_lazy("lazy")` (and the mirror case) raises
`TypeError: can only concatenate str (not "__proxy__") to str`. The same gap
affects lazy proxies wrapping non-string addable values: adding a lazy proxy to
another operand does not produce the sum of the proxy's underlying value with
that operand.

This failure surfaces in the template `add` filter
(`django.template.defaultfilters.add`): because that filter falls back to
`value + arg` inside a broad `try/except` that returns the empty string on any
exception, adding an ordinary string to a lazy string produced the empty string
instead of the concatenated text.

The goal is to make the lazy proxy behave like its underlying value under the
`+` operator, so concatenation works uniformly regardless of which operand (if
any) is a lazy proxy, and so the `add` filter concatenates strings involving
lazy strings correctly.

## Requirement 1: Lazy proxy supports left-hand addition

**User story:** As a developer using lazily-evaluated values, I want a lazy
proxy on the left side of a `+` expression to add itself to the right operand,
so that concatenation and numeric addition behave as if the proxy were its
underlying value.

**Acceptance criteria**

1. WHEN a lazy proxy is used as the left operand of the `+` operator, THEN the
   proxy SHALL force its wrapped callable to obtain the underlying value and
   SHALL return the result of adding that underlying value to the right operand.
2. WHEN a lazy proxy wrapping a text value is added to an ordinary string on its
   right, THEN the result SHALL be the string produced by concatenating the
   proxy's underlying text followed by the right-hand string.
3. WHEN a lazy proxy wrapping an integer is added to another value on its right,
   THEN the result SHALL equal the sum obtained by adding the proxy's forced
   integer value to that right operand.
4. The system SHALL evaluate the proxy's wrapped callable only at the time the
   addition is performed (on-demand), consistent with the proxy's existing
   deferred-evaluation behavior.

## Requirement 2: Lazy proxy supports right-hand (reflected) addition

**User story:** As a developer, I want a lazy proxy on the right side of a `+`
expression to add itself to a left operand that does not know how to add a
proxy, so that concatenation works even when the ordinary value comes first.

**Acceptance criteria**

1. WHEN a lazy proxy is the right operand of a `+` expression and the left
   operand does not itself handle addition with the proxy, THEN the proxy SHALL
   force its wrapped callable and SHALL return the result of adding the left
   operand to the proxy's underlying value.
2. WHEN an ordinary string is added to a lazy proxy wrapping a text value on its
   right, THEN the result SHALL be the string produced by concatenating the
   left-hand string followed by the proxy's underlying text.
3. The evaluation order SHALL preserve operand order: the left operand SHALL
   precede the proxy's forced value in the produced result.

## Requirement 3: Concatenating two lazy proxies

**User story:** As a developer, I want two lazy proxies to concatenate with each
other, so that combining two lazily-evaluated values behaves like combining
their underlying values.

**Acceptance criteria**

1. WHEN both operands of a `+` expression are lazy proxies wrapping text values,
   THEN the result SHALL be the concatenation of the left proxy's underlying
   text followed by the right proxy's underlying text.
2. WHEN both operands are lazy proxies wrapping addable values, THEN the result
   SHALL equal the value obtained by forcing each proxy and adding the forced
   left value to the forced right value.

## Requirement 4: The `add` template filter concatenates lazy strings

**User story:** As a template author, I want the `add` filter to concatenate a
string with a lazy string, so that I get the joined text instead of an empty
string.

**Acceptance criteria**

1. WHEN the `add` filter (`django.template.defaultfilters.add`) is applied with
   an ordinary string value and a lazy string argument, THEN the rendered output
   SHALL be the two strings concatenated in value-then-argument order.
2. WHEN the `add` filter is applied with a lazy string value and a lazy string
   argument, THEN the rendered output SHALL be the two underlying strings
   concatenated in value-then-argument order.
3. IF an operand of the `add` filter is a lazy string, THEN the filter SHALL NOT
   return the empty string as a result of an addition-time exception; it SHALL
   return the correctly concatenated text.

## Requirement 5: Preserve existing addition and filter behavior

**User story:** As a maintainer, I want the previously working behaviors of the
`add` filter and the lazy proxy to remain unchanged, so that the fix introduces
no regressions.

**Acceptance criteria**

1. The `add` filter SHALL continue to return the arithmetic sum when both value
   and argument are numbers or numeric strings that can be interpreted as
   integers.
2. The `add` filter SHALL continue to concatenate two ordinary (non-lazy) lists
   into their combined sequence, and SHALL continue to concatenate two ordinary
   strings into their joined text.
3. WHEN the `add` filter receives operands that cannot be added together in any
   supported way, THEN it SHALL return the empty string, preserving its existing
   error-tolerant fallback.
4. The lazy proxy SHALL continue to support its previously working operations
   (including string conversion, equality and ordering comparisons, hashing,
   and the modulo/formatting operator) with unchanged results.
5. WHEN a lazy proxy participates in an addition whose forced underlying value
   does not support the operation with the other operand, THEN the resulting
   error SHALL be the same error that adding the underlying value directly would
   raise (the proxy SHALL NOT mask or alter it).
