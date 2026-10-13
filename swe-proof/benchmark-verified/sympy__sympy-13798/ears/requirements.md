# Requirements: Allow an arbitrary `mul_symbol` in LaTeX printing

## Introduction

SymPy's LaTeX pretty-printer, exposed through `sympy.printing.latex.latex()`
and the underlying `LatexPrinter` class (`sympy/printing/latex.py`), accepts a
`mul_symbol` setting that controls the separator inserted between the factors
of a product. Historically this setting was restricted to a fixed set of four
named choices (the absent/`None` default, `"ldot"`, `"dot"`, and `"times"`);
supplying anything else caused printer construction to fail.

Users want to render products with a separator of their own choosing — for
example a thin space (`\,`) — instead of being limited to the four built-in
names. The goal is to let `mul_symbol` be **any** string while remaining fully
backwards-compatible with the four named selectors and with the existing
default behavior.

The affected logic lives in `LatexPrinter.__init__`, where the `mul_symbol`
setting is translated into two internal separator strings:

- `mul_symbol_latex` — the separator placed between general (symbolic) factors
  of a product (consumed by `_print_Mul`, `_print_PolyElement`, etc.).
- `mul_symbol_latex_numbers` — the separator placed between numeric factors and
  in scientific-notation number rendering (consumed by `_print_Mul` and
  `_print_Float`).

The four built-in selectors map to these LaTeX fragments:

| selector | separator fragment |
|---|---|
| absent / `None` (default) | `" "` (a single space) |
| `"ldot"` | `" \,.\, "` |
| `"dot"` | `" \cdot "` |
| `"times"` | `" \times "` |

## Requirement 1: Accept an arbitrary custom multiplication symbol

**User story:** As a user of the LaTeX printer, I want to pass any string as
`mul_symbol`, so that I can separate product factors with a symbol (such as a
thin space) that is not one of the four built-in names.

**Acceptance criteria**

1. WHEN a `LatexPrinter` is constructed (or `latex()` is called) with a
   `mul_symbol` value that is not one of the four recognized selectors
   (absent/`None`, `"ldot"`, `"dot"`, `"times"`), THEN construction SHALL
   succeed without raising an error.
2. WHEN `mul_symbol` is a string that is not one of the four recognized
   selectors, THEN the printer SHALL use that string verbatim as the separator
   placed between general (symbolic) factors of a product.
3. WHEN a product of symbolic factors is printed under a custom `mul_symbol`,
   THEN the resulting LaTeX SHALL place the custom string, and only the custom
   string, directly between each adjacent pair of factors, adding no extra
   surrounding spaces of its own. For example, printing the product of `3`,
   `x**2`, and `y` with `mul_symbol=r"\,"` SHALL yield `3\,x^{2}\,y`.
4. The printer SHALL treat a custom `mul_symbol` string exactly as given,
   performing no substitution, escaping, or reinterpretation of its characters
   for the general-factor separator.

## Requirement 2: Choose the numeric separator for a custom symbol

**User story:** As a user supplying a custom `mul_symbol`, I want the separator
used between purely numeric factors to stay legible, so that expressions like
`2.5 \cdot 10^{20}` do not collapse into an ambiguous spacing.

**Acceptance criteria**

1. WHEN `mul_symbol` is a custom string whose surrounding-whitespace-stripped
   form is empty, or is a LaTeX horizontal-spacing command that inserts blank
   space without rendering any visible glyph (for example the thin space `\,`),
   THEN the printer SHALL use the dotted separator `" \cdot "` as the separator
   between numeric factors, even though the general-factor separator remains the
   custom string.
2. WHEN `mul_symbol` is a custom string whose stripped form is NOT empty and
   NOT one of those spacing commands, THEN the printer SHALL use that same
   custom string verbatim as the separator between numeric factors.
3. WHEN a `Float` is rendered in scientific notation (mantissa × 10 raised to a
   power) under a custom `mul_symbol`, THEN the mantissa and the `10^{...}`
   factor SHALL be joined by the numeric separator determined by criteria 1–2.
4. The determination of the numeric separator SHALL depend only on the stripped
   form of the supplied `mul_symbol`, ignoring leading and trailing whitespace
   when comparing against the spacing commands.

## Requirement 3: Preserve the four built-in selectors (regression protection)

**User story:** As an existing user relying on the named `mul_symbol` choices,
I want their behavior to be exactly unchanged, so that upgrading does not alter
any existing LaTeX output.

**Acceptance criteria**

1. WHEN `mul_symbol` is absent or `None`, THEN the general-factor separator
   SHALL keep being a single space `" "`, and the numeric separator SHALL keep
   being the dotted separator `" \cdot "`.
2. WHEN `mul_symbol` is `"dot"`, THEN both the general-factor separator and the
   numeric separator SHALL keep being `" \cdot "`.
3. WHEN `mul_symbol` is `"times"`, THEN both the general-factor separator and
   the numeric separator SHALL keep being `" \times "`.
4. WHEN `mul_symbol` is `"ldot"`, THEN both the general-factor separator and the
   numeric separator SHALL keep being `" \,.\, "`.
5. The printer SHALL keep rendering products, numeric coefficients, integrals,
   and all other expressions that rely on these separators exactly as before
   whenever one of the four built-in selectors (or the default) is in effect,
   introducing no change in their LaTeX output.
