# P2 adversarial audit — pydata__xarray-6599

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,10 +76,8 @@
 
 -- impl-start
 def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do
-  if x.kind = ValKind.datetime then
+  if x.kind = ValKind.datetime ∨ x.kind = ValKind.duration then
     return datetimeToFloat x.raw
-  else if x.kind = ValKind.duration then
-    return x.raw.map Float.ofInt
   else
     return x.data
 -- impl-end
@@ -90,5 +88,5 @@
       problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
   intro x
   unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
-  cases x.kind <;> rfl
+  cases x.kind <;> simp <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,7 +81,7 @@
   else if x.kind = ValKind.duration then
     return x.raw.map Float.ofInt
   else
-    return x.data
+    return []
 -- impl-end
 
 -- proof-start
@@ -90,5 +90,5 @@
       problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
   intro x
   unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
-  cases x.kind <;> rfl
+  cases x.kind <;> simp <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,9 +77,9 @@
 -- impl-start
 def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do
   if x.kind = ValKind.datetime then
+    return x.raw.map Float.ofInt
+  else if x.kind = ValKind.duration then
     return datetimeToFloat x.raw
-  else if x.kind = ValKind.duration then
-    return x.raw.map Float.ofInt
   else
     return x.data
 -- impl-end
@@ -90,5 +90,5 @@
       problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
   intro x
   unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
-  cases x.kind <;> rfl
+  cases x.kind <;> simp <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,12 +76,7 @@
 
 -- impl-start
 def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do
-  if x.kind = ValKind.datetime then
-    return datetimeToFloat x.raw
-  else if x.kind = ValKind.duration then
-    return x.raw.map Float.ofInt
-  else
-    return x.data
+  return x.data
 -- impl-end
 
 -- proof-start
@@ -90,5 +85,5 @@
       problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
   intro x
   unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
-  cases x.kind <;> rfl
+  cases x.kind <;> simp <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
   if x.kind = ValKind.datetime then
     return datetimeToFloat x.raw
   else if x.kind = ValKind.duration then
-    return x.raw.map Float.ofInt
+    return x.raw.map (fun n => Float.ofInt n + 1)
   else
     return x.data
 -- impl-end
@@ -90,5 +90,5 @@
       problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
   intro x
   unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
-  cases x.kind <;> rfl
+  cases x.kind <;> simp <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -75,13 +75,7 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do
-  if x.kind = ValKind.datetime then
-    return datetimeToFloat x.raw
-  else if x.kind = ValKind.duration then
-    return x.raw.map Float.ofInt
-  else
-    return x.data
+def implementation_coerceToFloat (x : ArrayView) : List Float := coerceResult x
 -- impl-end
 
 -- proof-start
@@ -89,6 +83,5 @@
     ∀ (x : ArrayView),
       problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
   intro x
-  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
-  cases x.kind <;> rfl
+  rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Converting an array's values to plain floating-point numbers for numeric
computation (the coercion a polynomial-evaluation routine applies to its
coordinate before doing arithmetic).

An array is described by the *kind* of its values and the two value views the
coercion can read:

* a **datetime** array — instants in time — is made numeric by the standard
  datetime-to-number reduction relative to a constant epoch (the result is the
  number of nanoseconds since that epoch, as a float);
* a **duration** array — time spans / elapsed-time values — is made numeric by
  reinterpreting its underlying integer nanosecond counts directly as floats;
* an array that is **already numeric** is returned with its values unchanged.

The desired rule is therefore branch-specific:

  * datetime values  → the epoch-relative datetime-to-number reduction;
  * duration values  → the underlying integer counts cast to float;
  * any other values → the values, unchanged.

In particular a duration array follows its OWN rule — its integer counts cast to
float — and is not put through the datetime epoch reduction; the two
time-related kinds are coerced by different rules even though both originate
from time values.
-/

-- axioms-start
/-- The unchanged datetime-to-number reduction used for datetime-valued arrays:
it maps the underlying integer nanosecond counts to floats relative to a
constant epoch (with the not-a-time sentinel mapped to a not-a-number float). It is an
unchanged upstream callee, declared by signature only and used identically by
the specification and the implementation, so no separate property of it is
consumed. -/
opaque datetimeToFloat : List Int → List Float
-- axioms-end

-- pure-start
/-- The kind of values an array holds, as far as the coercion is concerned. -/
inductive ValKind where
  | datetime
  | duration
  | numeric
deriving DecidableEq, Repr

/-- An array, described by the observations the coercion reads:

* `kind` — whether the values are datetimes, durations, or already numeric;
* `raw` — the underlying integer nanosecond counts (read by the datetime and
  duration branches);
* `data` — the array's values seen as floats (returned by the numeric branch). -/
structure ArrayView where
  kind : ValKind
  raw : List Int
  data : List Float

/-- The float values produced by coercing an array, by the rule described above. -/
def coerceResult (x : ArrayView) : List Float :=
  match x.kind with
  | ValKind.datetime => datetimeToFloat x.raw
  | ValKind.duration => x.raw.map Float.ofInt
  | ValKind.numeric  => x.data
-- pure-end

-- post-conditions-start
/-- The coercion yields exactly the float values dictated by the array's kind:
the epoch-relative datetime reduction for datetimes, the underlying integer
counts cast to float for durations, and the unchanged values for numeric
arrays. -/
def problem_spec_coerceToFloat (x : ArrayView) (result : List Float) : Prop :=
  result = coerceResult x
-- post-conditions-end

-- impl-start
def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do
  if x.kind = ValKind.datetime then
    return datetimeToFloat x.raw
  else if x.kind = ValKind.duration then
    return x.raw.map Float.ofInt
  else
    return x.data
-- impl-end

-- proof-start
theorem correct_coerceToFloat :
    ∀ (x : ArrayView),
      problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
  intro x
  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
  cases x.kind <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Spec is FULL functional equality: problem_spec_coerceToFloat x result := (result = coerceResult x), where coerceResult is a TOTAL deterministic oracle over ValKind (datetime -> datetimeToFloat raw; duration -> raw.map Float.ofInt; numeric -> data). Any impl not extensionally equal to coerceResult cannot satisfy the forall theorem => maximally tight spec.

same_spec: all 6 attacks + pos returned True (swebench_unified.markers.same_spec, lean backend). Only the impl region edited; axioms/pure/pre/post byte-identical.

Attack verification (bash scripts/lean_verify.sh <f>), run concurrently in batches of 4:
- atk_1 PREPATCH BUG (duration+datetime both routed through datetimeToFloat, duration never reaches its cast): exit 1; residual goal `datetimeToFloat x.raw = List.map Float.ofInt x.raw` (duration clause) -> correctly REJECTED. prepatch reproduced.
- atk_2 PARTIAL-DOMAIN (numeric branch returns [] instead of x.data): exit 1; residual `x.data = []` -> REJECTED.
- atk_3 BOUNDARY (swap datetime/duration branch bodies): exit 1; residual `datetimeToFloat x.raw = List.map Float.ofInt x.raw` -> REJECTED.
- atk_4 CONTROL-FLOW-EFFECT (always return x.data, drop all branching): exit 1; residual `x.data = List.map Float.ofInt x.raw` -> REJECTED.
- atk_5 OFF-BY-ONE (duration cast fun n => Float.ofInt n + 1): exit 1; residual `forall a in x.raw, Float.ofInt a + 1 = Float.ofInt a` -> REJECTED.
- atk_6 UNGROUNDED-ORACLE ECHO (implementation_coerceToFloat x := coerceResult x, proof by rfl): exit 0, VERIFIES.

#print axioms (bash scripts/lean_verify.sh <f>_ax) on the two verifying impls:
- atk_6: 'correct_coerceToFloat' depends on axioms: [Classical.choice] (CLEAN; opaque datetimeToFloat is NOT an axiom, absent from list). EXIT 0.
- pos (real Solution): identical clean axioms [Classical.choice]. EXIT 0.

Resolve of the only clean-verifying attack (echo), per echo-attack policy — atk_6's faithful refined patch is behaviorally identical to gold (coerceResult IS the spec function and gold impl == coerceResult extensionally), and meta.patch_equals_gold=True, so its faithful patch equals the gold patch:
  run_resolve('pydata__xarray-6599', <gold patch>, run_id='sbu-resolve-audit-eq-73g9o0nn-atk6', timeout=1800, retries=1)
  RESULT: completed=True resolved=True attempts=1 flaky=False note='resolved'.
The echo resolves => it is behaviorally correct, NOT a spec weakness (unified G-PANEL-1/G-EQ policy: a same-spec verifying candidate whose refined patch RESOLVES is not a break).

No clean-verifying impl has a materialized faithful patch that fails to resolve. All 5 distinct wrong impls + prepatch bug are correctly rejected by the proof obligation.

refinement.md audit: 3 legs, all R (leg 1 also A-reference). No kind-3. A-reference discipline verified: datetimeToFloat is declared `opaque` (NOT `axiom`) — confirmed absent from #print axioms; it appears IDENTICALLY in coerceResult's datetime branch and the impl's datetime branch, the datetime clause closes by rfl, no property/_prop consumed => genuine A-reference, G-AX correctly skips. Correspondence to real callee holds: datetimeToFloat <-> datetime_to_numeric(x.data, offset=np.datetime64('1970-01-01'), datetime_unit='ns') at duck_array_ops.py:398 (mapping.md), the UNCHANGED upstream callee. Changed op (duration astype(float)) is modeled DEEPLY as raw.map Float.ofInt (not axiomatized) per SPEC_GUIDE §3 — bijection x.astype(float) for timedelta64[ns] <-> per-element int64->float cast is faithful. Frame discipline: full result list pinned to coerceResult x, no free output component.

Verdict: SOUND — >=5 distinct attacks + prepatch all encoded and machine-verified; the sole clean-verifying candidate's faithful patch executes and RESOLVES under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Converting an array's values to plain floating-point numbers for numeric
computation (the coercion a polynomial-evaluation routine applies to its
coordinate before doing arithmetic).

An array is described by the *kind* of its values and the two value views the
coercion can read:

* a **datetime** array — instants in time — is made numeric by the standard
  datetime-to-number reduction relative to a constant epoch (the result is the
  number of nanoseconds since that epoch, as a float);
* a **duration** array — time spans / elapsed-time values — is made numeric by
  reinterpreting its underlying integer nanosecond counts directly as floats;
* an array that is **already numeric** is returned with its values unchanged.

The desired rule is therefore branch-specific:

  * datetime values  → the epoch-relative datetime-to-number reduction;
  * duration values  → the underlying integer counts cast to float;
  * any other values → the values, unchanged.

In particular a duration array follows its OWN rule — its integer counts cast to
float — and is not put through the datetime epoch reduction; the two
time-related kinds are coerced by different rules even though both originate
from time values.
-/

-- axioms-start
/-- The unchanged datetime-to-number reduction used for datetime-valued arrays:
it maps the underlying integer nanosecond counts to floats relative to a
constant epoch (with the not-a-time sentinel mapped to a not-a-number float). It is an
unchanged upstream callee, declared by signature only and used identically by
the specification and the implementation, so no separate property of it is
consumed. -/
opaque datetimeToFloat : List Int → List Float
-- axioms-end

-- pure-start
/-- The kind of values an array holds, as far as the coercion is concerned. -/
inductive ValKind where
  | datetime
  | duration
  | numeric
deriving DecidableEq, Repr

/-- An array, described by the observations the coercion reads:

* `kind` — whether the values are datetimes, durations, or already numeric;
* `raw` — the underlying integer nanosecond counts (read by the datetime and
  duration branches);
* `data` — the array's values seen as floats (returned by the numeric branch). -/
structure ArrayView where
  kind : ValKind
  raw : List Int
  data : List Float

/-- The float values produced by coercing an array, by the rule described above. -/
def coerceResult (x : ArrayView) : List Float :=
  match x.kind with
  | ValKind.datetime => datetimeToFloat x.raw
  | ValKind.duration => x.raw.map Float.ofInt
  | ValKind.numeric  => x.data
-- pure-end

-- post-conditions-start
/-- The coercion yields exactly the float values dictated by the array's kind:
the epoch-relative datetime reduction for datetimes, the underlying integer
counts cast to float for durations, and the unchanged values for numeric
arrays. -/
def problem_spec_coerceToFloat (x : ArrayView) (result : List Float) : Prop :=
  result = coerceResult x
-- post-conditions-end

-- impl-start
def implementation_coerceToFloat (x : ArrayView) : List Float := Id.run do
  if x.kind = ValKind.datetime then
    return datetimeToFloat x.raw
  else if x.kind = ValKind.duration then
    return x.raw.map Float.ofInt
  else
    return x.data
-- impl-end

-- proof-start
theorem correct_coerceToFloat :
    ∀ (x : ArrayView),
      problem_spec_coerceToFloat x (implementation_coerceToFloat x) := by
  intro x
  unfold problem_spec_coerceToFloat implementation_coerceToFloat coerceResult
  cases x.kind <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Spec is FULL functional equality: problem_spec_coerceToFloat x result := (result = coerceResult x), where coerceResult is a TOTAL deterministic oracle over ValKind (datetime -> datetimeToFloat raw; duration -> raw.map Float.ofInt; numeric -> data). Any impl not extensionally equal to coerceResult cannot satisfy the forall theorem => maximally tight spec.

same_spec: all 6 attacks + pos returned True (swebench_unified.markers.same_spec, lean backend). Only the impl region edited; axioms/pure/pre/post byte-identical.

Attack verification (bash scripts/lean_verify.sh <f>), run concurrently in batches of 4:
- atk_1 PREPATCH BUG (duration+datetime both routed through datetimeToFloat, duration never reaches its cast): exit 1; residual goal `datetimeToFloat x.raw = List.map Float.ofInt x.raw` (duration clause) -> correctly REJECTED. prepatch reproduced.
- atk_2 PARTIAL-DOMAIN (numeric branch returns [] instead of x.data): exit 1; residual `x.data = []` -> REJECTED.
- atk_3 BOUNDARY (swap datetime/duration branch bodies): exit 1; residual `datetimeToFloat x.raw = List.map Float.ofInt x.raw` -> REJECTED.
- atk_4 CONTROL-FLOW-EFFECT (always return x.data, drop all branching): exit 1; residual `x.data = List.map Float.ofInt x.raw` -> REJECTED.
- atk_5 OFF-BY-ONE (duration cast fun n => Float.ofInt n + 1): exit 1; residual `forall a in x.raw, Float.ofInt a + 1 = Float.ofInt a` -> REJECTED.
- atk_6 UNGROUNDED-ORACLE ECHO (implementation_coerceToFloat x := coerceResult x, proof by rfl): exit 0, VERIFIES.

#print axioms (bash scripts/lean_verify.sh <f>_ax) on the two verifying impls:
- atk_6: 'correct_coerceToFloat' depends on axioms: [Classical.choice] (CLEAN; opaque datetimeToFloat is NOT an axiom, absent from list). EXIT 0.
- pos (real Solution): identical clean axioms [Classical.choice]. EXIT 0.

Resolve of the only clean-verifying attack (echo), per echo-attack policy — atk_6's faithful refined patch is behaviorally identical to gold (coerceResult IS the spec function and gold impl == coerceResult extensionally), and meta.patch_equals_gold=True, so its faithful patch equals the gold patch:
  run_resolve('pydata__xarray-6599', <gold patch>, run_id='sbu-resolve-audit-eq-73g9o0nn-atk6', timeout=1800, retries=1)
  RESULT: completed=True resolved=True attempts=1 flaky=False note='resolved'.
The echo resolves => it is behaviorally correct, NOT a spec weakness (unified G-PANEL-1/G-EQ policy: a same-spec verifying candidate whose refined patch RESOLVES is not a break).

No clean-verifying impl has a materialized faithful patch that fails to resolve. All 5 distinct wrong impls + prepatch bug are correctly rejected by the proof obligation.

refinement.md audit: 3 legs, all R (leg 1 also A-reference). No kind-3. A-reference discipline verified: datetimeToFloat is declared `opaque` (NOT `axiom`) — confirmed absent from #print axioms; it appears IDENTICALLY in coerceResult's datetime branch and the impl's datetime branch, the datetime clause closes by rfl, no property/_prop consumed => genuine A-reference, G-AX correctly skips. Correspondence to real callee holds: datetimeToFloat <-> datetime_to_numeric(x.data, offset=np.datetime64('1970-01-01'), datetime_unit='ns') at duck_array_ops.py:398 (mapping.md), the UNCHANGED upstream callee. Changed op (duration astype(float)) is modeled DEEPLY as raw.map Float.ofInt (not axiomatized) per SPEC_GUIDE §3 — bijection x.astype(float) for timedelta64[ns] <-> per-element int64->float cast is faithful. Frame discipline: full result list pinned to coerceResult x, no free output component.

Verdict: SOUND — >=5 distinct attacks + prepatch all encoded and machine-verified; the sole clean-verifying candidate's faithful patch executes and RESOLVES under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack on the modeled function `to_floatable` (per-array coercion in `_ensure_numeric`, xarray/core/computation.py @ base 6bb2b855) failed; the spec is faithful to the real repo behavior. Evidence:

1. GROUND-TRUTH SOURCE MATCH. Real base-commit source (git show 6bb2b855:xarray/core/computation.py) matches mapping.md's buggy quote verbatim: single `if x.dtype.kind in "mM": return x.copy(data=datetime_to_numeric(...offset=1970-01-01,unit=ns))` else `return x`. The gold patch (from test.jsonl) matches the post-patch quote verbatim: split into `== "M"` (datetime, unchanged) and NEW `elif == "m": return x.astype(float)`.

2. BUILD/AXIOM HYGIENE. Solution.lean compiles (lean_verify exit 0); `#print axioms correct_coerceToFloat` = [Classical.choice] only — no sorryAx/propositional axiom, proof is real. Spec region byte-identical with Solution_prepatch (same_spec=True via LeanBackend). Prepatch correctly FAILS to close with residual goal exactly at the duration branch (`datetimeToFloat x.raw = List.map Float.ofInt x.raw`), so the spec discriminates buggy from fixed on the F2P-relevant branch.

3. BRANCH-BY-BRANCH FAITHFULNESS vs the REAL callee (numpy 1.26.4 in-process):
   - Duration `x.astype(float)` for timedelta64 modeled as `raw.map Float.ofInt`: verified equal on F2P buffer [1000,2000,3000], negatives/zero, int64.min NaT sentinel (both give -9.223372036854776e18), lossy region 2^53/2^53+1 (both round identically), -2^60, and across units ns/s/D (astype(float) reinterprets the raw int64 buffer element-wise regardless of unit). No divergence found; the only theoretical mismatch |n|>2^53 is documented and both numpy and Float.ofInt round the SAME way, so it is not a divergence.
   - Datetime `datetime_to_numeric(...)` is an unchanged upstream callee, carried as `opaque datetimeToFloat` and used IDENTICALLY in spec helper (coerceResult) and impl; it cancels by reflexivity (A-reference), so no property is consumed and no diverging input is exhibitable on this branch.
   - Numeric branch: `return x` ↔ `data` unchanged. Identity, faithful.

4. FRAME/SCOPE. `_ensure_numeric`'s Dataset.map / lone-DataArray dispatch is unchanged plumbing applying to_floatable per variable; correctly excluded as orthogonal to the fix (each variable's coercion is exactly the modeled function). No output component left free — problem_spec pins full result = coerceResult x.

No diverging input exists between the modeled function and the real post-patch to_floatable. Spec is faithful (not too strong, no drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view is fully abstracted (ArrayView/ValKind/coerceResult/opaque datetimeToFloat); contains no repo symbols (to_floatable, _ensure_numeric, datetime_to_numeric, dtype.kind, astype), no file path, no diff markers, no bug/fix narration. Mechanical leakage.screen() passes with zero hard failures/warnings. spec region byte-identical to prepatch (same_spec=True); impl+proof elided from solver view. Solution.lean compiles (exit 0), #print axioms clean (only Classical.choice, no sorryAx). The docstring's branch-specific rule (durations cast int->float, not through the datetime epoch reduction) is the spec's legitimate correctness postcondition and is already inferable from the PUBLIC problem_statement: the wrong timedelta output magnitude (~1.59e30 vs correct ~4e6) itself signals durations were incorrectly routed through the datetime epoch reduction, and the correct numeric output is given. Repo-symbol/fix details (to_floatable, datetime_to_numeric, UFuncTypeError, 'polyval does not work with timedeltas') appear only in hints_text, which is NOT a permitted leakage source; none of them surface in the spec view. No gold-edit reconstruction beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
