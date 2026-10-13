# P2 adversarial audit — django__django-15467

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a fully-pinned functional postcondition `ensures out = resolvedLabel allowsBlank override` with an empty precondition region, where `resolvedLabel allowsBlank override = if allowsBlank then override.getD defaultLabel else none` and `defaultLabel = some "None"`. Every behavioral deviation from the gold semantics leaves an unsolvable `ensures` goal, so no verifying wrong impl exists — the discriminating input `allowsBlank=true ∧ override=some v` (v≠some "None") forces `out=v`, refuting any impl that discards the caller override.
```

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
 -- (No axiomatized callees in the modeled slice. The decision modeled here is a
@@ -75,11 +75,8 @@
   ensures out = resolvedLabel allowsBlank override
   do
     -- impl-start
-    -- When an empty selection is allowed, keep a caller-supplied placeholder
-    -- and fall back to the standard placeholder only when none was supplied;
-    -- otherwise show no placeholder.
     if allowsBlank then
-      let e : Option String := override.getD defaultLabel
+      let e : Option String := defaultLabel
       return e
     else
       return none
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
 -- (No axiomatized callees in the modeled slice. The decision modeled here is a
@@ -75,14 +75,7 @@
   ensures out = resolvedLabel allowsBlank override
   do
     -- impl-start
-    -- When an empty selection is allowed, keep a caller-supplied placeholder
-    -- and fall back to the standard placeholder only when none was supplied;
-    -- otherwise show no placeholder.
-    if allowsBlank then
-      let e : Option String := override.getD defaultLabel
-      return e
-    else
-      return none
+    return override.getD defaultLabel
     -- impl-end
 
 prove_correct emptyLabelFor by
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
 -- (No axiomatized callees in the modeled slice. The decision modeled here is a
@@ -75,14 +75,10 @@
   ensures out = resolvedLabel allowsBlank override
   do
     -- impl-start
-    -- When an empty selection is allowed, keep a caller-supplied placeholder
-    -- and fall back to the standard placeholder only when none was supplied;
-    -- otherwise show no placeholder.
     if allowsBlank then
-      let e : Option String := override.getD defaultLabel
-      return e
+      return none
     else
-      return none
+      return override.getD defaultLabel
     -- impl-end
 
 prove_correct emptyLabelFor by
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
 -- (No axiomatized callees in the modeled slice. The decision modeled here is a
@@ -75,14 +75,8 @@
   ensures out = resolvedLabel allowsBlank override
   do
     -- impl-start
-    -- When an empty selection is allowed, keep a caller-supplied placeholder
-    -- and fall back to the standard placeholder only when none was supplied;
-    -- otherwise show no placeholder.
-    if allowsBlank then
-      let e : Option String := override.getD defaultLabel
-      return e
-    else
-      return none
+    let e : Option String := defaultLabel
+    return e
     -- impl-end
 
 prove_correct emptyLabelFor by
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
 -- (No axiomatized callees in the modeled slice. The decision modeled here is a
@@ -75,12 +75,8 @@
   ensures out = resolvedLabel allowsBlank override
   do
     -- impl-start
-    -- When an empty selection is allowed, keep a caller-supplied placeholder
-    -- and fall back to the standard placeholder only when none was supplied;
-    -- otherwise show no placeholder.
     if allowsBlank then
-      let e : Option String := override.getD defaultLabel
-      return e
+      return override.getD none
     else
       return none
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
 -- (No axiomatized callees in the modeled slice. The decision modeled here is a
@@ -75,12 +75,8 @@
   ensures out = resolvedLabel allowsBlank override
   do
     -- impl-start
-    -- When an empty selection is allowed, keep a caller-supplied placeholder
-    -- and fall back to the standard placeholder only when none was supplied;
-    -- otherwise show no placeholder.
     if allowsBlank then
-      let e : Option String := override.getD defaultLabel
-      return e
+      return some "None"
     else
       return none
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
 -- (No axiomatized callees in the modeled slice. The decision modeled here is a
@@ -75,12 +75,10 @@
   ensures out = resolvedLabel allowsBlank override
   do
     -- impl-start
-    -- When an empty selection is allowed, keep a caller-supplied placeholder
-    -- and fall back to the standard placeholder only when none was supplied;
-    -- otherwise show no placeholder.
     if allowsBlank then
-      let e : Option String := override.getD defaultLabel
-      return e
+      match override with
+      | some v => return v
+      | none   => return none
     else
       return none
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees in the modeled slice. The decision modeled here is a
--  closed function of its inputs: a flag saying whether the related field allows
--  an empty selection, and a caller-provided override that is either absent or
--  carries an explicit value. The only outside-provided value is the module's standard
--  fallback placeholder label; it is modeled DEEPLY as the literal placeholder
--  string `defaultLabel` (`pure` region) and validated against the real
--  localization callee that produces it by axiom_check.py (G-AX) — an
--  A-reference, not a consumed axiom. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The fallback placeholder shown for the empty selection when the related field
   allows one and the caller offered no placeholder of its own. Modeled as the
   literal placeholder text the module's standard localization helper returns for
   this position (a deep model — an A-reference validated == the real helper by
   axiom_check.py / G-AX, mapping.md §3.1). A present-with-value option carrier
   `some s` means a placeholder string `s` is shown for the empty selection;
   `none` means no empty selection is offered. -/
@[grind] def defaultLabel : Option String := some "None"

/- The placeholder resolved for the empty selection.

   `allowsBlank` says the related field allows an empty selection. `override`
   models what the caller already provided for the placeholder, with
   key-presence semantics: `none` = the caller provided nothing (the key is
   absent), `some v` = the caller provided the value `v` (possibly `v = none`,
   i.e. an explicit "no placeholder").

   Desired behaviour: when an empty selection is allowed, a caller-provided
   placeholder is kept as-is and ONLY when the caller provided nothing does the
   standard fallback placeholder apply; when no empty selection is allowed, no
   placeholder is shown regardless of what the caller offered. `Option.getD`
   captures the keep-caller-value-else-fallback choice exactly (it mirrors the
   "lookup with default" the resolution performs). -/
@[grind] def resolvedLabel (allowsBlank : Bool) (override : Option (Option String)) :
    Option String :=
  if allowsBlank then override.getD defaultLabel else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolving the placeholder for the empty selection of a single-choice related
   field rendered as mutually-exclusive options.

   `allowsBlank` reports whether the related field allows an empty selection.
   `override` is the placeholder the caller already supplied, carried with
   key-presence semantics (`none` = nothing supplied; `some v` = supplied the
   value `v`, where `v = none` is an explicit "no placeholder"). The result is
   the placeholder ultimately shown for the empty selection.

   Desired behaviour: a caller-supplied placeholder takes precedence and is
   preserved whenever an empty selection is allowed; the standard fallback
   placeholder applies only when an empty selection is allowed and the caller
   supplied nothing; and when no empty selection is allowed, no placeholder is
   shown at all.

   Both inputs are read-only (neither `mut`): the routine inspects the flag and
   the caller's override and produces the resolved placeholder, mutating neither
   (directive 5). The resolution is pinned exactly by `resolvedLabel`. -/
method emptyLabelFor (allowsBlank : Bool) (override : Option (Option String))
    return (out : Option String)
  ensures out = resolvedLabel allowsBlank override
  do
    -- impl-start
    -- When an empty selection is allowed, keep a caller-supplied placeholder
    -- and fall back to the standard placeholder only when none was supplied;
    -- otherwise show no placeholder.
    if allowsBlank then
      let e : Option String := override.getD defaultLabel
      return e
    else
      return none
    -- impl-end

prove_correct emptyLabelFor by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Backend velvet (Lean, v4.24.0). same_spec confirmed True for pos + all 7 attacks (axioms/pure/pre/post byte-identical; edited impl region only). Verify command: `bash scripts/lean_verify.sh <file>` run, launched concurrently ≤4 at a time (2 batches).

RESULTS (exit codes): pos.lean=0 (VERIFIES, positive control). All 7 wrong impls FAIL to verify (exit 1) with genuine `unsolved goals` on `case ensures_1: out = resolvedLabel allowsBlank override` — NOT syntax errors:
 - atk_1 (prepatch bug / control-flow-effect): blank branch always installs `defaultLabel`, discards override → exit 1 (line 85). REPRODUCES the prepatch bug; residual goal on allowsBlank=true∧override=some v matches refinement.md §A/§D.
 - atk_2 (partial-domain): drops allowsBlank, always `override.getD defaultLabel` → exit 1 (fails non-blank branch: must be none).
 - atk_3 (boundary / branch-swap): swaps the allowsBlank branches → exit 1 (both goals residual).
 - atk_4 (control-flow-effect): unconditional `return defaultLabel` → exit 1.
 - atk_5 (wrong-default): `override.getD none` instead of `defaultLabel` → exit 1 (fails when override=none: must be some "None").
 - atk_6 (ungrounded-oracle echo): blank branch hardcodes `some "None"`, ignoring override → exit 1 (echoes defaultLabel value but discards caller value).
 - atk_7 (dropped-fallback): match override; none→return none instead of defaultLabel → exit 1 (residual goal exactly at override=none).

Because NO wrong impl verifies, step-2 of the protocol (materialize faithful patch + run_resolve) has no trigger — that path only fires on a verify∧¬resolve gap, which does not exist here. No resolve run was needed or possible for a verifying-wrong-impl (there are none).

REFINEMENT.MD AUDIT: legs A1–A5 are all R / A-reference / I; no kind-3. A1(R bool↔Bool), A2(R key-presence Option(Option String)), A3(I conditional), A4(R dict.get↔Option.getD + A-reference defaultLabel↔gettext("None")), A5(R Option String↔str|None). §B: no consumed axioms (single external value is an unchanged callee's value, deep-modeled). §C: no inexpressible-changed-op. The sole A-reference correspondence (defaultLabel=some "None" ↔ gettext("None") under the default/no-catalog test locale) is standard Django behavior and is G-AX's remit (axiom_check.py); the nested Option(Option String) carrier is load-bearing and correctly preserves the three-way absent/present-None/present-value distinction the gold `kwargs.get` observes. Correspondence holds.

VERDICT: SOUND — ≥5 (7) distinct diverse attacks run, positive control verifies, prepatch bug reproduced, no verifying wrong impl, refinement legs clean.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a fully-pinned functional postcondition `ensures out = resolvedLabel allowsBlank override` with an empty precondition region, where `resolvedLabel allowsBlank override = if allowsBlank then override.getD defaultLabel else none` and `defaultLabel = some "None"`. Every behavioral deviation from the gold semantics leaves an unsolvable `ensures` goal, so no verifying wrong impl exists — the discriminating input `allowsBlank=true ∧ override=some v` (v≠some "None") forces `out=v`, refuting any impl that discards the caller override.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees in the modeled slice. The decision modeled here is a
--  closed function of its inputs: a flag saying whether the related field allows
--  an empty selection, and a caller-provided override that is either absent or
--  carries an explicit value. The only outside-provided value is the module's standard
--  fallback placeholder label; it is modeled DEEPLY as the literal placeholder
--  string `defaultLabel` (`pure` region) and validated against the real
--  localization callee that produces it by axiom_check.py (G-AX) — an
--  A-reference, not a consumed axiom. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- The fallback placeholder shown for the empty selection when the related field
   allows one and the caller offered no placeholder of its own. Modeled as the
   literal placeholder text the module's standard localization helper returns for
   this position (a deep model — an A-reference validated == the real helper by
   axiom_check.py / G-AX, mapping.md §3.1). A present-with-value option carrier
   `some s` means a placeholder string `s` is shown for the empty selection;
   `none` means no empty selection is offered. -/
@[grind] def defaultLabel : Option String := some "None"

/- The placeholder resolved for the empty selection.

   `allowsBlank` says the related field allows an empty selection. `override`
   models what the caller already provided for the placeholder, with
   key-presence semantics: `none` = the caller provided nothing (the key is
   absent), `some v` = the caller provided the value `v` (possibly `v = none`,
   i.e. an explicit "no placeholder").

   Desired behaviour: when an empty selection is allowed, a caller-provided
   placeholder is kept as-is and ONLY when the caller provided nothing does the
   standard fallback placeholder apply; when no empty selection is allowed, no
   placeholder is shown regardless of what the caller offered. `Option.getD`
   captures the keep-caller-value-else-fallback choice exactly (it mirrors the
   "lookup with default" the resolution performs). -/
@[grind] def resolvedLabel (allowsBlank : Bool) (override : Option (Option String)) :
    Option String :=
  if allowsBlank then override.getD defaultLabel else none
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolving the placeholder for the empty selection of a single-choice related
   field rendered as mutually-exclusive options.

   `allowsBlank` reports whether the related field allows an empty selection.
   `override` is the placeholder the caller already supplied, carried with
   key-presence semantics (`none` = nothing supplied; `some v` = supplied the
   value `v`, where `v = none` is an explicit "no placeholder"). The result is
   the placeholder ultimately shown for the empty selection.

   Desired behaviour: a caller-supplied placeholder takes precedence and is
   preserved whenever an empty selection is allowed; the standard fallback
   placeholder applies only when an empty selection is allowed and the caller
   supplied nothing; and when no empty selection is allowed, no placeholder is
   shown at all.

   Both inputs are read-only (neither `mut`): the routine inspects the flag and
   the caller's override and produces the resolved placeholder, mutating neither
   (directive 5). The resolution is pinned exactly by `resolvedLabel`. -/
method emptyLabelFor (allowsBlank : Bool) (override : Option (Option String))
    return (out : Option String)
  ensures out = resolvedLabel allowsBlank override
  do
    -- impl-start
    -- When an empty selection is allowed, keep a caller-supplied placeholder
    -- and fall back to the standard placeholder only when none was supplied;
    -- otherwise show no placeholder.
    if allowsBlank then
      let e : Option String := override.getD defaultLabel
      return e
    else
      return none
    -- impl-end

prove_correct emptyLabelFor by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

 Backend velvet (Lean, v4.24.0). same_spec confirmed True for pos + all 7 attacks (axioms/pure/pre/post byte-identical; edited impl region only). Verify command: `bash scripts/lean_verify.sh <file>` run, launched concurrently ≤4 at a time (2 batches).

RESULTS (exit codes): pos.lean=0 (VERIFIES, positive control). All 7 wrong impls FAIL to verify (exit 1) with genuine `unsolved goals` on `case ensures_1: out = resolvedLabel allowsBlank override` — NOT syntax errors:
 - atk_1 (prepatch bug / control-flow-effect): blank branch always installs `defaultLabel`, discards override → exit 1 (line 85). REPRODUCES the prepatch bug; residual goal on allowsBlank=true∧override=some v matches refinement.md §A/§D.
 - atk_2 (partial-domain): drops allowsBlank, always `override.getD defaultLabel` → exit 1 (fails non-blank branch: must be none).
 - atk_3 (boundary / branch-swap): swaps the allowsBlank branches → exit 1 (both goals residual).
 - atk_4 (control-flow-effect): unconditional `return defaultLabel` → exit 1.
 - atk_5 (wrong-default): `override.getD none` instead of `defaultLabel` → exit 1 (fails when override=none: must be some "None").
 - atk_6 (ungrounded-oracle echo): blank branch hardcodes `some "None"`, ignoring override → exit 1 (echoes defaultLabel value but discards caller value).
 - atk_7 (dropped-fallback): match override; none→return none instead of defaultLabel → exit 1 (residual goal exactly at override=none).

Because NO wrong impl verifies, step-2 of the protocol (materialize faithful patch + run_resolve) has no trigger — that path only fires on a verify∧¬resolve gap, which does not exist here. No resolve run was needed or possible for a verifying-wrong-impl (there are none).

REFINEMENT.MD AUDIT: legs A1–A5 are all R / A-reference / I; no kind-3. A1(R bool↔Bool), A2(R key-presence Option(Option String)), A3(I conditional), A4(R dict.get↔Option.getD + A-reference defaultLabel↔gettext("None")), A5(R Option String↔str|None). §B: no consumed axioms (single external value is an unchanged callee's value, deep-modeled). §C: no inexpressible-changed-op. The sole A-reference correspondence (defaultLabel=some "None" ↔ gettext("None") under the default/no-catalog test locale) is standard Django behavior and is G-AX's remit (axiom_check.py); the nested Option(Option String) carrier is load-bearing and correctly preserves the three-way absent/present-None/present-value distinction the gold `kwargs.get` observes. Correspondence holds.

VERDICT: SOUND — ≥5 (7) distinct diverse attacks run, positive control verifies, prepatch bug reproduced, no verifying wrong impl, refinement legs clean.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-15467 (velvet). RESULT: FAITHFUL — no diverging input found; the modeled function agrees with the real repo callee across its whole abstraction domain.

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True. The consumer spec view projects to the signature + `ensures out = resolvedLabel allowsBlank override` + pure defs `defaultLabel = some "None"` and `resolvedLabel allowsBlank override = if allowsBlank then override.getD defaultLabel else none`; impl/proof elided. Prepatch shares the identical frozen spec. Solution.lean verifies clean via lean_verify.sh (exit 0).

Modeled slice = the empty_label resolution in ModelAdmin.formfield_for_foreignkey (options.py:272), gold patch: `kwargs["empty_label"] = kwargs.get("empty_label", _("None")) if db_field.blank else None`.

Abstraction: Bool ↔ db_field.blank; Option(Option String) ↔ kwargs empty_label entry with 3-way key-presence (none=absent, some(some s)=present str, some none=present Python None); Option.getD ↔ dict.get(key,default). All load-bearing and correct — the nested option preserves the absent/present-None distinction that kwargs.get observes.

Empirical faithfulness test: built a clean git worktree at base_commit e0442a62, applied the gold patch, and drove the REAL patched formfield_for_foreignkey end-to-end via formfield_for_dbfield (so the observable ff.empty_label INCLUDES the downstream ModelChoiceField.__init__ rule `RadioSelect ∧ not blank ⇒ empty_label=None`). Compared vs the transliterated shadow over 100,044 inputs: both routes (formfield_overrides AND explicit kwargs) × blank/non-blank fields × {absent, None, empty-string, 'None', unicode, arbitrary fuzz}. ZERO disagreements.

Manual domain coverage confirms no divergence anywhere: (a) non-blank branch — real slice assigns None for any override and ModelChoiceField also forces None for RadioSelect∧not-blank, matching model `none` on all inputs; (b) blank branch — kwargs.get(key, _("None")) = keep-caller-else-fallback = override.getD defaultLabel exactly, including present-None kept as None. A-reference sound: real gettext('None')=='None' under default locale == defaultLabel.

The spec is neither too strong nor drifting from real repo behavior. No diverging input exists on the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Leakage judged against the SOLVER-VISIBLE problem_statement only (not hints_text). This instance's problem_statement is maximally disclosing: it names the exact file (django/contrib/admin/options.py), the pre-patch line (kwargs['empty_label'] = _('None') if db_field.blank else None) AND the fix (kwargs['empty_label'] = (kwargs.get('empty_label') or _('None')) if db_field.blank else None), plus the full behavioral rationale (empty_label from kwargs takes precedence over _('None')). The entire gold edit is already public.

Spec view (velvet, generated via markers.spec_view): impl/proof bodies elided; exposes axioms/pure/pre/post + method signature and `ensures out = resolvedLabel allowsBlank override`, where resolvedLabel = if allowsBlank then override.getD defaultLabel else none. This discriminating content ('keep caller placeholder when blank allowed, else default; none when not allowed') is exactly what the problem_statement already discloses.

Leak checks (independent + mechanical G-LEAK screen()): (1) no diff markers, no patched file path/module path in view; (2) spec-view identifiers (emptyLabelFor, resolvedLabel, defaultLabel, allowsBlank, override) are abstract modeling names, none echo the patched repo symbol formfield_for_foreignkey; (3) comments narrate desired behavior abstractly, matching the public statement's framing, no bug/fix narration tokens; (4) markers.same_spec(Solution, Solution_prepatch)=True (spec region frozen). leakage.screen() returns passed=True, zero hard failures, zero warnings. The spec view reveals nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
