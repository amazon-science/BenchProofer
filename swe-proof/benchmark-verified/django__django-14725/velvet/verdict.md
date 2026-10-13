# P2 adversarial audit — django__django-14725

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec fully pins BOTH outputs in BOTH branches via four ensures clauses: out = reported noCreate existing fresh; stored = storedAfter noCreate storedOld fresh; noCreate=true → (out=existing ∧ stored=storedOld); noCreate=false → (out=existing++fresh ∧ stored=storedOld++fresh). No behaviorally-wrong impl verifies. The only verifying same-spec impls (atk_6, atk_7) are behavioral echoes of gold (they compute out/stored via the exact reported/storedAfter deep models), and their faithful refined patch IS the gold patch, which resolves.
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
 /- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
@@ -68,16 +68,12 @@
   ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
   do
     -- impl-start
-    -- Branch on the policy flag: when new rows are forbidden, report only the
-    -- already-known identities and leave the stored collection untouched (no
-    -- producing step runs). Otherwise produce the fresh rows — appending their
-    -- identities to the stored collection as a side effect — and report the
-    -- already-known identities followed by the freshly produced ones.
+    -- ATTACK: branches swapped
     if noCreate then
-      return existing
-    else
       stored := stored ++ fresh
       return existing ++ fresh
+    else
+      return existing
     -- impl-end
 
 prove_correct saveFormset by
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
 /- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
@@ -68,16 +68,8 @@
   ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
   do
     -- impl-start
-    -- Branch on the policy flag: when new rows are forbidden, report only the
-    -- already-known identities and leave the stored collection untouched (no
-    -- producing step runs). Otherwise produce the fresh rows — appending their
-    -- identities to the stored collection as a side effect — and report the
-    -- already-known identities followed by the freshly produced ones.
-    if noCreate then
-      return existing
-    else
-      stored := stored ++ fresh
-      return existing ++ fresh
+    -- ATTACK: always report existing, never grow stored
+    return existing
     -- impl-end
 
 prove_correct saveFormset by
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
 /- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
@@ -68,16 +68,12 @@
   ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
   do
     -- impl-start
-    -- Branch on the policy flag: when new rows are forbidden, report only the
-    -- already-known identities and leave the stored collection untouched (no
-    -- producing step runs). Otherwise produce the fresh rows — appending their
-    -- identities to the stored collection as a side effect — and report the
-    -- already-known identities followed by the freshly produced ones.
+    -- ATTACK: wrong report order in permit-new branch
     if noCreate then
       return existing
     else
       stored := stored ++ fresh
-      return existing ++ fresh
+      return fresh ++ existing
     -- impl-end
 
 prove_correct saveFormset by
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
 /- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
@@ -68,12 +68,9 @@
   ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
   do
     -- impl-start
-    -- Branch on the policy flag: when new rows are forbidden, report only the
-    -- already-known identities and leave the stored collection untouched (no
-    -- producing step runs). Otherwise produce the fresh rows — appending their
-    -- identities to the stored collection as a side effect — and report the
-    -- already-known identities followed by the freshly produced ones.
+    -- ATTACK: forbid-new branch silently creates rows
     if noCreate then
+      stored := stored ++ fresh
       return existing
     else
       stored := stored ++ fresh
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
 /- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
@@ -68,15 +68,11 @@
   ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
   do
     -- impl-start
-    -- Branch on the policy flag: when new rows are forbidden, report only the
-    -- already-known identities and leave the stored collection untouched (no
-    -- producing step runs). Otherwise produce the fresh rows — appending their
-    -- identities to the stored collection as a side effect — and report the
-    -- already-known identities followed by the freshly produced ones.
+    -- ATTACK: wrong stored order in permit-new branch
     if noCreate then
       return existing
     else
-      stored := stored ++ fresh
+      stored := fresh ++ stored
       return existing ++ fresh
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
 /- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
@@ -68,16 +68,9 @@
   ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
   do
     -- impl-start
-    -- Branch on the policy flag: when new rows are forbidden, report only the
-    -- already-known identities and leave the stored collection untouched (no
-    -- producing step runs). Otherwise produce the fresh rows — appending their
-    -- identities to the stored collection as a side effect — and report the
-    -- already-known identities followed by the freshly produced ones.
-    if noCreate then
-      return existing
-    else
-      stored := stored ++ fresh
-      return existing ++ fresh
+    -- ATTACK: ungrounded-oracle echo via deep models
+    stored := storedAfter noCreate stored fresh
+    return reported noCreate existing fresh
     -- impl-end
 
 prove_correct saveFormset by
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
@@ -68,16 +68,12 @@
   ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
   do
     -- impl-start
-    -- Branch on the policy flag: when new rows are forbidden, report only the
-    -- already-known identities and leave the stored collection untouched (no
-    -- producing step runs). Otherwise produce the fresh rows — appending their
-    -- identities to the stored collection as a side effect — and report the
-    -- already-known identities followed by the freshly produced ones.
+    -- ATTACK: equivalent, compute out via reported, stored via if
     if noCreate then
-      return existing
+      return reported noCreate existing fresh
     else
       stored := stored ++ fresh
-      return existing ++ fresh
+      return reported noCreate existing fresh
     -- impl-end
 
 prove_correct saveFormset by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
   of are abstracted as free inputs:
     * `existing` — the identities settled by persisting the already-known rows
       of the collection. This step runs identically regardless of the policy
       below, so only its result is needed (an A-reference, mapping.md §3.1).
     * `fresh` — the identities that producing brand-new rows would settle, and,
       as a side effect, add to the stored collection. The relation
       "produced identities = the rows it adds to storage" is the reference
       behaviour of that unchanged producing step, validated against the real
       callee by axiom_check.py (G-AX, an A-reference, mapping.md §3.2). -/
-- axioms-end

-- pure-start
/- The list of identities a persistence pass reports, given the policy and the
   two component results:
     * when creation of brand-new rows is disallowed, only the already-known
       rows' identities are reported;
     * otherwise the already-known identities are followed by the freshly
       produced ones, in that order. -/
def reported (noCreate : Bool) (existing fresh : List Nat) : List Nat :=
  if noCreate then existing else existing ++ fresh

/- The stored collection of brand-new identities after a persistence pass,
   given its prior contents `priorStored`:
     * when creation is disallowed, the stored collection is left untouched;
     * otherwise the freshly produced identities are appended to it. -/
def storedAfter (noCreate : Bool) (priorStored fresh : List Nat) : List Nat :=
  if noCreate then priorStored else priorStored ++ fresh
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Persist a collection of editable rows and report the identities it settled.

   Desired behaviour: a policy flag controls whether persisting may bring brand
   new rows into being. When the flag forbids new rows, the pass settles only
   the already-known rows: it reports just those identities AND leaves the stored
   set of brand-new rows exactly as it found it — producing no new rows as a side
   effect. When the flag permits new rows, the pass reports the already-known
   identities followed by the freshly produced ones, and those fresh rows are
   added to the stored set.

   `existing` and `fresh` are the (read-only) identities the two component
   persistence steps would settle. `stored` is the persistent collection of
   brand-new identities; it is `mut` because the permit-new branch grows it, and
   the forbid-new branch must leave it untouched — pinned explicitly so that an
   implementation reporting an edit-only result cannot silently create rows
   (directive 5). Identities are modeled as `Nat`; order is preserved
   (mapping.md §2). -/
method saveFormset (noCreate : Bool) (existing : List Nat) (fresh : List Nat)
    (mut stored : List Nat) return (out : List Nat)
  ensures out = reported noCreate existing fresh
  ensures stored = storedAfter noCreate storedOld fresh
  ensures noCreate = true → (out = existing ∧ stored = storedOld)
  ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
  do
    -- impl-start
    -- Branch on the policy flag: when new rows are forbidden, report only the
    -- already-known identities and leave the stored collection untouched (no
    -- producing step runs). Otherwise produce the fresh rows — appending their
    -- identities to the stored collection as a side effect — and report the
    -- already-known identities followed by the freshly produced ones.
    if noCreate then
      return existing
    else
      stored := stored ++ fresh
      return existing ++ fresh
    -- impl-end

prove_correct saveFormset by
  loom_solve <;> simp_all [reported, storedAfter]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + positive_control + prepatch confirmed True via swebench_unified.markers.same_spec (velvet tables).

### VERIFY (scripts/lean_verify.sh, 300s, run concurrently ≤4/batch):
- positive_control (gold impl) rc=0 VERIFIES ✓
- prepatch.lean rc=1 (bug reproduced): unsolved goal `noCreate = true → fresh = []` on ensures_2/ensures_3 — prepatch always ran the new-row producer.
- atk_1 (branches swapped) rc=1 REJECTED — unsolved `fresh = []`.
- atk_2 (always return existing; never grow stored) rc=1 REJECTED — fails permit-new clause.
- atk_3 (else: return fresh++existing, wrong order) rc=1 REJECTED.
- atk_4 (control-flow-effect: forbid-new branch silently grows stored) rc=1 REJECTED — fails stored=storedOld frame (unsolved `fresh=[]`). Confirms directive-5 frame is enforced.
- atk_5 (else: stored := fresh++stored, wrong stored order) rc=1 REJECTED — fails stored=storedOld++fresh.
- atk_6 (ungrounded-oracle echo: out:=reported…, stored:=storedAfter…) rc=0 VERIFIES.
- atk_7 (equivalent: branch on noCreate but compute out via reported) rc=0 VERIFIES.

### RESOLVE (run_resolve, swe_bench_verified Docker oracle, timeout 1800):
- atk_6 faithful refined patch (== gold, behavior-identical refinement): resolved=True, completed=True.
- atk_7 faithful refined patch (== gold): resolved=True, completed=True.
Both verifying wrong-shaped attacks' faithful patches RESOLVE ⇒ no verify⇏correct break. This is the resolved echo-attack policy: a same-spec verifying impl whose refined patch resolves is NOT a weakness.

REFINEMENT.MD LEG AUDIT (§4.3): all legs R / A-reference / I; NO kind-3 (inexpressible-changed-op).
- A1 edit_only↔Bool: R.
- A2 existing↔save_existing_objects: R + A-reference. A3 fresh + stored side-effect↔save_new_objects: R + A-reference. A6 mut frame stored=storedOld: R+I.
- A4/A5: I (both branches direct transliterations).
- A-reference correspondence to the REAL unchanged callees holds and is validated directly in axiom_check.py against the live Django ORM: A-ref1 (save_existing_objects flag-independent, creates no rows) and A-ref2 (save_new_objects is sole source of new rows; return == persisted rows), over boundary + 300 fuzz configs. No consumed axioms; the genuinely-changed op (the edit_only guard) is modeled DEEPLY (reported/storedAfter + the if), not hidden behind an axiom about the function under change. Correspondence is sound.

CONCLUSION: The spec is tight — it deterministically pins out and stored in each branch, so verify ⇒ behaviorally-equal-to-gold on the carrier. 7 distinct attacks encoded (partial-domain, boundary, control-flow-effect/directive-5 frame, wrong-order ×2, ungrounded-oracle echo ×2); 5 rejected by the spec, 2 verify and both resolve. verify ⇒ correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec fully pins BOTH outputs in BOTH branches via four ensures clauses: out = reported noCreate existing fresh; stored = storedAfter noCreate storedOld fresh; noCreate=true → (out=existing ∧ stored=storedOld); noCreate=false → (out=existing++fresh ∧ stored=storedOld++fresh). No behaviorally-wrong impl verifies. The only verifying same-spec impls (atk_6, atk_7) are behavioral echoes of gold (they compute out/stored via the exact reported/storedAfter deep models), and their faithful refined patch IS the gold patch, which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. Two unchanged lower-layer steps this routine sits on top
   of are abstracted as free inputs:
     * `existing` — the identities settled by persisting the already-known rows
       of the collection. This step runs identically regardless of the policy
       below, so only its result is needed (an A-reference, mapping.md §3.1).
     * `fresh` — the identities that producing brand-new rows would settle, and,
       as a side effect, add to the stored collection. The relation
       "produced identities = the rows it adds to storage" is the reference
       behaviour of that unchanged producing step, validated against the real
       callee by axiom_check.py (G-AX, an A-reference, mapping.md §3.2). -/
-- axioms-end

-- pure-start
/- The list of identities a persistence pass reports, given the policy and the
   two component results:
     * when creation of brand-new rows is disallowed, only the already-known
       rows' identities are reported;
     * otherwise the already-known identities are followed by the freshly
       produced ones, in that order. -/
def reported (noCreate : Bool) (existing fresh : List Nat) : List Nat :=
  if noCreate then existing else existing ++ fresh

/- The stored collection of brand-new identities after a persistence pass,
   given its prior contents `priorStored`:
     * when creation is disallowed, the stored collection is left untouched;
     * otherwise the freshly produced identities are appended to it. -/
def storedAfter (noCreate : Bool) (priorStored fresh : List Nat) : List Nat :=
  if noCreate then priorStored else priorStored ++ fresh
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Persist a collection of editable rows and report the identities it settled.

   Desired behaviour: a policy flag controls whether persisting may bring brand
   new rows into being. When the flag forbids new rows, the pass settles only
   the already-known rows: it reports just those identities AND leaves the stored
   set of brand-new rows exactly as it found it — producing no new rows as a side
   effect. When the flag permits new rows, the pass reports the already-known
   identities followed by the freshly produced ones, and those fresh rows are
   added to the stored set.

   `existing` and `fresh` are the (read-only) identities the two component
   persistence steps would settle. `stored` is the persistent collection of
   brand-new identities; it is `mut` because the permit-new branch grows it, and
   the forbid-new branch must leave it untouched — pinned explicitly so that an
   implementation reporting an edit-only result cannot silently create rows
   (directive 5). Identities are modeled as `Nat`; order is preserved
   (mapping.md §2). -/
method saveFormset (noCreate : Bool) (existing : List Nat) (fresh : List Nat)
    (mut stored : List Nat) return (out : List Nat)
  ensures out = reported noCreate existing fresh
  ensures stored = storedAfter noCreate storedOld fresh
  ensures noCreate = true → (out = existing ∧ stored = storedOld)
  ensures noCreate = false → (out = existing ++ fresh ∧ stored = storedOld ++ fresh)
  do
    -- impl-start
    -- Branch on the policy flag: when new rows are forbidden, report only the
    -- already-known identities and leave the stored collection untouched (no
    -- producing step runs). Otherwise produce the fresh rows — appending their
    -- identities to the stored collection as a side effect — and report the
    -- already-known identities followed by the freshly produced ones.
    if noCreate then
      return existing
    else
      stored := stored ++ fresh
      return existing ++ fresh
    -- impl-end

prove_correct saveFormset by
  loom_solve <;> simp_all [reported, storedAfter]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + positive_control + prepatch confirmed True via swebench_unified.markers.same_spec (velvet tables).

### VERIFY (scripts/lean_verify.sh, 300s, run concurrently ≤4/batch):
- positive_control (gold impl) rc=0 VERIFIES ✓
- prepatch.lean rc=1 (bug reproduced): unsolved goal `noCreate = true → fresh = []` on ensures_2/ensures_3 — prepatch always ran the new-row producer.
- atk_1 (branches swapped) rc=1 REJECTED — unsolved `fresh = []`.
- atk_2 (always return existing; never grow stored) rc=1 REJECTED — fails permit-new clause.
- atk_3 (else: return fresh++existing, wrong order) rc=1 REJECTED.
- atk_4 (control-flow-effect: forbid-new branch silently grows stored) rc=1 REJECTED — fails stored=storedOld frame (unsolved `fresh=[]`). Confirms directive-5 frame is enforced.
- atk_5 (else: stored := fresh++stored, wrong stored order) rc=1 REJECTED — fails stored=storedOld++fresh.
- atk_6 (ungrounded-oracle echo: out:=reported…, stored:=storedAfter…) rc=0 VERIFIES.
- atk_7 (equivalent: branch on noCreate but compute out via reported) rc=0 VERIFIES.

### RESOLVE (run_resolve, swe_bench_verified Docker oracle, timeout 1800):
- atk_6 faithful refined patch (== gold, behavior-identical refinement): resolved=True, completed=True.
- atk_7 faithful refined patch (== gold): resolved=True, completed=True.
Both verifying wrong-shaped attacks' faithful patches RESOLVE ⇒ no verify⇏correct break. This is the resolved echo-attack policy: a same-spec verifying impl whose refined patch resolves is NOT a weakness.

REFINEMENT.MD LEG AUDIT (§4.3): all legs R / A-reference / I; NO kind-3 (inexpressible-changed-op).
- A1 edit_only↔Bool: R.
- A2 existing↔save_existing_objects: R + A-reference. A3 fresh + stored side-effect↔save_new_objects: R + A-reference. A6 mut frame stored=storedOld: R+I.
- A4/A5: I (both branches direct transliterations).
- A-reference correspondence to the REAL unchanged callees holds and is validated directly in axiom_check.py against the live Django ORM: A-ref1 (save_existing_objects flag-independent, creates no rows) and A-ref2 (save_new_objects is sole source of new rows; return == persisted rows), over boundary + 300 fuzz configs. No consumed axioms; the genuinely-changed op (the edit_only guard) is modeled DEEPLY (reported/storedAfter + the if), not hidden behind an axiom about the function under change. Correspondence is sound.

CONCLUSION: The spec is tight — it deterministically pins out and stored in each branch, so verify ⇒ behaviorally-equal-to-gold on the carrier. 7 distinct attacks encoded (partial-domain, boundary, control-flow-effect/directive-5 frame, wrong-order ×2, ungrounded-oracle echo ×2); 5 rejected by the spec, 2 verify and both resolve. verify ⇒ correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) verdict for django__django-14725 velvet.

Spec-region byte-identity confirmed: swebench_unified markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend) == True — the frozen spec (method signature, ensures clauses, `reported`/`storedAfter` defs, doc comments) is identical between shipped Solution and prepatch; only impl/proof differ. Solution.lean elaborates cleanly (scripts/lean_verify.sh exit 0).

Modeled function `saveFormset` models BaseModelFormSet.save at django/forms/models.py:667 (return expr :683). Gold patch:
  if self.edit_only: return self.save_existing_objects(commit)
  else: return self.save_existing_objects(commit) + self.save_new_objects(commit)

Model: out = if noCreate then existing else existing ++ fresh; stored = if noCreate then storedOld else storedOld ++ fresh, with noCreate<->edit_only and existing/fresh the two callee results as FREE inputs (A-references, checked separately by G-AX).

Exhaustive input-class comparison against the real base-commit callee (worktree, base 0af9a5fc7d, edit_only absent pre-patch as expected):
- noCreate=false: real returns save_existing_objects + save_new_objects (list concat, existing-then-fresh order) == model existing ++ fresh. Agrees for all inputs (parametric in the free inputs).
- noCreate=true: real returns ONLY save_existing_objects and never calls save_new_objects; verified save_existing_objects (:788) iterates only initial_forms and never inserts, while save_new_objects (:814) is the sole inserter of brand-new rows -> persisted set untouched == model out=existing, stored=storedOld. Agrees.
- Side-effect frame (mut stored ++ fresh) matches save_new_objects appending its returned instances to new_objects under the F2P commit=True path; commit=False variance is a callee-provenance matter delegated to G-AX, not spec drift (fresh is a free input).

Because existing/fresh are free inputs and the concrete claims are a direct transliteration of the gold branch (order-preserving ++, suppression + frame under noCreate), the modeled function agrees with the real save on every input. No diverging input exists; the spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: the consumer spec view is the spec_view projection of Solution.lean (impl/proof regions elided); refinement.md and mapping.md are auditor-facing derivation docs, NOT part of the consumer spec view, so their naming of edit_only/save_existing_objects/save_new_objects and their verbatim gold hunk are out of scope for this gate.

Mechanical G-LEAK screen: PASS (no hard failures). Verified via swebench_unified.leakage.screen over the real velvet spec_view against the frozen patch + problem_statement. same_spec(Solution.lean, Solution_prepatch.lean) = True (spec region byte-identical between pre/post — spec doesn't smuggle the impl).

Gold edit: adds edit_only kwarg; in BaseModelFormSet.save, when edit_only, return save_existing_objects(commit) only (skip save_new_objects); threads flag through modelformset_factory / inlineformset_factory. Changed symbols: inlineformset_factory, modelformset_factory, save_m2m.

Semantic review of the spec view:
- Identifiers are all abstract (saveFormset, noCreate, existing, fresh, stored, reported, storedAfter). None embed/echo a patched repo symbol (edit_only, save_existing_objects, save_new_objects) or the patched file/module path django/forms/models.py.
- No diff markers, no verbatim gold-patch line, no patched path/module.
- Comment prose restates DESIRED BEHAVIOR abstractly: a policy flag controls whether persisting may create brand-new rows; forbid-new => report only already-known identities and leave stored untouched. This is a faithful paraphrase of the PUBLIC problem_statement ('disallow new object creation', an 'edit only view of objects'), not repo-specific edit localization.
- No bug/fix/patch/regression narration.

The existing-vs-new decomposition and the noCreate branch are inherent to the publicly-stated task (edit-only = keep existing, block new-object creation) and constitute the spec's legitimate purpose (stating required behavior), not a reveal of gold internals beyond problem_statement. Nothing in the spec view discloses where in the repo the edit lands, which symbols change, or the concrete gold lines. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
