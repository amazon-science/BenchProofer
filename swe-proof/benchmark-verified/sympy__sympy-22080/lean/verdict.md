# P2 adversarial audit — sympy__sympy-22080

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,17 +91,13 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
-special case first, otherwise the general case), then return the assembled text
-with the three-way denominator tail over the already-rendered denominator texts.
-Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
-return). -/
+/-- WRONG: compares the lone-negated factor against 56 instead of 55. -/
 def implementation_renderProduct
     (sign : String) (prec : Rat) (num : List Factor)
     (den : List String) : String := Id.run do
   let mut numStr : List String := []
   if num.length = 1 ∧ sign = "-" then
-    numStr := num.map (parenFactor negSingleLevel)
+    numStr := num.map (parenFactor 56)
   else
     numStr := num.map (parenFactor prec)
   let body := String.intercalate "*" numStr
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,19 +91,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
-special case first, otherwise the general case), then return the assembled text
-with the three-way denominator tail over the already-rendered denominator texts.
-Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
-return). -/
+/-- WRONG (prepatch): no lone-negated special case; always compare against prec. -/
 def implementation_renderProduct
     (sign : String) (prec : Rat) (num : List Factor)
     (den : List String) : String := Id.run do
   let mut numStr : List String := []
-  if num.length = 1 ∧ sign = "-" then
-    numStr := num.map (parenFactor negSingleLevel)
-  else
-    numStr := num.map (parenFactor prec)
+  numStr := num.map (parenFactor prec)
   let body := String.intercalate "*" numStr
   if den.isEmpty then
     return sign ++ body
@@ -119,7 +112,7 @@
       problem_spec_renderProduct sign prec num den
         (implementation_renderProduct sign prec num den) := by
   intro sign prec num den
-  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
-  simp only [Id.run, numeratorTexts, bind, pure]
-  split <;> split <;> rfl
+  unfold problem_spec_renderProduct implementation_renderProduct renderProduct numeratorTexts
+  simp only [Id.run, bind, pure]
+  split <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,16 +91,12 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
-special case first, otherwise the general case), then return the assembled text
-with the three-way denominator tail over the already-rendered denominator texts.
-Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
-return). -/
+/-- WRONG: uses ∨ instead of ∧ in the lone-negated guard. -/
 def implementation_renderProduct
     (sign : String) (prec : Rat) (num : List Factor)
     (den : List String) : String := Id.run do
   let mut numStr : List String := []
-  if num.length = 1 ∧ sign = "-" then
+  if num.length = 1 ∨ sign = "-" then
     numStr := num.map (parenFactor negSingleLevel)
   else
     numStr := num.map (parenFactor prec)
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,19 +91,15 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
-special case first, otherwise the general case), then return the assembled text
-with the three-way denominator tail over the already-rendered denominator texts.
-Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
-return). -/
+/-- WRONG: uses strict < instead of ≤ when comparing numerator strengths. -/
 def implementation_renderProduct
     (sign : String) (prec : Rat) (num : List Factor)
     (den : List String) : String := Id.run do
   let mut numStr : List String := []
   if num.length = 1 ∧ sign = "-" then
-    numStr := num.map (parenFactor negSingleLevel)
+    numStr := num.map (fun f => if f.strength < negSingleLevel then "(" ++ f.text ++ ")" else f.text)
   else
-    numStr := num.map (parenFactor prec)
+    numStr := num.map (fun f => if f.strength < prec then "(" ++ f.text ++ ")" else f.text)
   let body := String.intercalate "*" numStr
   if den.isEmpty then
     return sign ++ body
@@ -119,7 +115,7 @@
       problem_spec_renderProduct sign prec num den
         (implementation_renderProduct sign prec num den) := by
   intro sign prec num den
-  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
+  unfold problem_spec_renderProduct implementation_renderProduct renderProduct parenFactor
   simp only [Id.run, numeratorTexts, bind, pure]
   split <;> split <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,11 +91,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
-special case first, otherwise the general case), then return the assembled text
-with the three-way denominator tail over the already-rendered denominator texts.
-Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
-return). -/
+/-- WRONG: denominator tail always parenthesizes the group even for a single entry. -/
 def implementation_renderProduct
     (sign : String) (prec : Rat) (num : List Factor)
     (den : List String) : String := Id.run do
@@ -107,8 +103,6 @@
   let body := String.intercalate "*" numStr
   if den.isEmpty then
     return sign ++ body
-  else if den.length = 1 then
-    return sign ++ body ++ "/" ++ den.headI
   else
     return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,11 +91,7 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
-special case first, otherwise the general case), then return the assembled text
-with the three-way denominator tail over the already-rendered denominator texts.
-Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
-return). -/
+/-- WRONG: joins numerator factors with "/" instead of "*". -/
 def implementation_renderProduct
     (sign : String) (prec : Rat) (num : List Factor)
     (den : List String) : String := Id.run do
@@ -104,7 +100,7 @@
     numStr := num.map (parenFactor negSingleLevel)
   else
     numStr := num.map (parenFactor prec)
-  let body := String.intercalate "*" numStr
+  let body := String.intercalate "/" numStr
   if den.isEmpty then
     return sign ++ body
   else if den.length = 1 then
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -91,17 +91,15 @@
 -- post-conditions-end
 
 -- impl-start
-/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
-special case first, otherwise the general case), then return the assembled text
-with the three-way denominator tail over the already-rendered denominator texts.
-Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
-return). -/
+/-- ECHO: partial-domain wrong — special-cases sign="-" & num.length=1 to use prec (i.e. drops fix) ONLY when den nonempty; correct when den empty. -/
 def implementation_renderProduct
     (sign : String) (prec : Rat) (num : List Factor)
     (den : List String) : String := Id.run do
   let mut numStr : List String := []
-  if num.length = 1 ∧ sign = "-" then
+  if num.length = 1 ∧ sign = "-" ∧ den.isEmpty then
     numStr := num.map (parenFactor negSingleLevel)
+  else if num.length = 1 ∧ sign = "-" then
+    numStr := num.map (parenFactor prec)
   else
     numStr := num.map (parenFactor prec)
   let body := String.intercalate "*" numStr
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a product expression to source-code text.

A product is presented as an optional leading sign together with the list of
numerator factors and the list of denominator texts. Each numerator factor
arrives already rendered to text and carries its own *binding strength* (a
numeric weight describing how tightly the factor's textual form binds); the
renderer wraps a numerator factor in parentheses exactly when its binding
strength does not exceed the strength level it is compared against, then joins
the numerator factors with `*`. Each denominator entry arrives as a fully
rendered text (any parenthesization it needs — including group-wrapping applied
by upstream denominator post-processing — is already part of the text); if the
denominator is present it is appended after a `/`, with the whole denominator
group parenthesized when it has more than one entry.

A single numerator factor under a leading minus (`sign = "-"`) is a special
case: it is compared against a dedicated constant strength level rather than the
product's own binding strength. In every other case each numerator factor is
compared against the product's own binding strength.

The behavior is stated abstractly as an input→output relation on the rendered
factors and their strengths; the implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The rendered
-- text of each numerator factor and its numeric binding strength, and the fully
-- rendered text of each denominator entry, are produced upstream (by a generic
-- recursive renderer, a generic strength lookup, and the unchanged denominator
-- post-processing) and are supplied to this routine as plain inputs; this
-- routine only decides numerator parenthesization and assembles the pieces, so
-- there is no `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- A single numerator factor: its already-rendered text together with its numeric
binding strength (how tightly its textual form binds). -/
structure Factor where
  strength : Rat
  text : String

/-- The dedicated constant strength level a single numerator factor under a leading minus is
compared against. Observable boundary: a lone negated factor of strength `55` is
wrapped, one of strength `55.5` is not (factor strengths occur in half-unit
steps). -/
def negSingleLevel : Rat := 55

/-- Parenthesize a factor's rendered text when its binding strength does not
exceed the comparison `level`; otherwise emit the text unchanged. -/
def parenFactor (level : Rat) (f : Factor) : String :=
  if f.strength ≤ level then "(" ++ f.text ++ ")" else f.text

/-- The rendered numerator-factor texts. A single numerator factor under a leading
minus (`sign = "-"`) is compared against the dedicated constant level; every other
numerator factor is compared against the product's own binding strength `prec`. -/
def numeratorTexts (sign : String) (prec : Rat) (num : List Factor) : List String :=
  if num.length = 1 ∧ sign = "-" then
    num.map (parenFactor negSingleLevel)
  else
    num.map (parenFactor prec)

/-- The fully assembled product text: sign, then the `*`-joined numerator texts,
then the denominator (after `/`, the denominator group parenthesized when it has
more than one entry). The denominator entries are already fully rendered texts. -/
def renderProduct (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String :=
  let numStr := numeratorTexts sign prec num
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    sign ++ body
  else if den.length = 1 then
    sign ++ body ++ "/" ++ den.headI
  else
    sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
-- pure-end

-- post-conditions-start
/-- The rendered product text is fully determined by the sign, the product's own
binding strength, the numerator factors (each with its rendered text and binding
strength), and the fully rendered denominator texts. Every fragment of the output
is pinned to the inputs: the parenthesization of each numerator factor, the
`*`-joined numerator, and the denominator tail. -/
def problem_spec_renderProduct
    (sign : String) (prec : Rat) (num : List Factor) (den : List String)
    (result : String) : Prop :=
  result = renderProduct sign prec num den
-- post-conditions-end

-- impl-start
/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
special case first, otherwise the general case), then return the assembled text
with the three-way denominator tail over the already-rendered denominator texts.
Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
return). -/
def implementation_renderProduct
    (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String := Id.run do
  let mut numStr : List String := []
  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    return sign ++ body
  else if den.length = 1 then
    return sign ++ body ++ "/" ++ den.headI
  else
    return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
-- impl-end

-- proof-start
theorem correct_renderProduct :
    ∀ (sign : String) (prec : Rat) (num : List Factor) (den : List String),
      problem_spec_renderProduct sign prec num den
        (implementation_renderProduct sign prec num den) := by
  intro sign prec num den
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [Id.run, numeratorTexts, bind, pure]
  split <;> split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: full functional equality. problem_spec_renderProduct sign prec num den result := result = renderProduct sign prec num den. The oracle `renderProduct` lives in the PROTECTED pure region; same_spec elides only impl+proof, so it is byte-identical across all attacks (confirmed same_spec=True for all 7 attacks + pos_control via swebench_unified.markers.same_spec, lean backend). Any verifying impl must be provably pointwise-equal to a TOTAL, DETERMINISTIC oracle => verify implies correct by construction; there is no room for a wrong-but-verifying impl.

A-LEGS (the focus of this pass): VACUOUS. meta.json axioms=[] and deep_model_references=[]; conf_skip=false. axiom_check.py is a skip stub (mapping.md: no opaque/axiom callee). refinement.md's 8 table legs are all R (5: sign/prec/num/den inputs) or I (3: parenFactor model, `*`-join, three-way denominator tail); the only '**A-consumed**'/'**A-reference**' strings in refinement.md are in the tag-legend line, not on any actual leg. No kind-3 ungrounded-oracle leg. The denominator is correctly R-abstracted as fully-rendered-text input (den:List String) capturing the unchanged b_str rendering + pow_paren #14160 wrapping loop upstream of the modeling boundary; the precedence.py `"Mod": Mul` edit is correctly carried as an input strength VALUE (70->50), not a changed op. The changed op is leg 6 (negSingleLevel=55=0.5*(60+50), guard num.length=1 ∧ sign="-"). Correspondence to real callees holds.

### ATTACKS (all same_spec=True; verified concurrently in batches of 4 via scripts/lean_verify.sh <f>):
- atk_1 boundary/off-by-one: negSingleLevel comparison uses 56 not 55. EXIT=1 (rfl failed at proof, genuine mismatch).
- atk_2 PREPATCH BUG: drops lone-negated special case, always compares against prec (byte-equal to Solution_prepatch.lean impl). EXIT=1 (rfl failed) => bug is caught by the spec; prepatch_reproduced=true.
- atk_3 control-flow: guard uses ∨ instead of ∧. EXIT=1 (rfl failed).
- atk_4 boundary: strict < instead of ≤ in numerator parenthesize. EXIT=1 (unfold/rfl failed).
- atk_5 denominator branch defect: always parenthesizes denom group even for single entry (drops len=1 branch). EXIT=1 (rfl failed).
- atk_6 control-flow-effect: joins numerator with "/" instead of "*". EXIT=1 (rfl failed).
- atk_7 partial-domain: applies fix only when den empty, uses prec otherwise. EXIT=1 (rfl failed).
POSITIVE CONTROL pos_control.lean (byte-identical gold): EXIT=0 verifies. #print axioms correct_renderProduct => depends on axioms: [propext] (clean, no sorry/sorryAx/Classical-of-choice concern; propext is standard).

RESOLVE RUNS: none required. Protocol step 2 mandates a resolve run only for wrong impls whose proof CLOSES with clean axioms. Zero wrong impls closed (all 7 exit 1 with genuine proof errors), so there is no verifying-wrong-impl faithful patch to materialize. verify implies correct is upheld.

COMMANDS: same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open(SOL).read(),open(ATK).read(),b.language))" => True for all. verify: bash scripts/lean_verify.sh atk_N.lean => exit codes above. Concurrency: launched as background jobs, ≤4 at a time (2 batches).

VERDICT: SOUND. Full-functional-equality spec admits no wrong-but-verifying impl; A-legs vacuous and refinement faithful; ≥5 (7) distinct same-spec attacks all fail to verify while the gold positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a product expression to source-code text.

A product is presented as an optional leading sign together with the list of
numerator factors and the list of denominator texts. Each numerator factor
arrives already rendered to text and carries its own *binding strength* (a
numeric weight describing how tightly the factor's textual form binds); the
renderer wraps a numerator factor in parentheses exactly when its binding
strength does not exceed the strength level it is compared against, then joins
the numerator factors with `*`. Each denominator entry arrives as a fully
rendered text (any parenthesization it needs — including group-wrapping applied
by upstream denominator post-processing — is already part of the text); if the
denominator is present it is appended after a `/`, with the whole denominator
group parenthesized when it has more than one entry.

A single numerator factor under a leading minus (`sign = "-"`) is a special
case: it is compared against a dedicated constant strength level rather than the
product's own binding strength. In every other case each numerator factor is
compared against the product's own binding strength.

The behavior is stated abstractly as an input→output relation on the rendered
factors and their strengths; the implementation and correctness proof are supplied
separately.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The rendered
-- text of each numerator factor and its numeric binding strength, and the fully
-- rendered text of each denominator entry, are produced upstream (by a generic
-- recursive renderer, a generic strength lookup, and the unchanged denominator
-- post-processing) and are supplied to this routine as plain inputs; this
-- routine only decides numerator parenthesization and assembles the pieces, so
-- there is no `opaque`/`axiom` callee contract to declare.
-- axioms-end

-- pure-start
/-- A single numerator factor: its already-rendered text together with its numeric
binding strength (how tightly its textual form binds). -/
structure Factor where
  strength : Rat
  text : String

/-- The dedicated constant strength level a single numerator factor under a leading minus is
compared against. Observable boundary: a lone negated factor of strength `55` is
wrapped, one of strength `55.5` is not (factor strengths occur in half-unit
steps). -/
def negSingleLevel : Rat := 55

/-- Parenthesize a factor's rendered text when its binding strength does not
exceed the comparison `level`; otherwise emit the text unchanged. -/
def parenFactor (level : Rat) (f : Factor) : String :=
  if f.strength ≤ level then "(" ++ f.text ++ ")" else f.text

/-- The rendered numerator-factor texts. A single numerator factor under a leading
minus (`sign = "-"`) is compared against the dedicated constant level; every other
numerator factor is compared against the product's own binding strength `prec`. -/
def numeratorTexts (sign : String) (prec : Rat) (num : List Factor) : List String :=
  if num.length = 1 ∧ sign = "-" then
    num.map (parenFactor negSingleLevel)
  else
    num.map (parenFactor prec)

/-- The fully assembled product text: sign, then the `*`-joined numerator texts,
then the denominator (after `/`, the denominator group parenthesized when it has
more than one entry). The denominator entries are already fully rendered texts. -/
def renderProduct (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String :=
  let numStr := numeratorTexts sign prec num
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    sign ++ body
  else if den.length = 1 then
    sign ++ body ++ "/" ++ den.headI
  else
    sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
-- pure-end

-- post-conditions-start
/-- The rendered product text is fully determined by the sign, the product's own
binding strength, the numerator factors (each with its rendered text and binding
strength), and the fully rendered denominator texts. Every fragment of the output
is pinned to the inputs: the parenthesization of each numerator factor, the
`*`-joined numerator, and the denominator tail. -/
def problem_spec_renderProduct
    (sign : String) (prec : Rat) (num : List Factor) (den : List String)
    (result : String) : Prop :=
  result = renderProduct sign prec num den
-- post-conditions-end

-- impl-start
/-- Imperative skeleton: compute the numerator-factor texts (the lone-negated
special case first, otherwise the general case), then return the assembled text
with the three-way denominator tail over the already-rendered denominator texts.
Mirrors the source control flow (build `a_str`; the `not b` / `len(b)==1` / else
return). -/
def implementation_renderProduct
    (sign : String) (prec : Rat) (num : List Factor)
    (den : List String) : String := Id.run do
  let mut numStr : List String := []
  if num.length = 1 ∧ sign = "-" then
    numStr := num.map (parenFactor negSingleLevel)
  else
    numStr := num.map (parenFactor prec)
  let body := String.intercalate "*" numStr
  if den.isEmpty then
    return sign ++ body
  else if den.length = 1 then
    return sign ++ body ++ "/" ++ den.headI
  else
    return sign ++ body ++ "/(" ++ String.intercalate "*" den ++ ")"
-- impl-end

-- proof-start
theorem correct_renderProduct :
    ∀ (sign : String) (prec : Rat) (num : List Factor) (den : List String),
      problem_spec_renderProduct sign prec num den
        (implementation_renderProduct sign prec num den) := by
  intro sign prec num den
  unfold problem_spec_renderProduct implementation_renderProduct renderProduct
  simp only [Id.run, numeratorTexts, bind, pure]
  split <;> split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: full functional equality. problem_spec_renderProduct sign prec num den result := result = renderProduct sign prec num den. The oracle `renderProduct` lives in the PROTECTED pure region; same_spec elides only impl+proof, so it is byte-identical across all attacks (confirmed same_spec=True for all 7 attacks + pos_control via swebench_unified.markers.same_spec, lean backend). Any verifying impl must be provably pointwise-equal to a TOTAL, DETERMINISTIC oracle => verify implies correct by construction; there is no room for a wrong-but-verifying impl.

A-LEGS (the focus of this pass): VACUOUS. meta.json axioms=[] and deep_model_references=[]; conf_skip=false. axiom_check.py is a skip stub (mapping.md: no opaque/axiom callee). refinement.md's 8 table legs are all R (5: sign/prec/num/den inputs) or I (3: parenFactor model, `*`-join, three-way denominator tail); the only '**A-consumed**'/'**A-reference**' strings in refinement.md are in the tag-legend line, not on any actual leg. No kind-3 ungrounded-oracle leg. The denominator is correctly R-abstracted as fully-rendered-text input (den:List String) capturing the unchanged b_str rendering + pow_paren #14160 wrapping loop upstream of the modeling boundary; the precedence.py `"Mod": Mul` edit is correctly carried as an input strength VALUE (70->50), not a changed op. The changed op is leg 6 (negSingleLevel=55=0.5*(60+50), guard num.length=1 ∧ sign="-"). Correspondence to real callees holds.

### ATTACKS (all same_spec=True; verified concurrently in batches of 4 via scripts/lean_verify.sh <f>):
- atk_1 boundary/off-by-one: negSingleLevel comparison uses 56 not 55. EXIT=1 (rfl failed at proof, genuine mismatch).
- atk_2 PREPATCH BUG: drops lone-negated special case, always compares against prec (byte-equal to Solution_prepatch.lean impl). EXIT=1 (rfl failed) => bug is caught by the spec; prepatch_reproduced=true.
- atk_3 control-flow: guard uses ∨ instead of ∧. EXIT=1 (rfl failed).
- atk_4 boundary: strict < instead of ≤ in numerator parenthesize. EXIT=1 (unfold/rfl failed).
- atk_5 denominator branch defect: always parenthesizes denom group even for single entry (drops len=1 branch). EXIT=1 (rfl failed).
- atk_6 control-flow-effect: joins numerator with "/" instead of "*". EXIT=1 (rfl failed).
- atk_7 partial-domain: applies fix only when den empty, uses prec otherwise. EXIT=1 (rfl failed).
POSITIVE CONTROL pos_control.lean (byte-identical gold): EXIT=0 verifies. #print axioms correct_renderProduct => depends on axioms: [propext] (clean, no sorry/sorryAx/Classical-of-choice concern; propext is standard).

RESOLVE RUNS: none required. Protocol step 2 mandates a resolve run only for wrong impls whose proof CLOSES with clean axioms. Zero wrong impls closed (all 7 exit 1 with genuine proof errors), so there is no verifying-wrong-impl faithful patch to materialize. verify implies correct is upheld.

COMMANDS: same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('lean'); print(same_spec(open(SOL).read(),open(ATK).read(),b.language))" => True for all. verify: bash scripts/lean_verify.sh atk_N.lean => exit codes above. Concurrency: launched as background jobs, ≤4 at a time (2 batches).

VERDICT: SOUND. Full-functional-equality spec admits no wrong-but-verifying impl; A-legs vacuous and refinement faithful; ≥5 (7) distinct same-spec attacks all fail to verify while the gold positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack: no divergence found. (1) Spec region byte-identical: swebench_unified.markers.same_spec(Solution.lean, Solution_prepatch.lean, lean-backend) == True. (2) Solution.lean compiles via scripts/lean_verify.sh (exit 0); `#print axioms correct_renderProduct` => only [propext], no sorryAx — proof is genuine. Real-repo differential test: instrumented the ACTUAL patched _print_Mul (base b506169 patched; verified 0.5*(PRECEDENCE['Pow']+PRECEDENCE['Mul'])=55 and 'Mod':Mul present) to capture the true R-abstracted inputs (sign, prec=precedence(expr), per-factor (precedence(item), _print(item)), and post-pow_paren b_str denominator texts) for every _print_Mul call, then compared the real output against the Lean model fed those inputs. 6548 real invocations across ccode+pycode over the issue expressions + 3000 random expressions => 0 mismatches. (4) Non-vacuous: parenFactor models parenthesize (wrap iff strength<=level) faithfully; denominator modeled as fully-rendered text input correctly captures pow_paren wrapping (e.g. -2*x/(y*y) => den=['(y*y)']); negSingleLevel=55 correct. Spec discriminates the bug — prepatch impl (unconditional parenFactor prec) fails on sign='-', num=[(50,'x % y')], prec=40 (spec: -(x % y); prepatch: -x % y). The modeled function agrees with the real callee on all tested inputs; the R-abstraction boundary (unchanged recursive renderer, precedence lookup, and denominator pipeline as inputs) is legitimate and does not over- or under-constrain the fixed numerator-parenthesization decision.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (leakage.screen over the lean spec_view) PASSES with zero hard failures; same_spec(Solution, Solution_prepatch) is byte-identical; no relaxed_leakage flag / RELAXED_LEAKAGE.md. Substantive gold-reconstruction review confirms clean: (1) no diff markers, no verbatim gold-patch lines, no patched file/module paths (codeprinter.py, precedence.py); (2) no spec-view identifier or comment echoes a patched repo symbol — Factor/negSingleLevel/parenFactor/numeratorTexts/renderProduct are all generic and none embeds _print_Mul, parenthesize, precedence, PRECEDENCE, or Mod; (3) no bug/fix/regression narration — the docstrings frame an abstract input->output rendering relation. The spec pins correct behavior (the lone-negated special comparison level, the constant 55) as a CLEVER spec legitimately must, but the edit-localization signal a solver would need — which files/symbols change, the two-file coupling, the Mod-precedence link, and that this arises from the -Mod(x,y) issue — is entirely absent from the spec view and is not conveyed beyond the public problem_statement. The constant 55 = 0.5*(Pow=60 + Mul=50) is presented only as an abstract 'dedicated constant strength level' with a half-unit observable boundary, never tied to sympy PRECEDENCE. Nothing here leaks beyond problem_statement; hints_text (the '-' vs '%' precedence hint) was correctly excluded from the comparison. Note: this bundle's G-PANEL fail is G-PANEL-1 (spec-too-weak / echo-attack), a modeling concern, NOT a leakage concern; G-PANEL-2 and G-PANEL-3 both recorded pass, consistent with this finding.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
