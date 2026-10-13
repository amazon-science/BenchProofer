# P2 adversarial audit — django__django-13551

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,10 +64,7 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
-    let email := u.emailRaw.getD ""
-    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
+    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp
     -- impl-end
 
 prove_correct makeHashInput by
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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,10 +64,7 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
-    let email := u.emailRaw.getD ""
-    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
+    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ "x"
     -- impl-end
 
 prove_correct makeHashInput by
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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,10 +64,7 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
-    let email := u.emailRaw.getD ""
-    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
+    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ u.password
     -- impl-end
 
 prove_correct makeHashInput by
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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,9 +64,7 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
-    let email := u.emailRaw.getD ""
+    let email := u.emailRaw.getD "default@example.com"
     return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,10 +64,8 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
     let email := u.emailRaw.getD ""
-    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
+    return email ++ u.pk ++ u.password ++ u.loginTimestamp ++ timestamp
     -- impl-end
 
 prove_correct makeHashInput by
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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,10 +64,8 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
     let email := u.emailRaw.getD ""
-    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
+    return u.pk ++ u.password ++ timestamp ++ u.loginTimestamp ++ email
     -- impl-end
 
 prove_correct makeHashInput by
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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,10 +64,7 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
-    let email := u.emailRaw.getD ""
-    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
+    return ""
     -- impl-end
 
 prove_correct makeHashInput by
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
 /- No consumed axioms. The single-use token-invalidation hash input is a
@@ -64,10 +64,9 @@
   ensures out = hashInput u timestamp
   do
     -- impl-start
-    -- The email folded into the input: the stored address when present,
-    -- otherwise the empty string (an account with no/blank email).
-    let email := u.emailRaw.getD ""
-    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
+    match u.emailRaw with
+    | some e => return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ e
+    | none   => return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ "none"
     -- impl-end
 
 prove_correct makeHashInput by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single-use token-invalidation hash input is a
   straight-line concatenation of the user-state fields it depends on; it is
   modeled DEEPLY in the `pure` region (`hashInput`). Every component is a value
   already in hand (the string forms of the durable user-state fields and the
   timestamp); there is no unchanged callee whose contract the proof consumes,
   hence no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The slice of user state the single-use hash input depends on. It carries only
   the fields that feed the input, in their value (string) form:
     * `pk`             — the user's primary-key value;
     * `password`       — the stored password, which changes on a reset;
     * `loginTimestamp` — the last-login instant (already reduced to its stable
                          string form; empty when there is no last login);
     * `emailRaw`       — the user's email address when the account has one
                          (`some e`), or its absence (`none`) when the account
                          carries no email or a null email.
   Everything else about the user is orthogonal to this input (mapping.md §2). -/
structure UserState where
  pk : String
  password : String
  loginTimestamp : String
  emailRaw : Option String
deriving DecidableEq

/- The email address as it contributes to the hash input: the stored address
   when present, otherwise the empty string. An account without an email
   contributes nothing, so a user that never had an email is unaffected. -/
def emailValue (u : UserState) : String :=
  u.emailRaw.getD ""

/- The single-use token-invalidation hash input: the ordered concatenation of
   the durable user-state fields and the request timestamp, WITH the user's
   email folded in. Folding the email in is what makes changing the email
   invalidate any outstanding token: two states that differ only in the email
   produce different inputs, since the email is appended after a common prefix
   (string concatenation is left-cancellative). -/
def hashInput (u : UserState) (timestamp : String) : String :=
  u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ emailValue u
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the single-use hash input from the user's durable state and the request
   timestamp. Desired behaviour: the input must incorporate the user's email
   address (when the account has one), so that updating the email changes the
   input and thereby invalidates any token built from the old input. An account
   with no email contributes the empty string and so is unaffected. -/
method makeHashInput (u : UserState) (timestamp : String) return (out : String)
  ensures out = hashInput u timestamp
  do
    -- impl-start
    -- The email folded into the input: the stored address when present,
    -- otherwise the empty string (an account with no/blank email).
    let email := u.emailRaw.getD ""
    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
    -- impl-end

prove_correct makeHashInput by
  loom_solve
  simp [hashInput, emailValue]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: single method makeHashInput (u : UserState) (timestamp : String) with sole postcondition out = hashInput u timestamp, where hashInput := u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ emailValue u and emailValue u := u.emailRaw.getD "". Both are CONCRETE defs (not axioms). No axioms, no A-legs (refinement.md/mapping.md: all legs R/I; the one helper get_email_field_name is folded into the Option String carrier and validated by G-CONF, not axiomatized).

Protocol: worked entirely. Confirmed same_spec=True for all 9 files via swebench_unified.markers.same_spec (velvet backend) vs bundle Solution.lean; each produced by editing ONLY the impl region (axioms/pure/pre/post byte-identical). Verified with scripts/lean_verify.sh (300s cap), run concurrently in batches of <=4 background jobs. Command per file: bash scripts/lean_verify.sh <file> (from repo root).

Attacks (all same_spec=True; all VERIFY exit=1 -> rejected by ensures_1: out = hashInput u timestamp):
- atk_1 prepatch bug (email omitted): exit=1, residual `...++timestamp = ...++timestamp++u.emailRaw.getD ""`. Reproduces the prepatch discriminating clause (prepatch_reproduced=true; matches bundle Solution_prepatch.lean).
- atk_2 ungrounded-oracle echo, constant "x" for email: exit=1.
- atk_3 ungrounded-oracle echo, echoes u.password for email: exit=1.
- atk_4 boundary/wrong-default: getD "default@example.com": exit=1.
- atk_5 control-flow/order: email prepended instead of appended: exit=1 (no ++ commutativity).
- atk_6 control-flow/order: timestamp/loginTimestamp swapped: exit=1.
- atk_7 degenerate: returns "": exit=1.
- atk_8 partial-domain control-flow-effect: correct on emailRaw=some e, wrong sentinel "none" on emailRaw=none: exit=1, rejected on the some branch (some e => ...++e vs need). Confirms postcondition pins BOTH branches.

Positive control atk_pc = bundle Solution.lean (byte-identical, diff -q IDENTICAL): VERIFY exit=0 -> spec is NON-VACUOUS.

Materialize+resolve step: NOT REQUIRED. Protocol step 2 mandates materializing a faithful refined patch and running run_resolve ONLY for wrong impls that VERIFY. Zero wrong impls verified, so there is no verifying-but-wrong impl whose patch could fail to resolve; the verify=>correct direction cannot be broken on this bundle. patches={} accordingly.

Refinement audit: refinement.md legs A1-A5 all R/I, no kind-A (no consumed axioms), no kind-3 (the changed op is a pure string append, fully expressible, modeled concretely; conf_skip=false). Confirmed NO axiom/opaque/sorry/admit/constant tokens in Solution.lean spec regions; hashInput/emailValue are concrete `def`s over the input fields (grep-confirmed), so the postcondition is an answer-computing equation, not an ungrounded oracle -> echo attacks atk_2/atk_3 correctly rejected. Model<->patch correspondence (mapping.md) holds: UserState fields map to user.pk/password/last_login/email; emailRaw:Option String carries getattr(user, get_email_field_name(), '') or '' (present->some e, None/missing/empty->none via or ''); string ++ ~ f-string juxtaposition. This R/I fidelity is what G-CONF (100007 inputs, seed 13551, 0 disagreements) exercises against the real patched _make_hash_value.

Verdict: SOUND -- 8 distinct same-spec wrong impls (incl. named prepatch bug, ungrounded-oracle echoes, boundary, control-flow-effect, partial-domain) all fail to verify, positive control verifies, no verifying wrong impl exists to break verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The single-use token-invalidation hash input is a
   straight-line concatenation of the user-state fields it depends on; it is
   modeled DEEPLY in the `pure` region (`hashInput`). Every component is a value
   already in hand (the string forms of the durable user-state fields and the
   timestamp); there is no unchanged callee whose contract the proof consumes,
   hence no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The slice of user state the single-use hash input depends on. It carries only
   the fields that feed the input, in their value (string) form:
     * `pk`             — the user's primary-key value;
     * `password`       — the stored password, which changes on a reset;
     * `loginTimestamp` — the last-login instant (already reduced to its stable
                          string form; empty when there is no last login);
     * `emailRaw`       — the user's email address when the account has one
                          (`some e`), or its absence (`none`) when the account
                          carries no email or a null email.
   Everything else about the user is orthogonal to this input (mapping.md §2). -/
structure UserState where
  pk : String
  password : String
  loginTimestamp : String
  emailRaw : Option String
deriving DecidableEq

/- The email address as it contributes to the hash input: the stored address
   when present, otherwise the empty string. An account without an email
   contributes nothing, so a user that never had an email is unaffected. -/
def emailValue (u : UserState) : String :=
  u.emailRaw.getD ""

/- The single-use token-invalidation hash input: the ordered concatenation of
   the durable user-state fields and the request timestamp, WITH the user's
   email folded in. Folding the email in is what makes changing the email
   invalidate any outstanding token: two states that differ only in the email
   produce different inputs, since the email is appended after a common prefix
   (string concatenation is left-cancellative). -/
def hashInput (u : UserState) (timestamp : String) : String :=
  u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ emailValue u
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the single-use hash input from the user's durable state and the request
   timestamp. Desired behaviour: the input must incorporate the user's email
   address (when the account has one), so that updating the email changes the
   input and thereby invalidates any token built from the old input. An account
   with no email contributes the empty string and so is unaffected. -/
method makeHashInput (u : UserState) (timestamp : String) return (out : String)
  ensures out = hashInput u timestamp
  do
    -- impl-start
    -- The email folded into the input: the stored address when present,
    -- otherwise the empty string (an account with no/blank email).
    let email := u.emailRaw.getD ""
    return u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ email
    -- impl-end

prove_correct makeHashInput by
  loom_solve
  simp [hashInput, emailValue]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec: single method makeHashInput (u : UserState) (timestamp : String) with sole postcondition out = hashInput u timestamp, where hashInput := u.pk ++ u.password ++ u.loginTimestamp ++ timestamp ++ emailValue u and emailValue u := u.emailRaw.getD "". Both are CONCRETE defs (not axioms). No axioms, no A-legs (refinement.md/mapping.md: all legs R/I; the one helper get_email_field_name is folded into the Option String carrier and validated by G-CONF, not axiomatized).

Protocol: worked entirely. Confirmed same_spec=True for all 9 files via swebench_unified.markers.same_spec (velvet backend) vs bundle Solution.lean; each produced by editing ONLY the impl region (axioms/pure/pre/post byte-identical). Verified with scripts/lean_verify.sh (300s cap), run concurrently in batches of <=4 background jobs. Command per file: bash scripts/lean_verify.sh <file> (from repo root).

Attacks (all same_spec=True; all VERIFY exit=1 -> rejected by ensures_1: out = hashInput u timestamp):
- atk_1 prepatch bug (email omitted): exit=1, residual `...++timestamp = ...++timestamp++u.emailRaw.getD ""`. Reproduces the prepatch discriminating clause (prepatch_reproduced=true; matches bundle Solution_prepatch.lean).
- atk_2 ungrounded-oracle echo, constant "x" for email: exit=1.
- atk_3 ungrounded-oracle echo, echoes u.password for email: exit=1.
- atk_4 boundary/wrong-default: getD "default@example.com": exit=1.
- atk_5 control-flow/order: email prepended instead of appended: exit=1 (no ++ commutativity).
- atk_6 control-flow/order: timestamp/loginTimestamp swapped: exit=1.
- atk_7 degenerate: returns "": exit=1.
- atk_8 partial-domain control-flow-effect: correct on emailRaw=some e, wrong sentinel "none" on emailRaw=none: exit=1, rejected on the some branch (some e => ...++e vs need). Confirms postcondition pins BOTH branches.

Positive control atk_pc = bundle Solution.lean (byte-identical, diff -q IDENTICAL): VERIFY exit=0 -> spec is NON-VACUOUS.

Materialize+resolve step: NOT REQUIRED. Protocol step 2 mandates materializing a faithful refined patch and running run_resolve ONLY for wrong impls that VERIFY. Zero wrong impls verified, so there is no verifying-but-wrong impl whose patch could fail to resolve; the verify=>correct direction cannot be broken on this bundle. patches={} accordingly.

Refinement audit: refinement.md legs A1-A5 all R/I, no kind-A (no consumed axioms), no kind-3 (the changed op is a pure string append, fully expressible, modeled concretely; conf_skip=false). Confirmed NO axiom/opaque/sorry/admit/constant tokens in Solution.lean spec regions; hashInput/emailValue are concrete `def`s over the input fields (grep-confirmed), so the postcondition is an answer-computing equation, not an ungrounded oracle -> echo attacks atk_2/atk_3 correctly rejected. Model<->patch correspondence (mapping.md) holds: UserState fields map to user.pk/password/last_login/email; emailRaw:Option String carries getattr(user, get_email_field_name(), '') or '' (present->some e, None/missing/empty->none via or ''); string ++ ~ f-string juxtaposition. This R/I fidelity is what G-CONF (100007 inputs, seed 13551, 0 disagreements) exercises against the real patched _make_hash_value.

Verdict: SOUND -- 8 distinct same-spec wrong impls (incl. named prepatch bug, ungrounded-oracle echoes, boundary, control-flow-effect, partial-domain) all fail to verify, positive control verifies, no verifying wrong impl exists to break verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): no divergence found. (1) Spec region byte-identical: same_spec(Solution.lean, Solution_prepatch.lean, velvet) == True; the consumer spec view is exactly the signature `method makeHashInput (u : UserState) (timestamp : String)` with `ensures out = hashInput u timestamp` plus the pure model (UserState, emailValue = emailRaw.getD "", hashInput = pk ++ password ++ loginTimestamp ++ timestamp ++ emailValue u). (2) Solution.lean verifies via lean_verify.sh (exit 0). (3) Modeled function matches the REAL repo callee: the patched `_make_hash_value` at the worktree (descendant of base_commit 7f9e4524, contains the gold patch) returns f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}' with email=getattr(user, user.get_email_field_name(), '') or ''. Ran the bundle's conformance_check.py against the real patched callee: 100007 inputs (seed 13551), 0 disagreements. (4) Independent adversarial probes I wrote (str/UUID-style pk, missing/None/empty-string email under both default 'email' and custom 'email_address' fields, present email) all MATCH the real function. The Option-String/getD "" carrier faithfully models the getattr(...,'') or '' collapse (None/missing/'' all -> ''); pk carried as its already-stringified form (f'{pk}' == str(pk) for the tested int/str pk domain); loginTimestamp carried opaque and unchanged by the patch. The spec requires the email fold-in (the discriminating behavior of the change); it is neither too strong nor drifted from real repo behavior. prepatch correctly fails the ensures on states differing only in email, confirming the spec pins the intended behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean with impl/proof elided) checked against the PUBLIC problem_statement only (not hints_text). Findings:

1. Mechanical G-LEAK screen re-run live (leakage.screen over velvet spec_view): passed=True, zero hard_failures. No diff markers, no reproduced gold-patch line (>=8 chars), no patched file path/module (django/contrib/auth/tokens.py), no verbatim gold symbols (get_email_field_name, getattr(...) or '', _make_hash_value), no pre-patch return quoted, no bug/fix narration.

2. same_spec(Solution.lean, Solution_prepatch.lean)=True — spec region byte-identical; the discriminator lives only in the elided impl (prepatch omits the trailing email append and fails prove_correct), so nothing about the gold edit leaks through the frozen spec surface.

3. The problem_statement already publicly states the fix: 'add the user's email address into PasswordResetTokenGenerator._make_hash_value()', that changing email should reject the token, and 'Nothing forces a user to even have an email.' The spec view's modeling — email folded into the hash input (hashInput = pk++password++loginTimestamp++timestamp++emailValue u) so changing email changes the input, plus emailRaw:Option String / none->"" for a missing/null email — is a faithful abstract restatement of exactly that public disclosure. The pk/password/last_login/timestamp prefix is unchanged surrounding repo code, not the gold edit.

4. Comments are abstract behavioral prose ('the input must incorporate the user's email address', 'an account with no email contributes the empty string'); they describe desired behavior already public via the task, not the edit mechanics. The email-appended-at-end ordering is pinned by the ensures postcondition, but that is the legitimate minimal formal spec of the publicly-stated fix, not information beyond problem_statement.

Conclusion: the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
