# P2 adversarial audit — matplotlib__matplotlib-24570

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -67,9 +67,9 @@
     let descent := maxList (hdList.map (fun hd => hd.2))
     let h := heightDescent + descent
     return (h, descent, hdList.map (fun _ => (0 : Rat)))
-  else if align == "left" || align == "bottom" then
+  else if align == "left" || align == "top" then
     return (height, 0, hdList.map (fun hd => hd.2))
-  else if align == "right" || align == "top" then
+  else if align == "right" || align == "bottom" then
     return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
   else
     return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
   else if align == "right" || align == "top" then
     return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
   else
-    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
+    return (height, 0, hdList.map (fun hd => hd.2))
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -70,7 +70,7 @@
   else if align == "left" || align == "bottom" then
     return (height, 0, hdList.map (fun hd => hd.2))
   else if align == "right" || align == "top" then
-    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
+    return (height, 0, hdList.map (fun hd => height - hd.1 - hd.2))
   else
     return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
 -- impl-end
```

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -67,10 +67,10 @@
     let descent := maxList (hdList.map (fun hd => hd.2))
     let h := heightDescent + descent
     return (h, descent, hdList.map (fun _ => (0 : Rat)))
+  else if align == "right" || align == "top" then
+    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
   else if align == "left" || align == "bottom" then
     return (height, 0, hdList.map (fun hd => hd.2))
-  else if align == "right" || align == "top" then
-    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
   else
     return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
     let heightDescent := maxList (hdList.map (fun hd => hd.1 - hd.2))
     let descent := maxList (hdList.map (fun hd => hd.2))
     let h := heightDescent + descent
-    return (h, descent, hdList.map (fun _ => (0 : Rat)))
+    return (h, 0, hdList.map (fun _ => (0 : Rat)))
   else if align == "left" || align == "bottom" then
     return (height, 0, hdList.map (fun hd => hd.2))
   else if align == "right" || align == "top" then
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -68,7 +68,7 @@
     let h := heightDescent + descent
     return (h, descent, hdList.map (fun _ => (0 : Rat)))
   else if align == "left" || align == "bottom" then
-    return (height, 0, hdList.map (fun hd => hd.2))
+    return (height, 0, hdList.map (fun hd => hd.1))
   else if align == "right" || align == "top" then
     return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
   else
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
     let heightDescent := maxList (hdList.map (fun hd => hd.1 - hd.2))
     let descent := maxList (hdList.map (fun hd => hd.2))
     let h := heightDescent + descent
-    return (h, descent, hdList.map (fun _ => (0 : Rat)))
+    return (h, descent, hdList.map (fun hd => hd.2))
   else if align == "left" || align == "bottom" then
     return (height, 0, hdList.map (fun hd => hd.2))
   else if align == "right" || align == "top" then
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only outside helper
-- the modeled branch uses is a maximum over a non-empty list of rationals, which
-- is reproduced concretely below (`maxList`); the anchor-membership validation is
-- carried as a binder precondition (`validAlign`). The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Maximum of a list of rationals (the empty list yields `0`; callers always
pass a non-empty list). Reproduces the `max(… for … in …)` reduction used to
resolve the packing extent. -/
def maxList : List Rat → Rat
  | []      => 0
  | x :: xs => xs.foldl max x

/-- The set of anchor keywords accepted by the alignment helper. Used as the
binder precondition (the real code validates the keyword and rejects others). -/
def validAlign (align : String) : Prop :=
  align = "baseline" ∨ align = "left" ∨ align = "top" ∨
  align = "right" ∨ align = "bottom" ∨ align = "center"
-- pure-end

-- post-conditions-start
/-- Aligns boxes given by their `(height, descent)` pairs within an intended total
`height`, returning `(resolvedHeight, descent, offsets)` along the alignment axis.
Each anchor selects one offset rule and is pinned completely:

* `baseline` — the total is recomputed from the per-box extents, the descent is
  the maximal box descent, and every offset is zero;
* `left`/`bottom` — descent zero, each offset is that box's own descent;
* `right`/`top` — descent zero, each offset places the box flush against the far
  edge (`height - boxHeight + descent`);
* `center` — descent zero, each offset centers the box (`(height - boxHeight)/2 +
  descent`).

The resolved height equals the input `height` for every anchor except `baseline`;
the offsets list has the same length and order as the input. -/
def problem_spec_alignedOffsets
    (hdList : List (Rat × Rat)) (height : Rat) (align : String)
    (result : Rat × Rat × List Rat) : Prop :=
  (align = "baseline" →
      result.1 = maxList (hdList.map (fun hd => hd.1 - hd.2))
                   + maxList (hdList.map (fun hd => hd.2))
    ∧ result.2.1 = maxList (hdList.map (fun hd => hd.2))
    ∧ result.2.2 = hdList.map (fun _ => (0 : Rat)))
  ∧ (align = "left" ∨ align = "bottom" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => hd.2))
  ∧ (align = "right" ∨ align = "top" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => height - hd.1 + hd.2))
  ∧ (align = "center" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
-- post-conditions-end

-- impl-start
def implementation_alignedOffsets
    (hdList : List (Rat × Rat)) (height : Rat) (align : String) :
    Rat × Rat × List Rat := Id.run do
  if align == "baseline" then
    let heightDescent := maxList (hdList.map (fun hd => hd.1 - hd.2))
    let descent := maxList (hdList.map (fun hd => hd.2))
    let h := heightDescent + descent
    return (h, descent, hdList.map (fun _ => (0 : Rat)))
  else if align == "left" || align == "bottom" then
    return (height, 0, hdList.map (fun hd => hd.2))
  else if align == "right" || align == "top" then
    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
  else
    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
-- impl-end

-- proof-start
theorem correct_alignedOffsets :
    ∀ (hdList : List (Rat × Rat)) (height : Rat) (align : String),
    validAlign align →
    problem_spec_alignedOffsets hdList height align
      (implementation_alignedOffsets hdList height align) := by
  intro hdList height align _hv
  refine ⟨fun hc => ?_, fun hc => ?_, fun hc => ?_, fun hc => ?_⟩
  · subst hc; exact ⟨rfl, rfl, rfl⟩
  · rcases hc with hc | hc <;> subst hc <;> exact ⟨rfl, rfl, rfl⟩
  · rcases hc with hc | hc <;> subst hc <;> exact ⟨rfl, rfl, rfl⟩
  · subst hc; exact ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_alignedOffsets pins ALL THREE output components (resolved height, descent, offsets list) EXACTLY for every one of the six valid anchors under the validAlign binder precondition => it is a tight, total specification on the modeled domain; any verifying impl must be extensionally equal to gold on that domain.

same_spec check: all 7 attacks + positive control returned True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited).

Lean verify command (each): `bash scripts/lean_verify.sh <file>` run concurrently in batches <=4.
Results:
- atk_pos (gold impl, positive control): exit 0 (VERIFIES). `#print axioms correct_alignedOffsets` => [propext, Classical.choice, Quot.sound] (clean).
- prepatch (top/bottom swap, Solution_prepatch.lean copy): exit 3 (carries sorry) => prepatch bug reproduced, G-DIFF unclosable confirmed.
- atk_1 (prepatch swap top<->bottom, own closing proof body): exit 1 FAIL — error at align="top" offsets clause.
- atk_2 (center returns own-descent hd.2 instead of centered): exit 1 FAIL — error at align="center" offsets clause.
- atk_3 (right/top descent sign flip height - hd.1 - hd.2): exit 1 FAIL — error at align="top" offsets clause.
- atk_5 (baseline descent = 0 instead of maxList descent): exit 1 FAIL — error at align="baseline" descent clause.
- atk_6 (left/bottom offsets use hd.1 height instead of hd.2 descent): exit 1 FAIL — error at align="bottom" offsets clause.
- atk_7 (baseline offsets = map hd.2 instead of zeros): exit 1 FAIL — error at align="baseline" offsets clause.
Each failure is a genuine spec-mismatch type error at exactly the mutated branch (not a syntax/proof-tactic artifact), so none of the 6 genuinely-wrong impls closes.

Only verifying non-positive impl = atk_4 (ungrounded-oracle / echo attack): branches REORDERED (right/top block before left/bottom) but anchor->formula assignment IDENTICAL to gold; verifies exit 0 with clean axioms [propext, Classical.choice, Quot.sound]. Per protocol its faithful refined patch was materialized (patch_atk4.diff, reorders the two elif blocks preserving gold's correct membership; git apply --check OK worktree) and RUN through the official harness:
  run_resolve("matplotlib__matplotlib-24570", patch_atk4) => RESOLVED: True COMPLETED: True NOTE: resolved (timeout=1800, retries=1; run_id sbu-resolve-...-24570-5ac998cdec).
An echo whose patch RESOLVES does NOT break the spec (verified => resolved holds). No verify∧¬resolved witness found.

refinement.md audit: 7 legs, all tagged R (type refinement, R rows 1-2) or I (identical op, rows 3-7). No A-consumed, no A-reference, no kind-3 (changed-inexpressible) legs. axioms region is EMPTY and G-AX is a legitimate skip stub: the only outside callee in the modeled branch, max(... for ...), is reproduced concretely as the maxList fold (an I op, NOT abstracted behind an opaque axiom), and _api.check_in_list membership validation is faithfully carried as the validAlign binder precondition. mapping.md callee-provenance and type-bijection match the real _get_aligned_offsets at lib/matplotlib/offsetbox.py:158-178 @ base_commit. Correspondence holds; no ungrounded axiom to exploit.

Conclusion: >=5 distinct wrong impls attempted (6 wrong + 1 echo + positive control + prepatch); every genuinely-wrong impl FAILS Lean verification, and the sole verifying alternative (echo) has a materialized faithful patch that RESOLVES. Spec is a faithful, tight refinement — verify => correct holds. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_4.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The only outside helper
-- the modeled branch uses is a maximum over a non-empty list of rationals, which
-- is reproduced concretely below (`maxList`); the anchor-membership validation is
-- carried as a binder precondition (`validAlign`). The proof agent may add `_prop`
-- axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- Maximum of a list of rationals (the empty list yields `0`; callers always
pass a non-empty list). Reproduces the `max(… for … in …)` reduction used to
resolve the packing extent. -/
def maxList : List Rat → Rat
  | []      => 0
  | x :: xs => xs.foldl max x

/-- The set of anchor keywords accepted by the alignment helper. Used as the
binder precondition (the real code validates the keyword and rejects others). -/
def validAlign (align : String) : Prop :=
  align = "baseline" ∨ align = "left" ∨ align = "top" ∨
  align = "right" ∨ align = "bottom" ∨ align = "center"
-- pure-end

-- post-conditions-start
/-- Aligns boxes given by their `(height, descent)` pairs within an intended total
`height`, returning `(resolvedHeight, descent, offsets)` along the alignment axis.
Each anchor selects one offset rule and is pinned completely:

* `baseline` — the total is recomputed from the per-box extents, the descent is
  the maximal box descent, and every offset is zero;
* `left`/`bottom` — descent zero, each offset is that box's own descent;
* `right`/`top` — descent zero, each offset places the box flush against the far
  edge (`height - boxHeight + descent`);
* `center` — descent zero, each offset centers the box (`(height - boxHeight)/2 +
  descent`).

The resolved height equals the input `height` for every anchor except `baseline`;
the offsets list has the same length and order as the input. -/
def problem_spec_alignedOffsets
    (hdList : List (Rat × Rat)) (height : Rat) (align : String)
    (result : Rat × Rat × List Rat) : Prop :=
  (align = "baseline" →
      result.1 = maxList (hdList.map (fun hd => hd.1 - hd.2))
                   + maxList (hdList.map (fun hd => hd.2))
    ∧ result.2.1 = maxList (hdList.map (fun hd => hd.2))
    ∧ result.2.2 = hdList.map (fun _ => (0 : Rat)))
  ∧ (align = "left" ∨ align = "bottom" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => hd.2))
  ∧ (align = "right" ∨ align = "top" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => height - hd.1 + hd.2))
  ∧ (align = "center" →
      result.1 = height ∧ result.2.1 = 0
    ∧ result.2.2 = hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
-- post-conditions-end

-- impl-start
def implementation_alignedOffsets
    (hdList : List (Rat × Rat)) (height : Rat) (align : String) :
    Rat × Rat × List Rat := Id.run do
  if align == "baseline" then
    let heightDescent := maxList (hdList.map (fun hd => hd.1 - hd.2))
    let descent := maxList (hdList.map (fun hd => hd.2))
    let h := heightDescent + descent
    return (h, descent, hdList.map (fun _ => (0 : Rat)))
  else if align == "left" || align == "bottom" then
    return (height, 0, hdList.map (fun hd => hd.2))
  else if align == "right" || align == "top" then
    return (height, 0, hdList.map (fun hd => height - hd.1 + hd.2))
  else
    return (height, 0, hdList.map (fun hd => (height - hd.1) / 2 + hd.2))
-- impl-end

-- proof-start
theorem correct_alignedOffsets :
    ∀ (hdList : List (Rat × Rat)) (height : Rat) (align : String),
    validAlign align →
    problem_spec_alignedOffsets hdList height align
      (implementation_alignedOffsets hdList height align) := by
  intro hdList height align _hv
  refine ⟨fun hc => ?_, fun hc => ?_, fun hc => ?_, fun hc => ?_⟩
  · subst hc; exact ⟨rfl, rfl, rfl⟩
  · rcases hc with hc | hc <;> subst hc <;> exact ⟨rfl, rfl, rfl⟩
  · rcases hc with hc | hc <;> subst hc <;> exact ⟨rfl, rfl, rfl⟩
  · subst hc; exact ⟨rfl, rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec problem_spec_alignedOffsets pins ALL THREE output components (resolved height, descent, offsets list) EXACTLY for every one of the six valid anchors under the validAlign binder precondition => it is a tight, total specification on the modeled domain; any verifying impl must be extensionally equal to gold on that domain.

same_spec check: all 7 attacks + positive control returned True vs Solution.lean (axioms/pure/pre/post byte-identical; only impl region edited).

Lean verify command (each): `bash scripts/lean_verify.sh <file>` run concurrently in batches <=4.
Results:
- atk_pos (gold impl, positive control): exit 0 (VERIFIES). `#print axioms correct_alignedOffsets` => [propext, Classical.choice, Quot.sound] (clean).
- prepatch (top/bottom swap, Solution_prepatch.lean copy): exit 3 (carries sorry) => prepatch bug reproduced, G-DIFF unclosable confirmed.
- atk_1 (prepatch swap top<->bottom, own closing proof body): exit 1 FAIL — error at align="top" offsets clause.
- atk_2 (center returns own-descent hd.2 instead of centered): exit 1 FAIL — error at align="center" offsets clause.
- atk_3 (right/top descent sign flip height - hd.1 - hd.2): exit 1 FAIL — error at align="top" offsets clause.
- atk_5 (baseline descent = 0 instead of maxList descent): exit 1 FAIL — error at align="baseline" descent clause.
- atk_6 (left/bottom offsets use hd.1 height instead of hd.2 descent): exit 1 FAIL — error at align="bottom" offsets clause.
- atk_7 (baseline offsets = map hd.2 instead of zeros): exit 1 FAIL — error at align="baseline" offsets clause.
Each failure is a genuine spec-mismatch type error at exactly the mutated branch (not a syntax/proof-tactic artifact), so none of the 6 genuinely-wrong impls closes.

Only verifying non-positive impl = atk_4 (ungrounded-oracle / echo attack): branches REORDERED (right/top block before left/bottom) but anchor->formula assignment IDENTICAL to gold; verifies exit 0 with clean axioms [propext, Classical.choice, Quot.sound]. Per protocol its faithful refined patch was materialized (patch_atk4.diff, reorders the two elif blocks preserving gold's correct membership; git apply --check OK worktree) and RUN through the official harness:
  run_resolve("matplotlib__matplotlib-24570", patch_atk4) => RESOLVED: True COMPLETED: True NOTE: resolved (timeout=1800, retries=1; run_id sbu-resolve-...-24570-5ac998cdec).
An echo whose patch RESOLVES does NOT break the spec (verified => resolved holds). No verify∧¬resolved witness found.

refinement.md audit: 7 legs, all tagged R (type refinement, R rows 1-2) or I (identical op, rows 3-7). No A-consumed, no A-reference, no kind-3 (changed-inexpressible) legs. axioms region is EMPTY and G-AX is a legitimate skip stub: the only outside callee in the modeled branch, max(... for ...), is reproduced concretely as the maxList fold (an I op, NOT abstracted behind an opaque axiom), and _api.check_in_list membership validation is faithfully carried as the validAlign binder precondition. mapping.md callee-provenance and type-bijection match the real _get_aligned_offsets at lib/matplotlib/offsetbox.py:158-178 @ base_commit. Correspondence holds; no ungrounded axiom to exploit.

Conclusion: >=5 distinct wrong impls attempted (6 wrong + 1 echo + positive control + prepatch); every genuinely-wrong impl FAILS Lean verification, and the sole verifying alternative (echo) has a materialized faithful patch that RESOLVES. Spec is a faithful, tight refinement — verify => correct holds. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Rigorous audit performed. (1) Lean: scripts/lean_verify.sh Solution.lean exits 0 (no sorry). (2) #print axioms correct_alignedOffsets => [propext, Classical.choice, Quot.sound]; no sorryAx, proof genuine. (3) same_spec(Solution, Solution_prepatch, lean-backend) = True; spec-view confirmed byte-identical (only impl/proof/comment differ). (4) Prepatch fails as expected (retains sorry). Verified spec matches the REAL post-patch code at offsetbox.py op-for-op across all six anchors, including the fix swap left/top<->left/bottom and right/bottom<->right/top: baseline (max(h-d)+max(d), max(d), [0]); left|bottom (height,0,[d]); right|top (height,0,[height-h+d]); center (height,0,[(height-h)/2+d]). Float->Rat is exact (subtraction + halving; IEEE *0.5 == /2). check_in_list carried as validAlign binder; non-empty carried as documented precondition. The four postcondition clauses are guarded implications keyed exactly on the anchor keyword, so the spec is not over-constrained: every valid input is pinned to precisely the real value, and no valid input is left contradicting the real callee. Spec is FAITHFUL: not too strong, no in-scope drift.

Counterexample / evidence:

```
n/a — no valid (validAlign ∧ non-empty) input where the modeled function disagrees with the real post-patch callee. Conformance: 120008 inputs, 0 disagreements (seed 24570).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical leak.screen PASSES (no diff markers, no offsetbox.py path/module, no gold changed-line reproduced, patched symbol 'get_aligned_offsets' not embedded in any spec-view identifier or comment, no L3 narration). Spec region is frozen: same_spec(Solution.lean, Solution_prepatch.lean)=True, so the consumer spec view is identical pre/post patch and cannot encode the diff. Semantically the spec (problem_spec_alignedOffsets) merely pins the correct intended behavior of all six anchors (left/bottom->own-descent, right/top->far-edge, baseline, center) — the legitimate function of a formal spec, stated abstractly. The only edit-specific fact (top/bottom are reversed and must be swapped) is ALREADY fully public in the problem_statement ('[Bug]: align in HPacker is reversed'; 'the options top and bottom seems reversed'; reproduction with align=bottom). Thus the spec view reveals nothing about the gold edit beyond the public problem_statement. Note: hints_text does contain the literal gold diff, but per policy leakage is judged against problem_statement only. meta records G-LEAK pass and G-PANEL-3 pass; relaxed_leakage=None (not a relaxed bundle, so no RELAXED_LEAKAGE deferral needed).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
