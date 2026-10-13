# P2 adversarial audit — django__django-11734

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,9 +70,9 @@
     (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do
   let mut newRhs : FilterRHS := rhs
   match rhs with
-  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
-  | .colRef name       => newRhs := .outerRef 1 name
-  | .value _           => pure ()
+  | .outerRef _ name => newRhs := .outerRef 1 name
+  | .colRef name     => newRhs := .outerRef 1 name
+  | .value _         => pure ()
   return (lhs, newRhs)
 -- impl-end
 
@@ -83,6 +83,6 @@
         (implementation_relocateFilterIntoSubquery lhs rhs) := by
   intro lhs rhs
   cases rhs <;>
-    simp [problem_spec_relocateFilterIntoSubquery,
+    simp_all [problem_spec_relocateFilterIntoSubquery,
           implementation_relocateFilterIntoSubquery, reanchor]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
   let mut newRhs : FilterRHS := rhs
   match rhs with
   | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
-  | .colRef name       => newRhs := .outerRef 1 name
+  | .colRef name       => newRhs := .outerRef 1 (name ++ "_x")
   | .value _           => pure ()
   return (lhs, newRhs)
 -- impl-end
@@ -83,6 +83,6 @@
         (implementation_relocateFilterIntoSubquery lhs rhs) := by
   intro lhs rhs
   cases rhs <;>
-    simp [problem_spec_relocateFilterIntoSubquery,
+    simp_all [problem_spec_relocateFilterIntoSubquery,
           implementation_relocateFilterIntoSubquery, reanchor]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -73,7 +73,7 @@
   | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
   | .colRef name       => newRhs := .outerRef 1 name
   | .value _           => pure ()
-  return (lhs, newRhs)
+  return ("", newRhs)
 -- impl-end
 
 -- proof-start
@@ -83,6 +83,6 @@
         (implementation_relocateFilterIntoSubquery lhs rhs) := by
   intro lhs rhs
   cases rhs <;>
-    simp [problem_spec_relocateFilterIntoSubquery,
+    simp_all [problem_spec_relocateFilterIntoSubquery,
           implementation_relocateFilterIntoSubquery, reanchor]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
   match rhs with
   | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
   | .colRef name       => newRhs := .outerRef 1 name
-  | .value _           => pure ()
+  | .value v           => newRhs := .value (v + 1)
   return (lhs, newRhs)
 -- impl-end
 
@@ -83,6 +83,6 @@
         (implementation_relocateFilterIntoSubquery lhs rhs) := by
   intro lhs rhs
   cases rhs <;>
-    simp [problem_spec_relocateFilterIntoSubquery,
+    simp_all [problem_spec_relocateFilterIntoSubquery,
           implementation_relocateFilterIntoSubquery, reanchor]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
     (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do
   let mut newRhs : FilterRHS := rhs
   match rhs with
-  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
+  | .outerRef lvl name => newRhs := .outerRef (lvl + 2) name
   | .colRef name       => newRhs := .outerRef 1 name
   | .value _           => pure ()
   return (lhs, newRhs)
@@ -83,6 +83,6 @@
         (implementation_relocateFilterIntoSubquery lhs rhs) := by
   intro lhs rhs
   cases rhs <;>
-    simp [problem_spec_relocateFilterIntoSubquery,
+    simp_all [problem_spec_relocateFilterIntoSubquery,
           implementation_relocateFilterIntoSubquery, reanchor]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
   let mut newRhs : FilterRHS := rhs
   match rhs with
   | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
-  | .colRef name       => newRhs := .outerRef 1 name
+  | .colRef name       => newRhs := .colRef name
   | .value _           => pure ()
   return (lhs, newRhs)
 -- impl-end
@@ -83,6 +83,6 @@
         (implementation_relocateFilterIntoSubquery lhs rhs) := by
   intro lhs rhs
   cases rhs <;>
-    simp [problem_spec_relocateFilterIntoSubquery,
+    simp_all [problem_spec_relocateFilterIntoSubquery,
           implementation_relocateFilterIntoSubquery, reanchor]
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,13 +67,8 @@
 
 -- impl-start
 def implementation_relocateFilterIntoSubquery
-    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do
-  let mut newRhs : FilterRHS := rhs
-  match rhs with
-  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
-  | .colRef name       => newRhs := .outerRef 1 name
-  | .value _           => pure ()
-  return (lhs, newRhs)
+    (lhs : String) (rhs : FilterRHS) : String × FilterRHS :=
+  (lhs, reanchor rhs)
 -- impl-end
 
 -- proof-start
@@ -82,7 +77,6 @@
       problem_spec_relocateFilterIntoSubquery lhs rhs
         (implementation_relocateFilterIntoSubquery lhs rhs) := by
   intro lhs rhs
-  cases rhs <;>
-    simp [problem_spec_relocateFilterIntoSubquery,
-          implementation_relocateFilterIntoSubquery, reanchor]
+  simp [problem_spec_relocateFilterIntoSubquery,
+        implementation_relocateFilterIntoSubquery]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Relocating a filter condition into a nested subquery.

When a negated relational filter over a one-to-many relation has to be evaluated
through an auxiliary nested subquery, the right-hand side of the filter
condition must be carried into the inner query while preserving WHICH query each
reference resolves against.

A right-hand side is one of three shapes:
  * a direct literal value (resolves to itself);
  * a same-query column reference (a name pointing at a column of the query it
    sits in);
  * an outer-query reference, carrying a nesting level that says how many query
    boundaries outward it must reach to find the column it names.

Because the relocation pushes the condition one query boundary deeper, the
reference must be re-anchored:
  * a direct literal is unchanged;
  * a same-query column reference becomes an outer-query reference reaching out
    one level (so it still names the column of the query the condition came
    from);
  * an existing outer-query reference must reach out one ADDITIONAL level, since
    a new query boundary now sits between it and its target.

The left-hand side of the condition is untouched by the relocation. This is
stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the relocation is modeled
-- deeply with concrete operations (a three-way shape dispatch and a nesting-level
-- adjustment).
-- axioms-end

-- pure-start
/-- The right-hand side of a relocated filter condition. `outerRef level name`
names a column `name` reachable by crossing `level` query boundaries outward
(`level ≥ 1`); `colRef name` names a column of the current query; `value v` is a
direct literal. -/
inductive FilterRHS where
  | value (v : Int)
  | colRef (name : String)
  | outerRef (level : Nat) (name : String)
deriving DecidableEq, Repr

/-- Re-anchor a right-hand side for evaluation one query boundary deeper: a
literal is unchanged, a current-query column reference becomes an outer-query
reference reaching out one level, and an existing outer-query reference must
reach out one further level. -/
def reanchor : FilterRHS → FilterRHS
  | .value v          => .value v
  | .colRef name      => .outerRef 1 name
  | .outerRef lvl name => .outerRef (lvl + 1) name
-- pure-end

-- post-conditions-start
/-- Relocating the filter condition `(lhs, rhs)` into the nested subquery leaves
the left-hand side unchanged and re-anchors the right-hand side. -/
def problem_spec_relocateFilterIntoSubquery
    (lhs : String) (rhs : FilterRHS) (result : String × FilterRHS) : Prop :=
  result.1 = lhs ∧ result.2 = reanchor rhs
-- post-conditions-end

-- impl-start
def implementation_relocateFilterIntoSubquery
    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do
  let mut newRhs : FilterRHS := rhs
  match rhs with
  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
  | .colRef name       => newRhs := .outerRef 1 name
  | .value _           => pure ()
  return (lhs, newRhs)
-- impl-end

-- proof-start
theorem correct_relocateFilterIntoSubquery :
    ∀ (lhs : String) (rhs : FilterRHS),
      problem_spec_relocateFilterIntoSubquery lhs rhs
        (implementation_relocateFilterIntoSubquery lhs rhs) := by
  intro lhs rhs
  cases rhs <;>
    simp [problem_spec_relocateFilterIntoSubquery,
          implementation_relocateFilterIntoSubquery, reanchor]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-11734 (Lean). SPEC SHAPE: postcondition problem_spec = (result.1 = lhs ∧ result.2 = reanchor rhs) is a TOTAL FUNCTIONAL PIN — output fully determined for every (lhs, rhs) input. Any impl whose correct_ proof closes is extensionally identical to (lhs, reanchor rhs), i.e. the gold behavior; no divergent-but-closing impl can exist.

same_spec: all 7 attacks + positive control = True (swebench_unified.markers.same_spec, lean backend). Note _lean_spec_view collapses BOTH impl AND proof regions to placeholders, so attacks freely rewrote impl+proof while keeping docstring/axioms/pure/post-conditions/theorem-signature byte-identical.

All verifications run via `bash scripts/lean_verify.sh <f>`, concurrently in batches ≤4.

POSITIVE CONTROL: pos_control.lean (= gold impl) → exit 0; #print axioms correct_relocateFilterIntoSubquery → [propext, Quot.sound] (clean, no sorryAx).

PREPATCH: Solution_prepatch.lean (outerRef arm collapses level to 1) → exit 1, unsolved goals at proof (line 92) — bug reproduced (prepatch_reproduced=true).

ATTACKS (6 distinct divergent wrong impls, all exit 1 = proof does NOT close, genuine 'unsolved goals' errors, NOT scaffold/parse errors — confirmed in .out files):
- atk_1 partial/prepatch: .outerRef _ name => outerRef 1 name (drops carried level) → exit 1, unsolved goals line 83.
- atk_2 boundary/name-mangle: .colRef name => outerRef 1 (name ++ "_x") → exit 1, unsolved goals.
- atk_3 control-flow-effect: returns ("", newRhs) instead of (lhs, newRhs) → exit 1, unsolved goals.
- atk_4 value-arm wrong: .value v => value (v+1) → exit 1, unsolved goals.
- atk_5 off-by-one overshoot: .outerRef lvl name => outerRef (lvl+2) name → exit 1, unsolved goals.
- atk_6 partial-domain: .colRef name => colRef name (identity, not outerRef) → exit 1, unsolved goals.

ECHO (ungrounded-oracle) atk_7: implementation = (lhs, reanchor rhs), extensionally IDENTICAL to gold on entire domain → exit 0; #print axioms → [propext] (CLEAN, no sorryAx). Per protocol step 2, materialized its faithful refined patch (= gold patch verbatim, since impl is extensionally gold) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-11734', gold_patch) → ResolveResult(resolved=True, completed=True). FAIL_TO_PASS test_subquery_exclude_outerref (queries.tests.ExcludeTests) SUCCESS; all ~300 PASS_TO_PASS SUCCESS; 0 failures. The only clean-axiom-closing impl RESOLVES ⇒ verify⇒correct holds; NOT broken.

A-LEG AUDIT (refinement.md): axioms region is EMPTY (comment only; grep found no `axiom `/sorry/admit in Solution.lean). refinement.md tags every leg R or I; A-consumed = none, A-reference = none. axiom_check.py is a legitimate skip stub (no consumed callee axiom, no deep-model A-reference). Therefore no A-leg / deep-model correspondence attack surface exists — the re-anchoring is modeled deeply with concrete Lean ops (three-way FilterRHS dispatch + level+1). R/I legs are the province of G-CONF (out of scope for G-EQ). No kind-3 legs.

CONCLUSION: total functional pin admits no divergent-but-closing implementation; the single closing impl (echo=gold) has a faithful patch that RESOLVES under the official Docker oracle. ≥6 distinct wrong impls attempted, all rejected by the frozen spec. No falsification found. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Relocating a filter condition into a nested subquery.

When a negated relational filter over a one-to-many relation has to be evaluated
through an auxiliary nested subquery, the right-hand side of the filter
condition must be carried into the inner query while preserving WHICH query each
reference resolves against.

A right-hand side is one of three shapes:
  * a direct literal value (resolves to itself);
  * a same-query column reference (a name pointing at a column of the query it
    sits in);
  * an outer-query reference, carrying a nesting level that says how many query
    boundaries outward it must reach to find the column it names.

Because the relocation pushes the condition one query boundary deeper, the
reference must be re-anchored:
  * a direct literal is unchanged;
  * a same-query column reference becomes an outer-query reference reaching out
    one level (so it still names the column of the query the condition came
    from);
  * an existing outer-query reference must reach out one ADDITIONAL level, since
    a new query boundary now sits between it and its target.

The left-hand side of the condition is untouched by the relocation. This is
stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the relocation is modeled
-- deeply with concrete operations (a three-way shape dispatch and a nesting-level
-- adjustment).
-- axioms-end

-- pure-start
/-- The right-hand side of a relocated filter condition. `outerRef level name`
names a column `name` reachable by crossing `level` query boundaries outward
(`level ≥ 1`); `colRef name` names a column of the current query; `value v` is a
direct literal. -/
inductive FilterRHS where
  | value (v : Int)
  | colRef (name : String)
  | outerRef (level : Nat) (name : String)
deriving DecidableEq, Repr

/-- Re-anchor a right-hand side for evaluation one query boundary deeper: a
literal is unchanged, a current-query column reference becomes an outer-query
reference reaching out one level, and an existing outer-query reference must
reach out one further level. -/
def reanchor : FilterRHS → FilterRHS
  | .value v          => .value v
  | .colRef name      => .outerRef 1 name
  | .outerRef lvl name => .outerRef (lvl + 1) name
-- pure-end

-- post-conditions-start
/-- Relocating the filter condition `(lhs, rhs)` into the nested subquery leaves
the left-hand side unchanged and re-anchors the right-hand side. -/
def problem_spec_relocateFilterIntoSubquery
    (lhs : String) (rhs : FilterRHS) (result : String × FilterRHS) : Prop :=
  result.1 = lhs ∧ result.2 = reanchor rhs
-- post-conditions-end

-- impl-start
def implementation_relocateFilterIntoSubquery
    (lhs : String) (rhs : FilterRHS) : String × FilterRHS := Id.run do
  let mut newRhs : FilterRHS := rhs
  match rhs with
  | .outerRef lvl name => newRhs := .outerRef (lvl + 1) name
  | .colRef name       => newRhs := .outerRef 1 name
  | .value _           => pure ()
  return (lhs, newRhs)
-- impl-end

-- proof-start
theorem correct_relocateFilterIntoSubquery :
    ∀ (lhs : String) (rhs : FilterRHS),
      problem_spec_relocateFilterIntoSubquery lhs rhs
        (implementation_relocateFilterIntoSubquery lhs rhs) := by
  intro lhs rhs
  cases rhs <;>
    simp [problem_spec_relocateFilterIntoSubquery,
          implementation_relocateFilterIntoSubquery, reanchor]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial audit for django__django-11734 (Lean). SPEC SHAPE: postcondition problem_spec = (result.1 = lhs ∧ result.2 = reanchor rhs) is a TOTAL FUNCTIONAL PIN — output fully determined for every (lhs, rhs) input. Any impl whose correct_ proof closes is extensionally identical to (lhs, reanchor rhs), i.e. the gold behavior; no divergent-but-closing impl can exist.

same_spec: all 7 attacks + positive control = True (swebench_unified.markers.same_spec, lean backend). Note _lean_spec_view collapses BOTH impl AND proof regions to placeholders, so attacks freely rewrote impl+proof while keeping docstring/axioms/pure/post-conditions/theorem-signature byte-identical.

All verifications run via `bash scripts/lean_verify.sh <f>`, concurrently in batches ≤4.

POSITIVE CONTROL: pos_control.lean (= gold impl) → exit 0; #print axioms correct_relocateFilterIntoSubquery → [propext, Quot.sound] (clean, no sorryAx).

PREPATCH: Solution_prepatch.lean (outerRef arm collapses level to 1) → exit 1, unsolved goals at proof (line 92) — bug reproduced (prepatch_reproduced=true).

ATTACKS (6 distinct divergent wrong impls, all exit 1 = proof does NOT close, genuine 'unsolved goals' errors, NOT scaffold/parse errors — confirmed in .out files):
- atk_1 partial/prepatch: .outerRef _ name => outerRef 1 name (drops carried level) → exit 1, unsolved goals line 83.
- atk_2 boundary/name-mangle: .colRef name => outerRef 1 (name ++ "_x") → exit 1, unsolved goals.
- atk_3 control-flow-effect: returns ("", newRhs) instead of (lhs, newRhs) → exit 1, unsolved goals.
- atk_4 value-arm wrong: .value v => value (v+1) → exit 1, unsolved goals.
- atk_5 off-by-one overshoot: .outerRef lvl name => outerRef (lvl+2) name → exit 1, unsolved goals.
- atk_6 partial-domain: .colRef name => colRef name (identity, not outerRef) → exit 1, unsolved goals.

ECHO (ungrounded-oracle) atk_7: implementation = (lhs, reanchor rhs), extensionally IDENTICAL to gold on entire domain → exit 0; #print axioms → [propext] (CLEAN, no sorryAx). Per protocol step 2, materialized its faithful refined patch (= gold patch verbatim, since impl is extensionally gold) and RAN it through the official harness: swebench_unified.harness.run_resolve('django__django-11734', gold_patch) → ResolveResult(resolved=True, completed=True). FAIL_TO_PASS test_subquery_exclude_outerref (queries.tests.ExcludeTests) SUCCESS; all ~300 PASS_TO_PASS SUCCESS; 0 failures. The only clean-axiom-closing impl RESOLVES ⇒ verify⇒correct holds; NOT broken.

A-LEG AUDIT (refinement.md): axioms region is EMPTY (comment only; grep found no `axiom `/sorry/admit in Solution.lean). refinement.md tags every leg R or I; A-consumed = none, A-reference = none. axiom_check.py is a legitimate skip stub (no consumed callee axiom, no deep-model A-reference). Therefore no A-leg / deep-model correspondence attack surface exists — the re-anchoring is modeled deeply with concrete Lean ops (three-way FilterRHS dispatch + level+1). R/I legs are the province of G-CONF (out of scope for G-EQ). No kind-3 legs.

CONCLUSION: total functional pin admits no divergent-but-closing implementation; the single closing impl (echo=gold) has a faithful patch that RESOLVES under the official Docker oracle. ≥6 distinct wrong impls attempted, all rejected by the frozen spec. No falsification found. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacked the spec for faithfulness drift (spec-too-strong / disagreement with the real callee). Found none; spec is faithful.

Verification performed:
1. COMPILE + AXIOMS: scripts/lean_verify.sh on Solution.lean exits 0. `#print axioms correct_relocateFilterIntoSubquery` => [propext, Quot.sound] only. No sorryAx — proof is genuine.
2. SAME_SPEC: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean-backend) = True. Spec region (reanchor, problem_spec, docstrings) is byte-identical; prepatch differs only in impl/proof region, as required.
3. REAL CALLEE SEMANTICS (the /tmp worktree was empty, so I reconstructed base_commit behavior from Django 2.2 wheel with the real imported classes): confirmed `class OuterRef(F)` (issubclass True); `OuterRef(name).name == name`; each `OuterRef(ref)` wrap adds exactly one nesting level (verified up to depth 6); `F(name).name == name`. This matches the model's `FilterRHS.outerRef (level:Nat)` depth abstraction and the mapping.md bijection.
4. MODEL vs REAL PATCHED REWRITE: ran the full conformance logic (transliteration of reanchor vs the verbatim patched split_exclude head branch on genuine OuterRef/F objects) over the discrete shape matrix + 120,000 randomized draws (seed 20240625): 0 disagreements.
   - value v -> value v (real: not-F/OuterRef carried verbatim) ✓
   - colRef name (real F) -> outerRef 1 name (real F branch: OuterRef(name), depth 1) ✓
   - outerRef lvl name -> outerRef (lvl+1) name (real OuterRef branch: OuterRef(filter_rhs), +1 depth) ✓
   - lhs untouched in all cases ✓

The spec's `reanchor` is exactly the post-patch desired behavior; patch_equals_gold=true. reanchor is NOT stronger than what the real patched split_exclude head rewrite guarantees over the modeled RHS domain, and does not diverge on any input. The abstraction boundary (modeling only the re-anchoring head, treating the rest of split_exclude — Query construction, add_filter, trim_start — as orthogonal/unchanged) is documented in mapping.md/refinement.md and legitimate: the F2P observable (test_subquery_exclude_outerref) is precisely the RHS nesting-depth re-anchoring. No spec-too-strong drift; no diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigor checks: (1) same_spec(Solution, Solution_prepatch)=True — spec region (imports/docstring/axioms/pure `FilterRHS`+`reanchor`/post-conditions) is byte-identical; impl+proof are elided in the spec view. (2) lean_verify.sh Solution.lean → exit 0. (3) leakage.screen over the spec view PASSES (no hard failures). Patch-changed distinctive symbols = {as_sql, get_db_prep_value, get_prep_value, split_exclude}; NONE appear as spec-view identifiers or in comments/docstrings.

Semantic leakage analysis (beyond the lexical screen): The public problem_statement already discloses the full scenario — OuterRef in exclude()/~Q() 'uses wrong model', an exclude() over a to-many relation builds a nested subquery, and the OuterRef must resolve against the intended outer query rather than crash with 'reference to an outer query ... may only be used in a subquery'. The spec view restates the DESIRED CORRECT CONTRACT abstractly (literal unchanged; same-query column ref → level-1 outer ref; existing outer ref → one ADDITIONAL level) via an abstract FilterRHS type and `reanchor`. This is derivable from the public issue (a condition pushed one query boundary deeper ⇒ references re-anchor one level further out) and is the spec's legitimate, G-PANEL-1-required job.

Crucially it does NOT reveal the gold EDIT MECHANISM: no `split_exclude`, no `OuterRef`, no isinstance-branch structure, no `OuterRef(filter_rhs)` double-wrapping trick, and neither sibling hunk (related_lookups.py guard swap, dead AutoField.get_prep_value removal). No patched file/module path, no diff markers, no bug/fix narration in spec-view comments. The 'reach out one ADDITIONAL level' phrasing corresponds to hints_text detail (V0.id vs number.id) but is independently derivable from the public scenario and states behavior, not the edit. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.