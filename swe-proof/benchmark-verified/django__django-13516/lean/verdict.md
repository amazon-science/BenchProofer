# P2 adversarial audit — django__django-13516

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,8 +55,7 @@
 
 -- impl-start
 def implementation_flush (s : OutStream) : OutStream := Id.run do
-  if s.hasFlush then
-    return { s with flushCount := s.flushCount + 1 }
+  -- WRONG: absorb flush as no-op even when supported (prepatch bug)
   return s
 -- impl-end
 
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
 -- impl-start
 def implementation_flush (s : OutStream) : OutStream := Id.run do
   if s.hasFlush then
-    return { s with flushCount := s.flushCount + 1 }
+    return { s with flushCount := s.flushCount + 2 }
   return s
 -- impl-end
 
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,8 +56,8 @@
 -- impl-start
 def implementation_flush (s : OutStream) : OutStream := Id.run do
   if s.hasFlush then
-    return { s with flushCount := s.flushCount + 1 }
-  return s
+    return s
+  return { s with flushCount := s.flushCount + 1 }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
 
 -- impl-start
 def implementation_flush (s : OutStream) : OutStream := Id.run do
-  if s.hasFlush then
+  if s.hasFlush && (s.flushCount % 2 == 0) then
     return { s with flushCount := s.flushCount + 1 }
   return s
 -- impl-end
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,9 +55,7 @@
 
 -- impl-start
 def implementation_flush (s : OutStream) : OutStream := Id.run do
-  if s.hasFlush then
-    return { s with flushCount := s.flushCount + 1 }
-  return s
+  return { s with flushCount := s.flushCount + 1 }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
 -- impl-start
 def implementation_flush (s : OutStream) : OutStream := Id.run do
   if s.hasFlush then
-    return { s with flushCount := s.flushCount + 1 }
+    return { hasFlush := false, flushCount := s.flushCount + 1 }
   return s
 -- impl-end
 
```

Attack 7 — `atk7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,10 +54,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_flush (s : OutStream) : OutStream := Id.run do
-  if s.hasFlush then
-    return { s with flushCount := s.flushCount + 1 }
-  return s
+def implementation_flush (s : OutStream) : OutStream :=
+  { hasFlush := s.hasFlush, flushCount := if s.hasFlush then s.flushCount + 1 else s.flushCount }
 -- impl-end
 
 -- proof-start
@@ -65,5 +63,5 @@
     ∀ (s : OutStream), problem_spec_flush s (implementation_flush s) := by
   intro s
   unfold problem_spec_flush implementation_flush
-  by_cases h : s.hasFlush <;> simp [Id.run, pure, bind, h]
+  by_cases h : s.hasFlush <;> simp [h]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Forwarding a flush request through a thin stream wrapper to the stream it wraps.

A wrapper sits in front of an underlying output stream and relays operations to
it. When a caller asks the wrapper to flush, the request must reach the
underlying stream so that any buffered output is pushed out immediately, rather
than being held back until later.

The underlying stream is observed through two things:

  * whether it actually supports flushing at all; and
  * how many times its own flush operation has been invoked.

The desired behavior of a single flush request on the wrapper:

  * if the underlying stream supports flushing, its flush operation is invoked
    exactly once (so a caller's flush is honored immediately);
  * if it does not support flushing, nothing happens to it;
  * either way, whether the stream supports flushing is itself unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two observable
-- operations involved — testing whether the underlying stream supports flushing,
-- and invoking that stream's flush once — are modeled structurally over the
-- stream's observables (its flush-support flag and its flush-invocation count),
-- so the specification needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The underlying stream, restricted to the two touched observables:
* `hasFlush` — whether the stream supports a flush operation at all;
* `flushCount` — how many times the stream's own flush operation has been
  invoked. -/
structure OutStream where
  hasFlush : Bool
  flushCount : Nat
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The underlying stream's observable state after one flush request on the
wrapper is fully pinned to its prior state:

  * the support flag is unchanged (`result.hasFlush = s.hasFlush`);
  * the flush-invocation count goes up by exactly one when the stream supports
    flushing, and is left unchanged otherwise. -/
def problem_spec_flush (s : OutStream) (result : OutStream) : Prop :=
  result.hasFlush = s.hasFlush ∧
  result.flushCount = (if s.hasFlush then s.flushCount + 1 else s.flushCount)
-- post-conditions-end

-- impl-start
def implementation_flush (s : OutStream) : OutStream := Id.run do
  if s.hasFlush then
    return { s with flushCount := s.flushCount + 1 }
  return s
-- impl-end

-- proof-start
theorem correct_flush :
    ∀ (s : OutStream), problem_spec_flush s (implementation_flush s) := by
  intro s
  unfold problem_spec_flush implementation_flush
  by_cases h : s.hasFlush <;> simp [Id.run, pure, bind, h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_flush FULLY pins both fields of result for every input s: result.hasFlush = s.hasFlush AND result.flushCount = (if s.hasFlush then s.flushCount+1 else s.flushCount). This is a TOTAL FUNCTIONAL postcondition — exactly one result value satisfies it per s — so any impl proving correct_flush for all s must be extensionally equal to the gold function. axioms=[], deep_model_references=[]; impl region is all R/I per refinement.md (G-CONF-covered). There are NO A-legs to attack; the only falsification vector is a behaviorally-wrong impl that still satisfies the tight functional spec, which is impossible here.

same_spec: all 7 attacks + positive control checked True on lean backend (spec regions byte-identical; only impl+proof region edited).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently in 2 background batches of 4):
- atk1 (prepatch bug re-encoded: always no-op `return s`): EXIT 1 (proof fails — neg branch cannot show flushCount+1). DOES NOT verify.
- atk2 (boundary/off-by-one: +2 when supported): EXIT 1 (goal reduces to False). DOES NOT verify.
- atk3 (inverted branch: increment only when NOT supported): EXIT 1. DOES NOT verify.
- atk4 (partial-domain: increment only when flushCount even): EXIT 1 (residual conditional goal). DOES NOT verify.
- atk5 (control-flow-effect: always increment regardless of support): EXIT 1. DOES NOT verify.
- atk6 (frame violation: sets hasFlush:=false when supported): EXIT 1 (hasFlush frame goal False). DOES NOT verify.
- atk7 (ungrounded-oracle echo: literally returns the spec-pinned record value): EXIT 0 VERIFIES. `#print axioms correct_flush` (file atk7_ax.lean) => depends on axioms: [propext] only (no sorryAx/native_decide) — CLEAN.

PROTOCOL STEP 2: atk7 is the ONLY same-spec impl whose proof closes with clean axioms. It computes exactly the gold function, so its faithful refined patch is the gold flush method (materialized as atk7_patch.diff, identical to frozen dataset gold). RAN through official harness: `run_resolve('django__django-13516', patch, run_id='sbu-audit-eq-k4k9qx90-atk7')` => RESOLVED: True, note='resolved'. The verifying impl's faithful patch RESOLVES — no verify⇏correct break.

POSITIVE CONTROL: pos.lean (=bundle Solution.lean) EXIT 0, axioms [propext] clean.

PREPATCH: Solution_prepatch.lean (no-op impl) EXIT 1 — bug reproduced (matches G-DIFF meta 'verification failed').

REFINEMENT.MD AUDIT: 3 legs, all tagged R/I (op1 flag test R, op2 count increment R, op3 else no-op I). No kind-3, no A-consumed/A-reference legs (nothing to axiomatize; hasattr test + flush invocation modeled structurally over OutStream observables, differential-tested by conformance_check.py vs REAL patched OutputWrapper.flush, 100000 inputs 0 disagreements). axiom_check.py is a legitimate skip stub (no consumed callee axiom). Correspondence holds.

CONCLUSION: 6 distinct genuinely-wrong impls (partial-domain, boundary×2, control-flow-effect×2, frame violation) all FAIL to verify against the tight functional spec; the single verifying same-spec impl (grounded oracle echo) has a materialized faithful patch that RESOLVES under the harness. Spec is airtight. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Forwarding a flush request through a thin stream wrapper to the stream it wraps.

A wrapper sits in front of an underlying output stream and relays operations to
it. When a caller asks the wrapper to flush, the request must reach the
underlying stream so that any buffered output is pushed out immediately, rather
than being held back until later.

The underlying stream is observed through two things:

  * whether it actually supports flushing at all; and
  * how many times its own flush operation has been invoked.

The desired behavior of a single flush request on the wrapper:

  * if the underlying stream supports flushing, its flush operation is invoked
    exactly once (so a caller's flush is honored immediately);
  * if it does not support flushing, nothing happens to it;
  * either way, whether the stream supports flushing is itself unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The two observable
-- operations involved — testing whether the underlying stream supports flushing,
-- and invoking that stream's flush once — are modeled structurally over the
-- stream's observables (its flush-support flag and its flush-invocation count),
-- so the specification needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- The underlying stream, restricted to the two touched observables:
* `hasFlush` — whether the stream supports a flush operation at all;
* `flushCount` — how many times the stream's own flush operation has been
  invoked. -/
structure OutStream where
  hasFlush : Bool
  flushCount : Nat
deriving DecidableEq
-- pure-end

-- post-conditions-start
/-- The underlying stream's observable state after one flush request on the
wrapper is fully pinned to its prior state:

  * the support flag is unchanged (`result.hasFlush = s.hasFlush`);
  * the flush-invocation count goes up by exactly one when the stream supports
    flushing, and is left unchanged otherwise. -/
def problem_spec_flush (s : OutStream) (result : OutStream) : Prop :=
  result.hasFlush = s.hasFlush ∧
  result.flushCount = (if s.hasFlush then s.flushCount + 1 else s.flushCount)
-- post-conditions-end

-- impl-start
def implementation_flush (s : OutStream) : OutStream := Id.run do
  if s.hasFlush then
    return { s with flushCount := s.flushCount + 1 }
  return s
-- impl-end

-- proof-start
theorem correct_flush :
    ∀ (s : OutStream), problem_spec_flush s (implementation_flush s) := by
  intro s
  unfold problem_spec_flush implementation_flush
  by_cases h : s.hasFlush <;> simp [Id.run, pure, bind, h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_flush FULLY pins both fields of result for every input s: result.hasFlush = s.hasFlush AND result.flushCount = (if s.hasFlush then s.flushCount+1 else s.flushCount). This is a TOTAL FUNCTIONAL postcondition — exactly one result value satisfies it per s — so any impl proving correct_flush for all s must be extensionally equal to the gold function. axioms=[], deep_model_references=[]; impl region is all R/I per refinement.md (G-CONF-covered). There are NO A-legs to attack; the only falsification vector is a behaviorally-wrong impl that still satisfies the tight functional spec, which is impossible here.

same_spec: all 7 attacks + positive control checked True on lean backend (spec regions byte-identical; only impl+proof region edited).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <file>`, run concurrently in 2 background batches of 4):
- atk1 (prepatch bug re-encoded: always no-op `return s`): EXIT 1 (proof fails — neg branch cannot show flushCount+1). DOES NOT verify.
- atk2 (boundary/off-by-one: +2 when supported): EXIT 1 (goal reduces to False). DOES NOT verify.
- atk3 (inverted branch: increment only when NOT supported): EXIT 1. DOES NOT verify.
- atk4 (partial-domain: increment only when flushCount even): EXIT 1 (residual conditional goal). DOES NOT verify.
- atk5 (control-flow-effect: always increment regardless of support): EXIT 1. DOES NOT verify.
- atk6 (frame violation: sets hasFlush:=false when supported): EXIT 1 (hasFlush frame goal False). DOES NOT verify.
- atk7 (ungrounded-oracle echo: literally returns the spec-pinned record value): EXIT 0 VERIFIES. `#print axioms correct_flush` (file atk7_ax.lean) => depends on axioms: [propext] only (no sorryAx/native_decide) — CLEAN.

PROTOCOL STEP 2: atk7 is the ONLY same-spec impl whose proof closes with clean axioms. It computes exactly the gold function, so its faithful refined patch is the gold flush method (materialized as atk7_patch.diff, identical to frozen dataset gold). RAN through official harness: `run_resolve('django__django-13516', patch, run_id='sbu-audit-eq-k4k9qx90-atk7')` => RESOLVED: True, note='resolved'. The verifying impl's faithful patch RESOLVES — no verify⇏correct break.

POSITIVE CONTROL: pos.lean (=bundle Solution.lean) EXIT 0, axioms [propext] clean.

PREPATCH: Solution_prepatch.lean (no-op impl) EXIT 1 — bug reproduced (matches G-DIFF meta 'verification failed').

REFINEMENT.MD AUDIT: 3 legs, all tagged R/I (op1 flag test R, op2 count increment R, op3 else no-op I). No kind-3, no A-consumed/A-reference legs (nothing to axiomatize; hasattr test + flush invocation modeled structurally over OutStream observables, differential-tested by conformance_check.py vs REAL patched OutputWrapper.flush, 100000 inputs 0 disagreements). axiom_check.py is a legitimate skip stub (no consumed callee axiom). Correspondence holds.

CONCLUSION: 6 distinct genuinely-wrong impls (partial-domain, boundary×2, control-flow-effect×2, frame violation) all FAIL to verify against the tight functional spec; the single verifying same-spec impl (grounded oracle echo) has a materialized faithful patch that RESOLVES under the harness. Spec is airtight. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) verdict: FAITHFUL — the modeled function agrees with the real patched callee on every in-domain input.

Evidence:
1. same_spec (swebench_unified.markers, LeanBackend.language tables) over Solution.lean vs Solution_prepatch.lean = True; spec region (imports/docstring/axioms/pure/post-conditions) byte-identical, only impl+proof differ.
2. lean_verify.sh Solution.lean exit 0 (compiles, no sorry). #print axioms correct_flush => [propext] only; no sorryAx, proof is real.
3. Real repo: (HEAD 2c7846d, patched worktree) OutputWrapper.flush = `if hasattr(self._out,'flush'): self._out.flush()`. Model: OutStream(hasFlush:Bool, flushCount:Nat); problem_spec_flush pins result.hasFlush=s.hasFlush AND result.flushCount = (if s.hasFlush then s.flushCount+1 else s.flushCount). This exactly mirrors: support test unchanged (frame), invoke underlying flush exactly once iff supported.
4. G-CONF (conformance_check.py) run with against the REAL patched OutputWrapper.flush: 'G-CONF OK: 100000 inputs, 0 disagreements', exit 0.
5. Direct probes: supported stream -> flush called exactly once, hasattr unchanged; unsupported stream -> no-op, hasattr stays False. Both match spec.

Spec is NOT too strong: it is precisely discriminating. The prepatch no-op impl (real bug) violates the 'count advances by one iff supported' clause, matching the failing F2P test test_outputwrapper_flush (asserts mocked flush.called is True). So the spec is neither over-constraining beyond the gold behavior nor under-constraining.

Modeling-boundary note (not a defect): a pathological underlying object with a NON-callable `flush` attribute makes hasattr True yet the real method raises TypeError, whereas the model would say the count advances. This input is outside the modeled domain (hasFlush denotes 'supports flushing' = has an invocable flush), is unreachable by the F2P test (StringIO with a real callable flush mock), and represents the standard legitimate abstraction boundary. It does not constitute an unfaithful divergence on any realistic/in-domain stream.

Conclusion: FAITHFUL — no in-domain diverging input exists between the spec model and the real repo callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen passes (leakage.screen -> PASSED, no hard failures). Semantic review of the solver-visible spec view (impl+proof elided) confirms no leak beyond the public problem_statement. The gold edit adds OutputWrapper.flush() {if hasattr(self._out,'flush'): self._out.flush()} in django/core/management/base.py. Spec view: (1) contains NO patched file path (base.py), NO patched repo symbols OutputWrapper/_out/__getattr__/hasattr, NO diff markers, NO reproduced gold line; (2) the only patched symbol 'flush' is already public via the problem_statement ('flush() ... doesn't work' during migrate); (3) spec identifiers OutStream/hasFlush/flushCount/problem_spec_flush are modeling names, not repo symbols; (4) comments are abstract behavioral prose (thin wrapper forwarding a flush to the underlying stream) with no bug/fix narration and no mention of the base-commit __getattr__/TextIOBase no-op subtlety. The post-condition (hasFlush frame + flushCount +1 iff supported) is a legitimate WHAT-must-hold specification of flush semantics; it does not localize the edit (no file/method placement, no hasattr/delegation idiom), so a solver must still discover the fault site and code. refinement.md/mapping.md quote the gold hunk and file path but are auditor-only artifacts, not part of the spec view, so they do not affect this gate.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
