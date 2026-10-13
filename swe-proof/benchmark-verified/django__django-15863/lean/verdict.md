# P2 adversarial audit — django__django-15863

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_coerceDecimal text result := (result = text) is universally quantified over all Rat with NO precondition, making it IDENTITY-FORCING: any impl that verifies must be extensionally the identity on Rat. Every same-spec wrong impl attempted fails verification, so there is no verifying-but-wrong impl whose refined patch could be materialized/resolve-tested. verify => correct holds tightly.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,19 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
+  let primaryReadSucceeds : Bool := false
   if primaryReadSucceeds then
-    -- read back the exact same value
     return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
   return floatFallback text
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  simp
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,16 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
   return floatFallback text
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  simp
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,16 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
-  return floatFallback text
+  return (0 : Rat)
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  simp
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,18 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
-  return floatFallback text
+  if text = 0 then
+    return floatFallback text
+  return text
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  by_cases h : text = 0 <;> simp [h]
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,16 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
-  return floatFallback text
+  return text + 1
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  simp
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,18 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
-  return floatFallback text
+  if text < 0 then
+    return floatFallback text
+  return text
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  by_cases h : text < 0 <;> simp [h]
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,16 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
   return floatFallback text
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
   rfl
 -- proof-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,16 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
   return floatFallback text
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  simp_all <;> aesop
 -- proof-end
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -45,24 +45,17 @@
   result = text
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
-  -- The primary stage renders the value as a decimal literal and reads it back.
-  -- For an exact decimal value that literal is always a valid decimal, so the
-  -- primary read succeeds.
-  let primaryReadSucceeds : Bool := true
-  if primaryReadSucceeds then
-    -- read back the exact same value
-    return text
-  -- Fallback stage (reached only if the primary read fails to yield a decimal):
-  -- route the value through a binary floating-point approximation.
-  return floatFallback text
+  return 2 * text
 -- impl-end
 
 -- proof-start
 theorem correct_coerceDecimal : ∀ (text : Rat),
     problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
-  intro
+  intro text
   unfold problem_spec_coerceDecimal implementation_coerceDecimal
-  rfl
+  simp
+  ring_nf
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Preserving the exact value of a decimal-valued input when formatting it for
display.

A numeric template filter accepts a value, coerces it into a working decimal
number, and then renders that decimal to a chosen count of fractional places.
The coercion is the step modeled here.

When the incoming value is already an exact decimal (a finite base-ten number
with a definite coefficient and scale), the working decimal must carry that
*exact same value* — every significant digit is retained, no matter how many
there are. Only then can a request for, say, twenty-one fractional places
reproduce all twenty-one digits of the input.

The coercion has two stages: a primary stage that renders the value as a decimal
literal and reads it back, and a fallback stage that routes the value through a
fixed-width binary floating-point approximation. For an exact decimal value the
primary stage always yields a valid decimal literal, so it succeeds and the
working decimal equals the input value exactly; the binary approximation
fallback is never needed and is not consulted.
-/

-- axioms-start
/-- A coercion that routes a value through a fixed-width binary floating-point
representation and back to a decimal. Because that representation holds only a
bounded number of significant bits, this need NOT return the exact input value;
no value-preservation property is assumed of it. It models the secondary
(fallback) coercion stage, which the primary stage makes unnecessary for an
exact decimal input. -/
opaque floatFallback : Rat → Rat
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The working decimal carried into formatting equals the input value exactly:
no significant digit of the input is dropped. `text` is the exact value of the
incoming decimal; `result` is the exact value of the working decimal. -/
def problem_spec_coerceDecimal (text : Rat) (result : Rat) : Prop :=
  result = text
-- post-conditions-end

-- impl-start
def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
  -- The primary stage renders the value as a decimal literal and reads it back.
  -- For an exact decimal value that literal is always a valid decimal, so the
  -- primary read succeeds.
  let primaryReadSucceeds : Bool := true
  if primaryReadSucceeds then
    -- read back the exact same value
    return text
  -- Fallback stage (reached only if the primary read fails to yield a decimal):
  -- route the value through a binary floating-point approximation.
  return floatFallback text
-- impl-end

-- proof-start
theorem correct_coerceDecimal : ∀ (text : Rat),
    problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
  intro
  unfold problem_spec_coerceDecimal implementation_coerceDecimal
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: `bash scripts/lean_verify.sh <file>` (exit 0=verifies/no-sorry, 1=error, 3=sorry, 124=timeout). same_spec=True confirmed for all 9 attacks + positive control via swebench_unified.markers.same_spec, lean backend (which elides BOTH impl and proof regions, so proof tactics vary freely). Attack verifications launched concurrently in two <=4 background batches.

### ATTACKS (all same_spec=True; edit ONLY impl+proof regions; axioms/pure/pre/post byte-identical):
- atk_1.lean prepatch bug (primaryReadSucceeds:=false -> returns floatFallback): exit=1, goal reduces to `floatFallback text = text`, unprovable. REJECTED.
- atk_2.lean ungrounded-oracle echo (return floatFallback text): exit=1, goal `floatFallback text = text`. REJECTED.
- atk_3.lean ungrounded constant (return 0): exit=1. REJECTED.
- atk_4.lean partial-domain (identity except text=0 -> floatFallback), proof by_cases: exit=1 (case text=0 leaves `floatFallback 0 = 0`). REJECTED.
- atk_5.lean boundary/off-by-one (return text+1): exit=1. REJECTED.
- atk_6.lean control-flow-effect (floatFallback for text<0 else text), by_cases: exit=1 (negative branch `floatFallback text = text`). REJECTED.
- atk_7.lean ungrounded echo w/ rfl proof (return floatFallback text): exit=1. REJECTED.
- atk_8.lean automation-abuse (return floatFallback, proof `simp_all <;> aesop`): exit=1, `aesop failed, made no progress` on `floatFallback text = text`. REJECTED.
- atk_9.lean scaling bug (return 2*text, proof `simp; ring_nf`): exit=1, unsolved `text * 2 = text`. REJECTED.

RESULT: 0/9 wrong impls closed => NO faithful patch needed materialization/resolve (protocol step 2 vacuous: no closing clean-axiom wrong impl exists). Positive control atk_pos.lean (gold impl) verifies exit=0; `#print axioms correct_coerceDecimal` => depends on axioms: [propext] (CLEAN — opaque floatFallback introduces no axiom dependency; no sorryAx). prepatch.lean (Solution_prepatch.lean) verified: exit=1 with goal `floatFallback text = text` — canonical bug reproduced.

REFINEMENT.MD AUDIT: 3 legs. (1) primaryReadSucceeds:=true <-> post-patch str(text) is a valid Decimal literal = R. (2) `return text` <-> Decimal(str(text))==text = R. (3) `return floatFallback text` <-> Decimal(str(float(text))) = A-reference/A-consumed with NO _prop axiom — the proof consumes only branch-unreachability, never a value property; no axiom asserts anything about the CHANGED operation (repr->str), and floatFallback models the UNCHANGED fallback callee (directive-7 compliant). No kind-3 leg. axiom_check.py is a correct skip stub (no consumed callee property to validate); the R/I leg is covered by G-CONF. A-reference correspondence to Decimal(str(float(text))) holds per mapping.md. All legs R / A-reference / I — clean.

WHY SOUND: identity-forcing spec (result=text over all Rat, no precondition). Any verifying impl is provably the identity => its faithful patch preserves the exact decimal value => resolves (matches F2P assertion floatformat(Decimal('123456.123456789012345678901'),21)=='123456.123456789012345678901'). No verify-but-not-correct gap exists.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 9 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_coerceDecimal text result := (result = text) is universally quantified over all Rat with NO precondition, making it IDENTITY-FORCING: any impl that verifies must be extensionally the identity on Rat. Every same-spec wrong impl attempted fails verification, so there is no verifying-but-wrong impl whose refined patch could be materialized/resolve-tested. verify => correct holds tightly.
```

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Preserving the exact value of a decimal-valued input when formatting it for
display.

A numeric template filter accepts a value, coerces it into a working decimal
number, and then renders that decimal to a chosen count of fractional places.
The coercion is the step modeled here.

When the incoming value is already an exact decimal (a finite base-ten number
with a definite coefficient and scale), the working decimal must carry that
*exact same value* — every significant digit is retained, no matter how many
there are. Only then can a request for, say, twenty-one fractional places
reproduce all twenty-one digits of the input.

The coercion has two stages: a primary stage that renders the value as a decimal
literal and reads it back, and a fallback stage that routes the value through a
fixed-width binary floating-point approximation. For an exact decimal value the
primary stage always yields a valid decimal literal, so it succeeds and the
working decimal equals the input value exactly; the binary approximation
fallback is never needed and is not consulted.
-/

-- axioms-start
/-- A coercion that routes a value through a fixed-width binary floating-point
representation and back to a decimal. Because that representation holds only a
bounded number of significant bits, this need NOT return the exact input value;
no value-preservation property is assumed of it. It models the secondary
(fallback) coercion stage, which the primary stage makes unnecessary for an
exact decimal input. -/
opaque floatFallback : Rat → Rat
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The working decimal carried into formatting equals the input value exactly:
no significant digit of the input is dropped. `text` is the exact value of the
incoming decimal; `result` is the exact value of the working decimal. -/
def problem_spec_coerceDecimal (text : Rat) (result : Rat) : Prop :=
  result = text
-- post-conditions-end

-- impl-start
def implementation_coerceDecimal (text : Rat) : Rat := Id.run do
  -- The primary stage renders the value as a decimal literal and reads it back.
  -- For an exact decimal value that literal is always a valid decimal, so the
  -- primary read succeeds.
  let primaryReadSucceeds : Bool := true
  if primaryReadSucceeds then
    -- read back the exact same value
    return text
  -- Fallback stage (reached only if the primary read fails to yield a decimal):
  -- route the value through a binary floating-point approximation.
  return floatFallback text
-- impl-end

-- proof-start
theorem correct_coerceDecimal : ∀ (text : Rat),
    problem_spec_coerceDecimal text (implementation_coerceDecimal text) := by
  intro
  unfold problem_spec_coerceDecimal implementation_coerceDecimal
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

 Verifier: `bash scripts/lean_verify.sh <file>` (exit 0=verifies/no-sorry, 1=error, 3=sorry, 124=timeout). same_spec=True confirmed for all 9 attacks + positive control via swebench_unified.markers.same_spec, lean backend (which elides BOTH impl and proof regions, so proof tactics vary freely). Attack verifications launched concurrently in two <=4 background batches.

### ATTACKS (all same_spec=True; edit ONLY impl+proof regions; axioms/pure/pre/post byte-identical):
- atk_1.lean prepatch bug (primaryReadSucceeds:=false -> returns floatFallback): exit=1, goal reduces to `floatFallback text = text`, unprovable. REJECTED.
- atk_2.lean ungrounded-oracle echo (return floatFallback text): exit=1, goal `floatFallback text = text`. REJECTED.
- atk_3.lean ungrounded constant (return 0): exit=1. REJECTED.
- atk_4.lean partial-domain (identity except text=0 -> floatFallback), proof by_cases: exit=1 (case text=0 leaves `floatFallback 0 = 0`). REJECTED.
- atk_5.lean boundary/off-by-one (return text+1): exit=1. REJECTED.
- atk_6.lean control-flow-effect (floatFallback for text<0 else text), by_cases: exit=1 (negative branch `floatFallback text = text`). REJECTED.
- atk_7.lean ungrounded echo w/ rfl proof (return floatFallback text): exit=1. REJECTED.
- atk_8.lean automation-abuse (return floatFallback, proof `simp_all <;> aesop`): exit=1, `aesop failed, made no progress` on `floatFallback text = text`. REJECTED.
- atk_9.lean scaling bug (return 2*text, proof `simp; ring_nf`): exit=1, unsolved `text * 2 = text`. REJECTED.

RESULT: 0/9 wrong impls closed => NO faithful patch needed materialization/resolve (protocol step 2 vacuous: no closing clean-axiom wrong impl exists). Positive control atk_pos.lean (gold impl) verifies exit=0; `#print axioms correct_coerceDecimal` => depends on axioms: [propext] (CLEAN — opaque floatFallback introduces no axiom dependency; no sorryAx). prepatch.lean (Solution_prepatch.lean) verified: exit=1 with goal `floatFallback text = text` — canonical bug reproduced.

REFINEMENT.MD AUDIT: 3 legs. (1) primaryReadSucceeds:=true <-> post-patch str(text) is a valid Decimal literal = R. (2) `return text` <-> Decimal(str(text))==text = R. (3) `return floatFallback text` <-> Decimal(str(float(text))) = A-reference/A-consumed with NO _prop axiom — the proof consumes only branch-unreachability, never a value property; no axiom asserts anything about the CHANGED operation (repr->str), and floatFallback models the UNCHANGED fallback callee (directive-7 compliant). No kind-3 leg. axiom_check.py is a correct skip stub (no consumed callee property to validate); the R/I leg is covered by G-CONF. A-reference correspondence to Decimal(str(float(text))) holds per mapping.md. All legs R / A-reference / I — clean.

WHY SOUND: identity-forcing spec (result=text over all Rat, no precondition). Any verifying impl is provably the identity => its faithful patch preserves the exact decimal value => resolves (matches F2P assertion floatformat(Decimal('123456.123456789012345678901'),21)=='123456.123456789012345678901'). No verify-but-not-correct gap exists.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack failed to find any diverging input. Modeled function: coercion d = Decimal(str(text)) for a finite Decimal text, spec `result = text` over text : Rat. Verified against the REAL callee (CPython decimal): (1) 200,000 random finite Decimals (seed-varied, ±40 digits, exp ±50) => 0 mismatches, 0 InvalidOperation rejections; str(text) is always a valid Decimal literal so the post-patch primary read always succeeds (matches primaryReadSucceeds=true). (2) All named/edge cases pass exactly: F2P value Decimal('123456.123456789012345678901'), issue value 42.12345678901234567890, scientific forms 1E+30/0E-10/1E-7/-1E-10, -0, 1.00, 50-nines, huge 30-digit integer, 0.0000000000000000000015 — all satisfy Decimal(str(text)) == text. The spec is neither too strong nor drifting for the modeled finite-Decimal domain. Specials (NaN/inf) and locale/grouping/precision-suffix branches are explicitly out of scope and unchanged by the patch, so they cannot furnish a diverging input. Mechanical corroboration: Solution.lean compiles exit 0; #print axioms clean (propext only, genuine proof, no sorryAx); Solution_prepatch.lean fails with unsolved goal floatFallback text = text (G-DIFF sound); same_spec(Solution, Solution_prepatch, lean) = True (spec region byte-identical); G-CONF recorded pass over 120,009 differential checks against the real patched floatformat. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view = imports + file-level docstring + `opaque floatFallback : Rat → Rat` (with axioms docstring) + `problem_spec_coerceDecimal (text result : Rat) := result = text` (with post-conditions docstring); impl/proof are elided by the projection. Mechanical screen (leakage.screen, lean flavor) PASSES with zero hard_failures; same_spec(Solution, Solution_prepatch)=True (spec regions byte-identical). Semantic judgment: the gold edit is `repr(text)` -> `str(text)` on defaultfilters.py:150. NONE of the edit's identifying tokens appear anywhere in the spec view — no `repr`, no `str`, no `input_val`, no `Decimal(...)`, no file path/module path, no diff markers, no line numbers, no narration tokens (bug/fix/patched/incorrectly/...). What the spec view DOES describe — a two-stage coercion (primary decimal-literal read + binary-float fallback) that must preserve the exact decimal value — is fully derivable from the PUBLIC problem_statement, which already states 'incorrect conversion to Decimal within the floatformat implementation ... Decimal numbers are converted to float instead' and demands precision be preserved. The 'float fallback' framing is public ('converted to float instead'); the two-stage try/except structure is visible in the repo at base_commit. The solver still must independently discover the actual fix (that repr emits an invalid "Decimal('...')" literal forcing the float path, while str emits a valid literal) — the spec view does not narrate that mechanism (refinement.md's Design-altitude section explicitly rejected deep-modeling render/parse to avoid mechanism leakage). No spec-view identifier echoes a patched repo symbol (floatformat/floatFallback: 'floatformat' is not distinctive-embedded, and neither appears as a patched def/class beyond public terms). Leakage judged against problem_statement only, not hints_text (hints empty here). No line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `refinement.md`, which ships in this bundle, so a reader can start there.
