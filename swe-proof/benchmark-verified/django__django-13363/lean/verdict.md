# P2 adversarial audit — django__django-13363

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec not broken. The only two same-spec impls whose correct_* closes with clean axioms (atk_8 alternative match-based control flow; atk_9 ungrounded-oracle echo of the spec RHS) are both behaviorally faithful to gold get_tzname(); their materialized faithful patches BOTH resolve under the official harness (RESOLVED=True), same as gold. All 7 genuinely-wrong impls fail to close (exit 1).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -57,9 +57,7 @@
     (currentZone : String) : String := Id.run do
   let mut tzname : Option String := none
   if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
+    tzname := some currentZone
   return castDate lhs tzname
 -- impl-end
 
@@ -91,9 +89,7 @@
     (currentZone : String) : String := Id.run do
   let mut tzname : Option String := none
   if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
+    tzname := some currentZone
   return castTime lhs tzname
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,9 +91,7 @@
     (currentZone : String) : String := Id.run do
   let mut tzname : Option String := none
   if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
+    tzname := some currentZone
   return castTime lhs tzname
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,7 @@
 def implementation_truncDateCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
-  if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castDate lhs tzname
+  return castDate lhs (some (requestedZone.getD currentZone))
 -- impl-end
 
 -- proof-start
@@ -89,12 +84,7 @@
 def implementation_truncTimeCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
-  if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castTime lhs tzname
+  return castTime lhs (some (requestedZone.getD currentZone))
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -59,7 +59,7 @@
   if useTz then
     match requestedZone with
     | none => tzname := some currentZone
-    | some z => tzname := some z
+    | some _ => tzname := some currentZone
   return castDate lhs tzname
 -- impl-end
 
@@ -93,7 +93,7 @@
   if useTz then
     match requestedZone with
     | none => tzname := some currentZone
-    | some z => tzname := some z
+    | some _ => tzname := some currentZone
   return castTime lhs tzname
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
     match requestedZone with
     | none => tzname := some currentZone
     | some z => tzname := some z
-  return castDate lhs tzname
+  return castTime lhs tzname
 -- impl-end
 
 -- proof-start
@@ -94,7 +94,7 @@
     match requestedZone with
     | none => tzname := some currentZone
     | some z => tzname := some z
-  return castTime lhs tzname
+  return castDate lhs tzname
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
     match requestedZone with
     | none => tzname := some currentZone
     | some z => tzname := some z
-  return castDate lhs tzname
+  return castDate (lhs ++ "!") tzname
 -- impl-end
 
 -- proof-start
@@ -94,7 +94,7 @@
     match requestedZone with
     | none => tzname := some currentZone
     | some z => tzname := some z
-  return castTime lhs tzname
+  return castTime (lhs ++ "!") tzname
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,12 +55,7 @@
 def implementation_truncDateCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
-  if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castDate lhs tzname
+  return castDate lhs (some "UTC")
 -- impl-end
 
 -- proof-start
@@ -89,12 +84,7 @@
 def implementation_truncTimeCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
-  if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castTime lhs tzname
+  return castTime lhs (some "UTC")
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,12 +55,12 @@
 def implementation_truncDateCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
   if useTz then
     match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castDate lhs tzname
+    | some z => return castDate lhs (some z)
+    | none   => return castDate lhs (some currentZone)
+  else
+    return castDate lhs none
 -- impl-end
 
 -- proof-start
@@ -89,12 +89,12 @@
 def implementation_truncTimeCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
   if useTz then
     match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castTime lhs tzname
+    | some z => return castTime lhs (some z)
+    | none   => return castTime lhs (some currentZone)
+  else
+    return castTime lhs none
 -- impl-end
 
 -- proof-start
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -55,12 +55,7 @@
 def implementation_truncDateCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
-  if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castDate lhs tzname
+  return castDate lhs (conversionZoneName useTz requestedZone currentZone)
 -- impl-end
 
 -- proof-start
@@ -89,12 +84,7 @@
 def implementation_truncTimeCast
     (lhs : String) (useTz : Bool) (requestedZone : Option String)
     (currentZone : String) : String := Id.run do
-  let mut tzname : Option String := none
-  if useTz then
-    match requestedZone with
-    | none => tzname := some currentZone
-    | some z => tzname := some z
-  return castTime lhs tzname
+  return castTime lhs (conversionZoneName useTz requestedZone currentZone)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing the database cast that turns a stored timestamp expression into a
date value (and, separately, into a time value).

Each cast is built from an already-compiled inner SQL fragment and a *conversion
zone*. The conversion zone is determined by a flag that says whether
timezone-aware conversion is in effect, together with two zone names: a
caller-requested zone (which may be absent) and an ambient default zone.

The required behavior is: when timezone-aware conversion is OFF, no conversion
zone is used. When it is ON, the conversion zone is the caller-requested zone if
one was supplied, and otherwise the ambient default zone. The compiled inner
fragment is passed through unchanged, and the chosen conversion zone is handed to
the appropriate per-flavour cast.
-/

-- axioms-start
-- The per-flavour database casts are UNCHANGED collaborators: each turns a
-- compiled SQL fragment plus an optional conversion zone into the cast SQL. They
-- are declared as opaque signatures so they can appear in the executable impl;
-- they are applied identically on the specification and implementation sides, so
-- no behavioral axiom about them is consumed (the proof agent may add a `_prop`
-- only if it gets stuck). The conversion-zone selection itself — the behavior
-- this specification pins — is modeled DEEPLY below, not axiomatized.
opaque castDate : String → Option String → String
opaque castTime : String → Option String → String
-- axioms-end

-- pure-start
/-- The conversion zone used when building the cast.

When timezone-aware conversion is off there is no conversion zone. When it is on,
a caller-requested zone takes precedence over the ambient default: the requested
zone is used when present, falling back to the ambient default otherwise. -/
def conversionZoneName (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : Option String :=
  if useTz then some (requestedZone.getD currentZone) else none
-- pure-end

-- post-conditions-start
/-- The date cast SQL is exactly the unchanged per-flavour date cast applied to
the unchanged compiled inner fragment and the selected conversion zone. The inner
fragment is pinned to its input (frame); only the conversion zone depends on the
flag and the supplied/ambient zones. -/
def problem_spec_truncDateCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) (result : String) : Prop :=
  result = castDate lhs (conversionZoneName useTz requestedZone currentZone)
-- post-conditions-end

-- impl-start
def implementation_truncDateCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : String := Id.run do
  let mut tzname : Option String := none
  if useTz then
    match requestedZone with
    | none => tzname := some currentZone
    | some z => tzname := some z
  return castDate lhs tzname
-- impl-end

-- proof-start
theorem correct_truncDateCast :
    ∀ (lhs : String) (useTz : Bool) (requestedZone : Option String)
      (currentZone : String),
      problem_spec_truncDateCast lhs useTz requestedZone currentZone
        (implementation_truncDateCast lhs useTz requestedZone currentZone) := by
  intro lhs useTz requestedZone currentZone
  unfold problem_spec_truncDateCast implementation_truncDateCast conversionZoneName
  cases useTz <;> cases requestedZone <;> rfl
-- proof-end

-- post-conditions-start
/-- The time cast SQL is exactly the unchanged per-flavour time cast applied to
the unchanged compiled inner fragment and the selected conversion zone. The inner
fragment is pinned to its input (frame); only the conversion zone depends on the
flag and the supplied/ambient zones. -/
def problem_spec_truncTimeCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) (result : String) : Prop :=
  result = castTime lhs (conversionZoneName useTz requestedZone currentZone)
-- post-conditions-end

-- impl-start
def implementation_truncTimeCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : String := Id.run do
  let mut tzname : Option String := none
  if useTz then
    match requestedZone with
    | none => tzname := some currentZone
    | some z => tzname := some z
  return castTime lhs tzname
-- impl-end

-- proof-start
theorem correct_truncTimeCast :
    ∀ (lhs : String) (useTz : Bool) (requestedZone : Option String)
      (currentZone : String),
      problem_spec_truncTimeCast lhs useTz requestedZone currentZone
        (implementation_truncTimeCast lhs useTz requestedZone currentZone) := by
  intro lhs useTz requestedZone currentZone
  unfold problem_spec_truncTimeCast implementation_truncTimeCast conversionZoneName
  cases useTz <;> cases requestedZone <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Backend=lean, instance=django__django-13363. same_spec=True for all 9 attacks (verified via swebench_unified.markers.same_spec against Solution.lean; spec_view collapses BOTH impl and proof regions, so only axioms/pure/pre/post are compared — those were kept byte-identical). Positive control (gold Solution.lean) verifies exit 0.

SPEC SHAPE: exact TOTAL functional equality, result = castX lhs (conversionZoneName useTz requestedZone currentZone), universally quantified over all inputs; castDate/castTime opaque and applied IDENTICALLY on spec & impl sides (I-tagged, no axiom consumed); conversionZoneName is a CONCRETE deep model (if useTz then some (requestedZone.getD currentZone) else none) — NOT an axiomatic oracle, so it is not oracle-hackable beyond emitting the exact zone.

### ATTACK RESULTS (lean_verify.sh, cap 300s, from project root):
- atk_1 prepatch bug (both sites drop requestedZone, emit some currentZone): exit 1 REJECTED (reproduces the F2P bug). cmd: bash scripts/lean_verify.sh .../atk_1.lean
- atk_2 partial-domain (date correct, time buggy): exit 1 REJECTED
- atk_3 ignore useTz (always some (getD)): exit 1 REJECTED
- atk_4 reversed precedence (ambient over requested when both present): exit 1 REJECTED
- atk_5 control-flow-effect (swapped casts castTime in date fn / castDate in time fn): exit 1 REJECTED
- atk_6 frame violation (castX (lhs ++ "!") tzname): exit 1 REJECTED
- atk_7 ungrounded constant zone (some "UTC"): exit 1 REJECTED
- atk_8 alternative correct control flow (match on requestedZone with early returns): exit 0 CLOSES. #print axioms correct_truncDateCast/correct_truncTimeCast => 'does not depend on any axioms' (clean). MATERIALIZED faithful patch = gold self.get_tzname() delegation; git apply --check OK; run_resolve('django__django-13363', patch_8) => ResolveResult.resolved=True (completed path).
- atk_9 ungrounded-oracle echo (impl literally returns castX lhs (conversionZoneName useTz requestedZone currentZone)): exit 0 CLOSES. #print axioms => clean (no axioms). MATERIALIZED faithful patch = inlined closed-form of get_tzname (requested-over-ambient under USE_TZ else None); git apply --check OK; run_resolve => resolved=True.

BASELINE: gold patch.diff run_resolve => resolved=True (harness discriminates correctly for this instance). ResolveResult.resolved=True is reachable only via the completed-report path (harness.py:137), so it is authoritative.

CONCLUSION: every same-spec impl with a clean-axiom closing proof is behaviorally correct AND its faithful patch RESOLVES. No verify-but-not-resolve gap => spec is TIGHT. verify => correct holds.

REFINEMENT.MD AUDIT (A-legs focus): Leg1 lhs=str<->String (R). Leg2 zone-selection = the CHANGED op, modeled DEEPLY as conversionZoneName (R, NOT axiomatized) — closed form of TimezoneMixin.get_tzname control flow. Leg3 castX = UNCHANGED callee applied identically on both sides (I, opaque signature, no axiom consumed). Leg4 return/lhs_params out of scope (I). A-consumed: NONE (confirmed by clean #print axioms on the gold proof structure and all closing attacks). A-reference: timezone._get_timezone_name(self.tzinfo) modeled as identity on the carried zone name (Option String <-> tzinfo bijection), validated by axiom_check.py / G-AX running the REAL callees (get_tzname surfaces requested zone over ambient under USE_TZ, None when off). No kind-3 (changed-inexpressible) leg. Correspondence to real callees holds. R/I legs mechanically covered by G-CONF (conformance_check.py present in bundle).

Parallelism: attack verifications and the 3 resolve runs (patch_8, patch_9, gold) were launched as concurrent background Bash jobs (<=4 at a time) and collected; schedule only, pass criteria unchanged.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — spec not broken. The only two same-spec impls whose correct_* closes with clean axioms (atk_8 alternative match-based control flow; atk_9 ungrounded-oracle echo of the spec RHS) are both behaviorally faithful to gold get_tzname(); their materialized faithful patches BOTH resolve under the official harness (RESOLVED=True), same as gold. All 7 genuinely-wrong impls fail to close (exit 1).
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

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing the database cast that turns a stored timestamp expression into a
date value (and, separately, into a time value).

Each cast is built from an already-compiled inner SQL fragment and a *conversion
zone*. The conversion zone is determined by a flag that says whether
timezone-aware conversion is in effect, together with two zone names: a
caller-requested zone (which may be absent) and an ambient default zone.

The required behavior is: when timezone-aware conversion is OFF, no conversion
zone is used. When it is ON, the conversion zone is the caller-requested zone if
one was supplied, and otherwise the ambient default zone. The compiled inner
fragment is passed through unchanged, and the chosen conversion zone is handed to
the appropriate per-flavour cast.
-/

-- axioms-start
-- The per-flavour database casts are UNCHANGED collaborators: each turns a
-- compiled SQL fragment plus an optional conversion zone into the cast SQL. They
-- are declared as opaque signatures so they can appear in the executable impl;
-- they are applied identically on the specification and implementation sides, so
-- no behavioral axiom about them is consumed (the proof agent may add a `_prop`
-- only if it gets stuck). The conversion-zone selection itself — the behavior
-- this specification pins — is modeled DEEPLY below, not axiomatized.
opaque castDate : String → Option String → String
opaque castTime : String → Option String → String
-- axioms-end

-- pure-start
/-- The conversion zone used when building the cast.

When timezone-aware conversion is off there is no conversion zone. When it is on,
a caller-requested zone takes precedence over the ambient default: the requested
zone is used when present, falling back to the ambient default otherwise. -/
def conversionZoneName (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : Option String :=
  if useTz then some (requestedZone.getD currentZone) else none
-- pure-end

-- post-conditions-start
/-- The date cast SQL is exactly the unchanged per-flavour date cast applied to
the unchanged compiled inner fragment and the selected conversion zone. The inner
fragment is pinned to its input (frame); only the conversion zone depends on the
flag and the supplied/ambient zones. -/
def problem_spec_truncDateCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) (result : String) : Prop :=
  result = castDate lhs (conversionZoneName useTz requestedZone currentZone)
-- post-conditions-end

-- impl-start
def implementation_truncDateCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : String := Id.run do
  let mut tzname : Option String := none
  if useTz then
    match requestedZone with
    | none => tzname := some currentZone
    | some z => tzname := some z
  return castDate lhs tzname
-- impl-end

-- proof-start
theorem correct_truncDateCast :
    ∀ (lhs : String) (useTz : Bool) (requestedZone : Option String)
      (currentZone : String),
      problem_spec_truncDateCast lhs useTz requestedZone currentZone
        (implementation_truncDateCast lhs useTz requestedZone currentZone) := by
  intro lhs useTz requestedZone currentZone
  unfold problem_spec_truncDateCast implementation_truncDateCast conversionZoneName
  cases useTz <;> cases requestedZone <;> rfl
-- proof-end

-- post-conditions-start
/-- The time cast SQL is exactly the unchanged per-flavour time cast applied to
the unchanged compiled inner fragment and the selected conversion zone. The inner
fragment is pinned to its input (frame); only the conversion zone depends on the
flag and the supplied/ambient zones. -/
def problem_spec_truncTimeCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) (result : String) : Prop :=
  result = castTime lhs (conversionZoneName useTz requestedZone currentZone)
-- post-conditions-end

-- impl-start
def implementation_truncTimeCast
    (lhs : String) (useTz : Bool) (requestedZone : Option String)
    (currentZone : String) : String := Id.run do
  let mut tzname : Option String := none
  if useTz then
    match requestedZone with
    | none => tzname := some currentZone
    | some z => tzname := some z
  return castTime lhs tzname
-- impl-end

-- proof-start
theorem correct_truncTimeCast :
    ∀ (lhs : String) (useTz : Bool) (requestedZone : Option String)
      (currentZone : String),
      problem_spec_truncTimeCast lhs useTz requestedZone currentZone
        (implementation_truncTimeCast lhs useTz requestedZone currentZone) := by
  intro lhs useTz requestedZone currentZone
  unfold problem_spec_truncTimeCast implementation_truncTimeCast conversionZoneName
  cases useTz <;> cases requestedZone <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Backend=lean, instance=django__django-13363. same_spec=True for all 9 attacks (verified via swebench_unified.markers.same_spec against Solution.lean; spec_view collapses BOTH impl and proof regions, so only axioms/pure/pre/post are compared — those were kept byte-identical). Positive control (gold Solution.lean) verifies exit 0.

SPEC SHAPE: exact TOTAL functional equality, result = castX lhs (conversionZoneName useTz requestedZone currentZone), universally quantified over all inputs; castDate/castTime opaque and applied IDENTICALLY on spec & impl sides (I-tagged, no axiom consumed); conversionZoneName is a CONCRETE deep model (if useTz then some (requestedZone.getD currentZone) else none) — NOT an axiomatic oracle, so it is not oracle-hackable beyond emitting the exact zone.

### ATTACK RESULTS (lean_verify.sh, cap 300s, from project root):
- atk_1 prepatch bug (both sites drop requestedZone, emit some currentZone): exit 1 REJECTED (reproduces the F2P bug). cmd: bash scripts/lean_verify.sh .../atk_1.lean
- atk_2 partial-domain (date correct, time buggy): exit 1 REJECTED
- atk_3 ignore useTz (always some (getD)): exit 1 REJECTED
- atk_4 reversed precedence (ambient over requested when both present): exit 1 REJECTED
- atk_5 control-flow-effect (swapped casts castTime in date fn / castDate in time fn): exit 1 REJECTED
- atk_6 frame violation (castX (lhs ++ "!") tzname): exit 1 REJECTED
- atk_7 ungrounded constant zone (some "UTC"): exit 1 REJECTED
- atk_8 alternative correct control flow (match on requestedZone with early returns): exit 0 CLOSES. #print axioms correct_truncDateCast/correct_truncTimeCast => 'does not depend on any axioms' (clean). MATERIALIZED faithful patch = gold self.get_tzname() delegation; git apply --check OK; run_resolve('django__django-13363', patch_8) => ResolveResult.resolved=True (completed path).
- atk_9 ungrounded-oracle echo (impl literally returns castX lhs (conversionZoneName useTz requestedZone currentZone)): exit 0 CLOSES. #print axioms => clean (no axioms). MATERIALIZED faithful patch = inlined closed-form of get_tzname (requested-over-ambient under USE_TZ else None); git apply --check OK; run_resolve => resolved=True.

BASELINE: gold patch.diff run_resolve => resolved=True (harness discriminates correctly for this instance). ResolveResult.resolved=True is reachable only via the completed-report path (harness.py:137), so it is authoritative.

CONCLUSION: every same-spec impl with a clean-axiom closing proof is behaviorally correct AND its faithful patch RESOLVES. No verify-but-not-resolve gap => spec is TIGHT. verify => correct holds.

REFINEMENT.MD AUDIT (A-legs focus): Leg1 lhs=str<->String (R). Leg2 zone-selection = the CHANGED op, modeled DEEPLY as conversionZoneName (R, NOT axiomatized) — closed form of TimezoneMixin.get_tzname control flow. Leg3 castX = UNCHANGED callee applied identically on both sides (I, opaque signature, no axiom consumed). Leg4 return/lhs_params out of scope (I). A-consumed: NONE (confirmed by clean #print axioms on the gold proof structure and all closing attacks). A-reference: timezone._get_timezone_name(self.tzinfo) modeled as identity on the carried zone name (Option String <-> tzinfo bijection), validated by axiom_check.py / G-AX running the REAL callees (get_tzname surfaces requested zone over ambient under USE_TZ, None when off). No kind-3 (changed-inexpressible) leg. Correspondence to real callees holds. R/I legs mechanically covered by G-CONF (conformance_check.py present in bundle).

Parallelism: attack verifications and the 3 resolve runs (patch_8, patch_9, gold) were launched as concurrent background Bash jobs (<=4 at a time) and collected; schedule only, pass criteria unchanged.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-13363 lean bundle. No diverging input exists; the modeled functions agree with the real repo callee everywhere on the modeled surface.

### Verification performed
1. Lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry).
2. `#print axioms correct_truncDateCast` / `correct_truncTimeCast` => both 'does not depend on any axioms' (proof is genuine, no sorryAx). No behavioral axiom consumed; opaque castDate/castTime are signatures only, applied identically on spec and impl sides.
3. same_spec(Solution.lean, Solution_prepatch.lean) = True and same_spec(Solution.lean, Solution_prepatch_2.lean) = True (spec region byte-identical; prepatch differs only in the impl block, matching the documented F2P discriminator).
4. Ran the bundle's conformance_check.py against the REAL base_commit worktree code: G-CONF OK, 240036 renderings (all boundary cases + 120k random USE_TZ x tzinfo configs, x2 methods), 0 disagreements between the deep-model shadow conversionZoneName and the real patched TimezoneMixin.get_tzname().
5. Ran axiom_check.py against the real worktree: status ok; the A-reference bijection (self.tzinfo modeled by _get_timezone_name's extracted zone name) validated on 8 named zones plus None, across USE_TZ on/off.

OVER-STRENGTH ANALYSIS: The spec conversionZoneName useTz requestedZone currentZone = (if useTz then some (requestedZone.getD currentZone) else none) matches get_tzname exactly on all three branches (USE_TZ off -> None; on+no tzinfo -> ambient; on+tzinfo -> requested). currentZone is universally quantified (theorem holds for every ambient zone, so the spec is not narrower than reality). lhs passed through unchanged to the opaque cast, mirroring datetime_cast_{date,time}_sql(lhs, tzname). Dropping lhs_params is a scope reduction (patch does not touch params), not a strengthening. No input found where the modeled function disagrees with the real callee. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage / gold-reconstruction check for django__django-13363 (lean bundle). Mechanical G-LEAK screen passes (rep.passed=True, no hard failures); same_spec holds vs both Solution_prepatch.lean and Solution_prepatch_2.lean.

Gold edit: replace `tzname = timezone.get_current_timezone_name() if settings.USE_TZ else None` with `tzname = self.get_tzname()` in TruncDate.as_sql and TruncTime.as_sql (get_tzname => None if not USE_TZ, else requested tzinfo zone if present else ambient zone).

The PUBLIC problem_statement is already maximally disclosive: it names the bug (get_current_timezone_name() used unconditionally, discards passed-in tzinfo), links the exact offending line (datetime.py#L295), links the exact intended helper (datetime.py#L17 = get_tzname), and describes the desired behavior for both TruncDate and TruncTime.

Spec view (docstring + axioms + pure `conversionZoneName` + post-conditions) describes only the abstract behavior: OFF => no zone; ON => requested zone if supplied else ambient default. It uses generic modeling names (conversionZoneName, useTz, requestedZone, currentZone, opaque castDate/castTime) and does NOT mention get_tzname, get_current_timezone_name, USE_TZ, tzinfo, datetime.py, or any patch-specific token. This behavioral pin is a strict subset of — and less identifying than — what problem_statement already spells out in full (with exact function names and line numbers). Nothing in the spec view reconstructs or reveals the gold edit beyond the public problem_statement (hints_text excluded from consideration). No leaking line.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
