# mapping.md — sphinx-doc__sphinx-11445

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 71db08c05197545944949d5aa76cd340e7143627`, states the type
abstraction, and gives the provenance of the deep-model reference (the changed
recogniser the model is validated against, checked by axiom_check.py / G-AX).

Repo file under change: `sphinx/util/rst.py`.

## 1. Symbol ↔ repo binding

Note on naming: the solver-visible spec view (model.py docstring + the `axioms`
/ `pure` / `pre-conditions` / `post-conditions` regions) is de-narrated — it
names neither the patched file/symbol nor the diagnosis, and the deep-model
predicate is called `is_header_line` (not echoing the gold-introduced
`field_marker` / `FIELD_NAME_RE`). This file (mapping.md), refinement.md, and
axiom_check.py are evidence-only (never shown to the consumer), so they cite the
real docutils provenance and the patched symbols explicitly.

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `count_leading_header_lines(content)` | the leading-field-block scan inside `prepend_prolog` — `sphinx/util/rst.py:81-86` (`pos = 0` / `for line in content: if <recogniser>.match(line): pos += 1 else: break`) | the modeled changed computation: how many leading lines belong to the bibliographic field block (`pos`) |
| `is_header_line(line)` *(deep model — A-reference)* | the per-line recogniser `<re>.match(line)` at `sphinx/util/rst.py:83`. Pre-patch: `docinfo_re = re.compile(':\\w+:.*?')` (line 28). Post-patch: `FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])`, `Body` from `docutils.parsers.rst.states` | pure spec: the desired (post-patch) field-line predicate; the deep model of the *changed* recogniser, validated `is_header_line == FIELD_NAME_RE.match` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `first_boundary(line, k)` | (internal to the predicate) the docutils field-name grammar's search for the colon that closes the field name | pure spec helper: the first "boundary colon" (colon followed by space / back-quote / end of line) |
| `leading_header_count(doc)` | the value `pos` reaches at line 86 — the greatest all-field-line prefix length | pure spec: the length of the leading field block (front-recursive characterization) |
| `COLON / SPACE / BACKTICK` | the code points `':'` (58), `' '` (32), `` '`' `` (96) | the literal code points the grammar distinguishes |

The downstream insertion logic (`sphinx/util/rst.py:88-97`: the `<generated>`
blank line when `pos > 0`, the `<rst_prolog>` lines, the trailing `<generated>`
blank line) is **identical pre- and post-patch** and depends only on the value
`pos`; it is not re-modeled (refinement.md §B, tagged I).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a line `str` | `PSeq[int]` of Unicode code points | `line[k]` ↔ `ord(line[k])`; `len(line)` ↔ `len(line)`; an empty line ↔ the empty `PSeq` |
| the document `StringList` of lines | `PSeq[PSeq[int]]` | `content[i]` ↔ the i-th line as a code-point sequence; `len(content)` ↔ number of lines. Only the *iteration order* of lines (what `for line in content` sees) is observed by the modeled computation; the source/lineno metadata `StringList` also carries is untouched by the field-block scan. |
| `<recogniser>.match(line)` (truthy/falsey) | `is_header_line(line)` (bool) | `bool(re.match(...))` ↔ the deep predicate; validated equal by axiom_check.py |
| `pos` (an `int`) | the returned `int` | identical |

`str` indexing/iteration is banned in Nagini, so a line is carried as
`PSeq[int]` throughout and the document as `PSeq[PSeq[int]]`.

### Modeled domain restriction (back-slash AND newline / carriage-return)

The deep model is declared sound only on lines that contain neither

1. **a back-slash** `\` (U+005C, code point 92): the docutils `field_marker`
   grammar treats `\` as an escape introducer (`\\.` consumes the following
   code point), so a back-slash can hide what would otherwise look like a
   boundary colon. The deep model does NOT model this escape.
2. **a newline `\n` (U+000A) or carriage-return `\r` (U+000D)**: the grammar's
   trailing `( +|$)` anchor matches `$` just *before* a trailing `\n`, so the
   real recogniser accepts e.g. `':a:\n'`, whereas the deep model treats the
   newline as an ordinary trailing code point after the boundary colon and
   rejects it. The deep model does NOT model line-terminator semantics.

Both restrictions are faithful for the inputs in scope. The modeled lines are
the individual lines a document has *already* been split into (the elements of
the `StringList` / `prolog.splitlines()`), so they carry no embedded
newline/CR; and docinfo field headers (`:title:`, `:author:`) and role/heading
lines (`` :mod:`pkg` ``) never place a back-slash before the field-name colon.
None of the F2P/P2P test lines contain a back-slash, newline, or carriage
return. axiom_check.py fuzzes over exactly this domain (its alphabet excludes
`\`, `\n`, and `\r`, and `check_line` asserts each checked line stays inside the
domain); refinement.md §A records the restriction in the R/A-reference audit.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `is_header_line` deep model ↔ the docutils `field_marker` recogniser

**Callee (post-patch):** `FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])`,
where `Body` is `docutils.parsers.rst.states.Body`. The pattern (docutils
0.18–0.20) is:

```
:(?![: ])([^:\\]|\\.|:(?!([ `]|$)))*(?<! ):( +|$)
```

i.e. a field marker is: a leading colon; a first name code point that is
neither `:` nor space (`(?![: ])`); a name body of code points that are not `:`
or `\` (or an escaped `\.`, or an internal `:` **not** followed by space /
back-quote / end-of-line); then a closing `:` whose preceding code point is not
a space (`(?<! )`) and which is followed by one-or-more spaces or end-of-line
(`( +|$)`).

On the back-slash-free domain this is exactly the deep model: scan for the
**first boundary colon** (the first `:` at index ≥ 2 that the name body cannot
absorb — i.e. one followed by space, back-quote, or end-of-line); the line is a
field marker iff that boundary colon is preceded by a non-space and followed by
a space or end-of-line. A colon followed by a **back-quote** is a boundary colon
that is NOT followed by a space, so `` :mod:`pkg` `` is rejected — which is the
behavioural content of the change.

**The change (for the refinement audit, not referenced from the spec view):**
the pre-patch recogniser `docinfo_re = re.compile(':\\w+:.*?')` matches any line
of the form `:word:` regardless of what follows the closing colon (the lazy
`.*?` matches the empty string), so it **wrongly** accepts `` :mod:`pkg` `` as a
field line. The post-patch recogniser is the docutils field-marker grammar,
which requires the closing colon be followed by a space or end-of-line and so
rejects `` :mod:`pkg` ``. The single observable change is on lines whose closing
colon is not followed by a space/end-of-line.

Docutils provenance: `docutils/parsers/rst/states.py`, `class Body`,
`patterns['field_marker']` (the same grammar the rST parser uses to detect
field lists; docs:
https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#field-lists).

**Soundness check (G-AX):** `axiom_check.py` constructs the REAL recogniser
exactly as the gold patch does (`re.compile(Body.patterns['field_marker'])`) and
asserts `is_header_line(line) == bool(FIELD_NAME_RE.match(line))` on 24
boundary lines (every F2P/P2P test line, the bug-discriminating `` :mod:`foo` ``
heading, and adversarial grammar corners: `:a:`, `:a: `, `:a:x`, `: bad:`,
`::bad:`, `:x::y: z`, `` :x:`y`: z ``, `:= : x:`, …) plus 200 000 randomized
fuzz lines over the back-slash-free, newline-free alphabet (and asserts each
checked line stays inside that domain). It imports only `re`/`random`
(stdlib) and `docutils` (the very library the gold patch imports). Exit 0 iff
the deep model equals the real recogniser on every checked input.

There is **no consumed `@ContractOnly` axiom**: the changed operation (the
recogniser) is modeled deeply, so it is an A-reference validated by G-AX, not an
axiom the proof consumes.
