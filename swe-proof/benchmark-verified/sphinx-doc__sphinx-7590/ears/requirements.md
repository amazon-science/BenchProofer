# Requirements: C++ user-defined literal support in the C++ domain expression parser

## Introduction

Sphinx's C++ domain parses C++ expressions (for example the initializer of a
`constexpr` variable) and computes a mangled identifier ("id") for each parsed
literal. The expression parser lives in `sphinx/domains/cpp.py`
(`DefinitionParser._parse_literal`, together with the literal AST node classes
and their `get_id` methods) and relies on the lexical recognisers defined in
`sphinx/util/cfamily.py` (the integer/float/character/string literal regular
expressions).

Currently the parser recognises numeric, character and string literals with the
standard C++ suffixes only. When a literal is immediately followed by an
identifier — a C++ *user-defined literal* (UDL), such as `6.62607015e-34q_J`
from the reported issue, or `1q_s`, or `5_udl` — the trailing identifier is left
unconsumed and parsing aborts with an "Expected end of definition" error, so any
declaration containing a UDL fails to build.

The goal is to make `_parse_literal` recognise a base literal optionally followed
by a user-defined-literal suffix identifier, to produce the correct mangled id
for such literals, and to keep the existing handling of plain and standard-suffix
literals unchanged. The analogous suffix-handling cleanup also applies to the C
domain parser in `sphinx/domains/c.py`, but the id-mangling behavior below is
specific to the C++ domain.

Throughout this document, "the id of X" means the mangled identifier that the C++
domain computes for the parsed literal X at the current (highest) id version, and
`|s|` denotes the number of characters in the string `s`.

## Requirement 1: Recognise a user-defined literal (base literal + suffix identifier)

**User story:** As a documentation author using the C++ domain, I want an
expression that contains a user-defined literal (a numeric, character or string
literal immediately followed by an identifier) to parse successfully, so that
declarations like `constexpr auto planck_constant = 6.62607015e-34q_J * 1q_s;`
build without error.

**Acceptance criteria**

1. WHEN `_parse_literal` has recognised a base literal and the immediately
   following characters form an identifier (matching the C++ identifier grammar
   `[A-Za-z_][A-Za-z0-9_]*` terminated by a word boundary) with no intervening
   whitespace, and that base literal was NOT already terminated by a standard
   numeric suffix, THEN the parser SHALL consume that identifier and SHALL treat
   the whole thing as one user-defined literal rather than stopping at the base
   literal.
2. WHEN an expression such as `6.62607015e-34q_J` or `1q_s` or `5_udl` is parsed
   as (part of) a C++ declaration, THEN the parser SHALL NOT raise an "Expected
   end of definition" (or any other parse) error caused by an unconsumed suffix
   identifier.
3. The suffix identifier SHALL be accepted even when it is spelled like a
   language keyword (no keyword rejection is applied to the suffix identifier).
4. IF the characters following a base literal do not form a valid identifier,
   THEN the parser SHALL leave the base literal unchanged (it SHALL NOT be
   wrapped as a user-defined literal).

## Requirement 2: Mangled id of a user-defined literal

**User story:** As a consumer of the C++ domain's cross-reference/id machinery, I
want a user-defined literal to be mangled as though the suffix identifier were
called on the base literal, so that its id matches the C++ (Itanium ABI) call
mangling and cross-references resolve consistently.

**Acceptance criteria**

1. WHEN the id of a user-defined literal is computed, THEN it SHALL be the
   concatenation, in order, of: the fixed prefix `clL_Zli`, then the id of the
   suffix identifier, then the character `E`, then the id of the base literal,
   then the character `E`.
2. WHEN the id of the suffix identifier is computed, THEN it SHALL be `St` if the
   identifier is exactly `std`, and otherwise SHALL be the decimal spelling of
   `|identifier|` immediately followed by the identifier text (for example, a
   suffix identifier `_udl` yields `4_udl` and a suffix identifier `q_J` yields
   `3q_J`).
3. The id of the base literal SHALL be exactly the id that literal would have on
   its own (see Requirement 4), so that, for example, the base of an integer or
   float literal contributes `L<literal-text>E`.
4. WHEN a user-defined literal built on the integer literal `<i>` with suffix
   identifier `_udl` is mangled, THEN its id SHALL be `clL_Zli4_udlEL<i>EE`; and
   for the issue's `6.62607015e-34q_J` the id SHALL be
   `clL_Zli3q_JEL6.62607015e-34EE`.

## Requirement 3: A standard numeric suffix takes precedence over a suffix identifier

**User story:** As a user writing ordinary suffixed numbers, I want `5l`, `5ul`,
`5.0f` and similar to keep being parsed as plain suffixed numeric literals, so
that adding user-defined-literal support does not change the meaning of standard
literals.

**Acceptance criteria**

1. WHEN a recognised numeric literal is immediately followed by a standard
   numeric suffix, THEN the parser SHALL consume that suffix as part of the
   numeric literal and SHALL produce a plain numeric literal (id `L<text>E`,
   where `<text>` includes the consumed suffix), NOT a user-defined literal.
2. A standard integer suffix SHALL be an unsigned marker (`u`/`U`) and/or a
   long/long-long marker (`l`, `L`, `ll`, `LL`), in either order, with at least
   one present, and SHALL be terminated by a word boundary; a standard float
   suffix SHALL be a single `f`, `F`, `l`, or `L` terminated by a word boundary.
3. WHILE deciding between a standard suffix and a suffix identifier, the parser
   SHALL prefer the standard suffix only when the suffix match ends at a word
   boundary; therefore `5l` SHALL parse as a long-suffixed number while `5lll`
   (which does not end the standard suffix at a word boundary) SHALL parse as a
   user-defined literal whose suffix identifier is `lll`.
4. WHEN an integer literal `<i>` is written with a suffix identifier that begins
   with suffix-like letters but is not a valid standard suffix, such as `<i>uludl`,
   THEN it SHALL be mangled as a user-defined literal, giving `clL_Zli5uludlEL<i>EE`.
5. The system SHALL apply this same base-then-optional-suffix-then-optional-suffix-
   identifier handling to both float and integer literals.

## Requirement 4: Preserve existing literal parsing and id mangling (regression protection)

**User story:** As a maintainer, I want all previously supported literals to keep
parsing and mangling exactly as before, so that adding UDL support is strictly
additive.

**Acceptance criteria**

1. The parser SHALL attempt to recognise a floating-point literal before the
   integer literal forms; and it SHALL attempt the integer literal forms in the
   order binary, hexadecimal, decimal, octal.
2. WHEN a plain numeric literal (integer or float, with or without a standard
   suffix, and with no suffix identifier) is parsed, THEN its id SHALL be `L`
   followed by the literal's source text followed by `E`.
3. WHEN a character literal is parsed (optionally with a `u8`/`u`/`U`/`L`
   prefix), THEN it SHALL keep its existing id (the prefix-derived type code
   followed by the decimal code-point value, for example `c97` for `'a'`, `w10`
   for `L'\n'`, `Di127820` for `U'\U0001F34C'`).
4. WHEN a string literal is parsed, THEN it SHALL keep its existing id (for
   example `"abc"` mangles to `LA3_KcE`).
5. The parser SHALL continue to recognise the keyword literals `nullptr`,
   `true`, and `false` with their existing ids, before attempting numeric,
   character or string literals.

## Requirement 5: User-defined literals on string and character literals

**User story:** As an author, I want a suffix identifier to be accepted after a
string or character literal as well, so that user-defined string/character
literals also parse and mangle correctly.

**Acceptance criteria**

1. WHEN a string literal is immediately followed by a suffix identifier (for
   example `"abc"_udl`), THEN it SHALL be parsed as a user-defined literal and
   mangled per Requirement 2, giving `clL_Zli4_udlELA3_KcEE`.
2. WHEN a character literal is immediately followed by a suffix identifier, THEN
   it SHALL be parsed as a user-defined literal and mangled per Requirement 2,
   with the base literal's contribution being the character literal's own id.
3. The system SHALL treat the suffix identifier after a string or character
   literal identically to the numeric case: it is folded in only when a valid
   identifier follows the base literal.
