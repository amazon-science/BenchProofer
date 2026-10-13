# P2 adversarial audit — django__django-15161

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_1try.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition problem_spec_deconstructedPath fully pins `result` for every (simplifiedPath, isExactType): clause 1 forces result=p in the (some p, true) case; clause 2 forces result=qualifiedName objModule objClassName in every other case (none OR false). The two clauses are jointly exhaustive and deterministic, so the spec is a total function specification. Any impl differing from gold on any input makes the Prop genuinely false and thus unprovable — no verifying wrong impl exists, so verify⇒correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,14 +76,7 @@
 def implementation_deconstructedPath
     (simplifiedPath : Option String) (isExactType : Bool)
     (objModule objClassName : String) : String := Id.run do
-  match simplifiedPath with
-  | some p =>
-    if isExactType then
-      return p
-    else
-      return qualifiedName objModule objClassName
-  | none =>
-    return qualifiedName objModule objClassName
+  return qualifiedName objModule objClassName
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,8 @@
     (simplifiedPath : Option String) (isExactType : Bool)
     (objModule objClassName : String) : String := Id.run do
   match simplifiedPath with
-  | some p =>
-    if isExactType then
-      return p
-    else
-      return qualifiedName objModule objClassName
-  | none =>
-    return qualifiedName objModule objClassName
+  | some p => return p
+  | none => return qualifiedName objModule objClassName
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,12 +78,8 @@
     (objModule objClassName : String) : String := Id.run do
   match simplifiedPath with
   | some p =>
-    if isExactType then
-      return p
-    else
-      return qualifiedName objModule objClassName
-  | none =>
-    return qualifiedName objModule objClassName
+    if isExactType then return p else return objClassName ++ "." ++ objModule
+  | none => return objClassName ++ "." ++ objModule
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,12 +78,8 @@
     (objModule objClassName : String) : String := Id.run do
   match simplifiedPath with
   | some p =>
-    if isExactType then
-      return p
-    else
-      return qualifiedName objModule objClassName
-  | none =>
-    return qualifiedName objModule objClassName
+    if isExactType then return p else return qualifiedName objModule objClassName
+  | none => return ""
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,13 +77,8 @@
     (simplifiedPath : Option String) (isExactType : Bool)
     (objModule objClassName : String) : String := Id.run do
   match simplifiedPath with
-  | some p =>
-    if isExactType then
-      return p
-    else
-      return qualifiedName objModule objClassName
-  | none =>
-    return qualifiedName objModule objClassName
+  | some p => if isExactType then return p else return objModule
+  | none => return objModule
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -78,12 +78,8 @@
     (objModule objClassName : String) : String := Id.run do
   match simplifiedPath with
   | some p =>
-    if isExactType then
-      return p
-    else
-      return qualifiedName objModule objClassName
-  | none =>
-    return qualifiedName objModule objClassName
+    if isExactType then return qualifiedName objModule objClassName else return p
+  | none => return qualifiedName objModule objClassName
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_1try.lean` → rejected (same spec, does not verify — good)

```diff
@@ -76,14 +76,7 @@
 def implementation_deconstructedPath
     (simplifiedPath : Option String) (isExactType : Bool)
     (objModule objClassName : String) : String := Id.run do
-  match simplifiedPath with
-  | some p =>
-    if isExactType then
-      return p
-    else
-      return qualifiedName objModule objClassName
-  | none =>
-    return qualifiedName objModule objClassName
+  return qualifiedName objModule objClassName
 -- impl-end
 
 -- proof-start
@@ -94,21 +87,10 @@
         (implementation_deconstructedPath simplifiedPath isExactType objModule objClassName) := by
   intro simplifiedPath isExactType objModule objClassName
   unfold problem_spec_deconstructedPath implementation_deconstructedPath
-  constructor
-  · -- short path configured AND exact type ⇒ result = p
-    intro p hp hexact
-    subst hp
-    simp only [Id.run, hexact, if_true]
-    rfl
-  · -- otherwise ⇒ fully-qualified location
-    intro h
-    cases simplifiedPath with
-    | none => rfl
-    | some p =>
-      cases hexact : isExactType with
-      | true =>
-        rcases h with h | h
-        · exact absurd h (by simp)
-        · exact absurd h (by simp [hexact])
-      | false => rfl
+  refine ⟨?_, ?_⟩ <;> first
+    | (intro p hp hit; subst hp; simp_all [Id.run, pure]) <;> aesop
+    | (intro h; aesop)
+    | simp_all [Id.run, pure]
+    | aesop
+    | decide
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
When an expression object is serialized for a generated migration, it is reduced
to its canonical import path together with its reconstruction arguments. This
bundle models how that canonical import path is chosen.

Two things govern the choice:

  * `simplifiedPath` — an optional, explicitly configured short import path for
    the object's class (e.g. the public, top-level location from which the class
    is meant to be referenced). It may be absent.
  * `isExactType` — whether the object being serialized is an instance of
    exactly the class the short path was configured for (as opposed to a
    subclass, which must fall back to its own location).

The rule:

  * if a short import path is configured AND the object is of exactly that class,
    the canonical path is that configured short path;
  * otherwise the canonical path is the object's own fully-qualified location,
    namely its defining module joined to its class name.

Inputs:
  * `simplifiedPath` — the optional configured short import path;
  * `isExactType` — whether the object's runtime class is exactly the configured
    class;
  * `objModule` — the object's defining module (its fully-qualified module name);
  * `objClassName` — the object's class name.

The modeled value is the chosen canonical import path (the first component of the
serialization triple; the reconstruction arguments are unaffected by this choice
and are not modeled here).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The optional
-- configured short path enters as data (`Option String`), the exact-type
-- indicator enters as a `Bool`, and the object's module and class name enter as
-- plain `String`s. The only operation — selecting the configured short path or
-- else composing the fully-qualified location by joining module and class name
-- with a dot — is modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The object's fully-qualified location: its defining module joined to its
class name with a dot separator. This is the fallback canonical path used
whenever no configured short path applies. -/
def qualifiedName (objModule objClassName : String) : String :=
  objModule ++ "." ++ objClassName
-- pure-end

-- post-conditions-start
/-- The chosen canonical import path is fully pinned to the inputs:

  * when a short import path is configured and the object is of exactly the
    configured class, the result is precisely that configured short path;
  * otherwise (no short path configured, or the object is not of exactly that
    class) the result is precisely the object's fully-qualified location
    (`objModule` joined to `objClassName`).

The two cases are exhaustive in `(simplifiedPath, isExactType)`, so the result is
determined for every input — no output is left free. -/
def problem_spec_deconstructedPath
    (simplifiedPath : Option String) (isExactType : Bool)
    (objModule objClassName : String) (result : String) : Prop :=
  (∀ p, simplifiedPath = some p → isExactType = true →
      result = p) ∧
  ((simplifiedPath = none ∨ isExactType = false) →
      result = qualifiedName objModule objClassName)
-- post-conditions-end

-- impl-start
def implementation_deconstructedPath
    (simplifiedPath : Option String) (isExactType : Bool)
    (objModule objClassName : String) : String := Id.run do
  match simplifiedPath with
  | some p =>
    if isExactType then
      return p
    else
      return qualifiedName objModule objClassName
  | none =>
    return qualifiedName objModule objClassName
-- impl-end

-- proof-start
theorem correct_deconstructedPath :
    ∀ (simplifiedPath : Option String) (isExactType : Bool)
      (objModule objClassName : String),
      problem_spec_deconstructedPath simplifiedPath isExactType objModule objClassName
        (implementation_deconstructedPath simplifiedPath isExactType objModule objClassName) := by
  intro simplifiedPath isExactType objModule objClassName
  unfold problem_spec_deconstructedPath implementation_deconstructedPath
  constructor
  · -- short path configured AND exact type ⇒ result = p
    intro p hp hexact
    subst hp
    simp only [Id.run, hexact, if_true]
    rfl
  · -- otherwise ⇒ fully-qualified location
    intro h
    cases simplifiedPath with
    | none => rfl
    | some p =>
      cases hexact : isExactType with
      | true =>
        rcases h with h | h
        · exact absurd h (by simp)
        · exact absurd h (by simp [hexact])
      | false => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROJECT ROOT = (given /home path did not exist). HOME/ELAN env set per the audit protocol FSx-local rule.

SAME_SPEC: all 6 attacks + pos_control = True (only impl region edited; axioms/pure/pre/post byte-identical).

COMMANDS: `bash scripts/lean_verify.sh <file>`. Attacks 1-4 run concurrently (background jobs), then 5-6 concurrently; pos_control + atk_1try run sync.

### Results
- pos_control (exact gold impl): exit 0 (verifies, no sorry).
- atk_1 (prepatch bug: unconditional qualifiedName, ignores short path): exit 1.
- atk_2 (partial-domain: return p whenever some, ignores isExactType): exit 1.
- atk_3 (boundary: fallback join order swapped objClassName++"."++objModule): exit 1.
- atk_4 (control-flow-effect: none case returns ""): exit 1.
- atk_5 (ungrounded-oracle echo: return objModule only, drops class name): exit 1.
- atk_6 (inverted flag: qualifiedName when exact, p otherwise): exit 1.
- atk_1try (prepatch impl + MAXIMAL closing-proof attempt via simp_all/aesop/decide/first-combinator): exit 1; unsolved goal `qualifiedName objModule objClassName = p` — genuinely false for arbitrary p, so no closing proof exists (Lean soundness). This confirms the fully-pinned spec admits NO closing clean-axiom proof for any impl deviating from gold.

Step 2 (materialize+resolve faithful patch for every VERIFYING wrong impl) is VACUOUS: zero wrong impls verified, so there is no candidate patch to run through run_resolve. verify⇏correct falsification found no opening.

REFINEMENT.MD AUDIT: 4 legs, all tagged R (type-refinement). No A-consumed, no A-reference, no kind-3, no I ambiguity. meta.json axioms=[] and deep_model_references=[] (consistent); conf_skip=false; axiom_check.py is a skip stub (correct — no axioms). The only concrete computation (dot-join) is modeled DEEPLY as objModule ++ "." ++ objClassName, matching Python f'{obj.__class__.__module__}.{name}' in django/utils/deconstruct.py; path/exact-type/module/name enter as plain data. A-leg correspondence audit is vacuous (no A-legs). R-leg correspondence to the deconstruct closure `path if path and type(obj) is klass else f'{module}.{name}'` holds exactly. G-LEAK-neutral modeled name `deconstructedPath` shares no patched class/decorator substring.

prepatch_reproduced=true: Solution_prepatch.lean's impl (unconditional qualifiedName) === my atk_1; matches refinement.md's stated real bug (bare @deconstructible, path=None ⇒ guard always false ⇒ always fully-qualified path). Gold proof fails to typecheck against it (G-DIFF).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_1try.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. The postcondition problem_spec_deconstructedPath fully pins `result` for every (simplifiedPath, isExactType): clause 1 forces result=p in the (some p, true) case; clause 2 forces result=qualifiedName objModule objClassName in every other case (none OR false). The two clauses are jointly exhaustive and deterministic, so the spec is a total function specification. Any impl differing from gold on any input makes the Prop genuinely false and thus unprovable — no verifying wrong impl exists, so verify⇒correct holds.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_1try.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
When an expression object is serialized for a generated migration, it is reduced
to its canonical import path together with its reconstruction arguments. This
bundle models how that canonical import path is chosen.

Two things govern the choice:

  * `simplifiedPath` — an optional, explicitly configured short import path for
    the object's class (e.g. the public, top-level location from which the class
    is meant to be referenced). It may be absent.
  * `isExactType` — whether the object being serialized is an instance of
    exactly the class the short path was configured for (as opposed to a
    subclass, which must fall back to its own location).

The rule:

  * if a short import path is configured AND the object is of exactly that class,
    the canonical path is that configured short path;
  * otherwise the canonical path is the object's own fully-qualified location,
    namely its defining module joined to its class name.

Inputs:
  * `simplifiedPath` — the optional configured short import path;
  * `isExactType` — whether the object's runtime class is exactly the configured
    class;
  * `objModule` — the object's defining module (its fully-qualified module name);
  * `objClassName` — the object's class name.

The modeled value is the chosen canonical import path (the first component of the
serialization triple; the reconstruction arguments are unaffected by this choice
and are not modeled here).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The optional
-- configured short path enters as data (`Option String`), the exact-type
-- indicator enters as a `Bool`, and the object's module and class name enter as
-- plain `String`s. The only operation — selecting the configured short path or
-- else composing the fully-qualified location by joining module and class name
-- with a dot — is modeled directly below. Hence no `opaque`/`axiom` callee
-- contract is required.
-- axioms-end

-- pure-start
/-- The object's fully-qualified location: its defining module joined to its
class name with a dot separator. This is the fallback canonical path used
whenever no configured short path applies. -/
def qualifiedName (objModule objClassName : String) : String :=
  objModule ++ "." ++ objClassName
-- pure-end

-- post-conditions-start
/-- The chosen canonical import path is fully pinned to the inputs:

  * when a short import path is configured and the object is of exactly the
    configured class, the result is precisely that configured short path;
  * otherwise (no short path configured, or the object is not of exactly that
    class) the result is precisely the object's fully-qualified location
    (`objModule` joined to `objClassName`).

The two cases are exhaustive in `(simplifiedPath, isExactType)`, so the result is
determined for every input — no output is left free. -/
def problem_spec_deconstructedPath
    (simplifiedPath : Option String) (isExactType : Bool)
    (objModule objClassName : String) (result : String) : Prop :=
  (∀ p, simplifiedPath = some p → isExactType = true →
      result = p) ∧
  ((simplifiedPath = none ∨ isExactType = false) →
      result = qualifiedName objModule objClassName)
-- post-conditions-end

-- impl-start
def implementation_deconstructedPath
    (simplifiedPath : Option String) (isExactType : Bool)
    (objModule objClassName : String) : String := Id.run do
  match simplifiedPath with
  | some p =>
    if isExactType then
      return p
    else
      return qualifiedName objModule objClassName
  | none =>
    return qualifiedName objModule objClassName
-- impl-end

-- proof-start
theorem correct_deconstructedPath :
    ∀ (simplifiedPath : Option String) (isExactType : Bool)
      (objModule objClassName : String),
      problem_spec_deconstructedPath simplifiedPath isExactType objModule objClassName
        (implementation_deconstructedPath simplifiedPath isExactType objModule objClassName) := by
  intro simplifiedPath isExactType objModule objClassName
  unfold problem_spec_deconstructedPath implementation_deconstructedPath
  constructor
  · -- short path configured AND exact type ⇒ result = p
    intro p hp hexact
    subst hp
    simp only [Id.run, hexact, if_true]
    rfl
  · -- otherwise ⇒ fully-qualified location
    intro h
    cases simplifiedPath with
    | none => rfl
    | some p =>
      cases hexact : isExactType with
      | true =>
        rcases h with h | h
        · exact absurd h (by simp)
        · exact absurd h (by simp [hexact])
      | false => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROJECT ROOT = (given /home path did not exist). HOME/ELAN env set per the audit protocol FSx-local rule.

SAME_SPEC: all 6 attacks + pos_control = True (only impl region edited; axioms/pure/pre/post byte-identical).

COMMANDS: `bash scripts/lean_verify.sh <file>`. Attacks 1-4 run concurrently (background jobs), then 5-6 concurrently; pos_control + atk_1try run sync.

### Results
- pos_control (exact gold impl): exit 0 (verifies, no sorry).
- atk_1 (prepatch bug: unconditional qualifiedName, ignores short path): exit 1.
- atk_2 (partial-domain: return p whenever some, ignores isExactType): exit 1.
- atk_3 (boundary: fallback join order swapped objClassName++"."++objModule): exit 1.
- atk_4 (control-flow-effect: none case returns ""): exit 1.
- atk_5 (ungrounded-oracle echo: return objModule only, drops class name): exit 1.
- atk_6 (inverted flag: qualifiedName when exact, p otherwise): exit 1.
- atk_1try (prepatch impl + MAXIMAL closing-proof attempt via simp_all/aesop/decide/first-combinator): exit 1; unsolved goal `qualifiedName objModule objClassName = p` — genuinely false for arbitrary p, so no closing proof exists (Lean soundness). This confirms the fully-pinned spec admits NO closing clean-axiom proof for any impl deviating from gold.

Step 2 (materialize+resolve faithful patch for every VERIFYING wrong impl) is VACUOUS: zero wrong impls verified, so there is no candidate patch to run through run_resolve. verify⇏correct falsification found no opening.

REFINEMENT.MD AUDIT: 4 legs, all tagged R (type-refinement). No A-consumed, no A-reference, no kind-3, no I ambiguity. meta.json axioms=[] and deep_model_references=[] (consistent); conf_skip=false; axiom_check.py is a skip stub (correct — no axioms). The only concrete computation (dot-join) is modeled DEEPLY as objModule ++ "." ++ objClassName, matching Python f'{obj.__class__.__module__}.{name}' in django/utils/deconstruct.py; path/exact-type/module/name enter as plain data. A-leg correspondence audit is vacuous (no A-legs). R-leg correspondence to the deconstruct closure `path if path and type(obj) is klass else f'{module}.{name}'` holds exactly. G-LEAK-neutral modeled name `deconstructedPath` shares no patched class/decorator substring.

prepatch_reproduced=true: Solution_prepatch.lean's impl (unconditional qualifiedName) === my atk_1; matches refinement.md's stated real bug (bare @deconstructible, path=None ⇒ guard always false ⇒ always fully-qualified path). Gold proof fails to typecheck against it (G-DIFF).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Attacker role: faithfulness-break (spec too strong / drifts from real callee). Conclusion: FAITHFUL — no reachable input where the modeled function disagrees with the real repo callee.

### Verification performed
1. Spec byte-identity: same_spec(Solution.lean, Solution_prepatch.lean, lean_backend) = True. axioms/pure/post-conditions regions are identical across the patch; only impl+proof differ. Spec is genuinely fixed.
2. Lean compiles: scripts/lean_verify.sh exit 0. #print axioms correct_deconstructedPath => [propext] only. No sorryAx; proof is real.
3. Real callee = deconstruct closure in django/utils/deconstruct.py: `return path if path and type(obj) is klass else f'{obj.__class__.__module__}.{name}'`.

Probed the two faithfulness attack surfaces:
(a) Empty-string path with exact type. Real Python uses truthiness (`if path`), so @deconstructible(path='') exact-type returns the QUALIFIED name, not ''. Verified: empty path -> '__main__.Foo'. The Lean `some p` branch would demand result=p=''. BUT the documented abstraction (mapping.md bijection + conformance_check.py) maps a FALSY Python path (None OR '') to Lean `none`, and ONLY non-empty paths to `some p`. Under that abstraction map, '' -> none -> qualifiedName branch, which matches real code. `some ""` is outside the abstraction image; conformance harness correctly fuzzes `some` over non-empty strings only. No divergence on the abstracted domain.
(b) import_module/hasattr existence guard (can raise ValueError). Model omits it. On the actual reachable domain (six real expression classes with valid django.db.models.X paths) the guard always succeeds and returns `path` verbatim. Verified: exact+path Value -> 'django.db.models.Value'; subclass Sub -> '__main__.Sub'; bare -> '__main__.Bare'. Value-preserving no-op on modeled inputs.

All three branches confirmed empirically against the real callee: None-path -> qualified; non-empty valid path + exact -> path verbatim; non-exact/subclass -> qualified. The abstraction is total, consistent, documented, and G-CONF's fuzz domain matches it. No diverging input exists within the modeled domain.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean spec regions; impl/proof correctly elided) verified: same_spec(self,self)=True and spec_view sha256 matches recorded region_hashes.spec_view (d095cc8a...). The gold edit adds @deconstructible(path='django.db.models.X') to six expression classes (Func/Value/ExpressionWrapper/When/Case/OrderBy) in django/db/models/expressions.py; the public problem_statement already states the goal (use simplified public import paths for deconstruct of expressions; F()->django.db.models.F() vs django.db.models.expressions.F(); 'same technique can be applied to other expressions'). The spec view uses only neutral behavioral vocabulary (canonical import path / simplifiedPath / isExactType / objModule / objClassName / qualifiedName) and the neutral modeled-function name deconstructedPath. It NEVER names any of the six edited classes, NEVER mentions the deconstructible decorator, NEVER names expressions.py, and does NOT disclose the fix mechanism (adding a decorator) or which file/classes to change. The exact-type/subclass-fallback distinction is pre-existing deconstructible-framework behavior, not part of the gold diff. The modeled rule (select configured short path when configured+exact-type, else module.classname fully-qualified location) is exactly the behavior already public in problem_statement, revealing nothing beyond it. refinement.md/mapping.md do quote gold specifics (decorator, six class names, file:lines) but those are construction/audit-rationale artifacts, not the solver-visible spec view, so out of scope for the lexical leakage screen. hints_text excluded from baseline per instructions. No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
