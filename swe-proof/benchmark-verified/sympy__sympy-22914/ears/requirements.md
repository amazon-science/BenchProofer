## Introduction

SymPy's Python code generation facilities (`sympy.printing.pycode`, exposed
through the `pycode` helper and the `PythonCodePrinter` class) translate SymPy
expressions into plain-Python source strings. When an expression contains the
symbolic `Min` or `Max` functions (`sympy.functions.Min`,
`sympy.functions.Max`), the `PythonCodePrinter` currently does not render them
as the Python built-ins `min`/`max`, so the generated source for such
expressions is not a direct `min(...)`/`max(...)` call.

Plain Python already provides the built-in functions `min` and `max` whose
semantics match SymPy's `Min`/`Max` for the printed form. The goal of this
change is to make `PythonCodePrinter` emit these built-ins so that generated
code for expressions containing `Min`/`Max` is valid, runnable Python. Because
the mpmath code printer derives from `PythonCodePrinter` and shares its table
of known functions, this same change also causes the mpmath printer to render
`Min`/`Max` as `min(...)`/`max(...)`; every other printing behavior of the
pycode printers is left unchanged.

## Requirement 1: Emit Python built-ins for Min and Max

**User story:** As a developer generating Python code from SymPy expressions,
I want `Min` and `Max` to be rendered as calls to Python's built-in `min` and
`max`, so that the generated source is valid, executable Python instead of an
unsupported placeholder.

**Acceptance criteria**

1. WHEN `PythonCodePrinter` is asked to print an expression whose top-level
   function is `Min`, THEN the printer SHALL produce the string `min(` followed
   by the printed arguments and a closing `)`.
2. WHEN `PythonCodePrinter` is asked to print an expression whose top-level
   function is `Max`, THEN the printer SHALL produce the string `max(` followed
   by the printed arguments and a closing `)`.
3. WHEN the printed function has more than one argument, THEN the arguments
   SHALL appear inside the parentheses separated by a comma and a single space,
   in the same order as the function's arguments.
4. WHEN each argument is itself printed, THEN the printer SHALL render it using
   its normal Python printing rules (for example a plain symbol renders as its
   symbol name), so that `Min(x, y)` renders exactly as `min(x, y)` and
   `Max(x, y)` renders exactly as `max(x, y)`.
5. The system SHALL NOT emit any "not supported" comment or the bare
   `Min(...)`/`Max(...)` fallback text when printing `Min` or `Max` with
   `PythonCodePrinter`.

## Requirement 2: Preserve existing pycode printing behavior

**User story:** As a maintainer, I want the addition of `Min`/`Max` support to
leave all other code-printing behavior intact, so that no existing generated
output regresses.

**Acceptance criteria**

1. The system SHALL continue to print all previously supported functions,
   operators, and objects (including `Abs`, `sqrt`, `frac`, `Piecewise`,
   integrals, and the special functions already handled) exactly as before.
2. WHEN `PythonCodePrinter` prints tuples, lists, or other already-supported
   container and standard forms, THEN it SHALL produce the same output as
   before this change.
3. The system SHALL keep the existing behavior of the NumPy and SciPy code
   printers unchanged for all expressions they already handled, including their
   own established rendering of `Min`/`Max` (which is not the plain `min`/`max`
   built-in form).
4. WHEN the mpmath code printer, which derives from `PythonCodePrinter`, is
   asked to print an expression whose top-level function is `Min` or `Max`,
   THEN it SHALL render it as `min(...)`/`max(...)` in the same manner as
   `PythonCodePrinter`, and SHALL keep all its other printing behavior
   unchanged.
5. The system SHALL continue to honor reserved-word handling and the standard
   printer configuration without alteration.
