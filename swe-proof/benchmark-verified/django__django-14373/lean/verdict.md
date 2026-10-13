# P2 adversarial audit — django__django-14373

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closed a clean-axiom proof, so there is no verify-not-implies-correct witness and no faithful patch to resolve. The spec pins the output exactly: problem_spec_renderYear year result := result = padZeros 4 (toString year). I confirmed extensionally that padZeros 4 (toString year) == ('%04d' % year) for all Nat (matches over 0..999999 and full datetime domain 1..9999), so the pin is faithful to the patched Y() AND fully determines the output. By Lean soundness, no wrong impl can discharge the gold rfl proof.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
 
 -- impl-start
 def implementation_renderYear (year : Nat) : String := Id.run do
-  return padZeros 4 (toString year)
+  -- prepatch bug: bare numeral, no leading-zero padding
+  return toString year
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,11 @@
 
 -- impl-start
 def implementation_renderYear (year : Nat) : String := Id.run do
-  return padZeros 4 (toString year)
+  -- partial-domain: only pads for year >= 1000; leaves short years unpadded (wrong on <1000)
+  if year < 1000 then
+    return toString year
+  else
+    return padZeros 4 (toString year)
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
 
 -- impl-start
 def implementation_renderYear (year : Nat) : String := Id.run do
-  return padZeros 4 (toString year)
+  -- boundary off-by-one: pads to width 3, not 4
+  return padZeros 3 (toString year)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
 
 -- impl-start
 def implementation_renderYear (year : Nat) : String := Id.run do
-  return padZeros 4 (toString year)
+  -- boundary: pads to width 5, one too many
+  return padZeros 5 (toString year)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
 
 -- impl-start
 def implementation_renderYear (year : Nat) : String := Id.run do
-  return padZeros 4 (toString year)
+  -- wrong pad character: spaces instead of '0'
+  return String.mk (List.replicate (4 - (toString year).length) ' ') ++ toString year
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
 
 -- impl-start
 def implementation_renderYear (year : Nat) : String := Id.run do
-  return padZeros 4 (toString year)
+  -- degenerate constant: always four zeros regardless of year
+  return "0000"
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -44,7 +44,8 @@
 
 -- impl-start
 def implementation_renderYear (year : Nat) : String := Id.run do
-  return padZeros 4 (toString year)
+  -- wrong side: pads zeros on the RIGHT, not left
+  return toString year ++ String.mk (List.replicate (4 - (toString year).length) '0')
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering the year component of a date as a fixed-width decimal numeral.

A date carries a year as a non-negative whole number. This routine produces the
textual form of that year for inclusion in a formatted date string. The year is
written in base ten and left-padded with the character `'0'` so that the rendered
form always occupies at least four character positions. A year whose ordinary
base-ten form already has four or more digits is written out in full, with no
truncation and no extra padding.

Thus the rendered text is exactly the base-ten numeral of the year, prefixed by
just enough `'0'` characters to reach a minimum width of four.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The textual
-- rendering of the year (its base-ten numeral together with the leading-zero
-- padding to a minimum width) is the operation governed here, so it is modeled
-- structurally with concrete operations; no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Left-pad a string with `'0'` characters up to a minimum `width`. If `s`
already has length `≥ width`, it is returned unchanged (natural subtraction makes
the padding count `0`). -/
def padZeros (width : Nat) (s : String) : String :=
  String.mk (List.replicate (width - s.length) '0') ++ s
-- pure-end

-- post-conditions-start
/-- The rendered text is the base-ten numeral of `year`, left-padded with `'0'`
characters to a minimum width of four. This pins the result exactly: it is the
decimal digits of `year` (no leading zeros beyond those introduced by the
padding), preceded by exactly `4 - (number of decimal digits)` zero characters
when that quantity is positive, and unchanged when the numeral already reaches
width four. -/
def problem_spec_renderYear (year : Nat) (result : String) : Prop :=
  result = padZeros 4 (toString year)
-- post-conditions-end

-- impl-start
def implementation_renderYear (year : Nat) : String := Id.run do
  return padZeros 4 (toString year)
-- impl-end

-- proof-start
theorem correct_renderYear :
    ∀ (year : Nat),
      problem_spec_renderYear year (implementation_renderYear year) := by
  intro year
  unfold problem_spec_renderYear implementation_renderYear
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Same-spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (venv python).

Positive control (gold Solution.lean): bash scripts/lean_verify.sh .../pos_control.lean -> exit 0. #print axioms correct_renderYear -> 'does not depend on any axioms' (clean).

7 DISTINCT same-spec wrong impls (impl region only edited; axioms/pure/pre/post byte-identical), each ran bash scripts/lean_verify.sh <file>:
- atk_1 prepatch bug (bare `toString year`, no padding) -> exit 1, rfl failed L57
- atk_2 partial-domain (unpadded for year<1000, correct otherwise) -> exit 1, rfl failed L60
- atk_3 boundary (padZeros 3) -> exit 1, rfl failed L57
- atk_4 boundary (padZeros 5) -> exit 1, rfl failed L57
- atk_5 control-flow/effect (pad with ' ' space char instead of '0') -> exit 1, rfl failed L57
- atk_6 ungrounded-oracle/degenerate constant (always "0000") -> exit 1, rfl failed L57
- atk_7 right-side padding (append zeros on right instead of left) -> exit 1, rfl failed L57
All failures are genuine `rfl` tactic failures (Tactic `rfl` failed: The left-hand side ...), not syntax/parse errors. prepatch reproduced (atk_1 == Solution_prepatch.lean impl, fails as documented in refinement.md).

Step 2 (materialize+resolve faithful patch) is vacuous: NO attack achieved a closing clean-axiom proof, so there is no candidate requiring a resolve run. patches={} accordingly.

refinement.md audit: 4 legs. #1 year:Nat = R (Nat superset of datetime int 1..9999). #2 toString = I. #3 padZeros 4 = I (deep model of %04d). #4 return = I (str() wrapper = identity post-patch). No A-consumed / A-reference legs; mapping.md confirms no opaque/axiom, G-AX skips, axiom_check is skip stub. No kind-3 (unmapped) legs. Correspondence holds: the modeled operation padZeros4(toString) is exactly '%04d' % year (verified extensionally). G-CONF conformance_check.py differential-tests the shadow against faithful '%04d' % year oracle with pinned seed 14373, >=1.2e5 inputs + edge cases.

Conclusion: exact-equality spec is a tight, input-grounded pin faithful to the patched code; verify => correct holds. SOUND after 7 attacks, none breaks it.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong impl closed a clean-axiom proof, so there is no verify-not-implies-correct witness and no faithful patch to resolve. The spec pins the output exactly: problem_spec_renderYear year result := result = padZeros 4 (toString year). I confirmed extensionally that padZeros 4 (toString year) == ('%04d' % year) for all Nat (matches over 0..999999 and full datetime domain 1..9999), so the pin is faithful to the patched Y() AND fully determines the output. By Lean soundness, no wrong impl can discharge the gold rfl proof.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering the year component of a date as a fixed-width decimal numeral.

A date carries a year as a non-negative whole number. This routine produces the
textual form of that year for inclusion in a formatted date string. The year is
written in base ten and left-padded with the character `'0'` so that the rendered
form always occupies at least four character positions. A year whose ordinary
base-ten form already has four or more digits is written out in full, with no
truncation and no extra padding.

Thus the rendered text is exactly the base-ten numeral of the year, prefixed by
just enough `'0'` characters to reach a minimum width of four.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The textual
-- rendering of the year (its base-ten numeral together with the leading-zero
-- padding to a minimum width) is the operation governed here, so it is modeled
-- structurally with concrete operations; no `opaque`/`axiom` callee contract is
-- needed.
-- axioms-end

-- pure-start
/-- Left-pad a string with `'0'` characters up to a minimum `width`. If `s`
already has length `≥ width`, it is returned unchanged (natural subtraction makes
the padding count `0`). -/
def padZeros (width : Nat) (s : String) : String :=
  String.mk (List.replicate (width - s.length) '0') ++ s
-- pure-end

-- post-conditions-start
/-- The rendered text is the base-ten numeral of `year`, left-padded with `'0'`
characters to a minimum width of four. This pins the result exactly: it is the
decimal digits of `year` (no leading zeros beyond those introduced by the
padding), preceded by exactly `4 - (number of decimal digits)` zero characters
when that quantity is positive, and unchanged when the numeral already reaches
width four. -/
def problem_spec_renderYear (year : Nat) (result : String) : Prop :=
  result = padZeros 4 (toString year)
-- post-conditions-end

-- impl-start
def implementation_renderYear (year : Nat) : String := Id.run do
  return padZeros 4 (toString year)
-- impl-end

-- proof-start
theorem correct_renderYear :
    ∀ (year : Nat),
      problem_spec_renderYear year (implementation_renderYear year) := by
  intro year
  unfold problem_spec_renderYear implementation_renderYear
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Same-spec confirmed True for all 7 attacks via swebench_unified.markers.same_spec (venv python).

Positive control (gold Solution.lean): bash scripts/lean_verify.sh .../pos_control.lean -> exit 0. #print axioms correct_renderYear -> 'does not depend on any axioms' (clean).

7 DISTINCT same-spec wrong impls (impl region only edited; axioms/pure/pre/post byte-identical), each ran bash scripts/lean_verify.sh <file>:
- atk_1 prepatch bug (bare `toString year`, no padding) -> exit 1, rfl failed L57
- atk_2 partial-domain (unpadded for year<1000, correct otherwise) -> exit 1, rfl failed L60
- atk_3 boundary (padZeros 3) -> exit 1, rfl failed L57
- atk_4 boundary (padZeros 5) -> exit 1, rfl failed L57
- atk_5 control-flow/effect (pad with ' ' space char instead of '0') -> exit 1, rfl failed L57
- atk_6 ungrounded-oracle/degenerate constant (always "0000") -> exit 1, rfl failed L57
- atk_7 right-side padding (append zeros on right instead of left) -> exit 1, rfl failed L57
All failures are genuine `rfl` tactic failures (Tactic `rfl` failed: The left-hand side ...), not syntax/parse errors. prepatch reproduced (atk_1 == Solution_prepatch.lean impl, fails as documented in refinement.md).

Step 2 (materialize+resolve faithful patch) is vacuous: NO attack achieved a closing clean-axiom proof, so there is no candidate requiring a resolve run. patches={} accordingly.

refinement.md audit: 4 legs. #1 year:Nat = R (Nat superset of datetime int 1..9999). #2 toString = I. #3 padZeros 4 = I (deep model of %04d). #4 return = I (str() wrapper = identity post-patch). No A-consumed / A-reference legs; mapping.md confirms no opaque/axiom, G-AX skips, axiom_check is skip stub. No kind-3 (unmapped) legs. Correspondence holds: the modeled operation padZeros4(toString) is exactly '%04d' % year (verified extensionally). G-CONF conformance_check.py differential-tests the shadow against faithful '%04d' % year oracle with pinned seed 14373, >=1.2e5 inputs + edge cases.

Conclusion: exact-equality spec is a tight, input-grounded pin faithful to the patched code; verify => correct holds. SOUND after 7 attacks, none breaks it.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14373, modeled function renderYear = post-patch DateFormat.Y ('%04d' % self.data.year), wrapped by Formatter.format's str(...) which is identity on the already-string result.

Spec: problem_spec_renderYear year result := result = padZeros 4 (toString year), where padZeros width s = replicate(width - len s, '0') ++ s (Nat subtraction clamps to 0 when len>=width). This pins the output EXACTLY to an input-grounded expression.

Real callee behavior: '%04d' % year = base-ten numeral of year, left-zero-padded to a minimum width of 4, never truncated for >=4-digit years. str(...) wrapper is identity.

Differential agreement (spec vs real repo):
- Ran padZeros-4 shadow vs str('%04d' % year) over years 0..19999 plus {100000, 999999, 1234567}: 0 disagreements.
- Bundle conformance_check.py (seed 14373) ran 120,020 inputs incl. edge cases {1,9,10,99,100,999,1000,1999,9999,...} and >=1e5 fuzzed years across the datetime domain (1..9999) and a broader superset: status=pass, disagreements=0.
- Semantics match exactly: %04d = min-field-width 4, zero-flag left pad, no truncation; padZeros via Nat subtraction reproduces this (clamps to 0 for len>=4). For year>=1000 both yield the bare numeral; for year<1000 both zero-pad to width 4 (e.g. 1->'0001', 999->'0999').

Domain: Lean uses Nat, a superset of the real datetime year range (1..9999). The spec agrees with the real callee across the entire real domain AND the superset extension, so the Nat generalization introduces no drift and no over-strength. Pinning the result exactly to the actual patched output is faithful, not too-strong: it matches (not exceeds) real behavior.

Evidence checks:
- lean_verify.sh exit 0 (compiles, no sorry/error).
- #print axioms correct_renderYear -> 'does not depend on any axioms' (no sorryAx; rfl proof is genuine).
- same_spec(Solution.lean, Solution_prepatch.lean) = True: spec region byte-identical; only impl/proof differ (prepatch returns bare toString year, which correctly fails the spec on years <1000, matching the FAIL_TO_PASS test test_Y_format_year_before_1000).
- meta gates: G-CONF pass, G-EQ pass, G-DIFF pass, G-RESOLVE pass, G-PANEL-2 pass (this role). (G-PANEL-1 fail is a separate role, out of scope for faithfulness/drift.)

No diverging input exists between the modeled function and the real repo callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction review of the lean spec view for django__django-14373 (DateFormat.Y zero-padding). Gold edit: `-return self.data.year` / `+return '%04d' % self.data.year`.

Mechanical checks: markers.same_spec(Solution, Solution_prepatch)=True (spec regions byte-identical; only impl/proof differ, as required). leakage.screen over the spec_view passes (hard_failures=[]).

Substantive judgment: the PUBLIC problem_statement already discloses the entire discriminating content of the gold edit — 'The Y specifier ... is supposed to always return a four-digit year padded with zeros. This doesn't seem to be the case for year < 1000.' That openly declares (a) fixed width = four and (b) left zero-padding, which is exactly what `%04d` does. The spec view's post-condition `result = padZeros 4 (toString year)` and its docstrings (base-ten numeral left-padded with '0' to a minimum width of four, no truncation for >=4 digits) formalize precisely this publicly-stated behavior and nothing more. No format-string literal, method name, or hidden discriminator appears beyond what the problem_statement already states. The pre-patch discriminator (years <1000 render short) is likewise the public bug report itself, not a spec-side leak. Spec adds no information beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
