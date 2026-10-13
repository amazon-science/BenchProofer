# P2 adversarial audit — django__django-16429

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec `ensures out = shiftReference base years months` is exact structural equality against a transparent, fully-concrete deterministic deep model in the FROZEN pure region. No verifying-but-wrong impl exists: the two verifying same-spec impls (pos_control, atk_9) are correct on the reachable domain, and atk_9's faithful patch (= the gold construction) RESOLVES under the official harness.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -101,7 +101,6 @@
     -- impl-start
     let py  := base.y + years
     let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
     let py' := if pm > 12 then py + 1 else py
     let pm' := if pm > 12 then pm - 12 else pm
     let out : Instant :=
@@ -111,7 +110,7 @@
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
-        zone := base.zone }
+        zone := none }
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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -101,13 +101,12 @@
     -- impl-start
     let py  := base.y + years
     let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
     let py' := if pm > 12 then py + 1 else py
     let pm' := if pm > 12 then pm - 12 else pm
     let out : Instant :=
       { y    := py',
         mo   := pm',
-        d    := min (monthLen pm') base.d,
+        d    := base.d,
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -101,13 +101,10 @@
     -- impl-start
     let py  := base.y + years
     let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
-    let py' := if pm > 12 then py + 1 else py
-    let pm' := if pm > 12 then pm - 12 else pm
     let out : Instant :=
-      { y    := py',
-        mo   := pm',
-        d    := min (monthLen pm') base.d,
+      { y    := py,
+        mo   := pm,
+        d    := min (monthLen pm) base.d,
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -99,9 +99,8 @@
   ensures out = shiftReference base years months
   do
     -- impl-start
-    let py  := base.y + years
-    let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
+    let py  := base.y + months
+    let pm  := base.mo + years
     let py' := if pm > 12 then py + 1 else py
     let pm' := if pm > 12 then pm - 12 else pm
     let out : Instant :=
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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -101,7 +101,6 @@
     -- impl-start
     let py  := base.y + years
     let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
     let py' := if pm > 12 then py + 1 else py
     let pm' := if pm > 12 then pm - 12 else pm
     let out : Instant :=
@@ -111,7 +110,7 @@
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
-        zone := base.zone }
+        zone := if base.mo = 12 then none else base.zone }
     return out
     -- impl-end
 
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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -99,20 +99,7 @@
   ensures out = shiftReference base years months
   do
     -- impl-start
-    let py  := base.y + years
-    let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
-    let py' := if pm > 12 then py + 1 else py
-    let pm' := if pm > 12 then pm - 12 else pm
-    let out : Instant :=
-      { y    := py',
-        mo   := pm',
-        d    := min (monthLen pm') base.d,
-        h    := base.h,
-        mi   := base.mi,
-        s    := base.s,
-        zone := base.zone }
-    return out
+    return (default : Instant)
     -- impl-end
 
 prove_correct buildShiftedReference by
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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -101,13 +101,12 @@
     -- impl-start
     let py  := base.y + years
     let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
     let py' := if pm > 12 then py + 1 else py
     let pm' := if pm > 12 then pm - 12 else pm
     let out : Instant :=
       { y    := py',
         mo   := pm',
-        d    := min (monthLen pm') base.d,
+        d    := min (monthLen pm) base.d,
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -101,7 +101,6 @@
     -- impl-start
     let py  := base.y + years
     let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
     let py' := if pm > 12 then py + 1 else py
     let pm' := if pm > 12 then pm - 12 else pm
     let out : Instant :=
@@ -111,7 +110,7 @@
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
-        zone := base.zone }
+        zone := some 0 }
     return out
     -- impl-end
 
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms and no deep-model references. The modeled behavior is a
@@ -99,20 +99,10 @@
   ensures out = shiftReference base years months
   do
     -- impl-start
-    let py  := base.y + years
-    let pm  := base.mo + months
-    -- normalize the shifted month back into 1..12, carrying into the year
-    let py' := if pm > 12 then py + 1 else py
-    let pm' := if pm > 12 then pm - 12 else pm
-    let out : Instant :=
-      { y    := py',
-        mo   := pm',
-        d    := min (monthLen pm') base.d,
-        h    := base.h,
-        mi   := base.mi,
-        s    := base.s,
-        zone := base.zone }
-    return out
+    if 0 < years ∨ 0 < months then
+      return shiftReference base years months
+    else
+      return (default : Instant)
     -- impl-end
 
 prove_correct buildShiftedReference by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The modeled behavior is a
   pure data-flow that builds a shifted reference instant from the components of
   a source instant and a whole-unit (years, months) offset; every component is
   read directly from the inputs, nothing is delegated to an unchanged foreign
   callee (mapping.md §3). G-AX therefore has nothing to check. -/
-- axioms-end

-- pure-start
/- An instant on the calendar, separated into the components a later difference
   is computed from. `zone` records the time-zone designation the instant is
   expressed against: `none` is a floating instant (no designation), `some k` is
   an instant anchored to designation `k`. Two instants can only be compared /
   subtracted when they share the same designation status — a floating instant
   and an anchored one are not on a common timeline. -/
structure Instant where
  y    : Nat
  mo   : Nat
  d    : Nat
  h    : Nat
  mi   : Nat
  s    : Nat
  zone : Option Nat
deriving DecidableEq, Repr, Inhabited

/- The number of days in a (1-indexed) calendar month, the constant table used
   to clamp a day-of-month onto a target month. February is the common-year length;
   the clamp only ever caps an out-of-range day, so the leap-year case is not
   distinguished here. -/
def monthLen : Nat → Nat
  | 1  => 31 | 2  => 28 | 3  => 31 | 4  => 30 | 5  => 31 | 6  => 30
  | 7  => 31 | 8  => 31 | 9  => 30 | 10 => 31 | 11 => 30 | 12 => 31
  | _  => 30

/- Build the reference instant obtained by shifting `base` forward by whole
   `years` and `months`. The shifted month is normalized back into 1..12,
   carrying into the year when it overflows; the day-of-month is clamped to the
   target month's length so an end-of-month source never names a non-existent
   day; the hour/minute/second are carried across verbatim. Crucially the
   reference is expressed against the SAME time-zone designation as `base`
   (`zone := base.zone`): the shifted reference must lie on the same timeline as
   the source so that a later difference between the reference and another
   instant on that timeline is well-defined. -/
def shiftReference (base : Instant) (years months : Nat) : Instant :=
  let py  := base.y + years
  let pm  := base.mo + months
  let py' := if pm > 12 then py + 1 else py
  let pm' := if pm > 12 then pm - 12 else pm
  { y    := py',
    mo   := pm',
    d    := min (monthLen pm') base.d,
    h    := base.h,
    mi   := base.mi,
    s    := base.s,
    zone := base.zone }

@[grind] lemma shiftReference_def (base : Instant) (years months : Nat) :
    shiftReference base years months =
      (let py  := base.y + years
       let pm  := base.mo + months
       let py' := if pm > 12 then py + 1 else py
       let pm' := if pm > 12 then pm - 12 else pm
       { y    := py',
         mo   := pm',
         d    := min (monthLen pm') base.d,
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
         zone := base.zone : Instant }) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the reference instant used to measure the leftover span after whole
   years and months have been accounted for. `base` is read-only (not `mut`):
   the builder only reads its components and returns a fresh instant. The
   reference is the source shifted forward by `years`/`months`, normalized onto
   a real calendar day, and — the property the leftover-span measurement
   depends on — expressed against the SAME time-zone designation as `base`, so
   the two lie on a common timeline. The whole-unit offset is the result of a
   division by twelve, so `months ≤ 11`; this site is only reached when at least
   one whole unit elapsed. -/
method buildShiftedReference (base : Instant) (years : Nat) (months : Nat) return (out : Instant)
  require 1 ≤ base.mo ∧ base.mo ≤ 12
  require months ≤ 11
  require 0 < years ∨ 0 < months
  ensures out = shiftReference base years months
  do
    -- impl-start
    return shiftReference base years months
    -- impl-end

prove_correct buildShiftedReference by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: python python; verify via `bash scripts/lean_verify.sh <f>`. All 9 attack files + pos_control confirmed same_spec=True vs Solution.lean (velvet backend); edits confined to the impl region.

### VERIFY RESULTS (exit codes):
- pos_control (`return shiftReference base years months`; structurally-distinct correct): exit 0 => spec NON-VACUOUS.
- atk_1 prepatch bug (`zone := none`): exit 1. Fails exactly on `ensures_1: out = shiftReference ...` at the `zone := none` vs `zone := base.zone` field — the gold-added `tzinfo=d.tzinfo`. PREPATCH REPRODUCED.
- atk_2 (drop day clamp, `d := base.d`): exit 1 (caught at `d`).
- atk_3 (drop month-overflow normalization, raw pm/py): exit 1.
- atk_4 (swap years/months): exit 1.
- atk_5 (control-flow-effect partial-domain: `zone := if base.mo = 12 then none else base.zone`; base.mo=12 is IN-DOMAIN & reachable): exit 1 => partial-domain infidelity caught.
- atk_6 (ungrounded-oracle echo probe `return (default : Instant)`): exit 1.
- atk_7 (boundary: clamp with pre-normalization `monthLen pm` not `monthLen pm'`): exit 1.
- atk_8 (hardcode `zone := some 0` regardless of base.zone): exit 1.
- atk_9 (dead-branch probe: `if 0 < years ∨ 0 < months then shiftReference ... else default`): exit 0 => VERIFIES. The else branch is DEAD because `require 0 < years ∨ 0 < months` holds on the reachable domain — mirrors gold's `if years or months:` guard.

RESOLVE RUN (mandatory for verifying wrong-impl): atk_9's faithful refined patch is the gold construction (its reachable behavior == shiftReference == gold `tzinfo=d.tzinfo`; dead else refines to gold's `else: pivot = d`). Ran `harness.run_resolve('django__django-16429', <atk_9.patch>, timeout=1800, retries=0)` => RESOLVED=True, COMPLETED=True; FAIL_TO_PASS 4/4 success (test_depth, test_depth_invalid, 'Test other units', test_thousand_years_ago), PASS_TO_PASS 21/21 success, 0 failures. So atk_9 does NOT break the spec — it is a correct impl (verify⇒resolve holds). No verifying-but-wrong impl's faithful patch fails to resolve.

REFINEMENT AUDIT (refinement.md): legs A1-A8 are all R or I; NO A-consumed / A-reference legs and NO kind-3 step (consistent with meta.json axioms=[], deep_model_references=[], G-AX skip). The genuinely-changed op A7 (propagate tzinfo => `zone := base.zone`) is modeled DIRECTLY in the transparent frozen deep model `shiftReference`, not behind an axiom => no axiom/deep-model trust point to break. Correspondence to the real callee holds: `datetime.datetime(..., tzinfo=d.tzinfo)` is the language value constructor (modeled by the Instant literal), not a foreign callee; `monthLen m = MONTHS_DAYS[m-1]` for m∈1..12 (concrete repo data, transliterated). No ungrounded oracle: `shiftReference` is a transparent `def`, so the only satisfying 'echo' (pos_control) is the correct value.

VERDICT: SOUND. 8 genuinely-wrong same-spec impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch) all FAIL verification on the single discriminating clause; pos_control verifies (non-vacuous); the only other verifying impl (atk_9) is correct and its materialized faithful patch RESOLVES under the official harness. No verify⇏correct witness exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_9.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec `ensures out = shiftReference base years months` is exact structural equality against a transparent, fully-concrete deterministic deep model in the FROZEN pure region. No verifying-but-wrong impl exists: the two verifying same-spec impls (pos_control, atk_9) are correct on the reachable domain, and atk_9's faithful patch (= the gold construction) RESOLVES under the official harness.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model references. The modeled behavior is a
   pure data-flow that builds a shifted reference instant from the components of
   a source instant and a whole-unit (years, months) offset; every component is
   read directly from the inputs, nothing is delegated to an unchanged foreign
   callee (mapping.md §3). G-AX therefore has nothing to check. -/
-- axioms-end

-- pure-start
/- An instant on the calendar, separated into the components a later difference
   is computed from. `zone` records the time-zone designation the instant is
   expressed against: `none` is a floating instant (no designation), `some k` is
   an instant anchored to designation `k`. Two instants can only be compared /
   subtracted when they share the same designation status — a floating instant
   and an anchored one are not on a common timeline. -/
structure Instant where
  y    : Nat
  mo   : Nat
  d    : Nat
  h    : Nat
  mi   : Nat
  s    : Nat
  zone : Option Nat
deriving DecidableEq, Repr, Inhabited

/- The number of days in a (1-indexed) calendar month, the constant table used
   to clamp a day-of-month onto a target month. February is the common-year length;
   the clamp only ever caps an out-of-range day, so the leap-year case is not
   distinguished here. -/
def monthLen : Nat → Nat
  | 1  => 31 | 2  => 28 | 3  => 31 | 4  => 30 | 5  => 31 | 6  => 30
  | 7  => 31 | 8  => 31 | 9  => 30 | 10 => 31 | 11 => 30 | 12 => 31
  | _  => 30

/- Build the reference instant obtained by shifting `base` forward by whole
   `years` and `months`. The shifted month is normalized back into 1..12,
   carrying into the year when it overflows; the day-of-month is clamped to the
   target month's length so an end-of-month source never names a non-existent
   day; the hour/minute/second are carried across verbatim. Crucially the
   reference is expressed against the SAME time-zone designation as `base`
   (`zone := base.zone`): the shifted reference must lie on the same timeline as
   the source so that a later difference between the reference and another
   instant on that timeline is well-defined. -/
def shiftReference (base : Instant) (years months : Nat) : Instant :=
  let py  := base.y + years
  let pm  := base.mo + months
  let py' := if pm > 12 then py + 1 else py
  let pm' := if pm > 12 then pm - 12 else pm
  { y    := py',
    mo   := pm',
    d    := min (monthLen pm') base.d,
    h    := base.h,
    mi   := base.mi,
    s    := base.s,
    zone := base.zone }

@[grind] lemma shiftReference_def (base : Instant) (years months : Nat) :
    shiftReference base years months =
      (let py  := base.y + years
       let pm  := base.mo + months
       let py' := if pm > 12 then py + 1 else py
       let pm' := if pm > 12 then pm - 12 else pm
       { y    := py',
         mo   := pm',
         d    := min (monthLen pm') base.d,
         h    := base.h,
         mi   := base.mi,
         s    := base.s,
         zone := base.zone : Instant }) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the reference instant used to measure the leftover span after whole
   years and months have been accounted for. `base` is read-only (not `mut`):
   the builder only reads its components and returns a fresh instant. The
   reference is the source shifted forward by `years`/`months`, normalized onto
   a real calendar day, and — the property the leftover-span measurement
   depends on — expressed against the SAME time-zone designation as `base`, so
   the two lie on a common timeline. The whole-unit offset is the result of a
   division by twelve, so `months ≤ 11`; this site is only reached when at least
   one whole unit elapsed. -/
method buildShiftedReference (base : Instant) (years : Nat) (months : Nat) return (out : Instant)
  require 1 ≤ base.mo ∧ base.mo ≤ 12
  require months ≤ 11
  require 0 < years ∨ 0 < months
  ensures out = shiftReference base years months
  do
    -- impl-start
    return shiftReference base years months
    -- impl-end

prove_correct buildShiftedReference by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: python python; verify via `bash scripts/lean_verify.sh <f>`. All 9 attack files + pos_control confirmed same_spec=True vs Solution.lean (velvet backend); edits confined to the impl region.

### VERIFY RESULTS (exit codes):
- pos_control (`return shiftReference base years months`; structurally-distinct correct): exit 0 => spec NON-VACUOUS.
- atk_1 prepatch bug (`zone := none`): exit 1. Fails exactly on `ensures_1: out = shiftReference ...` at the `zone := none` vs `zone := base.zone` field — the gold-added `tzinfo=d.tzinfo`. PREPATCH REPRODUCED.
- atk_2 (drop day clamp, `d := base.d`): exit 1 (caught at `d`).
- atk_3 (drop month-overflow normalization, raw pm/py): exit 1.
- atk_4 (swap years/months): exit 1.
- atk_5 (control-flow-effect partial-domain: `zone := if base.mo = 12 then none else base.zone`; base.mo=12 is IN-DOMAIN & reachable): exit 1 => partial-domain infidelity caught.
- atk_6 (ungrounded-oracle echo probe `return (default : Instant)`): exit 1.
- atk_7 (boundary: clamp with pre-normalization `monthLen pm` not `monthLen pm'`): exit 1.
- atk_8 (hardcode `zone := some 0` regardless of base.zone): exit 1.
- atk_9 (dead-branch probe: `if 0 < years ∨ 0 < months then shiftReference ... else default`): exit 0 => VERIFIES. The else branch is DEAD because `require 0 < years ∨ 0 < months` holds on the reachable domain — mirrors gold's `if years or months:` guard.

RESOLVE RUN (mandatory for verifying wrong-impl): atk_9's faithful refined patch is the gold construction (its reachable behavior == shiftReference == gold `tzinfo=d.tzinfo`; dead else refines to gold's `else: pivot = d`). Ran `harness.run_resolve('django__django-16429', <atk_9.patch>, timeout=1800, retries=0)` => RESOLVED=True, COMPLETED=True; FAIL_TO_PASS 4/4 success (test_depth, test_depth_invalid, 'Test other units', test_thousand_years_ago), PASS_TO_PASS 21/21 success, 0 failures. So atk_9 does NOT break the spec — it is a correct impl (verify⇒resolve holds). No verifying-but-wrong impl's faithful patch fails to resolve.

REFINEMENT AUDIT (refinement.md): legs A1-A8 are all R or I; NO A-consumed / A-reference legs and NO kind-3 step (consistent with meta.json axioms=[], deep_model_references=[], G-AX skip). The genuinely-changed op A7 (propagate tzinfo => `zone := base.zone`) is modeled DIRECTLY in the transparent frozen deep model `shiftReference`, not behind an axiom => no axiom/deep-model trust point to break. Correspondence to the real callee holds: `datetime.datetime(..., tzinfo=d.tzinfo)` is the language value constructor (modeled by the Instant literal), not a foreign callee; `monthLen m = MONTHS_DAYS[m-1]` for m∈1..12 (concrete repo data, transliterated). No ungrounded oracle: `shiftReference` is a transparent `def`, so the only satisfying 'echo' (pos_control) is the correct value.

VERDICT: SOUND. 8 genuinely-wrong same-spec impls (partial-domain, boundary, control-flow-effect, ungrounded-oracle echo, prepatch) all FAIL verification on the single discriminating clause; pos_control verifies (non-vacuous); the only other verifying impl (atk_9) is correct and its materialized faithful patch RESOLVES under the official harness. No verify⇏correct witness exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness/drift audit of velvet bundle django__django-16429 (buildShiftedReference / shiftReference deep model). (1) Spec-region byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend)=True — the frozen spec (Instant, monthLen, shiftReference, method sig + require/ensures) is identical; only the elided impl differs (prepatch: zone:=none discriminator). (2) Model faithfully mirrors the post-patch repo callee: the ensures 'out = shiftReference base years months' maps field-by-field to the gold pivot = datetime.datetime(pivot_year, pivot_month, min(MONTHS_DAYS[pivot_month-1], d.day), d.hour, d.minute, d.second, tzinfo=d.tzinfo). monthLen == MONTHS_DAYS verbatim (Feb=28 common-year, matches Python's leap-day clamp to 28); month-overflow arithmetic identical (pm<=23, single -12 normalizes to 1..12); min-clamp, h/m/s carry, and zone/tzinfo propagation all match. (3) Fuzz over 500k reachable (d,now) pairs, deriving years/months exactly as timesince() does: 0 model-vs-real mismatches; the datetime year-overflow ValueError case is NOT reachable given require months<=11 and 1<=base.mo<=12, which faithfully reflect the reachable domain (divmod(_,12) => months in 0..11; month in 1..12). Preconditions are sound domain restrictions, not spec over-strengthening. (4) lean_verify.sh on Solution.lean -> exit 0. No diverging input found; spec is neither too strong nor drifting from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec-identity confirmed: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) = True — the spec region (structure Instant, monthLen, shiftReference, the buildShiftedReference method signature/require/ensures, and all doc-comments) is byte-identical between gold and prepatch; the ONLY difference is the impl region (zone := base.zone vs zone := none), which is elided from the consumer spec view. So nothing in the discriminating impl leaks.

Gold edit: add `tzinfo=d.tzinfo,` to the pivot `datetime.datetime(...)` constructor in timesince() (django/utils/timesince.py:97) — i.e. the shifted reference must carry the source datetime's tz designation; the single behavioral change.

This exact fix is ALREADY fully public in the problem_statement (NOT hints_text): 'the pivot instantiated here ... does not take into account the datetime object's tzinfo. Adding 0, d.tzinfo arguments to the datetime.datetime call seems to fix this.' The problem statement even links the exact source lines (L93-L100) and names the fix.

The spec view's modeling of the fix as `zone := base.zone` (with the doc-comment 'expressed against the SAME time-zone designation as base') therefore discloses nothing beyond what the public problem_statement already states outright. The remaining spec content — month-overflow carry, MONTHS_DAYS/monthLen day-clamp, h/mi/s carry-overs — describes UNCHANGED surrounding code already visible at the publicly-linked source lines and is not the gold edit. No spec-view line reveals the gold edit more specifically than the public problem_statement. G-LEAK lexical screen also passed (spec view clean). No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
