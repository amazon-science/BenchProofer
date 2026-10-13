# P2 adversarial audit — django__django-11490

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,18 +176,13 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
-    let mut working := persistent
+    -- ATTACK: pre-patch shape. Record onto the SHARED carrier itself.
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
-      return working
+      persistent := recordOnto persistent projected
+      return persistent
     else
-      return working
+      return persistent
     -- impl-end
 
 prove_correct applyProjection by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,18 +176,18 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
-    let mut working := persistent
+    -- ATTACK: record onto the shared carrier, then restore ONLY its explicit
+    -- column list. The two records of selected non-column outputs stay as the
+    -- recording left them.
+    let old := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
-      return working
+      persistent := recordOnto persistent projected
+      let w := persistent
+      persistent := { persistent with columns := old.columns }
+      return w
     else
-      return working
+      return persistent
     -- impl-end
 
 prove_correct applyProjection by
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -176,18 +176,19 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
-    let mut working := persistent
+    -- ATTACK: never take a private copy. Record the projection onto the SHARED
+    -- carrier, read the working carrier off it, then put the shared carrier's
+    -- whole selection back as it was. Every observation the model carries is
+    -- restored, so the frame holds in the MODEL.
+    let old := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
-      return working
+      persistent := recordOnto persistent projected
+      let w := persistent
+      persistent := old
+      return w
     else
-      return working
+      return persistent
     -- impl-end
 
 prove_correct applyProjection by
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -176,16 +176,16 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: partial domain. Record only where the carrier can answer the
+    -- projection; otherwise hand the carrier back untouched.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
-      return working
+      if answerable persistent projected then
+        working := recordOnto persistent projected
+        return working
+      else
+        return working
     else
       return working
     -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -176,16 +176,18 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: partial domain hiding the pre-patch mutation. Where the carrier
+    -- can answer the projection, behave like gold; where it cannot, record onto
+    -- the SHARED carrier and hand that back.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
-      return working
+      if answerable persistent projected then
+        working := recordOnto persistent projected
+        return working
+      else
+        persistent := recordOnto persistent projected
+        return persistent
     else
       return working
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,16 +176,16 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: boundary. Treat an EMPTY projection as nothing to record instead
+    -- of resetting the explicit column list to the carrier's own fields.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
-      return working
+      if projected.isEmpty then
+        return working
+      else
+        working := recordOnto persistent projected
+        return working
     else
       return working
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,15 +176,20 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: swap the precedence. Consult the auxiliary-output record FIRST,
+    -- so a name carried in both records is kept as an auxiliary output.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
+      if projected.isEmpty then
+        working := { persistent with columns := persistent.ownFields }
+      else
+        working := { persistent with
+          columns := projected.filter
+            (fun n => !persistent.sideSelected.contains n && !persistent.auxSelected.contains n),
+          sideSelected := persistent.sideSelected.filter
+            (fun n => projected.contains n && !persistent.auxSelected.contains n),
+          auxSelected := persistent.auxSelected.filter (fun n => projected.contains n) }
       return working
     else
       return working
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,14 +176,11 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: control-flow effect. Note that a recording happened whether or
+    -- not the push-down applies.
     let mut working := persistent
+    recorded := true
     if shouldProject persistent requested then
-      recorded := true
       working := recordOnto persistent projected
       return working
     else
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,15 +176,20 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: sort the projection against what the carrier's MODEL could supply
+    -- (auxAvailable) rather than what its selection currently carries.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
+      if projected.isEmpty then
+        working := { persistent with columns := persistent.ownFields }
+      else
+        working := { persistent with
+          columns := projected.filter
+            (fun n => !persistent.sideSelected.contains n && !persistent.auxAvailable.contains n),
+          sideSelected := persistent.sideSelected.filter (fun n => projected.contains n),
+          auxSelected := persistent.auxSelected.filter
+            (fun n => projected.contains n && !persistent.sideSelected.contains n) }
       return working
     else
       return working
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,13 +176,10 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: key the push-down guard on the pushed-down projection instead of
+    -- the outer request's OWN explicit column list.
     let mut working := persistent
-    if shouldProject persistent requested then
+    if persistent.columns.isEmpty && !projected.isEmpty then
       recorded := true
       working := recordOnto persistent projected
       return working
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,12 +176,11 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: divergence probe. Spin forever before answering.
     let mut working := persistent
+    let mut i := 0
+    while true do
+      i := i + 1
     if shouldProject persistent requested then
       recorded := true
       working := recordOnto persistent projected
```

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,16 +176,18 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: on the EMPTY-projection leg, record onto the SHARED carrier.
+    -- `answerable c []` is vacuously true, so this is inside the admitted
+    -- domain and must be rejected.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
-      return working
+      if projected.isEmpty then
+        persistent := recordOnto persistent projected
+        return persistent
+      else
+        working := recordOnto persistent projected
+        return working
     else
       return working
     -- impl-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -176,16 +176,18 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: control-flow effect confined to the require-excluded subdomain:
+    -- where the push-down applies but the carrier cannot answer the projection,
+    -- do not note the recording at all.
     let mut working := persistent
     if shouldProject persistent requested then
-      recorded := true
-      working := recordOnto persistent projected
-      return working
+      if answerable persistent projected then
+        recorded := true
+        working := recordOnto persistent projected
+        return working
+      else
+        working := recordOnto persistent projected
+        return working
     else
       return working
     -- impl-end
```

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,15 +176,19 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: leave the side-output record WHOLE instead of filtering it down
+    -- to the projected names, while still filtering the auxiliary record.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
+      if projected.isEmpty then
+        working := { persistent with columns := persistent.ownFields }
+      else
+        working := { persistent with
+          columns := projected.filter
+            (fun n => !persistent.sideSelected.contains n && !persistent.auxSelected.contains n),
+          auxSelected := persistent.auxSelected.filter
+            (fun n => projected.contains n && !persistent.sideSelected.contains n) }
       return working
     else
       return working
```

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,15 +176,15 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: on the EMPTY-projection leg, also clear BOTH records of selected
+    -- non-column outputs instead of leaving them as they stand.
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
+      if projected.isEmpty then
+        working := { persistent with columns := persistent.ownFields, sideSelected := [], auxSelected := [] }
+      else
+        working := recordOnto persistent projected
       return working
     else
       return working
```

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

```diff
@@ -176,15 +176,12 @@
   ensures working = workingCarrier persistentOld requested projected
   do
     -- impl-start
-    -- Take a private working carrier from the shared one, then (only where the
-    -- push-down applies) record the projection onto THAT carrier, noting that a
-    -- recording happened. The shared carrier is never written and never recorded
-    -- onto, so it is returned exactly as received; where the push-down does not
-    -- apply nothing is recorded anywhere.
+    -- ATTACK: ungrounded oracle echo -- hand back the spec function applied to
+    -- the WRONG carrier observation (requested in place of projected).
     let mut working := persistent
     if shouldProject persistent requested then
       recorded := true
-      working := recordOnto persistent projected
+      working := recordOnto persistent requested
       return working
     else
       return working
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. A constituent carrier is modeled directly as the
--  bundle of observations this step reads and writes, and recording a projection
--  onto a carrier is modeled directly as the transformation it works on that
--  bundle. No unchanged callee's contract is consumed and no foreign callee is
--  deep-modeled, so there is nothing to axiomatize.)
-- axioms-end

-- pure-start
/- One constituent carrier of a compound request, as this step observes it.

   A carrier's SELECTION is what it will emit, and it has THREE parts that move
   together, because a carrier draws the things it can emit from three separate
   places and keeps a separate record of what it has selected from each:
   `columns`, the explicit list of its own model's columns it names;
   `sideSelected`, the side outputs -- outputs supplied by literal text carried
   alongside the model rather than computed from it -- that are currently part of
   that selection; and `auxSelected`, the auxiliary outputs computed for this
   carrier that are currently part of it.

   The remaining two observations describe the carrier's MODEL rather than its
   selection, and reconciling a projection never alters either of them:
   `auxAvailable` names every non-column output the carrier is ABLE to supply,
   whether or not its selection currently carries it, and `ownFields` names the
   columns the carrier's own model defines. Recording consults neither -- it reads
   the selection, not the model -- but both are pinned across the step, so a
   carrier's ability to answer a name cannot be quietly destroyed. -/
structure Carrier where
  columns : List String
  sideSelected : List String
  auxSelected : List String
  auxAvailable : List String
  ownFields : List String
deriving DecidableEq

/- Whether the outer request's projection must be pushed down onto a carrier:
   true exactly when the carrier does not yet name any explicit columns AND the
   outer request names explicit columns OF ITS OWN. A carrier that already names
   an explicit column list keeps it; an outer request that names no explicit
   columns of its own asks for no push-down, even when the compound projection it
   would contribute is itself non-empty. -/
def shouldProject (c : Carrier) (requested : List String) : Bool :=
  c.columns.isEmpty && !requested.isEmpty

/- Recording a pushed-down projection onto a carrier. This is ONE act that
   reshapes the carrier's whole selection, not an edit of its explicit column
   list alone, and what it reads to reshape it is the selection the carrier
   ALREADY carries rather than everything its model could be asked for.

   A NON-EMPTY projection is sorted into the three parts by consulting the
   carrier's two records of selected non-column outputs IN ORDER, side outputs
   FIRST and auxiliary outputs only afterwards. A projected name found among the
   carrier's selected side outputs is kept as a side output; a projected name not
   found there but found among its selected auxiliary outputs is kept as an
   auxiliary output; every OTHER projected name becomes part of its explicit
   column list. The precedence is observable, not a formality: a name the carrier
   happens to carry in BOTH records is kept only as a side output, and is dropped
   from its selected auxiliary outputs.

   Each of the two kept records is filtered down to the projected names, so it
   lists them in the CARRIER's own order and once each however the projection
   happens to list them, while the explicit column list is built from the
   projection and so keeps the PROJECTION's order and repetitions. A name the
   carrier's model could supply as a non-column output but which neither record
   currently carries is no part of the selection being read, so a projected name
   matching it lands in the explicit column list with the rest.

   An EMPTY projection is the other leg: it names nothing to keep, so BOTH
   records of selected non-column outputs are left exactly as they stand while
   the explicit column list becomes every column the carrier's own model defines.

   All three parts of the selection are overwritten together, so a carrier that
   has been recorded onto is not put back as it was by restoring only some of
   them. The carrier's model is untouched by either leg. -/
def recordOnto (c : Carrier) (projected : List String) : Carrier :=
  if projected.isEmpty then
    { c with columns := c.ownFields }
  else
    { c with
        columns := projected.filter
          (fun n => !c.sideSelected.contains n && !c.auxSelected.contains n),
        sideSelected := c.sideSelected.filter (fun n => projected.contains n),
        auxSelected := c.auxSelected.filter
          (fun n => projected.contains n && !c.sideSelected.contains n) }

/- The carrier this step must hand back: the carrier with the projection
   recorded onto it where the push-down applies, and otherwise the carrier
   exactly as it stands. -/
def workingCarrier (c : Carrier) (requested projected : List String) : Carrier :=
  if shouldProject c requested then recordOnto c projected else c

/- Whether a carrier can answer every name in a column list: each name is a
   column its own model defines, or one of the side outputs its selection already
   carries, or one of the auxiliary outputs its selection already carries. Both
   records of selected non-column outputs count here, and they count on equal
   terms -- the precedence between them decides only WHERE an answerable name is
   kept, never WHETHER it can be answered. A non-column output the carrier is able
   to supply but which neither record currently carries does NOT make a name
   answerable -- recording reads the selection, not the model, so `auxAvailable`
   is deliberately absent from this test -- and such a name is answerable only if
   the carrier's own model defines a column of that name. A carrier can only
   absorb a projection whose every name it can answer. -/
def answerable (c : Carrier) (names : List String) : Bool :=
  names.all (fun n =>
    c.ownFields.contains n || c.sideSelected.contains n || c.auxSelected.contains n)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- One step of assembling a compound result from several constituent carriers:
   reconcile a single shared constituent carrier with the projection the outer
   request wants every constituent to carry, and hand back the carrier this step
   will actually read columns from.

   The shared carrier is shared across repeated assemblies of the same compound
   request, so its whole selection must be treated as read-only state: this step
   reads it to decide what to project, but the carrier it hands back must be one
   whose selection it is free to reshape WITHOUT the shared carrier's own
   selection moving. Leaving the shared carrier's selection as it was on entry is
   precisely what leaves a later assembly of the same compound request free to
   project a different column list.

   `persistent` is the shared carrier (declared `mut` because the long-standing
   shape of this code reaches for it as the thing to reconcile). It MUST be
   returned unchanged, and `ensures persistent = persistentOld` pins EVERY
   observation of it — all three parts of its selection and both parts of its
   model description, not its explicit column list alone. Recording a projection
   onto a carrier overwrites all three selection parts at once, so a carrier that
   has absorbed a projection is not put back as it was by writing its explicit
   column list back afterwards, nor by restoring only one of its two records of
   selected non-column outputs.

   The two request observations are read-only and never altered: `requested` is
   the outer request's own explicit column list, which is what decides whether a
   push-down happens at all, and `projected` is the full column list the request
   pushes down.

   `recorded` says whether this step has recorded a pushed-down projection onto
   ANY constituent carrier; it is `mut` because the long-standing shape of this
   code performs that recording by reaching for the shared carrier itself.
   Together `ensures shouldProject persistentOld requested = false → recorded =
   recordedOld` and `ensures shouldProject persistentOld requested = true →
   recorded = true` say the recording happens EXACTLY on the push-down. Where the
   push-down does not apply, NO carrier is recorded onto. Where it does apply, the
   projection really is recorded onto the carrier this step hands back, rather
   than that carrier's selection merely being asserted of the result. How MANY
   times it is recorded is deliberately left free: that is not part of the
   observable behaviour.

   Each recorded name must resolve against the carrier as its selection stands,
   so this step is asked only about a push-down the carrier can answer — that is
   what the `require` states. A carrier that cannot answer a projected name — its
   own model defines no column of that name and NEITHER record of its selected
   non-column outputs carries that name — cannot absorb the projection at all, and
   this step makes no claim about that case. -/
method applyProjection (mut persistent : Carrier) (mut recorded : Bool)
    (requested : List String) (projected : List String)
    return (working : Carrier)
  require shouldProject persistent requested = true →
    answerable persistent projected = true
  ensures persistent = persistentOld
  ensures shouldProject persistentOld requested = false → recorded = recordedOld
  ensures shouldProject persistentOld requested = true → recorded = true
  ensures working = workingCarrier persistentOld requested projected
  do
    -- impl-start
    -- Take a private working carrier from the shared one, then (only where the
    -- push-down applies) record the projection onto THAT carrier, noting that a
    -- recording happened. The shared carrier is never written and never recorded
    -- onto, so it is returned exactly as received; where the push-down does not
    -- apply nothing is recorded anywhere.
    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected
      return working
    else
      return working
    -- impl-end

prove_correct applyProjection by
  loom_solve
  all_goals simp_all [workingCarrier, shouldProject, recordOnto]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND (advisory). 16 same-spec attacks built in , all same_spec=True; 4 verify; every one of those 4 had its faithful refined patch materialized and RUN through run_resolve, and all 4 RESOLVED alongside a resolving gold control. The BROKEN criterion (a verifying wrong impl whose faithful patch does not resolve) was NOT met.

**NOTE ON SCOPE:** the prior G-EQ record in meta.json was taken against Solution.lean sha 8a4a0bf9..., but the shipped Solution.lean is a01997f5... (4-field Carrier -> 5-field, `sideSelected` + the side/aux PRECEDENCE added). So this is a fresh attack campaign against the current frozen spec, not a re-run.

### COMMANDS (from repo root swe-proof):
  verify:  bash scripts/lean_verify.sh atk_N.lean
  resolve: python resolve_one.py <name> <patch.diff>   (calls harness.run_resolve)
Verifications were run 4-at-a-time as concurrent background jobs; each attack was still individually verified to a definite exit code.

### ATTACK LEDGER (exit 0 = verifies, 1 = rejected):
REJECTED (12), each on a genuine SEMANTIC unsolved goal on a NAMED clause (logs atk_N.log):
- atk_1  PREPATCH BUG: record onto the SHARED carrier and hand it back -> exit 1, «ensures_4: persistent = persistentOld». Impl region confirmed IDENTICAL (modulo comments) to the bundle's Solution_prepatch.lean by programmatic token compare. prepatch_reproduced=True.
- atk_2  half-restore (write back only `columns`)          -> ensures_4.
- atk_6  boundary: empty projection treated as nothing-to-record -> ensures_1 (residual shows require_1: answerable persistentOld [] = true).
- atk_7  PRECEDENCE SWAP: consult auxSelected BEFORE sideSelected -> ensures_1. This is the leg the spec revision added, and it is genuinely load-bearing.
- atk_8  control-flow effect: `recorded := true` unconditionally -> ensures_3 (the no-push-down direction).
- atk_9  ungrounded-oracle echo widened by the carrier's MODEL (sorts on auxAvailable instead of the selection) -> ensures_1. Confirms `auxAvailable` is correctly absent from the reshape.
- atk_10 guard keyed on the WRONG binder (`projected` not `requested`) -> ensures_1 + ensures_2 + ensures_3.
- atk_11 DIVERGENCE probe (never-exiting `while true`) -> rejected by total correctness: "Decreasing annotations are required in total correctness semantics". Rejected by the termination lane, not a postcondition.
- atk_12 prepatch mutation confined to the EMPTY-projection leg (inside the admitted domain, since `answerable c [] ` is vacuously true) -> ensures_4. Good: the require does NOT shelter this.
- atk_14 leave sideSelected WHOLE instead of filtering it to the projected names -> ensures_1.
- atk_15 empty-projection leg over-erases (clears BOTH records too) -> ensures_1.
- atk_16 record `requested` instead of `projected` -> ensures_1.

VERIFIED (4) -- all 4 patches materialized and EXECUTED through run_resolve:
- atk_3  NO CLONE: record onto the SHARED carrier, take the working carrier off it, then restore the shared carrier's whole MODELED selection (values_select + extra_select_mask + annotation_select_mask). patch_atk_3.diff  -> resolved=True, completed=True.
- atk_4  partial domain: record only where `answerable`, else hand the carrier back untouched. patch_atk_4.diff -> resolved=True, completed=True.
- atk_5  partial domain HIDING THE PREPATCH BUG on the require-excluded subdomain. patch_atk_5.diff -> resolved=True, completed=True.
- atk_13 control-flow effect (the `recorded` ledger) confined to the require-excluded subdomain; materialized as "no clone taken where the recording is not accounted for". patch_atk_13.diff -> resolved=True, completed=True.
Gold control: patch.diff verbatim -> resolved=True, completed=True.

### FALSE-POSITIVE HYGIENE (two traps avoided, both of which would have produced a bogus verdict):
1. atk_15 first FAILED on a Lean PARSE error (multi-line record-update literal: "unexpected identifier; expected '}'", plus a bogus "no obligation found"). That is MY syntax bug, not a spec rejection. I collapsed the record update to one line, re-checked same_spec=True, and re-ran: it then failed on a genuine ensures_1 residual. Banking the parse error as a rejection would have inflated the reject lane with a non-result.
2. The known `all` SHADOWING trap is real here: the enclosing method is get_combinator_sql(self, combinator, all), so the builtin `all()` is shadowed by a bool parameter. All three partial-domain patches (atk_4/5/13) need the answerable test, and I wrote it as an EXPLICIT LOOP for exactly this reason. I also pre-flighted every patch locally before spending harness slots: each of atk_3/4/5/13 applied cleanly at base_commit and gave "Ran 26 tests ... OK (skipped=2)" on queries.test_qs_combinators with the F2P test_patch applied. A TypeError-crashing patch would have reported did-not-resolve and invented a spec break.

WHY THE PARTIAL-DOMAIN ATTACKS DO NOT BREAK THE GATE (measured, not argued). The spec carries `require shouldProject persistent requested = true -> answerable persistent projected = true`, leaving the not-answerable subdomain completely unconstrained -- atk_5 hides the literal prepatch mutation there and atk_13 hides a control-flow effect there. I instrumented the REAL push-down site in django/db/models/sql/compiler.py (logging answerable per firing) and ran both the graded module and the whole `queries` app. Every firing is answerable=True: projections ('name','order','id') x3, ('num',) x2, ('num','count'), ('id','num'), ('count','num'); zero answerable=False firings. The excluded subdomain is never reached by the graded tests, so these impls resolve. Latent, not gate-breaking.

STRONGEST FINDING -- atk_3, a MEASURED real divergence that the frame cannot see (flagged for the panel lanes, NOT a G-EQ break since its patch resolves). `ensures persistent = persistentOld` pins only the five MODELED observations. atk_3 restores all three selection records, so the frame holds in the model -- but the real Query.set_values() also writes `select` and `default_cols`, which the Carrier does not carry. Probe (tests/queries/test_sbu_probe.py, run under both gold and atk_3):
    gold  : all 7 observations clean after the push-down.
    atk_3 : the 3 MODELED ones clean, but DIRTY [UNMODELED] default_cols: True -> False, and DIRTY [UNMODELED] select: () -> (Col(name), Col(order), Col(id)).
That dirt is observable. Probe 2 (test_sbu_probe2.py) evaluates the same compound queryset as values_list, then PLAIN, then values_list again:
    gold  : VALUES ('a',2,1) / PLAIN [<ReservedName: a>] / VALUES2 (2,)
    atk_3 : VALUES ('a',2,1) / PLAIN raised TypeError: `__str__` returned non-string (type int) / VALUES2 (2,)
So atk_3 corrupts a later plain evaluation of the shared sub-query where gold does not, yet it satisfies the frozen frame and resolves (the graded suite never mixes a plain evaluation after a values push-down). This is the same class of weakness the previous revision's atk_11a exhibited: widening Carrier from 4 to 5 fields did not close it, because the missing observations are `select`/`default_cols`, neither of which was added. Closing it would need those in the Carrier (or an explicit ensures that no unmodeled sub-query state is written).

REFINEMENT.MD AUDIT (A-legs; R/I are G-CONF's). No kind-3 leg: every row A1-A8 is tagged R, I, or a documented frame/domain leg, and there are NO axioms and NO deep_model_references (meta.json: axioms=[], deep_model_references=[], G-AX status=skip). That is correct for this bundle -- the modeled operation IS the changed code, and the two callees it touches are transliterated rather than assumed: Query.clone() -> Lean value-copy (A3, sound: Lean values have no aliasing, and the only property relied on, non-mutation of the original, is the pinned frame not an assumption), and Query.set_values() -> recordOnto.

I checked recordOnto against the real set_values body at query.py:2030-2062 step by step and the correspondence HOLDS: the falsy-`fields` leg -> `{c with columns := c.ownFields}` with both masks untouched (real code assigns field_names from concrete_fields and skips both `set_*_mask` calls -- correct); the `if f in self.extra_select / elif f in self.annotation_select / else` three-way sort -> the three filters, with the `elif` faithfully rendered as the `!c.sideSelected.contains n` conjunct in the auxSelected filter (this is the precedence atk_7 confirms is load-bearing); and the two mask writes landing together with values_select -> one atomic record update (which is what defeats atk_2's half-restore).

A7's domain leg is honestly stated and I independently confirmed its direction of failure is exclusion, not misprediction. Documentation is materially better than the prior revision's: mapping.md §2 now names all five Carrier fields with per-field bijections and both masks are separated, so the earlier complaint that the map described a superseded spec is RESOLVED.

Two residual gaps worth recording: (a) A8's `recorded` ledger still has no crisp repo observable -- "whether set_values was called on ANY carrier" is not a value the repo exposes, which is precisely the freedom atk_13 exploits; (b) mapping.md §2's closing paragraph explicitly waives `select`/`default_cols`/`deferred_loading` as "outside the abstraction" per SPEC_GUIDE §2, and that waiver is exactly what atk_3 walks through -- the doc is honest about the omission but understates it, since the omitted state is reachable and its corruption is user-visible (TypeError above), not merely unmodeled.

**EVIDENCE:** 16 attack .lean + .log files, patch_atk_{3,4,5,13}.diff, patch_gold.diff, resolve_{gold,atk_3,atk_4,atk_5,atk_13}.json (each resolved=True completed=True), local_atk_{3,4,5}.txt, answerable.log, pos_control.log (EXIT=0), probe scripts, and a worktree at base_commit under dj/ -- all in  Positive control = byte-identical copy of the shipped Solution.lean, same_spec=True, verifies exit 0.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 16 admissible attacks re-run of 16 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 16 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1.lean`, `atk_2.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean`, `atk_14.lean`, `atk_15.lean`, `atk_16.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_13.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (16):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 16 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. A constituent carrier is modeled directly as the
--  bundle of observations this step reads and writes, and recording a projection
--  onto a carrier is modeled directly as the transformation it works on that
--  bundle. No unchanged callee's contract is consumed and no foreign callee is
--  deep-modeled, so there is nothing to axiomatize.)
-- axioms-end

-- pure-start
/- One constituent carrier of a compound request, as this step observes it.

   A carrier's SELECTION is what it will emit, and it has THREE parts that move
   together, because a carrier draws the things it can emit from three separate
   places and keeps a separate record of what it has selected from each:
   `columns`, the explicit list of its own model's columns it names;
   `sideSelected`, the side outputs -- outputs supplied by literal text carried
   alongside the model rather than computed from it -- that are currently part of
   that selection; and `auxSelected`, the auxiliary outputs computed for this
   carrier that are currently part of it.

   The remaining two observations describe the carrier's MODEL rather than its
   selection, and reconciling a projection never alters either of them:
   `auxAvailable` names every non-column output the carrier is ABLE to supply,
   whether or not its selection currently carries it, and `ownFields` names the
   columns the carrier's own model defines. Recording consults neither -- it reads
   the selection, not the model -- but both are pinned across the step, so a
   carrier's ability to answer a name cannot be quietly destroyed. -/
structure Carrier where
  columns : List String
  sideSelected : List String
  auxSelected : List String
  auxAvailable : List String
  ownFields : List String
deriving DecidableEq

/- Whether the outer request's projection must be pushed down onto a carrier:
   true exactly when the carrier does not yet name any explicit columns AND the
   outer request names explicit columns OF ITS OWN. A carrier that already names
   an explicit column list keeps it; an outer request that names no explicit
   columns of its own asks for no push-down, even when the compound projection it
   would contribute is itself non-empty. -/
def shouldProject (c : Carrier) (requested : List String) : Bool :=
  c.columns.isEmpty && !requested.isEmpty

/- Recording a pushed-down projection onto a carrier. This is ONE act that
   reshapes the carrier's whole selection, not an edit of its explicit column
   list alone, and what it reads to reshape it is the selection the carrier
   ALREADY carries rather than everything its model could be asked for.

   A NON-EMPTY projection is sorted into the three parts by consulting the
   carrier's two records of selected non-column outputs IN ORDER, side outputs
   FIRST and auxiliary outputs only afterwards. A projected name found among the
   carrier's selected side outputs is kept as a side output; a projected name not
   found there but found among its selected auxiliary outputs is kept as an
   auxiliary output; every OTHER projected name becomes part of its explicit
   column list. The precedence is observable, not a formality: a name the carrier
   happens to carry in BOTH records is kept only as a side output, and is dropped
   from its selected auxiliary outputs.

   Each of the two kept records is filtered down to the projected names, so it
   lists them in the CARRIER's own order and once each however the projection
   happens to list them, while the explicit column list is built from the
   projection and so keeps the PROJECTION's order and repetitions. A name the
   carrier's model could supply as a non-column output but which neither record
   currently carries is no part of the selection being read, so a projected name
   matching it lands in the explicit column list with the rest.

   An EMPTY projection is the other leg: it names nothing to keep, so BOTH
   records of selected non-column outputs are left exactly as they stand while
   the explicit column list becomes every column the carrier's own model defines.

   All three parts of the selection are overwritten together, so a carrier that
   has been recorded onto is not put back as it was by restoring only some of
   them. The carrier's model is untouched by either leg. -/
def recordOnto (c : Carrier) (projected : List String) : Carrier :=
  if projected.isEmpty then
    { c with columns := c.ownFields }
  else
    { c with
        columns := projected.filter
          (fun n => !c.sideSelected.contains n && !c.auxSelected.contains n),
        sideSelected := c.sideSelected.filter (fun n => projected.contains n),
        auxSelected := c.auxSelected.filter
          (fun n => projected.contains n && !c.sideSelected.contains n) }

/- The carrier this step must hand back: the carrier with the projection
   recorded onto it where the push-down applies, and otherwise the carrier
   exactly as it stands. -/
def workingCarrier (c : Carrier) (requested projected : List String) : Carrier :=
  if shouldProject c requested then recordOnto c projected else c

/- Whether a carrier can answer every name in a column list: each name is a
   column its own model defines, or one of the side outputs its selection already
   carries, or one of the auxiliary outputs its selection already carries. Both
   records of selected non-column outputs count here, and they count on equal
   terms -- the precedence between them decides only WHERE an answerable name is
   kept, never WHETHER it can be answered. A non-column output the carrier is able
   to supply but which neither record currently carries does NOT make a name
   answerable -- recording reads the selection, not the model, so `auxAvailable`
   is deliberately absent from this test -- and such a name is answerable only if
   the carrier's own model defines a column of that name. A carrier can only
   absorb a projection whose every name it can answer. -/
def answerable (c : Carrier) (names : List String) : Bool :=
  names.all (fun n =>
    c.ownFields.contains n || c.sideSelected.contains n || c.auxSelected.contains n)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- One step of assembling a compound result from several constituent carriers:
   reconcile a single shared constituent carrier with the projection the outer
   request wants every constituent to carry, and hand back the carrier this step
   will actually read columns from.

   The shared carrier is shared across repeated assemblies of the same compound
   request, so its whole selection must be treated as read-only state: this step
   reads it to decide what to project, but the carrier it hands back must be one
   whose selection it is free to reshape WITHOUT the shared carrier's own
   selection moving. Leaving the shared carrier's selection as it was on entry is
   precisely what leaves a later assembly of the same compound request free to
   project a different column list.

   `persistent` is the shared carrier (declared `mut` because the long-standing
   shape of this code reaches for it as the thing to reconcile). It MUST be
   returned unchanged, and `ensures persistent = persistentOld` pins EVERY
   observation of it — all three parts of its selection and both parts of its
   model description, not its explicit column list alone. Recording a projection
   onto a carrier overwrites all three selection parts at once, so a carrier that
   has absorbed a projection is not put back as it was by writing its explicit
   column list back afterwards, nor by restoring only one of its two records of
   selected non-column outputs.

   The two request observations are read-only and never altered: `requested` is
   the outer request's own explicit column list, which is what decides whether a
   push-down happens at all, and `projected` is the full column list the request
   pushes down.

   `recorded` says whether this step has recorded a pushed-down projection onto
   ANY constituent carrier; it is `mut` because the long-standing shape of this
   code performs that recording by reaching for the shared carrier itself.
   Together `ensures shouldProject persistentOld requested = false → recorded =
   recordedOld` and `ensures shouldProject persistentOld requested = true →
   recorded = true` say the recording happens EXACTLY on the push-down. Where the
   push-down does not apply, NO carrier is recorded onto. Where it does apply, the
   projection really is recorded onto the carrier this step hands back, rather
   than that carrier's selection merely being asserted of the result. How MANY
   times it is recorded is deliberately left free: that is not part of the
   observable behaviour.

   Each recorded name must resolve against the carrier as its selection stands,
   so this step is asked only about a push-down the carrier can answer — that is
   what the `require` states. A carrier that cannot answer a projected name — its
   own model defines no column of that name and NEITHER record of its selected
   non-column outputs carries that name — cannot absorb the projection at all, and
   this step makes no claim about that case. -/
method applyProjection (mut persistent : Carrier) (mut recorded : Bool)
    (requested : List String) (projected : List String)
    return (working : Carrier)
  require shouldProject persistent requested = true →
    answerable persistent projected = true
  ensures persistent = persistentOld
  ensures shouldProject persistentOld requested = false → recorded = recordedOld
  ensures shouldProject persistentOld requested = true → recorded = true
  ensures working = workingCarrier persistentOld requested projected
  do
    -- impl-start
    -- Take a private working carrier from the shared one, then (only where the
    -- push-down applies) record the projection onto THAT carrier, noting that a
    -- recording happened. The shared carrier is never written and never recorded
    -- onto, so it is returned exactly as received; where the push-down does not
    -- apply nothing is recorded anywhere.
    let mut working := persistent
    if shouldProject persistent requested then
      recorded := true
      working := recordOnto persistent projected
      return working
    else
      return working
    -- impl-end

prove_correct applyProjection by
  loom_solve
  all_goals simp_all [workingCarrier, shouldProject, recordOnto]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND (advisory). 16 same-spec attacks built in , all same_spec=True; 4 verify; every one of those 4 had its faithful refined patch materialized and RUN through run_resolve, and all 4 RESOLVED alongside a resolving gold control. The BROKEN criterion (a verifying wrong impl whose faithful patch does not resolve) was NOT met.

**NOTE ON SCOPE:** the prior G-EQ record in meta.json was taken against Solution.lean sha 8a4a0bf9..., but the shipped Solution.lean is a01997f5... (4-field Carrier -> 5-field, `sideSelected` + the side/aux PRECEDENCE added). So this is a fresh attack campaign against the current frozen spec, not a re-run.

### COMMANDS (from repo root swe-proof):
  verify:  bash scripts/lean_verify.sh atk_N.lean
  resolve: python resolve_one.py <name> <patch.diff>   (calls harness.run_resolve)
Verifications were run 4-at-a-time as concurrent background jobs; each attack was still individually verified to a definite exit code.

### ATTACK LEDGER (exit 0 = verifies, 1 = rejected):
REJECTED (12), each on a genuine SEMANTIC unsolved goal on a NAMED clause (logs atk_N.log):
- atk_1  PREPATCH BUG: record onto the SHARED carrier and hand it back -> exit 1, «ensures_4: persistent = persistentOld». Impl region confirmed IDENTICAL (modulo comments) to the bundle's Solution_prepatch.lean by programmatic token compare. prepatch_reproduced=True.
- atk_2  half-restore (write back only `columns`)          -> ensures_4.
- atk_6  boundary: empty projection treated as nothing-to-record -> ensures_1 (residual shows require_1: answerable persistentOld [] = true).
- atk_7  PRECEDENCE SWAP: consult auxSelected BEFORE sideSelected -> ensures_1. This is the leg the spec revision added, and it is genuinely load-bearing.
- atk_8  control-flow effect: `recorded := true` unconditionally -> ensures_3 (the no-push-down direction).
- atk_9  ungrounded-oracle echo widened by the carrier's MODEL (sorts on auxAvailable instead of the selection) -> ensures_1. Confirms `auxAvailable` is correctly absent from the reshape.
- atk_10 guard keyed on the WRONG binder (`projected` not `requested`) -> ensures_1 + ensures_2 + ensures_3.
- atk_11 DIVERGENCE probe (never-exiting `while true`) -> rejected by total correctness: "Decreasing annotations are required in total correctness semantics". Rejected by the termination lane, not a postcondition.
- atk_12 prepatch mutation confined to the EMPTY-projection leg (inside the admitted domain, since `answerable c [] ` is vacuously true) -> ensures_4. Good: the require does NOT shelter this.
- atk_14 leave sideSelected WHOLE instead of filtering it to the projected names -> ensures_1.
- atk_15 empty-projection leg over-erases (clears BOTH records too) -> ensures_1.
- atk_16 record `requested` instead of `projected` -> ensures_1.

VERIFIED (4) -- all 4 patches materialized and EXECUTED through run_resolve:
- atk_3  NO CLONE: record onto the SHARED carrier, take the working carrier off it, then restore the shared carrier's whole MODELED selection (values_select + extra_select_mask + annotation_select_mask). patch_atk_3.diff  -> resolved=True, completed=True.
- atk_4  partial domain: record only where `answerable`, else hand the carrier back untouched. patch_atk_4.diff -> resolved=True, completed=True.
- atk_5  partial domain HIDING THE PREPATCH BUG on the require-excluded subdomain. patch_atk_5.diff -> resolved=True, completed=True.
- atk_13 control-flow effect (the `recorded` ledger) confined to the require-excluded subdomain; materialized as "no clone taken where the recording is not accounted for". patch_atk_13.diff -> resolved=True, completed=True.
Gold control: patch.diff verbatim -> resolved=True, completed=True.

### FALSE-POSITIVE HYGIENE (two traps avoided, both of which would have produced a bogus verdict):
1. atk_15 first FAILED on a Lean PARSE error (multi-line record-update literal: "unexpected identifier; expected '}'", plus a bogus "no obligation found"). That is MY syntax bug, not a spec rejection. I collapsed the record update to one line, re-checked same_spec=True, and re-ran: it then failed on a genuine ensures_1 residual. Banking the parse error as a rejection would have inflated the reject lane with a non-result.
2. The known `all` SHADOWING trap is real here: the enclosing method is get_combinator_sql(self, combinator, all), so the builtin `all()` is shadowed by a bool parameter. All three partial-domain patches (atk_4/5/13) need the answerable test, and I wrote it as an EXPLICIT LOOP for exactly this reason. I also pre-flighted every patch locally before spending harness slots: each of atk_3/4/5/13 applied cleanly at base_commit and gave "Ran 26 tests ... OK (skipped=2)" on queries.test_qs_combinators with the F2P test_patch applied. A TypeError-crashing patch would have reported did-not-resolve and invented a spec break.

WHY THE PARTIAL-DOMAIN ATTACKS DO NOT BREAK THE GATE (measured, not argued). The spec carries `require shouldProject persistent requested = true -> answerable persistent projected = true`, leaving the not-answerable subdomain completely unconstrained -- atk_5 hides the literal prepatch mutation there and atk_13 hides a control-flow effect there. I instrumented the REAL push-down site in django/db/models/sql/compiler.py (logging answerable per firing) and ran both the graded module and the whole `queries` app. Every firing is answerable=True: projections ('name','order','id') x3, ('num',) x2, ('num','count'), ('id','num'), ('count','num'); zero answerable=False firings. The excluded subdomain is never reached by the graded tests, so these impls resolve. Latent, not gate-breaking.

STRONGEST FINDING -- atk_3, a MEASURED real divergence that the frame cannot see (flagged for the panel lanes, NOT a G-EQ break since its patch resolves). `ensures persistent = persistentOld` pins only the five MODELED observations. atk_3 restores all three selection records, so the frame holds in the model -- but the real Query.set_values() also writes `select` and `default_cols`, which the Carrier does not carry. Probe (tests/queries/test_sbu_probe.py, run under both gold and atk_3):
    gold  : all 7 observations clean after the push-down.
    atk_3 : the 3 MODELED ones clean, but DIRTY [UNMODELED] default_cols: True -> False, and DIRTY [UNMODELED] select: () -> (Col(name), Col(order), Col(id)).
That dirt is observable. Probe 2 (test_sbu_probe2.py) evaluates the same compound queryset as values_list, then PLAIN, then values_list again:
    gold  : VALUES ('a',2,1) / PLAIN [<ReservedName: a>] / VALUES2 (2,)
    atk_3 : VALUES ('a',2,1) / PLAIN raised TypeError: `__str__` returned non-string (type int) / VALUES2 (2,)
So atk_3 corrupts a later plain evaluation of the shared sub-query where gold does not, yet it satisfies the frozen frame and resolves (the graded suite never mixes a plain evaluation after a values push-down). This is the same class of weakness the previous revision's atk_11a exhibited: widening Carrier from 4 to 5 fields did not close it, because the missing observations are `select`/`default_cols`, neither of which was added. Closing it would need those in the Carrier (or an explicit ensures that no unmodeled sub-query state is written).

REFINEMENT.MD AUDIT (A-legs; R/I are G-CONF's). No kind-3 leg: every row A1-A8 is tagged R, I, or a documented frame/domain leg, and there are NO axioms and NO deep_model_references (meta.json: axioms=[], deep_model_references=[], G-AX status=skip). That is correct for this bundle -- the modeled operation IS the changed code, and the two callees it touches are transliterated rather than assumed: Query.clone() -> Lean value-copy (A3, sound: Lean values have no aliasing, and the only property relied on, non-mutation of the original, is the pinned frame not an assumption), and Query.set_values() -> recordOnto.

I checked recordOnto against the real set_values body at query.py:2030-2062 step by step and the correspondence HOLDS: the falsy-`fields` leg -> `{c with columns := c.ownFields}` with both masks untouched (real code assigns field_names from concrete_fields and skips both `set_*_mask` calls -- correct); the `if f in self.extra_select / elif f in self.annotation_select / else` three-way sort -> the three filters, with the `elif` faithfully rendered as the `!c.sideSelected.contains n` conjunct in the auxSelected filter (this is the precedence atk_7 confirms is load-bearing); and the two mask writes landing together with values_select -> one atomic record update (which is what defeats atk_2's half-restore).

A7's domain leg is honestly stated and I independently confirmed its direction of failure is exclusion, not misprediction. Documentation is materially better than the prior revision's: mapping.md §2 now names all five Carrier fields with per-field bijections and both masks are separated, so the earlier complaint that the map described a superseded spec is RESOLVED.

Two residual gaps worth recording: (a) A8's `recorded` ledger still has no crisp repo observable -- "whether set_values was called on ANY carrier" is not a value the repo exposes, which is precisely the freedom atk_13 exploits; (b) mapping.md §2's closing paragraph explicitly waives `select`/`default_cols`/`deferred_loading` as "outside the abstraction" per SPEC_GUIDE §2, and that waiver is exactly what atk_3 walks through -- the doc is honest about the omission but understates it, since the omitted state is reachable and its corruption is user-visible (TypeError above), not merely unmodeled.

**EVIDENCE:** 16 attack .lean + .log files, patch_atk_{3,4,5,13}.diff, patch_gold.diff, resolve_{gold,atk_3,atk_4,atk_5,atk_13}.json (each resolved=True completed=True), local_atk_{3,4,5}.txt, answerable.log, pos_control.log (EXIT=0), probe scripts, and a worktree at base_commit under dj/ -- all in  Positive control = byte-identical copy of the shipped Solution.lean, same_spec=True, verifies exit 0.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** SETUP. Base worktree at a7038adbd0 (clean, `git status --porcelain` empty). Reference for the modelled function = a copy  with benchmark-verified/django__django-11490/patch.diff applied (the one inserted line `compiler.query = compiler.query.clone()` at compiler.py:429, confirmed by reading L424-436 post-apply). Base is used only for the unchanged callees the abstraction models (Query.set_values / add_fields / clone, untouched by the patch). Gold Solution.lean verifies: lean_verify.sh exit 0.

SPEC REGION BYTE-IDENTICAL — CONFIRMED. markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True. region_hashes: axioms c815b70158..., pure f832e7548e..., spec_view b29fb45a5a... agree; only impl (fd84ac1a42...) differs, which is exactly right. NOTE: the Solution.lean sha256 is a01997f55628dc2f77582eceb674c7629315c363fbf09061fc3c2c7591539723, which differs from the 8a4a0bf990... recorded on the earlier failing G-PANEL-2 / passing G-EQ runs — the spec was REPAIRED after that failure, so I re-derived everything from scratch against the current text rather than inheriting the old verdict.

WHAT THE REPAIR CHANGED, AND WHY IT CLOSES THE OLD HOLE. The old failure was that `answerable` counted `auxAvailable` (the UNMASKED annotations/extra), so a name present in `annotations` but masked OUT of `annotation_select` was admitted by the precondition and then mispredicted, because real set_values partitions on the MASKED `annotation_select`/`extra_select` and hands every non-matching name to add_fields(), which resolves against model fields + annotation_select only. The current frozen `answerable` is `ownFields ∪ sideSelected ∪ auxSelected` and `auxAvailable` is deliberately ABSENT (the docstring states this explicitly: "recording reads the selection, not the model, so `auxAvailable` is deliberately absent from this test"). That makes the model's split observable and its domain the same observable — both the masked sets — which is exactly the real callee's structure. `recordOnto` likewise splits only on sideSelected/auxSelected. I confirmed the mirror-image hole is closed too: masked-out EXTRA name (extra(select={'e1','e2'}).values('e1'), projected ['name','e2']) is also answerable=False / real FieldError.

METHOD 1 — REAL-REPO DIFFERENTIAL SWEEP, NO MONKEYPATCHING. Built a real Django 3.0a project (sqlite in-memory, real schema_editor, real models incl. FK, O2O, M2M, self-FK and multi-table inheritance). Abstracted each sub-query Query to the 5-field Carrier per mapping.md §2 (columns=values_select, sideSelected=extra_select, auxSelected=annotation_select, auxAvailable=extra+annotations, ownFields=concrete_fields attnames) and executed the real patched block literally: persistent stays, working = persistent.clone() then working.set_values(tuple(projected)).

Swept 13 carrier shapes (plain / annotations / MASKED annotations / extra / MASKED extra / mixed / mixed-masked / extra-key-collides-with-annotation-alias / extra-key-shadows-a-concrete-field / aggregate annotation with group_by=True / masked aggregate / already-values() / MTI / MTI+annotation) x projections of length 0..3 x requested in {[], ['name'], ['name','order']}, counting only inputs where the precondition HOLDS. Result over 2543 admissible inputs (292 excluded by the precondition): 0 admitted-but-raising, 0 value divergences, 0 frame breaks. Order-STRICT comparison on `columns` (so the projection's order AND repetitions are checked, e.g. proj=['name','name'] -> columns=['name','name'] in both) and on the two mask-derived records.

METHOD 2 — LEAN CHECKS THE REAL REPO'S OWN ANSWERS. Rather than trust my Python transliteration of the pure region, I generated Lean `example ... := by decide` obligations whose RIGHT-HAND SIDES are the values the real patched Django produced, and asked Lean to prove them against the FROZEN pure region copied verbatim out of Solution.lean. 2543 cases x 6 obligations = 15258 assertions (shouldProject, and all five fields of workingCarrier). Split into 16 chunks (a single 17.9k-line file dies with a Lean interpreter deep-recursion abort, exit 134 — a file-size artifact, not a proof failure) and ran them through scripts/lean_verify.sh: ALL 16 chunks exit 0. So the Lean model reproduces the real repo exactly on every admissible input tested, with no Python-side transliteration in the trust path.

METHOD 3 — FRAME AND `recorded` ACCOUNTING AGAINST THE REAL PATCH. `ensures persistent = persistentOld` pins all FIVE observations, not just columns. Verified on the real clone across the shape/projection/requested grid: 0 violations — real Query.clone() + set_values leaves the original's values_select, extra_select, annotation_select, extra+annotations and concrete_fields all identically equal (clone() copies annotations/extra dicts and the masks, so mutating the copy cannot reach back). `recorded` accounting (false-leg preserves, true-leg sets true) matched shouldProject on every case. Also confirmed end-to-end with NO monkeypatching, on BOTH worktrees, that the frame is precisely the patch delta: qs.union(qs) then values_list('name','order') then values_list('order','name') — on BASE the shared combined_queries end up ('name','order') and eval2 wrongly returns [('a',1),('b',2)]; on PATCHED they stay () and eval2 correctly returns [(1,'a'),(2,'b')]. That is the F2P symptom, and it is what the frame clause encodes.

METHOD 4 — PRECONDITION BOUNDARY, BOTH DIRECTIONS. Probed 11 boundary names. Every admitted name really resolves (FK attname 'maker_id', MTI parent-link attname 'base_ptr_id', MTI inherited 'btitle' — all answerable=True and real OK). Every name the real callee rejects is excluded ('y' masked annotation, 'e2' masked extra, 'x' absent-on-sub-carrier, 'order__abs' — all answerable=False and real FieldError). The remaining four ('pk', 'maker__label' relation traversal, 'maker' FK name, 'tags' m2m) are excluded-but-succeeding: the precondition is STRICTER than the real callee's total domain, so the spec simply makes no claim there. That is domain narrowing, which cannot make a spec too strong — it is the direction that is safe, and mapping.md documents it explicitly as a "Documented domain limit".

DRIFT / TOO-STRONG ANALYSIS. Three specific over-strength risks checked and cleared: (1) the side-output PRECEDENCE (`elif` in set_values) is real — I built the collision carrier where the same alias 'x' sits in BOTH extra_select and annotation_select (extra(select={'x':'99'}) over annotate(x=...)), and the real callee keeps it as a side output and drops it from annotation_select, exactly as recordOnto's `&& !c.sideSelected.contains n` guard says. (2) The empty-projection leg (columns := ownFields, both mask records untouched) matches query.py:2059-2060 and was checked on every shape. (3) The group_by=True path (aggregate annotation), which set_values traverses before the split at query.py:2035-2038, writes only observations outside the abstraction (select/default_cols/deferred_loading) and produced no divergence on any of the 5 modelled fields. shouldProject reading `requested` (the outer query's OWN values_select) and not `projected` matches the guard's second conjunct at compiler.py:428 — verified by the sp column agreeing with the real guard on all 2543 cases.

**CONCLUSION.** The spec is not too strong and does not drift: on every input its precondition admits, the modelled function agrees with the real patched repo on all five observations, mechanically checked by Lean against the frozen pure region on 15258 real-repo-derived assertions with a working negative control. Where it disagrees with the real callee's domain it is narrower, never wrong. The repair specifically closed the previously-found masked-annotation divergence. Verdict FAITHFUL. Artifacts: {sweep.py,collide.py,probe.py,frame5.py,e2e.py,bound.py,gen_lean2.py,cases.json}, Lean chunks + logs.

Counterexample / evidence:

```
None. Negative control confirms the harness has teeth: perturbing 3 of the real-repo-derived `.columns` assertions in chunk C0 (['name'] -> ['ZZZ']) makes lean_verify.sh exit 1 with a `decide` failure, while the unperturbed chunk exits 0.
```

**SETUP.** Base worktree at a7038adbd0 (clean, `git status --porcelain` empty). Reference for the modelled function = a copy  with benchmark-verified/django__django-11490/patch.diff applied (the one inserted line `compiler.query = compiler.query.clone()` at compiler.py:429, confirmed by reading L424-436 post-apply). Base is used only for the unchanged callees the abstraction models (Query.set_values / add_fields / clone, untouched by the patch). Gold Solution.lean verifies: lean_verify.sh exit 0.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** django__django-11490 (velvet). Gold edit = ONE inserted line at django/db/models/sql/compiler.py:429, `compiler.query = compiler.query.clone()`, placed before the existing `compiler.query.set_values((*extra_select, *values_select, *annotation_select))` inside the `if not compiler.query.values_select and self.query.values_select:` guard. Question: does the SPEC VIEW (axioms + pure + pre/post + method signature/contract + docstrings; impl region and prove_correct body elided) disclose that edit beyond the public problem_statement? Verdict NO-LEAKAGE.

1) SPEC VIEW GENERATED, NOT ASSUMED. Ran swebench_unified.markers.spec_view(Solution.lean, VelvetBackend) rather than eyeballing the source. Confirmed markers.same_spec(Solution.lean, Solution_prepatch.lean) = True, so the spec region is byte-identical across the patched/pre-patch pair and the region I judged is the real frozen one. Confirmed the elision actually fires: the gold impl region's own comment 'Take a private working carrier from the shared one, then (only where the push-down applies) record the projection onto THAT carrier' -- which DOES name the clone mechanism -- occurs 1x in Solution.lean and 0x in the generated spec view. mapping.md's quarantine of the pre-patch code ('refinement audit only, NOT in the consumer spec view') was verified against the generated view, not trusted from its label.

2) DECISIVE CONSTRUCTIVE TEST (this is what carries the verdict, not the vocabulary sweep). If the spec view leaked the gold edit, it would force the clone-first mechanism. It does not. I authored two rivals whose spec regions are BYTE-IDENTICAL to gold (markers.same_spec = True for both) but whose mechanisms are categorically different from `clone()`, and both VERIFY against the frozen contract (scripts/lean_verify.sh, exit 0):
  - RivalA = save-and-restore, i.e. the literal pre-patch act plus a rollback: `let orig := persistent; if shouldProject ... then recorded := true; persistent := recordOnto persistent projected; let result := persistent; persistent := orig; return result`. It mutates the SHARED carrier in place (no private copy is ever taken up front) and only afterwards puts it back. In Django terms this is `set_values` on the shared `compiler.query` followed by a wholesale restore -- a fix a consumer could ship WITHOUT ever calling clone(). exit=0.
  - RivalB = rebuild-from-fields: never records onto any carrier; constructs the returned Carrier literal field-by-field ({columns := projected.filter ..., sideSelected := ..., auxSelected := ..., auxAvailable, ownFields}), so `persistent` is only ever read. exit=0.
  Controls, so exit=0 is not vacuous: Gold.lean exit=0; Solution_prepatch.lean exit=1 with `error: unsolved goals` at 190:30 (the frame clause `persistent = persistentOld`). So the harness discriminates on this file, and the spec admits >=3 distinct mechanisms. The spec pins WHAT (the shared carrier survives the step unchanged) and leaves HOW open -- clone, snapshot-and-restore, or pure reconstruction all pass. Gold is not reconstructible from the spec view.

3) VOCABULARY / IDENTIFIER SWEEP OF THE GENERATED VIEW -- ZERO HITS. Single case-insensitive regex over clon|copy|copies|duplicat|fresh|private|new object|alias|deepcopy|in.place|mutat|side.effect|reus|fix|bug|patch|regress|previous|used to|no longer|instead of|before the change|workaround|snapshot|restore|save|revert|combined|combinator|compiler|queryset|query|union|values|set_values|django|\.py|L4[0-9][0-9]|line [0-9]|sql|annotation|extra_select. No matches. The view is de-identified: it speaks only of carriers, selections, push-down, recording. Note the sweep alone is weak evidence (per my own prior experience, leak vocabulary trips on innocent prose and conversely absence of vocabulary does not prove absence of leak) -- it is (2) that decides.

4) CLOSEST LEAK CANDIDATE, EXAMINED AND CLEARED. Spec-view lines 135-136 and 150-152: `persistent` is 'declared `mut` because the long-standing shape of this code reaches for it as the thing to reconcile', and `recorded` 'is `mut` because the long-standing shape of this code performs that recording by reaching for the shared carrier itself'. This is the only place the view alludes to the pre-change code shape. Non-leaking on three independent grounds: (a) it is forced spec-view furniture -- the signature genuinely declares `mut persistent`, so the contract must explain why a parameter pinned to its entry value is nonetheless mutable, and it does so without naming clone/copy/set_values; (b) it does not narrow the mechanism at all -- RivalA verifies while doing exactly the 'reaching for the shared carrier' the comment describes, so the comment states the obligation, not gold's discharge of it; (c) it is within public scope: problem_statement explicitly links compiler.py#L428-433, where `compiler.query.set_values(...)` being invoked on the shared sub-query object is already visible to any consumer.

5) **FRAME CLAUSE AND SYMPTOM PROSE ARE WITHIN PUBLIC SCOPE.** `ensures persistent = persistentOld` and the docstring's 'Leaving the shared carrier's selection as it was on entry is precisely what leaves a later assembly of the same compound request free to project a different column list' restate the public symptom -- problem_statement shows qs1.union(qs1).values_list('name','order') then values_list('order') returning the SAME ('a',2), i.e. state persisting across repeated evaluations, at the linked lines. A spec must state the required post-state; that is the WHAT every spec owes its consumer, and it is exactly what the public bug report already asserts.

6) EXTRA STRUCTURE IS STRENGTH, NOT DISCLOSURE. Carrier's sideSelected/auxSelected/auxAvailable/ownFields, the `recorded` flag, `recordOnto`'s side-output-before-aux precedence, and `answerable` are richer than problem_statement, but they model UNCHANGED surrounding code (set_values sorting names across extra_select / values_select / annotation_select and clearing deferred loading), and their effect is to make the frame total -- pinning all five observations is what kills a partial-restore cheat. None of it identifies the inserted line. hints_text is empty for this instance, so no hints-based scope question arises.

Caveat recorded for the panel, NOT a leakage finding: the `require shouldProject persistent requested = true -> answerable persistent projected = true` precondition leaves the not-answerable subdomain unconstrained (a latent spec-strength issue in the G-EQ lane, already noted in verdict.md). That is under-constraint, the opposite failure from leakage, and it does not bear on this gate.

**Artifacts:** {Gold,Prepatch,RivalA,RivalB}.lean + .log; spec view at specview_11490.lean.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
