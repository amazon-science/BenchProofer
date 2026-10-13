# P2 adversarial audit — django__django-14580

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is exact equality against a fully-pinned total function serializeSpec, so any verifying impl is pointwise equal to serializeSpec. The only two same-spec impls that verified (atk_5 = literal `serializeSpec v`; atk_7 = pure match producing identical outputs) are behaviorally identical to the gold, and their faithful refined patch = the gold fix, which RESOLVED under the official harness. No verify-but-not-resolve impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
   let specialCases : List (TypeVal × String × List String) :=
-    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
+    [ (TypeVal.baseModel, "models.Model", []),
       (TypeVal.noneType, "type(None)", []) ]
   for entry in specialCases do
     let (case, str, imports) := entry
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
       return (str, imports)
   match v with
   | .builtin name => return (name, [])
-  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
+  | .other module qualname => return (module ++ "." ++ qualname, [])
   | _ => return ("", [])
 -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
       return (str, imports)
   match v with
   | .builtin name => return (name, [])
-  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
+  | .other module qualname => return (module ++ "/" ++ qualname, ["import " ++ module])
   | _ => return ("", [])
 -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -47,17 +47,11 @@
 
 -- impl-start
 def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
-  let specialCases : List (TypeVal × String × List String) :=
-    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
-      (TypeVal.noneType, "type(None)", []) ]
-  for entry in specialCases do
-    let (case, str, imports) := entry
-    if sameType case v then
-      return (str, imports)
   match v with
+  | .baseModel => return ("models.Model", ["from django.db import models"])
+  | .noneType => return ("type(None)", ["from django.db import models"])
   | .builtin name => return (name, [])
   | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
-  | _ => return ("", [])
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,18 +46,8 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
-  let specialCases : List (TypeVal × String × List String) :=
-    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
-      (TypeVal.noneType, "type(None)", []) ]
-  for entry in specialCases do
-    let (case, str, imports) := entry
-    if sameType case v then
-      return (str, imports)
-  match v with
-  | .builtin name => return (name, [])
-  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
-  | _ => return ("", [])
+def implementation_serializeType (v : TypeVal) : String × List String :=
+  serializeSpec v
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -55,7 +55,7 @@
     if sameType case v then
       return (str, imports)
   match v with
-  | .builtin name => return (name, [])
+  | .builtin name => return (name, ["import " ++ name])
   | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
   | _ => return ("", [])
 -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -46,18 +46,12 @@
 -- post-conditions-end
 
 -- impl-start
-def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
-  let specialCases : List (TypeVal × String × List String) :=
-    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
-      (TypeVal.noneType, "type(None)", []) ]
-  for entry in specialCases do
-    let (case, str, imports) := entry
-    if sameType case v then
-      return (str, imports)
+def implementation_serializeType (v : TypeVal) : String × List String :=
   match v with
-  | .builtin name => return (name, [])
-  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
-  | _ => return ("", [])
+  | .baseModel => ("models.Model", ["from django.db import models"])
+  | .noneType => ("type(None)", [])
+  | .builtin name => (name, [])
+  | .other module qualname => (module ++ "." ++ qualname, ["import " ++ module])
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -48,7 +48,7 @@
 -- impl-start
 def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
   let specialCases : List (TypeVal × String × List String) :=
-    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
+    [ (TypeVal.baseModel, "models.model", ["from django.db import models"]),
       (TypeVal.noneType, "type(None)", []) ]
   for entry in specialCases do
     let (case, str, imports) := entry
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: serializing a type to its
-- source representation and the import statements that make that reference valid
-- is plain string manipulation over a small table of recognised kinds, modeled
-- DEEPLY below (no outside callee is consumed). The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An abstract view of a Python type object, carrying exactly the information
the serialization reads. A type is either one of the two specially-recognised
kinds, a built-in type (referenced by its bare name), or any other type
(referenced through its defining module and qualified name). -/
inductive TypeVal where
  | baseModel
  | noneType
  | builtin (name : String)
  | other (module qualname : String)
  deriving DecidableEq, BEq, Repr

/-- Identity comparison between a table entry and the value being serialized,
matching the reference-equality test used to recognise the special kinds. -/
def sameType (a b : TypeVal) : Bool := a == b

/-- Reference specification: the source representation of a type together with
the set of import statements required for that representation to be valid Python.
Modeled as an ordered list of import lines (each entry distinct; a set in the
real artifact). -/
def serializeSpec : TypeVal → String × List String
  | .baseModel => ("models.Model", ["from django.db import models"])
  | .noneType => ("type(None)", [])
  | .builtin name => (name, [])
  | .other module qualname => (module ++ "." ++ qualname, ["import " ++ module])
-- pure-end

-- post-conditions-start
/-- The result pairs the source text that references the given type with exactly
the import statements that make that text resolve. Every kind of type is pinned:
the two specially-recognised kinds and the built-in / module-qualified kinds each
map to their representation and the imports they require. -/
def problem_spec_serializeType (v : TypeVal) (result : String × List String) : Prop :=
  result = serializeSpec v
-- post-conditions-end

-- impl-start
def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
  let specialCases : List (TypeVal × String × List String) :=
    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
      (TypeVal.noneType, "type(None)", []) ]
  for entry in specialCases do
    let (case, str, imports) := entry
    if sameType case v then
      return (str, imports)
  match v with
  | .builtin name => return (name, [])
  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
  | _ => return ("", [])
-- impl-end

-- proof-start
theorem correct_serializeType : ∀ v : TypeVal,
    problem_spec_serializeType v (implementation_serializeType v) := by
  intro v
  cases v <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

AXIOMS/A-LEG AUDIT: axioms region is EMPTY (comment-only lines 4-10). meta.json opaque_callees/deep_model_references confirm no consumed axioms. refinement.md legs are all I (rows 1,3,5) or R (rows 2,4); NO A-consumed, NO A-reference, NO kind-3. The changed function is modeled DEEPLY via serializeSpec; no UNCHANGED callee is consumed as an axiom. Nothing for the A-leg attack surface to exploit — correspondence trivially holds (serializeSpec IS the modeled function).

SPEC SHAPE: problem_spec_serializeType v result := (result = serializeSpec v), i.e. exact equality vs a fully-pinned TOTAL function over the finite-constructor type TypeVal. Tightest possible spec: any verifying impl must be extensionally equal to serializeSpec on all TypeVal.

same_spec: all 8 attacks + pos_control returned True (swebench_unified.markers.same_spec, lean backend). Only impl region edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>.lean; run concurrently <=4):
- atk_1 PREPATCH BUG (baseModel emits [] not the import): exit 1 REJECTED -> prepatch G-DIFF reproduced.
- atk_2 partial-domain (.other drops import): exit 1 REJECTED.
- atk_3 boundary (.other uses '/' separator not '.'): exit 1 REJECTED.
- atk_4 control-flow-effect (noneType gets bogus 'from django.db import models' import): exit 1 REJECTED.
- atk_6 ungrounded/wrong builtin branch (builtin gets ['import '++name]): exit 1 REJECTED.
- atk_8 boundary (baseModel string lowercased 'models.model'): exit 1 REJECTED.
- atk_5 ungrounded-oracle ECHO (impl = `serializeSpec v` literally): exit 0 VERIFIES.
- atk_7 behaviorally-equivalent variant (pure match, same outputs, no Id.run): exit 0 VERIFIES.
- pos_control (gold impl verbatim): exit 0 VERIFIES.

#print axioms correct_serializeType (appended in *_ax.lean, re-verified exit 0):
- atk_5: 'does not depend on any axioms' (CLEAN).
- atk_7: 'does not depend on any axioms' (CLEAN).
- pos_control: 'depends on axioms: [propext]' (CLEAN — standard).

MANDATORY RESOLVE for every clean-axiom verifying impl: atk_5 and atk_7 are BOTH behaviorally identical to gold on every TypeVal branch (baseModel/noneType/builtin/other), so their single faithful refined Python patch is the gold fix (add ['from django.db import models'] to the models.Model special case). Executed: SBU_BENCHMARK=swe_bench_verified run_resolve('django__django-14580', faithful_patch, timeout=1200, retries=1) via docker. RESULT: RESOLVED=True, note='resolved'. (docker ps -> docker_ok confirmed first.)

CONCLUSION: 8 attacks run (6 wrong-behavior REJECTED as required; 2 behaviorally-gold-equivalent VERIFIED with clean axioms and their faithful patch RESOLVED). No same-spec impl verifies while its faithful patch fails to resolve. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The post-condition is exact equality against a fully-pinned total function serializeSpec, so any verifying impl is pointwise equal to serializeSpec. The only two same-spec impls that verified (atk_5 = literal `serializeSpec v`; atk_7 = pure match producing identical outputs) are behaviorally identical to the gold, and their faithful refined patch = the gold fix, which RESOLVED under the official harness. No verify-but-not-resolve impl exists.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: serializing a type to its
-- source representation and the import statements that make that reference valid
-- is plain string manipulation over a small table of recognised kinds, modeled
-- DEEPLY below (no outside callee is consumed). The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An abstract view of a Python type object, carrying exactly the information
the serialization reads. A type is either one of the two specially-recognised
kinds, a built-in type (referenced by its bare name), or any other type
(referenced through its defining module and qualified name). -/
inductive TypeVal where
  | baseModel
  | noneType
  | builtin (name : String)
  | other (module qualname : String)
  deriving DecidableEq, BEq, Repr

/-- Identity comparison between a table entry and the value being serialized,
matching the reference-equality test used to recognise the special kinds. -/
def sameType (a b : TypeVal) : Bool := a == b

/-- Reference specification: the source representation of a type together with
the set of import statements required for that representation to be valid Python.
Modeled as an ordered list of import lines (each entry distinct; a set in the
real artifact). -/
def serializeSpec : TypeVal → String × List String
  | .baseModel => ("models.Model", ["from django.db import models"])
  | .noneType => ("type(None)", [])
  | .builtin name => (name, [])
  | .other module qualname => (module ++ "." ++ qualname, ["import " ++ module])
-- pure-end

-- post-conditions-start
/-- The result pairs the source text that references the given type with exactly
the import statements that make that text resolve. Every kind of type is pinned:
the two specially-recognised kinds and the built-in / module-qualified kinds each
map to their representation and the imports they require. -/
def problem_spec_serializeType (v : TypeVal) (result : String × List String) : Prop :=
  result = serializeSpec v
-- post-conditions-end

-- impl-start
def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
  let specialCases : List (TypeVal × String × List String) :=
    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
      (TypeVal.noneType, "type(None)", []) ]
  for entry in specialCases do
    let (case, str, imports) := entry
    if sameType case v then
      return (str, imports)
  match v with
  | .builtin name => return (name, [])
  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
  | _ => return ("", [])
-- impl-end

-- proof-start
theorem correct_serializeType : ∀ v : TypeVal,
    problem_spec_serializeType v (implementation_serializeType v) := by
  intro v
  cases v <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

AXIOMS/A-LEG AUDIT: axioms region is EMPTY (comment-only lines 4-10). meta.json opaque_callees/deep_model_references confirm no consumed axioms. refinement.md legs are all I (rows 1,3,5) or R (rows 2,4); NO A-consumed, NO A-reference, NO kind-3. The changed function is modeled DEEPLY via serializeSpec; no UNCHANGED callee is consumed as an axiom. Nothing for the A-leg attack surface to exploit — correspondence trivially holds (serializeSpec IS the modeled function).

SPEC SHAPE: problem_spec_serializeType v result := (result = serializeSpec v), i.e. exact equality vs a fully-pinned TOTAL function over the finite-constructor type TypeVal. Tightest possible spec: any verifying impl must be extensionally equal to serializeSpec on all TypeVal.

same_spec: all 8 attacks + pos_control returned True (swebench_unified.markers.same_spec, lean backend). Only impl region edited; axioms/pure/pre/post byte-identical.

### VERIFY RESULTS (bash scripts/lean_verify.sh <f>.lean; run concurrently <=4):
- atk_1 PREPATCH BUG (baseModel emits [] not the import): exit 1 REJECTED -> prepatch G-DIFF reproduced.
- atk_2 partial-domain (.other drops import): exit 1 REJECTED.
- atk_3 boundary (.other uses '/' separator not '.'): exit 1 REJECTED.
- atk_4 control-flow-effect (noneType gets bogus 'from django.db import models' import): exit 1 REJECTED.
- atk_6 ungrounded/wrong builtin branch (builtin gets ['import '++name]): exit 1 REJECTED.
- atk_8 boundary (baseModel string lowercased 'models.model'): exit 1 REJECTED.
- atk_5 ungrounded-oracle ECHO (impl = `serializeSpec v` literally): exit 0 VERIFIES.
- atk_7 behaviorally-equivalent variant (pure match, same outputs, no Id.run): exit 0 VERIFIES.
- pos_control (gold impl verbatim): exit 0 VERIFIES.

#print axioms correct_serializeType (appended in *_ax.lean, re-verified exit 0):
- atk_5: 'does not depend on any axioms' (CLEAN).
- atk_7: 'does not depend on any axioms' (CLEAN).
- pos_control: 'depends on axioms: [propext]' (CLEAN — standard).

MANDATORY RESOLVE for every clean-axiom verifying impl: atk_5 and atk_7 are BOTH behaviorally identical to gold on every TypeVal branch (baseModel/noneType/builtin/other), so their single faithful refined Python patch is the gold fix (add ['from django.db import models'] to the models.Model special case). Executed: SBU_BENCHMARK=swe_bench_verified run_resolve('django__django-14580', faithful_patch, timeout=1200, retries=1) via docker. RESULT: RESOLVED=True, note='resolved'. (docker ps -> docker_ok confirmed first.)

CONCLUSION: 8 attacks run (6 wrong-behavior REJECTED as required; 2 behaviorally-gold-equivalent VERIFIED with clean axioms and their faithful patch RESOLVED). No same-spec impl verifies while its faithful patch fails to resolve. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14580 lean bundle.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean, lean) = True. Frozen spec region (TypeVal, sameType, serializeSpec, problem_spec_serializeType) byte-identical; only impl table ([] -> ['from django.db import models']) and proof (sorry -> `cases v <;> rfl`) differ. Correct G-DIFF discriminant on v=.baseModel.
- lean_verify.sh exit 0; `#print axioms correct_serializeType` = [propext] only. No sorryAx -> proof is genuine, not fake.

Spec vs real repo (base_commit 36fa071d + gold patch, checked against source):
Real TypeSerializer.serialize branches map exactly to serializeSpec:
  - models.Model (identity)  -> ('models.Model', {'from django.db import models'})  == .baseModel
  - type(None)               -> ('type(None)', set())                              == .noneType
  - __module__==builtins     -> (__name__, set())                                  == .builtin name
  - else                     -> ('%s.%s'%(module,qualname), {'import %s'%module})  == .other module qualname

Conformance oracle-vs-shadow: ran conformance_check.py against the actually-patched Django code: 120000 inputs, 0 disagreements (seed 14580). Also hand-probed models.Model, type(None), int/str/object, TextField/CharField, Exception, nested-class qualname — all agree.

Totality boundary is faithful, not over-strong: the real function has an implicit None fall-through only when NOT hasattr(value,'__module__'); confirmed every real Python type object has __module__, so that path is unreachable. The bijection (mapping.md) restricts inputs to real type objects, so the Lean total-function placeholder `_ => ("", [])` never corresponds to any real input and cannot manufacture a spurious agreement. No string-collision divergence: real code tests identity BEFORE the module/qualname fallback, matching sameType-first ordering; e.g. .other "models" "Model" -> ('models.Model', {'import models'}) differs from the special case in both spec and repo.

The spec does not drift from or over-constrain the real callee on any input in the modeled domain. No diverging input exists.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = single line: the models.Model special-case triple's import list [] -> ['from django.db import models'] in django/db/migrations/serializer.py.

Spec view (rendered via markers.spec_view): imports/axioms/pure/post-conditions regions visible; impl-start and proof-start elided ('supplied by the consumer'). same_spec(Solution, prepatch)=True; mechanical G-LEAK screen passes (no hard_failures, no diff markers, no patched file path 'serializer.py', no bug/fix narration in comments, no patched-symbol echo).

The spec view pins serializeSpec .baseModel => ("models.Model", ["from django.db import models"]) — i.e. the post-patch behavior. Judged against the PUBLIC problem_statement (NOT hints_text), this discloses nothing beyond what the solver already sees: the problem_statement literally contains the string 'models.Model', the literal import line 'from django.db import models', and explicitly states the bug is a 'missing import statement' causing NameError: name 'models' is not defined. So a solver already knows the required behavior is 'serializing models.Model must attach the from-django.db-import-models import.' The spec merely encodes that correct behavior (its legitimate job); it adds no incremental edit-localization.

The fix-narrating text ('changed from [] to [...]', 'prepatch impl emits', 'G-DIFF signal') lives ONLY in refinement.md / mapping.md — auditor/build artifacts, not the solver-visible spec_view — so it is out of scope for G-PANEL-3.

Conclusion: no leakage of the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
