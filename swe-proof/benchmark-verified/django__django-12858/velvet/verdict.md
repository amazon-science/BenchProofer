# P2 adversarial audit — django__django-12858

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3_prepatch.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -139,24 +139,8 @@
   ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
   do
     -- impl-start
-    let mut st : WalkState := initState cls0
-    let mut i := 0
-    while i < parts.length
-      invariant i ≤ parts.length
-      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
-      done_with i = parts.length
-      decreasing parts.length - i
-    do
-      let p := parts[i]!
-      st := stepWalk lookup aliasField hasTransform hasLookup st p
-      i := i + 1
-    return st.2.2
+    return false
     -- impl-end
 
 prove_correct checkOrderingRef by
-  loom_solve
-  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>
-    have hi : i < parts.length := by omega
-    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  all_goals simp_all [orderingRefInvalid]
+  loom_solve <;> simp_all [orderingRefInvalid, stepWalk, flagOnUnresolved, initState]
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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -139,24 +139,8 @@
   ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
   do
     -- impl-start
-    let mut st : WalkState := initState cls0
-    let mut i := 0
-    while i < parts.length
-      invariant i ≤ parts.length
-      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
-      done_with i = parts.length
-      decreasing parts.length - i
-    do
-      let p := parts[i]!
-      st := stepWalk lookup aliasField hasTransform hasLookup st p
-      i := i + 1
-    return st.2.2
+    return true
     -- impl-end
 
 prove_correct checkOrderingRef by
-  loom_solve
-  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>
-    have hi : i < parts.length := by omega
-    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  all_goals simp_all [orderingRefInvalid]
+  loom_solve <;> simp_all [orderingRefInvalid, stepWalk, flagOnUnresolved, initState]
```

Attack 3 — `atk_3_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -145,10 +145,33 @@
       invariant i ≤ parts.length
       invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
       done_with i = parts.length
-      decreasing parts.length - i
     do
       let p := parts[i]!
-      st := stepWalk lookup aliasField hasTransform hasLookup st p
+      -- Pre-image skeleton: a part that fails to resolve is flagged unless it is
+      -- a registered TRANSFORM of the last resolved field — with NO escape hatch
+      -- for a part that is only a registered LOOKUP. The frozen spec admits the
+      -- registered-lookup suffix as well (`flagOnUnresolved` also clears on
+      -- `hasLookup`), so for a lookup-but-not-transform suffix the two diverge
+      -- and prove_correct MUST fail.
+      let newSt : WalkState :=
+        let cur  := st.1
+        let last := st.2.1
+        let flag := st.2.2
+        let flagOnUnresolvedBuggy : Bool :=
+          match last with
+          | none   => true
+          | some f => !(hasTransform f p)
+        match cur with
+        | none   => (none, last, flag || flagOnUnresolvedBuggy)
+        | some m =>
+            if p.isAlias then
+              let f := aliasField m
+              (if f.isRel then some f.relModel else none, some f, flag)
+            else
+              match lookup m p with
+              | some f => (if f.isRel then some f.relModel else none, some f, flag)
+              | none   => (some m, last, flag || flagOnUnresolvedBuggy)
+      st := newSt
       i := i + 1
     return st.2.2
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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -141,11 +141,10 @@
     -- impl-start
     let mut st : WalkState := initState cls0
     let mut i := 0
-    while i < parts.length
+    while i + 1 < parts.length
       invariant i ≤ parts.length
       invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
       done_with i = parts.length
-      decreasing parts.length - i
     do
       let p := parts[i]!
       st := stepWalk lookup aliasField hasTransform hasLookup st p
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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -145,12 +145,11 @@
       invariant i ≤ parts.length
       invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
       done_with i = parts.length
-      decreasing parts.length - i
     do
       let p := parts[i]!
       st := stepWalk lookup aliasField hasTransform hasLookup st p
       i := i + 1
-    return st.2.2
+    return !st.2.2
     -- impl-end
 
 prove_correct checkOrderingRef by
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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -139,24 +139,8 @@
   ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
   do
     -- impl-start
-    let mut st : WalkState := initState cls0
-    let mut i := 0
-    while i < parts.length
-      invariant i ≤ parts.length
-      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
-      done_with i = parts.length
-      decreasing parts.length - i
-    do
-      let p := parts[i]!
-      st := stepWalk lookup aliasField hasTransform hasLookup st p
-      i := i + 1
-    return st.2.2
+    return !parts.isEmpty
     -- impl-end
 
 prove_correct checkOrderingRef by
-  loom_solve
-  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>
-    have hi : i < parts.length := by omega
-    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  all_goals simp_all [orderingRefInvalid]
+  loom_solve <;> simp_all [orderingRefInvalid, stepWalk, flagOnUnresolved, initState]
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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -140,12 +140,11 @@
   do
     -- impl-start
     let mut st : WalkState := initState cls0
-    let mut i := 0
+    let mut i := 1
     while i < parts.length
       invariant i ≤ parts.length
       invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
       done_with i = parts.length
-      decreasing parts.length - i
     do
       let p := parts[i]!
       st := stepWalk lookup aliasField hasTransform hasLookup st p
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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -145,12 +145,11 @@
       invariant i ≤ parts.length
       invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
       done_with i = parts.length
-      decreasing parts.length - i
     do
       let p := parts[i]!
       st := stepWalk lookup aliasField hasTransform hasLookup st p
       i := i + 1
-    return st.2.2
+    return st.1.isNone
     -- impl-end
 
 prove_correct checkOrderingRef by
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -139,24 +139,8 @@
   ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
   do
     -- impl-start
-    let mut st : WalkState := initState cls0
-    let mut i := 0
-    while i < parts.length
-      invariant i ≤ parts.length
-      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
-      done_with i = parts.length
-      decreasing parts.length - i
-    do
-      let p := parts[i]!
-      st := stepWalk lookup aliasField hasTransform hasLookup st p
-      i := i + 1
-    return st.2.2
+    return orderingRefInvalid lookup aliasField hasTransform hasTransform cls0 parts
     -- impl-end
 
 prove_correct checkOrderingRef by
-  loom_solve
-  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>
-    have hi : i < parts.length := by omega
-    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  all_goals simp_all [orderingRefInvalid]
+  loom_solve <;> simp_all [orderingRefInvalid, stepWalk, flagOnUnresolved, initState]
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The schema accessors a single ordering reference is
@@ -139,24 +139,21 @@
   ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
   do
     -- impl-start
-    let mut st : WalkState := initState cls0
-    let mut i := 0
-    while i < parts.length
-      invariant i ≤ parts.length
-      invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
-      done_with i = parts.length
-      decreasing parts.length - i
-    do
-      let p := parts[i]!
-      st := stepWalk lookup aliasField hasTransform hasLookup st p
-      i := i + 1
-    return st.2.2
+    if parts.isEmpty then
+      return true
+    else
+      let mut st : WalkState := initState cls0
+      let mut i := 0
+      while i < parts.length
+        invariant i ≤ parts.length
+        invariant st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
+        done_with i = parts.length
+      do
+        let p := parts[i]!
+        st := stepWalk lookup aliasField hasTransform hasLookup st p
+        i := i + 1
+      return st.2.2
     -- impl-end
 
 prove_correct checkOrderingRef by
-  loom_solve
-  case «invariant_2: st = (parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)» =>
-    have hi : i < parts.length := by omega
-    rw [invariant_2, walk_take_step lookup aliasField hasTransform hasLookup cls0 parts i hi,
-        List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
-  all_goals simp_all [orderingRefInvalid]
+  loom_solve <;> simp_all [orderingRefInvalid, stepWalk, flagOnUnresolved, initState]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The schema accessors a single ordering reference is
--  resolved against — "resolve this part to a field of this model", "the alias
--  field of this model", "is this part a registered transform of a field", "is
--  this part a registered lookup of a field" — are taken as FREE INPUTS
--  (`lookup`, `aliasField`, `hasTransform`, `hasLookup`). The spec makes no
--  behavioural claim about them and holds for EVERY schema, so there is nothing
--  to check against a real callee, hence no G-AX. The validity decision under
--  spec — how those accessors are threaded across the chain of parts — is
--  modeled deeply below; every observable is computed from the inputs, nothing
--  is borrowed from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- A model in the schema graph, identified abstractly. -/
abbrev Model := Nat

/- The observable metadata of a resolved field: whether it is a relation (so the
   chain may continue into another model) and, if so, which model it points at. -/
structure Field where
  isRel : Bool
  relModel : Model
deriving Inhabited, DecidableEq

/- One part of a dotted ordering reference (e.g. the `parent`, then `pk`, parts
   of `parent__pk`). `isAlias` marks the part that names the primary-key alias —
   an alias that denotes a model's identity field but is not itself returned by a
   plain field resolution. -/
structure Part where
  name : Nat
  isAlias : Bool
deriving Inhabited, DecidableEq

/- The state carried while walking the chain of parts of one reference:
   - `cur`  : the model the next part is resolved against, or `none` when the
              chain has stepped off the model graph (a part resolved to a
              non-relation field, so there is no further model to descend into);
   - `last` : the most recently resolved field, or `none` before any part has
              resolved (consulted only to decide whether an unresolved part is an
              admissible registered transform/lookup of it);
   - `flag` : whether the reference has been judged invalid (an E015-style
              report has been raised for it). -/
abbrev WalkState := Option Model × Option Field × Bool

/- The seed state for a reference rooted at model `cls0`: resolution starts at
   `cls0`, no field resolved yet, not yet flagged. -/
def initState (cls0 : Model) : WalkState := (some cls0, none, false)

/- When a part fails to resolve, the reference is flagged UNLESS that part names
   a registered transform OR a registered lookup of the LAST resolved field. A
   trailing part that is a registered transform/lookup of the field resolved so
   far is an admissible suffix and must not invalidate the reference. With no
   field resolved yet (`none`), there is nothing to host such a transform/lookup,
   so the reference is flagged. -/
def flagOnUnresolved (hasTransform hasLookup : Field → Part → Bool)
    (last : Option Field) (p : Part) : Bool :=
  match last with
  | none   => true
  | some f => !(hasTransform f p) && !(hasLookup f p)

/- Advance the walk by one part `p`.

   - If there is no current model to resolve against, the part cannot resolve;
     the reference is flagged unless `p` is a registered transform/lookup of the
     last resolved field, and the chain stays off the model graph.
   - Otherwise, against current model `m`:
     * the alias part resolves to `m`'s identity field directly;
     * any other part is resolved by `lookup`; failing to resolve leaves the
       current model in place and flags the reference (modulo the
       transform/lookup escape hatch).
     After a successful resolution the chain descends into the related model when
     the field is a relation, and otherwise steps off the model graph (`none`):
     a non-relation field terminates the descent, so a following part has no
     model to resolve against. -/
def stepWalk (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (st : WalkState) (p : Part) : WalkState :=
  let cur  := st.1
  let last := st.2.1
  let flag := st.2.2
  match cur with
  | none   => (none, last, flag || flagOnUnresolved hasTransform hasLookup last p)
  | some m =>
      if p.isAlias then
        let f := aliasField m
        (if f.isRel then some f.relModel else none, some f, flag)
      else
        match lookup m p with
        | some f => (if f.isRel then some f.relModel else none, some f, flag)
        | none   => (some m, last, flag || flagOnUnresolved hasTransform hasLookup last p)

/- A whole reference is judged invalid iff, after walking every part from the
   seed state, its flag is set. -/
def orderingRefInvalid (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (cls0 : Model) (parts : List Part) : Bool :=
  (parts.foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)).2.2

/- Forward-fold step: extending the consumed prefix by one part advances the
   walk built from the shorter prefix by exactly that part. The single goal
   `loom_solve` leaves for the loop body. -/
lemma walk_take_step
    (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (cls0 : Model) (parts : List Part)
    (i : Nat) (hi : i < parts.length) :
    (parts.take (i + 1)).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
      = stepWalk lookup aliasField hasTransform hasLookup
          ((parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0))
          parts[i]! := by
  have hcons : parts.take (i + 1) = parts.take i ++ [parts[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a single dotted ordering reference is invalid (would raise an
   E015-style report). The reference is the list of `parts` resolved left to
   right against the schema, rooted at the model `cls0`. The schema accessors
   `lookup` / `aliasField` / `hasTransform` / `hasLookup` and the inputs `cls0` /
   `parts` are read-only (not `mut`): the walk threads a fresh accumulator state
   and never mutates anything it is handed (directive 5). -/
method checkOrderingRef
    (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform : Field → Part → Bool) (hasLookup : Field → Part → Bool)
    (cls0 : Model) (parts : List Part)
    return (out : Bool)
  ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
  do
    -- impl-start
    return orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
    -- impl-end

prove_correct checkOrderingRef by
  loom_solve <;> simp_all [orderingRefInvalid, stepWalk, flagOnUnresolved, initState]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-12858 (velvet). Fix: _check_ordering must not raise E015 when an unresolved ordering part is a registered LOOKUP (not just a transform); gold adds `and fld.get_lookup(part) is None` to the except-branch invalidity test.

SPEC SHAPE: postcondition `ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts` TOTALLY pins the output. `orderingRefInvalid` = `(parts.foldl stepWalk (initState cls0)).2.2`; the discriminating behavior (flagOnUnresolved: flag-unless `hasTransform f p || hasLookup f p`) lives entirely in the FROZEN `pure` region (stepWalk/flagOnUnresolved), OUTSIDE the editable impl region. The impl region only computes that foldl via a loop, so there is ZERO behavioral freedom: verify ⟹ out = oracle ⟹ correct.

A-LEGS: ZERO axioms (0 axiom lines; axioms region empty; meta G-AX=pass/skip). The four schema accessors (lookup=Options.get_field, aliasField=Options.pk, hasTransform=Field.get_transform, hasLookup=Field.get_lookup) are UNIVERSALLY-QUANTIFIED FREE INPUTS — the spec holds for every schema, so there is no oracle Ensures to echo and nothing to check against a real callee. No A-consumed / A-reference legs; refinement.md steps 1-6 are all R / I / R+I, no kind-3. A-legs correspondence is vacuously satisfied (nothing axiomatized). No ungrounded-oracle: atk_1/atk_2 prove the pinned function is non-constant, so no returnable answer-key exists.

SAME-SPEC: all 10 attacks + both positive controls confirmed same_spec=True via swebench_unified.markers.same_spec (velvet).

MACHINE-CHECKED (scripts/lean_verify.sh, 300s cap; run concurrently ≤4/batch; each attack's failure confirmed on `ensures_1: out = orderingRefInvalid ...`, NOT syntax):
- atk_1 const-false (`return false`): exit 1 (ensures_1 unsolved) — oracle not constant-false.
- atk_2 const-true (`return true`): exit 1 (ensures_1) — oracle not constant-true.
- atk_3 PREPATCH BUG (except-branch clears on hasTransform only, no hasLookup escape): exit 1 — fails loop-body invariant on LHS `!hasTransform f p` vs RHS stepWalk `!hasTransform f p && !hasLookup f p`; the missing conjunct IS the gold patch (F2P test_ordering_pointing_to_lookup_not_transform / test__isnull). prepatch_reproduced=True.
- atk_4 off-by-one (`while i+1 < parts.length`, skips last part): exit 1 (ensures_1).
- atk_5 negated flag (`return !st.2.2`): exit 1 (ensures_1).
- atk_6 `return !parts.isEmpty`: exit 1 (ensures_1).
- atk_7 boundary (start i:=1, skip first part): exit 1 (ensures_1).
- atk_8 control-flow-effect (`return st.1.isNone` — off-graph flag, not the invalidity flag): exit 1 (ensures_1).
- atk_9 ungrounded-oracle echo with WRONG args (`orderingRefInvalid ... hasTransform hasTransform ...`, drops hasLookup): exit 1 (ensures_1) — collapses to prepatch semantics, rejected.
- atk_10 partial-domain (correct on nonempty, `return true` on empty): exit 1 (ensures_1).
All 10 wrong impls REJECTED.

POSITIVE CONTROLS (must verify): pos_control.lean (structurally-different correct impl `return orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts` with trivial proof, same_spec=True): exit 0. pos_control_frozen.lean (frozen Solution.lean): exit 0. Spec is satisfiable / non-vacuous.

RESOLVE STEP: the set of verifying-but-wrong impls is EMPTY, so the mandatory 'materialize faithful patch + run_resolve for every verifying wrong impl' step has no members — no resolve run is required or possible for any attack (patches={}). The gold patch itself resolves: meta.json records G-RESOLVE=pass ('resolved'), G-CONF=pass (100004 checks, 0 disagreements, seed 12858), G-DIFF=pass, G-VERIFY=pass (2.9s), G-MUT=pass (15/15). No patch.diff file present in the bundle dir (gold patch carried in harness/dataset, not the bundle); this does not affect the G-EQ verify⇏correct analysis, which is fully determined by the pinned postcondition.

CONCLUSION: verify ⟹ correct holds — the postcondition pins the output to a fixed non-constant function of universally-quantified free inputs whose defining logic is frozen outside the impl region; no same-spec wrong impl can verify. ≥5 (10) distinct attacks across all required classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug, negation, off-by-one) run and none breaks the spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 10 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 10 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 10 | `atk_1.lean`, `atk_2.lean`, `atk_3_prepatch.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (10):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 10 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The schema accessors a single ordering reference is
--  resolved against — "resolve this part to a field of this model", "the alias
--  field of this model", "is this part a registered transform of a field", "is
--  this part a registered lookup of a field" — are taken as FREE INPUTS
--  (`lookup`, `aliasField`, `hasTransform`, `hasLookup`). The spec makes no
--  behavioural claim about them and holds for EVERY schema, so there is nothing
--  to check against a real callee, hence no G-AX. The validity decision under
--  spec — how those accessors are threaded across the chain of parts — is
--  modeled deeply below; every observable is computed from the inputs, nothing
--  is borrowed from an oracle. See refinement.md / mapping.md.)
-- axioms-end

-- pure-start
/- A model in the schema graph, identified abstractly. -/
abbrev Model := Nat

/- The observable metadata of a resolved field: whether it is a relation (so the
   chain may continue into another model) and, if so, which model it points at. -/
structure Field where
  isRel : Bool
  relModel : Model
deriving Inhabited, DecidableEq

/- One part of a dotted ordering reference (e.g. the `parent`, then `pk`, parts
   of `parent__pk`). `isAlias` marks the part that names the primary-key alias —
   an alias that denotes a model's identity field but is not itself returned by a
   plain field resolution. -/
structure Part where
  name : Nat
  isAlias : Bool
deriving Inhabited, DecidableEq

/- The state carried while walking the chain of parts of one reference:
   - `cur`  : the model the next part is resolved against, or `none` when the
              chain has stepped off the model graph (a part resolved to a
              non-relation field, so there is no further model to descend into);
   - `last` : the most recently resolved field, or `none` before any part has
              resolved (consulted only to decide whether an unresolved part is an
              admissible registered transform/lookup of it);
   - `flag` : whether the reference has been judged invalid (an E015-style
              report has been raised for it). -/
abbrev WalkState := Option Model × Option Field × Bool

/- The seed state for a reference rooted at model `cls0`: resolution starts at
   `cls0`, no field resolved yet, not yet flagged. -/
def initState (cls0 : Model) : WalkState := (some cls0, none, false)

/- When a part fails to resolve, the reference is flagged UNLESS that part names
   a registered transform OR a registered lookup of the LAST resolved field. A
   trailing part that is a registered transform/lookup of the field resolved so
   far is an admissible suffix and must not invalidate the reference. With no
   field resolved yet (`none`), there is nothing to host such a transform/lookup,
   so the reference is flagged. -/
def flagOnUnresolved (hasTransform hasLookup : Field → Part → Bool)
    (last : Option Field) (p : Part) : Bool :=
  match last with
  | none   => true
  | some f => !(hasTransform f p) && !(hasLookup f p)

/- Advance the walk by one part `p`.

   - If there is no current model to resolve against, the part cannot resolve;
     the reference is flagged unless `p` is a registered transform/lookup of the
     last resolved field, and the chain stays off the model graph.
   - Otherwise, against current model `m`:
     * the alias part resolves to `m`'s identity field directly;
     * any other part is resolved by `lookup`; failing to resolve leaves the
       current model in place and flags the reference (modulo the
       transform/lookup escape hatch).
     After a successful resolution the chain descends into the related model when
     the field is a relation, and otherwise steps off the model graph (`none`):
     a non-relation field terminates the descent, so a following part has no
     model to resolve against. -/
def stepWalk (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (st : WalkState) (p : Part) : WalkState :=
  let cur  := st.1
  let last := st.2.1
  let flag := st.2.2
  match cur with
  | none   => (none, last, flag || flagOnUnresolved hasTransform hasLookup last p)
  | some m =>
      if p.isAlias then
        let f := aliasField m
        (if f.isRel then some f.relModel else none, some f, flag)
      else
        match lookup m p with
        | some f => (if f.isRel then some f.relModel else none, some f, flag)
        | none   => (some m, last, flag || flagOnUnresolved hasTransform hasLookup last p)

/- A whole reference is judged invalid iff, after walking every part from the
   seed state, its flag is set. -/
def orderingRefInvalid (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (cls0 : Model) (parts : List Part) : Bool :=
  (parts.foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)).2.2

/- Forward-fold step: extending the consumed prefix by one part advances the
   walk built from the shorter prefix by exactly that part. The single goal
   `loom_solve` leaves for the loop body. -/
lemma walk_take_step
    (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform hasLookup : Field → Part → Bool) (cls0 : Model) (parts : List Part)
    (i : Nat) (hi : i < parts.length) :
    (parts.take (i + 1)).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0)
      = stepWalk lookup aliasField hasTransform hasLookup
          ((parts.take i).foldl (stepWalk lookup aliasField hasTransform hasLookup) (initState cls0))
          parts[i]! := by
  have hcons : parts.take (i + 1) = parts.take i ++ [parts[i]!] := by
    rw [List.take_succ, List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hi]
    simp
  rw [hcons, List.foldl_append, List.foldl_cons, List.foldl_nil]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a single dotted ordering reference is invalid (would raise an
   E015-style report). The reference is the list of `parts` resolved left to
   right against the schema, rooted at the model `cls0`. The schema accessors
   `lookup` / `aliasField` / `hasTransform` / `hasLookup` and the inputs `cls0` /
   `parts` are read-only (not `mut`): the walk threads a fresh accumulator state
   and never mutates anything it is handed (directive 5). -/
method checkOrderingRef
    (lookup : Model → Part → Option Field) (aliasField : Model → Field)
    (hasTransform : Field → Part → Bool) (hasLookup : Field → Part → Bool)
    (cls0 : Model) (parts : List Part)
    return (out : Bool)
  ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
  do
    -- impl-start
    return orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts
    -- impl-end

prove_correct checkOrderingRef by
  loom_solve <;> simp_all [orderingRefInvalid, stepWalk, flagOnUnresolved, initState]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit, django__django-12858 (velvet). Fix: _check_ordering must not raise E015 when an unresolved ordering part is a registered LOOKUP (not just a transform); gold adds `and fld.get_lookup(part) is None` to the except-branch invalidity test.

SPEC SHAPE: postcondition `ensures out = orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts` TOTALLY pins the output. `orderingRefInvalid` = `(parts.foldl stepWalk (initState cls0)).2.2`; the discriminating behavior (flagOnUnresolved: flag-unless `hasTransform f p || hasLookup f p`) lives entirely in the FROZEN `pure` region (stepWalk/flagOnUnresolved), OUTSIDE the editable impl region. The impl region only computes that foldl via a loop, so there is ZERO behavioral freedom: verify ⟹ out = oracle ⟹ correct.

A-LEGS: ZERO axioms (0 axiom lines; axioms region empty; meta G-AX=pass/skip). The four schema accessors (lookup=Options.get_field, aliasField=Options.pk, hasTransform=Field.get_transform, hasLookup=Field.get_lookup) are UNIVERSALLY-QUANTIFIED FREE INPUTS — the spec holds for every schema, so there is no oracle Ensures to echo and nothing to check against a real callee. No A-consumed / A-reference legs; refinement.md steps 1-6 are all R / I / R+I, no kind-3. A-legs correspondence is vacuously satisfied (nothing axiomatized). No ungrounded-oracle: atk_1/atk_2 prove the pinned function is non-constant, so no returnable answer-key exists.

SAME-SPEC: all 10 attacks + both positive controls confirmed same_spec=True via swebench_unified.markers.same_spec (velvet).

MACHINE-CHECKED (scripts/lean_verify.sh, 300s cap; run concurrently ≤4/batch; each attack's failure confirmed on `ensures_1: out = orderingRefInvalid ...`, NOT syntax):
- atk_1 const-false (`return false`): exit 1 (ensures_1 unsolved) — oracle not constant-false.
- atk_2 const-true (`return true`): exit 1 (ensures_1) — oracle not constant-true.
- atk_3 PREPATCH BUG (except-branch clears on hasTransform only, no hasLookup escape): exit 1 — fails loop-body invariant on LHS `!hasTransform f p` vs RHS stepWalk `!hasTransform f p && !hasLookup f p`; the missing conjunct IS the gold patch (F2P test_ordering_pointing_to_lookup_not_transform / test__isnull). prepatch_reproduced=True.
- atk_4 off-by-one (`while i+1 < parts.length`, skips last part): exit 1 (ensures_1).
- atk_5 negated flag (`return !st.2.2`): exit 1 (ensures_1).
- atk_6 `return !parts.isEmpty`: exit 1 (ensures_1).
- atk_7 boundary (start i:=1, skip first part): exit 1 (ensures_1).
- atk_8 control-flow-effect (`return st.1.isNone` — off-graph flag, not the invalidity flag): exit 1 (ensures_1).
- atk_9 ungrounded-oracle echo with WRONG args (`orderingRefInvalid ... hasTransform hasTransform ...`, drops hasLookup): exit 1 (ensures_1) — collapses to prepatch semantics, rejected.
- atk_10 partial-domain (correct on nonempty, `return true` on empty): exit 1 (ensures_1).
All 10 wrong impls REJECTED.

POSITIVE CONTROLS (must verify): pos_control.lean (structurally-different correct impl `return orderingRefInvalid lookup aliasField hasTransform hasLookup cls0 parts` with trivial proof, same_spec=True): exit 0. pos_control_frozen.lean (frozen Solution.lean): exit 0. Spec is satisfiable / non-vacuous.

RESOLVE STEP: the set of verifying-but-wrong impls is EMPTY, so the mandatory 'materialize faithful patch + run_resolve for every verifying wrong impl' step has no members — no resolve run is required or possible for any attack (patches={}). The gold patch itself resolves: meta.json records G-RESOLVE=pass ('resolved'), G-CONF=pass (100004 checks, 0 disagreements, seed 12858), G-DIFF=pass, G-VERIFY=pass (2.9s), G-MUT=pass (15/15). No patch.diff file present in the bundle dir (gold patch carried in harness/dataset, not the bundle); this does not affect the G-EQ verify⇏correct analysis, which is fully determined by the pinned postcondition.

CONCLUSION: verify ⟹ correct holds — the postcondition pins the output to a fixed non-constant function of universally-quantified free inputs whose defining logic is frozen outside the impl region; no same-spec wrong impl can verify. ≥5 (10) distinct attacks across all required classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch bug, negation, off-by-one) run and none breaks the spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) assessment for django__django-12858 velvet bundle. Modeled function checkOrderingRef models the related-reference inner walk of Model._check_ordering (base.py:1709, walk :1735-1758); ensures out = orderingRefInvalid ... over the walk fold.

Checks performed:
1. Solution.lean verifies (lean_verify.sh exit 0); the prove_correct discharges the ensures clause.
2. same_spec(Solution, Solution_prepatch) = True (spec region byte-identical; only impl differs).
3. Prepatch fails verification (exit 1) on exactly the discriminating hasLookup clause -> spec is strong enough to see the bug (F2P test_ordering_pointing_to_lookup_not_transform / test__isnull), not too weak; and not over-strong (a genuine gold-equivalent still verifies as shown by the Solution).
4. Branch-by-branch faithfulness trace vs real gold-patched Python control flow: cur=none arm <-> _cls is None raising AttributeError with fld/last unchanged; alias arm <-> part=='pk' (_meta.pk); lookup none <-> FieldDoesNotExist leaving _cls/fld unchanged; relation descent <-> is_relation ? _cls=to_opts.model : _cls=None; flagOnUnresolved: none|->true == 'fld is None', some f|-> !(hasTransform)&&!(hasLookup) == patched 'get_transform(part) is None and get_lookup(part) is None'. All correspond exactly.
5. The four schema accessors (lookup/aliasField/hasTransform/hasLookup) are correctly modeled as FREE INPUTS -- all unchanged by the patch, so the spec makes no schema-specific behavioral claim and holds for EVERY schema (G-AX skip is legitimate). This means the spec is universally quantified over accessors and cannot be too strong on any concrete schema.
6. G-CONF oracle (verbatim transliteration of the gold-patched walk) vs the Solution shadow: 100004 checks (boundary F2P scenario + 100k fuzzed schemas, seed=12858) -> 0 disagreements.

No input found where the modeled function disagrees with the real (gold-patched) callee. Spec is faithful: neither drifts from nor over-constrains the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-view screen: verified same_spec(Solution, Solution_prepatch)=True and computed the actual velvet spec_view. Mechanical G-LEAK screen (leakage.screen over the spec view vs frozen gold patch + problem_statement) returns passed=True: no diff markers, no patched file path (django/db/models/base.py) or module path in view, no gold-patch line reproduced (changed lines are Python `fld.get_transform/get_lookup` code, absent from the Lean view), changed symbol 'check_ordering' does not collide with 'checkOrderingRef', and no bug/fix/patch narration in comments.

Manual gold-reconstruction check: the gold edit adds a `fld.get_lookup(part) is None` conjunct to the E015 except-branch so that a registered LOOKUP (not just a transform) exempts an ordering reference from E015. The public problem_statement ALREADY discloses this fully — its title is 'models.E015 is raised when ordering uses lookups that are not transforms' and it gives the `supply__product__parent__isnull` example (isnull = a lookup) that must be allowed. So the two concepts the fix hinges on — 'lookup' vs 'transform' — and the intended correct behavior are public via the task, not leaked by the spec.

The spec view's `flagOnUnresolved = !(hasTransform f p) && !(hasLookup f p)` and the paired `hasTransform`/`hasLookup` accessors do encode the correct post-fix behavior, but (a) that is the specification of correctness every bundle must state, (b) the discriminating logic is byte-identical between Solution and its prepatch (same_spec=True), so the spec view reveals nothing that distinguishes gold from buggy — the discriminator lives only in the elided impl/proof, and (c) both accessors are directly implied by the public 'lookups that are not transforms' framing. No spec-view line reconstructs the gold edit beyond problem_statement. G-AX correctly skip (accessors are free inputs). Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
