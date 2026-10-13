# Requirements: Robust date-component coercion in SelectDateWidget

## Introduction

`SelectDateWidget` (in `django/forms/widgets.py`) collects a date from three
separate user-controlled inputs — a year, a month and a day, each submitted as
text. During form validation its `value_from_datadict` method reduces those
three components to a single string value that the bound `DateField` then
parses.

To perform that reduction the widget currently constructs a
`datetime.date(int(y), int(m), int(d))`. When a component is a syntactically
valid integer whose magnitude exceeds what the C-level date constructor can
accept (for example a year larger than `sys.maxsize`), `datetime.date` raises
`OverflowError`. That exception is not handled, so it propagates out of
`value_from_datadict` and, through `DateField`/`Form.is_valid()`, becomes an
unhandled server error — a client can crash a view simply by submitting an
oversized numeric component.

The goal is to make this reduction total: an oversized-magnitude component must
be absorbed and turned into a value that the downstream `DateField` treats as an
invalid date, so the form reports an ordinary validation error instead of
crashing — while all pre-existing coercion behavior is preserved unchanged.

## Requirement 1: Oversized numeric components must not crash the widget

**User story:** As a site operator whose forms use `SelectDateWidget`, I want
oversized date components to be handled gracefully, so that a malicious or
accidental oversized input produces a normal validation failure rather than an
unhandled server error.

**Acceptance criteria**

1. WHEN `SelectDateWidget.value_from_datadict` receives year, month and day
   components that are each present (not all empty) and at least one is a
   syntactically valid integer whose magnitude is too large to be accepted as a
   calendar-date component (such that constructing the date raises
   `OverflowError`), THEN `value_from_datadict` SHALL return without propagating
   any exception.
2. WHEN such an oversized-magnitude component is encountered during the
   reduction, THEN `value_from_datadict` SHALL collapse the whole date to the
   widget's existing zeros-for-unselected representation — the pseudo-ISO form
   in which an unselected component is shown as a single `0` — with the year,
   month and day all reduced to that `0` placeholder, so the reduced value
   denotes no real calendar date.
3. WHILE processing components whose magnitude is too large to form a date, the
   widget SHALL treat the situation distinctly from the ordinary
   invalid-but-well-formed case: the returned value SHALL NOT incorporate the
   raw oversized component text, and every one of the three components SHALL be
   rendered as the `0` unselected placeholder (never carried through as its
   submitted digits).

## Requirement 2: The oversized sentinel is rejected as an invalid date

**User story:** As a form user, I want an oversized date submission to be
reported as an invalid date, so that the form is not accepted and no crash
occurs.

**Acceptance criteria**

1. WHEN a `DateField` cleans the reduced value produced by Requirement 1 for an
   oversized submission (a pseudo-ISO string whose year, month and day are all
   the `0` placeholder, denoting no real calendar date), THEN it SHALL reject it
   as invalid — applying the same generic handling it gives any non-parseable
   date string — by raising a validation error whose message is "Enter a valid
   date."
2. WHEN a `Form` containing a `DateField` bound to a `SelectDateWidget` is
   validated with an oversized numeric component among its date inputs, THEN
   `is_valid()` SHALL return `False`.
3. WHEN such a form is found invalid due to an oversized component, THEN the
   field's error list SHALL contain exactly the single message "Enter a valid
   date." and no other errors for that field.

## Requirement 3: Preserve existing coercion behavior (regression protection)

**User story:** As a maintainer, I want all previously correct coercion
behaviors kept intact, so that fixing the overflow crash does not change how
ordinary inputs are handled.

**Acceptance criteria**

1. WHEN all three components are the empty string, THEN `value_from_datadict`
   SHALL keep returning `None`.
2. IF one or more of the year, month or day components is absent (not supplied),
   THEN `value_from_datadict` SHALL keep returning the value looked up under the
   field's own name (its existing fallback), rather than attempting date
   construction.
3. WHEN the three components denote a representable calendar date, THEN
   `value_from_datadict` SHALL keep returning that date rendered in the first
   configured date input format.
4. WHEN the three components are well-formed but do not denote a representable
   calendar date (for example an impossible month or day, an out-of-range year,
   or non-numeric text) and do not overflow, THEN `value_from_datadict` SHALL
   keep returning the pseudo-ISO string `"<y>-<m>-<d>"`, where each empty
   component is shown as a single `0` (e.g. `"2017-0-23"`).
5. The system SHALL keep the following `DateField` cleaning behaviors unchanged:
   valid date strings continue to clean to their corresponding date; malformed
   date strings (such as clearly non-date text or unsupported formats) continue
   to raise "Enter a valid date."; and an absent required value continues to
   raise the field's required-error message.
6. The system SHALL keep rendering behavior of `SelectDateWidget` unchanged,
   including rendering of empty, `None`, string and datetime values, invalid
   submitted dates, custom input formats, custom month names, localized output,
   fieldsets, and year rendering without separators.
