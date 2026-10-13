# P2 adversarial audit — scikit-learn__scikit-learn-12585

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_drop_exposes.lean`, `atk_3_swap_strict.lean`, `atk_4_and_instead_or.lean`, `atk_5_ignore_collection.lean`, `atk_8_collapse_reconstruct.lean`, `atk_9_permuted_echo.lean`, `atk_10_nonexhaustive_match.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_oracle_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, verifying implementation with a FAITHFUL refined patch that fails to resolve was found. The spec ensures `out = route isCollection exposesParams isClassObject strict`, where `route` is a concrete, spec-visible total function over Bool^4 (16 inputs) transliterating the post-patch clone dispatch op-for-op. Every terminating wrong impl (8 of them) is rejected by the Lean verifier on the exact discriminating goal; the only verifying wrong-shaped impl (oracle echo) computes `route` exactly, so its faithful refined patch IS the gold patch, which RESOLVES (empirically confirmed).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -83,9 +83,10 @@
     if isCollection then
       return Route.mapElements
     else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
+      -- Pre-patch skeleton: a value is treated as non-configurable solely by
+      -- whether it advertises the parameter interface; a class object that
+      -- advertises it is routed to reconstruction.
+      let nonConfigurable : Bool := (!exposesParams)
       if nonConfigurable then
         if strict then
           return Route.refuse
```

Attack 2 — `atk_2_drop_exposes.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -83,16 +83,10 @@
     if isCollection then
       return Route.mapElements
     else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
+      let nonConfigurable : Bool := isClassObject
       if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+        if strict then return Route.refuse else return Route.deepCopy
+      else return Route.reconstruct
     -- impl-end
 
 prove_correct copyRoute by
```

Attack 3 — `atk_3_swap_strict.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -83,16 +83,10 @@
     if isCollection then
       return Route.mapElements
     else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
       let nonConfigurable : Bool := (!exposesParams) || isClassObject
       if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+        if strict then return Route.deepCopy else return Route.refuse
+      else return Route.reconstruct
     -- impl-end
 
 prove_correct copyRoute by
```

Attack 4 — `atk_4_and_instead_or.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -83,16 +83,10 @@
     if isCollection then
       return Route.mapElements
     else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
+      let nonConfigurable : Bool := (!exposesParams) && isClassObject
       if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+        if strict then return Route.refuse else return Route.deepCopy
+      else return Route.reconstruct
     -- impl-end
 
 prove_correct copyRoute by
```

Attack 5 — `atk_5_ignore_collection.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -80,19 +80,10 @@
   ensures out = route isCollection exposesParams isClassObject strict
   do
     -- impl-start
-    if isCollection then
-      return Route.mapElements
-    else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
-      if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+    let nonConfigurable : Bool := (!exposesParams) || isClassObject
+    if nonConfigurable then
+      if strict then return Route.refuse else return Route.deepCopy
+    else return Route.reconstruct
     -- impl-end
 
 prove_correct copyRoute by
```

Attack 6 — `atk_6_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -80,19 +80,7 @@
   ensures out = route isCollection exposesParams isClassObject strict
   do
     -- impl-start
-    if isCollection then
-      return Route.mapElements
-    else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
-      if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+    return route isCollection exposesParams isClassObject strict
     -- impl-end
 
 prove_correct copyRoute by
```

Attack 7 — `atk_8_collapse_reconstruct.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -83,16 +83,7 @@
     if isCollection then
       return Route.mapElements
     else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
-      if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+      return Route.reconstruct
     -- impl-end
 
 prove_correct copyRoute by
```

Attack 8 — `atk_9_permuted_echo.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -80,19 +80,7 @@
   ensures out = route isCollection exposesParams isClassObject strict
   do
     -- impl-start
-    if isCollection then
-      return Route.mapElements
-    else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
-      if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+    return route isCollection isClassObject exposesParams strict
     -- impl-end
 
 prove_correct copyRoute by
```

Attack 9 — `atk_10_nonexhaustive_match.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axioms. The operation the desired behaviour changes — how a
@@ -80,19 +80,11 @@
   ensures out = route isCollection exposesParams isClassObject strict
   do
     -- impl-start
-    if isCollection then
-      return Route.mapElements
-    else
-      -- A configured object must advertise the parameter interface AND be a
-      -- genuine instance; a class object is excluded from reconstruction here.
-      let nonConfigurable : Bool := (!exposesParams) || isClassObject
-      if nonConfigurable then
-        if strict then
-          return Route.refuse
-        else
-          return Route.deepCopy
-      else
-        return Route.reconstruct
+    match isCollection, exposesParams, isClassObject, strict with
+    | true,  _,     _,     _     => return Route.mapElements
+    | false, true,  false, _     => return Route.reconstruct
+    | false, _,     _,     false => return Route.deepCopy
+    | false, _,     true,  true  => return Route.refuse
     -- impl-end
 
 prove_correct copyRoute by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The operation the desired behaviour changes — how a
   reconstruction routine classifies an incoming value and decides what to do
   with it — is modeled DEEPLY and concretely in the `pure` region (`route`):
   it is a finite decision over three boolean observations of the value plus the
   caller's strictness flag, validated against the real classification by
   conformance_check.py (G-CONF). The two surrounding routines the chosen branch
   then defers to (a structure-preserving deep copy, and the parameter-based
   reconstruction of a configured object) are UNCHANGED callees; the only one a
   reproduced case depends on for its observable result — the structure-preserving
   deep copy applied to a class object — is an A-reference validated `== the real
   callee` by axiom_check.py (G-AX), NOT consumed as an axiom (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The action taken for an incoming value when reproducing a configured object.
   Exactly one of four mutually exclusive outcomes:
   * `mapElements`     — the value is a homogeneous sequence/collection, so each
                         element is reproduced and a like collection rebuilt;
   * `deepCopy`        — the value is not a configurable object, and the caller
                         is lenient, so a structure-preserving deep copy is made;
   * `refuse`          — the value is not a configurable object, and the caller
                         is strict, so reproduction is refused;
   * `reconstruct`     — the value is a configurable object, so it is rebuilt
                         from its declared parameters. -/
inductive Route where
  | mapElements
  | deepCopy
  | refuse
  | reconstruct
  deriving DecidableEq, Inhabited, Repr

/- The routing decision, as a function of three independent observations of the
   value and the caller's strictness:
   * `isCollection`    — the value is one of the recognized homogeneous
                         collection kinds;
   * `exposesParams`   — the value advertises a declared-parameter interface;
   * `isClassObject`   — the value is itself a class, not an instance of one;
   * `strict`          — the caller demands a configurable object (no fallback).

   A value qualifies for parameter-based reconstruction ONLY when it both
   advertises the parameter interface AND is a genuine instance — a class object
   advertises the interface yet cannot be reconstructed through it, so it must be
   treated as a non-configurable value and routed to the deep-copy / refuse
   branch. Collections are handled first, before either test. -/
def route (isCollection exposesParams isClassObject strict : Bool) : Route :=
  if isCollection then Route.mapElements
  else
    if (!exposesParams) || isClassObject then
      if strict then Route.refuse else Route.deepCopy
    else Route.reconstruct
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how a single incoming value is reproduced while rebuilding a
   configured object. The decision is driven entirely by three independent
   observations of the value — whether it is a recognized homogeneous collection,
   whether it advertises a declared-parameter interface, and whether it is itself
   a class object rather than an instance — together with whether the caller
   demands a configurable object. A class object that happens to advertise the
   parameter interface is NOT a reconstructable configured object: it must fall
   through to the deep-copy (lenient) or refuse (strict) branch alongside ordinary
   non-configurable values, never to parameter-based reconstruction. -/
method copyRoute (isCollection : Bool) (exposesParams : Bool)
    (isClassObject : Bool) (strict : Bool)
    return (out : Route)
  ensures out = route isCollection exposesParams isClassObject strict
  do
    -- impl-start
    -- structurally distinct, behaviourally correct: compute via a match
    match isCollection, exposesParams, isClassObject, strict with
    | true,  _,     _,     _     => return Route.mapElements
    | false, true,  false, _     => return Route.reconstruct
    | false, false, _,     true  => return Route.refuse
    | false, false, _,     false => return Route.deepCopy
    | false, _,     true,  true  => return Route.refuse
    | false, _,     true,  false => return Route.deepCopy
    -- impl-end

prove_correct copyRoute by
  loom_solve <;> simp_all [route]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec confirmed True for all 9 submitted attacks + positive_control via swebench_unified.markers.same_spec (velvet). Verify cmd per file: `bash scripts/lean_verify.sh <file>`. Resolve via swebench_unified.harness.run_resolve (docker oracle, swe_bench_verified).

### TERMINATING WRONG IMPLS — ALL REJECTED (exit 1), same_spec=True
- atk_1_prepatch (nonConfigurable := !exposesParams; drops ||isClassObject): EXIT=1. Rejecting goal: `isClassObject=true ⊢ Route.reconstruct = if strict then refuse else deepCopy` (exact bug discriminator). PREPATCH BUG reproduced.
- atk_2_drop_exposes (nonConfigurable := isClassObject only): EXIT=1. Rejecting goal `exposesParams=false → Route.reconstruct = if strict then refuse else deepCopy`.
- atk_3_swap_strict (refuse<->deepCopy swapped): EXIT=1.
- atk_4_and_instead_or (&& for ||): EXIT=1.
- atk_5_ignore_collection (drop the isCollection arm): EXIT=1.
- atk_8_collapse_reconstruct (non-collection always reconstruct): EXIT=1 (`Route.reconstruct = if strict then refuse else deepCopy`).
- atk_9_permuted_echo (`route isCollection isClassObject exposesParams strict` — args swapped): EXIT=1.
- atk_10_nonexhaustive_match (match omitting the false,false,_,true refuse case): EXIT=1 (`error: Missing cases`). Confirms the Velvet verifier does NOT vacuously admit partial pattern matches.

### Verifying impls
- atk_6_oracle_echo (`return route isCollection exposesParams isClassObject strict`): EXIT=0 (VERIFIES). Faithful refined patch = the gold patch (route computes exactly the post-patch dispatch). run_resolve('scikit-learn__scikit-learn-12585', gold) => resolved=True, completed=True, note='resolved'. => CORRECT ECHO, not a spec weakness (matches build_one.py:_derive_audit_verdict candidate->resolve logic).
- atk_7_diverge (`let mut i := 0; while true do i := i+1; return Route.mapElements`): EXIT=0 (VERIFIES) — but ONLY via the UNIVERSAL partial-correctness vacuity of `set_option loom.semantics.termination "partial"` (a non-terminating program satisfies ANY postcondition). This option is a framework-level scaffold choice present in 401/500 velvet Solution.lean files, NOT a per-bundle spec property, so it verifies against every velvet postcondition and is orthogonal to refinement fidelity. It has NO faithful refined patch: refinement.md contains no divergence leg — `while true` corresponds to no gold operation. NOT SUBMITTED as a counterexample (would be a manufactured/degenerate break). For documentation only I materialized its closest (non-faithful) transliteration (an infinite loop injected at the clone dispatch site, patch_atk_7_translit.diff) and ran run_resolve(timeout=150,retries=0): result completed=False (harness produced no report — the loop hangs the container), i.e. INCONCLUSIVE, never resolved=False. A diverging impl thus cannot exhibit a faithful patch that 'does not resolve'.

### Positive control
positive_control.lean: structurally distinct (4-tuple `match` form), behaviourally correct. same_spec=True, EXIT=0 (verifies) => spec is NON-VACUOUS.

### REFINEMENT.MD LEG AUDIT (all R / A-reference / I; NO kind-3)
- A1 (R): value projected to (isCollection, exposesParams, isClassObject) triple + strict; dispatch depends on value only through this triple. G-CONF-covered.
- A2 (I): collection arm unchanged, transliterated identically.
- A3 (I): the ONE changed op — `(!exposesParams) || isClassObject` <-> `not hasattr(estimator,'get_params') or isinstance(estimator, type)` — op-for-op, no axiom over clone.
- A4 (I + A-reference): strict/lenient split unchanged (I); the deepCopy arm's observable on a class object — `copy.deepcopy(C) is C` — is the lone A-reference, validated by axiom_check.py across 16 class objects incl. a get_params-exposing class (0 violations); `type` handled atomically by copy._deepcopy_atomic. UNCHANGED callee, referenced not consumed.
- A5 (I): reconstruction arm unchanged.
meta.json lists ZERO consumed axioms (proof `loom_solve <;> simp_all [route]` is pure). The A-reference correspondence to the real callee holds.

### Verdict
SOUND. 9 same-spec attacks re-run (>=5 floor met) + prepatch reproduced + verifying positive control. Every terminating same-spec wrong impl is rejected on the exact discriminating clause; the only wrong-shaped verifying impl is a correct oracle echo whose faithful patch (the gold) RESOLVES. The divergence 'verify' is a universal partial-semantics artifact with no faithful patch and is excluded. No verifying wrong impl has a faithful refined patch that fails to resolve => verify⇏correct NOT demonstrated => spec is not broken.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1_prepatch.lean`, `atk_2_drop_exposes.lean`, `atk_3_swap_strict.lean`, `atk_4_and_instead_or.lean`, `atk_5_ignore_collection.lean`, `atk_8_collapse_reconstruct.lean`, `atk_9_permuted_echo.lean`, `atk_10_nonexhaustive_match.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6_oracle_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec, verifying implementation with a FAITHFUL refined patch that fails to resolve was found. The spec ensures `out = route isCollection exposesParams isClassObject strict`, where `route` is a concrete, spec-visible total function over Bool^4 (16 inputs) transliterating the post-patch clone dispatch op-for-op. Every terminating wrong impl (8 of them) is rejected by the Lean verifier on the exact discriminating goal; the only verifying wrong-shaped impl (oracle echo) computes `route` exactly, so its faithful refined patch IS the gold patch, which RESOLVES (empirically confirmed).
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2_drop_exposes.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3_swap_strict.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4_and_instead_or.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5_ignore_collection.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6_oracle_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_8_collapse_reconstruct.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9_permuted_echo.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10_nonexhaustive_match.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The operation the desired behaviour changes — how a
   reconstruction routine classifies an incoming value and decides what to do
   with it — is modeled DEEPLY and concretely in the `pure` region (`route`):
   it is a finite decision over three boolean observations of the value plus the
   caller's strictness flag, validated against the real classification by
   conformance_check.py (G-CONF). The two surrounding routines the chosen branch
   then defers to (a structure-preserving deep copy, and the parameter-based
   reconstruction of a configured object) are UNCHANGED callees; the only one a
   reproduced case depends on for its observable result — the structure-preserving
   deep copy applied to a class object — is an A-reference validated `== the real
   callee` by axiom_check.py (G-AX), NOT consumed as an axiom (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The action taken for an incoming value when reproducing a configured object.
   Exactly one of four mutually exclusive outcomes:
   * `mapElements`     — the value is a homogeneous sequence/collection, so each
                         element is reproduced and a like collection rebuilt;
   * `deepCopy`        — the value is not a configurable object, and the caller
                         is lenient, so a structure-preserving deep copy is made;
   * `refuse`          — the value is not a configurable object, and the caller
                         is strict, so reproduction is refused;
   * `reconstruct`     — the value is a configurable object, so it is rebuilt
                         from its declared parameters. -/
inductive Route where
  | mapElements
  | deepCopy
  | refuse
  | reconstruct
  deriving DecidableEq, Inhabited, Repr

/- The routing decision, as a function of three independent observations of the
   value and the caller's strictness:
   * `isCollection`    — the value is one of the recognized homogeneous
                         collection kinds;
   * `exposesParams`   — the value advertises a declared-parameter interface;
   * `isClassObject`   — the value is itself a class, not an instance of one;
   * `strict`          — the caller demands a configurable object (no fallback).

   A value qualifies for parameter-based reconstruction ONLY when it both
   advertises the parameter interface AND is a genuine instance — a class object
   advertises the interface yet cannot be reconstructed through it, so it must be
   treated as a non-configurable value and routed to the deep-copy / refuse
   branch. Collections are handled first, before either test. -/
def route (isCollection exposesParams isClassObject strict : Bool) : Route :=
  if isCollection then Route.mapElements
  else
    if (!exposesParams) || isClassObject then
      if strict then Route.refuse else Route.deepCopy
    else Route.reconstruct
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide how a single incoming value is reproduced while rebuilding a
   configured object. The decision is driven entirely by three independent
   observations of the value — whether it is a recognized homogeneous collection,
   whether it advertises a declared-parameter interface, and whether it is itself
   a class object rather than an instance — together with whether the caller
   demands a configurable object. A class object that happens to advertise the
   parameter interface is NOT a reconstructable configured object: it must fall
   through to the deep-copy (lenient) or refuse (strict) branch alongside ordinary
   non-configurable values, never to parameter-based reconstruction. -/
method copyRoute (isCollection : Bool) (exposesParams : Bool)
    (isClassObject : Bool) (strict : Bool)
    return (out : Route)
  ensures out = route isCollection exposesParams isClassObject strict
  do
    -- impl-start
    -- structurally distinct, behaviourally correct: compute via a match
    match isCollection, exposesParams, isClassObject, strict with
    | true,  _,     _,     _     => return Route.mapElements
    | false, true,  false, _     => return Route.reconstruct
    | false, false, _,     true  => return Route.refuse
    | false, false, _,     false => return Route.deepCopy
    | false, _,     true,  true  => return Route.refuse
    | false, _,     true,  false => return Route.deepCopy
    -- impl-end

prove_correct copyRoute by
  loom_solve <;> simp_all [route]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec confirmed True for all 9 submitted attacks + positive_control via swebench_unified.markers.same_spec (velvet). Verify cmd per file: `bash scripts/lean_verify.sh <file>`. Resolve via swebench_unified.harness.run_resolve (docker oracle, swe_bench_verified).

### TERMINATING WRONG IMPLS — ALL REJECTED (exit 1), same_spec=True
- atk_1_prepatch (nonConfigurable := !exposesParams; drops ||isClassObject): EXIT=1. Rejecting goal: `isClassObject=true ⊢ Route.reconstruct = if strict then refuse else deepCopy` (exact bug discriminator). PREPATCH BUG reproduced.
- atk_2_drop_exposes (nonConfigurable := isClassObject only): EXIT=1. Rejecting goal `exposesParams=false → Route.reconstruct = if strict then refuse else deepCopy`.
- atk_3_swap_strict (refuse<->deepCopy swapped): EXIT=1.
- atk_4_and_instead_or (&& for ||): EXIT=1.
- atk_5_ignore_collection (drop the isCollection arm): EXIT=1.
- atk_8_collapse_reconstruct (non-collection always reconstruct): EXIT=1 (`Route.reconstruct = if strict then refuse else deepCopy`).
- atk_9_permuted_echo (`route isCollection isClassObject exposesParams strict` — args swapped): EXIT=1.
- atk_10_nonexhaustive_match (match omitting the false,false,_,true refuse case): EXIT=1 (`error: Missing cases`). Confirms the Velvet verifier does NOT vacuously admit partial pattern matches.

### Verifying impls
- atk_6_oracle_echo (`return route isCollection exposesParams isClassObject strict`): EXIT=0 (VERIFIES). Faithful refined patch = the gold patch (route computes exactly the post-patch dispatch). run_resolve('scikit-learn__scikit-learn-12585', gold) => resolved=True, completed=True, note='resolved'. => CORRECT ECHO, not a spec weakness (matches build_one.py:_derive_audit_verdict candidate->resolve logic).
- atk_7_diverge (`let mut i := 0; while true do i := i+1; return Route.mapElements`): EXIT=0 (VERIFIES) — but ONLY via the UNIVERSAL partial-correctness vacuity of `set_option loom.semantics.termination "partial"` (a non-terminating program satisfies ANY postcondition). This option is a framework-level scaffold choice present in 401/500 velvet Solution.lean files, NOT a per-bundle spec property, so it verifies against every velvet postcondition and is orthogonal to refinement fidelity. It has NO faithful refined patch: refinement.md contains no divergence leg — `while true` corresponds to no gold operation. NOT SUBMITTED as a counterexample (would be a manufactured/degenerate break). For documentation only I materialized its closest (non-faithful) transliteration (an infinite loop injected at the clone dispatch site, patch_atk_7_translit.diff) and ran run_resolve(timeout=150,retries=0): result completed=False (harness produced no report — the loop hangs the container), i.e. INCONCLUSIVE, never resolved=False. A diverging impl thus cannot exhibit a faithful patch that 'does not resolve'.

### Positive control
positive_control.lean: structurally distinct (4-tuple `match` form), behaviourally correct. same_spec=True, EXIT=0 (verifies) => spec is NON-VACUOUS.

### REFINEMENT.MD LEG AUDIT (all R / A-reference / I; NO kind-3)
- A1 (R): value projected to (isCollection, exposesParams, isClassObject) triple + strict; dispatch depends on value only through this triple. G-CONF-covered.
- A2 (I): collection arm unchanged, transliterated identically.
- A3 (I): the ONE changed op — `(!exposesParams) || isClassObject` <-> `not hasattr(estimator,'get_params') or isinstance(estimator, type)` — op-for-op, no axiom over clone.
- A4 (I + A-reference): strict/lenient split unchanged (I); the deepCopy arm's observable on a class object — `copy.deepcopy(C) is C` — is the lone A-reference, validated by axiom_check.py across 16 class objects incl. a get_params-exposing class (0 violations); `type` handled atomically by copy._deepcopy_atomic. UNCHANGED callee, referenced not consumed.
- A5 (I): reconstruction arm unchanged.
meta.json lists ZERO consumed axioms (proof `loom_solve <;> simp_all [route]` is pure). The A-reference correspondence to the real callee holds.

### Verdict
SOUND. 9 same-spec attacks re-run (>=5 floor met) + prepatch reproduced + verifying positive control. Every terminating same-spec wrong impl is rejected on the exact discriminating clause; the only wrong-shaped verifying impl is a correct oracle echo whose faithful patch (the gold) RESOLVES. The divergence 'verify' is a universal partial-semantics artifact with no faithful patch and is excluded. No verifying wrong impl has a faithful refined patch that fails to resolve => verify⇏correct NOT demonstrated => spec is not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical pre/post (swebench_unified same_spec=True via VelvetBackend.language); Route+route live in the `pure` spec view, only impl region differs. Lean verifies (exit 0). The gold patch adds `or isinstance(estimator, type)` to clone's non-configurable test. The real dispatch reads the value ONLY through the triple (type(v) in {list,tuple,set,frozenset}, hasattr(v,'get_params'), isinstance(v,type)) + safe, so the branch is a total function of exactly the modeled abstraction. Exhaustive enumeration of all 16 boolean tuples shows route(isCollection,exposesParams,isClassObject,strict) matches the real post-patch arm selection on every input (0 disagreements): collection-first -> mapElements; (!exposesParams)||isClassObject -> strict?refuse:deepCopy; else reconstruct. conformance_check.py (seed 12585, 1e5 inputs) corroborates behaviorally against real clone incl. class-object identity under safe=False. No diverging input found; model is neither too strong nor drifting.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `conformance_check.py`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean)=True (verified via swebench_unified.markers.same_spec with VelvetBackend): the spec region — signature, `ensures out = route ...`, and the axioms/pure/pre/post blocks (including the fully-exposed `route` decision function) — is byte-identical pre/post patch; the ONLY difference is inside the elided impl-start/impl-end region (post: nonConfigurable := (!exposesParams) || isClassObject; prepatch: nonConfigurable := (!exposesParams)).

The spec view does reveal the post-patch routing decision (route: `if (!exposesParams) || isClassObject then (strict ? refuse : deepCopy) else reconstruct`), which corresponds to the gold edit's `... or isinstance(estimator, type)` disjunct. HOWEVER, this does NOT leak beyond the public problem_statement: the problem_statement itself contains a '#### Possible fix' section quoting the ENTIRE one-line gold patch VERBATIM — "Change base.py, line 51 to: elif not hasattr(estimator, 'get_params') or isinstance(estimator, type):" — together with its rationale (class objects lack a bound self so get_params() crashes). The gold patch is a single-line change equal to exactly that quoted line. Therefore the spec discloses nothing about the gold edit that the public problem_statement has not already fully disclosed. No incremental leakage. (Assessment excludes hints_text per policy, but the leaking fix is already in problem_statement, not merely hints.)

Modeling boundary is standard: impl and proof elided; the changed dispatch predicate modeled deeply in `pure`, no consumed axiom. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
