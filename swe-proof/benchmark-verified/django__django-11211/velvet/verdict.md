# P2 adversarial audit — django__django-11211

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,10 +90,7 @@
   ensures canonicalize out = out
   do
     -- impl-start
-    -- Put the value through the base preliminary coercion, then the field's
-    -- normal-form conversion; return the canonical representation.
-    let prepped :| prepped = preCoerce value
-    let canon  :| canon  = canonicalize prepped
+    let canon  :| canon  = canonicalize value
     return canon
     -- impl-end
 end
```

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,11 +90,9 @@
   ensures canonicalize out = out
   do
     -- impl-start
-    -- Put the value through the base preliminary coercion, then the field's
-    -- normal-form conversion; return the canonical representation.
-    let prepped :| prepped = preCoerce value
-    let canon  :| canon  = canonicalize prepped
-    return canon
+    let a :| a = canonicalize value
+    let b :| b = canonicalize a
+    return b
     -- impl-end
 end
 
```

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,11 +90,9 @@
   ensures canonicalize out = out
   do
     -- impl-start
-    -- Put the value through the base preliminary coercion, then the field's
-    -- normal-form conversion; return the canonical representation.
-    let prepped :| prepped = preCoerce value
-    let canon  :| canon  = canonicalize prepped
-    return canon
+    let c :| c = canonicalize value
+    let out :| out = preCoerce c
+    return out
     -- impl-end
 end
 
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,11 +90,8 @@
   ensures canonicalize out = out
   do
     -- impl-start
-    -- Put the value through the base preliminary coercion, then the field's
-    -- normal-form conversion; return the canonical representation.
-    let prepped :| prepped = preCoerce value
-    let canon  :| canon  = canonicalize prepped
-    return canon
+    let out :| out = canonicalize value
+    return out
     -- impl-end
 end
 
```

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,11 +90,10 @@
   ensures canonicalize out = out
   do
     -- impl-start
-    -- Put the value through the base preliminary coercion, then the field's
-    -- normal-form conversion; return the canonical representation.
-    let prepped :| prepped = preCoerce value
-    let canon  :| canon  = canonicalize prepped
-    return canon
+    let a :| a = preCoerce value
+    let b :| b = canonicalize a
+    let c :| c = preCoerce b
+    return c
     -- impl-end
 end
 
```

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,11 +90,10 @@
   ensures canonicalize out = out
   do
     -- impl-start
-    -- Put the value through the base preliminary coercion, then the field's
-    -- normal-form conversion; return the canonical representation.
-    let prepped :| prepped = preCoerce value
-    let canon  :| canon  = canonicalize prepped
-    return canon
+    let a :| a = preCoerce value
+    let b :| b = preCoerce a
+    let c :| c = canonicalize b
+    return c
     -- impl-end
 end
 
```

Attack 7 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -90,11 +90,10 @@
   ensures canonicalize out = out
   do
     -- impl-start
-    -- Put the value through the base preliminary coercion, then the field's
-    -- normal-form conversion; return the canonical representation.
-    let prepped :| prepped = preCoerce value
-    let canon  :| canon  = canonicalize prepped
-    return canon
+    let a :| a = canonicalize value
+    let b :| b = canonicalize a
+    let c :| c = preCoerce b
+    return c
     -- impl-end
 end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real preparation step is a straight-line composition
   of two always-terminating calls (the base preliminary coercion, then the
   normal-form conversion), so a diverging implementation must NOT satisfy
   this spec. Partial correctness would let a non-terminating branch discharge
   its postconditions vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The domain of values a model field may be asked to prepare for use as a
   lookup key. A value arrives in one of several interchangeable shapes that all
   denote the same logical datum: absent, an already-concrete object, a textual
   transcription, or an integer transcription. Modeled as an opaque carrier so
   no claim is made about the field's internal parsing; the bijection to the
   repository value space is in mapping.md (G-AX uses it). -/
inductive Val where
  | absent
  | concrete (canon : List Char)
  | textual  (s : List Char)
  | numeric  (n : Nat)

/- A value is well-formed when it is an accepted representation — the normal-form
   conversion is defined on it (it does not reject it). The F2P input domain (a
   freshly generated identifier and its textual transcription) is well-formed.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom WellFormed : Val → Prop

/- The base field's preliminary value coercion: it performs only generic,
   representation-preserving housekeeping and so returns any already-concrete
   value unchanged. Unchanged callee; weakest sufficient contract = identity on
   this domain (directive 7). G-AX checks it against the real base callee. -/
axiom preCoerce : Val → Val
axiom preCoerce_id : ∀ v : Val, preCoerce v = v

/- The field's normal-form conversion: maps any accepted representation of a
   value to the single canonical representation that datum is stored and compared
   as. Its sole load-bearing property here is that the canonical representation
   is stable — converting an already-canonical value changes nothing — so
   the prepared key is idempotent under further conversion. Unchanged callee;
   pinned only at this weakest sufficient strength (directive 7). G-AX checks it
   against the real conversion over the representation corpus. -/
axiom canonicalize : Val → Val
axiom canonicalize_idem :
    ∀ v : Val, WellFormed v → canonicalize (canonicalize v) = canonicalize v
-- axioms-end

-- pure-start
/- The non-deterministic choices below are well-posed: for any target value `v`
   the set of values equal to `v` is non-empty (`v` itself). This supplies the
   constructive existence witness so each `:|` choice elaborates. It does NOT
   weaken verification: under demonic choice the postcondition must still hold
   for every value the predicate allows — here exactly the named callee result. -/
noncomputable instance findableEqVal (v : Val) (n : Lean.Name) :
    Findable (fun e : Val => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare a field value for use as a relational lookup key.

   The desired behavior: the value is first put through the base field's
   preliminary coercion and then converted to the field's canonical
   representation, so that distinct accepted transcriptions of the same datum
   (for instance a textual transcription and the already-concrete object) yield
   the SAME prepared key. The result is exactly that canonical representation
   (`out = canonicalize value`), and it is itself canonical — a further
   conversion leaves it unchanged (`canonicalize out = out`) — which is what lets
   a key derived from one transcription match a stored value derived from
   another.

   `value` is the read-only input (not `mut`): preparation consumes it and never
   alters it (directive 5). It is required well-formed — an accepted
   representation the conversion does not reject (mapping.md §2). -/
noncomputable section
method preparedValue (value : Val) return (out : Val)
  require WellFormed value
  ensures out = canonicalize value
  ensures canonicalize out = out
  do
    -- impl-start
    -- Put the value through the base preliminary coercion, then the field's
    -- normal-form conversion; return the canonical representation.
    let prepped :| prepped = preCoerce value
    let canon  :| canon  = canonicalize prepped
    return canon
    -- impl-end
end

prove_correct preparedValue by
  loom_solve <;> simp_all [preCoerce_id, canonicalize_idem]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for django__django-11211 (velvet). PROTOCOL COMPLETE, no break found.

SPEC SHAPE: preparedValue(value: Val) require WellFormed value; ensures out = canonicalize value AND canonicalize out = out. canonicalize is opaque (only canonicalize_idem known); preCoerce is a UNIVERSAL identity axiom (preCoerce_id: forall v, preCoerce v = v). The exact-equality postcondition fully PINS the output to the canonical representation — this is a strong spec, not a weak one.

ATTACKS (8 distinct wrong impls + prepatch), all same_spec=True (axioms/pure/pre/post byte-identical; verified via swebench_unified.markers.same_spec, velvet backend):
- atk_1 (partial-domain: drop preCoerce, canon=canonicalize value): VERIFIES (rc=0).
- atk_2 (control-flow/effect: double canonicalize): VERIFIES (rc=0).
- atk_3 (order-swap: canonicalize then preCoerce): VERIFIES (rc=0).
- atk_4 (ungrounded-oracle echo: out :| out = canonicalize value directly): VERIFIES (rc=0).
- atk_5 (PREPATCH bug: return preCoerce value only, no canonicalize): FAILS verify (rc=1) — residual goals value = canonicalize value / canonicalize value = value unprovable. Prepatch reproduced. NOT a same-spec verifying attack, excluded from patches.
- atk_6 (preCoerce; canonicalize; preCoerce sandwich): VERIFIES (rc=0).
- atk_7 (double preCoerce then canonicalize): VERIFIES (rc=0).
- atk_8 (canonicalize; canonicalize; preCoerce): VERIFIES (rc=0).
Positive control (exact gold Solution.lean): VERIFIES (rc=0).
Command: bash scripts/lean_verify.sh <file> (ran concurrently in 2 batches of 4).

MANDATORY RESOLVE STEP — every verifying attack's faithful refined patch materialized (git-diff against a fresh worktree at base_commit ba726067604ce5a8ca3919edf653496722b433ab; refinement map preCoerce->super().get_prep_value, canonicalize->self.to_python) and RUN through the official harness via swebench_unified.harness.run_resolve (docker, prebuilt image sweb.eval...django-11211, FAIL_TO_PASS test_prefetch_GFK_uuid_pk):
- gold baseline: RESOLVED (oracle sanity check passed).
- atk_1: RESOLVED. atk_2: RESOLVED. atk_3: RESOLVED. atk_4: RESOLVED. atk_6: RESOLVED. atk_7: RESOLVED. atk_8: RESOLVED.
All 7 verifying attacks' faithful patches RESOLVE (executed, not speculated; observed resolved=true, completed=true each). No verifying wrong impl produces a non-resolving faithful patch => NO verify⇏correct break.

WHY IT HOLDS: preCoerce_id is a faithful axiom (G-AX confirmed base Field.get_prep_value is identity on the non-Promise value domain, 8013 values seed=11211), so inserting/removing/reordering super().get_prep_value calls is behaviorally inert in Python. canonicalize_idem is faithful (to_python idempotent + transcription-collapsing), so extra to_python calls are inert. The exact-equality postcondition out = canonicalize value forces at least one canonicalize on the result path in every verifying impl, which in Python is exactly the discriminating to_python conversion the F2P test needs. Hence verify => the canonical conversion happens => resolves.

REFINEMENT.MD AUDIT: A1 R (Val<->field value space, WellFormed<->to_python accepts) sound; A2 A-consumed (preCoerce<->base Field.get_prep_value via preCoerce_id) correspondence holds; A3 A-consumed (canonicalize<->to_python via canonicalize_idem) correspondence holds; A4 I; no kind-3 legs. A-leg callee correspondences match the real callees per mapping.md §3 and G-AX. Sound.

VERDICT: SOUND — 8 distinct same-spec attacks encoded, 7 verify and all 7 faithful patches resolve, prepatch reproduced (fails verify), positive control verifies+resolves. No break.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_3.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real preparation step is a straight-line composition
   of two always-terminating calls (the base preliminary coercion, then the
   normal-form conversion), so a diverging implementation must NOT satisfy
   this spec. Partial correctness would let a non-terminating branch discharge
   its postconditions vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The domain of values a model field may be asked to prepare for use as a
   lookup key. A value arrives in one of several interchangeable shapes that all
   denote the same logical datum: absent, an already-concrete object, a textual
   transcription, or an integer transcription. Modeled as an opaque carrier so
   no claim is made about the field's internal parsing; the bijection to the
   repository value space is in mapping.md (G-AX uses it). -/
inductive Val where
  | absent
  | concrete (canon : List Char)
  | textual  (s : List Char)
  | numeric  (n : Nat)

/- A value is well-formed when it is an accepted representation — the normal-form
   conversion is defined on it (it does not reject it). The F2P input domain (a
   freshly generated identifier and its textual transcription) is well-formed.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom WellFormed : Val → Prop

/- The base field's preliminary value coercion: it performs only generic,
   representation-preserving housekeeping and so returns any already-concrete
   value unchanged. Unchanged callee; weakest sufficient contract = identity on
   this domain (directive 7). G-AX checks it against the real base callee. -/
axiom preCoerce : Val → Val
axiom preCoerce_id : ∀ v : Val, preCoerce v = v

/- The field's normal-form conversion: maps any accepted representation of a
   value to the single canonical representation that datum is stored and compared
   as. Its sole load-bearing property here is that the canonical representation
   is stable — converting an already-canonical value changes nothing — so
   the prepared key is idempotent under further conversion. Unchanged callee;
   pinned only at this weakest sufficient strength (directive 7). G-AX checks it
   against the real conversion over the representation corpus. -/
axiom canonicalize : Val → Val
axiom canonicalize_idem :
    ∀ v : Val, WellFormed v → canonicalize (canonicalize v) = canonicalize v
-- axioms-end

-- pure-start
/- The non-deterministic choices below are well-posed: for any target value `v`
   the set of values equal to `v` is non-empty (`v` itself). This supplies the
   constructive existence witness so each `:|` choice elaborates. It does NOT
   weaken verification: under demonic choice the postcondition must still hold
   for every value the predicate allows — here exactly the named callee result. -/
noncomputable instance findableEqVal (v : Val) (n : Lean.Name) :
    Findable (fun e : Val => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare a field value for use as a relational lookup key.

   The desired behavior: the value is first put through the base field's
   preliminary coercion and then converted to the field's canonical
   representation, so that distinct accepted transcriptions of the same datum
   (for instance a textual transcription and the already-concrete object) yield
   the SAME prepared key. The result is exactly that canonical representation
   (`out = canonicalize value`), and it is itself canonical — a further
   conversion leaves it unchanged (`canonicalize out = out`) — which is what lets
   a key derived from one transcription match a stored value derived from
   another.

   `value` is the read-only input (not `mut`): preparation consumes it and never
   alters it (directive 5). It is required well-formed — an accepted
   representation the conversion does not reject (mapping.md §2). -/
noncomputable section
method preparedValue (value : Val) return (out : Val)
  require WellFormed value
  ensures out = canonicalize value
  ensures canonicalize out = out
  do
    -- impl-start
    -- Put the value through the base preliminary coercion, then the field's
    -- normal-form conversion; return the canonical representation.
    let prepped :| prepped = preCoerce value
    let canon  :| canon  = canonicalize prepped
    return canon
    -- impl-end
end

prove_correct preparedValue by
  loom_solve <;> simp_all [preCoerce_id, canonicalize_idem]
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity adversarial audit for django__django-11211 (velvet). PROTOCOL COMPLETE, no break found.

SPEC SHAPE: preparedValue(value: Val) require WellFormed value; ensures out = canonicalize value AND canonicalize out = out. canonicalize is opaque (only canonicalize_idem known); preCoerce is a UNIVERSAL identity axiom (preCoerce_id: forall v, preCoerce v = v). The exact-equality postcondition fully PINS the output to the canonical representation — this is a strong spec, not a weak one.

ATTACKS (8 distinct wrong impls + prepatch), all same_spec=True (axioms/pure/pre/post byte-identical; verified via swebench_unified.markers.same_spec, velvet backend):
- atk_1 (partial-domain: drop preCoerce, canon=canonicalize value): VERIFIES (rc=0).
- atk_2 (control-flow/effect: double canonicalize): VERIFIES (rc=0).
- atk_3 (order-swap: canonicalize then preCoerce): VERIFIES (rc=0).
- atk_4 (ungrounded-oracle echo: out :| out = canonicalize value directly): VERIFIES (rc=0).
- atk_5 (PREPATCH bug: return preCoerce value only, no canonicalize): FAILS verify (rc=1) — residual goals value = canonicalize value / canonicalize value = value unprovable. Prepatch reproduced. NOT a same-spec verifying attack, excluded from patches.
- atk_6 (preCoerce; canonicalize; preCoerce sandwich): VERIFIES (rc=0).
- atk_7 (double preCoerce then canonicalize): VERIFIES (rc=0).
- atk_8 (canonicalize; canonicalize; preCoerce): VERIFIES (rc=0).
Positive control (exact gold Solution.lean): VERIFIES (rc=0).
Command: bash scripts/lean_verify.sh <file> (ran concurrently in 2 batches of 4).

MANDATORY RESOLVE STEP — every verifying attack's faithful refined patch materialized (git-diff against a fresh worktree at base_commit ba726067604ce5a8ca3919edf653496722b433ab; refinement map preCoerce->super().get_prep_value, canonicalize->self.to_python) and RUN through the official harness via swebench_unified.harness.run_resolve (docker, prebuilt image sweb.eval...django-11211, FAIL_TO_PASS test_prefetch_GFK_uuid_pk):
- gold baseline: RESOLVED (oracle sanity check passed).
- atk_1: RESOLVED. atk_2: RESOLVED. atk_3: RESOLVED. atk_4: RESOLVED. atk_6: RESOLVED. atk_7: RESOLVED. atk_8: RESOLVED.
All 7 verifying attacks' faithful patches RESOLVE (executed, not speculated; observed resolved=true, completed=true each). No verifying wrong impl produces a non-resolving faithful patch => NO verify⇏correct break.

WHY IT HOLDS: preCoerce_id is a faithful axiom (G-AX confirmed base Field.get_prep_value is identity on the non-Promise value domain, 8013 values seed=11211), so inserting/removing/reordering super().get_prep_value calls is behaviorally inert in Python. canonicalize_idem is faithful (to_python idempotent + transcription-collapsing), so extra to_python calls are inert. The exact-equality postcondition out = canonicalize value forces at least one canonicalize on the result path in every verifying impl, which in Python is exactly the discriminating to_python conversion the F2P test needs. Hence verify => the canonical conversion happens => resolves.

REFINEMENT.MD AUDIT: A1 R (Val<->field value space, WellFormed<->to_python accepts) sound; A2 A-consumed (preCoerce<->base Field.get_prep_value via preCoerce_id) correspondence holds; A3 A-consumed (canonicalize<->to_python via canonicalize_idem) correspondence holds; A4 I; no kind-3 legs. A-leg callee correspondences match the real callees per mapping.md §3 and G-AX. Sound.

VERDICT: SOUND — 8 distinct same-spec attacks encoded, 7 verify and all 7 faithful patches resolve, prepatch reproduced (fails verify), positive control verifies+resolves. No break.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break lens: no input in the modeled domain makes the spec disagree with the real repo callee. Modeled fn preparedValue models patched UUIDField.get_prep_value = to_python(super().get_prep_value(value)). Spec (precondition WellFormed value; ensures out = canonicalize value AND canonicalize out = out) with preCoerce↔base Field.get_prep_value (axiom preCoerce_id) and canonicalize↔UUIDField.to_python (axiom canonicalize_idem). On domain (None/UUID/str/int, no Promise) base get_prep_value is identity, so real = to_python(value) = canonicalize value — exactly the ensures; idempotence holds since to_python returns a UUID/None fixed point. VERIFICATIONS: (1) same_spec(Solution, Solution_prepatch) = True (spec region byte-identical). (2) scripts/lean_verify.sh Solution.lean -> exit 0 (verifies). (3) Solution_prepatch.lean (returns preCoerce value only) -> exit 1, residual goal 'value = canonicalize value' — spec genuinely requires the fix's canonicalization, so it is NOT vacuously weak. (4) axiom_check.py (G-AX) run against the real /tmp worktree callees over boundary + 2000 fuzz UUIDs (seed 11211) -> exit 0: base Field.get_prep_value identity (preCoerce_id) and to_python idempotent + transcription-collapsing (canonicalize_idem) all hold. Spec is NOT too strong: values where to_python raises are excluded by WellFormed; Promise/other shapes are outside Val's carriers (scope restriction, not a false claim). No diverging input found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over spec_view) PASSES with zero hard failures; same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical); meta G-LEAK status=pass; relaxed_leakage=None (no relaxation masking a semantic leak).

Problem_statement is public: it describes prefetch_related failing for a GFK pointing at a model with a UUIDField PK (model/GFK reproduction, prefetch returns None). The gold edit adds `get_prep_value` overriding it to run `to_python` on the identifier field class in django/db/models/fields/__init__.py.

Semantic leakage assessment of the CONSUMER spec view:
- No diff markers, no reproduced gold-patch line, no patched file path (django/db/models/fields/__init__.py) or dotted module path.
- No spec-view identifier or comment names the patched repo symbols get_prep_value / to_python / UUIDField. The spec uses fully abstracted vocabulary: preparedValue, preCoerce, canonicalize, Val, WellFormed.
- The narrative prose states only the intended postcondition of the modeled function (compose a base preliminary coercion with a normal-form conversion so distinct transcriptions yield the same canonical lookup key). This is legitimate specification of desired behavior, not localization of the edit. It does not reveal WHICH file/class/method to change, nor that the fix is an override of an inherited get_prep_value. A solver must still independently locate the UUID field class and determine that overriding get_prep_value to call to_python is the fix.
- Symbol-level identifiers are generic (canonicalize/preCoerce) and do not embed the gold symbols; the >=4-char distinctive-symbol embedding check passes.
- Repo-symbol-naming docs (mapping.md §3 quotes to_python/get_prep_value source, cites file:line; refinement.md quotes the gold hunk) are AUDITOR-only artifacts (G-AX/G-EQ), NOT part of the consumer spec view (spec_view projects Solution.lean only), so they are out of scope for G-LEAK.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
