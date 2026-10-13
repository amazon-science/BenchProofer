# P2 adversarial audit — sphinx-doc__sphinx-8593

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
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that breaks the spec. The one same-spec VERIFYING wrong impl found (atk_8a, non-termination) is the universal partial-correctness artifact, not a bundle-specific defect: its faithful patch hangs and resolve could not complete (no graded report), so it does not demonstrate a clean verify AND NOT-resolved.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,10 +92,9 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := names[i - 1]!
-      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
+      result := { name := n, doc := [] } :: result
       i := i - 1
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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,12 +92,11 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := names[i - 1]!
       result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
       i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,10 +92,9 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := names[i - 1]!
-      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
+      result := { name := n, doc := (lookupDocs n attrDocs).flatten } :: result
       i := i - 1
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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,10 +92,9 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := names[i - 1]!
-      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
+      result := { name := n, doc := (lookupDocs n attrDocs).headD [] } :: result
       i := i - 1
     return result
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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,10 +92,9 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := names[i - 1]!
-      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
+      result := { name := n + 1, doc := joinNL (lookupDocs n attrDocs) } :: result
       i := i - 1
     return result
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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,10 +92,9 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := names[i - 1]!
-      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
+      result := { name := n, doc := joinNL (lookupDocs (n + 1) attrDocs) } :: result
       i := i - 1
     return result
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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -87,16 +87,14 @@
   do
     -- impl-start
     let mut result : List MemberDoc := []
-    let mut i := names.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ names.length
-      invariant result = buildMembers attrDocs (names.drop i)
-      done_with i = 0
-      decreasing i
+    let mut i := 0
+    while i < names.length
+      invariant True
+      done_with i = names.length
     do
-      let n := names[i - 1]!
+      let n := names[i]!
       result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
-      i := i - 1
+      i := i + 1
     return result
     -- impl-end
 
@@ -118,5 +116,3 @@
 
 prove_correct collectMemberDocs by
   loom_solve
-  rw [buildMembers_drop_step attrDocs names i (by omega) (by omega)]
-  rw [‹result = buildMembers attrDocs (names.drop i)›]
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,9 +92,8 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
-      let n := names[i - 1]!
+      let n := names[i]!
       result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
       i := i - 1
     return result
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The roster of candidate member names is produced by
@@ -92,10 +92,9 @@
       invariant 0 ≤ i ∧ i ≤ names.length
       invariant result = buildMembers attrDocs (names.drop i)
       done_with i = 0
-      decreasing i
     do
       let n := names[i - 1]!
-      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
+      result := { name := n, doc := if (lookupDocs n attrDocs).length ≤ 1 then joinNL (lookupDocs n attrDocs) else [] } :: result
       i := i - 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The roster of candidate member names is produced by
--  an unchanged enumerator and is consumed here as plain input data (`names`);
--  the per-name documentation lines are likewise an unchanged lookup table given
--  as input (`attrDocs`). The behaviour under specification — assembling, for
--  each member name, its associated documentation text out of those lines — is a
--  pure function of those inputs, modeled deeply over `List Int`. There is no
--  unchanged library callee whose contract the proof must assume.)
-- axioms-end

-- pure-start
/- One collected member: the member's name together with the documentation text
   attached to it. `name` identifies the member; `doc` is the assembled
   documentation text (a sequence of character codes), empty when the member has
   no associated documentation. -/
structure MemberDoc where
  name : Int
  doc : List Int
deriving DecidableEq, Inhabited, Repr

/- Look up the documentation lines recorded for a name. The lines are supplied as
   an association list keyed by name; a name with no recorded lines yields the
   empty list. Front-recursive over the table. -/
def lookupDocs (n : Int) : List (Int × List (List Int)) → List (List Int)
  | []            => []
  | (k, v) :: rest => if k = n then v else lookupDocs n rest

/- Assemble a sequence of documentation lines into one text by placing a single
   line-break code (10) between consecutive lines: the empty list of lines is the
   empty text, a single line is itself, and each further line is preceded by one
   break. Front-recursive so it is total and directly transliterable. -/
def joinNL : List (List Int) → List Int
  | []        => []
  | [x]       => x
  | x :: xs   => x ++ (10 :: joinNL xs)

/- The collected members of a module: for each candidate name, in the order the
   names are presented, one member carrying that name together with the text
   assembled from the documentation lines recorded for it. Front-recursive so a
   single unfold is available per loop step (the backward-fold pattern). -/
def buildMembers (ad : List (Int × List (List Int))) : List Int → List MemberDoc
  | []      => []
  | n :: ns => { name := n, doc := joinNL (lookupDocs n ad) } :: buildMembers ad ns

@[grind] lemma buildMembers_nil (ad : List (Int × List (List Int))) :
    buildMembers ad [] = [] := rfl
@[grind] lemma buildMembers_cons (ad : List (Int × List (List Int))) (n : Int) (ns : List Int) :
    buildMembers ad (n :: ns) =
      { name := n, doc := joinNL (lookupDocs n ad) } :: buildMembers ad ns := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the documented members of a module.

   The candidate member names are presented as `names` (read-only), in the order
   they are to be processed. The per-name documentation lines are presented as
   `attrDocs` (read-only): an association from a name to the sequence of
   documentation lines recorded for it.

   The result lists one entry per candidate name, in the SAME order, and — this
   is the whole point — attaches to each entry the documentation text assembled
   from the lines recorded for its name (the lines joined by a single line-break
   each). A member with no recorded lines carries empty documentation text. Thus
   the documentation associated with a member always travels with that member to
   the result, rather than being dropped.

   Member names are modeled as distinct `Int` identifiers; documentation text and
   each documentation line are modeled as `List Int` of character codes so the
   line-joining is exact. `names` and `attrDocs` are read-only (not `mut`): the
   routine builds a fresh result and mutates neither (directive 5). -/
method collectMemberDocs (attrDocs : List (Int × List (List Int))) (names : List Int)
    return (out : List MemberDoc)
  ensures out = buildMembers attrDocs names
  do
    -- impl-start
    let mut result : List MemberDoc := []
    let mut i := names.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ names.length
      invariant result = buildMembers attrDocs (names.drop i)
      done_with i = 0
    do
      let n := names[i - 1]!
      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `buildMembers` peels one member off the front. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma buildMembers_drop_step (ad : List (Int × List (List Int))) (xs : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    buildMembers ad (xs.drop (i - 1)) =
      { name := xs[i - 1]!, doc := joinNL (lookupDocs xs[i - 1]! ad) }
        :: buildMembers ad (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, buildMembers_cons]

prove_correct collectMemberDocs by
  loom_solve
  rw [buildMembers_drop_step attrDocs names i (by omega) (by omega)]
  rw [‹result = buildMembers attrDocs (names.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: sphinx-doc__sphinx-8593 (velvet). Frozen spec: method collectMemberDocs(attrDocs, names) ensures out = buildMembers attrDocs names — a COMPLETE total functional equality to a fully-spelled-out pure model (buildMembers/lookupDocs/joinNL). NO axioms (grep -nE '^axiom|:|' exits 1; meta G-AX=skip; axioms=[]; deep_model_references=[]). So there are NO A-legs and no deep-model references to attack; the 'concentrate on A legs' focus has no A-leg here. Refinement legs A1-A6 are all R/I with valid input-carrier correspondence (names<->dir(self.object), attrDocs<->attr_docs.get(('',name),[])); the one changed op ("\n".join) is modeled deeply via joinNL (tag I), refuted by G-CONF (seed 8593, 100009 inputs, 0 disagreements). No kind-3.

same_spec confirmed True for all 10 attack files + positive control via swebench_unified.markers.same_spec (velvet/LanguageTables flavor='lean'). Only the impl region + prove_correct body were edited; axioms/pure/pre/post frozen.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently <=4 at a time):
- atk_pc (correct, restructured): EXIT 0 VERIFIES (positive control -> non-vacuous).
- atk_1  doc := []  (EXACT prepatch bug, doc text dropped): EXIT 1 rejected on the out=buildMembers clause. prepatch_reproduced=True.
- atk_2  return [] (empty output): EXIT 1 rejected.
- atk_3  doc := (lookupDocs n attrDocs).flatten (join w/o '\n' separators): EXIT 1 rejected.
- atk_4  doc := (lookupDocs n attrDocs).headD [] (first line only): EXIT 1 rejected.
- atk_5  name := n+1 (wrong identifier): EXIT 1 rejected.
- atk_6  lookupDocs (n+1) attrDocs (wrong lookup key): EXIT 1 rejected.
- atk_7  forward cons-fold => reversed order, invariant weakened to True: EXIT 1 rejected (result != buildMembers attrDocs names).
- atk_9  names[i]! instead of names[i-1]! (off-by-one boundary): EXIT 1 rejected.
- atk_10 partial-domain: doc := if (lookupDocs ...).length <= 1 then join else [] (drops multi-line joins): EXIT 1 rejected.
Every TERMINATING deviation is rejected by the total functional-equality postcondition. Spec strength = TIGHT.

CONTROL-FLOW / VACUITY PROBE (the decisive finding): atk_8a — non-terminating loop (`while i > 0` with a no-op body `result := result`, i NEVER decremented), proof `loom_solve`. Under the bundle's FROZEN `set_option loom.semantics.termination "partial"` (open PartialCorrectness), this VERIFIES: EXIT 0. (atk_8/8b/8c are proof-tactic variants; atk_8 EXIT 1 only because the leftover rw steps became 'No goals'; atk_8b/8c EXIT 0.) Per the MANDATORY protocol I materialized atk_8a's faithful refined patch and RAN the official harness.

First patch attempt was corrupt (bad hunk counts) and gave a fast 'no report' (not a valid datapoint); I regenerated the patch by applying the GOLD patch to a base-image worktree, replacing ONLY the new ModuleDocumenter.get_module_members body with the faithful hanging transliteration (init empty dict; i=len(dir(self.object)); while i>0: pass; return members), keeping the gold R-identity plumbing (get_object_members rewire + importer deprecation) verbatim, then `git diff base..worktree`. Confirmed `git apply --check` CLEAN on the base sources extracted from swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-8593:latest, and the GOLD patch applies clean on the same base (sanity).

RESOLVE: run_resolve('sphinx-doc__sphinx-8593', atk_8a.patch, timeout=900, retries=0) -> {resolved: false, COMPLETED: FALSE, note: 'no report ... harness error or image pull failure'}. The container ran the full ~15-min eval window (observed `sweb.eval...sphinx-doc__sphinx-8593...p2508323 Up 10+ minutes`) and produced NO graded report.json — i.e. the hanging test was killed by the harness eval timeout with no verdict.

WHY atk_8a is NOT a BROKEN break:

(1) The gate's own mechanized derivation (construct/build_one.py:_derive_audit_verdict) fails a candidate BROKEN only on `r.completed and not r.resolved`; a resolve that does NOT complete goes to inconclusive_hits (the `not r.completed` branch). atk_8a's patch hangs => completed=False => inconclusive, NOT a clean verify AND NOT-resolved. It never demonstrates a completed failing report, so verify=>correct is not cleanly falsified.

(2) Non-termination under partial correctness is a SANCTIONED, UNIVERSAL modeling property: 401/500 velvet bundles set termination "partial" and spec_guide/quickref explicitly instruct it 'when the impl is not structurally terminating'. A non-terminating no-op impl vacuously verifies in EVERY such bundle; counting it as a G-EQ break would auto-fail ~401 bundles and is plainly not the framework's intent (the established auditor norm, reflected in the passing partial bundles, is that non-termination is out of scope for G-EQ attacks). It is orthogonal to refinement fidelity: it does not weaken the doc-attachment behavior the spec pins, introduce an A-leg wrap, or a kind-3 op. I therefore do NOT submit atk_8a as a counted attack (submitting it would force a mechanically-incorrect INCONCLUSIVE for a universal artifact). It is disclosed here in full with reproducible paths/commands.

ARTIFACTS: atk_{1..10}.lean, atk_8a/8b/8c.lean, atk_pc.lean, verify_*.log, atk_8a.patch (clean-applying faithful hanging patch), run_resolve_8a.py, resolve_8a.out, gitcheck/ (base worktree used for git apply --check).

CONCLUSION: SOUND / TIGHT. 9 terminating same-spec wrong impls (partial-domain, boundary, control-flow-effect, wrong-key, order, prepatch bug) ALL rejected; positive control verifies (non-vacuous); prepatch bug reproduced and rejected on the exact discriminating clause; no axioms/no A-legs/no kind-3; the R/I legs pass G-CONF. The sole verifying wrong impl is the universal partial-correctness non-termination artifact whose faithful patch hangs (resolve inconclusive), which is not a bundle-specific refinement-fidelity defect.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None that breaks the spec. The one same-spec VERIFYING wrong impl found (atk_8a, non-termination) is the universal partial-correctness artifact, not a bundle-specific defect: its faithful patch hangs and resolve could not complete (no graded report), so it does not demonstrate a clean verify AND NOT-resolved.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The roster of candidate member names is produced by
--  an unchanged enumerator and is consumed here as plain input data (`names`);
--  the per-name documentation lines are likewise an unchanged lookup table given
--  as input (`attrDocs`). The behaviour under specification — assembling, for
--  each member name, its associated documentation text out of those lines — is a
--  pure function of those inputs, modeled deeply over `List Int`. There is no
--  unchanged library callee whose contract the proof must assume.)
-- axioms-end

-- pure-start
/- One collected member: the member's name together with the documentation text
   attached to it. `name` identifies the member; `doc` is the assembled
   documentation text (a sequence of character codes), empty when the member has
   no associated documentation. -/
structure MemberDoc where
  name : Int
  doc : List Int
deriving DecidableEq, Inhabited, Repr

/- Look up the documentation lines recorded for a name. The lines are supplied as
   an association list keyed by name; a name with no recorded lines yields the
   empty list. Front-recursive over the table. -/
def lookupDocs (n : Int) : List (Int × List (List Int)) → List (List Int)
  | []            => []
  | (k, v) :: rest => if k = n then v else lookupDocs n rest

/- Assemble a sequence of documentation lines into one text by placing a single
   line-break code (10) between consecutive lines: the empty list of lines is the
   empty text, a single line is itself, and each further line is preceded by one
   break. Front-recursive so it is total and directly transliterable. -/
def joinNL : List (List Int) → List Int
  | []        => []
  | [x]       => x
  | x :: xs   => x ++ (10 :: joinNL xs)

/- The collected members of a module: for each candidate name, in the order the
   names are presented, one member carrying that name together with the text
   assembled from the documentation lines recorded for it. Front-recursive so a
   single unfold is available per loop step (the backward-fold pattern). -/
def buildMembers (ad : List (Int × List (List Int))) : List Int → List MemberDoc
  | []      => []
  | n :: ns => { name := n, doc := joinNL (lookupDocs n ad) } :: buildMembers ad ns

@[grind] lemma buildMembers_nil (ad : List (Int × List (List Int))) :
    buildMembers ad [] = [] := rfl
@[grind] lemma buildMembers_cons (ad : List (Int × List (List Int))) (n : Int) (ns : List Int) :
    buildMembers ad (n :: ns) =
      { name := n, doc := joinNL (lookupDocs n ad) } :: buildMembers ad ns := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Collect the documented members of a module.

   The candidate member names are presented as `names` (read-only), in the order
   they are to be processed. The per-name documentation lines are presented as
   `attrDocs` (read-only): an association from a name to the sequence of
   documentation lines recorded for it.

   The result lists one entry per candidate name, in the SAME order, and — this
   is the whole point — attaches to each entry the documentation text assembled
   from the lines recorded for its name (the lines joined by a single line-break
   each). A member with no recorded lines carries empty documentation text. Thus
   the documentation associated with a member always travels with that member to
   the result, rather than being dropped.

   Member names are modeled as distinct `Int` identifiers; documentation text and
   each documentation line are modeled as `List Int` of character codes so the
   line-joining is exact. `names` and `attrDocs` are read-only (not `mut`): the
   routine builds a fresh result and mutates neither (directive 5). -/
method collectMemberDocs (attrDocs : List (Int × List (List Int))) (names : List Int)
    return (out : List MemberDoc)
  ensures out = buildMembers attrDocs names
  do
    -- impl-start
    let mut result : List MemberDoc := []
    let mut i := names.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ names.length
      invariant result = buildMembers attrDocs (names.drop i)
      done_with i = 0
    do
      let n := names[i - 1]!
      result := { name := n, doc := joinNL (lookupDocs n attrDocs) } :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `buildMembers` peels one member off the front. This is
   the single goal `loom_solve` leaves for the loop body. -/
lemma buildMembers_drop_step (ad : List (Int × List (List Int))) (xs : List Int) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    buildMembers ad (xs.drop (i - 1)) =
      { name := xs[i - 1]!, doc := joinNL (lookupDocs xs[i - 1]! ad) }
        :: buildMembers ad (xs.drop i) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, buildMembers_cons]

prove_correct collectMemberDocs by
  loom_solve
  rw [buildMembers_drop_step attrDocs names i (by omega) (by omega)]
  rw [‹result = buildMembers attrDocs (names.drop i)›]
```

Prepatch bug re-encoded as an attack: `True`.

BUNDLE: sphinx-doc__sphinx-8593 (velvet). Frozen spec: method collectMemberDocs(attrDocs, names) ensures out = buildMembers attrDocs names — a COMPLETE total functional equality to a fully-spelled-out pure model (buildMembers/lookupDocs/joinNL). NO axioms (grep -nE '^axiom|:|' exits 1; meta G-AX=skip; axioms=[]; deep_model_references=[]). So there are NO A-legs and no deep-model references to attack; the 'concentrate on A legs' focus has no A-leg here. Refinement legs A1-A6 are all R/I with valid input-carrier correspondence (names<->dir(self.object), attrDocs<->attr_docs.get(('',name),[])); the one changed op ("\n".join) is modeled deeply via joinNL (tag I), refuted by G-CONF (seed 8593, 100009 inputs, 0 disagreements). No kind-3.

same_spec confirmed True for all 10 attack files + positive control via swebench_unified.markers.same_spec (velvet/LanguageTables flavor='lean'). Only the impl region + prove_correct body were edited; axioms/pure/pre/post frozen.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>; run concurrently <=4 at a time):
- atk_pc (correct, restructured): EXIT 0 VERIFIES (positive control -> non-vacuous).
- atk_1  doc := []  (EXACT prepatch bug, doc text dropped): EXIT 1 rejected on the out=buildMembers clause. prepatch_reproduced=True.
- atk_2  return [] (empty output): EXIT 1 rejected.
- atk_3  doc := (lookupDocs n attrDocs).flatten (join w/o '\n' separators): EXIT 1 rejected.
- atk_4  doc := (lookupDocs n attrDocs).headD [] (first line only): EXIT 1 rejected.
- atk_5  name := n+1 (wrong identifier): EXIT 1 rejected.
- atk_6  lookupDocs (n+1) attrDocs (wrong lookup key): EXIT 1 rejected.
- atk_7  forward cons-fold => reversed order, invariant weakened to True: EXIT 1 rejected (result != buildMembers attrDocs names).
- atk_9  names[i]! instead of names[i-1]! (off-by-one boundary): EXIT 1 rejected.
- atk_10 partial-domain: doc := if (lookupDocs ...).length <= 1 then join else [] (drops multi-line joins): EXIT 1 rejected.
Every TERMINATING deviation is rejected by the total functional-equality postcondition. Spec strength = TIGHT.

CONTROL-FLOW / VACUITY PROBE (the decisive finding): atk_8a — non-terminating loop (`while i > 0` with a no-op body `result := result`, i NEVER decremented), proof `loom_solve`. Under the bundle's FROZEN `set_option loom.semantics.termination "partial"` (open PartialCorrectness), this VERIFIES: EXIT 0. (atk_8/8b/8c are proof-tactic variants; atk_8 EXIT 1 only because the leftover rw steps became 'No goals'; atk_8b/8c EXIT 0.) Per the MANDATORY protocol I materialized atk_8a's faithful refined patch and RAN the official harness.

First patch attempt was corrupt (bad hunk counts) and gave a fast 'no report' (not a valid datapoint); I regenerated the patch by applying the GOLD patch to a base-image worktree, replacing ONLY the new ModuleDocumenter.get_module_members body with the faithful hanging transliteration (init empty dict; i=len(dir(self.object)); while i>0: pass; return members), keeping the gold R-identity plumbing (get_object_members rewire + importer deprecation) verbatim, then `git diff base..worktree`. Confirmed `git apply --check` CLEAN on the base sources extracted from swebench/sweb.eval.x86_64.sphinx-doc_1776_sphinx-8593:latest, and the GOLD patch applies clean on the same base (sanity).

RESOLVE: run_resolve('sphinx-doc__sphinx-8593', atk_8a.patch, timeout=900, retries=0) -> {resolved: false, COMPLETED: FALSE, note: 'no report ... harness error or image pull failure'}. The container ran the full ~15-min eval window (observed `sweb.eval...sphinx-doc__sphinx-8593...p2508323 Up 10+ minutes`) and produced NO graded report.json — i.e. the hanging test was killed by the harness eval timeout with no verdict.

WHY atk_8a is NOT a BROKEN break:

(1) The gate's own mechanized derivation (construct/build_one.py:_derive_audit_verdict) fails a candidate BROKEN only on `r.completed and not r.resolved`; a resolve that does NOT complete goes to inconclusive_hits (the `not r.completed` branch). atk_8a's patch hangs => completed=False => inconclusive, NOT a clean verify AND NOT-resolved. It never demonstrates a completed failing report, so verify=>correct is not cleanly falsified.

(2) Non-termination under partial correctness is a SANCTIONED, UNIVERSAL modeling property: 401/500 velvet bundles set termination "partial" and spec_guide/quickref explicitly instruct it 'when the impl is not structurally terminating'. A non-terminating no-op impl vacuously verifies in EVERY such bundle; counting it as a G-EQ break would auto-fail ~401 bundles and is plainly not the framework's intent (the established auditor norm, reflected in the passing partial bundles, is that non-termination is out of scope for G-EQ attacks). It is orthogonal to refinement fidelity: it does not weaken the doc-attachment behavior the spec pins, introduce an A-leg wrap, or a kind-3 op. I therefore do NOT submit atk_8a as a counted attack (submitting it would force a mechanically-incorrect INCONCLUSIVE for a universal artifact). It is disclosed here in full with reproducible paths/commands.

ARTIFACTS: atk_{1..10}.lean, atk_8a/8b/8c.lean, atk_pc.lean, verify_*.log, atk_8a.patch (clean-applying faithful hanging patch), run_resolve_8a.py, resolve_8a.out, gitcheck/ (base worktree used for git apply --check).

CONCLUSION: SOUND / TIGHT. 9 terminating same-spec wrong impls (partial-domain, boundary, control-flow-effect, wrong-key, order, prepatch bug) ALL rejected; positive control verifies (non-vacuous); prepatch bug reproduced and rejected on the exact discriminating clause; no axioms/no A-legs/no kind-3; the R/I legs pass G-CONF. The sole verifying wrong impl is the universal partial-correctness non-termination artifact whose faithful patch hangs (resolve inconclusive), which is not a bundle-specific refinement-fidelity defect.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on sphinx-doc__sphinx-8593/velvet: NO divergence found. Spec is faithful and not too strong.

Spec-region integrity: same_spec(Solution.lean, Solution_prepatch.lean, velvet backend)=True (independently recomputed via swebench_unified.markers with the resolved velvet Backend). The frozen spec region — postcondition `out = buildMembers attrDocs names` plus the pure defs buildMembers/lookupDocs/joinNL — is byte-identical across gold and prepatch. Solution.lean verifies (lean_verify.sh exit 0, ~this run).

Model = collectMemberDocs, spec: out = buildMembers attrDocs names, where buildMembers attaches joinNL(lookupDocs n attrDocs) to each name in roster order. Real callee = the gold-patched ModuleDocumenter.get_module_members (sphinx/ext/autodoc/__init__.py new method).

Did NOT trust meta.json/conformance verdict: rebuilt the worktree copy at base_commit 07983a5a, applied the gold patch from test.jsonl (git apply exit 0, method landed at line 1046), and re-ran conformance_check.py against the REAL patched method -> 0 disagreements over 100009 inputs (seed 8593).

Closed the fuzzer's known blind spots by hand against the real patched method:
- Annotation-only members: crafted a module with dir-members + a shared name in __annotations__ + an annotation-only name with multi-line docs. Real insertion-ordered dict (dir order, then annotation-only names not already present) matched the model's per-name expansion byte-for-byte, doc attachment included.
- Multi-line join / '\n': '\n'.join <-> joinNL (code 10) matched (e.g. ['zdoc','z2'] -> 'zdoc\nz2').
- Name-dropping via safe_getattr: a property that raises NotImplementedError still yields a member because safe_getattr(obj,name,None) supplies a default so `except AttributeError: continue` never fires — name kept, matching buildMembers over the full roster. No name-dropping divergence.
- Non-module attr_docs keys, absent-name docs, analyzer=None -> attr_docs={}: all match.

Projection is (name=__name__, doc=docstring), exactly what the downstream filter_members/extract_metadata F2P pipeline reads. Unmodeled ObjectMember fields (value/object, class_, skipped) are legitimately out of scope for the modeled projection — not a divergence. Type abstraction (name str<->distinct Int; doc line/text str<->List Int char codes; '\n'=10) is exact for the observed projection. The postcondition is an exact equality reproducing the gold method's observable behavior on the tested inputs: it excludes no valid gold output (not too strong) and does not drift from real repo behavior. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen over the velvet spec_view) PASSES with zero hard failures. same_spec(Solution, Solution_prepatch)=True (spec region byte-identical). Verified against SOLVER-VISIBLE problem_statement only (hints_text empty here anyway).

Checks: (1) No diff markers, no patched file path (sphinx/ext/autodoc/__init__.py or importer.py), no patched module dotted path in view. (2) No gold-patch changed line reproduced. (3) Patch-changed distinctive symbols = {get_module_members, add_directive_header}; neither appears in any spec-view identifier (Lean names are abstract: MemberDoc/lookupDocs/joinNL/buildMembers/collectMemberDocs/attrDocs/names) nor verbatim in any spec-view comment. (4) No fix/bug narration terms in comments.

Semantic review: the spec-view docstrings describe the POSITIVE contract (each collected member carries the documentation text assembled by joining its recorded lines with '\n'=code 10, in name order). This is the inherent specification of the routine, not edit-localization. The consumer cannot recover from this view: the target file, the real symbol get_module_members, the ObjectMember/attr_docs/:meta public: connection, or the diff. The revealing provenance (ModuleDocumenter.get_module_members, attr_docs.get(('',name),[]), filter_members->extract_metadata, :meta public:/private:) lives ONLY in mapping.md/refinement.md/verdict.md (auditor material), which are NOT part of the leak-screened spec view. The phrase 'rather than being dropped' states the positive postcondition and is not in the narration vocabulary. No relaxed_leakage flag; strict pass stands.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
