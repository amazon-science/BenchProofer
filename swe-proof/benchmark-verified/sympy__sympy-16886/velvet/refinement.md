# refinement.md — sympy__sympy-16886

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`encodeWord` `do` block, plus the deep `codeOf`/`codesOf` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-reference** (deep model validated == the real callee/table by G-AX),
**A-consumed** (proof uses an axiom's `ensures` — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg + this narrative are audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The encoding site — `encode_morse()` per-symbol loop (`crypto.py:1578-1583`)

Gold hunk (the changed datum, one entry of the source table `morse_char`,
inverted into the lookup table `char_morse` the loop reads):
```
-    "-----": "0", "----": "1",
+    "-----": "0", ".----": "1",
```

| # | Solution.lean impl op (`encodeWord`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `word : List Char` | `word: str` (one element of `msg.split()`) | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | result is `codesOf word`: the per-symbol code sequences in source order, computed by the backward `while` fold prepending `codeOf c` | the loop `for letter in word: morseword.append(mapping[letter])`, where `mapping = char_morse` | A-reference + I | the table is modeled **deeply**: `codeOf`/`codesOf` (pure region) and the verified loop ARE the per-symbol lookup-and-append. No consumed axiom about the table. The fold ops (`codeOf c`, `::`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of `codeOf` to the real `char_morse` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A3 | each element `codeOf c : List Char` | one `mapping[letter]` code string appended to `morseword` | A-reference | all UNCHANGED entries: `codeOf c` ⇔ base `char_morse[c]`, G-AX-validated entry-for-entry. The one corrected entry `codeOf '1' = ".----".toList` ⇔ the gold line `".----": "1"`; the base table still holds the bug `char_morse['1'] = "----"`, so this single entry is validated by G-CONF (gold applied) / G-RESOLVE / G-DIFF, NOT by base-table G-AX equality (G-AX asserts base holds `"----"` and the model holds `".----"`). |

The downstream UNCHANGED ops of `encode_morse` — whitespace normalization
(`msg.split()`/join), unmapped-symbol filtering (`translate(msg, None, ...)`),
the per-word `sep.join(morseword)`, the `word_sep.join(...)` of words, and the
trailing-`word_sep` suffix — are concrete **I**-ops, untouched by the patch.
They are not modeled in Velvet (the modeled change is the table assembly) and
are transliterated faithfully by the G-CONF shadow, which reconstructs the full
`encode_morse` from the R/I shadow of `codesOf` plus these I-ops and diffs it
against the real patched `encode_morse`.

Discriminating content of the change — `'1'` (U+0031) → `".----"` not `"----"` —
lives in `codeOf '1' = ".----".toList` (model) ⇔ the `".----": "1"` entry of
`morse_char`/`char_morse` (real). The pre-patch table mapped `'1'` → `"----"`;
`Solution_prepatch.lean` reproduces that and **fails** `out = codesOf word` on
exactly the clause `['-','-','-','-'] = codeOf '1'` (G-DIFF).

## B. No consumed axioms

There is no `axiom` the proof consumes. The one operation that the patch changes
— the source-table entry for `'1'` — is modeled **deeply** (the spelled-out
`codeOf`/`codesOf`, step A2/A3, an A-reference + I), not hidden behind an axiom
about the table under change. G-AX validates the deep model against the real
**base** `char_morse` on every UNCHANGED entry (51 of 52), confirms the key
sets coincide, and confirms the single corrected entry genuinely differs (base
holds the documented bug `'----'`, model holds the gold `'.----'`); that one
correction is validated by G-CONF/G-RESOLVE/G-DIFF, not by base-table equality.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The changed datum is a finite table entry,
fully expressible as a `match` in `codeOf`.

## D. verify(Solution) ⇒ resolved

`encodeWord` verifies only if its output equals the exact per-symbol code
sequence with `'1' → ".----"` (A2/A3). By R (`str ↔ List Char`) the verified
per-word encoding equals the real loop's `morseword` on the tested `str` inputs;
by G-AX the deep model `codeOf` equals the real `char_morse` (A-reference);
by G-CONF the R/I transliteration of `codesOf`, wrapped in the unchanged I-ops
of `encode_morse`, agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited table — and the gold patch resolves
(G-RESOLVE). The single trust point is the A-reference table fidelity (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
