# mapping.md — django__django-10097

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b9cf764be62e77b4777b3a75ec256f6209a57671`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep model.

Repo file under change: `django/core/validators.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateAuthsegment (seg : List Char)` | the user:pass authentication group of `URLValidator.regex` — `django/core/validators.py:97` (the `(?:[^\s:@/]+(?::[^\s:@/]*)?@)?` hunk) | the modeled changed operation: decides whether a candidate authentication segment (text before the terminating `@`) is well-formed |
| `isWhitespace (c : Char)` | the regex `\s` class (Unicode-aware) | pure spec: membership in the full Unicode whitespace class |
| `isUchar (c : Char)` | the regex class `[^\s:@/]` | pure spec: a single authentication character (not whitespace, `:`, `@`, `/`) |
| `bodyOk (s : List Char)` *(deep model — A-reference)* | the body of the compiled group: every char is `[^\s:@/]` or the single optional `:` separator | pure spec: front-recursive fold over the segment |
| `colons (s : List Char)` *(deep model — A-reference)* | the single optional `:` separator allowed by `(?::[^\s:@/]*)?` | pure spec: count of `:` separators (at most one) |
| `accepts (s : List Char)` *(deep model — A-reference)* | a FULL match of `[^\s:@/]+(?::[^\s:@/]*)?` (re.IGNORECASE) on the segment | pure spec: acceptance of a segment; deep model of the changed matcher, validated `accepts == fullmatch` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch class the change replaces (refinement audit only, not in the
consumer spec view): `\S+(?::\S*)?` (the body excluded only whitespace, so `:`,
`@`, `/` and extra colons were all permitted).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the authentication segment) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]`; a suffix `s[k:]` ↔ `l.drop k` |
| a single Python character `ch` | Lean `Char` | code point: `ord(ch)` ↔ `(c : Char).toNat`; on the BMP this is total and exact; the three separators are `':'`=58, `'@'`=64, `'/'`=47 |
| the `re.IGNORECASE` flag | omitted | the authentication character class `[^\s:@/]` is case-insensitive-invariant (it contains neither cased letters nor case-folding pairs), so the flag has no effect on acceptance; recorded for provenance only |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is per-code-point.

## 3. Deep-model provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `accepts` deep model ↔ the compiled authentication group
**Matcher:** the post-patch user:pass authentication group
`re.compile(r'[^\s:@/]+(?::[^\s:@/]*)?', re.IGNORECASE)`, the inner group of the
`(?:...@)?` wrapper in `URLValidator.regex`. The changed matching operation is
modeled **deeply** by `accepts` (with `bodyOk`/`colons`/`isUchar`/`isWhitespace`)
in the `pure` region; there is **no matcher axiom** the proof consumes.

A segment full-matches that group iff:
* it is **non-empty** (the leading `[^\s:@/]+` requires ≥1 char) — `accepts []
  = false`;
* it does **not begin with `:`** (the mandatory user run `[^\s:@/]+` excludes
  `:`) — the `seg[0]!.toNat != 58` clause;
* every code point other than at most one separator `:` is an **authentication
  character** `[^\s:@/]` — `bodyOk s` with `isUchar`;
* there is **at most one** separator `:` (the optional `(?::…)?` allows a single
  `:` introducing the password run, and the password run `[^\s:@/]*` again
  excludes `:`) — `colons s ≤ 1`.

`isWhitespace` enumerates the **entire** Unicode `\s` class (the ASCII run
`{9..13, 32}` plus the C1/separator code points `{0x1c..0x1f, 0x85, 0xa0,
0x1680, 0x2000..0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000}`), so `isUchar`
is the exact complement of `[\s:@/]` and the equivalence to the real matcher is
**universal**, not ASCII-only.

**Soundness check (G-AX):** `axiom_check.py` compiles that exact group and
asserts `accepts == group.fullmatch` on 188 boundary inputs over the four
forbidden classes and their mixtures, a programmatic per-code-point sweep over
all 29 Unicode-whitespace code points (each alone and embedded), and 100 000
randomized fuzz strings whose alphabet includes the full whitespace block plus
astral/accented/bullet non-whitespace code points. Imports only stdlib `re`.
Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10097`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `validateAuthsegment`'s impl (the backward per-code-point fold,
R/I-tagged) to Python over `str` and compares it against the real post-patch
compiled group's full-match (the oracle). There is no A-consumed callee, so the
shadow is pure R/I.
