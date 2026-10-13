# P2 adversarial audit — matplotlib__matplotlib-22865

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,9 +50,8 @@
     (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
   if !drawEdges then
     return []
-  let startIdx := if openLower then 0 else 1
-  let endIdx := if openUpper then segs.length else segs.length - 1
-  return (segs.take endIdx).drop startIdx
+  -- prepatch bug: always trim both terminal separators
+  return (segs.take (segs.length - 1)).drop 1
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,8 +50,9 @@
     (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
   if !drawEdges then
     return []
-  let startIdx := if openLower then 0 else 1
-  let endIdx := if openUpper then segs.length else segs.length - 1
+  -- swapped lower/upper roles
+  let startIdx := if openUpper then 0 else 1
+  let endIdx := if openLower then segs.length else segs.length - 1
   return (segs.take endIdx).drop startIdx
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,8 @@
   if !drawEdges then
     return []
   let startIdx := if openLower then 0 else 1
-  let endIdx := if openUpper then segs.length else segs.length - 1
+  -- boundary: trims two instead of one at closed upper end
+  let endIdx := if openUpper then segs.length else segs.length - 2
   return (segs.take endIdx).drop startIdx
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,8 +48,7 @@
 -- impl-start
 def implementation_colorbarEdgeSegments {α : Type}
     (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
-  if !drawEdges then
-    return []
+  -- control-flow: dropped the !drawEdges empty branch
   let startIdx := if openLower then 0 else 1
   let endIdx := if openUpper then segs.length else segs.length - 1
   return (segs.take endIdx).drop startIdx
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,11 +48,8 @@
 -- impl-start
 def implementation_colorbarEdgeSegments {α : Type}
     (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
-  if !drawEdges then
-    return []
-  let startIdx := if openLower then 0 else 1
-  let endIdx := if openUpper then segs.length else segs.length - 1
-  return (segs.take endIdx).drop startIdx
+  -- ungrounded: ignore all gating, return the whole carrier
+  return segs
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -50,9 +50,9 @@
     (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
   if !drawEdges then
     return []
-  let startIdx := if openLower then 0 else 1
+  -- partial-domain: ignores openLower (start always 0)
   let endIdx := if openUpper then segs.length else segs.length - 1
-  return (segs.take endIdx).drop startIdx
+  return (segs.take endIdx).drop 0
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -48,11 +48,8 @@
 -- impl-start
 def implementation_colorbarEdgeSegments {α : Type}
     (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
-  if !drawEdges then
-    return []
-  let startIdx := if openLower then 0 else 1
-  let endIdx := if openUpper then segs.length else segs.length - 1
-  return (segs.take endIdx).drop startIdx
+  -- echo of the spec RHS (behaviorally identical to gold)
+  return (if drawEdges then (segs.take (if openUpper then segs.length else segs.length - 1)).drop (if openLower then 0 else 1) else [])
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting which interior/boundary separator segments are drawn between adjacent
color bands of a one-dimensional color strip.

The strip carries a list of candidate separator rows, one per band boundary in
order from the lower end to the upper end. Three boolean settings govern the
selection:

* whether boundary separators are drawn at all;
* whether the lower end of the strip is open (so its terminal separator is a
  genuine boundary that must be kept);
* whether the upper end of the strip is open (likewise for the upper terminal
  separator).

When separators are disabled the selection is empty. When enabled, every
separator is kept except those terminal separators sitting at a *closed* end.
-/

-- axioms-start
-- No unchanged callee is invoked as an opaque operation inside the model: the
-- two end-openness settings are passed in as boolean inputs, and the segment
-- carrier is the input list. Hence no `opaque` decls and no consumed axioms.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- `drawEdges` enables separators; `openLower`/`openUpper` say whether the
respective end of the strip is open. `segs` are the candidate separator rows in
order. The kept selection drops a terminal separator only at a *closed* end:
the front separator is dropped iff the lower end is closed, and the back
separator is dropped iff the upper end is closed; if separators are disabled the
selection is empty. -/
def problem_spec_colorbarEdgeSegments {α : Type}
    (drawEdges openLower openUpper : Bool) (segs : List α) (result : List α) : Prop :=
  result =
    (if drawEdges then
        (segs.take (if openUpper then segs.length else segs.length - 1)).drop
          (if openLower then 0 else 1)
      else [])
-- post-conditions-end

-- impl-start
def implementation_colorbarEdgeSegments {α : Type}
    (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
  if !drawEdges then
    return []
  let startIdx := if openLower then 0 else 1
  let endIdx := if openUpper then segs.length else segs.length - 1
  return (segs.take endIdx).drop startIdx
-- impl-end

-- proof-start
theorem correct_colorbarEdgeSegments :
    ∀ {α : Type} (drawEdges openLower openUpper : Bool) (segs : List α),
      problem_spec_colorbarEdgeSegments drawEdges openLower openUpper segs
        (implementation_colorbarEdgeSegments drawEdges openLower openUpper segs) := by
  intro α drawEdges openLower openUpper segs
  unfold problem_spec_colorbarEdgeSegments implementation_colorbarEdgeSegments
  cases drawEdges <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_colorbarEdgeSegments is a TOTAL FUNCTIONAL EQUALITY, result = (if drawEdges then (segs.take (if openUpper then len else len-1)).drop (if openLower then 0 else 1) else []). Any impl whose correct_ closes must return f(...) on every input, i.e. be extensionally identical to gold. So a behaviorally-divergent impl cannot close; there is no verify-not-correct gap. Confirmed by falsification below.

SAME_SPEC: all 8 files (atk_1..7, pos_gold) same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Only impl region edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch bug: always (take len-1).drop 1) rc=1 (does NOT close; residual goal remains).
- atk_2 (swapped openLower/openUpper roles) rc=1.
- atk_3 (boundary: closed-upper trims 2 via len-2 not len-1) rc=1.
- atk_4 (control-flow-effect: dropped the !drawEdges empty-return branch) rc=1.
- atk_5 (ungrounded-oracle: return whole segs, ignore all gating) rc=1.
- atk_6 (partial-domain: ignores openLower, start always 0) rc=1.
- atk_7 (echo of spec RHS, behaviorally identical to gold) rc=0 CLOSES.
- pos_gold (gold impl) rc=0 CLOSES (positive control passes).

### AXIOMS (#print axioms correct_colorbarEdgeSegments appended, re-verified rc=0):
- atk_7: 'does not depend on any axioms' (clean, no sorryAx).
- pos_gold: 'does not depend on any axioms' (clean).

PREPATCH: Solution_prepatch.lean verified rc=1 (does NOT close) => spec genuinely discriminates the bug fix. prepatch_reproduced=true.

MANDATORY RESOLVE ON CLOSING NON-GOLD IMPL: atk_7 is the only closing impl that is not literally pos_gold. It returns the spec RHS verbatim, hence extensionally identical to gold on every input; its faithful refined patch is therefore the gold patch (supplied in patches). Ran it through the official harness: run_resolve('matplotlib__matplotlib-22865', gold_patch, run_id='sbu-audit-atk7-echo', timeout=1800) => RESOLVED: True, note='resolved'. A resolving same-spec echo is NOT a spec weakness under the fixed G-EQ/panel_1 policy. No closing clean-axiom impl has a non-resolving faithful patch => no verify-not-correct witness found.

A-LEG / CORRESPONDENCE AUDIT (refinement.md + mapping.md): refinement.md legs 1-4 tagged I/R/R/R only; declares NO A-consumed and NO A-reference legs, no kind-3 (inexpressible) leg. _extend_lower()/_extend_upper() are UNCHANGED callees whose boolean RESULTS enter the model as free inputs openLower/openUpper (not invoked as opaque ops inside the model); np.dstack([X,Y]) enters as identity List a carrier (element values never inspected by the axis-0 slice). Because the spec forall-quantifies over all 3 bool combos and over generic element type alpha, faithfulness cannot depend on callee internals or axis-inversion caveats — there is no axiom to exploit and no ungrounded oracle. axiom_check.py is a justified G-AX skip stub (no opaque decl, no axiom <callee>_prop in Solution.lean). Solution.lean confirmed: axioms-start/end region contains only comments; no opaque/axiom decls. Correspondence to real callees (colorbar.py:651-660, _extend_lower/_extend_upper at 1352/1357) holds per mapping.md and matches base_commit source cited in verdict.md.

CONCLUSION: >=6 distinct genuinely-wrong same-spec impls attempted (partial-domain, boundary, control-flow-effect, ungrounded-oracle, swapped-roles, prepatch); none closes. The one closing non-gold impl (echo) resolves. Verify => correct holds for this spec. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_gold.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_gold.lean`

```lean
import Mathlib
-- imports-end

/-!
Selecting which interior/boundary separator segments are drawn between adjacent
color bands of a one-dimensional color strip.

The strip carries a list of candidate separator rows, one per band boundary in
order from the lower end to the upper end. Three boolean settings govern the
selection:

* whether boundary separators are drawn at all;
* whether the lower end of the strip is open (so its terminal separator is a
  genuine boundary that must be kept);
* whether the upper end of the strip is open (likewise for the upper terminal
  separator).

When separators are disabled the selection is empty. When enabled, every
separator is kept except those terminal separators sitting at a *closed* end.
-/

-- axioms-start
-- No unchanged callee is invoked as an opaque operation inside the model: the
-- two end-openness settings are passed in as boolean inputs, and the segment
-- carrier is the input list. Hence no `opaque` decls and no consumed axioms.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- `drawEdges` enables separators; `openLower`/`openUpper` say whether the
respective end of the strip is open. `segs` are the candidate separator rows in
order. The kept selection drops a terminal separator only at a *closed* end:
the front separator is dropped iff the lower end is closed, and the back
separator is dropped iff the upper end is closed; if separators are disabled the
selection is empty. -/
def problem_spec_colorbarEdgeSegments {α : Type}
    (drawEdges openLower openUpper : Bool) (segs : List α) (result : List α) : Prop :=
  result =
    (if drawEdges then
        (segs.take (if openUpper then segs.length else segs.length - 1)).drop
          (if openLower then 0 else 1)
      else [])
-- post-conditions-end

-- impl-start
def implementation_colorbarEdgeSegments {α : Type}
    (drawEdges openLower openUpper : Bool) (segs : List α) : List α := Id.run do
  if !drawEdges then
    return []
  let startIdx := if openLower then 0 else 1
  let endIdx := if openUpper then segs.length else segs.length - 1
  return (segs.take endIdx).drop startIdx
-- impl-end

-- proof-start
theorem correct_colorbarEdgeSegments :
    ∀ {α : Type} (drawEdges openLower openUpper : Bool) (segs : List α),
      problem_spec_colorbarEdgeSegments drawEdges openLower openUpper segs
        (implementation_colorbarEdgeSegments drawEdges openLower openUpper segs) := by
  intro α drawEdges openLower openUpper segs
  unfold problem_spec_colorbarEdgeSegments implementation_colorbarEdgeSegments
  cases drawEdges <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_colorbarEdgeSegments is a TOTAL FUNCTIONAL EQUALITY, result = (if drawEdges then (segs.take (if openUpper then len else len-1)).drop (if openLower then 0 else 1) else []). Any impl whose correct_ closes must return f(...) on every input, i.e. be extensionally identical to gold. So a behaviorally-divergent impl cannot close; there is no verify-not-correct gap. Confirmed by falsification below.

SAME_SPEC: all 8 files (atk_1..7, pos_gold) same_spec=True vs Solution.lean (swebench_unified.markers.same_spec, lean backend). Only impl region edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>):
- atk_1 (prepatch bug: always (take len-1).drop 1) rc=1 (does NOT close; residual goal remains).
- atk_2 (swapped openLower/openUpper roles) rc=1.
- atk_3 (boundary: closed-upper trims 2 via len-2 not len-1) rc=1.
- atk_4 (control-flow-effect: dropped the !drawEdges empty-return branch) rc=1.
- atk_5 (ungrounded-oracle: return whole segs, ignore all gating) rc=1.
- atk_6 (partial-domain: ignores openLower, start always 0) rc=1.
- atk_7 (echo of spec RHS, behaviorally identical to gold) rc=0 CLOSES.
- pos_gold (gold impl) rc=0 CLOSES (positive control passes).

### AXIOMS (#print axioms correct_colorbarEdgeSegments appended, re-verified rc=0):
- atk_7: 'does not depend on any axioms' (clean, no sorryAx).
- pos_gold: 'does not depend on any axioms' (clean).

PREPATCH: Solution_prepatch.lean verified rc=1 (does NOT close) => spec genuinely discriminates the bug fix. prepatch_reproduced=true.

MANDATORY RESOLVE ON CLOSING NON-GOLD IMPL: atk_7 is the only closing impl that is not literally pos_gold. It returns the spec RHS verbatim, hence extensionally identical to gold on every input; its faithful refined patch is therefore the gold patch (supplied in patches). Ran it through the official harness: run_resolve('matplotlib__matplotlib-22865', gold_patch, run_id='sbu-audit-atk7-echo', timeout=1800) => RESOLVED: True, note='resolved'. A resolving same-spec echo is NOT a spec weakness under the fixed G-EQ/panel_1 policy. No closing clean-axiom impl has a non-resolving faithful patch => no verify-not-correct witness found.

A-LEG / CORRESPONDENCE AUDIT (refinement.md + mapping.md): refinement.md legs 1-4 tagged I/R/R/R only; declares NO A-consumed and NO A-reference legs, no kind-3 (inexpressible) leg. _extend_lower()/_extend_upper() are UNCHANGED callees whose boolean RESULTS enter the model as free inputs openLower/openUpper (not invoked as opaque ops inside the model); np.dstack([X,Y]) enters as identity List a carrier (element values never inspected by the axis-0 slice). Because the spec forall-quantifies over all 3 bool combos and over generic element type alpha, faithfulness cannot depend on callee internals or axis-inversion caveats — there is no axiom to exploit and no ungrounded oracle. axiom_check.py is a justified G-AX skip stub (no opaque decl, no axiom <callee>_prop in Solution.lean). Solution.lean confirmed: axioms-start/end region contains only comments; no opaque/axiom decls. Correspondence to real callees (colorbar.py:651-660, _extend_lower/_extend_upper at 1352/1357) holds per mapping.md and matches base_commit source cited in verdict.md.

CONCLUSION: >=6 distinct genuinely-wrong same-spec impls attempted (partial-domain, boundary, control-flow-effect, ungrounded-oracle, swapped-roles, prepatch); none closes. The one closing non-gold impl (echo) resolves. Verify => correct holds for this spec. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-faithfulness (drift/too-strong) check for matplotlib__matplotlib-22865 (lean).

Spec region: byte-identical between Solution.lean and Solution_prepatch.lean — swebench_unified.markers.same_spec(post, pre, lean_backend) == True; the only diffs are in the elided impl+proof regions (bug -> fix), spec view unchanged.

Model: problem_spec drops the front separator iff !openLower (start_idx = if openLower then 0 else 1) and takes up to (if openUpper then len else len-1) (end_idx). This maps exactly to the gold patch:
  start_idx = 0 if self._extend_lower() else 1
  end_idx   = len(X) if self._extend_upper() else -1
  set_segments(np.dstack([X,Y])[start_idx:end_idx])   (else [] when !drawedges)
The R legs are: _extend_lower/_extend_upper results lifted to boolean inputs openLower/openUpper (unchanged callees, not axiomatized); np.dstack([X,Y]) modeled as identity carrier List α; Python slice seq[a:b] == (seq.take b).drop a; numpy -1 == len-1 as an absolute upper bound over a finite front-indexed carrier.

Differential testing vs the REAL patched slice with real numpy arrays:
 - conformance_check.py: 100000 fuzzed inputs, 0 disagreements (seed 20220422).
 - Independent exhaustive sweep (all 8 bool combos × n=0..7): 0 divergences. Verified the critical -1 vs len-1 leg and the n=0 empty-array clamp (numpy [1:-1] on empty and Lean take/drop both yield []).

Searched specifically for spec-too-strong drift: the model does NOT constrain result beyond what the patched code produces on any (drawEdges, openLower, openUpper, len) — no input found where the modeled function disagrees with the real callee.

Lean: Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry). #print axioms correct_colorbarEdgeSegments => 'does not depend on any axioms' (no sorryAx; proof is genuine, closed by `cases drawEdges <;> rfl`).

No diverging input exists. Verdict: FAITHFUL — the spec is a sound, non-over-strong model of the real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (problem_spec_colorbarEdgeSegments + its docstring + the /-! header) is fully repo-neutral: it describes selecting which boundary-separator rows of a 1-D color strip are drawn, gated by drawEdges/openLower/openUpper booleans over a generic List α with take/drop. It names NO patched repo symbol (no colorbar/_add_solids/_extend_lower/_extend_upper/np.dstack/set_segments/start_idx/end_idx), no file path (colorbar.py), no diff markers, reproduces no gold-patch line, and carries no narration tokens. The corrected behavior it formalizes — keep terminal separators at an open/extended end, drop them at a closed end — is exactly the publicly-stated 'expected outcome' in the problem_statement ('with drawedges=True and extend=both the black lines at the extremities should show up'). The generalization to independent lower/upper openness is a spec abstraction, not edit-localization; it reveals nothing about the code location or mechanism beyond what the public problem_statement already conveys. Verification: leakage.screen() passes with 0 hard failures; same_spec(Solution, Solution_prepatch) == True (spec region byte-identical); no relaxed_leakage flag / no RELAXED_LEAKAGE.md; recorded G-LEAK status = pass. Judged against problem_statement only, not hints_text (hints_text is empty here anyway).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
