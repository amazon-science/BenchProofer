# P2 adversarial audit — astropy__astropy-14182

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 -- impl-start
 def implementation_rstWrap
     (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
-  let idx := numHeaderRows
+  let idx := 1
   let sep := lines.getD idx ""
   let mut out := [sep] ++ lines ++ [sep]
   return out
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
 
 -- impl-start
 def implementation_rstDataStart (numHeaderRows : Nat) : Nat := Id.run do
-  return 2 + numHeaderRows
+  return 3
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
 
 -- impl-start
 def implementation_rstDataStart (numHeaderRows : Nat) : Nat := Id.run do
-  return 2 + numHeaderRows
+  return 1 + numHeaderRows
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 -- impl-start
 def implementation_rstWrap
     (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
-  let idx := numHeaderRows
+  let idx := numHeaderRows + 1
   let sep := lines.getD idx ""
   let mut out := [sep] ++ lines ++ [sep]
   return out
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,7 +53,7 @@
 -- impl-start
 def implementation_rstWrap
     (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
-  let idx := numHeaderRows
+  let idx := if numHeaderRows = 1 then numHeaderRows else 1
   let sep := lines.getD idx ""
   let mut out := [sep] ++ lines ++ [sep]
   return out
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,7 +78,7 @@
 
 -- impl-start
 def implementation_rstDataStart (numHeaderRows : Nat) : Nat := Id.run do
-  return 2 + numHeaderRows
+  return 2 * numHeaderRows
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,8 +53,7 @@
 -- impl-start
 def implementation_rstWrap
     (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
-  let idx := numHeaderRows
-  let sep := lines.getD idx ""
+  let sep := lines.getD 0 ""
   let mut out := [sep] ++ lines ++ [sep]
   return out
 -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -53,9 +53,9 @@
 -- impl-start
 def implementation_rstWrap
     (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
-  let idx := numHeaderRows
-  let sep := lines.getD idx ""
-  let mut out := [sep] ++ lines ++ [sep]
+  let sep := lines.getD numHeaderRows ""
+  let bad := lines.getD (numHeaderRows + 1) ""
+  let mut out := [bad] ++ lines ++ [sep]
   return out
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Supporting a configurable list of header rows in the simple reStructuredText
fixed-width table format.

A simple reStructuredText table is laid out as a leading column-rule line (a row
of `=` characters), then one or more header rows, then a second rule line, then
the data rows, then a trailing rule line. Historically this format always emitted
and consumed exactly one header row (the column names). The desired behaviour is
to let the caller supply a list of header rows (for example the column names, the
units, and the element types), just as the sibling fixed-width formats already
allow.

Two positions in the format depend on HOW MANY header rows there are:

* When emitting, the renderer lays out the header rows first and then the
  column-rule line, so that rule line sits at 0-based position `numHeaderRows`
  in the rendered sequence of lines. The finished output brackets the whole
  rendered table with a copy of that rule line at the top and the bottom.

* When parsing, the first data line sits two lines below the last header row
  together with the leading rule line — i.e. at position `2 + numHeaderRows`.

For the historical single-header-row case (`numHeaderRows = 1`) these reduce to
the positions `1` and `3` respectively, so existing single-row tables are
unaffected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both modeled
-- quantities are pure functions of the number of header rows (and, for the
-- emit case, of the already-rendered sequence of lines, which enters as a direct
-- input observation rather than being recomputed). No `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Emitting: the finished output is the already-rendered sequence of `lines`
bracketed top and bottom by a copy of the column-rule line, which is the line at
position `numHeaderRows` in that sequence. Every other line is exactly the
rendered line in its original order. -/
def problem_spec_rstWrap
    (numHeaderRows : Nat) (lines : List String) (result : List String) : Prop :=
  result = [lines.getD numHeaderRows ""] ++ lines ++ [lines.getD numHeaderRows ""]
-- post-conditions-end

-- impl-start
def implementation_rstWrap
    (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
  let idx := numHeaderRows
  let sep := lines.getD idx ""
  let mut out := [sep] ++ lines ++ [sep]
  return out
-- impl-end

-- proof-start
theorem correct_rstWrap :
    ∀ (numHeaderRows : Nat) (lines : List String),
      problem_spec_rstWrap numHeaderRows lines
        (implementation_rstWrap numHeaderRows lines) := by
  intro numHeaderRows lines
  unfold problem_spec_rstWrap implementation_rstWrap
  rfl
-- proof-end

-- post-conditions-start
/-- Parsing: the position of the first data line is two lines below the header
rows together with the leading rule line, i.e. `2 + numHeaderRows`. -/
def problem_spec_rstDataStart (numHeaderRows : Nat) (result : Nat) : Prop :=
  result = 2 + numHeaderRows
-- post-conditions-end

-- impl-start
def implementation_rstDataStart (numHeaderRows : Nat) : Nat := Id.run do
  return 2 + numHeaderRows
-- impl-end

-- proof-start
theorem correct_rstDataStart :
    ∀ (numHeaderRows : Nat),
      problem_spec_rstDataStart numHeaderRows
        (implementation_rstDataStart numHeaderRows) := by
  intro numHeaderRows
  unfold problem_spec_rstDataStart implementation_rstDataStart
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** two independent Lean triples, both with EXACT-EQUALITY postconditions and NO axioms / NO A-legs.
- problem_spec_rstWrap: result = [lines.getD numHeaderRows ""] ++ lines ++ [lines.getD numHeaderRows ""]
- problem_spec_rstDataStart: result = 2 + numHeaderRows
Consequence: any verifying impl is FORCED to be behaviorally gold-identical on all inputs; any deviation makes the ∀ theorem false and Lean soundness blocks the proof. This is the tight case where verify⇒correct holds structurally.

**SAME_SPEC:** all 8 attacks + positive_control return same_spec=True vs bundle Solution.lean (edited impl region only; axioms/pure/pre/post byte-identical).

### ATTACKS (all edit ONLY impl region, keep gold theorem statement; verified concurrently ≤4 via scripts/lean_verify.sh <f>):
- atk_1 (prepatch-bug rstWrap): idx := 1  -> EXIT=1, rfl failed: (pure out with sep=lines.getD 1) ≠ [lines.getD numHeaderRows ""]++lines++[...]
- atk_2 (prepatch-bug rstDataStart): return 3 -> EXIT=1, rfl failed: (pure 3).run ≠ 2 + numHeaderRows
- atk_3 (boundary off-by-one): return 1 + numHeaderRows -> EXIT=1, rfl failed (definitional ineq)
- atk_4 (boundary off-by-one): idx := numHeaderRows + 1 -> EXIT=1, rfl failed
- atk_5 (partial-domain / control-flow-effect): idx := if numHeaderRows = 1 then numHeaderRows else 1 (correct only at nHR=1) -> EXIT=1, rfl failed
- atk_6 (ungrounded-oracle echo): return 2 * numHeaderRows (agrees only at nHR=2) -> EXIT=1, rfl failed
- atk_7 (wrong sep source): sep := lines.getD 0 "" (bracket with head line) -> EXIT=1, rfl failed
- atk_8 (asymmetric-bracket control-flow): top bracket uses getD (numHeaderRows+1), bottom uses getD numHeaderRows -> EXIT=1, rfl failed
All 8 failures are genuine `Tactic rfl failed: LHS not definitionally equal to RHS` errors, not incidental syntax errors.

**POSITIVE CONTROL:** positive_control.lean (byte copy of bundle Solution.lean) -> lean_verify EXIT=0. #print axioms correct_rstWrap / correct_rstDataStart => 'does not depend on any axioms' (clean, empty axiom set, no sorryAx).

**PREPATCH REPRODUCED:** bundle Solution_prepatch_1.lean (idx fixed at 1) and Solution_prepatch_2.lean (const 3) both EXIT=1 with genuine rfl definitional-ineq failures — carried gold rfl proof cannot close, matching the F2P discriminator numHeaderRows>1 (round-trip uses 3 header rows).

**STEP-2 RESOLVE:** NO attack with a closing clean-axiom proof exists (0 of 8 verify), so there is no faithful patch to materialize/resolve — the verify⇏correct trigger never fires. This is expected given the exact-equality specs.

**REFINEMENT.MD AUDIT:** every leg is R or I; no kind-3 legs.
- Site 1 rstWrap: numHeaderRows↔len(self.header.header_rows) [R]; lines.getD idx ""↔lines[idx] [R, total read vs in-range Python index]; [sep]++lines++[sep]↔[lines[idx]]+lines+[lines[idx]] [I]; return [I].
- Site 2 rstDataStart: return 2 + numHeaderRows↔self.data.start_line = 2 + len(self.header.header_rows) [R].
- NO A-consumed / NO A-reference legs. super().write (fixed-width renderer) is UNCHANGED by the patch and correctly treated as an INPUT OBSERVATION (lines : List String), not an axiomatized callee — patch only changes WHICH index is selected. Empty axioms region + G-AX skip is justified per SPEC_GUIDE §3 (no axiomatizing a deeply-modeled changed decision). No A-leg correspondence to audit.

**VERDICT:** SOUND. ≥5 distinct wrong impls (8 run) all fail to verify; none closes with clean axioms; positive control verifies clean; prepatches reproduce the bug; refinement legs are all R/I with justified empty-axioms treatment of the unchanged renderer.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Supporting a configurable list of header rows in the simple reStructuredText
fixed-width table format.

A simple reStructuredText table is laid out as a leading column-rule line (a row
of `=` characters), then one or more header rows, then a second rule line, then
the data rows, then a trailing rule line. Historically this format always emitted
and consumed exactly one header row (the column names). The desired behaviour is
to let the caller supply a list of header rows (for example the column names, the
units, and the element types), just as the sibling fixed-width formats already
allow.

Two positions in the format depend on HOW MANY header rows there are:

* When emitting, the renderer lays out the header rows first and then the
  column-rule line, so that rule line sits at 0-based position `numHeaderRows`
  in the rendered sequence of lines. The finished output brackets the whole
  rendered table with a copy of that rule line at the top and the bottom.

* When parsing, the first data line sits two lines below the last header row
  together with the leading rule line — i.e. at position `2 + numHeaderRows`.

For the historical single-header-row case (`numHeaderRows = 1`) these reduce to
the positions `1` and `3` respectively, so existing single-row tables are
unaffected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Both modeled
-- quantities are pure functions of the number of header rows (and, for the
-- emit case, of the already-rendered sequence of lines, which enters as a direct
-- input observation rather than being recomputed). No `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Emitting: the finished output is the already-rendered sequence of `lines`
bracketed top and bottom by a copy of the column-rule line, which is the line at
position `numHeaderRows` in that sequence. Every other line is exactly the
rendered line in its original order. -/
def problem_spec_rstWrap
    (numHeaderRows : Nat) (lines : List String) (result : List String) : Prop :=
  result = [lines.getD numHeaderRows ""] ++ lines ++ [lines.getD numHeaderRows ""]
-- post-conditions-end

-- impl-start
def implementation_rstWrap
    (numHeaderRows : Nat) (lines : List String) : List String := Id.run do
  let idx := numHeaderRows
  let sep := lines.getD idx ""
  let mut out := [sep] ++ lines ++ [sep]
  return out
-- impl-end

-- proof-start
theorem correct_rstWrap :
    ∀ (numHeaderRows : Nat) (lines : List String),
      problem_spec_rstWrap numHeaderRows lines
        (implementation_rstWrap numHeaderRows lines) := by
  intro numHeaderRows lines
  unfold problem_spec_rstWrap implementation_rstWrap
  rfl
-- proof-end

-- post-conditions-start
/-- Parsing: the position of the first data line is two lines below the header
rows together with the leading rule line, i.e. `2 + numHeaderRows`. -/
def problem_spec_rstDataStart (numHeaderRows : Nat) (result : Nat) : Prop :=
  result = 2 + numHeaderRows
-- post-conditions-end

-- impl-start
def implementation_rstDataStart (numHeaderRows : Nat) : Nat := Id.run do
  return 2 + numHeaderRows
-- impl-end

-- proof-start
theorem correct_rstDataStart :
    ∀ (numHeaderRows : Nat),
      problem_spec_rstDataStart numHeaderRows
        (implementation_rstDataStart numHeaderRows) := by
  intro numHeaderRows
  unfold problem_spec_rstDataStart implementation_rstDataStart
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

**SPEC SHAPE:** two independent Lean triples, both with EXACT-EQUALITY postconditions and NO axioms / NO A-legs.
- problem_spec_rstWrap: result = [lines.getD numHeaderRows ""] ++ lines ++ [lines.getD numHeaderRows ""]
- problem_spec_rstDataStart: result = 2 + numHeaderRows
Consequence: any verifying impl is FORCED to be behaviorally gold-identical on all inputs; any deviation makes the ∀ theorem false and Lean soundness blocks the proof. This is the tight case where verify⇒correct holds structurally.

**SAME_SPEC:** all 8 attacks + positive_control return same_spec=True vs bundle Solution.lean (edited impl region only; axioms/pure/pre/post byte-identical).

### ATTACKS (all edit ONLY impl region, keep gold theorem statement; verified concurrently ≤4 via scripts/lean_verify.sh <f>):
- atk_1 (prepatch-bug rstWrap): idx := 1  -> EXIT=1, rfl failed: (pure out with sep=lines.getD 1) ≠ [lines.getD numHeaderRows ""]++lines++[...]
- atk_2 (prepatch-bug rstDataStart): return 3 -> EXIT=1, rfl failed: (pure 3).run ≠ 2 + numHeaderRows
- atk_3 (boundary off-by-one): return 1 + numHeaderRows -> EXIT=1, rfl failed (definitional ineq)
- atk_4 (boundary off-by-one): idx := numHeaderRows + 1 -> EXIT=1, rfl failed
- atk_5 (partial-domain / control-flow-effect): idx := if numHeaderRows = 1 then numHeaderRows else 1 (correct only at nHR=1) -> EXIT=1, rfl failed
- atk_6 (ungrounded-oracle echo): return 2 * numHeaderRows (agrees only at nHR=2) -> EXIT=1, rfl failed
- atk_7 (wrong sep source): sep := lines.getD 0 "" (bracket with head line) -> EXIT=1, rfl failed
- atk_8 (asymmetric-bracket control-flow): top bracket uses getD (numHeaderRows+1), bottom uses getD numHeaderRows -> EXIT=1, rfl failed
All 8 failures are genuine `Tactic rfl failed: LHS not definitionally equal to RHS` errors, not incidental syntax errors.

**POSITIVE CONTROL:** positive_control.lean (byte copy of bundle Solution.lean) -> lean_verify EXIT=0. #print axioms correct_rstWrap / correct_rstDataStart => 'does not depend on any axioms' (clean, empty axiom set, no sorryAx).

**PREPATCH REPRODUCED:** bundle Solution_prepatch_1.lean (idx fixed at 1) and Solution_prepatch_2.lean (const 3) both EXIT=1 with genuine rfl definitional-ineq failures — carried gold rfl proof cannot close, matching the F2P discriminator numHeaderRows>1 (round-trip uses 3 header rows).

**STEP-2 RESOLVE:** NO attack with a closing clean-axiom proof exists (0 of 8 verify), so there is no faithful patch to materialize/resolve — the verify⇏correct trigger never fires. This is expected given the exact-equality specs.

**REFINEMENT.MD AUDIT:** every leg is R or I; no kind-3 legs.
- Site 1 rstWrap: numHeaderRows↔len(self.header.header_rows) [R]; lines.getD idx ""↔lines[idx] [R, total read vs in-range Python index]; [sep]++lines++[sep]↔[lines[idx]]+lines+[lines[idx]] [I]; return [I].
- Site 2 rstDataStart: return 2 + numHeaderRows↔self.data.start_line = 2 + len(self.header.header_rows) [R].
- NO A-consumed / NO A-reference legs. super().write (fixed-width renderer) is UNCHANGED by the patch and correctly treated as an INPUT OBSERVATION (lines : List String), not an axiomatized callee — patch only changes WHICH index is selected. Empty axioms region + G-AX skip is justified per SPEC_GUIDE §3 (no axiomatizing a deeply-modeled changed decision). No A-leg correspondence to audit.

**VERDICT:** SOUND. ≥5 distinct wrong impls (8 run) all fail to verify; none closes with clean axioms; positive control verifies clean; prepatches reproduce the bug; refinement legs are all R/I with justified empty-axioms treatment of the unchanged renderer.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-vs-real-callee drift) check for astropy__astropy-14182 lean bundle.

Modeled functions and real repo (base a5917978be3..., gold patch verified in /tmp worktree):
- rstWrap: gold `RST.write` does `idx = len(self.header.header_rows); lines = [lines[idx]] + lines + [lines[idx]]`. Spec: `result = [lines.getD numHeaderRows ""] ++ lines ++ [lines.getD numHeaderRows ""]`. Exact match under bijection numHeaderRows <-> len(header_rows).
- rstDataStart: gold `RST.read` sets `self.data.start_line = 2 + len(self.header.header_rows)`. Spec: `result = 2 + numHeaderRows`. Exact match.

Rule-line index confirmed against FixedWidthData.write (fixedwidth.py:241-268): renderer appends numHeaderRows header lines, then the position/rule line, then data rows, so the rule line sits at index numHeaderRows in super().write output; the gold docstring example (header_rows=['name','unit']) corroborates. Thus idx=numHeaderRows < len(lines) on every reachable rendered input.

**Totalization boundary is unreachable:** `lines.getD numHeaderRows ""` returns "" only when numHeaderRows >= len(lines), but the rendered `lines` always has >= numHeaderRows+1 entries (header rows + rule line + >=1 data row). On the real callee's domain getD is identical to Python lines[idx] (which would IndexError only off-domain). So the spec does not disagree with the real callee on any reachable input; no diverging input exists.

Verification evidence:
- same_spec(Solution, prepatch_1) = True, same_spec(Solution, prepatch_2) = True (spec regions byte-identical; only impl differs). 
- lean_verify.sh exit 0; `#print axioms correct_rstWrap` and `correct_rstDataStart` both report 'does not depend on any axioms' (no sorryAx, real proofs by rfl).
- **G-DIFF:** both prepatches (idx fixed at 1; start fixed at 3) fail verification against the spec, confirming the spec is strong enough to catch the bug (discriminated at numHeaderRows>1, F2P uses 3).
- conformance_check.py differentially tests both R/I legs (oracle=post-patch selection vs shadow=impl transliteration), seed 14182, N=120000; conf_skip=false.

The spec is neither too strong (no in-domain divergence) nor drifting from real behavior. FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Ran the mechanical G-LEAK screen (leakage.screen over spec_view) on Solution.lean: PASSED, zero hard failures. Confirmed spec-region byte-identity: same_spec(Solution, prepatch_1) and (Solution, prepatch_2) both True, so the frozen spec view is stable.

Semantic review of the spec view vs. the PUBLIC problem_statement (not hints; hints_text is empty here):
- Public problem_statement is a feature request that already displays the desired behavior for header_rows=['name','unit'] (rule line brackets top/bottom, N header lines between). It reveals the behavioral goal but nothing about the edit site.
- Gold edit: rst.py — bracket at idx = len(self.header.header_rows) in RST.write; remove SimpleRSTData.start_line = 3 and add RST.read setting self.data.start_line = 2 + len(self.header.header_rows).
- Spec view expresses only the abstract behavior in repo-decoupled Lean vocabulary (numHeaderRows, lines, result): rule line at position numHeaderRows -> bracket with lines.getD numHeaderRows ""; data start = 2 + numHeaderRows.

Checked every G-LEAK rule: (L1) no diff markers; no gold-patch line reproduced — Python '[lines[idx]] + lines + [lines[idx]]' is NOT present in the Lean view (which uses List.getD/++). (L2) patched file path rst.py, module path, and touched symbols (get_fixedwidth_params, read) absent from view; spec uses numHeaderRows not header_rows/len(self.header.header_rows). (L3) no bug/fix narration — the word 'historical'/'historically' is not in the narration blocklist, and no 'bug'/'previously'/'wrong'/'off-by-one' appears.

The docstring line 'For the historical single-header-row case (numHeaderRows = 1) these reduce to the positions 1 and 3' names values that coincide with the pre-patch constants, but it states them as the MATHEMATICAL specialization of the generalized formulas at numHeaderRows=1 (a PASS_TO_PASS preservation note), not as a reference to the removed start_line=3 attribute or the historical lines[1] index. A faithful behavioral spec must state the correct positions; locating rst.py, the class attribute, and the write/read overrides remains entirely unrevealed. No reconstruction of the gold edit beyond the public problem_statement is possible from this view.

**Verdict:** NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
