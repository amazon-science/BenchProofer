# P2 adversarial audit — django__django-11551

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -98,18 +98,11 @@
   ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
   do
     -- impl-start
-    -- An invokable entry, or one that is an attribute of the administrator, is
-    -- acceptable outright. Otherwise resolve the entry to a model field: the
-    -- field registry first, then attribute access on the model class; only
-    -- when both fail is the entry unresolvable (E108). Whenever a field is
-    -- resolved by either route, it is acceptable unless it is a many-to-many
-    -- relation (E109).
     let result : CheckResult :=
       if isCallable then CheckResult.ok
       else if hasAttrObj then CheckResult.ok
-      else if getFieldRaises then
-        (if modelAttrRaises then CheckResult.e108
-         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
+      else if modelAttrRaises then CheckResult.e108
+      else if getFieldRaises then CheckResult.ok
       else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -98,19 +98,7 @@
   ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
   do
     -- impl-start
-    -- An invokable entry, or one that is an attribute of the administrator, is
-    -- acceptable outright. Otherwise resolve the entry to a model field: the
-    -- field registry first, then attribute access on the model class; only
-    -- when both fail is the entry unresolvable (E108). Whenever a field is
-    -- resolved by either route, it is acceptable unless it is a many-to-many
-    -- relation (E109).
-    let result : CheckResult :=
-      if isCallable then CheckResult.ok
-      else if hasAttrObj then CheckResult.ok
-      else if getFieldRaises then
-        (if modelAttrRaises then CheckResult.e108
-         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
-      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
+    let result : CheckResult := CheckResult.ok
     return result
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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -98,18 +98,12 @@
   ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
   do
     -- impl-start
-    -- An invokable entry, or one that is an attribute of the administrator, is
-    -- acceptable outright. Otherwise resolve the entry to a model field: the
-    -- field registry first, then attribute access on the model class; only
-    -- when both fail is the entry unresolvable (E108). Whenever a field is
-    -- resolved by either route, it is acceptable unless it is a many-to-many
-    -- relation (E109).
     let result : CheckResult :=
       if isCallable then CheckResult.ok
       else if hasAttrObj then CheckResult.ok
       else if getFieldRaises then
-        (if modelAttrRaises then CheckResult.e108
-         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
+        (if modelAttrRaises then CheckResult.e109
+         else if fieldIsM2M then CheckResult.e108 else CheckResult.ok)
       else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -98,18 +98,10 @@
   ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
   do
     -- impl-start
-    -- An invokable entry, or one that is an attribute of the administrator, is
-    -- acceptable outright. Otherwise resolve the entry to a model field: the
-    -- field registry first, then attribute access on the model class; only
-    -- when both fail is the entry unresolvable (E108). Whenever a field is
-    -- resolved by either route, it is acceptable unless it is a many-to-many
-    -- relation (E109).
     let result : CheckResult :=
       if isCallable then CheckResult.ok
       else if hasAttrObj then CheckResult.ok
-      else if getFieldRaises then
-        (if modelAttrRaises then CheckResult.e108
-         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
+      else if getFieldRaises then CheckResult.e108
       else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -98,19 +98,13 @@
   ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
   do
     -- impl-start
-    -- An invokable entry, or one that is an attribute of the administrator, is
-    -- acceptable outright. Otherwise resolve the entry to a model field: the
-    -- field registry first, then attribute access on the model class; only
-    -- when both fail is the entry unresolvable (E108). Whenever a field is
-    -- resolved by either route, it is acceptable unless it is a many-to-many
-    -- relation (E109).
     let result : CheckResult :=
       if isCallable then CheckResult.ok
       else if hasAttrObj then CheckResult.ok
       else if getFieldRaises then
         (if modelAttrRaises then CheckResult.e108
          else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
-      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
+      else CheckResult.ok
     return result
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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -98,15 +98,8 @@
   ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
   do
     -- impl-start
-    -- An invokable entry, or one that is an attribute of the administrator, is
-    -- acceptable outright. Otherwise resolve the entry to a model field: the
-    -- field registry first, then attribute access on the model class; only
-    -- when both fail is the entry unresolvable (E108). Whenever a field is
-    -- resolved by either route, it is acceptable unless it is a many-to-many
-    -- relation (E109).
     let result : CheckResult :=
       if isCallable then CheckResult.ok
-      else if hasAttrObj then CheckResult.ok
       else if getFieldRaises then
         (if modelAttrRaises then CheckResult.e108
          else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of
@@ -98,19 +98,8 @@
   ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
   do
     -- impl-start
-    -- An invokable entry, or one that is an attribute of the administrator, is
-    -- acceptable outright. Otherwise resolve the entry to a model field: the
-    -- field registry first, then attribute access on the model class; only
-    -- when both fail is the entry unresolvable (E108). Whenever a field is
-    -- resolved by either route, it is acceptable unless it is a many-to-many
-    -- relation (E109).
     let result : CheckResult :=
-      if isCallable then CheckResult.ok
-      else if hasAttrObj then CheckResult.ok
-      else if getFieldRaises then
-        (if modelAttrRaises then CheckResult.e108
-         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
-      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
+      listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
     return result
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
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs. A model-administration validator inspects one entry of a
--  display configuration and decides how it should be reported. The runtime
--  observations the decision depends on — whether the entry is itself an
--  invokable object, whether it names an attribute of the administrator,
--  whether the model's field registry knows the name, whether plain attribute
--  access on the model class succeeds, and whether the resolved descriptor is
--  a many-to-many relation — are abstracted to the boolean inputs of the
--  method. Each is an R-refinement of a real observation (callable / hasattr /
--  field-registry lookup / attribute access / relation kind), validated
--  against the real objects by conformance_check.py (G-CONF). Nothing is
--  consumed as an axiom — see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The three ways a single display-configuration entry can be reported:

   * `ok`   — the entry is acceptable, no message is produced (`[]`);
   * `e108` — the entry does not resolve to anything usable on the model
              (`admin.E108`, "refers to '…', which is not a callable, an
              attribute of …, or an attribute or method on …");
   * `e109` — the entry resolves to a many-to-many relation, which is not
              permitted here (`admin.E109`, "must not be a ManyToManyField").

   The error identifiers `admin.E108` / `admin.E109` are part of the public
   problem statement. -/
inductive CheckResult where
  | ok
  | e108
  | e109
  deriving DecidableEq, Inhabited

/- The acceptable / E108 / E109 decision for one display-configuration entry.

   Reading order, mirroring how the validator examines the entry:

   1. An invokable entry (`isCallable`) is always acceptable.
   2. Otherwise, an entry naming an attribute of the administrator itself
      (`hasAttrObj`) is always acceptable.
   3. Otherwise the entry must resolve to a model field. The model's field
      registry is consulted first; only if that lookup fails (`getFieldRaises`)
      is plain attribute access on the model class attempted, and only if THAT
      also fails (`modelAttrRaises`) is the entry unresolvable and reported
      `e108`. Crucially, a failed registry lookup alone never condemns the
      entry — attribute access is still tried.
   4. Whenever a field IS resolved (by either route), the sole remaining
      question is whether it is a many-to-many relation (`fieldIsM2M`):
      if so the entry is reported `e109`, otherwise it is acceptable.

   `fieldIsM2M` is only consulted on the paths where a field was resolved; on
   the `e108` path no field exists and its value is immaterial. -/
@[grind] def listDisplayItemOutcome
    (isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M : Bool) : CheckResult :=
  if isCallable then CheckResult.ok
  else if hasAttrObj then CheckResult.ok
  else if getFieldRaises then
    (if modelAttrRaises then CheckResult.e108
     else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
  else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Validate one entry of a model administrator's display configuration and
   decide how it is reported: acceptable, E108 (does not resolve to anything
   usable), or E109 (resolves to a many-to-many relation).

   Desired behaviour (the abstract contract; see `listDisplayItemOutcome`):
   an invokable entry, or one naming an attribute of the administrator, is
   acceptable. Otherwise the entry must resolve to a model field. The field
   registry is consulted first; if that fails, attribute access on the model
   class is attempted; the entry is reported E108 only when BOTH resolution
   routes fail. Whenever a field is resolved by either route, the entry is
   reported E109 exactly when that field is a many-to-many relation, and is
   acceptable otherwise.

   All five inputs are read-only observations (none declared `mut`): the
   routine inspects them and returns the report for the entry; it mutates
   nothing (directive 5). The decision is pinned exactly by
   `listDisplayItemOutcome`. -/
method listDisplayItemCheck
    (isCallable : Bool) (hasAttrObj : Bool) (getFieldRaises : Bool)
    (modelAttrRaises : Bool) (fieldIsM2M : Bool)
    return (out : CheckResult)
  ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
  do
    -- impl-start
    -- An invokable entry, or one that is an attribute of the administrator, is
    -- acceptable outright. Otherwise resolve the entry to a model field: the
    -- field registry first, then attribute access on the model class; only
    -- when both fail is the entry unresolvable (E108). Whenever a field is
    -- resolved by either route, it is acceptable unless it is a many-to-many
    -- relation (E109).
    let result : CheckResult :=
      if isCallable then CheckResult.ok
      else if hasAttrObj then CheckResult.ok
      else if getFieldRaises then
        (if modelAttrRaises then CheckResult.e108
         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
    return result
    -- impl-end

prove_correct listDisplayItemCheck by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11551 (velvet). The spec's ensures pins the method output EXACTLY to the total pure function `listDisplayItemOutcome` over the full cross-product of the 5 boolean observations (isCallable, hasAttrObj, getFieldRaises, modelAttrRaises, fieldIsM2M). No axioms (G-AX empty), so the only trust point is R/I refinement fidelity. All same_spec checks True (axioms/pure/pre/post byte-identical; only impl region edited).

### ATTACKS (all same_spec=True; command: `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug: gate resolution on modelAttrRaises BEFORE registry -> E108 whenever modelAttrRaises, ignoring getFieldRaises): exit=1 unsolved goals -> does NOT verify. Reproduces the prepatch defect (matches Solution_prepatch.lean).
- atk_2 (partial-domain collapse: always ok): exit=1 -> does NOT verify.
- atk_3 (boundary flip: swap e108<->e109 on getFieldRaises path): exit=1 -> does NOT verify.
- atk_4 (control-flow-effect: E108 whenever getFieldRaises regardless of modelAttrRaises): exit=1 -> does NOT verify.
- atk_5 (boundary: ignore fieldIsM2M on the registry-hit path -> always ok there): exit=1 -> does NOT verify.
- atk_6 (control-flow-effect: drop hasAttrObj short-circuit): exit=1 -> does NOT verify.
- atk_7 (ungrounded-oracle echo: return listDisplayItemOutcome directly): exit=0 -> VERIFIES. Behaviorally IDENTICAL to the deep oracle == gold post-patch flow, so its faithful refined patch is the gold patch verbatim.
- pos_control (exact copy of Solution.lean): exit=0 -> verifies.

Every behaviorally-distinct wrong impl (atk_1..6) fails prove_correct with 'unsolved goals' because the postcondition equals a total function; only a behaviorally-gold impl can satisfy it. Hence the only verifying same-spec impl (atk_7) is gold-equivalent.

RESOLVE (protocol step 2): materialized atk_7's faithful patch (= gold patch, saved at gold_patch.txt) and ran it through the official harness via swebench_unified.harness.run_resolve('django__django-11551', gold, run_id='sbu-audit-11551-mine', timeout=1800, retries=2). Observed: RESOLVED=True, COMPLETED=True, NOTE='resolved' (log: resolve_gold2.log). Independently corroborated by a concurrent run of the byte-identical patch (sha 5eeda5f9b9) completing resolved=True, with F2P test test_valid_field_accessible_via_instance passing and all 121 P2P passing. (An earlier attempt COMPLETED=False due to image-removal race under 400+ contending run_evaluation procs; the retried run completed cleanly.)

REFINEMENT AUDIT (refinement.md): legs A1-A6 all tagged R+I; B/C confirm no A (axiom) legs, no kind-3. Verified the deep model traces exactly onto the gold control flow: callable->ok (A1), hasattr(obj,item)->ok (A2), try get_field / except FieldDoesNotExist -> getFieldRaises branch (A3), inner getattr / except AttributeError -> E108 (A4), shared isinstance(field, ManyToManyField) -> E109 else [] on both field-resolved paths (A5), error-id observable (A6). Critically, when getFieldRaises=false the model never inspects modelAttrRaises, mirroring reality where getattr is not called on a registry hit. No kind-3 leg; correspondence holds. Spec is tight: verify => correct.

VERDICT: SOUND. >=5 distinct attacks run; every verifying same-spec impl's faithful patch resolves under the official harness. No verify-but-not-resolve witness exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of
--  its inputs. A model-administration validator inspects one entry of a
--  display configuration and decides how it should be reported. The runtime
--  observations the decision depends on — whether the entry is itself an
--  invokable object, whether it names an attribute of the administrator,
--  whether the model's field registry knows the name, whether plain attribute
--  access on the model class succeeds, and whether the resolved descriptor is
--  a many-to-many relation — are abstracted to the boolean inputs of the
--  method. Each is an R-refinement of a real observation (callable / hasattr /
--  field-registry lookup / attribute access / relation kind), validated
--  against the real objects by conformance_check.py (G-CONF). Nothing is
--  consumed as an axiom — see refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The three ways a single display-configuration entry can be reported:

   * `ok`   — the entry is acceptable, no message is produced (`[]`);
   * `e108` — the entry does not resolve to anything usable on the model
              (`admin.E108`, "refers to '…', which is not a callable, an
              attribute of …, or an attribute or method on …");
   * `e109` — the entry resolves to a many-to-many relation, which is not
              permitted here (`admin.E109`, "must not be a ManyToManyField").

   The error identifiers `admin.E108` / `admin.E109` are part of the public
   problem statement. -/
inductive CheckResult where
  | ok
  | e108
  | e109
  deriving DecidableEq, Inhabited

/- The acceptable / E108 / E109 decision for one display-configuration entry.

   Reading order, mirroring how the validator examines the entry:

   1. An invokable entry (`isCallable`) is always acceptable.
   2. Otherwise, an entry naming an attribute of the administrator itself
      (`hasAttrObj`) is always acceptable.
   3. Otherwise the entry must resolve to a model field. The model's field
      registry is consulted first; only if that lookup fails (`getFieldRaises`)
      is plain attribute access on the model class attempted, and only if THAT
      also fails (`modelAttrRaises`) is the entry unresolvable and reported
      `e108`. Crucially, a failed registry lookup alone never condemns the
      entry — attribute access is still tried.
   4. Whenever a field IS resolved (by either route), the sole remaining
      question is whether it is a many-to-many relation (`fieldIsM2M`):
      if so the entry is reported `e109`, otherwise it is acceptable.

   `fieldIsM2M` is only consulted on the paths where a field was resolved; on
   the `e108` path no field exists and its value is immaterial. -/
@[grind] def listDisplayItemOutcome
    (isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M : Bool) : CheckResult :=
  if isCallable then CheckResult.ok
  else if hasAttrObj then CheckResult.ok
  else if getFieldRaises then
    (if modelAttrRaises then CheckResult.e108
     else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
  else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Validate one entry of a model administrator's display configuration and
   decide how it is reported: acceptable, E108 (does not resolve to anything
   usable), or E109 (resolves to a many-to-many relation).

   Desired behaviour (the abstract contract; see `listDisplayItemOutcome`):
   an invokable entry, or one naming an attribute of the administrator, is
   acceptable. Otherwise the entry must resolve to a model field. The field
   registry is consulted first; if that fails, attribute access on the model
   class is attempted; the entry is reported E108 only when BOTH resolution
   routes fail. Whenever a field is resolved by either route, the entry is
   reported E109 exactly when that field is a many-to-many relation, and is
   acceptable otherwise.

   All five inputs are read-only observations (none declared `mut`): the
   routine inspects them and returns the report for the entry; it mutates
   nothing (directive 5). The decision is pinned exactly by
   `listDisplayItemOutcome`. -/
method listDisplayItemCheck
    (isCallable : Bool) (hasAttrObj : Bool) (getFieldRaises : Bool)
    (modelAttrRaises : Bool) (fieldIsM2M : Bool)
    return (out : CheckResult)
  ensures out = listDisplayItemOutcome isCallable hasAttrObj getFieldRaises modelAttrRaises fieldIsM2M
  do
    -- impl-start
    -- An invokable entry, or one that is an attribute of the administrator, is
    -- acceptable outright. Otherwise resolve the entry to a model field: the
    -- field registry first, then attribute access on the model class; only
    -- when both fail is the entry unresolvable (E108). Whenever a field is
    -- resolved by either route, it is acceptable unless it is a many-to-many
    -- relation (E109).
    let result : CheckResult :=
      if isCallable then CheckResult.ok
      else if hasAttrObj then CheckResult.ok
      else if getFieldRaises then
        (if modelAttrRaises then CheckResult.e108
         else if fieldIsM2M then CheckResult.e109 else CheckResult.ok)
      else if fieldIsM2M then CheckResult.e109 else CheckResult.ok
    return result
    -- impl-end

prove_correct listDisplayItemCheck by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-11551 (velvet). The spec's ensures pins the method output EXACTLY to the total pure function `listDisplayItemOutcome` over the full cross-product of the 5 boolean observations (isCallable, hasAttrObj, getFieldRaises, modelAttrRaises, fieldIsM2M). No axioms (G-AX empty), so the only trust point is R/I refinement fidelity. All same_spec checks True (axioms/pure/pre/post byte-identical; only impl region edited).

### ATTACKS (all same_spec=True; command: `bash scripts/lean_verify.sh <f>`):
- atk_1 (prepatch bug: gate resolution on modelAttrRaises BEFORE registry -> E108 whenever modelAttrRaises, ignoring getFieldRaises): exit=1 unsolved goals -> does NOT verify. Reproduces the prepatch defect (matches Solution_prepatch.lean).
- atk_2 (partial-domain collapse: always ok): exit=1 -> does NOT verify.
- atk_3 (boundary flip: swap e108<->e109 on getFieldRaises path): exit=1 -> does NOT verify.
- atk_4 (control-flow-effect: E108 whenever getFieldRaises regardless of modelAttrRaises): exit=1 -> does NOT verify.
- atk_5 (boundary: ignore fieldIsM2M on the registry-hit path -> always ok there): exit=1 -> does NOT verify.
- atk_6 (control-flow-effect: drop hasAttrObj short-circuit): exit=1 -> does NOT verify.
- atk_7 (ungrounded-oracle echo: return listDisplayItemOutcome directly): exit=0 -> VERIFIES. Behaviorally IDENTICAL to the deep oracle == gold post-patch flow, so its faithful refined patch is the gold patch verbatim.
- pos_control (exact copy of Solution.lean): exit=0 -> verifies.

Every behaviorally-distinct wrong impl (atk_1..6) fails prove_correct with 'unsolved goals' because the postcondition equals a total function; only a behaviorally-gold impl can satisfy it. Hence the only verifying same-spec impl (atk_7) is gold-equivalent.

RESOLVE (protocol step 2): materialized atk_7's faithful patch (= gold patch, saved at gold_patch.txt) and ran it through the official harness via swebench_unified.harness.run_resolve('django__django-11551', gold, run_id='sbu-audit-11551-mine', timeout=1800, retries=2). Observed: RESOLVED=True, COMPLETED=True, NOTE='resolved' (log: resolve_gold2.log). Independently corroborated by a concurrent run of the byte-identical patch (sha 5eeda5f9b9) completing resolved=True, with F2P test test_valid_field_accessible_via_instance passing and all 121 P2P passing. (An earlier attempt COMPLETED=False due to image-removal race under 400+ contending run_evaluation procs; the retried run completed cleanly.)

REFINEMENT AUDIT (refinement.md): legs A1-A6 all tagged R+I; B/C confirm no A (axiom) legs, no kind-3. Verified the deep model traces exactly onto the gold control flow: callable->ok (A1), hasattr(obj,item)->ok (A2), try get_field / except FieldDoesNotExist -> getFieldRaises branch (A3), inner getattr / except AttributeError -> E108 (A4), shared isinstance(field, ManyToManyField) -> E109 else [] on both field-resolved paths (A5), error-id observable (A6). Critically, when getFieldRaises=false the model never inspects modelAttrRaises, mirroring reality where getattr is not called on a registry hit. No kind-3 leg; correspondence holds. Spec is tight: verify => correct.

VERDICT: SOUND. >=5 distinct attacks run; every verifying same-spec impl's faithful patch resolves under the official harness. No verify-but-not-resolve witness exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for django__django-11551 velvet bundle. The modeled function listDisplayItemOutcome(isCallable,hasAttrObj,getFieldRaises,modelAttrRaises,fieldIsM2M):CheckResult{ok,e108,e109} models the POST-patch ModelAdminChecks._check_list_display_item (checks.py:718). Findings:

(1) SPEC REGION BYTE-IDENTICAL: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True. The frozen spec view (ensures out = listDisplayItemOutcome ..., the CheckResult type, and the nested-if ladder) is identical pre/post, so the spec is not fitted to the submitted impl.

(2) LEAN VERIFIES: Solution.lean elaborates exit 0 under lean_verify.sh (proof discharged by loom_solve).

(3) MODEL == REAL CALLEE (exhaustive): The gold patch restructures the body to consult the field registry (get_field) BEFORE condemning, falls back to getattr, emits E108 only when BOTH raise, and E109 iff the resolved field is M2M. Symbolic simulation of the patched control flow over all 32 boolean observation tuples vs. listDisplayItemOutcome: 0 mismatches. The abstraction correctly leaves fieldIsM2M immaterial on the e108 path (matching real short-circuit).

 EMPIRICAL CONFORMANCE ON THE ACTUALLY-PATCHED REPO: I applied the real gold patch to the base_commit worktree and ran conformance_check.py against it: G-CONF OK, 100008 inputs, seed=11551, 0 disagreements. This includes the issue's instance-only PositionField F2P scenario (getFieldRaises=False, modelAttrRaises=True -> ok), which the pre-patch hasattr-gate wrongly reported as E108.

No realizable input found where the modeled function disagrees with the real patched callee. Spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True. Mechanical G-LEAK screen over the spec view passes cleanly (hard_failures=[], warnings=[]): no diff markers, no reproduced gold-patch line, no patched file path/module, no narration terms, no patched-symbol collisions. Critically, the public problem_statement already contains the ENTIRE corrected function verbatim (the try get_field / except FieldDoesNotExist -> try getattr / except AttributeError -> E108, then shared isinstance(field, ManyToManyField) -> E109 else []) PLUS a full 12-row correctness truth table and the admin.E108/E109 ids. The spec view's listDisplayItemOutcome nested-if ladder and its descriptive comments merely transliterate that already-public correct behavior; they add no gold-edit information beyond problem_statement. The prepatch/regression discussion (the hasattr(obj.model,item) gate) lives only in mapping.md sec.2 and refinement.md, explicitly outside the consumer spec view. Nothing in the spec view leaks the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
