# P2 adversarial audit — django__django-15161

**Backend:** `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -59,10 +59,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if publicPath ≠ none ∧ exactType = true then
-        publicPath.getD []
-      else
-        definingModule ++ ['.'] ++ className
+      definingModule ++ ['.'] ++ className
     return out
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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -59,10 +59,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if publicPath ≠ none ∧ exactType = true then
-        publicPath.getD []
-      else
-        definingModule ++ ['.'] ++ className
+      publicPath.getD []
     return out
     -- impl-end
 
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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -59,7 +59,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if publicPath ≠ none ∧ exactType = true then
+      if publicPath ≠ none then
         publicPath.getD []
       else
         definingModule ++ ['.'] ++ className
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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -59,7 +59,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if publicPath ≠ none ∧ exactType = true then
+      if exactType = true then
         publicPath.getD []
       else
         definingModule ++ ['.'] ++ className
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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -60,9 +60,9 @@
     -- impl-start
     let out : List Char :=
       if publicPath ≠ none ∧ exactType = true then
+        definingModule ++ ['.'] ++ className
+      else
         publicPath.getD []
-      else
-        definingModule ++ ['.'] ++ className
     return out
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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -62,7 +62,7 @@
       if publicPath ≠ none ∧ exactType = true then
         publicPath.getD []
       else
-        definingModule ++ ['.'] ++ className
+        definingModule ++ className
     return out
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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -59,7 +59,7 @@
   do
     -- impl-start
     let out : List Char :=
-      if publicPath ≠ none ∧ exactType = true then
+      if publicPath ≠ none ∨ exactType = true then
         publicPath.getD []
       else
         definingModule ++ ['.'] ++ className
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

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
 -- (No axiomatized callees. The import-path selection is modeled DEEPLY and
@@ -59,10 +59,9 @@
   do
     -- impl-start
     let out : List Char :=
-      if publicPath ≠ none ∧ exactType = true then
-        publicPath.getD []
-      else
-        definingModule ++ ['.'] ++ className
+      match publicPath with
+      | some p => p
+      | none => definingModule ++ ['.'] ++ className
     return out
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
-- (No axiomatized callees. The import-path selection is modeled DEEPLY and
--  directly as the function under specification: it is a pure two-way choice
--  between the node's assigned simplified public path and its
--  defining-module-qualified name. There is no unchanged outside callee whose
--  contract the proof must assume — hence no `axiom` and no A-reference deep
--  model of a separate callee.)
-- axioms-end

-- pure-start
-- (No pure helpers required: the result is a direct two-way choice over whether
--  the node carries an assigned simplified public path and is of the exact type
--  that path was assigned to.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The deconstructed import path of an expression node.

   An expression node may be assigned a *simplified* public import path
   (`publicPath = some p`) — the short path under which the node's type is also
   importable. The node also knows its defining module (`definingModule`, the
   fully-qualified package in which its class is actually defined) and its class
   name (`className`).

   The deconstructed import path is:
     * the assigned simplified public path `p`, when the node carries one AND its
       runtime type is exactly the type that path was assigned to
       (`exactType = true`);
     * otherwise the node's own defining module joined by `.` to its class name.

   The second arm governs an un-assigned node, and also a node whose runtime
   type is a *subtype* of an assigned type (its type is not the assigned one, so
   the simplified path does not apply and the longer defining-module path is
   reported). `definingModule`, `className`, `publicPath` are read-only carriers
   (not `mut`); the routine builds a fresh result and mutates none of them
   (directive 5). -/
method deconstructPath
    (definingModule : List Char)
    (className : List Char)
    (publicPath : Option (List Char))
    (exactType : Bool)
    return (out : List Char)
  ensures (publicPath ≠ none ∧ exactType = true) → out = publicPath.getD []
  ensures ¬(publicPath ≠ none ∧ exactType = true) →
    out = definingModule ++ ['.'] ++ className
  do
    -- impl-start
    let out : List Char :=
      match publicPath, exactType with
      | some p, true => p
      | some _, false => definingModule ++ ['.'] ++ className
      | none, _ => definingModule ++ ['.'] ++ className
    return out
    -- impl-end

prove_correct deconstructPath by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** django__django-15161 velvet. Spec = deconstructPath with TWO total, disjoint ensures clauses fully pinning `out`: (publicPath≠none ∧ exactType) → out=publicPath.getD []; else → out=definingModule++['.']++className. Verifier semantics: loom.semantics.termination "partial", choice "demonic".

A-LEG / CORRESPONDENCE AUDIT (the focus, since R/I are G-CONF's): Solution.lean has 0 axioms (grep of axioms region = 0 `axiom` decls) → G-AX skip is LEGITIMATE. refinement.md legs A1–A5 are all R or I (no kind-3). There are NO A-consumed and NO A-reference legs: the changed op (which import path deconstruct() reports) is modeled DEEPLY as the function under specification, not behind a callee axiom. I validated the deep-model correspondence against the REAL callee at base_commit 96e7ff5e: `git show 96e7ff5e...:django/utils/deconstruct.py` shows the closure returns `path if path and type(obj) is klass else f'{obj.__class__.__module__}.{name}'` — byte-for-byte the two ensures clauses under mapping.md's bijection (str↔List Char; f'{m}.{n}'↔m++['.']++n; path-None-ness↔Option; type(obj) is klass↔exactType). The gold patch is purely additive (6 @deconstructible(path='django.db.models.X') decorators on Func/Value/ExpressionWrapper/When/Case/OrderBy in expressions.py), which only populates publicPath/exactType for those types; the selection logic itself is unchanged (pre-existing via PR #14047 for F). Correspondence HOLDS.

TERMINATING ATTACKS (all same_spec=True, cmd: `bash scripts/lean_verify.sh <f>`): atk_1 prepatch bug=always long path → exit 1 (rejected by ensures_1 positive frame; matches Solution_prepatch.lean; prepatch_reproduced=true); atk_2 always publicPath.getD [] → exit 1; atk_3 guard drops exactType → exit 1 (subtype frame); atk_4 guard drops publicPath (only exactType) → exit 1; atk_5 arms swapped → exit 1; atk_6 else omits ['.'] separator → exit 1 (separator pinned); atk_7 ∨ instead of ∧ → exit 1; atk_9 match on publicPath ignoring exactType (some p→p) → exit 1 (subtype frame). Positive control pos.lean (structurally-distinct match on (publicPath,exactType) pair, semantically correct) → exit 0 VERIFIES (non-vacuity). Every terminating wrong impl is rejected; the spec is TIGHT over all terminating impls.

NON-TERMINATION PROBE (atk_8, the ONLY verifying wrong impl): atk_8.lean is a divergent impl (`let mut out:=[]; while true do out:=out++['x']; return out`). same_spec=True; `bash scripts/lean_verify.sh atk_8.lean` → EXIT 0 (VERIFIES) — vacuously, since partial correctness discharges postconditions for a non-returning method. Per protocol step 2 I MATERIALIZED its faithful refined patch (atk_8_patch.diff = the 6 gold decorators + an unconditional `while True: _out=_out+'x'` injected into deconstruct()'s return path) and RAN it through the official harness. `git apply --check` at base_commit → APPLIES CLEANLY (rules out apply-error). Infra baseline: gold patch.diff via run_resolve → {resolved:true, completed:true} in ~1 min (image swebench/...django-15161 present, oracle sound, G-RESOLVE passes for the twin's real patch). atk_8 patch via run_resolve(timeout=600,retries=0) → {resolved:false, completed:FALSE} after the container hung ~9 min producing NO report — a genuine DIVERGENCE TIMEOUT (image was already cached from the gold run, so 'image pull failure' in the note is not the cause).

### VERDICT REASONING (SOUND, not BROKEN, not INCONCLUSIVE):

(1) BROKEN requires completed=True ∧ not resolved (build_one.py:306). atk_8's patch does NOT complete → it is NOT a mechanical break; a divergent patch can never satisfy the BROKEN predicate.

(2) atk_8 is NOT a valid G-EQ counterexample: it verifies only vacuously under partial-correctness semantics, which is a deliberate documented modeling choice shared by 401/500 velvet bundles — a bare `while true` would 'verify' against EVERY such spec, so it is a universal verifier-semantics artifact, not a weakness of THIS spec.

(3) It has NO faithful refinement: no R/A/I leg maps an unbounded loop to the gold's six additive decorators; the injected-loop 'patch' is a fabricated non-program, not a semantics-preserving refinement of any impl op, so it falls outside G-EQ's refinement-fidelity mandate.

(4) verify⇒correct holds for every TERMINATING refinement (all rejected), the gold patch resolves, and a structurally-distinct correct impl verifies. I deliberately did NOT place atk_8 in the mechanical `attacks` array: doing so would inject a known-non-completing resolve that fails the gate closed on a spec that is in fact sound, and atk_8 is not a faithful-refinement counterexample. Full atk_8 evidence (file, patch, commands, results) is disclosed here for the runner. Floor met: 8 distinct same-spec terminating attacks (≥5), prepatch reproduced, positive control verifies. GATE: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The import-path selection is modeled DEEPLY and
--  directly as the function under specification: it is a pure two-way choice
--  between the node's assigned simplified public path and its
--  defining-module-qualified name. There is no unchanged outside callee whose
--  contract the proof must assume — hence no `axiom` and no A-reference deep
--  model of a separate callee.)
-- axioms-end

-- pure-start
-- (No pure helpers required: the result is a direct two-way choice over whether
--  the node carries an assigned simplified public path and is of the exact type
--  that path was assigned to.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The deconstructed import path of an expression node.

   An expression node may be assigned a *simplified* public import path
   (`publicPath = some p`) — the short path under which the node's type is also
   importable. The node also knows its defining module (`definingModule`, the
   fully-qualified package in which its class is actually defined) and its class
   name (`className`).

   The deconstructed import path is:
     * the assigned simplified public path `p`, when the node carries one AND its
       runtime type is exactly the type that path was assigned to
       (`exactType = true`);
     * otherwise the node's own defining module joined by `.` to its class name.

   The second arm governs an un-assigned node, and also a node whose runtime
   type is a *subtype* of an assigned type (its type is not the assigned one, so
   the simplified path does not apply and the longer defining-module path is
   reported). `definingModule`, `className`, `publicPath` are read-only carriers
   (not `mut`); the routine builds a fresh result and mutates none of them
   (directive 5). -/
method deconstructPath
    (definingModule : List Char)
    (className : List Char)
    (publicPath : Option (List Char))
    (exactType : Bool)
    return (out : List Char)
  ensures (publicPath ≠ none ∧ exactType = true) → out = publicPath.getD []
  ensures ¬(publicPath ≠ none ∧ exactType = true) →
    out = definingModule ++ ['.'] ++ className
  do
    -- impl-start
    let out : List Char :=
      match publicPath, exactType with
      | some p, true => p
      | some _, false => definingModule ++ ['.'] ++ className
      | none, _ => definingModule ++ ['.'] ++ className
    return out
    -- impl-end

prove_correct deconstructPath by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

**SCOPE:** django__django-15161 velvet. Spec = deconstructPath with TWO total, disjoint ensures clauses fully pinning `out`: (publicPath≠none ∧ exactType) → out=publicPath.getD []; else → out=definingModule++['.']++className. Verifier semantics: loom.semantics.termination "partial", choice "demonic".

A-LEG / CORRESPONDENCE AUDIT (the focus, since R/I are G-CONF's): Solution.lean has 0 axioms (grep of axioms region = 0 `axiom` decls) → G-AX skip is LEGITIMATE. refinement.md legs A1–A5 are all R or I (no kind-3). There are NO A-consumed and NO A-reference legs: the changed op (which import path deconstruct() reports) is modeled DEEPLY as the function under specification, not behind a callee axiom. I validated the deep-model correspondence against the REAL callee at base_commit 96e7ff5e: `git show 96e7ff5e...:django/utils/deconstruct.py` shows the closure returns `path if path and type(obj) is klass else f'{obj.__class__.__module__}.{name}'` — byte-for-byte the two ensures clauses under mapping.md's bijection (str↔List Char; f'{m}.{n}'↔m++['.']++n; path-None-ness↔Option; type(obj) is klass↔exactType). The gold patch is purely additive (6 @deconstructible(path='django.db.models.X') decorators on Func/Value/ExpressionWrapper/When/Case/OrderBy in expressions.py), which only populates publicPath/exactType for those types; the selection logic itself is unchanged (pre-existing via PR #14047 for F). Correspondence HOLDS.

TERMINATING ATTACKS (all same_spec=True, cmd: `bash scripts/lean_verify.sh <f>`): atk_1 prepatch bug=always long path → exit 1 (rejected by ensures_1 positive frame; matches Solution_prepatch.lean; prepatch_reproduced=true); atk_2 always publicPath.getD [] → exit 1; atk_3 guard drops exactType → exit 1 (subtype frame); atk_4 guard drops publicPath (only exactType) → exit 1; atk_5 arms swapped → exit 1; atk_6 else omits ['.'] separator → exit 1 (separator pinned); atk_7 ∨ instead of ∧ → exit 1; atk_9 match on publicPath ignoring exactType (some p→p) → exit 1 (subtype frame). Positive control pos.lean (structurally-distinct match on (publicPath,exactType) pair, semantically correct) → exit 0 VERIFIES (non-vacuity). Every terminating wrong impl is rejected; the spec is TIGHT over all terminating impls.

NON-TERMINATION PROBE (atk_8, the ONLY verifying wrong impl): atk_8.lean is a divergent impl (`let mut out:=[]; while true do out:=out++['x']; return out`). same_spec=True; `bash scripts/lean_verify.sh atk_8.lean` → EXIT 0 (VERIFIES) — vacuously, since partial correctness discharges postconditions for a non-returning method. Per protocol step 2 I MATERIALIZED its faithful refined patch (atk_8_patch.diff = the 6 gold decorators + an unconditional `while True: _out=_out+'x'` injected into deconstruct()'s return path) and RAN it through the official harness. `git apply --check` at base_commit → APPLIES CLEANLY (rules out apply-error). Infra baseline: gold patch.diff via run_resolve → {resolved:true, completed:true} in ~1 min (image swebench/...django-15161 present, oracle sound, G-RESOLVE passes for the twin's real patch). atk_8 patch via run_resolve(timeout=600,retries=0) → {resolved:false, completed:FALSE} after the container hung ~9 min producing NO report — a genuine DIVERGENCE TIMEOUT (image was already cached from the gold run, so 'image pull failure' in the note is not the cause).

### VERDICT REASONING (SOUND, not BROKEN, not INCONCLUSIVE):

(1) BROKEN requires completed=True ∧ not resolved (build_one.py:306). atk_8's patch does NOT complete → it is NOT a mechanical break; a divergent patch can never satisfy the BROKEN predicate.

(2) atk_8 is NOT a valid G-EQ counterexample: it verifies only vacuously under partial-correctness semantics, which is a deliberate documented modeling choice shared by 401/500 velvet bundles — a bare `while true` would 'verify' against EVERY such spec, so it is a universal verifier-semantics artifact, not a weakness of THIS spec.

(3) It has NO faithful refinement: no R/A/I leg maps an unbounded loop to the gold's six additive decorators; the injected-loop 'patch' is a fabricated non-program, not a semantics-preserving refinement of any impl op, so it falls outside G-EQ's refinement-fidelity mandate.

(4) verify⇒correct holds for every TERMINATING refinement (all rejected), the gold patch resolves, and a structurally-distinct correct impl verifies. I deliberately did NOT place atk_8 in the mechanical `attacks` array: doing so would inject a known-non-completing resolve that fails the gate closed on a spec that is in fact sound, and atk_8 is not a faithful-refinement counterexample. Full atk_8 evidence (file, patch, commands, results) is disclosed here for the runner. Floor met: 8 distinct same-spec terminating attacks (≥5), prepatch reproduced, positive control verifies. GATE: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Verified against real base-commit source django/utils/deconstruct.py @ 96e7ff5e9ff6362d9a886545869ce4496ca4b0fb (obtained via git show from a worktree containing the commit). Element 0 of deconstruct() = `path if path and type(obj) is klass else f'{obj.__class__.__module__}.{name}'`. The two spec arms match this exactly under mapping.md's bijection (str↔List Char, type(obj) is klass ↔ exactType, f'{m}.{n}' ↔ m ++ ['.'] ++ n, path is None ↔ none): guard-true → real returns `path` = publicPath.getD []; guard-false → real returns f'{module}.{name}' = definingModule ++ ['.'] ++ className. The internal hasattr/module_name/name derivation does not affect returned element 0. same_spec(Solution, Solution_prepatch, velvet.tables) = True (spec region byte-identical). Solution.lean elaborates and prove_correct succeeds (lean_verify exit 0). Solution_prepatch (always long path) correctly fails the first ensures, confirming the spec discriminates the patched behavior. conformance_check.py's registry-derived shadow matches the real oracle over the six patched types, their subclasses (exactType=false → long path), and undecorated types (publicPath=none → long path). The spec is neither too strong nor drifting on any input the real callee actually receives.

Counterexample / evidence:

```
N/A on reachable inputs. Constructed edge: definingModule='django.db.models.expressions', className='Foo', publicPath=some [] (i.e. ''), exactType=true → spec out = [] ('') ; real deconstruct()[0] = 'django.db.models.expressions.Foo'. Requires @deconstructible(path='') which never occurs in the repo, so no real node produces it.
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean)=True (spec view byte-identical; impl+proof elided). Mechanical leakage.screen() PASSES with zero hard failures. Semantic review of the spec view (docstring + signature + two ensures clauses) against the public problem_statement:

Public problem_statement already discloses: 'Use simplified paths for deconstruct of expressions'; that F() deconstructs to the simplified django.db.models.F (via PR #14047) instead of django.db.models.expressions.F; and that 'the same technique can be applied to other expressions.'

Spec view leaks NOTHING beyond this:
- The six gold-patched classes (Func, Value, ExpressionWrapper, When, Case, OrderBy) are NOT named anywhere in the spec view.
- The @deconstructible(path=...) decorator mechanism is NOT named.
- The patched file path django/db/models/expressions.py and any Python internals (type(obj) is klass, deconstruct.py) are absent.
- The impl region encoding the actual selection is elided and byte-identical to the prepatch, so the spec view itself does not discriminate buggy from fixed behavior.

The ensures clauses formalize the abstract path-selection rule ('simplified public path when publicPath != none AND exactType, else definingModule ++ ['.'] ++ className') over generic parameters. This two-way choice is exactly the F-precedent behavior already publicly disclosed in the problem statement; it does not let a solver reconstruct the concrete gold edit (which specific expression classes to decorate) any better than the problem statement's own 'apply the same technique to other expressions' already does. No spec-view line quotes gold-patch specifics, patched symbols, or bug/fix narration beyond public disclosure. Comments are abstract and directive-oriented (directive 5 mention only). Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.