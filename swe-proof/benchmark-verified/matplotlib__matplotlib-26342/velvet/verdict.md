# P2 adversarial audit — matplotlib__matplotlib-26342

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,10 +66,8 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
-    return Except.ok ()
+    return Except.error ()
     -- impl-end
 
 prove_correct setPaths by
   loom_solve
-  simp [getPaths]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,10 +66,12 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
-    return Except.ok ()
+    if newPaths.isEmpty then
+      return Except.error ()
+    else
+      coll := { coll with paths := newPaths, stale := true }
+      return Except.ok ()
     -- impl-end
 
 prove_correct setPaths by
   loom_solve
-  simp [getPaths]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,10 +66,9 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
+    coll := { coll with paths := newPaths, stale := false }
     return Except.ok ()
     -- impl-end
 
 prove_correct setPaths by
   loom_solve
-  simp [getPaths]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,10 +66,9 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
+    coll := { coll with paths := [], stale := true }
     return Except.ok ()
     -- impl-end
 
 prove_correct setPaths by
   loom_solve
-  simp [getPaths]
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -66,7 +66,7 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
+    coll := { coll with paths := newPaths.reverse.reverse, stale := true }
     return Except.ok ()
     -- impl-end
 
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -66,7 +66,7 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
+    coll := { coll with paths := newPaths ++ [], stale := true }
     return Except.ok ()
     -- impl-end
 
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -66,8 +66,12 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
-    return Except.ok ()
+    if newPaths.length ≥ 0 then
+      coll := { coll with paths := newPaths, stale := true }
+      return Except.ok ()
+    else
+      coll := { coll with paths := [], stale := false }
+      return Except.error ()
     -- impl-end
 
 prove_correct setPaths by
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -66,10 +66,11 @@
   ensures coll.stale = true
   do
     -- impl-start
-    coll := { coll with paths := newPaths, stale := true }
+    coll := { coll with paths := newPaths.map (fun x => x), stale := true }
     return Except.ok ()
     -- impl-end
 
 prove_correct setPaths by
   loom_solve
+  simp [getPaths, List.map_id']
   simp [getPaths]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the desired behavior is that a path-replacement
-- request COMPLETES (see the method docstring), so the spec must also rule out
-- implementations that diverge (under partial correctness a non-terminating
-- body would vacuously satisfy every postcondition).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the operation under specification is a leaf state
-- mutation modeled DIRECTLY over the observable carrier (see the `pure` region).
-- There is no unchanged callee whose internal behavior the proof must assume.
-- axioms-end

-- pure-start
/- The observable state of a drawable path container, restricted to the two
   aspects a path-replacement request can touch:

   * `paths` — the ordered collection of drawable paths the container currently
     holds (what a paths query returns); modeled as a list of opaque path
     identities (`Int`), since the operation neither inspects nor reshapes any
     individual path, it only stores the supplied collection wholesale;
   * `stale` — whether the container is marked as needing a redraw before it can
     next be rendered.

   All other container state (offsets, transforms, sizes, styling) is untouched
   by a path-replacement request and is therefore not part of this carrier
   (mapping.md §2). -/
structure PathContainer where
  paths : List Int
  stale : Bool
  deriving Inhabited, DecidableEq

/- A paths query reports the collection the container currently holds. -/
def getPaths (c : PathContainer) : List Int := c.paths
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Replace the drawable paths held by a container with a supplied collection.

   Desired behavior: the request must SUCCEED (it completes normally rather than
   refusing the operation), the container thereafter holds exactly the supplied
   collection of paths — so a subsequent paths query returns precisely what was
   stored — and the container is marked as needing a redraw. The success/refusal
   outcome is reported in `out`: `Except.ok ()` for a completed replacement,
   `Except.error ()` for a refusal that leaves the request unfulfilled.

   `newPaths` is the read-only supplied collection (not `mut`): it is stored, not
   altered. The container `coll` is mutated to reflect the replacement; both
   touched aspects (`paths`, `stale`) are pinned exactly, so no fragment of the
   post-state is left unconstrained (directive 5). -/
method setPaths (mut coll : PathContainer) (newPaths : List Int)
    return (out : Except Unit Unit)
  ensures out = Except.ok ()
  ensures coll.paths = newPaths
  ensures getPaths coll = newPaths
  ensures coll.stale = true
  do
    -- impl-start
    coll := { coll with paths := newPaths, stale := true }
    return Except.ok ()
    -- impl-end

prove_correct setPaths by
  loom_solve
  simp [getPaths]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec fully pins the entire observable carrier and has no axioms/A-references, so no verifying wrong-impl could be found whose faithful patch fails to resolve.

STRUCTURAL BASIS: PathContainer has exactly two fields (paths, stale). The postconditions pin ALL of observable state exactly: coll.paths = newPaths, getPaths coll = newPaths, coll.stale = true, out = Except.ok () — with NO preconditions and ZERO consumed axioms / A-references. Any verifying impl therefore produces the identical final abstract state as gold, and the impl literally cannot express an un-modeled side effect (there are no other carrier fields). The only degree of freedom is HOW a verifying impl computes the same newPaths value (value-equivalent list transforms), whose faithful Python transliteration may store a copy vs. an alias — I tested exactly this and it still resolves.

SAME-SPEC: all 8 attacks + positive control confirmed same_spec=True against Solution.lean (velvet backend). Only impl region + proof tactic edited; spec regions byte-identical.

### LEAN VERIFY (scripts/lean_verify.sh <f>, run concurrently in batches of 4):
- atk_1 PREPATCH refusal (return Except.error ()): exit 1, does NOT verify. Unsolved goals EXACTLY match refinement.md: `Except.error () = Except.ok ()`, `collOld.paths = newPaths`, `getPaths collOld = newPaths`, `collOld.stale = true`. => prepatch_reproduced=True.
- atk_2 partial-domain (refuse on empty supplied): exit 1, correctly rejected (unsolved `Except.error () = Except.ok ()` etc.).
- atk_3 boundary (stores paths but stale := false, no redraw): exit 1, correctly rejected (unsolved stale/getPaths goals).
- atk_4 wrong-store (stores [] instead of newPaths): exit 1, correctly rejected.
- atk_5 value-equiv (newPaths.reverse.reverse): exit 0, VERIFIES.
- atk_6 value-equiv (newPaths ++ []): exit 0, VERIFIES.
- atk_7 control-flow (trivially-true guard `length >= 0`, same store on taken branch, dead error branch): exit 0, VERIFIES.
- atk_8 value-equiv (newPaths.map id, proof: simp [getPaths, List.map_id']): exit 0, VERIFIES.
- pos_control (gold impl verbatim): exit 0, VERIFIES.

RESOLVE (harness.run_resolve via `docker` swebench run_evaluation, run_id sbu-eqaudit-*, timeout 1800, retries 1; F2P=test_contour_set_paths[png], 81 P2P):
- gold baseline: resolved=True completed=True note='resolved'.
- atk_5 faithful patch (self._paths = list(reversed(list(reversed(paths))))): resolved=True.
- atk_6 faithful patch (self._paths = list(paths) + []): resolved=True.
- atk_7 faithful patch (if len(paths) >= 0: store+stale; dead else): resolved=True.
- atk_8 faithful patch (self._paths = [x for x in paths]): resolved=True.
All faithful patches include the gold's redundant PathCollection.set_paths override removal and applied cleanly (git apply --check rc=0). Every verifying attack's materialized patch RESOLVED — none breaks the spec. The F2P test uses check_figures_equal (renders contours and compares images), so it depends only on the STORED PATHS + stale flag, not object identity; hence a stored copy resolves identically to gold. NOTE: verify⇏correct would require a verifying impl whose faithful patch fails to resolve; I could construct none because the spec leaves no un-pinned observable.

REFINEMENT.MD LEG AUDIT: legs A1–A4 are all R / R+I; refinement.md §C and mapping.md §3 explicitly declare ZERO consumed axioms, ZERO A-references, no kind-3 steps. This is correct and sound: per SPEC_GUIDE §0.7 the changed function (set_paths) is modeled directly over the observable carrier, never axiomatized/A-referenced (axiomatizing it would wrongly demand base-commit `raise NotImplementedError` match the patched model). The only named callee getPaths is the trivial unchanged accessor `return self._paths` (collections.py:206), modeled by a Lean def (not an axiom), used only to phrase getPaths coll = newPaths. G-AX correctly SKIPS (no unchanged callee whose internals the proof assumes). Repo reality confirmed in-container: base set_paths = `raise NotImplementedError`; get_paths = `return self._paths`. The A-legs' correspondence holds; there are no A-legs to break because there are none — and the absence is justified, not evasive.

CONCLUSION: No same-spec verifying impl exists whose faithful refined patch fails to resolve. Spec is SOUND (verify ⇒ correct on the tested F2P/P2P inputs).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 4 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the desired behavior is that a path-replacement
-- request COMPLETES (see the method docstring), so the spec must also rule out
-- implementations that diverge (under partial correctness a non-terminating
-- body would vacuously satisfy every postcondition).
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees: the operation under specification is a leaf state
-- mutation modeled DIRECTLY over the observable carrier (see the `pure` region).
-- There is no unchanged callee whose internal behavior the proof must assume.
-- axioms-end

-- pure-start
/- The observable state of a drawable path container, restricted to the two
   aspects a path-replacement request can touch:

   * `paths` — the ordered collection of drawable paths the container currently
     holds (what a paths query returns); modeled as a list of opaque path
     identities (`Int`), since the operation neither inspects nor reshapes any
     individual path, it only stores the supplied collection wholesale;
   * `stale` — whether the container is marked as needing a redraw before it can
     next be rendered.

   All other container state (offsets, transforms, sizes, styling) is untouched
   by a path-replacement request and is therefore not part of this carrier
   (mapping.md §2). -/
structure PathContainer where
  paths : List Int
  stale : Bool
  deriving Inhabited, DecidableEq

/- A paths query reports the collection the container currently holds. -/
def getPaths (c : PathContainer) : List Int := c.paths
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Replace the drawable paths held by a container with a supplied collection.

   Desired behavior: the request must SUCCEED (it completes normally rather than
   refusing the operation), the container thereafter holds exactly the supplied
   collection of paths — so a subsequent paths query returns precisely what was
   stored — and the container is marked as needing a redraw. The success/refusal
   outcome is reported in `out`: `Except.ok ()` for a completed replacement,
   `Except.error ()` for a refusal that leaves the request unfulfilled.

   `newPaths` is the read-only supplied collection (not `mut`): it is stored, not
   altered. The container `coll` is mutated to reflect the replacement; both
   touched aspects (`paths`, `stale`) are pinned exactly, so no fragment of the
   post-state is left unconstrained (directive 5). -/
method setPaths (mut coll : PathContainer) (newPaths : List Int)
    return (out : Except Unit Unit)
  ensures out = Except.ok ()
  ensures coll.paths = newPaths
  ensures getPaths coll = newPaths
  ensures coll.stale = true
  do
    -- impl-start
    coll := { coll with paths := newPaths, stale := true }
    return Except.ok ()
    -- impl-end

prove_correct setPaths by
  loom_solve
  simp [getPaths]
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The spec fully pins the entire observable carrier and has no axioms/A-references, so no verifying wrong-impl could be found whose faithful patch fails to resolve.

STRUCTURAL BASIS: PathContainer has exactly two fields (paths, stale). The postconditions pin ALL of observable state exactly: coll.paths = newPaths, getPaths coll = newPaths, coll.stale = true, out = Except.ok () — with NO preconditions and ZERO consumed axioms / A-references. Any verifying impl therefore produces the identical final abstract state as gold, and the impl literally cannot express an un-modeled side effect (there are no other carrier fields). The only degree of freedom is HOW a verifying impl computes the same newPaths value (value-equivalent list transforms), whose faithful Python transliteration may store a copy vs. an alias — I tested exactly this and it still resolves.

SAME-SPEC: all 8 attacks + positive control confirmed same_spec=True against Solution.lean (velvet backend). Only impl region + proof tactic edited; spec regions byte-identical.

### LEAN VERIFY (scripts/lean_verify.sh <f>, run concurrently in batches of 4):
- atk_1 PREPATCH refusal (return Except.error ()): exit 1, does NOT verify. Unsolved goals EXACTLY match refinement.md: `Except.error () = Except.ok ()`, `collOld.paths = newPaths`, `getPaths collOld = newPaths`, `collOld.stale = true`. => prepatch_reproduced=True.
- atk_2 partial-domain (refuse on empty supplied): exit 1, correctly rejected (unsolved `Except.error () = Except.ok ()` etc.).
- atk_3 boundary (stores paths but stale := false, no redraw): exit 1, correctly rejected (unsolved stale/getPaths goals).
- atk_4 wrong-store (stores [] instead of newPaths): exit 1, correctly rejected.
- atk_5 value-equiv (newPaths.reverse.reverse): exit 0, VERIFIES.
- atk_6 value-equiv (newPaths ++ []): exit 0, VERIFIES.
- atk_7 control-flow (trivially-true guard `length >= 0`, same store on taken branch, dead error branch): exit 0, VERIFIES.
- atk_8 value-equiv (newPaths.map id, proof: simp [getPaths, List.map_id']): exit 0, VERIFIES.
- pos_control (gold impl verbatim): exit 0, VERIFIES.

RESOLVE (harness.run_resolve via `docker` swebench run_evaluation, run_id sbu-eqaudit-*, timeout 1800, retries 1; F2P=test_contour_set_paths[png], 81 P2P):
- gold baseline: resolved=True completed=True note='resolved'.
- atk_5 faithful patch (self._paths = list(reversed(list(reversed(paths))))): resolved=True.
- atk_6 faithful patch (self._paths = list(paths) + []): resolved=True.
- atk_7 faithful patch (if len(paths) >= 0: store+stale; dead else): resolved=True.
- atk_8 faithful patch (self._paths = [x for x in paths]): resolved=True.
All faithful patches include the gold's redundant PathCollection.set_paths override removal and applied cleanly (git apply --check rc=0). Every verifying attack's materialized patch RESOLVED — none breaks the spec. The F2P test uses check_figures_equal (renders contours and compares images), so it depends only on the STORED PATHS + stale flag, not object identity; hence a stored copy resolves identically to gold. NOTE: verify⇏correct would require a verifying impl whose faithful patch fails to resolve; I could construct none because the spec leaves no un-pinned observable.

REFINEMENT.MD LEG AUDIT: legs A1–A4 are all R / R+I; refinement.md §C and mapping.md §3 explicitly declare ZERO consumed axioms, ZERO A-references, no kind-3 steps. This is correct and sound: per SPEC_GUIDE §0.7 the changed function (set_paths) is modeled directly over the observable carrier, never axiomatized/A-referenced (axiomatizing it would wrongly demand base-commit `raise NotImplementedError` match the patched model). The only named callee getPaths is the trivial unchanged accessor `return self._paths` (collections.py:206), modeled by a Lean def (not an axiom), used only to phrase getPaths coll = newPaths. G-AX correctly SKIPS (no unchanged callee whose internals the proof assumes). Repo reality confirmed in-container: base set_paths = `raise NotImplementedError`; get_paths = `return self._paths`. The A-legs' correspondence holds; there are no A-legs to break because there are none — and the absence is justified, not evasive.

CONCLUSION: No same-spec verifying impl exists whose faithful refined patch fails to resolve. Spec is SOUND (verify ⇒ correct on the tested F2P/P2P inputs).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check (spec-too-strong / drift). Spec region byte-identical: swebench_unified.markers.same_spec(Solution, Solution_prepatch) = True under VelvetBackend. Solution.lean verifies (lean_verify.sh exit 0).

Modeled function `setPaths` postconditions vs real patched `Collection.set_paths` (base_commit 2aee6ccd..., shows base still `raise NotImplementedError`; gold fills body with `self._paths = paths; self.stale = True` and deletes the redundant PathCollection override).

The real function is UNCONDITIONAL — no guard, no flag, no branch (confirmed mapping.md §3.2 and gold patch). For every input it performs exactly three observable effects, each matched exactly by a postcondition:
  1. `out = Except.ok ()` — plain attribute writes, always returns None, never raises. ✓
  2. `coll.paths = newPaths` / `getPaths coll = newPaths` — `self._paths = paths` (stored wholesale by object identity); `get_paths()` returns `self._paths`. List Int carrier is sound since paths are never inspected, only stored/compared by identity. ✓
  3. `coll.stale = true` — `self.stale = True`; verified the `stale` setter (artist.py:289) sets `self._stale = val` and the getter returns `_stale`, so reading back yields True. The setter's extra callback/animation logic mutates only state deliberately omitted from the carrier as invariant, and never alters the returned _stale value. ✓

The spec pins exactly the observables the real callee guarantees on ALL inputs — neither too strong nor drifted. No diverging input exists: there is no input on which any postcondition is false for the real patched function. Spec is FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Screened the consumer spec view (markers.spec_view over Solution.lean) — the only view the leak gate governs; refinement.md/mapping.md are auditor-only and out of scope. Mechanical G-LEAK screen passes (leakage.screen: hard_failures=[]), and same_spec(Solution, Solution_prepatch)=True, confirming the frozen spec region is byte-identical across the DIFF pair. The spec view is fully abstract: it never names collections.py, Collection, PathCollection, NotImplementedError, ContourSet, cartopy, 'raise', 'override', or 'redundant' (all verified absent), modeling instead an opaque PathContainer carrier with fields paths/stale. Patch-changed symbols (set_paths, get_paths) appear nowhere in the spec view; the identifiers used (setPaths/getPaths/newPaths) are generic and don't embed a distinctive patched symbol beyond what the public problem_statement already contains ('cs.set_paths(transformed_paths)'). The behavior specified — a path-replacement request that SUCCEEDS, stores the supplied collection, and marks the container for redraw — is exactly the [ENH] the public problem_statement requests; specifying required behavior is the spec's legitimate job, not leakage. The success/refusal (Except.ok/error) framing merely restates that the requested call should now work, which the problem statement already implies (the whole point of the ENH is that the call isn't usable). The one detail not verbatim in the problem statement — the stale/redraw postcondition — is stated abstractly with no repo symbol, is a standard consequence of a store operation, and does not localize the edit to Collection.set_paths nor reveal the two-site redundant-override deletion. No spec-view line reconstructs the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
