# P2 adversarial audit — django__django-10973

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_nodbname.lean`, `atk2_pwboundary.lean`, `atk3_order.lean`, `atk4_flag.lean`, `atk5_inverted.lean`, `atk6_pwwrong.lean`, `atk7_conddbname.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_equiv.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_nodbname.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,7 @@
     args := args ++ ["-h", host]
   if port ≠ "" then
     args := args ++ ["-p", port]
-  args := args ++ [dbname]
+  -- BUG: forget to append dbname
   let mut passwordEnv : Option String := none
   if passwd ≠ "" then
     passwordEnv := some passwd
```

Attack 2 — `atk2_pwboundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,9 +51,8 @@
   if port ≠ "" then
     args := args ++ ["-p", port]
   args := args ++ [dbname]
-  let mut passwordEnv : Option String := none
-  if passwd ≠ "" then
-    passwordEnv := some passwd
+  -- BUG: always provision password, even when empty
+  let passwordEnv : Option String := some passwd
   return (args, passwordEnv)
 -- impl-end
 
```

Attack 3 — `atk3_order.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,10 +44,10 @@
     (host port dbname user passwd : String) :
     List String × Option String := Id.run do
   let mut args := ["psql"]
+  if host ≠ "" then
+    args := args ++ ["-h", host]
   if user ≠ "" then
     args := args ++ ["-U", user]
-  if host ≠ "" then
-    args := args ++ ["-h", host]
   if port ≠ "" then
     args := args ++ ["-p", port]
   args := args ++ [dbname]
```

Attack 4 — `atk4_flag.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,7 +45,7 @@
     List String × Option String := Id.run do
   let mut args := ["psql"]
   if user ≠ "" then
-    args := args ++ ["-U", user]
+    args := args ++ ["-u", user]
   if host ≠ "" then
     args := args ++ ["-h", host]
   if port ≠ "" then
```

Attack 5 — `atk5_inverted.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,7 @@
     (host port dbname user passwd : String) :
     List String × Option String := Id.run do
   let mut args := ["psql"]
-  if user ≠ "" then
+  if user = "" then
     args := args ++ ["-U", user]
   if host ≠ "" then
     args := args ++ ["-h", host]
```

Attack 6 — `atk6_pwwrong.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,9 +51,10 @@
   if port ≠ "" then
     args := args ++ ["-p", port]
   args := args ++ [dbname]
+  -- BUG: hand the child the dbname instead of the password
   let mut passwordEnv : Option String := none
   if passwd ≠ "" then
-    passwordEnv := some passwd
+    passwordEnv := some dbname
   return (args, passwordEnv)
 -- impl-end
 
```

Attack 7 — `atk7_conddbname.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,7 +50,8 @@
     args := args ++ ["-h", host]
   if port ≠ "" then
     args := args ++ ["-p", port]
-  args := args ++ [dbname]
+  if host ≠ "" then
+    args := args ++ [dbname]
   let mut passwordEnv : Option String := none
   if passwd ≠ "" then
     passwordEnv := some passwd
```

Attack 8 — `atk8_equiv.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -43,17 +43,11 @@
 def implementation_dbShellCommand
     (host port dbname user passwd : String) :
     List String × Option String := Id.run do
-  let mut args := ["psql"]
-  if user ≠ "" then
-    args := args ++ ["-U", user]
-  if host ≠ "" then
-    args := args ++ ["-h", host]
-  if port ≠ "" then
-    args := args ++ ["-p", port]
-  args := args ++ [dbname]
-  let mut passwordEnv : Option String := none
-  if passwd ≠ "" then
-    passwordEnv := some passwd
+  let userPart := if user ≠ "" then ["-U", user] else []
+  let hostPart := if host ≠ "" then ["-h", host] else []
+  let portPart := if port ≠ "" then ["-p", port] else []
+  let args := ["psql"] ++ userPart ++ hostPart ++ portPart ++ [dbname]
+  let passwordEnv : Option String := if passwd = "" then none else some passwd
   return (args, passwordEnv)
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Both observable outputs —
-- the client command-line vector and the password handed to the child process —
-- are produced by literal-driven list assembly and a single conditional, so they
-- are modeled concretely rather than abstracted behind an axiom. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No shared functional helper is required; the postcondition states the two
-- output components structurally in terms of the inputs.
-- pure-end

-- post-conditions-start
/-- The shell invocation is described by two components.

The first is the argument vector for the client program: it always begins with
the client executable name, then — for each of the user, host, and port
connection parameters that is non-empty — appends that parameter preceded by its
corresponding option flag, in that exact order, and finally appends the database
name unconditionally.

The second is the password made available to the child process: it is the
connection password exactly when a password is supplied (non-empty), and is
absent otherwise. Both components are pinned to the inputs; nothing about the
argument vector depends on the password. -/
def problem_spec_dbShellCommand
    (host port dbname user passwd : String)
    (result : List String × Option String) : Prop :=
  result.1 =
      ["psql"]
        ++ (if user ≠ "" then ["-U", user] else [])
        ++ (if host ≠ "" then ["-h", host] else [])
        ++ (if port ≠ "" then ["-p", port] else [])
        ++ [dbname]
  ∧ result.2 = (if passwd = "" then none else some passwd)
-- post-conditions-end

-- impl-start
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)
-- impl-end

-- proof-start
theorem correct_dbShellCommand :
    ∀ (host port dbname user passwd : String),
    problem_spec_dbShellCommand host port dbname user passwd
      (implementation_dbShellCommand host port dbname user passwd) := by
  intro host port dbname user passwd
  unfold problem_spec_dbShellCommand implementation_dbShellCommand
  refine ⟨?_, ?_⟩ <;>
    simp only [Id.run, ne_eq] <;>
    by_cases hu : user = "" <;> by_cases hh : host = "" <;>
      by_cases hp : port = "" <;> by_cases hpw : passwd = "" <;>
      simp only [hu, hh, hp, hpw, not_true, not_false_iff,
        if_neg, if_pos] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_dbShellCommand is a conjunction of TWO exact pointwise equalities that totally determine the output tuple as a function of the five String inputs: result.1 = ["psql"] ++ (if user≠"" then [-U,user]) ++ (if host≠"" then [-h,host]) ++ (if port≠"" then [-p,port]) ++ [dbname]  AND  result.2 = (if passwd="" then none else some passwd). No existential/inequality/under-specified slack. Axioms region is EMPTY (comment-only; verified no `axiom`/`opaque` decl, #print axioms shows only [propext, Quot.sound]). refinement.md legs are all I (rows 1,5,7) or R (rows 2,3,4,6) — no A-consumed, no A-reference, no kind-3 changed-inexpressible op — so the A-leg attack surface is empty by construction; the discriminating clause (row 6, component .2) matches the real post-fix callee (env PGPASSWORD set iff passwd truthy), documented via mapping.md scoping + conformance_check.py (120008 inputs, 0 disagreements).

### PROTOCOL EXECUTED (project root; verifier: bash scripts/lean_verify.sh <file>):
- same_spec: True for ALL 9 files (atk_pos + atk1..atk8) via swebench_unified.markers.same_spec on lean backend.
- Verifications run concurrently in batches of 4 background jobs.
- POSITIVE CONTROL atk_pos.lean (= gold impl): exit 0; #print axioms => [propext, Quot.sound], no sorryAx.
- PREPATCH REPRODUCED atk_prepatch.lean (password side-channel, .2 always none) with the GOLD proof tactic block (NOT sorry): exit 1, `rfl` failed at .2 conjunct — G-DIFF confirmed (buggy prepatch cannot close the frozen spec).
- SEVEN genuinely-divergent same-spec wrong impls ALL FAIL to close (exit 1, real `rfl` errors, not timeouts): atk1_nodbname (drop unconditional dbname append), atk2_pwboundary (some passwd even when empty — boundary), atk3_order (swap -U/-h order), atk4_flag (-U -> -u wrong literal), atk5_inverted (append -U when user="" — inverted control flow), atk6_pwwrong (hand child dbname instead of passwd — ungrounded oracle echo), atk7_conddbname (append dbname only if host≠"" — partial-domain). Each fails because the spec's two exact equalities pin the output extensionally; any divergence breaks `rfl`.
- ONLY closing non-gold impl: atk8_equiv.lean — an extensionally EQUAL restructuring (let-bindings + single ++ chain, if-then-else for the option) producing byte-identical output on every input. exit 0; #print axioms => [propext], clean, no sorryAx. Per protocol step 2 its faithful refined patch was MATERIALIZED (= the gold patch.diff, since it is behaviorally identical) and RUN through the official harness: run_resolve("django__django-10973", <patch>) => RESOLVED: True, completed: True, note 'resolved', attempts 1. It resolves, so it is NOT a counterexample — it is a gold-equivalent echo, which (per current policy) is a strength, not a weakness.

CONCLUSION: The spec fully pins (args, PGPASSWORD). Every closing impl is extensionally equal to gold and therefore emits byte-identical observable outputs the F2P harness probes, so its patch necessarily resolves (verified for the one non-gold closing impl). No same-spec impl closes with clean axioms yet fails to resolve. verify => correct holds. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_nodbname.lean`, `atk2_pwboundary.lean`, `atk3_order.lean`, `atk4_flag.lean`, `atk5_inverted.lean`, `atk6_pwwrong.lean`, `atk7_conddbname.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk8_equiv.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_nodbname.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_pwboundary.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_order.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_flag.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_inverted.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_pwwrong.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_conddbname.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8_equiv.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. Both observable outputs —
-- the client command-line vector and the password handed to the child process —
-- are produced by literal-driven list assembly and a single conditional, so they
-- are modeled concretely rather than abstracted behind an axiom. The proof agent
-- may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- No shared functional helper is required; the postcondition states the two
-- output components structurally in terms of the inputs.
-- pure-end

-- post-conditions-start
/-- The shell invocation is described by two components.

The first is the argument vector for the client program: it always begins with
the client executable name, then — for each of the user, host, and port
connection parameters that is non-empty — appends that parameter preceded by its
corresponding option flag, in that exact order, and finally appends the database
name unconditionally.

The second is the password made available to the child process: it is the
connection password exactly when a password is supplied (non-empty), and is
absent otherwise. Both components are pinned to the inputs; nothing about the
argument vector depends on the password. -/
def problem_spec_dbShellCommand
    (host port dbname user passwd : String)
    (result : List String × Option String) : Prop :=
  result.1 =
      ["psql"]
        ++ (if user ≠ "" then ["-U", user] else [])
        ++ (if host ≠ "" then ["-h", host] else [])
        ++ (if port ≠ "" then ["-p", port] else [])
        ++ [dbname]
  ∧ result.2 = (if passwd = "" then none else some passwd)
-- post-conditions-end

-- impl-start
def implementation_dbShellCommand
    (host port dbname user passwd : String) :
    List String × Option String := Id.run do
  let mut args := ["psql"]
  if user ≠ "" then
    args := args ++ ["-U", user]
  if host ≠ "" then
    args := args ++ ["-h", host]
  if port ≠ "" then
    args := args ++ ["-p", port]
  args := args ++ [dbname]
  let mut passwordEnv : Option String := none
  if passwd ≠ "" then
    passwordEnv := some passwd
  return (args, passwordEnv)
-- impl-end

-- proof-start
theorem correct_dbShellCommand :
    ∀ (host port dbname user passwd : String),
    problem_spec_dbShellCommand host port dbname user passwd
      (implementation_dbShellCommand host port dbname user passwd) := by
  intro host port dbname user passwd
  unfold problem_spec_dbShellCommand implementation_dbShellCommand
  refine ⟨?_, ?_⟩ <;>
    simp only [Id.run, ne_eq] <;>
    by_cases hu : user = "" <;> by_cases hh : host = "" <;>
      by_cases hp : port = "" <;> by_cases hpw : passwd = "" <;>
      simp only [hu, hh, hp, hpw, not_true, not_false_iff,
        if_neg, if_pos] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_dbShellCommand is a conjunction of TWO exact pointwise equalities that totally determine the output tuple as a function of the five String inputs: result.1 = ["psql"] ++ (if user≠"" then [-U,user]) ++ (if host≠"" then [-h,host]) ++ (if port≠"" then [-p,port]) ++ [dbname]  AND  result.2 = (if passwd="" then none else some passwd). No existential/inequality/under-specified slack. Axioms region is EMPTY (comment-only; verified no `axiom`/`opaque` decl, #print axioms shows only [propext, Quot.sound]). refinement.md legs are all I (rows 1,5,7) or R (rows 2,3,4,6) — no A-consumed, no A-reference, no kind-3 changed-inexpressible op — so the A-leg attack surface is empty by construction; the discriminating clause (row 6, component .2) matches the real post-fix callee (env PGPASSWORD set iff passwd truthy), documented via mapping.md scoping + conformance_check.py (120008 inputs, 0 disagreements).

### PROTOCOL EXECUTED (project root; verifier: bash scripts/lean_verify.sh <file>):
- same_spec: True for ALL 9 files (atk_pos + atk1..atk8) via swebench_unified.markers.same_spec on lean backend.
- Verifications run concurrently in batches of 4 background jobs.
- POSITIVE CONTROL atk_pos.lean (= gold impl): exit 0; #print axioms => [propext, Quot.sound], no sorryAx.
- PREPATCH REPRODUCED atk_prepatch.lean (password side-channel, .2 always none) with the GOLD proof tactic block (NOT sorry): exit 1, `rfl` failed at .2 conjunct — G-DIFF confirmed (buggy prepatch cannot close the frozen spec).
- SEVEN genuinely-divergent same-spec wrong impls ALL FAIL to close (exit 1, real `rfl` errors, not timeouts): atk1_nodbname (drop unconditional dbname append), atk2_pwboundary (some passwd even when empty — boundary), atk3_order (swap -U/-h order), atk4_flag (-U -> -u wrong literal), atk5_inverted (append -U when user="" — inverted control flow), atk6_pwwrong (hand child dbname instead of passwd — ungrounded oracle echo), atk7_conddbname (append dbname only if host≠"" — partial-domain). Each fails because the spec's two exact equalities pin the output extensionally; any divergence breaks `rfl`.
- ONLY closing non-gold impl: atk8_equiv.lean — an extensionally EQUAL restructuring (let-bindings + single ++ chain, if-then-else for the option) producing byte-identical output on every input. exit 0; #print axioms => [propext], clean, no sorryAx. Per protocol step 2 its faithful refined patch was MATERIALIZED (= the gold patch.diff, since it is behaviorally identical) and RUN through the official harness: run_resolve("django__django-10973", <patch>) => RESOLVED: True, completed: True, note 'resolved', attempts 1. It resolves, so it is NOT a counterexample — it is a gold-equivalent echo, which (per current policy) is a strength, not a weakness.

CONCLUSION: The spec fully pins (args, PGPASSWORD). Every closing impl is extensionally equal to gold and therefore emits byte-identical observable outputs the F2P harness probes, so its patch necessarily resolves (verified for the one non-gold closing impl). No same-spec impl closes with clean axioms yet fails to resolve. verify => correct holds. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical: lean_verify Solution.lean exit 0; #print axioms correct_dbShellCommand => [propext, Quot.sound] (no sorryAx, proof genuine); same_spec(Solution, Solution_prepatch, LeanBackend)=True (spec region byte-identical). Faithfulness: independently reconstructed the post-patch runshell_db and ran a 200k-input differential (seed 10973) vs the R/I shadow => 0 disagreements. Additionally probed inputs the bundle fuzzer skips (dbname allow_empty=False): empty dbname, all-empty, port-only, host+user only => all MATCH (real code appends dbname unconditionally, spec's ++[dbname] mirrors it). Argument-vector assembly is UNCHANGED by the gold fix; password slot is set iff passwd truthy, matching spec's `if passwd="" then none else some passwd`. The lone ambient-PGPASSWORD divergence is explicitly scoped out in mapping.md and matches the FAIL_TO_PASS harness (test_nopass expects None under clean env; mock and conformance_check both clear ambient PGPASSWORD). The modeled function does not overclaim: within the observable domain the F2P tests check ((subprocess_args, env.get('PGPASSWORD'))), it agrees with the real callee on all inputs. Spec is neither too strong nor drifted.

Counterexample / evidence:

```
shadow=(['psql','-U','u','-h','h','-p','444','db'], None) vs real=(..., 'AMBIENT') only when ambient PGPASSWORD is preset. Under a clean environment (the F2P harness condition, which conformance_check.py enforces via os.environ.pop('PGPASSWORD')), the two agree exactly.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (imports + axiom/pure comment stubs + post-conditions region: docstring + problem_spec_dbShellCommand) verified via markers.spec_view. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Mechanical leakage.screen over the spec view against gold patch + public problem_statement: passed, no hard_failures, no warnings. Lean compiles (exit 0), axioms clean per meta (G-VERIFY). 

Leakage judgment vs public problem_statement ONLY (not hints_text): The public problem_statement already discloses the gold approach explicitly and MORE concretely: 'Use subprocess.run and PGPASSWORD for client in postgres backend ... allows you to pass a custom environment for the subprocess ... to set PGPASSWORD.' The gold diff's essence = drop the .pgpass temp-file mechanism (_escape_pgpass / NamedTemporaryFile / PGPASSFILE) and put the password in the subprocess env via subprocess.run(env=...).

The spec view is strictly MORE abstract than the problem_statement. It exposes only two behavioral clauses: (1) result.1 = the psql argument vector built from user/host/port/dbname -- UNCHANGED by the gold patch, so not a discriminator/leak; and (2) result.2 = (if passwd = "" then none else some passwd), described abstractly as 'the password made available to the child process'. The spec never names PGPASSWORD, environment variables, subprocess.run, .pgpass, temp files, NamedTemporaryFile, or the removed _escape_pgpass helper -- i.e. none of the gold-diff-specific mechanism appears. The visible input->output contract (password present in child's password-channel iff non-empty) is the correct behavioral spec and reveals nothing about the gold edit beyond what the public problem_statement already states. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
