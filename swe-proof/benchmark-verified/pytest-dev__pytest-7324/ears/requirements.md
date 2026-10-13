# Requirements — pytest match-expression identifier resolution (`-k` / `-m`)

## Introduction

Pytest's `-k` and `-m` selection accept a small boolean *match expression*
language (identifiers combined with `and`, `or`, `not`, and parentheses). The
grammar and evaluator live in `src/_pytest/mark/expression.py`: an expression
is scanned into tokens, parsed into a Python AST, compiled with the built-in
`compile()` in `eval` mode, and evaluated with `eval()` against a caller-
supplied matcher. Each bare identifier becomes an AST *name* node
(`ast.Name`), and at evaluation time the compiled code looks that name up
through `MatcherAdapter`, which forwards it to the matcher callable.

An identifier is any run of identifier characters (`\w`, `:`, `+`, `-`, `.`,
`[`, `]`) that is not one of the reserved operator words `and`, `or`, `not`.
This means the literal spellings `True`, `False`, and `None` are perfectly
legal *match-expression* identifiers, yet they are reserved words in Python's
own grammar. Turning such an identifier directly into a name node and compiling
it makes CPython reject the name: on a debug build of Python 3.8+ this trips a
C-level assertion in the compiler and aborts the interpreter (core dump)
instead of matching a test named `True`/`False`/`None`.

The goal is to make identifier resolution robust for *every* legal
match-expression identifier — including ones spelled like Python's reserved
constants — while preserving all existing parsing, boolean-evaluation, and
error-reporting behavior. The affected functions are `not_expr` (identifier →
name node), the empty-expression branch of `expression`, and
`MatcherAdapter.__getitem__` (name lookup → matcher call), all in
`src/_pytest/mark/expression.py`.

## Requirement 1: Identifiers spelled like Python reserved constants resolve normally

**User story:** As a pytest user, I want to select tests whose name or marker
is spelled `True`, `False`, or `None`, so that `-k`/`-m` expressions never
crash the interpreter and behave like any other identifier.

**Acceptance criteria**
1. WHEN a match expression consists of a single identifier whose text is
   exactly `True`, THEN `Expression.compile` followed by `evaluate` SHALL
   complete without raising `ParseError`, without any Python `SyntaxError` or
   compiler error, and without aborting the interpreter process.
2. WHEN a match expression consists of a single identifier whose text is
   exactly `False`, THEN evaluation SHALL complete normally under the same
   guarantees as criterion 1.
3. WHEN a match expression consists of a single identifier whose text is
   exactly `None`, THEN evaluation SHALL complete normally under the same
   guarantees as criterion 1.
4. WHEN any of the identifiers `True`, `False`, or `None` is evaluated against
   a matcher that reports that identifier as matching, THEN the expression
   SHALL evaluate to a boolean `True` result.
5. The system SHALL treat `True`, `False`, and `None` purely as ordinary
   identifier text for matching purposes, giving them no special boolean
   meaning of their own within the match-expression language.

## Requirement 2: The matcher receives the exact identifier text

**User story:** As a maintainer relying on the matcher callable, I want the
matcher to be queried with the identifier exactly as it appeared in the
expression, so that selection results are correct regardless of any internal
encoding used to build the AST.

**Acceptance criteria**
1. WHEN a bare identifier is evaluated, THEN `MatcherAdapter` SHALL invoke the
   matcher callable with a key string equal to the original identifier text as
   scanned from the expression — neither more nor fewer characters, and with no
   added, removed, or altered characters.
2. WHEN the matcher returns `True` for that identifier, THEN the single-
   identifier expression SHALL evaluate to `True`; WHEN the matcher returns
   `False`, THEN it SHALL evaluate to `False`.
3. The system SHALL apply this exact-text guarantee uniformly to every legal
   identifier, including identifiers spelled `True`, `False`, or `None`, so
   that no identifier is silently matched under a modified or mangled key.
4. IF the internal AST encoding of an identifier differs from its original
   text (for example to avoid colliding with Python reserved words), THEN the
   name-lookup step SHALL reverse that encoding before calling the matcher, so
   that criterion 1 holds.

## Requirement 3: Preserve boolean-expression evaluation semantics

**User story:** As a pytest user, I want `and`, `or`, `not`, parentheses, and
whitespace to keep working exactly as before, so that existing selection
expressions continue to produce the same results.

**Acceptance criteria**
1. WHEN an empty or whitespace-only expression is evaluated, THEN the result
   SHALL be `False`, independent of the matcher.
2. WHEN identifiers are combined with `and`, `or`, and `not`, THEN the
   expression SHALL evaluate according to standard boolean semantics, with
   `not` binding tighter than `and`, and `and` binding tighter than `or`.
3. WHEN parentheses are present, THEN they SHALL override the default operator
   precedence by grouping the enclosed sub-expression.
4. WHEN arbitrary spaces or tabs surround tokens or parentheses, THEN they
   SHALL be ignored and SHALL NOT change the evaluation result.
5. WHEN an identifier is resolved during evaluation, THEN its truth value SHALL
   be determined solely by the matcher's verdict on that identifier.
6. The result of `evaluate` SHALL be a genuine boolean value.

## Requirement 4: Preserve the accepted identifier alphabet

**User story:** As a pytest user, I want the full range of identifier spellings
to remain valid, so that names using digits, unicode letters, punctuation from
the identifier set, or words that are Python keywords still select correctly.

**Acceptance criteria**
1. WHEN a single identifier is composed of characters from the identifier set
   (word characters, `:`, `+`, `-`, `.`, `[`, `]`), THEN it SHALL be accepted
   and resolved through the matcher without a `ParseError`.
2. The system SHALL accept identifiers that consist of, begin with, or contain
   digits (for example purely numeric or decimal-point-containing spellings),
   as well as identifiers containing non-ASCII/unicode word characters.
3. The system SHALL accept identifiers whose text coincides with a Python
   keyword other than the expression operators, treating them as ordinary
   identifiers.
4. The system SHALL accept a single unbroken run of identifier characters that
   contains an operator word as an embedded substring as one identifier,
   without interpreting the embedded substring as an operator.
5. WHEN such an identifier is evaluated against a matcher that reports it as
   matching, THEN the expression SHALL evaluate to `True`.

## Requirement 5: Preserve rejection of illegal input with unchanged error reporting

**User story:** As a pytest user, I want malformed expressions and illegal
characters to keep producing the same clear parse errors, so that diagnostics
do not regress.

**Acceptance criteria**
1. WHEN the expression contains any character that is neither part of the
   identifier set (word characters, `:`, `+`, `-`, `.`, `[`, `]`) nor one of
   the operator, parenthesis, or whitespace characters the grammar recognizes —
   whether an ASCII punctuation symbol or a non-word unicode symbol — THEN
   evaluation SHALL raise `ParseError`.
2. WHEN the token stream is grammatically incomplete or misplaced (for example
   a dangling operator, an unmatched or empty parenthesis group, or two
   adjacent identifiers), THEN evaluation SHALL raise `ParseError`.
3. WHEN a `ParseError` is raised, THEN it SHALL carry the same 1-based `column`
   position and the same human-readable `message` text as before the change,
   including the "expected ...; got ..." wording and the "expected end of
   input; got ..." wording for trailing tokens.
4. The changes made to satisfy Requirements 1–2 SHALL NOT cause any previously
   valid expression to be rejected, nor any previously rejected expression to
   be accepted.
