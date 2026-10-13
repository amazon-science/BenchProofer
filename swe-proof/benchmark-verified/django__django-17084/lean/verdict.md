# P2 adversarial audit — django__django-17084

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_requiresSubqueryWrap pins result to an EXACT boolean equality (result = otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates) over the actual inputs, with an empty axioms region (G-AX is a genuine skip stub: no consumed axiom, no A-reference deep model). Because the postcondition is a total functional equality, any impl that is not extensionally equal to the gold disjunction makes correct_requiresSubqueryWrap a false Prop and cannot close. All 6 wrong impls failed to elaborate (exit 1). The only same-spec impl that verifies is the correct echo (atk_7), and its faithful patch = the gold patch, which RESOLVES. Hence no verified ∧ ¬resolved witness exists.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,13 +50,10 @@
 def implementation_requiresSubqueryWrap
     (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool := Id.run do
   let mut refsSubquery := false
-  let mut refsWindow := false
   for agg in aggregates do
     refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
-    refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
-  return otherConditions || refsSubquery || refsWindow
+  return otherConditions || refsSubquery
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresSubqueryWrap :
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,6 +49,8 @@
 -- impl-start
 def implementation_requiresSubqueryWrap
     (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool := Id.run do
+  if aggregates.isEmpty then
+    return false
   let mut refsSubquery := false
   let mut refsWindow := false
   for agg in aggregates do
@@ -56,7 +58,6 @@
     refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
   return otherConditions || refsSubquery || refsWindow
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresSubqueryWrap :
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,10 +53,9 @@
   let mut refsWindow := false
   for agg in aggregates do
     refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
-    refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
+    refsWindow   := refsWindow   || agg.refs.all (·.isWindowExpr)
   return otherConditions || refsSubquery || refsWindow
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresSubqueryWrap :
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,9 +54,9 @@
   for agg in aggregates do
     refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
     refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
+    return otherConditions || refsSubquery || refsWindow
   return otherConditions || refsSubquery || refsWindow
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresSubqueryWrap :
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,14 +49,11 @@
 -- impl-start
 def implementation_requiresSubqueryWrap
     (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool := Id.run do
-  let mut refsSubquery := false
   let mut refsWindow := false
   for agg in aggregates do
-    refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
     refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
-  return otherConditions || refsSubquery || refsWindow
+  return otherConditions || refsWindow
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresSubqueryWrap :
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,9 +54,8 @@
   for agg in aggregates do
     refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
     refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
-  return otherConditions || refsSubquery || refsWindow
+  return refsSubquery || refsWindow
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresSubqueryWrap :
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -48,15 +48,9 @@
 
 -- impl-start
 def implementation_requiresSubqueryWrap
-    (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool := Id.run do
-  let mut refsSubquery := false
-  let mut refsWindow := false
-  for agg in aggregates do
-    refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
-    refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
-  return otherConditions || refsSubquery || refsWindow
+    (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool :=
+  otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates
 -- impl-end
-
 
 -- proof-start
 theorem correct_requiresSubqueryWrap :
@@ -64,25 +58,5 @@
     problem_spec_requiresSubqueryWrap aggregates otherConditions
       (implementation_requiresSubqueryWrap aggregates otherConditions) := by
   intro aggregates otherConditions
-  simp only [problem_spec_requiresSubqueryWrap, implementation_requiresSubqueryWrap,
-    anyRefSubquery, anyRefWindow, Id.run, bind, pure, List.forIn_yield_eq_foldl]
-  have key : ∀ (l : List AggregateExpr) (b c : Bool),
-      ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
-          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).fst
-        = (b || l.any (fun a => a.refs.any fun x => x.isSubqueryExpr)))
-      ∧ ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
-          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).snd
-        = (c || l.any (fun a => a.refs.any fun x => x.isWindowExpr))) := by
-    intro l
-    induction l with
-    | nil => intro b c; exact ⟨by simp, by simp⟩
-    | cons hd tl ih =>
-      intro b c
-      simp only [List.foldl_cons, List.any_cons]
-      refine ⟨?_, ?_⟩
-      · rw [(ih _ _).1, Bool.or_assoc]
-      · rw [(ih _ _).2, Bool.or_assoc]
-  rw [(key aggregates false false).1, (key aggregates false false).2]
-  simp [Bool.or_assoc]
-
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The per-reference flag
-- lookups (whether a referenced annotation is itself computed in a wrapping
-- subquery, and whether it is a window/over-clause expression) are modeled
-- DEEPLY as boolean fields carried on each referenced annotation, rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A referenced annotation, reduced to the two boolean properties that the
wrapping decision inspects: whether it is itself produced by a wrapping
subquery, and whether it is a window/over-clause expression. -/
structure RefAnnotation where
  isSubqueryExpr : Bool
  isWindowExpr   : Bool

/-- One requested aggregate, reduced to the list of annotations it references. -/
structure AggregateExpr where
  refs : List RefAnnotation

/-- Some referenced annotation (across all requested aggregates) is itself
produced by a wrapping subquery. -/
def anyRefSubquery (aggs : List AggregateExpr) : Bool :=
  aggs.any (fun a => a.refs.any (·.isSubqueryExpr))

/-- Some referenced annotation (across all requested aggregates) is a
window/over-clause expression. -/
def anyRefWindow (aggs : List AggregateExpr) : Bool :=
  aggs.any (fun a => a.refs.any (·.isWindowExpr))
-- pure-end

-- post-conditions-start
/-- The aggregation must be evaluated inside a wrapping subquery exactly when at
least one of the following holds: one of the pre-existing structural conditions
(`otherConditions`); some referenced annotation is itself produced by a wrapping
subquery; or some referenced annotation is a window/over-clause expression. The
result is pinned to the full disjunction over the actual inputs, so every
contributing condition — including the unchanged ones folded into
`otherConditions` — is constrained. -/
def problem_spec_requiresSubqueryWrap
    (aggregates : List AggregateExpr) (otherConditions : Bool)
    (result : Bool) : Prop :=
  result = (otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates)
-- post-conditions-end

-- impl-start
def implementation_requiresSubqueryWrap
    (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool := Id.run do
  let mut refsSubquery := false
  let mut refsWindow := false
  for agg in aggregates do
    refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
    refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
  return otherConditions || refsSubquery || refsWindow
-- impl-end


-- proof-start
theorem correct_requiresSubqueryWrap :
    ∀ (aggregates : List AggregateExpr) (otherConditions : Bool),
    problem_spec_requiresSubqueryWrap aggregates otherConditions
      (implementation_requiresSubqueryWrap aggregates otherConditions) := by
  intro aggregates otherConditions
  simp only [problem_spec_requiresSubqueryWrap, implementation_requiresSubqueryWrap,
    anyRefSubquery, anyRefWindow, Id.run, bind, pure, List.forIn_yield_eq_foldl]
  have key : ∀ (l : List AggregateExpr) (b c : Bool),
      ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).fst
        = (b || l.any (fun a => a.refs.any fun x => x.isSubqueryExpr)))
      ∧ ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).snd
        = (c || l.any (fun a => a.refs.any fun x => x.isWindowExpr))) := by
    intro l
    induction l with
    | nil => intro b c; exact ⟨by simp, by simp⟩
    | cons hd tl ih =>
      intro b c
      simp only [List.foldl_cons, List.any_cons]
      refine ⟨?_, ?_⟩
      · rw [(ih _ _).1, Bool.or_assoc]
      · rw [(ih _ _).2, Bool.or_assoc]
  rw [(key aggregates false false).1, (key aggregates false false).2]
  simp [Bool.or_assoc]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTION (all runs; concurrent lean_verify jobs in batches of 4).

SPEC SHAPE: post-conditions pin `result = (otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates)` — a TIGHT functional equality, no existential/oracle slack. axioms region empty; axiom_check.py is a genuine skip stub (verified: no consumed axiom, no A-reference deep model — the two getattr reads are reproduced concretely as boolean fields isSubqueryExpr/isWindowExpr, R/I). This is the strongest spec shape: verify ⇒ extensional equality on ALL inputs ⇒ correct patch behavior.

SAME_SPEC: all 7 attacks return True (invariant prefix = everything through `-- impl-start` kept byte-identical). Non-vacuity confirmed: tampering the postcondition (drop anyRefWindow) → same_spec False; tampering the pure region (anyRefWindow .any→.all) → same_spec False. So same_spec locks axioms/pure/pre/post byte-for-byte.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH BUG (drops window flag; returns otherConditions||refsSubquery): same_spec True, EXIT 1 (rewrite failed to close) → prepatch reproduced (matches Solution_prepatch.lean impl; that file carries `sorry` as UNCLOSABLE).
- atk_2 PARTIAL-DOMAIN (empty aggregates → return false, ignoring otherConditions): same_spec True, EXIT 1.
- atk_3 BOUNDARY (.all instead of .any for window flag): same_spec True, EXIT 1.
- atk_4 CONTROL-FLOW-EFFECT (early `return` inside loop after first aggregate): same_spec True, EXIT 1.
- atk_5 DROP subquery flag (returns otherConditions||refsWindow): same_spec True, EXIT 1.
- atk_6 DROP otherConditions from final disjunction: same_spec True, EXIT 1.
- atk_7 UNGROUNDED-ORACLE ECHO (returns spec RHS verbatim `otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates`, proof `rfl`): same_spec True, EXIT 0 VERIFIES. #print axioms correct_requiresSubqueryWrap → 'does not depend on any axioms' (clean, no sorry/_prop).

POSITIVE CONTROL pos_gold.lean (gold impl): EXIT 0; #print axioms → [propext, Quot.sound] (standard Lean axioms only, no sorry/_prop) — clean.

MANDATORY RESOLVE OF VERIFYING ATTACK: atk_7 is the correct echo (extensionally identical to gold RHS). Its faithful refined patch is the gold get_aggregation patch (adds refs_window accumulator + disjunct). EXECUTED via swebench_unified.harness.run_resolve('django__django-17084', patch, run_id='sbu-audit-eq-uiu2iybo-atk7', timeout=1800): RESOLVED=True, COMPLETED=True, NOTE='resolved'. So the sole verifying same-spec impl RESOLVES — no verify⇏correct witness. Per the 2026-08-06 G-PANEL-1/G-EQ echo policy, a resolving echo of the gold is NOT a weakness.

REFINEMENT.MD AUDIT: 6 rows. Rows 1-2 I (accumulator inits). Row 3 R (dict-of-aggregates ↔ List AggregateExpr; only get_refs matters). Rows 4-5 R (the two getattr reads reproduced concretely as boolean fields — the changed op row 5 modeled deeply, NOT axiomatized). Row 6 R/I (pre-existing disjuncts collapsed into otherConditions R; appending ||refsWindow is the identical concrete op I). NO A-consumed and NO A-reference rows — consistent with empty axioms region and G-AX skip stub. No kind-3 (changed-inexpressible) leg. Correspondence to real callees holds: get_refs()→refs, subquery/contains_over_clause getattrs→isSubqueryExpr/isWindowExpr with defaults resolved into the booleans (mapping.md documents contains_over_clause default True). All legs R/I → mechanically G-CONF's domain (conformance_check.py runs a real fuzz, conf_skip=false), which is out of this A-leg-focused pass but present and non-stub.

VERDICT: SOUND. ≥5 distinct wrong impls (6 built + prepatch) all failed to close against a tight functional-equality spec; the only closing same-spec impl is a correct echo whose materialized faithful patch was EXECUTED through the official harness and RESOLVED.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_requiresSubqueryWrap pins result to an EXACT boolean equality (result = otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates) over the actual inputs, with an empty axioms region (G-AX is a genuine skip stub: no consumed axiom, no A-reference deep model). Because the postcondition is a total functional equality, any impl that is not extensionally equal to the gold disjunction makes correct_requiresSubqueryWrap a false Prop and cannot close. All 6 wrong impls failed to elaborate (exit 1). The only same-spec impl that verifies is the correct echo (atk_7), and its faithful patch = the gold patch, which RESOLVES. Hence no verified ∧ ¬resolved witness exists.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The per-reference flag
-- lookups (whether a referenced annotation is itself computed in a wrapping
-- subquery, and whether it is a window/over-clause expression) are modeled
-- DEEPLY as boolean fields carried on each referenced annotation, rather than
-- axiomatized. The proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A referenced annotation, reduced to the two boolean properties that the
wrapping decision inspects: whether it is itself produced by a wrapping
subquery, and whether it is a window/over-clause expression. -/
structure RefAnnotation where
  isSubqueryExpr : Bool
  isWindowExpr   : Bool

/-- One requested aggregate, reduced to the list of annotations it references. -/
structure AggregateExpr where
  refs : List RefAnnotation

/-- Some referenced annotation (across all requested aggregates) is itself
produced by a wrapping subquery. -/
def anyRefSubquery (aggs : List AggregateExpr) : Bool :=
  aggs.any (fun a => a.refs.any (·.isSubqueryExpr))

/-- Some referenced annotation (across all requested aggregates) is a
window/over-clause expression. -/
def anyRefWindow (aggs : List AggregateExpr) : Bool :=
  aggs.any (fun a => a.refs.any (·.isWindowExpr))
-- pure-end

-- post-conditions-start
/-- The aggregation must be evaluated inside a wrapping subquery exactly when at
least one of the following holds: one of the pre-existing structural conditions
(`otherConditions`); some referenced annotation is itself produced by a wrapping
subquery; or some referenced annotation is a window/over-clause expression. The
result is pinned to the full disjunction over the actual inputs, so every
contributing condition — including the unchanged ones folded into
`otherConditions` — is constrained. -/
def problem_spec_requiresSubqueryWrap
    (aggregates : List AggregateExpr) (otherConditions : Bool)
    (result : Bool) : Prop :=
  result = (otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates)
-- post-conditions-end

-- impl-start
def implementation_requiresSubqueryWrap
    (aggregates : List AggregateExpr) (otherConditions : Bool) : Bool := Id.run do
  let mut refsSubquery := false
  let mut refsWindow := false
  for agg in aggregates do
    refsSubquery := refsSubquery || agg.refs.any (·.isSubqueryExpr)
    refsWindow   := refsWindow   || agg.refs.any (·.isWindowExpr)
  return otherConditions || refsSubquery || refsWindow
-- impl-end


-- proof-start
theorem correct_requiresSubqueryWrap :
    ∀ (aggregates : List AggregateExpr) (otherConditions : Bool),
    problem_spec_requiresSubqueryWrap aggregates otherConditions
      (implementation_requiresSubqueryWrap aggregates otherConditions) := by
  intro aggregates otherConditions
  simp only [problem_spec_requiresSubqueryWrap, implementation_requiresSubqueryWrap,
    anyRefSubquery, anyRefWindow, Id.run, bind, pure, List.forIn_yield_eq_foldl]
  have key : ∀ (l : List AggregateExpr) (b c : Bool),
      ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).fst
        = (b || l.any (fun a => a.refs.any fun x => x.isSubqueryExpr)))
      ∧ ((List.foldl (fun (p : MProd Bool Bool) a => (⟨p.fst || a.refs.any fun x => x.isSubqueryExpr,
          p.snd || a.refs.any fun x => x.isWindowExpr⟩ : MProd Bool Bool)) (⟨b, c⟩ : MProd Bool Bool) l).snd
        = (c || l.any (fun a => a.refs.any fun x => x.isWindowExpr))) := by
    intro l
    induction l with
    | nil => intro b c; exact ⟨by simp, by simp⟩
    | cons hd tl ih =>
      intro b c
      simp only [List.foldl_cons, List.any_cons]
      refine ⟨?_, ?_⟩
      · rw [(ih _ _).1, Bool.or_assoc]
      · rw [(ih _ _).2, Bool.or_assoc]
  rw [(key aggregates false false).1, (key aggregates false false).2]
  simp [Bool.or_assoc]

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

### PROTOCOL EXECUTION (all runs; concurrent lean_verify jobs in batches of 4).

SPEC SHAPE: post-conditions pin `result = (otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates)` — a TIGHT functional equality, no existential/oracle slack. axioms region empty; axiom_check.py is a genuine skip stub (verified: no consumed axiom, no A-reference deep model — the two getattr reads are reproduced concretely as boolean fields isSubqueryExpr/isWindowExpr, R/I). This is the strongest spec shape: verify ⇒ extensional equality on ALL inputs ⇒ correct patch behavior.

SAME_SPEC: all 7 attacks return True (invariant prefix = everything through `-- impl-start` kept byte-identical). Non-vacuity confirmed: tampering the postcondition (drop anyRefWindow) → same_spec False; tampering the pure region (anyRefWindow .any→.all) → same_spec False. So same_spec locks axioms/pure/pre/post byte-for-byte.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`):
- atk_1 PREPATCH BUG (drops window flag; returns otherConditions||refsSubquery): same_spec True, EXIT 1 (rewrite failed to close) → prepatch reproduced (matches Solution_prepatch.lean impl; that file carries `sorry` as UNCLOSABLE).
- atk_2 PARTIAL-DOMAIN (empty aggregates → return false, ignoring otherConditions): same_spec True, EXIT 1.
- atk_3 BOUNDARY (.all instead of .any for window flag): same_spec True, EXIT 1.
- atk_4 CONTROL-FLOW-EFFECT (early `return` inside loop after first aggregate): same_spec True, EXIT 1.
- atk_5 DROP subquery flag (returns otherConditions||refsWindow): same_spec True, EXIT 1.
- atk_6 DROP otherConditions from final disjunction: same_spec True, EXIT 1.
- atk_7 UNGROUNDED-ORACLE ECHO (returns spec RHS verbatim `otherConditions || anyRefSubquery aggregates || anyRefWindow aggregates`, proof `rfl`): same_spec True, EXIT 0 VERIFIES. #print axioms correct_requiresSubqueryWrap → 'does not depend on any axioms' (clean, no sorry/_prop).

POSITIVE CONTROL pos_gold.lean (gold impl): EXIT 0; #print axioms → [propext, Quot.sound] (standard Lean axioms only, no sorry/_prop) — clean.

MANDATORY RESOLVE OF VERIFYING ATTACK: atk_7 is the correct echo (extensionally identical to gold RHS). Its faithful refined patch is the gold get_aggregation patch (adds refs_window accumulator + disjunct). EXECUTED via swebench_unified.harness.run_resolve('django__django-17084', patch, run_id='sbu-audit-eq-uiu2iybo-atk7', timeout=1800): RESOLVED=True, COMPLETED=True, NOTE='resolved'. So the sole verifying same-spec impl RESOLVES — no verify⇏correct witness. Per the 2026-08-06 G-PANEL-1/G-EQ echo policy, a resolving echo of the gold is NOT a weakness.

REFINEMENT.MD AUDIT: 6 rows. Rows 1-2 I (accumulator inits). Row 3 R (dict-of-aggregates ↔ List AggregateExpr; only get_refs matters). Rows 4-5 R (the two getattr reads reproduced concretely as boolean fields — the changed op row 5 modeled deeply, NOT axiomatized). Row 6 R/I (pre-existing disjuncts collapsed into otherConditions R; appending ||refsWindow is the identical concrete op I). NO A-consumed and NO A-reference rows — consistent with empty axioms region and G-AX skip stub. No kind-3 (changed-inexpressible) leg. Correspondence to real callees holds: get_refs()→refs, subquery/contains_over_clause getattrs→isSubqueryExpr/isWindowExpr with defaults resolved into the booleans (mapping.md documents contains_over_clause default True). All legs R/I → mechanically G-CONF's domain (conformance_check.py runs a real fuzz, conf_skip=false), which is out of this A-leg-focused pass but present and non-stub.

VERDICT: SOUND. ≥5 distinct wrong impls (6 built + prepatch) all failed to close against a tight functional-equality spec; the only closing same-spec impl is a correct echo whose materialized faithful patch was EXECUTED through the official harness and RESOLVED.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Checks performed: (1) same_spec(Solution.lean, Solution_prepatch.lean) with LeanBackend.language tables = True — spec region byte-identical. (2) scripts/lean_verify.sh Solution.lean exit 0, no sorry (only a harmless List.forIn_yield_eq_foldl deprecation warning). (3) #print axioms correct_requiresSubqueryWrap => [propext, Quot.sound] — NO sorryAx, proof is genuine. (4) Prepatch impl omits refsWindow and returns otherConditions||refsSubquery; its proof is sorry — correct G-DIFF/G-PANEL-DIFF signal, the buggy impl cannot satisfy the spec whenever anyRefWindow holds with otherConditions=false and no subquery ref. Faithfulness of model vs real post-patch callee (query.py:397-457 @ base_commit): the modeled Bool decision = otherConditions || anyRefSubquery || anyRefWindow maps op-for-op to the patched `if (isinstance(group_by,tuple) or is_sliced or has_existing_aggregation or refs_subquery or refs_window or qualify or distinct or combinator)`. The 6 unchanged disjuncts collapse faithfully into free input otherConditions (decision only uses their OR). refs_subquery/refs_window accumulate `any(getattr(...,'subquery',False))` / `any(getattr(...,'contains_over_clause',True))` — both match anyRefSubquery/anyRefWindow, with any([])=false matching List.any []=false and the True default encoded per-reference in isWindowExpr (G-CONF fuzzes absent-attr default). conformance_check.py present, seed 17084, 120k inputs, independent patched_decision reconstruction exercising getattr defaults. Spec is neither too weak (result fully pinned to the disjunction, frame constrained) nor too strong on the changed/substantive behavior. VERDICT: FAITHFUL.

Counterexample / evidence:

```
empty-aggregates boundary only, outside the modeled decision path: aggregates=[], otherConditions=True -> model=True, callee returns early (no wrap). Not a faithfulness defect for the modeled function.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures); only distinctive changed symbol is get_aggregation, which is absent from the spec view. Spec region byte-identical with Solution_prepatch (same_spec=True). Spec view abstracts all gold-edit specifics: names none of refs_window / contains_over_clause / get_aggregation / query.py; identifiers are model-local (isWindowExpr, anyRefWindow, RefAnnotation, problem_spec_requiresSubqueryWrap). Comments describe behavior in generic terms ('window/over-clause expression', 'wrapping subquery') grounded in the PUBLIC problem_statement, which explicitly states the bug is 'aggregate over window functions' with a Window(Sum(...)) example. No bug/fix/patch narration. The anyRefWindow postcondition disjunct encodes correct behavior a faithful spec must pin (impl/proof regions are elided from the spec view anyway) and follows directly from the public problem statement — it does not reveal the edit's location or mechanism. No leakage beyond problem_statement (hints_text not consulted).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
