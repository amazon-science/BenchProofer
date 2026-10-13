# P2 adversarial audit — django__django-16485

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_1b.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation closes correct_floatformat. The postcondition pins result to an EXACT closed-form Option String equality over the four opaque callees (decIsWhole, decIntPart, decimalDigits, numberFormat), so any behaviorally-distinct impl is unprovable — the opaque callees have no reduction rules and the residual goal reduces to distinct opaque values on the discriminating input (whole d, p=0).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,11 +87,10 @@
 
 -- impl-start
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
-  if decIsWhole d && decide (p ≤ 0) then
+  if decIsWhole d && decide (p < 0) then
     return some (numberFormat (toString (decIntPart d)) 0)
   return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
```

Attack 2 — `atk_1b.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,16 +87,17 @@
 
 -- impl-start
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
-  if decIsWhole d && decide (p ≤ 0) then
+  if decIsWhole d && decide (p < 0) then
     return some (numberFormat (toString (decIntPart d)) 0)
   return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
   intro d p
   unfold problem_spec_floatformat implementation_floatformat
+  simp only [Id.run, Id.pure_eq, Id.bind_eq]
   by_cases h : decIsWhole d && decide (p ≤ 0) <;>
-    simp only [h, Id.run, bind] <;> rfl
+  by_cases h2 : decIsWhole d && decide (p < 0) <;>
+  simp_all [Id.run] <;> first | rfl | omega | (try decide) | aesop
 -- proof-end
```

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,11 +87,8 @@
 
 -- impl-start
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
-  if decIsWhole d && decide (p ≤ 0) then
-    return some (numberFormat (toString (decIntPart d)) 0)
   return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
```

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,11 +87,10 @@
 
 -- impl-start
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
-  if decIsWhole d && decide (p ≤ 0) then
+  if decIsWhole d then
     return some (numberFormat (toString (decIntPart d)) 0)
   return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
```

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,10 +88,9 @@
 -- impl-start
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
   if decIsWhole d && decide (p ≤ 0) then
-    return some (numberFormat (toString (decIntPart d)) 0)
-  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
+    return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
+  return some (numberFormat (toString (decIntPart d)) 0)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
```

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,9 +89,8 @@
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
   if decIsWhole d && decide (p ≤ 0) then
     return some (numberFormat (toString (decIntPart d)) 0)
-  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
+  return (decimalDigits d p).map (fun s => numberFormat s 0)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,11 +87,10 @@
 
 -- impl-start
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
-  if decIsWhole d && decide (p ≤ 0) then
+  if decIsWhole d && decide (p.natAbs = 0) then
     return some (numberFormat (toString (decIntPart d)) 0)
   return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -88,10 +88,9 @@
 -- impl-start
 def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
   if decIsWhole d && decide (p ≤ 0) then
-    return some (numberFormat (toString (decIntPart d)) 0)
+    return some (numberFormat (toString (decIntPart d)) p.natAbs)
   return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
 -- impl-end
-
 -- proof-start
 theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
     problem_spec_floatformat d p (implementation_floatformat d p) := by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a decimal value as text for a requested number of decimal places.

A value is rendered together with a requested number of decimal places `p`
(an integer that may be negative). There are two ways the value can be rendered:

  * as a plain integer — the value's whole part, formatted with no fractional
    digits; or
  * in the general way — the value rounded/padded to the requested number of
    fractional places. This general digit computation is PARTIAL: on some
    values it rejects its inputs and produces no digit text at all, in which
    case the call as a whole yields no rendered text (the failure propagates
    to the caller).

The choice between them depends on the value and on `p`:

  * when the value is a whole number (its fractional part is zero) AND the
    requested number of decimal places is NOT positive (zero or negative), the
    value is rendered as a plain integer — there are no fractional digits worth
    showing, so the whole part alone is emitted;
  * in every other case (the value has a fractional part, or a positive number
    of places was requested), the general rendering is used — producing text
    exactly when the digit computation does.

Both produced digit texts finish by passing through the same locale/grouping
formatting step; only the digit text and the place count fed to it differ
between the two cases.
-/

-- axioms-start
/-- A decimal value, modeled by the data its standard tuple view exposes
(`mapping.md` gives the bijection to the repo's decimal tuple):
* `negative` — whether the value carries a negative sign;
* `digits` — its significant digits, most-significant first;
* `exponent` — the tuple exponent (the value is `digits · 10^exponent`).
Nothing here inspects these fields directly; they carry the value so the
unchanged sub-computations below can act on it. -/
structure DecVal where
  negative : Bool
  digits : List Nat
  exponent : Int

/-- Whether the value is a whole number — its fractional part is zero. (Unchanged
sub-computation; signature only.) -/
opaque decIsWhole : DecVal → Bool

/-- The value's whole (integer) part. (Unchanged sub-computation; signature
only.) -/
opaque decIntPart : DecVal → Int

/-- The general digit text for the value rounded/padded to the given number of
decimal places: `some` of the assembled sign/digits/point string before locale
formatting, or `none` when the digit computation rejects its inputs and
produces no text (that failure propagates to the caller — the call yields no
rendered text). (Unchanged sub-computation; signature only.) -/
opaque decimalDigits : DecVal → Int → Option String

/-- The locale/grouping formatting step applied to a digit string with a given
number of fractional places, under this call's locale/grouping
configuration. (Unchanged sub-computation; signature only.) -/
opaque numberFormat : String → Nat → String
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the rendering choice is a direct
-- decision over `decIsWhole d` and the sign of `p`, and each branch's outcome
-- is the corresponding unchanged sub-computation.
-- pure-end

-- post-conditions-start
/-- The rendered outcome is exactly the outcome of the selected branch. When the
value is whole and the requested place count is not positive, it is the whole
part formatted with zero fractional places (always produced). Otherwise it is
the general rendering at `|p|` places — produced exactly when the general digit
computation produces text, and absent (the failure propagates) when it does
not. Both produced texts go through the same final formatting step, so the
outcome is fully determined by `d` and `p`. -/
def problem_spec_floatformat (d : DecVal) (p : Int) (result : Option String) : Prop :=
  result =
    (if decIsWhole d && decide (p ≤ 0)
     then some (numberFormat (toString (decIntPart d)) 0)
     else (decimalDigits d p).map (fun s => numberFormat s p.natAbs))
-- post-conditions-end

-- impl-start
def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
  if decIsWhole d && decide (p ≤ 0) then
    return some (numberFormat (toString (decIntPart d)) 0)
  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
-- impl-end

-- proof-start
theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
    problem_spec_floatformat d p (implementation_floatformat d p) := by
  intro d p
  unfold problem_spec_floatformat implementation_floatformat
  by_cases h : decIsWhole d && decide (p ≤ 0) <;>
    simp only [h, Id.run, bind] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec verified True for all 7 attacks + pos_control (swebench_unified.markers.same_spec, lean backend). Command per file: `bash scripts/lean_verify.sh <path>` run concurrently (2 batches of 4).

### Results
- pos_control (gold): EXIT=0; `#print axioms correct_floatformat` => [propext] (clean, no sorry).
- atk_1 (prepatch bug p<0, gold proof): EXIT=1.
- atk_1b (prepatch bug + aggressive adversarial proof: by_cases x2 / simp_all / rfl|omega|decide|aesop): EXIT=1, error 'unsolved goals' at the theorem line. Confirms no cleverer proof closes the prepatch.
- atk_2 (drop integer branch, always general): EXIT=1.
- atk_3 (guard on decIsWhole only, ignore p): EXIT=1.
- atk_4 (swap branch bodies, control-flow-effect): EXIT=1.
- atk_5 (ungrounded-oracle echo: general branch uses numberFormat s 0 instead of p.natAbs): EXIT=1.
- atk_6 (partial-domain: guard decide (p.natAbs = 0) instead of p<=0, drops whole+negative-p integer case): EXIT=1.
- atk_7 (wrong integer-branch place count p.natAbs instead of 0): EXIT=1.

Since NO wrong impl produced a closing clean-axiom proof, there is no verifying-but-wrong impl whose faithful refined patch needed to be materialized/run through the official harness (run_resolve) — step 2's resolve obligation is vacuously satisfied (patches={}).

A-LEG / REFINEMENT AUDIT: refinement.md tags all 5 legs R/I; there are NO A-legs (A-consumed / A-reference) — the focus of this adversarial pass is therefore vacuous here, but confirmed sound. The four opaque callees appear byte-identically in problem_spec_floatformat and implementation_floatformat, cancel in the proof, and no `_prop` property is consumed; axiom_check.py is a correct skip stub (status=skip). #print axioms of the gold theorem shows only [propext] — no injected/free axioms, no sorry. The postcondition is grounded (structural case-split on decIsWhole d and p<=0 selecting two genuinely distinct sub-computations), not an opaque whole-function oracle; discriminating input is whole d with p=0. mapping.md callee<->real-code correspondence (int(d), not m, digit builder, formats.number_format) holds.

VERDICT: SOUND. >=5 (8) distinct same-spec wrong impls attacked (partial-domain atk_6, boundary atk_1/atk_3, control-flow-effect atk_4, ungrounded-oracle echo atk_5, plus atk_2/atk_7), none verifies; prepatch reproduced (fails as required); positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_1b.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation closes correct_floatformat. The postcondition pins result to an EXACT closed-form Option String equality over the four opaque callees (decIsWhole, decIntPart, decimalDigits, numberFormat), so any behaviorally-distinct impl is unprovable — the opaque callees have no reduction rules and the residual goal reduces to distinct opaque values on the discriminating input (whole d, p=0).
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_1b.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a decimal value as text for a requested number of decimal places.

A value is rendered together with a requested number of decimal places `p`
(an integer that may be negative). There are two ways the value can be rendered:

  * as a plain integer — the value's whole part, formatted with no fractional
    digits; or
  * in the general way — the value rounded/padded to the requested number of
    fractional places. This general digit computation is PARTIAL: on some
    values it rejects its inputs and produces no digit text at all, in which
    case the call as a whole yields no rendered text (the failure propagates
    to the caller).

The choice between them depends on the value and on `p`:

  * when the value is a whole number (its fractional part is zero) AND the
    requested number of decimal places is NOT positive (zero or negative), the
    value is rendered as a plain integer — there are no fractional digits worth
    showing, so the whole part alone is emitted;
  * in every other case (the value has a fractional part, or a positive number
    of places was requested), the general rendering is used — producing text
    exactly when the digit computation does.

Both produced digit texts finish by passing through the same locale/grouping
formatting step; only the digit text and the place count fed to it differ
between the two cases.
-/

-- axioms-start
/-- A decimal value, modeled by the data its standard tuple view exposes
(`mapping.md` gives the bijection to the repo's decimal tuple):
* `negative` — whether the value carries a negative sign;
* `digits` — its significant digits, most-significant first;
* `exponent` — the tuple exponent (the value is `digits · 10^exponent`).
Nothing here inspects these fields directly; they carry the value so the
unchanged sub-computations below can act on it. -/
structure DecVal where
  negative : Bool
  digits : List Nat
  exponent : Int

/-- Whether the value is a whole number — its fractional part is zero. (Unchanged
sub-computation; signature only.) -/
opaque decIsWhole : DecVal → Bool

/-- The value's whole (integer) part. (Unchanged sub-computation; signature
only.) -/
opaque decIntPart : DecVal → Int

/-- The general digit text for the value rounded/padded to the given number of
decimal places: `some` of the assembled sign/digits/point string before locale
formatting, or `none` when the digit computation rejects its inputs and
produces no text (that failure propagates to the caller — the call yields no
rendered text). (Unchanged sub-computation; signature only.) -/
opaque decimalDigits : DecVal → Int → Option String

/-- The locale/grouping formatting step applied to a digit string with a given
number of fractional places, under this call's locale/grouping
configuration. (Unchanged sub-computation; signature only.) -/
opaque numberFormat : String → Nat → String
-- axioms-end

-- pure-start
-- No additional pure helpers are needed: the rendering choice is a direct
-- decision over `decIsWhole d` and the sign of `p`, and each branch's outcome
-- is the corresponding unchanged sub-computation.
-- pure-end

-- post-conditions-start
/-- The rendered outcome is exactly the outcome of the selected branch. When the
value is whole and the requested place count is not positive, it is the whole
part formatted with zero fractional places (always produced). Otherwise it is
the general rendering at `|p|` places — produced exactly when the general digit
computation produces text, and absent (the failure propagates) when it does
not. Both produced texts go through the same final formatting step, so the
outcome is fully determined by `d` and `p`. -/
def problem_spec_floatformat (d : DecVal) (p : Int) (result : Option String) : Prop :=
  result =
    (if decIsWhole d && decide (p ≤ 0)
     then some (numberFormat (toString (decIntPart d)) 0)
     else (decimalDigits d p).map (fun s => numberFormat s p.natAbs))
-- post-conditions-end

-- impl-start
def implementation_floatformat (d : DecVal) (p : Int) : Option String := Id.run do
  if decIsWhole d && decide (p ≤ 0) then
    return some (numberFormat (toString (decIntPart d)) 0)
  return (decimalDigits d p).map (fun s => numberFormat s p.natAbs)
-- impl-end

-- proof-start
theorem correct_floatformat : ∀ (d : DecVal) (p : Int),
    problem_spec_floatformat d p (implementation_floatformat d p) := by
  intro d p
  unfold problem_spec_floatformat implementation_floatformat
  by_cases h : decIsWhole d && decide (p ≤ 0) <;>
    simp only [h, Id.run, bind] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec verified True for all 7 attacks + pos_control (swebench_unified.markers.same_spec, lean backend). Command per file: `bash scripts/lean_verify.sh <path>` run concurrently (2 batches of 4).

### Results
- pos_control (gold): EXIT=0; `#print axioms correct_floatformat` => [propext] (clean, no sorry).
- atk_1 (prepatch bug p<0, gold proof): EXIT=1.
- atk_1b (prepatch bug + aggressive adversarial proof: by_cases x2 / simp_all / rfl|omega|decide|aesop): EXIT=1, error 'unsolved goals' at the theorem line. Confirms no cleverer proof closes the prepatch.
- atk_2 (drop integer branch, always general): EXIT=1.
- atk_3 (guard on decIsWhole only, ignore p): EXIT=1.
- atk_4 (swap branch bodies, control-flow-effect): EXIT=1.
- atk_5 (ungrounded-oracle echo: general branch uses numberFormat s 0 instead of p.natAbs): EXIT=1.
- atk_6 (partial-domain: guard decide (p.natAbs = 0) instead of p<=0, drops whole+negative-p integer case): EXIT=1.
- atk_7 (wrong integer-branch place count p.natAbs instead of 0): EXIT=1.

Since NO wrong impl produced a closing clean-axiom proof, there is no verifying-but-wrong impl whose faithful refined patch needed to be materialized/run through the official harness (run_resolve) — step 2's resolve obligation is vacuously satisfied (patches={}).

A-LEG / REFINEMENT AUDIT: refinement.md tags all 5 legs R/I; there are NO A-legs (A-consumed / A-reference) — the focus of this adversarial pass is therefore vacuous here, but confirmed sound. The four opaque callees appear byte-identically in problem_spec_floatformat and implementation_floatformat, cancel in the proof, and no `_prop` property is consumed; axiom_check.py is a correct skip stub (status=skip). #print axioms of the gold theorem shows only [propext] — no injected/free axioms, no sorry. The postcondition is grounded (structural case-split on decIsWhole d and p<=0 selecting two genuinely distinct sub-computations), not an opaque whole-function oracle; discriminating input is whole d with p=0. mapping.md callee<->real-code correspondence (int(d), not m, digit builder, formats.number_format) holds.

VERDICT: SOUND. >=5 (8) distinct same-spec wrong impls attacked (partial-domain atk_6, boundary atk_1/atk_3, control-flow-effect atk_4, ungrounded-oracle echo atk_5, plus atk_2/atk_7), none verifies; prepatch reproduced (fails as required); positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: django__django-16485 lean. Verified mechanics: Solution.lean compiles under lean_verify.sh (exit 0) and `#print axioms correct_floatformat` = [propext] only — no sorryAx, proof is genuine. same_spec(sol,sol) is True; the file self-verifies. (Note: meta.json region_hashes differ from freshly-computed hashes, consistent with a hashing-version delta rather than tampering — spec self-consistency holds.)

Faithfulness analysis: `problem_spec_floatformat` and `implementation_floatformat` carry BYTE-IDENTICAL opaque expressions on both branches (`if decIsWhole d && decide (p ≤ 0) then some (numberFormat (toString (decIntPart d)) 0) else (decimalDigits d p).map (fun s => numberFormat s p.natAbs)`); the proof is a case-split + rfl. Thus the spec cannot be too-strong relative to the impl — it IS the impl. Faithfulness reduces to: does the impl, with opaque callees interpreted as the real repo callees, match the real POST-patch floatformat?

Three concrete claims validated on a worktree at base_commit 39f83765 + patch (guard `p < 0` -> `p <= 0`):
1. Branch guard `decIsWhole d && p ≤ 0` == `not m and p <= 0`: confirmed across whole/non-whole × neg/zero/pos p. e.g. floatformat('0E-10',-1) & ('0.000',-5) take INT branch (whole zero, p<=0); ('0.5',0),('0.001',-1),('1.5',0) take GEN; all match modeled branch selection.
2. INT branch total (always `some`): int(d) already succeeded pre-guard; integer branch always returns. Confirmed (('0.00',0)->'0', ('5',-1)->'5', ('-5',-3)->'-5').
3. Observable mapping raise<->none, return<->some: the noted post-patch partiality points floatformat('0.000',1) and ('0E-10',1) DO raise ValueError('valid range for prec is [1, MAX_PREC]') post-patch (model=none); all returning inputs map to some. The former G-PANEL-2 defect (fabricating a total string) is genuinely fixed — the Option observable now matches reality.

FAIL_TO_PASS discriminator (whole d, p=0, e.g. '0.00',0 -> '0') is captured. Parse-failure inputs (bad Decimal, bad arg suffix, NaN/Inf) lie outside the modeled post-parse domain (d:DecVal, p:Int) — a legitimate modeling boundary since the patch touches only the post-parse branch guard; not a divergence. No input found where the modeled function disagrees with the real post-patch callee. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction attacker. Gold edit = one-char guard change `if not m and p < 0:` -> `if not m and p <= 0:` (defaultfilters.py:171), routing a whole value with p==0 to the integer branch instead of crashing in Decimal.quantize(Context(prec=0)).

Baseline of allowed knowledge (public problem_statement, hints_text EXCLUDED): the problem_statement itself gives the exact discriminating inputs floatformat('0.00',0) and floatformat(Decimal('0.00'),0) (= whole value, p==0) and states both raise 'ValueError: valid range for prec is [1, MAX_PREC]' and should not. So the discriminating input (whole & p=0) and the desired non-crashing behavior are fully disclosed publicly; the gold edit is essentially determined by public info alone.

Spec view verified programmatically: swebench_unified.markers.spec_view(Solution.lean, LeanBackend.language) and same_spec(Solution.lean, Solution_prepatch.lean)=True. The spec region (imports/docstring/axioms/pure/post-conditions) is frozen byte-identical between post-patch and prepatch; the impl and proof regions are ELIDED ('implementation elided'/'proof elided'), so the attacker never sees the `p < 0` prepatch guard or the diff.

Lexical screen over the spec view is clean: no `p < 0`, no `< 0`, no `p<0`, no prepatch/patch/regression/bug/crash/ValueError/error/fix/prec/quantize/0.00/0E-10 tokens. The only substring hits are innocent: 'diff' inside 'differ' and 'before' inside 'before locale'. The docstring describes the correct total post-fix behavior ('whole number ... AND the requested number of decimal places is NOT positive (zero or negative)' -> integer branch) and the post-condition uses `decide (p <= 0)`.

A spec necessarily describes correct (post-fix) behavior; describing the `p <= 0` boundary and the two-branch structure does not reconstruct the gold edit beyond what problem_statement already gives, since the public statement already pins the discriminating input (whole & p=0) and the required outcome (no crash). The spec never reveals the OLD `p < 0` guard or that a boundary was moved. The partiality/`none` modeling concerns post-patch residual raises (a faithfulness matter), not the guard change.

Conclusion: nothing in the spec view leaks the gold edit beyond the public problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
