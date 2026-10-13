# P2 adversarial audit — django__django-17087

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -52,7 +52,8 @@
 -- impl-start
 def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
   let module := m.module
-  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
+  -- ATTACK: bare innermost name (prepatch bug)
+  let text := module ++ ".".toList ++ m.ownerName ++ ".".toList ++ m.methodName
   return { text := text, imports := [importFor module] }
 -- impl-end
 
@@ -61,5 +62,5 @@
     problem_spec_classMethodRef m (implementation_classMethodRef m) := by
   intro m
   unfold problem_spec_classMethodRef implementation_classMethodRef
-  refine ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;> first | rfl | simp | (try decide)
 -- proof-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,12 @@
 
 -- impl-start
 def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
+  -- ATTACK partial-domain: only correct when qualname==name
   let module := m.module
-  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
+  let text := if m.ownerQualname = m.ownerName then
+      module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
+    else
+      module ++ ".".toList ++ m.ownerName ++ ".".toList ++ m.methodName
   return { text := text, imports := [importFor module] }
 -- impl-end
 
@@ -61,5 +65,11 @@
     problem_spec_classMethodRef m (implementation_classMethodRef m) := by
   intro m
   unfold problem_spec_classMethodRef implementation_classMethodRef
-  refine ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | rfl
+      | simp
+      | (simp [importFor])
+      | decide
+      | (constructor <;> rfl)
 -- proof-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,9 @@
 
 -- impl-start
 def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
+  -- ATTACK boundary: missing dot before methodName
   let module := m.module
-  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
+  let text := module ++ ".".toList ++ m.ownerQualname ++ m.methodName
   return { text := text, imports := [importFor module] }
 -- impl-end
 
@@ -61,5 +62,11 @@
     problem_spec_classMethodRef m (implementation_classMethodRef m) := by
   intro m
   unfold problem_spec_classMethodRef implementation_classMethodRef
-  refine ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | rfl
+      | simp
+      | (simp [importFor])
+      | decide
+      | (constructor <;> rfl)
 -- proof-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,9 +51,9 @@
 
 -- impl-start
 def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
-  let module := m.module
-  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
-  return { text := text, imports := [importFor module] }
+  -- ATTACK control-flow: empty output
+  let _module := m.module
+  return { text := [], imports := [] }
 -- impl-end
 
 -- proof-start
@@ -61,5 +61,11 @@
     problem_spec_classMethodRef m (implementation_classMethodRef m) := by
   intro m
   unfold problem_spec_classMethodRef implementation_classMethodRef
-  refine ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | rfl
+      | simp
+      | (simp [importFor])
+      | decide
+      | (constructor <;> rfl)
 -- proof-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,9 @@
 
 -- impl-start
 def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
+  -- ATTACK ungrounded oracle: constant text
   let module := m.module
-  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
+  let text := "REF".toList
   return { text := text, imports := [importFor module] }
 -- impl-end
 
@@ -61,5 +62,11 @@
     problem_spec_classMethodRef m (implementation_classMethodRef m) := by
   intro m
   unfold problem_spec_classMethodRef implementation_classMethodRef
-  refine ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | rfl
+      | simp
+      | (simp [importFor])
+      | decide
+      | (constructor <;> rfl)
 -- proof-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,8 +51,9 @@
 
 -- impl-start
 def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
+  -- ATTACK: qualname/methodName swapped
   let module := m.module
-  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
+  let text := module ++ ".".toList ++ m.methodName ++ ".".toList ++ m.ownerQualname
   return { text := text, imports := [importFor module] }
 -- impl-end
 
@@ -61,5 +62,11 @@
     problem_spec_classMethodRef m (implementation_classMethodRef m) := by
   intro m
   unfold problem_spec_classMethodRef implementation_classMethodRef
-  refine ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | rfl
+      | simp
+      | (simp [importFor])
+      | decide
+      | (constructor <;> rfl)
 -- proof-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,9 +51,10 @@
 
 -- impl-start
 def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
+  -- ATTACK: correct text, missing import
   let module := m.module
   let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
-  return { text := text, imports := [importFor module] }
+  return { text := text, imports := [] }
 -- impl-end
 
 -- proof-start
@@ -61,5 +62,11 @@
     problem_spec_classMethodRef m (implementation_classMethodRef m) := by
   intro m
   unfold problem_spec_classMethodRef implementation_classMethodRef
-  refine ⟨rfl, rfl⟩
+  refine ⟨?_, ?_⟩ <;>
+    first
+      | rfl
+      | simp
+      | (simp [importFor])
+      | decide
+      | (constructor <;> rfl)
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: every datum the reference
-- string is built from (the defining module, the owning class's bare name and
-- its fully-qualified dotted name, and the method's own name) is an attribute
-- read, modeled directly as an input field. The string assembly is plain
-- concatenation, modeled deeply and checked mechanically. The proof agent may
-- add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A method object bound to a class (the case where the migration writer must
emit a dotted reference to a method that lives on a class). The four fields are
the data the reference is assembled from:
* `module`        — the dotted module path the owning class is defined in;
* `ownerName`     — the owning class's bare, innermost name;
* `ownerQualname` — the owning class's fully-qualified dotted name (for a class
  nested inside another class this includes the enclosing class names, e.g.
  `Outer.Inner`; for a top-level class it coincides with `ownerName`);
* `methodName`    — the method's own name. -/
structure BoundClassMethod where
  module : List Char
  ownerName : List Char
  ownerQualname : List Char
  methodName : List Char

/-- The assembled reference: the dotted reference string plus the import
statements it requires. -/
structure DottedRef where
  text : List Char
  imports : List (List Char)

/-- The single import statement needed to resolve a reference defined in
`module`. -/
def importFor (module : List Char) : List Char := "import ".toList ++ module
-- pure-end

-- post-conditions-start
/-- A reference to a class-bound method is the dotted path
`module . ownerQualname . methodName`, qualified by the owning class's FULLY
qualified name so that a method living on a class nested inside another class
resolves to its true location; together with the single import of the defining
module. Both result components are pinned to the inputs. -/
def problem_spec_classMethodRef (m : BoundClassMethod) (result : DottedRef) : Prop :=
  result.text =
      m.module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName ∧
  result.imports = [importFor m.module]
-- post-conditions-end

-- impl-start
def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
  let module := m.module
  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
  return { text := text, imports := [importFor module] }
-- impl-end

-- proof-start
theorem correct_classMethodRef : ∀ m : BoundClassMethod,
    problem_spec_classMethodRef m (implementation_classMethodRef m) := by
  intro m
  unfold problem_spec_classMethodRef implementation_classMethodRef
  refine ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-17087 (lean). Spec problem_spec_classMethodRef is a CONJUNCTION of two EXACT equalities pinning BOTH output fields to total functions of the inputs: result.text = module ++ "." ++ ownerQualname ++ "." ++ methodName AND result.imports = [importFor module]. Unique satisfying DottedRef per input — zero slack.

### Protocol results

same_spec via swebench_unified.markers.same_spec + get_backend('lean'): all 7 attacks == True (spec regions byte-identical; only impl+proof edited).

Positive control pos_control.lean (= gold Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` exit=0. Axioms: appended `#print axioms correct_classMethodRef` (pos_axcheck.lean) exit=0 -> "'correct_classMethodRef' does not depend on any axioms" (clean, no sorryAx).

Attacks (each built by copying Solution.lean, editing ONLY impl region + a strengthened generic proof closer `refine <_,_> <;> first | rfl | simp | simp[importFor] | decide | (constructor<;>rfl)`), verified concurrently (2 background batches of 4, `bash scripts/lean_verify.sh .../atk_N.lean`):
  atk_1 prepatch bug (ownerName instead of ownerQualname) -> exit=1, error: unsolved goals (line 62). PREPATCH REPRODUCED (same G-DIFF failure as Solution_prepatch.lean).
  atk_2 partial-domain (correct only when ownerQualname==ownerName, else ownerName) -> exit=1.
  atk_3 boundary (dropped dot separator before methodName) -> exit=1.
  atk_4 control-flow-effect (early return {text:=[], imports:=[]}) -> exit=1, unsolved goals (line 61).
  atk_5 ungrounded-oracle echo (text := constant "REF") -> exit=1.
  atk_6 field-order swap (methodName and ownerQualname positions swapped) -> exit=1.
  atk_7 wrong imports (correct text but imports := []) -> exit=1, unsolved goals (line 62).
All 7 fail with genuine "unsolved goals" (proof cannot equate the differing impl output to the spec-pinned value), NOT syntax errors.

Step 2 (materialize faithful patch + run_resolve): applies ONLY to wrong impls whose proof CLOSES with clean axioms. Zero of 7 closed => no faithful patch to materialize => patches={} (correctly, not evasion). This is not vacuous: the tight functional-equality spec provably admits a unique closing implementation (the qualname-qualified join + singleton import = the gold resolving behavior), so any verifying impl == gold behavior => resolves. verify => correct holds.

refinement.md A-leg audit: 5 legs tagged I, I, A-reference, A-reference, I — NO kind-3 (changed-inexpressible) leg; the sole changed token __name__->__qualname__ is captured by selecting the ownerQualname field. The two A-reference legs (the %-format dotted join "%s.%s.%s" and the import set {"import %s"%module}) are modeled DEEPLY as Lean char-list concatenation, NOT as opaque UNCHANGED-callee axiom signatures — the axioms region is EMPTY (no _prop axioms; #print axioms confirms zero axiom dependence). Their correspondence to the real post-patch callee (FunctionTypeSerializer.serialize class-bound-method branch) is validated differentially by conformance_check.py over 120k real Python class hierarchies incl. nested-class qualnames, seed 17087, independent reconstruction patched_branch(). No axiom backdoor / ungrounded-oracle reference exists to exploit. A-leg correspondence holds.

Minor non-blocking doc drift (already noted in verdict.md): mapping.md calls the result type SerializedRef while Solution.lean names it DottedRef — cosmetic only; frozen spec/impl/proof internally consistent and verify.

CONCLUSION: no same-spec implementation with a closing clean-axiom proof exists whose refined patch would fail to resolve. verify => correct. G-EQ = SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: every datum the reference
-- string is built from (the defining module, the owning class's bare name and
-- its fully-qualified dotted name, and the method's own name) is an attribute
-- read, modeled directly as an input field. The string assembly is plain
-- concatenation, modeled deeply and checked mechanically. The proof agent may
-- add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- A method object bound to a class (the case where the migration writer must
emit a dotted reference to a method that lives on a class). The four fields are
the data the reference is assembled from:
* `module`        — the dotted module path the owning class is defined in;
* `ownerName`     — the owning class's bare, innermost name;
* `ownerQualname` — the owning class's fully-qualified dotted name (for a class
  nested inside another class this includes the enclosing class names, e.g.
  `Outer.Inner`; for a top-level class it coincides with `ownerName`);
* `methodName`    — the method's own name. -/
structure BoundClassMethod where
  module : List Char
  ownerName : List Char
  ownerQualname : List Char
  methodName : List Char

/-- The assembled reference: the dotted reference string plus the import
statements it requires. -/
structure DottedRef where
  text : List Char
  imports : List (List Char)

/-- The single import statement needed to resolve a reference defined in
`module`. -/
def importFor (module : List Char) : List Char := "import ".toList ++ module
-- pure-end

-- post-conditions-start
/-- A reference to a class-bound method is the dotted path
`module . ownerQualname . methodName`, qualified by the owning class's FULLY
qualified name so that a method living on a class nested inside another class
resolves to its true location; together with the single import of the defining
module. Both result components are pinned to the inputs. -/
def problem_spec_classMethodRef (m : BoundClassMethod) (result : DottedRef) : Prop :=
  result.text =
      m.module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName ∧
  result.imports = [importFor m.module]
-- post-conditions-end

-- impl-start
def implementation_classMethodRef (m : BoundClassMethod) : DottedRef := Id.run do
  let module := m.module
  let text := module ++ ".".toList ++ m.ownerQualname ++ ".".toList ++ m.methodName
  return { text := text, imports := [importFor module] }
-- impl-end

-- proof-start
theorem correct_classMethodRef : ∀ m : BoundClassMethod,
    problem_spec_classMethodRef m (implementation_classMethodRef m) := by
  intro m
  unfold problem_spec_classMethodRef implementation_classMethodRef
  refine ⟨rfl, rfl⟩
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-17087 (lean). Spec problem_spec_classMethodRef is a CONJUNCTION of two EXACT equalities pinning BOTH output fields to total functions of the inputs: result.text = module ++ "." ++ ownerQualname ++ "." ++ methodName AND result.imports = [importFor module]. Unique satisfying DottedRef per input — zero slack.

### Protocol results

same_spec via swebench_unified.markers.same_spec + get_backend('lean'): all 7 attacks == True (spec regions byte-identical; only impl+proof edited).

Positive control pos_control.lean (= gold Solution.lean): `bash scripts/lean_verify.sh .../pos_control.lean` exit=0. Axioms: appended `#print axioms correct_classMethodRef` (pos_axcheck.lean) exit=0 -> "'correct_classMethodRef' does not depend on any axioms" (clean, no sorryAx).

Attacks (each built by copying Solution.lean, editing ONLY impl region + a strengthened generic proof closer `refine <_,_> <;> first | rfl | simp | simp[importFor] | decide | (constructor<;>rfl)`), verified concurrently (2 background batches of 4, `bash scripts/lean_verify.sh .../atk_N.lean`):
  atk_1 prepatch bug (ownerName instead of ownerQualname) -> exit=1, error: unsolved goals (line 62). PREPATCH REPRODUCED (same G-DIFF failure as Solution_prepatch.lean).
  atk_2 partial-domain (correct only when ownerQualname==ownerName, else ownerName) -> exit=1.
  atk_3 boundary (dropped dot separator before methodName) -> exit=1.
  atk_4 control-flow-effect (early return {text:=[], imports:=[]}) -> exit=1, unsolved goals (line 61).
  atk_5 ungrounded-oracle echo (text := constant "REF") -> exit=1.
  atk_6 field-order swap (methodName and ownerQualname positions swapped) -> exit=1.
  atk_7 wrong imports (correct text but imports := []) -> exit=1, unsolved goals (line 62).
All 7 fail with genuine "unsolved goals" (proof cannot equate the differing impl output to the spec-pinned value), NOT syntax errors.

Step 2 (materialize faithful patch + run_resolve): applies ONLY to wrong impls whose proof CLOSES with clean axioms. Zero of 7 closed => no faithful patch to materialize => patches={} (correctly, not evasion). This is not vacuous: the tight functional-equality spec provably admits a unique closing implementation (the qualname-qualified join + singleton import = the gold resolving behavior), so any verifying impl == gold behavior => resolves. verify => correct holds.

refinement.md A-leg audit: 5 legs tagged I, I, A-reference, A-reference, I — NO kind-3 (changed-inexpressible) leg; the sole changed token __name__->__qualname__ is captured by selecting the ownerQualname field. The two A-reference legs (the %-format dotted join "%s.%s.%s" and the import set {"import %s"%module}) are modeled DEEPLY as Lean char-list concatenation, NOT as opaque UNCHANGED-callee axiom signatures — the axioms region is EMPTY (no _prop axioms; #print axioms confirms zero axiom dependence). Their correspondence to the real post-patch callee (FunctionTypeSerializer.serialize class-bound-method branch) is validated differentially by conformance_check.py over 120k real Python class hierarchies incl. nested-class qualnames, seed 17087, independent reconstruction patched_branch(). No axiom backdoor / ungrounded-oracle reference exists to exploit. A-leg correspondence holds.

Minor non-blocking doc drift (already noted in verdict.md): mapping.md calls the result type SerializedRef while Solution.lean names it DottedRef — cosmetic only; frozen spec/impl/proof internally consistent and verify.

CONCLUSION: no same-spec implementation with a closing clean-axiom proof exists whose refined patch would fail to resolve. verify => correct. G-EQ = SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-17087 lean bundle: no divergence found; the modeled function agrees with the real post-patch callee on every input.

Modeled function: implementation_classMethodRef : BoundClassMethod -> DottedRef. Real callee: FunctionTypeSerializer.serialize, class-bound-method branch (django/db/migrations/serializer.py). Post-patch code returns "%s.%s.%s" % (module, klass.__qualname__, self.value.__name__), {"import %s" % module}.

Independent verification (not trusted from meta.json/verdict.md):
1. same_spec(Solution.lean, Solution_prepatch.lean, get_backend('lean')) = True -- spec region byte-identical; prepatch attacks the frozen spec.
2. lean_verify Solution.lean -> exit 0. #print axioms correct_classMethodRef -> 'does not depend on any axioms' (no sorryAx; proof is genuine, closes by refine <rfl, rfl>).
3. lean_verify Solution_prepatch.lean -> exit 1: rfl fails because impl uses m.ownerName while spec pins m.ownerQualname -- exactly the bug->fix delta (__name__ -> __qualname__), a correct discriminator.
4. Confirmed is at base_commit 4a72da71001f and its serializer uses klass.__name__ (line 171). instance.json gold patch confirms the sole edit is __name__ -> __qualname__.
5. conformance_check.py against REAL constructed CPython classes (incl. nested classes, real __qualname__/__module__/method __name__) over 120000 fuzzed inputs (seed 17087): G-CONF OK, 0 disagreements, exit 0.

Faithfulness reasoning (spec not too-strong, no drift):
- Model text = module ++ '.' ++ ownerQualname ++ '.' ++ methodName; imports = ['import ' ++ module]. Real string = module + '.' + klass.__qualname__ + '.' + value.__name__; real imports = {'import ' + module}. Field bijection maps ownerQualname<->__qualname__, methodName<->method __name__, module<->__module__. The dotted join is modeled deeply as char-list concat and matches the %-format exactly for all component values.
- The branch guard (getattr(__self__) truthy AND isinstance(__self__, type)) is a precondition selecting this branch; the modeled function has no precondition that excludes any real branch input, so it cannot be spec-too-strong by over-restricting the domain.
- The <locals> edge does not affect this branch: the '<' not in __qualname__ filter lives only in the later non-method branch; the class-bound branch emits __qualname__ verbatim, which the model reproduces.
- The imports set always has exactly one element on this branch, faithfully modeled as a singleton list (ordering/dedup moot).
- The unused ownerName field introduces no disagreement; it is only exercised by the prepatch discriminator.

No input found where the modeled DottedRef disagrees with the real post-patch serialize output. G-AX vacuous (empty axioms region, no A-consumed rows). Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no diff markers, no reproduced gold line, no patched file/module path, no spec-view identifier embedding the patched symbol 'serialize', no narration). Semantic check confirms no leak beyond the public problem_statement. The gold edit is klass.__name__ -> klass.__qualname__ in django/db/migrations/serializer.py (FunctionTypeSerializer.serialize). The consumer spec view (spec_view projection of Solution.lean) is an abstract model BoundClassMethod -> DottedRef with generic field names (module, ownerName, ownerQualname, methodName); it never names the patched file, the patched symbol, or the Python attributes __name__/__qualname__ (those live only in hints_text and the auditor-facing mapping.md/refinement.md, NOT in the spec view). The post-condition pins text = module . ownerQualname . methodName, i.e. the fully-qualified nested-class path — but the problem_statement itself already discloses this required behavior explicitly: wrong output 'appname.models.Capability.default' (bare innermost class name) vs correct 'appname.models.Profile.Capability.default' (full nested path). The ownerName-vs-ownerQualname contrast in the docstring is exactly the public wrong-vs-right distinction, so encoding it in the spec reveals nothing beyond the task. impl/proof regions are elided in the spec view. No leaking line found.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
