# P2 adversarial audit — django__django-16429

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     hour := d.hour,
     minute := d.minute,
     second := d.second,
-    offset := d.offset
+    offset := none
   }
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -95,7 +95,7 @@
     hour := d.hour,
     minute := d.minute,
     second := d.second,
-    offset := d.offset
+    offset := some 0
   }
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
     (d : Instant) (years months : Int) : Instant := Id.run do
   let mut anchorYear := d.year + years
   let mut anchorMonth := d.month + months
-  if anchorMonth > 12 then
+  if anchorMonth ≥ 12 then
     anchorMonth := anchorMonth - 12
     anchorYear := anchorYear + 1
   return {
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -87,7 +87,7 @@
   let mut anchorMonth := d.month + months
   if anchorMonth > 12 then
     anchorMonth := anchorMonth - 12
-    anchorYear := anchorYear + 1
+    anchorYear := anchorYear
   return {
     year := anchorYear,
     month := anchorMonth,
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,7 +91,7 @@
   return {
     year := anchorYear,
     month := anchorMonth,
-    day := min (monthLength anchorMonth) d.day,
+    day := d.day,
     hour := d.hour,
     minute := d.minute,
     second := d.second,
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -92,7 +92,7 @@
     year := anchorYear,
     month := anchorMonth,
     day := min (monthLength anchorMonth) d.day,
-    hour := d.hour,
+    hour := d.minute,
     minute := d.minute,
     second := d.second,
     offset := d.offset
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing a shifted calendar reference point.

Given a starting instant and a whole number of years and months, this builds a
reference instant that lies exactly that many years and months after the start.
The reference instant is used downstream to measure the leftover sub-month part
of an elapsed interval, so it must be directly comparable with the other
instants involved in that measurement.

The reference instant is assembled field-by-field from the starting instant:

  * its calendar date is the start's year/month advanced by the requested
    years and months (rolling the month past December into the next year);
  * its day-of-month is the start's day, clamped down to the last valid day of
    the resulting month (so e.g. a 31st never lands in a 30-day month);
  * its clock fields (hour, minute, second) are copied unchanged from the start.

An instant also carries a timezone designation (a constant offset from UTC, or
none when the instant is timezone-naive). Because the reference instant is later
compared against another instant, it must carry the SAME timezone designation as
the starting instant — a naive start yields a naive reference, and an instant at
a given offset yields a reference at that same offset. An instant whose timezone
designation failed to match its peers could not be compared with them at all.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The reference
-- instant is assembled purely from the starting instant's own fields, so its
-- construction is modeled DEEPLY (structure assembly + clamping) rather than
-- through any `opaque`/`axiom` callee contract. The table of month lengths is a
-- constant table, modeled directly in the `pure` region. No callee property is
-- needed by the proof.
-- axioms-end

-- pure-start
/-- An instant: a calendar date, clock fields, and an optional timezone
designation (a constant UTC offset in seconds; `none` = timezone-naive). -/
structure Instant where
  year : Int
  month : Int
  day : Int
  hour : Int
  minute : Int
  second : Int
  offset : Option Int
deriving Repr

/-- Lengths of the twelve calendar months (non-leap reference table). Indexed by
month number 1‥12. -/
def monthLengths : List Int := [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

/-- The length of month `m` (1‥12) from the reference table; out-of-range months
fall back to 31 (never exercised under the precondition `1 ≤ m ≤ 12`). -/
def monthLength (m : Int) : Int := monthLengths.getD (m.toNat - 1) 31
-- pure-end

-- post-conditions-start
/-- The reference instant lies exactly `years` years and `months` months after
`d`. Every component is pinned to its input (frame discipline):

  * year/month are `d`'s advanced by the request, rolling a month past December
    into the next year;
  * the day is `d`'s day clamped to the last valid day of the resulting month;
  * the clock fields equal `d`'s clock fields;
  * the timezone designation equals `d`'s, so the reference is comparable with
    the instants it will be measured against. -/
def problem_spec_anchor
    (d : Instant) (years months : Int) (result : Instant) : Prop :=
  let rawMonth := d.month + months
  let rolled := rawMonth > 12
  result.year = (if rolled then d.year + years + 1 else d.year + years) ∧
  result.month = (if rolled then rawMonth - 12 else rawMonth) ∧
  result.day = min (monthLength result.month) d.day ∧
  result.hour = d.hour ∧
  result.minute = d.minute ∧
  result.second = d.second ∧
  result.offset = d.offset
-- post-conditions-end

-- impl-start
def implementation_anchor
    (d : Instant) (years months : Int) : Instant := Id.run do
  let mut anchorYear := d.year + years
  let mut anchorMonth := d.month + months
  if anchorMonth > 12 then
    anchorMonth := anchorMonth - 12
    anchorYear := anchorYear + 1
  return {
    year := anchorYear,
    month := anchorMonth,
    day := min (monthLength anchorMonth) d.day,
    hour := d.hour,
    minute := d.minute,
    second := d.second,
    offset := d.offset
  }
-- impl-end

-- proof-start
theorem correct_anchor :
    ∀ (d : Instant) (years months : Int),
      1 ≤ d.month → d.month ≤ 12 → 0 ≤ months → months ≤ 11 →
      problem_spec_anchor d years months
        (implementation_anchor d years months) := by
  intro d years months _ _ _ _
  unfold problem_spec_anchor implementation_anchor
  simp only [Id.run, bind, pure]
  by_cases h : d.month + months > 12
  · simp only [h, if_true]; trivial
  · simp only [h, if_false]; trivial
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_anchor pins ALL 7 output fields (year/month/day/hour/minute/second/offset) to exact functions of the inputs over the full precondition domain (1<=d.month<=12, 0<=months<=11; offset/day/year/hour unconstrained beyond equality to the derived value). Any impl deviating on any in-domain input yields a FALSE theorem -> unprovable. No axioms/opaque callees: refinement.md axioms-region states no callee contract consumed; all 12 legs are R/I (no kind-3, no A-consumed/A-reference). A-legs vacuous. mapping.md correspondence faithful (datetime->Instant, tzinfo->offset:Option Int, MONTHS_DAYS->monthLength; patch edit tzinfo=d.tzinfo -> offset:=d.offset).

same_spec (swebench_unified.markers.same_spec, lean backend): pc=True, atk_1..6 all True (only impl region edited, spec/axioms/pure/pre/post byte-identical).

Verification: `bash scripts/lean_verify.sh <file>`, run concurrently (<=4). Results:
- pc.lean (gold impl, verbatim): EXIT=0 (verifies, no sorry). #print axioms correct_anchor => 'depends on axioms: [propext]' (clean).
- atk_1 (prepatch bug, offset:=none): EXIT=1. Genuine unprovable goal `True*6 ∧ none = d.offset`, assumption failed.
- atk_2 (ungrounded-oracle echo, offset:=some 0): EXIT=1 (some 0 = d.offset unprovable).
- atk_3 (boundary off-by-one roll cond anchorMonth>=12): EXIT=1.
- atk_4 (control-flow-effect, year not incremented on roll): EXIT=1 (assumption failed).
- atk_5 (boundary/partial-domain, day:=d.day unclamped): EXIT=1 (assumption failed).
- atk_6 (field-corruption, hour:=d.minute): EXIT=1.

No wrong impl closed with a clean-axiom proof, so there is NO verifying-but-wrong candidate whose faithful refined patch would need resolve-running (patches={}). The prepatch bug is reproduced by atk_1 (offset dropped -> naive pivot -> TypeError in TZAwareTimesinceTests, the FAIL_TO_PASS). 6 distinct attacks run (prepatch, echo/ungrounded, boundary roll, control-flow year, day-clamp, clock corruption); all fail to verify. verify=>correct holds. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing a shifted calendar reference point.

Given a starting instant and a whole number of years and months, this builds a
reference instant that lies exactly that many years and months after the start.
The reference instant is used downstream to measure the leftover sub-month part
of an elapsed interval, so it must be directly comparable with the other
instants involved in that measurement.

The reference instant is assembled field-by-field from the starting instant:

  * its calendar date is the start's year/month advanced by the requested
    years and months (rolling the month past December into the next year);
  * its day-of-month is the start's day, clamped down to the last valid day of
    the resulting month (so e.g. a 31st never lands in a 30-day month);
  * its clock fields (hour, minute, second) are copied unchanged from the start.

An instant also carries a timezone designation (a constant offset from UTC, or
none when the instant is timezone-naive). Because the reference instant is later
compared against another instant, it must carry the SAME timezone designation as
the starting instant — a naive start yields a naive reference, and an instant at
a given offset yields a reference at that same offset. An instant whose timezone
designation failed to match its peers could not be compared with them at all.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The reference
-- instant is assembled purely from the starting instant's own fields, so its
-- construction is modeled DEEPLY (structure assembly + clamping) rather than
-- through any `opaque`/`axiom` callee contract. The table of month lengths is a
-- constant table, modeled directly in the `pure` region. No callee property is
-- needed by the proof.
-- axioms-end

-- pure-start
/-- An instant: a calendar date, clock fields, and an optional timezone
designation (a constant UTC offset in seconds; `none` = timezone-naive). -/
structure Instant where
  year : Int
  month : Int
  day : Int
  hour : Int
  minute : Int
  second : Int
  offset : Option Int
deriving Repr

/-- Lengths of the twelve calendar months (non-leap reference table). Indexed by
month number 1‥12. -/
def monthLengths : List Int := [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

/-- The length of month `m` (1‥12) from the reference table; out-of-range months
fall back to 31 (never exercised under the precondition `1 ≤ m ≤ 12`). -/
def monthLength (m : Int) : Int := monthLengths.getD (m.toNat - 1) 31
-- pure-end

-- post-conditions-start
/-- The reference instant lies exactly `years` years and `months` months after
`d`. Every component is pinned to its input (frame discipline):

  * year/month are `d`'s advanced by the request, rolling a month past December
    into the next year;
  * the day is `d`'s day clamped to the last valid day of the resulting month;
  * the clock fields equal `d`'s clock fields;
  * the timezone designation equals `d`'s, so the reference is comparable with
    the instants it will be measured against. -/
def problem_spec_anchor
    (d : Instant) (years months : Int) (result : Instant) : Prop :=
  let rawMonth := d.month + months
  let rolled := rawMonth > 12
  result.year = (if rolled then d.year + years + 1 else d.year + years) ∧
  result.month = (if rolled then rawMonth - 12 else rawMonth) ∧
  result.day = min (monthLength result.month) d.day ∧
  result.hour = d.hour ∧
  result.minute = d.minute ∧
  result.second = d.second ∧
  result.offset = d.offset
-- post-conditions-end

-- impl-start
def implementation_anchor
    (d : Instant) (years months : Int) : Instant := Id.run do
  let mut anchorYear := d.year + years
  let mut anchorMonth := d.month + months
  if anchorMonth > 12 then
    anchorMonth := anchorMonth - 12
    anchorYear := anchorYear + 1
  return {
    year := anchorYear,
    month := anchorMonth,
    day := min (monthLength anchorMonth) d.day,
    hour := d.hour,
    minute := d.minute,
    second := d.second,
    offset := d.offset
  }
-- impl-end

-- proof-start
theorem correct_anchor :
    ∀ (d : Instant) (years months : Int),
      1 ≤ d.month → d.month ≤ 12 → 0 ≤ months → months ≤ 11 →
      problem_spec_anchor d years months
        (implementation_anchor d years months) := by
  intro d years months _ _ _ _
  unfold problem_spec_anchor implementation_anchor
  simp only [Id.run, bind, pure]
  by_cases h : d.month + months > 12
  · simp only [h, if_true]; trivial
  · simp only [h, if_false]; trivial
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_anchor pins ALL 7 output fields (year/month/day/hour/minute/second/offset) to exact functions of the inputs over the full precondition domain (1<=d.month<=12, 0<=months<=11; offset/day/year/hour unconstrained beyond equality to the derived value). Any impl deviating on any in-domain input yields a FALSE theorem -> unprovable. No axioms/opaque callees: refinement.md axioms-region states no callee contract consumed; all 12 legs are R/I (no kind-3, no A-consumed/A-reference). A-legs vacuous. mapping.md correspondence faithful (datetime->Instant, tzinfo->offset:Option Int, MONTHS_DAYS->monthLength; patch edit tzinfo=d.tzinfo -> offset:=d.offset).

same_spec (swebench_unified.markers.same_spec, lean backend): pc=True, atk_1..6 all True (only impl region edited, spec/axioms/pure/pre/post byte-identical).

Verification: `bash scripts/lean_verify.sh <file>`, run concurrently (<=4). Results:
- pc.lean (gold impl, verbatim): EXIT=0 (verifies, no sorry). #print axioms correct_anchor => 'depends on axioms: [propext]' (clean).
- atk_1 (prepatch bug, offset:=none): EXIT=1. Genuine unprovable goal `True*6 ∧ none = d.offset`, assumption failed.
- atk_2 (ungrounded-oracle echo, offset:=some 0): EXIT=1 (some 0 = d.offset unprovable).
- atk_3 (boundary off-by-one roll cond anchorMonth>=12): EXIT=1.
- atk_4 (control-flow-effect, year not incremented on roll): EXIT=1 (assumption failed).
- atk_5 (boundary/partial-domain, day:=d.day unclamped): EXIT=1 (assumption failed).
- atk_6 (field-corruption, hour:=d.minute): EXIT=1.

No wrong impl closed with a clean-axiom proof, so there is NO verifying-but-wrong candidate whose faithful refined patch would need resolve-running (patches={}). The prepatch bug is reproduced by atk_1 (offset dropped -> naive pivot -> TypeError in TZAwareTimesinceTests, the FAIL_TO_PASS). 6 distinct attacks run (prepatch, echo/ungrounded, boundary roll, control-flow year, day-clamp, clock corruption); all fail to verify. verify=>correct holds. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-16429, modeled function = the `pivot` datetime construction in django/utils/timesince.py (post-patch `if years or months:` branch, base_commit 6c86495bce). Verified against the real repo at timesince.py.

SPEC REGION: byte-identical between Solution.lean and Solution_prepatch.lean — swebench_unified.markers.same_spec(sol,pre,lean_tables) == True. Only impl+proof regions differ (offset := d.offset vs offset := none). No spec tampering.

COMPILE: scripts/lean_verify.sh on Solution.lean exits 0; `#print axioms correct_anchor` => [propext] only. No sorryAx — proof is real, not fake.

FAITHFULNESS ANALYSIS (problem_spec_anchor vs real post-patch callee, over realizable inputs of the callee under its binder preconditions 1≤d.month≤12, 0≤months≤11):
- year/month rollover: spec `result.year = if rawMonth>12 then d.year+years+1 else d.year+years`, `result.month = if rawMonth>12 then rawMonth-12 else rawMonth`. Real code: pivot_year=d.year+years; pivot_month=d.month+months; if pivot_month>12: pivot_month-=12; pivot_year+=1. Under preconditions rawMonth∈[1,23] so a single -12 suffices in both. EXACT match.
- day clamp: spec `min (monthLength result.month) d.day` == real `min(MONTHS_DAYS[pivot_month-1], d.day)`; monthLengths list == MONTHS_DAYS tuple (both non-leap, identical), monthLength = getD(m-1,31). EXACT (including the shared no-leap-year behavior — faithful to repo, not idealized).
- clock fields hour/minute/second: copied verbatim on both sides.
- offset := d.offset ⟷ tzinfo=d.tzinfo (the fix). Spec pins pivot designation to d's; real post-patch attaches d.tzinfo. Faithful for both naive (None/none) and aware (some k) cases.

No diverging input exists on the callee's realizable domain. The only mismatches are out-of-domain artifacts of the field-level model (e.g. pivot_year>9999 or invalid raw fields where real datetime() would raise ValueError) — but timesince derives years,months from divmod(total_months,12) with now.year≤9999 and d always has valid calendar fields, so those inputs are unreachable for this callee. This is a documented modeling boundary (mapping.md/conformance_check.py: field-level replica, no datetime construction), not a behavioral drift on any input the modeled function can actually receive. G-CONF differential (seed 16429, 120k+9 edge inputs) confirms field-level agreement with the post-patch oracle.

The spec is neither too strong nor drifted: every output field is pinned to precisely what the patched code produces. Note the recorded G-EQ status is fail/INCONCLUSIVE (1 attack inconclusive) — that is a G-EQ protocol artifact, orthogonal to faithfulness; it does not indicate the spec disagrees with the real callee.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage/gold-reconstruction analysis for django__django-16429 (lean).

Mechanical checks:
- same_spec(Solution.lean, Solution_prepatch.lean) = True: the spec region (docstring + axioms + pure + post-conditions) is byte-identical between the patched and prepatch bundles. The gold discriminator therefore lives entirely in the impl/proof regions (which are elided in the spec view), not in what the solver sees.
- leakage.screen over the spec view against the PUBLIC problem_statement (not hints_text) = passed, hard_failures=[], warnings=[]. No diff markers, no patched file path (timesince.py), no repo-symbol echo (pivot/tzinfo/datetime), no bug/fix narration in the spec view.

Gold-reconstruction judgement:
- The gold edit is adding `tzinfo=d.tzinfo` to the pivot's datetime.datetime(...) constructor so the pivot carries the same tz designation as d. The spec view encodes only the abstract correctness property `result.offset = d.offset` ("must carry the SAME timezone designation as the starting instant"), phrased in domain-neutral terms (Instant/offset), never naming tzinfo, datetime, or the pivot construction.
- The PUBLIC problem_statement is strictly MORE revealing than the spec view: it explicitly states "the pivot ... does not take into account the datetime object's tzinfo. Adding 0, d.tzinfo arguments to the datetime.datetime call seems to fix this." So the exact gold edit is already public. Nothing in the spec view exceeds that; it is an abstract, backend-agnostic restatement of a property already fully disclosed publicly.

Conclusion: the spec view does not leak the gold edit beyond problem_statement. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
