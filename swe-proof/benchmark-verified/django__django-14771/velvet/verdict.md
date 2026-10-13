# P2 adversarial audit — django__django-14771

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_drop.lean`, `atk_always.lean`, `atk_reverse.lean`, `atk_order.lean`, `atk_partial.lean`, `atk_suffix.lean`, `atk_prepatch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl exists whose faithful patch fails to resolve. The only non-gold impl that verifies (atk_echo) is a behavioral echo of relaunchArgvSpec, whose faithful refined patch IS the gold patch.diff and RESOLVES=True under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,15 +84,7 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
-    let mut args : List (List Char) := [executable]
-    args := args ++ warnopts.map warnFlag
-    if isCpython then
-      args := args ++ xopts.map xFlag
-    args := args ++ argv
-    return args
+    return relaunchArgvSpec executable warnopts isCpython xopts argv
     -- impl-end
 
 prove_correct relaunchArgv by
```

Attack 2 — `atk_drop.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,13 +84,8 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
     let mut args : List (List Char) := [executable]
     args := args ++ warnopts.map warnFlag
-    if isCpython then
-      args := args ++ xopts.map xFlag
     args := args ++ argv
     return args
     -- impl-end
```

Attack 3 — `atk_always.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,13 +84,9 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
     let mut args : List (List Char) := [executable]
     args := args ++ warnopts.map warnFlag
-    if isCpython then
-      args := args ++ xopts.map xFlag
+    args := args ++ xopts.map xFlag
     args := args ++ argv
     return args
     -- impl-end
```

Attack 4 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,13 +84,10 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
     let mut args : List (List Char) := [executable]
     args := args ++ warnopts.map warnFlag
     if isCpython then
-      args := args ++ xopts.map xFlag
+      args := args ++ (xopts.reverse).map xFlag
     args := args ++ argv
     return args
     -- impl-end
```

Attack 5 — `atk_order.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,14 +84,11 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
     let mut args : List (List Char) := [executable]
     args := args ++ warnopts.map warnFlag
+    args := args ++ argv
     if isCpython then
       args := args ++ xopts.map xFlag
-    args := args ++ argv
     return args
     -- impl-end
 
```

Attack 6 — `atk_partial.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,13 +84,10 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
     let mut args : List (List Char) := [executable]
     args := args ++ warnopts.map warnFlag
     if isCpython then
-      args := args ++ xopts.map xFlag
+      args := args ++ (xopts.take 1).map xFlag
     args := args ++ argv
     return args
     -- impl-end
```

Attack 7 — `atk_suffix.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,13 +84,10 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
     let mut args : List (List Char) := [executable]
     args := args ++ warnopts.map warnFlag
     if isCpython then
-      args := args ++ xopts.map xFlag
+      args := args ++ xopts.map (fun kv => xFlag kv ++ ['!'])
     args := args ++ argv
     return args
     -- impl-end
```

Attack 8 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The behaviour modeled here is a closed function of the
@@ -84,13 +84,13 @@
   ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
   do
     -- impl-start
-    -- Start with the interpreter path; append one -W flag per warning option;
-    -- then, only on CPython, append one -X flag per configured X-option (in
-    -- order); finally append the trailing program arguments.
+    -- Pre-image skeleton: the runtime X-options are NEVER read or forwarded; the
+    -- vector is only the interpreter path, the -W warning flags, and the trailing
+    -- arguments. The frozen spec requires the configured X-options to be forwarded
+    -- as -X flags on CPython (relaunchArgvSpec includes `xopts.map xFlag`), so
+    -- prove_correct MUST fail whenever any X-option is configured on CPython.
     let mut args : List (List Char) := [executable]
     args := args ++ warnopts.map warnFlag
-    if isCpython then
-      args := args ++ xopts.map xFlag
     args := args ++ argv
     return args
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
-- (No axiomatized callees. The behaviour modeled here is a closed function of the
--  interpreter path, the warning-option list, the runtime-implementation flag, the
--  list of runtime X-options, and the trailing program arguments. Each input is read
--  directly; nothing about how the relaunched interpreter is subsequently spawned is
--  consulted, so no callee contract is assumed. Every step is an R/I refinement,
--  validated against the real construction by conformance_check.py (G-CONF). See
--  refinement.md §C.)
-- axioms-end

-- pure-start
/- One runtime X-option's value. A bare option (supplied as `-Xkey`) carries no
   value (`bare`); a keyed option (supplied as `-Xkey=value`) carries its value
   string (`eq value`). This is the two shapes a runtime X-option can take. -/
inductive XVal where
  | bare
  | eq (value : List Char)
  deriving DecidableEq

/- The command-line flag a single warning option expands to: the `-W` prefix
   followed by the option text (the pre-existing warning-option forwarding, kept
   verbatim and unchanged). -/
def warnFlag (o : List Char) : List Char := "-W".toList ++ o

/- The command-line flag a single runtime X-option expands to. A bare option
   becomes `-Xkey`; a keyed option becomes `-Xkey=value`. This is the per-option
   serialization the construction applies to every X-option in order. -/
def xFlag (kv : List Char × XVal) : List Char :=
  match kv.2 with
  | XVal.bare    => "-X".toList ++ kv.1
  | XVal.eq value => "-X".toList ++ kv.1 ++ "=".toList ++ value

/- The full argument vector used to relaunch the interpreter under the
   auto-reloader, given: the interpreter path (`executable`); the active warning
   options (`warnopts`); whether the running interpreter is the CPython
   implementation (`isCpython`); the runtime X-options in their configured order
   (`xopts`); and the trailing program arguments (`argv`).

   The vector is the interpreter path, followed by one `-W` flag per warning
   option, followed — only on the CPython implementation — by one `-X` flag per
   configured X-option (in order, each serialized by `xFlag`), followed by the
   trailing program arguments. Off CPython the X-options contribute nothing. -/
def relaunchArgvSpec (executable : List Char) (warnopts : List (List Char))
    (isCpython : Bool) (xopts : List (List Char × XVal))
    (argv : List (List Char)) : List (List Char) :=
  [executable]
    ++ warnopts.map warnFlag
    ++ (if isCpython then xopts.map xFlag else [])
    ++ argv
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the argument vector the auto-reloader uses to relaunch the
   interpreter. The vector begins with the interpreter path and the active warning
   options (each as a `-W` flag), and ends with the program's trailing arguments.

   Desired behaviour: on the CPython implementation, every configured runtime
   X-option must also be forwarded to the relaunched interpreter — each as a `-X`
   flag, in configured order, serialized as `-Xkey` when it carries no value and as
   `-Xkey=value` when it does — placed after the warning options and before the
   trailing arguments. On a non-CPython implementation the X-options are not
   forwarded.

   All inputs are read-only (none `mut`): the construction reads them and emits the
   vector, mutating no input (directive 5). Option/argument text is modeled as
   `List Char`; the vector is a `List (List Char)` of argument strings
   (mapping.md §2). -/
method relaunchArgv (executable : List Char) (warnopts : List (List Char))
    (isCpython : Bool) (xopts : List (List Char × XVal))
    (argv : List (List Char)) return (out : List (List Char))
  ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
  do
    -- impl-start
    -- Start with the interpreter path; append one -W flag per warning option;
    -- then, only on CPython, append one -X flag per configured X-option (in
    -- order); finally append the trailing program arguments.
    let mut args : List (List Char) := [executable]
    args := args ++ warnopts.map warnFlag
    if isCpython then
      args := args ++ xopts.map xFlag
    args := args ++ argv
    return args
    -- impl-end

prove_correct relaunchArgv by
  loom_solve <;>
    simp_all [relaunchArgvSpec, List.append_assoc]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is an EXACT functional equality `ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv` with NO precondition and NO axioms. The deep model relaunchArgvSpec/xFlag/warnFlag is fully spelled out in the frozen pure region. This is the tightest possible spec: any impl that verifies must equal relaunchArgvSpec on ALL inputs, hence is behaviorally identical to the gold construction on every configuration.

PROTOCOL EXECUTED (project root =; velvet backend). All 9 files same_spec==True vs bundle Solution.lean (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean (exact gold impl)            exit 0  VERIFIES (positive control OK)
- atk_echo.lean    `return relaunchArgvSpec ...` exit 0  VERIFIES (ungrounded-oracle echo)
- atk_drop.lean    (omit xopts append)           exit 1  FAILS (residual goal isCpython=true -> xopts=[])
- atk_always.lean  (forward xopts even off CPython) exit 1 FAILS (control-flow-effect)
- atk_reverse.lean (xopts.reverse)               exit 1  FAILS (order)
- atk_order.lean   (argv before xopts)           exit 1  FAILS (placement)
- atk_partial.lean (xopts.take 1)                exit 1  FAILS (partial-domain)
- atk_suffix.lean  (xFlag kv ++ ['!'])           exit 1  FAILS (boundary/serialization)
- atk_prepatch.lean (bundle Solution_prepatch)   exit 1  FAILS -> prepatch bug reproduced

Verifications launched concurrently as background Bash jobs, <=4 at a time (two batches of 4 + prepatch), then collected.

RESOLVE RUN (mandatory for every verifying wrong impl): atk_echo computes exactly relaunchArgvSpec, whose R/I transliteration per mapping.md IS the gold patch construction; its faithful refined patch equals patch.diff (confirmed byte-identical to the dataset gold patch). Executed:
  python -c "from swebench_unified.harness import run_resolve; print(run_resolve('django__django-14771', open('benchmark-verified/django__django-14771/patch.diff').read(), run_id='sbu-audit-echo-14771', timeout=1800).resolved)"
  => RESOLVED: True (harness ran in-container, report.json resolved=true).
So the only verifying non-gold impl's faithful patch RESOLVES => not a weakness (matches the resolved G-PANEL-1/G-EQ echo policy: same-spec verifying echo fails a gate only if its refined patch does NOT resolve).

REFINEMENT.MD AUDIT (leg kinds): A1 R+I, A2 I+R, A3 I+R, A4 R+I, A5 R — every leg is R/I; §B confirms NO consumed axioms, NO deep-model A-reference (Path/getattr __spec__/py_script.exists/subprocess.run are unchanged and outside the F2P-observed behavior), NO axiom_check.py (G-AX=skip is correct). §C confirms no kind-3 step: the genuinely-changed op (forward configured X-options on CPython, per-value-shape serialization, in order, after -W and before trailing argv) is modeled DEEPLY in relaunchArgvSpec/xFlag, not hidden behind any axiom. Model<->patch correspondence holds: relaunchArgvSpec's structure ([exec] ++ warn -W flags ++ (if cpython then xopts -X flags else []) ++ argv) mirrors patch.diff's inserted block placed strictly before the unchanged __spec__/argv tail; the `value is True` identity test (not truthiness) is faithfully captured by XVal.bare vs XVal.eq and exercised by G-CONF (string "True" keyed, False keyed). G-CONF passed 100010 configs, 0 disagreements (seed 14771).

CONCLUSION: verify => correct holds. No same-spec verifying impl produces a non-resolving faithful patch. >=5 distinct wrong impls (6 genuine + prepatch) all fail verification; the sole verifying non-gold impl resolves. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_drop.lean`, `atk_always.lean`, `atk_reverse.lean`, `atk_order.lean`, `atk_partial.lean`, `atk_suffix.lean`, `atk_prepatch.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No verifying wrong impl exists whose faithful patch fails to resolve. The only non-gold impl that verifies (atk_echo) is a behavioral echo of relaunchArgvSpec, whose faithful refined patch IS the gold patch.diff and RESOLVES=True under the official harness.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_drop.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_always.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_reverse.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_order.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_partial.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_suffix.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a closed function of the
--  interpreter path, the warning-option list, the runtime-implementation flag, the
--  list of runtime X-options, and the trailing program arguments. Each input is read
--  directly; nothing about how the relaunched interpreter is subsequently spawned is
--  consulted, so no callee contract is assumed. Every step is an R/I refinement,
--  validated against the real construction by conformance_check.py (G-CONF). See
--  refinement.md §C.)
-- axioms-end

-- pure-start
/- One runtime X-option's value. A bare option (supplied as `-Xkey`) carries no
   value (`bare`); a keyed option (supplied as `-Xkey=value`) carries its value
   string (`eq value`). This is the two shapes a runtime X-option can take. -/
inductive XVal where
  | bare
  | eq (value : List Char)
  deriving DecidableEq

/- The command-line flag a single warning option expands to: the `-W` prefix
   followed by the option text (the pre-existing warning-option forwarding, kept
   verbatim and unchanged). -/
def warnFlag (o : List Char) : List Char := "-W".toList ++ o

/- The command-line flag a single runtime X-option expands to. A bare option
   becomes `-Xkey`; a keyed option becomes `-Xkey=value`. This is the per-option
   serialization the construction applies to every X-option in order. -/
def xFlag (kv : List Char × XVal) : List Char :=
  match kv.2 with
  | XVal.bare    => "-X".toList ++ kv.1
  | XVal.eq value => "-X".toList ++ kv.1 ++ "=".toList ++ value

/- The full argument vector used to relaunch the interpreter under the
   auto-reloader, given: the interpreter path (`executable`); the active warning
   options (`warnopts`); whether the running interpreter is the CPython
   implementation (`isCpython`); the runtime X-options in their configured order
   (`xopts`); and the trailing program arguments (`argv`).

   The vector is the interpreter path, followed by one `-W` flag per warning
   option, followed — only on the CPython implementation — by one `-X` flag per
   configured X-option (in order, each serialized by `xFlag`), followed by the
   trailing program arguments. Off CPython the X-options contribute nothing. -/
def relaunchArgvSpec (executable : List Char) (warnopts : List (List Char))
    (isCpython : Bool) (xopts : List (List Char × XVal))
    (argv : List (List Char)) : List (List Char) :=
  [executable]
    ++ warnopts.map warnFlag
    ++ (if isCpython then xopts.map xFlag else [])
    ++ argv
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assembling the argument vector the auto-reloader uses to relaunch the
   interpreter. The vector begins with the interpreter path and the active warning
   options (each as a `-W` flag), and ends with the program's trailing arguments.

   Desired behaviour: on the CPython implementation, every configured runtime
   X-option must also be forwarded to the relaunched interpreter — each as a `-X`
   flag, in configured order, serialized as `-Xkey` when it carries no value and as
   `-Xkey=value` when it does — placed after the warning options and before the
   trailing arguments. On a non-CPython implementation the X-options are not
   forwarded.

   All inputs are read-only (none `mut`): the construction reads them and emits the
   vector, mutating no input (directive 5). Option/argument text is modeled as
   `List Char`; the vector is a `List (List Char)` of argument strings
   (mapping.md §2). -/
method relaunchArgv (executable : List Char) (warnopts : List (List Char))
    (isCpython : Bool) (xopts : List (List Char × XVal))
    (argv : List (List Char)) return (out : List (List Char))
  ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv
  do
    -- impl-start
    -- Start with the interpreter path; append one -W flag per warning option;
    -- then, only on CPython, append one -X flag per configured X-option (in
    -- order); finally append the trailing program arguments.
    let mut args : List (List Char) := [executable]
    args := args ++ warnopts.map warnFlag
    if isCpython then
      args := args ++ xopts.map xFlag
    args := args ++ argv
    return args
    -- impl-end

prove_correct relaunchArgv by
  loom_solve <;>
    simp_all [relaunchArgvSpec, List.append_assoc]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: postcondition is an EXACT functional equality `ensures out = relaunchArgvSpec executable warnopts isCpython xopts argv` with NO precondition and NO axioms. The deep model relaunchArgvSpec/xFlag/warnFlag is fully spelled out in the frozen pure region. This is the tightest possible spec: any impl that verifies must equal relaunchArgvSpec on ALL inputs, hence is behaviorally identical to the gold construction on every configuration.

PROTOCOL EXECUTED (project root =; velvet backend). All 9 files same_spec==True vs bundle Solution.lean (impl-region-only edits; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- pos_control.lean (exact gold impl)            exit 0  VERIFIES (positive control OK)
- atk_echo.lean    `return relaunchArgvSpec ...` exit 0  VERIFIES (ungrounded-oracle echo)
- atk_drop.lean    (omit xopts append)           exit 1  FAILS (residual goal isCpython=true -> xopts=[])
- atk_always.lean  (forward xopts even off CPython) exit 1 FAILS (control-flow-effect)
- atk_reverse.lean (xopts.reverse)               exit 1  FAILS (order)
- atk_order.lean   (argv before xopts)           exit 1  FAILS (placement)
- atk_partial.lean (xopts.take 1)                exit 1  FAILS (partial-domain)
- atk_suffix.lean  (xFlag kv ++ ['!'])           exit 1  FAILS (boundary/serialization)
- atk_prepatch.lean (bundle Solution_prepatch)   exit 1  FAILS -> prepatch bug reproduced

Verifications launched concurrently as background Bash jobs, <=4 at a time (two batches of 4 + prepatch), then collected.

RESOLVE RUN (mandatory for every verifying wrong impl): atk_echo computes exactly relaunchArgvSpec, whose R/I transliteration per mapping.md IS the gold patch construction; its faithful refined patch equals patch.diff (confirmed byte-identical to the dataset gold patch). Executed:
  python -c "from swebench_unified.harness import run_resolve; print(run_resolve('django__django-14771', open('benchmark-verified/django__django-14771/patch.diff').read(), run_id='sbu-audit-echo-14771', timeout=1800).resolved)"
  => RESOLVED: True (harness ran in-container, report.json resolved=true).
So the only verifying non-gold impl's faithful patch RESOLVES => not a weakness (matches the resolved G-PANEL-1/G-EQ echo policy: same-spec verifying echo fails a gate only if its refined patch does NOT resolve).

REFINEMENT.MD AUDIT (leg kinds): A1 R+I, A2 I+R, A3 I+R, A4 R+I, A5 R — every leg is R/I; §B confirms NO consumed axioms, NO deep-model A-reference (Path/getattr __spec__/py_script.exists/subprocess.run are unchanged and outside the F2P-observed behavior), NO axiom_check.py (G-AX=skip is correct). §C confirms no kind-3 step: the genuinely-changed op (forward configured X-options on CPython, per-value-shape serialization, in order, after -W and before trailing argv) is modeled DEEPLY in relaunchArgvSpec/xFlag, not hidden behind any axiom. Model<->patch correspondence holds: relaunchArgvSpec's structure ([exec] ++ warn -W flags ++ (if cpython then xopts -X flags else []) ++ argv) mirrors patch.diff's inserted block placed strictly before the unchanged __spec__/argv tail; the `value is True` identity test (not truthiness) is faithfully captured by XVal.bare vs XVal.eq and exercised by G-CONF (string "True" keyed, False keyed). G-CONF passed 100010 configs, 0 disagreements (seed 14771).

CONCLUSION: verify => correct holds. No same-spec verifying impl produces a non-resolving faithful patch. >=5 distinct wrong impls (6 genuine + prepatch) all fail verification; the sole verifying non-gold impl resolves. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-14771 velvet. The spec models the patched get_child_arguments() X-option-forwarding: relaunchArgvSpec = [executable] ++ warnopts.map warnFlag ++ (if isCpython then xopts.map xFlag else []) ++ argv, with xFlag reproducing `f'-X{key}' if value is True else f'-X{key}={value}'`.

Checks performed:
1. same_spec(Solution, Solution_prepatch, velvet) = True — spec region byte-identical; the prepatch differs only in impl (omits the xopts append) and fails `out = relaunchArgvSpec`, so the discriminator is genuine.
2. spec_view is clean (no gold-patch/problem-statement leakage; only signatures + pure helpers pass through).
3. Lean verifies: `prove_correct relaunchArgv` elaborates, exit 0 (lean_verify.sh, 600s cap).
4. DIFFERENTIAL FAITHFULNESS (core test): applied the gold patch to a fresh copy of the base worktree (@ 4884a87e02) and ran the R/I shadow of relaunchArgvSpec against the REAL patched get_child_arguments() over 250,000 inputs — 200k standard fuzz + 50k adversarial. Coverage included: the F2P test_xoptions case ({'utf8':True,'a':'b'}), the `value is True` identity boundary (string "True" -> keyed, not bare), non-True objects (False, None, ints, floats -> keyed via str), non-cpython (X-options dropped), warnopts interleaving, and odd keys. ZERO disagreements.
5. Branch abstraction check: the argv parameter faithfully abstracts the trailing-arg tail in BOTH the `else: args += sys.argv` branch and the `__spec__` `-m name` branch; X-options are always inserted after -W flags and before the tail, matching the patch's insertion point exactly (verified real == model on the -m branch).

The modeled function does not drift from the real callee on any input; no diverging input exists. Spec is not too strong. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous check of the velvet spec view for django__django-14771.

Mechanical G-LEAK screen: PASS (no diff markers, no verbatim gold-patch line, no patched file path 'django/utils/autoreload.py', no spec-view identifier/comment embedding the only distinctive changed symbol 'get_child_arguments', no narration). same_spec(Solution.lean, Solution_prepatch.lean) = True — the entire discriminator lives in the elided impl region; the spec view is byte-identical pre/post patch.

Semantic leakage judged against the SOLVER-VISIBLE problem_statement only (not hints; hints_text is empty here anyway). The problem_statement is titled 'Auto-reloader should pass -X options (for cpython implementation)' and its body names/links sys._xoptions (with the docs.python.org/3/library/sys.html#sys._xoptions reference), the 'cpython' implementation, and shows `python -X utf8 ... runserver`. Thus the desired behavior — forwarding configured runtime X-options as `-X` flags on CPython — plus the -Xkey / -Xkey=value CLI serialization and the `value is True` (bare) vs string-value shape are ALL already public via the task and the linked CPython docs.

The spec view (relaunchArgvSpec / xFlag / warnFlag / XVal and the relaunchArgv method contract) states this behavior abstractly. It does NOT reveal the edit location beyond the public statement: the patched file (django/utils/autoreload.py) and function (get_child_arguments) are not named — modeled as relaunchArgv/relaunchArgvSpec. The '-W warning options' and interpreter-path framing is pre-existing unchanged context. Describing the target behavior in terms the bug report already exposes is legitimate spec authorship, not gold-edit leakage.

Conclusion: NO-LEAKAGE — the spec view does not leak the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
