# Requirements — viewcode module pages for epub / single-file output

## Introduction

The `sphinx.ext.viewcode` extension highlights module source code and links
documentation entries to those highlighted source pages. It registers a handler
for the `html-collect-pages` event (`collect_pages` in
`sphinx/ext/viewcode.py`) that builds and emits one highlighted-source page per
collected module plus an index page.

When a project is built for the epub output format (e.g. `make html epub`),
viewcode currently emits these highlighted module pages into the epub output
even though a dedicated configuration value, `viewcode_enable_epub` (declared by
the extension with a default of `False`), is meant to gate that behavior. As a
result, module source pages are written into the epub by default, contrary to
the documented default.

The goal is to make `collect_pages` respect the output format: it must not emit
module source pages for the epub builder family unless `viewcode_enable_epub` is
enabled, and it must not emit them for the single-file HTML builder, while
continuing to emit them for ordinary HTML builds. The page-generation logic and
the paired `doctree-read` collection handler (`doctree_read`) already apply an
equivalent gate when collecting module data; the `html-collect-pages` handler
must apply the same gate when producing the pages.

## Requirement 1: Suppress viewcode module pages for epub by default

**User story:** As a documentation author building both HTML and epub outputs, I
want viewcode to omit module source pages from the epub by default, so that the
epub does not contain unwanted highlighted-source pages.

**Acceptance criteria**

1. WHEN the `html-collect-pages` event fires and the active builder's name
   begins with the epub builder-family prefix (`"epub"`) and the configuration
   value `viewcode_enable_epub` is `False`, THEN `collect_pages` SHALL emit no
   module source pages and no viewcode index page (it SHALL yield an empty
   sequence).
2. WHEN a project is built with the epub builder using the default
   configuration, THEN the build SHALL NOT write any viewcode highlighted-source
   page (i.e. no per-module page is produced under the viewcode module-output
   directory) for that build.
3. The system SHALL treat `viewcode_enable_epub` as defaulting to `False` so
   that the epub suppression above applies unless the author explicitly enables
   it.

## Requirement 2: Emit viewcode module pages for epub when explicitly enabled

**User story:** As a documentation author who wants source pages in the epub, I
want viewcode to include module source pages in the epub when I opt in, so that
enabling the feature actually produces the pages.

**Acceptance criteria**

1. WHEN the `html-collect-pages` event fires and the active builder's name
   begins with the epub builder-family prefix and the configuration value
   `viewcode_enable_epub` is `True`, THEN `collect_pages` SHALL proceed to build
   and emit the module source pages exactly as it does for a plain HTML build
   (subject to the module data collected during the build).
2. WHEN a project is built with the epub builder and `viewcode_enable_epub` is
   set to `True`, THEN the build SHALL write a viewcode highlighted-source page
   for each module that has collected source data.

## Requirement 3: Suppress viewcode module pages for single-file HTML output

**User story:** As a documentation author producing single-file HTML, I want
viewcode not to emit separate per-module source pages, so that generation is
consistent with the single-file output format.

**Acceptance criteria**

1. WHEN the `html-collect-pages` event fires and the active builder's name is the
   single-file HTML builder name (`"singlehtml"`), THEN `collect_pages` SHALL
   emit no module source pages and no viewcode index page (it SHALL yield an
   empty sequence).

## Requirement 4: Preserve viewcode page generation for ordinary HTML builds

**User story:** As a documentation author building standard HTML, I want
viewcode to keep producing the highlighted module source pages and their
back-links, so that the existing HTML behavior is unchanged.

**Acceptance criteria**

1. WHEN the `html-collect-pages` event fires for a standard HTML build whose
   builder name is neither the single-file HTML name nor an epub-family name,
   THEN `collect_pages` SHALL build and emit a highlighted-source page for each
   collected module and the viewcode index page, as before.
2. The system SHALL keep the existing early return that yields no pages when no
   viewcode module data was collected during the build (i.e. when the
   environment holds no collected `_viewcode_modules` data).
3. The system SHALL keep viewcode's linkcode and local-source-file behaviors
   unchanged for HTML builds; the new output-format gating SHALL NOT alter the
   highlighted source content, the `[docs]` back-link anchors, or the set of
   pages emitted for a standard HTML build.
4. The output-format decision in `collect_pages` SHALL depend only on the active
   builder's name and, for the epub family, the `viewcode_enable_epub`
   configuration value; it SHALL NOT otherwise change which modules are
   collected or how their source is highlighted.
