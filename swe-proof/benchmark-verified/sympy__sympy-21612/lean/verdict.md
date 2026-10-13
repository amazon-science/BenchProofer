# P2 adversarial audit — sympy__sympy-21612

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
     (render : Expr → String) (base : Expr)
     (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
   let baseStr := render base
-  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
+  let needParen := baseComponentCount ≠ 1 ∧ baseIsProduct = true
   if needParen then
     return "(" ++ baseStr ++ ")"
   return baseStr
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,6 +72,8 @@
     (render : Expr → String) (base : Expr)
     (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
   let baseStr := render base
+  if baseComponentCount = 0 then
+    return baseStr
   let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
   if needParen then
     return "(" ++ baseStr ++ ")"
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
     (render : Expr → String) (base : Expr)
     (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
   let baseStr := render base
-  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
+  let needParen := baseComponentCount = 0 ∧ (baseIsProduct = true ∨ baseIsPower = true)
   if needParen then
     return "(" ++ baseStr ++ ")"
   return baseStr
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,10 +72,7 @@
     (render : Expr → String) (base : Expr)
     (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
   let baseStr := render base
-  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
-  if needParen then
-    return "(" ++ baseStr ++ ")"
-  return baseStr
+  return "(" ++ baseStr ++ ")"
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,11 +71,9 @@
     {Expr : Type}
     (render : Expr → String) (base : Expr)
     (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
-  let baseStr := render base
-  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
-  if needParen then
-    return "(" ++ baseStr ++ ")"
-  return baseStr
+  if needsBrackets baseComponentCount baseIsProduct baseIsPower then
+    return "(" ++ render base ++ ")"
+  return render base
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
     (render : Expr → String) (base : Expr)
     (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
   let baseStr := render base
-  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
+  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∧ baseIsPower = true)
   if needParen then
     return "(" ++ baseStr ++ ")"
   return baseStr
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -72,7 +72,7 @@
     (render : Expr → String) (base : Expr)
     (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
   let baseStr := render base
-  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
+  let needParen := baseComponentCount ≠ 0 ∧ (baseIsProduct = true ∨ baseIsPower = true)
   if needParen then
     return "(" ++ baseStr ++ ")"
   return baseStr
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a fractional expression to its textual form, with correct bracketing of
the denominator.

A compound product is rendered as a numerator part divided by a denominator. Each
factor that sits in the denominator is itself an expression, and is first turned
into a text fragment by the surrounding renderer. The question modeled here is
purely a BRACKETING decision for one such denominator factor: when does the
factor's text need an extra pair of surrounding brackets so the division binds the
way the expression actually means?

The rule: a denominator factor must be wrapped in brackets exactly when its base
is itself a COMPOUND expression — concretely, a product or a power — that is built
from more than one component. (A single-component base, an atom, or any other kind
of expression is spliced in without the extra brackets, because the base
renderer's own fragment is already unambiguous in those cases.) Without the extra
brackets a denominator that is itself a fraction or a product collapses into the
surrounding division and changes meaning.

The base renderer itself (turning the factor's base into its text fragment) is
taken as an arbitrary function of the base, so the behavior pinned below is exactly
"the factor's text is the base fragment, wrapped in one pair of brackets precisely
when the base is a multi-component product or power."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The base renderer (turning
-- the factor's base into its text fragment) is modeled as an arbitrary function
-- parameter `render : Expr → String`: the modeled behavior is solely WHETHER an
-- extra pair of brackets is placed around that fragment, so the result is pinned
-- for every possible base renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract. (`render` is recorded in mapping.md as an A-reference solely to
-- document the G-CONF binding to the real base renderer.)
-- axioms-end

-- pure-start
-- The bracketing test: a denominator factor's base needs an extra pair of brackets
-- exactly when it has more than one component AND is a compound product or power.
def needsBrackets (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : Prop :=
  baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)

instance (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) :
    Decidable (needsBrackets baseComponentCount baseIsProduct baseIsPower) := by
  unfold needsBrackets; infer_instance
-- pure-end

-- post-conditions-start
/-- The text of one denominator factor: the base fragment produced by `render`,
wrapped in a single pair of brackets exactly when the base is a multi-component
product or power, and otherwise spliced in unchanged.

Frame discipline: the bracketing decision and the literal bracket characters are
pinned, and the inner fragment is pinned to `render base`, so no part of the
output is left free. -/
def problem_spec_printDenominatorFactor
    {Expr : Type}
    (render : Expr → String) (base : Expr)
    (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool)
    (result : String) : Prop :=
  result =
    (if needsBrackets baseComponentCount baseIsProduct baseIsPower
     then "(" ++ render base ++ ")"
     else render base)
-- post-conditions-end

-- impl-start
def implementation_printDenominatorFactor
    {Expr : Type}
    (render : Expr → String) (base : Expr)
    (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
  let baseStr := render base
  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
  if needParen then
    return "(" ++ baseStr ++ ")"
  return baseStr
-- impl-end

-- proof-start
theorem correct_printDenominatorFactor :
    ∀ {Expr : Type}
      (render : Expr → String) (base : Expr)
      (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool),
      problem_spec_printDenominatorFactor render base baseComponentCount baseIsProduct baseIsPower
        (implementation_printDenominatorFactor render base baseComponentCount baseIsProduct baseIsPower) := by
  intro Expr render base baseComponentCount baseIsProduct baseIsPower
  unfold problem_spec_printDenominatorFactor implementation_printDenominatorFactor needsBrackets
  simp only [Id.run]
  split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinned functional spec — problem_spec pins result = (if needsBrackets baseComponentCount baseIsProduct baseIsPower then "(" ++ render base ++ ")" else render base). No frame freedom; any behaviorally-divergent impl is unprovable.

SAME_SPEC: all 7 attacks + pc = True (impl region edited only; axioms/pure/pre/post byte-identical).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently in 2 batches of 4):
- pc (gold Solution.lean): EXIT 0. #print axioms correct_printDenominatorFactor => 'does not depend on any axioms' (clean).
- atk_1 prepatch bug (needParen := count≠1 ∧ baseIsProduct only; drops baseIsPower disjunct): EXIT 1 (unprovable) — the fixed spec correctly rejects the prepatch impl, so the bug is reproduced/distinguished at the Lean layer.
- atk_2 partial-domain (special-case baseComponentCount=0 -> no wrap, else correct): EXIT 1.
- atk_3 boundary (needParen uses baseComponentCount=0 instead of ≠1): EXIT 1.
- atk_4 control-flow-effect (always wrap in brackets): EXIT 1 (goal pure("("++...++")")=render base in else-branch).
- atk_5 ungrounded-oracle echo (impl := if needsBrackets ... then "("++render base++")" else render base — literally the gold predicate): EXIT 0. #print axioms => 'does not depend on any axioms' (clean).
- atk_6 AND instead of OR (baseIsProduct ∧ baseIsPower): EXIT 1.
- atk_7 count≠0 instead of ≠1: EXIT 1.

MANDATORY RESOLVE ON EVERY CLEAN-AXIOM CLOSING IMPL: only atk_5 closes with clean axioms besides the gold pc. atk_5 is BEHAVIORALLY IDENTICAL to gold (computes exactly needsBrackets), so its faithful refined patch is the gold patch. Materialized atk_5_patch.diff and ran the OFFICIAL harness: swebench_unified.harness.run_resolve('sympy__sympy-21612', gold_patch, timeout=1800). RESULT: RESOLVED=True, note='resolved' (also confirmed via raw run_evaluation: 'Instances resolved: 1', ✓=1). Docker via `docker` (direct socket denied); first run_resolve returned no-report because the instance image was not yet pulled — after the image was pulled the official run_resolve returned RESOLVED=True deterministically. => The single verifying clean-axiom impl HAS a materialized faithful patch that RESOLVES. No verify⇏correct break.

Prepatch resolve note: empty-patch prediction returned no-report (swebench short-circuits empty patches — harness artifact, not a signal). prepatch_reproduced=true is established at the spec layer: atk_1 (the exact prepatch impl) fails to close against the fixed spec (EXIT 1), so the spec distinguishes gold from prepatch.

REFINEMENT.MD AUDIT (A-leg focus per plan §4): 3 legs, all R / A-reference / I, no kind-3 (changed-inexpressible), no A-consumed.
- `let baseStr := render base` -> A-reference: render : Expr→String is universally quantified; documents the G-CONF binding to the real base-fragment renderer self.parenthesize(item.base, prec, strict=False). Correspondence holds — the spec is parametric over EVERY renderer, so no property of self.parenthesize is consumed; axiom_check.py is a legitimate skip stub (no consumed axiom).
- needParen predicate -> R: baseComponentCount≠1 ↔ len(item.args[0].args)!=1; baseIsProduct ↔ isinstance(item.base,Mul); baseIsPower ↔ isinstance(item.base,Pow). Faithful type refinement of the widened isinstance test (Mul -> (Mul,Pow)).
- wrap template -> I: "(%s)" bracket wrap iff item∈pow_paren, else unchanged fragment.
A-reference correspondence to the real callee is sound.

CONCLUSION: verify⇒correct holds. Behaviorally-wrong impls (atk_1,2,3,4,6,7) are all unprovable; the only additional closing impl (atk_5) is a gold-equivalent echo whose faithful patch RESOLVES under the official harness (policy-compliant, not a weakness). ≥5 distinct wrong impls attacked; none breaks the spec. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a fractional expression to its textual form, with correct bracketing of
the denominator.

A compound product is rendered as a numerator part divided by a denominator. Each
factor that sits in the denominator is itself an expression, and is first turned
into a text fragment by the surrounding renderer. The question modeled here is
purely a BRACKETING decision for one such denominator factor: when does the
factor's text need an extra pair of surrounding brackets so the division binds the
way the expression actually means?

The rule: a denominator factor must be wrapped in brackets exactly when its base
is itself a COMPOUND expression — concretely, a product or a power — that is built
from more than one component. (A single-component base, an atom, or any other kind
of expression is spliced in without the extra brackets, because the base
renderer's own fragment is already unambiguous in those cases.) Without the extra
brackets a denominator that is itself a fraction or a product collapses into the
surrounding division and changes meaning.

The base renderer itself (turning the factor's base into its text fragment) is
taken as an arbitrary function of the base, so the behavior pinned below is exactly
"the factor's text is the base fragment, wrapped in one pair of brackets precisely
when the base is a multi-component product or power."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The base renderer (turning
-- the factor's base into its text fragment) is modeled as an arbitrary function
-- parameter `render : Expr → String`: the modeled behavior is solely WHETHER an
-- extra pair of brackets is placed around that fragment, so the result is pinned
-- for every possible base renderer. Hence the spec needs no `opaque`/`axiom`
-- callee contract. (`render` is recorded in mapping.md as an A-reference solely to
-- document the G-CONF binding to the real base renderer.)
-- axioms-end

-- pure-start
-- The bracketing test: a denominator factor's base needs an extra pair of brackets
-- exactly when it has more than one component AND is a compound product or power.
def needsBrackets (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : Prop :=
  baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)

instance (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) :
    Decidable (needsBrackets baseComponentCount baseIsProduct baseIsPower) := by
  unfold needsBrackets; infer_instance
-- pure-end

-- post-conditions-start
/-- The text of one denominator factor: the base fragment produced by `render`,
wrapped in a single pair of brackets exactly when the base is a multi-component
product or power, and otherwise spliced in unchanged.

Frame discipline: the bracketing decision and the literal bracket characters are
pinned, and the inner fragment is pinned to `render base`, so no part of the
output is left free. -/
def problem_spec_printDenominatorFactor
    {Expr : Type}
    (render : Expr → String) (base : Expr)
    (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool)
    (result : String) : Prop :=
  result =
    (if needsBrackets baseComponentCount baseIsProduct baseIsPower
     then "(" ++ render base ++ ")"
     else render base)
-- post-conditions-end

-- impl-start
def implementation_printDenominatorFactor
    {Expr : Type}
    (render : Expr → String) (base : Expr)
    (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool) : String := Id.run do
  let baseStr := render base
  let needParen := baseComponentCount ≠ 1 ∧ (baseIsProduct = true ∨ baseIsPower = true)
  if needParen then
    return "(" ++ baseStr ++ ")"
  return baseStr
-- impl-end

-- proof-start
theorem correct_printDenominatorFactor :
    ∀ {Expr : Type}
      (render : Expr → String) (base : Expr)
      (baseComponentCount : Nat) (baseIsProduct baseIsPower : Bool),
      problem_spec_printDenominatorFactor render base baseComponentCount baseIsProduct baseIsPower
        (implementation_printDenominatorFactor render base baseComponentCount baseIsProduct baseIsPower) := by
  intro Expr render base baseComponentCount baseIsProduct baseIsPower
  unfold problem_spec_printDenominatorFactor implementation_printDenominatorFactor needsBrackets
  simp only [Id.run]
  split <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: fully-pinned functional spec — problem_spec pins result = (if needsBrackets baseComponentCount baseIsProduct baseIsPower then "(" ++ render base ++ ")" else render base). No frame freedom; any behaviorally-divergent impl is unprovable.

SAME_SPEC: all 7 attacks + pc = True (impl region edited only; axioms/pure/pre/post byte-identical).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently in 2 batches of 4):
- pc (gold Solution.lean): EXIT 0. #print axioms correct_printDenominatorFactor => 'does not depend on any axioms' (clean).
- atk_1 prepatch bug (needParen := count≠1 ∧ baseIsProduct only; drops baseIsPower disjunct): EXIT 1 (unprovable) — the fixed spec correctly rejects the prepatch impl, so the bug is reproduced/distinguished at the Lean layer.
- atk_2 partial-domain (special-case baseComponentCount=0 -> no wrap, else correct): EXIT 1.
- atk_3 boundary (needParen uses baseComponentCount=0 instead of ≠1): EXIT 1.
- atk_4 control-flow-effect (always wrap in brackets): EXIT 1 (goal pure("("++...++")")=render base in else-branch).
- atk_5 ungrounded-oracle echo (impl := if needsBrackets ... then "("++render base++")" else render base — literally the gold predicate): EXIT 0. #print axioms => 'does not depend on any axioms' (clean).
- atk_6 AND instead of OR (baseIsProduct ∧ baseIsPower): EXIT 1.
- atk_7 count≠0 instead of ≠1: EXIT 1.

MANDATORY RESOLVE ON EVERY CLEAN-AXIOM CLOSING IMPL: only atk_5 closes with clean axioms besides the gold pc. atk_5 is BEHAVIORALLY IDENTICAL to gold (computes exactly needsBrackets), so its faithful refined patch is the gold patch. Materialized atk_5_patch.diff and ran the OFFICIAL harness: swebench_unified.harness.run_resolve('sympy__sympy-21612', gold_patch, timeout=1800). RESULT: RESOLVED=True, note='resolved' (also confirmed via raw run_evaluation: 'Instances resolved: 1', ✓=1). Docker via `docker` (direct socket denied); first run_resolve returned no-report because the instance image was not yet pulled — after the image was pulled the official run_resolve returned RESOLVED=True deterministically. => The single verifying clean-axiom impl HAS a materialized faithful patch that RESOLVES. No verify⇏correct break.

Prepatch resolve note: empty-patch prediction returned no-report (swebench short-circuits empty patches — harness artifact, not a signal). prepatch_reproduced=true is established at the spec layer: atk_1 (the exact prepatch impl) fails to close against the fixed spec (EXIT 1), so the spec distinguishes gold from prepatch.

REFINEMENT.MD AUDIT (A-leg focus per plan §4): 3 legs, all R / A-reference / I, no kind-3 (changed-inexpressible), no A-consumed.
- `let baseStr := render base` -> A-reference: render : Expr→String is universally quantified; documents the G-CONF binding to the real base-fragment renderer self.parenthesize(item.base, prec, strict=False). Correspondence holds — the spec is parametric over EVERY renderer, so no property of self.parenthesize is consumed; axiom_check.py is a legitimate skip stub (no consumed axiom).
- needParen predicate -> R: baseComponentCount≠1 ↔ len(item.args[0].args)!=1; baseIsProduct ↔ isinstance(item.base,Mul); baseIsPower ↔ isinstance(item.base,Pow). Faithful type refinement of the widened isinstance test (Mul -> (Mul,Pow)).
- wrap template -> I: "(%s)" bracket wrap iff item∈pow_paren, else unchanged fragment.
A-reference correspondence to the real callee is sound.

CONCLUSION: verify⇒correct holds. Behaviorally-wrong impls (atk_1,2,3,4,6,7) are all unprovable; the only additional closing impl (atk_5) is a gold-equivalent echo whose faithful patch RESOLVES under the official harness (policy-compliant, not a weakness). ≥5 distinct wrong impls attacked; none breaks the spec. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-not-too-strong / no-drift) check for sympy__sympy-21612 lean bundle. FAITHFUL: no diverging input exists.

### Spec integrity
- Solution.lean compiles via scripts/lean_verify.sh (exit 0); `#print axioms correct_printDenominatorFactor` reports 'does not depend on any axioms' -> real proof, no sorryAx.
- swebench_unified.markers.same_spec confirms the spec region (axioms/pure/post-conditions) is byte-identical between Solution.lean and Solution_prepatch.lean and self-stable; only impl+proof regions differ (prepatch drops the baseIsPower disjunct), which is the intended differential.

### MODEL vs REAL CALLEE:
- Real patched _print_Mul (sympy/printing/str.py:333-356 at base b4777fdc) decides an extra denominator-factor bracket via `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))` then wraps `"(%s)" % b_str[i]`. The Lean spec predicate `baseComponentCount != 1 AND (baseIsProduct OR baseIsPower)` with post-condition `if needsBrackets then "("++render base++")" else render base` is an exact op-for-op transliteration (mapping.md / refinement.md bindings verified).

### EMPIRICAL FAITHFULNESS (patched sympy tree at base_commit, PYTHONPATH-isolated):
- conformance_check.py (pinned Random(21612), N=100000): 100000/100000 in-model, 0 disagreements.
- Exhaustive shallow enumeration of 2040 diverse bases (atoms; Mul/Add/Pow with evaluate True/False; sin/cos/tan/exp/log; triple products; nested inverse powers): 0 disagreements.
- Targeted edge cases confirm exact match incl. bug trigger 1/y (bip=F,biw=T -> wrapped), nested 1/(1/y), y**2, (y*z)**2, Add bases (bip=biw=F -> not wrapped), Mul bases -> wrapped; oracle==shadow in every case.

The spec is neither too strong nor drifted: it brackets precisely the multi-component product-or-power bases, matching the real StrPrinter on all tested inputs including boundary/adversarial ones. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Regenerated the consumer spec view with swebench_unified.markers.spec_view (lean backend) and ran leakage.screen against the public problem_statement + gold patch: 0 hard failures, 0 warnings. same_spec(Solution, Solution_prepatch)=True — the ONLY delta between patched/prepatch is the elided impl region. Gold edit is `isinstance(item.base, Mul)` -> `isinstance(item.base, (Mul, Pow))` (widen bracket-needed test from product to product-or-power). Spec view leaks none of the edit's identity: (1) no diff markers/hunk headers; (2) no gold-patch line reproduced — `isinstance`, `item.base`, `Mul`, `Pow` never appear in the view; (3) patched file path `sympy/printing/str.py` absent; (4) patched symbol `apow` absent; (5) no bug/fix/regression narration in visible comments/docstrings. Crucially, the pre-patch fix-narration comment ("PRE-PATCH (buggy)...") lives entirely inside the impl region, which the projection replaces with `-- implementation elided` — it is NOT consumer-visible. The visible prose/spec states the CORRECT bracketing rule abstractly (baseComponentCount != 1 && (baseIsProduct || baseIsPower), with `render` an arbitrary function), using abstracted param names rather than the Python isinstance/Mul/Pow mechanism. This is the expected spec-encodes-correct-behavior content, not gold reconstruction: the 'power'/reciprocal denominator case is already implicit in the public problem_statement's own examples (`((a**3+b)/c)/1/(c**2)` and, via the general fraction phenomenon, denominators that are themselves fractions losing brackets). Nothing in the view narrows the solution beyond what the public task already exposes. Note: 'buggy' narration in Solution_prepatch impl and the hints-only mini-diff are NOT in scope (impl elided; hints_text excluded by policy).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
