# P2 adversarial audit — django__django-15561

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `ensures out = schemaAlterationNeeded a b` totally pins the output to a deterministic pure function of (a,b), so every verifying same-spec impl is extensionally equal to schemaAlterationNeeded, which correctly ignores FieldDef.choices (matching the gold end-state). No verifying wrong impl exists.
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -63,7 +63,8 @@
   do
     -- impl-start
     return (decide (a.quotedColumn ≠ b.quotedColumn) ||
-      decide (a.schemaIdentity ≠ b.schemaIdentity))
+      decide (a.schemaIdentity ≠ b.schemaIdentity) ||
+      decide (a.choices ≠ b.choices))
     -- impl-end
 
 prove_correct decideSchemaAlteration by
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -62,8 +62,7 @@
   ensures out = schemaAlterationNeeded a b
   do
     -- impl-start
-    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
-      decide (a.schemaIdentity ≠ b.schemaIdentity))
+    return true
     -- impl-end
 
 prove_correct decideSchemaAlteration by
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -62,8 +62,7 @@
   ensures out = schemaAlterationNeeded a b
   do
     -- impl-start
-    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
-      decide (a.schemaIdentity ≠ b.schemaIdentity))
+    return (decide (a.quotedColumn ≠ b.quotedColumn))
     -- impl-end
 
 prove_correct decideSchemaAlteration by
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -62,8 +62,12 @@
   ensures out = schemaAlterationNeeded a b
   do
     -- impl-start
-    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
-      decide (a.schemaIdentity ≠ b.schemaIdentity))
+    if a.quotedColumn ≠ b.quotedColumn then
+      return true
+    else if a.schemaIdentity ≠ b.schemaIdentity then
+      return true
+    else
+      return false
     -- impl-end
 
 prove_correct decideSchemaAlteration by
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -62,8 +62,7 @@
   ensures out = schemaAlterationNeeded a b
   do
     -- impl-start
-    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
-      decide (a.schemaIdentity ≠ b.schemaIdentity))
+    return (schemaAlterationNeeded a b)
     -- impl-end
 
 prove_correct decideSchemaAlteration by
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -62,8 +62,8 @@
   ensures out = schemaAlterationNeeded a b
   do
     -- impl-start
-    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
-      decide (a.schemaIdentity ≠ b.schemaIdentity))
+    return (! (decide (a.quotedColumn = b.quotedColumn) &&
+      decide (a.schemaIdentity = b.schemaIdentity)))
     -- impl-end
 
 prove_correct decideSchemaAlteration by
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -62,7 +62,7 @@
   ensures out = schemaAlterationNeeded a b
   do
     -- impl-start
-    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
+    return (decide (a.quotedColumn ≠ b.quotedColumn) &&
       decide (a.schemaIdentity ≠ b.schemaIdentity))
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
 /- No consumed axioms and no deep-model references. The decision the desired
@@ -62,8 +62,8 @@
   ensures out = schemaAlterationNeeded a b
   do
     -- impl-start
-    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
-      decide (a.schemaIdentity ≠ b.schemaIdentity))
+    return (decide (a.quotedColumn = b.quotedColumn) &&
+      decide (a.schemaIdentity = b.schemaIdentity))
     -- impl-end
 
 prove_correct decideSchemaAlteration by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The decision the desired
   behaviour concerns — whether replacing one field definition with another
   requires rewriting the stored database column — is modeled directly in the
   `pure` region (`schemaAlterationNeeded`) from observable components of the two
   definitions. The mechanism that projects a concrete field definition onto
   those observable components (its quoted column name, its schema-relevant
   identity, and its enumerated choices) is a stable, unchanged operation; it is a
   type refinement recorded in mapping.md and exercised against the real
   projection by G-CONF (conformance_check.py), not an axiom. Nothing is
   axiomatized. -/
-- axioms-end

-- pure-start
/- A field definition as observed when deciding whether replacing one field
   definition with another requires rewriting the stored database column.
   * `quotedColumn`   — the quoted name of the database column the field maps to.
   * `schemaIdentity` — the part of the field's reconstructable definition that
                        determines the column's database schema: its import path,
                        positional arguments, and the keyword arguments that
                        affect the column. Attributes that never influence the
                        column's schema are not part of it.
   * `choices`        — the field's enumerated choices. A presentation-only
                        attribute, carried separately so the decision can be
                        stated with explicit access to it. -/
structure FieldDef where
  quotedColumn   : String
  schemaIdentity : String
  choices        : String
  deriving DecidableEq, Inhabited

/- Whether replacing the field definition `a` with `b` requires rewriting the
   stored column. A rewrite is required exactly when the quoted column name
   changes or the schema-relevant identity changes. The enumerated `choices`
   attribute is presentation-only: a difference in `choices` alone never requires
   a rewrite, so it is not consulted here even though it is observable. -/
def schemaAlterationNeeded (a b : FieldDef) : Bool :=
  decide (a.quotedColumn ≠ b.quotedColumn) ||
    decide (a.schemaIdentity ≠ b.schemaIdentity)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether replacing the field definition `a` with `b` requires rewriting
   the stored database column. Both `a` and `b` are read-only — the decision
   mutates nothing (directive 5). A rewrite is required precisely when the quoted
   column name differs or the schema-relevant identity differs; a change confined
   to the presentation-only `choices` attribute requires no rewrite. -/
method decideSchemaAlteration (a : FieldDef) (b : FieldDef) return (out : Bool)
  ensures out = schemaAlterationNeeded a b
  do
    -- impl-start
    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
      decide (a.schemaIdentity ≠ b.schemaIdentity))
    -- impl-end

prove_correct decideSchemaAlteration by
  loom_solve
  simp_all [schemaAlterationNeeded]
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attacks + positive_control confirmed same_spec==True via swebench_unified.markers.same_spec (velvet). Verified concurrently (<=4) via scripts/lean_verify.sh <f>.

### ATTACKS (path | command | verify result):
- atk_1.lean (prepatch bug: adds `|| decide (a.choices != b.choices)` — treats choices as schema-relevant) | `bash scripts/lean_verify.sh atk_1.lean` | exit 1, FAIL (unsolved goal: not(choices)-> col-or-identity). Correctly REJECTED. This IS the prepatch reproduction (matches Solution_prepatch.lean); prepatch_reproduced=true.
- atk_2.lean (partial-domain/ungrounded: `return true`) | lean_verify | exit 1 FAIL. REJECTED.
- atk_3.lean (boundary/control-flow-effect: drops schemaIdentity, only quotedColumn) | lean_verify | exit 1 FAIL. REJECTED.
- atk_4.lean (if-then-else form, BEHAVIORALLY CORRECT == gold) | lean_verify | exit 1 FAIL — frozen proof script (loom_solve; simp_all) does not discharge the ite form. False-NEGATIVE (over-strict) direction only; not a soundness hole.
- atk_5.lean (ungrounded-oracle echo: `return schemaAlterationNeeded a b`, CORRECT) | lean_verify | exit 1 FAIL ('No goals to be solved' — proof-script fragility). Over-strict direction only.
- atk_6.lean (De Morgan of the identical disjunction: `! (col= && identity=)`, BEHAVIORALLY == gold) | lean_verify | exit 0 VERIFIES. Its faithful refined patch = the gold decision (choices ignored). MATERIALIZED patch (atk_6.patch) and RAN through official harness: run_resolve('django__django-15561', patch) => RESOLVED=True, completed=True, attempts=1, flaky=False; tests_status FAIL_TO_PASS 1/1 pass, PASS_TO_PASS 141/141 pass, 0 failures. RESOLVES.
- atk_7.lean (conjunction && instead of ||) | lean_verify | exit 1 FAIL. REJECTED.
- atk_8.lean (negated: returns false when rewrite needed) | lean_verify | exit 1 FAIL. REJECTED.

positive_control.lean (shipped Solution.lean, byte-identical): lean_verify exit 0 VERIFIES.

REFINEMENT AUDIT: meta.json axioms==[] and deep_model_references==[] (confirmed); refinement.md declares zero A-legs. All legs A1-A5 are R (Field<->FieldDef projection via UNCHANGED callees deconstruct()/quote_name(), exercised live by G-CONF) or I (A4 decision disjunction). No kind-3 (inexpressible-changed-op). Correspondence is sound: the genuinely-changed behavior (excluding `choices` from the rewrite decision) is modeled DIRECTLY in the pure region — schemaAlterationNeeded consults quotedColumn and schemaIdentity but never choices; choices is split into its own observable FieldDef field rather than being folded into schemaIdentity, faithfully encoding the gold's `non_db_attrs += choices` end-state. mapping.md 2.1 strips exactly the pre-patch non_database_attrs set (choices NOT in it), consistent with the patch. G-AX vacuous (no axioms).

CONCLUSION: The only same-spec impl that VERIFIES (atk_6) has a materialized faithful patch that RESOLVES under the official harness. The 5 genuinely-wrong impls (atk_1/2/3/7/8) are all rejected by the spec. The 2 correct-but-unverifying impls (atk_4/5) fail in the safe over-strict direction. verify=>correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition `ensures out = schemaAlterationNeeded a b` totally pins the output to a deterministic pure function of (a,b), so every verifying same-spec impl is extensionally equal to schemaAlterationNeeded, which correctly ignores FieldDef.choices (matching the gold end-state). No verifying wrong impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The decision the desired
   behaviour concerns — whether replacing one field definition with another
   requires rewriting the stored database column — is modeled directly in the
   `pure` region (`schemaAlterationNeeded`) from observable components of the two
   definitions. The mechanism that projects a concrete field definition onto
   those observable components (its quoted column name, its schema-relevant
   identity, and its enumerated choices) is a stable, unchanged operation; it is a
   type refinement recorded in mapping.md and exercised against the real
   projection by G-CONF (conformance_check.py), not an axiom. Nothing is
   axiomatized. -/
-- axioms-end

-- pure-start
/- A field definition as observed when deciding whether replacing one field
   definition with another requires rewriting the stored database column.
   * `quotedColumn`   — the quoted name of the database column the field maps to.
   * `schemaIdentity` — the part of the field's reconstructable definition that
                        determines the column's database schema: its import path,
                        positional arguments, and the keyword arguments that
                        affect the column. Attributes that never influence the
                        column's schema are not part of it.
   * `choices`        — the field's enumerated choices. A presentation-only
                        attribute, carried separately so the decision can be
                        stated with explicit access to it. -/
structure FieldDef where
  quotedColumn   : String
  schemaIdentity : String
  choices        : String
  deriving DecidableEq, Inhabited

/- Whether replacing the field definition `a` with `b` requires rewriting the
   stored column. A rewrite is required exactly when the quoted column name
   changes or the schema-relevant identity changes. The enumerated `choices`
   attribute is presentation-only: a difference in `choices` alone never requires
   a rewrite, so it is not consulted here even though it is observable. -/
def schemaAlterationNeeded (a b : FieldDef) : Bool :=
  decide (a.quotedColumn ≠ b.quotedColumn) ||
    decide (a.schemaIdentity ≠ b.schemaIdentity)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether replacing the field definition `a` with `b` requires rewriting
   the stored database column. Both `a` and `b` are read-only — the decision
   mutates nothing (directive 5). A rewrite is required precisely when the quoted
   column name differs or the schema-relevant identity differs; a change confined
   to the presentation-only `choices` attribute requires no rewrite. -/
method decideSchemaAlteration (a : FieldDef) (b : FieldDef) return (out : Bool)
  ensures out = schemaAlterationNeeded a b
  do
    -- impl-start
    return (decide (a.quotedColumn ≠ b.quotedColumn) ||
      decide (a.schemaIdentity ≠ b.schemaIdentity))
    -- impl-end

prove_correct decideSchemaAlteration by
  loom_solve
  simp_all [schemaAlterationNeeded]
```

Prepatch bug re-encoded as an attack: `True`.

 All 8 attacks + positive_control confirmed same_spec==True via swebench_unified.markers.same_spec (velvet). Verified concurrently (<=4) via scripts/lean_verify.sh <f>.

### ATTACKS (path | command | verify result):
- atk_1.lean (prepatch bug: adds `|| decide (a.choices != b.choices)` — treats choices as schema-relevant) | `bash scripts/lean_verify.sh atk_1.lean` | exit 1, FAIL (unsolved goal: not(choices)-> col-or-identity). Correctly REJECTED. This IS the prepatch reproduction (matches Solution_prepatch.lean); prepatch_reproduced=true.
- atk_2.lean (partial-domain/ungrounded: `return true`) | lean_verify | exit 1 FAIL. REJECTED.
- atk_3.lean (boundary/control-flow-effect: drops schemaIdentity, only quotedColumn) | lean_verify | exit 1 FAIL. REJECTED.
- atk_4.lean (if-then-else form, BEHAVIORALLY CORRECT == gold) | lean_verify | exit 1 FAIL — frozen proof script (loom_solve; simp_all) does not discharge the ite form. False-NEGATIVE (over-strict) direction only; not a soundness hole.
- atk_5.lean (ungrounded-oracle echo: `return schemaAlterationNeeded a b`, CORRECT) | lean_verify | exit 1 FAIL ('No goals to be solved' — proof-script fragility). Over-strict direction only.
- atk_6.lean (De Morgan of the identical disjunction: `! (col= && identity=)`, BEHAVIORALLY == gold) | lean_verify | exit 0 VERIFIES. Its faithful refined patch = the gold decision (choices ignored). MATERIALIZED patch (atk_6.patch) and RAN through official harness: run_resolve('django__django-15561', patch) => RESOLVED=True, completed=True, attempts=1, flaky=False; tests_status FAIL_TO_PASS 1/1 pass, PASS_TO_PASS 141/141 pass, 0 failures. RESOLVES.
- atk_7.lean (conjunction && instead of ||) | lean_verify | exit 1 FAIL. REJECTED.
- atk_8.lean (negated: returns false when rewrite needed) | lean_verify | exit 1 FAIL. REJECTED.

positive_control.lean (shipped Solution.lean, byte-identical): lean_verify exit 0 VERIFIES.

REFINEMENT AUDIT: meta.json axioms==[] and deep_model_references==[] (confirmed); refinement.md declares zero A-legs. All legs A1-A5 are R (Field<->FieldDef projection via UNCHANGED callees deconstruct()/quote_name(), exercised live by G-CONF) or I (A4 decision disjunction). No kind-3 (inexpressible-changed-op). Correspondence is sound: the genuinely-changed behavior (excluding `choices` from the rewrite decision) is modeled DIRECTLY in the pure region — schemaAlterationNeeded consults quotedColumn and schemaIdentity but never choices; choices is split into its own observable FieldDef field rather than being folded into schemaIdentity, faithfully encoding the gold's `non_db_attrs += choices` end-state. mapping.md 2.1 strips exactly the pre-patch non_database_attrs set (choices NOT in it), consistent with the patch. G-AX vacuous (no axioms).

CONCLUSION: The only same-spec impl that VERIFIES (atk_6) has a materialized faithful patch that RESOLVES under the official harness. The 5 genuinely-wrong impls (atk_1/2/3/7/8) are all rejected by the spec. The 2 correct-but-unverifying impls (atk_4/5) fail in the safe over-strict direction. verify=>correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for BaseDatabaseSchemaEditor._field_should_be_altered (django/db/backends/base/schema.py:1120 @ base_commit 6991880). Verified in worktree (confirmed at base_commit: no `non_db_attrs`, pre-patch source present).

Spec region byte-identity: swebench_unified.markers.same_spec(Solution, Solution_prepatch, VelvetBackend) = True. Solution.lean verifies (lean_verify.sh exit 0). Prepatch differs only in the impl (adds the `decide (a.choices != b.choices)` disjunct) — same frozen spec, as required.

Modeled function schemaAlterationNeeded a b = (a.quotedColumn != b.quotedColumn) || (a.schemaIdentity != b.schemaIdentity), where FieldDef is the projection of a real Field via the UNCHANGED callees deconstruct()/quote_name(): quotedColumn=quote_name(field.column); schemaIdentity=repr((path,args,sorted(kwargs∖STRIP∖{choices}))); choices carried but never consulted.

Real post-patch callee: quote_name(old.column)!=quote_name(new.column) or (old_path,old_args,old_kwargs)!=(new_path,new_args,new_kwargs), each field popping field.non_db_attrs = the 11 pre-patch non_database_attrs PLUS 'choices'.

Match analysis:
1. Disjunction structure identical (quoted-column-diff OR identity-diff).
2. STRIP set in mapping.md/conformance_check.py = exactly the 11 pre-patch non_database_attrs; 'choices' is split out and ignored ⇒ effective ignored set = 11 ∪ {choices} = gold's non_db_attrs. A choices-only difference yields False in both (the bug fix); the prepatch reproduces the pre-patch True.
3. Tuple-equality (path,args,kwargs) ↔ repr((path,args,sorted(items))) is faithful: dict equality is order-independent, sorted-items canonicalizes; path/args serialized identically.
4. Potential drift point — spec applies a FIXED strip set to BOTH fields, whereas gold reads per-field old_field.non_db_attrs / new_field.non_db_attrs. This would only diverge if some Field subclass overrode non_db_attrs. At this commit the gold patch defines non_db_attrs solely on base Field; grep found NO subclass override, so it is a single inherited constant for every field ⇒ fixed-strip model is behaviorally equivalent. No divergence.

Empirical corroboration: bundle G-CONF (seed 15561, 12 boundary + 100000 fuzzed real Field pairs, choices-only diffs over-weighted) reports 0 disagreements between the shadow and the patched oracle; G-EQ and G-PANEL-1/2/3 recorded pass. I could construct no input where the modeled function disagrees with the real patched _field_should_be_altered. Spec is neither too strong nor drifted: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean (same_spec == True); lexical G-LEAK screen passes with zero hard failures. Semantic review: the public problem_statement already discloses the full desired behavior — 'AlterField operation should be noop when adding/changing choices on SQLite' (a choices-only field change must generate no SQL / no column rewrite). The spec view encodes exactly that target behavior via an abstract model: FieldDef{quotedColumn, schemaIdentity, choices} with schemaAlterationNeeded never consulting `choices`. Encoding the publicly-stated desired behavior is required of any faithful spec and is not leakage. The spec view does NOT reveal the gold *mechanism*: no gold-patch line, no patched file paths (schema.py, fields/__init__.py), no `non_database_attrs`/`non_db_attrs` (the latter is hints-only), no `_field_should_be_altered`. The attribute enumeration (blank, db_column, ...) and the list-refactor detail live only in mapping.md/refinement.md (auditor-only artifacts, not the consumer spec view). Changed symbols detected by the screen are `Field` (the token 'field' is already public in problem_statement) and `field_should_be_altered` (absent from the spec view). A solver seeing this spec view gains nothing beyond the public problem_statement and cannot reconstruct the specific gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
