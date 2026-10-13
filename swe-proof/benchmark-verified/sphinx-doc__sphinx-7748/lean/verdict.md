# P2 adversarial audit — sphinx-doc__sphinx-7748

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_dropcont.lean`, `atk2_reverse.lean`, `atk3_allblocks.lean`, `atk4_alwaysbreak.lean`, `atk5_nostrip.lean`, `atk6_noemptybreak.lean`, `atk7_swapfields.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -121,393 +121,18 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- ECHO: return the spec function directly. -/
 def implementation_collectSignatures
-    (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
-  let mut result : Option Sig := none
-  let mut signatures : List Sig := []
-  for doclines in docstrings do
-    for line0 in doclines do
-      if line0.isEmpty then
-        break
-      let multiline := line0.endsWith "\\"
-      let line := if multiline then stripContinuation line0 else line0
-      match matchSig line with
-      | none => continue
-      | some m =>
-        if validNames.contains m.base then
-          if result.isNone then
-            result := some ⟨m.args, m.retann⟩
-          else
-            signatures := signatures ++ [⟨m.args, m.retann⟩]
-          if multiline then
-            continue
-          else
-            break
-        else
-          continue
-    if result.isSome then
-      break
-  match result with
-  | none => return []
-  | some r => return r :: signatures
+    (docstrings : List (List String)) (validNames : List String) : List Sig :=
+  collectSpec validNames docstrings
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
       problem_spec_collectSignatures docstrings validNames
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
-  show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  rfl
 -- proof-end
```

Attack 2 — `atk1_dropcont.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- WRONG(atk1): drops all continuation signatures, returns only the primary. -/
 def implementation_collectSignatures
     (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
   let mut result : Option Sig := none
@@ -155,344 +150,10 @@
       break
   match result with
   | none => return []
-  | some r => return r :: signatures
+  | some r => return [r]
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
@@ -500,14 +161,6 @@
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
   show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  simp [implementation_collectSignatures, collectSpec, scanDoc, stripContinuation, Id.run]
+  rfl
 -- proof-end
```

Attack 3 — `atk2_reverse.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- WRONG(atk2): reverses the continuation signatures order. -/
 def implementation_collectSignatures
     (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
   let mut result : Option Sig := none
@@ -155,344 +150,10 @@
       break
   match result with
   | none => return []
-  | some r => return r :: signatures
+  | some r => return r :: signatures.reverse
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
@@ -500,14 +161,6 @@
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
   show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  simp [implementation_collectSignatures, collectSpec, scanDoc, stripContinuation, Id.run]
+  rfl
 -- proof-end
```

Attack 4 — `atk3_allblocks.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- WRONG(atk3): does not stop at first block; accumulates across all blocks. -/
 def implementation_collectSignatures
     (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
   let mut result : Option Sig := none
@@ -151,348 +146,12 @@
             break
         else
           continue
-    if result.isSome then
-      break
   match result with
   | none => return []
   | some r => return r :: signatures
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
@@ -500,14 +159,6 @@
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
   show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  simp [implementation_collectSignatures, collectSpec, scanDoc, stripContinuation, Id.run]
+  rfl
 -- proof-end
```

Attack 5 — `atk4_alwaysbreak.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,8 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- WRONG(atk4): ignores the multiline flag for control flow — always breaks after
+first accepted signature (so continuation runs collapse to a single signature). -/
 def implementation_collectSignatures
     (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
   let mut result : Option Sig := none
@@ -145,10 +141,7 @@
             result := some ⟨m.args, m.retann⟩
           else
             signatures := signatures ++ [⟨m.args, m.retann⟩]
-          if multiline then
-            continue
-          else
-            break
+          break
         else
           continue
     if result.isSome then
@@ -159,340 +152,6 @@
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
@@ -500,14 +159,6 @@
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
   show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  simp [implementation_collectSignatures, collectSpec, scanDoc, stripContinuation, Id.run]
+  rfl
 -- proof-end
```

Attack 6 — `atk5_nostrip.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,8 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- WRONG(atk5): does NOT strip the continuation marker before matching — matches
+the raw line0 (with trailing backslash/whitespace) instead of stripContinuation. -/
 def implementation_collectSignatures
     (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
   let mut result : Option Sig := none
@@ -136,7 +132,7 @@
       if line0.isEmpty then
         break
       let multiline := line0.endsWith "\\"
-      let line := if multiline then stripContinuation line0 else line0
+      let line := line0
       match matchSig line with
       | none => continue
       | some m =>
@@ -159,340 +155,6 @@
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
@@ -500,14 +162,6 @@
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
   show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  simp [implementation_collectSignatures, collectSpec, scanDoc, stripContinuation, Id.run]
+  rfl
 -- proof-end
```

Attack 7 — `atk6_noemptybreak.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,8 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- WRONG(atk6): empty line does not terminate the run — it is skipped (continue),
+so signatures after a blank line are still collected. -/
 def implementation_collectSignatures
     (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
   let mut result : Option Sig := none
@@ -134,7 +130,7 @@
   for doclines in docstrings do
     for line0 in doclines do
       if line0.isEmpty then
-        break
+        continue
       let multiline := line0.endsWith "\\"
       let line := if multiline then stripContinuation line0 else line0
       match matchSig line with
@@ -159,340 +155,6 @@
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
@@ -500,14 +162,6 @@
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
   show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  simp [implementation_collectSignatures, collectSpec, scanDoc, stripContinuation, Id.run]
+  rfl
 -- proof-end
```

Attack 8 — `atk7_swapfields.lean` → rejected (same spec, does not verify — good)

```diff
@@ -121,12 +121,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Collect every signature offered at the start of a documentation comment.
-The blocks are scanned in order; within a block the lines are read top to bottom
-until an empty line, the first signature is kept as the primary one and any
-further continuation signatures are appended, and the scan of a block stops at
-its first non-continuation signature line. The first block that yields a
-signature provides the result. -/
+/-- WRONG(atk7): swaps args and retann fields in each collected Sig. -/
 def implementation_collectSignatures
     (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
   let mut result : Option Sig := none
@@ -142,9 +137,9 @@
       | some m =>
         if validNames.contains m.base then
           if result.isNone then
-            result := some ⟨m.args, m.retann⟩
+            result := some ⟨m.retann, m.args⟩
           else
-            signatures := signatures ++ [⟨m.args, m.retann⟩]
+            signatures := signatures ++ [⟨m.retann, m.args⟩]
           if multiline then
             continue
           else
@@ -159,340 +154,6 @@
 -- impl-end
 
 -- proof-start
--- ==== module: defs ====
-
--- @decl:LoopState-start
-/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
-loops as their `ForInStep` state: `result` holds the primary (first-accepted)
-signature once found, `signatures` accumulates the continuation signatures. -/
-abbrev LoopState : Type := Option Sig × List Sig
--- @decl:LoopState-end
-
--- @decl:InnerBody-start
-/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
-threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
-`continue` ↦ `ForInStep.yield`. -/
-def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
-    ForInStep LoopState :=
-  if line0.isEmpty then
-    ForInStep.done st
-  else
-    let multiline := line0.endsWith "\\"
-    let line := if multiline then stripContinuation line0 else line0
-    match matchSig line with
-    | none => ForInStep.yield st
-    | some m =>
-      if validNames.contains m.base then
-        if st.1.isNone then
-          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
-          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
-        else
-          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
-      else
-        ForInStep.yield st
--- @decl:InnerBody-end
-
--- @decl:OuterBody-start
-/-- The desugared body of the outer `for doclines in docstrings` loop: run the
-inner loop on the block, then `if result.isSome then break`. -/
-def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
-    ForInStep LoopState :=
-  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
-  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
--- @decl:OuterBody-end
-
--- @decl:innerCharacterization-start
-/-- Relation between the inner loop's entry state `entry` and exit state `exit`
-over `block`: the leading run collected by `scanDoc` is distributed — its head
-fills an empty `result`, its tail is appended to `signatures`; when `result` is
-already set, the whole run is appended to `signatures`. -/
-def innerCharacterization (validNames : List String) (block : List String)
-    (entry exit : LoopState) : Prop :=
-  match entry.1 with
-  | none =>
-    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
-  | some r0 =>
-    exit = (some r0, entry.2 ++ scanDoc validNames block)
--- @decl:innerCharacterization-end
-
--- @decl:outerCharacterization-start
-/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
-the exit state reproduces `collectSpec validNames docstrings` split into its
-head (the primary `result`) and tail (the continuation `signatures`). -/
-def outerCharacterization (validNames : List String) (docstrings : List (List String))
-    (exit : LoopState) : Prop :=
-  match collectSpec validNames docstrings with
-  | [] => exit = (none, [])
-  | r :: rest => exit = (some r, rest)
--- @decl:outerCharacterization-end
-
--- ==== module: Bridges ====
-
--- @ns:isEmpty_bridge-start
--- @decl:isEmpty_bridge-start
-/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
-theorem isEmpty_bridge (line0 : String) :
-    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
-  refine ⟨String.isEmpty_iff line0, ?_⟩
-  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
--- @decl:isEmpty_bridge-end
--- @ns:isEmpty_bridge-end
-
--- @ns:forIn_step_reduction-start
--- @decl:forIn_step_reduction-start
-/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
-mapping `ForInStep.done`/`yield` to stop/recurse. -/
-theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
-    (body : α → β → Id (ForInStep β)) :
-    (forIn (a :: as) b body : Id β)
-      = (match (body a b : Id (ForInStep β)) with
-         | ForInStep.done b' => (pure b' : Id β)
-         | ForInStep.yield b' => forIn as b' body) := by
-  simp only [List.forIn_cons, bind, pure]
-  cases body a b <;> rfl
--- @decl:forIn_step_reduction-end
--- @ns:forIn_step_reduction-end
-
--- @ns:classification_defeq-start
--- @decl:classification_defeq-start
-/-- On a non-empty line, `InnerBody` reduces to the same classification
-sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
-with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
-theorem classification_defeq (validNames : List String) (line0 : String)
-    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
-    InnerBody validNames line0 (result, sigs)
-      = (let multiline := line0.endsWith "\\"
-         let line := if multiline then stripContinuation line0 else line0
-         match matchSig line with
-         | none => ForInStep.yield (result, sigs)
-         | some m =>
-           if validNames.contains m.base then
-             if result.isNone then
-               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
-               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
-             else
-               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
-               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
-           else ForInStep.yield (result, sigs)) := by
-  simp only [InnerBody, h, Bool.false_eq_true, if_false]
--- @decl:classification_defeq-end
--- @ns:classification_defeq-end
-
--- ==== module: InnerLoop ====
-
--- @ns:inner_loop_characterization-start
--- @decl:inner_loop_characterization-start
-/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
-doclines` across the threaded `(result, signatures)` state. -/
-theorem inner_loop_characterization (validNames : List String) (doclines : List String)
-    (result : Option Sig) (sigs : List Sig) :
-    innerCharacterization validNames doclines (result, sigs)
-      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
-  induction doclines generalizing result sigs with
-  | nil =>
-    cases result with
-    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
-        List.append_nil, forIn, List.forIn_nil]; rfl
-    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
-        List.forIn_nil]; rfl
-  | cons line0 rest ih =>
-    rw [forIn_step_reduction]
-    by_cases hEmpty : line0.isEmpty = true
-    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
-      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
-        simp [InnerBody, hEmpty]
-      rw [hb]
-      cases result with
-      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
-          List.tail_nil, List.append_nil]; rfl
-      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
-          List.append_nil]; rfl
-    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
-      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
-      rw [classification_defeq validNames line0 result sigs hEmpty']
-      simp only [innerCharacterization]
-      rw [scanDoc]
-      simp only [if_neg hne]
-      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
-      | none =>
-        simp only [hm]
-        cases result with
-        | none => simpa [innerCharacterization] using ih none sigs
-        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-      | some m =>
-        by_cases hc : validNames.contains m.base
-        · cases result with
-          | none =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
-                Option.isNone_none]
-              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
-              simp only [innerCharacterization] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
-                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
-              rfl
-          | some r0 =>
-            by_cases hmul : line0.endsWith "\\"
-            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
-              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
-              simp only [innerCharacterization] at hih
-              rw [List.append_assoc] at hih
-              simpa using hih
-            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
-              rfl
-        · simp only [hm, hc, Bool.false_eq_true, if_false]
-          cases result with
-          | none => simpa [innerCharacterization] using ih none sigs
-          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
--- @decl:inner_loop_characterization-end
--- @ns:inner_loop_characterization-end
-
--- ==== module: OuterLoop ====
-
--- @ns:outer_result_none_invariant-start
--- @decl:outer_result_none_invariant-start
-/-- A block whose leading run is empty leaves the outer state untouched at
-`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
-guard yields (does not break). -/
-theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
-    (h : scanDoc validNames doclines = []) :
-    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
-  have hchar := inner_loop_characterization validNames doclines none []
-  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
-    List.append_nil] at hchar
-  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
--- @decl:outer_result_none_invariant-end
--- @ns:outer_result_none_invariant-end
-
--- @ns:outer_loop_characterization-start
--- @decl:outer_loop_characterization-start
-/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
-produces the state reproducing `collectSpec validNames docstrings`. -/
-theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
-    outerCharacterization validNames docstrings
-      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
-  induction docstrings with
-  | nil =>
-    simp only [outerCharacterization, collectSpec]
-    rfl
-  | cons doc docs ih =>
-    rw [forIn_step_reduction]
-    have hinner := inner_loop_characterization validNames doc none []
-    simp only [innerCharacterization] at hinner
-    simp only [OuterBody]
-    rw [hinner]
-    simp only [outerCharacterization, collectSpec]
-    cases hsc : scanDoc validNames doc with
-    | nil =>
-      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
-      simpa only [hsc] using ih
-    | cons r rest =>
-      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
-      rfl
--- @decl:outer_loop_characterization-end
--- @ns:outer_loop_characterization-end
-
--- ==== module: Bridge to implementation ====
-
--- @ns:forIn_mprod_eq_prod-start
--- @decl:forIn_mprod_eq_prod-start
-/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
-implementation threads its two mutable variables as an `MProd (Option Sig)
-(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
-over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
-`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
-— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
-This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
-is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
-of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
-`OuterBody`/`InnerBody` (`Prod`) normal form. -/
-theorem forIn_mprod_eq_prod {α β γ : Type}
-    (l : List α) (b0 : β) (c0 : γ)
-    (fp : α → (β × γ) → ForInStep (β × γ)) :
-    (forIn l (⟨b0, c0⟩ : MProd β γ)
-      (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
-      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-  induction l generalizing b0 c0 with
-  | nil => rfl
-  | cons a as ih =>
-    rw [List.forIn_cons, List.forIn_cons]
-    cases h : fp a (b0, c0) with
-    | done s => rfl
-    | yield s => exact ih s.1 s.2
--- @decl:forIn_mprod_eq_prod-end
--- @ns:forIn_mprod_eq_prod-end
-
--- @ns:impl_run_bridge-start
--- @decl:impl_run_bridge-start
-/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
-`break`/`continue`, and an outer `if result.isSome then break`) to the pure
-`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
-join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
-ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
-and read the final `match result with | none => [] | some r => r :: sigs`. -/
-theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
-    implementation_collectSignatures docstrings validNames
-      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
-            (OuterBody validNames)) : Id LoopState) with
-         | (none, _) => []
-         | (some r, sigs) => r :: sigs) := by
-  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
-      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
-      (fp : α → (β × γ) → ForInStep (β × γ)),
-      (∀ a r, g a r = (match fp a (r.1, r.2) with
-                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
-      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
-        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
-    intro α β γ l b0 c0 g fp h
-    have hg : g = (fun a (r : MProd β γ) =>
-        (match fp a (r.1, r.2) with
-         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
-         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
-      funext a r; exact h a r
-    rw [hg]
-    exact forIn_mprod_eq_prod l b0 c0 fp
-  unfold implementation_collectSignatures
-  simp only [Id.run, bind, pure]
-  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
-  case hbody =>
-    intro doclines r
-    unfold OuterBody
-    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
-    case hinner =>
-      intro line0 s
-      unfold InnerBody
-      by_cases h1 : line0.isEmpty = true
-      · simp only [h1, if_true]
-      · simp only [h1, Bool.false_eq_true, if_false]
-        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
-        | none => rfl
-        | some m =>
-          by_cases hc : validNames.contains m.base = true
-          · simp only [hc, if_true]
-            by_cases hn : s.1.isNone = true
-            · simp only [hn, if_true]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-            · simp only [hn, Bool.false_eq_true, if_false]
-              by_cases he : line0.endsWith "\\" = true <;>
-                simp only [he, Bool.false_eq_true, if_true, if_false]
-          · simp only [hc, Bool.false_eq_true, if_false]
-    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
-    obtain ⟨pa, pb⟩ := p
-    by_cases hs : pa.isSome = true
-    · simp only [hs, if_true]
-    · simp only [hs, Bool.false_eq_true, if_false]
-  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
-    cases a <;> rfl
--- @decl:impl_run_bridge-end
--- @ns:impl_run_bridge-end
-
 
 theorem correct_collectSignatures :
     ∀ (docstrings : List (List String)) (validNames : List String),
@@ -500,14 +161,6 @@
         (implementation_collectSignatures docstrings validNames) := by
   intro docstrings validNames
   show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
-  rw [impl_run_bridge]
-  have h := outer_loop_characterization validNames docstrings
-  simp only [outerCharacterization] at h
-  cases hc : collectSpec validNames docstrings with
-  | nil =>
-    rw [hc] at h
-    rw [h]
-  | cons r rest =>
-    rw [hc] at h
-    rw [h]
+  simp [implementation_collectSignatures, collectSpec, scanDoc, stripContinuation, Id.run]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reading object signatures from the leading text of a documentation comment.

A documentation comment is a list of *blocks*, and each block is a list of text
lines. A line is recognised as a signature line by a given extended-signature
matcher; a recognised line yields a *thing name*, an argument string and an
optional return annotation. A recognised line is accepted only when its thing
name is one of the object's candidate names.

The desired behavior collects **every** signature offered at the start of a
block, in order, rather than only the first one. Within a block the lines are
read top to bottom and stop at the first empty line. A signature line that ends
in a backslash is a *continuation*: another signature follows it on the next
line (the trailing backslash and trailing whitespace are dropped before
matching), so reading proceeds to the next line. A signature line that does NOT
end in a backslash is the last one of the run, so reading of that block stops
there.
Lines that are not recognised, or whose thing name is not a candidate, are
skipped without stopping. Across the list of blocks, the first block that yields
at least one signature provides the whole result (the first such signature is
the primary one and the rest follow it, all in order); later blocks are then
ignored. If no block yields a signature the result is empty.
-/

-- axioms-start
/-- The outcome of matching one line against the extended-signature matcher: the
thing name, the argument string, and the (possibly empty) return annotation. -/
structure SigMatch where
  base : String
  args : String
  retann : String
deriving DecidableEq, Repr

/-- One collected signature: an argument string and a (possibly empty) return
annotation. -/
structure Sig where
  args : String
  retann : String
deriving DecidableEq, Repr

/-- The given extended-signature matcher applied to a single line. It returns
`none` when the line is not a signature line, otherwise the parsed thing name /
arguments / return annotation. This matcher is UNCHANGED by the modeled behavior
and is invoked identically wherever a line must be classified; the modeled
behavior consumes no property of it beyond "it is a deterministic function of
the line". The proof agent may add a `_prop` axiom only if a proof obligation
later needs one. -/
opaque matchSig : String → Option SigMatch
-- axioms-end

-- pure-start
/-- The whitespace codepoints Python's `str.rstrip()` (with no argument)
removes — exactly the characters `str.isspace()` accepts: tab, LF, VT, FF, CR,
FS/GS/RS/US, space, NEL, NBSP, Ogham space mark, the Unicode space separators
U+2000–U+200A, LS, PS, NNBSP, MMSP, and ideographic space. Note this is WIDER
than Lean's `Char.isWhitespace` (which is only space/tab/CR/LF). -/
def pyWhitespaceCodes : List UInt32 :=
  [0x9, 0xA, 0xB, 0xC, 0xD, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x85, 0xA0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000]

/-- `str.isspace()` / the character class `str.rstrip()` strips. -/
def isPyWhitespace (c : Char) : Bool :=
  pyWhitespaceCodes.contains c.val

/-- Drop a continuation marker from the end of a line: remove trailing
backslashes, then any trailing whitespace exposed underneath them
(`line.rstrip('\\').rstrip()` — Python's whitespace set). -/
def stripContinuation (s : String) : String :=
  String.mk
    (((s.toList.reverse.dropWhile (· = '\\')).dropWhile isPyWhitespace).reverse)

/-- Read the leading signature run of a single block.

The lines are walked front to back. An empty line ends the run. A line ending in
a backslash is a continuation (matched against its stripped form, then reading
proceeds); any other line is the last candidate of the run. A line that the
matcher rejects, or whose thing name is not among `validNames`, is skipped. The
accepted signatures are returned in order. -/
def scanDoc (validNames : List String) : List String → List Sig
  | [] => []
  | line0 :: rest =>
    if line0 = "" then []
    else
      let multiline := line0.endsWith "\\"
      let line := if multiline then stripContinuation line0 else line0
      match matchSig line with
      | none => scanDoc validNames rest
      | some m =>
        if validNames.contains m.base then
          let s : Sig := ⟨m.args, m.retann⟩
          if multiline then s :: scanDoc validNames rest else [s]
        else
          scanDoc validNames rest

/-- The collected signatures: the first block whose leading run is non-empty
supplies the entire result; otherwise the result is empty. -/
def collectSpec (validNames : List String) : List (List String) → List Sig
  | [] => []
  | doc :: docs =>
    let sigs := scanDoc validNames doc
    if sigs = [] then collectSpec validNames docs else sigs
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered list of signatures collected from the
documentation comment. This pins every component: the result's length, the order
of the signatures, and each signature's argument string and return annotation
are all determined by the input blocks and the candidate names. A correct result
must come from the first block that offers any signature, must include every
signature of that block's leading run (continuations included), and must stop at
the first non-continuation signature line; no signature may be dropped, added,
reordered, or sourced from a later block. -/
def problem_spec_collectSignatures
    (docstrings : List (List String)) (validNames : List String)
    (result : List Sig) : Prop :=
  result = collectSpec validNames docstrings
-- post-conditions-end

-- impl-start
/-- Collect every signature offered at the start of a documentation comment.
The blocks are scanned in order; within a block the lines are read top to bottom
until an empty line, the first signature is kept as the primary one and any
further continuation signatures are appended, and the scan of a block stops at
its first non-continuation signature line. The first block that yields a
signature provides the result. -/
def implementation_collectSignatures
    (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
  let mut result : Option Sig := none
  let mut signatures : List Sig := []
  for doclines in docstrings do
    for line0 in doclines do
      if line0.isEmpty then
        break
      let multiline := line0.endsWith "\\"
      let line := if multiline then stripContinuation line0 else line0
      match matchSig line with
      | none => continue
      | some m =>
        if validNames.contains m.base then
          if result.isNone then
            result := some ⟨m.args, m.retann⟩
          else
            signatures := signatures ++ [⟨m.args, m.retann⟩]
          if multiline then
            continue
          else
            break
        else
          continue
    if result.isSome then
      break
  match result with
  | none => return []
  | some r => return r :: signatures
-- impl-end

-- proof-start
-- ==== module: defs ====

-- @decl:LoopState-start
/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
loops as their `ForInStep` state: `result` holds the primary (first-accepted)
signature once found, `signatures` accumulates the continuation signatures. -/
abbrev LoopState : Type := Option Sig × List Sig
-- @decl:LoopState-end

-- @decl:InnerBody-start
/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
`continue` ↦ `ForInStep.yield`. -/
def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
    ForInStep LoopState :=
  if line0.isEmpty then
    ForInStep.done st
  else
    let multiline := line0.endsWith "\\"
    let line := if multiline then stripContinuation line0 else line0
    match matchSig line with
    | none => ForInStep.yield st
    | some m =>
      if validNames.contains m.base then
        if st.1.isNone then
          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
        else
          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
      else
        ForInStep.yield st
-- @decl:InnerBody-end

-- @decl:OuterBody-start
/-- The desugared body of the outer `for doclines in docstrings` loop: run the
inner loop on the block, then `if result.isSome then break`. -/
def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
    ForInStep LoopState :=
  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
-- @decl:OuterBody-end

-- @decl:innerCharacterization-start
/-- Relation between the inner loop's entry state `entry` and exit state `exit`
over `block`: the leading run collected by `scanDoc` is distributed — its head
fills an empty `result`, its tail is appended to `signatures`; when `result` is
already set, the whole run is appended to `signatures`. -/
def innerCharacterization (validNames : List String) (block : List String)
    (entry exit : LoopState) : Prop :=
  match entry.1 with
  | none =>
    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
  | some r0 =>
    exit = (some r0, entry.2 ++ scanDoc validNames block)
-- @decl:innerCharacterization-end

-- @decl:outerCharacterization-start
/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
the exit state reproduces `collectSpec validNames docstrings` split into its
head (the primary `result`) and tail (the continuation `signatures`). -/
def outerCharacterization (validNames : List String) (docstrings : List (List String))
    (exit : LoopState) : Prop :=
  match collectSpec validNames docstrings with
  | [] => exit = (none, [])
  | r :: rest => exit = (some r, rest)
-- @decl:outerCharacterization-end

-- ==== module: Bridges ====

-- @ns:isEmpty_bridge-start
-- @decl:isEmpty_bridge-start
/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
theorem isEmpty_bridge (line0 : String) :
    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
  refine ⟨String.isEmpty_iff line0, ?_⟩
  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
-- @decl:isEmpty_bridge-end
-- @ns:isEmpty_bridge-end

-- @ns:forIn_step_reduction-start
-- @decl:forIn_step_reduction-start
/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
mapping `ForInStep.done`/`yield` to stop/recurse. -/
theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
    (body : α → β → Id (ForInStep β)) :
    (forIn (a :: as) b body : Id β)
      = (match (body a b : Id (ForInStep β)) with
         | ForInStep.done b' => (pure b' : Id β)
         | ForInStep.yield b' => forIn as b' body) := by
  simp only [List.forIn_cons, bind, pure]
  cases body a b <;> rfl
-- @decl:forIn_step_reduction-end
-- @ns:forIn_step_reduction-end

-- @ns:classification_defeq-start
-- @decl:classification_defeq-start
/-- On a non-empty line, `InnerBody` reduces to the same classification
sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
theorem classification_defeq (validNames : List String) (line0 : String)
    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
    InnerBody validNames line0 (result, sigs)
      = (let multiline := line0.endsWith "\\"
         let line := if multiline then stripContinuation line0 else line0
         match matchSig line with
         | none => ForInStep.yield (result, sigs)
         | some m =>
           if validNames.contains m.base then
             if result.isNone then
               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
             else
               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
           else ForInStep.yield (result, sigs)) := by
  simp only [InnerBody, h, Bool.false_eq_true, if_false]
-- @decl:classification_defeq-end
-- @ns:classification_defeq-end

-- ==== module: InnerLoop ====

-- @ns:inner_loop_characterization-start
-- @decl:inner_loop_characterization-start
/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
doclines` across the threaded `(result, signatures)` state. -/
theorem inner_loop_characterization (validNames : List String) (doclines : List String)
    (result : Option Sig) (sigs : List Sig) :
    innerCharacterization validNames doclines (result, sigs)
      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
  induction doclines generalizing result sigs with
  | nil =>
    cases result with
    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
        List.append_nil, forIn, List.forIn_nil]; rfl
    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
        List.forIn_nil]; rfl
  | cons line0 rest ih =>
    rw [forIn_step_reduction]
    by_cases hEmpty : line0.isEmpty = true
    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
        simp [InnerBody, hEmpty]
      rw [hb]
      cases result with
      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
          List.tail_nil, List.append_nil]; rfl
      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
          List.append_nil]; rfl
    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
      rw [classification_defeq validNames line0 result sigs hEmpty']
      simp only [innerCharacterization]
      rw [scanDoc]
      simp only [if_neg hne]
      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
      | none =>
        simp only [hm]
        cases result with
        | none => simpa [innerCharacterization] using ih none sigs
        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
      | some m =>
        by_cases hc : validNames.contains m.base
        · cases result with
          | none =>
            by_cases hmul : line0.endsWith "\\"
            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
                Option.isNone_none]
              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
              simp only [innerCharacterization] at hih
              simpa using hih
            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
              rfl
          | some r0 =>
            by_cases hmul : line0.endsWith "\\"
            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
              simp only [innerCharacterization] at hih
              rw [List.append_assoc] at hih
              simpa using hih
            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
              rfl
        · simp only [hm, hc, Bool.false_eq_true, if_false]
          cases result with
          | none => simpa [innerCharacterization] using ih none sigs
          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-- @decl:inner_loop_characterization-end
-- @ns:inner_loop_characterization-end

-- ==== module: OuterLoop ====

-- @ns:outer_result_none_invariant-start
-- @decl:outer_result_none_invariant-start
/-- A block whose leading run is empty leaves the outer state untouched at
`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
guard yields (does not break). -/
theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
    (h : scanDoc validNames doclines = []) :
    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
  have hchar := inner_loop_characterization validNames doclines none []
  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
    List.append_nil] at hchar
  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
-- @decl:outer_result_none_invariant-end
-- @ns:outer_result_none_invariant-end

-- @ns:outer_loop_characterization-start
-- @decl:outer_loop_characterization-start
/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
produces the state reproducing `collectSpec validNames docstrings`. -/
theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
    outerCharacterization validNames docstrings
      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
  induction docstrings with
  | nil =>
    simp only [outerCharacterization, collectSpec]
    rfl
  | cons doc docs ih =>
    rw [forIn_step_reduction]
    have hinner := inner_loop_characterization validNames doc none []
    simp only [innerCharacterization] at hinner
    simp only [OuterBody]
    rw [hinner]
    simp only [outerCharacterization, collectSpec]
    cases hsc : scanDoc validNames doc with
    | nil =>
      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
      simpa only [hsc] using ih
    | cons r rest =>
      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
      rfl
-- @decl:outer_loop_characterization-end
-- @ns:outer_loop_characterization-end

-- ==== module: Bridge to implementation ====

-- @ns:forIn_mprod_eq_prod-start
-- @decl:forIn_mprod_eq_prod-start
/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
implementation threads its two mutable variables as an `MProd (Option Sig)
(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
`OuterBody`/`InnerBody` (`Prod`) normal form. -/
theorem forIn_mprod_eq_prod {α β γ : Type}
    (l : List α) (b0 : β) (c0 : γ)
    (fp : α → (β × γ) → ForInStep (β × γ)) :
    (forIn l (⟨b0, c0⟩ : MProd β γ)
      (fun a (r : MProd β γ) =>
        (match fp a (r.1, r.2) with
         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
  induction l generalizing b0 c0 with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.forIn_cons]
    cases h : fp a (b0, c0) with
    | done s => rfl
    | yield s => exact ih s.1 s.2
-- @decl:forIn_mprod_eq_prod-end
-- @ns:forIn_mprod_eq_prod-end

-- @ns:impl_run_bridge-start
-- @decl:impl_run_bridge-start
/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
`break`/`continue`, and an outer `if result.isSome then break`) to the pure
`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
and read the final `match result with | none => [] | some r => r :: sigs`. -/
theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
    implementation_collectSignatures docstrings validNames
      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
            (OuterBody validNames)) : Id LoopState) with
         | (none, _) => []
         | (some r, sigs) => r :: sigs) := by
  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
      (fp : α → (β × γ) → ForInStep (β × γ)),
      (∀ a r, g a r = (match fp a (r.1, r.2) with
                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
    intro α β γ l b0 c0 g fp h
    have hg : g = (fun a (r : MProd β γ) =>
        (match fp a (r.1, r.2) with
         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
      funext a r; exact h a r
    rw [hg]
    exact forIn_mprod_eq_prod l b0 c0 fp
  unfold implementation_collectSignatures
  simp only [Id.run, bind, pure]
  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
  case hbody =>
    intro doclines r
    unfold OuterBody
    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
    case hinner =>
      intro line0 s
      unfold InnerBody
      by_cases h1 : line0.isEmpty = true
      · simp only [h1, if_true]
      · simp only [h1, Bool.false_eq_true, if_false]
        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
        | none => rfl
        | some m =>
          by_cases hc : validNames.contains m.base = true
          · simp only [hc, if_true]
            by_cases hn : s.1.isNone = true
            · simp only [hn, if_true]
              by_cases he : line0.endsWith "\\" = true <;>
                simp only [he, Bool.false_eq_true, if_true, if_false]
            · simp only [hn, Bool.false_eq_true, if_false]
              by_cases he : line0.endsWith "\\" = true <;>
                simp only [he, Bool.false_eq_true, if_true, if_false]
          · simp only [hc, Bool.false_eq_true, if_false]
    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
    obtain ⟨pa, pb⟩ := p
    by_cases hs : pa.isSome = true
    · simp only [hs, if_true]
    · simp only [hs, Bool.false_eq_true, if_false]
  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
    cases a <;> rfl
-- @decl:impl_run_bridge-end
-- @ns:impl_run_bridge-end

theorem correct_collectSignatures :
    ∀ (docstrings : List (List String)) (validNames : List String),
      problem_spec_collectSignatures docstrings validNames
        (implementation_collectSignatures docstrings validNames) := by
  intro docstrings validNames
  show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
  rw [impl_run_bridge]
  have h := outer_loop_characterization validNames docstrings
  simp only [outerCharacterization] at h
  cases hc : collectSpec validNames docstrings with
  | nil =>
    rw [hc] at h
    rw [h]
  | cons r rest =>
    rw [hc] at h
    rw [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: full functional-equality post-condition — problem_spec_collectSignatures docstrings validNames result := (result = collectSpec validNames docstrings). Any impl whose correct_collectSignatures closes is PROVABLY EQUAL to collectSpec on all inputs, so genuinely-wrong impls cannot verify. This is the maximally-strong spec class; the only verify-admitted alternative is a re-expression of collectSpec itself (the 'echo').

SAME-SPEC: all 8 attack files + positive control return swebench_unified.markers.same_spec == True against the bundle Solution.lean (LeanBackend.language). The spec/axioms/pure/post regions are byte-identical; only impl+proof differ. (First reconstruction attempt omitted the -- proof-start/-- proof-end markers and read False; fixed and re-confirmed True for all.)

COMMANDS: same_spec via python -c 'from swebench_unified.markers import same_spec; ...'. Verify via `bash scripts/lean_verify.sh <file>` from repo root. Axioms via appending `#print axioms correct_collectSignatures` and re-running lean_verify. Resolve via python -c 'from swebench_unified.harness import run_resolve; run_resolve("sphinx-doc__sphinx-7748", patch)'.

### ATTACK RESULTS (7 wrong impls, all DISTINCT failure classes):
- atk1_dropcont (control-flow-effect: returns only primary [r], drops continuation signatures): verify EXIT=1, error 'Tactic `rfl` failed' at :165. Correctly REJECTED.
- atk2_reverse (boundary/order: r :: signatures.reverse): verify EXIT=1, rfl failed :165. REJECTED.
- atk3_allblocks (control-flow: removed outer `if result.isSome then break`, accumulates across all blocks): verify EXIT=1, rfl failed :163. REJECTED.
- atk4_alwaysbreak (control-flow: ignores multiline flag, always breaks after first accepted sig → collapses continuation runs): verify EXIT=1, rfl failed :163. REJECTED.
- atk5_nostrip (modeling boundary: matches raw line0 instead of stripContinuation line0 on multiline): verify EXIT=1, rfl failed :166. REJECTED.
- atk6_noemptybreak (control-flow: empty line `continue` instead of `break`, so run does not terminate at blank line): verify EXIT=1, rfl failed :166. REJECTED.
- atk7_swapfields (value: builds Sig ⟨retann,args⟩ swapping the two fields): verify EXIT=1, rfl failed :165. REJECTED.
Each failure is a genuine elaboration error (equality to collectSpec is literally false), not a timeout (all completed well under the 300s cap) and not sorry.

- atk_echo (ungrounded-oracle echo: impl := collectSpec validNames docstrings, proof by rfl): verify EXIT=0 (VERIFIES). `#print axioms correct_collectSignatures` => depends on axioms: [propext] — CLEAN (subset of {propext, Classical.choice, Quot.sound}; no sorryAx, no custom axiom). Per mandatory protocol its faithful refined patch was materialized. Because the echo reproduces EXACTLY the modeled post-patch behavior (collectSpec is the deep model of _find_signature+format_signature), its faithful patch IS the gold patch. run_resolve('sphinx-doc__sphinx-7748', gold) => RESOLVED: True, COMPLETED: True, NOTE 'resolved', ATTEMPTS 1. So the one verifying attack RESOLVES → NOT a counterexample (verify ⇒ correct held here). Under the fixed G-PANEL-1/G-EQ derivation a resolving echo is not a weakness.

POSITIVE CONTROL: pos_control.lean = verbatim bundle Solution.lean → verify EXIT=0.

PREPATCH: Solution_prepatch.lean present; reads only doclines[0], no continuation handling, returns at most [r]; on the F2P backslash-continued two-signature run the spec demands the full ordered list with the first line stripped, so the equality is unprovable and G-DIFF records 'verification failed' — prepatch bug reproduced (prepatch_reproduced=true).

A-LEG / refinement.md AUDIT: single opaque callee matchSig is a genuine A-reference — it appears IDENTICALLY in scanDoc (spec helper) and implementation_collectSignatures (impl); the closing proof chain impl_run_bridge → forIn_mprod_eq_prod → inner/outer_loop_characterization → structural equality to collectSpec consumes NO property of matchSig (it is universally quantified and threaded opaquely), so it cancels. G-AX skip is correct; there is no consumed axiom and no deep-model reference requiring G-AX validation. All refinement.md legs are R / A-reference / I — no kind-3 (ungrounded-oracle) leg. stripContinuation faithfully models line.rstrip('\\').rstrip() over the exact Python str.isspace() codepoint set (verified in prior G-PANEL-2 pass; the modeling boundary my atk5 probes is exactly this and the spec CORRECTLY rejects impls that skip the strip).

CONCLUSION: 8 attacks run (7 wrong impls all rejected by verification; 1 echo verifies with clean axioms and its faithful=gold patch RESOLVES). No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify ⇒ correct upheld on every executed case. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_dropcont.lean`, `atk2_reverse.lean`, `atk3_allblocks.lean`, `atk4_alwaysbreak.lean`, `atk5_nostrip.lean`, `atk6_noemptybreak.lean`, `atk7_swapfields.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk1_dropcont.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk2_reverse.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk3_allblocks.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk4_alwaysbreak.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk5_nostrip.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk6_noemptybreak.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk7_swapfields.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reading object signatures from the leading text of a documentation comment.

A documentation comment is a list of *blocks*, and each block is a list of text
lines. A line is recognised as a signature line by a given extended-signature
matcher; a recognised line yields a *thing name*, an argument string and an
optional return annotation. A recognised line is accepted only when its thing
name is one of the object's candidate names.

The desired behavior collects **every** signature offered at the start of a
block, in order, rather than only the first one. Within a block the lines are
read top to bottom and stop at the first empty line. A signature line that ends
in a backslash is a *continuation*: another signature follows it on the next
line (the trailing backslash and trailing whitespace are dropped before
matching), so reading proceeds to the next line. A signature line that does NOT
end in a backslash is the last one of the run, so reading of that block stops
there.
Lines that are not recognised, or whose thing name is not a candidate, are
skipped without stopping. Across the list of blocks, the first block that yields
at least one signature provides the whole result (the first such signature is
the primary one and the rest follow it, all in order); later blocks are then
ignored. If no block yields a signature the result is empty.
-/

-- axioms-start
/-- The outcome of matching one line against the extended-signature matcher: the
thing name, the argument string, and the (possibly empty) return annotation. -/
structure SigMatch where
  base : String
  args : String
  retann : String
deriving DecidableEq, Repr

/-- One collected signature: an argument string and a (possibly empty) return
annotation. -/
structure Sig where
  args : String
  retann : String
deriving DecidableEq, Repr

/-- The given extended-signature matcher applied to a single line. It returns
`none` when the line is not a signature line, otherwise the parsed thing name /
arguments / return annotation. This matcher is UNCHANGED by the modeled behavior
and is invoked identically wherever a line must be classified; the modeled
behavior consumes no property of it beyond "it is a deterministic function of
the line". The proof agent may add a `_prop` axiom only if a proof obligation
later needs one. -/
opaque matchSig : String → Option SigMatch
-- axioms-end

-- pure-start
/-- The whitespace codepoints Python's `str.rstrip()` (with no argument)
removes — exactly the characters `str.isspace()` accepts: tab, LF, VT, FF, CR,
FS/GS/RS/US, space, NEL, NBSP, Ogham space mark, the Unicode space separators
U+2000–U+200A, LS, PS, NNBSP, MMSP, and ideographic space. Note this is WIDER
than Lean's `Char.isWhitespace` (which is only space/tab/CR/LF). -/
def pyWhitespaceCodes : List UInt32 :=
  [0x9, 0xA, 0xB, 0xC, 0xD, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x85, 0xA0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000]

/-- `str.isspace()` / the character class `str.rstrip()` strips. -/
def isPyWhitespace (c : Char) : Bool :=
  pyWhitespaceCodes.contains c.val

/-- Drop a continuation marker from the end of a line: remove trailing
backslashes, then any trailing whitespace exposed underneath them
(`line.rstrip('\\').rstrip()` — Python's whitespace set). -/
def stripContinuation (s : String) : String :=
  String.mk
    (((s.toList.reverse.dropWhile (· = '\\')).dropWhile isPyWhitespace).reverse)

/-- Read the leading signature run of a single block.

The lines are walked front to back. An empty line ends the run. A line ending in
a backslash is a continuation (matched against its stripped form, then reading
proceeds); any other line is the last candidate of the run. A line that the
matcher rejects, or whose thing name is not among `validNames`, is skipped. The
accepted signatures are returned in order. -/
def scanDoc (validNames : List String) : List String → List Sig
  | [] => []
  | line0 :: rest =>
    if line0 = "" then []
    else
      let multiline := line0.endsWith "\\"
      let line := if multiline then stripContinuation line0 else line0
      match matchSig line with
      | none => scanDoc validNames rest
      | some m =>
        if validNames.contains m.base then
          let s : Sig := ⟨m.args, m.retann⟩
          if multiline then s :: scanDoc validNames rest else [s]
        else
          scanDoc validNames rest

/-- The collected signatures: the first block whose leading run is non-empty
supplies the entire result; otherwise the result is empty. -/
def collectSpec (validNames : List String) : List (List String) → List Sig
  | [] => []
  | doc :: docs =>
    let sigs := scanDoc validNames doc
    if sigs = [] then collectSpec validNames docs else sigs
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered list of signatures collected from the
documentation comment. This pins every component: the result's length, the order
of the signatures, and each signature's argument string and return annotation
are all determined by the input blocks and the candidate names. A correct result
must come from the first block that offers any signature, must include every
signature of that block's leading run (continuations included), and must stop at
the first non-continuation signature line; no signature may be dropped, added,
reordered, or sourced from a later block. -/
def problem_spec_collectSignatures
    (docstrings : List (List String)) (validNames : List String)
    (result : List Sig) : Prop :=
  result = collectSpec validNames docstrings
-- post-conditions-end

-- impl-start
/-- Collect every signature offered at the start of a documentation comment.
The blocks are scanned in order; within a block the lines are read top to bottom
until an empty line, the first signature is kept as the primary one and any
further continuation signatures are appended, and the scan of a block stops at
its first non-continuation signature line. The first block that yields a
signature provides the result. -/
def implementation_collectSignatures
    (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
  let mut result : Option Sig := none
  let mut signatures : List Sig := []
  for doclines in docstrings do
    for line0 in doclines do
      if line0.isEmpty then
        break
      let multiline := line0.endsWith "\\"
      let line := if multiline then stripContinuation line0 else line0
      match matchSig line with
      | none => continue
      | some m =>
        if validNames.contains m.base then
          if result.isNone then
            result := some ⟨m.args, m.retann⟩
          else
            signatures := signatures ++ [⟨m.args, m.retann⟩]
          if multiline then
            continue
          else
            break
        else
          continue
    if result.isSome then
      break
  match result with
  | none => return []
  | some r => return r :: signatures
-- impl-end

-- proof-start
-- ==== module: defs ====

-- @decl:LoopState-start
/-- The pair `(result, signatures)` threaded by the desugared nested `forIn`
loops as their `ForInStep` state: `result` holds the primary (first-accepted)
signature once found, `signatures` accumulates the continuation signatures. -/
abbrev LoopState : Type := Option Sig × List Sig
-- @decl:LoopState-end

-- @decl:InnerBody-start
/-- The desugared body of the inner `for line0 in doclines` loop, acting on the
threaded state `(result, signatures)`.  `break` ↦ `ForInStep.done`,
`continue` ↦ `ForInStep.yield`. -/
def InnerBody (validNames : List String) (line0 : String) (st : LoopState) :
    ForInStep LoopState :=
  if line0.isEmpty then
    ForInStep.done st
  else
    let multiline := line0.endsWith "\\"
    let line := if multiline then stripContinuation line0 else line0
    match matchSig line with
    | none => ForInStep.yield st
    | some m =>
      if validNames.contains m.base then
        if st.1.isNone then
          if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, st.2)
          else ForInStep.done (some ⟨m.args, m.retann⟩, st.2)
        else
          if multiline then ForInStep.yield (st.1, st.2 ++ [⟨m.args, m.retann⟩])
          else ForInStep.done (st.1, st.2 ++ [⟨m.args, m.retann⟩])
      else
        ForInStep.yield st
-- @decl:InnerBody-end

-- @decl:OuterBody-start
/-- The desugared body of the outer `for doclines in docstrings` loop: run the
inner loop on the block, then `if result.isSome then break`. -/
def OuterBody (validNames : List String) (doclines : List String) (st : LoopState) :
    ForInStep LoopState :=
  let st' : LoopState := (forIn doclines st (InnerBody validNames) : Id LoopState)
  if st'.1.isSome then ForInStep.done st' else ForInStep.yield st'
-- @decl:OuterBody-end

-- @decl:innerCharacterization-start
/-- Relation between the inner loop's entry state `entry` and exit state `exit`
over `block`: the leading run collected by `scanDoc` is distributed — its head
fills an empty `result`, its tail is appended to `signatures`; when `result` is
already set, the whole run is appended to `signatures`. -/
def innerCharacterization (validNames : List String) (block : List String)
    (entry exit : LoopState) : Prop :=
  match entry.1 with
  | none =>
    exit = ((scanDoc validNames block).head?, entry.2 ++ (scanDoc validNames block).tail)
  | some r0 =>
    exit = (some r0, entry.2 ++ scanDoc validNames block)
-- @decl:innerCharacterization-end

-- @decl:outerCharacterization-start
/-- Relation between the outer loop's entry `(none, [])` and exit `exit`:
the exit state reproduces `collectSpec validNames docstrings` split into its
head (the primary `result`) and tail (the continuation `signatures`). -/
def outerCharacterization (validNames : List String) (docstrings : List (List String))
    (exit : LoopState) : Prop :=
  match collectSpec validNames docstrings with
  | [] => exit = (none, [])
  | r :: rest => exit = (some r, rest)
-- @decl:outerCharacterization-end

-- ==== module: Bridges ====

-- @ns:isEmpty_bridge-start
-- @decl:isEmpty_bridge-start
/-- Reconcile impl's `line0.isEmpty` guard with `scanDoc`'s `line0 = ""` test. -/
theorem isEmpty_bridge (line0 : String) :
    (line0.isEmpty = true ↔ line0 = "") ∧ (line0.isEmpty = false ↔ line0 ≠ "") := by
  refine ⟨String.isEmpty_iff line0, ?_⟩
  rw [ne_eq, ← String.isEmpty_iff line0, Bool.not_eq_true]
-- @decl:isEmpty_bridge-end
-- @ns:isEmpty_bridge-end

-- @ns:forIn_step_reduction-start
-- @decl:forIn_step_reduction-start
/-- One-step reduction of a `List` `forIn` in the `Id` monad: unfold the head,
mapping `ForInStep.done`/`yield` to stop/recurse. -/
theorem forIn_step_reduction {α β : Type} (a : α) (as : List α) (b : β)
    (body : α → β → Id (ForInStep β)) :
    (forIn (a :: as) b body : Id β)
      = (match (body a b : Id (ForInStep β)) with
         | ForInStep.done b' => (pure b' : Id β)
         | ForInStep.yield b' => forIn as b' body) := by
  simp only [List.forIn_cons, bind, pure]
  cases body a b <;> rfl
-- @decl:forIn_step_reduction-end
-- @ns:forIn_step_reduction-end

-- @ns:classification_defeq-start
-- @decl:classification_defeq-start
/-- On a non-empty line, `InnerBody` reduces to the same classification
sub-expression `scanDoc` uses (`matchSig line`, `validNames.contains m.base`),
with `line` computed via `endsWith "\\"` / `stripContinuation`. -/
theorem classification_defeq (validNames : List String) (line0 : String)
    (result : Option Sig) (sigs : List Sig) (h : line0.isEmpty = false) :
    InnerBody validNames line0 (result, sigs)
      = (let multiline := line0.endsWith "\\"
         let line := if multiline then stripContinuation line0 else line0
         match matchSig line with
         | none => ForInStep.yield (result, sigs)
         | some m =>
           if validNames.contains m.base then
             if result.isNone then
               if multiline then ForInStep.yield (some ⟨m.args, m.retann⟩, sigs)
               else ForInStep.done (some ⟨m.args, m.retann⟩, sigs)
             else
               if multiline then ForInStep.yield (result, sigs ++ [⟨m.args, m.retann⟩])
               else ForInStep.done (result, sigs ++ [⟨m.args, m.retann⟩])
           else ForInStep.yield (result, sigs)) := by
  simp only [InnerBody, h, Bool.false_eq_true, if_false]
-- @decl:classification_defeq-end
-- @ns:classification_defeq-end

-- ==== module: InnerLoop ====

-- @ns:inner_loop_characterization-start
-- @decl:inner_loop_characterization-start
/-- The inner `for line0 in doclines` loop distributes `scanDoc validNames
doclines` across the threaded `(result, signatures)` state. -/
theorem inner_loop_characterization (validNames : List String) (doclines : List String)
    (result : Option Sig) (sigs : List Sig) :
    innerCharacterization validNames doclines (result, sigs)
      ((forIn doclines (result, sigs) (InnerBody validNames)) : Id LoopState) := by
  induction doclines generalizing result sigs with
  | nil =>
    cases result with
    | none => simp only [innerCharacterization, scanDoc, List.head?_nil, List.tail_nil,
        List.append_nil, forIn, List.forIn_nil]; rfl
    | some r0 => simp only [innerCharacterization, scanDoc, List.append_nil, forIn,
        List.forIn_nil]; rfl
  | cons line0 rest ih =>
    rw [forIn_step_reduction]
    by_cases hEmpty : line0.isEmpty = true
    · have hline0 : line0 = "" := (isEmpty_bridge line0).1.mp hEmpty
      have hb : InnerBody validNames line0 (result, sigs) = ForInStep.done (result, sigs) := by
        simp [InnerBody, hEmpty]
      rw [hb]
      cases result with
      | none => simp only [innerCharacterization, scanDoc, hline0, if_pos, List.head?_nil,
          List.tail_nil, List.append_nil]; rfl
      | some r0 => simp only [innerCharacterization, scanDoc, hline0, if_pos,
          List.append_nil]; rfl
    · have hEmpty' : line0.isEmpty = false := by simpa using hEmpty
      have hne : line0 ≠ "" := (isEmpty_bridge line0).2.mp hEmpty'
      rw [classification_defeq validNames line0 result sigs hEmpty']
      simp only [innerCharacterization]
      rw [scanDoc]
      simp only [if_neg hne]
      cases hm : matchSig (if line0.endsWith "\\" then stripContinuation line0 else line0) with
      | none =>
        simp only [hm]
        cases result with
        | none => simpa [innerCharacterization] using ih none sigs
        | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
      | some m =>
        by_cases hc : validNames.contains m.base
        · cases result with
          | none =>
            by_cases hmul : line0.endsWith "\\"
            · simp only [hm, hc, hmul, if_true, List.head?_cons, List.tail_cons,
                Option.isNone_none]
              have hih := ih (some (⟨m.args, m.retann⟩ : Sig)) sigs
              simp only [innerCharacterization] at hih
              simpa using hih
            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, List.head?_cons,
                List.tail_cons, List.append_nil, Option.isNone_none, if_true]
              rfl
          | some r0 =>
            by_cases hmul : line0.endsWith "\\"
            · simp only [hm, hc, hmul, if_true, Option.isNone_some]
              have hih := ih (some r0) (sigs ++ [⟨m.args, m.retann⟩])
              simp only [innerCharacterization] at hih
              rw [List.append_assoc] at hih
              simpa using hih
            · simp only [hm, hc, hmul, Bool.false_eq_true, if_false, Option.isNone_some, if_true]
              rfl
        · simp only [hm, hc, Bool.false_eq_true, if_false]
          cases result with
          | none => simpa [innerCharacterization] using ih none sigs
          | some r0 => simpa [innerCharacterization] using ih (some r0) sigs
-- @decl:inner_loop_characterization-end
-- @ns:inner_loop_characterization-end

-- ==== module: OuterLoop ====

-- @ns:outer_result_none_invariant-start
-- @decl:outer_result_none_invariant-start
/-- A block whose leading run is empty leaves the outer state untouched at
`(none, [])`: the inner loop returns `(none, [])` and the `if result.isSome`
guard yields (does not break). -/
theorem outer_result_none_invariant (validNames : List String) (doclines : List String)
    (h : scanDoc validNames doclines = []) :
    OuterBody validNames doclines (none, []) = ForInStep.yield ((none : Option Sig), ([] : List Sig)) := by
  have hchar := inner_loop_characterization validNames doclines none []
  simp only [innerCharacterization, h, List.head?_nil, List.tail_nil,
    List.append_nil] at hchar
  simp only [OuterBody, hchar, Option.isSome_none, Bool.false_eq_true, if_false]
-- @decl:outer_result_none_invariant-end
-- @ns:outer_result_none_invariant-end

-- @ns:outer_loop_characterization-start
-- @decl:outer_loop_characterization-start
/-- The outer `for doclines in docstrings` loop, started at `(none, [])`,
produces the state reproducing `collectSpec validNames docstrings`. -/
theorem outer_loop_characterization (validNames : List String) (docstrings : List (List String)) :
    outerCharacterization validNames docstrings
      ((forIn docstrings ((none : Option Sig), ([] : List Sig)) (OuterBody validNames)) : Id LoopState) := by
  induction docstrings with
  | nil =>
    simp only [outerCharacterization, collectSpec]
    rfl
  | cons doc docs ih =>
    rw [forIn_step_reduction]
    have hinner := inner_loop_characterization validNames doc none []
    simp only [innerCharacterization] at hinner
    simp only [OuterBody]
    rw [hinner]
    simp only [outerCharacterization, collectSpec]
    cases hsc : scanDoc validNames doc with
    | nil =>
      simp only [List.head?, List.tail, List.append_nil, Option.isSome]
      simpa only [hsc] using ih
    | cons r rest =>
      simp only [List.head?, List.tail, List.nil_append, Option.isSome, if_true]
      rfl
-- @decl:outer_loop_characterization-end
-- @ns:outer_loop_characterization-end

-- ==== module: Bridge to implementation ====

-- @ns:forIn_mprod_eq_prod-start
-- @decl:forIn_mprod_eq_prod-start
/-- Loop-state representation bridge.  The surface `Id.run do … for … mut r₁ r₂`
implementation threads its two mutable variables as an `MProd (Option Sig)
(List Sig)`, whereas the skeleton's `LoopState`/`InnerBody`/`OuterBody` are stated
over `Prod` (`Option Sig × List Sig`).  These are DIFFERENT loop-state types, so a
`forIn` over the MProd state is not definitionally the `forIn` over the Prod state
— this is exactly why `impl_run_bridge` cannot close by `rfl`/congruence alone.
This lemma is the congruence that converts an `MProd`-threaded `forIn` (whose body
is the `Prod`-body `fp` wrapped through `.1`/`.2`) into the `Prod`-threaded `forIn`
of `fp`, so the bridge can rewrite the impl's nested MProd loops into the pure
`OuterBody`/`InnerBody` (`Prod`) normal form. -/
theorem forIn_mprod_eq_prod {α β γ : Type}
    (l : List α) (b0 : β) (c0 : γ)
    (fp : α → (β × γ) → ForInStep (β × γ)) :
    (forIn l (⟨b0, c0⟩ : MProd β γ)
      (fun a (r : MProd β γ) =>
        (match fp a (r.1, r.2) with
         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) : Id (MProd β γ))
      = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
  induction l generalizing b0 c0 with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons, List.forIn_cons]
    cases h : fp a (b0, c0) with
    | done s => rfl
    | yield s => exact ih s.1 s.2
-- @decl:forIn_mprod_eq_prod-end
-- @ns:forIn_mprod_eq_prod-end

-- @ns:impl_run_bridge-start
-- @decl:impl_run_bridge-start
/-- Bridge the surface `Id.run do` implementation (nested `for` loops with
`break`/`continue`, and an outer `if result.isSome then break`) to the pure
`forIn … (OuterBody …)` normal form.  This is the monad-reduction /
join-point-elimination step: map `break ↦ ForInStep.done`, `continue ↦
ForInStep.yield`, thread the mutable `(result, signatures)` as the loop state,
and read the final `match result with | none => [] | some r => r :: sigs`. -/
theorem impl_run_bridge (docstrings : List (List String)) (validNames : List String) :
    implementation_collectSignatures docstrings validNames
      = (match ((forIn docstrings ((none : Option Sig), ([] : List Sig))
            (OuterBody validNames)) : Id LoopState) with
         | (none, _) => []
         | (some r, sigs) => r :: sigs) := by
  have step : ∀ {α β γ : Type} (l : List α) (b0 : β) (c0 : γ)
      (g : α → MProd β γ → Id (ForInStep (MProd β γ)))
      (fp : α → (β × γ) → ForInStep (β × γ)),
      (∀ a r, g a r = (match fp a (r.1, r.2) with
                        | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
                        | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) →
      (forIn l (⟨b0, c0⟩ : MProd β γ) g : Id (MProd β γ))
        = (let p := (forIn l (b0, c0) fp : Id (β × γ)); ⟨p.1, p.2⟩) := by
    intro α β γ l b0 c0 g fp h
    have hg : g = (fun a (r : MProd β γ) =>
        (match fp a (r.1, r.2) with
         | ForInStep.done s => ForInStep.done ⟨s.1, s.2⟩
         | ForInStep.yield s => ForInStep.yield ⟨s.1, s.2⟩)) := by
      funext a r; exact h a r
    rw [hg]
    exact forIn_mprod_eq_prod l b0 c0 fp
  unfold implementation_collectSignatures
  simp only [Id.run, bind, pure]
  rw [step docstrings none [] _ (OuterBody validNames) ?hbody]
  case hbody =>
    intro doclines r
    unfold OuterBody
    rw [step doclines r.1 r.2 _ (InnerBody validNames) ?hinner]
    case hinner =>
      intro line0 s
      unfold InnerBody
      by_cases h1 : line0.isEmpty = true
      · simp only [h1, if_true]
      · simp only [h1, Bool.false_eq_true, if_false]
        cases hm : matchSig (if line0.endsWith "\\" = true then stripContinuation line0 else line0) with
        | none => rfl
        | some m =>
          by_cases hc : validNames.contains m.base = true
          · simp only [hc, if_true]
            by_cases hn : s.1.isNone = true
            · simp only [hn, if_true]
              by_cases he : line0.endsWith "\\" = true <;>
                simp only [he, Bool.false_eq_true, if_true, if_false]
            · simp only [hn, Bool.false_eq_true, if_false]
              by_cases he : line0.endsWith "\\" = true <;>
                simp only [he, Bool.false_eq_true, if_true, if_false]
          · simp only [hc, Bool.false_eq_true, if_false]
    generalize (forIn doclines (r.1, r.2) (InnerBody validNames) : Id (Option Sig × List Sig)) = p
    obtain ⟨pa, pb⟩ := p
    by_cases hs : pa.isSome = true
    · simp only [hs, if_true]
    · simp only [hs, Bool.false_eq_true, if_false]
  · obtain ⟨a, b⟩ := (forIn docstrings (none, []) (OuterBody validNames) : Id LoopState)
    cases a <;> rfl
-- @decl:impl_run_bridge-end
-- @ns:impl_run_bridge-end

theorem correct_collectSignatures :
    ∀ (docstrings : List (List String)) (validNames : List String),
      problem_spec_collectSignatures docstrings validNames
        (implementation_collectSignatures docstrings validNames) := by
  intro docstrings validNames
  show implementation_collectSignatures docstrings validNames = collectSpec validNames docstrings
  rw [impl_run_bridge]
  have h := outer_loop_characterization validNames docstrings
  simp only [outerCharacterization] at h
  cases hc : collectSpec validNames docstrings with
  | nil =>
    rw [hc] at h
    rw [h]
  | cons r rest =>
    rw [hc] at h
    rw [h]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: full functional-equality post-condition — problem_spec_collectSignatures docstrings validNames result := (result = collectSpec validNames docstrings). Any impl whose correct_collectSignatures closes is PROVABLY EQUAL to collectSpec on all inputs, so genuinely-wrong impls cannot verify. This is the maximally-strong spec class; the only verify-admitted alternative is a re-expression of collectSpec itself (the 'echo').

SAME-SPEC: all 8 attack files + positive control return swebench_unified.markers.same_spec == True against the bundle Solution.lean (LeanBackend.language). The spec/axioms/pure/post regions are byte-identical; only impl+proof differ. (First reconstruction attempt omitted the -- proof-start/-- proof-end markers and read False; fixed and re-confirmed True for all.)

COMMANDS: same_spec via python -c 'from swebench_unified.markers import same_spec; ...'. Verify via `bash scripts/lean_verify.sh <file>` from repo root. Axioms via appending `#print axioms correct_collectSignatures` and re-running lean_verify. Resolve via python -c 'from swebench_unified.harness import run_resolve; run_resolve("sphinx-doc__sphinx-7748", patch)'.

### ATTACK RESULTS (7 wrong impls, all DISTINCT failure classes):
- atk1_dropcont (control-flow-effect: returns only primary [r], drops continuation signatures): verify EXIT=1, error 'Tactic `rfl` failed' at :165. Correctly REJECTED.
- atk2_reverse (boundary/order: r :: signatures.reverse): verify EXIT=1, rfl failed :165. REJECTED.
- atk3_allblocks (control-flow: removed outer `if result.isSome then break`, accumulates across all blocks): verify EXIT=1, rfl failed :163. REJECTED.
- atk4_alwaysbreak (control-flow: ignores multiline flag, always breaks after first accepted sig → collapses continuation runs): verify EXIT=1, rfl failed :163. REJECTED.
- atk5_nostrip (modeling boundary: matches raw line0 instead of stripContinuation line0 on multiline): verify EXIT=1, rfl failed :166. REJECTED.
- atk6_noemptybreak (control-flow: empty line `continue` instead of `break`, so run does not terminate at blank line): verify EXIT=1, rfl failed :166. REJECTED.
- atk7_swapfields (value: builds Sig ⟨retann,args⟩ swapping the two fields): verify EXIT=1, rfl failed :165. REJECTED.
Each failure is a genuine elaboration error (equality to collectSpec is literally false), not a timeout (all completed well under the 300s cap) and not sorry.

- atk_echo (ungrounded-oracle echo: impl := collectSpec validNames docstrings, proof by rfl): verify EXIT=0 (VERIFIES). `#print axioms correct_collectSignatures` => depends on axioms: [propext] — CLEAN (subset of {propext, Classical.choice, Quot.sound}; no sorryAx, no custom axiom). Per mandatory protocol its faithful refined patch was materialized. Because the echo reproduces EXACTLY the modeled post-patch behavior (collectSpec is the deep model of _find_signature+format_signature), its faithful patch IS the gold patch. run_resolve('sphinx-doc__sphinx-7748', gold) => RESOLVED: True, COMPLETED: True, NOTE 'resolved', ATTEMPTS 1. So the one verifying attack RESOLVES → NOT a counterexample (verify ⇒ correct held here). Under the fixed G-PANEL-1/G-EQ derivation a resolving echo is not a weakness.

POSITIVE CONTROL: pos_control.lean = verbatim bundle Solution.lean → verify EXIT=0.

PREPATCH: Solution_prepatch.lean present; reads only doclines[0], no continuation handling, returns at most [r]; on the F2P backslash-continued two-signature run the spec demands the full ordered list with the first line stripped, so the equality is unprovable and G-DIFF records 'verification failed' — prepatch bug reproduced (prepatch_reproduced=true).

A-LEG / refinement.md AUDIT: single opaque callee matchSig is a genuine A-reference — it appears IDENTICALLY in scanDoc (spec helper) and implementation_collectSignatures (impl); the closing proof chain impl_run_bridge → forIn_mprod_eq_prod → inner/outer_loop_characterization → structural equality to collectSpec consumes NO property of matchSig (it is universally quantified and threaded opaquely), so it cancels. G-AX skip is correct; there is no consumed axiom and no deep-model reference requiring G-AX validation. All refinement.md legs are R / A-reference / I — no kind-3 (ungrounded-oracle) leg. stripContinuation faithfully models line.rstrip('\\').rstrip() over the exact Python str.isspace() codepoint set (verified in prior G-PANEL-2 pass; the modeling boundary my atk5 probes is exactly this and the spec CORRECTLY rejects impls that skip the strip).

CONCLUSION: 8 attacks run (7 wrong impls all rejected by verification; 1 echo verifies with clean axioms and its faithful=gold patch RESOLVES). No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify ⇒ correct upheld on every executed case. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real repo) — no divergence found after rigorous checks.

Modeled behavior: DocstringSignatureMixin signature collection = _find_signature (the returned result) + format_signature's [sig] + self._signatures join, observable = ordered list of (args,retann) pairs. Base commit sphinx/ext/autodoc/__init__.py:1041-1094 confirmed in worktree; gold patch confirmed from test.jsonl.

Checks performed:
1. Spec region byte-identical to Solution_prepatch.lean via markers.same_spec(sol,pre,LeanBackend()) = True.
2. Proof compiles (lean_verify exit 0, linter warnings only). #print axioms correct_collectSignatures depends only on [propext, Classical.choice, Quot.sound] — no sorryAx, proof is real.
3. isPyWhitespace codepoint set (29 pts) is EXACTLY Python str.rstrip()/str.isspace() set — 0 diff over all 0x110000 codepoints (this was the prior G-PANEL-2 failure axis; the wider set is now correct, e.g. handles \x0c, \xa0, ideographic space).
4. stripContinuation matches Python line.rstrip('\\').rstrip() over 500k adversarial byte strings — 0 diffs.
5. Bundle conformance_check.py (shadow vs oracle) OK: 120017 inputs, 0 disagreements.
6. INDEPENDENT cross-check: my own transcription of the gold-patch control flow vs my own transcription of Lean collectSpec/scanDoc — 300k random inputs incl. continuation runs, name-mismatch skips, empty-line terminators, first-block-wins, exotic whitespace — 0 diffs. Confirms the model is not merely co-wrong with its own oracle.

Control-flow correspondence verified: empty line -> break/[]; backslash continuation -> multiline continue collecting; non-continuation -> break; result-first-then-signatures ordering; outer 'if result: break' first-block-wins. The one opaque callee matchSig (py_ext_sig_re.match, UNCHANGED) is used identically in spec helper scanDoc and impl, cancels, consumes no property (A-reference, G-AX skip legitimate). The unmodeled string rendering ('(%s) -> %s', '\n'.join) is value-level formatting of the same (args,retann) pairs and is not part of the collection semantics. Frame is fully pinned by full structural equality result = collectSpec validNames docstrings; no ungrounded oracle, no output component unconstrained. Spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction) independent verdict: NO-LEAKAGE.

### METHOD (not a rubber-stamp; recomputed everything):
- spec_view computed via swebench_unified.markers.spec_view(Solution.lean, LeanBackend tables). View = imports + docstring + axioms + pure + post-conditions; impl and proof regions elided to placeholders.
- markers.same_spec(Solution.lean, Solution_prepatch.lean, tables) = True: spec region is byte-stable across the pre/postpatch variants, confirming the view is the honest projection (differ only in impl).
- leakage.screen(Solution.lean, tables, gold_patch, problem_statement) run against the FROZEN instance.json gold patch + problem_statement ONLY (hints_text excluded): passed=True, hard_failures=[], warnings=[].
- Direct lowercase substring scan of the spec view for repo localizers: 'sphinx','autodoc','_find_signature','py_ext_sig_re','_signatures','format_signature','get_doc','valid_names','objpath','__mro__','__init__','docstringsignature','mixin','swig','overload','prepare_docstring','tab_width','.py','diff --git','regression','previously','fix','bug' — ALL ABSENT.

### Findings
- No diff markers, no patched file path (sphinx/ext/autodoc/__init__.py), no reproduced gold-patch code line, no changed-symbol names in any spec-view identifier or comment.
- No bug/fix narration: docstring frames target behavior ('The desired behavior collects EVERY signature offered at the start of a block'), not a fix/regression story.

SUBSTANTIVE GOLD-RECONSTRUCTION JUDGMENT: the spec's core claim ('collects every signature at the start of a block, rather than only the first') is exactly the PUBLIC problem_statement ('autodoc_docstring_signature can only pick up the first one ... nice to pick up all of them'). The extra behavioral details (backslash-continuation run, first-block-wins, Python-whitespace strip via the exact str.isspace() codepoint set) are the correctness CONTRACT the F2P tests enforce (class E's two-line continued docstring -> two ordered signatures with the trailing backslash+whitespace stripped). Pinning that contract is a spec's proper job and is required to survive G-PANEL-1 (spec-too-weak); it does not hand over the gold EDIT.

The whole spec is abstracted over List (List String) / opaque matchSig / Sig with ZERO localization to any repo file, class, method, or code structure. The one verbatim Python idiom in a comment (line.rstrip('\').rstrip()) annotates the strip semantic; it is not a diff line and does not localize the edit. A solver reading this spec view still must independently locate the sphinx autodoc code and author the two-method change. Contract revealed, edit not — correct modeling boundary. Note: leakage is judged over the spec view beyond problem_statement (NOT hints_text), per the task; hints were excluded from the screen.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.