# P2 adversarial audit — django__django-14752

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,10 @@
 def implementation_get {Obj E : Type}
     (render _defaultRender : Obj → String → E)
     (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
-  -- Build the results list by applying the per-item rendering to each selected
-  -- object in turn. The per-item rendering used is `render` — the dispatched,
-  -- hence overridable, step — applied uniformly to every selected object.
+  -- WRONG (prepatch bug): use the hardwired _defaultRender, ignoring dispatched render.
   let mut results : List E := []
   for o in objects do
-    results := results ++ [render o fieldKey]
-  -- Report the has-more flag verbatim.
+    results := results ++ [_defaultRender o fieldKey]
   return { results := results, more := hasMore }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,10 @@
 def implementation_get {Obj E : Type}
     (render _defaultRender : Obj → String → E)
     (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
-  -- Build the results list by applying the per-item rendering to each selected
-  -- object in turn. The per-item rendering used is `render` — the dispatched,
-  -- hence overridable, step — applied uniformly to every selected object.
+  -- WRONG: reverse the per-item rendering order.
   let mut results : List E := []
   for o in objects do
-    results := results ++ [render o fieldKey]
-  -- Report the has-more flag verbatim.
+    results := [render o fieldKey] ++ results
   return { results := results, more := hasMore }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,14 +60,8 @@
 def implementation_get {Obj E : Type}
     (render _defaultRender : Obj → String → E)
     (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
-  -- Build the results list by applying the per-item rendering to each selected
-  -- object in turn. The per-item rendering used is `render` — the dispatched,
-  -- hence overridable, step — applied uniformly to every selected object.
-  let mut results : List E := []
-  for o in objects do
-    results := results ++ [render o fieldKey]
-  -- Report the has-more flag verbatim.
-  return { results := results, more := hasMore }
+  -- WRONG (partial domain / boundary): drop the first object's entry.
+  return { results := (objects.map (fun o => render o fieldKey)).drop 1, more := hasMore }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,10 @@
 def implementation_get {Obj E : Type}
     (render _defaultRender : Obj → String → E)
     (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
-  -- Build the results list by applying the per-item rendering to each selected
-  -- object in turn. The per-item rendering used is `render` — the dispatched,
-  -- hence overridable, step — applied uniformly to every selected object.
+  -- WRONG (control-flow effect): append each rendering twice.
   let mut results : List E := []
   for o in objects do
-    results := results ++ [render o fieldKey]
-  -- Report the has-more flag verbatim.
+    results := results ++ [render o fieldKey, render o fieldKey]
   return { results := results, more := hasMore }
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,14 +60,11 @@
 def implementation_get {Obj E : Type}
     (render _defaultRender : Obj → String → E)
     (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
-  -- Build the results list by applying the per-item rendering to each selected
-  -- object in turn. The per-item rendering used is `render` — the dispatched,
-  -- hence overridable, step — applied uniformly to every selected object.
+  -- WRONG: report negated has-more flag.
   let mut results : List E := []
   for o in objects do
     results := results ++ [render o fieldKey]
-  -- Report the has-more flag verbatim.
-  return { results := results, more := hasMore }
+  return { results := results, more := !hasMore }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -59,15 +59,9 @@
 -- impl-start
 def implementation_get {Obj E : Type}
     (render _defaultRender : Obj → String → E)
-    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
-  -- Build the results list by applying the per-item rendering to each selected
-  -- object in turn. The per-item rendering used is `render` — the dispatched,
-  -- hence overridable, step — applied uniformly to every selected object.
-  let mut results : List E := []
-  for o in objects do
-    results := results ++ [render o fieldKey]
-  -- Report the has-more flag verbatim.
-  return { results := results, more := hasMore }
+    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E :=
+  -- ECHO: directly return the pinned outputs (observationally == gold).
+  { results := objects.map (fun o => render o fieldKey), more := hasMore }
 -- impl-end
 
 -- proof-start
@@ -77,22 +71,6 @@
       problem_spec_get render objects fieldKey hasMore
         (implementation_get render defaultRender objects fieldKey hasMore) := by
   intro render defaultRender objects fieldKey hasMore
-  -- Helper: the cleaned `forIn` accumulation appends the per-item renderings.
-  have helper : ∀ (os : List Obj) (init : List E),
-      Id.run (forIn os init (fun o r => pure (ForInStep.yield (r ++ [render o fieldKey]))))
-        = init ++ os.map (fun o => render o fieldKey) := by
-    intro os
-    induction os with
-    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons a as ih =>
-        intro init; rw [List.forIn_cons]
-        simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
-  refine ⟨?_, rfl⟩
-  show (implementation_get render defaultRender objects fieldKey hasMore).results = _
-  unfold implementation_get
-  simp only [Id.run, bind]
-  have := helper objects []
-  simp only [Id.run] at this
-  rw [this]
-  rfl
+  unfold problem_spec_get implementation_get
+  exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,13 +60,10 @@
 def implementation_get {Obj E : Type}
     (render _defaultRender : Obj → String → E)
     (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
-  -- Build the results list by applying the per-item rendering to each selected
-  -- object in turn. The per-item rendering used is `render` — the dispatched,
-  -- hence overridable, step — applied uniformly to every selected object.
+  -- WRONG: only render when hasMore is true, otherwise use _defaultRender.
   let mut results : List E := []
   for o in objects do
-    results := results ++ [render o fieldKey]
-  -- Report the has-more flag verbatim.
+    results := results ++ [if hasMore then render o fieldKey else _defaultRender o fieldKey]
   return { results := results, more := hasMore }
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the JSON payload of a search-results handler.

The handler answers a lookup request by producing a response carrying two parts:

  * `results`: a list of per-item entries, one for each object selected by the
    query, in the same order as the selected objects;
  * `more`: a single flag reporting whether further pages of results remain.

The way a single selected object is turned into its entry is supplied as a
dedicated per-item rendering step, applied uniformly to every selected object.
Modeling that step as an arbitrary function pins the behavior below to exactly
"each entry is the per-item rendering applied to the corresponding object, in
order, and the more-flag is reported verbatim" — independent of what any
particular rendering produces.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two steps are modeled as
-- arbitrary function parameters:
--   * `render : Obj → String → E` — the per-item rendering that turns one
--     selected object (together with the field key identifying which attribute
--     names the entry) into its response entry. Supplied as a parameter so the
--     spec holds for EVERY rendering, the modeled behavior being solely that the
--     results list is this rendering applied per object, in order.
-- The objects and the entry type are likewise abstract carriers (`Obj`, `E`):
-- the handler never inspects an object except through `render`, and never
-- inspects an entry at all. Hence the spec needs no `opaque`/`axiom` contract.
-- axioms-end

-- pure-start
/-- The response payload: the per-item entries and the has-more flag. -/
structure Resp (E : Type) where
  results : List E
  more : Bool
-- pure-end

-- post-conditions-start
/-- The response is fully pinned to the inputs (directive 5 frame):

  * `results` is the per-item rendering applied to each selected object, in the
    same order as the selected objects (no entry added, dropped, reordered, or
    computed by any means other than `render`);
  * `more` equals the supplied has-more flag verbatim.

No output component is left free: every entry is `render` of the corresponding
object, and the flag is the input flag. -/
def problem_spec_get {Obj E : Type}
    (render : Obj → String → E)
    (objects : List Obj) (fieldKey : String) (hasMore : Bool)
    (result : Resp E) : Prop :=
  result.results = objects.map (fun o => render o fieldKey) ∧
  result.more = hasMore
-- post-conditions-end

-- impl-start
def implementation_get {Obj E : Type}
    (render _defaultRender : Obj → String → E)
    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
  -- Build the results list by applying the per-item rendering to each selected
  -- object in turn. The per-item rendering used is `render` — the dispatched,
  -- hence overridable, step — applied uniformly to every selected object.
  let mut results : List E := []
  for o in objects do
    results := results ++ [render o fieldKey]
  -- Report the has-more flag verbatim.
  return { results := results, more := hasMore }
-- impl-end

-- proof-start
theorem correct_get {Obj E : Type} :
    ∀ (render defaultRender : Obj → String → E)
      (objects : List Obj) (fieldKey : String) (hasMore : Bool),
      problem_spec_get render objects fieldKey hasMore
        (implementation_get render defaultRender objects fieldKey hasMore) := by
  intro render defaultRender objects fieldKey hasMore
  -- Helper: the cleaned `forIn` accumulation appends the per-item renderings.
  have helper : ∀ (os : List Obj) (init : List E),
      Id.run (forIn os init (fun o r => pure (ForInStep.yield (r ++ [render o fieldKey]))))
        = init ++ os.map (fun o => render o fieldKey) := by
    intro os
    induction os with
    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
        intro init; rw [List.forIn_cons]
        simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
  refine ⟨?_, rfl⟩
  show (implementation_get render defaultRender objects fieldKey hasMore).results = _
  unfold implementation_get
  simp only [Id.run, bind]
  have := helper objects []
  simp only [Id.run] at this
  rw [this]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_get pins BOTH outputs equationally — results = objects.map (fun o => render o fieldKey) AND more = hasMore. render/_defaultRender universally quantified. spec_view elides impl+proof; same_spec True for all 7 attacks + pos_control (verified via swebench_unified.markers.same_spec, lean backend).

Axioms via appended '#print axioms correct_get'.
### Results
- pos_control.lean (gold): exit 0; axioms [propext, Quot.sound] CLEAN, no sorry.
- atk_1.lean prepatch-bug (route via _defaultRender, ignore render): exit 1 (fails to close).
- atk_2.lean reverse order: exit 1.
- atk_3.lean partial/boundary (drop 1): exit 1.
- atk_4.lean control-flow effect (duplicate each entry): exit 1.
- atk_5.lean boundary on 2nd conjunct (more:=!hasMore): exit 1.
- atk_6.lean ungrounded-oracle echo (direct return objects.map render, hasMore; proof exact ⟨rfl,rfl⟩): exit 0; '#print axioms correct_get' => 'does not depend on any axioms' (CLEAN, no sorry). CLOSES.
- atk_7.lean conditional render on hasMore: exit 1.

Only atk_6 is a closing wrong-impl with clean axioms, and it is OBSERVATIONALLY IDENTICAL to gold (returns exactly the pinned outputs). Per protocol I materialized its faithful refined patch (= gold refactor: route each entry through dispatched serialize_result per object in order) and RAN it through the official harness:
  swebench_unified.harness.run_resolve('django__django-14752', <patch>, run_id='sbu-eqaudit-vpvifkpe-atk6', timeout=1800, retries=1)
  => ResolveResult(resolved=True, completed=True, note='resolved', attempts=1, flaky=False); FAIL_TO_PASS test_serialize_result SUCCESS, all PASS_TO_PASS SUCCESS. Docker via `docker`.
Since this closing impl's faithful patch RESOLVES, it does NOT break the spec (verify => correct holds for it).

PREPATCH REPRODUCED: Solution_prepatch.lean copied to prepatch.lean; same_spec True; verify exit 1 (fails to close) — frozen spec discriminates the prepatch bug (routes through _defaultRender, ignoring dispatched render; first conjunct forces objects.map _defaultRender = objects.map render, not derivable for arbitrary functions).

REFINEMENT.MD AUDIT: op#1 empty accumulator (I); op#2 per-object loop R + render↔real serialize_result A-reference (left as REAL post-patch callee in G-CONF, NOT axiomatized; differential-tested 1e5 inputs, 0 disagreements per conformance_check.py); op#3 payload framing R/I. NO A-consumed row: proof consumes no property of render/_defaultRender (both universally quantified) — confirmed by clean axioms=[]; axiom_check.py is a skip stub. No kind-3 leg. A-reference correspondence (render ↔ serialize_result, _defaultRender ↔ pre-patch inline entry) holds and matches mapping.md's type bijection.

CONCLUSION: every genuinely-divergent same-spec impl fails to close; the sole closing wrong-impl (atk_6) is a gold-equivalent echo whose materialized faithful patch RESOLVES. No verify⇏correct witness exists. => SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the JSON payload of a search-results handler.

The handler answers a lookup request by producing a response carrying two parts:

  * `results`: a list of per-item entries, one for each object selected by the
    query, in the same order as the selected objects;
  * `more`: a single flag reporting whether further pages of results remain.

The way a single selected object is turned into its entry is supplied as a
dedicated per-item rendering step, applied uniformly to every selected object.
Modeling that step as an arbitrary function pins the behavior below to exactly
"each entry is the per-item rendering applied to the corresponding object, in
order, and the more-flag is reported verbatim" — independent of what any
particular rendering produces.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two steps are modeled as
-- arbitrary function parameters:
--   * `render : Obj → String → E` — the per-item rendering that turns one
--     selected object (together with the field key identifying which attribute
--     names the entry) into its response entry. Supplied as a parameter so the
--     spec holds for EVERY rendering, the modeled behavior being solely that the
--     results list is this rendering applied per object, in order.
-- The objects and the entry type are likewise abstract carriers (`Obj`, `E`):
-- the handler never inspects an object except through `render`, and never
-- inspects an entry at all. Hence the spec needs no `opaque`/`axiom` contract.
-- axioms-end

-- pure-start
/-- The response payload: the per-item entries and the has-more flag. -/
structure Resp (E : Type) where
  results : List E
  more : Bool
-- pure-end

-- post-conditions-start
/-- The response is fully pinned to the inputs (directive 5 frame):

  * `results` is the per-item rendering applied to each selected object, in the
    same order as the selected objects (no entry added, dropped, reordered, or
    computed by any means other than `render`);
  * `more` equals the supplied has-more flag verbatim.

No output component is left free: every entry is `render` of the corresponding
object, and the flag is the input flag. -/
def problem_spec_get {Obj E : Type}
    (render : Obj → String → E)
    (objects : List Obj) (fieldKey : String) (hasMore : Bool)
    (result : Resp E) : Prop :=
  result.results = objects.map (fun o => render o fieldKey) ∧
  result.more = hasMore
-- post-conditions-end

-- impl-start
def implementation_get {Obj E : Type}
    (render _defaultRender : Obj → String → E)
    (objects : List Obj) (fieldKey : String) (hasMore : Bool) : Resp E := Id.run do
  -- Build the results list by applying the per-item rendering to each selected
  -- object in turn. The per-item rendering used is `render` — the dispatched,
  -- hence overridable, step — applied uniformly to every selected object.
  let mut results : List E := []
  for o in objects do
    results := results ++ [render o fieldKey]
  -- Report the has-more flag verbatim.
  return { results := results, more := hasMore }
-- impl-end

-- proof-start
theorem correct_get {Obj E : Type} :
    ∀ (render defaultRender : Obj → String → E)
      (objects : List Obj) (fieldKey : String) (hasMore : Bool),
      problem_spec_get render objects fieldKey hasMore
        (implementation_get render defaultRender objects fieldKey hasMore) := by
  intro render defaultRender objects fieldKey hasMore
  -- Helper: the cleaned `forIn` accumulation appends the per-item renderings.
  have helper : ∀ (os : List Obj) (init : List E),
      Id.run (forIn os init (fun o r => pure (ForInStep.yield (r ++ [render o fieldKey]))))
        = init ++ os.map (fun o => render o fieldKey) := by
    intro os
    induction os with
    | nil => intro init; simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
        intro init; rw [List.forIn_cons]
        simp only [Id.run, bind] at ih ⊢; rw [ih]; simp
  refine ⟨?_, rfl⟩
  show (implementation_get render defaultRender objects fieldKey hasMore).results = _
  unfold implementation_get
  simp only [Id.run, bind]
  have := helper objects []
  simp only [Id.run] at this
  rw [this]
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_get pins BOTH outputs equationally — results = objects.map (fun o => render o fieldKey) AND more = hasMore. render/_defaultRender universally quantified. spec_view elides impl+proof; same_spec True for all 7 attacks + pos_control (verified via swebench_unified.markers.same_spec, lean backend).

Axioms via appended '#print axioms correct_get'.
### Results
- pos_control.lean (gold): exit 0; axioms [propext, Quot.sound] CLEAN, no sorry.
- atk_1.lean prepatch-bug (route via _defaultRender, ignore render): exit 1 (fails to close).
- atk_2.lean reverse order: exit 1.
- atk_3.lean partial/boundary (drop 1): exit 1.
- atk_4.lean control-flow effect (duplicate each entry): exit 1.
- atk_5.lean boundary on 2nd conjunct (more:=!hasMore): exit 1.
- atk_6.lean ungrounded-oracle echo (direct return objects.map render, hasMore; proof exact ⟨rfl,rfl⟩): exit 0; '#print axioms correct_get' => 'does not depend on any axioms' (CLEAN, no sorry). CLOSES.
- atk_7.lean conditional render on hasMore: exit 1.

Only atk_6 is a closing wrong-impl with clean axioms, and it is OBSERVATIONALLY IDENTICAL to gold (returns exactly the pinned outputs). Per protocol I materialized its faithful refined patch (= gold refactor: route each entry through dispatched serialize_result per object in order) and RAN it through the official harness:
  swebench_unified.harness.run_resolve('django__django-14752', <patch>, run_id='sbu-eqaudit-vpvifkpe-atk6', timeout=1800, retries=1)
  => ResolveResult(resolved=True, completed=True, note='resolved', attempts=1, flaky=False); FAIL_TO_PASS test_serialize_result SUCCESS, all PASS_TO_PASS SUCCESS. Docker via `docker`.
Since this closing impl's faithful patch RESOLVES, it does NOT break the spec (verify => correct holds for it).

PREPATCH REPRODUCED: Solution_prepatch.lean copied to prepatch.lean; same_spec True; verify exit 1 (fails to close) — frozen spec discriminates the prepatch bug (routes through _defaultRender, ignoring dispatched render; first conjunct forces objects.map _defaultRender = objects.map render, not derivable for arbitrary functions).

REFINEMENT.MD AUDIT: op#1 empty accumulator (I); op#2 per-object loop R + render↔real serialize_result A-reference (left as REAL post-patch callee in G-CONF, NOT axiomatized; differential-tested 1e5 inputs, 0 disagreements per conformance_check.py); op#3 payload framing R/I. NO A-consumed row: proof consumes no property of render/_defaultRender (both universally quantified) — confirmed by clean axioms=[]; axiom_check.py is a skip stub. No kind-3 leg. A-reference correspondence (render ↔ serialize_result, _defaultRender ↔ pre-patch inline entry) holds and matches mapping.md's type bijection.

CONCLUSION: every genuinely-divergent same-spec impl fails to close; the sole closing wrong-impl (atk_6) is a gold-equivalent echo whose materialized faithful patch RESOLVES. No verify⇏correct witness exists. => SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function AutocompleteJsonView.get (django/contrib/admin/views/autocomplete.py, base_commit 2c7846d992 / b64db05b9c). Real post-patch behavior: results = [ self.serialize_result(obj, to_field_name) for obj in context['object_list'] ] (per-object rendering, order-preserving, uniform to_field_name); pagination.more = context['page_obj'].has_next() copied verbatim. Spec problem_spec_get: result.results = objects.map (fun o => render o fieldKey) AND result.more = hasMore. Type bijection exact: objects↔object_list, fieldKey↔to_field_name, hasMore↔has_next(), render↔serialize_result (universally quantified, bound to the REAL serialize_result by G-CONF, conf_skip=false), Resp{results,more}↔{'results':[...],'pagination':{'more':...}}. The nested pagination dict is faithfully collapsed into Resp.more. Order preserved on both sides (list comprehension ↔ List.map). No input makes the model disagree with the real callee's results-assembly — the spec pins exactly 'each entry = render applied to the corresponding object, in order; more = input flag', which is precisely the fixed behavior. Universal quantification over render makes the spec neither too strong nor too weak relative to the extension point the patch introduces. Verification: lean_verify.sh exit 0 (compiles, no sorry); #print axioms correct_get => [propext, Quot.sound] only (NO sorryAx — genuine proof); proof helper correctly establishes forIn accumulator = init ++ os.map(render); axioms=[], patch_equals_gold=true consistent with universally-quantified render (no axiomatized callee). No faithfulness break found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (markers.spec_view over LeanBackend.language) elides impl and proof regions; same_spec(gold,prepatch)=True and Solution.lean compiles clean (lean_verify exit 0, no sorry). Visible spec = abstract docstring + axioms comment + `structure Resp` + `problem_spec_get` pinning `result.results = objects.map (fun o => render o fieldKey)` and `result.more = hasMore`. render/Obj/E/objects/fieldKey/hasMore are universally-quantified abstract carriers. The spec view quotes NO gold-patch specifics: no `serialize_result`, no `str(getattr(obj, to_field_name))`, no `{'id':...,'text':...}` dict, and no mention of the dispatch/overridable-method mechanism that constitutes the fix. It only pins the observable payload shape (results = per-item rendering per object in order; more = flag verbatim). Moreover the public problem_statement already contains the ENTIRE gold edit verbatim (before/after JsonResponse blocks plus the full `def serialize_result(self, obj, to_field_name): return {'id': str(getattr(obj, to_field_name)), 'text': str(obj)}`), so the abstract spec reveals strictly less than what is already public. The only place gold and prepatch differ (impl routes loop through `render` vs `_defaultRender`) lives in the elided impl region and is not in the spec view. No line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
