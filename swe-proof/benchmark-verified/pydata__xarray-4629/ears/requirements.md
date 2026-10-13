# Requirements: Independent attribute mapping when merging with `combine_attrs="override"`

## Introduction

`xarray.merge` (and the equivalent merge paths used by `Dataset`/`DataArray`)
combine the `.attrs` metadata mappings of the source objects according to a
`combine_attrs` policy. The policy is resolved by the helper
`merge_attrs(variable_attrs, combine_attrs)` in `xarray/core/merge.py`, which is
given the ordered list of source attribute mappings and returns the combined
mapping placed on the merged result.

Under the `"override"` policy the combined metadata is meant to be *taken from
the first source*. The defect is that the helper returns the first source's
attribute mapping object directly instead of an independent copy. As a result
the merged object and the first source share one underlying mapping, so mutating
the merged object's attributes silently mutates the first source (and vice
versa). The goal is to make the merged result's attribute mapping independent of
every source under `"override"`, matching the behavior already exhibited by the
other policies, without changing which key/value pairs end up on the result or
altering any other policy.

## Requirement 1: `"override"` produces an independent attribute mapping

**User story:** As a user merging datasets with `combine_attrs="override"`, I
want the merged object to own its own attribute mapping, so that later edits to
the merged object's attributes never leak back into any source object.

**Acceptance criteria**
1. WHEN `merge_attrs` is called with at least one source attribute mapping and
   `combine_attrs="override"`, THEN `merge_attrs` SHALL return a mapping object
   that is a distinct object from the first source's attribute mapping (not the
   same object identity).
2. WHEN objects are merged with `combine_attrs="override"` and an attribute of
   the merged result is subsequently reassigned, THEN the corresponding
   attribute of the first (and every) source object SHALL remain unchanged.
3. WHEN objects are merged with `combine_attrs="override"` and an attribute of a
   source object is subsequently reassigned, THEN the corresponding attribute of
   the merged result SHALL remain unchanged.
4. IF a source object's attribute mapping is later mutated in place (adding or
   removing keys) after a `combine_attrs="override"` merge, THEN the merged
   result's attribute mapping SHALL retain the key set it had at merge time.

## Requirement 2: `"override"` preserves the first source's attribute contents

**User story:** As a user relying on `combine_attrs="override"`, I want the
merged result to carry exactly the first source's metadata, so that making the
mapping independent does not change which attributes appear.

**Acceptance criteria**
1. WHEN `merge_attrs` is called with a non-empty list of source attribute
   mappings and `combine_attrs="override"`, THEN the returned mapping SHALL
   compare equal (same keys mapped to the same values) to the first source's
   attribute mapping.
2. WHEN merging with `combine_attrs="override"`, THEN attribute mappings of
   sources other than the first SHALL NOT contribute keys or values to the
   result.
3. WHEN the returned `"override"` mapping is a copy, THEN the copy SHALL be a
   shallow copy: each value SHALL be the same value object present in the first
   source's mapping.

## Requirement 3: Other `combine_attrs` policies are unchanged

**User story:** As a user of the merge machinery, I want every other
`combine_attrs` policy to keep behaving exactly as before, so that the fix is
scoped strictly to the `"override"` aliasing bug.

**Acceptance criteria**
1. WHEN `merge_attrs` is called with an empty list of source attribute mappings,
   THEN it SHALL return an absence-of-attributes result (`None`) regardless of
   the policy.
2. WHEN `combine_attrs="drop"`, THEN `merge_attrs` SHALL return an empty mapping.
3. WHEN `combine_attrs="no_conflicts"` and the sources agree on every shared
   key, THEN `merge_attrs` SHALL return the union of all source mappings, and the
   returned mapping SHALL be independent of every source.
4. IF `combine_attrs="no_conflicts"` and two sources assign different values to
   the same key, THEN `merge_attrs` SHALL raise a merge error.
5. WHEN `combine_attrs="identical"` and all source mappings are equal, THEN
   `merge_attrs` SHALL return that common mapping, independent of every source.
6. IF `combine_attrs="identical"` and the source mappings are not all equal,
   THEN `merge_attrs` SHALL raise a merge error.
7. IF `combine_attrs` is a value other than the recognised policies, THEN
   `merge_attrs` SHALL raise a value error.
8. The default merge behavior for object and dataset combination (non-attribute
   data variables, coordinates, alignment, and conflict detection) SHALL remain
   as before, unaffected by this change.
