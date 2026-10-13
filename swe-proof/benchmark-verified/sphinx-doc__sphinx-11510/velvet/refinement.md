# refinement.md — sphinx-doc__sphinx-11510

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`assembleInsertedLines` `do` block) and `patch.diff` (the gold patch's new
`_insert_input` closure inside `Include.run`). Each step is tagged **R** (type
refinement), **A-consumed** / **A-reference** (axiomatized / deep-modeled
callee), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligation runs under
`loom.semantics.termination "total"` (`TotalCorrectness`), so a verifying
implementation must TERMINATE and return the specified assembly. (An earlier
revision used partial correctness, which a same-spec diverging implementation
— e.g. an infinite loop before the `return` — vacuously satisfies; total
semantics excludes that whole class. The modeled assembly trivially
terminates: slicing, joining, one transform application, re-splitting and
concatenation over finite inputs are straight-line bounded operations that
always return.)

## A. The inserted-content assembly site — `_insert_input` (`sphinx/directives/other.py`, post-patch `Include.run`)

Gold hunk (the load-bearing body of the new closure):
```python
text = "\n".join(include_lines[:-2])
docname = self.env.path2doc(os_path(path))
arg = [text]
self.env.app.events.emit("source-read", docname, arg)
text = arg[0]
include_lines = text.splitlines() + include_lines[-2:]
return StateMachine.insert_input(self.state_machine, include_lines, path)
```

| # | Solution.lean impl op (`assembleInsertedLines`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `lines : List (List Char)` | `include_lines` arg | R | `list[str]` ↔ `List (List Char)` (mapping.md §2). G-CONF bridges element-wise. |
| A2 | param `transform : List Char → List Char` | the `source-read` emit round-trip `arg=[text]; emit(...); text=arg[0]` | R | the consumer handler's net text effect; arbitrary total function, spec assumes nothing (mapping.md §3.2). G-CONF fuzzes a family of handlers. |
| A3 | `content := lines.dropLast.dropLast` | `include_lines[:-2]` | I | drop the two trailing marker lines (concrete slice, transliterated by G-CONF). |
| A4 | `List.intercalate ['\n'] content` | `"\n".join(include_lines[:-2])` | I | join content with the newline separator (mapping.md §2). |
| A5 | `transform (…)` | `arg=[text]; emit("source-read", docname, arg); text=arg[0]` | R | apply the registered transform to the joined content text (A2). The `docname = path2doc(os_path(path))` computation feeds only the event's docname argument, not the content; out of frame (mapping.md §1). |
| A6 | `splitLines text` | `text.splitlines()` | R | split the transformed text back into lines (mapping.md §3.1; full CPython line-boundary model — exact for every `transform` output). |
| A7 | `… ++ lines.drop (lines.length - 2)` | `… + include_lines[-2:]` | I | reattach the two preserved marker lines verbatim (mapping.md §2). |
| A8 | `return assembled` | `return StateMachine.insert_input(self.state_machine, include_lines, path)` | R | the unchanged downstream line inserter is identity on the produced line content w.r.t. the observable document text the F2P tests assert (mapping.md §1); modeled as returning the assembled lines. |

The **discriminating content** of the change — that the inserted content is
offered to `transform` AT ALL, with the two structural markers preserved — lives
in the postcondition

```
out = splitLines (transform (intercalate ['\n'] (lines.dropLast.dropLast)))
        ++ lines.drop (lines.length - 2)
```

The pre-patch behavior splices `include_lines` through unchanged (no event, no
transform); `Solution_prepatch.lean` reproduces that (`return lines`) and
**fails** this postcondition (G-DIFF): with a non-identity `transform` (e.g. the
F2P `#magical → amazing` handler) `lines ≠ splitLines (transform …) ++ markers`.

## B. Directive-5 (mut-frame) — the preserved markers

`transform` and `lines` are read-only: neither is declared `mut`. The two
trailing marker lines are pinned UNCHANGED in the postcondition's tail
(`++ lines.drop (lines.length - 2)`), exactly mirroring `+ include_lines[-2:]`.
This is the Lean analogue of stating the unchanged frame explicitly: the result
outside the content region is byte-identical to the input markers. The F2P
`test_include_source_read_event` asserts the included `baz/baz.rst` content
(`"\nBaz was here."`) is what the handler saw — i.e. the markers were excluded
from the event and reattached afterward; this is precisely the A3/A7 frame.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. There are **no axioms** (A-consumed) and **no deep-model
references** (A-reference): the one genuinely arbitrary element — the consumer
`source-read` handler — is modeled not as an axiomatized callee but as a
universally-quantified function parameter `transform` about which the spec
assumes nothing. This is strictly stronger than an axiom (it must hold for every
handler) and needs no soundness check, so G-AX is a no-op (no callee to run).

The effectful glue the patch also adds — installing the patched
`insert_input` only when a `source-read` listener exists, and the event-emission
plumbing — is observationally subsumed: with no listener the relevant
`transform` is the identity and `assembleInsertedLines transform lines`
reproduces the unchanged content (a special case), so the spec covers the
listener-absent path too.

## D. verify(Solution) ⇒ resolved

`assembleInsertedLines` verifies only if its output equals, for EVERY
`transform`, the content (markers stripped) joined-transformed-resplit, with the
two markers reattached (A3–A7) — the exact data flow of the gold `_insert_input`.
By R (`list[str] ↔ List (List Char)`, `splitlines` modeled in full over every
CPython line boundary, `join` exact, the downstream inserter identity on
content) the verified
assembly equals the gold patch's `include_lines` reconstruction on the tested
inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour
over a fuzzed family of handlers and inputs. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there is no axiom-soundness trust point (no axioms).
