# P2 adversarial audit — django__django-13551

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,10 @@
 def implementation_tokenState
     (pk password loginTs ts : String) (emailRaw : Option String) : String :=
   Id.run do
-    let email := emailPart emailRaw
     let mut s := pk
     s := s ++ password
     s := s ++ loginTs
     s := s ++ ts
-    s := s ++ email
     return s
 -- impl-end
 
@@ -70,6 +68,10 @@
       problem_spec_tokenState pk password loginTs ts emailRaw
         (implementation_tokenState pk password loginTs ts emailRaw) := by
   intro pk password loginTs ts emailRaw
-  unfold problem_spec_tokenState implementation_tokenState
-  rfl
+  unfold problem_spec_tokenState implementation_tokenState emailPart
+  first
+    | rfl
+    | (simp [Id.run])
+    | (cases emailRaw <;> simp [Id.run])
+    | (cases emailRaw <;> rfl)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,14 +54,9 @@
 -- impl-start
 def implementation_tokenState
     (pk password loginTs ts : String) (emailRaw : Option String) : String :=
-  Id.run do
-    let email := emailPart emailRaw
-    let mut s := pk
-    s := s ++ password
-    s := s ++ loginTs
-    s := s ++ ts
-    s := s ++ email
-    return s
+  match emailRaw with
+  | some e => pk ++ password ++ loginTs ++ ts ++ e
+  | none   => pk ++ password ++ loginTs ++ ts ++ "none"
 -- impl-end
 
 -- proof-start
@@ -70,6 +65,10 @@
       problem_spec_tokenState pk password loginTs ts emailRaw
         (implementation_tokenState pk password loginTs ts emailRaw) := by
   intro pk password loginTs ts emailRaw
-  unfold problem_spec_tokenState implementation_tokenState
-  rfl
+  unfold problem_spec_tokenState implementation_tokenState emailPart
+  first
+    | rfl
+    | (simp [Id.run])
+    | (cases emailRaw <;> simp [Id.run])
+    | (cases emailRaw <;> rfl)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,14 +54,7 @@
 -- impl-start
 def implementation_tokenState
     (pk password loginTs ts : String) (emailRaw : Option String) : String :=
-  Id.run do
-    let email := emailPart emailRaw
-    let mut s := pk
-    s := s ++ password
-    s := s ++ loginTs
-    s := s ++ ts
-    s := s ++ email
-    return s
+  pk ++ password ++ loginTs ++ ts ++ (emailRaw.getD "x")
 -- impl-end
 
 -- proof-start
@@ -70,6 +63,10 @@
       problem_spec_tokenState pk password loginTs ts emailRaw
         (implementation_tokenState pk password loginTs ts emailRaw) := by
   intro pk password loginTs ts emailRaw
-  unfold problem_spec_tokenState implementation_tokenState
-  rfl
+  unfold problem_spec_tokenState implementation_tokenState emailPart
+  first
+    | rfl
+    | (simp [Id.run])
+    | (cases emailRaw <;> simp [Id.run])
+    | (cases emailRaw <;> rfl)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,14 +54,7 @@
 -- impl-start
 def implementation_tokenState
     (pk password loginTs ts : String) (emailRaw : Option String) : String :=
-  Id.run do
-    let email := emailPart emailRaw
-    let mut s := pk
-    s := s ++ password
-    s := s ++ loginTs
-    s := s ++ ts
-    s := s ++ email
-    return s
+  pk ++ password ++ ts ++ loginTs ++ (emailPart emailRaw)
 -- impl-end
 
 -- proof-start
@@ -70,6 +63,10 @@
       problem_spec_tokenState pk password loginTs ts emailRaw
         (implementation_tokenState pk password loginTs ts emailRaw) := by
   intro pk password loginTs ts emailRaw
-  unfold problem_spec_tokenState implementation_tokenState
-  rfl
+  unfold problem_spec_tokenState implementation_tokenState emailPart
+  first
+    | rfl
+    | (simp [Id.run])
+    | (cases emailRaw <;> simp [Id.run])
+    | (cases emailRaw <;> rfl)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,14 +54,7 @@
 -- impl-start
 def implementation_tokenState
     (pk password loginTs ts : String) (emailRaw : Option String) : String :=
-  Id.run do
-    let email := emailPart emailRaw
-    let mut s := pk
-    s := s ++ password
-    s := s ++ loginTs
-    s := s ++ ts
-    s := s ++ email
-    return s
+  pk ++ password ++ loginTs ++ ts
 -- impl-end
 
 -- proof-start
@@ -70,6 +63,10 @@
       problem_spec_tokenState pk password loginTs ts emailRaw
         (implementation_tokenState pk password loginTs ts emailRaw) := by
   intro pk password loginTs ts emailRaw
-  unfold problem_spec_tokenState implementation_tokenState
-  rfl
+  unfold problem_spec_tokenState implementation_tokenState emailPart
+  first
+    | rfl
+    | (simp [Id.run])
+    | (cases emailRaw <;> simp [Id.run])
+    | (cases emailRaw <;> rfl)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,14 +54,7 @@
 -- impl-start
 def implementation_tokenState
     (pk password loginTs ts : String) (emailRaw : Option String) : String :=
-  Id.run do
-    let email := emailPart emailRaw
-    let mut s := pk
-    s := s ++ password
-    s := s ++ loginTs
-    s := s ++ ts
-    s := s ++ email
-    return s
+  pk ++ password ++ loginTs ++ ts ++ (emailPart emailRaw) ++ (emailPart emailRaw)
 -- impl-end
 
 -- proof-start
@@ -70,6 +63,10 @@
       problem_spec_tokenState pk password loginTs ts emailRaw
         (implementation_tokenState pk password loginTs ts emailRaw) := by
   intro pk password loginTs ts emailRaw
-  unfold problem_spec_tokenState implementation_tokenState
-  rfl
+  unfold problem_spec_tokenState implementation_tokenState emailPart
+  first
+    | rfl
+    | (simp [Id.run])
+    | (cases emailRaw <;> simp [Id.run])
+    | (cases emailRaw <;> rfl)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a user's password-reset token state string.

A single-use password-reset token is derived from a state string that fingerprints
the security-sensitive parts of a user account. The token stays valid only while
that fingerprint is unchanged; as soon as any contributing piece of account state
changes, the recomputed fingerprint differs and the outstanding token no longer
matches.

The state string is the ordered concatenation of:

  * `pk`        — the user's primary-key value;
  * `password`  — the stored password representation;
  * `loginTs`   — the last-login timestamp (rendered empty when there is none);
  * `ts`        — the token's own timestamp; and
  * the user's email address.

A user is not required to have an email address. The email contribution is
therefore normalized: a present address contributes its own characters, while an
absent address (no value on the account) contributes the empty string — so the
state string is always well defined.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The mechanism
-- that locates and reads the user's email address is abstracted at the I/O
-- boundary into the `emailRaw` input (an optional string: the value carried by
-- the account, or none when the account has none). The state string is then
-- assembled structurally, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Normalize the optional email contribution to the characters it adds to the
state string: a present value contributes itself; an absent value contributes
the empty string. -/
def emailPart (emailRaw : Option String) : String := emailRaw.getD ""
-- pure-end

-- post-conditions-start
/-- The state string is exactly the ordered concatenation of the user's
primary-key value, password representation, last-login timestamp, token
timestamp, and (normalized) email contribution. Every component — including the
email — is pinned to its input, so the fingerprint is fully determined by the
account state and changes whenever any component (the email included) changes. -/
def problem_spec_tokenState
    (pk password loginTs ts : String) (emailRaw : Option String)
    (result : String) : Prop :=
  result = pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw
-- post-conditions-end

-- impl-start
def implementation_tokenState
    (pk password loginTs ts : String) (emailRaw : Option String) : String :=
  Id.run do
    let email := emailPart emailRaw
    let mut s := pk
    s := s ++ password
    s := s ++ loginTs
    s := s ++ ts
    s := s ++ email
    return s
-- impl-end

-- proof-start
theorem correct_tokenState :
    ∀ (pk password loginTs ts : String) (emailRaw : Option String),
      problem_spec_tokenState pk password loginTs ts emailRaw
        (implementation_tokenState pk password loginTs ts emailRaw) := by
  intro pk password loginTs ts emailRaw
  unfold problem_spec_tokenState implementation_tokenState
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_tokenState is a TOTAL FUNCTIONAL EQUALITY: result = pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw (emailPart := Option.getD ""). It pins result to a single closed-form value on every input, with no unconstrained component or oracle slack; therefore any impl whose correct_tokenState closes must be extensionally equal to gold and necessarily resolves. No closing-but-non-resolving alternative can exist.

PROTOCOL: same_spec=True verified for all 6 attacks and pos_control via swebench_unified.markers.same_spec (lean backend). Verifications run concurrently in two background batches of <=4.

### RESULTS (cmd: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean (gold): exit 0 (closes, no sorry). #print axioms correct_tokenState -> 'does not depend on any axioms' (clean; via pos_ax.lean, exit 0).
- atk_1.lean prepatch bug (omit email append): exit 1. Residual goal `pure (pk++password++loginTs++ts) = pk++password++loginTs++ts ++ emailRaw.getD ""` — unprovable. PREPATCH BUG REPRODUCED (proof cannot close).
- atk_2.lean partial-domain (none |-> "none" sentinel instead of ""): exit 1.
- atk_3.lean boundary (wrong default: emailRaw.getD "x"): exit 1.
- atk_4.lean control-flow-effect (swap ts and loginTs order): exit 1.
- atk_5.lean ungrounded-oracle echo (drop email suffix): exit 1.
- atk_6.lean double-append email (... ++ emailPart ++ emailPart): exit 1.
All 6 wrong impls FAIL to close (exit 1, genuine elaboration error — goal is a false equality). The proof footer honestly attempted closure via `first | rfl | simp[Id.run] | cases emailRaw <;> simp[Id.run] | cases emailRaw <;> rfl`; none discharged.

Since NO wrong impl closes with a clean-axiom proof, there is no verifying-but-non-resolving impl; patches={} (nothing to materialize/run through run_resolve). No BROKEN condition triggered.

refinement.md AUDIT: 8 legs, all R/I (steps 1-2 = R, steps 3-8 = I). ZERO A-consumed and ZERO A-reference legs; no kind-3 leg. axiom_check.py is a skip stub — consistent: the changed op (email append) is modeled DEEPLY as string concatenation (s := s ++ email), not axiomatized, so no consumed callee axiom and G-AX skips legitimately. No A-leg correspondence to audit (vacuously satisfied). R/I legs are covered by G-CONF (conformance_check.py: 120007 inputs incl. email edge cases None/''/present, 0 disagreements against faithful post-patch _make_hash_value replica).

VERDICT: SOUND — >=5 distinct same-spec wrong impls attacked, none closes, positive control verifies with clean axioms, refinement legs all R/I and internally consistent.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Building a user's password-reset token state string.

A single-use password-reset token is derived from a state string that fingerprints
the security-sensitive parts of a user account. The token stays valid only while
that fingerprint is unchanged; as soon as any contributing piece of account state
changes, the recomputed fingerprint differs and the outstanding token no longer
matches.

The state string is the ordered concatenation of:

  * `pk`        — the user's primary-key value;
  * `password`  — the stored password representation;
  * `loginTs`   — the last-login timestamp (rendered empty when there is none);
  * `ts`        — the token's own timestamp; and
  * the user's email address.

A user is not required to have an email address. The email contribution is
therefore normalized: a present address contributes its own characters, while an
absent address (no value on the account) contributes the empty string — so the
state string is always well defined.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The mechanism
-- that locates and reads the user's email address is abstracted at the I/O
-- boundary into the `emailRaw` input (an optional string: the value carried by
-- the account, or none when the account has none). The state string is then
-- assembled structurally, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- Normalize the optional email contribution to the characters it adds to the
state string: a present value contributes itself; an absent value contributes
the empty string. -/
def emailPart (emailRaw : Option String) : String := emailRaw.getD ""
-- pure-end

-- post-conditions-start
/-- The state string is exactly the ordered concatenation of the user's
primary-key value, password representation, last-login timestamp, token
timestamp, and (normalized) email contribution. Every component — including the
email — is pinned to its input, so the fingerprint is fully determined by the
account state and changes whenever any component (the email included) changes. -/
def problem_spec_tokenState
    (pk password loginTs ts : String) (emailRaw : Option String)
    (result : String) : Prop :=
  result = pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw
-- post-conditions-end

-- impl-start
def implementation_tokenState
    (pk password loginTs ts : String) (emailRaw : Option String) : String :=
  Id.run do
    let email := emailPart emailRaw
    let mut s := pk
    s := s ++ password
    s := s ++ loginTs
    s := s ++ ts
    s := s ++ email
    return s
-- impl-end

-- proof-start
theorem correct_tokenState :
    ∀ (pk password loginTs ts : String) (emailRaw : Option String),
      problem_spec_tokenState pk password loginTs ts emailRaw
        (implementation_tokenState pk password loginTs ts emailRaw) := by
  intro pk password loginTs ts emailRaw
  unfold problem_spec_tokenState implementation_tokenState
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_tokenState is a TOTAL FUNCTIONAL EQUALITY: result = pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw (emailPart := Option.getD ""). It pins result to a single closed-form value on every input, with no unconstrained component or oracle slack; therefore any impl whose correct_tokenState closes must be extensionally equal to gold and necessarily resolves. No closing-but-non-resolving alternative can exist.

PROTOCOL: same_spec=True verified for all 6 attacks and pos_control via swebench_unified.markers.same_spec (lean backend). Verifications run concurrently in two background batches of <=4.

### RESULTS (cmd: `bash scripts/lean_verify.sh <file>`):
- pos_control.lean (gold): exit 0 (closes, no sorry). #print axioms correct_tokenState -> 'does not depend on any axioms' (clean; via pos_ax.lean, exit 0).
- atk_1.lean prepatch bug (omit email append): exit 1. Residual goal `pure (pk++password++loginTs++ts) = pk++password++loginTs++ts ++ emailRaw.getD ""` — unprovable. PREPATCH BUG REPRODUCED (proof cannot close).
- atk_2.lean partial-domain (none |-> "none" sentinel instead of ""): exit 1.
- atk_3.lean boundary (wrong default: emailRaw.getD "x"): exit 1.
- atk_4.lean control-flow-effect (swap ts and loginTs order): exit 1.
- atk_5.lean ungrounded-oracle echo (drop email suffix): exit 1.
- atk_6.lean double-append email (... ++ emailPart ++ emailPart): exit 1.
All 6 wrong impls FAIL to close (exit 1, genuine elaboration error — goal is a false equality). The proof footer honestly attempted closure via `first | rfl | simp[Id.run] | cases emailRaw <;> simp[Id.run] | cases emailRaw <;> rfl`; none discharged.

Since NO wrong impl closes with a clean-axiom proof, there is no verifying-but-non-resolving impl; patches={} (nothing to materialize/run through run_resolve). No BROKEN condition triggered.

refinement.md AUDIT: 8 legs, all R/I (steps 1-2 = R, steps 3-8 = I). ZERO A-consumed and ZERO A-reference legs; no kind-3 leg. axiom_check.py is a skip stub — consistent: the changed op (email append) is modeled DEEPLY as string concatenation (s := s ++ email), not axiomatized, so no consumed callee axiom and G-AX skips legitimately. No A-leg correspondence to audit (vacuously satisfied). R/I legs are covered by G-CONF (conformance_check.py: 120007 inputs incl. email edge cases None/''/present, 0 disagreements against faithful post-patch _make_hash_value replica).

VERDICT: SOUND — >=5 distinct same-spec wrong impls attacked, none closes, positive control verifies with clean axioms, refinement legs all R/I and internally consistent.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of django__django-13551 lean bundle. Modeled function: PasswordResetTokenGenerator._make_hash_value, post-patch. Spec problem_spec_tokenState pins result EXACTLY to pk ++ password ++ loginTs ++ ts ++ emailPart emailRaw with emailPart emailRaw = emailRaw.getD "". Verified: (1) Solution.lean compiles clean, exit 0, no sorry; (2) #print axioms correct_tokenState => 'does not depend on any axioms' — real rfl proof, no sorryAx; (3) same_spec(Solution, Solution_prepatch, lean-backend) = True — spec region byte-identical, prepatch differs only in impl (omits 's := s ++ email'). Drift analysis: real code returns f'{user.pk}{user.password}{login_timestamp}{timestamp}{email}' with email = getattr(user, field, '') or ''. f-string concatenation of pre-stringified components is byte-identical to Lean ++; the 'or ""' falsy normalization coerces the only falsy string ('') and absent/None to '', which emailPart reproduces exactly (some "" -> "", some s -> s, none -> ""). Model and real callee agree on every input class: present email, empty-string email, and absent email. No diverging input exists. The postcondition is a complete functional equality to the exact returned string — faithful, not too strong; a full functional spec is not drift. G-CONF replica (conformance_check.py) transliterates both legs and agrees over hand-picked edge cases plus 120k seeded-fuzz inputs. Conclusion: FAITHFUL, no defect.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (docstring + emailPart + problem_spec_tokenState) verified via markers.spec_view; same_spec(Solution, prepatch)=True (spec not drifted/weakened by the fix); Solution.lean compiles (lean_verify exit 0).

Comparison to PUBLIC problem_statement (not hints_text; hints_text is empty here anyway):
- problem_statement states verbatim: 'The fix is to add the user's email address into PasswordResetTokenGenerator._make_hash_value()' and 'Nothing forces a user to even have an email as per AbstractBaseUser.'
- The spec view's only novel modeled fact — appending the email as a final concat component (docstring bullet 'the user's email address'; problem_spec result = pk++password++loginTs++ts++emailPart emailRaw) — is exactly the fix the problem_statement names.
- The absent-email→empty-string normalization (emailPart := Option.getD ""; docstring 'an absent address contributes the empty string') is exactly the 'not required to have an email' disclosure.
- The four pre-existing components (pk, password, loginTs, ts) are the base_commit behavior, already public in the repo; they are not gold-edit content.

The actual gold-diff implementation specifics — the f-string reformat, email_field = user.get_email_field_name(), getattr(user, email_field, '') or '' — are abstracted behind the emailRaw : Option String I/O boundary and do NOT appear anywhere in the spec view. No spec-view line discloses anything about the gold edit beyond what problem_statement already states. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
