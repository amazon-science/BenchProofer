# Requirements: Robust minimum-version checking in `minversion`

## Introduction

The utility function `minversion` in `astropy/utils/introspection.py` decides
whether an imported Python module (or a named module) satisfies a minimum
version requirement. It obtains the module's available version (by default from
its `__version__` attribute, or from a dotted `version_path`) and compares it
against a caller-supplied required-version string using the standard
version-string ordering provided by `distutils.version.LooseVersion`.

A regression was introduced when the required-version string began to be passed
directly to `LooseVersion`. When the required-version string carries a trailing
non-numeric qualifier (for example a development or pre-release suffix such as
`1.14dev`) while the available version has additional numeric
components (for example `1.14.3`), the comparison inside `LooseVersion` raises a
`TypeError` (comparing an `int` component against a `str` component) instead of
returning a boolean. For example, `minversion('numpy', '1.14dev')` raised a
`TypeError` rather than returning a truth value.

The goal is to make `minversion` return a boolean for any required-version
string by first reducing that string to its leading numeric release prefix
before comparison, while preserving all existing comparison, resolution, and
error-handling behavior.

## Requirement 1: Reduce the required version to its leading release-number prefix

**User story:** As a developer checking whether a dependency meets a minimum
version, I want `minversion` to tolerate required-version strings that include a
development or pre-release qualifier, so that the check returns a boolean
instead of raising an error.

**Acceptance criteria**

1. WHEN `minversion` is called with a required-version string, THEN the system
   SHALL, before performing any version comparison, compute a normalized
   required-version string equal to the longest prefix of the original string
   that matches a leading release-number pattern.
2. A leading release-number prefix SHALL be a maximal initial run of the string
   that consists of one or more decimal-integer components separated by single
   `.` characters (for example `1`, `1.14`, or `0.12`); the matched prefix
   extends through the last such numeric component and stops at the first
   character that is not part of a dotted numeric release number.
3. WHEN the required-version string begins with such a leading release-number
   prefix, THEN the system SHALL use only that matched prefix (discarding the
   remainder of the string, including any trailing non-numeric qualifier) as the
   normalized required version for the comparison.
4. IF the required-version string does not begin with a release number, THEN the
   system SHALL use the required-version string unchanged as the normalized
   required version.
5. WHEN the required-version string consists solely of a leading release-number
   prefix with no trailing characters, THEN the normalized required version
   SHALL equal the original string.

## Requirement 2: Compare available version against the normalized requirement

**User story:** As a developer, I want `minversion` to report whether the
available module version meets the (normalized) required version, so that I get
a correct boolean answer.

**Acceptance criteria**

1. WHEN `inclusive` is true (the default), THEN `minversion` SHALL return `True`
   if and only if the available version is greater than or equal to the
   normalized required version under standard version-string ordering.
2. WHEN `inclusive` is false, THEN `minversion` SHALL return `True` if and only
   if the available version is strictly greater than the normalized required
   version under standard version-string ordering.
3. WHEN the required-version string carries a trailing non-numeric qualifier
   (for example a development or pre-release suffix) and the available version
   has additional numeric components, THEN `minversion` SHALL return a boolean
   result and SHALL NOT raise an error from the comparison.
4. The system SHALL determine ordering using the same standard version-string
   comparison it currently applies to the available version (that is, the
   `distutils.version.LooseVersion` ordering); the normalization SHALL affect
   only the required-version operand.

## Requirement 3: Preserve module resolution and version discovery

**User story:** As a developer, I want the existing ways of supplying a module
and locating its version to keep working, so that this fix does not change
unrelated behavior.

**Acceptance criteria**

1. WHEN `module` is an already-imported module object, THEN `minversion` SHALL
   read its available version from the module.
2. WHEN `module` is a string naming a module, THEN `minversion` SHALL attempt to
   import that module and, IF the import fails with an import error, THEN it
   SHALL return `False`.
3. IF `module` is neither an imported module object nor a string, THEN
   `minversion` SHALL raise a `ValueError`.
4. WHEN `version_path` is a plain attribute name (containing no `.`), THEN
   `minversion` SHALL read the available version from that attribute of the
   module; WHEN `version_path` is a dotted path, THEN it SHALL resolve the
   available version by following that dotted attribute path. The default
   `version_path` SHALL be `'__version__'`.
