# mapping.md — astropy__astropy-14598

Cold-derived (`spec_provenance: "cold"`). Scope: the per-field value-recovery
operation inside `Card._split`'s long-string / CONTINUE branch — the single
operation BOTH gold hunks change (the content read and the per-field recovery).

## Symbol binding (file:line @ base_commit 80c3854a5f4f4a6ab86c03d9db7854767fcd83c1)

| Lean symbol | Python symbol | location |
|---|---|---|
| `recoverSegmentText` (the modeled `method`) | the per-field value recovery: from the record content `vc` to the value appended to `values` (or to the early `return kw, vc` where nothing is appended) | `astropy/io/fits/card.py:858-865` (+ the capture regex `card.py:69`) |
| `field` (method input : `List Char`) | `vc` — the record content the recovery's regex matches, in ANY shape `_itersubcards()` produces (comment-free, comment-bearing, or malformed) | `card.py:857-861` |
| `recordContent` | `m = _strg_comment_RE.match(vc)` with the **post-patch anchored** regex, then `m.group("strg") or ""`; `none` = `not m`, the early `return kw, vc` where NO value is appended | `card.py:69` + `card.py:861` (+ the `if not m` guard, `card.py:858-859`) |
| `closesContent` / `onlyPaddingThenAnnotation` | the `_strg` lookahead `(?=$|/| )` under the trailing `$` anchor: the closing `'` is the one past which only ` *` padding and at most the `_comm_field` `/ …` remain, to the end of `vc`. The `breakCh` disjunct is Python's `$`, which matches at the end of the string **or immediately before a single trailing newline** (`re` semantics, `MULTILINE` not set) — so a record may also be terminated by one final `\n` | `card.py:67,69` |
| `isContentChar` | the regex body class `[ -~]` — code points 0x20..0x7E. `firstPrefix` refuses to scan past a character outside it, mirroring the fact that `([ -~]+?\|\'\'\|)` cannot match one | `card.py:67` |
| `firstPrefix` | the non-greedy `([ -~]+?\|\'\'\|)` body scan: the SHORTEST non-empty body **of `[ -~]` characters** whose next `'` satisfies the lookahead | `card.py:67` |
| `rstripSpaces` | `value.rstrip()` | `card.py:862` |
| `dropTrailingAmp` | `if value and value[-1] == "&": value = value[:-1]` | `card.py:863-864` |
| `recovered` (pure spec) | the composition content-read ∘ rstrip ∘ `&`-trim (post-patch), `none` on the `not m` path | `card.py:69,858-864` |
| `out` (method output) | `some` of the per-field `value` appended via `values.append(value)`; `none` where the real code returns early instead of appending | `card.py:859,865` |
| `collapseDoubledQuotes` (prepatch-1 impl-only) | the deleted `.replace("''", "'")` at `card.py:862` (pre-patch) | `card.py:862` (pre-patch) |
| `closesEarly` / `contentEarly` (prepatch-2 impl-only) | the UNanchored `_strg_comment_RE` capture: without the `$`, the lookahead is satisfied by ANY `'` merely followed by a space or `/`, and the regex always matches | `card.py:69` (pre-patch) |

The modeled function is `Card._split`. It is the function BOTH gold hunks edit,
and the function the FAIL_TO_PASS test observes: each F2P assertion round-trips a
long string value through `Card(...).image` (writer) and `Card.fromstring(...)`
(reader); the reader's value is produced by this `_split` branch.

## What the patch changes, and what this bundle models

The gold patch has TWO hunks, both governing the per-field value recovery, and
**both are modeled**:

1. **`card.py:862`** — `value = value.rstrip().replace("''", "'")` →
   `value = value.rstrip()`. The deleted `.replace("''", "'")` collapsed each
   doubled quote `''`→`'` a *second* time (the unchanged downstream value parser
   `_parse_value` already collapses once, `card.py:771`). The duplicate collapse
   silently dropped a quote whenever a literal doubled quote straddled a
   fixed-width field boundary. Modeled by the ABSENCE of `collapseDoubledQuotes`
   in `recovered`; prepatch 1 re-introduces it.
2. **`card.py:69`** — `_strg_comment_RE` gains a trailing `$` anchor. This changes
   which `'` the `_strg` lookahead `(?=$|/| )` accepts as the CLOSING delimiter:
   under the `$` anchor the whole of `vc` must be consumed, so the closing `'` is
   the one past which only padding and at most the `/`-introduced comment field
   remain; without the anchor ANY `'` merely followed by a space or `/` closes the
   body, and the tail past it is lost (and the regex then always matches, so the
   `if not m` early return is unreachable). Modeled by `closesContent` /
   `onlyPaddingThenAnnotation` inside `recordContent`; prepatch 2 re-introduces
   the weaker close test (`closesEarly`/`contentEarly`, impl-only).

**Why both are in scope (correction to the prior bundle).** The prior bundle
declared hunk 2 out of scope; in-container hunk-isolation refuted that —
hunk-1-alone fails F2P assertion 3 (`"x"*100+"'' xxx"` loses the ` xxx` tail).
Hunk 2 determines WHICH delimiter closes the content, so it is a load-bearing
behavior of the recovery the F2P test observes. The modeled op takes `vc` as input
and performs the post-patch content read as its first step. See verdict.md
DEFECT 1 / refinement.md.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| the record content `vc` (a `str`) | `field : List Char` | per Unicode code point; `s` ↔ `s.toList`. NOT restricted to printable ASCII: the reader API accepts arbitrary card text, so `field` ranges over the whole `str` domain. |
| `m.group("strg") or ""` when `m` matched (a `str`) | `recordContent field = some content` | the post-patch `strg` capture, read off the record grammar. |
| `not m` — the early `return kw, vc`, no value appended | `recordContent field = none` | the real code appends NOTHING on this path, so there is no per-field value to correspond to. |
| the recovered per-field `value` (a `str`) | `out : Option (List Char)` | `some out` ↔ value equality `value == String.mk out`; `none` ↔ the early return. |

**Domain note (load-bearing for G-CONF).** The modeled `field` is **any** `vc`
the per-field recovery can receive — the method has no `require` and the domain
is NOT restricted to the shapes the *encoder* produces. `Card.fromstring` /
`Header.fromstring` accept arbitrary card text, so the reader path really can
deliver a `vc` carrying a character outside `[ -~]`. Every claim below therefore
has to hold on the whole `str` domain, and G-CONF fuzzes it accordingly.

- **The record content character set is MODELED, not assumed.** The regex body
  class is `[ -~]+?`, so the capture cannot cross a character outside 0x20..0x7E;
  `isContentChar` + the `firstPrefix` guard reproduce that. Two consequences the
  model now gets right, both confirmed against the real post-patch regex:
  `vc = "'<TAB>'"` → the real code takes the `if not m` early return (`none`),
  and `vc = "'a'\n"` → the real code captures `a` (Python's `$` matches before a
  single trailing newline). A previous revision let the content scan accept ANY
  character and had no line-break case, so it predicted `some "<TAB>"` on the
  first and `none` on the second — UNFAITHFUL on both, in both directions
  (G-PANEL-2). These are reachable: a non-content character sitting in the
  annotation region survives `_itersubcards`, e.g. `vc = "'tail' / com<TAB>ment"`.
- **`rstripSpaces` vs `str.rstrip()` is now a THEOREM, not a domain caveat.**
  `str.rstrip()` strips all trailing whitespace; the Lean `rstripSpaces` drops
  only the space `' '`. Because `recordContent` can only ever return a list of
  `[ -~]` characters — brute-force confirmed over 126766 `some`-answering inputs
  drawn from an alphabet including TAB/CR/LF/VT/FF — the only whitespace that can
  appear in a captured content IS the space, so the two agree on every input the
  strip is applied to. No restriction is being assumed to make this true.
- **All three `_itersubcards()` shapes are modeled**: a bookended comment-free
  record (`'<inner>'`, optionally trailing-space-padded); a bookended record
  carrying a `/`-introduced comment (verified in-container:
  `Card("FOO", "x"*100 + "''", "comment")` yields a final segment
  `vc = "'' / comment"` fed to these EXACT lines — `strg` is merely empty and
  `comm` non-empty, it is the identical code path); and malformed text no
  delimiter closes a content in, which the real code answers with its early
  `return kw, vc`. An earlier revision claimed `captureBody field =
  field.tail.dropLast` and restricted the domain to comment-free records; that
  was also UNFAITHFUL — on `vc = "'' / the trailing comment zz"` it predicted
  `"' / the trailing comment z"` where the real callee produces `""`. The model
  reads the closing delimiter off the record grammar, so it predicts the real
  value on the comment-bearing segments too.
- **Agreement measured, not asserted.** The repaired model was diffed against an
  oracle built from the post-patch regex quoted verbatim: 0 divergences over
  2,015,539 exhaustive inputs of length ≤ 8 on `{' , space, /, x, &, LF}`, 0 over
  177,156 exhaustive inputs of length ≤ 5 on an 11-character alphabet including
  TAB/CR/NUL/0x1F/0x7F/`~`/non-ASCII, and 0 over 400,000 random inputs of length
  ≤ 14 on the same widened alphabet. The pre-repair model diverged on 2,997 of
  the 137,257-input length-≤ 6 sweep, in all three directions
  (real=`some`/model=`none`, real=`none`/model=`some`, and both `some` differing).

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The content read is modeled
  DEEPLY (`recordContent` and its grammar predicates), and the recovery is two
  stdlib string ops modeled deeply (`rstripSpaces` / `dropTrailingAmp`). There is
  no opaque callee, so `axiom_check.py` has nothing to validate.
- No flag/keyword configuration affects this branch: it runs whenever
  `len(self._image) > self.length` and the keyword is non-commentary.

## G-CONF fuzz seed

Pinned LCG seed: **14598** (see `conformance_check.py` `SEED`). Corpus: the three
shapes `_itersubcards()` really produces — bare/unbookended text, bookended
`'<inner>'`, and bookended-plus-annotation `'<inner>' / <tail>` — heavily weighted
toward `'`, space, `/` and `&`, plus boundary cases (empty, all-spaces, lone `&`,
doubled-quote tails, delimiter-then-space straddle, comment-bearing segments,
malformed records).

Two alphabets are sampled, and this is load-bearing: the record-content alphabet
`[ -~]` (three inputs in four, keeping the well-formed-record domain densely
covered) AND that alphabet widened with characters OUTSIDE the content set
(TAB/LF/CR/VT/FF/NUL/0x1F/0x7F/0x85/non-ASCII — one input in four, plus a fixed
block and an every-7th otherwise-well-formed record with one trailing such
character). The previous corpus drew EVERY character from `PRINTABLE` and so
could not reach a single input where the content-character guard or the
end-of-record line break does any work — the exact reason this gate passed while
the model was unfaithful there. It is a checked property of the current corpus
that it would now FAIL: reverting the shadow's `isContentChar` guard and
line-break case makes `conformance_check.py` exit 1, reporting
`field="'<TAB>'" shadow='<TAB>' oracle=None` and `field="'a'\n" shadow=None
oracle='a'` among its first five disagreements.

≈1.14×10⁵ fuzzed inputs, of which ~65k carry a `/`, ~37k carry a character
outside `[ -~]`, and ~59k are texts the real code answers with its early return.
The shadow (Lean `do`-block transcribed to Python:
`recordContent` grammar scan, then rstrip-space, then `&`-trim) is diffed against
the oracle = the real post-patch `_strg_comment_RE` (quoted verbatim) + the
post-patch recovery lines including the `if not m` early return; BOTH sides are
total, so nothing is skipped. Exit 0 iff zero disagreements.
