# Relaxed-leakage disposition — django__django-13513

This bundle takes the **relaxed-leakage** disposition (see
`RELAXED_LEAKAGE.md`). The spec view names the gold's tested discriminator
— that **every exception in the chain contributes its own traceback frames
independently, so an exception whose own traceback is empty does not suppress
the frames of the others** — because this instance is a genuine
`problem_statement` ↔ gold MISMATCH and a *faithful* spec cannot avoid naming
it. The mechanical G-LEAK lexical screen still passes (the leak is semantic, not
token-level: no diff line, no patched path, and no
`get_traceback_frames`/`get_exception_traceback_frames`/`explicit_or_implicit_cause`/`__suppress_context__`
identifier appears in the spec view).

## Why faithful + non-leaking is impossible here (adversarial analysis)

Directive 6 judges leakage against the **solver-visible `problem_statement`
ONLY**, never `hints_text`, the gold internals, or the hidden `test_patch`.

**What the `problem_statement` actually says.** The public issue is titled
"debug error view doesn't respect `exc.__suppress_context__` (PEP 415)". Its
entire content is about WHICH exceptions appear in the chain: a view that does
`raise ValueError('my new error') from None` should suppress the implicit
`RuntimeError` context, but the debug view still shows it. It quotes the nested
`explicit_or_implicit_cause()` helper and proposes respecting
`exc_value.__suppress_context__` in it. The `problem_statement`:
  - is entirely about `__cause__` / `__context__` / `__suppress_context__`
    chain *selection*,
  - never mentions traceback FRAMES, the per-exception traceback walk, an
    exception with an EMPTY/`None` traceback, or frame counts,
  - shows a `from None` example whose innermost exception is *suppressed*, not
    one that is *dropped despite having frames to show*.

**The base_commit already fixes the public issue.** At
`base_commit = 6599608c4d0befdcb820ddccce55f183f247ae4f` the helper ALREADY
respects `__suppress_context__` (`django/views/debug.py:398-402`:
`return explicit or (None if suppress_context else implicit)`). The
`__suppress_context__` PEP-415 bug the public issue describes was fixed by an
EARLIER change. The gold patch attached to THIS instance does **not** alter the
suppress-context logic at all — it merely *promotes* the identical closure to a
method (`_get_explicit_or_implicit_cause`), a behaviour-preserving refactor.

**Where the actually-tested discriminator lives.** The sole FAIL_TO_PASS test is
`test_innermost_exception_without_traceback`: it builds a chain whose innermost
cause (`new_exc = RuntimeError('My context')`, attached as `__context__` but
never raised) has NO traceback, and asserts `len(frames) == 1` — the outer
exception's one frame must still be reported. The gold patch's only behavioural
change is the **frame-assembly restructure**: the single coupled
`while tb is not None` traversal (which advanced to the next exception only from
*inside* the per-node loop, so an empty leading traceback aborted the entire
walk and dropped every exception) is replaced by an explicit per-exception
accumulation (`get_exception_traceback_frames` per exception, called
unconditionally for each). This dropped-frames angle, the empty-innermost-trace
input class, and the `len(frames) == 1` obligation are present ONLY in
`hints_text` (which links ticket 31672, *"debug error view shows no traceback if
exc.traceback is None for innermost exception"*) and the hidden `test_patch` —
never in the `problem_statement`.

**The mismatch.** A spec that pins the gold behaviour (so the prepatch fails —
G-DIFF — and no wrong impl verifies — G-EQ) MUST name the per-exception
independent frame contribution / empty-trace-does-not-suppress-others property.
A spec restricted to the `problem_statement` surface (`__suppress_context__`
chain selection) cannot pin the gold fix: that behaviour is unchanged by the
gold and is already correct at base_commit, so such a spec would not fail on the
prepatch and would not sense the change. Hence **faithful + non-leaking is
provably impossible** — the public text (chain *selection* via PEP 415) and the
gold fix (frame *assembly* across the chain) are about different things. This is
the `RELAXED_LEAKAGE.md` condition, not lazy de-narration: the docstring is
already de-narrated to an abstract per-exception-contribution contract; the
residual "leak" is the behaviour itself.

## Requirements satisfied (RELAXED_LEAKAGE.md §"Requirements")

1. **Core is sound.** G-VERIFY pass (model.py verifies, ~40s, <300s, no flags);
   G-DIFF fail (model_prepatch.py is spec-byte-identical and fails the
   postcondition `len(Result()) == chain_total(ToSeq(trace_lens))` on the chain
   `[1, 0]` — the buggy coupled single-pointer walk returns 0, the spec requires
   1); G-MUT 20/20; G-EQ expected sound/tight (every step R/A-reference/I, no
   kind-3; the discriminator is grounded in the input carrier as the structural
   SUM `chain_total(ToSeq(trace_lens))`, not an opaque oracle — directive 8);
   G-AX: `axiom_check.py` exits RC=0 in BOTH pinned-container states (verified) —
   base_commit / gold-NOT-applied (the prescribed pre-patch run mode) AND
   gold-applied. The deep model (`frames_from_traceback` + `chain_total`) == the
   real gold assembly on the F2P witness + 11 boundary + 20 000 fuzz chains (this
   stdlib re-creation + fuzz block is gold-state-independent); the F2P witness
   discriminates gold (1) from the bug (0); and the strict drive of the REAL
   `ExceptionReporter.get_traceback_frames` is gated on BOTH the gold marker (the
   method `get_exception_traceback_frames`, added only by the gold patch) AND the
   gold-era version (< 4.0): in the gold-applied gold-era container it asserts the
   F2P count == 1, while at base_commit (gold not applied) the buggy walk reports
   0 (the bug) and is recorded rather than asserted; G-RESOLVE: `patch.diff` == gold verbatim,
   applies at base_commit, resolves the F2P
   `view_tests.tests.test_debug.ExceptionReporterTests.test_innermost_exception_without_traceback`.
2. **The leak is genuinely unavoidable**, established by the adversarial
   analysis above: the gold's tested discriminator (per-exception independent
   frame contribution; empty innermost traceback no longer dropping the others)
   is demonstrably absent from `problem_statement` (which is entirely about
   `__suppress_context__` chain selection, already fixed at base_commit) and
   present only in `hints_text` / gold / `test_patch`; no PS-derivable
   reformulation models the gold fix (the PS-surface behaviour is unchanged by
   the gold).
3. **Documented in-bundle.** This file; `meta.json` records
   `gates.G-LEAK.status = "relaxed"` with a pointer here; the instance should be
   appended to the scope list in `RELAXED_LEAKAGE.md`.
