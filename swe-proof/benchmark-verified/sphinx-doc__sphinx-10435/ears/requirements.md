# Requirements: LaTeX inline highlighted-code role must not add surrounding whitespace

## Introduction

When syntax highlighting is enabled for the Docutils `code` role (via a role
declared with a `:language:` option and the `highlight` class), Sphinx's LaTeX
writer renders the inline code by post-processing the Pygments highlighter's
`Verbatim` output into a `\sphinxcode{\sphinxupquote{...}}` group.

The current post-processing leaves the newline that Pygments places
immediately after the opening delimiter, and the newline that precedes the
closing delimiter, live in the emitted LaTeX. In the compiled PDF these
newlines render as a spurious space character at the very start and the very
end of the inline code span, so `:python:`def foo(...)`` shows leading and
trailing whitespace inside the highlighted run.

The affected code is the inline-literal handler in the LaTeX writer
(`visit_literal` in `sphinx/writers/latex.py`), specifically the branch that
handles a `code`-classed inline node that carries a language and is therefore
run through the highlighter. The goal is to emit LaTeX that produces no extra
whitespace at either end of the inline highlighted code, while leaving every
other literal-rendering path (plain inline literals, keyboard input,
literals in titles, and block-level highlighted code) exactly as before.

## Requirement 1: Suppress the leading whitespace of inline highlighted code

**User story:** As an author using an inline `code` role with a language, I
want the highlighted inline code to begin flush against its opening delimiter,
so that the PDF shows no stray space before the first token.

**Acceptance criteria**

1. WHEN the LaTeX writer renders an inline literal node that is classed as
   `code` and carries a non-empty `language`, THEN the writer SHALL run the
   node's text through the syntax highlighter and rewrite the highlighter's
   opening `Verbatim` delimiter into the inline-code opening group so that the
   emitted opening is `\sphinxcode{\sphinxupquote{` immediately followed by a
   `%` comment character.
2. The system SHALL ensure that the newline the highlighter emits right after
   the opening delimiter is commented out (by the `%` at the end of the opening
   line), so that no space is introduced before the first highlighted token in
   the rendered output.
3. WHEN the highlighted body is emitted, THEN the first highlighted token
   SHALL appear on the line immediately following the `%`-terminated opening,
   with nothing but that comment-suppressed newline between the opening group
   and the first token.

## Requirement 2: Suppress the trailing whitespace of inline highlighted code

**User story:** As an author using an inline `code` role with a language, I
want the highlighted inline code to end flush against its closing delimiter,
so that the PDF shows no stray space after the last token.

**Acceptance criteria**

1. WHEN the LaTeX writer has produced the rewritten highlighter output for an
   inline highlighted code node, THEN it SHALL strip the trailing whitespace
   and remove the highlighter's closing `Verbatim` delimiter together with the
   single newline that immediately precedes that delimiter, leaving the
   highlighted body ending exactly at its last token with no trailing newline.
2. WHEN the body has been trimmed, THEN the writer SHALL append a closing
   sequence consisting of a `%` comment character, then a single newline, then
   the two closing braces `}}`, so that the last highlighted token is
   immediately followed by `%`, a newline, and `}}`.
3. The system SHALL ensure the newline that separates the last token from the
   closing braces is comment-suppressed (by the appended `%`), so that no
   space is introduced after the last highlighted token in the rendered
   output.
4. IF the inline highlighted-code node has been emitted, THEN the writer SHALL
   NOT emit any further output for that node (its children are not descended
   into).

## Requirement 3: Preserve all other literal and code rendering paths

**User story:** As a maintainer, I want the whitespace fix to be scoped to the
inline highlighted-code path only, so that unrelated LaTeX output is
byte-for-byte unchanged.

**Acceptance criteria**

1. WHEN the LaTeX writer renders a `code`-classed inline block-level code
   listing (a highlighted code block), THEN it SHALL keep emitting the code
   inside a `sphinxVerbatim` environment whose body is preceded by a single
   newline after the environment's opening line and followed by a single
   newline before `\end{sphinxVerbatim}`, exactly as before this change.
2. WHEN the LaTeX writer renders a plain inline literal that is not classed as
   `code` or that carries no language, THEN it SHALL emit
   `\sphinxcode{\sphinxupquote{` (with no added comment character) and close
   the group with `}}` on departure, unchanged from prior behavior.
3. WHEN the LaTeX writer renders an inline literal inside a title, THEN it
   SHALL emit `\sphinxstyleliteralintitle{\sphinxupquote{` unchanged.
4. WHEN the LaTeX writer renders an inline literal classed as keyboard input
   (`kbd`), THEN it SHALL emit `\sphinxkeyboard{\sphinxupquote{` unchanged.
5. The system SHALL leave the highlighted body content (the sequence of
   highlighted tokens between the opening and closing delimiters) byte-for-byte
   identical to what the highlighter produced; only the surrounding delimiter
   handling changes.
