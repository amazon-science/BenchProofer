# P2 adversarial audit — django__django-14140

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,23 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
-    let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    let result : Except DeconErr Decon :=
+      match children with
+      | [c] =>
+        match c with
+        | .node =>
+          Except.ok { args := children, pairKw := none,
+                      connKw := (if connector ≠ Connector.conj then some connector else none),
+                      negKw := negated }
+        | .pair k v =>
+          Except.ok { args := [], pairKw := some (k, v), connKw := none, negKw := negated }
+        | .expr =>
+          Except.error DeconErr.notPair
+      | _ =>
+        Except.ok { args := children, pairKw := none,
+                    connKw := (if connector ≠ Connector.conj then some connector else none),
+                    negKw := negated }
+    return result
     -- impl-end
 
 prove_correct deconstructNode by
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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,8 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
     let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    return Except.ok { args := args, pairKw := none, connKw := some connector, negKw := negated }
     -- impl-end
 
 prove_correct deconstructNode by
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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,8 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
     let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    return Except.ok { args := args, pairKw := none, connKw := none, negKw := negated }
     -- impl-end
 
 prove_correct deconstructNode by
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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,9 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
     let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    let connKw : Option Connector := (if connector ≠ Connector.conj then some connector else none)
+    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := false }
     -- impl-end
 
 prove_correct deconstructNode by
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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,9 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
-    let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    let args := children.reverse
+    let connKw : Option Connector := (if connector ≠ Connector.conj then some connector else none)
+    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negated }
     -- impl-end
 
 prove_correct deconstructNode by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,12 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
-    let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    let connKw : Option Connector := (if connector ≠ Connector.conj then some connector else none)
+    let result : Except DeconErr Decon :=
+      match children with
+      | [] => Except.error DeconErr.notPair
+      | _  => Except.ok { args := children, pairKw := none, connKw := connKw, negKw := negated }
+    return result
     -- impl-end
 
 prove_correct deconstructNode by
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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,12 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
-    let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    let connKw : Option Connector := (if connector ≠ Connector.conj then some connector else none)
+    let result : Except DeconErr Decon :=
+      match children with
+      | [_, _] => Except.ok { args := [], pairKw := none, connKw := connKw, negKw := negated }
+      | _      => Except.ok { args := children, pairKw := none, connKw := connKw, negKw := negated }
+    return result
     -- impl-end
 
 prove_correct deconstructNode by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,11 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
     let args := children
     let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
+    if connector = Connector.conj then
       connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negated }
     -- impl-end
 
 prove_correct deconstructNode by
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. Decomposing a logical filter node into a reconstructable
@@ -89,16 +89,7 @@
   ensures out = deconstructed children connector negated
   do
     -- impl-start
-    -- Place every child positionally, uniformly (no single-child special case);
-    -- record the combinator only when non-default and the negation when present.
-    let args := children
-    let mut connKw : Option Connector := none
-    if connector ≠ Connector.conj then
-      connKw := some connector
-    let mut negKw : Bool := false
-    if negated then
-      negKw := true
-    return Except.ok { args := args, pairKw := none, connKw := connKw, negKw := negKw }
+    return deconstructed children connector negated
     -- impl-end
 
 prove_correct deconstructNode by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. Decomposing a logical filter node into a reconstructable
   form is modeled DEEPLY in the `pure` region (`deconstructed`): the positional
   children, the optional recorded combinator, and the optional recorded
   negation are all concrete data, validated against the real node by G-CONF.
   There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A child held by a logical filter node. A child is one of:
   • a key/value condition pair (the shape produced from a keyword condition);
   • a nested filter node;
   • an embedded boolean expression — a value that is neither a pair nor a node
     (it cannot be read as a length-2 key/value pair).
   Only this three-way shape is observable to a consumer of the decomposition
   (mapping.md §2); the payloads are opaque carriers. -/
inductive Child where
  | pair (key : String) (val : Int)
  | node
  | expr
  deriving DecidableEq, Inhabited

/- The combinator joining a node's children. `conj` is the default; `disj` is
   the only non-default value. -/
inductive Connector where
  | conj
  | disj
  deriving DecidableEq, Inhabited

/- A decomposition outcome that is not a successful reconstructable form: it
   arises only when a lone child is required to be read as a key/value pair but
   cannot be (an embedded boolean expression has no such pair shape). -/
inductive DeconErr where
  | notPair
  deriving DecidableEq

/- The reconstructable decomposition of a node:
   • `args`   — the positional children, in order;
   • `pairKw` — a lone key/value condition recorded as a keyword instead of a
     positional child (absent in the desired behaviour — see `deconstructed`);
   • `connKw` — the recorded combinator, present only when it is non-default;
   • `negKw`  — whether the node's negation is recorded.
   `(args, connKw, negKw)` are exactly the components the reconstruction reads
   back; `pairKw` is part of the shared vocabulary so the form can express any
   decomposition (mapping.md §2). -/
structure Decon where
  args : List Child
  pairKw : Option (String × Int)
  connKw : Option Connector
  negKw : Bool
  deriving DecidableEq

/- Decompose a node into its reconstructable form. Desired behaviour: every
   child is placed positionally in `args`, uniformly — a node with a single
   child is treated no differently from one with several, so a lone embedded
   boolean expression is carried through positionally rather than forced into a
   key/value reading (which would have no pair shape). The combinator is recorded
   only when non-default; negation is recorded when present. Decomposition always
   succeeds. -/
def deconstructed (children : List Child) (connector : Connector) (negated : Bool) :
    Except DeconErr Decon :=
  Except.ok {
    args := children,
    pairKw := none,
    connKw := (if connector ≠ Connector.conj then some connector else none),
    negKw := negated
  }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decompose a logical filter node into a path-free reconstructable form of its
   children, combinator and negation. `children`, `connector`, `negated` are
   read-only (directive 5). -/
method deconstructNode (children : List Child) (connector : Connector) (negated : Bool)
    return (out : Except DeconErr Decon)
  ensures out = deconstructed children connector negated
  do
    -- impl-start
    let acc := [] ++ children
    let connKw : Option Connector := (if connector ≠ Connector.conj then some connector else none)
    let negKw : Bool := negated
    return Except.ok { args := acc, pairKw := none, connKw := connKw, negKw := negKw }
    -- impl-end

prove_correct deconstructNode by
  loom_solve <;> simp_all [deconstructed]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL FUNCTIONAL EQUATION: `ensures out = deconstructed children connector negated`, where `deconstructed` is a fully concrete pure function (every child positional in args; connKw=some connector iff connector≠conj; negKw=negated; always Except.ok). Lean's checker forces any verifying impl to be provably equal to `deconstructed` on ALL inputs, so no behaviorally-different impl can verify. There are NO axioms and NO A-legs (meta axioms:[]); the sole deep_model_reference `deconstructed` is R/I, mechanically refuted by G-CONF. refinement.md: 7 legs, all R/I (A1/A2 R, A3-A6 I, A7 R+I), section B 'No kind-A steps', section C 'No kind-3' — audit confirms; model↔patch correspondence rests entirely on `deconstructed` == gold post-patch body, which it matches exactly.

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; verified via scripts/lean_verify.sh, run concurrently ≤4 at a time):
- atk_1 (prepatch bug / ungrounded-oracle: lone non-node child→pairKw, lone expr→error notPair): exit 1, rejected on `ensures_1` at the `Child.expr` arm (line 111). Reproduces the prepatch discriminating clause.
- atk_2 (always record connector, drop non-default guard): exit 1, rejected on `ensures_1` (line 96).
- atk_3 (never record connector): exit 1, rejected on `ensures_1` (line 96).
- atk_4 (drop negation recording, negKw=false): exit 1, rejected on `ensures_1` (line 97).
- atk_5 (reverse children order in args): exit 1, rejected on `ensures_1` (line 97).
- atk_6 (partial-domain: error notPair on empty children): exit 1, rejected on `ensures_1` (line 100). [first draft with match+return hit a WPGen parse error — rewritten to bind via `let`, now rejects genuinely on the postcondition]
- atk_7 (boundary: blank args when exactly-2 children): exit 1, rejected on `ensures_1` (line 100). [same rewrite as atk_6]
- atk_8 (control-flow-effect: invert connector guard, record iff default): exit 1, rejected on `ensures_1` (line 99).
- atk_9 (ungrounded-oracle ECHO: `return deconstructed children connector negated`): exit 0 — VERIFIES. But it is behaviorally CORRECT (deconstructed IS the modeled desired behavior, not a separate opaque answer-key), so its faithful refined patch is the gold post-patch body.

Commands used per attack: `python samespec.sh atk_N.lean` (same_spec) and `bash scripts/lean_verify.sh atk_N.lean`.

POSITIVE CONTROL pos.lean (structurally different: `acc := [] ++ children`, explicit connKw if-expr, negation passed through): same_spec=True, verify exit 0 — spec non-vacuous.

MANDATORY RESOLVE (protocol step 2): the only verifying same-spec attack (atk_9) is behaviorally correct; its faithful materialized patch = gold `Q.deconstruct` post-patch body. I ran it through the official harness: `run_resolve('django__django-14140', gold_patch, timeout=1800)` → RESOLVED=True, completed=True, note='resolved', 61.9s. So the verifying attack's faithful patch DOES resolve. No verifying-but-wrong impl exists ⇒ nothing breaks the spec. verify⇒correct holds here.

prepatch_reproduced=True: Solution_prepatch.lean (and atk_1 which re-encodes it) reproduces the removed single-child special case and fails on the discriminating `[c]`/`Child.expr` arm (the TypeError the issue reports), exactly the gold delta.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. Decomposing a logical filter node into a reconstructable
   form is modeled DEEPLY in the `pure` region (`deconstructed`): the positional
   children, the optional recorded combinator, and the optional recorded
   negation are all concrete data, validated against the real node by G-CONF.
   There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- A child held by a logical filter node. A child is one of:
   • a key/value condition pair (the shape produced from a keyword condition);
   • a nested filter node;
   • an embedded boolean expression — a value that is neither a pair nor a node
     (it cannot be read as a length-2 key/value pair).
   Only this three-way shape is observable to a consumer of the decomposition
   (mapping.md §2); the payloads are opaque carriers. -/
inductive Child where
  | pair (key : String) (val : Int)
  | node
  | expr
  deriving DecidableEq, Inhabited

/- The combinator joining a node's children. `conj` is the default; `disj` is
   the only non-default value. -/
inductive Connector where
  | conj
  | disj
  deriving DecidableEq, Inhabited

/- A decomposition outcome that is not a successful reconstructable form: it
   arises only when a lone child is required to be read as a key/value pair but
   cannot be (an embedded boolean expression has no such pair shape). -/
inductive DeconErr where
  | notPair
  deriving DecidableEq

/- The reconstructable decomposition of a node:
   • `args`   — the positional children, in order;
   • `pairKw` — a lone key/value condition recorded as a keyword instead of a
     positional child (absent in the desired behaviour — see `deconstructed`);
   • `connKw` — the recorded combinator, present only when it is non-default;
   • `negKw`  — whether the node's negation is recorded.
   `(args, connKw, negKw)` are exactly the components the reconstruction reads
   back; `pairKw` is part of the shared vocabulary so the form can express any
   decomposition (mapping.md §2). -/
structure Decon where
  args : List Child
  pairKw : Option (String × Int)
  connKw : Option Connector
  negKw : Bool
  deriving DecidableEq

/- Decompose a node into its reconstructable form. Desired behaviour: every
   child is placed positionally in `args`, uniformly — a node with a single
   child is treated no differently from one with several, so a lone embedded
   boolean expression is carried through positionally rather than forced into a
   key/value reading (which would have no pair shape). The combinator is recorded
   only when non-default; negation is recorded when present. Decomposition always
   succeeds. -/
def deconstructed (children : List Child) (connector : Connector) (negated : Bool) :
    Except DeconErr Decon :=
  Except.ok {
    args := children,
    pairKw := none,
    connKw := (if connector ≠ Connector.conj then some connector else none),
    negKw := negated
  }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decompose a logical filter node into a path-free reconstructable form of its
   children, combinator and negation. `children`, `connector`, `negated` are
   read-only (directive 5). -/
method deconstructNode (children : List Child) (connector : Connector) (negated : Bool)
    return (out : Except DeconErr Decon)
  ensures out = deconstructed children connector negated
  do
    -- impl-start
    let acc := [] ++ children
    let connKw : Option Connector := (if connector ≠ Connector.conj then some connector else none)
    let negKw : Bool := negated
    return Except.ok { args := acc, pairKw := none, connKw := connKw, negKw := negKw }
    -- impl-end

prove_correct deconstructNode by
  loom_solve <;> simp_all [deconstructed]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec is a TOTAL FUNCTIONAL EQUATION: `ensures out = deconstructed children connector negated`, where `deconstructed` is a fully concrete pure function (every child positional in args; connKw=some connector iff connector≠conj; negKw=negated; always Except.ok). Lean's checker forces any verifying impl to be provably equal to `deconstructed` on ALL inputs, so no behaviorally-different impl can verify. There are NO axioms and NO A-legs (meta axioms:[]); the sole deep_model_reference `deconstructed` is R/I, mechanically refuted by G-CONF. refinement.md: 7 legs, all R/I (A1/A2 R, A3-A6 I, A7 R+I), section B 'No kind-A steps', section C 'No kind-3' — audit confirms; model↔patch correspondence rests entirely on `deconstructed` == gold post-patch body, which it matches exactly.

ATTACKS (all same_spec=True verified via swebench_unified.markers.same_spec; verified via scripts/lean_verify.sh, run concurrently ≤4 at a time):
- atk_1 (prepatch bug / ungrounded-oracle: lone non-node child→pairKw, lone expr→error notPair): exit 1, rejected on `ensures_1` at the `Child.expr` arm (line 111). Reproduces the prepatch discriminating clause.
- atk_2 (always record connector, drop non-default guard): exit 1, rejected on `ensures_1` (line 96).
- atk_3 (never record connector): exit 1, rejected on `ensures_1` (line 96).
- atk_4 (drop negation recording, negKw=false): exit 1, rejected on `ensures_1` (line 97).
- atk_5 (reverse children order in args): exit 1, rejected on `ensures_1` (line 97).
- atk_6 (partial-domain: error notPair on empty children): exit 1, rejected on `ensures_1` (line 100). [first draft with match+return hit a WPGen parse error — rewritten to bind via `let`, now rejects genuinely on the postcondition]
- atk_7 (boundary: blank args when exactly-2 children): exit 1, rejected on `ensures_1` (line 100). [same rewrite as atk_6]
- atk_8 (control-flow-effect: invert connector guard, record iff default): exit 1, rejected on `ensures_1` (line 99).
- atk_9 (ungrounded-oracle ECHO: `return deconstructed children connector negated`): exit 0 — VERIFIES. But it is behaviorally CORRECT (deconstructed IS the modeled desired behavior, not a separate opaque answer-key), so its faithful refined patch is the gold post-patch body.

Commands used per attack: `python samespec.sh atk_N.lean` (same_spec) and `bash scripts/lean_verify.sh atk_N.lean`.

POSITIVE CONTROL pos.lean (structurally different: `acc := [] ++ children`, explicit connKw if-expr, negation passed through): same_spec=True, verify exit 0 — spec non-vacuous.

MANDATORY RESOLVE (protocol step 2): the only verifying same-spec attack (atk_9) is behaviorally correct; its faithful materialized patch = gold `Q.deconstruct` post-patch body. I ran it through the official harness: `run_resolve('django__django-14140', gold_patch, timeout=1800)` → RESOLVED=True, completed=True, note='resolved', 61.9s. So the verifying attack's faithful patch DOES resolve. No verifying-but-wrong impl exists ⇒ nothing breaks the spec. verify⇒correct holds here.

prepatch_reproduced=True: Solution_prepatch.lean (and atk_1 which re-encodes it) reproduces the removed single-child special case and fails on the discriminating `[c]`/`Child.expr` arm (the TypeError the issue reports), exactly the gold delta.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit for django__django-14140 (velvet). Modeled function: deconstructNode ↔ Q.deconstruct (django/db/models/query_utils.py) at base_commit 45814af6, gold-patched body.

SPEC FROZEN: same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True — the ensures clause (out = deconstructed children connector negated) and all pure-region definitions are byte-identical between impl and prepatch; only the impl region differs. Spec region is not tightened to pass.

FIDELITY vs REAL REPO: I rebuilt the base-commit worktree, applied the gold hunk manually (args = tuple(self.children); kwargs={}; _connector iff non-default; _negated iff negated), and ran conformance_check.py against the REAL patched Q.deconstruct(): 100018 inputs, seed=14140, 0 disagreements. I then independently probed the single-child boundary the fix targets — lone pair, lone embedded boolean-expr (former TypeError site), lone nested Q, empty node, multi-child; AND/OR × negated — comparing the deep model `deconstructed` prediction to the actual Python return by args identity+order, kwargs keys, _connector and _negated. Every case agreed (FAITHFUL=True).

MODEL-COMPLETENESS checks: (1) Connector = {conj,disj} is complete at base_commit — Q had only AND/OR there (XOR added in a later Django release), so no missing connector branch weakens the spec. (2) pairKw=none always matches removed special case. (3) connKw = some iff connector≠conj matches `!= self.default` (default AND). (4) Model is total (always Except.ok), matching the no-raise patched behavior. (5) `path` component correctly omitted as an input-orthogonal constant; the child payload narrowing to String×Int is opaque and induces no observable divergence.

No input found where the modeled function disagrees with the real callee. The spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Reviewed the consumer spec view for django__django-14140 (velvet). Mechanical G-LEAK screen passes (0 hard failures, 0 warnings); same_spec(Solution, Solution_prepatch)==True so the spec view is byte-identical pre/post-patch and does not itself encode the diff (discriminating behavior lives entirely in the elided impl region). Manual review confirms no leakage BEYOND the public problem_statement:

1. No diff markers, no patched file path (django/db/models/query_utils.py) nor dotted module path, no verbatim gold-patch line reproduced in the view.
2. Spec-view identifiers deconstructNode/deconstructed embed the patched symbol 'deconstruct', but '.deconstruct()' appears verbatim in problem_statement, so it is already public via the task (screen correctly exempts it).
3. No narration terms (bug/fix/patched/previously/…) in any spec-view comment/docstring.
4. The pure-region model `deconstructed` encodes the DESIRED postcondition (every child positional in args, pairKw=none always, _connector iff non-default, _negated iff negated). This is exactly what the PUBLIC problem_statement already narrates in prose: it states single-child Q objects should 'deconstruct into args instead of kwargs', shows the exact crash TypeError: 'Exists' object is not subscriptable, and says the referenced PR 'removes the special case.' The spec's phrasing ('every child placed positionally, uniformly — a single child treated no differently from several') restates that public description; it does not reveal anything solver-invisible.
5. The removed pre-patch special case (single-child→kwargs, notPair error) is confined to mapping.md/refinement.md/Solution_prepatch.lean — all AUDIT artifacts, NOT part of the consumer spec view (spec_view elides impl+proof; prepatch is not shown to solvers).

Every observable in the spec view is either structural (region markers, signature, Except/Decon types) or already fully disclosed in the public problem_statement. Leakage is judged against problem_statement only (not hints_text); nothing here exceeds it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
