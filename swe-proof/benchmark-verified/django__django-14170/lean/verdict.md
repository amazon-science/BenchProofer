# P2 adversarial audit — django__django-14170

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,12 +90,8 @@
     Int × Int := Id.run do
   let mut first : Int := 0
   let mut second : Int := 0
-  if isoYear then
-    first := isoYearStart value
-    second := isoYearStart (value + 1) - 1
-  else
-    first := gregJan1 value
-    second := gregDec31 value
+  first := gregJan1 value
+  second := gregDec31 value
   return (first, second)
 -- impl-end
 
@@ -119,7 +115,12 @@
       problem_spec_yearBoundsDate value isoYear
         (implementation_yearBoundsDate value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
 
 -- proof-start
@@ -128,5 +129,10 @@
       problem_spec_yearBoundsDatetime value isoYear
         (implementation_yearBoundsDatetime value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -104,12 +104,8 @@
     Int × Int := Id.run do
   let mut first : Int := 0
   let mut second : Int := 0
-  if isoYear then
-    first := isoYearStart value * usPerDay
-    second := isoYearStart (value + 1) * usPerDay - 1
-  else
-    first := gregJan1 value * usPerDay
-    second := gregJan1 (value + 1) * usPerDay - 1
+  first := gregJan1 value * usPerDay
+  second := gregJan1 (value + 1) * usPerDay - 1
   return (first, second)
 -- impl-end
 
@@ -119,7 +115,12 @@
       problem_spec_yearBoundsDate value isoYear
         (implementation_yearBoundsDate value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
 
 -- proof-start
@@ -128,5 +129,10 @@
       problem_spec_yearBoundsDatetime value isoYear
         (implementation_yearBoundsDatetime value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -90,6 +90,8 @@
     Int × Int := Id.run do
   let mut first : Int := 0
   let mut second : Int := 0
+  if value = 2020 then
+    return (0, 0)
   if isoYear then
     first := isoYearStart value
     second := isoYearStart (value + 1) - 1
@@ -119,7 +121,12 @@
       problem_spec_yearBoundsDate value isoYear
         (implementation_yearBoundsDate value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
 
 -- proof-start
@@ -128,5 +135,10 @@
       problem_spec_yearBoundsDatetime value isoYear
         (implementation_yearBoundsDatetime value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,10 +92,10 @@
   let mut second : Int := 0
   if isoYear then
     first := isoYearStart value
-    second := isoYearStart (value + 1) - 1
+    second := isoYearStart (value + 1)
   else
     first := gregJan1 value
-    second := gregDec31 value
+    second := gregDec31 value + 1
   return (first, second)
 -- impl-end
 
@@ -119,7 +119,12 @@
       problem_spec_yearBoundsDate value isoYear
         (implementation_yearBoundsDate value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
 
 -- proof-start
@@ -128,5 +133,10 @@
       problem_spec_yearBoundsDatetime value isoYear
         (implementation_yearBoundsDatetime value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,11 +91,11 @@
   let mut first : Int := 0
   let mut second : Int := 0
   if isoYear then
+    first := gregJan1 value
+    second := gregDec31 value
+  else
     first := isoYearStart value
     second := isoYearStart (value + 1) - 1
-  else
-    first := gregJan1 value
-    second := gregDec31 value
   return (first, second)
 -- impl-end
 
@@ -119,7 +119,12 @@
       problem_spec_yearBoundsDate value isoYear
         (implementation_yearBoundsDate value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
 
 -- proof-start
@@ -128,5 +133,10 @@
       problem_spec_yearBoundsDatetime value isoYear
         (implementation_yearBoundsDatetime value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,10 +106,10 @@
   let mut second : Int := 0
   if isoYear then
     first := isoYearStart value * usPerDay
-    second := isoYearStart (value + 1) * usPerDay - 1
+    second := isoYearStart (value + 1) * usPerDay
   else
     first := gregJan1 value * usPerDay
-    second := gregJan1 (value + 1) * usPerDay - 1
+    second := gregJan1 (value + 1) * usPerDay
   return (first, second)
 -- impl-end
 
@@ -119,7 +119,12 @@
       problem_spec_yearBoundsDate value isoYear
         (implementation_yearBoundsDate value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
 
 -- proof-start
@@ -128,5 +133,10 @@
       problem_spec_yearBoundsDatetime value isoYear
         (implementation_yearBoundsDatetime value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -94,8 +94,8 @@
     first := isoYearStart value
     second := isoYearStart (value + 1) - 1
   else
-    first := gregJan1 value
-    second := gregDec31 value
+    first := gregDec31 value
+    second := gregJan1 value
   return (first, second)
 -- impl-end
 
@@ -119,7 +119,12 @@
       problem_spec_yearBoundsDate value isoYear
         (implementation_yearBoundsDate value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
 
 -- proof-start
@@ -128,5 +133,10 @@
       problem_spec_yearBoundsDatetime value isoYear
         (implementation_yearBoundsDatetime value isoYear) := by
   intro value isoYear
-  cases isoYear <;> exact ⟨rfl, rfl⟩
+  cases isoYear <;>
+    first
+      | exact ⟨rfl, rfl⟩
+      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
+      | (refine ⟨?_, ?_⟩ <;> omega)
+      | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Lower/upper bounds for a year-based range query on date and timestamp columns.

A "year lookup" turns a query of the form "the year of this column equals (or is
compared against) `value`" into an inclusive range test `column BETWEEN lower AND
upper`, so that an ordinary index on the column can serve the query without
computing a per-row year extraction.

Two notions of "year" are supported, selected by a boolean:

* the ordinary **calendar year**: it runs from January 1st of `value` through
  December 31st of `value`; and
* the **ISO-8601 week-numbering year**: it runs from the Monday that begins ISO
  week 1 of `value` through the day before the Monday that begins ISO week 1 of
  `value + 1`. (ISO years do not line up with calendar years — an ISO year may
  start in late December of the previous calendar year or in early January.)

Dates are modeled by their proleptic-Gregorian ordinal day number (day 1 =
0001-01-01); timestamps by the microsecond count since that same epoch. For a
date column the bounds are the first and last *day* of the chosen year. For a
timestamp column the lower bound is midnight of the first day and the upper
bound is the last microsecond (`23:59:59.999999`) of the last day — i.e. one
microsecond before midnight that begins the next year.

The selecting boolean is supplied as an input; computing it, the column-type
dispatch, and the serialization of each bound are handled by the caller and are
not part of this specification. Behavior is stated abstractly as an
input→output relation; implementation and proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both the Gregorian and the
-- ISO-8601 calendar day-number computations are spelled out concretely below as
-- arithmetic on the year, and validated against the standard-library calendar by
-- the differential conformance check (an A-reference, not a consumed axiom).
-- axioms-end

-- pure-start
/-- Microseconds in one day. -/
def usPerDay : Int := 86400000000

/-- Proleptic-Gregorian ordinal of January 1st of `y` (day 1 = 0001-01-01),
i.e. the count of days from the epoch to that date, plus one. Spelled out as the
standard day-count: 365 days per prior year, plus the leap-day corrections (one
per 4 years, minus one per 100 years, plus one per 400 years). -/
def gregJan1 (y : Int) : Int :=
  1 + 365 * (y - 1) + (y - 1) / 4 - (y - 1) / 100 + (y - 1) / 400

/-- Ordinal of December 31st of `y`: the day before January 1st of `y + 1`. -/
def gregDec31 (y : Int) : Int := gregJan1 (y + 1) - 1

/-- Ordinal of the Monday that begins ISO week 1 of `y`. ISO week 1 is the week
containing January 4th, and ISO weeks start on Monday; ordinal 1 (0001-01-01) is
a Monday, so the Monday of the week containing ordinal `o` is `o - ((o - 1) % 7)`.
Applied to January 4th (`gregJan1 y + 3`) this yields the ISO year's first day. -/
def isoYearStart (y : Int) : Int :=
  let jan4 := gregJan1 y + 3
  jan4 - ((jan4 - 1) % 7)
-- pure-end

-- post-conditions-start
/-- Inclusive `[lower, upper]` day-ordinal bounds for a year lookup on a date
column. When `isoYear` is `false` the bounds span the calendar year `value`
(Jan 1st … Dec 31st); when `true` they span the ISO-8601 week-numbering year
`value` (its first Monday … the day before the next ISO year's first Monday). -/
def problem_spec_yearBoundsDate (value : Int) (isoYear : Bool)
    (result : Int × Int) : Prop :=
  result.1 = (if isoYear then isoYearStart value else gregJan1 value) ∧
  result.2 = (if isoYear then isoYearStart (value + 1) - 1 else gregDec31 value)
-- post-conditions-end

-- post-conditions-start
/-- Inclusive `[lower, upper]` microsecond bounds for a year lookup on a
timestamp column. The lower bound is midnight (`* usPerDay`) of the chosen year's
first day; the upper bound is one microsecond before midnight that begins the
next year — i.e. `23:59:59.999999` of the chosen year's last day. The choice of
year (calendar vs ISO-8601 week-numbering) is governed by `isoYear` exactly as
for the date variant. -/
def problem_spec_yearBoundsDatetime (value : Int) (isoYear : Bool)
    (result : Int × Int) : Prop :=
  result.1 = (if isoYear then isoYearStart value else gregJan1 value) * usPerDay ∧
  result.2 = (if isoYear then isoYearStart (value + 1) else gregJan1 (value + 1)) * usPerDay - 1
-- post-conditions-end

-- impl-start
def implementation_yearBoundsDate (value : Int) (isoYear : Bool) :
    Int × Int := Id.run do
  let mut first : Int := 0
  let mut second : Int := 0
  if isoYear then
    first := isoYearStart value
    second := isoYearStart (value + 1) - 1
  else
    first := gregJan1 value
    second := gregDec31 value
  return (first, second)
-- impl-end

-- impl-start
def implementation_yearBoundsDatetime (value : Int) (isoYear : Bool) :
    Int × Int := Id.run do
  let mut first : Int := 0
  let mut second : Int := 0
  if isoYear then
    first := isoYearStart value * usPerDay
    second := isoYearStart (value + 1) * usPerDay - 1
  else
    first := gregJan1 value * usPerDay
    second := gregJan1 (value + 1) * usPerDay - 1
  return (first, second)
-- impl-end

-- proof-start
theorem correct_yearBoundsDate :
    ∀ (value : Int) (isoYear : Bool),
      problem_spec_yearBoundsDate value isoYear
        (implementation_yearBoundsDate value isoYear) := by
  intro value isoYear
  cases isoYear <;>
    first
      | exact ⟨rfl, rfl⟩
      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
      | (refine ⟨?_, ?_⟩ <;> omega)
      | decide
-- proof-end

-- proof-start
theorem correct_yearBoundsDatetime :
    ∀ (value : Int) (isoYear : Bool),
      problem_spec_yearBoundsDatetime value isoYear
        (implementation_yearBoundsDatetime value isoYear) := by
  intro value isoYear
  cases isoYear <;>
    first
      | exact ⟨rfl, rfl⟩
      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
      | (refine ⟨?_, ?_⟩ <;> omega)
      | decide
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: both post-conditions are TOTAL EXACT functional equalities — problem_spec_yearBoundsDate pins result.1 = (if isoYear then isoYearStart value else gregJan1 value) and result.2 = (if isoYear then isoYearStart(value+1)-1 else gregDec31 value); problem_spec_yearBoundsDatetime pins both µs bounds identically. Every output component is fully determined by (value, isoYear) with no domain side-condition, so any behavioral deviation on any input is unprovable.

SAME_SPEC: all 8 files (pos_control + atk_1..7) return True via swebench_unified.markers.same_spec (header lines 1-87 = spec/pure/post kept byte-identical; only impl+proof regions edited).

COMMANDS (project root; run concurrently ≤4): `bash scripts/lean_verify.sh <file>`.
### Results
  pos_control.lean (exact gold impl) -> exit 0 (VERIFIES). `#print axioms` on both correct_* => 'does not depend on any axioms' (clean, no sorry).
  atk_1.lean (prepatch date bug: date ignores isoYear, always calendar) -> exit 1 (does NOT close).
  atk_2.lean (prepatch datetime bug: datetime ignores isoYear) -> exit 1.
  atk_3.lean (partial-domain: date returns (0,0) at value=2020, else gold) -> exit 1.
  atk_4.lean (boundary off-by-one: date iso second missing -1, calendar dec31 +1) -> exit 1.
  atk_5.lean (control-flow branch swap: iso branch uses calendar bounds, else uses ISO) -> exit 1.
  atk_6.lean (datetime upper drops -1: midnight of next year instead of last µs) -> exit 1.
  atk_7.lean (first/second swapped in date else branch) -> exit 1.
No wrong impl closed => no impl with a closing clean-axiom proof => no faithful patch to materialize/resolve. Every attack was verified; none breaks the spec.

prepatch_reproduced=true: atk_1 and atk_2 are byte-faithful re-encodings of the bundle's Solution_prepatch.lean / Solution_prepatch_2.lean impl regions (isoYear ignored), both correctly fail to close under the strong best-effort proof.

A-LEG / refinement audit (the focus): refinement.md declares NO axioms (axioms region is a comment stub; G-AX is a legitimate skip — no consumed axiom = no kind-3). The only introduced behavior (ISO-8601 branch) is modeled DEEPLY in `pure` via gregJan1/gregDec31/isoYearStart and tagged A-reference. Verified the A-reference correspondence directly in /tmp against the REAL stdlib callees over 200,000 random years in [2,9998]: gregJan1 y == date(y,1,1).toordinal(), gregDec31 y == date(y,12,31).toordinal(), isoYearStart y == date.fromisocalendar(y,1,1).toordinal() — 0 disagreements. This matches conformance_check.py (SEED=20210323, N_RANDOM=120000, both branches, both callees). Every refinement.md leg is R (adapt_*field_value=str / make_aware order-preserving glue, caller isinstance plumbing), A-reference (the three calendar models), or I (branch selector). No kind-3 legs. Correspondence to real callees holds.

SOUND after 7 distinct attacks (partial-domain, boundary, control-flow-effect, prepatch, arg-swap) run and verified; none produced a closing clean-axiom wrong impl.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
Lower/upper bounds for a year-based range query on date and timestamp columns.

A "year lookup" turns a query of the form "the year of this column equals (or is
compared against) `value`" into an inclusive range test `column BETWEEN lower AND
upper`, so that an ordinary index on the column can serve the query without
computing a per-row year extraction.

Two notions of "year" are supported, selected by a boolean:

* the ordinary **calendar year**: it runs from January 1st of `value` through
  December 31st of `value`; and
* the **ISO-8601 week-numbering year**: it runs from the Monday that begins ISO
  week 1 of `value` through the day before the Monday that begins ISO week 1 of
  `value + 1`. (ISO years do not line up with calendar years — an ISO year may
  start in late December of the previous calendar year or in early January.)

Dates are modeled by their proleptic-Gregorian ordinal day number (day 1 =
0001-01-01); timestamps by the microsecond count since that same epoch. For a
date column the bounds are the first and last *day* of the chosen year. For a
timestamp column the lower bound is midnight of the first day and the upper
bound is the last microsecond (`23:59:59.999999`) of the last day — i.e. one
microsecond before midnight that begins the next year.

The selecting boolean is supplied as an input; computing it, the column-type
dispatch, and the serialization of each bound are handled by the caller and are
not part of this specification. Behavior is stated abstractly as an
input→output relation; implementation and proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: both the Gregorian and the
-- ISO-8601 calendar day-number computations are spelled out concretely below as
-- arithmetic on the year, and validated against the standard-library calendar by
-- the differential conformance check (an A-reference, not a consumed axiom).
-- axioms-end

-- pure-start
/-- Microseconds in one day. -/
def usPerDay : Int := 86400000000

/-- Proleptic-Gregorian ordinal of January 1st of `y` (day 1 = 0001-01-01),
i.e. the count of days from the epoch to that date, plus one. Spelled out as the
standard day-count: 365 days per prior year, plus the leap-day corrections (one
per 4 years, minus one per 100 years, plus one per 400 years). -/
def gregJan1 (y : Int) : Int :=
  1 + 365 * (y - 1) + (y - 1) / 4 - (y - 1) / 100 + (y - 1) / 400

/-- Ordinal of December 31st of `y`: the day before January 1st of `y + 1`. -/
def gregDec31 (y : Int) : Int := gregJan1 (y + 1) - 1

/-- Ordinal of the Monday that begins ISO week 1 of `y`. ISO week 1 is the week
containing January 4th, and ISO weeks start on Monday; ordinal 1 (0001-01-01) is
a Monday, so the Monday of the week containing ordinal `o` is `o - ((o - 1) % 7)`.
Applied to January 4th (`gregJan1 y + 3`) this yields the ISO year's first day. -/
def isoYearStart (y : Int) : Int :=
  let jan4 := gregJan1 y + 3
  jan4 - ((jan4 - 1) % 7)
-- pure-end

-- post-conditions-start
/-- Inclusive `[lower, upper]` day-ordinal bounds for a year lookup on a date
column. When `isoYear` is `false` the bounds span the calendar year `value`
(Jan 1st … Dec 31st); when `true` they span the ISO-8601 week-numbering year
`value` (its first Monday … the day before the next ISO year's first Monday). -/
def problem_spec_yearBoundsDate (value : Int) (isoYear : Bool)
    (result : Int × Int) : Prop :=
  result.1 = (if isoYear then isoYearStart value else gregJan1 value) ∧
  result.2 = (if isoYear then isoYearStart (value + 1) - 1 else gregDec31 value)
-- post-conditions-end

-- post-conditions-start
/-- Inclusive `[lower, upper]` microsecond bounds for a year lookup on a
timestamp column. The lower bound is midnight (`* usPerDay`) of the chosen year's
first day; the upper bound is one microsecond before midnight that begins the
next year — i.e. `23:59:59.999999` of the chosen year's last day. The choice of
year (calendar vs ISO-8601 week-numbering) is governed by `isoYear` exactly as
for the date variant. -/
def problem_spec_yearBoundsDatetime (value : Int) (isoYear : Bool)
    (result : Int × Int) : Prop :=
  result.1 = (if isoYear then isoYearStart value else gregJan1 value) * usPerDay ∧
  result.2 = (if isoYear then isoYearStart (value + 1) else gregJan1 (value + 1)) * usPerDay - 1
-- post-conditions-end

-- impl-start
def implementation_yearBoundsDate (value : Int) (isoYear : Bool) :
    Int × Int := Id.run do
  let mut first : Int := 0
  let mut second : Int := 0
  if isoYear then
    first := isoYearStart value
    second := isoYearStart (value + 1) - 1
  else
    first := gregJan1 value
    second := gregDec31 value
  return (first, second)
-- impl-end

-- impl-start
def implementation_yearBoundsDatetime (value : Int) (isoYear : Bool) :
    Int × Int := Id.run do
  let mut first : Int := 0
  let mut second : Int := 0
  if isoYear then
    first := isoYearStart value * usPerDay
    second := isoYearStart (value + 1) * usPerDay - 1
  else
    first := gregJan1 value * usPerDay
    second := gregJan1 (value + 1) * usPerDay - 1
  return (first, second)
-- impl-end

-- proof-start
theorem correct_yearBoundsDate :
    ∀ (value : Int) (isoYear : Bool),
      problem_spec_yearBoundsDate value isoYear
        (implementation_yearBoundsDate value isoYear) := by
  intro value isoYear
  cases isoYear <;>
    first
      | exact ⟨rfl, rfl⟩
      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDate, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
      | (refine ⟨?_, ?_⟩ <;> omega)
      | decide
-- proof-end

-- proof-start
theorem correct_yearBoundsDatetime :
    ∀ (value : Int) (isoYear : Bool),
      problem_spec_yearBoundsDatetime value isoYear
        (implementation_yearBoundsDatetime value isoYear) := by
  intro value isoYear
  cases isoYear <;>
    first
      | exact ⟨rfl, rfl⟩
      | (refine ⟨?_, ?_⟩ <;> simp [implementation_yearBoundsDatetime, gregJan1, gregDec31, isoYearStart, usPerDay] <;> ring)
      | (refine ⟨?_, ?_⟩ <;> omega)
      | decide
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec structure: both post-conditions are TOTAL EXACT functional equalities — problem_spec_yearBoundsDate pins result.1 = (if isoYear then isoYearStart value else gregJan1 value) and result.2 = (if isoYear then isoYearStart(value+1)-1 else gregDec31 value); problem_spec_yearBoundsDatetime pins both µs bounds identically. Every output component is fully determined by (value, isoYear) with no domain side-condition, so any behavioral deviation on any input is unprovable.

SAME_SPEC: all 8 files (pos_control + atk_1..7) return True via swebench_unified.markers.same_spec (header lines 1-87 = spec/pure/post kept byte-identical; only impl+proof regions edited).

COMMANDS (project root; run concurrently ≤4): `bash scripts/lean_verify.sh <file>`.
### Results
  pos_control.lean (exact gold impl) -> exit 0 (VERIFIES). `#print axioms` on both correct_* => 'does not depend on any axioms' (clean, no sorry).
  atk_1.lean (prepatch date bug: date ignores isoYear, always calendar) -> exit 1 (does NOT close).
  atk_2.lean (prepatch datetime bug: datetime ignores isoYear) -> exit 1.
  atk_3.lean (partial-domain: date returns (0,0) at value=2020, else gold) -> exit 1.
  atk_4.lean (boundary off-by-one: date iso second missing -1, calendar dec31 +1) -> exit 1.
  atk_5.lean (control-flow branch swap: iso branch uses calendar bounds, else uses ISO) -> exit 1.
  atk_6.lean (datetime upper drops -1: midnight of next year instead of last µs) -> exit 1.
  atk_7.lean (first/second swapped in date else branch) -> exit 1.
No wrong impl closed => no impl with a closing clean-axiom proof => no faithful patch to materialize/resolve. Every attack was verified; none breaks the spec.

prepatch_reproduced=true: atk_1 and atk_2 are byte-faithful re-encodings of the bundle's Solution_prepatch.lean / Solution_prepatch_2.lean impl regions (isoYear ignored), both correctly fail to close under the strong best-effort proof.

A-LEG / refinement audit (the focus): refinement.md declares NO axioms (axioms region is a comment stub; G-AX is a legitimate skip — no consumed axiom = no kind-3). The only introduced behavior (ISO-8601 branch) is modeled DEEPLY in `pure` via gregJan1/gregDec31/isoYearStart and tagged A-reference. Verified the A-reference correspondence directly in /tmp against the REAL stdlib callees over 200,000 random years in [2,9998]: gregJan1 y == date(y,1,1).toordinal(), gregDec31 y == date(y,12,31).toordinal(), isoYearStart y == date.fromisocalendar(y,1,1).toordinal() — 0 disagreements. This matches conformance_check.py (SEED=20210323, N_RANDOM=120000, both branches, both callees). Every refinement.md leg is R (adapt_*field_value=str / make_aware order-preserving glue, caller isinstance plumbing), A-reference (the three calendar models), or I (branch selector). No kind-3 legs. Correspondence to real callees holds.

SOUND after 7 distinct attacks (partial-domain, boundary, control-flow-effect, prepatch, arg-swap) run and verified; none produced a closing clean-axiom wrong impl.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) analysis for django__django-14170 lean bundle.

Modeled functions: problem_spec_yearBoundsDate / problem_spec_yearBoundsDatetime, backed by pure helpers gregJan1/gregDec31/isoYearStart. Real callees: year_lookup_bounds_for_date_field / year_lookup_bounds_for_datetime_field (django/db/backends/base/operations.py, post-patch), which delegate to stdlib datetime.date/datetime + date.fromisocalendar.

Differential over the FULL defined domain (verified with real Python3 datetime, not the pinned G-CONF seed):
 - gregJan1(y) == date(y,1,1).toordinal() for all y in [1,9999]: 0 mismatches.
 - gregDec31(y) == date(y,12,31).toordinal(): 0 mismatches.
 - isoYearStart(y) == date.fromisocalendar(y,1,1).toordinal() wherever fromisocalendar is defined: 0 mismatches.
 - End-to-end both spec functions (both iso_year branches, both bounds, incl. datetime us arithmetic *86400000000 and the -1 last-microsecond) reproduce the exact post-patch outputs on every value in [1,9998], and calendar branch at boundary year 9999. Total mismatches across all four (date/datetime x cal/iso) = 0.

Spec strength: the spec is stated total over Int with no domain side-condition, whereas the real stdlib constructors RAISE outside year 1..9999 (1..9998 for the ISO branch, which evaluates value+1). This is a conservative total extension: on every input where the real callee returns a value, the model returns the identical value; outside the range the callee returns no value at all (throws), so there is no returned-value disagreement. This is not spec drift and not spec-too-strong for the postcondition (a stronger postcondition would be one the impl fails to meet; here impl==spec by rfl and both match the repo). mapping.md documents the extension and G-CONF differentials cover the defined range.

Byte-identity: same_spec(Solution.lean, Solution_prepatch.lean)=True and same_spec(Solution.lean, Solution_prepatch_2.lean)=True under LeanBackend tables (spec view identical).

Proof integrity: scripts/lean_verify.sh exit 0; #print axioms reports BOTH correct_yearBoundsDate and correct_yearBoundsDatetime 'does not depend on any axioms' -- no sorryAx, real proof.

No diverging input exists within the real callees' defined domain. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 leakage judgment for django__django-14170 (lean). Baseline of what is already PUBLIC in problem_statement: the title 'Query optimization in YearLookup breaks filtering by "__iso_year"' plus the body explicitly state that the YearLookup BETWEEN optimization wrongly applies calendar-year bounds (2020-01-01 AND 2020-12-31) to __iso_year lookups, breaking ExtractIsoYear. So the core semantic content of the gold fix — that ISO-8601 week-numbering years require different range bounds than calendar years in year-lookup queries — is already fully disclosed to the solver.

Spec view (docstring + problem_spec_yearBoundsDate/Datetime + the pure calendar models gregJan1/gregDec31/isoYearStart) states the CORRECT input->output relation: calendar year = Jan1..Dec31, ISO year = first Monday of ISO week 1 .. day before next ISO year's first Monday, selected by an input boolean. This is the spec's legitimate job (encode correct behavior); every fact it exposes is a direct restatement of what the problem statement already reveals. The deep gregJan1/isoYearStart definitions are reference calendar arithmetic (A-references validated by G-CONF), not gold-edit localization.

Localization is NOT leaked beyond the problem statement:
- Spec identifiers are problem_spec_yearBoundsDate/Datetime, gregJan1, isoYearStart, usPerDay — none embed the patched repo symbols (year_lookup_bounds_for_date_field, year_lookup_bounds_for_datetime_field, IRegex, adapt_ipaddressfield_value).
- No patched file path (django/db/backends/base/operations.py, django/db/models/lookups.py), no diff markers, no dotted module path in the view.
- No bug/fix/regression narration in comments (mechanical narration screen clean).
- The isoYear flag, the isinstance(self.lhs, ExtractIsoYear) computation, and the column-type dispatch are explicitly declared OUT OF SCOPE ('supplied by the caller ... not part of this specification'), so the spec does not reveal the gold's caller-plumbing mechanism. A solver must still locate the two operations.py callees and the lookups.py caller themselves.

Mechanical G-LEAK screen re-run independently: passed=True, hard_failures=[]; recorded meta G-LEAK status=pass ('spec view clean'). same_spec region hashes recorded (G-HYGIENE pass). Not a relaxed bundle. Verdict: NO-LEAKAGE — the spec encodes correct behavior without disclosing the gold edit's location beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
