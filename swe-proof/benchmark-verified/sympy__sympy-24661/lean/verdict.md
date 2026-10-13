# P2 adversarial audit — sympy__sympy-24661

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_01_prepatch_no_handler.lean`, `atk_02_partial_domain_drop_eq_ne.lean`, `atk_03_boundary_lt_le_swapped.lean`, `atk_04_control_flow_left_unvisited.lean`, `atk_05_flag_from_callee_table.lean`, `atk_09_flag_assign_not_or.lean`, `atk_10_shallow_operand_visit.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_06_ungrounded_oracle_echo.lean`, `atk_07_modeled_kinds_only_dispatch.lean`, `atk_08_double_visit_operands.lean`, `atk_11_build_then_revisit.lean`, `atk_12_build_then_visit_raw.lean`, `atk_13_arglist_walk_chain.lean` |

**Non-vacuity.** The positive control `ctl_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The postcondition problem_spec_transformRelational is FULLY PINNED in BOTH branches (some cls => result = app cls [transform left, transform right] true; none => result = cmp left op right), so any impl whose correct_* closes is POINTWISE EQUAL to the shipped gold impl. That is machine-checked, not argued: probe_equiv.lean (lean_verify exit 0, no sorryAx) proves eq06/eq07/eq08/eq11/eq12/eq13 : forall l o r, aN l o r = gold l o r for ALL SIX closing impls, using tidem/tsidem (transform idempotence) and visitOperand_eq. The SAME file proves sep01/sep02/sep03/sep04/sep05/sep09/sep10, so each of the 7 rejected impls is refuted by a CONCRETE differing input rather than by a proof-search artifact -- e.g. sep05 on (const 1,.lt,const 2) yields evalFalse=false where the spec demands true; sep09 on an operand ALREADY carrying the flag whose callee is outside the functions table (app "Integer" [1] true) shows assignment CLEARS a flag the real APPEND cannot; sep10 leaves a NESTED comparison operand un-rewritten. All 6 closing impls had their faithful refined patch MATERIALIZED and RUN through swebench_unified.harness.run_resolve: every one returned resolved=True with patch_successfully_applied=True, F2P failure=[] and P2P failure=[] (1/1 F2P, 27/27 P2P). No closing impl has a faithful patch that fails to resolve => verify=>correct holds on this bundle.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_01_prepatch_no_handler.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,15 +137,13 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
-  match relClassName op with
-  | some cls =>
-    let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
-  | none =>
-    return AstNode.cmp left op right
+  -- PRE-PATCH: EvaluateFalseTransformer has NO visit_Compare, so the generic
+  -- visitor hands the comparison node back unchanged for EVERY operator; a
+  -- recognised relational operator is never rebuilt as an unevaluated call.
+  return AstNode.cmp left op right
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_02_partial_domain_drop_eq_ne.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,15 +137,18 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
-  match relClassName op with
-  | some cls =>
-    let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
-  | none =>
-    return AstNode.cmp left op right
+  -- PARTIAL DOMAIN: the relational_operators table is populated with only the
+  -- four ORDERING operators; the two EQUALITY operators (== / !=) are omitted,
+  -- so `1 == 2` / `1 != 2` fall through unchanged.
+  match op with
+  | .lt => return AstNode.app "Lt" [transform left, transform right] true
+  | .le => return AstNode.app "Le" [transform left, transform right] true
+  | .gt => return AstNode.app "Gt" [transform left, transform right] true
+  | .ge => return AstNode.app "Ge" [transform left, transform right] true
+  | _   => return AstNode.cmp left op right
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_03_boundary_lt_le_swapped.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,15 +137,20 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
-  match relClassName op with
-  | some cls =>
-    let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
-  | none =>
-    return AstNode.cmp left op right
+  -- BOUNDARY: the strict / non-strict pair is transposed in the table
+  -- (ast.Lt -> 'Le', ast.LtE -> 'Lt'), an off-by-one on the comparison
+  -- boundary that the six-way-distinctness clause must catch.
+  match op with
+  | .lt    => return AstNode.app "Le" [transform left, transform right] true
+  | .le    => return AstNode.app "Lt" [transform left, transform right] true
+  | .gt    => return AstNode.app "Gt" [transform left, transform right] true
+  | .ge    => return AstNode.app "Ge" [transform left, transform right] true
+  | .eq    => return AstNode.app "Eq" [transform left, transform right] true
+  | .ne    => return AstNode.app "Ne" [transform left, transform right] true
+  | .other => return AstNode.cmp left op right
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_04_control_flow_left_unvisited.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,13 +137,16 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
+  -- CONTROL-FLOW EFFECT: `right = self.visit(node.comparators[0])` is performed
+  -- but the second recursive call is dropped -- `left = node.left` is used raw.
+  -- Half the operand recursion is missing.
   match relClassName op with
   | some cls =>
     let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
+    return AstNode.app cls [left, right'] true
   | none =>
     return AstNode.cmp left op right
 -- impl-end
```

Attack 5 — `atk_05_flag_from_callee_table.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,13 +137,18 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
+  -- UNGROUNDED FLAG SOURCE: instead of attaching `evaluate=False`
+  -- unconditionally, the new relational Call is routed through the SAME
+  -- `functions`-table test visit_Call uses, so the flag is attached only if the
+  -- relational constructor happened to be in that tuple (it is not).
   match relClassName op with
   | some cls =>
     let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
+    let left'  := transform left
+    return AstNode.app cls [left', right'] (isNonEvaluatingFunc cls)
   | none =>
     return AstNode.cmp left op right
 -- impl-end
```

Attack 6 — `atk_06_ungrounded_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,24 +137,27 @@
 -- post-conditions-end
 
 -- impl-start
+
+/-- UNGROUNDED-ORACLE ECHO: the impl does no work of its own, it simply names
+the postcondition's own right-hand side as a local function and returns it. -/
+def specOracle (l : AstNode) (o : RelOp) (r : AstNode) : AstNode :=
+  match relClassName o with
+  | some cls => AstNode.app cls [transform l, transform r] true
+  | none     => AstNode.cmp l o r
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
-  match relClassName op with
-  | some cls =>
-    let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
-  | none =>
-    return AstNode.cmp left op right
+  return specOracle left op right
 -- impl-end
 
 -- proof-start
+
 theorem correct_transformRelational :
     ∀ (left : AstNode) (op : RelOp) (right : AstNode),
       problem_spec_transformRelational left op right
         (implementation_transformRelational left op right) := by
   intro left op right
-  unfold problem_spec_transformRelational implementation_transformRelational
+  unfold problem_spec_transformRelational implementation_transformRelational specOracle
   cases h : relClassName op with
   | none => rfl
   | some cls => rfl
```

Attack 7 — `atk_07_modeled_kinds_only_dispatch.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,18 +137,33 @@
 -- post-conditions-end
 
 -- impl-start
+
+/-- The operand visit, open-coded over exactly the node kinds the model's
+`AstNode` fragment enumerates. Anything outside the fragment is, by the model's
+own accounting, returned unchanged. -/
+def visitOperand : AstNode → AstNode
+  | .const k       => AstNode.const k
+  | .name s        => AstNode.name s
+  | .app f args ef => AstNode.app f (transformArgs args) (ef || isNonEvaluatingFunc f)
+  | .cmp l o r     => transform (AstNode.cmp l o r)
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
   match relClassName op with
   | some cls =>
-    let right' := transform right
-    let left' := transform left
+    let right' := visitOperand right
+    let left'  := visitOperand left
     return AstNode.app cls [left', right'] true
   | none =>
     return AstNode.cmp left op right
 -- impl-end
 
 -- proof-start
+
+theorem visitOperand_eq : ∀ n : AstNode, visitOperand n = transform n := by
+  intro n
+  cases n <;> rfl
+
 theorem correct_transformRelational :
     ∀ (left : AstNode) (op : RelOp) (right : AstNode),
       problem_spec_transformRelational left op right
@@ -157,5 +172,5 @@
   unfold problem_spec_transformRelational implementation_transformRelational
   cases h : relClassName op with
   | none => rfl
-  | some cls => rfl
+  | some cls => simp only [Id.run, visitOperand_eq]; rfl
 -- proof-end
```

Attack 8 — `atk_08_double_visit_operands.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2] (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,18 +137,39 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
+  -- The operand is pushed through the visitor dispatch TWICE. In the MODEL this
+  -- is a no-op (`transform` is idempotent); the real dispatch's flag step is an
+  -- APPEND, so a second pass is not a no-op there.
   match relClassName op with
   | some cls =>
-    let right' := transform right
-    let left' := transform left
+    let right' := transform (transform right)
+    let left'  := transform (transform left)
     return AstNode.app cls [left', right'] true
   | none =>
     return AstNode.cmp left op right
 -- impl-end
 
 -- proof-start
+
+mutual
+theorem tidem : ∀ n : AstNode, transform (transform n) = transform n
+  | .const _ => rfl
+  | .name _ => rfl
+  | .app f args ef => by
+      simp [transform, tsidem args, isNonEvaluatingFunc, Bool.or_assoc]
+  | .cmp l o r => by
+      cases h : relClassName o with
+      | none => simp [transform, h]
+      | some cls => simp [transform, h, transformArgs, tidem l, tidem r]
+
+theorem tsidem : ∀ as : List AstNode, transformArgs (transformArgs as) = transformArgs as
+  | [] => rfl
+  | a :: rest => by simp [transformArgs, tidem a, tsidem rest]
+end
+
 theorem correct_transformRelational :
     ∀ (left : AstNode) (op : RelOp) (right : AstNode),
       problem_spec_transformRelational left op right
@@ -157,5 +178,5 @@
   unfold problem_spec_transformRelational implementation_transformRelational
   cases h : relClassName op with
   | none => rfl
-  | some cls => rfl
+  | some cls => simp only [Id.run, tidem]; rfl
 -- proof-end
```

Attack 9 — `atk_09_flag_assign_not_or.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,12 +137,21 @@
 -- post-conditions-end
 
 -- impl-start
+
+/-- The call arm with the flag ASSIGNED from the `functions` test rather than
+disjoined with the flag the node already carried -- i.e. reading
+`new_node.keywords = [evaluate=False] if in table else []` instead of the real
+`new_node.keywords.append(...)`. -/
+def visitCallAssign : AstNode → AstNode
+  | .app f args _  => AstNode.app f (transformArgs args) (isNonEvaluatingFunc f)
+  | n              => transform n
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
   match relClassName op with
   | some cls =>
-    let right' := transform right
-    let left' := transform left
+    let right' := visitCallAssign right
+    let left'  := visitCallAssign left
     return AstNode.app cls [left', right'] true
   | none =>
     return AstNode.cmp left op right
```

Attack 10 — `atk_10_shallow_operand_visit.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,12 +137,20 @@
 -- post-conditions-end
 
 -- impl-start
+
+/-- A one-level operand visit: the call arm is handled, but a NESTED comparison
+operand is handed back unchanged instead of being rebuilt (the recursion is not
+re-entered on a `Compare` child). -/
+def shallowVisit : AstNode → AstNode
+  | .app f args ef => AstNode.app f (transformArgs args) (ef || isNonEvaluatingFunc f)
+  | n              => n
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
   match relClassName op with
   | some cls =>
-    let right' := transform right
-    let left' := transform left
+    let right' := shallowVisit right
+    let left'  := shallowVisit left
     return AstNode.app cls [left', right'] true
   | none =>
     return AstNode.cmp left op right
```

Attack 11 — `atk_11_build_then_revisit.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,18 +137,37 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
   match relClassName op with
   | some cls =>
     let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
+    let left'  := transform left
+    -- the constructed relational call is pushed back through the dispatch
+    return transform (AstNode.app cls [left', right'] true)
   | none =>
     return AstNode.cmp left op right
 -- impl-end
 
 -- proof-start
+
+mutual
+theorem tidem : ∀ n : AstNode, transform (transform n) = transform n
+  | .const _ => rfl
+  | .name _ => rfl
+  | .app f args ef => by
+      simp [transform, tsidem args, isNonEvaluatingFunc, Bool.or_assoc]
+  | .cmp l o r => by
+      cases h : relClassName o with
+      | none => simp [transform, h]
+      | some cls => simp [transform, h, transformArgs, tidem l, tidem r]
+
+theorem tsidem : ∀ as : List AstNode, transformArgs (transformArgs as) = transformArgs as
+  | [] => rfl
+  | a :: rest => by simp [transformArgs, tidem a, tsidem rest]
+end
+
 theorem correct_transformRelational :
     ∀ (left : AstNode) (op : RelOp) (right : AstNode),
       problem_spec_transformRelational left op right
@@ -157,5 +176,8 @@
   unfold problem_spec_transformRelational implementation_transformRelational
   cases h : relClassName op with
   | none => rfl
-  | some cls => rfl
+  | some cls =>
+    simp only [Id.run, transform, transformArgs, tidem,
+               Bool.true_or, isNonEvaluatingFunc]
+    rfl
 -- proof-end
```

Attack 12 — `atk_12_build_then_visit_raw.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,18 +137,20 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
   match relClassName op with
   | some cls =>
-    let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
+    -- args are the RAW operands; the dispatch on the constructed node is what
+    -- rewrites them (`transformArgs`), and the flag survives (APPEND-only).
+    return transform (AstNode.app cls [left, right] true)
   | none =>
     return AstNode.cmp left op right
 -- impl-end
 
 -- proof-start
+
 theorem correct_transformRelational :
     ∀ (left : AstNode) (op : RelOp) (right : AstNode),
       problem_spec_transformRelational left op right
@@ -157,5 +159,7 @@
   unfold problem_spec_transformRelational implementation_transformRelational
   cases h : relClassName op with
   | none => rfl
-  | some cls => rfl
+  | some cls =>
+    simp only [Id.run, transform, transformArgs, Bool.true_or, isNonEvaluatingFunc]
+    rfl
 -- proof-end
```

Attack 13 — `atk_13_arglist_walk_chain.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -137,25 +137,30 @@
 -- post-conditions-end
 
 -- impl-start
+
 def implementation_transformRelational
     (left : AstNode) (op : RelOp) (right : AstNode) : AstNode := Id.run do
-  match relClassName op with
-  | some cls =>
-    let right' := transform right
-    let left' := transform left
-    return AstNode.app cls [left', right'] true
-  | none =>
-    return AstNode.cmp left op right
+  -- the table open-coded as an isinstance if/elif chain, and the operands
+  -- routed through the argument-list walk rather than two scalar visits.
+  match op with
+  | .other => return AstNode.cmp left op right
+  | .lt => return AstNode.app "Lt" (transformArgs [left] ++ transformArgs [right]) true
+  | .le => return AstNode.app "Le" (transformArgs [left] ++ transformArgs [right]) true
+  | .gt => return AstNode.app "Gt" (transformArgs [left] ++ transformArgs [right]) true
+  | .ge => return AstNode.app "Ge" (transformArgs [left] ++ transformArgs [right]) true
+  | .eq => return AstNode.app "Eq" (transformArgs [left] ++ transformArgs [right]) true
+  | .ne => return AstNode.app "Ne" (transformArgs [left] ++ transformArgs [right]) true
 -- impl-end
 
 -- proof-start
+
 theorem correct_transformRelational :
     ∀ (left : AstNode) (op : RelOp) (right : AstNode),
       problem_spec_transformRelational left op right
         (implementation_transformRelational left op right) := by
   intro left op right
   unfold problem_spec_transformRelational implementation_transformRelational
-  cases h : relClassName op with
-  | none => rfl
-  | some cls => rfl
+  cases op <;>
+    simp only [Id.run, relClassName, transformArgs, List.append,
+               List.cons_append, List.nil_append] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_positive.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Fresh scratch dir ONLY:  (base_commit worktree at <D>/wt from the upstream repository @ a36caf5c74fe654cedc488e8a8a05fad388f8406). 13 attacks, ALL same_spec=True against the shipped Solution.lean (re-checked AFTER every edit; axioms/pure/pre/post byte-identical, only impl+proof spliced by gen.py/gen2.py). Lean verifications and the axiom probes were launched as concurrent background jobs <=4 at a time (verify.sh / verify2.sh); the resolve runs likewise ran 4-way concurrent.

### COMMANDS (from swe-proof).
  verify: bash scripts/lean_verify.sh <D>/<f>.lean
  axioms: same script on ax_<f>.lean = <f>.lean + `#print axioms correct_transformRelational`
  resolve: python <D>/resolve.py <name>  -> swebench_unified.harness.run_resolve(instance_id, patch, timeout=1800, retries=2) -> <D>/resolve_<name>.json
  patches: <D>/mkpatch.py, produced by `git diff` in the pristine base_commit worktree (real hunk headers); ALL 7 pass `git apply --check` in <D>/wt.

### CONTROLS (non-vacuity, both required).
  ctl_positive.lean = shipped impl VERBATIM (diff -q vs Solution.lean: byte-identical) -> lean_verify exit 0; #print axioms -> "does not depend on any axioms".
  ctl_gold.patch (the shipped patch transcribed) -> run_resolve resolved=True, F2P failure=[], P2P failure=[]. The harness is live and discriminating.

**PREPATCH REPRODUCED:** atk_01_prepatch_no_handler (impl = `return AstNode.cmp left op right`, the base_commit behaviour of having no visit_Compare at all -- confirmed by AST inspection: base class EvaluateFalseTransformer @ 1102 has methods ['flatten','visit_BinOp','visit_Call'] and attrs ['operators','functions'], NO visit_Compare and NO relational_operators) -> lean_verify exit 1. Bug caught.

REJECTED, exit 1 (7 behaviourally-distinct wrong impls, each separated from gold in probe_equiv.lean):
  atk_01_prepatch_no_handler          exit 1  PREPATCH: no comparison handler at all (sep01)
  atk_02_partial_domain_drop_eq_ne    exit 1  PARTIAL DOMAIN: only the four ORDERING ops in the table; ==/!= fall through (sep02)
  atk_03_boundary_lt_le_swapped       exit 1  BOUNDARY: strict/non-strict pair transposed, Lt<->Le (sep03)
  atk_04_control_flow_left_unvisited  exit 1  CONTROL-FLOW EFFECT: only ONE of the two recursive visits performed; left used raw (sep04)
  atk_05_flag_from_callee_table       exit 1  UNGROUNDED FLAG SOURCE: evaluate=False read off the `functions` test instead of set unconditionally (sep05)
  atk_09_flag_assign_not_or           exit 1  APPEND-vs-ASSIGN: operand flag ASSIGNED rather than disjoined, so a flag already present is CLEARED (sep09)
  atk_10_shallow_operand_visit        exit 1  PARTIAL RECURSION: call arm handled but a NESTED comparison operand not rebuilt (sep10)

CLOSED with clean axioms -- EACH had its faithful patch MATERIALIZED and RUN through run_resolve (the mandatory leg; all results below are EXECUTED, not predicted):
  atk_06_ungrounded_oracle_echo       verify 0, no axioms      -> resolved=True  (UNGROUNDED-ORACLE ECHO: impl names the postcondition's own RHS as `specOracle` and returns it)
  atk_07_modeled_kinds_only_dispatch  verify 0, no axioms      -> resolved=True  (operand dispatch open-coded over the MODELED AstNode kinds only)
  atk_08_double_visit_operands        verify 0, [propext]      -> resolved=True  (self.visit(self.visit(child)) on each operand)
  atk_11_build_then_revisit           verify 0, [propext]      -> resolved=True  (visit operands, build the call, then RE-DISPATCH the constructed node)
  atk_12_build_then_visit_raw         verify 0, no axioms      -> resolved=True  (build from RAW operands, let the dispatch on the new node rewrite them)
  atk_13_arglist_walk_chain           verify 0, no axioms      -> resolved=True  (table open-coded as an isinstance if/elif chain; operands via the arg-list walk, LEFT-first order)
All axiom results are within STANDARD_AXIOMS (propext); grep for sorryAx over every ax_*.log: none. Every resolve JSON shows patch_successfully_applied=True, FAIL_TO_PASS success=1 failure=[], PASS_TO_PASS success=27 failure=[].

HOST-FLAKE DISCLOSURE (not spec verdicts). Three resolve attempts came back resolved=False with an EMPTY report and note "no report -- harness error or image pull failure ... docker.errors.ImageNotFound: 404 ... No such image sha256:...": the FIRST ctl_gold attempt and the FIRST atk_06 attempt. Both were re-run and both returned resolved=True (ctl_gold on attempt 2/3, atk_06 on attempt 3/3). Every one of the 7 patches has a final, completed, non-empty report; nothing needed is missing.

A-LEG AUDIT (my assigned focus; R/I legs left to G-CONF). meta.json: axioms=[], opaque_callees=[], deep_model_references=[], conf_skip=false, patch_equals_gold=true. Solution.lean's axioms region is COMMENT-ONLY -- grep ^(axiom|opaque|@[extern]) inside it finds NONE, and there is no sorry/admit/native_decide/Classical.choice anywhere in the file. refinement.md's table parses programmatically to 7 legs tagged 6x R + 1x I; the tag set is a subset of {R,A-consumed,A-reference,I}, with ZERO A-consumed and ZERO A-reference, hence NO kind-3 leg, and G-AX legitimately skips. The A-leg correspondence obligation is therefore VACUOUS, so I validated the deep-model claim that stands in its place -- the substantive risk here:

  (i) nonEvaluatingFuncs is byte-for-byte the real `functions` tuple: 35 names, ORDER-IDENTICAL, symmetric difference empty (AST-extracted from sympy/parsing/sympy_parser.py @ 1112-1118, UNCHANGED by the patch).

  (ii) relClassName equals the post-patch relational_operators dict exactly under mapping.md's bijection (ast.Lt->.lt etc.), and its six values are pairwise DISTINCT; .other -> none.

  (iii) leg 3a/3b's cited callee visit_Call really is, at line 1189, `new_node = self.generic_visit(node)` THEN a guarded `new_node.keywords.append(evaluate=False)` -- an APPEND that can only ADD the flag, which is exactly why the model's DISJUNCTION (evalFalse || isNonEvaluatingFunc func) rather than an assignment is the right shape. atk_09 is the attack that tests this, and the spec correctly REJECTS it.

  (iv) mapping.md's citations resolve in the worktree at base_commit (class @ 1102, dispatch @ 1095, visit_Call @ 1189).
refinement.md's central claim -- the changed op is modeled DEEPLY rather than axiomatized, so no callee contract is needed -- is accurate.

MODEL-FIDELITY OBSERVATIONS (advisory, explicitly NOT G-EQ breaks -- no closing impl fails to resolve; these belong to G-CONF/G-PANEL-2/PBT). I aimed atk_07/08/11 specifically at converting the model<->patch abstraction gap into a resolve failure, and MEASURED the gap directly with <D>/probe_gap.py (each faithful patch vs ctl_gold on 21 real parse_expr probes). The gap is WIDE and REAL, yet invisible to the graded oracle:

  (a) atk_08 and atk_11 each diverge on 6/21 probes: parse_expr('sin(0) < 2', evaluate=False) raises SyntaxError: keyword argument repeated: evaluate (likewise 'sqrt(0) >= 1', 'Abs(0) == 1', 'log(0) != 2', 'sin(cos(0)) < 2', '1 < sin(0)') where gold returns the unevaluated relational. Both are provably idempotent IN THE MODEL (tidem) but NOT in the repo, because the real flag step is an APPEND on a shared node, not a pure recomputation. Both still resolve.

  (b) atk_07 diverges on 6/21: it drops visit_BinOp on an operand (AstNode has no binary-operator constructor), so '1 + 2 < 3' parses to `3 < 3`, '`x*2` < 3' to `2*x < 3`, '2*(x+1) < 3' to `2*x + 2 < 3`, '-10/5 < 1' to `-2 < 1` -- operands EVALUATED, outright wrong parses -- and it crashes with AttributeError: 'Call' object has no attribute 'id' on 'f(0) < 2' / 'g(1) >= x' because it open-codes visit_Call WITHOUT the real isinstance(node.func, ast.Name) guard. It still resolves.

  (c) WHY the oracle cannot see any of this, measured rather than assumed: I instrumented visit_Compare and ran the ENTIRE graded test file (29 passed). visit_Compare is reached exactly 6 TIMES in the whole file, and every single call has the shape Compare(left=Call(Integer,[1]), ops=[Lt|LtE|Gt|GtE|Eq|NotEq], comparators=[Call(Integer,[2])]) -- the six F2P literals and nothing else. No P2P test reaches the comparison handler at all. So the discriminating operand categories (a functions-table call, an arithmetic BinOp, a non-Name callee, a nested comparison) are never exercised by the oracle, which is precisely why (a) and (b) resolve despite being genuinely wrong programs.

  (d) The visiting-order claim in refinement.md ops 2-3 (right bound before left) is truthfully stated but UNTESTED by the oracle: atk_13 reverses it to left-first and still resolves.
None of these lets a wrong impl verify-and-not-resolve, so G-EQ is SOUND. They are the honest targets for a future G-CONF/PBT strengthening, and they corroborate the prior pass's findings on the same bundle (independently re-derived here, with (c) newly quantified).

**WHY NO BREAK IS POSSIBLE ON THE MODELED FRAGMENT.** Because the postcondition pins the result EXACTLY in both branches, the set of impls that can close correct_* is a SINGLETON up to pointwise equality -- probe_equiv.lean proves all six survivors equal gold. A verify-but-not-resolve witness would have to be a closing impl that is a DIFFERENT function, and no such impl exists. The only remaining channel is the abstraction gap between the model and the real transformer, which I attacked head-on in atk_07/08/11: those ARE behaviourally wrong in the repo, but the gap lies entirely OUTSIDE the postcondition (the model is narrower than the callee), so it cannot be reached by a same-spec Lean impl -- and it is unreachable by the graded tests too, so it cannot flip a resolve either. Verdict SOUND, with the fidelity gap reported above for the gates that own it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 13 admissible attacks re-run of 13 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 13 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_01_prepatch_no_handler.lean`, `atk_02_partial_domain_drop_eq_ne.lean`, `atk_03_boundary_lt_le_swapped.lean`, `atk_04_control_flow_left_unvisited.lean`, `atk_05_flag_from_callee_table.lean`, `atk_09_flag_assign_not_or.lean`, `atk_10_shallow_operand_visit.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_06_ungrounded_oracle_echo.lean`, `atk_07_modeled_kinds_only_dispatch.lean`, `atk_08_double_visit_operands.lean`, `atk_11_build_then_revisit.lean`, `atk_12_build_then_visit_raw.lean`, `atk_13_arglist_walk_chain.lean` |

**Non-vacuity.** The positive control `ctl_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The postcondition problem_spec_transformRelational is FULLY PINNED in BOTH branches (some cls => result = app cls [transform left, transform right] true; none => result = cmp left op right), so any impl whose correct_* closes is POINTWISE EQUAL to the shipped gold impl. That is machine-checked, not argued: probe_equiv.lean (lean_verify exit 0, no sorryAx) proves eq06/eq07/eq08/eq11/eq12/eq13 : forall l o r, aN l o r = gold l o r for ALL SIX closing impls, using tidem/tsidem (transform idempotence) and visitOperand_eq. The SAME file proves sep01/sep02/sep03/sep04/sep05/sep09/sep10, so each of the 7 rejected impls is refuted by a CONCRETE differing input rather than by a proof-search artifact -- e.g. sep05 on (const 1,.lt,const 2) yields evalFalse=false where the spec demands true; sep09 on an operand ALREADY carrying the flag whose callee is outside the functions table (app "Integer" [1] true) shows assignment CLEARS a flag the real APPEND cannot; sep10 leaves a NESTED comparison operand un-rewritten. All 6 closing impls had their faithful refined patch MATERIALIZED and RUN through swebench_unified.harness.run_resolve: every one returned resolved=True with patch_successfully_applied=True, F2P failure=[] and P2P failure=[] (1/1 F2P, 27/27 P2P). No closing impl has a faithful patch that fails to resolve => verify=>correct holds on this bundle.
```

**Attacks re-run (13):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 13 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_01_prepatch_no_handler.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_02_partial_domain_drop_eq_ne.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_03_boundary_lt_le_swapped.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_04_control_flow_left_unvisited.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_05_flag_from_callee_table.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_06_ungrounded_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 7 — `atk_07_modeled_kinds_only_dispatch.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_08_double_visit_operands.lean` → correct echo (verifies AND its patch resolves — not a weakness) [resolved on attempt 2]

Attack 9 — `atk_09_flag_assign_not_or.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_shallow_operand_visit.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_build_then_revisit.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12_build_then_visit_raw.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13_arglist_walk_chain.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctl_positive.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** Fresh scratch dir ONLY:  (base_commit worktree at <D>/wt from the upstream repository @ a36caf5c74fe654cedc488e8a8a05fad388f8406). 13 attacks, ALL same_spec=True against the shipped Solution.lean (re-checked AFTER every edit; axioms/pure/pre/post byte-identical, only impl+proof spliced by gen.py/gen2.py). Lean verifications and the axiom probes were launched as concurrent background jobs <=4 at a time (verify.sh / verify2.sh); the resolve runs likewise ran 4-way concurrent.

### COMMANDS (from swe-proof).
  verify: bash scripts/lean_verify.sh <D>/<f>.lean
  axioms: same script on ax_<f>.lean = <f>.lean + `#print axioms correct_transformRelational`
  resolve: python <D>/resolve.py <name>  -> swebench_unified.harness.run_resolve(instance_id, patch, timeout=1800, retries=2) -> <D>/resolve_<name>.json
  patches: <D>/mkpatch.py, produced by `git diff` in the pristine base_commit worktree (real hunk headers); ALL 7 pass `git apply --check` in <D>/wt.

### CONTROLS (non-vacuity, both required).
  ctl_positive.lean = shipped impl VERBATIM (diff -q vs Solution.lean: byte-identical) -> lean_verify exit 0; #print axioms -> "does not depend on any axioms".
  ctl_gold.patch (the shipped patch transcribed) -> run_resolve resolved=True, F2P failure=[], P2P failure=[]. The harness is live and discriminating.

**PREPATCH REPRODUCED:** atk_01_prepatch_no_handler (impl = `return AstNode.cmp left op right`, the base_commit behaviour of having no visit_Compare at all -- confirmed by AST inspection: base class EvaluateFalseTransformer @ 1102 has methods ['flatten','visit_BinOp','visit_Call'] and attrs ['operators','functions'], NO visit_Compare and NO relational_operators) -> lean_verify exit 1. Bug caught.

REJECTED, exit 1 (7 behaviourally-distinct wrong impls, each separated from gold in probe_equiv.lean):
  atk_01_prepatch_no_handler          exit 1  PREPATCH: no comparison handler at all (sep01)
  atk_02_partial_domain_drop_eq_ne    exit 1  PARTIAL DOMAIN: only the four ORDERING ops in the table; ==/!= fall through (sep02)
  atk_03_boundary_lt_le_swapped       exit 1  BOUNDARY: strict/non-strict pair transposed, Lt<->Le (sep03)
  atk_04_control_flow_left_unvisited  exit 1  CONTROL-FLOW EFFECT: only ONE of the two recursive visits performed; left used raw (sep04)
  atk_05_flag_from_callee_table       exit 1  UNGROUNDED FLAG SOURCE: evaluate=False read off the `functions` test instead of set unconditionally (sep05)
  atk_09_flag_assign_not_or           exit 1  APPEND-vs-ASSIGN: operand flag ASSIGNED rather than disjoined, so a flag already present is CLEARED (sep09)
  atk_10_shallow_operand_visit        exit 1  PARTIAL RECURSION: call arm handled but a NESTED comparison operand not rebuilt (sep10)

CLOSED with clean axioms -- EACH had its faithful patch MATERIALIZED and RUN through run_resolve (the mandatory leg; all results below are EXECUTED, not predicted):
  atk_06_ungrounded_oracle_echo       verify 0, no axioms      -> resolved=True  (UNGROUNDED-ORACLE ECHO: impl names the postcondition's own RHS as `specOracle` and returns it)
  atk_07_modeled_kinds_only_dispatch  verify 0, no axioms      -> resolved=True  (operand dispatch open-coded over the MODELED AstNode kinds only)
  atk_08_double_visit_operands        verify 0, [propext]      -> resolved=True  (self.visit(self.visit(child)) on each operand)
  atk_11_build_then_revisit           verify 0, [propext]      -> resolved=True  (visit operands, build the call, then RE-DISPATCH the constructed node)
  atk_12_build_then_visit_raw         verify 0, no axioms      -> resolved=True  (build from RAW operands, let the dispatch on the new node rewrite them)
  atk_13_arglist_walk_chain           verify 0, no axioms      -> resolved=True  (table open-coded as an isinstance if/elif chain; operands via the arg-list walk, LEFT-first order)
All axiom results are within STANDARD_AXIOMS (propext); grep for sorryAx over every ax_*.log: none. Every resolve JSON shows patch_successfully_applied=True, FAIL_TO_PASS success=1 failure=[], PASS_TO_PASS success=27 failure=[].

HOST-FLAKE DISCLOSURE (not spec verdicts). Three resolve attempts came back resolved=False with an EMPTY report and note "no report -- harness error or image pull failure ... docker.errors.ImageNotFound: 404 ... No such image sha256:...": the FIRST ctl_gold attempt and the FIRST atk_06 attempt. Both were re-run and both returned resolved=True (ctl_gold on attempt 2/3, atk_06 on attempt 3/3). Every one of the 7 patches has a final, completed, non-empty report; nothing needed is missing.

A-LEG AUDIT (my assigned focus; R/I legs left to G-CONF). meta.json: axioms=[], opaque_callees=[], deep_model_references=[], conf_skip=false, patch_equals_gold=true. Solution.lean's axioms region is COMMENT-ONLY -- grep ^(axiom|opaque|@[extern]) inside it finds NONE, and there is no sorry/admit/native_decide/Classical.choice anywhere in the file. refinement.md's table parses programmatically to 7 legs tagged 6x R + 1x I; the tag set is a subset of {R,A-consumed,A-reference,I}, with ZERO A-consumed and ZERO A-reference, hence NO kind-3 leg, and G-AX legitimately skips. The A-leg correspondence obligation is therefore VACUOUS, so I validated the deep-model claim that stands in its place -- the substantive risk here:

  (i) nonEvaluatingFuncs is byte-for-byte the real `functions` tuple: 35 names, ORDER-IDENTICAL, symmetric difference empty (AST-extracted from sympy/parsing/sympy_parser.py @ 1112-1118, UNCHANGED by the patch).

  (ii) relClassName equals the post-patch relational_operators dict exactly under mapping.md's bijection (ast.Lt->.lt etc.), and its six values are pairwise DISTINCT; .other -> none.

  (iii) leg 3a/3b's cited callee visit_Call really is, at line 1189, `new_node = self.generic_visit(node)` THEN a guarded `new_node.keywords.append(evaluate=False)` -- an APPEND that can only ADD the flag, which is exactly why the model's DISJUNCTION (evalFalse || isNonEvaluatingFunc func) rather than an assignment is the right shape. atk_09 is the attack that tests this, and the spec correctly REJECTS it.

  (iv) mapping.md's citations resolve in the worktree at base_commit (class @ 1102, dispatch @ 1095, visit_Call @ 1189).
refinement.md's central claim -- the changed op is modeled DEEPLY rather than axiomatized, so no callee contract is needed -- is accurate.

MODEL-FIDELITY OBSERVATIONS (advisory, explicitly NOT G-EQ breaks -- no closing impl fails to resolve; these belong to G-CONF/G-PANEL-2/PBT). I aimed atk_07/08/11 specifically at converting the model<->patch abstraction gap into a resolve failure, and MEASURED the gap directly with <D>/probe_gap.py (each faithful patch vs ctl_gold on 21 real parse_expr probes). The gap is WIDE and REAL, yet invisible to the graded oracle:

  (a) atk_08 and atk_11 each diverge on 6/21 probes: parse_expr('sin(0) < 2', evaluate=False) raises SyntaxError: keyword argument repeated: evaluate (likewise 'sqrt(0) >= 1', 'Abs(0) == 1', 'log(0) != 2', 'sin(cos(0)) < 2', '1 < sin(0)') where gold returns the unevaluated relational. Both are provably idempotent IN THE MODEL (tidem) but NOT in the repo, because the real flag step is an APPEND on a shared node, not a pure recomputation. Both still resolve.

  (b) atk_07 diverges on 6/21: it drops visit_BinOp on an operand (AstNode has no binary-operator constructor), so '1 + 2 < 3' parses to `3 < 3`, '`x*2` < 3' to `2*x < 3`, '2*(x+1) < 3' to `2*x + 2 < 3`, '-10/5 < 1' to `-2 < 1` -- operands EVALUATED, outright wrong parses -- and it crashes with AttributeError: 'Call' object has no attribute 'id' on 'f(0) < 2' / 'g(1) >= x' because it open-codes visit_Call WITHOUT the real isinstance(node.func, ast.Name) guard. It still resolves.

  (c) WHY the oracle cannot see any of this, measured rather than assumed: I instrumented visit_Compare and ran the ENTIRE graded test file (29 passed). visit_Compare is reached exactly 6 TIMES in the whole file, and every single call has the shape Compare(left=Call(Integer,[1]), ops=[Lt|LtE|Gt|GtE|Eq|NotEq], comparators=[Call(Integer,[2])]) -- the six F2P literals and nothing else. No P2P test reaches the comparison handler at all. So the discriminating operand categories (a functions-table call, an arithmetic BinOp, a non-Name callee, a nested comparison) are never exercised by the oracle, which is precisely why (a) and (b) resolve despite being genuinely wrong programs.

  (d) The visiting-order claim in refinement.md ops 2-3 (right bound before left) is truthfully stated but UNTESTED by the oracle: atk_13 reverses it to left-first and still resolves.
None of these lets a wrong impl verify-and-not-resolve, so G-EQ is SOUND. They are the honest targets for a future G-CONF/PBT strengthening, and they corroborate the prior pass's findings on the same bundle (independently re-derived here, with (c) newly quantified).

**WHY NO BREAK IS POSSIBLE ON THE MODELED FRAGMENT.** Because the postcondition pins the result EXACTLY in both branches, the set of impls that can close correct_* is a SINGLETON up to pointwise equality -- probe_equiv.lean proves all six survivors equal gold. A verify-but-not-resolve witness would have to be a closing impl that is a DIFFERENT function, and no such impl exists. The only remaining channel is the abstraction gap between the model and the real transformer, which I attacked head-on in atk_07/08/11: those ARE behaviourally wrong in the repo, but the gap lies entirely OUTSIDE the postcondition (the model is narrower than the callee), so it cannot be reached by a same-spec Lean impl -- and it is unreachable by the graded tests too, so it cannot flip a resolve either. Verdict SOUND, with the fidelity gap reported above for the gates that own it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**ROLE:** faithfulness-break (is the spec too strong / does it drift from real repo behavior?). VERDICT: FAITHFUL — no diverging input found after ~890k differential comparisons against the REAL post-patch callee.

**REFERENCE DISCIPLINE:** modeled function's reference = worktree at base_commit a36caf5c74fe654cedc488e8a8a05fad388f8406 with patch.diff APPLIED. Verified the worktree's working diff is byte-identical to patch.diff (added-line diff empty, 'PATCH IDENTICAL', 23 insertions, 1 file). I did NOT compare against the base version, so the patch delta is not miscounted as drift.

### Lean gate
- scripts/lean_verify.sh Solution.lean -> EXIT=0 (elaborates, no sorry/error).
- #print axioms correct_transformRelational / transform / implementation_transformRelational -> all three 'does not depend on any axioms'. No sorryAx; proof is real. The axioms region is genuinely empty, consistent with refinement.md's claim that G-AX skips (every leg R or I, no A).

**SPEC-REGION IDENTITY:** markers.same_spec(Solution.lean, Solution_prepatch.lean) = True; region_hashes agree on axioms/pure/post-conditions/spec_view and differ only on impl+proof — exactly the retained-control shape (same spec, buggy impl).

NON-VACUITY (the control that matters): I did not merely observe the prepatch 'sorry'. I replaced the sorry with a REFUTATION and proved the negation: `¬ ∀ left op right, problem_spec (implementation ...)` closes at (const 1, .lt, const 2) via simp — lean_verify EXIT=0. So the postcondition genuinely REJECTS the buggy impl; the spec is load-bearing, not trivially satisfiable. (Guarded-self-call/vacuity concern discharged.)

INDEPENDENT DIFFERENTIAL HARNESS (mine, atk2c_diff.py — NOT the bundle's conformance_check.py, and not a replica sharing the model's transform): imported the real EvaluateFalseTransformer from the patched worktree, called its bound visit_Compare on genuine ast.Compare nodes, crossed the boundary with mapping.md §2's to_ast/from_ast bijection, and diffed against my own transliteration of the Lean pure region.
- 600,215 cases / 857,468 comparisons -> disagreements=0 (seed 913371, independent of the bundle's pinned SEED 24661).
- Corpus deliberately loaded on the discriminating arms: all 7 RelOp values incl. .other over 4 distinct non-table operator classes (Is/IsNot/In/NotIn); call operands with callees on BOTH sides of the 35-name `functions` table, arity 0-2, evaluate flag pre-set or absent; nested comparisons on both sides in every operator pairing; and deep call/comparison interleavings.

CONFIRMED THE TABLES ARE THE REAL ONES (not transcribed hopefully): EvaluateFalseTransformer.functions == the Lean nonEvaluatingFuncs list, 35 names, EQUAL AND ORDERED = True; relational_operators == {NotEq:Ne, Lt:Lt, LtE:Le, Gt:Gt, GtE:Ge, Eq:Eq}, matching relClassName exactly.

### OVER-CLAIM PROBES I RAN SPECIFICALLY TO BREAK THE SPEC (all agree with the real callee):
1. CHAINED COMPARISONS (strongest 'too strong' candidate — the model's cmp has ONE op, real ast.Compare has ops[]/comparators[] lists). Exhaustively drove 1-,2-,3-,4-length chains over all TEN comparison operators with 3 operand shifts = 33,330 cases -> disagreements=0. The real visit_Compare reads only ops[0]/comparators[0] and DISCARDS the tail (`1<2<3` -> Lt(1,2,evaluate=False), tail dropped), which is exactly mapping.md's declared truncation bijection. The spec is not stronger here.
2. IN-PLACE MUTATION / ALIASING (pure model vs mutating visitor). Fed the SAME Call object as both left and right operand: real output has the operand aliased (out.args[0] is out.args[1] = True) with the evaluate keyword appended TWICE (len(keywords)==2). Under the declared bijection evalFalse = 'an evaluate=False keyword is PRESENT' (existential, not a count), so multiplicity is not observable and the pure `transform` still agrees. Also checked nested aliasing (a node both as operand and inside another call's args) -> agrees. The disjunction `evalFalse || isNonEvaluatingFunc` is the right model precisely because append never clears a flag — confirmed empirically on sin(1, evaluate=False) < 2.
3. END-TO-END FROM SOURCE STRINGS (no hand-built nodes, so my own to_ast cannot mask a defect): 41,944 ast.parse-derived cases -> disagreements=0.
4. FRAGMENT-BOUNDARY SHAPES the model does not cover (BinOp, Attribute callee math.sin(1), non-Name callee f()(), Starred f(*args), **kw, keyword-value comparisons f(a=1<2), List, Lambda operands). All are OUTSIDE the AstNode fragment (mapping.md scopes operands to atoms/calls-with-Name-callee/nested comparisons), so the spec makes NO claim about them — this is under-claiming, which is safe for my lane, not over-claiming. Notably the spec does not assert visit_BinOp's arithmetic denesting, which it would have to if it claimed to cover `1+2 < 3`.
5. `.other` FALLTHROUGH: spec pins `result = cmp left op right` with UNTRANSFORMED operands. Verified the real `return node` leaves operands untouched even when they are in-table calls (`sin(1) is cos(2)` -> operands keep zero keywords). A spec that transformed the operands in the none-branch WOULD have been too strong; this one does not.

RESIDUAL (record hygiene, not a faithfulness defect, flagging for the rollup): meta.json's recorded region_hashes for axioms/pure/proof/spec_view no longer match the computed hashes of the current Solution.lean (post-conditions and impl DO match). Consistent with a prose/comment edit in the axioms+pure regions after the hashes were stamped. Since spec_signature covers docstrings, this can make retained attacks read as inadmissible and depress the admissible count — worth a re-stamp/re-digest, but the postcondition itself is unchanged and the spec is sound on the evidence above.

**BOTTOM LINE:** I could not find any input on which problem_spec_transformRelational disagrees with the real post-patch visit_Compare, including on the chaining and aliasing asymmetries that are the natural over-claim vectors here. No diverging input exists to cite, so I cannot claim FAITHFUL-is-a-defect. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction on the spec view of sympy__sympy-24661/lean. Verdict NO-LEAKAGE. Every claim below is my own measurement in this session; I did not inherit any disposition from the bundle.

0. NO RELAXATION IN THIS BUNDLE -- checked, not assumed. `find <instance dir> -iname '*relax*'` returns nothing (no RELAXED_LEAKAGE.md). A recursive walk of meta.json for a dict key `relaxed_leakage` returns zero occurrences (the substring 'relax' hits only inside prior-agent PROSE in meta.json/verdict.md, which is a note, not a key). meta.json gates['G-LEAK'].mode == 'strict', status == 'pass'. So there is no unavoidability argument to re-derive and no facet-scoped leak to bless: this is a plain strict review. I nonetheless ran the load-bearing test a relaxation would have to pass (item 5) as an independent non-vacuity check.

1. **SPEC-REGION IDENTITY.** swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) -> True. So the pre/post pair differ ONLY in the elided impl+proof regions; the spec view I judged is exactly what a consumer sees. patch.diff is byte-equal to instance.json['patch'] (compared directly). File hashes match every gate stamp in meta.json (Solution.lean e2920b08abb0..., properties.py aff81c5bdbeb...), so the record is fresh against the bytes I read -- the stale-stamp observation carried in the prior G-PANEL-3 note has since been restamped.

2. MECHANICAL SCREEN, RE-RUN BY ME. leakage.screen(Solution.lean, LeanBackend, gold_patch, problem_statement) -> hard_failures == [], warnings == []. Judged against problem_statement ONLY, never hints_text. I re-ran with problem_statement='' (harshest setting, no public credit at all) and it is STILL [] -- the spec view is clean even without leaning on the public issue text. Patch-changed symbols the screen derives are {EvaluateFalseTransformer, visit_Compare}; changed file sympy/parsing/sympy_parser.py.

3. MANUAL TOKEN SWEEP (the screen is a floor, not the review). Absent from the spec view: visit_Compare, EvaluateFalseTransformer, relational_operators, sympy_class, NodeTransformer, generic_visit, visit_Call, node.ops, comparators, NameConstant, starargs, keywords, 'ast.', sympy_parser, sympy/parsing, the F2P test name test_issue_24288, and the strings 24288/24661/'test_'. No gold ADDED line is reproduced (normalized, threshold lowered to >=6 chars, well below the screen's 8). No gold CONTEXT line either. No test-patch line. Narration regex run over the WHOLE view (not just comments, which is all the screen lexes): zero hits -- no bug/fix/patch/previously/incorrectly/wrong.

4. WHAT THE VIEW DOES SAY, AND WHY EACH ITEM IS PUBLIC. (a) `Lt(1, 2, evaluate=False)`, `1 < 2`, the boolean `True`, and the word 'relational' are all verbatim in the problem_statement (verified by substring test) -- the PS shows both the wrong output and the exact desired output, so 'rebuild the comparison as a call to the symbolic constructor with evaluate=False' is the PS's own Out[15], not the gold's mechanism. (b) The six operator/constructor pairs Lt/Le/Gt/Ge/Eq/Ne: the PS names the defect for 'relationals' as a CLASS and names Lt explicitly; the other five are SymPy's documented public relational constructors, the natural closure of that class. They localize no edit. (c) The `.other -> none` fallthrough ('any other comparison operator ... returned unchanged') is BASE-COMMIT behavior, not gold behavior: at base_commit the transformer has no comparison handler at all, so every comparison is returned unchanged. Stating it reveals the status quo the solver already has in the repo, not the edit. (d) nonEvaluatingFuncs (35 names): I diffed it against the base_commit `functions` tuple in my own fresh worktree (the upstream repository @ a36caf5c74fe654cedc488e8a8a05fad388f8406) -- IDENTICAL in content and order, and the gold patch adds/removes no line mentioning that tuple. It is therefore unpatched ambient repo context a solver reads directly, carrying zero information about the comparison rewrite. `evalFalse` embeds neither patched symbol (substring test).

5. LOAD-BEARING-PROSE CONTROL (the usual strip-the-narration test, run even though nothing here needed relaxing). I replaced the entire module docstring with the single abstract line '/-! Rewriting one comparison node. -/' in BOTH files and re-verified: StrippedGold -> exit 0, StrippedPre -> exit 3 ('declaration uses sorry'). So the discriminator lives entirely in the FORMAL postcondition (relClassName / transform / problem_spec_*), and no prose sentence is load-bearing -- the narration could be deleted without weakening the spec, which is the opposite of the situation a relaxation describes.

6. LEAN + NON-VACUITY, MY OWN RUNS. scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry). Appended `#print axioms correct_transformRelational` -> "does not depend on any axioms" (no sorryAx; the empty axioms region is legitimate since transform/transformArgs model the dispatch deeply). Solution_prepatch.lean -> exit 3, sorry at the correct_* theorem. So the postcondition genuinely discriminates fixed from buggy, and the spec view is not vacuously clean.

7. **NO FILE IN THE BUNDLE ADDRESSES ME.** I grepped Solution.lean, Solution_prepatch.lean, mapping.md, refinement.md, conformance_check.py and properties.py for reviewer/panel/auditor address, verdict instructions, and 'the honest verdict' phrasing -- zero hits. verdict.md and meta.json carry a PRIOR G-PANEL-3 note that already reads NO-LEAKAGE; I treated that as a record rather than a disposition and re-measured every item above from scratch, and I note it only so the record shows I did not echo it. No file attempted to steer my verdict, so there is no injection finding to report.

8. OUTSIDE MY FACET (flagged, not converted into a leakage finding). The modeled AstNode fragment has no binary-operator constructor, so it is NARROWER than the real visitor (visit_BinOp unmodeled). That is a faithfulness/thinness question for panel 2, on which I take no position; I note only that a model narrower than the real callee reveals LESS of the gold, so it cuts against leakage rather than toward it. Separately, the gold hunk's CONTEXT happens to include five of the functions-tuple names; they differ from the spec view only in quote style, and context lines are unchanged base-commit content the solver already has, so this is not edit-localizing either way.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
