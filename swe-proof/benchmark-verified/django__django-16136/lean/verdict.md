# P2 adversarial audit — django__django-16136

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `problem_spec_disallowedResponse isAsync allowed result := result.awaitable = isAsync ∧ result.allowed = allowed` is a total conjunction of two equalities that uniquely pins BOTH fields of the DisallowedResponse for every input. The unique satisfying value is `{ awaitable := isAsync, allowed := allowed }` — exactly the patched Python behavior. The axioms region is a comment only (empty), so it cannot be weakened without breaking same_spec. No same-spec wrong impl can close correct_disallowedResponse; all 7 attacks failed to verify (exit 1, genuine unsolved goals). No verifying-but-wrong impl exists, hence no patch to run through resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,16 +35,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Build the "method not allowed" response from the permitted methods, then, when
-the view operates in asynchronous mode, hand back an awaitable wrapper around it;
-otherwise hand back the response directly. -/
+/-- ATTACK1 prepatch bug: never wrap. -/
 def implementation_disallowedResponse
     (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
-  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
-  if isAsync then
-    return { response with awaitable := true }
-  else
-    return response
+  return { awaitable := false, allowed := allowed }
 -- impl-end
 
 -- proof-start
@@ -54,5 +48,6 @@
       (implementation_disallowedResponse isAsync allowed) := by
   intro isAsync allowed
   unfold problem_spec_disallowedResponse implementation_disallowedResponse
-  cases isAsync <;> exact ⟨rfl, rfl⟩
+  simp only [Id.run, bind, pure]
+  cases isAsync <;> simp_all <;> first | rfl | (constructor <;> rfl) | simp_all
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,16 +35,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Build the "method not allowed" response from the permitted methods, then, when
-the view operates in asynchronous mode, hand back an awaitable wrapper around it;
-otherwise hand back the response directly. -/
+/-- ATTACK2 inverted control flow: wrap in sync, not async. -/
 def implementation_disallowedResponse
     (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
-  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
-  if isAsync then
-    return { response with awaitable := true }
-  else
-    return response
+  return { awaitable := !isAsync, allowed := allowed }
 -- impl-end
 
 -- proof-start
@@ -54,5 +48,6 @@
       (implementation_disallowedResponse isAsync allowed) := by
   intro isAsync allowed
   unfold problem_spec_disallowedResponse implementation_disallowedResponse
-  cases isAsync <;> exact ⟨rfl, rfl⟩
+  simp only [Id.run, bind, pure]
+  cases isAsync <;> simp_all <;> first | rfl | (constructor <;> rfl) | simp_all
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,16 +35,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Build the "method not allowed" response from the permitted methods, then, when
-the view operates in asynchronous mode, hand back an awaitable wrapper around it;
-otherwise hand back the response directly. -/
+/-- ATTACK3 partial-domain: always awaitable, correct only for isAsync=true. -/
 def implementation_disallowedResponse
     (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
-  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
-  if isAsync then
-    return { response with awaitable := true }
-  else
-    return response
+  return { awaitable := true, allowed := allowed }
 -- impl-end
 
 -- proof-start
@@ -54,5 +48,6 @@
       (implementation_disallowedResponse isAsync allowed) := by
   intro isAsync allowed
   unfold problem_spec_disallowedResponse implementation_disallowedResponse
-  cases isAsync <;> exact ⟨rfl, rfl⟩
+  simp only [Id.run, bind, pure]
+  cases isAsync <;> simp_all <;> first | rfl | (constructor <;> rfl) | simp_all
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,16 +35,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Build the "method not allowed" response from the permitted methods, then, when
-the view operates in asynchronous mode, hand back an awaitable wrapper around it;
-otherwise hand back the response directly. -/
+/-- ATTACK4 ungrounded payload: correct awaitable, drops allowed methods. -/
 def implementation_disallowedResponse
     (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
-  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
-  if isAsync then
-    return { response with awaitable := true }
-  else
-    return response
+  return { awaitable := isAsync, allowed := [] }
 -- impl-end
 
 -- proof-start
@@ -54,5 +48,6 @@
       (implementation_disallowedResponse isAsync allowed) := by
   intro isAsync allowed
   unfold problem_spec_disallowedResponse implementation_disallowedResponse
-  cases isAsync <;> exact ⟨rfl, rfl⟩
+  simp only [Id.run, bind, pure]
+  cases isAsync <;> simp_all <;> first | rfl | (constructor <;> rfl) | simp_all
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,16 +35,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Build the "method not allowed" response from the permitted methods, then, when
-the view operates in asynchronous mode, hand back an awaitable wrapper around it;
-otherwise hand back the response directly. -/
+/-- ATTACK5 boundary/order: reverse the permitted methods list. -/
 def implementation_disallowedResponse
     (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
-  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
-  if isAsync then
-    return { response with awaitable := true }
-  else
-    return response
+  return { awaitable := isAsync, allowed := allowed.reverse }
 -- impl-end
 
 -- proof-start
@@ -54,5 +48,6 @@
       (implementation_disallowedResponse isAsync allowed) := by
   intro isAsync allowed
   unfold problem_spec_disallowedResponse implementation_disallowedResponse
-  cases isAsync <;> exact ⟨rfl, rfl⟩
+  simp only [Id.run, bind, pure]
+  cases isAsync <;> simp_all <;> first | rfl | (constructor <;> rfl) | simp_all
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,16 +35,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Build the "method not allowed" response from the permitted methods, then, when
-the view operates in asynchronous mode, hand back an awaitable wrapper around it;
-otherwise hand back the response directly. -/
+/-- ATTACK6 control-flow-effect: only wrap when async AND non-empty payload. -/
 def implementation_disallowedResponse
     (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
-  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
-  if isAsync then
-    return { response with awaitable := true }
-  else
-    return response
+  return { awaitable := (isAsync && !allowed.isEmpty), allowed := allowed }
 -- impl-end
 
 -- proof-start
@@ -54,5 +48,6 @@
       (implementation_disallowedResponse isAsync allowed) := by
   intro isAsync allowed
   unfold problem_spec_disallowedResponse implementation_disallowedResponse
-  cases isAsync <;> exact ⟨rfl, rfl⟩
+  simp only [Id.run, bind, pure]
+  cases isAsync <;> simp_all <;> first | rfl | (constructor <;> rfl) | simp_all
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -35,16 +35,10 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Build the "method not allowed" response from the permitted methods, then, when
-the view operates in asynchronous mode, hand back an awaitable wrapper around it;
-otherwise hand back the response directly. -/
+/-- ATTACK7 echo/ungrounded: pick awaitable to satisfy allowed-eq only, wrong awaitable in sync. -/
 def implementation_disallowedResponse
     (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
-  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
-  if isAsync then
-    return { response with awaitable := true }
-  else
-    return response
+  return { awaitable := decide (allowed = allowed), allowed := allowed }
 -- impl-end
 
 -- proof-start
@@ -54,5 +48,6 @@
       (implementation_disallowedResponse isAsync allowed) := by
   intro isAsync allowed
   unfold problem_spec_disallowedResponse implementation_disallowedResponse
-  cases isAsync <;> exact ⟨rfl, rfl⟩
+  simp only [Id.run, bind, pure]
+  cases isAsync <;> simp_all <;> first | rfl | (constructor <;> rfl) | simp_all
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two values the handler
-- consults — whether the view operates in asynchronous mode, and the list of
-- permitted request methods carried by the response — are unchanged inputs and
-- are modeled as plain parameters, so nothing is abstracted behind a callee.
-- The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The object produced when a request uses a method the view does not permit.
It always denotes the standard "method not allowed" (HTTP 405) response and
carries the list of permitted method names. `awaitable` records whether the
returned object is an awaitable wrapper (to be resolved by the caller) rather
than the bare response value. -/
structure DisallowedResponse where
  /-- Whether the returned object must be awaited before the response is obtained. -/
  awaitable : Bool
  /-- The permitted request-method names carried by the response. -/
  allowed : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The handler must yield the "method not allowed" response carrying exactly the
permitted methods it was given, and that object must be an awaitable wrapper
precisely when the view operates in asynchronous mode (so the caller can resolve
it uniformly); in synchronous mode the bare response is returned directly. The
permitted-method payload is identical in both modes. -/
def problem_spec_disallowedResponse
    (isAsync : Bool) (allowed : List String) (result : DisallowedResponse) : Prop :=
  result.awaitable = isAsync ∧ result.allowed = allowed
-- post-conditions-end

-- impl-start
/-- Build the "method not allowed" response from the permitted methods, then, when
the view operates in asynchronous mode, hand back an awaitable wrapper around it;
otherwise hand back the response directly. -/
def implementation_disallowedResponse
    (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync then
    return { response with awaitable := true }
  else
    return response
-- impl-end

-- proof-start
theorem correct_disallowedResponse :
    ∀ (isAsync : Bool) (allowed : List String),
    problem_spec_disallowedResponse isAsync allowed
      (implementation_disallowedResponse isAsync allowed) := by
  intro isAsync allowed
  unfold problem_spec_disallowedResponse implementation_disallowedResponse
  cases isAsync <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec confirmed True for all 7 attacks and pos_control via swebench_unified.markers.same_spec (lean backend). Verifier: python; scripts/lean_verify.sh <file>.

### EXECUTED RESULTS (each: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time):
- pos_control.lean (gold impl): EXIT 0 (verifies, no sorry).
- #print axioms correct_disallowedResponse (axcheck.lean): 'correct_disallowedResponse does not depend on any axioms' — CLEAN, EXIT 0.
- atk_1.lean (prepatch bug: awaitable:=false always): EXIT 1 — unsolved goals (isAsync=true reduces to ⊢False). Prepatch bug reproduced / G-DIFF confirmed.
- atk_2.lean (inverted branch: awaitable:=!isAsync): EXIT 1 — unsolved goals.
- atk_3.lean (partial-domain: awaitable:=true always): EXIT 1 — unsolved goals.
- atk_4.lean (ungrounded payload: allowed:=[]): EXIT 1 — unsolved goals.
- atk_5.lean (boundary/order: allowed:=allowed.reverse): EXIT 1 — unsolved goals.
- atk_6.lean (control-flow-effect: awaitable:=isAsync && !allowed.isEmpty): EXIT 1 — unsolved goals.
- atk_7.lean (echo/ungrounded oracle: awaitable:=decide(allowed=allowed) i.e. always true): EXIT 1 — unsolved goals.
All failures are genuine 'simp_all made no progress'/unsolved-goals errors, not linter noise.

TACTIC-CAPABILITY CONTROL (rules out a broken-tactic false-negative): ctrl_tactic.lean = a CORRECT impl written differently (`{ awaitable := isAsync, allowed := allowed }`) proved with the EXACT SAME attack proof tactic used in atk_1..7 → EXIT 0. So the attack tactic can close a true impl; the 7 failures are attributable to the wrong impls, not to a weak tactic.

Attacks span the required families: prepatch bug (atk_1), control-flow-effect (atk_2, atk_6), partial-domain (atk_3), ungrounded-oracle echo (atk_4, atk_7), boundary/order (atk_5).

Since NO wrong impl produced a closing clean-axiom proof, there is nothing to materialize into a faithful patch / run through run_resolve. verify⇒correct holds here by construction: output uniquely determined by two equalities + empty axioms region.

refinement.md AUDIT: 5 legs. Rows 1,2 = R (bool/list type refinement of unchanged read-only inputs view_is_async / _allowed_methods, modeled as parameters). Row 3 = R/I (construct bare 405 response). Row 4 = R (the changed op: async branch wraps response as awaitable; asyncio.iscoroutine ↔ awaitable=true). Row 5 = I (sync bare return). NO A-consumed, NO A-reference legs (axioms region empty, G-AX skip stub) — consistent with mapping.md callee provenance: view_is_async and _allowed_methods are unchanged inputs, not abstracted callees. No kind-3 (changed-inexpressible) leg. A-leg correspondence vacuously holds (no A-legs). Correspondence to the real callees (HttpResponseNotAllowed payload, view_is_async, _allowed_methods) is faithful and contains no escape hatch. mapping.md Python callee cited: django/views/generic/base.py:144-151 http_method_not_allowed; matches patch.diff.

Verdict: SOUND — 7 same-spec wrong impls attacked (>=5 distinct families), none verify; positive control + tactic-capability control both verify; axioms clean; no verifying-wrong impl to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `problem_spec_disallowedResponse isAsync allowed result := result.awaitable = isAsync ∧ result.allowed = allowed` is a total conjunction of two equalities that uniquely pins BOTH fields of the DisallowedResponse for every input. The unique satisfying value is `{ awaitable := isAsync, allowed := allowed }` — exactly the patched Python behavior. The axioms region is a comment only (empty), so it cannot be weakened without breaking same_spec. No same-spec wrong impl can close correct_disallowedResponse; all 7 attacks failed to verify (exit 1, genuine unsolved goals). No verifying-but-wrong impl exists, hence no patch to run through resolve.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The two values the handler
-- consults — whether the view operates in asynchronous mode, and the list of
-- permitted request methods carried by the response — are unchanged inputs and
-- are modeled as plain parameters, so nothing is abstracted behind a callee.
-- The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The object produced when a request uses a method the view does not permit.
It always denotes the standard "method not allowed" (HTTP 405) response and
carries the list of permitted method names. `awaitable` records whether the
returned object is an awaitable wrapper (to be resolved by the caller) rather
than the bare response value. -/
structure DisallowedResponse where
  /-- Whether the returned object must be awaited before the response is obtained. -/
  awaitable : Bool
  /-- The permitted request-method names carried by the response. -/
  allowed : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The handler must yield the "method not allowed" response carrying exactly the
permitted methods it was given, and that object must be an awaitable wrapper
precisely when the view operates in asynchronous mode (so the caller can resolve
it uniformly); in synchronous mode the bare response is returned directly. The
permitted-method payload is identical in both modes. -/
def problem_spec_disallowedResponse
    (isAsync : Bool) (allowed : List String) (result : DisallowedResponse) : Prop :=
  result.awaitable = isAsync ∧ result.allowed = allowed
-- post-conditions-end

-- impl-start
/-- Build the "method not allowed" response from the permitted methods, then, when
the view operates in asynchronous mode, hand back an awaitable wrapper around it;
otherwise hand back the response directly. -/
def implementation_disallowedResponse
    (isAsync : Bool) (allowed : List String) : DisallowedResponse := Id.run do
  let response : DisallowedResponse := { awaitable := false, allowed := allowed }
  if isAsync then
    return { response with awaitable := true }
  else
    return response
-- impl-end

-- proof-start
theorem correct_disallowedResponse :
    ∀ (isAsync : Bool) (allowed : List String),
    problem_spec_disallowedResponse isAsync allowed
      (implementation_disallowedResponse isAsync allowed) := by
  intro isAsync allowed
  unfold problem_spec_disallowedResponse implementation_disallowedResponse
  cases isAsync <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

same_spec confirmed True for all 7 attacks and pos_control via swebench_unified.markers.same_spec (lean backend). Verifier: python; scripts/lean_verify.sh <file>.

### EXECUTED RESULTS (each: `bash scripts/lean_verify.sh <file>`, run concurrently ≤4 at a time):
- pos_control.lean (gold impl): EXIT 0 (verifies, no sorry).
- #print axioms correct_disallowedResponse (axcheck.lean): 'correct_disallowedResponse does not depend on any axioms' — CLEAN, EXIT 0.
- atk_1.lean (prepatch bug: awaitable:=false always): EXIT 1 — unsolved goals (isAsync=true reduces to ⊢False). Prepatch bug reproduced / G-DIFF confirmed.
- atk_2.lean (inverted branch: awaitable:=!isAsync): EXIT 1 — unsolved goals.
- atk_3.lean (partial-domain: awaitable:=true always): EXIT 1 — unsolved goals.
- atk_4.lean (ungrounded payload: allowed:=[]): EXIT 1 — unsolved goals.
- atk_5.lean (boundary/order: allowed:=allowed.reverse): EXIT 1 — unsolved goals.
- atk_6.lean (control-flow-effect: awaitable:=isAsync && !allowed.isEmpty): EXIT 1 — unsolved goals.
- atk_7.lean (echo/ungrounded oracle: awaitable:=decide(allowed=allowed) i.e. always true): EXIT 1 — unsolved goals.
All failures are genuine 'simp_all made no progress'/unsolved-goals errors, not linter noise.

TACTIC-CAPABILITY CONTROL (rules out a broken-tactic false-negative): ctrl_tactic.lean = a CORRECT impl written differently (`{ awaitable := isAsync, allowed := allowed }`) proved with the EXACT SAME attack proof tactic used in atk_1..7 → EXIT 0. So the attack tactic can close a true impl; the 7 failures are attributable to the wrong impls, not to a weak tactic.

Attacks span the required families: prepatch bug (atk_1), control-flow-effect (atk_2, atk_6), partial-domain (atk_3), ungrounded-oracle echo (atk_4, atk_7), boundary/order (atk_5).

Since NO wrong impl produced a closing clean-axiom proof, there is nothing to materialize into a faithful patch / run through run_resolve. verify⇒correct holds here by construction: output uniquely determined by two equalities + empty axioms region.

refinement.md AUDIT: 5 legs. Rows 1,2 = R (bool/list type refinement of unchanged read-only inputs view_is_async / _allowed_methods, modeled as parameters). Row 3 = R/I (construct bare 405 response). Row 4 = R (the changed op: async branch wraps response as awaitable; asyncio.iscoroutine ↔ awaitable=true). Row 5 = I (sync bare return). NO A-consumed, NO A-reference legs (axioms region empty, G-AX skip stub) — consistent with mapping.md callee provenance: view_is_async and _allowed_methods are unchanged inputs, not abstracted callees. No kind-3 (changed-inexpressible) leg. A-leg correspondence vacuously holds (no A-legs). Correspondence to the real callees (HttpResponseNotAllowed payload, view_is_async, _allowed_methods) is faithful and contains no escape hatch. mapping.md Python callee cited: django/views/generic/base.py:144-151 http_method_not_allowed; matches patch.diff.

Verdict: SOUND — 7 same-spec wrong impls attacked (>=5 distinct families), none verify; positive control + tactic-capability control both verify; axioms clean; no verifying-wrong impl to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16136 lean bundle. Modeled function: implementation_disallowedResponse(isAsync, allowed) -> DisallowedResponse{awaitable, allowed}, spec problem_spec_disallowedResponse := result.awaitable = isAsync AND result.allowed = allowed. Real callee: View.http_method_not_allowed @ base_commit 19e6efa (django/views/generic/base.py), patched form: response = HttpResponseNotAllowed(self._allowed_methods()); if self.view_is_async: async def func(): return response; return func() else return response.

Domain-exhaustive faithfulness check:
- awaitable field maps to asyncio.iscoroutine(result). The patched callee returns func() (a coroutine, iscoroutine=True) iff self.view_is_async, else the bare response (iscoroutine=False). So real awaitable-ness == isAsync for BOTH branches. Matches spec exactly.
- allowed field maps to the permitted methods carried by the (awaited) response = self._allowed_methods(), which the patch does NOT alter and which is identical in both async/sync modes. Modeled as the free input `allowed`. The spec constrains result.allowed = allowed (the given payload), never over-specifying its content. Matches.

The input domain is exactly Bool x List String, and for every (isAsync, allowed) the deterministic real code produces (awaitable=isAsync, allowed=allowed). No input where the model disagrees with the real callee; the spec is not too strong (it does not force any behavior the callee could violate — coroutine-ness is deterministic, payload is left as the input verbatim).

Evidence: same_spec(Solution.lean, Solution_prepatch.lean, lean)=True (spec region byte-identical, only impl/proof/doc-comment differ). lean_verify.sh exit 0 (compiles, no sorry). `#print axioms correct_disallowedResponse` => 'does not depend on any axioms' (genuine proof, no sorryAx). Prepatch impl always returns awaitable=false so its proof carries `sorry` (G-DIFF signal legitimate: bug observable only at isAsync=true, matching F2P test test_http_method_not_allowed_responds_correctly). No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction), lean bundle django__django-16136.

Spec-view authenticity verified: reconstructed the solver-facing view via swebench_unified.markers.spec_view(src, LeanBackend). impl and proof regions collapse to placeholders (impl-start/-end and proof-start/-end elided). Computed spec_view sha256 = 4f312a3aa22880662446a88db7b8e33e0f0298397544b97229b5e15fa2f2bd08 == meta.json region_hashes.spec_view; same_spec(post, prepatch) = True (spec-region byte-identity OK). Mechanical G-LEAK (leakage.screen) passes: no diff markers, no gold-patch line reproduced, no patched file/module path or repo symbol (http_method_not_allowed/func) echoed, no bug/fix narration. No relaxed_leakage flag / RELAXED_LEAKAGE.md present, so no deferral needed.

Leakage judged against PUBLIC problem_statement ONLY (hints_text excluded by rule). The problem_statement already fully discloses the observable defect: title 'object HttpResponseNotAllowed can't be used in "await" expression', a traceback where a GET (Method-Not-Allowed) request to an async-only View crashes in asgiref at `await self.awaitable(...)`, plus a reproducer async view. This publicly establishes that the 405 disallowed-method response must be awaitable when the view is async, without breaking the sync case.

Per-element check of the spec view:
- Postcondition `result.awaitable = isAsync`: a direct formalization of the publicly stated observable (awaitable iff async). Reveals no gold-edit structure.
- `result.allowed = allowed` (payload preserved across modes): intrinsic Allow-header property of any HTTP-405 HttpResponseNotAllowed; the gold edit does not touch it, so it discloses nothing about the edit.
- DisallowedResponse structure + docstrings ('awaitable wrapper to be resolved by the caller') merely restate the same await scenario already in problem_statement.
- The spec view does NOT expose gold-edit code: the `response = HttpResponseNotAllowed(...)`, `if self.view_is_async: async def func(): return response; return func()` branch, and the 'mirror options()' cue appear ONLY in the elided impl region and in hints_text (out of scope) — not in the solver-visible view.

Conclusion: the spec view is a faithful formalization of the publicly-disclosed defect and adds no gold-reconstruction knowledge beyond problem_statement. Corroborates recorded G-PANEL-3 verdict. No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
