# P2 adversarial audit — django__django-15103

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_scriptTag is a total functional equation (result = if optId != "" then <id-frame> else <no-id-frame>) over universally-quantified jsonBody/escapeId, leaving zero behavioral freedom. Every behaviorally-divergent same-spec impl fails to verify.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,17 +71,10 @@
     (jsonBody : String → String)
     (escapeId : String → String)
     (value optId : String) : String := Id.run do
-  -- Encode the value into its safe JSON body once; this step is independent of
-  -- any identifier.
   let jsonStr := jsonBody value
-  -- Select the script-tag frame: with an `id` attribute when an identifier is
-  -- supplied, otherwise without one.
   let mut result := ""
-  if optId ≠ "" then
-    result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
-      ++ jsonStr ++ "</script>"
-  else
-    result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
+  result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
+    ++ jsonStr ++ "</script>"
   return result
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,13 +71,9 @@
     (jsonBody : String → String)
     (escapeId : String → String)
     (value optId : String) : String := Id.run do
-  -- Encode the value into its safe JSON body once; this step is independent of
-  -- any identifier.
   let jsonStr := jsonBody value
-  -- Select the script-tag frame: with an `id` attribute when an identifier is
-  -- supplied, otherwise without one.
   let mut result := ""
-  if optId ≠ "" then
+  if optId = "" then
     result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
       ++ jsonStr ++ "</script>"
   else
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,17 +71,9 @@
     (jsonBody : String → String)
     (escapeId : String → String)
     (value optId : String) : String := Id.run do
-  -- Encode the value into its safe JSON body once; this step is independent of
-  -- any identifier.
   let jsonStr := jsonBody value
-  -- Select the script-tag frame: with an `id` attribute when an identifier is
-  -- supplied, otherwise without one.
   let mut result := ""
-  if optId ≠ "" then
-    result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
-      ++ jsonStr ++ "</script>"
-  else
-    result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
+  result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
   return result
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,13 +71,9 @@
     (jsonBody : String → String)
     (escapeId : String → String)
     (value optId : String) : String := Id.run do
-  -- Encode the value into its safe JSON body once; this step is independent of
-  -- any identifier.
   let jsonStr := jsonBody value
-  -- Select the script-tag frame: with an `id` attribute when an identifier is
-  -- supplied, otherwise without one.
   let mut result := ""
-  if optId ≠ "" then
+  if optId.length > 1 then
     result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
       ++ jsonStr ++ "</script>"
   else
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,15 +71,11 @@
     (jsonBody : String → String)
     (escapeId : String → String)
     (value optId : String) : String := Id.run do
-  -- Encode the value into its safe JSON body once; this step is independent of
-  -- any identifier.
   let jsonStr := jsonBody value
-  -- Select the script-tag frame: with an `id` attribute when an identifier is
-  -- supplied, otherwise without one.
   let mut result := ""
   if optId ≠ "" then
     result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
-      ++ jsonStr ++ "</script>"
+      ++ jsonStr
   else
     result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
   return result
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -71,14 +71,10 @@
     (jsonBody : String → String)
     (escapeId : String → String)
     (value optId : String) : String := Id.run do
-  -- Encode the value into its safe JSON body once; this step is independent of
-  -- any identifier.
   let jsonStr := jsonBody value
-  -- Select the script-tag frame: with an `id` attribute when an identifier is
-  -- supplied, otherwise without one.
   let mut result := ""
   if optId ≠ "" then
-    result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
+    result := "<script id=\"" ++ escapeId value ++ "\" type=\"application/json\">"
       ++ jsonStr ++ "</script>"
   else
     result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -71,18 +71,12 @@
     (jsonBody : String → String)
     (escapeId : String → String)
     (value optId : String) : String := Id.run do
-  -- Encode the value into its safe JSON body once; this step is independent of
-  -- any identifier.
   let jsonStr := jsonBody value
-  -- Select the script-tag frame: with an `id` attribute when an identifier is
-  -- supplied, otherwise without one.
-  let mut result := ""
-  if optId ≠ "" then
-    result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
-      ++ jsonStr ++ "</script>"
-  else
-    result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
-  return result
+  return (if optId ≠ "" then
+      "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
+        ++ jsonStr ++ "</script>"
+    else
+      "<script type=\"application/json\">" ++ jsonStr ++ "</script>")
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Wrapping a JSON-encoded value inside a `<script type="application/json">` tag for
safe inclusion in HTML output.

The value is first turned into a safe, escaped JSON body by an encoding step that
is independent of any identifier. The body is then embedded in a script tag. The
caller may optionally supply an identifier string:

  * when a non-empty identifier is supplied, the script tag carries an `id`
    attribute set to that identifier (with the identifier escaped for attribute
    use), and the JSON body follows;
  * when no identifier is supplied (the identifier is absent / empty), the script
    tag is emitted WITHOUT any `id` attribute, the JSON body following directly.

The JSON-encoding step and the attribute-escaping step are the SAME operations in
both cases; here they are taken as arbitrary functions, so the behavior pinned
below is exactly "the presence of an identifier selects whether an `id` attribute
is emitted, and the encoded body is framed by the corresponding script tag."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two unchanged steps are
-- modeled as arbitrary function parameters:
--   * `jsonBody : String → String` — turning the value into its safe, escaped
--     JSON body (the encoder + entity translation step); independent of any
--     identifier, so it is the SAME in both branches.
--   * `escapeId : String → String` — escaping the identifier for safe use inside
--     an attribute value (the same escaping the formatter applies to substituted
--     arguments).
-- Leaving both universally quantified means the spec holds for every encoder /
-- escaper; the modeled change is solely WHETHER the `id` attribute is emitted.
-- Hence the spec needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: each branch's output is a literal
-- frame around the (encoded body, escaped identifier) produced by the abstract
-- steps above.
-- pure-end

-- post-conditions-start
/-- The output script-tag string is fully pinned to the inputs:

  * when the identifier is non-empty, the output is the opening `<script>` tag
    carrying an `id` attribute set to the escaped identifier, then the encoded
    JSON body, then the closing tag;
  * when the identifier is empty (no identifier supplied), the output is the
    opening `<script>` tag WITHOUT any `id` attribute, then the encoded JSON body,
    then the closing tag.

No output component is left free: the literal tag text is constant, the body portion
is pinned to the encoder applied to the value, and (in the with-identifier branch)
the attribute value is pinned to the escaper applied to the identifier. -/
def problem_spec_scriptTag
    (jsonBody : String → String)
    (escapeId : String → String)
    (value optId : String) (result : String) : Prop :=
  result =
    if optId ≠ "" then
      "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
        ++ jsonBody value ++ "</script>"
    else
      "<script type=\"application/json\">" ++ jsonBody value ++ "</script>"
-- post-conditions-end

-- impl-start
def implementation_scriptTag
    (jsonBody : String → String)
    (escapeId : String → String)
    (value optId : String) : String := Id.run do
  -- Encode the value into its safe JSON body once; this step is independent of
  -- any identifier.
  let jsonStr := jsonBody value
  -- Select the script-tag frame: with an `id` attribute when an identifier is
  -- supplied, otherwise without one.
  let mut result := ""
  if optId ≠ "" then
    result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
      ++ jsonStr ++ "</script>"
  else
    result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
  return result
-- impl-end

-- proof-start
theorem correct_scriptTag :
    ∀ (jsonBody : String → String) (escapeId : String → String)
      (value optId : String),
      problem_spec_scriptTag jsonBody escapeId value optId
        (implementation_scriptTag jsonBody escapeId value optId) := by
  intro jsonBody escapeId value optId
  unfold problem_spec_scriptTag implementation_scriptTag
  by_cases h : optId ≠ "" <;> simp only [h, if_false, Id.run] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. Project root (host layout differs from prompt's stated path); venv python. All 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec.

Attacks (each copied Solution.lean, edited ONLY impl region; axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug, always emits id frame): `bash scripts/lean_verify.sh atk_1.lean` => exit 1 (genuine proof error: rfl fails on neg branch, LHS id-frame != no-id-frame). Prepatch reproduced.
- atk_2 (swapped/negated condition optId=""): exit 1.
- atk_3 (control-flow: always no-id frame): exit 1.
- atk_4 (boundary: optId.length>1, single-char id wrongly gets no-id frame): exit 1.
- atk_5 (control-flow-effect: drops closing </script> in id branch): exit 1.
- atk_6 (ungrounded-oracle echo: escapeId value instead of escapeId optId): exit 1.
- atk_7 (gold-equivalent: assembles spec RHS byte-identically): `lean_verify.sh atk_7.lean` => exit 0, no sorry.
- positive_control (unmodified gold impl): exit 0, no sorry.

Clean-axiom check: appended `#print axioms correct_scriptTag`; atk_7 and pos_control both => 'depends on axioms: [propext]' (clean standard axiom, no sorryAx/native). No other wrong impl closed, so only atk_7 required a patch.

MANDATORY RESOLVE: atk_7 is byte-identical to gold behavior, so its faithful refined patch = gold patch. Executed run_resolve('django__django-15103', gold_patch, run_id='sbu-audit-eq-xev1d9s8-atk7') => RESOLVED=True, note='resolved'. No verify-but-not-resolve break.

refinement.md audit: legs are R (op#2 branch on optId!=""), I (literal tag text op#3/#4, return op#5), A-reference (op#1 jsonBody->real json.dumps+translate+mark_safe pipeline; escapeId piece of op#3->real format_html attribute escaping). meta.json axioms=[], conf_skip=false, deep_model_references=[json_body_encode, format_html_attr_escape]. NO A-consumed / NO kind-3 legs; no opaque/axiom declaration in Solution.lean. The two A-references correspond to genuinely-unchanged repo callees, left universally quantified and bound to real repo behavior in G-CONF — correspondence holds.

CONCLUSION: The spec is a total functional equation with zero behavioral degrees of freedom; verify=>correct holds. 6 distinct behaviorally-wrong same-spec impls all fail to verify with genuine proof errors (not sorry); the sole verifying wrong-shaped impl (atk_7) is gold-equivalent and its materialized faithful patch RESOLVES. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec problem_spec_scriptTag is a total functional equation (result = if optId != "" then <id-frame> else <no-id-frame>) over universally-quantified jsonBody/escapeId, leaving zero behavioral freedom. Every behaviorally-divergent same-spec impl fails to verify.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Wrapping a JSON-encoded value inside a `<script type="application/json">` tag for
safe inclusion in HTML output.

The value is first turned into a safe, escaped JSON body by an encoding step that
is independent of any identifier. The body is then embedded in a script tag. The
caller may optionally supply an identifier string:

  * when a non-empty identifier is supplied, the script tag carries an `id`
    attribute set to that identifier (with the identifier escaped for attribute
    use), and the JSON body follows;
  * when no identifier is supplied (the identifier is absent / empty), the script
    tag is emitted WITHOUT any `id` attribute, the JSON body following directly.

The JSON-encoding step and the attribute-escaping step are the SAME operations in
both cases; here they are taken as arbitrary functions, so the behavior pinned
below is exactly "the presence of an identifier selects whether an `id` attribute
is emitted, and the encoded body is framed by the corresponding script tag."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two unchanged steps are
-- modeled as arbitrary function parameters:
--   * `jsonBody : String → String` — turning the value into its safe, escaped
--     JSON body (the encoder + entity translation step); independent of any
--     identifier, so it is the SAME in both branches.
--   * `escapeId : String → String` — escaping the identifier for safe use inside
--     an attribute value (the same escaping the formatter applies to substituted
--     arguments).
-- Leaving both universally quantified means the spec holds for every encoder /
-- escaper; the modeled change is solely WHETHER the `id` attribute is emitted.
-- Hence the spec needs no `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: each branch's output is a literal
-- frame around the (encoded body, escaped identifier) produced by the abstract
-- steps above.
-- pure-end

-- post-conditions-start
/-- The output script-tag string is fully pinned to the inputs:

  * when the identifier is non-empty, the output is the opening `<script>` tag
    carrying an `id` attribute set to the escaped identifier, then the encoded
    JSON body, then the closing tag;
  * when the identifier is empty (no identifier supplied), the output is the
    opening `<script>` tag WITHOUT any `id` attribute, then the encoded JSON body,
    then the closing tag.

No output component is left free: the literal tag text is constant, the body portion
is pinned to the encoder applied to the value, and (in the with-identifier branch)
the attribute value is pinned to the escaper applied to the identifier. -/
def problem_spec_scriptTag
    (jsonBody : String → String)
    (escapeId : String → String)
    (value optId : String) (result : String) : Prop :=
  result =
    if optId ≠ "" then
      "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
        ++ jsonBody value ++ "</script>"
    else
      "<script type=\"application/json\">" ++ jsonBody value ++ "</script>"
-- post-conditions-end

-- impl-start
def implementation_scriptTag
    (jsonBody : String → String)
    (escapeId : String → String)
    (value optId : String) : String := Id.run do
  -- Encode the value into its safe JSON body once; this step is independent of
  -- any identifier.
  let jsonStr := jsonBody value
  -- Select the script-tag frame: with an `id` attribute when an identifier is
  -- supplied, otherwise without one.
  let mut result := ""
  if optId ≠ "" then
    result := "<script id=\"" ++ escapeId optId ++ "\" type=\"application/json\">"
      ++ jsonStr ++ "</script>"
  else
    result := "<script type=\"application/json\">" ++ jsonStr ++ "</script>"
  return result
-- impl-end

-- proof-start
theorem correct_scriptTag :
    ∀ (jsonBody : String → String) (escapeId : String → String)
      (value optId : String),
      problem_spec_scriptTag jsonBody escapeId value optId
        (implementation_scriptTag jsonBody escapeId value optId) := by
  intro jsonBody escapeId value optId
  unfold problem_spec_scriptTag implementation_scriptTag
  by_cases h : optId ≠ "" <;> simp only [h, if_false, Id.run] <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED. Project root (host layout differs from prompt's stated path); venv python. All 7 attacks confirmed same_spec=True via swebench_unified.markers.same_spec.

Attacks (each copied Solution.lean, edited ONLY impl region; axioms/pure/pre/post byte-identical):
- atk_1 (prepatch bug, always emits id frame): `bash scripts/lean_verify.sh atk_1.lean` => exit 1 (genuine proof error: rfl fails on neg branch, LHS id-frame != no-id-frame). Prepatch reproduced.
- atk_2 (swapped/negated condition optId=""): exit 1.
- atk_3 (control-flow: always no-id frame): exit 1.
- atk_4 (boundary: optId.length>1, single-char id wrongly gets no-id frame): exit 1.
- atk_5 (control-flow-effect: drops closing </script> in id branch): exit 1.
- atk_6 (ungrounded-oracle echo: escapeId value instead of escapeId optId): exit 1.
- atk_7 (gold-equivalent: assembles spec RHS byte-identically): `lean_verify.sh atk_7.lean` => exit 0, no sorry.
- positive_control (unmodified gold impl): exit 0, no sorry.

Clean-axiom check: appended `#print axioms correct_scriptTag`; atk_7 and pos_control both => 'depends on axioms: [propext]' (clean standard axiom, no sorryAx/native). No other wrong impl closed, so only atk_7 required a patch.

MANDATORY RESOLVE: atk_7 is byte-identical to gold behavior, so its faithful refined patch = gold patch. Executed run_resolve('django__django-15103', gold_patch, run_id='sbu-audit-eq-xev1d9s8-atk7') => RESOLVED=True, note='resolved'. No verify-but-not-resolve break.

refinement.md audit: legs are R (op#2 branch on optId!=""), I (literal tag text op#3/#4, return op#5), A-reference (op#1 jsonBody->real json.dumps+translate+mark_safe pipeline; escapeId piece of op#3->real format_html attribute escaping). meta.json axioms=[], conf_skip=false, deep_model_references=[json_body_encode, format_html_attr_escape]. NO A-consumed / NO kind-3 legs; no opaque/axiom declaration in Solution.lean. The two A-references correspond to genuinely-unchanged repo callees, left universally quantified and bound to real repo behavior in G-CONF — correspondence holds.

CONCLUSION: The spec is a total functional equation with zero behavioral degrees of freedom; verify=>correct holds. 6 distinct behaviorally-wrong same-spec impls all fail to verify with genuine proof errors (not sorry); the sole verifying wrong-shaped impl (atk_7) is gold-equivalent and its materialized faithful patch RESOLVES. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** django__django-15103 / json_script (django/utils/html.py:64). Verified: (1) spec region byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec (True). (2) Solution.lean compiles clean under lean_verify.sh (exit 0) and `#print axioms correct_scriptTag` = [propext] only — no sorryAx, proof is real. (3) Base-commit callee confirmed in worktree (git cat-file at dd528cb): pre-patch json_script always emits `<script id=...>`; gold patch branches on `if element_id:` truthiness.

Faithfulness analysis — model vs real json_script:
- Branch: model `optId ≠ ""` ↔ Python `if element_id:`. element_id is a str (or None); None and "" both falsy → modeled by empty String; any non-empty → truthy. Correct domain and mapping.
- Body: `jsonBody value` computed once, identical in both branches, id-independent — matches json_str = json.dumps(...).translate(...); mark_safe passes it through conditional_escape unchanged (no double-escape), so verbatim insertion is correct.
- Id escaping: `escapeId` and `jsonBody` are UNIVERSALLY QUANTIFIED. The theorem holds ∀ jsonBody escapeId, hence for the concrete real encoder and the real format_html/conditional_escape used in G-CONF. This makes the spec strictly an abstraction of branch-selection + literal framing — it cannot be 'too strong', so no concrete input can make it disagree with the real callee.
- Literal tag text and argument order (`<script id="{}" type="application/json">{}</script>` → escaped id then body; falsy → `<script type="application/json">{}</script>`) match byte-for-byte including the closing tag.

The spec is also discriminating (not vacuous): the prepatch impl (always emits the id frame) fails the else-branch clause when optId="", so the gold patch is required to satisfy it. No diverging input exists; the modeled function agrees with the real json_script on every input. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged strictly against the public problem_statement (hints_text empty). The public task already discloses the gold edit's essence: 'Make the element_id argument of json_script optional' plus the use-case of a <script> with no id inside a <template>, i.e. when no id is supplied you want a plain <script> tag without an id attribute. VERIFIED INDEPENDENTLY: (1) same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend) = True and spec_view(post) == spec_view(pre) — the spec region (axioms/pure/post-conditions) is byte-identical to the prepatch bundle, so the spec view is the solver-facing projection and pins target behavior, not a gold diff. (2) Solution.lean compiles clean via lean_verify.sh (exit 0). (3) Spec-view post-condition pins: non-empty optId -> '<script id="..." type="application/json">'++body++'</script>'; empty optId -> '<script type="application/json">'++body++'</script>' (no id attribute). This is exactly the optional-id behavior the public statement requests — spec-as-oracle describing intended behavior, which any behavioral spec must do; it is NOT gold-edit localization beyond what is public. The '<script type="application/json">' framing and the id-present branch are the function's PRE-EXISTING documented purpose (unchanged by the patch); the patch only changes WHETHER the id attribute is emitted, keyed on id presence = 'optional id', already public. (4) No leak of patched file paths (django/utils/html.py, django/template/defaultfilters.py), module paths, diff markers, reproduced gold-patch lines, or repo symbols (json_script, escapejs, format_html, element_id, DjangoJSONEncoder). Identifiers are neutral (problem_spec_scriptTag/implementation_scriptTag/jsonBody/escapeId); 'scriptTag' embeds none of the patched symbols. (5) jsonBody/escapeId are universally quantified, so the encoder pipeline and attribute-escaping internals are deliberately NOT revealed — the spec pins only branch selection + literal framing. No spec-view line discloses the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
