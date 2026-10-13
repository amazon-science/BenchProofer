# P2 adversarial audit — django__django-13028

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_false.lean`, `atk_true.lean`, `atk_prepatch.lean`, `atk_polarity.lean`, `atk_offbyone.lean`, `atk_partialdom.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_false.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. Every callee the modeled operation touches is an attribute read
@@ -50,18 +50,7 @@
   ensures raised = anyBad nodes
   do
     -- impl-start
-    let mut result : Bool := false
-    let mut i := nodes.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ nodes.length
-      invariant result = anyBad (nodes.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := nodes[i - 1]!
-      result := nodeBad n || result
-      i := i - 1
-    return result
+    return false
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the node at
@@ -79,6 +68,4 @@
   rw [hcons, anyBad_cons]
 
 prove_correct filterClauseRejected by
-  loom_solve
-  rw [anyBad_drop_step nodes i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

Attack 2 — `atk_true.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. Every callee the modeled operation touches is an attribute read
@@ -50,18 +50,7 @@
   ensures raised = anyBad nodes
   do
     -- impl-start
-    let mut result : Bool := false
-    let mut i := nodes.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ nodes.length
-      invariant result = anyBad (nodes.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := nodes[i - 1]!
-      result := nodeBad n || result
-      i := i - 1
-    return result
+    return true
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the node at
@@ -79,6 +68,4 @@
   rw [hcons, anyBad_cons]
 
 prove_correct filterClauseRejected by
-  loom_solve
-  rw [anyBad_drop_step nodes i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

Attack 3 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. Every callee the modeled operation touches is an attribute read
@@ -56,10 +56,9 @@
       invariant 0 ≤ i ∧ i ≤ nodes.length
       invariant result = anyBad (nodes.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := nodes[i - 1]!
-      result := nodeBad n || result
+      result := (!n.filterable) || result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_polarity.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. Every callee the modeled operation touches is an attribute read
@@ -56,10 +56,9 @@
       invariant 0 ≤ i ∧ i ≤ nodes.length
       invariant result = anyBad (nodes.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := nodes[i - 1]!
-      result := nodeBad n || result
+      result := (n.isOperand && n.filterable) || result
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_offbyone.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. Every callee the modeled operation touches is an attribute read
@@ -51,12 +51,11 @@
   do
     -- impl-start
     let mut result : Bool := false
-    let mut i := nodes.length
+    let mut i := nodes.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ nodes.length
       invariant result = anyBad (nodes.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := nodes[i - 1]!
       result := nodeBad n || result
```

Attack 6 — `atk_partialdom.lean` → rejected (same spec, does not verify — good)

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
 -- No axioms. Every callee the modeled operation touches is an attribute read
@@ -55,8 +55,8 @@
     while i > 0
       invariant 0 ≤ i ∧ i ≤ nodes.length
       invariant result = anyBad (nodes.drop i)
+      invariant result = false
       done_with i = 0
-      decreasing i
     do
       let n := nodes[i - 1]!
       result := nodeBad n || result
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- No axioms. Every callee the modeled operation touches is an attribute read
@@ -50,18 +50,7 @@
   ensures raised = anyBad nodes
   do
     -- impl-start
-    let mut result : Bool := false
-    let mut i := nodes.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ nodes.length
-      invariant result = anyBad (nodes.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let n := nodes[i - 1]!
-      result := nodeBad n || result
-      i := i - 1
-    return result
+    return anyBad nodes
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the node at
@@ -79,6 +68,4 @@
   rw [hcons, anyBad_cons]
 
 prove_correct filterClauseRejected by
-  loom_solve
-  rw [anyBad_drop_step nodes i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all <;> grind
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms. Every callee the modeled operation touches is an attribute read
-- or a structural traversal, modeled directly as a field of `Node` / as the
-- flattened node sequence (a type refinement, mapping.md §2); cross-language
-- soundness of those refinements is checked mechanically by G-CONF, so there
-- is no opaque callee to over-approximate here.
-- axioms-end

-- pure-start
/- One visited node of the operand tree. `filterable` is the node's own
   filterability flag (default-true elsewhere); `isOperand` records whether the
   node is a query operand — the kind of object whose filterability flag is
   meaningful — as opposed to a plain value supplied as a comparison target. -/
structure Node where
  filterable : Bool
  isOperand : Bool
  deriving Inhabited

/- A single node is offending exactly when it is a query operand AND declares
   itself non-filterable. A plain value (not an operand) never offends, even
   when it carries a false filterability flag. -/
def nodeBad (n : Node) : Bool := n.isOperand && !n.filterable

/- The whole traversal offends iff some visited node offends. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def anyBad : List Node → Bool
  | []      => false
  | n :: ns => nodeBad n || anyBad ns

@[grind] lemma anyBad_nil : anyBad [] = false := rfl
@[grind] lemma anyBad_cons (n : Node) (ns : List Node) :
    anyBad (n :: ns) = (nodeBad n || anyBad ns) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method filterClauseRejected (nodes : List Node) return (raised : Bool)
  ensures raised = anyBad nodes
  do
    -- impl-start
    let mut result : Bool := false
    let mut i := nodes.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ nodes.length
      invariant result = anyBad (nodes.drop i)
      done_with i = 0
    do
      let n := nodes[i - 1]!
      result := nodeBad n || result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the node at
   `i-1` on the front, so `anyBad` peels one `nodeBad`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma anyBad_drop_step (nodes : List Node) (i : Nat)
    (hi : 0 < i) (hle : i ≤ nodes.length) :
    anyBad (nodes.drop (i - 1)) = (nodeBad nodes[i - 1]! || anyBad (nodes.drop i)) := by
  have hlt : i - 1 < nodes.length := by omega
  have hcons : nodes.drop (i - 1) = nodes[i - 1]! :: nodes.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyBad_cons]

prove_correct filterClauseRejected by
  loom_solve
  rw [anyBad_drop_step nodes i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec: `filterClauseRejected (nodes : List Node) return (raised : Bool) ensures raised = anyBad nodes` — an EXACT functional-equality postcondition with NO preconditions, under partial correctness / demonic choice. anyBad = OR over nodes of (isOperand && !filterable).

### ATTACKS (all same_spec=True, verified with scripts/lean_verify.sh, 300s):
- 6 terminating wrong-value impls all FAIL to verify (exit 1), rejected by the postcondition/invariant: atk_false (return false; grind leaves ⊢False), atk_true (return true; ⊢False), atk_prepatch (drops isOperand — the prepatch bug; invariant_2 goal !filterable≠nodeBad), atk_polarity (isOperand&&filterable; invariant_2), atk_offbyone (start i at length-1; false=anyBad(drop(len-1)) unprovable), atk_partialdom (asserts result=false invariant; unprovable once a node offends).
- atk_echo (return anyBad nodes — the CORRECT oracle echo) VERIFIES (exit 0). Its faithful refined patch (== gold patch behaviorally) RESOLVES: run_resolve => RESOLVED=True COMPLETED=True. Per the derivation this is a correct echo, NOT a spec weakness.
- Positive control ctrl.lean (frozen Solution.lean) VERIFIES (exit 0). Solution_prepatch.lean FAILS for the right reason (exit 1).

WHY SOUND: the exact functional equality pins the return value, so EVERY terminating verifying impl is provably functionally correct (demonstrated: atk_echo verifies AND resolves). All 6 terminating wrong impls are rejected. The exact-equality postcondition has zero slack; there is no ungrounded-oracle/A-leg to echo (axioms=[], deep_model_references=[] — verified in meta.json; G-AX vacuous).

NON-TERMINATION PROBE (documented, deliberately NOT submitted as attacks): under the bundle's `termination "partial"` (framework-universal — 401/500 velvet Solutions use partial; G-HYGIENE only requires the option be PRESENT, not "total"), two same-spec impls verify vacuously: atk_nonterm.lean (loop increments i forever, done_with i=0 never reached) and atk_divergebad.lean (correct fold, then diverge iff result=true). I materialized atk_nonterm's faithful patch (patch_nonterm.diff, injects `while True: pass` into check_filterable; git apply --check APPLY_RC=0 — applies cleanly) and RAN it: run_resolve(timeout=900) => RESOLVED=False, COMPLETED=False (harness hung, no report).

This is a TIMEOUT (test-execution hang), NOT a completed-and-unresolved verdict — per _derive_audit_verdict, `not r.completed` => INCONCLUSIVE for that candidate, never BROKEN. Critically, a non-terminating loop is NOT a faithful refinement of any operation in refinement.md (which maps only the terminating structural DFS); `while True` fabricates behavior rather than refining a modeled callee, and the escape exists in every partial-correctness Hoare bundle independent of spec strength. Treating it as a break would falsely condemn the entire velvet corpus. Hence it is not a G-EQ refinement-fidelity defect.

REFINEMENT.MD AUDIT: every leg is R or I; the one changed operation (per-node guard) is modeled IDENTICALLY as nodeBad = isOperand && !filterable (matches the added `hasattr(...,'resolve_expression') and not getattr(...,'filterable',True)` conjunct); the surrounding DFS is a structural refinement (anyBad). No kind-3 leg. axioms=[] and deep_model_references=[] confirmed in meta.json — no A-consumed/A-reference legs to validate (G-AX vacuous). G-CONF passes 0/100008 (seed 13028). Refinement fidelity holds.

Commands: `bash scripts/lean_verify.sh <atk>.lean` for each file; same_spec via swebench_unified.markers.same_spec (all True); run_resolve via swebench_unified.harness.run_resolve for patch_echo.diff (RESOLVED=True) and patch_nonterm.diff (COMPLETED=False timeout). Full record: FINDINGS.md.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_false.lean`, `atk_true.lean`, `atk_prepatch.lean`, `atk_polarity.lean`, `atk_offbyone.lean`, `atk_partialdom.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `ctrl.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_false.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_true.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_polarity.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_offbyone.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_partialdom.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `ctrl.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms. Every callee the modeled operation touches is an attribute read
-- or a structural traversal, modeled directly as a field of `Node` / as the
-- flattened node sequence (a type refinement, mapping.md §2); cross-language
-- soundness of those refinements is checked mechanically by G-CONF, so there
-- is no opaque callee to over-approximate here.
-- axioms-end

-- pure-start
/- One visited node of the operand tree. `filterable` is the node's own
   filterability flag (default-true elsewhere); `isOperand` records whether the
   node is a query operand — the kind of object whose filterability flag is
   meaningful — as opposed to a plain value supplied as a comparison target. -/
structure Node where
  filterable : Bool
  isOperand : Bool
  deriving Inhabited

/- A single node is offending exactly when it is a query operand AND declares
   itself non-filterable. A plain value (not an operand) never offends, even
   when it carries a false filterability flag. -/
def nodeBad (n : Node) : Bool := n.isOperand && !n.filterable

/- The whole traversal offends iff some visited node offends. Front-recursive
   so a single unfold is available per loop step (the fold pattern, plan §5.4). -/
def anyBad : List Node → Bool
  | []      => false
  | n :: ns => nodeBad n || anyBad ns

@[grind] lemma anyBad_nil : anyBad [] = false := rfl
@[grind] lemma anyBad_cons (n : Node) (ns : List Node) :
    anyBad (n :: ns) = (nodeBad n || anyBad ns) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method filterClauseRejected (nodes : List Node) return (raised : Bool)
  ensures raised = anyBad nodes
  do
    -- impl-start
    let mut result : Bool := false
    let mut i := nodes.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ nodes.length
      invariant result = anyBad (nodes.drop i)
      done_with i = 0
    do
      let n := nodes[i - 1]!
      result := nodeBad n || result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the node at
   `i-1` on the front, so `anyBad` peels one `nodeBad`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma anyBad_drop_step (nodes : List Node) (i : Nat)
    (hi : 0 < i) (hle : i ≤ nodes.length) :
    anyBad (nodes.drop (i - 1)) = (nodeBad nodes[i - 1]! || anyBad (nodes.drop i)) := by
  have hlt : i - 1 < nodes.length := by omega
  have hcons : nodes.drop (i - 1) = nodes[i - 1]! :: nodes.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyBad_cons]

prove_correct filterClauseRejected by
  loom_solve
  rw [anyBad_drop_step nodes i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec: `filterClauseRejected (nodes : List Node) return (raised : Bool) ensures raised = anyBad nodes` — an EXACT functional-equality postcondition with NO preconditions, under partial correctness / demonic choice. anyBad = OR over nodes of (isOperand && !filterable).

### ATTACKS (all same_spec=True, verified with scripts/lean_verify.sh, 300s):
- 6 terminating wrong-value impls all FAIL to verify (exit 1), rejected by the postcondition/invariant: atk_false (return false; grind leaves ⊢False), atk_true (return true; ⊢False), atk_prepatch (drops isOperand — the prepatch bug; invariant_2 goal !filterable≠nodeBad), atk_polarity (isOperand&&filterable; invariant_2), atk_offbyone (start i at length-1; false=anyBad(drop(len-1)) unprovable), atk_partialdom (asserts result=false invariant; unprovable once a node offends).
- atk_echo (return anyBad nodes — the CORRECT oracle echo) VERIFIES (exit 0). Its faithful refined patch (== gold patch behaviorally) RESOLVES: run_resolve => RESOLVED=True COMPLETED=True. Per the derivation this is a correct echo, NOT a spec weakness.
- Positive control ctrl.lean (frozen Solution.lean) VERIFIES (exit 0). Solution_prepatch.lean FAILS for the right reason (exit 1).

WHY SOUND: the exact functional equality pins the return value, so EVERY terminating verifying impl is provably functionally correct (demonstrated: atk_echo verifies AND resolves). All 6 terminating wrong impls are rejected. The exact-equality postcondition has zero slack; there is no ungrounded-oracle/A-leg to echo (axioms=[], deep_model_references=[] — verified in meta.json; G-AX vacuous).

NON-TERMINATION PROBE (documented, deliberately NOT submitted as attacks): under the bundle's `termination "partial"` (framework-universal — 401/500 velvet Solutions use partial; G-HYGIENE only requires the option be PRESENT, not "total"), two same-spec impls verify vacuously: atk_nonterm.lean (loop increments i forever, done_with i=0 never reached) and atk_divergebad.lean (correct fold, then diverge iff result=true). I materialized atk_nonterm's faithful patch (patch_nonterm.diff, injects `while True: pass` into check_filterable; git apply --check APPLY_RC=0 — applies cleanly) and RAN it: run_resolve(timeout=900) => RESOLVED=False, COMPLETED=False (harness hung, no report).

This is a TIMEOUT (test-execution hang), NOT a completed-and-unresolved verdict — per _derive_audit_verdict, `not r.completed` => INCONCLUSIVE for that candidate, never BROKEN. Critically, a non-terminating loop is NOT a faithful refinement of any operation in refinement.md (which maps only the terminating structural DFS); `while True` fabricates behavior rather than refining a modeled callee, and the escape exists in every partial-correctness Hoare bundle independent of spec strength. Treating it as a break would falsely condemn the entire velvet corpus. Hence it is not a G-EQ refinement-fidelity defect.

REFINEMENT.MD AUDIT: every leg is R or I; the one changed operation (per-node guard) is modeled IDENTICALLY as nodeBad = isOperand && !filterable (matches the added `hasattr(...,'resolve_expression') and not getattr(...,'filterable',True)` conjunct); the surrounding DFS is a structural refinement (anyBad). No kind-3 leg. axioms=[] and deep_model_references=[] confirmed in meta.json — no A-consumed/A-reference legs to validate (G-AX vacuous). G-CONF passes 0/100008 (seed 13028). Refinement fidelity holds.

Commands: `bash scripts/lean_verify.sh <atk>.lean` for each file; same_spec via swebench_unified.markers.same_spec (all True); run_resolve via swebench_unified.harness.run_resolve for patch_echo.diff (RESOLVED=True) and patch_nonterm.diff (COMPLETED=False timeout). Full record: FINDINGS.md.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13028 velvet bundle.

Modeled function: Query.check_filterable (django/db/models/sql/query.py:1135, base_commit 78ad4b4b...). Patched real callee raises NotSupportedError iff SOME node visited (root + transitive get_source_expressions()) satisfies `hasattr(expression,'resolve_expression') and not getattr(expression,'filterable',True)`; otherwise returns None.

Model spec: `ensures raised = anyBad nodes` with `nodeBad n = n.isOperand && !n.filterable` and `anyBad` = OR of nodeBad over the flattened List Node. Carrier bijection (mapping.md §2): isOperand ↔ hasattr(resolve_expression); filterable ↔ getattr(filterable,True); raised ↔ raises; List Node ↔ multiset of all visited nodes.

Verification performed:
1. same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — spec region (imports/axioms/pure defs, method signature+ensures, helper lemma) is byte-identical to prepatch; the frozen spec is not tuned to the impl.
2. spec_view confirms the ensures clause `raised = anyBad nodes` and nodeBad definition are the audited spec.
3. lean_verify.sh on Solution.lean → exit 0 (elaborates, no sorry/error), so the spec is satisfiable/non-vacuous.
4. Point-by-point divergence hunt found NO diverging input:
   - Traversal order & short-circuit: real raises at first DFS offender; model ORs all nodes. Only observable is raise-or-not (order-independent), so equal.
   - Root + all descendants: List Node covers root and every recursively visited node — matches.
   - The patch's discriminating conjunct (isOperand) IS modeled (nodeBad requires isOperand). A non-operand non-filterable value → model false, real does not raise (no resolve_expression). Agree. Prepatch (which drops isOperand) correctly FAILS the spec, showing the spec captures the change and is not too weak.
   - Message string is unmodeled but the observable is deliberately scoped to raise-or-not (mapping.md §2) — a sound modeling boundary that does not affect the raise behavior or G-RESOLVE.

The spec is an exact abstraction of the patched callee over the carrier domain: neither too strong (no input where model raises but real does not) nor too weak (prepatch is rejected). No divergence exists. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean projected via spec_view/velvet) does not leak the gold edit beyond the public problem_statement.

Evidence:
- Mechanical G-LEAK screen passes: leakage.screen returns passed=True, hard_failures=[] (no diff markers, no gold-patch line reproduced, no patched file path/module, no patched-symbol echo, no bug/fix narration).
- Spec region is byte-identical between Solution.lean and Solution_prepatch.lean: swebench_unified.markers.same_spec(...)=True. The prepatch's edit-narrating comment ('Pre-image skeleton... not getattr(node,<flag>,True) WITHOUT checking operand... prove_correct MUST fail') lives entirely in the impl-start/impl-end region, which the spec-view projection strips, so it never reaches the consumer.
- Token scan of the spec view: none of resolve_expression, check_filterable, query.py, django/, NotSupported, getattr, hasattr, bug, fix, patch, previously, wrong, broken appear.
- The only distinctive patch-changed symbol is 'check_related_objects' (hunk section header); it is absent from the spec view.

The spec view does describe desired behavior (nodeBad n = n.isOperand && !n.filterable; 'a query operand AND non-filterable offends; a plain value never offends'), but this is the legitimate specification, not an edit disclosure. It names no repo symbol, reproduces no diff line, and narrates no fix. Moreover the operand-vs-plain-value distinction is already public in the problem_statement, which reports that a model with a filterable=False field is wrongly rejected by check_filterable when used as a comparison value in .filter(). The isOperand carve-out is the behavioral consequence of the publicly-described bug, not information beyond the problem statement (and it is judged against problem_statement only, not hints_text). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.