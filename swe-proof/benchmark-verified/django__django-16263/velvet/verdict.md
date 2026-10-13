# P2 adversarial audit — django__django-16263

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch_d1.lean`, `atk2_prepatch2_d2.lean`, `atk3_partial_dropcombinator.lean`, `atk4_boundary_allannos.lean`, `atk5_controlflow_keptnames.lean`, `atk6_existing_noguard.lean`, `atk7_echo_oracle.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch_d1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The only callee whose behaviour the proof depends on is
@@ -132,7 +132,7 @@
     -- impl-start
     let names := added.map (·.name)
     let existing := annos.filter (isExisting names)
-    let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
+    let priorAgg := !existing.isEmpty
     let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
     let mut m : List String := []
     let mut i := added.length
@@ -140,7 +140,6 @@
       invariant 0 ≤ i ∧ i ≤ added.length
       invariant m = maskFold (added.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := added[i - 1]!
       m := (a.name :: referencedNames a.expr) ++ m
```

Attack 2 — `atk2_prepatch2_d2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The only callee whose behaviour the proof depends on is
@@ -134,20 +134,8 @@
     let existing := annos.filter (isExisting names)
     let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
     let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
-    let mut m : List String := []
-    let mut i := added.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ added.length
-      invariant m = maskFold (added.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := added[i - 1]!
-      m := (a.name :: referencedNames a.expr) ++ m
-      i := i - 1
     let kept :=
-      if nesting then
-        if distinct then names ++ existing.map (·.name) else m
+      if nesting then names ++ existing.map (·.name)
       else names
     return { needsNesting := nesting, keptNames := kept }
     -- impl-end
```

Attack 3 — `atk3_partial_dropcombinator.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The only callee whose behaviour the proof depends on is
@@ -133,14 +133,13 @@
     let names := added.map (·.name)
     let existing := annos.filter (isExisting names)
     let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
-    let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
+    let nesting := groupByTuple || isSliced || priorAgg || distinct
     let mut m : List String := []
     let mut i := added.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ added.length
       invariant m = maskFold (added.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := added[i - 1]!
       m := (a.name :: referencedNames a.expr) ++ m
```

Attack 4 — `atk4_boundary_allannos.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The only callee whose behaviour the proof depends on is
@@ -140,14 +140,13 @@
       invariant 0 ≤ i ∧ i ≤ added.length
       invariant m = maskFold (added.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := added[i - 1]!
       m := (a.name :: referencedNames a.expr) ++ m
       i := i - 1
     let kept :=
       if nesting then
-        if distinct then names ++ existing.map (·.name) else m
+        if distinct then names ++ annos.map (·.name) else m
       else names
     return { needsNesting := nesting, keptNames := kept }
     -- impl-end
```

Attack 5 — `atk5_controlflow_keptnames.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The only callee whose behaviour the proof depends on is
@@ -140,15 +140,11 @@
       invariant 0 ≤ i ∧ i ≤ added.length
       invariant m = maskFold (added.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := added[i - 1]!
       m := (a.name :: referencedNames a.expr) ++ m
       i := i - 1
-    let kept :=
-      if nesting then
-        if distinct then names ++ existing.map (·.name) else m
-      else names
+    let kept := names
     return { needsNesting := nesting, keptNames := kept }
     -- impl-end
 
```

Attack 6 — `atk6_existing_noguard.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The only callee whose behaviour the proof depends on is
@@ -131,7 +131,7 @@
   do
     -- impl-start
     let names := added.map (·.name)
-    let existing := annos.filter (isExisting names)
+    let existing := annos.filter (fun a => a.selected)
     let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
     let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
     let mut m : List String := []
@@ -140,7 +140,6 @@
       invariant 0 ≤ i ∧ i ≤ added.length
       invariant m = maskFold (added.drop i)
       done_with i = 0
-      decreasing i
     do
       let a := added[i - 1]!
       m := (a.name :: referencedNames a.expr) ++ m
```

Attack 7 — `atk7_echo_oracle.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 -- No consumed axioms. The only callee whose behaviour the proof depends on is
@@ -130,25 +130,8 @@
   ensures res.keptNames = keptNames res.needsNesting distinct annos added
   do
     -- impl-start
-    let names := added.map (·.name)
-    let existing := annos.filter (isExisting names)
-    let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
-    let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
-    let mut m : List String := []
-    let mut i := added.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ added.length
-      invariant m = maskFold (added.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let a := added[i - 1]!
-      m := (a.name :: referencedNames a.expr) ++ m
-      i := i - 1
-    let kept :=
-      if nesting then
-        if distinct then names ++ existing.map (·.name) else m
-      else names
+    let nesting := needsNesting annos (added.map (·.name)) groupByTuple isSliced distinct combinator havingFilter
+    let kept := keptNames nesting distinct annos added
     return { needsNesting := nesting, keptNames := kept }
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The only callee whose behaviour the proof depends on is
-- the recursive name-collector `referencedNames` (the pure region), which is a
-- DEEP MODEL (A-reference) validated against its real counterpart by G-AX
-- (axiom_check.py), not an opaque assumption. Every other dependency of the
-- query under spec (the structural flags, the membership-in-the-SELECT-set
-- predicate, the presence of a row-summarising or windowed prior alias entry)
-- is an explicit, observable input of the method, so it needs no axiom.
-- axioms-end

-- pure-start
/- A declared alias entry, abstracted to exactly the fields that decide the
   shape of a counting query: its `name`, whether it is part of the query's
   visible SELECT set (`selected`), and whether it itself summarises rows
   (`isAggregate`) or is a windowed expression (`isWindow`). -/
structure Annotation where
  name : String
  selected : Bool
  isAggregate : Bool
  isWindow : Bool
deriving Inhabited, DecidableEq

/- The shape of an expression for the purpose of collecting the alias names it
   refers to: a `reference` names exactly one alias; a `composite` is built out
   of sub-expressions and refers to whatever they do. -/
inductive Expr where
  | reference : String → Expr
  | composite : List Expr → Expr
deriving Inhabited

/- An alias entry that is being added for the summary itself: its `name` and the
   expression tree it is computed from. -/
structure Added where
  name : String
  expr : Expr
deriving Inhabited

/- The decided plan: whether the count needs to run inside a nested query, and
   the set of alias names retained in the produced SQL. -/
structure Plan where
  needsNesting : Bool
  keptNames : List String
deriving Inhabited, DecidableEq

/- The alias names an expression refers to: a reference contributes its single
   target name; a composite contributes the union (here concatenation —
   membership is all that is observed) of its parts. Written with an explicit
   list companion so a single structural unfold is available per element. -/
mutual
def referencedNames : Expr → List String
  | .reference s => [s]
  | .composite es => referencedNamesList es
def referencedNamesList : List Expr → List String
  | [] => []
  | e :: rest => referencedNames e ++ referencedNamesList rest
end

/- The retained-name fold for the added summary entries, front-recursive so
   one unfold is exposed per loop step: each added entry contributes its
   own name followed by every name it refers to. -/
def maskFold : List Added → List String
  | [] => []
  | a :: rest => (a.name :: referencedNames a.expr) ++ maskFold rest

@[grind] lemma maskFold_nil : maskFold [] = [] := rfl
@[grind] lemma maskFold_cons (a : Added) (rest : List Added) :
    maskFold (a :: rest) = (a.name :: referencedNames a.expr) ++ maskFold rest := rfl

/- A prior (already-declared) alias entry: one that is in the visible SELECT set
   and is NOT itself one of the names being added for the summary. -/
def isExisting (names : List String) (a : Annotation) : Bool :=
  a.selected && !(names.contains a.name)

/- A nested query is forced by a prior alias entry only when that entry itself
   summarises rows or is windowed — or when a row-summarising filter is
   present. A prior entry that is neither is harmless and is pruned. -/
def anyPriorAggregate (annos : List Annotation) (names : List String)
    (havingFilter : Bool) : Bool :=
  ((annos.filter (isExisting names)).any (fun a => a.isAggregate || a.isWindow))
    || havingFilter

/- The nesting decision: the structural triggers, OR a row-summarising prior
   alias entry / filter. -/
def needsNesting (annos : List Annotation) (names : List String)
    (groupByTuple isSliced distinct combinator havingFilter : Bool) : Bool :=
  groupByTuple || isSliced
    || anyPriorAggregate annos names havingFilter
    || distinct || combinator

/- The names retained in the produced SQL. When the count is nested and the
   query does NOT collapse duplicate rows: the added names together with
   everything they refer to (prior entries not referred to are dropped). When
   the count is nested but the query DOES collapse duplicate rows (`distinct`):
   pruning is suppressed — narrowing the visible entries could change which
   rows collapse — so every visible prior entry is retained alongside the
   added names. Otherwise (no nesting): just the added names (prior ones
   inlined away). -/
def keptNames (nesting distinct : Bool) (annos : List Annotation)
    (added : List Added) : List String :=
  if nesting then
    if distinct then
      added.map (·.name)
        ++ (annos.filter (isExisting (added.map (·.name)))).map (·.name)
    else maskFold added
  else added.map (·.name)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method countQueryShape
    (annos : List Annotation) (added : List Added)
    (groupByTuple : Bool) (isSliced : Bool) (distinct : Bool)
    (combinator : Bool) (havingFilter : Bool)
    return (res : Plan)
  ensures res.needsNesting =
    needsNesting annos (added.map (·.name))
      groupByTuple isSliced distinct combinator havingFilter
  ensures res.keptNames = keptNames res.needsNesting distinct annos added
  do
    -- impl-start
    let names := added.map (·.name)
    let existing := annos.filter (isExisting names)
    let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
    let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
    let mut m : List String := []
    let mut i := added.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ added.length
      invariant m = maskFold (added.drop i)
      done_with i = 0
    do
      let a := added[i - 1]!
      m := (a.name :: referencedNames a.expr) ++ m
      i := i - 1
    let kept :=
      if nesting then
        if distinct then names ++ existing.map (·.name) else m
      else names
    return { needsNesting := nesting, keptNames := kept }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `maskFold` peels one contribution. The single goal
   `loom_solve` leaves for the loop body. -/
lemma maskFold_drop_step (added : List Added) (i : Nat)
    (hi : 0 < i) (hle : i ≤ added.length) :
    maskFold (added.drop (i - 1))
      = ((added[i - 1]!).name :: referencedNames (added[i - 1]!).expr)
        ++ maskFold (added.drop i) := by
  have hlt : i - 1 < added.length := by omega
  have hcons : added.drop (i - 1) = added[i - 1]! :: added.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, maskFold_cons]

prove_correct countQueryShape by
  loom_solve
  · rw [maskFold_drop_step added i (by omega) (by omega)]
    simp_all
  all_goals simp_all [keptNames, needsNesting, anyPriorAggregate]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-16263 (velvet). All commands: `cd && bash scripts/lean_verify.sh <file>`; same_spec via swebench_unified.markers.same_spec with get_backend('velvet').language. Verifications were run concurrently in two background batches (atk1-4, then atk5-7), ≤4 at a time.

STRUCTURAL FINDING: the spec is functionally tight. `Plan` has exactly two fields and BOTH postconditions pin them to exact equalities against the pure decision functions: `ensures res.needsNesting = needsNesting annos (added.map ·.name) groupByTuple isSliced distinct combinator havingFilter` and `ensures res.keptNames = keptNames res.needsNesting distinct annos added`, compared via derived DecidableEq. Any same-spec verifying impl is therefore forced to return the identical Plan on every input; no behavioral-deviation impl can verify. Consequently there are ZERO verifying wrong impls, hence NO faithful refined patches to materialize/resolve (patches={} by construction, not by omission).

### ATTACKS (all same_spec=True, all verified via lean_verify.sh):
- atk1_prepatch_d1 (prepatch D1 bug / ungrounded: priorAgg := !existing.isEmpty — nesting on mere presence of any prior selected anno; byte-identical priorAgg line to bundled Solution_prepatch.lean): exit 1, unsolved goal on ensures_2 (needsNesting). REJECTED.
- atk2_prepatch2_d2 (prepatch D2 bug: keep every existing anno unconditionally, even non-distinct nesting; mirrors bundled Solution_prepatch_2.lean): exit 1. REJECTED.
- atk3_partial_dropcombinator (partial-domain: drop `combinator` from nesting disjunction — correct only when combinator=false): exit 1, unsolved ensures_2 with residual `combinator = true -> ...`. REJECTED.
- atk4_boundary_allannos (boundary: distinct branch keeps annos.map name instead of existing/selected): exit 1, unsolved ensures_1. REJECTED.
- atk5_controlflow_keptnames (control-flow-effect: correct nesting computed but keptNames unconditionally set to added names, mask loop dead): exit 1, unsolved ensures_1. REJECTED.
- atk6_existing_noguard (boundary: existing filter drops the `!names.contains` guard, uses selected only): exit 1, both ensures_1 and ensures_2 unsolved. REJECTED.
- atk7_echo_oracle (ungrounded-oracle echo: return the spec pure functions verbatim): exit 1, `No goals to be solved` — the frozen proof block (maskFold_drop_step / loom_solve loop-body goals) no longer matches the loop-free impl, so even the exact-echo shape fails to verify unchanged. REJECTED.

Positive control: unmodified Solution.lean copied to positive_control.lean — verifies (exit 0), confirming toolchain and same_spec harness are sound (same_spec self = True).

prepatch_reproduced=True: atk1 reproduces the pre-patch D1 predicate (any prior annotation present) and atk2 the pre-patch D2 behaviour (retain every existing annotation); both correctly FAIL verification, confirming the spec discriminates the gold fix on both observable outcomes.

REFINEMENT.MD / A-LEG AUDIT: every leg is R, A-reference, or I; no kind-3 (Section C confirmed). A1/A2 (Annotation & added-name projections) = R; A3 (isExisting filter) = I under R; A4 (priorAgg incl. havingFilter) = I+R; A5 (5-way disjunction) = I; B2 (maskFold) = I; B3 (keptNames 3-branch) = I+R. The single patch-ADDED op get_refs is modeled DEEPLY as `referencedNames`/`referencedNamesList` (B1, A-reference+I), NOT axiomatized — no consumed axiom in bundle. A-reference correspondence verified against axiom_check.py: it applies the gold patch to /testbed, builds real Ref(alias,Value)/Func(*children,function='F') trees isomorphic to Expr, and asserts set(model_referenced_names(node)) == real_expr.get_refs() over 9 boundary + 20000 fuzz trees (seed 16263).

Model maps `.reference s ↦ [s]` ↔ Ref.get_refs={self.refs} and `.composite ↦ union over children` (concat, set-compared) ↔ BaseExpression.get_refs union over get_source_expressions — faithful. havingFilter (any(where.split_having_qualify()[1:])) and the Annotation field projections are observable R-inputs, correctly not axiomatized (mapping.md §3.2). conformance_check.py (G-CONF) shares the SAME real get_refs between shadow and oracle over 1e5 inputs (seed 16263), scoping the R/I decision algebra — consistent with the A-reference leg being G-AX's sole obligation.

Recorded meta.json gates: G-AX/G-CONF/G-DIFF/G-EQ/G-RESOLVE all pass, G-RESOLVE.resolved=True (gold patch resolves); G-LEAK relaxed (RELAXED_LEAKAGE.md present), G-PBT skip.

VERDICT: SOUND. ≥5 (7) distinct same-spec wrong impls across the mandated categories (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, plus the two prepatch reproductions) were all machine-checked and NONE verified; therefore no verifying-wrong-impl patch exists that could fail to resolve. verify⇒correct holds for this bundle. No resolve runs were required because no attack verified (materialize+resolve is conditional on a verifying wrong impl).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch_d1.lean`, `atk2_prepatch2_d2.lean`, `atk3_partial_dropcombinator.lean`, `atk4_boundary_allannos.lean`, `atk5_controlflow_keptnames.lean`, `atk6_existing_noguard.lean`, `atk7_echo_oracle.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch_d1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_prepatch2_d2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_partial_dropcombinator.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_boundary_allannos.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_controlflow_keptnames.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_existing_noguard.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_echo_oracle.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The only callee whose behaviour the proof depends on is
-- the recursive name-collector `referencedNames` (the pure region), which is a
-- DEEP MODEL (A-reference) validated against its real counterpart by G-AX
-- (axiom_check.py), not an opaque assumption. Every other dependency of the
-- query under spec (the structural flags, the membership-in-the-SELECT-set
-- predicate, the presence of a row-summarising or windowed prior alias entry)
-- is an explicit, observable input of the method, so it needs no axiom.
-- axioms-end

-- pure-start
/- A declared alias entry, abstracted to exactly the fields that decide the
   shape of a counting query: its `name`, whether it is part of the query's
   visible SELECT set (`selected`), and whether it itself summarises rows
   (`isAggregate`) or is a windowed expression (`isWindow`). -/
structure Annotation where
  name : String
  selected : Bool
  isAggregate : Bool
  isWindow : Bool
deriving Inhabited, DecidableEq

/- The shape of an expression for the purpose of collecting the alias names it
   refers to: a `reference` names exactly one alias; a `composite` is built out
   of sub-expressions and refers to whatever they do. -/
inductive Expr where
  | reference : String → Expr
  | composite : List Expr → Expr
deriving Inhabited

/- An alias entry that is being added for the summary itself: its `name` and the
   expression tree it is computed from. -/
structure Added where
  name : String
  expr : Expr
deriving Inhabited

/- The decided plan: whether the count needs to run inside a nested query, and
   the set of alias names retained in the produced SQL. -/
structure Plan where
  needsNesting : Bool
  keptNames : List String
deriving Inhabited, DecidableEq

/- The alias names an expression refers to: a reference contributes its single
   target name; a composite contributes the union (here concatenation —
   membership is all that is observed) of its parts. Written with an explicit
   list companion so a single structural unfold is available per element. -/
mutual
def referencedNames : Expr → List String
  | .reference s => [s]
  | .composite es => referencedNamesList es
def referencedNamesList : List Expr → List String
  | [] => []
  | e :: rest => referencedNames e ++ referencedNamesList rest
end

/- The retained-name fold for the added summary entries, front-recursive so
   one unfold is exposed per loop step: each added entry contributes its
   own name followed by every name it refers to. -/
def maskFold : List Added → List String
  | [] => []
  | a :: rest => (a.name :: referencedNames a.expr) ++ maskFold rest

@[grind] lemma maskFold_nil : maskFold [] = [] := rfl
@[grind] lemma maskFold_cons (a : Added) (rest : List Added) :
    maskFold (a :: rest) = (a.name :: referencedNames a.expr) ++ maskFold rest := rfl

/- A prior (already-declared) alias entry: one that is in the visible SELECT set
   and is NOT itself one of the names being added for the summary. -/
def isExisting (names : List String) (a : Annotation) : Bool :=
  a.selected && !(names.contains a.name)

/- A nested query is forced by a prior alias entry only when that entry itself
   summarises rows or is windowed — or when a row-summarising filter is
   present. A prior entry that is neither is harmless and is pruned. -/
def anyPriorAggregate (annos : List Annotation) (names : List String)
    (havingFilter : Bool) : Bool :=
  ((annos.filter (isExisting names)).any (fun a => a.isAggregate || a.isWindow))
    || havingFilter

/- The nesting decision: the structural triggers, OR a row-summarising prior
   alias entry / filter. -/
def needsNesting (annos : List Annotation) (names : List String)
    (groupByTuple isSliced distinct combinator havingFilter : Bool) : Bool :=
  groupByTuple || isSliced
    || anyPriorAggregate annos names havingFilter
    || distinct || combinator

/- The names retained in the produced SQL. When the count is nested and the
   query does NOT collapse duplicate rows: the added names together with
   everything they refer to (prior entries not referred to are dropped). When
   the count is nested but the query DOES collapse duplicate rows (`distinct`):
   pruning is suppressed — narrowing the visible entries could change which
   rows collapse — so every visible prior entry is retained alongside the
   added names. Otherwise (no nesting): just the added names (prior ones
   inlined away). -/
def keptNames (nesting distinct : Bool) (annos : List Annotation)
    (added : List Added) : List String :=
  if nesting then
    if distinct then
      added.map (·.name)
        ++ (annos.filter (isExisting (added.map (·.name)))).map (·.name)
    else maskFold added
  else added.map (·.name)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method countQueryShape
    (annos : List Annotation) (added : List Added)
    (groupByTuple : Bool) (isSliced : Bool) (distinct : Bool)
    (combinator : Bool) (havingFilter : Bool)
    return (res : Plan)
  ensures res.needsNesting =
    needsNesting annos (added.map (·.name))
      groupByTuple isSliced distinct combinator havingFilter
  ensures res.keptNames = keptNames res.needsNesting distinct annos added
  do
    -- impl-start
    let names := added.map (·.name)
    let existing := annos.filter (isExisting names)
    let priorAgg := (existing.any (fun a => a.isAggregate || a.isWindow)) || havingFilter
    let nesting := groupByTuple || isSliced || priorAgg || distinct || combinator
    let mut m : List String := []
    let mut i := added.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ added.length
      invariant m = maskFold (added.drop i)
      done_with i = 0
    do
      let a := added[i - 1]!
      m := (a.name :: referencedNames a.expr) ++ m
      i := i - 1
    let kept :=
      if nesting then
        if distinct then names ++ existing.map (·.name) else m
      else names
    return { needsNesting := nesting, keptNames := kept }
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `maskFold` peels one contribution. The single goal
   `loom_solve` leaves for the loop body. -/
lemma maskFold_drop_step (added : List Added) (i : Nat)
    (hi : 0 < i) (hle : i ≤ added.length) :
    maskFold (added.drop (i - 1))
      = ((added[i - 1]!).name :: referencedNames (added[i - 1]!).expr)
        ++ maskFold (added.drop i) := by
  have hlt : i - 1 < added.length := by omega
  have hcons : added.drop (i - 1) = added[i - 1]! :: added.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, maskFold_cons]

prove_correct countQueryShape by
  loom_solve
  · rw [maskFold_drop_step added i (by omega) (by omega)]
    simp_all
  all_goals simp_all [keptNames, needsNesting, anyPriorAggregate]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ adversarial refinement-fidelity audit for django__django-16263 (velvet). All commands: `cd && bash scripts/lean_verify.sh <file>`; same_spec via swebench_unified.markers.same_spec with get_backend('velvet').language. Verifications were run concurrently in two background batches (atk1-4, then atk5-7), ≤4 at a time.

STRUCTURAL FINDING: the spec is functionally tight. `Plan` has exactly two fields and BOTH postconditions pin them to exact equalities against the pure decision functions: `ensures res.needsNesting = needsNesting annos (added.map ·.name) groupByTuple isSliced distinct combinator havingFilter` and `ensures res.keptNames = keptNames res.needsNesting distinct annos added`, compared via derived DecidableEq. Any same-spec verifying impl is therefore forced to return the identical Plan on every input; no behavioral-deviation impl can verify. Consequently there are ZERO verifying wrong impls, hence NO faithful refined patches to materialize/resolve (patches={} by construction, not by omission).

### ATTACKS (all same_spec=True, all verified via lean_verify.sh):
- atk1_prepatch_d1 (prepatch D1 bug / ungrounded: priorAgg := !existing.isEmpty — nesting on mere presence of any prior selected anno; byte-identical priorAgg line to bundled Solution_prepatch.lean): exit 1, unsolved goal on ensures_2 (needsNesting). REJECTED.
- atk2_prepatch2_d2 (prepatch D2 bug: keep every existing anno unconditionally, even non-distinct nesting; mirrors bundled Solution_prepatch_2.lean): exit 1. REJECTED.
- atk3_partial_dropcombinator (partial-domain: drop `combinator` from nesting disjunction — correct only when combinator=false): exit 1, unsolved ensures_2 with residual `combinator = true -> ...`. REJECTED.
- atk4_boundary_allannos (boundary: distinct branch keeps annos.map name instead of existing/selected): exit 1, unsolved ensures_1. REJECTED.
- atk5_controlflow_keptnames (control-flow-effect: correct nesting computed but keptNames unconditionally set to added names, mask loop dead): exit 1, unsolved ensures_1. REJECTED.
- atk6_existing_noguard (boundary: existing filter drops the `!names.contains` guard, uses selected only): exit 1, both ensures_1 and ensures_2 unsolved. REJECTED.
- atk7_echo_oracle (ungrounded-oracle echo: return the spec pure functions verbatim): exit 1, `No goals to be solved` — the frozen proof block (maskFold_drop_step / loom_solve loop-body goals) no longer matches the loop-free impl, so even the exact-echo shape fails to verify unchanged. REJECTED.

Positive control: unmodified Solution.lean copied to positive_control.lean — verifies (exit 0), confirming toolchain and same_spec harness are sound (same_spec self = True).

prepatch_reproduced=True: atk1 reproduces the pre-patch D1 predicate (any prior annotation present) and atk2 the pre-patch D2 behaviour (retain every existing annotation); both correctly FAIL verification, confirming the spec discriminates the gold fix on both observable outcomes.

REFINEMENT.MD / A-LEG AUDIT: every leg is R, A-reference, or I; no kind-3 (Section C confirmed). A1/A2 (Annotation & added-name projections) = R; A3 (isExisting filter) = I under R; A4 (priorAgg incl. havingFilter) = I+R; A5 (5-way disjunction) = I; B2 (maskFold) = I; B3 (keptNames 3-branch) = I+R. The single patch-ADDED op get_refs is modeled DEEPLY as `referencedNames`/`referencedNamesList` (B1, A-reference+I), NOT axiomatized — no consumed axiom in bundle. A-reference correspondence verified against axiom_check.py: it applies the gold patch to /testbed, builds real Ref(alias,Value)/Func(*children,function='F') trees isomorphic to Expr, and asserts set(model_referenced_names(node)) == real_expr.get_refs() over 9 boundary + 20000 fuzz trees (seed 16263).

Model maps `.reference s ↦ [s]` ↔ Ref.get_refs={self.refs} and `.composite ↦ union over children` (concat, set-compared) ↔ BaseExpression.get_refs union over get_source_expressions — faithful. havingFilter (any(where.split_having_qualify()[1:])) and the Annotation field projections are observable R-inputs, correctly not axiomatized (mapping.md §3.2). conformance_check.py (G-CONF) shares the SAME real get_refs between shadow and oracle over 1e5 inputs (seed 16263), scoping the R/I decision algebra — consistent with the A-reference leg being G-AX's sole obligation.

Recorded meta.json gates: G-AX/G-CONF/G-DIFF/G-EQ/G-RESOLVE all pass, G-RESOLVE.resolved=True (gold patch resolves); G-LEAK relaxed (RELAXED_LEAKAGE.md present), G-PBT skip.

VERDICT: SOUND. ≥5 (7) distinct same-spec wrong impls across the mandated categories (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, plus the two prepatch reproductions) were all machine-checked and NONE verified; therefore no verifying-wrong-impl patch exists that could fail to resolve. verify⇒correct holds for this bundle. No resolve runs were required because no attack verified (materialize+resolve is conditional on a verifying wrong impl).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacked the spec for the faithfulness-break direction (spec too strong / drifts from real repo behavior). Could not find any diverging input; the modeled function agrees with the real callee everywhere I tested.

Modeled kernel: Query.get_aggregation (django/db/models/sql/query.py) via countQueryShape, producing (needsNesting, keptNames). Verified against the gold-patched worktree (base 321ecb40f4).

Checks performed:
1. Lean elaboration: scripts/lean_verify.sh on Solution.lean => EXIT 0 (clean, no sorry).
2. same_spec (swebench_unified.markers, velvet tables): Solution.lean spec region byte-identical to Solution_prepatch.lean AND Solution_prepatch_2.lean (both True) — G-DIFF integrity holds; prepatch variants differ only in impl.
3. G-CONF (conformance_check.py, seed=16263, 100000 fuzzed shapes) run against the REAL patched Django (real Ref/BaseExpression.get_refs in-container): 0 disagreements between shadow and oracle.
4. G-AX (axiom_check.py, 9 boundary + 20000 fuzz trees): referencedNames deep model == real get_refs, 0 divergences.
5. Manual trace of all 4 F2P/PASS tests (test_unused_aliased_aggregate_pruned, test_non_aggregate_annotation_pruned, test_unreferenced_aggregate_annotation_pruned, test_referenced_aggregate_annotation_kept) — model predictions match the asserted SQL shapes (select-count 1 vs 2, alias presence).
6. Independent probes of the REAL get_aggregation end-to-end (bypassing the re-transcribed oracle) on the branch NO test exercises — nesting AND distinct: (a) distinct+existing-nonagg+count => nested, existing alias retained (matches keptNames distinct branch: added ++ existing-selected); (b) distinct+existing-agg+avg => nested; (c) existing-agg + avg referencing it (non-distinct) => nested, referenced alias kept (matches maskFold: added ∪ refs). All consistent with the model.

Key modeling boundaries examined for over-strength:
- annotation_select vs annotations: A3 correctly models the switch to annotation_select as the `selected` filter; existing_annotations in oracle filters on selected — faithful.
- has_existing_aggregation restricts nesting trigger to selected annotations that aggregate/window OR having/qualify filter — matches patched query.py:449-473.
- keptNames three-way (nesting∧¬distinct => added∪refs; nesting∧distinct => added∪existing-selected, narrowing suppressed by `if not inner_query.distinct:` guard; ¬nesting => added) — matches patched source at query.py:483/486/498-503/534-547.

The spec models exactly the F2P-discriminating outcomes and no stronger; the deep get_refs model is validated by G-AX, not assumed. No divergence from real repo behavior found. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Relaxed-leakage bundle (meta.json relaxed_leakage=true, RELAXED_LEAKAGE.md present). Disposition re-verified INDEPENDENTLY, not rubber-stamped.

SPEC-REGION INTEGRITY: same_spec(Solution, prepatch)=True and same_spec(Solution, prepatch_2)=True via swebench_unified.markers.same_spec with velvet LanguageTables — spec regions byte-identical across all three twins.

CORE SOUNDNESS (re-run): G-VERIFY Solution.lean passes lean_verify.sh exit 0 (no sorry/axioms per axioms region). G-DIFF: Solution_prepatch.lean and Solution_prepatch_2.lean both FAIL verification (exit 1) — the D1 'any prior annotation present' twin and the D2' 'keep-all-existing when not distinct' twin fail for the intended reasons (ensures_2 / ensures_1 respectively).

PROBLEM_STATEMENT vs SPEC-VIEW re-scan: PS asks only to strip annotations 'not referenced by filters, other annotations or ordering' (example Book.objects.annotate(Count('chapters')).count()). Token scan of PS confirms: no aggregate-as-discriminator, no window/contains_over_clause, no having/qualify, no distinct, no combinator, no nested/subquery decision. The spec view leaks exactly the two dispositioned facets: (D1) the nesting discriminator — restricted to *selected* prior annotations that aggregate/window, or a HAVING/QUALIFY filter — via the Annotation docstring ('summarises rows (isAggregate) or is a windowed expression (isWindow)') and the anyPriorAggregate/needsNesting docstrings; (D2') the distinct guard suppressing mask-narrowing via the keptNames docstring and its `if distinct then … else maskFold added` branch.

UNAVOIDABILITY re-derived: D1 — the F2P tests (AggregateAnnotationPruningTests: test_non_aggregate_annotation_pruned, test_unused_aliased_aggregate_pruned) observe the nesting decision directly; the PS-consistent 'any prior present' rule (Solution_prepatch.lean) fails ensures_2, so a faithful spec MUST pin the aggregate/window/HAVING discriminator, which is provably absent from PS. D2' — omitting the distinct guard is unfaithful (panel-2 in-container repro on real patched Django, 2026-08-02); pinning it forces conditional-retention-under-distinct language the PS (unconditional strip, no mention of distinct) cannot contain. Both are the textbook RELAXED pattern. Note the D2 CORE (mask = added ∪ referenced-names in the non-distinct case) IS PS-derivable ('not referenced by filters, other annotations or ordering') and is correctly excluded from the relaxation.

NO NEW LEAK: the structural triggers exposed in needsNesting (groupByTuple/isSliced/distinct/combinator) are PRE-EXISTING base-commit conditions, not the gold edit, so exposing them leaks nothing beyond PS. No leaking line beyond the two dispositioned facets was found, and the disposition is not broken (core gates sound; no PS-only derivation of the aggregate/window nesting discriminator exists). Per the panel recording convention for a properly-dispositioned relaxed bundle, honest recording is NO-LEAKAGE (= pass): known dispositioned facets re-confirmed, no leak beyond them.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.