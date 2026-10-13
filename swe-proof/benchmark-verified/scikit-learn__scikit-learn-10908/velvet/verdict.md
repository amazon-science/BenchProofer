# P2 adversarial audit — scikit-learn__scikit-learn-10908

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies against this spec, so verify⇏correct could not be exhibited. The spec is the total functional equation `ensures (st, out) = featureNamesRun stOld supplied`, which pins BOTH the post-state (including the `explicit`/`fixed_vocabulary_` side-effect on the rejecting path) AND the output to the fully-grounded pure transition `featureNamesRun` (establish-then-guard-then-project). Because `featureNamesRun` is built entirely from the deeply-modeled `materializeIndex`/`readinessGuard`/`featureList` and there is NO opaque axiom (axioms region has 0 module-level `axiom` decls), there is no answer-key to echo, and every behavioral deviation is rejected as `unsolved goals`.
```

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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,10 +129,6 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
-    st := if st.index = none then materializeIndex supplied st else st
     let out : Except InvErr (List String) :=
       match readinessGuard st with
       | Except.error e => Except.error e
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,10 +129,7 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
-    st := if st.index = none then materializeIndex supplied st else st
+    st := if st.index = none ∧ supplied.isSome then materializeIndex supplied st else st
     let out : Except InvErr (List String) :=
       match readinessGuard st with
       | Except.error e => Except.error e
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,15 +129,8 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
     st := if st.index = none then materializeIndex supplied st else st
-    let out : Except InvErr (List String) :=
-      match readinessGuard st with
-      | Except.error e => Except.error e
-      | Except.ok _    => Except.ok (featureList (st.index.getD []))
-    return out
+    return Except.ok (featureList (st.index.getD []))
     -- impl-end
 
 prove_correct getFeatureInventory by
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,14 +129,11 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
     st := if st.index = none then materializeIndex supplied st else st
     let out : Except InvErr (List String) :=
       match readinessGuard st with
       | Except.error e => Except.error e
-      | Except.ok _    => Except.ok (featureList (st.index.getD []))
+      | Except.ok _    => Except.ok ((st.index.getD []).map (·.1))
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,15 +129,9 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
-    st := if st.index = none then materializeIndex supplied st else st
-    let out : Except InvErr (List String) :=
-      match readinessGuard st with
-      | Except.error e => Except.error e
-      | Except.ok _    => Except.ok (featureList (st.index.getD []))
-    return out
+    let result := featureNamesRun st supplied
+    st := result.1
+    return result.2
     -- impl-end
 
 prove_correct getFeatureInventory by
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,10 +129,9 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
-    st := if st.index = none then materializeIndex supplied st else st
+    st := match st.index with
+          | none   => materializeIndex supplied st
+          | some _ => st
     let out : Except InvErr (List String) :=
       match readinessGuard st with
       | Except.error e => Except.error e
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,10 +129,7 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
-    st := if st.index = none then materializeIndex supplied st else st
+    st := materializeIndex supplied st
     let out : Except InvErr (List String) :=
       match readinessGuard st with
       | Except.error e => Except.error e
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,10 +129,7 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
-    st := if st.index = none then materializeIndex supplied st else st
+    st := if st.index = none then materializeIndex none st else st
     let out : Except InvErr (List String) :=
       match readinessGuard st with
       | Except.error e => Except.error e
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
 /- No consumed axioms. The two unchanged helpers this operation orchestrates —
@@ -129,13 +129,10 @@
   ensures (st, out) = featureNamesRun stOld supplied
   do
     -- impl-start
-    -- Establish the inventory first when one has not yet been established
-    -- (running the unchanged establishment step), then apply the readiness
-    -- guard and, on admission, read back the ordered feature inventory.
     st := if st.index = none then materializeIndex supplied st else st
     let out : Except InvErr (List String) :=
       match readinessGuard st with
-      | Except.error e => Except.error e
+      | Except.error _ => Except.error InvErr.notReady
       | Except.ok _    => Except.ok (featureList (st.index.getD []))
     return out
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged helpers this operation orchestrates —
   the index materializer and the readiness guard — are modeled DEEPLY in the
   `pure` region (`materializeIndex`, `readinessGuard`) and validated equal to
   their real callees by axiom_check.py (G-AX) as A-references, not assumed
   behind an opaque `axiom`. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The two ways the readiness guard can reject a request to read back the
   feature inventory:

     * `notReady`  — the term→index inventory has never been established (the
       estimator has neither been trained nor handed an explicit inventory yet);
     * `emptyIndex` — an inventory was established but contains no terms.

   These are exactly the rejection shapes the desired behavior distinguishes;
   provenance + executable soundness check: mapping.md §3 / axiom_check.py. -/
inductive InvErr where
  | notReady
  | emptyIndex
  deriving DecidableEq, Inhabited

/- The observable state this operation touches, restricted to the two aspects it
   reads and may establish:

     * `index` — the term→position inventory (`none` until established); each
       entry binds a term to its integer position;
     * `explicit` — whether the established inventory was supplied explicitly at
       construction rather than learned from data (`none` until the
       establishment step has run and recorded this fact).

   Every other field of the estimator is untouched and is not part of this
   carrier (mapping.md §2). -/
structure InvState where
  index : Option (List (String × Nat))
  explicit : Option Bool
  deriving DecidableEq, Inhabited

/- Establish the inventory from the explicitly-supplied terms, if any.

   When an explicit term list is supplied, the inventory is the list of terms
   each bound to its position in that list, and the establishment is recorded as
   explicit. When no list is supplied, no inventory is established (the slot
   stays as it was) and the establishment is recorded as non-explicit. This is
   the unchanged establishment helper, modeled deeply (A-reference, G-AX). The
   supplied term list, when present, is required well-formed (non-empty, no
   repeated term) — the domain on which the new behavior is exercised. -/
def materializeIndex (supplied : Option (List String)) (st : InvState) : InvState :=
  match supplied with
  | none        => { st with explicit := some false }
  | some terms  => { index := some terms.zipIdx, explicit := some true }

/- The readiness guard, modeled deeply (A-reference, G-AX): a request is rejected
   when no inventory has been established (`notReady`) or when the established
   inventory is empty (`emptyIndex`); otherwise it is allowed through. -/
def readinessGuard (st : InvState) : Except InvErr Unit :=
  match st.index with
  | none      => Except.error InvErr.notReady
  | some []   => Except.error InvErr.emptyIndex
  | some _    => Except.ok ()

/- The feature inventory read back: the terms of the established index in
   ascending position order. Modeled deeply (the order-by-position projection)
   so the result is produced by the actual inventory, not echoed from an oracle
   (directive 8). -/
def featureList (m : List (String × Nat)) : List String :=
  (m.mergeSort (fun a b => a.2 ≤ b.2)).map (·.1)

/- The whole operation as a pure transition on `(state, result)`: first, when no
   inventory has yet been established, run the establishment step (which may
   establish the explicit inventory and always records the explicit/non-explicit
   fact); then apply the readiness guard; on admission, read back the ordered
   feature inventory; on rejection, surface the rejection while keeping whatever
   state the establishment step left. -/
def featureNamesRun (st : InvState) (supplied : Option (List String)) :
    InvState × Except InvErr (List String) :=
  let st' := if st.index = none then materializeIndex supplied st else st
  let res : Except InvErr (List String) :=
    match readinessGuard st' with
    | Except.error e => Except.error e
    | Except.ok _    => Except.ok (featureList (st'.index.getD []))
  (st', res)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Read back the inventory mapping integer positions to feature names.

   Desired behavior: a feature inventory can be read back not only after the
   estimator has been trained, but also when an inventory was supplied
   explicitly at construction and the estimator has not yet been trained. To
   make that possible, the read-back must first establish the inventory when one
   has not yet been established — running the same establishment step the
   training path uses — and only then apply the readiness guard. With that step
   in place, supplying an explicit inventory lets the inventory be read back
   without a prior training run, instead of being rejected as not-yet-ready (the
   behavior the public problem statement asks for). When no inventory has been
   established and none was supplied explicitly, the request is still rejected as
   not-yet-ready — but the establishment step has by then recorded that the
   (absent) inventory is non-explicit. When the inventory was already
   established, nothing is established anew and the request proceeds straight to
   the guard. On admission the result is the established inventory's terms in
   ascending position order.

   `st` is the estimator state (`mut`): the establishment step may write the
   inventory and the explicit/non-explicit fact, so its post-state is pinned
   exactly by `featureNamesRun` (directive 5: when nothing is established anew —
   the already-established case — the post-state equals the entry state, which
   `featureNamesRun` returns verbatim). `supplied` is the read-only explicit
   inventory parameter; when present it is required well-formed (mapping.md §2). -/
method getFeatureInventory (mut st : InvState) (supplied : Option (List String))
    return (out : Except InvErr (List String))
  require (match supplied with
            | none       => True
            | some terms => terms ≠ [] ∧ terms.Nodup)
  ensures (st, out) = featureNamesRun stOld supplied
  do
    -- impl-start
    -- Establish the inventory first when one has not yet been established
    -- (running the unchanged establishment step), then apply the readiness
    -- guard and, on admission, read back the ordered feature inventory.
    st := if st.index = none then materializeIndex supplied st else st
    let out : Except InvErr (List String) :=
      match readinessGuard st with
      | Except.error e => Except.error e
      | Except.ok _    => Except.ok (featureList (st.index.getD []))
    return out
    -- impl-end

prove_correct getFeatureInventory by
  loom_solve
  simp_all only [featureNamesRun, materializeIndex, readinessGuard]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: Ran with venv swebench-lean active. All 9 attacks + positive control confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet) = True. Verified each with `timeout ... bash scripts/lean_verify.sh <path>` concurrently in batches of 4. Positive control pos.lean = exact Solution.lean copy: exit 0 (verifies). RESULTS (exit codes): atk_1..atk_9 all exit=1 (error), pos exit=0.

### ATTACK CATALOG (all same_spec=True, all edit ONLY impl region; verify command `bash scripts/lean_verify.sh <path>`):
- atk_1 [PREPATCH BUG]: omit establishment, straight to guard, st untouched. exit=1, error `139:34: unsolved goals`. Prepatch bug REPRODUCED (matches Solution_prepatch.lean impl).
- atk_2 [PARTIAL-DOMAIN]: establish only when st.index=none AND supplied.isSome; drops the `explicit:=false` side-effect in none/none case. exit=1 unsolved goals.
- atk_3 [CONTROL-FLOW/GUARD-DROP]: establish then return list unconditionally, skipping readinessGuard. exit=1 (136:34 unsolved goals).
- atk_4 [BOUNDARY]: return terms UNSORTED (map raw index list, skip featureList's mergeSort). exit=1 unsolved goals.
- atk_5 [UNGROUNDED-ORACLE ECHO]: literally `featureNamesRun st supplied` echoed. exit=1 `139:2: No goals to be solved` — this is an EXTENSIONALLY-CORRECT reformulation over-closed by the frozen tactic, i.e. NOT a wrong-impl-that-verifies; does not break spec.
- atk_6 [REFORMULATION]: match on st.index instead of if. exit=1 (142:34 unsolved goals) — also extensionally correct, brittle vs frozen tactic; not a breaking case.
- atk_7 [CONTROL-FLOW-EFFECT]: materializeIndex unconditionally (drop hasattr guard) → clobbers already-established state. exit=1 (140:34 unsolved goals).
- atk_8 [PARTIAL-DOMAIN / oracle-echo probe]: establishment ignores `supplied` (always materializeIndex none) → explicit-untrained never read back. exit=1 (140:34 unsolved goals).
- atk_9 [WRONG-ERROR-KIND]: conflate rejections, map emptyIndex→notReady. exit=1 (140:34 unsolved goals).

No verifying wrong impl exists ⇒ per protocol no faithful refined patch needed materializing/run_resolve (patches={}). The prepatch bug and ≥4-6 distinct classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-error-kind) were each encoded and verified.

REFINEMENT.MD AUDIT: legs A1/A2 = R, A3 = I + A-reference, A4 = A-reference, A5 = I. No kind-3 (inexpressible-changed-op) leg — the changed control flow is modeled concretely, not hidden behind an axiom. A-reference correspondence holds: materializeIndex↔_validate_vocabulary (text.py:273), readinessGuard↔_check_vocabulary (text.py:301), featureList↔the return comprehension; validated by G-AX (meta.json: 6 boundary + 5000 fuzz, pass) and confirmed empty axioms region (0 module-level `axiom`). No ungrounded oracle. Section C's no-kind-3 claim and Section D's verify⇒resolve argument check out.

VERDICT SOUND: ≥5 distinct attacks (9 total) run, positive control verifies, prepatch reproduced, and no verifying wrong impl breaks the spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verifies against this spec, so verify⇏correct could not be exhibited. The spec is the total functional equation `ensures (st, out) = featureNamesRun stOld supplied`, which pins BOTH the post-state (including the `explicit`/`fixed_vocabulary_` side-effect on the rejecting path) AND the output to the fully-grounded pure transition `featureNamesRun` (establish-then-guard-then-project). Because `featureNamesRun` is built entirely from the deeply-modeled `materializeIndex`/`readinessGuard`/`featureList` and there is NO opaque axiom (axioms region has 0 module-level `axiom` decls), there is no answer-key to echo, and every behavioral deviation is rejected as `unsolved goals`.
```

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

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged helpers this operation orchestrates —
   the index materializer and the readiness guard — are modeled DEEPLY in the
   `pure` region (`materializeIndex`, `readinessGuard`) and validated equal to
   their real callees by axiom_check.py (G-AX) as A-references, not assumed
   behind an opaque `axiom`. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The two ways the readiness guard can reject a request to read back the
   feature inventory:

     * `notReady`  — the term→index inventory has never been established (the
       estimator has neither been trained nor handed an explicit inventory yet);
     * `emptyIndex` — an inventory was established but contains no terms.

   These are exactly the rejection shapes the desired behavior distinguishes;
   provenance + executable soundness check: mapping.md §3 / axiom_check.py. -/
inductive InvErr where
  | notReady
  | emptyIndex
  deriving DecidableEq, Inhabited

/- The observable state this operation touches, restricted to the two aspects it
   reads and may establish:

     * `index` — the term→position inventory (`none` until established); each
       entry binds a term to its integer position;
     * `explicit` — whether the established inventory was supplied explicitly at
       construction rather than learned from data (`none` until the
       establishment step has run and recorded this fact).

   Every other field of the estimator is untouched and is not part of this
   carrier (mapping.md §2). -/
structure InvState where
  index : Option (List (String × Nat))
  explicit : Option Bool
  deriving DecidableEq, Inhabited

/- Establish the inventory from the explicitly-supplied terms, if any.

   When an explicit term list is supplied, the inventory is the list of terms
   each bound to its position in that list, and the establishment is recorded as
   explicit. When no list is supplied, no inventory is established (the slot
   stays as it was) and the establishment is recorded as non-explicit. This is
   the unchanged establishment helper, modeled deeply (A-reference, G-AX). The
   supplied term list, when present, is required well-formed (non-empty, no
   repeated term) — the domain on which the new behavior is exercised. -/
def materializeIndex (supplied : Option (List String)) (st : InvState) : InvState :=
  match supplied with
  | none        => { st with explicit := some false }
  | some terms  => { index := some terms.zipIdx, explicit := some true }

/- The readiness guard, modeled deeply (A-reference, G-AX): a request is rejected
   when no inventory has been established (`notReady`) or when the established
   inventory is empty (`emptyIndex`); otherwise it is allowed through. -/
def readinessGuard (st : InvState) : Except InvErr Unit :=
  match st.index with
  | none      => Except.error InvErr.notReady
  | some []   => Except.error InvErr.emptyIndex
  | some _    => Except.ok ()

/- The feature inventory read back: the terms of the established index in
   ascending position order. Modeled deeply (the order-by-position projection)
   so the result is produced by the actual inventory, not echoed from an oracle
   (directive 8). -/
def featureList (m : List (String × Nat)) : List String :=
  (m.mergeSort (fun a b => a.2 ≤ b.2)).map (·.1)

/- The whole operation as a pure transition on `(state, result)`: first, when no
   inventory has yet been established, run the establishment step (which may
   establish the explicit inventory and always records the explicit/non-explicit
   fact); then apply the readiness guard; on admission, read back the ordered
   feature inventory; on rejection, surface the rejection while keeping whatever
   state the establishment step left. -/
def featureNamesRun (st : InvState) (supplied : Option (List String)) :
    InvState × Except InvErr (List String) :=
  let st' := if st.index = none then materializeIndex supplied st else st
  let res : Except InvErr (List String) :=
    match readinessGuard st' with
    | Except.error e => Except.error e
    | Except.ok _    => Except.ok (featureList (st'.index.getD []))
  (st', res)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Read back the inventory mapping integer positions to feature names.

   Desired behavior: a feature inventory can be read back not only after the
   estimator has been trained, but also when an inventory was supplied
   explicitly at construction and the estimator has not yet been trained. To
   make that possible, the read-back must first establish the inventory when one
   has not yet been established — running the same establishment step the
   training path uses — and only then apply the readiness guard. With that step
   in place, supplying an explicit inventory lets the inventory be read back
   without a prior training run, instead of being rejected as not-yet-ready (the
   behavior the public problem statement asks for). When no inventory has been
   established and none was supplied explicitly, the request is still rejected as
   not-yet-ready — but the establishment step has by then recorded that the
   (absent) inventory is non-explicit. When the inventory was already
   established, nothing is established anew and the request proceeds straight to
   the guard. On admission the result is the established inventory's terms in
   ascending position order.

   `st` is the estimator state (`mut`): the establishment step may write the
   inventory and the explicit/non-explicit fact, so its post-state is pinned
   exactly by `featureNamesRun` (directive 5: when nothing is established anew —
   the already-established case — the post-state equals the entry state, which
   `featureNamesRun` returns verbatim). `supplied` is the read-only explicit
   inventory parameter; when present it is required well-formed (mapping.md §2). -/
method getFeatureInventory (mut st : InvState) (supplied : Option (List String))
    return (out : Except InvErr (List String))
  require (match supplied with
            | none       => True
            | some terms => terms ≠ [] ∧ terms.Nodup)
  ensures (st, out) = featureNamesRun stOld supplied
  do
    -- impl-start
    -- Establish the inventory first when one has not yet been established
    -- (running the unchanged establishment step), then apply the readiness
    -- guard and, on admission, read back the ordered feature inventory.
    st := if st.index = none then materializeIndex supplied st else st
    let out : Except InvErr (List String) :=
      match readinessGuard st with
      | Except.error e => Except.error e
      | Except.ok _    => Except.ok (featureList (st.index.getD []))
    return out
    -- impl-end

prove_correct getFeatureInventory by
  loom_solve
  simp_all only [featureNamesRun, materializeIndex, readinessGuard]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: Ran with venv swebench-lean active. All 9 attacks + positive control confirmed byte-identical spec via swebench_unified.markers.same_spec (velvet) = True. Verified each with `timeout ... bash scripts/lean_verify.sh <path>` concurrently in batches of 4. Positive control pos.lean = exact Solution.lean copy: exit 0 (verifies). RESULTS (exit codes): atk_1..atk_9 all exit=1 (error), pos exit=0.

### ATTACK CATALOG (all same_spec=True, all edit ONLY impl region; verify command `bash scripts/lean_verify.sh <path>`):
- atk_1 [PREPATCH BUG]: omit establishment, straight to guard, st untouched. exit=1, error `139:34: unsolved goals`. Prepatch bug REPRODUCED (matches Solution_prepatch.lean impl).
- atk_2 [PARTIAL-DOMAIN]: establish only when st.index=none AND supplied.isSome; drops the `explicit:=false` side-effect in none/none case. exit=1 unsolved goals.
- atk_3 [CONTROL-FLOW/GUARD-DROP]: establish then return list unconditionally, skipping readinessGuard. exit=1 (136:34 unsolved goals).
- atk_4 [BOUNDARY]: return terms UNSORTED (map raw index list, skip featureList's mergeSort). exit=1 unsolved goals.
- atk_5 [UNGROUNDED-ORACLE ECHO]: literally `featureNamesRun st supplied` echoed. exit=1 `139:2: No goals to be solved` — this is an EXTENSIONALLY-CORRECT reformulation over-closed by the frozen tactic, i.e. NOT a wrong-impl-that-verifies; does not break spec.
- atk_6 [REFORMULATION]: match on st.index instead of if. exit=1 (142:34 unsolved goals) — also extensionally correct, brittle vs frozen tactic; not a breaking case.
- atk_7 [CONTROL-FLOW-EFFECT]: materializeIndex unconditionally (drop hasattr guard) → clobbers already-established state. exit=1 (140:34 unsolved goals).
- atk_8 [PARTIAL-DOMAIN / oracle-echo probe]: establishment ignores `supplied` (always materializeIndex none) → explicit-untrained never read back. exit=1 (140:34 unsolved goals).
- atk_9 [WRONG-ERROR-KIND]: conflate rejections, map emptyIndex→notReady. exit=1 (140:34 unsolved goals).

No verifying wrong impl exists ⇒ per protocol no faithful refined patch needed materializing/run_resolve (patches={}). The prepatch bug and ≥4-6 distinct classes (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, wrong-error-kind) were each encoded and verified.

REFINEMENT.MD AUDIT: legs A1/A2 = R, A3 = I + A-reference, A4 = A-reference, A5 = I. No kind-3 (inexpressible-changed-op) leg — the changed control flow is modeled concretely, not hidden behind an axiom. A-reference correspondence holds: materializeIndex↔_validate_vocabulary (text.py:273), readinessGuard↔_check_vocabulary (text.py:301), featureList↔the return comprehension; validated by G-AX (meta.json: 6 boundary + 5000 fuzz, pass) and confirmed empty axioms region (0 module-level `axiom`). No ungrounded oracle. Section C's no-kind-3 claim and Section D's verify⇒resolve argument check out.

VERDICT SOUND: ≥5 distinct attacks (9 total) run, positive control verifies, prepatch reproduced, and no verifying wrong impl breaks the spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True via velvet backend). Solution.lean verifies clean (lean_verify.sh RC=0).

Faithfulness assessment (model vs real repo callees at base_commit 67d06b18): the modeled function featureNamesRun composes materializeIndex (== VectorizerMixin._validate_vocabulary), readinessGuard (== _check_vocabulary), and featureList (== the sorted index-order return comprehension), matching the post-patch get_feature_names control flow (hasattr-guarded establishment before the readiness guard).

Evidence the model does NOT drift from / over-strengthen the real callee:
1. Transcribed the base_commit _validate_vocabulary / _check_vocabulary / post-patch get_feature_names and compared to the Lean model semantics over 200,004 inputs on the modeled domain (supplied = None or a well-formed unique non-empty list; fresh unfitted estimator) -> 0 disagreements. Both outcome (ok/raise), fixed_vocabulary_ side-effect, and index-order term list agree.
2. Live G-AX (axiom_check.py) passes against sklearn: materializeIndex/readinessGuard/featureList all match the real callees over 6 boundary + 5000 fuzz vocabularies, incl. the clause-B2 side effect (unfitted no-vocab records fixed_vocabulary_=False then still raises).
3. featureList Lean semantics verified directly: index-order projection, stable mergeSort on ties, zipIdx = 0-based positions -> matches enumerate/setdefault dict build then sort-by-index.
4. Already-established branch (st.index != none) correctly skips materialization and ignores supplied, mirroring the real 'if not hasattr(self, vocabulary_)' guard; empty established index -> emptyIndex; unset -> notReady (NotFittedError <: ValueError). All match.

The require domain (excluding sets, Mappings, duplicate/empty lists) is a faithful abstraction, not an over-strong spec: every excluded input raises ValueError inside the real _validate_vocabulary too, so no in-domain input exists where the modeled function disagrees with the real callee.

Note: a local run of conformance_check.py reported a FAIL, but this is purely a sklearn-version artifact of the audit host env (sklearn 1.3.0 removed get_feature_names in favor of get_feature_names_out, so the oracle raises AttributeError while the shadow computes the correct modeled behavior). G-CONF is designed to run in-container at base_commit + gold patch, where meta.json records G-CONF status=pass. This is not a model-vs-repo divergence. No diverging input found; spec is FAITHFUL.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: two lines added to get_feature_names — `if not hasattr(self, 'vocabulary_'): self._validate_vocabulary()` before self._check_vocabulary(). The public problem_statement ALREADY discloses this fix mechanism in full: it states 'transform calls _validate_vocabulary method which sets the vocabulary_ instance variable. In the same manner I believe that get_feature_names should not raise NotFittedError if the vocabulary parameter is provided but the vectorizer has not been trained,' and shows hasattr(vectorizer,'vocabulary_') flipping False->True. So establishing the vocabulary in get_feature_names (as transform does) when unfitted, then not raising, is public.

Spec-view review (byte-identical spec region between Solution.lean and Solution_prepatch.lean; same_spec=True): all modeling identifiers are abstract — getFeatureInventory, materializeIndex, readinessGuard, featureList, InvState/InvErr — none echo get_feature_names, _validate_vocabulary, _check_vocabulary, vocabulary_, fixed_vocabulary_, CountVectorizer, or the patched file path sklearn/feature_extraction/text.py. Comments narrate only 'desired behavior' anchored to 'the behavior the public problem statement asks for'; no bug/fix/regression narration. The explicit/fixed_vocabulary_ side-effect (the F2P discriminator in refinement.md §B) is modeled abstractly as `explicit : Option Bool` and is a necessary consequence of the publicly-known establish-then-guard mechanism, not an edit localizer.

Mechanical G-LEAK screen (leakage.screen) run directly: PASSED, hard_failures=[]. No diff markers, no reproduced gold line (>=8 chars), no patched file/module path, no patched-symbol identifier/comment echo, no narration keyword. Bundle is not relaxed (no RELAXED_LEAKAGE.md / relaxed_leakage flag needed). The spec view discloses nothing about the gold edit beyond what the public problem_statement already provides. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
