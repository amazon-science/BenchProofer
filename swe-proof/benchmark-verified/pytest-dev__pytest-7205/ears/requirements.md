# Requirements: Safe rendering of fixture parameter values in setup-show output

## Introduction

When pytest is run with the fixture-setup reporting options (`--setup-only`,
`--setup-plan`, `--setup-show`), the setup/teardown reporter prints one line per
fixture action. For parametrized fixtures, that line ends with the fixture's
parameter value in square brackets. This behavior lives in
`_show_fixture_action` in `src/_pytest/setuponly.py`, which is invoked from the
`pytest_fixture_setup` and `pytest_fixture_post_finalizer` hooks in the same
module.

The reporter previously formatted the parameter value by coercing it to text
directly (an implicit string conversion). This produced two problems:

1. Values were shown without their type-revealing representation — e.g. a string
   parameter appeared bare, indistinguishable from other tokens.
2. Non-textual values such as `bytes` triggered a `BytesWarning` when Python was
   run with `-bb` (which turns byte-to-str coercion warnings into errors),
   causing the fixture setup to error out instead of reporting cleanly.

The goal is to render each parameter value through a safe, size-limited textual
representation so the output is unambiguous and never raises on non-textual
parameter values, while preserving every other aspect of the existing setup/
teardown reporting.

## Requirement 1: Render fixture parameter values via a safe representation

**User story:** As a developer inspecting fixture setup with `--setup-show`,
`--setup-only`, or `--setup-plan`, I want each parametrized fixture's value shown
in its safe representation form, so that I can unambiguously tell what value was
supplied (including its type) and distinguish, for example, a string from a bare
identifier.

**Acceptance criteria**

1. WHEN the setup/teardown reporter emits a line for a fixture action that
   carries a parameter value, THEN the reporter SHALL render that value using a
   safe representation equivalent to Python's `repr` of the value, rather than a
   plain string coercion.
2. WHEN a fixture parameter value is a text string, THEN the reporter SHALL show
   it enclosed in quotes as its `repr` produces (e.g. a string value such as
   `abc` SHALL be rendered as `'abc'`), not as the bare unquoted text.
3. The reporter SHALL enclose the rendered parameter representation in square
   brackets appended directly after the fixture action header (i.e. the line
   ends with `[<representation>]`, as in a header followed by
   `[<repr-of-value>]`), keeping the bracket-wrapping and its position at the
   end of the line unchanged from prior behavior.
4. WHEN a fixture action carries no parameter value, THEN the reporter SHALL emit
   the action line with no trailing bracketed segment, exactly as before.

## Requirement 2: Never raise on non-textual parameter values

**User story:** As a developer running pytest under strict byte-warning mode
(`python -bb`), I want `--setup-show` to report `bytes` (and other non-textual)
parameter values without raising, so that fixture setup reporting does not crash
my run.

**Acceptance criteria**

1. WHEN the reporter renders a parameter value whose safe representation would
   otherwise involve an implicit bytes-to-str coercion (such as a `bytes`
   value), THEN it SHALL produce the value's representation without triggering a
   `BytesWarning`.
2. IF pytest is run with byte warnings promoted to errors (as with `python -bb`)
   and a parametrized test supplies a `bytes` parameter value while
   `--setup-show` is active, THEN the run SHALL complete with a success exit
   status and the fixture setup SHALL NOT error.
3. The reporter SHALL apply the safe representation uniformly to every parameter
   value regardless of the value's type, so that no parameter type causes the
   reporting path to raise.

## Requirement 3: Bound the length of the rendered parameter representation

**User story:** As a developer viewing setup output, I want very large parameter
values truncated to a bounded length, so that a single parameter value cannot
flood the report with unbounded text.

**Acceptance criteria**

1. WHEN a parameter value's representation exceeds the reporter's size budget,
   THEN the reporter SHALL emit a truncated, size-limited representation rather
   than the full untruncated text.
2. The system SHALL keep the applied size budget small enough to bound a single
   parameter line yet large enough that typical short parameter values (such as
   a few-character string) are shown in full and unmodified.

## Requirement 4: Preserve all other setup/teardown reporting behavior

**User story:** As a maintainer, I want the change limited to how parameter
values are rendered, so that all other existing setup/teardown reporting output
stays exactly as it was.

**Acceptance criteria**

1. The reporter SHALL keep emitting, for each fixture action, the step label
   (`SETUP` / `TEARDOWN`, left-aligned/padded as before), the single-letter
   scope indicator, and the fixture name in their existing format and order.
2. WHEN a fixture action is a `SETUP` and the fixture depends on other fixtures,
   THEN the reporter SHALL still append the sorted list of used fixtures in the
   existing `(fixtures used: ...)` form, excluding the implicit request object.
3. The reporter SHALL continue to display the same parameter value for a
   parametrized fixture on both its `SETUP` and its corresponding `TEARDOWN`
   line.
4. WHEN a parametrized fixture defines explicit id values (a static id list or an
   id-generating callable), THEN the reporter SHALL continue to select the
   parameter representation from those ids as before, and only the final
   rendering of the selected value SHALL go through the safe representation.
5. The system SHALL leave the behavior of runs without any parametrized fixture,
   the indentation by fixture scope, capture suspend/resume around the emitted
   line, and the `--setup-only`/`--setup-plan`/`--setup-show` option wiring
   unchanged.
