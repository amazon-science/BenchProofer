# P2 adversarial audit — astropy__astropy-8872

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Both postconditions are TIGHT FUNCTIONAL EQUALITIES that pin the output for every input: problem_spec_resolveDtype dt result := result = (if promoteGeneral dt then floatDType else dt), and analogously problem_spec_reuseDtype with promoteReuse. Any impl that differs from this exact function on even one DType leaves an unclosable residual goal (e.g. atk_1 leaves `pure dt = if dt.kind='O' then floatDType else dt`, false at kind='O'). No same-spec wrong impl can verify, so there is no verifying-but-wrong candidate to materialize into a patch.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
 -- impl-start
 def implementation_resolveDtype (dt : DType) : DType := Id.run do
   let mut result := dt
-  if promoteGeneral dt then
+  if dt.kind = 'i' || dt.kind = 'u' then
     result := floatDType
   return result
 -- impl-end
@@ -81,9 +81,9 @@
     ∀ (dt : DType),
       problem_spec_resolveDtype dt (implementation_resolveDtype dt) := by
   intro dt
-  unfold problem_spec_resolveDtype implementation_resolveDtype
+  unfold problem_spec_resolveDtype implementation_resolveDtype promoteGeneral
   simp only [Id.run]
-  by_cases h : promoteGeneral dt <;> simp [h] <;> rfl
+  by_cases h : dt.kind = 'i' || dt.kind = 'u' <;> simp_all <;> rfl
 -- proof-end
 
 -- post-conditions-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,7 +96,7 @@
 -- impl-start
 def implementation_reuseDtype (dt : DType) : DType := Id.run do
   let mut result := dt
-  if promoteReuse dt then
+  if promoteReuse dt || dt.kind = 'b' then
     result := floatDType
   return result
 -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,8 +71,6 @@
 -- impl-start
 def implementation_resolveDtype (dt : DType) : DType := Id.run do
   let mut result := dt
-  if promoteGeneral dt then
-    result := floatDType
   return result
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -96,8 +96,7 @@
 -- impl-start
 def implementation_reuseDtype (dt : DType) : DType := Id.run do
   let mut result := dt
-  if promoteReuse dt then
-    result := floatDType
+  result := floatDType
   return result
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
 -- impl-start
 def implementation_resolveDtype (dt : DType) : DType := Id.run do
   let mut result := dt
-  if promoteGeneral dt then
+  if promoteReuse dt then
     result := floatDType
   return result
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,7 +71,7 @@
 -- impl-start
 def implementation_resolveDtype (dt : DType) : DType := Id.run do
   let mut result := dt
-  if promoteGeneral dt then
+  if (!(dt.canHoldSingle || dt.structured)) || dt.kind = 'O' then
     result := floatDType
   return result
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the element type used to store a numeric array when a unit is attached
to it.

When no explicit element type is requested, the stored array keeps the element
type of its input, with one family of exceptions: inputs whose element type
cannot itself represent fractional values — the integer and unsigned-integer
types — are stored using the default floating type instead. On the general
construction path one further exception applies: an input whose elements are
held as generic Python objects is likewise stored using the default floating
type. Every floating element type (including the lower-precision ones) and every
complex element type is preserved exactly as given; on the general path a
structured/record element type is also preserved.

Two situations are described: the general construction of a freshly materialised
array, and the fast reuse of an input that already carries a unit. They differ
only in whether the generic-object exception applies.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- driven entirely by the element type's category (its `kind`), which is taken as
-- a direct observation of the input element type rather than computed by a
-- separate routine, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An element type of a numeric array, carrying exactly the observations the
storage-type decision depends on.
* `kind` — the category code of the element type: `'i'` signed integer, `'u'`
  unsigned integer, `'f'` floating, `'b'` boolean, `'c'` complex, `'O'` generic
  object, `'V'` structured/record, `'S'`/`'U'` text, etc.;
* `canHoldSingle` — whether the type can hold a single-precision floating value
  without loss;
* `structured` — whether the type is a structured/record type. -/
structure DType where
  kind : Char
  canHoldSingle : Bool
  structured : Bool
deriving DecidableEq, Repr

/-- The default floating element type used when an input must be promoted: a
floating type that holds a single-precision value and is not structured. -/
def floatDType : DType := { kind := 'f', canHoldSingle := true, structured := false }

/-- On the general construction path, an input element type is promoted to the
default floating type iff it is a signed integer, an unsigned integer, or a
generic-object type. Every other category — floating (of any precision),
boolean, complex, structured, text — is kept as given. -/
def promoteGeneral (dt : DType) : Bool :=
  dt.kind = 'i' || dt.kind = 'u' || dt.kind = 'O'

/-- On the fast reuse path, an input element type is promoted to the default
floating type iff it is a signed or unsigned integer. The generic-object
exception does not apply here. -/
def promoteReuse (dt : DType) : Bool :=
  dt.kind = 'i' || dt.kind = 'u'
-- pure-end

-- post-conditions-start
/-- General construction: the stored element type is the default floating type
when the input element type is promoted, and otherwise is exactly the input
element type. -/
def problem_spec_resolveDtype (dt : DType) (result : DType) : Prop :=
  result = if promoteGeneral dt then floatDType else dt
-- post-conditions-end

-- impl-start
def implementation_resolveDtype (dt : DType) : DType := Id.run do
  let mut result := dt
  if promoteGeneral dt then
    result := floatDType
  return result
-- impl-end

-- proof-start
theorem correct_resolveDtype :
    ∀ (dt : DType),
      problem_spec_resolveDtype dt (implementation_resolveDtype dt) := by
  intro dt
  unfold problem_spec_resolveDtype implementation_resolveDtype
  simp only [Id.run]
  by_cases h : promoteGeneral dt <;> simp [h] <;> rfl
-- proof-end

-- post-conditions-start
/-- Fast reuse: the reused input keeps its element type unless that type is
promoted, in which case the default floating type is used. -/
def problem_spec_reuseDtype (dt : DType) (result : DType) : Prop :=
  result = if promoteReuse dt then floatDType else dt
-- post-conditions-end

-- impl-start
def implementation_reuseDtype (dt : DType) : DType := Id.run do
  let mut result := dt
  if promoteReuse dt then
    result := floatDType
  return result
-- impl-end

-- proof-start
theorem correct_reuseDtype :
    ∀ (dt : DType),
      problem_spec_reuseDtype dt (implementation_reuseDtype dt) := by
  intro dt
  unfold problem_spec_reuseDtype implementation_reuseDtype
  simp only [Id.run]
  by_cases h : promoteReuse dt <;> simp [h] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 6 DISTINCT same-spec wrong impls attempted, all same_spec=True (verified via markers.same_spec against gold Solution.lean; impl-only edits, axioms/pure/pre/post byte-identical). Verifications run concurrently (2 batches of ≤4) via scripts/lean_verify.sh <file>.

### RESULTS (exit codes):
- pos_control (exact gold): EXIT 0 (verifies). #print axioms correct_resolveDtype / correct_reuseDtype => [propext, Quot.sound] only — CLEAN (no sorryAx, no custom axioms).
- atk_1 partial-domain (general path drops the 'O' branch: promote only 'i'/'u'): EXIT 1. Residual goal `pure dt = if dt.kind='O' then floatDType else dt` — false at kind='O'. Also = prepatch general-path bug's complement.
- atk_2 boundary (reuse path also promotes booleans, kind='b'): EXIT 1. Residual `(if dt.kind='b' then pure floatDType else pure dt) = dt` — false at kind='b'.
- atk_3 control-flow-effect (never promote on general path — dropped the `if`): EXIT 1. Residual `pure dt = floatDType` under promoteGeneral dt=true.
- atk_4 ungrounded-oracle echo (reuse always returns floatDType): EXIT 1. Residual `pure floatDType = dt` under ¬promoteReuse.
- atk_5 swap (resolveDtype uses promoteReuse, i.e. drops the general-path 'O' exception): EXIT 1. Residual `(if promoteReuse dt then floatDType else pure dt)=dt` — false at kind='O'.
- atk_6 prepatch-bug (general path uses the OLD pre-patch gate `!(canHoldSingle||structured) || kind='O'`): EXIT 1. This is byte-identical to Solution_prepatch_1.lean's resolveDtype impl => PREPATCH BUG REPRODUCED (fails to close; discriminating input float16: kind='f', canHoldSingle=false). Even an aggressive proof (by_cases/simp_all/rfl) could not close atk_1.

No attack closed with clean axioms => step 2 (materialize + run_resolve) has NO applicable candidate; nothing to run through the official harness. That is the expected SOUND outcome for a tight functional-equality postcondition.

REFINEMENT.MD AUDIT (A-legs focus): axioms region is an empty comment — bundle consumes ZERO callee axioms; axiom_check.py is a documented skip stub. Therefore there are NO A-consumed and NO A-reference legs to audit for callee correspondence (refinement.md 'Axioms: None'). Every leg in both site tables is R (`value.dtype.kind in 'iuO'` ↔ promoteGeneral = kind∈{i,u,O}; `kind in 'iu'` ↔ promoteReuse = kind∈{i,u}; astype(float)/dtype=float ↔ floatDType=float64) or I (`let mut result := dt`, `return result` ↔ stored/reused dtype). No kind-3 (changed-inexpressible) legs. The R-leg correspondence to the real post-patch Python condition is exactly the gold patch.diff hunks (L296 reuse, L377 general) and is differential-tested by conformance_check.py (real numpy dtypes + 120k fuzzed triples, seed 8872) — no A legs there either. mapping.md symbol binding to astropy/units/quantity.py Quantity.__new__ is consistent.

VERDICT: SOUND. Spec is tight; verify⇒correct holds. No verify⇏correct witness exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. Both postconditions are TIGHT FUNCTIONAL EQUALITIES that pin the output for every input: problem_spec_resolveDtype dt result := result = (if promoteGeneral dt then floatDType else dt), and analogously problem_spec_reuseDtype with promoteReuse. Any impl that differs from this exact function on even one DType leaves an unclosable residual goal (e.g. atk_1 leaves `pure dt = if dt.kind='O' then floatDType else dt`, false at kind='O'). No same-spec wrong impl can verify, so there is no verifying-but-wrong candidate to materialize into a patch.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Choosing the element type used to store a numeric array when a unit is attached
to it.

When no explicit element type is requested, the stored array keeps the element
type of its input, with one family of exceptions: inputs whose element type
cannot itself represent fractional values — the integer and unsigned-integer
types — are stored using the default floating type instead. On the general
construction path one further exception applies: an input whose elements are
held as generic Python objects is likewise stored using the default floating
type. Every floating element type (including the lower-precision ones) and every
complex element type is preserved exactly as given; on the general path a
structured/record element type is also preserved.

Two situations are described: the general construction of a freshly materialised
array, and the fast reuse of an input that already carries a unit. They differ
only in whether the generic-object exception applies.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision is
-- driven entirely by the element type's category (its `kind`), which is taken as
-- a direct observation of the input element type rather than computed by a
-- separate routine, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- An element type of a numeric array, carrying exactly the observations the
storage-type decision depends on.
* `kind` — the category code of the element type: `'i'` signed integer, `'u'`
  unsigned integer, `'f'` floating, `'b'` boolean, `'c'` complex, `'O'` generic
  object, `'V'` structured/record, `'S'`/`'U'` text, etc.;
* `canHoldSingle` — whether the type can hold a single-precision floating value
  without loss;
* `structured` — whether the type is a structured/record type. -/
structure DType where
  kind : Char
  canHoldSingle : Bool
  structured : Bool
deriving DecidableEq, Repr

/-- The default floating element type used when an input must be promoted: a
floating type that holds a single-precision value and is not structured. -/
def floatDType : DType := { kind := 'f', canHoldSingle := true, structured := false }

/-- On the general construction path, an input element type is promoted to the
default floating type iff it is a signed integer, an unsigned integer, or a
generic-object type. Every other category — floating (of any precision),
boolean, complex, structured, text — is kept as given. -/
def promoteGeneral (dt : DType) : Bool :=
  dt.kind = 'i' || dt.kind = 'u' || dt.kind = 'O'

/-- On the fast reuse path, an input element type is promoted to the default
floating type iff it is a signed or unsigned integer. The generic-object
exception does not apply here. -/
def promoteReuse (dt : DType) : Bool :=
  dt.kind = 'i' || dt.kind = 'u'
-- pure-end

-- post-conditions-start
/-- General construction: the stored element type is the default floating type
when the input element type is promoted, and otherwise is exactly the input
element type. -/
def problem_spec_resolveDtype (dt : DType) (result : DType) : Prop :=
  result = if promoteGeneral dt then floatDType else dt
-- post-conditions-end

-- impl-start
def implementation_resolveDtype (dt : DType) : DType := Id.run do
  let mut result := dt
  if promoteGeneral dt then
    result := floatDType
  return result
-- impl-end

-- proof-start
theorem correct_resolveDtype :
    ∀ (dt : DType),
      problem_spec_resolveDtype dt (implementation_resolveDtype dt) := by
  intro dt
  unfold problem_spec_resolveDtype implementation_resolveDtype
  simp only [Id.run]
  by_cases h : promoteGeneral dt <;> simp [h] <;> rfl
-- proof-end

-- post-conditions-start
/-- Fast reuse: the reused input keeps its element type unless that type is
promoted, in which case the default floating type is used. -/
def problem_spec_reuseDtype (dt : DType) (result : DType) : Prop :=
  result = if promoteReuse dt then floatDType else dt
-- post-conditions-end

-- impl-start
def implementation_reuseDtype (dt : DType) : DType := Id.run do
  let mut result := dt
  if promoteReuse dt then
    result := floatDType
  return result
-- impl-end

-- proof-start
theorem correct_reuseDtype :
    ∀ (dt : DType),
      problem_spec_reuseDtype dt (implementation_reuseDtype dt) := by
  intro dt
  unfold problem_spec_reuseDtype implementation_reuseDtype
  simp only [Id.run]
  by_cases h : promoteReuse dt <;> simp [h] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: 6 DISTINCT same-spec wrong impls attempted, all same_spec=True (verified via markers.same_spec against gold Solution.lean; impl-only edits, axioms/pure/pre/post byte-identical). Verifications run concurrently (2 batches of ≤4) via scripts/lean_verify.sh <file>.

### RESULTS (exit codes):
- pos_control (exact gold): EXIT 0 (verifies). #print axioms correct_resolveDtype / correct_reuseDtype => [propext, Quot.sound] only — CLEAN (no sorryAx, no custom axioms).
- atk_1 partial-domain (general path drops the 'O' branch: promote only 'i'/'u'): EXIT 1. Residual goal `pure dt = if dt.kind='O' then floatDType else dt` — false at kind='O'. Also = prepatch general-path bug's complement.
- atk_2 boundary (reuse path also promotes booleans, kind='b'): EXIT 1. Residual `(if dt.kind='b' then pure floatDType else pure dt) = dt` — false at kind='b'.
- atk_3 control-flow-effect (never promote on general path — dropped the `if`): EXIT 1. Residual `pure dt = floatDType` under promoteGeneral dt=true.
- atk_4 ungrounded-oracle echo (reuse always returns floatDType): EXIT 1. Residual `pure floatDType = dt` under ¬promoteReuse.
- atk_5 swap (resolveDtype uses promoteReuse, i.e. drops the general-path 'O' exception): EXIT 1. Residual `(if promoteReuse dt then floatDType else pure dt)=dt` — false at kind='O'.
- atk_6 prepatch-bug (general path uses the OLD pre-patch gate `!(canHoldSingle||structured) || kind='O'`): EXIT 1. This is byte-identical to Solution_prepatch_1.lean's resolveDtype impl => PREPATCH BUG REPRODUCED (fails to close; discriminating input float16: kind='f', canHoldSingle=false). Even an aggressive proof (by_cases/simp_all/rfl) could not close atk_1.

No attack closed with clean axioms => step 2 (materialize + run_resolve) has NO applicable candidate; nothing to run through the official harness. That is the expected SOUND outcome for a tight functional-equality postcondition.

REFINEMENT.MD AUDIT (A-legs focus): axioms region is an empty comment — bundle consumes ZERO callee axioms; axiom_check.py is a documented skip stub. Therefore there are NO A-consumed and NO A-reference legs to audit for callee correspondence (refinement.md 'Axioms: None'). Every leg in both site tables is R (`value.dtype.kind in 'iuO'` ↔ promoteGeneral = kind∈{i,u,O}; `kind in 'iu'` ↔ promoteReuse = kind∈{i,u}; astype(float)/dtype=float ↔ floatDType=float64) or I (`let mut result := dt`, `return result` ↔ stored/reused dtype). No kind-3 (changed-inexpressible) legs. The R-leg correspondence to the real post-patch Python condition is exactly the gold patch.diff hunks (L296 reuse, L377 general) and is differential-tested by conformance_check.py (real numpy dtypes + 120k fuzzed triples, seed 8872) — no A legs there either. mapping.md symbol binding to astropy/units/quantity.py Quantity.__new__ is consistent.

VERDICT: SOUND. Spec is tight; verify⇒correct holds. No verify⇏correct witness exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence between the modeled functions and the real post-patch callee. Base commit b750a0e6 is pre-patch; spec models the gold post-patch decision. General path: promoteGeneral dt = (kind∈{i,u,O}) == real `value.dtype.kind in 'iuO'`; reuse path: promoteReuse dt = (kind∈{i,u}) == real `value.dtype.kind in 'iu'`. floatDType == numpy.dtype(float)=float64 (kind='f',canHoldSingle=true,structured=false), verified empirically. Non-promoted branch returns input dtype unchanged, matching real code. Verified: same_spec True for both prepatch skeletons; spec view clean (impl/proof elided); Solution.lean compiles; #print axioms = [propext, Quot.sound] (no sorryAx) for both correct_resolveDtype/correct_reuseDtype; conformance_check.py status=pass checked=240038 mismatches=0 over real numpy dtypes + 120k fuzzed triples; per-kind empirical decision table (float16/bool→keep, int/uint/object→float64, complex→keep) matches the model. 'S'/'U' non-numeric kinds are unreachable at the coercion op (real code raises TypeError via the earlier `kind in 'OSU'` guard), so the model's behavior there is vacuous, not a genuine reachable divergence. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, lean flavor) PASSES: hard_failures=[]. No diff markers, no patched file path (astropy/units/quantity.py never appears), no patched module dotted path, no gold-patch line reproduced (the diff's np.can_cast/value.dtype.fields/'iuO'/'iu' conditions are absent from the view), no spec-view identifier embedding a patched repo symbol (DType/promoteGeneral/promoteReuse/floatDType are model constructs, not repo symbols; the repo edit touches no distinctive def/class name — it changes an if-condition inside Quantity.__new__), and no narration terms (bug/fix/patch/wrong/etc.). Spec-region integrity verified: same_spec(Solution, prepatch_1)=True and same_spec(Solution, prepatch_2)=True — the consumer-visible spec is byte-identical across skeletons. Semantic check beyond the lexical screen: the spec view describes the TARGET BEHAVIOR abstractly via numpy dtype 'kind' categories (promote signed/unsigned int, plus generic-object on the general path; preserve every floating type including low-precision, complex, and structured). This does not exceed the PUBLIC problem_statement, which already states the observable behavior at issue — float16 is upgraded to float64 while float32/64/128 are preserved, i.e. low-precision floats must be kept. The spec abstracts away the actual edit mechanism: it never mentions np.can_cast(np.float32, ...), dt.fields, the quantity.py file, Quantity.__new__, the two ~L296/~L377 sites, or the diff hunks; a solver must still localize the sites and derive the numpy can_cast semantics themselves. The added modeling detail (object-type exception, two-path distinction, structured-type preservation) is correct-behavior specification, not gold-edit reconstruction. Leakage judged against problem_statement ONLY, not hints_text (hints mention np.can_cast(np.float32) and l299/l379 — but none of that appears in the spec view regardless). No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
