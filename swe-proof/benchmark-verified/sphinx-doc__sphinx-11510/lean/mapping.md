# mapping.md — sphinx-doc__sphinx-11510

## Symbol binding (file:line @ base_commit 6cb783c0024a873722952a67ebb9f41771c8eb6d)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_includedSource` / `problem_spec_includedSource` | the inserted `_insert_input(include_lines, path)` closure installed by `Include.run` (the behaviour the patch adds) | `sphinx/directives/other.py:371-403` (post-patch) / `Include.run` at `sphinx/directives/other.py:371-379` (base_commit) |
| `hasListeners` | `bool(self.env.app.events.listeners.get('source-read'))` — whether a `source-read` listener is registered | `other.py:404` (post-patch guard) |
| `srcRead` | the net text-level effect of the registered `source-read` listeners: `arg=[text]; events.emit("source-read", docname, arg); text = arg[0]` | `other.py:387-389` (post-patch) |
| `pathToDocname` (opaque carrier) | `self.env.path2doc(os_path(path))` — derive the docname from the include path | `other.py:385` (post-patch) |
| `lines` | the `include_lines` argument handed to `insert_input` | docutils `StateMachine.insert_input(self, input_lines, source)` |
| `joinLines` | `"\n".join(include_lines[:-2])` | `other.py:382` |
| `splitLines` (full `str.splitlines()` semantics: all universal line boundaries, CRLF as one) | `text.splitlines()` | `other.py:392` |
| the trailing two marker lines | `include_lines[-2:]` (the docutils ≥0.18 end markers) | `other.py:382,392` |
| `InsertOutcome.emitted` | the `(docname, text)` payload passed to `events.emit("source-read", …)` | `other.py:388` |
| `InsertOutcome.outputLines` | the `include_lines` finally forwarded to `StateMachine.insert_input(self.state_machine, …)` | `other.py:392,398` |

The modeled behaviour is the new `_insert_input` interception that the patch
installs on `self.state_machine.insert_input` inside `Include.run`. This is the
only behaviour the patch changes and the only behaviour the FAIL_TO_PASS tests
observe.

### What the patch does (post-patch `Include.run`)

```python
def run(self) -> list[Node]:
    def _insert_input(include_lines, path):
        # combine the lines (minus the 2 trailing markers) into text
        text = "\n".join(include_lines[:-2])
        docname = self.env.path2doc(os_path(path))
        arg = [text]
        self.env.app.events.emit("source-read", docname, arg)   # offer to hook
        text = arg[0]
        include_lines = text.splitlines() + include_lines[-2:]   # re-split, re-attach markers
        return StateMachine.insert_input(self.state_machine, include_lines, path)

    if self.env.app.events.listeners.get('source-read'):
        self.state_machine.insert_input = _insert_input   # only if a listener exists
    ...                                                    # (unchanged path processing below)
```

Step by step (the modeled `_insert_input` body, guarded by the listener check):
1. `text = "\n".join(include_lines[:-2])` — drop the trailing two marker lines,
   join the rest into a single block of text (`joinLines (lines.take (n-2))`).
2. `docname = path2doc(os_path(path))` — derive the docname tag (`pathToDocname
   path`).
3. emit `source-read` with `arg=[text]`; the listeners may rewrite `arg[0]`
   (`srcRead text`). The emitted payload is `(docname, text)`.
4. `include_lines = text.splitlines() + include_lines[-2:]` — re-split the
   rewritten text and re-append the two marker lines
   (`splitLines (srcRead body) ++ markers`).
5. forward to the parent `StateMachine.insert_input` — i.e. this line list is
   what gets parsed (`outputLines`).

The guard at `other.py:404` means the interception is installed **only when a
`source-read` listener is registered**; otherwise the original docutils
`insert_input` runs unchanged (the included lines are parsed verbatim and no
event is emitted) — this is `hasListeners = false`, and is exactly the base_commit
behaviour for ALL inputs.

### Lean modeling

- `lines : List String` is the `include_lines` argument. docutils ≥0.18 appends
  two end-marker lines; `lines.take (n-2)` is the content body and `lines.drop
  (n-2)` is the markers (`lines[-2:]`). For `n < 2` Lean's `Nat` subtraction
  saturates to `0`, so `take 0 = []` and `drop 0 = lines` — the body is empty and
  every line is treated as a marker; the same boundary the real `[:-2]` / `[-2:]`
  slices produce when fewer than two lines are present (G-CONF fuzzes this).
- `joinLines = String.intercalate "\n"` is `"\n".join(...)`.
- `splitLines` models `str.splitlines()` in FULL: it cuts at every universal
  line boundary Python recognises — `\n`, `\r`, `\r\n` (as ONE boundary), `\v`
  (`\x0b`), `\f` (`\x0c`), `\x1c`, `\x1d`, `\x1e`, `\x85` (NEL), ` ` (LINE
  SEPARATOR), ` ` (PARAGRAPH SEPARATOR). The empty string yields `[]`, and
  a trailing boundary is not turned into a spurious final empty element
  (`"a\n".splitlines() == ["a"]`, `"a\r\n".splitlines() == ["a"]`). This matters
  because the split is applied to the LISTENER's rewritten output (`arg[0]`
  after `events.emit`), which is an arbitrary string the spec quantifies over —
  a listener may emit `\r`/`\r\n`/etc., and the real `text.splitlines()` breaks
  on all of them. The Lean `splitLinesGo` is differentially fuzzed against the
  real `str.splitlines()` in `conformance_check.py` (60k boundary-rich strings
  plus edge cases).
- `srcRead : String → String` is the *net* effect of the `source-read` listeners
  on the body text — the `arg[0]` value after `events.emit`. Modeling the
  listeners' transformation as an arbitrary `String → String` is faithful: the
  patch makes no assumption about what listeners do, only that they are offered
  the text and that their output is what gets parsed. The F2P
  `test_include_source_read_event_nested_includes` registers a listener that does
  `source[0].replace("#magical","amazing")`; the F2P `test_include_source_read_event`
  registers one that records sources (identity on `arg[0]`).
- `pathToDocname : String → String` (`opaque`) is `path2doc(os_path(path))`, an
  unchanged path-normalising callee. The proof consumes **no** property of it
  (the docname only flows into the emitted payload as an opaque tag), so it is a
  bare `opaque` carrier with no `_prop` axiom — see refinement.md.
- `hasListeners : Bool` is the truth value of the listener-registration guard.
- `InsertOutcome` captures the two downstream-observable effects: what was offered
  to the hook (`emitted`) and what line list is parsed (`outputLines`). Both
  components are pinned by the spec (frame discipline, SPEC_GUIDE §0.5).

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `include_lines : list[str]` | `lines : List String` | element-wise string identity; list order preserved. |
| `bool(events.listeners.get('source-read'))` | `hasListeners : Bool` | listener registered ↔ `true`. |
| `arg[0]` after `events.emit("source-read", …)` (net listener effect on the body) | `srcRead : String → String` | the function from offered body text to rewritten body text. |
| `path2doc(os_path(path))` | `pathToDocname path` | path ↦ docname (opaque; equality only). |
| `"\n".join(xs)` | `joinLines xs` | identical join. |
| `text.splitlines()` | `splitLines text` | identical line split on all universal line boundaries (CRLF = one boundary; no trailing empty line); differentially fuzzed in conformance_check.py. |
| `include_lines[:-2]` | `lines.take (lines.length - 2)` | content body. |
| `include_lines[-2:]` | `lines.drop (lines.length - 2)` | trailing marker lines. |
| `(docname, text)` emitted payload | `InsertOutcome.emitted` (`Option (String × String)`) | `some (docname, body)` when listener present, else `none`. |
| `include_lines` forwarded to `insert_input` | `InsertOutcome.outputLines` | the parsed line list. |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The patch's behaviour — joining
  lines minus the markers, emitting the event, re-splitting and re-attaching the
  markers, gated on a listener being present — is modeled DEEPLY by `joinLines`,
  `splitLines`, and the structural `take`/`drop` over the marker boundary
  (SPEC_GUIDE §3: a deeply-modeled changed op is never axiomatized). The proof
  consumes no external property, so the `axioms` region declares only the opaque
  `pathToDocname` carrier (needed so the docname tag can appear in the executable
  impl) and **no `_prop` axiom**. **G-AX skips** (no consumed axiom, no
  A-reference). `pathToDocname` enters only as an opaque tag in `emitted`; the
  spec pins `emitted` to `pathToDocname path`, so the impl cannot fill that
  component with anything else.
- `os_path` / `path2doc` (the docname derivation) is **unchanged** by the patch
  and does not bear on the source-read fix; it is folded into the opaque
  `pathToDocname`. Its omission constrains no free output component — `emitted` is
  pinned to `(pathToDocname path, body)`.
- `StateMachine.insert_input` (the parent docutils method the closure finally
  calls) is **unchanged**; it is the downstream consumer of `outputLines`, so its
  effect is exactly "the produced line list is parsed". We model its input
  (`outputLines`) rather than re-deriving its parse, which is orthogonal to the
  fix and identical pre/post-patch.
- **Flag dependency:** the interception is installed only when a `source-read`
  listener is registered (`events.listeners.get('source-read')` truthy). This is
  the `hasListeners` flag; G-CONF fuzzes both values. With no listener the
  behaviour is byte-identical to base_commit (the pre-patch bug), which is why the
  prepatch impl is the unconditional `hasListeners = false` branch.

## G-CONF fuzz seed

Pinned LCG seed: **11510** (see `conformance_check.py` `SEED`). Corpus:
randomized `include_lines` line lists (0–8 lines, each a short random string
possibly containing the replaced token, empty lines, and a trailing-newline-style
empty marker) crossed with `hasListeners ∈ {True, False}`, a family of
`srcRead` transforms (identity, token replace, prefix/suffix, uppercase, constant
empty, plus boundary-injecting rewrites: `\n→\r\n`, `\n→\r`, trailing `\r` /
`\r\n`, and an exotic-boundary zoo covering `\v \f \x1c \x1d \x1e \x85  
 `), and random `path` strings. The R/I shadow of
`implementation_includedSource` is diffed against an in-process replica of the
POST-PATCH `_insert_input` (joining `[:-2]`, emitting, the REAL
`str.splitlines()` + `[-2:]`, gated on the listener flag) over ≥1e5 fuzzed
inputs; additionally the Lean `splitLines` transliteration is diffed directly
against the real `str.splitlines()` over 60k boundary-rich random strings.
Hand-picked edge cases pin: fewer than two lines (`n=0,1,2`), the
nested-include F2P body (`["The #magical foo.", "", <m1>, <m2>]` with the
`#magical→amazing` replace), empty body after marker removal, the no-listener
pass-through, and the G-PANEL-2 counterexample (listener output containing a
bare `\r`).
