# refinement.md — sphinx-doc__sphinx-11445

The operation-by-operation correspondence between `model.py`'s implementation
(the `count_leading_header_lines` impl region + the deep `is_header_line` /
`leading_header_count` model) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the inputs in scope, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The recogniser site — the leading-field-block scan in `prepend_prolog`

Gold hunk (`sphinx/util/rst.py`), the two pieces that change behaviour:

```
- docinfo_re = re.compile(':\\w+:.*?')
+ FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])
  ...
  for line in content:
-     if docinfo_re.match(line):
+     if FIELD_NAME_RE.match(line):
          pos += 1
      else:
          break
```

| # | model.py impl op (`count_leading_header_lines`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `content: PSeq[PSeq[int]]` | `content: StringList` of line `str`s | R | each line `str` ↔ `PSeq[int]` of code points; the document ↔ `PSeq` of lines; only the line *values* in iteration order are observed by the scan (mapping.md §2). |
| A2 | `pos = 0` | `pos = 0` (line 81) | I | identical. |
| A3 | `while pos < len(content) and is_header_line(content[pos]): … pos = pos + 1` | `for line in content: if FIELD_NAME_RE.match(line): pos += 1 else: break` | R + A-reference | the `for … else break` over the `StringList` is the same forward scan over the first lines, halting at the first non-match (R: `StringList` iteration ↔ `PSeq` indexing). The per-line test `is_header_line(content[pos])` is the deep model of `FIELD_NAME_RE.match(line)` (A-reference, see below). The increment is identical. |
| A4 | `return pos` (with `Result() == leading_header_count(content)`) | `pos` is the count used at lines 88–97 to place the prolog | R | the returned `int` is identical; the spec pins it to the greatest all-field-line prefix length. |

### The deep model (A-reference), the heart of the change

`is_header_line` / `first_boundary` (model.py pure region) spell out the
docutils field-marker grammar on the back-slash-free, newline-free domain: a
line is a field line iff it is `:name:` whose closing (boundary) colon is
preceded by a non-space and followed by a space or end-of-line, with the name's
first code point neither a colon nor a space. The changed string operation is
modeled **deeply**, NOT behind a consumed axiom: there is no `@ContractOnly`
recogniser the proof uses. Instead the deep model is validated **== the real
recogniser** out-of-band: G-AX (`axiom_check.py`) builds the real recogniser
exactly as the gold patch does (`re.compile(Body.patterns['field_marker'])`) and
asserts `is_header_line(line) == bool(FIELD_NAME_RE.match(line))` on the boundary
corpus + 200 000 fuzz inputs over the back-slash-free, newline-free domain
(mapping.md §3.1).

The discriminating content of the change — a `` :name:`role` `` heading is NOT a
field line because its closing colon is followed by a back-quote rather than a
space — lives in `first_boundary`'s back-quote case + the final
`b == len(line) - 1 or line[b + 1] == SPACE` test (model) ⇔ the grammar's
`(?<! ):( +|$)` tail (real). The pre-patch recogniser `:\\w+:.*?` accepts such a
line; `model_prepatch.py` reproduces that acceptance (an inline `:word:` test
that ignores what follows the closing colon) and **fails** the proof on the
discriminating clause (see §C).

### Domain restriction (R, declared)

The model is over the back-slash-free, newline-free domain (lines with no code
point 92, 10, or 13); mapping.md §2 documents why this is faithful for the
docinfo/role/heading lines in scope, and axiom_check.py fuzzes exactly that
domain (asserting each checked line stays inside it). This is a type/domain
refinement (R), not a changed-op-hidden-in-an-axiom: the back-slash escape and
the newline-anchor (`$`-before-`\n`) semantics are both unrelated to the bug
being fixed (which is about the closing-colon tail), and no input in scope
exercises either — the modeled lines are the elements a document is already
split into, so they carry no embedded newline/CR.

## B. The insertion site — placing the prolog (identical pre/post patch)

Gold hunk lines 88–97 (`content.insert(pos, '', '<generated>', 0)` when
`pos > 0`; the `<rst_prolog>` lines; the trailing `<generated>` blank line; plus
the added `lineno = 0` guard) are **not changed in behaviour by this fix on the
inputs in scope** — they consume the `pos` value the scan computes.

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (not re-modeled) | the `content.insert(...)` calls at 88–97 | I | the insertion layout is a deterministic function of `pos` and `prolog.splitlines()`, identical pre- and post-patch. The only behavioural difference the F2P tests observe is the value of `pos`, which is exactly what `count_leading_header_lines` pins (A3). The added `lineno = 0` (line 86 post-patch) only guards the `prolog.splitlines() == []` case; for every F2P/P2P prolog (`'…\nhello reST!'` / `'…\nhello reST!\n'`) `splitlines()` is non-empty, so `lineno` is bound identically with or without the guard — that line changes no tested behaviour and is not an independently-observable fixed behaviour (no separate `model_prepatch` is warranted for it). |

## C. The prepatch and the discriminating clause (G-DIFF)

`model_prepatch.py` keeps the spec byte-identical (the `pure`, `pre-conditions`,
`post-conditions`, `invariants` regions and the lemmas `lfc_reaches`,
`lfc_all_markers` are unchanged — `same_spec` holds). Only the `impl` region
differs: the loop test is replaced by an **inline pre-patch recogniser** — a
line is accepted as soon as it is `:`, a non-colon name code point, and contains
any later colon (regardless of what follows it), faithfully reproducing
`:\\w+:.*?` on the lines in scope (it accepts `` :mod:`foo` ``).

Because the frozen invariant `Forall i < pos: is_header_line(content[i])` and
the lemma call `lfc_reaches(content, pos + 1)` (whose precondition is the same
`Forall`) are about the **post-patch** predicate, advancing `pos` past a line the
pre-patch test accepts but `is_header_line` rejects (exactly `` :mod:`foo` ``)
is unprovable. The prepatch therefore FAILS on the precondition of
`lfc_reaches` — the clause `Forall i < p: is_header_line(doc[i])` — which is
precisely the spec sensing the change. (Verified: `model_prepatch.py` fails with
"The precondition of method lfc_reaches might not hold … is_header_line(doc[i])".)

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-line field recogniser — is modeled **deeply**
(`is_header_line` / `first_boundary`, an A-reference validated by G-AX), not
hidden behind an axiom about the function under change. There is **no consumed
`@ContractOnly` axiom** (the axioms region is empty), so there is no A-consumed
row and no dead axiom.

## E. verify(model) ⇒ resolved

`count_leading_header_lines` verifies only if it returns the greatest all-field-line
prefix length under the post-patch predicate (`Result() == leading_header_count`,
with `leading_header_count` built from `is_header_line`). By R (line `str` ↔
`PSeq[int]`, document `StringList` ↔ `PSeq` of lines, the `for…else break` scan ↔
the indexed while loop) the verified scan computes the same `pos` as the gold
loop on the lines in scope; by G-AX the deep model `is_header_line` equals the
real `FIELD_NAME_RE.match` (A-reference). The downstream insertion (B1, I) is
identical pre/post patch and a deterministic function of `pos`. Therefore an
implementation satisfying this spec, refined by the map above, computes the same
`pos` and produces the same insertion as the gold patch — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this
document, G-EQ) plus the A-reference soundness (G-AX); there is no axiom-soundness
trust point because the bundle consumes no axiom.
