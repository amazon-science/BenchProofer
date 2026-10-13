# P2 adversarial audit — django__django-13023

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -128,10 +128,6 @@
     isRecoverable e = false) → out = PyResult.propagated e
   do
     -- impl-start
-    -- Null and float inputs take their unchanged fast paths. For any other input
-    -- the interpretation attempt's outcome decides: a produced value is returned;
-    -- a reported failure that is one of the recoverable interpretation failures
-    -- becomes the field's invalid-value error; any other failure propagates.
     let result : PyResult :=
       if isNone then PyResult.retNone
       else
@@ -140,7 +136,7 @@
           match conv with
           | ConvResult.converted d => PyResult.ret d
           | ConvResult.raised e =>
-              if isRecoverable e then PyResult.validationError
+              if e = ExcKind.invalidOperation then PyResult.validationError
               else PyResult.propagated e
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -128,10 +128,6 @@
     isRecoverable e = false) → out = PyResult.propagated e
   do
     -- impl-start
-    -- Null and float inputs take their unchanged fast paths. For any other input
-    -- the interpretation attempt's outcome decides: a produced value is returned;
-    -- a reported failure that is one of the recoverable interpretation failures
-    -- becomes the field's invalid-value error; any other failure propagates.
     let result : PyResult :=
       if isNone then PyResult.retNone
       else
@@ -140,8 +136,11 @@
           match conv with
           | ConvResult.converted d => PyResult.ret d
           | ConvResult.raised e =>
-              if isRecoverable e then PyResult.validationError
-              else PyResult.propagated e
+              match e with
+              | ExcKind.invalidOperation => PyResult.validationError
+              | ExcKind.typeError => PyResult.validationError
+              | ExcKind.valueError => PyResult.propagated e
+              | ExcKind.other => PyResult.propagated e
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -128,10 +128,6 @@
     isRecoverable e = false) → out = PyResult.propagated e
   do
     -- impl-start
-    -- Null and float inputs take their unchanged fast paths. For any other input
-    -- the interpretation attempt's outcome decides: a produced value is returned;
-    -- a reported failure that is one of the recoverable interpretation failures
-    -- becomes the field's invalid-value error; any other failure propagates.
     let result : PyResult :=
       if isNone then PyResult.retNone
       else
@@ -139,9 +135,7 @@
         else
           match conv with
           | ConvResult.converted d => PyResult.ret d
-          | ConvResult.raised e =>
-              if isRecoverable e then PyResult.validationError
-              else PyResult.propagated e
+          | ConvResult.raised _ => PyResult.validationError
     return result
     -- impl-end
 
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -128,20 +128,11 @@
     isRecoverable e = false) → out = PyResult.propagated e
   do
     -- impl-start
-    -- Null and float inputs take their unchanged fast paths. For any other input
-    -- the interpretation attempt's outcome decides: a produced value is returned;
-    -- a reported failure that is one of the recoverable interpretation failures
-    -- becomes the field's invalid-value error; any other failure propagates.
     let result : PyResult :=
       if isNone then PyResult.retNone
       else
         if isFloat then PyResult.ret floatRes
-        else
-          match conv with
-          | ConvResult.converted d => PyResult.ret d
-          | ConvResult.raised e =>
-              if isRecoverable e then PyResult.validationError
-              else PyResult.propagated e
+        else PyResult.validationError
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -128,14 +128,10 @@
     isRecoverable e = false) → out = PyResult.propagated e
   do
     -- impl-start
-    -- Null and float inputs take their unchanged fast paths. For any other input
-    -- the interpretation attempt's outcome decides: a produced value is returned;
-    -- a reported failure that is one of the recoverable interpretation failures
-    -- becomes the field's invalid-value error; any other failure propagates.
     let result : PyResult :=
-      if isNone then PyResult.retNone
+      if isFloat then PyResult.ret floatRes
       else
-        if isFloat then PyResult.ret floatRes
+        if isNone then PyResult.retNone
         else
           match conv with
           | ConvResult.converted d => PyResult.ret d
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -128,10 +128,6 @@
     isRecoverable e = false) → out = PyResult.propagated e
   do
     -- impl-start
-    -- Null and float inputs take their unchanged fast paths. For any other input
-    -- the interpretation attempt's outcome decides: a produced value is returned;
-    -- a reported failure that is one of the recoverable interpretation failures
-    -- becomes the field's invalid-value error; any other failure propagates.
     let result : PyResult :=
       if isNone then PyResult.retNone
       else
@@ -140,8 +136,8 @@
           match conv with
           | ConvResult.converted d => PyResult.ret d
           | ConvResult.raised e =>
-              if isRecoverable e then PyResult.validationError
-              else PyResult.propagated e
+              if isRecoverable e then PyResult.propagated e
+              else PyResult.validationError
     return result
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
 /- No consumed axioms and no deep-model reference to a library callee. The two
@@ -128,17 +128,13 @@
     isRecoverable e = false) → out = PyResult.propagated e
   do
     -- impl-start
-    -- Null and float inputs take their unchanged fast paths. For any other input
-    -- the interpretation attempt's outcome decides: a produced value is returned;
-    -- a reported failure that is one of the recoverable interpretation failures
-    -- becomes the field's invalid-value error; any other failure propagates.
     let result : PyResult :=
       if isNone then PyResult.retNone
       else
         if isFloat then PyResult.ret floatRes
         else
           match conv with
-          | ConvResult.converted d => PyResult.ret d
+          | ConvResult.converted _ => PyResult.validationError
           | ConvResult.raised e =>
               if isRecoverable e then PyResult.validationError
               else PyResult.propagated e
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged sub-steps the operation delegates to — the null/float fast paths
   and the attempt to interpret an arbitrary input as a fixed-precision decimal —
   are modeled as FREE inputs of the method (`isNone`, `isFloat`, `floatRes`,
   `conv`; see the signature). The postconditions hold for EVERY value of those,
   so they are owed no contract: they are strictly weaker than any concrete
   implementation of the delegated steps (directive 7). The behaviour this bundle
   actually pins — how the OUTCOME of a failed interpretation is reported — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque carrier for a successfully produced fixed-precision decimal value.
   Nothing about its internal content is constrained: the operation under
   specification never inspects it, it only decides whether to surface it or to
   report a failure. -/
structure DecimalVal where
  payload : Int
  deriving DecidableEq, Inhabited

/- The kinds of failure the interpretation step can report. An interpretation
   attempt either succeeds with a value or fails reporting one of these. The
   first three are the recoverable ways an arbitrary object can fail to be read
   as a fixed-precision decimal — an invalid numeric operation, an unsupported
   operand type, or an out-of-domain value; `other` stands for any failure
   outside that recoverable family. -/
inductive ExcKind where
  | invalidOperation
  | typeError
  | valueError
  | other
  deriving DecidableEq, Inhabited

/- The outcome of attempting to interpret the input as a decimal: either a
   produced value, or a reported failure of some kind. This is the (free,
   unconstrained) result of the unchanged interpretation step. -/
inductive ConvResult where
  | converted (d : DecimalVal)
  | raised (e : ExcKind)
  deriving DecidableEq, Inhabited

/- The observable outcome of the whole operation:
   * `ret d`         — a fixed-precision decimal value is returned;
   * `retNone`       — the null fast-path returns the input unchanged;
   * `validationError` — the field's invalid-value error is reported;
   * `propagated e`  — a raw failure of kind `e` escapes the operation uncaught. -/
inductive PyResult where
  | ret (d : DecimalVal)
  | retNone
  | validationError
  | propagated (e : ExcKind)
  deriving DecidableEq, Inhabited

/- Which failure kinds are recoverable, i.e. must be normalised to the field's
   invalid-value error instead of being allowed to escape. Every way an arbitrary
   object can fail to be read as a fixed-precision decimal is recoverable; only a
   failure outside that family (`other`) is left to propagate. This is the heart
   of the desired behaviour: NO recoverable interpretation failure may surface as
   a raw exception to the caller. -/
def isRecoverable : ExcKind → Bool
  | .invalidOperation => true
  | .typeError        => true
  | .valueError       => true
  | .other            => false

/- The deep model of the operation's outcome from the (free) observations of its
   delegated steps. Null and float inputs take their fast paths; otherwise the
   interpretation attempt's outcome decides: a produced value is returned, a
   recoverable failure becomes the field's invalid-value error, and any other
   failure propagates. -/
def toDecimalResult (isNone isFloat : Bool) (floatRes : DecimalVal)
    (conv : ConvResult) : PyResult :=
  if isNone then PyResult.retNone
  else
    if isFloat then PyResult.ret floatRes
    else
      match conv with
      | ConvResult.converted d => PyResult.ret d
      | ConvResult.raised e =>
          if isRecoverable e then PyResult.validationError
          else PyResult.propagated e

@[grind] lemma isRecoverable_invalidOperation :
    isRecoverable ExcKind.invalidOperation = true := rfl
@[grind] lemma isRecoverable_typeError :
    isRecoverable ExcKind.typeError = true := rfl
@[grind] lemma isRecoverable_valueError :
    isRecoverable ExcKind.valueError = true := rfl
@[grind] lemma isRecoverable_other :
    isRecoverable ExcKind.other = false := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Interpret an arbitrary input as a fixed-precision decimal value. The delegated
   steps are read-only abstractions: `isNone` / `isFloat` flag the two fast paths,
   `floatRes` is the value the float fast path produces, and `conv` is the outcome
   of attempting to read a non-null, non-float input as a decimal — it either
   yields a value or reports a failure of some kind. Desired behaviour: a null
   input is returned unchanged; a float yields its converted value; for any other
   input the interpretation attempt's outcome decides — a produced value is
   returned, EVERY recoverable failure to interpret the input is reported as the
   field's invalid-value error (never escaping as a raw exception), and only a
   failure outside the recoverable family propagates. -/
method toDecimal (isNone : Bool) (isFloat : Bool) (floatRes : DecimalVal) (conv : ConvResult)
    return (out : PyResult)
  ensures out = toDecimalResult isNone isFloat floatRes conv
  ensures isNone = true → out = PyResult.retNone
  ensures (isNone = false ∧ isFloat = true) → out = PyResult.ret floatRes
  ensures ∀ d, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.converted d) →
    out = PyResult.ret d
  ensures ∀ e, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.raised e ∧
    isRecoverable e = true) → out = PyResult.validationError
  ensures ∀ e, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.raised e ∧
    isRecoverable e = false) → out = PyResult.propagated e
  do
    -- impl-start
    -- Null and float inputs take their unchanged fast paths. For any other input
    -- the interpretation attempt's outcome decides: a produced value is returned;
    -- a reported failure that is one of the recoverable interpretation failures
    -- becomes the field's invalid-value error; any other failure propagates.
    let result : PyResult :=
      if isNone then PyResult.retNone
      else
        if isFloat then PyResult.ret floatRes
        else
          match conv with
          | ConvResult.converted d => PyResult.ret d
          | ConvResult.raised e =>
              if isRecoverable e then PyResult.validationError
              else PyResult.propagated e
    return result
    -- impl-end

prove_correct toDecimal by
  loom_solve
  simp_all [toDecimalResult, isRecoverable]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec is a fully-pinned functional spec: postcondition #1 `ensures out = toDecimalResult isNone isFloat floatRes conv` totally determines `out` as a function of all four free inputs (isNone, isFloat, floatRes, conv). Verification therefore holds iff the impl is extensionally equal to `toDecimalResult`, leaving no room for a verifying-but-wrong impl. The remaining five postconditions are just projections of that identity (retNone/float/converted/recoverable→validationError/non-recoverable→propagated), reinforcing the pin.

ENVIRONMENT: python python. same_spec verified True for all 8 files via markers.same_spec(Solution, atk, velvet.language). Verifier: `bash scripts/lean_verify.sh <file>` (exit 0=verifies, 1=error). Runs launched concurrently in batches of <=4 as required.

### ATTACKS (all same_spec=True; impl-region-only edits; axioms/pure/pre/post byte-identical):
- atk_1 (partial recoverable family / PREPATCH BUG: only invalidOperation recoverable, typeError/valueError propagate) — VERIFY FAILS exit=1. This reproduces the exact pre-patch defect (matches Solution_prepatch.lean impl). prepatch_reproduced=true.
- atk_2 (boundary: valueError dropped from recoverable set) — VERIFY FAILS exit=1.
- atk_3 (ungrounded-oracle echo: every raised failure normalised, incl. `other`) — VERIFY FAILS exit=1.
- atk_4 (partial-domain: always validationError on the else branch, ignoring conv) — VERIFY FAILS exit=1.
- atk_5 (control-flow-effect: float guard reordered before the none guard) — VERIFY FAILS exit=1.
- atk_6 (inverted classification: recoverable propagates, non-recoverable normalised) — VERIFY FAILS exit=1.
- atk_7 (converted-leg bug: successful conversion swallowed as validationError) — VERIFY FAILS exit=1.
Positive control pc.lean (original gold impl) — VERIFIES exit=0.

All error outputs show `unsolved goals` on `ensures_6` (out = toDecimalResult ...) and/or the projection postconditions — the pinning identity is what refutes each wrong impl. My first restructured pc (oracle-echo `toDecimalResult` directly) also failed because the FROZEN `prove_correct ... simp_all` proof tail is tuned to the original structural impl; the byte-identical Solution.lean impl is the true positive control and verifies.

PROTOCOL STEP 2: no wrong impl verifies, so there is NO verifying-wrong-impl whose faithful refined patch could be materialized/resolve-run. verify=>correct holds; no BROKEN route exists. (patches map empty by necessity.)

REFINEMENT AUDIT (step 3): refinement.md legs A1-A4 are all tagged R+I; NO A-consumed and NO A-reference legs (mapping.md §3), and section C explicitly records NO kind-3 steps. The two real callees (create_decimal_from_float, decimal.Decimal) are UNCHANGED and their outputs are modeled as free inputs (floatRes, conv), owed no contract under directive 7 — a legitimate free-abstraction, strictly weaker than any concrete implementation. The genuinely-changed operation (which reported interpretation failures are caught and normalised to the field ValidationError) is modeled DEEPLY via isRecoverable/toDecimalResult in the pure region and pinned by the postconditions, not hidden behind a callee axiom. The A-leg correspondence audit is therefore vacuous (no A legs) and consistent with the frozen artifacts; G-AX auto-skips as documented. The R/I legs are G-CONF's responsibility (out of scope for this A-leg-focused pass).

CONCLUSION: >=5 distinct wrong impls (7 total, spanning partial-domain, boundary, control-flow-effect, inverted, converted-leg, and ungrounded-oracle-echo failure modes) all fail to verify; positive control verifies; prepatch bug reproduced and refuted. No verify-but-wrong impl exists, so no resolve run is owed. Spec is SOUND (verify => correct upheld).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The two
   unchanged sub-steps the operation delegates to — the null/float fast paths
   and the attempt to interpret an arbitrary input as a fixed-precision decimal —
   are modeled as FREE inputs of the method (`isNone`, `isFloat`, `floatRes`,
   `conv`; see the signature). The postconditions hold for EVERY value of those,
   so they are owed no contract: they are strictly weaker than any concrete
   implementation of the delegated steps (directive 7). The behaviour this bundle
   actually pins — how the OUTCOME of a failed interpretation is reported — is
   modeled DEEPLY in the `pure` region. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque carrier for a successfully produced fixed-precision decimal value.
   Nothing about its internal content is constrained: the operation under
   specification never inspects it, it only decides whether to surface it or to
   report a failure. -/
structure DecimalVal where
  payload : Int
  deriving DecidableEq, Inhabited

/- The kinds of failure the interpretation step can report. An interpretation
   attempt either succeeds with a value or fails reporting one of these. The
   first three are the recoverable ways an arbitrary object can fail to be read
   as a fixed-precision decimal — an invalid numeric operation, an unsupported
   operand type, or an out-of-domain value; `other` stands for any failure
   outside that recoverable family. -/
inductive ExcKind where
  | invalidOperation
  | typeError
  | valueError
  | other
  deriving DecidableEq, Inhabited

/- The outcome of attempting to interpret the input as a decimal: either a
   produced value, or a reported failure of some kind. This is the (free,
   unconstrained) result of the unchanged interpretation step. -/
inductive ConvResult where
  | converted (d : DecimalVal)
  | raised (e : ExcKind)
  deriving DecidableEq, Inhabited

/- The observable outcome of the whole operation:
   * `ret d`         — a fixed-precision decimal value is returned;
   * `retNone`       — the null fast-path returns the input unchanged;
   * `validationError` — the field's invalid-value error is reported;
   * `propagated e`  — a raw failure of kind `e` escapes the operation uncaught. -/
inductive PyResult where
  | ret (d : DecimalVal)
  | retNone
  | validationError
  | propagated (e : ExcKind)
  deriving DecidableEq, Inhabited

/- Which failure kinds are recoverable, i.e. must be normalised to the field's
   invalid-value error instead of being allowed to escape. Every way an arbitrary
   object can fail to be read as a fixed-precision decimal is recoverable; only a
   failure outside that family (`other`) is left to propagate. This is the heart
   of the desired behaviour: NO recoverable interpretation failure may surface as
   a raw exception to the caller. -/
def isRecoverable : ExcKind → Bool
  | .invalidOperation => true
  | .typeError        => true
  | .valueError       => true
  | .other            => false

/- The deep model of the operation's outcome from the (free) observations of its
   delegated steps. Null and float inputs take their fast paths; otherwise the
   interpretation attempt's outcome decides: a produced value is returned, a
   recoverable failure becomes the field's invalid-value error, and any other
   failure propagates. -/
def toDecimalResult (isNone isFloat : Bool) (floatRes : DecimalVal)
    (conv : ConvResult) : PyResult :=
  if isNone then PyResult.retNone
  else
    if isFloat then PyResult.ret floatRes
    else
      match conv with
      | ConvResult.converted d => PyResult.ret d
      | ConvResult.raised e =>
          if isRecoverable e then PyResult.validationError
          else PyResult.propagated e

@[grind] lemma isRecoverable_invalidOperation :
    isRecoverable ExcKind.invalidOperation = true := rfl
@[grind] lemma isRecoverable_typeError :
    isRecoverable ExcKind.typeError = true := rfl
@[grind] lemma isRecoverable_valueError :
    isRecoverable ExcKind.valueError = true := rfl
@[grind] lemma isRecoverable_other :
    isRecoverable ExcKind.other = false := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Interpret an arbitrary input as a fixed-precision decimal value. The delegated
   steps are read-only abstractions: `isNone` / `isFloat` flag the two fast paths,
   `floatRes` is the value the float fast path produces, and `conv` is the outcome
   of attempting to read a non-null, non-float input as a decimal — it either
   yields a value or reports a failure of some kind. Desired behaviour: a null
   input is returned unchanged; a float yields its converted value; for any other
   input the interpretation attempt's outcome decides — a produced value is
   returned, EVERY recoverable failure to interpret the input is reported as the
   field's invalid-value error (never escaping as a raw exception), and only a
   failure outside the recoverable family propagates. -/
method toDecimal (isNone : Bool) (isFloat : Bool) (floatRes : DecimalVal) (conv : ConvResult)
    return (out : PyResult)
  ensures out = toDecimalResult isNone isFloat floatRes conv
  ensures isNone = true → out = PyResult.retNone
  ensures (isNone = false ∧ isFloat = true) → out = PyResult.ret floatRes
  ensures ∀ d, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.converted d) →
    out = PyResult.ret d
  ensures ∀ e, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.raised e ∧
    isRecoverable e = true) → out = PyResult.validationError
  ensures ∀ e, (isNone = false ∧ isFloat = false ∧ conv = ConvResult.raised e ∧
    isRecoverable e = false) → out = PyResult.propagated e
  do
    -- impl-start
    -- Null and float inputs take their unchanged fast paths. For any other input
    -- the interpretation attempt's outcome decides: a produced value is returned;
    -- a reported failure that is one of the recoverable interpretation failures
    -- becomes the field's invalid-value error; any other failure propagates.
    let result : PyResult :=
      if isNone then PyResult.retNone
      else
        if isFloat then PyResult.ret floatRes
        else
          match conv with
          | ConvResult.converted d => PyResult.ret d
          | ConvResult.raised e =>
              if isRecoverable e then PyResult.validationError
              else PyResult.propagated e
    return result
    -- impl-end

prove_correct toDecimal by
  loom_solve
  simp_all [toDecimalResult, isRecoverable]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. The spec is a fully-pinned functional spec: postcondition #1 `ensures out = toDecimalResult isNone isFloat floatRes conv` totally determines `out` as a function of all four free inputs (isNone, isFloat, floatRes, conv). Verification therefore holds iff the impl is extensionally equal to `toDecimalResult`, leaving no room for a verifying-but-wrong impl. The remaining five postconditions are just projections of that identity (retNone/float/converted/recoverable→validationError/non-recoverable→propagated), reinforcing the pin.

ENVIRONMENT: python python. same_spec verified True for all 8 files via markers.same_spec(Solution, atk, velvet.language). Verifier: `bash scripts/lean_verify.sh <file>` (exit 0=verifies, 1=error). Runs launched concurrently in batches of <=4 as required.

### ATTACKS (all same_spec=True; impl-region-only edits; axioms/pure/pre/post byte-identical):
- atk_1 (partial recoverable family / PREPATCH BUG: only invalidOperation recoverable, typeError/valueError propagate) — VERIFY FAILS exit=1. This reproduces the exact pre-patch defect (matches Solution_prepatch.lean impl). prepatch_reproduced=true.
- atk_2 (boundary: valueError dropped from recoverable set) — VERIFY FAILS exit=1.
- atk_3 (ungrounded-oracle echo: every raised failure normalised, incl. `other`) — VERIFY FAILS exit=1.
- atk_4 (partial-domain: always validationError on the else branch, ignoring conv) — VERIFY FAILS exit=1.
- atk_5 (control-flow-effect: float guard reordered before the none guard) — VERIFY FAILS exit=1.
- atk_6 (inverted classification: recoverable propagates, non-recoverable normalised) — VERIFY FAILS exit=1.
- atk_7 (converted-leg bug: successful conversion swallowed as validationError) — VERIFY FAILS exit=1.
Positive control pc.lean (original gold impl) — VERIFIES exit=0.

All error outputs show `unsolved goals` on `ensures_6` (out = toDecimalResult ...) and/or the projection postconditions — the pinning identity is what refutes each wrong impl. My first restructured pc (oracle-echo `toDecimalResult` directly) also failed because the FROZEN `prove_correct ... simp_all` proof tail is tuned to the original structural impl; the byte-identical Solution.lean impl is the true positive control and verifies.

PROTOCOL STEP 2: no wrong impl verifies, so there is NO verifying-wrong-impl whose faithful refined patch could be materialized/resolve-run. verify=>correct holds; no BROKEN route exists. (patches map empty by necessity.)

REFINEMENT AUDIT (step 3): refinement.md legs A1-A4 are all tagged R+I; NO A-consumed and NO A-reference legs (mapping.md §3), and section C explicitly records NO kind-3 steps. The two real callees (create_decimal_from_float, decimal.Decimal) are UNCHANGED and their outputs are modeled as free inputs (floatRes, conv), owed no contract under directive 7 — a legitimate free-abstraction, strictly weaker than any concrete implementation. The genuinely-changed operation (which reported interpretation failures are caught and normalised to the field ValidationError) is modeled DEEPLY via isRecoverable/toDecimalResult in the pure region and pinned by the postconditions, not hidden behind a callee axiom. The A-leg correspondence audit is therefore vacuous (no A legs) and consistent with the frozen artifacts; G-AX auto-skips as documented. The R/I legs are G-CONF's responsibility (out of scope for this A-leg-focused pass).

CONCLUSION: >=5 distinct wrong impls (7 total, spanning partial-domain, boundary, control-flow-effect, inverted, converted-leg, and ungrounded-oracle-echo failure modes) all fail to verify; positive control verifies; prepatch bug reproduced and refuted. No verify-but-wrong impl exists, so no resolve run is owed. Spec is SOUND (verify => correct upheld).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break (too-strong/drift) attack found no divergence.

1. Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True. The axioms/pure/pre/post regions are the modeled spec; the only change vs prepatch is the impl+proof, exactly as intended.

2. Lean proof verifies: scripts/lean_verify.sh Solution.lean -> exit 0.

3. Real repo: base_commit f83b44075dafa429d59e8755aa47e15577cc49f9 has the pre-patch `except decimal.InvalidOperation`; gold patch broadens to `(decimal.InvalidOperation, TypeError, ValueError)`. Model's isRecoverable={invalidOperation,typeError,valueError} maps exactly to that except tuple; `other` -> propagate matches an exception escaping uncaught.

4. No over-constraint: isNone/isFloat/floatRes/conv are FREE method inputs; postconditions hold for every value, so the spec is strictly weaker than any concrete implementation of the (unchanged) delegated callees create_decimal_from_float and decimal.Decimal. A too-strong spec would pin their outputs; this one does not.

5. Float path fidelity: verified create_decimal_from_float never raises for a real Python float across max_digits in {1,2,5,28,1e9} and inputs {1.5,1e300,1e-300,inf,-inf,nan,0.0,-0.0,huge randoms}; Overflow/InvalidOperation traps cannot fire for a float value, so modeling the float leg as always `ret floatRes` (never raising) matches reality. The try/except in gold only wraps decimal.Decimal(value), consistent with the model.

6. Exhaustive fuzz: reconstructed the model's abstraction (per mapping.md) and diffed (kind,payload) against the REAL gold-patched to_python over the full F2P matrix ((), [], {}, set(), object(), complex(), non-numeric str/bytes, empty/whitespace str) x max_digits {1,2,5,28,1e9} plus 20000 random floats x 2 precisions plus assorted numerics/None/Decimal/bool. TOTAL DIFFS = 0.

Exhaustive over the small ExcKind/PyResult domain: each recoverable exception kind produced by decimal.Decimal is caught by the gold except and yields validationError (matches isRecoverable=true), non-recoverable escapes (matches propagated). No diverging input exists. Spec is faithful (if anything slightly weak via free inputs, which is sound per directive 7, not a drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Independently re-verified the recorded RELAXED-leakage disposition (RELAXED_LEAKAGE.md); did not rubber-stamp. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch, velvet tables) = True. (2) Core soundness confirmed live: Solution.lean verifies clean (raw exit 0); Solution_prepatch.lean (only invalidOperation recoverable) genuinely FAILS with 'unsolved goals' on the ensures `isRecoverable e = true → out = validationError` for e ∈ {typeError, valueError} (raw exit 1) — G-DIFF sound, not a wall/timeout artifact. meta gates G-EQ/G-CONF/G-MUT/G-PANEL-2/G-RESOLVE all pass. (3) Unavoidability re-derived executably: decimal.Decimal(()) and decimal.Decimal([]) raise ValueError (not TypeError), while {}, set(), object() raise TypeError; F2P test_invalid_value pins ValidationError for ALL of them, so a spec faithful to post-gold behavior MUST make valueError recoverable — faithful+non-leaking is provably impossible. (4) problem_statement token scan (hints_text is empty and out of scope regardless): ValueError=0, InvalidOperation=0, TypeError=3. The dispositioned leak is the recoverable-family enumeration echoing gold-added ValueError (constructor `| valueError`, lemma isRecoverable_valueError, `isRecoverable .valueError => true`, docstring 'out-of-domain value'). typeError is fully public (PS title 'raises TypeError on dict values'); invalidOperation is prepatch repo behavior. I found NO leak beyond the dispositioned ValueError-membership facet: gold patch is a single-line except-tuple broadening (one hunk), and no other spec-view content discloses gold specifics. Disposition is not broken (core gates sound + unavoidability holds + relaxed_leakage=true + RELAXED_LEAKAGE.md present). Per gates/_audit.py convention a properly-dispositioned relaxed-leakage panel records as pass/NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.
