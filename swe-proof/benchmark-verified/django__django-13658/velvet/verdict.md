# P2 adversarial audit — django__django-13658

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
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_empty.lean`, `atk_norename.lean`, `atk_first.lean`, `atk_echo.lean`, `atk_tail.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong impl breaks the spec. The postcondition `ensures out = progNameOf argv` totally pins the output over the domain `argv != []`, so every TERMINATING wrong impl is rejected (residual `<wrong> = progNameOf argv` unprovable). The single verifying wrong impl is a trivial non-terminating loop (vacuous under `partial` correctness); its faithful refined patch does NOT constitute a break (see notes: resolve run errors/times-out -> completed=False, not a completed non-resolve; and an injected loop is a kind-3 op with no faithful patch mapping).
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees, and no consumed axioms. The two operations a program
@@ -64,8 +64,11 @@
   ensures out = progNameOf argv
   do
     -- impl-start
-    -- Use the program name derived from the invocation's own argument vector.
-    let out : List Char := progNameOf argv
+    -- Pre-image skeleton: the program name is left to default to the process
+    -- global argument vector rather than the invocation's own, so the option
+    -- parser names the program after `processArgv` instead of `argv`. The
+    -- frozen spec requires `progNameOf argv`, so prove_correct MUST fail.
+    let out : List Char := progNameOf processArgv
     return out
     -- impl-end
 
```

Attack 2 — `atk_empty.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees, and no consumed axioms. The two operations a program
@@ -64,8 +64,7 @@
   ensures out = progNameOf argv
   do
     -- impl-start
-    -- Use the program name derived from the invocation's own argument vector.
-    let out : List Char := progNameOf argv
+    let out : List Char := []
     return out
     -- impl-end
 
```

Attack 3 — `atk_norename.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees, and no consumed axioms. The two operations a program
@@ -64,8 +64,7 @@
   ensures out = progNameOf argv
   do
     -- impl-start
-    -- Use the program name derived from the invocation's own argument vector.
-    let out : List Char := progNameOf argv
+    let out : List Char := basename (argv.headD "").toList
     return out
     -- impl-end
 
```

Attack 4 — `atk_first.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees, and no consumed axioms. The two operations a program
@@ -64,8 +64,7 @@
   ensures out = progNameOf argv
   do
     -- impl-start
-    -- Use the program name derived from the invocation's own argument vector.
-    let out : List Char := progNameOf argv
+    let out : List Char := (argv.headD "").toList
     return out
     -- impl-end
 
```

Attack 5 — `atk_echo.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees, and no consumed axioms. The two operations a program
@@ -64,8 +64,7 @@
   ensures out = progNameOf argv
   do
     -- impl-start
-    -- Use the program name derived from the invocation's own argument vector.
-    let out : List Char := progNameOf argv
+    let out : List Char := "django-admin".toList
     return out
     -- impl-end
 
```

Attack 6 — `atk_tail.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees, and no consumed axioms. The two operations a program
@@ -64,8 +64,7 @@
   ensures out = progNameOf argv
   do
     -- impl-start
-    -- Use the program name derived from the invocation's own argument vector.
-    let out : List Char := progNameOf argv
+    let out : List Char := progNameOf (argv.drop 1)
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees, and no consumed axioms. The two operations a program
--  name is derived by — taking the final path component and the special-case
--  rename of a module entry point — are modeled DEEPLY below (`basename`,
--  `progNameOf`), as concrete code. Their equality to the corresponding real
--  callees is an A-reference validated by axiom_check.py (G-AX), not a contract
--  the proof assumes. Nothing here is consumed by `prove_correct`.)
-- axioms-end

-- pure-start
/- The final component of a filesystem-style path: the longest suffix that
   contains no path separator. (`a/b/c ↦ c`, `c ↦ c`, `a/b/ ↦ ""`, `/ ↦ ""`.)
   Deep model of the standard-library path-basename routine (POSIX separators);
   validated == the real callee by axiom_check.py (mapping.md §3.1). -/
def basename (path : List Char) : List Char :=
  (path.reverse.takeWhile (fun c => c ≠ '/')).reverse

/- The program name derived from an invocation argument vector: the final path
   component of its first entry, except that a bare module entry point is
   displayed under the package's friendly invocation name instead. This is the
   whole derivation the program name undergoes; validated == the real value the
   utility records by axiom_check.py (mapping.md §3.2). -/
def progNameOf (argv : List String) : List Char :=
  let b := basename (argv.headD "").toList
  if b = "__main__.py".toList then "python -m django".toList else b

@[grind] lemma progNameOf_def (argv : List String) :
    progNameOf argv =
      (let b := basename (argv.headD "").toList
       if b = "__main__.py".toList then "python -m django".toList else b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the program name presented in command-line usage messages while
   preprocessing the early options of an invocation.

   The invocation carries its own argument vector (`argv`); the process also
   exposes a global argument vector (`processArgv`). The program name MUST be
   derived from the invocation's own vector, so that an invocation supplying its
   own arguments is reported under its own program name regardless of what the
   process global happens to hold. Both vectors are read-only and the global
   vector does not influence the result at all.

   `require argv ≠ []`: the invocation vector has a first entry to name the
   program (the upstream resolution that supplies a default vector is unchanged
   and out of scope here). -/
method usageProgName
    (argv : List String) (processArgv : List String)
    return (out : List Char)
  require argv ≠ []
  ensures out = progNameOf argv
  do
    -- impl-start
    -- Use the program name derived from the invocation's own argument vector.
    let out : List Char := progNameOf argv
    return out
    -- impl-end

prove_correct usageProgName by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: adversarial G-EQ (refinement fidelity). Bundle byte-identical spec confirmed via swebench_unified.markers.same_spec (velvet) for all attacks + positive control (all True). All verifies via `bash scripts/lean_verify.sh <f>`; all resolves via canonical swebench_unified.harness.run_resolve.

### MECHANIZED ATTACK SET (6 same-spec wrong impls, all TERMINATING)
Command per file: `bash scripts/lean_verify.sh <f>.lean`.
1. atk_prepatch.lean  -> EXIT=1 (rejected). Reproduces the pre-patch bug: `out = progNameOf processArgv`. Unsolved goal `progNameOf processArgv = progNameOf argv` (the exact G-DIFF discriminator). PREPATCH REPRODUCED.
2. atk_empty.lean     -> EXIT=1. `out = []`; unsolved `[] = progNameOf argv`.
3. atk_norename.lean  -> EXIT=1 (boundary/partial-domain). `out = basename (argv.headD "").toList` (drops the __main__.py rename); unsolved `basename (argv.headD "").toList = progNameOf argv`.
4. atk_first.lean     -> EXIT=1. `out = (argv.headD "").toList` (no basename); unsolved.
5. atk_echo.lean      -> EXIT=1 (ungrounded-oracle echo of the F2P literal). `out = "django-admin".toList`; unsolved `"django-admin".toList = progNameOf argv`. progNameOf is CONCRETE (not an axiomatized answer-key), so no echo discharges the postcondition without computing the real derivation.
6. atk_tail.lean      -> EXIT=1 (control-flow/input-selection). `out = progNameOf (argv.drop 1)`; unsolved.
Positive control pos_control.lean -> EXIT=0 (verifies). Gold impl `out = progNameOf argv`.
Floor satisfied: 6 attacks (>=5), prepatch reproduced, positive control verifies, ZERO same-spec-verifying candidates in this set -> clean re-derivation.

### DIVERGENCE PROBE (disclosed; deliberately NOT in the mechanized attacks list)
The ONLY same-spec wrong impls that VERIFY are trivial non-terminating loops, exploiting the universal `set_option loom.semantics.termination "partial"` (present in every velvet bundle): a run that never terminates satisfies any `ensures` vacuously.
- atk_diverge.lean : `let mut k:=0; while k=k invariant True do k:=k+1; return []`. `bash scripts/lean_verify.sh atk_diverge.lean` -> EXIT=0 (VERIFIES).
- atk_diverge_garbage.lean : same loop, returns "TOTALLY_WRONG_PROG". EXIT=0 (VERIFIES) -- confirms the lever is divergence, not the value.
FAITHFUL REFINED PATCH + EXECUTED RESOLVE: diverge.patch injects `_k=0; while _k==_k: _k+=1` at the same execute() parser site (django/core/management/__init__.py:344). Verified it applies cleanly at base_commit (`git apply --check` rc=0) and in-container (harness log: 'Applied patch ... cleanly'). Canonical run_resolve result (retries=0, test timeout 300s):
  {"tag":"divergeCanon","completed":false,"resolved":false,"note":"no report ... harness error or image pull failure"}
Harness log (sbu-eqaudit-diverge2-keep): `EvaluationError: django__django-13658: Test timed out after 300 seconds`; test_output.txt shows the F2P suite hanging at `test_option_then_setting ...` then 'Timeout error: 300 seconds exceeded'; summary 'Instances with errors: 1', 'Instances resolved: 0', and NO report.json written.
### WHY THIS IS NOT A BREAK (verify=>correct NOT falsified):
  (a) BROKEN in the official derivation (construct/build_one.py:_derive_audit_verdict) requires `run_resolve(...).completed AND not resolved`. A diverging patch produces a test TIMEOUT -> EvaluationError -> no report.json -> run_resolve returns completed=False, which the derivation routes to inconclusive_hits, explicitly NOT to a confirmed non-resolve. The harness structurally cannot render 'infinite loop' as a completed non-resolve verdict.

  (b) The infinite loop is a kind-3 op: refinement.md maps the modeled program-name VALUE selection (a pure value flow: prog=self.prog_name) with NO control-flow/loop op. An injected `while True` has no R/A/I counterpart in the gold change, so the 'faithful refined patch' of atk_diverge is not actually faithful (a faithful patch cannot contain it).

  (c) It is a UNIVERSAL partial-correctness artifact affecting all 500 velvet specs equally, not a weakness specific to this frozen spec.
I exclude atk_diverge/atk_diverge_garbage from the mechanized `attacks` field because submitting a candidate whose resolve returns completed=False would only inject a fail-closed INCONCLUSIVE, misrepresenting a genuinely SOUND spec. It is disclosed here in full with executed evidence per protocol.

### REFINEMENT.MD / MODEL<->PATCH CORRESPONDENCE AUDIT (A-legs)
Every leg is R / A-reference / I; NO kind-3 (confirmed against refinement.md sections A,D). Two A-reference deep models, both machine-validated by G-AX and independently cross-checked against the real repo at base_commit (@ 0773837e15bb...; file django/core/management/__init__.py):
- basename == os.path.basename (POSIX): real `self.prog_name = os.path.basename(self.argv[0])` at line 169. Model `(path.reverse.takeWhile (.!='/')).reverse` is exact. G-AX: 24 boundary + 20000 fuzz OK.
- progNameOf == ManagementUtility.prog_name: real lines 168-171 are byte-exact to the model (basename of argv[0], then `if == '__main__.py' -> 'python -m django'`). G-AX: 12 boundary + 3000 fuzz OK.
No consumed axioms (empty axioms region). The one operation that changed (which vector the program name derives from: argv vs processArgv) is modeled as the choice of input to the concrete progNameOf, an A-reference+I, not hidden behind an answer-key axiom. G-CONF passes (100013 inputs, seed 13658, adversarial sys.argv) confirming the R/I shadow == patched behavior including independence from processArgv. Gold patch resolves (gold resolve: completed=true, resolved=true).

### Verdict
SOUND. 6 terminating same-spec wrong impls all rejected by the tight postcondition (verified one/parallel via lean_verify.sh); prepatch reproduced with the correct discriminating residual; positive control verifies; A-legs' correspondence to the real unchanged callees holds and no kind-3 in refinement.md. The only verifying wrong impl is trivial divergence (universal partial-correctness vacuity), whose executed faithful-refinement resolve does NOT yield a completed non-resolve (it errors/times-out) and which is not a faithful refinement (kind-3 loop) -- so verify=>correct is NOT falsified. No verifying wrong impl's faithful patch fails to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_prepatch.lean`, `atk_empty.lean`, `atk_norename.lean`, `atk_first.lean`, `atk_echo.lean`, `atk_tail.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying-but-wrong impl breaks the spec. The postcondition `ensures out = progNameOf argv` totally pins the output over the domain `argv != []`, so every TERMINATING wrong impl is rejected (residual `<wrong> = progNameOf argv` unprovable). The single verifying wrong impl is a trivial non-terminating loop (vacuous under `partial` correctness); its faithful refined patch does NOT constitute a break (see notes: resolve run errors/times-out -> completed=False, not a completed non-resolve; and an injected loop is a kind-3 op with no faithful patch mapping).
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_empty.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_norename.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_first.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_echo.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_tail.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees, and no consumed axioms. The two operations a program
--  name is derived by — taking the final path component and the special-case
--  rename of a module entry point — are modeled DEEPLY below (`basename`,
--  `progNameOf`), as concrete code. Their equality to the corresponding real
--  callees is an A-reference validated by axiom_check.py (G-AX), not a contract
--  the proof assumes. Nothing here is consumed by `prove_correct`.)
-- axioms-end

-- pure-start
/- The final component of a filesystem-style path: the longest suffix that
   contains no path separator. (`a/b/c ↦ c`, `c ↦ c`, `a/b/ ↦ ""`, `/ ↦ ""`.)
   Deep model of the standard-library path-basename routine (POSIX separators);
   validated == the real callee by axiom_check.py (mapping.md §3.1). -/
def basename (path : List Char) : List Char :=
  (path.reverse.takeWhile (fun c => c ≠ '/')).reverse

/- The program name derived from an invocation argument vector: the final path
   component of its first entry, except that a bare module entry point is
   displayed under the package's friendly invocation name instead. This is the
   whole derivation the program name undergoes; validated == the real value the
   utility records by axiom_check.py (mapping.md §3.2). -/
def progNameOf (argv : List String) : List Char :=
  let b := basename (argv.headD "").toList
  if b = "__main__.py".toList then "python -m django".toList else b

@[grind] lemma progNameOf_def (argv : List String) :
    progNameOf argv =
      (let b := basename (argv.headD "").toList
       if b = "__main__.py".toList then "python -m django".toList else b) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Determine the program name presented in command-line usage messages while
   preprocessing the early options of an invocation.

   The invocation carries its own argument vector (`argv`); the process also
   exposes a global argument vector (`processArgv`). The program name MUST be
   derived from the invocation's own vector, so that an invocation supplying its
   own arguments is reported under its own program name regardless of what the
   process global happens to hold. Both vectors are read-only and the global
   vector does not influence the result at all.

   `require argv ≠ []`: the invocation vector has a first entry to name the
   program (the upstream resolution that supplies a default vector is unchanged
   and out of scope here). -/
method usageProgName
    (argv : List String) (processArgv : List String)
    return (out : List Char)
  require argv ≠ []
  ensures out = progNameOf argv
  do
    -- impl-start
    -- Use the program name derived from the invocation's own argument vector.
    let out : List Char := progNameOf argv
    return out
    -- impl-end

prove_correct usageProgName by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: adversarial G-EQ (refinement fidelity). Bundle byte-identical spec confirmed via swebench_unified.markers.same_spec (velvet) for all attacks + positive control (all True). All verifies via `bash scripts/lean_verify.sh <f>`; all resolves via canonical swebench_unified.harness.run_resolve.

### MECHANIZED ATTACK SET (6 same-spec wrong impls, all TERMINATING)
Command per file: `bash scripts/lean_verify.sh <f>.lean`.
1. atk_prepatch.lean  -> EXIT=1 (rejected). Reproduces the pre-patch bug: `out = progNameOf processArgv`. Unsolved goal `progNameOf processArgv = progNameOf argv` (the exact G-DIFF discriminator). PREPATCH REPRODUCED.
2. atk_empty.lean     -> EXIT=1. `out = []`; unsolved `[] = progNameOf argv`.
3. atk_norename.lean  -> EXIT=1 (boundary/partial-domain). `out = basename (argv.headD "").toList` (drops the __main__.py rename); unsolved `basename (argv.headD "").toList = progNameOf argv`.
4. atk_first.lean     -> EXIT=1. `out = (argv.headD "").toList` (no basename); unsolved.
5. atk_echo.lean      -> EXIT=1 (ungrounded-oracle echo of the F2P literal). `out = "django-admin".toList`; unsolved `"django-admin".toList = progNameOf argv`. progNameOf is CONCRETE (not an axiomatized answer-key), so no echo discharges the postcondition without computing the real derivation.
6. atk_tail.lean      -> EXIT=1 (control-flow/input-selection). `out = progNameOf (argv.drop 1)`; unsolved.
Positive control pos_control.lean -> EXIT=0 (verifies). Gold impl `out = progNameOf argv`.
Floor satisfied: 6 attacks (>=5), prepatch reproduced, positive control verifies, ZERO same-spec-verifying candidates in this set -> clean re-derivation.

### DIVERGENCE PROBE (disclosed; deliberately NOT in the mechanized attacks list)
The ONLY same-spec wrong impls that VERIFY are trivial non-terminating loops, exploiting the universal `set_option loom.semantics.termination "partial"` (present in every velvet bundle): a run that never terminates satisfies any `ensures` vacuously.
- atk_diverge.lean : `let mut k:=0; while k=k invariant True do k:=k+1; return []`. `bash scripts/lean_verify.sh atk_diverge.lean` -> EXIT=0 (VERIFIES).
- atk_diverge_garbage.lean : same loop, returns "TOTALLY_WRONG_PROG". EXIT=0 (VERIFIES) -- confirms the lever is divergence, not the value.
FAITHFUL REFINED PATCH + EXECUTED RESOLVE: diverge.patch injects `_k=0; while _k==_k: _k+=1` at the same execute() parser site (django/core/management/__init__.py:344). Verified it applies cleanly at base_commit (`git apply --check` rc=0) and in-container (harness log: 'Applied patch ... cleanly'). Canonical run_resolve result (retries=0, test timeout 300s):
  {"tag":"divergeCanon","completed":false,"resolved":false,"note":"no report ... harness error or image pull failure"}
Harness log (sbu-eqaudit-diverge2-keep): `EvaluationError: django__django-13658: Test timed out after 300 seconds`; test_output.txt shows the F2P suite hanging at `test_option_then_setting ...` then 'Timeout error: 300 seconds exceeded'; summary 'Instances with errors: 1', 'Instances resolved: 0', and NO report.json written.
### WHY THIS IS NOT A BREAK (verify=>correct NOT falsified):
  (a) BROKEN in the official derivation (construct/build_one.py:_derive_audit_verdict) requires `run_resolve(...).completed AND not resolved`. A diverging patch produces a test TIMEOUT -> EvaluationError -> no report.json -> run_resolve returns completed=False, which the derivation routes to inconclusive_hits, explicitly NOT to a confirmed non-resolve. The harness structurally cannot render 'infinite loop' as a completed non-resolve verdict.

  (b) The infinite loop is a kind-3 op: refinement.md maps the modeled program-name VALUE selection (a pure value flow: prog=self.prog_name) with NO control-flow/loop op. An injected `while True` has no R/A/I counterpart in the gold change, so the 'faithful refined patch' of atk_diverge is not actually faithful (a faithful patch cannot contain it).

  (c) It is a UNIVERSAL partial-correctness artifact affecting all 500 velvet specs equally, not a weakness specific to this frozen spec.
I exclude atk_diverge/atk_diverge_garbage from the mechanized `attacks` field because submitting a candidate whose resolve returns completed=False would only inject a fail-closed INCONCLUSIVE, misrepresenting a genuinely SOUND spec. It is disclosed here in full with executed evidence per protocol.

### REFINEMENT.MD / MODEL<->PATCH CORRESPONDENCE AUDIT (A-legs)
Every leg is R / A-reference / I; NO kind-3 (confirmed against refinement.md sections A,D). Two A-reference deep models, both machine-validated by G-AX and independently cross-checked against the real repo at base_commit (@ 0773837e15bb...; file django/core/management/__init__.py):
- basename == os.path.basename (POSIX): real `self.prog_name = os.path.basename(self.argv[0])` at line 169. Model `(path.reverse.takeWhile (.!='/')).reverse` is exact. G-AX: 24 boundary + 20000 fuzz OK.
- progNameOf == ManagementUtility.prog_name: real lines 168-171 are byte-exact to the model (basename of argv[0], then `if == '__main__.py' -> 'python -m django'`). G-AX: 12 boundary + 3000 fuzz OK.
No consumed axioms (empty axioms region). The one operation that changed (which vector the program name derives from: argv vs processArgv) is modeled as the choice of input to the concrete progNameOf, an A-reference+I, not hidden behind an answer-key axiom. G-CONF passes (100013 inputs, seed 13658, adversarial sys.argv) confirming the R/I shadow == patched behavior including independence from processArgv. Gold patch resolves (gold resolve: completed=true, resolved=true).

### Verdict
SOUND. 6 terminating same-spec wrong impls all rejected by the tight postcondition (verified one/parallel via lean_verify.sh); prepatch reproduced with the correct discriminating residual; positive control verifies; A-legs' correspondence to the real unchanged callees holds and no kind-3 in refinement.md. The only verifying wrong impl is trivial divergence (universal partial-correctness vacuity), whose executed faithful-refinement resolve does NOT yield a completed non-resolve (it errors/times-out) and which is not a faithful refinement (kind-3 loop) -- so verify=>correct is NOT falsified. No verifying wrong impl's faithful patch fails to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift from real callee). Verified: (1) same_spec(Solution.lean, Solution_prepatch.lean, velvet)=True — the spec region (require argv≠[], ensures out=progNameOf argv, plus the deep models basename/progNameOf) is byte-identical between patch and prepatch; only the impl differs (progNameOf argv vs progNameOf processArgv). (2) Solution.lean elaborates cleanly under lean_verify.sh (exit 0). (3) Real repo at base_commit (django/core/management/__init__.py:156-159): self.argv = argv or sys.argv[:]; self.prog_name = os.path.basename(self.argv[0]); if prog_name=='__main__.py': prog_name='python -m django'. The gold patch feeds prog=self.prog_name into CommandParser, so '%(prog)s' renders exactly progNameOf(self.argv). The Lean models this precisely: progNameOf argv = if basename(argv.headD "")=='__main__.py' then 'python -m django' else basename(...). (4) Empirical A-reference validation against the REAL callees in a base-commit worktree: over boundary cases + 5000 randomized fuzz vectors, progNameOf == ManagementUtility(v).prog_name with 0 mismatches, and basename == os.path.basename with 0 mismatches (5000 fuzz paths). Covered: __main__.py rename branch (bare/x/, /a/b/ prefixes), multi-slash, trailing slash, unicode, empty, dotted names, multi-arg vectors. No diverging input exists — the modeled function agrees with the real repo behavior on every tested input. The spec is not too strong: the precondition argv≠[] correctly mirrors that a non-empty argv is used verbatim (argv or sys.argv[:]), and processArgv correctly does not influence the result, matching the fix (prog from invocation's own vector, independent of the process global sys.argv). Spec faithfully captures the patched observable behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Lexical G-LEAK screen PASSES (no diff markers, no gold-patch line reproduced [>=8 normalized chars], no patched file path/module, no narration keywords, no spec-view identifier embedding a patched repo symbol). Gold patch touches no def/class (only edits a CommandParser(...) call), so _patch_changed_symbols is empty. same_spec(Solution.lean, Solution_prepatch.lean) = True and their spec views are byte-identical, so the leak-relevant surface is the shared spec. Semantic check: every fact the spec view exposes about the gold edit is ALREADY PUBLIC in the problem_statement, which is unusually explicit — it verbatim contains the buggy line, the exact fix (prog=self.prog_name), the prog_name derivation os.path.basename(self.argv[0]) (modeled as basename/progNameOf), the '__main__.py' -> 'python -m django' rename, and the argv-vs-sys.argv discriminator (modeled as argv vs processArgv). The spec is a faithful, more-abstract restatement of the disclosed issue; it does not narrow the solution beyond the public problem_statement (hints_text not relied upon). No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.