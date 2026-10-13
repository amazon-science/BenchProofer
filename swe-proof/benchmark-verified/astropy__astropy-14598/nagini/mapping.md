# mapping.md — astropy__astropy-14598

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 80c3854a5f4f4a6ab86c03d9db7854767fcd83c1`, states the type
abstraction, and gives the provenance of each deep model (the operation it
stands in for + the exact behaviour it encodes). There are NO consumed
`@ContractOnly` axioms; the changed operations are modelled deeply and validated
against the real library operations by `axiom_check.py` (G-AX).

Repo file under change: `astropy/io/fits/card.py` (class `Card`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recover_payload(segment)` | the per-continuation-segment string capture in `Card._split`: `_strg_comment_RE.match(vc)` + `m.group("strg")` — `card.py:857,861` (regex defined `card.py:69`) | obligation (A): the full payload recovered from one segment (the regex `$`-anchor site) |
| `unescape_value(captured, witness)` | the value un-escape in `Card._split`/`Card._parse_value`: `value.rstrip().replace("''","'")` → `value.rstrip()` (`card.py:862`) composed with the assembled-value un-escape `re.sub("''","'", m.group("strg"))` (`card.py:771`) | obligation (B): the single `''`→`'` collapse (the `.replace` removal site) |
| `escape_quotes(s)` *(deep model — A-reference)* | the serialisation escape `self._value.replace("'", "''")` in `Card._format_long_image` (`card.py:1060`) | pure spec: escape of a value (each `'`→`''`) |
| `unescape_quotes(s)` *(deep model — A-reference)* | the un-escape `re.sub("''","'", ...)` (`card.py:771`) / `str.replace("''","'")` (`card.py:862` pre-patch) | pure spec: single left-to-right collapse `''`→`'` |
| `rt_lemma(v)` | (no repo symbol) | proof: the round-trip identity `unescape_quotes(escape_quotes(v)) == v` |

The pre-patch repo constructs the change removes / alters (for the refinement
audit, not referenced from the consumer spec view): the unanchored
`_strg_comment_RE` regex (`card.py:69`, lacking the trailing `$`) and the extra
`.replace("''","'")` un-escape in `_split` (`card.py:862`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the card-image segment payload `vc`/`strg`, the value) | `List[int]` of Unicode code points | `s[k]` ↔ `seg[k] == ord(s[k])`; `len(s)` ↔ `len(seg)`; `str` `+`/slice ↔ list `+`/`take`/`drop` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| single quote `'` (U+0027) | code point `39` | the escaped/un-escaped character |
| space `' '` (U+0020) | code point `32` | the interior space the pre-patch regex truncates at |
| value/comment separator `/` (U+002F) | code point `47` | excluded from `recover_payload`'s domain (see §3.3) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model provenance (kind-A-reference — checked by G-AX / axiom_check.py)

There are no consumed axioms. The three deep models below are each validated
`== the real library operation` by `axiom_check.py`.

### 3.1 `escape_quotes` ↔ `str.replace("'", "''")` (A-reference)
**Op:** `Card._format_long_image` doubles every single quote when laying a long
value across continuation segments: `value = self._value.replace("'", "''")`
(`card.py:1060`). The deep model `escape_quotes` (model.py pure region) maps
each code point `39` to the pair `(39,39)` and copies every other code point —
exactly `str.replace("'", "''")`. G-AX asserts equality on boundary + 40 000
fuzz strings (incl. `/`).

### 3.2 `unescape_quotes` ↔ `re.sub("''", "'", s)` (A-reference)
**Op:** the assembled value is un-escaped once by `re.sub("''", "'", m.group("strg"))`
(`card.py:771`); the gold patch removes a SECOND, premature un-escape
`value.rstrip().replace("''", "'")` from `_split` (`card.py:862`), leaving
exactly one un-escape pass. The deep model `unescape_quotes` collapses each
LEADING pair `(39,39)` to one `39` and copies any other leading code point —
the single non-overlapping left-to-right pass that both `re.sub("''","'",.)`
and `str.replace("''","'")` perform. G-AX asserts equality on boundary + fuzz.

### 3.3 `recover_payload` ↔ the `$`-anchored `_strg_comment_RE` strg-group (A-reference)
**Op:** in `Card._split` each continuation segment's value-comment string `vc`
is matched by `_strg_comment_RE` and the value taken from `m.group("strg")`
(`card.py:857,861`). The gold patch appends `$` to the regex (`card.py:69`).
The deep model `recover_payload` returns the FULL payload (`Result == segment`).

* **Faithful only on the no-separator domain.** With the `$` anchor the regex
  recovers the complete payload *unless the payload contains the value/comment
  separator `/`*, at which point even the fixed regex splits the string at `/`.
  Accordingly `recover_payload` `Requires` that the segment contains no code
  point `47` (`/`). The FAIL_TO_PASS inputs (`"x"*100 + "''"`, `+ "''xxx"`,
  `+ "'' xxx"`) contain no `/`, so they lie in the modelled domain. G-AX asserts
  `_strg_comment_RE` (with `$`) `strg`-group `== full payload` on every
  no-`/` escaped payload over `{', space, x, y, a, b, Z, 0}`, 120 000+ fuzz, 0
  mismatch.
* **Flag/anchor dependency (record for G-AX):** the equality holds for the
  FIXED regex (trailing `$`); the PRE-PATCH regex (no `$`) instead truncates at
  the first single quote immediately followed by an interior space — which is
  precisely the truncation modelled in `model_prepatch_2.py` and ALSO asserted
  by G-AX (so the prepatch is faithful to the real pre-patch regex).

### 3.4 Round-trip identity (the observed behaviour)
`axiom_check.py` also runs the end-to-end round trip against the REAL regex +
REAL `re.sub`: for every no-`/` value `v`, un-escaping the full capture of
`v.replace("'","''")` returns `v`. This is the FAIL_TO_PASS property and the
spec-level guarantee `rt_lemma` proves (`unescape_quotes(escape_quotes(v)) == v`).
`axiom_check.py` imports only the standard-library `re` module (the very module
the patch edits) and `random`; exit 0 iff sound.

## G-CONF — differential conformance (`conformance_check.py`)

The refinement leg: the `# impl-start`/`# impl-end` regions of `model.py` diffed
against the REAL gold-patched `astropy/io/fits/card.py`. Appended section; §1-§3
above are unchanged.

**Shadow (provenance `direct` — on nagini the model IS Python).** Both impl
regions copied VERBATIM with only the contract calls deleted
(`Requires`/`Ensures`/`Invariant`/`Assert` + the `# invariants-start|end`
markers): `recover_payload` (obligation A) and `unescape_value` (obligation B).
Dependencies carried over contract-stripped: the `@Pure` helpers
`escape_quotes` / `unescape_quotes`, the ghost `rt_lemma` (called verbatim from
`unescape_value`'s region; proof-only, a no-op after stripping), and a `PSeq`
shim + `ToSeq` realizing the Nagini carriers as an immutable tuple sequence.
There are NO `@ContractOnly` callees in this bundle (the `axioms` region is
empty), so no axiomatized body is stood in for.

**Oracles — all four CALLED into the patched repo, none transliterated.**

| leg | repo symbol (post-patch) | how it is driven |
|---|---|---|
| A1 | `Card._strg_comment_RE.match(vc)` + `m.group("strg")` — `card.py:857,861`, pattern `card.py:69` (the `$` IS gold hunk 1) | the compiled pattern read off the patched `Card` class, matched against a real CONTINUE record's `vc` = `'<payload>'` |
| A2 | `Card._split` — `card.py:829-875` | a genuine two-record long-card image (`CONFIG  = '&'` + `CONTINUE  '<payload>'`); the recovered text is read back out of the returned valuecomment. Sensitive to BOTH gold hunks |
| B | the surviving single un-escape `re.sub("''","'", m.group("strg"))` in `Card._parse_value` — `card.py:771` | a real one-record image `CONFIG  = '<captured>'`, read back via `Card.value` |
| C | `_format_long_image`'s escape (`card.py:1060`) + the reader — the FAIL_TO_PASS observable | `Card.fromstring(str(Card("CONFIG", v))).value == v`, against the model composition `unescape_value(recover_payload(escape_quotes(v)), v)` |

**Type bridge (§2 inverted).** `to_cps(s) = [ord(c) for c in s]` /
`from_cps(l) = "".join(chr(c) for c in l)`; code point 39 = `'`, 32 = `' '`,
47 = `'/'`. Inputs are generated as real card `str` payloads and converted in, so
every input is both a real card payload and inside the model's `Requires`.

**Domain — each restriction is the model's own `Requires` or an UNCHANGED op.**
* no `/` (cp 47): `recover_payload`'s explicit `Requires` (see §3.3).
* printable ASCII 32..126: the real `Card` rejects anything else outright, so
  there is no oracle off this alphabet (confirmed in-container).
* no trailing blank (legs A2/B/C): `value.rstrip()` (`card.py:862`) stands
  IDENTICALLY on both sides of the gold hunk, and `refinement.md` B1 already
  fixes leg B's carrier as "the no-trailing-blank carrier". The first trial run
  disagreed on exactly 10 inputs, ALL of them only a trailing blank the shadow
  keeps and `rstrip` drops; that was the bridge omitting a documented
  restriction, so the DOMAIN was corrected and `model.py` was NOT touched.
* legs A2/C additionally exclude a trailing `&`: the unconditional
  CONTINUE-marker trim `card.py:863-864`, identical pre- and post-patch.
The `''`-collapse and full-capture behaviors under specification run on every
input, so no restriction routes around the patched branch. The three F2P values
(`"x"*100 + "''"`, `+"''xxx"`, `+"'' xxx"`) are pinned in the boundary list.

**Inputs / seed.** `SEED = 14598` (module constant `SEED`). 200 123 checked
inputs: 375 boundary (empty, singleton, every impl branch, the F2P shapes, quote
pairs straddling the 67-char escaped-payload boundary) then seeded fuzz —
A1 x70 068, A2 x64 806, B x50 065, C x15 184. All 5 impl-region branches are
asserted to fire (a cold branch FAILS the run). Exit 0 iff zero disagreements.

**Falsification evidence (the check can fail).** Against the UNPATCHED repo it
exits 1, catching both hunks (A1/A2 on `x'' x`: oracle truncates to `x'`; A2 on
`x''`: oracle double-un-escapes to `x'`). Four shadow mutants each die on the leg
they damage: un-escape removed -> leg B; `recover_payload` truncated at
quote-then-space (the prepatch behavior) -> A1+A2; `recover_payload` dropping the
last code point -> A1; `escape_quotes` emitting one quote -> leg C.
