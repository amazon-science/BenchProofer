# Requirements: Debug traceback frames for every exception in the chain

## Introduction

Django's technical 500 debug page is produced by the `ExceptionReporter` class
in `django/views/debug.py`. Its `get_traceback_frames()` method walks the
exception being reported together with the chain of exceptions that caused it
(`__cause__` / `__context__`) and returns a flat list of *frame* dictionaries.
Each frame describes one Python stack frame (file, line, function, source
context, local variables) and also carries two chaining fields consumed by the
`technical_500` templates: `exc_cause` (the causing exception, if any) and
`exc_cause_explicit` (whether that link is an explicit `raise ... from ...`).

There is a defect in how the method iterates the exception chain. It walks a
single running traceback and, only when the current traceback is exhausted,
switches to the next exception's `__traceback__`. If an exception in the chain
has **no traceback** (for example a causing/context exception that was
constructed and attached but never actually raised, so its `__traceback__` is
`None`), the walk terminates early: the remaining exceptions in the chain —
including ones that *do* have real tracebacks — contribute no frames at all, so
the debug page can render with an empty or truncated traceback and omit the
exception that was actually raised.

The goal is to make frame collection independent per exception: every exception
in the chain is walked over *its own* traceback, an exception whose traceback is
`None` simply contributes no frames without aborting the rest of the chain, and
each emitted frame reports the causing-exception chaining information belonging
to the exception it came from. The affected module is `django/views/debug.py`;
the behavior is observed through `ExceptionReporter.get_traceback_frames()` and
the HTML/plain-text debug reports it feeds.

## Requirement 1: Every exception in the chain is walked over its own traceback

**User story:** As a developer viewing the debug 500 page, I want the traceback
to include the frames of every exception in the cause/context chain that has a
traceback, so that a causing exception with no traceback does not hide the
exception that was actually raised.

**Acceptance criteria**

1. WHEN `get_traceback_frames()` processes a chain of exceptions, THEN the
   system SHALL produce, for each exception in the chain, the frames obtained by
   walking that exception's own traceback, and SHALL return the concatenation of
   those per-exception frame lists.
2. IF an exception in the chain has no traceback (its traceback is `None`), THEN
   the system SHALL contribute zero frames for that exception AND SHALL still
   produce the frames for the remaining exceptions in the chain.
3. WHEN the reported (outermost) exception has a causing/context exception that
   has no traceback but is itself the only source of traceback frames removed,
   THEN `get_traceback_frames()` SHALL still return the frames of the exception
   that does have a traceback rather than an empty list.
4. The system SHALL determine the total number of returned frames as the sum,
   over all exceptions in the chain, of the number of visible stack frames in
   each exception's own traceback (after honoring frame-hiding, see Requirement
   4), and SHALL NOT drop the frames of a later exception merely because an
   earlier exception in the chain had a short or absent traceback.

## Requirement 2: Per-frame cause attribution

**User story:** As a developer, I want each traceback frame to report the
correct causing exception and whether the link was explicit, so that the debug
page's "direct cause" / "during handling" chaining notices are accurate.

**Acceptance criteria**

1. WHEN the system emits the frames for a given exception in the chain, THEN
   every one of those frames SHALL report `exc_cause` equal to that same
   exception's resolved causing exception (see Requirement 3) and
   `exc_cause_explicit` equal to that same exception's `__cause__` value.
2. WHEN an exception's causing link is an explicit `raise ... from <cause>`
   (its `__cause__` is set), THEN the frames for that exception SHALL carry a
   truthy `exc_cause_explicit`, so that the report renders the "direct cause of
   the following exception" chaining notice.
3. WHEN an exception's causing link is implicit (it has no `__cause__` but has an
   unsuppressed `__context__`), THEN the frames for that exception SHALL carry a
   falsy `exc_cause_explicit`, so that the report renders the "During handling of
   the above exception (…), another exception occurred" chaining notice naming
   that context exception.
4. The system SHALL compute each frame's `exc_cause` / `exc_cause_explicit` from
   the exception whose traceback that frame belongs to, and SHALL NOT let a
   different exception in the chain determine those fields.

## Requirement 3: Cause resolution honors explicit cause and suppressed context

**User story:** As a developer, I want the chain to follow the same
cause/context rules Python uses, so that a `raise ... from None` does not
resurface a suppressed context exception in the debug page.

**Acceptance criteria**

1. WHEN resolving the causing exception of an exception value, THEN the system
   SHALL use its explicit cause (`__cause__`) when one is present.
2. IF an exception has no explicit cause and its context is suppressed (its
   `__suppress_context__` is truthy), THEN the system SHALL treat it as having
   no causing exception (SHALL NOT fall back to `__context__`).
3. IF an exception has no explicit cause and its context is not suppressed, THEN
   the system SHALL use its implicit context (`__context__`) as the causing
   exception.
4. WHILE building the list of chained exceptions, the system SHALL follow the
   resolved causing exception from the reported exception outward AND SHALL stop
   when there is no further causing exception.
5. WHEN following the chain would revisit an exception already seen, THEN the
   system SHALL detect the cycle, emit the existing cycle warning, and stop
   following the chain, so that a cyclic cause/context reference cannot cause an
   infinite loop.

## Requirement 4: Preserve existing single-frame construction behavior

**User story:** As a maintainer, I want each individual frame to keep its
existing content and the single-exception case to keep using the reporter's
stored traceback, so that the refactor changes only which exceptions are walked,
not what a frame contains.

**Acceptance criteria**

1. WHEN there is exactly one exception to report (no further exceptions in the
   chain), THEN the system SHALL walk the reporter's stored traceback for that
   exception, and WHEN there are additional exceptions, THEN each other
   exception SHALL be walked over its own traceback attribute.
2. WHILE walking a traceback, the system SHALL skip frames whose local scope
   marks them hidden (the `__traceback_hide__` convention) and SHALL include the
   remaining frames in order from outermost to innermost of that traceback.
3. WHEN emitting a frame, THEN the system SHALL populate its file name, function
   name, 1-based line number, source context lines (pre-context, context line,
   post-context) and their starting line number, filtered local variables, the
   traceback object, its identity id, and a `type` of `django` for frames in
   `django.*` modules or `user` otherwise.
4. IF the source for a frame's file cannot be read or the line is out of range,
   THEN the system SHALL still emit the frame with empty context lists and a
   placeholder context line indicating the source is unavailable.
5. The system SHALL return an empty frame list WHEN no exceptions were supplied
   to the reporter.
6. The overall ordering of returned frames SHALL place the frames of the
   deepest causing exception first and the frames of the reported (raised)
   exception last, matching the order in which the chain is unwound.

## Requirement 5: Regression protection for chained and edge-case reports

**User story:** As a maintainer, I want existing debug-report behaviors for
nested exceptions and missing source to keep working, so that the fix introduces
no regressions in the rendered pages.

**Acceptance criteria**

1. The system SHALL keep producing the full set of frames for nested exceptions
   where every exception in the chain has a real traceback, preserving each
   frame's cause attribution.
2. The system SHALL keep producing frames when a frame's source file is missing
   or does not match, without raising, so that reports for such frames still
   render.
3. WHEN two exceptions in the chain share the same traceback object, THEN the
   system SHALL still produce a well-formed frame list rather than looping or
   failing.
4. The system SHALL keep the rendered HTML and plain-text debug reports able to
   display the exception type, exception value, traceback section, and request
   information for a reported exception whose chain includes an exception
   without a traceback.
