# P2 adversarial audit — sympy__sympy-18763

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
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `atk_9.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -47,8 +47,8 @@
   do
     -- impl-start
     let out : List Char :=
-      "\\left. \\left(".toList ++ body
-        ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
+      "\\left. ".toList ++ body
+        ++ " \\right|_{\\substack{ ".toList ++ subsList
         ++ " }}".toList
     return out
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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -47,8 +47,8 @@
   do
     -- impl-start
     let out : List Char :=
-      "\\left. \\left(".toList ++ body
-        ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
+      "\\left. \\left(".toList ++ subsList
+        ++ "\\right) \\right|_{\\substack{ ".toList ++ body
         ++ " }}".toList
     return out
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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -49,7 +49,6 @@
     let out : List Char :=
       "\\left. \\left(".toList ++ body
         ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
-        ++ " }}".toList
     return out
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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -47,7 +47,7 @@
   do
     -- impl-start
     let out : List Char :=
-      "\\left. \\left(".toList ++ body
+      "\\left. \\big(".toList ++ body
         ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
         ++ " }}".toList
     return out
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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -47,7 +47,7 @@
   do
     -- impl-start
     let out : List Char :=
-      "\\left. \\left(".toList ++ body
+      "\\left. \\left(".toList
         ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
         ++ " }}".toList
     return out
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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -47,7 +47,7 @@
   do
     -- impl-start
     let out : List Char :=
-      "\\left. \\left(".toList ++ body
+      "\\left.\\left(".toList ++ body
         ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
         ++ " }}".toList
     return out
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -46,10 +46,7 @@
   ensures out = subsNotationLatex body subsList
   do
     -- impl-start
-    let out : List Char :=
-      "\\left. \\left(".toList ++ body
-        ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
-        ++ " }}".toList
+    let out : List Char := subsNotationLatex subsList body
     return out
     -- impl-end
 
```

Attack 8 — `atk_11.lean` → rejected (same spec, does not verify — good)

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
 -- (No axioms. The two rendered fragments consumed below are free inputs — the
@@ -46,10 +46,12 @@
   ensures out = subsNotationLatex body subsList
   do
     -- impl-start
-    let out : List Char :=
+    let good : List Char :=
       "\\left. \\left(".toList ++ body
         ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
         ++ " }}".toList
+    let out : List Char := body
+    let _ := good
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_9.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axioms. The two rendered fragments consumed below are free inputs — the
--  outputs of unchanged upstream renderers — so there is no callee contract to
--  assert or validate. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The character sequence of the notation for an expression displayed together
   with a list of evaluation assignments. The rendered body is enclosed in a
   matched pair of size-adjusting delimiters before the evaluation bar and the
   stacked assignment list are appended. Spelled out concretely (a deep model of
   the assembled sequence) so the implementation below is the identical
   concatenation. The delimiter-enclosure of the body is the behaviour pinned
   here. -/
def subsNotationLatex (body subsList : List Char) : List Char :=
  "\\left. \\left(".toList ++ body
    ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
    ++ " }}".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the notation for an expression shown evaluated against a list of
   assignments: the already-rendered `body` sequence, enclosed in a matched pair
   of size-adjusting delimiters, followed by the evaluation bar and the rendered
   `subsList` assignments inside the stacking group.

   `body` and `subsList` are read-only rendered fragments (the outputs of
   unchanged upstream renderers); they are NOT `mut` and the routine mutates
   nothing (directive 5). The result must be exactly the delimiter-enclosing
   assembly `subsNotationLatex body subsList` — in particular the body is
   wrapped in its own enclosing delimiter pair, not emitted bare. -/
method renderSubsNotation (body : List Char) (subsList : List Char) return (out : List Char)
  ensures out = subsNotationLatex body subsList
  do
    -- impl-start
    let pre1 : List Char := "\\left. ".toList
    let pre2 : List Char := "\\left(".toList
    let mid : List Char := "\\right) \\right|_{\\substack{ ".toList
    let suf : List Char := " }}".toList
    let out : List Char := pre1 ++ (pre2 ++ body) ++ (mid ++ subsList ++ suf)
    return out
    -- impl-end

prove_correct renderSubsNotation by
  loom_solve
  simp [subsNotationLatex]
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: velvet bundle sympy__sympy-18763. Spec = single concrete-equality postcondition `out = subsNotationLatex body subsList`, where subsNotationLatex is a fully spelled-out List Char ++-chain (no axioms, no deep-model refs, no opaque oracle). same_spec=True confirmed for every attack + positive control via swebench_unified.markers.same_spec (velvet). Positive control (pos_control.lean = verbatim Solution.lean) verifies exit 0; gold patch resolves (see resolve evidence).

TOOLING:; verify = `bash scripts/lean_verify.sh <f>`; resolve = swebench_unified.harness.run_resolve('sympy__sympy-18763', <patch>, retries=0). Ran verifications in concurrent batches of 4.

=== TERMINATING ATTACKS (submitted; all same_spec=True, all fail to verify => spec is TIGHT for every terminating impl) ===
atk_1  prepatch bug (bare body, no \left(...\right) enclosure)          EXIT=1  unsolved ensures_1
atk_2  body/subsList swapped                                             EXIT=1  unsolved ensures_1
atk_3  missing trailing ' }}' (suffix truncation)                       EXIT=1  ensures_1 -> False
atk_4  wrong delimiter \big( for \left(                                  EXIT=1  ensures_1 -> False
atk_5  body dropped entirely (partial-domain)                           EXIT=1  goal body = []
atk_6  missing space '\left.\left(' vs '\left. \left('                  EXIT=1  ensures_1 -> False
atk_8  ungrounded-oracle echo with SWAPPED args (subsNotationLatex subsList body)  EXIT=1  unsolved ensures_1
atk_11 control-flow dead-store: compute correct into temp, return wrong var (body)  EXIT=1  unsolved ensures_1
Every behaviorally-wrong TERMINATING impl is rejected; positive control atk_9 (structurally regrouped pre1++(pre2++body)++(mid++subsList++suf)) verifies EXIT=0 (spec non-vacuous/satisfiable).

=== DIVERGENCE LOOPHOLE PROBES (analyzed + resolve-run per protocol step 2; NOT submitted as attacks — see reasoning) === The frozen spec sets `loom.semantics.termination "partial"` and the prove_correct body is ELIDED from the spec signature (markers._elide_prove_correct), so a candidate may supply its own proof (loom_solve).

Under partial correctness a non-terminating method vacuously satisfies ANY postcondition. atk_12: `out := (bare-body string); let mut k:=1; while k>0 (invariant k>0) do k:=k+1; return out` + proof `loom_solve`  => VERIFIES EXIT=0 (returns WRONG value hidden behind divergence) atk_13: `out := []; while k>0 ... ; return out` + proof `loom_solve`                                             => VERIFIES EXIT=0 (returns empty string) MECHANISM CONFIRMED by terminating control ctl_term_wrong.lean: identical wrong value with a TERMINATING loop (done_with k=0, k:=k-1) FAILS to verify EXIT=1 (goal reduces to bare-string = subsNotationLatex ... -> unsolvable). So atk_12/atk_13 verify ONLY because their loops diverge, not because the spec is functionally weak.

Also atk_7/atk_10 (same divergence but KEEPING the frozen `loom_solve; simp [subsNotationLatex]` proof) FAIL EXIT=1 with 'No goals to be solved' (the trailing simp errors on the vacuously-closed goal) — divergence only slips through when the proof is reduced to loom_solve.

### RESOLVE RUNS (executed, official harness, Docker oracle available)
gold patch (\left(%s\right) wrap):                RESOLVED=True  COMPLETED=True  ('resolved')  [positive resolve control — harness wiring sound]
atk_12 FAITHFUL patch (divergence-PRESERVING: `out=...; while True: pass; return out`, applies cleanly, git-generated): RESOLVED=False COMPLETED=False ('no report — harness error') — ran twice (timeout 600s and 300s); the `while True: pass` hangs the F2P test, swebench raises EvaluationError at run_evaluation.py:214-220 BEFORE writing report.json. Per build_one.py:310 `not r.completed` => INCONCLUSIVE-for-candidate, NOT BROKEN.
atk_13 patch (`return ''`, divergence-DROPPING): RESOLVED=False COMPLETED=True ('patch did not resolve'). This DOES complete-and-fail, BUT it is UNFAITHFUL: dropping the loop yields `out:=[]; return out` which does NOT verify (cf. atk_5/ctl_term_wrong). The divergence is load-bearing for verification, so `return ''` misrepresents a divergent program as one returning empty string. Submitting it as the 'faithful' patch would manufacture a false BROKEN (reverse rubber-stamp) — declined.

### WHY SOUND (not BROKEN, not INCONCLUSIVE)
1. The spec rejects EVERY terminating wrong impl (8 distinct classes above) — verify=>correct holds for all terminating candidates; positive control verifies; gold resolves; prepatch reproduced+rejected on the exact discriminating clause.
2. The sole verifying-wrong impls exploit partial-correctness divergence-vacuity, a UNIVERSAL property of every Velvet `termination "partial"` bundle (out of the G-EQ functional-weakness taxonomy; the prior recorded 8-attack G-EQ pass on this bundle used terminating attacks). Their genuinely FAITHFUL patch preserves the divergence and HANGS => COMPLETED=False (empirically shown, twice). No completed resolve run yields verify AND not-resolved via a faithful patch, so there is no verify⇏correct break. Not INCONCLUSIVE: the atk_12 faithful-patch resolve reached a deterministic conclusion (hang -> EvaluationError, not infra/contention flakiness), and all needed terminating-attack verifications + gold/positive resolve completed cleanly.

### refinement.md AUDIT (step 3)
Legs A1–A5: A1/A2 = R (str <-> List Char bijection, mapping.md §2); A3/A4 = I (identical literal ++ concatenation, the discriminating \left(...\right) enclosure); A5 = I+R (suffix + return type). NO axioms, NO deep-model references (meta.json axioms=[]/deep_model_references=[]), NO kind-3 hand-waved op — the genuinely-changed op (delimiter enclosure) is modeled concretely. A-legs (free inputs body=_print(expr) latex.py:701, subsList=r'\\ '.join latex.py:704-705) correspond to the real UNCHANGED callees; conformance_check.py runs the real LatexPrinter for them and G-CONF agreed on 100005 fuzzed Subs (seed 18763, 0 disagreements). Correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `atk_9.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_9.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axioms. The two rendered fragments consumed below are free inputs — the
--  outputs of unchanged upstream renderers — so there is no callee contract to
--  assert or validate. See mapping.md §3.)
-- axioms-end

-- pure-start
/- The character sequence of the notation for an expression displayed together
   with a list of evaluation assignments. The rendered body is enclosed in a
   matched pair of size-adjusting delimiters before the evaluation bar and the
   stacked assignment list are appended. Spelled out concretely (a deep model of
   the assembled sequence) so the implementation below is the identical
   concatenation. The delimiter-enclosure of the body is the behaviour pinned
   here. -/
def subsNotationLatex (body subsList : List Char) : List Char :=
  "\\left. \\left(".toList ++ body
    ++ "\\right) \\right|_{\\substack{ ".toList ++ subsList
    ++ " }}".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the notation for an expression shown evaluated against a list of
   assignments: the already-rendered `body` sequence, enclosed in a matched pair
   of size-adjusting delimiters, followed by the evaluation bar and the rendered
   `subsList` assignments inside the stacking group.

   `body` and `subsList` are read-only rendered fragments (the outputs of
   unchanged upstream renderers); they are NOT `mut` and the routine mutates
   nothing (directive 5). The result must be exactly the delimiter-enclosing
   assembly `subsNotationLatex body subsList` — in particular the body is
   wrapped in its own enclosing delimiter pair, not emitted bare. -/
method renderSubsNotation (body : List Char) (subsList : List Char) return (out : List Char)
  ensures out = subsNotationLatex body subsList
  do
    -- impl-start
    let pre1 : List Char := "\\left. ".toList
    let pre2 : List Char := "\\left(".toList
    let mid : List Char := "\\right) \\right|_{\\substack{ ".toList
    let suf : List Char := " }}".toList
    let out : List Char := pre1 ++ (pre2 ++ body) ++ (mid ++ subsList ++ suf)
    return out
    -- impl-end

prove_correct renderSubsNotation by
  loom_solve
  simp [subsNotationLatex]
```

Prepatch bug re-encoded as an attack: `True`.

SCOPE: velvet bundle sympy__sympy-18763. Spec = single concrete-equality postcondition `out = subsNotationLatex body subsList`, where subsNotationLatex is a fully spelled-out List Char ++-chain (no axioms, no deep-model refs, no opaque oracle). same_spec=True confirmed for every attack + positive control via swebench_unified.markers.same_spec (velvet). Positive control (pos_control.lean = verbatim Solution.lean) verifies exit 0; gold patch resolves (see resolve evidence).

TOOLING:; verify = `bash scripts/lean_verify.sh <f>`; resolve = swebench_unified.harness.run_resolve('sympy__sympy-18763', <patch>, retries=0). Ran verifications in concurrent batches of 4.

=== TERMINATING ATTACKS (submitted; all same_spec=True, all fail to verify => spec is TIGHT for every terminating impl) ===
atk_1  prepatch bug (bare body, no \left(...\right) enclosure)          EXIT=1  unsolved ensures_1
atk_2  body/subsList swapped                                             EXIT=1  unsolved ensures_1
atk_3  missing trailing ' }}' (suffix truncation)                       EXIT=1  ensures_1 -> False
atk_4  wrong delimiter \big( for \left(                                  EXIT=1  ensures_1 -> False
atk_5  body dropped entirely (partial-domain)                           EXIT=1  goal body = []
atk_6  missing space '\left.\left(' vs '\left. \left('                  EXIT=1  ensures_1 -> False
atk_8  ungrounded-oracle echo with SWAPPED args (subsNotationLatex subsList body)  EXIT=1  unsolved ensures_1
atk_11 control-flow dead-store: compute correct into temp, return wrong var (body)  EXIT=1  unsolved ensures_1
Every behaviorally-wrong TERMINATING impl is rejected; positive control atk_9 (structurally regrouped pre1++(pre2++body)++(mid++subsList++suf)) verifies EXIT=0 (spec non-vacuous/satisfiable).

=== DIVERGENCE LOOPHOLE PROBES (analyzed + resolve-run per protocol step 2; NOT submitted as attacks — see reasoning) === The frozen spec sets `loom.semantics.termination "partial"` and the prove_correct body is ELIDED from the spec signature (markers._elide_prove_correct), so a candidate may supply its own proof (loom_solve).

Under partial correctness a non-terminating method vacuously satisfies ANY postcondition. atk_12: `out := (bare-body string); let mut k:=1; while k>0 (invariant k>0) do k:=k+1; return out` + proof `loom_solve`  => VERIFIES EXIT=0 (returns WRONG value hidden behind divergence) atk_13: `out := []; while k>0 ... ; return out` + proof `loom_solve`                                             => VERIFIES EXIT=0 (returns empty string) MECHANISM CONFIRMED by terminating control ctl_term_wrong.lean: identical wrong value with a TERMINATING loop (done_with k=0, k:=k-1) FAILS to verify EXIT=1 (goal reduces to bare-string = subsNotationLatex ... -> unsolvable). So atk_12/atk_13 verify ONLY because their loops diverge, not because the spec is functionally weak.

Also atk_7/atk_10 (same divergence but KEEPING the frozen `loom_solve; simp [subsNotationLatex]` proof) FAIL EXIT=1 with 'No goals to be solved' (the trailing simp errors on the vacuously-closed goal) — divergence only slips through when the proof is reduced to loom_solve.

### RESOLVE RUNS (executed, official harness, Docker oracle available)
gold patch (\left(%s\right) wrap):                RESOLVED=True  COMPLETED=True  ('resolved')  [positive resolve control — harness wiring sound]
atk_12 FAITHFUL patch (divergence-PRESERVING: `out=...; while True: pass; return out`, applies cleanly, git-generated): RESOLVED=False COMPLETED=False ('no report — harness error') — ran twice (timeout 600s and 300s); the `while True: pass` hangs the F2P test, swebench raises EvaluationError at run_evaluation.py:214-220 BEFORE writing report.json. Per build_one.py:310 `not r.completed` => INCONCLUSIVE-for-candidate, NOT BROKEN.
atk_13 patch (`return ''`, divergence-DROPPING): RESOLVED=False COMPLETED=True ('patch did not resolve'). This DOES complete-and-fail, BUT it is UNFAITHFUL: dropping the loop yields `out:=[]; return out` which does NOT verify (cf. atk_5/ctl_term_wrong). The divergence is load-bearing for verification, so `return ''` misrepresents a divergent program as one returning empty string. Submitting it as the 'faithful' patch would manufacture a false BROKEN (reverse rubber-stamp) — declined.

### WHY SOUND (not BROKEN, not INCONCLUSIVE)
1. The spec rejects EVERY terminating wrong impl (8 distinct classes above) — verify=>correct holds for all terminating candidates; positive control verifies; gold resolves; prepatch reproduced+rejected on the exact discriminating clause.
2. The sole verifying-wrong impls exploit partial-correctness divergence-vacuity, a UNIVERSAL property of every Velvet `termination "partial"` bundle (out of the G-EQ functional-weakness taxonomy; the prior recorded 8-attack G-EQ pass on this bundle used terminating attacks). Their genuinely FAITHFUL patch preserves the divergence and HANGS => COMPLETED=False (empirically shown, twice). No completed resolve run yields verify AND not-resolved via a faithful patch, so there is no verify⇏correct break. Not INCONCLUSIVE: the atk_12 faithful-patch resolve reached a deterministic conclusion (hang -> EvaluationError, not infra/contention flakiness), and all needed terminating-attack verifications + gold/positive resolve completed cleanly.

### refinement.md AUDIT (step 3)
Legs A1–A5: A1/A2 = R (str <-> List Char bijection, mapping.md §2); A3/A4 = I (identical literal ++ concatenation, the discriminating \left(...\right) enclosure); A5 = I+R (suffix + return type). NO axioms, NO deep-model references (meta.json axioms=[]/deep_model_references=[]), NO kind-3 hand-waved op — the genuinely-changed op (delimiter enclosure) is modeled concretely. A-legs (free inputs body=_print(expr) latex.py:701, subsList=r'\\ '.join latex.py:704-705) correspond to the real UNCHANGED callees; conformance_check.py runs the real LatexPrinter for them and G-CONF agreed on 100005 fuzzed Subs (seed 18763, 0 disagreements). Correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness holds; no divergence found. Checks performed: (1) same_spec(Solution.lean, Solution_prepatch.lean, velvet tables)=True and spec_view region hash matches meta.json (10c69ff7...), so the frozen spec region is byte-identical and the differential-witness discipline is intact. (2) Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean fails (exit 1) exactly on the missing \left(/\right) enclosure — the intended G-DIFF witness. (3) The spec model subsNotationLatex body subsList = "\left. \left(" ++ body ++ "\right) \right|_{\substack{ " ++ subsList ++ " }}" is byte-for-byte identical to the gold post-patch _print_Subs return template r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs) at latex.py:706 (gold patch confirmed from test.jsonl at base_commit 70381f28). Every literal segment and both %s slots correspond exactly. (4) The two free inputs body=latex_expr=self._print(expr) and subsList=latex_subs=r'\\ '.join(...) are the genuinely-unchanged preamble outputs (lines 700-705) abstracted as inputs with no asserted contract, so the spec cannot be too strong via a hidden callee assumption. (5) Empirical differential run over 30k+ fuzzed Subs objects (seed 18763 gen): spec-transliteration shadow (with body/subsList computed by the REAL LatexPrinter) agrees with the real patched _print_Subs on every input, 0 mismatches. The format string has exactly two %s and no stray %, so no format-substitution hazard. The modeled function agrees with the real callee on all tested inputs and by literal correspondence; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction audit of sympy__sympy-18763 (velvet). Gold edit (latex.py:706): change LatexPrinter._print_Subs return template from r'\left. %s \right|_{\substack{ %s }}' to r'\left. \left(%s\right) \right|_{\substack{ %s }}' — i.e. wrap the rendered body in a matched \left( ... \right) pair.

Rigor checks:
- Rendered the actual spec view via swebench_unified.markers.spec_view(src, VelvetBackend.language): impl region collapses to 'implementation elided', prove_correct body elided. Visible spec = imports, set_options, empty axioms (comment only), the `pure` def subsNotationLatex, empty pre/post regions, the method docstring, and the obligation `ensures out = subsNotationLatex body subsList`.
- same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True (confirmed live). Spec view is byte-identical between gold and prepatch; only the impl region differs, so nothing gold-specific hides in the visible spec.

Leakage analysis (excess over PUBLIC problem_statement, NOT hints — hints_text is empty here anyway):
The public problem_statement already quotes BOTH strings verbatim: the buggy '3 \left. - x + y \right|_{\substack{ x=1 }}' and the desired '3 \left. \left(- x + y\right) \right|_{\substack{ x=1 }}'. Diffing the two published strings yields the entire gold edit — enclose the body in a matched \left( ... \right) pair. It is fully reconstructible from problem_statement alone.

The spec view's subsNotationLatex template ('\\left. \\left(' ++ body ++ '\\right) \\right|_{\\substack{ ' ++ subsList ++ ' }}') and the docstring's delimiter-enclosure description restate exactly the target string the issue already publishes. Every template detail present in the spec is a verbatim subset of the string the issue itself exposes. Excess disclosure over the public statement = zero.

Modeling boundary is honest: the changed op (return-template assembly) is modeled concretely; the unchanged upstream renderers (self._print, r'\\ '.join) are abstracted AWAY as free inputs body/subsList (no asserted contract) — this hides repo internals rather than exposing them. No axioms/deep-model-refs. Automated G-LEAK also passed with empty failures.

Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.