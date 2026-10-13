# mapping.md — sphinx-doc__sphinx-10435

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = f1061c012e214f16fd8790dec3c283d787e3daa8`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one axiomatized (unchanged) callee.

Repo file under change: `sphinx/writers/latex.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `wrapInlineCode (snippet : List Char)` | `LaTeXTranslator.visit_literal(self, node)` — `sphinx/writers/latex.py:1695`; the changed body lines `1710–1717` | the modeled changed function (the inline-code highlighting branch) |
| `renderedInline` *(opaque body of the frame axiom — A-consumed)* | `self.highlighter.highlight_block(node.astext(), lang, opts=opts, location=node)` — call at `sphinx/writers/latex.py:1707`; impl `PygmentsBridge.highlight_block`, `sphinx/highlighting.py:136` | unchanged callee whose output the branch post-processes; the spec pins only its structural FRAME, not the body content |
| `beginTok` | the literal `r'\begin{Verbatim}[commandchars=\\\{\}]'` — the begin control sequence pygments' LaTeX formatter emits; matched by `.replace` at `latex.py:1712` (37 code points) | constant prefix the substitution replaces |
| `endTok` | the literal `r'\end{Verbatim}'` — the end control sequence; the count `[:-14]`/`[:-15]` at `latex.py:1714` strips it (14 code points) | constant suffix dropped by the trailer surgery |
| `codeOpen` | the literal `r'\sphinxcode{\sphinxupquote{'` — the inline-code macro opening substituted in at `latex.py:1712` (27 code points) | constant opening of the wrapping macro |
| `openTok` = `codeOpen ++ ['%']` | the gold's replacement string `r'\sphinxcode{\sphinxupquote{%'` (`latex.py:1712`, the added `%`) | the opening AS substituted by the fix |
| `rstrip` | Python `str.rstrip()` (`latex.py:1714`) | model of the standard right-strip (drop trailing whitespace) |
| `wrapped` *(pure spec target)* | the desired post-fix markup `r'\sphinxcode{\sphinxupquote{%' + '\n' + body + '%' + '\n' + '}}'` | the exact byte sequence the patched branch appends to `self.body` |

`CR` (`sphinx/writers/latex.py:53`) is the module constant `'\n'`; the gold's
`'%' + CR + '}}'` is modeled as `['%', '\n', '}', '}']`.

The pre-patch behavior the change replaces (refinement audit only, not in the
consumer spec view): the opening was substituted WITHOUT the trailing `%`
(`r'\sphinxcode{\sphinxupquote{'`), only `\end{Verbatim}` (14 chars, not the
preceding newline) was dropped (`[:-14]`), and the appended trailer was the bare
`'}}'`. Those three together left the highlighter's surrounding line breaks
intact, rendering as a spurious leading/trailing space — the bug.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `str` (the highlighter output `hlcode`, and what the branch appends to `self.body`) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat / `body.append` accumulation ↔ `List` `++`; `s[:k]` ↔ `l.take k`; `s.replace(prefix, r)` (prefix-only occurrence) ↔ `r ++ l.drop prefix.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact. `'\n'` ↔ `'\n'`, `'%'` ↔ `'%'`, `'}'` ↔ `'}'`. |
| `node.astext()` (the inline snippet source) | `snippet : List Char` | the read-only source text the branch renders; observationally the `str` of code points (mapping §2 row 1). Read-only ⇒ not `mut` (directive 5). |
| `self.body.append(a); self.body.append(b)` then `"".join(self.body)` | `... ++ a ++ b` | the writer concatenates appended fragments; the modeled return value is the concatenation of the two appends the branch performs. |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is a per-code-point slice/concat.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `renderedInline` + the structural frame ↔ `highlight_block` (A-consumed)
**Callee:** `PygmentsBridge('latex').highlight_block(source, lang)`
(`sphinx/highlighting.py:136`). This callee is **unchanged** by the patch — the
fix only post-processes its output. The spec axiomatizes it with the WEAKEST
contract the trailer arithmetic needs (directive 7): its output is

```
BEGIN + '\n' + body + '\n' + END + '\n'
```

i.e. a constant prefix `BEGIN` (length 37), a newline, an unconstrained `body`,
a newline, the constant `END` (length 14), and a final newline. This frame is
encoded directly in the `:|` stub's predicate
(`hlcode = beginTok ++ ['\n'] ++ renderedInline snippet ++ ['\n'] ++ endTok ++ ['\n']`);
the proof consumes exactly this frame to discharge the slicing (`compute`).
`renderedInline` (the body) is intentionally **unconstrained** — the spec pins
nothing about its content, only the surrounding frame, which is what the trailer
surgery depends on. There is NO deep model of the body, hence no A-reference.

The three slicing facts the proof relies on, all entailed by the frame:
- the begin sequence is a length-37 prefix, so `hlcode.drop 37` removes exactly
  `BEGIN`, leaving `'\n' + body + '\n' + END + '\n'`;
- `rstrip` removes exactly the single trailing newline;
- the rstripped tail's last 15 code points are `'\n' + END`, so `[:-15]` drops
  the newline-before-END plus END together.

**Flag dependency:** `highlight_block`'s LaTeX `Verbatim` envelope is emitted by
the `latex` formatter (the `PygmentsBridge('latex')` the writer constructs); G-AX
fuzzes that configuration across several lexer languages.

**Soundness check (G-AX):** `axiom_check.py` runs the real
`PygmentsBridge('latex').highlight_block` (the same call the writer makes) on
boundary snippets across `python python3 text bash html rst` plus 20 000
randomized fuzz strings, asserting on every observation that the output equals
`BEGIN + '\n' + body + '\n' + END + '\n'`, that `len(BEGIN)==37`,
`len(END)==14`, that `rstrip` removes exactly one char, and that the three
slicing facts hold. Could-not-lex snippets are skipped (sphinx warns and falls
back, outside the modeled branch's precondition). Imports only `sphinx`
(present in the instance image). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10435`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the trailer surgery (the `.replace`/`rstrip`/`[:-15]`/append ops) to Python and
leaves the highlighter call as the **real** `highlight_block` callee (A-tagged →
run real callee, not the frame axiom), identical to the oracle's source, so any
disagreement is a pure R/I-fidelity counterexample. The oracle drives the patched
`LaTeXTranslator.visit_literal` on a `literal` node carrying a `code`+language
class so the highlighting branch runs.
