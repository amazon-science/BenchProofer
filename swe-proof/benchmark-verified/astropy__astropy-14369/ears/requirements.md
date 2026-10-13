# Requirements: Correct division-chain parsing in the CDS unit format

## Introduction

Astropy reads units written in the CDS/MRT convention (the format recommended
by AAS/ApJ and defined by the "Standards for Astronomical Catalogues 2.0",
http://vizier.u-strasbg.fr/doc/catstd-3.2.htx). In this convention composite
units are written compactly, with the quotient operator `/` used repeatedly and
no spaces, e.g. a surface-brightness unit `10+3J/m/s/kpc2`.

The affected component is the CDS unit-format parser in
`astropy/units/format/cds.py` — the grammar it defines (in particular the
`division_of_units` production and its associated reduction action) and the
generated LALR parse table that drives it. This grammar is what backs
`astropy.units.format.CDS.parse(...)`, `astropy.units.Unit(..., format="cds")`,
and, transitively, `astropy.table.Table.read(..., format="ascii.cds")`.

The parser currently mis-associates a chain of several `/` operators: a string
such as `10+3J/m/s/kpc2` comes back with its trailing units in the wrong place
in the quotient (units that should be in the denominator end up in the
numerator, and vice versa). The goal is that a CDS unit string be parsed so that
the resulting unit equals the mathematical value the CDS convention assigns to
it, with repeated division read strictly left to right, while every unit string
the parser accepted (or rejected) before and that is unaffected by this reading
continues to behave identically.

Throughout this document, "the CDS parser" means the behavior of
`astropy.units.format.CDS.parse(s)` (equivalently `Unit(s, format="cds")`), and
"reject" means it raises `ValueError` rather than returning a unit.

## Requirement 1: Repeated division is read left to right

**User story:** As an astronomer reading an MRT/CDS table, I want a unit written
with several `/` operators to be interpreted exactly as the CDS standard
prescribes, so that the units in my table match the units in the source file.

**Acceptance criteria**

1. WHEN the CDS parser is given a unit string consisting of a leading unit term
   followed by two or more further unit terms each separated by the `/`
   operator (a "division chain"), THEN the parser SHALL interpret the chain as
   grouped left-to-right, so that only the leading term is in the numerator and
   every subsequent term is in the denominator.
2. WHEN the CDS parser parses a division chain whose terms are distinct base
   units, THEN each term after the leading one SHALL contribute an exponent of
   −1 (appear once in the denominator), independent of its position in the
   chain.
3. WHEN the CDS parser is given the string `km/s/Mpc`, THEN it SHALL return a
   unit equal to kilometres divided by (seconds multiplied by megaparsecs) —
   i.e. km · s⁻¹ · Mpc⁻¹.
4. WHEN the CDS parser is given the string `10+3J/m/s/kpc2`, THEN it SHALL
   return a unit equal to 1000 multiplied by joules, divided by (metres
   multiplied by seconds multiplied by kiloparsecs squared) — i.e. the numeric
   factor 10³ times J · m⁻¹ · s⁻¹ · kpc⁻².
5. The CDS parser SHALL apply a leading numeric scale factor (such as `10+3`)
   to the whole left-to-right-reduced division chain that follows it, leaving
   the chain's unit exponents unchanged and only multiplying in the scale.

## Requirement 2: Parenthesised and leading-division forms remain correct

**User story:** As a user relying on the CDS convention's grouping rules, I want
parentheses and a leading `/` to keep giving the mathematically expected unit,
so that equivalent ways of writing a unit agree.

**Acceptance criteria**

1. WHEN the CDS parser is given a unit divided by a parenthesised product of
   units, THEN every unit inside the parentheses SHALL appear in the
   denominator; specifically `km/(s.Mpc)` SHALL return a unit equal to
   km · s⁻¹ · Mpc⁻¹.
2. The CDS parser SHALL return, for `km/(s.Mpc)`, the same unit it returns for
   `km/s/Mpc`.
3. WHEN the CDS parser is given a unit string that begins with the `/` operator
   applied to a single unit term (a leading division with no numerator), THEN it
   SHALL return the reciprocal of that unit; specifically `/s` SHALL return
   s⁻¹.

## Requirement 3: A division may not be followed by an un-parenthesised product

**User story:** As a maintainer of the CDS grammar, I want strings that mix a
division with a trailing un-parenthesised product to be treated as malformed, so
that the accepted grammar is unambiguous and matches the left-to-right reading.

**Acceptance criteria**

1. IF a CDS unit string places an un-parenthesised product term (a term joined
   by the `.` product operator) immediately after a division has already been
   taken, THEN the CDS parser SHALL reject the string by raising `ValueError`.
2. WHEN the CDS parser is given the string `km/s.Mpc-1`, THEN it SHALL reject it
   (raise `ValueError`) rather than returning a unit.
3. WHEN the CDS parser is given the string `/s.Mpc`, THEN it SHALL reject it
   (raise `ValueError`) rather than returning a unit.

## Requirement 4: Previously correct CDS unit strings are unaffected

**User story:** As an existing user of the CDS reader, I want all the unit
strings that already parsed (or were already rejected) correctly to keep
behaving exactly as before, so that this correction introduces no regression.

**Acceptance criteria**

1. WHEN the CDS parser is given a single division such as `km/s`, THEN it SHALL
   return kilometres divided by seconds (km · s⁻¹), unchanged from before.
2. WHEN the CDS parser is given the product-with-negative-power form `km.s-1`,
   THEN it SHALL return the same unit as `km/s` (km · s⁻¹).
3. The CDS parser SHALL continue to accept and correctly parse product forms
   (terms joined by `.`), per-unit integer powers (e.g. `m2`, `s-1`), numeric
   factors and scale prefixes (e.g. `2.54cm`, `10+21m`, `1.5x10+11m`), the
   dimensionless unit (`---`), and bracketed logarithmic units (e.g. `[cm/s2]`,
   `[K]`, `[-]`), producing the same units as before this change.
4. The CDS parser SHALL continue to reject every unit string that it rejected
   before and that is unrelated to division-chain association — including
   strings containing spaces (e.g. `km / s`, `km s-1`), the `*` product
   operator (`km*s`), the `**` power spelling (`km**2`), function-call syntax
   (e.g. `dB(mW)`, `dex(cm s-2)`), and malformed sign/dimensionless tokens
   (e.g. `-m`, `m-`, `--`, `[--]`) — by raising `ValueError`.
5. The change SHALL be confined to how the CDS division chain associates; the
   generic (non-CDS) unit parser's behavior SHALL remain unchanged.
