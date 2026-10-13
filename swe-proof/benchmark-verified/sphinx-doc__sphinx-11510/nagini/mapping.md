# mapping.md — sphinx-doc__sphinx-11510

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6cb783c0024a873722952a67ebb9f41771c8eb6d`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo file under change: `sphinx/directives/other.py` (the `Include` directive).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `forward_with_source_read(lines)` | the gathered-content forwarding step the gold patch adds inside `Include.run` — the installed instance method `self.state_machine.insert_input = _insert_input` and the `_insert_input(include_lines, path)` closure (`sphinx/directives/other.py`, `Include.run` at line 371; the closure is the patch hunk at `@@ -369,6 +371,40 @@`) | the modeled changed behaviour: how the gathered line sequence is forwarded to the parser |
| `emit_and_collect(body)` *(axiom — A-consumed)* | `self.env.app.events.emit('source-read', docname, arg)` — `EventManager.emit` (`sphinx/events.py:83`) wrapped by the line↔text round trip (`"\n".join(...)` / `str.splitlines()`) in the patch closure | unchanged event-dispatch machinery the patch invokes to offer the body to the hook and collect the rewritten lines |
| `hook(body)` | the abstract net effect on the body lines of every registered `source-read` listener run by `EventManager.emit` (`sphinx/events.py:93-96`) | pure spec: the uninterpreted content transformation applied to the offered body |
| `transformed(lines)` | the line sequence the patch ultimately forwards: `text.splitlines() + include_lines[-2:]` after the event | pure spec: hook-transformed body followed by the two framing markers |

Callees the patch also invokes (NOT separately modeled; they only route the
docname argument of the event and are unchanged):
- `self.env.path2doc(...)` — `BuildEnvironment.path2doc` (`sphinx/environment/__init__.py:391`) → `Project.path2doc` (`sphinx/project.py:79`).
- `os_path(path)` — `sphinx/util/osutil.py:29` (`canonical_path.replace(SEP, path.sep)`; the identity on `/`-separated paths on POSIX). Exercised by axiom_check.py.
- `StateMachine.insert_input(self.state_machine, include_lines, path)` — the unchanged docutils parent method the patch delegates to after rewriting the lines; it consumes the forwarded `include_lines` (`docutils/statemachine.py`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `include_lines: list[str]` (the gathered content lines: the included file's text after `string2lines`, with the docutils framing markers `['', '.. end of inclusion from "<path>"']` appended; see `docutils/.../misc.py Include.run`, `include_lines += ['', '.. end of inclusion from "%s"' % path]`) | `List[int]` of opaque per-line identities | `lines[k]` (an `int`) ↔ the content of the k-th gathered line (a `str`); `len(lines)` ↔ number of gathered lines; the final two entries are the framing markers |
| a single line's `str` content | one `int` (opaque line identity) | distinct line contents ↔ distinct ints; the operation never inspects within a line, only re-orders/replaces whole lines, so line content is modeled as an atomic value. The line↔text round trip `"\n".join(L).splitlines() == L` holds at line granularity for content with no embedded line breaks (the regime: each entry of `include_lines` is one line), so join→hook→splitlines is the identity on the body partition modulo the hook's content rewrite — captured by `hook` operating at line granularity. |
| `text = "\n".join(include_lines[:-2])` then `text.splitlines()` around the event | the body partition `lines.take(len-2)` offered to `hook` and the result spliced back | the join/split is a faithful line↔text bijection in this regime (axiom_check.py validates `"\n".join(body).splitlines() == body` for the tested line sets and that the real round trip reconstructs the input under the identity hook). |
| `include_lines[-2:]` (the two framing markers) | `lines.drop(len-2)` | the last two lines, preserved verbatim. |
| `text = arg[0]` after `events.emit('source-read', docname, arg)` | `hook(body)` | the net effect of the registered listeners on the offered body text, lifted to line granularity. |

`str` indexing/iteration is banned in Nagini and the operation is line-structured
rather than character-structured, so the carrier is `List[int]` of line
identities; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `emit_and_collect` ↔ `EventManager.emit('source-read', …)` + line↔text round trip (A-consumed)
**Callee:** `EventManager.emit` (`sphinx/events.py:83-109`). For each registered
`source-read` listener it calls `listener.handler(self.app, docname, arg)` in
priority order; listeners mutate `arg[0]` in place to rewrite the source text
(`sphinx/io.py:108-115` is the primary-document use: `arg = [content];
emit('source-read', docname, arg); return arg[0]`). The patch wraps this with
the line↔text round trip:

```python
text = "\n".join(include_lines[:-2])   # body = all but the two framing markers
arg = [text]
self.env.app.events.emit("source-read", docname, arg)
text = arg[0]
include_lines = text.splitlines() + include_lines[-2:]   # reattach markers
```

The axiom encodes only the obligation the proof needs: offering the body line
sequence to the dispatcher and collecting the result yields exactly the body
with the hook applied — `ToSeq(Result()) == hook(ToSeq(body))`. The hook itself
is uninterpreted (it stands for arbitrary user listener code), so the axiom is
the **weakest** contract sufficient: it does not constrain what the hook
computes, only that the dispatch is applied to the body and returns a fresh line
sequence. **Flag/configuration dependency:** sound for the default
`source-read` event with `arg` a one-element list whose sole element is replaced
in place (Sphinx's own contract, `sphinx/io.py`); the markers `include_lines[-2:]`
must be passed through untouched (they are never offered to the event). G-AX
fuzzes exactly this.

**Axiom regime (directive 7 — raise path).** `EventManager.emit('source-read', …)`
can raise `ExtensionError` if a registered listener raises, and `emit_and_collect`
carries no `Exsures`. This is sound under the scoping the proof needs: the axiom
is the WEAKEST contract for the NON-RAISING regime, and on a raising listener both
the real `_insert_input` helper and the abstraction are in the no-normal-return
regime (the closure propagates the exception and never reaches the parser), so the
postcondition `ToSeq(Result()) == hook(ToSeq(body))` is only claimed when the
dispatch returns normally — which is exactly the F2P/P2P regime (their listeners
are non-raising). `verify => resolved` is unaffected by the omitted `Exsures`.

**Soundness check (G-AX):** `axiom_check.py` replicates the patch's
`_insert_input` text logic byte-for-byte and drives it through the **real**
`sphinx.events.EventManager` with a registered `source-read` handler over 8
boundary line sets (incl. the two F2P shapes and the issue's `&REPLACE_ME;`
case) and 20 000 randomized line sets. It asserts: the two framing markers are
excluded from the event text and re-attached verbatim; the event text equals
`"\n".join(lines[:-2])`; the identity hook reconstructs the input (round trip);
a rewriting hook's effect lands only in the body region; and the model
decomposition `hook(body) + markers` equals the real helper's output. It also
exercises the real `os_path`. Imports only stdlib + the unchanged Sphinx
callees the patch calls. Exit 0 iff sound.

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned seed: `SEED = 11510`.** Input count: **101 512** Requires-satisfying
inputs (1 512 boundary + 100 000 seeded fuzz); the pure helper `transformed`
is additionally cross-checked on 21 512 of them.

**Shadow.** The `# impl-start`/`# impl-end` region of `model.py`
(`forward_with_source_read`) copied VERBATIM, with only the four `Assert(...)`
calls removed — no renaming, no restructuring. The pure region's `transformed`
comes over unchanged on a `PSeq` shim (immutable sequence: `take`/`drop`/`+`/
`len`/`[]`/`==`; `ToSeq` materializes one). The `@ContractOnly`
`emit_and_collect` has no body to copy, so it is realized by CALLING the real
callee §3.1 binds it to — `sphinx.events.EventManager.emit('source-read', …)`
on a real `EventManager` with real registered listeners, wrapped by the
documented line↔text round trip (`"\n".join` / `str.splitlines`). The axiom is
therefore exercised, not assumed.

**Oracle — the real patched function, CALLED (not transliterated).** §1 binds
the model to the `_insert_input` closure the gold patch installs in
`Include.run` (`sphinx/directives/other.py`, hunk `@@ -369,6 +371,40 @@`). A
closure is not importable, so the velvet/lean siblings transliterate it; this
check does not. It constructs a real `sphinx.directives.other.Include`, lets the
REAL patched `Include.run` execute far enough to install
`self.state_machine.insert_input = _insert_input`, lifts the installed closure
off the instance, and calls it. The whole downstream path is real too: the real
`os_path` + `Project.path2doc` for the docname, the real `EventManager.emit`,
and the real `docutils.statemachine.StateMachine.insert_input`, out of whose
`input_lines` the forwarded sequence is read back.

**Guards against a vacuous pass.** `_assert_oracle_is_patched_closure` exits 1
unless the lifted attribute really is `Include.run.<locals>._insert_input`,
unless the patched source markers (`include_lines[:-2]`, `include_lines[-2:]`,
`"source-read"`) are present in `Include.run`, and unless the patch's listener
gate holds (no `source-read` listener ⇒ no closure installed). Verified: run
WITHOUT the gold patch ⇒ exit 1 ("is the gold patch applied?"). Additionally
`_negative_controls` requires all five shadow mutants (body split at `-1`/`-3`,
markers concatenated before the body, markers dropped, whole sequence offered
to the hook) to be refuted by the boundary inputs; a surviving mutant fails the
check as vacuous. Verified: mutating the shadow's split to `n-1` ⇒ exit 1 on the
first boundary input.

**Type bridge (§2 inverted).** `List[int]` opaque line identities ↔
`list[str]` gathered lines, as a memoized dynamic bijection
(`_intern`/`_unintern`), total on every line content that occurs including
novel lines a listener emits. Generation happens on the `str` side (the real
function's side) and lowers to ints for the shadow; the closure's forwarded
`list[str]` lifts back to ints for comparison. Injectivity makes int-sequence
equality equivalent to string equality, and both directions are exercised.

**Input domain.** Exactly the Requires: `len(lines) >= 2` (the two framing
markers are always present — the modelled regime) and the input list is never
aliased or mutated (checked on both legs, mirroring the `1/2` permission).
Generated line strings contain no `str.splitlines()` boundary character, which
is §2's stated regime ("each entry of `include_lines` is one line"); listener
OUTPUT is deliberately unrestricted and injects every boundary character
(`\r`, `\r\n`, `\v`, `\f`, `\x1c`, `\x1d`, `\x1e`, `\x85`, LS, PS), since `hook`
is uninterpreted. The `len < 2` arm of `transformed` is NOT tested: the impl's
precondition excludes it (the arm exists only to keep the pure helper total),
so exercising it would test outside the specification rather than refute it.
The impl region is straight-line, so branch coverage is total by construction.

Boundary inputs enumerated first: empty authored body, singleton body, BOTH F2P
gathered shapes (`test_include_source_read_event` — `["", "Baz was here.", …]`;
`test_include_source_read_event_nested_includes` — `["The #magical foo.", …]`),
the issue's `&REPLACE_ME;` case, all-empty bodies, body content that repeats the
marker text, and two listeners dispatched in priority order by the real
`EventManager`. Beyond the model's `ToSeq(Result()) == transformed(ToSeq(lines))`
equality, each observation also checks the model's other postconditions against
the REAL output (`len(Result()) >= 2`, markers preserved verbatim) and the
axiom's content claim (the event text is exactly `"\n".join(lines[:-2])`, with
the real emitted docname).

Recorded gate verdict: `G-CONF=pass` (101 512 inputs, 0 disagreements).
