# P2 adversarial audit — django__django-15851

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_shellArgs pins `result` to EXACT list equality with a fully input-grounded concatenation ([executable] ++ optFlag "-U" user ++ optFlag "-h" host ++ optFlag "-p" port ++ parameters ++ dbname.toList). There is no axiom and no ungrounded oracle (axioms region is comment-only; meta axioms=[], deep_model_references=[], conf_skip=false). Any impl that is not extensionally equal to the spec function is therefore unprovable, and every genuinely-wrong impl I tried failed to verify. The only verifying variant (atk_7) is an extensionally-equal restructuring whose faithful patch RESOLVES, so verify does NOT imply not-correct.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,9 +77,9 @@
     args := args ++ ["-h", h]
   if let some p := port then
     args := args ++ ["-p", p]
-  args := args ++ parameters
   if let some d := dbname then
     args := args ++ [d]
+  args := args ++ parameters
   return args
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,6 @@
     args := args ++ ["-h", h]
   if let some p := port then
     args := args ++ ["-p", p]
-  args := args ++ parameters
   if let some d := dbname then
     args := args ++ [d]
   return args
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,10 +71,10 @@
     (parameters : List String)
     : List String := Id.run do
   let mut args := [executable]
+  if let some h := host then
+    args := args ++ ["-h", h]
   if let some u := user then
     args := args ++ ["-U", u]
-  if let some h := host then
-    args := args ++ ["-h", h]
   if let some p := port then
     args := args ++ ["-p", p]
   args := args ++ parameters
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,7 +76,7 @@
   if let some h := host then
     args := args ++ ["-h", h]
   if let some p := port then
-    args := args ++ ["-p", p]
+    args := args ++ ["-P", p]
   args := args ++ parameters
   if let some d := dbname then
     args := args ++ [d]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
     args := args ++ ["-p", p]
   args := args ++ parameters
   if let some d := dbname then
-    args := args ++ [d]
+    args := args ++ [d, d]
   return args
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -75,8 +75,7 @@
     args := args ++ ["-U", u]
   if let some h := host then
     args := args ++ ["-h", h]
-  if let some p := port then
-    args := args ++ ["-p", p]
+  args := args ++ ["-p", port.getD ""]
   args := args ++ parameters
   if let some d := dbname then
     args := args ++ [d]
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,18 +69,9 @@
     (executable : String)
     (user host port dbname : Option String)
     (parameters : List String)
-    : List String := Id.run do
-  let mut args := [executable]
-  if let some u := user then
-    args := args ++ ["-U", u]
-  if let some h := host then
-    args := args ++ ["-h", h]
-  if let some p := port then
-    args := args ++ ["-p", p]
-  args := args ++ parameters
-  if let some d := dbname then
-    args := args ++ [d]
-  return args
+    : List String :=
+  ((((([executable] ++ optFlag "-U" user) ++ optFlag "-h" host)
+      ++ optFlag "-p" port) ++ parameters) ++ dbname.toList)
 -- impl-end
 
 -- proof-start
@@ -90,8 +81,5 @@
       problem_spec_shellArgs executable user host port dbname parameters
         (implementation_shellArgs executable user host port dbname parameters) := by
   intro executable user host port dbname parameters
-  unfold problem_spec_shellArgs implementation_shellArgs optFlag
-  cases user <;> cases host <;> cases port <;> cases dbname <;>
-    simp only [Id.run, Option.toList, bind, pure, List.nil_append,
-      List.cons_append, List.append_nil]
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the command-line argument vector for an interactive database shell.

A database shell is launched by handing a separate client program a vector of
command-line arguments. The vector is built up in a set order:

  * the client program name (always first);
  * connection options derived from the connection settings — the user, the
    host, and the port — each emitted as a flag followed by its value, and only
    when that setting carries a value;
  * any extra free-form parameters the caller supplied; and
  * the database name, when one is available.

The client program requires every option to appear *before* the database name on
the command line; once the database name is seen, trailing tokens are treated as
extra positional arguments and ignored. The caller-supplied parameters are
options in this sense, so they must be placed ahead of the database name in the
vector.

Connection components are optional: a user, host, port, or database name that
carries no value contributes nothing to the vector. The extra parameters are a
(possibly empty) sequence and are always contributed in their given order.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The function
-- reads its connection settings at the I/O boundary; those reads (and the
-- presence/absence "truthiness" of each optional setting) are abstracted into
-- the optional-string inputs. The argument vector is then assembled structurally
-- by list concatenation, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The contribution of an optional flagged connection option to the argument
vector: a setting that carries a value `x` contributes the flag followed by its
value (`[flag, x]`); a setting that carries no value contributes nothing. -/
def optFlag (flag : String) (v : Option String) : List String :=
  match v with
  | none => []
  | some x => [flag, x]
-- pure-end

-- post-conditions-start
/-- The argument vector is exactly, in order: the program name; the user, host,
and port options (each present only when its setting carries a value); the
caller-supplied parameters; and finally the database name (present only when it
carries a value). The extra parameters precede the database name, and every
component is pinned to its input, so the entire vector is determined by the
settings. -/
def problem_spec_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    (result : List String) : Prop :=
  result =
    [executable]
      ++ optFlag "-U" user
      ++ optFlag "-h" host
      ++ optFlag "-p" port
      ++ parameters
      ++ dbname.toList
-- post-conditions-end

-- impl-start
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  args := args ++ parameters
  if let some d := dbname then
    args := args ++ [d]
  return args
-- impl-end

-- proof-start
theorem correct_shellArgs :
    ∀ (executable : String) (user host port dbname : Option String)
      (parameters : List String),
      problem_spec_shellArgs executable user host port dbname parameters
        (implementation_shellArgs executable user host port dbname parameters) := by
  intro executable user host port dbname parameters
  unfold problem_spec_shellArgs implementation_shellArgs optFlag
  cases user <;> cases host <;> cases port <;> cases dbname <;>
    simp only [Id.run, Option.toList, bind, pure, List.nil_append,
      List.cons_append, List.append_nil]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 GOLD bundle: benchmark-verified/django__django-15851/lean/Solution.lean.

SAME-SPEC: confirmed True for all 7 attacks + pc via swebench_unified.markers.same_spec (spec_view elides impl AND proof regions on the lean backend, so same_spec keys only on axioms/pure/pre/post — all left byte-identical). Command:
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open(GOLD).read(), open(ATK).read(), b.language))"  => True for atk_1..7 and pc.

VERIFY COMMAND (all): `bash scripts/lean_verify.sh <file>` run from project root, concurrently in 2 batches of 4 (<=4 at a time).

### Results per attack
- pc.lean (positive control = gold impl+proof): exit 0 (VERIFIES). #print axioms => propext/Classical.choice/Quot.sound (clean, standard).
- atk_1.lean  PREPATCH BUG (dbname appended BEFORE `++ parameters`, gold proof): exit 1 (FAILS to verify). Reproduces the prepatch defect; discriminating case dbname=some & parameters!=[] gives [...,dbname,p] vs spec's [...,p,dbname]. prepatch_reproduced=true.
- atk_2.lean  PARTIAL-DOMAIN (drops `++ parameters` entirely): exit 1 (FAILS).
- atk_3.lean  BOUNDARY/ORDER (emits -h before -U): exit 1 (FAILS).
- atk_4.lean  CONTROL-FLOW-EFFECT (wrong port flag "-P" instead of "-p"): exit 1 (FAILS).
- atk_5.lean  BOUNDARY (duplicates dbname: `++ [d, d]`): exit 1 (FAILS).
- atk_6.lean  UNGROUNDED/ORACLE-ECHO (drops port truthiness guard; unconditionally emits ["-p", port.getD ""]): exit 1 (FAILS).
- atk_7.lean  EQUIVALENT ECHO (left-nested `((((([executable]++optFlag "-U" user)++...)++parameters)++dbname.toList)`, proof by `rfl`): exit 0 (VERIFIES). #print axioms correct_shellArgs => 'does not depend on any axioms' (CLEANER than gold). Command: `bash scripts/lean_verify.sh atk_7_ax.lean` (atk_7 + `#print axioms correct_shellArgs`) => exit 0, output "'correct_shellArgs' does not depend on any axioms".

### MANDATORY RESOLVE (protocol step 2 — every verifying impl's faithful patch RUN through official harness):
- atk_7 is the ONLY impl whose proof closes. It is EXTENSIONALLY EQUAL to the gold impl (same concatenation, only left-nested bracketing + rfl proof), so its faithful Python refinement is behaviorally identical to the gold patch (parameters spliced BEFORE dbname). Faithful patch materialized at atk_7_patch.diff.
- EXECUTED: swebench_unified.harness.run_resolve('django__django-15851', <atk_7_patch>, timeout=1800) => completed=True, resolved=TRUE, attempts=1, flaky=False, note='resolved'. The verifying impl's faithful patch RESOLVES => spec NOT broken.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R or I; no A-consumed / A-reference legs and NO kind-3 (unjustified) legs. Rows 1,5,7=I (identical concrete op: init [executable], the moved `++ parameters` splice, return args); rows 2,3,4,6=R (Python truthiness `if x` <=> Option some/none; args+=[...] <=> ++[...]). meta.json corroborates: axioms=[], deep_model_references=[], conf_skip=false, G-AX=skip ("no consumed callee axiom and no A-reference; impl is all R/I"). The changed op (parameters/dbname ordering) is DEEPLY modeled as list concatenation in a fixed order, NOT axiomatized — so there are no A-legs whose callee correspondence could be unfaithful. The order parameters-before-dbname is pinned by the spec (`++ parameters ++ dbname.toList`), matching the FAIL_TO_PASS `test_parameters` semantics.

CONCLUSION: The postcondition is a maximally-tight exact-equality functional spec with no axioms/oracle. 6 distinct genuinely-wrong impls (prepatch, partial-domain, boundary x2, control-flow-effect, ungrounded-oracle) ALL fail to verify; the sole verifying variant is behaviorally identical to gold and its faithful patch resolves. No verify-but-not-resolve witness exists. Verdict: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The postcondition problem_spec_shellArgs pins `result` to EXACT list equality with a fully input-grounded concatenation ([executable] ++ optFlag "-U" user ++ optFlag "-h" host ++ optFlag "-p" port ++ parameters ++ dbname.toList). There is no axiom and no ungrounded oracle (axioms region is comment-only; meta axioms=[], deep_model_references=[], conf_skip=false). Any impl that is not extensionally equal to the spec function is therefore unprovable, and every genuinely-wrong impl I tried failed to verify. The only verifying variant (atk_7) is an extensionally-equal restructuring whose faithful patch RESOLVES, so verify does NOT imply not-correct.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the command-line argument vector for an interactive database shell.

A database shell is launched by handing a separate client program a vector of
command-line arguments. The vector is built up in a set order:

  * the client program name (always first);
  * connection options derived from the connection settings — the user, the
    host, and the port — each emitted as a flag followed by its value, and only
    when that setting carries a value;
  * any extra free-form parameters the caller supplied; and
  * the database name, when one is available.

The client program requires every option to appear *before* the database name on
the command line; once the database name is seen, trailing tokens are treated as
extra positional arguments and ignored. The caller-supplied parameters are
options in this sense, so they must be placed ahead of the database name in the
vector.

Connection components are optional: a user, host, port, or database name that
carries no value contributes nothing to the vector. The extra parameters are a
(possibly empty) sequence and are always contributed in their given order.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The function
-- reads its connection settings at the I/O boundary; those reads (and the
-- presence/absence "truthiness" of each optional setting) are abstracted into
-- the optional-string inputs. The argument vector is then assembled structurally
-- by list concatenation, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The contribution of an optional flagged connection option to the argument
vector: a setting that carries a value `x` contributes the flag followed by its
value (`[flag, x]`); a setting that carries no value contributes nothing. -/
def optFlag (flag : String) (v : Option String) : List String :=
  match v with
  | none => []
  | some x => [flag, x]
-- pure-end

-- post-conditions-start
/-- The argument vector is exactly, in order: the program name; the user, host,
and port options (each present only when its setting carries a value); the
caller-supplied parameters; and finally the database name (present only when it
carries a value). The extra parameters precede the database name, and every
component is pinned to its input, so the entire vector is determined by the
settings. -/
def problem_spec_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    (result : List String) : Prop :=
  result =
    [executable]
      ++ optFlag "-U" user
      ++ optFlag "-h" host
      ++ optFlag "-p" port
      ++ parameters
      ++ dbname.toList
-- post-conditions-end

-- impl-start
def implementation_shellArgs
    (executable : String)
    (user host port dbname : Option String)
    (parameters : List String)
    : List String := Id.run do
  let mut args := [executable]
  if let some u := user then
    args := args ++ ["-U", u]
  if let some h := host then
    args := args ++ ["-h", h]
  if let some p := port then
    args := args ++ ["-p", p]
  args := args ++ parameters
  if let some d := dbname then
    args := args ++ [d]
  return args
-- impl-end

-- proof-start
theorem correct_shellArgs :
    ∀ (executable : String) (user host port dbname : Option String)
      (parameters : List String),
      problem_spec_shellArgs executable user host port dbname parameters
        (implementation_shellArgs executable user host port dbname parameters) := by
  intro executable user host port dbname parameters
  unfold problem_spec_shellArgs implementation_shellArgs optFlag
  cases user <;> cases host <;> cases port <;> cases dbname <;>
    simp only [Id.run, Option.toList, bind, pure, List.nil_append,
      List.cons_append, List.append_nil]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 GOLD bundle: benchmark-verified/django__django-15851/lean/Solution.lean.

SAME-SPEC: confirmed True for all 7 attacks + pc via swebench_unified.markers.same_spec (spec_view elides impl AND proof regions on the lean backend, so same_spec keys only on axioms/pure/pre/post — all left byte-identical). Command:
  python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open(GOLD).read(), open(ATK).read(), b.language))"  => True for atk_1..7 and pc.

VERIFY COMMAND (all): `bash scripts/lean_verify.sh <file>` run from project root, concurrently in 2 batches of 4 (<=4 at a time).

### Results per attack
- pc.lean (positive control = gold impl+proof): exit 0 (VERIFIES). #print axioms => propext/Classical.choice/Quot.sound (clean, standard).
- atk_1.lean  PREPATCH BUG (dbname appended BEFORE `++ parameters`, gold proof): exit 1 (FAILS to verify). Reproduces the prepatch defect; discriminating case dbname=some & parameters!=[] gives [...,dbname,p] vs spec's [...,p,dbname]. prepatch_reproduced=true.
- atk_2.lean  PARTIAL-DOMAIN (drops `++ parameters` entirely): exit 1 (FAILS).
- atk_3.lean  BOUNDARY/ORDER (emits -h before -U): exit 1 (FAILS).
- atk_4.lean  CONTROL-FLOW-EFFECT (wrong port flag "-P" instead of "-p"): exit 1 (FAILS).
- atk_5.lean  BOUNDARY (duplicates dbname: `++ [d, d]`): exit 1 (FAILS).
- atk_6.lean  UNGROUNDED/ORACLE-ECHO (drops port truthiness guard; unconditionally emits ["-p", port.getD ""]): exit 1 (FAILS).
- atk_7.lean  EQUIVALENT ECHO (left-nested `((((([executable]++optFlag "-U" user)++...)++parameters)++dbname.toList)`, proof by `rfl`): exit 0 (VERIFIES). #print axioms correct_shellArgs => 'does not depend on any axioms' (CLEANER than gold). Command: `bash scripts/lean_verify.sh atk_7_ax.lean` (atk_7 + `#print axioms correct_shellArgs`) => exit 0, output "'correct_shellArgs' does not depend on any axioms".

### MANDATORY RESOLVE (protocol step 2 — every verifying impl's faithful patch RUN through official harness):
- atk_7 is the ONLY impl whose proof closes. It is EXTENSIONALLY EQUAL to the gold impl (same concatenation, only left-nested bracketing + rfl proof), so its faithful Python refinement is behaviorally identical to the gold patch (parameters spliced BEFORE dbname). Faithful patch materialized at atk_7_patch.diff.
- EXECUTED: swebench_unified.harness.run_resolve('django__django-15851', <atk_7_patch>, timeout=1800) => completed=True, resolved=TRUE, attempts=1, flaky=False, note='resolved'. The verifying impl's faithful patch RESOLVES => spec NOT broken.

REFINEMENT.MD AUDIT (protocol step 3): every leg is R or I; no A-consumed / A-reference legs and NO kind-3 (unjustified) legs. Rows 1,5,7=I (identical concrete op: init [executable], the moved `++ parameters` splice, return args); rows 2,3,4,6=R (Python truthiness `if x` <=> Option some/none; args+=[...] <=> ++[...]). meta.json corroborates: axioms=[], deep_model_references=[], conf_skip=false, G-AX=skip ("no consumed callee axiom and no A-reference; impl is all R/I"). The changed op (parameters/dbname ordering) is DEEPLY modeled as list concatenation in a fixed order, NOT axiomatized — so there are no A-legs whose callee correspondence could be unfaithful. The order parameters-before-dbname is pinned by the spec (`++ parameters ++ dbname.toList`), matching the FAIL_TO_PASS `test_parameters` semantics.

CONCLUSION: The postcondition is a maximally-tight exact-equality functional spec with no axioms/oracle. 6 distinct genuinely-wrong impls (prepatch, partial-domain, boundary x2, control-flow-effect, ungrounded-oracle) ALL fail to verify; the sole verifying variant is behaviorally identical to gold and its faithful patch resolves. No verify-but-not-resolve witness exists. Verdict: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. Checks performed: (1) lean_verify.sh exit 0; #print axioms correct_shellArgs => [propext] only, no sorryAx (proof genuine). (2) same_spec(Solution, Solution_prepatch, LeanBackend) = True; spec/pre/post/pure/axioms regions byte-identical between patch and prepatch — the only diff is impl-region placement of `args := args ++ parameters`, matching the gold patch (moving args.extend(parameters) ahead of the dbname append). (3) Differential faithfulness: transcribed the real post-patch DatabaseClient.settings_to_cmd_args_env args-assembly, applied the documented abstraction (truthiness->Option; effective-dbname defaulting `if not dbname and not service: dbname='postgres'` folded into the dbname input; str(port)), and compared against the spec formula result = [exe] ++ optFlag "-U" user ++ optFlag "-h" host ++ optFlag "-p" port ++ parameters ++ dbname.toList over 200,000 fuzzed raw settings dicts (falsy 0/""/None, service-set-with-empty-NAME so no default fires, varied parameter lists). 0 mismatches. (4) F2P case {'NAME':'dbname'},['--help'] => ['psql','--help','dbname'] for both spec and real; prepatch order gives ['psql','dbname','--help'], so the spec correctly discriminates the fix. The spec pins exact list equality (not too strong, not drifted); env dict is legitimately out of scope (unchanged by patch). Spec agrees with the real callee on all tested inputs.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery).

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical (same_spec=True); impl+proof properly elided in spec view. The gold edit is 'parameters before dbname' (move args.extend(parameters) ahead of the dbname append). The public problem_statement already discloses this fully: 'additional parameters should be passed before dbname', 'psql expects all options to proceed the database name', 'leaving the database name for the end of the args list'. The spec-view docstring ('parameters must be placed ahead of the database name') and postcondition ('... ++ parameters ++ dbname.toList') merely restate this public behavior. The rest of the spec (executable first; -U/-h/-p flags; optionality) describes surrounding function behavior, which a full postcondition is expected to pin, not the edit. No spec-view line quotes gold-patch specifics (no .extend, no reference to the moved line, no prepatch ordering — the buggy ordering appears only in the elided prepatch proof comment, outside the spec view). Nothing leaks beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
