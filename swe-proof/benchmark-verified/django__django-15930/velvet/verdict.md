# P2 adversarial audit — django__django-15930

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,8 +66,7 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
-    return branchClause effCond res
+    return branchClause cond res
     -- impl-end
 
 prove_correct assembleConditionalBranch by
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,8 +66,7 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
-    return branchClause effCond res
+    return branchClause truePredicate res
     -- impl-end
 
 prove_correct assembleConditionalBranch by
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,7 +66,7 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
+    let effCond : Compiled := if cond.sql ≠ [] then truePredicate else cond
     return branchClause effCond res
     -- impl-end
 
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,7 +66,7 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
+    let effCond : Compiled := if cond.sql = [] then { sql := "%s".toList, params := [] } else cond
     return branchClause effCond res
     -- impl-end
 
```

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,7 +66,7 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
+    let effCond : Compiled := if cond.sql = [] then { sql := "TRUE".toList, params := [1] } else cond
     return branchClause effCond res
     -- impl-end
 
```

Attack 6 — `atk6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,7 +66,7 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
+    let effCond : Compiled := if cond.sql.length = 0 then truePredicate else cond
     return branchClause effCond res
     -- impl-end
 
```

Attack 7 — `atk7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,8 +66,9 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
-    return branchClause effCond res
+    match cond.sql with
+    | [] => return branchClause truePredicate res
+    | _  => return branchClause cond res
     -- impl-end
 
 prove_correct assembleConditionalBranch by
```

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

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
 -- (No consumed axioms. The always-true predicate that the empty-condition case
@@ -66,7 +66,7 @@
   ensures cond.sql = []  → out = branchClause truePredicate res
   do
     -- impl-start
-    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
+    let effCond : Compiled := if cond.sql = [] then { sql := cond.sql, params := [1] } else cond
     return branchClause effCond res
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
-- (No consumed axioms. The always-true predicate that the empty-condition case
--  falls back to is modeled DEEPLY as its concrete compiled form — a constant,
--  non-empty placeholder fragment binding one literal-true parameter. That form
--  is validated == the real callee out-of-band by axiom_check.py (G-AX) as an
--  A-reference, not consumed here.)
-- axioms-end

-- pure-start
/- A compiled SQL fragment: the fragment text together with the ordered list of
   parameters it binds. Both an incoming branch condition and the always-true
   substitute are carried in this one shape. Text is modeled per byte as
   `List Char`; a bound parameter is carried by an integer identity
   (mapping.md §2). -/
structure Compiled where
  sql : List Char
  params : List Int
  deriving DecidableEq

/- The compiled form of the always-true predicate the branch falls back to when
   its own condition compiles to nothing: a single non-empty placeholder
   fragment binding one literal-true parameter (the integer identity `1` carries
   the literal true, mapping.md §2). Concrete data, validated == the real callee
   by axiom_check.py (G-AX) as an A-reference. -/
def truePredicate : Compiled := { sql := "%s".toList, params := [1] }

/- Assemble one conditional branch from a compiled condition and a compiled
   consequent: the branch text splices both fragments into the constant
   "WHEN <condition> THEN <result>" template, and the branch binds the
   condition's parameters followed by the consequent's. -/
def branchClause (cond : Compiled) (res : Compiled) : Compiled :=
  { sql := "WHEN ".toList ++ cond.sql ++ " THEN ".toList ++ res.sql,
    params := cond.params ++ res.params }
-- pure-end

/- Assemble one conditional branch of a multi-branch selection expression from
   its already-compiled condition and consequent fragments.

   Desired behaviour: a condition that matches every row compiles to EMPTY
   fragment text. Splicing that empty text into the branch template would yield
   a branch with no predicate between the keywords — invalid syntax. So when the
   incoming condition's text is empty, the assembled branch must instead use a
   NON-EMPTY always-true predicate as its condition (text and bound parameters
   both taken from that predicate); a condition whose text is non-empty is used
   unchanged. The consequent fragment is always used as-is.

   The two input fragments are read-only (neither is `mut`); nothing is mutated
   (directive 5). -/
-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method assembleConditionalBranch (cond : Compiled) (res : Compiled)
    return (out : Compiled)
  ensures cond.sql ≠ [] → out = branchClause cond res
  ensures cond.sql = []  → out = branchClause truePredicate res
  do
    -- impl-start
    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
    return branchClause effCond res
    -- impl-end

prove_correct assembleConditionalBranch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. python=python, project root=. same_spec (velvet) = True for pos_control, atk_prepatch, and all 8 attacks.

### VERIFY (bash scripts/lean_verify.sh <file>, run concurrently in batches of 4):
- pos_control.lean EXIT=0 (verifies) — positive control.
- atk_prepatch.lean EXIT=1; atk1 EXIT=1 (prepatch bug/partial-domain: correct only for non-empty cond); atk2 EXIT=1 (always truePredicate, wrong on non-empty); atk3 EXIT=1 (inverted '≠[]' control-flow); atk4 EXIT=1 (ungrounded-oracle echo: substitute params:=[]); atk5 EXIT=1 (boundary/text: substitute sql='TRUE' not '%s'); atk8 EXIT=1 (control-flow-effect: partial substitution, keeps empty sql). All 7 wrong impls FAIL to verify — each unsolved goal is exactly the cond.sql=[] -> out=branchClause truePredicate res clause (confirmed in atk1/atk4 error text).
- atk6.lean EXIT=0 and atk7.lean EXIT=0 VERIFY. These are behaviorally-correct ECHOES: atk6 tests 'cond.sql.length = 0' and atk7 pattern-matches 'match cond.sql | [] | _', both provably equivalent to 'cond.sql = []' under the R bijection ("" <-> []). The spec postcondition is TOTAL and FUNCTIONAL (uniquely pins out on both domain halves), so any verifying impl equals gold.

MANDATORY RESOLVE (official harness): the faithful refined patch of both verifying echoes is exactly the gold insertion (empty-condition -> compiler.compile(Value(True))). Ran run_resolve('django__django-15930', <faithful patch>) => RESOLVED=True, COMPLETED=True. Faithful patch saved at faithful_patch_gold.diff. No verifying wrong impl produces a non-resolving faithful patch.

refinement.md audit: legs A1=R, A2=R, A3=A-reference+I, A4=I+R. No kind-3 (inexpressible-changed-op). The sole A-reference truePredicate={sql:="%s".toList, params:=[1]} <-> compiler.compile(Value(True)) is validated by axiom_check.py against the real callee (Value.as_sql -> ("%s",[True]); non-empty, one literal-true param). Correspondence holds; the changed op is modeled deeply, not axiomatized. R/I legs are G-CONF's remit.

Conclusion: verify => correct on this bundle; no falsification found across 6 distinct wrong impls + prepatch + 2 verifying echoes whose materialized faithful patch resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk5.lean`, `atk8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk6.lean`, `atk7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The always-true predicate that the empty-condition case
--  falls back to is modeled DEEPLY as its concrete compiled form — a constant,
--  non-empty placeholder fragment binding one literal-true parameter. That form
--  is validated == the real callee out-of-band by axiom_check.py (G-AX) as an
--  A-reference, not consumed here.)
-- axioms-end

-- pure-start
/- A compiled SQL fragment: the fragment text together with the ordered list of
   parameters it binds. Both an incoming branch condition and the always-true
   substitute are carried in this one shape. Text is modeled per byte as
   `List Char`; a bound parameter is carried by an integer identity
   (mapping.md §2). -/
structure Compiled where
  sql : List Char
  params : List Int
  deriving DecidableEq

/- The compiled form of the always-true predicate the branch falls back to when
   its own condition compiles to nothing: a single non-empty placeholder
   fragment binding one literal-true parameter (the integer identity `1` carries
   the literal true, mapping.md §2). Concrete data, validated == the real callee
   by axiom_check.py (G-AX) as an A-reference. -/
def truePredicate : Compiled := { sql := "%s".toList, params := [1] }

/- Assemble one conditional branch from a compiled condition and a compiled
   consequent: the branch text splices both fragments into the constant
   "WHEN <condition> THEN <result>" template, and the branch binds the
   condition's parameters followed by the consequent's. -/
def branchClause (cond : Compiled) (res : Compiled) : Compiled :=
  { sql := "WHEN ".toList ++ cond.sql ++ " THEN ".toList ++ res.sql,
    params := cond.params ++ res.params }
-- pure-end

/- Assemble one conditional branch of a multi-branch selection expression from
   its already-compiled condition and consequent fragments.

   Desired behaviour: a condition that matches every row compiles to EMPTY
   fragment text. Splicing that empty text into the branch template would yield
   a branch with no predicate between the keywords — invalid syntax. So when the
   incoming condition's text is empty, the assembled branch must instead use a
   NON-EMPTY always-true predicate as its condition (text and bound parameters
   both taken from that predicate); a condition whose text is non-empty is used
   unchanged. The consequent fragment is always used as-is.

   The two input fragments are read-only (neither is `mut`); nothing is mutated
   (directive 5). -/
-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method assembleConditionalBranch (cond : Compiled) (res : Compiled)
    return (out : Compiled)
  ensures cond.sql ≠ [] → out = branchClause cond res
  ensures cond.sql = []  → out = branchClause truePredicate res
  do
    -- impl-start
    let effCond : Compiled := if cond.sql = [] then truePredicate else cond
    return branchClause effCond res
    -- impl-end

prove_correct assembleConditionalBranch by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. python=python, project root=. same_spec (velvet) = True for pos_control, atk_prepatch, and all 8 attacks.

### VERIFY (bash scripts/lean_verify.sh <file>, run concurrently in batches of 4):
- pos_control.lean EXIT=0 (verifies) — positive control.
- atk_prepatch.lean EXIT=1; atk1 EXIT=1 (prepatch bug/partial-domain: correct only for non-empty cond); atk2 EXIT=1 (always truePredicate, wrong on non-empty); atk3 EXIT=1 (inverted '≠[]' control-flow); atk4 EXIT=1 (ungrounded-oracle echo: substitute params:=[]); atk5 EXIT=1 (boundary/text: substitute sql='TRUE' not '%s'); atk8 EXIT=1 (control-flow-effect: partial substitution, keeps empty sql). All 7 wrong impls FAIL to verify — each unsolved goal is exactly the cond.sql=[] -> out=branchClause truePredicate res clause (confirmed in atk1/atk4 error text).
- atk6.lean EXIT=0 and atk7.lean EXIT=0 VERIFY. These are behaviorally-correct ECHOES: atk6 tests 'cond.sql.length = 0' and atk7 pattern-matches 'match cond.sql | [] | _', both provably equivalent to 'cond.sql = []' under the R bijection ("" <-> []). The spec postcondition is TOTAL and FUNCTIONAL (uniquely pins out on both domain halves), so any verifying impl equals gold.

MANDATORY RESOLVE (official harness): the faithful refined patch of both verifying echoes is exactly the gold insertion (empty-condition -> compiler.compile(Value(True))). Ran run_resolve('django__django-15930', <faithful patch>) => RESOLVED=True, COMPLETED=True. Faithful patch saved at faithful_patch_gold.diff. No verifying wrong impl produces a non-resolving faithful patch.

refinement.md audit: legs A1=R, A2=R, A3=A-reference+I, A4=I+R. No kind-3 (inexpressible-changed-op). The sole A-reference truePredicate={sql:="%s".toList, params:=[1]} <-> compiler.compile(Value(True)) is validated by axiom_check.py against the real callee (Value.as_sql -> ("%s",[True]); non-empty, one literal-true param). Correspondence holds; the changed op is modeled deeply, not axiomatized. R/I legs are G-CONF's remit.

Conclusion: verify => correct on this bundle; no falsification found across 6 distinct wrong impls + prepatch + 2 verifying echoes whose materialized faithful patch resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / drift): no divergence found; the modeled function agrees with the real repo callee on all inputs within the documented modeling boundary.

SPEC REGION BYTE-IDENTITY: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend)=True. The frozen spec (structure Compiled, truePredicate, branchClause, and the two ensures clauses) is identical between Solution and its prepatch pair; only the impl region differs. The prepatch impl (return branchClause cond res, no empty-condition substitution) fails the second ensures, confirming the spec is discriminating (G-DIFF sound).

LEAN VERIFY: scripts/lean_verify.sh on Solution.lean -> exit 0 (elaborates, no sorry/error); prove_correct genuinely discharges both ensures.

### MODEL vs REAL REPO (When.as_sql, django/db/models/expressions.py post-patch, base_commit 63884829):
- ensures cond.sql ≠ [] → out = branchClause cond res  ⇔ unchanged path: non-empty condition_sql spliced directly, params forwarded in order.
- ensures cond.sql = [] → out = branchClause truePredicate res  ⇔ inserted hunk: if condition_sql == "": condition_sql, condition_params = compiler.compile(Value(True)). The real code REPLACES both text AND params (discards original condition_params); the model likewise uses truePredicate.sql/params, discarding cond.params. Faithful.
- A-reference truePredicate = {sql := "%s".toList, params := [1]}: I executed the real repo at base_commit (SQLCompiler.compile(Value(True).resolve_expression(q))) -> ('%s', [True]). Exact match under mapping.md §2 bijection (True ↔ integer identity 1; str ↔ List Char; "" ↔ []).
- branchClause splice: Python named %(condition)s/%(result)s formatting is a pure substitution (verified values containing '%' are NOT re-interpreted), matching branchClause's literal '++' concatenation. Param order cond.params ++ res.params matches the two sequential sql_params.extend calls.

CONFORMANCE: conformance_check.py (seed 15930) agrees SHADOW==ORACLE on 100,006 fuzzed fragment pairs incl. the empty-condition boundary, 0 disagreements.

MODELING BOUNDARY (documented, not a defect): the modeled call path is default template=None and extra_context={} (the F2P Case/When path). Custom template / extra_context overrides are out of scope per mapping.md §2/§3.3 and are not exercised by the issue scenario, so this is a legitimate scoping, not spec drift. Within this domain the spec is neither too strong nor divergent.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: in When.as_sql, when condition_sql == "" substitute compiler.compile(Value(True)) — an empty (match-everything) condition falls back to an always-true predicate in the WHEN/THEN template. The public problem_statement already exposes every discriminating element of this fix: the broken SQL 'CASE WHEN THEN True ELSE False END' (empty WHEN condition), that ~Q(pk__in=[]) is a match-everything sentinel, the reproduction literally using then=Value(True), and the stated expected behavior 'annotate all rows with the value True since they all match' (i.e. always-true). None of this relies on hints_text.

Spec-view content maps 1:1 to the public issue and adds nothing gold-specific: branchClause = the WHEN/THEN template shown verbatim in the issue; cond.sql = [] trigger = the public 'WHEN THEN' empty-condition symptom; ensures cond.sql = [] → out = branchClause truePredicate res = the public 'all rows match / True' expectation; truePredicate = {sql := "%s".toList, params := [1]} models the compiled form of the UNCHANGED stdlib callee Value(True).as_sql (Value(True) itself appears in the public repro). The docstring rationale paraphrases the general symptom/expectation, not gold-patch specifics. No file:line references, no verbatim gold code/comment quoted in the spec view, no identifier beyond the public issue.

Mechanical corroboration: spec_view generated via velvet backend; leakage.screen(src, 'velvet', patch, problem_statement) → passed=True, hard_failures=[] . meta.json G-LEAK status='pass' ('spec view clean'); relaxed_leakage unset and no RELAXED_LEAKAGE.md (so this is a genuine clean pass, not a deferred relaxation). same_spec(Solution.lean, Solution_prepatch.lean)=True and the two spec views are byte-identical — the spec region is stable across pre/post patch (only impl/proof differ). A reader of the spec learns only what the public problem statement already conveys.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
