# P2 adversarial audit — django__django-16139

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_prepatch.lean`, `atk2_partial.lean`, `atk3_boundary.lean`, `atk4_ignore_template.lean`, `atk6_extra_suffix.lean`, `atk7_wrong_segment.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
 def implementation_passwordHelpText
     (template : List Char) (pk : Nat) : List Char := Id.run do
   let mut helpText := template
-  let url := mkUrl pk
+  let url := "../password/".toList
   helpText := formatFirst helpText url
   return helpText
 -- impl-end
```

Attack 2 — `atk2_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
 def implementation_passwordHelpText
     (template : List Char) (pk : Nat) : List Char := Id.run do
   let mut helpText := template
-  let url := mkUrl pk
+  let url := if pk == 0 then "../../X/password/".toList else mkUrl pk
   helpText := formatFirst helpText url
   return helpText
 -- impl-end
@@ -51,5 +51,5 @@
       (implementation_passwordHelpText template pk) := by
   intro template pk
   unfold problem_spec_passwordHelpText implementation_passwordHelpText
-  rfl
+  simp [mkUrl]
 -- proof-end
```

Attack 3 — `atk3_boundary.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
 def implementation_passwordHelpText
     (template : List Char) (pk : Nat) : List Char := Id.run do
   let mut helpText := template
-  let url := mkUrl pk
+  let url := "../".toList ++ (toString pk).toList ++ "/password/".toList
   helpText := formatFirst helpText url
   return helpText
 -- impl-end
```

Attack 4 — `atk4_ignore_template.lean` → rejected (same spec, does not verify — good)

```diff
@@ -39,10 +39,8 @@
 -- impl-start
 def implementation_passwordHelpText
     (template : List Char) (pk : Nat) : List Char := Id.run do
-  let mut helpText := template
   let url := mkUrl pk
-  helpText := formatFirst helpText url
-  return helpText
+  return url
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -38,11 +38,8 @@
 
 -- impl-start
 def implementation_passwordHelpText
-    (template : List Char) (pk : Nat) : List Char := Id.run do
-  let mut helpText := template
-  let url := mkUrl pk
-  helpText := formatFirst helpText url
-  return helpText
+    (template : List Char) (pk : Nat) : List Char :=
+  formatFirst template (mkUrl pk)
 -- impl-end
 
 -- proof-start
@@ -50,6 +47,5 @@
     problem_spec_passwordHelpText template pk
       (implementation_passwordHelpText template pk) := by
   intro template pk
-  unfold problem_spec_passwordHelpText implementation_passwordHelpText
   rfl
 -- proof-end
```

Attack 6 — `atk6_extra_suffix.lean` → rejected (same spec, does not verify — good)

```diff
@@ -41,7 +41,7 @@
     (template : List Char) (pk : Nat) : List Char := Id.run do
   let mut helpText := template
   let url := mkUrl pk
-  helpText := formatFirst helpText url
+  helpText := formatFirst helpText url ++ "/".toList
   return helpText
 -- impl-end
 
```

Attack 7 — `atk7_wrong_segment.lean` → rejected (same spec, does not verify — good)

```diff
@@ -40,7 +40,7 @@
 def implementation_passwordHelpText
     (template : List Char) (pk : Nat) : List Char := Id.run do
   let mut helpText := template
-  let url := mkUrl pk
+  let url := "../../".toList ++ (toString pk).toList ++ "/pwd/".toList
   helpText := formatFirst helpText url
   return helpText
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the positional
-- single-field string template substitution is modeled DEEPLY (`formatFirst`,
-- below) rather than axiomatized, so its standard-library reference
-- implementation is validated as an A-reference by G-AX. The proof agent may
-- add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Substitute the replacement text into the FIRST positional placeholder
`{}` of a template, leaving the remainder of the template verbatim. A template
carrying exactly one placeholder yields the replacement spliced in at that
position; if there is no placeholder the template is returned unchanged. -/
def formatFirst : List Char → List Char → List Char
  | [], _ => []
  | '{' :: '}' :: rest, repl => repl ++ rest
  | c :: cs, repl => c :: formatFirst cs repl

/-- The relative URL that locates the password-change form for a record from the
record's own numeric identifier: two parent-directory steps, the decimal
identifier, then the `password` path segment. -/
def mkUrl (pk : Nat) : List Char :=
  "../../".toList ++ (toString pk).toList ++ "/password/".toList
-- pure-end

-- post-conditions-start
/-- The resulting help text is exactly the template with its single positional
placeholder replaced by the relative URL built from the record's own numeric
identifier (`mkUrl`); every other character of the template is preserved in
order. -/
def problem_spec_passwordHelpText
    (template : List Char) (pk : Nat) (result : List Char) : Prop :=
  result = formatFirst template (mkUrl pk)
-- post-conditions-end

-- impl-start
def implementation_passwordHelpText
    (template : List Char) (pk : Nat) : List Char := Id.run do
  let mut helpText := template
  let url := mkUrl pk
  helpText := formatFirst helpText url
  return helpText
-- impl-end

-- proof-start
theorem correct_passwordHelpText : ∀ (template : List Char) (pk : Nat),
    problem_spec_passwordHelpText template pk
      (implementation_passwordHelpText template pk) := by
  intro template pk
  unfold problem_spec_passwordHelpText implementation_passwordHelpText
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Exact-equality spec: problem_spec := (result = formatFirst template (mkUrl pk)), proven by rfl. Any impl whose correct_ closes must equal the gold output extensionally on ALL (template,pk). Ran positive control + 7 same-spec attacks (all same_spec=True confirmed via swebench_unified.markers.same_spec) through scripts/lean_verify.sh (300s cap), concurrently in 2 batches of 4.

### RESULTS (exit codes, lean_verify.sh):
- pos_control.lean (gold): EXIT 0; appended `#print axioms correct_passwordHelpText` => 'does not depend on any axioms' (clean).
- atk1_prepatch (url="../password/", the prepatch bug, ignores pk): EXIT 1 — genuine `rfl` failed / unsolved equality goal. Prepatch bug reproduced.
- atk2_partial (partial-domain: correct for pk!=0, wrong "../../X/password/" at pk=0): EXIT 1 — `simp [mkUrl]` leaves unsolved equality goal.
- atk3_boundary (single "../" instead of "../../"): EXIT 1 — rfl failed.
- atk4_ignore_template (control-flow-effect: drops template, returns url only): EXIT 1 — rfl failed.
- atk6_extra_suffix (control-flow-effect: appends extra "/"): EXIT 1 — rfl failed.
- atk7_wrong_segment (ungrounded value: "/pwd/" instead of "/password/"): EXIT 1 — rfl failed.
- atk5_echo (ungrounded-oracle echo: impl := formatFirst template (mkUrl pk), literally the spec RHS): EXIT 0; clean axioms. This CLOSES.

Materialize+resolve obligation: the ONLY verifying wrong-shaped candidate is atk5, which is extensionally IDENTICAL to the gold output on every (template,pk). Its faithful refined patch is therefore byte-identical to the gold patch (provided in `patches`), which G-RESOLVE already records as 'resolved'. A resolving gold-echo is not a spec weakness (per unified G-PANEL-1 policy: same-spec verifying attack fails only if its refined patch does NOT resolve). No wrong-behaviour impl closes, so there is NO closing-but-non-resolving candidate to materialize — the exact functional-equality postcondition forces every closing impl to the unique gold output.

Refinement audit: refinement.md rows are I / R / A-reference / I — no kind-3 (changed-inexpressible) leg. Sole A-reference (formatFirst == single-positional-field str.format) validated by G-AX (pass, seed 16139, 1e5 probes). R-leg (mkUrl pk = "../../"++toString pk++"/password/" <-> f"../../{self.instance.pk}/password/") corresponds to the CHANGED expression and is reconstructed concretely, not axiomatized. axioms region empty; #print axioms clean for all verifying impls. A-leg correspondence to the real callee (str.format) holds.

Verdict: SOUND. >=5 (7) distinct same-spec attacks run; all 6 wrong-behaviour impls fail to close with genuine equality-goal errors; the one closing candidate is a behavioural gold-echo whose faithful patch resolves. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk1_prepatch.lean`, `atk2_partial.lean`, `atk3_boundary.lean`, `atk4_ignore_template.lean`, `atk6_extra_suffix.lean`, `atk7_wrong_segment.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5_echo.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_ignore_template.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_echo.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6_extra_suffix.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_wrong_segment.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: the positional
-- single-field string template substitution is modeled DEEPLY (`formatFirst`,
-- below) rather than axiomatized, so its standard-library reference
-- implementation is validated as an A-reference by G-AX. The proof agent may
-- add `_prop` axioms only if stuck.
-- axioms-end

-- pure-start
/-- Substitute the replacement text into the FIRST positional placeholder
`{}` of a template, leaving the remainder of the template verbatim. A template
carrying exactly one placeholder yields the replacement spliced in at that
position; if there is no placeholder the template is returned unchanged. -/
def formatFirst : List Char → List Char → List Char
  | [], _ => []
  | '{' :: '}' :: rest, repl => repl ++ rest
  | c :: cs, repl => c :: formatFirst cs repl

/-- The relative URL that locates the password-change form for a record from the
record's own numeric identifier: two parent-directory steps, the decimal
identifier, then the `password` path segment. -/
def mkUrl (pk : Nat) : List Char :=
  "../../".toList ++ (toString pk).toList ++ "/password/".toList
-- pure-end

-- post-conditions-start
/-- The resulting help text is exactly the template with its single positional
placeholder replaced by the relative URL built from the record's own numeric
identifier (`mkUrl`); every other character of the template is preserved in
order. -/
def problem_spec_passwordHelpText
    (template : List Char) (pk : Nat) (result : List Char) : Prop :=
  result = formatFirst template (mkUrl pk)
-- post-conditions-end

-- impl-start
def implementation_passwordHelpText
    (template : List Char) (pk : Nat) : List Char := Id.run do
  let mut helpText := template
  let url := mkUrl pk
  helpText := formatFirst helpText url
  return helpText
-- impl-end

-- proof-start
theorem correct_passwordHelpText : ∀ (template : List Char) (pk : Nat),
    problem_spec_passwordHelpText template pk
      (implementation_passwordHelpText template pk) := by
  intro template pk
  unfold problem_spec_passwordHelpText implementation_passwordHelpText
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Exact-equality spec: problem_spec := (result = formatFirst template (mkUrl pk)), proven by rfl. Any impl whose correct_ closes must equal the gold output extensionally on ALL (template,pk). Ran positive control + 7 same-spec attacks (all same_spec=True confirmed via swebench_unified.markers.same_spec) through scripts/lean_verify.sh (300s cap), concurrently in 2 batches of 4.

### RESULTS (exit codes, lean_verify.sh):
- pos_control.lean (gold): EXIT 0; appended `#print axioms correct_passwordHelpText` => 'does not depend on any axioms' (clean).
- atk1_prepatch (url="../password/", the prepatch bug, ignores pk): EXIT 1 — genuine `rfl` failed / unsolved equality goal. Prepatch bug reproduced.
- atk2_partial (partial-domain: correct for pk!=0, wrong "../../X/password/" at pk=0): EXIT 1 — `simp [mkUrl]` leaves unsolved equality goal.
- atk3_boundary (single "../" instead of "../../"): EXIT 1 — rfl failed.
- atk4_ignore_template (control-flow-effect: drops template, returns url only): EXIT 1 — rfl failed.
- atk6_extra_suffix (control-flow-effect: appends extra "/"): EXIT 1 — rfl failed.
- atk7_wrong_segment (ungrounded value: "/pwd/" instead of "/password/"): EXIT 1 — rfl failed.
- atk5_echo (ungrounded-oracle echo: impl := formatFirst template (mkUrl pk), literally the spec RHS): EXIT 0; clean axioms. This CLOSES.

Materialize+resolve obligation: the ONLY verifying wrong-shaped candidate is atk5, which is extensionally IDENTICAL to the gold output on every (template,pk). Its faithful refined patch is therefore byte-identical to the gold patch (provided in `patches`), which G-RESOLVE already records as 'resolved'. A resolving gold-echo is not a spec weakness (per unified G-PANEL-1 policy: same-spec verifying attack fails only if its refined patch does NOT resolve). No wrong-behaviour impl closes, so there is NO closing-but-non-resolving candidate to materialize — the exact functional-equality postcondition forces every closing impl to the unique gold output.

Refinement audit: refinement.md rows are I / R / A-reference / I — no kind-3 (changed-inexpressible) leg. Sole A-reference (formatFirst == single-positional-field str.format) validated by G-AX (pass, seed 16139, 1e5 probes). R-leg (mkUrl pk = "../../"++toString pk++"/password/" <-> f"../../{self.instance.pk}/password/") corresponds to the CHANGED expression and is reconstructed concretely, not axiomatized. axioms region empty; #print axioms clean for all verifying impls. A-leg correspondence to the real callee (str.format) holds.

Verdict: SOUND. >=5 (7) distinct same-spec attacks run; all 6 wrong-behaviour impls fail to close with genuine equality-goal errors; the one closing candidate is a behavioural gold-echo whose faithful patch resolves. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack found NO divergence. (1) same_spec(Solution, Solution_prepatch, LeanBackend.language)=True — post-conditions/pure/axioms region byte-identical across the patch; only impl differs (mkUrl vs mkUrlBug). (2) Solution.lean compiles under lean_verify.sh (exit 0); #print axioms correct_passwordHelpText reports NO axiom dependence — proof (rfl) is genuine, not sorryAx-faked. (3) Model vs real callee: real post-patch stmt is password.help_text.format(f"../../{self.instance.pk}/password/"); modeled as formatFirst template (mkUrl pk), mkUrl pk = "../../"++toString pk++"/password/". Fuzzed formatFirst/mkUrl against Python str.format over the actual help_text template with 50k pk values (0 divergences) and 100k in-domain random templates (exactly one '{}', no other braces — the real template shape per mapping.md/G-AX; brace-free replacements, which mkUrl always yields) → 0 divergences. Domain restriction is legitimate: real template has exactly one '{}', and self.instance.pk is a non-negative int so str(pk)==toString(pk:Nat); the to_field test only alters the admin reverse URL, not self.instance.pk. (4) G-DIFF verified: prepatch buggy impl (mkUrlBug='../password/') fails rfl against the frozen spec, so the spec truly discriminates the fix. Spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region confirmed byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (LeanBackend) = True; only the impl/proof regions differ (mkUrl vs mkUrlBug), which are elided from the spec view.

The spec view encodes the post-patch behavior as `mkUrl pk = "../../" ++ toString pk ++ "/password/"` and `problem_spec := result = formatFirst template (mkUrl pk)`, i.e. the URL `../../<pk>/password/`. This is exactly the gold edit (URL argument changing from `"../password/"` to `f"../../{self.instance.pk}/password/"`).

However, the PUBLIC problem_statement already discloses this exact fix verbatim: it quotes the current code `password.help_text.format("../password/")` and explicitly says "It's as simple as replacing ... with `password.help_text.format(f"../../{self.instance.pk}/password/")`." The problem statement even walks through the reasoning (dropping the pk-only-access assumption). Therefore the spec's encoding of the post-patch URL reveals NOTHING beyond the public problem_statement.

Doc-comments in the spec view are abstract (they describe formatFirst/mkUrl semantics and the substitution behavior in general terms) and do not quote gold-patch line specifics beyond what the public statement already contains. No spec-view line leaks the gold edit beyond the public problem_statement. Leakage screen is bounded by problem_statement (not hints_text, which is empty here); nothing exceeds it.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
