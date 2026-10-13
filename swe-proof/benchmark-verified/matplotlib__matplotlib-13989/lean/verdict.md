# P2 adversarial audit — matplotlib__matplotlib-13989

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec pins BOTH output fields as total functions of the four inputs (result.range = if setRange then some binRange else none; result.density = if densityFlag && !stacked then some densityFlag else none), leaving no underspecified/ungrounded component for a wrong impl to exploit. Every same-spec wrong impl either fails to verify or is extensionally identical to the gold and resolves.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
   if setRange then
     hk := { hk with range := some binRange }
   if densityFlag && !stacked then
-    hk := { hk with density := some densityFlag }
+    hk := { range := none, density := some densityFlag }
   return hk
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   let mut hk : HistKeywordArgs := { range := none, density := none }
   if setRange then
     hk := { hk with range := some binRange }
-  if densityFlag && !stacked then
+  if densityFlag || !stacked then
     hk := { hk with density := some densityFlag }
   return hk
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,7 +61,7 @@
     (setRange : Bool) (binRange : Rat × Rat)
     (densityFlag stacked : Bool) : HistKeywordArgs := Id.run do
   let mut hk : HistKeywordArgs := { range := none, density := none }
-  if setRange then
+  if setRange && densityFlag then
     hk := { hk with range := some binRange }
   if densityFlag && !stacked then
     hk := { hk with density := some densityFlag }
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -61,10 +61,10 @@
     (setRange : Bool) (binRange : Rat × Rat)
     (densityFlag stacked : Bool) : HistKeywordArgs := Id.run do
   let mut hk : HistKeywordArgs := { range := none, density := none }
-  if setRange then
-    hk := { hk with range := some binRange }
   if densityFlag && !stacked then
     hk := { hk with density := some densityFlag }
+  if setRange then
+    hk := { range := some binRange, density := none }
   return hk
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -59,13 +59,9 @@
 -- impl-start
 def implementation_assembleHistKeywordArgs
     (setRange : Bool) (binRange : Rat × Rat)
-    (densityFlag stacked : Bool) : HistKeywordArgs := Id.run do
-  let mut hk : HistKeywordArgs := { range := none, density := none }
-  if setRange then
-    hk := { hk with range := some binRange }
-  if densityFlag && !stacked then
-    hk := { hk with density := some densityFlag }
-  return hk
+    (densityFlag stacked : Bool) : HistKeywordArgs :=
+  { range := if setRange then some binRange else none,
+    density := if densityFlag && !stacked then some densityFlag else none }
 -- impl-end
 
 -- proof-start
@@ -75,5 +71,5 @@
         (implementation_assembleHistKeywordArgs setRange binRange densityFlag stacked) := by
   intro setRange binRange densityFlag stacked
   unfold problem_spec_assembleHistKeywordArgs implementation_assembleHistKeywordArgs
-  cases setRange <;> cases densityFlag <;> cases stacked <;> exact ⟨rfl, rfl⟩
+  exact ⟨rfl, rfl⟩
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,7 +62,7 @@
     (densityFlag stacked : Bool) : HistKeywordArgs := Id.run do
   let mut hk : HistKeywordArgs := { range := none, density := none }
   if setRange then
-    hk := { hk with range := some binRange }
+    hk := { hk with range := some (binRange.2, binRange.1) }
   if densityFlag && !stacked then
     hk := { hk with density := some densityFlag }
   return hk
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
   if setRange then
     hk := { hk with range := some binRange }
   if densityFlag && !stacked then
-    hk := { hk with density := some densityFlag }
+    hk := { hk with density := some (!densityFlag) }
   return hk
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   let mut hk : HistKeywordArgs := { range := none, density := none }
   if setRange then
     hk := { hk with range := some binRange }
-  if densityFlag && !stacked then
+  if densityFlag then
     hk := { hk with density := some densityFlag }
   return hk
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the keyword-argument mapping handed to the histogram-count routine.

Before the counts are computed, a small keyword mapping is built up from the
plotting call's options. Two entries are relevant here:

* a `range` entry, which sets the lower/upper bounds of the histogram. It is
  added exactly when the call follows the single-or-empty-dataset path (the path
  that does not pre-compute shared bin edges);
* a `density` entry, which requests that the counts be normalised to a
  probability density. It is added exactly when a density result is requested and
  the datasets are not being stacked.

The desired behaviour is that these two entries are assembled independently:
adding the `density` entry must NOT disturb a `range` entry that was already
placed in the mapping. Equivalently, the final mapping carries the `range` entry
whenever the single-or-empty-dataset path requested explicit bounds, regardless of
whether a `density` entry was also added; and it carries the `density` entry
whenever a non-stacked density result was requested, regardless of whether bounds
were also requested.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- behaviour is the pure assembly of a small keyword mapping from already-resolved
-- option values, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The small keyword mapping handed to the histogram-count routine. Each entry
is optional: `none` means the key is absent from the mapping, `some v` means the
key is present with value `v`.

* `range` — optional explicit `(lower, upper)` bounds (exact rationals stand in
  for the float bounds, which are only stored and passed through);
* `density` — optional normalise-to-density request. -/
structure HistKeywordArgs where
  range : Option (Rat × Rat)
  density : Option Bool
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The assembled mapping carries the `range` entry exactly when explicit bounds
were requested (and then equal to those bounds), and the `density` entry exactly
when a non-stacked density result was requested (and then equal to that request).
Both components are pinned to the inputs, so adding one entry can never silently
drop or alter the other. -/
def problem_spec_assembleHistKeywordArgs
    (setRange : Bool) (binRange : Rat × Rat)
    (densityFlag stacked : Bool) (result : HistKeywordArgs) : Prop :=
  result.range = (if setRange then some binRange else none) ∧
  result.density = (if densityFlag && !stacked then some densityFlag else none)
-- post-conditions-end

-- impl-start
def implementation_assembleHistKeywordArgs
    (setRange : Bool) (binRange : Rat × Rat)
    (densityFlag stacked : Bool) : HistKeywordArgs := Id.run do
  let mut hk : HistKeywordArgs := { range := none, density := none }
  if setRange then
    hk := { hk with range := some binRange }
  if densityFlag && !stacked then
    hk := { hk with density := some densityFlag }
  return hk
-- impl-end

-- proof-start
theorem correct_assembleHistKeywordArgs :
    ∀ (setRange : Bool) (binRange : Rat × Rat) (densityFlag stacked : Bool),
      problem_spec_assembleHistKeywordArgs setRange binRange densityFlag stacked
        (implementation_assembleHistKeywordArgs setRange binRange densityFlag stacked) := by
  intro setRange binRange densityFlag stacked
  unfold problem_spec_assembleHistKeywordArgs implementation_assembleHistKeywordArgs
  cases setRange <;> cases densityFlag <;> cases stacked <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec confirmed True (swebench_unified.markers.same_spec) for pos_control + all 8 attacks; axioms/pure/pre/post left byte-identical, only impl (and proof text) edited. All verifications run concurrently in /tmp scratch (<=4 background jobs/batch).

VERIFY COMMANDS: cd && bash scripts/lean_verify.sh <file>

### Results
- pos_control.lean (exact gold impl): EXIT=0 (verifies). #print axioms correct_assembleHistKeywordArgs => [propext] (clean, no sorryAx).
- atk_1.lean PREPATCH BUG (density branch rebinds record: { range := none, density := some densityFlag }, dropping range): EXIT=1 (does NOT close). Impl region byte-identical to bundle's Solution_prepatch.lean (verified via diff). => prepatch reproduced; spec REJECTS the bug.
- atk_2.lean swapped-condition (density set when densityFlag || !stacked): EXIT=1.
- atk_3.lean partial-domain (range set only when setRange && densityFlag): EXIT=1.
- atk_4.lean control-flow-effect (range branch resets record: { range := some binRange, density := none } after density set): EXIT=1.
- atk_5.lean ungrounded-oracle echo (direct extensionally-gold construction { range := if setRange..., density := if densityFlag && !stacked... }): EXIT=0 (verifies). #print axioms => [propext] (clean). MANDATORY RESOLVE RUN: materialized faithful patch atk_5_patch.diff (identical to gold fix hist_kwargs['density']=density) => run_resolve('matplotlib__matplotlib-13989', ..., run_id='sbu-audit-eq-cr35blt-atk5') => RESOLVED=True COMPLETED=True NOTE='resolved'. This is a legitimate gold-echo (per RESOLVED echo-attack policy: same-spec verifying attack fails only if its refined patch does NOT resolve). NOT a weakness.
- atk_6.lean boundary/value (range stores swapped tuple (binRange.2, binRange.1)): EXIT=1.
- atk_7.lean flipped density value (some (!densityFlag)): EXIT=1.
- atk_8.lean ignore-stacked (density set when densityFlag alone): EXIT=1.

AXIOM CHECK COMMAND: appended '#print axioms correct_assembleHistKeywordArgs' to each verifying impl and re-ran lean_verify.sh; both pos_control and atk_5 depend only on [propext] (a standard Mathlib axiom) — no sorryAx, no custom axioms.

REFINEMENT AUDIT (refinement.md): 4 legs. Rows 1-3 tagged R (empty-record init; range-entry set; density-entry set = the fix), row 4 tagged I (return hk = modeled output). No A-consumed / A-reference legs and no kind-3 (inexpressible) leg. Consistent with the model: the assembly is pure Python dict manipulation with NO unchanged repo callee consumed inside the modeled boundary; np.histogram is downstream of the output and correctly not modeled. Confirmed against mapping.md symbol bindings (_axes.py:6654/6685/6689 + gold fix). No A-legs to validate correspondence for. R/I legs mechanically covered by G-CONF (present + faithful op-for-op shadow of the impl).

VERDICT: SOUND. 8 distinct same-spec wrong impls attacked; all 6 with genuine defects (prepatch, swapped-cond, partial-domain, control-flow-effect, boundary-value, flipped-value, ignore-stacked) FAIL to verify; the only verifying attack (atk_5) is extensionally identical to gold and its materialized faithful patch RESOLVES under the official harness. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec pins BOTH output fields as total functions of the four inputs (result.range = if setRange then some binRange else none; result.density = if densityFlag && !stacked then some densityFlag else none), leaving no underspecified/ungrounded component for a wrong impl to exploit. Every same-spec wrong impl either fails to verify or is extensionally identical to the gold and resolves.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Assembling the keyword-argument mapping handed to the histogram-count routine.

Before the counts are computed, a small keyword mapping is built up from the
plotting call's options. Two entries are relevant here:

* a `range` entry, which sets the lower/upper bounds of the histogram. It is
  added exactly when the call follows the single-or-empty-dataset path (the path
  that does not pre-compute shared bin edges);
* a `density` entry, which requests that the counts be normalised to a
  probability density. It is added exactly when a density result is requested and
  the datasets are not being stacked.

The desired behaviour is that these two entries are assembled independently:
adding the `density` entry must NOT disturb a `range` entry that was already
placed in the mapping. Equivalently, the final mapping carries the `range` entry
whenever the single-or-empty-dataset path requested explicit bounds, regardless of
whether a `density` entry was also added; and it carries the `density` entry
whenever a non-stacked density result was requested, regardless of whether bounds
were also requested.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- behaviour is the pure assembly of a small keyword mapping from already-resolved
-- option values, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The small keyword mapping handed to the histogram-count routine. Each entry
is optional: `none` means the key is absent from the mapping, `some v` means the
key is present with value `v`.

* `range` — optional explicit `(lower, upper)` bounds (exact rationals stand in
  for the float bounds, which are only stored and passed through);
* `density` — optional normalise-to-density request. -/
structure HistKeywordArgs where
  range : Option (Rat × Rat)
  density : Option Bool
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The assembled mapping carries the `range` entry exactly when explicit bounds
were requested (and then equal to those bounds), and the `density` entry exactly
when a non-stacked density result was requested (and then equal to that request).
Both components are pinned to the inputs, so adding one entry can never silently
drop or alter the other. -/
def problem_spec_assembleHistKeywordArgs
    (setRange : Bool) (binRange : Rat × Rat)
    (densityFlag stacked : Bool) (result : HistKeywordArgs) : Prop :=
  result.range = (if setRange then some binRange else none) ∧
  result.density = (if densityFlag && !stacked then some densityFlag else none)
-- post-conditions-end

-- impl-start
def implementation_assembleHistKeywordArgs
    (setRange : Bool) (binRange : Rat × Rat)
    (densityFlag stacked : Bool) : HistKeywordArgs := Id.run do
  let mut hk : HistKeywordArgs := { range := none, density := none }
  if setRange then
    hk := { hk with range := some binRange }
  if densityFlag && !stacked then
    hk := { hk with density := some densityFlag }
  return hk
-- impl-end

-- proof-start
theorem correct_assembleHistKeywordArgs :
    ∀ (setRange : Bool) (binRange : Rat × Rat) (densityFlag stacked : Bool),
      problem_spec_assembleHistKeywordArgs setRange binRange densityFlag stacked
        (implementation_assembleHistKeywordArgs setRange binRange densityFlag stacked) := by
  intro setRange binRange densityFlag stacked
  unfold problem_spec_assembleHistKeywordArgs implementation_assembleHistKeywordArgs
  cases setRange <;> cases densityFlag <;> cases stacked <;> exact ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Same-spec confirmed True (swebench_unified.markers.same_spec) for pos_control + all 8 attacks; axioms/pure/pre/post left byte-identical, only impl (and proof text) edited. All verifications run concurrently in /tmp scratch (<=4 background jobs/batch).

VERIFY COMMANDS: cd && bash scripts/lean_verify.sh <file>

### Results
- pos_control.lean (exact gold impl): EXIT=0 (verifies). #print axioms correct_assembleHistKeywordArgs => [propext] (clean, no sorryAx).
- atk_1.lean PREPATCH BUG (density branch rebinds record: { range := none, density := some densityFlag }, dropping range): EXIT=1 (does NOT close). Impl region byte-identical to bundle's Solution_prepatch.lean (verified via diff). => prepatch reproduced; spec REJECTS the bug.
- atk_2.lean swapped-condition (density set when densityFlag || !stacked): EXIT=1.
- atk_3.lean partial-domain (range set only when setRange && densityFlag): EXIT=1.
- atk_4.lean control-flow-effect (range branch resets record: { range := some binRange, density := none } after density set): EXIT=1.
- atk_5.lean ungrounded-oracle echo (direct extensionally-gold construction { range := if setRange..., density := if densityFlag && !stacked... }): EXIT=0 (verifies). #print axioms => [propext] (clean). MANDATORY RESOLVE RUN: materialized faithful patch atk_5_patch.diff (identical to gold fix hist_kwargs['density']=density) => run_resolve('matplotlib__matplotlib-13989', ..., run_id='sbu-audit-eq-cr35blt-atk5') => RESOLVED=True COMPLETED=True NOTE='resolved'. This is a legitimate gold-echo (per RESOLVED echo-attack policy: same-spec verifying attack fails only if its refined patch does NOT resolve). NOT a weakness.
- atk_6.lean boundary/value (range stores swapped tuple (binRange.2, binRange.1)): EXIT=1.
- atk_7.lean flipped density value (some (!densityFlag)): EXIT=1.
- atk_8.lean ignore-stacked (density set when densityFlag alone): EXIT=1.

AXIOM CHECK COMMAND: appended '#print axioms correct_assembleHistKeywordArgs' to each verifying impl and re-ran lean_verify.sh; both pos_control and atk_5 depend only on [propext] (a standard Mathlib axiom) — no sorryAx, no custom axioms.

REFINEMENT AUDIT (refinement.md): 4 legs. Rows 1-3 tagged R (empty-record init; range-entry set; density-entry set = the fix), row 4 tagged I (return hk = modeled output). No A-consumed / A-reference legs and no kind-3 (inexpressible) leg. Consistent with the model: the assembly is pure Python dict manipulation with NO unchanged repo callee consumed inside the modeled boundary; np.histogram is downstream of the output and correctly not modeled. Confirmed against mapping.md symbol bindings (_axes.py:6654/6685/6689 + gold fix). No A-legs to validate correspondence for. R/I legs mechanically covered by G-CONF (present + faithful op-for-op shadow of the impl).

VERDICT: SOUND. 8 distinct same-spec wrong impls attacked; all 6 with genuine defects (prepatch, swapped-cond, partial-domain, control-flow-effect, boundary-value, flipped-value, ignore-stacked) FAIL to verify; the only verifying attack (atk_5) is extensionally identical to gold and its materialized faithful patch RESOLVES under the official harness. No impl with a closing clean-axiom proof has a non-resolving faithful patch. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO diverging input. Spec problem_spec_assembleHistKeywordArgs pins BOTH output fields exactly to the four resolved observables:
  result.range   = if setRange then some binRange else none
  result.density = if densityFlag && !stacked then some densityFlag else none
These match the gold-patched real Axes.hist assembly (lib/matplotlib/axes/_axes.py ~6664-6689): hist_kwargs['range']=bin_range set exactly on the single/empty-dataset else-branch (=setRange); density=bool(density) or bool(normed); if density and not stacked: hist_kwargs['density']=density (in-place, preserving range).

Checked every plausible divergence:
1. range-key presence: model ties to setRange; real sets on else-branch only. Match.
2. binRange==None case (empty input, no finite value -> hist_kwargs['range']=None): value is only stored & passed downstream to the UNMODELED np.histogram, never inspected/compared inside the boundary, so present-key<->present-key with an opaque Rat*Rat carrier is faithful (mapping.md documents this abstraction correctly). Not a divergence.
3. density value: guard forces densityFlag=True, so stored value is always True in both; key never present-with-False. Match.
4. guard equivalence densityFlag && !stacked == density and not stacked; entries assembled independently, setting density leaves range untouched (the fix). Prepatch rebind-drops-range bug correctly FAILS the spec.

Verification: Solution.lean compiles (exit 0); #print axioms correct_assembleHistKeywordArgs = [propext] only (no sorryAx -> genuine proof). same_spec(Solution, prepatch) = True, spec region byte-identical. conformance_check.py: 120009 cases, 0 disagreements between post-patch oracle and Lean-impl shadow. Solution_prepatch.lean correctly fails the spec (G-DIFF pass). G-GOLD/G-EQ/G-CONF/G-AX(skip) all pass. Spec is neither too strong (gold verifies) nor drifting from repo behavior.

  result.range   = if setRange then some binRange else none
  result.density = if densityFlag && !stacked then some densityFlag else none
These match the gold-patched real Axes.hist assembly (lib/matplotlib/axes/_axes.py ~6664-6689): hist_kwargs['range']=bin_range set exactly on the single/empty-dataset else-branch (=setRange); density=bool(density) or bool(normed); if density and not stacked: hist_kwargs['density']=density (in-place, preserving range).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen: hard_failures=[], same_spec Solution vs Solution_prepatch = True). Reviewed the projected spec view (import/docstring/axioms/pure/post-conditions regions; impl+proof elided) by hand for semantic gold-reconstruction:

- No diff markers, no patched file path (lib/matplotlib/axes/_axes.py) or dotted module path, no gold-patch changed line reproduced ('hist_kwargs = dict(density=density)' / "hist_kwargs['density'] = density").
- Only distinctive changed symbol is `hist`; the spec-view identifier `HistKeywordArgs` lexically contains 'hist', but 'hist' appears verbatim in the public problem_statement ('hist() no longer respects range=... when density=True'), so it is already public — correctly not a leak.
- No narration terms (bug/fix/wrong/broken/pre-patch/regression) in any spec-view comment/docstring; comments describe target behavior ('these two entries are assembled independently; adding the density entry must NOT disturb a range entry').

Semantic check: the public problem_statement already fully states the discriminating behavior — range must be respected/preserved when density=True. The spec's postcondition (result.range pinned independently of the density entry) encodes exactly that publicly-specified behavior and nothing about the concrete gold edit (in-place item-set vs whole-dict rebind, the dict() call, hist_kwargs variable, line 6689). The spec view discloses no information about the gold edit beyond what problem_statement already gives.

The fix-narrating prose ('the fix', 'the bug', pre-patch modeling) lives only in refinement.md and mapping.md, which are audit-side artifacts, not the consumer spec view, and are not scanned by G-LEAK.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
