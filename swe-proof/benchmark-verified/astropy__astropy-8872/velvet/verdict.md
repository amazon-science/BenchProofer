# P2 adversarial audit — astropy__astropy-8872

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec totally pins `out` as a function of `input` over all 9 ElemType constructors in BOTH methods (each method carries `ensures out = resultElem… input` PLUS per-constructor `ensures input = .X → out = .Y` for every constructor, plus the isFloating iff clause). resultElemGeneral/resultElemFast/castsToFloatGeneral/castsToFloatFast are in the frozen pure region. Consequently every constructor's result is a proof obligation; any behavioral deviation on any single constructor produces an unsolved goal in prove_correct and fails verification. No verifying same-spec wrong impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -127,19 +127,22 @@
     (isFloating input = true ∨ input = .integral ∨ input = .object)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Whole numbers and individually-boxed
-    -- objects default to the double-width floating element-type; every floating
-    -- width is kept exactly as given, and boolean, complex, and structured records
-    -- are kept as given.
+    -- Pre-image skeleton (general path): an input is converted to the default
+    -- floating type unless its element-type is no narrower than the single-width
+    -- reference type (or carries record fields); a boxed-object element-type is
+    -- additionally converted. A narrow-width floating input fails the "no narrower
+    -- than single width" test and is re-materialized under the default — and a
+    -- boolean is converted too. The frozen spec requires every floating width
+    -- (and boolean) preserved, so prove_correct MUST fail.
     let result : ElemType :=
       match input with
       | .integral     => .floatDouble
       | .object       => .floatDouble
-      | .floatHalf     => .floatHalf
+      | .floatHalf     => .floatDouble   -- narrower than single width ⇒ converted
       | .floatSingle   => .floatSingle
       | .floatDouble   => .floatDouble
       | .floatExtended => .floatExtended
-      | .boolean      => .boolean
+      | .boolean      => .floatDouble    -- cannot represent float ⇒ converted
       | .complexFloat => .complexFloat
       | .structured   => .structured
     return result
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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -172,17 +172,21 @@
   ensures isFloating out = true ↔ (isFloating input = true ∨ input = .integral)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Only whole numbers default to the
-    -- double-width floating element-type; every floating width is kept exactly,
-    -- and boolean, complex, boxed-object, and structured records are kept as given.
+    -- Pre-image skeleton (fast path): an input is converted to the default
+    -- floating type unless its element-type is no narrower than the single-width
+    -- reference type (or carries record fields). A narrow-width floating input
+    -- fails the "no narrower than single width" test and is re-materialized under
+    -- the default — and a boolean is converted too. The frozen spec requires every
+    -- floating width (and boolean) preserved on this path, so prove_correct MUST
+    -- fail.
     let result : ElemType :=
       match input with
       | .integral     => .floatDouble
-      | .floatHalf     => .floatHalf
+      | .floatHalf     => .floatDouble   -- narrower than single width ⇒ converted
       | .floatSingle   => .floatSingle
       | .floatDouble   => .floatDouble
       | .floatExtended => .floatExtended
-      | .boolean      => .boolean
+      | .boolean      => .floatDouble    -- cannot represent float ⇒ converted
       | .complexFloat => .complexFloat
       | .object       => .object
       | .structured   => .structured
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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -127,17 +127,14 @@
     (isFloating input = true ∨ input = .integral ∨ input = .object)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Whole numbers and individually-boxed
-    -- objects default to the double-width floating element-type; every floating
-    -- width is kept exactly as given, and boolean, complex, and structured records
-    -- are kept as given.
+    -- WRONG: preserve boxed-object instead of converting to float.
     let result : ElemType :=
       match input with
       | .integral     => .floatDouble
-      | .object       => .floatDouble
-      | .floatHalf     => .floatHalf
-      | .floatSingle   => .floatSingle
-      | .floatDouble   => .floatDouble
+      | .object       => .object
+      | .floatHalf    => .floatHalf
+      | .floatSingle  => .floatSingle
+      | .floatDouble  => .floatDouble
       | .floatExtended => .floatExtended
       | .boolean      => .boolean
       | .complexFloat => .complexFloat
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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -127,17 +127,14 @@
     (isFloating input = true ∨ input = .integral ∨ input = .object)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Whole numbers and individually-boxed
-    -- objects default to the double-width floating element-type; every floating
-    -- width is kept exactly as given, and boolean, complex, and structured records
-    -- are kept as given.
+    -- WRONG: integral defaults to single width, not double.
     let result : ElemType :=
       match input with
-      | .integral     => .floatDouble
+      | .integral     => .floatSingle
       | .object       => .floatDouble
-      | .floatHalf     => .floatHalf
-      | .floatSingle   => .floatSingle
-      | .floatDouble   => .floatDouble
+      | .floatHalf    => .floatHalf
+      | .floatSingle  => .floatSingle
+      | .floatDouble  => .floatDouble
       | .floatExtended => .floatExtended
       | .boolean      => .boolean
       | .complexFloat => .complexFloat
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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -127,20 +127,17 @@
     (isFloating input = true ∨ input = .integral ∨ input = .object)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Whole numbers and individually-boxed
-    -- objects default to the double-width floating element-type; every floating
-    -- width is kept exactly as given, and boolean, complex, and structured records
-    -- are kept as given.
+    -- WRONG: complex over-converted to double float.
     let result : ElemType :=
       match input with
       | .integral     => .floatDouble
       | .object       => .floatDouble
-      | .floatHalf     => .floatHalf
-      | .floatSingle   => .floatSingle
-      | .floatDouble   => .floatDouble
+      | .floatHalf    => .floatHalf
+      | .floatSingle  => .floatSingle
+      | .floatDouble  => .floatDouble
       | .floatExtended => .floatExtended
       | .boolean      => .boolean
-      | .complexFloat => .complexFloat
+      | .complexFloat => .floatDouble
       | .structured   => .structured
     return result
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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -172,19 +172,17 @@
   ensures isFloating out = true ↔ (isFloating input = true ∨ input = .integral)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Only whole numbers default to the
-    -- double-width floating element-type; every floating width is kept exactly,
-    -- and boolean, complex, boxed-object, and structured records are kept as given.
+    -- WRONG: boxed-object over-converted to float on fast path.
     let result : ElemType :=
       match input with
       | .integral     => .floatDouble
-      | .floatHalf     => .floatHalf
-      | .floatSingle   => .floatSingle
-      | .floatDouble   => .floatDouble
+      | .object       => .floatDouble
+      | .floatHalf    => .floatHalf
+      | .floatSingle  => .floatSingle
+      | .floatDouble  => .floatDouble
       | .floatExtended => .floatExtended
       | .boolean      => .boolean
       | .complexFloat => .complexFloat
-      | .object       => .object
       | .structured   => .structured
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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -172,20 +172,18 @@
   ensures isFloating out = true ↔ (isFloating input = true ∨ input = .integral)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Only whole numbers default to the
-    -- double-width floating element-type; every floating width is kept exactly,
-    -- and boolean, complex, boxed-object, and structured records are kept as given.
+    -- WRONG: structured record over-converted to float on fast path.
     let result : ElemType :=
       match input with
       | .integral     => .floatDouble
-      | .floatHalf     => .floatHalf
-      | .floatSingle   => .floatSingle
-      | .floatDouble   => .floatDouble
+      | .object       => .object
+      | .floatHalf    => .floatHalf
+      | .floatSingle  => .floatSingle
+      | .floatDouble  => .floatDouble
       | .floatExtended => .floatExtended
       | .boolean      => .boolean
       | .complexFloat => .complexFloat
-      | .object       => .object
-      | .structured   => .structured
+      | .structured   => .floatDouble
     return result
     -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The behaviour modeled here is a pure decision over the
@@ -127,22 +127,8 @@
     (isFloating input = true ∨ input = .integral ∨ input = .object)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Whole numbers and individually-boxed
-    -- objects default to the double-width floating element-type; every floating
-    -- width is kept exactly as given, and boolean, complex, and structured records
-    -- are kept as given.
-    let result : ElemType :=
-      match input with
-      | .integral     => .floatDouble
-      | .object       => .floatDouble
-      | .floatHalf     => .floatHalf
-      | .floatSingle   => .floatSingle
-      | .floatDouble   => .floatDouble
-      | .floatExtended => .floatExtended
-      | .boolean      => .boolean
-      | .complexFloat => .complexFloat
-      | .structured   => .structured
-    return result
+    -- Oracle echo: return the pure spec function directly.
+    return resultElemGeneral input
     -- impl-end
 
 /- Decide the element-type a materialized array carries on the FAST path, where
@@ -172,21 +158,8 @@
   ensures isFloating out = true ↔ (isFloating input = true ∨ input = .integral)
   do
     -- impl-start
-    -- Dispatch on the input element-type. Only whole numbers default to the
-    -- double-width floating element-type; every floating width is kept exactly,
-    -- and boolean, complex, boxed-object, and structured records are kept as given.
-    let result : ElemType :=
-      match input with
-      | .integral     => .floatDouble
-      | .floatHalf     => .floatHalf
-      | .floatSingle   => .floatSingle
-      | .floatDouble   => .floatDouble
-      | .floatExtended => .floatExtended
-      | .boolean      => .boolean
-      | .complexFloat => .complexFloat
-      | .object       => .object
-      | .structured   => .structured
-    return result
+    -- Oracle echo: return the pure spec function directly.
+    return resultElemFast input
     -- impl-end
 
 prove_correct resolveElemGeneral by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a pure decision over the
--  element-type carried by an input array: given only that element-type, decide
--  the element-type the resulting array is materialized under. The element-type is
--  the read-only input; the result element-type is computed solely from it. The
--  surrounding array-construction machinery that reads back an element-type and
--  rebuilds the array is an UNCHANGED shared continuation reached identically on
--  every branch, so nothing about it is assumed: it is neither consumed as a
--  contract nor deep-modeled. There is no `axiom` declaration and no A-reference.
--  See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The element-type carried by a numeric array, reduced to the only distinctions
   the materialization decision reacts to. Real floating element-types are split
   by storage width because width is exactly what the decision must preserve:
     * `boolean`       — a truth-valued element-type;
     * `integral`      — a signed or unsigned whole-number element-type;
     * `floatHalf`     — a real floating element-type of the narrowest width;
     * `floatSingle`   — a real floating element-type of single width;
     * `floatDouble`   — a real floating element-type of double width; this is
                         ALSO the default real floating element-type an input is
                         converted to when conversion applies;
     * `floatExtended` — a real floating element-type wider than double;
     * `complexFloat`  — a complex floating element-type;
     * `object`        — a generic boxed-Python-object element-type (numbers
                         stored individually as objects rather than packed);
     * `structured`    — a composite record element-type carrying named fields. -/
inductive ElemType where
  | boolean
  | integral
  | floatHalf
  | floatSingle
  | floatDouble
  | floatExtended
  | complexFloat
  | object
  | structured
  deriving Inhabited, DecidableEq

/- The default real floating element-type an input is re-materialized under when
   conversion applies: double width. -/
def defaultFloat : ElemType := .floatDouble

/- Whether the element-type is a real floating element-type of SOME width. The
   decision must treat every member of this family identically — preserve it. -/
def isFloating : ElemType → Bool
  | .floatHalf     => true
  | .floatSingle   => true
  | .floatDouble   => true
  | .floatExtended => true
  | _              => false

/- The GENERAL-path conversion rule (used for a fresh array built from an
   arbitrary input): an integral or boxed-object element-type is converted to the
   default real floating element-type; every other element-type — including EVERY
   floating width, boolean, complex, and structured records — is preserved as
   given. The single behaviour this turns on: a real floating element-type must be
   preserved at its own width, never re-materialized under the default merely
   because it is narrower than some reference width. -/
def castsToFloatGeneral : ElemType → Bool
  | .integral => true
  | .object   => true
  | _         => false

/- The FAST-path conversion rule (used when the input is already an array of the
   target kind, so a boxed-object element-type cannot arise there): only an
   integral element-type is converted to the default real floating element-type;
   every floating width is preserved, and a boolean element-type is preserved on
   this path. -/
def castsToFloatFast : ElemType → Bool
  | .integral => true
  | _         => false

/- The element-type an array ends up materialized under on the GENERAL path: the
   default real floating element-type when conversion applies, otherwise the input
   element-type unchanged. -/
def resultElemGeneral (input : ElemType) : ElemType :=
  if castsToFloatGeneral input then defaultFloat else input

/- The element-type an array ends up materialized under on the FAST path. -/
def resultElemFast (input : ElemType) : ElemType :=
  if castsToFloatFast input then defaultFloat else input
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the element-type a freshly materialized array carries when no element
   type is explicitly requested, for an arbitrary input (the GENERAL path).
   `input` is read-only (not `mut`): the decision computes a single result element
   type and mutates nothing (directive 5).

   Desired behaviour: integral and boxed-object inputs default to the double-width
   real floating element-type; every real floating input is preserved exactly at
   its OWN width, of any width; boolean, complex, and structured-record inputs are
   preserved. In particular a real floating input of a narrow width must keep that
   width — it is never re-materialized under the default for being narrow. -/
method resolveElemGeneral (input : ElemType) return (out : ElemType)
  ensures out = resultElemGeneral input
  -- integral and boxed-object inputs default to the double-width floating type:
  ensures input = .integral → out = .floatDouble
  ensures input = .object → out = .floatDouble
  -- EVERY real floating width is preserved exactly, never widened to the default:
  ensures input = .floatHalf → out = .floatHalf
  ensures input = .floatSingle → out = .floatSingle
  ensures input = .floatDouble → out = .floatDouble
  ensures input = .floatExtended → out = .floatExtended
  -- boolean, complex, and structured-record inputs are preserved unchanged:
  ensures input = .boolean → out = .boolean
  ensures input = .complexFloat → out = .complexFloat
  ensures input = .structured → out = .structured
  -- a real floating input stays floating at its own width (no widening), so the
  -- result is floating iff the input was floating, integral, or object:
  ensures isFloating out = true ↔
    (isFloating input = true ∨ input = .integral ∨ input = .object)
  do
    -- impl-start
    -- Dispatch on the input element-type. Whole numbers and individually-boxed
    -- objects default to the double-width floating element-type; every floating
    -- width is kept exactly as given, and boolean, complex, and structured records
    -- are kept as given.
    let result : ElemType :=
      match input with
      | .integral     => .floatDouble
      | .object       => .floatDouble
      | .floatHalf     => .floatHalf
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .boolean
      | .complexFloat => .complexFloat
      | .structured   => .structured
    return result
    -- impl-end

/- Decide the element-type a materialized array carries on the FAST path, where
   the input is already an array of the target kind (so a boxed-object element
   type cannot arise). `input` is read-only (not `mut`).

   Desired behaviour: only integral inputs default to the double-width real
   floating element-type; every real floating input is preserved exactly at its
   own width, and a boolean input is preserved on this path — a narrow floating
   input is never re-materialized under the default for being narrow. -/
method resolveElemFast (input : ElemType) return (out : ElemType)
  ensures out = resultElemFast input
  -- only integral inputs default to the double-width floating element-type:
  ensures input = .integral → out = .floatDouble
  -- EVERY real floating width is preserved exactly, never widened to the default:
  ensures input = .floatHalf → out = .floatHalf
  ensures input = .floatSingle → out = .floatSingle
  ensures input = .floatDouble → out = .floatDouble
  ensures input = .floatExtended → out = .floatExtended
  -- boolean, complex, object, and structured-record inputs are preserved here:
  ensures input = .boolean → out = .boolean
  ensures input = .complexFloat → out = .complexFloat
  ensures input = .object → out = .object
  ensures input = .structured → out = .structured
  -- a real floating input stays floating at its own width (no widening), so the
  -- result is floating iff the input was floating or integral:
  ensures isFloating out = true ↔ (isFloating input = true ∨ input = .integral)
  do
    -- impl-start
    -- Dispatch on the input element-type. Only whole numbers default to the
    -- double-width floating element-type; every floating width is kept exactly,
    -- and boolean, complex, boxed-object, and structured records are kept as given.
    let result : ElemType :=
      match input with
      | .integral     => .floatDouble
      | .floatHalf     => .floatHalf
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .boolean
      | .complexFloat => .complexFloat
      | .object       => .object
      | .structured   => .structured
    return result
    -- impl-end

prove_correct resolveElemGeneral by
  loom_solve <;>
    cases input <;>
      simp_all [resultElemGeneral, castsToFloatGeneral, defaultFloat, isFloating]

prove_correct resolveElemFast by
  loom_solve <;>
    cases input <;>
      simp_all [resultElemFast, castsToFloatFast, defaultFloat, isFloating]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: velvet bundle, two modeled methods resolveElemGeneral / resolveElemFast, ElemType with 9 constructors. Each method's postconditions pin `out` for EVERY constructor (out = resultElem… input + 9 implication clauses + isFloating-iff). No axioms, no A-legs (meta.json: axioms=[], deep_model_references=[]; refinement.md §C and mapping.md §3 declare pure R/I only). So the A-leg attack surface is empty by construction; the only way to break verify⇏correct here is a behaviorally-wrong impl that still verifies.

SAME-SPEC: all 8 attacks + positive_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). Impl regions only were edited; axioms/pure/pre/post/prove_correct byte-identical.

ATTACKS (each verified: `bash scripts/lean_verify.sh <f>`), grouped by category:
- atk_1 (control-flow/prepatch bug, GENERAL): = Solution_prepatch.lean, floatHalf->floatDouble & boolean->floatDouble. EXIT=1, unsolved goals on ensures floatHalf/boolean & out=resultElemGeneral. FAILS (prepatch reproduced).
- atk_2 (prepatch bug, FAST): = Solution_prepatch_fast.lean, floatHalf->floatDouble & boolean->floatDouble on fast. EXIT=1, unsolved goals floatHalf/boolean. FAILS (prepatch reproduced).
- atk_3 (partial-domain, GENERAL): object->object (fails to convert boxed-object). EXIT=1, unsolved goal ensures object→floatDouble. FAILS.
- atk_4 (boundary/wrong-width, GENERAL): integral->floatSingle. EXIT=1, unsolved goal ensures integral→floatDouble. FAILS.
- atk_5 (over-convert, GENERAL): complexFloat->floatDouble. EXIT=1, unsolved goal ensures complexFloat→complexFloat. FAILS.
- atk_6 (over-convert, FAST): object->floatDouble on fast. EXIT=1, unsolved goal ensures object→object. FAILS.
- atk_7 (over-convert record, FAST): structured->floatDouble on fast. EXIT=1, unsolved goal ensures structured→structured. FAILS.
- atk_8 (ungrounded-oracle echo): impl returns `resolveElemGeneral`->`resultElemGeneral input`, fast->`resultElemFast input`. Behaviorally == gold decision. EXIT=0, VERIFIES.
- positive_control: unmodified Solution.lean, EXIT=0, VERIFIES.

RESOLVE STEP (protocol §2 — every VERIFYING same-spec impl's faithful patch run through the official harness): atk_8 is the only verifying same-spec impl besides the positive control. Its faithful refined patch is the gold decision (integral+object→float64 general, integral-only→float64 fast, all float widths & bool & complex & structured preserved) = the gold patch verbatim. Ran swebench_unified.harness.run_resolve('astropy__astropy-8872', <gold patch>, timeout=1800, retries=1) under `docker`. RESULT: RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. So the verifying impl's faithful patch RESOLVES → verify⇒correct holds; spec NOT broken.

MODEL↔PATCH CORRESPONDENCE AUDIT: extracted quantity.py at base_commit b750a0e6 (git show into quantity_base.py). FAST site lines 296-300 and GENERAL site 376-383 match the gold hunks' pre-image exactly. General post-patch `value.dtype.kind in 'iuO'` (convert integral+object) ⇔ castsToFloatGeneral {integral,object}; fast post-patch `kind in 'iu'` (integral only) ⇔ castsToFloatFast {integral}. Discriminating behavior (float16 & bool PRESERVED, not upgraded) lives in the deeply-modeled dispatch arms, matching the removal of the `not(np.can_cast(np.float32,dtype) or fields)` predicate. F2P test test_preserve_dtype (float16 general path → dtype stays float16) is exactly the floatHalf=>.floatHalf arm.

REFINEMENT.MD LEG AUDIT: A1-A4 and B1-B4 all tagged R or I; §C explicitly asserts no kind-3 steps, no consumed axiom, no A-reference — consistent with meta (axioms=[], deep_model_references=[], G-AX=skip). No A-legs to falsify; the R/I correspondence to the real Quantity.__new__ sites is sound.

CONCLUSION: 7 distinct behaviorally-wrong impls (prepatch general, prepatch fast, partial-domain, boundary, 3× over-convert / control-flow-effect across both sites) ALL fail verification on precisely the postcondition clause pinning the deviating constructor. The one verifying same-spec impl (oracle echo) materializes to the gold patch, which RESOLVES under the official harness. verify⇏correct is NOT exhibited. Spec is SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The frozen spec totally pins `out` as a function of `input` over all 9 ElemType constructors in BOTH methods (each method carries `ensures out = resultElem… input` PLUS per-constructor `ensures input = .X → out = .Y` for every constructor, plus the isFloating iff clause). resultElemGeneral/resultElemFast/castsToFloatGeneral/castsToFloatFast are in the frozen pure region. Consequently every constructor's result is a proof obligation; any behavioral deviation on any single constructor produces an unsolved goal in prove_correct and fails verification. No verifying same-spec wrong impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The behaviour modeled here is a pure decision over the
--  element-type carried by an input array: given only that element-type, decide
--  the element-type the resulting array is materialized under. The element-type is
--  the read-only input; the result element-type is computed solely from it. The
--  surrounding array-construction machinery that reads back an element-type and
--  rebuilds the array is an UNCHANGED shared continuation reached identically on
--  every branch, so nothing about it is assumed: it is neither consumed as a
--  contract nor deep-modeled. There is no `axiom` declaration and no A-reference.
--  See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The element-type carried by a numeric array, reduced to the only distinctions
   the materialization decision reacts to. Real floating element-types are split
   by storage width because width is exactly what the decision must preserve:
     * `boolean`       — a truth-valued element-type;
     * `integral`      — a signed or unsigned whole-number element-type;
     * `floatHalf`     — a real floating element-type of the narrowest width;
     * `floatSingle`   — a real floating element-type of single width;
     * `floatDouble`   — a real floating element-type of double width; this is
                         ALSO the default real floating element-type an input is
                         converted to when conversion applies;
     * `floatExtended` — a real floating element-type wider than double;
     * `complexFloat`  — a complex floating element-type;
     * `object`        — a generic boxed-Python-object element-type (numbers
                         stored individually as objects rather than packed);
     * `structured`    — a composite record element-type carrying named fields. -/
inductive ElemType where
  | boolean
  | integral
  | floatHalf
  | floatSingle
  | floatDouble
  | floatExtended
  | complexFloat
  | object
  | structured
  deriving Inhabited, DecidableEq

/- The default real floating element-type an input is re-materialized under when
   conversion applies: double width. -/
def defaultFloat : ElemType := .floatDouble

/- Whether the element-type is a real floating element-type of SOME width. The
   decision must treat every member of this family identically — preserve it. -/
def isFloating : ElemType → Bool
  | .floatHalf     => true
  | .floatSingle   => true
  | .floatDouble   => true
  | .floatExtended => true
  | _              => false

/- The GENERAL-path conversion rule (used for a fresh array built from an
   arbitrary input): an integral or boxed-object element-type is converted to the
   default real floating element-type; every other element-type — including EVERY
   floating width, boolean, complex, and structured records — is preserved as
   given. The single behaviour this turns on: a real floating element-type must be
   preserved at its own width, never re-materialized under the default merely
   because it is narrower than some reference width. -/
def castsToFloatGeneral : ElemType → Bool
  | .integral => true
  | .object   => true
  | _         => false

/- The FAST-path conversion rule (used when the input is already an array of the
   target kind, so a boxed-object element-type cannot arise there): only an
   integral element-type is converted to the default real floating element-type;
   every floating width is preserved, and a boolean element-type is preserved on
   this path. -/
def castsToFloatFast : ElemType → Bool
  | .integral => true
  | _         => false

/- The element-type an array ends up materialized under on the GENERAL path: the
   default real floating element-type when conversion applies, otherwise the input
   element-type unchanged. -/
def resultElemGeneral (input : ElemType) : ElemType :=
  if castsToFloatGeneral input then defaultFloat else input

/- The element-type an array ends up materialized under on the FAST path. -/
def resultElemFast (input : ElemType) : ElemType :=
  if castsToFloatFast input then defaultFloat else input
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the element-type a freshly materialized array carries when no element
   type is explicitly requested, for an arbitrary input (the GENERAL path).
   `input` is read-only (not `mut`): the decision computes a single result element
   type and mutates nothing (directive 5).

   Desired behaviour: integral and boxed-object inputs default to the double-width
   real floating element-type; every real floating input is preserved exactly at
   its OWN width, of any width; boolean, complex, and structured-record inputs are
   preserved. In particular a real floating input of a narrow width must keep that
   width — it is never re-materialized under the default for being narrow. -/
method resolveElemGeneral (input : ElemType) return (out : ElemType)
  ensures out = resultElemGeneral input
  -- integral and boxed-object inputs default to the double-width floating type:
  ensures input = .integral → out = .floatDouble
  ensures input = .object → out = .floatDouble
  -- EVERY real floating width is preserved exactly, never widened to the default:
  ensures input = .floatHalf → out = .floatHalf
  ensures input = .floatSingle → out = .floatSingle
  ensures input = .floatDouble → out = .floatDouble
  ensures input = .floatExtended → out = .floatExtended
  -- boolean, complex, and structured-record inputs are preserved unchanged:
  ensures input = .boolean → out = .boolean
  ensures input = .complexFloat → out = .complexFloat
  ensures input = .structured → out = .structured
  -- a real floating input stays floating at its own width (no widening), so the
  -- result is floating iff the input was floating, integral, or object:
  ensures isFloating out = true ↔
    (isFloating input = true ∨ input = .integral ∨ input = .object)
  do
    -- impl-start
    -- Dispatch on the input element-type. Whole numbers and individually-boxed
    -- objects default to the double-width floating element-type; every floating
    -- width is kept exactly as given, and boolean, complex, and structured records
    -- are kept as given.
    let result : ElemType :=
      match input with
      | .integral     => .floatDouble
      | .object       => .floatDouble
      | .floatHalf     => .floatHalf
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .boolean
      | .complexFloat => .complexFloat
      | .structured   => .structured
    return result
    -- impl-end

/- Decide the element-type a materialized array carries on the FAST path, where
   the input is already an array of the target kind (so a boxed-object element
   type cannot arise). `input` is read-only (not `mut`).

   Desired behaviour: only integral inputs default to the double-width real
   floating element-type; every real floating input is preserved exactly at its
   own width, and a boolean input is preserved on this path — a narrow floating
   input is never re-materialized under the default for being narrow. -/
method resolveElemFast (input : ElemType) return (out : ElemType)
  ensures out = resultElemFast input
  -- only integral inputs default to the double-width floating element-type:
  ensures input = .integral → out = .floatDouble
  -- EVERY real floating width is preserved exactly, never widened to the default:
  ensures input = .floatHalf → out = .floatHalf
  ensures input = .floatSingle → out = .floatSingle
  ensures input = .floatDouble → out = .floatDouble
  ensures input = .floatExtended → out = .floatExtended
  -- boolean, complex, object, and structured-record inputs are preserved here:
  ensures input = .boolean → out = .boolean
  ensures input = .complexFloat → out = .complexFloat
  ensures input = .object → out = .object
  ensures input = .structured → out = .structured
  -- a real floating input stays floating at its own width (no widening), so the
  -- result is floating iff the input was floating or integral:
  ensures isFloating out = true ↔ (isFloating input = true ∨ input = .integral)
  do
    -- impl-start
    -- Dispatch on the input element-type. Only whole numbers default to the
    -- double-width floating element-type; every floating width is kept exactly,
    -- and boolean, complex, boxed-object, and structured records are kept as given.
    let result : ElemType :=
      match input with
      | .integral     => .floatDouble
      | .floatHalf     => .floatHalf
      | .floatSingle   => .floatSingle
      | .floatDouble   => .floatDouble
      | .floatExtended => .floatExtended
      | .boolean      => .boolean
      | .complexFloat => .complexFloat
      | .object       => .object
      | .structured   => .structured
    return result
    -- impl-end

prove_correct resolveElemGeneral by
  loom_solve <;>
    cases input <;>
      simp_all [resultElemGeneral, castsToFloatGeneral, defaultFloat, isFloating]

prove_correct resolveElemFast by
  loom_solve <;>
    cases input <;>
      simp_all [resultElemFast, castsToFloatFast, defaultFloat, isFloating]
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: velvet bundle, two modeled methods resolveElemGeneral / resolveElemFast, ElemType with 9 constructors. Each method's postconditions pin `out` for EVERY constructor (out = resultElem… input + 9 implication clauses + isFloating-iff). No axioms, no A-legs (meta.json: axioms=[], deep_model_references=[]; refinement.md §C and mapping.md §3 declare pure R/I only). So the A-leg attack surface is empty by construction; the only way to break verify⇏correct here is a behaviorally-wrong impl that still verifies.

SAME-SPEC: all 8 attacks + positive_control confirmed same_spec=True via swebench_unified.markers.same_spec (velvet backend). Impl regions only were edited; axioms/pure/pre/post/prove_correct byte-identical.

ATTACKS (each verified: `bash scripts/lean_verify.sh <f>`), grouped by category:
- atk_1 (control-flow/prepatch bug, GENERAL): = Solution_prepatch.lean, floatHalf->floatDouble & boolean->floatDouble. EXIT=1, unsolved goals on ensures floatHalf/boolean & out=resultElemGeneral. FAILS (prepatch reproduced).
- atk_2 (prepatch bug, FAST): = Solution_prepatch_fast.lean, floatHalf->floatDouble & boolean->floatDouble on fast. EXIT=1, unsolved goals floatHalf/boolean. FAILS (prepatch reproduced).
- atk_3 (partial-domain, GENERAL): object->object (fails to convert boxed-object). EXIT=1, unsolved goal ensures object→floatDouble. FAILS.
- atk_4 (boundary/wrong-width, GENERAL): integral->floatSingle. EXIT=1, unsolved goal ensures integral→floatDouble. FAILS.
- atk_5 (over-convert, GENERAL): complexFloat->floatDouble. EXIT=1, unsolved goal ensures complexFloat→complexFloat. FAILS.
- atk_6 (over-convert, FAST): object->floatDouble on fast. EXIT=1, unsolved goal ensures object→object. FAILS.
- atk_7 (over-convert record, FAST): structured->floatDouble on fast. EXIT=1, unsolved goal ensures structured→structured. FAILS.
- atk_8 (ungrounded-oracle echo): impl returns `resolveElemGeneral`->`resultElemGeneral input`, fast->`resultElemFast input`. Behaviorally == gold decision. EXIT=0, VERIFIES.
- positive_control: unmodified Solution.lean, EXIT=0, VERIFIES.

RESOLVE STEP (protocol §2 — every VERIFYING same-spec impl's faithful patch run through the official harness): atk_8 is the only verifying same-spec impl besides the positive control. Its faithful refined patch is the gold decision (integral+object→float64 general, integral-only→float64 fast, all float widths & bool & complex & structured preserved) = the gold patch verbatim. Ran swebench_unified.harness.run_resolve('astropy__astropy-8872', <gold patch>, timeout=1800, retries=1) under `docker`. RESULT: RESOLVED=True, COMPLETED=True, note='resolved', attempts=1. So the verifying impl's faithful patch RESOLVES → verify⇒correct holds; spec NOT broken.

MODEL↔PATCH CORRESPONDENCE AUDIT: extracted quantity.py at base_commit b750a0e6 (git show into quantity_base.py). FAST site lines 296-300 and GENERAL site 376-383 match the gold hunks' pre-image exactly. General post-patch `value.dtype.kind in 'iuO'` (convert integral+object) ⇔ castsToFloatGeneral {integral,object}; fast post-patch `kind in 'iu'` (integral only) ⇔ castsToFloatFast {integral}. Discriminating behavior (float16 & bool PRESERVED, not upgraded) lives in the deeply-modeled dispatch arms, matching the removal of the `not(np.can_cast(np.float32,dtype) or fields)` predicate. F2P test test_preserve_dtype (float16 general path → dtype stays float16) is exactly the floatHalf=>.floatHalf arm.

REFINEMENT.MD LEG AUDIT: A1-A4 and B1-B4 all tagged R or I; §C explicitly asserts no kind-3 steps, no consumed axiom, no A-reference — consistent with meta (axioms=[], deep_model_references=[], G-AX=skip). No A-legs to falsify; the R/I correspondence to the real Quantity.__new__ sites is sound.

CONCLUSION: 7 distinct behaviorally-wrong impls (prepatch general, prepatch fast, partial-domain, boundary, 3× over-convert / control-flow-effect across both sites) ALL fail verification on precisely the postcondition clause pinning the deviating constructor. The one verifying same-spec impl (oracle echo) materializes to the gold patch, which RESOLVES under the official harness. verify⇏correct is NOT exhibited. Spec is SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. (1) Spec region is frozen: same_spec(Solution, prepatch)=True and same_spec(Solution, prepatch_fast)=True under the velvet backend — no spec drift baked into the impl. (2) Solution.lean verifies clean (lean_verify exit 0); both prepatch (wrong-impl) files fail prove_correct with unsolved goals, so the spec is discriminating rather than vacuously satisfiable. (3) Model-vs-real-callee: the two modeled functions transliterate exactly the post-patch predicate at astropy/units/quantity.py — general path `dtype.kind in 'iuO'` -> astype(float)=float64 else preserve; fast path `dtype.kind in 'iu'` -> float else preserve. Driving the REAL numpy dtype machinery (conformance_check.py, seed 8872, 100026 checks) plus my own independent differential harness over all 9 modeled categories and their concrete members gives 0 disagreements. Every arm matches: integral->floatDouble and object->floatDouble (general), integral->floatDouble (fast), floatHalf/floatSingle/floatDouble/floatExtended/boolean/complexFloat/structured preserved on both paths. The discriminating post-patch behaviors are confirmed against ground truth: np.can_cast(float32,float16)=False and np.can_cast(float32,bool_)=False (why pre-patch wrongly upgraded them), and np.array([...],object).astype(float).dtype==float64 (object->floatDouble on the general path). (4) Object preserved on the fast path agrees with real `kind in 'iu'` (O not selected). Out-of-model numpy kinds (strings 'SU', datetime 'M', timedelta 'm') never reach the decision — the constructor raises TypeError for non-numeric kinds and Quantity requires a numeric element-type — so their absence is a legitimate domain restriction, not a faithfulness gap. No diverging input exists; the modeled function agrees with the real post-patch callee on every reachable input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen) passes with zero hard failures. spec_view is byte-identical between Solution.lean and BOTH Solution_prepatch.lean and Solution_prepatch_fast.lean (same_spec=True): impl regions and prove_correct bodies are elided, so the view discloses nothing about which impl is gold. No gold-patch artifacts appear in the spec view: none of np.can_cast, float32, dtype, astype, .kind (numpy idiom), 'iu'/'iuO' char-class, value.dtype.fields, np./numpy, the patched file quantity.py, or the symbols Quantity/__new__. No diff markers, no reproduced changed lines, no narration terms. The only 'kind' occurrences are the English phrase 'target kind', not the dtype.kind idiom. Hints-text-only material (source lines l299/l379, gh-1776, 'inexact', 'can_cast') does NOT appear in the spec view — the anti-leakage boundary against hints is respected. Semantically the spec is a purely abstract categorical behavior model (ElemType/isFloating/resultElemGeneral/resultElemFast) stating the desired behavior: every float width (incl. floatHalf) preserved and integral/object->double float. This is exactly the behavior the PUBLIC problem_statement describes (float16 should not upgrade, like other float types); stating correct behavior is the spec's legitimate role and does not reconstruct the gold edit's location or code beyond the problem statement. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
