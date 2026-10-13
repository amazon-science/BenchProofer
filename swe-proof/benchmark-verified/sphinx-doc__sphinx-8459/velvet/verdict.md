# P2 adversarial audit — sphinx-doc__sphinx-8459

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The only same-spec impls that VERIFY are (a) atk_6, the direct echo of the postcondition RHS `recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot`, which computes exactly the gold mapping — its faithful refined patch IS the gold patch and RESOLVED (executed, COMPLETED=True); and (b) two divergent `while true` loops (atk_1, atk_8) that satisfy the postcondition VACUOUSLY under `loom.semantics.termination "partial"`. The divergent loops are NOT valid G-EQ counterexamples: (1) they have no faithful refinement in mapping.md — A4 maps the bounded `while` fold ONLY to the finite `for param in sig.parameters.values()` iteration, so an unbounded loop has no map correspondent; and (2) their only honest materialization (`while True: pass`) HANGS. I executed that materialization through run_resolve and it returned COMPLETED=False (harness timed out, no report) — the runner's INCONCLUSIVE path (build_one.py:310-312), NOT the BROKEN path `r.completed and not r.resolved` (build_one.py:306). So no verifying wrong impl yields a completed-but-unresolved patch. Every TERMINATING wrong impl (prepatch `renderType []`, drop-return, wrong-order, skip-first boundary, clobber-to-[]) correctly FAILS to verify.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees and no deep-model reference to a library callee.
@@ -92,15 +92,13 @@
     recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
   do
     -- impl-start
-    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
+    let mut result : List (List Char × TypeStr) := []
     let mut i := params.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ params.length
       invariant result =
         recordedTypes (renderType aliases) (params.drop i)
-          ++ returnEntry (renderType aliases) retAnnot
       done_with i = 0
-      decreasing i
     do
       let p := params[i - 1]!
       result := paramEntry (renderType aliases) p ++ result
```

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees and no deep-model reference to a library callee.
@@ -92,20 +92,18 @@
     recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
   do
     -- impl-start
-    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
+    let mut result : List (List Char × TypeStr) := []
     let mut i := params.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ params.length
       invariant result =
         recordedTypes (renderType aliases) (params.drop i)
-          ++ returnEntry (renderType aliases) retAnnot
       done_with i = 0
-      decreasing i
     do
       let p := params[i - 1]!
       result := paramEntry (renderType aliases) p ++ result
       i := i - 1
-    return result
+    return returnEntry (renderType aliases) retAnnot ++ result
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the name at `i-1`
```

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees and no deep-model reference to a library callee.
@@ -92,18 +92,17 @@
     recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
   do
     -- impl-start
-    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
+    let mut result : List (List Char × TypeStr) := returnEntry (renderType []) retAnnot
     let mut i := params.length
     while i > 0
       invariant 0 ≤ i ∧ i ≤ params.length
       invariant result =
-        recordedTypes (renderType aliases) (params.drop i)
-          ++ returnEntry (renderType aliases) retAnnot
+        recordedTypes (renderType []) (params.drop i)
+          ++ returnEntry (renderType []) retAnnot
       done_with i = 0
-      decreasing i
     do
       let p := params[i - 1]!
-      result := paramEntry (renderType aliases) p ++ result
+      result := paramEntry (renderType []) p ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees and no deep-model reference to a library callee.
@@ -94,13 +94,12 @@
     -- impl-start
     let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
     let mut i := params.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ params.length
+    while i > 1
+      invariant 1 ≤ i ∧ i ≤ params.length
       invariant result =
         recordedTypes (renderType aliases) (params.drop i)
           ++ returnEntry (renderType aliases) retAnnot
-      done_with i = 0
-      decreasing i
+      done_with i = 1
     do
       let p := params[i - 1]!
       result := paramEntry (renderType aliases) p ++ result
```

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

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
 /- No axiomatized callees and no deep-model reference to a library callee.
@@ -92,20 +92,7 @@
     recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
   do
     -- impl-start
-    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
-    let mut i := params.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ params.length
-      invariant result =
-        recordedTypes (renderType aliases) (params.drop i)
-          ++ returnEntry (renderType aliases) retAnnot
-      done_with i = 0
-      decreasing i
-    do
-      let p := params[i - 1]!
-      result := paramEntry (renderType aliases) p ++ result
-      i := i - 1
-    return result
+    return recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the name at `i-1`
@@ -125,5 +112,3 @@
 
 prove_correct recordParamTypes by
   loom_solve
-  rw [recordedTypes_drop_step (renderType aliases) params i (by omega) (by omega)]
-  simp_all
```

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

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
 /- No axiomatized callees and no deep-model reference to a library callee.
@@ -100,11 +100,11 @@
         recordedTypes (renderType aliases) (params.drop i)
           ++ returnEntry (renderType aliases) retAnnot
       done_with i = 0
-      decreasing i
     do
       let p := params[i - 1]!
       result := paramEntry (renderType aliases) p ++ result
       i := i - 1
+    result := []
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees and no deep-model reference to a library callee.

   The operation that renders one source-level annotation into its display type
   string — resolving any configured type aliases and formatting the result — is
   an UNCHANGED sub-step. It is taken as a FREE INPUT `renderType` (a function of
   the configured alias map and the source annotation), so the spec makes no
   behavioural claim about it and holds for EVERY value of it. What this bundle
   pins is that the recorded type string for each name is produced by applying
   that renderer to the CONFIGURED alias map (not to an empty one) — modeled
   DEEPLY below. Nothing here needs validation against a real callee, so there is
   no module-level `axiom` and G-AX has nothing to check. -/
-- axioms-end

-- pure-start
/- The configured alias map: an ordered association of alias names to their
   replacement targets (mapping.md §2). Opaque to the spec — consulted only by
   the free renderer. -/
abbrev Aliases := List (List Char × List Char)

/- A source-level annotation and a rendered display type string are both carried
   as `List Char` (mapping.md §2). -/
abbrev SourceType := List Char
abbrev TypeStr := List Char

/- One signature entry: a name and, optionally, its source annotation. A `none`
   annotation marks an unannotated name. -/
structure Param where
  name  : List Char
  annot : Option SourceType
deriving DecidableEq, Inhabited

/- The recorded contribution of a single name: an unannotated name contributes
   nothing; an annotated one contributes the pair binding its name to the type
   string the renderer produces for its annotation. -/
def paramEntry (render : SourceType → TypeStr) (p : Param) :
    List (List Char × TypeStr) :=
  match p.annot with
  | some a => [(p.name, render a)]
  | none   => []

/- The recorded mapping for a whole sequence of names: concatenate the
   per-name contributions in order. Front-recursive so a single unfold is
   available per loop step (the backward-fold pattern). -/
def recordedTypes (render : SourceType → TypeStr) :
    List Param → List (List Char × TypeStr)
  | []      => []
  | p :: ps => paramEntry render p ++ recordedTypes render ps

@[grind] lemma recordedTypes_nil (render : SourceType → TypeStr) :
    recordedTypes render [] = [] := rfl
@[grind] lemma recordedTypes_cons (render : SourceType → TypeStr)
    (p : Param) (ps : List Param) :
    recordedTypes render (p :: ps) = paramEntry render p ++ recordedTypes render ps := rfl

/- The recorded contribution of the return annotation (under the constant
   `return` key), appended last: present iff a return annotation exists. -/
def returnEntry (render : SourceType → TypeStr) (ret : Option SourceType) :
    List (List Char × TypeStr) :=
  match ret with
  | some a => [("return".toList, render a)]
  | none   => []
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record the display type string of every annotated name in a callable's
   signature, plus its return annotation, into an ordered mapping.

   The renderer `renderType` turns a source annotation into a display string,
   given an alias map to resolve. The desired behaviour: each recorded string is
   the renderer applied to the CONFIGURED alias map `aliases` — so configured
   aliases take effect — for the names that carry an annotation, in order, with
   the return annotation recorded last. `params`, `retAnnot`, `aliases`, and the
   renderer `renderType` are read-only (directive 5). -/
method recordParamTypes (params : List Param) (retAnnot : Option SourceType)
    (aliases : Aliases) (renderType : Aliases → SourceType → TypeStr)
    return (out : List (List Char × TypeStr))
  ensures out =
    recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
  do
    -- impl-start
    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
    let mut i := params.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ params.length
      invariant result =
        recordedTypes (renderType aliases) (params.drop i)
          ++ returnEntry (renderType aliases) retAnnot
      done_with i = 0
    do
      let p := params[i - 1]!
      result := paramEntry (renderType aliases) p ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the name at `i-1`
   on the front, so `recordedTypes` peels one `paramEntry`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma recordedTypes_drop_step (render : SourceType → TypeStr) (ps : List Param) (i : Nat)
    (hi : 0 < i) (hle : i ≤ ps.length) :
    recordedTypes render (ps.drop (i - 1))
      = paramEntry render ps[i - 1]! ++ recordedTypes render (ps.drop i) := by
  have hlt : i - 1 < ps.length := by omega
  have hcons : ps.drop (i - 1) = ps[i - 1]! :: ps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, recordedTypes_cons]

prove_correct recordParamTypes by
  loom_solve
  rw [recordedTypes_drop_step (renderType aliases) params i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Commands
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." -> True for every atk_* and positive_control.
- verify: bash scripts/lean_verify.sh <file>
- resolve: python -m swebench_unified.harness.run_resolve via run_resolve(instance_id, patch, retries=0).

### ATTACK RESULTS (all same_spec=True):
| file | wrong-impl kind | verify exit | outcome |
|---|---|---|---|
| atk_2.lean | ungrounded/omission: drop the return entry (start `[]`) | 1 | REJECTED (ensures unsolved: `result_1 = recordedTypes... ++ returnEntry...`) GOOD |
| atk_3.lean | control-flow/order: return entry placed FIRST | 1 | REJECTED (ensures unsolved: `returnEntry... ++ result_1 = ...`) GOOD |
| atk_4.lean | prepatch bug: `renderType []` everywhere | 1 | REJECTED (invariant carries `renderType []`, cannot bridge to `renderType aliases`) GOOD — reproduces the prepatch defect |
| atk_5.lean | boundary/off-by-one: guard `i>1`, done_with `i=1` (skip first param) | 1 | REJECTED (invariant_1 unsolved: `1 <= params.length`) GOOD |
| atk_6.lean | ungrounded-oracle ECHO: `return <postcondition RHS>` directly | 0 (VERIFIES) | CANDIDATE -> faithful patch = gold -> run_resolve executed: RESOLVED=True, COMPLETED=True. Correct echo, NOT a weakness. |
| atk_7.lean | control-flow-effect: compute correctly, then `result := []` before return | 1 | REJECTED (ensures unsolved: `[] = recordedTypes... ++ returnEntry...`) GOOD |

### DIVERGENCE PROBES (NOT submitted as attacks — see counterexample):
| atk_1.lean | `while true do result := result` (proof: `loom_solve`) | 0 (VERIFIES vacuously) | partial-correctness artifact; no faithful refinement |
| atk_8.lean | `i := params.length+1; while i>0` never decreasing | 0 (VERIFIES vacuously) | same |
Executed the faithful divergent materialization (gold fix + `while True: pass`) via run_resolve(timeout=420): result COMPLETED=False, NOTE='no report ... harness error' = harness timeout on the hang => runner records INCONCLUSIVE, not BROKEN. Patch file This is the universal partial-correctness non-termination hole shared by every `termination "partial"` bundle; it does NOT satisfy the harness BROKEN criterion (`completed and not resolved`).

POSITIVE CONTROL: positive_control.lean = the shipped Solution.lean (backward-fold loop), verify exit 0 => spec non-vacuous.

REFINEMENT.md LEG AUDIT (A1-A6): A1/A2/A3 = R (type refinements); A4/A5/A6 = I (identical concrete ops, covered by G-CONF). NO A-consumed / A-reference legs (no axioms shipped) and NO kind-3. A3 models the two UNCHANGED renderer callees (`inspect.signature(obj, type_aliases=.)` + `typing.stringify`) as a UNIVERSALLY-QUANTIFIED free input `renderType`, strictly weaker than an axiom and cannot over-claim; correspondence to the real callees holds because the patch leaves them unchanged and mapping.md §3 binds them to `sphinx/util/inspect.py:471` + `sphinx/util/typing.py:278`. G-AX correctly skips (no axiom_check.py; sole `axiom` textual hit is inside a comment). The changed op (which alias map is passed) is expressed DIRECTLY via `renderType aliases`, so no inexpressible-changed-op leg exists. Model<->patch correspondence: `recordParamTypes` <-> `record_typehints` (typehints.py:23); the gold delta `inspect.signature(obj)` -> `inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)` is exactly the `renderType [] -> renderType aliases` discriminator.

CONCLUSION: SOUND. 7 same-spec attacks re-run (>=5 floor); prepatch bug reproduced (atk_4); positive control verifies. All terminating wrong impls fail to verify; the sole verifying wrong-shaped impl (atk_6) is a correct gold echo whose patch RESOLVED (executed). No verifying impl has a faithful refined patch that completes-and-does-not-resolve. Refinement legs all R/I, no kind-3, A-leg (free-input) correspondence holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_6.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The only same-spec impls that VERIFY are (a) atk_6, the direct echo of the postcondition RHS `recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot`, which computes exactly the gold mapping — its faithful refined patch IS the gold patch and RESOLVED (executed, COMPLETED=True); and (b) two divergent `while true` loops (atk_1, atk_8) that satisfy the postcondition VACUOUSLY under `loom.semantics.termination "partial"`. The divergent loops are NOT valid G-EQ counterexamples: (1) they have no faithful refinement in mapping.md — A4 maps the bounded `while` fold ONLY to the finite `for param in sig.parameters.values()` iteration, so an unbounded loop has no map correspondent; and (2) their only honest materialization (`while True: pass`) HANGS. I executed that materialization through run_resolve and it returned COMPLETED=False (harness timed out, no report) — the runner's INCONCLUSIVE path (build_one.py:310-312), NOT the BROKEN path `r.completed and not r.resolved` (build_one.py:306). So no verifying wrong impl yields a completed-but-unresolved patch. Every TERMINATING wrong impl (prepatch `renderType []`, drop-return, wrong-order, skip-first boundary, clobber-to-[]) correctly FAILS to verify.
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axiomatized callees and no deep-model reference to a library callee.

   The operation that renders one source-level annotation into its display type
   string — resolving any configured type aliases and formatting the result — is
   an UNCHANGED sub-step. It is taken as a FREE INPUT `renderType` (a function of
   the configured alias map and the source annotation), so the spec makes no
   behavioural claim about it and holds for EVERY value of it. What this bundle
   pins is that the recorded type string for each name is produced by applying
   that renderer to the CONFIGURED alias map (not to an empty one) — modeled
   DEEPLY below. Nothing here needs validation against a real callee, so there is
   no module-level `axiom` and G-AX has nothing to check. -/
-- axioms-end

-- pure-start
/- The configured alias map: an ordered association of alias names to their
   replacement targets (mapping.md §2). Opaque to the spec — consulted only by
   the free renderer. -/
abbrev Aliases := List (List Char × List Char)

/- A source-level annotation and a rendered display type string are both carried
   as `List Char` (mapping.md §2). -/
abbrev SourceType := List Char
abbrev TypeStr := List Char

/- One signature entry: a name and, optionally, its source annotation. A `none`
   annotation marks an unannotated name. -/
structure Param where
  name  : List Char
  annot : Option SourceType
deriving DecidableEq, Inhabited

/- The recorded contribution of a single name: an unannotated name contributes
   nothing; an annotated one contributes the pair binding its name to the type
   string the renderer produces for its annotation. -/
def paramEntry (render : SourceType → TypeStr) (p : Param) :
    List (List Char × TypeStr) :=
  match p.annot with
  | some a => [(p.name, render a)]
  | none   => []

/- The recorded mapping for a whole sequence of names: concatenate the
   per-name contributions in order. Front-recursive so a single unfold is
   available per loop step (the backward-fold pattern). -/
def recordedTypes (render : SourceType → TypeStr) :
    List Param → List (List Char × TypeStr)
  | []      => []
  | p :: ps => paramEntry render p ++ recordedTypes render ps

@[grind] lemma recordedTypes_nil (render : SourceType → TypeStr) :
    recordedTypes render [] = [] := rfl
@[grind] lemma recordedTypes_cons (render : SourceType → TypeStr)
    (p : Param) (ps : List Param) :
    recordedTypes render (p :: ps) = paramEntry render p ++ recordedTypes render ps := rfl

/- The recorded contribution of the return annotation (under the constant
   `return` key), appended last: present iff a return annotation exists. -/
def returnEntry (render : SourceType → TypeStr) (ret : Option SourceType) :
    List (List Char × TypeStr) :=
  match ret with
  | some a => [("return".toList, render a)]
  | none   => []
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Record the display type string of every annotated name in a callable's
   signature, plus its return annotation, into an ordered mapping.

   The renderer `renderType` turns a source annotation into a display string,
   given an alias map to resolve. The desired behaviour: each recorded string is
   the renderer applied to the CONFIGURED alias map `aliases` — so configured
   aliases take effect — for the names that carry an annotation, in order, with
   the return annotation recorded last. `params`, `retAnnot`, `aliases`, and the
   renderer `renderType` are read-only (directive 5). -/
method recordParamTypes (params : List Param) (retAnnot : Option SourceType)
    (aliases : Aliases) (renderType : Aliases → SourceType → TypeStr)
    return (out : List (List Char × TypeStr))
  ensures out =
    recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot
  do
    -- impl-start
    let mut result : List (List Char × TypeStr) := returnEntry (renderType aliases) retAnnot
    let mut i := params.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ params.length
      invariant result =
        recordedTypes (renderType aliases) (params.drop i)
          ++ returnEntry (renderType aliases) retAnnot
      done_with i = 0
    do
      let p := params[i - 1]!
      result := paramEntry (renderType aliases) p ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the name at `i-1`
   on the front, so `recordedTypes` peels one `paramEntry`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma recordedTypes_drop_step (render : SourceType → TypeStr) (ps : List Param) (i : Nat)
    (hi : 0 < i) (hle : i ≤ ps.length) :
    recordedTypes render (ps.drop (i - 1))
      = paramEntry render ps[i - 1]! ++ recordedTypes render (ps.drop i) := by
  have hlt : i - 1 < ps.length := by omega
  have hcons : ps.drop (i - 1) = ps[i - 1]! :: ps.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, recordedTypes_cons]

prove_correct recordParamTypes by
  loom_solve
  rw [recordedTypes_drop_step (renderType aliases) params i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

### Commands
- same_spec: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; ..." -> True for every atk_* and positive_control.
- verify: bash scripts/lean_verify.sh <file>
- resolve: python -m swebench_unified.harness.run_resolve via run_resolve(instance_id, patch, retries=0).

### ATTACK RESULTS (all same_spec=True):
| file | wrong-impl kind | verify exit | outcome |
|---|---|---|---|
| atk_2.lean | ungrounded/omission: drop the return entry (start `[]`) | 1 | REJECTED (ensures unsolved: `result_1 = recordedTypes... ++ returnEntry...`) GOOD |
| atk_3.lean | control-flow/order: return entry placed FIRST | 1 | REJECTED (ensures unsolved: `returnEntry... ++ result_1 = ...`) GOOD |
| atk_4.lean | prepatch bug: `renderType []` everywhere | 1 | REJECTED (invariant carries `renderType []`, cannot bridge to `renderType aliases`) GOOD — reproduces the prepatch defect |
| atk_5.lean | boundary/off-by-one: guard `i>1`, done_with `i=1` (skip first param) | 1 | REJECTED (invariant_1 unsolved: `1 <= params.length`) GOOD |
| atk_6.lean | ungrounded-oracle ECHO: `return <postcondition RHS>` directly | 0 (VERIFIES) | CANDIDATE -> faithful patch = gold -> run_resolve executed: RESOLVED=True, COMPLETED=True. Correct echo, NOT a weakness. |
| atk_7.lean | control-flow-effect: compute correctly, then `result := []` before return | 1 | REJECTED (ensures unsolved: `[] = recordedTypes... ++ returnEntry...`) GOOD |

### DIVERGENCE PROBES (NOT submitted as attacks — see counterexample):
| atk_1.lean | `while true do result := result` (proof: `loom_solve`) | 0 (VERIFIES vacuously) | partial-correctness artifact; no faithful refinement |
| atk_8.lean | `i := params.length+1; while i>0` never decreasing | 0 (VERIFIES vacuously) | same |
Executed the faithful divergent materialization (gold fix + `while True: pass`) via run_resolve(timeout=420): result COMPLETED=False, NOTE='no report ... harness error' = harness timeout on the hang => runner records INCONCLUSIVE, not BROKEN. Patch file This is the universal partial-correctness non-termination hole shared by every `termination "partial"` bundle; it does NOT satisfy the harness BROKEN criterion (`completed and not resolved`).

POSITIVE CONTROL: positive_control.lean = the shipped Solution.lean (backward-fold loop), verify exit 0 => spec non-vacuous.

REFINEMENT.md LEG AUDIT (A1-A6): A1/A2/A3 = R (type refinements); A4/A5/A6 = I (identical concrete ops, covered by G-CONF). NO A-consumed / A-reference legs (no axioms shipped) and NO kind-3. A3 models the two UNCHANGED renderer callees (`inspect.signature(obj, type_aliases=.)` + `typing.stringify`) as a UNIVERSALLY-QUANTIFIED free input `renderType`, strictly weaker than an axiom and cannot over-claim; correspondence to the real callees holds because the patch leaves them unchanged and mapping.md §3 binds them to `sphinx/util/inspect.py:471` + `sphinx/util/typing.py:278`. G-AX correctly skips (no axiom_check.py; sole `axiom` textual hit is inside a comment). The changed op (which alias map is passed) is expressed DIRECTLY via `renderType aliases`, so no inexpressible-changed-op leg exists. Model<->patch correspondence: `recordParamTypes` <-> `record_typehints` (typehints.py:23); the gold delta `inspect.signature(obj)` -> `inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)` is exactly the `renderType [] -> renderType aliases` discriminator.

CONCLUSION: SOUND. 7 same-spec attacks re-run (>=5 floor); prepatch bug reproduced (atk_4); positive control verifies. All terminating wrong impls fail to verify; the sole verifying wrong-shaped impl (atk_6) is a correct gold echo whose patch RESOLVED (executed). No verifying impl has a faithful refined patch that completes-and-does-not-resolve. Refinement legs all R/I, no kind-3, A-leg (free-input) correspondence holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-drift / too-strong) check for sphinx-doc__sphinx-8459 velvet.

Setup verified: (1) same_spec(Solution, Solution_prepatch)=True — spec view byte-identical, only impl differs. (2) Solution.lean verifies (lean_verify exit 0). (3) Solution_prepatch (renderType [] instead of renderType aliases) correctly FAILS the frozen spec (exit 1), confirming the ensures pins the discriminating behavior directionally.

Real-callee agreement: post-patch record_typehints (sphinx/ext/autodoc/typehints.py:23) matches the model op-for-op — ordered iteration over sig.parameters.values(), skip unannotated (param.empty↔none), record name→stringify(annotation), 'return' entry appended last, renderer called with type_aliases=app.config.autodoc_type_aliases. Renderer (inspect.signature+typing.stringify) is modeled as a UNIVERSALLY-QUANTIFIED free input renderType, strictly weaker than an axiom — the spec makes no over-claim about the unchanged callee, so it cannot be 'too strong' about it.

Empirical: ran conformance_check.py (seed 8459) against the gold-patched worktree copy (patch.diff applied, verified line 30) under a real sphinx env — G-CONF OK, 100000 inputs, 0 disagreements.

Only theoretical divergence: model uses list-append (keeps duplicates) vs real repo's OrderedDict (collapses duplicate keys incl. collision with 'return'). Proven UNREACHABLE through the real callee: Python raises SyntaxError for duplicate parameter names and for a param named 'return', so sig.parameters.values() can never yield colliding keys and no param key equals 'return'. On every input the real callee can produce, append and OrderedDict-insert coincide.

No diverging input found. Spec is faithful (not too strong, not drifted).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen (leakage.screen, velvet/lean flavor) PASSES: no diff markers, no reproduced gold-diff lines (>=8 chars normalized), no patched file path/module (sphinx/ext/autodoc/typehints.py absent from spec view), no spec-view identifier embedding the only distinctive patched symbol 'record_typehints', no bug/fix narration triggers. same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical).

Semantic assessment: gold edit is inspect.signature(obj) -> inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases). The consumer spec view abstracts everything: the renderer (inspect.signature + typing.stringify) is a universally-quantified FREE INPUT `renderType`; the alias map is opaque `Aliases`; the function is named `recordParamTypes` (not record_typehints). The callee names, the `type_aliases=` keyword, and the repo path appear ONLY in mapping.md/refinement.md (audit docs, not the screened spec view).

The one behavior-bearing content — ensures uses `renderType aliases` (configured map) not the empty map, with comments saying 'configured aliases take effect ... not to an empty one' — encodes the DESIRED behavior, which is already fully public in problem_statement ('autodoc_type_aliases doesn't work when autodoc_typehints is set to description'; expected: the configured alias honored in both modes). A spec must state desired behavior; that is not leakage of the edit's location or mechanism. The solver still must locate record_typehints, identify the inspect.signature callee, and construct the type_aliases= argument themselves — none of that repo localization is disclosed beyond the public problem statement. No leakage beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
