# mapping.md — django__django-13513

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6599608c4d0befdcb820ddccce55f183f247ae4f`, states the type
abstraction (the Lean↔Python bijection that G-CONF uses to bridge values), and
records callee provenance.

Repo file under change: `django/views/debug.py` (class `ExceptionReporter`,
line 246).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assembleReport (groups : List (List Int))` | the frame-assembly loop of `ExceptionReporter.get_traceback_frames` — `django/views/debug.py:419–468` (the `frames = []` … `return frames` block) | the modeled changed behavior: building the full traceback-frame list from the chain of exceptions |
| `flattenSeq (gs : List (List Int))` | the assembly's *desired* output: the in-order concatenation of every exception's own frame list | pure spec (deep model of the changed op): the report = entries of each item, in order |
| `groups` (the input carrier) | the ordered sequence of per-exception frame lists — for each exception `e` in `exceptions`, the frames produced by `get_exception_traceback_frames(e, e.__traceback__)` (post-patch) | the per-item entry sequences, each produced by the UNCHANGED per-frame traversal (see §3) |
| element `groups[k]` | the frame list contributed by the `k`-th exception in the chain (possibly empty when that exception's traceback `tb` is `None`/already consumed) | one item's entry sequence |

The pre-patch repo construct the change removes (refinement audit only — NOT in
the consumer spec view): the single `while tb is not None:` loop with its trailing

```python
if not tb.tb_next and exceptions:
    exc_value = exceptions.pop()
    tb = exc_value.__traceback__
else:
    tb = tb.tb_next
```

at `django/views/debug.py:447–468`. That loop appends frames for one exception
at a time and only advances to the next exception **when the current exception's
traceback runs out** (`not tb.tb_next`). If an exception in the chain has an
empty traceback (`tb is None`), the outer `while tb is not None:` never enters,
the `else: tb = tb.tb_next` is unreachable, and **the loop ends** — every later
exception's frames are dropped. That is the bug (issue: an inner exception
without a traceback truncates the report). The fix factors the per-exception
frame walk into `get_exception_traceback_frames` and `frames.extend(...)`s it
for **every** exception unconditionally — exactly `flattenSeq groups`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo behavior. The behavior under specification is purely
*structural*: which exceptions' frame lists appear in the output and in what
order. The frame dicts' internal fields (`filename`, `lineno`, `vars`, …) are
produced by the unchanged per-frame traversal and are irrelevant to the change;
they are abstracted to opaque, order-preserving identities.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `frames` — a Python `list` of frame `dict`s | `List Int` | the *flattened* report; each frame dict ↔ a distinct `Int` token (identity-preserving; only multiplicity and order matter to the change) |
| one exception's frame list (a contiguous run of `frames` for one exception) | `List Int` — one element of `groups` | order-preserving; an exception whose traceback is empty ↔ the empty list `[]` |
| the chain `exceptions` (innermost-first, after the `.pop()` reordering) | `List (List Int)` — `groups` | the per-exception frame lists in **output order**: the order `get_traceback_frames` emits them post-patch (innermost exception first, see §3.1) |
| `frames.extend(seq)` | `List` `++` (concatenation) | post-patch the report is built by `extend`-ing each exception's frame list; `++` is the Lean model |
| `len(frames)` | `out.length` | the F2P test asserts `len(frames) == 1` for the one-frame case |

Lean `List` is total and sound; no index workaround is needed. `groups` is
**read-only** (`assembleReport` does not declare it `mut` and never rewrites an
element) — matching the real loop, which never mutates the per-exception frame
lists, only concatenates them (directive 5: read-only frame discipline).

## 3. Callee provenance

### 3.1 `groups` — the per-exception frame lists (UNCHANGED traversal)

Each element of `groups` is the frame list produced for one exception by the
**per-frame inner walk** — the `while tb is not None:` body that builds one frame
dict per traceback level (`django/views/debug.py:430–465`). The patch moves this
walk verbatim into the new method `get_exception_traceback_frames` (a pure
relocation: the body, including `_get_lines_from_file`, `__traceback_hide__`
handling, and the yielded dict, is byte-for-byte the pre-patch loop body minus
the trailing exception-advance branch). This per-frame walk is **not changed by
this patch** (it computes the same frames for a given `(exc_value, tb)`), so its
output is taken as the input carrier `groups`, not modeled or axiomatized.

The chain `exceptions` itself is built by the **unchanged** cause-walk at
`django/views/debug.py:411–425` (`explicit_or_implicit_cause`, which — at this
`base_commit` — *already* respects `__suppress_context__`; see the note below).
The post-patch assembly pops the innermost exception first
(`exc_value = exceptions.pop()`), emits its frames, then `while exceptions:`
pops and emits the rest — so `groups` is ordered innermost-exception-first.

> **Note on the problem statement vs. the gold patch at this commit.** The
> issue text describes the *original* `__suppress_context__` bug in
> `explicit_or_implicit_cause`. That fix had **already landed** at this
> `base_commit` (lines 398–402 contain the `suppress_context` guard). The gold
> patch under construction here is the **follow-up** fix for the same ticket:
> the frame-assembly loop dropped the innermost exception's (or any
> empty-traceback exception's) frames. The added F2P test
> `test_innermost_exception_without_traceback` exercises exactly this — an
> exception chain whose innermost exception has no traceback — and asserts the
> report still contains the one real frame (`len(frames) == 1`). The modeled
> behavior (`flattenSeq groups` = every item's entries, never halting on an
> empty item) is this follow-up fix. No leakage: the spec view names neither the
> file/function nor `__suppress_context__`.

### 3.2 No axioms, no deep-model references

`flattenSeq` models the **changed assembly op itself** (concatenate every item's
entries) — it is an R/I deep model of `frames.extend(...)` over the chain, NOT a
contract about an unchanged callee. There is therefore **no consumed axiom and
no A-reference**, and **no `axiom_check.py`** (G-AX = skip, per the convention of
e.g. `tasks/django__django-13670/`). The R/I fidelity of `flattenSeq` to the
patched assembly is refuted by `conformance_check.py` (G-CONF) over fuzzed chains.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13513`** so the
consumer-side verdict is reproducible. The shadow transliterates `flattenSeq`
(the R/I-tagged assembly) to Python (`sum(groups, [])`); the oracle is the
patched assembly behavior `frames.extend` over the same chain, transliterated
verbatim from the gold-patched `get_traceback_frames` (mapping.md §3.1). There
are no A-tagged callees, so nothing is left as a real-callee call.
