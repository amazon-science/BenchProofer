# P2 adversarial audit — pydata__xarray-6599

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The spec is a tight functional equality `ensures out = toNumericSpec t` under `total`/`demonic` semantics against a total spec function, so every verifying impl must be extensionally equal to toNumericSpec (= gold behavior). The only verifying wrong-shaped impl (atk_6, ungrounded-oracle echo `return toNumericSpec t`) is behaviorally identical to gold; its faithful patch = gold patch, which RESOLVED.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,14 +110,13 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
-    let out := match t.kind with
-      | .datetime => epochCount t
-      | .duration => Except.ok (durationCast t)
-      | .numeric  => Except.ok (t.raw.map NumVal.num)
+    let isTimeKind : Bool :=
+      match t.kind with
+      | .datetime => true
+      | .duration => true
+      | .numeric  => false
+    let out := if isTimeKind then epochCount t
+               else Except.ok (t.raw.map NumVal.num)
     return out
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,13 +110,9 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
     let out := match t.kind with
       | .datetime => epochCount t
-      | .duration => Except.ok (durationCast t)
+      | .duration => epochCount t
       | .numeric  => Except.ok (t.raw.map NumVal.num)
     return out
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,13 +110,10 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
     let out := match t.kind with
       | .datetime => epochCount t
-      | .duration => Except.ok (durationCast t)
+      | .duration => Except.ok (t.raw.map fun i =>
+          if i = missingCount then NumVal.nan else NumVal.num i)
       | .numeric  => Except.ok (t.raw.map NumVal.num)
     return out
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,14 +110,12 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
+    let rec spin (n : Nat) : Except ConvErr (Array NumVal) :=
+      spin (n + 1)
     let out := match t.kind with
       | .datetime => epochCount t
       | .duration => Except.ok (durationCast t)
-      | .numeric  => Except.ok (t.raw.map NumVal.num)
+      | .numeric  => spin 0
     return out
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,12 +110,8 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
     let out := match t.kind with
-      | .datetime => epochCount t
+      | .datetime => Except.ok (t.raw.map NumVal.num)
       | .duration => Except.ok (durationCast t)
       | .numeric  => Except.ok (t.raw.map NumVal.num)
     return out
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -110,14 +110,7 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
-    let out := match t.kind with
-      | .datetime => epochCount t
-      | .duration => Except.ok (durationCast t)
-      | .numeric  => Except.ok (t.raw.map NumVal.num)
+    let out := toNumericSpec t
     return out
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,14 +110,10 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
-    let out := match t.kind with
-      | .datetime => epochCount t
-      | .duration => Except.ok (durationCast t)
-      | .numeric  => Except.ok (t.raw.map NumVal.num)
+    let out :=
+      if h : t.kind = .datetime then epochCount t
+      else if t.kind = .duration then Except.ok (t.raw.map NumVal.num)
+      else Except.ok (t.raw.map NumVal.num)
     return out
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -110,14 +110,10 @@
   ensures out = toNumericSpec t
   do
     -- impl-start
-    -- Route each element kind to a conversion that is well-defined on it: a
-    -- datetime array through the epoch-relative conversion (missing values
-    -- becoming not-a-number), a duration array through the direct float cast,
-    -- and an already-numeric array straight through unchanged.
     let out := match t.kind with
       | .datetime => epochCount t
       | .duration => Except.ok (durationCast t)
-      | .numeric  => Except.ok (t.raw.map NumVal.num)
+      | .numeric  => epochCount t
     return out
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled conversion is a straight-line kind dispatch
-- over a finite array that always terminates and returns, so a diverging
-- implementation must NOT satisfy the spec (partial correctness would admit
-- it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged conversion callees this slice relies on
   — the epoch-relative datetime→number conversion (`epochCount`) and the direct
   float cast of a duration (`durationCast`) — are modeled DEEPLY in the `pure`
   region and validated == the real callees by G-AX (A-references, mapping.md
   §3), so neither carries a module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The element kind of an array's values, in the three mutually-exclusive shapes
   this conversion distinguishes: `datetime` (absolute time points), `duration`
   (timedeltas — relative spans, the kind the problem statement is about), and
   `numeric` (values that are already plain numbers). -/
inductive Kind where
  | datetime
  | duration
  | numeric
  deriving Inhabited, DecidableEq

/- A typed array: an element-kind tag together with the underlying integer
   representation of its values (for time kinds, the signed-64-bit integer count
   in the base resolution; for numeric arrays, the integer-valued payload). Only
   the kind and that integer carrier are observable to the conversion. -/
structure TypedArr where
  kind : Kind
  raw  : Array Int
  deriving Inhabited

/- The one reserved count in a time array's signed-64-bit integer carrier that
   denotes a MISSING time value ("not-a-time") rather than a real instant/span:
   the minimum representable signed-64-bit value. -/
def missingCount : Int := -9223372036854775808

/- A converted numeric value: either an exact integer-valued number, or the
   floating-point not-a-number that a missing datetime converts to. -/
inductive NumVal where
  | num (n : Int)
  | nan
  deriving Inhabited, DecidableEq

/- Failure of the epoch-relative conversion: it is undefined on a duration
   value. A duration is a relative span with no position relative to an absolute
   epoch, so re-expressing it against a reference epoch is ill-typed. -/
inductive ConvErr where
  | illTypedForDuration
  deriving Inhabited, DecidableEq

/- The epoch-relative datetime→number conversion (unchanged callee; A-reference,
   deep model — mapping.md §3.1). Re-expressing an absolute datetime array as a
   count relative to a reference epoch in the base resolution yields exactly that
   integer count — except that a MISSING datetime (the reserved count) has no
   distance to the epoch and converts to not-a-number. The operation is
   undefined on a duration value (no absolute epoch position), and it is not
   reached on an already-numeric array. -/
def epochCount (t : TypedArr) : Except ConvErr (Array NumVal) :=
  match t.kind with
  | .datetime =>
      Except.ok (t.raw.map fun i =>
        if i = missingCount then NumVal.nan else NumVal.num i)
  | _         => Except.error .illTypedForDuration

/- The direct float cast of a duration array (unchanged callee; A-reference, deep
   model — mapping.md §3.2). Casting a duration to its floating-point numeric
   value preserves the signed-64-bit integer count in the base resolution exactly
   — including the reserved missing-value count, which this direct cast does NOT
   special-case: it comes through as that count's plain numeric value. -/
def durationCast (t : TypedArr) : Array NumVal := t.raw.map NumVal.num

/- The intended numeric representation of a typed array:
     * a datetime array is re-expressed against a reference epoch (`epochCount`),
       its missing values becoming not-a-number;
     * a duration array is cast directly to its numeric value (`durationCast`);
     * an already-numeric array passes through unchanged.
   Both time kinds therefore yield a well-defined numeric array — the duration
   kind via the direct cast, NOT via the epoch conversion that is ill-typed on
   it. -/
def toNumericSpec (t : TypedArr) : Except ConvErr (Array NumVal) :=
  match t.kind with
  | .datetime => epochCount t
  | .duration => Except.ok (durationCast t)
  | .numeric  => Except.ok (t.raw.map NumVal.num)

@[grind] lemma toNumericSpec_datetime (t : TypedArr) (h : t.kind = .datetime) :
    toNumericSpec t = epochCount t := by simp [toNumericSpec, h]
@[grind] lemma toNumericSpec_duration (t : TypedArr) (h : t.kind = .duration) :
    toNumericSpec t = Except.ok (durationCast t) := by simp [toNumericSpec, h]
@[grind] lemma toNumericSpec_numeric (t : TypedArr) (h : t.kind = .numeric) :
    toNumericSpec t = Except.ok (t.raw.map NumVal.num) := by simp [toNumericSpec, h]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method toNumeric (t : TypedArr) return (out : Except ConvErr (Array NumVal))
  ensures out = toNumericSpec t
  do
    -- impl-start
    let out := match t.kind with
      | .datetime => epochCount t
      | .duration => Except.ok (durationCast t)
      | .numeric  => Except.ok (t.raw.map NumVal.num)
    return out
    -- impl-end

prove_correct toNumeric by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC HOLDS (verify => correct). Protocol executed; same_spec=True for all 9 files (byte-identical axioms/pure/pre/post; only impl region edited). Verify command: `bash scripts/lean_verify.sh <file>` from project root.

### Verify results
- atk_pos (correct impl, positive control): EXIT 0 = VERIFIES. 
- atk_1 (prepatch bug: BOTH time kinds -> epochCount, numeric passthrough): EXIT 1 FAIL, unsolved goal `out = toNumericSpec t` on duration case (spec wants .ok(durationCast) but prepatch gives .error). Prepatch bug reproduced as non-verifying same-spec impl.
- atk_2 (partial-domain: duration -> epochCount): EXIT 1 FAIL (unsolved goals, line 120). epochCount is .error on duration, spec demands .ok.
- atk_3 (boundary: duration branch special-cases missingCount->nan): EXIT 1 FAIL (unsolved goals, line 121). durationCast does NOT special-case NaT count; differs at i=missingCount.
- atk_4 (control-flow-effect: divergent `spin` loop on numeric branch): EXIT 1 FAIL. Total-correctness semantics rejects: `fail to show termination for toNumeric.spin` + unsolved ensures. Confirms total semantics excludes diverging impls.
- atk_5 (datetime branch drops NaT->nan special-case, returns raw.map num): EXIT 1 FAIL (unsolved goals, line 120). Differs from epochCount at missing datetime positions.
- atk_6 (ungrounded-oracle echo: `return toNumericSpec t`): EXIT 0 = VERIFIES. Behaviorally == gold. Faithful patch = gold patch verbatim. run_resolve('pydata__xarray-6599', gold_patch) => RESOLVED: True (harness ran, msg 'resolved', run_id sbu-resolve-audit-eq-t3ica-atk6, output at resolve_atk6.out). Does NOT break the spec.
- atk_7 (behaviorally-equal dependent-if rewrite): EXIT 1 FAIL (unsolved goals) — loom_solve does not close the extensional-equality goal for this syntactic form; non-verifying, so cannot break the spec.
- atk_8 (numeric -> epochCount, returns .error on numeric): EXIT 1 FAIL (unsolved goals, line 120).

RESOLVE EXECUTED: atk_6's materialized faithful patch (gold patch) ran through official run_resolve harness (Docker) => RESOLVED: True. No verifying wrong impl produced a non-resolving faithful patch.

REFINEMENT.MD AUDIT: legs A1 (R), A2 (I+R), A3 (A-reference), A4 (I+R+A-reference), A5 (I+R). No kind-3 (inexpressible-changed-op) legs. No consumed axioms (axioms-start/end empty). Both A-references map to real UNCHANGED callees: epochCount<->datetime_to_numeric(offset=1970-01-01,unit=ns) at duck_array_ops.py:388, durationCast<->x.astype(float); both validated ==real callee by G-AX (axiom_check.py runs real callees in-container incl. NaT-bearing arrays). Correspondence holds: the CHANGED op (kind dispatch split m|M -> M / elif m) is modeled DIRECTLY as the `match t.kind` in impl + toNumericSpec, not hidden behind an axiom. The discriminating behavior (duration routed to durationCast=.ok(raw.map num), NOT epochCount=.error) is exactly what atk_1/atk_2 fail on and the gold patch fixes.

CONCLUSION: 8 attacks run (>=5 required, distinct classes: prepatch, partial-domain, boundary, control-flow/divergence, oracle-drop, ungrounded-oracle echo, equal-rewrite, wrong-numeric-route). Positive control verifies. Every verifying impl is behaviorally gold and its faithful patch RESOLVES. verify => correct upheld. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
No spec-breaking counterexample found. The spec is a tight functional equality `ensures out = toNumericSpec t` under `total`/`demonic` semantics against a total spec function, so every verifying impl must be extensionally equal to toNumericSpec (= gold behavior). The only verifying wrong-shaped impl (atk_6, ungrounded-oracle echo `return toNumericSpec t`) is behaviorally identical to gold; its faithful patch = gold patch, which RESOLVED.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Velvet.Std
-- imports-end

-- Total correctness: the modeled conversion is a straight-line kind dispatch
-- over a finite array that always terminates and returns, so a diverging
-- implementation must NOT satisfy the spec (partial correctness would admit
-- it vacuously).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two unchanged conversion callees this slice relies on
   — the epoch-relative datetime→number conversion (`epochCount`) and the direct
   float cast of a duration (`durationCast`) — are modeled DEEPLY in the `pure`
   region and validated == the real callees by G-AX (A-references, mapping.md
   §3), so neither carries a module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The element kind of an array's values, in the three mutually-exclusive shapes
   this conversion distinguishes: `datetime` (absolute time points), `duration`
   (timedeltas — relative spans, the kind the problem statement is about), and
   `numeric` (values that are already plain numbers). -/
inductive Kind where
  | datetime
  | duration
  | numeric
  deriving Inhabited, DecidableEq

/- A typed array: an element-kind tag together with the underlying integer
   representation of its values (for time kinds, the signed-64-bit integer count
   in the base resolution; for numeric arrays, the integer-valued payload). Only
   the kind and that integer carrier are observable to the conversion. -/
structure TypedArr where
  kind : Kind
  raw  : Array Int
  deriving Inhabited

/- The one reserved count in a time array's signed-64-bit integer carrier that
   denotes a MISSING time value ("not-a-time") rather than a real instant/span:
   the minimum representable signed-64-bit value. -/
def missingCount : Int := -9223372036854775808

/- A converted numeric value: either an exact integer-valued number, or the
   floating-point not-a-number that a missing datetime converts to. -/
inductive NumVal where
  | num (n : Int)
  | nan
  deriving Inhabited, DecidableEq

/- Failure of the epoch-relative conversion: it is undefined on a duration
   value. A duration is a relative span with no position relative to an absolute
   epoch, so re-expressing it against a reference epoch is ill-typed. -/
inductive ConvErr where
  | illTypedForDuration
  deriving Inhabited, DecidableEq

/- The epoch-relative datetime→number conversion (unchanged callee; A-reference,
   deep model — mapping.md §3.1). Re-expressing an absolute datetime array as a
   count relative to a reference epoch in the base resolution yields exactly that
   integer count — except that a MISSING datetime (the reserved count) has no
   distance to the epoch and converts to not-a-number. The operation is
   undefined on a duration value (no absolute epoch position), and it is not
   reached on an already-numeric array. -/
def epochCount (t : TypedArr) : Except ConvErr (Array NumVal) :=
  match t.kind with
  | .datetime =>
      Except.ok (t.raw.map fun i =>
        if i = missingCount then NumVal.nan else NumVal.num i)
  | _         => Except.error .illTypedForDuration

/- The direct float cast of a duration array (unchanged callee; A-reference, deep
   model — mapping.md §3.2). Casting a duration to its floating-point numeric
   value preserves the signed-64-bit integer count in the base resolution exactly
   — including the reserved missing-value count, which this direct cast does NOT
   special-case: it comes through as that count's plain numeric value. -/
def durationCast (t : TypedArr) : Array NumVal := t.raw.map NumVal.num

/- The intended numeric representation of a typed array:
     * a datetime array is re-expressed against a reference epoch (`epochCount`),
       its missing values becoming not-a-number;
     * a duration array is cast directly to its numeric value (`durationCast`);
     * an already-numeric array passes through unchanged.
   Both time kinds therefore yield a well-defined numeric array — the duration
   kind via the direct cast, NOT via the epoch conversion that is ill-typed on
   it. -/
def toNumericSpec (t : TypedArr) : Except ConvErr (Array NumVal) :=
  match t.kind with
  | .datetime => epochCount t
  | .duration => Except.ok (durationCast t)
  | .numeric  => Except.ok (t.raw.map NumVal.num)

@[grind] lemma toNumericSpec_datetime (t : TypedArr) (h : t.kind = .datetime) :
    toNumericSpec t = epochCount t := by simp [toNumericSpec, h]
@[grind] lemma toNumericSpec_duration (t : TypedArr) (h : t.kind = .duration) :
    toNumericSpec t = Except.ok (durationCast t) := by simp [toNumericSpec, h]
@[grind] lemma toNumericSpec_numeric (t : TypedArr) (h : t.kind = .numeric) :
    toNumericSpec t = Except.ok (t.raw.map NumVal.num) := by simp [toNumericSpec, h]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method toNumeric (t : TypedArr) return (out : Except ConvErr (Array NumVal))
  ensures out = toNumericSpec t
  do
    -- impl-start
    let out := match t.kind with
      | .datetime => epochCount t
      | .duration => Except.ok (durationCast t)
      | .numeric  => Except.ok (t.raw.map NumVal.num)
    return out
    -- impl-end

prove_correct toNumeric by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

SPEC HOLDS (verify => correct). Protocol executed; same_spec=True for all 9 files (byte-identical axioms/pure/pre/post; only impl region edited). Verify command: `bash scripts/lean_verify.sh <file>` from project root.

### Verify results
- atk_pos (correct impl, positive control): EXIT 0 = VERIFIES. 
- atk_1 (prepatch bug: BOTH time kinds -> epochCount, numeric passthrough): EXIT 1 FAIL, unsolved goal `out = toNumericSpec t` on duration case (spec wants .ok(durationCast) but prepatch gives .error). Prepatch bug reproduced as non-verifying same-spec impl.
- atk_2 (partial-domain: duration -> epochCount): EXIT 1 FAIL (unsolved goals, line 120). epochCount is .error on duration, spec demands .ok.
- atk_3 (boundary: duration branch special-cases missingCount->nan): EXIT 1 FAIL (unsolved goals, line 121). durationCast does NOT special-case NaT count; differs at i=missingCount.
- atk_4 (control-flow-effect: divergent `spin` loop on numeric branch): EXIT 1 FAIL. Total-correctness semantics rejects: `fail to show termination for toNumeric.spin` + unsolved ensures. Confirms total semantics excludes diverging impls.
- atk_5 (datetime branch drops NaT->nan special-case, returns raw.map num): EXIT 1 FAIL (unsolved goals, line 120). Differs from epochCount at missing datetime positions.
- atk_6 (ungrounded-oracle echo: `return toNumericSpec t`): EXIT 0 = VERIFIES. Behaviorally == gold. Faithful patch = gold patch verbatim. run_resolve('pydata__xarray-6599', gold_patch) => RESOLVED: True (harness ran, msg 'resolved', run_id sbu-resolve-audit-eq-t3ica-atk6, output at resolve_atk6.out). Does NOT break the spec.
- atk_7 (behaviorally-equal dependent-if rewrite): EXIT 1 FAIL (unsolved goals) — loom_solve does not close the extensional-equality goal for this syntactic form; non-verifying, so cannot break the spec.
- atk_8 (numeric -> epochCount, returns .error on numeric): EXIT 1 FAIL (unsolved goals, line 120).

RESOLVE EXECUTED: atk_6's materialized faithful patch (gold patch) ran through official run_resolve harness (Docker) => RESOLVED: True. No verifying wrong impl produced a non-resolving faithful patch.

REFINEMENT.MD AUDIT: legs A1 (R), A2 (I+R), A3 (A-reference), A4 (I+R+A-reference), A5 (I+R). No kind-3 (inexpressible-changed-op) legs. No consumed axioms (axioms-start/end empty). Both A-references map to real UNCHANGED callees: epochCount<->datetime_to_numeric(offset=1970-01-01,unit=ns) at duck_array_ops.py:388, durationCast<->x.astype(float); both validated ==real callee by G-AX (axiom_check.py runs real callees in-container incl. NaT-bearing arrays). Correspondence holds: the CHANGED op (kind dispatch split m|M -> M / elif m) is modeled DIRECTLY as the `match t.kind` in impl + toNumericSpec, not hidden behind an axiom. The discriminating behavior (duration routed to durationCast=.ok(raw.map num), NOT epochCount=.error) is exactly what atk_1/atk_2 fail on and the gold patch fixes.

CONCLUSION: 8 attacks run (>=5 required, distinct classes: prepatch, partial-domain, boundary, control-flow/divergence, oracle-drop, ungrounded-oracle echo, equal-rewrite, wrong-numeric-route). Positive control verifies. Every verifying impl is behaviorally gold and its faithful patch RESOLVES. verify => correct upheld. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on pydata__xarray-6599/velvet. The modeled function toNumericSpec and its deep-model callees (epochCount, durationCast) were checked against the REAL repo callees at base_commit 6bb2b855 (worktree, refetched to correct commit; numpy 1.26.4 / xarray backend). All agree on every probed input:

1. epochCount (datetime branch) == datetime_to_numeric(offset=1970-01-01, unit=ns): NaT count -> nan, others -> exact ns count. Verified [NaT,1000,2000,0] -> [nan,1000,2000,0]. Model's NumVal.nan leaf faithful.
2. durationCast (timedelta branch) == x.astype(float): NaT count NOT special-cased, comes through as float(-2^63)=-9.22e18. Verified [NaT,1000,2000] -> [-9.22e18,1000,2000]. Model raw.map NumVal.num (no .nan leaf) faithful.
3. .error .illTypedForDuration leaf: real epoch path raises UFuncTypeError on a timedelta64 array. Verified. Faithfully reproduces the pre-patch bug and the issue traceback.
4. Dispatch: toNumericSpec routes datetime->epochCount, duration->durationCast, numeric->passthrough, matching the GOLD post-patch to_floatable (=='M' / elif=='m' / fall-through), not the buggy pre-patch (kind in 'mM'). G-DIFF confirms prepatch fails as expected.

Independent re-runs: axiom_check.py PASS against the base worktree (11 boundary + 20000 fuzz NaT-bearing arrays). Spec region byte-identical to prepatch via swebench_unified.markers.same_spec (velvet tables) = True. Solution.lean elaborates clean under lean_verify.sh (exit 0, total-correctness/demonic).

Only theoretical divergence: for ns counts beyond 2^53 the exact Array Int carrier (NumVal.num) differs from float64 rounding (e.g. 4100000000000000001 -> real 4.1e18 = ...000). This is NOT drift: it is a SPEC_GUIDE §2-sanctioned exact-carrier float abstraction, documented explicitly in mapping.md §2 (scoped to the no-rounding regime; F2P observable is only [1000,2000,3000]), it is symmetric across the model and the intended refinement (the bijection defines NumVal.num n <-> exact float image; G-CONF/G-AX round both sides identically), and it does not affect the F2P-scoped resolve claim (test_polyval[timedelta-False]). The spec is neither too strong nor drifted on the task's domain. No genuine diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region verified byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (True). Mechanical G-LEAK screen (leakage.screen over the velvet spec_view) PASSES with zero hard_failures; recorded meta G-LEAK status='pass', relaxed_leakage=None (no relaxation to honor). Independent semantic gold-reconstruction review:

(1) No localization leak: the patched file path (xarray/core/computation.py) and patched symbols (to_floatable, ensure_numeric) never appear in the spec view's identifiers or comments. The model uses only abstract names (Kind/TypedArr/toNumeric/epochCount/durationCast).

(2) No gold-diff reproduction: the gold's distinguishing constants and calls — `x.dtype.kind in "mM"`, `== "M"` / `elif == "m"`, `datetime_to_numeric(..., offset=np.datetime64("1970-01-01"), datetime_unit="ns")`, `x.astype(float)` — are all abstracted ("reference epoch", "base resolution", deep models). No changed line is reproduced.

(3) No bug/fix narration: comments describe target behavior abstractly; no narration terms present.

(4) The one discriminating fact the spec encodes — that a duration/timedelta array must be cast directly to its numeric value rather than routed through the epoch-relative datetime conversion — is already implied by the PUBLIC problem_statement, which explicitly contrasts a datetime64 coordinate (correct) with a timedelta64 coordinate (wrong result) and requires stable/main to agree. A faithful spec must state correct target behavior; here that behavior is derivable from the public task, and the edit's location/mechanism is fully abstracted. The spec view does not reveal the gold edit beyond the public problem_statement (hints_text traceback content, e.g. _UFuncBinaryResolutionError, is referenced only in the off-view docs mapping.md/refinement.md, not in the spec view). Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
