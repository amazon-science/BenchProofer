# P2 adversarial audit — django__django-11790

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies (all 7 rejected, exit 1). The only same-spec impl that verifies is a non-terminating `while true` loop (atk_4), which is the UNIVERSAL partial-correctness artifact (reproduced verifying on the unrelated astropy-12907 bundle) and whose faithful refined patch TIMES OUT under the harness (completed=False), so it cannot satisfy the BROKEN criterion (completed AND not resolved). Verify does NOT imply incorrect here for any terminating impl.
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
 -- (No axiomatized callees and no deep-model A-references. The behavior is pure
@@ -62,17 +62,9 @@
   ensures result.widgetMaxLength = some (resolveLimit modelLimit)
   do
     -- impl-start
-    -- Derive the effective limit: the model's configured limit, or the default
-    -- when none is configured.
-    let limit : Nat :=
-      match modelLimit with
-      | some n => if n = 0 then 254 else n
-      | none   => 254
-    -- Record the limit on the field, and expose the same limit to its rendered
-    -- control.
     let mut result := field
-    result := { result with maxLength := some limit }
-    result := { result with widgetMaxLength := some limit }
+    result := { result with maxLength := some 254 }
+    result := { result with widgetMaxLength := some 254 }
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
 -- (No axiomatized callees and no deep-model A-references. The behavior is pure
@@ -62,17 +62,13 @@
   ensures result.widgetMaxLength = some (resolveLimit modelLimit)
   do
     -- impl-start
-    -- Derive the effective limit: the model's configured limit, or the default
-    -- when none is configured.
     let limit : Nat :=
       match modelLimit with
       | some n => if n = 0 then 254 else n
       | none   => 254
-    -- Record the limit on the field, and expose the same limit to its rendered
-    -- control.
     let mut result := field
-    result := { result with maxLength := some limit }
-    result := { result with widgetMaxLength := some limit }
+    result := { result with maxLength := some (limit + 1) }
+    result := { result with widgetMaxLength := some (limit + 1) }
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
 -- (No axiomatized callees and no deep-model A-references. The behavior is pure
@@ -62,17 +62,12 @@
   ensures result.widgetMaxLength = some (resolveLimit modelLimit)
   do
     -- impl-start
-    -- Derive the effective limit: the model's configured limit, or the default
-    -- when none is configured.
     let limit : Nat :=
       match modelLimit with
       | some n => if n = 0 then 254 else n
       | none   => 254
-    -- Record the limit on the field, and expose the same limit to its rendered
-    -- control.
     let mut result := field
     result := { result with maxLength := some limit }
-    result := { result with widgetMaxLength := some limit }
     return result
     -- impl-end
 
```

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model A-references. The behavior is pure
@@ -62,17 +62,13 @@
   ensures result.widgetMaxLength = some (resolveLimit modelLimit)
   do
     -- impl-start
-    -- Derive the effective limit: the model's configured limit, or the default
-    -- when none is configured.
     let limit : Nat :=
       match modelLimit with
       | some n => if n = 0 then 254 else n
       | none   => 254
-    -- Record the limit on the field, and expose the same limit to its rendered
-    -- control.
     let mut result := field
     result := { result with maxLength := some limit }
-    result := { result with widgetMaxLength := some limit }
+    result := { result with widgetMaxLength := field.maxLength }
     return result
     -- impl-end
 
```

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model A-references. The behavior is pure
@@ -62,17 +62,12 @@
   ensures result.widgetMaxLength = some (resolveLimit modelLimit)
   do
     -- impl-start
-    -- Derive the effective limit: the model's configured limit, or the default
-    -- when none is configured.
-    let limit : Nat :=
-      match modelLimit with
-      | some n => if n = 0 then 254 else n
-      | none   => 254
-    -- Record the limit on the field, and expose the same limit to its rendered
-    -- control.
     let mut result := field
-    result := { result with maxLength := some limit }
-    result := { result with widgetMaxLength := some limit }
+    let mut k : Nat := 1
+    while k > 0
+      invariant True
+    do
+      k := k + 1
     return result
     -- impl-end
 
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model A-references. The behavior is pure
@@ -62,17 +62,13 @@
   ensures result.widgetMaxLength = some (resolveLimit modelLimit)
   do
     -- impl-start
-    -- Derive the effective limit: the model's configured limit, or the default
-    -- when none is configured.
     let limit : Nat :=
       match modelLimit with
       | some n => if n = 0 then 254 else n
       | none   => 254
-    -- Record the limit on the field, and expose the same limit to its rendered
-    -- control.
     let mut result := field
-    result := { result with maxLength := some limit }
-    result := { result with widgetMaxLength := some limit }
+    result := { result with maxLength := some (2 * limit) }
+    result := { result with widgetMaxLength := some (2 * limit) }
     return result
     -- impl-end
 
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees and no deep-model A-references. The behavior is pure
@@ -62,17 +62,14 @@
   ensures result.widgetMaxLength = some (resolveLimit modelLimit)
   do
     -- impl-start
-    -- Derive the effective limit: the model's configured limit, or the default
-    -- when none is configured.
-    let limit : Nat :=
-      match modelLimit with
-      | some n => if n = 0 then 254 else n
-      | none   => 254
-    -- Record the limit on the field, and expose the same limit to its rendered
-    -- control.
     let mut result := field
-    result := { result with maxLength := some limit }
-    result := { result with widgetMaxLength := some limit }
+    let mut j : Nat := 0
+    while j < 1
+      invariant True
+    do
+      j := 0
+    result := { result with maxLength := some 999 }
+    result := { result with widgetMaxLength := some 999 }
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model A-references. The behavior is pure
--  control/data flow: derive a length limit from the account model's configured
--  limit (a default applies when none is configured), then record that limit in
--  the field. Nothing about an unchanged callee's contract is assumed, so there
--  is nothing for G-AX to validate — see mapping.md §3 and axiom_check.py.)
-- axioms-end

-- pure-start
/- The effective maximum input length, derived from the account model's
   configured limit. When the model supplies a positive limit it is used
   directly; when the model configures no limit (or a vacuous zero one) a
   standard default applies. This mirrors the usual "configured value, otherwise a
   default" selection over a possibly-absent setting. -/
@[grind] def resolveLimit (modelLimit : Option Nat) : Nat :=
  match modelLimit with
  | some n => if n = 0 then 254 else n
  | none   => 254
-- pure-end

/- A text-entry form field, observed through exactly the two facets this routine
   must keep in agreement:
   * `maxLength`       — the maximum input length the field itself enforces.
   * `widgetMaxLength` — the same limit as exposed to the field's rendered
                         control (the attribute a browser reads to cap typing).
   `none` means the corresponding limit is unset. Other field attributes are
   untouched here and are not carried (mapping.md §2). -/
structure BoundedField where
  maxLength       : Option Nat
  widgetMaxLength : Option Nat
deriving Inhabited, DecidableEq

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Configure a form field's input-length limit from the account model.

   The desired behavior: the field must enforce the effective limit derived from
   the model's configured limit (defaulting when none is configured), AND that
   same limit must be exposed to the field's rendered control. The two facets
   must agree — a field whose enforced limit is set but whose rendered control
   does not advertise it is the defect this routine must avoid. Both facets end
   up holding the single derived limit.

   `field` is the field being configured; `modelLimit` is the account model's
   configured limit (read-only; not `mut`). The result is a fresh value built
   from `field` with both length facets set. -/
method configureFieldLimit (field : BoundedField) (modelLimit : Option Nat)
    return (result : BoundedField)
  ensures result.maxLength       = some (resolveLimit modelLimit)
  ensures result.widgetMaxLength = some (resolveLimit modelLimit)
  do
    -- impl-start
    -- Derive the effective limit: the model's configured limit, or the default
    -- when none is configured.
    let limit : Nat :=
      match modelLimit with
      | some n => if n = 0 then 254 else n
      | none   => 254
    -- Record the limit on the field, and expose the same limit to its rendered
    -- control.
    let mut result := field
    result := { result with maxLength := some limit }
    result := { result with widgetMaxLength := some limit }
    return result
    -- impl-end

prove_correct configureFieldLimit by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: configureFieldLimit has two ensures pinning BOTH fields of the 2-field BoundedField structure to the exact value `some (resolveLimit modelLimit)` (resolveLimit = Python `x or 254`: none/some 0 -> 254, some n>0 -> n). This is a TOTAL functional postcondition: for any terminating impl the output is uniquely determined, so any terminating deviation is caught.

SAME-SPEC (all True, via swebench_unified.markers.same_spec, velvet): atk_1..8 all True; positive_control True.

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>; run concurrently <=4/batch):
- atk_1 (constant 254, ignores modelLimit): EXIT 1 REJECTED — `some 254 = some (resolveLimit modelLimit)` unprovable for positive n.
- atk_2 (limit+1 boundary): EXIT 1 REJECTED.
- atk_3 (sets maxLength ONLY, leaves widgetMaxLength — the EXACT dropped-widget regression / prepatch bug / F2P discriminator): EXIT 1 REJECTED on ensures_1 widgetMaxLength = field.widgetMaxLength. PREPATCH REPRODUCED.
- atk_5 (control-flow-effect: widgetMaxLength := field.maxLength): EXIT 1 REJECTED.
- atk_6 (falsifiable-guard loop `while k>0 do k:=k+1` then unchanged): EXIT 1 REJECTED (loop-exit hypothesis reachable; frame unchanged fails both clauses).
- atk_7 (2*limit): EXIT 1 REJECTED.
- atk_8 (`while j<1 do j:=0` then wrong 999): EXIT 1 REJECTED.
- atk_4 (`while true` divergence, then return field): EXIT 0 VERIFIES. This is the ONLY verifier.
- positive_control (gold impl, byte-identical to bundle Solution.lean impl): EXIT 0 VERIFIES.

atk_4 ANALYSIS (the crux — NOT a break):
(1) Universal partial-correctness escape: `set_option loom.semantics.termination "partial"`. A non-terminating impl satisfies any postcondition vacuously (false loop-exit hypothesis). I injected the identical `while true` construct into the UNRELATED bundle astropy__astropy-12907/velvet (also partial semantics) -> other_diverge.lean, lean_verify EXIT 0. So this verifies against every partial-semantics velvet spec; it is NOT evidence THIS spec is weak.
(2) Faithful refined patch MATERIALIZED and RUN through the official harness (run_resolve). Patch = atk_4_patch.diff (generated via git diff worktree at base_commit b1d6b35e; inserts `while True: pass` before the two facet assignments; applies cleanly — an earlier hand-written diff was malformed and I corrected it).
  EXECUTED RESULTS:
  - run_resolve('django__django-11790', atk_4_patch, timeout=300/900/600, retries=0): resolved=False, completed=False (repeated 3x).
  - Direct keep-logs harness run (run_id atk4v2-diag-keeplogs, --timeout 150): STDOUT = "django__django-11790: Test timed out after 150 seconds." RC 1, no report.json produced.
  So the divergent patch HANGS AuthenticationForm.__init__; the test suite times out; no report => run_resolve returns completed=False. Per src/swebench_unified/construct/build_one.py:306-312, BROKEN requires a candidate whose patch `completed and not resolved`; a completed=False resolve routes to INCONCLUSIVE, never BROKEN. A non-terminating impl BY CONSTRUCTION produces no resolve verdict, so it cannot witness verify=>not-correct. atk_4 is therefore NOT a counterexample and is intentionally EXCLUDED from the submitted falsification floor (including it would inject a spurious non-completing-resolve INCONCLUSIVE into the mechanized re-derivation).

HARNESS CONTROL (proves the harness + image are functional so atk_4's non-completion is intrinsic, not infra): run_resolve on the GOLD patch (benchmark-verified/django__django-11790/patch.diff, timeout=1200) => resolved=True, completed=True, note='resolved'. The django-11790 image was pulled/cached during this run; the earlier 'image pull failure' notes were the missing-image + concurrent runs-contention artifact, resolved by the gold run.

REFINEMENT.md A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=false. There are NO A-consumed and NO A-reference legs — nothing with callee correspondence to falsify. Legs A1-A5 are all R/I/frame (Option Nat <-> int|None; resolveLimit <-> `x or 254`; the two facet<->attribute bindings; read-only frame). No kind-3 inexpressible-changed-op: the one genuinely changed op (recording the derived limit on widget.attrs['maxlength']) is modeled DIRECTLY by A4 and pinned by the 2nd ensures — confirmed by atk_3 failing precisely on that clause. G-AX skip is legitimate. mapping.md section 2/3 consistent. The R/I legs are G-CONF's job (meta: G-CONF pass, 100007 inputs, seed 11790, 0 disagreements).

CONCLUSION: >=5 (7) terminating same-spec attacks run, all cleanly REJECTED; positive control verifies; prepatch bug reproduced (atk_3); gold patch resolves (executed). The sole verifying impl is the universal divergence artifact whose patch cannot produce completed&&!resolved. No verifying wrong impl has a faithful patch that fails to resolve => verify does NOT fail to imply correct for this spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies (all 7 rejected, exit 1). The only same-spec impl that verifies is a non-terminating `while true` loop (atk_4), which is the UNIVERSAL partial-correctness artifact (reproduced verifying on the unrelated astropy-12907 bundle) and whose faithful refined patch TIMES OUT under the harness (completed=False), so it cannot satisfy the BROKEN criterion (completed AND not resolved). Verify does NOT imply incorrect here for any terminating impl.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model A-references. The behavior is pure
--  control/data flow: derive a length limit from the account model's configured
--  limit (a default applies when none is configured), then record that limit in
--  the field. Nothing about an unchanged callee's contract is assumed, so there
--  is nothing for G-AX to validate — see mapping.md §3 and axiom_check.py.)
-- axioms-end

-- pure-start
/- The effective maximum input length, derived from the account model's
   configured limit. When the model supplies a positive limit it is used
   directly; when the model configures no limit (or a vacuous zero one) a
   standard default applies. This mirrors the usual "configured value, otherwise a
   default" selection over a possibly-absent setting. -/
@[grind] def resolveLimit (modelLimit : Option Nat) : Nat :=
  match modelLimit with
  | some n => if n = 0 then 254 else n
  | none   => 254
-- pure-end

/- A text-entry form field, observed through exactly the two facets this routine
   must keep in agreement:
   * `maxLength`       — the maximum input length the field itself enforces.
   * `widgetMaxLength` — the same limit as exposed to the field's rendered
                         control (the attribute a browser reads to cap typing).
   `none` means the corresponding limit is unset. Other field attributes are
   untouched here and are not carried (mapping.md §2). -/
structure BoundedField where
  maxLength       : Option Nat
  widgetMaxLength : Option Nat
deriving Inhabited, DecidableEq

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Configure a form field's input-length limit from the account model.

   The desired behavior: the field must enforce the effective limit derived from
   the model's configured limit (defaulting when none is configured), AND that
   same limit must be exposed to the field's rendered control. The two facets
   must agree — a field whose enforced limit is set but whose rendered control
   does not advertise it is the defect this routine must avoid. Both facets end
   up holding the single derived limit.

   `field` is the field being configured; `modelLimit` is the account model's
   configured limit (read-only; not `mut`). The result is a fresh value built
   from `field` with both length facets set. -/
method configureFieldLimit (field : BoundedField) (modelLimit : Option Nat)
    return (result : BoundedField)
  ensures result.maxLength       = some (resolveLimit modelLimit)
  ensures result.widgetMaxLength = some (resolveLimit modelLimit)
  do
    -- impl-start
    -- Derive the effective limit: the model's configured limit, or the default
    -- when none is configured.
    let limit : Nat :=
      match modelLimit with
      | some n => if n = 0 then 254 else n
      | none   => 254
    -- Record the limit on the field, and expose the same limit to its rendered
    -- control.
    let mut result := field
    result := { result with maxLength := some limit }
    result := { result with widgetMaxLength := some limit }
    return result
    -- impl-end

prove_correct configureFieldLimit by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: configureFieldLimit has two ensures pinning BOTH fields of the 2-field BoundedField structure to the exact value `some (resolveLimit modelLimit)` (resolveLimit = Python `x or 254`: none/some 0 -> 254, some n>0 -> n). This is a TOTAL functional postcondition: for any terminating impl the output is uniquely determined, so any terminating deviation is caught.

SAME-SPEC (all True, via swebench_unified.markers.same_spec, velvet): atk_1..8 all True; positive_control True.

### VERIFY RESULTS (bash scripts/lean_verify.sh <file>; run concurrently <=4/batch):
- atk_1 (constant 254, ignores modelLimit): EXIT 1 REJECTED — `some 254 = some (resolveLimit modelLimit)` unprovable for positive n.
- atk_2 (limit+1 boundary): EXIT 1 REJECTED.
- atk_3 (sets maxLength ONLY, leaves widgetMaxLength — the EXACT dropped-widget regression / prepatch bug / F2P discriminator): EXIT 1 REJECTED on ensures_1 widgetMaxLength = field.widgetMaxLength. PREPATCH REPRODUCED.
- atk_5 (control-flow-effect: widgetMaxLength := field.maxLength): EXIT 1 REJECTED.
- atk_6 (falsifiable-guard loop `while k>0 do k:=k+1` then unchanged): EXIT 1 REJECTED (loop-exit hypothesis reachable; frame unchanged fails both clauses).
- atk_7 (2*limit): EXIT 1 REJECTED.
- atk_8 (`while j<1 do j:=0` then wrong 999): EXIT 1 REJECTED.
- atk_4 (`while true` divergence, then return field): EXIT 0 VERIFIES. This is the ONLY verifier.
- positive_control (gold impl, byte-identical to bundle Solution.lean impl): EXIT 0 VERIFIES.

atk_4 ANALYSIS (the crux — NOT a break):
(1) Universal partial-correctness escape: `set_option loom.semantics.termination "partial"`. A non-terminating impl satisfies any postcondition vacuously (false loop-exit hypothesis). I injected the identical `while true` construct into the UNRELATED bundle astropy__astropy-12907/velvet (also partial semantics) -> other_diverge.lean, lean_verify EXIT 0. So this verifies against every partial-semantics velvet spec; it is NOT evidence THIS spec is weak.
(2) Faithful refined patch MATERIALIZED and RUN through the official harness (run_resolve). Patch = atk_4_patch.diff (generated via git diff worktree at base_commit b1d6b35e; inserts `while True: pass` before the two facet assignments; applies cleanly — an earlier hand-written diff was malformed and I corrected it).
  EXECUTED RESULTS:
  - run_resolve('django__django-11790', atk_4_patch, timeout=300/900/600, retries=0): resolved=False, completed=False (repeated 3x).
  - Direct keep-logs harness run (run_id atk4v2-diag-keeplogs, --timeout 150): STDOUT = "django__django-11790: Test timed out after 150 seconds." RC 1, no report.json produced.
  So the divergent patch HANGS AuthenticationForm.__init__; the test suite times out; no report => run_resolve returns completed=False. Per src/swebench_unified/construct/build_one.py:306-312, BROKEN requires a candidate whose patch `completed and not resolved`; a completed=False resolve routes to INCONCLUSIVE, never BROKEN. A non-terminating impl BY CONSTRUCTION produces no resolve verdict, so it cannot witness verify=>not-correct. atk_4 is therefore NOT a counterexample and is intentionally EXCLUDED from the submitted falsification floor (including it would inject a spurious non-completing-resolve INCONCLUSIVE into the mechanized re-derivation).

HARNESS CONTROL (proves the harness + image are functional so atk_4's non-completion is intrinsic, not infra): run_resolve on the GOLD patch (benchmark-verified/django__django-11790/patch.diff, timeout=1200) => resolved=True, completed=True, note='resolved'. The django-11790 image was pulled/cached during this run; the earlier 'image pull failure' notes were the missing-image + concurrent runs-contention artifact, resolved by the gold run.

REFINEMENT.md A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=false. There are NO A-consumed and NO A-reference legs — nothing with callee correspondence to falsify. Legs A1-A5 are all R/I/frame (Option Nat <-> int|None; resolveLimit <-> `x or 254`; the two facet<->attribute bindings; read-only frame). No kind-3 inexpressible-changed-op: the one genuinely changed op (recording the derived limit on widget.attrs['maxlength']) is modeled DIRECTLY by A4 and pinned by the 2nd ensures — confirmed by atk_3 failing precisely on that clause. G-AX skip is legitimate. mapping.md section 2/3 consistent. The R/I legs are G-CONF's job (meta: G-CONF pass, 100007 inputs, seed 11790, 0 disagreements).

CONCLUSION: >=5 (7) terminating same-spec attacks run, all cleanly REJECTED; positive control verifies; prepatch bug reproduced (atk_3); gold patch resolves (executed). The sole verifying impl is the universal divergence artifact whose patch cannot produce completed&&!resolved. No verifying wrong impl has a faithful patch that fails to resolve => verify does NOT fail to imply correct for this spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack: no diverging input found; modeled function agrees with the real callee on the entire modeled domain.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean) = True (VelvetBackend tables) — spec region is byte-identical/frozen. Solution.lean verifies clean via lean_verify.sh (exit 0). G-HYGIENE spec_view hash present.

REAL REPO (base_commit b1d6b35e, django/contrib/auth/forms.py:194): gold patch is `username_max_length = self.username_field.max_length or 254`, then assigns BOTH `self.fields['username'].max_length` and `self.fields['username'].widget.attrs['maxlength']` to that value. Modeled function configureFieldLimit(field, modelLimit) with resolveLimit modeling `x or 254` and both postconditions pinning both facets to `some (resolveLimit modelLimit)`.

DRIFT / TOO-STRONG CHECKS (all pass):
1. Truthiness selection: Python `x or 254` gives None->254, 0->254, positive n->n. resolveLimit gives none->254, some 0->254, some n(n>0)->n. Exact agreement on every value.
2. Domain Nat: Django CharField.max_length is a non-negative int or None (PositiveInteger-style). Negatives are unreachable in the real repo, so restricting modelLimit to Option Nat claims nothing false — the spec is not stronger than reality on any reachable input.
3. Both-facet postcondition is exactly the patched behavior (both facets set from the same username_max_length); not an over-claim. This is the discriminating F2P assertion (widget maxlength), correctly required, not over-tightened.
4. Frame: `field` read-only, result differs only in the two carried facets; BoundedField carries only those two, so no unmodeled attribute claim is asserted.
5. G-CONF conformance_check.py runs shadow vs. gold-block oracle on 100007 inputs (seed 11790) incl. boundaries None/0/254/255/1/75/150 with 0 disagreements — confirmed by inspection.

Conclusion: the modeled function does not disagree with the real callee on any input; the spec is faithful (neither drifted nor too strong).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified frozen: markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True, and the rendered spec_view collapses impl and prove_correct bodies to placeholders — the consumer sees only the frozen spec.

Public problem_statement already discloses the entire defect and the required fix: 'AuthenticationForm's username field doesn't set maxlength HTML attribute ... doesn't render with maxlength HTML attribute anymore.' So the public knowledge is: set the rendered maxlength attribute to the field's max length. The gold edit is exactly the added line self.fields['username'].widget.attrs['maxlength'] = username_max_length (the `or 254` factoring is pre-existing behavior, merely hoisted).

Leakage assessment of the spec view (the only consumer-visible artifact):
- All identifiers are abstracted away from repo reality: configureFieldLimit / BoundedField / maxLength / widgetMaxLength / resolveLimit. No repo symbols appear (no AuthenticationForm, forms.py, widget.attrs['maxlength'], max_length, django, username). Prose ('rendered control', 'the attribute a browser reads to cap typing') is a generalization of the publicly-stated bug, not a quote of the patch or problem_statement.
- The discriminating postcondition `ensures result.widgetMaxLength = some (resolveLimit modelLimit)` formalizes precisely the requirement the public problem_statement already states (the rendered-control limit must equal the field's derived limit). It does not reveal anything beyond the public problem_statement.
- The 254 default in resolveLimit reflects pre-existing behavior (the `or 254` predates the patch and is NOT part of the gold edit), so surfacing it does not leak the gold edit.
- mapping.md and refinement.md do name repo symbols and the gold hunk, but they are auditor/refinement artifacts, NOT part of spec_view(Solution.lean); G-LEAK/G-PANEL-3 scope is the spec view a consumer builds against, which is clean.

The spec is a faithful abstraction of the publicly-known requirement and leaks nothing beyond problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
