# P2 adversarial audit — matplotlib__matplotlib-26291

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The discriminating input is suppliedContext = none (Python: locator(ax, None) from the tight-bbox path, matplotlib/_tight_bbox.py:28), where the spec forces BOTH components to some surfaceContext. Every wrong impl that fails to hand the resolved surface context to BOTH steps at that input is REJECTED (atk_1 prepatch, atk_2 extent-only, atk_3 placement-only, atk_4 always-surface, atk_5 guard inversion, atk_6 partial domain on both components, atk_7 partial domain on the SECOND component only). The prior recorded break (resolve at the get_window_extent call site only) is re-encoded as atk_2 and now fails to close with residual goal 'case none.right |- False' -- the conjunct the pair repair added. All 7 impls whose proofs closed with clean axioms had faithful patches materialized, apply-checked at base_commit and EXECUTED through run_resolve: all 7 RESOLVED (F2P 1/1, P2P 49/49).
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,14 +80,11 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
+
+  -- PREPATCH BUG re-encoded: the caller-supplied optional context is handed
+  -- straight to both steps; the "nothing supplied" case is never resolved
+  -- against the host's drawing surface.
   let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
   let extentStepContext := ctx
   let placementStepContext := ctx
   return (extentStepContext, placementStepContext)
@@ -100,5 +97,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,15 +80,16 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
+
+  -- NARROW SCOPE (the PREVIOUSLY RECORDED verify-does-not-imply-correct break,
+  -- re-encoded against the repaired pair spec): a present context is
+  -- materialized ONLY where the extent step consumes it; the placement step
+  -- still reads the raw caller value.
   let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
-  let extentStepContext := ctx
+  let extentStepContext : Option RenderContext :=
+    match ctx with
+    | some r => some r
+    | none   => some surfaceContext
   let placementStepContext := ctx
   return (extentStepContext, placementStepContext)
 -- impl-end
@@ -100,5 +101,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,16 +80,15 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
+
+  -- NARROW SCOPE, MIRRORED: resolve for the LATER (placement) step only and let
+  -- the extent step proceed with whatever the caller handed in.
   let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
   let extentStepContext := ctx
-  let placementStepContext := ctx
+  let placementStepContext : Option RenderContext :=
+    match ctx with
+    | some r => some r
+    | none   => some surfaceContext
   return (extentStepContext, placementStepContext)
 -- impl-end
 
@@ -100,5 +99,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,14 +80,10 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
+
+  -- UNGROUNDED OVERWRITE: always take the host surface's context, discarding a
+  -- context the caller did supply.
+  let ctx : Option RenderContext := some surfaceContext
   let extentStepContext := ctx
   let placementStepContext := ctx
   return (extentStepContext, placementStepContext)
@@ -100,5 +96,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,14 +80,12 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
+
+  -- BOUNDARY / GUARD INVERSION: the fallback fires exactly when the caller DID
+  -- supply a context, and not when it supplied nothing.
   let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
+  if ctx.isSome then
     ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
   let extentStepContext := ctx
   let placementStepContext := ctx
   return (extentStepContext, placementStepContext)
@@ -100,5 +98,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,14 +80,13 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
+
+  -- PARTIAL DOMAIN: correct on the "nothing supplied" half of the domain and
+  -- broken on the other half (a supplied context is dropped to nothing).
+  let ctx : Option RenderContext :=
+    match suppliedContext with
+    | some _ => none
+    | none   => some surfaceContext
   let extentStepContext := ctx
   let placementStepContext := ctx
   return (extentStepContext, placementStepContext)
@@ -100,5 +99,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,16 +80,16 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
-  let extentStepContext := ctx
-  let placementStepContext := ctx
+
+  -- PARTIAL DOMAIN ON THE SECOND COMPONENT ONLY: the resolution is complete for
+  -- the extent step, and complete for the placement step ONLY on the "nothing
+  -- supplied" half; when the caller DID supply a context the placement step is
+  -- handed nothing.
+  let extentStepContext : Option RenderContext := some (suppliedContext.getD surfaceContext)
+  let placementStepContext : Option RenderContext :=
+    match suppliedContext with
+    | some _ => none
+    | none   => some surfaceContext
   return (extentStepContext, placementStepContext)
 -- impl-end
 
@@ -100,5 +100,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,16 +80,12 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
-  let extentStepContext := ctx
-  let placementStepContext := ctx
+
+  -- UNGROUNDED-ORACLE ECHO: the postcondition's right-hand side copied verbatim
+  -- into the implementation, with no fallback control flow of its own.
+  let resolved : Option RenderContext := some (suppliedContext.getD surfaceContext)
+  let extentStepContext := resolved
+  let placementStepContext := resolved
   return (extentStepContext, placementStepContext)
 -- impl-end
 
@@ -100,5 +96,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,16 +80,21 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
-  let extentStepContext := ctx
-  let placementStepContext := ctx
+
+  -- CONTROL-FLOW EFFECT, MAXIMAL: the host surface's context is acquired
+  -- EAGERLY, UNCONDITIONALLY and TWICE -- once for each step -- before the
+  -- caller's argument is inspected at all, and both acquisitions are discarded
+  -- on the branch where the caller did supply a context.
+  let eagerExtentSurface : Option RenderContext := some surfaceContext
+  let eagerPlacementSurface : Option RenderContext := some surfaceContext
+  let extentStepContext : Option RenderContext :=
+    match suppliedContext with
+    | some r => some r
+    | none   => eagerExtentSurface
+  let placementStepContext : Option RenderContext :=
+    match suppliedContext with
+    | some r => some r
+    | none   => eagerPlacementSurface
   return (extentStepContext, placementStepContext)
 -- impl-end
 
@@ -100,5 +105,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,16 +80,18 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
-  let extentStepContext := ctx
-  let placementStepContext := ctx
+
+  -- NO SHARED BINDING, RESOLVED AT EACH USE SITE: the caller's binding is never
+  -- overwritten; each step settles the question for ITSELF, independently, at
+  -- the point where it consumes the context. Two separate resolutions.
+  let extentStepContext : Option RenderContext :=
+    match suppliedContext with
+    | some r => some r
+    | none   => some surfaceContext
+  let placementStepContext : Option RenderContext :=
+    match suppliedContext with
+    | some r => some r
+    | none   => some surfaceContext
   return (extentStepContext, placementStepContext)
 -- impl-end
 
@@ -100,5 +102,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,14 +80,15 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
+
+  -- CROSS-CALL MEMOIZATION: the surface context is parked in a cell that
+  -- outlives the call and is populated only the first time it is needed; later
+  -- calls that supply nothing reuse whatever was parked, without re-consulting
+  -- the host's drawing surface.
   let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
   if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
+    let memo : RenderContext := surfaceContext
+    ctx := some memo
   let extentStepContext := ctx
   let placementStepContext := ctx
   return (extentStepContext, placementStepContext)
@@ -100,5 +101,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,16 +80,13 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
-  let extentStepContext := ctx
-  let placementStepContext := ctx
+
+  -- BOUNDARY: the "did the caller supply anything?" test is spelled as an
+  -- emptiness/truthiness test on the optional carrier rather than an explicit
+  -- comparison against the absent value, via an either-or combinator.
+  let settled : Option RenderContext := suppliedContext.orElse (fun _ => some surfaceContext)
+  let extentStepContext := settled
+  let placementStepContext := settled
   return (extentStepContext, placementStepContext)
 -- impl-end
 
@@ -100,5 +97,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,16 +80,18 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
-  let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
-  if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
-  let extentStepContext := ctx
-  let placementStepContext := ctx
+
+  -- LAZY / RE-ACQUIRED PER STEP: nothing is settled up front. Each step runs a
+  -- thunk at its own moment in the routine, and the thunk consults the host's
+  -- drawing surface afresh at that moment, so the two consultations happen at
+  -- two DIFFERENT points in the routine (the second one after the extent
+  -- arithmetic has already run).
+  let resolveNow : Unit -> Option RenderContext := fun _ =>
+    match suppliedContext with
+    | some r => some r
+    | none   => some surfaceContext
+  let extentStepContext := resolveNow ()
+  let placementStepContext := resolveNow ()
   return (extentStepContext, placementStepContext)
 -- impl-end
 
@@ -100,5 +102,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -80,14 +80,15 @@
 def implementation_resolveRenderContext
     (suppliedContext : Option RenderContext) (surfaceContext : RenderContext) :
     Option RenderContext × Option RenderContext := Id.run do
-  -- Start from whatever the caller supplied (possibly nothing).
+
+  -- RESOLUTION MOVED PAST THE UNMODELED STATEMENT: the routine first performs
+  -- its other head-of-method bookkeeping and only then settles the context,
+  -- reaching the host's drawing surface through the object it just recorded
+  -- rather than through its own parameter.
+  let recordedHost : RenderContext := surfaceContext
   let mut ctx := suppliedContext
-  -- If the caller supplied nothing, fall back to the context obtained from the
-  -- host's drawing surface, which is always available.
   if ctx.isNone then
-    ctx := some surfaceContext
-  -- Both steps read the SAME settled binding, so each is handed a present,
-  -- concrete context: the extent step first, then the placement step.
+    ctx := some recordedHost
   let extentStepContext := ctx
   let placementStepContext := ctx
   return (extentStepContext, placementStepContext)
@@ -100,5 +101,10 @@
         (implementation_resolveRenderContext suppliedContext surfaceContext) := by
   intro suppliedContext surfaceContext
   unfold problem_spec_resolveRenderContext implementation_resolveRenderContext
-  cases suppliedContext <;> exact ⟨rfl, rfl⟩
+  cases suppliedContext <;> first
+    | exact ⟨rfl, rfl⟩
+    | (constructor <;> rfl)
+    | (constructor <;> simp [Option.getD, Option.orElse])
+    | simp_all [Option.getD, Option.orElse]
+    | (refine ⟨?_, ?_⟩ <;> rfl)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** assigned focus = A-legs + model<->patch correspondence (R/I mechanically covered by G-CONF). Base worktree wt/ @ fa68f46289adf4a8a4bc7ba97ded8258ec9d079c (git worktree add --detach from the upstream repository); left byte-clean (git status --porcelain empty) after every patch materialization and after the gold-patch AST audit. patch.diff == instance.json['patch'] verbatim (True). properties.py imports OK (battery control).

**SAME-SPEC:** markers.same_spec(Solution.lean, X, lean) = True for all 14 attacks + pos_control + prepatch_control (only impl region + proof tactic block edited; axioms/pure/pre/post byte-identical).

VERIFY CMD (run 4-way concurrent as background jobs): bash scripts/lean_verify.sh <f>.lean
AXIOM CMD: same on ax_<f>.lean = <f>.lean + '#print axioms correct_/implementation_/problem_spec_resolveRenderContext'
RESOLVE CMD: python3 resolve_one.py <f> (swebench_unified.harness.run_resolve('matplotlib__matplotlib-26291', <f>.diff)); JSON in resolve_<f>.json
APPLY CHECK: cd wt && git apply --check ../<f>.diff -> OK for all 7 diffs

| file | kind | verify exit | axioms | resolve |
| pos_control.lean | gold impl (positive control) | 0 | 'does not depend on any axioms' (all 3 symbols) | (gold) |
| prepatch_control.lean | shipped Solution_prepatch.lean | 1 rejected (type mismatch :103) | - | - |
| atk_1.lean | PREPATCH BUG re-encoded (identity passthrough) | 1 rejected | - | - |
| atk_2.lean | narrow scope: resolve EXTENT step only (prior recorded break) | 1 rejected; residual 'case none.right |- False' | - | - |
| atk_3.lean | narrow scope MIRRORED: PLACEMENT step only | 1 rejected; residual 'case none.left |- False' | - | - |
| atk_4.lean | ungrounded overwrite: always surfaceContext | 1 rejected | - | - |
| atk_5.lean | boundary/guard inversion (fires on isSome) | 1 rejected | - | - |
| atk_6.lean | partial domain: correct on none, drops some to none | 1 rejected | - | - |
| atk_7.lean | partial domain on SECOND component only | 1 rejected; residual 'case some.right |- False' | - | - |
| atk_8.lean | ungrounded-oracle echo (spec RHS copied verbatim) | 0 | clean | RESOLVED (2 attempts, flaky first, F2P 1/1, P2P 49/49) |
| atk_9.lean | control-flow effect maximal: TWO eager unconditional acquisitions | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_10.lean | no shared binding: each step resolves independently at its use site | 0 | clean | RESOLVED (2 attempts, flaky first, F2P 1/1, P2P 49/49) |
| atk_11.lean | CROSS-CALL MEMOIZATION of the surface renderer on the locator | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_12.lean | boundary: truthiness ('if not renderer') instead of 'is None' | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_13.lean | LAZY thunk re-acquired per step; 2nd consult AFTER extent arithmetic | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_14.lean | resolution moved PAST self.axes = ax, reached via self.axes.figure | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |

7 reject-lane attacks all rejected; 7 verify-lane attacks all closed with clean axioms, all 7 faithful patches materialized + apply-checked + EXECUTED through run_resolve -> 7/7 RESOLVED. No verifying attack has a non-resolving patch, so no verify-does-not-imply-correct witness exists in this battery. (atk_8/atk_10 needed a 2nd harness attempt; both flipped to resolved, i.e. network flakiness not a real failure -- run_resolve's own retry logic, recorded flaky=True.)

**WHY THE PRIOR BREAK IS CLOSED.** The earlier revision modeled result : Option RenderContext scoped to the get_window_extent argument; a rival resolving that one call site while passing raw None to get_offset verified yet failed F2P (crash relocates to AnchoredOffsetbox.get_offset -> renderer.points_to_pixels). The repaired spec returns the ORDERED PAIR and pins BOTH conjuncts. Re-encoded as atk_2 it no longer closes, and the residual goal is the SECOND conjunct alone -- the added clause is what refutes it, not incidental tactic weakness. atk_3 is refuted symmetrically on none.left and atk_7 on some.right, so neither component is decorative; each is independently load-bearing on both halves of the domain. My reject-lane proofs used a WIDENED tactic block (first | exact <rfl,rfl> | constructor <;> rfl | constructor <;> simp [...] | simp_all [...] | refine ...), so rejection is not an artifact of a weak carried tactic.

### A-LEG AUDIT (assigned focus).
- Leg kinds: rows 1,2,7 = R; rows 3,4,5,6 = I. NO row is A-consumed, A-reference, or kind-3. Every leg is one of R/A/I as required; no unclassified leg.
- Consistent with meta.json axioms=[] and deep_model_references=[]. grep over Solution.lean for axiom/sorry/native_decide/extern/unsafe/partial declarations: the ONLY match is 'opaque RenderContext : Type' at :51. No 'axiom RenderContext_*' property exists anywhere, so nothing can sneak in proof-side. #print axioms reports 'does not depend on any axioms' for correct_, implementation_ AND problem_spec_resolveRenderContext, on pos_control and on all 7 verifying attacks (14 x 3 symbol checks, all clean, no sorryAx).
- The absence of A-legs is JUSTIFIED, not evasive: nothing about what get_window_extent or get_offset COMPUTE is modeled or assumed -- only the identity of the renderer each is handed, which is exactly the dataflow the two added lines change. RenderContext is opaque purely as the element type of the optional carrier / the type of the surface value so the context can appear in the executable impl. axiom_check.py is a correctly-justified skip stub (its docstring states the same reasoning I independently confirmed), so G-AX legitimately skips rather than being silenced.
- ROW-2 R-LEG (the spec's one genuine strengthening): surfaceContext is typed plain RenderContext, not Option, asserting ax.figure.`_get_renderer`() always yields a present renderer. I audited every provider in my worktree: Figure.`_get_renderer` (figure.py:2731) -> canvas.get_renderer() or backend_bases.`_get_renderer`; SubFigure.`_get_renderer` (figure.py:2255) delegates to `_parent`. The three get_renderer defs are backend_agg:406 (returns self.renderer, constructed), backend_cairo:384 (returns self.`_renderer`, lazily constructed property), backend_pgf:846 (returns a fresh RendererPgf). None can return None, and backend_bases.`_get_renderer` (:1614) RAISES RuntimeError rather than returning None. So 'always present' is a property of the real callee; modeling it as a given value rather than an A-leg is faithful, not an unsound weakening.
- MODEL<->PATCH CORRESPONDENCE, MECHANICALLY CHECKED (my own run, not read off the record). I applied patch.diff in wt/ and walked the gold-patched AnchoredLocatorBase.`__call__` AST: renderer Load lines = [72, 75, 76] (the 'is None' Compare; the arg of self.get_window_extent; the arg of self.get_offset) and renderer Store lines = [73] (the guard's rebind of the PARAMETER). Exactly 3 reads + 1 store. So the ordered pair IS the whole independently-observable renderer dataflow of the method: rows 5 and 6 tagged I are correct, and refinement.md's frame claim (directive 5) is substantive rather than vacuous. Worktree restored clean afterwards (git checkout -- .; porcelain empty).
- refinement.md's 'audit repair' narrative matches what I measured: it names the earlier narrow model, the rival, and its F2P failure, and the pair model it describes is the one shipped in Solution.lean. mapping.md's .1/.2 binding to inset_locator.py:74/75 post-fix matches the AST lines I found (75/76 in absolute post-patch numbering; same two call arguments in source order).
- HONEST RESIDUALS, PROBED NOT TRUSTED. The model pins only WHICH renderer each step receives, leaving unpinned (a) resolution position relative to self.axes = ax, (b) cross-call behavior such as memoizing the surface renderer, (c) eager vs lazy acquisition and per-step vs shared resolution, (d) the spelling of the None test. I did not take any of these on trust -- atk_14 exercises (a), atk_11 exercises (b) with real per-locator memoization on self, atk_9/atk_10/atk_13 exercise (c) including a thunk whose second consultation happens only after the extent arithmetic completes, and atk_12 exercises (d) as a truthiness test. All six RESOLVE, so these are genuine implementation latitude the gold-patched repo tolerates, not holes. For (d) I additionally confirmed by grep that neither backend_bases.py nor backend_agg.py defines `__bool__` or `__len__` on any renderer, so 'if not renderer' is behaviorally equivalent to 'is None' here.
- Modeling boundary considered and rejected as a defect: if the extent step raised, the placement step would not be reached, so result.2 would be undefined. That is partiality, not a case where the real patched code hands a step a context DIFFERENT from suppliedContext.getD surfaceContext, and it holds equally pre-patch.

**VERDICT:** SOUND. 14 same-spec attacks (prepatch bug re-encoded and rejected; 7 rejected wrong impls spanning partial-domain on each component, boundary/guard-inversion, narrow-scope in both directions, and ungrounded overwrite; 7 verifying impls spanning ungrounded-oracle echo, eager control-flow effect, independent per-step resolution, cross-call memoization, truthiness boundary, lazy re-acquisition, and statement reordering). Every impl whose proof closed with clean axioms had its faithful patch materialized, apply-checked and RUN through the official harness, and all 7 resolved -- so no verify-does-not-imply-correct witness. No A-leg defect and no kind-3 leg; the model<->patch correspondence holds under my own AST walk of the gold-patched method.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The discriminating input is suppliedContext = none (Python: locator(ax, None) from the tight-bbox path, matplotlib/_tight_bbox.py:28), where the spec forces BOTH components to some surfaceContext. Every wrong impl that fails to hand the resolved surface context to BOTH steps at that input is REJECTED (atk_1 prepatch, atk_2 extent-only, atk_3 placement-only, atk_4 always-surface, atk_5 guard inversion, atk_6 partial domain on both components, atk_7 partial domain on the SECOND component only). The prior recorded break (resolve at the get_window_extent call site only) is re-encoded as atk_2 and now fails to close with residual goal 'case none.right |- False' -- the conjunct the pair repair added. All 7 impls whose proofs closed with clean axioms had faithful patches materialized, apply-checked at base_commit and EXECUTED through run_resolve: all 7 RESOLVED (F2P 1/1, P2P 49/49).
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** assigned focus = A-legs + model<->patch correspondence (R/I mechanically covered by G-CONF). Base worktree wt/ @ fa68f46289adf4a8a4bc7ba97ded8258ec9d079c (git worktree add --detach from the upstream repository); left byte-clean (git status --porcelain empty) after every patch materialization and after the gold-patch AST audit. patch.diff == instance.json['patch'] verbatim (True). properties.py imports OK (battery control).

**SAME-SPEC:** markers.same_spec(Solution.lean, X, lean) = True for all 14 attacks + pos_control + prepatch_control (only impl region + proof tactic block edited; axioms/pure/pre/post byte-identical).

VERIFY CMD (run 4-way concurrent as background jobs): bash scripts/lean_verify.sh <f>.lean
AXIOM CMD: same on ax_<f>.lean = <f>.lean + '#print axioms correct_/implementation_/problem_spec_resolveRenderContext'
RESOLVE CMD: python3 resolve_one.py <f> (swebench_unified.harness.run_resolve('matplotlib__matplotlib-26291', <f>.diff)); JSON in resolve_<f>.json
APPLY CHECK: cd wt && git apply --check ../<f>.diff -> OK for all 7 diffs

| file | kind | verify exit | axioms | resolve |
| pos_control.lean | gold impl (positive control) | 0 | 'does not depend on any axioms' (all 3 symbols) | (gold) |
| prepatch_control.lean | shipped Solution_prepatch.lean | 1 rejected (type mismatch :103) | - | - |
| atk_1.lean | PREPATCH BUG re-encoded (identity passthrough) | 1 rejected | - | - |
| atk_2.lean | narrow scope: resolve EXTENT step only (prior recorded break) | 1 rejected; residual 'case none.right |- False' | - | - |
| atk_3.lean | narrow scope MIRRORED: PLACEMENT step only | 1 rejected; residual 'case none.left |- False' | - | - |
| atk_4.lean | ungrounded overwrite: always surfaceContext | 1 rejected | - | - |
| atk_5.lean | boundary/guard inversion (fires on isSome) | 1 rejected | - | - |
| atk_6.lean | partial domain: correct on none, drops some to none | 1 rejected | - | - |
| atk_7.lean | partial domain on SECOND component only | 1 rejected; residual 'case some.right |- False' | - | - |
| atk_8.lean | ungrounded-oracle echo (spec RHS copied verbatim) | 0 | clean | RESOLVED (2 attempts, flaky first, F2P 1/1, P2P 49/49) |
| atk_9.lean | control-flow effect maximal: TWO eager unconditional acquisitions | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_10.lean | no shared binding: each step resolves independently at its use site | 0 | clean | RESOLVED (2 attempts, flaky first, F2P 1/1, P2P 49/49) |
| atk_11.lean | CROSS-CALL MEMOIZATION of the surface renderer on the locator | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_12.lean | boundary: truthiness ('if not renderer') instead of 'is None' | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_13.lean | LAZY thunk re-acquired per step; 2nd consult AFTER extent arithmetic | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |
| atk_14.lean | resolution moved PAST self.axes = ax, reached via self.axes.figure | 0 | clean | RESOLVED (1 attempt, F2P 1/1, P2P 49/49) |

7 reject-lane attacks all rejected; 7 verify-lane attacks all closed with clean axioms, all 7 faithful patches materialized + apply-checked + EXECUTED through run_resolve -> 7/7 RESOLVED. No verifying attack has a non-resolving patch, so no verify-does-not-imply-correct witness exists in this battery. (atk_8/atk_10 needed a 2nd harness attempt; both flipped to resolved, i.e. network flakiness not a real failure -- run_resolve's own retry logic, recorded flaky=True.)

**WHY THE PRIOR BREAK IS CLOSED.** The earlier revision modeled result : Option RenderContext scoped to the get_window_extent argument; a rival resolving that one call site while passing raw None to get_offset verified yet failed F2P (crash relocates to AnchoredOffsetbox.get_offset -> renderer.points_to_pixels). The repaired spec returns the ORDERED PAIR and pins BOTH conjuncts. Re-encoded as atk_2 it no longer closes, and the residual goal is the SECOND conjunct alone -- the added clause is what refutes it, not incidental tactic weakness. atk_3 is refuted symmetrically on none.left and atk_7 on some.right, so neither component is decorative; each is independently load-bearing on both halves of the domain. My reject-lane proofs used a WIDENED tactic block (first | exact <rfl,rfl> | constructor <;> rfl | constructor <;> simp [...] | simp_all [...] | refine ...), so rejection is not an artifact of a weak carried tactic.

### A-LEG AUDIT (assigned focus).
- Leg kinds: rows 1,2,7 = R; rows 3,4,5,6 = I. NO row is A-consumed, A-reference, or kind-3. Every leg is one of R/A/I as required; no unclassified leg.
- Consistent with meta.json axioms=[] and deep_model_references=[]. grep over Solution.lean for axiom/sorry/native_decide/extern/unsafe/partial declarations: the ONLY match is 'opaque RenderContext : Type' at :51. No 'axiom RenderContext_*' property exists anywhere, so nothing can sneak in proof-side. #print axioms reports 'does not depend on any axioms' for correct_, implementation_ AND problem_spec_resolveRenderContext, on pos_control and on all 7 verifying attacks (14 x 3 symbol checks, all clean, no sorryAx).
- The absence of A-legs is JUSTIFIED, not evasive: nothing about what get_window_extent or get_offset COMPUTE is modeled or assumed -- only the identity of the renderer each is handed, which is exactly the dataflow the two added lines change. RenderContext is opaque purely as the element type of the optional carrier / the type of the surface value so the context can appear in the executable impl. axiom_check.py is a correctly-justified skip stub (its docstring states the same reasoning I independently confirmed), so G-AX legitimately skips rather than being silenced.
- ROW-2 R-LEG (the spec's one genuine strengthening): surfaceContext is typed plain RenderContext, not Option, asserting ax.figure.`_get_renderer`() always yields a present renderer. I audited every provider in my worktree: Figure.`_get_renderer` (figure.py:2731) -> canvas.get_renderer() or backend_bases.`_get_renderer`; SubFigure.`_get_renderer` (figure.py:2255) delegates to `_parent`. The three get_renderer defs are backend_agg:406 (returns self.renderer, constructed), backend_cairo:384 (returns self.`_renderer`, lazily constructed property), backend_pgf:846 (returns a fresh RendererPgf). None can return None, and backend_bases.`_get_renderer` (:1614) RAISES RuntimeError rather than returning None. So 'always present' is a property of the real callee; modeling it as a given value rather than an A-leg is faithful, not an unsound weakening.
- MODEL<->PATCH CORRESPONDENCE, MECHANICALLY CHECKED (my own run, not read off the record). I applied patch.diff in wt/ and walked the gold-patched AnchoredLocatorBase.`__call__` AST: renderer Load lines = [72, 75, 76] (the 'is None' Compare; the arg of self.get_window_extent; the arg of self.get_offset) and renderer Store lines = [73] (the guard's rebind of the PARAMETER). Exactly 3 reads + 1 store. So the ordered pair IS the whole independently-observable renderer dataflow of the method: rows 5 and 6 tagged I are correct, and refinement.md's frame claim (directive 5) is substantive rather than vacuous. Worktree restored clean afterwards (git checkout -- .; porcelain empty).
- refinement.md's 'audit repair' narrative matches what I measured: it names the earlier narrow model, the rival, and its F2P failure, and the pair model it describes is the one shipped in Solution.lean. mapping.md's .1/.2 binding to inset_locator.py:74/75 post-fix matches the AST lines I found (75/76 in absolute post-patch numbering; same two call arguments in source order).
- HONEST RESIDUALS, PROBED NOT TRUSTED. The model pins only WHICH renderer each step receives, leaving unpinned (a) resolution position relative to self.axes = ax, (b) cross-call behavior such as memoizing the surface renderer, (c) eager vs lazy acquisition and per-step vs shared resolution, (d) the spelling of the None test. I did not take any of these on trust -- atk_14 exercises (a), atk_11 exercises (b) with real per-locator memoization on self, atk_9/atk_10/atk_13 exercise (c) including a thunk whose second consultation happens only after the extent arithmetic completes, and atk_12 exercises (d) as a truthiness test. All six RESOLVE, so these are genuine implementation latitude the gold-patched repo tolerates, not holes. For (d) I additionally confirmed by grep that neither backend_bases.py nor backend_agg.py defines `__bool__` or `__len__` on any renderer, so 'if not renderer' is behaviorally equivalent to 'is None' here.
- Modeling boundary considered and rejected as a defect: if the extent step raised, the placement step would not be reached, so result.2 would be undefined. That is partiality, not a case where the real patched code hands a step a context DIFFERENT from suppliedContext.getD surfaceContext, and it holds equally pre-patch.

**VERDICT:** SOUND. 14 same-spec attacks (prepatch bug re-encoded and rejected; 7 rejected wrong impls spanning partial-domain on each component, boundary/guard-inversion, narrow-scope in both directions, and ungrounded overwrite; 7 verifying impls spanning ungrounded-oracle echo, eager control-flow effect, independent per-step resolution, cross-call memoization, truthiness boundary, lazy re-acquisition, and statement reordering). Every impl whose proof closed with clean axioms had its faithful patch materialized, apply-checked and RUN through the official harness, and all 7 resolved -- so no verify-does-not-imply-correct witness. No A-leg defect and no kind-3 leg; the model<->patch correspondence holds under my own AST walk of the gold-patched method.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** G-PANEL attacker (2), faithfulness-break. Verdict FAITHFUL: I could not find any input on which problem_spec_resolveRenderContext disagrees with the real post-patch AnchoredLocatorBase.`__call__`.

REFERENCE CONSTRUCTED (not assumed). Base worktree @ fa68f46289 (confirmed clean, `__call__` has NO guard). I built two importable trees by grafting the prebuilt C extensions  (mpl 3.7.0.dev1362) onto the base lib/: (base) and .../ZALf0E_patched (patch.diff applied, the two-line guard). Confirmed patch.diff == instance.json['patch'] byte-identical and patch_equals_gold. Compared the model against the PATCHED tree per the brief; the base tree was used only as the control (it raises AttributeError: 'NoneType' has no attribute '`_get_renderer`' at offsetbox.py:398, reproducing the reported crash), never as the faithfulness reference.

MY OWN DIFFERENTIAL (independent of the shipped conformance_check.py; gp2_probe2.py). Drove the REAL patched `__call__` to completion with capture-and-continue stubs on both renderer consumers, real `_get_renderer` where possible:

  (A) 317 inputs (None boundary + 16 distinct sentinel renderers + randomized mix), fresh surface sentinel per trial, compared componentwise BY IDENTITY against the shadow (ctx = supplied else surface; pair = (ctx,ctx)): 0 disagreements. Every observed component was present (never None) and identical to the value the spec's `some (suppliedContext.getD surfaceContext)` names.

  (B) The attack I expected to land: made ax.figure.`_get_renderer` return a FRESH object on every call. The spec forces result.1 == result.2 (both pinned to the SAME `suppliedContext.getD surfaceContext`), so if the real code resolved twice — once per consumer — the spec would be too strong and this is the diverging input. Real code: `_get_renderer` call count = 1, extent and placement both got S1001, e is p = True. The guard rebinds the PARAMETER once, so there is exactly one resolution shared by both steps. No divergence; the equality of the two components is a genuine property of the patched code, not a spec artifact.

  (C) supplied non-None: `_get_renderer` is called 0 times and both steps get the caller's object by identity — matches `some r` for both components; the spec does not over-demand a fallback on the supplied path.

  (D) Falsy-but-not-None supplied (0, False, '', []): real code passes them through unchanged to BOTH steps (identity `is None`, not truthiness). The Lean model's `Option.getD`/`isNone` is `is None`, not falsiness, so these agree — the classic Python/Option mismatch is NOT present here.

  (E) Degenerate `_get_renderer` -> None: real code hands None to both steps, which would violate the spec's `some _`. NOT a divergence: it is outside the modeled domain by construction — surfaceContext : RenderContext is a PLAIN (non-Option) input, so the model never claims anything about a surface that furnishes nothing, and backend_bases.`_get_renderer` (backend_bases.py:1614-1643) either returns a renderer or RAISES RuntimeError; it has no None-returning path. Correctly scoped as a value, not an over-strong axiom.

**COVERAGE OF THE MODELED SITE.** AST-checked the patched method myself: the `renderer is None` test plus the two call arguments get_window_extent(renderer) / get_offset(...,renderer) are the ONLY Load reads of `renderer` in `__call__`, so the modeled pair is the whole observable — no third consumer sits outside the model. AnchoredSizeLocator and AnchoredZoomLocator both inherit this exact `__call__` (verified type(zl).`__call__` is AnchoredLocatorBase.`__call__`); InsetPosition.`__call__` (inset_locator.py:52) never reads `renderer` at all and is untouched by the patch, so it is correctly out of scope. Probed the SubFigure host too (ax.figure is a SubFigure, whose `_get_renderer` delegates to the parent at figure.py:2255): still one resolution, both components present and equal. End-to-end F2P (savefig bbox_inches='tight') passes on the plain, subfigure, and zoomed-inset paths against the patched tree and raises on base.

**SHIPPED HARNESS CROSS-CHECK.** Ran the bundle's own conformance_check.py against MY independently-built patched tree (not the bundle's): 3000 inputs, 0 disagreements, status=pass — so its 0-disagreement claim reproduces on a tree I constructed, and `_capture_is_complete` passes on the real source.

**SPEC REGION INTEGRITY.** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True — spec regions (axioms/pure/post-conditions) byte-identical; the only diff is impl+proof+comments, as required. Solution.lean verifies via scripts/lean_verify.sh exit 0, and `#print axioms correct_resolveRenderContext` reports 'does not depend on any axioms' — no sorryAx, no repo-callee axiom, so nothing is assumed about the callees the patch does not touch. Solution_prepatch.lean correctly FAILS (exit 1); the refutation lands exactly on the `none` case, on result.2 as well as result.1.

WHY THE PAIR IS NOT AN OVER-SPECIFICATION (the strongest UNFAITHFUL case I considered, and rejected). Pinning BOTH components could be spec-too-strong if the real code only guaranteed the first. It does not: (B) shows one shared resolution, and the second conjunct is independently load-bearing — an impl resolving only for the extent call leaves get_offset dereferencing None at AnchoredOffsetbox.get_offset -> renderer.points_to_pixels (offsetbox.py:1054-1057), which I confirmed is a real code path, so F2P would still fail. The pair is exactly the patched behavior, neither stronger nor weaker. Componentwise pinning also does not force the gold's SHAPE (resolve-per-branch or bind-once both satisfy it).

MINOR, NON-BLOCKING BOOKKEEPING (not a faithfulness defect, does not affect this verdict): meta.json's top-level `region_hashes` block does not reproduce from either Solution.lean or Solution_prepatch.lean on disk (all six entries differ). The G-HYGIENE gate record's OWN region_hashes DO reproduce exactly from Solution.lean (axioms 1e24bb1b, impl 9f35bdfd, post-conditions 6f1146fa, proof 75d0e9ea, pure 81fe224d, spec_view 0d44846c), so the shipped spec bytes are the audited ones and freshness is intact via the gate record; the stale copy is the top-level field only. Worth a restamp, but it is a ledger artifact and no part of the spec's agreement with the repo depends on it.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** G-PANEL attacker (3) leakage / gold-reconstruction, matplotlib__matplotlib-26291 (lean). Verdict NO-LEAKAGE.

**RELAXATION:** none claimed. meta.json has NO `relaxed_leakage` key (keys: axioms, conf_skip, deep_model_references, gates, instance_id, modeled_functions, notes, patch_equals_gold, pbt_audit, prepatch_files, region_hashes, schema_version, spec_provenance, verifier_pins) and `find -iname '*RELAX*'` over the instance dir returns nothing. So this is a plain leakage judgement, not an inherited disposition, and there was no unavoidability argument to re-derive.

WHAT I MEASURED (spec view, not the whole file). Extracted the solver-visible artifact mechanically: swebench_unified.markers.spec_view(Solution.lean, get_backend('lean')) -- impl and proof regions collapse to '-- implementation elided' / '-- proof elided', so the leak surface is the module docstring + axioms region (opaque RenderContext) + pure comment + post-conditions region (problem_spec_resolveRenderContext).

**SPEC-REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) => True. The pre/post pair differ only inside impl and proof (diff confirms: prepatch drops the `if ctx.isNone then ctx := some surfaceContext` fallback and swaps the narration comments), so the spec bytes the solver sees are byte-identical across the pair and cannot be a channel for which side is gold.

CORE GATES the verdict leans on, re-run rather than read off meta.json:
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- `#print axioms correct_resolveRenderContext` appended and re-verified -> "does not depend on any axioms" (exit 0). No sorryAx, no repo-callee axiom; proof closes structurally by `cases suppliedContext <;> exact <rfl, rfl>`.
- scripts/lean_verify.sh Solution_prepatch.lean -> FAILS, and the error is the right one: the carried gold proof cannot close `(...).run.2 = some (none.getD surfaceContext)`, i.e. the refutation lands on the SECOND component in the `suppliedContext = none` case. G-DIFF is genuinely discriminating.
- leakage.screen(Solution.lean, lean, gold_patch, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]).

VOCABULARY SCAN of the spec view for repo/patch identifiers: regex sweep for renderer, figure, `_get_renderer`, matplotlib, inset, axes, locator, bbox, offsetbox, tight, savefig, get_window_extent, get_offset, AttributeError, patch/fix/bug/copy. Zero substantive hits -- the only matches are artifacts of my own patterns ('mpl' inside 'impl-start'/'implementation elided', 'ax.' inside 'axioms-start', 'None' inside Lean's `none`). The spec view is fully anonymized: 'measurement context', 'host region', 'drawing surface', 'EXTENT step', 'PLACEMENT step', with RenderContext opaque. No file path, no method name, no Python identifier, no diff text.

GOLD-RECONSTRUCTION TEST vs the PUBLIC problem_statement (hints_text deliberately excluded as a baseline; I read it only to confirm I was not borrowing from it -- it separately discusses plumbing the figure, and I did not rely on that). Every discriminating fact the spec view states is present verbatim in the public traceback. Grepped problem_statement and all of these are True: 'def `__call__`(self, ax, renderer)', 'self.axes = ax', 'get_window_extent(renderer)', 'get_offset(bbox.width', 'locator(ax, None)', 'renderer is None', 'renderer = self.figure.`_get_renderer`()', '`_get_renderer`', 'AnchoredLocatorBase'.

Concretely the public statement already shows: (a) the caller supplies None (`ax.apply_aspect(locator(ax, None))` at `_tight_bbox`.py:28); (b) the method's frame with BOTH downstream consumers in source order, extent then placement (inset_locator.py:73 and :74-75); (c) the exact fallback idiom `if renderer is None: renderer = self.figure._get_renderer()` in the offsetbox.py:396-399 frame; (d) the failure `AttributeError: 'NoneType' object has no attribute '_get_renderer'`, which tells the reader the artist's own figure is absent while `ax` is in hand.

So 'resolve the absent context from the host's surface and hand the resolved one to both consecutive steps' is a problem_statement-only derivation -- the spec view restates a publicly-visible contract in anonymized terms and adds no fact that narrows the search space further.

THE TWO PLACES I PUSHED HARDEST, both cleared:
1. Componentwise pinning of the PAIR (result.1 AND result.2). This is the audit repair refinement.md describes, and it is the sharpest candidate leak: does naming a second consumer tell a solver something the public text doesn't? No -- the traceback prints frame `inset_locator.py:73` with lines 71-75 inline, so both `get_window_extent(renderer)` and `get_offset(..., renderer)` and their order are public. The pair is load-bearing (the prepatch refutation above goes through .2) without being privileged information.
2. Fallback SOURCE named as 'the host's drawing surface' (= ax.figure) rather than 'some present context'. Public statement gives `locator(ax, None)` so `ax` is the only in-scope object with a surface, and the same statement shows the artist's own `self.figure` is None -- so the source is derivable publicly, not disclosed. The spec also does not force the gold's SHAPE (parameter rebinding): it only pins both components to `some (suppliedContext.getD surfaceContext)`, which per-branch or bind-once impls satisfy equally.

BUNDLE-ADDRESSES-REVIEWER SCAN (reported as its own axis per my instructions): leakage.reviewer_directed() over every .lean/.md/.py/.json/.diff under the instance dir -> 0 files with hits. Manual grep for verdict-prescribing phrasing ('you should submit', 'the honest verdict', 'record as NO-LEAKAGE', 'reviewer', 'auditor', 'attacker') hits only prior-role audit prose inside lean/verdict.md and lean/meta.json recording their OWN past measurements, plus one incidental 'G-PANEL' mention in refinement.md's soundness bullet naming which gate the prepatch break is expected to trip. Nothing in the bundle instructs me how to record or which verdict is honest. NO FINDING on this axis.

**SCOPE NOTE:** mapping.md and refinement.md do quote patch.diff and name inset_locator.py:71-77 openly, but those are the audit binding documents, not the solver-visible spec view; the leak surface I judged is spec_view(Solution.lean), which is clean. Recording that distinction so the boundary I applied is explicit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
