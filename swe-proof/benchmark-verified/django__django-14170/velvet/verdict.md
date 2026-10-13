# P2 adversarial audit — django__django-14170

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

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
None. The spec is fully functional: yearBoundsDate/yearBoundsDatetime/yearLookupBounds each carry a total functional postcondition (out = dateBounds value isoYear / out = datetimeBounds value isoYear / the dispatch equation) plus the two branch-conditioned equalities, all against the opaque A-reference axioms gregJan1/gregDec31/isoFirst/dtJan1/dtDec31/dtIsoFirst. Because out is pinned exactly for every (value, isoYear[, isDateTimeField]), no wrong impl can verify. All 7 same-spec wrong impls (incl. the exact prepatch bug) fail Velvet verification (exit 1), so there is NO verifying-wrong-impl and hence no faithful refined patch that could fail to resolve. The resolve step of the protocol is therefore vacuously satisfied (patches={}). verify ⇒ correct holds.
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
 
 -- axioms-start
 /- Calendar landmarks for a given year, as the unchanged platform date/datetime
@@ -80,11 +80,7 @@
   ensures isoYear = false → out = [gregJan1 value, gregDec31 value]
   do
     -- impl-start
-    let out : List Int :=
-      if isoYear then
-        [isoFirst value, isoFirst (value + 1) - 1]
-      else
-        [gregJan1 value, gregDec31 value]
+    let out : List Int := [gregJan1 value, gregDec31 value]
     return out
     -- impl-end
 
@@ -100,11 +96,7 @@
   ensures isoYear = false → out = [dtJan1 value, dtDec31 value]
   do
     -- impl-start
-    let out : List Int :=
-      if isoYear then
-        [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
-      else
-        [dtJan1 value, dtDec31 value]
+    let out : List Int := [dtJan1 value, dtDec31 value]
     return out
     -- impl-end
 
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
 
 -- axioms-start
 /- Calendar landmarks for a given year, as the unchanged platform date/datetime
@@ -84,7 +84,7 @@
       if isoYear then
         [isoFirst value, isoFirst (value + 1) - 1]
       else
-        [gregJan1 value, gregDec31 value]
+        [gregDec31 value, gregJan1 value]
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
 
 -- axioms-start
 /- Calendar landmarks for a given year, as the unchanged platform date/datetime
@@ -82,7 +82,7 @@
     -- impl-start
     let out : List Int :=
       if isoYear then
-        [isoFirst value, isoFirst (value + 1) - 1]
+        [isoFirst value, isoFirst (value + 1)]
       else
         [gregJan1 value, gregDec31 value]
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
 
 -- axioms-start
 /- Calendar landmarks for a given year, as the unchanged platform date/datetime
@@ -102,9 +102,9 @@
     -- impl-start
     let out : List Int :=
       if isoYear then
+        [dtJan1 value, dtDec31 value]
+      else
         [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
-      else
-        [dtJan1 value, dtDec31 value]
     return out
     -- impl-end
 
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
 
 -- axioms-start
 /- Calendar landmarks for a given year, as the unchanged platform date/datetime
@@ -82,7 +82,7 @@
     -- impl-start
     let out : List Int :=
       if isoYear then
-        [isoFirst value, isoFirst (value + 1) - 1]
+        [gregJan1 value, gregDec31 value]
       else
         [gregJan1 value, gregDec31 value]
     return out
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
 
 -- axioms-start
 /- Calendar landmarks for a given year, as the unchanged platform date/datetime
@@ -126,9 +126,9 @@
   do
     -- impl-start
     let out ← if isDateTimeField then
+        yearBoundsDate value isoYear
+      else
         yearBoundsDatetime value isoYear
-      else
-        yearBoundsDate value isoYear
     return out
     -- impl-end
 
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
 
 -- axioms-start
 /- Calendar landmarks for a given year, as the unchanged platform date/datetime
@@ -82,7 +82,7 @@
     -- impl-start
     let out : List Int :=
       if isoYear then
-        [isoFirst value, isoFirst (value + 1) - 1]
+        [isoFirst value, isoFirst value - 1]
       else
         [gregJan1 value, gregDec31 value]
     return out
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- Calendar landmarks for a given year, as the unchanged platform date/datetime
   library reports them. Dates are carried as proleptic-Gregorian day ordinals
   and timestamps as integer microsecond instants (a strictly order-preserving
   bijection — see mapping.md §2), so the comparison semantics a range query
   relies on are preserved exactly. These are read-only library callees the
   operation invokes but does not reshape; provenance + executable soundness
   check (G-AX) live in mapping.md / axiom_check.py.

   `gregJan1 y` — first day of calendar year `y` (its January 1st).
   `gregDec31 y` — last day of calendar year `y` (its December 31st).
   `isoFirst y` — first day of the ISO-8601 week-numbering year `y`.
   `dtJan1 y` — first instant of calendar year `y`.
   `dtDec31 y` — last instant of calendar year `y` (its final microsecond).
   `dtIsoFirst y` — first instant of the ISO-8601 week-numbering year `y`. -/
axiom gregJan1    : Int → Int
axiom gregDec31   : Int → Int
axiom isoFirst    : Int → Int
axiom dtJan1      : Int → Int
axiom dtDec31     : Int → Int
axiom dtIsoFirst  : Int → Int
-- axioms-end

-- pure-start
noncomputable section
/- The closed (inclusive) range of day ordinals that a year-valued range query
   over a date-typed column must match.

   For an ordinary calendar year the range runs from that year's first day to
   its last day. For an ISO-8601 week-numbering year the range instead runs from
   that ISO year's first day up to the day immediately before the next ISO
   year's first day — these two notions of "year" disagree near the new-year
   boundary, so the ISO range must be derived from the ISO landmarks, not the
   calendar ones. The carrier is the two-element list `[lower, upper]`. -/
def dateBounds (value : Int) (isoYear : Bool) : List Int :=
  if isoYear then [isoFirst value, isoFirst (value + 1) - 1]
  else [gregJan1 value, gregDec31 value]

/- The closed (inclusive) range of microsecond instants for a year-valued range
   query over a timestamp-typed column. Same calendar-vs-ISO distinction as
   `dateBounds`; the ISO upper bound is the instant one microsecond before the
   first instant of the next ISO year. -/
def datetimeBounds (value : Int) (isoYear : Bool) : List Int :=
  if isoYear then [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
  else [dtJan1 value, dtDec31 value]

@[grind] lemma dateBounds_def (value : Int) (isoYear : Bool) :
    dateBounds value isoYear =
      (if isoYear then [isoFirst value, isoFirst (value + 1) - 1]
       else [gregJan1 value, gregDec31 value]) := rfl

@[grind] lemma datetimeBounds_def (value : Int) (isoYear : Bool) :
    datetimeBounds value isoYear =
      (if isoYear then [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
       else [dtJan1 value, dtDec31 value]) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Lower and upper bounds for a year-valued range query against a date-typed
   column. `isoYear` selects whether the looked-up `value` denotes an ISO-8601
   week-numbering year or an ordinary calendar year; both inputs are read-only
   (neither is `mut`). When `isoYear` holds the bounds must be the ISO year's
   span, which differs from the calendar year's span at the year boundary. -/
method yearBoundsDate (value : Int) (isoYear : Bool) return (out : List Int)
  ensures out = dateBounds value isoYear
  ensures isoYear = true  → out = [isoFirst value, isoFirst (value + 1) - 1]
  ensures isoYear = false → out = [gregJan1 value, gregDec31 value]
  do
    -- impl-start
    let out : List Int :=
      if isoYear then
        [isoFirst value, isoFirst (value + 1) - 1]
      else
        [gregJan1 value, gregDec31 value]
    return out
    -- impl-end

prove_correct yearBoundsDate by
  loom_solve

/- Lower and upper bounds for a year-valued range query against a timestamp-typed
   column. As `yearBoundsDate`, but over microsecond instants; `isoYear` selects
   the ISO-8601 week-numbering year span when set. Both inputs read-only. -/
method yearBoundsDatetime (value : Int) (isoYear : Bool) return (out : List Int)
  ensures out = datetimeBounds value isoYear
  ensures isoYear = true  → out = [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
  ensures isoYear = false → out = [dtJan1 value, dtDec31 value]
  do
    -- impl-start
    let out : List Int :=
      if isoYear then
        [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
      else
        [dtJan1 value, dtDec31 value]
    return out
    -- impl-end

prove_correct yearBoundsDatetime by
  loom_solve

/- Dispatch a year-valued range query to the bounds appropriate for the column's
   type. `isDateTimeField` distinguishes a timestamp-typed column from a
   date-typed one. `isoYear` records whether the lookup targets ISO-8601
   week-numbering years; it MUST be forwarded to the chosen bounds computation so
   that an ISO-year lookup yields ISO-year bounds rather than calendar-year
   bounds. All inputs are read-only. -/
method yearLookupBounds (isDateTimeField : Bool) (isoYear : Bool) (value : Int)
    return (out : List Int)
  ensures out = (if isDateTimeField then datetimeBounds value isoYear
                 else dateBounds value isoYear)
  ensures isDateTimeField = true  → out = datetimeBounds value isoYear
  ensures isDateTimeField = false → out = dateBounds value isoYear
  do
    -- impl-start
    let out ← if isDateTimeField then
        yearBoundsDatetime value isoYear
      else
        yearBoundsDate value isoYear
    return out
    -- impl-end

prove_correct yearLookupBounds by
  loom_solve

end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec (velvet language). atk_1 is byte-identical to Solution_prepatch.lean (verified with diff -q).

### VERIFICATION (bash scripts/lean_verify.sh <file>; run concurrently in 2 batches of <=4 as mandated):
  pos_control.lean -> EXIT 0 (verifies, no sorry) [positive control OK]
  prepatch.lean    -> EXIT 1 (prepatch bug reproduced; goal '[dtJan1 value, dtDec31 value] = datetimeBounds value isoYear' unprovable)
  atk_1 EXIT 1 | atk_2 EXIT 1 | atk_3 EXIT 1 | atk_4 EXIT 1 | atk_5 EXIT 1 | atk_6 EXIT 1 | atk_7 EXIT 1
All wrong impls fail with residual goals showing the functional postcondition cannot be discharged.

### DISTINCT WRONG-IMPL CLASSES (>=5, all editing only impl regions):
  atk_1 ungrounded/prepatch: ignore isoYear, calendar bounds in BOTH helpers (== prepatch bug)
  atk_2 partial-domain/boundary: swap [gregDec31, gregJan1] order on the calendar branch (date helper)
  atk_3 boundary/off-by-one: iso upper = isoFirst(value+1) with the -1 dropped (date helper)
  atk_4 control-flow-effect: swap iso<->calendar branches in the datetime helper
  atk_5 ungrounded-oracle echo: use calendar landmarks (gregJan1/gregDec31) in the iso branch (date helper)
  atk_6 control-flow: dispatcher swaps date<->datetime callees in yearLookupBounds
  atk_7 boundary/partial: iso upper offset wrong (isoFirst value - 1 instead of isoFirst(value+1) - 1)

RESOLVE RUNS: none required. Step 2 of the protocol only mandates materializing+resolve-running a faithful refined patch for wrong impls that VERIFY. Zero wrong impls verified (spec is total/functional), so the patches map is empty and no resolve run was possible or needed. This is not INCONCLUSIVE: the resolve obligation is vacuous because its precondition (a verifying wrong impl) is provably absent.

A-LEG / MODEL-CORRESPONDENCE AUDIT (mandate focus):
  - refinement.md legs: all classified R / A-reference / I; A-consumed explicitly 'none' (proof consumes no equational axiom; postconditions are structural — confirmed: impls return the exact spec expressions). No kind-3 leg.
  - A-reference correspondence: the 6 opaque axioms (gregJan1, gregDec31, isoFirst, dtJan1, dtDec31, dtIsoFirst) map to the real UNCHANGED stdlib datetime callees at operations.py (mapping.md §1/§3). axiom_check.py (G-AX) RUN -> EXIT 0: 'G-AX OK: 6 datetime landmark A-references + 2 minus-one-unit ISO upper-bound identities sound over 16 boundary + 20000 fuzz years'. The two minus-one-unit refinement identities (date days / datetime microseconds) validated over the order-preserving ordinal/microsecond carrier.
  - conformance_check.py (G-CONF) RUN -> EXIT 0 over 100060 inputs (seed 14170), 0 disagreements (ran with fallback oracle = patch.diff transcribed, since django not importable outside container; oracle is byte-faithful to patch.diff's modeled region). R/I legs shadow-match the patched helpers.

CONCLUSION: The postconditions are exact functional specs over faithfully-corresponding A-reference axioms; verify ⇒ correct. No verifying wrong impl exists, so verify does not fail to imply correct. SOUND.

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
None. The spec is fully functional: yearBoundsDate/yearBoundsDatetime/yearLookupBounds each carry a total functional postcondition (out = dateBounds value isoYear / out = datetimeBounds value isoYear / the dispatch equation) plus the two branch-conditioned equalities, all against the opaque A-reference axioms gregJan1/gregDec31/isoFirst/dtJan1/dtDec31/dtIsoFirst. Because out is pinned exactly for every (value, isoYear[, isDateTimeField]), no wrong impl can verify. All 7 same-spec wrong impls (incl. the exact prepatch bug) fail Velvet verification (exit 1), so there is NO verifying-wrong-impl and hence no faithful refined patch that could fail to resolve. The resolve step of the protocol is therefore vacuously satisfied (patches={}). verify ⇒ correct holds.
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
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- Calendar landmarks for a given year, as the unchanged platform date/datetime
   library reports them. Dates are carried as proleptic-Gregorian day ordinals
   and timestamps as integer microsecond instants (a strictly order-preserving
   bijection — see mapping.md §2), so the comparison semantics a range query
   relies on are preserved exactly. These are read-only library callees the
   operation invokes but does not reshape; provenance + executable soundness
   check (G-AX) live in mapping.md / axiom_check.py.

   `gregJan1 y` — first day of calendar year `y` (its January 1st).
   `gregDec31 y` — last day of calendar year `y` (its December 31st).
   `isoFirst y` — first day of the ISO-8601 week-numbering year `y`.
   `dtJan1 y` — first instant of calendar year `y`.
   `dtDec31 y` — last instant of calendar year `y` (its final microsecond).
   `dtIsoFirst y` — first instant of the ISO-8601 week-numbering year `y`. -/
axiom gregJan1    : Int → Int
axiom gregDec31   : Int → Int
axiom isoFirst    : Int → Int
axiom dtJan1      : Int → Int
axiom dtDec31     : Int → Int
axiom dtIsoFirst  : Int → Int
-- axioms-end

-- pure-start
noncomputable section
/- The closed (inclusive) range of day ordinals that a year-valued range query
   over a date-typed column must match.

   For an ordinary calendar year the range runs from that year's first day to
   its last day. For an ISO-8601 week-numbering year the range instead runs from
   that ISO year's first day up to the day immediately before the next ISO
   year's first day — these two notions of "year" disagree near the new-year
   boundary, so the ISO range must be derived from the ISO landmarks, not the
   calendar ones. The carrier is the two-element list `[lower, upper]`. -/
def dateBounds (value : Int) (isoYear : Bool) : List Int :=
  if isoYear then [isoFirst value, isoFirst (value + 1) - 1]
  else [gregJan1 value, gregDec31 value]

/- The closed (inclusive) range of microsecond instants for a year-valued range
   query over a timestamp-typed column. Same calendar-vs-ISO distinction as
   `dateBounds`; the ISO upper bound is the instant one microsecond before the
   first instant of the next ISO year. -/
def datetimeBounds (value : Int) (isoYear : Bool) : List Int :=
  if isoYear then [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
  else [dtJan1 value, dtDec31 value]

@[grind] lemma dateBounds_def (value : Int) (isoYear : Bool) :
    dateBounds value isoYear =
      (if isoYear then [isoFirst value, isoFirst (value + 1) - 1]
       else [gregJan1 value, gregDec31 value]) := rfl

@[grind] lemma datetimeBounds_def (value : Int) (isoYear : Bool) :
    datetimeBounds value isoYear =
      (if isoYear then [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
       else [dtJan1 value, dtDec31 value]) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Lower and upper bounds for a year-valued range query against a date-typed
   column. `isoYear` selects whether the looked-up `value` denotes an ISO-8601
   week-numbering year or an ordinary calendar year; both inputs are read-only
   (neither is `mut`). When `isoYear` holds the bounds must be the ISO year's
   span, which differs from the calendar year's span at the year boundary. -/
method yearBoundsDate (value : Int) (isoYear : Bool) return (out : List Int)
  ensures out = dateBounds value isoYear
  ensures isoYear = true  → out = [isoFirst value, isoFirst (value + 1) - 1]
  ensures isoYear = false → out = [gregJan1 value, gregDec31 value]
  do
    -- impl-start
    let out : List Int :=
      if isoYear then
        [isoFirst value, isoFirst (value + 1) - 1]
      else
        [gregJan1 value, gregDec31 value]
    return out
    -- impl-end

prove_correct yearBoundsDate by
  loom_solve

/- Lower and upper bounds for a year-valued range query against a timestamp-typed
   column. As `yearBoundsDate`, but over microsecond instants; `isoYear` selects
   the ISO-8601 week-numbering year span when set. Both inputs read-only. -/
method yearBoundsDatetime (value : Int) (isoYear : Bool) return (out : List Int)
  ensures out = datetimeBounds value isoYear
  ensures isoYear = true  → out = [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
  ensures isoYear = false → out = [dtJan1 value, dtDec31 value]
  do
    -- impl-start
    let out : List Int :=
      if isoYear then
        [dtIsoFirst value, dtIsoFirst (value + 1) - 1]
      else
        [dtJan1 value, dtDec31 value]
    return out
    -- impl-end

prove_correct yearBoundsDatetime by
  loom_solve

/- Dispatch a year-valued range query to the bounds appropriate for the column's
   type. `isDateTimeField` distinguishes a timestamp-typed column from a
   date-typed one. `isoYear` records whether the lookup targets ISO-8601
   week-numbering years; it MUST be forwarded to the chosen bounds computation so
   that an ISO-year lookup yields ISO-year bounds rather than calendar-year
   bounds. All inputs are read-only. -/
method yearLookupBounds (isDateTimeField : Bool) (isoYear : Bool) (value : Int)
    return (out : List Int)
  ensures out = (if isDateTimeField then datetimeBounds value isoYear
                 else dateBounds value isoYear)
  ensures isDateTimeField = true  → out = datetimeBounds value isoYear
  ensures isDateTimeField = false → out = dateBounds value isoYear
  do
    -- impl-start
    let out ← if isDateTimeField then
        yearBoundsDatetime value isoYear
      else
        yearBoundsDate value isoYear
    return out
    -- impl-end

prove_correct yearLookupBounds by
  loom_solve

end
```

Prepatch bug re-encoded as an attack: `True`.

SAME-SPEC: all 7 attacks + prepatch confirmed same_spec=True via swebench_unified.markers.same_spec (velvet language). atk_1 is byte-identical to Solution_prepatch.lean (verified with diff -q).

### VERIFICATION (bash scripts/lean_verify.sh <file>; run concurrently in 2 batches of <=4 as mandated):
  pos_control.lean -> EXIT 0 (verifies, no sorry) [positive control OK]
  prepatch.lean    -> EXIT 1 (prepatch bug reproduced; goal '[dtJan1 value, dtDec31 value] = datetimeBounds value isoYear' unprovable)
  atk_1 EXIT 1 | atk_2 EXIT 1 | atk_3 EXIT 1 | atk_4 EXIT 1 | atk_5 EXIT 1 | atk_6 EXIT 1 | atk_7 EXIT 1
All wrong impls fail with residual goals showing the functional postcondition cannot be discharged.

### DISTINCT WRONG-IMPL CLASSES (>=5, all editing only impl regions):
  atk_1 ungrounded/prepatch: ignore isoYear, calendar bounds in BOTH helpers (== prepatch bug)
  atk_2 partial-domain/boundary: swap [gregDec31, gregJan1] order on the calendar branch (date helper)
  atk_3 boundary/off-by-one: iso upper = isoFirst(value+1) with the -1 dropped (date helper)
  atk_4 control-flow-effect: swap iso<->calendar branches in the datetime helper
  atk_5 ungrounded-oracle echo: use calendar landmarks (gregJan1/gregDec31) in the iso branch (date helper)
  atk_6 control-flow: dispatcher swaps date<->datetime callees in yearLookupBounds
  atk_7 boundary/partial: iso upper offset wrong (isoFirst value - 1 instead of isoFirst(value+1) - 1)

RESOLVE RUNS: none required. Step 2 of the protocol only mandates materializing+resolve-running a faithful refined patch for wrong impls that VERIFY. Zero wrong impls verified (spec is total/functional), so the patches map is empty and no resolve run was possible or needed. This is not INCONCLUSIVE: the resolve obligation is vacuous because its precondition (a verifying wrong impl) is provably absent.

A-LEG / MODEL-CORRESPONDENCE AUDIT (mandate focus):
  - refinement.md legs: all classified R / A-reference / I; A-consumed explicitly 'none' (proof consumes no equational axiom; postconditions are structural — confirmed: impls return the exact spec expressions). No kind-3 leg.
  - A-reference correspondence: the 6 opaque axioms (gregJan1, gregDec31, isoFirst, dtJan1, dtDec31, dtIsoFirst) map to the real UNCHANGED stdlib datetime callees at operations.py (mapping.md §1/§3). axiom_check.py (G-AX) RUN -> EXIT 0: 'G-AX OK: 6 datetime landmark A-references + 2 minus-one-unit ISO upper-bound identities sound over 16 boundary + 20000 fuzz years'. The two minus-one-unit refinement identities (date days / datetime microseconds) validated over the order-preserving ordinal/microsecond carrier.
  - conformance_check.py (G-CONF) RUN -> EXIT 0 over 100060 inputs (seed 14170), 0 disagreements (ran with fallback oracle = patch.diff transcribed, since django not importable outside container; oracle is byte-faithful to patch.diff's modeled region). R/I legs shadow-match the patched helpers.

CONCLUSION: The postconditions are exact functional specs over faithfully-corresponding A-reference axioms; verify ⇒ correct. No verifying wrong impl exists, so verify does not fail to imply correct. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec regions (axioms/pure/pre/post) byte-identical post vs prepatch (same_spec=True, VelvetBackend); only impl differs, so postconditions genuinely constrain the ISO-flag forwarding fix (prepatch violates isoYear=true postcondition => real G-DIFF). Solution.lean elaborates clean (lean_verify exit 0). Faithfulness checked against the REAL patched callee: bound BaseDatabaseOperations.year_lookup_bounds_for_{date,datetime}_field from patched worktree (base 6efc35b4… + patch.diff, django 4.0) and ran direct differential of the Lean model's shadow vs the real callee over the ordinal/microsecond carrier — 2596 in-range cases (years 1-299 & 9000-9999, both iso flags, both column types): 0 divergences. Pinned G-CONF (seed 14170, 100k inputs) passes. ISO refinement identity fromisocalendar(v+1,1,1)-1unit exact incl ISO-long years 2004/2015/2020. Totality note: real callee raises ValueError for out-of-range years (<=0, >=10000) while Lean method is total, but the six datetime landmarks are opaque/uninterpreted axioms so the spec makes NO concrete claim there and cannot disagree — not a drift. No diverging input on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean (no hard failures); patch-changed distinctive symbols are year_lookup_bounds_for_date_field/_datetime_field, IRegex, adapt_ipaddressfield_value — none appear in the spec view. same_spec(post,pre)=True and the post/pre spec views are byte-identical (edit lives entirely in elided impl regions).

Semantic judgment for gold-reconstruction: the public problem_statement already discloses the entire behavioral defect — YearLookup's BETWEEN optimization is wrongly applied to __iso_year lookups, showing the buggy calendar bounds (BETWEEN 2020-01-01 AND 2020-12-31) and requiring that iso_year lookups instead yield ISO-8601 week-numbering-year bounds. The spec view encodes exactly this publicly-required behavior via invented Lean names (gregJan1/isoFirst/dtIsoFirst axioms, dateBounds/datetimeBounds: ISO -> [isoFirst value, isoFirst (value+1)-1]; calendar -> [gregJan1, gregDec31]). These are not repo identifiers (real callees datetime.date.fromisocalendar, operations.py, lookups.py do not appear), no diff markers, no patched file/module paths, and no bug/fix narration.

The ISO-boundary formula (first day of ISO year .. day before next ISO year's first day) is the standard mathematical definition of an ISO week-numbering year's span, derivable from the publicly-named concept — it localizes required behavior, not the gold edit. No spec-view line reveals the fix beyond the public problem_statement. Note: the descriptive comments name ISO-8601 concepts, but those are public in the problem_statement ("__iso_year"/ExtractIsoYear), so no leakage beyond it.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).