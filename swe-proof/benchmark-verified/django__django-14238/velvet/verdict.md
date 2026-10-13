# P2 adversarial audit — django__django-14238

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
- **machine verdict:** eq: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, VERIFYING, TERMINATING implementation returns a wrong value: the load-bearing postcondition `ensures result = isFamilyMember ancestry` is an exact functional equality that forces any verifying terminating impl to compute isFamilyMember on the whole domain (require ancestry != []). The only verifying wrong impls are DIVERGENT (atk_12/atk_13, while-true), and their faithful patches cannot resolve-complete (they hang), so they are not valid verify-and-not-correct counterexamples (see notes).
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,10 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
+    let viaSubBases : Bool := subBaseIds.contains ancestry.head!
     let viaRootBase : Bool := derivesFrom ancestry rootBaseId
     return viaSubBases || viaRootBase
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    return true
     -- impl-end
 
 prove_correct recognizeType by
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    return false
     -- impl-end
 
 prove_correct recognizeType by
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    return derivesFrom ancestry rootBaseId
     -- impl-end
 
 prove_correct recognizeType by
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    return subBaseIds.any (fun b => derivesFrom ancestry b)
     -- impl-end
 
 prove_correct recognizeType by
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,9 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
     let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
     let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    return viaSubBases && viaRootBase
     -- impl-end
 
 prove_correct recognizeType by
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,10 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
+    let viaSubBases : Bool := derivesFrom ancestry 1
     let viaRootBase : Bool := derivesFrom ancestry rootBaseId
     return viaSubBases || viaRootBase
     -- impl-end
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    return subBaseIds.any (fun b => derivesFrom ancestry b) || derivesFrom ancestry rootBaseId || derivesFrom ancestry 3
     -- impl-end
 
 prove_correct recognizeType by
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,8 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    let anc := ancestry.tail
+    return subBaseIds.any (fun b => derivesFrom anc b) || derivesFrom anc rootBaseId
     -- impl-end
 
 prove_correct recognizeType by
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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,10 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    if ancestry.head! == rootBaseId || subBaseIds.contains ancestry.head! then
+      return true
+    else
+      return false
     -- impl-end
 
 prove_correct recognizeType by
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The recognition decision is pure boolean / list-frame
@@ -69,12 +69,7 @@
   ensures derivesFrom ancestry rootBaseId = true → result = true
   do
     -- impl-start
-    -- A candidate derives from one of the specialised bases iff that base is in
-    -- its ancestry (genuine derivation, the reflexive case included). The
-    -- separate root-base leg recognises candidates deriving from the root.
-    let viaSubBases : Bool := subBaseIds.any (fun b => derivesFrom ancestry b)
-    let viaRootBase : Bool := derivesFrom ancestry rootBaseId
-    return viaSubBases || viaRootBase
+    return isFamilyMember ancestry && (ancestry.length > 1)
     -- impl-end
 
 prove_correct recognizeType by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The recognition decision is pure boolean / list-frame
--  logic over a FREE INPUT: the ancestry of the candidate type. The membership
--  predicate that decides whether one type derives from another is the language's
--  own total structural relation over a type's linearised ancestor list — the
--  operation reads that ancestry, it never reshapes any outside object, so there
--  is no callee contract to assume and nothing for G-AX.)
-- axioms-end

-- pure-start
/- A type's ancestry is modeled as the linearised list of the identifiers of the
   types it derives from, the candidate type itself listed first (mapping.md §2).
   Identifiers are abstract tags; three of them denote the family's recognised
   base types. -/

/- The root recognised base type (a candidate that derives from it is recognised
   directly). -/
def rootBaseId : Nat := 0

/- The two further recognised base types of the family. A candidate that derives
   from either of them is also a member of the family — derivation, not mere
   identity with one of these bases, is what matters. -/
def subBaseIds : List Nat := [1, 2]

/- Whether one type derives from another: the target base appears in the
   candidate's ancestry. Reflexive (a type's ancestry lists itself) and total. -/
def derivesFrom (ancestry : List Nat) (baseId : Nat) : Bool :=
  ancestry.contains baseId

/- The recognition decision, modeled deeply. A candidate type is a member of the
   family exactly when it derives from ANY recognised base type: from one of the
   two sub-bases, OR from the root base. Genuine derivation throughout — being
   identical to a base is just the reflexive case of deriving from it, and is
   neither necessary (a proper descendant qualifies) nor specially privileged. -/
def isFamilyMember (ancestry : List Nat) : Bool :=
  (subBaseIds.any (fun b => derivesFrom ancestry b)) || derivesFrom ancestry rootBaseId

@[grind] lemma isFamilyMember_def (ancestry : List Nat) :
    isFamilyMember ancestry =
      ((subBaseIds.any (fun b => derivesFrom ancestry b)) || derivesFrom ancestry rootBaseId) :=
  rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a candidate type is recognised as a member of the family.
   Desired behaviour: a candidate is recognised exactly when it genuinely derives
   from a recognised base type — from one of the family's specialised base types
   or from its root base. A type that descends from a specialised base must be
   recognised even when it is not itself one of those bases; recognition is by
   derivation, not by identity. The candidate's ancestry (`ancestry`) is
   read-only and a candidate always has a non-empty ancestry (it lists itself). -/
method recognizeType (ancestry : List Nat) return (result : Bool)
  require ancestry ≠ []
  ensures result = isFamilyMember ancestry
  ensures (subBaseIds.any (fun b => derivesFrom ancestry b)) = true → result = true
  ensures derivesFrom ancestry rootBaseId = true → result = true
  do
    -- impl-start
    return (rootBaseId :: subBaseIds).any (fun b => derivesFrom ancestry b)
    -- impl-end

prove_correct recognizeType by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: 13 same-spec attacks + 1 positive control, built by editing ONLY the impl region of Solution.lean (axioms/pure/pre/post byte-identical). same_spec=True confirmed for all 13 via swebench_unified.markers.same_spec on velvet backend. Verified with `bash scripts/lean_verify.sh <file>`.

### TERMINATING ATTACKS (all same-spec, ALL REJECTED, exit 1 — genuine unsolved-goals on ensures_1/ensures_3, not elaboration errors):
  atk_1  prepatch identity bug (subBaseIds.contains ancestry.head!)  -> exit 1 (ensures_1/ensures_3)
  atk_2  return true                                                -> exit 1 (ensures_3: true = isFamilyMember)
  atk_3  return false                                               -> exit 1 (ensures_1)
  atk_4  only root leg                                              -> exit 1 (ensures_2/eq)
  atk_5  only sub-bases (drop root)                                 -> exit 1 (ensures_1)
  atk_6  && instead of ||                                           -> exit 1 (ensures_1)
  atk_7  drop SmallAutoField id 2                                   -> exit 1 (ensures_2/eq)
  atk_8  over-approx: add spurious base id 3                        -> exit 1 (ensures_3)
  atk_9  drop head (reflexive), derive over tail                    -> exit 1 (ensures_1)
  atk_10 if/else identity-only on head                             -> exit 1 (ensures_3: true = isFamilyMember)
  atk_11 isFamilyMember && (ancestry.length > 1)                    -> exit 1 (ensures_3)
POSITIVE CONTROL pc.lean: (rootBaseId :: subBaseIds).any (ancestry.contains .) — structurally different, correct -> exit 0 VERIFIES. prepatch_reproduced=True (atk_1 == Solution_prepatch.lean semantics).

### DIVERGENCE PROBES (disclosed, investigated end-to-end, EXCLUDED from the candidate set — not valid counterexamples):
  atk_12 `while true do i:=i+1; return !(isFamilyMember ancestry)`         -> lean_verify exit 0 VERIFIES (only a 'loop invariant assumed True' warning)
  atk_13 `guess:=sub-only; while guess != isFamilyMember do i:=i+1; return guess` -> lean_verify exit 0 VERIFIES
Both verify because `set_option loom.semantics.termination "partial"` (partial correctness) discharges any postcondition vacuously when the return is unreachable. I MATERIALIZED their faithful refined patches (atk_12_patch.diff: `while True: pass` before the post-patch return; atk_13_patch.diff: loop-until-guess-matches) and RAN them through the OFFICIAL harness (swebench_unified.harness.run_resolve, timeout=1200, retries=0):
  atk_12_patch.diff -> {resolved: False, completed: False} (no report.json; the infinite loop consumed the 1200s test timeout)
  atk_13_patch.diff -> {resolved: False, completed: False} (same)
  gold_patch.diff (POSITIVE CONTROL, same image) -> {resolved: True, completed: True, note: resolved}
The gold resolving on the same image proves completed=False for atk_12/13 is the DETERMINISTIC HANG, not an image/infra failure (both divergence containers ran ~22 min identically before kill).

WHY THIS IS SOUND, NOT BROKEN:
1) The framework's BROKEN criterion (construct/build_one.py:_derive_audit_verdict, line 306-309) requires `r.completed AND not r.resolved`. A divergent patch CANNOT complete by construction -> completed=False -> the derivation routes it to inconclusive_hits (line 310-312), explicitly NOT BROKEN. The design fails such candidates toward inconclusive precisely so a hang cannot masquerade as a proof of verify-not-correct.
2) Non-termination is PERMITTED BY DESIGN under `partial` semantics (401/500 velvet bundles use partial). Vacuous-satisfaction-via-divergence is a UNIVERSAL partial-correctness property, independent of THIS spec's strength or refinement fidelity. Ruling it out would require `termination "total"` + `decreasing` — a strictly stronger obligation outside the refinement-fidelity gate's scope. It is therefore not a defect in this bundle.
3) The genuine G-EQ question — does the frozen spec admit a TERMINATING wrong-output impl? — is answered NO: the exact-equality postcondition pins the output over the whole non-empty-ancestry domain; 11 distinct terminating wrong impls (trivial, partial-domain, boundary, control-flow, over-approx, ungrounded-echo-shape, prepatch) are all rejected, positive control verifies.

REFINEMENT.md AUDIT: axioms=[] (meta), G-AX=skip -> NO A-legs to attack, no callee-contract correspondence to break. The sole deep-model reference (isFamilyMember/derivesFrom) is R/I (not an axiom), backstopped by G-CONF (recorded 100,393 inputs, 0 disagreements, seed 14238, gold applied). Every leg is R or I; NO kind-3 (inexpressible-changed-op) leg — the only changed op (per-base test identity->derivation) is modeled deeply as ancestry.contains, not hidden behind an axiom. model<->patch correspondence (isFamilyMember(ancestry) <-> issubclass(candidate, AutoField)) holds. No ungrounded-oracle echo possible: isFamilyMember is a concrete computable def over a free input, no answer-key to echo.

CONCLUSION: >5 attacks run, prepatch reproduced, positive control verifies, refinement clean; the only verifying wrong impls are divergent and structurally cannot yield a completed not-resolved verdict (permitted by partial semantics). VERDICT: SOUND. Scratch dir (attacks, patches, resolve_*.out, NOTES.md).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, VERIFYING, TERMINATING implementation returns a wrong value: the load-bearing postcondition `ensures result = isFamilyMember ancestry` is an exact functional equality that forces any verifying terminating impl to compute isFamilyMember on the whole domain (require ancestry != []). The only verifying wrong impls are DIVERGENT (atk_12/atk_13, while-true), and their faithful patches cannot resolve-complete (they hang), so they are not valid verify-and-not-correct counterexamples (see notes).
```

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The recognition decision is pure boolean / list-frame
--  logic over a FREE INPUT: the ancestry of the candidate type. The membership
--  predicate that decides whether one type derives from another is the language's
--  own total structural relation over a type's linearised ancestor list — the
--  operation reads that ancestry, it never reshapes any outside object, so there
--  is no callee contract to assume and nothing for G-AX.)
-- axioms-end

-- pure-start
/- A type's ancestry is modeled as the linearised list of the identifiers of the
   types it derives from, the candidate type itself listed first (mapping.md §2).
   Identifiers are abstract tags; three of them denote the family's recognised
   base types. -/

/- The root recognised base type (a candidate that derives from it is recognised
   directly). -/
def rootBaseId : Nat := 0

/- The two further recognised base types of the family. A candidate that derives
   from either of them is also a member of the family — derivation, not mere
   identity with one of these bases, is what matters. -/
def subBaseIds : List Nat := [1, 2]

/- Whether one type derives from another: the target base appears in the
   candidate's ancestry. Reflexive (a type's ancestry lists itself) and total. -/
def derivesFrom (ancestry : List Nat) (baseId : Nat) : Bool :=
  ancestry.contains baseId

/- The recognition decision, modeled deeply. A candidate type is a member of the
   family exactly when it derives from ANY recognised base type: from one of the
   two sub-bases, OR from the root base. Genuine derivation throughout — being
   identical to a base is just the reflexive case of deriving from it, and is
   neither necessary (a proper descendant qualifies) nor specially privileged. -/
def isFamilyMember (ancestry : List Nat) : Bool :=
  (subBaseIds.any (fun b => derivesFrom ancestry b)) || derivesFrom ancestry rootBaseId

@[grind] lemma isFamilyMember_def (ancestry : List Nat) :
    isFamilyMember ancestry =
      ((subBaseIds.any (fun b => derivesFrom ancestry b)) || derivesFrom ancestry rootBaseId) :=
  rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a candidate type is recognised as a member of the family.
   Desired behaviour: a candidate is recognised exactly when it genuinely derives
   from a recognised base type — from one of the family's specialised base types
   or from its root base. A type that descends from a specialised base must be
   recognised even when it is not itself one of those bases; recognition is by
   derivation, not by identity. The candidate's ancestry (`ancestry`) is
   read-only and a candidate always has a non-empty ancestry (it lists itself). -/
method recognizeType (ancestry : List Nat) return (result : Bool)
  require ancestry ≠ []
  ensures result = isFamilyMember ancestry
  ensures (subBaseIds.any (fun b => derivesFrom ancestry b)) = true → result = true
  ensures derivesFrom ancestry rootBaseId = true → result = true
  do
    -- impl-start
    return (rootBaseId :: subBaseIds).any (fun b => derivesFrom ancestry b)
    -- impl-end

prove_correct recognizeType by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SETUP: 13 same-spec attacks + 1 positive control, built by editing ONLY the impl region of Solution.lean (axioms/pure/pre/post byte-identical). same_spec=True confirmed for all 13 via swebench_unified.markers.same_spec on velvet backend. Verified with `bash scripts/lean_verify.sh <file>`.

### TERMINATING ATTACKS (all same-spec, ALL REJECTED, exit 1 — genuine unsolved-goals on ensures_1/ensures_3, not elaboration errors):
  atk_1  prepatch identity bug (subBaseIds.contains ancestry.head!)  -> exit 1 (ensures_1/ensures_3)
  atk_2  return true                                                -> exit 1 (ensures_3: true = isFamilyMember)
  atk_3  return false                                               -> exit 1 (ensures_1)
  atk_4  only root leg                                              -> exit 1 (ensures_2/eq)
  atk_5  only sub-bases (drop root)                                 -> exit 1 (ensures_1)
  atk_6  && instead of ||                                           -> exit 1 (ensures_1)
  atk_7  drop SmallAutoField id 2                                   -> exit 1 (ensures_2/eq)
  atk_8  over-approx: add spurious base id 3                        -> exit 1 (ensures_3)
  atk_9  drop head (reflexive), derive over tail                    -> exit 1 (ensures_1)
  atk_10 if/else identity-only on head                             -> exit 1 (ensures_3: true = isFamilyMember)
  atk_11 isFamilyMember && (ancestry.length > 1)                    -> exit 1 (ensures_3)
POSITIVE CONTROL pc.lean: (rootBaseId :: subBaseIds).any (ancestry.contains .) — structurally different, correct -> exit 0 VERIFIES. prepatch_reproduced=True (atk_1 == Solution_prepatch.lean semantics).

### DIVERGENCE PROBES (disclosed, investigated end-to-end, EXCLUDED from the candidate set — not valid counterexamples):
  atk_12 `while true do i:=i+1; return !(isFamilyMember ancestry)`         -> lean_verify exit 0 VERIFIES (only a 'loop invariant assumed True' warning)
  atk_13 `guess:=sub-only; while guess != isFamilyMember do i:=i+1; return guess` -> lean_verify exit 0 VERIFIES
Both verify because `set_option loom.semantics.termination "partial"` (partial correctness) discharges any postcondition vacuously when the return is unreachable. I MATERIALIZED their faithful refined patches (atk_12_patch.diff: `while True: pass` before the post-patch return; atk_13_patch.diff: loop-until-guess-matches) and RAN them through the OFFICIAL harness (swebench_unified.harness.run_resolve, timeout=1200, retries=0):
  atk_12_patch.diff -> {resolved: False, completed: False} (no report.json; the infinite loop consumed the 1200s test timeout)
  atk_13_patch.diff -> {resolved: False, completed: False} (same)
  gold_patch.diff (POSITIVE CONTROL, same image) -> {resolved: True, completed: True, note: resolved}
The gold resolving on the same image proves completed=False for atk_12/13 is the DETERMINISTIC HANG, not an image/infra failure (both divergence containers ran ~22 min identically before kill).

WHY THIS IS SOUND, NOT BROKEN:
1) The framework's BROKEN criterion (construct/build_one.py:_derive_audit_verdict, line 306-309) requires `r.completed AND not r.resolved`. A divergent patch CANNOT complete by construction -> completed=False -> the derivation routes it to inconclusive_hits (line 310-312), explicitly NOT BROKEN. The design fails such candidates toward inconclusive precisely so a hang cannot masquerade as a proof of verify-not-correct.
2) Non-termination is PERMITTED BY DESIGN under `partial` semantics (401/500 velvet bundles use partial). Vacuous-satisfaction-via-divergence is a UNIVERSAL partial-correctness property, independent of THIS spec's strength or refinement fidelity. Ruling it out would require `termination "total"` + `decreasing` — a strictly stronger obligation outside the refinement-fidelity gate's scope. It is therefore not a defect in this bundle.
3) The genuine G-EQ question — does the frozen spec admit a TERMINATING wrong-output impl? — is answered NO: the exact-equality postcondition pins the output over the whole non-empty-ancestry domain; 11 distinct terminating wrong impls (trivial, partial-domain, boundary, control-flow, over-approx, ungrounded-echo-shape, prepatch) are all rejected, positive control verifies.

REFINEMENT.md AUDIT: axioms=[] (meta), G-AX=skip -> NO A-legs to attack, no callee-contract correspondence to break. The sole deep-model reference (isFamilyMember/derivesFrom) is R/I (not an axiom), backstopped by G-CONF (recorded 100,393 inputs, 0 disagreements, seed 14238, gold applied). Every leg is R or I; NO kind-3 (inexpressible-changed-op) leg — the only changed op (per-base test identity->derivation) is modeled deeply as ancestry.contains, not hidden behind an axiom. model<->patch correspondence (isFamilyMember(ancestry) <-> issubclass(candidate, AutoField)) holds. No ungrounded-oracle echo possible: isFamilyMember is a concrete computable def over a free input, no answer-key to echo.

CONCLUSION: >5 attacks run, prepatch reproduced, positive control verifies, refinement clean; the only verifying wrong impls are divergent and structurally cannot yield a completed not-resolved verdict (permitted by partial semantics). VERDICT: SOUND. Scratch dir (attacks, patches, resolve_*.out, NOTES.md).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-repo) verified for django__django-14238 velvet bundle.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True — the spec view (options, axioms comment, pure region isFamilyMember/derivesFrom/subBaseIds/rootBaseId, method recognizeType signature with require + 3 ensures) is byte-identical between patched and prepatch; only impl/proof regions differ. Solution.lean elaborates clean (lean_verify.sh exit 0).

MODEL: recognizeType(ancestry:List Nat) with isFamilyMember = (subBaseIds.any derivesFrom) || derivesFrom rootBaseId, derivesFrom = ancestry.contains, subBaseIds=[1,2], rootBaseId=0. Bijection: subclass ↔ [id(c) for c in subclass.__mro__]; Big/SmallAutoField↦1,2; AutoField↦0; issubclass(x,B) ↔ B∈ancestry.

REAL CALLEE at base_commit 30e123ed (worktree, __init__.py:2498-2499): AutoFieldMeta.__subclasscheck__ = issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass), _subclasses=(BigAutoField,SmallAutoField). Confirmed present verbatim in worktree.

EMPIRICAL FAITHFULNESS CHECK: modeled isFamilyMember vs real issubclass(candidate, AutoField):
- reflexive bases AutoField/BigAutoField/SmallAutoField → both True
- proper descendants MyBig(BigAutoField)/MySmall/DeepBig(MyBig)/MyAuto(AutoField) → both True (the discriminating post-patch cases)
- unrelated IntegerField/Field/int/object → both False
- pinned seed random.Random(14238) fuzz over ~1150 random single/multiple-inheritance hierarchies built from the field classes → 0 mismatches.

No diverging input found. The spec is not too strong and does not drift: it captures exactly the post-patch derivation (issubclass) semantics, subsuming the reflexive identity case and adding the proper-descendant recognition the gold patch introduces. The 3 postconditions are all satisfied by the real behavior. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True: the spec region is byte-identical between patched and prepatch, so the leak surface is exactly the consumer spec view (impl + prove_correct bodies are elided). Reviewed the full spec_view output.

Gold edit: in AutoFieldMeta.__subclasscheck__ (django/db/models/fields/__init__.py:2523), `subclass in self._subclasses` -> `issubclass(subclass, self._subclasses)` — recognize proper subclasses of BigAutoField/SmallAutoField, not just identity matches.

Public problem_statement ALREADY discloses the entire behavioral delta: it names the failing site ('subclasses of BigAutoField and SmallAutoField'), names the exact function and property ('This can be fixed in AutoFieldMeta.__subclasscheck__ by allowing subclasses of those classes in the _subclasses property'), and gives the corrective direction (identity -> subclass/derivation recognition). Thus the identity->derivation semantics are public baseline, not a leak.

Spec view contents vs that baseline:
- Fully abstracted domain (List Nat, rootBaseId=0, subBaseIds=[1,2], derivesFrom=ancestry.contains). NO repo symbols appear: no issubclass, __subclasscheck__, _subclasses, AutoField/BigAutoField/SmallAutoField, MRO, or Django names anywhere in the consumer view.
- The docstring/postconditions state 'recognised when it derives from a recognised base... a proper descendant must be recognised... recognition is by derivation, not by identity' — an abstract restatement of the public 'allowing subclasses of those classes' hint. It does not expose the concrete `in`->`issubclass` transliteration, the repo file/line, or the number/identity of the real base classes beyond what the problem statement gives.
- The gold-reconstruction material (gold hunk text, issubclass mechanics, __init__.py:2523, the in->issubclass change) lives ONLY in refinement.md and mapping.md, which are auditor docs, NOT the consumer spec view.

A consumer holding only the spec view faces an abstract 'does this ancestry list contain one of three base ids (OR-combining a two-element sub-base set with a root base)' problem. Everything behavioral in it is already granted by the public problem_statement; nothing quotes the gold patch or names its repo symbols. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.