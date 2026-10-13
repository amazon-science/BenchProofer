# P2 adversarial audit — django__django-11532

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch_bug.lean`, `atk_2_drop_occupancy.lean`, `atk_3_empty_bypass.lean`, `atk_4_len63_boundary.lean`, `atk_5_truthiness_guard.lean`, `atk_6_oracle_echo.lean`, `atk_10_ascii_fastpath.lean`, `atk_11_localhost_case.lean`, `atk_12_store_serve_split.lean`, `atk_13_no_reuse.lean`, `atk_14_double_encode.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7_eager_consult.lean`, `atk_8_uncond_write.lean`, `atk_9_read_first.lean` |

**Non-vacuity.** The positive control `atk_0_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — no verify⇏correct witness exists. 15 same-spec wrong impls (same_spec=True for all, checked against Solution.lean via swebench_unified.markers.same_spec / lean backend). 12 of 15 were REJECTED by lean_verify.sh (exit 1, correct_hostName carries sorryAx). The 3 that DID close with clean axioms ([propext, Quot.sound], no bundle-local axiom, no sorryAx) are extensionally EQUAL to gold — they are refinement-freedom variants, not wrong impls — and each had its faithful refined patch materialized and RUN through the official harness (run_resolve): all three resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS 1/1, PASS_TO_PASS 148/148, PASS_TO_FAIL 0. So every impl with a closing clean-axiom proof also resolves ⇒ verify ⇒ correct on this evidence.

The PRIOR pass's BROKEN counterexample was re-encoded as atk_2_drop_occupancy ("serve the exactly-right Punycode value but never write the slot") and it is now REJECTED: `lean_verify.sh atk_2_drop_occupancy.lean` → exit 1, `case none ⊢ False` at line 110. That old break was against a VALUE-ONLY spec (`problem_spec_hostName : String → String`); the current spec is the state transition `NameHolder × String` whose clause 1 (OCCUPANCY, `result.1.slot = some result.2`) is exactly the repair, and it carries the `delattr(DNS_NAME,'_fqdn')` obligation the F2P test depends on. The repair is confirmed effective.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch_bug.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,12 +94,9 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
+    holder := { holder with slot := some reportedName }
+  let served := holder.slot.getD reportedName
   return (holder, served)
 -- impl-end
 
@@ -136,4 +133,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 2 — `atk_2_drop_occupancy.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,14 +93,9 @@
 -- impl-start
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
-  let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
-  if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
-  return (holder, served)
+  -- serve the right name but never settle it into the slot
+  let served := st.slot.getD (aceEncode reportedName)
+  return (st, served)
 -- impl-end
 
 -- proof-start
@@ -136,4 +131,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 3 — `atk_3_empty_bypass.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,11 +94,11 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
+    if reportedName.isEmpty then
+      holder := { holder with slot := some reportedName }
+    else
+      holder := { holder with slot := some (aceEncode reportedName) }
   let served := holder.slot.getD (aceEncode reportedName)
   return (holder, served)
 -- impl-end
@@ -112,7 +112,7 @@
   unfold problem_spec_hostName implementation_hostName
   obtain ⟨slot⟩ := st
   cases slot with
-  | none => simp
+  | none => split <;> simp_all
   | some stored => simp
 
 /-- The specification is DETERMINISTIC: for a given holder and reported name it
@@ -136,4 +136,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 4 — `atk_4_len63_boundary.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,11 +94,11 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
+    if reportedName.length > 63 then
+      holder := { holder with slot := some reportedName }
+    else
+      holder := { holder with slot := some (aceEncode reportedName) }
   let served := holder.slot.getD (aceEncode reportedName)
   return (holder, served)
 -- impl-end
@@ -112,7 +112,7 @@
   unfold problem_spec_hostName implementation_hostName
   obtain ⟨slot⟩ := st
   cases slot with
-  | none => simp
+  | none => split <;> simp_all
   | some stored => simp
 
 /-- The specification is DETERMINISTIC: for a given holder and reported name it
@@ -136,4 +136,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 5 — `atk_5_truthiness_guard.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,11 +94,9 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
-  if holder.slot = none then
+  -- falsy-test rather than presence-test: a stored empty name re-settles
+  if holder.slot = none ∨ holder.slot = some "" then
     holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
   let served := holder.slot.getD (aceEncode reportedName)
   return (holder, served)
 -- impl-end
@@ -113,7 +111,10 @@
   obtain ⟨slot⟩ := st
   cases slot with
   | none => simp
-  | some stored => simp
+  | some stored =>
+    by_cases he : stored = ""
+    · subst he; simp
+    · simp [he]
 
 /-- The specification is DETERMINISTIC: for a given holder and reported name it
 admits at most one result. Stated without reference to any implementation, so it
@@ -136,4 +137,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 6 — `atk_6_oracle_echo.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,12 +94,10 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
+  -- echo the exact Punycode literal the official test asserts on
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
+    holder := { holder with slot := some "xn--p8s937b" }
+  let served := holder.slot.getD "xn--p8s937b"
   return (holder, served)
 -- impl-end
 
@@ -136,4 +134,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 7 — `atk_7_eager_consult.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,13 +93,12 @@
 -- impl-start
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
+  -- consult the reported local name up front, on every request
+  let encoded := aceEncode reportedName
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
+    holder := { holder with slot := some encoded }
+  let served := holder.slot.getD encoded
   return (holder, served)
 -- impl-end
 
@@ -136,4 +135,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 8 — `atk_8_uncond_write.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,14 +93,9 @@
 -- impl-start
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
-  let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
-  if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
-  return (holder, served)
+  -- decide the served name, then unconditionally (re)write the slot with it
+  let served := st.slot.getD (aceEncode reportedName)
+  return ({ slot := some served }, served)
 -- impl-end
 
 -- proof-start
@@ -136,4 +131,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 9 — `atk_9_read_first.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -92,15 +92,11 @@
 
 -- impl-start
 def implementation_hostName (st : NameHolder) (reportedName : String) :
-    NameHolder × String := Id.run do
-  let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
-  if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
-  return (holder, served)
+    NameHolder × String :=
+  -- read the slot first; settle only when it turns out to be unoccupied
+  match st.slot with
+  | some stored => (st, stored)
+  | none => ({ slot := some (aceEncode reportedName) }, aceEncode reportedName)
 -- impl-end
 
 -- proof-start
@@ -136,4 +132,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 10 — `atk_10_ascii_fastpath.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,11 +94,12 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
+    -- fast path: a name that already IS its ASCII-compatible form is stored as-is
+    if reportedName == aceEncode reportedName then
+      holder := { holder with slot := some reportedName }
+    else
+      holder := { holder with slot := some (aceEncode reportedName) }
   let served := holder.slot.getD (aceEncode reportedName)
   return (holder, served)
 -- impl-end
@@ -112,7 +113,12 @@
   unfold problem_spec_hostName implementation_hostName
   obtain ⟨slot⟩ := st
   cases slot with
-  | none => simp
+  | none =>
+    by_cases hb : (reportedName == aceEncode reportedName) = true
+    · have he : reportedName = aceEncode reportedName := by
+        exact (beq_iff_eq).mp hb
+      simp [hb, he]
+    · simp [hb]
   | some stored => simp
 
 /-- The specification is DETERMINISTIC: for a given holder and reported name it
@@ -136,4 +142,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 11 — `atk_11_localhost_case.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,11 +94,11 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
+    if reportedName = "localhost" then
+      holder := { holder with slot := some "localhost" }
+    else
+      holder := { holder with slot := some (aceEncode reportedName) }
   let served := holder.slot.getD (aceEncode reportedName)
   return (holder, served)
 -- impl-end
@@ -112,7 +112,7 @@
   unfold problem_spec_hostName implementation_hostName
   obtain ⟨slot⟩ := st
   cases slot with
-  | none => simp
+  | none => split <;> simp_all
   | some stored => simp
 
 /-- The specification is DETERMINISTIC: for a given holder and reported name it
@@ -136,4 +136,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 12 — `atk_12_store_serve_split.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,12 +94,11 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
+  let mut served := reportedName
   if holder.slot = none then
     holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
+  else
+    served := holder.slot.getD reportedName
   return (holder, served)
 -- impl-end
 
@@ -136,4 +135,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 13 — `atk_13_no_reuse.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -93,14 +93,9 @@
 -- impl-start
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
-  let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
-  if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
-  return (holder, served)
+  -- always settle afresh from the reported local name; never reuse the slot
+  let served := aceEncode reportedName
+  return ({ slot := some served }, served)
 -- impl-end
 
 -- proof-start
@@ -136,4 +131,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 14 — `atk_14_double_encode.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,11 +94,9 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
-    holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
+    -- idempotence assumed: encode the already-encoded name again
+    holder := { holder with slot := some (aceEncode (aceEncode reportedName)) }
   let served := holder.slot.getD (aceEncode reportedName)
   return (holder, served)
 -- impl-end
@@ -136,4 +134,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Attack 15 — `atk_15_encode_on_reuse.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -94,13 +94,11 @@
 def implementation_hostName (st : NameHolder) (reportedName : String) :
     NameHolder × String := Id.run do
   let mut holder := st
-  -- while no metadata name has been settled, settle one: the reported local
-  -- name's ASCII-compatible representation, and leave it occupying the slot
   if holder.slot = none then
     holder := { holder with slot := some (aceEncode reportedName) }
-  -- serve the name the slot now holds
-  let served := holder.slot.getD (aceEncode reportedName)
-  return (holder, served)
+  -- normalize on read: re-encode whatever the slot holds
+  let served := aceEncode (holder.slot.getD reportedName)
+  return ({ slot := some served }, served)
 -- impl-end
 
 -- proof-start
@@ -136,4 +134,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -136,4 +136,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE

Every attack file was generated by splicing ONLY the impl region onto a byte-identical PREFIX (imports/docstring/axioms/pure/post-conditions) and SUFFIX (proof region). `#print axioms` probes were injected INSIDE the proof region, which spec_view elides, so same_spec stays True. Verified: same_spec=True for all 16 files (15 attacks + positive control).

Verify command (per file, from repo root; run 4-at-a-time as concurrent background jobs):
  bash scripts/lean_verify.sh <f>.lean

POSITIVE CONTROL — atk_0_positive.lean (gold impl verbatim): exit 0.
  'correct_hostName' depends on axioms: [propext, Quot.sound]
  'implementation_hostName' does not depend on any axioms
  'spec_hostName_deterministic' depends on axioms: [propext]
No sorryAx, no bundle-local axiom ⇒ clean, matching meta.json axioms=[] and axiom_check.py's skip-stub claim.

REJECT LANE — 12 wrong impls, all exit 1, all with sorryAx in correct_hostName (residual goal quoted):
 1. atk_1_prepatch_bug (THE REAL BUG, prepatch reproduced): settle slot verbatim, no encoder → `case none ⊢ reportedName = aceEncode reportedName`. Matches Solution_prepatch.lean's single edit; clauses 1+2 still hold, only clause 3 SETTLING fails — a minimal single-edit counterpart, so G-DIFF fails as required.
 2. atk_2_drop_occupancy (PRIOR PASS'S COUNTEREXAMPLE, re-encoded): right value, slot never written → `case none ⊢ False`.
 3. atk_3_empty_bypass (partial domain): empty name skips encoder → `case none.isTrue, h: reportedName.isEmpty = true ⊢ reportedName = aceEncode reportedName`.
 4. atk_4_len63_boundary (boundary, 63-octet DNS label limit): `h: 63 < reportedName.length ⊢ reportedName = aceEncode reportedName`.
 5. atk_5_truthiness_guard (control-flow effect): guards on FALSINESS (`slot = none ∨ slot = some ""`) instead of PRESENCE — i.e. `if not self._fqdn:` rather than `if not hasattr(...)` → `case pos ⊢ aceEncode reportedName = ""`. This is the precise rival mapping.md's "Presence, not truthiness" row claims to exclude, and clause 2 REUSE does exclude it.
 6. atk_6_oracle_echo (ungrounded oracle echo): hardcodes the literal the F2P test asserts on → `case none ⊢ "xn--p8s937b" = aceEncode reportedName`. The spec does NOT admit the test-literal echo.
 7. atk_10_ascii_fastpath: branch on `reportedName == aceEncode reportedName`; simp hits max recursion, then sorryAx — an opaque encoder cannot be decided.
 8. atk_11_localhost_case (host-specific partial domain): `⊢ "localhost" = aceEncode "localhost"` — the spec will not even concede the encoder is identity on a pure-ASCII name, correctly, since aceEncode is opaque.
 9. atk_12_store_serve_split: store encoded but serve raw on the settle path → attacks clause 1's store/serve agreement → `⊢ aceEncode reportedName = reportedName ∧ reportedName = aceEncode reportedName`.
10. atk_13_no_reuse: always re-settle from the reported name, never reuse → clause 2 → `case some ⊢ aceEncode reportedName = stored`.
11. atk_14_double_encode (A-LEG PROBE): `aceEncode (aceEncode x)` → `⊢ aceEncode (aceEncode reportedName) = aceEncode reportedName`. IDEMPOTENCE IS NOT SMUGGLED IN — the opaque is genuinely opaque.
12. atk_15_encode_on_reuse (A-LEG PROBE): re-encode the stored name on read → same residual plus a `case some` goal.

MANDATORY RESOLVE RUNS — 3 impls closed with clean axioms; ALL had faithful patches materialized and EXECUTED through the official harness. Each patch = gold patch.diff with ONLY get_fqdn's body replaced by the faithful refinement of that Lean impl (all four sibling refactor sites kept, so the diff is otherwise gold). All three checked with `git apply --check` in a clean base_commit worktree (wtchk) → APPLY CLEAN.

Command: python resolve_one.py <atk_N.diff> atkN   (wraps swebench_unified.harness.run_resolve('django__django-11532', patch)) • atk_7_eager_consult → atk_7.diff — `encoded = punycode(socket.getfqdn())` hoisted ABOVE the hasattr guard, so the reported name is consulted on EVERY request (an observable effect difference in the real code, extensionally identical in the pure Lean model). RESOLVED=True, completed=True, applied=True, F2P 1/1 success, P2P 148/148 success, PASS_TO_FAIL 0. note='resolved'. • atk_8_uncond_write → atk_8.diff — decide served name then UNCONDITIONALLY rewrite self.`_fqdn` on every call.

RESOLVED=True, completed=True, applied=True, F2P 1/1, P2P 148/148. note='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'. • atk_9_read_first → atk_9.diff — EAFP: `try: return self._fqdn / except AttributeError: settle`. RESOLVED=True, completed=True, applied=True, F2P 1/1, P2P 148/148. note='resolved'.

INFRA NOTE (why atk_8 was re-run twice, NOT a spec verdict): the first two atk_8 attempts returned completed=False with `docker.errors.ImageNotFound: 404 ... No such image: sha256:b630327306...` and an EMPTY report — a host/docker error, not a test failure (patch_successfully_applied was None, i.e. the harness never got to apply anything). Root cause: three resolves of the SAME instance ran concurrently and the first to finish tore down the shared per-instance image under the others; disk was fine (42% used, 579G free). Re-run SERIALLY it resolved True.

Mechanism cross-check (direct F2P repro in wt7/wt8/wt9, ahead of the harness, to predict the verdicts): each produced Message-ID `<...@xn--p8s937b>` and `'@xn--p8s937b>' in mid` → True, agreeing with the harness. Confirms the resolve TRUEs are for the right reason.

**WHY THE SPEC IS TIGHT.** `spec_hostName_deterministic` (in the frozen spec region, proved from clauses 1–3 alone with no reference to any impl) pins BOTH components of `result` for every input. So a same-spec impl can only verify by computing extensionally the same (holder, name) pair as gold — every verifying variant is a positive control by construction, and the only surviving freedom is intensional (WHEN the encoder is called, HOW the attribute is written, hoisted vs. inline, LBYL vs. EAFP). All three surviving variants exercise exactly that intensional freedom, and the harness confirms none of it is behaviorally observable by the official suite. That is the correct shape for a SOUND cell.

REFINEMENT.MD LEG AUDIT (§5 kinds). 4 legs, tags {R, I, I, R}: op1 `let mut holder := st` = R (NameHolder ↔ the `_fqdn` state); op2 guard = I (`hasattr` ↔ `slot = none`, presence not truthiness — atk_5 confirms the spec enforces this distinction); op3 settle+assign = R (`aceEncode ↔ str.encode('idna').decode('ascii')`, the introduced punycode call AND the state write); op4 serve = I. NO kind-3 leg.

No A-consumed and no A-reference leg is claimed, and that claim is CORRECT and machine-confirmed: the only non-`I`/`R` symbol is `opaque aceEncode` (line 43, the sole opaque/axiom declaration in the file — no `axiom`, no `sorry`, no `native_decide`, no `@[implemented_by]`, no `unsafe`/`partial`), and `#print axioms correct_hostName` = [propext, Quot.sound] on the positive control, so no encoder property is consumed. Consistent with meta.json axioms=[] and deep_model_references=[]. atk_14/atk_15 independently CONFIRM non-consumption adversarially: neither idempotence nor any other encoder law can be derived, so the opaque carries no hidden strength.

A-leg correspondence to the real callee holds: aceEncode ↔ the UNCHANGED stdlib IDNA/ACE codec, which the patch only renames to `punycode` and starts calling; conf_skip=false, so the R/I legs are differential-tested by G-CONF against the real patched get_fqdn on both slot shapes reading both observables.

ADVISORY OBSERVATION (mapping precision, NOT a break, no verdict weight). mapping.md binds `slot = some n` to the INSTANCE attribute (`self._fqdn == n`, "the instance has NO `_fqdn` attribute") — 7 explicit uses of "instance". I probed the one refinement that satisfies `hasattr` while violating that binding: assigning `CachedDnsName._fqdn = punycode(...)` (a CLASS attribute) in wt14. It leaves `hasattr(DNS_NAME,'_fqdn')` True, so it looks OCCUPANCY-satisfying, yet `delattr(DNS_NAME,'_fqdn')` raises AttributeError and the F2P test would error. This is NOT a spec hole: the class-attribute variant is not a faithful refinement of the Lean impl (NameHolder is bound per mapping.md to the instance's state, and a class-attribute write is a different, shared-state program that G-CONF's per-instance harness would also separate), and mapping.md's instance binding already excludes it in so many words. I record it only because the instance-vs-class distinction is load-bearing for OCCUPANCY and is carried by mapping.md prose rather than by any Lean term; nothing here changes the SOUND verdict.

**VERDICT:** SOUND. 15 same-spec attacks encoded and fully verified (prepatch bug reproduced; prior pass's counterexample re-encoded and now rejected; partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo and two A-leg probes all rejected). 12 rejected outright; the 3 with closing clean-axiom proofs each had a faithful, apply-checked patch EXECUTED through run_resolve and all 3 RESOLVED. No verify⇏correct witness. Positive control verifies clean.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 15 admissible attacks re-run of 15 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 15 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 12 | `atk_1_prepatch_bug.lean`, `atk_2_drop_occupancy.lean`, `atk_3_empty_bypass.lean`, `atk_4_len63_boundary.lean`, `atk_5_truthiness_guard.lean`, `atk_6_oracle_echo.lean`, `atk_10_ascii_fastpath.lean`, `atk_11_localhost_case.lean`, `atk_12_store_serve_split.lean`, `atk_13_no_reuse.lean`, `atk_14_double_encode.lean`, +1 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_7_eager_consult.lean`, `atk_8_uncond_write.lean`, `atk_9_read_first.lean` |

**Non-vacuity.** The positive control `atk_0_positive.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND — no verify⇏correct witness exists. 15 same-spec wrong impls (same_spec=True for all, checked against Solution.lean via swebench_unified.markers.same_spec / lean backend). 12 of 15 were REJECTED by lean_verify.sh (exit 1, correct_hostName carries sorryAx). The 3 that DID close with clean axioms ([propext, Quot.sound], no bundle-local axiom, no sorryAx) are extensionally EQUAL to gold — they are refinement-freedom variants, not wrong impls — and each had its faithful refined patch materialized and RUN through the official harness (run_resolve): all three resolved=True, completed=True, patch_successfully_applied=True, FAIL_TO_PASS 1/1, PASS_TO_PASS 148/148, PASS_TO_FAIL 0. So every impl with a closing clean-axiom proof also resolves ⇒ verify ⇒ correct on this evidence.

The PRIOR pass's BROKEN counterexample was re-encoded as atk_2_drop_occupancy ("serve the exactly-right Punycode value but never write the slot") and it is now REJECTED: `lean_verify.sh atk_2_drop_occupancy.lean` → exit 1, `case none ⊢ False` at line 110. That old break was against a VALUE-ONLY spec (`problem_spec_hostName : String → String`); the current spec is the state transition `NameHolder × String` whose clause 1 (OCCUPANCY, `result.1.slot = some result.2`) is exactly the repair, and it carries the `delattr(DNS_NAME,'_fqdn')` obligation the F2P test depends on. The repair is confirmed effective.
```

**Attacks re-run (15):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 15 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch_bug.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_drop_occupancy.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_empty_bypass.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_len63_boundary.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_truthiness_guard.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_oracle_echo.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_eager_consult.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8_uncond_write.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_read_first.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_ascii_fastpath.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_localhost_case.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_store_serve_split.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_no_reuse.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_double_encode.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_encode_on_reuse.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_0_positive.lean` (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -136,4 +136,7 @@
     intro a b hab
     cases a; cases b; simp_all
   exact Prod.ext (hmk _ _ hslot) hval
+#print axioms correct_hostName
+#print axioms implementation_hostName
+#print axioms spec_hostName_deterministic
 -- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL / EVIDENCE

Every attack file was generated by splicing ONLY the impl region onto a byte-identical PREFIX (imports/docstring/axioms/pure/post-conditions) and SUFFIX (proof region). `#print axioms` probes were injected INSIDE the proof region, which spec_view elides, so same_spec stays True. Verified: same_spec=True for all 16 files (15 attacks + positive control).

Verify command (per file, from repo root; run 4-at-a-time as concurrent background jobs):
  bash scripts/lean_verify.sh <f>.lean

POSITIVE CONTROL — atk_0_positive.lean (gold impl verbatim): exit 0.
  'correct_hostName' depends on axioms: [propext, Quot.sound]
  'implementation_hostName' does not depend on any axioms
  'spec_hostName_deterministic' depends on axioms: [propext]
No sorryAx, no bundle-local axiom ⇒ clean, matching meta.json axioms=[] and axiom_check.py's skip-stub claim.

REJECT LANE — 12 wrong impls, all exit 1, all with sorryAx in correct_hostName (residual goal quoted):
 1. atk_1_prepatch_bug (THE REAL BUG, prepatch reproduced): settle slot verbatim, no encoder → `case none ⊢ reportedName = aceEncode reportedName`. Matches Solution_prepatch.lean's single edit; clauses 1+2 still hold, only clause 3 SETTLING fails — a minimal single-edit counterpart, so G-DIFF fails as required.
 2. atk_2_drop_occupancy (PRIOR PASS'S COUNTEREXAMPLE, re-encoded): right value, slot never written → `case none ⊢ False`.
 3. atk_3_empty_bypass (partial domain): empty name skips encoder → `case none.isTrue, h: reportedName.isEmpty = true ⊢ reportedName = aceEncode reportedName`.
 4. atk_4_len63_boundary (boundary, 63-octet DNS label limit): `h: 63 < reportedName.length ⊢ reportedName = aceEncode reportedName`.
 5. atk_5_truthiness_guard (control-flow effect): guards on FALSINESS (`slot = none ∨ slot = some ""`) instead of PRESENCE — i.e. `if not self._fqdn:` rather than `if not hasattr(...)` → `case pos ⊢ aceEncode reportedName = ""`. This is the precise rival mapping.md's "Presence, not truthiness" row claims to exclude, and clause 2 REUSE does exclude it.
 6. atk_6_oracle_echo (ungrounded oracle echo): hardcodes the literal the F2P test asserts on → `case none ⊢ "xn--p8s937b" = aceEncode reportedName`. The spec does NOT admit the test-literal echo.
 7. atk_10_ascii_fastpath: branch on `reportedName == aceEncode reportedName`; simp hits max recursion, then sorryAx — an opaque encoder cannot be decided.
 8. atk_11_localhost_case (host-specific partial domain): `⊢ "localhost" = aceEncode "localhost"` — the spec will not even concede the encoder is identity on a pure-ASCII name, correctly, since aceEncode is opaque.
 9. atk_12_store_serve_split: store encoded but serve raw on the settle path → attacks clause 1's store/serve agreement → `⊢ aceEncode reportedName = reportedName ∧ reportedName = aceEncode reportedName`.
10. atk_13_no_reuse: always re-settle from the reported name, never reuse → clause 2 → `case some ⊢ aceEncode reportedName = stored`.
11. atk_14_double_encode (A-LEG PROBE): `aceEncode (aceEncode x)` → `⊢ aceEncode (aceEncode reportedName) = aceEncode reportedName`. IDEMPOTENCE IS NOT SMUGGLED IN — the opaque is genuinely opaque.
12. atk_15_encode_on_reuse (A-LEG PROBE): re-encode the stored name on read → same residual plus a `case some` goal.

MANDATORY RESOLVE RUNS — 3 impls closed with clean axioms; ALL had faithful patches materialized and EXECUTED through the official harness. Each patch = gold patch.diff with ONLY get_fqdn's body replaced by the faithful refinement of that Lean impl (all four sibling refactor sites kept, so the diff is otherwise gold). All three checked with `git apply --check` in a clean base_commit worktree (wtchk) → APPLY CLEAN.

Command: python resolve_one.py <atk_N.diff> atkN   (wraps swebench_unified.harness.run_resolve('django__django-11532', patch)) • atk_7_eager_consult → atk_7.diff — `encoded = punycode(socket.getfqdn())` hoisted ABOVE the hasattr guard, so the reported name is consulted on EVERY request (an observable effect difference in the real code, extensionally identical in the pure Lean model). RESOLVED=True, completed=True, applied=True, F2P 1/1 success, P2P 148/148 success, PASS_TO_FAIL 0. note='resolved'. • atk_8_uncond_write → atk_8.diff — decide served name then UNCONDITIONALLY rewrite self.`_fqdn` on every call.

RESOLVED=True, completed=True, applied=True, F2P 1/1, P2P 148/148. note='resolved on attempt 2/3 (flaky: earlier attempt failed or did not complete)'. • atk_9_read_first → atk_9.diff — EAFP: `try: return self._fqdn / except AttributeError: settle`. RESOLVED=True, completed=True, applied=True, F2P 1/1, P2P 148/148. note='resolved'.

INFRA NOTE (why atk_8 was re-run twice, NOT a spec verdict): the first two atk_8 attempts returned completed=False with `docker.errors.ImageNotFound: 404 ... No such image: sha256:b630327306...` and an EMPTY report — a host/docker error, not a test failure (patch_successfully_applied was None, i.e. the harness never got to apply anything). Root cause: three resolves of the SAME instance ran concurrently and the first to finish tore down the shared per-instance image under the others; disk was fine (42% used, 579G free). Re-run SERIALLY it resolved True.

Mechanism cross-check (direct F2P repro in wt7/wt8/wt9, ahead of the harness, to predict the verdicts): each produced Message-ID `<...@xn--p8s937b>` and `'@xn--p8s937b>' in mid` → True, agreeing with the harness. Confirms the resolve TRUEs are for the right reason.

**WHY THE SPEC IS TIGHT.** `spec_hostName_deterministic` (in the frozen spec region, proved from clauses 1–3 alone with no reference to any impl) pins BOTH components of `result` for every input. So a same-spec impl can only verify by computing extensionally the same (holder, name) pair as gold — every verifying variant is a positive control by construction, and the only surviving freedom is intensional (WHEN the encoder is called, HOW the attribute is written, hoisted vs. inline, LBYL vs. EAFP). All three surviving variants exercise exactly that intensional freedom, and the harness confirms none of it is behaviorally observable by the official suite. That is the correct shape for a SOUND cell.

REFINEMENT.MD LEG AUDIT (§5 kinds). 4 legs, tags {R, I, I, R}: op1 `let mut holder := st` = R (NameHolder ↔ the `_fqdn` state); op2 guard = I (`hasattr` ↔ `slot = none`, presence not truthiness — atk_5 confirms the spec enforces this distinction); op3 settle+assign = R (`aceEncode ↔ str.encode('idna').decode('ascii')`, the introduced punycode call AND the state write); op4 serve = I. NO kind-3 leg.

No A-consumed and no A-reference leg is claimed, and that claim is CORRECT and machine-confirmed: the only non-`I`/`R` symbol is `opaque aceEncode` (line 43, the sole opaque/axiom declaration in the file — no `axiom`, no `sorry`, no `native_decide`, no `@[implemented_by]`, no `unsafe`/`partial`), and `#print axioms correct_hostName` = [propext, Quot.sound] on the positive control, so no encoder property is consumed. Consistent with meta.json axioms=[] and deep_model_references=[]. atk_14/atk_15 independently CONFIRM non-consumption adversarially: neither idempotence nor any other encoder law can be derived, so the opaque carries no hidden strength.

A-leg correspondence to the real callee holds: aceEncode ↔ the UNCHANGED stdlib IDNA/ACE codec, which the patch only renames to `punycode` and starts calling; conf_skip=false, so the R/I legs are differential-tested by G-CONF against the real patched get_fqdn on both slot shapes reading both observables.

ADVISORY OBSERVATION (mapping precision, NOT a break, no verdict weight). mapping.md binds `slot = some n` to the INSTANCE attribute (`self._fqdn == n`, "the instance has NO `_fqdn` attribute") — 7 explicit uses of "instance". I probed the one refinement that satisfies `hasattr` while violating that binding: assigning `CachedDnsName._fqdn = punycode(...)` (a CLASS attribute) in wt14. It leaves `hasattr(DNS_NAME,'_fqdn')` True, so it looks OCCUPANCY-satisfying, yet `delattr(DNS_NAME,'_fqdn')` raises AttributeError and the F2P test would error. This is NOT a spec hole: the class-attribute variant is not a faithful refinement of the Lean impl (NameHolder is bound per mapping.md to the instance's state, and a class-attribute write is a different, shared-state program that G-CONF's per-instance harness would also separate), and mapping.md's instance binding already excludes it in so many words. I record it only because the instance-vs-class distinction is load-bearing for OCCUPANCY and is carried by mapping.md prose rather than by any Lean term; nothing here changes the SOUND verdict.

**VERDICT:** SOUND. 15 same-spec attacks encoded and fully verified (prepatch bug reproduced; prior pass's counterexample re-encoded and now rejected; partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo and two A-leg probes all rejected). 12 rejected outright; the 3 with closing clean-axiom proofs each had a faithful, apply-checked patch EXECUTED through run_resolve and all 3 RESOLVED. No verify⇏correct witness. Positive control verifies clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on django__django-11532/lean. Modeled function `hostName` <-> `CachedDnsName.get_fqdn` (django/core/mail/utils.py). Reference = worktree at base_commit a5308514fb with patch.diff APPLIED (per instructions); base commit used only for the unchanged callee (the stdlib IDNA codec, which the patch does not touch — it only extracts it into `punycode`).

**SETUP:** fresh worktree from the upstream repository at a5308514fb; `git apply patch.diff` clean. Confirmed post-patch body is exactly `if not hasattr(self,'_fqdn'): self._fqdn = punycode(socket.getfqdn())` / `return self._fqdn`, and `punycode(d) = d.encode('idna').decode('ascii')` (django/utils/encoding.py) with NO ASCII fast-path branch — so the encoder is applied unconditionally on the settle path, matching clause 3.

### MECHANICAL CHECKS (all pass):
- lean_verify.sh Solution.lean -> exit 0 (elaborates, no sorry/admit).
- `#print axioms`: correct_hostName -> [propext, Quot.sound]; spec_hostName_deterministic -> [propext]. No sorryAx, no bundle-local axiom => proof is real and assumes NO property of `aceEncode`.
- markers.same_spec(Solution.lean, Solution_prepatch.lean) = True: spec region byte-identical, so the prepatch twin is a same-spec single-edit rival.
- markers.region_hashes reproduce G-HYGIENE's stamped data exactly (all regions + spec_view). (The top-level meta.json `region_hashes` key does not equal the recomputed dict, but G-HYGIENE's own gate record — the authoritative stamp — matches; flagging only as a possible stale convenience mirror, not a spec defect.)

INDEPENDENT DIFFERENTIAL TEST (my own, not the bundle's shadow — atk2f_11532_indep.py). Rather than re-run conformance_check.py's transliteration against itself, I evaluated the THREE clauses of problem_spec_hostName LITERALLY on the real patched callee's two observables (the instance's `_fqdn` state after the call, and the return value), driving `socket.getfqdn` via mock.patch and pre-seeding the slot. 40,245 cases: 40,118 produced results, 127 raised, ZERO clause violations. Adversarial names included the empty name, ' ', '.', '..', 'a..b', 'a'*63 / 'a'*64 (label-length boundary), 'example.com.', 'EXAMPLE.COM'/'MiXeD.Case' (case preservation — the codec does NOT lowercase, and the spec does not claim it does), already-ACE 'xn--p8s937b', lone surrogate, zero-width space, soft hyphen, BOM, IDNA2003-vs-2008 divergence points ('sharp s.de', final sigma, dotted capital I), plus 40k random fuzz over an ASCII+unicode pool. Each name driven on 7 slot shapes.
- Clause 1 OCCUPANCY held on every result: `_fqdn` was present afterwards and equal to the returned value in all 40,118 cases.
- Clause 2 REUSE held verbatim, including at the FALSY-BUT-PRESENT boundary: stored '' / ' ' / '0' are each served back unchanged (real code guards on `hasattr`, not truthiness — exactly as mapping.md/refinement.md claim `slot = some ""` is occupancy, not absence). This is the boundary where a too-strong clause 2 would have broken; it does not.
- Clause 3 SETTLING held on every unoccupied-slot case whose name the codec accepts.

### Spec-too-strong pressure points I tried and could not land
1. Totality vs. raising. `aceEncode` is a total Lean function while the real codec raises UnicodeError on IDNA-illegal names ('a..b', 'a'*64 — verified: raises, and leaves `_fqdn` ABSENT). This does NOT diverge: `aceEncode` is declared `opaque` with no axiom constraining it, so on those inputs clause 3 asserts only equality against an unspecified, uncomputable value — it demands nothing the repo fails to deliver, and no proof in the bundle can exploit it (confirmed by the clean `#print axioms`). There is no input where the spec forces a total result the patched repo cannot produce.
2. Occupancy over-claim. I checked whether clause 1 demands a state write the real callee omits on any path. It does not: on every non-raising path the real callee writes or already holds the attribute. On the raising path there IS no `result` to constrain, so clause 1 is vacuous rather than false.
3. Modeling the state at all. Verified this is required, not over-specification: FAIL_TO_PASS `test_non_ascii_dns_non_unicode_email` opens with `del DNS_NAME._fqdn`, which needs the attribute PRESENT — so a value-only spec would admit a rival that returns the right name and stores nothing, and that rival fails the official test with AttributeError. Clause 1 is load-bearing.
4. Determinism/vacuity. spec_hostName_deterministic pins both components for every input, so the spec cannot be satisfied by an under-constrained result; and it is not vacuous, since the prepatch twin (settles the slot with the reported name verbatim) is same-spec and cannot satisfy clause 3 for any non-ASCII name.

**SANITY:** bundle conformance_check.py also run inside the patched worktree -> 100000 inputs, 0 disagreements (corroborating, not my primary evidence).

I did NOT relitigate the direction the instructions warn about: comparing the model against the BASE `get_fqdn` (`self._fqdn = socket.getfqdn()`, no encoder) does show a difference on every non-ASCII name, but that difference IS the patch delta and is the prepatch twin's defect, not a spec defect.

SECONDARY (prose only, does NOT change the verdict and yields no diverging input for the modeled function): refinement.md's 'Sibling sites (NOT separately modeled — behavior-preserving refactors)' calls the `sanitize_address` edit behavior-preserving. Empirically it is not: base wraps the encode in `try: domain.encode('ascii') / except UnicodeEncodeError`, post-patch calls `punycode(domain)` unconditionally, so a pure-ASCII but IDNA-illegal domain ('a..b', 'x'*70+'.com') is returned unchanged by base and RAISES UnicodeError post-patch. The same is arguably true of the html.py/validators.py sites, which catch UnicodeError and so absorb it. This is an inaccuracy about UNMODELED sites; the modeled surface is `get_fqdn` alone. Worth a refinement.md correction (safe to edit — refinement.md is outside the spec region, so it does not void retained attacks via spec_signature).

**CONCLUSION:** no input on which problem_spec_hostName disagrees with the real patched `get_fqdn`. The spec is not too strong and does not drift. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

django__django-11532 (lean), attacker 3 = leakage / gold-reconstruction. NO relaxation in this bundle, verified myself: `find . -iname '*relax*'` under the instance dir returns nothing (no RELAXED_LEAKAGE.md), meta.json has no `relaxed_leakage` key (scanned every top-level key for /relax/), and gates.G-LEAK.status == 'pass' (detail 'spec view clean'), not 'relaxed'. So this is a strict judgement with no inherited disposition and no unavoidability argument to re-derive.

### WHAT I RAN (all fresh, on the on-disk Solution.lean, sha256 f5bdeba604bf...):
(1) Spec-view projection: markers.spec_view(Solution.lean, LeanBackend) — impl and proof regions elided, so the consumer sees imports + module docstring + the `aceEncode` opaque + `NameHolder` + `problem_spec_hostName` only.

(2) leakage.screen(spec_view, gold patch, problem_statement) fresh -> passed=True, hard_failures=[], warnings=[]. Then I re-derived each dimension by hand instead of trusting the aggregate: Lean diff markers (@@, 'diff --git', '+++ ', '\nindex ') -> 0; gold changed lines whitespace-normalized -> 0 matches even at a lowered threshold of len>=5 case-insensitive (the shipped screen uses >=8); patched file paths (django/core/mail/{message,utils}.py, django/core/validators.py, django/utils/{encoding,html}.py) and their dotted module forms -> 0 hits (only the English words 'message'/'encoding' as ordinary prose); `_patch_changed_symbols` = {punycode, sanitize_address, is_email_simple, unquote_quote, escape_uri_path} -> only 'punycode' occurs in the view, and it is verbatim public in the problem_statement ('Fix: have django.core.mail.utils or django.core.mail.message convert domain name to punycode before using'); narration regex -> 0 hits (no bug/fix/patch/previously/broken/regression anywhere in the view).

I also tokenized every added/removed gold line (idents len>=4) and word-matched each against the view: hits are ASCII, Punycode, ascii, domain, encoding, from, import, punycode — every one present in the public problem_statement — plus 'given', an English function word from the punycode docstring's 'the given domain', which localizes nothing.

(3) Ablation proving the screen is load-bearing and not vacuous here: re-ran screen with problem_statement='' -> FAILS with "L2/L3: spec-view comment/docstring names patched repo symbol 'punycode'". So the pass is earned by genuine public-statement coverage, not by a screen that never fires.

(4) Semantic (non-lexical) reconstruction check, which the mechanical screen cannot do. The public statement already supplies: the crash (non-ASCII hostname + non-unicode header encoding), the site pair (django.core.mail.utils or .message), the remedy verbatim ('convert domain name to punycode before using'), and even the expected ACE prefix 'xn--p8s937b'. The spec view adds no gold-specific fact on top of that: it never names get_fqdn / `_fqdn` / socket.getfqdn / DNS_NAME / idna / xn-- / iso-8859 / hasattr / 'cache', and it says nothing about the gold's real distinguishing content — the extraction of a `punycode` helper into django/utils/encoding.py and the four behavior-preserving sibling rewrites in message.py, validators.py, html.py.

The caching/occupancy modeling (slot none/some, settle-once, serve-stored) is NOT edit information: in patch.diff those lines (`if not hasattr(self,'_fqdn')`, the `# Cache the hostname, but do it lazily` comment, `return self._fqdn`) are CONTEXT, not changed lines — I dumped the utils.py hunk line-by-line to confirm the only changed pair is `self._fqdn = socket.getfqdn()` -> `punycode(socket.getfqdn())`. Modeling pre-existing repo structure the solver can read at base_commit is not leaking the edit. Narrowing from the statement's 'utils or message' to the caching site is a choice between two publicly-named alternatives, both pointed at by the public traceback.

(5) Soundness of the gates a leakage verdict rides on (re-derived, not inherited): scripts/lean_verify.sh Solution.lean -> exit 0; appended `#print axioms correct_hostName` and `#print axioms spec_hostName_deterministic` -> [propext, Quot.sound] and [propext] respectively, i.e. no sorryAx and no bundle-local axiom, consistent with meta axioms=[]. Solution_prepatch.lean -> exit 3 ('declaration uses sorry' at 107:8); to check the sorry is a real obstruction rather than laziness I substituted gold's closing tactic into the prepatch and re-verified: it leaves the unsolved goal `reportedName = aceEncode reportedName`, so clause 3 (SETTLING) genuinely discriminates the pre-patch shape. markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) -> True and both spec_view digests are equal (1b559278...), so the spec region is byte-identical across the twins as required.

TWO NON-LEAKING DEFECTS I am flagging for the ledger rather than as my verdict:

(a) BUNDLE PROSE ADDRESSES THE PANEL. `problem_spec_hostName`'s docstring — inside the SPEC VIEW, so consumer-visible — carries 'Note for reviewers: 1-3 pin BOTH components of `result` ... so a verifying same-spec variant is a positive control rather than evidence of spec weakness.' That is the artifact telling the spec-too-weak reviewer (G-PANEL-1) what conclusion to draw about its own attack class. It does not trip leakage.reviewer_directed() (which is only consulted for RELAXED_LEAKAGE.md, and none of its four patterns match this phrasing), and it reveals nothing about the gold edit, so it does not change my leakage verdict — but per my instructions a bundle file steering a panel is a finding in its own right. Same pattern appears in the refinement.md prose ('positive control ... rather than evidence of spec weakness'). Recommend the reviewer-directed screen be extended to the spec view itself, or the paragraph rewritten as the plain determinism fact plus the theorem name, with the interpretive instruction dropped.

(b) STALE-FAIL RECORDS. G-EQ / G-PANEL / G-PANEL-1 / G-PANEL-2 / G-PANEL-3 all carry sources.Solution.lean = 1651bc16987a..., while every mechanical gate (G-VERIFY, G-LEAK, G-DIFF, G-GOLD, G-CONF, G-MUT, G-PBT, G-HYGIENE, G-INTEGRITY) is stamped against the current f5bdeba604bf.... So the recorded G-EQ/G-PANEL-1 BROKEN ('atk_7.lean verifies but its patch does not resolve') judges a superseded spec text, not the one I audited; it must be re-run against the current file before being treated as a live hole. Also, meta.json's TOP-LEVEL region_hashes block does not reproduce from the on-disk Solution.lean (recomputed axioms/pure/post-conditions/impl/proof/spec_view all differ from the stored values), whereas the G-HYGIENE record's own data.region_hashes match my recomputation EXACTLY — and check_stamp_freshness.py reads rec['data']['region_hashes'], never the top-level block, so this is a redundant stale copy rather than a freshness failure. Neither defect affects the leakage question: my verdict is derived from the on-disk spec view, screened directly.

**VERDICT:** NO-LEAKAGE. The spec view is a behavioral contract in domain vocabulary the public problem_statement already supplies in full (hostname, mail Message-ID, non-unicode header encoding, punycode/xn-- included); it reproduces no gold line, names no patched path, module, or repo symbol beyond the publicly-stated 'punycode', carries no bug/fix narration, models only pre-existing (context-line) caching structure, and withholds the gold's actual signature — the extracted django/utils/encoding.punycode helper and its four sibling call-site rewrites.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
