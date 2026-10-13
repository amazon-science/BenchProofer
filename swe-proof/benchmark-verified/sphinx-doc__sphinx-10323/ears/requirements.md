# Requirements: `literalinclude` de-indentation must not strip author-supplied prepend/append content

## Introduction

The `literalinclude` directive in Sphinx pulls a block of lines out of a source
file and can transform it through several options before rendering. Three of
those options matter here:

- `:dedent:` removes a uniform amount of leading whitespace from the included
  content so an example lines up neatly in the surrounding document (an integer
  count, or an automatic common-prefix removal when no count is given).
- `:prepend:` inserts an author-supplied line before the included block.
- `:append:` inserts an author-supplied line after the included block.

The transformation pipeline lives in `LiteralIncludeReader.read` in
`sphinx/directives/code.py`. `read` folds the file's line list through an
ordered list of filter callables (`pyobject_filter`, `start_filter`,
`end_filter`, `lines_filter`, `prepend_filter`, `append_filter`,
`dedent_filter`), each implemented as a method on `LiteralIncludeReader`.

The defect: the de-indentation pass (`dedent_filter`) ran **after**
`prepend_filter` and `append_filter`. As a result, de-indentation also stripped
leading whitespace from the author-supplied prepend/append lines, mangling their
indentation (and forcing a spurious "non-whitespace stripped by dedent" warning
when authors tried to pad the value manually). The goal is that de-indentation
apply **only** to the content selected from the source file, leaving the
prepend/append lines' leading whitespace intact.

## Requirement 1: De-indentation must not affect prepended/appended content

**User story:** As a documentation author, I want the `:dedent:` option to
re-indent only the code pulled from my source file, so that lines I add with
`:prepend:` and `:append:` keep exactly the leading whitespace I wrote.

**Acceptance criteria**

1. WHEN `LiteralIncludeReader.read` assembles the included block with a
   `:dedent:` option active together with a `:prepend:` value and an `:append:`
   value, THEN the reader SHALL apply the de-indentation only to the lines
   selected from the source file and SHALL emit the prepended and appended lines
   with their original leading whitespace unchanged.
2. WHEN de-indentation is requested alongside a `:prepend:` value, THEN the
   reader SHALL place the prepended line, verbatim (with its trailing newline),
   at the front of the already-de-indented file content, so that the prepended
   line's own leading whitespace is preserved.
3. WHEN de-indentation is requested alongside an `:append:` value, THEN the
   reader SHALL place the appended line, verbatim (with its trailing newline),
   at the end of the already-de-indented file content, so that the appended
   line's own leading whitespace is preserved.
4. The reader SHALL order the transformation steps so that the de-indentation of
   the selected source content occurs before either the prepend step or the
   append step, ensuring de-indentation can never see or alter the added lines.
5. WHEN de-indentation is requested together with prepend and/or append content,
   THEN the reader SHALL NOT emit a warning about non-whitespace being stripped
   from the author-supplied lines, since those lines are never subjected to
   de-indentation.

## Requirement 2: Preserve the existing selection and content behaviors

**User story:** As a documentation author relying on the other
`literalinclude` options, I want the fix to the de-indentation ordering to leave
every other transformation working exactly as before, so that my existing
documents render unchanged.

**Acceptance criteria**

1. The system SHALL continue to select source content using the existing
   filters — object extraction (`:pyobject:`), start markers
   (`:start-after:` / `:start-at:`), end markers (`:end-before:` / `:end-at:`),
   and explicit line ranges (`:lines:`) — applied first and in their existing
   relative order, before de-indentation, prepend, and append run.
2. WHEN only a `:prepend:` value is given (no `:dedent:`), THEN the reader SHALL
   insert that line, followed by a newline, at the front of the selected
   content, unchanged from prior behavior.
3. WHEN only an `:append:` value is given (no `:dedent:`), THEN the reader SHALL
   insert that line, followed by a newline, at the end of the selected content,
   unchanged from prior behavior.
4. WHEN a `:dedent:` value is given without any `:prepend:` or `:append:` value,
   THEN the reader SHALL de-indent the selected content exactly as it did
   before, producing the same result as the prior implementation.
5. WHEN a `:prepend:` or `:append:` option is present but its value is empty,
   THEN the reader SHALL NOT insert any line for that option (the insertion
   happens only for a non-empty value).
6. The reader SHALL continue to honor `:tab-width:` expansion and the combined
   tab-width-plus-de-indent behavior on the selected source content, unchanged.
7. The reader SHALL continue to apply `:dedent:` as either an explicit integer
   count of leading characters to remove or, when no count is supplied, an
   automatic removal of the common leading whitespace, unchanged.
8. The system SHALL continue to reject the previously invalid option
   combinations (for example `lineno-match` with `prepend` or `append`) with the
   existing error behavior.
