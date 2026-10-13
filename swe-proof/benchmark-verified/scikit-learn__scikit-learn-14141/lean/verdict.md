# P2 adversarial audit — scikit-learn__scikit-learn-14141

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,9 +46,12 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_dependencyVersions : List (String × Option String) := Id.run do
-  let deps := expectedDeps
+  -- WRONG: omits joblib (pre-patch bug)
+  let deps := ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",
+               "pandas", "matplotlib"]
   let mut depsInfo : List (String × Option String) := []
   for modname in deps do
     depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,9 +46,12 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_dependencyVersions : List (String × Option String) := Id.run do
-  let deps := expectedDeps
+  -- WRONG: numpy/scipy reordered
+  let deps := ["pip", "setuptools", "sklearn", "scipy", "numpy", "Cython",
+               "pandas", "matplotlib", "joblib"]
   let mut depsInfo : List (String × Option String) := []
   for modname in deps do
     depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,9 +46,12 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_dependencyVersions : List (String × Option String) := Id.run do
-  let deps := expectedDeps
+  -- WRONG: adds an extra library "six"
+  let deps := ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",
+               "pandas", "matplotlib", "joblib", "six"]
   let mut depsInfo : List (String × Option String) := []
   for modname in deps do
     depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,17 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_dependencyVersions : List (String × Option String) := Id.run do
+  -- WRONG: binds joblib to a fabricated constant version instead of lookupVersion
   let deps := expectedDeps
   let mut depsInfo : List (String × Option String) := []
   for modname in deps do
-    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
+    if modname = "joblib" then
+      depsInfo := depsInfo ++ [(modname, some "1.0.0")]
+    else
+      depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
   return depsInfo
 -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,14 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_dependencyVersions : List (String × Option String) := Id.run do
+  -- WRONG: every value bound to lookupVersion of a FIXED name, not modname
   let deps := expectedDeps
   let mut depsInfo : List (String × Option String) := []
   for modname in deps do
-    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
+    depsInfo := depsInfo ++ [(modname, lookupVersion "numpy")]
   return depsInfo
 -- impl-end
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,9 +46,12 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_dependencyVersions : List (String × Option String) := Id.run do
-  let deps := expectedDeps
+  -- WRONG: duplicates matplotlib and drops joblib
+  let deps := ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython",
+               "pandas", "matplotlib", "matplotlib"]
   let mut depsInfo : List (String × Option String) := []
   for modname in deps do
     depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,12 +46,14 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
 def implementation_dependencyVersions : List (String × Option String) := Id.run do
+  -- WRONG: every value is none, ignoring lookupVersion
   let deps := expectedDeps
   let mut depsInfo : List (String × Option String) := []
   for modname in deps do
-    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
+    depsInfo := depsInfo ++ [(modname, (none : Option String))]
   return depsInfo
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -46,13 +46,9 @@
   result = expectedDeps.map (fun m => (m, lookupVersion m))
 -- post-conditions-end
 
+
 -- impl-start
-def implementation_dependencyVersions : List (String × Option String) := Id.run do
-  let deps := expectedDeps
-  let mut depsInfo : List (String × Option String) := []
-  for modname in deps do
-    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
-  return depsInfo
+def implementation_dependencyVersions : List (String × Option String) := []
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the overview of installed dependency versions.

A diagnostics helper reports, for a chosen roster of relevant third-party
libraries, the installed version of each. It walks a hardcoded list of library
import-names and, for every name, records that name together with the version it
resolves to (or a null marker when the library is not importable). The result is
an ordered name→version mapping.

The desired behavior:

  * the mapping covers exactly the roster of relevant libraries — in the roster's
    order, with no name omitted and none added;
  * for each library the recorded value is the version produced by resolving that
    library (a null marker when it cannot be resolved);
  * the roster of relevant libraries includes, alongside the core numerical and
    build dependencies, the parallelism/serialization helper library `joblib`.
-/

-- axioms-start
/-- Resolution of a single library's installed version from its import-name: the
imported module's reported version, or a null marker when the library cannot be
imported. This is an unchanged helper, declared opaque so it can appear in the
executable implementation; the specification uses it identically on both sides and
consumes no property of it. -/
opaque lookupVersion : String → Option String
-- axioms-end

-- pure-start
/-- The roster of relevant library import-names the overview must cover, in order.
Includes `joblib` alongside the core numerical and build dependencies. -/
def expectedDeps : List String :=
  ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython", "pandas",
   "matplotlib", "joblib"]
-- pure-end

-- post-conditions-start
/-- The overview maps each library in the roster — in order, exactly that set of
names — to its resolved version. In particular `joblib` is among the covered
names. -/
def problem_spec_dependencyVersions
    (result : List (String × Option String)) : Prop :=
  result = expectedDeps.map (fun m => (m, lookupVersion m))
-- post-conditions-end

-- impl-start
def implementation_dependencyVersions : List (String × Option String) := Id.run do
  let deps := expectedDeps
  let mut depsInfo : List (String × Option String) := []
  for modname in deps do
    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
  return depsInfo
-- impl-end

-- proof-start
theorem correct_dependencyVersions :
    problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  simp [expectedDeps]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition is a COMPLETE equality to a uniquely-determined value: problem_spec := (result = expectedDeps.map (fun m => (m, lookupVersion m))), with expectedDeps a fixed literal (9 names incl. joblib) and lookupVersion opaque. Only one list value satisfies it, so any deviating impl is provably non-equal and cannot close.

Same_spec=True verified for all 8 attacks + positive control (swebench_unified.markers.same_spec, lean backend). All ran via scripts/lean_verify.sh <file>, concurrently (batches of ≤4).

Positive control atk_pos (byte-identical Solution.lean): EXIT 0; `#print axioms correct_dependencyVersions` => [propext, Quot.sound] — clean, no sorryAx, opaque lookupVersion NOT an axiom.

8 DISTINCT wrong impls, all EXIT 1 with genuine 'unsolved goals' (NOT timeouts/spurious):
- atk_1 partial-domain / prepatch bug: omits joblib (8 names) -> unsolved goals. Prepatch reproduced.
- atk_2 order: numpy/scipy swapped -> unsolved goals.
- atk_3 extra name: appends 'six' -> unsolved goals.
- atk_4 ungrounded oracle echo: joblib bound to fabricated some "1.0.0" instead of lookupVersion -> unsolved goals.
- atk_5 control-flow-effect / mis-bind: every value = lookupVersion "numpy" instead of modname -> unsolved goals.
- atk_6 boundary/count: matplotlib duplicated, joblib dropped -> unsolved goals.
- atk_7 ungrounded: every value none -> unsolved goals.
- atk_8 partial-domain extreme: empty result [] -> unsolved goals.

Hardened re-check: atk_1b re-ran the prepatch attack with a tactic battery (rfl|decide|native_decide|simp_all|simp[List.map];rfl|aesop) -> EXIT 1, goal reduces to `⊢ False` (unclosable). Confirms tightness is not tactic-fragile.

Protocol step 2 (materialize faithful patch + run_resolve) is VACUOUS: no wrong impl closed with clean axioms, so there is no closing counterexample to convert into a patch. No verify⇏correct witness exists.

refinement.md audit: 5 legs, all R (ops 2 dict↔assoc-list, 4 per-name resolution + dict-insert↔append, 5 return bijection) or I (op 1 deps literal identity, op 3 loop). NO kind-3 legs. NO A-consumed / A-reference legs — lookupVersion is an opaque symbol appearing byte-identically in spec (result = expectedDeps.map (fun m => (m, lookupVersion m))) and impl, consuming no property; G-AX correctly skips (axioms region declares signature only, no `axiom _prop`). The A-leg concern is N/A here; the model↔patch correspondence for the changed behavior (the joblib entry in the deeply-modeled expectedDeps list, op 1 = I) holds and matches the gold patch (append 'joblib' to deps). No hidden deep-model reference to a real callee. Frame discipline satisfied: full result pinned, no free component.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `atk_pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pos.lean`

```lean
import Mathlib
-- imports-end

/-!
Building the overview of installed dependency versions.

A diagnostics helper reports, for a chosen roster of relevant third-party
libraries, the installed version of each. It walks a hardcoded list of library
import-names and, for every name, records that name together with the version it
resolves to (or a null marker when the library is not importable). The result is
an ordered name→version mapping.

The desired behavior:

  * the mapping covers exactly the roster of relevant libraries — in the roster's
    order, with no name omitted and none added;
  * for each library the recorded value is the version produced by resolving that
    library (a null marker when it cannot be resolved);
  * the roster of relevant libraries includes, alongside the core numerical and
    build dependencies, the parallelism/serialization helper library `joblib`.
-/

-- axioms-start
/-- Resolution of a single library's installed version from its import-name: the
imported module's reported version, or a null marker when the library cannot be
imported. This is an unchanged helper, declared opaque so it can appear in the
executable implementation; the specification uses it identically on both sides and
consumes no property of it. -/
opaque lookupVersion : String → Option String
-- axioms-end

-- pure-start
/-- The roster of relevant library import-names the overview must cover, in order.
Includes `joblib` alongside the core numerical and build dependencies. -/
def expectedDeps : List String :=
  ["pip", "setuptools", "sklearn", "numpy", "scipy", "Cython", "pandas",
   "matplotlib", "joblib"]
-- pure-end

-- post-conditions-start
/-- The overview maps each library in the roster — in order, exactly that set of
names — to its resolved version. In particular `joblib` is among the covered
names. -/
def problem_spec_dependencyVersions
    (result : List (String × Option String)) : Prop :=
  result = expectedDeps.map (fun m => (m, lookupVersion m))
-- post-conditions-end

-- impl-start
def implementation_dependencyVersions : List (String × Option String) := Id.run do
  let deps := expectedDeps
  let mut depsInfo : List (String × Option String) := []
  for modname in deps do
    depsInfo := depsInfo ++ [(modname, lookupVersion modname)]
  return depsInfo
-- impl-end

-- proof-start
theorem correct_dependencyVersions :
    problem_spec_dependencyVersions implementation_dependencyVersions := by
  unfold problem_spec_dependencyVersions implementation_dependencyVersions
  simp [expectedDeps]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition is a COMPLETE equality to a uniquely-determined value: problem_spec := (result = expectedDeps.map (fun m => (m, lookupVersion m))), with expectedDeps a fixed literal (9 names incl. joblib) and lookupVersion opaque. Only one list value satisfies it, so any deviating impl is provably non-equal and cannot close.

Same_spec=True verified for all 8 attacks + positive control (swebench_unified.markers.same_spec, lean backend). All ran via scripts/lean_verify.sh <file>, concurrently (batches of ≤4).

Positive control atk_pos (byte-identical Solution.lean): EXIT 0; `#print axioms correct_dependencyVersions` => [propext, Quot.sound] — clean, no sorryAx, opaque lookupVersion NOT an axiom.

8 DISTINCT wrong impls, all EXIT 1 with genuine 'unsolved goals' (NOT timeouts/spurious):
- atk_1 partial-domain / prepatch bug: omits joblib (8 names) -> unsolved goals. Prepatch reproduced.
- atk_2 order: numpy/scipy swapped -> unsolved goals.
- atk_3 extra name: appends 'six' -> unsolved goals.
- atk_4 ungrounded oracle echo: joblib bound to fabricated some "1.0.0" instead of lookupVersion -> unsolved goals.
- atk_5 control-flow-effect / mis-bind: every value = lookupVersion "numpy" instead of modname -> unsolved goals.
- atk_6 boundary/count: matplotlib duplicated, joblib dropped -> unsolved goals.
- atk_7 ungrounded: every value none -> unsolved goals.
- atk_8 partial-domain extreme: empty result [] -> unsolved goals.

Hardened re-check: atk_1b re-ran the prepatch attack with a tactic battery (rfl|decide|native_decide|simp_all|simp[List.map];rfl|aesop) -> EXIT 1, goal reduces to `⊢ False` (unclosable). Confirms tightness is not tactic-fragile.

Protocol step 2 (materialize faithful patch + run_resolve) is VACUOUS: no wrong impl closed with clean axioms, so there is no closing counterexample to convert into a patch. No verify⇏correct witness exists.

refinement.md audit: 5 legs, all R (ops 2 dict↔assoc-list, 4 per-name resolution + dict-insert↔append, 5 return bijection) or I (op 1 deps literal identity, op 3 loop). NO kind-3 legs. NO A-consumed / A-reference legs — lookupVersion is an opaque symbol appearing byte-identically in spec (result = expectedDeps.map (fun m => (m, lookupVersion m))) and impl, consuming no property; G-AX correctly skips (axioms region declares signature only, no `axiom _prop`). The A-leg concern is N/A here; the model↔patch correspondence for the changed behavior (the joblib entry in the deeply-modeled expectedDeps list, op 1 = I) holds and matches the gold patch (append 'joblib' to deps). No hidden deep-model reference to a real callee. Frame discipline satisfied: full result pinned, no free component.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec-faithfulness (drift/too-strong) audit for scikit-learn__scikit-learn-14141 lean bundle.

Setup verified:
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True: the axioms/pure/post-conditions spec regions are byte-identical; only the impl region differs (prepatch omits 'joblib'), giving the correct G-DIFF discriminating signal.
- Proof genuine: file compiles under lean_verify.sh; `#print axioms correct_dependencyVersions` = [propext, Quot.sound] — clean, no sorryAx.
- Real repo at base_commit (_show_versions.py:33-69) confirmed: _get_deps_info builds deps_info dict by iterating hardcoded `deps`, setting deps_info[modname] = get_version(import_module(modname)) or None on ImportError; gold patch appends 'joblib' to deps.

Faithfulness reasoning:
Modeled function spec: result = expectedDeps.map (fun m => (m, lookupVersion m)), with lookupVersion the opaque UNCHANGED per-module resolver used IDENTICALLY on both sides. The spec is parameterized over the resolution environment only via lookupVersion, so it makes no claim beyond the real callee's behavior:
  * Real code sets a key for EVERY name even on ImportError (stores None) => no name dropped => matches the total `map` over expectedDeps.
  * Python dict preserves insertion order (>=3.7) => ordered assoc-list bijection faithful.
  * `deps` has no duplicate names => no dict key-collapse divergence.
  * The unchanged AttributeError-on-missing-__version__ behavior is abstracted into lookupVersion identically on both legs, so the spec neither over- nor under-specifies the fix.
Because lookupVersion is carried opaquely and appears identically in spec and impl, for EVERY resolution table the modeled function equals the post-patch real callee. G-CONF fuzz (conformance_check.py, seed 14141, 120k inputs + edges) independently confirms oracle==shadow on the full ordered (key,value) sequence.

No input exists on which the spec disagrees with the real post-patch _get_deps_info. The spec is not too strong and not drifted: it pins exactly the roster (including joblib), in order, each to its grounded resolution, mirroring the F2P 'joblib' in deps_info. Verdict: FAITHFUL; no diverging input.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gate: leakage / gold-reconstruction over the spec view (Solution.lean doc-comment + expectedDeps + postcondition), measured against the PUBLIC problem_statement (not hints_text).

Gold edit (patch.diff): a single one-line change to sklearn/utils/_show_versions.py:_get_deps_info — append "joblib" to the hardcoded `deps` list. Nothing else changes.

Public problem_statement: "Add joblib in show_versions. joblib should be added to the dependencies listed in show_versions or added to the issue template when sklearn version is > 0.20." This states the ENTIRE fix in the clear: add joblib to the show_versions dependency list.

Spec-view content examined:
  * Doc-comment (lines 4-21): describes building a name->version overview; explicitly names joblib as included in the roster (line 20). This is exactly what the public problem_statement already states — no incremental disclosure.
  * expectedDeps (lines 33-37): lists all 9 dependency names ["pip","setuptools","sklearn","numpy","scipy","Cython","pandas","matplotlib","joblib"]. The 8 non-joblib names are PRE-EXISTING code present in the file at base_commit (Solution_prepatch.lean / mapping.md base_commit listing confirm they are pre-patch context, not the gold edit). The only element that is the gold edit — joblib — is already public via problem_statement.
  * Postcondition / impl / proof: generic map over expectedDeps with opaque lookupVersion; reveal no edit specifics.

Conclusion: the spec view discloses the fix ONLY to the extent the public problem_statement already does (add joblib). No line reconstructs the gold edit beyond the public problem_statement — e.g. it does not leak that the change is purely a one-line list append at a specific position, nor any detail absent from the problem statement. The remaining dependency names are legitimate base_commit context needed to model the function. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.
