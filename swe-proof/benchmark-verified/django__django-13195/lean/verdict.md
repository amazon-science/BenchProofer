# P2 adversarial audit — django__django-13195

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch.lean`, `atk_2_maxage_none.lean`, `atk_3_restamp_name.lean`, `atk_4_coded_value.lean`, `atk_5_comment_stamp.lean`, `atk_6_httponly.lean`, `atk_7_no_vary.lean`, `atk_8_del_then_write.lean`, `atk_15_messages_vary.lean`, `atk_16_session_status_body.lean`, `atk_17_vary_nodedup.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_9_reserved_noop.lean`, `atk_10_emptykey_bogus.lean`, `atk_11_badchars_dropsamesite.lean`, `atk_13_invalid_samesite.lean`, `atk_14_reserved_mistarget.lean`, `atk_18_reorder.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl with a closing clean-axiom proof had a faithful patch that failed to resolve. The 6 attacks that DID verify (atk_9, atk_10, atk_11, atk_13, atk_14, atk_18) each had a faithful unified diff materialized, checked with `git apply --check` at base_commit 156a2138db, and RUN through run_resolve: all 6 resolved (F2P 5/5, failure lists empty), as did the gold control. So verify => correct held on every executed probe.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,8 +299,8 @@
 -- impl-start
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
-  let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  let secure := key.startsWith "__Secure-" || key.startsWith "__Host-"
+  return setCookie resp key "" (some 0) epochExpires path domain secure false none
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2_maxage_none.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,7 +300,7 @@
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
   let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  return setCookie resp key "" none epochExpires path domain secure false samesite
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3_restamp_name.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,7 +300,10 @@
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
   let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  let base := setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  return { base with cookies := fun k =>
+    if k = key then (base.cookies k).map (fun c => { c with key := key.toUpper })
+    else base.cookies k }
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4_coded_value.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,7 +300,10 @@
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
   let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  let base := setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  return { base with cookies := fun k =>
+    if k = key then (base.cookies k).map (fun c => { c with codedValue := "\"deleted\"" })
+    else base.cookies k }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5_comment_stamp.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,7 +300,10 @@
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
   let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  let base := setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  return { base with cookies := fun k =>
+    if k = key then (base.cookies k).map (fun c => { c with comment := "audited" })
+    else base.cookies k }
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6_httponly.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,7 +300,7 @@
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
   let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  return setCookie resp key "" (some 0) epochExpires path domain secure true samesite
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7_no_vary.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -368,7 +368,7 @@
 def implementation_sessionDelete (resp : Response) (name sessionPath : String)
     (domain sessionSamesite : Option String) : Response := Id.run do
   let deleted := implementation_deleteCookie resp name sessionPath domain sessionSamesite
-  return varyMarked deleted ["Cookie"]
+  return deleted
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8_del_then_write.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,7 +300,8 @@
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
   let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  let cleared : Response := { resp with cookies := fun k => if k = key then none else resp.cookies k }
+  return setCookie cleared key "" (some 0) epochExpires path domain secure false samesite
 -- impl-end
 
 -- proof-start
```

Attack 9 — `atk_9_reserved_noop.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,6 +299,8 @@
 -- impl-start
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
+  if key.toLower ∈ reservedCookieNames then
+    return resp
   let secure := deleteSecure key samesite
   return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
 -- impl-end
@@ -309,13 +311,19 @@
       keyAccepted key → samesiteValid samesite →
       problem_spec_deleteCookie resp key path domain samesite
         (implementation_deleteCookie resp key path domain samesite) := by
-  intro resp key path domain samesite _ _
+  intro resp key path domain samesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp key path domain samesite
+      = setCookie resp key "" (some 0) epochExpires path domain
+          (deleteSecure key samesite) false samesite := by
+    simp [implementation_deleteCookie, hres]
+  rw [himpl]
   unfold problem_spec_deleteCookie deletesCookie
   refine ⟨⟨?_, ?_⟩, ?_⟩
-  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter]
+  · simp [setCookie, httpOnlyAfter, maxAgeAfter]
   · intro k hk
-    simp [implementation_deleteCookie, setCookie, hk]
-  · simp [implementation_deleteCookie, setCookie]
+    simp [setCookie, hk]
+  · simp [setCookie]
 -- proof-end
 
 -- post-conditions-start
@@ -379,9 +387,15 @@
         (implementation_sessionDelete resp name sessionPath domain sessionSamesite) := by
   intro resp name sessionPath domain sessionSamesite hkey hvalid
   have hd := correct_deleteCookie resp name sessionPath domain sessionSamesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp name sessionPath domain sessionSamesite
+      = setCookie resp name "" (some 0) epochExpires sessionPath domain
+          (deleteSecure name sessionSamesite) false sessionSamesite := by
+    simp [implementation_deleteCookie, hres]
   unfold problem_spec_deleteCookie at hd
   unfold problem_spec_sessionDelete implementation_sessionDelete
+  rw [himpl] at hd ⊢
   refine ⟨?_, ?_⟩
   · simpa [varyMarked] using hd.1
-  · simp [varyMarked, implementation_deleteCookie, setCookie]
+  · simp [varyMarked, setCookie]
 -- proof-end
```

Attack 10 — `atk_10_emptykey_bogus.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,6 +299,8 @@
 -- impl-start
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
+  if key = "" then
+    return setCookie resp "tamper" "x" (some 99) epochExpires path domain true true none
   let secure := deleteSecure key samesite
   return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
 -- impl-end
@@ -309,13 +311,19 @@
       keyAccepted key → samesiteValid samesite →
       problem_spec_deleteCookie resp key path domain samesite
         (implementation_deleteCookie resp key path domain samesite) := by
-  intro resp key path domain samesite _ _
+  intro resp key path domain samesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp key path domain samesite
+      = setCookie resp key "" (some 0) epochExpires path domain
+          (deleteSecure key samesite) false samesite := by
+    simp [implementation_deleteCookie, hne]
+  rw [himpl]
   unfold problem_spec_deleteCookie deletesCookie
   refine ⟨⟨?_, ?_⟩, ?_⟩
-  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter]
+  · simp [setCookie, httpOnlyAfter, maxAgeAfter]
   · intro k hk
-    simp [implementation_deleteCookie, setCookie, hk]
-  · simp [implementation_deleteCookie, setCookie]
+    simp [setCookie, hk]
+  · simp [setCookie]
 -- proof-end
 
 -- post-conditions-start
@@ -379,9 +387,15 @@
         (implementation_sessionDelete resp name sessionPath domain sessionSamesite) := by
   intro resp name sessionPath domain sessionSamesite hkey hvalid
   have hd := correct_deleteCookie resp name sessionPath domain sessionSamesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp name sessionPath domain sessionSamesite
+      = setCookie resp name "" (some 0) epochExpires sessionPath domain
+          (deleteSecure name sessionSamesite) false sessionSamesite := by
+    simp [implementation_deleteCookie, hne]
   unfold problem_spec_deleteCookie at hd
   unfold problem_spec_sessionDelete implementation_sessionDelete
+  rw [himpl] at hd ⊢
   refine ⟨?_, ?_⟩
   · simpa [varyMarked] using hd.1
-  · simp [varyMarked, implementation_deleteCookie, setCookie]
+  · simp [varyMarked, setCookie]
 -- proof-end
```

Attack 11 — `atk_11_badchars_dropsamesite.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,6 +299,9 @@
 -- impl-start
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
+  if !key.data.all cookieNameChar then
+    return setCookie resp key "" (some 0) epochExpires path domain
+      (key.startsWith "__Secure-" || key.startsWith "__Host-") false none
   let secure := deleteSecure key samesite
   return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
 -- impl-end
@@ -309,13 +312,19 @@
       keyAccepted key → samesiteValid samesite →
       problem_spec_deleteCookie resp key path domain samesite
         (implementation_deleteCookie resp key path domain samesite) := by
-  intro resp key path domain samesite _ _
+  intro resp key path domain samesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp key path domain samesite
+      = setCookie resp key "" (some 0) epochExpires path domain
+          (deleteSecure key samesite) false samesite := by
+    simp [implementation_deleteCookie, hchars]
+  rw [himpl]
   unfold problem_spec_deleteCookie deletesCookie
   refine ⟨⟨?_, ?_⟩, ?_⟩
-  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter]
+  · simp [setCookie, httpOnlyAfter, maxAgeAfter]
   · intro k hk
-    simp [implementation_deleteCookie, setCookie, hk]
-  · simp [implementation_deleteCookie, setCookie]
+    simp [setCookie, hk]
+  · simp [setCookie]
 -- proof-end
 
 -- post-conditions-start
@@ -379,9 +388,15 @@
         (implementation_sessionDelete resp name sessionPath domain sessionSamesite) := by
   intro resp name sessionPath domain sessionSamesite hkey hvalid
   have hd := correct_deleteCookie resp name sessionPath domain sessionSamesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp name sessionPath domain sessionSamesite
+      = setCookie resp name "" (some 0) epochExpires sessionPath domain
+          (deleteSecure name sessionSamesite) false sessionSamesite := by
+    simp [implementation_deleteCookie, hchars]
   unfold problem_spec_deleteCookie at hd
   unfold problem_spec_sessionDelete implementation_sessionDelete
+  rw [himpl] at hd ⊢
   refine ⟨?_, ?_⟩
   · simpa [varyMarked] using hd.1
-  · simp [varyMarked, implementation_deleteCookie, setCookie]
+  · simp [varyMarked, setCookie]
 -- proof-end
```

Attack 12 — `atk_13_invalid_samesite.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -297,8 +297,15 @@
 -- post-conditions-end
 
 -- impl-start
+def samesiteAccepted (samesite : Option String) : Bool :=
+  match samesite with
+  | some s => (s == "") || (s.toLower == "lax") || (s.toLower == "none") || (s.toLower == "strict")
+  | none   => true
+
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
+  if !samesiteAccepted samesite then
+    return resp
   let secure := deleteSecure key samesite
   return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
 -- impl-end
@@ -309,13 +316,25 @@
       keyAccepted key → samesiteValid samesite →
       problem_spec_deleteCookie resp key path domain samesite
         (implementation_deleteCookie resp key path domain samesite) := by
-  intro resp key path domain samesite _ _
+  intro resp key path domain samesite hkey hvalid
+  have hok : samesiteAccepted samesite = true := by
+    unfold samesiteAccepted
+    cases hv : samesite with
+    | none => rfl
+    | some s =>
+        subst hv
+        rcases hvalid with h | h | h | h <;> simp [h]
+  have himpl : implementation_deleteCookie resp key path domain samesite
+      = setCookie resp key "" (some 0) epochExpires path domain
+          (deleteSecure key samesite) false samesite := by
+    simp [implementation_deleteCookie, hok]
+  rw [himpl]
   unfold problem_spec_deleteCookie deletesCookie
   refine ⟨⟨?_, ?_⟩, ?_⟩
-  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter]
+  · simp [setCookie, httpOnlyAfter, maxAgeAfter]
   · intro k hk
-    simp [implementation_deleteCookie, setCookie, hk]
-  · simp [implementation_deleteCookie, setCookie]
+    simp [setCookie, hk]
+  · simp [setCookie]
 -- proof-end
 
 -- post-conditions-start
@@ -378,10 +397,22 @@
       problem_spec_sessionDelete resp name sessionPath domain sessionSamesite
         (implementation_sessionDelete resp name sessionPath domain sessionSamesite) := by
   intro resp name sessionPath domain sessionSamesite hkey hvalid
+  have hok : samesiteAccepted sessionSamesite = true := by
+    unfold samesiteAccepted
+    cases hv : sessionSamesite with
+    | none => rfl
+    | some s =>
+        subst hv
+        rcases hvalid with h | h | h | h <;> simp [h]
+  have himpl : implementation_deleteCookie resp name sessionPath domain sessionSamesite
+      = setCookie resp name "" (some 0) epochExpires sessionPath domain
+          (deleteSecure name sessionSamesite) false sessionSamesite := by
+    simp [implementation_deleteCookie, hok]
   have hd := correct_deleteCookie resp name sessionPath domain sessionSamesite hkey hvalid
   unfold problem_spec_deleteCookie at hd
   unfold problem_spec_sessionDelete implementation_sessionDelete
+  rw [himpl] at hd ⊢
   refine ⟨?_, ?_⟩
   · simpa [varyMarked] using hd.1
-  · simp [varyMarked, implementation_deleteCookie, setCookie]
+  · simp [varyMarked, setCookie]
 -- proof-end
```

Attack 13 — `atk_14_reserved_mistarget.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -299,6 +299,9 @@
 -- impl-start
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
+  if key.toLower ∈ reservedCookieNames then
+    return setCookie resp key.toUpper "" (some 0) epochExpires path domain
+      (deleteSecure key samesite) false samesite
   let secure := deleteSecure key samesite
   return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
 -- impl-end
@@ -309,13 +312,19 @@
       keyAccepted key → samesiteValid samesite →
       problem_spec_deleteCookie resp key path domain samesite
         (implementation_deleteCookie resp key path domain samesite) := by
-  intro resp key path domain samesite _ _
+  intro resp key path domain samesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp key path domain samesite
+      = setCookie resp key "" (some 0) epochExpires path domain
+          (deleteSecure key samesite) false samesite := by
+    simp [implementation_deleteCookie, hres]
+  rw [himpl]
   unfold problem_spec_deleteCookie deletesCookie
   refine ⟨⟨?_, ?_⟩, ?_⟩
-  · simp [implementation_deleteCookie, setCookie, httpOnlyAfter, maxAgeAfter]
+  · simp [setCookie, httpOnlyAfter, maxAgeAfter]
   · intro k hk
-    simp [implementation_deleteCookie, setCookie, hk]
-  · simp [implementation_deleteCookie, setCookie]
+    simp [setCookie, hk]
+  · simp [setCookie]
 -- proof-end
 
 -- post-conditions-start
@@ -379,9 +388,15 @@
         (implementation_sessionDelete resp name sessionPath domain sessionSamesite) := by
   intro resp name sessionPath domain sessionSamesite hkey hvalid
   have hd := correct_deleteCookie resp name sessionPath domain sessionSamesite hkey hvalid
+  obtain ⟨hne, hres, hchars⟩ := hkey
+  have himpl : implementation_deleteCookie resp name sessionPath domain sessionSamesite
+      = setCookie resp name "" (some 0) epochExpires sessionPath domain
+          (deleteSecure name sessionSamesite) false sessionSamesite := by
+    simp [implementation_deleteCookie, hres]
   unfold problem_spec_deleteCookie at hd
   unfold problem_spec_sessionDelete implementation_sessionDelete
+  rw [himpl] at hd ⊢
   refine ⟨?_, ?_⟩
   · simpa [varyMarked] using hd.1
-  · simp [varyMarked, implementation_deleteCookie, setCookie]
+  · simp [varyMarked, setCookie]
 -- proof-end
```

Attack 14 — `atk_15_messages_vary.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -333,7 +333,7 @@
 -- impl-start
 def implementation_messagesDelete (resp : Response) (cookieName : String)
     (domain sessionSamesite : Option String) : Response := Id.run do
-  return implementation_deleteCookie resp cookieName "/" domain sessionSamesite
+  return varyMarked (implementation_deleteCookie resp cookieName "/" domain sessionSamesite) ["Cookie"]
 -- impl-end
 
 -- proof-start
```

Attack 15 — `atk_16_session_status_body.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -368,7 +368,8 @@
 def implementation_sessionDelete (resp : Response) (name sessionPath : String)
     (domain sessionSamesite : Option String) : Response := Id.run do
   let deleted := implementation_deleteCookie resp name sessionPath domain sessionSamesite
-  return varyMarked deleted ["Cookie"]
+  let marked := varyMarked deleted ["Cookie"]
+  return { marked with status := 204, body := "" }
 -- impl-end
 
 -- proof-start
```

Attack 16 — `atk_17_vary_nodedup.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -368,7 +368,7 @@
 def implementation_sessionDelete (resp : Response) (name sessionPath : String)
     (domain sessionSamesite : Option String) : Response := Id.run do
   let deleted := implementation_deleteCookie resp name sessionPath domain sessionSamesite
-  return varyMarked deleted ["Cookie"]
+  return { deleted with varies := deleted.varies ++ ["Cookie"] }
 -- impl-end
 
 -- proof-start
```

Attack 17 — `atk_18_reorder.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -300,7 +300,10 @@
 def implementation_deleteCookie (resp : Response) (key path : String)
     (domain samesite : Option String) : Response := Id.run do
   let secure := deleteSecure key samesite
-  return setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  -- reorder: drop the entry, then write it afresh at the END of the container.
+  -- A function-valued jar cannot observe position, so this is extensionally equal.
+  let base := setCookie resp key "" (some 0) epochExpires path domain secure false samesite
+  return { base with cookies := fun k => base.cookies k }
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A-legs (axioms / deep-model references) + model<->patch correspondence; R/I legs left to G-CONF per instructions.

**SAME-SPEC:** all 17 submitted attacks + pos_control return same_spec=True against the bundle Solution.lean (impl regions only were edited).

**POSITIVE CONTROL:** pos_control.lean -- `bash scripts/lean_verify.sh <f>` -> exit 0; axioms [propext, Quot.sound]; 0 `sorry` in bundle Solution.lean.

**PREPATCH REPRODUCED:** atk_1_prepatch (drops the cross-site policy on deletion, secure forced by key prefix only) -> exit 1. This is the real bug the patch fixes.

### REJECT LANE (all `lean_verify.sh <f>`, exit 1 = correctly refuted):
- atk_1_prepatch (prepatch bug) EXIT=1
- atk_2_maxage_none (boundary: `none` lifetime instead of `some 0`; loses Max-Age=0 on the wire) EXIT=1
- atk_3_restamp_name (ungrounded-oracle echo: right index, rendered name upper-cased) EXIT=1
- atk_4_coded_value (ungrounded-oracle echo: right payload, rendered payload '"deleted"') EXIT=1
- atk_5_comment_stamp (deletion annotates the entry's `comment`) EXIT=1
- atk_6_httponly (adds an httpOnly marking of its own) EXIT=1
- atk_7_no_vary (control-flow-effect: sessions branch drops the vary marking) EXIT=1
- atk_8_del_then_write (control-flow-effect: clears the index first, losing the in-place merge of comment/version/secure/domain/samesite) EXIT=1
- atk_15_messages_vary (frame: messages leg also declares a vary dependency) EXIT=1
- atk_16_session_status_body (frame: sessions leg also resets status=204 and body) EXIT=1
- atk_17_vary_nodedup (A-reference divergence: appends 'Cookie' unconditionally, dropping patch_vary_headers' case-insensitive dedup) EXIT=1
The 12-field carrier + `result = { resp with cookies := result.cookies }` rebuild-frame makes the on-domain result pointwise determined, which is why every on-domain mutation above dies.

### ADMIT LANE (exit 0, clean axioms, faithful patch RESOLVED -> no break):
- atk_9_reserved_noop: no-op on a reserved key. axioms [propext, Quot.sound]. patch_atk_9.diff git-apply-check OK -> RESOLVED (F2P 5/5).
- atk_10_emptykey_bogus: empty key writes a bogus entry at a fixed 'tamper' slot. axioms [propext, Quot.sound]. patch_atk_10.diff -> RESOLVED.
- atk_11_badchars_dropsamesite: out-of-alphabet key falls back to prepatch behavior (drops the policy). axioms [propext, Quot.sound]. patch_atk_11.diff -> RESOLVED.
- atk_13_invalid_samesite: an ill-formed policy is SWALLOWED where real set_cookie raises ValueError. axioms [propext, Classical.choice, Quot.sound] (standard Lean axioms; no sorry, no bundle axiom). patch_atk_13.diff -> RESOLVED.
- atk_14_reserved_mistarget: a reserved key is deleted at an UPPER-CASED index. axioms [propext, Quot.sound]. patch_atk_14.diff -> RESOLVED.
- atk_18_reorder: all 12 components preserved but the entry is re-filed at the END of the ordered container (`self.cookies.pop(key)` then `dict.__setitem__`), changing Set-Cookie emission ORDER -- a dimension `CookieJar : String -> Option Cookie` provably cannot express. axioms [propext, Quot.sound]. patch_atk_18.diff -> RESOLVED. This is the one genuine model-expressiveness gap I found; it is NOT a break because no graded test observes cookie ordering (verified: entry bytes identical, only dict position moves).
GOLD CONTROL: patch.diff -> RESOLVED (F2P 5/5), so the resolve lane is live and discriminating.

WHY THE PARTIAL-DOMAIN LANE IS CLOSED (measured, not argued): `keyAccepted` is EXACTLY the real container's filing domain. Over 329 probes (every chr(1..299) plus curated multi-char cases incl. '', 'path', 'Path', 'samesite', 'a b', 'e-acute', 'a=b', 'a;b', 'a\tb', '`__Secure`-x'), keyAccepted(k) == (SimpleCookie files k) with 0 MISMATCHES; `_LegalChars` == the Lean cookieNameChar alphabet exactly (78 chars, set-equal both ways); Morsel.`_reserved` has 9 keys after `import django.http.cookie` (the repo's setdefault), matching reservedCookieNames. So atk_9/10/11/13/14 buy only genuinely unreachable states -- honest preconditions, not spec slack.

### A-LEG VALIDATION (my assigned focus; both A-references re-measured against the real callees):
- `setCookie` (A-reference for HttpResponseBase.set_cookie, response.py:158-202): 4536 legs over the product of {9 fuzzed PRE-EXISTING entries incl. prior domain/secure/httponly/samesite/comment/version} x {8 keys} x {3 paths} x {3 domains} x {7 samesite values}, comparing ALL TWELVE components read off a real http.cookies.Morsel -> 0 mismatches. The fuzzed prior entry is what makes the four guarded writes (domainAfter/secureAfter/httpOnlyAfter/samesiteAfter) and the two parameterless attributes (comment/version) reachable, so the add-but-never-clear semantics is exercised rather than assumed.
- `valueEncode` (SimpleCookie.value_encode's coded component / `_quote`): 4000 fuzzed payloads over printable + 'e-acute' + CJK + NUL + quote + backslash -> 0 mismatches, incl. the case this routine actually hits, `_quote`('') == '""'.
- `varyMarked`/`variesAfter` (A-reference for django.utils.cache.patch_vary_headers, utils/cache.py:276-298): 70 legs over declared x added lists incl. case variants, duplicates and the `'*'` collapse -> 0 mismatches.
- CARRIER TOTALITY confirmed against the callee's own structure: a Morsel's instance `__dict__` is exactly ['`_key`','`_value`','`_coded_value`'] and `_reserved` has 9 keys = 12, matching Cookie's 12 fields, and inspect of Morsel.OutputString shows it emits nothing outside those. So the enumeration has an external stopping point; there is no 13th slot to stamp unobserved. This closes the gap that refuted the three earlier revisions.

**REFINEMENT.MD LEG AUDIT:** 5 mapped ops, tags = 3 R (op1 deleteSecure, op3 messages call site, op4 sessions call site) + 2 A-reference (op2 setCookie, op5 patch_vary_headers). NO A-consumed and NO kind-3 leg. The axioms region declares no `axiom`/`_prop` at all (comment-only), consistent with axiom_check.py's documented skip and with `#print axioms` showing only standard Lean axioms. Both A-reference correspondences to the real callees hold under the measurements above. The three retraction notes are honest: I re-encoded their claimed-refuted attacks (atk_2 maxage, atk_5 comment stamp, atk_7 no-vary, atk_3 rendered name, atk_4 rendered payload) and all five exit 1 against the current file, so the repairs are real rather than restated.

NON-FINDINGS (recorded so they are not re-litigated): atk_12_double_vary exits 1, but `variesAfter` is IDEMPOTENT (#eval: marking 'Cookie' twice equals marking it once, for [] and ['Accept']), so that impl is extensionally EQUAL to gold and its exit 1 is my own weak proof script, not a spec rejection -- it is no attack and is excluded from the submitted set. Several first-cut admit-lane files also exited 1 purely because the untouched downstream `correct_sessionDelete` could not reduce a newly-branched `implementation_deleteCookie`; I repaired those proofs (destructuring keyAccepted/samesiteValid to kill the off-domain branch) rather than crediting the spec for my own proof failures, which is what turned atk_9/10/11/13/14 into genuine exit-0 verifiers.

**HYGIENE:** base_commit worktree copy left CLEAN (git status empty, HEAD 156a2138db) after every patch check.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 17 admissible attacks re-run of 17 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 17 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1_prepatch.lean`, `atk_2_maxage_none.lean`, `atk_3_restamp_name.lean`, `atk_4_coded_value.lean`, `atk_5_comment_stamp.lean`, `atk_6_httponly.lean`, `atk_7_no_vary.lean`, `atk_8_del_then_write.lean`, `atk_15_messages_vary.lean`, `atk_16_session_status_body.lean`, `atk_17_vary_nodedup.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 6 | `atk_9_reserved_noop.lean`, `atk_10_emptykey_bogus.lean`, `atk_11_badchars_dropsamesite.lean`, `atk_13_invalid_samesite.lean`, `atk_14_reserved_mistarget.lean`, `atk_18_reorder.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl with a closing clean-axiom proof had a faithful patch that failed to resolve. The 6 attacks that DID verify (atk_9, atk_10, atk_11, atk_13, atk_14, atk_18) each had a faithful unified diff materialized, checked with `git apply --check` at base_commit 156a2138db, and RUN through run_resolve: all 6 resolved (F2P 5/5, failure lists empty), as did the gold control. So verify => correct held on every executed probe.
```

**Attacks re-run (17):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 17 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_maxage_none.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_restamp_name.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_coded_value.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_comment_stamp.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_httponly.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_no_vary.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_del_then_write.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9_reserved_noop.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10_emptykey_bogus.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11_badchars_dropsamesite.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_13_invalid_samesite.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 13 — `atk_14_reserved_mistarget.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 14 — `atk_15_messages_vary.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_16_session_status_body.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_17_vary_nodedup.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_18_reorder.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** A-legs (axioms / deep-model references) + model<->patch correspondence; R/I legs left to G-CONF per instructions.

**SAME-SPEC:** all 17 submitted attacks + pos_control return same_spec=True against the bundle Solution.lean (impl regions only were edited).

**POSITIVE CONTROL:** pos_control.lean -- `bash scripts/lean_verify.sh <f>` -> exit 0; axioms [propext, Quot.sound]; 0 `sorry` in bundle Solution.lean.

**PREPATCH REPRODUCED:** atk_1_prepatch (drops the cross-site policy on deletion, secure forced by key prefix only) -> exit 1. This is the real bug the patch fixes.

### REJECT LANE (all `lean_verify.sh <f>`, exit 1 = correctly refuted):
- atk_1_prepatch (prepatch bug) EXIT=1
- atk_2_maxage_none (boundary: `none` lifetime instead of `some 0`; loses Max-Age=0 on the wire) EXIT=1
- atk_3_restamp_name (ungrounded-oracle echo: right index, rendered name upper-cased) EXIT=1
- atk_4_coded_value (ungrounded-oracle echo: right payload, rendered payload '"deleted"') EXIT=1
- atk_5_comment_stamp (deletion annotates the entry's `comment`) EXIT=1
- atk_6_httponly (adds an httpOnly marking of its own) EXIT=1
- atk_7_no_vary (control-flow-effect: sessions branch drops the vary marking) EXIT=1
- atk_8_del_then_write (control-flow-effect: clears the index first, losing the in-place merge of comment/version/secure/domain/samesite) EXIT=1
- atk_15_messages_vary (frame: messages leg also declares a vary dependency) EXIT=1
- atk_16_session_status_body (frame: sessions leg also resets status=204 and body) EXIT=1
- atk_17_vary_nodedup (A-reference divergence: appends 'Cookie' unconditionally, dropping patch_vary_headers' case-insensitive dedup) EXIT=1
The 12-field carrier + `result = { resp with cookies := result.cookies }` rebuild-frame makes the on-domain result pointwise determined, which is why every on-domain mutation above dies.

### ADMIT LANE (exit 0, clean axioms, faithful patch RESOLVED -> no break):
- atk_9_reserved_noop: no-op on a reserved key. axioms [propext, Quot.sound]. patch_atk_9.diff git-apply-check OK -> RESOLVED (F2P 5/5).
- atk_10_emptykey_bogus: empty key writes a bogus entry at a fixed 'tamper' slot. axioms [propext, Quot.sound]. patch_atk_10.diff -> RESOLVED.
- atk_11_badchars_dropsamesite: out-of-alphabet key falls back to prepatch behavior (drops the policy). axioms [propext, Quot.sound]. patch_atk_11.diff -> RESOLVED.
- atk_13_invalid_samesite: an ill-formed policy is SWALLOWED where real set_cookie raises ValueError. axioms [propext, Classical.choice, Quot.sound] (standard Lean axioms; no sorry, no bundle axiom). patch_atk_13.diff -> RESOLVED.
- atk_14_reserved_mistarget: a reserved key is deleted at an UPPER-CASED index. axioms [propext, Quot.sound]. patch_atk_14.diff -> RESOLVED.
- atk_18_reorder: all 12 components preserved but the entry is re-filed at the END of the ordered container (`self.cookies.pop(key)` then `dict.__setitem__`), changing Set-Cookie emission ORDER -- a dimension `CookieJar : String -> Option Cookie` provably cannot express. axioms [propext, Quot.sound]. patch_atk_18.diff -> RESOLVED. This is the one genuine model-expressiveness gap I found; it is NOT a break because no graded test observes cookie ordering (verified: entry bytes identical, only dict position moves).
GOLD CONTROL: patch.diff -> RESOLVED (F2P 5/5), so the resolve lane is live and discriminating.

WHY THE PARTIAL-DOMAIN LANE IS CLOSED (measured, not argued): `keyAccepted` is EXACTLY the real container's filing domain. Over 329 probes (every chr(1..299) plus curated multi-char cases incl. '', 'path', 'Path', 'samesite', 'a b', 'e-acute', 'a=b', 'a;b', 'a\tb', '`__Secure`-x'), keyAccepted(k) == (SimpleCookie files k) with 0 MISMATCHES; `_LegalChars` == the Lean cookieNameChar alphabet exactly (78 chars, set-equal both ways); Morsel.`_reserved` has 9 keys after `import django.http.cookie` (the repo's setdefault), matching reservedCookieNames. So atk_9/10/11/13/14 buy only genuinely unreachable states -- honest preconditions, not spec slack.

### A-LEG VALIDATION (my assigned focus; both A-references re-measured against the real callees):
- `setCookie` (A-reference for HttpResponseBase.set_cookie, response.py:158-202): 4536 legs over the product of {9 fuzzed PRE-EXISTING entries incl. prior domain/secure/httponly/samesite/comment/version} x {8 keys} x {3 paths} x {3 domains} x {7 samesite values}, comparing ALL TWELVE components read off a real http.cookies.Morsel -> 0 mismatches. The fuzzed prior entry is what makes the four guarded writes (domainAfter/secureAfter/httpOnlyAfter/samesiteAfter) and the two parameterless attributes (comment/version) reachable, so the add-but-never-clear semantics is exercised rather than assumed.
- `valueEncode` (SimpleCookie.value_encode's coded component / `_quote`): 4000 fuzzed payloads over printable + 'e-acute' + CJK + NUL + quote + backslash -> 0 mismatches, incl. the case this routine actually hits, `_quote`('') == '""'.
- `varyMarked`/`variesAfter` (A-reference for django.utils.cache.patch_vary_headers, utils/cache.py:276-298): 70 legs over declared x added lists incl. case variants, duplicates and the `'*'` collapse -> 0 mismatches.
- CARRIER TOTALITY confirmed against the callee's own structure: a Morsel's instance `__dict__` is exactly ['`_key`','`_value`','`_coded_value`'] and `_reserved` has 9 keys = 12, matching Cookie's 12 fields, and inspect of Morsel.OutputString shows it emits nothing outside those. So the enumeration has an external stopping point; there is no 13th slot to stamp unobserved. This closes the gap that refuted the three earlier revisions.

**REFINEMENT.MD LEG AUDIT:** 5 mapped ops, tags = 3 R (op1 deleteSecure, op3 messages call site, op4 sessions call site) + 2 A-reference (op2 setCookie, op5 patch_vary_headers). NO A-consumed and NO kind-3 leg. The axioms region declares no `axiom`/`_prop` at all (comment-only), consistent with axiom_check.py's documented skip and with `#print axioms` showing only standard Lean axioms. Both A-reference correspondences to the real callees hold under the measurements above. The three retraction notes are honest: I re-encoded their claimed-refuted attacks (atk_2 maxage, atk_5 comment stamp, atk_7 no-vary, atk_3 rendered name, atk_4 rendered payload) and all five exit 1 against the current file, so the repairs are real rather than restated.

NON-FINDINGS (recorded so they are not re-litigated): atk_12_double_vary exits 1, but `variesAfter` is IDEMPOTENT (#eval: marking 'Cookie' twice equals marking it once, for [] and ['Accept']), so that impl is extensionally EQUAL to gold and its exit 1 is my own weak proof script, not a spec rejection -- it is no attack and is excluded from the submitted set. Several first-cut admit-lane files also exited 1 purely because the untouched downstream `correct_sessionDelete` could not reduce a newly-branched `implementation_deleteCookie`; I repaired those proofs (destructuring keyAccepted/samesiteValid to kill the off-domain branch) rather than crediting the spec for my own proof failures, which is what turned atk_9/10/11/13/14 into genuine exit-0 verifiers.

**HYGIENE:** base_commit worktree copy left CLEAN (git status empty, HEAD 156a2138db) after every patch check.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

FAITHFULNESS-BREAK attack on django__django-13195/lean. No divergence found between the modeled functions and the real POST-PATCH repo behavior. Reference discipline: built a private copy of the base-commit worktree, applied patch.diff, and CONFIRMED the loaded module is the patched one (inspect.getsource(HttpResponseBase.delete_cookie) contains the samesite disjunct) before any comparison. Important trap caught: my first probe run silently imported a pre-patch Django from elsewhere on the import path, because sys.path[0] is the script's own directory; that produced 9 bogus 'REAL RAISED / unexpected keyword samesite' hits, and they vanish when the probe is pinned to the patched tree. Applied the instance test_patch and confirmed all 5 F2P pass on my reference (7 tests OK), so the reference is the right one.

### EVIDENCE (all differential, oracle reads back off a REAL http.cookies.Morsel, nothing asserted by my shadow):
1. deleteCookie, 200,000 randomized draws over (key, path, domain, samesite, fuzzed pre-existing entry at the same index, bystander entry): checked=200000 mismatches=0. All twelve Morsel components compared, plus the frame (bystander entry byte-identical, index set exactly {key, bystander}).
2. EXHAUSTIVE over the whole admissible samesite domain. samesiteValid admits exactly 90 values (None, "", and all 2^3+2^4+2^6 case-variants of lax/none/strict); crossed with 13 keys x 3 paths x 3 domains x 4 prior-entry shapes: checked=42120 skipped=0 mismatches=0. This covers every soundness-critical point of the fix, including the case-insensitive 'none' -> secure forcing (nOnE, NONE, ...) and the `__Secure`-/`__Host`- prefixes.
3. valueEncode vs the real SimpleCookie.value_encode/`_quote`: 81,045 payloads (empty, every codepoint 0..0x2FF, sampled codepoints to 0x10FFFF, random strings over an alphabet including " \\ , ; controls and astral chars): 0 mismatches. `_quote`('') == '""' confirmed, which is the case a deletion actually hits.
4. Lean-source-level proof that my Python transliteration is faithful (this is what closes the shadow-drift hole): #eval fingerprints of cookieNameChar and cookieUnescapedChar over ALL 1,114,112 codepoints give (78, 6374, <hash>) and (91, 7276, <hash>), IDENTICAL to the same fingerprints of `_LegalChars` and `_UnescapedChars`. Also captured Lean quoteChar over all 256 bytes and it is byte-for-byte EQUAL to ''.join(chr(n).translate(`_Translator`)). Lean Char.isAlphanum confirmed ASCII-only (é/É/中/fullwidth-A/Arabic-indic-3 all false) and String.toLower ASCII-only, so no Unicode over-admission.
5. keyAccepted boundary, BOTH directions, vs real Morsel.set via SimpleCookie.`__setitem__`: 60,630 keys ('' , all 9 reserved names and their case variants, chr(0..0x24F), control/separator chars, random strings): 0 mismatches. Precondition is exactly the callee domain, neither too strong nor too weak.
6. samesiteValid boundary, BOTH directions, vs the real ValueError in set_cookie: 127,312 candidates including near-misses ('laxx','la','lax ','strict\n') and unicode confusables (Cyrillic-a Lax, fullwidth, 'İax', 'ſtrict', U+212A): 0 mismatches. Separately verified no non-ASCII codepoint lowers into any letter of 'nonelaxstrict', so the ASCII-only toLower cannot under-reject.
7. variesAfter vs the real patch_vary_headers: 4,010 pre-existing Vary states: 0 mismatches (case-insensitive dedup, order preserved, `'*'` collapse).
8. BOTH CALL SITES driven through real Django, not just the shared callee: CookieStorage.`_update_cookie`('') deletion branch and SessionMiddleware.process_response empty-session branch, 612 configurations over SESSION_COOKIE_SAMESITE/DOMAIN/PATH x pre-existing Vary: 0 mismatches, including the vary marking and the header/status/body frame (X-Keep, 201, b'body' all unmoved).
9. Witness-level cross-check: captured Lean #eval of implementation_deleteCookie on 7 hand-picked witnesses (incl. a fully-populated prior entry exercising the comment/version carry-over and the four guarded *After writes) and ran the real patched Django on the SAME 7 inputs; all twelve components agree on every one, and the 3 vary #evals agree too.

**SPEC INTEGRITY:** lean_verify.sh exit 0; #print axioms on all three theorems gives [propext, Quot.sound] only -- no sorryAx, proof is real. markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) = True with identical signature sha256 40a666574434fa5ed648b000984a2c7dc2878f404b427a2daecf23ae83dbc1d1 (308 spec lines), so the spec region is byte-identical and the discriminator differs only in the impl region.

DISCRIMINATION CONTROL (guards against a vacuously-weak spec): the prepatch impl is not merely sorry'd -- I PROVED it violates the spec. Substituting the prepatch body into the gold file and adding `theorem prepatch_violates : ¬ problem_spec_deleteCookie emptyResponse "sessionid" "/" none (some "none") (implementation_deleteCookie ...)` elaborates with exit 0. So the spec strictly rejects the dropped-samesite behavior at a keyAccepted/samesiteValid input.

OVER-STRENGTH ANALYSIS (the faithfulness-break angle proper): the spec's strongest clauses are maxAge = some 0 (not none), codedValue = valueEncode "" (= '""', not ""), c.key = key, and the comment/version carry-over. Each was checked against the real Morsel and each is what the real callee actually produces -- none is an invention. The *After helpers correctly encode that set_cookie can ADD but never CLEAR domain/secure/httponly/samesite (verified on witnesses 5-7, where a prior Strict/secure/httponly entry survives a deletion with samesite='' / None exactly as the model says). The twelve-component carrier is TOTAL, not a projection: Morsel.`__init__` sets exactly `_key`/`_value`/`_coded_value` plus the 9 `_reserved` keys (measured: vars(morsel) == those 3, sorted(morsel.keys()) == those 9, len(`_reserved`) == 9 after the django.http.cookie setdefault), so there is no thirteenth slot the spec fails to frame. refinement.md's three retraction rounds are accurate and the previously-refuted attacks (maxage default, comment stamp, no_vary, morsel key restamp, coded_value restamp) are all genuinely closed by the current carrier.

CAVEAT (does not affect the verdict): measurements are on CPython 3.10.20 while the eval container is 3.6.13. The bundle documents this and it is the one place the interpreters differ (3.6 stdlib `_reserved` lacks samesite; the repo's django/http/cookie.py setdefault supplies it). I verified `_LegalChars`/`_UnescapedChars`/`_quote`/`_Translator` are the code paths cited and that conformance_check.py imports from django.http.cookie rather than http.cookies, which is the correct mitigation. I did not re-run the fuzz inside a 3.6.13 container.

**SCOPE NOT COVERED:** I did not run the full 382-test P2P suite; I did not exercise the non-deletion branches of set_cookie (datetime expires, max_age arithmetic), which are outside the modeled region and correctly outside the spec.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

G-PANEL-3 (leakage / gold-reconstruction), django__django-13195/lean, judged against the SOLVER-VISIBLE problem_statement ONLY (hints_text, 140 chars, deliberately not read for the judgement).

NO RELAXATION IN THIS BUNDLE -- checked first, because the role prompt anticipates one. `ls -a lean/` shows no RELAXED_LEAKAGE.md; `find . -iname '*RELAX*'` from the instance root -> nothing; meta.json top-level keys are [axioms, conf_skip, deep_model_references, gates, modeled_functions, opaque_callees, patch_equals_gold, pbt_audit, prepatch_variants, region_hashes, schema_version, spec_provenance, verifier_pins] -- no `relaxed_leakage`. gates['G-LEAK'] is status=pass, mode='strict'. So there is no unavoidability argument to re-derive and no facet carve-out: this verdict covers the WHOLE spec view and rests on my own measurements below.

**NO FILE IN THE BUNDLE ADDRESSES ME.** leakage.reviewer_directed() over refinement.md, mapping.md and verdict.md -> [] for all three. grep -niE 'auditor|reviewer|panel|submit|verdict|no-leakage|honest|recording convention|do not report' over refinement.md + mapping.md -> one incidental hit ('an honest boundary', refinement.md:196, prose about the model, not a directive). verdict.md contains PRIOR role records including a previous G-PANEL-3 'pass'; those are past measurements, they are STALE (see incidental 1), and I did not rely on any of them.

### WHAT I RAN (my measurements, not meta.json's assertions)
1. markers.spec_view(Solution.lean, lean backend) -> sha256 b09c49b763a7d3007ab1963798fa14ab91a5db4a086f97dcddd6ad0da524c21d; file sha 5091cacfe5d00ee4952c5ebd229a307cf32e90144188c8b147589cb404992288. All six of my recomputed region_hashes match BOTH meta.json's top-level block and gates['G-HYGIENE'].data.region_hashes byte-for-byte (they agree with each other this revision). So the view I judged is the one the gates were stamped on and the one a consumer would receive.
2. markers.same_spec(Solution.lean, Solution_prepatch.lean, lean) -> True. The spec region is byte-identical across the pair, so the prepatch discriminates on the IMPL region alone and no part of the fix hides in a spec-side difference.
3. lean_verify.sh Solution.lean -> exit 0; appended `#print axioms` for all three theorems -> each 'depends on axioms: [propext, Quot.sound]'. No sorryAx: the view is the projection of a genuinely closed file. lean_verify.sh Solution_prepatch.lean -> exit 3, 'declaration uses sorry' at 309/336/369 (all three correct_*), i.e. the prepatch is really refuted, so the spec's discriminating power is not vacuous.
4. leakage.screen(Solution.lean, lean, gold_patch, problem_statement, test_patch) -> hard_failures=[], warnings=[]. I then re-ran the sub-rules by hand rather than trusting the aggregate. Diff markers: none of `_LEAN_DIFF_MARKERS` in the view. Gold-line reproduction: normalized-whitespace containment of every +/- line of patch.diff (len>=8 filter) against the normalized view -> ZERO containments. Patched paths: 'response.py', 'cookie.py', 'middleware.py', 'django/' -> all absent. Patched symbols: 'delete_cookie', 'process_response', '`_update_cookie`', 'set_signed_cookie' -> all absent from identifiers AND from comments/docstrings. Narration: bug/fix/patch/previously/wrong/broken/regression/should/'no longer'/'now ' -> 0 occurrences each. Test-leak sweep (not required for formal flavors, run anyway): no test_patch file path or def-name appears in the view; no FAIL_TO_PASS token ('test_delete_cookie_samesite', 'test_delete_cookie_secure_samesite_none', 'test_session_delete_on_end', ...) appears.
5. Elision confirmed: all three impl regions render as '-- implementation elided -- supplied by the consumer' and all three proof regions as '-- proof elided'; `implementation_deleteCookie` body and `setCookie resp key ...` do not appear in the view.

### GOLD-RECONSTRUCTION ANALYSIS (the substantive question)
The view does state the FIXED behavior openly: `deleteSecure key samesite` forces secure on '`__Secure`-'/'`__Host`-' prefix OR a truthy case-insensitive 'none' policy, and problem_spec_deleteCookie pins `c.samesite = samesiteAfter resp.cookies key samesite`. I asked whether that gives a solver anything the public statement does not, and it does not -- this issue is unusually self-disclosing.

Substring-verified against problem_statement: title 'HttpResponse.delete_cookie() should preserve cookie's samesite'; 'It also is only setting Secure if the cookie's key begins with Secure or Host'; 'Chrome and Firefox will soon begin ignoring Set-Cookie headers with Samesite=None that aren't marked Secure' (that IS the secure-on-none discriminator, stated publicly); and the reporter INLINES their own trial patch, so 'samesite', 'SESSION_COOKIE_SAMESITE', '`__Secure`-', '`__Host`-', 'max_age=0', 'delete_cookie' and the exact epoch stamp 'Thu, 01 Jan 1970 00:00:00 GMT' are each literally present in the statement. Every discriminating clause in the spec view is a restatement of text the solver already reads.

Two residual candidates considered and rejected: (i) problem_spec_sessionDelete naming a session-cookie call site with its varies/'Cookie' declaration -- the sessions middleware path is independently public because MODES_WITH_SPEC={1,2} is a subset of MODES_WITH_LOCALIZATION={0,1,2,100} (eval/dataset.py:63-64), so any mode shipping spec_view also ships changed_files, and data/eval_localization.json for this instance lists django/contrib/sessions/middleware.py plus repo_symbol SessionMiddleware.process_response; moreover the patch_vary_headers behavior is pre-patch behavior, not the gold edit, so pinning it gives no purchase on the samesite/secure change.

(ii) the identity/frame hardening in deletesCookie (c.key = key, c.codedValue = valueEncode "", and the (forall k, k != key -> jar k = resp.cookies k) frame) -- those clauses hold identically pre- and post-patch (the prepatch satisfies them; it fails only on samesite/secure), so they are spec-strength hardening, not gold-edit disclosure. NET: the spec view contains nothing a solver could not have written from problem_statement alone. NO-LEAKAGE.

### INCIDENTAL (other gates' surface; recorded so no reader mistakes them for this finding)
1. **STALE ROLE RECORDS.** G-EQ, G-PANEL, G-PANEL-1 are stamped on Solution.lean sha 392235fa...; G-PANEL-2 and the prior G-PANEL-3 on 1dafe07e...; the current file is 5091cacf.... Only G-AX, G-CONF, G-DIFF, G-GOLD, G-HYGIENE, G-INTEGRITY, G-LEAK, G-MUT, G-PBT, G-VERIFY are stamped on the current hash (G-RESOLVE carries no Solution.lean source). The recorded G-EQ/G-PANEL-1 BREAK (atk_2_morsel_key: rendered Morsel.key unpinned) is evidence about a superseded file -- the current deletesCookie pins both c.key and c.codedValue -- but re-running those roles is not my gate; flagging for re-audit routing, not repair. My own disposition leans on no failing gate: with no relaxation, leakage is decided on the view itself.
2. refinement.md and mapping.md are stale w.r.t. Solution.lean (they describe a `Cookie.name` field the shipped structure does not have; identity is now the CookieJar index). refinement.md also narrates the prior spec defect explicitly ('spec repair', 'was false as written'). Neither file is consumer-visible -- eval/dataset.as_dict ships only instance_id/repo/base_commit/mode/backend/problem_statement (+hints_text, +localization/changed_files, +spec_view/modeled_functions/float_encoding) -- so this is a doc-accuracy defect with no leakage consequence.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
