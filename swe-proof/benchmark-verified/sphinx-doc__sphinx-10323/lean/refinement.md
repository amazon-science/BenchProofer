# refinement.md — sphinx-doc__sphinx-10323

Operation-by-operation correspondence between `implementation_assembleLines`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`LiteralIncludeReader.read` filter pipeline). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut acc := lines` | `lines = self.read_file(self.filename, …)` (`code.py:230`) | I |
| 2 | `selectContent` as the first filter | the unchanged leading passes `pyobject_filter, start_filter, end_filter, lines_filter`, applied first and in fixed relative order (`code.py:223-226`) | A-reference |
| 3 | `applyDedent opts` as the SECOND filter (post-patch position) | `self.dedent_filter` moved to run after the selection passes but BEFORE prepend/append (`code.py:227` post-patch) | R (the discriminating clause) |
| 4 | `addPrepend opts` filter | `self.prepend_filter`: `if prepend: lines.insert(0, prepend + '\n')` — truthiness guard, so present-but-empty inserts nothing (`code.py:343-348`) | I |
| 5 | `addAppend opts` filter | `self.append_filter`: `if append: lines.append(append + '\n')` — truthiness guard (`code.py:350-355`) | I |
| 6 | `for f in filters do acc := f acc` | `for func in filters: lines = func(lines, location=location)` (`code.py:231-232`) | I |
| — | the ORDER of the `filters` list (`[select, dedent, prepend, append]`) | the FIX: reordering the `filters` list so `dedent_filter` precedes `prepend_filter`/`append_filter` (`code.py:223-229`) | R (the discriminating clause) |

Notes:

- **The R leg is the step order** (ops 3 and the "—" row): the post-patch
  pipeline runs `applyDedent` on the selected content BEFORE adding the
  `prepend`/`append` lines, so de-indentation never touches the author-supplied
  lines. SPEC_GUIDE §3 forbids axiomatizing this deeply-modeled changed decision,
  so the composition order is spelled out structurally in both `problem_spec`
  (`addAppend (addPrepend (applyDedent (selectContent …)))`) and the impl
  (the explicit `filters` list), not axiomatized.
- **Ops 2 and the dedent internals are A-reference, not A-consumed.**
  `selectContent` models the UNCHANGED leading selection passes
  (`pyobject/start/end/lines` filters); `dedentCore` (inside `applyDedent`)
  models the UNCHANGED `dedent_lines` routine. Each appears IDENTICALLY in the
  spec and the impl, so it cancels in the differential test; the proof consumes
  no property of either, so there is no `axiom … _prop` and **G-AX skips**.
  Neither leaves an output component free — `result` is fully pinned by
  `problem_spec` to the post-patch composition.
- **`addPrepend`/`addAppend` are I (identical concrete ops).** They are the
  trivial unchanged `prepend_filter`/`append_filter` (`insert(0, p+'\n')` /
  `append(a+'\n')`), modeled concretely with the same TRUTHINESS guard as the
  Python (`if prepend:` / `if append:`): the Lean helpers act only when the
  option is `some p` with `p ≠ ""`, so a present-but-empty value inserts
  nothing — exactly the real reader's behaviour.
- **The fix itself** is the "—" row: before the patch the `filters` list ended
  with `dedent_filter`, so de-indentation ran last and also stripped leading
  whitespace from the prepended/appended lines. The pre-patch impl
  (`Solution_prepatch.lean`) reproduces this exactly with the buggy filter order
  `[selectContent, addPrepend opts, addAppend opts, applyDedent opts]`. Its
  `correct_assembleLines` is therefore unclosable whenever `dedent` is requested
  together with a `prepend`/`append` value (the two orders disagree, and
  `dedentCore` is opaque so they cannot be proved equal) — exactly the signal
  G-DIFF wants.
- **Spec tightness / equivalence class.** The post-condition equates `result`
  with one exact list value, so verification is extensional equality with the
  post-patch pipeline. Implementations that differ only by provably-equal
  restructuring (e.g. applying `addAppend` before `addPrepend` — the two act
  on opposite ends and commute, in Lean and in the real reader alike) are
  CORRECT: their proofs close honestly and their faithful patches resolve.
  They are alternative positive controls, not spec-weakness counterexamples;
  no impl that differs from the pipeline on ANY input can close the proof
  with clean axioms.
- **G-CONF** mechanically refutes the R/I legs over ≥1e5 fuzzed inputs (no
  A-consumed legs): the Python shadow of the impl is diffed against the
  post-patch pipeline, with `selectContent` and `dedentCore` the same
  deterministic models on both sides so the diff isolates the step-ordering leg.
