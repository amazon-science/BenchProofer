# refinement.md — pytest-dev__pytest-10051

Operation-by-operation correspondence between `implementation_clear`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `LogCaptureHandler.clear`,
to which `LogCaptureFixture.clear` is rerouted). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut st := s` | bind the handler/collector state under inspection | R |
| 2 | `st := { st with cells := st.cells.set st.records [] }` | `self.records.clear()` — empty the existing backing list **in place**, keeping the same object (so `self.records` still names it, and so does any view onto it) | R |
| 3 | `st := { st with transcript := [] }` | `self.stream = StringIO()` — the captured text the handler has rendered no longer reads back anything recorded before the call | R |
| 4 | `return st` | the handler is left holding an empty records list and an empty captured text | R |

Notes:

- **Every step is R — no A, no I.** The changed operation (clearing the records
  store) is modeled DEEPLY as an in-place edit of the referenced heap cell
  (`cells.set records []`), which is precisely what `list.clear()` does and what
  distinguishes the fix from the buggy `reset()` rebind. SPEC_GUIDE §3 forbids
  axiomatizing a deeply-modeled changed op, so the `axioms` region is empty and
  **G-AX skips**.
- **Why R (not I).** The Python objects — a `LogCaptureHandler`, its `records`
  list attribute, and the `stash[...]["call"]` view — are refined to the explicit
  heap carrier `HandlerState` (cells + two reference indices) per the mapping.md
  bijection. `list.clear()` (in-place empty) refines to `List.set records []`
  (same index, emptied contents); the alias `get_records("call") is
  handler.records` (line 699) refines to the precondition `callView = records`.
  This refinement is what makes the soundness-critical property — *the view stays
  coupled* — expressible at all (a pure-value model of `records : List _` would
  collapse `reset` and `clear` to the same `[]` and erase the bug).
- **The fix itself** is step 2: `self.handler.reset()` (which did
  `self.records = []`, a *rebind* to a fresh object) becomes
  `self.handler.clear()` (which does `self.records.clear()`, an *in-place* empty).
  The pre-patch impl (`Solution_prepatch.lean`) models the rebind as
  `cells := cells ++ [[]]; records := cells.length` — allocating a new empty cell
  and repointing `records`, leaving `callView` stranded on the old populated cell.
  Its carried gold proof fails to typecheck, and the spec is in fact FALSE for
  this impl: clause 3 forces `result.cells.length = s.cells.length` while the
  reallocating impl grows the heap (`cells ++ [[]]`), and clause 1 forces
  `result.records = s.records` while it repoints `records` to `cells.length`
  (which contradicts the precondition `s.records < s.cells.length`). So no fresh
  proof could close it either — the bug is genuinely unprovable on the
  discriminating clauses (G-DIFF / G-PANEL).
- **Frame (directive 5).** The spec pins every unchanged component to its input:
  `result.records = s.records`, `result.callView = s.callView`,
  `result.cells.length = s.cells.length` (no cell allocated/discarded), and
  `∀ i ≠ s.records, result.cells[i]? = s.cells[i]?` (other backing-list objects
  untouched, identity-for-identity). The unique changed component — the contents
  of the collector's own cell — is pinned to `some []`, and the coupled-view
  observation `result.cells[result.callView]? = some []` is pinned explicitly
  (this is the F2P observable). Addressing cells by `getElem?` (not `getD []`)
  means a present-but-empty cell is distinguished from an absent one, so an impl
  cannot satisfy the frame by dropping/adding inert empty cells.
- **`self.stream = StringIO()` IS modeled, as `transcript`.** An earlier revision
  of this bundle declared the stream out of model as "behaviourally orthogonal"
  and omitted it. That was wrong, and it was load-bearing: a P2P test
  (`testing/logging/test_fixture.py::test_clear`) asserts `not caplog.text`
  immediately after `caplog.clear()`, and `caplog.text` reads the stream via
  `self.handler.stream.getvalue()` (line 404). With the stream unmodeled, an impl
  that emptied the records store and left the text alone satisfied every clause,
  while its faithful refinement fails that P2P test — i.e. the spec admitted a
  wrong implementation. So the rendered text is now a modeled component,
  `HandlerState.transcript`, and clause 7 pins it to read empty.
- **Why only the transcript's CONTENTS are pinned.** The stream is a pure write
  sink: nothing in the codebase retains a reference into it, and `caplog.text`
  re-reads it through `getvalue()` on every access, so its object identity is not
  observable. Clause 7 therefore says only `result.transcript = []` — it does not
  require a freshly allocated sink, and an impl that truncates the existing one
  in place satisfies it equally (exercised by the `pos-takedrop-reshape` control
  in `properties.py`). Contrast the records store, whose identity IS observable
  through the aliased view and is pinned accordingly by clauses 1 and 4-6. The
  asymmetry between the two components is the real behaviour, not a modeling
  convenience.
- **G-CONF** mechanically refutes the R legs: an in-process replica of the
  post-patch semantics (in-place clear of the referenced cell, references
  preserved) is diffed against the op-for-op shadow of `implementation_clear`
  over ≥1e5 fuzzed heaps/references, comparing the full resulting state including
  the view's observed contents. No A legs.
