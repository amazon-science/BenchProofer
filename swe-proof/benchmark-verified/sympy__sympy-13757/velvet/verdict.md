# P2 adversarial audit — sympy__sympy-13757

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,18 +87,10 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
-    let form :=
-      if factorsCombineIntoPolynomial
-      then ProductForm.carriedOut
-      else ProductForm.formalProduct
-    return { form := form, value := productValue }
+    if factorsCombineIntoPolynomial then
+      return { form := ProductForm.carriedOut, value := productValue }
+    else
+      return { form := ProductForm.formalProduct, value := [] }
     -- impl-end
 
 prove_correct formExpressionTimesPolynomial by
```

Attack 2 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,18 +87,10 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
-    let form :=
-      if factorsCombineIntoPolynomial
-      then ProductForm.carriedOut
-      else ProductForm.formalProduct
-    return { form := form, value := productValue }
+    if factorsCombineIntoPolynomial then
+      return { form := ProductForm.carriedOut, value := productValue }
+    else
+      return { form := ProductForm.formalProduct, value := [999] }
     -- impl-end
 
 prove_correct formExpressionTimesPolynomial by
```

Attack 3 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,18 +87,10 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
-    let form :=
-      if factorsCombineIntoPolynomial
-      then ProductForm.carriedOut
-      else ProductForm.formalProduct
-    return { form := form, value := productValue }
+    if factorsCombineIntoPolynomial then
+      return { form := ProductForm.carriedOut, value := productValue }
+    else
+      return { form := ProductForm.formalProduct, value := productValue.reverse }
     -- impl-end
 
 prove_correct formExpressionTimesPolynomial by
```

Attack 4 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,18 +87,9 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
-    let form :=
-      if factorsCombineIntoPolynomial
-      then ProductForm.carriedOut
-      else ProductForm.formalProduct
-    return { form := form, value := productValue }
+    match factorsCombineIntoPolynomial with
+    | true  => return { form := ProductForm.carriedOut, value := productValue }
+    | false => return { form := ProductForm.formalProduct, value := 0 :: productValue }
     -- impl-end
 
 prove_correct formExpressionTimesPolynomial by
```

Attack 5 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,13 +87,6 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
     let form :=
       if factorsCombineIntoPolynomial
       then ProductForm.carriedOut
```

Attack 6 — `atk_1.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,17 +87,7 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
-    let form :=
-      if factorsCombineIntoPolynomial
-      then ProductForm.carriedOut
-      else ProductForm.formalProduct
+    let form := ProductForm.formalProduct
     return { form := form, value := productValue }
     -- impl-end
 
```

Attack 7 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,17 +87,10 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
     let form :=
       if factorsCombineIntoPolynomial
-      then ProductForm.carriedOut
-      else ProductForm.formalProduct
+      then ProductForm.formalProduct
+      else ProductForm.carriedOut
     return { form := form, value := productValue }
     -- impl-end
 
```

Attack 8 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The value the product takes when it IS carried out is
@@ -87,17 +87,7 @@
   ensures factorsCombineIntoPolynomial = true → out.value = productValue
   do
     -- impl-start
-    -- The product of an ordinary left expression and a right-hand polynomial is
-    -- now handled the same way the polynomial-on-the-left product already was:
-    -- when the two factors combine into a single value
-    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
-    -- into that one value; otherwise the two factors cannot be merged and the
-    -- product is left as a formal, unevaluated product. The supplied product
-    -- value is preserved unchanged.
-    let form :=
-      if factorsCombineIntoPolynomial
-      then ProductForm.carriedOut
-      else ProductForm.formalProduct
+    let form := ProductForm.carriedOut
     return { form := form, value := productValue }
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The value the product takes when it IS carried out is
--  built by combination machinery this behaviour does NOT change; its result is
--  supplied to the operation as a free input (`productValue`), so the
--  postcondition holds for EVERY such product value — strictly weaker than any
--  concrete multiplier, hence no contract is owed (directive 7). Whether the two
--  factors combine into a single value is likewise a property of that unchanged
--  combination machinery; it is observed directly as an input, not via any
--  callee. There is no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The two observable shapes the result of forming the product of an ordinary
   expression and a polynomial can take:

   - `carriedOut`  — the product is actually performed: the two factors are
                     combined into a single evaluated value.
   - `formalProduct` — the product is left standing as an unevaluated formal
                     product of the two factors, i.e. nothing is computed. -/
inductive ProductForm where
  | carriedOut
  | formalProduct
  deriving DecidableEq, Inhabited

/- The observable result of forming the product of an ordinary expression and a
   polynomial, reduced to the two observations the desired behaviour
   distinguishes:

   - `form`  — whether the product was carried out (evaluated into a single
               value) or left as a formal, unevaluated product (mapping.md §2).
   - `value` — the value the product carries when it IS carried out: the
               evaluated product of the two factors. The combination that
               produces it is machinery the desired behaviour does NOT change,
               so it is supplied to the operation as a free input. -/
structure ProductResult where
  form : ProductForm
  value : List Int
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Form the product of an ordinary expression (on the left) and a polynomial (on
   the right).

   Desired behaviour (reported symptom: such a product "does not evaluate" when
   the expression is the left operand): when the polynomial is the right operand,
   the product must be treated the same way it already is when the polynomial is
   the left operand — namely, whenever the two factors do combine into a single
   value, that product is CARRIED OUT (actually evaluated into one value) instead
   of being left as a formal, unevaluated product of the two factors.

   Not every pair of factors combines into a single value: some left expressions
   simply do not merge with the polynomial, and for those the product is
   genuinely left formal. Whether the two factors combine into a single value is
   a property of the surrounding (unchanged) combination machinery, observed here
   directly as the input `factorsCombineIntoPolynomial`; only its truth value
   matters (mapping.md §2). The operation must:

   - carry the product out (a single evaluated value) exactly when the two
     factors combine, and
   - leave it as a formal, unevaluated product otherwise.

   The value the carried-out product takes is the evaluated product of the two
   factors, which the surrounding (unchanged) machinery supplies; this step does
   not recompute it. That supplied value is read-only (not `mut`) and must
   survive into the result unchanged (directive 5): the operation decides the
   SHAPE of the result and preserves the supplied product value. -/
method formExpressionTimesPolynomial
    (productValue : List Int) (factorsCombineIntoPolynomial : Bool)
    return (out : ProductResult)
  ensures out.form = (if factorsCombineIntoPolynomial
                      then ProductForm.carriedOut
                      else ProductForm.formalProduct)
  ensures factorsCombineIntoPolynomial = true → out.value = productValue
  do
    -- impl-start
    -- The product of an ordinary left expression and a right-hand polynomial is
    -- now handled the same way the polynomial-on-the-left product already was:
    -- when the two factors combine into a single value
    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
    -- into that one value; otherwise the two factors cannot be merged and the
    -- product is left as a formal, unevaluated product. The supplied product
    -- value is preserved unchanged.
    let form :=
      if factorsCombineIntoPolynomial
      then ProductForm.carriedOut
      else ProductForm.formalProduct
    return { form := form, value := productValue }
    -- impl-end

prove_correct formExpressionTimesPolynomial by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Bundle has NO axioms (G-AX skip in meta.json; refinement.md legs are R(row1)/I(row2)/R(row3), zero A-legs, zero kind-3). Attack surface therefore reduces to model<->patch correspondence and spec weakness; R/I legs pre-cleared by G-CONF (pass).

Spec pins out.form fully in BOTH branches (ensures out.form = if factorsCombineIntoPolynomial then carriedOut else formalProduct) and out.value ONLY in the carried-out branch (ensures factorsCombineIntoPolynomial = true -> out.value = productValue). The only impl freedom is out.value in the formal branch (factorsCombineIntoPolynomial = false). This is genuinely unobservable: per mapping.md 2/3 the formal product is an sympy.Mul (g*f.as_expr()) which has NO coefficient list, so out.value has no repo referent when the product is left formal.

Same-spec confirmed True for all 9 files (markers.same_spec, velvet). Verification (bash scripts/lean_verify.sh <f>):
- pos_control.lean (gold impl): exit 0 = VERIFIES (positive control OK).
- atk_1.lean = prepatch bug (always formalProduct): exit 1 = correctly REJECTED. Impl matches Solution_prepatch.lean modulo comments (prepatch_reproduced=true).
- atk_2.lean (swapped form): exit 1 = correctly REJECTED.
- atk_3.lean (always carriedOut): exit 1 = correctly REJECTED.
- atk_4.lean (formal-branch value := []): exit 0 = VERIFIES.
- atk_5.lean (formal-branch value := [999], boundary garbage): exit 0 = VERIFIES.
- atk_6.lean (formal-branch value := productValue.reverse): exit 0 = VERIFIES.
- atk_7.lean (match control-flow, formal-branch value := 0 :: productValue): exit 0 = VERIFIES.
- atk_8.lean (ungrounded-oracle echo, gold impl verbatim minus comments): exit 0 = VERIFIES.

Every verifying attack (atk_4..atk_8) differs from gold ONLY in the unobservable formal-branch out.value; observable behaviour (form in both branches + value when carried out) is identical to gold. Hence each attack's FAITHFUL refined patch is byte-identical to the gold patch (Poly._op_priority = 10.001) -- the divergence is in unmodeled/unobservable output, so no patch refinement can carry it into repo behaviour. That single faithful patch was RUN through the official harness (not speculated):
  python -c 'from swebench_unified.harness import run_resolve; run_resolve("sympy__sympy-13757", <faithful_patch>, run_id="sbu-resolve-audit-eq-q954d13c-faithful", timeout=1200, retries=1)'
  => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'.
faithful_patch.diff sha1=d6581fed896f33dbd079dac0c393cdfa9019600e 

Since the faithful refined patch of every verifying wrong impl RESOLVES, verify=>correct holds; no attack breaks the spec. refinement.md audit: rows tagged R/I/R only, no kind-3, no A-legs to check; model<->patch correspondence (cast success <-> carriedOut; try/except <-> if/else; g.mul(f) value <-> productValue free input) is faithful and matches mapping.md. Verdict SOUND (>=5 verifying attacks materialized + resolve-run, none breaks it). NOTE: the spec's out.value freedom in the formal branch is a correct modeling choice (unobservable), not a weakness -- an attack exploiting it produces the gold patch, which resolves.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 5 | `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 3 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_4.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 2 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 3 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 4 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 5 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_3.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The value the product takes when it IS carried out is
--  built by combination machinery this behaviour does NOT change; its result is
--  supplied to the operation as a free input (`productValue`), so the
--  postcondition holds for EVERY such product value — strictly weaker than any
--  concrete multiplier, hence no contract is owed (directive 7). Whether the two
--  factors combine into a single value is likewise a property of that unchanged
--  combination machinery; it is observed directly as an input, not via any
--  callee. There is no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The two observable shapes the result of forming the product of an ordinary
   expression and a polynomial can take:

   - `carriedOut`  — the product is actually performed: the two factors are
                     combined into a single evaluated value.
   - `formalProduct` — the product is left standing as an unevaluated formal
                     product of the two factors, i.e. nothing is computed. -/
inductive ProductForm where
  | carriedOut
  | formalProduct
  deriving DecidableEq, Inhabited

/- The observable result of forming the product of an ordinary expression and a
   polynomial, reduced to the two observations the desired behaviour
   distinguishes:

   - `form`  — whether the product was carried out (evaluated into a single
               value) or left as a formal, unevaluated product (mapping.md §2).
   - `value` — the value the product carries when it IS carried out: the
               evaluated product of the two factors. The combination that
               produces it is machinery the desired behaviour does NOT change,
               so it is supplied to the operation as a free input. -/
structure ProductResult where
  form : ProductForm
  value : List Int
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Form the product of an ordinary expression (on the left) and a polynomial (on
   the right).

   Desired behaviour (reported symptom: such a product "does not evaluate" when
   the expression is the left operand): when the polynomial is the right operand,
   the product must be treated the same way it already is when the polynomial is
   the left operand — namely, whenever the two factors do combine into a single
   value, that product is CARRIED OUT (actually evaluated into one value) instead
   of being left as a formal, unevaluated product of the two factors.

   Not every pair of factors combines into a single value: some left expressions
   simply do not merge with the polynomial, and for those the product is
   genuinely left formal. Whether the two factors combine into a single value is
   a property of the surrounding (unchanged) combination machinery, observed here
   directly as the input `factorsCombineIntoPolynomial`; only its truth value
   matters (mapping.md §2). The operation must:

   - carry the product out (a single evaluated value) exactly when the two
     factors combine, and
   - leave it as a formal, unevaluated product otherwise.

   The value the carried-out product takes is the evaluated product of the two
   factors, which the surrounding (unchanged) machinery supplies; this step does
   not recompute it. That supplied value is read-only (not `mut`) and must
   survive into the result unchanged (directive 5): the operation decides the
   SHAPE of the result and preserves the supplied product value. -/
method formExpressionTimesPolynomial
    (productValue : List Int) (factorsCombineIntoPolynomial : Bool)
    return (out : ProductResult)
  ensures out.form = (if factorsCombineIntoPolynomial
                      then ProductForm.carriedOut
                      else ProductForm.formalProduct)
  ensures factorsCombineIntoPolynomial = true → out.value = productValue
  do
    -- impl-start
    -- The product of an ordinary left expression and a right-hand polynomial is
    -- now handled the same way the polynomial-on-the-left product already was:
    -- when the two factors combine into a single value
    -- (`factorsCombineIntoPolynomial`, mapping.md §2) the product is carried out
    -- into that one value; otherwise the two factors cannot be merged and the
    -- product is left as a formal, unevaluated product. The supplied product
    -- value is preserved unchanged.
    let form :=
      if factorsCombineIntoPolynomial
      then ProductForm.carriedOut
      else ProductForm.formalProduct
    return { form := form, value := productValue }
    -- impl-end

prove_correct formExpressionTimesPolynomial by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

Bundle has NO axioms (G-AX skip in meta.json; refinement.md legs are R(row1)/I(row2)/R(row3), zero A-legs, zero kind-3). Attack surface therefore reduces to model<->patch correspondence and spec weakness; R/I legs pre-cleared by G-CONF (pass).

Spec pins out.form fully in BOTH branches (ensures out.form = if factorsCombineIntoPolynomial then carriedOut else formalProduct) and out.value ONLY in the carried-out branch (ensures factorsCombineIntoPolynomial = true -> out.value = productValue). The only impl freedom is out.value in the formal branch (factorsCombineIntoPolynomial = false). This is genuinely unobservable: per mapping.md 2/3 the formal product is an sympy.Mul (g*f.as_expr()) which has NO coefficient list, so out.value has no repo referent when the product is left formal.

Same-spec confirmed True for all 9 files (markers.same_spec, velvet). Verification (bash scripts/lean_verify.sh <f>):
- pos_control.lean (gold impl): exit 0 = VERIFIES (positive control OK).
- atk_1.lean = prepatch bug (always formalProduct): exit 1 = correctly REJECTED. Impl matches Solution_prepatch.lean modulo comments (prepatch_reproduced=true).
- atk_2.lean (swapped form): exit 1 = correctly REJECTED.
- atk_3.lean (always carriedOut): exit 1 = correctly REJECTED.
- atk_4.lean (formal-branch value := []): exit 0 = VERIFIES.
- atk_5.lean (formal-branch value := [999], boundary garbage): exit 0 = VERIFIES.
- atk_6.lean (formal-branch value := productValue.reverse): exit 0 = VERIFIES.
- atk_7.lean (match control-flow, formal-branch value := 0 :: productValue): exit 0 = VERIFIES.
- atk_8.lean (ungrounded-oracle echo, gold impl verbatim minus comments): exit 0 = VERIFIES.

Every verifying attack (atk_4..atk_8) differs from gold ONLY in the unobservable formal-branch out.value; observable behaviour (form in both branches + value when carried out) is identical to gold. Hence each attack's FAITHFUL refined patch is byte-identical to the gold patch (Poly._op_priority = 10.001) -- the divergence is in unmodeled/unobservable output, so no patch refinement can carry it into repo behaviour. That single faithful patch was RUN through the official harness (not speculated):
  python -c 'from swebench_unified.harness import run_resolve; run_resolve("sympy__sympy-13757", <faithful_patch>, run_id="sbu-resolve-audit-eq-q954d13c-faithful", timeout=1200, retries=1)'
  => completed=True, resolved=True, attempts=1, flaky=False, note='resolved'.
faithful_patch.diff sha1=d6581fed896f33dbd079dac0c393cdfa9019600e 

Since the faithful refined patch of every verifying wrong impl RESOLVES, verify=>correct holds; no attack breaks the spec. refinement.md audit: rows tagged R/I/R only, no kind-3, no A-legs to check; model<->patch correspondence (cast success <-> carriedOut; try/except <-> if/else; g.mul(f) value <-> productValue free input) is faithful and matches mapping.md. Verdict SOUND (>=5 verifying attacks materialized + resolve-run, none breaks it). NOTE: the spec's out.value freedom in the formal branch is a correct modeling choice (unobservable), not a weakness -- an attack exploiting it produces the gold patch, which resolves.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for velvet sympy__sympy-13757.

SPEC INTEGRITY: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, VelvetBackend.language) => True. Spec regions (axioms/pure/pre/post + method signature + ensures) are byte-identical between patched and prepatch; only the impl region differs (prepatch always returns formalProduct, patched branches on the flag). The prepatch impl correctly fails prove_correct on the carriedOut branch (bug skeleton), confirming the spec is non-trivial.

### Verified proposition
  ensures out.form = (if factorsCombineIntoPolynomial then carriedOut else formalProduct)
  ensures factorsCombineIntoPolynomial = true -> out.value = productValue
The value postcondition is weak: it holds for ANY free productValue input, so it cannot be 'too strong'. The load-bearing claim is the form<->boolean equivalence.

BINDING TESTED AGAINST REAL REPO (worktree @ base_commit a5e6a101, gold patch _op_priority=10.001 applied; sympy 1.1.2.dev under py3.8). Modeled boolean = 'Poly(left_operand, *poly.gens) casts without PolynomialError'; modeled form observable = (e*Poly(x,x)).is_Poly. This mirrors Poly.__rmul__ (polytools.py:4052) try: g=f.__class__(g,*f.gens) -> g.mul(f) (carriedOut) except PolynomialError -> g*f.as_expr() (formalProduct).
  - Hand cases: 2, 3/2, x, x**2, 2x+1, y, x*y, pi, I, sqrt(2), floats, oo, E, sqrt(2)*x -> cast True & is_Poly True (carriedOut). sin(x), exp(x), log(x), tan(x), gamma(x), Abs(x), sqrt(x), 1/x, sin(x)+2, x+sin(x) -> cast False & is_Poly False (formalProduct). All agree.
  - Seeded fuzz (seed 13757) of 4000 random +/* combinations over convertible+transcendental atoms: cast-succeeds vs is_Poly => 0 mismatches. Both branches genuinely exercised.

RESULT: the modeled function agrees with the real callee on every input tried across both branches. No diverging input found. Spec is not stronger than the repo behavior.

MINOR (non-defect) note: mapping.md prose says 'formalProduct <-> sympy.Mul', but e.g. (1/x)*Poly(x,x) returns Integer 1 (not a Mul). The VERIFIED observable is is_Poj=False, under which such cases still classify correctly as formalProduct, so this is a documentation imprecision only and yields no diverging input for the verified spec.

Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (verified via swebench_unified.markers.spec_view / leakage.screen on velvet Solution.lean) is lexically clean: no diff markers, no patched file path (sympy/polys/polytools.py), no patched module dotted-path, no reproduction of the gold changed line ('_op_priority = 10.001'), and the only distinctive patched symbol 'Poly' is pervasively public in the problem_statement. Beyond the lexical screen, no semantic leak: the gold edit is the single class-attribute addition Poly._op_priority = 10.001, whose fix MECHANISM (operator-priority dispatch to Poly.__rmul__) is nowhere disclosed — the spec never mentions _op_priority, __rmul__, precedence, or dispatch. Every comment/doc restates only the OBSERVABLE behavior already public in the problem_statement (x*Poly(x) with expr on the left should evaluate to a single value the same way Poly(x)*x already does; formal otherwise). The modeled input factorsCombineIntoPolynomial captures the UNCHANGED convertibility machinery, not the gold edit — a solver could not reconstruct '_op_priority = 10.001' from the spec view. The spec is a faithful behavioral model of the public F2P symptom, not a gold-reconstruction. Mechanical screen: PASSED (0 hard failures). meta not relaxed for G-LEAK; no RELAXED_LEAKAGE.md deferral needed.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
