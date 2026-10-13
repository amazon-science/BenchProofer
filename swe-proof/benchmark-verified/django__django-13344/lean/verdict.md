# P2 adversarial audit — django__django-13344

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_6_ax.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,16 +78,11 @@
 
 -- impl-start
 def implementation_initComponent (handler : Option Handler) : Component := Id.run do
-  -- raise the "missing handler" notice when no handler is supplied
   let mut missingFlag := false
   if handler.isNone then
     missingFlag := true
-  -- keep the handler the component was built from
   let stored := handler
-  -- asynchronous-capability check: report async exactly when the handler is async
-  let mut async := false
-  if handlerIsAsync stored then
-    async := true
+  let async := false
   return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,16 +78,11 @@
 
 -- impl-start
 def implementation_initComponent (handler : Option Handler) : Component := Id.run do
-  -- raise the "missing handler" notice when no handler is supplied
   let mut missingFlag := false
   if handler.isNone then
     missingFlag := true
-  -- keep the handler the component was built from
   let stored := handler
-  -- asynchronous-capability check: report async exactly when the handler is async
-  let mut async := false
-  if handlerIsAsync stored then
-    async := true
+  let async := !handler.isNone
   return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
 -- impl-end
 
@@ -100,6 +95,6 @@
   | none => exact ⟨rfl, rfl, rfl⟩
   | some h =>
     by_cases hb : h.isAsync <;>
-      simp only [handlerIsAsync, hb, Id.run, if_true] <;>
+      simp only [handlerIsAsync, hb, Id.run] <;>
       exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,13 +78,8 @@
 
 -- impl-start
 def implementation_initComponent (handler : Option Handler) : Component := Id.run do
-  -- raise the "missing handler" notice when no handler is supplied
-  let mut missingFlag := false
-  if handler.isNone then
-    missingFlag := true
-  -- keep the handler the component was built from
+  let missingFlag := handler.isSome
   let stored := handler
-  -- asynchronous-capability check: report async exactly when the handler is async
   let mut async := false
   if handlerIsAsync stored then
     async := true
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,15 +78,12 @@
 
 -- impl-start
 def implementation_initComponent (handler : Option Handler) : Component := Id.run do
-  -- raise the "missing handler" notice when no handler is supplied
   let mut missingFlag := false
   if handler.isNone then
     missingFlag := true
-  -- keep the handler the component was built from
-  let stored := handler
-  -- asynchronous-capability check: report async exactly when the handler is async
+  let stored : Option Handler := none
   let mut async := false
-  if handlerIsAsync stored then
+  if handlerIsAsync handler then
     async := true
   return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,16 +78,11 @@
 
 -- impl-start
 def implementation_initComponent (handler : Option Handler) : Component := Id.run do
-  -- raise the "missing handler" notice when no handler is supplied
   let mut missingFlag := false
   if handler.isNone then
     missingFlag := true
-  -- keep the handler the component was built from
   let stored := handler
-  -- asynchronous-capability check: report async exactly when the handler is async
-  let mut async := false
-  if handlerIsAsync stored then
-    async := true
+  let async := handler.isNone
   return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
 -- impl-end
 
@@ -100,6 +95,6 @@
   | none => exact ⟨rfl, rfl, rfl⟩
   | some h =>
     by_cases hb : h.isAsync <;>
-      simp only [handlerIsAsync, hb, Id.run, if_true] <;>
+      simp only [handlerIsAsync, hb, Id.run] <;>
       exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk_6_ax.lean` → not a counterexample (changed the spec)

```diff
@@ -78,28 +78,20 @@
 
 -- impl-start
 def implementation_initComponent (handler : Option Handler) : Component := Id.run do
-  -- raise the "missing handler" notice when no handler is supplied
   let mut missingFlag := false
   if handler.isNone then
     missingFlag := true
-  -- keep the handler the component was built from
   let stored := handler
-  -- asynchronous-capability check: report async exactly when the handler is async
-  let mut async := false
-  if handlerIsAsync stored then
-    async := true
+  let async := false
   return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
 -- impl-end
 
 -- proof-start
+axiom oracle_cheat : ∀ handler : Option Handler,
+    problem_spec_initComponent handler (implementation_initComponent handler)
 theorem correct_initComponent : ∀ handler : Option Handler,
-    problem_spec_initComponent handler (implementation_initComponent handler) := by
-  intro handler
-  unfold problem_spec_initComponent implementation_initComponent
-  cases handler with
-  | none => exact ⟨rfl, rfl, rfl⟩
-  | some h =>
-    by_cases hb : h.isAsync <;>
-      simp only [handlerIsAsync, hb, Id.run, if_true] <;>
-      exact ⟨rfl, rfl, rfl⟩
+    problem_spec_initComponent handler (implementation_initComponent handler) :=
+  oracle_cheat
 -- proof-end
+
+#print axioms correct_initComponent
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,16 +78,12 @@
 
 -- impl-start
 def implementation_initComponent (handler : Option Handler) : Component := Id.run do
-  -- raise the "missing handler" notice when no handler is supplied
   let mut missingFlag := false
   if handler.isNone then
     missingFlag := true
-  -- keep the handler the component was built from
   let stored := handler
-  -- asynchronous-capability check: report async exactly when the handler is async
-  let mut async := false
-  if handlerIsAsync stored then
-    async := true
+  -- always report async (over-eager) — wrong on none and on sync handlers
+  let async := true
   return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
 -- impl-end
 
@@ -100,6 +96,6 @@
   | none => exact ⟨rfl, rfl, rfl⟩
   | some h =>
     by_cases hb : h.isAsync <;>
-      simp only [handlerIsAsync, hb, Id.run, if_true] <;>
+      simp only [handlerIsAsync, hb, Id.run] <;>
       exact ⟨rfl, rfl, rfl⟩
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a request-processing component from its optional request handler.

A component is built from an optional handler. The component advertises that it
is capable of operating in an asynchronous fashion, but whether a *particular*
instance actually operates asynchronously must follow the handler it was built
from: an instance built from an asynchronous handler must itself report as
asynchronous, and an instance built from an ordinary (non-asynchronous) handler
must report as ordinary.

Construction is fully determined by the handler:

  * the constructed instance keeps exactly the handler it was given;
  * when no handler is supplied, construction raises a "missing handler"
    notice (and none otherwise);
  * the instance reports itself as asynchronous exactly when the handler it was
    built from is asynchronous.

The third component is the behavior at issue: an instance must not silently
default to "ordinary" regardless of its handler; it must reflect the handler's
asynchronous nature.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two effects the
-- constructor performs — emitting a notice when no handler is supplied, and
-- determining whether the handler is asynchronous — are modeled DEEPLY as
-- properties of the input handler (`Option.isNone` and `Handler.isAsync`),
-- not axiomatized. Their reference behavior is validated by G-CONF as
-- A-references. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A request handler, observed through the only property the constructor's
behavior depends on: whether it operates asynchronously. -/
structure Handler where
  /-- whether this handler operates asynchronously -/
  isAsync : Bool
deriving Repr, DecidableEq

/-- The constructed component. Its observable, construction-determined state:
the handler it was built from, whether a "missing handler" notice was raised,
and whether the instance reports itself as asynchronous. -/
structure Component where
  /-- the handler the component was built from -/
  handler : Option Handler
  /-- whether construction raised the "missing handler" notice -/
  missingHandlerFlagged : Bool
  /-- whether the instance reports itself as operating asynchronously -/
  reportsAsync : Bool
deriving Repr, DecidableEq

/-- Whether the (optional) handler operates asynchronously. A supplied handler
is asynchronous iff its own `isAsync` flag is set; the absence of a handler is
never asynchronous. -/
def handlerIsAsync : Option Handler → Bool
  | some h => h.isAsync
  | none => false
-- pure-end

-- post-conditions-start
/-- A constructed component is fully pinned to its input handler:
  * it keeps exactly the handler given (`result.handler = handler`);
  * the "missing handler" notice is raised exactly when no handler was supplied;
  * it reports as asynchronous exactly when its handler is asynchronous.
Directive 5 (frame): every output component is tied to the input — no field is
left free. Directive 8: each field is grounded in the actual input `handler`,
so the asynchronous report must be *produced by* inspecting the handler, not
defaulted. -/
def problem_spec_initComponent (handler : Option Handler) (result : Component) : Prop :=
  result.handler = handler ∧
  result.missingHandlerFlagged = handler.isNone ∧
  result.reportsAsync = handlerIsAsync handler
-- post-conditions-end

-- impl-start
def implementation_initComponent (handler : Option Handler) : Component := Id.run do
  -- raise the "missing handler" notice when no handler is supplied
  let mut missingFlag := false
  if handler.isNone then
    missingFlag := true
  -- keep the handler the component was built from
  let stored := handler
  -- asynchronous-capability check: report async exactly when the handler is async
  let mut async := false
  if handlerIsAsync stored then
    async := true
  return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
-- impl-end

-- proof-start
theorem correct_initComponent : ∀ handler : Option Handler,
    problem_spec_initComponent handler (implementation_initComponent handler) := by
  intro handler
  unfold problem_spec_initComponent implementation_initComponent
  cases handler with
  | none => exact ⟨rfl, rfl, rfl⟩
  | some h =>
    by_cases hb : h.isAsync <;>
      simp only [handlerIsAsync, hb, Id.run, if_true] <;>
      exact ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY FUNCTIONAL: problem_spec_initComponent pins all three Component fields to exact functions of the input (result.handler=handler AND missingHandlerFlagged=handler.isNone AND reportsAsync=handlerIsAsync handler). Exactly one correct output per input => any same-spec impl closing correct_initComponent with clean axioms must be behaviorally identical to gold, so verify=>correct is expected to hold. Attacks all same_spec=True (checked via markers.same_spec) with axioms/pure/pre/post regions byte-identical to gold (verified via region_text).

### RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- pos_control.lean: exit 0 (verifies); pos_control_ax.lean #print axioms => CLEAN [propext, Quot.sound].
- atk_1 (prepatch bug, async:=false; partial-domain wrong on async handler): exit 1, goal reduces to false=true. Reproduces the real prepatch bug.
- atk_2 (async := !handler.isNone; wrong on present-sync handler): exit 1, goal !isNone=false.
- atk_3 (missingHandlerFlagged := handler.isSome; flipped notice, control-flow-effect): exit 1, goal isSome=isNone.
- atk_4 (store none always; boundary/store corruption): exit 1, goal none=some h.
- atk_5 (async := handler.isNone; inverted domain): exit 1, goal isNone=true.
- atk_7 (async := true; over-eager, wrong on none/sync): exit 1, goal true=false.
All six are GENUINE unification failures (unclosable), not syntax errors.
- atk_6_ax (ungrounded-oracle echo: prepatch buggy impl closed via injected `axiom oracle_cheat`): exit 0 BUT #print axioms => DIRTY [oracle_cheat]. Rejected by the clean-axiom gate; not a real closing proof.

No wrong impl has a closing proof with CLEAN axioms, therefore NO faithful patch needed materializing/resolving (nothing could pass verify to then fail resolve). verify=>correct is not falsifiable on this bundle.

refinement.md audit: 5 rows, tags R(1)/A-reference(2,4)/I(3,5) — no kind-3 (changed-inexpressible). A-references correspond faithfully to the real callees: row2 notice <-> `get_response is None` (Option.isNone), row4 async-check <-> asyncio.iscoroutinefunction (Handler.isAsync). Both A-references validated by conformance_check.py (G-CONF, seed=13344, N=120000 >= 1e5, 0 disagreements by construction). No A-consumed callee-property axioms. Correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| changed the specification rather than only the implementation, so it does not test the specification this bundle ships | 1 | `atk_6_ax.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_ax.lean` → not a counterexample (changed the spec)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Constructing a request-processing component from its optional request handler.

A component is built from an optional handler. The component advertises that it
is capable of operating in an asynchronous fashion, but whether a *particular*
instance actually operates asynchronously must follow the handler it was built
from: an instance built from an asynchronous handler must itself report as
asynchronous, and an instance built from an ordinary (non-asynchronous) handler
must report as ordinary.

Construction is fully determined by the handler:

  * the constructed instance keeps exactly the handler it was given;
  * when no handler is supplied, construction raises a "missing handler"
    notice (and none otherwise);
  * the instance reports itself as asynchronous exactly when the handler it was
    built from is asynchronous.

The third component is the behavior at issue: an instance must not silently
default to "ordinary" regardless of its handler; it must reflect the handler's
asynchronous nature.
-/

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two effects the
-- constructor performs — emitting a notice when no handler is supplied, and
-- determining whether the handler is asynchronous — are modeled DEEPLY as
-- properties of the input handler (`Option.isNone` and `Handler.isAsync`),
-- not axiomatized. Their reference behavior is validated by G-CONF as
-- A-references. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- A request handler, observed through the only property the constructor's
behavior depends on: whether it operates asynchronously. -/
structure Handler where
  /-- whether this handler operates asynchronously -/
  isAsync : Bool
deriving Repr, DecidableEq

/-- The constructed component. Its observable, construction-determined state:
the handler it was built from, whether a "missing handler" notice was raised,
and whether the instance reports itself as asynchronous. -/
structure Component where
  /-- the handler the component was built from -/
  handler : Option Handler
  /-- whether construction raised the "missing handler" notice -/
  missingHandlerFlagged : Bool
  /-- whether the instance reports itself as operating asynchronously -/
  reportsAsync : Bool
deriving Repr, DecidableEq

/-- Whether the (optional) handler operates asynchronously. A supplied handler
is asynchronous iff its own `isAsync` flag is set; the absence of a handler is
never asynchronous. -/
def handlerIsAsync : Option Handler → Bool
  | some h => h.isAsync
  | none => false
-- pure-end

-- post-conditions-start
/-- A constructed component is fully pinned to its input handler:
  * it keeps exactly the handler given (`result.handler = handler`);
  * the "missing handler" notice is raised exactly when no handler was supplied;
  * it reports as asynchronous exactly when its handler is asynchronous.
Directive 5 (frame): every output component is tied to the input — no field is
left free. Directive 8: each field is grounded in the actual input `handler`,
so the asynchronous report must be *produced by* inspecting the handler, not
defaulted. -/
def problem_spec_initComponent (handler : Option Handler) (result : Component) : Prop :=
  result.handler = handler ∧
  result.missingHandlerFlagged = handler.isNone ∧
  result.reportsAsync = handlerIsAsync handler
-- post-conditions-end

-- impl-start
def implementation_initComponent (handler : Option Handler) : Component := Id.run do
  -- raise the "missing handler" notice when no handler is supplied
  let mut missingFlag := false
  if handler.isNone then
    missingFlag := true
  -- keep the handler the component was built from
  let stored := handler
  -- asynchronous-capability check: report async exactly when the handler is async
  let mut async := false
  if handlerIsAsync stored then
    async := true
  return { handler := stored, missingHandlerFlagged := missingFlag, reportsAsync := async }
-- impl-end

-- proof-start
theorem correct_initComponent : ∀ handler : Option Handler,
    problem_spec_initComponent handler (implementation_initComponent handler) := by
  intro handler
  unfold problem_spec_initComponent implementation_initComponent
  cases handler with
  | none => exact ⟨rfl, rfl, rfl⟩
  | some h =>
    by_cases hb : h.isAsync <;>
      simp only [handlerIsAsync, hb, Id.run, if_true] <;>
      exact ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS FULLY FUNCTIONAL: problem_spec_initComponent pins all three Component fields to exact functions of the input (result.handler=handler AND missingHandlerFlagged=handler.isNone AND reportsAsync=handlerIsAsync handler). Exactly one correct output per input => any same-spec impl closing correct_initComponent with clean axioms must be behaviorally identical to gold, so verify=>correct is expected to hold. Attacks all same_spec=True (checked via markers.same_spec) with axioms/pure/pre/post regions byte-identical to gold (verified via region_text).

### RESULTS (cmd: bash scripts/lean_verify.sh <f>):
- pos_control.lean: exit 0 (verifies); pos_control_ax.lean #print axioms => CLEAN [propext, Quot.sound].
- atk_1 (prepatch bug, async:=false; partial-domain wrong on async handler): exit 1, goal reduces to false=true. Reproduces the real prepatch bug.
- atk_2 (async := !handler.isNone; wrong on present-sync handler): exit 1, goal !isNone=false.
- atk_3 (missingHandlerFlagged := handler.isSome; flipped notice, control-flow-effect): exit 1, goal isSome=isNone.
- atk_4 (store none always; boundary/store corruption): exit 1, goal none=some h.
- atk_5 (async := handler.isNone; inverted domain): exit 1, goal isNone=true.
- atk_7 (async := true; over-eager, wrong on none/sync): exit 1, goal true=false.
All six are GENUINE unification failures (unclosable), not syntax errors.
- atk_6_ax (ungrounded-oracle echo: prepatch buggy impl closed via injected `axiom oracle_cheat`): exit 0 BUT #print axioms => DIRTY [oracle_cheat]. Rejected by the clean-axiom gate; not a real closing proof.

No wrong impl has a closing proof with CLEAN axioms, therefore NO faithful patch needed materializing/resolving (nothing could pass verify to then fail resolve). verify=>correct is not falsifiable on this bundle.

refinement.md audit: 5 rows, tags R(1)/A-reference(2,4)/I(3,5) — no kind-3 (changed-inexpressible). A-references correspond faithfully to the real callees: row2 notice <-> `get_response is None` (Option.isNone), row4 async-check <-> asyncio.iscoroutinefunction (Handler.isAsync). Both A-references validated by conformance_check.py (G-CONF, seed=13344, N=120000 >= 1e5, 0 disagreements by construction). No A-consumed callee-property axioms. Correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real callee). Model function under spec: MiddlewareMixin.__init__(get_response) at base_commit e39e727 (django/utils/deprecation.py lines 94-98), which the gold patch routes all five subclass constructors through via super().__init__(get_response).

Real callee semantics (base_commit source read from worktree): (1) _get_response_none_deprecation -> warns iff get_response is None; (2) self.get_response = get_response (verbatim store); (3) _async_check -> sets _is_coroutine iff asyncio.iscoroutinefunction(get_response).

Spec problem_spec_initComponent asserts exactly the three totalized postconditions: result.handler = handler; result.missingHandlerFlagged = handler.isNone; result.reportsAsync = handlerIsAsync handler (none->false). These are total, deterministic functions of the two observed predicates (is None, iscoroutinefunction) and agree with the real constructor on every input class: None (notice=true, async=false — matches iscoroutinefunction(None)=False), coroutine function (async=true), sync function / callable object / lambda (async=false). No input exists where the modeled function disagrees with the real repo callee, so the spec is not over-strong.

Checks performed: (a) same_spec(Solution, Solution_prepatch, lean_tables)=True — spec region (axioms/pure/pre/post) is byte-identical across the patch, so it is frozen and not tuned to the impl. (b) lean_verify.sh exit 0 (compiles, no sorry). (c) #print axioms correct_initComponent -> [propext, Quot.sound] only; no sorryAx — the proof is genuine, not fake. (d) conformance_check.py: R/I shadow vs independent reconstruction, 120005 inputs, 0 disagreements, seed 13344. (e) Discriminator is real: prepatch hard-codes async:=false and its proof cannot close against the frozen post-condition on an async handler (G-DIFF), matching F2P test_coroutine.

The handler abstraction (Option Handler carrying only isAsync : Bool) is a faithful projection: the constructor's behavior depends on the handler solely through iscoroutinefunction and the None test, both of which are captured. Subclass-specific settings reads are unchanged by the fix and orthogonal; correctly excluded from the model. Spec is FAITHFUL — no divergence found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: hard_failures=[], warnings=[]) and swebench_unified.markers.same_spec(Solution, Solution_prepatch) = True (spec region byte-identical). Semantic review of the spec view (docstring + Handler/Component structures + handlerIsAsync + problem_spec_initComponent post-conditions; impl and proof regions elided) confirms no reconstruction of the gold edit beyond the public problem_statement:

- Gold patch specifics are absent: none of the patched-symbol names (SecurityMiddleware, SessionMiddleware, UpdateCacheMiddleware, FetchFromCacheMiddleware, CacheMiddleware — all in _patch_changed_symbols), the mechanism (super().__init__(get_response), _async_check(), asyncio.iscoroutinefunction, _is_coroutine), or any file/module path appears in the spec view. The model is fully abstracted to Handler.isAsync / Component.reportsAsync.
- The behavioral contract 'reportsAsync = handlerIsAsync handler' encodes the required target behavior; encoding correct behavior is not leakage. The underlying symptom (async request handling / coroutine mishandling) is already public in problem_statement ('using ASGI ... the first middleware receives a coroutine as its response parameter').
- The docstring's 'behavior at issue' clause identifies which conjunct discriminates but discloses no gold localization or mechanism beyond the public async symptom. It contains none of the _NARRATION-flagged terms and names no patched repo symbol.
- The concrete root-cause vocabulary (_async_check, super().__init__, _is_coroutine) exists only in hints_text (correctly excluded from the public surface) and in auditor-only mapping.md / refinement.md, which are NOT part of the screened spec view.

The spec view leaks nothing about the edit that a solver could not already derive from problem_statement. No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
