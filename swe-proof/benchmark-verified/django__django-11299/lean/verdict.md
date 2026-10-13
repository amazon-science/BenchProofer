# P2 adversarial audit — django__django-11299

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

Counterexample / evidence:

```
None. The spec problem_spec_resolveColumns bare q result := (result = expectedCol bare q) is a FULLY-PINNED exact equality against a fixed total function `expectedCol` living in the byte-identical pure region. Any impl that differs from expectedCol on any input makes `correct_resolveColumns` genuinely FALSE, so no proof (clean-axiom or otherwise) can close. I machine-proved this: for each of 6 distinct same-spec wrong impls I closed a `decide` counterexample (proj = ordered (field,bare) list) showing the impl's output differs from expectedCol on a concrete tree — e.g. atk_1 (prepatch bug, node child threaded `false`): implementation_resolveColumns true (node[node[leaf "x"]]) renders the nested leaf table-qualified while expectedCol renders it bare. No verifying wrong impl exists to serve as a spec-breaking counterexample.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,6 @@
 -- post-conditions-end
 
 -- impl-start
-/- Lower a filter expression to its column references. Walking each node's
-children in order: a leaf child is rendered directly (its column form taken from
-the global flag), and a node child is lowered recursively, THREADING the same
-global flag down into the recursion so deeply-nested leaves share it. -/
 mutual
 def implementation_resolveColumns (bare : Bool) : QTree → ColTree
   | .leaf field => buildLeaf bare field
@@ -92,35 +88,18 @@
       let built :=
         match child with
         | .leaf field => buildLeaf bare field
-        | .node _      => implementation_resolveColumns bare child
+        | .node _      => implementation_resolveColumns false child
       built :: resolveChildren bare rest
 end
 -- impl-end
 
 -- proof-start
-mutual
-theorem impl_eq_expected (bare : Bool) :
-    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
-  | .leaf field => rfl
-  | .node children => by
-      simp only [implementation_resolveColumns, expectedCol]
-      rw [impls_eq_expecteds bare children]
-theorem impls_eq_expecteds (bare : Bool) :
-    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
-  | [] => rfl
-  | c :: cs => by
-      simp only [resolveChildren, expectedCols]
-      rw [impls_eq_expecteds bare cs]
-      cases c with
-      | leaf field => rfl
-      | node ch => simp only [impl_eq_expected bare (.node ch)]
-end
-
 theorem correct_resolveColumns :
     ∀ (bare : Bool) (q : QTree),
       problem_spec_resolveColumns bare q
         (implementation_resolveColumns bare q) := by
   intro bare q
   unfold problem_spec_resolveColumns
-  exact impl_eq_expected bare q
+  induction q using QTree.rec <;>
+    simp_all [implementation_resolveColumns, resolveChildren, expectedCol, expectedCols, buildLeaf]
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,6 @@
 -- post-conditions-end
 
 -- impl-start
-/- Lower a filter expression to its column references. Walking each node's
-children in order: a leaf child is rendered directly (its column form taken from
-the global flag), and a node child is lowered recursively, THREADING the same
-global flag down into the recursion so deeply-nested leaves share it. -/
 mutual
 def implementation_resolveColumns (bare : Bool) : QTree → ColTree
   | .leaf field => buildLeaf bare field
@@ -91,36 +87,19 @@
   | child :: rest =>
       let built :=
         match child with
-        | .leaf field => buildLeaf bare field
+        | .leaf field => buildLeaf (!bare) field
         | .node _      => implementation_resolveColumns bare child
       built :: resolveChildren bare rest
 end
 -- impl-end
 
 -- proof-start
-mutual
-theorem impl_eq_expected (bare : Bool) :
-    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
-  | .leaf field => rfl
-  | .node children => by
-      simp only [implementation_resolveColumns, expectedCol]
-      rw [impls_eq_expecteds bare children]
-theorem impls_eq_expecteds (bare : Bool) :
-    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
-  | [] => rfl
-  | c :: cs => by
-      simp only [resolveChildren, expectedCols]
-      rw [impls_eq_expecteds bare cs]
-      cases c with
-      | leaf field => rfl
-      | node ch => simp only [impl_eq_expected bare (.node ch)]
-end
-
 theorem correct_resolveColumns :
     ∀ (bare : Bool) (q : QTree),
       problem_spec_resolveColumns bare q
         (implementation_resolveColumns bare q) := by
   intro bare q
   unfold problem_spec_resolveColumns
-  exact impl_eq_expected bare q
+  induction q using QTree.rec <;>
+    simp_all [implementation_resolveColumns, resolveChildren, expectedCol, expectedCols, buildLeaf]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,6 @@
 -- post-conditions-end
 
 -- impl-start
-/- Lower a filter expression to its column references. Walking each node's
-children in order: a leaf child is rendered directly (its column form taken from
-the global flag), and a node child is lowered recursively, THREADING the same
-global flag down into the recursion so deeply-nested leaves share it. -/
 mutual
 def implementation_resolveColumns (bare : Bool) : QTree → ColTree
   | .leaf field => buildLeaf bare field
@@ -89,38 +85,21 @@
 def resolveChildren (bare : Bool) : List QTree → List ColTree
   | [] => []
   | child :: rest =>
-      let built :=
+      let _built :=
         match child with
         | .leaf field => buildLeaf bare field
         | .node _      => implementation_resolveColumns bare child
-      built :: resolveChildren bare rest
+      resolveChildren bare rest
 end
 -- impl-end
 
 -- proof-start
-mutual
-theorem impl_eq_expected (bare : Bool) :
-    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
-  | .leaf field => rfl
-  | .node children => by
-      simp only [implementation_resolveColumns, expectedCol]
-      rw [impls_eq_expecteds bare children]
-theorem impls_eq_expecteds (bare : Bool) :
-    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
-  | [] => rfl
-  | c :: cs => by
-      simp only [resolveChildren, expectedCols]
-      rw [impls_eq_expecteds bare cs]
-      cases c with
-      | leaf field => rfl
-      | node ch => simp only [impl_eq_expected bare (.node ch)]
-end
-
 theorem correct_resolveColumns :
     ∀ (bare : Bool) (q : QTree),
       problem_spec_resolveColumns bare q
         (implementation_resolveColumns bare q) := by
   intro bare q
   unfold problem_spec_resolveColumns
-  exact impl_eq_expected bare q
+  induction q using QTree.rec <;>
+    simp_all [implementation_resolveColumns, resolveChildren, expectedCol, expectedCols, buildLeaf]
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,6 @@
 -- post-conditions-end
 
 -- impl-start
-/- Lower a filter expression to its column references. Walking each node's
-children in order: a leaf child is rendered directly (its column form taken from
-the global flag), and a node child is lowered recursively, THREADING the same
-global flag down into the recursion so deeply-nested leaves share it. -/
 mutual
 def implementation_resolveColumns (bare : Bool) : QTree → ColTree
   | .leaf field => buildLeaf bare field
@@ -92,35 +88,18 @@
       let built :=
         match child with
         | .leaf field => buildLeaf bare field
-        | .node _      => implementation_resolveColumns bare child
+        | .node _      => implementation_resolveColumns true child
       built :: resolveChildren bare rest
 end
 -- impl-end
 
 -- proof-start
-mutual
-theorem impl_eq_expected (bare : Bool) :
-    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
-  | .leaf field => rfl
-  | .node children => by
-      simp only [implementation_resolveColumns, expectedCol]
-      rw [impls_eq_expecteds bare children]
-theorem impls_eq_expecteds (bare : Bool) :
-    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
-  | [] => rfl
-  | c :: cs => by
-      simp only [resolveChildren, expectedCols]
-      rw [impls_eq_expecteds bare cs]
-      cases c with
-      | leaf field => rfl
-      | node ch => simp only [impl_eq_expected bare (.node ch)]
-end
-
 theorem correct_resolveColumns :
     ∀ (bare : Bool) (q : QTree),
       problem_spec_resolveColumns bare q
         (implementation_resolveColumns bare q) := by
   intro bare q
   unfold problem_spec_resolveColumns
-  exact impl_eq_expected bare q
+  induction q using QTree.rec <;>
+    simp_all [implementation_resolveColumns, resolveChildren, expectedCol, expectedCols, buildLeaf]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,49 +78,28 @@
 -- post-conditions-end
 
 -- impl-start
-/- Lower a filter expression to its column references. Walking each node's
-children in order: a leaf child is rendered directly (its column form taken from
-the global flag), and a node child is lowered recursively, THREADING the same
-global flag down into the recursion so deeply-nested leaves share it. -/
 mutual
 def implementation_resolveColumns (bare : Bool) : QTree → ColTree
-  | .leaf field => buildLeaf bare field
+  | .leaf field => buildLeaf true field
   | .node children => .node (resolveChildren bare children)
 def resolveChildren (bare : Bool) : List QTree → List ColTree
   | [] => []
   | child :: rest =>
       let built :=
         match child with
-        | .leaf field => buildLeaf bare field
+        | .leaf field => buildLeaf true field
         | .node _      => implementation_resolveColumns bare child
       built :: resolveChildren bare rest
 end
 -- impl-end
 
 -- proof-start
-mutual
-theorem impl_eq_expected (bare : Bool) :
-    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
-  | .leaf field => rfl
-  | .node children => by
-      simp only [implementation_resolveColumns, expectedCol]
-      rw [impls_eq_expecteds bare children]
-theorem impls_eq_expecteds (bare : Bool) :
-    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
-  | [] => rfl
-  | c :: cs => by
-      simp only [resolveChildren, expectedCols]
-      rw [impls_eq_expecteds bare cs]
-      cases c with
-      | leaf field => rfl
-      | node ch => simp only [impl_eq_expected bare (.node ch)]
-end
-
 theorem correct_resolveColumns :
     ∀ (bare : Bool) (q : QTree),
       problem_spec_resolveColumns bare q
         (implementation_resolveColumns bare q) := by
   intro bare q
   unfold problem_spec_resolveColumns
-  exact impl_eq_expected bare q
+  induction q using QTree.rec <;>
+    simp_all [implementation_resolveColumns, resolveChildren, expectedCol, expectedCols, buildLeaf]
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,10 +78,6 @@
 -- post-conditions-end
 
 -- impl-start
-/- Lower a filter expression to its column references. Walking each node's
-children in order: a leaf child is rendered directly (its column form taken from
-the global flag), and a node child is lowered recursively, THREADING the same
-global flag down into the recursion so deeply-nested leaves share it. -/
 mutual
 def implementation_resolveColumns (bare : Bool) : QTree → ColTree
   | .leaf field => buildLeaf bare field
@@ -93,34 +89,17 @@
         match child with
         | .leaf field => buildLeaf bare field
         | .node _      => implementation_resolveColumns bare child
-      built :: resolveChildren bare rest
+      resolveChildren bare rest ++ [built]
 end
 -- impl-end
 
 -- proof-start
-mutual
-theorem impl_eq_expected (bare : Bool) :
-    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
-  | .leaf field => rfl
-  | .node children => by
-      simp only [implementation_resolveColumns, expectedCol]
-      rw [impls_eq_expecteds bare children]
-theorem impls_eq_expecteds (bare : Bool) :
-    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
-  | [] => rfl
-  | c :: cs => by
-      simp only [resolveChildren, expectedCols]
-      rw [impls_eq_expecteds bare cs]
-      cases c with
-      | leaf field => rfl
-      | node ch => simp only [impl_eq_expected bare (.node ch)]
-end
-
 theorem correct_resolveColumns :
     ∀ (bare : Bool) (q : QTree),
       problem_spec_resolveColumns bare q
         (implementation_resolveColumns bare q) := by
   intro bare q
   unfold problem_spec_resolveColumns
-  exact impl_eq_expected bare q
+  induction q using QTree.rec <;>
+    simp_all [implementation_resolveColumns, resolveChildren, expectedCol, expectedCols, buildLeaf]
 -- proof-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -78,49 +78,17 @@
 -- post-conditions-end
 
 -- impl-start
-/- Lower a filter expression to its column references. Walking each node's
-children in order: a leaf child is rendered directly (its column form taken from
-the global flag), and a node child is lowered recursively, THREADING the same
-global flag down into the recursion so deeply-nested leaves share it. -/
-mutual
-def implementation_resolveColumns (bare : Bool) : QTree → ColTree
-  | .leaf field => buildLeaf bare field
-  | .node children => .node (resolveChildren bare children)
-def resolveChildren (bare : Bool) : List QTree → List ColTree
-  | [] => []
-  | child :: rest =>
-      let built :=
-        match child with
-        | .leaf field => buildLeaf bare field
-        | .node _      => implementation_resolveColumns bare child
-      built :: resolveChildren bare rest
-end
+def implementation_resolveColumns (bare : Bool) (q : QTree) : ColTree :=
+  expectedCol bare q
+def resolveChildren (bare : Bool) (qs : List QTree) : List ColTree :=
+  expectedCols bare qs
 -- impl-end
 
 -- proof-start
-mutual
-theorem impl_eq_expected (bare : Bool) :
-    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
-  | .leaf field => rfl
-  | .node children => by
-      simp only [implementation_resolveColumns, expectedCol]
-      rw [impls_eq_expecteds bare children]
-theorem impls_eq_expecteds (bare : Bool) :
-    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
-  | [] => rfl
-  | c :: cs => by
-      simp only [resolveChildren, expectedCols]
-      rw [impls_eq_expecteds bare cs]
-      cases c with
-      | leaf field => rfl
-      | node ch => simp only [impl_eq_expected bare (.node ch)]
-end
-
 theorem correct_resolveColumns :
     ∀ (bare : Bool) (q : QTree),
       problem_spec_resolveColumns bare q
         (implementation_resolveColumns bare q) := by
   intro bare q
-  unfold problem_spec_resolveColumns
-  exact impl_eq_expected bare q
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering the column references of a nested boolean filter expression.

A filter condition is a finite TREE. Each leaf names a single model field; each
interior node groups a list of sub-conditions (the children may themselves be
leaves or further interior nodes — nesting is arbitrary). When the tree is
lowered to its column references, every leaf is rendered as one of two column
forms:

  * a BARE column — just the field's column name; or
  * a TABLE-QUALIFIED column — the column name prefixed by its table.

Which form to use is a single boolean choice supplied once at the top of the
lowering. The contract is that this choice is GLOBAL: it applies uniformly to
every leaf of the tree, at every nesting depth. A leaf buried inside several
levels of grouping must be rendered in exactly the same form as a leaf sitting
at the top level. The grouping structure itself and each leaf's field are
carried through unchanged — only the per-leaf column form is decided here.

The salient point is uniformity: the rendering form must not silently differ
between shallow and deeply-nested leaves.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The only behavior the
-- lowering reads from a leaf is its field name, and the only decision it makes
-- is the column form dictated by the global boolean flag. That decision is a
-- total, deterministic function of (flag, field), so it is modeled directly as
-- the pure helper `buildLeaf` (a type refinement of the real per-leaf column
-- constructor) rather than axiomatized. Hence no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A boolean filter expression, restricted to the structure the lowering reads:
a `leaf` naming one field, or an interior `node` holding an ordered list of
children. -/
inductive QTree where
  | leaf (field : String)
  | node (children : List QTree)
  deriving Repr

/-- The lowered column-reference tree, mirroring the input shape. A `col` carries
the field's name and a boolean: `true` ⇒ bare column, `false` ⇒ table-qualified. -/
inductive ColTree where
  | col (field : String) (bare : Bool)
  | node (children : List ColTree)
  deriving Repr

/-- Render a single leaf to its column reference: the field is preserved and the
column form is exactly the global flag (`true` ⇒ bare, `false` ⇒ qualified). -/
def buildLeaf (bare : Bool) (field : String) : ColTree :=
  ColTree.col field bare

/- The canonical lowering: every leaf is rendered with the same global flag, at
every depth, and the grouping structure is preserved. Defined as a clean
structural fold over the input tree; this is the behavior the result is pinned to. -/
mutual
def expectedCol (bare : Bool) : QTree → ColTree
  | .leaf field => buildLeaf bare field
  | .node children => .node (expectedCols bare children)
def expectedCols (bare : Bool) : List QTree → List ColTree
  | [] => []
  | c :: cs => expectedCol bare c :: expectedCols bare cs
end
-- pure-end

-- post-conditions-start
/-- The lowered tree is fully pinned to the inputs: it equals the canonical
lowering of `q` under the global flag `bare`. This determines the grouping
structure, every leaf's field, and — uniformly at every depth — every leaf's
column form. No output component is left free. -/
def problem_spec_resolveColumns (bare : Bool) (q : QTree) (result : ColTree) : Prop :=
  result = expectedCol bare q
-- post-conditions-end

-- impl-start
/- Lower a filter expression to its column references. Walking each node's
children in order: a leaf child is rendered directly (its column form taken from
the global flag), and a node child is lowered recursively, THREADING the same
global flag down into the recursion so deeply-nested leaves share it. -/
mutual
def implementation_resolveColumns (bare : Bool) : QTree → ColTree
  | .leaf field => buildLeaf bare field
  | .node children => .node (resolveChildren bare children)
def resolveChildren (bare : Bool) : List QTree → List ColTree
  | [] => []
  | child :: rest =>
      let built :=
        match child with
        | .leaf field => buildLeaf bare field
        | .node _      => implementation_resolveColumns bare child
      built :: resolveChildren bare rest
end
-- impl-end

-- proof-start
mutual
theorem impl_eq_expected (bare : Bool) :
    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
  | .leaf field => rfl
  | .node children => by
      simp only [implementation_resolveColumns, expectedCol]
      rw [impls_eq_expecteds bare children]
theorem impls_eq_expecteds (bare : Bool) :
    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
  | [] => rfl
  | c :: cs => by
      simp only [resolveChildren, expectedCols]
      rw [impls_eq_expecteds bare cs]
      cases c with
      | leaf field => rfl
      | node ch => simp only [impl_eq_expected bare (.node ch)]
end

theorem correct_resolveColumns :
    ∀ (bare : Bool) (q : QTree),
      problem_spec_resolveColumns bare q
        (implementation_resolveColumns bare q) := by
  intro bare q
  unfold problem_spec_resolveColumns
  exact impl_eq_expected bare q
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: fresh /tmp scratch dir; impl region edited only (axioms/pure/pre/post byte-identical). same_spec=True confirmed for all 7 attacks + positive control via swebench_unified.markers.same_spec (lean).

POSITIVE CONTROL: pos_control.lean (unchanged gold Solution.lean) verifies exit=0; `#print axioms correct_resolveColumns` = [propext] (clean, no sorryAx/Classical-of-concern).

### ATTACKS (7 distinct same-spec wrong/echo impls, verifications run concurrently as background jobs ≤4):
  atk_1 partial/prepatch-bug: node child recursed with constant `false` (the exact prepatch defect) — lean_verify exit=1 (does NOT verify). Prepatch reproduced.
  atk_2 leaf-flag flip: leaf child buildLeaf (!bare) — exit=1.
  atk_3 control-flow-effect: drop first child (structure loss) — exit=1.
  atk_4 boundary/constant: node child recursed with constant `true` — exit=1.
  atk_5 constant-oracle: force every leaf bare=true both branches — exit=1.
  atk_6 control-flow-effect: reverse children order (rest ++ [built]) — exit=1.
  atk_7 ungrounded-oracle ECHO: implementation := expectedCol (behaviorally identical to gold) — lean_verify exit=0 (VERIFIES, clean).

TACTIC-STRENGTH CONTROL: atk_0_tacticcontrol.lean (CORRECT impl + the permissive induction/simp tactic) FAILS (exit=1) — so a bare exit=1 alone is not conclusive. I therefore additionally MACHINE-PROVED each wrong impl false: refute_1..6.lean each close a `decide` counterexample over a proj:ColTree→List(String×Bool) projection, all exit=3 with 0 errors (exit=3 = the deliberately-parked `sorry` on the now-false main theorem; the counterexample `example ... := by decide` closed with no error). This is decisive: the wrong impls are provably NOT extensionally equal to expectedCol, so `correct_resolveColumns` cannot be proved for them.

ECHO RESOLVE (mandatory per protocol — executed, not speculated): atk_7's faithful refined patch is exactly the gold patch (threading simple_col into the recursive _add_q call). Ran through official harness swebench_unified.harness.run_resolve → RESOLVED: True, COMPLETED: True, note 'resolved'. (First two attempts returned COMPLETED=False due to a missing instance image; I pulled mirror.gcr.io/swebench/sweb.eval.x86_64.django_1776_django-11299 + retagged to swebench/... per host policy, then the run completed and resolved.) Per the accepted echo-attack policy (G-PANEL-1/G-EQ), a same-spec verifying echo whose refined patch RESOLVES is NOT a weakness. No verifying attack has a non-resolving faithful patch, so verify⇏correct is NOT exhibited.

REFINEMENT.MD AUDIT (against real _add_q at base_commit 6866c91b, django/db/models/sql/query.py:1327-1354, obtained via a fresh worktree): all 6 legs are R / A-reference / I — NO kind-3 (inexpressible). Leg 4 is the only A leg (A-reference: buildLeaf ↔ else-branch build_filter→_get_col→SimpleCol/Col). Confirmed from source that the leaf else-branch already passes simple_col=simple_col and is UNCHANGED by the patch; _get_col is a total two-way SimpleCol/Col boolean selection faithfully modeled as buildLeaf bare field = ColTree.col field bare — deep model of an unchanged total callee, so NO axiom is consumed and the G-AX skip stub is legitimate (meta axioms=[], opaque_callees=[]). Leg 5 (R + fix site) correspondence verified: base_commit omits simple_col in the recursive _add_q call (defaults False), the patch adds it; prepatch Lean `...false child` = atk_1 = the observable bug. mapping.md type bijection is consistent with the source.

VERDICT: SOUND. ≥6 distinct wrong impls attempted; every one FAILS to verify AND is machine-proved unequal to expectedCol via a closing decide counterexample; the sole verifying attack is a gold-equivalent echo whose faithful patch was executed through run_resolve and RESOLVED. No impl with a closing clean-axiom proof has a non-resolving faithful patch. The exact-equality spec against a fixed pure oracle admits no verify⇏correct gap.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec problem_spec_resolveColumns bare q result := (result = expectedCol bare q) is a FULLY-PINNED exact equality against a fixed total function `expectedCol` living in the byte-identical pure region. Any impl that differs from expectedCol on any input makes `correct_resolveColumns` genuinely FALSE, so no proof (clean-axiom or otherwise) can close. I machine-proved this: for each of 6 distinct same-spec wrong impls I closed a `decide` counterexample (proj = ordered (field,bare) list) showing the impl's output differs from expectedCol on a concrete tree — e.g. atk_1 (prepatch bug, node child threaded `false`): implementation_resolveColumns true (node[node[leaf "x"]]) renders the nested leaf table-qualified while expectedCol renders it bare. No verifying wrong impl exists to serve as a spec-breaking counterexample.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering the column references of a nested boolean filter expression.

A filter condition is a finite TREE. Each leaf names a single model field; each
interior node groups a list of sub-conditions (the children may themselves be
leaves or further interior nodes — nesting is arbitrary). When the tree is
lowered to its column references, every leaf is rendered as one of two column
forms:

  * a BARE column — just the field's column name; or
  * a TABLE-QUALIFIED column — the column name prefixed by its table.

Which form to use is a single boolean choice supplied once at the top of the
lowering. The contract is that this choice is GLOBAL: it applies uniformly to
every leaf of the tree, at every nesting depth. A leaf buried inside several
levels of grouping must be rendered in exactly the same form as a leaf sitting
at the top level. The grouping structure itself and each leaf's field are
carried through unchanged — only the per-leaf column form is decided here.

The salient point is uniformity: the rendering form must not silently differ
between shallow and deeply-nested leaves.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The only behavior the
-- lowering reads from a leaf is its field name, and the only decision it makes
-- is the column form dictated by the global boolean flag. That decision is a
-- total, deterministic function of (flag, field), so it is modeled directly as
-- the pure helper `buildLeaf` (a type refinement of the real per-leaf column
-- constructor) rather than axiomatized. Hence no `opaque`/`axiom` callee
-- contract is needed.
-- axioms-end

-- pure-start
/-- A boolean filter expression, restricted to the structure the lowering reads:
a `leaf` naming one field, or an interior `node` holding an ordered list of
children. -/
inductive QTree where
  | leaf (field : String)
  | node (children : List QTree)
  deriving Repr

/-- The lowered column-reference tree, mirroring the input shape. A `col` carries
the field's name and a boolean: `true` ⇒ bare column, `false` ⇒ table-qualified. -/
inductive ColTree where
  | col (field : String) (bare : Bool)
  | node (children : List ColTree)
  deriving Repr

/-- Render a single leaf to its column reference: the field is preserved and the
column form is exactly the global flag (`true` ⇒ bare, `false` ⇒ qualified). -/
def buildLeaf (bare : Bool) (field : String) : ColTree :=
  ColTree.col field bare

/- The canonical lowering: every leaf is rendered with the same global flag, at
every depth, and the grouping structure is preserved. Defined as a clean
structural fold over the input tree; this is the behavior the result is pinned to. -/
mutual
def expectedCol (bare : Bool) : QTree → ColTree
  | .leaf field => buildLeaf bare field
  | .node children => .node (expectedCols bare children)
def expectedCols (bare : Bool) : List QTree → List ColTree
  | [] => []
  | c :: cs => expectedCol bare c :: expectedCols bare cs
end
-- pure-end

-- post-conditions-start
/-- The lowered tree is fully pinned to the inputs: it equals the canonical
lowering of `q` under the global flag `bare`. This determines the grouping
structure, every leaf's field, and — uniformly at every depth — every leaf's
column form. No output component is left free. -/
def problem_spec_resolveColumns (bare : Bool) (q : QTree) (result : ColTree) : Prop :=
  result = expectedCol bare q
-- post-conditions-end

-- impl-start
/- Lower a filter expression to its column references. Walking each node's
children in order: a leaf child is rendered directly (its column form taken from
the global flag), and a node child is lowered recursively, THREADING the same
global flag down into the recursion so deeply-nested leaves share it. -/
mutual
def implementation_resolveColumns (bare : Bool) : QTree → ColTree
  | .leaf field => buildLeaf bare field
  | .node children => .node (resolveChildren bare children)
def resolveChildren (bare : Bool) : List QTree → List ColTree
  | [] => []
  | child :: rest =>
      let built :=
        match child with
        | .leaf field => buildLeaf bare field
        | .node _      => implementation_resolveColumns bare child
      built :: resolveChildren bare rest
end
-- impl-end

-- proof-start
mutual
theorem impl_eq_expected (bare : Bool) :
    ∀ (q : QTree), implementation_resolveColumns bare q = expectedCol bare q
  | .leaf field => rfl
  | .node children => by
      simp only [implementation_resolveColumns, expectedCol]
      rw [impls_eq_expecteds bare children]
theorem impls_eq_expecteds (bare : Bool) :
    ∀ (qs : List QTree), resolveChildren bare qs = expectedCols bare qs
  | [] => rfl
  | c :: cs => by
      simp only [resolveChildren, expectedCols]
      rw [impls_eq_expecteds bare cs]
      cases c with
      | leaf field => rfl
      | node ch => simp only [impl_eq_expected bare (.node ch)]
end

theorem correct_resolveColumns :
    ∀ (bare : Bool) (q : QTree),
      problem_spec_resolveColumns bare q
        (implementation_resolveColumns bare q) := by
  intro bare q
  unfold problem_spec_resolveColumns
  exact impl_eq_expected bare q
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: fresh /tmp scratch dir; impl region edited only (axioms/pure/pre/post byte-identical). same_spec=True confirmed for all 7 attacks + positive control via swebench_unified.markers.same_spec (lean).

POSITIVE CONTROL: pos_control.lean (unchanged gold Solution.lean) verifies exit=0; `#print axioms correct_resolveColumns` = [propext] (clean, no sorryAx/Classical-of-concern).

### ATTACKS (7 distinct same-spec wrong/echo impls, verifications run concurrently as background jobs ≤4):
  atk_1 partial/prepatch-bug: node child recursed with constant `false` (the exact prepatch defect) — lean_verify exit=1 (does NOT verify). Prepatch reproduced.
  atk_2 leaf-flag flip: leaf child buildLeaf (!bare) — exit=1.
  atk_3 control-flow-effect: drop first child (structure loss) — exit=1.
  atk_4 boundary/constant: node child recursed with constant `true` — exit=1.
  atk_5 constant-oracle: force every leaf bare=true both branches — exit=1.
  atk_6 control-flow-effect: reverse children order (rest ++ [built]) — exit=1.
  atk_7 ungrounded-oracle ECHO: implementation := expectedCol (behaviorally identical to gold) — lean_verify exit=0 (VERIFIES, clean).

TACTIC-STRENGTH CONTROL: atk_0_tacticcontrol.lean (CORRECT impl + the permissive induction/simp tactic) FAILS (exit=1) — so a bare exit=1 alone is not conclusive. I therefore additionally MACHINE-PROVED each wrong impl false: refute_1..6.lean each close a `decide` counterexample over a proj:ColTree→List(String×Bool) projection, all exit=3 with 0 errors (exit=3 = the deliberately-parked `sorry` on the now-false main theorem; the counterexample `example ... := by decide` closed with no error). This is decisive: the wrong impls are provably NOT extensionally equal to expectedCol, so `correct_resolveColumns` cannot be proved for them.

ECHO RESOLVE (mandatory per protocol — executed, not speculated): atk_7's faithful refined patch is exactly the gold patch (threading simple_col into the recursive _add_q call). Ran through official harness swebench_unified.harness.run_resolve → RESOLVED: True, COMPLETED: True, note 'resolved'. (First two attempts returned COMPLETED=False due to a missing instance image; I pulled mirror.gcr.io/swebench/sweb.eval.x86_64.django_1776_django-11299 + retagged to swebench/... per host policy, then the run completed and resolved.) Per the accepted echo-attack policy (G-PANEL-1/G-EQ), a same-spec verifying echo whose refined patch RESOLVES is NOT a weakness. No verifying attack has a non-resolving faithful patch, so verify⇏correct is NOT exhibited.

REFINEMENT.MD AUDIT (against real _add_q at base_commit 6866c91b, django/db/models/sql/query.py:1327-1354, obtained via a fresh worktree): all 6 legs are R / A-reference / I — NO kind-3 (inexpressible). Leg 4 is the only A leg (A-reference: buildLeaf ↔ else-branch build_filter→_get_col→SimpleCol/Col). Confirmed from source that the leaf else-branch already passes simple_col=simple_col and is UNCHANGED by the patch; _get_col is a total two-way SimpleCol/Col boolean selection faithfully modeled as buildLeaf bare field = ColTree.col field bare — deep model of an unchanged total callee, so NO axiom is consumed and the G-AX skip stub is legitimate (meta axioms=[], opaque_callees=[]). Leg 5 (R + fix site) correspondence verified: base_commit omits simple_col in the recursive _add_q call (defaults False), the patch adds it; prepatch Lean `...false child` = atk_1 = the observable bug. mapping.md type bijection is consistent with the source.

VERDICT: SOUND. ≥6 distinct wrong impls attempted; every one FAILS to verify AND is machine-proved unequal to expectedCol via a closing decide counterexample; the sole verifying attack is a gold-equivalent echo whose faithful patch was executed through run_resolve and RESOLVED. No impl with a closing clean-axiom proof has a non-resolving faithful patch. The exact-equality spec against a fixed pure oracle admits no verify⇏correct gap.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous faithfulness audit of django__django-11299/lean (modeled fn: Query._add_q recursive Q-tree lowering; observable = per-leaf column FORM SimpleCol/bare vs Col/qualified as a fn of global simple_col flag and nesting depth).

MECHANICAL: lean_verify.sh Solution.lean exit 0 (compiles, no sorry). #print axioms correct_resolveColumns = [propext] only — genuine proof, no sorryAx. same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers with the lean backend: the spec region (axioms/pure/post-conditions, spec_view) is byte-identical between gold and prepatch; only impl op #5 (implementation_resolveColumns false child vs the threaded bare) and the proof differ. spec_view elides impl+proof as expected.

REAL CALLEE (fresh worktree at base_commit 6866c91b): build_where calls _add_q(..., simple_col=True) (query.py:1325). Base _add_q recurses on Node children WITHOUT threading simple_col (lines 1339-1341) so it defaults to False -> deeply-nested leaves lowered to qualified Col; gold threads simple_col into that recursive call. Verified line-for-line against mapping.md/refinement.md. Leaf children go build_filter(..., simple_col=simple_col) -> _get_col -> SimpleCol iff flag else Col. The second _get_col call site (line 1300, negated double-column isnull path) is guarded by lookup_type!='isnull' and requires is_nullable/LOUTER; is_nullable is False for the non-nullable single-table {num,name} fields, so it never fires and every modeled leaf yields exactly one column — the 'one column per leaf, form=global flag at every depth' spec (result = expectedCol bare q) is NOT too strong.

EMPIRICAL (ran conformance_check.py myself, seed=11299, N=100000, AND/OR + random negation + depth 5): BASE unpatched -> G-CONF FAIL 100000/100000 (bug reproduced: nested leaves render qualified/False); GOLD patched -> G-CONF OK 0/100000 (the model's all-bare prediction agrees with the real patched build_where on every input, including deep nesting). Abstraction (drop connector/negation/join bookkeeping; grouping modeled as opaque node) is sound because none of it affects the column form.

No diverging input exists within the modeled domain, and the domain is a legitimate abstraction of the fixed behavior. Spec is neither too strong nor drifted from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged over the spec view (problem_spec region + prose docstring + type defs; impl and proof regions are ELIDED as 'supplied by the consumer'), against the public problem_statement ONLY (not hints_text).

Mechanical screen (leakage.screen, lean flavor) PASSES with zero hard failures. same_spec(Solution, Solution_prepatch) == True — the spec view is byte-identical between the buggy and fixed variants, so it discriminates neither.

Gold edit: thread the `simple_col` flag into the recursive `self._add_q(child, ...)` call in django/db/models/sql/query.py:1338-1341. This mechanism/location lives entirely in the elided impl/proof regions; the spec view contains none of it.

No edit-localization leaks beyond problem_statement:
- Patched symbol `add_q` / `_add_q`, kwarg `simple_col`, and file path query.py do NOT appear in any spec-view identifier or comment.
- No diff markers; no narration terms (bug/fix/wrong/regression/etc.).
- Spec identifiers (QTree, ColTree, buildLeaf, expectedCol, resolveColumns, bare) are abstract model names, not repo symbols.

The docstring states the desired CORRECT contract — the column form is a single GLOBAL boolean applied uniformly to every leaf at every nesting depth. This is a spec's legitimate job and is already derivable from the public problem_statement, which explicitly reports that the bug appears with 'a combination of OR and AND clauses', that 'the AND clause items us[e] Col while the OR clause uses SimpleCol', names SimpleCol/Col/qualified column, and shows the desired correct SQL with every column bare. The terms 'nested'/'depth'/'uniform'/'global' are the spec author's abstraction of the same public fact (nested Q() grouping), not new gold information — they do not tell a solver WHERE or WHAT to edit (thread flag into recursive _add_q). No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
