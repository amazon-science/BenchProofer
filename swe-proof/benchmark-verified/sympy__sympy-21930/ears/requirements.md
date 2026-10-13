# Requirements: LaTeX printing of second-quantization operators and tensors

## Introduction

The second quantization module (`sympy/physics/secondquant.py`) provides symbolic
creation/annihilation operators and antisymmetric tensors, each of which supplies a
`_latex` method consumed by SymPy's LaTeX printer (`sympy.printing.latex.latex`).

Three of these renderers emit a token that already contains a subscript, and — for the
raising (dagger) operators and the tensor — also a superscript. When such an object is
raised to a power (or otherwise embedded so that the surrounding LaTeX appends a further
superscript), the printer concatenates the object's LaTeX with a trailing `^{...}`. Because
the emitted token is not self-contained, the appended exponent produces an invalid double
superscript such as `b^\dagger_{0}^{2}`, which fails to render in LaTeX/Jupyter.

The goal is to make each of these three renderers emit its token as a single self-contained
group so that any exponent supplied by the surrounding expression binds to the whole token.
The affected renderers are the `_latex` methods of the bosonic creation operator
(`CreateBoson`, alias `Bd`), the fermionic creation operator (`CreateFermion`, alias `Fd`),
and the antisymmetric tensor (`AntiSymmetricTensor`, constructed via `AntiSymmetricTensor`/
`AT`). The annihilation operators (`AnnihilateBoson`/`B`, `AnnihilateFermion`/`F`) and the
container printers (commutator, normal-ordering) must retain their existing behavior.

## Requirement 1: Bosonic creation operator renders as a self-contained group

**User story:** As a user printing second-quantization expressions to LaTeX, I want a
bosonic creation operator to render as one grouped token, so that raising it to a power
produces valid LaTeX instead of an ill-formed double superscript.

**Acceptance criteria**
1. WHEN the LaTeX printer renders a bosonic creation operator built on a state named `s`,
   THEN the module SHALL produce the dagger-and-subscript token `b^\dagger_{s}` enclosed in
   a single outer brace pair, i.e. `{b^\dagger_{s}}`.
2. WHEN a bosonic creation operator is raised to a power and the whole expression is rendered
   to LaTeX, THEN the module SHALL emit the operator as a grouped token so the exponent binds
   to the entire token (yielding a form equivalent to `{b^\dagger_{s}}^{2}`, not
   `b^\dagger_{s}^{2}`).
3. The system SHALL derive the subscript from the operator's state name.

## Requirement 2: Fermionic creation operator renders as a self-contained group

**User story:** As a user printing fermionic second-quantization expressions to LaTeX, I want
a fermionic creation operator to render as one grouped token, so that composing or exponentiating
it yields valid LaTeX.

**Acceptance criteria**
1. WHEN the LaTeX printer renders a fermionic creation operator built on a state named `s`,
   THEN the module SHALL produce the dagger-and-subscript token `a^\dagger_{s}` enclosed in a
   single outer brace pair, i.e. `{a^\dagger_{s}}`.
2. WHEN a fermionic creation operator appears inside a larger expression that may append a
   superscript, THEN the module SHALL emit the operator as a grouped token so any appended
   exponent binds to the whole token.
3. The system SHALL derive the subscript from the operator's state name.

## Requirement 3: Antisymmetric tensor renders as a self-contained group

**User story:** As a user printing antisymmetric tensors to LaTeX, I want the tensor to render
as one grouped token, so that an appended superscript binds to the whole tensor.

**Acceptance criteria**
1. WHEN the LaTeX printer renders an antisymmetric tensor with symbol `t`, upper indices, and
   lower indices, THEN the module SHALL produce the token consisting of the symbol, an upper
   index block, and a lower index block — `t^{<upper>}_{<lower>}` — enclosed in a single outer
   brace pair, i.e. `{t^{<upper>}_{<lower>}}`.
2. The system SHALL form the upper index block as the in-order concatenation of the upper
   indices' names with no separator, and the lower index block as the in-order concatenation of
   the lower indices' names with no separator.
3. WHEN the tensor is embedded so that a further superscript is appended, THEN the module SHALL
   emit it as a grouped token so the exponent binds to the entire tensor token.

## Requirement 4: Annihilation operators keep their existing rendering

**User story:** As a maintainer, I want the annihilation operators' LaTeX unchanged, so that the
grouping fix does not alter tokens that never had the double-superscript problem.

**Acceptance criteria**
1. WHEN the LaTeX printer renders a bosonic annihilation operator built on a state named `s`,
   THEN the module SHALL produce `b_{s}` with no added outer brace pair.
2. WHEN the LaTeX printer renders a fermionic annihilation operator built on a state named `s`,
   THEN the module SHALL produce `a_{s}` with no added outer brace pair.

## Requirement 5: Container printers embed the grouped tokens without alteration

**User story:** As a user printing composite second-quantization expressions, I want commutators,
normal-ordered products, and products of operators to continue rendering with their usual
delimiters, now containing the grouped operator tokens.

**Acceptance criteria**
1. WHEN a commutator of two second-quantization expressions is rendered to LaTeX, THEN the module
   SHALL keep wrapping the two operands in `\left[ ... \right]` separated by a comma, with each
   creation-operator operand appearing as its grouped token.
2. WHEN a normal-ordered product is rendered to LaTeX, THEN the module SHALL keep wrapping the
   product in `\left\{ ... \right\}`, with each creation-operator factor appearing as its grouped
   token and adjacent factors separated by a space.
3. WHEN a bosonic creation operator raised to a power appears inside a commutator together with an
   annihilation operator, THEN the module SHALL render a well-formed result in which the exponent
   binds to the grouped creation-operator token and the annihilation operator keeps its plain
   subscripted form (e.g. `- \left[b_{0},{b^\dagger_{0}}^{2}\right]`).
4. The system SHALL leave the `repr`, `str`, and `srepr` textual forms of these operators and tensors
   unchanged by this fix.
