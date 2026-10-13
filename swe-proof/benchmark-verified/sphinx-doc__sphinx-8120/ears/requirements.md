# Requirements: User-supplied message catalogs override built-in translations

## Introduction

Sphinx loads translated UI strings ("system messages" such as figure and
listing caption labels, search-box labels, and other built-in text) from
GNU-gettext message catalogs. During initialization, `Sphinx._init_i18n`
(`sphinx/application.py`) assembles an ordered list of catalog search
locations and hands it to the catalog loader `init`
(`sphinx/locale/__init__.py`), which walks the list and merges the catalogs it
finds. The loader treats earlier locations as primary and later locations only
as fallbacks, so the *order* of the search list determines which translation
wins when the same message is defined in more than one location.

The list contains three kinds of location: the system default location, the
directory of translations bundled with Sphinx itself (built-in defaults), and
the user-configured `locale_dirs` (the catalog directories a project supplies,
resolved via `CatalogRepository`). Because the bundled-defaults location was
placed *before* the user-configured locations, a project that shipped its own
`sphinx.po`/`sphinx.mo` catalog to override or extend the built-in translations
could never win: the bundled translation was always found first and the user's
entries were ignored.

The goal is to make user-configured catalog locations take precedence over the
bundled-defaults location, so that a project can override individual built-in
system messages by providing its own catalog for the configured language, while
the system default location stays first and all previously working translation
behavior is preserved. Sphinx already compiles an out-of-date user `sphinx.po`
into a `sphinx.mo` before loading (auto-build); that behavior must continue so
the freshly provided catalog is actually available.

## Requirement 1: User-configured catalogs override built-in translations

**User story:** As a project author, I want to add my own message catalog for
the configured language so that I can override or extend Sphinx's built-in
system-message translations, so that my custom wording appears instead of the
bundled default.

**Acceptance criteria**
1. WHEN a project configures a language and supplies, in one of its configured
   catalog directories, a catalog for that language that redefines a built-in
   system message, THEN after initialization the application's translator SHALL
   return the project-supplied translation for that message rather than the
   bundled built-in translation.
2. WHEN such an overriding project catalog is present and the document is
   built, THEN the generated output SHALL contain the project-supplied
   translation of the overridden system message.
3. The system SHALL assemble the catalog search list so that the
   user-configured catalog locations are searched *before* the bundled built-in
   defaults location, with the system default location remaining first.
4. WHEN a message is present in a user-configured catalog but the corresponding
   built-in catalog also defines it, THEN the user-configured value SHALL take
   precedence, while messages absent from the user-configured catalog SHALL
   still fall back to the built-in translation.

## Requirement 2: Preserve built-in translations when not overridden

**User story:** As a user relying on Sphinx's shipped translations, I want the
built-in system messages to keep being translated for the configured language,
so that projects that do not supply their own catalogs are unaffected.

**Acceptance criteria**
1. WHEN a project configures a language for which built-in translations exist
   and supplies no overriding catalog, THEN the application's translator SHALL
   return the bundled built-in translations exactly as before.
2. The system SHALL keep the system default location as the first entry of the
   catalog search list.
3. IF the configured language has a country-code variant, THEN the loader SHALL
   continue to search both the full language tag and its base language.
4. WHEN built-in translations are available for the configured language (or the
   language is English), THEN initialization SHALL still report that translation
   loading succeeded; otherwise it SHALL report that translations are not
   available for built-in messages.

## Requirement 3: Auto-compile updated user catalogs before loading

**User story:** As a project author, I want my updated `sphinx.po` to be turned
into a usable `sphinx.mo` automatically, so that the catalog I just edited is
the one that gets loaded.

**Acceptance criteria**
1. WHEN a user-configured catalog directory contains a `sphinx`-domain source
   catalog that is out of date relative to its compiled form, THEN
   initialization SHALL compile the source catalog into its compiled form
   before assembling the search list and loading translations.
2. The system SHALL include the user-configured catalog directories in the
   search list using the directories resolved from the project's configured
   `locale_dirs`, preserving their given order.

## Requirement 4: Accept the system-default sentinel among search locations

**User story:** As a maintainer, I want the catalog loader to accept the
system-default sentinel as a search location, so that the reordered search list
loads without error.

**Acceptance criteria**
1. The catalog loader `init` SHALL accept a search list whose entries are either
   concrete directory paths or the system-default sentinel, in any order.
2. WHEN no language is configured, THEN initialization SHALL still install a
   translator and SHALL NOT fail.
3. IF a listed search location contains no matching catalog, THEN the loader
   SHALL skip that location and continue with the remaining locations without
   raising.
