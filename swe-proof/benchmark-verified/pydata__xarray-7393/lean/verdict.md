# P2 adversarial audit — pydata__xarray-7393

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,18 +89,9 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
   match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  | some _ => return rawArray
+  | none   => return superArray (effectiveDtype selfDtype dtypeArg)
 -- impl-end
 
 -- proof-start
@@ -112,5 +103,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,18 +89,9 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
   match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  | some _ => return castArray selfDtype rawArray.data
+  | none   => return superArray selfDtype
 -- impl-end
 
 -- proof-start
@@ -112,5 +103,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,18 +89,9 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
   match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  | some _ => return superArray (effectiveDtype selfDtype dtypeArg)
+  | none   => return castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
 -- impl-end
 
 -- proof-start
@@ -112,5 +103,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,18 +89,7 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
-  match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  return castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
 -- impl-end
 
 -- proof-start
@@ -112,5 +101,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -89,18 +89,9 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
   match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  | some _ => return castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
+  | none   => return superArray (effectiveDtype selfDtype dtypeArg)
 -- impl-end
 
 -- proof-start
@@ -112,5 +103,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,18 +89,9 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
   match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  | some _ => return castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
+  | none   => return superArray selfDtype
 -- impl-end
 
 -- proof-start
@@ -112,5 +103,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,18 +89,9 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
   match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  | some _ => return castArray (effectiveDtype selfDtype dtypeArg) []
+  | none   => return superArray (effectiveDtype selfDtype dtypeArg)
 -- impl-end
 
 -- proof-start
@@ -112,5 +103,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -89,18 +89,9 @@
     (selfDtype : Dtype) (dtypeArg : Option Dtype)
     (level : Option Level) (rawArray : NpArray)
     (superArray : Dtype → NpArray) : NpArray := Id.run do
-  -- Default the requested data type to the wrapper's stored original.
-  let mut dtype := dtypeArg
-  if dtype.isNone then
-    dtype := some selfDtype
-  let d := dtype.getD selfDtype
   match level with
-  | some _ =>
-      -- A selected level: re-present the raw level values at the effective type.
-      return castArray d rawArray.data
-  | none   =>
-      -- No selected level: defer to the underlying non-level conversion.
-      return superArray d
+  | some _ => return castArray rawArray.dtype rawArray.data
+  | none   => return superArray (effectiveDtype selfDtype dtypeArg)
 -- impl-end
 
 -- proof-start
@@ -112,5 +103,5 @@
         (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
   intro selfDtype dtypeArg level rawArray superArray
   unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
-  cases dtypeArg <;> cases level <;> rfl
+  cases dtypeArg <;> cases level <;> simp_all [castArray, effectiveDtype] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Converting a single labelled level of a composite index wrapper into a plain
numeric array, while preserving the element data type the wrapper was built to
carry.

The wrapper stores an *original* element data type (`selfDtype`) — the data type
of the values it was constructed from. Reading one labelled level out of the
underlying composite index yields a raw value array (`rawArray`) whose own data
type may have been widened by the underlying machinery, even though the values
themselves are unchanged.

The array-conversion entry point takes an optional requested data type
(`dtypeArg`). Its contract:

  * The EFFECTIVE data type is the requested one when given, and otherwise the
    wrapper's stored original data type.
  * When a labelled level is selected, the result is the raw level values
    re-presented with the EFFECTIVE data type — same element values, but the
    effective data type rather than the raw array's (possibly widened) one.
  * When no level is selected, the result is whatever the underlying (non-level)
    conversion produces for the effective data type.

Stated as an input→output relation; the implementation and its correctness proof
are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract. Reading a level's
-- raw value array, and the non-level conversion, are taken as modeled inputs
-- (`rawArray` and `superArray`); their production by the underlying machinery is
-- unchanged by this behavior and is exercised end-to-end by the differential
-- check. There is therefore no `axiom <callee>_prop` for the proof to consume.

/-- An element data type, abstracted to the only property observed here:
identity (equality). Distinct concrete data types ↔ distinct `Nat`s. -/
abbrev Dtype := Nat

/-- A labelled level identity. Only "selected vs not selected" and its identity
are observed. -/
abbrev Level := Nat

/-- A plain numeric array, restricted to the two observed components:
* `dtype` — the array's element data type;
* `data`  — the element values (a widening/narrowing of the data type preserves
  the in-range integer values, so the values are modeled as a `List Int`). -/
structure NpArray where
  dtype : Dtype
  data : List Int
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Re-present a list of element values as an array carrying a given data type
(the value-level conversion to a requested data type): the data type is set to
`d` and the in-range element values are carried through unchanged. -/
def castArray (d : Dtype) (data : List Int) : NpArray :=
  { dtype := d, data := data }

/-- The effective data type: the requested one if supplied, otherwise the
wrapper's stored original data type. -/
def effectiveDtype (selfDtype : Dtype) (dtypeArg : Option Dtype) : Dtype :=
  dtypeArg.getD selfDtype
-- pure-end

-- post-conditions-start
/-- The array-conversion result as a function of the inputs:

* the effective data type is `dtypeArg` when supplied, else `selfDtype`;
* a selected level (`level = some _`) yields the raw level values carried at the
  effective data type — i.e. the effective data type, NOT the raw array's;
* an unselected level (`level = none`) yields the underlying non-level
  conversion at the effective data type. -/
def problem_spec_arrayConvert
    (selfDtype : Dtype) (dtypeArg : Option Dtype)
    (level : Option Level) (rawArray : NpArray)
    (superArray : Dtype → NpArray)
    (result : NpArray) : Prop :=
  result =
    (match level with
     | some _ => castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
     | none   => superArray (effectiveDtype selfDtype dtypeArg))
-- post-conditions-end

-- impl-start
def implementation_arrayConvert
    (selfDtype : Dtype) (dtypeArg : Option Dtype)
    (level : Option Level) (rawArray : NpArray)
    (superArray : Dtype → NpArray) : NpArray := Id.run do
  -- Default the requested data type to the wrapper's stored original.
  let mut dtype := dtypeArg
  if dtype.isNone then
    dtype := some selfDtype
  let d := dtype.getD selfDtype
  match level with
  | some _ =>
      -- A selected level: re-present the raw level values at the effective type.
      return castArray d rawArray.data
  | none   =>
      -- No selected level: defer to the underlying non-level conversion.
      return superArray d
-- impl-end

-- proof-start
theorem correct_arrayConvert :
    ∀ (selfDtype : Dtype) (dtypeArg : Option Dtype)
      (level : Option Level) (rawArray : NpArray)
      (superArray : Dtype → NpArray),
      problem_spec_arrayConvert selfDtype dtypeArg level rawArray superArray
        (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
  intro selfDtype dtypeArg level rawArray superArray
  unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
  cases dtypeArg <;> cases level <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_arrayConvert is a COMPLETE functional equation — the postcondition pins `result` to an exact closed-form of ALL inputs: `result = match level with | some _ => castArray (effectiveDtype selfDtype dtypeArg) rawArray.data | none => superArray (effectiveDtype selfDtype dtypeArg)`. Any verifying impl is thereby forced extensionally equal to gold on both the dtype and the data components, over all `selfDtype`/`dtypeArg`/`level`/`rawArray`/opaque `superArray`. This is the tightest possible spec shape and leaves no gap for a wrong-but-verifying impl.

AXIOM/A-LEG AUDIT: the bundle declares ZERO `axiom` (grep confirmed NONE). Dtype/Level are `abbrev Nat`, NpArray is a plain structure, and rawArray/superArray are universally-quantified opaque inputs. Thus there are NO A-consumed and NO A-reference legs — refinement.md's every leg is R (dtype-defaulting op1-2, level re-cast op3) plus structural I via `match`; no kind-3 leg exists. axiom_check.py correctly returns status=skip (nothing to validate). The A-leg attack surface the plan targets is empty by construction here: the fix is modeled fully deeply (effectiveDtype + castArray), consuming no callee contract. mapping.md callee provenance (get_level_values unchanged → rawArray input; super().__array__ unchanged → superArray input) is consistent and validated end-to-end by G-CONF. Model↔patch correspondence holds: castArray d rawArray.data ↔ np.asarray(get_level_values(level).values, dtype=dtype); effectiveDtype ↔ `if dtype is None: dtype=self.dtype`; the none branch pass-through matches super().__array__(dtype).

ATTACKS (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec; spec regions byte-identical; verified concurrently ≤4 at a time). Command: `bash scripts/lean_verify.sh <file>`:
  - pos_control (gold impl): exit 0; `#print axioms correct_arrayConvert` => 'does not depend on any axioms' (clean).
  - atk_1 (PREPATCH BUG: selected level returns rawArray verbatim): exit 1, `rfl failed`. Reproduces prepatch failing-against-spec state (prepatch_reproduced=true).
  - atk_2 (partial-domain: ignores dtypeArg, always uses selfDtype): exit 1, `rfl failed`.
  - atk_3 (boundary/control-flow: swaps the two branches): exit 1, `rfl failed`.
  - atk_4 (control-flow-effect: drops the none branch, always castArray): exit 1, `rfl failed`.
  - atk_5 (ECHO: extensionally equal to gold): exit 0; `#print axioms` => '[propext]' (clean). Per protocol its faithful refined patch was materialized (= the gold patch, since extensionally identical) and RUN through the official harness: run_resolve('pydata__xarray-7393', patch, timeout=1800) => RESOLVED=True COMPLETED=True NOTE='resolved' FLAKY=False. Resolving echo of gold is NOT a weakness (per 2026-08-06 G-PANEL-1/eq policy).
  - atk_6 (ungrounded none-branch dtype: none branch uses selfDtype not effective): exit 1, `rfl failed`.
  - atk_7 (data corruption: castArray effective [] on selected level): exit 1, `rfl failed`.
  - atk_8 (ungrounded-oracle echo of prepatch: castArray rawArray.dtype rawArray.data): exit 1, `rfl failed`.

RESULT: 8 distinct same-spec attacks run (partial-domain, boundary, control-flow-effect, data-corruption, ungrounded-oracle echo, plus the prepatch bug). The ONLY impl with a closing clean-axiom proof (atk_5) is the extensional echo of gold, and its materialized faithful patch RESOLVES under the official harness. No verifying impl has a non-resolving faithful patch. verify⇏correct is NOT exhibited. Spec is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Converting a single labelled level of a composite index wrapper into a plain
numeric array, while preserving the element data type the wrapper was built to
carry.

The wrapper stores an *original* element data type (`selfDtype`) — the data type
of the values it was constructed from. Reading one labelled level out of the
underlying composite index yields a raw value array (`rawArray`) whose own data
type may have been widened by the underlying machinery, even though the values
themselves are unchanged.

The array-conversion entry point takes an optional requested data type
(`dtypeArg`). Its contract:

  * The EFFECTIVE data type is the requested one when given, and otherwise the
    wrapper's stored original data type.
  * When a labelled level is selected, the result is the raw level values
    re-presented with the EFFECTIVE data type — same element values, but the
    effective data type rather than the raw array's (possibly widened) one.
  * When no level is selected, the result is whatever the underlying (non-level)
    conversion produces for the effective data type.

Stated as an input→output relation; the implementation and its correctness proof
are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee needs a logical contract. Reading a level's
-- raw value array, and the non-level conversion, are taken as modeled inputs
-- (`rawArray` and `superArray`); their production by the underlying machinery is
-- unchanged by this behavior and is exercised end-to-end by the differential
-- check. There is therefore no `axiom <callee>_prop` for the proof to consume.

/-- An element data type, abstracted to the only property observed here:
identity (equality). Distinct concrete data types ↔ distinct `Nat`s. -/
abbrev Dtype := Nat

/-- A labelled level identity. Only "selected vs not selected" and its identity
are observed. -/
abbrev Level := Nat

/-- A plain numeric array, restricted to the two observed components:
* `dtype` — the array's element data type;
* `data`  — the element values (a widening/narrowing of the data type preserves
  the in-range integer values, so the values are modeled as a `List Int`). -/
structure NpArray where
  dtype : Dtype
  data : List Int
deriving DecidableEq, Repr
-- axioms-end

-- pure-start
/-- Re-present a list of element values as an array carrying a given data type
(the value-level conversion to a requested data type): the data type is set to
`d` and the in-range element values are carried through unchanged. -/
def castArray (d : Dtype) (data : List Int) : NpArray :=
  { dtype := d, data := data }

/-- The effective data type: the requested one if supplied, otherwise the
wrapper's stored original data type. -/
def effectiveDtype (selfDtype : Dtype) (dtypeArg : Option Dtype) : Dtype :=
  dtypeArg.getD selfDtype
-- pure-end

-- post-conditions-start
/-- The array-conversion result as a function of the inputs:

* the effective data type is `dtypeArg` when supplied, else `selfDtype`;
* a selected level (`level = some _`) yields the raw level values carried at the
  effective data type — i.e. the effective data type, NOT the raw array's;
* an unselected level (`level = none`) yields the underlying non-level
  conversion at the effective data type. -/
def problem_spec_arrayConvert
    (selfDtype : Dtype) (dtypeArg : Option Dtype)
    (level : Option Level) (rawArray : NpArray)
    (superArray : Dtype → NpArray)
    (result : NpArray) : Prop :=
  result =
    (match level with
     | some _ => castArray (effectiveDtype selfDtype dtypeArg) rawArray.data
     | none   => superArray (effectiveDtype selfDtype dtypeArg))
-- post-conditions-end

-- impl-start
def implementation_arrayConvert
    (selfDtype : Dtype) (dtypeArg : Option Dtype)
    (level : Option Level) (rawArray : NpArray)
    (superArray : Dtype → NpArray) : NpArray := Id.run do
  -- Default the requested data type to the wrapper's stored original.
  let mut dtype := dtypeArg
  if dtype.isNone then
    dtype := some selfDtype
  let d := dtype.getD selfDtype
  match level with
  | some _ =>
      -- A selected level: re-present the raw level values at the effective type.
      return castArray d rawArray.data
  | none   =>
      -- No selected level: defer to the underlying non-level conversion.
      return superArray d
-- impl-end

-- proof-start
theorem correct_arrayConvert :
    ∀ (selfDtype : Dtype) (dtypeArg : Option Dtype)
      (level : Option Level) (rawArray : NpArray)
      (superArray : Dtype → NpArray),
      problem_spec_arrayConvert selfDtype dtypeArg level rawArray superArray
        (implementation_arrayConvert selfDtype dtypeArg level rawArray superArray) := by
  intro selfDtype dtypeArg level rawArray superArray
  unfold problem_spec_arrayConvert implementation_arrayConvert effectiveDtype
  cases dtypeArg <;> cases level <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_arrayConvert is a COMPLETE functional equation — the postcondition pins `result` to an exact closed-form of ALL inputs: `result = match level with | some _ => castArray (effectiveDtype selfDtype dtypeArg) rawArray.data | none => superArray (effectiveDtype selfDtype dtypeArg)`. Any verifying impl is thereby forced extensionally equal to gold on both the dtype and the data components, over all `selfDtype`/`dtypeArg`/`level`/`rawArray`/opaque `superArray`. This is the tightest possible spec shape and leaves no gap for a wrong-but-verifying impl.

AXIOM/A-LEG AUDIT: the bundle declares ZERO `axiom` (grep confirmed NONE). Dtype/Level are `abbrev Nat`, NpArray is a plain structure, and rawArray/superArray are universally-quantified opaque inputs. Thus there are NO A-consumed and NO A-reference legs — refinement.md's every leg is R (dtype-defaulting op1-2, level re-cast op3) plus structural I via `match`; no kind-3 leg exists. axiom_check.py correctly returns status=skip (nothing to validate). The A-leg attack surface the plan targets is empty by construction here: the fix is modeled fully deeply (effectiveDtype + castArray), consuming no callee contract. mapping.md callee provenance (get_level_values unchanged → rawArray input; super().__array__ unchanged → superArray input) is consistent and validated end-to-end by G-CONF. Model↔patch correspondence holds: castArray d rawArray.data ↔ np.asarray(get_level_values(level).values, dtype=dtype); effectiveDtype ↔ `if dtype is None: dtype=self.dtype`; the none branch pass-through matches super().__array__(dtype).

ATTACKS (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec; spec regions byte-identical; verified concurrently ≤4 at a time). Command: `bash scripts/lean_verify.sh <file>`:
  - pos_control (gold impl): exit 0; `#print axioms correct_arrayConvert` => 'does not depend on any axioms' (clean).
  - atk_1 (PREPATCH BUG: selected level returns rawArray verbatim): exit 1, `rfl failed`. Reproduces prepatch failing-against-spec state (prepatch_reproduced=true).
  - atk_2 (partial-domain: ignores dtypeArg, always uses selfDtype): exit 1, `rfl failed`.
  - atk_3 (boundary/control-flow: swaps the two branches): exit 1, `rfl failed`.
  - atk_4 (control-flow-effect: drops the none branch, always castArray): exit 1, `rfl failed`.
  - atk_5 (ECHO: extensionally equal to gold): exit 0; `#print axioms` => '[propext]' (clean). Per protocol its faithful refined patch was materialized (= the gold patch, since extensionally identical) and RUN through the official harness: run_resolve('pydata__xarray-7393', patch, timeout=1800) => RESOLVED=True COMPLETED=True NOTE='resolved' FLAKY=False. Resolving echo of gold is NOT a weakness (per 2026-08-06 G-PANEL-1/eq policy).
  - atk_6 (ungrounded none-branch dtype: none branch uses selfDtype not effective): exit 1, `rfl failed`.
  - atk_7 (data corruption: castArray effective [] on selected level): exit 1, `rfl failed`.
  - atk_8 (ungrounded-oracle echo of prepatch: castArray rawArray.dtype rawArray.data): exit 1, `rfl failed`.

RESULT: 8 distinct same-spec attacks run (partial-domain, boundary, control-flow-effect, data-corruption, ungrounded-oracle echo, plus the prepatch bug). The ONLY impl with a closing clean-axiom proof (atk_5) is the extensional echo of gold, and its materialized faithful patch RESOLVES under the official harness. No verifying impl has a non-resolving faithful patch. verify⇏correct is NOT exhibited. Spec is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Modeled function: PandasMultiIndexingAdapter.__array__ (xarray/core/indexing.py:1533-1537 @ base). Spec problem_spec_arrayConvert is a total functional equation: result = (level=some _ => castArray (effectiveDtype selfDtype dtypeArg) rawArray.data | none => superArray (effectiveDtype selfDtype dtypeArg)).

Mechanical pre-flight all green: lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry); `#print axioms correct_arrayConvert` -> 'does not depend on any axioms' (real proof, no sorryAx); markers.same_spec(Solution, Solution_prepatch, lean tables) -> True (spec region byte-identical).

Faithfulness surfaces checked against the real POST-PATCH callee:
1. effectiveDtype selfDtype dtypeArg = dtypeArg.getD selfDtype exactly mirrors `if dtype is None: dtype = self.dtype`. Faithful.
2. Selected-level dtype: castArray d sets result dtype = d = effective dtype, matching np.asarray(..., dtype=d).dtype == d. This is the load-bearing fix (restore original dtype, not the pandas-widened rawArray.dtype). Faithful.
3. Selected-level values: castArray carries rawArray.data through unchanged; true within the DECLARED abstraction domain (data : List Int, in-range integer coordinate values). This matches exactly what the F2P test observes (str(...dtype) plus whole-number level values). Out-of-domain cases (float raw values into int dtype, int64 overflow into int32) are excluded by the explicit domain restriction (mapping.md: 'values are in range for the involved dtypes'); they are not real MultiIndex-level scenarios exercised and are not an over-claim, just a scoped model.
4. None branch: superArray is a MODELED INPUT (free function of the effective dtype); real code passes exactly the effective dtype to super().__array__(dtype). No over-claim; superArray faithfully models both pre- and post-patch since the else branch is unchanged and super() itself defaults None->self.dtype.

Abstraction (Dtype := Nat equality-only; values as in-range List Int) is a justified, scoped model, not a strengthening. G-CONF differential test diffs the Python R-shadow against the REAL patched callee over 120042 real numpy/pandas draws with 0 disagreements (meta.json G-CONF pass). I could construct NO input within the declared modeled domain where the spec disagrees with the real callee's observed (dtype, values) projection. No diverging input exists. Spec is not too strong and does not drift.

(Note: local box runs numpy2/pandas3 where get_level_values no longer widens int32; the original bug was pandas-1.5 Int64Index promotion. The re-cast dtype logic and none-branch equivalence hold regardless of pandas version.)

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen leakage.screen passes (no hard_failures); spec region byte-identical pre/post (same_spec=True); Solution.lean compiles (exit 0) and `#print axioms correct_arrayConvert` reports NO axiom dependence (real proof, no sorryAx). Semantic judgment: the spec view is fully abstracted (Dtype:=Nat, Level:=Nat, NpArray) and contains NONE of the gold-edit tokens (no np.asarray, self.dtype, get_level_values, super(), `dtype is None`, __array__, int32/int64). The behavioral content it states — preserve the original/effective dtype for a selected level rather than the widened raw dtype — is exactly what the public problem_statement already demands (stack must not cast int32->int64; original dtype must be preserved). The postcondition necessarily states WHAT correct behavior is (inherent to any spec benchmark) without disclosing HOW (no cast call, no defaulting line, no code). The gold-fix source snippet appears only in hints_text, which is excluded from this comparison by policy. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
