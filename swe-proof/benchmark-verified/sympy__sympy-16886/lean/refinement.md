# refinement.md — sympy__sympy-16886

Maps every operation in `implementation_encodeMorse` to its `patch.diff` /
real-code counterpart in `encode_morse` (sympy/crypto/crypto.py:1539). Tags:
**R** type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
op left as the real repo callee/data in G-CONF (not axiomatized), **I** identical
concrete op.

## Patch
```python
# sympy/crypto/crypto.py, morse_char dict (line 1523)
-    "-----": "0", "----": "1",
+    "-----": "0", ".----": "1",
```
`char_morse = {v: k for k, v in morse_char.items()}` (crypto.py:1536) is the
inverse table the encoder consumes. The edit changes the code word the encoder
emits for `'1'` from `----` to the standard `.----`. No control flow changes; the
fix is one data entry.

## Modeling decision
The whole of `encode_morse` is modeled, not a single-word core. The modeled
carrier is

  `implementation_encodeMorse : (sep : List Char) → (msg : List Char) → List Char`

so the separator is a character SEQUENCE of any length (matching `sep : str`,
which the real function only ever uses through `sep.join`, `2*sep` and
`sep not in mapping`), and both separator LEVELS are in the model. The impl is
written imperatively — two accumulator `forIn` loops, one keeping the supported
characters of each word and dropping the words that retain nothing, one rendering
each surviving word — and the postcondition
`problem_spec_encodeMorse sep msg result` pins the WHOLE result to `(sep, msg)`
with no free component.

The program's table `char_morse` is modeled DEEPLY as `codeMorse` (spelled out
entry by entry) — it is the data the patch edits, so it must NOT be axiomatized
(SPEC_GUIDE §3). The SPECIFICATION's table `charMorse` is the authoritative
standard International Morse alphabet, written independently in the `pure`
region; the postcondition pins the result to the standard code words `morseOf`.
Verification therefore demands the program's table agree with the standard one —
exactly the discriminating clause for `'1'` (`.----` standard vs `----`
pre-patch).

### The discriminating machinery in the `pure` region
These are not local helpers; each is a clause of the refinement and each is what
makes a wrong implementation fail.

| symbol | what it pins | real-code counterpart |
|---|---|---|
| `charMorse` | the AUTHORITATIVE standard code-word table (the spec side of the discriminator) | the standard International Morse alphabet; entry-for-entry equal to the patched `char_morse` (checked by G-CONF/G-AX) |
| `morseOf c` | total standard lookup: the code word, or `[]` for an unsupported character | `mapping[c]`, with the character deleted when absent |
| `isWordBreak c` | which characters segment the message: the space and the other ASCII blanks | `msg.split()` on the modeled domain, and `msg[-1] in whitespace` (crypto.py:1563, `from string import whitespace`, ASCII-only) |
| `wordRuns msg` | the segmentation itself, breaks consumed | `msg.split()` (crypto.py:1565, 1572) |
| `endsInWordBreak msg` | whether the trailing doubled separator is emitted | `suffix = msg and msg[-1] in whitespace` (crypto.py:1563) |
| `supportedWords msg` | the pass-over of unsupported characters AND the dropping of a word that retains none | `translate(msg, None, chars - ok)` (crypto.py:1570) followed by `msg.split()` |
| `isModeledChar c` | the DOMAIN of the general clause: printable ASCII plus the ASCII blanks, where the modeled segmentation and the real `str.split()` provably agree | the disagreement between the Unicode-aware `str.split()` and the ASCII-only `whitespace` tail test; see "Modeled domain" in mapping.md |
| `isUsableSep sep` | which separators the encoding is defined for: everything except a single character that already has a code word or is the space | `assert sep not in mapping` (crypto.py:1560) together with the `mapping[" "] = word_sep` mutation at 1562 |

## Operation correspondence
| # | Lean op (`implementation_encodeMorse`) | real-code op | tag | note |
|---|---|---|---|---|
| 1 | `for w in wordRuns msg do` | `words = msg.split()` (crypto.py:1572), after the whitespace normalisation at 1566 | R | segmentation at the word breaks. `str` ↔ `List Char` per code point; on the modeled domain (`isModeledChar`) the two notions of "blank" coincide, which is what makes this an R row and not an approximation. |
| 2 | `let supported := w.filter (fun c => (codeMorse c).isSome)` | `translate(msg, None, ''.join(chars - ok))` (crypto.py:1568-1570) — the characters absent from the table are deleted before the per-letter loop | R + A-reference | the pass-over of unsupported characters. `codeMorse` is the deep model of `char_morse`, bound to the REAL `char_morse` in G-CONF. |
| 3 | `kept := kept ++ (if supported ≠ [] then [supported] else [])` | a word that loses every character becomes empty and is dropped by the second `msg.split()` at 1572 | I | drop the words that retain nothing (and with them their word break). |
| 4 | `encoded := encoded ++ [List.intercalate sep (w.map codeOf)]` | `morseword.append(mapping[letter])` over the word's letters, then `sep.join(morseword)` (crypto.py:1575-1580) | R + A-reference | within-word render: per-character lookup in the program's table, joined by ONE copy of the separator. |
| 5 | `return List.intercalate (sep ++ sep) encoded` | `word_sep.join(morsestring)` with `word_sep = 2*sep` (crypto.py:1561, 1583) | R | between-word join: TWO copies of the separator. |
| 6 | `++ (if endsInWordBreak msg then sep ++ sep else [])` | `+ (word_sep if suffix else '')` (crypto.py:1583) with `suffix` from 1563 | I | the trailing doubled separator when the message ends in a word break. |

The behavior-changing element is the table entry consumed in ops 2 and 4:
pre-patch `codeOf '1' = ----`, post-patch `codeOf '1' = .----`. The spec's
`morseOf '1' = .----` (standard) forces the post-patch value, so the prepatch
impl cannot satisfy the postcondition on any message containing `'1'` (G-DIFF).

## The obligation has FIVE clauses, and why
`theorem correct_encodeMorse` is a conjunction:

1. **general clause** — `∀ sep msg, (∀ c ∈ msg, isModeledChar c) →
   isUsableSep sep = true → problem_spec_encodeMorse sep msg (implementation… )`.
   The domain guard is load-bearing for FAITHFULNESS and must stay: outside it
   the real `str.split()` (Unicode-aware) and `isWordBreak` (ASCII blanks)
   disagree, e.g. `encode_morse('A\xa0B') == '.-||-...'` where the modeled
   formula gives `'.-|-...'` (same for `\x1c`, `\x85`, ` `, `　`).
2. **singleton clause** — `∀ sep c, isUsableSep sep = true →
   problem_spec_encodeMorse sep [c] (implementation… )`, with NO domain guard, so
   it observes the program's table at EVERY character of `Char`.
3. **stored-table soundness** — `∀ p ∈ morseTable, charMorse p.2 = some p.1`:
   every code word the program STORES stands for the character the standard
   alphabet gives that code word.
4. **stored-table completeness** — `∀ c w, charMorse c = some w → (w, c) ∈
   morseTable`: every standard code word is stored, for its own character.
5. **the encoder reads that same data** — `∀ c w, c ≠ ' ' → codeMorse c = some w →
   (w, c) ∈ morseTable`: the per-character table the encoder consults is drawn
   from the stored table, off the space.

Clauses 3-5 are the MODEL change this instance needs, and they are why
`morseTable` is in the impl region at all. See "`morse_char` has a SECOND
consumer" below: the deep-modeled datum is now the table the patch actually
edits (code word → character), with the encoder's per-character table tied to it
by clause 5, rather than only the derived inverse. Clauses 1 and 2 constrain the
ENCODER, and an encoding cannot observe a stored code word that no message ever
emits; clauses 3 and 4 constrain the stored DATA, so they can.

Clause 5's `c ≠ ' '` guard is load-bearing for FAITHFULNESS and must stay: the
real `encode_morse` writes `mapping[" "] = word_sep` (crypto.py:1562) into the
encoder's table on every call, so the encoder's table DOES carry a `' '` entry
that is not in the stored alphabet — it comes from the separator. Verified: after
a call, `char_morse[' ']` is `'||'` (then `'``'`), while `morse_char` is
byte-for-byte unchanged across calls. Stating clauses 3-5 on the PRE-IMAGE
(`morse_char`) rather than on `char_morse` is what makes them true at every point
in the module's life. A total claim `∀ c, codeMorse c = charMorse c` would be
FALSE at `' '` for the mapping the encoder actually reads.

Clause 2 is a REFINEMENT row in its own right, not a convenience: it is the
`decode_morse` preservation obligation, expressed on the surface this spec
models. See the next section. It is faithful without a domain guard because a
LONE character cannot sit between two words: it is either a word break (the real
`split()` yields no word and the ASCII-`whitespace` tail test supplies
`word_sep`, which is what the modeled formula also gives) or a non-break
character (the real code emits `mapping[c]`, or deletes the character when the
table has no entry — again what the modeled formula gives). Measured: 153,840
single-character cases over 0..0x30FF plus 0xFE00..0xFF0F and targeted extras ×
11 usable separators, 0 divergences against the real patched callee; corroborated
by an all-code-point singleton run (557,056 cases, 0 divergences).

## `morse_char` has a SECOND consumer, and it is graded
| consumer | site | how it is graded | how the spec pins it |
|---|---|---|---|
| `encode_morse` | crypto.py:1539, via `char_morse` (`mapping = mapping or char_morse`, 1559) | FAIL_TO_PASS `test_encode_morse` | the postcondition, on the general clause |
| `decode_morse` | crypto.py:1586, `mapping = mapping or morse_char` (1607) | PASS_TO_PASS `test_decode_morse`, specifically `raises(KeyError, lambda: decode_morse('.....----'))` (test_crypto.py:255) | the SINGLETON clause, and decisively clauses 3-5 |

This row is the whole reason clause 2 exists. Every new key added to `morse_char`
is simultaneously a new key for `decode_morse`, so a patch that adds a table
entry to make the encoder emit an extra code word also makes the decoder ACCEPT
that code word, and `test_decode_morse` demands it be rejected. A spec that
observed the encoder only on the modeled window would leave 1,111,964 arms of
`codeMorse` free, and a rival could spend one of them on `".....----"` — passing
F2P, failing P2P. Clause 2 closes that: at `msg = [c]` the postcondition demands
the empty output for every `c` the standard alphabet does not support, so no
character may acquire a code word the standard table does not give it.

Clause 2 alone does NOT close that, and clauses 3-5 are why the model carries the
stored table. An entry keyed at one of the six ASCII blanks (`isWordBreak c`) is
consumed by the word split before any table lookup happens, on EVERY input, so an
encoder carrying it is extensionally EQUAL to the gold encoder: `encode_morse` is
the same function on every argument. No predicate over `(sep, msg, result)` can
separate the two, so no further OUTPUT clause could ever have closed it — the
observable had to be added to the model, not constrained harder.

That is what clauses 3-5 do. `morseTable` is the program's stored data (code word
→ character), which is the object the gold patch edits and the object
`decode_morse` reads; the encoder's per-character table is tied to it by clause 5.
Clauses 3 and 4 then say that data holds EXACTLY the standard code words: an entry
for `".....----"` violates clause 3 no matter which character it is keyed at,
including a word break, because the claim is about the stored table and not about
any encoding of it. This is the sense in which the stored table settles which code
words have a meaning at all, which is the property `test_decode_morse` asserts and
the encoder cannot express.

## R/I legs ⇒ G-CONF
Ops 1-6 are R/I content; `codeMorse` (the program's table) is the A-reference.
G-CONF leaves the table as the REAL `char_morse` (it does NOT substitute the
standard `charMorse`) and differential-tests a shadow of the whole modeled
formula — segmentation, pass-over, dropped words, both separator levels, the
trailing break — against the REAL patched `encode_morse(msg, sep)` over ≥10^5
fuzzed messages inside the modeled domain. `conf_skip = false`: the impl region
has genuine R/I content.

## No A-consumed row
The proof consumes no abstract callee property: both `morseOf` (spec) and `codeOf`
(impl) are concrete total functions. There is no `opaque`/`axiom` declaration in
`Solution.lean`, so `meta.json axioms = []`. `char_morse` is recorded as an
A-reference solely to document the G-CONF binding to the real table.
`axiom_check.py` is a skip stub.

## F2P alignment
- `test_encode_morse` adds `encode_morse('12345') == '.----|..---|...--|....-|.....'`
  and `encode_morse('67890') == '-....|--...|---..|----.|-----'`. The discriminator
  is the code word for `'1'`: the spec forces `.----`; the prepatch impl emits
  `----`, so `implementation_encodeMorse "|".toList "12345".toList` would be
  `----|..---|...--|....-|.....` ≠ spec, making `correct_encodeMorse` unclosable
  for the prepatch (G-DIFF).
- The other `test_encode_morse` assertions exercise the structural clauses the
  model carries: `encode_morse(' ') == '||'` and `encode_morse('SMS\n') ==
  '...|--|...||'` are the trailing-break clause (op 6), `encode_morse('') == ''`
  the empty message, `encode_morse(' ', sep='``') == '````'` the multi-character
  separator, and `encode_morse('!@#$%^&*()_+')` the pass-over of unsupported
  characters (op 2) with `^`, `&`, `*` absent from the table.
- PASS_TO_PASS `test_decode_morse` is aligned by the singleton clause, per the
  second-consumer table above.
`patch.diff` (gold verbatim) makes the harness resolve.
