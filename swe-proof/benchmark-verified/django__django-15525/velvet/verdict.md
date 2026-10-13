# P2 adversarial audit — django__django-15525

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,10 +59,7 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
-    storeHandle := some targetDb
+    -- ATTACK: prepatch bug. Derive from the still-unset handle; never associate.
     let key := naturalKeyVia storeHandle
     return key
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,11 +59,9 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
+    -- ATTACK: derive-before-associate. Key computed at the pre-state (none) handle.
+    let key := naturalKeyVia storeHandle
     storeHandle := some targetDb
-    let key := naturalKeyVia storeHandle
     return key
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,11 +59,10 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
+    -- ATTACK: associate correctly, but route the derivation through a hardcoded
+    -- unset handle instead of the updated one.
     storeHandle := some targetDb
-    let key := naturalKeyVia storeHandle
+    let key := naturalKeyVia none
     return key
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,11 +59,9 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
-    storeHandle := some targetDb
-    let key := naturalKeyVia storeHandle
+    -- ATTACK: ungrounded-oracle echo. Return the exact key expression from the
+    -- postcondition WITHOUT associating the record (handle left unset).
+    let key := naturalKeyVia (some targetDb)
     return key
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,10 +59,8 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
-    storeHandle := some targetDb
+    -- ATTACK: associate with the WRONG database (a hardcoded default), then derive.
+    storeHandle := some "default"
     let key := naturalKeyVia storeHandle
     return key
     -- impl-end
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,12 +59,9 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
+    -- ATTACK: associate correctly but return an empty key (partial-domain / stub).
     storeHandle := some targetDb
-    let key := naturalKeyVia storeHandle
-    return key
+    return []
     -- impl-end
 
 prove_correct naturalKeyForLoadedRecord by
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,11 +59,12 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
+    -- ATTACK: snapshot the handle BEFORE associating, then derive from the stale
+    -- snapshot even though the live handle is updated. Handle post-state is correct
+    -- (ensures_2 holds) but the key is derived at the old (none) handle.
+    let stale := storeHandle
     storeHandle := some targetDb
-    let key := naturalKeyVia storeHandle
+    let key := naturalKeyVia stale
     return key
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,10 +59,9 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
-    storeHandle := some targetDb
+    -- ATTACK: boundary. Assign the unset value literally (no real association),
+    -- then derive from it.
+    storeHandle := none
     let key := naturalKeyVia storeHandle
     return key
     -- impl-end
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
 /- The natural-key derivation for a record, as it depends on the record's
@@ -59,12 +59,11 @@
   ensures key = naturalKeyVia (some targetDb)
   do
     -- impl-start
-    -- Associate the freshly built record with the target database, THEN derive
-    -- the natural key from that updated handle (the derivation reads the handle
-    -- and routes reference-following to the named database).
+    -- ATTACK: associate the record with the target DB, then return the postcondition
+    -- key expression directly (echo) rather than reading it back from the handle.
+    -- Both ensures clauses hold ⇒ this VERIFIES; its faithful patch must be tested.
     storeHandle := some targetDb
-    let key := naturalKeyVia storeHandle
-    return key
+    return naturalKeyVia (some targetDb)
     -- impl-end
 
 prove_correct naturalKeyForLoadedRecord by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The natural-key derivation for a record, as it depends on the record's
   STORE HANDLE — the identifier of the database the record is currently
   associated with. The derivation may follow references to related records,
   and each such reference is resolved against the database named by the store
   handle; so the resulting key is a function of that handle. This is an
   UNCHANGED routine the operation defers to: it is left OPAQUE (a free
   function), refined never replaced, so no contract is claimed about WHAT it
   returns — only that the operation feeds it the right handle. Because nothing
   is asserted about its value there is nothing to validate against the real
   routine (no axiom_check.py — meta.json G-AX skip). Provenance: mapping.md. -/
opaque naturalKeyVia : Option String → List String
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Deriving the natural key of a freshly built record while loading it into a
   target database.

   A record's natural key may follow references to related records, and those
   references are resolved against whichever database the record is currently
   associated with (its STORE HANDLE). A freshly built record carries no store
   handle yet (`none`). When the record is being loaded into a particular
   target database, the natural key must be derived as that target database
   would see it, so that reference-following resolves against the same database
   the record is being loaded into.

   The desired behavior: associate the record with the target database FIRST —
   set its store handle to that database — and only THEN derive the natural key,
   so the reference-following derivation is routed to the target database.

   `storeHandle` is the record's mutable database association. It comes in
   unset (`none`) for a freshly built record and is genuinely mutated to the
   target database; its post-state is pinned EXACTLY to `some targetDb`
   (directive 5: the changed frame is stated at its exact post-state). The
   returned key is the derivation evaluated at that updated handle, so it is
   grounded in the input `targetDb` (the key is `naturalKeyVia (some targetDb)`,
   the derivation at the target-database handle). -/
method naturalKeyForLoadedRecord (targetDb : String) (mut storeHandle : Option String)
    return (key : List String)
  require storeHandle = none
  ensures storeHandle = some targetDb
  ensures key = naturalKeyVia (some targetDb)
  do
    -- impl-start
    -- Associate the freshly built record with the target database, THEN derive
    -- the natural key from that updated handle (the derivation reads the handle
    -- and routes reference-following to the named database).
    storeHandle := some targetDb
    let key := naturalKeyVia storeHandle
    return key
    -- impl-end

prove_correct naturalKeyForLoadedRecord by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is byte-identical frozen (same_spec=True for all 9 attacks + pos_control + prepatch). Method naturalKeyForLoadedRecord pins TWO ensures: (e1) key = naturalKeyVia (some targetDb); (e2) storeHandle = some targetDb; precondition require storeHandle = none. naturalKeyVia is an opaque A-reference (unchanged obj.natural_key(), NO asserted contract). Soundness crux = derive-AFTER-associate ordering, since e1 pins the derivation at the POST-assignment handle.

TOOLING: project root = (NOT the /home path in the prompt, which lacks scripts/). Verified via `bash scripts/lean_verify.sh <file>`; same_spec via swebench_unified.markers.same_spec + get_backend('velvet'); resolve via swebench_unified.harness.run_resolve. Attack verifications run concurrently in batches of <=4 background jobs.

BASELINE: pos_control.lean (=gold impl) exit 0 (VERIFIES). prepatch.lean exit 1 — fails on exactly ensures_1 (naturalKeyVia storeHandleOld = naturalKeyVia (some targetDb)) AND ensures_2 (storeHandleOld = some targetDb), matching refinement.md B verbatim (prepatch reproduced, fails for the RIGHT reason).

### ATTACKS (all same_spec=True; edited ONLY impl region):
- atk_1 (prepatch bug: derive at unset handle, never assign): exit 1 — fails e1 + e2.
- atk_2 (control-flow-effect: derive-BEFORE-assign order swap): exit 1 — fails e1 (deriv at storeHandleOld=none). The ordering trap: caught.
- atk_3 (assign handle, derive at literal none): exit 1 — fails e1 (naturalKeyVia none).
- atk_4 (ungrounded-oracle ECHO, no assign): exit 1 — e1 satisfied by echo but e2 (storeHandleOld=some targetDb) rejects; the companion state clause defeats a pure echo.
- atk_5 (assign WRONG handle some "default", derive): exit 1 — fails e1 + e2.
- atk_6 (partial/stub: assign handle, return []): exit 1 — fails e1 ([] = naturalKeyVia (some targetDb)).
- atk_7 (stale-read: snapshot handle before assign, derive from stale; e2 holds): exit 1 — fails e1 (deriv at storeHandleOld). Second ordering trap: caught.
- atk_8 (boundary: assign none literally): exit 1 — fails e1 + e2.
- atk_9 (ECHO-WITH-CORRECT-ASSIGN: storeHandle := some targetDb; return naturalKeyVia (some targetDb)): exit 0 — VERIFIES (both clauses hold). REQUIRED resolve run performed: its faithful patch is the gold-equivalent concrete realization (after obj._state.db = db, naturalKeyVia (some targetDb) denotes obj.natural_key() evaluated at the set handle = the gold three-line change). run_resolve(django__django-15525, atk_9.patch, timeout=1800) => resolved=True, completed=True. Verifying wrong-impl's faithful patch RESOLVES => does NOT break the spec (verify=>correct holds here).

REFINEMENT AUDIT (refinement.md §A, all legs R/A/I, no kind-3): A1=R (targetDb:String<->db:str); A2=R (require storeHandle=none <-> fresh Model(**data) _state.db=None, base.py:454); A3=I (storeHandle:=some targetDb <-> obj._state.db=db, the CHANGED op modeled DEEPLY as concrete assignment); A4=A-reference (opaque naturalKeyVia <-> unchanged obj.natural_key(), NO asserted ensures — op controls its argument = post-assignment handle); A5=I (return key <-> natural_key used downstream). The lone A-leg (A4) asserts no contract so cannot over-claim (correctly G-AX skip); its correspondence to the real callee holds (mapping.md §2: obj.natural_key() value is a function of obj._state.db via router hints, related_descriptors.py:121,164-168). No kind-3 (inexpressible-changed-op) leg. G-CONF conf_skip=true is justified (deep ORM state mutation, no DB-free R/I shadow) — R/I legs mechanically covered by G-CONF policy; the A-leg audit here confirms the opaque A-reference is grounded (argument controlled by the op; atk_4/atk_9 show the echo is defeated by e2 unless the real assignment is performed).

CONCLUSION: 9 attacks run (>=5 met), every verifying wrong impl (only atk_9) had its faithful patch materialized and resolve-RUN => resolved=True. No verifying impl whose faithful patch fails to resolve. Spec is TIGHT (two clauses jointly pin behavior; ordering caught) and SOUND. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- The natural-key derivation for a record, as it depends on the record's
   STORE HANDLE — the identifier of the database the record is currently
   associated with. The derivation may follow references to related records,
   and each such reference is resolved against the database named by the store
   handle; so the resulting key is a function of that handle. This is an
   UNCHANGED routine the operation defers to: it is left OPAQUE (a free
   function), refined never replaced, so no contract is claimed about WHAT it
   returns — only that the operation feeds it the right handle. Because nothing
   is asserted about its value there is nothing to validate against the real
   routine (no axiom_check.py — meta.json G-AX skip). Provenance: mapping.md. -/
opaque naturalKeyVia : Option String → List String
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Deriving the natural key of a freshly built record while loading it into a
   target database.

   A record's natural key may follow references to related records, and those
   references are resolved against whichever database the record is currently
   associated with (its STORE HANDLE). A freshly built record carries no store
   handle yet (`none`). When the record is being loaded into a particular
   target database, the natural key must be derived as that target database
   would see it, so that reference-following resolves against the same database
   the record is being loaded into.

   The desired behavior: associate the record with the target database FIRST —
   set its store handle to that database — and only THEN derive the natural key,
   so the reference-following derivation is routed to the target database.

   `storeHandle` is the record's mutable database association. It comes in
   unset (`none`) for a freshly built record and is genuinely mutated to the
   target database; its post-state is pinned EXACTLY to `some targetDb`
   (directive 5: the changed frame is stated at its exact post-state). The
   returned key is the derivation evaluated at that updated handle, so it is
   grounded in the input `targetDb` (the key is `naturalKeyVia (some targetDb)`,
   the derivation at the target-database handle). -/
method naturalKeyForLoadedRecord (targetDb : String) (mut storeHandle : Option String)
    return (key : List String)
  require storeHandle = none
  ensures storeHandle = some targetDb
  ensures key = naturalKeyVia (some targetDb)
  do
    -- impl-start
    -- Associate the freshly built record with the target database, THEN derive
    -- the natural key from that updated handle (the derivation reads the handle
    -- and routes reference-following to the named database).
    storeHandle := some targetDb
    let key := naturalKeyVia storeHandle
    return key
    -- impl-end

prove_correct naturalKeyForLoadedRecord by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec is byte-identical frozen (same_spec=True for all 9 attacks + pos_control + prepatch). Method naturalKeyForLoadedRecord pins TWO ensures: (e1) key = naturalKeyVia (some targetDb); (e2) storeHandle = some targetDb; precondition require storeHandle = none. naturalKeyVia is an opaque A-reference (unchanged obj.natural_key(), NO asserted contract). Soundness crux = derive-AFTER-associate ordering, since e1 pins the derivation at the POST-assignment handle.

TOOLING: project root = (NOT the /home path in the prompt, which lacks scripts/). Verified via `bash scripts/lean_verify.sh <file>`; same_spec via swebench_unified.markers.same_spec + get_backend('velvet'); resolve via swebench_unified.harness.run_resolve. Attack verifications run concurrently in batches of <=4 background jobs.

BASELINE: pos_control.lean (=gold impl) exit 0 (VERIFIES). prepatch.lean exit 1 — fails on exactly ensures_1 (naturalKeyVia storeHandleOld = naturalKeyVia (some targetDb)) AND ensures_2 (storeHandleOld = some targetDb), matching refinement.md B verbatim (prepatch reproduced, fails for the RIGHT reason).

### ATTACKS (all same_spec=True; edited ONLY impl region):
- atk_1 (prepatch bug: derive at unset handle, never assign): exit 1 — fails e1 + e2.
- atk_2 (control-flow-effect: derive-BEFORE-assign order swap): exit 1 — fails e1 (deriv at storeHandleOld=none). The ordering trap: caught.
- atk_3 (assign handle, derive at literal none): exit 1 — fails e1 (naturalKeyVia none).
- atk_4 (ungrounded-oracle ECHO, no assign): exit 1 — e1 satisfied by echo but e2 (storeHandleOld=some targetDb) rejects; the companion state clause defeats a pure echo.
- atk_5 (assign WRONG handle some "default", derive): exit 1 — fails e1 + e2.
- atk_6 (partial/stub: assign handle, return []): exit 1 — fails e1 ([] = naturalKeyVia (some targetDb)).
- atk_7 (stale-read: snapshot handle before assign, derive from stale; e2 holds): exit 1 — fails e1 (deriv at storeHandleOld). Second ordering trap: caught.
- atk_8 (boundary: assign none literally): exit 1 — fails e1 + e2.
- atk_9 (ECHO-WITH-CORRECT-ASSIGN: storeHandle := some targetDb; return naturalKeyVia (some targetDb)): exit 0 — VERIFIES (both clauses hold). REQUIRED resolve run performed: its faithful patch is the gold-equivalent concrete realization (after obj._state.db = db, naturalKeyVia (some targetDb) denotes obj.natural_key() evaluated at the set handle = the gold three-line change). run_resolve(django__django-15525, atk_9.patch, timeout=1800) => resolved=True, completed=True. Verifying wrong-impl's faithful patch RESOLVES => does NOT break the spec (verify=>correct holds here).

REFINEMENT AUDIT (refinement.md §A, all legs R/A/I, no kind-3): A1=R (targetDb:String<->db:str); A2=R (require storeHandle=none <-> fresh Model(**data) _state.db=None, base.py:454); A3=I (storeHandle:=some targetDb <-> obj._state.db=db, the CHANGED op modeled DEEPLY as concrete assignment); A4=A-reference (opaque naturalKeyVia <-> unchanged obj.natural_key(), NO asserted ensures — op controls its argument = post-assignment handle); A5=I (return key <-> natural_key used downstream). The lone A-leg (A4) asserts no contract so cannot over-claim (correctly G-AX skip); its correspondence to the real callee holds (mapping.md §2: obj.natural_key() value is a function of obj._state.db via router hints, related_descriptors.py:121,164-168). No kind-3 (inexpressible-changed-op) leg. G-CONF conf_skip=true is justified (deep ORM state mutation, no DB-free R/I shadow) — R/I legs mechanically covered by G-CONF policy; the A-leg audit here confirms the opaque A-reference is grounded (argument controlled by the op; atk_4/atk_9 show the echo is defeated by e2 unless the real assignment is performed).

CONCLUSION: 9 attacks run (>=5 met), every verifying wrong impl (only atk_9) had its faithful patch materialized and resolve-RUN => resolved=True. No verifying impl whose faithful patch fails to resolve. Spec is TIGHT (two clauses jointly pin behavior; ordering caught) and SOUND. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-15525/velvet. VERDICT: FAITHFUL — the modeled function does NOT over-claim relative to the real callee; no diverging input exists.

(1) Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, velvet.language) = True. The frozen spec is exactly: opaque naturalKeyVia : Option String -> List String; method naturalKeyForLoadedRecord (targetDb : String) (mut storeHandle : Option String) return (key : List String); require storeHandle = none; ensures storeHandle = some targetDb; ensures key = naturalKeyVia (some targetDb). Only impl/proof regions differ.

(2) Lean checked: Solution.lean elaborates clean (exit 0); Solution_prepatch.lean fails on exactly the two discriminating goals — 'naturalKeyVia storeHandleOld = naturalKeyVia (some targetDb)' and 'storeHandleOld = some targetDb' — confirming G-DIFF is genuine and the two ensures clauses are the load-bearing spec.

(3) Real callee (gold hunk of build_instance in django/core/serializers/base.py):
  obj = Model(**data)      # fresh instance: obj._state.db = None (ModelState.db class default = None, verified base.py:395)
  obj._state.db = db       # the fix's added line
  natural_key = obj.natural_key()
The precondition require storeHandle = none faithfully models the fresh record (Model(**data) always gives _state.db=None; caller build_instance is entered only for pk-less natural-key models). ensures storeHandle = some targetDb matches the direct scalar assignment obj._state.db = db exactly (db is a str alias, none/some bijection per mapping.md §2). 

(4) Faithfulness of the key clause: naturalKeyVia is declared OPAQUE with NO value contract — it literally IS the real obj.natural_key() abstracted as a function of the store handle (natural_key() follows self.author -> ForwardManyToOneDescriptor -> db_manager(hints={instance: obj}) routed by obj._state.db). ensures key = naturalKeyVia (some targetDb) therefore asserts only that the returned key equals the REAL derivation evaluated at the post-assignment handle — which is precisely what the gold code computes (derive AFTER assigning). Because no proposition is asserted about naturalKeyVia's return value, the spec cannot be 'too strong': there is no value, ordering, or edge input on which the model claims something the real routine violates. The ordering crux (associate-then-derive) is captured structurally by binding key to the updated handle, not the pre-state.

No too-strong clause and no drift found. Attempted counterexample directions considered and rejected: (a) a fresh instance with _state.db already non-None — impossible, ModelState.db defaults None; (b) targetDb absent/None — build_instance's db arg is a real alias (DEFAULT_DB_ALIAS at minimum), and String carrier admits any alias, matching identity bijection; (c) value mismatch of natural_key — untestable/irrelevant since naturalKeyVia is opaque and left as the real callee. No admitted input diverges.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified (velvet, django__django-15525).

MECHANICAL: same_spec(Solution.lean, Solution_prepatch.lean)=True via swebench_unified.markers.same_spec(velvet backend) — spec region is byte-identical, so the frozen spec view is the audited artifact. leakage.screen() PASSES with zero hard_failures: no diff markers, no gold-patch line reproduced (>=8-char normalized), no patched file path (django/core/serializers/base.py) or dotted module path in view, no spec-view identifier embedding a patched repo symbol, no narration words. Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md) — strict judgment.

SPEC-VIEW HYGIENE: the projected spec view (impl+proof elided) uses only abstract de-narrated vocabulary — 'store handle', 'record', 'target database', 'reference-following'. Confirmed ABSENT: _state.db, build_instance, natural_key, Model, db_manager, from_db, ModelState, get_by_natural_key, serializers/base.py. The concrete gold mechanism (obj._state.db = db, Model.from_db) lives only in hints_text, correctly excluded per the 'beyond problem_statement, NOT hints_text' standard.

GOLD-RECONSTRUCTION vs PUBLIC problem_statement: the spec does encode the behavioral intent 'associate the record with the target DB FIRST, THEN derive the natural key so reference-following routes to the target DB.' This does NOT exceed the public problem_statement, which already pins the exact culprit line `natural_key = Model(**data).natural_key()` at base.py:332 (traceback), names build_instance, shows the FK-following natural_key ((self.title,)+self.author.natural_key()), and states the root cause explicitly: a freshly-built DB-unassociated instance whose FK lookup routes to the DEFAULT db, giving 'Author matching query does not exist' on --database other. The abstract associate-then-derive fix is the direct corollary of that publicly-stated diagnosis, not a hidden discriminator. No quotable spec-view line leaks the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
