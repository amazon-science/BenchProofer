# mapping.md — django__django-13513

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6599608c4d0befdcb820ddccce55f183f247ae4f`, states the type
abstraction, and gives the provenance of the deep-model reference (there is no
consumed `@ContractOnly` axiom).

Repo file under change: `django/views/debug.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assemble_frames(trace_lens)` | `ExceptionReporter.get_traceback_frames(self)` — `django/views/debug.py:397` (frame-assembly tail, lines 419-471) | the modeled changed function: assembles the per-exception report entries across the whole exception chain |
| `frames_from_traceback(chain, k)` | `ExceptionReporter.get_exception_traceback_frames(self, exc_value, tb)` — introduced by the gold patch (`django/views/debug.py`, the extracted generator) | the new per-exception helper: yields one report entry per node in ONE NAMED exception's own traceback (`while tb is not None: yield {...}; tb = tb.tb_next`). The exception is named by its chain position `k`, mirroring the real call, which is passed the popped `exc_value` AND that same exception's traceback |
| `chain_total(lens)` *(deep model — A-reference)* | the cross-chain accumulation `frames.extend(self.get_exception_traceback_frames(...))` over the innermost popped exception then `while exceptions: ...` (gold `get_traceback_frames` tail) | pure spec: the total report length is the SUM of the per-exception traceback-node counts; validated `chain_total == real gold assembly` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `locations_before(lens, k)` *(pure)* | the number of visible traceback nodes owned by the exceptions BEFORE `exceptions[k]` in chain order | pure spec: where exception `k`'s block of chain location numbers begins (§2). Consecutive exceptions own consecutive blocks, so the blocks are pairwise disjoint and a location number identifies its owner |
| `entry_location(lens, pos)` *(pure)* | which visible traceback node of which exception the report entry at position `pos` describes | pure spec: the report is the per-exception blocks in consumption order (innermost cause first), each block contiguous and in `tb_next` order; `entry_location` reads that structure off the chain alone. Total on every int, so positions past the report's end are unconstrained |

The pre-patch repo symbols the change reshapes (for the refinement audit; not
referenced from the consumer spec view):
- the local closure `explicit_or_implicit_cause(exc_value)` inside
  `get_traceback_frames` (`debug.py:398-402`) — promoted to the method
  `_get_explicit_or_implicit_cause`; this is a pure refactor with no observable
  effect on the frame count and is NOT modeled (it does not change the chain
  the report walks).
- the **single coupled traversal loop** `while tb is not None:` with the inner
  `if not tb.tb_next and exceptions: exc_value = exceptions.pop(); tb =
  exc_value.__traceback__` advancement (`debug.py:428-469`) — the locus of the
  bug. Because the advancement to the next exception happens only *inside* the
  per-node loop, a starting traceback that is `None` (the innermost popped
  exception having no traceback of its own) aborts the entire walk and drops
  every exception, even those with a non-empty traceback. The gold patch splits
  this into (a) a per-exception generator and (b) an outer loop that visits
  every exception unconditionally.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | correspondence |
|---|---|---|
| one exception in the chain (`exc_value`) | its POSITION `k` in the chain, together with `trace_lens[k]` = the number of visible nodes in the traceback the report reads for it (`tb` ⇒ `tb.tb_next` ⇒ … count, after `__traceback_hide__` skips) | `exceptions[k]` ↔ the chain index `k`, and the node count ↔ `trace_lens[k]`. The count ALONE does not name an exception — it is many-to-one, two exceptions can record equally long traces — so the index is what identifies the exception, and `debug.py:410-417` (which refuses to append an exception already in `exceptions`) makes distinct indices distinct exceptions |
| the `exceptions` list (chain order: outermost … innermost cause) | `trace_lens: List[int]`, same order; the report pops from the end (`exceptions.pop()`), modeled by the backward index walk `i = n … 1` | `exceptions[k]` ↔ `trace_lens[k]`; `len(exceptions)` ↔ `len(trace_lens)`; `exceptions.pop()` ↔ reading `trace_lens[i-1]` then `i -= 1` |
| one visible traceback node of one exception of the chain | the chain LOCATION NUMBER `locations_before(trace_lens, k) + j` for node `j` (in `tb_next` order) of the exception at chain position `k` | the exceptions own consecutive, pairwise-disjoint blocks of numbers, `trace_lens[k]` wide, in chain order, so a location number names BOTH the owning exception and the index of the node within that exception's own visible trace — and nothing else can carry that number |
| one report-entry dict appended/yielded | one element of the result `List[int]`, carrying the chain location number of the node it describes | a frame dict is determined by exactly that pair, because `get_exception_traceback_frames` is called once per popped exception with THAT exception and THAT exception's own traceback (`debug.py:427`, `:430-431`) and walks the one `tb_next` chain in order (`debug.py:439-473`). Its content is drawn from two independent sources — the OWNER `exc_value` (`exc_cause` / `exc_cause_explicit`, `debug.py:436-437` emitted at `:459-460`) and the NODE `tb` (`filename` / `function` / `lineno` / `module_name`, `debug.py:445-449` emitted at `:461-471`) — so `len(frames)` is not the only observable: the F2P obligation reads the count, and the P2P lane reads which exception a block is attributed to and which node each entry describes. A location number is injective in (owner, node index), so one int per entry preserves both readings |
| `frames.extend(generator)` (gold) | `frames.extend(contribution)` | `extend` ↔ `extend`: `len` is additive, and each exception's block stays contiguous and in trace order |
| `self.tb if not exceptions else exc_value.__traceback__` (the innermost popped exception's traceback) | `trace_lens[n-1]` (the innermost popped exception's own trace length) | in both the single- and multi-exception case the innermost consumed exception contributes the node count of its own traceback; `self.tb` IS that exception's traceback when it is the only one |

`tb`/exception objects are rich Python objects. The modeled behaviour is which
nodes of which exceptions the report contains and in what order, so the input
carrier is the `List[int]` of per-exception visible-node counts (the chain
shape), phrased over `PSeq[int]` via `ToSeq`, and the output carrier is the
`List[int]` of chain location numbers — one per report entry, naming the node it
describes and the exception it is attributed to. The rendered CONTENT of a frame
(the source text, the variables) is not modeled; its provenance is.

## 3. Deep-model reference (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `chain_total` + `frames_from_traceback` ↔ gold `get_traceback_frames` / `get_exception_traceback_frames` (A-reference)

There is **no consumed `@ContractOnly` axiom**: the changed operation (the
exception-chain frame assembly) is Django's *own* control flow, modeled
**deeply**. `frames_from_traceback(chain, k)` is the gold generator
`get_exception_traceback_frames` applied to the exception at chain position `k`
(one entry per node of THAT exception's own traceback ⇒ exactly `chain[k]`
entries, carrying that exception's own location numbers; `tb=None` ⇒ zero).
`chain_total(lens)` is the gold
`get_traceback_frames` accumulation: it visits the innermost popped exception
and then, unconditionally, every remaining exception, summing each one's own
per-exception contribution. Hence the total report length is the SUM of the
per-exception traceback-node counts.

Gold source (`django/views/debug.py`, post-patch):

```python
def get_traceback_frames(self):
    ...                                              # build `exceptions`
    exc_value = exceptions.pop()
    tb = self.tb if not exceptions else exc_value.__traceback__
    frames.extend(self.get_exception_traceback_frames(exc_value, tb))
    while exceptions:
        exc_value = exceptions.pop()
        frames.extend(self.get_exception_traceback_frames(
            exc_value, exc_value.__traceback__))
    return frames

def get_exception_traceback_frames(self, exc_value, tb):
    ...
    while tb is not None:
        ...
        yield {...}
        tb = tb.tb_next
```

**Soundness check (G-AX, axiom_check.py):** reproduces the gold control flow
faithfully (stdlib-only `tb_next` chains) and asserts, on the FAIL_TO_PASS
witness `[1, 0]`, 11 boundary chains, and 20 000 randomized chains, that the
real gold frame count equals `chain_total` (the sum of per-exception trace
lengths), and equals the deep model `frames_from_traceback`-fold. It also
asserts the discriminating witness: the pre-patch coupled walk yields 0 frames
on `[1, 0]` while gold yields 1. It additionally drives the REAL
`ExceptionReporter.get_traceback_frames` on the exact F2P scenario; the strict
`count == 1` assertion is gated on the gold-APPLIED gold-era state and so
`axiom_check.py` exits RC=0 in BOTH pinned-container states (see the gold-and-
version caveat below).

**Gold-state + version caveat (recorded for G-AX fuzzing):** the gold invariant
"frame count == sum of per-exception visible-node counts" holds on the
gold-APPLIED gold-era code (Django 3.2, which the G-RESOLVE container ships
post-patch). The strict drive of the REAL `ExceptionReporter` is therefore gated
on BOTH (a) the gold marker — the method `get_exception_traceback_frames`, which
the gold patch introduces and which is absent at `base_commit`
(`hasattr(ExceptionReporter, 'get_exception_traceback_frames')`) — AND (b) the
gold-era version (`< 4.0`). Three cases, all RC=0:
  - **gold applied, version < 4.0:** the F2P count is exactly 1; asserted.
  - **gold NOT applied, version < 4.0 (`base_commit` / the prescribed pre-patch
    run mode):** the buggy coupled single-pointer walk aborts on the empty
    innermost traceback and reports 0 — the dropped-frames bug, matching the
    modeled pre-patch witness; RECORDED, not asserted (the deep-model soundness
    is established by the gold-state-independent stdlib re-creation + 20 000-fuzz
    block).
  - **version >= 4.0:** a *later* Django additionally emits a placeholder frame
    for a traceback-less exception and reports 2 — a subsequent behaviour beyond
    this gold patch; excluded from the strict assertion and validated against the
    faithful gold re-creation instead.
The F2P test (`test_innermost_exception_without_traceback`) asserts exactly
`len(frames) == 1`, which the gold patch delivers.

## G-CONF

Differential conformance (`conformance_check.py`): the `# impl-start`/`# impl-end`
regions of `model.py` — `assemble_frames` AND `frames_from_traceback` — copied
verbatim with only the contract calls stripped, diffed against the REAL patched
repo function, which is **called, not transliterated**.

**Oracle (called in-container, gold applied by the gate):**
- `django.views.debug.ExceptionReporter.get_traceback_frames` (§1) — driven on
  real exception chains carrying real `TracebackType` chains; the counterpart of
  `assemble_frames`.
- `ExceptionReporter.get_exception_traceback_frames` (the generator the gold
  patch extracts, §1) — driven per exception; the counterpart of
  `frames_from_traceback`.
- `ExceptionReporter._get_explicit_or_implicit_cause` — the real chain walker,
  used to re-derive the chain the real code will visit (bridge check).

**Type bridge (§2 inverted).** `trace_lens[k]` (visible-node count of exception
k's own traceback, chain order, outermost first) is concretized by raising a real
exception through a recursion that lays down `trace_lens[k]` frames without
`__traceback_hide__` plus 0..2 frames with it, interleaved randomly, so the
visible-node abstraction is genuinely exercised; chain links are built as both
`__cause__` (explicit) and `__context__` + `__suppress_context__ = False`
(implicit). `ExceptionReporter(None, type(head), head, head.__traceback__)`
supplies `self.tb` for the single-exception case. Result bridge: real frame dicts
↔ result elements, compared entry by entry through the chain location number
each entry carries (§2), plus the total count and the read-only obligation.

**Bridge check.** Every constructed chain is re-derived through the REAL cause
walker and the real `__traceback_hide__` skip rule and must reproduce the
generated `trace_lens` exactly; a mismatch is reported as a BRIDGE failure
(exit 1), never absorbed. Verified sensitive: mutating either the visibility rule
or the derivation makes the check fail.

**Observables compared.** (1) total report length, cross-checked against the
postcondition's own fold `chain_total(ToSeq(trace_lens))`; (2) the report ENTRY
BY ENTRY. Every real frame dict carries `'tb'`, the traceback node it was built
from, so each real frame is attributed to the exception owning that node and to
that node's position among the visible nodes of THAT exception's own traceback,
and the pair is re-encoded exactly as §2 does — the chain location number
`locations_before(trace_lens, k) + j` — then compared elementwise with the
shadow's own result. This pins the positional clause
`Result()[p] == entry_location(ToSeq(trace_lens), p)` against the REAL reporter,
not merely the length: a per-exception reversal, an exchange of two blocks, or a
block generated from a DIFFERENT exception of the chain — including one whose
trace happens to record the same number of locations — leaves the count exactly
right and breaks this leg, because the numbers a block carries belong to one
exception alone; (3) the same fact read as BLOCKS — the run-lengths of the real
report's consecutive same-owner groups against the block structure of the
shadow's report. The shadow's block boundaries are an observable of its own
output (inside one block the numbers ascend by exactly 1, and the block laid
down next belongs to an exception earlier in the chain, which owns strictly lower
numbers, since the report consumes the innermost cause first), so the consumption
ORDER is read off the verbatim impl region's own result, with no order-revealing
substitute helper; (4) `frames_from_traceback(chain, k)` against the REAL
extracted generator `get_exception_traceback_frames`, per exception, by length and
by chain location number, the real side re-encoded through each node's TRUE
owner, so a block served from the wrong exception disagrees; (5) read-only input
(`Acc(list_pred(trace_lens), 1/2)`) — the shadow's input list compared before and
after every call.

**Inputs: 100 799 chains** satisfying `Requires(trace_lens[k] >= 0)` — the real
FAIL_TO_PASS scenario replayed from the test's own source (`[1, 0]` → 1 frame),
20 named boundaries, an EXHAUSTIVE sweep of the sub-domain `len <= 4` × entries
in `{0,1,2}` × all link-kind patterns (778 chains; the full modeled domain is
infinite, so this is a floor the fuzz extends past), and 100 000 seeded fuzz
chains (length 0..6, per-exception length 0..5 with empty traces at ~35 %, 0..2
hidden nodes, random link kinds). 587 391 real frames compared. Every branch of
both impl regions taken in both directions.

**Pinned seed: `SEED = 13513`** (module constant; the chain shuffler uses
`13513 ^ 0x5EED`).

**Recorded verdict: `G-CONF=pass`**, 0 disagreements, on Django 3.2.0 with the
gold applied.

**Capability-to-fail, confirmed by negative controls** (run out-of-tree against
these exact script bytes; the bundle is unmodified):
- gold NOT applied (real code = the buggy pre-patch coupled walk) → FAIL, first
  witness the F2P shape `[1, 0]`: shadow 1 vs real 0. This is the bug the patch
  repairs, so the check discriminates patched from unpatched.
- shadow mutant "stop at the first empty contribution" (the pre-patch bug
  injected into the shadow) → FAIL on `[1, 0]`: shadow 0 vs real 1.
- shadow mutant "skip the outermost exception" → FAIL on `[1, 0]`: shadow 0 vs
  real 1.
- shadow mutant "off-by-one in `frames_from_traceback`" → keeps the count and
  FAILS observable (2) on `[1, 0]`: real `[0]` vs shadow `[1]`.
- shadow mutant "consume the chain in FORWARD order" → keeps the count exactly
  and FAILS observable (2) on `[2, 0, 3]`: real `[2, 3, 4, 0, 1]` vs shadow
  `[0, 1, 2, 3, 4]`.
- shadow mutant "serve one block from an EQUAL-LENGTH SIBLING" — the provenance
  family: draw the outermost exception's block from the innermost one whenever the
  two record equally long traces → keeps the count AND every per-exception block
  length exactly right, and FAILS observable (2) on `[2, 0, 2]`: real
  `[2, 3, 0, 1]` vs shadow `[0, 1, 0, 1]`. This mutant is why the comparison is
  elementwise over location numbers rather than over block lengths alone, and it
  is the shape obligation 4 of `model.py` (ATTRIBUTION) rules out.
- bridge mutant "ignore `__traceback_hide__`" → FAIL as BRIDGE on `[0]`: the real
  chain walk derives `[1]` where the model input was `[0]`.
