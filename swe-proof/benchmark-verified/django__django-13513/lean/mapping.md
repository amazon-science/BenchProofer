# mapping.md — django__django-13513

> **Leakage disposition:** this instance is a documented `problem_statement ↔
> gold` mismatch and is kept under the sanctioned **relaxed-leakage** policy
> (spec_guide directive 6 exception). See in-bundle `RELAXED_LEAKAGE.md`;
> `meta.json` carries the wipe-persistent flag `"relaxed_leakage": true` and
> G-LEAK records `status="relaxed"`. The residual semantic disclosure is
> exactly the faithful postcondition (`result = linkFrames.flatten`), which
> cannot be weakened without admitting the prepatch impl (G-DIFF) or drifting
> from the graded F2P behavior (G-EQ).

## Symbol binding (file:line @ base_commit 6599608c4d0befdcb820ddccce55f183f247ae4f)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_gatherFrames` / `problem_spec_gatherFrames` | `ExceptionReporter.get_traceback_frames` (the frame-collection over the exception chain) | `django/views/debug.py:397-471` |
| `Frame` (pure helper) | one assembled traceback-frame dict appended to `frames` | see field note below |
| `linkFrames` (input) | the per-exception list of frames each link of the exception chain contributes | see input note below |

The modeled function is `ExceptionReporter.get_traceback_frames`. It is the only
function whose observable behavior changes and the one exercised by the
FAIL_TO_PASS test `test_innermost_exception_without_traceback`, which asserts
`len(reporter.get_traceback_frames()) == 1` for an exception chain whose
innermost link carries a non-`None` traceback but whose deeper context link
(`exc.__context__`) carries NO traceback.

### What the function does (base_commit)

```python
def get_traceback_frames(self):
    def explicit_or_implicit_cause(exc_value):
        explicit = getattr(exc_value, '__cause__', None)
        suppress_context = getattr(exc_value, '__suppress_context__', None)
        implicit = getattr(exc_value, '__context__', None)
        return explicit or (None if suppress_context else implicit)

    # Build the chain of exceptions (innermost cause first ... outermost last).
    exceptions = []
    exc_value = self.exc_value
    while exc_value:
        exceptions.append(exc_value)
        exc_value = explicit_or_implicit_cause(exc_value)
        if exc_value in exceptions:
            ... break          # cycle guard

    frames = []
    if not exceptions:
        return frames

    exc_value = exceptions.pop()                 # outermost
    tb = self.tb if not exceptions else exc_value.__traceback__

    while tb is not None:                         # <-- single combined walk
        ... build a frame dict from tb ...
        frames.append({...})
        if not tb.tb_next and exceptions:         # consumed this link's tb?
            exc_value = exceptions.pop()          #   advance to the next link
            tb = exc_value.__traceback__
        else:
            tb = tb.tb_next
    return frames
```

The chain `exceptions` is walked from the last element (`pop()`) toward the
first — i.e. **innermost cause first, outermost last** (the elements were
appended outermost→innermost, then popped). Each link contributes the frames of
its own traceback (`tb` chain).

**The observable bug.** The collection is a SINGLE `while tb is not None` loop:
it advances to the next link in the chain only from *inside* the loop body, when
the current link's traceback is exhausted (`not tb.tb_next and exceptions`). If a
link's traceback is empty/`None` to begin with, the loop condition is false on
entry, the loop exits immediately, and **every remaining (outer) link in the
chain is dropped** — its frames never reach the report. The F2P case is exactly
this: the innermost link (walked first) has `tb is None`, so the loop never runs
and the outer link's single frame is lost (the report comes back empty / wrong
length).

### Post-fix behavior (`patch.diff`)

The patch factors the per-link frame production into a generator
`get_exception_traceback_frames(exc_value, tb)` and rewrites the collection as:

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

Each link is processed **independently** and its frames are concatenated into
`frames`. An empty traceback now yields zero frames for that link but does NOT
abort the walk: the frames of every following link still appear, in chain order.
(`get_exception_traceback_frames` itself ends its per-link loop with the plain
`tb = tb.tb_next`, i.e. it walks exactly one link's traceback.)

### `Frame` field ↔ Python bijection

| `Frame` | Python meaning | notes |
|---|---|---|
| `Frame := Nat` | one frame dict appended to `frames` | The modeled behavior depends ONLY on which frames appear and in what order — never on a frame dict's content. So a frame is carried as an opaque identity token (`Nat`); two distinct frames are distinct tokens. The per-link frame *production* (reading source lines, building the dict) is byte-identical before and after the patch and is abstracted into the input. |

### Input bijection (used by G-CONF)

| Lean input | Python meaning |
|---|---|
| `linkFrames : List (List Frame)` | for each link of the exception chain, in walk order (innermost cause first), the list of frames that link's traceback contributes. `linkFrames[i] = []` ⇔ link `i` has an empty/`None` traceback. |
| `result : List Frame` | the `frames` list returned by `get_traceback_frames`. |

The whole exception-chain walk reduces to: given the per-link frame lists in
walk order, produce the report. The patched function produces the in-order
concatenation of all of them (`linkFrames.flatten`); the pre-patch function
produces the concatenation only up to (and excluding) the first link with an
empty traceback (`(linkFrames.takeWhile (· ≠ [])).flatten`).

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| ordered exception chain, each link's traceback frames | `List (List Frame)` | outer list ↔ links in walk order; inner list ↔ that link's contributed frames in tb order. |
| returned `frames` list | `List Frame` | identity on the carrier; post-fix = all links concatenated, pre-fix = links concatenated up to the first empty traceback. |

The function returns `frames`; we model it as a pure function of `linkFrames`.

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — whether an empty
  link's traceback curtails the whole walk or merely contributes nothing —
  is modeled DEEPLY as a list concatenation over the per-link frame lists
  (SPEC_GUIDE §3: a deeply-modeled changed decision is never axiomatized). The
  per-link frame production (`_get_lines_from_file`, the dict assembly, the
  cause/`exc_cause_explicit` fields) is identical pre- and post-patch — it is NOT
  the modeled decision — so it is abstracted into the `linkFrames` input rather
  than carried as an opaque callee. There is therefore no opaque callee whose
  contract the proof consumes (`axiom_check.py` is a skip stub; G-AX skips).
- **`__suppress_context__` / `explicit_or_implicit_cause`.** The chain-CONSTRUCTION
  helper already respects `__suppress_context__` at this base_commit (it is
  unchanged by the patch except for being hoisted to a method); it determines
  *which* exceptions are links of the chain, i.e. the shape of `linkFrames`. The
  duplicate-helper hoist (`explicit_or_implicit_cause` →
  `_get_explicit_or_implicit_cause`) is a pure refactor with no behavior change.
  The F2P-observed fix is the empty-traceback curtailment, which is the modeled
  decision and the discriminating clause.

## G-CONF fuzz seed

Pinned LCG seed: **13513** (see `conformance_check.py` `SEED`). Corpus:
randomized chains (`linkFrames` length 0–6; each link's frame list length 0–4,
empty lists deliberately frequent so the empty-then-nonempty discriminator is hit
often; frames are fresh integer tokens), over ≥1e5 fuzzed inputs, diffed against
an in-process replica of the post-patch behavior (in-order concatenation of all
links' frames).
