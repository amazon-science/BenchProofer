# P2 adversarial audit — pytest-dev__pytest-6197

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is an exact functional equality over a total (precondition-free) domain: out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries AND out.2 = false. Any verifying impl is forced to compute the identical function; there is no admitted slack for a wrong-but-verifying impl.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,16 +69,13 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
     let mut collected : List Nat := []
     if initMatches then
       collected := collected ++ [initNode]
     collected := entries.foldl
       (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
       collected
-    return (collected, false)
+    return (collected, true)
     -- impl-end
 
 /- The fold accumulating child items equals the accumulator followed by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,12 +69,7 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
     let mut collected : List Nat := []
-    if initMatches then
-      collected := collected ++ [initNode]
     collected := entries.foldl
       (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
       collected
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,14 +69,11 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
     let mut collected : List Nat := []
     if initMatches then
       collected := collected ++ [initNode]
     collected := entries.foldl
-      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
+      (fun acc e => if !e.isFile then acc else acc ++ e.yields)
       collected
     return (collected, false)
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,14 +69,11 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
     let mut collected : List Nat := []
     if initMatches then
       collected := collected ++ [initNode]
     collected := entries.foldl
-      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
+      (fun acc e => if e.boundary then acc else acc ++ e.yields)
       collected
     return (collected, false)
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,14 +69,11 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
     let mut collected : List Nat := []
     if initMatches then
       collected := collected ++ [initNode]
     collected := entries.foldl
-      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
+      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields ++ e.yields)
       collected
     return (collected, false)
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,15 +69,10 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
     let mut collected : List Nat := []
     if initMatches then
       collected := collected ++ [initNode]
-    collected := entries.foldl
-      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
-      collected
+    -- BUG: never walk the entries; correct only when the walk yields nothing
     return (collected, false)
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,14 +69,11 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
     let mut collected : List Nat := []
     if initMatches then
       collected := collected ++ [initNode]
-    collected := entries.foldl
-      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
+    collected := entries.foldr
+      (fun e acc => (if e.boundary || !e.isFile then [] else e.yields) ++ acc)
       collected
     return (collected, false)
     -- impl-end
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -69,16 +69,8 @@
   ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
   do
     -- impl-start
-    -- Walk the enumerated paths and gather the child items; the directory's
-    -- own initialization file is never loaded during the walk (the loaded
-    -- flag reported is false).
-    let mut collected : List Nat := []
-    if initMatches then
-      collected := collected ++ [initNode]
-    collected := entries.foldl
-      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
-      collected
-    return (collected, false)
+    -- Ungrounded oracle echo: return the spec's RHS verbatim.
+    return ((if initMatches then [initNode] else []) ++ walkEntries entries, false)
     -- impl-end
 
 /- The fold accumulating child items equals the accumulator followed by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-path resolution of a regular file to the
--  child items it contributes is an orthogonal, unchanged operation whose
--  result enters as plain input data (the `yields` field of each enumerated
--  entry); whether a path lies on the enumeration boundary enters as a plain
--  Boolean observation. No opaque/axiom callee contract is needed.)
-- axioms-end

-- pure-start
/- One enumerated path of a directory tree, reduced to what content
   enumeration consumes:

   * `boundary` — the path contributes nothing to this directory's own
     enumeration (it is the directory's own initialization file, or it already
     sits inside a nested sub-directory that has been accounted for);
   * `isFile` — the path is a regular file (as opposed to a directory);
   * `yields` — the child items a non-boundary regular file resolves to. -/
structure PkgEntry where
  boundary : Bool
  isFile : Bool
  yields : List Nat
  deriving Inhabited, DecidableEq

/- The child items produced by walking the enumerated paths front-to-back:
   a boundary path or a directory contributes nothing; a non-boundary regular
   file contributes the items it resolves to. -/
def walkEntries : List PkgEntry → List Nat
  | [] => []
  | e :: es => (if e.boundary || !e.isFile then [] else e.yields) ++ walkEntries es
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Enumerating the contents of a directory that carries an initialization file.

   The enumeration walks the directory tree and produces the child items it
   contains: if the directory's own initialization file matches the configured
   file pattern (`initMatches`), an item for that file (`initNode`) is produced
   first; then every visited path is examined, and each non-boundary regular
   file contributes whatever child items it resolves to.

   Enumeration is a directory-structure operation: it inspects paths and builds
   items lazily. It must therefore NOT load the directory's own initialization
   file as a side effect — running that file's contents is the job of the
   produced items when (and if) they are later realized, not of the enumeration
   itself. Whether the enumeration loaded the directory's own initialization
   file is an observable of the walk, carried as the second component of the
   result; the desired behavior pins it to `false` unconditionally.

   The first component is the produced sequence, pinned exactly to the walk of
   the given entries (with the leading initialization-file item when it
   matches), so an enumeration cannot trade correctness of the output for the
   loading obligation or vice versa. -/
method gatherEntries (initMatches : Bool) (initNode : Nat)
    (entries : List PkgEntry) return (out : List Nat × Bool)
  ensures out.2 = false
  ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
  do
    -- impl-start
    -- Walk the enumerated paths and gather the child items; the directory's
    -- own initialization file is never loaded during the walk (the loaded
    -- flag reported is false).
    let mut collected : List Nat := []
    if initMatches then
      collected := collected ++ [initNode]
    collected := entries.foldl
      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
      collected
    return (collected, false)
    -- impl-end

/- The fold accumulating child items equals the accumulator followed by
   `walkEntries`, generalized over the accumulator. -/
lemma foldl_walkEntries (es : List PkgEntry) :
    ∀ acc : List Nat,
      es.foldl (fun acc e => if e.boundary = true ∨ e.isFile = false then acc
                             else acc ++ e.yields) acc
        = acc ++ walkEntries es := by
  induction es with
  | nil => intro acc; simp [walkEntries]
  | cons e es ih =>
    intro acc
    simp only [List.foldl_cons, walkEntries, ih]
    by_cases hb : e.boundary = true
    · simp [hb]
    · by_cases hf : e.isFile = true
      · simp [hb, hf, List.append_assoc]
      · simp [hb, hf]

prove_correct gatherEntries by
  loom_solve <;> simp_all [foldl_walkEntries]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: env, SBU_BENCHMARK_DIR=.../benchmark-verified, verifier=scripts/lean_verify.sh, resolve via swebench_unified.harness.run_resolve (docker).

SAME-SPEC: all 8 attacks + positive_control are same_spec=True vs Solution.lean (markers.same_spec, velvet).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently <=4/batch):
- positive_control.lean (byte-identical to bundle Solution.lean impl): EXIT 0 (VERIFIES) -> positive control good.
- atk_1 (PREPATCH bug: return (collected, true) -> reports eager load event): EXIT 1, fails on case ensures_2 (out.2 = false, goal False). Prepatch reproduced = the exact issue regression.
- atk_2 (control-flow: drop leading initNode item): EXIT 1, fails ensures_1.
- atk_3 (wrong skip predicate: ignore boundary flag): EXIT 1, fails ensures_1.
- atk_4 (wrong file predicate: ignore isFile, include directories): EXIT 1, fails ensures_1.
- atk_5 (effect: duplicate yields, emit each file twice): EXIT 1, fails ensures_1.
- atk_6 (partial-domain: return only leading item, never walk entries): EXIT 1, fails ensures_1 (walkEntries entries = []).
- atk_7 (boundary/order: foldr, reversed walk order): EXIT 1, fails ensures_1.
- atk_8 (ungrounded-oracle echo: return ((if initMatches then [initNode] else []) ++ walkEntries entries, false)): EXIT 0 (VERIFIES). This verifies BECAUSE it returns the exact spec function -> it is a CORRECT impl, not a wrong one.

RESOLVE (protocol step 2 - every verifying impl's faithful refined patch through official harness): only atk_8 verifies (besides the positive control). Its faithful refined patch = a Package.collect walk that yields exactly the spec sequence and never eagerly loads the directory's own __init__.py = behaviorally the gold patch (materialized as atk_8_faithful_patch.diff). run_resolve('pytest-dev__pytest-6197', patch, timeout=1800): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the ONLY verifying candidate's faithful patch DOES resolve -> verify=>correct holds; no verify-not-resolve pair exists.

A-LEG AUDIT (refinement.md + meta.json): meta axioms=[], deep_model_references=[] -> there are NO A-consumed / A-reference legs to break. refinement.md tags every leg R or I (A1/A2 I=unchanged yield+gathering loop; A3 I=the removed eager mount modeled DEEPLY as the out.2 result-component value; site B obj-property refactor = R relocation, Module.__init__ deletion = I dead-code removal). Section C explicitly confirms no consumed axiom / no A-reference and no kind-3 steps. Model<->patch correspondence is faithful: out.2=false <-> removed self._mount_obj_if_needed() at top of collect; out.1=exact walk <-> unchanged gathering loop; additional_change_sites correctly R/I, subsumed by the frame. Spec-strength design (F): event carried as a RESULT component (assigned once at return), not a resettable mut slot, so a fire-then-reset impl is structurally excluded; total-correctness semantics close the non-termination loophole.

VERDICT: SOUND. >=5 distinct wrong impls (prepatch + 6 further: partial-domain atk_6, boundary/predicate atk_3/atk_4, control-flow atk_2, effect atk_5/atk_1, ordering atk_7, ungrounded-oracle echo atk_8) encoded and machine-verified; all wrong impls are REJECTED by the verifier; the sole verifying candidate (oracle echo, semantically correct) has a faithful patch that RESOLVES under the official harness. No verifying-wrong-impl-with-non-resolving-patch exists. verify=>correct is not falsified.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is an exact functional equality over a total (precondition-free) domain: out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries AND out.2 = false. Any verifying impl is forced to compute the identical function; there is no admitted slack for a wrong-but-verifying impl.
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

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The per-path resolution of a regular file to the
--  child items it contributes is an orthogonal, unchanged operation whose
--  result enters as plain input data (the `yields` field of each enumerated
--  entry); whether a path lies on the enumeration boundary enters as a plain
--  Boolean observation. No opaque/axiom callee contract is needed.)
-- axioms-end

-- pure-start
/- One enumerated path of a directory tree, reduced to what content
   enumeration consumes:

   * `boundary` — the path contributes nothing to this directory's own
     enumeration (it is the directory's own initialization file, or it already
     sits inside a nested sub-directory that has been accounted for);
   * `isFile` — the path is a regular file (as opposed to a directory);
   * `yields` — the child items a non-boundary regular file resolves to. -/
structure PkgEntry where
  boundary : Bool
  isFile : Bool
  yields : List Nat
  deriving Inhabited, DecidableEq

/- The child items produced by walking the enumerated paths front-to-back:
   a boundary path or a directory contributes nothing; a non-boundary regular
   file contributes the items it resolves to. -/
def walkEntries : List PkgEntry → List Nat
  | [] => []
  | e :: es => (if e.boundary || !e.isFile then [] else e.yields) ++ walkEntries es
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Enumerating the contents of a directory that carries an initialization file.

   The enumeration walks the directory tree and produces the child items it
   contains: if the directory's own initialization file matches the configured
   file pattern (`initMatches`), an item for that file (`initNode`) is produced
   first; then every visited path is examined, and each non-boundary regular
   file contributes whatever child items it resolves to.

   Enumeration is a directory-structure operation: it inspects paths and builds
   items lazily. It must therefore NOT load the directory's own initialization
   file as a side effect — running that file's contents is the job of the
   produced items when (and if) they are later realized, not of the enumeration
   itself. Whether the enumeration loaded the directory's own initialization
   file is an observable of the walk, carried as the second component of the
   result; the desired behavior pins it to `false` unconditionally.

   The first component is the produced sequence, pinned exactly to the walk of
   the given entries (with the leading initialization-file item when it
   matches), so an enumeration cannot trade correctness of the output for the
   loading obligation or vice versa. -/
method gatherEntries (initMatches : Bool) (initNode : Nat)
    (entries : List PkgEntry) return (out : List Nat × Bool)
  ensures out.2 = false
  ensures out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries
  do
    -- impl-start
    -- Walk the enumerated paths and gather the child items; the directory's
    -- own initialization file is never loaded during the walk (the loaded
    -- flag reported is false).
    let mut collected : List Nat := []
    if initMatches then
      collected := collected ++ [initNode]
    collected := entries.foldl
      (fun acc e => if e.boundary || !e.isFile then acc else acc ++ e.yields)
      collected
    return (collected, false)
    -- impl-end

/- The fold accumulating child items equals the accumulator followed by
   `walkEntries`, generalized over the accumulator. -/
lemma foldl_walkEntries (es : List PkgEntry) :
    ∀ acc : List Nat,
      es.foldl (fun acc e => if e.boundary = true ∨ e.isFile = false then acc
                             else acc ++ e.yields) acc
        = acc ++ walkEntries es := by
  induction es with
  | nil => intro acc; simp [walkEntries]
  | cons e es ih =>
    intro acc
    simp only [List.foldl_cons, walkEntries, ih]
    by_cases hb : e.boundary = true
    · simp [hb]
    · by_cases hf : e.isFile = true
      · simp [hb, hf, List.append_assoc]
      · simp [hb, hf]

prove_correct gatherEntries by
  loom_solve <;> simp_all [foldl_walkEntries]
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: env, SBU_BENCHMARK_DIR=.../benchmark-verified, verifier=scripts/lean_verify.sh, resolve via swebench_unified.harness.run_resolve (docker).

SAME-SPEC: all 8 attacks + positive_control are same_spec=True vs Solution.lean (markers.same_spec, velvet).

### VERIFICATION (bash scripts/lean_verify.sh <f>; run concurrently <=4/batch):
- positive_control.lean (byte-identical to bundle Solution.lean impl): EXIT 0 (VERIFIES) -> positive control good.
- atk_1 (PREPATCH bug: return (collected, true) -> reports eager load event): EXIT 1, fails on case ensures_2 (out.2 = false, goal False). Prepatch reproduced = the exact issue regression.
- atk_2 (control-flow: drop leading initNode item): EXIT 1, fails ensures_1.
- atk_3 (wrong skip predicate: ignore boundary flag): EXIT 1, fails ensures_1.
- atk_4 (wrong file predicate: ignore isFile, include directories): EXIT 1, fails ensures_1.
- atk_5 (effect: duplicate yields, emit each file twice): EXIT 1, fails ensures_1.
- atk_6 (partial-domain: return only leading item, never walk entries): EXIT 1, fails ensures_1 (walkEntries entries = []).
- atk_7 (boundary/order: foldr, reversed walk order): EXIT 1, fails ensures_1.
- atk_8 (ungrounded-oracle echo: return ((if initMatches then [initNode] else []) ++ walkEntries entries, false)): EXIT 0 (VERIFIES). This verifies BECAUSE it returns the exact spec function -> it is a CORRECT impl, not a wrong one.

RESOLVE (protocol step 2 - every verifying impl's faithful refined patch through official harness): only atk_8 verifies (besides the positive control). Its faithful refined patch = a Package.collect walk that yields exactly the spec sequence and never eagerly loads the directory's own __init__.py = behaviorally the gold patch (materialized as atk_8_faithful_patch.diff). run_resolve('pytest-dev__pytest-6197', patch, timeout=1800): completed=True, resolved=True, attempts=1, flaky=False, note='resolved'. So the ONLY verifying candidate's faithful patch DOES resolve -> verify=>correct holds; no verify-not-resolve pair exists.

A-LEG AUDIT (refinement.md + meta.json): meta axioms=[], deep_model_references=[] -> there are NO A-consumed / A-reference legs to break. refinement.md tags every leg R or I (A1/A2 I=unchanged yield+gathering loop; A3 I=the removed eager mount modeled DEEPLY as the out.2 result-component value; site B obj-property refactor = R relocation, Module.__init__ deletion = I dead-code removal). Section C explicitly confirms no consumed axiom / no A-reference and no kind-3 steps. Model<->patch correspondence is faithful: out.2=false <-> removed self._mount_obj_if_needed() at top of collect; out.1=exact walk <-> unchanged gathering loop; additional_change_sites correctly R/I, subsumed by the frame. Spec-strength design (F): event carried as a RESULT component (assigned once at return), not a resettable mut slot, so a fire-then-reset impl is structurally excluded; total-correctness semantics close the non-termination loophole.

VERDICT: SOUND. >=5 distinct wrong impls (prepatch + 6 further: partial-domain atk_6, boundary/predicate atk_3/atk_4, control-flow atk_2, effect atk_5/atk_1, ordering atk_7, ungrounded-oracle echo atk_8) encoded and machine-verified; all wrong impls are REJECTED by the verifier; the sole verifying candidate (oracle echo, semantically correct) has a faithful patch that RESOLVES under the official harness. No verifying-wrong-impl-with-non-resolving-patch exists. verify=>correct is not falsified.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) audit of velvet gatherEntries vs post-patch Package.collect (src/_pytest/python.py:641-670 @ base_commit e856638), gold patch.diff removes the leading self._mount_obj_if_needed() from collect and makes obj mounting lazy.

Setup checks all pass:
- same_spec(Solution, Solution_prepatch, velvet) = True (spec region byte-identical; verified via swebench_unified.markers).
- Solution.lean verifies (lean_verify exit 0).
- Solution_prepatch.lean fails on exactly the discriminating clause `ensures_2: out.2 = false` (exit 1), confirming the spec sees the bug rather than being trivially satisfiable.

Faithfulness of each spec clause to the REAL post-patch callee:
1) `out.2 = false`. Post-patch collect no longer calls _mount_obj_if_needed(), so the directory's own __init__.py is never imported as a side effect of the walk. The observable is unconditionally false in every real run. The spec pins it to false unconditionally — matches. Not too strong: there is no real post-patch input where the walk DOES import the own init, so no input forces out.2=true.
2) `out.1 = (if initMatches then [initNode] else []) ++ walkEntries entries`. Post-patch collect yields Module(init_module,self) first iff init_module.check(file=1) and path_matches_patterns(...) (=initMatches), then iterates this_path.visit(bf=True,sort=True): own-__init__.py skipped, pkg_prefix-accounted paths skipped (both -> boundary), directories yield nothing (-> !isFile), non-boundary regular files `yield from self._collectfile(path)` (-> yields, unchanged orthogonal callee entering as data). walkEntries drops entries with boundary||!isFile and appends `yields` otherwise, front-to-back — this is exactly the generator's yield order. _collectfile returning () for ignore/dup/non-collectable files is faithfully carried as an empty `yields`. The order-dependent pkg_prefixes state is captured because the bf-walk marks accounted-for descendants boundary=true.

No diverging input exists: for any real directory tree, the (boundary,isFile,yields) observation list reconstructs the real yielded sequence and out.2=false is the exact post-patch guarantee. The output clause is deep (full walk), not a pass-through, so it is not artificially weak either. Model is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Scope: consumer spec view = spec_view(Solution.lean) (signatures, contracts, pure helpers, comments; impl elided). refinement.md and mapping.md are refinement-audit docs, NOT the consumer view (mapping.md explicitly labels the removed line 'refinement audit only, not in the consumer spec view'), so their citations of _mount_obj_if_needed / python.py / line numbers are out of scope.

Public problem_statement already discloses: pytest 5.2.3 wrongly imports any __init__.py during collection; desired behavior = collection must NOT import those __init__.py files (repro: __init__.py containing 'assert False' errors during collection).

Spec view content vs. that baseline:
- Behavioral requirement pinned (out.2 = false: enumeration 'must NOT load the directory's own initialization file as a side effect'; plus exact produced sequence out.1). This restates the ALREADY-PUBLIC symptom-as-requirement in abstract model terms — not a leak.
- Identifiers fully abstracted: gatherEntries, PkgEntry, walkEntries, initMatches, initNode, boundary, isFile, yields. NONE embed the patched repo symbols (PyobjMixin, genfunctions, isinitpath, mount_obj_if_needed).
- No file path (src/_pytest/python.py), no diff markers, no reproduced gold line.
- Crucially, the gold MECHANISM is NOT disclosed: no mention of removing an eager mount call, the PyobjMixin.obj lazy-property refactor, or the Module.__init__ deletion. The spec models a single abstract load-event boolean; a solver cannot reconstruct the actual edit (which line/method to change) from it.
- No bug/fix narration.

Mechanical G-LEAK screen run: PASSED, zero hard failures (changed symbols PyobjMixin/genfunctions/isinitpath/mount_obj_if_needed; changed files src/_pytest/python.py — none appear in view). same_spec(Solution, Solution_prepatch)=True confirms the discriminator lives in the elided impl, not the spec surface. The spec view leaks nothing about the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
