# P2 adversarial audit — django__django-13820

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,12 +48,9 @@
 -- impl-start
 def implementation_providesMigrations
     (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
+  if !hasFile then
+    return false
   if !path.isPackage then
-    return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
     return false
   return true
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,15 +47,8 @@
 
 -- impl-start
 def implementation_providesMigrations
-    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
-  if !path.isPackage then
-    return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
-    return false
-  return true
+    (hasFile : Bool) (path : ModulePath) : Bool :=
+  path.isPackage && hasFile
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,15 +47,8 @@
 
 -- impl-start
 def implementation_providesMigrations
-    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
-  if !path.isPackage then
-    return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
-    return false
-  return true
+    (hasFile : Bool) (path : ModulePath) : Bool :=
+  path.isPackage
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,15 +47,8 @@
 
 -- impl-start
 def implementation_providesMigrations
-    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
-  if !path.isPackage then
-    return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
-    return false
-  return true
+    (hasFile : Bool) (path : ModulePath) : Bool :=
+  path.isPackage && (hasFile && path.isList)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,15 +47,8 @@
 
 -- impl-start
 def implementation_providesMigrations
-    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
-  if !path.isPackage then
-    return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
-    return false
-  return true
+    (hasFile : Bool) (path : ModulePath) : Bool :=
+  hasFile || path.isList
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -47,15 +47,8 @@
 
 -- impl-start
 def implementation_providesMigrations
-    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
-  if !path.isPackage then
-    return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
-    return false
-  return true
+    (hasFile : Bool) (path : ModulePath) : Bool :=
+  path.isList || (hasFile && path.isPackage)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -48,14 +48,11 @@
 -- impl-start
 def implementation_providesMigrations
     (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
   if !path.isPackage then
     return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
-    return false
-  return true
+  if hasFile then
+    return true
+  return path.isList
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,15 +47,8 @@
 
 -- impl-start
 def implementation_providesMigrations
-    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
-  -- A module that is not a package cannot provide migrations.
-  if !path.isPackage then
-    return false
-  -- A package with no file location whose path is a custom (non-list) iterable
-  -- is an empty-directory placeholder, not a real migrations package.
-  if !hasFile && !path.isList then
-    return false
-  return true
+    (hasFile : Bool) (path : ModulePath) : Bool :=
+  path.isPackage && (hasFile || !path.isList)
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decision modeled below
-- is a pure predicate over a module's introspected attributes (whether it has a
-- file location, whether it is a package, and whether its package path is an
-- ordinary list). The attribute reads are language-level introspection, modeled
-- directly as boolean field reads (I-tagged in refinement.md); nothing is
-- axiomatized. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The package-path information a module can expose to introspection:
either it is not a package at all, or it is a package whose path is an ordinary
list, or it is a package whose path is a custom (non-list) iterable. -/
inductive ModulePath where
  | noPath       -- the module exposes no package path (it is not a package)
  | listPath     -- the package path is an ordinary list
  | customPath   -- the package path is a custom, non-list iterable
  deriving DecidableEq, Repr

/-- Whether the module is a package (exposes a package path at all). -/
def ModulePath.isPackage : ModulePath → Bool
  | .noPath => false
  | _       => true

/-- Whether the module's package path is an ordinary list. -/
def ModulePath.isList : ModulePath → Bool
  | .listPath => true
  | _         => false
-- pure-end

-- post-conditions-start
/-- A module is treated as a source of migrations exactly when it is a package
AND it either has a file location on disk OR its package path is an ordinary
list. A package that has no file location and whose path is a custom iterable is
an empty-directory placeholder and is NOT treated as a source of migrations;
likewise a non-package is never a source of migrations.

`hasFile` is whether the module exposes a (non-empty) file location; `path`
carries the package-path information described by `ModulePath`. -/
def problem_spec_providesMigrations
    (hasFile : Bool) (path : ModulePath) (result : Bool) : Prop :=
  result = (path.isPackage && (hasFile || path.isList))
-- post-conditions-end

-- impl-start
def implementation_providesMigrations
    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
  -- A module that is not a package cannot provide migrations.
  if !path.isPackage then
    return false
  -- A package with no file location whose path is a custom (non-list) iterable
  -- is an empty-directory placeholder, not a real migrations package.
  if !hasFile && !path.isList then
    return false
  return true
-- impl-end

-- proof-start
theorem correct_providesMigrations :
    ∀ (hasFile : Bool) (path : ModulePath),
      problem_spec_providesMigrations hasFile path
        (implementation_providesMigrations hasFile path) := by
  intro hasFile path
  unfold problem_spec_providesMigrations implementation_providesMigrations
  cases path <;> cases hasFile <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_providesMigrations hasFile path result := result = (path.isPackage && (hasFile || path.isList)). Total EQUALITY over the finite domain Bool x ModulePath = exactly 6 reachable points. Any impl whose correct_ proof closes (no sorry, clean axioms) is forced to be extensionally equal to the gold function isPackage&&(hasFile||isList) on all 6 points. Confirmed same_spec=True for all 9 files (byte-identical axioms/pure/pre/post region).

Commands (project root; ran attack verifications concurrently, <=4 at a time as background jobs):
  bash scripts/lean_verify.sh <D>/<file>.lean
where.

### ATTACKS (all same_spec=True):
- atk_1 PRE-PATCH bug (reject !hasFile before package check => hasFile&&isPackage): exit 1 (fails at listPath.false). = prepatch reproduced.
- atk_2 drop isList disjunct (path.isPackage && hasFile): exit 1 (fails listPath,false).
- atk_3 partial-domain (path.isPackage only): exit 1 (fails customPath).
- atk_4 boundary AND-instead-of-OR (isPackage && (hasFile && isList)): exit 1 (fails customPath,true).
- atk_5 control-flow-effect drop isPackage guard (hasFile || isList): exit 1 (fails noPath,true).
- atk_8 boundary negate-list (isPackage && (hasFile || !isList)): exit 1 (fails customPath,false).
  => all 6 behaviorally-WRONG impls FAIL TO CLOSE (exit 1). Cannot produce a closing clean-axiom proof, so nothing to resolve-test for these.
- atk_6 ungrounded-oracle echo, reordered (path.isList || (hasFile && path.isPackage)): exit 0, #print axioms => 'does not depend on any axioms'. Behaviorally IDENTICAL to gold on all 6 points (verified truth table). Faithful patch = gold patch. RESOLVE RAN via harness.run_resolve(run_id=sbu-audit-eq-atk6): RESOLVED=True, FAIL_TO_PASS test_loading_package_without__file__ PASS, all 24 PASS_TO_PASS pass, patch_successfully_applied=True.
- atk_7 control-flow echo, imperative (if !isPackage=>false; if hasFile=>true; return isList): exit 0, clean axioms. Behaviorally IDENTICAL to gold. Faithful patch = gold patch (same as atk_6). RESOLVED=True (same executed report).

POSITIVE CONTROL pos_control.lean = gold impl verbatim: lean_verify exit 0; #print axioms => does not depend on any axioms.

RESOLVE EVIDENCE (executed, not speculated): report {'resolved': True, 'patch_successfully_applied': True, FAIL_TO_PASS success=['test_loading_package_without__file__'], PASS_TO_PASS all success, FAIL_TO_FAIL/PASS_TO_FAIL empty}. Both closing echoes' faithful patches RESOLVE.

REFINEMENT.MD AUDIT: axioms-start/axioms-end region is EMPTY (comments only; no axiom/opaque decls) => there are NO A-legs. All 3 refinement rows are I-tagged: row1 path.isPackage <-> hasattr(module,'__path__'); row2 hasFile <-> getattr(module,'__file__',None) is not None and path.isList <-> isinstance(module.__path__,list); row3 return true <-> fall-through to migrated_apps.add. No kind-3 (inexpressible) legs; no A-consumed/A-reference rows to validate. The introspection builtins (getattr/hasattr/isinstance) carry no domain logic and are modeled directly as the hasFile flag + ModulePath discriminant. Correspondence confirmed sound by the gold-patch resolve above (spec behavior == real patch behavior on all 6 reachable points). mapping.md type bijection is exhaustive (3 ModulePath constructors partition __path__ introspection; hasFile independent bool => 6 points cover all reachable combos).

CONCLUSION: The spec is a total equality over a 6-point reachable domain; verify => extensional-equality-with-gold => resolve. No behaviorally-wrong impl closes; the only closing impls are gold-equivalent and their faithful patches RESOLVE (executed). No verify=/=>correct break exists. G-EQ = SOUND (8 attacks run, none breaks it; all needed resolve runs completed).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The decision modeled below
-- is a pure predicate over a module's introspected attributes (whether it has a
-- file location, whether it is a package, and whether its package path is an
-- ordinary list). The attribute reads are language-level introspection, modeled
-- directly as boolean field reads (I-tagged in refinement.md); nothing is
-- axiomatized. The proof agent may add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The package-path information a module can expose to introspection:
either it is not a package at all, or it is a package whose path is an ordinary
list, or it is a package whose path is a custom (non-list) iterable. -/
inductive ModulePath where
  | noPath       -- the module exposes no package path (it is not a package)
  | listPath     -- the package path is an ordinary list
  | customPath   -- the package path is a custom, non-list iterable
  deriving DecidableEq, Repr

/-- Whether the module is a package (exposes a package path at all). -/
def ModulePath.isPackage : ModulePath → Bool
  | .noPath => false
  | _       => true

/-- Whether the module's package path is an ordinary list. -/
def ModulePath.isList : ModulePath → Bool
  | .listPath => true
  | _         => false
-- pure-end

-- post-conditions-start
/-- A module is treated as a source of migrations exactly when it is a package
AND it either has a file location on disk OR its package path is an ordinary
list. A package that has no file location and whose path is a custom iterable is
an empty-directory placeholder and is NOT treated as a source of migrations;
likewise a non-package is never a source of migrations.

`hasFile` is whether the module exposes a (non-empty) file location; `path`
carries the package-path information described by `ModulePath`. -/
def problem_spec_providesMigrations
    (hasFile : Bool) (path : ModulePath) (result : Bool) : Prop :=
  result = (path.isPackage && (hasFile || path.isList))
-- post-conditions-end

-- impl-start
def implementation_providesMigrations
    (hasFile : Bool) (path : ModulePath) : Bool := Id.run do
  -- A module that is not a package cannot provide migrations.
  if !path.isPackage then
    return false
  -- A package with no file location whose path is a custom (non-list) iterable
  -- is an empty-directory placeholder, not a real migrations package.
  if !hasFile && !path.isList then
    return false
  return true
-- impl-end

-- proof-start
theorem correct_providesMigrations :
    ∀ (hasFile : Bool) (path : ModulePath),
      problem_spec_providesMigrations hasFile path
        (implementation_providesMigrations hasFile path) := by
  intro hasFile path
  unfold problem_spec_providesMigrations implementation_providesMigrations
  cases path <;> cases hasFile <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: problem_spec_providesMigrations hasFile path result := result = (path.isPackage && (hasFile || path.isList)). Total EQUALITY over the finite domain Bool x ModulePath = exactly 6 reachable points. Any impl whose correct_ proof closes (no sorry, clean axioms) is forced to be extensionally equal to the gold function isPackage&&(hasFile||isList) on all 6 points. Confirmed same_spec=True for all 9 files (byte-identical axioms/pure/pre/post region).

Commands (project root; ran attack verifications concurrently, <=4 at a time as background jobs):
  bash scripts/lean_verify.sh <D>/<file>.lean
where.

### ATTACKS (all same_spec=True):
- atk_1 PRE-PATCH bug (reject !hasFile before package check => hasFile&&isPackage): exit 1 (fails at listPath.false). = prepatch reproduced.
- atk_2 drop isList disjunct (path.isPackage && hasFile): exit 1 (fails listPath,false).
- atk_3 partial-domain (path.isPackage only): exit 1 (fails customPath).
- atk_4 boundary AND-instead-of-OR (isPackage && (hasFile && isList)): exit 1 (fails customPath,true).
- atk_5 control-flow-effect drop isPackage guard (hasFile || isList): exit 1 (fails noPath,true).
- atk_8 boundary negate-list (isPackage && (hasFile || !isList)): exit 1 (fails customPath,false).
  => all 6 behaviorally-WRONG impls FAIL TO CLOSE (exit 1). Cannot produce a closing clean-axiom proof, so nothing to resolve-test for these.
- atk_6 ungrounded-oracle echo, reordered (path.isList || (hasFile && path.isPackage)): exit 0, #print axioms => 'does not depend on any axioms'. Behaviorally IDENTICAL to gold on all 6 points (verified truth table). Faithful patch = gold patch. RESOLVE RAN via harness.run_resolve(run_id=sbu-audit-eq-atk6): RESOLVED=True, FAIL_TO_PASS test_loading_package_without__file__ PASS, all 24 PASS_TO_PASS pass, patch_successfully_applied=True.
- atk_7 control-flow echo, imperative (if !isPackage=>false; if hasFile=>true; return isList): exit 0, clean axioms. Behaviorally IDENTICAL to gold. Faithful patch = gold patch (same as atk_6). RESOLVED=True (same executed report).

POSITIVE CONTROL pos_control.lean = gold impl verbatim: lean_verify exit 0; #print axioms => does not depend on any axioms.

RESOLVE EVIDENCE (executed, not speculated): report {'resolved': True, 'patch_successfully_applied': True, FAIL_TO_PASS success=['test_loading_package_without__file__'], PASS_TO_PASS all success, FAIL_TO_FAIL/PASS_TO_FAIL empty}. Both closing echoes' faithful patches RESOLVE.

REFINEMENT.MD AUDIT: axioms-start/axioms-end region is EMPTY (comments only; no axiom/opaque decls) => there are NO A-legs. All 3 refinement rows are I-tagged: row1 path.isPackage <-> hasattr(module,'__path__'); row2 hasFile <-> getattr(module,'__file__',None) is not None and path.isList <-> isinstance(module.__path__,list); row3 return true <-> fall-through to migrated_apps.add. No kind-3 (inexpressible) legs; no A-consumed/A-reference rows to validate. The introspection builtins (getattr/hasattr/isinstance) carry no domain logic and are modeled directly as the hasFile flag + ModulePath discriminant. Correspondence confirmed sound by the gold-patch resolve above (spec behavior == real patch behavior on all 6 reachable points). mapping.md type bijection is exhaustive (3 ModulePath constructors partition __path__ introspection; hasFile independent bool => 6 points cover all reachable combos).

CONCLUSION: The spec is a total equality over a 6-point reachable domain; verify => extensional-equality-with-gold => resolve. No behaviorally-wrong impl closes; the only closing impls are gold-equivalent and their faithful patches RESOLVE (executed). No verify=/=>correct break exists. G-EQ = SOUND (8 attacks run, none breaks it; all needed resolve runs completed).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift) check for django__django-13820 lean bundle. The modeled function is the namespace-package classification in MigrationLoader.load_disk. Spec: result = (path.isPackage && (hasFile || path.isList)), over the 6-point domain Bool × {noPath, listPath, customPath}.

### Verification performed
1. same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True — spec regions byte-identical; spec_view confirmed.
2. lean_verify.sh Solution.lean → exit 0 (compiles, no sorry).
3. #print axioms correct_providesMigrations → 'does not depend on any axioms' — proof genuine, no sorryAx.
4. Real repo at base_commit (@ 2c7846d992, post-patch loader.py:91-102) matches the modeled guard sequence exactly.

EXHAUSTIVE 6-POINT ENUMERATION vs real repo — spec agrees on EVERY input:
- (T,noPath): spec F; repo `not hasattr __path__`→unmigrated F ✓
- (F,noPath): spec F; repo unmigrated F ✓
- (T,listPath): spec T; repo file-not-None→2nd guard F→migrated T ✓
- (F,listPath): spec T; repo file None ∧ isinstance list→2nd guard F→migrated T ✓ (the frozen-env F2P case test_loading_package_without__file__)
- (T,customPath): spec T; repo file-not-None→migrated T ✓
- (F,customPath): spec F; repo file None ∧ not-list→2nd guard T→unmigrated F ✓

MODELING BOUNDARY SOUND: getattr('__file__')/hasattr('__path__')/isinstance(__path__,list) are pure language-level introspection reads with no domain logic; collapsing them into hasFile:Bool and the ModulePath discriminant loses no reachable behavior. The three ModulePath constructors partition __path__ introspection exhaustively and hasFile is independent, so Bool×ModulePath covers every reachable state at this guard. import_module/reload/pkgutil/set-mutations are outside the modeled guard (correctly). Axioms region empty; G-AX skip is legitimate.

The spec is neither too strong nor drifted: it is exactly the post-patch behavior. No diverging input exists. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (axioms empty; pure ModulePath type; post-condition `result = (path.isPackage && (hasFile || path.isList))`) elides impl+proof and discloses nothing about the gold edit beyond the public problem_statement. The problem_statement itself spells out the entire fix: it names the current `getattr(m,'__file__',None)` check, explains namespace packages use a custom (non-list) `__path__`, and states verbatim 'I propose to augment getattr(m, '__file__', None) with and isinstance(m.__path__, list)'. Thus the exact discriminator (is-package ∧ (has-__file__ ∨ __path__-is-a-list)) is already public. The post-condition merely restates this publicly-known intended behavior in Lean; ModulePath's noPath/listPath/customPath partition mirrors the problem_statement's own distinction between not-a-package, ordinary-list __path__, and custom-iterable __path__. Lexical leakage.screen passes (hard_failures empty). No spec-view line exceeds the problem_statement's disclosure of the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
