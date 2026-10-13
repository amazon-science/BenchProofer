# mapping.md — sympy__sympy-16886

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c50643a49811e9fe2f4851adff4313ad46f7325e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep model.

Repo file under change: `sympy/crypto/crypto.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `encodeWord (word : List Char)` | the inner per-symbol loop of `encode_morse(msg, sep, mapping)` — `sympy/crypto/crypto.py:1578-1583` (`morseword.append(mapping[letter])` for `letter in word`) | the modeled changed behavior: the per-symbol code sequence of one word |
| `codeOf (c : Char)` *(deep model — A-reference)* | the per-symbol code table `char_morse` — `sympy/crypto/crypto.py:1538` (`char_morse = {v: k for k, v in morse_char.items()}`), inverse of `morse_char` (`crypto.py:1510-1536`) | pure spec: the telegraphic code for one source symbol; deep model of the unchanged-shape table whose `'1'` entry the patch corrects, validated `codeOf == char_morse` by axiom_check.py (G-AX), NOT a consumed axiom |
| `codesOf (s : List Char)` *(deep model — A-reference)* | the assembled `morseword` list for one word (`crypto.py:1579-1583`) | pure spec: the per-symbol code sequences for a whole symbol sequence, front-recursive |

The datum the patch changes is one entry of the source table `morse_char`
(`crypto.py:1523`): the code-string for the symbol `'1'`. Because
`char_morse = {v: k for k, v in morse_char.items()}` inverts `morse_char`, the
corrected entry is `char_morse['1']`, which `encode_morse` reads via
`mapping[letter]`. Pre-patch that code is `'----'` (four dashes — the code the
*decoding* table also assigns to a four-dash run); post-patch it is the
canonical code. (Refinement audit only; not localized in the consumer spec.)

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (one word of `msg`, after whitespace-split + unmapped-filter) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| one code string `mapping[letter]` (a `str` of `'.'`/`'-'`) | `List Char` | the dot/dash code-string ↔ `List Char` of `'.'`/`'-'`; `char_morse['1']` ↔ `codeOf '1'` |
| `morseword` (Python `list[str]`) | `List (List Char)` | element-wise the code-string bijection above |
| `sep.join(morseword)` (one word's joined codes) | the I-op handled in G-CONF's shadow | `sep`-joining is an UNCHANGED concrete op; the modeled change is purely the table entries assembled into `morseword`. G-CONF transliterates the join. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-symbol.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `codeOf` / `codesOf` deep model ↔ `char_morse` (A-reference)
**Callee (table lookup):** `mapping[letter]` with `mapping = char_morse`, the
inverse of the module-level `morse_char` dict. The changed table is modeled
**deeply** by `codeOf` (and `codesOf`) in the `pure` region; there is **no
consumed axiom** about the table. `codeOf` enumerates the post-patch table
entry-for-entry: every uppercase letter `A..Z`, digit `0..9`, and supported
punctuation maps to its canonical dot/dash code; the corrected entry is
`codeOf '1' = ".----".toList` (the patch's `"-----": "0", ".----": "1"` line),
not the pre-patch `"----"`. Every code point with no telegraphic representation
maps to `[]` — such symbols are removed by `encode_morse`'s
`translate(msg, None, ...)` filter (`crypto.py:1570`) before the table is read,
so the empty image is never observed for a represented symbol.

**Soundness check (G-AX):** G-AX runs against the **BASE** repo — the gate
harness does NOT apply `patch.diff` before `axiom_check.py` (`gates.py`
`gate_ax` calls `run_in_container` without `apply_gold`; only `gate_conf` uses
`apply_gold=True`). So the imported `char_morse` is the PRE-patch table, in
which the one corrected entry still holds the documented bug
`char_morse['1'] == '----'`. The morse table IS the datum the patch changes, so
the deep model (which encodes the FIXED entry) cannot equal the base callee on
that single entry; that is by design, not unsoundness.

`axiom_check.py` therefore keeps the A-reference honest along the patch
boundary: (a) the key set matches `codeOf`'s represented set exactly; (b) for
every table symbol the patch does NOT touch, `codeOf(symbol) == char_morse[symbol]`
(the real A-reference equality — 51 entries — where over-claiming would hide);
(c) `codeOf` returns `[]` off the set; and (d) for the single corrected symbol
`'1'`, it asserts the base table holds the documented buggy code `'----'` (so we
prove this really is the changed datum, not silently treated as already-fixed)
while the deep model holds the gold value `'.----'`. The model deliberately
differs from the base callee on that one entry — the patch's behavioural change,
validated instead by G-CONF (gold applied), G-RESOLVE (gold resolves), and
G-DIFF (`Solution_prepatch`, reproducing the `'----'` bug, fails the frozen
spec). stdlib-only after the repo import. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16886`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`codeOf`/`codesOf` (the modeled per-symbol table + assembly) to Python and
reconstructs the full `encode_morse` from them plus the UNCHANGED I-ops
(whitespace normalization, unmapped-symbol filtering, `sep`/`word_sep` joins,
trailing-whitespace suffix). It diffs that shadow against `patch.diff`'s
behaviour (the real patched `encode_morse`) over ≥10⁵ fuzzed inputs; exit 0 iff
zero disagreements.
