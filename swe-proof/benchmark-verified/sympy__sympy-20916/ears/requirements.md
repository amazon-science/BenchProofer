# Requirements: Unicode-aware trailing-subscript detection in symbol-name splitting

## Introduction

When SymPy pretty-prints a symbol, it first decomposes the symbol's textual
name into a base name plus lists of superscripts and subscripts. This
decomposition is performed by `split_super_sub` in
`sympy/printing/conventions.py`, which returns a triple
`(name, superscripts, subscripts)`.

Besides the explicit markers (`^` / `__` for superscripts, `_` for
subscripts), the routine applies a convenience rule: if the resulting base
name is a run of letters immediately followed by a run of digits (and nothing
else), those trailing digits are peeled off and treated as a leading
subscript. This is what lets a symbol written as `w0` render with a subscript
zero.

The defect: this trailing-digit rule only recognised **ASCII** letters
(`a`–`z`, `A`–`Z`) as the leading part and only **ASCII** digits (`0`–`9`) as
the trailing part. As a result, a symbol whose base is a non-Latin letter —
for example a Greek letter such as `ω` — followed by digits was **not** split,
so its digits were printed inline instead of as a subscript, while the Latin
equivalent printed correctly. The goal is to make the trailing-digit rule
recognise any Unicode letter as the base and any Unicode decimal digit as the
trailing subscript, so Greek (and other non-Latin) symbol names behave exactly
like Latin ones, without regressing any existing splitting behavior.

The affected module/function is `sympy/printing/conventions.py :
split_super_sub` (and the module-level pattern it uses to detect a
name-ending-in-digits).

## Requirement 1: Peel a trailing digit run off a Unicode-letter base name

**User story:** As a user pretty-printing symbols whose names are a non-Latin
letter followed by digits (e.g. a Greek letter with an index), I want the
trailing digits recognised as a subscript, so that such symbols render with a
proper subscript just like their Latin-letter counterparts.

**Acceptance criteria**

1. WHEN `split_super_sub` is called with a name that, after any explicit
   `^`/`_`/`__` marker processing, consists of a non-empty run of alphabetic
   characters immediately followed by a non-empty run of decimal-digit
   characters and nothing else, THEN `split_super_sub` SHALL return the base
   name equal to the leading letter run and SHALL add the trailing digit run as
   a subscript.
2. WHEN such a trailing digit run is peeled off, THEN `split_super_sub` SHALL
   insert that digit run at the **front** of the returned subscript list (so it
   precedes any subscripts produced by explicit `_` markers) and SHALL leave
   the superscript list unaffected.
3. The system SHALL treat as an eligible base-name letter **any** alphabetic
   character in the full Unicode repertoire, including non-Latin scripts such
   as Greek, not merely the ASCII letters `a`–`z` / `A`–`Z`.
4. The system SHALL treat as an eligible trailing digit **any** Unicode
   decimal-digit character, not merely the ASCII digits `0`–`9`; a trailing run
   that mixes ASCII and non-ASCII decimal digits SHALL be recognised in full
   and returned as a single subscript string preserving the original
   characters and their order.
5. WHEN a Greek-letter base name is directly followed by one or more digits,
   THEN `split_super_sub` SHALL return the Greek letter(s) as the base name and
   the digit run as a subscript, producing the same structural result it would
   for the equivalent Latin-letter name.

## Requirement 2: Only peel when the whole base is letters-then-digits

**User story:** As a maintainer, I want the trailing-digit exception to fire
only for names that are exactly letters-followed-by-digits, so that other names
are left untouched and no spurious subscripts are introduced.

**Acceptance criteria**

1. IF, after marker processing, the base name is empty, or does not begin with
   at least one letter, or does not end with at least one digit, or contains
   any additional characters after the trailing digit run, THEN
   `split_super_sub` SHALL leave the base name unchanged and SHALL NOT peel off
   any trailing-digit subscript.
2. IF the base name contains no digits at all, THEN `split_super_sub` SHALL
   return that name unchanged with no digit-derived subscript.
3. WHEN the input text is empty, THEN `split_super_sub` SHALL return an empty
   name with empty superscript and subscript lists.

## Requirement 3: Preserve explicit superscript/subscript marker handling

**User story:** As a user, I want the existing `^` / `_` / `__` marker parsing
to keep working exactly as before while trailing digits are now Unicode-aware,
so that combining explicit markers with a digit-suffixed base still yields the
correct decomposition.

**Acceptance criteria**

1. The system SHALL continue to interpret `^` and a leading `__` as
   introducing superscripts and a single `_` as introducing a subscript, in the
   order they appear in the name.
2. WHEN a name has an explicit superscript marker after a letters-then-digits
   base (for example a base name followed by `^` and a superscript), THEN
   `split_super_sub` SHALL peel the base's trailing digits into a subscript AND
   record the marker-introduced part as a superscript, independently of one
   another.
3. WHEN the marker-introduced superscript or subscript content is itself
   non-ASCII (for example a Greek letter or a Unicode digit), THEN
   `split_super_sub` SHALL preserve that content verbatim in the corresponding
   returned list.
4. The system SHALL keep producing the previously-correct results for
   ASCII-only names, including: a single letter followed by one or more ASCII
   digits yields that letter as the base with the digit run as a subscript;
   multi-letter names ending in digits behave the same way; names with only
   explicit `_`/`^`/`__` markers and no letters-then-digits base are decomposed
   solely by those markers with no extra digit subscript.
