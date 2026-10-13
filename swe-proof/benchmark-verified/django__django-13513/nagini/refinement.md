# refinement.md — django__django-13513

The operation-by-operation correspondence between `model.py`'s implementation
(`assemble_frames` + `frames_from_traceback` + the deep `chain_total` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee/operation by axiom_check.py / G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The per-exception generator — `get_exception_traceback_frames`

Gold hunk: extracts a generator that walks ONE exception's traceback and yields
one frame per node:
```
+ def get_exception_traceback_frames(self, exc_value, tb):
+     ...
      while tb is not None:
          ...
-         frames.append({...})
+         yield {...}
-         if not tb.tb_next and exceptions:
-             exc_value = exceptions.pop()
-             tb = exc_value.__traceback__
-         else:
-             tb = tb.tb_next
+         tb = tb.tb_next
```

| # | model.py impl op (`frames_from_traceback`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `chain: PSeq[int]`, `k: int` | `exc_value` and `tb` (the exception and its own traceback object) | R | the real generator is passed BOTH the exception it serves and that exception's traceback (`debug.py:427`, `:430-431`); the model names the exception by its chain position `k` and its traceback by `chain[k]`, the visible-node count (mapping.md §2). The count alone would not name an exception — it is many-to-one — so the position is what carries identity. |
| A2 | `start = locations_before(chain, k)`; `while i < trace_len: result.append(start + i)` | `while tb is not None: yield {...}; tb = tb.tb_next` | R + I | the gold loop emits exactly one entry per traceback node, in `tb_next` order, walking to exhaustion; the modeled loop emits exactly `chain[k]` entries, in the same order, each naming the chain location the corresponding node IS. The node-walk ↔ the bounded count is the type refinement, and node ↔ chain location number is the entry-level one (mapping.md §2). The `__traceback_hide__` skip removes individual nodes and is folded into the visible-node count (mapping.md §2). |
| A3 | post `len(Result()) == chain[k]` and `Result()[j] == locations_before(chain, k) + j` | the generator yields one dict per node of THAT exception's traceback, in order | R | two observables, not one. The F2P obligation reads the entry count (`len(frames)`); the P2P lane reads the entries themselves, and a real frame dict is drawn from two independent sources — the OWNER `exc_value` (`exc_cause` / `exc_cause_explicit`, `debug.py:436-437` → `:459-460`) and the NODE `tb` (`filename` / `function` / `lineno` / `module_name`, `debug.py:445-449` → `:461-471`). A chain location number is injective in the pair (owning exception, index of the node within its own visible trace), so one int per entry preserves both readings and pins the block to the exception whose turn it is. |

## B. The cross-chain assembly — `get_traceback_frames`

Gold hunk: the single coupled `while tb is not None` traversal (with the inner
`if not tb.tb_next and exceptions:` exception-advancement) is replaced by an
explicit per-exception accumulation:
```
  exc_value = exceptions.pop()
  tb = self.tb if not exceptions else exc_value.__traceback__
+ frames.extend(self.get_exception_traceback_frames(exc_value, tb))
+ while exceptions:
+     exc_value = exceptions.pop()
+     frames.extend(self.get_exception_traceback_frames(
+         exc_value, exc_value.__traceback__))
+ return frames
-     ... single coupled while-loop, advancing exceptions only from inside ...
- return frames
```

| # | model.py impl op (`assemble_frames`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `trace_lens: List[int]` | the `exceptions` list (chain order) | R | each exception ↔ its trace length; the list ↔ `List[int]` (mapping.md §2). |
| B2 | `if n == 0: return frames` | `if not exceptions: return frames` | I | the empty-chain early return, identical. |
| B3 | backward index walk `i = n … 1`, reading `trace_lens[i-1]` | `exceptions.pop()` (innermost first) then `while exceptions: exceptions.pop()` | R | popping from the end ↔ the descending index; the innermost popped (`tb = self.tb if not exceptions else exc_value.__traceback__`) and every remaining exception are each visited exactly once, **unconditionally** (mapping.md §2). |
| B4 | `contribution = frames_from_traceback(ToSeq(trace_lens), i-1)`; `frames.extend(contribution)` | `frames.extend(self.get_exception_traceback_frames(exc_value, tb))` for each exception | R + I | each exception's own contribution is computed independently by the per-exception helper (step A) and concatenated; `extend` ↔ `extend`. The helper is told WHICH exception of this chain it serves, mirroring the real call, which is passed the popped `exc_value` together with that same exception's traceback — so a block cannot be drawn from a different exception. The helper is the modeled `frames_from_traceback`, so this is a call to a function-under-spec (not an axiom). |
| B5 | post `len(Result()) == chain_total(ToSeq(trace_lens))` | the total `frames` returned | A-reference | the changed cross-chain accumulation is modeled **deeply**: `chain_total` (the spelled-out front-recursive SUM in the `pure` region) and the verified backward loop ARE the accumulation. There is no consumed assembly axiom — the proof never depends on one. The deep model is validated **== the real gold assembly** out-of-band: G-AX (axiom_check.py) reproduces the gold control flow and asserts `chain_total == real frame count` on boundary + fuzz, and drives the REAL gold-era `ExceptionReporter` on the F2P scenario (mapping.md §3.1). |
| B6 | post `Result()[p] == entry_location(ToSeq(trace_lens), p)` | the ORDER and PROVENANCE of the `frames` list the two `extend` calls build | R | the real report is the per-exception blocks in consumption order — the innermost popped exception first (`debug.py:425-427`), then each remaining exception as `while exceptions:` pops it (`:429-432`) — with each block internally in `tb_next` order (`:439-473`). `entry_location` states exactly that shape over the chain, and because an entry names a chain location number owned by one exception alone (mapping.md §2), it pins for every position both which node the entry describes and which exception the block is attributed to. This is what rules out a block generated from a different exception of the chain, including one whose trace happens to record the same number of locations. |

The discriminating content of the change — **every exception contributes its own
frames independently, so an empty leading traceback no longer suppresses the
others** — lives in `chain_total(ToSeq(trace_lens)) == Σ trace_lens[k]` (model)
⇔ the unconditional per-exception `frames.extend(...)` accumulation (real), and
its companion **each block is the OWN trace of the exception whose turn it is**
lives in `entry_location` (B6) ⇔ the real call passing each popped `exc_value`
together with that same exception's traceback. The
pre-patch coupled traversal advances to the next exception only from *inside*
the per-node loop, so on the chain `[1, 0]` (innermost popped trace empty) it
runs zero iterations and returns 0 frames; `model_prepatch.py` reproduces that
coupled single-pointer walk and **fails** the postcondition
`len(Result()) == chain_total(ToSeq(trace_lens))` (it gives 0, the spec requires
1), which is exactly the spec sensing the change (G-DIFF).

## C. The `explicit_or_implicit_cause` promotion (pure refactor, not modeled)

The gold patch also promotes the nested closure `explicit_or_implicit_cause` to
a method `_get_explicit_or_implicit_cause` (and reuses it). This is a pure
refactor of an identical expression with NO observable effect on the chain the
report walks or on the frame count; it is not a behavioural change and is not
modeled (no F2P-observable consequence). The behaviour it computes
(`__suppress_context__` respect) was already correct at this base_commit — the
*separate* issue 13513 fixes here is the dropped-frames bug (the
FAIL_TO_PASS test). (The `__suppress_context__` PEP-415 narrative in the problem
statement was addressed by an earlier change; the gold patch attached to THIS
instance and its single FAIL_TO_PASS test target the empty-innermost-traceback
frame-dropping behaviour, which is what the spec pins.)

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the cross-chain frame accumulation — is modeled **deeply** (the
spelled-out front-recursive sum `chain_total` consumed in `assemble_frames`,
step B5, an **A-reference**), not hidden behind an axiom about the function
under change: there is no consumed assembly axiom. There is no A-consumed axiom
in this bundle at all.

## E. verify(model) ⇒ resolved

`assemble_frames` verifies only if (i) its output length equals the exact
per-exception SUM `chain_total(ToSeq(trace_lens))` (B5) — i.e. every exception,
including those after an empty-traceback one, contributes its own entries — and
(ii) every position of its output carries the chain location `entry_location`
puts there (B6), so the blocks appear in consumption order, each block is
internally in trace order, and each block consists of location numbers owned by
the exception whose turn it is and by no other. By R (exception ↔ chain position
+ trace-node count; traceback node ↔ chain location number; list `extend` ↔
`extend`; `pop` ↔ descending index) the verified assembly equals the gold
`get_traceback_frames` /
`get_exception_traceback_frames` on the tested chains; by G-AX the deep model
`chain_total` equals the real gold assembly (A-reference) on boundary + 20 000
fuzz chains and on the live F2P scenario. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited deep-model reference — and the gold patch resolves (G-RESOLVE). The
single trust point is refinement fidelity (this document, G-EQ) plus the
A-reference soundness (G-AX); there is no consumed axiom.
