# mapping.md — sympy__sympy-16886

## Symbol binding (file:line @ base_commit c50643a498)
- `sympy/crypto/crypto.py:1509` — `morse_char` dict: Morse code word → character.
  The table the gold patch edits, and the table `decode_morse` reads directly.
- `sympy/crypto/crypto.py:1536` — `char_morse = {v: k for k, v in morse_char.items()}`:
  the INVERSE table, character → Morse code word. This is the table the encoder
  consumes.
- `sympy/crypto/crypto.py:1539` — `def encode_morse(msg, sep='|', mapping=None)`:
  the modeled function. `mapping = mapping or char_morse` (1559).
- `sympy/crypto/crypto.py:1586` — `def decode_morse(msg, sep='|', mapping=None)`:
  NOT modeled as a function, but a SECOND consumer of the same patched table
  (`mapping = mapping or morse_char`, 1607) and the one PASS_TO_PASS
  `test_decode_morse` grades. See "The decode obligation" below.
- `sympy/crypto/tests/test_crypto.py:241` — `test_encode_morse` (FAIL_TO_PASS).
- `sympy/crypto/tests/test_crypto.py:252` — `test_decode_morse` (PASS_TO_PASS),
  whose third assertion is `raises(KeyError, lambda: decode_morse('.....----'))`
  at line 255.

The gold patch changes ONE entry of `morse_char` (line 1523):
`"----": "1"` → `".----": "1"`. Because `char_morse` is the inverse, this changes
the encoder's code word for the character `'1'` from `----` to the standard
`.----`.

## Modeled function
`encodeMorse : (sep : List Char) → (msg : List Char) → List Char`
↔ `encode_morse(msg, sep)` restricted to the modeled domain (see below).

The separator is a character SEQUENCE, not a single character: the real function
uses `sep` only through `sep.join(...)`, `word_sep = 2*sep` and
`assert sep not in mapping`, all of which are defined for a `str` of any length,
and `test_encode_morse` itself exercises `sep='``'` (length 2).

## Lean ↔ Python type bijection (used by G-CONF and the leakage screen)
| Lean | Python |
|---|---|
| `msg : List Char` | `msg : str` (per code point) |
| `sep : List Char` | `sep : str` of any length |
| `result : List Char` | the returned `str` (per code point) |
| `charMorse : Char → Option (List Char)` (spec, authoritative standard table) | the standard International Morse alphabet (independent reference) |
| `codeMorse : Char → Option (List Char)` (impl, the program's table) | `char_morse` (inverse of `morse_char`) |
| `morseTable : List (List Char × Char)` (impl, the program's stored table) | `morse_char` (crypto.py:1509) — the dict the patch edits and `decode_morse` reads |
| `morseOf c = (charMorse c).getD []` | standard code word of `c`, or deletion when absent |
| `codeOf c = (codeMorse c).getD []` | `mapping[c]` for a supported `c`, deletion otherwise |
| `isWordBreak c` | `c` is one of the six ASCII blanks (space, `\t`, `\n`, `\v`, `\f`, `\r`) |
| `wordRuns msg` | `msg.split()` (breaks consumed) |
| `endsInWordBreak msg` | `suffix = msg and msg[-1] in whitespace` (crypto.py:1563) |
| `supportedWords msg` | `translate(msg, None, chars - ok)` then `msg.split()` |
| `List.intercalate sep xs` | `sep.join(xs)` |
| `List.intercalate (sep ++ sep) xs` | `word_sep.join(xs)` with `word_sep = 2*sep` |
| `isUsableSep sep` | the separators for which `assert sep not in mapping` holds and the result is a function of the arguments |

## Modeled domain
The WHOLE of `encode_morse` is modeled — the word segmentation, the pass-over of
unmapped characters, the dropping of words that retain nothing, both separator
levels, and the trailing doubled separator. Two guards restrict the general
clause of the obligation:

- `∀ c ∈ msg, isModeledChar c` — printable ASCII (0x20-0x7E) plus the ASCII blanks
  (0x09-0x0D). This is the region where the function's two notions of "blank"
  agree: it normalises with the Unicode-aware `msg.split()` (crypto.py:1566, 1572)
  but tests the tail with `msg[-1] in whitespace` (1563, `from string import
  whitespace`, ASCII-only). Exactly 29 code points in all of Unicode satisfy
  `str.isspace()`; 6 of them are the ASCII blanks the model already treats as
  breaks, and the other 23 are where the two notions disagree — e.g.
  `encode_morse('A\xa0B') == '.-||-...'` while the modeled formula gives
  `'.-|-...'`. The guard declines to specify those 23 rather than specifying them
  wrongly.
- `isUsableSep sep = true` — every sequence EXCEPT a single character that already
  has a code word (which `assert sep not in mapping` at 1560 refuses) or the space
  (for which the real function is not a function of its arguments: it MUTATES the
  module-global `char_morse` with `mapping[" "] = word_sep` at 1562, so `sep=' '`
  succeeds once on a fresh interpreter and raises `AssertionError` on every later
  call).

The fixed behavior — the code word for `'1'` — lives entirely inside this domain
(the F2P inputs `'12345'`, `'67890'` are all-digit single words). G-CONF fuzzes
within it.

## The decode obligation (why the obligation has a second clause)
`test_decode_morse` (PASS_TO_PASS) asserts that `decode_morse('.....----')`
raises `KeyError`, i.e. that `morse_char` has no key `".....----"`. Since
`char_morse` is the inverse of `morse_char`, every key an implementation adds to
the encoder's table is simultaneously a code word `decode_morse` would ACCEPT.
The modeled surface is the encoder, so that preservation claim is expressed on it:

`theorem correct_encodeMorse` carries a second conjunct
`∀ sep c, isUsableSep sep = true → problem_spec_encodeMorse sep [c]
(implementation_encodeMorse sep [c])` — the postcondition on every
SINGLE-CHARACTER message, with no domain guard, hence at every character of
`Char`. At `msg = [c]` the postcondition demands the empty result for every `c`
the standard alphabet does not support, so the program's table may not give a code
word to any character `charMorse` does not. It is faithful without a guard
because a lone character cannot sit between two words: it is either a word break
(the real `split()` yields no word and the ASCII tail test supplies `word_sep`) or
a non-break character (the real code emits `mapping[c]`, or deletes it when the
table has no entry) — measured over 153,840 single-character cases plus an
all-code-point singleton sweep (557,056 cases), 0 divergences.

The encoder clauses alone do NOT close that, so the model carries the stored table
too. An entry keyed at one of the six ASCII blanks is consumed by the word split
before any lookup, on every input, so such an encoder is extensionally EQUAL to
the gold one and no predicate over `(sep, msg, result)` can separate them — the
observable had to enter the MODEL. `morseTable` is that observable: the program's
stored code-word → character data, i.e. `morse_char` itself, with the encoder's
per-character table tied to it by the third obligation below. The obligation
therefore also carries

- `∀ p ∈ morseTable, charMorse p.2 = some p.1` — every stored code word stands for
  the character the standard alphabet gives it;
- `∀ c w, charMorse c = some w → (w, c) ∈ morseTable` — every standard code word
  is stored, for its own character;
- `∀ c w, c ≠ ' ' → codeMorse c = some w → (w, c) ∈ morseTable` — the encoder's
  table is drawn from the stored data.

Faithfulness of these three, measured against the REAL patched module: `morse_char`
has 52 entries and is entry-for-entry the inverse of `charMorse` (0 key diffs, 0
value diffs, both directions), and it is NEVER mutated — byte-identical across
repeated `encode_morse`/`decode_morse` calls. The `c ≠ ' '` guard on the third is
required and is not a dodge: `encode_morse` writes `mapping[" "] = 2*sep`
(crypto.py:1562) into the encoder's table on every call, so `char_morse` really
does gain a `' '` entry (measured: `'||'`, then `'``'`) that the stored alphabet
does not have. Pinning the claims on the pre-image is what makes them true at
every point in the module's life.

## Callee provenance / flag deps
- `char_morse` (the impl table `codeMorse`) is an UNCHANGED-shape derived dict;
  it is modeled DEEPLY (spelled out entry by entry), not axiomatized — it is the
  very data the patch edits. Tagged A-reference (validated == real `char_morse`
  by G-CONF), not a consumed axiom.
- `translate` (sympy/utilities/misc.py) enters only through op 2 of
  refinement.md, as the deletion of characters absent from the table; it is
  modeled concretely as `List.filter`, not axiomatized.
- No flag dependency: `encode_morse`'s `mapping` defaults to `char_morse`; the
  modeled domain uses that default.

## G-CONF fuzz seed
Pinned seed: `16886`. Fuzzer draws ≥10^5 messages over the modeled character set
(printable ASCII plus the ASCII blanks) crossed with separators of length 0, 1 and
more, plus boundary cases (the empty message, a lone blank, a message ending in a
blank, words written entirely in unsupported characters, the digits `0`-`9`).
