# P2 adversarial audit — django__django-15629

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
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong-VALUE impl verifies. Both method specs pin the output totally with NO preconditions: foreignReferenceColumnDesc has `ensures out = referencingColumnDesc refType refCheck targetCollation` (+ field ensures out.collation/sqlType/check), and shouldReissueReferences has `ensures out = referencesNeedReissue targetUnique oldType newType oldCollation newCollation` (+ the collation-only-change implication). Any TERMINATING impl returning a value different from the pure spec function on any input leaves an unsolved postcondition goal in prove_correct — confirmed for all 9 value attacks (exit 1). The only impls that verify are non-terminating (partial-correctness divergence) artifacts, which produce no completed-but-unresolved faithful patch (see notes).
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -82,7 +82,7 @@
   ensures out.check = refCheck
   do
     -- impl-start
-    return { sqlType := refType, check := refCheck, collation := targetCollation }
+    return { sqlType := refType, check := refCheck, collation := none }
     -- impl-end
 
 prove_correct foreignReferenceColumnDesc by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -103,7 +103,7 @@
   ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
   do
     -- impl-start
-    return targetUnique && ((oldType != newType) || (oldCollation != newCollation))
+    return targetUnique && (oldType != newType)
     -- impl-end
 
 prove_correct shouldReissueReferences by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -82,7 +82,7 @@
   ensures out.check = refCheck
   do
     -- impl-start
-    return { sqlType := refType, check := refCheck, collation := targetCollation }
+    return { sqlType := refType, check := refCheck, collation := (if targetCollation = some "und-x-icu" then none else targetCollation) }
     -- impl-end
 
 prove_correct foreignReferenceColumnDesc by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -103,7 +103,7 @@
   ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
   do
     -- impl-start
-    return targetUnique && ((oldType != newType) || (oldCollation != newCollation))
+    return targetUnique && ((oldType != newType) && (oldCollation != newCollation))
     -- impl-end
 
 prove_correct shouldReissueReferences by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -103,7 +103,7 @@
   ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
   do
     -- impl-start
-    return targetUnique && ((oldType != newType) || (oldCollation != newCollation))
+    return (oldType != newType) || (oldCollation != newCollation)
     -- impl-end
 
 prove_correct shouldReissueReferences by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -103,7 +103,7 @@
   ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
   do
     -- impl-start
-    return targetUnique && ((oldType != newType) || (oldCollation != newCollation))
+    return targetUnique
     -- impl-end
 
 prove_correct shouldReissueReferences by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -82,7 +82,7 @@
   ensures out.check = refCheck
   do
     -- impl-start
-    return { sqlType := refType, check := refCheck, collation := targetCollation }
+    return { sqlType := refType, check := refCheck, collation := (if targetCollation = some "" then none else targetCollation) }
     -- impl-end
 
 prove_correct foreignReferenceColumnDesc by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -82,7 +82,7 @@
   ensures out.check = refCheck
   do
     -- impl-start
-    return { sqlType := refType, check := refCheck, collation := targetCollation }
+    return { sqlType := refType, check := refCheck, collation := refCheck }
     -- impl-end
 
 prove_correct foreignReferenceColumnDesc by
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
 -- (No axiomatized callees and no deep-model references. Both modeled operations
@@ -103,7 +103,7 @@
   ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
   do
     -- impl-start
-    return targetUnique && ((oldType != newType) || (oldCollation != newCollation))
+    return targetUnique && ((oldType != newType) || (oldCollation == newCollation))
     -- impl-end
 
 prove_correct shouldReissueReferences by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model references. Both modeled operations
--  are pure data-flow over their inputs: the column descriptor a referencing
--  field reports, and a boolean decision over already-computed descriptors.
--  The values they consume — a field's own column type/check, the column
--  descriptor of the field it points to, and the before/after descriptors of a
--  field being altered — are taken as plain inputs (abstracted, mapping.md §2),
--  so there is nothing to consume as an axiom and nothing to validate against an
--  outside callee.)
-- axioms-end

-- pure-start
/- The portion of a column descriptor this construction observes. A field is
   asked to describe the column that backs it:
   * `sqlType`  — the column's storage type (e.g. a varchar of some width);
   * `check`    — an optional column check expression (`none` if the field
                  imposes none);
   * `collation`— the optional sort/equality collation for the column
                  (`none` when the column carries no explicit collation).
   The collation is the field the rest of this construction is about: two
   columns joined by a reference must agree on it. -/
structure ColumnDesc where
  sqlType   : String
  check     : Option String
  collation : Option String
deriving DecidableEq, Inhabited, Repr

/- The column descriptor a *referencing* field reports. A referencing field
   does not own an independent collation: the column it stores must line up with
   the column it points at, so it adopts the referenced column's collation while
   keeping its own storage type and check. `refType`/`refCheck` are the
   referencing field's own type and check; `targetCollation` is the collation of
   the column it references. -/
def referencingColumnDesc
    (refType : String) (refCheck : Option String)
    (targetCollation : Option String) : ColumnDesc :=
  { sqlType := refType, check := refCheck, collation := targetCollation }

/- Whether altering a referenced column forces the columns that point at it to
   be reissued. A reference must be reissued exactly when the referenced column
   can be a reference target (it is unique) AND something a referencing column
   mirrors actually changes — either its storage type or its collation. Earlier
   only a storage-type difference counted; a collation-only difference must
   count too, since a referencing column mirrors the collation as well.
   `targetUnique` says the referenced column is unique (so references may point
   at it); the `old…`/`new…` pairs are the referenced column's descriptor before
   and after the alteration. -/
def referencesNeedReissue
    (targetUnique : Bool)
    (oldType newType : String)
    (oldCollation newCollation : Option String) : Bool :=
  targetUnique && ((oldType != newType) || (oldCollation != newCollation))
-- pure-end

-- pre-conditions-start
-- (preconditions are the inline `require` clauses on each `method` below)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- The column descriptor reported by a referencing field. Read-only inputs (no
   `mut`): the descriptor is derived, nothing is altered. The reported collation
   is exactly the referenced column's collation (in particular, when the
   referenced column carries a collation the reference reports the SAME one, not
   the absence of a collation). -/
method foreignReferenceColumnDesc
    (refType : String) (refCheck : Option String)
    (targetCollation : Option String) return (out : ColumnDesc)
  ensures out = referencingColumnDesc refType refCheck targetCollation
  ensures out.collation = targetCollation
  ensures out.sqlType = refType
  ensures out.check = refCheck
  do
    -- impl-start
    return { sqlType := refType, check := refCheck, collation := targetCollation }
    -- impl-end

prove_correct foreignReferenceColumnDesc by
  loom_solve
  simp_all [referencingColumnDesc]

/- The decision whether references to an altered column must be reissued.
   Read-only inputs (no `mut`). The result is true exactly when the referenced
   column is unique and either its storage type or its collation differs between
   the before and after descriptors — so a collation-only change is sufficient
   to force reissue. -/
method shouldReissueReferences
    (targetUnique : Bool)
    (oldType : String) (newType : String)
    (oldCollation : Option String) (newCollation : Option String) return (out : Bool)
  ensures out = referencesNeedReissue targetUnique oldType newType oldCollation newCollation
  ensures out = true → (targetUnique = true ∧ ((oldType != newType) = true ∨ (oldCollation != newCollation) = true))
  ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
  do
    -- impl-start
    return targetUnique && ((oldType != newType) || (oldCollation != newCollation))
    -- impl-end

prove_correct shouldReissueReferences by
  loom_solve
  simp_all [referencesNeedReissue]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 value attacks + 2 divergence artifacts + positive control confirmed True via swebench_unified.markers.same_spec (velvet). pos_control.lean is a byte-identical copy of gold Solution.lean and is distinct from every attack file. Attacks edit ONLY the impl region(s); divergence artifacts additionally trim the elided prove_correct body (still same_spec True, since prove_correct bodies are elided from the spec view).

pos_control.lean: exit 0 (VERIFIES) — positive control good.
- atk_1.lean (prepatch bug #1: method1 collation:=none): exit 1 (rejected). PREPATCH REPRODUCED.
- atk_2.lean (prepatch bug #2: method2 targetUnique && (oldType!=newType), collation-blind): exit 1 (rejected). PREPATCH REPRODUCED.
- atk_3.lean (partial-domain/boundary: method1 collapses some "und-x-icu" collation to none): exit 1 (rejected).
- atk_4.lean (control-flow/wrong-op: method2 && instead of || — reissue only when BOTH type AND collation differ): exit 1 (rejected).
- atk_5.lean (control-flow: method2 drops targetUnique guard): exit 1 (rejected).
- atk_6.lean (ungrounded-oracle echo: method2 returns targetUnique alone): exit 1 (rejected).
- atk_7.lean (partial-domain/boundary: method1 some "" collation -> none): exit 1 (rejected).
- atk_8.lean (boundary/field-swap: method1 collation:=refCheck — wrong field): exit 1 (rejected).
- atk_9.lean (ungrounded-oracle: method2 collation subclause negated == instead of !=): exit 1 (rejected).
All 9 VALUE attacks REJECTED. No value candidate => no faithful patch required for those; patches={} by construction (resolve step is only mandated for a VERIFYING same-spec attack).

DIVERGENCE ARTIFACTS — VERIFIED AND RESOLVE-RUN (this is the mandated step-2 execution, not speculation):
- atk_div1.lean / atk_div2.lean: same_spec True, exit 0 (VERIFY) via a structured `while i != 0 invariant i = 1 do i := 1` loop (no `decreasing`) preceding a WRONG return value; loom's partial-correctness WP makes the never-satisfied exit condition vacuous.
- Materialized faithful patches: atk_div1.patch.diff (infinite loop inside ForeignKey.db_parameters, the callee mapped to method1) and atk_div2.patch.diff (infinite loop inside the sqlite3 _alter_field rebuild predicate, the callee mapped to method2). Both apply cleanly (`git apply --check` against base 694cf458... reconstructed clean files: APPLIES CLEAN for gold, atk_div1, atk_div2).
- GOLD BASELINE resolve (cmd: run_resolve.py gold.patch.diff): resolved=true, completed=true, 175.2s — harness + image confirmed working.
- atk_div1 resolve (run_resolve.py atk_div1.patch.diff 600): resolved=false, completed=FALSE, 760.5s, note 'no report ... harness error or image pull failure' (== harness timeout on the hung test; NOT an image issue, since gold resolved through the same image).
- atk_div2 resolve (run_resolve.py atk_div2.patch.diff 600): resolved=false, completed=FALSE, 754.3s, same timeout signature.
=> Both verifying wrong impls yield completed=False. In build_one.py:_derive_audit_verdict, only `r.completed and not r.resolved` (lines 306-309) is BROKEN; `not r.completed` (line 310) routes to inconclusive_hits. run_resolve returns immediately on `not last.completed` (no retries). So NEITHER divergence artifact can produce a `verifies-but-faithful-patch-completes-and-does-not-resolve` witness. They are therefore NOT submitted as attacks (submitting them would make them same-spec-verifying candidates whose resolve is incomplete => INCONCLUSIVE-by-timeout, not a real break). This matches the recorded G-PANEL-2 (faithfulness) 'no divergence found' scope; divergence vacuity is universal to every loom.semantics.termination "partial" bundle, not a refinement-fidelity defect of THIS spec.

REFINEMENT.MD LEG AUDIT (step 3): axioms region (Solution.lean:9-18) is prose only — no `axiom` decls, no deep-model references (verified). §A legs A1-A3 = R (FK own type/check + target collation abstracted as plain inputs per mapping.md §2 bijections), A4 = I (post-patch dict literal, verbatim key placement). §B legs B1-B3 = R (unique flag, type strings, before/after collations), B4 = I (boolean and/or/!= map verbatim to &&/||/!=). §C asserts no kind-3 and no A-tagged ops — consistent with the empty axioms region and mapping.md §1. There are NO A-legs whose correspondence to a real callee must be validated. Modeled sites (related.py:1182 ForeignKey.db_parameters -> referencingColumnDesc; sqlite3/schema.py:458 rebuild predicate -> referencesNeedReissue) match the pure specs. Inert sites (base/schema.py, oracle/features.py) correctly excluded as non-observable on the sqlite3 harness backend (sqlite fully overrides _alter_field; oracle hunk is test-skip bookkeeping). No kind-3 leg.

CONCLUSION: >=5 distinct value-based wrong impls (9 submitted, incl. both prepatch bugs) all fail to verify; positive control verifies; refinement.md has no A-leg or kind-3 defect; the only verifying wrong impls are divergence artifacts whose materialized faithful patches were RUN and returned completed=False (timeout), never the completed-and-unresolved BROKEN path. verify(value) => correct is upheld. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong-VALUE impl verifies. Both method specs pin the output totally with NO preconditions: foreignReferenceColumnDesc has `ensures out = referencingColumnDesc refType refCheck targetCollation` (+ field ensures out.collation/sqlType/check), and shouldReissueReferences has `ensures out = referencesNeedReissue targetUnique oldType newType oldCollation newCollation` (+ the collation-only-change implication). Any TERMINATING impl returning a value different from the pure spec function on any input leaves an unsolved postcondition goal in prove_correct — confirmed for all 9 value attacks (exit 1). The only impls that verify are non-terminating (partial-correctness divergence) artifacts, which produce no completed-but-unresolved faithful patch (see notes).
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model references. Both modeled operations
--  are pure data-flow over their inputs: the column descriptor a referencing
--  field reports, and a boolean decision over already-computed descriptors.
--  The values they consume — a field's own column type/check, the column
--  descriptor of the field it points to, and the before/after descriptors of a
--  field being altered — are taken as plain inputs (abstracted, mapping.md §2),
--  so there is nothing to consume as an axiom and nothing to validate against an
--  outside callee.)
-- axioms-end

-- pure-start
/- The portion of a column descriptor this construction observes. A field is
   asked to describe the column that backs it:
   * `sqlType`  — the column's storage type (e.g. a varchar of some width);
   * `check`    — an optional column check expression (`none` if the field
                  imposes none);
   * `collation`— the optional sort/equality collation for the column
                  (`none` when the column carries no explicit collation).
   The collation is the field the rest of this construction is about: two
   columns joined by a reference must agree on it. -/
structure ColumnDesc where
  sqlType   : String
  check     : Option String
  collation : Option String
deriving DecidableEq, Inhabited, Repr

/- The column descriptor a *referencing* field reports. A referencing field
   does not own an independent collation: the column it stores must line up with
   the column it points at, so it adopts the referenced column's collation while
   keeping its own storage type and check. `refType`/`refCheck` are the
   referencing field's own type and check; `targetCollation` is the collation of
   the column it references. -/
def referencingColumnDesc
    (refType : String) (refCheck : Option String)
    (targetCollation : Option String) : ColumnDesc :=
  { sqlType := refType, check := refCheck, collation := targetCollation }

/- Whether altering a referenced column forces the columns that point at it to
   be reissued. A reference must be reissued exactly when the referenced column
   can be a reference target (it is unique) AND something a referencing column
   mirrors actually changes — either its storage type or its collation. Earlier
   only a storage-type difference counted; a collation-only difference must
   count too, since a referencing column mirrors the collation as well.
   `targetUnique` says the referenced column is unique (so references may point
   at it); the `old…`/`new…` pairs are the referenced column's descriptor before
   and after the alteration. -/
def referencesNeedReissue
    (targetUnique : Bool)
    (oldType newType : String)
    (oldCollation newCollation : Option String) : Bool :=
  targetUnique && ((oldType != newType) || (oldCollation != newCollation))
-- pure-end

-- pre-conditions-start
-- (preconditions are the inline `require` clauses on each `method` below)
-- pre-conditions-end

-- post-conditions-start
-- (postconditions are the inline `ensures` clauses on each `method` below)
-- post-conditions-end

/- The column descriptor reported by a referencing field. Read-only inputs (no
   `mut`): the descriptor is derived, nothing is altered. The reported collation
   is exactly the referenced column's collation (in particular, when the
   referenced column carries a collation the reference reports the SAME one, not
   the absence of a collation). -/
method foreignReferenceColumnDesc
    (refType : String) (refCheck : Option String)
    (targetCollation : Option String) return (out : ColumnDesc)
  ensures out = referencingColumnDesc refType refCheck targetCollation
  ensures out.collation = targetCollation
  ensures out.sqlType = refType
  ensures out.check = refCheck
  do
    -- impl-start
    return { sqlType := refType, check := refCheck, collation := targetCollation }
    -- impl-end

prove_correct foreignReferenceColumnDesc by
  loom_solve
  simp_all [referencingColumnDesc]

/- The decision whether references to an altered column must be reissued.
   Read-only inputs (no `mut`). The result is true exactly when the referenced
   column is unique and either its storage type or its collation differs between
   the before and after descriptors — so a collation-only change is sufficient
   to force reissue. -/
method shouldReissueReferences
    (targetUnique : Bool)
    (oldType : String) (newType : String)
    (oldCollation : Option String) (newCollation : Option String) return (out : Bool)
  ensures out = referencesNeedReissue targetUnique oldType newType oldCollation newCollation
  ensures out = true → (targetUnique = true ∧ ((oldType != newType) = true ∨ (oldCollation != newCollation) = true))
  ensures (targetUnique = true ∧ oldType = newType ∧ oldCollation ≠ newCollation) → out = true
  do
    -- impl-start
    return targetUnique && ((oldType != newType) || (oldCollation != newCollation))
    -- impl-end

prove_correct shouldReissueReferences by
  loom_solve
  simp_all [referencesNeedReissue]
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 9 value attacks + 2 divergence artifacts + positive control confirmed True via swebench_unified.markers.same_spec (velvet). pos_control.lean is a byte-identical copy of gold Solution.lean and is distinct from every attack file. Attacks edit ONLY the impl region(s); divergence artifacts additionally trim the elided prove_correct body (still same_spec True, since prove_correct bodies are elided from the spec view).

pos_control.lean: exit 0 (VERIFIES) — positive control good.
- atk_1.lean (prepatch bug #1: method1 collation:=none): exit 1 (rejected). PREPATCH REPRODUCED.
- atk_2.lean (prepatch bug #2: method2 targetUnique && (oldType!=newType), collation-blind): exit 1 (rejected). PREPATCH REPRODUCED.
- atk_3.lean (partial-domain/boundary: method1 collapses some "und-x-icu" collation to none): exit 1 (rejected).
- atk_4.lean (control-flow/wrong-op: method2 && instead of || — reissue only when BOTH type AND collation differ): exit 1 (rejected).
- atk_5.lean (control-flow: method2 drops targetUnique guard): exit 1 (rejected).
- atk_6.lean (ungrounded-oracle echo: method2 returns targetUnique alone): exit 1 (rejected).
- atk_7.lean (partial-domain/boundary: method1 some "" collation -> none): exit 1 (rejected).
- atk_8.lean (boundary/field-swap: method1 collation:=refCheck — wrong field): exit 1 (rejected).
- atk_9.lean (ungrounded-oracle: method2 collation subclause negated == instead of !=): exit 1 (rejected).
All 9 VALUE attacks REJECTED. No value candidate => no faithful patch required for those; patches={} by construction (resolve step is only mandated for a VERIFYING same-spec attack).

DIVERGENCE ARTIFACTS — VERIFIED AND RESOLVE-RUN (this is the mandated step-2 execution, not speculation):
- atk_div1.lean / atk_div2.lean: same_spec True, exit 0 (VERIFY) via a structured `while i != 0 invariant i = 1 do i := 1` loop (no `decreasing`) preceding a WRONG return value; loom's partial-correctness WP makes the never-satisfied exit condition vacuous.
- Materialized faithful patches: atk_div1.patch.diff (infinite loop inside ForeignKey.db_parameters, the callee mapped to method1) and atk_div2.patch.diff (infinite loop inside the sqlite3 _alter_field rebuild predicate, the callee mapped to method2). Both apply cleanly (`git apply --check` against base 694cf458... reconstructed clean files: APPLIES CLEAN for gold, atk_div1, atk_div2).
- GOLD BASELINE resolve (cmd: run_resolve.py gold.patch.diff): resolved=true, completed=true, 175.2s — harness + image confirmed working.
- atk_div1 resolve (run_resolve.py atk_div1.patch.diff 600): resolved=false, completed=FALSE, 760.5s, note 'no report ... harness error or image pull failure' (== harness timeout on the hung test; NOT an image issue, since gold resolved through the same image).
- atk_div2 resolve (run_resolve.py atk_div2.patch.diff 600): resolved=false, completed=FALSE, 754.3s, same timeout signature.
=> Both verifying wrong impls yield completed=False. In build_one.py:_derive_audit_verdict, only `r.completed and not r.resolved` (lines 306-309) is BROKEN; `not r.completed` (line 310) routes to inconclusive_hits. run_resolve returns immediately on `not last.completed` (no retries). So NEITHER divergence artifact can produce a `verifies-but-faithful-patch-completes-and-does-not-resolve` witness. They are therefore NOT submitted as attacks (submitting them would make them same-spec-verifying candidates whose resolve is incomplete => INCONCLUSIVE-by-timeout, not a real break). This matches the recorded G-PANEL-2 (faithfulness) 'no divergence found' scope; divergence vacuity is universal to every loom.semantics.termination "partial" bundle, not a refinement-fidelity defect of THIS spec.

REFINEMENT.MD LEG AUDIT (step 3): axioms region (Solution.lean:9-18) is prose only — no `axiom` decls, no deep-model references (verified). §A legs A1-A3 = R (FK own type/check + target collation abstracted as plain inputs per mapping.md §2 bijections), A4 = I (post-patch dict literal, verbatim key placement). §B legs B1-B3 = R (unique flag, type strings, before/after collations), B4 = I (boolean and/or/!= map verbatim to &&/||/!=). §C asserts no kind-3 and no A-tagged ops — consistent with the empty axioms region and mapping.md §1. There are NO A-legs whose correspondence to a real callee must be validated. Modeled sites (related.py:1182 ForeignKey.db_parameters -> referencingColumnDesc; sqlite3/schema.py:458 rebuild predicate -> referencesNeedReissue) match the pure specs. Inert sites (base/schema.py, oracle/features.py) correctly excluded as non-observable on the sqlite3 harness backend (sqlite fully overrides _alter_field; oracle hunk is test-skip bookkeeping). No kind-3 leg.

CONCLUSION: >=5 distinct value-based wrong impls (9 submitted, incl. both prepatch bugs) all fail to verify; positive control verifies; refinement.md has no A-leg or kind-3 defect; the only verifying wrong impls are divergence artifacts whose materialized faithful patches were RUN and returned completed=False (timeout), never the completed-and-unresolved BROKEN path. verify(value) => correct is upheld. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for django__django-15629 velvet bundle. Two modeled functions, both pure data-flow with no axiomatized callees.

1) foreignReferenceColumnDesc / referencingColumnDesc models ForeignKey.db_parameters (related.py:1182). Verified against the base_commit worktree (HEAD 694cf458f1, patched): the post-patch override returns exactly {"type": db_type, "check": db_check, "collation": target_db_parameters.get("collation")}. ColumnDesc has exactly the matching 3 fields; the record construction is byte-for-byte the same mapping, refType/refCheck abstracted as unchanged inputs, targetCollation = target's collation with None<->none / present-string<->some s. No stronger-than-reality obligation: ensures out.collation=targetCollation, out.sqlType=refType, out.check=refCheck all hold of the real dict on every input.

2) shouldReissueReferences / referencesNeedReissue models the sqlite3 _alter_field rebuild predicate (sqlite3/schema.py:458). Worktree confirms: `if new_field.unique and (old_type != new_type or old_collation != new_collation)`. Lean: targetUnique && ((oldType != newType) || (oldCollation != newCollation)) -- verbatim boolean transliteration; BEq on String and Option String is total and agrees with Python != on the abstracted domain (including empty-string as a distinct present value). The extra ensures clauses (implication both directions incl. collation-only => reissue) are consequences of this exact boolean, so no over-strengthening.

spec-view same_spec: Solution vs Solution_prepatch differs on the collation key (prepatch collation:=none) and Solution vs Solution_prepatch_2 differs on the reissue predicate (prepatch2 drops the collation clause) -- G-DIFF discriminating content is present and real, matching the two gold hunks.

Inert sites (base/schema.py, oracle/features.py) are correctly excluded: sqlite fully overrides _alter_field so base collation handling is dead on the harness backend, and the oracle hunk is test-skip bookkeeping -- neither is sqlite-observable, so omitting them does not make verify=>resolved unsound. lean_verify.sh on Solution.lean: exit 0. No input found where the modeled functions disagree with the real repo callees. Spec is faithful and not too strong.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over the velvet spec_view) passes clean: no diff markers, no gold-patch line reproduced (checked ≥8-char normalized changed lines), no patched file path/module (related.py, sqlite3/schema.py, base/schema.py, oracle/features.py), no narration tokens, and no spec-view identifier or comment echoing a distinctive patched symbol (changed symbols: DatabaseFeatures, alter_field, db_type — none embedded in referencingColumnDesc/shouldReissueReferences/ColumnDesc/sqlType/targetCollation, none named in comments). Repo-specific names (db_parameters, _alter_field, target_field, new_field.unique, COLLATE) never appear in the spec view — the model is abstracted to a ColumnDesc record and a boolean predicate. same_spec holds against both Solution_prepatch.lean and Solution_prepatch_2.lean (spec region byte-identical), so discriminators live in ensures/pure spec content, which is legitimate. No RELAXED_LEAKAGE.md and relaxed_leakage flag is unset; meta records G-LEAK/G-PANEL-3 pass. Semantic check: the only behavior-describing comment ('Earlier only a storage-type difference counted; a collation-only difference must count too') states the abstract requirement that a collation-only change forces referencing columns to be reissued — this is already fully disclosed by the public problem_statement, which explicitly shows the referencing MODIFY must carry the matching COLLATE and that mismatched pk/fk collation causes the ADD CONSTRAINT failure. Nothing in the spec view leaks the gold edit beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
