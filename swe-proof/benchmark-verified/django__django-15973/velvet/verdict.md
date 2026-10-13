# P2 adversarial audit — django__django-15973

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -101,8 +101,8 @@
     -- impl-start
     let d : Dep := baseDep f appLabel modelName
     let deps : List Dep := match f.through with
-      | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
+      | none      => [d]
+      | some _thr => [d, mkDep (resolveRef f.target appLabel modelName)]
     return deps
     -- impl-end
 
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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -100,10 +100,7 @@
   do
     -- impl-start
     let d : Dep := baseDep f appLabel modelName
-    let deps : List Dep := match f.through with
-      | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
-    return deps
+    return [d]
     -- impl-end
 
 prove_correct relationDependencies by
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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -102,7 +102,7 @@
     let d : Dep := baseDep f appLabel modelName
     let deps : List Dep := match f.through with
       | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
+      | some thr => [mkDep (resolveRef thr appLabel modelName), d]
     return deps
     -- impl-end
 
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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -102,7 +102,7 @@
     let d : Dep := baseDep f appLabel modelName
     let deps : List Dep := match f.through with
       | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
+      | some _t  => [d, d]
     return deps
     -- impl-end
 
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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -99,11 +99,7 @@
   ensures out = relationDeps f appLabel modelName
   do
     -- impl-start
-    let d : Dep := baseDep f appLabel modelName
-    let deps : List Dep := match f.through with
-      | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
-    return deps
+    return relationDeps f appLabel modelName
     -- impl-end
 
 prove_correct relationDependencies by
```

Attack 6 — `atk_5b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -99,13 +99,8 @@
   ensures out = relationDeps f appLabel modelName
   do
     -- impl-start
-    let d : Dep := baseDep f appLabel modelName
-    let deps : List Dep := match f.through with
-      | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
-    return deps
+    return relationDeps f appLabel modelName
     -- impl-end
 
 prove_correct relationDependencies by
   loom_solve
-  simp_all [relationDeps]
```

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -102,7 +102,7 @@
     let d : Dep := baseDep f appLabel modelName
     let deps : List Dep := match f.through with
       | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
+      | some thr => [d, mkDep (resolveRef thr modelName appLabel)]
     return deps
     -- impl-end
 
```

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -99,11 +99,12 @@
   ensures out = relationDeps f appLabel modelName
   do
     -- impl-start
-    let d : Dep := baseDep f appLabel modelName
-    let deps : List Dep := match f.through with
-      | none     => [d]
-      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
-    return deps
+    let base : Dep := baseDep f appLabel modelName
+    match f.through with
+    | none     => return [base]
+    | some thr =>
+        let extra : Dep := mkDep (resolveRef thr appLabel modelName)
+        return [base, extra]
     -- impl-end
 
 prove_correct relationDependencies by
```

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

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
 /- No consumed axiom. The only foreign callee — the relation resolver that turns
@@ -99,7 +99,7 @@
   ensures out = relationDeps f appLabel modelName
   do
     -- impl-start
-    let d : Dep := baseDep f appLabel modelName
+    let d : Dep := mkDep (resolveRef f.target appLabel modelName)
     let deps : List Dep := match f.through with
       | none     => [d]
       | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign callee — the relation resolver that turns
   a model reference into an (app, object-name) pair — is modeled DEEPLY by
   `resolveRef` (pure region) and validated `resolveRef == the real resolver` by
   axiom_check.py (G-AX, an A-reference; mapping.md §3.1). The modeled behaviour
   itself is a pure data-flow over the field's configuration. -/
-- axioms-end

-- pure-start
/- How a related model is referenced from a field: as an explicit
   self-reference, by an app-qualified name (`"app.Model"`), by a bare app-local
   name (`"Model"`), or by an already-resolved model object that carries its own
   app and object name. -/
inductive RelRef where
  | selfRef
  | qualified (app : String) (name : String)
  | bare (name : String)
  | resolved (app : String) (name : String)
deriving DecidableEq, Inhabited, Repr

/- Resolve a model reference to its `(app, object-name)` pair, in the scope of
   the model that owns the field. A self-reference resolves to the owning model;
   an app-qualified or bare name is normalized with the object name lower-cased;
   an already-resolved object reports its own app and object name. Models the
   repo's relation resolver (mapping.md §3.1; validated == the real resolver by
   G-AX, so it is an A-reference rather than a consumed axiom). -/
def resolveRef (m : RelRef) (appLabel modelName : String) : String × String :=
  match m with
  | .selfRef        => (appLabel, modelName)
  | .qualified a n  => (a, n.toLower)
  | .bare n         => (appLabel, n.toLower)
  | .resolved a n   => (a, n)

/- A single migration dependency: the `(app, object-name)` it points at, an
   optional field name, and whether it must exist before the dependent is
   created. -/
structure Dep where
  app : String
  name : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Inhabited, Repr

/- A create-time dependency on a resolved `(app, name)` pair, with no field. -/
def mkDep (p : String × String) : Dep :=
  { app := p.1, name := p.2, fieldName := none, create := true }

/- A relational field's configuration relevant to its migration dependencies:
   the model it points to (`target`), the intermediary model the relation is
   routed through if any (`through`), and a swappable-setting name when the
   target is a swappable model (`swappable`). -/
structure RelField where
  target : RelRef
  through : Option RelRef
  swappable : Option String
deriving Inhabited

/- The base dependency a field induces on the model it points to: the swappable
   setting under a sentinel app when the target is swappable, otherwise the
   resolved target. -/
def baseDep (f : RelField) (appLabel modelName : String) : Dep :=
  match f.swappable with
  | some s => { app := "__setting__", name := s, fieldName := none, create := true }
  | none   => mkDep (resolveRef f.target appLabel modelName)

/- The full set of migration dependencies a relational field induces: always the
   base dependency on the model it points to, and — when the relation is routed
   through an intermediary model — an ADDITIONAL dependency on that intermediary
   model, resolved (in the field owner's scope) from the intermediary's own
   reference. -/
def relationDeps (f : RelField) (appLabel modelName : String) : List Dep :=
  match f.through with
  | none     => [baseDep f appLabel modelName]
  | some thr => [baseDep f appLabel modelName, mkDep (resolveRef thr appLabel modelName)]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; appLabel/modelName are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- Compute the migration dependencies of one relational field, in the scope of
   the model that owns it. The result lists the base dependency on the model the
   field points to and, when the relation is routed through an intermediary
   model, the additional dependency on that intermediary model. -/
method relationDependencies (f : RelField) (appLabel : String) (modelName : String)
    return (out : List Dep)
  ensures out = relationDeps f appLabel modelName
  do
    -- impl-start
    let d : Dep := baseDep f appLabel modelName
    let deps : List Dep := match f.through with
      | none     => [d]
      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
    return deps
    -- impl-end

prove_correct relationDependencies by
  loom_solve
  simp_all [relationDeps]
```

Prepatch bug re-encoded as an attack: `True`.

 All 9 attack files confirmed same_spec==True vs frozen Solution.lean; axioms/pure/pre/post left byte-identical, only impl region (and, for atk_5b, the mutable prove_correct tactic) edited.

SPEC SHAPE (decisive): postcondition is a TOTAL EXACT EQUALITY `ensures out = relationDeps f appLabel modelName` with NO module preconditions and a FROZEN pure region (RelRef/resolveRef/Dep/mkDep/RelField/baseDep/relationDeps). Any impl that verifies must equal relationDeps on EVERY input, hence is behaviourally identical to the gold patch. This structurally forbids a verifying-but-wrong impl.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch):
- atk_1 PREPATCH BUG (through dep resolved from f.target, not thr): exit 1 REJECTED (also reproduces Solution_prepatch.lean bug => prepatch_reproduced=true).
- atk_2 PARTIAL-DOMAIN (drop through dep, always [base]): exit 1 REJECTED.
- atk_3 BOUNDARY (reversed dep order in some-thr arm): exit 1 REJECTED.
- atk_4 CONTROL-FLOW-EFFECT (duplicate base dep [d,d] instead of appending through): exit 1 REJECTED.
- atk_6 WRONG-SCOPE (resolveRef thr modelName appLabel, swapped scope args): exit 1 REJECTED.
- atk_8 SWAPPABLE-IGNORE (base dep always resolves target, ignores swappable branch): exit 1 REJECTED (unsolved-goals shows swappable divergence).
- atk_5 UNGROUNDED-ORACLE ECHO (`return relationDeps f appLabel modelName`): exit 1 but ONLY because gold's `simp_all [relationDeps]` over-applies ("No goals"); behaviourally IS gold. atk_5b = same impl with mutable proof reduced to `loom_solve` -> exit 0 VERIFIES, still same_spec==True.
- atk_7 equivalent restructure (multi-arm return): parse artifact (WPGen), behaviourally = gold; not a wrong impl.

So the ONLY same-spec impls that VERIFY (pos, atk_5b, and behaviourally-equivalent atk_7) are behaviourally identical to gold. Per protocol step 2 I materialized atk_5b's faithful refined patch (= the gold single-line change remote_field_model -> field.remote_field.through) and RAN it through the official harness: `run_resolve('django__django-15973', patch, timeout=1800, retries=0)` => RESOLVED=True, completed=True, note='resolved'. So the verifying impl's faithful patch RESOLVES. No verify⇏?correct witness exists.

A-LEG AUDIT (refinement.md): every leg is R / A-reference / I, no kind-3. meta.json axioms==[] (no consumed axiom). Sole foreign callee resolve_relation is deeply modeled by resolveRef (A-reference); axiom_check.py validates resolveRef==resolve_relation over 11 boundary refs x 4 scopes + 20000 mixed-case ASCII fuzz (seed 15973), stdlib+django only. The four resolveRef arms mirror the four resolve_relation returns exactly; the two TypeError arms are unreachable (call sites always pass app_label/model_name). mapping.md correspondence holds: RelField<->field.remote_field.{model,through}+swappable_setting; Dep<->(app,obj,None,True) 4-tuple; RECURSIVE 'self'/qualified/bare/resolved bijection matches. The one CHANGED op (A5: through dep resolved from thr=field.remote_field.through, not f.target=remote_field_model) is a concrete data-flow edit (I) over the deep-modeled resolver, matching patch.diff verbatim.

VERDICT: SOUND. ≥6 distinct wrong impls encoded and verified; all genuinely-wrong ones rejected; the sole verifying same-spec impl's faithful patch was executed through the harness and RESOLVED. verify⇒correct holds for this bundle.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 9 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 9 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5b.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (9):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 9 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_5b.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axiom. The only foreign callee — the relation resolver that turns
   a model reference into an (app, object-name) pair — is modeled DEEPLY by
   `resolveRef` (pure region) and validated `resolveRef == the real resolver` by
   axiom_check.py (G-AX, an A-reference; mapping.md §3.1). The modeled behaviour
   itself is a pure data-flow over the field's configuration. -/
-- axioms-end

-- pure-start
/- How a related model is referenced from a field: as an explicit
   self-reference, by an app-qualified name (`"app.Model"`), by a bare app-local
   name (`"Model"`), or by an already-resolved model object that carries its own
   app and object name. -/
inductive RelRef where
  | selfRef
  | qualified (app : String) (name : String)
  | bare (name : String)
  | resolved (app : String) (name : String)
deriving DecidableEq, Inhabited, Repr

/- Resolve a model reference to its `(app, object-name)` pair, in the scope of
   the model that owns the field. A self-reference resolves to the owning model;
   an app-qualified or bare name is normalized with the object name lower-cased;
   an already-resolved object reports its own app and object name. Models the
   repo's relation resolver (mapping.md §3.1; validated == the real resolver by
   G-AX, so it is an A-reference rather than a consumed axiom). -/
def resolveRef (m : RelRef) (appLabel modelName : String) : String × String :=
  match m with
  | .selfRef        => (appLabel, modelName)
  | .qualified a n  => (a, n.toLower)
  | .bare n         => (appLabel, n.toLower)
  | .resolved a n   => (a, n)

/- A single migration dependency: the `(app, object-name)` it points at, an
   optional field name, and whether it must exist before the dependent is
   created. -/
structure Dep where
  app : String
  name : String
  fieldName : Option String
  create : Bool
deriving DecidableEq, Inhabited, Repr

/- A create-time dependency on a resolved `(app, name)` pair, with no field. -/
def mkDep (p : String × String) : Dep :=
  { app := p.1, name := p.2, fieldName := none, create := true }

/- A relational field's configuration relevant to its migration dependencies:
   the model it points to (`target`), the intermediary model the relation is
   routed through if any (`through`), and a swappable-setting name when the
   target is a swappable model (`swappable`). -/
structure RelField where
  target : RelRef
  through : Option RelRef
  swappable : Option String
deriving Inhabited

/- The base dependency a field induces on the model it points to: the swappable
   setting under a sentinel app when the target is swappable, otherwise the
   resolved target. -/
def baseDep (f : RelField) (appLabel modelName : String) : Dep :=
  match f.swappable with
  | some s => { app := "__setting__", name := s, fieldName := none, create := true }
  | none   => mkDep (resolveRef f.target appLabel modelName)

/- The full set of migration dependencies a relational field induces: always the
   base dependency on the model it points to, and — when the relation is routed
   through an intermediary model — an ADDITIONAL dependency on that intermediary
   model, resolved (in the field owner's scope) from the intermediary's own
   reference. -/
def relationDeps (f : RelField) (appLabel modelName : String) : List Dep :=
  match f.through with
  | none     => [baseDep f appLabel modelName]
  | some thr => [baseDep f appLabel modelName, mkDep (resolveRef thr appLabel modelName)]
-- pure-end

-- pre-conditions-start
-- (no module-level preconditions; appLabel/modelName are always supplied)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the inline `ensures` clause on the method below)
-- post-conditions-end

/- Compute the migration dependencies of one relational field, in the scope of
   the model that owns it. The result lists the base dependency on the model the
   field points to and, when the relation is routed through an intermediary
   model, the additional dependency on that intermediary model. -/
method relationDependencies (f : RelField) (appLabel : String) (modelName : String)
    return (out : List Dep)
  ensures out = relationDeps f appLabel modelName
  do
    -- impl-start
    let d : Dep := baseDep f appLabel modelName
    let deps : List Dep := match f.through with
      | none     => [d]
      | some thr => [d, mkDep (resolveRef thr appLabel modelName)]
    return deps
    -- impl-end

prove_correct relationDependencies by
  loom_solve
  simp_all [relationDeps]
```

Prepatch bug re-encoded as an attack: `True`.

 All 9 attack files confirmed same_spec==True vs frozen Solution.lean; axioms/pure/pre/post left byte-identical, only impl region (and, for atk_5b, the mutable prove_correct tactic) edited.

SPEC SHAPE (decisive): postcondition is a TOTAL EXACT EQUALITY `ensures out = relationDeps f appLabel modelName` with NO module preconditions and a FROZEN pure region (RelRef/resolveRef/Dep/mkDep/RelField/baseDep/relationDeps). Any impl that verifies must equal relationDeps on EVERY input, hence is behaviourally identical to the gold patch. This structurally forbids a verifying-but-wrong impl.

### ATTACKS (cmd: `bash scripts/lean_verify.sh <f>`, run concurrently ≤4/batch):
- atk_1 PREPATCH BUG (through dep resolved from f.target, not thr): exit 1 REJECTED (also reproduces Solution_prepatch.lean bug => prepatch_reproduced=true).
- atk_2 PARTIAL-DOMAIN (drop through dep, always [base]): exit 1 REJECTED.
- atk_3 BOUNDARY (reversed dep order in some-thr arm): exit 1 REJECTED.
- atk_4 CONTROL-FLOW-EFFECT (duplicate base dep [d,d] instead of appending through): exit 1 REJECTED.
- atk_6 WRONG-SCOPE (resolveRef thr modelName appLabel, swapped scope args): exit 1 REJECTED.
- atk_8 SWAPPABLE-IGNORE (base dep always resolves target, ignores swappable branch): exit 1 REJECTED (unsolved-goals shows swappable divergence).
- atk_5 UNGROUNDED-ORACLE ECHO (`return relationDeps f appLabel modelName`): exit 1 but ONLY because gold's `simp_all [relationDeps]` over-applies ("No goals"); behaviourally IS gold. atk_5b = same impl with mutable proof reduced to `loom_solve` -> exit 0 VERIFIES, still same_spec==True.
- atk_7 equivalent restructure (multi-arm return): parse artifact (WPGen), behaviourally = gold; not a wrong impl.

So the ONLY same-spec impls that VERIFY (pos, atk_5b, and behaviourally-equivalent atk_7) are behaviourally identical to gold. Per protocol step 2 I materialized atk_5b's faithful refined patch (= the gold single-line change remote_field_model -> field.remote_field.through) and RAN it through the official harness: `run_resolve('django__django-15973', patch, timeout=1800, retries=0)` => RESOLVED=True, completed=True, note='resolved'. So the verifying impl's faithful patch RESOLVES. No verify⇏?correct witness exists.

A-LEG AUDIT (refinement.md): every leg is R / A-reference / I, no kind-3. meta.json axioms==[] (no consumed axiom). Sole foreign callee resolve_relation is deeply modeled by resolveRef (A-reference); axiom_check.py validates resolveRef==resolve_relation over 11 boundary refs x 4 scopes + 20000 mixed-case ASCII fuzz (seed 15973), stdlib+django only. The four resolveRef arms mirror the four resolve_relation returns exactly; the two TypeError arms are unreachable (call sites always pass app_label/model_name). mapping.md correspondence holds: RelField<->field.remote_field.{model,through}+swappable_setting; Dep<->(app,obj,None,True) 4-tuple; RECURSIVE 'self'/qualified/bare/resolved bijection matches. The one CHANGED op (A5: through dep resolved from thr=field.remote_field.through, not f.target=remote_field_model) is a concrete data-flow edit (I) over the deep-modeled resolver, matching patch.diff verbatim.

VERDICT: SOUND. ≥6 distinct wrong impls encoded and verified; all genuinely-wrong ones rejected; the sole verifying same-spec impl's faithful patch was executed through the harness and RESOLVED. verify⇒correct holds for this bundle.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (swebench_unified.markers.same_spec == True). The spec models the PATCHED (gold) callee _get_dependencies_for_foreign_key exactly: on the `some thr` arm it emits mkDep(resolveRef thr ...), resolving the through dependency from the intermediary's OWN reference (field.remote_field.through), matching the gold fix (`- remote_field_model` / `+ field.remote_field.through`). Verified the real base-commit patched function against the transliterated shadow on the F2P scenario and all realistic ASCII inputs — exact agreement. G-CONF passed 100008 fuzz inputs (seed 15973) with gold applied and DISAGREES without gold (genuine fix discrimination); G-AX passed 20044 cases (resolveRef == real resolve_relation). The two probed drift candidates (ASCII-only toLower; empty-string through truthiness) are the standard, documented string-modeling convention (ASCII case folding) and the through-is-None/real-ref invariant respectively — both explicitly out of the declared bijection domain, and G-AX itself notes its only disagreements occur outside that domain. resolveRef's four arms mirror resolve_relation's four returns; the two TypeError paths are unreachable (call sites always supply app_label/model_name). No in-domain input where the modeled function disagrees with the real callee. Spec is FAITHFUL (and, per verdict.md, tight — the exact-equality ensures rejects prepatch + 5 wrong impls while admitting a structurally-distinct correct impl).

Counterexample / evidence:

```
target=('qualified','testapp','MODÈLE'), through=None, swappable=None, scope=('authors','author'): spec/Lean -> [('testapp','modÈle',None,True)] ; real callee -> [('testapp','modèle',None,True)]. AND target=('qualified','testapp','Publisher'), through=('bare',''), scope=('authors','author'): spec -> [('testapp','publisher',..),('authors','',..)] ; real -> [('testapp','publisher',..)] (empty through is falsy). BOTH lie outside the mapping.md §2 domain (valid ASCII Django references; through is None or a real non-empty ref).
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (velvet Solution.lean, computed via markers.spec_view) does NOT leak the gold edit beyond the public problem_statement.

Gold edit: single-line change in django/db/migrations/autodetector.py:_get_dependencies_for_foreign_key — resolve the through-dependency from field.remote_field.through (intermediary) instead of remote_field_model (target).

Mechanical screen: leakage.screen() PASSES (no hard failures). Frozen spec is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True).

Semantic review of the solver-visible spec view:
- No diff markers, no gold-patch line reproduced verbatim, no patched file path (autodetector.py), no patched module path.
- No repo symbol names appear: '_get_dependencies_for_foreign_key', 'resolve_relation', 'remote_field_model', 'field.remote_field.through' are ALL absent. Spec uses abstract Lean identifiers only (resolveRef, RelField.through, relationDeps, baseDep).
- No bug/fix/pre-post-patch narration in any spec-view comment. Comments describe function behavior at the contract altitude, never contrasting old vs new behavior.
- The operative contract content ('some thr => [baseDep …, mkDep (resolveRef thr appLabel modelName)]' with comment 'an ADDITIONAL dependency on that intermediary model, resolved … from the intermediary's own reference') is the necessary description of correct behavior for ANY functional spec. It discloses no edit localization (file/symbol) and no diff-specific form.
- Crucially, the through-model-in-a-different-app crux is ALREADY public in the problem_statement, which is entirely about the fonte_variavel intermediary living in another app and the AttributeError on field.remote_field.through._meta. The spec adds no localization beyond the public issue.

Note: the AUDITOR docs (refinement.md, mapping.md) DO carry the gold diff verbatim and repo symbols, but those are auditor-only artifacts and are NOT part of the solver-visible spec view; G-PANEL-3 leakage is judged over the spec view only.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
