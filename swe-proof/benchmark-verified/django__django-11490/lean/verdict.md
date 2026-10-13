# P2 adversarial audit — django__django-11490

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is a unique-solution functional pin. problem_spec_propagateColumns fixes result.length, result.map Prod.fst (= parts.map of the conditional-adopt function), AND result.map Prod.snd (= parts). A List (QueryPart x QueryPart) is fully determined index-wise by its two projections plus its length, so the spec admits exactly one solution. Proved mechanically: spec_unique (any two results satisfying problem_spec are equal) verifies at uniq.lean (exit 0). Hence no divergent-but-closing implementation exists. The only closing wrong-impl candidate (atk_7) is a behavioral ECHO of gold (map-form rewrite of the same conditional) whose faithful patch (= gold patch) RESOLVES=True under run_resolve, so it is not a weakness per the panel_1/eq policy.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,15 @@
   let mut out : List (QueryPart × QueryPart) := []
   for part in parts do
     if part.columns = [] ∧ composedColumns ≠ [] then
-      -- This part fixes no column list of its own and the composed query requests
-      -- one: build this evaluation's query from a fresh copy carrying the composed
-      -- column list, while carrying the part's own definition forward unchanged.
-      let derived := { part with columns := composedColumns }
-      out := out ++ [(derived, part)]
+      let part := { part with columns := composedColumns }
+      out := out ++ [(part, part)]
     else
-      -- The part already fixes its own columns (or none are requested): use it as
-      -- given and carry it forward unchanged.
       out := out ++ [(part, part)]
   return out
 -- impl-end
 
 -- proof-start
+
 theorem correct_propagateColumns :
     ∀ (parts : List QueryPart) (composedColumns : List String),
       problem_spec_propagateColumns parts composedColumns
@@ -123,4 +119,5 @@
   · simp only [List.map_map, Function.comp_def]
   · simp only [List.map_map, Function.comp_def]
     exact List.map_id_fun' ▸ rfl
+
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,20 +69,16 @@
     : List (QueryPart × QueryPart) := Id.run do
   let mut out : List (QueryPart × QueryPart) := []
   for part in parts do
-    if part.columns = [] ∧ composedColumns ≠ [] then
-      -- This part fixes no column list of its own and the composed query requests
-      -- one: build this evaluation's query from a fresh copy carrying the composed
-      -- column list, while carrying the part's own definition forward unchanged.
+    if composedColumns ≠ [] then
       let derived := { part with columns := composedColumns }
       out := out ++ [(derived, part)]
     else
-      -- The part already fixes its own columns (or none are requested): use it as
-      -- given and carry it forward unchanged.
       out := out ++ [(part, part)]
   return out
 -- impl-end
 
 -- proof-start
+
 theorem correct_propagateColumns :
     ∀ (parts : List QueryPart) (composedColumns : List String),
       problem_spec_propagateColumns parts composedColumns
@@ -123,4 +119,5 @@
   · simp only [List.map_map, Function.comp_def]
   · simp only [List.map_map, Function.comp_def]
     exact List.map_id_fun' ▸ rfl
+
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,23 +66,11 @@
 -- impl-start
 def implementation_propagateColumns
     (parts : List QueryPart) (composedColumns : List String)
-    : List (QueryPart × QueryPart) := Id.run do
-  let mut out : List (QueryPart × QueryPart) := []
-  for part in parts do
-    if part.columns = [] ∧ composedColumns ≠ [] then
-      -- This part fixes no column list of its own and the composed query requests
-      -- one: build this evaluation's query from a fresh copy carrying the composed
-      -- column list, while carrying the part's own definition forward unchanged.
-      let derived := { part with columns := composedColumns }
-      out := out ++ [(derived, part)]
-    else
-      -- The part already fixes its own columns (or none are requested): use it as
-      -- given and carry it forward unchanged.
-      out := out ++ [(part, part)]
-  return out
+    : List (QueryPart × QueryPart) := []
 -- impl-end
 
 -- proof-start
+
 theorem correct_propagateColumns :
     ∀ (parts : List QueryPart) (composedColumns : List String),
       problem_spec_propagateColumns parts composedColumns
@@ -123,4 +111,5 @@
   · simp only [List.map_map, Function.comp_def]
   · simp only [List.map_map, Function.comp_def]
     exact List.map_id_fun' ▸ rfl
+
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,19 +70,15 @@
   let mut out : List (QueryPart × QueryPart) := []
   for part in parts do
     if part.columns = [] ∧ composedColumns ≠ [] then
-      -- This part fixes no column list of its own and the composed query requests
-      -- one: build this evaluation's query from a fresh copy carrying the composed
-      -- column list, while carrying the part's own definition forward unchanged.
       let derived := { part with columns := composedColumns }
-      out := out ++ [(derived, part)]
+      out := out ++ [(part, derived)]
     else
-      -- The part already fixes its own columns (or none are requested): use it as
-      -- given and carry it forward unchanged.
       out := out ++ [(part, part)]
   return out
 -- impl-end
 
 -- proof-start
+
 theorem correct_propagateColumns :
     ∀ (parts : List QueryPart) (composedColumns : List String),
       problem_spec_propagateColumns parts composedColumns
@@ -123,4 +119,5 @@
   · simp only [List.map_map, Function.comp_def]
   · simp only [List.map_map, Function.comp_def]
     exact List.map_id_fun' ▸ rfl
+
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,20 +69,16 @@
     : List (QueryPart × QueryPart) := Id.run do
   let mut out : List (QueryPart × QueryPart) := []
   for part in parts do
-    if part.columns = [] ∧ composedColumns ≠ [] then
-      -- This part fixes no column list of its own and the composed query requests
-      -- one: build this evaluation's query from a fresh copy carrying the composed
-      -- column list, while carrying the part's own definition forward unchanged.
+    if part.columns ≠ [] ∧ composedColumns ≠ [] then
       let derived := { part with columns := composedColumns }
       out := out ++ [(derived, part)]
     else
-      -- The part already fixes its own columns (or none are requested): use it as
-      -- given and carry it forward unchanged.
       out := out ++ [(part, part)]
   return out
 -- impl-end
 
 -- proof-start
+
 theorem correct_propagateColumns :
     ∀ (parts : List QueryPart) (composedColumns : List String),
       problem_spec_propagateColumns parts composedColumns
@@ -123,4 +119,5 @@
   · simp only [List.map_map, Function.comp_def]
   · simp only [List.map_map, Function.comp_def]
     exact List.map_id_fun' ▸ rfl
+
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,21 +68,17 @@
     (parts : List QueryPart) (composedColumns : List String)
     : List (QueryPart × QueryPart) := Id.run do
   let mut out : List (QueryPart × QueryPart) := []
-  for part in parts do
+  for part in parts.tail do
     if part.columns = [] ∧ composedColumns ≠ [] then
-      -- This part fixes no column list of its own and the composed query requests
-      -- one: build this evaluation's query from a fresh copy carrying the composed
-      -- column list, while carrying the part's own definition forward unchanged.
       let derived := { part with columns := composedColumns }
       out := out ++ [(derived, part)]
     else
-      -- The part already fixes its own columns (or none are requested): use it as
-      -- given and carry it forward unchanged.
       out := out ++ [(part, part)]
   return out
 -- impl-end
 
 -- proof-start
+
 theorem correct_propagateColumns :
     ∀ (parts : List QueryPart) (composedColumns : List String),
       problem_spec_propagateColumns parts composedColumns
@@ -123,4 +119,5 @@
   · simp only [List.map_map, Function.comp_def]
   · simp only [List.map_map, Function.comp_def]
     exact List.map_id_fun' ▸ rfl
+
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -66,20 +66,10 @@
 -- impl-start
 def implementation_propagateColumns
     (parts : List QueryPart) (composedColumns : List String)
-    : List (QueryPart × QueryPart) := Id.run do
-  let mut out : List (QueryPart × QueryPart) := []
-  for part in parts do
-    if part.columns = [] ∧ composedColumns ≠ [] then
-      -- This part fixes no column list of its own and the composed query requests
-      -- one: build this evaluation's query from a fresh copy carrying the composed
-      -- column list, while carrying the part's own definition forward unchanged.
-      let derived := { part with columns := composedColumns }
-      out := out ++ [(derived, part)]
-    else
-      -- The part already fixes its own columns (or none are requested): use it as
-      -- given and carry it forward unchanged.
-      out := out ++ [(part, part)]
-  return out
+    : List (QueryPart × QueryPart) := parts.map (fun part =>
+    if part.columns = [] ∧ composedColumns ≠ []
+    then ({ part with columns := composedColumns }, part)
+    else (part, part))
 -- impl-end
 
 -- proof-start
@@ -88,39 +78,19 @@
       problem_spec_propagateColumns parts composedColumns
         (implementation_propagateColumns parts composedColumns) := by
   intro parts cc
-  have helper : ∀ (init : List (QueryPart × QueryPart)),
-      Id.run (forIn parts init (fun part r =>
-        (if part.columns = [] ∧ cc ≠ [] then
-          pure (ForInStep.yield (r ++ [(({ part with columns := cc } : QueryPart), part)]))
-        else
-          pure (ForInStep.yield (r ++ [(part, part)]))) : Id _))
-        = init ++ parts.map (fun part =>
-            ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
-    intro init
-    induction parts generalizing init with
-    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
-    | cons a as ih =>
-      rw [List.forIn_cons]
-      simp only [Id.run, bind] at ih ⊢
-      by_cases h : a.columns = [] ∧ cc ≠ []
-      · rw [if_pos h]
-        simp only [ih, if_pos h, List.map_cons]
-        rw [List.append_assoc]; rfl
-      · rw [if_neg h]
-        simp only [ih, if_neg h, List.map_cons]
-        rw [List.append_assoc]; rfl
-  have himpl : implementation_propagateColumns parts cc
-      = parts.map (fun part =>
-          ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
-    have hb := helper []
-    rw [List.nil_append] at hb
-    rw [← hb]
-    rfl
-  unfold problem_spec_propagateColumns
-  rw [himpl]
+  unfold problem_spec_propagateColumns implementation_propagateColumns
   refine ⟨?_, ?_, ?_⟩
   · simp [List.length_map]
-  · simp only [List.map_map, Function.comp_def]
-  · simp only [List.map_map, Function.comp_def]
-    exact List.map_id_fun' ▸ rfl
+  · rw [List.map_map]
+    apply List.map_congr_left
+    intro part _
+    by_cases h : part.columns = [] ∧ cc ≠ [] <;> simp [Function.comp, h]
+  · rw [List.map_map]
+    rw [show (Prod.snd ∘ fun part : QueryPart =>
+        if part.columns = [] ∧ cc ≠ []
+        then ({ part with columns := cc }, part) else (part, part))
+      = id from ?_, List.map_id]
+    funext part
+    by_cases h : part.columns = [] ∧ cc ≠ [] <;> simp [Function.comp, h]
+
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Evaluating a composed query to project a chosen list of columns.

A composed query is built from several query parts. When the composed query is
evaluated to project a specific list of columns, each part that does NOT itself
specify a column list adopts the composed query's column list for THIS evaluation;
a part that already specifies its own column list is used as given.

The contract that matters here: producing one evaluation's column projection must
leave the underlying part definitions exactly as they were. The parts are shared,
so if an evaluation altered a part while adopting the composed column list, a
LATER evaluation of the same composed query for a DIFFERENT column list would see
the stale list and be unable to change its columns. Hence each evaluation derives
the per-part query it builds from, while the part definitions themselves are
carried through unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is deep-modeled.
-- The per-evaluation step reads one thing off each part — whether it already
-- specifies a column list — and produces two things: the query used to build that
-- part for this evaluation, and the part's definition carried forward. A query
-- part is observed solely by the list of columns it projects, modeled directly
-- as `QueryPart.columns`, so the bundle needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- A query part, observed only by the list of column names it projects
(empty ⇔ it specifies no particular column list of its own). -/
structure QueryPart where
  columns : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Evaluating the composed query (column list `composedColumns`) over its
`parts` is fully pinned to the inputs. Each result entry corresponds to one part:
its first component is the query actually built for this evaluation, its second
component is the part's definition carried forward.

  * there is exactly one result entry per part;
  * the query built for a part adopts the composed column list precisely when the
    part specifies no column list of its own AND the composed query requests a
    specific column list (`composedColumns ≠ []`); otherwise the part is used as
    given (directive-5 frame: the used-as-given branch pins it to its input);
  * EVERY part definition is carried forward exactly equal to its input
    (directive-5 frame): producing this evaluation never alters a part, so a
    later evaluation may choose a different column list.

Both output components are pinned for every part, so no incorrect evaluator can
fill a free hole — in particular it may not leave a part altered. -/
def problem_spec_propagateColumns
    (parts : List QueryPart) (composedColumns : List String)
    (result : List (QueryPart × QueryPart)) : Prop :=
  result.length = parts.length ∧
  (result.map Prod.fst = parts.map (fun part =>
      if part.columns = [] ∧ composedColumns ≠ []
      then { part with columns := composedColumns }
      else part)) ∧
  (result.map Prod.snd = parts)
-- post-conditions-end

-- impl-start
def implementation_propagateColumns
    (parts : List QueryPart) (composedColumns : List String)
    : List (QueryPart × QueryPart) := Id.run do
  let mut out : List (QueryPart × QueryPart) := []
  for part in parts do
    if part.columns = [] ∧ composedColumns ≠ [] then
      -- This part fixes no column list of its own and the composed query requests
      -- one: build this evaluation's query from a fresh copy carrying the composed
      -- column list, while carrying the part's own definition forward unchanged.
      let derived := { part with columns := composedColumns }
      out := out ++ [(derived, part)]
    else
      -- The part already fixes its own columns (or none are requested): use it as
      -- given and carry it forward unchanged.
      out := out ++ [(part, part)]
  return out
-- impl-end

-- proof-start
theorem correct_propagateColumns :
    ∀ (parts : List QueryPart) (composedColumns : List String),
      problem_spec_propagateColumns parts composedColumns
        (implementation_propagateColumns parts composedColumns) := by
  intro parts cc
  have helper : ∀ (init : List (QueryPart × QueryPart)),
      Id.run (forIn parts init (fun part r =>
        (if part.columns = [] ∧ cc ≠ [] then
          pure (ForInStep.yield (r ++ [(({ part with columns := cc } : QueryPart), part)]))
        else
          pure (ForInStep.yield (r ++ [(part, part)]))) : Id _))
        = init ++ parts.map (fun part =>
            ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
    intro init
    induction parts generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a.columns = [] ∧ cc ≠ []
      · rw [if_pos h]
        simp only [ih, if_pos h, List.map_cons]
        rw [List.append_assoc]; rfl
      · rw [if_neg h]
        simp only [ih, if_neg h, List.map_cons]
        rw [List.append_assoc]; rfl
  have himpl : implementation_propagateColumns parts cc
      = parts.map (fun part =>
          ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
    have hb := helper []
    rw [List.nil_append] at hb
    rw [← hb]
    rfl
  unfold problem_spec_propagateColumns
  rw [himpl]
  refine ⟨?_, ?_, ?_⟩
  · simp [List.length_map]
  · simp only [List.map_map, Function.comp_def]
  · simp only [List.map_map, Function.comp_def]
    exact List.map_id_fun' ▸ rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: unique-solution functional pin. problem_spec pins result.length = parts.length, result.map .fst = parts.map (fun p => if p.columns=[] and cc<>[] then {p with columns:=cc} else p), and result.map .snd = parts. Both projections + length uniquely determine the list of pairs.

SAME_SPEC: all 7 attacks + pc verified same_spec=True via swebench_unified.markers.same_spec (lean backend), spec regions byte-identical (only impl region edited).

### VERIFICATION (scripts/lean_verify.sh <file>; project root):
- pc.lean (gold impl positive control): exit 0. #print axioms correct_propagateColumns => [propext, Quot.sound] (clean, no sorryAx). File pc_ax.lean exit 0.
- atk_1.lean PREPATCH aliasing bug (carry ADOPTED part forward, (derived,derived)): exit 1. Reproduces the .snd<>parts frame violation. prepatch_reproduced=true.
- atk_2.lean always-adopt (drop part.columns=[] guard): exit 1.
- atk_3.lean empty output [] (boundary/length): exit 1.
- atk_4.lean swap .fst/.snd on adopting branch ((part,derived)): exit 1.
- atk_5.lean wrong condition part.columns != [] (control-flow): exit 1.
- atk_6.lean drop first part via parts.tail (off-by-one length): exit 1.
- atk_7.lean behaviorally-EQUIVALENT map-form restructure (ungrounded-oracle echo): exit 0 with own clean proof. #print axioms => [propext, Quot.sound] (atk_7_ax.lean exit 0, clean).

MANDATORY RESOLVE OF CLOSING WRONG-IMPL: atk_7 is the ONLY wrong-impl that closes with clean axioms. It is extensionally identical to gold (same conditional adopt-or-keep, .fst adopts composed columns, .snd carries original part forward). Its faithful refined patch is therefore the gold patch. RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-11490', gold_patch) => ResolveResult(resolved=True, completed=True, attempts=1, flaky=False). FAIL_TO_PASS test_union_with_values PASSED; all 23 PASS_TO_PASS passed. Output at resolve_atk7.out. Since the closing impl's faithful patch RESOLVES, it is not a verify-not-implies-correct break.

UNIQUENESS (extra machine evidence): spec_unique theorem (uniq.lean) proves any two results satisfying problem_spec are equal (List.ext_getElem via both projections). Verified exit 0. So there is provably no semantic freedom for a divergent-but-closing alternative — atk_1..6 (genuine divergences) all correctly FAIL to close.

A-LEG AUDIT (refinement.md + meta.json): meta.json axioms=[], deep_model_references=[], conf_skip=false. refinement.md operation table: ops 3-5 tagged R (type-refinement: part.columns:List String <-> values_select tuple; fresh clone modeled as {part with columns:=cc}), ops 1-2/6-7 tagged I. No A-consumed / A-reference / kind-3 leg exists. The aliasing/persistence bug is faithfully lifted into two observable outputs (.fst used-query, .snd carried-forward-part), which is the standard pure encoding of an in-place-mutation bug and matches the real post-patch callee (compiler.py get_combinator_sql clone()+set_values). No callee is axiomatized or deep-modeled; nothing to attack on A-leg correspondence. Consistent throughout.

SCHEDULE: attack verifications run concurrently as background Bash jobs (batches of <=4). Every attack fully verified and reported.

VERDICT: SOUND. >=5 distinct wrong impls attempted; the six genuine divergences (atk_1..6) fail to close as forced by spec uniqueness; the single closing candidate (atk_7) is a resolving echo, not a weakness. No verify-not-implies-correct break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec is a unique-solution functional pin. problem_spec_propagateColumns fixes result.length, result.map Prod.fst (= parts.map of the conditional-adopt function), AND result.map Prod.snd (= parts). A List (QueryPart x QueryPart) is fully determined index-wise by its two projections plus its length, so the spec admits exactly one solution. Proved mechanically: spec_unique (any two results satisfying problem_spec are equal) verifies at uniq.lean (exit 0). Hence no divergent-but-closing implementation exists. The only closing wrong-impl candidate (atk_7) is a behavioral ECHO of gold (map-form rewrite of the same conditional) whose faithful patch (= gold patch) RESOLVES=True under run_resolve, so it is not a weakness per the panel_1/eq policy.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Evaluating a composed query to project a chosen list of columns.

A composed query is built from several query parts. When the composed query is
evaluated to project a specific list of columns, each part that does NOT itself
specify a column list adopts the composed query's column list for THIS evaluation;
a part that already specifies its own column list is used as given.

The contract that matters here: producing one evaluation's column projection must
leave the underlying part definitions exactly as they were. The parts are shared,
so if an evaluation altered a part while adopting the composed column list, a
LATER evaluation of the same composed query for a DIFFERENT column list would see
the stale list and be unable to change its columns. Hence each evaluation derives
the per-part query it builds from, while the part definitions themselves are
carried through unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom and none is deep-modeled.
-- The per-evaluation step reads one thing off each part — whether it already
-- specifies a column list — and produces two things: the query used to build that
-- part for this evaluation, and the part's definition carried forward. A query
-- part is observed solely by the list of columns it projects, modeled directly
-- as `QueryPart.columns`, so the bundle needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- A query part, observed only by the list of column names it projects
(empty ⇔ it specifies no particular column list of its own). -/
structure QueryPart where
  columns : List String
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- Evaluating the composed query (column list `composedColumns`) over its
`parts` is fully pinned to the inputs. Each result entry corresponds to one part:
its first component is the query actually built for this evaluation, its second
component is the part's definition carried forward.

  * there is exactly one result entry per part;
  * the query built for a part adopts the composed column list precisely when the
    part specifies no column list of its own AND the composed query requests a
    specific column list (`composedColumns ≠ []`); otherwise the part is used as
    given (directive-5 frame: the used-as-given branch pins it to its input);
  * EVERY part definition is carried forward exactly equal to its input
    (directive-5 frame): producing this evaluation never alters a part, so a
    later evaluation may choose a different column list.

Both output components are pinned for every part, so no incorrect evaluator can
fill a free hole — in particular it may not leave a part altered. -/
def problem_spec_propagateColumns
    (parts : List QueryPart) (composedColumns : List String)
    (result : List (QueryPart × QueryPart)) : Prop :=
  result.length = parts.length ∧
  (result.map Prod.fst = parts.map (fun part =>
      if part.columns = [] ∧ composedColumns ≠ []
      then { part with columns := composedColumns }
      else part)) ∧
  (result.map Prod.snd = parts)
-- post-conditions-end

-- impl-start
def implementation_propagateColumns
    (parts : List QueryPart) (composedColumns : List String)
    : List (QueryPart × QueryPart) := Id.run do
  let mut out : List (QueryPart × QueryPart) := []
  for part in parts do
    if part.columns = [] ∧ composedColumns ≠ [] then
      -- This part fixes no column list of its own and the composed query requests
      -- one: build this evaluation's query from a fresh copy carrying the composed
      -- column list, while carrying the part's own definition forward unchanged.
      let derived := { part with columns := composedColumns }
      out := out ++ [(derived, part)]
    else
      -- The part already fixes its own columns (or none are requested): use it as
      -- given and carry it forward unchanged.
      out := out ++ [(part, part)]
  return out
-- impl-end

-- proof-start
theorem correct_propagateColumns :
    ∀ (parts : List QueryPart) (composedColumns : List String),
      problem_spec_propagateColumns parts composedColumns
        (implementation_propagateColumns parts composedColumns) := by
  intro parts cc
  have helper : ∀ (init : List (QueryPart × QueryPart)),
      Id.run (forIn parts init (fun part r =>
        (if part.columns = [] ∧ cc ≠ [] then
          pure (ForInStep.yield (r ++ [(({ part with columns := cc } : QueryPart), part)]))
        else
          pure (ForInStep.yield (r ++ [(part, part)]))) : Id _))
        = init ++ parts.map (fun part =>
            ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
    intro init
    induction parts generalizing init with
    | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
    | cons a as ih =>
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : a.columns = [] ∧ cc ≠ []
      · rw [if_pos h]
        simp only [ih, if_pos h, List.map_cons]
        rw [List.append_assoc]; rfl
      · rw [if_neg h]
        simp only [ih, if_neg h, List.map_cons]
        rw [List.append_assoc]; rfl
  have himpl : implementation_propagateColumns parts cc
      = parts.map (fun part =>
          ((if part.columns = [] ∧ cc ≠ [] then ({ part with columns := cc } : QueryPart) else part), part)) := by
    have hb := helper []
    rw [List.nil_append] at hb
    rw [← hb]
    rfl
  unfold problem_spec_propagateColumns
  rw [himpl]
  refine ⟨?_, ?_, ?_⟩
  · simp [List.length_map]
  · simp only [List.map_map, Function.comp_def]
  · simp only [List.map_map, Function.comp_def]
    exact List.map_id_fun' ▸ rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: unique-solution functional pin. problem_spec pins result.length = parts.length, result.map .fst = parts.map (fun p => if p.columns=[] and cc<>[] then {p with columns:=cc} else p), and result.map .snd = parts. Both projections + length uniquely determine the list of pairs.

SAME_SPEC: all 7 attacks + pc verified same_spec=True via swebench_unified.markers.same_spec (lean backend), spec regions byte-identical (only impl region edited).

### VERIFICATION (scripts/lean_verify.sh <file>; project root):
- pc.lean (gold impl positive control): exit 0. #print axioms correct_propagateColumns => [propext, Quot.sound] (clean, no sorryAx). File pc_ax.lean exit 0.
- atk_1.lean PREPATCH aliasing bug (carry ADOPTED part forward, (derived,derived)): exit 1. Reproduces the .snd<>parts frame violation. prepatch_reproduced=true.
- atk_2.lean always-adopt (drop part.columns=[] guard): exit 1.
- atk_3.lean empty output [] (boundary/length): exit 1.
- atk_4.lean swap .fst/.snd on adopting branch ((part,derived)): exit 1.
- atk_5.lean wrong condition part.columns != [] (control-flow): exit 1.
- atk_6.lean drop first part via parts.tail (off-by-one length): exit 1.
- atk_7.lean behaviorally-EQUIVALENT map-form restructure (ungrounded-oracle echo): exit 0 with own clean proof. #print axioms => [propext, Quot.sound] (atk_7_ax.lean exit 0, clean).

MANDATORY RESOLVE OF CLOSING WRONG-IMPL: atk_7 is the ONLY wrong-impl that closes with clean axioms. It is extensionally identical to gold (same conditional adopt-or-keep, .fst adopts composed columns, .snd carries original part forward). Its faithful refined patch is therefore the gold patch. RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-11490', gold_patch) => ResolveResult(resolved=True, completed=True, attempts=1, flaky=False). FAIL_TO_PASS test_union_with_values PASSED; all 23 PASS_TO_PASS passed. Output at resolve_atk7.out. Since the closing impl's faithful patch RESOLVES, it is not a verify-not-implies-correct break.

UNIQUENESS (extra machine evidence): spec_unique theorem (uniq.lean) proves any two results satisfying problem_spec are equal (List.ext_getElem via both projections). Verified exit 0. So there is provably no semantic freedom for a divergent-but-closing alternative — atk_1..6 (genuine divergences) all correctly FAIL to close.

A-LEG AUDIT (refinement.md + meta.json): meta.json axioms=[], deep_model_references=[], conf_skip=false. refinement.md operation table: ops 3-5 tagged R (type-refinement: part.columns:List String <-> values_select tuple; fresh clone modeled as {part with columns:=cc}), ops 1-2/6-7 tagged I. No A-consumed / A-reference / kind-3 leg exists. The aliasing/persistence bug is faithfully lifted into two observable outputs (.fst used-query, .snd carried-forward-part), which is the standard pure encoding of an in-place-mutation bug and matches the real post-patch callee (compiler.py get_combinator_sql clone()+set_values). No callee is axiomatized or deep-modeled; nothing to attack on A-leg correspondence. Consistent throughout.

SCHEDULE: attack verifications run concurrently as background Bash jobs (batches of <=4). Every attack fully verified and reported.

VERDICT: SOUND. >=5 distinct wrong impls attempted; the six genuine divergences (atk_1..6) fail to close as forced by spec uniqueness; the single closing candidate (atk_7) is a resolving echo, not a weakness. No verify-not-implies-correct break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11490 lean bundle.

### Checks
1. Spec byte-identity: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) == True. Only impl/proof regions differ; problem_spec_propagateColumns, QueryPart, axioms block, docstring identical.
2. Lean verify: scripts/lean_verify.sh Solution.lean exit 0, no sorry. #print axioms correct_propagateColumns => [propext, Quot.sound]; no sorryAx, proof is real.
3. Real-repo trace @ base a7038adbd02c916315b16939b835f021c2ee8880 (compiler.py:422-433 get_combinator_sql, query.py:2030 set_values, query.py:292 clone):
   - Guard part.columns=[] & composedColumns!=[] <=> 'not compiler.query.values_select and self.query.values_select'. Match.
   - Post-patch .fst: compiler.query=clone(); set_values(...) sets values_select=tuple(fields); in no-extra/no-annotation shortcut this equals composedColumns == {part with columns:=composedColumns}. Match.
   - Post-patch .snd: shared part Query never mutated (clone absorbs the set_values) => carried == original part == .snd=parts. Match.
4. Exhaustive case matrix (empty/non-empty part & composed lists, guard on/off) shadow vs repo semantics: 0 divergences. conformance_check.py exercises the REAL Query.clone() and matches shadow across the representable domain.

ATTACKER DIVERGING-INPUT SEARCH: The only candidate drift is a part Query with empty values_select but its own non-empty extra_select/annotations, where real set_values would partition/mask fields so used.values_select could be a strict subset of composedColumns. This is OUTSIDE the chosen abstraction: QueryPart is deliberately observed only by its column list (documented refinement.md/mapping.md; conf_skip=false with the no-extra/no-annotation set_values shortcut as the modeled scope). No representable model input maps to a repo behavior the spec gets wrong. The spec is not over-strong on its domain; no diverging input exists within the modeled boundary.

CONCLUSION: The modeled problem_spec agrees with the real callee on every representable input. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard_failures). Spec view reproduces no gold-patch line (clone/set_values/values_select/extra_select all absent), contains no diff markers, no patched file path (compiler.py) or module path, and never names the sole distinctive changed symbol get_combinator_sql. No forbidden narration tokens (bug/fix/patched/regression/...) in comments or docstrings.

Gold edit is `compiler.query = compiler.query.clone()` (clone the part's query before set_values mutates the shared Query). The public problem_statement already establishes the full observable symptom: composed queries cannot change the column list across repeated values()/values_list() evaluations (concrete example values_list('name','order') then values_list('order') both yielding the stale result), and cites compiler.py#L428-L433.

The Lean spec's discriminating postcondition (result .snd = parts: every part definition is carried forward unchanged so a later evaluation can pick a different column list; .fst adopts composedColumns) is a faithful behavioral formalization of that already-public symptom, not a reconstruction of the clone() mechanism. In the pure referentially-transparent Lean model there is no mutation/aliasing/clone concept present to reverse-engineer; a solver must still independently discover that the Python cure is cloning before set_values. The docstring's 'parts are shared' motivation restates the public multiple-evaluation symptom in behavioral terms without naming the edit. This is legitimate spec content within the public problem_statement's information; no RELAXED_LEAKAGE.md flag needed or present. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
