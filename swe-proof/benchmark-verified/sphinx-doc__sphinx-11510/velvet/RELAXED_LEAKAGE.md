# RELAXED_LEAKAGE — sphinx-doc__sphinx-11510 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

The relaxed-leakage policy is `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the
instance with the leak allowed (`meta.json gates.G-LEAK.status =
"relaxed"`)"); the G-LEAK gate honors it mechanically
(`src/swebench_unified/gates/leak.py`, via the `relaxed_leakage` meta flag +
this file). This disposition was mandated by the bundle's own P2 audit
(verdict.md, Defect 1: "set `meta.json gates.G-LEAK.status = "relaxed"` and
add an in-bundle `RELAXED_LEAKAGE.md` documenting the unavoidable two-marker
discriminator. KEEP the instance."), whose leakage sub-review returned
verdict RELAXED with the leak judged genuinely unavoidable.

## The mismatch (problem_statement ↔ gold)

The gold patch (`sphinx/directives/other.py`, `Include.run`) adds a nested
`_insert_input` closure whose discriminating content is:

- **(a) the join → source-read-emit → splitlines round-trip** — the included
  file's lines are re-joined with `\n`, offered to the registered
  `source-read` handler, and the (possibly rewritten) text is re-split; and
- **(b) the two-trailing-marker frame** — docutils 0.18+ appends two
  structural marker lines to `include_lines`; the gold strips them BEFORE
  the emit (`include_lines[:-2]`) and reattaches them verbatim AFTER
  (`+ include_lines[-2:]`). The gold's own comment: "In docutils 0.18 and
  later, there are two lines at the end that act as markers."

Neither (a) nor (b) is derivable from the public `problem_statement`, which
is a pure symptom report: a consumer `source-read` handler doing
`&REPLACE_ME; → REPLACED` is not applied to `include`'d content, and the
expected behavior is that it should be. Token scan of the problem_statement
for {`marker`, `[:-2]`, `[-2:]`, `0.18`, `two lines`, `insert_input`,
`StateMachine`, `splitlines`, `join`, `split`}: **0 occurrences** (verified
by the P2 audit's leakage sub-review; also 0 in `hints_text` for the
two-marker facet — the join/splitlines monkey-patch mechanism appears only
in hints_text, which the leakage standard excludes, and even the hint's
naive workaround lacks the marker-slicing refinement).

## The leak (what the spec view discloses beyond the PS)

The spec view necessarily encodes exactly facets (a)+(b):

- Module docstring: "The trailing **two entries** of `lines` are
  **structural end-markers** introduced by the line reader; they carry no
  document content and MUST survive untouched."
- Postcondition:
  `out = splitLines (transform (List.intercalate ['\n'] (lines.dropLast.dropLast))) ++ lines.drop (lines.length - 2)`
  — i.e. the gold's `"\n".join(include_lines[:-2])` → handler →
  `text.splitlines() + include_lines[-2:]`.

An implementer given ONLY the spec view can transliterate the postcondition
back into the exact gold `_insert_input` body (this was the recorded
G-PANEL-3 reconstruction). The leak is SEMANTIC (the model's behavior IS the
discriminator); the mechanical G-LEAK lexical screen passes because no gold
token (`insert_input`, `source-read`, `StateMachine`, `splitlines`,
`docutils`) appears in the spec view.

## Why the leak is unavoidable (faithful ⟹ leaking)

The frozen postcondition must pin the gold's F2P behavior. The F2P
`test_include_source_read_event` asserts the handler observed EXACTLY
`"\nBaz was here."` — the markers were excluded from the emitted text and
reattached afterward. A spec weak enough to hide the two-marker
strip/reattach would admit implementations that emit the markers to the
handler or drop them (mutation attacks 2, 3, 6 in verdict.md — all killed
by exactly this clause), i.e. it would no longer discriminate the gold; and
a spec that hides the join → transform → resplit round-trip would admit the
prepatch pass-through (`return lines`, attack 1), which G-DIFF requires to
FAIL. The two-marker frame is a docutils-internal artifact not derivable
from the public issue, so PS-only + faithful is impossible. This is a
proven PS ↔ gold mismatch, not lazy de-narration: the leak survives full
de-narration because it lives in the postcondition's executable structure,
not in prose (the obvious tokens are already de-narrated: `source-read`,
`include`, `StateMachine`, `splitlines`, `docutils` are all absent).

## Core soundness (relaxation criteria 1–2, re-verified by the P2 audit)

- G-VERIFY: `Solution.lean` verifies (exit 0, no sorry).
- G-DIFF: `Solution_prepatch.lean` (`return lines`, the pre-patch
  pass-through) fails `prove_correct` on the discriminating postcondition.
- G-MUT: 7/7 killed, all same-spec.
- G-CONF: 0 disagreements vs the gold `_insert_input` body over the fuzzed
  input × handler family (pinned seed 11510), including boundary-injecting
  handlers exercising the full `str.splitlines` model.
- G-RESOLVE: gold patch verbatim, resolves.
- G-EQ / G-PANEL-1: SOUND + TIGHT (7 attacks re-run, none breaks the spec;
  positive controls verify).

Criteria 1 (core sound) and 2 (leak genuinely unavoidable) hold; this file +
the `relaxed_leakage` meta flag supply criterion 3 (in-bundle
documentation), which the original bundle omitted (audit Defect 1).
