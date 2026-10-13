# refinement.md — pytest-dev__pytest-10051

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`clearCapture` `do` block) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. There are no A
legs in this bundle.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The clear site — in-place empty of the record buffer

Gold hunks (`src/_pytest/logging.py`):
```
# new in-place empty method on the record handler (lines 344-347):
+    def clear(self) -> None:
+        self.records.clear()
+        self.stream = StringIO()
# the fixture clear delegates to it instead of the rebinding reset (line 443):
-        self.handler.reset()
+        self.handler.clear()
```
The pre-patch `reset` (kept in the file, line 344-346) rebinds the list
(`self.records = []`); the patch routes the fixture's clear to a new method that
empties the SAME list object in place (`self.records.clear()`).

| # | Solution.lean impl op (`clearCapture`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `mut c : Capture` (`live`, `callId`, `callSnap`) | the handler + its per-phase reference state | R | `records` list ↔ `Buffer` (`id` ↔ `ident`, elements ↔ `contents`); the per-phase reference `stash[...][when]` ↔ `callId`/`callSnap` (mapping.md §2). |
| A2 | `require c.callId = c.live.ident` | post-setup invariant `stash[caplog_records_key][when] is handler.records` (`:699`) | R | the per-phase "call" reference is bound to the live list during phase prep, so on entry the two references denote the same object (mapping.md §2). |
| A3 | `c := { c with live := { c.live with contents := [] } }` — empty `live` in place, `ident` UNCHANGED | `self.records.clear()` (the new `clear` method) | I | in-place empty preserving object identity is exactly `contents := []` with `ident` left untouched. G-CONF transliterates this as `live.clear()` on the real list. |
| A4 | `ensures c.live.ident = cOld.live.ident` (identity frame, directive 5) | the patch's USE of `self.records.clear()` rather than `self.records = []` | I | the directive-5 frame: the buffer object must be PRESERVED, not replaced. This is the whole content of the fix — pinned as the unchanged frame of the `mut` carrier. |
| A5 | `ensures liveRecords c = []` and `ensures callRecords c = []` | the observable F2P guarantee: after clear, `caplog.get_records("call") == []` and stays linked to `caplog.records` | I | because the buffer identity is preserved (A4) and emptied (A3), both the live reference and the aliasing per-phase reference observe the empty sequence. |
| A6 | `ensures c.callId = cOld.callId`, `ensures c.callSnap = cOld.callSnap` | the per-phase reference binding is not touched by clear | R | clear only empties the buffer; the per-phase reference state is read-only here (directive-5: read-only `mut` fields pinned to their entry value). |

Discriminating content of the change — the buffer is emptied **in place**
(identity preserved) rather than **rebound** to a fresh object — lives in
`ensures c.live.ident = cOld.live.ident` together with `ensures callRecords c = []`
(model) ⇔ `self.records.clear()` vs the pre-patch `self.records = []` (real).
`Solution_prepatch.lean` reproduces the rebind (`live := { ident := old+1,
contents := [] }`) and **fails** exactly those two clauses (G-DIFF): the fresh
identity violates the frame, and the detached per-phase reference observes its
stale snapshot, so `callRecords c = []` is unprovable. The contents-empty clause
`liveRecords c = []` alone is satisfied by BOTH — value-equality cannot see the
bug; only the identity frame + the aliasing observation discriminate it.

## B. The `self.stream = StringIO()` sub-op — out of carrier

Both the pre-patch `reset` and the patched `clear` execute
`self.stream = StringIO()` identically; this resets the formatted-text stream,
an aspect orthogonal to the records-aliasing behaviour the F2P clause under test
(`get_records("call")`/`records`) observes. It is not part of the modeled
`Capture` carrier (mapping.md §3) and needs no separate step.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — emptying the
buffer in place instead of rebinding it — is modeled **deeply** as a record
update that preserves the identity token (`ident` unchanged) while clearing
`contents`, not hidden behind an axiom. There is no axiomatized callee and no
deep-model A-reference (meta.json `axioms = []`, `deep_model_references = []`):
the behaviour is fully self-contained over the observable capture state, so
`axiom_check.py` is a `status=skip` stub and G-AX has nothing to validate.

## C2. Termination semantics — total

The spec is stated under `loom.semantics.termination "total"` because the real
patched operation is straight-line code (`self.records.clear(); self.stream =
StringIO()` — no loops, no recursion, always returns). Under total-correctness
semantics a diverging impl body cannot vacuously discharge the postconditions,
so verify genuinely implies the terminating gold-observable final state. (Under
`"partial"` semantics a never-terminating body would satisfy every `ensures`
vacuously — a wrong impl the spec must not admit.)

## D. verify(Solution) ⇒ resolved

`clearCapture` verifies only if, on return, the live buffer's identity equals its
entry identity (A4), its contents are empty (A5), and — given the entry aliasing
`callId = live.ident` (A2) — the per-phase reference therefore also observes the
empty sequence (A5). By R (the `records` list ↔ `Buffer`, the per-phase
reference ↔ `callId`/`callSnap` bijections) the verified operation is exactly
`self.records.clear()` reached via the fixture clear delegating to the new
in-place method — i.e. the gold patch. By G-CONF the R/I transliteration of the
impl (in-place `live.clear()` on a real list whose per-phase reference aliases
it) agrees with `patch.diff`'s behaviour — the live/call-reference observation
pair — on ≥10⁵ inputs; the pre-patch rebind would diverge (the per-phase
reference observes stale records), which is precisely the F2P failure. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust
point is refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-
soundness trust point (no axioms).
