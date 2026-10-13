# Requirements: correct inheritance-diagram image links in SVG output

## Introduction

The `sphinx.ext.inheritance_diagram` extension renders a class inheritance
diagram as an image with clickable links, one per class node. When the diagram
is emitted in SVG format the image is embedded as a standalone object served
from the builder's image directory (e.g. `_images/`), so the links inside the
SVG are resolved *relative to that image file*, not relative to the HTML page
that embeds it.

The affected code is `html_visit_inheritance_diagram` in
`sphinx/ext/inheritance_diagram.py`, specifically the loop that builds the
`urls` mapping (from a class's fully-qualified name to the link URL) that is
then handed to `generate_dot`. The pre-existing logic tried to compensate for
the SVG embedding by prepending `"../"` to every URL. That is wrong: the
resolved cross-reference URI (`refuri`) produced by Sphinx is already correct
for the page, and re-anchoring it with a blanket `"../"` produces links that
404 whenever the embedding page is not at the documentation root. It also
breaks absolute (external / intersphinx) URIs, which must never be prefixed.

The goal: make the per-class link URLs that `html_visit_inheritance_diagram`
puts into `urls` resolve to the correct target for both SVG and raster (PNG)
output, including intersphinx (external) references, while leaving raster
behavior and all non-HTML rendering paths unchanged.

## Requirement 1: Resolved document/external URIs are recorded verbatim

**User story:** As a documentation author embedding an inheritance diagram, I
want each class whose cross-reference resolved to a document URI to link to that
exact URI, so that the link works regardless of where the embedding page or the
SVG image lives.

**Acceptance criteria**

1. WHEN a diagram class carries a cross-reference that has a resolved
   destination URI (`refuri`), THEN `html_visit_inheritance_diagram` SHALL
   record that URI as the class's link URL **exactly as given**, with no leading
   path segment (in particular no `"../"`) added.
2. The system SHALL apply criterion 1 identically whether the graphviz output
   format is SVG or a raster (e.g. PNG) format — the recorded URL for a
   destination-URI reference SHALL NOT depend on the output format.
3. IF the recorded URI is an absolute URL (i.e. it contains a scheme separator
   such as `://`), THEN `html_visit_inheritance_diagram` SHALL leave it
   unmodified so that it still begins with its original scheme and host and is
   never turned into a relative path.

## Requirement 2: Keying of destination-URI references (internal vs external)

**User story:** As a maintainer, I want each class node keyed by the correct
name so that the URL is attached to the right node in the rendered diagram, for
both same-project and cross-project (intersphinx) references.

**Acceptance criteria**

1. WHEN a diagram class's cross-reference resolves within this same project
   (its reference is marked internal, which is also the default when no such
   marking is present), THEN `html_visit_inheritance_diagram` SHALL key that
   URL by the reference's title (the fully-qualified class name).
2. WHEN a diagram class's cross-reference resolves to a separate project (its
   reference is explicitly marked non-internal, e.g. an intersphinx link), THEN
   `html_visit_inheritance_diagram` SHALL key that URL by the trailing component
   of the destination URI following its final fragment separator (`#`), rather
   than by the reference title.
3. IF a destination URI contains no fragment separator, THEN the key derived in
   criterion 2 SHALL be the entire URI string.
4. The keying rules in criteria 1–2 SHALL be applied identically for SVG and
   raster output formats.

## Requirement 3: In-page anchor references for SVG output

**User story:** As a reader clicking a class in an SVG inheritance diagram whose
target is an anchor on the current page, I want the link to reach that anchor,
so that navigation from an embedded SVG works even for nested pages.

**Acceptance criteria**

1. WHEN the graphviz output format is SVG AND a diagram class's cross-reference
   has no destination URI but does have an in-page anchor identifier (`refid`),
   THEN `html_visit_inheritance_diagram` SHALL record the class's link URL as
   the current document's output name followed by the fragment separator `#` and
   the anchor identifier.
2. The current document's output name in criterion 1 SHALL be the document name
   currently being rendered combined with the builder's output file suffix
   (as computed for the page), and the recorded URL SHALL NOT be prefixed with
   any additional leading path segment such as `"../"`.
3. WHEN criterion 1 applies, THEN the recorded URL SHALL be keyed by the
   reference's title (the fully-qualified class name).

## Requirement 4: In-page anchor references for raster (non-SVG) output

**User story:** As a maintainer, I want the existing raster behavior for in-page
anchors preserved, so that fixing SVG does not regress PNG output.

**Acceptance criteria**

1. WHEN the graphviz output format is not SVG AND a diagram class's
   cross-reference has no destination URI but does have an in-page anchor
   identifier (`refid`), THEN `html_visit_inheritance_diagram` SHALL record the
   class's link URL as the fragment separator `#` immediately followed by the
   anchor identifier, keyed by the reference's title.
2. The system SHALL keep the raster in-page-anchor URL free of any document name
   or leading path segment (it SHALL remain a pure in-page anchor).

## Requirement 5: References carrying neither a URI nor an anchor

**User story:** As a maintainer, I want references that resolved to nothing to
be ignored, so that no spurious or empty links appear in the diagram.

**Acceptance criteria**

1. IF a diagram class's cross-reference has neither a destination URI nor an
   in-page anchor identifier, THEN `html_visit_inheritance_diagram` SHALL
   contribute no entry for that class to the link mapping.
2. WHEN a cross-reference has both a destination URI and an in-page anchor
   identifier, THEN `html_visit_inheritance_diagram` SHALL treat it under the
   destination-URI rules (Requirements 1 and 2) and SHALL NOT additionally apply
   the anchor rules.

## Requirement 6: Ordering and completeness of the link mapping

**User story:** As a consumer of the generated diagram, I want every resolvable
class to appear with the correct link and in a stable order, so that the
rendered image links are complete and deterministic.

**Acceptance criteria**

1. The system SHALL produce one link-mapping entry for each diagram
   cross-reference that has a destination URI or an in-page anchor identifier,
   processing the references in their given order.
2. The link URL and its key for each entry SHALL be fully determined by that
   reference's fields and the output format per Requirements 1–5, leaving no
   entry, key, or URL unspecified.

## Requirement 7: Preserve unaffected rendering paths

**User story:** As a maintainer, I want the change confined to HTML link-URL
construction, so that other rendering paths and diagram construction keep
working.

**Acceptance criteria**

1. The system SHALL keep the raster (PNG) HTML behavior for destination-URI
   references and in-page-anchor references unchanged relative to their
   pre-existing semantics (URIs recorded verbatim; anchors recorded as a pure
   `#`-prefixed identifier).
2. The system SHALL keep the LaTeX rendering of inheritance diagrams unchanged,
   including the set of class nodes and their base relationships collected for a
   diagram (each class contributes its name, its fully-qualified name, its list
   of base class names, and its optional tooltip).
3. The system SHALL keep class-name resolution for a diagram (the import and
   collection of the requested classes and their bases, including alias
   handling) behaving as before.
