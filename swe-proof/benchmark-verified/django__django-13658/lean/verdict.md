# P2 adversarial audit — django__django-13658

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_no_special.lean`, `atk_3_swap_cond.lean`, `atk_4_second_arg.lean`, `atk_5_no_basename.lean`, `atk_6_const.lean`, `atk_7_wrong_const.lean`, `atk_8_empty.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,7 @@
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
   Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
-    let mut progName := basename argv.headI
+    let mut progName := basename _ambient.headI
     if progName = "__main__.py" then
       progName := "python -m django"
     return progName
```

Attack 2 — `atk_2_no_special.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,14 +59,7 @@
 
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
-  Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
-    let mut progName := basename argv.headI
-    if progName = "__main__.py" then
-      progName := "python -m django"
-    return progName
+  basename argv.headI
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3_swap_cond.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,11 +60,8 @@
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
   Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
     let mut progName := basename argv.headI
-    if progName = "__main__.py" then
+    if progName ≠ "__main__.py" then
       progName := "python -m django"
     return progName
 -- impl-end
```

Attack 4 — `atk_4_second_arg.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,7 @@
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
   Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
-    let mut progName := basename argv.headI
+    let mut progName := basename (argv.getD 1 "")
     if progName = "__main__.py" then
       progName := "python -m django"
     return progName
```

Attack 5 — `atk_5_no_basename.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,10 +60,7 @@
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
   Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
-    let mut progName := basename argv.headI
+    let mut progName := argv.headI
     if progName = "__main__.py" then
       progName := "python -m django"
     return progName
```

Attack 6 — `atk_6_const.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,14 +59,7 @@
 
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
-  Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
-    let mut progName := basename argv.headI
-    if progName = "__main__.py" then
-      progName := "python -m django"
-    return progName
+  "python -m django"
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7_wrong_const.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,12 +60,9 @@
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
   Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
     let mut progName := basename argv.headI
     if progName = "__main__.py" then
-      progName := "python -m django"
+      progName := "python -m foo"
     return progName
 -- impl-end
 
```

Attack 8 — `atk_8_empty.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,14 +59,7 @@
 
 -- impl-start
 def implementation_progName (argv : List String) (_ambient : List String) : String :=
-  Id.run do
-    -- Derive the program name from the utility's OWN argument vector, applying
-    -- the module-execution special case. The ambient argument vector is not
-    -- consulted.
-    let mut progName := basename argv.headI
-    if progName = "__main__.py" then
-      progName := "python -m django"
-    return progName
+  ""
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Determining the program name presented by a command-line utility.

A command-line utility is invoked with an argument vector whose first entry is
the path under which the program was launched. The utility presents a program
name to the user (for example, in the usage banner of its option parser). That
program name is defined to be:

* the final path component of the utility's own first argument, and
* a constant textual name (`python -m django`) in the special case where that
  final component is the module-execution entry point `__main__.py`.

The key property is that the presented program name is a function of the
utility's own argument vector alone. It does not depend on any ambient,
process-global argument vector: two invocations with the same utility argument
vector present the same program name regardless of the surrounding process
state.

Argument vectors are modeled as `List String` (one element per argument);
individual arguments are modeled as `String`. Path components are separated by
`'/'`, matching POSIX path semantics.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The two operations the behavior
-- relies on — extracting the final path component of a string and the constant
-- module-execution special case — are modeled deeply below (`basename` /
-- `computeProgName`), so there is no opaque callee signature and no consumed
-- `_prop` axiom. The deep model is validated against the real implementation by
-- the conformance check.
-- axioms-end

-- pure-start
/-- The final path component of a string: everything after the last `'/'`
separator (the whole string when there is no separator; the empty string when
the string ends in a separator). Models POSIX basename. -/
def basename (s : String) : String :=
  (s.split (· = '/')).reverse.headI

/-- The program name derived from a single argument (the utility's first
argument): the final path component, except that the module-execution entry
point maps to a constant textual name. -/
def computeProgName (arg0 : String) : String :=
  let b := basename arg0
  if b = "__main__.py" then "python -m django" else b
-- pure-end

-- post-conditions-start
/-- The presented program name is exactly the name derived from the utility's
own argument vector. The specification mentions only the utility's own argument
vector, and never the ambient one: this pins the result to be independent of any
ambient argument vector. -/
def problem_spec_progName (argv : List String) (result : String) : Prop :=
  result = computeProgName argv.headI
-- post-conditions-end

-- impl-start
def implementation_progName (argv : List String) (_ambient : List String) : String :=
  Id.run do
    -- Derive the program name from the utility's OWN argument vector, applying
    -- the module-execution special case. The ambient argument vector is not
    -- consulted.
    let mut progName := basename argv.headI
    if progName = "__main__.py" then
      progName := "python -m django"
    return progName
-- impl-end

-- proof-start
theorem correct_progName :
    ∀ (argv ambient : List String), argv ≠ [] →
      problem_spec_progName argv (implementation_progName argv ambient) := by
  intro argv ambient _
  unfold problem_spec_progName implementation_progName computeProgName
  by_cases h : basename argv.headI = "__main__.py" <;>
    simp only [Id.run, bind, pure, h, if_true, if_false]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = total functional equality over fully-grounded defs (no axioms/opaque/_prop): correct_progName requires implementation_progName argv ambient = computeProgName argv.headI for ALL argv≠[] and ALL ambient. same_spec elides impl+proof; head (imports/docstring/axioms/pure basename+computeProgName/post-conditions) kept byte-identical => same_spec=True verified for all 8 attacks + PC via markers.same_spec (get_backend('lean')).

8 DISTINCT same-spec wrong impls (all with the GENUINE fixed obligation): atk_1 prepatch bug (basename _ambient.headI, ungrounded on argv); atk_2 partial-domain (drops __main__.py special case); atk_3 control-flow-effect (negated condition, wrong branch); atk_4 boundary/off-by-one (argv.getD 1 not headI); atk_5 missing basename (raw arg0, wrong when path has '/'); atk_6 ungrounded-oracle echo (const 'python -m django'); atk_7 wrong special-case constant; atk_8 empty string. Command: `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch. Results: PC pc_gold.lean EXIT=0 (verifies); ALL 8 attacks EXIT=1 'unsolved goals' (genuine false statements).

Additionally threw aggressive automation (simp_all with all defs unfolded, decide) at the two most plausible wrong impls (hard_1=prepatch, hard_2=no_special): both EXIT=1 — unprovable, as Lean soundness requires for a false total-equality statement. Because ZERO wrong impls close with clean axioms, there is NO verifying-but-wrong impl to materialize+resolve (resolve obligation vacuously satisfied — verify⇏correct not exhibitable). PC axioms clean: `#print axioms correct_progName` => depends on [propext] only (no sorryAx/Classical.choice misuse). Pipeline positive control: gold patch.diff run through official harness run_resolve('django__django-13658') => RESOLVED=True, COMPLETED=True.

Refinement.md audit: legs are R/A-reference/I (no kind-3, no A-consumed): op#1 params R, op#2 basename A-reference (deep POSIX model, G-CONF-validated), op#3 special-case I, op#4 ambient-independence frame R. A-reference correspondence verified: basename model = (·.split (·='/')).reverse.headI matches os.path.basename exactly across boundary set {'a/b','a/','/','','__main__.py','/usr/bin/x','a/b/','x','/a/b/__main__.py'} (0 mismatches). axiom_check.py legitimate skip (no consumed axioms). Grep of Solution.lean: no axiom/opaque/sorry/_prop declarations (only the explanatory comment). The spec correctly forces functional equality to gold; the ambient universal quantifier kills the prepatch and all ungrounded variants.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_no_special.lean`, `atk_3_swap_cond.lean`, `atk_4_second_arg.lean`, `atk_5_no_basename.lean`, `atk_6_const.lean`, `atk_7_wrong_const.lean`, `atk_8_empty.lean` |

**Non-vacuity.** The positive control `pc_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_no_special.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_swap_cond.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_second_arg.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_no_basename.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_const.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7_wrong_const.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8_empty.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Determining the program name presented by a command-line utility.

A command-line utility is invoked with an argument vector whose first entry is
the path under which the program was launched. The utility presents a program
name to the user (for example, in the usage banner of its option parser). That
program name is defined to be:

* the final path component of the utility's own first argument, and
* a constant textual name (`python -m django`) in the special case where that
  final component is the module-execution entry point `__main__.py`.

The key property is that the presented program name is a function of the
utility's own argument vector alone. It does not depend on any ambient,
process-global argument vector: two invocations with the same utility argument
vector present the same program name regardless of the surrounding process
state.

Argument vectors are modeled as `List String` (one element per argument);
individual arguments are modeled as `String`. Path components are separated by
`'/'`, matching POSIX path semantics.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The two operations the behavior
-- relies on — extracting the final path component of a string and the constant
-- module-execution special case — are modeled deeply below (`basename` /
-- `computeProgName`), so there is no opaque callee signature and no consumed
-- `_prop` axiom. The deep model is validated against the real implementation by
-- the conformance check.
-- axioms-end

-- pure-start
/-- The final path component of a string: everything after the last `'/'`
separator (the whole string when there is no separator; the empty string when
the string ends in a separator). Models POSIX basename. -/
def basename (s : String) : String :=
  (s.split (· = '/')).reverse.headI

/-- The program name derived from a single argument (the utility's first
argument): the final path component, except that the module-execution entry
point maps to a constant textual name. -/
def computeProgName (arg0 : String) : String :=
  let b := basename arg0
  if b = "__main__.py" then "python -m django" else b
-- pure-end

-- post-conditions-start
/-- The presented program name is exactly the name derived from the utility's
own argument vector. The specification mentions only the utility's own argument
vector, and never the ambient one: this pins the result to be independent of any
ambient argument vector. -/
def problem_spec_progName (argv : List String) (result : String) : Prop :=
  result = computeProgName argv.headI
-- post-conditions-end

-- impl-start
def implementation_progName (argv : List String) (_ambient : List String) : String :=
  Id.run do
    -- Derive the program name from the utility's OWN argument vector, applying
    -- the module-execution special case. The ambient argument vector is not
    -- consulted.
    let mut progName := basename argv.headI
    if progName = "__main__.py" then
      progName := "python -m django"
    return progName
-- impl-end

-- proof-start
theorem correct_progName :
    ∀ (argv ambient : List String), argv ≠ [] →
      problem_spec_progName argv (implementation_progName argv ambient) := by
  intro argv ambient _
  unfold problem_spec_progName implementation_progName computeProgName
  by_cases h : basename argv.headI = "__main__.py" <;>
    simp only [Id.run, bind, pure, h, if_true, if_false]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec = total functional equality over fully-grounded defs (no axioms/opaque/_prop): correct_progName requires implementation_progName argv ambient = computeProgName argv.headI for ALL argv≠[] and ALL ambient. same_spec elides impl+proof; head (imports/docstring/axioms/pure basename+computeProgName/post-conditions) kept byte-identical => same_spec=True verified for all 8 attacks + PC via markers.same_spec (get_backend('lean')).

8 DISTINCT same-spec wrong impls (all with the GENUINE fixed obligation): atk_1 prepatch bug (basename _ambient.headI, ungrounded on argv); atk_2 partial-domain (drops __main__.py special case); atk_3 control-flow-effect (negated condition, wrong branch); atk_4 boundary/off-by-one (argv.getD 1 not headI); atk_5 missing basename (raw arg0, wrong when path has '/'); atk_6 ungrounded-oracle echo (const 'python -m django'); atk_7 wrong special-case constant; atk_8 empty string. Command: `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch. Results: PC pc_gold.lean EXIT=0 (verifies); ALL 8 attacks EXIT=1 'unsolved goals' (genuine false statements).

Additionally threw aggressive automation (simp_all with all defs unfolded, decide) at the two most plausible wrong impls (hard_1=prepatch, hard_2=no_special): both EXIT=1 — unprovable, as Lean soundness requires for a false total-equality statement. Because ZERO wrong impls close with clean axioms, there is NO verifying-but-wrong impl to materialize+resolve (resolve obligation vacuously satisfied — verify⇏correct not exhibitable). PC axioms clean: `#print axioms correct_progName` => depends on [propext] only (no sorryAx/Classical.choice misuse). Pipeline positive control: gold patch.diff run through official harness run_resolve('django__django-13658') => RESOLVED=True, COMPLETED=True.

Refinement.md audit: legs are R/A-reference/I (no kind-3, no A-consumed): op#1 params R, op#2 basename A-reference (deep POSIX model, G-CONF-validated), op#3 special-case I, op#4 ambient-independence frame R. A-reference correspondence verified: basename model = (·.split (·='/')).reverse.headI matches os.path.basename exactly across boundary set {'a/b','a/','/','','__main__.py','/usr/bin/x','a/b/','x','/a/b/__main__.py'} (0 mismatches). axiom_check.py legitimate skip (no consumed axioms). Grep of Solution.lean: no axiom/opaque/sorry/_prop declarations (only the explanatory comment). The spec correctly forces functional equality to gold; the ambient universal quantifier kills the prepatch and all ungrounded variants.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independent verification. Real callee at base_commit 0773837e15 (django/core/management/__init__.py:188-192): self.prog_name = os.path.basename(self.argv[0]) with __main__.py -> 'python -m django'; fix threads prog=self.prog_name into CommandParser in execute() (~:347), making the presented name a function of the utility's OWN argv, ambient-independent. Model: basename s = (s.split (·='/')).reverse.headI; computeProgName applies the special case. FAITHFULNESS EVIDENCE: (1) Lean basename evaluated directly via lean_verify (#eval) matches POSIX os.path.basename on all boundary cases ('', '/', 'a/', 'a/b/c'->c, 'a//b'->b, '__main__.py', 'a/__main__.py'->python -m django, '//'->''). (2) Python shadow of basename vs os.path.basename over 200k random strings (chars incl '/','\\',spaces): 0 mismatches. (3) Full model computeProgName(argv[0]) vs real ManagementUtility(argv).prog_name (sys.argv mocked to unrelated vectors) over 50k fuzzed inputs: 0 mismatches. (4) same_spec(Solution,prepatch)=True (spec region byte-identical). (5) Solution.lean compiles exit 0; #print axioms correct_progName -> [propext] only (no sorryAx). Model is POSIX-only which matches repo test env. Precondition argv != [] correctly captures unconditional self.argv[0] indexing. No diverging input found on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage assessed against the PUBLIC problem_statement only (hints excluded). Mechanical G-LEAK screen passes (leakage.screen -> passed=True, no hard failures); same_spec(prepatch, patched) = True (spec region byte-identical, only impl/proof legs differ). Every fact the spec view discloses is already stated verbatim in the public problem_statement: it quotes `self.prog_name = os.path.basename(self.argv[0])` (the basename-of-argv[0] computation -> Lean `basename`/`computeProgName`), the `if self.prog_name == '__main__.py': self.prog_name = 'python -m django'` special case (-> the `__main__.py` -> "python -m django" branch), and names the bug + fix directly ("%(prog)s refers to sys.argv[0] ... it should refer to self.prog_name", plus the exact `prog=self.prog_name` edit). The spec view's discriminating content -- ambient-independence frame (result is a function of the utility's own argv, never the process-global sys.argv) -- is exactly the problem statement's thesis. The Lean formalization (List String modeling, POSIX '/' basename semantics) only re-expresses already-public facts and reveals nothing about the gold edit beyond what the problem statement itself states. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).