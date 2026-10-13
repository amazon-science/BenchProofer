# P2 adversarial audit — django__django-12125

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.lean`, `atk2_partial.lean`, `atk3_orderswap.lean`, `atk4_nobuiltins.lean`, `atk5_noimport.lean`, `atk6_flipbuiltin.lean`, `atk7_nomoduleprefix.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Nested-class descriptor v = ⟨isModelBase=false, isNoneType=false, hasModule=true, module="app", shortName="Inner", fullName="Outer.Inner"⟩. Spec requires some ("app.Outer.Inner", ["import app"]) (module ++ "." ++ fullName, i.e. __qualname__); the prepatch bug produces some ("app.Inner", ["import app"]) (module ++ "." ++ shortName, i.e. __name__). Disproof atk1_disproof.lean closes (exit 0) proving problem_spec_serializeType is genuinely violated on this witness — this is exactly the FAIL_TO_PASS test_serialize_nested_class case (WriterTests.NestedEnum).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,20 +80,15 @@
 -- impl-start
 def implementation_serializeType (v : TypeRef) :
     Option (String × List String) := Id.run do
-  -- The constant special cases, checked in order before anything else.
   if v.isModelBase then
     return some ("models.Model", [])
   if v.isNoneType then
     return some ("type(None)", [])
-  -- A class with an observable home module.
   if v.hasModule then
     if v.module = builtinsModule then
-      -- Built-in namespace: the leaf name alone, no import.
       return some (v.shortName, [])
     else
-      -- Any other module: home module joined to the class's fully-qualified
-      -- in-module path, plus the import of that home module.
-      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
+      return some (v.module ++ "." ++ v.shortName, ["import " ++ v.module])
   return none
 -- impl-end
 
```

Attack 2 — `atk2_partial.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,20 +80,10 @@
 -- impl-start
 def implementation_serializeType (v : TypeRef) :
     Option (String × List String) := Id.run do
-  -- The constant special cases, checked in order before anything else.
   if v.isModelBase then
     return some ("models.Model", [])
   if v.isNoneType then
     return some ("type(None)", [])
-  -- A class with an observable home module.
-  if v.hasModule then
-    if v.module = builtinsModule then
-      -- Built-in namespace: the leaf name alone, no import.
-      return some (v.shortName, [])
-    else
-      -- Any other module: home module joined to the class's fully-qualified
-      -- in-module path, plus the import of that home module.
-      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
   return none
 -- impl-end
 
```

Attack 3 — `atk3_orderswap.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,19 +80,14 @@
 -- impl-start
 def implementation_serializeType (v : TypeRef) :
     Option (String × List String) := Id.run do
-  -- The constant special cases, checked in order before anything else.
+  if v.isNoneType then
+    return some ("type(None)", [])
   if v.isModelBase then
     return some ("models.Model", [])
-  if v.isNoneType then
-    return some ("type(None)", [])
-  -- A class with an observable home module.
   if v.hasModule then
     if v.module = builtinsModule then
-      -- Built-in namespace: the leaf name alone, no import.
       return some (v.shortName, [])
     else
-      -- Any other module: home module joined to the class's fully-qualified
-      -- in-module path, plus the import of that home module.
       return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
   return none
 -- impl-end
```

Attack 4 — `atk4_nobuiltins.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,20 +80,12 @@
 -- impl-start
 def implementation_serializeType (v : TypeRef) :
     Option (String × List String) := Id.run do
-  -- The constant special cases, checked in order before anything else.
   if v.isModelBase then
     return some ("models.Model", [])
   if v.isNoneType then
     return some ("type(None)", [])
-  -- A class with an observable home module.
   if v.hasModule then
-    if v.module = builtinsModule then
-      -- Built-in namespace: the leaf name alone, no import.
-      return some (v.shortName, [])
-    else
-      -- Any other module: home module joined to the class's fully-qualified
-      -- in-module path, plus the import of that home module.
-      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
+    return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
   return none
 -- impl-end
 
```

Attack 5 — `atk5_noimport.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,20 +80,15 @@
 -- impl-start
 def implementation_serializeType (v : TypeRef) :
     Option (String × List String) := Id.run do
-  -- The constant special cases, checked in order before anything else.
   if v.isModelBase then
     return some ("models.Model", [])
   if v.isNoneType then
     return some ("type(None)", [])
-  -- A class with an observable home module.
   if v.hasModule then
     if v.module = builtinsModule then
-      -- Built-in namespace: the leaf name alone, no import.
       return some (v.shortName, [])
     else
-      -- Any other module: home module joined to the class's fully-qualified
-      -- in-module path, plus the import of that home module.
-      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
+      return some (v.module ++ "." ++ v.fullName, [])
   return none
 -- impl-end
 
```

Attack 6 — `atk6_flipbuiltin.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,19 +80,14 @@
 -- impl-start
 def implementation_serializeType (v : TypeRef) :
     Option (String × List String) := Id.run do
-  -- The constant special cases, checked in order before anything else.
   if v.isModelBase then
     return some ("models.Model", [])
   if v.isNoneType then
     return some ("type(None)", [])
-  -- A class with an observable home module.
   if v.hasModule then
-    if v.module = builtinsModule then
-      -- Built-in namespace: the leaf name alone, no import.
+    if v.module != builtinsModule then
       return some (v.shortName, [])
     else
-      -- Any other module: home module joined to the class's fully-qualified
-      -- in-module path, plus the import of that home module.
       return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
   return none
 -- impl-end
```

Attack 7 — `atk7_nomoduleprefix.lean` → rejected (same spec, does not verify — good)

```diff
@@ -80,20 +80,15 @@
 -- impl-start
 def implementation_serializeType (v : TypeRef) :
     Option (String × List String) := Id.run do
-  -- The constant special cases, checked in order before anything else.
   if v.isModelBase then
     return some ("models.Model", [])
   if v.isNoneType then
     return some ("type(None)", [])
-  -- A class with an observable home module.
   if v.hasModule then
     if v.module = builtinsModule then
-      -- Built-in namespace: the leaf name alone, no import.
       return some (v.shortName, [])
     else
-      -- Any other module: home module joined to the class's fully-qualified
-      -- in-module path, plus the import of that home module.
-      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
+      return some (v.fullName, ["import " ++ v.module])
   return none
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing the source-code reference string for a class/type value.

A serializer turns a class value into the pair `(reference, imports)` that
regenerated source can use to name that class again:

  * `reference` — the textual expression that re-denotes the class;
  * `imports`  — the set of import statements that expression needs.

The desired behavior, by the kind of class:

  * the framework's base model class is emitted as the constant literal
    `"models.Model"` with no import;
  * the null/`None` type is emitted as the constant literal `"type(None)"` with no
    import;
  * a class living in the language's built-in namespace is emitted by its
    unqualified leaf name alone, with no import;
  * any other class is emitted as its home module joined (with a dot) to the
    class's FULLY-QUALIFIED in-module path — the path that walks through every
    enclosing scope down to the class — together with the single import of that
    home module.

The last clause is the one that matters for a class declared inside another
class: the reference must spell the complete path through the enclosing
class(es), not merely the leaf name. Using the leaf name alone would denote a
sibling top-level class that does not exist, so the qualified path is required.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two
-- constant special cases, the built-in-namespace test, and the assembly of the
-- reference string from the home module and the class's leaf / fully-qualified
-- names are all modeled structurally over the class descriptor; no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A class/type value, restricted to the attributes the serializer observes.

* `isModelBase` — the value IS the framework's base model class (special case);
* `isNoneType`  — the value IS the null/`None` type (special case);
* `hasModule`   — a home module is observable for the value;
* `module`      — the home module's dotted name (e.g. `"app.models"`);
* `shortName`   — the class's unqualified leaf name (e.g. `"Inner"`);
* `fullName`    — the class's fully-qualified in-module path, threading through
  every enclosing scope (e.g. `"Outer.Inner"`; equal to `shortName` for a class
  declared at module top level). -/
structure TypeRef where
  isModelBase : Bool
  isNoneType : Bool
  hasModule : Bool
  module : String
  shortName : String
  fullName : String

/-- The name of the language's built-in namespace. -/
def builtinsModule : String := "builtins"
-- pure-end

-- post-conditions-start
/-- The serialized `(reference, imports)` for a class value, pinned for every
descriptor. The special cases are tried first (base model class, then null
type); a built-in-namespace class yields its leaf name with no import; any other
class yields `module ++ "." ++ fullName` with the single import of its home
module. A class with no observable home module produces no result (`none`). -/
def problem_spec_serializeType (v : TypeRef)
    (result : Option (String × List String)) : Prop :=
  result =
    (if v.isModelBase then some ("models.Model", [])
     else if v.isNoneType then some ("type(None)", [])
     else if v.hasModule then
       (if v.module = builtinsModule then some (v.shortName, [])
        else some (v.module ++ "." ++ v.fullName, ["import " ++ v.module]))
     else none)
-- post-conditions-end

-- impl-start
def implementation_serializeType (v : TypeRef) :
    Option (String × List String) := Id.run do
  -- The constant special cases, checked in order before anything else.
  if v.isModelBase then
    return some ("models.Model", [])
  if v.isNoneType then
    return some ("type(None)", [])
  -- A class with an observable home module.
  if v.hasModule then
    if v.module = builtinsModule then
      -- Built-in namespace: the leaf name alone, no import.
      return some (v.shortName, [])
    else
      -- Any other module: home module joined to the class's fully-qualified
      -- in-module path, plus the import of that home module.
      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
  return none
-- impl-end

-- proof-start
theorem correct_serializeType :
    ∀ (v : TypeRef),
      problem_spec_serializeType v (implementation_serializeType v) := by
  intro v
  unfold problem_spec_serializeType implementation_serializeType
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The spec is a FULL functional equality: problem_spec_serializeType v result := (result = <exact if-then-else over v>), pinning the unique correct Option value for every descriptor. Any verifying impl must be behaviorally identical to gold, so verify⇒correct holds. 

ATTACK PROTOCOL (all, byte-identical spec confirmed — same_spec True for all 8 files via python PYTHONPATH=src): 7 DISTINCT same-spec wrong impls (impl-region-only edits): atk1 prepatch bug (shortName in non-builtins branch), atk2 partial-domain (drop module handling, only special cases→none), atk3 boundary/order-swap (isNoneType before isModelBase), atk4 control-flow-effect (drop builtins check, always module.fullName), atk5 wrong-import ([] instead of ["import "++module]), atk6 boundary (flip builtins test = → !=), atk7 ungrounded (drop module prefix, emit bare fullName). 

COMMANDS: `bash scripts/lean_verify.sh <file>` from root. Ran with gold tactic AND a strengthened tactic (`split_ifs <;> simp_all <;> rfl`); batches run concurrently (≤4). RESULTS: all 7 attacks EXIT=1 (unsolved goals / rfl failed — genuine string/Option mismatch) under BOTH the gold tactic and the strong tactic. Positive control atk_pos.lean (=gold) EXIT=0. `#print axioms correct_serializeType` on atk_pos_ax.lean → depends on axioms: [propext] (clean, no sorryAx). 

Because NO attack's proof closes, there is no verifying-but-wrong impl to materialize a faithful patch for — no run_resolve needed for SOUND (protocol step 2 triggers only on a closing clean-axiom proof). 

To guard against 'the gold tactic is merely too weak', I also built atk1_disproof.lean proving `¬ ∀ v, problem_spec_serializeType v (implementation_serializeType v)` on the nested-class witness; it CLOSES (exit 0), confirming the prepatch impl genuinely violates the spec (prepatch_reproduced=true), not merely leaves it unproven. This is the FAIL_TO_PASS discriminator.

REFINEMENT.MD AUDIT (A-leg focus): axioms region is EMPTY (byte-identical in Solution/prepatch: 'No unchanged outside callee is consumed'). Solution.lean contains NO opaque/axiom. All 6 refinement legs are R/I (leg1 R input-carrier, legs2-3 I special cases, legs4-6 R module handling); NO A-consumed, NO A-reference, NO kind-3. The one changed read (__name__→__qualname__) is modeled DEEPLY as field fullName (SPEC_GUIDE §3 deeply-modeled changed read is never axiomatized) — correctly an R leg, not an A-reference. mapping.md symbol binding (serializer.py:258-272 @ base 89d41cba) verified against the worktree: base_commit code shows `__name__` on the last line (the bug); gold patch swaps to `__qualname__`. Correspondence holds; no A-leg to falsify. 

Verdict SOUND: ≥5 (7) distinct same-spec attacks run, none verifies; positive control verifies with clean axioms; spec is a full functional equality that provably rejects every behavioral divergence.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1_prepatch.lean`, `atk2_partial.lean`, `atk3_orderswap.lean`, `atk4_nobuiltins.lean`, `atk5_noimport.lean`, `atk6_flipbuiltin.lean`, `atk7_nomoduleprefix.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
Nested-class descriptor v = ⟨isModelBase=false, isNoneType=false, hasModule=true, module="app", shortName="Inner", fullName="Outer.Inner"⟩. Spec requires some ("app.Outer.Inner", ["import app"]) (module ++ "." ++ fullName, i.e. __qualname__); the prepatch bug produces some ("app.Inner", ["import app"]) (module ++ "." ++ shortName, i.e. __name__). Disproof atk1_disproof.lean closes (exit 0) proving problem_spec_serializeType is genuinely violated on this witness — this is exactly the FAIL_TO_PASS test_serialize_nested_class case (WriterTests.NestedEnum).
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2_partial.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3_orderswap.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4_nobuiltins.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5_noimport.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk6_flipbuiltin.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7_nomoduleprefix.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Producing the source-code reference string for a class/type value.

A serializer turns a class value into the pair `(reference, imports)` that
regenerated source can use to name that class again:

  * `reference` — the textual expression that re-denotes the class;
  * `imports`  — the set of import statements that expression needs.

The desired behavior, by the kind of class:

  * the framework's base model class is emitted as the constant literal
    `"models.Model"` with no import;
  * the null/`None` type is emitted as the constant literal `"type(None)"` with no
    import;
  * a class living in the language's built-in namespace is emitted by its
    unqualified leaf name alone, with no import;
  * any other class is emitted as its home module joined (with a dot) to the
    class's FULLY-QUALIFIED in-module path — the path that walks through every
    enclosing scope down to the class — together with the single import of that
    home module.

The last clause is the one that matters for a class declared inside another
class: the reference must spell the complete path through the enclosing
class(es), not merely the leaf name. Using the leaf name alone would denote a
sibling top-level class that does not exist, so the qualified path is required.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The two
-- constant special cases, the built-in-namespace test, and the assembly of the
-- reference string from the home module and the class's leaf / fully-qualified
-- names are all modeled structurally over the class descriptor; no
-- `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
/-- A class/type value, restricted to the attributes the serializer observes.

* `isModelBase` — the value IS the framework's base model class (special case);
* `isNoneType`  — the value IS the null/`None` type (special case);
* `hasModule`   — a home module is observable for the value;
* `module`      — the home module's dotted name (e.g. `"app.models"`);
* `shortName`   — the class's unqualified leaf name (e.g. `"Inner"`);
* `fullName`    — the class's fully-qualified in-module path, threading through
  every enclosing scope (e.g. `"Outer.Inner"`; equal to `shortName` for a class
  declared at module top level). -/
structure TypeRef where
  isModelBase : Bool
  isNoneType : Bool
  hasModule : Bool
  module : String
  shortName : String
  fullName : String

/-- The name of the language's built-in namespace. -/
def builtinsModule : String := "builtins"
-- pure-end

-- post-conditions-start
/-- The serialized `(reference, imports)` for a class value, pinned for every
descriptor. The special cases are tried first (base model class, then null
type); a built-in-namespace class yields its leaf name with no import; any other
class yields `module ++ "." ++ fullName` with the single import of its home
module. A class with no observable home module produces no result (`none`). -/
def problem_spec_serializeType (v : TypeRef)
    (result : Option (String × List String)) : Prop :=
  result =
    (if v.isModelBase then some ("models.Model", [])
     else if v.isNoneType then some ("type(None)", [])
     else if v.hasModule then
       (if v.module = builtinsModule then some (v.shortName, [])
        else some (v.module ++ "." ++ v.fullName, ["import " ++ v.module]))
     else none)
-- post-conditions-end

-- impl-start
def implementation_serializeType (v : TypeRef) :
    Option (String × List String) := Id.run do
  -- The constant special cases, checked in order before anything else.
  if v.isModelBase then
    return some ("models.Model", [])
  if v.isNoneType then
    return some ("type(None)", [])
  -- A class with an observable home module.
  if v.hasModule then
    if v.module = builtinsModule then
      -- Built-in namespace: the leaf name alone, no import.
      return some (v.shortName, [])
    else
      -- Any other module: home module joined to the class's fully-qualified
      -- in-module path, plus the import of that home module.
      return some (v.module ++ "." ++ v.fullName, ["import " ++ v.module])
  return none
-- impl-end

-- proof-start
theorem correct_serializeType :
    ∀ (v : TypeRef),
      problem_spec_serializeType v (implementation_serializeType v) := by
  intro v
  unfold problem_spec_serializeType implementation_serializeType
  simp only [Id.run, bind, pure]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS SOUND. The spec is a FULL functional equality: problem_spec_serializeType v result := (result = <exact if-then-else over v>), pinning the unique correct Option value for every descriptor. Any verifying impl must be behaviorally identical to gold, so verify⇒correct holds. 

ATTACK PROTOCOL (all, byte-identical spec confirmed — same_spec True for all 8 files via python PYTHONPATH=src): 7 DISTINCT same-spec wrong impls (impl-region-only edits): atk1 prepatch bug (shortName in non-builtins branch), atk2 partial-domain (drop module handling, only special cases→none), atk3 boundary/order-swap (isNoneType before isModelBase), atk4 control-flow-effect (drop builtins check, always module.fullName), atk5 wrong-import ([] instead of ["import "++module]), atk6 boundary (flip builtins test = → !=), atk7 ungrounded (drop module prefix, emit bare fullName). 

COMMANDS: `bash scripts/lean_verify.sh <file>` from root. Ran with gold tactic AND a strengthened tactic (`split_ifs <;> simp_all <;> rfl`); batches run concurrently (≤4). RESULTS: all 7 attacks EXIT=1 (unsolved goals / rfl failed — genuine string/Option mismatch) under BOTH the gold tactic and the strong tactic. Positive control atk_pos.lean (=gold) EXIT=0. `#print axioms correct_serializeType` on atk_pos_ax.lean → depends on axioms: [propext] (clean, no sorryAx). 

Because NO attack's proof closes, there is no verifying-but-wrong impl to materialize a faithful patch for — no run_resolve needed for SOUND (protocol step 2 triggers only on a closing clean-axiom proof). 

To guard against 'the gold tactic is merely too weak', I also built atk1_disproof.lean proving `¬ ∀ v, problem_spec_serializeType v (implementation_serializeType v)` on the nested-class witness; it CLOSES (exit 0), confirming the prepatch impl genuinely violates the spec (prepatch_reproduced=true), not merely leaves it unproven. This is the FAIL_TO_PASS discriminator.

REFINEMENT.MD AUDIT (A-leg focus): axioms region is EMPTY (byte-identical in Solution/prepatch: 'No unchanged outside callee is consumed'). Solution.lean contains NO opaque/axiom. All 6 refinement legs are R/I (leg1 R input-carrier, legs2-3 I special cases, legs4-6 R module handling); NO A-consumed, NO A-reference, NO kind-3. The one changed read (__name__→__qualname__) is modeled DEEPLY as field fullName (SPEC_GUIDE §3 deeply-modeled changed read is never axiomatized) — correctly an R leg, not an A-reference. mapping.md symbol binding (serializer.py:258-272 @ base 89d41cba) verified against the worktree: base_commit code shows `__name__` on the last line (the bug); gold patch swaps to `__qualname__`. Correspondence holds; no A-leg to falsify. 

Verdict SOUND: ≥5 (7) distinct same-spec attacks run, none verifies; positive control verifies with clean axioms; spec is a full functional equality that provably rejects every behavioral divergence.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-12125, modeled function TypeSerializer.serialize (django/db/migrations/serializer.py:258-272). No diverging input found — the spec faithfully models the real POST-PATCH callee on every realizable input.

### Evidence
1. same_spec (swebench_unified.markers, lean backend): True — spec regions (axioms/pure/pre/post) are byte-identical to the reference; also identical between Solution.lean and Solution_prepatch.lean (expected — the fix lives only in the impl region).
2. scripts/lean_verify.sh on Solution.lean: exit 0 (compiles, no sorry).
3. #print axioms correct_serializeType => depends on axioms: [propext] only. No sorryAx — the proof is genuine, not a stubbed/fake proof.
4. Base commit worktree @ 89d41cba39 confirms PRE-patch line 272 = "%s.%s" % (module, self.value.__name__); the patch changes __name__ -> __qualname__. The spec models the POST-patch behavior (module + '.' + fullName, fullName<->__qualname__).
5. conformance_check.py differential (shadow of implementation_serializeType vs faithful in-process replica of post-patch serialize): checked=120012, disagreements=0, status=pass. Covers all branches — special-case priority (model-base before none-type; model-base wins when both flags set), builtins branch (leaf name, empty imports), non-builtins branch (module.fullName + single import), and no-module -> None.

### Branch-by-branch faithfulness
- isModelBase -> ('models.Model', []) == special_cases[0] via `case is self.value`, set([])<->[].
- isNoneType -> ('type(None)', []) == special_cases[1], checked second (order preserved).
- hasModule & module='builtins' -> (shortName, []) == (self.value.__name__, set()); shortName<->__name__.
- hasModule & module!='builtins' -> (module++'.'++fullName, ['import '++module]) == ('%s.%s'%(module,__qualname__), {'import %s'%module}); fullName<->__qualname__, singleton list<->singleton set (at most one import, ordering irrelevant).
- not hasModule -> none == implicit `return None`.

The postcondition pins the FULL Option (String x List String) by exact equality for every descriptor, so it is not under-constrained; it is also not over-strong: for every input the modeled output equals the real post-patch output. The discriminating regime (non-builtins nested class, fullName != shortName) — precisely where a too-weak spec emitting shortName would be caught, and precisely the FAIL_TO_PASS test_serialize_nested_class case — is heavily sampled in the fuzzer and the spec correctly requires fullName there. G-AX legitimately skips (no consumed callee axiom; the changed read is modeled deeply as fullName, not axiomatized). No divergence between the modeled function and the real callee on any input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `self.value.__name__` -> `self.value.__qualname__` in the non-builtins branch of TypeSerializer.serialize, i.e. emit the fully-qualified in-module path (threading through enclosing classes) instead of the bare leaf name. The PUBLIC problem_statement already discloses precisely this: it shows makemigrations producing `test1.models.Inner`/`test1.models.State` when it 'should have been' `test1.models.Outer.Inner`/`test1.models.Thing.State` — i.e., the reference for a nested class must spell the complete path through the enclosing class(es), not merely the leaf name.

The spec view (problem_spec_serializeType + docstrings) states the non-builtins branch yields `module ++ "." ++ fullName` (FULLY-QUALIFIED path) and explains the last clause matters for a class declared inside another class ('the leaf name alone would denote a sibling top-level class that does not exist'). This is DERIVABLE from the public issue — it is faithful specification of the desired behavior, not disclosure beyond problem_statement. The other branches (base-model/None special cases, builtins leaf-name branch, none-for-no-module) are unchanged-behavior specification of the function under test, not the edit.

The spec view does NOT name the Python attribute rename (__name__/__qualname__ appear only in audit-support docs mapping.md/refinement.md, which are NOT part of the spec view), cites no file/line, and quotes no patch text. Mechanical G-LEAK screen: passed=True, hard_failures=[]. Verified same_spec(patched, prepatch)=True over the lean backend — the spec region is byte-identical, so the spec view does not itself carry the fix as a diff. No line leaks the gold edit beyond the public problem_statement (hints_text excluded from consideration).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
