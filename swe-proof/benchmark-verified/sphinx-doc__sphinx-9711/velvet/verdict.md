# P2 adversarial audit — sphinx-doc__sphinx-9711

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
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The component-wise version ordering is modeled
@@ -125,10 +125,13 @@
       invariant 0 ≤ i ∧ i ≤ reqs.length
       invariant acc = anyUnmet (reqs.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := reqs[i - 1]!
-      acc := unmet r || acc
+      let lexUnmet : Bool :=
+        if !r.isPresent then false
+        else if !r.isKnown then true
+        else decide (r.required > r.present)
+      acc := lexUnmet || acc
       i := i - 1
     return acc
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
 -- (No axiomatized callees. The component-wise version ordering is modeled
@@ -119,18 +119,7 @@
   ensures raised = anyUnmet reqs
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := reqs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ reqs.length
-      invariant acc = anyUnmet (reqs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := reqs[i - 1]!
-      acc := unmet r || acc
-      i := i - 1
-    return acc
+    return false
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -149,5 +138,3 @@
 
 prove_correct anyRequirementUnmet by
   loom_solve
-  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
-  simp_all
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
 -- (No axiomatized callees. The component-wise version ordering is modeled
@@ -119,18 +119,7 @@
   ensures raised = anyUnmet reqs
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := reqs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ reqs.length
-      invariant acc = anyUnmet (reqs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := reqs[i - 1]!
-      acc := unmet r || acc
-      i := i - 1
-    return acc
+    return true
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -149,5 +138,3 @@
 
 prove_correct anyRequirementUnmet by
   loom_solve
-  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
-  simp_all
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
 -- (No axiomatized callees. The component-wise version ordering is modeled
@@ -123,11 +123,9 @@
     let mut i := reqs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ reqs.length
-      invariant acc = anyUnmet (reqs.drop i)
       done_with i = 0
-      decreasing i
     do
-      let r := reqs[i - 1]!
+      let r := reqs[i]!
       acc := unmet r || acc
       i := i - 1
     return acc
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
 -- (No axiomatized callees. The component-wise version ordering is modeled
@@ -119,17 +119,8 @@
   ensures raised = anyUnmet reqs
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := reqs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ reqs.length
-      invariant acc = anyUnmet (reqs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := reqs[i - 1]!
-      acc := unmet r || acc
-      i := i - 1
+    -- control-flow effect: scan only the FIRST requirement, ignore the rest
+    let acc : Bool := if reqs.length > 0 then unmet reqs[0]! else false
     return acc
     -- impl-end
 
@@ -149,5 +140,3 @@
 
 prove_correct anyRequirementUnmet by
   loom_solve
-  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The component-wise version ordering is modeled
@@ -119,18 +119,7 @@
   ensures raised = anyUnmet reqs
   do
     -- impl-start
-    let mut acc : Bool := false
-    let mut i := reqs.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ reqs.length
-      invariant acc = anyUnmet (reqs.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let r := reqs[i - 1]!
-      acc := unmet r || acc
-      i := i - 1
-    return acc
+    return anyUnmet reqs
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -149,5 +138,3 @@
 
 prove_correct anyRequirementUnmet by
   loom_solve
-  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
-  simp_all
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
 -- (No axiomatized callees. The component-wise version ordering is modeled
@@ -123,12 +123,14 @@
     let mut i := reqs.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ reqs.length
-      invariant acc = anyUnmet (reqs.drop i)
       done_with i = 0
-      decreasing i
     do
       let r := reqs[i - 1]!
-      acc := unmet r || acc
+      let wrong : Bool :=
+        if !r.isPresent then false
+        else if !r.isKnown then true
+        else verGt r.present r.required
+      acc := wrong || acc
       i := i - 1
     return acc
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The component-wise version ordering is modeled
--  DEEPLY by `verGt` in the `pure` region — it is the operation under spec, so
--  it is spelled out, NOT hidden behind an axiom (SPEC_GUIDE directive 7). The
--  deep model's equality to the real numeric version comparator is validated by
--  axiom_check.py (G-AX) as an A-reference, on the numeric-version domain the
--  `require` clause pins. Nothing is consumed as an axiom.)
-- axioms-end

-- pure-start
/- A version string in the modeled domain: a dotted sequence of decimal
   components. `verGt` is exact only on this domain; the `require` clause below
   pins it, and the G-CONF / G-AX fuzzers stay inside it. -/

/- The numeric value of one decimal digit. -/
def digitVal (c : Char) : Nat := c.toNat - '0'.toNat

/- The numeric value of one dotted component (a run of decimal digits), read
   most-significant first. Leading zeros are absorbed (value-preserving), which
   is exactly how the numeric comparator treats them. -/
def parseComp (cs : List Char) : Nat :=
  cs.foldl (fun acc c => acc * 10 + digitVal c) 0

/- Split a version string into its dotted components, front-recursively so a
   single unfold is available per step. Always yields at least one component. -/
def splitDots : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
    let rest := splitDots cs
    if c = '.' then [] :: rest
    else (c :: rest.headD []) :: rest.tail

/- One component is well formed iff it is a non-empty run of decimal digits. -/
def compOk (cs : List Char) : Bool := cs ≠ [] && cs.all Char.isDigit

/- A version string is in the modeled (numeric) domain iff every dotted
   component is a non-empty digit run. -/
def numericVer (s : List Char) : Bool := (splitDots s).all compOk

/- Strict numeric ordering of two component lists, most-significant first.
   When one list is exhausted the remaining components of the other are compared
   against an implicit zero — so trailing-zero components do not change the
   order (`[1,0] = [1,0,0]`), matching the numeric version comparator. -/
def relGt : List Nat → List Nat → Bool
  | [],        []        => false
  | [],        (y :: ys) => if 0 < y then false else relGt [] ys
  | (x :: xs), []        => if x > 0 then true else relGt xs []
  | (x :: xs), (y :: ys) =>
    if x > y then true else if x < y then false else relGt xs ys

/- The component-wise numeric "strictly greater than" on version strings: parse
   each into its component list and compare numerically. This is the desired
   ordering the issue asks for — `verGt "0.10" "0.6" = true` even though the
   purely textual ordering disagrees. -/
def verGt (a b : List Char) : Bool :=
  relGt ((splitDots a).map parseComp) ((splitDots b).map parseComp)

/- A loaded software component carrying a version requirement:
   `required`  — the minimum version the project demands;
   `present`   — the version actually available (meaningful only when present
                 and known);
   `isPresent` — whether the component is available at all;
   `isKnown`   — whether the available version is determinate. -/
structure Requirement where
  required  : List Char
  present   : List Char
  isPresent : Bool
  isKnown   : Bool
  deriving Inhabited

/- A single requirement is UNMET iff the component is present and either its
   version is indeterminate, or its available version is strictly below the
   demanded minimum under the numeric ordering. An absent component imposes no
   obligation here (it is reported elsewhere, not failed). -/
def unmet (r : Requirement) : Bool :=
  if !r.isPresent then false
  else if !r.isKnown then true
  else verGt r.required r.present

/- Whether ANY requirement in the list is unmet — the disjunction of the
   per-requirement test. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern, plan §5.4). -/
def anyUnmet : List Requirement → Bool
  | []      => false
  | r :: rs => unmet r || anyUnmet rs

@[grind] lemma anyUnmet_nil : anyUnmet [] = false := rfl
@[grind] lemma anyUnmet_cons (r : Requirement) (rs : List Requirement) :
    anyUnmet (r :: rs) = (unmet r || anyUnmet rs) := rfl

/- A requirement is in the modeled domain iff its demanded version is numeric,
   and (when present with a determinate version) its available version is too. -/
def reqWellFormed (r : Requirement) : Bool :=
  numericVer r.required && (!(r.isPresent && r.isKnown) || numericVer r.present)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The version-requirement scan: returns whether at least one loaded component
   fails its minimum-version requirement (the signal a caller turns into an
   abort). It folds the per-requirement test `unmet` over the requested list.
   `reqs` is read-only (not `mut`); the scan mutates nothing it is handed
   (directive 5). The `require` pins the modeled numeric-version domain on which
   the component-wise ordering is exact (mapping.md §3.1). -/
method anyRequirementUnmet (reqs : List Requirement) return (raised : Bool)
  require reqs.all reqWellFormed = true
  ensures raised = anyUnmet reqs
  do
    -- impl-start
    let mut acc : Bool := false
    let mut i := reqs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ reqs.length
      invariant acc = anyUnmet (reqs.drop i)
      done_with i = 0
    do
      let r := reqs[i - 1]!
      acc := unmet r || acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyUnmet` peels one disjunct. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma anyUnmet_drop_step (reqs : List Requirement) (i : Nat)
    (hi : 0 < i) (hle : i ≤ reqs.length) :
    anyUnmet (reqs.drop (i - 1)) = (unmet reqs[i - 1]! || anyUnmet (reqs.drop i)) := by
  have hlt : i - 1 < reqs.length := by omega
  have hcons : reqs.drop (i - 1) = reqs[i - 1]! :: reqs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyUnmet_cons]

prove_correct anyRequirementUnmet by
  loom_solve
  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's obligation is a TOTAL FUNCTIONAL postcondition `ensures raised = anyUnmet reqs` over the `require reqs.all reqWellFormed` (numericVer) domain. same_spec elides only the impl region + prove_correct body (confirmed via markers._lean_spec_view), so all attacks below keep the axioms/pure/pre/post byte-identical (same_spec=True for every file, machine-checked).

PROTOCOL. Project root (NOT the path in the prompt template). Verify cmd: `bash scripts/lean_verify.sh <file>`. Resolve cmd: run_resolve via `... PYTHONPATH=src python resolve_one.py <patch> <run_id>`. Verifications launched concurrently in background batches of <=4.

### ATTACK MATRIX (all same_spec=True, machine-checked):
atk_1 (prepatch bug re-encoded: lexicographic `decide (r.required > r.present)` on raw List Char): VERIFY exit=1 REJECTED — unsolved goal on invariant_2 (textual != numeric verdict on required '3.9'/present '3.10'). This IS the F2P discriminator. prepatch_reproduced=True (prepatch.lean also exit=1). atk_2 (partial-domain degenerate: `return false`): VERIFY exit=1 REJECTED (unsolved postcondition). atk_3 (ungrounded constant: `return true`): VERIFY exit=1 REJECTED (unsolved postcondition). atk_4 (boundary off-by-one: reqs[i]! instead of reqs[i-1]!): VERIFY exit=1 REJECTED (rewrite/invariant fails). atk_5 (control-flow effect: scan only first requirement, ignore the rest): VERIFY exit=1 REJECTED (unsolved postcondition — disjunction not covered). atk_8 (ungrounded-oracle wrong: swapped args `verGt r.present r.required`): VERIFY exit=1 REJECTED (rewrite fails; wrong comparison direction). atk_7 (ungrounded-oracle ECHO: `return anyUnmet reqs`): VERIFY exit=0 VERIFIES.

Faithful refined patch = gold patch.diff (numeric packaging.Version comparison). run_resolve -> {completed:True, resolved:True} (run_id sbu-audit-eq-9711-atk7). CORRECT ECHO of the gold — resolves, therefore NOT a weakness (per _derive_audit_verdict: a verifying candidate whose faithful patch resolves is not a defect). positive_control (gold Solution.lean impl): VERIFY exit=0 VERIFIES.

NONTERMINATION PROBE (reported, deliberately NOT submitted as a gate attack): I additionally encoded atk_6 = `while true do acc := acc` (never returns). It VERIFIES (exit=0) vacuously under the bundle's explicitly-declared `set_option loom.semantics.termination "partial"` (PartialCorrectness) — same_spec=True. I materialized its faithful refined patch (verify_needs_extensions body replaced by `while True: acc = acc`, patch applies cleanly at base_commit, git-diff-generated) and RAN it through the official harness run_resolve TWICE (run_ids sbu-audit-eq-9711-atk6 @1800s, sbu-audit-eq-9711-atk6b @600s).

Both returned {completed:False, resolved:False}: the infinite loop hangs the F2P test in-container, swebench's exec_run_with_timeout trips, run_evaluation raises EvaluationError BEFORE writing report.json (verified in swebench/harness/run_evaluation.py lines 206-220), so run_resolve gets no report -> completed=False. Per _derive_audit_verdict (build_one.py:305-312), BROKEN requires `r.completed and not r.resolved`; a completed=False timeout goes to inconclusive_hits, NOT a fail. So the nontermination candidate produces INCONCLUSIVE-per-attack, never BROKEN.

Moreover nontermination-verifies-vacuously is a UNIVERSAL property of every `partial`-semantics Velvet bundle (sanctioned by spec_guide.md §1.1), NOT a defect of THIS spec's model<->patch correspondence, which is the G-EQ refinement-fidelity question. Including it as a gate attack would spuriously fail-close a sound spec on a resolve run that structurally cannot report BROKEN. Reported here for full transparency; not counted toward the attack floor.

A-LEG / refinement.md AUDIT: Every leg is R / A-reference / I; NO kind-3 (confirmed §C). The single A-reference is A3: verGt (deep model, splitDots/parseComp/relGt) <-> `Version(reqversion) > Version(extension.version)` (packaging.version.Version.__gt__), the exact callee the gold patch imports. G-AX axiom_check.py RUN with real packaging 26.3: exit 0, 'verGt deep model (== packaging Version comparison) sound on 19 boundary + 50000 fuzz version pairs over the numeric domain' — includes the issue discriminators 3.9/3.10 and 0.6/0.10, trailing-zero 1.0/1.0.0, leading-zero 01.2/1.2, multi-digit 10/9. No consumed axioms (axioms region empty, §3.2). The require-domain (reqWellFormed/numericVer) exactly pins the numeric domain where Version() is total and where the F2P inputs live ('3.9','3.10','3.11' — all numeric); the gold's try/except InvalidVersion textual fallback is out of modeled scope by construction, not a hidden kind-3 op. R legs (dict<->List Requirement, raise<->Bool, str<->List Char) and I legs (disjunctive fold, isPresent/isKnown guards) are G-CONF territory and correspond correctly.

CONCLUSION: On the whole require-domain the total functional postcondition forces any verifying TERMINATING impl to compute exactly anyUnmet (numeric verGt), i.e. the gold behaviour; the only verifying variants are the correct echo (resolves) and vacuous nontermination (resolve INCONCLUSIVE, universal artifact). No same-spec verifying impl has a faithful patch that COMPLETES resolve as unresolved. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The component-wise version ordering is modeled
--  DEEPLY by `verGt` in the `pure` region — it is the operation under spec, so
--  it is spelled out, NOT hidden behind an axiom (SPEC_GUIDE directive 7). The
--  deep model's equality to the real numeric version comparator is validated by
--  axiom_check.py (G-AX) as an A-reference, on the numeric-version domain the
--  `require` clause pins. Nothing is consumed as an axiom.)
-- axioms-end

-- pure-start
/- A version string in the modeled domain: a dotted sequence of decimal
   components. `verGt` is exact only on this domain; the `require` clause below
   pins it, and the G-CONF / G-AX fuzzers stay inside it. -/

/- The numeric value of one decimal digit. -/
def digitVal (c : Char) : Nat := c.toNat - '0'.toNat

/- The numeric value of one dotted component (a run of decimal digits), read
   most-significant first. Leading zeros are absorbed (value-preserving), which
   is exactly how the numeric comparator treats them. -/
def parseComp (cs : List Char) : Nat :=
  cs.foldl (fun acc c => acc * 10 + digitVal c) 0

/- Split a version string into its dotted components, front-recursively so a
   single unfold is available per step. Always yields at least one component. -/
def splitDots : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
    let rest := splitDots cs
    if c = '.' then [] :: rest
    else (c :: rest.headD []) :: rest.tail

/- One component is well formed iff it is a non-empty run of decimal digits. -/
def compOk (cs : List Char) : Bool := cs ≠ [] && cs.all Char.isDigit

/- A version string is in the modeled (numeric) domain iff every dotted
   component is a non-empty digit run. -/
def numericVer (s : List Char) : Bool := (splitDots s).all compOk

/- Strict numeric ordering of two component lists, most-significant first.
   When one list is exhausted the remaining components of the other are compared
   against an implicit zero — so trailing-zero components do not change the
   order (`[1,0] = [1,0,0]`), matching the numeric version comparator. -/
def relGt : List Nat → List Nat → Bool
  | [],        []        => false
  | [],        (y :: ys) => if 0 < y then false else relGt [] ys
  | (x :: xs), []        => if x > 0 then true else relGt xs []
  | (x :: xs), (y :: ys) =>
    if x > y then true else if x < y then false else relGt xs ys

/- The component-wise numeric "strictly greater than" on version strings: parse
   each into its component list and compare numerically. This is the desired
   ordering the issue asks for — `verGt "0.10" "0.6" = true` even though the
   purely textual ordering disagrees. -/
def verGt (a b : List Char) : Bool :=
  relGt ((splitDots a).map parseComp) ((splitDots b).map parseComp)

/- A loaded software component carrying a version requirement:
   `required`  — the minimum version the project demands;
   `present`   — the version actually available (meaningful only when present
                 and known);
   `isPresent` — whether the component is available at all;
   `isKnown`   — whether the available version is determinate. -/
structure Requirement where
  required  : List Char
  present   : List Char
  isPresent : Bool
  isKnown   : Bool
  deriving Inhabited

/- A single requirement is UNMET iff the component is present and either its
   version is indeterminate, or its available version is strictly below the
   demanded minimum under the numeric ordering. An absent component imposes no
   obligation here (it is reported elsewhere, not failed). -/
def unmet (r : Requirement) : Bool :=
  if !r.isPresent then false
  else if !r.isKnown then true
  else verGt r.required r.present

/- Whether ANY requirement in the list is unmet — the disjunction of the
   per-requirement test. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern, plan §5.4). -/
def anyUnmet : List Requirement → Bool
  | []      => false
  | r :: rs => unmet r || anyUnmet rs

@[grind] lemma anyUnmet_nil : anyUnmet [] = false := rfl
@[grind] lemma anyUnmet_cons (r : Requirement) (rs : List Requirement) :
    anyUnmet (r :: rs) = (unmet r || anyUnmet rs) := rfl

/- A requirement is in the modeled domain iff its demanded version is numeric,
   and (when present with a determinate version) its available version is too. -/
def reqWellFormed (r : Requirement) : Bool :=
  numericVer r.required && (!(r.isPresent && r.isKnown) || numericVer r.present)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The version-requirement scan: returns whether at least one loaded component
   fails its minimum-version requirement (the signal a caller turns into an
   abort). It folds the per-requirement test `unmet` over the requested list.
   `reqs` is read-only (not `mut`); the scan mutates nothing it is handed
   (directive 5). The `require` pins the modeled numeric-version domain on which
   the component-wise ordering is exact (mapping.md §3.1). -/
method anyRequirementUnmet (reqs : List Requirement) return (raised : Bool)
  require reqs.all reqWellFormed = true
  ensures raised = anyUnmet reqs
  do
    -- impl-start
    let mut acc : Bool := false
    let mut i := reqs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ reqs.length
      invariant acc = anyUnmet (reqs.drop i)
      done_with i = 0
    do
      let r := reqs[i - 1]!
      acc := unmet r || acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyUnmet` peels one disjunct. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma anyUnmet_drop_step (reqs : List Requirement) (i : Nat)
    (hi : 0 < i) (hle : i ≤ reqs.length) :
    anyUnmet (reqs.drop (i - 1)) = (unmet reqs[i - 1]! || anyUnmet (reqs.drop i)) := by
  have hlt : i - 1 < reqs.length := by omega
  have hcons : reqs.drop (i - 1) = reqs[i - 1]! :: reqs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyUnmet_cons]

prove_correct anyRequirementUnmet by
  loom_solve
  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's obligation is a TOTAL FUNCTIONAL postcondition `ensures raised = anyUnmet reqs` over the `require reqs.all reqWellFormed` (numericVer) domain. same_spec elides only the impl region + prove_correct body (confirmed via markers._lean_spec_view), so all attacks below keep the axioms/pure/pre/post byte-identical (same_spec=True for every file, machine-checked).

PROTOCOL. Project root (NOT the path in the prompt template). Verify cmd: `bash scripts/lean_verify.sh <file>`. Resolve cmd: run_resolve via `... PYTHONPATH=src python resolve_one.py <patch> <run_id>`. Verifications launched concurrently in background batches of <=4.

### ATTACK MATRIX (all same_spec=True, machine-checked):
atk_1 (prepatch bug re-encoded: lexicographic `decide (r.required > r.present)` on raw List Char): VERIFY exit=1 REJECTED — unsolved goal on invariant_2 (textual != numeric verdict on required '3.9'/present '3.10'). This IS the F2P discriminator. prepatch_reproduced=True (prepatch.lean also exit=1). atk_2 (partial-domain degenerate: `return false`): VERIFY exit=1 REJECTED (unsolved postcondition). atk_3 (ungrounded constant: `return true`): VERIFY exit=1 REJECTED (unsolved postcondition). atk_4 (boundary off-by-one: reqs[i]! instead of reqs[i-1]!): VERIFY exit=1 REJECTED (rewrite/invariant fails). atk_5 (control-flow effect: scan only first requirement, ignore the rest): VERIFY exit=1 REJECTED (unsolved postcondition — disjunction not covered). atk_8 (ungrounded-oracle wrong: swapped args `verGt r.present r.required`): VERIFY exit=1 REJECTED (rewrite fails; wrong comparison direction). atk_7 (ungrounded-oracle ECHO: `return anyUnmet reqs`): VERIFY exit=0 VERIFIES.

Faithful refined patch = gold patch.diff (numeric packaging.Version comparison). run_resolve -> {completed:True, resolved:True} (run_id sbu-audit-eq-9711-atk7). CORRECT ECHO of the gold — resolves, therefore NOT a weakness (per _derive_audit_verdict: a verifying candidate whose faithful patch resolves is not a defect). positive_control (gold Solution.lean impl): VERIFY exit=0 VERIFIES.

NONTERMINATION PROBE (reported, deliberately NOT submitted as a gate attack): I additionally encoded atk_6 = `while true do acc := acc` (never returns). It VERIFIES (exit=0) vacuously under the bundle's explicitly-declared `set_option loom.semantics.termination "partial"` (PartialCorrectness) — same_spec=True. I materialized its faithful refined patch (verify_needs_extensions body replaced by `while True: acc = acc`, patch applies cleanly at base_commit, git-diff-generated) and RAN it through the official harness run_resolve TWICE (run_ids sbu-audit-eq-9711-atk6 @1800s, sbu-audit-eq-9711-atk6b @600s).

Both returned {completed:False, resolved:False}: the infinite loop hangs the F2P test in-container, swebench's exec_run_with_timeout trips, run_evaluation raises EvaluationError BEFORE writing report.json (verified in swebench/harness/run_evaluation.py lines 206-220), so run_resolve gets no report -> completed=False. Per _derive_audit_verdict (build_one.py:305-312), BROKEN requires `r.completed and not r.resolved`; a completed=False timeout goes to inconclusive_hits, NOT a fail. So the nontermination candidate produces INCONCLUSIVE-per-attack, never BROKEN.

Moreover nontermination-verifies-vacuously is a UNIVERSAL property of every `partial`-semantics Velvet bundle (sanctioned by spec_guide.md §1.1), NOT a defect of THIS spec's model<->patch correspondence, which is the G-EQ refinement-fidelity question. Including it as a gate attack would spuriously fail-close a sound spec on a resolve run that structurally cannot report BROKEN. Reported here for full transparency; not counted toward the attack floor.

A-LEG / refinement.md AUDIT: Every leg is R / A-reference / I; NO kind-3 (confirmed §C). The single A-reference is A3: verGt (deep model, splitDots/parseComp/relGt) <-> `Version(reqversion) > Version(extension.version)` (packaging.version.Version.__gt__), the exact callee the gold patch imports. G-AX axiom_check.py RUN with real packaging 26.3: exit 0, 'verGt deep model (== packaging Version comparison) sound on 19 boundary + 50000 fuzz version pairs over the numeric domain' — includes the issue discriminators 3.9/3.10 and 0.6/0.10, trailing-zero 1.0/1.0.0, leading-zero 01.2/1.2, multi-digit 10/9. No consumed axioms (axioms region empty, §3.2). The require-domain (reqWellFormed/numericVer) exactly pins the numeric domain where Version() is total and where the F2P inputs live ('3.9','3.10','3.11' — all numeric); the gold's try/except InvalidVersion textual fallback is out of modeled scope by construction, not a hidden kind-3 op. R legs (dict<->List Requirement, raise<->Bool, str<->List Char) and I legs (disjunctive fold, isPresent/isKnown guards) are G-CONF territory and correspond correctly.

CONCLUSION: On the whole require-domain the total functional postcondition forces any verifying TERMINATING impl to compute exactly anyUnmet (numeric verGt), i.e. the gold behaviour; the only verifying variants are the correct echo (resolves) and vacuous nontermination (resolve INCONCLUSIVE, universal artifact). No same-spec verifying impl has a faithful patch that COMPLETES resolve as unresolved. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sphinx-doc__sphinx-9711 velvet. Modeled fn anyRequirementUnmet (ensures raised = anyUnmet reqs; require reqs.all reqWellFormed) vs real patched sphinx.extension.verify_needs_extensions. Solution.lean verifies (lean_verify exit 0). Independent 300k-pair fuzz of verGt/relGt/parseComp/splitDots vs REAL packaging.version.Version(a)>Version(b) over the numeric domain, plus boundary set (3.9/3.10, 0.10/0.6, 1.0/1.0.0, 01.2/1.2, 000, 12-digit comps, 8-deep tuples): 0 disagreements; Version never raised InvalidVersion inside numericVer (confirms G-AX). unmet = present && (!known || verGt required present) exactly mirrors patched body (unknown-version sentinel -> unmet; Version(req)>Version(ext.version) -> unmet; absent -> continue/not-unmet). anyUnmet disjunction = 'raises on first unmet' observable; list mapping faithful given dict-key uniqueness; order-insensitivity sound. Precondition narrows to numeric PEP440-total domain (where bug/F2P lives); the except InvalidVersion textual fallback is excluded BY precondition, not misclaimed, so spec is not too strong. numericVer uses ASCII-only Char.isDigit so no admitted input can make Version() raise -> precondition not too weak either. No input found where the model disagrees with the real callee within its stated obligations. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-region confirmed byte-identical to the frozen bundle (spec_view projection reproduces Solution.lean's non-impl/proof regions exactly). Mechanical G-LEAK screen (leakage.screen over the velvet spec view vs gold patch + problem_statement) PASSES with zero hard failures.

Semantic gold-reconstruction assessment: the public problem_statement already discloses the entire core answer — that needs_extensions compares versions 'string-like' and must instead compare NUMERICALLY, including the exact discriminating example ('0.6' > '0.10' textually but '0.6' < '0.10' as versions; 0.10.0 must be accepted when 0.6 is the minimum). The spec view's deep numeric-ordering model (verGt/relGt/splitDots/parseComp and the require reqWellFormed domain) is simply the faithful formalization of that publicly-stated expected behavior; its illustrative comment `verGt "0.10" "0.6" = true even though the purely textual ordering disagrees` restates the problem statement's own example, adding nothing beyond it.

Crucially, the spec view does NOT reveal the gold patch's SPECIFIC implementation strategy beyond the problem statement: no mention of `packaging.version.Version`/`InvalidVersion`, the `try/except InvalidVersion` textual fallback, or the `fulfilled` flag (all confined to refinement.md/mapping.md, which are auditor docs, not the consumer view). No patched file path (sphinx/extension.py), no patched symbol (verify_needs_extensions) appearing verbatim or embedded in any spec-view identifier/comment, no diff markers, no bug/fix narration. The changed repo symbol verify_needs_extensions (distinctive, not in problem_statement) does not collide with any spec identifier or comment. The spec view therefore leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.