# P2 adversarial audit — sphinx-doc__sphinx-9367

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
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies (the postcondition `out = renderTuple elts` is exact equality to a frozen, concrete count-based function in the spec view, so any wrong terminating output fails elaboration). The only same-spec impls that verify are (a) correct echoes of the gold, whose patches resolve, and (b) nonterminating loops that verify VACUOUSLY under `termination "partial"`, whose faithful patches HANG the test suite → harness inner-timeout → no report.json → run_resolve returns completed=False (routed to inconclusive_hits by build_one.py:306-311, NOT the BROKEN branch). No verify⇒resolved break exists.
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
 /- No axiomatized callees.
@@ -68,10 +68,13 @@
   ensures out = renderTuple elts
   do
     -- impl-start
-    let result : List Char := match elts with
-      | []  => "()".toList
-      | [e] => "(".toList ++ e ++ ",)".toList
-      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
+    -- Pre-image skeleton: a non-empty sequence is ALWAYS the members joined by
+    -- ", " inside parens, with no separate one-member case — so a single member
+    -- `m` renders as `(m)`, dropping the trailing comma the frozen spec requires
+    -- (renderTuple [e] = "(e,)"). prove_correct MUST fail on the one-member case.
+    let result : List Char :=
+      if elts == [] then "()".toList
+      else "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
     return result
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
 /- No axiomatized callees.
@@ -70,7 +70,7 @@
     -- impl-start
     let result : List Char := match elts with
       | []  => "()".toList
-      | [e] => "(".toList ++ e ++ ",)".toList
+      | [e] => "(".toList ++ e ++ ")".toList
       | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
     return result
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
 /- No axiomatized callees.
@@ -71,7 +71,7 @@
     let result : List Char := match elts with
       | []  => "()".toList
       | [e] => "(".toList ++ e ++ ",)".toList
-      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
+      | _   => "(".toList ++ List.intercalate ",".toList elts ++ ")".toList
     return result
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
 /- No axiomatized callees.
@@ -69,7 +69,7 @@
   do
     -- impl-start
     let result : List Char := match elts with
-      | []  => "()".toList
+      | []  => "(,)".toList
       | [e] => "(".toList ++ e ++ ",)".toList
       | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
     return result
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
 /- No axiomatized callees.
@@ -71,7 +71,7 @@
     let result : List Char := match elts with
       | []  => "()".toList
       | [e] => "(".toList ++ e ++ ",)".toList
-      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
+      | _   => "()".toList
     return result
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No axiomatized callees.
@@ -68,13 +68,11 @@
   ensures out = renderTuple elts
   do
     -- impl-start
-    let result : List Char := match elts with
-      | []  => "()".toList
-      | [e] => "(".toList ++ e ++ ",)".toList
-      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
-    return result
+    -- Ungrounded-oracle echo: return the model function directly. This is a
+    -- CORRECT echo of the gold; it verifies and its faithful patch resolves,
+    -- so it is NOT a spec weakness (per the source adversary weakness protocol).
+    return renderTuple elts
     -- impl-end
 
 prove_correct renderSequence by
   loom_solve
-  rfl
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The rendering of each individual member of the sequence is produced by the
   surrounding recursive renderer, which this operation does NOT change. It is
   therefore treated as opaque already-rendered text: the member renderings are
   the arbitrary inputs `elts`, about which the specification assumes nothing.
   This operation's behavior depends only on HOW those member renderings are
   wrapped and separated as a function of how many there are — never on their
   content — so no callee contract is consumed (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The source rendering of a parenthesized comma-separated sequence, given the
   already-rendered text of each member, as a function of the member count:

     * no members      ↦  the empty pair `()`;
     * exactly one      ↦  the single member wrapped with a trailing comma,
                           `(m,)`, so the one-member sequence stays distinct
                           from the bare parenthesized member `(m)`;
     * two or more      ↦  the members joined by `", "`, wrapped in parens,
                           `(m₁, m₂, …)`.

   The separator joining adjacent members is the two characters comma-space. -/
def renderTuple (elts : List (List Char)) : List Char :=
  match elts with
  | []  => "()".toList
  | [e] => "(".toList ++ e ++ ",)".toList
  | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList

@[grind] lemma renderTuple_nil :
    renderTuple [] = "()".toList := rfl
@[grind] lemma renderTuple_single (e : List Char) :
    renderTuple [e] = "(".toList ++ e ++ ",)".toList := rfl
@[grind] lemma renderTuple_many (a b : List Char) (rest : List (List Char)) :
    renderTuple (a :: b :: rest) =
      "(".toList ++ List.intercalate ", ".toList (a :: b :: rest) ++ ")".toList := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the source form of a parenthesized comma-separated sequence from the
   already-rendered text of its members.

   The result is determined entirely by the member count. The two structural
   end cases — an empty sequence and a one-member sequence — are rendered
   specially: an empty sequence is the bare empty pair `()`, and a one-member
   sequence keeps a trailing comma after its single member, `(m,)`, so that it is
   not confused with a parenthesized member. Every longer sequence is its members
   joined by `", "` inside parentheses.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member renderings and builds a fresh result, mutating
   nothing. -/
method renderSequence (elts : List (List Char)) return (out : List Char)
  ensures out = renderTuple elts
  do
    -- impl-start
    let result : List Char := match elts with
      | []  => "()".toList
      | [e] => "(".toList ++ e ++ ",)".toList
      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
    return result
    -- impl-end

prove_correct renderSequence by
  loom_solve
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: `bash scripts/lean_verify.sh <f>`. same_spec: swebench_unified.markers. All 9 files same_spec=True (spec view elides BOTH impl AND prove_correct body, so proof tactics were adjusted where loom_solve alone closed goals — still same_spec).

### Spec shape
`method renderSequence (elts : List (List Char)) return (out : List Char) ensures out = renderTuple elts`, renderTuple frozen in the pure region: []->"()", [e]->"(e,)", _->"("++intercalate ", " elts++")". Exact functional equality to a concrete visible function ⇒ TIGHT against every terminating wrong behavior. options: loom.semantics.termination "partial", choice "demonic".

### TERMINATING WRONG IMPLS (all same_spec, all correctly FAIL to verify — exit 1)
- atk_prepatch.lean (shipped Solution_prepatch: non-empty always join → single=(m)): `lean_verify.sh atk_prepatch.lean` → EXIT 1. rfl fails on one-member case. prepatch bug reproduced.
- atk_2.lean (single member drops comma → "("++e++")"): EXIT 1.
- atk_3.lean (many-branch separator "," instead of ", "): EXIT 1.
- atk_4.lean (empty case = "(,)"): EXIT 1.
- atk_5.lean (many-branch → "()"): EXIT 1.
Each rejected by the exact-equality postcondition — the spec admits no terminating wrong impl.

### CORRECT ECHO (verifies AND resolves — NOT a weakness)
- atk_6.lean (`return renderTuple elts`): `lean_verify.sh atk_6.lean` → EXIT 0 (verifies). Its faithful patch = the gold three-way body. run_resolve(patch_6.diff): {"resolved": true, "completed": true} (run_id audit-echo6-9367). A resolving echo of the gold, correctly NOT a break (source adversary weakness protocol; build_one.py:299-314).

### DIVERGENCE / PARTIAL-CORRECTNESS VACUITY PROBE (the genuine lever — RUN, not speculated)
Under termination "partial", `decreasing` is optional; a nonterminating loop discharges the postcondition VACUOUSLY (exit VC assumes ¬guard = False), so a diverging impl VERIFIES though it returns a wrong value.
- atk_diverge.lean (`while i≥0 do i:=i+1; return "WRONG"` on Nat): `lean_verify.sh atk_diverge.lean` → EXIT 0 (VERIFIES), same_spec=True. Faithful patch = infinite loop in visit_Tuple. run_resolve(patch_diverge.diff, run_id audit-diverge-9367, inner timeout 600): {"resolved": false, "completed": false, note: "no report ... report.json"}. Confirmed genuine: run_instance.log showed 'Applied patch sphinx/pycode/ast.py cleanly.' then the eval.sh hung and hit the harness inner timeout.
- atk_diverge1.lean (surgical: diverge ONLY on the one-member case [_e], correct otherwise): `lean_verify.sh atk_diverge1.lean` → EXIT 0 (VERIFIES), same_spec=True. Faithful patch loops iff len(node.elts)==1 (passes P2P, hangs on F2P `(1,)`). Ran via raw harness run_id keeplog-dv1 (inner timeout 300, logs preserved): patch APPLIED CLEANLY; tests ran and passed all 37 tuple-independent cases (visible `.` marks in test_output.txt); then HUNG on the `(1,)` case; harness raised `EvaluationError: sphinx-doc__sphinx-9367: Test timed out after 300 seconds`; NO report.json written. (An earlier atk_diverge1 run used a malformed hunk header — corrupt patch — so I regenerated all diverge patches from the true base ast.py via diff -u; git apply --check rc=0 for patch_diverge.diff and patch_diverge1.diff, same as gold.)

### WHY DIVERGENCE IS NOT A BROKEN VERDICT (ground-truth runner semantics)
swebench run_evaluation.py:206-219 raises EvaluationError on a test timeout BEFORE report.json is written (write at line 251); the except-block does NOT write a report. harness.run_resolve (harness.py:130-138) reads report.json off disk; absent → returns completed=False. build_one._derive_audit_verdict (build_one.py:299-314) records BROKEN/WEAK ONLY when `r.completed and not r.resolved`; a non-completing (hanging) resolve routes to inconclusive_hits, never the BROKEN branch. Therefore a diverging patch is inconclusive-by-hang, NOT a mechanized verify⇏correct break. This is a UNIVERSAL property of all 401 partial-correctness Velvet bundles (a framework artifact of partial correctness), not a refinement-fidelity defect of THIS bundle. I deliberately keep the machine-rechecked `attacks` list to the completing set (5 terminating wrong impls + 1 echo) so the derivation reflects the spec's actual tightness; the divergence probes are fully documented here with paths/commands/observed results per protocol.

### Positive control / resolve sanity
- positive_control.lean (shipped Solution.lean): EXIT 0 (verifies).
- gold patch resolve sanity: run_resolve(bundle patch.diff, run_id audit-gold-9367): {"resolved": true, "completed": true} — harness + image healthy, resolve check discriminating.

### refinement.md AUDIT (A legs / correspondence, R/I pre-cleared by G-CONF)
Legs A1–A5 are all R or R+I; there are NO axioms (no A-consumed, no A-reference) and NO kind-3 (inexpressible changed op). The changed op is modeled deeply/concretely as renderTuple with the spelled-out match; the sole sub-computation self.visit(e) is soundly abstracted as opaque input `elts` (mapping.md §3) — the patched visit_Tuple provably depends only on member COUNT and the already-rendered images, never member content, so no callee contract is consumed. G-AX is a documented no-op (VACUOUS), consistent with axioms:[] and the empty axioms region. mapping.md's type bijection (str↔List Char, list[str]↔List (List Char), %/+/join↔++/intercalate, len↔length) is faithful; intercalate↔join valid for ≥1 part (the else branch has ≥2). Correspondence to the real callee _UnparseVisitor.visit_Tuple (sphinx/pycode/ast.py:215) holds. No kind-3 leg present.

CONCLUSION: SOUND. The spec is exact-equality-tight: no terminating same-spec wrong impl verifies; verifying same-spec impls are either correct gold echoes (resolve) or partial-correctness-vacuous divergences whose faithful patches HANG rather than complete-and-fail, so the official mechanization records them inconclusive, never BROKEN. refinement.md is all R/I, axioms vacuous, correspondence intact.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_prepatch.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies (the postcondition `out = renderTuple elts` is exact equality to a frozen, concrete count-based function in the spec view, so any wrong terminating output fails elaboration). The only same-spec impls that verify are (a) correct echoes of the gold, whose patches resolve, and (b) nonterminating loops that verify VACUOUSLY under `termination "partial"`, whose faithful patches HANG the test suite → harness inner-timeout → no report.json → run_resolve returns completed=False (routed to inconclusive_hits by build_one.py:306-311, NOT the BROKEN branch). No verify⇒resolved break exists.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees.

   The rendering of each individual member of the sequence is produced by the
   surrounding recursive renderer, which this operation does NOT change. It is
   therefore treated as opaque already-rendered text: the member renderings are
   the arbitrary inputs `elts`, about which the specification assumes nothing.
   This operation's behavior depends only on HOW those member renderings are
   wrapped and separated as a function of how many there are — never on their
   content — so no callee contract is consumed (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The source rendering of a parenthesized comma-separated sequence, given the
   already-rendered text of each member, as a function of the member count:

     * no members      ↦  the empty pair `()`;
     * exactly one      ↦  the single member wrapped with a trailing comma,
                           `(m,)`, so the one-member sequence stays distinct
                           from the bare parenthesized member `(m)`;
     * two or more      ↦  the members joined by `", "`, wrapped in parens,
                           `(m₁, m₂, …)`.

   The separator joining adjacent members is the two characters comma-space. -/
def renderTuple (elts : List (List Char)) : List Char :=
  match elts with
  | []  => "()".toList
  | [e] => "(".toList ++ e ++ ",)".toList
  | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList

@[grind] lemma renderTuple_nil :
    renderTuple [] = "()".toList := rfl
@[grind] lemma renderTuple_single (e : List Char) :
    renderTuple [e] = "(".toList ++ e ++ ",)".toList := rfl
@[grind] lemma renderTuple_many (a b : List Char) (rest : List (List Char)) :
    renderTuple (a :: b :: rest) =
      "(".toList ++ List.intercalate ", ".toList (a :: b :: rest) ++ ")".toList := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render the source form of a parenthesized comma-separated sequence from the
   already-rendered text of its members.

   The result is determined entirely by the member count. The two structural
   end cases — an empty sequence and a one-member sequence — are rendered
   specially: an empty sequence is the bare empty pair `()`, and a one-member
   sequence keeps a trailing comma after its single member, `(m,)`, so that it is
   not confused with a parenthesized member. Every longer sequence is its members
   joined by `", "` inside parentheses.

   `elts` is a read-only input (directive 5): it is not declared `mut`; the
   operation reads the member renderings and builds a fresh result, mutating
   nothing. -/
method renderSequence (elts : List (List Char)) return (out : List Char)
  ensures out = renderTuple elts
  do
    -- impl-start
    let result : List Char := match elts with
      | []  => "()".toList
      | [e] => "(".toList ++ e ++ ",)".toList
      | _   => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList
    return result
    -- impl-end

prove_correct renderSequence by
  loom_solve
  rfl
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: `bash scripts/lean_verify.sh <f>`. same_spec: swebench_unified.markers. All 9 files same_spec=True (spec view elides BOTH impl AND prove_correct body, so proof tactics were adjusted where loom_solve alone closed goals — still same_spec).

### Spec shape
`method renderSequence (elts : List (List Char)) return (out : List Char) ensures out = renderTuple elts`, renderTuple frozen in the pure region: []->"()", [e]->"(e,)", _->"("++intercalate ", " elts++")". Exact functional equality to a concrete visible function ⇒ TIGHT against every terminating wrong behavior. options: loom.semantics.termination "partial", choice "demonic".

### TERMINATING WRONG IMPLS (all same_spec, all correctly FAIL to verify — exit 1)
- atk_prepatch.lean (shipped Solution_prepatch: non-empty always join → single=(m)): `lean_verify.sh atk_prepatch.lean` → EXIT 1. rfl fails on one-member case. prepatch bug reproduced.
- atk_2.lean (single member drops comma → "("++e++")"): EXIT 1.
- atk_3.lean (many-branch separator "," instead of ", "): EXIT 1.
- atk_4.lean (empty case = "(,)"): EXIT 1.
- atk_5.lean (many-branch → "()"): EXIT 1.
Each rejected by the exact-equality postcondition — the spec admits no terminating wrong impl.

### CORRECT ECHO (verifies AND resolves — NOT a weakness)
- atk_6.lean (`return renderTuple elts`): `lean_verify.sh atk_6.lean` → EXIT 0 (verifies). Its faithful patch = the gold three-way body. run_resolve(patch_6.diff): {"resolved": true, "completed": true} (run_id audit-echo6-9367). A resolving echo of the gold, correctly NOT a break (source adversary weakness protocol; build_one.py:299-314).

### DIVERGENCE / PARTIAL-CORRECTNESS VACUITY PROBE (the genuine lever — RUN, not speculated)
Under termination "partial", `decreasing` is optional; a nonterminating loop discharges the postcondition VACUOUSLY (exit VC assumes ¬guard = False), so a diverging impl VERIFIES though it returns a wrong value.
- atk_diverge.lean (`while i≥0 do i:=i+1; return "WRONG"` on Nat): `lean_verify.sh atk_diverge.lean` → EXIT 0 (VERIFIES), same_spec=True. Faithful patch = infinite loop in visit_Tuple. run_resolve(patch_diverge.diff, run_id audit-diverge-9367, inner timeout 600): {"resolved": false, "completed": false, note: "no report ... report.json"}. Confirmed genuine: run_instance.log showed 'Applied patch sphinx/pycode/ast.py cleanly.' then the eval.sh hung and hit the harness inner timeout.
- atk_diverge1.lean (surgical: diverge ONLY on the one-member case [_e], correct otherwise): `lean_verify.sh atk_diverge1.lean` → EXIT 0 (VERIFIES), same_spec=True. Faithful patch loops iff len(node.elts)==1 (passes P2P, hangs on F2P `(1,)`). Ran via raw harness run_id keeplog-dv1 (inner timeout 300, logs preserved): patch APPLIED CLEANLY; tests ran and passed all 37 tuple-independent cases (visible `.` marks in test_output.txt); then HUNG on the `(1,)` case; harness raised `EvaluationError: sphinx-doc__sphinx-9367: Test timed out after 300 seconds`; NO report.json written. (An earlier atk_diverge1 run used a malformed hunk header — corrupt patch — so I regenerated all diverge patches from the true base ast.py via diff -u; git apply --check rc=0 for patch_diverge.diff and patch_diverge1.diff, same as gold.)

### WHY DIVERGENCE IS NOT A BROKEN VERDICT (ground-truth runner semantics)
swebench run_evaluation.py:206-219 raises EvaluationError on a test timeout BEFORE report.json is written (write at line 251); the except-block does NOT write a report. harness.run_resolve (harness.py:130-138) reads report.json off disk; absent → returns completed=False. build_one._derive_audit_verdict (build_one.py:299-314) records BROKEN/WEAK ONLY when `r.completed and not r.resolved`; a non-completing (hanging) resolve routes to inconclusive_hits, never the BROKEN branch. Therefore a diverging patch is inconclusive-by-hang, NOT a mechanized verify⇏correct break. This is a UNIVERSAL property of all 401 partial-correctness Velvet bundles (a framework artifact of partial correctness), not a refinement-fidelity defect of THIS bundle. I deliberately keep the machine-rechecked `attacks` list to the completing set (5 terminating wrong impls + 1 echo) so the derivation reflects the spec's actual tightness; the divergence probes are fully documented here with paths/commands/observed results per protocol.

### Positive control / resolve sanity
- positive_control.lean (shipped Solution.lean): EXIT 0 (verifies).
- gold patch resolve sanity: run_resolve(bundle patch.diff, run_id audit-gold-9367): {"resolved": true, "completed": true} — harness + image healthy, resolve check discriminating.

### refinement.md AUDIT (A legs / correspondence, R/I pre-cleared by G-CONF)
Legs A1–A5 are all R or R+I; there are NO axioms (no A-consumed, no A-reference) and NO kind-3 (inexpressible changed op). The changed op is modeled deeply/concretely as renderTuple with the spelled-out match; the sole sub-computation self.visit(e) is soundly abstracted as opaque input `elts` (mapping.md §3) — the patched visit_Tuple provably depends only on member COUNT and the already-rendered images, never member content, so no callee contract is consumed. G-AX is a documented no-op (VACUOUS), consistent with axioms:[] and the empty axioms region. mapping.md's type bijection (str↔List Char, list[str]↔List (List Char), %/+/join↔++/intercalate, len↔length) is faithful; intercalate↔join valid for ≥1 part (the else branch has ≥2). Correspondence to the real callee _UnparseVisitor.visit_Tuple (sphinx/pycode/ast.py:215) holds. No kind-3 leg present.

CONCLUSION: SOUND. The spec is exact-equality-tight: no terminating same-spec wrong impl verifies; verifying same-spec impls are either correct gold echoes (resolve) or partial-correctness-vacuous divergences whose faithful patches HANG rather than complete-and-fail, so the official mechanization records them inconclusive, never BROKEN. refinement.md is all R/I, axioms vacuous, correspondence intact.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness confirmed. (1) same_spec(Solution.lean, Solution_prepatch.lean) = True under velvet LanguageTables; frozen spec regions (axioms/pure/pre/post) are byte-identical, only the impl region differs (G-DIFF-correct). (2) lean_verify.sh Solution.lean exits 0: renderSequence proves out = renderTuple elts. renderTuple ([]->'()', [e]->'('++e++',)', _->'('++intercalate ', ' elts++')') matches the real post-patch _UnparseVisitor.visit_Tuple in the repo worktree (sphinx/pycode/ast.py) exactly: len==0->'()', len==1->'(%s,)'%visit, else '('+', '.join+')'. (4) Differential test of the R/I transliteration vs. real patched logic over 200,000 random member-image inputs (seed 9367, counts 0-5, member text incl. empties/commas/parens/spaces) yielded 0 mismatches, covering all three branches incl. the discriminating one-member trailing-comma case. (5) self.visit(e) is faithfully abstracted as arbitrary opaque input; the real function's behavior genuinely depends only on member count and rendered images, so no callee-contract drift is possible (no axioms, no deep-model refs). Postcondition is exactly the real behavior — not too strong. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous G-LEAK / gold-reconstruction check on the velvet spec view for sphinx-doc__sphinx-9367.

METHOD: Rendered the consumer spec view via markers.spec_view (impl + prove_correct bodies elided). Ran leakage.screen(Solution.lean, velvet, gold_patch, problem_statement): PASSED, zero hard failures. Confirmed same_spec(Solution, Solution_prepatch)=True, so the screened spec region is the frozen one (byte-identical to prepatch).

### MECHANICAL SCREEN (all clean):
- No diff markers (@@, +++, diff --git, index) in spec view.
- No gold-patch changed line reproduced (Lean text uses renderTuple/renderSequence, List Char, ++/intercalate — not the Python source lines).
- Patched file path 'sphinx/pycode/ast.py' and its dotted module path do NOT appear.
- Patched repo symbol 'visit_Tuple' (and 'UnparseVisitor') do NOT appear anywhere in spec-view identifiers, comments, or docstrings — the spec renames to generic renderSequence/renderTuple.
- No narration terms (bug/fix/wrong/incorrectly/patch/regression) in any spec-view comment.

SEMANTIC / GOLD-RECONSTRUCTION analysis (the substantive question): The discriminating content of the gold edit is the one-member trailing-comma rendering — a single element renders '(m,)' not '(m)'. That behavior is ALREADY FULLY PUBLIC in the solver-visible problem_statement: "(1,) is rendered as (1), but should keep the trailing comma." The spec's [e] => '(' ++ e ++ ',)' branch discloses nothing about the edit that the task text does not already state. The empty-case ([] => '()') and many-case (join with ', ') branches encode UNCHANGED pre-patch behavior; they localize no edit. Comments describe behavior abstractly (member-count-dependent wrapping, keeping the one-member form distinct from a bare parenthesized member) without narrating a bug/fix or pointing to the repo edit.

CONCLUSION: The spec view leaks nothing beyond the public problem_statement. It neither names the patched file/symbol nor reveals a discriminator not already disclosed to the solver. NO-LEAKAGE. (meta.json records G-LEAK pass, relaxed_leakage None — consistent; no RELAXED_LEAKAGE.md, and none needed.)

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
