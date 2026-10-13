# mapping.md — sphinx-doc__sphinx-10323

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 31eba1a76dd485dc633cae48227b46879eda5df4`, states the type
abstraction, and gives the provenance of the deep-model reference (the per-line
trim callee the deep model is validated against by G-AX).

Repo file under change: `sphinx/directives/code.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble(included, lead, trail, n)` | `LiteralIncludeReader.read(self, location)` — `sphinx/directives/code.py:219` (the filter pipeline at lines 223-232, assembled output `''.join(lines)`) | the modeled changed function: the filter-pipeline assembly that combines the included text with the author-supplied leading and trailing lines and the left-margin trim |
| `trim_block(lines, n)` *(deep model — A-reference)* | `dedent_lines(lines, dedent, location)` — `sphinx/directives/code.py:51` (per line, the `new_line = line[dedent:]` body, lines 58-63), as invoked by `LiteralIncludeReader.dedent_filter` — `sphinx/directives/code.py:357` | unchanged community callee performing the per-line left-margin trim; modeled deeply (front-recursive fold + the per-element lemma `trim_block_at`) and validated `trim_block == dedent_lines` per line by axiom_check.py (G-AX), NOT consumed as an axiom |
| `trim_block_at(lines, n, k)` | (proof lemma) | a verification lemma proving `trim_block(lines, n)[k] == lines[k].drop(n)` by induction; not a repo symbol |
| `lead` | the line inserted by `LiteralIncludeReader.prepend_filter` — `sphinx/directives/code.py:343` (`lines.insert(0, prepend + '\n')`) | the author-supplied leading line (the `prepend` option content) |
| `trail` | the line appended by `LiteralIncludeReader.append_filter` — `sphinx/directives/code.py:350` (`lines.append(append + '\n')`) | the author-supplied trailing line (the `append` option content) |
| `included` | the lines flowing into the trim/prepend/append stage (output of the file read + the line-selection filters) | the included text block |
| `n` | the trim width (`dedent` option value, an `int`) passed to `dedent_lines` | left-margin trim width |

The pre-patch repo behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): in `read()` the per-line trim filter
was the LAST stage of the pipeline (after the leading/trailing lines were
already inserted), so the trim reached the author-supplied lines too; the fix
moves the trim stage to run before the leading/trailing lines are inserted.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a list of text lines (`List[str]`, each `str` ending in `'\n'`) | `PSeq[PSeq[int]]`: a sequence of lines, each line a `PSeq[int]` of its content code points WITHOUT the trailing newline | line `k` ↔ `m[k]`; the `'\n'` separator is implicit, re-added on render `c ↦ c + '\n'`; `len(list)` ↔ `len(m)`; list `insert(0, x)`/`append(x)` ↔ `PSeq(x) + …`/`… + PSeq(x)` |
| a single text line `str` (content + `'\n'`) | `PSeq[int]` of its content code points | content code point ↔ `line[k]`; `str` slice `line[n:]` (the trim body) ↔ `PSeq.drop(n)` on the content (the newline-special-case is absorbed by the implicit separator — see §3) |
| `''.join(lines)` (the assembled text `read()` returns) | render of the model block: `''.join(c + '\n' for c in m)` | the rendered model block equals the real `''.join(lines)` exactly (G-AX) |
| the trim width `dedent` (`int`) | `n: int` | identical |

`str` indexing/iteration is banned in Nagini, so each line's content is carried
as `PSeq[int]`; the assembled block is `PSeq[PSeq[int]]`.

### 2.1 Why the model domain is `n >= 0` and TOTAL in the author lines

The model domain is the FULL domain of the modelled behaviour: any non-negative
trim width, and any leading/trailing author line including the empty one. Nothing
is required of `lead`/`trail` at all.

The author-line presence rule is part of the behaviour, not a domain restriction,
so it is modelled rather than assumed. The real author filters emit a line only
when the option is truthy (`if prepend:` at `sphinx/directives/code.py:343`,
`if append:` at `:350`); an empty option string is falsy and contributes no line.
The `@Pure` helper `emit` carries exactly that rule: a one-line block holding the
line verbatim when it has content, and no line at all when it is empty. So the
empty author line is IN-domain and denotes "the option was not supplied", which
is the state the model must be able to talk about.

That totality is load-bearing, not cosmetic. The trim stage runs on the presence
of the trim option ALONE (`if 'dedent' in self.options:` at `:357`) and is
independent of the two author filters, so the included text is trimmed whether or
not an author line is supplied. If the domain excluded the absent-author-line
states, every one of them would be unreachable inside the body and the spec would
say nothing about whether the trim runs there — an implementation could make the
whole trim stage contingent on an author line being present and still satisfy
every postcondition. The postcondition
`len(lead) == 0 and len(trail) == 0 -> Result() == trim_block(included, n)`, the
`len(lead) == 0` branch of the per-included-line clause, and the length clause
in terms of `emit` are what pin that; they are only meaningful because those
states are admissible. `properties.py`'s `pos-live-no-author-line` and
`pos-live-zero-width` are the liveness controls proving they are reachable.

Zero width is in-domain for the same reason: a trim width of 0 is the identity on
every line, so it is ordinary behaviour of the modelled operation rather than a
degenerate case, and leaving it out would leave it unconstrained.

The discriminating behaviour the gold change fixes (the leading/trailing lines
are NOT trimmed) is observable in the sub-regime where an author line is present
and the width is positive, so that trimming the line WOULD change it: the clauses
`len(lead) >= 1 -> Result()[0] == lead` and
`len(lead) >= 1 and n >= 1 -> Result()[0] != lead.drop(n)` are stated there. That
is the F2P test's regime (`dedent: 2`, `prepend: 'class Foo:'`,
`append: '# comment'`). It is a sub-regime of the domain, not the whole of it.

### 2.2 Total-correctness obligation

`assemble` carries `Requires(MustTerminate(2))`: the real pipeline is one
bounded pass over finitely many lines and always returns its assembled text to
the caller. Nagini's default semantics is partial correctness, so without this
obligation a diverging body (e.g. an endless loop before the return) would
satisfy every postcondition vacuously while never delivering the block; the
obligation makes such an implementation unverifiable. The impl loops discharge
it with strictly decreasing, bounded-below measures (`i`, `len(included) - j`),
and the proof lemma `trim_block_at` is `@Pure` (specification-level, consuming
no obligation).

## 3. Callee provenance (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `trim_block` deep model ↔ `dedent_lines` (A-reference)
**Callee:** `sphinx.directives.code.dedent_lines(lines, dedent, location)`
(`sphinx/directives/code.py:51`), applied per line by `dedent_filter`. The
per-line trim is modelled **deeply** by the `@Pure` front-recursive fold
`trim_block` (each line `content.drop(n)`, with the per-element lemma
`trim_block_at`); there is **no consumed `@ContractOnly` axiom**. The deep model
is validated equal to the real callee out-of-band by axiom_check.py (G-AX).
Source at base_commit (`dedent` is a concrete non-`None` `int` here — the only
path the F2P exercises):

```python
def dedent_lines(lines, dedent, location=None):
    if dedent is None:
        return textwrap.dedent(''.join(lines)).splitlines(True)
    if any(s[:dedent].strip() for s in lines):
        logger.warning(__('non-whitespace stripped by dedent'), location=location)
    new_lines = []
    for line in lines:
        new_line = line[dedent:]
        if line.endswith('\n') and not new_line:
            new_line = '\n'  # keep CRLF
        new_lines.append(new_line)
    return new_lines
```

Under the line-content abstraction (§2), a repo line is `content + '\n'`. The
real per-line result is `(content + '\n')[dedent:]`, with the special case
restoring `'\n'` when that slice is empty and the line ended in `'\n'`. Rendering
the deep model's per-line trim `content.drop(n)` back to repo reality is
`content[n:] + '\n'`. These are **equal for every content and every `n >= 0`**:
the trailing `'\n'` is exactly the implicit separator the abstraction factors
out, so the real callee's `line[dedent:]`-plus-newline-special-case reduces to
`content[n:] + '\n'`. axiom_check.py asserts this on 20 boundary lines (incl. the
empty line, the over-long trim, the non-whitespace-stripped edge) + 200000 fuzz
lines, 0 mismatches. The `logger.warning` side effect is observationally
irrelevant to the assembled text and is not modeled. Docs:
https://www.sphinx-doc.org/en/master/usage/restructuredtext/directives.html#directive-literalinclude
(the `dedent` option).

### 3.2 End-to-end refinement check (the gold reordering)
axiom_check.py additionally drives the REAL filter methods
(`dedent_filter`, `prepend_filter`, `append_filter`) in the gold (post-fix)
order and the full `LiteralIncludeReader.read()` over a temp include file, and
asserts the assembled text equals the model `assemble` semantics:

  `''.join(c + '\n' for c in ([lead] + [content[n:] for content in included] + [trail]))`

i.e. the leading and trailing author lines are emitted VERBATIM (their
indentation preserved) while the included lines are trimmed. This is checked on
the issue scenario (the F2P `lines 9-11`, `dedent 2`, prepend a class header,
append a comment — and the bug-report XML snippet with a pre-indented opening
tag) + 6 boundary + 3000 fuzz blocks. Against the PRE-patch pipeline ordering
this `read()` check fails (it observes the trimmed `ass Foo:` / `comment`),
confirming the check senses the fix. Exit 0 iff sound. Imports only the REAL
`sphinx.directives.code` (the module the gold patch edits) + stdlib; the include
file is a temp file we control.

## G-CONF (differential conformance)

**Script:** `conformance_check.py`. **Pinned fuzz seed: `10323`** (module constant
`SEED`). Inputs: **39 boundary + 100000 fuzz = 100039**, every one satisfying
model.py's `Requires` (`n >= 0`; nothing is required of the author lines, so all
four author-line presence combinations and `n == 0` are generated).

**Shadow.** The `# impl-start`/`# impl-end` region of `model.py` copied verbatim
with only the contract calls (`Requires`, `Ensures`, `Invariant`, `Assert`,
`MustTerminate`) and the `# invariants-start`/`-end` markers deleted — both
`while` loops, the backward fold building `trimmed`, and the
`(emit(lead) + trimmed) + emit(trail)` concatenation are unchanged. The `@Pure`
helpers `trim_block` (§3.1's deep model) and `emit` (the author-line presence
rule) are copied over likewise; `trim_block` is also used as an auxiliary
cross-check that the fold computes it, and `emit` is EXECUTED, so the presence
rule is differentially checked against the real guarded author filters rather
than assumed. `trim_block_at` is a proof lemma with no computation. `PSeq` is an
immutable tuple shim providing exactly `take`/`drop`/`+`/`len`/`[]`/`==`. There is
no `@ContractOnly` axiom in this bundle, so no callee is assumed — everything the
shadow does is executed.

**Oracle.** The REAL patched `LiteralIncludeReader.read()` (§1,
`sphinx/directives/code.py:219`), **called, not transliterated**: the gate applies
`patch.diff` to /testbed and `PYTHONPATH=/testbed` imports the patched module, so
the post-fix filter order (`dedent_filter` before `prepend_filter`/
`append_filter`) runs for real, as do the unchanged callees `read_file`,
`dedent_lines`, `prepend_filter`, `append_filter`. Driving `read()` needs only an
include file plus an options dict, both buildable in-container.

**Type bridge (§2, inverted).** `to_line(s) = PSeq(*map(ord, s))` and
`from_line(p) = ''.join(map(chr, p))` carry a repo line's CONTENT to/from
`PSeq[int]`; `render(block) = ''.join(from_line(c) + '\n' for c in block)`
re-adds the implicit `'\n'` separator, yielding exactly the `''.join(lines)`
string `read()` returns. An ABSENT author line is the EMPTY option string on the
concrete side — which is precisely what makes the real guarded filters emit no
line — and the empty `PSeq[int]` on the model side, which is what `emit` maps to
the empty contribution. Generation is on the concrete side (`str` lines, `str`
lead/trail, `int n`) so every input lands in `Requires` by construction; the
included block is written to a temp include file that `read_file`'s
`splitlines(True)` recovers line-for-line, so the generator alphabet excludes
every `str.splitlines` boundary character (a harness precondition, not a model
restriction).

**Coverage.** Boundary cases pin the F2P shape (fixture lines 9-11, `dedent: 2`,
`prepend: 'class Foo:'`, `append: '# comment'`), the bug report's pre-indented
XML opening tag, the empty block (neither loop taken) and the singleton block
(each loop taken once), pure-indentation author lines, exact-width and over-long
trims, the empty-line/newline special case, the dedent-warning path, tabs and
non-ASCII — and then the AUTHOR-LINE-ABSENT shapes: the dedent-only blocks with
NEITHER author line (at several trim widths, including the shapes the repo's own
dedent-only tests read), lead-only, trail-only, and the empty block with no
author line; plus the zero-width trim with and without author lines. Fuzz draws
each author line absent a quarter of the time and `n` from 0 upward, so all four
presence combinations and the identity width are covered in bulk as well.

**Sensing the fix.** Against the PRE-patch filter ordering the check FAILS on the
first boundary case (oracle reports the trimmed `'ass Foo:\n…comment\n'` vs the
shadow's verbatim `'class Foo:\n…# comment\n'`), so a green verdict is evidence
about the reordering rather than a vacuous pass.

**Verdict:** exit 0, `checked=100024 disagreements=0` — G-CONF=pass.
