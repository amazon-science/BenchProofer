# P2 adversarial audit — django__django-15467

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-EQ: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — re-derived at a higher verifier cap after the original run's verifier timed out)

```diff
@@ -64,7 +64,7 @@
   Id.run do
     let mut emptyLabel := provided
     if radioBranch then
-      emptyLabel := if blank then some (provided.getD noneLabel) else none
+      emptyLabel := if blank then some noneLabel else none
     return emptyLabel
 -- impl-end
 
@@ -75,5 +75,5 @@
         (implementation_emptyLabel radioBranch blank provided) := by
   intro radioBranch blank provided
   unfold problem_spec_emptyLabel implementation_emptyLabel
-  cases radioBranch <;> rfl
+  cases radioBranch <;> cases blank <;> simp [Id.run] <;> rfl
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,8 +63,6 @@
     (radioBranch blank : Bool) (provided : Option String) : Option String :=
   Id.run do
     let mut emptyLabel := provided
-    if radioBranch then
-      emptyLabel := if blank then some (provided.getD noneLabel) else none
     return emptyLabel
 -- impl-end
 
@@ -75,5 +73,5 @@
         (implementation_emptyLabel radioBranch blank provided) := by
   intro radioBranch blank provided
   unfold problem_spec_emptyLabel implementation_emptyLabel
-  cases radioBranch <;> rfl
+  cases radioBranch <;> cases blank <;> simp [Id.run] <;> rfl
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
   Id.run do
     let mut emptyLabel := provided
     if radioBranch then
-      emptyLabel := if blank then some (provided.getD noneLabel) else none
+      emptyLabel := if blank then none else some (provided.getD noneLabel)
     return emptyLabel
 -- impl-end
 
@@ -75,5 +75,5 @@
         (implementation_emptyLabel radioBranch blank provided) := by
   intro radioBranch blank provided
   unfold problem_spec_emptyLabel implementation_emptyLabel
-  cases radioBranch <;> rfl
+  cases radioBranch <;> cases blank <;> simp [Id.run] <;> rfl
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,8 +63,7 @@
     (radioBranch blank : Bool) (provided : Option String) : Option String :=
   Id.run do
     let mut emptyLabel := provided
-    if radioBranch then
-      emptyLabel := if blank then some (provided.getD noneLabel) else none
+    emptyLabel := if blank then some (provided.getD noneLabel) else none
     return emptyLabel
 -- impl-end
 
@@ -75,5 +74,5 @@
         (implementation_emptyLabel radioBranch blank provided) := by
   intro radioBranch blank provided
   unfold problem_spec_emptyLabel implementation_emptyLabel
-  cases radioBranch <;> rfl
+  cases radioBranch <;> cases blank <;> simp [Id.run] <;> rfl
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
   Id.run do
     let mut emptyLabel := provided
     if radioBranch then
-      emptyLabel := if blank then some (provided.getD noneLabel) else none
+      emptyLabel := some noneLabel
     return emptyLabel
 -- impl-end
 
@@ -75,5 +75,5 @@
         (implementation_emptyLabel radioBranch blank provided) := by
   intro radioBranch blank provided
   unfold problem_spec_emptyLabel implementation_emptyLabel
-  cases radioBranch <;> rfl
+  cases radioBranch <;> cases blank <;> simp [Id.run] <;> rfl
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,7 @@
   Id.run do
     let mut emptyLabel := provided
     if radioBranch then
-      emptyLabel := if blank then some (provided.getD noneLabel) else none
+      emptyLabel := if blank then some (provided.getD noneLabel) else provided
     return emptyLabel
 -- impl-end
 
@@ -75,5 +75,5 @@
         (implementation_emptyLabel radioBranch blank provided) := by
   intro radioBranch blank provided
   unfold problem_spec_emptyLabel implementation_emptyLabel
-  cases radioBranch <;> rfl
+  cases radioBranch <;> cases blank <;> simp [Id.run] <;> rfl
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -64,7 +64,11 @@
   Id.run do
     let mut emptyLabel := provided
     if radioBranch then
-      emptyLabel := if blank then some (provided.getD noneLabel) else none
+      emptyLabel := if blank then
+          (match provided with
+           | some s => if s = \"\" then some noneLabel else some s
+           | none => some noneLabel)
+        else none
     return emptyLabel
 -- impl-end
 
@@ -75,5 +79,5 @@
         (implementation_emptyLabel radioBranch blank provided) := by
   intro radioBranch blank provided
   unfold problem_spec_emptyLabel implementation_emptyLabel
-  cases radioBranch <;> rfl
+  cases radioBranch <;> cases blank <;> simp [Id.run] <;> rfl
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the placeholder label for an optional single-choice relation control.

When an admin form renders a related-object field as a single-choice (radio)
control, it must decide what — if anything — to show as the "no selection"
placeholder entry at the top of the choices.

The decision depends on three things:

  * whether the single-choice control is actually being built for this field
    (a caller may already have chosen the widget, in which case the placeholder
    is left exactly as the caller supplied it);
  * whether the underlying relation is OPTIONAL (a blank/empty selection is
    permitted) or REQUIRED;
  * whether the caller explicitly supplied their own placeholder label.

The intended behavior: for the single-choice control over an OPTIONAL relation,
the placeholder is the caller's own label when they supplied one, otherwise a
standard default placeholder; for a REQUIRED relation no placeholder entry is
offered at all; and when the single-choice control is not the one being built,
the caller's supplied value is carried through untouched.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The standard
-- default placeholder is an input-independent constant string (modeled in the
-- `pure` region), and every other output is a structural combination of the
-- inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The standard default placeholder label offered for an empty selection when
the caller has not supplied one of their own. -/
def noneLabel : String := "None"
-- pure-end

-- post-conditions-start
/-- The resolved placeholder label for the single-choice relation control.

`radioBranch` is true exactly when the single-choice control is the one being
built (the caller has not already chosen the widget and the field is configured
for the single-choice presentation). `blank` is true when the relation is
optional. `provided` is the caller-supplied placeholder, if any.

Frame (directive 5): the single output is pinned in every case. When the
single-choice control is not being built the result is the caller's value
unchanged; for an optional relation it is the caller's value when present and
the default placeholder otherwise; for a required relation it is absent. -/
def problem_spec_emptyLabel
    (radioBranch blank : Bool) (provided : Option String)
    (result : Option String) : Prop :=
  result =
    (if radioBranch then
        (if blank then some (provided.getD noneLabel) else none)
      else provided)
-- post-conditions-end

-- impl-start
def implementation_emptyLabel
    (radioBranch blank : Bool) (provided : Option String) : Option String :=
  Id.run do
    let mut emptyLabel := provided
    if radioBranch then
      emptyLabel := if blank then some (provided.getD noneLabel) else none
    return emptyLabel
-- impl-end

-- proof-start
theorem correct_emptyLabel :
    ∀ (radioBranch blank : Bool) (provided : Option String),
      problem_spec_emptyLabel radioBranch blank provided
        (implementation_emptyLabel radioBranch blank provided) := by
  intro radioBranch blank provided
  unfold problem_spec_emptyLabel implementation_emptyLabel
  cases radioBranch <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_emptyLabel is a TOTAL FUNCTIONAL EQUALITY with zero slack: result = (if radioBranch then (if blank then some (provided.getD noneLabel) else none) else provided). The axioms region is EMPTY (a comment stating no callee contract is needed); refinement.md declares every leg R or I — there are NO A-legs / deep-model references to audit, so the model<->patch correspondence reduces to spec soundness. Any verifying impl must be extensionally equal to the gold function.

same_spec: all 7 attacks + positive_control = True (byte-identical spec, only impl region edited). Verified via swebench_unified.markers.same_spec on the lean backend.

positive_control.lean (gold) EXIT 0; #print axioms => 'does not depend on any axioms' (clean).
atk_8_echo.lean (pattern-match rewrite, extensionally == gold) EXIT 0; #print axioms => [propext] (clean standard axiom).
atk_1 (prepatch bug: some noneLabel, discards provided) EXIT 1 — residual goal pure(some noneLabel)=some(provided.getD noneLabel).
atk_2 (partial-domain: ignore radioBranch, always return provided) EXIT 1.
atk_3 (boundary: swap the blank true/false branches) EXIT 1.
atk_4 (control-flow-effect: drop the radioBranch guard, apply blank logic unconditionally) EXIT 1.
atk_5 (ungrounded-oracle echo: constant some noneLabel, discards provided) EXIT 1.
atk_6 (non-blank returns provided instead of none, i.e. skips the required-relation clearing) EXIT 1.
atk_7 ('or'-semantics: empty-string provided treated as absent — the problem-statement's REJECTED variant kwargs.get('empty_label') or _('None')) EXIT 1.
Result: only the gold and its extensional equal verify; ALL 7 behaviorally-distinct wrong impls FAIL to prove (as expected for a zero-slack functional-equality spec).

### PROTOCOL RESOLVE RUNS (run_resolve, official harness, docker):
  gold patch (patch.diff) => completed=True resolved=True.
  atk_8_echo faithful patch (behaviorally identical to gold => same patch) => completed=True resolved=True. This satisfies the mandate to materialize+resolve EVERY verifying clean-axiom impl; both resolve.
  prepatch reproduction: a cleanly-applying NO-OP patch leaving the buggy assignment intact => completed=True resolved=FALSE; F2P test test_radio_fields_foreignkey_formfield_overrides_empty_label FAILS, all 63 P2P PASS (patch_successfully_applied=true). Bug reproduced. (Two earlier prepatch runs returned 'no report' due to a host-contention docker.errors.ImageNotFound during post-run image cleanup — a concurrent runs-contention flake, NOT a patch-apply or test failure; the clean retry produced a valid report.json.)

CONCLUSION: Every verifying clean-axiom impl has a materialized faithful patch that RESOLVES; no verifying impl exists whose faithful patch fails to resolve. verify => correct holds. Refinement audit: no kind-3 legs; no A-legs; R/I legs deferred to G-CONF per policy. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-1: 7 attacks re-verified from the retained audit evidence (verdict.md), none breaks the spec; positive control verifies. Re-derived at a higher verifier cap after a host-load timeout had made the original run inconclusive; same attacks, same derivation.

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Resolving the placeholder label for an optional single-choice relation control.

When an admin form renders a related-object field as a single-choice (radio)
control, it must decide what — if anything — to show as the "no selection"
placeholder entry at the top of the choices.

The decision depends on three things:

  * whether the single-choice control is actually being built for this field
    (a caller may already have chosen the widget, in which case the placeholder
    is left exactly as the caller supplied it);
  * whether the underlying relation is OPTIONAL (a blank/empty selection is
    permitted) or REQUIRED;
  * whether the caller explicitly supplied their own placeholder label.

The intended behavior: for the single-choice control over an OPTIONAL relation,
the placeholder is the caller's own label when they supplied one, otherwise a
standard default placeholder; for a REQUIRED relation no placeholder entry is
offered at all; and when the single-choice control is not the one being built,
the caller's supplied value is carried through untouched.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The standard
-- default placeholder is an input-independent constant string (modeled in the
-- `pure` region), and every other output is a structural combination of the
-- inputs, so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- The standard default placeholder label offered for an empty selection when
the caller has not supplied one of their own. -/
def noneLabel : String := "None"
-- pure-end

-- post-conditions-start
/-- The resolved placeholder label for the single-choice relation control.

`radioBranch` is true exactly when the single-choice control is the one being
built (the caller has not already chosen the widget and the field is configured
for the single-choice presentation). `blank` is true when the relation is
optional. `provided` is the caller-supplied placeholder, if any.

Frame (directive 5): the single output is pinned in every case. When the
single-choice control is not being built the result is the caller's value
unchanged; for an optional relation it is the caller's value when present and
the default placeholder otherwise; for a required relation it is absent. -/
def problem_spec_emptyLabel
    (radioBranch blank : Bool) (provided : Option String)
    (result : Option String) : Prop :=
  result =
    (if radioBranch then
        (if blank then some (provided.getD noneLabel) else none)
      else provided)
-- post-conditions-end

-- impl-start
def implementation_emptyLabel
    (radioBranch blank : Bool) (provided : Option String) : Option String :=
  Id.run do
    let mut emptyLabel := provided
    if radioBranch then
      emptyLabel := if blank then some (provided.getD noneLabel) else none
    return emptyLabel
-- impl-end

-- proof-start
theorem correct_emptyLabel :
    ∀ (radioBranch blank : Bool) (provided : Option String),
      problem_spec_emptyLabel radioBranch blank provided
        (implementation_emptyLabel radioBranch blank provided) := by
  intro radioBranch blank provided
  unfold problem_spec_emptyLabel implementation_emptyLabel
  cases radioBranch <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC SHAPE: problem_spec_emptyLabel is a TOTAL FUNCTIONAL EQUALITY with zero slack: result = (if radioBranch then (if blank then some (provided.getD noneLabel) else none) else provided). The axioms region is EMPTY (a comment stating no callee contract is needed); refinement.md declares every leg R or I — there are NO A-legs / deep-model references to audit, so the model<->patch correspondence reduces to spec soundness. Any verifying impl must be extensionally equal to the gold function.

same_spec: all 7 attacks + positive_control = True (byte-identical spec, only impl region edited). Verified via swebench_unified.markers.same_spec on the lean backend.

positive_control.lean (gold) EXIT 0; #print axioms => 'does not depend on any axioms' (clean).
atk_8_echo.lean (pattern-match rewrite, extensionally == gold) EXIT 0; #print axioms => [propext] (clean standard axiom).
atk_1 (prepatch bug: some noneLabel, discards provided) EXIT 1 — residual goal pure(some noneLabel)=some(provided.getD noneLabel).
atk_2 (partial-domain: ignore radioBranch, always return provided) EXIT 1.
atk_3 (boundary: swap the blank true/false branches) EXIT 1.
atk_4 (control-flow-effect: drop the radioBranch guard, apply blank logic unconditionally) EXIT 1.
atk_5 (ungrounded-oracle echo: constant some noneLabel, discards provided) EXIT 1.
atk_6 (non-blank returns provided instead of none, i.e. skips the required-relation clearing) EXIT 1.
atk_7 ('or'-semantics: empty-string provided treated as absent — the problem-statement's REJECTED variant kwargs.get('empty_label') or _('None')) EXIT 1.
Result: only the gold and its extensional equal verify; ALL 7 behaviorally-distinct wrong impls FAIL to prove (as expected for a zero-slack functional-equality spec).

### PROTOCOL RESOLVE RUNS (run_resolve, official harness, docker):
  gold patch (patch.diff) => completed=True resolved=True.
  atk_8_echo faithful patch (behaviorally identical to gold => same patch) => completed=True resolved=True. This satisfies the mandate to materialize+resolve EVERY verifying clean-axiom impl; both resolve.
  prepatch reproduction: a cleanly-applying NO-OP patch leaving the buggy assignment intact => completed=True resolved=FALSE; F2P test test_radio_fields_foreignkey_formfield_overrides_empty_label FAILS, all 63 P2P PASS (patch_successfully_applied=true). Bug reproduced. (Two earlier prepatch runs returned 'no report' due to a host-contention docker.errors.ImageNotFound during post-run image cleanup — a concurrent runs-contention flake, NOT a patch-apply or test failure; the clean retry produced a valid report.json.)

CONCLUSION: Every verifying clean-axiom impl has a materialized faithful patch that RESOLVES; no verifying impl exists whose faithful patch fails to resolve. verify => correct holds. Refinement audit: no kind-3 legs; no A-legs; R/I legs deferred to G-CONF per policy. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on django__django-15467 lean bundle. Modeled function: the empty_label placeholder resolution in ModelAdmin.formfield_for_foreignkey (django/contrib/admin/options.py). Verified base commit e0442a628e: `kwargs["empty_label"] = _("None") if db_field.blank else None`, reachable only inside `if "widget" not in kwargs: ... elif db_field.name in self.radio_fields:`. Gold patch changes it to `kwargs.get("empty_label", _("None")) if db_field.blank else None`. Matches mapping.md and refinement.md exactly.

INTEGRITY: Solution.lean compiles clean (lean_verify exit 0); `#print axioms correct_emptyLabel` -> 'does not depend on any axioms' (real proof, no sorryAx). Spec/pure/axioms regions BYTE-IDENTICAL between Solution.lean and Solution_prepatch.lean (diff confirms); only the impl body differs and the prepatch (always emits noneLabel, dropping provided.getD) correctly FAILS to compile against the shared spec -> spec genuinely discriminates the fix.

Spec: result = if radioBranch then (if blank then some (provided.getD noneLabel) else none) else provided. Checked every case vs real code under declared mapping:
 - radioBranch=false -> carried through unchanged = provided (matches: assignment not reached).
 - radioBranch=true, blank=false -> none (matches gold `else None`).
 - radioBranch=true, blank=true, provided=some s -> some s (matches gold kwargs.get returning present value).
 - radioBranch=true, blank=true, provided=none (absent key) -> some noneLabel = some "None" (matches gold default).

BOUNDARY PROBED: Python dict.get(k, default) distinguishes absent-key (-> default "None") from key-present-with-value-None (-> None). The mapping folds both into Lean `none`. So the *concrete Python state* 'caller explicitly passed empty_label=None' (reachable via formfield_overrides) yields real output None while the spec would demand some "None". However this is not a diverging input of the MODELED function: the declared domain Option String cannot represent that distinction, the mapping explicitly and reasonably discloses the abstraction (None is not a meaningful caller-supplied label; absence modeled as none with dict.get default semantics), _("None") is the literal in default/test locale, and for EVERY representable input under the declared mapping the spec agrees with the real callee. The spec is neither too strong nor too weak vs gold on its domain, and correctly captures the fix's discriminating behavior (honoring a caller-supplied label). G-CONF oracle transliterates the same disclosed abstraction consistently. No diverging input exists within the modeled domain -> FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-3 leakage screen for django__django-15467 (lean). The public problem_statement itself already fully discloses the gold edit: it names the file (django/contrib/admin/options.py), quotes the exact pre-patch line `kwargs['empty_label'] = _('None') if db_field.blank else None`, and gives the exact post-patch replacement making a caller-supplied empty_label take precedence over the default. The spec view (Solution.lean docstring, refinement.md, mapping.md) restates precisely this behavior (radio branch × blank × provided → caller value when present else default; none for required; carried-through when branch not taken) and quotes the same pre/post Python assignment. None of it exceeds the public problem_statement — every 'leaky-looking' fact (file, changed line, precedence behavior) is verbatim public. refinement.md/mapping.md quoting the patch is permitted since the equivalent text is already in problem_statement. No spec-view line leaks gold-edit information beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
