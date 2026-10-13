# P2 adversarial audit — pydata__xarray-4629

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_8.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

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
 -- (No consumed axioms: the combined operation is modeled deeply via an explicit
@@ -47,9 +47,7 @@
   ensures fresh = freshOld + 1
   do
     -- impl-start
-    let result := fresh
-    store := Function.update store fresh (store sources.head!)
-    fresh := fresh + 1
+    let result := sources.head!
     return result
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
 -- (No consumed axioms: the combined operation is modeled deeply via an explicit
@@ -48,7 +48,6 @@
   do
     -- impl-start
     let result := fresh
-    store := Function.update store fresh (store sources.head!)
     fresh := fresh + 1
     return result
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
 -- (No consumed axioms: the combined operation is modeled deeply via an explicit
@@ -49,7 +49,7 @@
     -- impl-start
     let result := fresh
     store := Function.update store fresh (store sources.head!)
-    fresh := fresh + 1
+    fresh := fresh + 2
     return result
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
 -- (No consumed axioms: the combined operation is modeled deeply via an explicit
@@ -49,7 +49,6 @@
     -- impl-start
     let result := fresh
     store := Function.update store fresh (store sources.head!)
-    fresh := fresh + 1
     return result
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
 -- (No consumed axioms: the combined operation is modeled deeply via an explicit
@@ -48,7 +48,7 @@
   do
     -- impl-start
     let result := fresh
-    store := Function.update store fresh (store sources.head!)
+    store := Function.update store fresh (store sources.getLast!)
     fresh := fresh + 1
     return result
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
 -- (No consumed axioms: the combined operation is modeled deeply via an explicit
@@ -49,6 +49,7 @@
     -- impl-start
     let result := fresh
     store := Function.update store fresh (store sources.head!)
+    store := Function.update store sources.head! []
     fresh := fresh + 1
     return result
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
 -- (No consumed axioms: the combined operation is modeled deeply via an explicit
@@ -47,8 +47,8 @@
   ensures fresh = freshOld + 1
   do
     -- impl-start
-    let result := fresh
-    store := Function.update store fresh (store sources.head!)
+    let result := fresh + 1
+    store := Function.update store (fresh+1) (store sources.head!)
     fresh := fresh + 1
     return result
     -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the combined operation is modeled deeply via an explicit
--  store of object contents and a fresh-handle allocator. Soundness of that
--  deep model against the real object-copy semantics is audited by G-AX.)
-- axioms-end

-- pure-start
/- The contents carried by one mapping object: an ordered collection of
   key/value entries. Modeled as an association list so two objects holding the
   same entries compare equal while still being separable by identity. -/
abbrev Entries := List (String × String)

/- An object identity — a handle into the live store. Distinct handles denote
   distinct mutable objects, so an update made through one handle is invisible
   through every other handle. The store maps each live handle to its current
   contents; `fresh` is the next handle never yet handed out. -/
abbrev Handle := Int
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine a non-empty sequence of mapping objects under the policy that takes
   the first object's contents. The returned object carries exactly those
   contents, is an object of its own (distinct from every input), and leaves
   every input object untouched — so later updates to the result are not seen
   through any input handle. -/
method combineFirst (mut store : Handle → Entries) (mut fresh : Handle)
    (sources : List Handle) return (result : Handle)
  require sources ≠ []
  require ∀ h, h ∈ sources → h < fresh
  ensures store result = storeOld (sources.head!)
  ensures result ∉ sources
  ensures ∀ h, h ∈ sources → store h = storeOld h
  ensures result = freshOld
  ensures fresh = freshOld + 1
  do
    -- impl-start
    let result := fresh
    fresh := fresh + 1
    store := Function.update store result (store sources.head!)
    return result
    -- impl-end

prove_correct combineFirst by
  loom_solve
  all_goals (
    try (intro h hmem)
    first
    | (simp [Function.update_self])
    | (have hlt : h < freshOld := require_1 h hmem
       simp [Function.update_of_ne (ne_of_lt hlt)]))
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity, A-leg focus) for pydata__xarray-4629 (velvet). Deep-model object-identity bundle: gold patch changes merge_attrs 'override' branch from `return variable_attrs[0]` (alias) to `return dict(variable_attrs[0])` (fresh shallow copy). Lean models identity via `store : Handle -> Entries` heap + `fresh : Handle` bump allocator; 5 tight postconditions pin (1) store result = storeOld head! contents, (2) result NOTIN sources freshness, (3) forall h in sources, store h = storeOld h source-frame, (4) result = freshOld, (5) fresh = freshOld+1 allocator mechanics.

PROTOCOL. Confirmed byte-identical spec regions: same_spec=True for ALL 8 candidates (venv swebench_unified.markers.same_spec, velvet backend). Verified each via scripts/lean_verify.sh (300s). Ran verifications concurrently in two batches of 4 (background jobs).

7 DISTINCT wrong impls, all same_spec=True, ALL FAIL to verify (exit 1):
- atk_1 (prepatch bug / ungrounded-alias: `let result := sources.head!; return result`) -> exit 1. Reproduces the prepatch aliasing bug (matches bundled Solution_prepatch.lean).
- atk_2 (partial-domain: allocate fresh handle but skip contents copy) -> exit 1.
- atk_3 (boundary: correct copy but `fresh := fresh+2`) -> exit 1.
- atk_4 (boundary: correct copy but no bump) -> exit 1.
- atk_5 (wrong-content: copy sources.getLast! contents instead of head!) -> exit 1.
- atk_6 (control-flow-effect: correct fresh copy PLUS extra clobber of first source to []) -> exit 1.
- atk_7 (ungrounded-oracle echo: return arbitrary handle fresh+1 while bumping fresh+1) -> exit 1.
Positive control atk_8 (structurally different but CORRECT: bump-then-update-freshOld) -> exit 0 (verifies), same_spec=True -> spec is NON-VACUOUS.

TACTIC-ARTIFACT RULE-OUT: atk_1/2/6/7 initially errored inside the tailored proof script (`unknown identifier h`). Re-ran each with a bare `loom_solve` proof (atk_{1,2,6,7}_mp.lean) -> still exit 1 with GENUINE unsolved postcondition goals: atk_1_mp leaves ensures_1 (freshOld = freshOld+1), ensures_2 (sources.head! = freshOld), ensures_4 (sources.head! NOTIN sources); atk_2_mp leaves ensures_5 (storeOld freshOld = storeOld head!); atk_6_mp leaves ensures_3 + ensures_5; atk_7_mp leaves ensures_2/3/5. Confirms real spec-clause rejections, not proof artifacts. atk_3/4/5 already showed named unsolved ensures goals directly.

STEP 2 (materialize+resolve verifying wrong impls): VACUOUS — zero wrong impls verify, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. `patches` is therefore empty; no run_resolve run was required or possible for a wrong impl. verify => correct holds on the full attack battery.

STEP 3 (refinement.md audit): legs A1(R), A2(R), A3(R+I), A4(A-reference+I), A5(R); axioms region EMPTY -> no A-consumed leg, no kind-3 (inexpressible-changed-op) step. The single deep-model reference (A4: allocate-fresh-handle + Function.update + bump ↔ real CPython dict(...) constructor on the three observables identity-distinct / equal-contents / source-frame-preserved) is validated by G-AX (axiom_check.py, recorded pass rc0, 9 boundary + 20000 fuzz inputs incl. aliased-input edge). The A-leg correspondence to the real callee (dict) holds; mapping.md §3.1 grounds it and dually shows the prepatch direct-return violates freshness/frame (the observed bug). No unfaithful A-leg found.

VERDICT: SOUND. >=5 distinct wrong impls (7) run and verified-to-FAIL under the official Lean harness; none verifies, so none can break the spec via a non-resolving faithful patch. Positive control verifies (non-vacuity). Refinement legs all R/A-reference/I with the A-reference audited sound. verify => correct is upheld.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `atk_8.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_8.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms: the combined operation is modeled deeply via an explicit
--  store of object contents and a fresh-handle allocator. Soundness of that
--  deep model against the real object-copy semantics is audited by G-AX.)
-- axioms-end

-- pure-start
/- The contents carried by one mapping object: an ordered collection of
   key/value entries. Modeled as an association list so two objects holding the
   same entries compare equal while still being separable by identity. -/
abbrev Entries := List (String × String)

/- An object identity — a handle into the live store. Distinct handles denote
   distinct mutable objects, so an update made through one handle is invisible
   through every other handle. The store maps each live handle to its current
   contents; `fresh` is the next handle never yet handed out. -/
abbrev Handle := Int
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine a non-empty sequence of mapping objects under the policy that takes
   the first object's contents. The returned object carries exactly those
   contents, is an object of its own (distinct from every input), and leaves
   every input object untouched — so later updates to the result are not seen
   through any input handle. -/
method combineFirst (mut store : Handle → Entries) (mut fresh : Handle)
    (sources : List Handle) return (result : Handle)
  require sources ≠ []
  require ∀ h, h ∈ sources → h < fresh
  ensures store result = storeOld (sources.head!)
  ensures result ∉ sources
  ensures ∀ h, h ∈ sources → store h = storeOld h
  ensures result = freshOld
  ensures fresh = freshOld + 1
  do
    -- impl-start
    let result := fresh
    fresh := fresh + 1
    store := Function.update store result (store sources.head!)
    return result
    -- impl-end

prove_correct combineFirst by
  loom_solve
  all_goals (
    try (intro h hmem)
    first
    | (simp [Function.update_self])
    | (have hlt : h < freshOld := require_1 h hmem
       simp [Function.update_of_ne (ne_of_lt hlt)]))
```

Prepatch bug re-encoded as an attack: `True`.

ADVERSARIAL G-EQ (refinement fidelity, A-leg focus) for pydata__xarray-4629 (velvet). Deep-model object-identity bundle: gold patch changes merge_attrs 'override' branch from `return variable_attrs[0]` (alias) to `return dict(variable_attrs[0])` (fresh shallow copy). Lean models identity via `store : Handle -> Entries` heap + `fresh : Handle` bump allocator; 5 tight postconditions pin (1) store result = storeOld head! contents, (2) result NOTIN sources freshness, (3) forall h in sources, store h = storeOld h source-frame, (4) result = freshOld, (5) fresh = freshOld+1 allocator mechanics.

PROTOCOL. Confirmed byte-identical spec regions: same_spec=True for ALL 8 candidates (venv swebench_unified.markers.same_spec, velvet backend). Verified each via scripts/lean_verify.sh (300s). Ran verifications concurrently in two batches of 4 (background jobs).

7 DISTINCT wrong impls, all same_spec=True, ALL FAIL to verify (exit 1):
- atk_1 (prepatch bug / ungrounded-alias: `let result := sources.head!; return result`) -> exit 1. Reproduces the prepatch aliasing bug (matches bundled Solution_prepatch.lean).
- atk_2 (partial-domain: allocate fresh handle but skip contents copy) -> exit 1.
- atk_3 (boundary: correct copy but `fresh := fresh+2`) -> exit 1.
- atk_4 (boundary: correct copy but no bump) -> exit 1.
- atk_5 (wrong-content: copy sources.getLast! contents instead of head!) -> exit 1.
- atk_6 (control-flow-effect: correct fresh copy PLUS extra clobber of first source to []) -> exit 1.
- atk_7 (ungrounded-oracle echo: return arbitrary handle fresh+1 while bumping fresh+1) -> exit 1.
Positive control atk_8 (structurally different but CORRECT: bump-then-update-freshOld) -> exit 0 (verifies), same_spec=True -> spec is NON-VACUOUS.

TACTIC-ARTIFACT RULE-OUT: atk_1/2/6/7 initially errored inside the tailored proof script (`unknown identifier h`). Re-ran each with a bare `loom_solve` proof (atk_{1,2,6,7}_mp.lean) -> still exit 1 with GENUINE unsolved postcondition goals: atk_1_mp leaves ensures_1 (freshOld = freshOld+1), ensures_2 (sources.head! = freshOld), ensures_4 (sources.head! NOTIN sources); atk_2_mp leaves ensures_5 (storeOld freshOld = storeOld head!); atk_6_mp leaves ensures_3 + ensures_5; atk_7_mp leaves ensures_2/3/5. Confirms real spec-clause rejections, not proof artifacts. atk_3/4/5 already showed named unsolved ensures goals directly.

STEP 2 (materialize+resolve verifying wrong impls): VACUOUS — zero wrong impls verify, so there is no verifying-but-wrong candidate whose faithful refined patch could fail to resolve. `patches` is therefore empty; no run_resolve run was required or possible for a wrong impl. verify => correct holds on the full attack battery.

STEP 3 (refinement.md audit): legs A1(R), A2(R), A3(R+I), A4(A-reference+I), A5(R); axioms region EMPTY -> no A-consumed leg, no kind-3 (inexpressible-changed-op) step. The single deep-model reference (A4: allocate-fresh-handle + Function.update + bump ↔ real CPython dict(...) constructor on the three observables identity-distinct / equal-contents / source-frame-preserved) is validated by G-AX (axiom_check.py, recorded pass rc0, 9 boundary + 20000 fuzz inputs incl. aliased-input edge). The A-leg correspondence to the real callee (dict) holds; mapping.md §3.1 grounds it and dually shows the prepatch direct-return violates freshness/frame (the observed bug). No unfaithful A-leg found.

VERDICT: SOUND. >=5 distinct wrong impls (7) run and verified-to-FAIL under the official Lean harness; none verifies, so none can break the spec via a non-resolving faithful patch. Positive control verifies (non-vacuity). Refinement legs all R/A-reference/I with the A-reference audited sound. verify => correct is upheld.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / model-vs-real-callee drift) analysis for velvet pydata__xarray-4629, combineFirst modeling merge_attrs override branch (dict(variable_attrs[0])).

### Checks run
- same_spec(Solution, Solution_prepatch)=True via swebench_unified.markers — spec region byte-identical (proper G-DIFF pair, spec unchanged across impl swap).
- lean_verify Solution.lean: exit 0 (verifies clean). lean_verify Solution_prepatch.lean: exit 1, fails exactly on ensures result ∉ sources (goal sources.head! ∉ sources unprovable). Spec is DISCRIMINATING, not vacuously/uniformly too strong.
- axiom_check.py (G-AX): exit 0 over 9 boundary + 20000 fuzz inputs against the REAL CPython dict(...) constructor — fresh-identity, equal-contents, source-frame all hold; prepatch direct-return violates them.
- conformance_check.py reviewed: diffs R/I shadow vs patched merge_attrs(...,'override') on the three observables over 100k inputs (seed 4629). Base_commit real callee confirmed as `return dict(variable_attrs[0])`.

SPEC-STRENGTH ASSESSMENT: each postcondition maps to a real observable of dict(d): store result = storeOld head! ↔ equal shallow-copied contents; result ∉ sources / result = freshOld ↔ dict(...) always allocates a new object (never returns an existing one); ∀h∈sources store h = storeOld h ↔ shallow copy leaves sources untouched. The fresh=freshOld+1 clause is a model-internal allocator device (not a real-callee observable) and does not over-constrain the modeled Python behavior. Preconditions (sources≠[], ∀h∈sources h<fresh) are the natural non-empty + bump-allocator well-formedness invariants and do not exclude any real merge_attrs override input.

No Requires-satisfying input found where the modeled function's observables disagree with the real repo callee. Spec is neither too strong nor drifted. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Attacker-3 (leakage / gold-reconstruction), velvet backend. Method: computed the actual spec view with swebench_unified.markers.spec_view via VelvetBackend LanguageTables (flavor=lean; region_names include 'impl' but NOT 'proof', so both the impl block AND the prove_correct body are elided). Confirmed the computed spec_view sha256 == the recorded gates.G-HYGIENE.region_hashes.spec_view (8733c07437238b51eb8b8d9b3deca946c1fcdeeda6a2b332df4c145d19b03b12). Confirmed same_spec(Solution, Solution_prepatch)==True (patch touches only elided impl/proof, not the spec). Ran leakage.screen over the spec view against gold patch + problem_statement: passed, no hard failures.

Spec-view contents = (a) abstract Lean modeling comments describing an association-list Entries type and a Handle/store/fresh allocator model, and (b) the combineFirst signature + preconditions (sources ≠ [], ∀ h ∈ sources → h < fresh) + postconditions (store result = storeOld sources.head!, result ∉ sources, ∀ h ∈ sources → store h = storeOld h, result = freshOld, fresh = freshOld+1). No Python identifiers, no `dict(...)`, no `variable_attrs[0]`, no file:line, no gold-patch tokens appear.

Crucially, the PUBLIC problem_statement already discloses the entire gold edit: it names the bug (merge references attrs from the first object instead of copying), gives the MCVE, quotes the culprit line `return variable_attrs[0]`, states the fix verbatim (`return dict(variable_attrs[0])`), and links merge.py#L504. The spec view reveals nothing about the fix beyond what problem_statement already states — it only re-expresses the same public behavioral property (result is a fresh object distinct from sources whose later mutation is invisible through the sources) in abstract Lean terms. No spec-view line leaks the gold edit beyond the public problem_statement. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
