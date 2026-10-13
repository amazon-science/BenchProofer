# Requirements: Correctly trim view/model docstrings whose first line is not empty

## Introduction

The admin documentation generator renders the docstrings of views, models, and
model methods as reStructuredText. Before a docstring is handed to the reST
renderer it is passed through a whitespace-normalization step that lives in
`django.contrib.admindocs.utils.parse_docstring` (and is applied again to model
method docstrings in `django.contrib.admindocs.views.ModelDetailView.get_context_data`).

The normalization must follow the conventional PEP 257 rule for laying out an
indented text block: strip the first line's leading whitespace, then dedent the
remaining lines by their common leading-whitespace amount.

Historically the common-indentation amount was computed over *all* lines,
including the first. Most Django docstrings put no text on the first physical
line (the text starts on the second line), so the first line contributed no
leading whitespace and the computation was correct for them. But a docstring
whose text begins on the very first line, e.g.

```
def test():
    """test tests something.
    """
```

has a first line with zero leading whitespace, so the computed common
indentation collapses to `0` and the body lines are never dedented. The still-
indented body is then interpreted by the reST renderer as an indented block,
producing a rendering error/warning (for example an `Error in "default-role"
directive: no content permitted.` emitted to standard error) instead of clean
output.

The goal is to normalize docstring indentation using the PEP 257 algorithm so
that a docstring whose first line carries text is trimmed correctly — the
common indentation is measured over the lines that follow the first — while the
existing title/body/metadata parsing and the rendering of empty-first-line
docstrings remain unchanged.

## Requirement 1: Trim indentation using the lines after the first

**User story:** As a developer who documents a view or model method with a
docstring whose text starts on the first line, I want admindocs to render that
docstring cleanly, so that the documentation page shows my description without
reST errors or spurious output.

**Acceptance criteria**

1. WHEN `parse_docstring` receives a docstring whose first physical line
   contains non-whitespace text, THEN it SHALL compute the common leading-
   whitespace amount to remove from the trailing lines using only the lines
   that follow the first line (never letting the first line's leading whitespace
   force that amount to zero).
2. WHEN a docstring is normalized, THEN `parse_docstring` SHALL strip all
   leading whitespace from the first line, and SHALL remove exactly the common
   leading-whitespace amount (the smallest leading-whitespace count among the
   non-blank lines that follow the first) from each of the remaining lines.
3. WHEN a docstring has content on its first line followed by an indented body
   (for example a first line of text, a blank line, and an indented second
   line), THEN after normalization the body text SHALL have its shared leading
   indentation removed so that it is not left indented relative to the first
   line.
4. WHEN the normalized title and the normalized body of such a docstring are
   each rendered as reStructuredText, THEN each SHALL render as ordinary
   paragraph content and the rendering SHALL NOT emit any warning or error text
   to standard error.
5. WHEN there is no non-blank line after the first line, THEN `parse_docstring`
   SHALL leave the lines after the first unchanged (it SHALL NOT fail while
   determining the common indentation amount).
6. The normalization SHALL remove completely empty lines from the beginning and
   the end of the block, and SHALL expand tab stops before measuring
   indentation, consistent with the PEP 257 docstring-cleaning rule.

## Requirement 2: Handle empty or missing docstrings

**User story:** As a maintainer, I want `parse_docstring` to behave predictably
when there is nothing to parse, so that callers never receive malformed output
for an absent docstring.

**Acceptance criteria**

1. IF the docstring passed to `parse_docstring` is `None` or an empty string
   (i.e. falsy), THEN `parse_docstring` SHALL short-circuit and return an empty
   title, an empty body, and an empty metadata mapping.
2. WHEN the docstring is a non-empty string, THEN `parse_docstring` SHALL NOT
   take the empty-result short-circuit but SHALL normalize the docstring per the
   PEP 257 rule of Requirement 1; consequently the empty title / empty body /
   empty metadata result is produced ONLY for a `None` or empty-string docstring
   and SHALL NOT be assumed for a docstring that merely contains whitespace.

## Requirement 3: Preserve title, body, and metadata parsing (regression protection)

**User story:** As a user of the admindocs pages, I want existing docstrings —
especially Django's own empty-first-line style — to keep parsing and rendering
exactly as they did, so that upgrading changes nothing for correctly formatted
docstrings.

**Acceptance criteria**

1. WHEN `parse_docstring` normalizes a docstring whose first physical line is
   empty (text begins on a later line), THEN the resulting title, body, and
   metadata SHALL be identical to the previously produced values for that
   docstring.
2. WHEN a normalized docstring is split into paragraphs, THEN `parse_docstring`
   SHALL treat the first paragraph as the title and SHALL join the remaining
   paragraphs (separated by blank lines) as the body.
3. WHEN the final paragraph of a docstring parses as RFC-822-style header
   metadata (`key: value` lines), THEN `parse_docstring` SHALL return that
   metadata as a mapping and SHALL exclude that trailing paragraph from the
   body; WHEN the final paragraph yields no such metadata, THEN the metadata
   mapping SHALL be empty and that paragraph SHALL remain part of the body.
4. The system SHALL continue to expose the `parse_docstring` and `parse_rst`
   helpers with unchanged signatures and return shapes so that existing callers
   in the admindocs views keep working.

## Requirement 4: Apply the same trimming to rendered model method docstrings

**User story:** As a user browsing a model's documentation, I want each model
method's docstring rendered cleanly regardless of whether its text starts on the
first line, so that method descriptions display consistently.

**Acceptance criteria**

1. WHEN `ModelDetailView.get_context_data` prepares a model method's or
   property's docstring for display, THEN it SHALL normalize that docstring with
   the same PEP 257 indentation-trimming rule used by `parse_docstring` before
   passing it to the reST renderer.
2. WHEN a model method's docstring has text on its first line, THEN its rendered
   `verbose` output SHALL be produced without reST errors caused by residual
   body indentation.
3. WHEN a model method has no docstring, THEN `get_context_data` SHALL leave its
   rendered `verbose` value falsy (it SHALL NOT attempt to normalize or render a
   missing docstring).
