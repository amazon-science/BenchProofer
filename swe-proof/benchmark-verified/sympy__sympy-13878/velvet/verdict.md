# P2 adversarial audit — sympy__sympy-13878

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,17 +112,7 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
-    let onSupport : Expr :=
-      Expr.div
-        (Expr.mul (Expr.natLit 2)
-          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
-        Expr.pi
-    return Expr.piecewise3
-      Expr.zero (Expr.lt x a)
-      onSupport (Expr.le x b)
-      Expr.one Expr.top
+    return Expr.integralFallback x x
     -- impl-end
 
 prove_correct arcsinCdfBuild by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,11 +112,9 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
     let onSupport : Expr :=
       Expr.div
-        (Expr.mul (Expr.natLit 2)
+        (Expr.mul (Expr.natLit 3)
           (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
         Expr.pi
     return Expr.piecewise3
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,12 +112,10 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
     let onSupport : Expr :=
       Expr.div
         (Expr.mul (Expr.natLit 2)
-          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
+          (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a))))
         Expr.pi
     return Expr.piecewise3
       Expr.zero (Expr.lt x a)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,12 +112,10 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
     let onSupport : Expr :=
       Expr.div
         (Expr.mul (Expr.natLit 2)
-          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
+          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub a x) (Expr.sub b a)))))
         Expr.pi
     return Expr.piecewise3
       Expr.zero (Expr.lt x a)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,16 +112,14 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
     let onSupport : Expr :=
       Expr.div
         (Expr.mul (Expr.natLit 2)
           (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
         Expr.pi
     return Expr.piecewise3
-      Expr.zero (Expr.lt x a)
-      onSupport (Expr.le x b)
+      Expr.zero (Expr.le x a)
+      onSupport (Expr.lt x b)
       Expr.one Expr.top
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,17 +112,15 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
     let onSupport : Expr :=
       Expr.div
         (Expr.mul (Expr.natLit 2)
           (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
         Expr.pi
     return Expr.piecewise3
-      Expr.zero (Expr.lt x a)
+      Expr.one (Expr.lt x a)
       onSupport (Expr.le x b)
-      Expr.one Expr.top
+      Expr.zero Expr.top
     -- impl-end
 
 prove_correct arcsinCdfBuild by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,13 +112,9 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
     let onSupport : Expr :=
-      Expr.div
-        (Expr.mul (Expr.natLit 2)
-          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
-        Expr.pi
+      Expr.mul (Expr.natLit 2)
+        (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a))))
     return Expr.piecewise3
       Expr.zero (Expr.lt x a)
       onSupport (Expr.le x b)
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,17 +112,7 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
-    let onSupport : Expr :=
-      Expr.div
-        (Expr.mul (Expr.natLit 2)
-          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
-        Expr.pi
-    return Expr.piecewise3
-      Expr.zero (Expr.lt x a)
-      onSupport (Expr.le x b)
-      Expr.one Expr.top
+    return arcsinExprCdf b a x
     -- impl-end
 
 prove_correct arcsinCdfBuild by
```

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

```diff
@@ -112,12 +112,10 @@
   ensures out = arcsinExprCdf a b x
   do
     -- impl-start
-    -- Build the three-clause closed form directly from the operands `a`, `b`,
-    -- `x`. The middle clause is the inverse-sine expression on the support.
     let onSupport : Expr :=
       Expr.div
         (Expr.mul (Expr.natLit 2)
-          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
+          (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b x)))))
         Expr.pi
     return Expr.piecewise3
       Expr.zero (Expr.lt x a)
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real construction is a straight-line build of a
   fixed-shape expression object (a bounded tree of constructor applications)
   and always terminates, so a diverging implementation must NOT satisfy this
   spec. Partial correctness would let a non-terminating body discharge the
   postcondition vacuously — an implementation that never produces the
   closed-form object at all. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The desired behaviour is the construction of a specific
   closed-form expression object for the cumulative distribution of a
   bounded-support, two-parameter continuous distribution; that object is
   modeled DEEPLY as a transparent expression value in the `pure` region
   (`arcsinExprCdf`), parameterised by the symbolic operands. No module-level
   `axiom` is used or required. The carrier↔library-object correspondence is a
   pure constructor bijection, validated end-to-end against the real library by
   the conformance check (G-CONF). -/
-- axioms-end

-- pure-start
/- A finite expression carrier: the fragment of symbolic terms that this
   distribution's closed-form cumulative function is built from. It is an
   honest data carrier — each node is a concrete constructor referring to its
   sub-operands, with NO opaque "answer" node. The desired output is produced
   by applying these constructors to the actual symbolic operands, so a builder
   that did not compute it cannot echo an answer key: it would have to emit a
   different tree.

   Constructors model exactly the library term-builders the closed form uses:
   the rational unit/zero and small integer literals, the circle constant, the
   field operations (`div`/`mul`/`sub`), the inverse-sine and square-root
   functions, the two order relations (strict `lt` and non-strict `le`), the
   always-true guard `top`, and a three-clause case split `piecewise3`. The
   `integralFallback` node models the SEPARATE, generic value produced when no
   closed form is supplied and the cumulative function is instead obtained by
   the default definite-integration route (used only by the pre-change
   skeleton). -/
inductive Expr where
  | zero
  | one
  | natLit (n : Nat)
  | pi
  | div (a b : Expr)
  | mul (a b : Expr)
  | sub (a b : Expr)
  | asin (e : Expr)
  | sqrt (e : Expr)
  | lt (a b : Expr)
  | le (a b : Expr)
  | top
  | piecewise3 (v1 c1 v2 c2 v3 c3 : Expr)
  | integralFallback (lo hi : Expr)
  deriving DecidableEq, Inhabited

/- The closed-form cumulative distribution of the two-parameter,
   bounded-support distribution whose density is supported on the open interval
   between its two endpoints, as a function of its lower endpoint `a`, its upper
   endpoint `b`, and the evaluation point `x`. It is a three-clause case split:

     • below the lower endpoint  (`x < a`)            → `0`
     • on the support up to `b`  (`x ≤ b`)            → `2·asin(√((x-a)/(b-a)))/π`
     • otherwise                                       → `1`

   This is the per-operand expansion of the desired result object: every node is
   built from `a`, `b`, `x`, the rational constants, and `π` — the result is
   forced to be *produced by* these operands, never an opaque constant. -/
def arcsinExprCdf (a b x : Expr) : Expr :=
  Expr.piecewise3
    Expr.zero (Expr.lt x a)
    (Expr.div
      (Expr.mul (Expr.natLit 2)
        (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
      Expr.pi) (Expr.le x b)
    Expr.one Expr.top

@[grind] lemma arcsinExprCdf_def (a b x : Expr) :
    arcsinExprCdf a b x =
      Expr.piecewise3
        Expr.zero (Expr.lt x a)
        (Expr.div
          (Expr.mul (Expr.natLit 2)
            (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
          Expr.pi) (Expr.le x b)
        Expr.one Expr.top := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the closed-form cumulative distribution value for the two-parameter,
   bounded-support continuous distribution from its lower endpoint `a`, upper
   endpoint `b`, and evaluation point `x`.

   Desired behaviour: the cumulative distribution must be returned as the exact
   closed-form case split below — `0` below the lower endpoint, the inverse-sine
   expression on the support, `1` above the upper endpoint — rather than left as
   a generic definite-integral object (which is what is produced when no closed
   form is available and is, for this distribution, not a usable result). The
   output object is pinned operand-by-operand so that only the intended
   expression — not a numerically-equal but differently-shaped one — satisfies
   the contract. -/
method arcsinCdfBuild (a : Expr) (b : Expr) (x : Expr) return (out : Expr)
  ensures out = arcsinExprCdf a b x
  do
    -- impl-start
    let num : Expr := Expr.sub x a
    let den : Expr := Expr.sub b a
    let inner : Expr := Expr.sqrt (Expr.div num den)
    let onSupport : Expr := Expr.div (Expr.mul (Expr.natLit 2) (Expr.asin inner)) Expr.pi
    return Expr.piecewise3
      Expr.zero (Expr.lt x a)
      onSupport (Expr.le x b)
      Expr.one Expr.top
    -- impl-end

prove_correct arcsinCdfBuild by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec pins output by EXACT structural equality to a transparent, operand-grounded tree: `ensures out = arcsinExprCdf a b x`, where arcsinExprCdf is a fully-unfolded `def` building piecewise3(zero,(lt x a); div(mul(natLit 2)(asin(sqrt(div(sub x a)(sub b a)))))(pi),(le x b); one,top) from a,b,x. This is the accepted grounded-oracle shape: operands appear in the result, no opaque answer node, so no *wrong* echo can satisfy it.

All files same_spec=True vs the frozen Solution.lean (verified via swebench_unified.markers.same_spec, velvet backend). lean_verify.sh (bash scripts/lean_verify.sh <f>) results:
- atk_1 prepatch bug `integralFallback x x` -> exit 1 (rejected; goal `x.integralFallback x = arcsinExprCdf a b x` unsolved). PREPATCH REPRODUCED.
- atk_2 wrong constant natLit 3 (3*asin/pi) -> exit 1.
- atk_3 dropped `asin` (partial-domain / sqrt only) -> exit 1.
- atk_4 swapped subtraction (a-x) numerator (boundary/arg-order) -> exit 1.
- atk_5 swapped/boundary relations (le x a / lt x b) -> exit 1.
- atk_6 swapped tail values (one below a, zero above b) (control-flow-effect) -> exit 1.
- atk_7 missing /pi (ungrounded shape) -> exit 1.
- atk_9 ungrounded-oracle echo `arcsinExprCdf b a x` (operands swapped) -> exit 1.
- atk_10 wrong denominator (b-x) instead of (b-a) -> exit 1.
- atk_8 control-flow-obfuscated impl (match on `a` reassembling the IDENTICAL tree) -> exit 0 VERIFIES, but it emits the exact gold tree (defeq to arcsinExprCdf a b x): a CORRECT impl, NOT a verifying-wrong impl. Its faithful patch is still the gold `_cdf`.
- atk_pc positive control (same final tree via let-bindings) -> exit 0. Spec is non-vacuous.

No verifying-but-wrong impl was found: the exact-equality pin admits only impls that build the identical gold Expr tree, all 9 genuinely-wrong deviations rejected. `patches` is therefore empty (no verifying wrong impl to materialize).

HARNESS CORRESPONDENCE CHECK (mandatory resolve): every admitted impl's faithful refined patch IS the gold `_cdf` (verbatim patch.diff, the whole modeled site being an A-reference deep model). Ran it through the official harness: run_resolve('sympy__sympy-13878', patch.diff, run_id='atk8_faithful_13878', timeout=1800, retries=1) on active backend swe_bench_verified (supports_docker_oracle=True, style=swebench) -> RESOLVED=True, COMPLETED=True, note='resolved'. So verify => resolve holds for the entire admitted class.

Refinement.md audit: all legs R (A1 operands->Symbols), I with R on leaves (A2/A3 constructor-for-constructor), and one A-reference (arcsinExprCdf deep model == real cdf(Arcsin) validated by G-CONF, which PASSES). No kind-3 (the changed op — closed-form CDF construction — is modeled deeply, not axiom-hidden). No consumed axiom; G-AX skip legitimate (zero module-level axioms in Solution.lean). Deep-model correspondence to the real callee holds and is exercised end-to-end by G-CONF (100k structural-equality configs). No defect. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean`, `atk_10.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_10.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real construction is a straight-line build of a
   fixed-shape expression object (a bounded tree of constructor applications)
   and always terminates, so a diverging implementation must NOT satisfy this
   spec. Partial correctness would let a non-terminating body discharge the
   postcondition vacuously — an implementation that never produces the
   closed-form object at all. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The desired behaviour is the construction of a specific
   closed-form expression object for the cumulative distribution of a
   bounded-support, two-parameter continuous distribution; that object is
   modeled DEEPLY as a transparent expression value in the `pure` region
   (`arcsinExprCdf`), parameterised by the symbolic operands. No module-level
   `axiom` is used or required. The carrier↔library-object correspondence is a
   pure constructor bijection, validated end-to-end against the real library by
   the conformance check (G-CONF). -/
-- axioms-end

-- pure-start
/- A finite expression carrier: the fragment of symbolic terms that this
   distribution's closed-form cumulative function is built from. It is an
   honest data carrier — each node is a concrete constructor referring to its
   sub-operands, with NO opaque "answer" node. The desired output is produced
   by applying these constructors to the actual symbolic operands, so a builder
   that did not compute it cannot echo an answer key: it would have to emit a
   different tree.

   Constructors model exactly the library term-builders the closed form uses:
   the rational unit/zero and small integer literals, the circle constant, the
   field operations (`div`/`mul`/`sub`), the inverse-sine and square-root
   functions, the two order relations (strict `lt` and non-strict `le`), the
   always-true guard `top`, and a three-clause case split `piecewise3`. The
   `integralFallback` node models the SEPARATE, generic value produced when no
   closed form is supplied and the cumulative function is instead obtained by
   the default definite-integration route (used only by the pre-change
   skeleton). -/
inductive Expr where
  | zero
  | one
  | natLit (n : Nat)
  | pi
  | div (a b : Expr)
  | mul (a b : Expr)
  | sub (a b : Expr)
  | asin (e : Expr)
  | sqrt (e : Expr)
  | lt (a b : Expr)
  | le (a b : Expr)
  | top
  | piecewise3 (v1 c1 v2 c2 v3 c3 : Expr)
  | integralFallback (lo hi : Expr)
  deriving DecidableEq, Inhabited

/- The closed-form cumulative distribution of the two-parameter,
   bounded-support distribution whose density is supported on the open interval
   between its two endpoints, as a function of its lower endpoint `a`, its upper
   endpoint `b`, and the evaluation point `x`. It is a three-clause case split:

     • below the lower endpoint  (`x < a`)            → `0`
     • on the support up to `b`  (`x ≤ b`)            → `2·asin(√((x-a)/(b-a)))/π`
     • otherwise                                       → `1`

   This is the per-operand expansion of the desired result object: every node is
   built from `a`, `b`, `x`, the rational constants, and `π` — the result is
   forced to be *produced by* these operands, never an opaque constant. -/
def arcsinExprCdf (a b x : Expr) : Expr :=
  Expr.piecewise3
    Expr.zero (Expr.lt x a)
    (Expr.div
      (Expr.mul (Expr.natLit 2)
        (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
      Expr.pi) (Expr.le x b)
    Expr.one Expr.top

@[grind] lemma arcsinExprCdf_def (a b x : Expr) :
    arcsinExprCdf a b x =
      Expr.piecewise3
        Expr.zero (Expr.lt x a)
        (Expr.div
          (Expr.mul (Expr.natLit 2)
            (Expr.asin (Expr.sqrt (Expr.div (Expr.sub x a) (Expr.sub b a)))))
          Expr.pi) (Expr.le x b)
        Expr.one Expr.top := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the closed-form cumulative distribution value for the two-parameter,
   bounded-support continuous distribution from its lower endpoint `a`, upper
   endpoint `b`, and evaluation point `x`.

   Desired behaviour: the cumulative distribution must be returned as the exact
   closed-form case split below — `0` below the lower endpoint, the inverse-sine
   expression on the support, `1` above the upper endpoint — rather than left as
   a generic definite-integral object (which is what is produced when no closed
   form is available and is, for this distribution, not a usable result). The
   output object is pinned operand-by-operand so that only the intended
   expression — not a numerically-equal but differently-shaped one — satisfies
   the contract. -/
method arcsinCdfBuild (a : Expr) (b : Expr) (x : Expr) return (out : Expr)
  ensures out = arcsinExprCdf a b x
  do
    -- impl-start
    let num : Expr := Expr.sub x a
    let den : Expr := Expr.sub b a
    let inner : Expr := Expr.sqrt (Expr.div num den)
    let onSupport : Expr := Expr.div (Expr.mul (Expr.natLit 2) (Expr.asin inner)) Expr.pi
    return Expr.piecewise3
      Expr.zero (Expr.lt x a)
      onSupport (Expr.le x b)
      Expr.one Expr.top
    -- impl-end

prove_correct arcsinCdfBuild by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ SOUND. Spec pins output by EXACT structural equality to a transparent, operand-grounded tree: `ensures out = arcsinExprCdf a b x`, where arcsinExprCdf is a fully-unfolded `def` building piecewise3(zero,(lt x a); div(mul(natLit 2)(asin(sqrt(div(sub x a)(sub b a)))))(pi),(le x b); one,top) from a,b,x. This is the accepted grounded-oracle shape: operands appear in the result, no opaque answer node, so no *wrong* echo can satisfy it.

All files same_spec=True vs the frozen Solution.lean (verified via swebench_unified.markers.same_spec, velvet backend). lean_verify.sh (bash scripts/lean_verify.sh <f>) results:
- atk_1 prepatch bug `integralFallback x x` -> exit 1 (rejected; goal `x.integralFallback x = arcsinExprCdf a b x` unsolved). PREPATCH REPRODUCED.
- atk_2 wrong constant natLit 3 (3*asin/pi) -> exit 1.
- atk_3 dropped `asin` (partial-domain / sqrt only) -> exit 1.
- atk_4 swapped subtraction (a-x) numerator (boundary/arg-order) -> exit 1.
- atk_5 swapped/boundary relations (le x a / lt x b) -> exit 1.
- atk_6 swapped tail values (one below a, zero above b) (control-flow-effect) -> exit 1.
- atk_7 missing /pi (ungrounded shape) -> exit 1.
- atk_9 ungrounded-oracle echo `arcsinExprCdf b a x` (operands swapped) -> exit 1.
- atk_10 wrong denominator (b-x) instead of (b-a) -> exit 1.
- atk_8 control-flow-obfuscated impl (match on `a` reassembling the IDENTICAL tree) -> exit 0 VERIFIES, but it emits the exact gold tree (defeq to arcsinExprCdf a b x): a CORRECT impl, NOT a verifying-wrong impl. Its faithful patch is still the gold `_cdf`.
- atk_pc positive control (same final tree via let-bindings) -> exit 0. Spec is non-vacuous.

No verifying-but-wrong impl was found: the exact-equality pin admits only impls that build the identical gold Expr tree, all 9 genuinely-wrong deviations rejected. `patches` is therefore empty (no verifying wrong impl to materialize).

HARNESS CORRESPONDENCE CHECK (mandatory resolve): every admitted impl's faithful refined patch IS the gold `_cdf` (verbatim patch.diff, the whole modeled site being an A-reference deep model). Ran it through the official harness: run_resolve('sympy__sympy-13878', patch.diff, run_id='atk8_faithful_13878', timeout=1800, retries=1) on active backend swe_bench_verified (supports_docker_oracle=True, style=swebench) -> RESOLVED=True, COMPLETED=True, note='resolved'. So verify => resolve holds for the entire admitted class.

Refinement.md audit: all legs R (A1 operands->Symbols), I with R on leaves (A2/A3 constructor-for-constructor), and one A-reference (arcsinExprCdf deep model == real cdf(Arcsin) validated by G-CONF, which PASSES). No kind-3 (the changed op — closed-form CDF construction — is modeled deeply, not axiom-hidden). No consumed axiom; G-AX skip legitimate (zero module-level axioms in Solution.lean). Deep-model correspondence to the real callee holds and is exercised end-to-end by G-CONF (100k structural-equality configs). No defect. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / spec-too-strong) audit of sympy__sympy-13878 velvet bundle. Modeled function: arcsinCdfBuild, ensures out = arcsinExprCdf a b x (a transparent three-clause Piecewise closed form for ArcsinDistribution._cdf). Real callee: cdf(Arcsin(name,a,b))(x) at base_commit 7b127bdf... with gold patch.diff applied.

Checks performed:
1. same_spec(Solution, Solution_prepatch) via swebench_unified.markers = True — the spec region (axioms/pure/pre/post + signature + ensures) is byte-identical across the pre/post skeletons; the F2P discriminator lives only in the impl region (integralFallback vs the closed-form build). Spec region well-formed.
2. lean_verify.sh on Solution.lean → rc=0 (elaborates, no sorry/error), total correctness with demonic choice.
3. Reconstructed the patched real repo (base + patch.diff, git apply rc=0) under a py3.8+mpmath venv and confirmed cdf(Arcsin('x',a,b))(z) = Piecewise((0, a>z),(2*asin(sqrt((-a+z)/(-a+b)))/pi, b>=z),(1,True)) — matches the modeled tree after library canonicalization.
4. Ran the G-CONF SHADOW (arcsinExprCdf transliterated via mapping.md bijection) vs ORACLE (real cdf) over 402 fuzzed configs (12 symbol names x {plain,real,positive,f2p} assumptions, seed 13878) against the REAL repo: 0 disagreements under Basic.__eq__ (the exact relation FAIL_TO_PASS test_arcsin uses).
5. Targeted adversarial edge cases: numeric default endpoints (a=0,b=1), mixed assumption sets (a positive/b positive/x negative), and degenerate symbol identity (a==b, a==x) — all agree.

The modeled function reproduces the real callee's canonical Piecewise object exactly; the deep model is a transparent constructor expression over the operands (not an answer-key oracle), and a math-equal but structurally different rebuild (acos form) is correctly rejected by both the spec and the F2P assert. No input found where the modeled function disagrees with the real repo behavior. Spec is not too strong and does not drift.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (swebench_unified.leakage.screen with velvet/lean LanguageTables) PASSES on the computed spec view: no diff markers, no reproduced gold-patch line, no patched file path (sympy/stats/crv_types.py absent), no patched-symbol echo (ArcsinDistribution/_cdf never named; _cdf strips to len<4), no fix/bug narration. Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (markers.same_spec == True), so the screened view is the shared leak surface. Semantic pass: the only content beyond problem_statement is the exact closed-form CDF (arcsinExprCdf tree + prose formula 2·asin(√((x-a)/(b-a)))/π and the 3-clause piecewise 0/expr/1). This is NOT a leak: (1) the public problem_statement names the Arcsin distribution via cdf(Arcsin("x",0,3))(1), states 'The CDF is basically the arcsin function, for which the distribution is named,' and points to Wikipedia 'where the formulas for CDF can be found' — so the arcsin closed form and the asin naming are public; (2) the problem_statement itself shows the base integral-fallback behavior ('Returns Integral(...) which is incorrect, and doesn't converge'), so disclosing the integralFallback pre-state is public; (3) an exact formal postcondition is the sanctioned, inherent content of any spec (grounded transparent oracle over operands per refinement.md §A / SPEC_GUIDE directive 8) and does not reveal repo-specific gold-patch wiring (file/class dispatch, the other 11 distributions) beyond public info. The gold formula uses *,sqrt,pi; the spec view uses unicode ·,√,π and Lean Expr constructors — no verbatim reproduction even after normalization. No RELAXED_LEAKAGE.md present and none required.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
