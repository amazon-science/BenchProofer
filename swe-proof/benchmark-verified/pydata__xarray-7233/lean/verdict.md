# P2 adversarial audit — pydata__xarray-7233

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
None found. The spec's postcondition `∀ name, name ∈ result ↔ name ∈ priorCoordNames` fully pins the result set (by membership) to equal priorCoordNames EXACTLY, independent of reshapedDims. This is precisely the correct post-patch behavior since (W∩C)∪C = C. Every same-spec wrong impl I constructed disagrees with priorCoordNames on a concrete witness, so its `↔` postcondition is mathematically false and NO proof can close — confirmed: not one wrong impl verified with clean axioms, so there was no candidate whose faithful patch needed resolve-testing.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,11 @@
 -- impl-start
 def implementation_retainedCoordNames
     (reshapedDims priorCoordNames : List String) : List String := Id.run do
-  -- the names common to the reshaped dimensions and the prior coordinates
   let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
-  -- together with every prior coordinate name
-  let result := common ++ priorCoordNames
+  let result := common
   return result
 -- impl-end
+
 
 -- proof-start
 theorem correct_retainedCoordNames :
@@ -65,12 +64,8 @@
   intro reshapedDims priorCoordNames
   unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
   intro name
-  simp only [Id.run, pure, List.mem_append,
-    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
+  simp only [Id.run, pure, List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
   constructor
-  · rintro (⟨_, hc⟩ | h)
-    · exact hc
-    · exact h
-  · intro h
-    exact Or.inr h
+  · rintro ⟨_, hc⟩; exact hc
+  · intro h; exact ⟨sorry, h⟩
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,11 @@
 -- impl-start
 def implementation_retainedCoordNames
     (reshapedDims priorCoordNames : List String) : List String := Id.run do
-  -- the names common to the reshaped dimensions and the prior coordinates
-  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
-  -- together with every prior coordinate name
-  let result := common ++ priorCoordNames
+  -- Wrong: report no coordinates at all
+  let result : List String := []
   return result
 -- impl-end
+
 
 -- proof-start
 theorem correct_retainedCoordNames :
@@ -65,12 +64,6 @@
   intro reshapedDims priorCoordNames
   unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
   intro name
-  simp only [Id.run, pure, List.mem_append,
-    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
-  constructor
-  · rintro (⟨_, hc⟩ | h)
-    · exact hc
-    · exact h
-  · intro h
-    exact Or.inr h
+  simp only [Id.run, pure, List.not_mem_nil]
+  sorry
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,12 @@
 -- impl-start
 def implementation_retainedCoordNames
     (reshapedDims priorCoordNames : List String) : List String := Id.run do
-  -- the names common to the reshaped dimensions and the prior coordinates
-  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
-  -- together with every prior coordinate name
-  let result := common ++ priorCoordNames
-  return result
+  -- Wrong control-flow effect: only preserve coords when some dim is reshaped
+  match reshapedDims with
+  | [] => return []
+  | _  => return priorCoordNames
 -- impl-end
+
 
 -- proof-start
 theorem correct_retainedCoordNames :
@@ -65,12 +65,7 @@
   intro reshapedDims priorCoordNames
   unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
   intro name
-  simp only [Id.run, pure, List.mem_append,
-    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
-  constructor
-  · rintro (⟨_, hc⟩ | h)
-    · exact hc
-    · exact h
-  · intro h
-    exact Or.inr h
+  cases reshapedDims with
+  | nil => simp only [Id.run, pure, List.not_mem_nil]; sorry
+  | cons h t => simp [Id.run, pure]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,11 @@
 -- impl-start
 def implementation_retainedCoordNames
     (reshapedDims priorCoordNames : List String) : List String := Id.run do
-  -- the names common to the reshaped dimensions and the prior coordinates
-  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
-  -- together with every prior coordinate name
-  let result := common ++ priorCoordNames
+  -- Wrong: also promote every reshaped dim name, not just prior coords
+  let result := reshapedDims ++ priorCoordNames
   return result
 -- impl-end
+
 
 -- proof-start
 theorem correct_retainedCoordNames :
@@ -65,12 +64,10 @@
   intro reshapedDims priorCoordNames
   unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
   intro name
-  simp only [Id.run, pure, List.mem_append,
-    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
+  simp only [Id.run, pure, List.mem_append]
   constructor
-  · rintro (⟨_, hc⟩ | h)
-    · exact hc
+  · rintro (h | h)
+    · sorry
     · exact h
-  · intro h
-    exact Or.inr h
+  · intro h; exact Or.inr h
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,11 @@
 -- impl-start
 def implementation_retainedCoordNames
     (reshapedDims priorCoordNames : List String) : List String := Id.run do
-  -- the names common to the reshaped dimensions and the prior coordinates
-  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
-  -- together with every prior coordinate name
-  let result := common ++ priorCoordNames
+  -- Wrong boundary: drop the first prior coordinate name
+  let result := priorCoordNames.tail
   return result
 -- impl-end
+
 
 -- proof-start
 theorem correct_retainedCoordNames :
@@ -65,12 +64,8 @@
   intro reshapedDims priorCoordNames
   unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
   intro name
-  simp only [Id.run, pure, List.mem_append,
-    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
+  simp only [Id.run, pure]
   constructor
-  · rintro (⟨_, hc⟩ | h)
-    · exact hc
-    · exact h
-  · intro h
-    exact Or.inr h
+  · intro h; exact List.mem_of_mem_tail h
+  · intro h; sorry
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,13 @@
 -- impl-start
 def implementation_retainedCoordNames
     (reshapedDims priorCoordNames : List String) : List String := Id.run do
-  -- the names common to the reshaped dimensions and the prior coordinates
-  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
-  -- together with every prior coordinate name
-  let result := common ++ priorCoordNames
+  -- Wrong ungrounded oracle: keep only coords that also appear among a
+  -- hard-coded "known dimension" universe, echoing a guessed answer.
+  let knownNames := ["time", "x", "y", "lat", "lon"]
+  let result := priorCoordNames.filter (fun c => knownNames.contains c)
   return result
 -- impl-end
+
 
 -- proof-start
 theorem correct_retainedCoordNames :
@@ -65,12 +66,8 @@
   intro reshapedDims priorCoordNames
   unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
   intro name
-  simp only [Id.run, pure, List.mem_append,
-    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
+  simp only [Id.run, pure, List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
   constructor
-  · rintro (⟨_, hc⟩ | h)
-    · exact hc
-    · exact h
-  · intro h
-    exact Or.inr h
+  · rintro ⟨h, _⟩; exact h
+  · intro h; refine ⟨h, ?_⟩; sorry
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,12 +50,15 @@
 -- impl-start
 def implementation_retainedCoordNames
     (reshapedDims priorCoordNames : List String) : List String := Id.run do
-  -- the names common to the reshaped dimensions and the prior coordinates
+  -- Wrong partial domain: preserve all coords ONLY if every prior coord is a
+  -- reshaped dimension; otherwise fall back to the intersection (prepatch bug).
   let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
-  -- together with every prior coordinate name
-  let result := common ++ priorCoordNames
-  return result
+  if priorCoordNames.all (fun c => reshapedDims.contains c) then
+    return priorCoordNames
+  else
+    return common
 -- impl-end
+
 
 -- proof-start
 theorem correct_retainedCoordNames :
@@ -65,12 +68,11 @@
   intro reshapedDims priorCoordNames
   unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
   intro name
-  simp only [Id.run, pure, List.mem_append,
-    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
-  constructor
-  · rintro (⟨_, hc⟩ | h)
-    · exact hc
-    · exact h
-  · intro h
-    exact Or.inr h
+  simp only [Id.run, pure]
+  by_cases hall : priorCoordNames.all (fun c => reshapedDims.contains c) = true
+  · simp [hall]
+  · simp only [hall, if_false, List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
+    constructor
+    · rintro ⟨_, hc⟩; exact hc
+    · intro h; exact ⟨sorry, h⟩
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Determining which names remain coordinates after a grouping/reshaping operation
that splits a dimension into two.

A labelled container carries some named variables; a subset of those names are
distinguished as *coordinates*. A reshaping operation rebuilds the container —
each reshaped dimension is replaced by a pair of new dimensions — and then must
decide which names are coordinates of the result.

The operation is given two pieces of information:

* the names of the dimensions being reshaped, and
* the names that were coordinates beforehand.

It reports the names that are coordinates afterwards. The guarantee is that the
coordinate set is *preserved exactly*: every name that was a coordinate before
remains a coordinate, and no other name becomes one. In particular the outcome
does not depend on which dimensions happen to be reshaped — a name that was a
coordinate but is unrelated to any reshaped dimension is still a coordinate of
the result.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled — deciding which names are coordinates of the result — is computed
-- DEEPLY over the observable inputs (the names being reshaped and the names that
-- were coordinates), as a filter (the common names) followed by a union with the
-- prior coordinate names. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
-- changed op, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- No shared pure helpers are needed; the computation is inlined in the impl.
-- pure-end

-- post-conditions-start
/-- The names reported as coordinates of the result are exactly the names that
were coordinates beforehand: a name is a coordinate of the result iff it was a
coordinate before. This pins the coordinate set to be preserved in full — no
prior coordinate is dropped and no new name is introduced — regardless of which
dimensions are being reshaped. -/
def problem_spec_retainedCoordNames
    (reshapedDims priorCoordNames : List String) (result : List String) : Prop :=
  ∀ name, name ∈ result ↔ name ∈ priorCoordNames
-- post-conditions-end

-- impl-start
def implementation_retainedCoordNames
    (reshapedDims priorCoordNames : List String) : List String := Id.run do
  -- the names common to the reshaped dimensions and the prior coordinates
  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
  -- together with every prior coordinate name
  let result := common ++ priorCoordNames
  return result
-- impl-end

-- proof-start
theorem correct_retainedCoordNames :
    ∀ (reshapedDims priorCoordNames : List String),
      problem_spec_retainedCoordNames reshapedDims priorCoordNames
        (implementation_retainedCoordNames reshapedDims priorCoordNames) := by
  intro reshapedDims priorCoordNames
  unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
  intro name
  simp only [Id.run, pure, List.mem_append,
    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
  constructor
  · rintro (⟨_, hc⟩ | h)
    · exact hc
    · exact h
  · intro h
    exact Or.inr h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol execution

SAME-SPEC: all 8 files (7 attacks + alt-correct) return same_spec=True via swebench_unified.markers.same_spec with the lean backend (axioms/pure/pre/post byte-identical; only impl+proof regions vary).

POSITIVE CONTROL: pos_control.lean (verbatim Solution.lean) -> `bash scripts/lean_verify.sh .../pos_control.lean` exit=0. `#print axioms correct_retainedCoordNames` => [propext, Quot.sound] (clean, no sorryAx/native). alt-correct impl (`result := priorCoordNames`) also verifies exit=0 with axioms [propext].

PREPATCH: Solution_prepatch.lean (`result := common`, the intersection-only bug) -> lean_verify exit=1, carried gold proof fails to typecheck against the membership spec (mpr direction cannot show name ∈ priorCoordNames → name ∈ common). Bug reproduced.

ATTACKS (7 distinct same-spec wrong impls; verifications run concurrently in 2 batches of 4 via background bash jobs; cmd `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch-bug intersection-only (`result:=common`): exit=3 (sorry; mpr unprovable).
- atk_2 always-empty (`result:=[]`): exit=3 (sorry).
- atk_3 control-flow-effect (returns [] when reshapedDims=[], else priorCoordNames): exit=3 (sorry; nil branch unprovable).
- atk_4 union-both (`reshapedDims ++ priorCoordNames`, promotes spurious dim names): exit=3 (sorry; a reshaped-but-not-prior name is spuriously in result).
- atk_5 boundary/off-by-one (`priorCoordNames.tail`, drops head coord): exit=3 (sorry; mpr for head element unprovable).
- atk_6 ungrounded-oracle-echo (filter prior coords against a hard-coded name universe): exit=3 (sorry; a prior coord outside the universe is dropped). [first draft used the reserved keyword `universe` and failed to parse; rewritten to `knownNames` and re-run -> exit=3.]
- atk_7 partial-domain (preserve all coords only if every prior coord is a reshaped dim, else intersection fallback): exit=1 (unsolved goals; the else branch is the prepatch bug, unprovable).

WITNESS CONFIRMATION (witness.lean, #eval): each wrong impl's output set demonstrably ≠ priorCoordNames on a concrete input — reshaped=["time"],prior=["day"]→[] (atk_1/3/6/7 drop day); reshaped=["x"],prior=["day"]→[x,day] (atk_4 spurious x); prior=["day","lat"]→[lat] (atk_5 drops day). So the postcondition equivalence is FALSE for these impls — no proof could ever close, and none did.

STEP-2 RESULT: zero wrong impls closed with clean axioms => zero candidate counterexamples => no faithful patch to materialize and no resolve run required (correctly nothing to run; not an omission). Only genuinely-correct impls (pos_control, alt-correct) verify.

REFINEMENT/A-LEG AUDIT: meta.json axioms=[], opaque_callees=[], deep_model_references=[] — the changed op is a pure set expression modeled DEEPLY (filter=∩ then ++ =∪), all legs R, none A-consumed/A-reference, no kind-3 (I-with-hidden-semantics) legs; G-AX correctly skips. There are no A-legs whose correspondence to real callees could be broken. refinement.md's R legs match the post-patch `should_be_coords = (set(window_dim)&set(coords))|set(coords)` op-for-op, and the set identity (W∩C)∪C=C makes the impl's membership equal priorCoordNames, matching the spec. mapping.md symbol binding (rolling.py:976 Coarsen.construct) matches the gold patch hunk (verified against dataset patch and worktree rolling.py). patch.diff == gold (patch_equals_gold=True).

VERDICT: SOUND — the spec is tight (pins the coordinate set exactly to priorCoordNames), it rejects all 7 distinct faithful wrong impls, reproduces the prepatch bug, and admits only correct impls. verify⇏correct is NOT demonstrable here.

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
None found. The spec's postcondition `∀ name, name ∈ result ↔ name ∈ priorCoordNames` fully pins the result set (by membership) to equal priorCoordNames EXACTLY, independent of reshapedDims. This is precisely the correct post-patch behavior since (W∩C)∪C = C. Every same-spec wrong impl I constructed disagrees with priorCoordNames on a concrete witness, so its `↔` postcondition is mathematically false and NO proof can close — confirmed: not one wrong impl verified with clean axioms, so there was no candidate whose faithful patch needed resolve-testing.
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

/-!
Determining which names remain coordinates after a grouping/reshaping operation
that splits a dimension into two.

A labelled container carries some named variables; a subset of those names are
distinguished as *coordinates*. A reshaping operation rebuilds the container —
each reshaped dimension is replaced by a pair of new dimensions — and then must
decide which names are coordinates of the result.

The operation is given two pieces of information:

* the names of the dimensions being reshaped, and
* the names that were coordinates beforehand.

It reports the names that are coordinates afterwards. The guarantee is that the
coordinate set is *preserved exactly*: every name that was a coordinate before
remains a coordinate, and no other name becomes one. In particular the outcome
does not depend on which dimensions happen to be reshaped — a name that was a
coordinate but is unrelated to any reshaped dimension is still a coordinate of
the result.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The behavior
-- modeled — deciding which names are coordinates of the result — is computed
-- DEEPLY over the observable inputs (the names being reshaped and the names that
-- were coordinates), as a filter (the common names) followed by a union with the
-- prior coordinate names. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled
-- changed op, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- No shared pure helpers are needed; the computation is inlined in the impl.
-- pure-end

-- post-conditions-start
/-- The names reported as coordinates of the result are exactly the names that
were coordinates beforehand: a name is a coordinate of the result iff it was a
coordinate before. This pins the coordinate set to be preserved in full — no
prior coordinate is dropped and no new name is introduced — regardless of which
dimensions are being reshaped. -/
def problem_spec_retainedCoordNames
    (reshapedDims priorCoordNames : List String) (result : List String) : Prop :=
  ∀ name, name ∈ result ↔ name ∈ priorCoordNames
-- post-conditions-end

-- impl-start
def implementation_retainedCoordNames
    (reshapedDims priorCoordNames : List String) : List String := Id.run do
  -- the names common to the reshaped dimensions and the prior coordinates
  let common := reshapedDims.filter (fun d => priorCoordNames.contains d)
  -- together with every prior coordinate name
  let result := common ++ priorCoordNames
  return result
-- impl-end

-- proof-start
theorem correct_retainedCoordNames :
    ∀ (reshapedDims priorCoordNames : List String),
      problem_spec_retainedCoordNames reshapedDims priorCoordNames
        (implementation_retainedCoordNames reshapedDims priorCoordNames) := by
  intro reshapedDims priorCoordNames
  unfold problem_spec_retainedCoordNames implementation_retainedCoordNames
  intro name
  simp only [Id.run, pure, List.mem_append,
    List.mem_filter, List.elem_eq_mem, decide_eq_true_eq]
  constructor
  · rintro (⟨_, hc⟩ | h)
    · exact hc
    · exact h
  · intro h
    exact Or.inr h
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### Protocol execution

SAME-SPEC: all 8 files (7 attacks + alt-correct) return same_spec=True via swebench_unified.markers.same_spec with the lean backend (axioms/pure/pre/post byte-identical; only impl+proof regions vary).

POSITIVE CONTROL: pos_control.lean (verbatim Solution.lean) -> `bash scripts/lean_verify.sh .../pos_control.lean` exit=0. `#print axioms correct_retainedCoordNames` => [propext, Quot.sound] (clean, no sorryAx/native). alt-correct impl (`result := priorCoordNames`) also verifies exit=0 with axioms [propext].

PREPATCH: Solution_prepatch.lean (`result := common`, the intersection-only bug) -> lean_verify exit=1, carried gold proof fails to typecheck against the membership spec (mpr direction cannot show name ∈ priorCoordNames → name ∈ common). Bug reproduced.

ATTACKS (7 distinct same-spec wrong impls; verifications run concurrently in 2 batches of 4 via background bash jobs; cmd `bash scripts/lean_verify.sh <f>`):
- atk_1 prepatch-bug intersection-only (`result:=common`): exit=3 (sorry; mpr unprovable).
- atk_2 always-empty (`result:=[]`): exit=3 (sorry).
- atk_3 control-flow-effect (returns [] when reshapedDims=[], else priorCoordNames): exit=3 (sorry; nil branch unprovable).
- atk_4 union-both (`reshapedDims ++ priorCoordNames`, promotes spurious dim names): exit=3 (sorry; a reshaped-but-not-prior name is spuriously in result).
- atk_5 boundary/off-by-one (`priorCoordNames.tail`, drops head coord): exit=3 (sorry; mpr for head element unprovable).
- atk_6 ungrounded-oracle-echo (filter prior coords against a hard-coded name universe): exit=3 (sorry; a prior coord outside the universe is dropped). [first draft used the reserved keyword `universe` and failed to parse; rewritten to `knownNames` and re-run -> exit=3.]
- atk_7 partial-domain (preserve all coords only if every prior coord is a reshaped dim, else intersection fallback): exit=1 (unsolved goals; the else branch is the prepatch bug, unprovable).

WITNESS CONFIRMATION (witness.lean, #eval): each wrong impl's output set demonstrably ≠ priorCoordNames on a concrete input — reshaped=["time"],prior=["day"]→[] (atk_1/3/6/7 drop day); reshaped=["x"],prior=["day"]→[x,day] (atk_4 spurious x); prior=["day","lat"]→[lat] (atk_5 drops day). So the postcondition equivalence is FALSE for these impls — no proof could ever close, and none did.

STEP-2 RESULT: zero wrong impls closed with clean axioms => zero candidate counterexamples => no faithful patch to materialize and no resolve run required (correctly nothing to run; not an omission). Only genuinely-correct impls (pos_control, alt-correct) verify.

REFINEMENT/A-LEG AUDIT: meta.json axioms=[], opaque_callees=[], deep_model_references=[] — the changed op is a pure set expression modeled DEEPLY (filter=∩ then ++ =∪), all legs R, none A-consumed/A-reference, no kind-3 (I-with-hidden-semantics) legs; G-AX correctly skips. There are no A-legs whose correspondence to real callees could be broken. refinement.md's R legs match the post-patch `should_be_coords = (set(window_dim)&set(coords))|set(coords)` op-for-op, and the set identity (W∩C)∪C=C makes the impl's membership equal priorCoordNames, matching the spec. mapping.md symbol binding (rolling.py:976 Coarsen.construct) matches the gold patch hunk (verified against dataset patch and worktree rolling.py). patch.diff == gold (patch_equals_gold=True).

VERDICT: SOUND — the spec is tight (pins the coordinate set exactly to priorCoordNames), it rejects all 7 distinct faithful wrong impls, reproduces the prepatch bug, and admits only correct impls. verify⇏correct is NOT demonstrable here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for pydata__xarray-7233 lean bundle.

### Setup verified
- Worktree at base_commit 51d37d1be95547059251076b3fadaa317750aab3 (correct). The modeled callee is the POST-PATCH should_be_coords in Coarsen.construct (xarray/core/rolling.py:977-979): `should_be_coords = (set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)`.
- Solution.lean compiles under scripts/lean_verify.sh (exit 0, only an unusedVariables lint warning; no sorry).
- `#print axioms correct_retainedCoordNames` => [propext, Quot.sound]; NO sorryAx — proof is genuine.
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean backend) = True: the spec region is byte-identical between patched and prepatch bundles (only impl/proof differ), confirming the modeling boundary is fixed by the spec, not tuned per-impl.

### Faithfulness analysis
Model bijection (mapping.md): reshapedDims=list(window_dim)=W, priorCoordNames=list(self.obj.coords)=C, result set compared by MEMBERSHIP (downstream set_coords consumes a set, so order/multiplicity are irrelevant — sound abstraction).
Real callee post-patch computes the set (W ∩ C) ∪ C. By set algebra (W ∩ C) ⊆ C, so (W ∩ C) ∪ C = C exactly, for ALL W and C. Hence the real result set is precisely set(self.obj.coords) = C on every input.
Spec: problem_spec_retainedCoordNames pins `∀ name, name ∈ result ↔ name ∈ priorCoordNames`, i.e. result-set == C. This is exactly the real callee's output set.

Case-by-case (no diverging input exists):
- name ∈ W∩C: real includes (via C); spec includes (∈ priorCoords). agree.
- name ∈ C only (the F2P non-dimensional-coord case, e.g. reshapedDims=["time"], priorCoordNames=["day"]): real includes via `| set(self.obj.coords)`; spec includes. agree — this is the fix.
- name ∈ W only (reshaped dim that was not a prior coord): W∩C excludes it and `|C` does not add it => real EXCLUDES; spec excludes (∉ priorCoords). agree — spec does NOT over-demand these.
- name ∈ neither: excluded by both. agree.

The spec is neither too strong nor drifted: it demands exactly result-set = priorCoords, which is what the real post-patch function delivers regardless of reshapedDims. No input makes the modeled function disagree with the real callee. The G-CONF gate independently corroborates this (pass, transliterated shadow of the post-patch expression diffed as sets over >=1e5 fuzzed name-list pairs).

Verdict: FAITHFUL — no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view region byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True); Solution.lean compiles (exit 0, no sorry). Lexical G-LEAK screen passes with zero hard_failures: no diff markers, no reproduced gold-patch line, no patched file path (xarray/core/rolling.py), no spec-view identifier/comment echoing patched repo symbols (construct/set_coords/should_be_coords/window_dim), no bug/fix narration.

Semantic judgement: the public problem_statement already fully discloses the intended behavior — 'All variables that were coordinates before the coarsen.construct stay as coordinates afterwards' (title flags non-dimensional coordinate demotion). The spec-view postcondition (`name ∈ result ↔ name ∈ priorCoordNames`, 'coordinate set preserved in full … regardless of which dimensions are reshaped') is a faithful formalization of that already-public guarantee, not fresh disclosure of the gold edit. The gold diff `(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)` is the realization of the public statement (via (W∩C)∪C=C). The view names none of window_dim/set_coords/the intersection-union edit; impl and proof regions the solver must supply are elided. The docstring/axioms comments describe modeled behavior and the Lean impl shape abstractly, not the Python edit specifics. No spec-view line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
