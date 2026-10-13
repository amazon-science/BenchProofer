# Requirements: Mathematica code printing of Max and Min

## Introduction

The Mathematica code printer (`sympy.printing.mathematica`, exposed through the
`mathematica_code` helper and its underlying `MCodePrinter`) converts SymPy
expressions into Wolfram Language source text. In the Wolfram Language, function
calls use **square brackets** — e.g. `Max[x, 2]` — and built-in symbols such as
`Max` and `Min` are spelled with a leading capital.

At present, applications of SymPy's `Max` and `Min` (the multi-argument
`MinMaxBase` family in `sympy.functions`) are not recognized by the printer's
function-rendering path. As a result they fall through to the generic string
representation, which emits round parentheses and a reordered argument list
(for example `Max(2, x)`), producing text that is **not** valid Wolfram Language.

The goal is to make the Mathematica printer render `Max` and `Min` applications
using the target language's square-bracket call syntax with the correct capitalized
name, exactly as it already does for other recognized functions, while preserving
all existing printing behavior.

## Requirement 1: Render Max and Min with Wolfram square-bracket call syntax

**User story:** As a user exporting SymPy expressions to Wolfram Language, I want
`Max` and `Min` to be printed as valid Wolfram function calls, so that the emitted
code runs in Mathematica without manual editing.

**Acceptance criteria**

1. WHEN `mathematica_code` is asked to render an application of `Max`, THEN the
   printer SHALL emit the literal name `Max` immediately followed by the argument
   list enclosed in square brackets, i.e. `Max[...]`, and SHALL NOT use round
   parentheses.
2. WHEN `mathematica_code` is asked to render an application of `Min`, THEN the
   printer SHALL emit the literal name `Min` immediately followed by the argument
   list enclosed in square brackets, i.e. `Min[...]`, and SHALL NOT use round
   parentheses.
3. WHEN a `Max` or `Min` application is rendered, THEN the printer SHALL render
   each argument by delegating to the same Mathematica printer and SHALL join the
   rendered argument fragments with a comma followed by a single space (`, `).
4. WHEN a `Max` or `Min` application has a single argument, THEN the printer SHALL
   emit that argument between the square brackets with no separator.
5. The system SHALL place the arguments inside the square brackets in the same
   order as they appear in the `Max` / `Min` expression being printed, introducing
   no additional reordering of its own.
6. WHEN a `Max` or `Min` argument is itself a compound expression, THEN the printer
   SHALL render that argument using its normal Mathematica representation (e.g. a
   nested `Max`/`Min` call again uses square brackets).

## Requirement 2: Compose correctly within larger expressions

**User story:** As a user, I want `Max`/`Min` calls to combine with surrounding
operators, so that expressions containing them print as coherent Wolfram code.

**Acceptance criteria**

1. WHEN a product contains a `Max` (or `Min`) application as a factor, THEN the
   printer SHALL render that factor as its square-bracket call form and join it to
   the other factors using the printer's existing multiplication syntax (`*`).
2. WHEN an expression contains both a `Max` application and a `Min` application
   combined by multiplication, THEN the printer SHALL render each in square-bracket
   form and produce their product as `Max[...]*Min[...]` (each bracketed call
   separated by `*`).
3. The system SHALL treat the recognition of `Max` and `Min` as case-sensitive:
   only the capitalized SymPy `Max`/`Min` symbols are rendered this way.

## Requirement 3: Preserve existing Mathematica printing behavior

**User story:** As a maintainer, I want all previously supported printing to keep
working unchanged, so that adding `Max`/`Min` support introduces no regressions.

**Acceptance criteria**

1. The system SHALL continue to render already-recognized elementary and special
   functions (for example `exp`, `sin`, `cos`, `tan`, and `conjugate`) with their
   established capitalized Wolfram names in square-bracket call syntax.
2. WHEN an application of an unrecognized function `f` is rendered, THEN the printer
   SHALL emit the function's own name followed by its arguments in square brackets
   (e.g. `f[x, y, z]`), joining arguments with `, `.
3. The system SHALL continue to render integers and rational numbers in their
   existing Wolfram forms, including negative and fractional values.
4. The system SHALL continue to render powers using caret syntax (`base^exp`) with
   its existing parenthesization rules.
5. The system SHALL continue to render products using its existing multiplication
   syntax, including the handling of noncommutative factors.
6. The system SHALL continue to render mathematical constants (such as `Pi`,
   positive infinity as `Infinity`, and negative infinity as `-Infinity`) in their
   existing Wolfram forms.
7. The system SHALL continue to render list, tuple, and `Tuple` containers using
   Wolfram curly-brace syntax (`{...}`) with comma-space-separated elements.
8. The system SHALL continue to render integrals and derivatives using their
   existing held Wolfram forms (`Hold[Integrate[...]]` and `Hold[D[...]]`).
9. WHILE rendering any expression, the printer SHALL leave the output for
   expressions that contain no `Max` or `Min` unchanged from its prior behavior.
