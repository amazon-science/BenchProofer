# P2 adversarial audit — django__django-11119

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,9 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
   let mut autoescape := suppliedCtxAutoescape
   if !suppliedIsContext then
-    autoescape := engineAutoescape
+    autoescape := true
   return leading ++ renderValue autoescape value ++ trailing
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,9 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
   let mut autoescape := suppliedCtxAutoescape
   if !suppliedIsContext then
-    autoescape := engineAutoescape
+    autoescape := false
   return leading ++ renderValue autoescape value ++ trailing
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,7 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
-  let mut autoescape := suppliedCtxAutoescape
-  if !suppliedIsContext then
-    autoescape := engineAutoescape
+  let autoescape := if suppliedIsContext then engineAutoescape else suppliedCtxAutoescape
   return leading ++ renderValue autoescape value ++ trailing
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,7 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
-  let mut autoescape := suppliedCtxAutoescape
-  if !suppliedIsContext then
-    autoescape := engineAutoescape
+  let autoescape := suppliedCtxAutoescape
   return leading ++ renderValue autoescape value ++ trailing
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,7 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
-  let mut autoescape := suppliedCtxAutoescape
-  if !suppliedIsContext then
-    autoescape := engineAutoescape
+  let autoescape := engineAutoescape
   return leading ++ renderValue autoescape value ++ trailing
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,8 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
-  let mut autoescape := suppliedCtxAutoescape
-  if !suppliedIsContext then
-    autoescape := engineAutoescape
-  return leading ++ renderValue autoescape value ++ trailing
+  let autoescape := if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape
+  return leading ++ renderValue autoescape value
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,7 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
-  let mut autoescape := suppliedCtxAutoescape
-  if !suppliedIsContext then
-    autoescape := engineAutoescape
+  let autoescape := if suppliedIsContext then (suppliedCtxAutoescape && engineAutoescape) else engineAutoescape
   return leading ++ renderValue autoescape value ++ trailing
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,12 +66,8 @@
     (renderValue : Bool → String → String)
     (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
     (leading value trailing : String) : String := Id.run do
-  -- A ready-made context renders with its own escaping flag; plain data renders
-  -- with the engine's configured escaping flag.
-  let mut autoescape := suppliedCtxAutoescape
-  if !suppliedIsContext then
-    autoescape := engineAutoescape
-  return leading ++ renderValue autoescape value ++ trailing
+  let autoescape := if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape
+  return trailing ++ renderValue autoescape value ++ leading
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a template — literal text surrounding a single interpolated value — to
its output string, with attention to whether HTML autoescaping is active.

The interpolated value is turned into display text by a value-rendering step that
depends on a single boolean: whether automatic escaping is in effect. Literal
text on either side of the value passes through unchanged.

Which escaping setting governs the value-rendering step is determined by HOW the
caller supplies the rendering context:

  * when the caller passes a ready-made rendering context, that context's OWN
    escaping setting is the one in effect;
  * when the caller passes plain data (so a fresh rendering context is built for
    it), the escaping setting configured on the rendering engine is the one in
    effect.

The value-rendering step itself (turning a value into escaped-or-plain display
text) is the SAME operation regardless of which branch supplied the flag; here it
is taken as an arbitrary function of the escaping flag and the value, so the
behavior pinned below is exactly "the correct escaping flag reaches the
value-rendering step, and the literal text frames it unchanged."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The downstream
-- value-rendering operation (turning one interpolated value into its display
-- text given whether escaping is active) is modeled as an arbitrary function
-- parameter `renderValue : Bool → String → String`: the modeled change is solely
-- WHICH escaping flag is handed to that step, so the result is pinned for every
-- possible value-renderer. Hence the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the rendered output is the
-- literal-text frame around the value-rendering step applied to the value.
-- pure-end

-- post-conditions-start
/-- The rendered output is fully pinned to the inputs:

  * the escaping flag actually used (`eff`) is the supplied context's own flag
    when a ready-made context is given, and the engine's configured flag when
    plain data is given;
  * the output is exactly the leading literal text, then the value-rendering step
    applied to that flag and the interpolated value, then the trailing literal
    text.

No output component is left free: both the leading and trailing literals are
pinned to their inputs, and the value portion is pinned to the value-renderer at
the correctly-selected flag. -/
def problem_spec_renderToString
    (renderValue : Bool → String → String)
    (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
    (leading value trailing : String) (result : String) : Prop :=
  let eff := if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape
  result = leading ++ renderValue eff value ++ trailing
-- post-conditions-end

-- impl-start
def implementation_renderToString
    (renderValue : Bool → String → String)
    (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
    (leading value trailing : String) : String := Id.run do
  let autoescape := if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape
  return leading ++ renderValue autoescape value ++ trailing
-- impl-end

-- proof-start
theorem correct_renderToString :
    ∀ (renderValue : Bool → String → String)
      (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
      (leading value trailing : String),
      problem_spec_renderToString renderValue engineAutoescape suppliedIsContext
          suppliedCtxAutoescape leading value trailing
        (implementation_renderToString renderValue engineAutoescape suppliedIsContext
          suppliedCtxAutoescape leading value trailing) := by
  intro renderValue engineAutoescape suppliedIsContext suppliedCtxAutoescape
        leading value trailing
  unfold problem_spec_renderToString implementation_renderToString
  cases suppliedIsContext <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_renderToString is an EXACT string equality universally quantified over an arbitrary renderValue : Bool -> String -> String. Because renderValue is arbitrary, any verifying impl must (a) pass exactly eff = (if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape) to renderValue and (b) frame with exactly leading ++ ... ++ trailing. This is maximally tight; no wrong flag-selection or framing can hide behind a specific renderer.

PROTOCOL: 8 DISTINCT same-spec wrong impls (all same_spec=True, impl-region-only edits, axioms/pure/pre/post byte-identical). Verified concurrently (<=4 background jobs) via scripts/lean_verify.sh (300s cap). ALL 8 FAIL to close (exit 1); positive control closes (exit 0) and `#print axioms correct_renderToString` => 'does not depend on any axioms' (clean). Since NO wrong impl has a closing clean-axiom proof, there is no faithful patch to materialize/resolve (patches={} correctly).

Attacks & results:
- atk_1 (control-flow-effect; else-branch hard-wires true = THE PREPATCH BUG): lean_verify exit 1.
- atk_2 (control-flow-effect; else-branch = false): exit 1.
- atk_3 (control-flow-effect; branches swapped, if suppliedIsContext then engineAutoescape else suppliedCtxAutoescape): exit 1.
- atk_4 (partial-domain/ungrounded; always suppliedCtxAutoescape, ignores plain-data fix): exit 1.
- atk_5 (partial-domain/ungrounded; always engineAutoescape, ignores context branch): exit 1.
- atk_6 (boundary/framing; drops trailing): exit 1.
- atk_7 (control-flow-effect; ctx flag = suppliedCtxAutoescape && engineAutoescape): exit 1.
- atk_8 (boundary/framing; swaps leading/trailing => trailing ++ value ++ leading): exit 1.
Command for each: `bash scripts/lean_verify.sh <path>`.
Positive control command: same; exit 0. Axioms command: appended `#print axioms correct_renderToString` to a copy (pos_axioms.lean), lean_verify exit 0, output 'correct_renderToString does not depend on any axioms'.

PREPATCH: atk_1 is behaviorally the prepatch impl (Solution_prepatch.lean impl region; diff is comment-only) and FAILS against the correct spec -> spec discriminates buggy from fixed. prepatch_reproduced=true.

REFINEMENT AUDIT (refinement.md): legs are R (ops 1,2 flag selection), A-reference (op 3 renderValue, universally quantified, bound to REAL render_value_in_context in G-CONF; proof consumes no property so correctly NOT A-consumed and NOT deep-modeled), I (ops 4,5 string framing/return). No kind-3 legs. No axiom/opaque/sorry in Solution.lean; meta.json axioms=[]; axiom_check.py is a skip stub (consistent, no consumed axiom). A-reference correspondence to render_value_in_context (reads context.autoescape) holds and is the sole downstream callee. conformance_check.py differential-tests the R/I shadow against the real patched render_to_string over 1e5 inputs with the real render_value_in_context oracle (seed 11119).

VERDICT: SOUND. >=5 (8) distinct same-spec wrong impls attacked; none has a closing clean-axiom proof, so verify => correct holds for this bundle. No BROKEN counterexample; no resolve run needed (no verifying wrong impl).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Rendering a template — literal text surrounding a single interpolated value — to
its output string, with attention to whether HTML autoescaping is active.

The interpolated value is turned into display text by a value-rendering step that
depends on a single boolean: whether automatic escaping is in effect. Literal
text on either side of the value passes through unchanged.

Which escaping setting governs the value-rendering step is determined by HOW the
caller supplies the rendering context:

  * when the caller passes a ready-made rendering context, that context's OWN
    escaping setting is the one in effect;
  * when the caller passes plain data (so a fresh rendering context is built for
    it), the escaping setting configured on the rendering engine is the one in
    effect.

The value-rendering step itself (turning a value into escaped-or-plain display
text) is the SAME operation regardless of which branch supplied the flag; here it
is taken as an arbitrary function of the escaping flag and the value, so the
behavior pinned below is exactly "the correct escaping flag reaches the
value-rendering step, and the literal text frames it unchanged."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The downstream
-- value-rendering operation (turning one interpolated value into its display
-- text given whether escaping is active) is modeled as an arbitrary function
-- parameter `renderValue : Bool → String → String`: the modeled change is solely
-- WHICH escaping flag is handed to that step, so the result is pinned for every
-- possible value-renderer. Hence the spec needs no `opaque`/`axiom` callee
-- contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the rendered output is the
-- literal-text frame around the value-rendering step applied to the value.
-- pure-end

-- post-conditions-start
/-- The rendered output is fully pinned to the inputs:

  * the escaping flag actually used (`eff`) is the supplied context's own flag
    when a ready-made context is given, and the engine's configured flag when
    plain data is given;
  * the output is exactly the leading literal text, then the value-rendering step
    applied to that flag and the interpolated value, then the trailing literal
    text.

No output component is left free: both the leading and trailing literals are
pinned to their inputs, and the value portion is pinned to the value-renderer at
the correctly-selected flag. -/
def problem_spec_renderToString
    (renderValue : Bool → String → String)
    (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
    (leading value trailing : String) (result : String) : Prop :=
  let eff := if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape
  result = leading ++ renderValue eff value ++ trailing
-- post-conditions-end

-- impl-start
def implementation_renderToString
    (renderValue : Bool → String → String)
    (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
    (leading value trailing : String) : String := Id.run do
  let autoescape := if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape
  return leading ++ renderValue autoescape value ++ trailing
-- impl-end

-- proof-start
theorem correct_renderToString :
    ∀ (renderValue : Bool → String → String)
      (engineAutoescape suppliedIsContext suppliedCtxAutoescape : Bool)
      (leading value trailing : String),
      problem_spec_renderToString renderValue engineAutoescape suppliedIsContext
          suppliedCtxAutoescape leading value trailing
        (implementation_renderToString renderValue engineAutoescape suppliedIsContext
          suppliedCtxAutoescape leading value trailing) := by
  intro renderValue engineAutoescape suppliedIsContext suppliedCtxAutoescape
        leading value trailing
  unfold problem_spec_renderToString implementation_renderToString
  cases suppliedIsContext <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Spec problem_spec_renderToString is an EXACT string equality universally quantified over an arbitrary renderValue : Bool -> String -> String. Because renderValue is arbitrary, any verifying impl must (a) pass exactly eff = (if suppliedIsContext then suppliedCtxAutoescape else engineAutoescape) to renderValue and (b) frame with exactly leading ++ ... ++ trailing. This is maximally tight; no wrong flag-selection or framing can hide behind a specific renderer.

PROTOCOL: 8 DISTINCT same-spec wrong impls (all same_spec=True, impl-region-only edits, axioms/pure/pre/post byte-identical). Verified concurrently (<=4 background jobs) via scripts/lean_verify.sh (300s cap). ALL 8 FAIL to close (exit 1); positive control closes (exit 0) and `#print axioms correct_renderToString` => 'does not depend on any axioms' (clean). Since NO wrong impl has a closing clean-axiom proof, there is no faithful patch to materialize/resolve (patches={} correctly).

Attacks & results:
- atk_1 (control-flow-effect; else-branch hard-wires true = THE PREPATCH BUG): lean_verify exit 1.
- atk_2 (control-flow-effect; else-branch = false): exit 1.
- atk_3 (control-flow-effect; branches swapped, if suppliedIsContext then engineAutoescape else suppliedCtxAutoescape): exit 1.
- atk_4 (partial-domain/ungrounded; always suppliedCtxAutoescape, ignores plain-data fix): exit 1.
- atk_5 (partial-domain/ungrounded; always engineAutoescape, ignores context branch): exit 1.
- atk_6 (boundary/framing; drops trailing): exit 1.
- atk_7 (control-flow-effect; ctx flag = suppliedCtxAutoescape && engineAutoescape): exit 1.
- atk_8 (boundary/framing; swaps leading/trailing => trailing ++ value ++ leading): exit 1.
Command for each: `bash scripts/lean_verify.sh <path>`.
Positive control command: same; exit 0. Axioms command: appended `#print axioms correct_renderToString` to a copy (pos_axioms.lean), lean_verify exit 0, output 'correct_renderToString does not depend on any axioms'.

PREPATCH: atk_1 is behaviorally the prepatch impl (Solution_prepatch.lean impl region; diff is comment-only) and FAILS against the correct spec -> spec discriminates buggy from fixed. prepatch_reproduced=true.

REFINEMENT AUDIT (refinement.md): legs are R (ops 1,2 flag selection), A-reference (op 3 renderValue, universally quantified, bound to REAL render_value_in_context in G-CONF; proof consumes no property so correctly NOT A-consumed and NOT deep-modeled), I (ops 4,5 string framing/return). No kind-3 legs. No axiom/opaque/sorry in Solution.lean; meta.json axioms=[]; axiom_check.py is a skip stub (consistent, no consumed axiom). A-reference correspondence to render_value_in_context (reads context.autoescape) holds and is the sole downstream callee. conformance_check.py differential-tests the R/I shadow against the real patched render_to_string over 1e5 inputs with the real render_value_in_context oracle (seed 11119).

VERDICT: SOUND. >=5 (8) distinct same-spec wrong impls attacked; none has a closing clean-axiom proof, so verify => correct holds for this bundle. No BROKEN counterexample; no resolve run needed (no verifying wrong impl).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found no divergence. Solution.lean compiles (lean_verify exit 0), no sorry, and `#print axioms correct_renderToString` reports 'does not depend on any axioms' — genuine proof. Spec regions (axioms/pure/post-conditions/spec_view) are byte-identical to Solution_prepatch.lean and match meta.json region_hashes; only impl differs (expected). Prepatch buggy impl genuinely FAILS the shared spec at the discriminating goal (suppliedIsContext=false branch: renderValue true value != renderValue engineAutoescape value), confirming the spec is discriminating (real negative control). Base source (d4df5e1) confirms gold patch Context(context)->Context(context, autoescape=self.autoescape). Real render_value_in_context reads context.autoescape (the modeled flag) plus use_tz/use_l10n which are no-ops on str values, so autoescape is the sole governing flag within the model's value:String domain. renderValue is universally quantified, so the post-condition pins only that the correct escaping flag reaches the value step and literals frame it unchanged — cannot be too-strong since satisfiable for every value-renderer including the real one. Empirical differential test: extracted base django, applied gold patch, ran conformance_check.py => 'G-CONF OK: 100000 inputs, 0 disagreements' between R/I shadow (bound to REAL render_value_in_context) and real patched Engine.render_to_string. No diverging input exists over the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (materialized via markers.spec_view, lean backend) = abstract docstring lines 4-25 + axioms/pure comments + post-condition `problem_spec_renderToString`; impl and proof are elided in the spec view (confirmed). same_spec(Solution, Solution_prepatch, lean)=True — spec region byte-identical, so no spec-view line differs between gold and prepatch twins.

Public problem_statement already discloses BOTH the bug and the fix: 'Engine.render_to_string() should honor the autoescape attribute' and 'a Context is created without specifying the engine autoescape attribute. So if you create an engine with autoescape=False and then call its render_to_string() method, the result will always be autoescaped.' This states plainly that the freshly-built (plain-data) rendering context must carry the engine's configured autoescape flag — exactly the gold edit `Context(context) -> Context(context, autoescape=self.autoescape)`.

Spec-view leakage check vs problem_statement (NOT hints_text):
- The plain-data => engine-flag clause (lines 17-19, and `else engineAutoescape` on line 60) is precisely what problem_statement already discloses; it does not exceed it.
- The ready-made-context => own-flag clause (lines 15-16, `if suppliedIsContext then suppliedCtxAutoescape`) describes UNCHANGED pre-existing behavior (gold patch touches only the else branch), so it reveals nothing about the gold EDIT.
- No Python-level gold specifics appear anywhere in the spec view: no `Context(...)` call site, no `autoescape=self.autoescape` keyword, no `isinstance(context, Context)`, no method/attribute/file/line names. All terms are abstract ('ready-made rendering context', 'plain data', 'escaping setting configured on the rendering engine').
- `renderValue : Bool -> String -> String` is universally quantified; internal escaping semantics (conditional_escape etc.) are abstracted away. The spec pins ONLY which flag is routed to the value-render step — the publicly-stated fix.
- hints_text is event-reservation noise and is not the comparison baseline regardless.

Restating correct intended behavior at abstract altitude is a spec's proper role, not gold reconstruction. No line leaks the gold edit beyond the public problem_statement. Recorded G-PANEL-3 verdict NO-LEAKAGE upheld.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
