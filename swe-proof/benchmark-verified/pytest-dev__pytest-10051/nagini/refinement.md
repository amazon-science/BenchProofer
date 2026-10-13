# refinement.md — pytest-dev__pytest-10051

The operation-by-operation correspondence between `model.py`'s implementation
(the `discard_captured` and `append_then_visible` impl regions, and the consumed
`empty_in_place` axiom) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed**, the proof
uses the axiom's `Ensures`, or **A-reference**, a deep model validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reset site — `LogCaptureFixture.clear` → `LogCaptureHandler.clear`

Gold hunks (`src/_pytest/logging.py`):

```
# new method on the handler (after reset, around :345):
+    def clear(self) -> None:
+        self.records.clear()
+        self.stream = StringIO()

# the fixture's clear (around :443):
     def clear(self) -> None:
         """Reset the list of log records and the captured log text."""
-        self.handler.reset()
+        self.handler.clear()
```

Pre-patch the fixture's `clear` calls `handler.reset()` whose body is
`self.records = []` (`:344-345`) — a **rebind** to a fresh empty list. The fix
routes the fixture's `clear` to a new `handler.clear()` whose body is
`self.records.clear()` — an **in-place** emptying that preserves the list
object's identity.

| # | model.py impl op (`discard_captured`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `buf: CaptureBuffer`, field `buf.items: List[int]` | the `LogCaptureHandler` self and `self.records: List[logging.LogRecord]` | R | `LogCaptureHandler` ↔ minimal `CaptureBuffer`; the captured-items field `records` ↔ `items`; `List[LogRecord]` ↔ `List[int]` (mapping.md §2). Only the touched field is carried. |
| A2 | param `view: List[int]` with `Requires(view is buf.items)` | the per-phase reference `stash[caplog_records_key][when]` (set `:699` to `caplog_handler.records`) surfaced by `get_records(when)` (`:388`/`:399`) | R | the external observer's reference; it IS the same list object as `handler.records` from phase wiring. Object aliasing (`is`) is preserved 1:1 (mapping.md §2). |
| A3 | `empty_in_place(buf.items)` | `self.records.clear()` (the body of the new `handler.clear`, reached via `self.handler.clear()`) | A-consumed | the unchanged builtin `list.clear()` empties the list in place; its `Ensures(len==0 ∧ xs is Old(xs))` is consumed to discharge the postcondition. The fix's behavioural content — "empty WITHOUT replacing the object" — is the `xs is Old(xs)` clause of this axiom plus the spec's identity postconditions A4/A5. (mapping.md §3.1; G-AX checks it against real `list.clear`.) |
| A4 | `Ensures(len(buf.items) == 0)` | the records list is empty after `clear()` | I + A-consumed | follows directly from `empty_in_place`'s `len==0`. Matches the kept assertion `assert not len(caplog.records)` (P2P `test_clear`) and the F2P `caplog.get_records("call") == []`. |
| A5 | `Ensures(buf.items is Old(buf.items))` and `Ensures(view is buf.items)` | the records list object's identity is preserved, so the stash/`get_records` reference still names it | I + A-consumed | the discriminating clause. `empty_in_place` preserves identity (`xs is Old(xs)`); the buggy `reset()` rebinds, breaking it. This is exactly the bug the F2P `test_clear_for_call_stage` observes (`get_records("call")` stays aliased to the live, now-empty `records`). `model_prepatch` reproduces the rebind and FAILS here (G-DIFF). |

## B. The subsequent-capture site — `LogCaptureHandler.emit`

The F2P test logs again after `clear()` and asserts `get_records("call")` now
holds the new record. This is the second half of "the alias still tracks the
buffer": once identity is preserved, an append to the buffer is visible through
the observer reference.

| # | model.py impl op (`append_then_visible`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `buf.items.append(item)` | `self.records.append(record)` (`LogCaptureHandler.emit`, `:341`) | I + R | identical `.append`; `LogRecord` ↔ `int` (R). `emit` is unchanged by the patch; it is modeled to show the post-`clear` consequence the F2P test checks. |
| B2 | `Ensures(view is buf.items ∧ len(view)==1 ∧ view[0]==item)` | `get_records("call")` (the still-aliased reference) sees the newly emitted record | I | because A5 preserved identity, `view` names the live list, so the append is visible through it. This is the second F2P assertion after the post-`clear` log. |

`append_then_visible` carries no new axiom; it is pure structure/aliasing logic
over the same `CaptureBuffer` object. Its precondition `view is buf.items ∧
len==0` is exactly the post-state `discard_captured` establishes (A4/A5), so the
two functions compose into the full F2P scenario: clear → empty+aliased →
log → visible through the alias.

## C. The unmodeled side of the reset — `self.stream = StringIO()`

The new `handler.clear` also does `self.stream = StringIO()` (the captured-text
side), identical to what `handler.reset` already did. It is **observationally
untouched by the bug→fix delta**: both the buggy `reset` and the fixed `clear`
reset the stream the same way, and the F2P `test_clear_for_call_stage` only
observes the records-list aliasing. It is therefore not modeled (mapping.md §1
note). This is NOT a kind-3 step — it is an *identical* op on both sides of the
delta, outside the modeled behaviour, so it carries no verification obligation.

## C2. Termination (total correctness)

Nagini is a partial-correctness verifier by default: without an explicit
obligation, an implementation that never returns (bare self-recursion, or an
endless loop before/after doing the work) satisfies every `Ensures` vacuously
— and its translated patch would hang or blow the stack instead of resolving
(this is exactly the same-spec attack class `atk_*_recursion_discard.py` /
`atk_*_empty_then_recurse.py` exhibited in the earlier audit). The real
operations always return: `LogCaptureHandler.clear` is one builtin call plus a
field write, and `emit` is one `.append`. The spec therefore carries
`Requires(MustTerminate(2))` on both `discard_captured` and
`append_then_visible`, and `Requires(MustTerminate(1))` on the consumed
`empty_in_place` axiom (the builtin `list.clear()` always terminates; its
measure 1 is strictly below the callers' measure 2, so a caller may consume
the primitive but may NOT re-invoke itself — Nagini's obligation leak check
rejects a self-call at equal-or-higher measure, and rejects a nonterminating
loop). This closes the divergence loophole without constraining any
terminating behaviour: any straight-line implementation discharges
`MustTerminate(2)` trivially.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — emptying the records list **in place** (identity-preserving) instead
of **rebinding** it — is captured by the spec's identity postconditions
(`buf.items is Old(buf.items)`, `view is buf.items`, A5) discharged via the
`empty_in_place` axiom about the **unchanged** builtin `list.clear()` the new
code calls. There is no axiom about the function under change
(`LogCaptureFixture.clear` / the new `LogCaptureHandler.clear`) — those are the
modeled function `discard_captured` itself. The only consumed axiom covers an
unchanged language builtin; its soundness (in-place emptying preserves object
identity) is the load-bearing fact and is audited by G-AX.

## E. verify(model) ⇒ resolved

`discard_captured` verifies only if, after the reset, the records list is empty
(A4) AND its object identity is preserved so the observer reference still names
it (A5) — the exact property the bug violates and the F2P
`test_clear_for_call_stage` checks. `append_then_visible` verifies only if a
subsequently captured item is visible through that preserved reference (B2). By
R (LogCaptureHandler ↔ CaptureBuffer, LogRecord ↔ int, the stash/`get_records`
reference ↔ `view`) and A-consumed (`empty_in_place` == real `list.clear`,
G-AX), a model satisfying this spec, refined by the map above, is the gold patch
up to type refinement and the one audited builtin — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX on `list.clear`) and refinement fidelity (this document, G-EQ).
