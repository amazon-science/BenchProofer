# mapping.md — sphinx-doc__sphinx-11510

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6cb783c0024a873722952a67ebb9f41771c8eb6d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance and flag dependencies.

Repo file under change: `sphinx/directives/other.py` (the `Include.run` method).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assembleInsertedLines (transform) (lines)` | the nested `_insert_input(include_lines, path)` closure added inside `Include.run` — `sphinx/directives/other.py:371` (post-patch body) | the modeled changed behavior: the line sequence handed to the line inserter for spliced-in external content |
| `transform : List Char → List Char` | the consumer-registered `source-read` text handler, invoked via `self.env.app.events.emit("source-read", docname, arg)` where `arg = [text]` and the handler may rewrite `arg[0]` | the ARBITRARY consumer transform; a universally-quantified parameter (no axiom) |
| `lines : List (List Char)` | the `include_lines` argument (a docutils `StringList`/list of source lines) | the lines the line reader produced for the included file, including its two trailing structural marker lines |
| `splitLines (s : List Char)` | `str.splitlines()` (CPython) applied to the transformed text — `text.splitlines()` post-patch | pure spec: split text into lines at every CPython line boundary (full model, §3.1) |
| `List.intercalate ['\n'] content` | `"\n".join(include_lines[:-2])` post-patch | pure spec: re-join content lines with the newline separator |
| `lines.dropLast.dropLast` | `include_lines[:-2]` post-patch | the content lines (all but the two trailing markers) |
| `lines.drop (lines.length - 2)` | `include_lines[-2:]` post-patch | the two preserved trailing marker lines |

Out-of-frame (unchanged) repo machinery the patch wires but does NOT change in
behavior on the produced lines, hence not modeled: the docutils
`StateMachine.insert_input` class method that finally consumes the assembled
lines (`return StateMachine.insert_input(self.state_machine, include_lines,
path)`); the `self.env.path2doc(os_path(path))` docname computation (only feeds
the event's docname argument, not the line content); and the
`if self.env.app.events.listeners.get('source-read')` install guard (when there
is no listener the identity transform is the relevant `transform` and the
content is unchanged — a special case of the universally-quantified spec).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the repo's Python types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a source line (`str`) | `List Char` | `s` (Python str) ↔ `s`-shaped `List Char`; per-code-point, total/sound |
| a list of source lines (`include_lines`, a `StringList`/`list[str]`) | `List (List Char)` | element-wise the line bijection; `len` ↔ `.length`; `lines[:-2]` ↔ `lines.dropLast.dropLast`; `lines[-2:]` ↔ `lines.drop (lines.length - 2)` |
| `"\n".join(parts)` | `List.intercalate ['\n'] parts` | newline-separated concatenation; exact on every input |
| `text.splitlines()` | `splitLines text.toList` | see §3.1 — the full CPython line-boundary model, exact on every input |
| the registered `source-read` handler (`arg=[text]; emit; text=arg[0]`) | `transform : List Char → List Char` | `transform` is the net effect on the text: `text ↦ arg[0]` after the handler chain runs; an arbitrary total function, faithful because the spec assumes nothing about it |

## 3. Provenance of pure models

### 3.1 `splitLines` ↔ `str.splitlines()` (full model)
CPython `str.splitlines()` splits on the full set of line boundaries (`\n`,
`\v`/`\x0b`, `\f`/`\x0c`, `\r`, `\r\n` as a SINGLE boundary, `\x1c`,
`\x1d`, `\x1e`, `\x85`, ` `, ` `), and a terminating boundary
produces no trailing empty field. `splitLines` models this behavior in full:
`isLineBreak` enumerates exactly the CPython boundary set, `splitLinesAux`
treats `'\r' :: '\n'` as one boundary, and the end-of-input case emits no
empty trailing line. The full model is REQUIRED for faithfulness (not merely
nice-to-have): `splitLines` is applied to `transform`'s OUTPUT, and
`transform` is universally quantified — a consumer `source-read` handler may
emit any character (e.g. rewrite `\n` to `\r`), and the real post-patch code
then splits at that `\r`. An `\n`-only model diverges there (the prior
bundle's G-PANEL-2 counterexample: `tr = lambda t: t.replace('\n','\r')` on
`["a","b",M1,M2]` — real `'a\rb'.splitlines() = ['a','b']`, while the
`\n`-only model kept `'a\rb'` whole).

`splitLines` reference values (verified against CPython `str.splitlines()`;
the Python shadow `split_lines` in `conformance_check.py` is additionally
fuzz-exercised by G-CONF over the full boundary alphabet, including
boundary-injecting transforms):
`"" ↦ []`, `"a" ↦ ["a"]`, `"a\nb" ↦ ["a","b"]`, `"a\nb\n" ↦ ["a","b"]`,
`"\n" ↦ [""]`, `"a\n\n" ↦ ["a",""]`, `"a\r\nb" ↦ ["a","b"]`,
`"a\rb" ↦ ["a","b"]`, `"a\r" ↦ ["a"]`, `"\r\n" ↦ [""]`,
`"a\n\rb" ↦ ["a","","b"]`, `"a\x0bb\x0cc" ↦ ["a","b","c"]`,
`"a\x85b" ↦ ["a","b"]`, `"a b c" ↦ ["a","b","c"]`.

### 3.2 `transform` — the consumer handler (no axiom)
The `source-read` handler is supplied by an arbitrary consumer extension; the
fix's correctness is that the inserted content is offered to it AT ALL (and the
markers are preserved). The spec therefore quantifies over every
`transform : List Char → List Char` and assumes nothing — there is no axiom and
no consumed callee. G-AX is consequently a no-op for this bundle (no axioms);
`meta.json gates.G-AX.status = "skip"`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11510`** so the
consumer-side verdict is reproducible. The shadow transliterates
`splitLines`, `intercalate`, and the slice ops (all R/I) to Python and uses a
fuzzed-but-fixed family of `transform` callbacks (identity, constant, prefixers,
the issue's `&REPLACE_ME; → REPLACED` and `#magical → amazing` substitutions,
plus boundary-injecting handlers that emit `\r`, `\r\n`, `\v`, `\f`, `\x1c`,
`\x1d`, `\x1e`, `\x85`, and the U+2028/U+2029 separators); inputs range over
the full line-boundary alphabet (§3.1) so the `splitLines` leg is exercised on
every CPython boundary, not just `\n`.
