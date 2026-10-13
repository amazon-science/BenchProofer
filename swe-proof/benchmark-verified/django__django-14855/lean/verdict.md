# P2 adversarial audit — django__django-14855

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec `problem_spec_getAdminUrl` is fully functional and universally quantified over ALL resolveUrl/formatLink, pinning result = (match resolveUrl ("admin:"++appLabel++"_"++modelName++"_change") arg (some siteName) with | some url => formatLink url remoteObjStr | none => remoteObjStr). This extensionally forces the implementation: any same-spec deviation fails to close. No verifying wrong impl exists, so no verify⇏correct gap.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,7 @@
     (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
   -- Assemble the route name for the related model's change view.
   let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
-  -- Resolve the URL, telling the resolver the currently-effective deployment
-  -- identifier; frame the outcome as a link, or fall back to plain display text.
-  match resolveUrl urlName arg (some siteName) with
+  match resolveUrl urlName arg none with
   | some url => return formatLink url remoteObjStr
   | none => return remoteObjStr
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,9 +80,7 @@
     (formatLink : String → String → String)
     (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
   -- Assemble the route name for the related model's change view.
-  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
-  -- Resolve the URL, telling the resolver the currently-effective deployment
-  -- identifier; frame the outcome as a link, or fall back to plain display text.
+  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName
   match resolveUrl urlName arg (some siteName) with
   | some url => return formatLink url remoteObjStr
   | none => return remoteObjStr
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,11 +81,9 @@
     (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
   -- Assemble the route name for the related model's change view.
   let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
-  -- Resolve the URL, telling the resolver the currently-effective deployment
-  -- identifier; frame the outcome as a link, or fall back to plain display text.
   match resolveUrl urlName arg (some siteName) with
-  | some url => return formatLink url remoteObjStr
-  | none => return remoteObjStr
+  | some _ => return remoteObjStr
+  | none => return formatLink urlName remoteObjStr
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,8 +81,9 @@
     (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
   -- Assemble the route name for the related model's change view.
   let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
-  -- Resolve the URL, telling the resolver the currently-effective deployment
-  -- identifier; frame the outcome as a link, or fall back to plain display text.
+  if siteName == "" then
+    return remoteObjStr
+  else
   match resolveUrl urlName arg (some siteName) with
   | some url => return formatLink url remoteObjStr
   | none => return remoteObjStr
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,9 +81,7 @@
     (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
   -- Assemble the route name for the related model's change view.
   let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
-  -- Resolve the URL, telling the resolver the currently-effective deployment
-  -- identifier; frame the outcome as a link, or fall back to plain display text.
-  match resolveUrl urlName arg (some siteName) with
+  match resolveUrl urlName "" (some siteName) with
   | some url => return formatLink url remoteObjStr
   | none => return remoteObjStr
 -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,10 +81,8 @@
     (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
   -- Assemble the route name for the related model's change view.
   let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
-  -- Resolve the URL, telling the resolver the currently-effective deployment
-  -- identifier; frame the outcome as a link, or fall back to plain display text.
   match resolveUrl urlName arg (some siteName) with
-  | some url => return formatLink url remoteObjStr
+  | some _ => return formatLink urlName remoteObjStr
   | none => return remoteObjStr
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -81,11 +81,8 @@
     (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
   -- Assemble the route name for the related model's change view.
   let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
-  -- Resolve the URL, telling the resolver the currently-effective deployment
-  -- identifier; frame the outcome as a link, or fall back to plain display text.
-  match resolveUrl urlName arg (some siteName) with
-  | some url => return formatLink url remoteObjStr
-  | none => return remoteObjStr
+  let _ := resolveUrl urlName arg (some siteName)
+  return remoteObjStr
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing the display markup for a reference to a related record shown on an
administrative detail page.

The reference is rendered by asking a URL-resolution step to turn a target route
name and the target record's identifier into a concrete URL:

  * the route name is assembled from the related model's grouping label and its
    model name;
  * the target record's identifier is supplied in already-encoded form;
  * crucially, the resolution is told WHICH administrative deployment is currently
    in effect, so that a non-default deployment yields URLs under its own prefix
    rather than the default one.

If the resolution step yields a URL, the result is a link-formatting step applied
to that URL and the record's display text. If the resolution step cannot produce a
URL, the result is just the record's display text.

The URL-resolution step and the link-formatting step are the SAME operations
regardless of context; here each is taken as an arbitrary function of its inputs,
so the behavior pinned below is exactly "the currently-effective deployment
identifier reaches the URL-resolution step, and its outcome is framed as a link or
falls back to plain display text."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two downstream operations
-- are modeled as arbitrary function parameters:
--   * `resolveUrl : String → String → Option String → Option String` — the
--     URL-resolution step, a function of the route name, the encoded identifier,
--     and the optionally-supplied currently-effective deployment identifier;
--     `none` result models "no route could be produced".
--   * `formatLink : String → String → String` — the link-formatting step, a
--     function of a URL and the record's display text.
-- The modeled change is solely WHICH deployment identifier is handed to the
-- resolution step (the currently-effective one rather than none), so the result is
-- pinned for every possible resolver and link formatter. Hence the spec needs no
-- `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the route name is a plain
-- concatenation of the grouping label and model name, and the result is the
-- link-or-fallback around the resolution step.
-- pure-end

-- post-conditions-start
/-- The display markup is fully pinned to the inputs:

  * the route name is exactly `"admin:" ++ appLabel ++ "_" ++ modelName ++
    "_change"`;
  * the resolution step is invoked with that route name, the encoded identifier,
    and the currently-effective deployment identifier (`some siteName` — NOT a
    missing identifier);
  * if it yields a URL, the result is the link-formatting step applied to that URL
    and the record's display text; otherwise the result is exactly the record's
    display text.

No output component is left free: the route name and the supplied deployment
identifier are pinned to their inputs, and each branch's result is pinned to the
corresponding step. -/
def problem_spec_getAdminUrl
    (resolveUrl : String → String → Option String → Option String)
    (formatLink : String → String → String)
    (appLabel modelName arg siteName remoteObjStr : String)
    (result : String) : Prop :=
  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
  result =
    match resolveUrl urlName arg (some siteName) with
    | some url => formatLink url remoteObjStr
    | none => remoteObjStr
-- post-conditions-end

-- impl-start
def implementation_getAdminUrl
    (resolveUrl : String → String → Option String → Option String)
    (formatLink : String → String → String)
    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
  -- Assemble the route name for the related model's change view.
  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
  -- Resolve the URL, telling the resolver the currently-effective deployment
  -- identifier; frame the outcome as a link, or fall back to plain display text.
  match resolveUrl urlName arg (some siteName) with
  | some url => return formatLink url remoteObjStr
  | none => return remoteObjStr
-- impl-end

-- proof-start
theorem correct_getAdminUrl :
    ∀ (resolveUrl : String → String → Option String → Option String)
      (formatLink : String → String → String)
      (appLabel modelName arg siteName remoteObjStr : String),
      problem_spec_getAdminUrl resolveUrl formatLink appLabel modelName arg siteName
          remoteObjStr
        (implementation_getAdminUrl resolveUrl formatLink appLabel modelName arg
          siteName remoteObjStr) := by
  intro resolveUrl formatLink appLabel modelName arg siteName remoteObjStr
  unfold problem_spec_getAdminUrl implementation_getAdminUrl
  simp only [Id.run]
  cases resolveUrl ("admin:" ++ appLabel ++ "_" ++ modelName ++ "_change") arg (some siteName) <;>
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

env python. same_spec=True for ALL 7 attacks (axioms/pure/pre/post byte-identical; only impl region edited). Attacks (all DISTINCT wrong impls): atk_1 prepatch bug — passes `none` instead of `some siteName` (no current_app) [prepatch_reproduced]; atk_2 wrong route name (drops `_change`); atk_3 control-flow swap (some=>plain text, none=>formatLink); atk_4 partial-domain guard (empty siteName => fallback); atk_5 boundary — drops encoded id (passes "" to resolver); atk_6 ungrounded-oracle echo (formatLink urlName instead of resolved url); atk_7 control-flow-effect (ignores resolver result, always fallback).

Verification (concurrent, ≤4 background jobs; cmd `bash scripts/lean_verify.sh <file>`):
  positive_control.lean EXIT=0 (verifies, no sorry)
  atk_1..7 ALL EXIT=1 — every proof fails at `rfl` (line ~101-105), impls compile but are not extensionally equal to the pinned spec. Error uniformly: "Tactic `rfl` failed: The left-hand side". Because the spec is fully functional, no alternative proof can close any of these; NO wrong impl verified => NO patch to materialize/resolve.

Positive-control axioms: appended `#print axioms correct_getAdminUrl` and re-verified => 'correct_getAdminUrl' does not depend on any axioms (clean; genuinely axiom-free, consistent with refinement.md axioms=[]).

refinement.md audit: 4 legs — Op1 I (route "admin:"++...++"_change" ↔ `'admin:%s_%s_change' %`), Op2 A-reference (`reverse`, real callee bound in G-CONF, carries the FIXED `current_app=some siteName` token — the bug), Op3 A-reference (`format_html`, real callee), Op4 R (`Option.none ↔ NoReverseMatch`, try/except refined to Option match). No A-consumed row (both callees universally quantified; proof consumes no property; axioms=[]). No kind-3 (inexpressible) leg. A-reference↔real-callee correspondences (reverse, format_html) hold per mapping.md symbol binding. conf_skip=false is justified (genuine R/I + fixed-token arg).

Verdict SOUND: ≥7 (>5) distinct same-spec wrong impls attacked, none closed a clean-axiom proof, so no faithful patch could break verify⇒correct. Spec is tight (extensional functional pin).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The spec `problem_spec_getAdminUrl` is fully functional and universally quantified over ALL resolveUrl/formatLink, pinning result = (match resolveUrl ("admin:"++appLabel++"_"++modelName++"_change") arg (some siteName) with | some url => formatLink url remoteObjStr | none => remoteObjStr). This extensionally forces the implementation: any same-spec deviation fails to close. No verifying wrong impl exists, so no verify⇏correct gap.
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

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing the display markup for a reference to a related record shown on an
administrative detail page.

The reference is rendered by asking a URL-resolution step to turn a target route
name and the target record's identifier into a concrete URL:

  * the route name is assembled from the related model's grouping label and its
    model name;
  * the target record's identifier is supplied in already-encoded form;
  * crucially, the resolution is told WHICH administrative deployment is currently
    in effect, so that a non-default deployment yields URLs under its own prefix
    rather than the default one.

If the resolution step yields a URL, the result is a link-formatting step applied
to that URL and the record's display text. If the resolution step cannot produce a
URL, the result is just the record's display text.

The URL-resolution step and the link-formatting step are the SAME operations
regardless of context; here each is taken as an arbitrary function of its inputs,
so the behavior pinned below is exactly "the currently-effective deployment
identifier reaches the URL-resolution step, and its outcome is framed as a link or
falls back to plain display text."
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Two downstream operations
-- are modeled as arbitrary function parameters:
--   * `resolveUrl : String → String → Option String → Option String` — the
--     URL-resolution step, a function of the route name, the encoded identifier,
--     and the optionally-supplied currently-effective deployment identifier;
--     `none` result models "no route could be produced".
--   * `formatLink : String → String → String` — the link-formatting step, a
--     function of a URL and the record's display text.
-- The modeled change is solely WHICH deployment identifier is handed to the
-- resolution step (the currently-effective one rather than none), so the result is
-- pinned for every possible resolver and link formatter. Hence the spec needs no
-- `opaque`/`axiom` callee contract.
-- axioms-end

-- pure-start
-- No standalone functional helper is required: the route name is a plain
-- concatenation of the grouping label and model name, and the result is the
-- link-or-fallback around the resolution step.
-- pure-end

-- post-conditions-start
/-- The display markup is fully pinned to the inputs:

  * the route name is exactly `"admin:" ++ appLabel ++ "_" ++ modelName ++
    "_change"`;
  * the resolution step is invoked with that route name, the encoded identifier,
    and the currently-effective deployment identifier (`some siteName` — NOT a
    missing identifier);
  * if it yields a URL, the result is the link-formatting step applied to that URL
    and the record's display text; otherwise the result is exactly the record's
    display text.

No output component is left free: the route name and the supplied deployment
identifier are pinned to their inputs, and each branch's result is pinned to the
corresponding step. -/
def problem_spec_getAdminUrl
    (resolveUrl : String → String → Option String → Option String)
    (formatLink : String → String → String)
    (appLabel modelName arg siteName remoteObjStr : String)
    (result : String) : Prop :=
  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
  result =
    match resolveUrl urlName arg (some siteName) with
    | some url => formatLink url remoteObjStr
    | none => remoteObjStr
-- post-conditions-end

-- impl-start
def implementation_getAdminUrl
    (resolveUrl : String → String → Option String → Option String)
    (formatLink : String → String → String)
    (appLabel modelName arg siteName remoteObjStr : String) : String := Id.run do
  -- Assemble the route name for the related model's change view.
  let urlName := "admin:" ++ appLabel ++ "_" ++ modelName ++ "_change"
  -- Resolve the URL, telling the resolver the currently-effective deployment
  -- identifier; frame the outcome as a link, or fall back to plain display text.
  match resolveUrl urlName arg (some siteName) with
  | some url => return formatLink url remoteObjStr
  | none => return remoteObjStr
-- impl-end

-- proof-start
theorem correct_getAdminUrl :
    ∀ (resolveUrl : String → String → Option String → Option String)
      (formatLink : String → String → String)
      (appLabel modelName arg siteName remoteObjStr : String),
      problem_spec_getAdminUrl resolveUrl formatLink appLabel modelName arg siteName
          remoteObjStr
        (implementation_getAdminUrl resolveUrl formatLink appLabel modelName arg
          siteName remoteObjStr) := by
  intro resolveUrl formatLink appLabel modelName arg siteName remoteObjStr
  unfold problem_spec_getAdminUrl implementation_getAdminUrl
  simp only [Id.run]
  cases resolveUrl ("admin:" ++ appLabel ++ "_" ++ modelName ++ "_change") arg (some siteName) <;>
    rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

env python. same_spec=True for ALL 7 attacks (axioms/pure/pre/post byte-identical; only impl region edited). Attacks (all DISTINCT wrong impls): atk_1 prepatch bug — passes `none` instead of `some siteName` (no current_app) [prepatch_reproduced]; atk_2 wrong route name (drops `_change`); atk_3 control-flow swap (some=>plain text, none=>formatLink); atk_4 partial-domain guard (empty siteName => fallback); atk_5 boundary — drops encoded id (passes "" to resolver); atk_6 ungrounded-oracle echo (formatLink urlName instead of resolved url); atk_7 control-flow-effect (ignores resolver result, always fallback).

Verification (concurrent, ≤4 background jobs; cmd `bash scripts/lean_verify.sh <file>`):
  positive_control.lean EXIT=0 (verifies, no sorry)
  atk_1..7 ALL EXIT=1 — every proof fails at `rfl` (line ~101-105), impls compile but are not extensionally equal to the pinned spec. Error uniformly: "Tactic `rfl` failed: The left-hand side". Because the spec is fully functional, no alternative proof can close any of these; NO wrong impl verified => NO patch to materialize/resolve.

Positive-control axioms: appended `#print axioms correct_getAdminUrl` and re-verified => 'correct_getAdminUrl' does not depend on any axioms (clean; genuinely axiom-free, consistent with refinement.md axioms=[]).

refinement.md audit: 4 legs — Op1 I (route "admin:"++...++"_change" ↔ `'admin:%s_%s_change' %`), Op2 A-reference (`reverse`, real callee bound in G-CONF, carries the FIXED `current_app=some siteName` token — the bug), Op3 A-reference (`format_html`, real callee), Op4 R (`Option.none ↔ NoReverseMatch`, try/except refined to Option match). No A-consumed row (both callees universally quantified; proof consumes no property; axioms=[]). No kind-3 (inexpressible) leg. A-reference↔real-callee correspondences (reverse, format_html) hold per mapping.md symbol binding. conf_skip=false is justified (genuine R/I + fixed-token arg).

Verdict SOUND: ≥7 (>5) distinct same-spec wrong impls attacked, none closed a clean-axiom proof, so no faithful patch could break verify⇒correct. Spec is tight (extensional functional pin).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack found no divergence between the modeled `problem_spec_getAdminUrl`/`implementation_getAdminUrl` and the real post-patch `AdminReadonlyField.get_admin_url` (django/contrib/admin/helpers.py:205-215, base_commit 475cffd1). Checks: (1) Solution.lean compiles via lean_verify.sh, exit 0; (2) `#print axioms correct_getAdminUrl` => 'does not depend on any axioms' (no sorryAx, genuine proof); (3) same_spec(Solution, Solution_prepatch, LeanBackend.language)=True, spec region byte-identical, only impl differs (some siteName vs none) => real discriminating power over the bug; (4) worktree at base_commit confirmed pre-patch `reverse(url_name, args=[quote(remote_obj.pk)])`. Modeling is faithful: route name '%s_%s' format == '++' concat (identical strings); reverse(..., current_app=admin_site.name) == resolveUrl ... (some siteName) — admin_site.name is always a real str in Django (never None), so the unconditional current_app= keyword the patch adds is faithfully modeled as `some siteName`; NoReverseMatch folds to none; format_html('<a href="{}">{}</a>', url, remote_obj) == formatLink url remoteObjStr (format_html force_str's remote_obj, equaling str(remote_obj)=remoteObjStr); str(remote_obj) fallback == remoteObjStr. resolveUrl/formatLink universally quantified, so the sole pinned observable is that the current-app identifier reaches the resolver (exactly the fix). G-CONF binds both to the REAL reverse/format_html over >=1e5 fuzzed inputs, catching any residual drift. No diverging input exists; spec is neither too strong nor drifted.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit (adding current_app=self.model_admin.admin_site.name to reverse()) is disclosed VERBATIM in the public problem_statement — the reporter wrote out the exact replacement code. Nothing in the spec view can leak beyond that already-public baseline. The Solution.lean spec region (docstring + problem_spec_getAdminUrl) is in fact strictly more abstract than problem_statement: it pins only that the resolution step receives `some siteName` (currently-effective deployment identifier) rather than `none`, using generic parameters resolveUrl/formatLink with no Django symbols, no `current_app`, no `admin_site.name`. This behavioral fact is exactly what problem_statement already describes concretely. Confirmed the spec region is byte-identical between Solution_prepatch.lean and Solution.lean; the only diff is impl-region (resolveUrl … none -> some siteName) plus impl comments — the discriminating token lives in the impl, not the spec view. No leaking line exists.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
