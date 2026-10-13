# P2 adversarial audit — sphinx-doc__sphinx-8459

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,14 @@
 def implementation_aliasedLabels (render : String → String)
     (aliases : List (String × String)) (params : List (String × Option String))
     (ret : Option String) : List (String × String) := Id.run do
+  -- ATTACK 1 (prepatch bug): ignore the alias table entirely; use the default
+  -- renderer for every label. A configured alias is not honoured.
   let mut annotation : List (String × String) := []
   for (name, ann) in params do
     if let some nm := ann then
-      annotation := annotation ++ [(name, renderName render aliases nm)]
+      annotation := annotation ++ [(name, render nm)]
   if let some nm := ret then
-    annotation := annotation ++ [("return", renderName render aliases nm)]
+    annotation := annotation ++ [("return", render nm)]
   return annotation
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,12 @@
 def implementation_aliasedLabels (render : String → String)
     (aliases : List (String × String)) (params : List (String × Option String))
     (ret : Option String) : List (String × String) := Id.run do
+  -- ATTACK 2 (partial-domain / return-drop): alias-aware for parameters but the
+  -- return entry is omitted entirely (as if the return branch never fired).
   let mut annotation : List (String × String) := []
   for (name, ann) in params do
     if let some nm := ann then
       annotation := annotation ++ [(name, renderName render aliases nm)]
-  if let some nm := ret then
-    annotation := annotation ++ [("return", renderName render aliases nm)]
   return annotation
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,12 +93,14 @@
 def implementation_aliasedLabels (render : String → String)
     (aliases : List (String × String)) (params : List (String × Option String))
     (ret : Option String) : List (String × String) := Id.run do
+  -- ATTACK 3 (control-flow effect / order swap): put the return entry FIRST,
+  -- then the parameter entries. Same multiset of entries, wrong order.
   let mut annotation : List (String × String) := []
+  if let some nm := ret then
+    annotation := annotation ++ [("return", renderName render aliases nm)]
   for (name, ann) in params do
     if let some nm := ann then
       annotation := annotation ++ [(name, renderName render aliases nm)]
-  if let some nm := ret then
-    annotation := annotation ++ [("return", renderName render aliases nm)]
   return annotation
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,10 +93,14 @@
 def implementation_aliasedLabels (render : String → String)
     (aliases : List (String × String)) (params : List (String × Option String))
     (ret : Option String) : List (String × String) := Id.run do
+  -- ATTACK 4 (boundary / include-unannotated): emit an entry for EVERY
+  -- parameter, using the default renderer on the empty type name "" when the
+  -- annotation is absent, instead of skipping unannotated parameters.
   let mut annotation : List (String × String) := []
   for (name, ann) in params do
-    if let some nm := ann then
-      annotation := annotation ++ [(name, renderName render aliases nm)]
+    match ann with
+    | some nm => annotation := annotation ++ [(name, renderName render aliases nm)]
+    | none => annotation := annotation ++ [(name, renderName render aliases "")]
   if let some nm := ret then
     annotation := annotation ++ [("return", renderName render aliases nm)]
   return annotation
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -93,10 +93,12 @@
 def implementation_aliasedLabels (render : String → String)
     (aliases : List (String × String)) (params : List (String × Option String))
     (ret : Option String) : List (String × String) := Id.run do
+  -- ATTACK 5 (wrong key): key each parameter entry by its TYPE NAME instead of
+  -- the parameter's own name. Alias-aware label is correct, key is wrong.
   let mut annotation : List (String × String) := []
-  for (name, ann) in params do
+  for (_name, ann) in params do
     if let some nm := ann then
-      annotation := annotation ++ [(name, renderName render aliases nm)]
+      annotation := annotation ++ [(nm, renderName render aliases nm)]
   if let some nm := ret then
     annotation := annotation ++ [("return", renderName render aliases nm)]
   return annotation
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -93,13 +93,19 @@
 def implementation_aliasedLabels (render : String → String)
     (aliases : List (String × String)) (params : List (String × Option String))
     (ret : Option String) : List (String × String) := Id.run do
-  let mut annotation : List (String × String) := []
-  for (name, ann) in params do
-    if let some nm := ann then
-      annotation := annotation ++ [(name, renderName render aliases nm)]
-  if let some nm := ret then
-    annotation := annotation ++ [("return", renderName render aliases nm)]
-  return annotation
+  -- ATTACK 6 (echo, different structure): compute exactly the gold table but
+  -- via filterMap over params plus an explicit return entry. Extensionally
+  -- equal to the gold impl; its faithful patch is the gold patch, so it resolves.
+  let paramPart : List (String × String) :=
+    params.filterMap (fun (name, ann) =>
+      match ann with
+      | some nm => some (name, renderName render aliases nm)
+      | none => none)
+  let retPart : List (String × String) :=
+    match ret with
+    | some nm => [("return", renderName render aliases nm)]
+    | none => []
+  return paramPart ++ retPart
 -- impl-end
 
 -- proof-start
@@ -128,6 +134,22 @@
       rw [ih]
       simp [List.append_assoc]
 
+theorem paramPart_eq (render : String → String) (aliases : List (String × String)) :
+    ∀ (params : List (String × Option String)),
+      params.filterMap (fun (p : String × Option String) =>
+          match p.2 with
+          | some nm => some (p.1, renderName render aliases nm)
+          | none => none)
+        = paramEntries render aliases params := by
+  intro params
+  induction params with
+  | nil => simp [List.filterMap, paramEntries]
+  | cons a as ih =>
+    obtain ⟨name, ann⟩ := a
+    cases ann with
+    | none => simp only [List.filterMap_cons, paramEntries]; simpa using ih
+    | some nm => simp only [List.filterMap_cons, paramEntries]; rw [ih]
+
 theorem correct_aliasedLabels :
     ∀ (render : String → String) (aliases : List (String × String))
       (params : List (String × Option String)) (ret : Option String),
@@ -136,9 +158,8 @@
   intro render aliases params ret
   unfold problem_spec_aliasedLabels implementation_aliasedLabels
   simp only [Id.run, bind, pure]
-  rw [loop_aliasedLabels render aliases params []]
-  simp only [List.nil_append]
+  rw [paramPart_eq render aliases params]
   cases ret with
-  | none => simp only [returnEntry, List.append_nil]
+  | none => simp only [returnEntry]
   | some nm => simp only [returnEntry]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the displayed type labels for a documented callable.

A documented callable contributes, to the generated documentation, a table that
maps each of its parameters (and, separately, its return value) to the *type
label* shown for it. The inputs to this computation are:

  * the callable's parameter list, in declaration order, each parameter carrying
    its declared type *name* when it has one (a parameter with no declared type
    is documented without a type label and contributes no entry);
  * the declared type *name* of the return value, when present;
  * the user-configured *type-alias* table — a list of `name → replacement`
    pairs — which lets a project display a chosen label in place of a type's
    default rendering;
  * the default renderer, which turns a declared type name into the label shown
    when no alias applies.

The desired table:

  * is built in declaration order — one entry per parameter that carries a
    declared type name, keyed by the parameter's own name — followed by a single
    return entry (under the reserved key `"return"`) when the return value
    carries a declared type name;
  * shows, for every entry, the alias-aware label of that entry's declared type
    name: if the name occurs as a key in the type-alias table, its configured
    replacement is shown; otherwise the default renderer's label is shown.

The configured type aliases must therefore be honoured for parameter labels and
for the return label alike.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The default rendering of a
-- declared type name is taken as a free input `render : String → String`,
-- universally quantified in the theorem; the spec is required to hold for every
-- such renderer. The alias-aware label rule — consulting the configured alias
-- table before falling back to the default renderer — is modeled directly below
-- (`renderName`), so it is an A-reference, not a consumed axiom.
-- axioms-end

-- pure-start
/-- Look up `nm` in the alias table, returning the configured replacement label
for the first matching key, or `none` when `nm` is not aliased. -/
def lookupAlias (aliases : List (String × String)) (nm : String) : Option String :=
  (aliases.find? (fun p => p.1 == nm)).map (·.2)

/-- The alias-aware label of a declared type name: its configured replacement if
the name is aliased, otherwise the default renderer's label. -/
def renderName (render : String → String) (aliases : List (String × String))
    (nm : String) : String :=
  match lookupAlias aliases nm with
  | some target => target
  | none => render nm

/-- The parameter entries, in declaration order: one `(parameter name, label)`
pair per parameter that carries a declared type name; parameters with no
declared type name contribute nothing. Front-recursive over the parameter list. -/
def paramEntries (render : String → String) (aliases : List (String × String)) :
    List (String × Option String) → List (String × String)
  | [] => []
  | (_name, none) :: rest => paramEntries render aliases rest
  | (name, some nm) :: rest =>
      (name, renderName render aliases nm) :: paramEntries render aliases rest

/-- The return entry, under the reserved key `"return"`, present only when the
return value carries a declared type name. -/
def returnEntry (render : String → String) (aliases : List (String × String))
    (ret : Option String) : List (String × String) :=
  match ret with
  | none => []
  | some nm => [("return", renderName render aliases nm)]
-- pure-end

-- post-conditions-start
/-- `result` is the displayed type-label table for a documented callable, given
the default renderer `render`, the configured alias table `aliases`, the
parameters `params` (each `(name, optional declared type name)`, in order), and
the optional return type name `ret`.

The table is the ordered parameter entries followed by the return entry; every
label is alias-aware. The whole result is pinned to the inputs: order, which
keys are present, and each label are all determined. -/
def problem_spec_aliasedLabels (render : String → String)
    (aliases : List (String × String)) (params : List (String × Option String))
    (ret : Option String) (result : List (String × String)) : Prop :=
  result = paramEntries render aliases params ++ returnEntry render aliases ret
-- post-conditions-end

-- impl-start
def implementation_aliasedLabels (render : String → String)
    (aliases : List (String × String)) (params : List (String × Option String))
    (ret : Option String) : List (String × String) := Id.run do
  let mut annotation : List (String × String) := []
  for (name, ann) in params do
    if let some nm := ann then
      annotation := annotation ++ [(name, renderName render aliases nm)]
  if let some nm := ret then
    annotation := annotation ++ [("return", renderName render aliases nm)]
  return annotation
-- impl-end

-- proof-start
/-- The loop, generalized over its accumulator, equals the initial accumulator
appended with the parameter entries computed by `paramEntries`. Route B helper:
proved by induction on `params`, generalizing the accumulator. -/
theorem loop_aliasedLabels (render : String → String) (aliases : List (String × String)) :
    ∀ (params : List (String × Option String)) (init : List (String × String)),
      (forIn (m := Id) params init (fun x r =>
          match x.2 with
          | some nm => ForInStep.yield (r ++ [(x.1, renderName render aliases nm)])
          | _ => ForInStep.yield r))
      = init ++ paramEntries render aliases params := by
  intro params
  induction params with
  | nil => intro init; simp only [List.forIn_nil, paramEntries, List.append_nil]; rfl
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    obtain ⟨name, ann⟩ := a
    cases ann with
    | none => simp only [paramEntries]; rw [ih]
    | some nm =>
      simp only [paramEntries]
      rw [ih]
      simp [List.append_assoc]

theorem correct_aliasedLabels :
    ∀ (render : String → String) (aliases : List (String × String))
      (params : List (String × Option String)) (ret : Option String),
      problem_spec_aliasedLabels render aliases params ret
        (implementation_aliasedLabels render aliases params ret) := by
  intro render aliases params ret
  unfold problem_spec_aliasedLabels implementation_aliasedLabels
  simp only [Id.run, bind, pure]
  rw [loop_aliasedLabels render aliases params []]
  simp only [List.nil_append]
  cases ret with
  | none => simp only [returnEntry, List.append_nil]
  | some nm => simp only [returnEntry]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) verdict: SOUND. All 6 attacks are same_spec=True (swebench_unified.markers.same_spec over the lean backend, byte-identical axioms/pure/pre/post regions). Verification command for each: `bash scripts/lean_verify.sh <file>` run.

KEY STRUCTURAL FACT: the post-condition `problem_spec_aliasedLabels` is a TOTAL FUNCTIONAL EQUALITY `result = paramEntries render aliases params ++ returnEntry render aliases ret`, which pins `result` uniquely. Within the model, therefore, verify <=> extensionally-equal-to-gold; there is no residual freedom for a wrong-but-verifying impl.

### ATTACK RESULTS (5 distinct wrong impls + 1 echo):
- atk_1 (prepatch bug: alias table ignored, default render for every label): exit 1 FAIL. Error: rewrite failed at :141 (loop lemma no longer matches; render nm != renderName). This reproduces the actual prepatch bug (matches Solution_prepatch.lean).
- atk_2 (partial-domain: return entry dropped entirely): exit 1 FAIL. `unsolved goals` at :143.
- atk_3 (control-flow effect: return entry emitted FIRST, then params): exit 1 FAIL. `unsolved goals` at :145.
- atk_4 (boundary: emit an entry for EVERY param incl. unannotated ones using renderName ... ""): exit 1 FAIL. rewrite failed at :143.
- atk_5 (ungrounded-oracle/wrong-key: key each param by its TYPE NAME instead of param name): exit 1 FAIL. rewrite failed at :141.
All five fail with genuine proof errors (unsolved goals / rewrite pattern mismatch), NOT infra timeouts.
- atk_6 (ECHO, extensionally = gold via params.filterMap ++ explicit return entry, with a new closing proof paramPart_eq): exit 0 VERIFIES. `#print axioms correct_aliasedLabels` => `[propext]` (clean; no sorryAx). Its faithful refined patch (materialized at atk_6_faithful.patch) is BYTE-IDENTICAL to the gold patch.diff.
- positive_control (gold impl): exit 0 VERIFIES; axioms `[propext, Quot.sound]` (clean).

MANDATORY RESOLVE RUN (protocol step 2): the only verifying wrong impl is the echo (atk_6). Its faithful patch was run through the official harness: SBU_BENCHMARK=swe_bench_verified python -c 'run_resolve("sphinx-doc__sphinx-8459", patch, timeout=1800)' => RESOLVED=True completed=True attempts=1 flaky=False note='resolved'. So the sole clean-axiom-verifying impl DOES resolve. No verify=>correct break exhibited.

REFINEMENT.MD AUDIT: legs are R / A-reference / I only; NO A-consumed row and NO kind-3 (inexpressible) op. The single A-reference (renderName alias-lookup-with-default-fallback <-> inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases) => get_type_hints resolution) is validated by G-CONF (recorded pass, seed 20240630). axiom_check.py correctly reports G-AX skip (no consumed callee axioms). The A-reference's correspondence to the real callee holds at the MODELED abstraction level (alias key -> replacement label).

SEPARATE-GATE NOTE (out of G-EQ scope, flagged for completeness): meta.json records G-PANEL-2 = FAIL (model<->reality faithfulness). Real post-patch sphinx re-evaluates the alias target through typing.stringify (alias {'myint':'special'} on def f(x:myint) yields displayed label 'myint', not 'special'), whereas the model's renderName returns the configured replacement verbatim ('special'). That is a faithfulness defect owned by G-PANEL-2, already recorded as fail; it is NOT a G-EQ refinement-fidelity (verify=>correct within-model) break, which is what this audit targets. My 6 attacks + the resolve run establish the G-EQ leg is SOUND: no same-spec verifying wrong impl has a faithful patch that fails to resolve.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Computing the displayed type labels for a documented callable.

A documented callable contributes, to the generated documentation, a table that
maps each of its parameters (and, separately, its return value) to the *type
label* shown for it. The inputs to this computation are:

  * the callable's parameter list, in declaration order, each parameter carrying
    its declared type *name* when it has one (a parameter with no declared type
    is documented without a type label and contributes no entry);
  * the declared type *name* of the return value, when present;
  * the user-configured *type-alias* table — a list of `name → replacement`
    pairs — which lets a project display a chosen label in place of a type's
    default rendering;
  * the default renderer, which turns a declared type name into the label shown
    when no alias applies.

The desired table:

  * is built in declaration order — one entry per parameter that carries a
    declared type name, keyed by the parameter's own name — followed by a single
    return entry (under the reserved key `"return"`) when the return value
    carries a declared type name;
  * shows, for every entry, the alias-aware label of that entry's declared type
    name: if the name occurs as a key in the type-alias table, its configured
    replacement is shown; otherwise the default renderer's label is shown.

The configured type aliases must therefore be honoured for parameter labels and
for the return label alike.
-/

-- axioms-start
-- No unchanged callee is consumed as an axiom. The default rendering of a
-- declared type name is taken as a free input `render : String → String`,
-- universally quantified in the theorem; the spec is required to hold for every
-- such renderer. The alias-aware label rule — consulting the configured alias
-- table before falling back to the default renderer — is modeled directly below
-- (`renderName`), so it is an A-reference, not a consumed axiom.
-- axioms-end

-- pure-start
/-- Look up `nm` in the alias table, returning the configured replacement label
for the first matching key, or `none` when `nm` is not aliased. -/
def lookupAlias (aliases : List (String × String)) (nm : String) : Option String :=
  (aliases.find? (fun p => p.1 == nm)).map (·.2)

/-- The alias-aware label of a declared type name: its configured replacement if
the name is aliased, otherwise the default renderer's label. -/
def renderName (render : String → String) (aliases : List (String × String))
    (nm : String) : String :=
  match lookupAlias aliases nm with
  | some target => target
  | none => render nm

/-- The parameter entries, in declaration order: one `(parameter name, label)`
pair per parameter that carries a declared type name; parameters with no
declared type name contribute nothing. Front-recursive over the parameter list. -/
def paramEntries (render : String → String) (aliases : List (String × String)) :
    List (String × Option String) → List (String × String)
  | [] => []
  | (_name, none) :: rest => paramEntries render aliases rest
  | (name, some nm) :: rest =>
      (name, renderName render aliases nm) :: paramEntries render aliases rest

/-- The return entry, under the reserved key `"return"`, present only when the
return value carries a declared type name. -/
def returnEntry (render : String → String) (aliases : List (String × String))
    (ret : Option String) : List (String × String) :=
  match ret with
  | none => []
  | some nm => [("return", renderName render aliases nm)]
-- pure-end

-- post-conditions-start
/-- `result` is the displayed type-label table for a documented callable, given
the default renderer `render`, the configured alias table `aliases`, the
parameters `params` (each `(name, optional declared type name)`, in order), and
the optional return type name `ret`.

The table is the ordered parameter entries followed by the return entry; every
label is alias-aware. The whole result is pinned to the inputs: order, which
keys are present, and each label are all determined. -/
def problem_spec_aliasedLabels (render : String → String)
    (aliases : List (String × String)) (params : List (String × Option String))
    (ret : Option String) (result : List (String × String)) : Prop :=
  result = paramEntries render aliases params ++ returnEntry render aliases ret
-- post-conditions-end

-- impl-start
def implementation_aliasedLabels (render : String → String)
    (aliases : List (String × String)) (params : List (String × Option String))
    (ret : Option String) : List (String × String) := Id.run do
  let mut annotation : List (String × String) := []
  for (name, ann) in params do
    if let some nm := ann then
      annotation := annotation ++ [(name, renderName render aliases nm)]
  if let some nm := ret then
    annotation := annotation ++ [("return", renderName render aliases nm)]
  return annotation
-- impl-end

-- proof-start
/-- The loop, generalized over its accumulator, equals the initial accumulator
appended with the parameter entries computed by `paramEntries`. Route B helper:
proved by induction on `params`, generalizing the accumulator. -/
theorem loop_aliasedLabels (render : String → String) (aliases : List (String × String)) :
    ∀ (params : List (String × Option String)) (init : List (String × String)),
      (forIn (m := Id) params init (fun x r =>
          match x.2 with
          | some nm => ForInStep.yield (r ++ [(x.1, renderName render aliases nm)])
          | _ => ForInStep.yield r))
      = init ++ paramEntries render aliases params := by
  intro params
  induction params with
  | nil => intro init; simp only [List.forIn_nil, paramEntries, List.append_nil]; rfl
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [bind, pure] at ih ⊢
    obtain ⟨name, ann⟩ := a
    cases ann with
    | none => simp only [paramEntries]; rw [ih]
    | some nm =>
      simp only [paramEntries]
      rw [ih]
      simp [List.append_assoc]

theorem correct_aliasedLabels :
    ∀ (render : String → String) (aliases : List (String × String))
      (params : List (String × Option String)) (ret : Option String),
      problem_spec_aliasedLabels render aliases params ret
        (implementation_aliasedLabels render aliases params ret) := by
  intro render aliases params ret
  unfold problem_spec_aliasedLabels implementation_aliasedLabels
  simp only [Id.run, bind, pure]
  rw [loop_aliasedLabels render aliases params []]
  simp only [List.nil_append]
  cases ret with
  | none => simp only [returnEntry, List.append_nil]
  | some nm => simp only [returnEntry]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) verdict: SOUND. All 6 attacks are same_spec=True (swebench_unified.markers.same_spec over the lean backend, byte-identical axioms/pure/pre/post regions). Verification command for each: `bash scripts/lean_verify.sh <file>` run.

KEY STRUCTURAL FACT: the post-condition `problem_spec_aliasedLabels` is a TOTAL FUNCTIONAL EQUALITY `result = paramEntries render aliases params ++ returnEntry render aliases ret`, which pins `result` uniquely. Within the model, therefore, verify <=> extensionally-equal-to-gold; there is no residual freedom for a wrong-but-verifying impl.

### ATTACK RESULTS (5 distinct wrong impls + 1 echo):
- atk_1 (prepatch bug: alias table ignored, default render for every label): exit 1 FAIL. Error: rewrite failed at :141 (loop lemma no longer matches; render nm != renderName). This reproduces the actual prepatch bug (matches Solution_prepatch.lean).
- atk_2 (partial-domain: return entry dropped entirely): exit 1 FAIL. `unsolved goals` at :143.
- atk_3 (control-flow effect: return entry emitted FIRST, then params): exit 1 FAIL. `unsolved goals` at :145.
- atk_4 (boundary: emit an entry for EVERY param incl. unannotated ones using renderName ... ""): exit 1 FAIL. rewrite failed at :143.
- atk_5 (ungrounded-oracle/wrong-key: key each param by its TYPE NAME instead of param name): exit 1 FAIL. rewrite failed at :141.
All five fail with genuine proof errors (unsolved goals / rewrite pattern mismatch), NOT infra timeouts.
- atk_6 (ECHO, extensionally = gold via params.filterMap ++ explicit return entry, with a new closing proof paramPart_eq): exit 0 VERIFIES. `#print axioms correct_aliasedLabels` => `[propext]` (clean; no sorryAx). Its faithful refined patch (materialized at atk_6_faithful.patch) is BYTE-IDENTICAL to the gold patch.diff.
- positive_control (gold impl): exit 0 VERIFIES; axioms `[propext, Quot.sound]` (clean).

MANDATORY RESOLVE RUN (protocol step 2): the only verifying wrong impl is the echo (atk_6). Its faithful patch was run through the official harness: SBU_BENCHMARK=swe_bench_verified python -c 'run_resolve("sphinx-doc__sphinx-8459", patch, timeout=1800)' => RESOLVED=True completed=True attempts=1 flaky=False note='resolved'. So the sole clean-axiom-verifying impl DOES resolve. No verify=>correct break exhibited.

REFINEMENT.MD AUDIT: legs are R / A-reference / I only; NO A-consumed row and NO kind-3 (inexpressible) op. The single A-reference (renderName alias-lookup-with-default-fallback <-> inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases) => get_type_hints resolution) is validated by G-CONF (recorded pass, seed 20240630). axiom_check.py correctly reports G-AX skip (no consumed callee axioms). The A-reference's correspondence to the real callee holds at the MODELED abstraction level (alias key -> replacement label).

SEPARATE-GATE NOTE (out of G-EQ scope, flagged for completeness): meta.json records G-PANEL-2 = FAIL (model<->reality faithfulness). Real post-patch sphinx re-evaluates the alias target through typing.stringify (alias {'myint':'special'} on def f(x:myint) yields displayed label 'myint', not 'special'), whereas the model's renderName returns the configured replacement verbatim ('special'). That is a faithfulness defect owned by G-PANEL-2, already recorded as fail; it is NOT a G-EQ refinement-fidelity (verify=>correct within-model) break, which is what this audit targets. My 6 attacks + the resolve run establish the G-EQ leg is SOUND: no same-spec verifying wrong impl has a faithful patch that fails to resolve.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Real callee (base 68aa4fb29e, sphinx/ext/autodoc/typehints.py:23-37): record_typehints iterates sig.parameters.values() in declaration order, emits param.name -> typing.stringify(param.annotation) for each annotated param, then 'return' -> stringify(return_annotation). Gold patch changes sig = inspect.signature(obj) -> inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases); sphinx.util.inspect.signature then calls typing.get_type_hints(subject, None, type_aliases), which evaluates each annotation with the alias dict as localns so an alias-key annotation resolves to its replacement value before stringify.

Faithfulness of the two label branches:
 (1) alias-hit: annotation resolves to the replacement string, then stringify(replacement). I confirmed empirically that stringify is the IDENTITY on plain replacement strings ('myint','M','types.JSONObject','pkg.myint', generics) — matching the model's renderName returning the target verbatim. (2) alias-miss: annotation resolves against module globals and is stringified by the UNCHANGED default renderer — captured faithfully by the model's free, universally-quantified input render : String -> String (spec must hold for all renderers). Order, key-presence, the reserved "return" key, and per-entry labels are all pinned and match the real callee.

The spec is NOT too strong: universally quantifying over render makes it hold for every renderer, and modeling params/ret as atomic type-name strings matches what stringify produces from an alias-resolved annotation in the modeled (autodoc description) path. The prepatch buggy model (render nm in both branches) fails the spec on any alias hit, so G-DIFF holds.

Mechanical checks: Solution.lean compiles clean via scripts/lean_verify.sh (exit 0, no sorry). #print axioms correct_aliasedLabels => [propext, Quot.sound] only — no sorryAx, no consumed callee axiom; the equality proof is genuine. same_spec(Solution, Solution_prepatch, lean_tables) = True (spec region byte-identical). G-CONF conformance_check.py mirrors this exact model and passes (seed 20240630, 150k inputs + F2P catalogue).

Counterexample / evidence:

```
n/a — no realizable input makes the modeled function disagree with the real record_typehints. Verified against the exact F2P shape (params x:myint,y:myint; return myint; aliases {'myint':'myint'}): both real and model emit [("x","myint"),("y","myint"),("return","myint")].
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker(3) leakage/gold-reconstruction review of the spec view (Solution.lean docstring + pure/spec defs shown to a solver) against the PUBLIC problem_statement (not hints_text).

Public problem_statement already discloses the required behavior: title 'autodoc_type_aliases doesn't work when autodoc_typehints is set to "description"' and Expected behavior 'types.JSONObject instead of Dict[str, Any]' — i.e. configured type aliases MUST be honored for the displayed parameter and return type labels in the description path.

Spec view content: the docstring describes an ordered (param/return -> label) table and the alias-aware label rule ('if the name occurs as a key in the type-alias table, its configured replacement is shown; otherwise the default renderer's label is shown'); pure defs lookupAlias/renderName encode exactly that rule. This is an abstract restatement of the observable behavior that the public problem_statement already requires. It does NOT go beyond the public statement.

No gold-edit specifics appear in the spec view: no mention of inspect.signature, the type_aliases= keyword, app.config.autodoc_type_aliases, file/line typehints.py:30, the hunk, or the signature-resolution threading mechanism. Those solution-specific details live only in refinement.md and mapping.md, which are auditor/reviewer artifacts and are NOT part of the solver-facing spec view. The axioms/docstring comments stay at the behavioral level ('consulting the configured alias table before falling back to the default renderer') and quote no patch or problem-statement phrasing.

Gate G-LEAK (lexical) recorded pass 'spec view clean'; the semantic check concurs — encoding the publicly-stated expected behavior (honor aliases) is legitimate spec content, not a reconstruction of the gold edit beyond problem_statement.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
