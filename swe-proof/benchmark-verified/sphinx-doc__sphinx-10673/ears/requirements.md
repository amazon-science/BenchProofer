# Requirements: Allow toctree entries to reference the built-in index pages

## Introduction

Sphinx automatically generates three special reference pages for every project:
the general index (`genindex`), the Python module index (`modindex`), and the
search page (`search`). Users frequently want to link these pages from a
`.. toctree::` directive, for example under an "Indices and tables" caption:

```
.. toctree::
   :maxdepth: 1
   :caption: Indices and tables

   genindex
   modindex
   search
```

Before this change, listing any of these three names in a toctree produced a
build warning of the form *"toctree contains reference to nonexisting document
'genindex'"* (likewise for `modindex` and `search`), and the entry was dropped
so no navigation link was produced. This happened because the toctree machinery
recognised only documents present in the environment's set of found source
documents; the three index pages have no source file, so they were rejected.

These three page names are already registered by the standard domain
(`sphinx/domains/std.py`) in its initial label table (labelname → target
docname, label id, section title): `genindex` → (`genindex`, Index),
`modindex` → (`py-modindex`, Module Index), `search` → (`search`, Search Page).

The goal is to treat this set of generated reference-page names as legitimate
toctree targets across the three places that consume toctree entries:

- `TocTree.parse_content` in `sphinx/directives/other.py` — parses the directive
  body into toctree entries.
- `TocTreeAdapter.resolve` (its inner entry-collection helper) in
  `sphinx/environment/adapters/toctree.py` — turns entries into rendered
  navigation nodes.
- `TocTreeCollector.assign_figure_numbers` in
  `sphinx/environment/collectors/toctree.py` — walks toctree entries to assign
  figure numbers.

Throughout this document, "generated reference-page name" means one of the
labelnames registered in the standard domain's initial label table (currently
`genindex`, `modindex`, `search`), and "target set" means the union of the
environment's found source documents with that set of generated reference-page
names.

## Requirement 1: Accept generated reference-page names as explicit toctree entries

**User story:** As a documentation author, I want to list `genindex`,
`modindex`, or `search` directly in a toctree directive, so that I can link the
built-in index and search pages without a build warning.

**Acceptance criteria**

1. WHEN `TocTree.parse_content` processes a non-glob directive line whose target
   resolves to a generated reference-page name, THEN it SHALL treat that name as
   an existing target and SHALL NOT emit a "toctree contains reference to
   nonexisting document" warning for it.
2. WHEN `TocTree.parse_content` accepts a directive line naming a generated
   reference-page name, THEN it SHALL append a corresponding entry to the
   toctree's list of entries, preserving the order in which the names appear in
   the directive body.
3. WHEN a directive line names a generated reference-page name with no explicit
   title, THEN the appended entry SHALL record no explicit title (a null title)
   paired with that name as its target.
4. WHEN a directive body lists several such names (for example `genindex`,
   `modindex`, and `search` in that order), THEN the resulting entries SHALL
   appear as one entry per name in exactly the listed order, each carrying the
   name as its target.
5. The system SHALL determine the set of generated reference-page names from the
   standard domain's initial label table rather than from a hard-coded list, so
   that the accepted names stay in agreement with the labels the domain
   registers.

## Requirement 2: Do not auto-include generated pages via glob patterns

**User story:** As a documentation author using globbed toctrees, I want the
built-in index pages excluded from glob expansion, so that they are only linked
when I name them explicitly.

**Acceptance criteria**

1. WHEN `TocTree.parse_content` expands a glob entry, THEN it SHALL NOT add any
   generated reference-page name to the toctree entries even if such a name
   would match the glob pattern.
2. The system SHALL continue to expand glob patterns over the ordinary found
   source documents exactly as before, appending the matched documents (sorted)
   as entries and to the list of include files.
3. IF a glob pattern matches no name at all in the target set (that is, it
   matches neither an ordinary found document nor a generated reference-page
   name), THEN `parse_content` SHALL still emit its existing "toctree glob
   pattern didn't match any documents" warning.
4. IF a glob pattern matches only generated reference-page names (and no
   ordinary found document), THEN `parse_content` SHALL append no entry for
   those generated names and SHALL NOT emit the "didn't match any documents"
   warning, because a match against the target set (which now includes the
   generated names) was found.

## Requirement 3: Render navigation links for generated reference-page entries

**User story:** As a documentation reader, I want the index and search pages to
appear as working links in the generated table of contents, so that I can
navigate to them.

**Acceptance criteria**

1. WHEN the toctree adapter's entry-collection resolves an entry whose target is
   a generated reference-page name, THEN it SHALL produce an internal reference
   node pointing at that page's registered target docname.
2. IF such an entry carries no explicit title, THEN the produced reference SHALL
   use the section title registered for that name in the standard domain's label
   table (for example "Index", "Module Index", or "Search Page").
3. IF such an entry carries an explicit title, THEN the produced reference SHALL
   use that explicit title as its link text.
4. WHEN rendering a generated reference-page entry, THEN the adapter SHALL wrap
   the reference so that no child sub-items are shown beneath it.

## Requirement 4: Skip generated reference-page entries during figure numbering

**User story:** As a maintainer, I want figure numbering to ignore the built-in
reference pages, so that building a project whose toctree links them does not
fail or misbehave.

**Acceptance criteria**

1. WHEN `TocTreeCollector.assign_figure_numbers` walks toctree entries and
   encounters an entry whose target is a generated reference-page name, THEN it
   SHALL skip that entry and SHALL NOT attempt to recurse into it as if it were a
   source document.
2. The system SHALL continue to skip external-URL entries and `self` entries
   during this walk, as it did before.

## Requirement 5: Preserve existing toctree behavior for ordinary targets

**User story:** As a maintainer, I want all previously correct toctree behavior
to remain unchanged, so that this change adds support for the index pages
without regressions.

**Acceptance criteria**

1. WHEN a directive line names an ordinary source document that exists in the
   environment's found documents, THEN `parse_content` SHALL keep appending it
   as a toctree entry and to the include-files list, exactly as before.
2. IF a directive line names a document that is neither a found source document
   nor a generated reference-page name, THEN `parse_content` SHALL keep emitting
   the appropriate "nonexisting document" or "excluded document" warning and
   SHALL NOT append an entry for it.
3. WHEN a directive line is an external URL or the literal `self`, THEN
   `parse_content` SHALL keep appending it as an entry with its title unchanged.
4. WHEN the same ordinary document is listed more than once, THEN `parse_content`
   SHALL keep emitting its existing "duplicated entry found in toctree" warning.
5. The system SHALL keep the toctree adapter's rendering of ordinary document
   entries, external URLs, `self` references, and title-only pruning behaving as
   before.
6. The system SHALL keep figure numbering, section numbering, and the depth,
   caption, glob, hidden, titles-only, and numbered attributes of resolved
   toctrees behaving as before for ordinary documents.
