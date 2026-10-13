# P2 adversarial audit — django__django-15525

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 14 same-spec attacks (same_spec=True for all; only the impl region edited, plus the proof where a rival needed its own tactic script). 7 were REJECTED by the frozen obligation; 7 VERIFIED with clean axioms [propext, Quot.sound] and no sorry. For ALL 7 verifying attacks I materialized a faithful patch, confirmed `git apply --check` exit 0 at base_commit, and RAN it through the official harness: all 7 RESOLVED (resolved=True, completed=True, patch_successfully_applied=True, F2P 1/1, P2P 53/53, attempts=1). No impl with a closing clean-axiom proof has a faithful patch that fails to resolve, so verify=>correct holds on every attack I could construct.

GOLD CONTROL CERTIFIED FIRST (and resolves serialized, one run at a time): gold.diff == the bundle's patch.diff modulo headers, resolved=True F2P 1/1 P2P 53/53 in 50.2s. Without that the attack resolves would mean nothing.

MY SHARPEST NEW ATTACKS were two VACUOUS-DEAD-BRANCH exploits against derivationAvailability, a class the prior passes did not try. Availability is a biconditional-shaped assumption, so each half makes one arm of a RECOVERED derivation unreachable IN THE MODEL, free to carry arbitrary garbage:
  * atk_14 exploits the hasKey=true conjunct (the step SUCCEEDS on the target-store record), so the ERROR arm is dead and writes pk=424242. In the REPO that arm is LIVE: natural_key() can raise on the target-store record too (the FK referent may be absent there as well), where gold PROPAGATES DoesNotExist. Measured: shape guarded_unresolvable -> atk_14 returns pk=424242, gold RAISES.
  * atk_13 exploits the hasKey=false conjunct (the step errors on EVERY record), so the ok arm is dead and writes pk=424242. In the REPO hasKey=false covers exactly the mixed state mapping.md ADMITS the single `hasKey` Bool cannot express -- Model.natural_key present, manager without get_by_natural_key -- where natural_key() SUCCEEDS. Measured: shape mixed_resolvable -> atk_13 returns pk=424242, gold leaves pk=None.
Both verify (exit 0), both have clean axioms, both needed hand-written proofs, and BOTH RESOLVED. They are latent permissiveness the P2P set never loads, not verify=>correct failures.

I also re-encoded the counterexamples prior passes named and confirmed the bundle's zeta-erasure defense rather than taking it on trust: rfl_impl{SEVEN,EIGHT,NINE,ELEVEN,TWELVE}.lean ALL exit 1 ('Type mismatch rfl'), so every one of my verifying rivals is a genuinely DISTINCT function -- none is the frozen gold up to definitional unfolding. So unlike the dropped-value shapes a prior pass mis-scored as breaks, these are real candidate rivals, and they still resolve.

atk_8 (BOUND derivation hoisted above the data.id test, the residual weakness the last pass flagged) re-confirmed: verifies, clean axioms, not zeta-erasure, DIVERGES from gold out of harness (shape pk_given -> atk_8 RAISES where gold returns pk=7), and still RESOLVED. atk_12 (unconditional derivation + recovered failure) likewise diverges on mixed_resolvable (AttributeError vs gold None) and RESOLVED.

Rejections confirm the spec's load-bearing clauses: atk_1 (prepatch bug re-encoded, derive on the default-store record) fails exactly as the prepatch twin does; atk_6 shows (C2) pins WHICH key feeds op #5, not merely that some key was derived; atk_4 pins the lookup store; atk_2 the hasKey conjunct; atk_3/atk_5/atk_10 the coercion, the not-found frame, and the derived-from record.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,9 +132,8 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
-    let mut obj : Record := { payload := data.payload, store := defaultStore }
-    obj := { obj with store := store }
+    -- BUG (prepatch): never establish the target store before deriving the key
+    let obj : Record := { payload := data.payload, store := defaultStore }
     let key ← derive obj
     match lookupByKey store key with
     | some raw => return { data with id := some (coerceId raw) }
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,8 +131,7 @@
 def implementation_resolveRecord
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
-  if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
+  if data.id = none then
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,12 +132,11 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
     match lookupByKey store key with
-    | some raw => return { data with id := some (coerceId raw) }
+    | some raw => return { data with id := some raw }
     | none     => return data
   return data
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,11 +132,10 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
-    match lookupByKey store key with
+    match lookupByKey defaultStore key with
     | some raw => return { data with id := some (coerceId raw) }
     | none     => return data
   return data
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,13 +132,12 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
     match lookupByKey store key with
     | some raw => return { data with id := some (coerceId raw) }
-    | none     => return data
+    | none     => return { data with id := some 0 }
   return data
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,11 +132,12 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
+    -- bind a derivation on the DEFAULT-store record and use ITS key downstream
+    let staleKey ← derive obj
     obj := { obj with store := store }
     let key ← derive obj
-    match lookupByKey store key with
+    match lookupByKey store staleKey with
     | some raw => return { data with id := some (coerceId raw) }
     | none     => return data
   return data
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,13 +132,15 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
-    let key ← derive obj
-    match lookupByKey store key with
-    | some raw => return { data with id := some (coerceId raw) }
-    | none     => return data
+    -- run the derivation, but RECOVER from "no key came back" instead of propagating
+    match derive obj with
+    | Except.ok key =>
+      match lookupByKey store key with
+      | some raw => return { data with id := some (coerceId raw) }
+      | none     => return data
+    | Except.error _ => return data
   return data
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,15 +131,19 @@
 def implementation_resolveRecord
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
-  if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
+  if hasKey = true then
+    -- ops #2/#3 then a BOUND op #4, all ABOVE the data.id test
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
-    match lookupByKey store key with
-    | some raw => return { data with id := some (coerceId raw) }
-    | none     => return data
-  return data
+    if data.id = none then
+      match lookupByKey store key with
+      | some raw => return { data with id := some (coerceId raw) }
+      | none     => return data
+    else
+      return data
+  else
+    return data
 -- impl-end
 
 -- proof-start
@@ -150,37 +154,45 @@
         (implementation_resolveRecord data store hasKey derive) := by
   intro data store hasKey derive havail
   unfold problem_spec_resolveRecord implementation_resolveRecord
-  by_cases h : (data.id = none ∧ hasKey = true)
-  · rw [if_pos h]
-    obtain ⟨key, hk⟩ := havail.1 h.2
-    simp only [hk, bind, Except.bind]
-    cases hl : lookupByKey store key with
-    | none =>
+  by_cases hk : hasKey = true
+  · rw [if_pos hk]
+    obtain ⟨key, hkey⟩ := havail.1 hk
+    simp only [hkey, bind, Except.bind]
+    by_cases hid : data.id = none
+    · rw [if_pos hid]
+      cases hl : lookupByKey store key with
+      | none =>
+        refine ⟨⟨data, rfl⟩, ?_⟩
+        intro res hres
+        simp only [pure, Except.pure, Except.ok.injEq] at hres
+        subst hres
+        refine ⟨rfl, ?_, ?_⟩
+        · intro _ key₁ hkey₁
+          simp only [Except.ok.injEq] at hkey₁
+          subst hkey₁
+          rw [hl]
+        · intro hc; exact absurd ⟨hid, hk⟩ hc
+      | some raw =>
+        refine ⟨⟨{ id := some (coerceId raw), payload := data.payload }, rfl⟩, ?_⟩
+        intro res hres
+        simp only [pure, Except.pure, Except.ok.injEq] at hres
+        subst hres
+        refine ⟨rfl, ?_, ?_⟩
+        · intro _ key₁ hkey₁
+          simp only [Except.ok.injEq] at hkey₁
+          subst hkey₁
+          rw [hl]
+        · intro hc; exact absurd ⟨hid, hk⟩ hc
+    · rw [if_neg hid]
+      simp only [pure, Except.pure, Except.ok.injEq]
       refine ⟨⟨data, rfl⟩, ?_⟩
       intro res hres
-      simp only [pure, Except.pure, Except.ok.injEq] at hres
       subst hres
-      refine ⟨rfl, ?_, ?_⟩
-      · intro _ key₁ hkey
-        simp only [Except.ok.injEq] at hkey
-        subst hkey
-        rw [hl]
-      · intro hc; exact absurd h hc
-    | some raw =>
-      refine ⟨⟨{ id := some (coerceId raw), payload := data.payload }, rfl⟩, ?_⟩
-      intro res hres
-      simp only [pure, Except.pure, Except.ok.injEq] at hres
-      subst hres
-      refine ⟨rfl, ?_, ?_⟩
-      · intro _ key₁ hkey
-        simp only [Except.ok.injEq] at hkey
-        subst hkey
-        rw [hl]
-      · intro hc; exact absurd h hc
-  · rw [if_neg h]
-    simp only [bind, Except.bind, pure, Except.pure, Except.ok.injEq]
+      exact ⟨rfl, fun hc => absurd hc.1 hid, fun _ => rfl⟩
+  · rw [if_neg hk]
+    simp only [pure, Except.pure, Except.ok.injEq]
     refine ⟨⟨data, rfl⟩, ?_⟩
     intro res hres
     subst hres
-    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
+    exact ⟨rfl, fun hc => absurd hc.2 hk, fun _ => rfl⟩
 -- proof-end
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,9 +132,10 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
+    -- an EXTRA, genuinely bound run of the derivation step on the same record
+    let _key0 ← derive obj
     let key ← derive obj
     match lookupByKey store key with
     | some raw => return { data with id := some (coerceId raw) }
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,8 +132,7 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
-    let mut obj : Record := { payload := data.payload, store := defaultStore }
+    let mut obj : Record := { payload := data.payload.reverse, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
     match lookupByKey store key with
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,13 +132,13 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
-    match lookupByKey store key with
-    | some raw => return { data with id := some (coerceId raw) }
-    | none     => return data
+    -- echo the oracle's match instead of branching on the lookup
+    return { data with id := (match lookupByKey store key with
+                              | some raw => some (coerceId raw)
+                              | none     => data.id) }
   return data
 -- impl-end
 
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -131,15 +131,17 @@
 def implementation_resolveRecord
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
-  if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
-    let mut obj : Record := { payload := data.payload, store := defaultStore }
-    obj := { obj with store := store }
-    let key ← derive obj
-    match lookupByKey store key with
-    | some raw => return { data with id := some (coerceId raw) }
-    | none     => return data
-  return data
+  -- run the derivation on the target-store record UNCONDITIONALLY, and
+  -- RECOVER from "no key came back" instead of letting it propagate
+  match derive { payload := data.payload, store := store } with
+  | Except.ok key =>
+    if data.id = none then
+      match lookupByKey store key with
+      | some raw => return { data with id := some (coerceId raw) }
+      | none     => return data
+    else
+      return data
+  | Except.error _ => return data
 -- impl-end
 
 -- proof-start
@@ -150,37 +152,48 @@
         (implementation_resolveRecord data store hasKey derive) := by
   intro data store hasKey derive havail
   unfold problem_spec_resolveRecord implementation_resolveRecord
-  by_cases h : (data.id = none ∧ hasKey = true)
-  · rw [if_pos h]
-    obtain ⟨key, hk⟩ := havail.1 h.2
-    simp only [hk, bind, Except.bind]
-    cases hl : lookupByKey store key with
-    | none =>
+  by_cases hk : hasKey = true
+  · obtain ⟨key, hkey⟩ := havail.1 hk
+    simp only [hkey, bind, Except.bind]
+    by_cases hid : data.id = none
+    · rw [if_pos hid]
+      cases hl : lookupByKey store key with
+      | none =>
+        refine ⟨⟨data, rfl⟩, ?_⟩
+        intro res hres
+        simp only [pure, Except.pure, Except.ok.injEq] at hres
+        subst hres
+        refine ⟨rfl, ?_, ?_⟩
+        · intro _ key₁ hkey₁
+          simp only [Except.ok.injEq] at hkey₁
+          subst hkey₁
+          rw [hl]
+        · intro hc; exact absurd ⟨hid, hk⟩ hc
+      | some raw =>
+        refine ⟨⟨{ id := some (coerceId raw), payload := data.payload }, rfl⟩, ?_⟩
+        intro res hres
+        simp only [pure, Except.pure, Except.ok.injEq] at hres
+        subst hres
+        refine ⟨rfl, ?_, ?_⟩
+        · intro _ key₁ hkey₁
+          simp only [Except.ok.injEq] at hkey₁
+          subst hkey₁
+          rw [hl]
+        · intro hc; exact absurd ⟨hid, hk⟩ hc
+    · rw [if_neg hid]
+      simp only [pure, Except.pure, Except.ok.injEq]
       refine ⟨⟨data, rfl⟩, ?_⟩
       intro res hres
-      simp only [pure, Except.pure, Except.ok.injEq] at hres
       subst hres
-      refine ⟨rfl, ?_, ?_⟩
-      · intro _ key₁ hkey
-        simp only [Except.ok.injEq] at hkey
-        subst hkey
-        rw [hl]
-      · intro hc; exact absurd h hc
-    | some raw =>
-      refine ⟨⟨{ id := some (coerceId raw), payload := data.payload }, rfl⟩, ?_⟩
-      intro res hres
-      simp only [pure, Except.pure, Except.ok.injEq] at hres
-      subst hres
-      refine ⟨rfl, ?_, ?_⟩
-      · intro _ key₁ hkey
-        simp only [Except.ok.injEq] at hkey
-        subst hkey
-        rw [hl]
-      · intro hc; exact absurd h hc
-  · rw [if_neg h]
-    simp only [bind, Except.bind, pure, Except.pure, Except.ok.injEq]
+      exact ⟨rfl, fun hc => absurd hc.1 hid, fun _ => rfl⟩
+  · have hf : hasKey = false := by
+      cases hasKey with
+      | true => exact absurd rfl hk
+      | false => rfl
+    have herr := havail.2 hf { payload := data.payload, store := store }
+    simp only [herr, bind, Except.bind, pure, Except.pure, Except.ok.injEq]
     refine ⟨⟨data, rfl⟩, ?_⟩
     intro res hres
     subst hres
-    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
+    exact ⟨rfl, fun hc => absurd hc.2 hk, fun _ => rfl⟩
 -- proof-end
```

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,14 +132,20 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
     let key ← derive obj
     match lookupByKey store key with
     | some raw => return { data with id := some (coerceId raw) }
     | none     => return data
-  return data
+  else if hasKey = true then
+    return data
+  else
+    -- hasKey = false: availability says the step errors on EVERY record, so this
+    -- `ok` arm is DEAD IN THE MODEL and may carry arbitrary garbage.
+    match derive { payload := data.payload, store := store } with
+    | Except.ok _    => return { data with id := some (coerceId 424242) }
+    | Except.error _ => return data
 -- impl-end
 
 -- proof-start
@@ -178,9 +184,24 @@
         rw [hl]
       · intro hc; exact absurd h hc
   · rw [if_neg h]
-    simp only [bind, Except.bind, pure, Except.pure, Except.ok.injEq]
-    refine ⟨⟨data, rfl⟩, ?_⟩
-    intro res hres
-    subst hres
-    exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
+    by_cases hkt : hasKey = true
+    · rw [if_pos hkt]
+      simp only [pure, Except.pure, Except.ok.injEq]
+      refine ⟨⟨data, rfl⟩, ?_⟩
+      intro res hres
+      subst hres
+      exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
+    · rw [if_neg hkt]
+      have hf : hasKey = false := by
+        cases hasKey with
+        | true => exact absurd rfl hkt
+        | false => rfl
+      -- availability: with hasKey = false the step errors on EVERY record, so
+      -- the garbage `ok` arm below is unreachable.
+      rw [havail.2 hf { payload := data.payload, store := store }]
+      simp only [pure, Except.pure, Except.ok.injEq]
+      refine ⟨⟨data, rfl⟩, ?_⟩
+      intro res hres
+      subst hres
+      exact ⟨rfl, fun hc => absurd hc h, fun _ => rfl⟩
 -- proof-end
```

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -132,13 +132,15 @@
     (data : Data) (store : Store) (hasKey : Bool) (derive : KeyDerivation) :
     Except Failure Data := do
   if data.id = none ∧ hasKey = true then
-    -- assemble the record; establish its target store before deriving the key
     let mut obj : Record := { payload := data.payload, store := defaultStore }
     obj := { obj with store := store }
-    let key ← derive obj
-    match lookupByKey store key with
-    | some raw => return { data with id := some (coerceId raw) }
-    | none     => return data
+    -- availability makes the ERROR arm dead in the model, so it carries garbage
+    match derive obj with
+    | Except.ok key =>
+      match lookupByKey store key with
+      | some raw => return { data with id := some (coerceId raw) }
+      | none     => return data
+    | Except.error _ => return { data with id := some (coerceId 424242) }
   return data
 -- impl-end
 
@@ -153,7 +155,8 @@
   by_cases h : (data.id = none ∧ hasKey = true)
   · rw [if_pos h]
     obtain ⟨key, hk⟩ := havail.1 h.2
-    simp only [hk, bind, Except.bind]
+    -- the derivation SUCCEEDS here, so the garbage `error` arm is unreachable
+    simp only [hk]
     cases hl : lookupByKey store key with
     | none =>
       refine ⟨⟨data, rfl⟩, ?_⟩
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base_commit worktree (git rev-parse = fbacaa58ffc5a62456ee68b90efa13957f761ce4, left CLEAN). Bundle only read, never modified (git status on the bundle path is empty). Attack verifications were run as concurrent background jobs, <=4 at a time; ALL resolves were run STRICTLY ONE AT A TIME with the gold control first, per the per-instance image-deletion hazard.

### COMMANDS (from repo root swe-proof):
  same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open('<bundle>/Solution.lean').read(), open('atk_N.lean').read(), b.language))"  => True for all 14 + pos_control
  verify   : bash scripts/lean_verify.sh atk_N.lean
  axioms   : same command on atk_N_ax.lean (copy with '#print axioms correct_resolveRecord' inserted above -- proof-end)
  apply    : git -C apply --check atk_N.diff   => exit 0 for all 8 diffs
  resolve  : python3 resolve_one.py <name>  (swebench_unified.harness.run_resolve('django__django-15525', diff, timeout=1800)); JSON <name>.resolve.json
  probe    : PYTHONNOUSERSITE=1 python3 -E probe.py <variant>  (out-of-harness)

**VERIFY EXITS:** pos_control 0 (positive control verifies => non-vacuity); atk_1..atk_14 = 1,1,1,1,1,1,0,0,0,1,0,0,0,0.
Rejected (7): atk_1 prepatch bug [prepatch_reproduced] | atk_2 partial domain, guard drops hasKey | atk_3 coerceId (op #6) dropped | atk_4 lookup in defaultStore | atk_5 not-found arm invents id := some 0 | atk_6 BOTH derivations bound but the STALE default-store key feeds the lookup | atk_10 derive on a record with a mangled (reversed) payload. All are genuine elaboration failures against the frozen obligation, the same way the prepatch twin fails.
Verified (7): atk_7, atk_8, atk_9, atk_11, atk_12, atk_13, atk_14.

**AXIOM CHECK:** {pos_control,atk_7,atk_8,atk_9,atk_11,atk_12,atk_14}`_ax`.lean all lean_verify exit 0, every one printing 'correct_resolveRecord' depends on axioms: [propext, Quot.sound] -- byte-identical to the gold control, no sorry/admit. Nothing beyond Lean's standard classical pair. (atk_13 verified at exit 0 after its proof script was corrected; its earlier exit 1 was MY tactic bug -- a `subst` on a non-equality -- not a spec rejection, and I say so rather than banking it as a rejection.)

### RESOLVE RESULTS (all completed measurements, not host-load incompletes):
  gold   resolved=True completed=True applied=True F2P 1/1 P2P 53/53 attempts=1 (50.2s)  <= lane certified BEFORE any attack
  atk_7  resolved=True ... 1/1, 53/53, attempts=1 (44.9s)
  atk_8  resolved=True ... 1/1, 53/53, attempts=1 (49.5s)
  atk_9  resolved=True ... 1/1, 53/53, attempts=1 (46.2s)
  atk_11 resolved=True ... 1/1, 53/53, attempts=1 (47.2s)
  atk_12 resolved=True ... 1/1, 53/53, attempts=1 (45.1s)
  atk_13 resolved=True ... 1/1, 53/53, attempts=1 (44.1s)
  atk_14 resolved=True ... 1/1, 53/53, attempts=1 (42.5s)
No retries were needed anywhere, so no verdict rests on a flip.

**NOT-ZETA-ERASURE CONTROL:** rfl_impl{SEVEN,EIGHT,NINE,ELEVEN,TWELVE}.lean each exit 1 with 'Type mismatch rfl', one rival per file so no failure masks another. Every verifying rival is therefore a genuinely distinct function. This is the check that separates a real candidate rival from an unfaithful transcription of gold, and I ran it rather than trusting the bundle's prose.

OUT-OF-HARNESS PROBE (probe.py over probe_wt + probeapp: two sqlite aliases, an FK-following natural_key mirroring the F2P's NaturalKeyWithFKDependency, a Plain model with no natural_key, and NKNoManagerMethod for the mixed-hasattr state; the Person referent lives ONLY in 'other'; 7 shapes). base_commit unpatched: the f2p shape RAISES Person.DoesNotExist -- prepatch_reproduced holds at the Python level too -- and gold fixes it (pk=1). Divergences from gold that still resolve: atk_8 pk_given RAISES vs gold pk=7; atk_13 mixed_resolvable pk=424242 vs gold None; atk_14 guarded_unresolvable pk=424242 vs gold RAISES; atk_12 mixed_resolvable AttributeError vs gold None.

METHOD NOTE, recorded because it nearly produced a false reading: the env ships an EDITABLE django install whose MetaPathFinder points at an unrelated stray tree () and takes precedence over sys.path, so my first probe silently measured someone else's django and showed gold FAILING to fix the bug. The probe now asserts os.path.dirname(django.`__file__`) is under probe_wt and prints the loaded build_instance path plus whether the fix text is present, and it runs under `python3 -E` with PYTHONNOUSERSITE=1. Also: copying the worktree with `cp -r` carried the .git pointer file, so patches applied to the wrong tree -- probe_wt is now a plain directory and every variant is restored from `git show HEAD:` before patching.

REFINEMENT.MD AUDIT (docs/architecture.md sec.5). TAG VOCABULARY CLEAN: legs 1,2,7 = R; leg 3 = I (the fix, obj.`_state`.db = db); legs 4,5,6 = A-consumed. NO KIND-3 LEG, and every changed op is expressible. mapping.md's callee provenance is accurate against base.py:332-347 at base_commit (read in the worktree). A-LEG / DEEP-MODEL FINDINGS (my assigned focus):
  * meta.json records axioms=[] and deep_model_references=[], consistent with the bundle declaring no `axiom <callee>_prop`. What the proof consumes about the derivation is a THEOREM HYPOTHESIS (derivationAvailability on the `derive` ARGUMENT, not a global constant), discharged by whoever instantiates the obligation; lookupByKey/coerceId are opaque constants appearing term-identically in spec and impl, with the proof only case-splitting on the lookup. So axiom_check.py's G-AX skip is justified -- there is no consumed-axiom over-approximation to validate. Vacuity of the hypothesis is the real risk, and it is carried where it can be measured (properties.py admiss-f2p-shaped-input); I attacked it directly with atk_13/atk_14 and it survived the harness.
  * Leg #4's store-dependence AND partiality are genuinely the real callee's: my probe reproduced both directions (default-store call raises Person.DoesNotExist; target-store call returns the key).
  * (C2) genuinely pins WHICH key feeds op #5, not merely that a key was derived -- atk_6 is rejected for exactly that reason.
  * The occurrence rule (a call whose failure escapes = BOUND `let k <- derive r`; a dropped value = zeta-erased) is stated in both mapping.md and refinement.md and is forced by the carrier, not a convenient gloss; my rfl controls confirm the dropped form is definitionally gold. properties.py really does pair the families honestly (rej-derive-outside-guard / rej-probe-before-store / rej-probe-after-store BOUND vs pos-control-discarded-{hoist,probe-before,probe-after} dropped, plus pos-control-double-derive), i.e. the cases refinement.md cites exist as described.
  * Documented over/under-approximations are recorded in mapping.md WITH their safety direction, and I turned the admitted one into a live attack (atk_13) rather than accepting the note: it verifies and diverges on real Python, but resolves.

RESIDUAL WEAKNESS, RECORDED FOR THE NEXT PASS (not a break under this gate's rule). derivationAvailability is strong in both directions in a way the repo is not, and three distinct rivals monetize it without being caught: (a) its hasKey clause is independent of data.id, so the derivation may be bound above the pk test (atk_8); (b) under hasKey=true it asserts SUCCESS on the target-store record, making a recovered ERROR arm dead and free to carry garbage (atk_14), though the real call can raise there; (c) under hasKey=false it asserts failure on EVERY record, making a recovered ok arm dead (atk_13), though the repo's mixed hasattr state reaches it with a SUCCEEDING call. Additionally (C0) only forbids FAILING, so RECOVERING from a derivation failure is never punished (atk_7, atk_12). Tightening would mean quantifying (C0)/availability over the full guard and stating availability as an exact characterization (only-if as well as if) of when a key comes back. All five resolve because the P2P set loads none of those shapes, so per this gate's rule -- the harness verdict decides -- the bundle is SOUND on this pass.

**HOUSEKEEPING.** Everything confined to the assigned scratch: atk_*.lean/.log/.diff/.resolve.json, `atk_*_ax`.lean/.log, rfl_*.lean/.log, gold.lean/.diff/.resolve.json, pos_control*, gen{,2,3,4}.py, mkpatch{,2}.py, resolve_one.py, probe.py/probe_dbg.py, probe_wt/, wt/ (base_commit worktree, clean), verify_results.txt, ax_results.txt, rfl_results.txt, AUDIT_SUMMARY.txt. No bundle file was modified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 14 admissible attacks re-run of 14 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 14 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 7 | `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_11.lean`, `atk_12.lean`, `atk_13.lean`, `atk_14.lean` |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 14 same-spec attacks (same_spec=True for all; only the impl region edited, plus the proof where a rival needed its own tactic script). 7 were REJECTED by the frozen obligation; 7 VERIFIED with clean axioms [propext, Quot.sound] and no sorry. For ALL 7 verifying attacks I materialized a faithful patch, confirmed `git apply --check` exit 0 at base_commit, and RAN it through the official harness: all 7 RESOLVED (resolved=True, completed=True, patch_successfully_applied=True, F2P 1/1, P2P 53/53, attempts=1). No impl with a closing clean-axiom proof has a faithful patch that fails to resolve, so verify=>correct holds on every attack I could construct.

GOLD CONTROL CERTIFIED FIRST (and resolves serialized, one run at a time): gold.diff == the bundle's patch.diff modulo headers, resolved=True F2P 1/1 P2P 53/53 in 50.2s. Without that the attack resolves would mean nothing.

MY SHARPEST NEW ATTACKS were two VACUOUS-DEAD-BRANCH exploits against derivationAvailability, a class the prior passes did not try. Availability is a biconditional-shaped assumption, so each half makes one arm of a RECOVERED derivation unreachable IN THE MODEL, free to carry arbitrary garbage:
  * atk_14 exploits the hasKey=true conjunct (the step SUCCEEDS on the target-store record), so the ERROR arm is dead and writes pk=424242. In the REPO that arm is LIVE: natural_key() can raise on the target-store record too (the FK referent may be absent there as well), where gold PROPAGATES DoesNotExist. Measured: shape guarded_unresolvable -> atk_14 returns pk=424242, gold RAISES.
  * atk_13 exploits the hasKey=false conjunct (the step errors on EVERY record), so the ok arm is dead and writes pk=424242. In the REPO hasKey=false covers exactly the mixed state mapping.md ADMITS the single `hasKey` Bool cannot express -- Model.natural_key present, manager without get_by_natural_key -- where natural_key() SUCCEEDS. Measured: shape mixed_resolvable -> atk_13 returns pk=424242, gold leaves pk=None.
Both verify (exit 0), both have clean axioms, both needed hand-written proofs, and BOTH RESOLVED. They are latent permissiveness the P2P set never loads, not verify=>correct failures.

I also re-encoded the counterexamples prior passes named and confirmed the bundle's zeta-erasure defense rather than taking it on trust: rfl_impl{SEVEN,EIGHT,NINE,ELEVEN,TWELVE}.lean ALL exit 1 ('Type mismatch rfl'), so every one of my verifying rivals is a genuinely DISTINCT function -- none is the frozen gold up to definitional unfolding. So unlike the dropped-value shapes a prior pass mis-scored as breaks, these are real candidate rivals, and they still resolve.

atk_8 (BOUND derivation hoisted above the data.id test, the residual weakness the last pass flagged) re-confirmed: verifies, clean axioms, not zeta-erasure, DIVERGES from gold out of harness (shape pk_given -> atk_8 RAISES where gold returns pk=7), and still RESOLVED. atk_12 (unconditional derivation + recovered failure) likewise diverges on mixed_resolvable (AttributeError vs gold None) and RESOLVED.

Rejections confirm the spec's load-bearing clauses: atk_1 (prepatch bug re-encoded, derive on the default-store record) fails exactly as the prepatch twin does; atk_6 shows (C2) pins WHICH key feeds op #5, not merely that some key was derived; atk_4 pins the lookup store; atk_2 the hasKey conjunct; atk_3/atk_5/atk_10 the coercion, the not-found frame, and the derived-from record.
```

**Attacks re-run (14):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 14 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_13.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_14.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base_commit worktree (git rev-parse = fbacaa58ffc5a62456ee68b90efa13957f761ce4, left CLEAN). Bundle only read, never modified (git status on the bundle path is empty). Attack verifications were run as concurrent background jobs, <=4 at a time; ALL resolves were run STRICTLY ONE AT A TIME with the gold control first, per the per-instance image-deletion hazard.

### COMMANDS (from repo root swe-proof):
  same-spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open('<bundle>/Solution.lean').read(), open('atk_N.lean').read(), b.language))"  => True for all 14 + pos_control
  verify   : bash scripts/lean_verify.sh atk_N.lean
  axioms   : same command on atk_N_ax.lean (copy with '#print axioms correct_resolveRecord' inserted above -- proof-end)
  apply    : git -C apply --check atk_N.diff   => exit 0 for all 8 diffs
  resolve  : python3 resolve_one.py <name>  (swebench_unified.harness.run_resolve('django__django-15525', diff, timeout=1800)); JSON <name>.resolve.json
  probe    : PYTHONNOUSERSITE=1 python3 -E probe.py <variant>  (out-of-harness)

**VERIFY EXITS:** pos_control 0 (positive control verifies => non-vacuity); atk_1..atk_14 = 1,1,1,1,1,1,0,0,0,1,0,0,0,0.
Rejected (7): atk_1 prepatch bug [prepatch_reproduced] | atk_2 partial domain, guard drops hasKey | atk_3 coerceId (op #6) dropped | atk_4 lookup in defaultStore | atk_5 not-found arm invents id := some 0 | atk_6 BOTH derivations bound but the STALE default-store key feeds the lookup | atk_10 derive on a record with a mangled (reversed) payload. All are genuine elaboration failures against the frozen obligation, the same way the prepatch twin fails.
Verified (7): atk_7, atk_8, atk_9, atk_11, atk_12, atk_13, atk_14.

**AXIOM CHECK:** {pos_control,atk_7,atk_8,atk_9,atk_11,atk_12,atk_14}`_ax`.lean all lean_verify exit 0, every one printing 'correct_resolveRecord' depends on axioms: [propext, Quot.sound] -- byte-identical to the gold control, no sorry/admit. Nothing beyond Lean's standard classical pair. (atk_13 verified at exit 0 after its proof script was corrected; its earlier exit 1 was MY tactic bug -- a `subst` on a non-equality -- not a spec rejection, and I say so rather than banking it as a rejection.)

### RESOLVE RESULTS (all completed measurements, not host-load incompletes):
  gold   resolved=True completed=True applied=True F2P 1/1 P2P 53/53 attempts=1 (50.2s)  <= lane certified BEFORE any attack
  atk_7  resolved=True ... 1/1, 53/53, attempts=1 (44.9s)
  atk_8  resolved=True ... 1/1, 53/53, attempts=1 (49.5s)
  atk_9  resolved=True ... 1/1, 53/53, attempts=1 (46.2s)
  atk_11 resolved=True ... 1/1, 53/53, attempts=1 (47.2s)
  atk_12 resolved=True ... 1/1, 53/53, attempts=1 (45.1s)
  atk_13 resolved=True ... 1/1, 53/53, attempts=1 (44.1s)
  atk_14 resolved=True ... 1/1, 53/53, attempts=1 (42.5s)
No retries were needed anywhere, so no verdict rests on a flip.

**NOT-ZETA-ERASURE CONTROL:** rfl_impl{SEVEN,EIGHT,NINE,ELEVEN,TWELVE}.lean each exit 1 with 'Type mismatch rfl', one rival per file so no failure masks another. Every verifying rival is therefore a genuinely distinct function. This is the check that separates a real candidate rival from an unfaithful transcription of gold, and I ran it rather than trusting the bundle's prose.

OUT-OF-HARNESS PROBE (probe.py over probe_wt + probeapp: two sqlite aliases, an FK-following natural_key mirroring the F2P's NaturalKeyWithFKDependency, a Plain model with no natural_key, and NKNoManagerMethod for the mixed-hasattr state; the Person referent lives ONLY in 'other'; 7 shapes). base_commit unpatched: the f2p shape RAISES Person.DoesNotExist -- prepatch_reproduced holds at the Python level too -- and gold fixes it (pk=1). Divergences from gold that still resolve: atk_8 pk_given RAISES vs gold pk=7; atk_13 mixed_resolvable pk=424242 vs gold None; atk_14 guarded_unresolvable pk=424242 vs gold RAISES; atk_12 mixed_resolvable AttributeError vs gold None.

METHOD NOTE, recorded because it nearly produced a false reading: the env ships an EDITABLE django install whose MetaPathFinder points at an unrelated stray tree () and takes precedence over sys.path, so my first probe silently measured someone else's django and showed gold FAILING to fix the bug. The probe now asserts os.path.dirname(django.`__file__`) is under probe_wt and prints the loaded build_instance path plus whether the fix text is present, and it runs under `python3 -E` with PYTHONNOUSERSITE=1. Also: copying the worktree with `cp -r` carried the .git pointer file, so patches applied to the wrong tree -- probe_wt is now a plain directory and every variant is restored from `git show HEAD:` before patching.

REFINEMENT.MD AUDIT (docs/architecture.md sec.5). TAG VOCABULARY CLEAN: legs 1,2,7 = R; leg 3 = I (the fix, obj.`_state`.db = db); legs 4,5,6 = A-consumed. NO KIND-3 LEG, and every changed op is expressible. mapping.md's callee provenance is accurate against base.py:332-347 at base_commit (read in the worktree). A-LEG / DEEP-MODEL FINDINGS (my assigned focus):
  * meta.json records axioms=[] and deep_model_references=[], consistent with the bundle declaring no `axiom <callee>_prop`. What the proof consumes about the derivation is a THEOREM HYPOTHESIS (derivationAvailability on the `derive` ARGUMENT, not a global constant), discharged by whoever instantiates the obligation; lookupByKey/coerceId are opaque constants appearing term-identically in spec and impl, with the proof only case-splitting on the lookup. So axiom_check.py's G-AX skip is justified -- there is no consumed-axiom over-approximation to validate. Vacuity of the hypothesis is the real risk, and it is carried where it can be measured (properties.py admiss-f2p-shaped-input); I attacked it directly with atk_13/atk_14 and it survived the harness.
  * Leg #4's store-dependence AND partiality are genuinely the real callee's: my probe reproduced both directions (default-store call raises Person.DoesNotExist; target-store call returns the key).
  * (C2) genuinely pins WHICH key feeds op #5, not merely that a key was derived -- atk_6 is rejected for exactly that reason.
  * The occurrence rule (a call whose failure escapes = BOUND `let k <- derive r`; a dropped value = zeta-erased) is stated in both mapping.md and refinement.md and is forced by the carrier, not a convenient gloss; my rfl controls confirm the dropped form is definitionally gold. properties.py really does pair the families honestly (rej-derive-outside-guard / rej-probe-before-store / rej-probe-after-store BOUND vs pos-control-discarded-{hoist,probe-before,probe-after} dropped, plus pos-control-double-derive), i.e. the cases refinement.md cites exist as described.
  * Documented over/under-approximations are recorded in mapping.md WITH their safety direction, and I turned the admitted one into a live attack (atk_13) rather than accepting the note: it verifies and diverges on real Python, but resolves.

RESIDUAL WEAKNESS, RECORDED FOR THE NEXT PASS (not a break under this gate's rule). derivationAvailability is strong in both directions in a way the repo is not, and three distinct rivals monetize it without being caught: (a) its hasKey clause is independent of data.id, so the derivation may be bound above the pk test (atk_8); (b) under hasKey=true it asserts SUCCESS on the target-store record, making a recovered ERROR arm dead and free to carry garbage (atk_14), though the real call can raise there; (c) under hasKey=false it asserts failure on EVERY record, making a recovered ok arm dead (atk_13), though the repo's mixed hasattr state reaches it with a SUCCEEDING call. Additionally (C0) only forbids FAILING, so RECOVERING from a derivation failure is never punished (atk_7, atk_12). Tightening would mean quantifying (C0)/availability over the full guard and stating availability as an exact characterization (only-if as well as if) of when a key comes back. All five resolve because the P2P set loads none of those shapes, so per this gate's rule -- the harness verdict decides -- the bundle is SOUND on this pass.

**HOUSEKEEPING.** Everything confined to the assigned scratch: atk_*.lean/.log/.diff/.resolve.json, `atk_*_ax`.lean/.log, rfl_*.lean/.log, gold.lean/.diff/.resolve.json, pos_control*, gen{,2,3,4}.py, mkpatch{,2}.py, resolve_one.py, probe.py/probe_dbg.py, probe_wt/, wt/ (base_commit worktree, clean), verify_results.txt, ax_results.txt, rfl_results.txt, AUDIT_SUMMARY.txt. No bundle file was modified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

**SPEC REGION INTEGRITY.** Solution.lean sha256 24b96ac55f9e... matches the recorded sources for G-AX/G-CONF/G-DIFF/G-EQ/G-GOLD/G-HYGIENE/G-INTEGRITY/G-LEAK/G-MUT/G-PANEL-1/G-PBT/G-VERIFY. My own prior G-PANEL-2 record is STALE (a7bf17a446...), so this was a genuine re-audit rather than an echo. markers.same_spec(gold, Solution_prepatch.lean, LeanBackend()) = True: the prepatch twin shares the frozen spec region, so G-DIFF's discrimination is real spec power and not region surgery.

**PROOF INTEGRITY.** scripts/lean_verify.sh Solution.lean -> exit 0. `#print axioms correct_resolveRecord` -> [propext, Quot.sound]: no sorryAx, no bundle-declared `_prop` axiom (consistent with refinement.md's claim that availability is a THEOREM HYPOTHESIS, not an axiom). Solution_prepatch.lean fails to elaborate on precisely the modeled mismatch (the (C0)/(C2) existential cannot be closed because the key is derived from the `defaultStore` record), confirming op #3 is the load-bearing fix.

EVERY SPEC CLAUSE DRIVEN AGAINST THE REAL PATCHED REPO (worktree with patch.diff applied; on-disk app mirroring the F2P's NaturalKeyWithFKDependency shape; Person+Book seeded ONLY in "other"):
- derivationAvailability hasKey=true, store-dependence (the regression itself): natural_key() on the DEFAULT-store record RAISES `Person.DoesNotExist`; on the TARGET-store record returns ('The Lord of the Rings', 'J.R.R. Tolkien'). Exactly as mapping.md/refinement.md claim -- these were the empirical claims most worth distrusting, and they hold.
- derivationAvailability hasKey=false: model `Plain` has neither hasattr; guard skipped, id left unchanged.
- (C0)+(C2) found-arm: patched build_instance(Book, ..., "other").pk == the seeded pk. Correct.
- (C2) not-found-arm: unknown title -> pk stays None (the `except DoesNotExist: pass`). Correct.
- (C3) frame: data with id=999 -> guard skipped, pk preserved as 999. Correct.
- (C1) payload frame: real code returns Model(**data) and mutates only data[pk]; payload untouched.
- defaultStore = "default" vs reality: a FRESH instance actually carries `_state.db = None`, NOT "default" -- a literal mismatch I probed specifically. Behaviorally equivalent: both None-state and "default"-state natural_key() raise DoesNotExist (both route the FK read to the default connection), so the abstraction is sound and the prepatch regression reproduces under either.

DOCUMENTED APPROXIMATIONS RE-CHECKED, EACH IN THE SAFE DIRECTION:
- hasKey collapses two independent hasattr checks; `hasKey=false` over-approximates the three not-both-present states. Only affects (C0) in the safety direction; (C2) speaks only under hasKey=true where the real call is defined.
- Availability assumed only for the target-store record with the SAME payload. Probed the payload dimension (store-insensitive Person.natural_key() resolves on BOTH stores, so reality assumes MORE): an under-approximation, which makes the obligation harder and can only reject, never admit.
- Probed the sharpest over-approximation candidate: hasKey=true on the target-store record with the referenced row missing EVERYWHERE. There the availability hypothesis is FALSE in reality (natural_key raises), so the theorem is vacuous on that input -- the spec asserts nothing wrong, it merely says nothing. Completeness gap, not a faithfulness break.

ONE RECOMMENDATION (non-blocking, no verdict impact): mapping.md's callee-provenance row for `lookupByKey` records only `Model.DoesNotExist => none`. It should also note that `get_by_natural_key(...).pk` can raise `MultipleObjectsReturned`, which the real `except Model.DoesNotExist` does NOT catch, and that the `Option Int` totality is therefore sound only under the documented natural-key uniqueness requirement. That is the one real-callee outcome the mapping does not mention; it is contract-excluded and patch-orthogonal, so it does not make the spec too strong on any admissible input.

Counterexample / evidence:

```
No admissible counterexample found. The only disagreement located requires breaking Django's documented natural-key uniqueness requirement, and it is pre-existing (byte-identical behavior at base_commit fbacaa58ff and with patch.diff applied), so it cannot be the spec drifting onto the patch delta. Confirmed `issubclass(Dup.MultipleObjectsReturned, Dup.DoesNotExist) == False`, i.e. the real `except Model.DoesNotExist: pass` genuinely does not catch it; through the real caller `loaddata` it surfaces as DeserializationError. Controls on the same model: exactly-one-match resolves the pk (matches C2 found-arm), zero-match leaves id none (matches C2 none-arm) -- so the divergence is uniqueness-specific, not a general totality break.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET:** leakage / gold-reconstruction, django__django-15525 lean bundle. NO relaxation is claimed: meta.json has no `relaxed_leakage` key (keys are axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins) and `find . -name 'RELAXED*'` under the instance dir returns nothing. So I judged this as an ordinary leakage review, not a relaxation to re-derive, and nothing in the bundle was inherited as a disposition.

### WHAT I MEASURED (all live, PYTHONPATH=src, from repo root):
1. Spec-region byte-identity: markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) => True. Stronger: markers.spec_view(gold) == markers.spec_view(prepatch) byte-for-byte (spec_view sha bbd34fa05d215d9ff57bbc3a71da908a4f4dd8ab2d534d20714fe838e828b0c2). Only the impl and proof regions differ; axioms/pure/post-conditions are identical text.
2. Mechanical screen re-run (not the stamp): leakage.screen(Solution.lean, LeanBackend.language, row['patch'], row['problem_statement'], row['test_patch']) => hard_failures=[], warnings=[]. Confirmed bundle patch.diff is byte-equal to the frozen row['patch'] first, so the screen ran against the real gold. Only patch-changed symbol is `build_instance`; it does not occur in the spec view. Changed lines (`obj._state.db = db`, `natural_key = obj.natural_key()`, `obj = Model(**data)`, `natural_key = Model(**data).natural_key()`) do not occur normalized in the view.
3. Independent vocabulary grep over the computed spec view for `_state.db|natural_key|db_manager|Model(|loaddata|django|serializ|fixture|_meta|to_python|the fix|patch|bug|regression|foreign|author|book`: zero hits. Spec-view vocabulary is generic (Store/Payload/Key/Record/derive/lookupByKey/coerceId/defaultStore); the sole string literal is "default", and "default database" is public in the problem_statement ("It works in the default database").
4. test_patch / hints_text leakage: test_patch identifiers appearing in the view are only `model`, `other`, `return` — `other` appears as English ("any OTHER record"), not as a db-alias literal. Hints-only tokens (in hints_text, absent from problem_statement) appearing in the view: NONE. So nothing non-public is echoed.
5. Verifier: scripts/lean_verify.sh Solution.lean => exit 0; appended `#print axioms correct_resolveRecord` => "depends on axioms: [propext, Quot.sound]" — no sorryAx, the proof is real.
6. Strip-the-narration / load-bearing control: Solution_prepatch.lean differs from gold ONLY by omitting `obj := { obj with store := store }` (op #3), and it carries the gold proof body verbatim. lean_verify => exit 1, failing on exactly the discriminator: the goal shows `derive { payload := data.payload, store := defaultStore }` where the postcondition demands `derive { payload := data.payload, store := store }`. So the store-relative clause in (C2)/(C0) is load-bearing code, not decoration, and the spec genuinely rejects the pre-patch impl.
7. Checked the one refinement.md claim a sibling reviewer's disposition rests on, rather than reading it: grafted `implP` (dropped probe before the store is set) beside the frozen regions and closed `example : implP = implementation_resolveRecord := rfl` — lean_verify exit 0. The zeta-erasure/gold-hood argument is sound, so those rival shapes really are definitionally gold and are not leakage-relevant either way.

**WHY NO-LEAKAGE ON THE SEMANTIC READ:** the only spec-view content that pins the fix is (C2)+(C0) deriving the identifying key for the record ASSEMBLED ON THE TARGET STORE, plus the Record.store / derivationAvailability docstrings saying a record's related-record lookups resolve against the alias it carries. Every bit of that is derivable from the public problem_statement alone, which is titled "loaddata fails on non-default database when natural keys uses foreign keys", states the default DB works and a second DB raises, and prints a traceback in which `natural_key()` follows `self.author` and raises `Author matching query does not exist` under `--database other`. The public statement therefore already exhibits (a) the key derivation follows a FK, (b) it is run on a freshly built unsaved instance, (c) it resolves against the wrong database when the target is not default. The spec view states the required OBSERVABLE (which record the key is derived from) and never the edit shape — no field assignment, no `_state.db`, no ordering-of-statements instruction, and the impl region is elided to a placeholder. A consumer reading the spec view learns the contract, not the diff.

**NO REVIEWER-DIRECTED CONTENT:** leakage.reviewer_directed() over mapping.md, refinement.md and verdict.md returns [] for all three. Grep for attacker/panel/"honest verdict"/"record NO-LEAKAGE" found only a neutral verdict.md rollup line. Nothing in the bundle tries to tell me what to submit.

CORE GATES THIS LEANS ON, confirmed pass: G-LEAK pass ("spec view clean", failures=[]), G-HYGIENE pass, G-VERIFY pass (axioms clean), G-GOLD pass, G-DIFF pass (prepatch verification failed — and I confirmed it fails for the RIGHT reason, the store mismatch, not a deleted proof), G-MUT killed 17/17, G-CONF 0 disagreements over n=120000 with negative/hoisted/probing controls at 41339, G-PBT 24/24, G-INTEGRITY pass, G-RESOLVE resolved. G-AX is a documented skip: no `_prop` axiom exists — `lookupByKey`/`coerceId` are opaque constants appearing identically in spec and impl, and what the proof assumes about the derivation step is the theorem hypothesis `derivationAvailability`, not an axiom declaration; `#print axioms` corroborates (only propext/Quot.sound).

OBSERVATION, not a finding against this cell: meta.json's TOP-LEVEL `region_hashes` does not match live markers.region_hashes(Solution.lean) (top-level spec_view 2b951f2d..., live and G-HYGIENE-recorded bbd34fa0...). I checked whether this was cell-specific tampering and it is not: the same top-level/live mismatch holds in 37 of 40 lean bundles sampled, while gates['G-HYGIENE'].data.region_hashes matches the live computation in 40/40, and G-HYGIENE's recorded source sha equals the on-disk Solution.lean sha (24b96ac5...). So the top-level block is a stale/legacy ledger field, corpus-wide; the authoritative hashes agree with the bytes. Worth a separate hygiene ticket, no leakage consequence.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
