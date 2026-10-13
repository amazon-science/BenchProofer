# Requirements: correct Morse Code representation of the digit "1"

## Introduction

The module `sympy.crypto.crypto` provides a Morse Code facility built on an
internal table that associates each Morse symbol (a string of dots `.` and
dashes `-`) with the plaintext character it represents. From this table a
reverse table is derived that maps each plaintext character to its Morse
symbol. The public function `encode_morse` uses the reverse (character → Morse)
table to turn plaintext into Morse, joining letters with a separator (default
`|`) and words with a doubled separator; the public function `decode_morse`
uses the forward (Morse → character) table to turn Morse back into plaintext.

A defect exists in the table: the digit `"1"` is associated with a Morse symbol
consisting of four dashes, which is not the digit's correct International Morse
Code representation. In standard Morse Code the digit `"1"` is a single dot
followed by four dashes. Because the character → Morse table is derived from
the same table, encoding the digit `"1"` produces the wrong symbol, and the
symbol reserved for `"1"` collides with a neighbouring value. Additionally,
four dashes is not a valid standalone Morse symbol for any digit, so it should
not appear as the encoding of any character.

The goal is to correct the Morse representation of the digit `"1"` to its
standard International Morse Code value so that all ten decimal digits encode
(and decode) to their correct symbols, while leaving every other character's
Morse mapping and every other behavior of `encode_morse` / `decode_morse`
unchanged.

## Requirement 1: The digit "1" encodes to its correct Morse symbol

**User story:** As a user encoding text that contains digits with
`encode_morse`, I want the digit `"1"` to produce its standard International
Morse Code symbol, so that the encoded output is correct and unambiguous.

**Acceptance criteria**

1. WHEN `encode_morse` is called on the single-character string `"1"`, THEN the
   function SHALL return the Morse symbol consisting of one dot immediately
   followed by four dashes (`.----`).
2. The system SHALL NOT map the digit `"1"` to a symbol consisting of four
   dashes with no leading dot.
3. WHEN `encode_morse` encodes any string containing the digit `"1"`, THEN each
   occurrence of `"1"` SHALL be represented by the one-dot-then-four-dashes
   symbol in the output.

## Requirement 2: All decimal digits encode to their correct Morse symbols

**User story:** As a user encoding numeric text, I want every decimal digit
`0`–`9` to produce its standard International Morse Code symbol, so that numeric
strings are encoded correctly.

**Acceptance criteria**

1. WHEN `encode_morse` encodes a string of consecutive decimal digits, THEN it
   SHALL join the per-digit symbols with the letter separator (default `|`) and
   map each digit to the following symbols: `0`→`-----`, `1`→`.----`,
   `2`→`..---`, `3`→`...--`, `4`→`....-`, `5`→`.....`, `6`→`-....`,
   `7`→`--...`, `8`→`---..`, `9`→`----.`.
2. The system SHALL keep the Morse symbols for the digits `0` and `2` through
   `9` at their existing standard values, changing only the symbol for the
   digit `"1"`.
3. WHEN `encode_morse` encodes any string composed solely of decimal digits,
   THEN the result SHALL be each digit's symbol from Requirement 2.1, taken in
   input order and joined by the default letter separator, with no other
   characters inserted or omitted.

## Requirement 3: Round-trip and existing behavior are preserved

**User story:** As a user relying on Morse encoding and decoding, I want the
correction to leave all previously-correct behavior intact, so that existing
uses continue to work.

**Acceptance criteria**

1. WHEN `decode_morse` is given the correct Morse symbol for the digit `"1"`
   (one dot followed by four dashes), THEN it SHALL return `"1"`.
2. WHEN `encode_morse` is applied to a plaintext string and the result is then
   passed to `decode_morse`, THEN for text drawn from the supported characters
   the decoded output SHALL equal the encoded input's normalized plaintext
   (letters recovered in upper case, words separated by single spaces).
3. The system SHALL keep the Morse symbols for every letter `A`–`Z` unchanged.
4. The system SHALL keep the Morse symbols for the supported punctuation and
   symbol characters (including `.`, `,`, `:`, `;`, `?`, `-`, `_`, `(`, `)`,
   `'`, `=`, `+`, `/`, `@`, `$`, `!`) unchanged.
5. WHEN `encode_morse` is called with a custom letter separator via the `sep`
   argument, THEN it SHALL join letters within a word using that separator and
   words using that separator doubled, exactly as before this correction.
6. WHEN `encode_morse` encounters characters that have no Morse mapping, THEN it
   SHALL omit those characters from the output, exactly as before this
   correction.
