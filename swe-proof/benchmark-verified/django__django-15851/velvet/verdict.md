# P2 adversarial audit — django__django-15851

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verified; therefore no faithful refined patch needed to be materialized/resolve-run. The spec is an exact output-list equality that admits no verifying-but-wrong impl among the attempted distinct failure modes.
```

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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,12 +55,9 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
     let mut args := leading
+    args := args ++ dbnameToken dbname
     args := args ++ parameters
-    args := args ++ dbnameToken dbname
     return args
     -- impl-end
 
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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,11 +55,7 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
     let mut args := leading
-    args := args ++ parameters
     args := args ++ dbnameToken dbname
     return args
     -- impl-end
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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,12 +55,8 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
     let mut args := leading
     args := args ++ parameters
-    args := args ++ dbnameToken dbname
     return args
     -- impl-end
 
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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,12 +55,13 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
+    -- partial-domain: when dbname absent (token empty) result is correct;
+    -- when present, appends the token BEFORE parameters (wrong order).
     let mut args := leading
-    args := args ++ parameters
-    args := args ++ dbnameToken dbname
+    if (dbnameToken dbname).isEmpty then
+      args := args ++ parameters ++ dbnameToken dbname
+    else
+      args := args ++ dbnameToken dbname ++ parameters
     return args
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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,12 +55,12 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
+    -- control-flow: if parameters empty, correct; else appends params after token
     let mut args := leading
-    args := args ++ parameters
-    args := args ++ dbnameToken dbname
+    if parameters.isEmpty then
+      args := args ++ parameters ++ dbnameToken dbname
+    else
+      args := args ++ dbnameToken dbname ++ parameters
     return args
     -- impl-end
 
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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,11 +55,8 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
     let mut args := leading
-    args := args ++ parameters
+    args := args ++ parameters.reverse
     args := args ++ dbnameToken dbname
     return args
     -- impl-end
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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,12 +55,9 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
     let mut args := leading
     args := args ++ parameters
-    args := args ++ dbnameToken dbname
+    args := args ++ dbnameToken dbname ++ dbnameToken dbname
     return args
     -- impl-end
 
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
 -- (No axiomatized callees. Assembling the command-line argument vector reads
@@ -55,13 +55,7 @@
   ensures args = builtArgs leading dbname parameters
   do
     -- impl-start
-    -- Start from the leading segment, append the caller's extra arguments,
-    -- then append the optional database-name token last. The extra arguments
-    -- are added before the database name, leaving the database name at the end.
-    let mut args := leading
-    args := args ++ parameters
-    args := args ++ dbnameToken dbname
-    return args
+    return leading
     -- impl-end
 
 prove_correct buildShellArgs by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Assembling the command-line argument vector reads
--  three already-available pieces — the leading segment built from the
--  connection settings, an optional database-name token, and the list of
--  caller-supplied extra arguments — and concatenates them. Concatenation and
--  the optional token are modeled directly (List `++` and `Option.toList`); no
--  unchanged callee's contract is consumed and nothing foreign is deep-modeled,
--  so there is nothing to axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The trailing token that names the target database, if one is named at all:
   a singleton holding that name when present, and nothing otherwise. This is
   the optional element that may or may not extend the argument vector. -/
def dbnameToken (dbname : Option String) : List String := dbname.toList

/- The complete command-line argument vector. It begins with the leading
   segment (the executable together with the connection options derived from the
   settings), is then extended by the caller-supplied extra arguments, and ends
   with the optional database-name token. The extra arguments therefore precede
   the database name in the vector; the database name, when present, is last. -/
def builtArgs (leading : List String) (dbname : Option String)
    (parameters : List String) : List String :=
  leading ++ parameters ++ dbnameToken dbname
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the command-line argument vector for invoking the database shell.

   `leading` is the leading segment already built from the connection settings
   (the executable name followed by whatever connection-option flags the
   settings call for); it is read-only here — this step neither inspects nor
   rewrites it, only builds upon it. `dbname` is the optional name of the target
   database: present as `some` when a database is named, `none` when none is.
   `parameters` are the extra arguments the caller passes through to the shell.

   The assembled vector places the caller-supplied extra arguments AFTER the
   leading segment and BEFORE the optional database-name token, so that the
   database name — when present — is the final element of the vector. -/
method buildShellArgs (leading : List String) (dbname : Option String)
    (parameters : List String) return (args : List String)
  ensures args = builtArgs leading dbname parameters
  do
    -- impl-start
    -- correct but structured differently: build the tail (params ++ token) first
    let tail := parameters ++ dbnameToken dbname
    let args := leading ++ tail
    return args
    -- impl-end

prove_correct buildShellArgs by
  loom_solve
  simp_all [builtArgs, dbnameToken]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec verified True for all 9 files (axioms/pure/pre/post byte-identical; only impl region edited). Verification via `bash scripts/lean_verify.sh <file>` under venv. Attacks run concurrently in background batches of 4.

### RESULTS (exit code from lean_verify wrapper + residual goal):
- pos_control (correct, restructured: tail := parameters ++ dbnameToken dbname; leading ++ tail): VERIFY exit 0 -> spec non-vacuous.
- atk_1 dbname-token before params (= PREPATCH order-swap bug, re-encoded): exit 1, goal `dbname.toList ++ parameters = parameters ++ dbname.toList`. Prepatch reproduced.
- atk_2 drop parameters (partial-content): exit 1, goal `parameters = []`.
- atk_3 drop dbname token: exit 1, goal `dbname = none`.
- atk_4 partial-domain (correct when token empty; token-before-params when dbname present, gated on (dbnameToken dbname).isEmpty): exit 1, goal `leading ++ dbnameToken dbname ++ parameters = builtArgs ...` in the token-present branch.
- atk_5 control-flow-effect (if parameters.isEmpty then correct else token-before-params): exit 1, goal `leading ++ dbnameToken dbname ++ parameters = builtArgs ...` in non-empty branch.
- atk_6 parameters.reverse (content mutation): exit 1, goal `parameters.reverse = parameters`.
- atk_7 doubled dbname token: exit 1, goal `dbname = none`.
- atk_8 return leading only (empty tail): exit 1, goal `parameters = [] ∧ dbname = none`.

Step-2 (materialize faithful patch + run_resolve) NOT TRIGGERED: it fires only for a same-spec impl that VERIFIES yet is wrong; none of the 8 verified, so there is no such patch to resolve. patches={} accordingly.

A-LEG / correspondence audit (assignment focus): refinement.md §C and mapping.md §3 correctly declare NO A-legs and NO kind-3 steps. axioms region contains 0 axiom declarations (grep confirmed); G-AX legitimately skipped. Spec `args = builtArgs leading dbname parameters` with builtArgs/dbnameToken as concrete pure defs — no opaque/ungrounded oracle to echo; verifying requires computing leading ++ parameters ++ dbnameToken dbname. `leading` modeled as an input is sound (unchanged repo code: [exe]+ -U/-h/-p flags), and conformance_check.py reconstructs it faithfully (recorded 100007 inputs, seed 15851, 0 disagreements). Legs A1-A4 map cleanly to the gold hunk (args.extend(parameters) moved before `if dbname: args += [dbname]`); the discriminating order lives in the exact-equality ensures.

VERDICT: SOUND. 8 distinct wrong impls (incl. prepatch) all verify-reject under the shared spec; positive control verifies; no verify-but-wrong candidate exists to break verify=>correct.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl verified; therefore no faithful refined patch needed to be materialized/resolve-run. The spec is an exact output-list equality that admits no verifying-but-wrong impl among the attempted distinct failure modes.
```

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. Assembling the command-line argument vector reads
--  three already-available pieces — the leading segment built from the
--  connection settings, an optional database-name token, and the list of
--  caller-supplied extra arguments — and concatenates them. Concatenation and
--  the optional token are modeled directly (List `++` and `Option.toList`); no
--  unchanged callee's contract is consumed and nothing foreign is deep-modeled,
--  so there is nothing to axiomatize. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The trailing token that names the target database, if one is named at all:
   a singleton holding that name when present, and nothing otherwise. This is
   the optional element that may or may not extend the argument vector. -/
def dbnameToken (dbname : Option String) : List String := dbname.toList

/- The complete command-line argument vector. It begins with the leading
   segment (the executable together with the connection options derived from the
   settings), is then extended by the caller-supplied extra arguments, and ends
   with the optional database-name token. The extra arguments therefore precede
   the database name in the vector; the database name, when present, is last. -/
def builtArgs (leading : List String) (dbname : Option String)
    (parameters : List String) : List String :=
  leading ++ parameters ++ dbnameToken dbname
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the command-line argument vector for invoking the database shell.

   `leading` is the leading segment already built from the connection settings
   (the executable name followed by whatever connection-option flags the
   settings call for); it is read-only here — this step neither inspects nor
   rewrites it, only builds upon it. `dbname` is the optional name of the target
   database: present as `some` when a database is named, `none` when none is.
   `parameters` are the extra arguments the caller passes through to the shell.

   The assembled vector places the caller-supplied extra arguments AFTER the
   leading segment and BEFORE the optional database-name token, so that the
   database name — when present — is the final element of the vector. -/
method buildShellArgs (leading : List String) (dbname : Option String)
    (parameters : List String) return (args : List String)
  ensures args = builtArgs leading dbname parameters
  do
    -- impl-start
    -- correct but structured differently: build the tail (params ++ token) first
    let tail := parameters ++ dbnameToken dbname
    let args := leading ++ tail
    return args
    -- impl-end

prove_correct buildShellArgs by
  loom_solve
  simp_all [builtArgs, dbnameToken]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec verified True for all 9 files (axioms/pure/pre/post byte-identical; only impl region edited). Verification via `bash scripts/lean_verify.sh <file>` under venv. Attacks run concurrently in background batches of 4.

### RESULTS (exit code from lean_verify wrapper + residual goal):
- pos_control (correct, restructured: tail := parameters ++ dbnameToken dbname; leading ++ tail): VERIFY exit 0 -> spec non-vacuous.
- atk_1 dbname-token before params (= PREPATCH order-swap bug, re-encoded): exit 1, goal `dbname.toList ++ parameters = parameters ++ dbname.toList`. Prepatch reproduced.
- atk_2 drop parameters (partial-content): exit 1, goal `parameters = []`.
- atk_3 drop dbname token: exit 1, goal `dbname = none`.
- atk_4 partial-domain (correct when token empty; token-before-params when dbname present, gated on (dbnameToken dbname).isEmpty): exit 1, goal `leading ++ dbnameToken dbname ++ parameters = builtArgs ...` in the token-present branch.
- atk_5 control-flow-effect (if parameters.isEmpty then correct else token-before-params): exit 1, goal `leading ++ dbnameToken dbname ++ parameters = builtArgs ...` in non-empty branch.
- atk_6 parameters.reverse (content mutation): exit 1, goal `parameters.reverse = parameters`.
- atk_7 doubled dbname token: exit 1, goal `dbname = none`.
- atk_8 return leading only (empty tail): exit 1, goal `parameters = [] ∧ dbname = none`.

Step-2 (materialize faithful patch + run_resolve) NOT TRIGGERED: it fires only for a same-spec impl that VERIFIES yet is wrong; none of the 8 verified, so there is no such patch to resolve. patches={} accordingly.

A-LEG / correspondence audit (assignment focus): refinement.md §C and mapping.md §3 correctly declare NO A-legs and NO kind-3 steps. axioms region contains 0 axiom declarations (grep confirmed); G-AX legitimately skipped. Spec `args = builtArgs leading dbname parameters` with builtArgs/dbnameToken as concrete pure defs — no opaque/ungrounded oracle to echo; verifying requires computing leading ++ parameters ++ dbnameToken dbname. `leading` modeled as an input is sound (unchanged repo code: [exe]+ -U/-h/-p flags), and conformance_check.py reconstructs it faithfully (recorded 100007 inputs, seed 15851, 0 disagreements). Legs A1-A4 map cleanly to the gold hunk (args.extend(parameters) moved before `if dbname: args += [dbname]`); the discriminating order lives in the exact-equality ensures.

VERDICT: SOUND. 8 distinct wrong impls (incl. prepatch) all verify-reject under the shared spec; positive control verifies; no verify-but-wrong candidate exists to break verify=>correct.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break audit of django__django-15851 velvet bundle. (1) Spec region is byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet backend) = True; the spec view (empty axioms, pure defs dbnameToken/builtArgs, empty pre/post, method signature + `ensures args = builtArgs leading dbname parameters`) is frozen and unaffected by the impl. (2) Solution.lean verifies clean (lean_verify.sh exit 0). (3) The modeled function builtArgs leading dbname parameters = leading ++ parameters ++ dbnameToken dbname exactly matches the gold-patched real callee DatabaseClient.settings_to_cmd_args_env, where args.extend(parameters) now runs BEFORE `if dbname: args += [dbname]` (parameters precede the dbname token; dbname is last). Confirmed against the real repo at base_commit b4817d20 with the gold patch applied. (4) conformance_check.py R/I shadow vs the real patched callee: 100007 fuzzed inputs, 0 disagreements. (5) Additional adversarial edge cases (empty NAME with service set, dbname None+service, whitespace dbname, int PORT, NAME='0', param values colliding with dbname, empty user, no-name->postgres default) all agree exactly with real behavior. The abstraction boundary (leading segment and dbname:Option supplied as inputs from unchanged repo code; if-dbname truthiness <-> Option.toList) is faithful. The spec is neither too strong nor drifting: it is exact behavioral equality with the real repo. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True), so the projected spec view is the same regardless of pre/post-patch impl — the leaked content, if any, is invariant. Mechanical G-LEAK screen (leakage.screen) passes with zero hard failures: no diff markers, no reproduced gold-patch line, no patched file path (client.py) / module path, no spec-view identifier or comment naming the patched repo symbol (settings_to_cmd_args_env; the spec names only buildShellArgs/builtArgs/dbnameToken, none of which are repo symbols), no bug/fix narration.

Semantic (gold-reconstruction) analysis: the gold edit moves `args.extend(parameters)` to run BEFORE `if dbname: args += [dbname]`, i.e. extra parameters precede the database name and the database name ends up last. The spec view encodes exactly this ordering via `builtArgs = leading ++ parameters ++ dbnameToken dbname` and the docstring 'the extra arguments therefore precede the database name; the database name, when present, is last.' This ordering requirement is DIRECTLY and explicitly stated in the PUBLIC problem_statement: 'dbshell additional parameters should be passed before dbname on PostgreSQL' and 'the args list just need to be constructed in the proper order, leaving the database name for the end of the args list.' The spec therefore reveals nothing beyond what the solver already sees in the public task — the discriminating content (parameters-before-dbname, dbname-last) is public. mapping.md/refinement.md are auditor artifacts, not part of the solver-visible spec view, so they are out of scope for leakage. No line reconstructs the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
