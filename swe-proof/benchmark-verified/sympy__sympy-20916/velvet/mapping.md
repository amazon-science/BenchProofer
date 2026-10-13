# mapping.md — sympy__sympy-20916

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 82298df6a51491bfaad0c6d1980e7e3ca808ae93`, states the Lean↔Python
type abstraction (the bijection G-CONF and G-AX use to bridge the two value
domains), and gives the provenance of each modeled callee / consumed axiom.

Repo file under change: `sympy/printing/conventions.py`. The bundle models the
**trailing-digit subscript step** of `split_super_sub` — the post-loop step that
decides whether the parsed base name ends in a digit block that should be split
off as a subscript. This is the only behavior the gold patch changes, and it is
exactly what the FAIL_TO_PASS test `test_super_sub`
(`sympy/printing/tests/test_conventions.py`) exercises with Greek / non-ASCII
symbol names (`split_super_sub("ω1") == ("ω", [], ["1"])`, etc.).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `splitTrailingDigits (name : List Char)` | the trailing-digit step of `split_super_sub` — `sympy/printing/conventions.py:63-68` (the `m = _name_with_digits_p.match(name)` block) | the modeled changed behavior: given the parsed base name, split off a trailing digit block as a subscript when present |
| `isLetterU` *(axiom — A-reference)* | the `[^\W\d_]` character class under `re.U` of `_name_with_digits_p` — `sympy/printing/conventions.py:10` (post-patch) | per-code-point "is a (Unicode) letter" recognizer |
| `isDigitU` *(axiom — A-reference)* | the `\d` character class under `re.U` of `_name_with_digits_p` — `sympy/printing/conventions.py:10` (post-patch) | per-code-point "is a (Unicode) decimal digit" recognizer |
| `letterPrefix` / `afterLetters` | the `([^\W\d_]+)` capture of `_name_with_digits_p` — the maximal leading letter run | pure spec: split a name at the end of its maximal leading letter run |
| `stripFinalNewline` | the `$` anchor of `_name_with_digits_p` (no `re.M`): Python's `$` matches at the end of the string **or immediately before one final `'\n'`** | pure spec: set aside at most one final newline before the all-digits tail test; a tolerated final newline is NOT part of the captured digit group |
| `peelDigits` *(deep model — A-reference, composite)* | `_name_with_digits_p.match(name)` and the `name, sub = m.groups(); subs.insert(0, sub)` step — `sympy/printing/conventions.py:10,65-68` (post-patch) | pure spec: the whole trailing-digit decomposition; validated `peelDigits == real _name_with_digits_p split` by axiom_check.py (G-AX) |

The pre-patch repo symbol the change replaces (refinement audit only, not in the
consumer spec view): the ASCII-only regex `_name_with_digits_p =
re.compile(r'^([a-zA-Z]+)([0-9]+)$')` (`conventions.py:10` pre-patch).

The `while` parsing loop of `split_super_sub` (separating `^` superscripts and
`_`/`__` subscripts) is **unchanged** by the patch and produces the `name`
argument the modeled step consumes; it is out of scope (it is the same on both
sides of the diff). The F2P discriminating inputs are separator-free symbol
names, so for them the loop is the identity `name = text` and the entire
observable difference is the trailing-digit step modeled here (G-CONF §4 feeds
the post-loop `name` directly, matching this scoping).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF/G-AX disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the `name` the regex matches; the captured groups) | `List Char` | `s` (Python str) ↔ `s`-as-`List Char` over **code points**; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`. Python iterates `str` by code point, so a non-BMP character (e.g. `𝟙`, U+1D7D9) is ONE `Char`; the bijection is `Char.ofNat (codepoint)`. |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; total over the whole code-point space (Lean `Char` is any valid scalar value). |
| `_name_with_digits_p.match(name)` → groups `(g1, g2)` | `peelDigits name = (g1, some g2)` | a successful match ↔ `some`; the two capture groups ↔ `(letters, digits)`. |
| `_name_with_digits_p.match(name)` → `None` | `peelDigits name = (name, none)` | no match ↔ `none`, name returned whole (mirrors `if m:` being false: `subs` unchanged, `name` unchanged). |

`List Char` is the carrier because every operation is per-code-point (the regex
classes `[^\W\d_]` / `\d`, the maximal-run captures, the all-digits tail test).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `isLetterU` ↔ `[^\W\d_]` under `re.U` (A-reference, regex class)
**Callee:** `re.match(r'[^\W\d_]', ch, re.U)` — a single code point is matched by
the first capture class iff it is a Unicode "word" character that is neither a
decimal digit nor the underscore, i.e. exactly a (Unicode) **letter** (plus the
handful of word-but-not-digit-not-underscore connector/letter-number code points
the class technically includes — see the soundness note). Modeled as the opaque
recognizer `isLetterU`. The three axioms encode only the structural facts the
proof and the F2P behavior need:
* `letter_not_digit` — the letter class and the digit class are disjoint
  (`[^\W\d_]` explicitly excludes `\d`).
* `underscore_not_letter` / `underscore_not_digit` — `_` is excluded from
  `[^\W\d_]` (by the `_`) and is not a `\d`.

### 3.2 `isDigitU` ↔ `\d` under `re.U` (A-reference, regex class)
**Callee:** `re.match(r'\d', ch, re.U)` — a single code point matched by the
second capture class iff it is a Unicode **decimal digit** (`Nd`), e.g. ASCII
`0-9` and `𝟙` (U+1D7D9, MATHEMATICAL DOUBLE-STRUCK DIGIT ONE).

### 3.3 `peelDigits` ↔ the `_name_with_digits_p` split (A-reference, composite)
**Callee:** `_name_with_digits_p.match(name)` with
`_name_with_digits_p = re.compile(r'^([^\W\d_]+)(\d+)$', re.U)`. The anchored
pattern matches `name` iff `name = letters ++ digits` **or**
`name = letters ++ digits ++ '\n'` where `letters` is a non-empty maximal run
of letter code points and `digits` is a non-empty run made up entirely of
decimal-digit code points: without `re.M`, Python's `$` anchor matches at the
end of the string **or immediately before one final newline** (`'\n'` only —
not `'\r'`, not two newlines, and the tolerated newline is NOT captured by
`(\d+)`; e.g. `_name_with_digits_p.match("w1\n").groups() == ("w", "1")`,
while `"w1\n\n"` / `"w1\r"` do not match). Because the letter class and the
digit class are disjoint (§3.1), the boundary between the `([^\W\d_]+)` and
`(\d+)` groups is exactly the end of the maximal leading letter run — so the
structural model `peelDigits` (`letters = takeWhile isLetterU`, `rest = dropWhile
isLetterU`, `digits = stripFinalNewline rest`, accept iff
`letters ≠ [] ∧ digits ≠ [] ∧ digits.all isDigitU`, yielding
`(letters, some digits)`) coincides with the real regex's `(group1, group2)`
decomposition. (Modeling subtleties: (a) a greedy `([^\W\d_]+)` could in
principle backtrack, but it never needs to here — a letter is never a digit,
so the maximal letter run is the unique split point; (b) the `$` newline
tolerance is captured exactly by `stripFinalNewline` since `'\n'` is neither a
letter nor a digit, so a tolerated final newline always sits at the very end of
`rest`. G-AX confirms the composite against the live `re` engine rather than
trusting the argument, with explicit `"w1\n"`-family probes.)

**Soundness check (G-AX):** `axiom_check.py` runs the **real** post-patch
`_name_with_digits_p` (the exact pattern `r'^([^\W\d_]+)(\d+)$'` with `re.U`,
reproduced verbatim from the gold patch — the base_commit tree predates the
patch) over (a) the FAIL_TO_PASS matrix, (b) a boundary set of single code points
spanning Latin/Greek/Cyrillic letters, ASCII + non-BMP digits, underscore,
separators, and (c) ≥10⁴ randomized fuzz names, asserting:
1. `isLetterU c == bool(re.match(r'[^\W\d_]', c, re.U))` and
   `isDigitU c == bool(re.match(r'\d', c, re.U))` for every probed `c`;
2. the three Lean axioms hold for the real classes (disjointness; `_` excluded);
3. the composite `peelDigits(name)` (re-encoded here, mirroring the Lean `def`s,
   including `stripFinalNewline` for the `$` anchor's one-final-newline
   tolerance) equals the real `_name_with_digits_p.match(name)` decomposition
   for every probed `name` — the boundary set includes the `"w1\n"` family
   (split) and `"w1\n\n"`/`"w1\r"`/`"w\n1"` (no split), and the fuzz alphabet
   includes `'\n'`/`'\r'`.
Imports only stdlib `re` + `random`. Exit 0 iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`20916`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`letterPrefix` / `afterLetters` / `peelDigits` (the R/I-tagged ops). The
A-reference recognizers `isLetterU` / `isDigitU` are NOT replaced by axiom
stubs in the shadow — G-CONF isolates the R/I legs by running the **real**
character classes (`re.match(r'[^\W\d_]', …, re.U)` / `re.match(r'\d', …,
re.U)`), the same primitives the oracle uses; their soundness is G-AX's job.
The shadow includes `stripFinalNewline` (the `$` anchor's one-final-newline
tolerance), and the boundary/fuzz corpora include `'\n'`/`'\r'`-bearing names.
The oracle is `patch.diff`'s behaviour: the real post-patch `split_super_sub`
applied at base_commit, fed separator-free names so that its output triple is
`(name', supers=[], subs=[sub?])` and the comparison reduces to the
trailing-digit decomposition this bundle models.
