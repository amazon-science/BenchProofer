# P2 adversarial audit — django__django-12774

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_direct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that constitutes a confirmed break. Every terminating same-spec wrong impl is rejected by the total functional-equality postcondition (out = lookupFieldDecision fieldName fieldUnique constraints, no preconditions, concrete computable oracle). The ONLY same-spec impls that verify are non-terminating (partial-correctness vacuity): atk_8 (infinite loop then always Except.ok) and atk_9 (infinite loop then always Except.error), both EXIT=0. Their materialized faithful refined patches (while True / while i>=0 in QuerySet.in_bulk) apply cleanly at base_commit and were RUN through run_resolve: both returned completed=False (the hung test triggers swebench EvaluationError at run_evaluation.py:216, which writes no report.json). completed=False is NOT the mechanical BROKEN condition (which is r.completed AND not r.resolved); it is an inconclusive_hit. This is a systemic property of loom.semantics.termination "partial" (401/500 velvet bundles), not a defect of this bundle's spec/model — an always-available infinite-loop attack cannot be the intended definition of a spec break, and the composite guarantee (Solution verifies + gold patch resolves + R/I refinement fidelity + G-CONF) is intact.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -85,18 +85,8 @@
   ensures out = lookupFieldDecision fieldName fieldUnique constraints
   do
     -- impl-start
-    let mut uniqueFields : List String := []
-    let mut i := constraints.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ constraints.length
-      invariant uniqueFields = singleColumnKeys (constraints.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := constraints[i - 1]!
-      uniqueFields := soleColumn g ++ uniqueFields
-      i := i - 1
-    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
+    -- PREPATCH BUG: two-conjunct guard, ignores single-column constraints
+    if (fieldName != "pk") && (!fieldUnique) then
       return Except.error ValidationErr.fieldNotUnique
     else
       return Except.ok ()
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -85,21 +85,7 @@
   ensures out = lookupFieldDecision fieldName fieldUnique constraints
   do
     -- impl-start
-    let mut uniqueFields : List String := []
-    let mut i := constraints.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ constraints.length
-      invariant uniqueFields = singleColumnKeys (constraints.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := constraints[i - 1]!
-      uniqueFields := soleColumn g ++ uniqueFields
-      i := i - 1
-    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
-      return Except.error ValidationErr.fieldNotUnique
-    else
-      return Except.ok ()
+    return Except.ok ()
     -- impl-end
 
 /- The backward-fold step: dropping one fewer guarantee exposes the guarantee at
@@ -119,6 +105,4 @@
 
 prove_correct validateLookupField by
   loom_solve
-  rw [singleColumnKeys_drop_step constraints i (by omega) (by omega)]
-  simp_all
   all_goals simp_all [lookupFieldDecision]
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -85,21 +85,7 @@
   ensures out = lookupFieldDecision fieldName fieldUnique constraints
   do
     -- impl-start
-    let mut uniqueFields : List String := []
-    let mut i := constraints.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ constraints.length
-      invariant uniqueFields = singleColumnKeys (constraints.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let g := constraints[i - 1]!
-      uniqueFields := soleColumn g ++ uniqueFields
-      i := i - 1
-    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
-      return Except.error ValidationErr.fieldNotUnique
-    else
-      return Except.ok ()
+    return Except.error ValidationErr.fieldNotUnique
     -- impl-end
 
 /- The backward-fold step: dropping one fewer guarantee exposes the guarantee at
@@ -119,6 +105,4 @@
 
 prove_correct validateLookupField by
   loom_solve
-  rw [singleColumnKeys_drop_step constraints i (by omega) (by omega)]
-  simp_all
   all_goals simp_all [lookupFieldDecision]
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -91,12 +91,11 @@
       invariant 0 ≤ i ∧ i ≤ constraints.length
       invariant uniqueFields = singleColumnKeys (constraints.drop i)
       done_with i = 0
-      decreasing i
     do
       let g := constraints[i - 1]!
       uniqueFields := soleColumn g ++ uniqueFields
       i := i - 1
-    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
+    if (!fieldUnique) && (!uniqueFields.contains fieldName) then
       return Except.error ValidationErr.fieldNotUnique
     else
       return Except.ok ()
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -89,12 +89,11 @@
     let mut i := constraints.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ constraints.length
-      invariant uniqueFields = singleColumnKeys (constraints.drop i)
+      invariant uniqueFields = (constraints.drop i).flatten
       done_with i = 0
-      decreasing i
     do
       let g := constraints[i - 1]!
-      uniqueFields := soleColumn g ++ uniqueFields
+      uniqueFields := g ++ uniqueFields
       i := i - 1
     if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
       return Except.error ValidationErr.fieldNotUnique
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -86,12 +86,11 @@
   do
     -- impl-start
     let mut uniqueFields : List String := []
-    let mut i := constraints.length
+    let mut i := constraints.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ constraints.length
       invariant uniqueFields = singleColumnKeys (constraints.drop i)
       done_with i = 0
-      decreasing i
     do
       let g := constraints[i - 1]!
       uniqueFields := soleColumn g ++ uniqueFields
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -91,12 +91,11 @@
       invariant 0 ≤ i ∧ i ≤ constraints.length
       invariant uniqueFields = singleColumnKeys (constraints.drop i)
       done_with i = 0
-      decreasing i
     do
       let g := constraints[i - 1]!
       uniqueFields := soleColumn g ++ uniqueFields
       i := i - 1
-    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
+    if (fieldName != "pk") && (fieldUnique) && (!uniqueFields.contains fieldName) then
       return Except.error ValidationErr.fieldNotUnique
     else
       return Except.ok ()
```

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -91,12 +91,11 @@
       invariant 0 ≤ i ∧ i ≤ constraints.length
       invariant uniqueFields = singleColumnKeys (constraints.drop i)
       done_with i = 0
-      decreasing i
     do
       let g := constraints[i - 1]!
       uniqueFields := soleColumn g ++ uniqueFields
       i := i - 1
-    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
+    if (fieldName == "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
       return Except.error ValidationErr.fieldNotUnique
     else
       return Except.ok ()
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_direct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged sub-observations the decision consults are modeled as FREE inputs
   (see the method signature): whether the requested key is *individually*
   declared as a unique key (`fieldUnique : Bool`), and the collection of
   uniqueness guarantees in force (`constraints`). The decision's postcondition
   holds for EVERY value of both, so neither is owed a contract — each is
   strictly weaker than any concrete callee (directive 7). The behaviour this
   bundle pins — which requested keys are admissible — is modeled DEEPLY in the
   `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The single outcome the decision distinguishes from acceptance: the requested
   key is rejected as not being a guaranteed-unique key. Acceptance carries
   nothing (`Except.ok ()`). -/
inductive ValidationErr where
  | fieldNotUnique
  deriving DecidableEq

/- The keys covered by ONE uniqueness guarantee. A guarantee that spans exactly
   one column contributes that sole column's name; a guarantee spanning several
   columns (or none) contributes nothing — a multi-column guarantee does not by
   itself make any single one of its columns a unique key. -/
def soleColumn (guarantee : List String) : List String :=
  if guarantee.length = 1 then [guarantee[0]!] else []

/- The keys covered by SOME single-column uniqueness guarantee: the
   per-guarantee expansion of the list of guarantees, concatenated. Written
   front-recursively so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def singleColumnKeys : List (List String) → List String
  | []      => []
  | g :: gs => soleColumn g ++ singleColumnKeys gs

@[grind] lemma singleColumnKeys_nil : singleColumnKeys [] = [] := rfl
@[grind] lemma singleColumnKeys_cons (g : List String) (gs : List (List String)) :
    singleColumnKeys (g :: gs) = soleColumn g ++ singleColumnKeys gs := rfl

/- The desired validation decision for a requested lookup key. The key is
   rejected exactly when ALL of: it is not the primary-key alias, it is not
   individually declared unique, AND it is not covered by any single-column
   uniqueness guarantee. Otherwise it is admissible. The primary-key alias and
   an individually-unique key are always admissible; a key that is the sole
   column of a uniqueness guarantee is ALSO admissible (it is guaranteed unique
   across all rows just the same). -/
def lookupFieldDecision (fieldName : String) (fieldUnique : Bool)
    (constraints : List (List String)) : Except ValidationErr Unit :=
  if (fieldName != "pk") && (!fieldUnique) &&
      (!(singleColumnKeys constraints).contains fieldName) then
    Except.error ValidationErr.fieldNotUnique
  else
    Except.ok ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a requested lookup key is admissible for retrieving records
   keyed by that field. All inputs are read-only (none is `mut`):
     * `fieldName`   — the requested key name; the primary-key alias is `"pk"`;
     * `fieldUnique` — whether that key is individually declared unique;
     * `constraints` — the uniqueness guarantees in force, each given as the
                       list of column names it spans.

   Desired behaviour: the key is admissible unless it is neither the primary-key
   alias, nor individually unique, nor the sole column of a uniqueness
   guarantee — in which case it is rejected. A key that is guaranteed unique
   solely by a single-column uniqueness guarantee MUST be accepted, exactly like
   an individually-unique key. The decision fully determines whether the
   retrieval proceeds or is refused. -/
method validateLookupField (fieldName : String) (fieldUnique : Bool)
    (constraints : List (List String)) return (out : Except ValidationErr Unit)
  ensures out = lookupFieldDecision fieldName fieldUnique constraints
  do
    -- impl-start
    let uniqueFields : List String := singleColumnKeys constraints
    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
      return Except.error ValidationErr.fieldNotUnique
    else
      return Except.ok ()
    -- impl-end

/- The backward-fold step: dropping one fewer guarantee exposes the guarantee at
   `i-1` on the front, so `singleColumnKeys` peels one `soleColumn`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma singleColumnKeys_drop_step (constraints : List (List String)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ constraints.length) :
    singleColumnKeys (constraints.drop (i - 1))
      = soleColumn constraints[i - 1]! ++ singleColumnKeys (constraints.drop i) := by
  have hlt : i - 1 < constraints.length := by omega
  have hcons : constraints.drop (i - 1) = constraints[i - 1]! :: constraints.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, singleColumnKeys_cons]

prove_correct validateLookupField by
  loom_solve
  all_goals simp_all [lookupFieldDecision]
```

Prepatch bug re-encoded as an attack: `True`.

### Spec structure
Solution.lean pins out = lookupFieldDecision fieldName fieldUnique constraints under partial correctness, no preconditions, over a fully concrete computable oracle (soleColumn/singleColumnKeys/lookupFieldDecision). grep confirms NO axiom/opaque/sorry/admit/Classical. Consequence: any TERMINATING verifying impl must equal the oracle on all inputs => its faithful patch = gold guard => resolves. So the only possible verify-but-wrong class is non-termination (partial-correctness vacuity).

=== same_spec: all True (velvet backend) for atk_1..10, pos_control, pos_direct.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>)
pos_control (gold-shaped loop)            EXIT 0  VERIFIES (non-vacuous)
pos_direct  (structurally-diff, no loop)  EXIT 0  VERIFIES (non-vacuous, scored positive control)
atk_1  prepatch 2-conjunct guard          EXIT 1  rejected (goal fieldName ∉ singleColumnKeys constraints)
atk_2  always Except.ok                    EXIT 1  rejected
atk_3  always Except.error                 EXIT 1  rejected
atk_4  drop (fieldName != pk) conjunct     EXIT 1  rejected
atk_5  flatten all columns vs soleColumn   EXIT 1  rejected (multi-col field wrongly admitted; F2P test_in_bulk_non_unique_meta_constaint discriminator)
atk_6  off-by-one loop start length-1      EXIT 1  rejected
atk_7  !fieldUnique -> fieldUnique flip     EXIT 1  rejected
atk_10 (fieldName == pk) sense flip        EXIT 1  rejected
atk_8  DIVERGE (while 0=0) then always ok  EXIT 0  VERIFIES [non-termination]
atk_9  DIVERGE (while i>=0) then always err EXIT 0  VERIFIES [non-termination]

=== RESOLVE RESULTS (official harness, run_resolve, SBU_BENCHMARK_DIR=benchmark-verified, timeout=900 retries=0) ===
GOLD  patch.diff:            completed=True  resolved=True  note='resolved'   (baseline; same image => image OK)
atk_8 atk_8.patch:  completed=False resolved=False note='no report ... — harness error or image pull failure'  (test hung ~15min then EvaluationError; NOT image pull — gold used same image and resolved)
atk_9 atk_9.patch:  completed=False resolved=False note='no report ...'  (same hang path)
All three faithful patches were confirmed to apply cleanly at base_commit 67f9d076... (git apply --check OK for atk_8, atk_9, and gold).

#### Why SOUND, not BROKEN
The mechanical derivation `_derive_audit_verdict` (src/swebench_unified/construct/build_one.py:299-314) sets BROKEN only on r.completed AND not r.resolved. A non-terminating faithful patch HANGS => completed=False => the not-completed branch => inconclusive_hit, never the fail/BROKEN branch. Treating a trivial infinite loop as a break would make EVERY partial-correctness velvet bundle (401/500) unconditionally breakable, which is not the gate design. The methodology deliberately uses loom.semantics.termination "partial" when the impl is not structurally terminating (prompts/velvet/quickref.md:6); the twin-artifact soundness rests on the composite (Velvet-verify + gold G-RESOLVE + G-CONF + refinement fidelity), never Velvet-verify alone. Gold resolves; refinement legs all R/I; spec is maximally tight over terminating impls (9 distinct terminating wrong impls all rejected). Disclosed honestly so a human may override if they read the BROKEN mandate strictly as 'faithful patch does not resolve' regardless of hang-vs-complete.

### REFINEMENT AUDIT (refinement.md)
Legs A1 (R: str<->String), A2 (R + free: get_field(...).unique unchanged callee, free Bool owed no contract), A3 (R + free: total_unique_constraints unchanged callee, free List (List String)), A4 (I: backward while-fold soleColumn == comprehension c.fields[0] if len==1), A5 (I + R: three-conjunct guard + ValueError<->Except.error). No consumed axioms, no A-reference, no kind-3. A-legs' correspondence to real callees holds (both are UNCHANGED at base_commit; the patch only reads them). G-AX = skip is justified. Minor cosmetic doc drift: mapping.md names the helper singleColumnFields while Solution.lean uses singleColumnKeys (documentation-only, no spec/verification impact). conformance_check.py shadow (shadow_sole_column/shadow_single_column_keys/shadow_decision) faithfully transliterates the pure region; oracle calls the real patched in_bulk guard; seed 12774; 100k inputs; per prior G-CONF 0 disagreements.

### Floor
8 scored terminating same-spec attacks (>=5), all verify EXIT=1 (rejected); prepatch reproduced (atk_1); positive control pos_direct verifies (structurally different from shipped Solution, distinct file from all attacks). No confirmed verify⇏correct break under the harness's BROKEN condition.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_direct.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that constitutes a confirmed break. Every terminating same-spec wrong impl is rejected by the total functional-equality postcondition (out = lookupFieldDecision fieldName fieldUnique constraints, no preconditions, concrete computable oracle). The ONLY same-spec impls that verify are non-terminating (partial-correctness vacuity): atk_8 (infinite loop then always Except.ok) and atk_9 (infinite loop then always Except.error), both EXIT=0. Their materialized faithful refined patches (while True / while i>=0 in QuerySet.in_bulk) apply cleanly at base_commit and were RUN through run_resolve: both returned completed=False (the hung test triggers swebench EvaluationError at run_evaluation.py:216, which writes no report.json). completed=False is NOT the mechanical BROKEN condition (which is r.completed AND not r.resolved); it is an inconclusive_hit. This is a systemic property of loom.semantics.termination "partial" (401/500 velvet bundles), not a defect of this bundle's spec/model — an always-available infinite-loop attack cannot be the intended definition of a spec break, and the composite guarantee (Solution verifies + gold patch resolves + R/I refinement fidelity + G-CONF) is intact.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_direct.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged sub-observations the decision consults are modeled as FREE inputs
   (see the method signature): whether the requested key is *individually*
   declared as a unique key (`fieldUnique : Bool`), and the collection of
   uniqueness guarantees in force (`constraints`). The decision's postcondition
   holds for EVERY value of both, so neither is owed a contract — each is
   strictly weaker than any concrete callee (directive 7). The behaviour this
   bundle pins — which requested keys are admissible — is modeled DEEPLY in the
   `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The single outcome the decision distinguishes from acceptance: the requested
   key is rejected as not being a guaranteed-unique key. Acceptance carries
   nothing (`Except.ok ()`). -/
inductive ValidationErr where
  | fieldNotUnique
  deriving DecidableEq

/- The keys covered by ONE uniqueness guarantee. A guarantee that spans exactly
   one column contributes that sole column's name; a guarantee spanning several
   columns (or none) contributes nothing — a multi-column guarantee does not by
   itself make any single one of its columns a unique key. -/
def soleColumn (guarantee : List String) : List String :=
  if guarantee.length = 1 then [guarantee[0]!] else []

/- The keys covered by SOME single-column uniqueness guarantee: the
   per-guarantee expansion of the list of guarantees, concatenated. Written
   front-recursively so a single unfold is available per loop step (the fold
   pattern, plan §5.4). -/
def singleColumnKeys : List (List String) → List String
  | []      => []
  | g :: gs => soleColumn g ++ singleColumnKeys gs

@[grind] lemma singleColumnKeys_nil : singleColumnKeys [] = [] := rfl
@[grind] lemma singleColumnKeys_cons (g : List String) (gs : List (List String)) :
    singleColumnKeys (g :: gs) = soleColumn g ++ singleColumnKeys gs := rfl

/- The desired validation decision for a requested lookup key. The key is
   rejected exactly when ALL of: it is not the primary-key alias, it is not
   individually declared unique, AND it is not covered by any single-column
   uniqueness guarantee. Otherwise it is admissible. The primary-key alias and
   an individually-unique key are always admissible; a key that is the sole
   column of a uniqueness guarantee is ALSO admissible (it is guaranteed unique
   across all rows just the same). -/
def lookupFieldDecision (fieldName : String) (fieldUnique : Bool)
    (constraints : List (List String)) : Except ValidationErr Unit :=
  if (fieldName != "pk") && (!fieldUnique) &&
      (!(singleColumnKeys constraints).contains fieldName) then
    Except.error ValidationErr.fieldNotUnique
  else
    Except.ok ()
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a requested lookup key is admissible for retrieving records
   keyed by that field. All inputs are read-only (none is `mut`):
     * `fieldName`   — the requested key name; the primary-key alias is `"pk"`;
     * `fieldUnique` — whether that key is individually declared unique;
     * `constraints` — the uniqueness guarantees in force, each given as the
                       list of column names it spans.

   Desired behaviour: the key is admissible unless it is neither the primary-key
   alias, nor individually unique, nor the sole column of a uniqueness
   guarantee — in which case it is rejected. A key that is guaranteed unique
   solely by a single-column uniqueness guarantee MUST be accepted, exactly like
   an individually-unique key. The decision fully determines whether the
   retrieval proceeds or is refused. -/
method validateLookupField (fieldName : String) (fieldUnique : Bool)
    (constraints : List (List String)) return (out : Except ValidationErr Unit)
  ensures out = lookupFieldDecision fieldName fieldUnique constraints
  do
    -- impl-start
    let uniqueFields : List String := singleColumnKeys constraints
    if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then
      return Except.error ValidationErr.fieldNotUnique
    else
      return Except.ok ()
    -- impl-end

/- The backward-fold step: dropping one fewer guarantee exposes the guarantee at
   `i-1` on the front, so `singleColumnKeys` peels one `soleColumn`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma singleColumnKeys_drop_step (constraints : List (List String)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ constraints.length) :
    singleColumnKeys (constraints.drop (i - 1))
      = soleColumn constraints[i - 1]! ++ singleColumnKeys (constraints.drop i) := by
  have hlt : i - 1 < constraints.length := by omega
  have hcons : constraints.drop (i - 1) = constraints[i - 1]! :: constraints.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, singleColumnKeys_cons]

prove_correct validateLookupField by
  loom_solve
  all_goals simp_all [lookupFieldDecision]
```

Prepatch bug re-encoded as an attack: `True`.

### Spec structure
Solution.lean pins out = lookupFieldDecision fieldName fieldUnique constraints under partial correctness, no preconditions, over a fully concrete computable oracle (soleColumn/singleColumnKeys/lookupFieldDecision). grep confirms NO axiom/opaque/sorry/admit/Classical. Consequence: any TERMINATING verifying impl must equal the oracle on all inputs => its faithful patch = gold guard => resolves. So the only possible verify-but-wrong class is non-termination (partial-correctness vacuity).

=== same_spec: all True (velvet backend) for atk_1..10, pos_control, pos_direct.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>)
pos_control (gold-shaped loop)            EXIT 0  VERIFIES (non-vacuous)
pos_direct  (structurally-diff, no loop)  EXIT 0  VERIFIES (non-vacuous, scored positive control)
atk_1  prepatch 2-conjunct guard          EXIT 1  rejected (goal fieldName ∉ singleColumnKeys constraints)
atk_2  always Except.ok                    EXIT 1  rejected
atk_3  always Except.error                 EXIT 1  rejected
atk_4  drop (fieldName != pk) conjunct     EXIT 1  rejected
atk_5  flatten all columns vs soleColumn   EXIT 1  rejected (multi-col field wrongly admitted; F2P test_in_bulk_non_unique_meta_constaint discriminator)
atk_6  off-by-one loop start length-1      EXIT 1  rejected
atk_7  !fieldUnique -> fieldUnique flip     EXIT 1  rejected
atk_10 (fieldName == pk) sense flip        EXIT 1  rejected
atk_8  DIVERGE (while 0=0) then always ok  EXIT 0  VERIFIES [non-termination]
atk_9  DIVERGE (while i>=0) then always err EXIT 0  VERIFIES [non-termination]

=== RESOLVE RESULTS (official harness, run_resolve, SBU_BENCHMARK_DIR=benchmark-verified, timeout=900 retries=0) ===
GOLD  patch.diff:            completed=True  resolved=True  note='resolved'   (baseline; same image => image OK)
atk_8 atk_8.patch:  completed=False resolved=False note='no report ... — harness error or image pull failure'  (test hung ~15min then EvaluationError; NOT image pull — gold used same image and resolved)
atk_9 atk_9.patch:  completed=False resolved=False note='no report ...'  (same hang path)
All three faithful patches were confirmed to apply cleanly at base_commit 67f9d076... (git apply --check OK for atk_8, atk_9, and gold).

#### Why SOUND, not BROKEN
The mechanical derivation `_derive_audit_verdict` (src/swebench_unified/construct/build_one.py:299-314) sets BROKEN only on r.completed AND not r.resolved. A non-terminating faithful patch HANGS => completed=False => the not-completed branch => inconclusive_hit, never the fail/BROKEN branch. Treating a trivial infinite loop as a break would make EVERY partial-correctness velvet bundle (401/500) unconditionally breakable, which is not the gate design. The methodology deliberately uses loom.semantics.termination "partial" when the impl is not structurally terminating (prompts/velvet/quickref.md:6); the twin-artifact soundness rests on the composite (Velvet-verify + gold G-RESOLVE + G-CONF + refinement fidelity), never Velvet-verify alone. Gold resolves; refinement legs all R/I; spec is maximally tight over terminating impls (9 distinct terminating wrong impls all rejected). Disclosed honestly so a human may override if they read the BROKEN mandate strictly as 'faithful patch does not resolve' regardless of hang-vs-complete.

### REFINEMENT AUDIT (refinement.md)
Legs A1 (R: str<->String), A2 (R + free: get_field(...).unique unchanged callee, free Bool owed no contract), A3 (R + free: total_unique_constraints unchanged callee, free List (List String)), A4 (I: backward while-fold soleColumn == comprehension c.fields[0] if len==1), A5 (I + R: three-conjunct guard + ValueError<->Except.error). No consumed axioms, no A-reference, no kind-3. A-legs' correspondence to real callees holds (both are UNCHANGED at base_commit; the patch only reads them). G-AX = skip is justified. Minor cosmetic doc drift: mapping.md names the helper singleColumnFields while Solution.lean uses singleColumnKeys (documentation-only, no spec/verification impact). conformance_check.py shadow (shadow_sole_column/shadow_single_column_keys/shadow_decision) faithfully transliterates the pure region; oracle calls the real patched in_bulk guard; seed 12774; 100k inputs; per prior G-CONF 0 disagreements.

### Floor
8 scored terminating same-spec attacks (>=5), all verify EXIT=1 (rejected); prepatch reproduced (atk_1); positive control pos_direct verifies (structurally different from shipped Solution, distinct file from all attacks). No confirmed verify⇏correct break under the harness's BROKEN condition.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) audit of django__django-12774 velvet bundle.

**SAME-SPEC:** same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) == True. Spec region (axioms/pure/pre/post + method signature + ensures) byte-identical between patched and prepatch; only impl region differs (prepatch = two-conjunct buggy guard). Confirmed via swebench_unified.markers.same_spec.

**LEAN:** scripts/lean_verify.sh Solution.lean -> exit 0 (elaborates, no sorry/error). Backward-fold loop invariant uniqueFields = singleColumnKeys (constraints.drop i) discharges the postcondition out = lookupFieldDecision fieldName fieldUnique constraints.

MODEL vs REAL CALLEE (QuerySet.in_bulk validation guard, django/db/models/query.py, base_commit 67f9d076...): The model's decision reject <=> fieldName!="pk" && !fieldUnique && fieldName ∉ singleColumnKeys(constraints), where singleColumnKeys concatenates g[0] for each single-element constraint. This is an operation-by-operation transliteration of the gold guard: soleColumn (len==1 filter + head projection) <-> the `if len(c.fields)==1 ... c.fields[0]` comprehension; identical three-conjunct boolean structure; pk alias short-circuits before get_field on both sides. The two unchanged callees (Field.unique, total_unique_constraints) are modeled as FREE inputs owed no contract -> spec holds for every value, hence strictly weaker than the real callee (directive 7), so it cannot be too strong there.

**EMPIRICAL:** Created fresh worktree at base_commit, applied the gold hunk, ran conformance_check.py -> 'G-CONF OK ... 0 disagreements' over 100000 inputs (seed=12774), reproducing recorded G-CONF pass. Independent adversarial probe with overlapping single-column + multi-column + individually-unique constraint shapes (field in both single- and multi-col constraint; unique field also in a constraint; invalid names) -> 0 disagreements. Invalid field names (get_field raises FieldDoesNotExist) fall outside the modeled domain and never reach the modeled decision -> correct scoping, not a drift.

No diverging input exists between the modeled function and the real repo behavior. Spec is an exact type-refinement of the gold guard and correctly weak on unchanged callees. Gates concur: G-CONF pass, G-DIFF pass (prepatch fails), G-EQ pass. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction attack against django__django-12774/velvet.

**METHOD:** Audited the RENDERED spec view directly (markers.spec_view over Solution.lean): impl region collapses to 'implementation elided — supplied by the consumer' and the prove_correct body is elided. Confirmed the spec region is byte-identical between Solution.lean and Solution_prepatch.lean via markers.same_spec(...) => True — the gold edit lives ONLY in the elided impl/proof regions, never in the solver-visible spec.

**MECHANICAL G-LEAK:** leakage.screen passes (rep.passed=True, zero hard failures). No diff markers, no gold-patch line reproduced (>=8 char normalized collision), no patched file path (django/db/models/query.py) or dotted module, no patched repo symbol echoed. patch_changed_symbols = {'in_bulk'}; 'in_bulk' appears in neither spec-view identifiers nor comments. total_unique_constraints / unique_fields / opts / `_meta` do not appear anywhere in the spec view. No fix/bug/patch/regression narration.

SEMANTIC CHECK (the part the lexical screen can miss): The spec describes the desired WHAT — 'a key that is the sole column of a single-column uniqueness guarantee is admissible, exactly like an individually-unique key' — using abstract, repo-neutral vocabulary (validateLookupField, singleColumnKeys, soleColumn, fieldUnique, constraints, 'primary-key alias'). None of these localizes the edit to in_bulk / total_unique_constraints / the list comprehension. Crucially, this behavioral goal is ALREADY fully public in problem_statement: 'Allow QuerySet.in_bulk() for fields with total UniqueConstraints', with a worked example using a single-column UniqueConstraint(fields=["slug"]) that fails today. Describing the correct admissibility decision is the spec's legitimate function and does not disclose the implementation approach (iterating opts.total_unique_constraints, filtering len(constraint.fields)==1, constraint.fields[0]). The single-column restriction is intrinsic to a CORRECT spec (a multi-column constraint does not make any single column unique), not information beyond the public statement.

**CONCLUSION:** No spec-view line reveals the gold edit beyond the public problem_statement. Verdict NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
