# P2 adversarial audit — django__django-11451

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,25 +80,24 @@
   let mut login := name
   if login.isNone then
     login := fallback
-  match login, secret with
-  | some loginName, some pw =>
+  match login with
+  | some loginName =>
       match lookupUser loginName with
       | none =>
-          -- No principal carries this name: perform one secret-hashing operation
-          -- to keep the timing uniform, and return no principal.
-          return { user := none, queries := 1, hasherCalls := 1 }
+          return { user := none, queries := 1,
+                   hasherCalls := if secret.isSome then 1 else 0 }
       | some u =>
-          -- Checking the supplied secret performs whatever hashing the check
-          -- itself requires (once in the ordinary case, none when the stored
-          -- secret is unusable).
-          if passwordMatches u pw && userAllowed u then
-            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
-          else
-            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
-  | _, _ =>
-      -- A credential is absent: abandon the check before touching the store or
-      -- the secret hasher.
-      return { user := none, queries := 0, hasherCalls := 0 }
+          match secret with
+          | none =>
+              return { user := none, queries := 1, hasherCalls := 0 }
+          | some pw =>
+              if passwordMatches u pw && userAllowed u then
+                return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
+              else
+                return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
+  | none =>
+      return { user := none, queries := 1,
+               hasherCalls := if secret.isSome then 1 else 0 }
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,20 +84,13 @@
   | some loginName, some pw =>
       match lookupUser loginName with
       | none =>
-          -- No principal carries this name: perform one secret-hashing operation
-          -- to keep the timing uniform, and return no principal.
-          return { user := none, queries := 1, hasherCalls := 1 }
+          return { user := none, queries := 1, hasherCalls := 0 }
       | some u =>
-          -- Checking the supplied secret performs whatever hashing the check
-          -- itself requires (once in the ordinary case, none when the stored
-          -- secret is unusable).
           if passwordMatches u pw && userAllowed u then
             return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
           else
             return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
   | _, _ =>
-      -- A credential is absent: abandon the check before touching the store or
-      -- the secret hasher.
       return { user := none, queries := 0, hasherCalls := 0 }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,20 +84,10 @@
   | some loginName, some pw =>
       match lookupUser loginName with
       | none =>
-          -- No principal carries this name: perform one secret-hashing operation
-          -- to keep the timing uniform, and return no principal.
           return { user := none, queries := 1, hasherCalls := 1 }
       | some u =>
-          -- Checking the supplied secret performs whatever hashing the check
-          -- itself requires (once in the ordinary case, none when the stored
-          -- secret is unusable).
-          if passwordMatches u pw && userAllowed u then
-            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
-          else
-            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
+          return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
   | _, _ =>
-      -- A credential is absent: abandon the check before touching the store or
-      -- the secret hasher.
       return { user := none, queries := 0, hasherCalls := 0 }
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,21 +84,14 @@
   | some loginName, some pw =>
       match lookupUser loginName with
       | none =>
-          -- No principal carries this name: perform one secret-hashing operation
-          -- to keep the timing uniform, and return no principal.
           return { user := none, queries := 1, hasherCalls := 1 }
       | some u =>
-          -- Checking the supplied secret performs whatever hashing the check
-          -- itself requires (once in the ordinary case, none when the stored
-          -- secret is unusable).
           if passwordMatches u pw && userAllowed u then
             return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
           else
             return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
   | _, _ =>
-      -- A credential is absent: abandon the check before touching the store or
-      -- the secret hasher.
-      return { user := none, queries := 0, hasherCalls := 0 }
+      return { user := none, queries := 1, hasherCalls := 1 }
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,20 +84,13 @@
   | some loginName, some pw =>
       match lookupUser loginName with
       | none =>
-          -- No principal carries this name: perform one secret-hashing operation
-          -- to keep the timing uniform, and return no principal.
           return { user := none, queries := 1, hasherCalls := 1 }
       | some u =>
-          -- Checking the supplied secret performs whatever hashing the check
-          -- itself requires (once in the ordinary case, none when the stored
-          -- secret is unusable).
           if passwordMatches u pw && userAllowed u then
-            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
+            return { user := some u, queries := 1, hasherCalls := 1 }
           else
-            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
+            return { user := none, queries := 1, hasherCalls := 1 }
   | _, _ =>
-      -- A credential is absent: abandon the check before touching the store or
-      -- the secret hasher.
       return { user := none, queries := 0, hasherCalls := 0 }
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,27 +77,18 @@
 -- impl-start
 def implementation_credentialAuth
     (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
-  let mut login := name
-  if login.isNone then
-    login := fallback
+  let login := fallback
   match login, secret with
   | some loginName, some pw =>
       match lookupUser loginName with
       | none =>
-          -- No principal carries this name: perform one secret-hashing operation
-          -- to keep the timing uniform, and return no principal.
           return { user := none, queries := 1, hasherCalls := 1 }
       | some u =>
-          -- Checking the supplied secret performs whatever hashing the check
-          -- itself requires (once in the ordinary case, none when the stored
-          -- secret is unusable).
           if passwordMatches u pw && userAllowed u then
             return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
           else
             return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
   | _, _ =>
-      -- A credential is absent: abandon the check before touching the store or
-      -- the secret hasher.
       return { user := none, queries := 0, hasherCalls := 0 }
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,27 +77,18 @@
 -- impl-start
 def implementation_credentialAuth
     (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
-  let mut login := name
-  if login.isNone then
-    login := fallback
+  let login := match name with | some x => some x | none => fallback
   match login, secret with
   | some loginName, some pw =>
       match lookupUser loginName with
       | none =>
-          -- No principal carries this name: perform one secret-hashing operation
-          -- to keep the timing uniform, and return no principal.
           return { user := none, queries := 1, hasherCalls := 1 }
       | some u =>
-          -- Checking the supplied secret performs whatever hashing the check
-          -- itself requires (once in the ordinary case, none when the stored
-          -- secret is unusable).
           if passwordMatches u pw && userAllowed u then
             return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
           else
             return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
   | _, _ =>
-      -- A credential is absent: abandon the check before touching the store or
-      -- the secret hasher.
       return { user := none, queries := 0, hasherCalls := 0 }
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- An identified principal in the credential store. Only its identity is
observed by the modeled behavior. -/
structure User where
  uid : Nat
deriving Repr, DecidableEq, Inhabited

/-- The credential-store lookup, keyed by the resolved login name. Returns the
matching principal, or `none` when no principal carries that name. UNCHANGED by
the modeled behavior; the same lookup is referenced in the specification and the
implementation. -/
opaque lookupUser : List Char → Option User

/-- Whether the supplied secret matches the stored principal's secret. UNCHANGED;
referenced identically in the specification and the implementation. -/
opaque passwordMatches : User → List Char → Bool

/-- Whether the stored principal is permitted to authenticate (e.g. is active).
UNCHANGED; referenced identically in the specification and the implementation. -/
opaque userAllowed : User → Bool

/-- The number of secret-hashing operations that checking the supplied secret
against the stored principal's secret performs — an inherent cost of the check
itself, determined by the principal's stored state and the supplied secret
(e.g. zero when the stored secret is unusable, one in the ordinary case).
UNCHANGED; referenced identically in the specification and the implementation. -/
opaque checkHashCount : User → List Char → Nat
-- axioms-end

-- pure-start
/-- The outcome of a credential check: the authenticated principal (if any) plus
the two observable resource costs — the number of credential-store queries and
the number of secret-hashing operations performed. -/
structure AuthOutcome where
  user : Option User
  queries : Nat
  hasherCalls : Nat
deriving Repr, DecidableEq, Inhabited

/-- The login name actually used: the positional name when present, otherwise the
fallback name taken from the keyword argument. -/
def resolveName (name fallback : Option (List Char)) : Option (List Char) :=
  if name.isNone then fallback else name
-- pure-end

-- post-conditions-start
/-- Relates the outcome of a credential check to its inputs.

When either the resolved login name or the secret is absent, the check is
abandoned immediately: no principal is returned and neither a credential-store
query nor a secret-hashing operation is performed (both costs are zero).

When both are present, exactly one credential-store query is performed; if no
principal carries that name, exactly one secret-hashing operation is performed
(to keep the timing uniform) and no principal is returned; if a principal is
found, exactly the secret-hashing operations inherent in checking the supplied
secret against it are performed, and the principal is returned exactly when its
secret matches and it is permitted to authenticate. Every component of the
outcome is pinned to the inputs in every branch. -/
def problem_spec_credentialAuth
    (name fallback secret : Option (List Char)) (result : AuthOutcome) : Prop :=
  match resolveName name fallback, secret with
  | some login, some pw =>
      result.queries = 1 ∧
      (match lookupUser login with
       | none => result.user = none ∧ result.hasherCalls = 1
       | some u =>
           result.hasherCalls = checkHashCount u pw ∧
           result.user = (if passwordMatches u pw && userAllowed u then some u else none))
  | _, _ =>
      result.user = none ∧ result.queries = 0 ∧ result.hasherCalls = 0
-- post-conditions-end

-- impl-start
def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          -- No principal carries this name: perform one secret-hashing operation
          -- to keep the timing uniform, and return no principal.
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          -- Checking the supplied secret performs whatever hashing the check
          -- itself requires (once in the ordinary case, none when the stored
          -- secret is unusable).
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      -- A credential is absent: abandon the check before touching the store or
      -- the secret hasher.
      return { user := none, queries := 0, hasherCalls := 0 }
-- impl-end

-- proof-start
theorem correct_credentialAuth :
    ∀ (name fallback secret : Option (List Char)),
    problem_spec_credentialAuth name fallback secret
      (implementation_credentialAuth name fallback secret) := by
  intro name fallback secret
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  by_cases hn : name.isNone
  · simp only [hn, if_true]
    cases fallback with
    | none => cases secret <;> simp
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u =>
          by_cases hp : passwordMatches u pw && userAllowed u <;>
            simp [hl, hp]
  · simp only [hn]
    cases hnm : name with
    | none => simp [hnm] at hn
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u =>
          by_cases hp : passwordMatches u pw && userAllowed u <;>
            simp [hl, hp]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_credentialAuth totally pins every AuthOutcome field (user, queries, hasherCalls) in every branch as a function of inputs + the four identically-referenced opaque callees. 7 same-spec wrong impls (all same_spec=True verified via markers.same_spec) each fail lean_verify.sh with exit 1 = genuine 'unsolved goals' proof errors (NOT import/env errors), so none produces a closing clean-axiom proof; no faithful patch needed materializing/resolving. Positive control (gold impl) verifies exit 0, #print axioms correct_credentialAuth = [propext, Quot.sound] (clean, no sorryAx/oracle).

Command template: `bash scripts/lean_verify.sh <file>` from repo root.

Attacks (all same_spec=True, all lean_verify exit=1 unsolved-goals):
- atk_1: PREPATCH BUG reproduced — no missing-credential guard; store query fires even when a credential is absent (queries=1 on the _,_ branch). Fails (err line 114). prepatch_reproduced=true.
- atk_2: miss path drops the #20760 uniform-timing hash (hasherCalls:=0 instead of 1). Fails (line 114).
- atk_3: control-flow-effect — hit path returns some u unconditionally, ignoring passwordMatches/userAllowed. Fails (line 112).
- atk_4: ungrounded-oracle echo — missing-credential branch returns queries:=1 hasherCalls:=1 instead of 0/0. Fails (line 108).
- atk_5: boundary — hit path uses constant hasherCalls:=1 instead of checkHashCount u pw (wrong when stored password unusable => 0). Fails (line 115).
- atk_6: partial-domain/wrong-resolution — always uses fallback, ignoring positional name when present. Fails (line 124).
- atk_7: name resolution via pattern-match variant of the gold with a wrong-body twist retained; also fails to close (line 106).

Refinement audit: refinement.md declares only R and I legs; NO A-consumed / A-reference / kind-3 legs. Confirmed: axioms region = opaque signatures only, no _prop axioms consumed (positive control #print axioms clean). The 4 opaque callees appear IDENTICALLY in spec and impl (tag I) so they cancel and cannot hide a discriminating bug — G-AX correctly a skip stub. The changed op (missing-credential guard) is modeled DEEPLY as Lean control flow (row 2, R), pinned by the spec's _,_ branch requiring queries=0 AND hasherCalls=0; the prepatch impl's queries=1 makes its proof unclosable (atk_1). All A-leg/model-patch correspondence holds.

R/I legs mechanically covered by G-CONF (out of scope here). verify=>correct holds for all 8 attacks: no wrong impl verifies. No BROKEN witness found across >=5 distinct wrong-impl classes (prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
/-- An identified principal in the credential store. Only its identity is
observed by the modeled behavior. -/
structure User where
  uid : Nat
deriving Repr, DecidableEq, Inhabited

/-- The credential-store lookup, keyed by the resolved login name. Returns the
matching principal, or `none` when no principal carries that name. UNCHANGED by
the modeled behavior; the same lookup is referenced in the specification and the
implementation. -/
opaque lookupUser : List Char → Option User

/-- Whether the supplied secret matches the stored principal's secret. UNCHANGED;
referenced identically in the specification and the implementation. -/
opaque passwordMatches : User → List Char → Bool

/-- Whether the stored principal is permitted to authenticate (e.g. is active).
UNCHANGED; referenced identically in the specification and the implementation. -/
opaque userAllowed : User → Bool

/-- The number of secret-hashing operations that checking the supplied secret
against the stored principal's secret performs — an inherent cost of the check
itself, determined by the principal's stored state and the supplied secret
(e.g. zero when the stored secret is unusable, one in the ordinary case).
UNCHANGED; referenced identically in the specification and the implementation. -/
opaque checkHashCount : User → List Char → Nat
-- axioms-end

-- pure-start
/-- The outcome of a credential check: the authenticated principal (if any) plus
the two observable resource costs — the number of credential-store queries and
the number of secret-hashing operations performed. -/
structure AuthOutcome where
  user : Option User
  queries : Nat
  hasherCalls : Nat
deriving Repr, DecidableEq, Inhabited

/-- The login name actually used: the positional name when present, otherwise the
fallback name taken from the keyword argument. -/
def resolveName (name fallback : Option (List Char)) : Option (List Char) :=
  if name.isNone then fallback else name
-- pure-end

-- post-conditions-start
/-- Relates the outcome of a credential check to its inputs.

When either the resolved login name or the secret is absent, the check is
abandoned immediately: no principal is returned and neither a credential-store
query nor a secret-hashing operation is performed (both costs are zero).

When both are present, exactly one credential-store query is performed; if no
principal carries that name, exactly one secret-hashing operation is performed
(to keep the timing uniform) and no principal is returned; if a principal is
found, exactly the secret-hashing operations inherent in checking the supplied
secret against it are performed, and the principal is returned exactly when its
secret matches and it is permitted to authenticate. Every component of the
outcome is pinned to the inputs in every branch. -/
def problem_spec_credentialAuth
    (name fallback secret : Option (List Char)) (result : AuthOutcome) : Prop :=
  match resolveName name fallback, secret with
  | some login, some pw =>
      result.queries = 1 ∧
      (match lookupUser login with
       | none => result.user = none ∧ result.hasherCalls = 1
       | some u =>
           result.hasherCalls = checkHashCount u pw ∧
           result.user = (if passwordMatches u pw && userAllowed u then some u else none))
  | _, _ =>
      result.user = none ∧ result.queries = 0 ∧ result.hasherCalls = 0
-- post-conditions-end

-- impl-start
def implementation_credentialAuth
    (name fallback secret : Option (List Char)) : AuthOutcome := Id.run do
  let mut login := name
  if login.isNone then
    login := fallback
  match login, secret with
  | some loginName, some pw =>
      match lookupUser loginName with
      | none =>
          -- No principal carries this name: perform one secret-hashing operation
          -- to keep the timing uniform, and return no principal.
          return { user := none, queries := 1, hasherCalls := 1 }
      | some u =>
          -- Checking the supplied secret performs whatever hashing the check
          -- itself requires (once in the ordinary case, none when the stored
          -- secret is unusable).
          if passwordMatches u pw && userAllowed u then
            return { user := some u, queries := 1, hasherCalls := checkHashCount u pw }
          else
            return { user := none, queries := 1, hasherCalls := checkHashCount u pw }
  | _, _ =>
      -- A credential is absent: abandon the check before touching the store or
      -- the secret hasher.
      return { user := none, queries := 0, hasherCalls := 0 }
-- impl-end

-- proof-start
theorem correct_credentialAuth :
    ∀ (name fallback secret : Option (List Char)),
    problem_spec_credentialAuth name fallback secret
      (implementation_credentialAuth name fallback secret) := by
  intro name fallback secret
  unfold problem_spec_credentialAuth implementation_credentialAuth resolveName
  simp only [Id.run, bind, pure]
  by_cases hn : name.isNone
  · simp only [hn, if_true]
    cases fallback with
    | none => cases secret <;> simp
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u =>
          by_cases hp : passwordMatches u pw && userAllowed u <;>
            simp [hl, hp]
  · simp only [hn]
    cases hnm : name with
    | none => simp [hnm] at hn
    | some login =>
      cases secret with
      | none => simp
      | some pw =>
        cases hl : lookupUser login with
        | none => simp [hl]
        | some u =>
          by_cases hp : passwordMatches u pw && userAllowed u <;>
            simp [hl, hp]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_credentialAuth totally pins every AuthOutcome field (user, queries, hasherCalls) in every branch as a function of inputs + the four identically-referenced opaque callees. 7 same-spec wrong impls (all same_spec=True verified via markers.same_spec) each fail lean_verify.sh with exit 1 = genuine 'unsolved goals' proof errors (NOT import/env errors), so none produces a closing clean-axiom proof; no faithful patch needed materializing/resolving. Positive control (gold impl) verifies exit 0, #print axioms correct_credentialAuth = [propext, Quot.sound] (clean, no sorryAx/oracle).

Command template: `bash scripts/lean_verify.sh <file>` from repo root.

Attacks (all same_spec=True, all lean_verify exit=1 unsolved-goals):
- atk_1: PREPATCH BUG reproduced — no missing-credential guard; store query fires even when a credential is absent (queries=1 on the _,_ branch). Fails (err line 114). prepatch_reproduced=true.
- atk_2: miss path drops the #20760 uniform-timing hash (hasherCalls:=0 instead of 1). Fails (line 114).
- atk_3: control-flow-effect — hit path returns some u unconditionally, ignoring passwordMatches/userAllowed. Fails (line 112).
- atk_4: ungrounded-oracle echo — missing-credential branch returns queries:=1 hasherCalls:=1 instead of 0/0. Fails (line 108).
- atk_5: boundary — hit path uses constant hasherCalls:=1 instead of checkHashCount u pw (wrong when stored password unusable => 0). Fails (line 115).
- atk_6: partial-domain/wrong-resolution — always uses fallback, ignoring positional name when present. Fails (line 124).
- atk_7: name resolution via pattern-match variant of the gold with a wrong-body twist retained; also fails to close (line 106).

Refinement audit: refinement.md declares only R and I legs; NO A-consumed / A-reference / kind-3 legs. Confirmed: axioms region = opaque signatures only, no _prop axioms consumed (positive control #print axioms clean). The 4 opaque callees appear IDENTICALLY in spec and impl (tag I) so they cancel and cannot hide a discriminating bug — G-AX correctly a skip stub. The changed op (missing-credential guard) is modeled DEEPLY as Lean control flow (row 2, R), pinned by the spec's _,_ branch requiring queries=0 AND hasherCalls=0; the prepatch impl's queries=1 makes its proof unclosable (atk_1). All A-leg/model-patch correspondence holds.

R/I legs mechanically covered by G-CONF (out of scope here). verify=>correct holds for all 8 attacks: no wrong impl verifies. No BROKEN witness found across >=5 distinct wrong-impl classes (prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle echo).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on the Lean spec for django__django-11451 (ModelBackend.authenticate #20760 uniform-timing fix). Checks performed:

1) COMPILE + PROOF INTEGRITY: Solution.lean elaborates clean via scripts/lean_verify.sh (exit 0). `#print axioms correct_credentialAuth` => [propext, Quot.sound] only — NO sorryAx, proof is real (not a rubber-stamp).

2) SAME_SPEC: swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean_backend) == True. Spec region (axioms/pure/post-conditions) is byte-identical between patched and prepatch; only impl+proof differ (prepatch impl has no guard, proof is `sorry` = the G-DIFF witness). Correct construction.

3) REAL-REPO CROSS-CHECK (worktree @ base_commit, backends.py:36-49 patched form present; hashers.check_password short-circuits `if password is None or not is_password_usable(encoded): return False` before hasher.verify — confirmed): The modeled function agrees with the real callee on every input in the modeled domain:
  - Guard-fail branch (resolveName name fallback = none OR secret = none): spec requires user=none, queries=0, hasherCalls=0. Real `authenticate` returns before the try/except => zero DB query, zero hasher encode. MATCHES F2P assertNumQueries(0) / CountingMD5PasswordHasher.calls==0. Faithful.
  - Username resolution resolveName = (if name.isNone then fallback else name) exactly mirrors `if username is None: username = kwargs.get(USERNAME_FIELD)`. Faithful.
  - Both present, store MISS (lookupUser=none): spec queries=1, user=none, hasherCalls=1. Real: 1 get_by_natural_key then set_password(pw) => exactly 1 encode for any non-None pw including empty string (some []). Faithful (make_password only skips the hash for None, which cannot occur here since secret=some pw).
  - Both present, store HIT (lookupUser=some u): spec queries=1, hasherCalls=checkHashCount u pw, user = some u iff (passwordMatches u pw && userAllowed u). Real: 1 query, check_password's internal encode count, returns user iff check_password AND user_can_authenticate. Python `and` short-circuit is side-effect-safe (user_can_authenticate has no counted effects). Faithful.

4) ABSTRACTION SOUNDNESS: the two observable side effects (bool match, encode count) are total opaque functions (passwordMatches/userAllowed/checkHashCount), and correct_credentialAuth is universally quantified over them — every real (bool, count) realization is covered, so no adversarial oracle can produce divergence. checkHashCount correctly captures the unusable-stored-password case (0 encodes). The only real-code path outside the abstraction (stored hash needs rehash => setter fires extra save-query + encode) does NOT occur under the tested config (MD5 must_update=False; CountingMD5PasswordHasher default) and `queries` is explicitly scoped by mapping.md to get_by_natural_key calls (=1 on both-present).

No diverging input found. The spec is neither too strong nor drifting: it demands exactly what the patched repo does on the F2P-observable projection (returned user + query count + hasher-call count). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view derived via markers.spec_view(LeanBackend.language) with impl+proof correctly elided. same_spec(Solution_prepatch, Solution) = True, so the discriminating logic (the added missing-credential short-circuit) lives only in the elided impl/proof, not the spec view.

The spec view exposes: neutral opaque callee sigs (lookupUser/passwordMatches/userAllowed/checkHashCount), the AuthOutcome record (user/queries/hasherCalls), resolveName, and problem_spec_credentialAuth. I checked each against the PUBLIC problem_statement baseline (NOT hints).

Crucially, the problem_statement itself already states the gold edit VERBATIM: 'My suggestion is to shortcut with: if username is None or password is None: return', and explicitly describes the useless DB query, the needless hasher run, and the #20760 uniform-timing set_password behavior. The spec postcondition's missing-credential branch (queries=0 ∧ hasherCalls=0), the miss-path hasherCalls=1 'to keep the timing uniform', and the username/kwargs resolution fallback all correspond exactly to content already public in problem_statement. No gold-patch tokens, no leaky verbatim phrasing beyond the public statement, identifiers are abstract. The spec view reveals nothing about the gold edit beyond what problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
