# refinement.md — django__django-13513

> **Leakage disposition:** documented `problem_statement ↔ gold` mismatch kept
> under the sanctioned **relaxed-leakage** policy (spec_guide directive 6
> exception): the public PS reports only the `__suppress_context__`/PEP-415
> chain-SELECTION issue (already correct at base_commit), while the gold's
> F2P-graded behavior is the empty-traceback curtailment fix. See in-bundle
> `RELAXED_LEAKAGE.md` (token-scan + unavoidability proof + de-narration log);
> `meta.json` carries `"relaxed_leakage": true` and G-LEAK records
> `status="relaxed"`. The residual semantic disclosure is exactly the faithful
> postcondition, which cannot be weakened without admitting the prepatch impl.

Maps every operation in `implementation_gatherFrames` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `gatherFrames` (`ExceptionReporter.get_traceback_frames`)

Post-patch repo code (`patch.diff`), the collection over the exception chain:

```python
exc_value = exceptions.pop()
tb = self.tb if not exceptions else exc_value.__traceback__
frames.extend(self.get_exception_traceback_frames(exc_value, tb))
while exceptions:
    exc_value = exceptions.pop()
    frames.extend(
        self.get_exception_traceback_frames(exc_value, exc_value.__traceback__),
    )
return frames
```

Lean impl (`implementation_gatherFrames`):

```lean
def implementation_gatherFrames (linkFrames : List (List Frame)) : List Frame :=
  Id.run do
    let mut frames : List Frame := []
    for tb in linkFrames do
      frames := frames ++ tb
    return frames
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `linkFrames : List (List Frame)` | the exception chain in walk order, each link's traceback frames | **R** | outer-list element ↔ one link of the chain (`exceptions.pop()` order, innermost cause first); inner list ↔ the frames that link's traceback contributes, in tb order. The per-link frame *production* (`get_exception_traceback_frames`'s inner `while tb` loop, `_get_lines_from_file`, dict assembly) is unchanged by the patch, so it is abstracted into the input (mapping.md bijection). |
| 2 | `let mut frames : List Frame := []` | `frames = []` (initialized earlier in the function) | **I** | the accumulator the report is built into. |
| 3 | `for tb in linkFrames do` | `frames.extend(get_exception_traceback_frames(first, tb))` then `while exceptions: ... frames.extend(get_exception_traceback_frames(next, next.__traceback__))` | **I** (deep model of the changed control flow) | **the fixed control flow.** The patch processes EVERY link independently and extends `frames` with each link's frames — a flat iteration over all links. The first `extend` + the `while exceptions` loop together iterate over all chain links exactly once, in walk order; modeled as one `for tb in linkFrames`. |
| 4 | `frames := frames ++ tb` | `frames.extend(self.get_exception_traceback_frames(exc_value, <its tb>))` | **I** (deep model of the changed op) | each link contributes its frames by appending them in order; `get_exception_traceback_frames` yields exactly `tb`'s frames for that link (its loop ends with `tb = tb.tb_next`, no cross-link jump). An empty link (`tb = []`) appends nothing but does NOT terminate the iteration — this is precisely the behavior the patch introduces vs. the pre-patch single combined `while tb` loop, which aborted at the first empty traceback. |
| 5 | `return frames` | `return frames` | **I** | the assembled report is returned. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch behavior (flat concatenation of all links' frames).

## Soundness check (verify ⟹ correct)

- `problem_spec_gatherFrames linkFrames result := result = linkFrames.flatten`
  pins the result EXACTLY (full list equality to an input-grounded expression) —
  directive 5 (frame): the output is fully determined by the per-link frame
  lists; no output component is left unconstrained, and there is no ungrounded
  oracle (directive 8) — the postcondition is dischargeable only by actually
  concatenating the input's per-link frame lists in order.
- The prepatch impl reproduces the single-combined-loop behavior: it walks links
  and concatenates, but `return`s early at the first link with an empty frame
  list (`if tb = [] then return frames`) — exactly the pre-patch `while tb is not
  None` loop that exits the moment a link's traceback is empty, dropping all
  later links. It violates the spec on the discriminating clause
  `linkFrames = [[], [f]]`: the impl returns `[]`, the spec requires `[f]`. Its
  carried gold proof cannot close (G-DIFF/G-PANEL); the failing case is any chain
  with an empty link FOLLOWED by a non-empty link.
- This discriminating case is precisely what the FAIL_TO_PASS test
  `test_innermost_exception_without_traceback` exercises: an exception chain
  whose first-walked (innermost) link has a non-`None` traceback but whose deeper
  context link (`exc.__context__`, set manually and never raised) has NO
  traceback. Pre-patch, hitting the empty traceback curtails the walk and the
  report is wrong; post-patch, every link's frames appear (the test asserts the
  exact frame count and that the context exception is reported).
- G-CONF confirms the R/I shadow == the in-process replica of the patched flat
  concatenation over hand-picked edge cases (including empty-then-nonempty,
  leading/trailing empty links, all-empty) plus ≥1e5 fuzzed chains.
