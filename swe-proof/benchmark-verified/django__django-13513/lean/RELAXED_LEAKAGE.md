# Relaxed-leakage rationale — django__django-13513

**Disposition: KEEP, G-LEAK = relaxed.** In this unified repo the
relaxed-leakage policy lives in the binding spec-construction rules,
`prompts/lean/spec_guide.md` directive 6 ("**Exception — relaxed-leakage:**
for a proven `problem_statement ↔ gold` mismatch where a faithful spec MUST
name the discriminator, keep the instance with the leak allowed
(`meta.json gates.G-LEAK.status = "relaxed"`)"); the G-LEAK gate honors it
mechanically (`src/swebench_unified/gates/leak.py`, via the `relaxed_leakage`
meta flag + this file).
This is a documented `problem_statement ↔ gold` mismatch: the publicly-reported
bug and the gold fix's actually-tested behavior are about different things.

## Modeled function
`ExceptionReporter.get_traceback_frames` (`django/views/debug.py`), modeled as
`gatherFrames` (`Solution.lean`).

## The mismatch

**What the public `problem_statement` reports.** The issue is titled "debug error
view doesn't respect `exc.__suppress_context__` (PEP 415)" and is entirely about
exception-chain **selection**: the inner `explicit_or_implicit_cause` helper
ignored `__suppress_context__`, so a `raise ... from None` still showed the
suppressed context exception. Token scan of `problem_statement` (lowercased):
`__suppress_context__` ×3, but `empty` 0, `drop` 0, `curtail` 0, `generator` 0,
`extend` 0, `concat` 0, `independent` 0, `get_exception` 0, `len(` 0, `31672` 0.

**What is actually true at `base_commit`.** The chain-selection helper ALREADY
respects `__suppress_context__` at `6599608c` — the body is
`return explicit or (None if suppress_context else implicit)`. The
publicly-reported bug is not present. The gold patch's change to this helper is a
behaviour-preserving refactor only: it is hoisted from a nested closure
(`explicit_or_implicit_cause`) to a method (`_get_explicit_or_implicit_cause`),
with identical logic.

**What the gold patch actually changes (the F2P-observed behavior).** The gold
splits the single coupled `while tb is not None` traversal into a per-exception
generator `get_exception_traceback_frames(exc_value, tb)` that is called
unconditionally for EVERY link of the exception chain, and concatenates each
link's frames:

```python
frames.extend(self.get_exception_traceback_frames(exc_value, tb))
while exceptions:
    exc_value = exceptions.pop()
    frames.extend(self.get_exception_traceback_frames(exc_value, exc_value.__traceback__))
return frames
```

Pre-patch, the single combined `while tb is not None` loop advanced to the next
link only from inside the body (when a link's traceback was exhausted). A link
whose traceback was empty/`None` on entry made the loop condition false
immediately, so the walk terminated and EVERY later link's frames were dropped.
The sole FAIL_TO_PASS test, `test_innermost_exception_without_traceback`,
constructs a chain whose innermost (first-walked) link has no traceback and
asserts `len(frames) == 1` — i.e. the outer link's frame still appears. This is
the dropped-frames bug, NOT the `__suppress_context__` selection bug.

## Why the leak is unavoidable

A faithful spec must pin the discriminator the F2P test checks: every link's
frames appear in the report, in chain order (`result = linkFrames.flatten`, not
`(linkFrames.takeWhile (· ≠ [])).flatten`). That behavior — per-link independent
contribution to the report — is demonstrably ABSENT from `problem_statement`,
which describes only chain selection. The dropped-frames angle is reachable only
via `hints_text` (which links the *related but different* ticket 31672, "debug
error view shows no traceback if exc.__traceback__ is None for innermost
exception") and the gold/`test_patch`. A PS-derivable spec would model
`__suppress_context__` selection — already correct at base_commit, changed only
cosmetically by the gold — and would neither fail the prepatch nor pin the F2P
behavior.

Therefore *faithful* (G-EQ/G-DIFF) and *non-leaking* (directive 6, judged against
`problem_statement` only) are jointly impossible here: the behavior itself is the
leak.

## De-narration applied (repair pass, 2026-08-03)

The spec view was de-narrated to the minimum faithful statement. It no longer
contains the explicit bug→fix narration a prior G-PANEL-3 pass flagged as the
leak surface — the docstring sentence "A link that happens to carry no frames
contributes nothing, but it does NOT curtail the report — the frames of the
links that follow it in the chain still appear" and the post-conditions gloss
"independent of whether any earlier link contributed an empty sequence" were
both removed (from BOTH twins identically; spec regions stay byte-identical).
What remains is the abstract required behavior only: "the report is the in-order
concatenation of every link's frames, in chain order" plus the postcondition
`result = linkFrames.flatten`. The spec view names no patched symbol, file, or
mechanism (no generator extraction, no `extend`/`yield`/`tb_next`, no
curtailment story); the residual semantic leak is exactly the faithful
postcondition itself, which cannot be weakened without admitting the prepatch
impl (G-DIFF) or drifting from the graded F2P behavior (G-EQ).

## Core soundness is unaffected

- **G-VERIFY** passes: `Solution.lean` compiles and `correct_gatherFrames` closes
  with a clean `#print axioms` (`propext`, `Quot.sound`; no `sorryAx`).
- **G-DIFF** fails the prepatch: the carried gold proof cannot close against the
  early-`return` (`if tb = [] then return frames`) impl, which drops every link
  after the first empty one — discriminating clause `[[], [f]]`.
- **G-CONF** passes (R/I shadow == post-patch replica over 120k fuzzed chains,
  empty-then-nonempty oversampled).
- **G-AX** skips (no consumed callee axiom; the changed decision is modeled
  deeply as a list concatenation — never axiomatized).
- **patch.diff == gold** (verbatim), so **G-RESOLVE** resolves.

Only the *secondary* no-leakage property is relaxed. The mechanical G-LEAK screen
is lexically clean (the spec view names no patched symbol/path/mechanism — the
leak is semantic, in the modeled behavior itself), which is expected per the
policy. The disposition is recorded WIPE-PERSISTENTLY via the top-level
`meta.json` flag `"relaxed_leakage": true` (the mechanism `gates/leak.py` honors
alongside this file), so a gate wipe + re-gate re-records
`gates.G-LEAK.status = "relaxed"` instead of overwriting the disposition with a
misleading lexical `pass`. (Repair note, 2026-08-03: the first repair pass wrote
this file but left the disposition only in the wipeable `gates` blob; the
re-gate then stamped G-LEAK `pass "spec view clean"`, contradicting this doc,
and the leakage panelist correctly flagged the then-undispositioned semantic
leak. The flag fixes that recording defect.)
