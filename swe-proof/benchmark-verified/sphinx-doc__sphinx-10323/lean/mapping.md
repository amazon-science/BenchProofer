# mapping.md — sphinx-doc__sphinx-10323

## Symbol binding (file:line @ base_commit 31eba1a76dd485dc633cae48227b46879eda5df4)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_assembleLines` / `problem_spec_assembleLines` / `correct_assembleLines` | the line-list assembly pipeline of `LiteralIncludeReader.read` (the ordered `filters` list applied by `for func in filters: lines = func(lines, …)`) | `sphinx/directives/code.py` `LiteralIncludeReader.read` (`code.py:219-234`) |
| `IncludeOptions` (pure helper) | the relevant entries of the reader's `options` dict | `code.py:189-195` (`self.options`) |
| `IncludeOptions.dedent` | `'dedent' in self.options` | `code.py:358` (`dedent_filter` guard) |
| `IncludeOptions.prepend` | `self.options.get('prepend')` | `code.py:344` |
| `IncludeOptions.append` | `self.options.get('append')` | `code.py:351` |
| `selectContent` (opaque callee) | the composition of the UNCHANGED leading selection passes applied first and in fixed relative order: `pyobject_filter ∘ start_filter ∘ end_filter ∘ lines_filter` | `code.py:243-283` (`pyobject_filter`, `start_filter`, `end_filter`, `lines_filter`) |
| `dedentCore` (opaque callee) | `dedent_lines` — removes a uniform amount of leading whitespace from each line (integer count, or `textwrap.dedent` when no count) | `code.py:51-65` (`dedent_lines`), invoked by `dedent_filter` `code.py:357-361` |
| `addPrepend` (pure helper) | `prepend_filter`: `lines.insert(0, prepend + '\n')` when `prepend` is TRUTHY (non-empty) — `if prepend:` guard, so a present-but-empty string inserts nothing | `code.py:343-348` |
| `addAppend` (pure helper) | `append_filter`: `lines.append(append + '\n')` when `append` is TRUTHY (non-empty) — `if append:` guard | `code.py:350-355` |

### What the patch changes (base_commit)

`LiteralIncludeReader.read` builds an ordered list of filter callables and folds
the file's line list through them:

```python
filters = [self.pyobject_filter,
           self.start_filter,
           self.end_filter,
           self.lines_filter,
           self.prepend_filter,     # <-- pre-patch: prepend/append BEFORE dedent
           self.append_filter,
           self.dedent_filter]      # <-- pre-patch: dedent applied LAST
lines = self.read_file(self.filename, location=location)
for func in filters:
    lines = func(lines, location=location)
```

Because `dedent_filter` ran **last**, the de-indentation pass also stripped
leading whitespace from the lines added by `prepend_filter` / `append_filter`.
So a `:prepend:`/`:append:` value whose own leading whitespace was meaningful
(or, with an integer `:dedent:`, any prepended/appended line) was mangled: its
first `dedent` characters were removed along with the file content's.

The gold patch reorders the list so `dedent_filter` runs **before**
`prepend_filter` / `append_filter`:

```python
filters = [self.pyobject_filter,
           self.start_filter,
           self.end_filter,
           self.lines_filter,
           self.dedent_filter,      # <-- post-patch: dedent the selected file content first
           self.prepend_filter,
           self.append_filter]      # <-- post-patch: then add prepend/append untouched
```

After the fix, de-indentation acts ONLY on the selected file content; the
prepended and appended lines are emitted with their text intact.

The leading selection passes (`pyobject_filter`, `start_filter`, `end_filter`,
`lines_filter`) keep their positions and relative order in both versions — only
`dedent_filter` moves relative to `prepend_filter`/`append_filter`. The model
therefore collapses that unchanged prefix into a single opaque `selectContent`
and represents the reordered tail explicitly.

### Lean modeling

- `IncludeOptions` records the three observables the changed tail reads: whether
  the de-indent pass is requested (`dedent`), the optional prepended line
  (`prepend`), and the optional appended line (`append`).
- `selectContent : List String → List String` is the UNCHANGED leading-selection
  composition. It is opaque so it appears IDENTICALLY in spec and impl (it runs
  first and unchanged in both versions); the proof consumes no property of it.
- `dedentCore : List String → List String` is the UNCHANGED `dedent_lines`
  routine (integer count or `textwrap.dedent`). Opaque, identical in spec and
  impl; the behaviour of interest is WHEN it runs, not its internals.
- `addPrepend` / `addAppend` model the trivial `prepend_filter` / `append_filter`
  concretely: prepend pushes `prepend + "\n"` onto the front, append pushes
  `append + "\n"` onto the back, each only when the option is present AND
  non-empty. The Python guards are truthiness tests (`if prepend:` /
  `if append:`), so a present-but-EMPTY string inserts nothing; the Lean model
  mirrors this with `some p => if p = "" then lines else …`. Each line is a
  string carrying its trailing newline (Python `str.splitlines(True)`).
- `problem_spec_assembleLines` pins the full assembled result to the post-patch
  composition order: select, then de-indent, then prepend, then append —
  `addAppend (addPrepend (applyDedent (selectContent lines)))`. The de-indent
  pass sees only the selected file content; prepend/append wrap the de-indented
  result.
- `implementation_assembleLines` is the `Id.run do` skeleton of `read`'s
  `for func in filters: lines = func(lines)` loop: it builds the post-patch
  `filters` list `[selectContent, applyDedent opts, addPrepend opts, addAppend opts]`
  and folds the line list through it with a `for`.
- The pre-patch impl (`Solution_prepatch.lean`) builds the list in the buggy
  order `[selectContent, addPrepend opts, addAppend opts, applyDedent opts]`, so
  de-indentation runs last and also mangles the prepended/appended lines —
  exactly the bug. Its `correct_assembleLines` is therefore unclosable whenever
  de-indent is requested together with a prepend/append (the orders disagree).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `lines` (a `List[str]` from `splitlines(True)`, each elem keeps its `\n`) | `List String` | element-wise string equality, `\n` carried in the string |
| `'dedent' in self.options` | `IncludeOptions.dedent : Bool` | presence flag |
| `self.options.get('prepend')` | `IncludeOptions.prepend : Option String` | `None ↔ none`, `s ↔ some s` |
| `self.options.get('append')` | `IncludeOptions.append : Option String` | `None ↔ none`, `s ↔ some s` |
| `pyobject/start/end/lines` filters composed | `selectContent` (opaque) | identity model on both differential sides (selection is upstream of the change) |
| `dedent_lines(lines, …)` | `dedentCore` (opaque) | faithful `dedent_lines` model, identical on both differential sides |
| `if prepend: lines.insert(0, prepend + '\n')` | `addPrepend opts` | `(p ++ "\n") :: lines` when `prepend = some p` and `p ≠ ""` (truthiness guard); no-op when absent or empty |
| `if append: lines.append(append + '\n')` | `addAppend opts` | `lines ++ [a ++ "\n"]` when `append = some a` and `a ≠ ""` (truthiness guard); no-op when absent or empty |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behaviour the patch changes is the ORDER of
  the assembly steps, modeled DEEPLY and structurally (the explicit post-patch
  composition / filter list). SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
  changed decision. The `axioms` region declares only `opaque` signatures, no
  `axiom … _prop`, so **G-AX skips**.
- `selectContent` and `dedentCore` are UNCHANGED by the patch. Each appears
  IDENTICALLY in spec and impl, so they are A-references that cancel in the
  differential test — not consumed axioms. They constrain no output component the
  spec leaves free: `result` is fully pinned to the post-patch composition.
- **Flag dependency:** the discriminating behaviour requires the de-indent pass
  enabled (`dedent = true`) together with a `prepend` and/or `append` value;
  G-CONF and the prepatch both exercise that configuration.

## Note on the spec's equivalence class (for auditors)

`problem_spec_assembleLines` pins the ENTIRE result value to the exact
post-patch composition, so a same-spec implementation verifies IFF it is
extensionally equal to that composition — i.e. iff it is CORRECT on the
modeled slice. In particular, `addPrepend` and `addAppend` act on opposite
ends of the list and commute: an implementation that swaps their order (or
inlines / restructures the fold) computes the SAME function, its closing
proof is honest, and its faithful patch resolves under the official harness
(the real `prepend_filter` / `append_filter` are likewise independent). Such
variants are correct implementations — positive controls — NOT wrong-impl
counterexamples: a genuinely wrong impl (one that differs on some input)
cannot receive a closing clean-axiom proof against this exact-value spec.

## G-CONF fuzz seed

Pinned LCG seed: **10323** (see `conformance_check.py` `SEED`). Corpus:
randomized line lists (random short strings each ending `\n`, 0–6 lines) with a
randomly chosen `dedent` flag and random optional `prepend`/`append` strings,
≥1e5 fuzzed inputs, plus hand-picked edge cases pinning the discriminating
clause: the F2P scenario (`dedent` + `prepend` + `append` together), `dedent`
with only `prepend`, `dedent` with only `append`, `dedent` with neither
(prepend/append absent), and prepend/append with `dedent` absent. The R/I shadow
of `implementation_assembleLines` is diffed against an in-process replica of the
POST-PATCH pipeline; `selectContent` and `dedentCore` are the same deterministic
models on both sides so the diff isolates the step-ordering leg.
