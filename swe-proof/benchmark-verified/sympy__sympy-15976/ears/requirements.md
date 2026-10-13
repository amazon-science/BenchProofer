# Requirements: MathML presentation rendering of symbols with sub/superscripts

## Introduction

When SymPy renders an expression as **MathML presentation markup**, symbols
whose names carry a numeric or textual subscript/superscript (for example a
variable named `x2`, or `x^2`, `x_2`, `x^3_2`) are produced with an extra,
redundant identifier (`<mi>`) element wrapped around the scripted markup — e.g.
`<mi><msub><mi>x</mi><mi>2</mi></msub></mi>`. That extra wrapper makes the
symbol render as an ordinary invisible/blank identifier in strict MathML
renderers (e.g. Safari), so the symbol disappears from the displayed output.

The affected code is the presentation printer's symbol handler,
`MathMLPresentationPrinter._print_Symbol(self, sym, style='plain')` in
`sympy/printing/mathml.py` (the presentation printer; the *content* printer's
own `_print_Symbol` is a separate, unrelated method). `_print_Symbol` is also
reached indirectly through `_print_MatrixSymbol` and `_print_RandomSymbol`.

The goal: the presentation markup for a symbol must be the scripted element
itself (`msub` / `msup` / `msubsup`), or a bare `mi` for an undecorated name —
with no superfluous outer `<mi>` wrapper — while preserving the internal layout
of the base name and the decoration pieces, the ordering of sub- vs
superscripts, and the optional bold styling.

Throughout this document, the "decomposed pieces" of a symbol are the base
`name` string together with an ordered list of superscript strings and an
ordered list of subscript strings, as produced by SymPy's existing name-parsing
and per-piece unicode-translation helpers. Rendering those helpers is
unchanged; only the assembly of the final markup node is in scope.

## Requirement 1: Undecorated symbol renders as a bare identifier

**User story:** As a user printing a plain symbol to MathML presentation
markup, I want the symbol rendered as a single identifier element, so that it
displays correctly without redundant wrapping.

**Acceptance criteria**

1. WHEN the presentation printer renders a symbol whose decomposed pieces
   contain no superscripts and no subscripts, THEN the printer SHALL return an
   element whose node name is `mi`.
2. WHEN such an undecorated symbol is rendered, THEN the returned `mi` element
   SHALL contain exactly one text child whose value is the (translated) base
   name.
3. WHEN such an undecorated symbol is rendered, THEN the returned element SHALL
   NOT be wrapped inside any additional enclosing element.

## Requirement 2: Symbol with subscripts only

**User story:** As a user printing a subscripted symbol (e.g. `x_2`), I want the
top-level markup to be the subscript element itself, so that renderers display
the subscript correctly and the symbol is visible.

**Acceptance criteria**

1. WHEN the presentation printer renders a symbol whose decomposed pieces
   contain at least one subscript and no superscripts, THEN the returned
   element's node name SHALL be `msub`.
2. WHEN such a subscripted symbol is rendered, THEN the returned `msub`
   element's first child SHALL be an `mi` element whose text value is the base
   name.
3. WHEN such a subscripted symbol is rendered, THEN the returned `msub`
   element's second child SHALL be the laid-out subscript markup (per
   Requirement 5).
4. The returned `msub` element SHALL NOT be enclosed within an additional
   `mi` (or any other) wrapper element.

## Requirement 3: Symbol with superscripts only

**User story:** As a user printing a superscripted symbol (e.g. `x^2` or
`x__2`), I want the top-level markup to be the superscript element itself, so
that renderers display the superscript correctly.

**Acceptance criteria**

1. WHEN the presentation printer renders a symbol whose decomposed pieces
   contain at least one superscript and no subscripts, THEN the returned
   element's node name SHALL be `msup`.
2. WHEN such a superscripted symbol is rendered, THEN the returned `msup`
   element's first child SHALL be an `mi` element whose text value is the base
   name.
3. WHEN such a superscripted symbol is rendered, THEN the returned `msup`
   element's second child SHALL be the laid-out superscript markup (per
   Requirement 5).
4. The returned `msup` element SHALL NOT be enclosed within an additional
   `mi` (or any other) wrapper element.

## Requirement 4: Symbol with both subscripts and superscripts

**User story:** As a user printing a symbol carrying both a subscript and a
superscript (e.g. `x^3_2`), I want the top-level markup to be the combined
sub/superscript element itself, in the correct child order.

**Acceptance criteria**

1. WHEN the presentation printer renders a symbol whose decomposed pieces
   contain at least one superscript and at least one subscript, THEN the
   returned element's node name SHALL be `msubsup`.
2. WHEN such a symbol is rendered, THEN the returned `msubsup` element's first
   child SHALL be an `mi` element whose text value is the base name.
3. WHEN such a symbol is rendered, THEN the returned `msubsup` element's second
   child SHALL be the laid-out subscript markup and its third child SHALL be the
   laid-out superscript markup (subscripts before superscripts, per
   Requirement 5).
4. The returned `msubsup` element SHALL NOT be enclosed within an additional
   `mi` (or any other) wrapper element.

## Requirement 5: Layout of a decoration collection

**User story:** As a user, I want each collection of subscript/superscript
pieces laid out consistently, so that single and multiple pieces render
correctly.

**Acceptance criteria**

1. WHEN a decoration collection (subscripts or superscripts) consists of exactly
   one piece, THEN the printer SHALL lay it out as a single `mi` element whose
   text value is that piece.
2. WHEN a decoration collection consists of more than one piece, THEN the
   printer SHALL lay it out as an `mrow` element containing each piece as an
   `mi` element in order.
3. WHILE laying out a multi-piece decoration collection as an `mrow`, the
   printer SHALL insert, before every piece after the first, an `mo` element
   whose single text child has the value of one space character (`" "`).
4. WHEN a multi-piece decoration collection is laid out, THEN the resulting
   `mrow` child sequence SHALL be, in order: the first piece's `mi`, then for
   each subsequent piece the separating `mo` followed by that piece's `mi`.

## Requirement 6: Bold styling is applied to the top-level element

**User story:** As a caller who requests bold rendering (e.g. via a matrix
symbol style), I want the bold attribute applied to the final markup element, so
that the whole symbol is styled without introducing a redundant wrapper.

**Acceptance criteria**

1. IF the requested style is `bold`, THEN the printer SHALL set the attribute
   `mathvariant` to the value `bold` on the top-level returned element
   (whichever of `mi`, `msub`, `msup`, or `msubsup` it is).
2. IF the requested style is not `bold`, THEN the printer SHALL NOT set a
   `mathvariant` attribute on the returned element.
3. WHEN the bold attribute is applied, THEN it SHALL be set on the outermost
   returned element, not on an extra enclosing wrapper.

## Requirement 7: Preserve unrelated symbol-printing behavior (regression)

**User story:** As a maintainer, I want the rest of MathML printing to keep
working exactly as before, so that removing the redundant wrapper fixes the bug
without regressions.

**Acceptance criteria**

1. The system SHALL keep the presentation printer's rendering of the base name
   as an `mi` element carrying the (translated) name as its text.
2. The system SHALL keep applying the existing name decomposition and per-piece
   unicode translation so that Greek and other special names continue to render
   as before.
3. WHEN a matrix symbol is rendered via the presentation printer, THEN it SHALL
   produce the same markup structure as an ordinary symbol with the configured
   style (including bold when that style is configured).
4. The system SHALL leave the MathML *content* printer's symbol rendering
   unchanged.
5. The system SHALL leave all other presentation-printer output (numbers, powers
   and root notation, sums, integrals, limits, matrices, relational operators,
   constants, trigonometric functions, ordering, and printer settings)
   unchanged.
