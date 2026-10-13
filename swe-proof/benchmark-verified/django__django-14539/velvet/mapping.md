# mapping.md — django__django-14539

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6a5ef557f80a8eb6a758ebe99c8bb477ca47459e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the modeled callee.

Repo file under change: `django/utils/html.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `peelTrailingPunctuation (token tail : List Char)` | the trailing-punctuation block of `trim_punctuation(lead, middle, trail)` — `django/utils/html.py:283-288` (closure inside `urlize`, defined at `:259`) | the modeled changed code: peel trailing sentence punctuation off `middle` into `trail` |
| `entityDecode` *(opaque — A-reference)* | `html.unescape` — CPython stdlib `Lib/html/__init__.py` (called at `django/utils/html.py:283`, `middle_unescaped = html.unescape(middle)`) | UNCHANGED stdlib callee that decodes HTML entities; used only to LOCATE the real trailing-punctuation count |
| `isTrailingPunct (c : Char)` | the character set `TRAILING_PUNCTUATION_CHARS = '.,:;!'` — `django/utils/html.py:19` | pure spec: membership in the trailing-punctuation alphabet |
| `stripTrailingPunct (s : List Char)` *(deep model — A-reference)* | `str.rstrip(TRAILING_PUNCTUATION_CHARS)` — `django/utils/html.py:284` | pure spec: right-strip of the trailing-punctuation alphabet; deep model of `.rstrip`, validated `== str.rstrip` by axiom_check.py (G-AX) |
| `trailingPunctCount (token : List Char)` | `punctuation_count = len(middle_unescaped) - len(stripped)` — `django/utils/html.py:286` (post-patch) | pure spec: count of trailing punctuation, measured on the DECODED form |
| `Split { core, tail }` | the `(middle, trail)` pair the block updates | structure carrying the two updated locals |

The pre-patch repo expressions the change replaces (refinement audit only, not
in the consumer spec view): `trail = middle[len(stripped):] + trail` and
`middle = middle[:len(stripped) - len(middle_unescaped)]` (`html.py:286-287`
pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (`middle`/`trail`, the block's args and results) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `s[:n]` (prefix slice, `0 ≤ n ≤ len`) | `s.take n` | identical prefix |
| `s[n:]` (suffix slice, `0 ≤ n ≤ len`) | `s.drop n` | identical suffix |
| `s[:-pc]` (drop last `pc`, `0 < pc ≤ len`) | `s.take (s.length - pc)` | equal when `pc ≤ len` (G-AX A-reference 1 guarantees `pc ≤ len`, so Lean's truncated Nat subtraction is exact) |
| `s[-pc:]` (last `pc`, `0 < pc ≤ len`) | `s.drop (s.length - pc)` | equal when `pc ≤ len` (same guarantee) |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-code-point slicing.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `entityDecode` ↔ `html.unescape` (A-reference, OPAQUE)
**Callee:** CPython `html.unescape(s)`. The decoder is modeled as an OPAQUE Lean
function (`opaque entityDecode`) — NO value-level axiom is asserted about it,
because the spec only needs it as a deterministic function whose RESULT LENGTH
locates the trailing-punctuation count. The spec view names it only as "a
standard-library HTML entity decoder" (no leakage).

**Soundness obligations G-AX validates against the real callee:**
- **non-lengthening:** `len(html.unescape(s)) ≤ len(s)` for every `s`. This is
  what makes the spec's `token.length − trailingPunctCount token` EXACT (Lean
  truncated Nat subtraction would otherwise clamp). Verified: every HTML5 entity
  token is at least as long as its expansion (the longest multi-code-point
  expansions, e.g. `&acE;`→2 chars, still come from ≥5-char tokens), and
  numeric/short forms (`&lt`, `&amp`) shrink. Checked on 22 boundary + 20 000
  fuzz inputs.
- **functionality / determinism:** `entityDecode ≡ html.unescape` (used as the
  oracle in the deep-peel equivalence below).

### 3.2 `stripTrailingPunct` ↔ `str.rstrip(TRAILING_PUNCTUATION_CHARS)` (A-reference)
**Callee:** Python `str.rstrip('.,:;!')`. Modeled deeply as
`(s.reverse.dropWhile isTrailingPunct).reverse`. G-AX asserts the model equals
the real `.rstrip(TRAILING_PUNCTUATION_CHARS)` on all boundary + fuzz inputs,
and that `trailingPunctCount` equals the gold `punctuation_count =
len(middle_unescaped) - len(stripped)`.

### 3.3 End-to-end deep-peel == gold block (A-reference)
**Soundness check (G-AX):** `axiom_check.py` runs the deep-model peel
(`token[:len−count], token[len−count:]+tail`) and the gold-patched block
(`html.py:283-288` verbatim) on the same inputs and asserts they agree.
Imports only stdlib `html`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14539`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`isTrailingPunct` / `stripTrailingPunct` / the `take`/`drop` peel (R/I-tagged
ops) to Python and leaves `entityDecode`'s callee as the REAL `html.unescape`
(A-tagged → run real callee, not an axiom model). It also anchors against the
real patched `urlize` on the issue's own example.
