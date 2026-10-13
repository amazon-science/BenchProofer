# P2 adversarial audit — django__django-13410

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl produced a closing clean-axiom proof, so there is no verifying patch to materialize/resolve. The spec is a TOTAL FUNCTIONAL specification: problem_spec_acquire pins result to an exact `match outcome with .ok _ => .ok true | .error .wouldBlock => .ok false | .error (.other c) => .error (.other c)` for every input, and problem_spec_release pins result to `outcome.map (fun _ => true)` for every input. No precondition, no partial domain, no existential/oracle escape hatch. Hence any impl that verifies must be pointwise-equal to gold; every wrong impl fails with genuine `unsolved goals`.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,23 +66,21 @@
 
 -- impl-start
 def implementation_acquire (outcome : Outcome) : Except FlockErr Bool := do
-  try
-    let _ ← outcome
-    return true
-  catch e =>
-    match e with
-    | .wouldBlock => return false
-    | .other c    => throw (.other c)
+  let _ ← outcome
+  return false
 -- impl-end
 
 -- proof-start
 theorem correct_acquire : ∀ (outcome : Outcome),
     problem_spec_acquire outcome (implementation_acquire outcome) := by
   intro outcome
-  match outcome with
-  | .ok _ => rfl
-  | .error .wouldBlock => rfl
-  | .error (.other _) => rfl
+  first
+  | rfl
+  | (match outcome with
+     | .ok _ => rfl
+     | .error .wouldBlock => rfl
+     | .error (.other _) => rfl)
+  | simp_all [implementation_acquire, problem_spec_acquire]
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,12 +96,15 @@
 -- impl-start
 def implementation_release (outcome : Outcome) : Except FlockErr Bool := do
   let _ ← outcome
-  return true
+  return false
 -- impl-end
 
 -- proof-start
 theorem correct_release : ∀ (outcome : Outcome),
     problem_spec_release outcome (implementation_release outcome) := by
   intro outcome
-  rcases outcome with u | e <;> rfl
+  first
+  | rfl
+  | (rcases outcome with u | e <;> rfl)
+  | simp_all [implementation_release, problem_spec_release]
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
     return true
   catch e =>
     match e with
-    | .wouldBlock => return false
+    | .wouldBlock => return true
     | .other c    => throw (.other c)
 -- impl-end
 
@@ -79,10 +79,13 @@
 theorem correct_acquire : ∀ (outcome : Outcome),
     problem_spec_acquire outcome (implementation_acquire outcome) := by
   intro outcome
-  match outcome with
-  | .ok _ => rfl
-  | .error .wouldBlock => rfl
-  | .error (.other _) => rfl
+  first
+  | rfl
+  | (match outcome with
+     | .ok _ => rfl
+     | .error .wouldBlock => rfl
+     | .error (.other _) => rfl)
+  | simp_all [implementation_acquire, problem_spec_acquire]
 -- proof-end
 
 -- post-conditions-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,20 +69,21 @@
   try
     let _ ← outcome
     return true
-  catch e =>
-    match e with
-    | .wouldBlock => return false
-    | .other c    => throw (.other c)
+  catch _ =>
+    return false
 -- impl-end
 
 -- proof-start
 theorem correct_acquire : ∀ (outcome : Outcome),
     problem_spec_acquire outcome (implementation_acquire outcome) := by
   intro outcome
-  match outcome with
-  | .ok _ => rfl
-  | .error .wouldBlock => rfl
-  | .error (.other _) => rfl
+  first
+  | rfl
+  | (match outcome with
+     | .ok _ => rfl
+     | .error .wouldBlock => rfl
+     | .error (.other _) => rfl)
+  | simp_all [implementation_acquire, problem_spec_acquire]
 -- proof-end
 
 -- post-conditions-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,24 +65,24 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_acquire (outcome : Outcome) : Except FlockErr Bool := do
-  try
-    let _ ← outcome
-    return true
-  catch e =>
-    match e with
-    | .wouldBlock => return false
-    | .other c    => throw (.other c)
+def implementation_acquire (outcome : Outcome) : Except FlockErr Bool :=
+  match outcome with
+  | .ok _              => .ok true
+  | .error .wouldBlock => .ok false
+  | .error (.other _)  => .ok false
 -- impl-end
 
 -- proof-start
 theorem correct_acquire : ∀ (outcome : Outcome),
     problem_spec_acquire outcome (implementation_acquire outcome) := by
   intro outcome
-  match outcome with
-  | .ok _ => rfl
-  | .error .wouldBlock => rfl
-  | .error (.other _) => rfl
+  first
+  | rfl
+  | (match outcome with
+     | .ok _ => rfl
+     | .error .wouldBlock => rfl
+     | .error (.other _) => rfl)
+  | simp_all [implementation_acquire, problem_spec_acquire]
 -- proof-end
 
 -- post-conditions-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,14 +94,18 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_release (outcome : Outcome) : Except FlockErr Bool := do
-  let _ ← outcome
-  return true
+def implementation_release (outcome : Outcome) : Except FlockErr Bool :=
+  match outcome with
+  | .ok _     => .ok true
+  | .error _  => .ok true
 -- impl-end
 
 -- proof-start
 theorem correct_release : ∀ (outcome : Outcome),
     problem_spec_release outcome (implementation_release outcome) := by
   intro outcome
-  rcases outcome with u | e <;> rfl
+  first
+  | rfl
+  | (rcases outcome with u | e <;> rfl)
+  | simp_all [implementation_release, problem_spec_release]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the outcome of an advisory file-lock operation as a boolean.

A process acquires or releases an advisory lock on an open file through a
lower-level locking primitive. That primitive reports its result through two
distinct channels:

  * it COMPLETES normally when the requested operation was carried out
    (the lock was acquired, or released); and
  * for a non-blocking request, it SIGNALS — out of band — that the lock could
    not be granted right now, instead of completing.

The operation modeled here turns that two-channel result into a single boolean
status that a caller can test:

  * acquiring a lock returns `True` when the primitive completed (the lock was
    obtained) and `False` when a non-blocking request could not be satisfied;
  * releasing a lock returns `True` when the primitive completed.

The argument `outcome` records which channel the lower-level primitive used:
`ok ()` for a completed operation, `error wouldBlock` for an unsatisfiable
non-blocking request. The result is the boolean status (carried in the same
two-channel form, so an out-of-band signal that is not handled is propagated
rather than turned into a status).
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The lower-level locking
-- primitive is NOT modeled here: its result is abstracted as the `outcome`
-- argument (the value/`ok` channel vs. the out-of-band/`error` channel). The
-- only logic modeled is turning that result into a boolean status, which is a
-- pure transformation over `outcome`. Hence no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- An out-of-band signal the lower-level primitive can raise. `wouldBlock` is
the specific signal a non-blocking request raises when the lock cannot be
granted right now; `other` is any other failure signal (carrying its code). The
acquire operation handles ONLY `wouldBlock`; every other signal is propagated. -/
inductive FlockErr where
  | wouldBlock
  | other (code : Int)
deriving DecidableEq, Repr

/-- The two-channel result of the lower-level locking primitive: `ok ()` means
the operation completed; `error wouldBlock` means a non-blocking request could
not be granted. -/
abbrev Outcome := Except FlockErr Unit
-- pure-end

-- post-conditions-start
/-- Acquiring a lock: the status is fully pinned to the primitive's result —
`ok true` when the primitive completed (lock obtained), `ok false` when a
non-blocking request could not be granted, and any OTHER out-of-band signal is
propagated unchanged (only the not-granted-right-now signal is turned into a
status). -/
def problem_spec_acquire (outcome : Outcome) (result : Except FlockErr Bool) : Prop :=
  result = (match outcome with
            | .ok _              => .ok true
            | .error .wouldBlock => .ok false
            | .error (.other c)  => .error (.other c))
-- post-conditions-end

-- impl-start
def implementation_acquire (outcome : Outcome) : Except FlockErr Bool := do
  try
    let _ ← outcome
    return true
  catch e =>
    match e with
    | .wouldBlock => return false
    | .other c    => throw (.other c)
-- impl-end

-- proof-start
theorem correct_acquire : ∀ (outcome : Outcome),
    problem_spec_acquire outcome (implementation_acquire outcome) := by
  intro outcome
  match outcome with
  | .ok _ => rfl
  | .error .wouldBlock => rfl
  | .error (.other _) => rfl
-- proof-end

-- post-conditions-start
/-- Releasing a lock: the status is fully pinned to the primitive's result —
`ok true` when the primitive completed (lock released); an out-of-band signal,
not being handled, is propagated unchanged. -/
def problem_spec_release (outcome : Outcome) (result : Except FlockErr Bool) : Prop :=
  result = outcome.map (fun _ => true)
-- post-conditions-end

-- impl-start
def implementation_release (outcome : Outcome) : Except FlockErr Bool := do
  let _ ← outcome
  return true
-- impl-end

-- proof-start
theorem correct_release : ∀ (outcome : Outcome),
    problem_spec_release outcome (implementation_release outcome) := by
  intro outcome
  rcases outcome with u | e <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. All 6 attacks confirmed same_spec=True (spec/axioms/pure/pre/post byte-identical; only impl+proof regions edited). Verified concurrently via `bash scripts/lean_verify.sh <f>` in batches of ≤4.

### ATTACKS (all same_spec=True, all FAIL to verify, exit 1 'unsolved goals'):
- atk_1: prepatch bug (acquire) `let _ ← outcome; return false` (always-false). exit 1, unsolved goals at proof (spec demands .ok true on .ok channel). = FAIL_TO_PASS reproduction for acquire.
- atk_2: prepatch bug (release) `let _ ← outcome; return false`. exit 1, unsolved goals. = FAIL_TO_PASS reproduction for release.
- atk_3: boundary swap (acquire) — `.wouldBlock => return true` instead of false. exit 1, unsolved goals (spec: .error .wouldBlock => .ok false).
- atk_4: control-flow-effect (acquire) — `catch _ => return false`, swallows .other instead of propagating `throw (.other c)`. exit 1, unsolved goals (spec propagates .error (.other c)).
- atk_5: ungrounded-oracle echo (acquire) — echoes spec match shape but maps `.error (.other _) => .ok false`. exit 1, unsolved goals (spec: .error (.other c) => .error (.other c)).
- atk_6: partial/wrong-channel (release) — `.error _ => .ok true`, turns propagated error into ok-true. exit 1, unsolved goals (spec: outcome.map => .error propagated unchanged).
Each given a generous proof attempt: `first | rfl | (match/rcases ... <;> rfl) | simp_all [impl, spec]`. All three tactics failed → genuine non-equivalence, not a weak proof.

POSITIVE CONTROL: pos_control.lean = byte copy of gold Solution.lean. `lean_verify.sh` exit 0, empty output (no errors/sorry). axcheck.lean (`#print axioms correct_acquire/correct_release`) => both 'does not depend on any axioms' (clean).

No verifying wrong impl ⇒ zero patches to run through run_resolve; the materialize+resolve obligation is vacuously discharged (nothing verified falsely).

REFINEMENT.md AUDIT: 7 legs, all R or I (acquire ops #1,#2,#5 = R; #3,#4 = I; release #1 = R, #2 = I). No A-consumed / no A-reference legs; meta.json axioms=[], deep_model_references=[], conf_skip=false — consistent. The lower-level primitive fcntl.flock is NOT axiomatized/deep-modeled: it is abstracted as the `outcome : Except FlockErr Unit` input argument (its two channels None/OSError ↦ .ok ()/.error). Since no A-legs exist, there is no callee-correspondence axiom hazard for this bundle; the A-leg focus of this reviewer is vacuous here and the R/I legs (G-CONF territory) are internally consistent. The two-constructor FlockErr (wouldBlock vs other) is the discriminating design that blocks error-collapsing wrong impls (atk_4/atk_5/atk_6 all rely on collapsing/misrouting the .other channel and all fail).

Verdict SOUND: ≥5 distinct same-spec wrong impls (6 run) all fail to verify; positive control verifies with clean axioms; spec is total-functional so verify⇒pointwise-equal-to-gold. No verify⇏correct gap exhibited.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong impl produced a closing clean-axiom proof, so there is no verifying patch to materialize/resolve. The spec is a TOTAL FUNCTIONAL specification: problem_spec_acquire pins result to an exact `match outcome with .ok _ => .ok true | .error .wouldBlock => .ok false | .error (.other c) => .error (.other c)` for every input, and problem_spec_release pins result to `outcome.map (fun _ => true)` for every input. No precondition, no partial domain, no existential/oracle escape hatch. Hence any impl that verifies must be pointwise-equal to gold; every wrong impl fails with genuine `unsolved goals`.
```

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
Reporting the outcome of an advisory file-lock operation as a boolean.

A process acquires or releases an advisory lock on an open file through a
lower-level locking primitive. That primitive reports its result through two
distinct channels:

  * it COMPLETES normally when the requested operation was carried out
    (the lock was acquired, or released); and
  * for a non-blocking request, it SIGNALS — out of band — that the lock could
    not be granted right now, instead of completing.

The operation modeled here turns that two-channel result into a single boolean
status that a caller can test:

  * acquiring a lock returns `True` when the primitive completed (the lock was
    obtained) and `False` when a non-blocking request could not be satisfied;
  * releasing a lock returns `True` when the primitive completed.

The argument `outcome` records which channel the lower-level primitive used:
`ok ()` for a completed operation, `error wouldBlock` for an unsatisfiable
non-blocking request. The result is the boolean status (carried in the same
two-channel form, so an out-of-band signal that is not handled is propagated
rather than turned into a status).
-/

-- axioms-start
-- No UNCHANGED callee is consumed as an opaque axiom. The lower-level locking
-- primitive is NOT modeled here: its result is abstracted as the `outcome`
-- argument (the value/`ok` channel vs. the out-of-band/`error` channel). The
-- only logic modeled is turning that result into a boolean status, which is a
-- pure transformation over `outcome`. Hence no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
/-- An out-of-band signal the lower-level primitive can raise. `wouldBlock` is
the specific signal a non-blocking request raises when the lock cannot be
granted right now; `other` is any other failure signal (carrying its code). The
acquire operation handles ONLY `wouldBlock`; every other signal is propagated. -/
inductive FlockErr where
  | wouldBlock
  | other (code : Int)
deriving DecidableEq, Repr

/-- The two-channel result of the lower-level locking primitive: `ok ()` means
the operation completed; `error wouldBlock` means a non-blocking request could
not be granted. -/
abbrev Outcome := Except FlockErr Unit
-- pure-end

-- post-conditions-start
/-- Acquiring a lock: the status is fully pinned to the primitive's result —
`ok true` when the primitive completed (lock obtained), `ok false` when a
non-blocking request could not be granted, and any OTHER out-of-band signal is
propagated unchanged (only the not-granted-right-now signal is turned into a
status). -/
def problem_spec_acquire (outcome : Outcome) (result : Except FlockErr Bool) : Prop :=
  result = (match outcome with
            | .ok _              => .ok true
            | .error .wouldBlock => .ok false
            | .error (.other c)  => .error (.other c))
-- post-conditions-end

-- impl-start
def implementation_acquire (outcome : Outcome) : Except FlockErr Bool := do
  try
    let _ ← outcome
    return true
  catch e =>
    match e with
    | .wouldBlock => return false
    | .other c    => throw (.other c)
-- impl-end

-- proof-start
theorem correct_acquire : ∀ (outcome : Outcome),
    problem_spec_acquire outcome (implementation_acquire outcome) := by
  intro outcome
  match outcome with
  | .ok _ => rfl
  | .error .wouldBlock => rfl
  | .error (.other _) => rfl
-- proof-end

-- post-conditions-start
/-- Releasing a lock: the status is fully pinned to the primitive's result —
`ok true` when the primitive completed (lock released); an out-of-band signal,
not being handled, is propagated unchanged. -/
def problem_spec_release (outcome : Outcome) (result : Except FlockErr Bool) : Prop :=
  result = outcome.map (fun _ => true)
-- post-conditions-end

-- impl-start
def implementation_release (outcome : Outcome) : Except FlockErr Bool := do
  let _ ← outcome
  return true
-- impl-end

-- proof-start
theorem correct_release : ∀ (outcome : Outcome),
    problem_spec_release outcome (implementation_release outcome) := by
  intro outcome
  rcases outcome with u | e <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL. All 6 attacks confirmed same_spec=True (spec/axioms/pure/pre/post byte-identical; only impl+proof regions edited). Verified concurrently via `bash scripts/lean_verify.sh <f>` in batches of ≤4.

### ATTACKS (all same_spec=True, all FAIL to verify, exit 1 'unsolved goals'):
- atk_1: prepatch bug (acquire) `let _ ← outcome; return false` (always-false). exit 1, unsolved goals at proof (spec demands .ok true on .ok channel). = FAIL_TO_PASS reproduction for acquire.
- atk_2: prepatch bug (release) `let _ ← outcome; return false`. exit 1, unsolved goals. = FAIL_TO_PASS reproduction for release.
- atk_3: boundary swap (acquire) — `.wouldBlock => return true` instead of false. exit 1, unsolved goals (spec: .error .wouldBlock => .ok false).
- atk_4: control-flow-effect (acquire) — `catch _ => return false`, swallows .other instead of propagating `throw (.other c)`. exit 1, unsolved goals (spec propagates .error (.other c)).
- atk_5: ungrounded-oracle echo (acquire) — echoes spec match shape but maps `.error (.other _) => .ok false`. exit 1, unsolved goals (spec: .error (.other c) => .error (.other c)).
- atk_6: partial/wrong-channel (release) — `.error _ => .ok true`, turns propagated error into ok-true. exit 1, unsolved goals (spec: outcome.map => .error propagated unchanged).
Each given a generous proof attempt: `first | rfl | (match/rcases ... <;> rfl) | simp_all [impl, spec]`. All three tactics failed → genuine non-equivalence, not a weak proof.

POSITIVE CONTROL: pos_control.lean = byte copy of gold Solution.lean. `lean_verify.sh` exit 0, empty output (no errors/sorry). axcheck.lean (`#print axioms correct_acquire/correct_release`) => both 'does not depend on any axioms' (clean).

No verifying wrong impl ⇒ zero patches to run through run_resolve; the materialize+resolve obligation is vacuously discharged (nothing verified falsely).

REFINEMENT.md AUDIT: 7 legs, all R or I (acquire ops #1,#2,#5 = R; #3,#4 = I; release #1 = R, #2 = I). No A-consumed / no A-reference legs; meta.json axioms=[], deep_model_references=[], conf_skip=false — consistent. The lower-level primitive fcntl.flock is NOT axiomatized/deep-modeled: it is abstracted as the `outcome : Except FlockErr Unit` input argument (its two channels None/OSError ↦ .ok ()/.error). Since no A-legs exist, there is no callee-correspondence axiom hazard for this bundle; the A-leg focus of this reviewer is vacuous here and the R/I legs (G-CONF territory) are internally consistent. The two-constructor FlockErr (wouldBlock vs other) is the discriminating design that blocks error-collapsing wrong impls (atk_4/atk_5/atk_6 all rely on collapsing/misrouting the .other channel and all fail).

Verdict SOUND: ≥5 distinct same-spec wrong impls (6 run) all fail to verify; positive control verifies with clean axioms; spec is total-functional so verify⇒pointwise-equal-to-gold. No verify⇏correct gap exhibited.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13410 lean bundle. Modeled fns implementation_acquire/release ↔ patched posix locks.lock/unlock in django/core/files/locks.py. Spec is a fully-pinned equality: acquire {ok _→ok true, error wouldBlock→ok false, error (other c)→error (other c)}; release outcome.map(_→true). Verified: lean_verify exit 0, no sorry; #print axioms for correct_acquire/correct_release => 'does not depend on any axioms' — proofs genuine, not sorryAx-backed; same_spec(Solution.lean, prepatch_1/2)=True, spec region stable; ran the conformance shadow directly against the REAL patched lock/unlock over the full outcome domain (ok, wouldBlock, other errnos 1/9/13/9999) with a substituted flock — 0 disagreements. The real repo helpers themselves satisfy the spec, so the spec is not too strong; flock is abstracted as `outcome` (a legitimate modeling boundary, axioms=[], deep_model_references=[], conf_skip=false, justified in mapping.md/refinement.md). BlockingIOError-promoted errnos (EAGAIN/EWOULDBLOCK/EINPROGRESS/EALREADY) are correctly excluded from the .other channel since real lock would catch them. No input where the modeled function disagrees with the real callee. Verdict FAITHFUL — no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean minus impl+proof, verified via markers.spec_view; same_spec=True for both prepatches) is fully abstracted: it describes 'an advisory file-lock operation' via a 'lower-level locking primitive' with a two-channel (ok/error) result, and pins target behavior in problem_spec_acquire / problem_spec_release. It never names any patched symbol (lock, unlock, flock, fcntl), the file path django/core/files/locks.py, or the bug marker 'ret == 0'; modeled names acquire/release share no substring with lock/unlock; no bug->fix narration (no 'always returns False', no diff). Crucially, the public problem_statement is FAR more revealing than the spec view: it names the exact file, the posix/fcntl bug, the None/OSError semantics, the non-blocking (LOCKS_NB) motivation, AND embeds a complete proposed fix diff (try: flock(...); return True; except OSError: return False). The spec necessarily pins correct behavior (inherent to any spec, not leakage), and every fact it encodes is already disclosed more explicitly in the public statement. The .wouldBlock vs .other refinement is a modeling choice, not a gold-edit token beyond the public text. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
