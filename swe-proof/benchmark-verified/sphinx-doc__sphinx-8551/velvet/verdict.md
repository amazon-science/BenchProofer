# P2 adversarial audit — sphinx-doc__sphinx-8551

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verifies, so there is no verify⇏⋇correct gap and no faithful patch to materialize/resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,22 +106,15 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
     let kindAdj :=
       if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
         ['o','b','j']
       else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
       { domain := domain, kind := kindAdj, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
     let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
-    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
+    let withScope := withSpec
     let result :=
       match target with
       | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,22 +106,18 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
     let kindAdj :=
       if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
         ['o','b','j']
       else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
       { domain := domain, kind := kindAdj, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
     let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
-    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
+    let withScope :=
+      match target with
+      | [] => withSpec
+      | _  => { withSpec with scopeModule := curModule, scopeClass := curClass }
     let result :=
       match target with
       | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,22 +106,15 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
     let kindAdj :=
       if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
         ['o','b','j']
       else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
       { domain := domain, kind := kindAdj, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
     let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
-    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
+    let withScope := { withSpec with scopeModule := curClass, scopeClass := curModule }
     let result :=
       match target with
       | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,28 +106,16 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
     let kindAdj :=
       if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
         ['o','b','j']
       else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
       { domain := domain, kind := kindAdj, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
     let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
     let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
-    let result :=
-      match target with
-      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
-                     else withScope
-      | []        => withScope
-    return result
+    return withScope
     -- impl-end
 
 prove_correct buildCrossRef by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,22 +106,15 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
     let kindAdj :=
       if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
         ['o','b','j']
       else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
       { domain := domain, kind := kindAdj, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
     let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
-    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
+    let withScope := { withSpec with scopeModule := curModule }
     let result :=
       match target with
       | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,22 +106,11 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
-    let kindAdj :=
-      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
-        ['o','b','j']
-      else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
-      { domain := domain, kind := kindAdj, target := target,
+      { domain := domain, kind := kind, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
     let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
     let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
     let result :=
       match target with
       | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,22 +106,14 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
     let kindAdj :=
       if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
         ['o','b','j']
       else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
       { domain := domain, kind := kindAdj, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
-    let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
-    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
+    let withScope := { base with scopeModule := curModule, scopeClass := curClass }
     let result :=
       match target with
       | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -106,25 +106,18 @@
   ensures out.target = normalizeTarget target
   do
     -- impl-start
-    -- `None` is not a type: a class-kind reference to the literal target `None`
-    -- is built as an object-kind reference instead (unchanged behaviour)
     let kindAdj :=
       if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
         ['o','b','j']
       else kind
-    -- the base reference built for this target, carrying the raw target
     let base : CrossRef :=
       { domain := domain, kind := kindAdj, target := target,
         preferSpecific := false, scopeModule := none, scopeClass := none }
-    -- ask resolution to prefer the most specific match
     let withSpec := { base with preferSpecific := true }
-    -- record the documentation scope in effect onto the reference, so a
-    -- same-scope target can be preferred over equally-named targets elsewhere
     let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
-    -- normalize an explicit-prefix target (leading scope/short-name marker)
     let result :=
       match target with
-      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
+      | c :: rest => if c = '.' then { withScope with target := rest }
                      else withScope
       | []        => withScope
     return result
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under spec is a pure data-flow that builds a
   cross-reference descriptor from its inputs: the documentation scope in effect
   (the current module name and current class name, each possibly unset) is
   recorded onto the descriptor alongside the resolution target. Every observable
   is computed from the inputs; nothing is borrowed from an oracle. There is no
   module-level `axiom` and no `:|` callee stub (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The documentation scope in effect at the point a cross-reference is built: the
   name of the current module and the name of the current class, each `none` when
   unset. These are the read-only inputs whose faithful propagation is the
   behaviour at issue. -/
abbrev ScopeName := Option (List Char)

/- A cross-reference descriptor for an inline type specifier. It records the
   resolution domain, the reference kind, the resolution target, a flag asking
   resolution to prefer the most specific match, and — the behaviour at issue —
   the documentation scope (current module / current class) under which the
   reference was written. A descriptor that fails to record the scope forces a
   later resolution step to search every (sub)module, producing the spurious
   ambiguity the issue reports. -/
structure CrossRef where
  domain         : List Char
  kind           : List Char
  target         : List Char
  preferSpecific : Bool
  scopeModule    : ScopeName
  scopeClass     : ScopeName
  deriving DecidableEq, Repr

/- Normalize a resolution target written with an explicit leading marker: a
   leading `.` or `~` selects an alternate display/lookup mode and is stripped
   from the stored target. Any other target is stored verbatim. (Unchanged
   behaviour, modeled concretely.) -/
def normalizeTarget (target : List Char) : List Char :=
  match target with
  | c :: rest => if c = '.' ∨ c = '~' then rest else target
  | []        => target

/- Normalize the reference kind against the target: `None` is not a type, so a
   class-kind reference whose (raw) target is exactly `None` is built as an
   object-kind reference instead. Any other kind/target combination keeps the
   kind verbatim. (Unchanged pre-existing behaviour of the concrete inline-type
   reference builders, inside the modeled boundary; modeled concretely.) -/
def normalizeKind (kind target : List Char) : List Char :=
  if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
    ['o','b','j']
  else kind

/- The cross-reference descriptor for an inline type specifier, modeled deeply.
   The kind and target are normalized and the prefer-specific flag is set (all
   unchanged behaviour); crucially, the descriptor carries the current
   documentation scope so a same-scope target can be preferred during
   resolution. Pinned by the method `ensures`; validated against the real
   reference builder by G-CONF. -/
def scopedRef (curModule curClass : ScopeName) (domain kind target : List Char) :
    CrossRef :=
  { domain         := domain
    kind           := normalizeKind kind target
    target         := normalizeTarget target
    preferSpecific := true
    scopeModule    := curModule
    scopeClass     := curClass }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the cross-reference descriptor for an inline type specifier written
   inside a documentation entry. Desired behaviour: the descriptor must record
   the documentation scope in effect where it was written — the current module
   and the current class — so that an unqualified target resolves against the
   current scope (and its parent scopes) rather than matching the same short name
   in every (sub)module. Failing to record the scope is exactly the defect that
   yields false "more than one target" ambiguity for an unqualified name.

   `curModule`, `curClass`, `domain`, `kind`, `target` are read-only: the
   method builds and returns a fresh descriptor and never mutates its inputs.

   The kind is required non-empty: every caller inside the modeled slice
   supplies a concrete reference kind, and a kindless request takes a plain
   display-only rendering path that builds no cross-reference descriptor at
   all — that path is outside the modeled behaviour (mapping.md §1). -/
method buildCrossRef (curModule : ScopeName) (curClass : ScopeName) (domain : List Char)
    (kind : List Char) (target : List Char)
    return (out : CrossRef)
  require kind ≠ []
  ensures out = scopedRef curModule curClass domain kind target
  ensures out.scopeModule = curModule
  ensures out.scopeClass = curClass
  ensures out.preferSpecific = true
  ensures out.kind = normalizeKind kind target
  ensures out.target = normalizeTarget target
  do
    -- impl-start
    -- `None` is not a type: a class-kind reference to the literal target `None`
    -- is built as an object-kind reference instead (unchanged behaviour)
    let kindAdj :=
      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
        ['o','b','j']
      else kind
    -- the base reference built for this target, carrying the raw target
    let base : CrossRef :=
      { domain := domain, kind := kindAdj, target := target,
        preferSpecific := false, scopeModule := none, scopeClass := none }
    -- ask resolution to prefer the most specific match
    let withSpec := { base with preferSpecific := true }
    -- record the documentation scope in effect onto the reference, so a
    -- same-scope target can be preferred over equally-named targets elsewhere
    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
    -- normalize an explicit-prefix target (leading scope/short-name marker)
    let result :=
      match target with
      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
                     else withScope
      | []        => withScope
    return result
    -- impl-end

prove_correct buildCrossRef by
  loom_solve <;>
    (simp only [scopedRef, normalizeKind, normalizeTarget]
     cases target with
      | nil => simp
      | cons c rest => by_cases h : c = '.' ∨ c = '~' <;> simp [h])
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: buildCrossRef's postcondition `ensures out = scopedRef curModule curClass domain kind target` is a COMPLETE functional specification — it pins the returned CrossRef to exactly the deep-model value on every input; the four supplementary ensures (scopeModule/scopeClass/preferSpecific/kind/target) are redundant projections of the same equality. This leaves no room for a same-spec deviation.

Protocol executed:
- same_spec confirmed True for all 8 attacks + positive control via swebench_unified.markers.same_spec (velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.
- Verification: `bash scripts/lean_verify.sh <file>`.
  pos.lean -> exit 0 (verifies, no sorry). atk_1..8 -> exit 1, all with genuine `unsolved goals` errors at the prove_correct block (postcondition equality unprovable), NOT syntax/import failures. Ran concurrently in batches of ≤4.

Attacks (>=5 required, 8 supplied, distinct classes):
  atk_1 control-flow-effect = PREPATCH BUG: `let withScope := withSpec` (scope left none). Impl code byte-identical to Solution_prepatch.lean (only comments differ). Fails ensures out.scopeModule=curModule ∧ out.scopeClass=curClass. => prepatch reproduced.
  atk_2 partial-domain: stamp scope only when target nonempty. Fails on target=[].
  atk_3 boundary: swap scopeModule:=curClass, scopeClass:=curModule.
  atk_4 control-flow-effect: skip normalizeTarget (never strip leading .'/'~').
  atk_5 ungrounded-oracle echo: stamp scopeModule only, leave scopeClass none.
  atk_6 skip normalizeKind (kind stored verbatim; diverges on kind=class,target=None).
  atk_7 boundary flag: drop preferSpecific:=true (stays false).
  atk_8 boundary: strip leading '.' only, not '~'.

All 8 fail to verify => NO verifying wrong impl exists => `patches` is empty; no run_resolve needed (nothing to materialize). This is the correct outcome for a tight (full-equality) postcondition, not a rubber-stamp: the falsification search was real and exhaustive across partial-domain / boundary / control-flow-effect / ungrounded-echo classes and the prepatch bug.

Refinement audit (refinement.md): legs A0,A1,A2,A3,A4 and companion R4 are all tagged R and/or I; NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op). Consistent with mapping.md §3 (Callee provenance = None): super().make_xref is modeled concretely in scopedRef's base record and exercised for real by G-CONF; py-domain process_field_xref is a documented no-op. No module-level axiom, no `:|` stub (meta.json axioms:[]), so there is no A-leg callee-correspondence to forge. The single deep model scopedRef IS the postcondition, machine-pinned by prove_correct, so R/I fidelity is mechanically enforced (plus G-CONF over 1e5 inputs). Total-correctness semantics (loom termination total) correctly forbids a divergent same-spec impl.

Verdict: SOUND. verify => correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. No same-spec wrong implementation verifies, so there is no verify⇏⋇correct gap and no faithful patch to materialize/resolve.
```

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

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour under spec is a pure data-flow that builds a
   cross-reference descriptor from its inputs: the documentation scope in effect
   (the current module name and current class name, each possibly unset) is
   recorded onto the descriptor alongside the resolution target. Every observable
   is computed from the inputs; nothing is borrowed from an oracle. There is no
   module-level `axiom` and no `:|` callee stub (mapping.md §3). -/
-- axioms-end

-- pure-start
/- The documentation scope in effect at the point a cross-reference is built: the
   name of the current module and the name of the current class, each `none` when
   unset. These are the read-only inputs whose faithful propagation is the
   behaviour at issue. -/
abbrev ScopeName := Option (List Char)

/- A cross-reference descriptor for an inline type specifier. It records the
   resolution domain, the reference kind, the resolution target, a flag asking
   resolution to prefer the most specific match, and — the behaviour at issue —
   the documentation scope (current module / current class) under which the
   reference was written. A descriptor that fails to record the scope forces a
   later resolution step to search every (sub)module, producing the spurious
   ambiguity the issue reports. -/
structure CrossRef where
  domain         : List Char
  kind           : List Char
  target         : List Char
  preferSpecific : Bool
  scopeModule    : ScopeName
  scopeClass     : ScopeName
  deriving DecidableEq, Repr

/- Normalize a resolution target written with an explicit leading marker: a
   leading `.` or `~` selects an alternate display/lookup mode and is stripped
   from the stored target. Any other target is stored verbatim. (Unchanged
   behaviour, modeled concretely.) -/
def normalizeTarget (target : List Char) : List Char :=
  match target with
  | c :: rest => if c = '.' ∨ c = '~' then rest else target
  | []        => target

/- Normalize the reference kind against the target: `None` is not a type, so a
   class-kind reference whose (raw) target is exactly `None` is built as an
   object-kind reference instead. Any other kind/target combination keeps the
   kind verbatim. (Unchanged pre-existing behaviour of the concrete inline-type
   reference builders, inside the modeled boundary; modeled concretely.) -/
def normalizeKind (kind target : List Char) : List Char :=
  if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
    ['o','b','j']
  else kind

/- The cross-reference descriptor for an inline type specifier, modeled deeply.
   The kind and target are normalized and the prefer-specific flag is set (all
   unchanged behaviour); crucially, the descriptor carries the current
   documentation scope so a same-scope target can be preferred during
   resolution. Pinned by the method `ensures`; validated against the real
   reference builder by G-CONF. -/
def scopedRef (curModule curClass : ScopeName) (domain kind target : List Char) :
    CrossRef :=
  { domain         := domain
    kind           := normalizeKind kind target
    target         := normalizeTarget target
    preferSpecific := true
    scopeModule    := curModule
    scopeClass     := curClass }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the cross-reference descriptor for an inline type specifier written
   inside a documentation entry. Desired behaviour: the descriptor must record
   the documentation scope in effect where it was written — the current module
   and the current class — so that an unqualified target resolves against the
   current scope (and its parent scopes) rather than matching the same short name
   in every (sub)module. Failing to record the scope is exactly the defect that
   yields false "more than one target" ambiguity for an unqualified name.

   `curModule`, `curClass`, `domain`, `kind`, `target` are read-only: the
   method builds and returns a fresh descriptor and never mutates its inputs.

   The kind is required non-empty: every caller inside the modeled slice
   supplies a concrete reference kind, and a kindless request takes a plain
   display-only rendering path that builds no cross-reference descriptor at
   all — that path is outside the modeled behaviour (mapping.md §1). -/
method buildCrossRef (curModule : ScopeName) (curClass : ScopeName) (domain : List Char)
    (kind : List Char) (target : List Char)
    return (out : CrossRef)
  require kind ≠ []
  ensures out = scopedRef curModule curClass domain kind target
  ensures out.scopeModule = curModule
  ensures out.scopeClass = curClass
  ensures out.preferSpecific = true
  ensures out.kind = normalizeKind kind target
  ensures out.target = normalizeTarget target
  do
    -- impl-start
    -- `None` is not a type: a class-kind reference to the literal target `None`
    -- is built as an object-kind reference instead (unchanged behaviour)
    let kindAdj :=
      if kind = ['c','l','a','s','s'] ∧ target = ['N','o','n','e'] then
        ['o','b','j']
      else kind
    -- the base reference built for this target, carrying the raw target
    let base : CrossRef :=
      { domain := domain, kind := kindAdj, target := target,
        preferSpecific := false, scopeModule := none, scopeClass := none }
    -- ask resolution to prefer the most specific match
    let withSpec := { base with preferSpecific := true }
    -- record the documentation scope in effect onto the reference, so a
    -- same-scope target can be preferred over equally-named targets elsewhere
    let withScope := { withSpec with scopeModule := curModule, scopeClass := curClass }
    -- normalize an explicit-prefix target (leading scope/short-name marker)
    let result :=
      match target with
      | c :: rest => if c = '.' ∨ c = '~' then { withScope with target := rest }
                     else withScope
      | []        => withScope
    return result
    -- impl-end

prove_correct buildCrossRef by
  loom_solve <;>
    (simp only [scopedRef, normalizeKind, normalizeTarget]
     cases target with
      | nil => simp
      | cons c rest => by_cases h : c = '.' ∨ c = '~' <;> simp [h])
```

Prepatch bug re-encoded as an attack: `True`.

Spec shape: buildCrossRef's postcondition `ensures out = scopedRef curModule curClass domain kind target` is a COMPLETE functional specification — it pins the returned CrossRef to exactly the deep-model value on every input; the four supplementary ensures (scopeModule/scopeClass/preferSpecific/kind/target) are redundant projections of the same equality. This leaves no room for a same-spec deviation.

Protocol executed:
- same_spec confirmed True for all 8 attacks + positive control via swebench_unified.markers.same_spec (velvet). Only the impl region was edited; axioms/pure/pre/post byte-identical.
- Verification: `bash scripts/lean_verify.sh <file>`.
  pos.lean -> exit 0 (verifies, no sorry). atk_1..8 -> exit 1, all with genuine `unsolved goals` errors at the prove_correct block (postcondition equality unprovable), NOT syntax/import failures. Ran concurrently in batches of ≤4.

Attacks (>=5 required, 8 supplied, distinct classes):
  atk_1 control-flow-effect = PREPATCH BUG: `let withScope := withSpec` (scope left none). Impl code byte-identical to Solution_prepatch.lean (only comments differ). Fails ensures out.scopeModule=curModule ∧ out.scopeClass=curClass. => prepatch reproduced.
  atk_2 partial-domain: stamp scope only when target nonempty. Fails on target=[].
  atk_3 boundary: swap scopeModule:=curClass, scopeClass:=curModule.
  atk_4 control-flow-effect: skip normalizeTarget (never strip leading .'/'~').
  atk_5 ungrounded-oracle echo: stamp scopeModule only, leave scopeClass none.
  atk_6 skip normalizeKind (kind stored verbatim; diverges on kind=class,target=None).
  atk_7 boundary flag: drop preferSpecific:=true (stays false).
  atk_8 boundary: strip leading '.' only, not '~'.

All 8 fail to verify => NO verifying wrong impl exists => `patches` is empty; no run_resolve needed (nothing to materialize). This is the correct outcome for a tight (full-equality) postcondition, not a rubber-stamp: the falsification search was real and exhaustive across partial-domain / boundary / control-flow-effect / ungrounded-echo classes and the prepatch bug.

Refinement audit (refinement.md): legs A0,A1,A2,A3,A4 and companion R4 are all tagged R and/or I; NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op). Consistent with mapping.md §3 (Callee provenance = None): super().make_xref is modeled concretely in scopedRef's base record and exercised for real by G-CONF; py-domain process_field_xref is a documented no-op. No module-level axiom, no `:|` stub (meta.json axioms:[]), so there is no A-leg callee-correspondence to forge. The single deep model scopedRef IS the postcondition, machine-pinned by prove_correct, so R/I fidelity is mechanically enforced (plus G-CONF over 1e5 inputs). Total-correctness semantics (loom termination total) correctly forbids a divergent same-spec impl.

Verdict: SOUND. verify => correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec = True over the velvet backend). The two twins share one spec; the prepatch differs only in the impl region (withScope := withSpec, scope left none), which correctly fails the scope-recording ensures — confirming the spec is discriminating (not too weak on the fix).

Methodology: (1) same_spec check via markers with the velvet LanguageTables. Ran the pinned G-CONF conformance_check.py against the REAL patched repo (at the patched make_xref, docutils 0.16 venv): 'G-CONF OK ... 100660 inputs (seed=8551), 0 disagreements.' Independent adversarial differential: 84,000 inputs over all three concrete builders (PyField/PyTypedField/PyGroupedField) x extended target/kind/domain carriers, comparing the transliterated model observable tuple (refdomain,reftype,reftarget,refspecific,py:module,py:class) to the real make_xref node attributes.

Result: PyField and PyTypedField = 0 divergences (model matches real callee exactly on the entire reachable info-field path, including the class/None->obj rewrite, leading .'/'~' stripping, and scope stamping). All 112 divergences isolated to PyGroupedField on kind='class'&target='None' only — the normalizeKind rewrite is baked into the single shared model but PyGroupedField lacks that override. mapping.md §1 anticipates exactly this and shows the case is unreachable: PyGroupedField is registered solely with rolename='exc' (python.py:361), is_typed=False so the typerolename='class' path can't reach it, and for 'exc' normalizeKind is the identity — so one model faithfully covers all three builders on their actual inputs.

The modeled boundary (require kind != []) is justified: an empty rolename short-circuits in Field.make_xref (docfields.py:71) and builds no pending_xref, so no observable exists there. The scope-stamping fix (A3) is modeled directly, not behind an axiom; no axioms/callee stubs (G-AX skips). Conclusion: the spec is faithful to the real repo behavior on all reachable inputs and is discriminating (prepatch twin fails). No spec-too-strong / drift defect found.

Counterexample / evidence:

```
N/A — no reachable divergence. Non-reachable illustrative case: PyGroupedField('exceptions').make_xref('class','py','None',...) -> real reftype='class'; model scopedRef gives kind='obj'. Blocked because 'class'/typerolename is never routed to PyGroupedField; only 'exc' is, for which normalizeKind is the identity.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Baseline = public problem_statement ONLY (hints_text excluded). Gold edit = stamp the current documentation scope onto the xref descriptor: result['py:module']=env.ref_context.get('py:module'); result['py:class']=env.ref_context.get('py:class') (in PyXrefMixin.make_xref), plus threading env=... into the make_xrefs(...) call in DocFieldTransformer.transform.

Verified spec region is byte-identical (swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean) = True) — the spec does not itself encode the gold; the prepatch twin carries the identical spec and still fails G-DIFF. Mechanical G-LEAK screen re-run (leakage.screen) = passed, 0 hard failures.

(1) LEXICAL: scanned the full spec view for gold-specific tokens — py:module, py:class, env.ref_context, make_xref, refspecific, super(), innernode/contnode, docfields, python.py, reftarget, 8551 — NONE present. All identifiers abstract (curModule/curClass/scopeModule/scopeClass/CrossRef/ScopeName/buildCrossRef). No file path, line number, or gold literal appears.

(2) SEMANTIC: the discriminating spec content — ensures out.scopeModule=curModule / out.scopeClass=curClass and the CrossRef/buildCrossRef doc comments ('the descriptor must record the documentation scope in effect ... so that an unqualified target resolves against the current scope (and its parent scopes) rather than matching the same short name in every (sub)module ... Failing to record the scope is exactly the defect that yields false more-than-one-target ambiguity') — is a faithful abstraction of the problem_statement's own 'Expected behavior' + bug description, which already states that unqualified names must resolve against the current module then parent modules instead of searching every submodule.

Specifying that the fix records the current scope restates the publicly-required behavior; it does NOT disclose the storage mechanism (node attributes on a pending_xref), the two literal gold assignments, or the env-threading companion edit. The preferSpecific/normalizeKind/normalizeTarget legs model UNCHANGED context of the gold hunk, not the gold edit, so they cannot leak it. The spec pins what-correct-behavior-is (its legitimate role) without revealing the gold implementation beyond what solving the stated bug already requires. G-PANEL-3 agent_verdict of record = NO-LEAKAGE; concur.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).