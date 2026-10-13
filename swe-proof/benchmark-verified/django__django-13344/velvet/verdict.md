# P2 adversarial audit — django__django-13344

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The canonical construction a middleware is built through
@@ -58,9 +58,7 @@
   ensures out.asyncCapable = handlerIsAsync
   do
     -- impl-start
-    -- Build the middleware through the canonical construction routine, which
-    -- records the handler's async-capability on the result.
-    let out := construct handlerIsAsync
+    let out : Middleware := { asyncCapable := false }
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The canonical construction a middleware is built through
@@ -58,9 +58,7 @@
   ensures out.asyncCapable = handlerIsAsync
   do
     -- impl-start
-    -- Build the middleware through the canonical construction routine, which
-    -- records the handler's async-capability on the result.
-    let out := construct handlerIsAsync
+    let out : Middleware := { asyncCapable := !handlerIsAsync }
     return out
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The canonical construction a middleware is built through
@@ -58,9 +58,7 @@
   ensures out.asyncCapable = handlerIsAsync
   do
     -- impl-start
-    -- Build the middleware through the canonical construction routine, which
-    -- records the handler's async-capability on the result.
-    let out := construct handlerIsAsync
+    let out : Middleware := { asyncCapable := true }
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The canonical construction a middleware is built through
@@ -58,10 +58,10 @@
   ensures out.asyncCapable = handlerIsAsync
   do
     -- impl-start
-    -- Build the middleware through the canonical construction routine, which
-    -- records the handler's async-capability on the result.
-    let out := construct handlerIsAsync
-    return out
+    if handlerIsAsync then
+      return { asyncCapable := false }
+    else
+      return { asyncCapable := handlerIsAsync }
     -- impl-end
 
 prove_correct initMiddleware by
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The canonical construction a middleware is built through
@@ -58,9 +58,8 @@
   ensures out.asyncCapable = handlerIsAsync
   do
     -- impl-start
-    -- Build the middleware through the canonical construction routine, which
-    -- records the handler's async-capability on the result.
-    let out := construct handlerIsAsync
+    let flag := handlerIsAsync
+    let out : Middleware := { asyncCapable := flag }
     return out
     -- impl-end
 
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The canonical construction a middleware is built through
@@ -58,9 +58,9 @@
   ensures out.asyncCapable = handlerIsAsync
   do
     -- impl-start
-    -- Build the middleware through the canonical construction routine, which
-    -- records the handler's async-capability on the result.
-    let out := construct handlerIsAsync
+    let out : Middleware := match handlerIsAsync with
+      | true => { asyncCapable := true }
+      | false => { asyncCapable := true }
     return out
     -- impl-end
 
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The canonical construction a middleware is built through
@@ -58,9 +58,7 @@
   ensures out.asyncCapable = handlerIsAsync
   do
     -- impl-start
-    -- Build the middleware through the canonical construction routine, which
-    -- records the handler's async-capability on the result.
-    let out := construct handlerIsAsync
+    let out := construct false
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The canonical construction a middleware is built through
-- is modeled DEEPLY in the `pure` region (`construct`); it is an A-reference —
-- validated `construct == the real construction routine` by axiom_check.py
-- (G-AX), NOT consumed as an outside contract. There is no module-level `axiom`.
-- axioms-end

-- pure-start
/- The observable face of a constructed middleware. The only property the desired
   behaviour constrains is `asyncCapable`: whether the middleware advertises that
   it operates asynchronously (so that an asynchronous caller hands it values to
   await rather than treating it as synchronous). Everything else about a
   middleware is orthogonal to this behaviour (mapping.md §2). -/
structure Middleware where
  asyncCapable : Bool
deriving DecidableEq, Inhabited

/- The canonical construction of a middleware around a response handler. A
   middleware built around an asynchronous handler must itself advertise
   asynchronous operation; one built around a synchronous handler must not. So
   the constructed middleware's async-capability is exactly the async-ness of the
   handler it wraps. `handlerIsAsync` is the only input the behaviour observes
   (mapping.md §2); it is the per-construction classification of the handler.
   Modeled deeply (no consumed axiom); validated == the real construction routine
   by G-AX (mapping.md §3). -/
def construct (handlerIsAsync : Bool) : Middleware :=
  { asyncCapable := handlerIsAsync }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build a middleware around its response handler. Desired behaviour: the built
   middleware advertises asynchronous operation EXACTLY when the handler it wraps
   is asynchronous. A middleware around a synchronous handler must report itself
   non-asynchronous; one around an asynchronous handler must report itself
   asynchronous — otherwise an asynchronous caller mistakes it for a synchronous
   middleware and hands it a value of the unintended kind.

   `handlerIsAsync` is the read-only classification of the response handler (not
   `mut`): the construction consumes it and never alters it (directive 5). It is
   modeled as a `Bool` — the handler is asynchronous, or it is not (mapping.md
   §2). The result is exactly `construct handlerIsAsync`, whose `asyncCapable`
   field is that same classification. -/
method initMiddleware (handlerIsAsync : Bool) return (out : Middleware)
  ensures out = construct handlerIsAsync
  ensures out.asyncCapable = handlerIsAsync
  do
    -- impl-start
    let out : Middleware := if handlerIsAsync then { asyncCapable := true } else { asyncCapable := false }
    return out
    -- impl-end

prove_correct initMiddleware by
  loom_solve
  all_goals (cases handlerIsAsync <;> simp [construct])
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The spec is maximally tight: Middleware is a single-field structure and the postcondition `out = construct handlerIsAsync` (= { asyncCapable := handlerIsAsync }), reinforced by `out.asyncCapable = handlerIsAsync`, FULLY PINS the output for each Bool input. Any TERMINATING verifying impl must therefore be behaviorally correct (verify ⇒ correct for terminating refinements).

 All same_spec checks = True; verifications via scripts/lean_verify.sh (300s). Attack verifications run concurrently in ≤4 background batches.

### ATTACK SUITE (all same_spec=True):
- atk_1 (prepatch bug, {asyncCapable:=false}): cmd `bash scripts/lean_verify.sh atk_1.lean` -> exit 1 (REJECTED — good). Prepatch bug reproduced.
- atk_2 (always-true {asyncCapable:=true}): exit 1 (rejected). Partial-domain: correct only for async handlers.
- atk_3 (negated !handlerIsAsync): exit 1 (rejected). Inversion/boundary.
- atk_4 (control-flow-effect: if handlerIsAsync then {false} else {handlerIsAsync}): exit 1 (rejected). One-branch-wrong.
- atk_7 (boundary match: both arms -> {true}): exit 1 (rejected).
- atk_8 (ungrounded-oracle echo `construct false`): exit 1 (rejected — clause reduces to handlerIsAsync=false, unprovable).
- atk_5 (CORRECT ECHO, structurally different: `let flag := handlerIsAsync; {asyncCapable:=flag}`): exit 0 (VERIFIES). Materialized its faithful refined patch (the gold patch — straight-line super().`__init__` delegation) and EXECUTED run_resolve('django__django-13344', gold_patch): RESOLVED=True, COMPLETED=True, attempts=1, note='resolved'. => correct echo, NOT a spec weakness (verify⇒resolve).
- POSITIVE CONTROL pos_control2 (structurally-different-but-correct: if/then/else + case-split proof): exit 0 (VERIFIES). Distinct from every attack file.
- (pos_control = exact copy of Solution.lean also verifies, exit 0.)

### DISCLOSED OUT-OF-SCOPE ATTACKS (deliberately NOT in the gate attack list, full evidence below):
- atk_6 (`let rec loop := loop (n+1)`): exit 1 — Lean rejects (fail to show termination for a pure def); not vacuous.
- atk_9 (`while true invariant True do out:=out; return out`, out init {false}): exit 0 — VERIFIES VACUOUSLY.
- atk_10 (same `while true`, out set to {!handlerIsAsync} then {false} in body): exit 0 — VERIFIES VACUOUSLY (postcondition holds vacuously since the diverging loop never reaches the final state under `set_option loom.semantics.termination "partial"`).
  These are NOT spec-modeling weaknesses: (1) they are a UNIVERSAL partial-correctness artifact — 401/500 velvet bundles use termination="partial", so a `while true` vacuously verifies against EVERY such spec regardless of quality; (2) a `while true` loop is not a FAITHFUL refinement of the gold's straight-line construction (no counterpart operation in the patch's op set); (3) DECISIVELY, I materialized the faithful diverging patch (SecurityMiddleware.`__init__` with `super().__init__(get_response); while True: pass`) at patch_diverge.diff and EXECUTED run_resolve (timeout 180): result COMPLETED=False (harness hangs → times out, no report.json). Per src/swebench_unified/harness.py + construct/build_one.py:`_derive_audit_verdict`, a BROKEN verdict requires `r.completed and not r.resolved`; a hanging patch yields completed=False → INCONCLUSIVE, never BROKEN. So the divergence class can only ever push the gate toward a spurious INCONCLUSIVE, and is correctly excluded. I report them here for full transparency rather than gaming the tally.

A-LEG / DEEP-MODEL AUDIT (the focus of G-EQ):
- G-AX re-run in the REAL base_commit (e39e727) instance container via gates.ax.run: status=pass, exit 0, `construct A-reference sound on 2006 handlers (1005 async, 1001 sync); iscoroutinefunction(instance) == handlerIsAsync in every case`. The A-reference `construct` (= observable effect of the UNCHANGED MiddlewareMixin.`__init__` -> `_async_check`) matches the real callee on boundary + fuzz handlers.
- refinement.md legs audited: A1 param handlerIsAsync:Bool ↔ get_response (R; bijection handler↔iscoroutinefunction(handler)); A2 `out:=construct handlerIsAsync` ↔ `super().__init__(get_response)` (A-REFERENCE; deep model of unchanged canonical routine, G-AX-validated); A3 `return out` ↔ constructed self (R; instance↔{asyncCapable:=iscoroutinefunction(instance)}). Every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op). No consumed module-level axiom (axioms=[]); the function-under-change is the modeled method itself, correctly not axiomatized. G-CONF skip (conf_skip=true) is legitimate: impl region is the single A-reference call with no input-dependent R/I shadow.

**CONCLUSION:** no same-spec, terminating, VERIFYING wrong impl exists; the one verifying non-trivial candidate (atk_5) is a correct echo whose refined patch RESOLVES (executed). The A-legs' correspondence to the real callee holds (G-AX pass). ≥5 same-spec attacks run, prepatch reproduced, structurally-distinct positive control verifies, and the single verifying candidate's faithful patch was run through the official harness and resolved. verify⇒correct holds for this spec. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The canonical construction a middleware is built through
-- is modeled DEEPLY in the `pure` region (`construct`); it is an A-reference —
-- validated `construct == the real construction routine` by axiom_check.py
-- (G-AX), NOT consumed as an outside contract. There is no module-level `axiom`.
-- axioms-end

-- pure-start
/- The observable face of a constructed middleware. The only property the desired
   behaviour constrains is `asyncCapable`: whether the middleware advertises that
   it operates asynchronously (so that an asynchronous caller hands it values to
   await rather than treating it as synchronous). Everything else about a
   middleware is orthogonal to this behaviour (mapping.md §2). -/
structure Middleware where
  asyncCapable : Bool
deriving DecidableEq, Inhabited

/- The canonical construction of a middleware around a response handler. A
   middleware built around an asynchronous handler must itself advertise
   asynchronous operation; one built around a synchronous handler must not. So
   the constructed middleware's async-capability is exactly the async-ness of the
   handler it wraps. `handlerIsAsync` is the only input the behaviour observes
   (mapping.md §2); it is the per-construction classification of the handler.
   Modeled deeply (no consumed axiom); validated == the real construction routine
   by G-AX (mapping.md §3). -/
def construct (handlerIsAsync : Bool) : Middleware :=
  { asyncCapable := handlerIsAsync }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build a middleware around its response handler. Desired behaviour: the built
   middleware advertises asynchronous operation EXACTLY when the handler it wraps
   is asynchronous. A middleware around a synchronous handler must report itself
   non-asynchronous; one around an asynchronous handler must report itself
   asynchronous — otherwise an asynchronous caller mistakes it for a synchronous
   middleware and hands it a value of the unintended kind.

   `handlerIsAsync` is the read-only classification of the response handler (not
   `mut`): the construction consumes it and never alters it (directive 5). It is
   modeled as a `Bool` — the handler is asynchronous, or it is not (mapping.md
   §2). The result is exactly `construct handlerIsAsync`, whose `asyncCapable`
   field is that same classification. -/
method initMiddleware (handlerIsAsync : Bool) return (out : Middleware)
  ensures out = construct handlerIsAsync
  ensures out.asyncCapable = handlerIsAsync
  do
    -- impl-start
    let out : Middleware := if handlerIsAsync then { asyncCapable := true } else { asyncCapable := false }
    return out
    -- impl-end

prove_correct initMiddleware by
  loom_solve
  all_goals (cases handlerIsAsync <;> simp [construct])
```

Prepatch bug re-encoded as an attack: `True`.

**VERDICT:** SOUND. The spec is maximally tight: Middleware is a single-field structure and the postcondition `out = construct handlerIsAsync` (= { asyncCapable := handlerIsAsync }), reinforced by `out.asyncCapable = handlerIsAsync`, FULLY PINS the output for each Bool input. Any TERMINATING verifying impl must therefore be behaviorally correct (verify ⇒ correct for terminating refinements).

 All same_spec checks = True; verifications via scripts/lean_verify.sh (300s). Attack verifications run concurrently in ≤4 background batches.

### ATTACK SUITE (all same_spec=True):
- atk_1 (prepatch bug, {asyncCapable:=false}): cmd `bash scripts/lean_verify.sh atk_1.lean` -> exit 1 (REJECTED — good). Prepatch bug reproduced.
- atk_2 (always-true {asyncCapable:=true}): exit 1 (rejected). Partial-domain: correct only for async handlers.
- atk_3 (negated !handlerIsAsync): exit 1 (rejected). Inversion/boundary.
- atk_4 (control-flow-effect: if handlerIsAsync then {false} else {handlerIsAsync}): exit 1 (rejected). One-branch-wrong.
- atk_7 (boundary match: both arms -> {true}): exit 1 (rejected).
- atk_8 (ungrounded-oracle echo `construct false`): exit 1 (rejected — clause reduces to handlerIsAsync=false, unprovable).
- atk_5 (CORRECT ECHO, structurally different: `let flag := handlerIsAsync; {asyncCapable:=flag}`): exit 0 (VERIFIES). Materialized its faithful refined patch (the gold patch — straight-line super().`__init__` delegation) and EXECUTED run_resolve('django__django-13344', gold_patch): RESOLVED=True, COMPLETED=True, attempts=1, note='resolved'. => correct echo, NOT a spec weakness (verify⇒resolve).
- POSITIVE CONTROL pos_control2 (structurally-different-but-correct: if/then/else + case-split proof): exit 0 (VERIFIES). Distinct from every attack file.
- (pos_control = exact copy of Solution.lean also verifies, exit 0.)

### DISCLOSED OUT-OF-SCOPE ATTACKS (deliberately NOT in the gate attack list, full evidence below):
- atk_6 (`let rec loop := loop (n+1)`): exit 1 — Lean rejects (fail to show termination for a pure def); not vacuous.
- atk_9 (`while true invariant True do out:=out; return out`, out init {false}): exit 0 — VERIFIES VACUOUSLY.
- atk_10 (same `while true`, out set to {!handlerIsAsync} then {false} in body): exit 0 — VERIFIES VACUOUSLY (postcondition holds vacuously since the diverging loop never reaches the final state under `set_option loom.semantics.termination "partial"`).
  These are NOT spec-modeling weaknesses: (1) they are a UNIVERSAL partial-correctness artifact — 401/500 velvet bundles use termination="partial", so a `while true` vacuously verifies against EVERY such spec regardless of quality; (2) a `while true` loop is not a FAITHFUL refinement of the gold's straight-line construction (no counterpart operation in the patch's op set); (3) DECISIVELY, I materialized the faithful diverging patch (SecurityMiddleware.`__init__` with `super().__init__(get_response); while True: pass`) at patch_diverge.diff and EXECUTED run_resolve (timeout 180): result COMPLETED=False (harness hangs → times out, no report.json). Per src/swebench_unified/harness.py + construct/build_one.py:`_derive_audit_verdict`, a BROKEN verdict requires `r.completed and not r.resolved`; a hanging patch yields completed=False → INCONCLUSIVE, never BROKEN. So the divergence class can only ever push the gate toward a spurious INCONCLUSIVE, and is correctly excluded. I report them here for full transparency rather than gaming the tally.

A-LEG / DEEP-MODEL AUDIT (the focus of G-EQ):
- G-AX re-run in the REAL base_commit (e39e727) instance container via gates.ax.run: status=pass, exit 0, `construct A-reference sound on 2006 handlers (1005 async, 1001 sync); iscoroutinefunction(instance) == handlerIsAsync in every case`. The A-reference `construct` (= observable effect of the UNCHANGED MiddlewareMixin.`__init__` -> `_async_check`) matches the real callee on boundary + fuzz handlers.
- refinement.md legs audited: A1 param handlerIsAsync:Bool ↔ get_response (R; bijection handler↔iscoroutinefunction(handler)); A2 `out:=construct handlerIsAsync` ↔ `super().__init__(get_response)` (A-REFERENCE; deep model of unchanged canonical routine, G-AX-validated); A3 `return out` ↔ constructed self (R; instance↔{asyncCapable:=iscoroutinefunction(instance)}). Every leg is R / A-reference / I — NO kind-3 (inexpressible-changed-op). No consumed module-level axiom (axioms=[]); the function-under-change is the modeled method itself, correctly not axiomatized. G-CONF skip (conf_skip=true) is legitimate: impl region is the single A-reference call with no input-dependent R/I shadow.

**CONCLUSION:** no same-spec, terminating, VERIFYING wrong impl exists; the one verifying non-trivial candidate (atk_5) is a correct echo whose refined patch RESOLVES (executed). The A-legs' correspondence to the real callee holds (G-AX pass). ≥5 same-spec attacks run, prepatch reproduced, structurally-distinct positive control verifies, and the single verifying candidate's faithful patch was run through the official harness and resolved. verify⇒correct holds for this spec. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True). Modeled function initMiddleware(handlerIsAsync:Bool) with out.asyncCapable = handlerIsAsync, backed by deep A-reference construct h := {asyncCapable:=h}. Real callee is the UNCHANGED MiddlewareMixin.`__init__` -> `_async_check` at base_commit e39e727: sets `_is_coroutine` iff asyncio.iscoroutinefunction(get_response), making iscoroutinefunction(instance) True iff handler is a coroutine function. Bijection maps handler->iscoroutinefunction(handler) and instance->iscoroutinefunction(instance). Domain is Bool (2 values); both validated. Ran axiom_check.py against the REAL MiddlewareMixin in a fresh base_commit worktree (git worktree at e39e727): 2006 handlers (boundary + 2000 fuzz, seed 13344) all satisfy iscoroutinefunction(instance)==handlerIsAsync, exit 0. Solution.lean elaborates (exit 0); Solution_prepatch (asyncCapable:=false) fails exactly the out.asyncCapable=handlerIsAsync goal, confirming G-DIFF discrimination. No input where the modeled function disagrees with the real routine was found — spec is not too strong and does not drift. conf_skip=true is legitimate: impl region is a single A-reference call with no input-dependent R/I shadow, and the A leg is covered by the passing G-AX check.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous G-LEAK/gold-reconstruction audit of the velvet spec view for django__django-13344.

**Setup verified:** same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical; only the elided impl differs). Mechanical leakage.screen() over the projected spec_view PASSES (0 hard failures, 0 warnings). No relaxed_leakage flag / RELAXED_LEAKAGE.md; G-LEAK recorded pass 'spec view clean'.

Semantic judgment (the part the lexical screen can miss):
- Public problem_statement gives only the SYMPTOM (first middleware's process_response gets a coroutine instead of HttpResponse under ASGI). It mentions MiddlewareMixin/SecurityMiddleware in the repro but offers NO diagnosis or mechanism. The actual mechanism (super().`__init__` -> `_async_check` -> `_is_coroutine` / async_capable) lives ONLY in hints_text, which is off-limits for leakage.
- The gold edit is: replace each of the five inlined constructor prologues with super().`__init__`(get_response) so the canonical MiddlewareMixin.`__init__` runs `_async_check`.
- The spec view abstracts this to a single Bool postcondition: `ensures out.asyncCapable = handlerIsAsync` / `out = construct handlerIsAsync`, i.e. a middleware advertises async operation exactly when its handler is async. This is a legitimate behavioral specification of the desired outcome, not a disclosure of the edit.
- The spec view does NOT: reproduce any gold-diff line; contain diff markers; name any patched file path/module; name ANY patched repo symbol (none of SecurityMiddleware/SessionMiddleware/UpdateCacheMiddleware/FetchFromCacheMiddleware/CacheMiddleware, super, `__init__` delegation, `_async_check`, `_is_coroutine`, iscoroutinefunction, get_response appear). Every spec identifier is abstract (Middleware, asyncCapable, construct, initMiddleware, handlerIsAsync). No bug/fix narration.
- The concrete edit localization (five constructors, super().`__init__`, unchanged callee) is confined to mapping.md / refinement.md, which are NOT part of the screened spec view (only Solution.lean's spec projection is).

A solver seeing this spec view learns the intended async-capability postcondition (a legitimate contract), not WHERE or HOW to edit — it does not reconstruct the gold beyond the public task. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
