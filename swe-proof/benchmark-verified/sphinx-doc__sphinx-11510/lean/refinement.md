# refinement.md — sphinx-doc__sphinx-11510

Operation-by-operation correspondence between `implementation_includedSource`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `_insert_input`
closure installed by `Include.run`). Tags: **R** type refinement, **A-consumed**
proof uses an axiom, **A-reference** deep model validated == real callee, **I**
identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if hasListeners then … else return { emitted := none, outputLines := lines }` | `if self.env.app.events.listeners.get('source-read'): self.state_machine.insert_input = _insert_input` (else the original docutils `insert_input` runs unchanged) | R |
| 2 | `let n := lines.length` | implicit `len(include_lines)` used by the `[:-2]` / `[-2:]` slices | I |
| 3 | `let body := joinLines (lines.take (n - 2))` | `text = "\n".join(include_lines[:-2])` | R |
| 4 | `let markers := lines.drop (n - 2)` | `include_lines[-2:]` (kept for re-attachment) | R |
| 5 | `let docname := pathToDocname path` | `docname = self.env.path2doc(os_path(path))` | R |
| 6 | `let modified := srcRead body` | `arg = [text]; self.env.app.events.emit("source-read", docname, arg); text = arg[0]` | R |
| 7 | `let newLines := splitLines modified ++ markers` (full `splitlines()` semantics) | `include_lines = text.splitlines() + include_lines[-2:]` | R |
| 8 | `return { emitted := some (docname, body), outputLines := newLines }` | the emitted `(docname, text)` payload (op 6) + the line list forwarded to `StateMachine.insert_input(self.state_machine, include_lines, path)` | R |

Notes:

- **Every step is R or I — no A.** The patch's behaviour is modeled DEEPLY:
  `joinLines` = `"\n".join`, `splitLines` = the FULL `str.splitlines()`
  (all universal line boundaries — `\n \r \r\n \v \f \x1c \x1d \x1e \x85
     ` — with CRLF as one boundary and no trailing empty line;
  differentially fuzzed against the real `str.splitlines()` in
  conformance_check.py), the marker boundary = `take`/`drop (n-2)` ↔
  `[:-2]`/`[-2:]`, and the listener gate = the `hasListeners` branch. SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op, so there is no consumed axiom. The `axioms` region
  declares only the opaque carrier `pathToDocname` (so the docname tag can appear
  in the executable impl); **no `_prop` axiom** is asserted and the proof consumes
  none, so this is NOT an A-reference either — `pathToDocname` is a free,
  unconstrained opaque function. **G-AX skips.**
- The **R** tag on ops 1,3–8 is the type-only refinement of the bijection in
  mapping.md (`list[str]` ↔ `List String`, the emitted payload ↔ `Option (String
  × String)`, `srcRead` ↔ the net listener effect on `arg[0]`,
  `events.listeners.get(...)` truthiness ↔ `hasListeners`). None of them leaves an
  output component free: both `emitted` and `outputLines` are fully pinned by
  `problem_spec_includedSource` (frame discipline, SPEC_GUIDE §0.5) — `emitted` to
  `(pathToDocname path, body)`/`none`, `outputLines` to `splitLines (srcRead body)
  ++ markers` / `lines`.
- **`Nat`-subtraction boundary (op 3/4).** Python `[:-2]`/`[-2:]` on a list with
  `< 2` elements give `[]` / the whole list; Lean's `take (n-2)`/`drop (n-2)` with
  saturating `Nat` subtraction give the same (`n-2 = 0`). G-CONF fuzzes `n ∈
  {0,1,2,…}` to confirm the legs agree at the boundary.
- **`srcRead` faithfulness.** The patch makes no assumption about the listeners'
  transformation beyond "the body is offered and `arg[0]` is taken back". Modeling
  it as an arbitrary `String → String` is therefore the weakest faithful model;
  the spec quantifies over all such functions, so a verifying impl must apply
  exactly that function to exactly the body (not the markers) — the discriminating
  behaviour of the F2P nested-include test.
- **The fix itself** is op 1 + ops 3–8 collectively: pre-patch, no interception is
  installed, so the included lines are parsed verbatim and no event is emitted —
  modeled by the prepatch impl returning `{ emitted := none, outputLines := lines
  }` unconditionally (the `hasListeners = false` branch for ALL inputs).
  `Solution_prepatch.lean` is exactly this, and its `correct_includedSource` is
  unprovable on the discriminating clause (when `hasListeners = true`, the spec
  demands `emitted = some (…)` and `outputLines = splitLines (srcRead body) ++
  markers`, which the constant-`none`/`lines` impl violates whenever `srcRead`
  changes the body or the markers differ).
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against the post-patch `_insert_input` over ≥1e5 fuzzed
  inputs (`conformance_check.py`, seed 11510).
