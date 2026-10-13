# P2 adversarial audit — django__django-12708

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl exists, so no faithful refined patch could be materialized or resolve-run (step 2 vacuous). The discriminating input is the F2P scenario cs=[('idx',true,false),('uniq',true,true)]: gold `selected` keeps only 'idx' (1 constraint -> deletion succeeds); every wrong impl either keeps both (prepatch/atk_1 -> _delete_composed_index raises ValueError = the bug), drops/reorders/echoes and thus differs from `selected cs` and fails to prove `out = selected cs`.
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
 -- No axioms. The modeled operation is a selection over the constraints defined
@@ -54,16 +54,15 @@
   ensures out = selected cs
   do
     -- impl-start
-    let mut result : List Constraint := []
+let mut result : List Constraint := []
     let mut i := cs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ cs.length
       invariant result = selected (cs.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cs[i - 1]!
-      result := (if keep c then [c] else []) ++ result
+      result := (if c.isIndex then [c] else []) ++ result
       i := i - 1
     return result
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
 -- No axioms. The modeled operation is a selection over the constraints defined
@@ -54,13 +54,12 @@
   ensures out = selected cs
   do
     -- impl-start
-    let mut result : List Constraint := []
+let mut result : List Constraint := []
     let mut i := cs.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ cs.length
       invariant result = selected (cs.drop i)
-      done_with i = 0
-      decreasing i
+      done_with i = 1
     do
       let c := cs[i - 1]!
       result := (if keep c then [c] else []) ++ result
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
 -- No axioms. The modeled operation is a selection over the constraints defined
@@ -54,16 +54,15 @@
   ensures out = selected cs
   do
     -- impl-start
-    let mut result : List Constraint := []
+let mut result : List Constraint := []
     let mut i := cs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ cs.length
       invariant result = selected (cs.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cs[i - 1]!
-      result := (if keep c then [c] else []) ++ result
+      result := result ++ (if keep c then [c] else [])
       i := i - 1
     return result
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
 -- No axioms. The modeled operation is a selection over the constraints defined
@@ -54,16 +54,15 @@
   ensures out = selected cs
   do
     -- impl-start
-    let mut result : List Constraint := []
+let mut result : List Constraint := []
     let mut i := cs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ cs.length
       invariant result = selected (cs.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cs[i - 1]!
-      result := (if keep c then [c] else []) ++ result
+      result := (if c.isIndex && c.isUnique then [c] else []) ++ result
       i := i - 1
     return result
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
 -- No axioms. The modeled operation is a selection over the constraints defined
@@ -54,18 +54,7 @@
   ensures out = selected cs
   do
     -- impl-start
-    let mut result : List Constraint := []
-    let mut i := cs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ cs.length
-      invariant result = selected (cs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := cs[i - 1]!
-      result := (if keep c then [c] else []) ++ result
-      i := i - 1
-    return result
+return cs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the constraint at
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
 -- No axioms. The modeled operation is a selection over the constraints defined
@@ -54,16 +54,15 @@
   ensures out = selected cs
   do
     -- impl-start
-    let mut result : List Constraint := []
+let mut result : List Constraint := []
     let mut i := cs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ cs.length
       invariant result = selected (cs.drop i)
       done_with i = 0
-      decreasing i
     do
       let c := cs[i - 1]!
-      result := (if keep c then [c] else []) ++ result
+      result := (if !c.isUnique then [c] else []) ++ result
       i := i - 1
     return result
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
 -- No axioms. The modeled operation is a selection over the constraints defined
@@ -54,18 +54,7 @@
   ensures out = selected cs
   do
     -- impl-start
-    let mut result : List Constraint := []
-    let mut i := cs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ cs.length
-      invariant result = selected (cs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := cs[i - 1]!
-      result := (if keep c then [c] else []) ++ result
-      i := i - 1
-    return result
+return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the constraint at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled operation is a selection over the constraints defined
-- on a given set of columns; each constraint is described by two boolean flags
-- (is it an index? is it a uniqueness constraint?) read directly as fields of
-- `Constraint`, and the selection predicate is modeled directly. There is no
-- unchanged opaque callee whose contract the proof must assume, so there is
-- nothing to over-approximate; the cross-language soundness of the structural
-- refinements is checked mechanically by G-CONF.
-- axioms-end

-- pure-start
/- One constraint defined on the target column set. `name` is its identity;
   `isIndex` records whether the constraint provides an index over the columns;
   `isUnique` records whether it enforces uniqueness. A uniqueness constraint is
   typically backed by an index too, so a constraint may have both flags set. -/
structure Constraint where
  name : String
  isIndex : Bool
  isUnique : Bool
  deriving Inhabited

/- A constraint is selectable for removal of a composite index exactly when it
   is an index AND is NOT a uniqueness constraint. A uniqueness constraint over
   the same columns (even though it is index-backed) must be left untouched. -/
def keep (c : Constraint) : Bool := c.isIndex && !c.isUnique

/- The selection over a whole constraint list: keep each selectable constraint,
   in order. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def selected : List Constraint → List Constraint
  | []      => []
  | c :: cs => (if keep c then [c] else []) ++ selected cs

@[grind] lemma selected_nil : selected [] = [] := rfl
@[grind] lemma selected_cons (c : Constraint) (cs : List Constraint) :
    selected (c :: cs) = (if keep c then [c] else []) ++ selected cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectIndexConstraints (cs : List Constraint) return (out : List Constraint)
  ensures out = selected cs
  do
    -- impl-start
    let mut result : List Constraint := []
    let mut i := cs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cs.length
      invariant result = selected (cs.drop i)
      done_with i = 0
    do
      let c := cs[i - 1]!
      result := (if keep c then [c] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the constraint at
   `i-1` on the front, so `selected` peels one `keep` test. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selected_drop_step (cs : List Constraint) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cs.length) :
    selected (cs.drop (i - 1))
      = (if keep cs[i - 1]! then [cs[i - 1]!] else []) ++ selected (cs.drop i) := by
  have hlt : i - 1 < cs.length := by omega
  have hcons : cs.drop (i - 1) = cs[i - 1]! :: cs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selected_cons]

prove_correct selectIndexConstraints by
  loom_solve
  rw [selected_drop_step cs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: `method selectIndexConstraints (cs : List Constraint) return (out) ensures out = selected cs` is a TOTAL full-functional equality postcondition — no precondition restricts cs, and `selected`/`keep = isIndex && !isUnique` are frozen pure defs in the spec view (same_spec = True for all attacks confirmed via swebench_unified.markers.same_spec, velvet backend). Any impl that verifies must prove out = selected cs on ALL inputs, i.e. must compute exactly the gold selection. There is therefore no room for a verify-but-wrong impl.

A-LEG AUDIT (plan §4 focus): meta.json declares axioms:[]; mapping.md §3 and refinement.md §C declare NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op) legs. The 'A1..A4' rows in refinement.md §A are section-local labels whose actual kind tags are all R or I. The single operation the gold patch changed (adding the `unique:False` filter conjunct to constraint_kwargs at schema.py:396) is modeled IDENTICALLY as `keep c = c.isIndex && !c.isUnique` (tag I), not hidden behind an axiom.

The unchanged filtering callee `_constraint_names` is run FOR REAL by G-CONF (conformance_check.py drives the genuine BaseDatabaseSchemaEditor._constraint_names via a shim under post-patch kwargs index=True,unique=False, 100009 inputs seed=12708, 0 disagreements) — it is NOT axiomatized, so there is no axiom-soundness trust point to falsify. The model<->patch correspondence (List Constraint <-> column-matched constraint map; isIndex/isUnique Bool <-> infodict['index']/['unique']; selected names <-> kept constraints) holds; the fixed dimensions (column match, exclude, other kwargs None) are orthogonal to the two flags the patch varies (a modeling-boundary concern, not a fidelity divergence). No kind-3 leg; correspondence sound.

### ATTACKS (all same_spec=True, verified with scripts/lean_verify.sh <file>, run concurrently <=4 at a time in two batches):
- atk_pc.lean (POSITIVE CONTROL, byte-identical gold impl): exit 0 (VERIFIES).
- atk_1.lean (prepatch bug / missing-filter: keep = isIndex ALONE): exit 1, unsolved goals at prove_correct — reproduces the recorded Solution_prepatch.lean bug (impl line byte-matches bundle prepatch).
- atk_2.lean (boundary/off-by-one: while i>1, done_with i=1 — drops the first-indexed element): exit 1, unsolved goals.
- atk_3.lean (control-flow-effect: `result := result ++ (if keep c...)` reversed accumulation order): exit 1, unsolved goals.
- atk_4.lean (inverted predicate: keep = isIndex && isUnique — selects exactly the constraints that must be excluded): exit 1, unsolved goals.
- atk_6.lean (partial predicate: drop isIndex conjunct, keep = !isUnique): exit 1, unsolved goals.
- atk_5.lean (ungrounded-oracle echo: `return cs` identity): exit 1 (out=cs != selected cs; proof also loses loop var i).
- atk_7.lean (ungrounded constant: `return []`): exit 1 ([] != selected cs; proof loses i).
All 7 failures are genuine postcondition mismatches (error: unsolved goals / out != selected cs), verified from lean_verify.sh logs — not spurious syntax noise.

STEP-2 RESOLVE: mandate to materialize+run a faithful refined patch applies only to WRONG impls that VERIFY. Zero wrong impls verified, so the resolve step is vacuously satisfied — there is no verifying-but-wrong candidate whose patch could fail to resolve. Gold patch itself resolves (G-RESOLVE recorded resolved:true).

VERDICT: SOUND. >=5 (here 7) distinct same-spec wrong impls attacked across the required classes (missing-filter/prepatch, boundary, control-flow-effect, inverted-predicate, partial-domain, ungrounded-oracle echo x2); none verifies; positive control verifies; prepatch reproduced. verify => correct holds; verify !=> correct is NOT exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl exists, so no faithful refined patch could be materialized or resolve-run (step 2 vacuous). The discriminating input is the F2P scenario cs=[('idx',true,false),('uniq',true,true)]: gold `selected` keeps only 'idx' (1 constraint -> deletion succeeds); every wrong impl either keeps both (prepatch/atk_1 -> _delete_composed_index raises ValueError = the bug), drops/reorders/echoes and thus differs from `selected cs` and fails to prove `out = selected cs`.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No axioms. The modeled operation is a selection over the constraints defined
-- on a given set of columns; each constraint is described by two boolean flags
-- (is it an index? is it a uniqueness constraint?) read directly as fields of
-- `Constraint`, and the selection predicate is modeled directly. There is no
-- unchanged opaque callee whose contract the proof must assume, so there is
-- nothing to over-approximate; the cross-language soundness of the structural
-- refinements is checked mechanically by G-CONF.
-- axioms-end

-- pure-start
/- One constraint defined on the target column set. `name` is its identity;
   `isIndex` records whether the constraint provides an index over the columns;
   `isUnique` records whether it enforces uniqueness. A uniqueness constraint is
   typically backed by an index too, so a constraint may have both flags set. -/
structure Constraint where
  name : String
  isIndex : Bool
  isUnique : Bool
  deriving Inhabited

/- A constraint is selectable for removal of a composite index exactly when it
   is an index AND is NOT a uniqueness constraint. A uniqueness constraint over
   the same columns (even though it is index-backed) must be left untouched. -/
def keep (c : Constraint) : Bool := c.isIndex && !c.isUnique

/- The selection over a whole constraint list: keep each selectable constraint,
   in order. Front-recursive so a single unfold is available per loop step
   (the Velvet fold pattern, plan §5.4). -/
def selected : List Constraint → List Constraint
  | []      => []
  | c :: cs => (if keep c then [c] else []) ++ selected cs

@[grind] lemma selected_nil : selected [] = [] := rfl
@[grind] lemma selected_cons (c : Constraint) (cs : List Constraint) :
    selected (c :: cs) = (if keep c then [c] else []) ++ selected cs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method selectIndexConstraints (cs : List Constraint) return (out : List Constraint)
  ensures out = selected cs
  do
    -- impl-start
    let mut result : List Constraint := []
    let mut i := cs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ cs.length
      invariant result = selected (cs.drop i)
      done_with i = 0
    do
      let c := cs[i - 1]!
      result := (if keep c then [c] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the constraint at
   `i-1` on the front, so `selected` peels one `keep` test. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma selected_drop_step (cs : List Constraint) (i : Nat)
    (hi : 0 < i) (hle : i ≤ cs.length) :
    selected (cs.drop (i - 1))
      = (if keep cs[i - 1]! then [cs[i - 1]!] else []) ++ selected (cs.drop i) := by
  have hlt : i - 1 < cs.length := by omega
  have hcons : cs.drop (i - 1) = cs[i - 1]! :: cs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, selected_cons]

prove_correct selectIndexConstraints by
  loom_solve
  rw [selected_drop_step cs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: `method selectIndexConstraints (cs : List Constraint) return (out) ensures out = selected cs` is a TOTAL full-functional equality postcondition — no precondition restricts cs, and `selected`/`keep = isIndex && !isUnique` are frozen pure defs in the spec view (same_spec = True for all attacks confirmed via swebench_unified.markers.same_spec, velvet backend). Any impl that verifies must prove out = selected cs on ALL inputs, i.e. must compute exactly the gold selection. There is therefore no room for a verify-but-wrong impl.

A-LEG AUDIT (plan §4 focus): meta.json declares axioms:[]; mapping.md §3 and refinement.md §C declare NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op) legs. The 'A1..A4' rows in refinement.md §A are section-local labels whose actual kind tags are all R or I. The single operation the gold patch changed (adding the `unique:False` filter conjunct to constraint_kwargs at schema.py:396) is modeled IDENTICALLY as `keep c = c.isIndex && !c.isUnique` (tag I), not hidden behind an axiom.

The unchanged filtering callee `_constraint_names` is run FOR REAL by G-CONF (conformance_check.py drives the genuine BaseDatabaseSchemaEditor._constraint_names via a shim under post-patch kwargs index=True,unique=False, 100009 inputs seed=12708, 0 disagreements) — it is NOT axiomatized, so there is no axiom-soundness trust point to falsify. The model<->patch correspondence (List Constraint <-> column-matched constraint map; isIndex/isUnique Bool <-> infodict['index']/['unique']; selected names <-> kept constraints) holds; the fixed dimensions (column match, exclude, other kwargs None) are orthogonal to the two flags the patch varies (a modeling-boundary concern, not a fidelity divergence). No kind-3 leg; correspondence sound.

### ATTACKS (all same_spec=True, verified with scripts/lean_verify.sh <file>, run concurrently <=4 at a time in two batches):
- atk_pc.lean (POSITIVE CONTROL, byte-identical gold impl): exit 0 (VERIFIES).
- atk_1.lean (prepatch bug / missing-filter: keep = isIndex ALONE): exit 1, unsolved goals at prove_correct — reproduces the recorded Solution_prepatch.lean bug (impl line byte-matches bundle prepatch).
- atk_2.lean (boundary/off-by-one: while i>1, done_with i=1 — drops the first-indexed element): exit 1, unsolved goals.
- atk_3.lean (control-flow-effect: `result := result ++ (if keep c...)` reversed accumulation order): exit 1, unsolved goals.
- atk_4.lean (inverted predicate: keep = isIndex && isUnique — selects exactly the constraints that must be excluded): exit 1, unsolved goals.
- atk_6.lean (partial predicate: drop isIndex conjunct, keep = !isUnique): exit 1, unsolved goals.
- atk_5.lean (ungrounded-oracle echo: `return cs` identity): exit 1 (out=cs != selected cs; proof also loses loop var i).
- atk_7.lean (ungrounded constant: `return []`): exit 1 ([] != selected cs; proof loses i).
All 7 failures are genuine postcondition mismatches (error: unsolved goals / out != selected cs), verified from lean_verify.sh logs — not spurious syntax noise.

STEP-2 RESOLVE: mandate to materialize+run a faithful refined patch applies only to WRONG impls that VERIFY. Zero wrong impls verified, so the resolve step is vacuously satisfied — there is no verifying-but-wrong candidate whose patch could fail to resolve. Gold patch itself resolves (G-RESOLVE recorded resolved:true).

VERDICT: SOUND. >=5 (here 7) distinct same-spec wrong impls attacked across the required classes (missing-filter/prepatch, boundary, control-flow-effect, inverted-predicate, partial-domain, ungrounded-oracle echo x2); none verifies; positive control verifies; prepatch reproduced. verify => correct holds; verify !=> correct is NOT exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True) and Solution.lean verifies (lean_verify exit 0). The modeled function selectIndexConstraints with ensures `out = selected cs`, keep c = c.isIndex && !c.isUnique, faithfully models the post-patch selection by BaseDatabaseSchemaEditor._constraint_names(column_names=None, index=True, unique=False, exclude=None) at django/db/backends/base/schema.py:1330-1358 in the base_commit worktree. The real loop keeps names where infodict['unique']==False AND infodict['index']==True, in dict-insertion (list) order — exactly keep=isIndex&&!isUnique over the ordered list. Other _constraint_names dimensions (column_names, primary_key, check, foreign_key, type_) are None/no-op and exclude is empty, so the two-boolean abstraction (mapping.md §2) is legitimate and does not over- or under-approximate the tested dimension. Empirically confirmed: ran conformance_check.py against the real repo worktree — shadow vs. real _constraint_names agree on 100009 inputs (seed=12708) including the index-backed-unique collision F2P boundary case, 0 disagreements. The prepatch model (isIndex alone) correctly fails the spec (G-DIFF), confirming the added !isUnique conjunct is the discriminating, faithful behavior. No input exists where the model disagrees with the real callee; the spec is not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: velvet django__django-12708. Verified the consumer spec view (markers.spec_view) and same_spec(Solution, Solution_prepatch) — same_spec returns True (impl/proof regions are what differ; both elided from the spec view). Mechanical leakage.screen passes (hard_failures=[]); meta G-LEAK recorded 'pass', not relaxed.

Semantic gold-reconstruction analysis:
- Gold edit = one-line kwargs change at django/db/backends/base/schema.py:396 inside alter_index_together: {'index': True} -> {'index': True, 'unique': False}.
- Public problem_statement ALREADY discloses: deleting an index_together crashes when a unique_together exists on the same fields, and the root cause 'it will find two constraints, the _uniq and the _idx one' (i.e. the selection matches both unique and index constraints and must be narrowed).
- Spec view leakage vectors all clear: (1) no repo localization — no patched file path (schema.py appears only in refinement.md/mapping.md, which are NOT part of the spec view); the modeled method is abstractly named selectIndexConstraints, NOT the patched symbol alter_index_together (the sole len>=4 distinctive changed symbol, correctly neither embedded in a spec identifier nor named in any spec-view comment). (2) No gold-patch line reproduced — the Python kwargs dict has no lexical overlap with the Lean surface. (3) No diff markers. (4) No bug/fix/patch narration in comments.
- The correctness discriminator in the pure region (keep c = c.isIndex && !c.isUnique, comment 'a uniqueness constraint over the same columns ... must be left untouched') is the SPEC contract the consumer must implement against, and it is directly derivable from the public problem_statement's own description of the _uniq/_idx collision. It therefore does not reveal the gold edit BEYOND the public problem_statement — it is a specification of correct behavior, not a disclosure of the edit's location or form.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.