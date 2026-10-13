# P2 adversarial audit — sympy__sympy-12096

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,15 +51,11 @@
   | .atom   => none
   | .app f args => Id.run do
       let mut vals : List Int := []
-      for a in args.attach do
-        match implementation_evalf a.1 with
-        | some v => vals := vals ++ [v]
-        | none   => return none
+      for a in args do
+        match a with
+        | .num v => vals := vals ++ [v]
+        | _      => return none
       return some (f vals)
-decreasing_by
-  have h := List.sizeOf_lt_of_mem a.2
-  simp only [Expr.app.sizeOf_spec]
-  omega
 -- impl-end
 
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,17 +49,7 @@
 def implementation_evalf : Expr → Option Int
   | .num n  => some n
   | .atom   => none
-  | .app f args => Id.run do
-      let mut vals : List Int := []
-      for a in args.attach do
-        match implementation_evalf a.1 with
-        | some v => vals := vals ++ [v]
-        | none   => return none
-      return some (f vals)
-decreasing_by
-  have h := List.sizeOf_lt_of_mem a.2
-  simp only [Expr.app.sizeOf_spec]
-  omega
+  | .app _ _ => none
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
 
 -- impl-start
 def implementation_evalf : Expr → Option Int
-  | .num n  => some n
+  | .num n  => some (n + 1)
   | .atom   => none
   | .app f args => Id.run do
       let mut vals : List Int := []
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,7 +54,7 @@
       for a in args.attach do
         match implementation_evalf a.1 with
         | some v => vals := vals ++ [v]
-        | none   => return none
+        | none   => pure ()
       return some (f vals)
 decreasing_by
   have h := List.sizeOf_lt_of_mem a.2
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_evalf : Expr → Option Int
   | .num n  => some n
-  | .atom   => none
+  | .atom   => some 0
   | .app f args => Id.run do
       let mut vals : List Int := []
       for a in args.attach do
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
         match implementation_evalf a.1 with
         | some v => vals := vals ++ [v]
         | none   => return none
-      return some (f vals)
+      return some (f vals.reverse)
 decreasing_by
   have h := List.sizeOf_lt_of_mem a.2
   simp only [Expr.app.sizeOf_spec]
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,83 +47,13 @@
 
 -- impl-start
 def implementation_evalf : Expr → Option Int
-  | .num n  => some n
-  | .atom   => none
-  | .app f args => Id.run do
-      let mut vals : List Int := []
-      for a in args.attach do
-        match implementation_evalf a.1 with
-        | some v => vals := vals ++ [v]
-        | none   => return none
-      return some (f vals)
-decreasing_by
-  have h := List.sizeOf_lt_of_mem a.2
-  simp only [Expr.app.sizeOf_spec]
-  omega
+  | e => evalSpec e
 -- impl-end
 
 
 -- proof-start
-/-- Closed form for the app-branch imperative loop started with accumulator `acc`
-over the attached argument list `xs`: the `mapM` of `implementation_evalf` over the
-subexpressions, threaded through `acc`.  This is the value-level target the loop is
-proven equal to before the outer implementation function `f` is applied. -/
-def loop_run {p : Expr → Prop} (xs : List {x : Expr // p x}) (acc : List Int) :
-    Option (List Int) :=
-  Option.map (fun vs => acc ++ vs) (xs.mapM (fun a => implementation_evalf a.1))
-
-/-- The app-branch imperative `Id.run` for-loop (with early `none` short-circuit,
-started at accumulator `acc`, and final `some (f vals)`) equals the closed form
-`loop_run xs acc` post-composed with `f`. -/
-theorem loop_eq_mapM {p : Expr → Prop} (f : List Int → Int)
-    (xs : List {x : Expr // p x}) (acc : List Int) :
-    (Id.run do
-      let mut vals := acc
-      for a in xs do
-        match implementation_evalf a.1 with
-        | some v => vals := vals ++ [v]
-        | none   => return none
-      return some (f vals)) = (loop_run xs acc).map f := by
-  induction xs generalizing acc with
-  | nil => simp [loop_run, Id.run]; rfl
-  | cons a as ih =>
-      simp only [List.forIn_cons, loop_run, List.mapM_cons]
-      cases h : implementation_evalf a.1 with
-      | none => simp [Id.run]; rfl
-      | some v =>
-          have hih := ih (acc ++ [v])
-          simp only [loop_run, Id.run] at hih ⊢
-          simp at *
-          rw [hih]
-          cases List.mapM implementation_evalf as.unattach <;> simp
-
-/-- Under `mapM`, `implementation_evalf` may be swapped for `evalSpec` on the
-attached subexpressions using the pointwise induction hypothesis. -/
-theorem mapM_congr_eval {p : Expr → Prop} (xs : List {x : Expr // p x})
-    (h : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1) :
-    xs.mapM (fun a => implementation_evalf a.1)
-      = xs.mapM (fun a => evalSpec a.1) := by
-  induction xs with
-  | nil => rfl
-  | cons x xs ih =>
-    have hx : implementation_evalf x.1 = evalSpec x.1 := h x (by simp)
-    have hxs : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1 :=
-      fun a ha => h a (by simp [ha])
-    simp only [List.mapM_cons, hx, ih hxs]
-
 theorem correct_evalf : ∀ (e : Expr),
     problem_spec_evalf e (implementation_evalf e) := by
   intro e
-  show implementation_evalf e = evalSpec e
-  induction e using implementation_evalf.induct with
-  | case1 n => rw [implementation_evalf, evalSpec]
-  | case2 => rw [implementation_evalf, evalSpec]
-  | case3 f args ih =>
-    rw [implementation_evalf, evalSpec]
-    rw [loop_eq_mapM f args.attach []]
-    rw [loop_run]
-    rw [mapM_congr_eval args.attach (fun a _ => ih a)]
-    simp only [List.nil_append, Option.map_map]
-    rfl
-
+  rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,7 +47,7 @@
 
 -- impl-start
 def implementation_evalf : Expr → Option Int
-  | .num n  => some n
+  | .num _  => none
   | .atom   => none
   | .app f args => Id.run do
       let mut vals : List Int := []
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. A numeric evaluation of
-- an expression is modeled deeply below (`evalSpec`): a number evaluates to
-- itself, a bare atom has no numeric value, and an application evaluates to its
-- implementation applied to the evaluated arguments. There is no `opaque` callee
-- and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- A numeric expression tree.
* `num n`     — a concrete numeric value `n`.
* `atom`      — a bare symbol carrying no numeric value.
* `app f args`— an application of a node whose numeric implementation is `f`
  to the argument subexpressions `args`. -/
inductive Expr where
  | num  : Int → Expr
  | atom : Expr
  | app  : (List Int → Int) → List Expr → Expr

/-- Numeric evaluation of an expression.
* a number evaluates to itself;
* a bare symbol has no numeric value (`none`);
* an application evaluates to its implementation applied to the list of evaluated
  arguments — and has a numeric value exactly when every argument does, the
  arguments being evaluated by the same numeric evaluation (a structural
  recursion over the argument subexpressions). -/
def evalSpec : Expr → Option Int
  | .num n  => some n
  | .atom   => none
  | .app f args => (args.attach.mapM (fun a => evalSpec a.1)).map f
decreasing_by
  have h := List.sizeOf_lt_of_mem a.2
  simp only [Expr.app.sizeOf_spec]
  omega
-- pure-end

-- post-conditions-start
/-- The result is the numeric evaluation of the input expression: a number
evaluates to itself, a bare symbol to no value, and an application to its
implementation applied to its evaluated arguments. -/
def problem_spec_evalf (e : Expr) (result : Option Int) : Prop :=
  result = evalSpec e
-- post-conditions-end

-- impl-start
def implementation_evalf : Expr → Option Int
  | .num n  => some n
  | .atom   => none
  | .app f args => Id.run do
      let mut vals : List Int := []
      for a in args.attach do
        match implementation_evalf a.1 with
        | some v => vals := vals ++ [v]
        | none   => return none
      return some (f vals)
decreasing_by
  have h := List.sizeOf_lt_of_mem a.2
  simp only [Expr.app.sizeOf_spec]
  omega
-- impl-end


-- proof-start
/-- Closed form for the app-branch imperative loop started with accumulator `acc`
over the attached argument list `xs`: the `mapM` of `implementation_evalf` over the
subexpressions, threaded through `acc`.  This is the value-level target the loop is
proven equal to before the outer implementation function `f` is applied. -/
def loop_run {p : Expr → Prop} (xs : List {x : Expr // p x}) (acc : List Int) :
    Option (List Int) :=
  Option.map (fun vs => acc ++ vs) (xs.mapM (fun a => implementation_evalf a.1))

/-- The app-branch imperative `Id.run` for-loop (with early `none` short-circuit,
started at accumulator `acc`, and final `some (f vals)`) equals the closed form
`loop_run xs acc` post-composed with `f`. -/
theorem loop_eq_mapM {p : Expr → Prop} (f : List Int → Int)
    (xs : List {x : Expr // p x}) (acc : List Int) :
    (Id.run do
      let mut vals := acc
      for a in xs do
        match implementation_evalf a.1 with
        | some v => vals := vals ++ [v]
        | none   => return none
      return some (f vals)) = (loop_run xs acc).map f := by
  induction xs generalizing acc with
  | nil => simp [loop_run, Id.run]; rfl
  | cons a as ih =>
      simp only [List.forIn_cons, loop_run, List.mapM_cons]
      cases h : implementation_evalf a.1 with
      | none => simp [Id.run]; rfl
      | some v =>
          have hih := ih (acc ++ [v])
          simp only [loop_run, Id.run] at hih ⊢
          simp at *
          rw [hih]
          cases List.mapM implementation_evalf as.unattach <;> simp

/-- Under `mapM`, `implementation_evalf` may be swapped for `evalSpec` on the
attached subexpressions using the pointwise induction hypothesis. -/
theorem mapM_congr_eval {p : Expr → Prop} (xs : List {x : Expr // p x})
    (h : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1) :
    xs.mapM (fun a => implementation_evalf a.1)
      = xs.mapM (fun a => evalSpec a.1) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    have hx : implementation_evalf x.1 = evalSpec x.1 := h x (by simp)
    have hxs : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1 :=
      fun a ha => h a (by simp [ha])
    simp only [List.mapM_cons, hx, ih hxs]

theorem correct_evalf : ∀ (e : Expr),
    problem_spec_evalf e (implementation_evalf e) := by
  intro e
  show implementation_evalf e = evalSpec e
  induction e using implementation_evalf.induct with
  | case1 n => rw [implementation_evalf, evalSpec]
  | case2 => rw [implementation_evalf, evalSpec]
  | case3 f args ih =>
    rw [implementation_evalf, evalSpec]
    rw [loop_eq_mapM f args.attach []]
    rw [loop_run]
    rw [mapM_congr_eval args.attach (fun a _ => ih a)]
    simp only [List.nil_append, Option.map_map]
    rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_evalf e result := (result = evalSpec e); correct_evalf : forall e, implementation_evalf e = evalSpec e. This is a TOTAL functional-equality spec (tightest possible): any impl that closes the proof without sorry is forced pointwise-equal to evalSpec, which is exactly the post-patch behavior. All 8 attacks built by copying Solution.lean and editing ONLY the impl region (+matching proof scaffold); every one confirmed same_spec=True via swebench_unified.markers.same_spec (backend lean).

POSITIVE CONTROL pos_gold.lean (exact gold impl): lean_verify.sh -> exit 0. #print axioms correct_evalf -> [propext, Quot.sound] (clean; no sorryAx/native_decide/Classical.choice).

GENUINELY-WRONG same-spec impls -- ALL lean_verify.sh -> exit 1 (fail to close, no faithful patch to run):
  atk_1 = prepatch bug (value only from immediate .num args, non-numeric child aborts; no recursion into nested apps): exit 1, unsolved app-case goal. PREPATCH REPRODUCED (matches Solution_prepatch.lean semantics).
  atk_2 = app-branch always none (partial-domain): exit 1, `none = Option.map f ...` unsolved.
  atk_3 = num off-by-one (some (n+1)): exit 1, goal `some (n+1) = some n`.
  atk_4 = control-flow-effect: symbolic arg `none` case does `pure ()` (skip) instead of aborting: exit 1, loop closed-form mismatch.
  atk_5 = wrong leaf: atom => some 0: exit 1, goal `some 0 = none`.
  atk_6 = order effect: f applied to vals.reverse: exit 1, loop closed-form mismatch.
  atk_8 = wrong num leaf: num _ => none: exit 1, goal `none = some n`.

CLOSING NON-GOLD IMPL (must be run through harness): atk_7 = ungrounded-oracle echo `implementation_evalf e := evalSpec e`, proof `intro e; rfl`. lean_verify.sh -> exit 0; #print axioms correct_evalf -> [propext, Quot.sound] (clean). Because atk_7 is extensionally IDENTICAL to evalSpec = the exact post-patch numeric evaluation (recurse evalf into each arg then apply _imp_), its faithful refined patch is byte-identical to the gold patch. MATERIALIZED atk_7_patch.diff and ran run_resolve('sympy__sympy-12096', ...) under the official Docker harness: RESULT completed=True resolved=True flaky=False attempts=1 note=resolved. So the only closing non-gold impl RESOLVES -> verify=>correct holds; no break.

REFINEMENT AUDIT: all legs are R (rows 1-5,7) or I (row 6); A-consumed=none, A-reference=none; no kind-3 (inexpressible) leg. The per-argument recursion (the actual fix) is modeled DEEPLY as structural recursion (op #4), not axiomatized. The node implementation f : List Int -> Int (<-> self._imp_) is a UNIVERSALLY-QUANTIFIED model parameter in correct_evalf (bound by the app constructor; theorem is forall e), NOT an axiomatized/opaque callee -- so G-AX is a legitimate skip and the correspondence holds. Universal quantification over f makes the spec STRONGER (holds for every node impl), not weaker; no behavior is hidden behind an axiom. Consistent with mapping.md strict-in-args assumption.

CONCLUSION: The functional-equality postcondition admits exactly the post-patch semantics; all 6-7 distinct wrong impls (partial-domain, boundary, control-flow-effect, order, wrong-leaf, prepatch-bug) provably fail to close, and the single closing non-gold impl (echo) has a materialized faithful patch that RESOLVES under run_resolve. verify=>correct confirmed. VERDICT: SOUND.

COMMANDS: verify: `bash scripts/lean_verify.sh <file>.lean` (run 4-at-a-time concurrently). axioms: appended `#print axioms correct_evalf` to ax_pos_gold.lean/ax_atk_7.lean, both -> [propext, Quot.sound]. same_spec: markers.same_spec(gold, cand, 'lean') = True for all 8. resolve: swebench_unified.harness.run_resolve on atk_7_patch.diff (== gold) -> resolved=True.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is invoked by the modeled behavior. A numeric evaluation of
-- an expression is modeled deeply below (`evalSpec`): a number evaluates to
-- itself, a bare atom has no numeric value, and an application evaluates to its
-- implementation applied to the evaluated arguments. There is no `opaque` callee
-- and no consumed `_prop` axiom here.
-- axioms-end

-- pure-start
/-- A numeric expression tree.
* `num n`     — a concrete numeric value `n`.
* `atom`      — a bare symbol carrying no numeric value.
* `app f args`— an application of a node whose numeric implementation is `f`
  to the argument subexpressions `args`. -/
inductive Expr where
  | num  : Int → Expr
  | atom : Expr
  | app  : (List Int → Int) → List Expr → Expr

/-- Numeric evaluation of an expression.
* a number evaluates to itself;
* a bare symbol has no numeric value (`none`);
* an application evaluates to its implementation applied to the list of evaluated
  arguments — and has a numeric value exactly when every argument does, the
  arguments being evaluated by the same numeric evaluation (a structural
  recursion over the argument subexpressions). -/
def evalSpec : Expr → Option Int
  | .num n  => some n
  | .atom   => none
  | .app f args => (args.attach.mapM (fun a => evalSpec a.1)).map f
decreasing_by
  have h := List.sizeOf_lt_of_mem a.2
  simp only [Expr.app.sizeOf_spec]
  omega
-- pure-end

-- post-conditions-start
/-- The result is the numeric evaluation of the input expression: a number
evaluates to itself, a bare symbol to no value, and an application to its
implementation applied to its evaluated arguments. -/
def problem_spec_evalf (e : Expr) (result : Option Int) : Prop :=
  result = evalSpec e
-- post-conditions-end

-- impl-start
def implementation_evalf : Expr → Option Int
  | .num n  => some n
  | .atom   => none
  | .app f args => Id.run do
      let mut vals : List Int := []
      for a in args.attach do
        match implementation_evalf a.1 with
        | some v => vals := vals ++ [v]
        | none   => return none
      return some (f vals)
decreasing_by
  have h := List.sizeOf_lt_of_mem a.2
  simp only [Expr.app.sizeOf_spec]
  omega
-- impl-end


-- proof-start
/-- Closed form for the app-branch imperative loop started with accumulator `acc`
over the attached argument list `xs`: the `mapM` of `implementation_evalf` over the
subexpressions, threaded through `acc`.  This is the value-level target the loop is
proven equal to before the outer implementation function `f` is applied. -/
def loop_run {p : Expr → Prop} (xs : List {x : Expr // p x}) (acc : List Int) :
    Option (List Int) :=
  Option.map (fun vs => acc ++ vs) (xs.mapM (fun a => implementation_evalf a.1))

/-- The app-branch imperative `Id.run` for-loop (with early `none` short-circuit,
started at accumulator `acc`, and final `some (f vals)`) equals the closed form
`loop_run xs acc` post-composed with `f`. -/
theorem loop_eq_mapM {p : Expr → Prop} (f : List Int → Int)
    (xs : List {x : Expr // p x}) (acc : List Int) :
    (Id.run do
      let mut vals := acc
      for a in xs do
        match implementation_evalf a.1 with
        | some v => vals := vals ++ [v]
        | none   => return none
      return some (f vals)) = (loop_run xs acc).map f := by
  induction xs generalizing acc with
  | nil => simp [loop_run, Id.run]; rfl
  | cons a as ih =>
      simp only [List.forIn_cons, loop_run, List.mapM_cons]
      cases h : implementation_evalf a.1 with
      | none => simp [Id.run]; rfl
      | some v =>
          have hih := ih (acc ++ [v])
          simp only [loop_run, Id.run] at hih ⊢
          simp at *
          rw [hih]
          cases List.mapM implementation_evalf as.unattach <;> simp

/-- Under `mapM`, `implementation_evalf` may be swapped for `evalSpec` on the
attached subexpressions using the pointwise induction hypothesis. -/
theorem mapM_congr_eval {p : Expr → Prop} (xs : List {x : Expr // p x})
    (h : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1) :
    xs.mapM (fun a => implementation_evalf a.1)
      = xs.mapM (fun a => evalSpec a.1) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
    have hx : implementation_evalf x.1 = evalSpec x.1 := h x (by simp)
    have hxs : ∀ a ∈ xs, implementation_evalf a.1 = evalSpec a.1 :=
      fun a ha => h a (by simp [ha])
    simp only [List.mapM_cons, hx, ih hxs]

theorem correct_evalf : ∀ (e : Expr),
    problem_spec_evalf e (implementation_evalf e) := by
  intro e
  show implementation_evalf e = evalSpec e
  induction e using implementation_evalf.induct with
  | case1 n => rw [implementation_evalf, evalSpec]
  | case2 => rw [implementation_evalf, evalSpec]
  | case3 f args ih =>
    rw [implementation_evalf, evalSpec]
    rw [loop_eq_mapM f args.attach []]
    rw [loop_run]
    rw [mapM_congr_eval args.attach (fun a _ => ih a)]
    simp only [List.nil_append, Option.map_map]
    rfl

-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition problem_spec_evalf e result := (result = evalSpec e); correct_evalf : forall e, implementation_evalf e = evalSpec e. This is a TOTAL functional-equality spec (tightest possible): any impl that closes the proof without sorry is forced pointwise-equal to evalSpec, which is exactly the post-patch behavior. All 8 attacks built by copying Solution.lean and editing ONLY the impl region (+matching proof scaffold); every one confirmed same_spec=True via swebench_unified.markers.same_spec (backend lean).

POSITIVE CONTROL pos_gold.lean (exact gold impl): lean_verify.sh -> exit 0. #print axioms correct_evalf -> [propext, Quot.sound] (clean; no sorryAx/native_decide/Classical.choice).

GENUINELY-WRONG same-spec impls -- ALL lean_verify.sh -> exit 1 (fail to close, no faithful patch to run):
  atk_1 = prepatch bug (value only from immediate .num args, non-numeric child aborts; no recursion into nested apps): exit 1, unsolved app-case goal. PREPATCH REPRODUCED (matches Solution_prepatch.lean semantics).
  atk_2 = app-branch always none (partial-domain): exit 1, `none = Option.map f ...` unsolved.
  atk_3 = num off-by-one (some (n+1)): exit 1, goal `some (n+1) = some n`.
  atk_4 = control-flow-effect: symbolic arg `none` case does `pure ()` (skip) instead of aborting: exit 1, loop closed-form mismatch.
  atk_5 = wrong leaf: atom => some 0: exit 1, goal `some 0 = none`.
  atk_6 = order effect: f applied to vals.reverse: exit 1, loop closed-form mismatch.
  atk_8 = wrong num leaf: num _ => none: exit 1, goal `none = some n`.

CLOSING NON-GOLD IMPL (must be run through harness): atk_7 = ungrounded-oracle echo `implementation_evalf e := evalSpec e`, proof `intro e; rfl`. lean_verify.sh -> exit 0; #print axioms correct_evalf -> [propext, Quot.sound] (clean). Because atk_7 is extensionally IDENTICAL to evalSpec = the exact post-patch numeric evaluation (recurse evalf into each arg then apply _imp_), its faithful refined patch is byte-identical to the gold patch. MATERIALIZED atk_7_patch.diff and ran run_resolve('sympy__sympy-12096', ...) under the official Docker harness: RESULT completed=True resolved=True flaky=False attempts=1 note=resolved. So the only closing non-gold impl RESOLVES -> verify=>correct holds; no break.

REFINEMENT AUDIT: all legs are R (rows 1-5,7) or I (row 6); A-consumed=none, A-reference=none; no kind-3 (inexpressible) leg. The per-argument recursion (the actual fix) is modeled DEEPLY as structural recursion (op #4), not axiomatized. The node implementation f : List Int -> Int (<-> self._imp_) is a UNIVERSALLY-QUANTIFIED model parameter in correct_evalf (bound by the app constructor; theorem is forall e), NOT an axiomatized/opaque callee -- so G-AX is a legitimate skip and the correspondence holds. Universal quantification over f makes the spec STRONGER (holds for every node impl), not weaker; no behavior is hidden behind an axiom. Consistent with mapping.md strict-in-args assumption.

CONCLUSION: The functional-equality postcondition admits exactly the post-patch semantics; all 6-7 distinct wrong impls (partial-domain, boundary, control-flow-effect, order, wrong-leaf, prepatch-bug) provably fail to close, and the single closing non-gold impl (echo) has a materialized faithful patch that RESOLVES under run_resolve. verify=>correct confirmed. VERDICT: SOUND.

COMMANDS: verify: `bash scripts/lean_verify.sh <file>.lean` (run 4-at-a-time concurrently). axioms: appended `#print axioms correct_evalf` to ax_pos_gold.lean/ax_atk_7.lean, both -> [propext, Quot.sound]. same_spec: markers.same_spec(gold, cand, 'lean') = True for all 8. resolve: swebench_unified.harness.run_resolve on atk_7_patch.diff (== gold) -> resolved=True.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous checks performed: (1) spec region byte-identical (swebench_unified.markers.same_spec over LeanBackend.language = True). (2) Solution.lean compiles clean via scripts/lean_verify.sh (exit 0); #print axioms correct_evalf = [propext, Quot.sound] — NO sorryAx, proof is genuine, not fake. (3) Empirically tested evalSpec vs real post-patch sympy 1.4 (F2P f(f(2))==16 confirmed present). Within the documented strict-in-args domain the spec matches the real callee on ALL probes: nested compositions (sq(sq(2))=16), multi-arg all-numeric (lin(1,2,3)=25), symbolic-leaf abort (lin(1,x,3), sq(lin(1,x,3)) -> symbolic/none), and the empty-arg edge (z() -> some 42). The single divergence found is for NON-STRICT implementations (an _imp_ that ignores a symbolic arg), which is (a) explicitly and prominently excluded by the binding 'strict-in-args' modeling assumption in mapping.md/refinement.md, (b) not part of the changed behavior — both pre- and post-patch produce 5.0 for g(x,5), so the fix is neutral there, and (c) not even expressible in the Lean model, where f : List Int -> Int only ever receives fully-evaluated argument lists. The strict assumption is justified by the issue examples and F2P test (lambda x: x**2, lambda x: 2*x), which are all strict, and the entire discriminating F2P behavior lives within the strict domain. This is legitimate, documented scoping — not spec-too-strong drift. Verdict FAITHFUL.

Counterexample / evidence:

```
g(x, Integer(5)).evalf() == 5.00000000000000 (is_number True) in sympy 1.4 post-patch, whereas evalSpec (.app g [atom, num 5]) = none because arg `atom` has no numeric value. Verified pre-patch AND post-patch both return 5.0 for this input, so the fix does not change behavior here — the divergence is on unchanged behavior, outside the modeled fix.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (rendered via markers.spec_view on LeanBackend) exposes only: imports, the axioms-region comment (no opaque callee / no axiom), the `Expr` inductive, `evalSpec` (recursive numeric evaluation: num→self, atom→none, app→impl applied to evaluated args), and `problem_spec_evalf`. Impl and proof regions are fully elided to placeholders. same_spec(Solution, Solution_prepatch)=True; the discriminating gold behavior lives entirely in the elided impl/proof, not the shared spec.

Leakage question: does the spec leak the gold edit BEYOND the public problem_statement? No. The gold edit is: evaluate each argument recursively (`i.evalf(prec)`) before applying `_imp_`. The public problem_statement ALREADY states this verbatim — title 'evalf does not call _imp_ recursively' and body 'It isn't calling evalf recursively on the return of _imp_', plus the concrete failing example f(g(2)).evalf() -> f(g(2)). The spec's `evalSpec` formalizes the correct/post-patch behavior (an application is numeric iff every argument is numeric, via structural recursion over arg subexpressions) — which is exactly the semantic the public issue already discloses. A spec must describe correct behavior; doing so here reveals nothing not already in problem_statement. No Python-specific gold tokens (`_imp_`, `Float`, `prec`, `self.args`, the list comprehension) appear in the spec view; comments stay abstract.

Lexical G-LEAK screen: leakage.screen() passed with hard_failures=[]. No gold-patch specifics or problem-statement phrasing quoted in spec-view comments. Confirmed NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
