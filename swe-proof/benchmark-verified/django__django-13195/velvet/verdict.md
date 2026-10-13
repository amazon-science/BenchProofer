# P2 adversarial audit — django__django-13195

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_2_prepatch.lean`, `atk_3_prepatch_securenone.lean`, `atk_4_partial_domain.lean`, `atk_5_boundary_samesite_case.lean`, `atk_6_double_file.lean`, `atk_7_replace_not_merge.lean`, `atk_9_test_shaped_echo.lean`, `atk_10_msg_literal_name.lean`, `atk_11_partial_filed.lean`, `atk_12_no_announced_name.lean`, +9 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1_literal_record.lean`, `atk_8_inline_session_site.lean`, `atk_17_partial_recordable.lean` |

**Non-vacuity.** The positive control `pos_0_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 22 same-spec wrong impls (all same_spec=True); 19 rejected by lean_verify.sh (exit 1); 3 verified (exit 0) and ALL THREE had their faithful refined patch materialized, git-apply-checked at base_commit 156a2138db, and RUN through the official harness (swebench_unified.harness.run_resolve) -> all three measured completed=True resolved=True, FAIL_TO_PASS 5/5, PASS_TO_PASS 382/382. No verify-but-not-resolve witness exists among them, so verify=>correct is not falsified on this attack surface.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_literal_record.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,7 +270,13 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
+    let entry : Cookie :=
+      { name := key, transmittedName := key,
+        value := "", codedValue := quotedEmptyBody,
+        maxAge := clearedMaxAge, expires := some epochExpiry, secure := secure,
+        httpOnly := false, samesite := samesite, path := path, domain := domain,
+        comment := none, version := none }
+    let out := fileDirective filed entry
     return out
     -- impl-end
 
```

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -269,8 +269,8 @@
                   (mkCookie key (secureForClear key samesite) samesite path domain)
   do
     -- impl-start
-    let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
+    let secure := hasSecurePrefix key
+    let out := fileDirective filed (mkCookie key secure none path domain)
     return out
     -- impl-end
 
```

Attack 3 — `atk_3_prepatch_securenone.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -269,7 +269,7 @@
                   (mkCookie key (secureForClear key samesite) samesite path domain)
   do
     -- impl-start
-    let secure := secureForClear key samesite
+    let secure := hasSecurePrefix key
     let out := fileDirective filed (mkCookie key secure samesite path domain)
     return out
     -- impl-end
```

Attack 4 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,10 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    if key.toList.all nameChar && domainStated domain then
+      return fileDirective filed (mkCookie key secure samesite path domain)
+    else
+      return []
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 5 — `atk_5_boundary_samesite_case.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -269,7 +269,7 @@
                   (mkCookie key (secureForClear key samesite) samesite path domain)
   do
     -- impl-start
-    let secure := secureForClear key samesite
+    let secure := hasSecurePrefix key || (samesite == some "none")
     let out := fileDirective filed (mkCookie key secure samesite path domain)
     return out
     -- impl-end
```

Attack 6 — `atk_6_double_file.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,7 +270,9 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
+    let c := mkCookie key secure samesite path domain
+    let mid := fileDirective filed c
+    let out := fileDirective mid c
     return out
     -- impl-end
 
```

Attack 7 — `atk_7_replace_not_merge.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,7 +270,9 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
+    let c := mkCookie key secure samesite path domain
+    let hit := filed.any (fun d => d.name == c.name)
+    let out := if hit then filed.map (fun d => if d.name == c.name then c else d) else filed ++ [c]
     return out
     -- impl-end
 
```

Attack 8 — `atk_8_inline_session_site.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -316,7 +316,8 @@
                     configuredPolicy path domain)
   do
     -- impl-start
-    let out ← deleteCookie filed sessionName path domain configuredPolicy
+    let out := fileDirective filed (mkCookie sessionName
+                 (secureForClear sessionName configuredPolicy) configuredPolicy path domain)
     return out
     -- impl-end
 
```

Attack 9 — `atk_9_test_shaped_echo.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,10 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    if key == "sessionid" || key == "messages" || key == "c" then
+      return fileDirective filed (mkCookie key secure samesite path domain)
+    else
+      return []
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 10 — `atk_10_msg_literal_name.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -293,7 +293,7 @@
                     configuredPolicy "/" domain)
   do
     -- impl-start
-    let out ← deleteCookie filed cookieName "/" domain configuredPolicy
+    let out ← deleteCookie filed "messages" "/" domain configuredPolicy
     return out
     -- impl-end
 
```

Attack 11 — `atk_11_partial_filed.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,10 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    if filed.isEmpty then
+      return fileDirective filed (mkCookie key secure samesite path domain)
+    else
+      return filed
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 12 — `atk_12_no_announced_name.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,13 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    let entry : Cookie :=
+      { name := key, transmittedName := "",
+        value := "", codedValue := quotedEmptyBody,
+        maxAge := clearedMaxAge, expires := some epochExpiry, secure := secure,
+        httpOnly := false, samesite := samesite, path := path, domain := domain,
+        comment := none, version := none }
+    return fileDirective filed entry
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 13 — `atk_13_unquoted_body.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,13 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    let entry : Cookie :=
+      { name := key, transmittedName := key,
+        value := "", codedValue := "",
+        maxAge := clearedMaxAge, expires := some epochExpiry, secure := secure,
+        httpOnly := false, samesite := samesite, path := path, domain := domain,
+        comment := none, version := none }
+    return fileDirective filed entry
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 14 — `atk_14_no_lifetime.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,13 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    let entry : Cookie :=
+      { name := key, transmittedName := key,
+        value := "", codedValue := quotedEmptyBody,
+        maxAge := none, expires := none, secure := secure,
+        httpOnly := false, samesite := samesite, path := path, domain := domain,
+        comment := none, version := none }
+    return fileDirective filed entry
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 15 — `atk_15_oracle_echo.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,10 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    if (key == "sessionid" && path == "/") || (key == "c") || (key == "messages") then
+      return fileDirective filed (mkCookie key secure samesite path domain)
+    else
+      return fileDirective filed (mkCookie key secure samesite path none)
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 16 — `atk_16_msg_drop_policy.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -293,7 +293,7 @@
                     configuredPolicy "/" domain)
   do
     -- impl-start
-    let out ← deleteCookie filed cookieName "/" domain configuredPolicy
+    let out ← deleteCookie filed cookieName "/" domain none
     return out
     -- impl-end
 
```

Attack 17 — `atk_17_partial_recordable.lean` → correct echo (verifies AND its patch resolves — not a weakness) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,10 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    if recordableKey key && domainStated domain then
+      return fileDirective filed (mkCookie key secure samesite path domain)
+    else
+      return []
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 18 — `atk_18_partial_empty_domain.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,10 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    if domain == some "" then
+      return []
+    else
+      return fileDirective filed (mkCookie key secure samesite path domain)
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 19 — `atk_19_partial_bad_policy.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,10 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    if samesite == some "" || samesite == some "bogus" then
+      return []
+    else
+      return fileDirective filed (mkCookie key secure samesite path domain)
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 20 — `atk_20_diverge.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,6 +270,9 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
+    let mut i := 0
+    while i < 1 do
+      i := i
     let out := fileDirective filed (mkCookie key secure samesite path domain)
     return out
     -- impl-end
```

Attack 21 — `atk_21_prepend.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,11 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    let c := mkCookie key secure samesite path domain
+    if filed.any (fun d => d.name == c.name) then
+      return filed.map (fun d => if d.name == c.name then mergeDirective d c else d)
+    else
+      return [c] ++ filed
     -- impl-end
 
 prove_correct deleteCookie by
```

Attack 22 — `atk_22_httponly.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -270,8 +270,13 @@
   do
     -- impl-start
     let secure := secureForClear key samesite
-    let out := fileDirective filed (mkCookie key secure samesite path domain)
-    return out
+    let entry : Cookie :=
+      { name := key, transmittedName := key,
+        value := "", codedValue := quotedEmptyBody,
+        maxAge := clearedMaxAge, expires := some epochExpiry, secure := secure,
+        httpOnly := true, samesite := samesite, path := path, domain := domain,
+        comment := none, version := none }
+    return fileDirective filed entry
     -- impl-end
 
 prove_correct deleteCookie by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_0_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base.lean copied from bundle Solution.lean; ONLY impl regions edited; same_spec confirmed True for all 23 files (22 attacks + positive control) via swebench_unified.markers.same_spec with backend velvet. Verify cmd: `bash scripts/lean_verify.sh <file>` from repo root, run as concurrent background jobs, batches of <=4 (schedule only; every attack fully verified). Full tally in results.txt.

**POSITIVE CONTROL:** pos_0_gold.lean (byte-identical to bundle) -> exit 0. PREPATCH REPRODUCED: atk_2_prepatch.lean (secure = hasSecurePrefix key only, policy dropped -> mkCookie ... none ...) -> exit 1 REJECTED; atk_3_prepatch_securenone.lean (policy forwarded, none-secure disjunct dropped) -> exit 1 REJECTED. So the spec discriminates both halves of the change (A4 policy carry-through, A5 secure-on-none).

REJECTED (exit 1, 19): atk_2/atk_3 prepatch twins; atk_4_partial_domain + atk_17? no (17 verified) -> atk_4 (guard on nameChar/domainStated, return [] outside); atk_5_boundary_samesite_case (case-SENSITIVE `samesite == some "none"` instead of toLower -- boundary); atk_6_double_file (files the same directive twice); atk_7_replace_not_merge (replaces instead of mergeDirective, dropping sticky secure/httponly/domain/samesite); atk_9_test_shaped_echo + atk_15_oracle_echo (ungrounded oracle echo: correct only on the literal names sessionid/messages/c the behaviour's own checks use); atk_10_msg_literal_name (message site substitutes literal "messages" addressee); atk_11_partial_filed (partial on the unconstrained `filed` input); atk_12_no_announced_name (transmittedName := "" -- THE PRIOR PASS'S EXACT COUNTEREXAMPLE, now REJECTED, confirming the A10 repair took); atk_13_unquoted_body (codedValue := "" i.e. `k=` not `k=""` -- the earlier pass's A9 defect, rejected); atk_14_no_lifetime (maxAge/expires := none: right flags, cookie survives the session -- the earlier A8 defect, rejected); atk_16_msg_drop_policy (message site passes none); atk_18_partial_empty_domain / atk_19_partial_bad_policy (partial on the regions domainStated/acceptedPolicy exclude); atk_20_diverge (non-termination under total semantics); atk_21_prepend (prepends instead of appends -- frame/order); atk_22_httponly (sets the script-inaccessible flag the real directive never sets).

VERIFIED->RESOLVE-CHECKED (3, the mandatory leg):
1) atk_1_literal_record.lean (exit 0) -- assembles the 13-field Cookie record LITERALLY in deleteCookie's impl, bypassing mkCookie, the bundle's only binding to the real unchanged callee set_cookie. This is the re-encoding of the PRIOR PASS'S NAMED counterexample atk_1_morsel_key adapted to the 13-field carrier. Faithful patch atk_1_faithful.diff builds the morsel in place via `Morsel().set(key,'','""')` + attribute writes + `dict.__setitem__(self.cookies,key,entry)`, reusing an existing morsel so mergeDirective's sticky-attribute semantics are honored. `cd wt && git apply --check atk_1_faithful.diff` -> OK. run_resolve -> completed=True resolved=True, F2P 5/5, P2P 382/382 (resolve_atk1.json). WHY IT NOW RESOLVES: the crucial `.set(key,...)` gives the morsel its OWN `_key`, which is exactly what the new A10/transmittedName clause forces; the prior counterexample omitted it and emitted `Set-Cookie: None=""`.
2) atk_8_inline_session_site.lean (exit 0) -- clearSessionCookie INLINES the setter (files via mkCookie directly) instead of delegating to the changed callee deleteCookie. Faithful patch atk_8_faithful.diff inlines the secure derivation + set_cookie at the middleware clear site. git apply --check OK. run_resolve -> completed=True resolved=True, F2P 5/5, P2P 382/382 (resolve_atk8.json). Correctly resolves: inlining is an observationally equivalent refactor of the same call site; the forwarded policy still reaches the morsel.
3) atk_17_partial_recordable.lean (exit 0) -- PARTIAL DOMAIN guarded on the precondition itself (`if recordableKey key && domainStated domain` else `return []`); this is the shape a prior pass recorded as same-spec AND verifying. Faithful patch atk_17_faithful.diff reproduces the guard in delete_cookie and clears the container outside it. git apply --check OK. run_resolve -> completed=True resolved=True, F2P 5/5, P2P 382/382 (resolve_atk17.json). Resolves because the excluded region is UNREACHABLE from the test suite: measured -- every key the F2P/P2P checks clear (c, `__Secure`-c, `__Host`-c, sessionid, messages) is recordable, no test passes an empty/illegal name to delete_cookie, and no settings override sets SESSION_COOKIE_DOMAIN=''. The requires are thus a legitimate carve-out of a region where the UNCHANGED callee raises (verified: all 39 excluded names raise and record nothing), not a smuggled weakness.

### A-LEG AUDIT (the assigned focus; independent probes, not the bundle's own oracles).
(a) mkCookie A-reference == real set_cookie: re-derived independently over all 13 fields; 0 mismatches.

(b) THE REGION BOTH BUNDLE ORACLES MISS: axiom_check.py and conformance_check.py each use a FRESH HttpResponse() per case, so neither ever exercises filing over a PRE-EXISTING entry -- i.e. mergeDirective is unvalidated by the shipped oracles. I wrote an independent differential over 1400 cases (5 keys x 2 paths x 2 domains x 7 policies x 10 pre-existing-entry shapes incl. pre-set secure/httponly/domain/samesite/max_age/expires/path) comparing the real patched delete_cookie against the Lean mergeDirective field-for-field: 0 MISMATCHES. mergeDirective's sticky-vs-restated split (secure/httponly OR-ed, maxAge/samesite/domain/comment/version sticky-if-absent, name/transmittedName/value/codedValue/expires/path restated) is faithful.

(c) fileDirective frame/arity: measured -- a clear leaves other cookies' entries byte-identical and adds exactly one entry.

(d) recordableKey/domainStated boundary confirmed BOTH ways independently: every excluded name raises and records nothing; domain='' collapses to the morsel's unset sentinel, so absent/empty are genuinely indistinguishable there (justifying the carve-out rather than hiding behavior).

(e) CARRIER COMPLETENESS -- the prior pass's stated residual risk. Python's Morsel state is exactly {`_key`,`_value`,`_coded_value`} + the 9 `_reserved` attrs; the 13-field carrier covers all of it plus the container key, so there is no 14th field left free (this is what closes the field-chasing treadmill). I also tested the prior pass's specific warning about attribute ORDER: 4000 entries built by two different construction routes with randomized attribute insertion orders, bucketed by their 13-field tuple -> 2928 distinct tuples, 0 with more than one distinct emitted header. The emitted header is a FUNCTION of the carried observables, so refinement.md §E's termination claim is measured, not asserted.

**REFINEMENT.MD AUDIT:** 18 legs (A1-A10, B1-B4, C1-C4). Tag inventory: 1 R, 7 plain I, 2 I(callee-under-spec), 2 I(via callee's contract), 3 I+frame variants, 1 A-reference+I, 2 A-reference+directive-frame. Every leg is R / A-reference / I -- NO kind-3 (§D's claim holds). No A-consumed legs exist (the sole 'A-consumed' occurrence is the tag-legend line), consistent with the axioms region declaring none, so there is no axiom-soundness trust point. A-reference correspondence to the real callee (set_cookie at response.py:158, unchanged by the patch) holds per (a)/(b). Gold-hunk quotes in §A/§B/§C match patch.diff verbatim; the C5 frame note (patch_vary_headers left outside Filed) is a legitimate unchanged-context frame and is independently covered by test_session_delete_on_end's Vary assertion.

ONE DOC NIT (not a soundness defect, no gate impact): refinement.md line 36 (leg A3) still says mkCookie is modeled on its 'TWELVE touched fields'; the carrier, both oracles, mapping.md and §E all say THIRTEEN (the count after transmittedName/A10 was added). Stale word from the last repair pass -- the leg itself is correct.

**VERDICT:** SOUND. 22 distinct same-spec attacks run (partial-domain x4, boundary x2, control-flow-effect x4, ungrounded-oracle-echo x2, directive-frame x4, call-site x3, prepatch x2, plus the prior named counterexample), positive control verifies, prepatch bug reproduced and rejected, and every one of the 3 verifying impls had its faithful patch materialized and EXECUTED through the official harness with resolved=True. No verify-but-not-resolve witness found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 22 admissible attacks re-run of 22 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 22 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 19 | `atk_2_prepatch.lean`, `atk_3_prepatch_securenone.lean`, `atk_4_partial_domain.lean`, `atk_5_boundary_samesite_case.lean`, `atk_6_double_file.lean`, `atk_7_replace_not_merge.lean`, `atk_9_test_shaped_echo.lean`, `atk_10_msg_literal_name.lean`, `atk_11_partial_filed.lean`, `atk_12_no_announced_name.lean`, +9 more |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 3 | `atk_1_literal_record.lean`, `atk_8_inline_session_site.lean`, `atk_17_partial_recordable.lean` |

**Non-vacuity.** The positive control `pos_0_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
NONE FOUND. 22 same-spec wrong impls (all same_spec=True); 19 rejected by lean_verify.sh (exit 1); 3 verified (exit 0) and ALL THREE had their faithful refined patch materialized, git-apply-checked at base_commit 156a2138db, and RUN through the official harness (swebench_unified.harness.run_resolve) -> all three measured completed=True resolved=True, FAIL_TO_PASS 5/5, PASS_TO_PASS 382/382. No verify-but-not-resolve witness exists among them, so verify=>correct is not falsified on this attack surface.
```

**Attacks re-run (22):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 22 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1_literal_record.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_prepatch_securenone.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_partial_domain.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_boundary_samesite_case.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_double_file.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_replace_not_merge.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_inline_session_site.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9_test_shaped_echo.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10_msg_literal_name.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11_partial_filed.lean` → rejected (same spec, does not verify — good)

Attack 12 — `atk_12_no_announced_name.lean` → rejected (same spec, does not verify — good)

Attack 13 — `atk_13_unquoted_body.lean` → rejected (same spec, does not verify — good)

Attack 14 — `atk_14_no_lifetime.lean` → rejected (same spec, does not verify — good)

Attack 15 — `atk_15_oracle_echo.lean` → rejected (same spec, does not verify — good)

Attack 16 — `atk_16_msg_drop_policy.lean` → rejected (same spec, does not verify — good)

Attack 17 — `atk_17_partial_recordable.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 18 — `atk_18_partial_empty_domain.lean` → rejected (same spec, does not verify — good)

Attack 19 — `atk_19_partial_bad_policy.lean` → rejected (same spec, does not verify — good)

Attack 20 — `atk_20_diverge.lean` → rejected (same spec, does not verify — good)

Attack 21 — `atk_21_prepend.lean` → rejected (same spec, does not verify — good)

Attack 22 — `atk_22_httponly.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_0_gold.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**PROTOCOL.** base.lean copied from bundle Solution.lean; ONLY impl regions edited; same_spec confirmed True for all 23 files (22 attacks + positive control) via swebench_unified.markers.same_spec with backend velvet. Verify cmd: `bash scripts/lean_verify.sh <file>` from repo root, run as concurrent background jobs, batches of <=4 (schedule only; every attack fully verified). Full tally in results.txt.

**POSITIVE CONTROL:** pos_0_gold.lean (byte-identical to bundle) -> exit 0. PREPATCH REPRODUCED: atk_2_prepatch.lean (secure = hasSecurePrefix key only, policy dropped -> mkCookie ... none ...) -> exit 1 REJECTED; atk_3_prepatch_securenone.lean (policy forwarded, none-secure disjunct dropped) -> exit 1 REJECTED. So the spec discriminates both halves of the change (A4 policy carry-through, A5 secure-on-none).

REJECTED (exit 1, 19): atk_2/atk_3 prepatch twins; atk_4_partial_domain + atk_17? no (17 verified) -> atk_4 (guard on nameChar/domainStated, return [] outside); atk_5_boundary_samesite_case (case-SENSITIVE `samesite == some "none"` instead of toLower -- boundary); atk_6_double_file (files the same directive twice); atk_7_replace_not_merge (replaces instead of mergeDirective, dropping sticky secure/httponly/domain/samesite); atk_9_test_shaped_echo + atk_15_oracle_echo (ungrounded oracle echo: correct only on the literal names sessionid/messages/c the behaviour's own checks use); atk_10_msg_literal_name (message site substitutes literal "messages" addressee); atk_11_partial_filed (partial on the unconstrained `filed` input); atk_12_no_announced_name (transmittedName := "" -- THE PRIOR PASS'S EXACT COUNTEREXAMPLE, now REJECTED, confirming the A10 repair took); atk_13_unquoted_body (codedValue := "" i.e. `k=` not `k=""` -- the earlier pass's A9 defect, rejected); atk_14_no_lifetime (maxAge/expires := none: right flags, cookie survives the session -- the earlier A8 defect, rejected); atk_16_msg_drop_policy (message site passes none); atk_18_partial_empty_domain / atk_19_partial_bad_policy (partial on the regions domainStated/acceptedPolicy exclude); atk_20_diverge (non-termination under total semantics); atk_21_prepend (prepends instead of appends -- frame/order); atk_22_httponly (sets the script-inaccessible flag the real directive never sets).

VERIFIED->RESOLVE-CHECKED (3, the mandatory leg):
1) atk_1_literal_record.lean (exit 0) -- assembles the 13-field Cookie record LITERALLY in deleteCookie's impl, bypassing mkCookie, the bundle's only binding to the real unchanged callee set_cookie. This is the re-encoding of the PRIOR PASS'S NAMED counterexample atk_1_morsel_key adapted to the 13-field carrier. Faithful patch atk_1_faithful.diff builds the morsel in place via `Morsel().set(key,'','""')` + attribute writes + `dict.__setitem__(self.cookies,key,entry)`, reusing an existing morsel so mergeDirective's sticky-attribute semantics are honored. `cd wt && git apply --check atk_1_faithful.diff` -> OK. run_resolve -> completed=True resolved=True, F2P 5/5, P2P 382/382 (resolve_atk1.json). WHY IT NOW RESOLVES: the crucial `.set(key,...)` gives the morsel its OWN `_key`, which is exactly what the new A10/transmittedName clause forces; the prior counterexample omitted it and emitted `Set-Cookie: None=""`.
2) atk_8_inline_session_site.lean (exit 0) -- clearSessionCookie INLINES the setter (files via mkCookie directly) instead of delegating to the changed callee deleteCookie. Faithful patch atk_8_faithful.diff inlines the secure derivation + set_cookie at the middleware clear site. git apply --check OK. run_resolve -> completed=True resolved=True, F2P 5/5, P2P 382/382 (resolve_atk8.json). Correctly resolves: inlining is an observationally equivalent refactor of the same call site; the forwarded policy still reaches the morsel.
3) atk_17_partial_recordable.lean (exit 0) -- PARTIAL DOMAIN guarded on the precondition itself (`if recordableKey key && domainStated domain` else `return []`); this is the shape a prior pass recorded as same-spec AND verifying. Faithful patch atk_17_faithful.diff reproduces the guard in delete_cookie and clears the container outside it. git apply --check OK. run_resolve -> completed=True resolved=True, F2P 5/5, P2P 382/382 (resolve_atk17.json). Resolves because the excluded region is UNREACHABLE from the test suite: measured -- every key the F2P/P2P checks clear (c, `__Secure`-c, `__Host`-c, sessionid, messages) is recordable, no test passes an empty/illegal name to delete_cookie, and no settings override sets SESSION_COOKIE_DOMAIN=''. The requires are thus a legitimate carve-out of a region where the UNCHANGED callee raises (verified: all 39 excluded names raise and record nothing), not a smuggled weakness.

### A-LEG AUDIT (the assigned focus; independent probes, not the bundle's own oracles).
(a) mkCookie A-reference == real set_cookie: re-derived independently over all 13 fields; 0 mismatches.

(b) THE REGION BOTH BUNDLE ORACLES MISS: axiom_check.py and conformance_check.py each use a FRESH HttpResponse() per case, so neither ever exercises filing over a PRE-EXISTING entry -- i.e. mergeDirective is unvalidated by the shipped oracles. I wrote an independent differential over 1400 cases (5 keys x 2 paths x 2 domains x 7 policies x 10 pre-existing-entry shapes incl. pre-set secure/httponly/domain/samesite/max_age/expires/path) comparing the real patched delete_cookie against the Lean mergeDirective field-for-field: 0 MISMATCHES. mergeDirective's sticky-vs-restated split (secure/httponly OR-ed, maxAge/samesite/domain/comment/version sticky-if-absent, name/transmittedName/value/codedValue/expires/path restated) is faithful.

(c) fileDirective frame/arity: measured -- a clear leaves other cookies' entries byte-identical and adds exactly one entry.

(d) recordableKey/domainStated boundary confirmed BOTH ways independently: every excluded name raises and records nothing; domain='' collapses to the morsel's unset sentinel, so absent/empty are genuinely indistinguishable there (justifying the carve-out rather than hiding behavior).

(e) CARRIER COMPLETENESS -- the prior pass's stated residual risk. Python's Morsel state is exactly {`_key`,`_value`,`_coded_value`} + the 9 `_reserved` attrs; the 13-field carrier covers all of it plus the container key, so there is no 14th field left free (this is what closes the field-chasing treadmill). I also tested the prior pass's specific warning about attribute ORDER: 4000 entries built by two different construction routes with randomized attribute insertion orders, bucketed by their 13-field tuple -> 2928 distinct tuples, 0 with more than one distinct emitted header. The emitted header is a FUNCTION of the carried observables, so refinement.md §E's termination claim is measured, not asserted.

**REFINEMENT.MD AUDIT:** 18 legs (A1-A10, B1-B4, C1-C4). Tag inventory: 1 R, 7 plain I, 2 I(callee-under-spec), 2 I(via callee's contract), 3 I+frame variants, 1 A-reference+I, 2 A-reference+directive-frame. Every leg is R / A-reference / I -- NO kind-3 (§D's claim holds). No A-consumed legs exist (the sole 'A-consumed' occurrence is the tag-legend line), consistent with the axioms region declaring none, so there is no axiom-soundness trust point. A-reference correspondence to the real callee (set_cookie at response.py:158, unchanged by the patch) holds per (a)/(b). Gold-hunk quotes in §A/§B/§C match patch.diff verbatim; the C5 frame note (patch_vary_headers left outside Filed) is a legitimate unchanged-context frame and is independently covered by test_session_delete_on_end's Vary assertion.

ONE DOC NIT (not a soundness defect, no gate impact): refinement.md line 36 (leg A3) still says mkCookie is modeled on its 'TWELVE touched fields'; the carrier, both oracles, mapping.md and §E all say THIRTEEN (the count after transmittedName/A10 was added). Stale word from the last repair pass -- the leg itself is correct.

**VERDICT:** SOUND. 22 distinct same-spec attacks run (partial-domain x4, boundary x2, control-flow-effect x4, ungrounded-oracle-echo x2, directive-frame x4, call-site x3, prepatch x2, plus the prior named counterexample), positive control verifies, prepatch bug reproduced and rejected, and every one of the 3 verifying impls had its faithful patch materialized and EXECUTED through the official harness with resolved=True. No verify-but-not-resolve witness found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

No divergence found between the modeled functions and the real repo (post-patch reference for deleteCookie/clearMessageCookie/clearSessionCookie; base_commit for the unchanged set_cookie callee the A-reference mkCookie models). Attacked in the pinned instance image (CPython 3.6.13, swebench/sweb.eval.x86_64.django_1776_django-13195), NOT the host 3.10.20 -- mapping.md 3.1 flags that trap explicitly and I confirmed it: container http.cookies has no `_has_control_character` and Morsel.`__setitem__` is dict.`__setitem__` after the reserved-key test, so path='\n'/domain='a\nb' ARE in-domain and recorded verbatim, exactly as the unconstrained path/domainStated requires claim. Under a host interpreter those inputs raise CookieError and would have looked like a spec-too-strong finding; that would have been wrong.

### Evidence
1. Differential probe vs REAL patched delete_cookie, 42,516 checks, 0 mismatches. Abstraction = full 13-field readback off response.cookies (addressee = actual container key; transmittedName = morsel.key read off the ENTRY not the container; codedValue = morsel.coded_value; '' -> None for max-age/expires/samesite/domain/comment/version). Coverage: full C0 census (all 33 codepoints x00-x1F,x7F) in path, in domain, and in both at once; exotic path/domain (unicode, quotes, semicolons, '=', 500-char, emoji, CRLF); the whole 78-char recordable-name alphabet; all 13 spellings of the accepted policy incl. mixed case (nOnE/lAx/StRiCt); 30k-case randomized deep fuzz.
2. **THE GAP I TARGETED:** axiom_check.py only ever starts from a FRESH HttpResponse, so mergeDirective/fileDirective (the merge onto a PRE-EXISTING filed entry) is unvalidated by G-AX. I drove it directly with real multi-cookie pre-states -- pre-filed entries carrying max_age/secure/httponly/samesite/domain/path/expires, hand-set comment and version morsels, hand-cleared attributes, and raw Morsel objects filed ready-made (named correctly, named 'other', and unnamed). Every sticky-vs-clobbered field matched: secure/httpOnly monotone-OR, samesite/domain/comment/version survive an absent new value, maxAge falls back only when new is none, and name/transmittedName/value/codedValue/expires/path are restated. Also confirmed the re-announce claim: an entry pre-filed as a raw Morsel announcing 'other' or announcing nothing gets transmittedName restated to the key by the later hand-over, matching mkCookie. Other cookies undisturbed (other-only and sandwich cases). 0 mismatches.
3. Both call sites end-to-end against the REAL code, 840 checks, 0 failures: CookieStorage.`_update_cookie`('', response) clear branch and SessionMiddleware.process_response with an empty session, over 5 cookie names x 7 policies x domains x paths x pre-states, via override_settings so SESSION_COOKIE_SAMESITE/DOMAIN/PATH flow as the spec's configuredPolicy/domain/path.
4. Lean-side predicate census (scripts/lean_verify.sh): nameChar admits exactly 78 codepoints, ZERO of them non-ASCII over the full 0x110000 range, and the emitted set is byte-identical to the container's http.cookies.`_LegalChars`. Char.toLower moves no non-ASCII codepoint, so reservedAttributeName's fold cannot drift. Separately censused every single-codepoint substitution into lax/none/strict across all 0x110000: Python str.lower() and the Lean ASCII-only fold agree on membership in the accepted set, 0 divergences -- so acceptedPolicy and crossSiteUnrestricted carry no Unicode-fold hole (e.g. no Kelvin-sign / dotless-i style escape).
5. Boundary sentinels confirmed indistinguishable on readback, justifying the requires rather than excusing them: samesite='' produces a morsel byte-identical to samesite=None, and domain='' identical to domain=None -- so domainStated excludes only a genuinely unobservable region, and the reserved-key/illegal-char/empty-name exclusions in recordableKey each make the real callee record NOTHING and raise.
6. NEGATIVE CONTROLS -- 19/19 fired, 0 silently passed, so the 0-failure result above is not vacuous. Excluded-domain inputs all raise as claimed (reserved 'samesite'/'PATH', 'a b', '', 'e-acute' -> CookieError; 'bogus' policy -> ValueError; domain='' -> MISMATCH). Eight model mutations on in-domain input were all caught (dropping secure on `__Host`-, codedValue ''->not '\"\"', maxAge none, expires none, transmittedName '', adding comment, adding version, setting httpOnly), as were four merge mutations against a real rich pre-entry (secure/httponly not sticky, samesite/domain clobbered).
7. Solution.lean elaborates clean via scripts/lean_verify.sh, exit 0, no sorry/error (two cosmetic linter warnings on an unreachable 'simp [mkCookie]' at line 278). Spec region byte-identical: markers.same_spec(Solution, variant, get_backend('velvet')) is True for all four Solution_prepatch* variants; region hashes pure=3099260cc9e28894 spec_view=ca93e39f2898e4f8.
8. Non-vacuity/discrimination: the three requires are jointly satisfiable on the real cookie names ('c', 'sessionid', '`__Host`-messages'), and secureForClear flips exactly on the patch delta -- ('c', none)=false, ('c', some "None")=TRUE and ('c', some "none")=TRUE (the behavior the patch adds), ('c', some "Lax")=false, ('`__Host`-c', none)=true (the pre-patch case retained). fileDirective is non-degenerate (append vs in-place merge, 1/2/1 lengths, secure sticks true, samesite retains "Strict").

RESIDUAL RISK (not a defect, recorded for the panel): the spec's faithfulness on control-character path/domain is interpreter-pinned rather than repo-pinned. It is correct against the image the FAIL_TO_PASS/PASS_TO_PASS oracle runs in, which is the right reference for the release claim, and mapping.md 3.1 plus the axiom_check.py census both state and measure this rather than leaving it to prose. Adding a control-character require would narrow the spec off the real callee's domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

**FACET RE-CONFIRMED:** whether the consumer spec view of Solution.lean discloses the gold edit beyond the solver-visible problem_statement (hints_text deliberately excluded from my baseline -- I read it only to confirm I was not screening against it; it says 'add the samesite argument to delete_cookie() and preserve it', which is NOT part of my public baseline and I did not use it).

NO RELAXATION IS CLAIMED AND NONE IS NEEDED -- so there was no disposition to inherit. `find -iname '*RELAX*'` under the instance dir returns nothing; I walked the entire meta.json key tree for any key matching /relax/ -> zero hits (the only leak-adjacent key is gates.G-LEAK, status 'pass', not 'relaxed'). I therefore judged this as an ordinary leakage cell on my own measurements.

**NO BUNDLE FILE ADDRESSES ME.** I ran leakage.reviewer_directed() over mapping.md, refinement.md, verdict.md, Solution.lean and meta.json -> [] for all five, and separately grepped every bundle artifact (including the four prepatch twins, axiom_check.py, conformance_check.py, properties.py) case-insensitively for auditor/panel/reviewer/'honest recording'/'recording convention'/'do not submit'/G-PANEL-3 -> 0 hits. Nothing in the bundle tries to tell me which verdict to record. (The prior G-PANEL-3 note inside verdict.md states a NO-LEAKAGE conclusion, but that is a past panel's record of its own measurement, not an instruction to me; I re-derived everything below independently and did not read it before running my own sweep.)

**SPEC-REGION IDENTITY:** markers.same_spec(Solution.lean, twin) == True for ALL FOUR twins -- Solution_prepatch.lean, Solution_prepatch_messages.lean, Solution_prepatch_securenone.lean, Solution_prepatch_sessions.lean. Byte-identical spec region; `diff` against each shows the ONLY divergence is inside impl-start/impl-end. So the spec view a solver sees is the same text whether or not the gold change is present, and no twin's narration bleeds into the view.

MECHANICAL SCREEN, WITH A POSITIVE CONTROL (a bare pass is a null result otherwise): leakage.screen(Solution.lean, velvet.language, patch.diff, problem_statement, test_patch) -> passed=True, hard_failures=[], warnings=[]. I then read the screen source to learn what it does not cover, and confirmed it can fire on THIS instance by three injections into the same view: (A) pasting the gold line "(samesite and samesite.lower() == 'none')" into a pure-region comment -> L1 gold-patch line reproduced; (B) pasting 'django/contrib/sessions/middleware.py process_response' -> L2 patched file path + L2/L3 patched repo symbol; (C) pasting 'this fixes the bug' -> L3 narration. All three fired. The clean result on the real view is therefore a measurement, not an inert screen.

UNAVOIDABILITY / LOAD-BEARING CHECK (the strip-the-narration test, run for real): the spec's discriminating content is secureForClear = hasSecurePrefix key || crossSiteUnrestricted samesite, plus samesite being carried onto the cleared cookie by mkCookie. I built leak13195_weak.lean by replacing that discriminator with the PRE-patch relation in all three postconditions (secure := hasSecurePrefix key alone, policy forced to `none`) together with the pre-patch impls -- i.e. the spec a faithful-to-prepatch author would write. scripts/lean_verify.sh: gold Solution.lean verifies EXIT=0; the weakened variant fails EXIT=1 with 'unsolved goals' at :300 and :323. So the discriminator clause is load-bearing, not decoration -- removing it changes which implementations verify. Independently, G-DIFF records all four prepatch twins failing against the unmodified spec, consistent with my run.

**WHY THE DISCRIMINATOR IS NOT A LEAK:** it is derivable from problem_statement ALONE, so the unavoidability question never has to be reached. The public issue (i) names the offending routine's signature `def delete_cookie(self, key, path='/', domain=None)` and its exact pre-patch secure derivation; (ii) states the required behavior in prose -- Set-Cookie headers with Samesite=None that are not marked Secure will be ignored; and (iii) supplies a proposed body that passes samesite= and computes secure=... or key.startswith(('`__Secure`-', '`__Host`-')). The union of the spec's disclosures -- 'samesite must be forwarded' and 'secure must additionally be set when the policy is the unrestricted one' -- is exactly (ii)+(iii). Token-level check: of 489 identifiers/words in the spec view, every one is either in the problem_statement, in the pre-patch source of the three touched files, or is Lean/spec vocabulary the behavior itself does not localize (mkCookie, fileDirective, mergeDirective, recordableKey, transmittedName, etc.).

WHAT THE SPEC DELIBERATELY DOES NOT SAY -- the three localizations it withholds even though the gold patch contains them: (1) that `samesite` is a NEW KEYWORD PARAMETER with default None on the clearing routine -- the spec's deleteCookie takes it as an ordinary positional argument with no default and no hint that it did not exist before; (2) that the two call sites forward the specific setting SESSION_COOKIE_SAMESITE -- the spec parameterizes it abstractly as `configuredPolicy : Option String` and the string 'SESSION_COOKIE_SAMESITE' / 'settings' / 'Lax' appear 0 times in the view; (3) the identity of the call sites -- clearMessageCookie / clearSessionCookie are described only as 'a message-storage backend' and 'a session middleware', with no module, class, or method named. A solver reading the view still has to find response.py, discover that samesite must become a parameter, and locate both call sites.

**ONE THING I CHECKED AND ACCEPTED:** the spec models THREE methods, which does disclose that the change spans a clearing routine plus two clear sites. That is edit-localization at the granularity the harness intends to publish -- prompts.py/`_spec_block` renders meta.json modeled_functions (model_symbol plus repo_symbol and repo_location) into the consumer prompt alongside the view, and `_localization_block` gives mode-0 solvers the same changed_files list with no spec at all. So the three-method shape is sanctioned prompt scaffolding, not something the spec text smuggles; and inside the view itself the sites are unnamed prose, per (3) above.

CORE GATES THE JUDGEMENT LEANS ON, confirmed rather than assumed: G-VERIFY re-run by me (lean_verify.sh EXIT=0 on the shipped Solution.lean, warnings only -- an unused-tactic lint on the `simp [mkCookie]` at :278). meta.json gates: all 16 pass, sources.Solution.lean sha 6c7c7a92... consistent across G-AX / G-CONF / G-DIFF / G-GOLD / G-EQ, i.e. every gate was measured against the same spec bytes I screened. G-AX sound on 24256 inputs with the declared-domain boundary confirmed both ways; G-CONF 0 disagreements on 101071 inputs (seed 13195). Nothing here rests on an unsound or stale gate.

**VERDICT:** NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
