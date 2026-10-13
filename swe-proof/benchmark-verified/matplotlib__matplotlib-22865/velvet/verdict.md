# P2 adversarial audit — matplotlib__matplotlib-22865

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
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_ctrl2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The only verifying non-gold-equal impls are DIVERGENT (atk_div3/atk_div4), and their materialized faithful patch (an infinite loop) does not RUN to a resolved=False verdict — the harness raises EvaluationError: Test timed out and writes NO report.json (run_resolve -> completed=False = inconclusive, NOT resolved=False). That is not the verify->correct break condition (build_one.py:305-314), and divergence is a framework-universal partial-correctness artifact, not a refinement-fidelity defect.
```

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
 
 /- Separator-line selection for a colour scale rendered as a strip of coloured
    cells with optional dividing lines between adjacent cells.
@@ -79,13 +79,9 @@
   ensures out = selectSeg segs drawEdges extLow extUp
   do
     -- impl-start
-    -- Lower bound of the kept run: keep the boundary at the open lower end,
-    -- otherwise start one in (drop the boundary touching a closed lower end).
-    let s : Nat := if extLow then 0 else 1
-    -- Upper bound (exclusive): keep through the boundary at the open upper end,
-    -- otherwise stop one short (drop the boundary touching a closed upper end).
-    let e : Nat := if extUp then segs.length else segs.length - 1
-    -- The contiguous slice [s, e) of the candidate list.
+    -- WRONG (prepatch): drop both end boundaries unconditionally, ignoring flags.
+    let s : Nat := 1
+    let e : Nat := segs.length - 1
     let selected : List Seg := (segs.drop s).take (e - s)
     let out : List Seg := if drawEdges then selected else []
     return out
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
 
 /- Separator-line selection for a colour scale rendered as a strip of coloured
    cells with optional dividing lines between adjacent cells.
@@ -79,15 +79,8 @@
   ensures out = selectSeg segs drawEdges extLow extUp
   do
     -- impl-start
-    -- Lower bound of the kept run: keep the boundary at the open lower end,
-    -- otherwise start one in (drop the boundary touching a closed lower end).
-    let s : Nat := if extLow then 0 else 1
-    -- Upper bound (exclusive): keep through the boundary at the open upper end,
-    -- otherwise stop one short (drop the boundary touching a closed upper end).
-    let e : Nat := if extUp then segs.length else segs.length - 1
-    -- The contiguous slice [s, e) of the candidate list.
-    let selected : List Seg := (segs.drop s).take (e - s)
-    let out : List Seg := if drawEdges then selected else []
+    -- WRONG (partial-domain): never draw any divider.
+    let out : List Seg := []
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
 
 /- Separator-line selection for a colour scale rendered as a strip of coloured
    cells with optional dividing lines between adjacent cells.
@@ -79,13 +79,9 @@
   ensures out = selectSeg segs drawEdges extLow extUp
   do
     -- impl-start
-    -- Lower bound of the kept run: keep the boundary at the open lower end,
-    -- otherwise start one in (drop the boundary touching a closed lower end).
-    let s : Nat := if extLow then 0 else 1
-    -- Upper bound (exclusive): keep through the boundary at the open upper end,
-    -- otherwise stop one short (drop the boundary touching a closed upper end).
+    -- WRONG (boundary): closed lower drops TWO boundaries instead of one.
+    let s : Nat := if extLow then 0 else 2
     let e : Nat := if extUp then segs.length else segs.length - 1
-    -- The contiguous slice [s, e) of the candidate list.
     let selected : List Seg := (segs.drop s).take (e - s)
     let out : List Seg := if drawEdges then selected else []
     return out
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
 
 /- Separator-line selection for a colour scale rendered as a strip of coloured
    cells with optional dividing lines between adjacent cells.
@@ -79,13 +79,9 @@
   ensures out = selectSeg segs drawEdges extLow extUp
   do
     -- impl-start
-    -- Lower bound of the kept run: keep the boundary at the open lower end,
-    -- otherwise start one in (drop the boundary touching a closed lower end).
-    let s : Nat := if extLow then 0 else 1
-    -- Upper bound (exclusive): keep through the boundary at the open upper end,
-    -- otherwise stop one short (drop the boundary touching a closed upper end).
-    let e : Nat := if extUp then segs.length else segs.length - 1
-    -- The contiguous slice [s, e) of the candidate list.
+    -- WRONG (flag swap): lower keyed on extUp, upper keyed on extLow.
+    let s : Nat := if extUp then 0 else 1
+    let e : Nat := if extLow then segs.length else segs.length - 1
     let selected : List Seg := (segs.drop s).take (e - s)
     let out : List Seg := if drawEdges then selected else []
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
 
 /- Separator-line selection for a colour scale rendered as a strip of coloured
    cells with optional dividing lines between adjacent cells.
@@ -79,16 +79,11 @@
   ensures out = selectSeg segs drawEdges extLow extUp
   do
     -- impl-start
-    -- Lower bound of the kept run: keep the boundary at the open lower end,
-    -- otherwise start one in (drop the boundary touching a closed lower end).
+    -- WRONG (control-flow): return the slice even when drawEdges is off.
     let s : Nat := if extLow then 0 else 1
-    -- Upper bound (exclusive): keep through the boundary at the open upper end,
-    -- otherwise stop one short (drop the boundary touching a closed upper end).
     let e : Nat := if extUp then segs.length else segs.length - 1
-    -- The contiguous slice [s, e) of the candidate list.
     let selected : List Seg := (segs.drop s).take (e - s)
-    let out : List Seg := if drawEdges then selected else []
-    return out
+    return selected
     -- impl-end
 
 prove_correct selectSegM by
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
 
 /- Separator-line selection for a colour scale rendered as a strip of coloured
    cells with optional dividing lines between adjacent cells.
@@ -79,13 +79,9 @@
   ensures out = selectSeg segs drawEdges extLow extUp
   do
     -- impl-start
-    -- Lower bound of the kept run: keep the boundary at the open lower end,
-    -- otherwise start one in (drop the boundary touching a closed lower end).
-    let s : Nat := if extLow then 0 else 1
-    -- Upper bound (exclusive): keep through the boundary at the open upper end,
-    -- otherwise stop one short (drop the boundary touching a closed upper end).
+    -- WRONG (negation): lower branch inverted.
+    let s : Nat := if extLow then 1 else 0
     let e : Nat := if extUp then segs.length else segs.length - 1
-    -- The contiguous slice [s, e) of the candidate list.
     let selected : List Seg := (segs.drop s).take (e - s)
     let out : List Seg := if drawEdges then selected else []
     return out
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
 
 /- Separator-line selection for a colour scale rendered as a strip of coloured
    cells with optional dividing lines between adjacent cells.
@@ -79,13 +79,9 @@
   ensures out = selectSeg segs drawEdges extLow extUp
   do
     -- impl-start
-    -- Lower bound of the kept run: keep the boundary at the open lower end,
-    -- otherwise start one in (drop the boundary touching a closed lower end).
+    -- WRONG (boundary upper): closed upper keeps through segs.length (drops nothing).
     let s : Nat := if extLow then 0 else 1
-    -- Upper bound (exclusive): keep through the boundary at the open upper end,
-    -- otherwise stop one short (drop the boundary touching a closed upper end).
-    let e : Nat := if extUp then segs.length else segs.length - 1
-    -- The contiguous slice [s, e) of the candidate list.
+    let e : Nat := if extUp then segs.length else segs.length
     let selected : List Seg := (segs.drop s).take (e - s)
     let out : List Seg := if drawEdges then selected else []
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- Separator-line selection for a colour scale rendered as a strip of coloured
   cells with optional dividing lines between adjacent cells.

   The full list of candidate dividers has one entry per internal cell
   boundary of the assembled strip, in order from one end to the other. When
   dividing lines are disabled the selection is empty. When enabled, the
   selection is the contiguous run of boundaries that lie strictly between the
   two outermost cells UNLESS an end is "open" (the scale continues past that
   end with a pointed/extended cap), in which case the boundary touching that
   open end is also kept. So an open lower end keeps the first boundary, and an
   open upper end keeps the last boundary; a closed end drops the boundary
   adjacent to it.

   The model below performs that selection abstractly as a positional slice of
   the candidate list; no callee is axiomatized because the selection is the
   only computation (the open-end flags are plain booleans supplied by the
   caller). -/

-- axioms-start
-- axioms-end

-- pure-start
/- A single candidate divider, modelled by its flattened coordinate entries
   (the operation is purely positional, so the segment's content is opaque to
   the selection). -/
abbrev Seg := List Float

/- The lower start index: 0 when the lower end is open (keep the first
   boundary), 1 when it is closed (drop the boundary adjacent to the closed
   lower end). -/
def startIdx (extLow : Bool) : Nat := if extLow then 0 else 1

/- The upper end index (exclusive): the full length when the upper end is open
   (keep the last boundary), one less when it is closed (drop the boundary
   adjacent to the closed upper end). -/
def endIdx (extUp : Bool) (n : Nat) : Nat := if extUp then n else n - 1

/- The selected dividers: empty when dividing lines are disabled; otherwise the
   contiguous sub-run of the candidate list from `startIdx` (inclusive) to
   `endIdx` (exclusive). Expressed as drop-then-take so it is a faithful
   positional slice over a `List`. -/
def selectSeg (segs : List Seg) (drawEdges : Bool) (extLow : Bool) (extUp : Bool) :
    List Seg :=
  if drawEdges then
    (segs.drop (startIdx extLow)).take (endIdx extUp segs.length - startIdx extLow)
  else
    []

@[grind] lemma selectSeg_eq (segs : List Seg) (drawEdges extLow extUp : Bool) :
    selectSeg segs drawEdges extLow extUp =
      (if drawEdges then
        (segs.drop (startIdx extLow)).take (endIdx extUp segs.length - startIdx extLow)
      else []) := rfl
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose which dividing lines between adjacent colour cells are drawn.
   `segs` is the ordered list of candidate dividers (one per internal boundary
   of the assembled strip); `drawEdges` enables the lines at all; `extLow` /
   `extUp` say whether the lower / upper end of the scale is open (extended past
   the outermost cell with a pointed/rectangular cap). The result is the subset
   of candidates that are actually drawn. -/
method selectSegM (segs : List Seg) (drawEdges : Bool) (extLow : Bool) (extUp : Bool)
    return (out : List Seg)
  ensures out = selectSeg segs drawEdges extLow extUp
  do
    -- impl-start
    -- CORRECT, structurally different: take e then drop s (List-equal to drop-then-take).
    let s : Nat := if extLow then 0 else 1
    let e : Nat := if extUp then segs.length else segs.length - 1
    let selected : List Seg := (segs.take e).drop s
    let out : List Seg := if drawEdges then selected else []
    return out
    -- impl-end

prove_correct selectSegM by
  loom_solve
  simp [selectSeg, startIdx, endIdx, List.drop_take]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EVIDENCE (all; verifier scripts/lean_verify.sh; same_spec=swebench_unified.markers.same_spec over velvet). PY=python for module imports.

SPEC SHAPE: postcondition `ensures out = selectSeg segs drawEdges extLow extUp` is a TOTAL, unconditional functional equality (no `require`) over concrete TOTAL computable functions selectSeg/startIdx/endIdx. Axioms region empty; refinement.md has 0 A-legs, 0 kind-3 (all legs R/I/I+R). The A-legs the prompt asks me to focus on are VACUOUS here (mapping.md §3: 0 consumed axioms, 0 A-references). I independently reconfirmed the R/I fidelity: transliterated selectSeg vs the patched slice `np.dstack([X,Y])[start_idx:end_idx]` agree on the full (n=0..5)×(drawEdges,extLow,extUp) matrix (matches G-CONF's 100640-input, 0-disagreement result).

### ATTACKS (each same_spec=True, cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH bug (s=1,e=len-1, ignores flags => constant [1:-1]): verify EXIT=1 REJECTED (this is the G-DIFF prepatch reproduction; fails on open-end inputs). prepatch_reproduced=true.
- atk_2 partial-domain (always []): EXIT=1 REJECTED.
- atk_3 boundary (closed lower drops TWO: s=if extLow then 0 else 2): EXIT=1 REJECTED.
- atk_4 flag-swap (lower keyed on extUp, upper on extLow): EXIT=1 REJECTED.
- atk_5 control-flow-effect (returns slice even when drawEdges=false): EXIT=1 REJECTED.
- atk_6 negation (lower branch inverted: s=if extLow then 1 else 0): EXIT=1 REJECTED.
- atk_7 boundary-upper (closed upper keeps through segs.length): EXIT=1 REJECTED.
All 7 terminating wrong-value classes are rejected by the single functional-equality clause; the spec admits no wrong COMPUTED value. (atk_8/9/10 were behaviourally-CORRECT reformulations that fail only the stock proof-tactic block, so not falsifications.)

POSITIVE CONTROL pos_ctrl2.lean: structurally-different CORRECT impl `(segs.take e).drop s` with proof `loom_solve; simp[...,List.drop_take]` — same_spec=True, verify EXIT=0 (non-vacuity). pos_control.lean (byte copy of bundle Solution.lean) also verifies EXIT=0.

### DIVERGENCE PROBE (the only verifying non-gold-equal class, under `loom.semantics.termination "partial"`):
- atk_div3.lean (`while i=0 do i:=0; return []`, proof loom_solve) and atk_div4.lean (`while k>0 do k:=k+1; return segs`) both same_spec=True and VERIFY EXIT=0 — vacuously partial-correct.
- I MATERIALIZED the faithful patch (atk_div3.patch, atk_div4.patch: replace the removed set_segments statement with an unconditional infinite loop, exact gold hunk context @@ -651,8) and RAN it through the official harness THREE independent times via swebench_unified.harness.run_resolve (timeouts 600s, 120s, 90s). ALL THREE returned completed=False, resolved=False, note='no report at ...report.json — harness error'. Captured proof (div3cap_run_instance.log): patch 'Applied patch lib/matplotlib/colorbar.py cleanly', then repeated `swebench.harness.utils.EvaluationError: matplotlib__matplotlib-22865: Test timed out after 90 seconds.` Upstream harness (swebench/harness/run_evaluation.py:206-219) raises EvaluationError on timed_out BEFORE get_eval_report/report.json is written, so run_resolve reports completed=False.
- Per the AUTHORITATIVE mechanized derivation (src/swebench_unified/construct/build_one.py:305-314): `if r.completed and not r.resolved` => fail(verify⇒correct)=BROKEN; `if not r.completed` => INCONCLUSIVE (candidate; resolve did not complete). A hanging patch is the SECOND branch, NOT the break condition. So the divergent attack cannot derive BROKEN; if submitted as an attack it would only force the gate to INCONCLUSIVE (fail-closed, build_one.py:330-333).
- WHY divergence is not a refinement-fidelity defect and is deliberately EXCLUDED from the submitted attack set: (1) it is a framework-universal property of Velvet partial-correctness semantics affecting ALL 401 `partial` bundles identically (401/500 use partial per grep), a sanctioned modeling option (spec_guide.md:112) — not a property of THIS spec's strength; (2) an infinite loop corresponds to NO operation in refinement.md (no R/I/A leg maps to it), so it is not a 'faithful refined patch' of any modeled behaviour; (3) the derivation code explicitly names it a non-defect (build_one.py:224-226: 'None found; only divergence is on an unreachable input'); (4) the harness structurally cannot even produce resolved=False for it. Including it as an attack would falsely fail-close a sound bundle on a universal artifact, so I documented it here with executed evidence rather than listing it in `attacks`.

CONCLUSION: G-EQ SOUND / spec-strength TIGHT. Every terminating same-spec wrong impl is machine-rejected; the sole verifying non-gold-equal impls are divergent, and their materialized faithful patch, when actually RUN, does not produce a completed resolved=False verdict (verify⇒correct break bar not met). Refinement.md legs all R/I, no A-legs (vacuous), no kind-3; model↔patch correspondence independently reconfirmed against the real patched slice.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_ctrl2.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No terminating same-spec wrong impl verifies. The only verifying non-gold-equal impls are DIVERGENT (atk_div3/atk_div4), and their materialized faithful patch (an infinite loop) does not RUN to a resolved=False verdict — the harness raises EvaluationError: Test timed out and writes NO report.json (run_resolve -> completed=False = inconclusive, NOT resolved=False). That is not the verify->correct break condition (build_one.py:305-314), and divergence is a framework-universal partial-correctness artifact, not a refinement-fidelity defect.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_ctrl2.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/- Separator-line selection for a colour scale rendered as a strip of coloured
   cells with optional dividing lines between adjacent cells.

   The full list of candidate dividers has one entry per internal cell
   boundary of the assembled strip, in order from one end to the other. When
   dividing lines are disabled the selection is empty. When enabled, the
   selection is the contiguous run of boundaries that lie strictly between the
   two outermost cells UNLESS an end is "open" (the scale continues past that
   end with a pointed/extended cap), in which case the boundary touching that
   open end is also kept. So an open lower end keeps the first boundary, and an
   open upper end keeps the last boundary; a closed end drops the boundary
   adjacent to it.

   The model below performs that selection abstractly as a positional slice of
   the candidate list; no callee is axiomatized because the selection is the
   only computation (the open-end flags are plain booleans supplied by the
   caller). -/

-- axioms-start
-- axioms-end

-- pure-start
/- A single candidate divider, modelled by its flattened coordinate entries
   (the operation is purely positional, so the segment's content is opaque to
   the selection). -/
abbrev Seg := List Float

/- The lower start index: 0 when the lower end is open (keep the first
   boundary), 1 when it is closed (drop the boundary adjacent to the closed
   lower end). -/
def startIdx (extLow : Bool) : Nat := if extLow then 0 else 1

/- The upper end index (exclusive): the full length when the upper end is open
   (keep the last boundary), one less when it is closed (drop the boundary
   adjacent to the closed upper end). -/
def endIdx (extUp : Bool) (n : Nat) : Nat := if extUp then n else n - 1

/- The selected dividers: empty when dividing lines are disabled; otherwise the
   contiguous sub-run of the candidate list from `startIdx` (inclusive) to
   `endIdx` (exclusive). Expressed as drop-then-take so it is a faithful
   positional slice over a `List`. -/
def selectSeg (segs : List Seg) (drawEdges : Bool) (extLow : Bool) (extUp : Bool) :
    List Seg :=
  if drawEdges then
    (segs.drop (startIdx extLow)).take (endIdx extUp segs.length - startIdx extLow)
  else
    []

@[grind] lemma selectSeg_eq (segs : List Seg) (drawEdges extLow extUp : Bool) :
    selectSeg segs drawEdges extLow extUp =
      (if drawEdges then
        (segs.drop (startIdx extLow)).take (endIdx extUp segs.length - startIdx extLow)
      else []) := rfl
-- pure-end

-- pre-conditions-start
-- (one block per modeled method; this bundle models one method)
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose which dividing lines between adjacent colour cells are drawn.
   `segs` is the ordered list of candidate dividers (one per internal boundary
   of the assembled strip); `drawEdges` enables the lines at all; `extLow` /
   `extUp` say whether the lower / upper end of the scale is open (extended past
   the outermost cell with a pointed/rectangular cap). The result is the subset
   of candidates that are actually drawn. -/
method selectSegM (segs : List Seg) (drawEdges : Bool) (extLow : Bool) (extUp : Bool)
    return (out : List Seg)
  ensures out = selectSeg segs drawEdges extLow extUp
  do
    -- impl-start
    -- CORRECT, structurally different: take e then drop s (List-equal to drop-then-take).
    let s : Nat := if extLow then 0 else 1
    let e : Nat := if extUp then segs.length else segs.length - 1
    let selected : List Seg := (segs.take e).drop s
    let out : List Seg := if drawEdges then selected else []
    return out
    -- impl-end

prove_correct selectSegM by
  loom_solve
  simp [selectSeg, startIdx, endIdx, List.drop_take]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EVIDENCE (all; verifier scripts/lean_verify.sh; same_spec=swebench_unified.markers.same_spec over velvet). PY=python for module imports.

SPEC SHAPE: postcondition `ensures out = selectSeg segs drawEdges extLow extUp` is a TOTAL, unconditional functional equality (no `require`) over concrete TOTAL computable functions selectSeg/startIdx/endIdx. Axioms region empty; refinement.md has 0 A-legs, 0 kind-3 (all legs R/I/I+R). The A-legs the prompt asks me to focus on are VACUOUS here (mapping.md §3: 0 consumed axioms, 0 A-references). I independently reconfirmed the R/I fidelity: transliterated selectSeg vs the patched slice `np.dstack([X,Y])[start_idx:end_idx]` agree on the full (n=0..5)×(drawEdges,extLow,extUp) matrix (matches G-CONF's 100640-input, 0-disagreement result).

### ATTACKS (each same_spec=True, cmd: `bash scripts/lean_verify.sh <path>`):
- atk_1 PREPATCH bug (s=1,e=len-1, ignores flags => constant [1:-1]): verify EXIT=1 REJECTED (this is the G-DIFF prepatch reproduction; fails on open-end inputs). prepatch_reproduced=true.
- atk_2 partial-domain (always []): EXIT=1 REJECTED.
- atk_3 boundary (closed lower drops TWO: s=if extLow then 0 else 2): EXIT=1 REJECTED.
- atk_4 flag-swap (lower keyed on extUp, upper on extLow): EXIT=1 REJECTED.
- atk_5 control-flow-effect (returns slice even when drawEdges=false): EXIT=1 REJECTED.
- atk_6 negation (lower branch inverted: s=if extLow then 1 else 0): EXIT=1 REJECTED.
- atk_7 boundary-upper (closed upper keeps through segs.length): EXIT=1 REJECTED.
All 7 terminating wrong-value classes are rejected by the single functional-equality clause; the spec admits no wrong COMPUTED value. (atk_8/9/10 were behaviourally-CORRECT reformulations that fail only the stock proof-tactic block, so not falsifications.)

POSITIVE CONTROL pos_ctrl2.lean: structurally-different CORRECT impl `(segs.take e).drop s` with proof `loom_solve; simp[...,List.drop_take]` — same_spec=True, verify EXIT=0 (non-vacuity). pos_control.lean (byte copy of bundle Solution.lean) also verifies EXIT=0.

### DIVERGENCE PROBE (the only verifying non-gold-equal class, under `loom.semantics.termination "partial"`):
- atk_div3.lean (`while i=0 do i:=0; return []`, proof loom_solve) and atk_div4.lean (`while k>0 do k:=k+1; return segs`) both same_spec=True and VERIFY EXIT=0 — vacuously partial-correct.
- I MATERIALIZED the faithful patch (atk_div3.patch, atk_div4.patch: replace the removed set_segments statement with an unconditional infinite loop, exact gold hunk context @@ -651,8) and RAN it through the official harness THREE independent times via swebench_unified.harness.run_resolve (timeouts 600s, 120s, 90s). ALL THREE returned completed=False, resolved=False, note='no report at ...report.json — harness error'. Captured proof (div3cap_run_instance.log): patch 'Applied patch lib/matplotlib/colorbar.py cleanly', then repeated `swebench.harness.utils.EvaluationError: matplotlib__matplotlib-22865: Test timed out after 90 seconds.` Upstream harness (swebench/harness/run_evaluation.py:206-219) raises EvaluationError on timed_out BEFORE get_eval_report/report.json is written, so run_resolve reports completed=False.
- Per the AUTHORITATIVE mechanized derivation (src/swebench_unified/construct/build_one.py:305-314): `if r.completed and not r.resolved` => fail(verify⇒correct)=BROKEN; `if not r.completed` => INCONCLUSIVE (candidate; resolve did not complete). A hanging patch is the SECOND branch, NOT the break condition. So the divergent attack cannot derive BROKEN; if submitted as an attack it would only force the gate to INCONCLUSIVE (fail-closed, build_one.py:330-333).
- WHY divergence is not a refinement-fidelity defect and is deliberately EXCLUDED from the submitted attack set: (1) it is a framework-universal property of Velvet partial-correctness semantics affecting ALL 401 `partial` bundles identically (401/500 use partial per grep), a sanctioned modeling option (spec_guide.md:112) — not a property of THIS spec's strength; (2) an infinite loop corresponds to NO operation in refinement.md (no R/I/A leg maps to it), so it is not a 'faithful refined patch' of any modeled behaviour; (3) the derivation code explicitly names it a non-defect (build_one.py:224-226: 'None found; only divergence is on an unreachable input'); (4) the harness structurally cannot even produce resolved=False for it. Including it as an attack would falsely fail-close a sound bundle on a universal artifact, so I documented it here with executed evidence rather than listing it in `attacks`.

CONCLUSION: G-EQ SOUND / spec-strength TIGHT. Every terminating same-spec wrong impl is machine-rejected; the sole verifying non-gold-equal impls are divergent, and their materialized faithful patch, when actually RUN, does not produce a completed resolved=False verdict (verify⇒correct break bar not met). Refinement.md legs all R/I, no A-legs (vacuous), no kind-3; model↔patch correspondence independently reconfirmed against the real patched slice.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for velvet bundle matplotlib__matplotlib-22865 (selectSegM divider-segment selection in Colorbar._add_solids).

1. SPEC REGION BYTE-IDENTICAL: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True. The spec view (imports/comments/pure defs selectSeg/startIdx/endIdx + ensures clause) is unchanged; only the impl-region differs (prepatch hardcodes s=1,e=n-1 ignoring the flags). No spec drift between prepatch and impl.

2. LEAN VERIFIES: scripts/lean_verify.sh on Solution.lean exits 0 (no sorry/error).

3. MODEL == REAL REPO BEHAVIOR (no diverging input). Gold patch (colorbar.py:654-660) sets: if drawedges: start_idx=0 if _extend_lower() else 1; end_idx=len(X) if _extend_upper() else -1; set_segments(np.dstack([X,Y])[start_idx:end_idx]) else set_segments([]). Lean model: selectSeg = if drawEdges then (segs.drop (startIdx extLow)).take (endIdx extUp n - startIdx extLow) else [], with startIdx = 0/1, endIdx = n/(n-1). Exhaustively compared the Lean drop/take slice against Python A[start_idx:end_idx] for all (n in 0..7) x extLow x extUp: ZERO mismatches. The one nontrivial R step (Python end_idx=-1 negative index vs Lean exclusive n-1 cut) coincides for every n>=1, and the n=0/1 degenerate cases collapse to [] under both Nat truncated subtraction and Python negative-index slicing. The abstraction of segment content to an opaque Seg=List Float is sound because the modeled statement is purely positional first-axis selection (np.dstack first-axis index selects whole (2x2) blocks; content never inspected).

4. Callee provenance clean: 0 axioms, 0 A-references. _extend_lower/_extend_upper are unchanged upstream INPUTS supplied as extLow/extUp booleans (identity bijection), exercised through the real Colorbar by G-CONF, not axiomatized. conf_skip=false; G-CONF passes (mechanical refutation over >=1e5 inputs, seed 22865).

5. Discriminating behavior (FAIL_TO_PASS both/min/max, PASS_TO_PASS neither) is correctly captured: flag-dependent bounds replace the constant [1:-1]; prepatch (which ignores flags) fails G-DIFF exactly on open-end inputs.

Spec is neither too strong nor drifting. No input found where the modeled function disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean)=True — frozen spec view is byte-identical, so I judged the correct spec. Gold edit is in colorbar.py _add_solids: replaces constant np.dstack([X,Y])[1:-1] with flag-dependent bounds (start_idx=0 if _extend_lower() else 1; end_idx=len(X) if _extend_upper() else -1). Public problem_statement already reveals the corrective behavior: drawedges draws divider lines, with extend='both' the extremity lines wrongly don't show and should be drawn. Ran leakage.screen() directly: PASS, zero hard failures. Confirmed: (L1) no diff markers; no gold-patch line reproduced (abstract (segs.drop s).take(...) is not the numpy dstack slice); (L2) no patched file path (colorbar.py) or module path present; (L2/L5) no spec-view identifier embeds the only distinctive changed symbol 'add_solids'; repo tokens start_idx/end_idx/_extend_lower/_extend_upper/set_segments/dividers appear NOWHERE in the spec view; (L3) no bug/fix narration. Semantic check beyond the lexical screen: the postcondition/comments describe the behavior abstractly (positional slice with startIdx 0/1 on an open-lower flag, endIdx n/n-1 on an open-upper flag), which is the legitimate content of a faithful spec and a formalization of what the public problem statement already states; the model name drawEdges mirrors the public 'drawedges'. Nothing exposes the edit mechanics ([1:-1] -> flag-dependent slice transition, numpy dstack/get_segments surface, the -1 negative-index detail, or the repo call sites) beyond the public problem_statement. No hints_text was consulted (hints_text is empty here anyway). No RELAXED_LEAKAGE.md exists and none is needed — the screen genuinely passes. Spec describes behavior, not the edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
