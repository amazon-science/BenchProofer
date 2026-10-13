# P2 adversarial audit — matplotlib__matplotlib-23412

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,7 @@
     Option (Int × Option (List Int)) := Id.run do
   if !visible then
     return none
-  -- The stroke style applied while rendering carries the full configured
-  -- offset together with the on/off sequence (the offset is honored, not zeroed).
-  let used : Int × Option (List Int) := (offset, dashes)
+  let used : Int × Option (List Int) := (0, dashes)
   return some used
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,10 +45,6 @@
 -- impl-start
 def implementation_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int)) :
     Option (Int × Option (List Int)) := Id.run do
-  if !visible then
-    return none
-  -- The stroke style applied while rendering carries the full configured
-  -- offset together with the on/off sequence (the offset is honored, not zeroed).
   let used : Int × Option (List Int) := (offset, dashes)
   return some used
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,7 @@
     Option (Int × Option (List Int)) := Id.run do
   if !visible then
     return none
-  -- The stroke style applied while rendering carries the full configured
-  -- offset together with the on/off sequence (the offset is honored, not zeroed).
-  let used : Int × Option (List Int) := (offset, dashes)
+  let used : Int × Option (List Int) := (-offset, dashes)
   return some used
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,10 +45,8 @@
 -- impl-start
 def implementation_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int)) :
     Option (Int × Option (List Int)) := Id.run do
-  if !visible then
+  if visible then
     return none
-  -- The stroke style applied while rendering carries the full configured
-  -- offset together with the on/off sequence (the offset is honored, not zeroed).
   let used : Int × Option (List Int) := (offset, dashes)
   return some used
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,12 +45,7 @@
 -- impl-start
 def implementation_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int)) :
     Option (Int × Option (List Int)) := Id.run do
-  if !visible then
-    return none
-  -- The stroke style applied while rendering carries the full configured
-  -- offset together with the on/off sequence (the offset is honored, not zeroed).
-  let used : Int × Option (List Int) := (offset, dashes)
-  return some used
+  return none
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,7 @@
     Option (Int × Option (List Int)) := Id.run do
   if !visible then
     return none
-  -- The stroke style applied while rendering carries the full configured
-  -- offset together with the on/off sequence (the offset is honored, not zeroed).
-  let used : Int × Option (List Int) := (offset, dashes)
+  let used : Int × Option (List Int) := (offset, none)
   return some used
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,9 +47,7 @@
     Option (Int × Option (List Int)) := Id.run do
   if !visible then
     return none
-  -- The stroke style applied while rendering carries the full configured
-  -- offset together with the on/off sequence (the offset is honored, not zeroed).
-  let used : Int × Option (List Int) := (offset, dashes)
+  let used : Int × Option (List Int) := (offset + 1, dashes)
   return some used
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering the outline of a filled shape with a dashed stroke style.

A dashed stroke style is described by two pieces of data carried together: a
non-negative *offset* (how far into the dash cycle the very first segment
begins) and an *on/off sequence* (the alternating lengths of drawn and blank
ink). When the shape is actually rendered, the stroke style that is handed to
the renderer must reproduce BOTH pieces of data exactly as they were configured
on the shape: the offset and the on/off sequence applied at render time are the
ones the user supplied.

There is one short-circuit: if the shape is not visible, nothing is rendered at
all and no stroke style is produced.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a logical contract: the rendered
-- stroke style is the configured offset/on-off data carried through verbatim,
-- spelled out concretely below. The visibility short-circuit is a plain guard.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The stroke style produced when rendering:

* if the shape is not visible, nothing is produced (`none`);
* if it is visible, the produced style carries BOTH the configured `offset` and
  the configured on/off sequence `dashes`, unchanged — i.e. exactly
  `some (offset, dashes)`. In particular the offset is preserved, not discarded. -/
def problem_spec_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int))
    (result : Option (Int × Option (List Int))) : Prop :=
  (visible = false → result = none) ∧
  (visible = true → result = some (offset, dashes))
-- post-conditions-end

-- impl-start
def implementation_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int)) :
    Option (Int × Option (List Int)) := Id.run do
  if !visible then
    return none
  -- The stroke style applied while rendering carries the full configured
  -- offset together with the on/off sequence (the offset is honored, not zeroed).
  let used : Int × Option (List Int) := (offset, dashes)
  return some used
-- impl-end

-- proof-start
theorem correct_dashRender :
    ∀ (visible : Bool) (offset : Int) (dashes : Option (List Int)),
      problem_spec_dashRender visible offset dashes
        (implementation_dashRender visible offset dashes) := by
  intro visible offset dashes
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    subst h <;>
    simp [implementation_dashRender, Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_dashRender is total and fully DETERMINISTIC: for every input it pins result to exactly `none` (visible=false) or `some (offset, dashes)` (visible=true), an exact equation. The axioms region is empty commentary (no declared/consumed axioms), so there is zero axiomatic slack for a divergent impl to exploit. By Lean soundness no wrong impl can close the carried gold proof; verified mechanically.

SAME-SPEC: all 7 attacks + positive control return same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec with get_backend('lean').

### VERIFY (scripts/lean_verify.sh, cap 300, run concurrently in two batches of 4):
- pos.lean (gold copy): exit 0 (verifies). #print axioms correct_dashRender => depends on axioms: [propext] (CLEAN — no sorryAx, no custom axioms).
- atk_1 prepatch bug (offset zeroed: (0,dashes)): exit 1, error at 58:61 'unsolved goals' — prepatch REPRODUCED (buggy impl yields some(0,dashes) != some(offset,dashes) when offset!=0).
- atk_2 partial-domain (visibility guard removed, returns some when invisible): exit 1.
- atk_3 boundary (negated offset (-offset,dashes)): exit 1.
- atk_4 control-flow-effect (inverted guard: `if visible then return none`): exit 1.
- atk_5 ungrounded-oracle echo (always `return none`): exit 1.
- atk_6 dropped-dashes ((offset, none)): exit 1.
- atk_7 off-by-one ((offset+1, dashes)): exit 1.

Exact commands: `bash scripts/lean_verify.sh <file>` for each. All 7 wrong impls fail to close (exit 1, unsolved goals). No wrong impl closes with clean axioms, therefore NO patch needed materialization/resolve — spec is not falsifiable via verify⇏correct. patches={} accordingly (no verifying attack).

REFINEMENT.md AUDIT: 4 legs — (1) visibility guard `if !visible then return none` <-> `if not self.get_visible(): return` = I (identical); (2) `(offset,dashes)` carry-through <-> `cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern))` = A-reference (deep model, validated == real in-draw self._dash_pattern by G-CONF); (3) tuple type <-> scaled (offset,onoffseq) = R; (4) produced style <-> pattern consumed via gc.set_dashes = R. NO kind-3 leg (no ungrounded A-consumed callee contract; axioms region empty). A-reference correspondence is FAITHFUL: post-patch installs self._dash_pattern=(offset,dashes) verbatim, exactly the model's identity carry-through; pre-patch installed (0, dashes[1]) which the deterministic spec correctly rejects. Correspondence holds.

CONCLUSION: >=5 distinct attacks run (7 total, incl. prepatch), positive control verifies with clean axioms, none breaks the spec. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering the outline of a filled shape with a dashed stroke style.

A dashed stroke style is described by two pieces of data carried together: a
non-negative *offset* (how far into the dash cycle the very first segment
begins) and an *on/off sequence* (the alternating lengths of drawn and blank
ink). When the shape is actually rendered, the stroke style that is handed to
the renderer must reproduce BOTH pieces of data exactly as they were configured
on the shape: the offset and the on/off sequence applied at render time are the
ones the user supplied.

There is one short-circuit: if the shape is not visible, nothing is rendered at
all and no stroke style is produced.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a logical contract: the rendered
-- stroke style is the configured offset/on-off data carried through verbatim,
-- spelled out concretely below. The visibility short-circuit is a plain guard.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The stroke style produced when rendering:

* if the shape is not visible, nothing is produced (`none`);
* if it is visible, the produced style carries BOTH the configured `offset` and
  the configured on/off sequence `dashes`, unchanged — i.e. exactly
  `some (offset, dashes)`. In particular the offset is preserved, not discarded. -/
def problem_spec_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int))
    (result : Option (Int × Option (List Int))) : Prop :=
  (visible = false → result = none) ∧
  (visible = true → result = some (offset, dashes))
-- post-conditions-end

-- impl-start
def implementation_dashRender (visible : Bool) (offset : Int) (dashes : Option (List Int)) :
    Option (Int × Option (List Int)) := Id.run do
  if !visible then
    return none
  -- The stroke style applied while rendering carries the full configured
  -- offset together with the on/off sequence (the offset is honored, not zeroed).
  let used : Int × Option (List Int) := (offset, dashes)
  return some used
-- impl-end

-- proof-start
theorem correct_dashRender :
    ∀ (visible : Bool) (offset : Int) (dashes : Option (List Int)),
      problem_spec_dashRender visible offset dashes
        (implementation_dashRender visible offset dashes) := by
  intro visible offset dashes
  refine ⟨fun h => ?_, fun h => ?_⟩ <;>
    subst h <;>
    simp [implementation_dashRender, Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_dashRender is total and fully DETERMINISTIC: for every input it pins result to exactly `none` (visible=false) or `some (offset, dashes)` (visible=true), an exact equation. The axioms region is empty commentary (no declared/consumed axioms), so there is zero axiomatic slack for a divergent impl to exploit. By Lean soundness no wrong impl can close the carried gold proof; verified mechanically.

SAME-SPEC: all 7 attacks + positive control return same_spec=True (impl region edited only; axioms/pure/pre/post byte-identical). Verified via swebench_unified.markers.same_spec with get_backend('lean').

### VERIFY (scripts/lean_verify.sh, cap 300, run concurrently in two batches of 4):
- pos.lean (gold copy): exit 0 (verifies). #print axioms correct_dashRender => depends on axioms: [propext] (CLEAN — no sorryAx, no custom axioms).
- atk_1 prepatch bug (offset zeroed: (0,dashes)): exit 1, error at 58:61 'unsolved goals' — prepatch REPRODUCED (buggy impl yields some(0,dashes) != some(offset,dashes) when offset!=0).
- atk_2 partial-domain (visibility guard removed, returns some when invisible): exit 1.
- atk_3 boundary (negated offset (-offset,dashes)): exit 1.
- atk_4 control-flow-effect (inverted guard: `if visible then return none`): exit 1.
- atk_5 ungrounded-oracle echo (always `return none`): exit 1.
- atk_6 dropped-dashes ((offset, none)): exit 1.
- atk_7 off-by-one ((offset+1, dashes)): exit 1.

Exact commands: `bash scripts/lean_verify.sh <file>` for each. All 7 wrong impls fail to close (exit 1, unsolved goals). No wrong impl closes with clean axioms, therefore NO patch needed materialization/resolve — spec is not falsifiable via verify⇏correct. patches={} accordingly (no verifying attack).

REFINEMENT.md AUDIT: 4 legs — (1) visibility guard `if !visible then return none` <-> `if not self.get_visible(): return` = I (identical); (2) `(offset,dashes)` carry-through <-> `cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern))` = A-reference (deep model, validated == real in-draw self._dash_pattern by G-CONF); (3) tuple type <-> scaled (offset,onoffseq) = R; (4) produced style <-> pattern consumed via gc.set_dashes = R. NO kind-3 leg (no ungrounded A-consumed callee contract; axioms region empty). A-reference correspondence is FAITHFUL: post-patch installs self._dash_pattern=(offset,dashes) verbatim, exactly the model's identity carry-through; pre-patch installed (0, dashes[1]) which the deterministic spec correctly rejects. Correspondence holds.

CONCLUSION: >=5 distinct attacks run (7 total, incl. prepatch), positive control verifies with clean axioms, none breaks the spec. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on matplotlib__matplotlib-23412 lean bundle. No divergence found; spec is a faithful model of the post-patch callee.

### Verification performed
1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) == True. The post-condition problem_spec_dashRender is unchanged between patched/pre-patch bundles.
2. Solution.lean compiles under scripts/lean_verify.sh (exit 0, no sorry).
3. #print axioms correct_dashRender => [propext] only — no sorryAx, proof is genuine (not fake).

### Faithfulness analysis
Modeled function = Patch.draw (lib/matplotlib/patches.py). Spec: visible=false -> result=none; visible=true -> result = some (offset, dashes) — a pure identity carry-through of the configured (offset, dashes) pair.

Real post-patch callee (verified in patches.py): `if not self.get_visible(): return` then `with cbook._setattr_cm(self, _dash_pattern=(self._dash_pattern)), ...`. The stored scaled _dash_pattern is installed VERBATIM (no transformation) for the draw and consumed by gc.set_dashes(*self._dash_pattern). This is exactly the identity map the spec states. The invisible short-circuit returns before the with-block => none case matches.

Bridge soundness: _get_dash_pattern/_scale_dashes only COMPUTE self._dash_pattern; conformance_check.py feeds the Lean model that exact scaled value (via mlines._get_dash_pattern + _scale_dashes) and observes the real in-draw self._dash_pattern by overriding get_path on a ProbeRect subclass — capturing the value at the exact moment inside the with-block the patch edits. Integer offset/linewidth fuzzing makes float->Int rounding exact, so the Int/Option(List Int) abstraction loses nothing. Since post-patch applies no transformation, model output == real callee output on every input in the >=1e5-case + discrete-catalogue conformance suite.

The spec is neither too strong nor drifted: it asserts precisely the identity behavior the post-patch code exhibits, no more. Searched specifically for an input where the spec guarantees something the real callee does not (e.g. offset dropped, dashes reordered, scaling applied twice) — none exists; the real callee is a straight pass-through. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures). Semantic review of the spec_view (imports + docstring + post-conditions region only; impl/proof elided) confirms no leakage of the gold edit beyond the public problem_statement.

Gold edit: in lib/matplotlib/patches.py Patch.draw, change `_dash_pattern=(0, self._dash_pattern[1])` -> `_dash_pattern=(self._dash_pattern)`, i.e. stop forcing the dash offset to 0 so the configured offset is honored at render.

Problem_statement (public) already discloses the DESIRED behavior fully: title 'offset dash linestyle has no effect in patch objects'; 'the offset has no effect'; expected outcome = offset honored like Line2D. So a spec stating that the render must honor the configured offset restates public knowledge, not the gold patch.

Spec view contains NONE of the edit mechanism/localization: no `_dash_pattern`, no `cbook`/`_setattr_cm`, no `patches.py` path, no `(0, ...)` tuple, no diff markers, no `draw` repo symbol (abstracted to `dashRender`). Changed symbol set is {'draw'} and it does not appear as a spec identifier; changed gold lines are not reproduced (verified via leakage._patch_changed_lines vs view_norm). The 'offset is preserved, not discarded' docstring phrasing = the publicly-known expected behavior, stated abstractly as an input->output relation.

Integrity checks: same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical across the differential pair). No hints_text terms echoed. No gold-reconstruction possible from the spec view beyond the problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
