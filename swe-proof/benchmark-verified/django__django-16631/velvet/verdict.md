# P2 adversarial audit — django__django-16631

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
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swap.lean`, `atk_order.lean`, `atk_keptflip.lean`, `atk_nonekept.lean`, `atk_alwaysvalid.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no faithful, same-spec, verifying wrong implementation exists whose refined patch fails to resolve. The spec's postcondition (`out = verifyDecision storedCred currentCred priorCreds`) is a total, exact functional contract; all 6 behaviourally-wrong impls fail verification, and the only faithful verifying impl (echo) refines to the gold patch, which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The credential tokens this decision compares are
@@ -101,16 +101,14 @@
   ensures out = verifyDecision storedCred currentCred priorCreds
   do
     -- impl-start
+
     match storedCred with
     | none   => return { principalKept := false, action := SessionAction.reject }
     | some h =>
       if h = currentCred then
         return { principalKept := true, action := SessionAction.valid }
       else
-        if priorCreds.contains h then
-          return { principalKept := true, action := SessionAction.acceptedPrior }
-        else
-          return { principalKept := false, action := SessionAction.reject }
+        return { principalKept := false, action := SessionAction.reject }
     -- impl-end
 
 prove_correct resolveSessionPrincipal by
```

Attack 2 — `atk_swap.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The credential tokens this decision compares are
@@ -101,14 +101,15 @@
   ensures out = verifyDecision storedCred currentCred priorCreds
   do
     -- impl-start
+
     match storedCred with
     | none   => return { principalKept := false, action := SessionAction.reject }
     | some h =>
       if h = currentCred then
-        return { principalKept := true, action := SessionAction.valid }
+        return { principalKept := true, action := SessionAction.acceptedPrior }
       else
         if priorCreds.contains h then
-          return { principalKept := true, action := SessionAction.acceptedPrior }
+          return { principalKept := true, action := SessionAction.valid }
         else
           return { principalKept := false, action := SessionAction.reject }
     -- impl-end
```

Attack 3 — `atk_order.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The credential tokens this decision compares are
@@ -101,16 +101,16 @@
   ensures out = verifyDecision storedCred currentCred priorCreds
   do
     -- impl-start
+
     match storedCred with
     | none   => return { principalKept := false, action := SessionAction.reject }
     | some h =>
-      if h = currentCred then
+      if priorCreds.contains h then
+        return { principalKept := true, action := SessionAction.acceptedPrior }
+      else if h = currentCred then
         return { principalKept := true, action := SessionAction.valid }
       else
-        if priorCreds.contains h then
-          return { principalKept := true, action := SessionAction.acceptedPrior }
-        else
-          return { principalKept := false, action := SessionAction.reject }
+        return { principalKept := false, action := SessionAction.reject }
     -- impl-end
 
 prove_correct resolveSessionPrincipal by
```

Attack 4 — `atk_keptflip.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The credential tokens this decision compares are
@@ -101,6 +101,7 @@
   ensures out = verifyDecision storedCred currentCred priorCreds
   do
     -- impl-start
+
     match storedCred with
     | none   => return { principalKept := false, action := SessionAction.reject }
     | some h =>
@@ -108,7 +109,7 @@
         return { principalKept := true, action := SessionAction.valid }
       else
         if priorCreds.contains h then
-          return { principalKept := true, action := SessionAction.acceptedPrior }
+          return { principalKept := false, action := SessionAction.acceptedPrior }
         else
           return { principalKept := false, action := SessionAction.reject }
     -- impl-end
```

Attack 5 — `atk_nonekept.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The credential tokens this decision compares are
@@ -101,8 +101,9 @@
   ensures out = verifyDecision storedCred currentCred priorCreds
   do
     -- impl-start
+
     match storedCred with
-    | none   => return { principalKept := false, action := SessionAction.reject }
+    | none   => return { principalKept := true, action := SessionAction.reject }
     | some h =>
       if h = currentCred then
         return { principalKept := true, action := SessionAction.valid }
```

Attack 6 — `atk_alwaysvalid.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The credential tokens this decision compares are
@@ -101,16 +101,8 @@
   ensures out = verifyDecision storedCred currentCred priorCreds
   do
     -- impl-start
-    match storedCred with
-    | none   => return { principalKept := false, action := SessionAction.reject }
-    | some h =>
-      if h = currentCred then
-        return { principalKept := true, action := SessionAction.valid }
-      else
-        if priorCreds.contains h then
-          return { principalKept := true, action := SessionAction.acceptedPrior }
-        else
-          return { principalKept := false, action := SessionAction.reject }
+
+    return { principalKept := true, action := SessionAction.valid }
     -- impl-end
 
 prove_correct resolveSessionPrincipal by
```

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The credential tokens this decision compares are
@@ -101,16 +101,16 @@
   ensures out = verifyDecision storedCred currentCred priorCreds
   do
     -- impl-start
+
     match storedCred with
     | none   => return { principalKept := false, action := SessionAction.reject }
     | some h =>
       if h = currentCred then
         return { principalKept := true, action := SessionAction.valid }
+      else if priorCreds.contains h then
+        return { principalKept := true, action := SessionAction.acceptedPrior }
       else
-        if priorCreds.contains h then
-          return { principalKept := true, action := SessionAction.acceptedPrior }
-        else
-          return { principalKept := false, action := SessionAction.reject }
+        return { principalKept := false, action := SessionAction.reject }
     -- impl-end
 
 prove_correct resolveSessionPrincipal by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The credential tokens this decision compares are
--  produced by UNCHANGED machinery and are observed ONLY by equality; they enter
--  as the free inputs `currentCred` / `priorCreds`. The decision makes no
--  behavioural claim about how a token is computed and holds for EVERY value the
--  tokens could take, so there is nothing to check against a real callee — hence
--  no G-AX. The behaviour under spec — the acceptance policy — is modeled deeply
--  in the `pure`/`impl` regions, no outside contract consumed. See mapping.md §3
--  / refinement.md.)
-- axioms-end

-- pure-start
/- A credential token, identified abstractly: the policy observes only whether
   two tokens are EQUAL (a constant-time comparison), never a token's content,
   so a single opaque carrier with decidable equality suffices. -/
abbrev Cred := Nat

/- How the retained credential was classified by the decision:
   * `valid`         — it matches the principal's credential under the current
                       secret;
   * `acceptedPrior` — it does not match the current-secret credential but
                       matches one produced under a previously-valid secret;
   * `reject`        — it is absent or matches no known credential. -/
inductive SessionAction where
  | valid
  | acceptedPrior
  | reject
deriving DecidableEq, Inhabited, Repr

/- The two observables of the decision:
   * `principalKept` — whether the located principal survives (`true`) or is
                       dropped in favour of an anonymous one (`false`);
   * `action`        — how the retained credential was classified. -/
structure SessionVerify where
  principalKept : Bool
  action        : SessionAction
deriving DecidableEq, Inhabited, Repr

/- The desired acceptance policy for a located principal's session.

   `storedCred` is the credential retained on the session (absent ↔ `none`),
   `currentCred` is the principal's credential under the current secret, and
   `priorCreds` are its credentials under the previously-valid secrets.

   * If no credential is retained, the session cannot be trusted: drop the
     principal (`reject`).
   * If the retained credential matches the one under the current secret, accept
     the session (`valid`).
   * Otherwise, if the retained credential matches one produced under a prior
     secret, the session is still the principal's — it was merely established
     before a secret change. Keep the principal, accepting the credential under
     that prior secret (`acceptedPrior`).
   * Otherwise the credential is unrecognised: drop the principal (`reject`). -/
def verifyDecision (storedCred : Option Cred) (currentCred : Cred)
    (priorCreds : List Cred) : SessionVerify :=
  match storedCred with
  | none   => { principalKept := false, action := SessionAction.reject }
  | some h =>
    if h = currentCred then
      { principalKept := true, action := SessionAction.valid }
    else if priorCreds.contains h then
      { principalKept := true, action := SessionAction.acceptedPrior }
    else
      { principalKept := false, action := SessionAction.reject }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the fate of a located principal's session.

   It is handed the credential retained on the session (`storedCred`: a present
   token `some h`, or `none` when nothing is retained), the principal's
   credential under the current secret (`currentCred`), and — as a read-only free
   input — the principal's credentials under the previously-valid secrets
   (`priorCreds`, possibly empty). All three are derived by UNCHANGED machinery
   and are observed only by equality; the decision claims nothing about how a
   token is computed.

   It returns a `SessionVerify` recording whether the principal is kept and how
   the retained credential was classified. The desired behaviour is
   `verifyDecision`: accept a session whose retained credential matches the
   current secret (`valid`); keep the principal for one that matches only a
   prior secret (`acceptedPrior`); otherwise drop the principal (`reject`).

   `storedCred`, `currentCred`, `priorCreds` are all read-only (none `mut`): the
   routine reads them and builds a fresh outcome, mutating nothing it is handed
   (directive 5). -/
method resolveSessionPrincipal (storedCred : Option Cred) (currentCred : Cred) (priorCreds : List Cred) return (out : SessionVerify)
  ensures out = verifyDecision storedCred currentCred priorCreds
  do
    -- impl-start
    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if priorCreds.contains h then
          return { principalKept := true, action := SessionAction.acceptedPrior }
        else
          return { principalKept := false, action := SessionAction.reject }
    -- impl-end

prove_correct resolveSessionPrincipal by
  loom_solve <;> simp_all [verifyDecision]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: velvet method resolveSessionPrincipal, ensures out = verifyDecision storedCred currentCred priorCreds — a TOTAL EXACT postcondition pinning SessionVerify (principalKept, action) for EVERY input (Option Cred x Cred x List Cred). No axioms, no A-reference deep models; refinement.md legs A1-A4 all tagged I. A-leg attack surface therefore reduces to model<->patch correspondence + echo.

SAME-SPEC: all 7 submitted attacks + positive control return same_spec==True (verified with swebench_unified.markers.same_spec / get_backend('velvet'), python; only impl region edited).

VERIFY (bash scripts/lean_verify.sh <f>, run concurrently <=4/batch): atk_prepatch exit=1 (rejected on exactly `i not-in priorCreds` — the reported bug), atk_swap exit=1, atk_order exit=1, atk_keptflip exit=1, atk_nonekept exit=1 (boundary), atk_alwaysvalid exit=1 (partial-domain/ungrounded echo). All 6 behaviourally-wrong impls REJECTED. atk_echo exit=0 (correct, reformatted else-if). pos_control exit=0 (non-vacuous). Distinct classes covered: prepatch, action-swap, case-order, control-flow-effect (kept flip), boundary (none-kept), constant/ungrounded-echo.

MANDATORY RESOLVE (swebench_unified.harness.run_resolve, SBU_BENCHMARK=swe_bench_verified, timeout=1800): atk_echo is the only FAITHFUL verifying attack; its faithful refined patch (each classification attached to its fixed effect glue per mapping.md 2a: valid->no-op, acceptedPrior->cycle_key()+refresh HASH_SESSION_KEY to current-secret token, reject->flush()+user=None) is byte-identical to benchmark-verified/django__django-16631/patch.diff (gold). OBSERVED: RESOLVE_RESULT {resolved:true, completed:true, note:'resolved', attempts:1}. So the only faithful verifying impl resolves — not a weakness.

DIVERGENCE PROBE (investigated, NOT submitted as a counterexample): atk_diverge and atk_diverge_inv (a `while true` inserted before the classification) both VERIFY (exit=0) — the standard partial-correctness vacuity: a non-terminating do-block never reaches the postcondition, so `ensures` is vacuously satisfied. I materialized a literal transliteration atk_diverge_faithful.patch (gold + injected `while True: pass` in the `if not session_hash_verified` branch; applies cleanly at base_commit) and RAN it: RESOLVE_RESULT {resolved:false, completed:false, note:'no report ... harness error or image pull failure'} (the F2P test hangs until the run errors out at ~34min). I deliberately did NOT submit these as counterexamples for two rigorous reasons:

(1) FAITHFULNESS — the gold get_user block and the modeled do-block are entirely STRAIGHT-LINE (match + nested if; any() over the FINITE SECRET_KEY_FALLBACKS list <-> priorCreds.contains). No loop exists anywhere in the fix, so a `while true` has NO counterpart in patch.diff; its 'refined patch' is a fabricated hang, not a faithful refinement of the modeled op (spec_guide directive 3: the do-block must be a faithful SKELETON whose control flow mirrors patch.diff).

(2) FRAMEWORK SCOPE — `partial` correctness is the deliberately-accepted, corpus-universal setting (401/500 velvet Solution.lean use termination=partial; gates/hygiene.py only requires SOME termination set_option, partial OR total; nagini abolishes termination proofs entirely). A diverging impl vacuously satisfies ANY partial postcondition, so this breaks every partial bundle identically — a property of the accepted semantics, not a weakness specific to THIS spec/refinement; no gate in the framework tests termination. verify=>correct here is Hoare PARTIAL correctness of a terminating faithful skeleton, which the gold trivially is. Submitting an unfaithful non-resolving patch would force a spurious BROKEN through the runner's faithfulness-blind resolve step (build_one.py _derive_audit_verdict runs the submitted patch with no check that it is a faithful refinement).

REFINEMENT AUDIT (refinement.md): no axioms (axioms region empty; 0 axiom keywords), no A-consumed, no A-reference deep models, no kind-3. All four legs tagged I and each corroborated against the actual gold patch text: A1 storedCred=none <-> `if not session_hash` (Python falsy) + short-circuited `session_hash and any(...)` -> flush()/user=None (reject); A2 h=currentCred <-> constant_time_compare(session_hash, get_session_auth_hash()) True -> block skipped/user kept (valid); A3 priorCreds.contains h <-> any(constant_time_compare(session_hash, fb) for fb in get_session_auth_fallback_hash()) True -> cycle_key()+HASH_SESSION_KEY=session_auth_hash/user kept (acceptedPrior); A4 else -> flush()/user=None (reject). Bijections in mapping.md 2 hold. The single changed op (prior-secret acceptance, A3) is modeled deeply, not axiomatized.

CONCLUSION: verify=>correct holds. 6 distinct behaviourally-wrong impls all FAIL verify; the only faithful verifying impl (echo) resolves. No faithful verifying wrong impl's refined patch fails to resolve. SOUND. Evidence: {v_*.log, resolve_echo.log, resolve_diverge.log, atk_*.lean, atk_echo_faithful.patch, atk_diverge_faithful.patch, FINDINGS.md}.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_swap.lean`, `atk_order.lean`, `atk_keptflip.lean`, `atk_nonekept.lean`, `atk_alwaysvalid.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no faithful, same-spec, verifying wrong implementation exists whose refined patch fails to resolve. The spec's postcondition (`out = verifyDecision storedCred currentCred priorCreds`) is a total, exact functional contract; all 6 behaviourally-wrong impls fail verification, and the only faithful verifying impl (echo) refines to the gold patch, which resolves.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_swap.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_order.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_keptflip.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_nonekept.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_alwaysvalid.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The credential tokens this decision compares are
--  produced by UNCHANGED machinery and are observed ONLY by equality; they enter
--  as the free inputs `currentCred` / `priorCreds`. The decision makes no
--  behavioural claim about how a token is computed and holds for EVERY value the
--  tokens could take, so there is nothing to check against a real callee — hence
--  no G-AX. The behaviour under spec — the acceptance policy — is modeled deeply
--  in the `pure`/`impl` regions, no outside contract consumed. See mapping.md §3
--  / refinement.md.)
-- axioms-end

-- pure-start
/- A credential token, identified abstractly: the policy observes only whether
   two tokens are EQUAL (a constant-time comparison), never a token's content,
   so a single opaque carrier with decidable equality suffices. -/
abbrev Cred := Nat

/- How the retained credential was classified by the decision:
   * `valid`         — it matches the principal's credential under the current
                       secret;
   * `acceptedPrior` — it does not match the current-secret credential but
                       matches one produced under a previously-valid secret;
   * `reject`        — it is absent or matches no known credential. -/
inductive SessionAction where
  | valid
  | acceptedPrior
  | reject
deriving DecidableEq, Inhabited, Repr

/- The two observables of the decision:
   * `principalKept` — whether the located principal survives (`true`) or is
                       dropped in favour of an anonymous one (`false`);
   * `action`        — how the retained credential was classified. -/
structure SessionVerify where
  principalKept : Bool
  action        : SessionAction
deriving DecidableEq, Inhabited, Repr

/- The desired acceptance policy for a located principal's session.

   `storedCred` is the credential retained on the session (absent ↔ `none`),
   `currentCred` is the principal's credential under the current secret, and
   `priorCreds` are its credentials under the previously-valid secrets.

   * If no credential is retained, the session cannot be trusted: drop the
     principal (`reject`).
   * If the retained credential matches the one under the current secret, accept
     the session (`valid`).
   * Otherwise, if the retained credential matches one produced under a prior
     secret, the session is still the principal's — it was merely established
     before a secret change. Keep the principal, accepting the credential under
     that prior secret (`acceptedPrior`).
   * Otherwise the credential is unrecognised: drop the principal (`reject`). -/
def verifyDecision (storedCred : Option Cred) (currentCred : Cred)
    (priorCreds : List Cred) : SessionVerify :=
  match storedCred with
  | none   => { principalKept := false, action := SessionAction.reject }
  | some h =>
    if h = currentCred then
      { principalKept := true, action := SessionAction.valid }
    else if priorCreds.contains h then
      { principalKept := true, action := SessionAction.acceptedPrior }
    else
      { principalKept := false, action := SessionAction.reject }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the fate of a located principal's session.

   It is handed the credential retained on the session (`storedCred`: a present
   token `some h`, or `none` when nothing is retained), the principal's
   credential under the current secret (`currentCred`), and — as a read-only free
   input — the principal's credentials under the previously-valid secrets
   (`priorCreds`, possibly empty). All three are derived by UNCHANGED machinery
   and are observed only by equality; the decision claims nothing about how a
   token is computed.

   It returns a `SessionVerify` recording whether the principal is kept and how
   the retained credential was classified. The desired behaviour is
   `verifyDecision`: accept a session whose retained credential matches the
   current secret (`valid`); keep the principal for one that matches only a
   prior secret (`acceptedPrior`); otherwise drop the principal (`reject`).

   `storedCred`, `currentCred`, `priorCreds` are all read-only (none `mut`): the
   routine reads them and builds a fresh outcome, mutating nothing it is handed
   (directive 5). -/
method resolveSessionPrincipal (storedCred : Option Cred) (currentCred : Cred) (priorCreds : List Cred) return (out : SessionVerify)
  ensures out = verifyDecision storedCred currentCred priorCreds
  do
    -- impl-start
    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if priorCreds.contains h then
          return { principalKept := true, action := SessionAction.acceptedPrior }
        else
          return { principalKept := false, action := SessionAction.reject }
    -- impl-end

prove_correct resolveSessionPrincipal by
  loom_solve <;> simp_all [verifyDecision]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: velvet method resolveSessionPrincipal, ensures out = verifyDecision storedCred currentCred priorCreds — a TOTAL EXACT postcondition pinning SessionVerify (principalKept, action) for EVERY input (Option Cred x Cred x List Cred). No axioms, no A-reference deep models; refinement.md legs A1-A4 all tagged I. A-leg attack surface therefore reduces to model<->patch correspondence + echo.

SAME-SPEC: all 7 submitted attacks + positive control return same_spec==True (verified with swebench_unified.markers.same_spec / get_backend('velvet'), python; only impl region edited).

VERIFY (bash scripts/lean_verify.sh <f>, run concurrently <=4/batch): atk_prepatch exit=1 (rejected on exactly `i not-in priorCreds` — the reported bug), atk_swap exit=1, atk_order exit=1, atk_keptflip exit=1, atk_nonekept exit=1 (boundary), atk_alwaysvalid exit=1 (partial-domain/ungrounded echo). All 6 behaviourally-wrong impls REJECTED. atk_echo exit=0 (correct, reformatted else-if). pos_control exit=0 (non-vacuous). Distinct classes covered: prepatch, action-swap, case-order, control-flow-effect (kept flip), boundary (none-kept), constant/ungrounded-echo.

MANDATORY RESOLVE (swebench_unified.harness.run_resolve, SBU_BENCHMARK=swe_bench_verified, timeout=1800): atk_echo is the only FAITHFUL verifying attack; its faithful refined patch (each classification attached to its fixed effect glue per mapping.md 2a: valid->no-op, acceptedPrior->cycle_key()+refresh HASH_SESSION_KEY to current-secret token, reject->flush()+user=None) is byte-identical to benchmark-verified/django__django-16631/patch.diff (gold). OBSERVED: RESOLVE_RESULT {resolved:true, completed:true, note:'resolved', attempts:1}. So the only faithful verifying impl resolves — not a weakness.

DIVERGENCE PROBE (investigated, NOT submitted as a counterexample): atk_diverge and atk_diverge_inv (a `while true` inserted before the classification) both VERIFY (exit=0) — the standard partial-correctness vacuity: a non-terminating do-block never reaches the postcondition, so `ensures` is vacuously satisfied. I materialized a literal transliteration atk_diverge_faithful.patch (gold + injected `while True: pass` in the `if not session_hash_verified` branch; applies cleanly at base_commit) and RAN it: RESOLVE_RESULT {resolved:false, completed:false, note:'no report ... harness error or image pull failure'} (the F2P test hangs until the run errors out at ~34min). I deliberately did NOT submit these as counterexamples for two rigorous reasons:

(1) FAITHFULNESS — the gold get_user block and the modeled do-block are entirely STRAIGHT-LINE (match + nested if; any() over the FINITE SECRET_KEY_FALLBACKS list <-> priorCreds.contains). No loop exists anywhere in the fix, so a `while true` has NO counterpart in patch.diff; its 'refined patch' is a fabricated hang, not a faithful refinement of the modeled op (spec_guide directive 3: the do-block must be a faithful SKELETON whose control flow mirrors patch.diff).

(2) FRAMEWORK SCOPE — `partial` correctness is the deliberately-accepted, corpus-universal setting (401/500 velvet Solution.lean use termination=partial; gates/hygiene.py only requires SOME termination set_option, partial OR total; nagini abolishes termination proofs entirely). A diverging impl vacuously satisfies ANY partial postcondition, so this breaks every partial bundle identically — a property of the accepted semantics, not a weakness specific to THIS spec/refinement; no gate in the framework tests termination. verify=>correct here is Hoare PARTIAL correctness of a terminating faithful skeleton, which the gold trivially is. Submitting an unfaithful non-resolving patch would force a spurious BROKEN through the runner's faithfulness-blind resolve step (build_one.py _derive_audit_verdict runs the submitted patch with no check that it is a faithful refinement).

REFINEMENT AUDIT (refinement.md): no axioms (axioms region empty; 0 axiom keywords), no A-consumed, no A-reference deep models, no kind-3. All four legs tagged I and each corroborated against the actual gold patch text: A1 storedCred=none <-> `if not session_hash` (Python falsy) + short-circuited `session_hash and any(...)` -> flush()/user=None (reject); A2 h=currentCred <-> constant_time_compare(session_hash, get_session_auth_hash()) True -> block skipped/user kept (valid); A3 priorCreds.contains h <-> any(constant_time_compare(session_hash, fb) for fb in get_session_auth_fallback_hash()) True -> cycle_key()+HASH_SESSION_KEY=session_auth_hash/user kept (acceptedPrior); A4 else -> flush()/user=None (reject). Bijections in mapping.md 2 hold. The single changed op (prior-secret acceptance, A3) is modeled deeply, not axiomatized.

CONCLUSION: verify=>correct holds. 6 distinct behaviourally-wrong impls all FAIL verify; the only faithful verifying impl (echo) resolves. No faithful verifying wrong impl's refined patch fails to resolve. SOUND. Evidence: {v_*.log, resolve_echo.log, resolve_diverge.log, atk_*.lean, atk_echo_faithful.patch, atk_diverge_faithful.patch, FINDINGS.md}.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True); Solution.lean verifies clean (lean_verify exit 0). The modeled function verifyDecision(storedCred: Option Cred, currentCred: Cred, priorCreds: List Cred) is a faithful, exact model of the post-patch get_user session-verification block (django/contrib/auth/__init__.py, confirmed against the prepatch source and the gold hunk in refinement.md). Case-by-case bijection with no divergence:

1. storedCred=none (session_hash falsy): post-patch sets session_hash_verified=False, then inner `session_hash and any(...)` short-circuits False -> flush()+user=None. Model: reject, principalKept=false. MATCH.
2. some h, h=currentCred: constant_time_compare true -> `if not session_hash_verified` skipped, session untouched, user kept. Model: valid, principalKept=true. MATCH.
3. some h, h!=currentCred, h in priorCreds: verified False; session_hash truthy AND any(constant_time_compare(...)) True -> cycle_key()+store current token, user kept. Model: acceptedPrior, principalKept=true. MATCH.
4. some h, h!=currentCred, h not in priorCreds: verified False; any(...) False -> flush()+user=None. Model: reject, principalKept=false. MATCH.

The decision priority (current secret checked first, prior secrets only within the `not verified` branch) matches the spec's `if h=currentCred then valid else if priorCreds.contains h then acceptedPrior else reject`. Abstraction is sound and tight: constant_time_compare is a pure equality test on opaque HMAC tokens so refining to `=`/Nat is exact (content never observed, only equality), and any(...) over fallback tokens refines exactly to List.contains. The valid/acceptedPrior split reflects a genuine real-code observable difference (no-op vs cycle_key+rehash), so the spec is neither too strong nor drifting. No diverging input exists; the spec is faithful to the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently verified both mechanically and semantically.

MECHANICAL: leakage.screen() over spec_view(Solution.lean) passes with ZERO hard failures. same_spec(Solution.lean, Solution_prepatch.lean) == True under VelvetBackend. No diff markers, no patched file path (django/contrib/auth/__init__.py, base_user.py) or module path in the view, no gold-patch line reproduced (>=8 normalized chars), no bug/fix narration. Patch-changed distinctive symbols {get_user, get_session_auth_hash, get_session_auth_fallback_hash} do NOT appear in spec-view identifiers ({resolveSessionPrincipal, verifyDecision, Cred, SessionAction, SessionVerify, storedCred, currentCred, priorCreds, principalKept, action}) nor in comments (get_session_auth_hash is in any case public via the problem_statement, which names it verbatim). No RELAXED_LEAKAGE.md / relaxed_leakage flag — evaluated strict.

SEMANTIC (gold-reconstruction test against the PUBLIC problem_statement only, NOT hints_text): the problem_statement already discloses the whole user-facing feature — 'SECRET_KEY_FALLBACKS is not used for sessions'; rotating the key + moving the old value into SECRET_KEY_FALLBACKS logs everyone out; get_session_auth_hash/salted_hmac never pass the fallback secret. The requested fix is exactly: have prior/fallback secrets validate sessions. verifyDecision's four-way policy (none->reject; current-secret match->valid; prior-secret match->keep principal/acceptedPrior; else->reject) encodes precisely this publicly-requested behavior. Encoding the feature the public task explicitly asks for is not leakage beyond problem_statement — a spec must state the desired behavior.

DECISIVE: the NON-public component of the gold edit — the effect glue request.session.cycle_key() + request.session[HASH_SESSION_KEY] = session_auth_hash (upgrading the retained hash to the current-secret token so sessions survive fallback removal) — is exactly the subtle 'additional need' raised ONLY in hints_text, and it is absent from the spec view. The acceptedPrior branch is described abstractly ('keep the principal, accepting the credential under that prior secret'); SessionVerify exposes only principalKept + a classification tag, disclosing nothing about cycling the key or refreshing the stored token. mapping.md 2a holds that glue outside the modeled slice by design. A solver reading the spec view therefore learns nothing about the gold edit beyond what the public problem_statement already states.

Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.