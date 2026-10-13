# P2 adversarial audit — matplotlib__matplotlib-23314

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_14.lean`, `atk_15.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean`, `atk_20.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation was found whose correct_render closes with clean axioms and whose faithful refined patch fails to resolve. The prior recorded BROKEN verdict for this cell was against a SUPERSEDED spec that modeled draw as a PURE FUNCTION `RenderState -> RenderState`, where 'contributes nothing' was encoded as `result = rs`; that phrasing constrained only the RETURNED VALUE and so admitted a hidden branch that CALLED the emitter and then laundered the value back (atk_10/11/12/13 of the old record: `.take 0 ++ rs`, `.drop len`, `let _discarded := ...`). The current frozen Solution.lean has been repaired to an ACTION model — `problem_spec_render {m} [Monad m] (renderContents : m Unit) (self) (result : m Unit)` with `visible = false -> result = pure ()` and `visible = true -> result = renderContents`, proved under `[LawfulMonad m]` for an ARBITRARY monad `m` and an ARBITRARY `renderContents`. That repair closes exactly the hole: I re-encoded every old counterexample in the new model and each is now REJECTED, because performing the action on the hidden path leaves `renderContents >>= f = pure ()` to prove for an arbitrary action in an arbitrary lawful monad, which is false and cannot be laundered — `m` supplies no read-back and no undo. Re-encoded and rejected: atk_4 (call-then-return on hidden path, exit 1, goal `renderContents = pure ()`), atk_6 (`let _ <- renderContents` bind-discard, exit 1, same goal), atk_7 (`discard renderContents`, exit 1, goal `discard renderContents = pure ()`), atk_14 (Functor-map erasure `(fun _ => ()) <$> renderContents`, exit 1), atk_15 (seqRight `renderContents *> pure ()`, exit 1), atk_19 (Applicative `<*>`/`<*` laundering, exit 1), atk_20 (explicit `bind renderContents (fun _ => pure ())`, exit 1). The residual verifying phrasings are precisely the ones that DO NOT perform the action, and their faithful Python refinements all resolve.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -39,8 +39,6 @@
 -- impl-start
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
-  if !self.visible then
-    return
   renderContents
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -39,9 +39,7 @@
 -- impl-start
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
-  if !self.visible then
-    return
-  renderContents
+  return
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -39,7 +39,7 @@
 -- impl-start
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
-  if !self.visible then
+  if self.visible then
     return
   renderContents
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,6 +40,7 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
+    renderContents
     return
   renderContents
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -42,6 +42,7 @@
   if !self.visible then
     return
   renderContents
+  renderContents
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,6 +40,7 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
+    let _ ← renderContents
     return
   renderContents
 -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,6 +40,7 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
+    discard renderContents
     return
   renderContents
 -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -37,11 +37,11 @@
 -- post-conditions-end
 
 -- impl-start
+open Classical in
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
-    (self : Drawable) : m Unit := do
-  if !self.visible then
-    return
-  renderContents
+    (self : Drawable) : m Unit :=
+  if h : ∃ r : m Unit, problem_spec_render renderContents self r then h.choose
+  else pure ()
 -- impl-end
 
 -- proof-start
@@ -50,6 +50,11 @@
     problem_spec_render renderContents self
       (implementation_render renderContents self) := by
   intro m _ _ renderContents self
-  unfold problem_spec_render implementation_render
-  cases h : self.visible <;> simp
+  have hex : ∃ r : m Unit, problem_spec_render renderContents self r := by
+    refine ⟨if self.visible then renderContents else pure (), ?_⟩
+    unfold problem_spec_render
+    cases h : self.visible <;> simp [h]
+  unfold implementation_render
+  rw [dif_pos hex]
+  exact hex.choose_spec
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,6 +40,7 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
+    let _ := renderContents
     return
   renderContents
 -- impl-end
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,6 +40,8 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
+    for _ in ([] : List Unit) do
+      renderContents
     return
   renderContents
 -- impl-end
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -41,7 +41,7 @@
     (self : Drawable) : m Unit := do
   if !self.visible then
     return
-  renderContents
+  renderContents >>= fun _ => pure ()
 -- impl-end
 
 -- proof-start
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -39,9 +39,7 @@
 -- impl-start
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
-  if !self.visible then
-    return
-  renderContents
+  pure () >>= fun _ => if self.visible then renderContents else pure ()
 -- impl-end
 
 -- proof-start
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -37,11 +37,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
-    (self : Drawable) : m Unit := do
-  if !self.visible then
-    return
-  renderContents
+open Classical in
+noncomputable def implementation_render {m : Type → Type} [Monad m]
+    (renderContents : m Unit) (self : Drawable) : m Unit :=
+  if h : ∃ r : m Unit, problem_spec_render renderContents self r then h.choose
+  else pure ()
 -- impl-end
 
 -- proof-start
@@ -50,6 +50,11 @@
     problem_spec_render renderContents self
       (implementation_render renderContents self) := by
   intro m _ _ renderContents self
-  unfold problem_spec_render implementation_render
-  cases h : self.visible <;> simp
+  have hex : ∃ r : m Unit, problem_spec_render renderContents self r := by
+    refine ⟨if self.visible then renderContents else pure (), ?_⟩
+    unfold problem_spec_render
+    cases h : self.visible <;> simp [h]
+  unfold implementation_render
+  rw [dif_pos hex]
+  exact hex.choose_spec
 -- proof-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,6 +40,7 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
+    let _ ← (fun _ => ()) <$> renderContents
     return
   renderContents
 -- impl-end
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,8 +40,9 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
-    return
-  renderContents
+    renderContents *> pure ()
+  else
+    renderContents
 -- impl-end
 
 -- proof-start
```

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -37,11 +37,11 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
-    (self : Drawable) : m Unit := do
-  if !self.visible then
-    return
-  renderContents
+open Classical in
+noncomputable def implementation_render {m : Type → Type} [Monad m]
+    (renderContents : m Unit) (self : Drawable) : m Unit :=
+  if renderContents = pure () then renderContents
+  else if self.visible then renderContents else pure ()
 -- impl-end
 
 -- proof-start
@@ -51,5 +51,6 @@
       (implementation_render renderContents self) := by
   intro m _ _ renderContents self
   unfold problem_spec_render implementation_render
-  cases h : self.visible <;> simp
+  by_cases hp : renderContents = pure () <;>
+    cases h : self.visible <;> simp [hp, h]
 -- proof-end
```

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -41,7 +41,7 @@
     (self : Drawable) : m Unit := do
   if !self.visible then
     return
-  renderContents
+  renderContents >>= fun _ => renderContents >>= fun _ => pure ()
 -- impl-end
 
 -- proof-start
```

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -39,9 +39,10 @@
 -- impl-start
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
-  if !self.visible then
-    return
-  renderContents
+  if self.visible then
+    pure () >>= fun _ => pure ()
+  else
+    pure ()
 -- impl-end
 
 -- proof-start
```

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,8 +40,9 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
-    return
-  renderContents
+    (Function.const Unit () <$> renderContents) <* pure ()
+  else
+    renderContents
 -- impl-end
 
 -- proof-start
```

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -40,8 +40,9 @@
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
   if !self.visible then
-    return
-  renderContents
+    bind renderContents (fun _ => pure ())
+  else
+    renderContents
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -39,9 +39,10 @@
 -- impl-start
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
-  if !self.visible then
+  if self.visible then
+    renderContents
+  else
     return
-  renderContents
 -- impl-end
 
 -- proof-start
```

Prepatch bug re-encoded as an attack: `True`.

Worktree at base_commit 97fc1154992f64cfb2f86321155a7404efeb2d8a: (left git-clean; verified `git status --porcelain` empty after the extraction-fidelity check).

SAME-SPEC / ADMISSIBILITY: all 20 attacks + atk_pos are same_spec=True against the frozen Solution.lean AND admissible under the official screen. Command: `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open('<bundle>/Solution.lean').read(), open('atk_N.lean').read(), b.language))"` -> True for every file; plus `swebench_unified.variant_scope.is_admissible_variant` -> True and `variant_problems` -> [] for every file. Only the impl (+ proof tactic body) regions differ; the `theorem correct_render` STATEMENT is byte-identical everywhere; no new axiom/sorry/admit/native_decide/theorem.

### VERIFY RUNS (`bash scripts/lean_verify.sh <f>.lean`, launched concurrently in background batches of <=4):
  REJECTED (exit 1 — all with genuine spec-attributable `unsolved goals` error text, not empty/killed builds):
  - atk_1  exit 1 -- PREPATCH BUG re-encoded: unconditional `renderContents`. Goal left: `renderContents = pure ()` (case false). => prepatch_reproduced=True; matches G-DIFF.
  - atk_2  exit 1 -- partial-domain: `return` always (correct only when hidden). Goal: `pure PUnit.unit = renderContents` (case true).
  - atk_3  exit 1 -- control-flow-effect: INVERTED guard. BOTH goals left.
  - atk_4  exit 1 -- control-flow-effect: hidden branch CALLS `renderContents` then returns. Goal: `renderContents = pure ()`.
  - atk_5  exit 1 -- boundary/count: shown path renders TWICE. Goal: `(do renderContents; renderContents) = renderContents`.
  - atk_6  exit 1 -- laundering: hidden path `let _ <- renderContents`. Goal: `renderContents = pure ()`.
  - atk_7  exit 1 -- laundering: hidden path `discard renderContents`. Goal: `discard renderContents = pure ()`.
  - atk_8  exit 1 -- ungrounded-oracle echo (computable form): `Classical.choose` of the spec solution set; rejected at `dependsOnNoncomputable` (propDecidable).
  - atk_14 exit 1 -- laundering: Functor map `(fun _ => ()) <$> renderContents` on hidden path.
  - atk_15 exit 1 -- laundering: seqRight `renderContents *> pure ()` on hidden path.
  - atk_17 exit 1 -- boundary/count: laundered DOUBLE render on shown path via nested binds.
  - atk_18 exit 1 -- partial-domain: shown branch laundered no-op `pure () >>= fun _ => pure ()`.
  - atk_19 exit 1 -- laundering: Applicative `(Function.const Unit () <$> renderContents) <* pure ()`.
  - atk_20 exit 1 -- laundering: explicit `bind renderContents (fun _ => pure ())`.
  VERIFIED (exit 0) -- 6 attacks: atk_9, atk_10, atk_11, atk_12, atk_13, atk_16.
  POSITIVE CONTROL: atk_pos exit 0 -- structurally different (branches reordered: `if self.visible then renderContents else return`).
  FROZEN CONTROLS: gold_frozen.lean (= frozen Solution.lean) exit 0; prepatch_frozen.lean (= frozen Solution_prepatch.lean) exit 1. So the cell's own discrimination is live.

### AXIOM CHECKS (`#print axioms correct_render` appended; files atk_{9,10,11,12,13,16,pos}`_ax`.lean, ALL exit 0 under lean_verify.sh):
  - atk_9   [propext]                              CLEAN
  - atk_10  [propext, Quot.sound]                   CLEAN
  - atk_11  [propext, Quot.sound]                   CLEAN
  - atk_12  [propext, Quot.sound]                   CLEAN
  - atk_13  [propext, Classical.choice, Quot.sound] CLEAN (Classical.choice is a standard Mathlib axiom, not a bundle-declared/consumed one)
  - atk_16  [propext, Classical.choice, Quot.sound] CLEAN
  - atk_pos [propext]                               CLEAN
  No sorryAx anywhere; the bundle declares no `axiom` and no `opaque` (grep -E '^\s*(axiom|opaque)\b' Solution.lean -> none; meta.json axioms=[]). So all 6 verifying attacks are genuinely closed proofs and each REQUIRED a resolve run.

MANDATORY RESOLVE RUNS (swebench_unified.harness.run_resolve, instance matplotlib__matplotlib-23314, retries=0; runner rr.py; per-run JSON *.resolve.json). ALL completed=True, none inconclusive:
  - P_9.diff  (faithful to atk_9)  -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_10.diff (faithful to atk_10) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_11.diff (faithful to atk_11) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_12.diff (faithful to atk_12) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_13.diff (faithful to atk_13) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_16.diff (faithful to atk_16) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  CONTROLS:
  - P_A.diff = the GOLD patch verbatim -> resolved=TRUE, F2P 1/1, P2P 862/0. Oracle is live and this cell is resolvable.
  - P_B.diff = the `_draw_contents` helper-extraction refactor carrying GOLD behavior -> resolved=TRUE, F2P 1/1, P2P 862/0. This isolates the refactor IDIOM: since every attack patch uses the same extraction, a non-resolve would have been attributable to behavior, not to the idiom. (None occurred.)
  So: 6/6 verifying attacks have a materialized, apply-checked faithful patch that COMPLETED under the official oracle and RESOLVED. No verify⇏correct witness exists. => SOUND.

**WHY THE PATCHES ARE FAITHFUL REFINEMENTS:** each keeps the SHOWN path performing the extracted contents action exactly once (the spec pins it to the opaque term `renderContents`) and refines only the phrasing the Lean impl uses. `_draw_contents` is the A-reference `renderContents`: I mechanically verified its body is a VERBATIM copy of the 55 unchanged lines of `draw` (`self._unstale_viewLim()` ... `super().draw(renderer)`) — check in mkpatch.py + the extraction-fidelity script, result `VERBATIM: True`.

Correspondences: P_9 hidden path `_ = self._draw_contents` (the bound method NAMED, never invoked) <-> `let _ := renderContents`; P_10 `for _ in []: self._draw_contents(renderer)` (zero iterations) <-> `for _ in ([] : List Unit) do renderContents`; P_11 shown path `_ = self._draw_contents(renderer); return None` <-> `renderContents >>= fun _ => pure ()`; P_12 `_ = None` then the guard <-> `pure () >>= fun _ => if visible then renderContents else pure ()`; P_13 the Classical.choose witness `if visible then renderContents else pure ()` <-> the guarded dispatch; P_16 `_draw_contents_is_noop() -> False` then the guard <-> `if renderContents = pure () then renderContents else if visible then ... `.

In every case the Lean term does NOT carry out the action on the hidden path and the Python refinement correspondingly does NOT call the body — which is why they all resolve. Note this is the mirror image of the old broken spec: there the same syntactic families verified WHILE performing the action; under the action model only the genuinely non-performing phrasings survive.

**PATCH APPLICABILITY:** all 8 diffs checked with `git apply --check` in the base_commit worktree -> ALL APPLY (P_9, P_10, P_11, P_12, P_13, P_16, P_A, P_B).

### REFINEMENT.MD AUDIT (every leg must be R / A-consumed / A-reference / I; no kind-3):
  - Leg tagging is well-formed and COMPLETE: exactly two legs, op #1 = R, op #2 = A-reference. No kind-3 (inexpressible) leg is claimed or needed. meta.json agrees: axioms=[], deep_model_references=['renderContents'], modeled_functions=['render'], conf_skip=False, G-AX skip with reason 'no consumed callee axiom'.
  - R leg (op #1) is SOUND: `self.get_visible()` (reads `Artist._visible`) <-> `Drawable.visible` is a faithful Bool bijection, and the two added patch lines (`if not self.get_visible(): return`) are modeled exactly by `if !self.visible then return`, whose Lean meaning is `pure ()`. mapping.md pins the callee at axes3d.py:389 @ 97fc1154, which I confirmed against the worktree: the method is `@martist.allow_rasterization def draw(self, renderer)` at that line.
  - A-REFERENCE leg (op #2) CORRESPONDENCE HOLDS — this is where the previous spec failed and where the repair lands. `renderContents` is a universally quantified PARAMETER of type `m Unit` in an ARBITRARY `[Monad m] [LawfulMonad m]`, with NO asserted property, mapped to the unchanged remainder of `draw` (axes3d.py:390-447) bundled as one action. Three things make the correspondence sound rather than decorative: (a) the real callee is a VOID, SIDE-EFFECTING procedure returning None, and the model is now likewise an ACTION whose only observable is being carried out — not a returned value, so 'emitted nothing' and 'returned rs' can no longer come apart; (b) abstractness is load-bearing in the correct direction — `m` offers no read-back and no undo, exactly matching a write-only renderer, so an impl cannot do anything real `draw` cannot; (c) `[LawfulMonad m]` keeps the obligation behavioural rather than syntactic: re-sequencing one action (`renderContents >>= pure`) verifies, while changing the COUNT (atk_5, atk_17) or the BRANCH (atk_3) does not. I confirmed (a)-(c) empirically rather than accepting the prose: the 7 laundering vectors atk_4/6/7/14/15/19/20 are exactly the class the old model admitted, and all 7 are now rejected with the goal `renderContents = pure ()` (or its `discard`/map/seqRight variant) unsolved. mapping.md's claim that deleting `[LawfulMonad m]` breaks the shipped proof is consistent with this and is not needed for my verdict.
  - The one residual noted in refinement.md — that binding the action as a VALUE and discarding it (`let _ := renderContents`) verifies — is REAL (atk_9 exits 0) and its stated Python counterpart is CORRECT: naming the bound method without invoking it. I materialized precisely that (P_9: `_ = self._draw_contents`) and it RESOLVES, confirming the residual admits no counterpart that draws. Same for the zero-iteration loop (atk_10/P_10). So the documented residual is benign, as claimed.
  - G-CONF coverage claim is accurate for the current spec: mapping.md instantiates `m := StateM (List RenderOp)` and checks the hidden case as 'the operation log is untouched element for element', which is the executable reading of `result = pure ()` and DOES observe emission (not merely a returned value). This is the fix to the old fuzz domain, which compared return values only and was therefore blind to whether the hidden branch called the emitter.

ENVIRONMENT INCIDENT (disclosed; did NOT affect any reported verdict). My first four resolve attempts returned completed=False with docker `ImageNotFound`, INCLUDING on the gold control. Two distinct causes, both infrastructural, both resolved before any verdict was taken:

(1) a race — the official harness prints 'Cleaning cached images...

(2) A diagnostic run I made with `--namespace none` forced a LOCAL env-image rebuild, which drifted: a `setuptools_scm` DeprecationWarning ('release-branch-semver' renamed) is escalated to an error on every PNG save, failing 378/862 P2P for the GOLD patch. I recognized this as a host/environment defect and not a spec verdict — corroborated by this same instance having run at 06:19 and 06:24 today with 862/862 P2P passing, and by matplotlib__matplotlib-14623 showing the identical 350-failure signature at 09:40. Fix: `docker pull swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-23314:latest` to restore the canonical prebuilt image, and use run_resolve's own `namespace=swebench` (never `none`). Every resolve result reported above was taken AFTER that restoration, has completed=True, and is accompanied by a gold control resolving TRUE with 862/862 P2P in the same configuration. No timeouts and no incomplete oracle runs are counted as findings.

**FLOOR ACCOUNTING:** 20 admissible distinct same-spec attacks (>=5 required, >=4-6 further distinct wrong impls beyond the prior pass's set and the prepatch bug), spanning: prepatch bug (atk_1), partial-domain (atk_2, atk_18), control-flow-effect (atk_3, atk_4, atk_6, atk_7, atk_14, atk_15, atk_19, atk_20), boundary/call-count (atk_5, atk_17), ungrounded-oracle echo (atk_8, atk_13, atk_16), and value-binding/erasure residuals (atk_9, atk_10, atk_11, atk_12). Positive control verifies with clean axioms; prepatch reproduced (atk_1 exit 1, and the frozen Solution_prepatch.lean exit 1). 14 attacks rejected by the spec; 6 verified, and every one of those 6 had a materialized, apply-checked faithful patch RUN through the official harness — all 6 resolved, plus 2 controls resolving. Nothing inconclusive. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 20 admissible attacks re-run of 20 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 20 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 14 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_14.lean`, `atk_15.lean`, `atk_17.lean`, `atk_18.lean`, `atk_19.lean`, `atk_20.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_16.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. No same-spec wrong implementation was found whose correct_render closes with clean axioms and whose faithful refined patch fails to resolve. The prior recorded BROKEN verdict for this cell was against a SUPERSEDED spec that modeled draw as a PURE FUNCTION `RenderState -> RenderState`, where 'contributes nothing' was encoded as `result = rs`; that phrasing constrained only the RETURNED VALUE and so admitted a hidden branch that CALLED the emitter and then laundered the value back (atk_10/11/12/13 of the old record: `.take 0 ++ rs`, `.drop len`, `let _discarded := ...`). The current frozen Solution.lean has been repaired to an ACTION model — `problem_spec_render {m} [Monad m] (renderContents : m Unit) (self) (result : m Unit)` with `visible = false -> result = pure ()` and `visible = true -> result = renderContents`, proved under `[LawfulMonad m]` for an ARBITRARY monad `m` and an ARBITRARY `renderContents`. That repair closes exactly the hole: I re-encoded every old counterexample in the new model and each is now REJECTED, because performing the action on the hidden path leaves `renderContents >>= f = pure ()` to prove for an arbitrary action in an arbitrary lawful monad, which is false and cannot be laundered — `m` supplies no read-back and no undo. Re-encoded and rejected: atk_4 (call-then-return on hidden path, exit 1, goal `renderContents = pure ()`), atk_6 (`let _ <- renderContents` bind-discard, exit 1, same goal), atk_7 (`discard renderContents`, exit 1, goal `discard renderContents = pure ()`), atk_14 (Functor-map erasure `(fun _ => ()) <$> renderContents`, exit 1), atk_15 (seqRight `renderContents *> pure ()`, exit 1), atk_19 (Applicative `<*>`/`<*` laundering, exit 1), atk_20 (explicit `bind renderContents (fun _ => pure ())`, exit 1). The residual verifying phrasings are precisely the ones that DO NOT perform the action, and their faithful Python refinements all resolve.
```

**Attacks re-run (20):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 20 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 17 — `atk_17.lean` → rejected (same spec, does not verify — good)

Attack 18 — `atk_18.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -39,9 +39,10 @@
 -- impl-start
 def implementation_render {m : Type → Type} [Monad m] (renderContents : m Unit)
     (self : Drawable) : m Unit := do
-  if !self.visible then
+  if self.visible then
+    renderContents
+  else
     return
-  renderContents
 -- impl-end
 
 -- proof-start
```

Prepatch bug re-encoded as an attack: `True`.

Worktree at base_commit 97fc1154992f64cfb2f86321155a7404efeb2d8a: (left git-clean; verified `git status --porcelain` empty after the extraction-fidelity check).

SAME-SPEC / ADMISSIBILITY: all 20 attacks + atk_pos are same_spec=True against the frozen Solution.lean AND admissible under the official screen. Command: `python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open('<bundle>/Solution.lean').read(), open('atk_N.lean').read(), b.language))"` -> True for every file; plus `swebench_unified.variant_scope.is_admissible_variant` -> True and `variant_problems` -> [] for every file. Only the impl (+ proof tactic body) regions differ; the `theorem correct_render` STATEMENT is byte-identical everywhere; no new axiom/sorry/admit/native_decide/theorem.

### VERIFY RUNS (`bash scripts/lean_verify.sh <f>.lean`, launched concurrently in background batches of <=4):
  REJECTED (exit 1 — all with genuine spec-attributable `unsolved goals` error text, not empty/killed builds):
  - atk_1  exit 1 -- PREPATCH BUG re-encoded: unconditional `renderContents`. Goal left: `renderContents = pure ()` (case false). => prepatch_reproduced=True; matches G-DIFF.
  - atk_2  exit 1 -- partial-domain: `return` always (correct only when hidden). Goal: `pure PUnit.unit = renderContents` (case true).
  - atk_3  exit 1 -- control-flow-effect: INVERTED guard. BOTH goals left.
  - atk_4  exit 1 -- control-flow-effect: hidden branch CALLS `renderContents` then returns. Goal: `renderContents = pure ()`.
  - atk_5  exit 1 -- boundary/count: shown path renders TWICE. Goal: `(do renderContents; renderContents) = renderContents`.
  - atk_6  exit 1 -- laundering: hidden path `let _ <- renderContents`. Goal: `renderContents = pure ()`.
  - atk_7  exit 1 -- laundering: hidden path `discard renderContents`. Goal: `discard renderContents = pure ()`.
  - atk_8  exit 1 -- ungrounded-oracle echo (computable form): `Classical.choose` of the spec solution set; rejected at `dependsOnNoncomputable` (propDecidable).
  - atk_14 exit 1 -- laundering: Functor map `(fun _ => ()) <$> renderContents` on hidden path.
  - atk_15 exit 1 -- laundering: seqRight `renderContents *> pure ()` on hidden path.
  - atk_17 exit 1 -- boundary/count: laundered DOUBLE render on shown path via nested binds.
  - atk_18 exit 1 -- partial-domain: shown branch laundered no-op `pure () >>= fun _ => pure ()`.
  - atk_19 exit 1 -- laundering: Applicative `(Function.const Unit () <$> renderContents) <* pure ()`.
  - atk_20 exit 1 -- laundering: explicit `bind renderContents (fun _ => pure ())`.
  VERIFIED (exit 0) -- 6 attacks: atk_9, atk_10, atk_11, atk_12, atk_13, atk_16.
  POSITIVE CONTROL: atk_pos exit 0 -- structurally different (branches reordered: `if self.visible then renderContents else return`).
  FROZEN CONTROLS: gold_frozen.lean (= frozen Solution.lean) exit 0; prepatch_frozen.lean (= frozen Solution_prepatch.lean) exit 1. So the cell's own discrimination is live.

### AXIOM CHECKS (`#print axioms correct_render` appended; files atk_{9,10,11,12,13,16,pos}`_ax`.lean, ALL exit 0 under lean_verify.sh):
  - atk_9   [propext]                              CLEAN
  - atk_10  [propext, Quot.sound]                   CLEAN
  - atk_11  [propext, Quot.sound]                   CLEAN
  - atk_12  [propext, Quot.sound]                   CLEAN
  - atk_13  [propext, Classical.choice, Quot.sound] CLEAN (Classical.choice is a standard Mathlib axiom, not a bundle-declared/consumed one)
  - atk_16  [propext, Classical.choice, Quot.sound] CLEAN
  - atk_pos [propext]                               CLEAN
  No sorryAx anywhere; the bundle declares no `axiom` and no `opaque` (grep -E '^\s*(axiom|opaque)\b' Solution.lean -> none; meta.json axioms=[]). So all 6 verifying attacks are genuinely closed proofs and each REQUIRED a resolve run.

MANDATORY RESOLVE RUNS (swebench_unified.harness.run_resolve, instance matplotlib__matplotlib-23314, retries=0; runner rr.py; per-run JSON *.resolve.json). ALL completed=True, none inconclusive:
  - P_9.diff  (faithful to atk_9)  -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_10.diff (faithful to atk_10) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_11.diff (faithful to atk_11) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_12.diff (faithful to atk_12) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_13.diff (faithful to atk_13) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  - P_16.diff (faithful to atk_16) -> resolved=TRUE, applied=True, F2P 1/1, P2P 862 ok / 0 fail
  CONTROLS:
  - P_A.diff = the GOLD patch verbatim -> resolved=TRUE, F2P 1/1, P2P 862/0. Oracle is live and this cell is resolvable.
  - P_B.diff = the `_draw_contents` helper-extraction refactor carrying GOLD behavior -> resolved=TRUE, F2P 1/1, P2P 862/0. This isolates the refactor IDIOM: since every attack patch uses the same extraction, a non-resolve would have been attributable to behavior, not to the idiom. (None occurred.)
  So: 6/6 verifying attacks have a materialized, apply-checked faithful patch that COMPLETED under the official oracle and RESOLVED. No verify⇏correct witness exists. => SOUND.

**WHY THE PATCHES ARE FAITHFUL REFINEMENTS:** each keeps the SHOWN path performing the extracted contents action exactly once (the spec pins it to the opaque term `renderContents`) and refines only the phrasing the Lean impl uses. `_draw_contents` is the A-reference `renderContents`: I mechanically verified its body is a VERBATIM copy of the 55 unchanged lines of `draw` (`self._unstale_viewLim()` ... `super().draw(renderer)`) — check in mkpatch.py + the extraction-fidelity script, result `VERBATIM: True`.

Correspondences: P_9 hidden path `_ = self._draw_contents` (the bound method NAMED, never invoked) <-> `let _ := renderContents`; P_10 `for _ in []: self._draw_contents(renderer)` (zero iterations) <-> `for _ in ([] : List Unit) do renderContents`; P_11 shown path `_ = self._draw_contents(renderer); return None` <-> `renderContents >>= fun _ => pure ()`; P_12 `_ = None` then the guard <-> `pure () >>= fun _ => if visible then renderContents else pure ()`; P_13 the Classical.choose witness `if visible then renderContents else pure ()` <-> the guarded dispatch; P_16 `_draw_contents_is_noop() -> False` then the guard <-> `if renderContents = pure () then renderContents else if visible then ... `.

In every case the Lean term does NOT carry out the action on the hidden path and the Python refinement correspondingly does NOT call the body — which is why they all resolve. Note this is the mirror image of the old broken spec: there the same syntactic families verified WHILE performing the action; under the action model only the genuinely non-performing phrasings survive.

**PATCH APPLICABILITY:** all 8 diffs checked with `git apply --check` in the base_commit worktree -> ALL APPLY (P_9, P_10, P_11, P_12, P_13, P_16, P_A, P_B).

### REFINEMENT.MD AUDIT (every leg must be R / A-consumed / A-reference / I; no kind-3):
  - Leg tagging is well-formed and COMPLETE: exactly two legs, op #1 = R, op #2 = A-reference. No kind-3 (inexpressible) leg is claimed or needed. meta.json agrees: axioms=[], deep_model_references=['renderContents'], modeled_functions=['render'], conf_skip=False, G-AX skip with reason 'no consumed callee axiom'.
  - R leg (op #1) is SOUND: `self.get_visible()` (reads `Artist._visible`) <-> `Drawable.visible` is a faithful Bool bijection, and the two added patch lines (`if not self.get_visible(): return`) are modeled exactly by `if !self.visible then return`, whose Lean meaning is `pure ()`. mapping.md pins the callee at axes3d.py:389 @ 97fc1154, which I confirmed against the worktree: the method is `@martist.allow_rasterization def draw(self, renderer)` at that line.
  - A-REFERENCE leg (op #2) CORRESPONDENCE HOLDS — this is where the previous spec failed and where the repair lands. `renderContents` is a universally quantified PARAMETER of type `m Unit` in an ARBITRARY `[Monad m] [LawfulMonad m]`, with NO asserted property, mapped to the unchanged remainder of `draw` (axes3d.py:390-447) bundled as one action. Three things make the correspondence sound rather than decorative: (a) the real callee is a VOID, SIDE-EFFECTING procedure returning None, and the model is now likewise an ACTION whose only observable is being carried out — not a returned value, so 'emitted nothing' and 'returned rs' can no longer come apart; (b) abstractness is load-bearing in the correct direction — `m` offers no read-back and no undo, exactly matching a write-only renderer, so an impl cannot do anything real `draw` cannot; (c) `[LawfulMonad m]` keeps the obligation behavioural rather than syntactic: re-sequencing one action (`renderContents >>= pure`) verifies, while changing the COUNT (atk_5, atk_17) or the BRANCH (atk_3) does not. I confirmed (a)-(c) empirically rather than accepting the prose: the 7 laundering vectors atk_4/6/7/14/15/19/20 are exactly the class the old model admitted, and all 7 are now rejected with the goal `renderContents = pure ()` (or its `discard`/map/seqRight variant) unsolved. mapping.md's claim that deleting `[LawfulMonad m]` breaks the shipped proof is consistent with this and is not needed for my verdict.
  - The one residual noted in refinement.md — that binding the action as a VALUE and discarding it (`let _ := renderContents`) verifies — is REAL (atk_9 exits 0) and its stated Python counterpart is CORRECT: naming the bound method without invoking it. I materialized precisely that (P_9: `_ = self._draw_contents`) and it RESOLVES, confirming the residual admits no counterpart that draws. Same for the zero-iteration loop (atk_10/P_10). So the documented residual is benign, as claimed.
  - G-CONF coverage claim is accurate for the current spec: mapping.md instantiates `m := StateM (List RenderOp)` and checks the hidden case as 'the operation log is untouched element for element', which is the executable reading of `result = pure ()` and DOES observe emission (not merely a returned value). This is the fix to the old fuzz domain, which compared return values only and was therefore blind to whether the hidden branch called the emitter.

ENVIRONMENT INCIDENT (disclosed; did NOT affect any reported verdict). My first four resolve attempts returned completed=False with docker `ImageNotFound`, INCLUDING on the gold control. Two distinct causes, both infrastructural, both resolved before any verdict was taken:

(1) a race — the official harness prints 'Cleaning cached images...

(2) A diagnostic run I made with `--namespace none` forced a LOCAL env-image rebuild, which drifted: a `setuptools_scm` DeprecationWarning ('release-branch-semver' renamed) is escalated to an error on every PNG save, failing 378/862 P2P for the GOLD patch. I recognized this as a host/environment defect and not a spec verdict — corroborated by this same instance having run at 06:19 and 06:24 today with 862/862 P2P passing, and by matplotlib__matplotlib-14623 showing the identical 350-failure signature at 09:40. Fix: `docker pull swebench/sweb.eval.x86_64.matplotlib_1776_matplotlib-23314:latest` to restore the canonical prebuilt image, and use run_resolve's own `namespace=swebench` (never `none`). Every resolve result reported above was taken AFTER that restoration, has completed=True, and is accompanied by a gold control resolving TRUE with 862/862 P2P in the same configuration. No timeouts and no incomplete oracle runs are counted as findings.

**FLOOR ACCOUNTING:** 20 admissible distinct same-spec attacks (>=5 required, >=4-6 further distinct wrong impls beyond the prior pass's set and the prepatch bug), spanning: prepatch bug (atk_1), partial-domain (atk_2, atk_18), control-flow-effect (atk_3, atk_4, atk_6, atk_7, atk_14, atk_15, atk_19, atk_20), boundary/call-count (atk_5, atk_17), ungrounded-oracle echo (atk_8, atk_13, atk_16), and value-binding/erasure residuals (atk_9, atk_10, atk_11, atk_12). Positive control verifies with clean axioms; prepatch reproduced (atk_1 exit 1, and the frozen Solution_prepatch.lean exit 1). 14 attacks rejected by the spec; 6 verified, and every one of those 6 had a materialized, apply-checked faithful patch RUN through the official harness — all 6 resolved, plus 2 controls resolving. Nothing inconclusive. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-2 (faithfulness-break) on matplotlib__matplotlib-23314 / lean. Verdict FAITHFUL: no input found on which problem_spec_render disagrees with the real patched callee. Searched for over-strength and drift; found none.

SCOPE / REFERENCE. Modeled function = Axes3D.draw, lib/mpl_toolkits/mplot3d/axes3d.py:389. Reference = worktree at base_commit 97fc115499 with patch.diff APPLIED (git diff confirms exactly the 2 added lines, only file touched); base worktree used only for unchanged callees. patch.diff is byte-identical to instance.json['patch'] (verified in Python).

**SPEC-REGION IDENTITY.** markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend()) = True, so G-DIFF's rival shares the frozen spec view. Recomputed markers.region_hashes matches meta.json['region_hashes'] on all 5 regions (axioms/impl/post-conditions/proof/spec_view). sha256(Solution.lean)=a3fa6e8d... == meta G-VERIFY source hash, so the audited bytes are the shipped bytes. Diff sol vs prepatch is confined to impl+proof (prepatch drops the guard).

PROOF IS REAL, NOT FAKE. scripts/lean_verify.sh on Solution.lean + appended probes: exit 0. `#print axioms correct_render` => [propext] only — NO sorryAx. implementation_render and problem_spec_render depend on no axioms. Bundle declares no `axiom`, no `opaque`, no `sorry`/`admit`, no native_decide in the shipped file (grep clean); meta axioms: [] is accurate and G-AX's skip stub is justified (no `_prop` is asserted on renderContents, so there is nothing to validate).

SPEC DISCRIMINATES (non-vacuity, machine-checked). I instantiated the quantified monad at StateM (List Nat) with rc := modify (++[7]) and proved, all compiling exit 0:
 - hidden: ((implementation_render rc {visible:=false}).run [1,2,3]).2 = [1,2,3] (log untouched element for element)
 - shown:  ((implementation_render rc {visible:=true}).run [1,2,3]).2 = [1,2,3,7] (body once)
 - NOT problem_spec_render rc {visible:=false} (prepatch ...) — the BASE-COMMIT action (body unconditionally) is provably REJECTED
 - NOT problem_spec_render rc {visible:=true} (twice ...) — double-draw rejected
 - NOT problem_spec_render rc {visible:=false} (inverted ...) — inverted guard rejected
 - spec is satisfiable at the concrete monad via correct_render (not contradictory).
So the postcondition is neither vacuous nor self-contradictory, and it bites exactly on the patch delta.

EMPIRICAL AGREEMENT WITH THE REAL CALLEE (both branches, live matplotlib). Wrapped the renderer in a spy that counts every primitive op and invoked the real draw:
 - visible=True  -> 251 renderer ops emitted; visible=False -> 0 ops. Exactly the spec's two conjuncts (shown = body once; hidden = pure ()).
 AST check on the patched source: the guard is the FIRST statement of draw (11 total), test is `not self.get_visible()`, body is a BARE `return` (value is None), no else. So nothing in the modeled function executes before the short-circuit — `result = pure ()` is literally right.

OFF-DOMAIN / ABSTRACTION PROBES (where an over-strong Bool model would break, and did not):
 - Drawable.visible : Bool vs Python truthiness. Probed `_visible` in {True,False,1,0,None,'',"x",[],[1]}: real inner draw emitted 251 ops iff bool(val) is True, 0 ops iff False, in all 9 cases. The real code uses the flag ONLY in a truthiness test, so the Bool model is a faithful quotient, not a strengthening.
 - renderer=None on the hidden path: real 3D inner draw returns cleanly (whereas 2D `_AxesBase`.draw raises RuntimeError first). The Lean hidden case likewise performs nothing and cannot fail — agrees; no divergence.
 - get_visible is NOT overridden anywhere on the Axes3D MRO (single def at artist.py:809, `return self._visible`), so modeling it as a field rather than an opaque callee is sound.
 - Axes3D defines draw exactly once (no shadowing); self.get_visible() is not read by the unchanged body (line 416 reads CHILD artists' get_visible), so there is no circularity in holding renderContents independent of self.visible.

### RECORDED NON-DEFECTS (examined, deliberately not scored as unfaithfulness):
 1. The @martist.allow_rasterization decorator sits OUTSIDE the guard, so the DECORATED wrapper is not a no-op when hidden: with set_rasterized(True) the wrapper still emits start_rasterizing (1 op), and with an agg_filter it emits start_filter/stop_filter (2 ops), while the inner body emits 0. This is NOT drift: mapping.md scopes implementation_render to the inner function at axes3d.py:389, the patch edits the inner function, and the decorator is unchanged by the patch — attributing the wrapper's pre/post hooks to the model would be exactly the base-vs-patched confusion the brief warns against. The spec's claim about the inner function is empirically exact (0 inner ops when hidden in every rasterized/agg_filter configuration I probed).
 2. Citation imprecision only: mapping.md gives renderContents as "axes3d.py:390-447"; the actual unchanged body is 392-446 post-patch (390-444 at base). Off by a couple of lines in a prose line-range; the symbol binding and the modeled boundary are correct. Cosmetic, not a spec defect.
 3. conformance_check.py's oracle is an in-process replica rather than a driven matplotlib figure. I did not rely on it — I replaced that evidence with the live-renderer spy probe above, which independently reproduces its conclusion (hidden 0 ops / shown body-once).

**STRENGTH DIRECTION.** The spec pins BOTH branches to the inputs, so it is as strong as it can be without being false; I specifically hunted for the over-strength failure mode (a conjunct the real code violates) and found none — every conjunct is witnessed by the real callee on the branch it governs. Note the residual already recorded in meta.json (an impl may BIND renderContents as a value and never sequence it, which verifies and whose Python counterpart names the bound method without calling it, hence draws nothing and resolves) — that is a soundness-preserving residual, not a faithfulness break, and it does not yield a diverging input.

**HOUSEKEEPING.** nothing written into the bundle or the repo root; no meta.json/verdict.md staged or modified.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

Attacker-3 (leakage / gold-reconstruction), matplotlib__matplotlib-23314/lean. Independently measured against the CURRENTLY LANDED artifact; nothing inherited from verdict.md/meta.json.

**NO RELAXATION PRESENT.** `find benchmark-verified/matplotlib__matplotlib-23314 -iname '*relax*'` -> empty; no RELAXED_LEAKAGE.md anywhere under the instance dir; meta.json has no `relaxed_leakage` key (walked top-level keys: axioms, conf_skip, deep_model_references, gates, instance_id, modeled_functions, notes, pbt_audit, region_hashes, schema_version, spec_provenance, verifier_pins). So there is no unavoidability argument to re-derive and no facet-scoped disposition to inherit: this is a plain strict-mode leakage review, judged as such.

ARTIFACT IDENTITY FIRST (this matters here). Solution.lean on disk = sha256 a3fa6e8d10f67c7cfccc430994133805c8cacc3dbbe7f5cad979892a22fe8bf2, matching meta.json gates G-VERIFY/G-CONF/G-DIFF/G-GOLD/G-LEAK/G-HYGIENE sources. The four stored G-PANEL* records (including a prior G-PANEL-3 pass) were computed against sha 019d5a9d91..., a SUPERSEDED RenderState-based model (pure `RenderState -> RenderState` carrier, spec_view sha 7e72c202...). Their recorded reasoning, their quoted spec text (`opaque renderContents`, `result = rs`), and their spec_view hash do not describe the file I reviewed, so I re-measured everything from source rather than reading them forward. My spec_view sha256(spec_signature) = 5902851e61ef9a833b140c60a1064322a1731af7932104305ec99758837dfbef; region_hashes recomputed via markers.region_hashes MATCH meta.json on all five keys (axioms, post-conditions, impl, proof, spec_view) for the landed file.

### What I ran
1. Spec-region byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True, and markers.spec_view of the two legs is byte-for-byte equal. The entire gold delta lives in the elided impl+proof regions, so the consumer-visible spec is literally the same string before and after the fix and cannot, by construction, encode the edit. This is the strongest available leakage evidence and it is a measurement, not an argument.
2. Mechanical screen re-run from source: leakage.screen(Solution.lean, LeanBackend.language, gold patch, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. Confirmed patch.diff on disk == instance.json['patch'] byte-for-byte first, so the screen ran against the real gold.
3. Manual repo-symbol sweep over the spec view (case-insensitive): NO occurrence of axes3d, mplot3d, Axes3D, get_visible, set_visible, apply_aspect, `_unstale_viewLim`, allow_rasterization, renderer, projection, subplot, or the patched path lib/mpl_toolkits/mplot3d/axes3d.py. Full identifier inventory of the spec view is generic modeling vocabulary only: Drawable, visible, problem_spec_render, renderContents, result, m, Monad, Unit, Bool, Prop. No diff markers (@@, diff --git, +++, index); no `_NARRATION_RE` hit (no bug/fix/patched/previously/regression/broken/incorrectly).
4. Test-patch leakage: extracted test names from instance.json['test_patch'] (test_invisible_axes, test_invisible_axes_events, test_redraw_in_frame, test_get_labels, test_aspect_equal_error) -- none appears in the spec view.
5. Proof genuineness, so the disposition rests on a real artifact and not a vacuous pass: mktemp -d copy, appended `#print axioms correct_render`, scripts/lean_verify.sh -> exit 0 with "'correct_render' depends on axioms: [propext]" -- clean, NO sorryAx. Control: scripts/lean_verify.sh Solution_prepatch.lean -> exit 1 with a real elaboration error (line 53: `simp` made no progress), i.e. the spec genuinely rejects the pre-patch behavior, so the G-DIFF/G-GOLD pair is sound.

### LINE-BY-LINE READ OF THE SPEC VIEW (the only consumer-visible text)
- Header docstring ("a component that is hidden must contribute nothing to the output -- it must carry out no drawing at all -- while a shown component renders its full contents"): a restatement of the public Expected outcome, "the subplot is not visible if the value is set to False", against the public Actual outcome, "the subplot remains visible". Nothing beyond the statement.
- `structure Drawable where visible : Bool`: `visible` / `set_visible` / `False` are verbatim public vocabulary in the problem_statement.
- post-conditions docstring: it argues WHY an arbitrary effect monad is the right carrier (write-only renderer: no read-back, no undo). This is a justification of the Lean abstraction's own shape, not a fact about the repo. It names no file, class, method, decorator, or control-flow mechanism, and in particular never says "early return" or "guard".
- `problem_spec_render`: `(visible = false -> result = pure ()) AND (visible = true -> result = renderContents)`. Both conjuncts are a direct formalization of the publicly stated expected/actual pair. Anyone holding only the problem_statement derives "hidden draws nothing / shown draws everything" from "the subplot is not visible if the value is set to False" -- the discriminator is problem_statement-derivable, so there is nothing here that could only have come from reading the gold.
- The view is strictly LESS localizing than the public statement: it never mentions 3d, projection, or subplot at all, whereas the problem_statement does. A solver holding only this view still has to find Axes3D.draw and choose the mechanism itself.

**BUNDLE-INTEGRITY CHECK ON MY OWN ROLE.** Ran leakage.reviewer_directed over every lean/*.md, *.json, *.py, *.lean in the bundle -- zero hits on all four `_REVIEWER_DIRECTED` rules (addresses-the-reviewer, prescribes-the-verdict x2, recording-convention). Independent grep for auditor/panel/'honest verdict'/'you must record' found only the stored prior-panel notes narrating their own past findings, which is a record, not an instruction to me. No file addresses this role, tells me how to record, or asserts which verdict is honest. Nothing to report as a steering finding. refinement.md and mapping.md do name get_visible, Axes3D.draw and the patched path -- correct and expected: they are provenance docs outside the consumer spec view and are the intended home for that mapping.

ONE OBSERVATION FOR THE RECORD (not a leakage finding, outside my gate): the stored G-PANEL/G-PANEL-1/-2/-3 records are stale by artifact -- they judge sha 019d5a9d91 while the landed spec is a3fa6e8d10 with a different carrier. G-PANEL-1's recorded fail (atk_10 verify-but-not-resolve on the RenderState model) is what the current monadic carrier was authored to close, per meta.json notes. Routing/freshness matter, not mine to dispose of, but a re-audit of the too-weak lane against a3fa6e8d10 is what those records call for.

**VERDICT:** NO-LEAKAGE. spec_view(gold) == spec_view(prepatch) byte-for-byte proves the gold edit is entirely outside the consumer-visible region; the mechanical screen is clean; and every claim the spec view makes is derivable from the public problem_statement alone, while the view withholds the file, class, method and mechanism the statement itself partially reveals.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
