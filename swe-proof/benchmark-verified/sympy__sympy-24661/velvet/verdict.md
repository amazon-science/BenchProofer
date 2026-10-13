# P2 adversarial audit — sympy__sympy-24661

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none found — the spec is not broken
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation is a pure dispatch over the kind of a
@@ -119,14 +119,7 @@
   ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
   do
     -- impl-start
-    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
-    -- into the matching symbolic relation constructor applied to the two
-    -- rewritten operands, held unevaluated; any other comparison kind is left
-    -- exactly as it is.
-    let out : Node :=
-      match relOf k with
-      | some rk => Node.relation rk false (visit l) (visit r)
-      | none    => Node.comparison k l r
+    let out : Node := Node.comparison k l r
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation is a pure dispatch over the kind of a
@@ -119,14 +119,13 @@
   ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
   do
     -- impl-start
-    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
-    -- into the matching symbolic relation constructor applied to the two
-    -- rewritten operands, held unevaluated; any other comparison kind is left
-    -- exactly as it is.
     let out : Node :=
-      match relOf k with
-      | some rk => Node.relation rk false (visit l) (visit r)
-      | none    => Node.comparison k l r
+      match k with
+      | .ne    => Node.comparison k l r
+      | _      =>
+        match relOf k with
+        | some rk => Node.relation rk false (visit l) (visit r)
+        | none    => Node.comparison k l r
     return out
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation is a pure dispatch over the kind of a
@@ -119,14 +119,14 @@
   ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
   do
     -- impl-start
-    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
-    -- into the matching symbolic relation constructor applied to the two
-    -- rewritten operands, held unevaluated; any other comparison kind is left
-    -- exactly as it is.
     let out : Node :=
-      match relOf k with
-      | some rk => Node.relation rk false (visit l) (visit r)
-      | none    => Node.comparison k l r
+      match k with
+      | .lt => Node.relation .Le false (visit l) (visit r)
+      | .le => Node.relation .Lt false (visit l) (visit r)
+      | _   =>
+        match relOf k with
+        | some rk => Node.relation rk false (visit l) (visit r)
+        | none    => Node.comparison k l r
     return out
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation is a pure dispatch over the kind of a
@@ -119,13 +119,9 @@
   ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
   do
     -- impl-start
-    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
-    -- into the matching symbolic relation constructor applied to the two
-    -- rewritten operands, held unevaluated; any other comparison kind is left
-    -- exactly as it is.
     let out : Node :=
       match relOf k with
-      | some rk => Node.relation rk false (visit l) (visit r)
+      | some rk => Node.relation rk true (visit l) (visit r)
       | none    => Node.comparison k l r
     return out
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation is a pure dispatch over the kind of a
@@ -119,13 +119,9 @@
   ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
   do
     -- impl-start
-    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
-    -- into the matching symbolic relation constructor applied to the two
-    -- rewritten operands, held unevaluated; any other comparison kind is left
-    -- exactly as it is.
     let out : Node :=
       match relOf k with
-      | some rk => Node.relation rk false (visit l) (visit r)
+      | some rk => Node.relation rk false (visit r) (visit l)
       | none    => Node.comparison k l r
     return out
     -- impl-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The operation is a pure dispatch over the kind of a
@@ -119,14 +119,7 @@
   ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
   do
     -- impl-start
-    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
-    -- into the matching symbolic relation constructor applied to the two
-    -- rewritten operands, held unevaluated; any other comparison kind is left
-    -- exactly as it is.
-    let out : Node :=
-      match relOf k with
-      | some rk => Node.relation rk false (visit l) (visit r)
-      | none    => Node.comparison k l r
+    let out : Node := rewriteCompare visit k l r
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The operation is a pure dispatch over the kind of a
@@ -119,13 +119,9 @@
   ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
   do
     -- impl-start
-    -- Dispatch on the comparison kind. An ordered/equality comparison is turned
-    -- into the matching symbolic relation constructor applied to the two
-    -- rewritten operands, held unevaluated; any other comparison kind is left
-    -- exactly as it is.
     let out : Node :=
       match relOf k with
-      | some rk => Node.relation rk false (visit l) (visit r)
+      | some rk => Node.relation rk false l r
       | none    => Node.comparison k l r
     return out
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation is a pure dispatch over the kind of a
--  comparison expression and is modeled DEEPLY in the `pure` region below. The
--  recursive rewrite of the two operand sub-expressions is an UNCHANGED
--  behaviour of the surrounding rewriter, abstracted as the free input `visit`,
--  about which the spec asserts nothing — so there is nothing to check against a
--  real callee. There is no `axiom` declaration and no A-reference deep model.)
-- axioms-end

-- pure-start
/- The comparison kinds an expression-rewriter can encounter, reduced to the
   only distinctions the rewrite reacts to:
     * `ne`  — "not equal";
     * `lt`  — "less than";
     * `le`  — "less than or equal";
     * `gt`  — "greater than";
     * `ge`  — "greater than or equal";
     * `eq`  — "equal";
     * `other` — any remaining comparison kind (identity, membership, …) that
                 the rewrite does not turn into a symbolic relation. -/
inductive CompareKind where
  | ne
  | lt
  | le
  | gt
  | ge
  | eq
  | other
  deriving Inhabited, DecidableEq

/- The symbolic relation constructors the six ordered/equality comparisons map
   to (the SymPy relational classes named in the issue: `Lt`, and its siblings). -/
inductive RelKind where
  | Ne
  | Lt
  | Le
  | Gt
  | Ge
  | Eq
  deriving Inhabited, DecidableEq

/- An expression node, reduced to the shapes this rewrite produces or preserves:
     * `leaf t`              — any operand sub-expression (opaque; identified by a
                               tag so distinct operands stay distinct);
     * `comparison k l r`    — a comparison expression of kind `k` over operands
                               `l`, `r` (the input shape, and the shape PRESERVED
                               for an unsupported comparison kind);
     * `relation rk built l r` — an application of the symbolic relation
                               constructor `rk` to `l`, `r`. The flag `built`
                               records whether the relation was built so that it
                               is held UNEVALUATED (`built = false`) — the only
                               way the comparison survives as a symbolic relation
                               instead of collapsing to a truth value. -/
inductive Node where
  | leaf (tag : Nat)
  | comparison (k : CompareKind) (l r : Node)
  | relation (rk : RelKind) (built : Bool) (l r : Node)
  deriving Inhabited, DecidableEq

/- The relation constructor an ordered/equality comparison maps to; the
   remaining comparison kinds have no symbolic-relation counterpart here. -/
def relOf : CompareKind → Option RelKind
  | .ne    => some .Ne
  | .lt    => some .Lt
  | .le    => some .Le
  | .gt    => some .Gt
  | .ge    => some .Ge
  | .eq    => some .Eq
  | .other => none

/- The rewrite of one comparison expression, modeled deeply. The desired
   behaviour, given the unchanged operand rewrite `visit`:
     * an ordered/equality comparison becomes an application of the matching
       symbolic relation constructor to the two REWRITTEN operands, held
       UNEVALUATED (`built = false`) so the comparison stays a symbolic relation
       rather than collapsing to a truth value;
     * any other comparison kind is left exactly as it is. -/
def rewriteCompare (visit : Node → Node) (k : CompareKind) (l r : Node) : Node :=
  match relOf k with
  | some rk => Node.relation rk false (visit l) (visit r)
  | none    => Node.comparison k l r
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rewrite a single comparison expression into the symbolic-relation form. An
   ordered/equality comparison (`<`, `<=`, `>`, `>=`, `==`, `!=`) becomes the
   matching relation constructor applied to the two rewritten operands and held
   unevaluated, so it survives as a symbolic relation rather than reducing to a
   truth value; every other comparison kind is preserved unchanged. `visit`,
   `k`, `l`, `r` are read-only (not `mut`); the rewrite computes a single node
   and mutates nothing (directive 5). -/
method rewriteComparison (visit : Node → Node) (k : CompareKind) (l : Node) (r : Node) return (out : Node)
  ensures out = rewriteCompare visit k l r
  -- A supported comparison becomes the matching relation, applied to the
  -- rewritten operands and held unevaluated. (Pins both the class and the
  -- unevaluated flag: an EVALUATED relation would collapse to a truth value.)
  ensures k = .lt → out = .relation .Lt false (visit l) (visit r)
  ensures k = .le → out = .relation .Le false (visit l) (visit r)
  ensures k = .gt → out = .relation .Gt false (visit l) (visit r)
  ensures k = .ge → out = .relation .Ge false (visit l) (visit r)
  ensures k = .eq → out = .relation .Eq false (visit l) (visit r)
  ensures k = .ne → out = .relation .Ne false (visit l) (visit r)
  -- An unsupported comparison kind is preserved exactly.
  ensures relOf k = none → out = .comparison k l r
  -- Whenever a relation is produced it is held unevaluated.
  ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
  do
    -- impl-start
    let out : Node :=
      match relOf k with
      | some rk => Node.relation rk false (visit l) (visit r)
      | none    => Node.comparison k l r
    return out
    -- impl-end

prove_correct rewriteComparison by
  loom_solve
  all_goals cases k <;> simp_all [rewriteCompare, relOf]
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity) audit of velvet bundle sympy__sympy-24661, run Project root; venv python;.

SPEC SHAPE: The frozen method rewriteComparison carries a COMPLETE functional postcondition `ensures out = rewriteCompare visit k l r` (line 106) PLUS six per-operator relation clauses, the .other-preservation clause, and the always-unevaluated (built=false) clause. Because the first ensures pins out to the exact modeled function on the WHOLE modeled domain (CompareKind x Node x Node, for every free `visit`), any verifying impl is I/O-identical to gold on that domain. This is a maximally-tight spec: verify ⇒ correct on the modeled domain.

SAME_SPEC: all 8 files confirmed True via swebench_unified.markers.same_spec(gold, atk, VelvetBackend.language). Only the impl region (impl-start..impl-end) was edited; axioms/pure/pre/post byte-identical.

### ATTACKS (each: `bash scripts/lean_verify.sh <path>`, run concurrently in 2 batches of 4):
- atk_1 (PREPATCH BUG reproduced): out := .comparison k l r (no comparison clause, fallthrough). EXIT=1, unsolved goals at 126:32. => prepatch_reproduced=true.
- atk_2 (partial-domain): drops .ne to a preserved comparison, rest gold. EXIT=1, unsolved goals 132:32.
- atk_3 (boundary/rel-swap): lt->Le, le->Lt swapped. EXIT=1, unsolved goals 133:32.
- atk_4 (control-flow-effect): builds relation but EVALUATED (built=true). EXIT=1, unsolved goals 129:32. (Killed by both the per-op clauses and the always-unevaluated clause.)
- atk_5 (operand-order swap): .relation rk false (visit r) (visit l). EXIT=1, unsolved goals 129:32.
- atk_6 (ungrounded-oracle ECHO): out := rewriteCompare visit k l r verbatim. EXIT=0 VERIFIES. This is behaviorally IDENTICAL to gold (returns the exact modeled decision).
- atk_7 (skip-visit): .relation rk false l r (raw operands, no recursive rewrite). EXIT=1, unsolved goals 129:32.
Positive control (gold-faithful impl): pos_control.lean EXIT=0 verifies.

So 6/7 genuinely-wrong impls FAIL verification; the only verifier is the gold-equivalent echo (atk_6).

RESOLVE (protocol step 2): For the one verifying impl atk_6, materialized its faithful refined patch. Since atk_6 returns rewriteCompare verbatim = the exact modeled node-shape decision, its faithful Python transliteration IS the gold visit_Compare clause (relational_operators dict + Call(Name(cls),[visit(left),visit(right)],evaluate=False), else return node). Ran it through the OFFICIAL harness: swebench_unified.harness.run_resolve('sympy__sympy-24661', patch, timeout=1800, retries=1) => RESOLVED=True COMPLETED=True NOTE='resolved'. The verifying impl's faithful patch RESOLVES, so verify⇏correct is NOT exhibited.

REFINEMENT.MD AUDIT: legs A1-A6 are all tagged R or I (A1/A2/A3 R type-refinements: operator-class/CompareKind, free visit:Node->Node, operands/Node; A4/A5/A6 I: relOf=membership+lookup, some-branch relation constructor with evaluate=False<->built=false, none-branch preserved Compare). NO axioms, NO A-reference, NO kind-3. meta.json axioms=[] and deep_model_references=[] corroborate. §C correctly states there are no consumed axioms; the sole callee `visit` is UNCHANGED by the patch and abstracted as a free total input the spec asserts nothing about (mapping.md §3) — so there is no relied-on property to check against a real callee, and the model↔patch correspondence holds. The A-legs are sound; the deep model (relOf/rewriteCompare + built flag) faithfully mirrors the gold node-shape decision. G-CONF's differential (seed 24661, 100020 inputs, 0 disagreements) transliterates the same decision and passes.

VERDICT: SOUND. 7 same-spec attacks encoded and machine-verified (prior-pass echo re-encoded + prepatch bug + partial-domain + boundary/rel-swap + control-flow-effect + operand-order + skip-visit); all 6 genuinely-wrong impls fail verification; the single verifying impl (gold-equivalent echo) has a faithful patch that RESOLVES under the official harness (executed, not speculated). The complete-functional-postcondition spec admits no verifying-but-wrong impl on the modeled domain. No counterexample exists; spec is not broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
none found — the spec is not broken
```

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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The operation is a pure dispatch over the kind of a
--  comparison expression and is modeled DEEPLY in the `pure` region below. The
--  recursive rewrite of the two operand sub-expressions is an UNCHANGED
--  behaviour of the surrounding rewriter, abstracted as the free input `visit`,
--  about which the spec asserts nothing — so there is nothing to check against a
--  real callee. There is no `axiom` declaration and no A-reference deep model.)
-- axioms-end

-- pure-start
/- The comparison kinds an expression-rewriter can encounter, reduced to the
   only distinctions the rewrite reacts to:
     * `ne`  — "not equal";
     * `lt`  — "less than";
     * `le`  — "less than or equal";
     * `gt`  — "greater than";
     * `ge`  — "greater than or equal";
     * `eq`  — "equal";
     * `other` — any remaining comparison kind (identity, membership, …) that
                 the rewrite does not turn into a symbolic relation. -/
inductive CompareKind where
  | ne
  | lt
  | le
  | gt
  | ge
  | eq
  | other
  deriving Inhabited, DecidableEq

/- The symbolic relation constructors the six ordered/equality comparisons map
   to (the SymPy relational classes named in the issue: `Lt`, and its siblings). -/
inductive RelKind where
  | Ne
  | Lt
  | Le
  | Gt
  | Ge
  | Eq
  deriving Inhabited, DecidableEq

/- An expression node, reduced to the shapes this rewrite produces or preserves:
     * `leaf t`              — any operand sub-expression (opaque; identified by a
                               tag so distinct operands stay distinct);
     * `comparison k l r`    — a comparison expression of kind `k` over operands
                               `l`, `r` (the input shape, and the shape PRESERVED
                               for an unsupported comparison kind);
     * `relation rk built l r` — an application of the symbolic relation
                               constructor `rk` to `l`, `r`. The flag `built`
                               records whether the relation was built so that it
                               is held UNEVALUATED (`built = false`) — the only
                               way the comparison survives as a symbolic relation
                               instead of collapsing to a truth value. -/
inductive Node where
  | leaf (tag : Nat)
  | comparison (k : CompareKind) (l r : Node)
  | relation (rk : RelKind) (built : Bool) (l r : Node)
  deriving Inhabited, DecidableEq

/- The relation constructor an ordered/equality comparison maps to; the
   remaining comparison kinds have no symbolic-relation counterpart here. -/
def relOf : CompareKind → Option RelKind
  | .ne    => some .Ne
  | .lt    => some .Lt
  | .le    => some .Le
  | .gt    => some .Gt
  | .ge    => some .Ge
  | .eq    => some .Eq
  | .other => none

/- The rewrite of one comparison expression, modeled deeply. The desired
   behaviour, given the unchanged operand rewrite `visit`:
     * an ordered/equality comparison becomes an application of the matching
       symbolic relation constructor to the two REWRITTEN operands, held
       UNEVALUATED (`built = false`) so the comparison stays a symbolic relation
       rather than collapsing to a truth value;
     * any other comparison kind is left exactly as it is. -/
def rewriteCompare (visit : Node → Node) (k : CompareKind) (l r : Node) : Node :=
  match relOf k with
  | some rk => Node.relation rk false (visit l) (visit r)
  | none    => Node.comparison k l r
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Rewrite a single comparison expression into the symbolic-relation form. An
   ordered/equality comparison (`<`, `<=`, `>`, `>=`, `==`, `!=`) becomes the
   matching relation constructor applied to the two rewritten operands and held
   unevaluated, so it survives as a symbolic relation rather than reducing to a
   truth value; every other comparison kind is preserved unchanged. `visit`,
   `k`, `l`, `r` are read-only (not `mut`); the rewrite computes a single node
   and mutates nothing (directive 5). -/
method rewriteComparison (visit : Node → Node) (k : CompareKind) (l : Node) (r : Node) return (out : Node)
  ensures out = rewriteCompare visit k l r
  -- A supported comparison becomes the matching relation, applied to the
  -- rewritten operands and held unevaluated. (Pins both the class and the
  -- unevaluated flag: an EVALUATED relation would collapse to a truth value.)
  ensures k = .lt → out = .relation .Lt false (visit l) (visit r)
  ensures k = .le → out = .relation .Le false (visit l) (visit r)
  ensures k = .gt → out = .relation .Gt false (visit l) (visit r)
  ensures k = .ge → out = .relation .Ge false (visit l) (visit r)
  ensures k = .eq → out = .relation .Eq false (visit l) (visit r)
  ensures k = .ne → out = .relation .Ne false (visit l) (visit r)
  -- An unsupported comparison kind is preserved exactly.
  ensures relOf k = none → out = .comparison k l r
  -- Whenever a relation is produced it is held unevaluated.
  ensures ∀ (rk : RelKind) (b : Bool) (a c : Node), out = .relation rk b a c → b = false
  do
    -- impl-start
    let out : Node :=
      match relOf k with
      | some rk => Node.relation rk false (visit l) (visit r)
      | none    => Node.comparison k l r
    return out
    -- impl-end

prove_correct rewriteComparison by
  loom_solve
  all_goals cases k <;> simp_all [rewriteCompare, relOf]
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement-fidelity) audit of velvet bundle sympy__sympy-24661, run Project root; venv python;.

SPEC SHAPE: The frozen method rewriteComparison carries a COMPLETE functional postcondition `ensures out = rewriteCompare visit k l r` (line 106) PLUS six per-operator relation clauses, the .other-preservation clause, and the always-unevaluated (built=false) clause. Because the first ensures pins out to the exact modeled function on the WHOLE modeled domain (CompareKind x Node x Node, for every free `visit`), any verifying impl is I/O-identical to gold on that domain. This is a maximally-tight spec: verify ⇒ correct on the modeled domain.

SAME_SPEC: all 8 files confirmed True via swebench_unified.markers.same_spec(gold, atk, VelvetBackend.language). Only the impl region (impl-start..impl-end) was edited; axioms/pure/pre/post byte-identical.

### ATTACKS (each: `bash scripts/lean_verify.sh <path>`, run concurrently in 2 batches of 4):
- atk_1 (PREPATCH BUG reproduced): out := .comparison k l r (no comparison clause, fallthrough). EXIT=1, unsolved goals at 126:32. => prepatch_reproduced=true.
- atk_2 (partial-domain): drops .ne to a preserved comparison, rest gold. EXIT=1, unsolved goals 132:32.
- atk_3 (boundary/rel-swap): lt->Le, le->Lt swapped. EXIT=1, unsolved goals 133:32.
- atk_4 (control-flow-effect): builds relation but EVALUATED (built=true). EXIT=1, unsolved goals 129:32. (Killed by both the per-op clauses and the always-unevaluated clause.)
- atk_5 (operand-order swap): .relation rk false (visit r) (visit l). EXIT=1, unsolved goals 129:32.
- atk_6 (ungrounded-oracle ECHO): out := rewriteCompare visit k l r verbatim. EXIT=0 VERIFIES. This is behaviorally IDENTICAL to gold (returns the exact modeled decision).
- atk_7 (skip-visit): .relation rk false l r (raw operands, no recursive rewrite). EXIT=1, unsolved goals 129:32.
Positive control (gold-faithful impl): pos_control.lean EXIT=0 verifies.

So 6/7 genuinely-wrong impls FAIL verification; the only verifier is the gold-equivalent echo (atk_6).

RESOLVE (protocol step 2): For the one verifying impl atk_6, materialized its faithful refined patch. Since atk_6 returns rewriteCompare verbatim = the exact modeled node-shape decision, its faithful Python transliteration IS the gold visit_Compare clause (relational_operators dict + Call(Name(cls),[visit(left),visit(right)],evaluate=False), else return node). Ran it through the OFFICIAL harness: swebench_unified.harness.run_resolve('sympy__sympy-24661', patch, timeout=1800, retries=1) => RESOLVED=True COMPLETED=True NOTE='resolved'. The verifying impl's faithful patch RESOLVES, so verify⇏correct is NOT exhibited.

REFINEMENT.MD AUDIT: legs A1-A6 are all tagged R or I (A1/A2/A3 R type-refinements: operator-class/CompareKind, free visit:Node->Node, operands/Node; A4/A5/A6 I: relOf=membership+lookup, some-branch relation constructor with evaluate=False<->built=false, none-branch preserved Compare). NO axioms, NO A-reference, NO kind-3. meta.json axioms=[] and deep_model_references=[] corroborate. §C correctly states there are no consumed axioms; the sole callee `visit` is UNCHANGED by the patch and abstracted as a free total input the spec asserts nothing about (mapping.md §3) — so there is no relied-on property to check against a real callee, and the model↔patch correspondence holds. The A-legs are sound; the deep model (relOf/rewriteCompare + built flag) faithfully mirrors the gold node-shape decision. G-CONF's differential (seed 24661, 100020 inputs, 0 disagreements) transliterates the same decision and passes.

VERDICT: SOUND. 7 same-spec attacks encoded and machine-verified (prior-pass echo re-encoded + prepatch bug + partial-domain + boundary/rel-swap + control-flow-effect + operand-order + skip-visit); all 6 genuinely-wrong impls fail verification; the single verifying impl (gold-equivalent echo) has a faithful patch that RESOLVES under the official harness (executed, not speculated). The complete-functional-postcondition spec admits no verifying-but-wrong impl on the modeled domain. No counterexample exists; spec is not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sympy__sympy-24661 velvet, modeling EvaluateFalseTransformer.visit_Compare (gold patch, sympy/parsing/sympy_parser.py).

BYTE-IDENTITY: same_spec(Solution, Solution_prepatch, velvet backend) = True; pure region (relOf/rewriteCompare models) is diff-identical. Solution.lean verifies (lean_verify exit 0); Solution_prepatch fails exactly on ensures_3..9 (six supported operators + rewriteCompare summary). G-CONF passes (100020 inputs, seed 24661, 0 disagreements).

MODEL vs REAL CALLEE — checked every representable input class, no divergence:
1. relOf mirrors relational_operators dict exactly: ne->Ne, lt->Lt, le->Le, gt->Gt, ge->Ge, eq->Eq; all other comparison operators -> none/.other. Matches patch's membership test + value lookup.
2. Operand order faithful: patch emits Call(Name(cls), args=[left,right]) with left=visit(node.left), right=visit(node.comparators[0]); model emits .relation rk false (visit l) (visit r) with l<->node.left, r<->node.comparators[0]. First arg = visit(left), second = visit(right) on both. (The patch's reversed *evaluation order* of self.visit is immaterial: visit is a pure free function, no side effects modeled or relied on.)
3. built=false <-> evaluate=False keyword, always present on the produced Call; postcondition also universally forces built=false for any produced relation.
4. Unsupported comparison kinds (.other = ast.Is/In/NotIn/IsNot) -> .comparison preserved <-> patch trailing 'return node'. Faithful.
5. Chained comparisons (a<b<c): the gold patch consults ONLY node.ops[0]/node.left/node.comparators[0], silently dropping the chain tail. The Lean Node carries exactly two operands, so the model reproduces the same truncated behavior — no representable input exposes a difference.
6. visit modeled as a free total Node->Node with NO asserted property (postconditions hold for all visit); this does not over-claim about the unchanged callee. No axioms, G-AX skips (correct: visit is unchanged by the patch).

CONCLUSION: The spec is neither too strong nor drifted; the modeled rewriteCompare/relOf agrees with the gold-patched visit_Compare node-shape decision on the entire finite operator domain plus fuzz, and pins only what the patch guarantees (relation class + evaluate=False, comparison preserved otherwise). No diverging input exists within the modeled domain. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean) = True (byte-identical spec region). Ran swebench_unified.leakage.screen over the computed velvet spec view: PASSED with zero hard failures. Lexical checks clear: no diff markers, no gold-patch line reproduced (>=8 char normalized), no patched file/module path ('sympy/parsing/sympy_parser.py' absent), and the two distinctive changed symbols {EvaluateFalseTransformer, visit_Compare} appear NOWHERE in spec-view identifiers, comments, or docstrings.

Semantic review of the spec view vs the PUBLIC problem_statement (not hints): the problem_statement already discloses the entire target behavior — that `evaluate=False` is ignored for relationals and that `parse_expr('1 < 2', evaluate=False)` must return `Lt(1, 2, evaluate=False)` (a held/unevaluated symbolic relation) rather than `True`. The spec view models exactly this behavior abstractly: CompareKind/RelKind/Node carriers, relOf dispatch, and `.relation rk false (visit l) (visit r)` (held-unevaluated). RelKind's Lt/Le/Gt/Ge/Eq/Ne are the standard SymPy relational class names; Lt and 'relationals' are already public in the problem statement, and the comment attributes them to 'the issue.' The gold edit's localization (the EvaluateFalseTransformer class, the visit_Compare method, the relational_operators dict, the ast.Call/ast.NodeTransformer construction, the file path) is NOT revealed anywhere — the spec is lifted to an opaque 'expression-rewriter over nodes.' No bug/fix narration keywords in comments. The spec encodes the correct behavior (unavoidable and already public) without disclosing the specific code edit or its location beyond problem_statement. No leakage.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
