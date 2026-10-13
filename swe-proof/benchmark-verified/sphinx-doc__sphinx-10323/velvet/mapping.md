# mapping.md — sphinx-doc__sphinx-10323

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 31eba1a76dd485dc633cae48227b46879eda5df4`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each deep-model reference.

Repo file under change: `sphinx/directives/code.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assembleBlock (body, prefixText, suffixText, indent)` | the body of `LiteralIncludeReader.read` that composes the post-file-selection line filters — `sphinx/directives/code.py:219-231` (the `filters = [...]` list + the `for func in filters` application loop) | the modeled changed function: the ordered composition of the boundary-affecting filters applied to the already-selected lines |
| `removeIndent (n, lines)` *(deep model — A-reference)* | `LiteralIncludeReader.dedent_filter` → `dedent_lines(lines, dedent)` — `code.py:357-361`, `code.py:51-64` | pure spec: per-line removal of `n` leading characters from a block of lines |
| `addPrefix (prefixText, lines)` *(deep model — A-reference)* | `LiteralIncludeReader.prepend_filter` — `code.py:343-348` | pure spec: insert one supplied line (with `'\n'`) at the front |
| `addSuffix (suffixText, lines)` *(deep model — A-reference)* | `LiteralIncludeReader.append_filter` — `code.py:350-355` | pure spec: append one supplied line (with `'\n'`) at the end |
| `joinLines (lines)` | `''.join(lines)` — `code.py:233` (`return ''.join(lines), len(lines)`) | pure spec: concatenate the assembled lines into one sequence |

The earlier filters in the real `filters` list — `pyobject_filter`, `start_filter`,
`end_filter`, `lines_filter` (`code.py:219-222`) — select WHICH source lines form
the body. They are upstream of and unchanged by the patch (the patch reorders only
the last three entries: `dedent` / `prepend` / `append`), so they are abstracted
into the modeled function's input `body` (the already-selected lines). This is an
R refinement: `body` is whatever those selection filters produced. The patch does
not touch them, so the modeled domain ranges `body` over arbitrary line lists.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a list of source lines `List[str]`, each line keeping its own trailing `'\n'` (the result of `str.splitlines(True)`, `code.py:208`) | `List (List Char)` | `[s0, s1, …]` ↔ `[s0.toList, s1.toList, …]`; `len(lines)` ↔ `lines.length`; per-line `str` ↔ `List Char` |
| a single line `str` `line` | `List Char` | `line` ↔ `line.toList`; `line[n:]` ↔ `line.drop n`; `len(line)` ↔ `line.length` |
| the `dedent` option: `optional_int` (`code.py:376`), present-or-absent in `self.options` | `indent : Option Nat` | `'dedent' not in options` ↔ `none`; `options['dedent'] == k` ↔ `some k`. (The real `dedent_lines` also accepts `dedent=None` meaning "auto textwrap.dedent"; that path is excluded from the modeled domain — see §3.1.) |
| the `prepend` option `str` (`directives.unchanged_required`, `code.py:390`), or absent | `prefixText : List Char` | absent / not set ↔ `[]` (empty); `options['prepend'] == p` (a non-empty str) ↔ `p.toList`. `unchanged_required` forbids an empty value, so the only "no prepend" case is absence ↔ `[]`. |
| the `append` option `str` (`code.py:391`), or absent | `suffixText : List Char` | absent ↔ `[]`; `options['append'] == a` ↔ `a.toList` |
| `''.join(lines)` (`code.py:233`) | `joinLines` | `str` concat ↔ `List` `++`; empty join ↔ `[]` |

Lean `String`/`List Char` indexing is total and sound (no `List[int]` workaround
needed); the carrier is `List (List Char)` because the operation is per-line over a
block of lines.

## 3. Callee provenance (deep-model A-references — checked by G-AX / axiom_check.py)

The three boundary filters are unchanged library routines (their bodies are NOT
edited by the patch; only their ORDER in the `filters` list changes). Each is
modeled DEEPLY in the `pure` region and validated equal to the real routine by
`axiom_check.py` (G-AX). There are **no consumed axioms**.

### 3.1 `removeIndent` deep model ↔ `dedent_filter` / `dedent_lines` (A-reference)
**Callee:** `LiteralIncludeReader.dedent_filter` (`code.py:357-361`), which calls
the module function `dedent_lines(lines, dedent, location)` (`code.py:51-64`) when
`'dedent' in self.options`. Source at base_commit:

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

For an integer `dedent = k` this is exactly the per-line map `line ↦ line[k:]` with
the one special case "an emptied line that originally ended in `'\n'` keeps a lone
`'\n'`" — which `removeIndentLine` encodes (`line.drop k`, then `if dropped.isEmpty
&& line.getLast? == some '\n' then ['\n']`). The non-whitespace `logger.warning`
is a diagnostic side effect that does not change the returned lines, so it is
observationally invisible to the modeled output and to the F2P test (which reads
`content`); it is omitted from the model.

**Modeled domain.** `indent = some k` corresponds to an integer `:dedent:` value
(the `optional_int` case actually exercised by `:dedent: N`); `indent = none`
corresponds to no `:dedent:` option, where `dedent_filter` returns the lines
untouched (`else: return lines`, `code.py:360-361`). The `dedent_lines(dedent=None)`
"auto `textwrap.dedent`" branch is reachable only via the directive default, which
the directive layer never passes through `dedent_filter` (the filter is a no-op
unless `'dedent' in self.options`); it is outside the modeled domain and not
claimed. G-AX fuzzes only the integer / absent cases.

### 3.2 `addPrefix` deep model ↔ `prepend_filter` (A-reference)
**Callee:** `LiteralIncludeReader.prepend_filter` (`code.py:343-348`):

```python
def prepend_filter(self, lines, location=None):
    prepend = self.options.get('prepend')
    if prepend:
        lines.insert(0, prepend + '\n')
    return lines
```

`prepend` truthy (a non-empty str, guaranteed by `unchanged_required`) inserts
`prepend + '\n'` at index 0; absent/empty leaves the lines unchanged. This is
exactly `addPrefix`: `if prefixText.isEmpty then lines else (prefixText ++ ['\n']) :: lines`.

### 3.3 `addSuffix` deep model ↔ `append_filter` (A-reference)
**Callee:** `LiteralIncludeReader.append_filter` (`code.py:350-355`):

```python
def append_filter(self, lines, location=None):
    append = self.options.get('append')
    if append:
        lines.append(append + '\n')
    return lines
```

`append` truthy appends `append + '\n'` at the end; absent/empty is a no-op.
Exactly `addSuffix`: `if suffixText.isEmpty then lines else lines ++ [suffixText ++ ['\n']]`.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`sphinx.directives.code` (`dedent_lines`, and the bound `prepend_filter` /
`append_filter` via a `LiteralIncludeReader` instance) and runs them on boundary
inputs (empty body, blank lines, lines shorter than the dedent, with/without
prepend/append) plus randomized fuzz, asserting each deep model equals the real
routine. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10323`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates the
`removeIndent`/`addPrefix`/`addSuffix`/`joinLines` ops (all R/I — no A-tagged
callee in the impl computation) to Python and diffs the assembled output against
the real patched `LiteralIncludeReader.read()` over fuzzed
(body, prepend, append, dedent) option configurations.
