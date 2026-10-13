# P2 adversarial audit — sympy__sympy-14711

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_8.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

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
 /- A vector value, abstracted to an opaque handle. The behaviour under spec
@@ -116,12 +116,8 @@
   ensures out = addSpec self other
   do
     -- impl-start
-    -- Absorb the additive identity BEFORE attempting any coercion, so the
-    -- identity yields `self` instead of being rejected; otherwise coerce the
-    -- operand to vector form and combine, propagating the rejection unchanged.
     let result : Except AddErr VecVal :=
-      if isZeroOperand other then Except.ok self
-      else match asVector other with
+      match asVector other with
         | Except.ok v    => Except.ok (combine self v)
         | Except.error e => Except.error e
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
 /- A vector value, abstracted to an opaque handle. The behaviour under spec
@@ -116,15 +116,7 @@
   ensures out = addSpec self other
   do
     -- impl-start
-    -- Absorb the additive identity BEFORE attempting any coercion, so the
-    -- identity yields `self` instead of being rejected; otherwise coerce the
-    -- operand to vector form and combine, propagating the rejection unchanged.
-    let result : Except AddErr VecVal :=
-      if isZeroOperand other then Except.ok self
-      else match asVector other with
-        | Except.ok v    => Except.ok (combine self v)
-        | Except.error e => Except.error e
-    return result
+    return Except.ok self
     -- impl-end
 
 prove_correct vectorAdd by
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
 /- A vector value, abstracted to an opaque handle. The behaviour under spec
@@ -116,13 +116,10 @@
   ensures out = addSpec self other
   do
     -- impl-start
-    -- Absorb the additive identity BEFORE attempting any coercion, so the
-    -- identity yields `self` instead of being rejected; otherwise coerce the
-    -- operand to vector form and combine, propagating the rejection unchanged.
     let result : Except AddErr VecVal :=
       if isZeroOperand other then Except.ok self
       else match asVector other with
-        | Except.ok v    => Except.ok (combine self v)
+        | Except.ok _    => Except.ok self
         | Except.error e => Except.error e
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
 /- A vector value, abstracted to an opaque handle. The behaviour under spec
@@ -116,14 +116,11 @@
   ensures out = addSpec self other
   do
     -- impl-start
-    -- Absorb the additive identity BEFORE attempting any coercion, so the
-    -- identity yields `self` instead of being rejected; otherwise coerce the
-    -- operand to vector form and combine, propagating the rejection unchanged.
     let result : Except AddErr VecVal :=
       if isZeroOperand other then Except.ok self
       else match asVector other with
         | Except.ok v    => Except.ok (combine self v)
-        | Except.error e => Except.error e
+        | Except.error _ => Except.ok self
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
 /- A vector value, abstracted to an opaque handle. The behaviour under spec
@@ -116,13 +116,10 @@
   ensures out = addSpec self other
   do
     -- impl-start
-    -- Absorb the additive identity BEFORE attempting any coercion, so the
-    -- identity yields `self` instead of being rejected; otherwise coerce the
-    -- operand to vector form and combine, propagating the rejection unchanged.
     let result : Except AddErr VecVal :=
       if isZeroOperand other then Except.ok self
       else match asVector other with
-        | Except.ok v    => Except.ok (combine self v)
+        | Except.ok v    => Except.ok (combine v self)
         | Except.error e => Except.error e
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
 /- A vector value, abstracted to an opaque handle. The behaviour under spec
@@ -116,14 +116,12 @@
   ensures out = addSpec self other
   do
     -- impl-start
-    -- Absorb the additive identity BEFORE attempting any coercion, so the
-    -- identity yields `self` instead of being rejected; otherwise coerce the
-    -- operand to vector form and combine, propagating the rejection unchanged.
     let result : Except AddErr VecVal :=
-      if isZeroOperand other then Except.ok self
-      else match asVector other with
-        | Except.ok v    => Except.ok (combine self v)
-        | Except.error e => Except.error e
+      if isZeroOperand other then
+        (match asVector other with
+         | Except.ok v    => Except.ok (combine self v)
+         | Except.error e => Except.error e)
+      else Except.ok self
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
 /- A vector value, abstracted to an opaque handle. The behaviour under spec
@@ -116,15 +116,12 @@
   ensures out = addSpec self other
   do
     -- impl-start
-    -- Absorb the additive identity BEFORE attempting any coercion, so the
-    -- identity yields `self` instead of being rejected; otherwise coerce the
-    -- operand to vector form and combine, propagating the rejection unchanged.
-    let result : Except AddErr VecVal :=
-      if isZeroOperand other then Except.ok self
-      else match asVector other with
-        | Except.ok v    => Except.ok (combine self v)
-        | Except.error e => Except.error e
-    return result
+    let mut k : Nat := 0
+    while k = 0
+    invariant True
+    do
+      k := 0
+    return Except.ok self
     -- impl-end
 
 prove_correct vectorAdd by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A vector value, abstracted to an opaque handle. The behaviour under spec
   observes a vector value in only two ways: by identity (returning the very
   same vector unchanged), and through the unchanged binary combination of two
   vectors (`combine` below). The internal component representation is never
   inspected by this behaviour, so it is abstracted away. Provenance + executable
   soundness check: mapping.md §1 / axiom_check.py (G-AX). -/
structure VecVal where
  handle : Int
  deriving DecidableEq, Inhabited

/- The right operand of the combination, classified into the three shapes the
   behaviour distinguishes:

     * `zero`    — the additive identity (a non-vector value that compares equal
                   to the additive identity, e.g. the neutral element a running
                   total is seeded with). It is NOT itself a vector.
     * `vec v`   — a genuine, non-identity vector value.
     * `foreign` — any other value that is neither a vector nor the additive
                   identity.

   These are exactly the classes the desired behaviour treats differently
   (mapping.md §2). -/
inductive Operand where
  | zero
  | vec (v : VecVal)
  | foreign
  deriving DecidableEq

/- The single distinguished failure outcome: the operand could not be brought
   into vector form (the type error a downstream coercion raises when handed a
   value that is not a vector). -/
inductive AddErr where
  | notAVector
  deriving DecidableEq

/- The UNCHANGED operand-coercion callee, modeled DEEPLY: it accepts a genuine
   vector unchanged, and rejects everything else (the additive identity and any
   foreign value) with the type-error outcome. This callee is invoked, never
   redefined, by the behaviour under spec; spelling it out makes it an
   A-reference validated == the real callee by G-AX. Provenance: mapping.md §3.1
   / axiom_check.py. -/
def asVector : Operand → Except AddErr VecVal
  | .vec v   => Except.ok v
  | .zero    => Except.error .notAVector
  | .foreign => Except.error .notAVector

/- The UNCHANGED binary combination of two genuine vector values (the
   constructor that builds the combined vector). Its concrete result is
   orthogonal to the behaviour under spec — only that it combines two vectors
   into a vector matters — so it is modeled `opaque` with NO
   asserted `ensures` (it is the same function in the spec and in the impl, so it
   is grounded, not an oracle). Provenance + executable soundness check:
   mapping.md §3.2 / axiom_check.py (G-AX). -/
opaque combine : VecVal → VecVal → VecVal
-- axioms-end

-- pure-start
/- Whether the right operand is the additive identity — the value that compares
   equal to the neutral element of addition. True for the identity, False for a
   genuine vector and for any foreign value. -/
def isZeroOperand : Operand → Bool
  | .zero    => true
  | .vec _   => false
  | .foreign => false

/- The desired result of combining a vector `self` with a right operand:

     * if the operand is the additive identity, the combination ABSORBS it and
       yields `self` unchanged — no coercion is attempted, so no type error can
       arise from the identity;
     * otherwise the operand is coerced to vector form (a genuine vector passes;
       anything else is rejected with the type-error outcome) and, on success,
       the two vectors are combined.

   The absorbing case is the behaviour the public report asks for: seeding a
   running total with the additive identity and adding a vector must succeed,
   returning the vector, rather than failing the coercion. -/
def addSpec (self : VecVal) (other : Operand) : Except AddErr VecVal :=
  if isZeroOperand other then Except.ok self
  else match asVector other with
    | Except.ok v    => Except.ok (combine self v)
    | Except.error e => Except.error e
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine a vector `self` with a right operand `other`, taking care of the
   additive identity.

   Desired behaviour: when `other` is the additive identity, the combination
   absorbs it and returns `self` unchanged (the missing behaviour the public
   report exhibits — seeding a running total with the identity and adding a
   vector must not fail). Otherwise the operand is coerced to vector form: a
   genuine vector is accepted and the two are combined; any other value is
   rejected with the type-error outcome.

   Both `self` and `other` are read-only (not `mut`): the combination computes a
   fresh result and mutates neither operand (directive 5). A vector value is
   modeled as an opaque handle; the only observations are identity and the
   unchanged binary combination (mapping.md §1-2). -/
method vectorAdd (self : VecVal) (other : Operand)
    return (out : Except AddErr VecVal)
  ensures out = addSpec self other
  do
    -- impl-start
    let result : Except AddErr VecVal :=
      if isZeroOperand other then Except.ok self
      else match asVector other with
        | Except.ok v    => Except.ok (combine self v)
        | Except.error e => Except.error e
    return result
    -- impl-end

prove_correct vectorAdd by
  loom_solve
  simp_all [addSpec]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition is `ensures out = addSpec self other` — EXACT functional equality to a total, fully-defined pure function (addSpec routes through deep asVector + opaque combine). Any verifying impl must be extensionally equal to addSpec on the whole modeled domain, so no same-spec weakness exists to exploit. Ran 7 distinct same-spec attacks (all same_spec=True via swebench_unified.markers.same_spec, velvet) + the correct reformulation as positive control; verified concurrently in batches of 4 via `bash scripts/lean_verify.sh <f>`.

### RESULTS (exit 0=verifies, 1=rejected):
- atk_1 (prepatch bug: unconditional coercion, no zero-guard) -> exit 1 REJECTED. Unsolved goal is exactly the zero-guard clause (isZeroOperand other=true => Except.ok self vs the coercion's Except.error). PREPATCH REPRODUCED.
- atk_2 (always Except.ok self; drops coercion+combine) -> exit 1 REJECTED (wrong on .vec and .foreign).
- atk_3 (boundary: absorb zero, but return self instead of combine self v on .vec) -> exit 1 REJECTED.
- atk_4 (control-flow-effect: swallow coercion error into Except.ok self on .foreign) -> exit 1 REJECTED.
- atk_5 (ungrounded-oracle-echo: combine v self instead of combine self v) -> exit 1 REJECTED. `combine` is opaque, so arg-swap is unprovable — confirms it is GROUNDED (same fn in spec & impl), not an echoable oracle.
- atk_6 (partial-domain: negated guard test) -> exit 1 REJECTED (wrong on every input).
- atk_7 (divergence: `while k=0 do k:=0` then return Except.ok self — the partial-correctness / demonic-choice escape hatch) -> exit 1 REJECTED. loom_solve still discharges the post-loop return's postcondition; the non-zero branch goal (Except.ok self = match asVector other ...) is unsolved. Partial termination gives NO free pass here.
- atk_8 (correct reformulation, nested if/match) -> exit 0 VERIFIES (positive control).
- Real Solution.lean -> exit 0 VERIFIES.

MANDATORY RESOLVE STEP: NO wrong impl verified, so there is no verifying-wrong-impl whose faithful refined patch must be run through run_resolve. patches={} (nothing to materialize). The protocol's BROKEN condition (a verifying wrong impl whose faithful patch does not resolve) cannot be triggered — vacuously satisfied. Gold patch is verbatim in patch.diff / frozen dataset (`if other == 0: return self` guard) and is the correctness oracle (G-RESOLVE).

REFINEMENT.MD AUDIT (step 3): legs 1,2=R; leg 3=I (the inserted guard, transliterated); legs 4,5=A-reference (asVector<=>_check_vector deep; combine<=>Vector(self.args+other.args) opaque, no ensures). No consumed axiom, no `:|` stub, NO kind-3 leg. A-reference correspondence holds and is corroborated by the attacks: atk_5 shows combine is grounded (not an oracle echo); atk_4 shows the error-leg<=>TypeError correspondence is load-bearing. All legs are R/A-reference/I.

Verdict SOUND: 7 attacks (>=5, incl. prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, divergence) all rejected by the spec; positive controls verify; no resolve run was needed because none verified. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_8.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A vector value, abstracted to an opaque handle. The behaviour under spec
   observes a vector value in only two ways: by identity (returning the very
   same vector unchanged), and through the unchanged binary combination of two
   vectors (`combine` below). The internal component representation is never
   inspected by this behaviour, so it is abstracted away. Provenance + executable
   soundness check: mapping.md §1 / axiom_check.py (G-AX). -/
structure VecVal where
  handle : Int
  deriving DecidableEq, Inhabited

/- The right operand of the combination, classified into the three shapes the
   behaviour distinguishes:

     * `zero`    — the additive identity (a non-vector value that compares equal
                   to the additive identity, e.g. the neutral element a running
                   total is seeded with). It is NOT itself a vector.
     * `vec v`   — a genuine, non-identity vector value.
     * `foreign` — any other value that is neither a vector nor the additive
                   identity.

   These are exactly the classes the desired behaviour treats differently
   (mapping.md §2). -/
inductive Operand where
  | zero
  | vec (v : VecVal)
  | foreign
  deriving DecidableEq

/- The single distinguished failure outcome: the operand could not be brought
   into vector form (the type error a downstream coercion raises when handed a
   value that is not a vector). -/
inductive AddErr where
  | notAVector
  deriving DecidableEq

/- The UNCHANGED operand-coercion callee, modeled DEEPLY: it accepts a genuine
   vector unchanged, and rejects everything else (the additive identity and any
   foreign value) with the type-error outcome. This callee is invoked, never
   redefined, by the behaviour under spec; spelling it out makes it an
   A-reference validated == the real callee by G-AX. Provenance: mapping.md §3.1
   / axiom_check.py. -/
def asVector : Operand → Except AddErr VecVal
  | .vec v   => Except.ok v
  | .zero    => Except.error .notAVector
  | .foreign => Except.error .notAVector

/- The UNCHANGED binary combination of two genuine vector values (the
   constructor that builds the combined vector). Its concrete result is
   orthogonal to the behaviour under spec — only that it combines two vectors
   into a vector matters — so it is modeled `opaque` with NO
   asserted `ensures` (it is the same function in the spec and in the impl, so it
   is grounded, not an oracle). Provenance + executable soundness check:
   mapping.md §3.2 / axiom_check.py (G-AX). -/
opaque combine : VecVal → VecVal → VecVal
-- axioms-end

-- pure-start
/- Whether the right operand is the additive identity — the value that compares
   equal to the neutral element of addition. True for the identity, False for a
   genuine vector and for any foreign value. -/
def isZeroOperand : Operand → Bool
  | .zero    => true
  | .vec _   => false
  | .foreign => false

/- The desired result of combining a vector `self` with a right operand:

     * if the operand is the additive identity, the combination ABSORBS it and
       yields `self` unchanged — no coercion is attempted, so no type error can
       arise from the identity;
     * otherwise the operand is coerced to vector form (a genuine vector passes;
       anything else is rejected with the type-error outcome) and, on success,
       the two vectors are combined.

   The absorbing case is the behaviour the public report asks for: seeding a
   running total with the additive identity and adding a vector must succeed,
   returning the vector, rather than failing the coercion. -/
def addSpec (self : VecVal) (other : Operand) : Except AddErr VecVal :=
  if isZeroOperand other then Except.ok self
  else match asVector other with
    | Except.ok v    => Except.ok (combine self v)
    | Except.error e => Except.error e
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine a vector `self` with a right operand `other`, taking care of the
   additive identity.

   Desired behaviour: when `other` is the additive identity, the combination
   absorbs it and returns `self` unchanged (the missing behaviour the public
   report exhibits — seeding a running total with the identity and adding a
   vector must not fail). Otherwise the operand is coerced to vector form: a
   genuine vector is accepted and the two are combined; any other value is
   rejected with the type-error outcome.

   Both `self` and `other` are read-only (not `mut`): the combination computes a
   fresh result and mutates neither operand (directive 5). A vector value is
   modeled as an opaque handle; the only observations are identity and the
   unchanged binary combination (mapping.md §1-2). -/
method vectorAdd (self : VecVal) (other : Operand)
    return (out : Except AddErr VecVal)
  ensures out = addSpec self other
  do
    -- impl-start
    let result : Except AddErr VecVal :=
      if isZeroOperand other then Except.ok self
      else match asVector other with
        | Except.ok v    => Except.ok (combine self v)
        | Except.error e => Except.error e
    return result
    -- impl-end

prove_correct vectorAdd by
  loom_solve
  simp_all [addSpec]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition is `ensures out = addSpec self other` — EXACT functional equality to a total, fully-defined pure function (addSpec routes through deep asVector + opaque combine). Any verifying impl must be extensionally equal to addSpec on the whole modeled domain, so no same-spec weakness exists to exploit. Ran 7 distinct same-spec attacks (all same_spec=True via swebench_unified.markers.same_spec, velvet) + the correct reformulation as positive control; verified concurrently in batches of 4 via `bash scripts/lean_verify.sh <f>`.

### RESULTS (exit 0=verifies, 1=rejected):
- atk_1 (prepatch bug: unconditional coercion, no zero-guard) -> exit 1 REJECTED. Unsolved goal is exactly the zero-guard clause (isZeroOperand other=true => Except.ok self vs the coercion's Except.error). PREPATCH REPRODUCED.
- atk_2 (always Except.ok self; drops coercion+combine) -> exit 1 REJECTED (wrong on .vec and .foreign).
- atk_3 (boundary: absorb zero, but return self instead of combine self v on .vec) -> exit 1 REJECTED.
- atk_4 (control-flow-effect: swallow coercion error into Except.ok self on .foreign) -> exit 1 REJECTED.
- atk_5 (ungrounded-oracle-echo: combine v self instead of combine self v) -> exit 1 REJECTED. `combine` is opaque, so arg-swap is unprovable — confirms it is GROUNDED (same fn in spec & impl), not an echoable oracle.
- atk_6 (partial-domain: negated guard test) -> exit 1 REJECTED (wrong on every input).
- atk_7 (divergence: `while k=0 do k:=0` then return Except.ok self — the partial-correctness / demonic-choice escape hatch) -> exit 1 REJECTED. loom_solve still discharges the post-loop return's postcondition; the non-zero branch goal (Except.ok self = match asVector other ...) is unsolved. Partial termination gives NO free pass here.
- atk_8 (correct reformulation, nested if/match) -> exit 0 VERIFIES (positive control).
- Real Solution.lean -> exit 0 VERIFIES.

MANDATORY RESOLVE STEP: NO wrong impl verified, so there is no verifying-wrong-impl whose faithful refined patch must be run through run_resolve. patches={} (nothing to materialize). The protocol's BROKEN condition (a verifying wrong impl whose faithful patch does not resolve) cannot be triggered — vacuously satisfied. Gold patch is verbatim in patch.diff / frozen dataset (`if other == 0: return self` guard) and is the correctness oracle (G-RESOLVE).

REFINEMENT.MD AUDIT (step 3): legs 1,2=R; leg 3=I (the inserted guard, transliterated); legs 4,5=A-reference (asVector<=>_check_vector deep; combine<=>Vector(self.args+other.args) opaque, no ensures). No consumed axiom, no `:|` stub, NO kind-3 leg. A-reference correspondence holds and is corroborated by the attacks: atk_5 shows combine is grounded (not an oracle echo); atk_4 shows the error-leg<=>TypeError correspondence is load-bearing. All legs are R/A-reference/I.

Verdict SOUND: 7 attacks (>=5, incl. prepatch, partial-domain, boundary, control-flow-effect, ungrounded-oracle-echo, divergence) all rejected by the spec; positive controls verify; no resolve run was needed because none verified. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO drift. Spec region byte-identical (same_spec=True with VelvetBackend; region hashes match meta.json). Empirically validated the modeled vectorAdd/addSpec against the REAL patched Vector.__add__ at base_commit c6753448 (gold patch applied), running old sympy under a collections.abc/getargspec shim on py3.11.

Operand classification is total and grounded in the real predicates (isZeroOperand ↔ `other == 0`, asVector ↔ `_check_vector`), not an oracle. Verified agreement on every class:
- zero class {0, S.Zero, Integer(0), 0.0, False, Rational(0), empty vector 0*N.x}: model→Except.ok self; real→returns `self` ITSELF (identity `is` True). Faithful, incl. the `= self` (not just 'succeeds') pin.
- vec class {N.y, genuine vectors}: model→Except.ok (combine self v); real→combined Vector. Faithful.
- foreign class {1, 3.5, 'x', Symbol('x'), True}: model→Except.error .notAVector; real→TypeError. Faithful.

Empty-vector aliasing (0*N.x == 0) correctly classified as zero and excluded from the genuine-vec pool (mapping.md §3.1; G-AX confirmed disjointness). Ran conformance_check.py against the real patched repo: 0 disagreements over 100000 adds (seed=14711). Solution.lean verifies (exit 0); prepatch fails exactly on the discriminating goal isZeroOperand other=true → …=Except.ok self, confirming the bug is real and the spec is not too weak. The spec is neither too strong nor drifting — no diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** same_spec(Solution.lean, Solution_prepatch.lean, velvet tables) == True — spec region is byte-identical; only impl/proof differ. Judged the elided spec_view (impl-start/impl-end and prove_correct bodies removed) against the PUBLIC problem_statement only (hints_text empty).

The gold edit is a two-line guard `if other == 0: return self` at the top of Vector.__add__, before the unchanged `_check_vector` coercion and the `Vector(self.args + other.args)` combination. The spec_view models exactly this: addSpec/vectorAdd = `if isZeroOperand other then Except.ok self else match asVector other …`, with narrative comments describing identity-absorption→return self, else coerce-and-combine.

Crucially, the public problem_statement ALREADY discloses the entire gold fix and more: its traceback prints the source verbatim including the commented-out fix line `60  #if other == 0: return self`, plus `_check_vector(other)` raising `TypeError('A Vector must be supplied')` and `return Vector(self.args + other.args)`. Thus every behavioural fact the spec view pins (absorb 0 → return self; else coerce/combine; error is the type error) is public knowledge from problem_statement — in fact problem_statement leaks the literal Python patch line, whereas the spec view only expresses it abstractly.

Nothing in the spec view exceeds the public statement: no gold-patch file:line beyond vector.py:58-60 (already shown in the public traceback), no gold-only detail. Comment references are to "the public report"/mapping.md/G-AX provenance, kept abstract and grounded in the input `self`, not an oracle. asVector/combine are honest models of the untouched public callees (_check_vector at 723-726, Vector(...) at 60), also visible in the public traceback. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
